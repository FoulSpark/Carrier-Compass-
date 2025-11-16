import ai_chat
import SIH_01

ai_chat.init_db()

def process_chat_message(message, user_id=None, quiz_results=None):
    """
    Process a chat message and return the AI response.
    This function can be called from the Flask app.
    """
    try:
        # Call the main AI function with quiz results
        response = SIH_01.Talk_Chat(message, user_id=user_id, quiz_results=quiz_results)
        return response
    except Exception as e:
        return f"Sorry, I encountered an error: {str(e)}"

def run_cli():
    """Run the CLI interface"""
    print("👋 Hi, I'm Spark! Let's figure out your career path.")
    print("Type 'exit' to quit.\n")

    # Optional: prompt for email to bind CLI session to a user
    current_user = None
    email = input("Enter your email to continue (or press Enter to use guest): ").strip()
    if email:
        user = ai_chat.get_user_by_email(email)
        if not user:
            name = input("New user detected. Enter your name: ").strip() or "Guest"
            password = input("Create a password: ")
            user_id = ai_chat.create_user(name, email, password)
            if user_id:
                current_user = {"id": user_id, "name": name, "email": email}
                print(f"Welcome, {name}! Your account has been created.")
            else:
                print("Email already exists or invalid. Continuing as guest.")
        else:
            password = input("Enter your password: ")
            verified = ai_chat.verify_user(email, password)
            if verified:
                current_user = verified
                print(f"Welcome back, {verified['name']}!")
            else:
                print("Login failed. Continuing as guest.")

    while True:
        user_input = input("You: ")
        if user_input.lower() in {"exit", "quit"}:
            print("👋 Bye, good luck with your studies!")
            break
        SIH_01.Talk_Chat(user_input, user_id=current_user["id"] if current_user else None)

if __name__ == "__main__":
    run_cli()


