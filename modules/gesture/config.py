# Tuning constants for gesture detection

DETECTION_AND_TRACING_CONFIDENCE = 0.8  # From 0.0 to 1.0
HISTORY_FRAME = 10
TRAJECTORY_FRAME = 20
CLEAR_DELAY = 0.7  # Seconds

# was_open_recently defaults
DEFAULT_OPEN_DURATION = 1.0
DEFAULT_VALIDITY_DURATION = 1.5

# fist detection thresholds
FIST_DISTANCE_RATIO = 0.6  # fingertip-to-wrist < ratio * palm_size => folded
FIST_REQUIRED_FOLDED = 3   # number of non-thumb fingers required folded