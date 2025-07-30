from modules.camera import Camera
from modules.gesture import HandTracker
from modules.music_player import MusicPlayer
from modules.controller import GestureController
from PyQt6.QtWidgets import QApplication
from modules.gui import UI
import sys

def main():
    app = QApplication(sys.argv)
    window = UI()

    cam = Camera()
    tracker = HandTracker()
    player = MusicPlayer()
    controller = GestureController(player, cooldown=2.5)

    window.play_button.clicked.connect(player.play)
    window.stop_button.clicked.connect(player.stop)
    window.next_button.clicked.connect(player.next)

    window.show()

    while window.isVisible():
        frame = cam.get_frame()
        if frame is None:
            break

        frame = tracker.process(frame)
        gesture = tracker.detect_gesture()
        controller.handle_gesture(gesture)

        window.update_frame(frame)
        window.update_gesture(gesture)

        app.processEvents()

    cam.release()

if __name__ == "__main__":
    main()
