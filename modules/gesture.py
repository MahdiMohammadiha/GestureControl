import mediapipe as mp
import cv2

class HandTracker:
    def __init__(self, max_num_hands=1, detection_confidence=0.7):
        # Initialize MediaPipe Hands solution
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            max_num_hands=max_num_hands,
            min_detection_confidence=detection_confidence,
            min_tracking_confidence=0.5
        )
        self.mp_draw = mp.solutions.drawing_utils  # For drawing landmarks
        self.landmarks = []  # Stores list of detected hand landmarks

    def process(self, frame):
        """
        Processes a video frame, detects hands, and draws landmarks.
        Returns the modified frame.
        """
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Convert BGR to RGB
        results = self.hands.process(rgb)  # Run hand detection
        self.landmarks = []

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Draw the detected hand landmarks on the frame
                self.mp_draw.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)

                lm_list = []
                h, w, _ = frame.shape
                for lm in hand_landmarks.landmark:
                    # Convert normalized coordinates to pixel values
                    lm_list.append((int(lm.x * w), int(lm.y * h)))
                self.landmarks.append(lm_list)

        return frame

    def get_fingers_status(self):
        """
        Returns a list of booleans [thumb, index, middle, ring, pinky].
        True means the finger is up, False means it's down.
        """
        if not self.landmarks:
            return []

        lm = self.landmarks[0]  # Use only the first detected hand
        fingers = []

        # Thumb: horizontal direction (x-axis)
        fingers.append(lm[4][0] > lm[3][0])

        # Other fingers: vertical direction (y-axis)
        fingers.append(lm[8][1] < lm[6][1])   # Index
        fingers.append(lm[12][1] < lm[10][1]) # Middle
        fingers.append(lm[16][1] < lm[14][1]) # Ring
        fingers.append(lm[20][1] < lm[18][1]) # Pinky

        return fingers

    def detect_gesture(self):
        """
        Detects specific hand gestures and returns a string:
        - "Next" for thumb pointing right
        - "Previous" for thumb pointing left
        - "Play" for index and middle fingers up (V shape)
        - "Pause" for all fingers down
        - "Unknown" if no gesture is recognized
        """
        if not self.landmarks:
            return "No hand"

        lm = self.landmarks[0]

        thumb_tip = lm[4]
        index_tip = lm[8]
        middle_tip = lm[12]
        ring_tip = lm[16]
        pinky_tip = lm[20]

        # 1. Thumb pointing to the right (Next)
        if thumb_tip[0] > index_tip[0] + 40 and all(
            lm[tip][1] > lm[base][1] for tip, base in [(8,6), (12,10), (16,14), (20,18)]
        ):
            return "Next"

        # 2. Thumb pointing to the left (Previous)
        if thumb_tip[0] < pinky_tip[0] - 40 and all(
            lm[tip][1] > lm[base][1] for tip, base in [(8,6), (12,10), (16,14), (20,18)]
        ):
            return "Previous"

        # 3. Play gesture: index and middle fingers up (V shape)
        if (
            lm[8][1] < lm[6][1] and    # Index finger up
            lm[12][1] < lm[10][1] and  # Middle finger up
            lm[16][1] > lm[14][1] and  # Ring finger down
            lm[20][1] > lm[18][1] and  # Pinky finger down
            lm[4][1] > lm[3][1]        # Thumb down or bent
        ):
            return "Play"

        # 4. Pause gesture: all fingers down
        if (
            lm[8][1] > lm[6][1] and
            lm[12][1] > lm[10][1] and
            lm[16][1] > lm[14][1] and
            lm[20][1] > lm[18][1] and
            lm[4][1] > lm[3][1]
        ):
            return "Pause"

        return "Unknown"
