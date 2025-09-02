# Tuning constants for gesture detection

# General settings
DETECTION_AND_TRACING_CONFIDENCE = 0.8  # From 0.0 to 1.0
HISTORY_FRAME = 10
TRAJECTORY_FRAME = 20
CLEAR_DELAY = 0.7  # Seconds

# was_open_recently defaults
DEFAULT_OPEN_DURATION = 1.0
DEFAULT_VALIDITY_DURATION = 1.5

# Stop gesture
STOP_FIST_CONFIRM = 0.5         # Seconds to hold fist
STOP_MOVEMENT_THRESHOLD = 100   # Pixels

# Swipe gesture
SWIPE_X_THRESHOLD = 110
SWIPE_Y_TOLERANCE = 20

# Volume gesture
VOLUME_PINCH_THRESHOLD = 40
VOLUME_SCALE = 0.05
VOLUME_MAX_X_MOVEMENT = 40  # Maximum allowable movement on the X axis
VOLUME_MIN_DY = 5   # Ignore tiny jitter

# Reserve gesture
RESERVE_COOLDOWN = 2.0
RESERVE_HISTORY_LEN = 20
RESERVE_MAJORITY_RATIO = 0.8

# Like/Dislike gesture
LIKE_THUMB_THRESHOLD = 10
LIKE_HISTORY_LEN = 15
LIKE_MAJORITY_RATIO = 0.6
LIKE_HOLD_TIME = 0.5
LIKE_COOLDOWN = 1.5
