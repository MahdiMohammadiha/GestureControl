from typing import List
from .utils import dist, palm_center
from .config import FIST_DISTANCE_RATIO, FIST_REQUIRED_FOLDED


Point = tuple[int, int]


def get_fingers_status(landmarks: List[Point]) -> List[bool]:
    """
    Returns [thumb, index, middle, ring, pinky] boolean list.
    True = finger up, False = finger down.
    """
    if not landmarks:
        return []

    lm = landmarks
    fingers = [
        lm[4][0] > lm[3][0],  # Thumb: tip x > ip x (heuristic)
        lm[8][1] < lm[6][1],  # Index: tip y < pip y (higher on image = smaller y)
        lm[12][1] < lm[10][1],  # Middle
        lm[16][1] < lm[14][1],  # Ring
        lm[20][1] < lm[18][1],  # Pinky
    ]
    return fingers


def is_open_palm(landmarks: List[Point]) -> bool:
    """
    Return True if the hand looks open (most fingers up).

    Conditions:
      - All 21 landmarks must be detected.
      - Index, middle, ring, and pinky fingers should be up (4 fingers).
    """
    if not landmarks or len(landmarks) != 21:
        return False

    fs = get_fingers_status(landmarks)
    if not fs:
        return False

    # require index..pinky up (at least 4 fingers up)
    return sum(fs[1:]) >= 4



def is_fist(landmarks: List[Point]) -> bool:
    """
    Return True if the hand is a fist.

    A fist is detected if:
    1. All non-thumb fingers (index, middle, ring, pinky) are folded down.
    2. The line between thumb points (1 -> 4) intersects with the line
       between wrist (0) and index fingertip (8). This ensures the thumb
       is closed across the palm.

    Args:
        landmarks (List[Point]): List of 21 hand landmark points as (x, y) tuples.

    Returns:
        bool: True if the hand is a fist, False otherwise.
    """
    if not landmarks:
        return False

    lm = landmarks

    # finger MCP,PIP,DIP,TIP indices for index, middle, ring, pinky
    fingers_idx = [
        (5, 6, 7, 8),  # index
        (9, 10, 11, 12),  # middle
        (13, 14, 15, 16),  # ring
        (17, 18, 19, 20),  # pinky
    ]

    try:
        # --- Step 1: check folded fingers ---
        for mcp, pip, dip, tip in fingers_idx:
            if not lm[tip][1] > lm[pip][1]:
                return False

        # --- Step 2: check thumb crossing palm ---
        def ccw(A, B, C):
            return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])

        def intersect(A, B, C, D):
            return ccw(A, C, D) != ccw(B, C, D) and ccw(A, B, C) != ccw(A, B, D)

        thumb_line = (lm[1], lm[4])  # thumb base (1) -> thumb tip (4)
        palm_line = (lm[0], lm[8])   # wrist -> index fingertip

        if not intersect(*thumb_line, *palm_line):
            return False

        return True
    except IndexError:
        return False


def detect_static_gesture(landmarks: List[Point]) -> str:
    """
    Recognize static gestures (Next, Previous, Play, Pause) using landmarks.
    Returns a string: "Next", "Previous", "Play", "Pause", "Unknown" or "No hand".
    """
    if not landmarks:
        return "No hand"

    lm = landmarks
    thumb_tip, index_tip, middle_tip, ring_tip, pinky_tip = (
        lm[4],
        lm[8],
        lm[12],
        lm[16],
        lm[20],
    )

    # Next
    if thumb_tip[0] > index_tip[0] + 40 and all(
        lm[tip][1] > lm[base][1] for tip, base in [(8, 6), (12, 10), (16, 14), (20, 18)]
    ):
        return "Next"

    # Previous
    if thumb_tip[0] < pinky_tip[0] - 40 and all(
        lm[tip][1] > lm[base][1] for tip, base in [(8, 6), (12, 10), (16, 14), (20, 18)]
    ):
        return "Previous"

    # Play
    if (
        lm[8][1] < lm[6][1]
        and lm[12][1] < lm[10][1]
        and lm[16][1] > lm[14][1]
        and lm[20][1] > lm[18][1]
        and lm[4][1] > lm[3][1]
    ):
        return "Play"

    # Pause
    if (
        lm[8][1] > lm[6][1]
        and lm[12][1] > lm[10][1]
        and lm[16][1] > lm[14][1]
        and lm[20][1] > lm[18][1]
        and lm[4][1] > lm[3][1]
    ):
        return "Pause"

    return "Unknown"
