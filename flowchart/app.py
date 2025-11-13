from flask import Flask, render_template, send_from_directory
import os

app = Flask(__name__)

@app.route('/')
def index():
    return send_from_directory('.', 'interactive_flowchart.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    print("🚀 Starting PCB Career Flowchart Server...")
    port = int(os.environ.get("PORT", 5004))
    print(f"📊 Interactive flowchart will be available at: http://localhost:{port}")
    print("✨ Features: Hover effects, clickable nodes, detailed career information")
    launched = os.environ.get("EDUPATH_LAUNCHER") == "1"
    app.run(debug=not launched, use_reloader=not launched, host='0.0.0.0', port=port)
