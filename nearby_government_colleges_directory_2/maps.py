import folium

# Create map centered at input location
m = folium.Map(location=[location.latitude, location.longitude], zoom_start=13)

# Add a marker for user location
folium.Marker(
    [location.latitude, location.longitude],
    popup="You are here",
    icon=folium.Icon(color="blue")
).add_to(m)

# Add markers for nearby colleges
for college in colleges:
    lat = college['lat']
    lon = college['lon']
    name = college['tags'].get('name', 'Unnamed College')
    folium.Marker(
        [lat, lon],
        popup=name,
        icon=folium.Icon(color="green", icon="graduation-cap", prefix='fa')
    ).add_to(m)

# Save map to HTML
m.save("colleges_map.html")