import subprocess
import platform
import shutil

OS = platform.system().lower()

# Windows-only import is guarded (so module imports on non-Windows don't fail)
if OS == "windows":
    import ctypes


class MusicPlayer:
    def __init__(self, music_folder: str = "music"):
        """
        Keep `music_folder` parameter for API compatibility (not used).
        Initialize platform-specific helpers.
        """
        self.music_folder = music_folder
        self.is_playing = False
        self.index = 0  # kept for compatibility (not used here)

        self._platform = OS

        if self._platform == "windows":
            # VK codes for multimedia keys
            self._VK_PLAY_PAUSE = 0xB3
            self._VK_NEXT = 0xB0
            self._VK_PREV = 0xB1
            self._VK_STOP = 0xB2
            # user32 DLL for key events
            self._user32 = ctypes.WinDLL("user32", use_last_error=True)

        elif self._platform == "darwin":
            # nothing to init; will use osascript
            pass

        else:
            # assume linux-like: we'll try playerctl, then xdotool as fallback
            self._has_playerctl = shutil.which("playerctl") is not None
            self._has_xdotool = shutil.which("xdotool") is not None

    # -----------------------
    # Platform helpers
    # -----------------------
    def _send_windows_media(self, vk_code: int):
        """
        Send a multimedia virtual-key event on Windows using keybd_event.
        (keybd_event is simple and widely available.)
        """
        # key down
        self._user32.keybd_event(vk_code, 0, 0, 0)
        # key up
        self._user32.keybd_event(vk_code, 0, 2, 0)

    def _run_osascript(self, script: str):
        """Run an AppleScript snippet on macOS."""
        try:
            subprocess.run(["osascript", "-e", script], check=False)
        except FileNotFoundError:
            print("osascript not available on this system.")

    def _run_playerctl(self, command: str):
        """Run playerctl <command> if available."""
        try:
            subprocess.run(["playerctl", command], check=False)
            return True
        except FileNotFoundError:
            return False

    def _run_xdotool_key(self, key: str):
        """Use xdotool to send XF86Audio keys as fallback on Linux."""
        try:
            subprocess.run(["xdotool", "key", key], check=False)
            return True
        except FileNotFoundError:
            return False

    # -----------------------
    # Public API (same names)
    # -----------------------
    def play(self):
        """
        Toggle play/pause (or send play command) on the system.
        We'll generally send a play/pause toggle because it's the most portable action.
        """
        if self._platform == "windows":
            self._send_windows_media(self._VK_PLAY_PAUSE)
        elif self._platform == "darwin":
            # Toggle play/pause in Music app (works on modern macOS)
            self._run_osascript('tell application "Music" to playpause')
        else:
            # linux: prefer playerctl, then xdotool XF86AudioPlay
            if self._has_playerctl:
                self._run_playerctl("play-pause")
            elif self._has_xdotool:
                self._run_xdotool_key("XF86AudioPlay")
            else:
                print(
                    "No system media controller found (install `playerctl` or `xdotool`),"
                    " cannot send play/pause."
                )
                return

        self.is_playing = True
        print(f"▶️ Sent Play/Pause command (platform={self._platform}).")

    def stop(self):
        """
        Send a stop command to the system (if supported).
        """
        if self._platform == "windows":
            self._send_windows_media(self._VK_STOP)
        elif self._platform == "darwin":
            self._run_osascript('tell application "Music" to stop')
        else:
            if self._has_playerctl:
                self._run_playerctl("stop")
            elif self._has_xdotool:
                self._run_xdotool_key("XF86AudioStop")
            else:
                print(
                    "No system media controller found (install `playerctl` or `xdotool`),"
                    " cannot send stop."
                )
                return

        self.is_playing = False
        print("⏹️ Sent Stop command.")

    def next(self):
        """
        Skip to next track on the system.
        """
        if self._platform == "windows":
            self._send_windows_media(self._VK_NEXT)
        elif self._platform == "darwin":
            self._run_osascript('tell application "Music" to next track')
        else:
            if self._has_playerctl:
                self._run_playerctl("next")
            elif self._has_xdotool:
                self._run_xdotool_key("XF86AudioNext")
            else:
                print(
                    "No system media controller found (install `playerctl` or `xdotool`),"
                    " cannot send next track."
                )
                return

        self.is_playing = True
        print("⏭️ Sent Next Track command.")

    def prev(self):
        """
        Go to previous track on the system.
        """
        if self._platform == "windows":
            self._send_windows_media(self._VK_PREV)
        elif self._platform == "darwin":
            self._run_osascript('tell application "Music" to previous track')
        else:
            if self._has_playerctl:
                self._run_playerctl("previous")
            elif self._has_xdotool:
                self._run_xdotool_key("XF86AudioPrev")
            else:
                print(
                    "No system media controller found (install `playerctl` or `xdotool`),"
                    " cannot send previous track."
                )
                return

        self.is_playing = True
        print("⏮️ Sent Previous Track command.")
