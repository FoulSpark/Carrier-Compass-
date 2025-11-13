#!/usr/bin/env python3
"""
Simple script to run the Flask server for the College Locator web app.
This connects the college_locator.py backend with the HTML frontend.
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import app
    print("✅ Flask app imported successfully")
    print("🌐 Starting College Locator Web Server...")
    port = int(os.environ.get("PORT", 5002))
    print(f"📍 Open your browser and go to: http://localhost:{port}")
    print("🔍 You can search for colleges by location or use live location")
    print("⚡ Press Ctrl+C to stop the server")
    print("-" * 50)
    
    # Run the Flask app
    launched = os.environ.get("EDUPATH_LAUNCHER") == "1"
    app.run(debug=not launched, use_reloader=not launched, host='0.0.0.0', port=port)
    
except ImportError as e:
    print(f"❌ Error importing Flask app: {e}")
    print("💡 Make sure Flask is installed: pip install flask flask-cors")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error starting server: {e}")
    sys.exit(1)
