import requests
import folium
from geopy.geocoders import Nominatim
import json
import os
import webbrowser
from typing import List, Dict, Optional, Tuple

class CollegeLocator:
    def __init__(self):
        self.geolocator = Nominatim(user_agent="college_locator")
        self.overpass_url = "http://overpass-api.de/api/interpreter"
        # Fast mirrors list to reduce waiting time and improve reliability
        self.overpass_mirrors = [
            "https://overpass.kumi.systems/api/interpreter",
            "https://overpass.openstreetmap.ru/api/interpreter",
            "https://overpass.nchc.org.tw/api/interpreter",
            "https://overpass-api.nextzen.org/api/interpreter",
            self.overpass_url,
        ]
        
        # Pre-defined coordinates for fast injection (no geocoding needed)
        self.jabalpur_colleges = {
            'jec': {
                'name': 'Jabalpur Engineering College',
                'lat': 23.1815,
                'lon': 79.9864,
                'amenity': 'college',
                'operator': 'Government of Madhya Pradesh',
                'website': 'https://www.jecjabalpur.ac.in/',
                'addr': 'Gokalpur, Jabalpur, Madhya Pradesh 482011, India',
                'phone': '',
                'tags': {'name': 'Jabalpur Engineering College', 'amenity': 'college'}
            },
            'nscb': {
                'name': 'NSCB Medical College (Netaji Subhash Chandra Bose Medical College)',
                'lat': 23.1510,
                'lon': 79.8815,
                'amenity': 'college',
                'operator': 'Government of Madhya Pradesh',
                'website': 'https://nscbmc.ac.in/',
                'addr': 'Jabalpur, Madhya Pradesh, India',
                'phone': '',
                'tags': {'name': 'NSCB Medical College', 'amenity': 'college'}
            },
            'mahakaushal': {
                'name': 'Mahakaushal Government Autonomous College',
                'lat': 23.1685,
                'lon': 79.9338,
                'amenity': 'college',
                'operator': 'Government of Madhya Pradesh',
                'website': '',
                'addr': 'Jabalpur, Madhya Pradesh, India',
                'phone': '',
                'tags': {'name': 'Mahakaushal Government Autonomous College', 'amenity': 'college'}
            }
        }
        
        # Simple cache for coordinates
        self.coordinate_cache = {}

    def _query_overpass_first_success(self, query: str, timeout_seconds: int = 8) -> Optional[dict]:
        """Query multiple Overpass mirrors and return the first successful JSON response."""
        last_error = None
        for base_url in self.overpass_mirrors:
            try:
                response = requests.get(base_url, params={'data': query}, timeout=timeout_seconds)
                response.raise_for_status()
                return response.json()
            except Exception as error:
                last_error = error
                continue
        if last_error:
            raise last_error
        return None

    def _inject_jec_if_jabalpur(self, colleges: List[Dict], context_location: str, stream: str = 'all') -> None:
        """
        Ensure Jabalpur Engineering College is included for Jabalpur searches.
        Modifies the provided colleges list in-place.
        """
        if not context_location or 'jabalpur' not in context_location.lower():
            return

        # Inject for engineering-relevant streams and 'all' stream
        if stream and stream.lower() not in ['all', 'pcm']:
            return

        # Skip if already present
        for existing in colleges:
            existing_name = existing.get('name', '').lower()
            if 'jabalpur engineering college' in existing_name or existing_name.strip() == 'jec':
                return

        # Use pre-defined coordinates (no geocoding needed)
        colleges.append(self.jabalpur_colleges['jec'].copy())
        print("✅ Injected Jabalpur Engineering College into results (fast).")

    def _inject_nscb_if_jabalpur(self, colleges: List[Dict], context_location: str, stream: str = 'all') -> None:
        """
        Ensure NSCB Medical College is included for Jabalpur PCB searches.
        Modifies the provided colleges list in-place.
        """
        if not context_location or 'jabalpur' not in context_location.lower():
            return

        # Inject for PCB stream and 'all' stream
        if stream and stream.lower() not in ['all', 'pcb']:
            return

        # Skip if already present
        for existing in colleges:
            existing_name = existing.get('name', '').lower()
            if 'nscb' in existing_name or 'netaji subhash chandra bose medical college' in existing_name or 'netaji subhas chandra bose medical college' in existing_name:
                return

        # Avoid duplicate by proximity (very close existing point)
        nscb_data = self.jabalpur_colleges['nscb']
        for existing in colleges:
            try:
                elat = float(existing.get('lat') or 0)
                elon = float(existing.get('lon') or 0)
                if abs(elat - nscb_data['lat']) < 0.0005 and abs(elon - nscb_data['lon']) < 0.0005:
                    return
            except Exception:
                pass

        colleges.append(nscb_data.copy())
        print("✅ Injected NSCB Medical College (fast) into results for PCB stream.")

    def _inject_mahakaushal_if_jabalpur(self, colleges: List[Dict], context_location: str, stream: str = 'all') -> None:
        """
        Ensure Mahakaushal Government Autonomous College is included for Jabalpur
        Arts/Commerce/All searches.
        """
        if not context_location or 'jabalpur' not in context_location.lower():
            return

        if stream and stream.lower() not in ['all', 'arts', 'commerce']:
            return

        for existing in colleges:
            existing_name = existing.get('name', '').lower()
            if 'mahakaushal' in existing_name and 'college' in existing_name:
                return

        # Use pre-defined coordinates (no geocoding needed)
        colleges.append(self.jabalpur_colleges['mahakaushal'].copy())
        print("✅ Injected Mahakaushal Government College into results (fast).")

    def _filter_colleges_by_stream(self, colleges: List[Dict], stream: str) -> List[Dict]:
        """Filter colleges by academic stream preference (pcm/pcb/all)."""
        normalized = (stream or 'all').strip().lower()
        if normalized in ['', 'all']:
            return colleges

        name_keywords_engineering = [
            'engineering', 'institute of technology', 'technology', 'polytechnic', 'iit', 'nit',
            'iiit', 'technical', 'engineering college'
        ]
        name_keywords_medical = [
            'medical', 'medicine', 'aiims', 'mbbs', 'dental', 'nursing', 'pharmacy', 'physiotherapy',
            'ayush', 'ayurveda', 'homeopathy', 'unani'
        ]
        name_keywords_arts = [
            'arts', 'fine arts', 'humanities', 'social sciences', 'liberal arts'
        ]
        name_keywords_commerce = [
            'commerce', 'b.com', 'bcom', 'bba', 'business', 'management', 'accounting', 'finance'
        ]
        generic_govt_college_keywords = [
            'government college', 'govt college', 'government autonomous college', 'govt. college',
            'government degree college'
        ]

        filtered: List[Dict] = []
        for c in colleges:
            name_l = c.get('name', '').lower()
            tags = c.get('tags', {}) or {}
            amenity = (tags.get('amenity') or c.get('amenity', '')).lower()

            if normalized == 'pcm':
                if any(k in name_l for k in name_keywords_engineering):
                    filtered.append(c)
            elif normalized == 'pcb':
                # For PCB, include government colleges but exclude specified non-medical ones
                excluded_pcb_names = [
                    'mahakaushal',
                    'mahakoushal',
                    'chanchala bai',
                    'chanchal bai',
                    'iiitdm',
                    'indian institute of information technology design and manufacturing',
                    'government model science college',
                    'government model sciecne college',
                    'govt model science college'
                ]
                if any(ex in name_l for ex in excluded_pcb_names):
                    continue
                filtered.append(c)
            elif normalized == 'arts':
                if any(k in name_l for k in name_keywords_arts):
                    filtered.append(c)
                else:
                    # Include generic govt colleges that are not clearly engineering/medical
                    if any(k in name_l for k in generic_govt_college_keywords) and not any(
                        k in name_l for k in (name_keywords_engineering + name_keywords_medical)
                    ):
                        filtered.append(c)
            elif normalized == 'commerce':
                # Exclude specified non-relevant college for Commerce stream
                excluded_commerce_names = [
                    'government college of educational psychology and guidance',
                    'educational psychology and guidance',
                    'college of educational psychology and guidance'
                ]
                if any(ex in name_l for ex in excluded_commerce_names):
                    continue
                if any(k in name_l for k in name_keywords_commerce):
                    filtered.append(c)
                else:
                    # Include generic govt colleges that are not clearly engineering/medical
                    if any(k in name_l for k in generic_govt_college_keywords) and not any(
                        k in name_l for k in (name_keywords_engineering + name_keywords_medical)
                    ):
                        filtered.append(c)

        # If filtering removed everything, fall back to the full government list
        return filtered if filtered else colleges

    def is_government_college(self, tags: Dict) -> bool:
        operator = tags.get('operator', '').lower()
        name = tags.get('name', '').lower()
        ownership = tags.get('ownership', '').lower()
        operator_type = tags.get('operator:type', '').lower()
        funding = tags.get('funding', '').lower()
        amenity = tags.get('amenity', '').lower()
        
        government_keywords = [
            'government', 'govt', 'public', 'state', 'central', 'national',
            'ministry', 'department', 'commission', 'board', 'council',
            'university grants commission', 'ugc', 'aicte', 'mhrd',
            'madhya pradesh', 'mp government', 'state government',
            'central government', 'union government', 'indian government'
            ,'JEC'
        ]
        
        private_keywords = [
            'private', 'pvt', 'ltd', 'limited', 'trust', 'society',
            'foundation', 'corporate', 'commercial', 'profit', 'pvt ltd',
            'private limited', 'private college', 'private university'
        ]

        # Explicit exclusions for well-known private institutions by name
        explicit_private_names = [
            'st aloysius', 'st. aloysius', 'saint aloysius',
            'st aloysious', 'st. aloysious', 'saint aloysious'
        ]
        if any(excluded in name for excluded in explicit_private_names):
            return False
        
        is_govt = (
            operator_type == 'government' or
            ownership == 'public' or
            funding == 'public' or
            any(keyword in operator for keyword in government_keywords) or
            any(keyword in name for keyword in government_keywords) or
            'govt' in name or
            'government' in name or
            'state' in name or
            'central' in name or
            'national' in name
        )
        
        special_govt_cases = [
            'iit', 'iim', 'nit', 'iisc', 'tifr', 'isro', 'dae', 'barc',
            'indian institute', 'national institute', 'central university',
            'state university', 'government college', 'govt college',
            'university', 'college', 'institute', 'academy', 'school',
            'polytechnic', 'engineering college', 'medical college',
            'agricultural university', 'technical university'
        ]
      
        is_educational = amenity in ['college', 'university'] or any(case in name for case in special_govt_cases)
        
        is_private = any(keyword in operator for keyword in private_keywords) or \
                    any(keyword in name for keyword in private_keywords)
        
        is_special_govt = any(case in name for case in special_govt_cases)
        
        return (is_govt or is_special_govt) and not is_private



    def get_live_location(self) -> Optional[Tuple[float, float, str]]:
        """
        Get user's live location using multiple geolocation services for better accuracy.
        
        Returns:
            Tuple[float, float, str]: (latitude, longitude, location_name) or None if not found
        """
        services = [
            ('http://ip-api.com/json/', self._parse_ipapi_response),
            ('http://ipinfo.io/json', self._parse_ipinfo_response),
            ('https://ipapi.co/json/', self._parse_ipapi_co_response)
        ]
        
        for url, parser in services:
            try:
                response = requests.get(url, timeout=3)  # Reduced from 10 to 3 seconds
                if response.status_code == 200:
                    data = response.json()
                    result = parser(data)
                    if result:
                        lat, lon, location_name = result
                        print(f"📍 Location detected via {url}: {location_name}")
                        return (lat, lon, location_name)
            except Exception as e:
                print(f"Service {url} failed: {e}")
                continue
        
        print("❌ All geolocation services failed")
        return None
    
    def _parse_ipapi_response(self, data: dict) -> Optional[Tuple[float, float, str]]:
        """Parse response from ip-api.com"""
        if data.get('status') == 'success':
            lat = data['lat']
            lon = data['lon']
            city = data.get('city', 'Unknown')
            region = data.get('regionName', '')
            country = data.get('country', '')
            
            # Override Bhopal with Jabalpur coordinates and location
            if city.lower() == 'bhopal':
                city = 'Jabalpur'
                lat = 23.1815  # Jabalpur coordinates
                lon = 79.9864
                print("📍 Location override: Bhopal detected, using Jabalpur instead")
            
            location_name = f"{city}, {region}, {country}".strip(', ')
            return (lat, lon, location_name)
        return None
    
    def _parse_ipinfo_response(self, data: dict) -> Optional[Tuple[float, float, str]]:
        """Parse response from ipinfo.io"""
        if 'loc' in data:
            lat, lon = map(float, data['loc'].split(','))
            city = data.get('city', 'Unknown')
            region = data.get('region', '')
            country = data.get('country', '')
            
            # Override Bhopal with Jabalpur coordinates and location
            if city.lower() == 'bhopal':
                city = 'Jabalpur'
                lat = 23.1815  # Jabalpur coordinates
                lon = 79.9864
                print("📍 Location override: Bhopal detected, using Jabalpur instead")
            
            location_name = f"{city}, {region}, {country}".strip(', ')
            return (lat, lon, location_name)
        return None
    
    def _parse_ipapi_co_response(self, data: dict) -> Optional[Tuple[float, float, str]]:
        """Parse response from ipapi.co"""
        if 'latitude' in data and 'longitude' in data:
            lat = data['latitude']
            lon = data['longitude']
            city = data.get('city', 'Unknown')
            region = data.get('region', '')
            country = data.get('country_name', '')
            
            # Override Bhopal with Jabalpur coordinates and location
            if city.lower() == 'bhopal':
                city = 'Jabalpur'
                lat = 23.1815  # Jabalpur coordinates
                lon = 79.9864
                print("📍 Location override: Bhopal detected, using Jabalpur instead")
            
            location_name = f"{city}, {region}, {country}".strip(', ')
            return (lat, lon, location_name)
        return None

    def get_coordinates(self, location: str) -> Optional[Tuple[float, float]]:
        """
        Get latitude and longitude coordinates for a given location with improved accuracy.
        
        Args:
            location (str): Location name (e.g., "Bhopal, India")
            
        Returns:
            Tuple[float, float]: (latitude, longitude) or None if not found
        """
        # Check cache first
        cache_key = location.lower().strip()
        if cache_key in self.coordinate_cache:
            print(f"📍 Using cached coordinates for: {location}")
            return self.coordinate_cache[cache_key]
        
        search_terms = [
            location,
            f"{location}, India",
            f"{location}, Madhya Pradesh, India",
            f"{location}, MP, India"
        ]
        
        for search_term in search_terms:
            try:
                print(f"🔍 Searching for: {search_term}")
                location_data = self.geolocator.geocode(search_term, timeout=5)  # Reduced from 10 to 5
                if location_data:
                    lat, lon = location_data.latitude, location_data.longitude
                    # Cache the result
                    self.coordinate_cache[cache_key] = (lat, lon)
                    print(f"✅ Found coordinates: {lat:.6f}, {lon:.6f}")
                    return (lat, lon)
            except Exception as e:
                print(f"Error geocoding '{search_term}': {e}")
                continue
        
        print(f"❌ Location '{location}' not found with any search term.")
        print("💡 Try being more specific (e.g., 'Jabalpur, Madhya Pradesh, India')")
        return None
    
    def get_nearby_colleges(self, lat: float, lon: float, radius: int = 5000, stream: str = 'all') -> List[Dict]:
        """
        Find nearby government colleges/universities using Overpass API with improved queries.
        """
        try:
            # Fast, simpler query first for quick results
            pcb = (stream or 'all').lower() == 'pcb'
            # PCB now fetches all colleges/universities in the requested radius, then filters to medical
            fast_query = f"""
            [out:json][timeout:{6 if pcb else 8}];
            (
              node(around:{radius},{lat},{lon})["amenity"~"^(college|university)$"];
              way(around:{radius},{lat},{lon})["amenity"~"^(college|university)$"];
              relation(around:{radius},{lat},{lon})["amenity"~"^(college|university)$"];
            );
            out center;
            """

            full_query = f"""
            [out:json];
            (
            // Primary search for colleges and universities
            node(around:{radius},{lat},{lon})["amenity"~"^(college|university)$"];
            way(around:{radius},{lat},{lon})["amenity"~"^(college|university)$"];
            relation(around:{radius},{lat},{lon})["amenity"~"^(college|university)$"];
            
            // Alternative tagging patterns
            node(around:{radius},{lat},{lon})["office"="educational_institution"];
            way(around:{radius},{lat},{lon})["office"="educational_institution"];
            relation(around:{radius},{lat},{lon})["office"="educational_institution"];
            
            // Schools that might be colleges
            node(around:{radius},{lat},{lon})["amenity"="school"]["name"~"(college|university|institute|academy)",i];
            way(around:{radius},{lat},{lon})["amenity"="school"]["name"~"(college|university|institute|academy)",i];
            relation(around:{radius},{lat},{lon})["amenity"="school"]["name"~"(college|university|institute|academy)",i];
            
            // Engineering and technical institutions
            node(around:{radius},{lat},{lon})["name"~"(engineering|technical|polytechnic|medical|agricultural)",i];
            way(around:{radius},{lat},{lon})["name"~"(engineering|technical|polytechnic|medical|agricultural)",i];
            relation(around:{radius},{lat},{lon})["name"~"(engineering|technical|polytechnic|medical|agricultural)",i];

            // Skip hospital fetch for PCB to keep query light
            );
            out center;
            """

            print(f"Querying Overpass (fast) for {radius/1000:.1f} km radius...")
            try:
                data = self._query_overpass_first_success(fast_query, timeout_seconds=(6 if pcb else 8))
            except Exception:
                if pcb:
                    print("Fast PCB query failed; skipping heavy full query to avoid timeouts.")
                    data = {'elements': []}
                else:
                    print("Fast query failed or timed out. Trying simplified query...")
                    # Use a much simpler query for fallback
                    simple_query = f"""
                    [out:json][timeout:5];
                    (
                      node(around:{min(radius, 10000)},{lat},{lon})["amenity"="college"];
                      node(around:{min(radius, 10000)},{lat},{lon})["amenity"="university"];
                    );
                    out;
                    """
                    try:
                        data = self._query_overpass_first_success(simple_query, timeout_seconds=5)
                    except Exception:
                        data = {'elements': []}

            # If PCB and still no elements, try a tiny targeted retry
            if pcb and (not data or not data.get('elements')):
                print("PCB: No results from fast query. Trying tiny targeted retry...")
                tiny_radius = min(radius, 5000)
                pcb_retry_query = f"""
                [out:json][timeout:8];
                (
                  node(around:{tiny_radius},{lat},{lon})["amenity"~"^(college|university)$"]["name"~"(medical|medical college|aiims|dental|nursing|pharmacy)",i];
                  way(around:{tiny_radius},{lat},{lon})["amenity"~"^(college|university)$"]["name"~"(medical|medical college|aiims|dental|nursing|pharmacy)",i];
                  relation(around:{tiny_radius},{lat},{lon})["amenity"~"^(college|university)$"]["name"~"(medical|medical college|aiims|dental|nursing|pharmacy)",i];
                );
                out center;
                """
                try:
                    data = self._query_overpass_first_success(pcb_retry_query, timeout_seconds=8)
                except Exception:
                    data = {'elements': []}

            # If non-PCB and no elements, attempt a basic retry with slightly larger radius
            if not pcb and (not data or not data.get('elements')):
                print("No results from fast query. Retrying with slightly larger radius...")
                retry_radius = min(radius + 3000, 15000)
                basic_retry = f"""
                [out:json][timeout:15];
                (
                  node(around:{retry_radius},{lat},{lon})["amenity"~"^(college|university)$"];
                  way(around:{retry_radius},{lat},{lon})["amenity"~"^(college|university)$"];
                  relation(around:{retry_radius},{lat},{lon})["amenity"~"^(college|university)$"];
                );
                out center;
                """
                try:
                    data = self._query_overpass_first_success(basic_retry, timeout_seconds=15)
                except Exception:
                    data = {'elements': []}

            colleges = []
            for element in data.get('elements', []):
                if 'tags' not in element:
                    continue

               
                if not self.is_government_college(element['tags']):
                    continue 

                lat_coord = element.get('lat') or element.get('center', {}).get('lat')
                lon_coord = element.get('lon') or element.get('center', {}).get('lon')

                if not lat_coord or not lon_coord:
                    continue

                college_data = {
                    'name': element['tags'].get('name', 'Unnamed College'),
                    'lat': lat_coord,
                    'lon': lon_coord,
                    'amenity': element['tags'].get('amenity', 'college'),
                    'operator': element['tags'].get('operator', 'Unknown'),
                    'website': element['tags'].get('website', ''),
                    'addr': element['tags'].get('addr:full', element['tags'].get('addr:street', '')),
                    'phone': element['tags'].get('phone', ''),
                    'tags': element['tags']
                }
                colleges.append(college_data)
                print(f"✅ Found Govt College: {college_data['name']} ({college_data['operator']})")

            print(f"Total government colleges found: {len(colleges)}")
            return colleges

        except requests.exceptions.RequestException as e:
            print(f"Error fetching college data: {e}")
            print("Trying fallback method...")
            return self._fallback_college_search(lat, lon, radius)
        except Exception as e:
            print(f"Unexpected error: {e}")
            return []

    
    def _fallback_college_search(self, lat: float, lon: float, radius: int) -> List[Dict]:
        """
        Fallback method using a simpler query if the main search fails.
        """
        try:
            query = f"""
            [out:json];
            (
            node(around:{radius},{lat},{lon})["amenity"~"^(college|university)$"];
            way(around:{radius},{lat},{lon})["amenity"~"^(college|university)$"];
            relation(around:{radius},{lat},{lon})["amenity"~"^(college|university)$"];
            );
            out center;
            """
            print("Trying fallback search...")
            response = requests.get(self.overpass_url, params={'data': query}, timeout=30)
            response.raise_for_status()
            data = response.json()

            colleges = []
            for element in data.get('elements', []):
                if 'tags' not in element:
                    continue
                if not self.is_government_college(element['tags']):
                    continue  # filter out private ones

                lat_coord = element.get('lat') or element.get('center', {}).get('lat')
                lon_coord = element.get('lon') or element.get('center', {}).get('lon')

                if lat_coord and lon_coord:
                    college_data = {
                        'name': element['tags'].get('name', 'Unnamed College'),
                        'lat': lat_coord,
                        'lon': lon_coord,
                        'amenity': element['tags'].get('amenity', 'college'),
                        'operator': element['tags'].get('operator', 'Unknown'),
                        'website': element['tags'].get('website', ''),
                        'addr': element['tags'].get('addr:full', element['tags'].get('addr:street', '')),
                        'phone': element['tags'].get('phone', ''),
                        'tags': element['tags']
                    }
                    colleges.append(college_data)
                    print(f"Fallback ✅ Govt College: {college_data['name']}")

            return colleges

        except Exception as e:
            print(f"Fallback search also failed: {e}")
            return []

    
    def create_map(self, user_lat: float, user_lon: float, colleges: List[Dict], 
                   location_name: str = "Your Location", radius: int = 10000) -> str:
        """
        Create an interactive map showing the user location and nearby colleges.
        
        Args:
            user_lat (float): User's latitude
            user_lon (float): User's longitude
            colleges (List[Dict]): List of college data
            location_name (str): Name of the user's location
            
        Returns:
            str: Path to the saved HTML map file
        """
        try:
            m = folium.Map(
                location=[user_lat, user_lon], 
                zoom_start=12,
                tiles='OpenStreetMap'
            )
         
            user_popup = f"""
            <div style="width: 200px;">
                <h4>📍 Your Location</h4>
                <p><strong>Location:</strong> {location_name}</p>
                <p><strong>Coordinates:</strong> {user_lat:.6f}, {user_lon:.6f}</p>
                <p><strong>Nearby Colleges:</strong> {len(colleges)} found</p>
            </div>
            """
            
            folium.Marker(
                [user_lat, user_lon],
                popup=folium.Popup(user_popup, max_width=250),
                tooltip="📍 Your Location",
                icon=folium.Icon(color="blue", icon="user", prefix='fa')
            ).add_to(m)
            
            folium.Circle(
                location=[user_lat, user_lon],
                radius=radius,
                popup=f"{radius/1000:.1f}km Search Radius",
                color="blue",
                fill=False,
                weight=2
            ).add_to(m)
            
            # Add college markers
            for i, college in enumerate(colleges, 1):
                # Create popup content
                popup_content = f"""
                <div style="width: 250px;">
                    <h4>{college['name']}</h4>
                    <p><strong>Type:</strong> {college['amenity'].title()}</p>
                    <p><strong>Operator:</strong> {college['operator']}</p>
                """
                
                if college['addr']:
                    popup_content += f"<p><strong>Address:</strong> {college['addr']}</p>"
                if college['phone']:
                    popup_content += f"<p><strong>Phone:</strong> {college['phone']}</p>"
                if college['website']:
                    popup_content += f"<p><strong>Website:</strong> <a href='{college['website']}' target='_blank'>Visit Website</a></p>"
                
                popup_content += "</div>"
                
                # Choose icon based on amenity type
                icon_color = "green" if college['amenity'] == 'university' else "red"
                icon_name = "university" if college['amenity'] == 'university' else "graduation-cap"
                
                folium.Marker(
                    [college['lat'], college['lon']],
                    popup=folium.Popup(popup_content, max_width=300),
                    tooltip=f"{i}. {college['name']}",
                    icon=folium.Icon(color=icon_color, icon=icon_name, prefix='fa')
                ).add_to(m)
            
            # Add a legend
            legend_html = '''
            <div style="position: fixed; 
                        bottom: 50px; left: 50px; width: 150px; height: 90px; 
                        background-color: white; border:2px solid grey; z-index:9999; 
                        font-size:14px; padding: 10px">
            <p><b>Legend</b></p>
            <p><i class="fa fa-user" style="color:blue"></i> Your Location</p>
            <p><i class="fa fa-university" style="color:green"></i> University</p>
            <p><i class="fa fa-graduation-cap" style="color:red"></i> College</p>
            </div>
            '''
            m.get_root().html.add_child(folium.Element(legend_html))
            
            # Save map
            map_filename = f"colleges_map_{location_name.replace(' ', '_').replace(',', '')}.html"
            m.save(map_filename)
            return map_filename
            
        except Exception as e:
            print(f"Error creating map: {e}")
            return ""
    
    def display_colleges(self, colleges: List[Dict]) -> None:
        """
        Display college information in a formatted way.
        
        Args:
            colleges (List[Dict]): List of college data
        """
        if not colleges:
            print("No government colleges found in the specified area.")
            return
        
        print(f"\n{'='*60}")
        print(f"FOUND {len(colleges)} GOVERNMENT COLLEGES/UNIVERSITIES")
        print(f"{'='*60}")
        
        for i, college in enumerate(colleges, 1):
            print(f"\n{i}. {college['name']}")
            print(f"   Type: {college['amenity'].title()}")
            print(f"   Operator: {college['operator']}")
            if college['addr']:
                print(f"   Address: {college['addr']}")
            if college['phone']:
                print(f"   Phone: {college['phone']}")
            if college['website']:
                print(f"   Website: {college['website']}")
            print(f"   Coordinates: {college['lat']:.6f}, {college['lon']:.6f}")
    
    def find_colleges_with_coords(self, lat: float, lon: float, location_name: str, radius: int = 10000, stream: str = 'all') -> None:
        """
        Find and display nearby government colleges using provided coordinates.
        
        Args:
            lat (float): Latitude
            lon (float): Longitude
            location_name (str): Name of the location
            radius (int): Search radius in meters
        """
        print(f"Searching for government colleges near: {location_name}")
        print(f"Search radius: {radius/1000:.1f} km")
        print(f"Coordinates: {lat:.6f}, {lon:.6f}")
        
        # Find nearby colleges
        print("\nFetching college data...")
        colleges = self.get_nearby_colleges(lat, lon, radius, stream)
        # Ensure JEC appears for Jabalpur when relevant
        self._inject_jec_if_jabalpur(colleges, location_name, stream)
        # Ensure NSCB appears for Jabalpur when relevant
        self._inject_nscb_if_jabalpur(colleges, location_name, stream)
        # Ensure Mahakaushal appears for Jabalpur when relevant
        self._inject_mahakaushal_if_jabalpur(colleges, location_name, stream)
        # Apply stream filter
        colleges = self._filter_colleges_by_stream(colleges, stream)
        
        # Display results
        self.display_colleges(colleges)
        
        # Create map
        if colleges:
            print(f"\nCreating interactive map...")
            map_file = self.create_map(lat, lon, colleges, location_name, radius)
            if map_file:
                print(f"Map saved as: {map_file}")
                print(f"Open {map_file} in your web browser to view the interactive map!")
                # Try to open the map automatically
                try:
                    webbrowser.open(f"file://{os.path.abspath(map_file)}")
                    print("🌐 Map opened in your default browser!")
                except:
                    print("Please manually open the map file in your browser.")
        else:
            print("\nNo government colleges found. Try increasing the search radius or checking a different location.")

    def find_colleges(self, location: str, radius: int = 10000, stream: str = 'all') -> None:
        """
        Main method to find and display nearby government colleges.
        
        Args:
            location (str): Location to search from
            radius (int): Search radius in meters
        """
        print(f"Searching for government colleges near: {location}")
        print(f"Search radius: {radius/1000:.1f} km")
        
        # Get coordinates
        coords = self.get_coordinates(location)
        if not coords:
            return
        
        lat, lon = coords
        print(f"Coordinates: {lat:.6f}, {lon:.6f}")
        
        # Find nearby colleges
        print("\nFetching college data...")
        colleges = self.get_nearby_colleges(lat, lon, radius, stream)
        # Ensure JEC appears for Jabalpur when relevant
        self._inject_jec_if_jabalpur(colleges, location, stream)
        # Ensure NSCB appears for Jabalpur when relevant
        self._inject_nscb_if_jabalpur(colleges, location, stream)
        # Ensure Mahakaushal appears for Jabalpur when relevant
        self._inject_mahakaushal_if_jabalpur(colleges, location, stream)
        # Apply stream filter
        colleges = self._filter_colleges_by_stream(colleges, stream)
        
        # Display results
        self.display_colleges(colleges)
        
        # Create map
        if colleges:
            print(f"\nCreating interactive map...")
            map_file = self.create_map(lat, lon, colleges, location, radius)
            if map_file:
                print(f"Map saved as: {map_file}")
                print(f"Open {map_file} in your web browser to view the interactive map!")
                # Try to open the map automatically
                try:
                    webbrowser.open(f"file://{os.path.abspath(map_file)}")
                    print("🌐 Map opened in your default browser!")
                except:
                    print("Please manually open the map file in your browser.")
        else:
            print("\nNo government colleges found. Try increasing the search radius or checking a different location.")


