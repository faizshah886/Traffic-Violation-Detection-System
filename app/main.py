# GitHub Copilot Instructions:
# Using the SRS in this file, automatically generate:
# - Flask backend
# - Video upload endpoints
# - Stop-line drawing page (Canvas)
# - Save configuration API
# - Background worker to process videos
# - YOLO detection pipeline
# - Helmet, triple riding, red-light detection
# - ANPR OCR extraction
# - Challan generator (PDF)
# - SQLite models and tables
# - HTML templates for upload, configure, challan list, and challan details
# Follow the folder structure and complete the code with no human intervention.

"""
Flask Backend for Smart Traffic Violation Detection System
"""
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from werkzeug.utils import secure_filename
import os
from pathlib import Path
from datetime import datetime
import cv2

# Import local modules
from database import (init_database, insert_video, save_stopline_config, 
                     get_stopline_config, get_all_challans, get_challan_by_id,
                     get_video_by_id)
from worker import processor
from utils import extract_first_frame

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'app/uploads'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size

# Allowed video extensions
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Initialize database on startup
with app.app_context():
    init_database()

@app.route('/')
def index():
    """Home page - redirect to upload"""
    return redirect(url_for('upload_page'))

@app.route('/upload')
def upload_page():
    """Video upload page"""
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_video():
    """
    Handle video upload
    POST /upload
    Returns: JSON with video_id and redirect URL
    """
    try:
        # Check if file is present
        if 'video' not in request.files:
            return jsonify({'error': 'No video file provided'}), 400
        
        file = request.files['video']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Allowed: mp4, avi, mov, mkv'}), 400
        
        # Save file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = Path(app.config['UPLOAD_FOLDER']) / filename
        file.save(str(filepath))
        
        # Create video record
        video_id = insert_video(filename)
        
        # Extract first frame for stop-line configuration
        frame_path = Path('app/frames') / f"{video_id}.jpg"
        extract_first_frame(filepath, frame_path)
        
        return jsonify({
            'success': True,
            'video_id': video_id,
            'redirect': url_for('configure_stopline', video_id=video_id)
        })
        
    except Exception as e:
        print(f"Upload error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/configure/<int:video_id>')
def configure_stopline(video_id):
    """
    Display stop-line configuration page
    GET /configure/<video_id>
    """
    video = get_video_by_id(video_id)
    if not video:
        return "Video not found", 404
    
    # Check if frame exists
    frame_file = Path('app/frames') / f"{video_id}.jpg"
    if not frame_file.exists():
        return "Frame not extracted. Please try uploading again.", 404
    
    return render_template('configure.html', video_id=video_id)

@app.route('/save_config/<int:video_id>', methods=['POST'])
def save_config(video_id):
    """
    Save stop-line configuration
    POST /save_config/<video_id>
    Body: {
        "stopline": {"x1": int, "y1": int, "x2": int, "y2": int},
        "red_duration": int (optional, default 10),
        "green_duration": int (optional, default 15),
        "processing_fps": int (optional, default 5)
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'stopline' not in data:
            return jsonify({'error': 'Stop-line data required'}), 400
        
        stopline = data['stopline']
        required_fields = ['x1', 'y1', 'x2', 'y2']
        
        if not all(field in stopline for field in required_fields):
            return jsonify({'error': 'Missing stop-line coordinates'}), 400
        
        # Get traffic light durations and processing settings (optional)
        red_duration = data.get('red_duration', 10)
        green_duration = data.get('green_duration', 15)
        processing_fps = data.get('processing_fps', 5)
        
        # Save configuration with traffic light settings
        config_data = {
            **stopline,
            'red_duration': red_duration,
            'green_duration': green_duration,
            'processing_fps': processing_fps
        }
        save_stopline_config(video_id, config_data)
        
        return jsonify({
            'success': True,
            'message': 'Configuration saved successfully',
            'redirect': url_for('process_video', video_id=video_id)
        })
        
    except Exception as e:
        print(f"Config save error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/process/<int:video_id>', methods=['POST'])
def process_video(video_id):
    """
    Start video processing
    POST /process/<video_id>
    """
    try:
        video = get_video_by_id(video_id)
        if not video:
            return jsonify({'error': 'Video not found'}), 404
        
        # Start background processing
        processor.process_video_async(video_id)
        
        return jsonify({
            'success': True,
            'message': 'Processing started',
            'video_id': video_id,
            'status_url': url_for('job_status', video_id=video_id)
        })
        
    except Exception as e:
        print(f"Process error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/job_status/<int:video_id>')
def job_status(video_id):
    """
    Get processing job status
    GET /job_status/<video_id>
    Returns: JSON with status
    """
    status = processor.get_job_status(video_id)
    return jsonify({
        'video_id': video_id,
        'status': status
    })

@app.route('/challans')
def challans_list():
    """
    Display all challans
    GET /challans
    """
    challans = get_all_challans()
    return render_template('challans.html', challans=challans)

@app.route('/challans/api')
def challans_api():
    """
    API endpoint for challans list
    GET /challans/api
    """
    challans = get_all_challans()
    return jsonify(challans)

@app.route('/challan/<int:challan_id>')
def challan_detail(challan_id):
    """
    Display challan details
    GET /challan/<challan_id>
    """
    challan = get_challan_by_id(challan_id)
    if not challan:
        return "Challan not found", 404
    
    return render_template('challan_detail.html', challan=challan)

@app.route('/challan/<int:challan_id>/api')
def challan_api(challan_id):
    """
    API endpoint for challan details
    GET /challan/<challan_id>/api
    """
    challan = get_challan_by_id(challan_id)
    if not challan:
        return jsonify({'error': 'Challan not found'}), 404
    
    return jsonify(challan)

@app.route('/challan/<int:challan_id>/pdf')
def download_challan_pdf(challan_id):
    """Download challan PDF"""
    pdf_path = Path(__file__).parent / 'challans' / f"{challan_id}.pdf"
    if pdf_path.exists():
        return send_file(str(pdf_path.absolute()), as_attachment=True)
    return "PDF not found", 404

@app.route('/frames/<path:filename>')
def serve_frame(filename):
    """Serve frame images"""
    frame_path = Path(__file__).parent / 'frames' / filename
    if frame_path.exists():
        return send_file(str(frame_path.absolute()))
    return "Frame not found", 404

@app.route('/processed/<path:filename>')
def serve_processed(filename):
    """Serve processed violation images"""
    processed_path = Path(__file__).parent / 'processed' / filename
    if processed_path.exists():
        return send_file(str(processed_path.absolute()))
    return "Image not found", 404

@app.route('/plates/<path:filename>')
def serve_plate(filename):
    """Serve plate images"""
    plate_path = Path(__file__).parent / 'plates' / filename
    if plate_path.exists():
        return send_file(str(plate_path.absolute()))
    return "Plate not found", 404

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    # Ensure all directories exist
    for directory in ['uploads', 'frames', 'processed', 'plates', 'challans']:
        Path(f'app/{directory}').mkdir(exist_ok=True)
    
    print("Starting Traffic Violation Detection System...")
    print("Server running on http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
