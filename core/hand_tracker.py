import cv2
import mediapipe as mp
import numpy as np
import config
from typing import Dict, List, Tuple, Optional, Any

class HandTracker:
    def __init__(self):
        """Initialize the hand tracker with MediaPipe Hands."""
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=config.MAX_NUM_HANDS,
            min_detection_confidence=config.HAND_DETECTION_CONFIDENCE,
            min_tracking_confidence=config.HAND_TRACKING_CONFIDENCE
        )
        self.mp_draw = mp.solutions.drawing_utils
        
        # Store the last recognized gestures to smooth out detection
        self.last_gestures = []
        self.gesture_history = []
        self.history_length = 5  # Number of frames to consider for smoothing
    
    def process_frame(self, frame):
        """Process a frame and return hand landmarks."""
        if frame is None:
            return None
            
        try:
            # Convert the BGR image to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process the frame and get hand landmarks
            results = self.hands.process(rgb_frame)
            
            # Ensure we have valid hand landmarks
            if not hasattr(results, 'multi_hand_landmarks') or not results.multi_hand_landmarks:
                return None
                
            return results
            
        except Exception as e:
            print(f"Error in process_frame: {e}")
            return None
    
    def draw_landmarks(self, frame, hand_landmarks, recognized_gesture: str = None):
        """Draw hand landmarks and recognized gesture on the frame."""
        if hand_landmarks is None:
            return frame
            
        try:
            # Get the color for the recognized gesture
            gesture_color = (255, 255, 255)  # Default white
            gesture_name = ""
            
            if recognized_gesture and recognized_gesture in config.GESTURE_TYPES:
                gesture_color = config.GESTURE_TYPES[recognized_gesture]['color']
                gesture_name = config.GESTURE_TYPES[recognized_gesture]['name']
            
            # Draw landmarks and connections
            if hasattr(hand_landmarks, 'landmark'):
                # Single hand
                self.mp_draw.draw_landmarks(
                    frame,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS,
                    landmark_drawing_spec=mp.solutions.drawing_utils.DrawingSpec(
                        color=gesture_color,
                        thickness=2,
                        circle_radius=2
                    ),
                    connection_drawing_spec=mp.solutions.drawing_utils.DrawingSpec(
                        color=gesture_color,
                        thickness=2
                    )
                )
                
                # Add gesture name text
                if gesture_name and hasattr(hand_landmarks, 'landmark') and hand_landmarks.landmark:
                    # Get wrist position for text placement
                    wrist = hand_landmarks.landmark[0]
                    h, w, _ = frame.shape
                    text_x = int(wrist.x * w) - 50
                    text_y = int(wrist.y * h) - 20
                    
                    # Draw text with background for better visibility
                    (text_w, text_h), _ = cv2.getTextSize(gesture_name, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
                    cv2.rectangle(frame, (text_x, text_y - 25), (text_x + text_w, text_y + 5), (0, 0, 0), -1)
                    cv2.putText(frame, gesture_name, (text_x, text_y),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            elif hasattr(hand_landmarks, '__iter__'):
                # Multiple hands
                for landmarks in hand_landmarks:
                    if hasattr(landmarks, 'landmark'):
                        self.mp_draw.draw_landmarks(
                            frame,
                            landmarks,
                            self.mp_hands.HAND_CONNECTIONS,
                            landmark_drawing_spec=mp.solutions.drawing_utils.DrawingSpec(
                                color=gesture_color,
                                thickness=2,
                                circle_radius=2
                            ),
                            connection_drawing_spec=mp.solutions.drawing_utils.DrawingSpec(
                                color=gesture_color,
                                thickness=2
                            )
                        )
        except Exception as e:
            print(f"Error drawing landmarks: {e}")
            
        return frame
    
    def _get_average_landmark_distance(self, landmarks):
        """Calculate the average distance between all pairs of landmarks."""
        if not landmarks or len(landmarks) < 2:
            return 0.0
            
        distances = []
        # Convert to numpy array for easier calculations
        landmarks_np = np.array(landmarks).reshape(-1, 3)
        
        # Calculate pairwise distances between all landmarks
        for i in range(len(landmarks_np)):
            for j in range(i + 1, len(landmarks_np)):
                dist = np.linalg.norm(landmarks_np[i] - landmarks_np[j])
                distances.append(dist)
                
        return np.mean(distances) if distances else 0.0
        
    def _recognize_gesture(self, landmarks) -> str:
        """Recognize the gesture based on landmark distances."""
        if not landmarks or len(landmarks) < 21 * 3:  # 21 landmarks * 3 coordinates each
            return "unknown"
            
        try:
            # Reshape landmarks to 21x3 array (21 landmarks with x,y,z coordinates)
            landmarks_np = np.array(landmarks).reshape(-1, 3)
            
            # Calculate hand span (distance between wrist and middle finger tip)
            wrist = landmarks_np[0]  # Wrist is the first landmark
            middle_tip = landmarks_np[12]  # Middle finger tip
            hand_span = np.linalg.norm(wrist - middle_tip)
            
            # Calculate average distance between landmarks
            avg_dist = self._get_average_landmark_distance(landmarks)
            
            # Normalize the average distance by hand span
            normalized_dist = avg_dist / hand_span if hand_span > 0 else 0
            
            # Match against known gesture types
            best_match = "unknown"
            min_diff = float('inf')
            
            for gesture_type, params in config.GESTURE_TYPES.items():
                # Check if the normalized distance is within the expected range
                if params['min_landmark_dist'] <= normalized_dist <= params['max_landmark_dist']:
                    # Calculate how close we are to the middle of the range
                    mid_range = (params['min_landmark_dist'] + params['max_landmark_dist']) / 2
                    diff = abs(normalized_dist - mid_range)
                    
                    if diff < min_diff:
                        min_diff = diff
                        best_match = gesture_type
            
            # Update gesture history for smoothing
            self.gesture_history.append(best_match)
            if len(self.gesture_history) > self.history_length:
                self.gesture_history.pop(0)
                
            # Return the most common gesture in history for stability
            if self.gesture_history:
                from collections import Counter
                return Counter(self.gesture_history).most_common(1)[0][0]
                
            return best_match
            
        except Exception as e:
            print(f"Error in _recognize_gesture: {e}")
            return "unknown"
    
    def get_landmarks_list(self, hand_landmarks):
        """Convert hand landmarks to a flat list of coordinates."""
        if not hand_landmarks:
            return None
            
        landmarks_list = []
        try:
            # Access the landmark property of the hand_landmarks object
            for landmark in hand_landmarks.landmark:
                landmarks_list.extend([landmark.x, landmark.y, landmark.z])
            return landmarks_list
        except AttributeError as e:
            print(f"Error processing landmarks: {e}")
            print(f"Landmarks object type: {type(hand_landmarks)}")
            print(f"Available attributes: {dir(hand_landmarks) if hasattr(hand_landmarks, '__dir__') else 'N/A'}")
            return None
    
    def release(self):
        """Release resources."""
        try:
            if hasattr(self, 'hands') and self.hands is not None:
                self.hands.close()
        except Exception as e:
            # Ignore errors during cleanup
            pass
        finally:
            self.hands = None
    
    def __del__(self):
        try:
            self.release()
        except Exception:
            # Ignore any errors during garbage collection
            pass
