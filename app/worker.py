"""
Background worker for video processing
"""
import cv2
import threading
from pathlib import Path
from datetime import datetime
from detector import ViolationDetector
from anpr import ANPR
from chalgen import ChallanGenerator
from database import (get_stopline_config, insert_challan, update_video_status,
                     get_video_by_id)
from models import FINE_STRUCTURE, ViolationType
from utils import save_cropped_image
from visualizer import visualize_detections, create_detection_window
from traffic_light import TrafficLightSimulator
from tracker import VehicleTracker

class VideoProcessor:
    def __init__(self, show_visualization=True):
        """Initialize video processor"""
        self.detector = ViolationDetector()
        self.anpr = ANPR(use_easyocr=False)  # Use Tesseract by default
        self.challan_gen = ChallanGenerator('app/challans')
        self.processing_jobs = {}
        self.show_visualization = show_visualization
    
    def process_video_async(self, video_id):
        """Start video processing in background thread"""
        thread = threading.Thread(target=self.process_video, args=(video_id,))
        thread.daemon = True
        thread.start()
        self.processing_jobs[video_id] = {
            'status': 'processing',
            'thread': thread,
            'started_at': datetime.now()
        }
    
    def get_job_status(self, video_id):
        """Get processing job status"""
        if video_id in self.processing_jobs:
            return self.processing_jobs[video_id]['status']
        
        # Check database
        video = get_video_by_id(video_id)
        if video:
            return video['status']
        
        return 'unknown'
    
    def process_video(self, video_id):
        """
        Process video and detect violations
        This runs in background thread
        """
        try:
            print(f"Starting processing for video {video_id}")
            
            # Update status
            update_video_status(video_id, processed=False, status='processing')
            
            # Get video info
            video = get_video_by_id(video_id)
            if not video:
                print(f"Video {video_id} not found")
                return
            
            video_path = Path('app/uploads') / video['filename']
            if not video_path.exists():
                print(f"Video file not found: {video_path}")
                update_video_status(video_id, processed=False, status='failed')
                return
            
            # Get stop-line configuration
            stopline_config = get_stopline_config(video_id)
            
            # Get traffic light durations from config
            red_duration = 10  # Default
            green_duration = 15  # Default
            processing_fps = 5  # Default: process 5 frames per second
            if stopline_config:
                red_duration = stopline_config.get('red_duration', 10)
                green_duration = stopline_config.get('green_duration', 15)
                processing_fps = stopline_config.get('processing_fps', 5)
            
            # Open video
            cap = cv2.VideoCapture(str(video_path))
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            print(f"Video: {total_frames} frames at {fps} FPS")
            print(f"Processing at {processing_fps} FPS (every {int(fps/processing_fps)} frames)")
            
            # Initialize traffic light simulator with configured durations and video FPS
            traffic_light = TrafficLightSimulator(
                red_duration=red_duration, 
                green_duration=green_duration,
                video_fps=fps
            )
            print(f"Traffic light simulator initialized: {red_duration}s RED, {green_duration}s GREEN")
            
            # Initialize vehicle tracker to prevent duplicate challans
            # iou_threshold=0.3: 30% overlap needed
            # max_age=15: Keep track for 15 frames without detection (~0.5-1 second)
            # max_distance=200: Max 200 pixels centroid movement between frames
            tracker = VehicleTracker(iou_threshold=0.3, max_age=15, max_distance=200)
            print("Vehicle tracker initialized (IoU=0.3, max_age=15, max_dist=200)")
            
            # Create visualization window if enabled
            if self.show_visualization:
                create_detection_window()
            
            frame_count = 0
            violations_detected = 0
            processed_dir = Path('app/processed')
            plates_dir = Path('app/plates')
            
            # Calculate frame skip based on processing_fps
            # If video is 30fps and processing_fps is 5, skip = 30/5 = 6 (process every 6th frame)
            frame_skip = max(1, int(fps / processing_fps))
            
            # Calculate wait time for visualization to match video speed
            # Wait time in milliseconds between frames
            wait_time_ms = int(1000 / fps) if self.show_visualization else 1
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_count += 1
                
                # Update traffic light with current frame number
                traffic_light.update_frame(frame_count)
                
                # Skip frames
                if frame_count % frame_skip != 0:
                    continue
                
                # Detect motorcycles
                motorcycles = self.detector.detect_motorcycles(frame)
                
                # Update vehicle tracker with detections
                bboxes = [m['bbox'] for m in motorcycles]
                track_ids = tracker.update(bboxes)
                
                # Debug: Log all detections periodically
                if frame_count % 50 == 0:
                    print(f"Frame {frame_count}: Detected {len(motorcycles)} vehicles, {len(tracker.tracks)} active tracks")
                
                # Detect helmets and plates for visualization
                helmets = self.detector.detect_helmets(frame)
                plates = self.detector.detect_number_plates(frame)
                
                # Show visualization if enabled
                if self.show_visualization:
                    vis_frame = visualize_detections(frame, motorcycles, helmets, plates, 
                                                     stopline_config, traffic_light)
                    cv2.imshow('Traffic Violation Detection', vis_frame)
                    # Wait appropriate time to match video FPS
                    # Multiply by frame_skip since we're skipping frames
                    key = cv2.waitKey(wait_time_ms * frame_skip) & 0xFF
                    if key == ord('q'):
                        print("Visualization stopped by user")
                        self.show_visualization = False
                        cv2.destroyAllWindows()
                
                for idx, motorcycle in enumerate(motorcycles):
                    bbox = motorcycle['bbox']
                    track_id = track_ids[idx] if idx < len(track_ids) else None
                    violations = []
                    
                    # Debug: Log motorcycle detection
                    if frame_count % 50 == 0 and idx == 0:
                        print(f"Frame {frame_count}: Detected {len(motorcycles)} motorcycles")
                        print(f"  Traffic light state: {traffic_light.get_current_state()}")
                        if stopline_config:
                            print(f"  Stop-line: ({stopline_config['x1']}, {stopline_config['y1']}) to ({stopline_config['x2']}, {stopline_config['y2']})")
                    
                    # Check helmet violation
                    if self.detector.check_helmet_violation(frame, bbox):
                        if track_id is None or not tracker.has_violation(track_id, ViolationType.HELMET):
                            violations.append(ViolationType.HELMET)
                            print(f"Frame {frame_count}: HELMET violation detected (track {track_id})")
                    
                    # Check triple riding
                    if self.detector.check_triple_riding(frame, bbox):
                        if track_id is None or not tracker.has_violation(track_id, ViolationType.TRIPLE_RIDING):
                            violations.append(ViolationType.TRIPLE_RIDING)
                            print(f"Frame {frame_count}: TRIPLE_RIDING violation detected (track {track_id})")
                    
                    # Check red light crossing
                    if stopline_config and self.detector.check_red_light_crossing(
                        frame, bbox, stopline_config, traffic_light):
                        if track_id is None or not tracker.has_violation(track_id, ViolationType.RED_LIGHT):
                            violations.append(ViolationType.RED_LIGHT)
                            print(f"Frame {frame_count}: RED_LIGHT violation detected (track {track_id})")
                    
                    # If violations detected, create challan
                    if violations:
                        # Find number plate
                        plate_data = self.detector.find_plate_for_vehicle(frame, bbox)
                        plate_number = None
                        plate_image_path = None
                        
                        if plate_data:
                            plate_bbox = plate_data['bbox']
                            # Read plate text
                            plate_number = self.anpr.read_plate(frame, plate_bbox)
                            
                            # Save plate image
                            if plate_number:
                                plate_filename = f"plate_{video_id}_{frame_count}_{idx}.jpg"
                                plate_image_path = plates_dir / plate_filename
                                self.anpr.save_plate_image(frame, plate_bbox, plate_image_path)
                                plate_image_path = str(plate_image_path)
                        
                        # Process each violation type
                        for violation_type in violations:
                            # Save violation image
                            violation_filename = f"violation_{video_id}_{frame_count}_{idx}_{violation_type}.jpg"
                            violation_image_path = processed_dir / violation_filename
                            save_cropped_image(frame, bbox, violation_image_path)
                            
                            # Get fine amount
                            fine_amount = FINE_STRUCTURE.get(violation_type, 1000)
                            
                            # Insert challan
                            challan_id = insert_challan(
                                video_id=video_id,
                                violation_type=violation_type,
                                fine_amount=fine_amount,
                                plate_number=plate_number,
                                image_path=str(violation_image_path),
                                plate_image_path=plate_image_path
                            )
                            
                            # Generate PDF
                            challan_data = {
                                'id': challan_id,
                                'plate_number': plate_number,
                                'violation_type': violation_type,
                                'fine_amount': fine_amount,
                                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                'image_path': str(violation_image_path),
                                'plate_image_path': plate_image_path,
                                'status': 'unpaid'
                            }
                            
                            self.challan_gen.generate_pdf(challan_data)
                            violations_detected += 1
                            
                            # Mark this violation as processed for this track
                            if track_id is not None:
                                tracker.add_violation(track_id, violation_type)
                            
                            print(f"Challan {challan_id} generated for {violation_type} (track {track_id})")
                
                # Progress update
                if frame_count % 100 == 0:
                    progress = (frame_count / total_frames) * 100
                    print(f"Progress: {progress:.1f}% - Violations: {violations_detected}")
            
            cap.release()
            
            # Close visualization window
            if self.show_visualization:
                cv2.destroyAllWindows()
            
            # Mark as completed
            update_video_status(video_id, processed=True, status='completed')
            self.processing_jobs[video_id]['status'] = 'completed'
            
            print(f"Processing completed for video {video_id}")
            print(f"Total violations detected: {violations_detected}")
            
        except Exception as e:
            print(f"Error processing video {video_id}: {e}")
            import traceback
            traceback.print_exc()
            update_video_status(video_id, processed=False, status='failed')
            if video_id in self.processing_jobs:
                self.processing_jobs[video_id]['status'] = 'failed'

# Global processor instance
processor = VideoProcessor()
