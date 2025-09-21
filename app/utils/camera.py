import cv2
import requests
import numpy as np
import threading
import time
import os
from dotenv import load_dotenv

load_dotenv()

class IPCamera:
    def __init__(self, url, name=None):
        self.url = url
        self.name = name or f"Camera-{id(self)}"
        self.cap = None
        self.last_frame = None
        self.last_accessed = time.time()
        self.lock = threading.Lock()
        self.is_running = False
        self.use_fallback = False
        self.fallback_frames = []
        self.fallback_index = 0
        self.fallback_last_time = 0
        self.connect()
        
    def connect(self):
        """Connect to the IP camera stream"""
        try:
            self.cap = cv2.VideoCapture(self.url)
            if not self.cap.isOpened():
                print(f"Could not open video stream from {self.url}")
                self._setup_fallback()
                return False
            self.is_running = True
            # Start a thread to continuously fetch frames
            threading.Thread(target=self._update_frame, daemon=True).start()
            return True
        except Exception as e:
            print(f"Error connecting to camera {self.name}: {str(e)}")
            self._setup_fallback()
            return False
            
    def _setup_fallback(self):
        """Set up a fallback video source when real camera is unavailable"""
        print(f"Setting up fallback video for {self.name}")
        self.use_fallback = True
        self.is_running = True
        
        # Generate a simple "Camera Offline" frame without fake detection elements
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        # Fill with dark gray
        frame[:] = (64, 64, 64)
        
        # Add camera name and status
        cv2.putText(frame, f"{self.name} - OFFLINE", (50, 200), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2)
        cv2.putText(frame, "Camera not connected", (50, 250), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 2)
        cv2.putText(frame, "Please check camera connection", (50, 300), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (150, 150, 150), 2)
        
        # Add a simple border
        cv2.rectangle(frame, (10, 10), (630, 470), (100, 100, 100), 2)
        
        self.fallback_frames = [frame]
        
        # Start a thread to cycle through frames
        threading.Thread(target=self._update_fallback_frame, daemon=True).start()
    
    def _update_fallback_frame(self):
        """Update the fallback frame periodically"""
        while self.use_fallback and self.is_running:
            current_time = time.time()
            # Update frame every 0.5 seconds
            if current_time - self.fallback_last_time > 0.5:
                with self.lock:
                    self.fallback_index = (self.fallback_index + 1) % len(self.fallback_frames)
                    self.last_frame = self.fallback_frames[self.fallback_index].copy()
                    self.last_accessed = current_time
                    self.fallback_last_time = current_time
            time.sleep(0.1)
            
    def _update_frame(self):
        """Continuously update the frame from the camera"""
        while self.is_running and not self.use_fallback:
            try:
                with self.lock:
                    ret, frame = self.cap.read()
                    if ret:
                        self.last_frame = frame
                        self.last_accessed = time.time()
                    else:
                        # Try to reconnect
                        print(f"Lost connection to {self.name}, attempting to reconnect...")
                        self.cap.release()
                        time.sleep(1)  # Wait before reconnecting
                        self.cap = cv2.VideoCapture(self.url)
                        if not self.cap.isOpened():
                            print(f"Reconnection failed for {self.name}, switching to fallback mode")
                            self._setup_fallback()
                            break
            except Exception as e:
                print(f"Error updating frame from {self.name}: {str(e)}")
                time.sleep(0.5)  # Brief pause before retrying
                
    def get_frame(self):
        """Get the most recent frame"""
        with self.lock:
            if self.last_frame is None:
                # If no frame available, return a blank frame with error message
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(frame, f"{self.name} - No Frame Available", (50, 50), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                return frame
            return self.last_frame.copy()
            
    def release(self):
        """Release the camera resources"""
        self.is_running = False
        if self.cap:
            self.cap.release()


class CameraManager:
    def __init__(self):
        self.cameras = {}
        self._load_cameras_from_env()
        
    def _load_cameras_from_env(self):
        """Load camera URLs from environment variables or configuration"""
        # Default test cameras if none are configured
        default_cameras = {
            0: "0",  # Default webcam if available
            1: "1",  # Second webcam if available
            2: "sample_video.mp4",  # Sample video file if available
            3: "rtsp://example.com/live/stream"  # Sample RTSP stream
        }
        
        # Try loading from environment variables
        for i in range(4):
            camera_url = os.getenv(f"CAMERA_{i}_URL", default_cameras.get(i))
            if camera_url:
                self.add_camera(i, camera_url)
                
    def add_camera(self, camera_id, url, name=None):
        """Add a new camera to the manager"""
        try:
            camera = IPCamera(url, name or f"Camera-{camera_id}")
            self.cameras[camera_id] = camera
            return True
        except Exception as e:
            print(f"Error adding camera {camera_id}: {str(e)}")
            return False
            
    def get_camera(self, camera_id):
        """Get a camera by ID"""
        return self.cameras.get(camera_id)
        
    def get_all_cameras(self):
        """Get all cameras"""
        return self.cameras
        
    def remove_camera(self, camera_id):
        """Remove a camera from the manager"""
        if camera_id in self.cameras:
            self.cameras[camera_id].release()
            del self.cameras[camera_id]
            return True
        return False 