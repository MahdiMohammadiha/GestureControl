from pathlib import Path
from typing import List
from mutagen import File as MutagenFile
from modules.internal_player.models import Music
from modules.internal_player.utils import is_audio_file

def scan_directory(dir_path: str, dir_id: int) -> List[Music]:
    base = Path(dir_path)
    items: List[Music] = []
    if not base.exists() or not base.is_dir():
        return items

    for p in sorted(base.iterdir()):
        if not p.is_file() or not is_audio_file(p):
            continue
        length = 0.0
        try:
            mf = MutagenFile(p.as_posix())
            if mf is not None and mf.info is not None and getattr(mf.info, 'length', None):
                length = float(mf.info.length)
        except Exception:
            length = 0.0
        size = p.stat().st_size
        items.append(Music(
            id=None,
            path=p.as_posix(),
            name=p.stem,
            length=length,
            size=size,
            played_count=0,
            is_liked=False,
            dir_id=dir_id,
        ))
    return items
