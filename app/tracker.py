"""
Vehicle tracking using IoU (Intersection over Union)
Prevents duplicate challans for same vehicle
"""
import numpy as np
from collections import defaultdict

class VehicleTracker:
    def __init__(self, iou_threshold=0.3, max_age=30, max_distance=150):
        """
        Initialize vehicle tracker
        Args:
            iou_threshold: Minimum IoU to consider same vehicle (0.3 = 30% overlap)
            max_age: Maximum frames to keep tracking a vehicle without detection
            max_distance: Maximum centroid distance (pixels) to consider same vehicle
        """
        self.iou_threshold = iou_threshold
        self.max_age = max_age
        self.max_distance = max_distance
        self.next_id = 0
        self.tracks = {}  # {track_id: {'bbox': (x1,y1,x2,y2), 'age': int, 'violations': set()}}
        
    def calculate_iou(self, bbox1, bbox2):
        """
        Calculate Intersection over Union between two bounding boxes
        bbox format: (x1, y1, x2, y2)
        """
        x1_1, y1_1, x2_1, y2_1 = bbox1
        x1_2, y1_2, x2_2, y2_2 = bbox2
        
        # Calculate intersection area
        x_left = max(x1_1, x1_2)
        y_top = max(y1_1, y1_2)
        x_right = min(x2_1, x2_2)
        y_bottom = min(y2_1, y2_2)
        
        if x_right < x_left or y_bottom < y_top:
            return 0.0
        
        intersection_area = (x_right - x_left) * (y_bottom - y_top)
        
        # Calculate union area
        bbox1_area = (x2_1 - x1_1) * (y2_1 - y1_1)
        bbox2_area = (x2_2 - x1_2) * (y2_2 - y1_2)
        union_area = bbox1_area + bbox2_area - intersection_area
        
        if union_area == 0:
            return 0.0
        
        iou = intersection_area / union_area
        return iou
    
    def calculate_centroid(self, bbox):
        """Calculate centroid of bounding box"""
        x1, y1, x2, y2 = bbox
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
        return (cx, cy)
    
    def calculate_distance(self, centroid1, centroid2):
        """Calculate Euclidean distance between two centroids"""
        return np.sqrt((centroid1[0] - centroid2[0])**2 + (centroid1[1] - centroid2[1])**2)
    
    def update(self, detections):
        """
        Update tracks with new detections
        Args:
            detections: List of bounding boxes [(x1,y1,x2,y2), ...]
        Returns:
            List of track IDs corresponding to each detection
        """
        if not detections:
            # Age all existing tracks
            for track_id in list(self.tracks.keys()):
                self.tracks[track_id]['age'] += 1
                if self.tracks[track_id]['age'] > self.max_age:
                    del self.tracks[track_id]
            return []
        
        # Match detections to existing tracks
        track_ids = []
        matched_tracks = set()
        
        for detection in detections:
            best_iou = 0
            best_track_id = None
            
            detection_centroid = self.calculate_centroid(detection)
            
            # Find best matching existing track
            for track_id, track_data in self.tracks.items():
                if track_id in matched_tracks:
                    continue
                
                track_centroid = self.calculate_centroid(track_data['bbox'])
                distance = self.calculate_distance(detection_centroid, track_centroid)
                
                # Only consider tracks within max_distance
                if distance > self.max_distance:
                    continue
                    
                iou = self.calculate_iou(detection, track_data['bbox'])
                
                # Combined score: prefer closer vehicles with good IoU
                # Give bonus to very close vehicles even with lower IoU
                score = iou
                if distance < 50:  # Very close
                    score += 0.2
                    
                if score > best_iou and iou > self.iou_threshold:
                    best_iou = score
                    best_track_id = track_id
            
            if best_track_id is not None:
                # Update existing track
                self.tracks[best_track_id]['bbox'] = detection
                self.tracks[best_track_id]['age'] = 0
                matched_tracks.add(best_track_id)
                track_ids.append(best_track_id)
            else:
                # Create new track
                new_id = self.next_id
                self.next_id += 1
                self.tracks[new_id] = {
                    'bbox': detection,
                    'age': 0,
                    'violations': set()
                }
                track_ids.append(new_id)
        
        # Age unmatched tracks
        for track_id in list(self.tracks.keys()):
            if track_id not in matched_tracks:
                self.tracks[track_id]['age'] += 1
                if self.tracks[track_id]['age'] > self.max_age:
                    del self.tracks[track_id]
        
        return track_ids
    
    def has_violation(self, track_id, violation_type):
        """
        Check if track already has this violation type
        """
        if track_id not in self.tracks:
            return False
        return violation_type in self.tracks[track_id]['violations']
    
    def add_violation(self, track_id, violation_type):
        """
        Mark that this track has received a challan for this violation type
        """
        if track_id in self.tracks:
            self.tracks[track_id]['violations'].add(violation_type)
    
    def reset(self):
        """Reset all tracks"""
        self.tracks = {}
        self.next_id = 0
