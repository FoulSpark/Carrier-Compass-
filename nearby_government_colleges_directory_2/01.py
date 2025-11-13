from geopy.geocoders import Nominatim

geolocator = Nominatim(user_agent="college_locator")

location = geolocator.geocode("Bhopal, India")
print(location.latitude, location.longitude)