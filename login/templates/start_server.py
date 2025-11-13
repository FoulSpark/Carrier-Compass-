#!/usr/bin/env python3
"""
Career Assessment Server Launcher
Automatically starts the local server and opens the assessment in your browser.
"""

import http.server
import socketserver
import webbrowser
import os
import sys
import threading
import time
from pathlib import Path

# Server configuration
PORT = 5002
HOST = "localhost"
ASSESSMENT_FILE = "test.html"

class CareerAssessmentServer:
    def __init__(self):
        self.port = PORT
        self.host = HOST
        self.server = None
        self.server_thread = None
        
    def find_available_port(self):
        """Find an available port starting from the default port"""
        import socket
        for port in range(self.port, self.port + 10):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind((self.host, port))
                    self.port = port
                    return port
            except OSError:
                continue
        raise Exception("No available ports found")
    
    def start_server(self):
        """Start the HTTP server in a separate thread"""
        try:
            # Find available port
            self.find_available_port()
            
            # Change to the script directory
            script_dir = Path(__file__).parent
            os.chdir(script_dir)
            
            # Create server
            handler = http.server.SimpleHTTPRequestHandler
            self.server = socketserver.TCPServer((self.host, self.port), handler)
            
            print(f"🚀 Starting Career Assessment Server...")
            print(f"📍 Server running at: http://{self.host}:{self.port}")
            print(f"📁 Serving files from: {os.getcwd()}")
            print(f"🎯 Assessment URL: http://{self.host}:{self.port}/{ASSESSMENT_FILE}")
            
            # Browser opening disabled - access manually at the URL above
            print("="*60)
            print("🎓 CAREER ASSESSMENT SYSTEM")
            print("="*60)
            print("✅ 40 Questions across 8 career domains")
            print("✅ Interactive career journey visualization")
            print("✅ Personalized exam & course recommendations")
            print("✅ No external dependencies required")
            print("="*60)
            print("\n💡 Press Ctrl+C to stop the server")
            
            # Start server in thread
            self.server_thread = threading.Thread(target=self.server.serve_forever)
            self.server_thread.daemon = True
            self.server_thread.start()
            
            return True
            
        except Exception as e:
            print(f"❌ Error starting server: {e}")
            return False
    
    def open_browser(self):
        """Browser opening disabled - access manually"""
        url = f"http://{self.host}:{self.port}/{ASSESSMENT_FILE}"
        print(f"💡 Access the assessment at: {url}")
        print(f"🌐 No browser will open automatically")
    
    def stop_server(self):
        """Stop the server gracefully"""
        if self.server:
            print("\n🛑 Stopping server...")
            self.server.shutdown()
            self.server.server_close()
            print("✅ Server stopped successfully!")

def main():
    """Main function to start the career assessment system"""
    print("🎯 Career Assessment System Launcher")
    print("=" * 40)
    
    # Create and start server
    server = CareerAssessmentServer()
    
    if server.start_server():
        # Open browser automatically
        browser_thread = threading.Thread(target=server.open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        try:
            # Keep the main thread alive
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            server.stop_server()
            print("\n👋 Thanks for using the Career Assessment System!")
            print("💡 Server was running on port 5002")
            sys.exit(0)
    else:
        print("❌ Failed to start server. Please check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
