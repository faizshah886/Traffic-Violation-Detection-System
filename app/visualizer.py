"""
Live visualization for YOLO detection - Shows detections in real-time window
"""
import cv2
from pathlib import Path

def visualize_detections(frame, motorcycles, helmets, plates, stopline_config=None, traffic_light=None):
    """
    Draw bounding boxes and visualizations on frame
    Returns annotated frame
    """
    vis_frame = frame.copy()
    
    # Draw traffic light indicator in top-right corner
    if traffic_light:
        state = traffic_light.get_current_state()
        time_remaining = int(traffic_light.get_time_remaining())
        
        # Draw traffic light circle
        light_x = frame.shape[1] - 100
        light_y = 50
        
        if state == 'RED':
            color = (0, 0, 255)  # Red
            text = f"RED: {time_remaining}s"
        else:
            color = (0, 255, 0)  # Green
            text = f"GREEN: {time_remaining}s"
        
        # Draw filled circle for traffic light
        cv2.circle(vis_frame, (light_x, light_y), 30, color, -1)
        cv2.circle(vis_frame, (light_x, light_y), 30, (255, 255, 255), 3)
        
        # Draw text
        cv2.putText(vis_frame, text, (light_x - 60, light_y + 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    
    # Draw motorcycles in green
    for moto in motorcycles:
        x1, y1, x2, y2 = [int(v) for v in moto['bbox']]
        cv2.rectangle(vis_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(vis_frame, f"Motorcycle {moto['confidence']:.2f}", 
                   (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
    # Draw helmets in blue
    for helmet in helmets:
        x1, y1, x2, y2 = [int(v) for v in helmet['bbox']]
        cv2.rectangle(vis_frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
        cv2.putText(vis_frame, "Helmet", (x1, y1-10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
    
    # Draw plates in yellow
    for plate in plates:
        x1, y1, x2, y2 = [int(v) for v in plate['bbox']]
        cv2.rectangle(vis_frame, (x1, y1), (x2, y2), (0, 255, 255), 2)
        cv2.putText(vis_frame, "Plate", (x1, y1-10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
    
    # Draw stop-line if configured
    if stopline_config:
        x1 = int(stopline_config['x1'])
        y1 = int(stopline_config['y1'])
        x2 = int(stopline_config['x2'])
        y2 = int(stopline_config['y2'])
        cv2.line(vis_frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
        cv2.putText(vis_frame, "STOP LINE", (x1+10, y1-10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    
    return vis_frame

def create_detection_window():
    """Create named window for displaying detections"""
    cv2.namedWindow('Traffic Violation Detection', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('Traffic Violation Detection', 1280, 720)
