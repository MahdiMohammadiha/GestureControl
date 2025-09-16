# main_tk.py
import tkinter as tk
from tkinter import messagebox

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Main Menu")
        self.geometry("300x200")

        internal_btn = tk.Button(self, text="Internal Music Player", command=self.open_internal_player)
        internal_btn.pack(pady=10, fill="x", padx=20)

        external_btn = tk.Button(self, text="External Music Player", command=self.open_player)
        external_btn.pack(pady=10, fill="x", padx=20)

        external_btn = tk.Button(self, text="Settings", command=self.open_player)
        external_btn.pack(pady=10, fill="x", padx=20)

    def open_internal_player(self):
        self.destroy()  # بستن پنجره اصلی
        try:
            # Lazy import: فقط وقتی کاربر کلیک کرد
            from modules.internal_player.main import open_internal_player_window
            open_internal_player_window()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open Internal Player:\n{e}")

    def open_player(self):
        self.destroy()
        try:
            from modules.main import open_player_window
            open_player_window()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open External Player:\n{e}")


if __name__ == "__main__":
    window = MainWindow()
    window.mainloop()
