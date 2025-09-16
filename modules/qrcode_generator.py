import qrcode
from PIL import Image, ImageTk
import tkinter as tk
import socket

def get_local_ip():
    """Get the local IP address of the system"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    except Exception:
        ip = "127.0.0.1"
    return ip

