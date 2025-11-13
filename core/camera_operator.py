import cv2
import threading
import time
from queue import Queue
import config  # Import the config module directly
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CameraOperator:
    def __init__(self):
        self.cap = None
        self.frame_queue = Queue(maxsize=1)  # Store only the latest frame
        self.running = False
        self.thread = None
        self.camera_initialized = threading.Event()
        
        # Initialize camera in the main thread
        self._init_camera()
    
    def _init_camera(self) -> bool:
        """Initialize the camera with the specified settings."""
        try:
            # Try to open the camera with DirectShow first (Windows)
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Use DirectShow for Windows
            
            if not self.cap.isOpened():
                # Try opening without DirectShow if that fails
                self.cap = cv2.VideoCapture(0)
                
            if not self.cap.isOpened():
                logger.error("Could not open camera. Please check if it's connected and not in use by another application.")
                return False
            
            # Try each resolution in order until we find one that works
            success = False
            for width, height in config.CAMERA_RESOLUTIONS:
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                
                # Get the actual resolution that was set
                actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                
                # If we got the resolution we asked for, use it
                if actual_width == width and actual_height == height:
                    logger.info(f"Successfully set camera resolution to: {actual_width}x{actual_height}")
                    success = True
                    break
            
            if not success:
                # If no resolution worked, use whatever the camera defaulted to
                actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                logger.warning(f"Could not set requested resolution. Using default: {actual_width}x{actual_height}")
            
            # Set FPS if supported
            self.cap.set(cv2.CAP_PROP_FPS, config.CAMERA_FPS)
            actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
            logger.info(f"Camera FPS set to: {actual_fps}")
            
            # Store the actual resolution for later use
            self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Start the frame grabbing thread
            self.running = True
            self.thread = threading.Thread(target=self._update_frame, daemon=True)
            self.thread.start()
            
            # Wait for the first frame to be captured
            start_time = time.time()
            while not self.camera_initialized.is_set() and (time.time() - start_time) < 5:
                time.sleep(0.1)
                
            if not self.camera_initialized.is_set():
                logger.error("Timed out waiting for camera to initialize")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error initializing camera: {e}")
            import traceback
            logger.error(traceback.format_exc())
            if hasattr(self, 'cap'):
                self.cap.release()
            return False
    
    def _update_frame(self):
        """Continuously grab frames from the camera."""
        consecutive_errors = 0
        max_errors = 5
        
        while self.running:
            try:
                ret, frame = self.cap.read()
                if not ret:
                    consecutive_errors += 1
                    logger.warning(f"Failed to grab frame (attempt {consecutive_errors}/{max_errors})")
                    
                    if consecutive_errors >= max_errors:
                        logger.error("Max consecutive errors reached. Attempting to reinitialize camera...")
                        if not self._init_camera():
                            logger.error("Failed to reinitialize camera")
                            break
                        consecutive_errors = 0
                        continue
                    
                    time.sleep(0.1)
                    continue
                
                # Reset error counter on successful frame capture
                consecutive_errors = 0
                
                # Mirror the frame
                frame = cv2.flip(frame, 1)
                
                # Replace the frame in the queue (discard old frames)
                while not self.frame_queue.empty():
                    try:
                        self.frame_queue.get_nowait()
                    except:
                        break
                        
                self.frame_queue.put(frame)
                
                # Signal that we've successfully captured at least one frame
                if not self.camera_initialized.is_set():
                    self.camera_initialized.set()
                
            except Exception as e:
                logger.error(f"Error in frame update: {e}")
                time.sleep(0.1)
    
    def get_frame(self):
        """Get the latest frame from the camera."""
        try:
            if not self.frame_queue.empty():
                return self.frame_queue.get()
            return None
        except Exception as e:
            logger.error(f"Error getting frame: {e}")
            return None
    
    def release(self):
        """Release the camera resources."""
        self.running = False
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
        
        if hasattr(self, 'cap') and self.cap is not None:
            try:
                if self.cap.isOpened():
                    self.cap.release()
            except:
                pass
            self.cap = None
            
        self.camera_initialized.clear()
    
    def is_opened(self):
        """Check if the camera is open and available."""
        return self.cap is not None and self.cap.isOpened() and self.camera_initialized.is_set()
    
    def __del__(self):
        self.release()
