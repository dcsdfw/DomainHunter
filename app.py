import streamlit as st
import pandas as pd
from domain_checker import check_domains

st.set_page_config(
    page_title="Domain Availability Checker",
    page_icon="🌐"
)

st.title("Domain Availability Checker")

# Input for business type
business_type = st.text_input("Business Type", value="janitorial")

# Input for cities
cities_input = st.text_area(
    "Enter cities (one per line)",
    height=200,
    help="Enter each city on a new line"
)

# Parameters for domain checking
delay = st.slider("Delay between requests (seconds)", 0.1, 2.0, 0.5, 0.1,
                 help="Higher values reduce the risk of being blocked")
timeout = st.slider("Request timeout (seconds)", 1, 10, 3, 1,
                   help="Time to wait for a domain to respond")

if st.button("Check Domains"):
    if not cities_input.strip():
        st.error("Please enter at least one city.")
    else:
        cities = [city.strip() for city in cities_input.split('\n') if city.strip()]
        
        # Display information
        st.info(f"Checking {len(cities)} domains with business type: {business_type}")
        
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
            domain = f"{city.lower().replace(' ', '')}{business_type}.com"
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
        st.subheader("Results")
        st.dataframe(df)
        
        # Add download button for CSV
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download Results as CSV",
            data=csv,
            file_name=f"{business_type}_domains.csv",
            mime="text/csv"
        )

# Display some example instructions
with st.expander("How to use this tool"):
    st.markdown("""
    1. Enter a business type (default is "janitorial")
    2. Enter cities, one per line
    3. Adjust the delay and timeout settings if needed
    4. Click "Check Domains" to start the process
    5. Download the results as a CSV file
    
    **Example cities:**
    ```
    Dallas
    Fort Worth
    Arlington
    Plano
    ```
    
    The tool will check if domains like "dallasjanitorial.com" are available.
    """)
