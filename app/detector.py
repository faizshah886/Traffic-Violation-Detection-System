"""
YOLO-based detection module for traffic violations
"""
import cv2
import numpy as np
from pathlib import Path
from ultralytics import YOLO
from utils import get_centroid, point_below_line, detect_red_light

class ViolationDetector:
    def __init__(self):
        """Initialize YOLO models"""
        yolo_dir = Path(__file__).parent.parent / 'yolo'
        
        # Load YOLO models (will use YOLOv8 pretrained models if custom not available)
        try:
            self.helmet_model = YOLO(str(yolo_dir / 'helmets.pt'))
        except:
            print("Custom helmet model not found, using YOLOv8n")
            self.helmet_model = YOLO('yolov8n.pt')
        
        try:
            self.motorcycle_model = YOLO(str(yolo_dir / 'motorcycle.pt'))
        except:
            print("Custom motorcycle model not found, using YOLOv8n")
            self.motorcycle_model = YOLO('yolov8n.pt')
        
        try:
            self.plate_model = YOLO(str(yolo_dir / 'plates.pt'))
        except:
            print("Custom plate model not found, using YOLOv8n")
            self.plate_model = YOLO('yolov8n.pt')
    
    def detect_motorcycles(self, frame):
        """Detect motorcycles and cars in frame"""
        results = self.motorcycle_model(frame, verbose=False)
        motorcycles = []
        
        for result in results:
            boxes = result.boxes
            for box in boxes:
                cls = int(box.cls)
                # COCO classes: 2=car, 3=motorcycle, 5=bus, 7=truck
                # Include cars and motorcycles for detection
                if cls in [2, 3, 4, 5, 7]:  # car, motorcycle, motorbike, bus, truck
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    conf = float(box.conf)
                    motorcycles.append({
                        'bbox': (x1, y1, x2, y2),
                        'confidence': conf,
                        'class': cls
                    })
        
        return motorcycles
    
    def detect_helmets(self, frame):
        """Detect helmets in frame"""
        results = self.helmet_model(frame, verbose=False)
        helmets = []
        
        for result in results:
            boxes = result.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = float(box.conf)
                helmets.append({
                    'bbox': (x1, y1, x2, y2),
                    'confidence': conf
                })
        
        return helmets
    
    def detect_persons(self, frame, roi=None):
        """Detect persons in frame or ROI"""
        if roi:
            x1, y1, x2, y2 = roi
            crop = frame[int(y1):int(y2), int(x1):int(x2)]
            results = self.motorcycle_model(crop, verbose=False)
        else:
            results = self.motorcycle_model(frame, verbose=False)
        
        persons = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                # Class 0 is person in COCO dataset
                if int(box.cls) == 0:
                    x1_p, y1_p, x2_p, y2_p = box.xyxy[0].cpu().numpy()
                    if roi:
                        # Adjust coordinates back to original frame
                        x1_p += roi[0]
                        x2_p += roi[0]
                        y1_p += roi[1]
                        y2_p += roi[1]
                    
                    conf = float(box.conf)
                    persons.append({
                        'bbox': (x1_p, y1_p, x2_p, y2_p),
                        'confidence': conf
                    })
        
        return persons
    
    def detect_number_plates(self, frame):
        """Detect number plates in frame"""
        results = self.plate_model(frame, verbose=False)
        plates = []
        
        for result in results:
            boxes = result.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = float(box.conf)
                plates.append({
                    'bbox': (x1, y1, x2, y2),
                    'confidence': conf
                })
        
        return plates
    
    def check_helmet_violation(self, frame, motorcycle_bbox):
        """Check if rider on motorcycle is wearing helmet"""
        # Detect persons on motorcycle
        persons = self.detect_persons(frame, roi=motorcycle_bbox)
        
        if len(persons) == 0:
            return False
        
        # Detect helmets in the motorcycle region
        helmets = self.detect_helmets(frame)
        
        # Check if each person has a helmet
        for person in persons:
            person_bbox = person['bbox']
            person_center = get_centroid(person_bbox)
            
            # Check if any helmet is near this person's head
            has_helmet = False
            for helmet in helmets:
                helmet_center = get_centroid(helmet['bbox'])
                # Check if helmet is near person's upper body
                distance = np.sqrt((person_center[0] - helmet_center[0])**2 + 
                                 (person_center[1] - helmet_center[1])**2)
                if distance < 100:  # Threshold for proximity
                    has_helmet = True
                    break
            
            if not has_helmet:
                return True  # Violation detected
        
        return False
    
    def check_triple_riding(self, frame, motorcycle_bbox):
        """Check if more than 2 persons on motorcycle"""
        persons = self.detect_persons(frame, roi=motorcycle_bbox)
        return len(persons) > 2
    
    def check_red_light_crossing(self, frame, motorcycle_bbox, stopline_config, traffic_light):
        """
        Check if motorcycle crosses stop-line on red light
        Args:
            frame: Current video frame
            motorcycle_bbox: Bounding box of motorcycle
            stopline_config: Stop-line coordinates
            traffic_light: TrafficLightSimulator instance
        """
        if not stopline_config:
            return False
        
        # Check if traffic light is red (simulated)
        is_red = traffic_light.is_red() if traffic_light else False
        
        # Get motorcycle centroid
        centroid = get_centroid(motorcycle_bbox)
        
        # Get stop-line coordinates
        x1 = stopline_config['x1']
        y1 = stopline_config['y1']
        x2 = stopline_config['x2']
        y2 = stopline_config['y2']
        
        # Check if centroid crossed the line
        crossed = point_below_line(centroid, (x1, y1), (x2, y2))
        
        # Debug logging (occasionally)
        import random
        if random.random() < 0.05:  # Log 5% of checks
            print(f"  Red light check: is_red={is_red}, crossed={crossed}, centroid={centroid}")
        
        # Return True only if light is red AND motorcycle crossed
        return is_red and crossed
    
    def find_plate_for_vehicle(self, frame, vehicle_bbox):
        """Find number plate for a specific vehicle"""
        # Detect all plates in frame
        plates = self.detect_number_plates(frame)
        
        if not plates:
            return None
        
        # Find plate closest to vehicle
        vehicle_center = get_centroid(vehicle_bbox)
        min_distance = float('inf')
        closest_plate = None
        
        for plate in plates:
            plate_center = get_centroid(plate['bbox'])
            distance = np.sqrt((vehicle_center[0] - plate_center[0])**2 + 
                             (vehicle_center[1] - plate_center[1])**2)
            if distance < min_distance:
                min_distance = distance
                closest_plate = plate
        
        # Only return plate if it's reasonably close to vehicle
        if min_distance < 300:
            return closest_plate
        
        return None
