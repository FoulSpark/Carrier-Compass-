import ai_chat
import re
import requests
from collections import Counter
import time
import random
import os

# Init DB
ai_chat.init_db()

# API Keys (read from environment if provided)
API_KEY = os.environ.get("GOOGLE_API_KEY", "")
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"

API_KEY2 = os.environ.get("GOOGLE_API_KEY2", "")
API_URL2 = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY2}"

GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "")
GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
PLACES_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"

MAX_CONTEXT_CHARS = 800

# Retry configuration for API calls
MAX_RETRIES = 3
BASE_DELAY = 1  # Base delay in seconds
MAX_DELAY = 10  # Maximum delay in seconds

def make_api_request_with_retry(url, data, headers, max_retries=MAX_RETRIES):
    """
    Make API request with exponential backoff retry for 503 errors
    """
    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                return response
            elif response.status_code == 503:
                if attempt < max_retries - 1:  # Don't sleep on last attempt
                    # Exponential backoff with jitter
                    delay = min(BASE_DELAY * (2 ** attempt) + random.uniform(0, 1), MAX_DELAY)
                    print(f"API overloaded (503), retrying in {delay:.1f}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(delay)
                    continue
                else:
                    print("API still overloaded after all retries. Please try again later.")
                    return response
            else:
                # For other errors, don't retry
                return response
                
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                delay = min(BASE_DELAY * (2 ** attempt), MAX_DELAY)
                print(f"Request timeout, retrying in {delay:.1f}s... (attempt {attempt + 1}/{max_retries})")
                time.sleep(delay)
                continue
            else:
                print("Request timed out after all retries.")
                raise
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            raise
    
    return response


# ---------- Location Utilities ----------
def geocode_city(city_name):
    """Convert a city name into latitude & longitude."""
    if not GOOGLE_MAPS_API_KEY:
        return None, None
    params = {"address": city_name, "key": GOOGLE_MAPS_API_KEY}
    response = requests.get(GEOCODE_URL, params=params)
    if response.status_code == 200:
        data = response.json()
        if data["results"]:
            loc = data["results"][0]["geometry"]["location"]
            print(f"Geocoded: {loc['lat']} {loc['lng']}")  # debug
            return loc["lat"], loc["lng"]
    return None, None


def get_nearby_colleges(lat, lng, keyword="college", radius=20000):
    """Fetch nearby colleges from Google Places API."""
    if not GOOGLE_MAPS_API_KEY:
        return []
    params = {
        "location": f"{lat},{lng}",
        "radius": radius,
        "keyword": keyword,
        "key": GOOGLE_MAPS_API_KEY
    }
    response = requests.get(PLACES_URL, params=params)
    if response.status_code == 200:
        data = response.json()
        print("DEBUG Google Places API response:", data)  # debug
        colleges = []
        for place in data.get("results", []):
            colleges.append({
                "name": place.get("name"),
                "address": place.get("vicinity"),
                "rating": place.get("rating", "N/A")
            })
        return colleges
    return []


# ---------- Confidence Scoring ----------
def get_confidence_from_ai(user_input, profile_data):
    data = {
        "contents": [
            {
                "parts": [
                    {"text": f"""
You are scoring how informative a student's answer is for career guidance.

Student's answer: "{user_input}"
Profile so far: {profile_data}

Return only a number between 0 and 100:
- 0 means vague or useless answer ("idk", "maybe").
- 100 means highly informative (includes class, subject interests, and career goal).
"""}
                ]
            }
        ]
    }

    response = make_api_request_with_retry(API_URL, data, {"Content-Type": "application/json"})
    if response.status_code == 200:
        result = response.json()
        score_text = result["candidates"][0]["content"]["parts"][0]["text"]
        try:
            return int(re.findall(r"\d+", score_text)[0])
        except:
            return 0
    return 0


# ---------- Helpers ----------
def clean_and_shorten(text, confidence_level=0):
    """Clean reply text (remove markdown artifacts like **) and preserve proper spacing."""
    # Remove markdown artifacts
    cleaned = re.sub(r"\*\*", "", text)
    
    # Add spacing after periods for better readability
    cleaned = re.sub(r'\.([A-Z])', r'. \1', cleaned)
    
    # Add spacing after colons when followed by text
    cleaned = re.sub(r':([A-Za-z])', r': \1', cleaned)
    
    # Preserve existing line breaks and paragraph structure
    # Replace multiple consecutive spaces with single space, but preserve newlines
    cleaned = re.sub(r'[ \t]+', ' ', cleaned)  # Only collapse spaces/tabs, not newlines
    
    # Normalize multiple newlines to maximum of 2 (paragraph break)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)  # Limit to max 2 newlines
    cleaned = re.sub(r'\n\s*\n', '\n\n', cleaned)  # Clean up whitespace between newlines
    
    # Clean up any trailing/leading whitespace on lines
    lines = cleaned.split('\n')
    cleaned_lines = [line.strip() for line in lines]
    result = '\n'.join(cleaned_lines)
    
    return result.strip()

def save_career_recommendations_from_response(response_text, user_id, confidence_score):
    """Parse AI response and save career recommendations when confidence >= 90%."""
    try:
        # Check if we already have high confidence recommendations for this user to avoid duplicates
        existing_recs = ai_chat.get_career_recommendations(user_id, limit=20)
        high_confidence_exists = any(rec['confidence'] >= 90 for rec in existing_recs)
        
        if high_confidence_exists:
            print(f"High confidence recommendations already exist for user {user_id}, skipping duplicate save")
            return
        
        # Extract career paths from the response
        career_paths = []
        
        # Look for numbered career paths or bullet points
        career_patterns = [
            r'(\d+)\.\s*\*\*([^*]+)\*\*[:\s]*([^*\n]+)',  # 1. **Career Name**: Description
            r'(\d+)\.\s*([A-Z][^:\n]+)[:]\s*([^\n]+)',     # 1. Career Name: Description
            r'[-•]\s*\*\*([^*]+)\*\*[:\s]*([^*\n]+)',      # - **Career Name**: Description
            r'[-•]\s*([A-Z][^:\n]+)[:]\s*([^\n]+)'         # - Career Name: Description
        ]
        
        for pattern in career_patterns:
            matches = re.findall(pattern, response_text, re.MULTILINE)
            for match in matches:
                if len(match) == 3:  # Numbered format
                    career_name = match[1].strip()
                    description = match[2].strip()
                elif len(match) == 2:  # Bullet format
                    career_name = match[0].strip()
                    description = match[1].strip()
                else:
                    continue
                    
                if career_name and description:
                    career_paths.append({
                        'name': career_name,
                        'description': description
                    })
        
        # If no structured paths found, extract general recommendations
        if not career_paths:
            # Look for general career mentions
            career_keywords = ['engineer', 'doctor', 'scientist', 'teacher', 'lawyer', 'business', 'artist', 'researcher']
            for keyword in career_keywords:
                if keyword.lower() in response_text.lower():
                    career_paths.append({
                        'name': keyword.title(),
                        'description': f"Career path identified from AI analysis with {confidence_score}% confidence"
                    })
        
        # Save only unique career path recommendations (limit to top 3 to avoid clutter)
        saved_careers = set()
        for career in career_paths[:3]:
            if career['name'] not in saved_careers:
                ai_chat.save_career_recommendation(
                    user_id=user_id,
                    career_path=career['name'],
                    recommendation_type=f"AI Analysis (Confidence: {confidence_score}%)",
                    details=career['description'],
                    confidence_score=confidence_score
                )
                saved_careers.add(career['name'])
            
    except Exception as e:
        print(f"Error saving career recommendations: {e}")



# ---------- Career Guidance & Counseling Function ----------
def Career_Guidance_Chat(user_input, user_id=None, session_context=None):
    """
    Specialized Gemini function for career guidance and counseling using API_KEY2.
    Provides personalized career counseling, educational pathway advice, and professional guidance.
    """
    
    # Get user profile and recent conversation context
    profile_data = ai_chat.get_profile_data(user_id=user_id)
    recent_messages = ai_chat.get_recent_messages(limit=3, user_id=user_id)
    recent_context = "\n".join([f"User: {u}\nCounselor: {a}" for u, a in recent_messages])
    
    # Simplified context for career counseling
    session_intro = f"""
    Starting career counseling session for student with:
    - Career Interests: {profile_data.get('interests', 'Not specified')}
    - Career Goals: {profile_data.get('career_goal', 'Not specified')}
    - Top Career Domain: {profile_data.get('top_career_domain', 'Not identified')}
    
    Ready to provide personalized career guidance.
    """
    
    return session_intro


# ---------- Toggle Button Chatbot Function ----------
def Toggle_Button_Chat(user_input, user_id=None, session_context=None):
    """
    New specialized chatbot function for toggle button interface.
    Provides comprehensive educational guidance with a focus on interactive assistance.
    Uses API_KEY (first API key) to differentiate from Career_Guidance_Chat.
    """
    
    # Get user profile and recent conversation context
    profile_data = ai_chat.get_profile_data(user_id=user_id)
    recent_messages = ai_chat.get_recent_messages(limit=3, user_id=user_id)
    recent_context = "\n".join([f"User: {u}\nAssistant: {a}" for u, a in recent_messages])
    
    # Build comprehensive educational assistance context
    toggle_chat_context = f"""
    You are EduPath Assistant 🎯 - An interactive educational guidance AI designed for comprehensive student support.
    
    Your capabilities include:
    - Academic planning and course selection
    - Study strategies and time management
    - College and university guidance  
    - Scholarship and financial aid information
    - Career exploration and planning
    - Entrance exam preparation guidance
    - Educational resource recommendations
    
    Student Profile:
    - Name: {profile_data.get('name', 'Student')}
    - Class: {profile_data.get('class', 'Not specified')}
    - Stream: {profile_data.get('stream', 'Not specified')}
    - Interests: {profile_data.get('interests', 'Not specified')}
    - Career Goals: {profile_data.get('career_goal', 'Not specified')}
    - Location: {profile_data.get('location', 'Not specified')}
    
    Recent Conversation Context:
    {recent_context}
    
    INTERACTION STYLE:
    - Be friendly, encouraging, and supportive
    - Provide detailed, actionable advice
    - Ask follow-up questions to better understand needs
    - Offer multiple perspectives and options
    - Use emojis appropriately to make interactions engaging
    - Provide step-by-step guidance when needed
    - Be encouraging and supportive in career discussions
    
    Current Student Query: "{user_input}"
    
    Provide focused career guidance addressing their question.
    """
    
    # Prepare Gemini API request using API_KEY2
    data = {
        "contents": [
            {
                "parts": [
                    {"text": counseling_context}
                ]
            }
        ]
    }
    
    try:
        # Make request to Gemini API using API_KEY2
        response = make_api_request_with_retry(API_URL2, data, {"Content-Type": "application/json"})
        
        if response.status_code == 200:
            result = response.json()
            counseling_response = result["candidates"][0]["content"]["parts"][0]["text"]
            
            # Clean and format the response
            formatted_response = clean_and_shorten(counseling_response)
            
            # Save the counseling session to chat history with special prefix
            ai_chat.save_chat(f"[COUNSELING] {user_input}", f"[Dr. Spark] {formatted_response}", user_id=user_id)
            
            # Update profile confidence if counseling provides new insights
            current_confidence = int(profile_data.get("confidence", 0))
            if current_confidence < 95:  # Only boost if not already very high
                new_confidence = min(current_confidence + 5, 100)  # Small boost for counseling session
                ai_chat.save_profile_data("confidence", str(new_confidence), user_id=user_id)
            
            print(f"[Career Counseling Session - Confidence: {profile_data.get('confidence', 0)}%]")
            print("Dr. Spark (Career Counselor):", formatted_response)
            return formatted_response
            
        else:
            error_msg = f"Counseling API Error: {response.status_code} {response.text}"
            print(error_msg)
            return "I apologize, but I'm experiencing technical difficulties. Please try again in a moment, and I'll be happy to provide you with personalized career guidance."
            
    except Exception as e:
        print(f"Error in Career Guidance Chat: {e}")
        return "I'm currently unable to access my counseling resources. Please try again shortly for personalized career guidance."


def Interactive_Career_Counselor(user_id=None):
    """
    Interactive career counseling session that guides users through comprehensive career planning.
    Uses the Career_Guidance_Chat function for specialized counseling.
    """
    
    print("\n🎓 Welcome to Interactive Career Counseling with Dr. Spark!")
    print("=" * 60)
    
    # Check if user has completed career assessment
    profile_data = ai_chat.get_profile_data(user_id=user_id)
    has_assessment = profile_data.get('career_quiz_completed') == 'true'
    
    if has_assessment:
        intro_context = f"Continuing counseling for student with completed career assessment in {profile_data.get('top_career_domain', 'identified field')}"
        welcome_msg = f"I see you've completed your career assessment! Let's build on your results showing interest in {profile_data.get('top_career_domain', 'your chosen field')}. What specific aspect of your career planning would you like to discuss today?"
    else:
        intro_context = "Initial counseling session for new student"
        welcome_msg = "I'm here to provide personalized career guidance. Whether you're exploring career options, planning your educational path, or preparing for entrance exams, I'm here to help. What's your main career concern or question today?"
    
    # Start counseling session
    initial_response = Career_Guidance_Chat(welcome_msg, user_id=user_id, session_context=intro_context)
    
    return initial_response


# ---------- Main Chat ----------
def load_career_quiz_data(user_id=None):
    """Load career quiz results and populate profile data if available"""
    try:
        # Try to get career results from backend or localStorage equivalent
        # This would typically be called from the frontend and passed to backend
        # For now, we'll check if we have stored career data in profile
        profile_data = ai_chat.get_profile_data(user_id=user_id)
        
        # If we don't have career quiz data, return False
        if not profile_data.get('career_quiz_completed'):
            return False
            
        return True
    except Exception as e:
        print(f"Error loading career quiz data: {e}")
        return False

def populate_profile_from_quiz(quiz_results, user_id=None):
    """Populate profile data from career quiz results"""
    try:
        if not quiz_results or 'top_careers' not in quiz_results:
            return False
            
        top_careers = quiz_results['top_careers']
        domain_scores = quiz_results.get('domain_scores', {})
        
        if top_careers:
            # Get the top career domain and details
            top_career = top_careers[0]
            career_domain = top_career['domain']
            career_score = top_career['score']
            career_options = top_career.get('careers', [])
            competitive_exams = top_career.get('competitive_exams', [])
            higher_studies = top_career.get('higher_studies', [])
            
            # Map domain to subjects and interests
            domain_to_subjects = {
                'Engineering': 'Mathematics, Physics, Computer Science',
                'Medical': 'Biology, Chemistry, Physics', 
                'Business': 'Commerce, Economics, Mathematics',
                'Arts': 'Literature, Fine Arts, Creative Writing',
                'Science': 'Physics, Chemistry, Biology, Mathematics',
                'Education': 'Psychology, Sociology, Subject specialization',
                'Law': 'Political Science, History, Economics',
                'Finance': 'Mathematics, Economics, Accounting'
            }
            
            domain_to_class = {
                'Engineering': '11th/12th PCM',
                'Medical': '11th/12th PCB', 
                'Business': '11th/12th Commerce',
                'Arts': '11th/12th Arts',
                'Science': '11th/12th Science',
                'Education': '11th/12th (Any stream)',
                'Law': '11th/12th (Any stream)',
                'Finance': '11th/12th Commerce/Science'
            }
            
            # Save comprehensive profile data
            ai_chat.save_profile_data('career_quiz_completed', 'true', user_id=user_id)
            ai_chat.save_profile_data('top_career_domain', career_domain, user_id=user_id)
            ai_chat.save_profile_data('career_score', str(career_score), user_id=user_id)
            ai_chat.save_profile_data('career_goal', f"{career_domain} field - {', '.join(career_options[:3])}", user_id=user_id)
            ai_chat.save_profile_data('subjects', domain_to_subjects.get(career_domain, 'Not specified'), user_id=user_id)
            ai_chat.save_profile_data('interests', f"{career_domain}, {', '.join(career_options[:2])}", user_id=user_id)
            ai_chat.save_profile_data('class', domain_to_class.get(career_domain, 'High School'), user_id=user_id)
            ai_chat.save_profile_data('competitive_exams', ', '.join(competitive_exams[:3]), user_id=user_id)
            ai_chat.save_profile_data('higher_studies', ', '.join(higher_studies[:3]), user_id=user_id)
            
            # Set high confidence since we have comprehensive data
            ai_chat.save_profile_data('confidence', '85', user_id=user_id)
            
            # Store all career recommendations for reference
            career_summary = f"Top 3 Career Domains: "
            for i, career in enumerate(top_careers[:3]):
                career_summary += f"{i+1}. {career['domain']} (Score: {career['score']}) "
            ai_chat.save_profile_data('career_recommendations', career_summary, user_id=user_id)
            
            return True
            
    except Exception as e:
        print(f"Error populating profile from quiz: {e}")
        return False
    
    return False

def Talk_Chat(user_input, user_id=None, quiz_results=None):
    # If quiz results are provided, populate profile first
    if quiz_results:
        populate_profile_from_quiz(quiz_results, user_id=user_id)
    
    profile_data = ai_chat.get_profile_data(user_id=user_id)

    # --- Detect city (improved) ---
    city = None
    # Case 1: "in Pune" / "from Delhi" / "at Mumbai"
    match = re.search(r"(?:in|from|at)\s+([A-Z][a-zA-Z]+)", user_input, re.IGNORECASE)
    if match:
        city = match.group(1)
    else:
        # Case 2: user typed only a city name like "pune"
        tokens = user_input.strip().split()
        if len(tokens) == 1 and tokens[0].isalpha():
            city = tokens[0].capitalize()

    if city:
        lat, lng = geocode_city(city)
        if lat and lng:
            ai_chat.save_profile_data("city", city, user_id=user_id)
            ai_chat.save_profile_data("lat", str(lat), user_id=user_id)
            ai_chat.save_profile_data("lng", str(lng), user_id=user_id)

    # --- Confidence ---
    # Check if we have career quiz data - if so, start with higher confidence
    has_quiz_data = profile_data.get('career_quiz_completed') == 'true'
    
    if has_quiz_data:
        # We have comprehensive data from quiz, so add less confidence boost from chat
        added_conf = get_confidence_from_ai(user_input, profile_data) // 2  # Reduce impact
        prev_conf = int(profile_data.get("confidence", 85))  # Start higher
    else:
        # No quiz data, use original logic
        added_conf = get_confidence_from_ai(user_input, profile_data)
        prev_conf = int(profile_data.get("confidence", 0))
    
    new_conf = min(prev_conf + added_conf, 100)
    ai_chat.save_profile_data("confidence", str(new_conf), user_id=user_id)

    # Lower threshold for advice mode if we have quiz data
    confidence_threshold = 75 if has_quiz_data else 90
    mode = "ask" if new_conf < confidence_threshold else "advise"

    # --- Context ---
    recent_messages = ai_chat.get_recent_messages(limit=5, user_id=user_id)
    recent_text = "\n".join([f"User: {u}\nAI: {a}" for u, a in recent_messages])
    if len(recent_text) > MAX_CONTEXT_CHARS:
        recent_text = recent_text[-MAX_CONTEXT_CHARS:]

    # --- System Instruction ---
    if mode == "ask":
        # Check what information we still need
        missing_info = []
        
        # If we have quiz data, we need less basic info
        if has_quiz_data:
            # Focus on specific clarifications rather than basic info
            if not profile_data.get("city"):
                missing_info.append("location preference")
            if not profile_data.get("skills"):
                missing_info.append("specific skills and strengths")
            if not profile_data.get("additional_preferences"):
                missing_info.append("specific preferences or concerns")
        else:
            # Original logic for users without quiz data
            if not profile_data.get("class"):
                missing_info.append("current class/level")
            if not profile_data.get("subjects"):
                missing_info.append("favorite subjects")
            if not profile_data.get("interests"):
                missing_info.append("areas of interest")
            if not profile_data.get("career_goal"):
                missing_info.append("career goals")
            if not profile_data.get("skills"):
                missing_info.append("skills and strengths")
            if not profile_data.get("city"):
                missing_info.append("location preference")
        
        if missing_info:
            if has_quiz_data:
                system_instruction = (
                    f"You are Spark ✨ — a supportive career buddy. "
                    f"I can see you've completed your career assessment! Based on your results showing strong interest in {profile_data.get('top_career_domain', 'your chosen field')}, "
                    f"I'd like to know more about: {', '.join(missing_info)}. "
                    f"Ask one specific question to better personalize my guidance. "
                    f"Keep it short and reference their quiz results to show you understand their interests."
                )
            else:
                system_instruction = (
                    f"You are Spark ✨ — a supportive career buddy. "
                    f"The student is missing information about: {', '.join(missing_info)}. "
                    f"Ask one clear, complete question at a time to gather this information. "
                    f"Keep it short (2–4 sentences), simple, and always end with a clear question. "
                    f"Be encouraging and show genuine interest in their future."
                )
        else:
            system_instruction = (
                "You are Spark ✨ — a supportive career buddy. "
                "You have enough information about the student. "
                "Ask one final clarifying question about their preferences or concerns, "
                "then move to providing personalized career guidance. "
                "Keep it short and encouraging."
            )
    else:
        city = profile_data.get("city", "")
        lat = profile_data.get("lat")
        lng = profile_data.get("lng")
        career_goal = profile_data.get("career_goal", "")

        # Search keyword for colleges
        keyword = "college"
        if "doctor" in career_goal.lower() or "medicine" in career_goal.lower():
            keyword = "medical college"
        elif "engineering" in career_goal.lower():
            keyword = "engineering college"
        elif "commerce" in career_goal.lower():
            keyword = "commerce college"

        nearby_colleges = []
        if lat and lng:
            nearby_colleges = get_nearby_colleges(float(lat), float(lng), keyword)

        college_list = "\n".join([
            f"- {c['name']} ({c['address']}, ⭐ {c['rating']})"
            for c in nearby_colleges[:5]
        ]) or "No nearby colleges found."

        # Build comprehensive profile summary
        profile_summary = f"""
        Student Profile:
        - Class/Level: {profile_data.get('class', 'Not specified')}
        - Favorite Subjects: {profile_data.get('subjects', 'Not specified')}
        - Areas of Interest: {profile_data.get('interests', 'Not specified')}
        - Career Goal: {profile_data.get('career_goal', 'Not specified')}
        - Skills & Strengths: {profile_data.get('skills', 'Not specified')}
        - Location: {city or 'Not specified'}
        - Additional Info: {profile_data.get('additional_info', 'None')}
        """
        
        # Add career quiz data if available
        if has_quiz_data:
            profile_summary += f"""
        
        Career Assessment Results:
        - Top Career Domain: {profile_data.get('top_career_domain', 'Not specified')} (Score: {profile_data.get('career_score', 'N/A')})
        - Career Recommendations: {profile_data.get('career_recommendations', 'Not specified')}
        - Recommended Competitive Exams: {profile_data.get('competitive_exams', 'Not specified')}
        - Higher Studies Options: {profile_data.get('higher_studies', 'Not specified')}
        - Assessment Confidence: {new_conf}% (Enhanced by career quiz data)
        """
        
        if has_quiz_data:
            system_instruction = (
                f"Confidence is {new_conf}% (Enhanced by career assessment data). "
                f"The student has completed a comprehensive career assessment showing strong alignment with {profile_data.get('top_career_domain', 'their chosen field')}. "
                f"Now provide targeted, personalized career guidance based on their complete profile and assessment results. "
                f"Here's their comprehensive profile:\n{profile_summary}\n\n"
                "IMPORTANT FORMATTING: Structure your response with clear paragraph breaks. Use double line breaks between major sections.\n\n"
                "Since they've already identified their career interests through the assessment, provide focused guidance on:\n\n"
                "1. **Next Steps**: Immediate actionable steps based on their top career domain\n\n"
                "2. **Educational Pathway**: Specific courses, streams, and degrees for their identified interests\n\n"
                "3. **Entrance Exam Strategy**: Detailed preparation plan for their relevant competitive exams\n\n"
                "4. **Skill Development**: Advanced skills needed for their chosen career path\n\n"
                "5. **Timeline & Milestones**: Personalized roadmap with deadlines and goals\n\n"
                "6. **College Recommendations**: "
            )
        else:
            system_instruction = (
                f"Confidence is {new_conf}%. "
                "Now provide comprehensive, personalized career guidance based on the student's complete profile. "
                f"Here's what we know about them:\n{profile_summary}\n\n"
                "IMPORTANT FORMATTING: Structure your response with clear paragraph breaks. Use double line breaks between major sections and after each numbered point.\n\n"
                "Provide detailed career guidance including:\n\n"
                "1. **Career Path Analysis**: Suggest 3-4 specific career paths that match their profile\n\n"
                "2. **Educational Roadmap**: For each career path, outline:\n\n"
                "   - Required subjects/streams in 11th-12th\n\n"
                "   - Recommended undergraduate degrees\n\n"
                "   - Important entrance exams (JEE, NEET, CLAT, etc.)\n\n"
                "   - Post-graduation options if applicable\n\n"
                "3. **Skill Development**: Suggest specific skills they should develop\n\n"
                "4. **Timeline & Milestones**: Create a step-by-step action plan\n\n"
                "5. **College Recommendations**: "
            )
        
        if city and lat and lng:
            system_instruction += f"Here are some colleges near {city}:\n{college_list}\n\n"
        else:
            system_instruction += "Since location isn't specified, suggest top colleges across India for their interests.\n\n"
            
        if has_quiz_data:
            system_instruction += (
                "Reference their career assessment results to show how your guidance builds on their identified strengths and interests. "
                "Be encouraging, practical, and specific. Since they've already done the assessment, focus on actionable next steps rather than general exploration.\n\n"
                "CRITICAL: Format your response with proper paragraph spacing. Use double line breaks (\\n\\n) between each major section and after bullet points to ensure readability."
            )
        else:
            system_instruction += (
                "Be encouraging, practical, and specific. Use their actual interests and goals to make recommendations feel personal and achievable.\n\n"
                "CRITICAL: Format your response with proper paragraph spacing. Use double line breaks (\\n\\n) between each major section and after bullet points to ensure readability."
            )
#  

    # --- Gemini Request ---
    data = {
        "contents": [
            {
                "parts": [
                    {"text": (
                        f"{system_instruction}\n\n"
                        f"Recent conversation:\n{recent_text}\n\n"
                        f"User’s profile so far: {profile_data}\n\n"
                        f"My new message is:\n{user_input}"
                    )}
                ]
            }
        ]
    }

    response = make_api_request_with_retry(API_URL, data, {"Content-Type": "application/json"})

    if response is not None and response.status_code == 200:
        result = response.json()
        reply = result["candidates"][0]["content"]["parts"][0]["text"]
        short_reply = clean_and_shorten(reply, new_conf)

        ai_chat.save_chat(user_input, short_reply, user_id=user_id)

        if new_conf >= 90:
            save_career_recommendations_from_response(short_reply, user_id, new_conf)

        print(f"[Confidence: {new_conf}%]")
        print("AI says:", short_reply)
        return short_reply
    else:
        # Local fallback to avoid user-facing errors when API fails
        fallback = []
        greeting = "Hi there! "
        if profile_data.get("class"):
            greeting = f"Hi! Since you're in {profile_data.get('class')}, "
        fallback.append(greeting + "here’s some immediate guidance based on what I know about you.")
        if profile_data.get("interests"):
            fallback.append(f"- Interests: {profile_data.get('interests')}")
        if profile_data.get("career_goal"):
            fallback.append(f"- Career goal: {profile_data.get('career_goal')}")
        if city:
            fallback.append(f"- Location preference: {city}")
        if nearby_colleges:
            fallback.append("Nearby colleges I found:")
            for c in nearby_colleges[:3]:
                fallback.append(f"  • {c['name']} ({c.get('address', 'address N/A')})")
        fallback.append("")
        fallback.append("Next steps:")
        fallback.append("1) Tell me your favorite subjects and any exams you plan to take (JEE, NEET, etc.).")
        fallback.append("2) I’ll suggest a focused roadmap with skills, exams, and top colleges.")
        fallback.append("")
        fallback_text = clean_and_shorten("\n".join(fallback), new_conf)
        ai_chat.save_chat(user_input, fallback_text, user_id=user_id)
        print("AI (fallback) says:", fallback_text)
        return fallback_text



# import ai_chat
# import re
# import requests
# from collections import Counter

# # Init DB
# ai_chat.init_db()

# # API Keys


# # Initialize DB tables (safe to call multiple times)
# API_KEY1 = "AIzaSyDe4uJLYc3PdWcHB2JMNm8eg4Mm7eM6djs"
# API_URL1 = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY1}"


# API_KEY2 = "AIzaSyD3GhpF1noULW8bMq4nFk-AqylwiSSvT5I" #AIzaSyD3GhpF1noULW8bMq4nFk-AqylwiSSvT5I   AIzaSyDe4uJLYc3PdWcHB2JMNm8eg4Mm7eM6djs  AIzaSyA_6G4F-mayTXCIo1OKtrCLK9aX34un9oo
# API_URL2 = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY2}"

# GOOGLE_MAPS_API_KEY = "AIzaSyAXK4aHLUS1236LLvHzWIUopKobvnxYRts"

# # API URLs
# API_URL1 = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY1}"
# GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
# PLACES_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"

# MAX_CONTEXT_CHARS = 800


# # ---------- Location Utilities ----------
# def geocode_city(city_name):
#     """Convert a city name into latitude & longitude."""
#     params = {"address": city_name, "key": GOOGLE_MAPS_API_KEY}
#     response = requests.get(GEOCODE_URL, params=params)
#     if response.status_code == 200:
#         data = response.json()
#         if data["results"]:
#             loc = data["results"][0]["geometry"]["location"]
#             return loc["lat"], loc["lng"]
#     return None, None


# def get_nearby_colleges(lat, lng, keyword="college", radius=5000):
#     """Fetch nearby colleges from Google Places API."""
#     params = {
#         "location": f"{lat},{lng}",
#         "radius": radius,
#         "keyword": keyword,
#         "key": GOOGLE_MAPS_API_KEY
#     }
#     response = requests.get(PLACES_URL, params=params)
#     if response.status_code == 200:
#         data = response.json()
#         colleges = []
#         for place in data.get("results", []):
#             colleges.append({
#                 "name": place.get("name"),
#                 "address": place.get("vicinity"),
#                 "rating": place.get("rating", "N/A")
#             })
#         return colleges
#     return []


# # ---------- Confidence Scoring ----------
# def get_confidence_from_ai(user_input, profile_data):
#     data = {
#         "contents": [
#             {
#                 "parts": [
#                     {"text": f"""
# You are scoring how informative a student's answer is for career guidance.

# Student's answer: "{user_input}"
# Profile so far: {profile_data}

# Return only a number between 0 and 100:
# - 0 means vague or useless answer ("idk", "maybe").
# - 100 means highly informative (includes class, subject interests, and career goal).
# """}
#                 ]
#             }
#         ]
#     }

#     response = requests.post(API_URL1, headers={"Content-Type": "application/json"}, json=data)
#     if response.status_code == 200:
#         result = response.json()
#         score_text = result["candidates"][0]["content"]["parts"][0]["text"]
#         try:
#             return int(re.findall(r"\d+", score_text)[0])
#         except:
#             return 0
#     return 0


# # ---------- Helpers ----------
# def clean_and_shorten(text, max_sentences=3):
#     cleaned = re.sub(r"\*\*", "", text)
#     sentences = re.split(r'(?<=[.!?]) +', cleaned)
#     short_text = ' '.join(sentences[:max_sentences]).strip()
#     return short_text if short_text.endswith('.') else short_text + '.'


# def keywords_delete(text, top_n=5):
#     words = re.findall(r'\b\w+\b', text.lower())
#     stopwords = {"the", "is", "in", "and", "a", "an", "of", "to", "on", "with", "for",
#                  "that", "this", "it", "as", "at", "by", "from", "or", "are", "be"}
#     filtered_words = [w for w in words if w not in stopwords]
#     word_counts = Counter(filtered_words)
#     return [w for w, _ in word_counts.most_common(top_n)]


# # ---------- Main Chat ----------
# def Talk_Chat(user_input):
#     profile_data = ai_chat.get_profile_data()

#     # --- Auto-detect if user mentioned a city ---
#     if "live in" in user_input.lower() or "from" in user_input.lower():
#         # Extract last word as city (simple heuristic)
#         city = user_input.split()[-1]
#         lat, lng = geocode_city(city)
#         if lat and lng:
#             ai_chat.save_profile_data("city", city)
#             ai_chat.save_profile_data("lat", str(lat))
#             ai_chat.save_profile_data("lng", str(lng))

#     # --- Confidence ---
#     added_conf = get_confidence_from_ai(user_input, profile_data)
#     prev_conf = int(profile_data.get("confidence", 0))
#     new_conf = min(prev_conf + added_conf, 100)
#     ai_chat.save_profile_data("confidence", str(new_conf))

#     mode = "ask" if new_conf < 90 else "advise"

#     # --- Context ---
#     recent_messages = ai_chat.get_recent_messages(limit=5)
#     recent_text = "\n".join([f"User: {u}\nAI: {a}" for u, a in recent_messages])
#     if len(recent_text) > MAX_CONTEXT_CHARS:
#         recent_text = recent_text[-MAX_CONTEXT_CHARS:]

#     # --- System Instruction ---
#     if mode == "ask":
#         system_instruction = (
#             "You are Spark ✨ — a supportive career buddy. "
#             "Ask one clear, complete question at a time to better understand the student. "
#             "Cover class, subjects, career goals, and location preference. "
#             "Keep it short (2–4 sentences), simple, and always end with a clear question."
#         )
#     else:
#         city = profile_data.get("city", "")
#         lat = profile_data.get("lat")
#         lng = profile_data.get("lng")
#         career_goal = profile_data.get("career_goal", "")

#         # Search keyword for colleges
#         keyword = "college"
#         if "doctor" in career_goal.lower() or "medicine" in career_goal.lower():
#             keyword = "medical college"
#         elif "engineering" in career_goal.lower():
#             keyword = "engineering college"
#         elif "commerce" in career_goal.lower():
#             keyword = "commerce college"

#         nearby_colleges = []
#         if lat and lng:
#             nearby_colleges = get_nearby_colleges(float(lat), float(lng), keyword)

#         college_list = "\n".join([
#             f"- {c['name']} ({c['address']}, ⭐ {c['rating']})"
#             for c in nearby_colleges[:5]
#         ]) or "No nearby colleges found."

#         system_instruction = (
#             f"Confidence is {new_conf}%. "
#             "Now stop asking and give personalized career guidance. "
#             "Summarize what the student has said, then suggest: "
#             "- Best subject streams or degrees "
#             "- Future career paths (jobs, exams, higher studies) "
#             f"- Colleges near {city} that match their interests:\n{college_list}\n\n"
#             "Be encouraging and practical in tone."
#         )

#     # --- Gemini Request ---
#     data = {
#         "contents": [
#             {
#                 "parts": [
#                     {"text": (
#                         f"{system_instruction}\n\n"
#                         f"Recent conversation:\n{recent_text}\n\n"
#                         f"User’s profile so far: {profile_data}\n\n"
#                         f"My new message is:\n{user_input}"
#                     )}
#                 ]
#             }
#         ]
#     }

#     response = requests.post(API_URL1, headers={"Content-Type": "application/json"}, json=data)

#     if response.status_code == 200:
#         result = response.json()
#         reply = result["candidates"][0]["content"]["parts"][0]["text"]
#         short_reply = clean_and_shorten(reply, max_sentences=5)

#         ai_chat.save_chat(user_input, short_reply)

#         print(f"[Confidence: {new_conf}%]")
#         print("AI says:", short_reply)
#         return short_reply
#     else:
#         error_msg = f"Error: {response.status_code} {response.text}"
#         print(error_msg)
#         return "Oops 😅 something went wrong, try again!"


# ---------- Toggle Button Chatbot Function ----------
def Toggle_Button_Chat(user_input, user_id=None, session_context=None):
    """
    Enhanced chatbot function for toggle button interface with comprehensive memory retention.
    Provides comprehensive educational guidance with a focus on interactive assistance.
    Uses API_KEY (first API key) to differentiate from Career_Guidance_Chat.
    """
    
    # Get user profile and comprehensive conversation history for memory retention
    profile_data = ai_chat.get_profile_data(user_id=user_id)
    
    # Get more conversation history for better memory retention (last 10 messages)
    recent_messages = ai_chat.get_recent_messages(limit=10, user_id=user_id)
    
    # Build conversation memory context
    conversation_memory = ""
    if recent_messages:
        conversation_memory = "Previous Conversation History:\n"
        for i, (user_msg, ai_msg) in enumerate(recent_messages):
            conversation_memory += f"[{i+1}] User: {user_msg}\n"
            conversation_memory += f"[{i+1}] Assistant: {ai_msg}\n"
        conversation_memory += "\n"
    
    # Get user preferences for additional context
    user_preferences = ai_chat.get_user_preferences(user_id) if user_id else []
    preferences_context = ""
    if user_preferences:
        preferences_context = "User Preferences & Interactions:\n"
        for pref in user_preferences[:5]:  # Last 5 preferences
            preferences_context += f"- {pref['type']}: {pref['value']}\n"
        preferences_context += "\n"
    
    # Build comprehensive educational assistance context
    toggle_chat_context = f"""
    You are EduPath Assistant 🎯 - An interactive educational guidance AI designed for comprehensive student support.
    
    MEMORY & CONTEXT AWARENESS:
    You have access to the user's conversation history and preferences. Use this information to:
    - Remember previous discussions and build upon them
    - Provide personalized responses based on past interactions
    - Avoid repeating information already discussed
    - Reference previous conversations when relevant
    - Maintain continuity in ongoing discussions
    - Learn from user's preferences and adapt recommendations accordingly
    
    Your capabilities include:
    - Academic planning and course selection
    - Study strategies and time management
    - College and university guidance  
    - Scholarship and financial aid information
    - Career exploration and planning
    - Entrance exam preparation guidance
    - Educational resource recommendations
    
    Student Profile:
    - Name: {profile_data.get('name', 'Student')}
    - Class: {profile_data.get('class', 'Not specified')}
    - Stream: {profile_data.get('stream', 'Not specified')}
    - Interests: {profile_data.get('interests', 'Not specified')}
    - Career Goals: {profile_data.get('career_goal', 'Not specified')}
    - Location: {profile_data.get('location', 'Not specified')}
    
    {conversation_memory}
    {preferences_context}
    
    INTERACTION STYLE:
    - Be friendly, encouraging, and supportive
    - Provide detailed, actionable advice
    - Ask follow-up questions to better understand needs
    - Offer multiple perspectives and options
    - Use emojis appropriately to make interactions engaging
    - Provide step-by-step guidance when needed
    - Reference past conversations to show continuity
    - Build upon previous discussions naturally
    
    Current Student Query: "{user_input}"
    
    Provide comprehensive educational assistance addressing their question with practical, actionable guidance.
    Use your memory of previous conversations to provide contextual and personalized responses.
    """
    
    # Prepare Gemini API request using API_KEY (first key)
    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": toggle_chat_context
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "topK": 40,
            "topP": 0.95,
            "maxOutputTokens": 1000,
        }
    }
    
    try:
        response = make_api_request_with_retry(API_URL, data, {"Content-Type": "application/json"})
        
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                ai_response = result['candidates'][0]['content']['parts'][0]['text']
                
                # Save the conversation
                if user_id:
                    ai_chat.add_chat_message(user_id, user_input, ai_response)
                
                # Format response for better readability
                formatted_response = ai_response.strip()
                
                return formatted_response
            else:
                return "I'm here to help with your educational journey! Could you please rephrase your question?"
        else:
            print(f"Gemini API error: {response.status_code}")
            return "I'm experiencing some technical difficulties. Please try again in a moment."
            
    except Exception as e:
        print(f"Toggle chat error: {e}")
        return "I'm having trouble connecting right now. Please try asking your question again."
