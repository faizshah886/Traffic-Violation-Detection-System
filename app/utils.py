"""
Utility functions for Traffic Violation System
"""
import cv2
import numpy as np
from pathlib import Path

def extract_first_frame(video_path, output_path):
    """Extract first frame from video"""
    cap = cv2.VideoCapture(str(video_path))
    ret, frame = cap.read()
    cap.release()
    
    if ret:
        cv2.imwrite(str(output_path), frame)
        return True
    return False

def point_below_line(point, line_start, line_end):
    """
    Check if a point is below a line (for stop-line crossing detection)
    Uses cross product to determine position
    """
    x, y = point
    x1, y1 = line_start
    x2, y2 = line_end
    
    # Calculate cross product
    cross = (x2 - x1) * (y - y1) - (y2 - y1) * (x - x1)
    return cross > 0

def detect_red_light(frame):
    """
    Detect red traffic light in frame using HSV color detection
    Returns True if red light detected
    """
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # Red color range in HSV
    lower_red1 = np.array([0, 120, 70])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([170, 120, 70])
    upper_red2 = np.array([180, 255, 255])
    
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask = cv2.bitwise_or(mask1, mask2)
    
    # Check if significant red area detected
    red_pixels = cv2.countNonZero(mask)
    return red_pixels > 1000  # Threshold for red light

def save_cropped_image(frame, bbox, output_path):
    """Save cropped region from frame"""
    x1, y1, x2, y2 = bbox
    cropped = frame[int(y1):int(y2), int(x1):int(x2)]
    cv2.imwrite(str(output_path), cropped)
    return output_path

def clean_plate_text(text):
    """Clean OCR text for number plate"""
    import re
    # Remove special characters, keep alphanumeric
    cleaned = re.sub(r'[^A-Z0-9]', '', text.upper())
    return cleaned

def get_centroid(bbox):
    """Get centroid of bounding box"""
    x1, y1, x2, y2 = bbox
    cx = (x1 + x2) / 2
    cy = (y1 + y2) / 2
    return (int(cx), int(cy))
