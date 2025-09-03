from typing import List, Optional
import cv2
import mediapipe as mp
from time import time
from .config import (
    DETECTION_AND_TRACING_CONFIDENCE,
    HISTORY_FRAME,
    TRAJECTORY_FRAME,
    CLEAR_DELAY,
    DEFAULT_OPEN_DURATION,
    DEFAULT_VALIDITY_DURATION,
    STOP_FIST_CONFIRM,
    STOP_MOVEMENT_THRESHOLD,
    SWIPE_X_THRESHOLD,
    SWIPE_Y_TOLERANCE,
    VOLUME_PINCH_THRESHOLD,
    VOLUME_SCALE,
    VOLUME_MAX_X_MOVEMENT,
    VOLUME_MIN_DY,
    RESERVE_COOLDOWN,
    RESERVE_HISTORY_LEN,
    RESERVE_MAJORITY_RATIO,
    LIKE_THUMB_THRESHOLD,
    LIKE_HISTORY_LEN,
    LIKE_MAJORITY_RATIO,
    LIKE_HOLD_TIME,
    LIKE_COOLDOWN,
)

from .stateless import (
    get_fingers_status as _get_fingers_status,
    is_open_palm as _is_open_palm,
    is_fist as _is_fist,
    detect_static_gesture as _detect_static_gesture,
)
from .utils import palm_center, play_sound_effect

# Import refactored detector implementations
from .detectors.stop import detect_stop as _detect_stop
from .detectors.swipe import detect_swipe as _detect_swipe
from .detectors.volume import detect_volume as _detect_volume
from .detectors.reserve import detect_reserve as _detect_reserve
from .detectors.like_dislike import detect_like_dislike as _detect_like_dislike


