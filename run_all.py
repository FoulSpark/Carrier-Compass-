# run_all.py - EduPath Unified Service Launcher
import subprocess
import os
import sys
import time
import threading
import requests
from urllib.parse import urlparse
import signal
import socket

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SERVICES = [
    {
        "name": "Main App",
        "path": os.path.join(BASE_DIR, "login", "app.py"),
        "port": 5000,
        "url": "http://127.0.0.1:5000",
        "health_endpoint": "/"
    },
    # {
    #     "name": "Aptitude Service", 
    #     "path": os.path.join(BASE_DIR, "aptitude_&_interest_quiz_page_2", "aptitude test", "ap1_flask.py"),
    #     "port": 5001,
    #     "url": "http://127.0.0.1:5001",
    #     "health_endpoint": "/api/ping",
    #     "env": {"FLASK_ENV": "production", "FLASK_DEBUG": "0"}
    # },
    {
        "name": "College Service",
        "path": os.path.join(BASE_DIR, "nearby_government_colleges_directory_2", "start_college_app.py"),
        "port": 5002,
        "url": "http://127.0.0.1:5002",
        "health_endpoint": "/"
    }
]

def check_file_exists(filepath):
    """Check if a file exists and is readable"""
    return os.path.isfile(filepath) and os.access(filepath, os.R_OK)

def check_dependencies():
    """Check if all required service files exist"""
    missing_files = []
    for service in SERVICES:
        if not check_file_exists(service["path"]):
            missing_files.append(f"{service['name']}: {service['path']}")
    
    if missing_files:
        print("❌ Missing required service files:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    return True

def is_port_in_use(port, host="127.0.0.1"):
    """Return True if a TCP port is open (in use) on host"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0

def check_service_health(service, timeout=10):
    """Check if a service is responding to HTTP requests"""
    try:
        # For aptitude service, try multiple ports
        if service["name"] == "Aptitude Service":
            for port in range(5001, 5010):
                try:
                    health_url = f"http://127.0.0.1:{port}{service['health_endpoint']}"
                    response = requests.get(health_url, timeout=2)
                    if response.status_code == 200:
                        # Update service URL with the working port
                        service["url"] = f"http://127.0.0.1:{port}"
                        service["port"] = port
                        return True
                except:
                    continue
            return False
        else:
            health_url = service["url"] + service["health_endpoint"]
            response = requests.get(health_url, timeout=timeout)
            return response.status_code == 200
    except:
        return False

def wait_for_service_startup(service, max_wait=180):
    """Wait for a service to become healthy"""
    print(f"   Waiting for {service['name']} to become ready...")
    start_time = time.time()
    
    # For Flask services, give them more time to start
    if service['name'] == 'Aptitude Service':
        time.sleep(3)  # Initial wait for Flask to start
    
    while time.time() - start_time < max_wait:
        if check_service_health(service, timeout=2):
            return True
        time.sleep(1)
    
    return False

def start_services():
    """Start all EduPath services"""
    processes = []
    
    print("🚀 Starting EduPath Services...")
    print("=" * 50)
    
    # Check dependencies first
    if not check_dependencies():
        print("\n❌ Cannot start services due to missing files.")
        return []
    
    # Start each service
    for service in SERVICES:
        try:
            print(f"Starting {service['name']}...")
            
            # Get the directory of the service file for proper working directory
            service_dir = os.path.dirname(service["path"])
            
            # Prepare environment variables
            env = os.environ.copy()
            # Flag to let child apps know they are launched by the unified launcher
            env["EDUPATH_LAUNCHER"] = "1"
            if "env" in service:
                env.update(service["env"])
            
            # Special handling for Flask apps
            if service["name"] == "Aptitude Service":
                # Set Flask to run the API server part only
                env["PYTHONPATH"] = service_dir
                env["FLASK_APP"] = "ap1_flask.py"
                env["FLASK_RUN_HOST"] = "127.0.0.1"
                # Let the Flask app find its own available port
                
            # Check port availability before starting
            if is_port_in_use(service["port"]):
                print(f"⚠️  Port {service['port']} is already in use. Skipping start for {service['name']}.")
                continue

            # Start the process without capturing output to allow it to run freely
            process = subprocess.Popen(
                [sys.executable, service["path"]], 
                cwd=service_dir,
                env=env,
                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
            )
            
            processes.append({
                "process": process,
                "service": service
            })
            
            # Wait for service to become healthy
            if wait_for_service_startup(service):
                print(f"✅ {service['name']} is running and healthy")
            else:
                print(f"⚠️  {service['name']} started but may not be fully ready")
                
        except Exception as e:
            print(f"❌ Error starting {service['name']}: {str(e)}")
    
    if processes:
        print("\n🌐 Services running at:")
        for proc_info in processes:
            if proc_info["process"].poll() is None:
                service = proc_info['service']
                print(f"   - {service['name']}: {service['url']}")
                if service['name'] == 'Aptitude Service':
                    print(f"     • API Endpoints: {service['url']}/api/question, {service['url']}/api/evaluate")
                    print(f"     • Health Check: {service['url']}/api/ping")
                elif service['name'] == 'Main App':
                    print(f"     • Login/Dashboard and main interface")
                elif service['name'] == 'College Service':
                    print(f"     • College directory and search")
        
        print("\n📝 Press Ctrl+C to stop all services")
        print("=" * 50)
    
    return processes

def main():
    """Main function to run all EduPath services"""
    processes = []
    
    try:
        processes = start_services()
        
        if not processes:
            print("❌ No services could be started.")
            return
        
        # Wait for all processes
        for proc_info in processes:
            proc_info["process"].wait()
            
    except KeyboardInterrupt:
        print("\n\n⛔ Stopping all services...")
        for proc_info in processes:
            try:
                proc_info["process"].terminate()
                print(f"   - Stopped {proc_info['service']['name']}")
            except:
                pass
        
        # Wait a bit for graceful shutdown
        time.sleep(2)
        
        # Force kill if still running
        for proc_info in processes:
            try:
                if proc_info["process"].poll() is None:
                    proc_info["process"].kill()
            except:
                pass
        
        print("✅ All services stopped.")
    
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        for proc_info in processes:
            try:
                proc_info["process"].terminate()
            except:
                pass

if __name__ == "__main__":
    main()
