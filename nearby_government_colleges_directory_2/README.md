# Government College Locator 🏛️

A Python application that finds nearby government colleges and universities based on a given location and displays them on an interactive map.

## Features

- **Location-based Search**: Enter any location (city, state, country) to find nearby government colleges
- **Interactive Map**: Visual representation of colleges with detailed information popups
- **Comprehensive Data**: Shows college name, type, operator, address, phone, and website
- **Customizable Radius**: Set your own search radius (default: 5 km)
- **User-friendly Interface**: Simple command-line interface with clear instructions

## Installation

1. **Clone or download** this repository to your local machine

2. **Install required dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Interactive Mode (Recommended)

Run the main application:
```bash
python college_locator.py
```

Follow the on-screen prompts:
1. Choose option 1 to search for colleges
2. Enter your location (e.g., "Bhopal, India")
3. Enter search radius in km (or press Enter for default 5 km)
4. View the results and open the generated HTML map

### Programmatic Usage

You can also use the `CollegeLocator` class in your own Python scripts:

```python
from college_locator import CollegeLocator

# Initialize the locator
locator = CollegeLocator()

# Find colleges near a specific location
locator.find_colleges("Delhi, India", radius=10000)  # 10 km radius
```

### Example Script

Run the example script to see the application in action:
```bash
python example_usage.py
```

## Output

The application provides:

1. **Console Output**: List of found colleges with details like:
   - College/University name
   - Type (College/University)
   - Operator (Government)
   - Address
   - Phone number
   - Website
   - Coordinates

2. **Interactive HTML Map**: 
   - Blue marker: Your location
   - Green markers: Universities
   - Red markers: Colleges
   - Clickable popups with detailed information
   - Legend for easy identification

## Data Source

The application uses the **Overpass API** to query OpenStreetMap data for government colleges and universities. It searches for:
- `amenity=college` with `operator~"government"`
- `amenity=university` with `operator~"government"`

## Requirements

- Python 3.7+
- requests
- folium
- geopy

## File Structure

```
maps/
├── college_locator.py      # Main application
├── example_usage.py        # Example usage script
├── requirements.txt        # Python dependencies
├── README.md              # This file
└── colleges_map_*.html    # Generated map files
```

## Troubleshooting

- **No colleges found**: Try increasing the search radius or checking a different location
- **Location not found**: Make sure to include country name (e.g., "Bhopal, India")
- **Map not opening**: Check that the HTML file was created and open it in a web browser

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve this application!

## License

This project is open source and available under the MIT License.
