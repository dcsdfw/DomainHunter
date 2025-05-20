import streamlit as st
import pandas as pd
from domain_checker import check_domains
from city_finder import find_cities_in_radius, get_city_coordinates
from hardcoded_cities import find_nearby_cities
import json
from datetime import datetime
import os
import time
import re
from functools import wraps
import secrets
import hashlib

# Security configurations
MAX_REQUESTS_PER_MINUTE = 30
MAX_CITIES_PER_SEARCH = 50
ALLOWED_TLDS = ["com", "net", "org", "io", "co"]
MAX_BUSINESS_TYPE_LENGTH = 30
SAVED_SEARCHES_DIR = "saved_searches"

# Initialize session state variables if they don't exist
if 'cities_list' not in st.session_state:
    st.session_state.cities_list = []
if 'show_domain_check' not in st.session_state:
    st.session_state.show_domain_check = False
if 'saved_searches' not in st.session_state:
    st.session_state.saved_searches = []
if 'request_count' not in st.session_state:
    st.session_state.request_count = 0
if 'last_request_time' not in st.session_state:
    st.session_state.last_request_time = time.time()
if 'session_id' not in st.session_state:
    st.session_state.session_id = secrets.token_hex(16)

# Create a directory for saved searches if it doesn't exist
if not os.path.exists(SAVED_SEARCHES_DIR):
    os.makedirs(SAVED_SEARCHES_DIR)

def rate_limit(func):
    """Decorator to implement rate limiting"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        current_time = time.time()
        # Reset counter if a minute has passed
        if current_time - st.session_state.last_request_time >= 60:
            st.session_state.request_count = 0
            st.session_state.last_request_time = current_time
        
        # Check if rate limit exceeded
        if st.session_state.request_count >= MAX_REQUESTS_PER_MINUTE:
            st.error("Rate limit exceeded. Please wait a minute before making more requests.")
            return None
        
        st.session_state.request_count += 1
        return func(*args, **kwargs)
    return wrapper

def sanitize_input(text):
    """Sanitize user input to prevent injection attacks"""
    # Remove any non-alphanumeric characters except spaces and basic punctuation
    sanitized = re.sub(r'[^a-zA-Z0-9\s\-\.]', '', text)
    return sanitized.strip()

def validate_business_type(business_type):
    """Validate business type input"""
    if not business_type:
        return False, "Business type cannot be empty"
    if len(business_type) > MAX_BUSINESS_TYPE_LENGTH:
        return False, f"Business type must be {MAX_BUSINESS_TYPE_LENGTH} characters or less"
    if not re.match(r'^[a-zA-Z0-9\s\-\.]+$', business_type):
        return False, "Business type contains invalid characters"
    return True, ""

def validate_city(city):
    """Validate city name input"""
    if not city:
        return False, "City name cannot be empty"
    if not re.match(r'^[a-zA-Z\s\-\.]+$', city):
        return False, "City name contains invalid characters"
    return True, ""

def load_saved_searches():
    """Load saved searches from JSON files"""
    saved_searches = []
    for filename in os.listdir(SAVED_SEARCHES_DIR):
        if filename.endswith('.json'):
            with open(os.path.join(SAVED_SEARCHES_DIR, filename), 'r') as f:
                saved_searches.append(json.load(f))
    return saved_searches

def save_search(results, business_type, selected_tld):
    """Save search results to a JSON file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{SAVED_SEARCHES_DIR}/search_{timestamp}.json"
    
    search_data = {
        'timestamp': timestamp,
        'business_type': business_type,
        'tld': selected_tld,
        'results': results
    }
    
    with open(filename, 'w') as f:
        json.dump(search_data, f)
    
    st.session_state.saved_searches = load_saved_searches()

def display_results(results):
    """Display results with affiliate links for available domains"""
    df = pd.DataFrame(results, columns=["Domain", "Status"])
    
    # Add color coding based on availability with better contrast
    def highlight_status(val):
        if val == "Available":
            return 'background-color: #2E7D32; color: white'  # Dark green with white text
        elif "Active Website" in val:
            return 'background-color: #C62828; color: white'  # Dark red with white text
        else:
            return 'background-color: #F9A825; color: black'  # Dark yellow with black text
    
    # Add affiliate link column for available domains
    def make_affiliate_link(domain, status):
        if status == "Available":
            return f"[Register on Namecheap](https://www.namecheap.com/domains/registration/results/?domain={domain}&aff=529630)"
        return ""
    
    df["Register"] = [make_affiliate_link(row[0], row[1]) for row in results]
    
    # Show results with styling
    st.subheader("Results")
    st.dataframe(df.style.map(highlight_status, subset=['Status']))
    
    # Count availability stats
    available_count = df[df['Status'] == 'Available'].shape[0]
    registered_active_count = df[df['Status'] == 'Registered (Active Website)'].shape[0]
    registered_inactive_count = df[df['Status'] == 'Registered (No Active Website)'].shape[0]
    
    # Display stats
    st.subheader("Summary")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Available", available_count, f"{available_count/len(results):.0%}")
    with col2:
        st.metric("Registered (Active)", registered_active_count, f"{registered_active_count/len(results):.0%}")
    with col3:
        st.metric("Registered (Inactive)", registered_inactive_count, f"{registered_inactive_count/len(results):.0%}")
    
    # Add download button for CSV
    csv = df.to_csv(index=False)
    st.download_button(
        label="Download Results as CSV",
        data=csv,
        file_name=f"domain_results.csv",
        mime="text/csv"
    )

