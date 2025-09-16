import asyncio
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
from pathlib import Path
from modules.internal_player.db import get_conn
import modules.internal_player.repository as repo
from modules.internal_player.player import MusicPlayer
from modules.internal_player.scanner import scan_directory
from modules.internal_player.utils import format_seconds, format_size


class MusicApp(toga.App):
    def startup(self):
        self.conn = get_conn()
        self.player = MusicPlayer()

        # Main box
        self.main_box = toga.Box(style=Pack(direction=COLUMN, padding=10))

        # Directory controls
        self.dir_select_button = toga.Button("Add Folder", on_press=self.add_folder)
        self.dir_set_default_button = toga.Button("Set as Default", on_press=self.set_default_folder)
        self.dir_box = toga.Box(
            children=[self.dir_select_button, self.dir_set_default_button],
            style=Pack(direction=ROW, padding=5)
        )

        # Music table
        self.music_table = toga.Table(
            headings=["Name", "Length", "Size", "Liked", "Played"],
            on_select=self.on_select_music,
            style=Pack(flex=1)
        )

        # Controls
        self.play_button = toga.Button("Play", on_press=self.on_play)
        self.pause_button = toga.Button("Pause", on_press=self.on_pause)
        self.prev_button = toga.Button("Prev", on_press=self.on_prev)
        self.next_button = toga.Button("Next", on_press=self.on_next)
        self.vol_up_button = toga.Button("Vol +", on_press=self.on_vol_up)
        self.vol_down_button = toga.Button("Vol -", on_press=self.on_vol_down)
        self.shuffle_button = toga.Button("Shuffle", on_press=self.on_shuffle)
        self.repeat_button = toga.Button("Repeat", on_press=self.on_repeat)
        self.like_button = toga.Button("Like/Unlike", on_press=self.on_like)

        self.ctrl_box = toga.Box(
            children=[
                self.play_button, self.pause_button, self.prev_button, self.next_button,
                self.vol_up_button, self.vol_down_button,
                self.shuffle_button, self.repeat_button, self.like_button
            ],
            style=Pack(direction=ROW, padding=5)
        )

        self.main_box.add(self.dir_box)
        self.main_box.add(self.music_table)
        self.main_box.add(self.ctrl_box)

        self.main_window = toga.MainWindow(title="BeeWare Music Player")
        self.main_window.content = self.main_box
        self.main_window.show()

        # Load default directory
        self.load_default_dir()

        # periodic timer
        self.add_background_task(self.monitor_end)

    async def monitor_end(self, widget, **kwargs):
        while True:
            await asyncio.sleep(1)
            ended = self.player.on_song_end()
            if ended:
                repo.increment_play_count(self.conn, ended.id)
                self.load_musics(ended.dir_id)

    def load_default_dir(self):
        d = repo.get_default_directory(self.conn)
        if d:
            self.load_musics(d.id)

    def load_musics(self, dir_id: int):
        musics = repo.list_musics_by_dir(self.conn, dir_id)
        self.music_table.data.clear()
        for m in musics:
            self.music_table.data.append(
(                m.name,
                format_seconds(m.length),
                format_size(m.size),
                "❤️" if m.is_liked else "",
                str(m.played_count))
            )
        self.player.set_queue(musics)

    def on_select_music(self, widget, row=None):
        if row is None:
            return

        try:
            idx = self.music_table.data.index(row)
            self.player.play_index(idx)
        except ValueError:
            print("Row not found in table data")


    def on_play(self, widget): self.player.play()
    def on_pause(self, widget): self.player.pause()
    def on_prev(self, widget): self.player.prev()
    def on_next(self, widget): self.player.next()
    def on_vol_up(self, widget): self.player.volume_up()
    def on_vol_down(self, widget): self.player.volume_down()
    def on_shuffle(self, widget):
        self.player.toggle_shuffle()
        self.shuffle_button.label = f"Shuffle: {'On' if self.player.shuffle else 'Off'}"
    def on_repeat(self, widget):
        mode = self.player.cycle_repeat()
        label = ["Off", "All", "One"][mode]
        self.repeat_button.label = f"Repeat: {label}"
    def on_like(self, widget):
        if self.player.current:
            new_val = not self.player.current.is_liked
            repo.set_like(self.conn, self.player.current.id, new_val)
            self.load_musics(self.player.current.dir_id)

    async def add_folder(self, widget):
        folder = await self.main_window.select_folder_dialog("Select Music Folder")
        if folder:
            dir_id = repo.upsert_directory(self.conn, folder, Path(folder).name)
            musics = scan_directory(folder, dir_id)
            for m in musics:
                repo.upsert_music(self.conn, m)
            self.load_musics(dir_id)

    async def set_default_folder(self, widget):
        if not self.player.queue:
            return
        dir_id = self.player.queue[0].dir_id
        repo.set_default_directory(self.conn, dir_id)


def main():
    return MusicApp("BeeWare Music Player", "org.example.musicplayer")
