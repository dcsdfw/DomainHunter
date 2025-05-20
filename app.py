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
    
    # Create a placeholder for the results
    results_placeholder = st.empty()
    
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
        
        # Update results table
        df = pd.DataFrame(results, columns=["Domain", "Status"])
        results_placeholder.dataframe(df)
    
    # Final update
    progress_bar.progress(1.0)
    status_text.text(f"Completed checking {len(cities_to_check)} domains!")
    
    # Convert to pandas DataFrame for final display
    df = pd.DataFrame(results, columns=["Domain", "Status"])
    
    # Add color coding based on availability with better contrast
    def highlight_status(val):
        if val == "Available":
            return 'background-color: #2E7D32; color: white'  # Dark green with white text
        elif "Active Website" in val:
            return 'background-color: #C62828; color: white'  # Dark red with white text
        else:
            return 'background-color: #F9A825; color: black'  # Dark yellow with black text
    
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
        st.metric("Available", available_count, f"{available_count/len(cities_to_check):.0%}")
    with col2:
        st.metric("Registered (Active)", registered_active_count, f"{registered_active_count/len(cities_to_check):.0%}")
    with col3:
        st.metric("Registered (Inactive)", registered_inactive_count, f"{registered_inactive_count/len(cities_to_check):.0%}")
    
    # Add save search button
    if st.button("Save This Search"):
        save_search(results, business_type, selected_tld)
        st.success("Search saved successfully!")
    
    # Add download button for CSV
    csv = df.to_csv(index=False)
    st.download_button(
        label="Download Results as CSV",
        data=csv,
        file_name=f"{business_type}_{selected_tld}_domains.csv",
        mime="text/csv"
    )

st.set_page_config(
    page_title="Domain Availability Checker",
    page_icon="🌐"
)

# Main App UI
st.title("Domain Availability Checker")

# Add a tab for viewing saved searches
tab1, tab2, tab3 = st.tabs(["Enter Cities Manually", "Find Cities by Radius", "Saved Searches"])

# Input for business type with validation
business_type = st.text_input(
    "Business Type",
    value="janitorial",
    max_chars=MAX_BUSINESS_TYPE_LENGTH,
    help=f"Enter a business type (max {MAX_BUSINESS_TYPE_LENGTH} characters)"
)

# Parameters for domain checking - placed at top level for access everywhere
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

with tab1:
    # Input for cities
    cities_input = st.text_area(
        "Enter cities (one per line)",
        height=150,
        help="Enter each city on a new line"
    )
    
    # Check domains button for manual entry
    if st.button("Check Domain Availability", type="primary"):
        if not cities_input:
            st.error("Please enter at least one city or use the radius search to find cities.")
        else:
            cities_to_check = [city.strip() for city in cities_input.split('\n') if city.strip()]
            
            if not cities_to_check:
                st.error("No valid cities found in the input.")
            else:
                check_city_domains(cities_to_check, business_type, selected_tld, delay, timeout)

with tab2:
    col1, col2 = st.columns(2)
    
    with col1:
        major_city = st.text_input("Major City", placeholder="e.g. Dallas")
        state_code = st.text_input("State (optional)", placeholder="e.g. TX", max_chars=2,
                                  help="Two-letter state code to improve search accuracy")
    
    with col2:
        radius = st.slider("Radius (miles)", 5, 100, 25, 5,
                          help="Search for cities within this distance")
        max_cities = st.slider("Max Cities", 5, 50, 20, 5,
                              help="Maximum number of cities to include")
    
    # Button to find nearby cities
    search_clicked = st.button("Find Nearby Cities")
    
    if search_clicked:
        if not major_city:
            st.error("Please enter a major city.")
        else:
            with st.spinner(f"Finding cities within {radius} miles of {major_city}..."):
                # First try the hardcoded city data (faster and more reliable)
                nearby_cities = find_nearby_cities(major_city, radius, max_cities)
                
                if not nearby_cities:
                    # If not found in hardcoded data, try the geocoding method
                    st.info(f"Searching for cities near {major_city}...")
                    coords = get_city_coordinates(major_city, state_code)
                    if not coords:
                        st.error(f"Could not find coordinates for {major_city}. Please check the city name and try again.")
                    else:
                        nearby_cities = find_cities_in_radius(major_city, radius, state_code, max_cities)
                
                if not nearby_cities:
                    st.warning(f"No cities found within {radius} miles of {major_city}. Try a larger radius or a different major city.")
                else:
                    # Display the found cities
                    st.success(f"Found {len(nearby_cities)} cities within {radius} miles of {major_city}!")
                    
                    # Create a DataFrame with the cities and distances
                    city_df = pd.DataFrame(nearby_cities, columns=["City", "Distance (miles)"])
                    city_df["Distance (miles)"] = city_df["Distance (miles)"].round(1)
                    
                    # Display the cities in a table
                    st.dataframe(city_df)
                    
                    # Store the city list in session state
                    st.session_state.cities_list = city_df["City"].tolist()
                    st.session_state.show_domain_check = True
    
    # Show the check domains button if we have cities
    if st.session_state.show_domain_check and st.session_state.cities_list:
        st.write("---")
        st.write("Found cities are ready for domain checking!")
        check_radius_domains = st.button("Check Domains for These Cities", type="primary")
        
        if check_radius_domains:
            # Run the domain check with the stored cities
            check_city_domains(st.session_state.cities_list, business_type, selected_tld, delay, timeout)

with tab3:
    st.subheader("Saved Searches")
    
    # Load and display saved searches
    saved_searches = load_saved_searches()
    
    if not saved_searches:
        st.info("No saved searches yet. Save your searches to view them here!")
    else:
        for search in saved_searches:
            with st.expander(f"Search from {search['timestamp']} - {search['business_type']}.{search['tld']}"):
                df = pd.DataFrame(search['results'], columns=["Domain", "Status"])
                
                # Apply the same styling as in the main results
                def highlight_status(val):
                    if val == "Available":
                        return 'background-color: #2E7D32; color: white'
                    elif "Active Website" in val:
                        return 'background-color: #C62828; color: white'
                    else:
                        return 'background-color: #F9A825; color: black'
                
                st.dataframe(df.style.map(highlight_status, subset=['Status']))
                
                # Add download button for this saved search
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download This Search as CSV",
                    data=csv,
                    file_name=f"saved_search_{search['timestamp']}.csv",
                    mime="text/csv"
                )

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
