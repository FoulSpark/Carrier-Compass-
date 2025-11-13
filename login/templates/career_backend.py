#!/usr/bin/env python3
"""
Career Results Backend Server
Handles saving and retrieving career assessment results
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# File to store career results
RESULTS_FILE = 'career_results.json'

@app.route('/save_career_results', methods=['POST'])
def save_career_results():
    """Save career assessment results to JSON file"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Add timestamp if not present
        if 'timestamp' not in data:
            data['timestamp'] = datetime.now().isoformat()
        
        # Save to JSON file
        with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return jsonify({
            'success': True, 
            'message': 'Career results saved successfully',
            'timestamp': data['timestamp']
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_career_results', methods=['GET'])
def get_career_results():
    """Retrieve saved career assessment results"""
    try:
        if not os.path.exists(RESULTS_FILE):
            return jsonify({
                'success': False,
                'message': 'No career results found. Please take the assessment first.',
                'data': None
            })
        
        with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return jsonify({
            'success': True,
            'message': 'Career results retrieved successfully',
            'data': data
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/clear_career_results', methods=['DELETE'])
def clear_career_results():
    """Clear saved career assessment results"""
    try:
        if os.path.exists(RESULTS_FILE):
            os.remove(RESULTS_FILE)
            return jsonify({
                'success': True,
                'message': 'Career results cleared successfully'
            })
        else:
            return jsonify({
                'success': True,
                'message': 'No career results found to clear'
            })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Career Results Backend',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/')
def index():
    """Root endpoint"""
    return jsonify({
        'service': 'EduPath Career Results Backend',
        'version': '1.0.0',
        'endpoints': {
            'save_results': '/save_career_results (POST)',
            'get_results': '/get_career_results (GET)',
            'health': '/health (GET)'
        }
    })

if __name__ == '__main__':
    print("🚀 Starting Career Results Backend Server...")
    port = int(os.environ.get("PORT", 5003))
    print(f"📍 Server will run at: http://localhost:{port}")
    print("📁 Results will be saved to:", os.path.abspath(RESULTS_FILE))
    print("💡 Press Ctrl+C to stop the server")
    
    launched = os.environ.get("EDUPATH_LAUNCHER") == "1"
    app.run(host='0.0.0.0', port=port, debug=not launched, use_reloader=not launched)
