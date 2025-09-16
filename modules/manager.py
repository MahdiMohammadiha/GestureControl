from socket import socket
from modules.camera import Camera
from modules.gesture import HandTracker
from modules.music_player import MusicPlayer
from modules.controller import GestureController
from PyQt6.QtWidgets import QApplication
from modules.gui import UI
import sys
import threading
from modules.servers import server
import qrcode
from PyQt6.QtGui import QImage, QPixmap
import io

server_thread = None
server_running = False

def start_server():
    global server_thread, server_running
    if server_running:
        return
    server_running = True
    window.update_server_status(True)  # وضعیت سرور رو آپدیت کن

    def run():
        server.main()

    server_thread = threading.Thread(target=run, daemon=True)
    server_thread.start()


import signal
import os

def stop_server():
    global server_running
    if not server_running:
        return
    server_running = False
    window.update_server_status(False)
    print("Server stopped")

    # روش ۱: raise مستقیم
    raise KeyboardInterrupt

    # یا روش ۲: ارسال سیگنال مثل Ctrl+C به پروسه
    os.kill(os.getpid(), signal.SIGINT)



# تولید QR code به QPixmap
def generate_qr_pixmap(url):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    qt_img = QImage.fromData(buf.getvalue())
    return QPixmap.fromImage(qt_img)


def main():
    global window
    app = QApplication(sys.argv)
    window = UI()

    cam = Camera()
    tracker = HandTracker()
    player = MusicPlayer()
    controller = GestureController(player, cooldown=2.5)

    window.play_button.clicked.connect(player.play)
    window.stop_button.clicked.connect(player.stop)
    window.next_button.clicked.connect(player.next)

    window.run_server_button.clicked.connect(start_server)
    window.stop_server_button.clicked.connect(stop_server)

    # QR code fallback

    from modules.qrcode_generator import get_local_ip
    ip = get_local_ip()
    qr_url = f"https://{ip}:10001"

    qr_pixmap = generate_qr_pixmap(qr_url)

    window.show()

    # اجرای خودکار سرور
    start_server()

    while window.isVisible():
        frame = cam.get_frame()
        if frame is None:
            window.image_label.setPixmap(qr_pixmap)
            window.update_status("هیچ فریمی انتخاب نشده.\nابتدا QR را اسکن و دسترسی بدهید")
            app.processEvents()
            continue

        frame = tracker.process(frame)
        gesture = tracker.detect_gesture()
        
        if gesture is not None:
            print("Gesture:", gesture)

        if gesture == "Reserve2":
            exit()

        controller.handle_gesture(gesture)

        if gesture is not None:
            window.update_status(f"آخرین ژست: {gesture}")
        else:
            window.update_status("فریمی دریافت شد، ژست شناسایی نشد")

        window.update_frame(frame)
        window.update_gesture(gesture)
        app.processEvents()

    cam.release()


if __name__ == "__main__":
    main()
