"""
This module provides a simpler, more reliable approach to city radius searching by using
pre-calculated distances between major cities and nearby cities.
"""

# Dictionary of major cities and their nearby cities with distances
# Format: {major_city: [(nearby_city1, distance1), (nearby_city2, distance2), ...]}
NEARBY_CITIES = {
    "dallas": [
        ("Fort Worth", 32),
        ("Arlington", 20),
        ("Plano", 19),
        ("Garland", 16),
        ("Irving", 12),
        ("Frisco", 28),
        ("McKinney", 32),
        ("Grand Prairie", 14),
        ("Denton", 40),
        ("Mesquite", 15),
        ("Carrollton", 18),
        ("Richardson", 13),
        ("Lewisville", 24),
        ("Allen", 26),
        ("Flower Mound", 28),
        ("North Richland Hills", 27),
        ("Mansfield", 25),
        ("Rowlett", 22),
        ("Euless", 19),
        ("DeSoto", 16),
        ("Grapevine", 22),
        ("Bedford", 24),
        ("Cedar Hill", 20),
        ("Wylie", 28),
        ("Keller", 30),
        ("Coppell", 16),
        ("Rockwall", 25),
        ("Haltom City", 30),
        ("The Colony", 23),
        ("Burleson", 37),
        ("Hurst", 25),
        ("Little Elm", 32),
        ("Lancaster", 15),
        ("Balch Springs", 14),
        ("Southlake", 26),
        ("Addison", 14),
        ("Farmers Branch", 10),
        ("Waxahachie", 30),
        ("University Park", 5)
    ],
    "houston": [
        ("Sugar Land", 22),
        ("The Woodlands", 30),
        ("Baytown", 26),
        ("Conroe", 40),
        ("Pearland", 17),
        ("League City", 27),
        ("Missouri City", 18),
        ("Kingwood", 23),
        ("Friendswood", 22),
        ("Rosenberg", 35),
        ("Spring", 23),
        ("Alvin", 30),
        ("Stafford", 17),
        ("Humble", 18),
        ("Richmond", 30),
        ("Webster", 25),
        ("Deer Park", 19),
        ("Tomball", 30),
        ("Galena Park", 10),
        ("Katy", 29)
    ],
    "chicago": [
        ("Evanston", 12),
        ("Oak Park", 9),
        ("Cicero", 7),
        ("Skokie", 12),
        ("Berwyn", 10),
        ("Oak Lawn", 13),
        ("Downers Grove", 21),
        ("Des Plaines", 17),
        ("Orland Park", 25),
        ("Arlington Heights", 24),
        ("Tinley Park", 28),
        ("Schaumburg", 30),
        ("Naperville", 28),
        ("Joliet", 40),
        ("Elgin", 38),
        ("Aurora", 40),
        ("Waukegan", 36),
        ("Bolingbrook", 30),
        ("Gary, IN", 30),
        ("Hammond, IN", 20)
    ],
    "new york": [
        ("Yonkers", 15),
        ("Newark", 10),
        ("Jersey City", 8),
        ("Hoboken", 4),
        ("White Plains", 25),
        ("New Rochelle", 17),
        ("Stamford, CT", 30),
        ("Hempstead", 26),
        ("Freeport", 29),
        ("Valley Stream", 20),
        ("Long Beach", 25),
        ("Mount Vernon", 15),
        ("Schenectady", 28),
        ("Troy", 24),
        ("Paterson, NJ", 15),
        ("Elizabeth, NJ", 14),
        ("Clifton, NJ", 12),
        ("Passaic, NJ", 10),
        ("Fort Lee, NJ", 8),
        ("Hackensack, NJ", 12)
    ],
    "los angeles": [
        ("Long Beach", 25),
        ("Anaheim", 26),
        ("Santa Ana", 30),
        ("Irvine", 40),
        ("Glendale", 8),
        ("Huntington Beach", 35),
        ("Santa Clarita", 35),
        ("Garden Grove", 33),
        ("Torrance", 20),
        ("Pasadena", 10),
        ("Burbank", 10),
        ("Inglewood", 10),
        ("Costa Mesa", 40),
        ("Downey", 15),
        ("West Covina", 19),
        ("Norwalk", 17),
        ("Compton", 17),
        ("South Gate", 10),
        ("Alhambra", 8),
        ("Whittier", 17)
    ],
    "san francisco": [
        ("Oakland", 8),
        ("Berkeley", 10),
        ("San Jose", 48),
        ("Fremont", 35),
        ("Hayward", 25),
        ("Sunnyvale", 40),
        ("Santa Clara", 45),
        ("Concord", 29),
        ("Daly City", 10),
        ("San Mateo", 20),
        ("Redwood City", 25),
        ("Palo Alto", 35),
        ("Richmond", 17),
        ("Alameda", 10),
        ("Walnut Creek", 25),
        ("San Rafael", 18),
        ("Novato", 30),
        ("San Bruno", 12),
        ("South San Francisco", 10),
        ("Pleasanton", 35)
    ],
    "miami": [
        ("Fort Lauderdale", 28),
        ("Hollywood", 20),
        ("Hialeah", 10),
        ("Pembroke Pines", 25),
        ("Miramar", 20),
        ("Coral Springs", 40),
        ("Miami Gardens", 15),
        ("Pompano Beach", 35),
        ("West Palm Beach", 70),
        ("Boca Raton", 44),
        ("Deerfield Beach", 40),
        ("Boynton Beach", 60),
        ("Plantation", 30),
        ("Sunrise", 30),
        ("Miami Beach", 5),
        ("Kendall", 15),
        ("Homestead", 35),
        ("North Miami", 10),
        ("North Miami Beach", 15),
        ("Aventura", 18)
    ],
    "atlanta": [
        ("Marietta", 20),
        ("Alpharetta", 26),
        ("Decatur", 7),
        ("Smyrna", 15),
        ("Dunwoody", 15),
        ("Sandy Springs", 16),
        ("Roswell", 22),
        ("Johns Creek", 27),
        ("Kennesaw", 27),
        ("Duluth", 22),
        ("Lawrenceville", 30),
        ("Norcross", 16),
        ("Douglasville", 20),
        ("Stockbridge", 20),
        ("Woodstock", 30),
        ("Conyers", 24),
        ("Fayetteville", 22),
        ("McDonough", 30),
        ("Newnan", 40),
        ("Peachtree City", 31)
    ],
    "austin": [
        ("Round Rock", 18),
        ("Cedar Park", 16),
        ("Georgetown", 27),
        ("San Marcos", 30),
        ("Pflugerville", 15),
        ("Leander", 25),
        ("Kyle", 20),
        ("Buda", 15),
        ("Lockhart", 30),
        ("Taylor", 40),
        ("Bastrop", 30),
        ("Dripping Springs", 25),
        ("Wimberley", 28),
        ("Lago Vista", 25),
        ("Bee Cave", 12),
        ("Lakeway", 20),
        ("Manor", 12),
        ("Hutto", 25),
        ("Elgin", 25),
        ("Marble Falls", 45)
    ],
    "seattle": [
        ("Bellevue", 10),
        ("Tacoma", 33),
        ("Everett", 28),
        ("Kent", 19),
        ("Renton", 11),
        ("Kirkland", 12),
        ("Redmond", 15),
        ("Sammamish", 20),
        ("Shoreline", 9),
        ("Burien", 8),
        ("Lynnwood", 16),
        ("Bothell", 15),
        ("Issaquah", 18),
        ("Edmonds", 15),
        ("Auburn", 28),
        ("Federal Way", 22),
        ("Tukwila", 11),
        ("Woodinville", 20),
        ("Mercer Island", 8),
        ("SeaTac", 13)
    ]
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