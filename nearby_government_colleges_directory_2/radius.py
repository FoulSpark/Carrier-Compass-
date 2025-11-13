import requests

def get_nearby_colleges(lat, lon, radius=5000):  # radius in meters
    overpass_url = "http://overpass-api.de/api/interpreter"
    query = f"""
    [out:json];
    node(around:{radius},{lat},{lon})["amenity"="college"]["operator"~"government",i];
    out;
    """
    response = requests.get(overpass_url, params={'data': query})
    data = response.json()
    return data['elements']

# Example:
colleges = get_nearby_colleges(location.latitude, location.longitude)
for college in colleges:
    print(college['tags'].get('name', 'Unnamed College'))