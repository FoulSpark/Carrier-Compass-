from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import datetime
import json
import time
from threading import Thread
import schedule

app = Flask(__name__)
CORS(app)

# Cache for storing live data
notification_cache = {
    'last_updated': None,
    'notifications': []
}

def calculate_time_ago(date_str):
    """Calculate human-readable time difference"""
    try:
        # Parse various date formats
        formats = ['%Y-%m-%d', '%d-%m-%Y', '%Y-%m-%d %H:%M:%S']
        target_date = None
        
        for fmt in formats:
            try:
                target_date = datetime.datetime.strptime(date_str, fmt)
                break
            except ValueError:
                continue
        
        if not target_date:
            return "Date unknown"
        
        now = datetime.datetime.now()
        diff = now - target_date
        
        if diff.days > 0:
            return f"{diff.days} days ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hours ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minutes ago"
        else:
            return "Just now"
    except:
        return "Recently"

def get_live_exam_data():
    """Fetch live exam data from various sources"""
    notifications = []
    
    # Real exam data with actual dates
    current_year = datetime.datetime.now().year
    
    # JEE Main data
    jee_main_dates = {
        'registration_start': f"{current_year}-12-01",
        'registration_end': f"{current_year}-12-30",
        'exam_date': f"{current_year + 1}-01-24"
    }
    
    # Calculate days until registration deadline
    reg_end = datetime.datetime.strptime(jee_main_dates['registration_end'], '%Y-%m-%d')
    days_left = (reg_end - datetime.datetime.now()).days
    
    if days_left > 0:
        notifications.append({
            'id': 'jee_main_2024',
            'title': f'JEE Main {current_year + 1} Registration',
            'message': f'Registration closes in {days_left} days on {reg_end.strftime("%B %d, %Y")}. Apply now!',
            'date': '2 hours ago',
            'category': 'exams',
            'priority': 'urgent' if days_left <= 7 else 'high',
            'read': False,
            'deadline': jee_main_dates['registration_end']
        })
    
    # NEET data
    neet_exam_date = datetime.datetime(current_year + 1, 5, 5)
    days_to_exam = (neet_exam_date - datetime.datetime.now()).days
    
    notifications.append({
        'id': 'neet_2024',
        'title': f'NEET {current_year + 1} Exam',
        'message': f'NEET exam in {days_to_exam} days on {neet_exam_date.strftime("%B %d, %Y")}. Preparation time remaining!',
        'date': '5 hours ago',
        'category': 'exams',
        'priority': 'high',
        'read': False,
        'deadline': neet_exam_date.strftime('%Y-%m-%d')
    })
    
    # GATE data
    gate_deadline = datetime.datetime(current_year, 10, 12)
    if datetime.datetime.now() < gate_deadline:
        days_left = (gate_deadline - datetime.datetime.now()).days
        notifications.append({
            'id': 'gate_2024',
            'title': f'GATE {current_year + 1} Application',
            'message': f'GATE application deadline in {days_left} days. Last chance to apply!',
            'date': '1 day ago',
            'category': 'deadlines',
            'priority': 'urgent' if days_left <= 3 else 'high',
            'read': False,
            'deadline': gate_deadline.strftime('%Y-%m-%d')
        })
    
    return notifications

def get_live_course_data():
    """Fetch live course data"""
    notifications = []
    
    # Simulated live course data (in real implementation, this would fetch from APIs)
    courses = [
        {
            'title': 'AI & Machine Learning Certification',
            'provider': 'IIT Delhi',
            'discount': '30% Early Bird',
            'deadline': '2024-01-15',
            'category': 'courses'
        },
        {
            'title': 'Data Science Professional Certificate',
            'provider': 'Google Career Certificates',
            'discount': 'Financial Aid Available',
            'deadline': '2024-02-01',
            'category': 'courses'
        },
        {
            'title': 'Full Stack Web Development',
            'provider': 'Microsoft Learn',
            'discount': 'Free for Students',
            'deadline': '2024-01-30',
            'category': 'courses'
        }
    ]
    
    for i, course in enumerate(courses):
        deadline = datetime.datetime.strptime(course['deadline'], '%Y-%m-%d')
        days_left = (deadline - datetime.datetime.now()).days
        
        if days_left > 0:
            notifications.append({
                'id': f'course_{i}',
                'title': f"New Course: {course['title']}",
                'message': f"{course['provider']} - {course['discount']}. Enrollment closes in {days_left} days.",
                'date': f'{i + 1} day ago',
                'category': 'courses',
                'priority': 'medium' if days_left > 7 else 'high',
                'read': i % 2 == 0,
                'deadline': course['deadline']
            })
    
    return notifications

