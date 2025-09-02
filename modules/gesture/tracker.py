from typing import List, Optional
import cv2
import mediapipe as mp
from time import time
from .config import (
    DETECTION_AND_TRACING_CONFIDENCE,
    HISTORY_FRAME,
    CLEAR_DELAY,
    DEFAULT_OPEN_DURATION,
    DEFAULT_VALIDITY_DURATION,
)
from .stateless import (
    get_fingers_status as _get_fingers_status,
    is_open_palm as _is_open_palm,
    is_fist as _is_fist,
    detect_static_gesture as _detect_static_gesture,
)
from .utils import palm_center, play_sound_effect


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
        fist_confirm: float = 0.5,
        movement_threshold: int = 100,
    ):
        """
        Updated detect_stop that coordinates with was_open_recently().
        - Call this every frame after process().
        - open_duration, validity_duration are forwarded to was_open_recently.
        - movement_threshold resets the open-timer if the hand moves too much while open.
        - Returns "Pause" when open->fist gesture confirmed, otherwise None.
        """
        now = time()

        # print(f"Fist: {self.fist()}, ")

        # --- Movement tracking while open: if moved too much, restart the open timer ---
        if self.landmarks and self.open_palm():
            # get current center (if available)
            if self.hand_center_positions:
                cx, cy = self.hand_center_positions[-1]
                if self._open_reference_pos is None:
                    self._open_reference_pos = (cx, cy)
                else:
                    rx, ry = self._open_reference_pos
                    if (
                        abs(cx - rx) > movement_threshold
                        or abs(cy - ry) > movement_threshold
                    ):
                        # movement too large => restart was_open timer and update reference pos
                        # we directly reset the internal "tentative" open-start used by was_open_recently
                        self._wo_open_start = now
                        self._open_reference_pos = (cx, cy)
        else:
            # not currently open (or no landmarks) -> clear positional reference
            self._open_reference_pos = None

        # --- update/ask was_open_recently (this also updates internal _wo_* state) ---
        was_open = self.was_open_recently(
            now=now, open_duration=open_duration, validity_duration=validity_duration
        )

        # --- Fist handling: require was_open_recently True then a stable fist for fist_confirm seconds ---
        if self.fist():
            if was_open:
                if self._fist_start_time is None:
                    self._fist_start_time = now
                elif now - self._fist_start_time >= fist_confirm:
                    # Confirmed open-then-fist -> trigger Pause
                    # Reset related states so gesture won't immediately re-trigger
                    self._fist_start_time = None

                    # clear open-related states (both old and the was_open_recently internals)
                    self._open_start_time = None
                    self._open_reference_pos = None

                    self._wo_confirmed = False
                    self._wo_was_open_until = 0.0
                    self._wo_open_start = None

                    return "Pause"
            else:
                # Fist but no recent-open -> don't accumulate fist time
                # Only keep fist timer if was_open still valid; otherwise reset
                self._fist_start_time = None
        else:
            # Not fist: if was_open is expired/false, clear fist timer
            if not was_open:
                self._fist_start_time = None

        return None

    def detect_swipe(self):
        """
        Detect horizontal swipe when hand is open.
        Returns: "Next", "Previous", or None
        """
        if len(self.hand_center_positions) < 3:
            return None

        if not self.open_palm():
            return None

        dx = self.hand_center_positions[-1][0] - self.hand_center_positions[0][0]
        dy = self.hand_center_positions[-1][1] - self.hand_center_positions[0][1]

        if abs(dx) > 110 and abs(dy) <= 20:
            self.hand_center_positions.clear()
            return "Next" if dx > 0 else "Previous"
        return None

    def detect_volume(
        self,
        open_duration: float = DEFAULT_OPEN_DURATION,
        validity_duration: float = DEFAULT_VALIDITY_DURATION,
        pinch_threshold: int = 40,
        volume_scale: float = 0.05,
    ):
        """
        Detect volume control gesture:
        1. Require open palm confirmation (similar to detect_stop).
        2. If thumb tip (4) and index tip (8) pinch together -> enter volume mode.
        3. Vertical movement of palm center controls volume:
           - Move up (y decreases) => increase volume
           - Move down (y increases) => decrease volume
        Returns: ("VolumeUp", delta), ("VolumeDown", delta), or None
        where delta is proportional to movement.
        """
        now = time()

        # Check open palm confirmation
        was_open = self.was_open_recently(
            now=now, open_duration=open_duration, validity_duration=validity_duration
        )
        if not was_open or not self.landmarks:
            return None

        lm = self.landmarks[0]

        # Check pinch (thumb tip close to index tip)
        thumb_tip, index_tip = lm[4], lm[8]
        pinch_dist = (
            (thumb_tip[0] - index_tip[0]) ** 2 + (thumb_tip[1] - index_tip[1]) ** 2
        ) ** 0.5
        if pinch_dist > pinch_threshold:
            # Not pinched -> reset reference
            self._volume_ref_center = None
            return None

        # Measure palm center movement
        cx, cy = palm_center(lm)
        if not hasattr(self, "_volume_ref_center") or self._volume_ref_center is None:
            self._volume_ref_center = (cx, cy)
            return None

        ref_x, ref_y = self._volume_ref_center
        dy = cy - ref_y  # +dy means moved down, -dy means moved up

        # update reference every frame to allow continuous control
        self._volume_ref_center = (cx, cy)

        # Map dy to volume change
        if abs(dy) < 5:  # ignore tiny jitter
            return None

        delta = abs(dy) * volume_scale
        if dy < 0:
            return ("VolumeUp", delta)
        else:
            return ("VolumeDown", delta)

    def detect_reserve(
        self,
        open_duration: float = DEFAULT_OPEN_DURATION,
        validity_duration: float = DEFAULT_VALIDITY_DURATION,
        cooldown: float = 2.0,
        history_len: int = 20,
        majority_ratio: float = 0.8,
    ):
        """
        Detect reserved number gestures after open palm confirmation.
        Thumb must be closed (checked via line intersection).
        """
        now = time()

        # --- Check cooldown ---
        if hasattr(self, "_reserve_cooldown_until") and now < self._reserve_cooldown_until:
            return None

        # --- Require open palm confirmation ---
        was_open = self.was_open_recently(
            now=now, open_duration=open_duration, validity_duration=validity_duration
        )
        if not was_open or not self.landmarks:
            self._reserve_history = []
            return None

        lm = self.landmarks[0]
        fs = _get_fingers_status(lm)  # [thumb, index, middle, ring, pinky]
        if not fs:
            return None

        # --- Thumb closed check: line intersection ---
        def ccw(A, B, C):
            return (C[1]-A[1]) * (B[0]-A[0]) > (B[1]-A[1]) * (C[0]-A[0])

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

        # --- Update history ---
        if not hasattr(self, "_reserve_history"):
            self._reserve_history = []
        self._reserve_history.append(candidate)
        if len(self._reserve_history) > history_len:
            self._reserve_history.pop(0)

        # --- Voting ---
        if candidate:
            count = self._reserve_history.count(candidate)
            ratio = count / len(self._reserve_history)
            if ratio >= majority_ratio:
                # Confirmed gesture
                self._reserve_cooldown_until = now + cooldown
                self._reserve_history = []
                return candidate

        return None


    def detect_like_dislike(
        self,
        open_duration: float = DEFAULT_OPEN_DURATION,
        validity_duration: float = DEFAULT_VALIDITY_DURATION,
        thumb_threshold: int = 10,
        history_len: int = 15,
        majority_ratio: float = 0.6,
        hold_time: float = 0.5,
        cooldown: float = 1.5,
    ):
        """
        Detect Like (thumb up) or Dislike (thumb down) gestures after open palm.
        - Uses last `history_len` frames for voting, confirms gesture if >= majority_ratio.
        - Requires holding the gesture for `hold_time` seconds.
        - After confirmation, a cooldown of `cooldown` seconds prevents repeated detection.

        Returns: "Like", "Dislike", or None.
        """
        from time import time

        def ccw(A, B, C):
            return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])

        def intersect(A, B, C, D):
            """Return True if line AB intersects line CD"""
            return ccw(A, C, D) != ccw(B, C, D) and ccw(A, B, C) != ccw(A, B, D)

        now = time()

        # Check cooldown
        if hasattr(self, "_like_cooldown_until") and now < self._like_cooldown_until:
            return None

        # Require open palm confirmation
        was_open = self.was_open_recently(
            now=now, open_duration=open_duration, validity_duration=validity_duration
        )
        if not was_open or not self.landmarks:
            self._like_history = []
            self._like_candidate = None
            self._like_start_time = None
            return None

        lm = self.landmarks[0]
        cx, cy = palm_center(lm)
        thumb_tip = lm[4]

        # Collect other fingertips (index, middle, ring, pinky)
        other_tips = [lm[i] for i in [8, 12, 16, 20]]

        # ====== شرط جدید: بررسی تقاطع ======
        thumb_line = (lm[1], lm[4])  # شصت
        index_wrist_line = (lm[0], lm[8])  # مچ ↔ نوک انگشت اشاره
        if intersect(*thumb_line, *index_wrist_line):
            return None  # اگر تقاطع داشت، هیچ ژستی تشخیص داده نشه

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
        if not hasattr(self, "_like_history"):
            self._like_history = []
        self._like_history.append(candidate)
        if len(self._like_history) > history_len:
            self._like_history.pop(0)

        # Voting
        if candidate:
            count = self._like_history.count(candidate)
            ratio = count / len(self._like_history)
            if ratio >= majority_ratio:
                # Check hold timer
                if self._like_candidate != candidate:
                    self._like_candidate = candidate
                    self._like_start_time = now
                    return None
                elif now - self._like_start_time >= hold_time:
                    # confirmed gesture
                    self._like_cooldown_until = now + cooldown
                    self._like_history = []
                    self._like_candidate = None
                    self._like_start_time = None
                    return candidate
        else:
            # reset if no candidate
            self._like_candidate = None
            self._like_start_time = None

        return None

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
