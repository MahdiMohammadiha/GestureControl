import pygame
import random
from pathlib import Path
from typing import List, Optional
from modules.internal_player.models import Music

class MusicPlayer:
    def __init__(self):
        pygame.mixer.init()
        self.current: Optional[Music] = None
        self.queue: List[Music] = []
        self.index: int = -1
        self.volume: float = 0.5
        self.shuffle: bool = False
        self.repeat_mode: int = 0  # 0=off, 1=all, 2=one
        pygame.mixer.music.set_volume(self.volume)

    def set_queue(self, musics: List[Music]):
        self.queue = musics
        self.index = -1

    def play_index(self, idx: int):
        if not (0 <= idx < len(self.queue)):
            return
        m = self.queue[idx]
        if not Path(m.path).exists():
            return
        pygame.mixer.music.load(m.path)
        pygame.mixer.music.play()
        self.current = m
        self.index = idx

    def play(self):
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.unpause()
        elif self.index >= 0:
            pygame.mixer.music.play()
        elif self.queue:
            self.play_index(0)

    def pause(self):
        pygame.mixer.music.pause()

    def stop(self):
        pygame.mixer.music.stop()

    def next(self):
        if not self.queue:
            return
        if self.shuffle:
            self.index = random.randrange(len(self.queue))
        else:
            self.index += 1
            if self.index >= len(self.queue):
                if self.repeat_mode == 1:  # repeat all
                    self.index = 0
                else:
                    self.index = len(self.queue) - 1
                    return
        self.play_index(self.index)

    def prev(self):
        if not self.queue:
            return
        self.index -= 1
        if self.index < 0:
            if self.repeat_mode == 1:  # repeat all
                self.index = len(self.queue) - 1
            else:
                self.index = 0
                return
        self.play_index(self.index)

    def set_volume(self, vol: float):
        self.volume = max(0.0, min(1.0, vol))
        pygame.mixer.music.set_volume(self.volume)

    def volume_up(self):
        self.set_volume(self.volume + 0.1)

    def volume_down(self):
        self.set_volume(self.volume - 0.1)

    def toggle_shuffle(self):
        self.shuffle = not self.shuffle

    def cycle_repeat(self):
        self.repeat_mode = (self.repeat_mode + 1) % 3
        return self.repeat_mode

    def is_playing(self):
        return pygame.mixer.music.get_busy()

    def on_song_end(self):
        """Check if current song ended and take action (repeat/next)."""
        if not self.current:
            return None
        if not pygame.mixer.music.get_busy():
            if self.repeat_mode == 2:  # repeat one
                self.play_index(self.index)
            else:
                self.next()
            return self.current
        return None
