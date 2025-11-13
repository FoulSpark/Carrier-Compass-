import sqlite3
import datetime
import hashlib

DB_PATH = "ai_chat.db"  

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Users
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password_hash TEXT,
            created_at TEXT
        )
        """
    )

    # Chat history (global, then ensure user_id column exists)
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            user_message TEXT,
            ai_response TEXT
        )
        """
    )

    # User profile key/value (global, then ensure user_id column exists)
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS user_profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT,
            value TEXT,
            timestamp TEXT
        )
        """
    )

    # Career recommendations tracking
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS career_recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            career_path TEXT,
            recommendation_type TEXT,
            details TEXT,
            confidence_score INTEGER,
            timestamp TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """
    )

    # User preferences and interactions
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS user_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            preference_type TEXT,
            preference_value TEXT,
            rating INTEGER,
            timestamp TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """
    )

    # Ensure user_id columns exist for per-user scoping
    def ensure_column(table_name, column_name, column_type):
        c.execute(f"PRAGMA table_info({table_name})")
        cols = [row[1] for row in c.fetchall()]
        if column_name not in cols:
            c.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")

    ensure_column("chat_history", "user_id", "INTEGER")
    ensure_column("user_profile", "user_id", "INTEGER")

    conn.commit()
    conn.close()

def save_chat(user_msg, ai_msg, user_id=None):
    """Store a user+AI exchange; optionally scoped to a user."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if user_id is None:
        c.execute(
            "INSERT INTO chat_history (timestamp, user_message, ai_response) VALUES (?, ?, ?)",
            (datetime.datetime.now().isoformat(), user_msg, ai_msg)
        )
    else:
        c.execute(
            "INSERT INTO chat_history (timestamp, user_message, ai_response, user_id) VALUES (?, ?, ?, ?)",
            (datetime.datetime.now().isoformat(), user_msg, ai_msg, user_id)
        )
    conn.commit()
    conn.close()

