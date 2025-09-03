from time import time
from ..config import (
    DEFAULT_OPEN_DURATION,
    DEFAULT_VALIDITY_DURATION,
    RESERVE_COOLDOWN,
    RESERVE_HISTORY_LEN,
    RESERVE_MAJORITY_RATIO,
)
from ..stateless import get_fingers_status as _get_fingers_status


def detect_reserve(
    tracker,
    open_duration: float = DEFAULT_OPEN_DURATION,
    validity_duration: float = DEFAULT_VALIDITY_DURATION,
    cooldown: float = RESERVE_COOLDOWN,
    history_len: int = RESERVE_HISTORY_LEN,
    majority_ratio: float = RESERVE_MAJORITY_RATIO,
):
    """
    Detect reserved number gestures after open palm confirmation.
    Thumb must be closed (checked via line intersection).
    """
    now = time()

    # Check cooldown
    if (
        hasattr(tracker, "_reserve_cooldown_until")
        and now < tracker._reserve_cooldown_until
    ):
        return None

    # Require open palm confirmation
    was_open = tracker.was_open_recently(
        now=now, open_duration=open_duration, validity_duration=validity_duration
    )
    if not was_open or not tracker.landmarks:
        tracker._reserve_history = []
        return None

    lm = tracker.landmarks[0]
    fs = _get_fingers_status(lm)  # [thumb, index, middle, ring, pinky]
    if not fs:
        return None

    # Thumb closed check: line intersection
    def ccw(A, B, C):
        return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])

    def intersect(A, B, C, D):
        return ccw(A, C, D) != ccw(B, C, D) and ccw(A, B, C) != ccw(A, B, D)

    thumb_line = (lm[1], lm[4])  # base to tip
    index_line = (lm[0], lm[5])  # wrist to base of index

    if not intersect(*thumb_line, *index_line):
        return None  # اگر شصت جمع نشده، خروجی None

    fingers = fs[1:]  # ignore thumb
    candidate = None
    if fingers == [True, False, False, False]:
        candidate = "Reserve1"
    elif fingers == [True, True, False, False]:
        candidate = "Reserve2"
    elif fingers == [True, True, True, False]:
        candidate = "Reserve3"

    # Update history
    if not hasattr(tracker, "_reserve_history"):
        tracker._reserve_history = []
    tracker._reserve_history.append(candidate)
    if len(tracker._reserve_history) > history_len:
        tracker._reserve_history.pop(0)

    # Voting
    if candidate:
        count = tracker._reserve_history.count(candidate)
        ratio = count / len(tracker._reserve_history)
        if ratio >= majority_ratio:
            # Confirmed gesture
            tracker._reserve_cooldown_until = now + cooldown
            tracker._reserve_history = []
            return candidate

    return None
