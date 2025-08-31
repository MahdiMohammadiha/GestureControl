import qrcode
from PIL import Image, ImageTk
import tkinter as tk

def generate_qr():
    url = url_entry.get()
    if not url:
        return
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    img_tk = ImageTk.PhotoImage(img)
    qr_label.config(image=img_tk)
    qr_label.image = img_tk  # Holding a reference to prevent deletion by the Garbage Collector

root = tk.Tk()
root.title("QR Code Generator")

tk.Label(root, text="Enter URL:").pack(pady=5)
url_entry = tk.Entry(root, width=50)
url_entry.pack(pady=5)

tk.Button(root, text="Generate QR Code", command=generate_qr).pack(pady=10)

qr_label = tk.Label(root)
qr_label.pack(pady=10)

root.mainloop()
