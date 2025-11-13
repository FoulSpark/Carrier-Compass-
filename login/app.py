
from flask import Flask, render_template, request, redirect, session, url_for, send_from_directory, jsonify
from flask_cors import CORS
import ai_chat
import SIH_01
import run_sih
from college_locator import CollegeLocator
from college_cache import CollegeCache
import os
import datetime
import requests
import json
import time
from threading import Thread

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
app.secret_key = "dev-secret"

# Initialize the college locator and cache
locator = CollegeLocator()
cache = CollegeCache()

ai_chat.init_db()

# Notification cache for storing live data
notification_cache = {
    'last_updated': None,
    'notifications': []
}

def get_live_notification_data():
    """Generate live notification data"""
    notifications = []
    current_year = datetime.datetime.now().year
    
    # JEE Main data with real calculations
    jee_main_dates = {
        'registration_start': f"{current_year}-12-01",
        'registration_end': f"{current_year}-12-30",
        'exam_date': f"{current_year + 1}-01-24"
    }
    
    reg_end = datetime.datetime.strptime(jee_main_dates['registration_end'], '%Y-%m-%d')
    days_left = (reg_end - datetime.datetime.now()).days
    
    if days_left > 0:
        notifications.append({
            'id': 'jee_main_2024',
            'title': f'JEE Main {current_year + 1} Registration',
            'message': f'Registration closes in {days_left} days on {reg_end.strftime("%B %d, %Y")}. Apply now!',
            'date': '2 hours ago',
            'category': 'exams',
            'priority': 'urgent' if days_left <= 7 else 'high',
            'read': False
        })
    
    # NEET data
    neet_exam_date = datetime.datetime(current_year + 1, 5, 5)
    days_to_exam = (neet_exam_date - datetime.datetime.now()).days
    
    notifications.append({
        'id': 'neet_2024',
        'title': f'NEET {current_year + 1} Exam',
        'message': f'NEET exam in {days_to_exam} days on {neet_exam_date.strftime("%B %d, %Y")}. Preparation time remaining!',
        'date': '5 hours ago',
        'category': 'exams',
        'priority': 'high',
        'read': False
    })
    
    # Course notifications
    courses = [
        {
            'title': 'AI & Machine Learning Certification',
            'provider': 'IIT Delhi',
            'discount': '30% Early Bird',
            'deadline': '2024-01-15'
        },
        {
            'title': 'Data Science Professional Certificate',
            'provider': 'Google Career Certificates',
            'discount': 'Financial Aid Available',
            'deadline': '2024-02-01'
        }
    ]
    
    for i, course in enumerate(courses):
        try:
            deadline = datetime.datetime.strptime(course['deadline'], '%Y-%m-%d')
            days_left = (deadline - datetime.datetime.now()).days
            
            if days_left > 0:
                notifications.append({
                    'id': f'course_{i}',
                    'title': f"New Course: {course['title']}",
                    'message': f"{course['provider']} - {course['discount']}. Enrollment closes in {days_left} days.",
                    'date': f'{i + 1} day ago',
                    'category': 'courses',
                    'priority': 'medium' if days_left > 7 else 'high',
                    'read': i % 2 == 0
                })
        except:
            continue
    
    # Scholarship notifications
    scholarships = [
        {
            'title': 'National Merit Scholarship',
            'amount': '₹50,000',
            'deadline': '2024-01-20',
            'eligibility': 'Engineering Students'
        },
        {
            'title': 'Microsoft Summer Internship',
            'amount': '₹40,000/month',
            'deadline': '2024-01-10',
            'eligibility': 'CS/IT Students'
        }
    ]
    
    for i, scholarship in enumerate(scholarships):
        try:
            deadline = datetime.datetime.strptime(scholarship['deadline'], '%Y-%m-%d')
            days_left = (deadline - datetime.datetime.now()).days
            
            if days_left > 0:
                notifications.append({
                    'id': f'scholarship_{i}',
                    'title': f"{scholarship['title']} - {scholarship['amount']}",
                    'message': f"For {scholarship['eligibility']}. Apply before {deadline.strftime('%B %d, %Y')} - {days_left} days left!",
                    'date': f'{i + 2} days ago',
                    'category': 'deadlines',
                    'priority': 'urgent' if days_left <= 5 else 'high',
                    'read': False
                })
        except:
            continue
    
    return notifications

