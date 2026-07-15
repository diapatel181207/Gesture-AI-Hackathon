import cv2

class WebcamManager:
    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self.cap = None

    def start(self):
        if self.cap is None or not self.cap.isOpened():
            self.cap = cv2.VideoCapture(self.camera_index)
            # You might want to adjust resolution here
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    def stop(self):
        if self.cap and self.cap.isOpened():
            self.cap.release()
            self.cap = None

    def read_frame(self):
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                # Flip the frame horizontally for a selfie-view display
                frame = cv2.flip(frame, 1)
                return frame
        return None
