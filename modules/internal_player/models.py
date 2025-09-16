from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

@dataclass
class MusicDirectory:
    id: Optional[int]
    path: str
    dir_name: str
    is_default: bool

@dataclass
class Music:
    id: Optional[int]
    path: str
    name: str
    length: float  # seconds
    size: int      # bytes
    played_count: int
    is_liked: bool
    dir_id: int