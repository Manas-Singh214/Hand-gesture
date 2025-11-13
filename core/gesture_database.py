import json
import os
import time
from typing import Dict, Any, Optional
from pathlib import Path
import numpy as np

class GestureDatabase:
    def __init__(self, db_path: str = None):
        """Initialize the gesture database.
        
        Args:
            db_path: Optional path to the database file. If not provided, uses 'gestures.json' in the 'data' directory
                    next to this file.
        """
        if db_path is None:
            # Use absolute path to ensure the file is always in the same location
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.db_path = os.path.join(base_dir, '..', 'data', 'gestures.json')
        else:
            self.db_path = os.path.abspath(db_path)
            
        # Ensure the directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
        self.gestures: Dict[str, Dict[str, Any]] = {}
        self._ensure_db_exists()
        self.load_gestures()
        print(f"Using gesture database at: {self.db_path}")  # Debug output
    
    def _get_default_gestures(self) -> Dict[str, Dict[str, Any]]:
        """Return default gestures with proper landmarks to initialize the database."""
        # Palm gesture landmarks (open hand)
        palm_landmarks = [
            0.5, 0.5, 0.0,  # Wrist
            0.6, 0.4, 0.0,   # Thumb CMC
            0.7, 0.3, 0.0,   # Thumb MCP
            0.8, 0.3, 0.0,   # Thumb IP
            0.9, 0.3, 0.0,   # Thumb tip
            0.5, 0.4, 0.0,   # Index MCP
            0.5, 0.3, 0.0,   # Index PIP
            0.5, 0.2, 0.0,   # Index DIP
            0.5, 0.1, 0.0,   # Index tip
            0.4, 0.4, 0.0,   # Middle MCP
            0.4, 0.3, 0.0,   # Middle PIP
            0.4, 0.2, 0.0,   # Middle DIP
            0.4, 0.1, 0.0,   # Middle tip
            0.3, 0.4, 0.0,   # Ring MCP
            0.3, 0.3, 0.0,   # Ring PIP
            0.3, 0.2, 0.0,   # Ring DIP
            0.3, 0.1, 0.0,   # Ring tip
            0.2, 0.5, 0.0,   # Pinky MCP
            0.2, 0.4, 0.0,   # Pinky PIP
            0.2, 0.3, 0.0,   # Pinky DIP
            0.2, 0.2, 0.0    # Pinky tip
        ]
        
        # Fist gesture landmarks (closed hand)
        fist_landmarks = [
            0.5, 0.5, 0.0,   # Wrist
            0.6, 0.4, 0.0,   # Thumb CMC
            0.7, 0.3, 0.0,   # Thumb MCP
            0.8, 0.3, 0.0,   # Thumb IP
            0.9, 0.3, 0.0,   # Thumb tip
            0.5, 0.4, 0.0,   # Index MCP
            0.5, 0.5, 0.0,   # Index PIP (folded)
            0.5, 0.6, 0.0,   # Index DIP (folded)
            0.5, 0.7, 0.0,   # Index tip (folded)
            0.4, 0.4, 0.0,   # Middle MCP
            0.4, 0.5, 0.0,   # Middle PIP (folded)
            0.4, 0.6, 0.0,   # Middle DIP (folded)
            0.4, 0.7, 0.0,   # Middle tip (folded)
            0.3, 0.4, 0.0,   # Ring MCP
            0.3, 0.5, 0.0,   # Ring PIP (folded)
            0.3, 0.6, 0.0,   # Ring DIP (folded)
            0.3, 0.7, 0.0,   # Ring tip (folded)
            0.2, 0.5, 0.0,   # Pinky MCP
            0.2, 0.5, 0.0,   # Pinky PIP (folded)
            0.2, 0.6, 0.0,   # Pinky DIP (folded)
            0.2, 0.7, 0.0    # Pinky tip (folded)
        ]
        
        # Point up gesture landmarks (index finger extended, others folded)
        point_up_landmarks = [
            0.5, 0.5, 0.0,   # Wrist
            0.6, 0.4, 0.0,   # Thumb CMC
            0.7, 0.3, 0.0,   # Thumb MCP
            0.8, 0.3, 0.0,   # Thumb IP
            0.9, 0.3, 0.0,   # Thumb tip
            0.5, 0.2, 0.0,   # Index MCP
            0.5, 0.1, 0.0,   # Index PIP
            0.5, 0.0, 0.0,   # Index DIP
            0.5, -0.1, 0.0,  # Index tip
            0.4, 0.4, 0.0,   # Middle MCP
            0.4, 0.5, 0.0,   # Middle PIP (folded)
            0.4, 0.6, 0.0,   # Middle DIP (folded)
            0.4, 0.7, 0.0,   # Middle tip (folded)
            0.3, 0.4, 0.0,   # Ring MCP
            0.3, 0.5, 0.0,   # Ring PIP (folded)
            0.3, 0.6, 0.0,   # Ring DIP (folded)
            0.3, 0.7, 0.0,   # Ring tip (folded)
            0.2, 0.5, 0.0,   # Pinky MCP
            0.2, 0.5, 0.0,   # Pinky PIP (folded)
            0.2, 0.6, 0.0,   # Pinky DIP (folded)
            0.2, 0.7, 0.0    # Pinky tip (folded)
        ]
        
        # Middle finger gesture (middle finger extended, others folded)
        middle_finger_landmarks = [
            0.5, 0.5, 0.0,   # Wrist
            0.6, 0.4, 0.0,   # Thumb CMC
            0.7, 0.3, 0.0,   # Thumb MCP
            0.8, 0.3, 0.0,   # Thumb IP
            0.9, 0.3, 0.0,   # Thumb tip
            0.5, 0.4, 0.0,   # Index MCP
            0.5, 0.5, 0.0,   # Index PIP (folded)
            0.5, 0.6, 0.0,   # Index DIP (folded)
            0.5, 0.7, 0.0,   # Index tip (folded)
            0.4, 0.2, 0.0,   # Middle MCP
            0.4, 0.1, 0.0,   # Middle PIP
            0.4, 0.0, 0.0,   # Middle DIP
            0.4, -0.1, 0.0,  # Middle tip
            0.3, 0.4, 0.0,   # Ring MCP
            0.3, 0.5, 0.0,   # Ring PIP (folded)
            0.3, 0.6, 0.0,   # Ring DIP (folded)
            0.3, 0.7, 0.0,   # Ring tip (folded)
            0.2, 0.5, 0.0,   # Pinky MCP
            0.2, 0.5, 0.0,   # Pinky PIP (folded)
            0.2, 0.6, 0.0,   # Pinky DIP (folded)
            0.2, 0.7, 0.0    # Pinky tip (folded)
        ]
        
        # Thumbs up gesture (thumb up, others folded)
        thumbs_up_landmarks = [
            0.5, 0.5, 0.0,   # Wrist
            0.6, 0.4, 0.0,   # Thumb CMC
            0.7, 0.3, 0.0,   # Thumb MCP
            0.8, 0.2, 0.0,   # Thumb IP
            0.9, 0.1, 0.0,   # Thumb tip
            0.5, 0.4, 0.0,   # Index MCP
            0.5, 0.5, 0.0,   # Index PIP (folded)
            0.5, 0.6, 0.0,   # Index DIP (folded)
            0.5, 0.7, 0.0,   # Index tip (folded)
            0.4, 0.4, 0.0,   # Middle MCP
            0.4, 0.5, 0.0,   # Middle PIP (folded)
            0.4, 0.6, 0.0,   # Middle DIP (folded)
            0.4, 0.7, 0.0,   # Middle tip (folded)
            0.3, 0.4, 0.0,   # Ring MCP
            0.3, 0.5, 0.0,   # Ring PIP (folded)
            0.3, 0.6, 0.0,   # Ring DIP (folded)
            0.3, 0.7, 0.0,   # Ring tip (folded)
            0.2, 0.5, 0.0,   # Pinky MCP
            0.2, 0.5, 0.0,   # Pinky PIP (folded)
            0.2, 0.6, 0.0,   # Pinky DIP (folded)
            0.2, 0.7, 0.0    # Pinky tip (folded)
        ]
        
        # Use fixed timestamps for default gestures
        timestamp = 0  # Use 0 as the timestamp for all default gestures
        
        return {
            "fist_default": {
                "name": "✊ Fist",
                "landmarks": fist_landmarks,
                "message": "I NEED HELP",
                "created_at": timestamp,
                "is_default": True
            },
            "point_up_default": {
                "name": "👆 Point Up",
                "landmarks": point_up_landmarks,
                "message": "I HAVE A DOUBT",
                "created_at": timestamp,
                "is_default": True
            },
            "palm_default": {
                "name": "🖐️ Palm",
                "landmarks": palm_landmarks,
                "message": "WAIT A MINUTE",
                "created_at": timestamp,
                "is_default": True
            },
            
        }

    def _ensure_db_exists(self):
        """Ensure the database file exists with default gestures if empty or corrupted."""
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Default gestures to use if database is empty or corrupted
        default_gestures = self._get_default_gestures()
        
        # If file doesn't exist, create it with default gestures
        if not os.path.exists(self.db_path):
            print("Creating new gesture database with default gestures")
            self.gestures = default_gestures
            self._save_gestures({
                "version": 1,
                "gestures": self.gestures
            })
            return
            
        # Try to load existing database
        try:
            with open(self.db_path, 'r') as f:
                data = json.load(f)
                
            # Handle different database formats
            if isinstance(data, dict):
                if 'gestures' in data and isinstance(data['gestures'], dict):
                    # New format with version and gestures
                    self.gestures = data['gestures']
                else:
                    # Old format where the entire file is the gestures dict
                    self.gestures = data
            else:
                raise ValueError("Invalid database format")
                
            # Remove any gestures with empty or invalid landmarks
            valid_gestures = {}
            has_invalid = False
            for gesture_id, gesture in self.gestures.items():
                # Skip default gestures to avoid duplicates
                if gesture.get('is_default'):
                    continue
                    
                # Ensure each gesture has all required fields
                if not all(key in gesture for key in ['name', 'landmarks', 'message', 'created_at']):
                    print(f"Warning: Gesture {gesture_id} is missing required fields, skipping")
                    has_invalid = True
                    continue
                    
                if not isinstance(gesture['landmarks'], list) or len(gesture['landmarks']) == 0:
                    print(f"Warning: Gesture {gesture_id} has invalid landmarks, skipping")
                    has_invalid = True
                    continue
                    
                valid_gestures[gesture_id] = gesture
            
            # Add back default gestures if they're missing
            default_gesture_names = {g['name'].lower() for g in default_gestures.values()}
            existing_gesture_names = {g['name'].lower() for g in valid_gestures.values()}
            
            # Only add default gestures if they're not already present (by name)
            for default_id, default_gesture in default_gestures.items():
                if default_gesture['name'].lower() not in existing_gesture_names:
                    valid_gestures[default_id] = default_gesture
            
            # If we found any invalid gestures, update the database
            if has_invalid or len(valid_gestures) != len(self.gestures):
                print("Updating gesture database with valid gestures...")
                self.gestures = valid_gestures
                if not self._save_gestures({
                    "version": 1,
                    "gestures": self.gestures
                }):
                    print("Error: Failed to save gestures to database")
            else:
                self.gestures = valid_gestures
                
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error loading gestures from {self.db_path}: {e}")
            print("Initializing with default gestures")
            self.gestures = default_gestures
            self._save_gestures({"version": 1, "gestures": self.gestures})
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            print(f"Error loading gesture database: {e}. Resetting to defaults.")
            self.gestures = default_gestures
            self._save_gestures({
                "version": 1,
                "gestures": self.gestures
            })

    def _save_gestures(self, data: Dict[str, Any]) -> bool:
        """Save gestures to the database file."""
        try:
            with open(self.db_path, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving gestures: {e}")
            return False

    def load_gestures(self) -> None:
        """Load gestures from the database file."""
        try:
            with open(self.db_path, 'r') as f:
                data = json.load(f)
                self.gestures = data.get('gestures', {})
        except (FileNotFoundError, json.JSONDecodeError):
            self.gestures = self._get_default_gestures()
            self._save_gestures({"version": 1, "gestures": self.gestures})

    def add_gesture(self, gesture_id: str, name: str, landmarks: list, message: str) -> bool:
        """Add or update a gesture in the database."""
        self.gestures[gesture_id] = {
            "name": name,
            "landmarks": landmarks,
            "message": message,
            "created_at": int(time.time())
        }
        return self._save_gestures({"version": 1, "gestures": self.gestures})

    def delete_gesture(self, gesture_id: str) -> bool:
        """Delete a gesture from the database."""
        if gesture_id in self.gestures:
            del self.gestures[gesture_id]
            return self._save_gestures({"version": 1, "gestures": self.gestures})
        return False

    def get_gesture(self, gesture_id: str) -> Optional[Dict[str, Any]]:
        """Get a gesture by its ID."""
        return self.gestures.get(gesture_id)

    def get_all_gestures(self) -> Dict[str, Dict[str, Any]]:
        """Get all gestures."""
        return self.gestures

    def _normalize_landmarks(self, landmarks):
        """Normalize landmarks to be invariant to scale and translation."""
        landmarks = np.array(landmarks).reshape(-1, 3)
        
        # Center the landmarks around the wrist (first point)
        wrist = landmarks[0].copy()
        centered = landmarks - wrist
        
        # Scale based on the distance between wrist and middle finger MCP (base of middle finger)
        scale = np.linalg.norm(centered[9])  # Index 9 is MCP of middle finger
        if scale > 0:
            centered = centered / scale
            
        return centered.flatten()
        
    def find_similar_gesture(self, landmarks: list, threshold: float = 0.6) -> Optional[Dict[str, Any]]:
        """
        Find a gesture similar to the given landmarks.
        Returns the most similar gesture if similarity is above threshold, else None.
        
        Args:
            landmarks: List of landmark coordinates [x1,y1,z1, x2,y2,z2, ...]
            threshold: Minimum similarity score (0-1) to consider a match
            
        Returns:
            Dictionary containing gesture data if a match is found, None otherwise
        """
        if not landmarks or not self.gestures:
            return None

        try:
            # Normalize input landmarks
            norm_landmarks = self._normalize_landmarks(landmarks)
        except Exception as e:
            print(f"Error normalizing landmarks: {e}")
            return None

        best_match = None
        best_score = -1
        best_gesture_id = None

        for gesture_id, gesture in self.gestures.items():
            if not gesture.get('landmarks') or len(gesture['landmarks']) == 0:
                continue

            try:
                # Normalize stored gesture landmarks
                stored_norm = self._normalize_landmarks(gesture['landmarks'])
                
                # Calculate distances between corresponding landmarks
                diff = norm_landmarks - stored_norm
                distances = np.linalg.norm(diff.reshape(-1, 3), axis=1)
                
                # Use mean of top 80% of distances to be robust to outliers
                k = max(1, int(len(distances) * 0.8))
                topk_distances = np.partition(distances, k-1)[:k]
                avg_distance = np.mean(topk_distances)
                
                # Convert distance to similarity score (lower distance = higher score)
                similarity = 1.0 / (1.0 + avg_distance)
                
                if similarity > best_score:
                    best_score = similarity
                    best_match = gesture.copy()
                    best_gesture_id = gesture_id
                    # Include the gesture ID in the returned dictionary
                    best_match['id'] = gesture_id
                    
            except Exception as e:
                print(f"Error comparing with gesture {gesture_id}: {e}")
                continue

        print(f"Best match score: {best_score:.3f} for gesture: {best_gesture_id}")
        return best_match if best_score >= threshold else None

    def _save_gestures(self, data: Dict[str, Any]) -> bool:
        """Save gestures to the database file."""
        try:
            # Create a temporary file first to ensure atomic write
            temp_path = self.db_path + '.tmp'
            
            # Save with pretty printing for better readability
            with open(temp_path, 'w') as f:
                json.dump(data, f, indent=2)
                
            # On Windows, we need to remove the destination file first if it exists
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
                
            # Rename the temp file to the actual file
            os.rename(temp_path, self.db_path)
            
            print(f"Successfully saved {len(data.get('gestures', {}))} gestures to {self.db_path}")
            return True
            
        except Exception as e:
            print(f"Error saving gestures to {self.db_path}: {e}")
            # Clean up temp file if it exists
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
            return False

    def load_gestures(self) -> None:
        """Load gestures from the database file."""
        try:
            if not os.path.exists(self.db_path):
                # If file doesn't exist, initialize with default gestures
                self.gestures = self._get_default_gestures()
                self._save_gestures({"version": 1, "gestures": self.gestures})
                return
                
            with open(self.db_path, 'r') as f:
                data = json.load(f)
                
            # Handle different database formats
            if isinstance(data, dict):
                if 'gestures' in data and isinstance(data['gestures'], dict):
                    self.gestures = data['gestures']
                else:
                    # Old format where the entire file is the gestures dict
                    self.gestures = data
            else:
                raise ValueError("Invalid database format - expected a dictionary")
                
        except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
            print(f"Error loading gestures from {self.db_path}: {e}")
            print("Initializing with default gestures")
            self.gestures = self._get_default_gestures()
            self._save_gestures({"version": 1, "gestures": self.gestures})

    def add_gesture(self, gesture_id: str, name: str, landmarks: list, message: str) -> bool:
        """Add or update a gesture in the database."""
        if not landmarks or len(landmarks) == 0:
            print("Error: Cannot add gesture with empty landmarks")
            return False
            
        self.gestures[gesture_id] = {
            "name": name,
            "landmarks": landmarks,
            "message": message,
            "created_at": int(time.time())
        }
        
        # Save the updated gestures to the database file
        return self._save_gestures({
            "version": 1,
            "gestures": self.gestures
        })

    def delete_gesture(self, gesture_id: str) -> bool:
        """Delete a gesture from the database."""
        if gesture_id in self.gestures:
            del self.gestures[gesture_id]
            return self._save_gestures({
                "version": 1,
                "gestures": self.gestures
            })
        return False

    def get_gesture(self, gesture_id: str) -> Optional[Dict[str, Any]]:
        """Get a gesture by its ID."""
        return self.gestures.get(gesture_id)

    def get_all_gestures(self) -> Dict[str, Dict[str, Any]]:
        """Get all gestures."""
        return self.gestures

    def _normalize_landmarks(self, landmarks):
        """Normalize landmarks to be invariant to scale and translation."""
        landmarks = np.array(landmarks).reshape(-1, 3)
    
        # Center the landmarks around the wrist (first point)
        wrist = landmarks[0].copy()
        centered = landmarks - wrist
        
        # Scale based on the distance between wrist and middle finger MCP (base of middle finger)
        scale = np.linalg.norm(centered[9])  # Index 9 is MCP of middle finger
        if scale > 0:
            centered = centered / scale
            
        return centered.flatten()
        
    def find_similar_gesture(self, landmarks: list, threshold: float = 0.6) -> Optional[Dict[str, Any]]:
        """
        Find a gesture similar to the given landmarks.
        Returns the most similar gesture if similarity is above threshold, else None.
        
        Args:
            landmarks: List of landmark coordinates [x1,y1,z1, x2,y2,z2, ...]
            threshold: Minimum similarity score (0-1) to consider a match
            
        Returns:
            Dictionary containing gesture data if a match is found, None otherwise
        """
        if not landmarks or not self.gestures:
            return None

        try:
            # Normalize input landmarks
            norm_landmarks = self._normalize_landmarks(landmarks)
        except Exception as e:
            print(f"Error normalizing landmarks: {e}")
            return None

        best_match = None
        best_score = -1
        best_gesture_id = None

        for gesture_id, gesture in self.gestures.items():
            if not gesture.get('landmarks') or len(gesture['landmarks']) == 0:
                continue

            try:
                # Normalize stored gesture landmarks
                stored_norm = self._normalize_landmarks(gesture['landmarks'])
                
                # Calculate distances between corresponding landmarks
                diff = norm_landmarks - stored_norm
                distances = np.linalg.norm(diff.reshape(-1, 3), axis=1)
                
                # Use mean of top 80% of distances to be robust to outliers
                k = max(1, int(len(distances) * 0.8))
                topk_distances = np.partition(distances, k-1)[:k]
                avg_distance = np.mean(topk_distances)
                
                # Convert distance to similarity score (lower distance = higher score)
                similarity = 1.0 / (1.0 + avg_distance)
                
                if similarity > best_score:
                    best_score = similarity
                    best_match = gesture.copy()
                    best_gesture_id = gesture_id
                    # Include the gesture ID in the returned dictionary
                    best_match['id'] = gesture_id
                        
            except Exception as e:
                print(f"Error comparing with gesture {gesture_id}: {e}")
                continue

        print(f"Best match score: {best_score:.3f} for gesture: {best_gesture_id}")
        return best_match if best_score >= threshold else None