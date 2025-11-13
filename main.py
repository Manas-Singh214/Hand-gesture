import tkinter as tk
import os
import sys
import time
import cv2
import numpy as np
from pathlib import Path

# Add the project root to the Python path
project_root = str(Path(__file__).parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.camera_operator import CameraOperator
from core.hand_tracker import HandTracker
from core.gesture_database import GestureDatabase
from core.text_to_speech import TextToSpeech
from ui.main_window import MainWindow
import config  # Import the config module directly


class SignToSpeechApp:
    def __init__(self, root):
        """Initialize the Sign-to-Speech application."""
        self.root = root
        
        # Initialize components
        self.camera = CameraOperator()
        self.hand_tracker = HandTracker()
        
        # Initialize gesture database with the path from config
        self.gesture_db = GestureDatabase(config.GESTURES_DB_PATH)
        print(f"Using gesture database at: {config.GESTURES_DB_PATH}")
        
        # Initialize text-to-speech
        self.tts = TextToSpeech()
        
        # Make sure the database is properly initialized
        if not os.path.exists(config.GESTURES_DB_PATH):
            print("Creating new gesture database...")
            # Save an empty database to ensure the file exists
            with open(config.GESTURES_DB_PATH, 'w') as f:
                json.dump({"version": 1, "gestures": {}}, f, indent=2)
        
        # Initialize UI
        self.ui = MainWindow(root)
        
        # Set up callbacks
        self._setup_callbacks()
        
        # State variables
        self.is_camera_running = False
        self.last_gesture_time = 0
        self.current_gesture = None
    
    def _setup_callbacks(self):
        """Set up UI callbacks."""
        self.ui.set_add_gesture_callback(self._on_add_gesture)
        self.ui.set_edit_gesture_callback(self._on_edit_gesture)
        self.ui.set_delete_gesture_callback(self._on_delete_gesture)
        self.ui.set_open_camera_callback(self._on_toggle_camera)
        
        # Set up window close handler
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _on_toggle_camera(self):
        """Toggle the camera on/off."""
        if self.is_camera_running:
            self._stop_camera()
        else:
            self._start_camera()
    
    def _start_camera(self):
        """Start the camera and begin processing frames."""
        if not self.is_camera_running:
            self.is_camera_running = True
            self.ui.set_status("Camera started. Show your hand gesture.")
            self._process_frame()
    
    def _stop_camera(self):
        """Stop the camera."""
        self.is_camera_running = False
        self.ui.set_status("Camera stopped. Click 'Open Camera' to start again.")
    
    def _process_frame(self):
        """Process a single frame from the camera."""
        if not self.is_camera_running:
            return
            
        try:
            # Get frame from camera
            frame = self.camera.get_frame()
            
            if frame is not None:
                # Make a copy of the frame for drawing
                frame_copy = frame.copy()
                
                # Process hand landmarks
                results = self.hand_tracker.process_frame(frame_copy)
                
                # Draw landmarks on frame if hands are detected
                if results and hasattr(results, 'multi_hand_landmarks') and results.multi_hand_landmarks:
                    # Process each detected hand
                    for hand_landmarks in results.multi_hand_landmarks:
                        # Get landmarks as a list for gesture recognition
                        landmarks = self.hand_tracker.get_landmarks_list(hand_landmarks)
                        
                        if landmarks and len(landmarks) > 0:
                            # Recognize the gesture based on hand shape
                            gesture_type = self.hand_tracker._recognize_gesture(landmarks)
                            
                            # Find the closest matching gesture in the database
                            matched_gesture = self.gesture_db.find_similar_gesture(
                                landmarks,
                                config.GESTURE_RECOGNITION_THRESHOLD
                            )
                            
                            # Use the recognized gesture type to get the display name and color
                            gesture_info = config.GESTURE_TYPES.get(gesture_type, {
                                'name': 'Unknown',
                                'color': (255, 255, 255)
                            })
                            
                            # Draw landmarks with gesture-specific color
                            self.hand_tracker.draw_landmarks(
                                frame_copy,
                                hand_landmarks,
                                gesture_type
                            )
                            
                            # If we found a matching gesture in the database, use its message
                            if matched_gesture:
                                self._handle_gesture_recognition(matched_gesture)
                                
                                # Display the recognized gesture and message
                                message = matched_gesture.get('message', '')
                                cv2.putText(frame_copy, 
                                          f"{gesture_info['name']}: {message}", 
                                          (10, 30), 
                                          cv2.FONT_HERSHEY_SIMPLEX, 
                                          0.8, 
                                          gesture_info['color'], 
                                          2)
                            else:
                                # Just show the recognized gesture type
                                cv2.putText(frame_copy, 
                                          gesture_info['name'], 
                                          (10, 30), 
                                          cv2.FONT_HERSHEY_SIMPLEX, 
                                          0.8, 
                                          gesture_info['color'], 
                                          2)
                else:
                    # No hands detected
                    cv2.putText(frame_copy, "No hands detected", (10, 30), 
                              cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                
                # Update the UI with the processed frame
                self.ui.update_video_frame(frame_copy)
            
            # Schedule next frame
            self.root.after(30, self._process_frame)
            
        except Exception as e:
            print(f"Error processing frame: {e}")
            import traceback
            traceback.print_exc()
            # Try to continue processing frames even if one fails
            self.root.after(30, self._process_frame)
    
    def _handle_gesture_recognition(self, gesture):
        """Handle a recognized gesture."""
        current_time = time.time()
        
        # Avoid processing the same gesture multiple times in quick succession
        if (self.current_gesture != gesture['id'] or 
            current_time - self.last_gesture_time > 5):  # 5 seconds cooldown
            
            self.current_gesture = gesture['id']
            self.last_gesture_time = current_time
            
            # Update UI and speak the message
            self.ui.set_recognized_text(gesture['message'])
            self.tts.speak(gesture['message'])
    
    def _on_add_gesture(self):
        """Handle adding a new gesture or updating an existing one."""
        if not self.is_camera_running:
            self.ui.show_error("Error", "Please start the camera first.")
            return
        
        # Show available default gestures to update
        default_gestures = {
            "Palm": "WAIT A MINUTE",
            "Fist": "I NEED HELP",
            "Point Up": "I HAVE A DOUBT"
        }
        
        # Ask user which gesture they want to record
        gesture_choice = self.ui.get_choice("Select Gesture", 
                                          "Select a gesture to record:",
                                          list(default_gestures.keys()) + ["Custom Gesture"])
        
        if not gesture_choice:
            return  # User cancelled
            
        if gesture_choice == "Custom Gesture":
            # For custom gestures, get name and message
            gesture_name = self.ui.get_text_input("Add Gesture", "Enter a name for this gesture:")
            if not gesture_name:
                return
                
            message = self.ui.get_text_input("Add Gesture", "Enter the message for this gesture:")
            if not message:
                return
        else:
            # For default gestures, use predefined names and messages
            gesture_name = gesture_choice
            message = default_gestures[gesture_choice]
        
        # Give user time to prepare
        self.ui.set_status(f"Preparing to record '{gesture_name}' in 3 seconds...")
        self.root.update()
        time.sleep(1)
        self.ui.set_status(f"Preparing to record '{gesture_name}' in 2 seconds...")
        self.root.update()
        time.sleep(1)
        self.ui.set_status(f"Preparing to record '{gesture_name}' in 1 second...")
        self.root.update()
        time.sleep(1)
        
        # Capture multiple frames and average the landmarks for better accuracy
        frames_to_capture = 10
        landmarks_list = []
        
        self.ui.set_status(f"Show the '{gesture_name}' gesture now... (Capturing {frames_to_capture} frames)")
        
        for i in range(frames_to_capture):
            frame = self.camera.get_frame()
            if frame is not None:
                results = self.hand_tracker.process_frame(frame)
                if results and results.multi_hand_landmarks:
                    landmarks = self.hand_tracker.get_landmarks_list(results.multi_hand_landmarks[0])
                    if landmarks:
                        landmarks_list.append(landmarks)
                
                # Show countdown
                self.ui.set_status(f"Capturing '{gesture_name}'... {i+1}/{frames_to_capture}")
                self.root.update()
            
            time.sleep(0.1)  # Small delay between captures
        
        if not landmarks_list:
            self.ui.show_error("Error", "No hand detected. Please try again.")
            return
        
        # Calculate average landmarks
        avg_landmarks = [sum(x) / len(x) for x in zip(*landmarks_list)]
        
        # Add to database with a unique ID based on the gesture name
        gesture_id = f"gesture_{gesture_name.lower().replace(' ', '_')}_{int(time.time())}"
        
        self.gesture_db.gestures[gesture_id] = {
            'name': gesture_name,
            'message': message,
            'landmarks': avg_landmarks,
            'created_at': int(time.time())
        }
        
        self.gesture_db.save_gestures()
        self.ui.show_info("Success", f"Gesture '{gesture_name}' added successfully!")
        self.ui.set_status("Ready. Show a gesture to the camera.")
    
    def _on_edit_gesture(self):
        """Handle editing an existing gesture's message."""
        gestures = self.gesture_db.get_all_gestures()
        if not gestures:
            self.ui.show_info("No Gestures", "No gestures found to edit.")
            return
        
        # In a real app, show a dialog to select and edit a gesture
        self.ui.show_info("Edit Gesture", "Gesture editing will be implemented in the full version.")
    
    def _on_delete_gesture(self):
        """Handle deleting a gesture."""
        gestures = self.gesture_db.get_all_gestures()
        if not gestures:
            self.ui.show_info("No Gestures", "No gestures found to delete.")
            return
        
        # In a real app, show a dialog to select and delete a gesture
        self.ui.show_info("Delete Gesture", "Gesture deletion will be implemented in the full version.")
    
    def _on_closing(self):
        """Clean up resources before closing the application."""
        self.is_camera_running = False
        self.camera.release()
        self.hand_tracker.release()
        self.tts.cleanup()
        self.root.destroy()


def main():
    """Main entry point for the application."""
    # Create the root window
    root = tk.Tk()
    
    # Create and run the application
    app = SignToSpeechApp(root)
    
    # Start the main event loop
    root.mainloop()

# In your main application class (e.g., SignToSpeechApp)
def _on_add_gesture(self):
    """Handle adding/recording a new gesture."""
    if not self.is_camera_running:
        self.ui.show_error("Error", "Please start the camera first.")
        return
    
    # Show gesture selection dialog
    default_gestures = {
        "Palm": "WAIT A MINUTE",
        "Fist": "I NEED HELP",
        "Point Up": "I HAVE A DOUBT"
    }
    
    # Let user select which gesture to record
    gesture_choice = self.ui.get_choice(
        "Select Gesture",
        "Choose a gesture to record:",
        list(default_gestures.keys()) + ["Custom Gesture"]
    )
    
    if not gesture_choice:
        return  # User cancelled
        
    if gesture_choice == "Custom Gesture":
        # For custom gestures, get name and message
        gesture_name = self.ui.get_text_input("Add Gesture", "Enter a name for this gesture:")
        if not gesture_name:
            return
            
        message = self.ui.get_text_input("Add Gesture", "Enter the message for this gesture:")
        if not message:
            return
    else:
        # For default gestures, use predefined names and messages
        gesture_name = gesture_choice
        message = default_gestures[gesture_choice]
    
    # Show countdown before recording
    self._show_countdown(gesture_name)
    
    # Record the gesture
    self._record_gesture(gesture_name, message)

def _show_countdown(self, gesture_name: str, count: int = 3):
    """Show a countdown before recording starts."""
    if count > 0:
        self.ui.set_status(f"Recording '{gesture_name}' in {count}...")
        self.root.after(1000, lambda: self._show_countdown(gesture_name, count - 1))
    else:
        self.ui.set_status(f"Recording '{gesture_name}'... Show your hand now!")

def _record_gesture(self, gesture_name: str, message: str, frames_to_capture: int = 30):
    """Record hand landmarks for a new gesture."""
    landmarks_list = []
    captured_frames = 0
    
    def capture_frame():
        nonlocal captured_frames, landmarks_list
        
        if captured_frames >= frames_to_capture:
            # Done capturing, process the landmarks
            if landmarks_list:
                # Average the landmarks for better accuracy
                avg_landmarks = np.mean(landmarks_list, axis=0).flatten().tolist()
                
                # Create a unique ID for the gesture
                gesture_id = f"{gesture_name.lower().replace(' ', '_')}_{int(time.time())}"
                
                # Save to database
                if self.gesture_db.add_gesture(gesture_id, gesture_name, avg_landmarks, message):
                    self.ui.show_info("Success", f"Gesture '{gesture_name}' recorded successfully!")
                    self.ui.update_gesture_list(self.gesture_db.get_all_gestures())
                else:
                    self.ui.show_error("Error", "Failed to save gesture.")
            else:
                self.ui.show_error("Error", "No hand detected. Please try again.")
            
            self.ui.set_status("Ready")
            return
        
        # Capture a frame
        frame = self.camera.get_frame()
        if frame is not None:
            results = self.hand_tracker.process_frame(frame)
            
            if results and results.multi_hand_landmarks:
                # Get landmarks for the first detected hand
                landmarks = self.hand_tracker.get_landmarks_list(results.multi_hand_landmarks[0])
                if landmarks:
                    landmarks_list.append(landmarks)
                    captured_frames += 1
                    self.ui.set_status(f"Recording '{gesture_name}'... {captured_frames}/{frames_to_capture}")
            
            # Draw landmarks on frame for feedback
            if results and results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    self.hand_tracker.draw_landmarks(frame, hand_landmarks)
            
            # Show the frame with landmarks
            self.ui.update_video_frame(frame)
        
        # Schedule next frame capture
        self.root.after(50, capture_frame)  # ~20 FPS
    
    # Start the capture process
    capture_frame()
    
if __name__ == "__main__":
    main()
