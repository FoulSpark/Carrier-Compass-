# ---------- Enhanced Toggle Button Chatbot Function with Memory ----------
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
        response = requests.post(API_URL, headers={"Content-Type": "application/json"}, json=data)
        
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                ai_response = result['candidates'][0]['content']['parts'][0]['text']
                
                # Save the conversation for future memory
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
