import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

class DummyHandLandmarks:
    def __init__(self, landmarks):
        self.landmark = landmarks

class DummyCategory:
    def __init__(self, label):
        self.label = label

class DummyHandedness:
    def __init__(self, category):
        self.classification = [DummyCategory(category.category_name)]

class DummyResults:
    def __init__(self, hand_landmarks_list, handedness_list):
        if hand_landmarks_list:
            self.multi_hand_landmarks = [DummyHandLandmarks(l) for l in hand_landmarks_list]
            self.multi_handedness = [DummyHandedness(c[0]) for c in handedness_list]
        else:
            self.multi_hand_landmarks = None
            self.multi_handedness = None

class HandDetector:
    def __init__(self, max_num_hands=2, min_detection_confidence=0.5, min_tracking_confidence=0.5):
        base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
        options = vision.HandLandmarkerOptions(base_options=base_options,
                                               num_hands=max_num_hands,
                                               min_hand_detection_confidence=min_detection_confidence,
                                               min_hand_presence_confidence=min_tracking_confidence)
        self.detector = vision.HandLandmarker.create_from_options(options)

    def process(self, frame):
        # Convert the BGR image to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        
        detection_result = self.detector.detect(mp_image)
        
        return DummyResults(detection_result.hand_landmarks, detection_result.handedness)

    def draw_landmarks(self, frame, results):
        if not results.multi_hand_landmarks:
            return frame

        h, w, c = frame.shape
        connections = [
            (0, 1), (1, 2), (2, 3), (3, 4),        # Thumb
            (0, 5), (5, 6), (6, 7), (7, 8),        # Index finger
            (5, 9), (9, 10), (10, 11), (11, 12),   # Middle finger
            (9, 13), (13, 14), (14, 15), (15, 16), # Ring finger
            (13, 17), (0, 17), (17, 18), (18, 19), (19, 20) # Pinky
        ]

        for hand_landmarks in results.multi_hand_landmarks:
            # Get pixel coordinates
            pixel_landmarks = []
            for lm in hand_landmarks.landmark:
                cx, cy = int(lm.x * w), int(lm.y * h)
                pixel_landmarks.append((cx, cy))
                # Draw points
                cv2.circle(frame, (cx, cy), 8, (120, 79, 38), cv2.FILLED)

            # Draw connections
            for connection in connections:
                pt1 = pixel_landmarks[connection[0]]
                pt2 = pixel_landmarks[connection[1]]
                cv2.line(frame, pt1, pt2, (255, 255, 255), 2)
                
        return frame
