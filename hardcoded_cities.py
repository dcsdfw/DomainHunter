"""
This module provides a simpler, more reliable approach to city radius searching by using
pre-calculated distances between major cities and nearby cities.
"""

import streamlit as st

# Top 50 US cities and their major suburbs/nearby cities (sample, can be expanded)
NEARBY_CITIES = {
    "new york": [
        ("Brooklyn", 5), ("Queens", 8), ("Bronx", 10), ("Jersey City", 7), ("Newark", 12), ("Yonkers", 15), ("Hoboken", 6), ("Staten Island", 12), ("White Plains", 22), ("New Rochelle", 18)
    ],
    "los angeles": [
        ("Long Beach", 25), ("Glendale", 10), ("Santa Monica", 15), ("Pasadena", 14), ("Burbank", 12), ("Inglewood", 11), ("Torrance", 20), ("Compton", 14), ("West Hollywood", 8), ("Culver City", 10)
    ],
    "chicago": [
        ("Evanston", 12), ("Oak Park", 9), ("Cicero", 8), ("Skokie", 15), ("Berwyn", 10), ("Elmwood Park", 13), ("Des Plaines", 18), ("Arlington Heights", 25), ("Schaumburg", 28), ("Naperville", 34)
    ],
    "houston": [
        ("Pasadena", 14), ("Sugar Land", 20), ("Pearland", 18), ("Baytown", 26), ("Missouri City", 19), ("Spring", 24), ("The Woodlands", 29), ("League City", 27), ("Friendswood", 22), ("Cypress", 25)
    ],
    "phoenix": [
        ("Mesa", 19), ("Scottsdale", 13), ("Tempe", 10), ("Chandler", 22), ("Gilbert", 24), ("Glendale", 10), ("Peoria", 15), ("Surprise", 25), ("Avondale", 17), ("Goodyear", 20)
    ],
    "philadelphia": [
        ("Camden", 8), ("Wilmington", 29), ("Cherry Hill", 13), ("Bensalem", 18), ("Norristown", 20), ("Levittown", 26), ("Chester", 16), ("Upper Darby", 9), ("Lansdowne", 10), ("Darby", 11)
    ],
    "san antonio": [
        ("New Braunfels", 32), ("Schertz", 21), ("Converse", 15), ("Live Oak", 17), ("Universal City", 18), ("Cibolo", 23), ("Seguin", 36), ("Helotes", 20), ("Leon Valley", 13), ("Alamo Heights", 7)
    ],
    "san diego": [
        ("Chula Vista", 9), ("La Mesa", 11), ("El Cajon", 15), ("National City", 7), ("Santee", 17), ("Poway", 22), ("Coronado", 8), ("Imperial Beach", 14), ("Lemon Grove", 10), ("Encinitas", 26)
    ],
    "dallas": [
        ("Plano", 19), ("Irving", 12), ("Garland", 16), ("Grand Prairie", 14), ("Mesquite", 15), ("Carrollton", 18), ("Richardson", 13), ("Lewisville", 23), ("Frisco", 25), ("Arlington", 20)
    ],
    "san jose": [
        ("Santa Clara", 6), ("Sunnyvale", 10), ("Milpitas", 11), ("Mountain View", 13), ("Cupertino", 12), ("Campbell", 8), ("Los Gatos", 15), ("Morgan Hill", 22), ("Palo Alto", 18), ("Fremont", 20)
    ],
    "austin": [
        ("Round Rock", 19), ("Cedar Park", 17), ("Pflugerville", 15), ("Georgetown", 27), ("San Marcos", 31), ("Leander", 22), ("Kyle", 21), ("Lakeway", 18), ("Hutto", 22), ("Buda", 15)
    ],
    "jacksonville": [
        ("Orange Park", 15), ("Atlantic Beach", 18), ("Neptune Beach", 19), ("Jacksonville Beach", 17), ("Fernandina Beach", 25), ("Middleburg", 23), ("Green Cove Springs", 28), ("St. Augustine", 38), ("Callahan", 22), ("Baldwin", 20)
    ],
    "fort worth": [
        ("Arlington", 15), ("North Richland Hills", 12), ("Haltom City", 8), ("Bedford", 14), ("Euless", 15), ("Grapevine", 21), ("Keller", 18), ("Saginaw", 10), ("Burleson", 17), ("Benbrook", 11)
    ],
    "indianapolis": [
        ("Carmel", 16), ("Fishers", 15), ("Greenwood", 12), ("Lawrence", 10), ("Beech Grove", 7),
        ("Speedway", 6), ("Plainfield", 15), ("Avon", 13), ("Zionsville", 18), ("Brownsburg", 17)
    ],
    "san francisco": [
        ("Oakland", 8), ("Berkeley", 10), ("Daly City", 10), ("San Mateo", 20), ("South San Francisco", 10),
        ("Pacifica", 12), ("Sausalito", 10), ("Millbrae", 15), ("Alameda", 12), ("Richmond", 15)
    ],
    "columbus": [
        ("Dublin", 15), ("Westerville", 14), ("Grove City", 12), ("Hilliard", 13), ("Gahanna", 11),
        ("Reynoldsburg", 13), ("Pickerington", 17), ("Upper Arlington", 8), ("Worthington", 10), ("Bexley", 7)
    ],
    "charlotte": [
        ("Concord", 20), ("Gastonia", 23), ("Huntersville", 15), ("Matthews", 13), ("Mint Hill", 14),
        ("Pineville", 11), ("Cornelius", 18), ("Davidson", 22), ("Belmont", 15), ("Indian Trail", 16)
    ],
    "detroit": [
        ("Dearborn", 10), ("Warren", 13), ("Livonia", 18), ("Southfield", 15), ("Royal Oak", 14),
        ("Taylor", 15), ("Westland", 17), ("Sterling Heights", 20), ("Redford", 12), ("Allen Park", 11)
    ],
    "el paso": [
        ("Socorro", 13), ("Horizon City", 20), ("Canutillo", 15), ("Sunland Park", 12), ("Anthony", 22),
        ("San Elizario", 18), ("Vinton", 20), ("Fabens", 25), ("Clint", 22), ("Tornillo", 30)
    ],
    "memphis": [
        ("Germantown", 15), ("Bartlett", 13), ("Collierville", 20), ("Southaven", 14), ("Horn Lake", 17),
        ("Olive Branch", 20), ("Lakeland", 18), ("Millington", 20), ("West Memphis", 12), ("Marion", 18)
    ],
    "boston": [
        ("Cambridge", 5), ("Somerville", 6), ("Brookline", 7), ("Newton", 10), ("Quincy", 10),
        ("Medford", 8), ("Chelsea", 7), ("Everett", 8), ("Watertown", 9), ("Malden", 9)
    ],
    "seattle": [
        ("Bellevue", 10), ("Redmond", 15), ("Kirkland", 12), ("Renton", 11), ("Shoreline", 9),
        ("Lynnwood", 16), ("Bothell", 15), ("Edmonds", 15), ("Burien", 8), ("Mercer Island", 8)
    ],
    "denver": [
        ("Aurora", 10), ("Lakewood", 8), ("Westminster", 12), ("Arvada", 10), ("Thornton", 13),
        ("Commerce City", 8), ("Englewood", 7), ("Littleton", 12), ("Northglenn", 14), ("Wheat Ridge", 9)
    ],
    "washington": [
        ("Arlington", 7), ("Alexandria", 8), ("Silver Spring", 9), ("Bethesda", 10), ("Hyattsville", 8),
        ("College Park", 12), ("Takoma Park", 7), ("Falls Church", 10), ("Greenbelt", 13), ("Oxon Hill", 11)
    ],
    "nashville": [
        ("Brentwood", 11), ("Franklin", 20), ("Hendersonville", 18), ("Smyrna", 23), ("La Vergne", 20),
        ("Mount Juliet", 17), ("Goodlettsville", 13), ("Gallatin", 25), ("Madison", 10), ("Antioch", 12)
    ],
    "baltimore": [
        ("Towson", 10), ("Dundalk", 8), ("Catonsville", 9), ("Parkville", 8), ("Pikesville", 11),
        ("Essex", 10), ("Rosedale", 9), ("Woodlawn", 11), ("Middle River", 13), ("Lansdowne", 8)
    ],
    "louisville": [
        ("Jeffersontown", 13), ("Shively", 8), ("St. Matthews", 9), ("Newburg", 10), ("Fern Creek", 14),
        ("Pleasure Ridge Park", 12), ("Valley Station", 15), ("Okolona", 11), ("Hurstbourne", 10), ("Middletown", 14)
    ],
    "portland": [
        ("Gresham", 15), ("Beaverton", 10), ("Hillsboro", 18), ("Tigard", 12), ("Lake Oswego", 9),
        ("West Linn", 14), ("Milwaukie", 8), ("Oregon City", 15), ("Happy Valley", 11), ("Aloha", 13)
    ],
    "oklahoma": [
        ("Norman", 20), ("Edmond", 15), ("Moore", 12), ("Midwest City", 10), ("Del City", 11),
        ("Yukon", 16), ("Bethany", 13), ("Mustang", 17), ("The Village", 12), ("Choctaw", 20)
    ],
    "milwaukee": [
        ("Wauwatosa", 8), ("West Allis", 7), ("Greenfield", 10), ("Brookfield", 13), ("Glendale", 8),
        ("Shorewood", 6), ("Whitefish Bay", 7), ("South Milwaukee", 12), ("Oak Creek", 14), ("Cudahy", 11)
    ],
    "las vegas": [
        ("North Las Vegas", 8), ("Henderson", 12), ("Paradise", 7), ("Spring Valley", 10), ("Sunrise Manor", 9),
        ("Enterprise", 13), ("Whitney", 11), ("Winchester", 8), ("Summerlin South", 15), ("Boulder City", 25)
    ],
    "albuquerque": [
        ("Rio Rancho", 15), ("South Valley", 10), ("North Valley", 12), ("Corrales", 14), ("Los Ranchos de Albuquerque", 11),
        ("Bernalillo", 18), ("Los Lunas", 22), ("Belen", 30), ("Tijeras", 20), ("Edgewood", 25)
    ],
    "tucson": [
        ("Oro Valley", 14), ("Marana", 15), ("Sahuarita", 18), ("Green Valley", 25), ("Vail", 20),
        ("South Tucson", 5), ("Drexel Heights", 10), ("Flowing Wells", 8), ("Casas Adobes", 12), ("Catalina Foothills", 13)
    ],
    "miami": [
        ("Miami Beach", 5), ("Hialeah", 10), ("Coral Gables", 7), ("Doral", 12), ("North Miami", 9), ("Kendall", 14), ("Aventura", 15), ("Homestead", 30), ("Key Biscayne", 8), ("Pinecrest", 11)
    ],
    # ... (continue for all other cities in the list not already present)
}

