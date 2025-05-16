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
    Note: This is a simplified approach that uses a preset list of cities.
    For a more comprehensive solution, you would need a more detailed database.
    
    Args:
        center_city (str): The central city name
        radius_miles (float): Radius in miles
        state (str, optional): US state abbreviation to narrow search
        max_results (int): Maximum number of cities to return
        
    Returns:
        list: List of city names within the radius
    """
    # Get coordinates of the center city
    center_coords = get_city_coordinates(center_city, state)
    if not center_coords:
        return []
    
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
    
    # If state isn't provided, use a combination of common cities from different states
    all_cities = []
    if state and state.upper() in us_cities:
        all_cities = us_cities[state.upper()]
    else:
        # Combine cities from all states
        for state_cities in us_cities.values():
            all_cities.extend(state_cities)
    
    # Find cities within the radius
    cities_in_radius = []
    for city in all_cities:
        if city.lower() == center_city.lower():
            continue  # Skip the center city
            
        # Get coordinates for this city
        time.sleep(1)  # Add delay to avoid rate limiting
        coords = get_city_coordinates(city, state)
        if coords:
            # Calculate distance
            distance = geodesic(center_coords, coords).miles
            if distance <= radius_miles:
                cities_in_radius.append((city, distance))
    
    # Sort by distance and limit results
    cities_in_radius.sort(key=lambda x: x[1])
    return cities_in_radius[:max_results]