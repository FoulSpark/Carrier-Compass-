#!/usr/bin/env python3
"""
Simple HTTP server to serve the career roadmap page
This solves CORS issues when accessing JSON files
"""

import http.server
import socketserver
import webbrowser
import os
import sys
from pathlib import Path

# Configuration
PORT = 8080
HOST = 'localhost'

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def main():
    # Change to the parent directory so we can access both folders
    parent_dir = Path(__file__).parent.parent
    os.chdir(parent_dir)
    
    print("=" * 60)
    print("🚀 CAREER ROADMAP SERVER")
    print("=" * 60)
    print(f"✅ Serving files from: {parent_dir}")
    print(f"✅ Server running at: http://{HOST}:{PORT}")
    print(f"✅ Career page: http://{HOST}:{PORT}/course-to-career_path_mapping_2/carrier.html")
    print(f"✅ Quiz page: http://{HOST}:{PORT}/aptitude_&_interest_quiz_page_2/test.html")
    print("=" * 60)
    print("💡 Press Ctrl+C to stop the server")
    print("🌐 Opening browser automatically...")
    
    # Open browser automatically
    webbrowser.open(f'http://{HOST}:{PORT}/course-to-career_path_mapping_2/carrier.html')
    
    # Start server
    with socketserver.TCPServer((HOST, PORT), CustomHTTPRequestHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Stopping server...")
            print("✅ Server stopped successfully!")
            print("👋 Thanks for using the Career Roadmap System!")

if __name__ == "__main__":
    main()
