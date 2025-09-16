import sqlite3
from pathlib import Path
from typing import Iterator

DB_PATH = Path(__file__).resolve().parent / "music_player.db"


SCHEMA = r"""
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS music_directories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT NOT NULL UNIQUE,
    dir_name TEXT NOT NULL,
    is_default INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS musics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    length REAL NOT NULL DEFAULT 0,
    size INTEGER NOT NULL DEFAULT 0,
    played_count INTEGER NOT NULL DEFAULT 0,
    is_liked INTEGER NOT NULL DEFAULT 0,
    dir_id INTEGER NOT NULL,
    FOREIGN KEY (dir_id) REFERENCES music_directories(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_musics_dir_id ON musics(dir_id);
"""

def get_conn() -> sqlite3.Connection:
    first_time = not DB_PATH.exists()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    if first_time:
        with conn:
            conn.executescript(SCHEMA)
    return conn

def transaction(conn: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    try:
        conn.execute("BEGIN")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
