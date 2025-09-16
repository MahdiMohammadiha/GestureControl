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


# from modules.servers.frame_parser import main_frame

# class Camera:
#     def __init__(self):
#         pass

#     def get_frame(self):
#         from modules.servers.frame_parser import main_frame
#         return main_frame