class HandTracker:
    """
    Hand tracking and gesture recognition using MediaPipe.
    This is a stateful class: call process(frame) every frame, then call the
    detectors like detect_stop(), detect_swipe(), detect_gesture(), etc.
    """

    def __init__(
        self,
        max_num_hands: int = 1,
        detection_confidence: float = DETECTION_AND_TRACING_CONFIDENCE,
        tracking_confidence: float = DETECTION_AND_TRACING_CONFIDENCE,
    ):
        # MediaPipe Hands setup
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            max_num_hands=max_num_hands,
            min_detection_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence,
        )
        self.mp_draw = mp.solutions.drawing_utils

        # State
        self._history_len = HISTORY_FRAME
        self.landmarks: List[List[tuple[int, int]]] = []  # Detected landmarks of hands
        self.hand_center_positions: List[tuple[int, int]] = []  # Hand centers history
        self.trajectory: List[float] = []  # Angle trajectory for rotation detection
        self._last_seen_time = time()  # The time the hand was last seen
        self._hand_state_history: List[str] = []  # History of open/fisted hands

        self._open_start_time: Optional[float] = None
        self._fist_start_time: Optional[float] = None
        self._open_reference_pos: Optional[tuple[int, int]] = None

        self._wo_open_start: Optional[float] = (
            None  # when continuous "open" started (for confirmation)
        )
        self._wo_confirmed: bool = (
            False  # True after we've confirmed open for open_duration
        )
        self._wo_was_open_until: float = (
            0.0  # timestamp until which was_open_recently returns True
        )

    # -------------------------
    # Processing
    # -------------------------
    def process(self, frame):
        """
        Detect hands in a frame, draw landmarks, and update state.

        WRIST   0
        THUMB   1-4
        INDEX   5-8
        MIDDLE  9-12
        RING    13-16
        PINKY   17-20
        """
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb)
        self.landmarks = []

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Draw landmarks
                self.mp_draw.draw_landmarks(
                    frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS
                )

                # Convert normalized coords to pixels
                lm_list = self._extract_landmarks(frame, hand_landmarks)
                self.landmarks.append(lm_list)

                # Save hand center position
                self._update_hand_position(lm_list)

            # Hand seen -> Update the time
            self._last_seen_time = time()

        else:
            if time() - self._last_seen_time > CLEAR_DELAY:
                self.hand_center_positions.clear()

        return frame

    # -------------------------
    # Helpers
    # -------------------------
    def _extract_landmarks(self, frame, hand_landmarks):
        """Convert normalized landmark coordinates to pixel values."""
        h, w, _ = frame.shape
        return [(int(lm.x * w), int(lm.y * h)) for lm in hand_landmarks.landmark]

    def _update_hand_position(self, landmarks):
        """Compute center of palm and update history."""
        center_x, center_y = palm_center(landmarks)
        self.hand_center_positions.append((center_x, center_y))
        if len(self.hand_center_positions) > self._history_len:
            self.hand_center_positions.pop(0)

    def open_palm(self):
        """Stateful wrapper: True if current frame looks like open palm."""
        if not self.landmarks:
            return False
        return _is_open_palm(self.landmarks[0])

    def fist(self):
        """Stateful wrapper: True if current frame looks like a fist."""
        if not self.landmarks:
            return False
        return _is_fist(self.landmarks[0])

    def was_open_recently(
        self,
        now=None,
        open_duration: float = DEFAULT_OPEN_DURATION,
        validity_duration: float = DEFAULT_VALIDITY_DURATION,
    ):
        """
        Frame-driven check for recent open-palm:
        - Must be called each frame (after self.landmarks and open_palm() reflect the current frame).
        - If the hand is continuously open for `open_duration` seconds -> confirm open.
        - After confirmation, returns True until `validity_duration` seconds have passed.
        - If no hand is present and confirmation expired -> returns False.
        - This method is self-contained (uses its own internal variables).
        """
        if now is None:
            now = time()

        # If already confirmed and still within validity window => keep True
        if self._wo_confirmed and now <= self._wo_was_open_until:
            return True

        # If confirmation expired, clear confirmation state
        if self._wo_confirmed and now > self._wo_was_open_until:
            self._wo_confirmed = False
            self._wo_open_start = None
            self._wo_was_open_until = 0.0

        # If there's no detected hand right now, we cannot progress toward confirmation.
        # Also clear tentative open-start timer.
        if not self.landmarks:
            self._wo_open_start = None
            return False

        # If current frame shows an open palm, advance/open the open-start timer.
        if self.open_palm():
            # start the continuous-open timer if not started yet
            if self._wo_open_start is None:
                self._wo_open_start = now
                return False

            # if we've been open for long enough, confirm and set validity window
            if now - self._wo_open_start >= open_duration:
                self._wo_confirmed = True
                self._wo_was_open_until = now + validity_duration
                # reset start so we don't re-trigger repeatedly
                self._wo_open_start = None
                play_sound_effect("alert.mp3")
                return True

            # still accumulating open time, not yet confirmed
            return False

        # current frame is not open -> reset tentative timer
        self._wo_open_start = None
        return False

    # -------------------------
    # Gesture Detection
    # -------------------------
    def detect_stop(
        self,
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
        return _detect_stop(
            self,
            open_duration=open_duration,
            validity_duration=validity_duration,
            fist_confirm=fist_confirm,
            movement_threshold=movement_threshold,
        )

    def detect_swipe(
        self,
        open_duration: float = DEFAULT_OPEN_DURATION,
        validity_duration: float = DEFAULT_VALIDITY_DURATION,
        swipe_x_threshold: int = SWIPE_X_THRESHOLD,
        swipe_y_tolerance: int = SWIPE_Y_TOLERANCE,
    ):
        """
        Detect horizontal swipe when hand is open.
        Returns: "Next", "Previous", or None
        """
        return _detect_swipe(
            self,
            open_duration=open_duration,
            validity_duration=validity_duration,
            swipe_x_threshold=swipe_x_threshold,
            swipe_y_tolerance=swipe_y_tolerance,
        )

    def detect_volume(
        self,
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
        return _detect_volume(
            self,
            open_duration=open_duration,
            validity_duration=validity_duration,
            pinch_threshold=pinch_threshold,
            volume_scale=volume_scale,
            max_x_movement=max_x_movement,
        )

    def detect_reserve(
        self,
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
        return _detect_reserve(
            self,
            open_duration=open_duration,
            validity_duration=validity_duration,
            cooldown=cooldown,
            history_len=history_len,
            majority_ratio=majority_ratio,
        )

    def detect_like_dislike(
        self,
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
        return _detect_like_dislike(
            self,
            open_duration=open_duration,
            validity_duration=validity_duration,
            thumb_threshold=thumb_threshold,
            history_len=history_len,
            majority_ratio=majority_ratio,
            hold_time=hold_time,
            cooldown=cooldown,
        )

    def detect_gesture(self):
        """
        Unified gesture detector:
        Priority order:
        1. Stop (open -> fist)
        2. Reserve numbers (Reserve1/2/3)
        3. Like/Dislike
        4. Swipe (Next/Previous)
        5. Volume (VolumeUp/VolumeDown)

        Returns: gesture string or ("VolumeUp/Down", delta) or None
        """
        # 1. Stop
        result = self.detect_stop()
        if result:
            return result

        # 2. Reserve
        result = self.detect_reserve()
        if result:
            return result

        # 3. Like/Dislike
        result = self.detect_like_dislike()
        if result:
            return result

        # 4. Swipe
        result = self.detect_swipe()
        if result:
            return result

        # 5. Volume
        result = self.detect_volume()
        if result:
            return result

        return None
