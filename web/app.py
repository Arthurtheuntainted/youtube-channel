"""
Flask Web Application for Cavern Wireless.
Provides public status page and admin dashboard.
"""

import logging
from functools import wraps
from flask import Flask, render_template, jsonify, request, session, redirect, url_for

from app.config import Config
from app.database import Database
from app.scheduler import RadioScheduler

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = "cavern-wireless-secret-key-change-in-production"

# Initialize components
db = Database(Config.DB_PATH)
scheduler: RadioScheduler = None

def set_scheduler(sched: RadioScheduler):
    """Set scheduler instance for web app."""
    global scheduler
    scheduler = sched

def require_admin(f):
    """Decorator to require admin authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    """Public status page."""
    return render_template('index.html')

@app.route('/admin')
@require_admin
def admin_dashboard():
    """Admin dashboard."""
    return render_template('admin.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login page."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == Config.ADMIN_USERNAME and password == Config.ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('login.html', error="Invalid credentials")
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Admin logout."""
    session.pop('admin_logged_in', None)
    return redirect(url_for('index'))

@app.route('/api/status')
def api_status():
    """Get current system status."""
    status = {
        'queue_count': db.get_queue_count(),
        'playback_status': db.get_playback_status(),
        'current_story': None,
        'system': {}
    }
    
    # Get current playing story
    current = db.get_current_playing()
    if current:
        status['current_story'] = {
            'ticket': current['ticket_number'],
            'title': current['story_title'],
            'author': current['name'],
            'status': current['status']
        }
    
    # Get scheduler status if available
    if scheduler:
        sched_status = scheduler.get_status()
        status['system'] = {
            'ollama': 'ONLINE' if sched_status['ollama_available'] else 'OFFLINE',
            'tts': 'ONLINE' if sched_status['tts_available'] else 'OFFLINE',
            'ffmpeg': 'ONLINE' if sched_status['ffmpeg_available'] else 'OFFLINE',
            'google': 'ONLINE' if sched_status['google_connected'] else 'OFFLINE',
            'scheduler_running': sched_status['is_running']
        }
    else:
        status['system'] = {
            'ollama': 'UNKNOWN',
            'tts': 'UNKNOWN',
            'ffmpeg': 'UNKNOWN',
            'google': 'UNKNOWN',
            'scheduler_running': False
        }
    
    return jsonify(status)

@app.route('/api/queue')
def api_queue():
    """Get queued stories."""
    stories = db.get_all_stories(limit=20)
    queue = []
    
    for s in stories:
        if s['status'] in ['QUEUED', 'PENDING_APPROVAL', 'PLAYING', 'PROCESSING']:
            queue.append({
                'id': s['id'],
                'ticket': s['ticket_number'],
                'title': s['story_title'],
                'author': s['name'],
                'status': s['status'],
                'created_at': s['created_at']
            })
    
    return jsonify(queue)

@app.route('/api/history')
def api_history():
    """Get recent broadcast history."""
    stories = db.get_all_stories(limit=10)
    history = []
    
    for s in stories:
        if s['status'] == 'COMPLETED':
            history.append({
                'ticket': s['ticket_number'],
                'title': s['story_title'],
                'author': s['name'],
                'completed_at': s['updated_at']
            })
    
    return jsonify(history)

@app.route('/api/admin/stories')
@require_admin
def api_admin_stories():
    """Get all stories for admin."""
    stories = db.get_all_stories(limit=100)
    return jsonify([{
        'id': s['id'],
        'ticket': s['ticket_number'],
        'title': s['story_title'],
        'author': s['name'],
        'status': s['status'],
        'created_at': s['created_at'],
        'rejection_reason': s.get('rejection_reason')
    } for s in stories])

@app.route('/api/admin/approve/<int:story_id>', methods=['POST'])
@require_admin
def api_approve_story(story_id):
    """Approve a pending story."""
    if db.approve_story(story_id):
        return jsonify({'success': True})
    return jsonify({'success': False}), 400

@app.route('/api/admin/reject/<int:story_id>', methods=['POST'])
@require_admin
def api_reject_story(story_id):
    """Reject a pending story."""
    reason = request.json.get('reason', 'No reason provided')
    if db.reject_story(story_id, reason):
        return jsonify({'success': True})
    return jsonify({'success': False}), 400

@app.route('/api/admin/delete/<int:story_id>', methods=['POST'])
@require_admin
def api_delete_story(story_id):
    """Delete a story."""
    if db.delete_story(story_id):
        return jsonify({'success': True})
    return jsonify({'success': False}), 400

@app.route('/api/admin/retry/<int:story_id>', methods=['POST'])
@require_admin
def api_retry_story(story_id):
    """Retry a failed story."""
    if db.retry_failed_story(story_id):
        return jsonify({'success': True})
    return jsonify({'success': False}), 400

@app.route('/api/admin/pause', methods=['POST'])
@require_admin
def api_pause_playback():
    """Pause playback."""
    db.pause_playback()
    return jsonify({'success': True})

@app.route('/api/admin/resume', methods=['POST'])
@require_admin
def api_resume_playback():
    """Resume playback."""
    db.resume_playback()
    return jsonify({'success': True})

@app.route('/api/admin/skip', methods=['POST'])
@require_admin
def api_skip_current():
    """Skip current story (mark as completed)."""
    current = db.get_current_playing()
    if current:
        db.mark_completed(current['id'], 0)
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'No story currently playing'}), 400

if __name__ == '__main__':
    app.run(host=Config.WEB_HOST, port=Config.WEB_PORT, debug=False)
