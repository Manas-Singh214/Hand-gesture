import os
from pathlib import Path

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.absolute()

# Ensure the data directory exists
DATA_DIR = PROJECT_ROOT / 'data'
os.makedirs(DATA_DIR, exist_ok=True)

# Database paths
GESTURES_DB_PATH = str(DATA_DIR / 'gestures.json')

# Camera settings - 16:9 aspect ratio
CAMERA_RESOLUTIONS = [
    (1920, 1080),  # Full HD
    (1600, 900),   # HD+
    (1366, 768),   # Common laptop resolution
    (1280, 720),   # HD
    (1024, 576),   # Widescreen SD
    (854, 480),    # FWVGA
    (640, 360)     # nHD
]
CAMERA_FPS = 30

# UI Color Scheme
UI_COLORS = {
    'background': '#2C3E50',      # Dark blue-gray
    'primary': '#3498DB',         # Bright blue
    'secondary': '#2ECC71',       # Green
    'accent': '#E74C3C',          # Red
    'text': '#ECF0F1',            # Light gray
    'highlight': '#F1C40F',       # Yellow
    'success': '#2ECC71',         # Green
    'warning': '#F39C12',         # Orange
    'error': '#E74C3C',           # Red
    'button_bg': '#3498DB',
    'button_fg': '#FFFFFF',
    'button_active': '#2980B9',
    'canvas_bg': '#1F2B38',
    'header_bg': '#1A252F',
    'footer_bg': '#1A252F',
}

# Gesture type identifiers
GESTURE_TYPES = {
    'palm': {
        'name': '🖐️ Palm',
        'color': (0, 255, 0),  # Green
        'min_landmark_dist': 0.1,  # Minimum distance between landmarks to be considered this gesture
        'max_landmark_dist': 0.5   # Maximum distance between landmarks
    },
    'fist': {
        'name': '✊ Fist',
        'color': (0, 0, 255),  # Red
        'min_landmark_dist': 0.02,
        'max_landmark_dist': 0.2
    },
    'point_up': {
        'name': '👆 Point Up',
        'color': (255, 255, 0),  # Yellow
        'min_landmark_dist': 0.05,
        'max_landmark_dist': 0.4
    },
    
}

# Hand tracking settings
MAX_NUM_HANDS = 2
HAND_DETECTION_CONFIDENCE = 0.5
HAND_TRACKING_CONFIDENCE = 0.5

# Text-to-speech settings
TTS_LANGUAGE = 'en'
TTS_SLOW = False

# Gesture recognition settings
GESTURE_RECOGNITION_THRESHOLD = 0.7
MIN_DETECTION_CONFIDENCE = 0.5
MIN_TRACKING_CONFIDENCE = 0.5

# Debug settings
DEBUG = True

def setup_directories():
    """Ensure all required directories exist."""
    os.makedirs(DATA_DIR, exist_ok=True)

# Run setup on import
setup_directories()
