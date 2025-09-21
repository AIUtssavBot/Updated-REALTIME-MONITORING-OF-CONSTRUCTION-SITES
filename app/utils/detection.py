import cv2
import numpy as np
import time
import os
import base64
from collections import defaultdict
from datetime import datetime

class SafetyGearDetector:
    def __init__(self, model_path=None):
        """
        Initialize the safety gear detector with improved real-time detection.
        """
        self.model_path = model_path
        self.model = None
        self.classes = ["helmet", "vest", "mask", "gloves", "boots"]
        self.violation_time = defaultdict(dict)  # Track violation time {camera_id: {worker_id: start_time}}
        self.alert_threshold = 3  # Alert after 3 seconds of violation
        self.violation_history = []  # Store violation history
        self.screenshot_dir = "static/violations"
        self.load_model()
        self.setup_directories()
        
    def setup_directories(self):
        """Create necessary directories for storing violation data"""
        os.makedirs(self.screenshot_dir, exist_ok=True)
        os.makedirs(f"{self.screenshot_dir}/safety_gear", exist_ok=True)
        os.makedirs(f"{self.screenshot_dir}/proximity", exist_ok=True)
        
    def load_model(self):
        """
        Load the safety gear detection model.
        Using OpenCV's DNN module for better real-time performance.
        """
        try:
            # Try to load a pre-trained model for person detection
            # For now, we'll use HOG detector but with improved parameters
            self.hog = cv2.HOGDescriptor()
            self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
            print("Safety gear detection model loaded successfully")
        except Exception as e:
            print(f"Error loading safety gear model: {e}")
            self.hog = None
        
    def detect(self, frame, camera_id):
        """
        Detect safety gear violations in the frame using real-time analysis.
        Returns the processed frame and a list of violations.
        """
        if self.hog is None:
            return frame, []
            
        # Convert to grayscale for HOG detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect people using HOG with optimized parameters for real-time performance
        boxes, weights = self.hog.detectMultiScale(
            gray, 
            winStride=(8, 8), 
            padding=(8, 8), 
            scale=1.05,
            hitThreshold=0.0,  # Lower threshold for better detection
            finalThreshold=2.0,
            useMeanshiftGrouping=False
        )
        
        current_time = time.time()
        violations = []
        
        # Filter out low-confidence detections
        valid_boxes = []
        for i, (x, y, w, h) in enumerate(boxes):
            if weights[i] > 0.5:  # Confidence threshold
                valid_boxes.append((x, y, w, h))
        
        # Process each detected person
        for i, (x, y, w, h) in enumerate(valid_boxes):
            worker_id = f"worker_{camera_id}_{i}"
            
            # Extract person region for analysis
            person_roi = frame[y:y+h, x:x+w]
            
            # Analyze safety gear using color and shape analysis
            missing_gear = self._analyze_safety_gear(person_roi, frame, x, y, w, h)
            
            # Draw bounding box
            color = (0, 255, 0)  # Green for compliant
            
            if missing_gear:
                color = (0, 0, 255)  # Red for violation
                
                # Track violation time
                if worker_id not in self.violation_time[camera_id]:
                    self.violation_time[camera_id][worker_id] = current_time
                
                # Check if violation has persisted past threshold
                violation_duration = current_time - self.violation_time[camera_id][worker_id]
                if violation_duration >= self.alert_threshold:
                    # Capture screenshot for violation
                    screenshot_path = self._capture_violation_screenshot(frame, camera_id, worker_id, "safety_gear")
                    
                    violation_data = {
                        "worker_id": worker_id,
                        "missing_gear": missing_gear,
                        "duration": round(violation_duration, 1),
                        "screenshot": screenshot_path,
                        "timestamp": datetime.now().isoformat(),
                        "camera_id": camera_id
                    }
                    
                    violations.append(violation_data)
                    
                    # Store in violation history
                    self.violation_history.append(violation_data)
                    
                    # Add violation duration text
                    cv2.putText(frame, f"VIOLATION: {round(violation_duration, 1)}s", 
                                (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            else:
                # Reset violation time if compliant
                if worker_id in self.violation_time[camera_id]:
                    del self.violation_time[camera_id][worker_id]
            
            # Draw box and label
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            cv2.putText(frame, f"Worker {i+1}", (x, y + h + 20), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            
            # Draw missing equipment text
            if missing_gear:
                cv2.putText(frame, f"Missing: {', '.join(missing_gear)}", 
                            (x, y + h + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        
        return frame, violations
    
    def _analyze_safety_gear(self, person_roi, full_frame, x, y, w, h):
        """
        Analyze safety gear using computer vision techniques.
        This is a simplified implementation - in production, you'd use a trained model.
        """
        missing_gear = []
        
        if person_roi.size == 0:
            return missing_gear
            
        # Convert to different color spaces for analysis
        hsv = cv2.cvtColor(person_roi, cv2.COLOR_BGR2HSV)
        
        # Analyze head region for helmet (top 20% of person)
        head_region = person_roi[0:int(h*0.2), :]
        if head_region.size > 0:
            # Look for bright colors (typical of hard hats)
            bright_pixels = cv2.inRange(head_region, (200, 200, 200), (255, 255, 255))
            bright_ratio = np.sum(bright_pixels > 0) / (head_region.shape[0] * head_region.shape[1])
            
            if bright_ratio < 0.1:  # Low bright pixel ratio suggests no helmet
                missing_gear.append("helmet")
        
        # Analyze torso region for safety vest (middle 40% of person)
        torso_region = person_roi[int(h*0.3):int(h*0.7), :]
        if torso_region.size > 0:
            # Look for high-visibility colors (yellow, orange, lime green)
            yellow_range = cv2.inRange(torso_region, (0, 200, 200), (50, 255, 255))
            orange_range = cv2.inRange(torso_region, (0, 100, 200), (50, 200, 255))
            lime_range = cv2.inRange(torso_region, (0, 200, 0), (100, 255, 100))
            
            vest_pixels = np.sum(yellow_range > 0) + np.sum(orange_range > 0) + np.sum(lime_range > 0)
            vest_ratio = vest_pixels / (torso_region.shape[0] * torso_region.shape[1])
            
            if vest_ratio < 0.05:  # Low high-vis color ratio suggests no vest
                missing_gear.append("vest")
        
        return missing_gear
    
    def _capture_violation_screenshot(self, frame, camera_id, worker_id, violation_type):
        """Capture and save a screenshot of the violation"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{violation_type}_{camera_id}_{worker_id}_{timestamp}.jpg"
        filepath = os.path.join(self.screenshot_dir, violation_type, filename)
        
        try:
            cv2.imwrite(filepath, frame)
            return f"/static/violations/{violation_type}/{filename}"
        except Exception as e:
            print(f"Error saving violation screenshot: {e}")
            return None


class ProximityDetector:
    def __init__(self):
        """
        Initialize the proximity detector for workers and heavy machinery.
        """
        self.proximity_threshold = 80  # Distance threshold in pixels
        self.machinery_positions = {}  # Track machinery positions {camera_id: [(x, y, w, h), ...]}
        self.alert_history = defaultdict(dict)  # Track alerts {camera_id: {worker_id: last_alert_time}}
        self.alert_cooldown = 5  # Cooldown period between alerts (seconds)
        self.violation_history = []  # Store violation history
        self.screenshot_dir = "static/violations"
        self.setup_directories()
        
    def setup_directories(self):
        """Create necessary directories for storing violation data"""
        os.makedirs(self.screenshot_dir, exist_ok=True)
        os.makedirs(f"{self.screenshot_dir}/proximity", exist_ok=True)
        
    def detect(self, frame, camera_id):
        """
        Detect proximity between workers and machinery using real-time analysis.
        Returns the processed frame and a list of proximity alerts.
        """
        height, width = frame.shape[:2]
        alerts = []
        
        # Detect machinery using color and shape analysis
        machinery = self._detect_machinery(frame, camera_id)
        
        # Detect people using HOG detector
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        hog = cv2.HOGDescriptor()
        hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        boxes, weights = hog.detectMultiScale(gray, winStride=(8, 8), padding=(8, 8), scale=1.05)
        
        current_time = time.time()
        
        # Filter out low-confidence detections
        valid_boxes = []
        for i, (x, y, w, h) in enumerate(boxes):
            if weights[i] > 0.5:  # Confidence threshold
                valid_boxes.append((x, y, w, h))
        
        # Check proximity for each person against each machinery
        for i, (x, y, w, h) in enumerate(valid_boxes):
            worker_id = f"worker_{camera_id}_{i}"
            worker_center = (x + w//2, y + h//2)
            
            # Draw worker box
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, f"Worker {i+1}", (x, y - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # Check proximity to each machinery
            for j, (mx, my, mw, mh) in enumerate(machinery):
                machine_center = (mx + mw//2, my + mh//2)
                
                # Calculate Euclidean distance between centers
                distance = np.sqrt((worker_center[0] - machine_center[0])**2 + 
                                  (worker_center[1] - machine_center[1])**2)
                
                # Check if distance is below threshold
                if distance < self.proximity_threshold:
                    # Check cooldown
                    key = f"{worker_id}_machine_{j}"
                    last_alert = self.alert_history[camera_id].get(key, 0)
                    
                    if current_time - last_alert >= self.alert_cooldown:
                        # Draw proximity warning line
                        cv2.line(frame, worker_center, machine_center, (0, 0, 255), 3)
                        
                        # Add warning text
                        mid_point = ((worker_center[0] + machine_center[0])//2, 
                                     (worker_center[1] + machine_center[1])//2)
                        cv2.putText(frame, f"PROXIMITY ALERT!", mid_point, 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                        
                        # Capture screenshot for violation
                        screenshot_path = self._capture_violation_screenshot(frame, camera_id, worker_id, "proximity")
                        
                        # Create alert
                        alert_data = {
                            "worker_id": worker_id,
                            "machine_id": f"machine_{camera_id}_{j}",
                            "distance": round(distance, 2),
                            "screenshot": screenshot_path,
                            "timestamp": datetime.now().isoformat(),
                            "camera_id": camera_id
                        }
                        
                        alerts.append(alert_data)
                        
                        # Store in violation history
                        self.violation_history.append(alert_data)
                        
                        # Update alert history
                        self.alert_history[camera_id][key] = current_time
        
        return frame, alerts
    
    def _detect_machinery(self, frame, camera_id):
        """
        Detect machinery in the frame using computer vision techniques.
        This is a simplified implementation - in production, you'd use a trained model.
        """
        # Initialize machinery positions for this camera if not exists
        if camera_id not in self.machinery_positions:
            self.machinery_positions[camera_id] = []
        
        # Use color detection to find machinery (typically yellow/orange construction equipment)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Define color ranges for construction machinery
        yellow_lower = np.array([20, 100, 100])
        yellow_upper = np.array([30, 255, 255])
        orange_lower = np.array([10, 100, 100])
        orange_upper = np.array([20, 255, 255])
        
        # Create masks for machinery colors
        yellow_mask = cv2.inRange(hsv, yellow_lower, yellow_upper)
        orange_mask = cv2.inRange(hsv, orange_lower, orange_upper)
        machinery_mask = cv2.bitwise_or(yellow_mask, orange_mask)
        
        # Find contours
        contours, _ = cv2.findContours(machinery_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        machinery = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 2000:  # Minimum area threshold
                x, y, w, h = cv2.boundingRect(contour)
                # Filter by aspect ratio (machinery is typically wider than tall)
                aspect_ratio = w / h
                if 0.5 < aspect_ratio < 3.0:  # Reasonable aspect ratio for machinery
                    machinery.append((x, y, w, h))
                    
                    # Draw machinery box
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 165, 0), 2)
                    cv2.putText(frame, f"Machinery {len(machinery)}", (x, y - 10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 165, 0), 2)
        
        # Update machinery positions
        self.machinery_positions[camera_id] = machinery
        
        return machinery
    
    def _capture_violation_screenshot(self, frame, camera_id, worker_id, violation_type):
        """Capture and save a screenshot of the violation"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{violation_type}_{camera_id}_{worker_id}_{timestamp}.jpg"
        filepath = os.path.join(self.screenshot_dir, violation_type, filename)
        
        try:
            cv2.imwrite(filepath, frame)
            return f"/static/violations/{violation_type}/{filename}"
        except Exception as e:
            print(f"Error saving violation screenshot: {e}")
            return None 