def find_nearby_cities(center_city, radius_miles, max_cities=20):
    """
    Get a list of nearby cities within a specified radius of a major city
    using pre-calculated distances for more reliable results.
    
    Args:
        center_city (str): The central city to search from
        radius_miles (float): Radius in miles
        max_cities (int): Maximum number of cities to return
        
    Returns:
        list: List of (city_name, distance) tuples within the radius
    """
    try:
        # Normalize the center city name to lowercase for lookup, and strip whitespace
        center_city_norm = center_city.strip().lower()
        st.write(f"Debug: Searching for city: '{center_city_norm}'")
        
        # Create a case-insensitive mapping of city names
        city_map = {city.lower(): city for city in NEARBY_CITIES.keys()}
        
        # Try to find the city in our case-insensitive map
        if center_city_norm in city_map:
            original_city = city_map[center_city_norm]
            st.write(f"Debug: Found city: '{original_city}'")
            
            # Auto-increase radius until at least 5 results or max 100 miles
            step = 10
            current_radius = radius_miles
            while current_radius <= 100:
                cities_in_radius = [
                    (city, distance) for city, distance in NEARBY_CITIES[original_city]
                    if distance <= current_radius
                ]
                if len(cities_in_radius) >= 5 or current_radius == 100:
                    cities_in_radius.sort(key=lambda x: x[1])
                    st.write(f"Debug: Found {len(cities_in_radius)} cities within {current_radius} miles")
                    return cities_in_radius[:max_cities]
                current_radius += step
            return []
        
        # If not found, try a fuzzy match
        for city_key in city_map.keys():
            if center_city_norm in city_key or city_key in center_city_norm:
                original_city = city_map[city_key]
                st.write(f"Debug: Found similar city: '{original_city}'")
                
                # Auto-increase radius until at least 5 results or max 100 miles
                step = 10
                current_radius = radius_miles
                while current_radius <= 100:
                    cities_in_radius = [
                        (city, distance) for city, distance in NEARBY_CITIES[original_city]
                        if distance <= current_radius
                    ]
                    if len(cities_in_radius) >= 5 or current_radius == 100:
                        cities_in_radius.sort(key=lambda x: x[1])
                        st.write(f"Debug: Found {len(cities_in_radius)} cities within {current_radius} miles")
                        return cities_in_radius[:max_cities]
                    current_radius += step
                return []
        
        st.write(f"Debug: City '{center_city_norm}' not found in database")
        st.write(f"Debug: Available cities: {', '.join(sorted(city_map.keys()))}")
        return []
        
    except Exception as e:
        st.error(f"Error finding nearby cities: {str(e)}")
        return []