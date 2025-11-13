from flask import Flask, render_template, request, redirect, session, url_for, send_from_directory
import ai_chat
import SIH_01
import run_sih

app = Flask(__name__)
app.secret_key = "dev-secret"

ai_chat.init_db()

# webflow animation 
def get_current_user_id():
    return session.get("user_id")


@app.route("/")
def index():
    if get_current_user_id():
        return redirect(url_for("dashboard"))
    return render_template("index.html")


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
    return render_template("profile.html", profile=profile_data)

@app.route("/dashboard")
def dashboard():
    user_id = get_current_user_id()
    if not user_id:
        return redirect(url_for("login"))
    profile_data = ai_chat.get_profile_data(user_id=user_id)
    user_name = session.get("user_name", "User")
    messages = ai_chat.get_recent_messages(limit=5, user_id=user_id)
    return render_template("dashboard.html", profile=profile_data, user_name=user_name, messages=messages)


@app.route("/chat", methods=["GET", "POST"])
def chat():
    user_id = get_current_user_id()
    if not user_id:
        return redirect(url_for("login"))
    messages = ai_chat.get_recent_messages(limit=10, user_id=user_id)
    if request.method == "POST":
        text = request.form.get("text", "").strip()
        if text:
            SIH_01.Talk_Chat(text, user_id=user_id)
        return redirect(url_for("chat"))
    return render_template("chat.html", messages=messages, user_name=session.get("user_name", "User"))

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
    
    if message:
        try:
            # Use the new function from run_sih.py
            response = run_sih.process_chat_message(message, user_id=user_id)
            return {"status": "success", "response": response}
        except Exception as e:
            return {"status": "error", "response": "Sorry, I'm having trouble processing your request."}
    
    return {"status": "error", "response": "No message provided."}

@app.route("/api/launch_cli", methods=["POST"])
def launch_cli():
    return {"status": "success", "message": "CLI launched successfully! Check your terminal/command prompt for the Spark CLI interface."}


if __name__ == "__main__":
    launched = os.environ.get("EDUPATH_LAUNCHER") == "1"
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=not launched, use_reloader=not launched)
