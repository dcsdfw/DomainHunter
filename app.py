import streamlit as st
import pandas as pd
from domain_checker import check_domains
from city_finder import find_cities_in_radius, get_city_coordinates

st.set_page_config(
    page_title="Domain Availability Checker",
    page_icon="🌐"
)

st.title("Domain Availability Checker")

# Input for business type
business_type = st.text_input("Business Type", value="janitorial")

# Create tabs for different input methods
tab1, tab2 = st.tabs(["Enter Cities Manually", "Find Cities by Radius"])

with tab1:
    # Input for cities
    cities_input = st.text_area(
        "Enter cities (one per line)",
        height=150,
        help="Enter each city on a new line"
    )

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
    if st.button("Find Nearby Cities"):
        if not major_city:
            st.error("Please enter a major city.")
        else:
            with st.spinner(f"Finding cities within {radius} miles of {major_city}..."):
                # Check if the city coordinates can be found
                coords = get_city_coordinates(major_city, state_code)
                if not coords:
                    st.error(f"Could not find coordinates for {major_city}. Please check the city name and try again.")
                else:
                    nearby_cities = find_cities_in_radius(major_city, radius, state_code, max_cities)
                    
                    if not nearby_cities:
                        st.warning(f"No cities found within {radius} miles of {major_city}.")
                    else:
                        # Display the found cities
                        st.success(f"Found {len(nearby_cities)} cities within {radius} miles of {major_city}!")
                        
                        # Create a DataFrame with the cities and distances
                        city_df = pd.DataFrame(nearby_cities, columns=["City", "Distance (miles)"])
                        city_df["Distance (miles)"] = city_df["Distance (miles)"].round(1)
                        
                        # Display the cities in a table
                        st.dataframe(city_df)
                        
                        # Button to use these cities
                        if st.button("Use These Cities for Domain Check"):
                            # Extract just the city names
                            cities_list = city_df["City"].tolist()
                            # Set the value in the first tab's text area
                            cities_input = "\n".join(cities_list)
                            st.session_state["cities_input"] = cities_input
                            # Switch to the first tab
                            st.rerun()

# Retrieve cities from session state if available
if "cities_input" in st.session_state:
    cities_input = st.session_state["cities_input"]
    del st.session_state["cities_input"]  # Clear after use

# Parameters for domain checking - placed outside tabs
with st.expander("Advanced Settings"):
    delay = st.slider("Delay between requests (seconds)", 0.1, 2.0, 0.5, 0.1,
                     help="Higher values reduce the risk of being blocked")
    timeout = st.slider("Request timeout (seconds)", 1, 10, 3, 1,
                       help="Time to wait for a domain to respond")

    # Domain TLD options
    tld_options = ["com", "net", "org", "io", "co"]
    selected_tld = st.selectbox("Domain Extension (TLD)", tld_options, index=0)

# Check domains button - placed outside tabs
if st.button("Check Domain Availability", type="primary"):
    if not cities_input:
        st.error("Please enter at least one city or use the radius search to find cities.")
    else:
        cities = [city.strip() for city in cities_input.split('\n') if city.strip()]
        
        if not cities:
            st.error("No valid cities found in the input.")
        else:
            # Display information
            st.info(f"Checking {len(cities)} domains with business type: {business_type} and TLD: .{selected_tld}")
            
            # Create a progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Create a placeholder for the results
            results_placeholder = st.empty()
            
            # Process domains in batches to update UI
            results = []
            for i, city in enumerate(cities):
                # Update progress and status
                progress = (i + 1) / len(cities)
                progress_bar.progress(progress)
                status_text.text(f"Checking domain for {city}... ({i+1}/{len(cities)})")
                
                # Check domain
                domain = f"{city.lower().replace(' ', '')}{business_type}.{selected_tld}"
                status = check_domains([domain], delay, timeout)[0][1]
                results.append([domain, status])
                
                # Update results table
                df = pd.DataFrame(results, columns=["Domain", "Status"])
                results_placeholder.dataframe(df)
            
            # Final update
            progress_bar.progress(1.0)
            status_text.text(f"Completed checking {len(cities)} domains!")
            
            # Convert to pandas DataFrame for final display
            df = pd.DataFrame(results, columns=["Domain", "Status"])
            
            # Add color coding based on availability
            def highlight_status(val):
                if val == "Available":
                    return 'background-color: #CCFFCC'  # Light green
                elif "Active Website" in val:
                    return 'background-color: #FFCCCC'  # Light red
                else:
                    return 'background-color: #FFFFCC'  # Light yellow
            
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
                st.metric("Available", available_count, f"{available_count/len(cities):.0%}")
            with col2:
                st.metric("Registered (Active)", registered_active_count, f"{registered_active_count/len(cities):.0%}")
            with col3:
                st.metric("Registered (Inactive)", registered_inactive_count, f"{registered_inactive_count/len(cities):.0%}")
            
            # Add download button for CSV
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download Results as CSV",
                data=csv,
                file_name=f"{business_type}_{selected_tld}_domains.csv",
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
    6. Download the results as a CSV file
    
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
