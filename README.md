# Gesture Control

This project is a gesture-controlled music player that allows you to control music playback using simple hand gestures in front of your webcam. It uses computer vision to detect hand positions and interprets gestures to play, pause, or switch tracks.


## ✨ Features

- Real-time hand tracking with MediaPipe  
- Control music playback using gestures  
- GUI built with PyQt6  
- Local `.mp3` music playback using `pygame`  
- Optional GUI buttons for manual control  


## ✋ Supported Gestures

| Gesture          | Action         |
|------------------|----------------|
| ✌️ V Sign         | Play Music     |
| ✊ Fist            | Pause Music    |
| 👉 Thumb Right     | Next Track     |
| 👈 Thumb Left      | Previous Track |


## 🧱 Project Structure

```
gesture_control/
│
├── main.py            # Entry point
├── modules/
│ ├── camera.py        # Webcam frame capture
│ ├── gesture.py       # Gesture detection
│ ├── music_player.py  # Music playback control
│ ├── controller.py    # Gesture → Action mapping
│ └── gui.py           # PyQt6 GUI
└── music/             # Folder for your MP3 files
```


## ⚙️ Requirements

```bash
pip install -r requirements.txt
```

Contents of `requirements.txt`:

```
opencv-python
mediapipe
PyQt6
pygame
```


## ▶️ How to Use

1. Place your `.mp3` music files in the `music/` folder.  
2. Run the program:

```bash
python main.py
```

3. Perform a gesture in front of your webcam and watch it control your music!


## 🧪 Example Usage

- Show ✌️ to start music  
- Show ✊ to stop music  
- Point 👉 to skip to next  
- Point 👈 to go back

