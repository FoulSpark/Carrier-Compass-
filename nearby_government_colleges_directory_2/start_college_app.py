#!/usr/bin/env python3
"""
Unified startup script for EduPath College Directory
This script ensures all dependencies are met and starts the Flask app on port 5002
"""

import sys
import os
import subprocess
import time

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = ['flask', 'flask_cors', 'requests', 'folium', 'geopy']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("💡 Installing missing packages...")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing_packages)
            print("✅ All packages installed successfully")
        except subprocess.CalledProcessError:
            print("❌ Failed to install packages. Please run: pip install -r requirements.txt")
            return False
    
    return True

def main():
    """Main startup function"""
    print("🌐 EduPath College Directory Startup")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Add current directory to Python path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    try:
        from app import app
        print("✅ Flask app imported successfully")
        print("🏫 Starting College Directory Server...")
        port = int(os.environ.get("PORT", 5002))
        print(f"📍 Open your browser and go to: http://localhost:{port}")
        print("🔍 Features available:")
        print("   • Search colleges by location")
        print("   • Use live location detection")
        print("   • Filter by academic streams")
        print("   • Interactive maps with college markers")
        print("⚡ Press Ctrl+C to stop the server")
        print("-" * 50)
        
        # Run the Flask app with launcher-aware settings
        launched = os.environ.get("EDUPATH_LAUNCHER") == "1"
        app.run(debug=not launched, use_reloader=not launched, host='0.0.0.0', port=port)
        
    except ImportError as e:
        print(f"❌ Error importing Flask app: {e}")
        print("💡 Make sure all dependencies are installed")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
