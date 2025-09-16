from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
)
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import Qt
import cv2


class UI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gesture Music Controller")
        self.setGeometry(100, 100, 800, 600)

        # Server control buttons
        self.run_server_button = QPushButton("Run Server")
        self.stop_server_button = QPushButton("Stop Server")

        # Image / QR display
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Status labels
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gesture_label = QLabel("Gesture: ...")
        self.gesture_label.setStyleSheet("font-size: 20px; color: green;")
        self.gesture_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.server_status_label = QLabel("Server: stopped")
        self.server_status_label.setStyleSheet("font-size: 14px; color: red;")
        self.server_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Music control buttons
        self.play_button = QPushButton("▶️ Play")
        self.stop_button = QPushButton("⏹️ Stop")
        self.next_button = QPushButton("⏭️ Next")

        # Layouts
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.play_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.next_button)

        server_layout = QHBoxLayout()
        server_layout.addWidget(self.run_server_button)
        server_layout.addWidget(self.stop_server_button)

        layout = QVBoxLayout()
        layout.addWidget(self.image_label)
        layout.addWidget(self.status_label)
        layout.addWidget(self.gesture_label)
        layout.addWidget(self.server_status_label)
        layout.addLayout(button_layout)
        layout.addLayout(server_layout)

        self.setLayout(layout)

    # نمایش فریم‌ها
    def update_frame(self, frame, max_width=640, max_height=480):
        h, w, ch = frame.shape

        # محدود کردن اندازه با حفظ نسبت تصویر
        scale_w = min(max_width / w, 1.0)
        scale_h = min(max_height / h, 1.0)
        scale = min(scale_w, scale_h)

        new_w = int(w * scale)
        new_h = int(h * scale)

        resized_frame = cv2.resize(frame, (new_w, new_h))

        bytes_per_line = ch * new_w
        qt_image = QImage(resized_frame.data, new_w, new_h, bytes_per_line, QImage.Format.Format_BGR888)
        pixmap = QPixmap.fromImage(qt_image)
        self.image_label.setPixmap(pixmap)


    # نمایش ژست
    def update_gesture(self, gesture_name):
        self.gesture_label.setText(f"Gesture: {gesture_name}")

    # نمایش پیام وضعیت عمومی (مثل QR یا هیچ فریم)
    def update_status(self, message: str):
        self.status_label.setText(message)

    # نمایش وضعیت سرور
    def update_server_status(self, running: bool):
        if running:
            self.server_status_label.setText("Server: running")
            self.server_status_label.setStyleSheet("font-size: 14px; color: green;")
        else:
            self.server_status_label.setText("Server: stopped")
            self.server_status_label.setStyleSheet("font-size: 14px; color: red;")
