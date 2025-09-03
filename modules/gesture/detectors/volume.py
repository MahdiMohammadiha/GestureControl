from time import time
from ..config import (
    DEFAULT_OPEN_DURATION,
    DEFAULT_VALIDITY_DURATION,
    VOLUME_PINCH_THRESHOLD,
    VOLUME_SCALE,
    VOLUME_MAX_X_MOVEMENT,
    VOLUME_MIN_DY,
)
from ..stateless import get_fingers_status as _get_fingers_status
from ..utils import palm_center


def detect_volume(
    tracker,
    open_duration: float = DEFAULT_OPEN_DURATION,
    validity_duration: float = DEFAULT_VALIDITY_DURATION,
    pinch_threshold: int = VOLUME_PINCH_THRESHOLD,
    volume_scale: float = VOLUME_SCALE,
    max_x_movement: int = VOLUME_MAX_X_MOVEMENT,
):
    """
    Detect volume control gesture:
    1. Require open palm confirmation (similar to detect_stop).
    2. Require index finger closed.
    3. Hand must NOT move too much horizontally (X-axis).
    4. If thumb tip (4) and index tip (8) pinch together -> enter volume mode.
    5. Vertical movement of palm center controls volume:
       - Move up (y decreases) => increase volume
       - Move down (y increases) => decrease volume
    Returns: ("VolumeUp", delta), ("VolumeDown", delta), or None
    where delta is proportional to movement.
    """
    now = time()

    # Check open palm confirmation
    was_open = tracker.was_open_recently(
        now=now, open_duration=open_duration, validity_duration=validity_duration
    )
    if not was_open or not tracker.landmarks:
        return None

    lm = tracker.landmarks[0]

    # The index finger must be closed.
    fs = _get_fingers_status(lm)  # [thumb, index, middle, ring, pinky]
    if not fs or fs[1]:  # If the index finger is open (True) => reject
        return None

    #  Limit movement on the X axis
    cx, cy = palm_center(lm)
    if not hasattr(tracker, "_volume_ref_x") or tracker._volume_ref_x is None:
        tracker._volume_ref_x = cx
    if abs(cx - tracker._volume_ref_x) > max_x_movement:
        return None  # If the hand moves too much in the horizontal direction => reject

    # Check pinch (thumb tip close to index tip)
    thumb_tip, index_tip = lm[4], lm[8]
    pinch_dist = (
        (thumb_tip[0] - index_tip[0]) ** 2 + (thumb_tip[1] - index_tip[1]) ** 2
    ) ** 0.5
    if pinch_dist > pinch_threshold:
        # Not pinched -> reset reference
        tracker._volume_ref_center = None
        return None

    # Measure palm center movement for Y-axis (volume control)
    if not hasattr(tracker, "_volume_ref_center") or tracker._volume_ref_center is None:
        tracker._volume_ref_center = (cx, cy)
        return None

    ref_x, ref_y = tracker._volume_ref_center
    dy = cy - ref_y  # +dy means moved down, -dy means moved up

    # update reference every frame to allow continuous control
    tracker._volume_ref_center = (cx, cy)

    # Map dy to volume change
    if abs(dy) < 5:  # ignore tiny jitter
        return None

    delta = abs(dy) * volume_scale
    if dy < 0:
        return ("VolumeUp", delta)
    else:
        return ("VolumeDown", delta)