def get_recent_messages(limit=5, user_id=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if user_id is None:
        c.execute(
            "SELECT user_message, ai_response FROM chat_history ORDER BY id DESC LIMIT ?",
            (limit,)
        )
    else:
        c.execute(
            "SELECT user_message, ai_response FROM chat_history WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit)
        )
    rows = c.fetchall()
    conn.close()
    return rows[::-1] 

def search_messages(keyword, limit=10, user_id=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if user_id is None:
        c.execute(
            """
            SELECT timestamp, user_message, ai_response
            FROM chat_history
            WHERE user_message LIKE ? OR ai_response LIKE ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (f"%{keyword}%", f"%{keyword}%", limit),
        )
    else:
        c.execute(
            """
            SELECT timestamp, user_message, ai_response
            FROM chat_history
            WHERE user_id = ? AND (user_message LIKE ? OR ai_response LIKE ?)
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, f"%{keyword}%", f"%{keyword}%", limit),
        )
    rows = c.fetchall()
    conn.close()
    return rows

def clear_messages(user_id=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if user_id is None:
        c.execute("DELETE FROM chat_history")
    else:
        c.execute("DELETE FROM chat_history WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def save_profile_data(key, value, user_id=None):
    """Save structured info like class, subjects, career goal; optionally scoped to user."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # First, delete any existing entry for this key and user_id
    if user_id is None:
        c.execute("DELETE FROM user_profile WHERE key = ? AND user_id IS NULL", (key,))
        c.execute(
            "INSERT INTO user_profile (key, value, timestamp) VALUES (?, ?, ?)",
            (key, value, datetime.datetime.now().isoformat()),
        )
    else:
        c.execute("DELETE FROM user_profile WHERE key = ? AND user_id = ?", (key, user_id))
        c.execute(
            "INSERT INTO user_profile (key, value, timestamp, user_id) VALUES (?, ?, ?, ?)",
            (key, value, datetime.datetime.now().isoformat(), user_id),
        )
    conn.commit()
    conn.close()

def get_profile_data(user_id=None):
    """Return latest profile info as dict; optionally scoped to user."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if user_id is None:
        c.execute(
            """
            SELECT key, value
            FROM user_profile
            ORDER BY id ASC
            """
        )
    else:
        c.execute(
            """
            SELECT key, value
            FROM user_profile
            WHERE user_id = ?
            ORDER BY id ASC
            """,
            (user_id,),
        )
    rows = c.fetchall()
    conn.close()
    return {k: v for k, v in rows}

def clear_profile_data(user_id=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if user_id is None:
        c.execute("DELETE FROM user_profile")
    else:
        c.execute("DELETE FROM user_profile WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

# ---------------- Users -----------------
def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def create_user(name: str, email: str, password: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (name, email, _hash_password(password), datetime.datetime.now().isoformat()),
        )
        conn.commit()
        user_id = c.lastrowid
        return user_id
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def get_user_by_email(email: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, name, email, password_hash FROM users WHERE email = ?", (email,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "name": row[1], "email": row[2], "password_hash": row[3]}
    return None

def verify_user(email: str, password: str):
    user = get_user_by_email(email)
    if not user:
        return None
    if user["password_hash"] == _hash_password(password):
        return user
    return None

# ---------------- Career Recommendations -----------------
def save_career_recommendation(user_id: int, career_path: str, recommendation_type: str, 
                              details: str, confidence_score: int = 0):
    """Save a career recommendation for a user."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO career_recommendations 
        (user_id, career_path, recommendation_type, details, confidence_score, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (user_id, career_path, recommendation_type, details, confidence_score, 
         datetime.datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def get_career_recommendations(user_id: int, limit: int = 10):
    """Get career recommendations for a user."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        SELECT career_path, recommendation_type, details, confidence_score, timestamp
        FROM career_recommendations 
        WHERE user_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
        """,
        (user_id, limit)
    )
    rows = c.fetchall()
    conn.close()
    return [{
        "career_path": row[0],
        "type": row[1], 
        "details": row[2],
        "confidence": row[3],
        "timestamp": row[4]
    } for row in rows]

def save_user_preference(user_id: int, preference_type: str, preference_value: str, rating: int = 0):
    """Save user preference or interaction."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO user_preferences 
        (user_id, preference_type, preference_value, rating, timestamp)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, preference_type, preference_value, rating, 
         datetime.datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def save_user_preference_with_metadata(user_id: int, preference_type: str, preference_value: str, rating: int = 0, metadata: str = ""):
    """Save user preference with metadata (for colleges, etc.)."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Check if metadata column exists, if not add it
    try:
        c.execute("SELECT metadata FROM user_preferences LIMIT 1")
    except sqlite3.OperationalError:
        # Add metadata column if it doesn't exist
        c.execute("ALTER TABLE user_preferences ADD COLUMN metadata TEXT DEFAULT ''")
        conn.commit()
    
    c.execute(
        """
        INSERT INTO user_preferences 
        (user_id, preference_type, preference_value, rating, timestamp, metadata)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (user_id, preference_type, preference_value, rating, 
         datetime.datetime.now().isoformat(), metadata)
    )
    conn.commit()
    conn.close()

def get_user_preferences(user_id: int, preference_type: str = None):
    """Get user preferences, optionally filtered by type."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Check if metadata column exists
    try:
        c.execute("SELECT metadata FROM user_preferences LIMIT 1")
        has_metadata = True
    except sqlite3.OperationalError:
        has_metadata = False
    
    if preference_type:
        if has_metadata:
            c.execute(
                """
                SELECT preference_type, preference_value, rating, timestamp, metadata
                FROM user_preferences
                WHERE user_id = ? AND preference_type = ?
                ORDER BY timestamp DESC
                """,
                (user_id, preference_type)
            )
        else:
            c.execute(
                """
                SELECT preference_type, preference_value, rating, timestamp
                FROM user_preferences
                WHERE user_id = ? AND preference_type = ?
                ORDER BY timestamp DESC
                """,
                (user_id, preference_type)
            )
    else:
        if has_metadata:
            c.execute(
                """
                SELECT preference_type, preference_value, rating, timestamp, metadata
                FROM user_preferences
                WHERE user_id = ?
                ORDER BY timestamp DESC
                """,
                (user_id,)
            )
        else:
            c.execute(
                """
                SELECT preference_type, preference_value, rating, timestamp
                FROM user_preferences
                WHERE user_id = ? AND preference_type = ?
                ORDER BY timestamp DESC
                """,
                (user_id, preference_type)
            )
    
    rows = c.fetchall()
    conn.close()
    
    # Return data with or without metadata based on what's available
    if has_metadata and len(rows) > 0 and len(rows[0]) > 4:
        return [{
            "type": row[0],
            "value": row[1],
            "rating": row[2],
            "timestamp": row[3],
            "metadata": row[4] if len(row) > 4 else ""
        } for row in rows]
    else:
        return [{
            "type": row[0],
            "value": row[1],
            "rating": row[2],
            "timestamp": row[3],
            "metadata": ""
        } for row in rows]

def get_user_analytics(user_id: int):
    """Get comprehensive user analytics for better recommendations."""
    profile_data = get_profile_data(user_id=user_id)
    all_recommendations = get_career_recommendations(user_id)
    preferences = get_user_preferences(user_id)
    
    # Remove duplicates based on career_path name
    seen_careers = set()
    unique_recommendations = []
    for rec in all_recommendations:
        if rec['career_path'] not in seen_careers:
            unique_recommendations.append(rec)
            seen_careers.add(rec['career_path'])
    
    return {
        "profile": profile_data,
        "recommendations": unique_recommendations,
        "preferences": preferences,
        "total_interactions": len(preferences),
        "profile_completion": len([k for k, v in profile_data.items() if v and v != "Not specified"])
    }

def add_chat_message(user_id: int, user_message: str, ai_response: str):
    """Add a chat message to the database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Ensure user_id column exists in chat_history
    try:
        c.execute("ALTER TABLE chat_history ADD COLUMN user_id INTEGER")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    timestamp = datetime.datetime.now().isoformat()
    c.execute(
        "INSERT INTO chat_history (user_id, timestamp, user_message, ai_response) VALUES (?, ?, ?, ?)",
        (user_id, timestamp, user_message, ai_response)
    )
    conn.commit()
    conn.close()

def get_recent_chat_history(user_id: int, limit: int = 10):
    """Get recent chat history for a user"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Check if user_id column exists
    try:
        c.execute("SELECT user_id, timestamp, user_message, ai_response FROM chat_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?", (user_id, limit))
        rows = c.fetchall()
    except sqlite3.OperationalError:
        # Fallback to global chat history if user_id column doesn't exist
        c.execute("SELECT timestamp, user_message, ai_response FROM chat_history ORDER BY timestamp DESC LIMIT ?", (limit,))
        rows = c.fetchall()
        rows = [(None, row[0], row[1], row[2]) for row in rows]
    
    conn.close()
    
    return [{
        "user_id": row[0],
        "timestamp": row[1],
        "user_message": row[2],
        "ai_response": row[3]
    } for row in rows]

def get_user_profile(user_id: int):
    """Get user profile information"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Get user basic info
    c.execute("SELECT name, email FROM users WHERE id = ?", (user_id,))
    user_row = c.fetchone()
    
    if not user_row:
        conn.close()
        return {}
    
    profile = {
        "name": user_row[0],
        "email": user_row[1]
    }
    
    # Get profile data
    try:
        c.execute("SELECT key, value FROM user_profile WHERE user_id = ?", (user_id,))
        profile_rows = c.fetchall()
        for key, value in profile_rows:
            profile[key] = value
    except sqlite3.OperationalError:
        # Fallback if user_id column doesn't exist in user_profile
        pass
    
    conn.close()
    return profile

def remove_user_preference(user_id: int, preference_type: str, preference_value: str):
    """Remove a specific user preference."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Delete the specific preference
        c.execute(
            """
            DELETE FROM user_preferences 
            WHERE user_id = ? AND preference_type = ? AND preference_value = ?
            """,
            (user_id, preference_type, preference_value)
        )
        
        # Check if any rows were affected
        rows_affected = c.rowcount
        conn.commit()
        conn.close()
        
        return rows_affected > 0
        
    except Exception as e:
        print(f"Error removing user preference: {e}")
        return False
    
# clear_profile_data()