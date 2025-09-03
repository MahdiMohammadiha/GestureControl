from time import time
from ..config import (
    DEFAULT_OPEN_DURATION,
    DEFAULT_VALIDITY_DURATION,
    LIKE_THUMB_THRESHOLD,
    LIKE_HISTORY_LEN,
    LIKE_MAJORITY_RATIO,
    LIKE_HOLD_TIME,
    LIKE_COOLDOWN,
)
from ..utils import palm_center


def detect_like_dislike(
    tracker,
    open_duration: float = DEFAULT_OPEN_DURATION,
    validity_duration: float = DEFAULT_VALIDITY_DURATION,
    thumb_threshold: int = LIKE_THUMB_THRESHOLD,
    history_len: int = LIKE_HISTORY_LEN,
    majority_ratio: float = LIKE_MAJORITY_RATIO,
    hold_time: float = LIKE_HOLD_TIME,
    cooldown: float = LIKE_COOLDOWN,
):
    """
    Detect Like (thumb up) or Dislike (thumb down) gestures after open palm.
    - Uses last `history_len` frames for voting, confirms gesture if >= majority_ratio.
    - Requires holding the gesture for `hold_time` seconds.
    - After confirmation, a cooldown of `cooldown` seconds prevents repeated detection.

    Returns: "Like", "Dislike", or None.
    """

    def ccw(A, B, C):
        return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])

    def intersect(A, B, C, D):
        """Return True if line AB intersects line CD"""
        return ccw(A, C, D) != ccw(B, C, D) and ccw(A, B, C) != ccw(A, B, D)

    now = time()

    # Check cooldown
    if hasattr(tracker, "_like_cooldown_until") and now < tracker._like_cooldown_until:
        return None

    # Require open palm confirmation
    was_open = tracker.was_open_recently(
        now=now, open_duration=open_duration, validity_duration=validity_duration
    )
    if not was_open or not tracker.landmarks:
        tracker._like_history = []
        tracker._like_candidate = None
        tracker._like_start_time = None
        return None

    lm = tracker.landmarks[0]
    cx, cy = palm_center(lm)
    thumb_tip = lm[4]

    # Collect other fingertips (index, middle, ring, pinky)
    other_tips = [lm[i] for i in [8, 12, 16, 20]]

    # Intersection check
    thumb_line = (lm[1], lm[4])  # شصت
    index_wrist_line = (lm[0], lm[8])  # Wrist ↔ index fingertip
    if intersect(*thumb_line, *index_wrist_line):
        return None  # If there is an intersection, no gesture will be recognized.

    # Determine candidate gesture
    candidate = None

    # Like: thumb up, all others below thumb
    if thumb_tip[1] < cy - thumb_threshold and all(
        tip[1] > thumb_tip[1] for tip in other_tips
    ):
        candidate = "Like"
    # Dislike: thumb down, all others above thumb
    elif thumb_tip[1] > cy + thumb_threshold and all(
        tip[1] < thumb_tip[1] for tip in other_tips
    ):
        candidate = "Dislike"

    # Update history
    if not hasattr(tracker, "_like_history"):
        tracker._like_history = []
    tracker._like_history.append(candidate)
    if len(tracker._like_history) > history_len:
        tracker._like_history.pop(0)

    # Voting
    if candidate:
        count = tracker._like_history.count(candidate)
        ratio = count / len(tracker._like_history)
        if ratio >= majority_ratio:
            # Check hold timer
            if tracker._like_candidate != candidate:
                tracker._like_candidate = candidate
                tracker._like_start_time = now
                return None
            elif now - tracker._like_start_time >= hold_time:
                # confirmed gesture
                tracker._like_cooldown_until = now + cooldown
                tracker._like_history = []
                tracker._like_candidate = None
                tracker._like_start_time = None
                return candidate
    else:
        # reset if no candidate
        tracker._like_candidate = None
        tracker._like_start_time = None

    return None
