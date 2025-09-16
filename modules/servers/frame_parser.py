import cv2
import numpy as np
import asyncio
import math

# تنظیمات
MAX_CLIENTS = 4
FRAME_WIDTH = 320
FRAME_HEIGHT = 240

# متغیر سراسری برای نگه داشتن main_frame
main_frame_id = None
main_frame = None
the_frame = None

# توابع دسترسی از ماژول دیگر
def get_main_frame_id():
    return main_frame_id

def get_main_frame():
    return main_frame

# callback ماوس برای انتخاب یا لغو انتخاب فریم
def mouse_callback(event, x, y, flags, param):
    global main_frame_id, main_frame
    if event == cv2.EVENT_LBUTTONDOWN:
        client_positions = param["positions"]
        latest_frames = param["latest_frames"]
        for client_id, (x1, y1, x2, y2) in client_positions.items():
            if x1 <= x < x2 and y1 <= y < y2:
                if client_id == main_frame_id:
                    # اگر دوباره روی همان فریم کلیک شد، لغو انتخاب
                    main_frame_id = None
                    main_frame = None
                    print(f"Main frame selection cancelled")
                else:
                    # انتخاب فریم جدید
                    main_frame_id = client_id
                    main_frame = latest_frames[client_id].copy()
                    print(f"Selected main frame: {main_frame_id}")
                break

async def show_frames(latest_frames):
    global main_frame_id, main_frame, the_frame
    while True:
        client_ids = list(latest_frames.keys())
        n_clients = len(client_ids)
        if n_clients == 0:
            canvas = np.zeros((FRAME_HEIGHT, FRAME_WIDTH, 3), dtype=np.uint8)
            client_positions = {}
        else:
            rows = math.ceil(math.sqrt(n_clients))
            cols = math.ceil(n_clients / rows)
            canvas = np.zeros((rows * FRAME_HEIGHT, cols * FRAME_WIDTH, 3), dtype=np.uint8)
            client_positions = {}

            for idx, client_id in enumerate(client_ids):
                frame = latest_frames[client_id]
                frame_resized = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
                
                row_idx = idx // cols
                col_idx = idx % cols
                
                y1 = row_idx * FRAME_HEIGHT
                y2 = y1 + FRAME_HEIGHT
                x1 = col_idx * FRAME_WIDTH
                x2 = x1 + FRAME_WIDTH
                
                canvas[y1:y2, x1:x2] = frame_resized
                cv2.putText(canvas, f"ID: {client_id}", (x1 + 5, y1 + 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                
                if client_id == main_frame_id:
                    cv2.rectangle(canvas, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    # آپدیت پنجره main_frame
                    main_frame = frame.copy()

                client_positions[client_id] = (x1, y1, x2, y2)

        cv2.imshow("All Clients", canvas)
        # نمایش main_frame در پنجره جداگانه
        if main_frame is not None:
            the_frame = main_frame

        cv2.setMouseCallback("All Clients", mouse_callback, param={"positions": client_positions, "latest_frames": latest_frames})
        
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
        await asyncio.sleep(0.01)

    cv2.destroyAllWindows()