def update_notification_cache():
    """Update notification cache with fresh data"""
    global notification_cache
    try:
        notifications = get_live_notification_data()
        priority_order = {'urgent': 0, 'high': 1, 'medium': 2, 'low': 3}
        notifications.sort(key=lambda x: (priority_order.get(x['priority'], 3), x['id']))
        
        notification_cache['notifications'] = notifications
        notification_cache['last_updated'] = datetime.datetime.now().isoformat()
    except Exception as e:
        print(f"Error updating notifications: {e}")

# Initialize notifications
update_notification_cache()

# webflow animation 
def get_current_user_id():
    return session.get("user_id")


@app.route("/landing")
def landing():
    return render_template("landing_page.html")

@app.route("/")
def index():
    if get_current_user_id():
        return redirect(url_for("dashboard"))
    return render_template("landing_page.html")

@app.route("/home")
def home():
    return render_template("landing_page.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        student_class = request.form.get("student_class", "").strip()
        interests = request.form.get("interests", "").strip()
        
        user_id = ai_chat.create_user(name, email, password)
        if user_id:
            session["user_id"] = user_id
            session["user_name"] = name
            session["user_email"] = email
            
            # Save additional profile data from registration
            if student_class:
                ai_chat.save_profile_data("class", student_class, user_id=user_id)
            if interests:
                ai_chat.save_profile_data("interests", interests, user_id=user_id)
            
            return redirect(url_for("profile"))
        else:
            error = "Email already registered. Please log in."
            return render_template("register.html", error=error)
    return render_template("register.html", error=None)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = ai_chat.verify_user(email, password)
        if user:
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_email"] = email
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Invalid credentials")
    return render_template("login.html", error=None)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/profile", methods=["GET", "POST"])
def profile():
    user_id = get_current_user_id()
    if not user_id:
        return redirect(url_for("login"))
    if request.method == "POST":
        # Save all profile fields
        fields = [
            "student_class", "subjects", "interests", "career_goal", 
            "location", "skills", "additional_info"
        ]
        for field in fields:
            value = request.form.get(field, "").strip()
            if value:
                ai_chat.save_profile_data(field, value, user_id=user_id)
        return redirect(url_for("dashboard"))
    profile_data = ai_chat.get_profile_data(user_id=user_id)
    user_email = session.get("user_email", "")
    user_email_md5 = hashlib.md5(user_email.lower().encode('utf-8')).hexdigest()
    return render_template("profile.html", 
                         profile=profile_data,
                         user_email_md5=user_email_md5)

import hashlib

@app.context_processor
def inject_user_email_md5():
    if 'user_email' in session:
        return {'user_email_md5': hashlib.md5(session['user_email'].lower().encode('utf-8')).hexdigest()}
    return {'user_email_md5': None}


@app.route("/dashboard")
def dashboard():
    user_id = get_current_user_id()
    if not user_id:
        return redirect(url_for("login"))
    profile_data = ai_chat.get_profile_data(user_id=user_id)
    user_name = session.get("user_name", "User")
    user_email = session.get("user_email", "")
    user_email_md5 = hashlib.md5(user_email.lower().encode('utf-8')).hexdigest()
    messages = ai_chat.get_recent_messages(limit=5, user_id=user_id)
    return render_template("dashboard.html", 
                         profile=profile_data, 
                         user_name=user_name, 
                         user_email_md5=user_email_md5,
                         messages=messages)


@app.route("/chat", methods=["GET", "POST"])
def chat():
    user_id = get_current_user_id()
    if not user_id:
        return redirect(url_for("login"))
    messages = ai_chat.get_recent_messages(limit=10, user_id=user_id)
    if request.method == "POST":
        text = request.form.get("text", "").strip()
        if text:
            response = run_sih.process_chat_message(text, user_id=user_id)
            return render_template("chat.html", 
                         messages=[{'text': text, 'response': response}] + messages, 
                         user_name=session.get("user_name", "User"),
                         user_email_md5=hashlib.md5(session.get("user_email", "").lower().encode('utf-8')).hexdigest())
    user_email = session.get("user_email", "")
    user_email_md5 = hashlib.md5(user_email.lower().encode('utf-8')).hexdigest()
    return render_template("chat.html", 
                         messages=messages, 
                         user_name=session.get("user_name", "User"),
                         user_email_md5=user_email_md5)

@app.route("/api/messages")
def get_messages():
    user_id = get_current_user_id()
    if not user_id:
        return {"messages": []}
    messages = ai_chat.get_recent_messages(limit=5, user_id=user_id)
    return {"messages": messages}

@app.route("/api/chat", methods=["POST"])
def api_chat():
    user_id = get_current_user_id()
    if not user_id:
        return {"status": "error", "response": "Please log in to use the AI chat."}, 401
    
    data = request.get_json()
    message = data.get("message", "")
    quiz_results = data.get("quiz_results")  # Optional career quiz results
    
    if message:
        try:
            # Use the new function from run_sih.py with quiz results
            response = run_sih.process_chat_message(message, user_id=user_id, quiz_results=quiz_results)
            return {"status": "success", "response": response}
        except Exception as e:
            return {"status": "error", "response": "Sorry, I'm having trouble processing your request."}
    
    return {"status": "error", "response": "No message provided."}

@app.route("/api/save_quiz_results", methods=["POST"])
def save_quiz_results():
    """Save career quiz results to user profile"""
    user_id = get_current_user_id()
    if not user_id:
        return {"status": "error", "message": "Please log in."}, 401
    
    try:
        data = request.get_json()
        quiz_results = data.get("quiz_results")
        
        if not quiz_results:
            return {"status": "error", "message": "No quiz results provided."}
        
        # Use the new function to populate profile from quiz
        import SIH_01
        success = SIH_01.populate_profile_from_quiz(quiz_results, user_id=user_id)
        
        if success:
            return {"status": "success", "message": "Quiz results saved successfully!"}
        else:
            return {"status": "error", "message": "Failed to save quiz results."}
            
    except Exception as e:
        return {"status": "error", "message": f"Error saving quiz results: {str(e)}"}

@app.route("/api/clear_chat", methods=["DELETE"])
def clear_chat():
    """Clear all chat history for the current user"""
    user_id = get_current_user_id()
    if not user_id:
        return {"status": "error", "message": "Please log in."}, 401
    
    try:
        # Clear chat messages
        ai_chat.clear_messages(user_id=user_id)
        
        # Optionally clear profile data (uncomment if you want to clear profile too)
        # ai_chat.clear_profile_data(user_id=user_id)
        
        return {"status": "success", "message": "Chat history cleared successfully!"}
        
    except Exception as e:
        return {"status": "error", "message": f"Error clearing chat: {str(e)}"}

@app.route("/api/launch_cli", methods=["POST"])
def launch_cli():
    return {"status": "success", "message": "CLI launched successfully! Check your terminal/command prompt for the Spark CLI interface."}

@app.route("/analytics")
def analytics():
    user_id = get_current_user_id()
    if not user_id:
        return redirect(url_for("login"))
    
    analytics_data = ai_chat.get_user_analytics(user_id)
    user_email = session.get("user_email", "")
    user_email_md5 = hashlib.md5(user_email.lower().encode('utf-8')).hexdigest()
    
    return render_template("analytics.html", 
                         analytics=analytics_data, 
                         user_name=session.get("user_name", "User"),
                         user_email_md5=user_email_md5)

@app.route("/api/save_preference", methods=["POST"])
def save_preference():
    user_id = get_current_user_id()
    if not user_id:
        return {"status": "error", "message": "Please log in."}, 401
    
    data = request.get_json()
    preference_type = data.get("type", "")
    preference_value = data.get("value", "")
    rating = data.get("rating", 0)
    metadata = data.get("metadata", "")
    
    if preference_type and preference_value:
        ai_chat.save_user_preference_with_metadata(user_id, preference_type, preference_value, rating, metadata)
        return {"status": "success", "message": "Preference saved successfully."}
    
    return {"status": "error", "message": "Invalid data provided."}, 400

@app.route("/api/get_preferences", methods=["GET"])
def get_preferences():
    user_id = get_current_user_id()
    if not user_id:
        return {"status": "error", "message": "Please log in."}, 401
    
    preference_type = request.args.get("type")
    preferences = ai_chat.get_user_preferences(user_id, preference_type)
    
    return {"status": "success", "preferences": preferences}

# Routes for static pages from New TEMPLATES
@app.route("/quiz")
@app.route("/test")
def test():
    return render_template("test.html")

@app.route("/colleges")
@app.route("/college")
def college():
    user_id = get_current_user_id()
    if not user_id:
        return redirect(url_for("login"))
    return render_template("college.html")

@app.route('/college_index')
def college_index():
    """Serve the college index HTML page"""
    user_id = get_current_user_id()
    if not user_id:
        return redirect(url_for("login"))
    return render_template('index.html')

@app.route("/career_paths")
@app.route("/carrier")
def carrier():
    return render_template("carrier.html")

@app.route("/resources")
@app.route("/study_material")
def study_material():
    return render_template("study_material.html")

@app.route("/timeline")
def timeline():
    return render_template("timeline.html")

@app.route("/home_page")
def home_page():
    return render_template("home.html")

# Serve CSS and JS files
@app.route("/css/<path:filename>")
def serve_css(filename):
    return send_from_directory("../", filename)

@app.route("/js/<path:filename>")
def serve_js(filename):
    return send_from_directory("../", filename)

# Serve images and other assets
@app.route("/assets/<path:filename>")
def serve_assets(filename):
    return send_from_directory("../", filename)

# College Directory API Routes
@app.route('/api/search', methods=['POST'])
def search_colleges():
    """API endpoint to search for colleges"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({'success': False, 'error': 'Please log in to search colleges'}), 401
        
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
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({'success': False, 'error': 'Please log in'}), 401
        
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
    user_id = get_current_user_id()
    if not user_id:
        return redirect(url_for("login"))
        
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        return content, 200, {'Content-Type': 'text/html'}
    except FileNotFoundError:
        return "Map not found", 404

@app.route('/api/cache/search', methods=['POST'])
def search_cache():
    """API endpoint to search colleges in cache"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({'success': False, 'error': 'Please log in'}), 401
        
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
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({'success': False, 'error': 'Please log in'}), 401
        
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
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({'success': False, 'error': 'Please log in'}), 401
        
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

@app.route('/career_guidance_hub')
def career_guidance_hub():
    """Route for the unified career guidance hub"""
    user_id = get_current_user_id()
    if not user_id:
        return redirect(url_for("login"))
    return render_template("career_guidance_hub.html")

@app.route('/career_guidance_chat', methods=['POST'])
def career_guidance_chat():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        
        if not user_message.strip():
            return jsonify({'success': False, 'error': 'Empty message'}), 400
        
        # Get session context for continuity
        session_context = session.get('chat_context', '')
        
        # Call the specialized Career Guidance Chat function
        response = SIH_01.Career_Guidance_Chat(user_message, user_id=user_id, session_context=session_context)
        
        # Update session context
        session['chat_context'] = f"Previous: {user_message[:100]}..."
        
        return jsonify({'success': True, 'response': response})
        
    except Exception as e:
        print(f"Error in career guidance chat: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/api/toggle_chat', methods=['POST'])
def toggle_chat():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        
        if not user_message.strip():
            return jsonify({'success': False, 'error': 'Empty message'}), 400
        
        # Get session context for continuity
        session_context = session.get('toggle_chat_context', '')
        
        # Call the new Toggle Button Chat function
        response = SIH_01.Toggle_Button_Chat(user_message, user_id=user_id, session_context=session_context)
        
        # Update session context
        session['toggle_chat_context'] = f"Previous: {user_message[:100]}..."
        
        return jsonify({'success': True, 'response': response})
        
    except Exception as e:
        print(f"Error in toggle chat: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/api/career_chat', methods=['POST'])
def career_chat():
    """API endpoint for career counselor chatbot (legacy route)"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({'success': False, 'error': 'Please log in'}), 401
    
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'success': False, 'error': 'Message is required'}), 400
        
        # Generate AI response based on message content
        response = generate_career_response(user_message, user_id)
        
        # Store chat history
        ai_chat.add_chat_message(user_id, user_message, response)
        
        return jsonify({
            'success': True,
            'response': response,
            'timestamp': datetime.datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def generate_career_response(message, user_id):
    """Generate AI-powered career counseling responses"""
    try:
        # Get user profile for personalized context
        user_profile = ai_chat.get_user_profile(user_id)
        user_name = user_profile.get('name', 'Student')
        user_interests = user_profile.get('interests', '')
        user_class = user_profile.get('student_class', '')
        
        # Get recent chat history for context
        chat_history = ai_chat.get_recent_chat_history(user_id, limit=5)
        
        # Try multiple AI services in order of preference
        ai_response = None
        
        # 1. Try Hugging Face Inference API (free)
        ai_response = get_huggingface_response(message, user_name, user_interests, user_class, chat_history)
        
        if not ai_response:
            # 2. Try Ollama local model (if available)
            ai_response = get_ollama_response(message, user_name, user_interests, user_class, chat_history)
        
        if not ai_response:
            # 3. Fallback to enhanced rule-based system with AI-like responses
            ai_response = get_enhanced_fallback_response(message, user_name, user_interests, user_class)
        
        return ai_response
        
    except Exception as e:
        print(f"Error in AI response generation: {e}")
        return get_enhanced_fallback_response(message, user_name if 'user_name' in locals() else 'Student', '', '')

def get_huggingface_response(message, user_name, user_interests, user_class, chat_history):
    """Get response from Hugging Face Inference API"""
    try:
        # Build context from user profile and chat history
        context = f"User: {user_name}"
        if user_class:
            context += f", Class: {user_class}"
        if user_interests:
            context += f", Interests: {user_interests}"
        
        # Add recent chat context
        if chat_history:
            context += "\nRecent conversation:\n"
            for chat in chat_history[-3:]:  # Last 3 messages for context
                context += f"User: {chat.get('user_message', '')}\nAI: {chat.get('ai_response', '')}\n"
        
        # Create career counselor prompt
        prompt = f"""You are an expert AI Career Counselor for Indian students. You provide personalized, practical career guidance.

Context: {context}

Current Question: {message}

Provide a helpful, personalized response (max 200 words) that:
1. Addresses the specific question
2. Uses the user's name ({user_name})
3. Considers their background and interests
4. Provides actionable advice
5. Mentions relevant Indian entrance exams, colleges, or career paths when appropriate
6. Is encouraging and supportive

Response:"""

        # Try Hugging Face API with a good conversational model
        api_url = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-large"
        
        headers = {
            "Authorization": "Bearer hf_demo",  # Using demo token - users should add their own
            "Content-Type": "application/json"
        }
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_length": 300,
                "temperature": 0.7,
                "do_sample": True,
                "pad_token_id": 50256
            }
        }
        
        response = requests.post(api_url, headers=headers, json=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                ai_text = result[0].get('generated_text', '').replace(prompt, '').strip()
                if ai_text and len(ai_text) > 10:
                    return ai_text
                    
    except Exception as e:
        print(f"Hugging Face API error: {e}")
        
    return None

def get_ollama_response(message, user_name, user_interests, user_class, chat_history):
    """Get response from local Ollama model"""
    try:
        # Check if Ollama is running locally
        ollama_url = "http://localhost:11434/api/generate"
        
        # Build context
        context = f"User: {user_name}"
        if user_class:
            context += f", Class: {user_class}"
        if user_interests:
            context += f", Interests: {user_interests}"
            
        prompt = f"""You are an expert AI Career Counselor for Indian students. 

Context: {context}
Question: {message}

Provide personalized career guidance in 150 words or less. Use the user's name ({user_name}) and be specific about Indian education system, entrance exams, and career paths."""

        payload = {
            "model": "llama2",  # or "mistral", "codellama" etc.
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 200
            }
        }
        
        response = requests.post(ollama_url, json=payload, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result.get('response', '').strip()
            if ai_response and len(ai_response) > 10:
                return ai_response
                
    except Exception as e:
        print(f"Ollama API error: {e}")
        
    return None

def get_enhanced_fallback_response(message, user_name, user_interests, user_class):
    """Enhanced fallback with AI-like contextual responses"""
    message_lower = message.lower()
    
    # Personalization based on user data
    greeting = f"Hi {user_name}!" if user_name != 'Student' else "Hello!"
    
    # Context-aware responses based on interests and class
    context_info = ""
    if user_class:
        context_info += f" Since you're in {user_class}, "
    if user_interests:
        context_info += f" Given your interests in {user_interests}, "
    
    # AI-like contextual career guidance
    if any(word in message_lower for word in ['career', 'job', 'profession', 'future']):
        if any(word in message_lower for word in ['engineering', 'tech', 'computer', 'software', 'coding']):
            return f"{greeting} {context_info}engineering is an excellent choice! The tech industry offers roles like Software Developer, Data Scientist, AI Engineer, Cybersecurity Specialist, and Product Manager. For engineering, focus on JEE Main/Advanced preparation. Top colleges include IITs, NITs, and BITS. The starting salaries range from ₹6-25 LPA depending on the college and company. Would you like specific guidance on JEE preparation or coding skills development?"
            
        elif any(word in message_lower for word in ['medical', 'doctor', 'medicine', 'healthcare', 'mbbs']):
            return f"{greeting} {context_info}medical field is noble and rewarding! Career options include MBBS (General Medicine), BDS (Dentistry), BAMS (Ayurveda), Pharmacy, Nursing, and Medical Research. NEET is mandatory for MBBS with 720 marks total. Top colleges include AIIMS, JIPMER, and government medical colleges. The journey is 5.5 years for MBBS plus internship. Success requires dedication and strong Biology/Chemistry foundation. Need help with NEET preparation strategy?"
            
        elif any(word in message_lower for word in ['business', 'management', 'commerce', 'finance', 'mba']):
            return f"{greeting} {context_info}business and management offer diverse opportunities! Paths include BBA→MBA, B.Com→CA/CS, Economics, or direct entrepreneurship. Key areas: Finance, Marketing, HR, Operations, Consulting. For MBA, prepare for CAT, MAT, XAT. Top B-schools include IIMs, ISB, FMS. Commerce students can pursue CA (3-4 years), CS (2-3 years), or CFA for finance. Starting packages range from ₹4-20 LPA. What specific business area interests you most?"
            
        elif any(word in message_lower for word in ['arts', 'creative', 'design', 'writing', 'media']):
            return f"{greeting} {context_info}creative fields are booming with digital transformation! Options include Graphic Design, UI/UX Design, Animation, Journalism, Content Writing, Psychology, Fine Arts, and Digital Marketing. Entrance exams include NIFT (fashion), NID (design), JMI (mass comm). The creative economy is worth ₹2.3 lakh crores in India. Skills matter more than degrees here. Portfolio development is crucial. Which creative field excites you most?"
            
        else:
            return f"{greeting} Career selection depends on your interests, strengths, and market opportunities. {context_info}Let's explore: Are you more inclined toward Science (PCM for engineering, PCB for medical), Commerce (business, finance), or Arts (creative, social sciences)? I can provide detailed guidance once I understand your preferences better. What subjects do you enjoy most?"
    
    # College and admission guidance
    elif any(word in message_lower for word in ['college', 'university', 'admission', 'cutoff']):
        return f"{greeting} College selection is crucial for your career! {context_info}I need to know: 1) Your target field (Engineering/Medical/Commerce/Arts), 2) Your location preference, 3) Budget considerations, 4) Your academic performance level. For engineering: IITs (JEE Advanced), NITs (JEE Main), private colleges (state CETs). For medical: AIIMS (NEET AIR 1-100), government colleges (state quotas), private colleges (higher fees). Use our College Directory to find nearby options. What's your target field?"
    
    # Exam preparation
    elif any(word in message_lower for word in ['exam', 'preparation', 'study', 'neet', 'jee', 'cat']):
        return f"{greeting} Exam preparation requires strategic planning! {context_info}Key exams: JEE (Engineering) - Physics, Chemistry, Maths; NEET (Medical) - Physics, Chemistry, Biology; CAT (MBA) - Quantitative, Verbal, Logical Reasoning. Success tips: 1) Start early (Class 11), 2) Consistent daily practice, 3) Previous year papers, 4) Mock tests, 5) Time management. Most toppers study 8-10 hours daily with focused revision. Which exam are you targeting? I can provide a detailed preparation roadmap."
    
    # Stream selection
    elif any(word in message_lower for word in ['stream', 'subject', 'pcm', 'pcb', 'commerce']):
        return f"{greeting} Stream selection shapes your career trajectory! {context_info}PCM (Physics, Chemistry, Maths): Opens doors to Engineering, Architecture, Pure Sciences, Defense services. PCB (Physics, Chemistry, Biology): Medical, Pharmacy, Biotechnology, Agriculture, Forensics. Commerce: CA, CS, Business, Economics, Banking. Arts: Psychology, Sociology, Political Science, Literature, Design. Choose based on: 1) Your strongest subjects, 2) Career interests, 3) Market demand. What are your top-performing subjects?"
    
    # Greetings and general
    elif any(word in message_lower for word in ['hello', 'hi', 'hey']):
        return f"{greeting} I'm your AI Career Counselor, here to guide you through India's education and career landscape. {context_info}I can help with career exploration, college selection, entrance exam strategies, stream choices, and study planning. Whether you're confused about PCM vs PCB, wondering about engineering vs medical, or need exam preparation tips, I'm here to provide personalized guidance. What's on your mind today?"
    
    # Default comprehensive response
    else:
        return f"{greeting} I'm here to provide comprehensive career guidance tailored to the Indian education system. {context_info}I can assist with: 🎯 Career path exploration (Engineering, Medical, Commerce, Arts), 🏫 College selection and admission guidance, 📚 Entrance exam preparation (JEE, NEET, CAT, etc.), 💡 Study strategies and time management, 🌟 Stream selection advice, 💰 Scholarship and financial aid information. The Indian job market is evolving rapidly - let's find the perfect path for your future! What specific area would you like to explore?"


@app.route('/api/remove_preference', methods=['POST'])
def remove_preference():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        pref_type = data.get('type')
        pref_value = data.get('value')
        user_id = session['user_id']
        
        if not pref_type or not pref_value:
            return jsonify({'success': False, 'error': 'Missing type or value'}), 400
        
        # Remove preference from user's data using ai_chat module
        success = ai_chat.remove_user_preference(user_id, pref_type, pref_value)
        
        if success:
            return jsonify({'success': True, 'message': 'Preference removed successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to remove preference'}), 500
            
    except Exception as e:
        print(f"Error removing preference: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

# Notification API endpoints
@app.route('/api/notifications')
def get_notifications():
    """API endpoint to get notifications"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({'success': False, 'error': 'Please log in'}), 401
    
    category_filter = request.args.get('category', 'all')
    
    notifications = notification_cache['notifications']
    
    # Apply filters
    if category_filter != 'all':
        if category_filter == 'urgent':
            notifications = [n for n in notifications if n['priority'] == 'urgent']
        else:
            notifications = [n for n in notifications if n['category'] == category_filter]
    
    return jsonify({
        'notifications': notifications,
        'last_updated': notification_cache['last_updated'],
        'total_count': len(notification_cache['notifications']),
        'filtered_count': len(notifications)
    })

@app.route('/api/notifications/refresh')
def refresh_notifications():
    """Force refresh notifications"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({'success': False, 'error': 'Please log in'}), 401
    
    update_notification_cache()
    return jsonify({'status': 'success', 'message': 'Notifications refreshed'})


if __name__ == "__main__":
    # Respect unified launcher settings to avoid reloader PID mismatch
    launched = os.environ.get("EDUPATH_LAUNCHER") == "1"
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=not launched, use_reloader=not launched)
