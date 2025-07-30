import cv2

class Camera:
    def __init__(self, index=0):
        self.cap = cv2.VideoCapture(index)

    def get_frame(self):
        success, frame = self.cap.read()
        if not success:
            return None
        return cv2.flip(frame, 1)

    def release(self):
        self.cap.release()
        cv2.destroyAllWindows()
