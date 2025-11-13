from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import json
import os
from college_locator import CollegeLocator
from college_cache import CollegeCache

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize the college locator and cache
locator = CollegeLocator()
cache = CollegeCache()

@app.route('/')
def index():
    """Serve the main HTML page"""
    return render_template('index.html')

@app.route('/college')
def college():
    """Serve the college HTML page"""
    return render_template('college.html')

@app.route('/index')
def index_page():
    """Serve the index HTML page"""
    return render_template('index.html')

@app.route('/api/search', methods=['POST'])
def search_colleges():
    """API endpoint to search for colleges"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data received'
            }), 400
            
        location = data.get('location', '')
        radius = int(data.get('radius', 10)) * 1000  # Convert km to meters
        stream = data.get('stream', 'all')
        use_live_location = data.get('use_live_location', False)
        
        if use_live_location:
            # Get live location
            live_data = locator.get_live_location()
            if not live_data:
                return jsonify({
                    'success': False,
                    'error': 'Could not detect live location'
                }), 400
            
            lat, lon, location_name = live_data
        else:
            # Get coordinates from location string
            coords = locator.get_coordinates(location)
            if not coords:
                return jsonify({
                    'success': False,
                    'error': f'Location "{location}" not found'
                }), 400
            
            lat, lon = coords
            location_name = location
        
        # First try to get colleges from cache
        print(f"🔍 Searching cache for colleges near {location_name}...")
        colleges = cache.get_cached_colleges(lat, lon, radius, stream, location_name)
        
        # If no colleges found in cache, fallback to API
        if colleges is None:
            print(f"📡 No colleges in cache, searching via API...")
            colleges = locator.get_nearby_colleges(lat, lon, radius, stream)
            
            # Apply injections for Jabalpur
            locator._inject_jec_if_jabalpur(colleges, location_name, stream)
            locator._inject_nscb_if_jabalpur(colleges, location_name, stream)
            locator._inject_mahakaushal_if_jabalpur(colleges, location_name, stream)
            
            # Filter by stream
            colleges = locator._filter_colleges_by_stream(colleges, stream)
            
            # Cache the results for future use
            if colleges:
                print(f"💾 Caching {len(colleges)} colleges for future searches...")
                cache.cache_colleges(lat, lon, radius, stream, colleges, location_name)
        else:
            print(f"✅ Found {len(colleges)} colleges in cache")
        
        # Create map
        map_file = ""
        if colleges:
            map_file = locator.create_map(lat, lon, colleges, location_name, radius)
        
        # Determine source for response
        source = 'cache' if colleges and len(colleges) > 0 else 'api'
        
        return jsonify({
            'success': True,
            'colleges': colleges,
            'location': {
                'name': location_name,
                'lat': lat,
                'lon': lon
            },
            'map_file': map_file,
            'total_found': len(colleges),
            'source': source,
            'debug_info': {
                'searched_lat': lat,
                'searched_lon': lon,
                'radius_km': radius/1000,
                'stream': stream
            }
        })
        
    except Exception as e:
        print(f"API Search Error: {str(e)}")  # Debug logging
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/live-location', methods=['GET'])
def get_live_location():
    """API endpoint to get user's live location"""
    try:
        live_data = locator.get_live_location()
        if live_data:
            lat, lon, location_name = live_data
            return jsonify({
                'success': True,
                'location': {
                    'name': location_name,
                    'lat': lat,
                    'lon': lon
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Could not detect live location'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/maps/<filename>')
def serve_map(filename):
    """Serve generated map files"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        return content, 200, {'Content-Type': 'text/html'}
    except FileNotFoundError:
        return "Map not found", 404

# Routes to serve static HTML files from other components
@app.route('/home')
def serve_home():
    """Serve home page"""
    try:
        file_path = os.path.join(os.path.dirname(__file__), '..', 'landing_page_(homepage)_2', 'home.html')
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix navigation links to point back to Flask server
        content = content.replace('href="../aptitude_&_interest_quiz_page_2/test.html"', 'href="http://localhost:5002/quiz"')
        content = content.replace('href="../nearby_government_colleges_directory_2/college.html"', 'href="http://localhost:5002/college"')
        content = content.replace('href="../course-to-career_path_mapping_2/carrier.html"', 'href="http://localhost:5002/career-paths"')
        content = content.replace('href="../study_material_&_resources_2/study_material.html"', 'href="http://localhost:5002/resources"')
        content = content.replace('href="../user_profile_&_personalization_2/profile.html"', 'href="http://localhost:5002/profile"')
        content = content.replace('href="../timeline_tracker_(notifications)_2/timeline.html"', 'href="http://localhost:5002/timeline"')
        
        return content, 200, {'Content-Type': 'text/html'}
    except FileNotFoundError:
        return "Home page not found", 404
    except Exception as e:
        return f"Error loading home page: {str(e)}", 500

@app.route('/quiz')
def serve_quiz():
    """Serve quiz page"""
    try:
        file_path = os.path.join(os.path.dirname(__file__), '..', 'aptitude_&_interest_quiz_page_2', 'test.html')
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix navigation links to point back to Flask server
        content = content.replace('href="../landing_page_(homepage)_2/home.html"', 'href="http://localhost:5002/home"')
        content = content.replace('href="../nearby_government_colleges_directory_2/college.html"', 'href="http://localhost:5002/college"')
        content = content.replace('href="../course-to-career_path_mapping_2/carrier.html"', 'href="http://localhost:5002/career-paths"')
        content = content.replace('href="../study_material_&_resources_2/study_material.html"', 'href="http://localhost:5002/resources"')
        content = content.replace('href="../user_profile_&_personalization_2/profile.html"', 'href="http://localhost:5002/profile"')
        content = content.replace('href="../timeline_tracker_(notifications)_2/timeline.html"', 'href="http://localhost:5002/timeline"')
        
        return content, 200, {'Content-Type': 'text/html'}
    except FileNotFoundError:
        return "Quiz page not found", 404
    except Exception as e:
        return f"Error loading quiz page: {str(e)}", 500

@app.route('/career-paths')
def serve_career_paths():
    """Serve career paths page"""
    try:
        file_path = os.path.join(os.path.dirname(__file__), '..', 'course-to-career_path_mapping_2', 'carrier.html')
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix navigation links to point back to Flask server
        content = content.replace('href="../landing_page_(homepage)_2/home.html"', 'href="http://localhost:5002/home"')
        content = content.replace('href="../aptitude_&_interest_quiz_page_2/test.html"', 'href="http://localhost:5002/quiz"')
        content = content.replace('href="../nearby_government_colleges_directory_2/college.html"', 'href="http://localhost:5002/college"')
        content = content.replace('href="../study_material_&_resources_2/study_material.html"', 'href="http://localhost:5002/resources"')
        content = content.replace('href="../user_profile_&_personalization_2/profile.html"', 'href="http://localhost:5002/profile"')
        content = content.replace('href="../timeline_tracker_(notifications)_2/timeline.html"', 'href="http://localhost:5002/timeline"')
        
        return content, 200, {'Content-Type': 'text/html'}
    except FileNotFoundError:
        return "Career paths page not found", 404
    except Exception as e:
        return f"Error loading career paths page: {str(e)}", 500

@app.route('/resources')
def serve_resources():
    """Serve resources page"""
    try:
        file_path = os.path.join(os.path.dirname(__file__), '..', 'study_material_&_resources_2', 'study_material.html')
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix navigation links to point back to Flask server
        content = content.replace('href="../landing_page_(homepage)_2/home.html"', 'href="http://localhost:5002/home"')
        content = content.replace('href="../aptitude_&_interest_quiz_page_2/test.html"', 'href="http://localhost:5002/quiz"')
        content = content.replace('href="../nearby_government_colleges_directory_2/college.html"', 'href="http://localhost:5002/college"')
        content = content.replace('href="../course-to-career_path_mapping_2/carrier.html"', 'href="http://localhost:5002/career-paths"')
        content = content.replace('href="../user_profile_&_personalization_2/profile.html"', 'href="http://localhost:5002/profile"')
        content = content.replace('href="../timeline_tracker_(notifications)_2/timeline.html"', 'href="http://localhost:5002/timeline"')
        
        return content, 200, {'Content-Type': 'text/html'}
    except FileNotFoundError:
        return "Resources page not found", 404
    except Exception as e:
        return f"Error loading resources page: {str(e)}", 500

@app.route('/profile')
def serve_profile():
    """Serve profile page"""
    try:
        file_path = os.path.join(os.path.dirname(__file__), '..', 'user_profile_&_personalization_2', 'profile.html')
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix navigation links to point back to Flask server
        content = content.replace('href="../landing_page_(homepage)_2/home.html"', 'href="http://localhost:5002/home"')
        content = content.replace('href="../aptitude_&_interest_quiz_page_2/test.html"', 'href="http://localhost:5002/quiz"')
        content = content.replace('href="../nearby_government_colleges_directory_2/college.html"', 'href="http://localhost:5002/college"')
        content = content.replace('href="../course-to-career_path_mapping_2/carrier.html"', 'href="http://localhost:5002/career-paths"')
        content = content.replace('href="../study_material_&_resources_2/study_material.html"', 'href="http://localhost:5002/resources"')
        content = content.replace('href="../timeline_tracker_(notifications)_2/timeline.html"', 'href="http://localhost:5002/timeline"')
        
        return content, 200, {'Content-Type': 'text/html'}
    except FileNotFoundError:
        return "Profile page not found", 404
    except Exception as e:
        return f"Error loading profile page: {str(e)}", 500

@app.route('/timeline')
def serve_timeline():
    """Serve timeline page"""
    try:
        file_path = os.path.join(os.path.dirname(__file__), '..', 'timeline_tracker_(notifications)_2', 'timeline.html')
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix navigation links to point back to Flask server
        content = content.replace('href="../landing_page_(homepage)_2/home.html"', 'href="http://localhost:5002/home"')
        content = content.replace('href="../aptitude_&_interest_quiz_page_2/test.html"', 'href="http://localhost:5002/quiz"')
        content = content.replace('href="../nearby_government_colleges_directory_2/college.html"', 'href="http://localhost:5002/college"')
        content = content.replace('href="../course-to-career_path_mapping_2/carrier.html"', 'href="http://localhost:5002/career-paths"')
        content = content.replace('href="../study_material_&_resources_2/study_material.html"', 'href="http://localhost:5002/resources"')
        content = content.replace('href="../user_profile_&_personalization_2/profile.html"', 'href="http://localhost:5002/profile"')
        
        return content, 200, {'Content-Type': 'text/html'}
    except FileNotFoundError:
        return "Timeline page not found", 404
    except Exception as e:
        return f"Error loading timeline page: {str(e)}", 500

@app.route('/api/cache/search', methods=['POST'])
def search_cache():
    """API endpoint to search colleges in cache"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data received'
            }), 400
        
        query = data.get('query', '')
        stream = data.get('stream', 'all')
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Search query is required'
            }), 400
        
        colleges = cache.search_cached_colleges(query, stream)
        
        return jsonify({
            'success': True,
            'colleges': colleges,
            'total_found': len(colleges),
            'source': 'cache'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/cache/locations', methods=['GET'])
def get_cached_locations():
    """API endpoint to get list of cached locations"""
    try:
        locations = cache.get_cached_locations()
        return jsonify({
            'success': True,
            'locations': locations,
            'total_locations': len(locations)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/cache/stats', methods=['GET'])
def get_cache_stats():
    """API endpoint to get cache statistics"""
    try:
        stats = cache.get_cache_stats()
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/cache/populate', methods=['POST'])
def populate_cache():
    """API endpoint to populate cache with sample data"""
    try:
        cache.populate_sample_cache()
        stats = cache.get_cache_stats()
        
        return jsonify({
            'success': True,
            'message': 'Cache populated successfully',
            'stats': stats
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/cache/clear', methods=['POST'])
def clear_cache():
    """API endpoint to clear cache"""
    try:
        cache.clear_cache()
        return jsonify({
            'success': True,
            'message': 'Cache cleared successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/cache/cleanup', methods=['POST'])
def cleanup_cache():
    """API endpoint to clean up expired cache entries"""
    try:
        data = request.get_json() or {}
        days = data.get('days', 7)
        
        removed_count = cache.clear_expired_cache(days)
        stats = cache.get_cache_stats()
        
        return jsonify({
            'success': True,
            'message': f'Removed {removed_count} expired entries',
            'removed_count': removed_count,
            'stats': stats
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # Initialize cache with sample data on startup if empty
    try:
        stats = cache.get_cache_stats()
        if stats['total_cached_locations'] == 0:
            print("🔄 Cache is empty, populating with sample data...")
            cache.populate_sample_cache()
        else:
            print(f"📊 Cache ready with {stats['total_cached_locations']} locations and {stats['total_cached_colleges']} colleges")
    except Exception as e:
        print(f"⚠️ Cache initialization warning: {e}")
    
    launched = os.environ.get("EDUPATH_LAUNCHER") == "1"
    port = int(os.environ.get("PORT", 5002))
    app.run(debug=not launched, use_reloader=not launched, host='0.0.0.0', port=port)
