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
if 'nearby_cities_df' not in st.session_state:
    st.session_state.nearby_cities_df = None

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

def ensure_saved_searches_dir():
    if not os.path.exists(SAVED_SEARCHES_DIR):
        os.makedirs(SAVED_SEARCHES_DIR)

# Ensure directory exists at startup
ensure_saved_searches_dir()

def load_saved_searches():
    """Load saved searches from JSON files"""
    ensure_saved_searches_dir()
    saved_searches = []
    for filename in os.listdir(SAVED_SEARCHES_DIR):
        if filename.endswith('.json'):
            with open(os.path.join(SAVED_SEARCHES_DIR, filename), 'r') as f:
                saved_searches.append(json.load(f))
    return saved_searches

def save_search(results, business_type, selected_tld, cities):
    """Save search results to a JSON file"""
    ensure_saved_searches_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{SAVED_SEARCHES_DIR}/search_{timestamp}.json"
    
    search_data = {
        'timestamp': timestamp,
        'business_type': business_type,
        'tld': selected_tld,
        'results': results,
        'cities': cities
    }
    
    with open(filename, 'w') as f:
        json.dump(search_data, f)
    
    st.session_state.saved_searches = load_saved_searches()

def display_results(results, key_prefix=None):
    """Display results with affiliate links for available domains"""
    st.subheader("Results")
    # Table header
    cols = st.columns([3, 2, 2])
    cols[0].markdown("**Domain**")
    cols[1].markdown("**Status**")
    cols[2].markdown("**Register**")

    for idx, (domain, status) in enumerate(results):
        cols = st.columns([3, 2, 2])
        # Color the status cell
        if status == "Available":
            status_md = f'<span style="color:white;background:#1976D2;padding:2px 8px;border-radius:4px;">{status}</span>'
        elif "Active Website" in status:
            status_md = f'<span style="color:white;background:#C62828;padding:2px 8px;border-radius:4px;">{status}</span>'
        else:
            status_md = f'<span style="color:black;background:#F9A825;padding:2px 8px;border-radius:4px;">{status}</span>'

        cols[0].markdown(domain)
        cols[1].markdown(status_md, unsafe_allow_html=True)
        if status == "Available":
            namecheap_url = f"https://www.namecheap.com/domains/registration/results/?domain={domain}&aff=529630"
            button_html = f'''
                <a href="{namecheap_url}" target="_blank" style="
                    display:inline-block;
                    padding:6px 16px;
                    background:#1976D2;
                    color:white;
                    border-radius:4px;
                    text-decoration:none;
                    font-weight:bold;
                ">Register</a>
            '''
            cols[2].markdown(button_html, unsafe_allow_html=True)
        else:
            cols[2].markdown("-")

    # Count availability stats
    df = pd.DataFrame(results, columns=["Domain", "Status"])
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

    # Add download button for CSV with unique key
    csv = df.to_csv(index=False)
    st.download_button(
        label="Download Results as CSV",
        data=csv,
        file_name=f"domain_results.csv",
        mime="text/csv",
        key=f"download_{key_prefix}_{hash(csv)}" if key_prefix is not None else f"download_{hash(csv)}"
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
    business_type_nospaces = business_type.replace(' ', '').lower()
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
        domain = f"{city.lower().replace(' ', '')}{business_type_nospaces}.{selected_tld}"
        status = check_domains([domain], delay, timeout)[0][1]
        results.append([domain, status])
    
    # Final update
    progress_bar.progress(1.0)
    status_text.text(f"Completed checking {len(cities_to_check)} domains!")
    
    # Display results with affiliate links
    display_results(results)
    
    # Add save search button
    if st.button("Save This Search"):
        save_search(results, business_type, selected_tld, cities_to_check)
        st.success("Search saved successfully!")

st.set_page_config(
    page_title="Exact Match Domain Generator",
    page_icon="🌐"
)

# Add custom CSS to change link hover color
st.markdown("""
    <style>
        a:hover {
            color: #1976D2 !important;
        }
    </style>
""", unsafe_allow_html=True)

# Main App UI
st.title("Exact Match Domain Generator")

# Add custom CSS to change success message color
st.markdown("""
    <style>
        div[data-testid="stSuccess"] {
            background-color: #1976D2;
        }
    </style>
""", unsafe_allow_html=True)

# Display some example instructions
with st.expander("How to use this tool"):
    st.markdown("""
    ## How to Use This Tool

- This tool helps you find exact match domain names for your industry. You can add a list of cities or search by major city names to find their surrounding cities and suburbs.

    **Instructions:**
    1. Type in a kind of business (like "janitorial" or "plumber").
    2. Type in city names, one on each line.
    3. Pick a website ending (like .com, .net, etc.).
    4. You can change the speed settings if you want.
    5. Click the button to check if the website names are available.
    6. You can save your searches to look at them later.
    7. You can also download your results as a file.

    **What the results mean:**
    - **Available:** You can buy this website name.
    - **Registered (Active Website):** Someone else owns this name and has a website.
    - **Registered (No Active Website):** Someone owns this name, but there is no website.

    **Example cities:**
    ```
    Dallas
    Fort Worth
    Arlington
    Plano
    ```

    The tool will check if names like "dallasjanitorial.com" are available to buy.
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
    st.session_state.business_type = ""

business_type = st.text_input(
    "Business Type",
    value=st.session_state.business_type,
    placeholder="Enter your business industry (Janitorial, Plumbing, Etc.)",
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
            business_type_nospaces = business_type.replace(' ', '').lower()
            with st.spinner("Checking domain availability..."):
                # Format domains before checking
                domains_to_check = [f"{city.lower().replace(' ', '')}{business_type_nospaces}.{selected_tld}" for city in cities]
                results = check_domains(domains_to_check, delay, timeout)
                display_results(results)
                save_search(results, business_type, selected_tld, cities)

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
                    df = pd.DataFrame(nearby_cities, columns=['City', 'Distance (miles)'])
                    df = df.sort_values('Distance (miles)')
                    st.session_state.nearby_cities_df = df
                else:
                    st.session_state.nearby_cities_df = None
                    st.error("No cities found or error occurred")

    # Always display the DataFrame if it exists
    if st.session_state.nearby_cities_df is not None:
        st.dataframe(st.session_state.nearby_cities_df, use_container_width=True)
        if st.button("Check Domains for These Cities"):
            cities = st.session_state.nearby_cities_df['City'].tolist()
            business_type_nospaces = business_type.replace(' ', '').lower()
            with st.spinner("Checking domain availability..."):
                domains_to_check = [f"{city.lower().replace(' ', '')}{business_type_nospaces}.{selected_tld}" for city in cities]
                results = check_domains(domains_to_check, delay, timeout)
                display_results(results)
                save_search(results, business_type, selected_tld, cities)

with tab3:
    # Display saved searches
    if 'saved_searches' not in st.session_state or not st.session_state.saved_searches:
        st.session_state.saved_searches = load_saved_searches()
    if st.session_state.saved_searches:
        for i, search in enumerate(st.session_state.saved_searches):
            with st.expander(f"Search {i+1}: {search['business_type']} in {', '.join(search['cities'])}"):
                display_results(search['results'], key_prefix=i)
                # Add download button for each search
                if st.button(f"Download Results {i+1}"):
                    download_results(search['results'])
    else:
        st.info("No saved searches yet. Perform a search to save results.") 