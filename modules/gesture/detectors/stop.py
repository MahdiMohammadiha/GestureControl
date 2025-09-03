from time import time
from ..config import (
    DEFAULT_OPEN_DURATION,
    DEFAULT_VALIDITY_DURATION,
    STOP_FIST_CONFIRM,
    STOP_MOVEMENT_THRESHOLD,
)


def detect_stop(
    tracker,
    open_duration: float = DEFAULT_OPEN_DURATION,
    validity_duration: float = DEFAULT_VALIDITY_DURATION,
    fist_confirm: float = STOP_FIST_CONFIRM,
    movement_threshold: int = STOP_MOVEMENT_THRESHOLD,
):
    """
    Updated detect_stop that coordinates with was_open_recently().
    - Call this every frame after process().
    - open_duration, validity_duration are forwarded to was_open_recently.
    - movement_threshold resets the open-timer if the hand moves too much while open.
    - Returns "Pause" when open->fist gesture confirmed, otherwise None.
    """
    now = time()

    # Movement tracking while open: if moved too much, restart the open timer
    if tracker.landmarks and tracker.open_palm():
        # get current center (if available)
        if tracker.hand_center_positions:
            cx, cy = tracker.hand_center_positions[-1]
            if tracker._open_reference_pos is None:
                tracker._open_reference_pos = (cx, cy)
            else:
                rx, ry = tracker._open_reference_pos
                if (
                    abs(cx - rx) > movement_threshold
                    or abs(cy - ry) > movement_threshold
                ):
                    # movement too large => restart was_open timer and update reference pos
                    # we directly reset the internal "tentative" open-start used by was_open_recently
                    tracker._wo_open_start = now
                    tracker._open_reference_pos = (cx, cy)
    else:
        # not currently open (or no landmarks) -> clear positional reference
        tracker._open_reference_pos = None

    # update/ask was_open_recently (this also updates internal _wo_* state)
    was_open = tracker.was_open_recently(
        now=now, open_duration=open_duration, validity_duration=validity_duration
    )

    # Fist handling: require was_open_recently True then a stable fist for fist_confirm seconds
    if tracker.fist():
        if was_open:
            if tracker._fist_start_time is None:
                tracker._fist_start_time = now
            elif now - tracker._fist_start_time >= fist_confirm:
                # Confirmed open-then-fist -> trigger Pause
                # Reset related states so gesture won't immediately re-trigger
                tracker._fist_start_time = None

                # clear open-related states (both old and the was_open_recently internals)
                tracker._open_start_time = None
                tracker._open_reference_pos = None

                tracker._wo_confirmed = False
                tracker._wo_was_open_until = 0.0
                tracker._wo_open_start = None

                return "Pause"
        else:
            # Fist but no recent-open -> don't accumulate fist time
            # Only keep fist timer if was_open still valid; otherwise reset
            tracker._fist_start_time = None
    else:
        # Not fist: if was_open is expired/false, clear fist timer
        if not was_open:
            tracker._fist_start_time = None

    return None
