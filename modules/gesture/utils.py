from typing import Tuple, List
import math
import threading
from playsound import playsound


Point = Tuple[int, int]


def play_sound_effect(file_path):
    threading.Thread(target=playsound, args=(file_path,), daemon=True).start()


def dist(a: Point, b: Point) -> float:
    """Euclidean distance between two points."""
    return math.hypot(a[0] - b[0], a[1] - b[1])


def palm_center(landmarks: List[Point]) -> Point:
    """Return a simple palm center estimate (wrist & middle_finger_mcp midpoint)."""
    # wrist = 0, middle_mcp = 9
    cx = (landmarks[0][0] + landmarks[9][0]) // 2
    cy = (landmarks[0][1] + landmarks[9][1]) // 2
    return (cx, cy)
