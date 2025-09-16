from pathlib import Path

AUDIO_EXTS = {".mp3", ".ogg", ".wav", ".flac", ".m4a", ".aac"}

def is_audio_file(p: Path) -> bool:
    return p.suffix.lower() in AUDIO_EXTS

def format_seconds(sec: float) -> str:
    sec = int(sec)
    m, s = divmod(sec, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

def format_size(bytes_: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if bytes_ < 1024 or unit == "GB":
            return f"{bytes_:.0f} {unit}" if unit == "B" else f"{bytes_/1024:.1f} {unit}"
        bytes_ /= 1024