@rate_limit
def check_city_domains(cities_to_check, business_type, selected_tld, delay, timeout):
    """Perform domain checks with rate limiting and input validation"""
    # Validate inputs
    if not cities_to_check:
        st.error("No cities provided for domain check.")
        return
    
    if len(cities_to_check) > MAX_CITIES_PER_SEARCH:
        st.error(f"Maximum {MAX_CITIES_PER_SEARCH} cities allowed per search.")
        return
    
    is_valid, message = validate_business_type(business_type)
    if not is_valid:
        st.error(message)
        return
    
    if selected_tld not in ALLOWED_TLDS:
        st.error("Invalid TLD selected.")
        return
    
    # Sanitize inputs
    business_type = sanitize_input(business_type)
    cities_to_check = [sanitize_input(city) for city in cities_to_check]
    
    # Display information
    st.info(f"Checking {len(cities_to_check)} domains with business type: {business_type} and TLD: .{selected_tld}")
    
    # Create a progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Process domains in batches to update UI
    results = []
    for i, city in enumerate(cities_to_check):
        # Update progress and status
        progress = (i + 1) / len(cities_to_check)
        progress_bar.progress(progress)
        status_text.text(f"Checking domain for {city}... ({i+1}/{len(cities_to_check)})")
        
        # Check domain
        domain = f"{city.lower().replace(' ', '')}{business_type}.{selected_tld}"
        status = check_domains([domain], delay, timeout)[0][1]
        results.append([domain, status])
    
    # Final update
    progress_bar.progress(1.0)
    status_text.text(f"Completed checking {len(cities_to_check)} domains!")
    
    # Display results with affiliate links
    display_results(results)
    
    # Add save search button
    if st.button("Save This Search"):
        save_search(results, business_type, selected_tld)
        st.success("Search saved successfully!")

st.set_page_config(
    page_title="Domain Availability Checker",
    page_icon="🌐"
)

# Main App UI
st.title("Domain Availability Checker")

# Display some example instructions
with st.expander("How to use this tool"):
    st.markdown("""
    ## Domain Availability Checker
    
    This tool helps you check if domain names are available for registration. It's useful for finding business domain names across multiple locations.
    
    ### Instructions:
    1. Enter a business type (default is "janitorial")
    2. Enter cities, one per line
    3. Choose a domain extension (.com, .net, etc.)
    4. Adjust the delay and timeout settings if needed
    5. Click "Check Domain Availability" to start the process
    6. Save your searches to view them later
    7. Download the results as a CSV file
    
    ### Status Meanings:
    - **Available:** The domain is likely available for registration
    - **Registered (Active Website):** Domain is taken and has an active website
    - **Registered (No Active Website):** Domain is registered but doesn't have an active website
    
    ### Example cities:
    ```
    Dallas
    Fort Worth
    Arlington
    Plano
    ```
    
    The tool will check if domains like "dallasjanitorial.com" are available for registration.
    """)

# Parameters for domain checking - placed after How to use this tool
with st.expander("Advanced Settings"):
    delay = st.slider(
        "Delay between requests (seconds)",
        0.1, 2.0, 0.5, 0.1,
        help="Higher values reduce the risk of being blocked"
    )
    timeout = st.slider(
        "Request timeout (seconds)",
        1, 10, 3, 1,
        help="Time to wait for a domain to respond"
    )

    # Domain TLD options
    selected_tld = st.selectbox(
        "Domain Extension (TLD)",
        ALLOWED_TLDS,
        index=0
    )

# Business type input above tabs
if 'business_type' not in st.session_state:
    st.session_state.business_type = "janitorial"

business_type = st.text_input(
    "Business Type",
    value=st.session_state.business_type,
    help="Enter the type of business (e.g., janitorial, plumbing, etc.)"
)
st.session_state.business_type = business_type

# Add a tab for viewing saved searches
tab1, tab2, tab3 = st.tabs(["Enter Cities Manually", "Find Cities by Radius", "Saved Searches"])

with tab1:
    # Input for cities
    cities_input = st.text_area(
        "Enter Cities",
        height=150,
        help="Enter one city per line"
    )

    if st.button("Check Domain Availability"):
        if not cities_input.strip():
            st.error("Please enter at least one city")
        else:
            cities = [city.strip() for city in cities_input.split('\n') if city.strip()]
            with st.spinner("Checking domain availability..."):
                results = check_domains(cities, business_type, selected_tld, delay, timeout)
                display_results(results)
                save_search(results, business_type, selected_tld)

with tab2:
    # Input for finding nearby cities
    col1, col2 = st.columns(2)
    with col1:
        city = st.text_input("Enter a city name")
    with col2:
        radius = st.number_input("Radius (miles)", min_value=1, max_value=100, value=25)

    if st.button("Find Nearby Cities"):
        if not city:
            st.error("Please enter a city name")
        else:
            with st.spinner("Finding nearby cities..."):
                nearby_cities = find_nearby_cities(city, radius)
                if nearby_cities:
                    st.success(f"Found {len(nearby_cities)} cities within {radius} miles of {city}")
                    st.write(nearby_cities)
                else:
                    st.error("No cities found or error occurred")

with tab3:
    # Display saved searches
    if 'saved_searches' in st.session_state and st.session_state.saved_searches:
        for i, search in enumerate(st.session_state.saved_searches):
            with st.expander(f"Search {i+1}: {search['business_type']} in {', '.join(search['cities'])}"):
                display_results(search['results'])
                # Add download button for each search
                if st.button(f"Download Results {i+1}"):
                    download_results(search['results'])
    else:
        st.info("No saved searches yet. Perform a search to save results.")
