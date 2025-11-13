#!/usr/bin/env python3
"""
EduPath Career Assessment System Launcher
Starts both the quiz server and career backend together
"""

import subprocess
import sys
import time
import threading
import os
from pathlib import Path

def install_requirements():
    """Install required packages"""
    try:
        import flask
        import flask_cors
        print("✅ Required packages already installed")
    except ImportError:
        print("📦 Installing required packages...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "flask", "flask-cors"])
        print("✅ Packages installed successfully")

def start_career_backend():
    """Start the career backend server"""
    try:
        print("🚀 Starting Career Backend Server on port 5003...")
        subprocess.run([sys.executable, "career_backend.py"], cwd=Path(__file__).parent)
    except Exception as e:
        print(f"❌ Error starting career backend: {e}")

def start_quiz_server():
    """Start the quiz server"""
    try:
        print("🚀 Starting Quiz Server on port 5002...")
        subprocess.run([sys.executable, "start_server.py"], cwd=Path(__file__).parent)
    except Exception as e:
        print(f"❌ Error starting quiz server: {e}")

def main():
    """Main function to start both servers"""
    print("🎯 EduPath Career Assessment System")
    print("=" * 50)
    
    # Install requirements
    install_requirements()
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print("\n🔧 Starting Career Assessment System...")
    print("📍 Quiz Server: http://localhost:5002")
    print("📍 Career Backend: http://localhost:5003")
    print("📍 Career Results: ../course-to-career_path_mapping_2/carrier.html")
    
    # Start career backend in a separate thread
    backend_thread = threading.Thread(target=start_career_backend, daemon=True)
    backend_thread.start()
    
    # Give backend time to start
    time.sleep(2)
    
    # Start quiz server (this will block)
    try:
        start_quiz_server()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Career Assessment System...")
        print("👋 Thanks for using EduPath!")

if __name__ == "__main__":
    main()
