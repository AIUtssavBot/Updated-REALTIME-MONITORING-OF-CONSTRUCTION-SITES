from flask import Blueprint, render_template, Response, jsonify, request
from app.utils.camera import CameraManager
from app.utils.detection import SafetyGearDetector, ProximityDetector
from app.database import ViolationDatabase
from app import socketio
import json
import cv2
import time
import os
import sqlite3

main = Blueprint('main', __name__)
camera_manager = CameraManager()
safety_detector = SafetyGearDetector()
proximity_detector = ProximityDetector()
db = ViolationDatabase()

# Store alerts and violations
alerts = {
    'safety_gear': [],
    'proximity': []
}

# Create necessary directories
os.makedirs('static/violations', exist_ok=True)
os.makedirs('static/violations/safety_gear', exist_ok=True)
os.makedirs('static/violations/proximity', exist_ok=True)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/video_feed/<int:camera_id>')
def video_feed(camera_id):
    return Response(generate_frames(camera_id),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

def generate_frames(camera_id):
    camera = camera_manager.get_camera(camera_id)
    if not camera:
        return None
        
    while True:
        frame = camera.get_frame()
        if frame is None:
            continue
            
        # Run safety gear detection
        frame, safety_violations = safety_detector.detect(frame, camera_id)
        
        # Run proximity detection
        frame, proximity_alerts = proximity_detector.detect(frame, camera_id)
        
        # If violations detected, emit alerts via socket and store in database
        if safety_violations:
            alerts['safety_gear'].append({
                'camera_id': camera_id,
                'violations': safety_violations,
                'timestamp': time.time()
            })
            socketio.emit('safety_alert', json.dumps({
                'camera_id': camera_id,
                'violations': safety_violations
            }))
            
            # Store in database
            for violation in safety_violations:
                db.add_violation(violation)
            
        if proximity_alerts:
            alerts['proximity'].append({
                'camera_id': camera_id,
                'alerts': proximity_alerts,
                'timestamp': time.time()
            })
            socketio.emit('proximity_alert', json.dumps({
                'camera_id': camera_id,
                'alerts': proximity_alerts
            }))
            
            # Store in database
            for alert in proximity_alerts:
                db.add_violation(alert)
        
        # Encode the processed frame for streaming
        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            continue
            
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@main.route('/alerts')
def get_alerts():
    return jsonify(alerts)

@main.route('/violations')
def violations():
    return render_template('violations.html')

@main.route('/api/violations')
def get_violations():
    """API endpoint to get all violations"""
    # Get filter parameters
    camera_id = request.args.get('camera_id', type=int)
    violation_type = request.args.get('type')
    status = request.args.get('status')
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    # Get violations from database
    violations = db.get_violations(
        limit=limit,
        offset=offset,
        camera_id=camera_id,
        violation_type=violation_type,
        status=status
    )
    
    # Format violations for frontend
    formatted_violations = []
    for violation in violations:
        formatted_violations.append({
            'id': violation['id'],
            'timestamp': violation['timestamp'],
            'camera_id': violation['camera_id'],
            'type': violation['violation_type'],
            'details': violation['details'],
            'duration': violation['duration'],
            'screenshot': violation['screenshot_path'],
            'status': violation['status'],
            'analysis': violation['analysis']
        })
    
    return jsonify(formatted_violations)

@main.route('/api/violations', methods=['POST'])
def add_violation():
    """Add a new violation to the database"""
    try:
        violation_data = request.get_json()
        violation_id = db.add_violation(violation_data)
        return jsonify({'success': True, 'id': violation_id, 'message': 'Violation added successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error adding violation: {str(e)}'}), 500

@main.route('/api/violations/<int:violation_id>/resolve', methods=['POST'])
def resolve_violation(violation_id):
    """Resolve a violation"""
    success = db.update_violation_status(violation_id, 'resolved')
    if success:
        return jsonify({'success': True, 'message': 'Violation resolved successfully'})
    else:
        return jsonify({'success': False, 'message': 'Violation not found'}), 404

@main.route('/api/statistics')
def get_statistics():
    """Get violation statistics"""
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    stats = db.get_violation_stats(date_from, date_to)
    return jsonify(stats)

@main.route('/api/violations/clear', methods=['POST'])
def clear_all_violations():
    """Clear all violations from database"""
    try:
        # Clear from database
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM violations')
        conn.commit()
        conn.close()
        
        # Clear from detection classes
        safety_detector.violation_history = []
        proximity_detector.violation_history = []
        
        return jsonify({'success': True, 'message': 'All violations cleared successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error clearing violations: {str(e)}'}), 500 