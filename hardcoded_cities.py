"""
This module provides a simpler, more reliable approach to city radius searching by using
pre-calculated distances between major cities and nearby cities.
"""

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
    # ... (add more cities as needed for the top 50)
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
    # Normalize the center city name to lowercase for lookup
    center_city_norm = center_city.lower()
    
    # Check if we have pre-calculated data for this city
    if center_city_norm in NEARBY_CITIES:
        # Filter cities within the radius
        cities_in_radius = [
            (city, distance) for city, distance in NEARBY_CITIES[center_city_norm]
            if distance <= radius_miles
        ]
        
        # Sort by distance and limit to max_cities
        cities_in_radius.sort(key=lambda x: x[1])
        return cities_in_radius[:max_cities]
    
    # If city not in our database, return empty list
    return []