def main():
    """Main function to run the college locator application."""
    print("🏛️  GOVERNMENT COLLEGE LOCATOR 🏛️")
    print("=" * 40)
    
    locator = CollegeLocator()
    
    while True:
        print("\nOptions:")
        print("1. Search for colleges using live location")
        print("2. Search for colleges using custom location")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == '1':
            print("Getting your live location...")
            live_data = locator.get_live_location()
            if live_data:
                lat, lon, location_name = live_data
                print(f"📍 Live location detected: {location_name}")
                print(f"Coordinates: {lat:.6f}, {lon:.6f}")
                
                try:
                    radius_input = input("Enter search radius in km (default: 10): ").strip()
                    radius = int(float(radius_input) * 1000) if radius_input else 10000
                except ValueError:
                    print("Invalid radius. Using default 10 km.")
                    radius = 10000
                stream = input("Enter stream (PCM/PCB/Arts/Commerce/All) [default: All]: ").strip() or 'All'
                
                locator.find_colleges_with_coords(lat, lon, location_name, radius, stream)
            else:
                print("❌ Could not detect live location. Please use option 2 for manual location.")
                
        elif choice == '2':
            location = input("Enter location (e.g., 'Bhopal, India'): ").strip()
            if not location:
                print("Please enter a valid location.")
                continue
            
            try:
                radius_input = input("Enter search radius in km (default: 10): ").strip()
                radius = int(float(radius_input) * 1000) if radius_input else 10000
            except ValueError:
                print("Invalid radius. Using default 10 km.")
                radius = 10000
            stream = input("Enter stream (PCM/PCB/Arts/Commerce/All) [default: All]: ").strip() or 'All'
            
            locator.find_colleges(location, radius, stream)
            
        elif choice == '3':
            print("Thank you for using Government College Locator!")
            break
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")


if __name__ == "__main__":
    main()