import sqlite3
from typing import List, Optional
from modules.internal_player.models import MusicDirectory, Music


# Directories
def upsert_directory(conn, path: str, dir_name: str, is_default: bool = False) -> int:
    path = str(path)
    dir_name = str(dir_name)
    cur = conn.execute(
        """
        INSERT INTO music_directories (path, dir_name, is_default)
        VALUES (?, ?, ?)
        ON CONFLICT(path) DO UPDATE SET dir_name=excluded.dir_name, is_default=excluded.is_default
        RETURNING id
        """,
        (path, dir_name, int(is_default)),
    )
    return int(cur.fetchone()[0])


def list_directories(conn) -> List[MusicDirectory]:
    cur = conn.execute(
        "SELECT id, path, dir_name, is_default FROM music_directories ORDER BY dir_name"
    )
    return [
        MusicDirectory(id=row[0], path=row[1], dir_name=row[2], is_default=bool(row[3]))
        for row in cur
    ]


def get_default_directory(conn) -> Optional[MusicDirectory]:
    cur = conn.execute(
        "SELECT id, path, dir_name, is_default FROM music_directories WHERE is_default=1 LIMIT 1"
    )
    row = cur.fetchone()
    return (
        MusicDirectory(id=row[0], path=row[1], dir_name=row[2], is_default=bool(row[3]))
        if row
        else None
    )


def set_default_directory(conn, dir_id: int):
    conn.execute(
        "UPDATE music_directories SET is_default=CASE WHEN id=? THEN 1 ELSE 0 END",
        (dir_id,),
    )


# Musics
def upsert_music(conn, m: Music) -> int:
    cur = conn.execute(
        """
        INSERT INTO musics (path, name, length, size, played_count, is_liked, dir_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(path) DO UPDATE SET
            name=excluded.name,
            length=excluded.length,
            size=excluded.size,
            dir_id=excluded.dir_id
        RETURNING id
        """,
        (m.path, m.name, m.length, m.size, m.played_count, int(m.is_liked), m.dir_id),
    )
    return int(cur.fetchone()[0])


def list_musics_by_dir(conn, dir_id: int) -> List[Music]:
    cur = conn.execute(
        "SELECT id, path, name, length, size, played_count, is_liked, dir_id FROM musics WHERE dir_id=? ORDER BY name",
        (dir_id,),
    )
    return [
        Music(
            id=row[0],
            path=row[1],
            name=row[2],
            length=row[3],
            size=row[4],
            played_count=row[5],
            is_liked=bool(row[6]),
            dir_id=row[7],
        )
        for row in cur
    ]


def increment_play_count(conn, music_id: int):
    conn.execute(
        "UPDATE musics SET played_count = played_count + 1 WHERE id=?", (music_id,)
    )


def set_like(conn, music_id: int, liked: bool):
    conn.execute("UPDATE musics SET is_liked=? WHERE id=?", (int(liked), music_id))


def get_music_by_id(conn, music_id: int) -> Optional[Music]:
    cur = conn.execute(
        "SELECT id, path, name, length, size, played_count, is_liked, dir_id FROM musics WHERE id=?",
        (music_id,),
    )
    row = cur.fetchone()
    if not row:
        return None
    return Music(
        id=row[0],
        path=row[1],
        name=row[2],
        length=row[3],
        size=row[4],
        played_count=row[5],
        is_liked=bool(row[6]),
        dir_id=row[7],
    )
