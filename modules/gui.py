from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton
)
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import Qt


class UI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gesture Music Controller")
        self.setGeometry(100, 100, 800, 600)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gesture_label = QLabel("Gesture: ...")
        self.gesture_label.setStyleSheet("font-size: 20px; color: green;")
        self.gesture_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Control buttons
        self.play_button = QPushButton("▶️ Play")
        self.stop_button = QPushButton("⏹️ Stop")
        self.next_button = QPushButton("⏭️ Next")

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.play_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.next_button)

        # Main layout
        layout = QVBoxLayout()
        layout.addWidget(self.image_label)
        layout.addWidget(self.gesture_label)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def update_frame(self, frame):
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_BGR888)
        pixmap = QPixmap.fromImage(qt_image)
        self.image_label.setPixmap(pixmap)

    def update_gesture(self, gesture_name):
        self.gesture_label.setText(f"Gesture: {gesture_name}")
