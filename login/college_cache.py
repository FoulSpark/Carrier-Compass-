import json
import os
import math
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta

class CollegeCache:
    def __init__(self, cache_file: str = "college_cache.json"):
        """Initialize the college cache system."""
        self.cache_file = cache_file
        self.cache_data = self._load_cache()
        
    def _load_cache(self) -> Dict:
        """Load cache data from JSON file."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Error loading cache: {e}")
                return {"locations": {}, "metadata": {"created": datetime.now().isoformat()}}
        else:
            return {"locations": {}, "metadata": {"created": datetime.now().isoformat()}}
    
    def _save_cache(self):
        """Save cache data to JSON file."""
        try:
            self.cache_data["metadata"]["last_updated"] = datetime.now().isoformat()
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache_data, f, indent=2, ensure_ascii=False)
            print(f"💾 Cache saved to {self.cache_file}")
        except Exception as e:
            print(f"❌ Error saving cache: {e}")
    
    def _generate_location_key(self, lat: float, lon: float, radius: int, stream: str) -> str:
        """Generate a unique key for location-based searches."""
        # Round coordinates to 3 decimal places for grouping nearby searches
        lat_rounded = round(lat, 3)
        lon_rounded = round(lon, 3)
        # Round radius to nearest 1000m for grouping
        radius_rounded = round(radius / 1000) * 1000
        return f"{lat_rounded}_{lon_rounded}_{radius_rounded}_{stream.lower()}"
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates using Haversine formula."""
        R = 6371000  # Earth's radius in meters
        
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def get_cached_colleges(self, lat: float, lon: float, radius: int, stream: str, location_name: str = "") -> Optional[List[Dict]]:
        """
        Get cached colleges for a location if available.
        
        Args:
            lat: Latitude
            lon: Longitude  
            radius: Search radius in meters
            stream: Course stream (pcm, pcb, arts, commerce, all)
            location_name: Name of the location
            
        Returns:
            List of colleges if found in cache, None otherwise
        """
        # Special handling for Bhopal - check by location name first
        if location_name and "bhopal" in location_name.lower():
            # Look for Bhopal entries in cache
            for key, entry in self.cache_data["locations"].items():
                if (entry.get("location_name", "").lower().find("bhopal") != -1 and 
                    entry.get("stream", "").lower() == stream.lower()):
                    
                    cached_time = datetime.fromisoformat(entry["timestamp"])
                    if datetime.now() - cached_time < timedelta(days=7):
                        print(f"✅ Found cached Bhopal colleges for {stream} stream ({len(entry['colleges'])} colleges)")
                        
                        # Update access count and last accessed time
                        entry["access_count"] = entry.get("access_count", 0) + 1
                        entry["last_accessed"] = datetime.now().isoformat()
                        self._save_cache()
                        
                        return entry["colleges"]
        
        cache_key = self._generate_location_key(lat, lon, radius, stream)
        
        if cache_key in self.cache_data["locations"]:
            cached_entry = self.cache_data["locations"][cache_key]
            
            # Check if cache is not too old (7 days)
            cached_time = datetime.fromisoformat(cached_entry["timestamp"])
            if datetime.now() - cached_time < timedelta(days=7):
                print(f"✅ Found cached colleges for {location_name} ({len(cached_entry['colleges'])} colleges)")
                
                # Update access count and last accessed time
                cached_entry["access_count"] = cached_entry.get("access_count", 0) + 1
                cached_entry["last_accessed"] = datetime.now().isoformat()
                self._save_cache()
                
                return cached_entry["colleges"]
            else:
                print(f"⏰ Cache expired for {location_name}, will refresh")
                # Remove expired cache
                del self.cache_data["locations"][cache_key]
                self._save_cache()
        
        # Also check for nearby cached locations (within 2km)
        for key, entry in self.cache_data["locations"].items():
            try:
                parts = key.split('_')
                if len(parts) >= 4:
                    cached_lat = float(parts[0])
                    cached_lon = float(parts[1])
                    cached_radius = int(parts[2])
                    cached_stream = parts[3]
                    
                    # Check if it's the same stream and similar location/radius
                    if (cached_stream == stream.lower() and 
                        abs(cached_radius - radius) <= 2000 and  # Within 2km radius difference
                        self._calculate_distance(lat, lon, cached_lat, cached_lon) <= 2000):  # Within 2km distance
                        
                        cached_time = datetime.fromisoformat(entry["timestamp"])
                        if datetime.now() - cached_time < timedelta(days=7):
                            print(f"✅ Found nearby cached colleges for {location_name}")
                            
                            # Filter colleges by actual radius
                            filtered_colleges = []
                            for college in entry["colleges"]:
                                college_distance = self._calculate_distance(lat, lon, college["lat"], college["lon"])
                                if college_distance <= radius:
                                    filtered_colleges.append(college)
                            
                            if filtered_colleges:
                                entry["access_count"] = entry.get("access_count", 0) + 1
                                entry["last_accessed"] = datetime.now().isoformat()
                                self._save_cache()
                                return filtered_colleges
            except (ValueError, KeyError):
                continue
        
        return None
    
    def cache_colleges(self, lat: float, lon: float, radius: int, stream: str, 
                      colleges: List[Dict], location_name: str = ""):
        """
        Cache colleges for a location.
        
        Args:
            lat: Latitude
            lon: Longitude
            radius: Search radius in meters
            stream: Course stream
            colleges: List of college data
            location_name: Name of the location
        """
        cache_key = self._generate_location_key(lat, lon, radius, stream)
        
        cache_entry = {
            "timestamp": datetime.now().isoformat(),
            "location_name": location_name,
            "lat": lat,
            "lon": lon,
            "radius": radius,
            "stream": stream,
            "colleges": colleges,
            "access_count": 1,
            "last_accessed": datetime.now().isoformat()
        }
        
        self.cache_data["locations"][cache_key] = cache_entry
        self._save_cache()
        
        print(f"💾 Cached {len(colleges)} colleges for {location_name}")
    
    def get_cached_locations(self) -> List[Dict]:
        """Get list of all cached locations with statistics."""
        locations = []
        for key, entry in self.cache_data["locations"].items():
            locations.append({
                "key": key,
                "location_name": entry.get("location_name", "Unknown"),
                "lat": entry.get("lat"),
                "lon": entry.get("lon"),
                "radius": entry.get("radius"),
                "stream": entry.get("stream"),
                "college_count": len(entry.get("colleges", [])),
                "access_count": entry.get("access_count", 0),
                "timestamp": entry.get("timestamp"),
                "last_accessed": entry.get("last_accessed")
            })
        
        # Sort by access count (most frequently accessed first)
        locations.sort(key=lambda x: x["access_count"], reverse=True)
        return locations
    
    def search_cached_colleges(self, query: str, stream: str = "all") -> List[Dict]:
        """Search for colleges in cache by name or location."""
        results = []
        query_lower = query.lower()
        
        for entry in self.cache_data["locations"].values():
            # Skip if stream doesn't match
            if stream != "all" and entry.get("stream", "").lower() != stream.lower():
                continue
                
            # Check if query matches location name
            location_match = query_lower in entry.get("location_name", "").lower()
            
            for college in entry.get("colleges", []):
                # Check if query matches college name
                college_match = query_lower in college.get("name", "").lower()
                
                if location_match or college_match:
                    college_copy = college.copy()
                    college_copy["cached_location"] = entry.get("location_name", "Unknown")
                    college_copy["cache_key"] = self._generate_location_key(
                        entry["lat"], entry["lon"], entry["radius"], entry["stream"]
                    )
                    results.append(college_copy)
        
        return results
    
    def clear_cache(self):
        """Clear all cached data."""
        self.cache_data = {"locations": {}, "metadata": {"created": datetime.now().isoformat()}}
        self._save_cache()
        print("🗑️ Cache cleared")
    
    def clear_expired_cache(self, days: int = 7):
        """Clear cache entries older than specified days."""
        current_time = datetime.now()
        expired_keys = []
        
        for key, entry in self.cache_data["locations"].items():
            try:
                cached_time = datetime.fromisoformat(entry["timestamp"])
                if current_time - cached_time > timedelta(days=days):
                    expired_keys.append(key)
            except (ValueError, KeyError):
                expired_keys.append(key)  # Remove invalid entries
        
        for key in expired_keys:
            del self.cache_data["locations"][key]
        
        if expired_keys:
            self._save_cache()
            print(f"🗑️ Removed {len(expired_keys)} expired cache entries")
        
        return len(expired_keys)
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics."""
        total_locations = len(self.cache_data["locations"])
        total_colleges = sum(len(entry.get("colleges", [])) for entry in self.cache_data["locations"].values())
        
        # Calculate total access count
        total_accesses = sum(entry.get("access_count", 0) for entry in self.cache_data["locations"].values())
        
        # Find most popular location
        most_popular = None
        max_access = 0
        for entry in self.cache_data["locations"].values():
            access_count = entry.get("access_count", 0)
            if access_count > max_access:
                max_access = access_count
                most_popular = entry.get("location_name", "Unknown")
        
        return {
            "total_cached_locations": total_locations,
            "total_cached_colleges": total_colleges,
            "total_accesses": total_accesses,
            "most_popular_location": most_popular,
            "most_popular_access_count": max_access,
            "cache_file_size": os.path.getsize(self.cache_file) if os.path.exists(self.cache_file) else 0
        }
    
    def populate_sample_cache(self):
        """Populate cache with sample data for popular locations."""
        print("🔄 Populating cache with sample college data...")
        
        # Bhopal colleges organized by stream
        bhopal_colleges = {
            "pcm": [
                {
                    "name": "Govt Motilal Vigyan Mahavidyalaya (MVM)",
                    "lat": 23.2599,
                    "lon": 77.4126,
                    "amenity": "college",
                    "operator": "Government of Madhya Pradesh",
                    "website": "",
                    "addr": "Jahangirabad, Bhopal, Madhya Pradesh",
                    "phone": "",
                    "tags": {"name": "Govt Motilal Vigyan Mahavidyalaya", "amenity": "college"}
                },
                {
                    "name": "Government Science and Commerce College",
                    "lat": 23.2550,
                    "lon": 77.4100,
                    "amenity": "college",
                    "operator": "Government of Madhya Pradesh",
                    "website": "",
                    "addr": "Benazir, Jehangirabad, Bhopal, Madhya Pradesh",
                    "phone": "",
                    "tags": {"name": "Government Science and Commerce College", "amenity": "college"}
                },
                {
                    "name": "Government Geetanjali Girls' College",
                    "lat": 23.2620,
                    "lon": 77.4150,
                    "amenity": "college",
                    "operator": "Government of Madhya Pradesh",
                    "website": "",
                    "addr": "Bhopal, Madhya Pradesh",
                    "phone": "",
                    "tags": {"name": "Government Geetanjali Girls' College", "amenity": "college"}
                },
                {
                    "name": "Government Post Graduate College, BHEL",
                    "lat": 23.2400,
                    "lon": 77.4800,
                    "amenity": "college",
                    "operator": "Government of Madhya Pradesh",
                    "website": "",
                    "addr": "Piplani, Bhopal, Madhya Pradesh",
                    "phone": "",
                    "tags": {"name": "Government Post Graduate College, BHEL", "amenity": "college"}
                },
                {
                    "name": "Government College, Bhopal",
                    "lat": 23.2580,
                    "lon": 77.4080,
                    "amenity": "college",
                    "operator": "Government of Madhya Pradesh",
                    "website": "",
                    "addr": "Bhopal, Madhya Pradesh",
                    "phone": "",
                    "tags": {"name": "Government College, Bhopal", "amenity": "college"}
                }
            ],
            "pcb": [
                {
                    "name": "Government Science & Commerce College (GSCC)",
                    "lat": 23.2570,
                    "lon": 77.4120,
                    "amenity": "college",
                    "operator": "Government of Madhya Pradesh",
                    "website": "",
                    "addr": "Bhopal, Madhya Pradesh",
                    "phone": "",
                    "tags": {"name": "Government Science & Commerce College", "amenity": "college"}
                },
                {
                    "name": "Government Dr. Shyama Prasad Mukherjee Science & Commerce College",
                    "lat": 23.2560,
                    "lon": 77.4110,
                    "amenity": "college",
                    "operator": "Government of Madhya Pradesh",
                    "website": "",
                    "addr": "Jahangirabad, Bhopal, Madhya Pradesh",
                    "phone": "",
                    "tags": {"name": "Government Dr. Shyama Prasad Mukherjee Science & Commerce College", "amenity": "college"}
                },
                {
                    "name": "Government PG College - Pipriya",
                    "lat": 23.2450,
                    "lon": 77.3950,
                    "amenity": "college",
                    "operator": "Government of Madhya Pradesh",
                    "website": "",
                    "addr": "Pipriya, Bhopal, Madhya Pradesh",
                    "phone": "",
                    "tags": {"name": "Government PG College - Pipriya", "amenity": "college"}
                }
            ],
            "arts": [
                {
                    "name": "Government Hamidia Arts & Commerce College",
                    "lat": 23.2590,
                    "lon": 77.4130,
                    "amenity": "college",
                    "operator": "Government of Madhya Pradesh",
                    "website": "",
                    "addr": "Bhopal, Madhya Pradesh",
                    "phone": "",
                    "tags": {"name": "Government Hamidia Arts & Commerce College", "amenity": "college"}
                },
                {
                    "name": "Government Geetanjali Girls' P.G. (Autonomous) College",
                    "lat": 23.2620,
                    "lon": 77.4150,
                    "amenity": "college",
                    "operator": "Government of Madhya Pradesh",
                    "website": "",
                    "addr": "Bhopal, Madhya Pradesh",
                    "phone": "",
                    "tags": {"name": "Government Geetanjali Girls' P.G. College", "amenity": "college"}
                },
                {
                    "name": "Government Home Science P.G. College",
                    "lat": 23.2610,
                    "lon": 77.4140,
                    "amenity": "college",
                    "operator": "Government of Madhya Pradesh",
                    "website": "",
                    "addr": "Bhopal, Madhya Pradesh",
                    "phone": "",
                    "tags": {"name": "Government Home Science P.G. College", "amenity": "college"}
                },
                {
                    "name": "Government Kamla Nehru Mahila Mahavidyalaya",
                    "lat": 23.2600,
                    "lon": 77.4160,
                    "amenity": "college",
                    "operator": "Government of Madhya Pradesh",
                    "website": "",
                    "addr": "Bhopal, Madhya Pradesh",
                    "phone": "",
                    "tags": {"name": "Government Kamla Nehru Mahila Mahavidyalaya", "amenity": "college"}
                },
                {
                    "name": "Government Science and Commerce College",
                    "lat": 23.2550,
                    "lon": 77.4100,
                    "amenity": "college",
                    "operator": "Government of Madhya Pradesh",
                    "website": "",
                    "addr": "Bhopal, Madhya Pradesh",
                    "phone": "",
                    "tags": {"name": "Government Science and Commerce College", "amenity": "college"}
                }
            ],
            "commerce": [
                {
                    "name": "Government Arts & Commerce (Naveen) College",
                    "lat": 23.2580,
                    "lon": 77.4090,
                    "amenity": "college",
                    "operator": "Government of Madhya Pradesh",
                    "website": "",
                    "addr": "Bhopal, Madhya Pradesh",
                    "phone": "",
                    "tags": {"name": "Government Arts & Commerce (Naveen) College", "amenity": "college"}
                },
                {
                    "name": "Government Dr. Shyama Prasad Mukherjee Science & Commerce College",
                    "lat": 23.2560,
                    "lon": 77.4110,
                    "amenity": "college",
                    "operator": "Government of Madhya Pradesh",
                    "website": "",
                    "addr": "Bhopal, Madhya Pradesh",
                    "phone": "",
                    "tags": {"name": "Government Dr. Shyama Prasad Mukherjee Science & Commerce College", "amenity": "college"}
                },
                {
                    "name": "Government PG College, Pipriya",
                    "lat": 23.2450,
                    "lon": 77.3950,
                    "amenity": "college",
                    "operator": "Government of Madhya Pradesh",
                    "website": "",
                    "addr": "Pipriya, Bhopal, Madhya Pradesh",
                    "phone": "",
                    "tags": {"name": "Government PG College, Pipriya", "amenity": "college"}
                },
                {
                    "name": "Government College, Bhopal",
                    "lat": 23.2580,
                    "lon": 77.4080,
                    "amenity": "college",
                    "operator": "Government of Madhya Pradesh",
                    "website": "",
                    "addr": "Bhopal, Madhya Pradesh",
                    "phone": "",
                    "tags": {"name": "Government College, Bhopal", "amenity": "college"}
                }
            ]
        }
        
        # Create all colleges list for "all" stream
        all_bhopal_colleges = []
        for stream_colleges in bhopal_colleges.values():
            for college in stream_colleges:
                if college not in all_bhopal_colleges:
                    all_bhopal_colleges.append(college)
        
        # Sample data for popular locations
        sample_locations = [
            {
                "location_name": "Jabalpur, Madhya Pradesh",
                "lat": 23.1815,
                "lon": 79.9864,
                "radius": 10000,
                "stream": "all",
                "colleges": [
                    {
                        "name": "Jabalpur Engineering College",
                        "lat": 23.1815,
                        "lon": 79.9864,
                        "amenity": "college",
                        "operator": "Government of Madhya Pradesh",
                        "website": "https://www.jecjabalpur.ac.in/",
                        "addr": "Gokalpur, Jabalpur, Madhya Pradesh 482011",
                        "phone": "",
                        "tags": {"name": "Jabalpur Engineering College", "amenity": "college"}
                    },
                    {
                        "name": "NSCB Medical College",
                        "lat": 23.1510,
                        "lon": 79.8815,
                        "amenity": "college",
                        "operator": "Government of Madhya Pradesh",
                        "website": "https://nscbmc.ac.in/",
                        "addr": "Jabalpur, Madhya Pradesh",
                        "phone": "",
                        "tags": {"name": "NSCB Medical College", "amenity": "college"}
                    },
                    {
                        "name": "Mahakaushal Government Autonomous College",
                        "lat": 23.1685,
                        "lon": 79.9338,
                        "amenity": "college",
                        "operator": "Government of Madhya Pradesh",
                        "website": "",
                        "addr": "Jabalpur, Madhya Pradesh",
                        "phone": "",
                        "tags": {"name": "Mahakaushal Government Autonomous College", "amenity": "college"}
                    }
                ]
            }
        ]
        
        # Add Bhopal colleges by stream
        for stream, colleges in bhopal_colleges.items():
            sample_locations.append({
                "location_name": "Bhopal, Madhya Pradesh",
                "lat": 23.2599,
                "lon": 77.4126,
                "radius": 15000,
                "stream": stream,
                "colleges": colleges
            })
        
        # Add Bhopal all colleges
        sample_locations.append({
            "location_name": "Bhopal, Madhya Pradesh",
            "lat": 23.2599,
            "lon": 77.4126,
            "radius": 15000,
            "stream": "all",
            "colleges": all_bhopal_colleges
        })
        
        # Add Indore colleges
        sample_locations.append({
            "location_name": "Indore, Madhya Pradesh",
            "lat": 22.7196,
            "lon": 75.8577,
            "radius": 12000,
            "stream": "all",
            "colleges": [
                {
                    "name": "IIT Indore",
                    "lat": 22.6708,
                    "lon": 75.9061,
                    "amenity": "university",
                    "operator": "Government of India",
                    "website": "https://www.iiti.ac.in/",
                    "addr": "Indore, Madhya Pradesh 453552",
                    "phone": "",
                    "tags": {"name": "IIT Indore", "amenity": "university"}
                },
                {
                    "name": "Government Holkar Science College",
                    "lat": 22.7085,
                    "lon": 75.8735,
                    "amenity": "college",
                    "operator": "Government of Madhya Pradesh",
                    "website": "",
                    "addr": "Indore, Madhya Pradesh",
                    "phone": "",
                    "tags": {"name": "Government Holkar Science College", "amenity": "college"}
                }
            ]
        })
        
        for location_data in sample_locations:
            self.cache_colleges(
                location_data["lat"],
                location_data["lon"],
                location_data["radius"],
                location_data["stream"],
                location_data["colleges"],
                location_data["location_name"]
            )
        
        print(f"✅ Sample cache populated with {len(sample_locations)} locations")
