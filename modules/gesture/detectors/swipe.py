from time import time
from ..config import (
    SWIPE_X_THRESHOLD,
    SWIPE_Y_TOLERANCE,
    DEFAULT_OPEN_DURATION,
    DEFAULT_VALIDITY_DURATION,
)


def detect_swipe(
    tracker,
    swipe_x_threshold: int = SWIPE_X_THRESHOLD,
    swipe_y_tolerance: int = SWIPE_Y_TOLERANCE,
    open_duration: float = DEFAULT_OPEN_DURATION,
    validity_duration: float = DEFAULT_VALIDITY_DURATION,
):
    """
    Detect horizontal swipe when hand is open.
    Returns: "Next", "Previous", or None
    """
    now = time()

    # Require recent confirmed open-palm before allowing swipe detection
    was_open = tracker.was_open_recently(
        now=now, open_duration=open_duration, validity_duration=validity_duration
    )
    if not was_open:
        return None

    if len(tracker.hand_center_positions) < 3:
        return None

    if not tracker.open_palm():
        return None

    dx = tracker.hand_center_positions[-1][0] - tracker.hand_center_positions[0][0]
    dy = tracker.hand_center_positions[-1][1] - tracker.hand_center_positions[0][1]

    if abs(dx) > swipe_x_threshold and abs(dy) <= swipe_y_tolerance:
        tracker.hand_center_positions.clear()
        return "Next" if dx > 0 else "Previous"
    return None
