from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import time

def get_city_coordinates(city_name, state=None):
    """
    Get the latitude and longitude of a city
    
    Args:
        city_name (str): Name of the city
        state (str, optional): US state abbreviation to narrow search
        
    Returns:
        tuple: (latitude, longitude) or None if not found
    """
    try:
        geolocator = Nominatim(user_agent="domain_checker_app")
        
        # Format query with state if provided
        if state:
            query = f"{city_name}, {state}, USA"
        else:
            query = f"{city_name}, USA"
            
        # Get location (synchronous call)
        location = geolocator.geocode(query, timeout=10)
        
        if location:
            return (location.latitude, location.longitude)
        return None
    except Exception as e:
        print(f"Error getting coordinates: {e}")
        return None


def find_cities_in_radius(center_city, radius_miles, state=None, max_results=30):
    """
    Find cities within a certain radius of a center city.
    Uses a preset list of cities by state for faster and more reliable results.
    
    Args:
        center_city (str): The central city name
        radius_miles (float): Radius in miles
        state (str, optional): US state abbreviation to narrow search
        max_results (int): Maximum number of cities to return
        
    Returns:
        list: List of (city_name, distance) tuples within the radius
    """
    # For debugging purposes
    print(f"Finding cities within {radius_miles} miles of {center_city}, state: {state}")
    
    # Get coordinates of the center city
    center_coords = get_city_coordinates(center_city, state)
    if not center_coords:
        print(f"Could not get coordinates for {center_city}")
        return []
    
    print(f"Center coordinates: {center_coords}")
    
    # Common US cities by state - this is just a sample, not comprehensive
    us_cities = {
        "TX": [
            "Dallas", "Fort Worth", "Arlington", "Plano", "Garland", 
            "Irving", "Frisco", "McKinney", "Grand Prairie", "Denton", 
            "Mesquite", "Carrollton", "Richardson", "Lewisville", "Allen", 
            "Flower Mound", "North Richland Hills", "Mansfield", "Rowlett", 
            "Euless", "DeSoto", "Grapevine", "Bedford", "Cedar Hill", "Wylie", 
            "Keller", "Coppell", "Rockwall", "Haltom City", "The Colony",
            "Burleson", "Hurst", "Little Elm", "Lancaster", "Balch Springs",
            "Southlake", "Addison", "Farmers Branch", "Waxahachie", "University Park"
        ],
        "CA": [
            "Los Angeles", "San Diego", "San Jose", "San Francisco", "Fresno",
            "Sacramento", "Long Beach", "Oakland", "Bakersfield", "Anaheim",
            "Santa Ana", "Riverside", "Stockton", "Irvine", "Chula Vista",
            "Fremont", "San Bernardino", "Modesto", "Fontana", "Oxnard",
            "Moreno Valley", "Huntington Beach", "Glendale", "Santa Clarita",
            "Garden Grove", "Oceanside", "Rancho Cucamonga", "Santa Rosa", "Ontario",
            "Lancaster", "Elk Grove", "Corona", "Palmdale", "Salinas", "Pomona"
        ],
        "FL": [
            "Jacksonville", "Miami", "Tampa", "Orlando", "St. Petersburg",
            "Hialeah", "Port St. Lucie", "Cape Coral", "Fort Lauderdale", "Pembroke Pines",
            "Hollywood", "Miramar", "Gainesville", "Coral Springs", "Miami Gardens",
            "Clearwater", "Palm Bay", "Pompano Beach", "West Palm Beach", "Lakeland",
            "Davie", "Miami Beach", "Sunrise", "Boca Raton", "Deltona",
            "Plantation", "Deerfield Beach", "Fort Myers", "Boynton Beach", "Lauderhill"
        ],
        "NY": [
            "New York City", "Buffalo", "Rochester", "Yonkers", "Syracuse",
            "Albany", "New Rochelle", "Mount Vernon", "Schenectady", "Utica",
            "White Plains", "Hempstead", "Troy", "Niagara Falls", "Binghamton",
            "Freeport", "Valley Stream", "Long Beach", "Rome", "North Tonawanda",
            "Ithaca", "Poughkeepsie", "Jamestown", "Elmira", "Saratoga Springs",
            "Lindenhurst", "Auburn", "Oswego", "Cortland", "Mamaroneck"
        ],
        "IL": [
            "Chicago", "Aurora", "Joliet", "Naperville", "Rockford",
            "Springfield", "Elgin", "Peoria", "Champaign", "Waukegan",
            "Cicero", "Bloomington", "Arlington Heights", "Evanston", "Schaumburg",
            "Bolingbrook", "Decatur", "Palatine", "Skokie", "Des Plaines",
            "Orland Park", "Tinley Park", "Oak Lawn", "Berwyn", "Mount Prospect",
            "Normal", "Wheaton", "Hoffman Estates", "Oak Park", "Downers Grove"
        ]
    }
    
    # Determine which cities to search
    all_cities = []
    
    # If state is provided and exists in our database, use just those cities
    if state and state.upper() in us_cities:
        all_cities = us_cities[state.upper()]
        print(f"Using {len(all_cities)} cities from state {state.upper()}")
    else:
        # If no state provided or state not found, use a subset from all states for better performance
        # Select first 20 cities from each state
        for state_code, state_cities in us_cities.items():
            all_cities.extend(state_cities[:20])
        print(f"Using {len(all_cities)} cities from all states (limited selection)")
    
    # A simplified approach for testing: use fixed distances for common city pairs
    # This helps when the geocoding API rate limits or has issues
    common_city_pairs = {
        ("Dallas", "Fort Worth"): 32,
        ("Dallas", "Arlington"): 20,
        ("Dallas", "Plano"): 19,
        ("Dallas", "Irving"): 12,
        ("Chicago", "Evanston"): 12,
        ("Chicago", "Oak Park"): 9,
        ("New York City", "Yonkers"): 15,
        ("Los Angeles", "Long Beach"): 25,
        ("Los Angeles", "Anaheim"): 26,
        ("Miami", "Fort Lauderdale"): 28
    }
    
    # Find cities within the radius
    cities_in_radius = []
    
    # Track cities we've processed to avoid duplicates
    processed_cities = set([center_city.lower()])
    
    print(f"Starting to check {len(all_cities)} cities for distance calculation")
    
    # First, try common pairs (faster)
    for (city1, city2), known_distance in common_city_pairs.items():
        if center_city.lower() == city1.lower() and known_distance <= radius_miles:
            cities_in_radius.append((city2, known_distance))
            processed_cities.add(city2.lower())
            print(f"Added {city2} using known distance: {known_distance} miles")
        elif center_city.lower() == city2.lower() and known_distance <= radius_miles:
            cities_in_radius.append((city1, known_distance))
            processed_cities.add(city1.lower())
            print(f"Added {city1} using known distance: {known_distance} miles")
    
    # Then check remaining cities (slower)
    for city in all_cities:
        if city.lower() in processed_cities:
            continue  # Skip cities we've already processed
            
        # Get coordinates for this city
        print(f"Checking distance to {city}")
        coords = get_city_coordinates(city, state)
        
        if coords:
            # Calculate distance
            distance = geodesic(center_coords, coords).miles
            print(f"Distance from {center_city} to {city}: {distance} miles")
            
            if distance <= radius_miles:
                cities_in_radius.append((city, distance))
                print(f"Added {city} at distance: {distance} miles")
        
        # Sleep to avoid rate limiting (shorter sleep since we have the known pairs approach)
        time.sleep(0.5)
    
    print(f"Found {len(cities_in_radius)} cities within radius")
    
    # Sort by distance and limit results
    cities_in_radius.sort(key=lambda x: x[1])
    return cities_in_radius[:max_results]