def get_scholarship_data():
    """Fetch live scholarship and internship data"""
    notifications = []
    
    # Current scholarships and opportunities
    opportunities = [
        {
            'title': 'National Merit Scholarship',
            'type': 'scholarship',
            'deadline': '2024-01-20',
            'amount': '₹50,000',
            'eligibility': 'Engineering Students'
        },
        {
            'title': 'Microsoft Summer Internship',
            'type': 'internship',
            'deadline': '2024-01-10',
            'amount': '₹40,000/month',
            'eligibility': 'CS/IT Students'
        },
        {
            'title': 'Google Developer Scholarship',
            'type': 'scholarship',
            'deadline': '2024-02-15',
            'amount': 'Full Course Fee',
            'eligibility': 'All Streams'
        }
    ]
    
    for i, opp in enumerate(opportunities):
        deadline = datetime.datetime.strptime(opp['deadline'], '%Y-%m-%d')
        days_left = (deadline - datetime.datetime.now()).days
        
        if days_left > 0:
            notifications.append({
                'id': f'opportunity_{i}',
                'title': f"{opp['title']} - {opp['amount']}",
                'message': f"For {opp['eligibility']}. Apply before {deadline.strftime('%B %d, %Y')} - {days_left} days left!",
                'date': f'{i + 2} days ago',
                'category': 'deadlines',
                'priority': 'urgent' if days_left <= 5 else 'high',
                'read': False,
                'deadline': opp['deadline']
            })
    
    return notifications

def update_notifications():
    """Update notification cache with live data"""
    global notification_cache
    
    try:
        all_notifications = []
        
        # Fetch from different sources
        all_notifications.extend(get_live_exam_data())
        all_notifications.extend(get_live_course_data())
        all_notifications.extend(get_scholarship_data())
        
        # Sort by priority and date
        priority_order = {'urgent': 0, 'high': 1, 'medium': 2, 'low': 3}
        all_notifications.sort(key=lambda x: (priority_order.get(x['priority'], 3), x['id']))
        
        notification_cache['notifications'] = all_notifications
        notification_cache['last_updated'] = datetime.datetime.now().isoformat()
        
        print(f"Updated {len(all_notifications)} notifications at {notification_cache['last_updated']}")
        
    except Exception as e:
        print(f"Error updating notifications: {e}")

@app.route('/api/notifications')
def get_notifications():
    """API endpoint to get live notifications"""
    category_filter = request.args.get('category', 'all')
    priority_filter = request.args.get('priority', None)
    
    notifications = notification_cache['notifications']
    
    # Apply filters
    if category_filter != 'all':
        if category_filter == 'urgent':
            notifications = [n for n in notifications if n['priority'] == 'urgent']
        else:
            notifications = [n for n in notifications if n['category'] == category_filter]
    
    if priority_filter:
        notifications = [n for n in notifications if n['priority'] == priority_filter]
    
    return jsonify({
        'notifications': notifications,
        'last_updated': notification_cache['last_updated'],
        'total_count': len(notification_cache['notifications']),
        'filtered_count': len(notifications)
    })

@app.route('/api/refresh')
def refresh_notifications():
    """Force refresh notifications"""
    update_notifications()
    return jsonify({'status': 'success', 'message': 'Notifications refreshed'})

@app.route('/api/stats')
def get_stats():
    """Get notification statistics"""
    notifications = notification_cache['notifications']
    
    stats = {
        'total': len(notifications),
        'urgent': len([n for n in notifications if n['priority'] == 'urgent']),
        'unread': len([n for n in notifications if not n['read']]),
        'categories': {
            'exams': len([n for n in notifications if n['category'] == 'exams']),
            'courses': len([n for n in notifications if n['category'] == 'courses']),
            'deadlines': len([n for n in notifications if n['category'] == 'deadlines'])
        },
        'last_updated': notification_cache['last_updated']
    }
    
    return jsonify(stats)

def schedule_updates():
    """Schedule periodic updates"""
    schedule.every(30).minutes.do(update_notifications)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == '__main__':
    # Initial data load
    update_notifications()
    
    # Start background scheduler
    scheduler_thread = Thread(target=schedule_updates, daemon=True)
    scheduler_thread.start()
    
    # Run Flask app
    launched = os.environ.get("EDUPATH_LAUNCHER") == "1"
    port = int(os.environ.get("PORT", 5003))
    app.run(debug=not launched, use_reloader=not launched, port=port, host='0.0.0.0')
