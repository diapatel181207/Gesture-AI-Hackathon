import asyncio
import websockets
import json
import threading
import cv2
import base64
from webcam import WebcamManager
from detector import HandDetector
from classifier import GestureClassifier
from automation import AutomationEngine
from database import DatabaseManager


class GestureApp:
    def __init__(self):
        self.db = DatabaseManager()
        self.webcam = WebcamManager()
        self.detector = HandDetector()
        self.classifier = GestureClassifier()
        self.automation = AutomationEngine(self.db)

        self.is_detecting = False
        self.connected_clients = set()
        self.loop = None  # set after asyncio loop starts

    async def register(self, websocket):
        self.connected_clients.add(websocket)
        try:
            async for message in websocket:
                data = json.loads(message)
                action = data.get("action")
                if action == "start":
                    self.start_detection()
                elif action == "stop":
                    self.stop_detection()
                elif action == "get_mappings":
                    await websocket.send(json.dumps({
                        "type": "mappings",
                        "data": self.db.get_mappings()
                    }))
                elif action == "update_mapping":
                    gesture = data.get("gesture")
                    new_action = data.get("mapped_action")
                    shortcut = data.get("shortcut", "")
                    if gesture and new_action:
                        self.db.update_mapping(gesture, new_action, shortcut)
                        await websocket.send(json.dumps({"type": "mapping_updated", "gesture": gesture}))
                elif action == "get_settings":
                    await websocket.send(json.dumps({
                        "type": "settings",
                        "data": {
                            "sensitivity": self.automation.get_sensitivity(),
                            "min_sensitivity": self.automation.MIN_SENSITIVITY,
                            "max_sensitivity": self.automation.MAX_SENSITIVITY,
                        }
                    }))
                elif action == "update_sensitivity":
                    value = data.get("sensitivity")
                    if value is not None:
                        new_value = self.automation.set_sensitivity(value)
                        await websocket.send(json.dumps({
                            "type": "settings",
                            "data": {
                                "sensitivity": new_value,
                                "min_sensitivity": self.automation.MIN_SENSITIVITY,
                                "max_sensitivity": self.automation.MAX_SENSITIVITY,
                            }
                        }))
                elif action == "get_history":
                    history = self.db.get_history()
                    await websocket.send(json.dumps({"type": "history", "data": history}))
        finally:
            self.connected_clients.discard(websocket)

    def start_detection(self):
        if not self.is_detecting:
            self.is_detecting = True
            self.webcam.start()
            threading.Thread(target=self.detection_loop, daemon=True).start()
            print("[GestureApp] Detection started")

    def stop_detection(self):
        self.is_detecting = False
        self.webcam.stop()
        print("[GestureApp] Detection stopped")

    def detection_loop(self):
        prev_gesture = None
        while self.is_detecting:
            frame = self.webcam.read_frame()
            if frame is None:
                continue

            results = self.detector.process(frame)
            frame = self.detector.draw_landmarks(frame, results)

            # Encode frame as JPEG base64
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 55])
            frame_b64 = base64.b64encode(buffer).decode('utf-8')

            gesture_name = None
            action_label = 'Idle'
            hand_label = ''

            if results.multi_hand_landmarks:
                for hand_lm, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                    hand_label = handedness.classification[0].label
                    gesture_name = self.classifier.classify(hand_lm, hand_label)

                    if gesture_name and gesture_name != 'Unknown':
                        action_label = self.automation.execute(gesture_name, hand_lm)
                    break  # Process first hand only for now

            # Build payload
            payload = {
                "type": "update",
                "frame": frame_b64,
                "gesture": gesture_name or "None",
                "hand": hand_label,
                "action": action_label,
            }

            if self.loop:
                asyncio.run_coroutine_threadsafe(
                    self.broadcast(json.dumps(payload)),
                    self.loop
                )

    async def broadcast(self, message):
        dead = set()
        for client in self.connected_clients:
            try:
                await client.send(message)
            except Exception:
                dead.add(client)
        self.connected_clients -= dead


async def main():
    app = GestureApp()

    async def serve(ws):
        await app.register(ws)

    async with websockets.serve(serve, "localhost", 8765):
        app.loop = asyncio.get_running_loop()
        print("[GestureApp] WebSocket server running on ws://localhost:8765")
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
