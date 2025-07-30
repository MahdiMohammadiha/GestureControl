import pygame
import os

class MusicPlayer:
    def __init__(self, music_folder="music"):
        pygame.mixer.init()
        self.music_folder = music_folder
        self.playlist = [f for f in os.listdir(music_folder) if f.endswith(".mp3")]
        self.playlist.sort()
        self.index = 0
        self.is_playing = False

        if not self.playlist:
            raise Exception("No MP3 files found in 'music' folder.")

    def play(self):
        if not self.is_playing:
            self._load_current()
            pygame.mixer.music.play()
            self.is_playing = True
            print(f"▶️ Playing: {self.playlist[self.index]}")

    def stop(self):
        pygame.mixer.music.stop()
        self.is_playing = False
        print("⏹️ Stopped.")

    def next(self):
        self.index = (self.index + 1) % len(self.playlist)
        self._load_current()
        pygame.mixer.music.play()
        self.is_playing = True
        print(f"⏭️ Next: {self.playlist[self.index]}")

    def prev(self):
        self.index = (self.index - 1) % len(self.playlist)
        self._load_current()
        pygame.mixer.music.play()
        self.is_playing = True
        print(f"⏮️ Previous: {self.playlist[self.index]}")

    def _load_current(self):
        path = os.path.join(self.music_folder, self.playlist[self.index])
        pygame.mixer.music.load(path)
