"""Capture and inference off the UI thread; retain only the latest frame in RAM."""

from contextlib import ExitStack
from dataclasses import dataclass
import threading
import time
import logging

from face_tracking import FaceTracker
from hand_tracking import HandTracker
from settings import CAMERA_WIDTH, CAMERA_HEIGHT


@dataclass(frozen=True)
class TrackingFrame:
    sequence: int
    captured_at: float
    rgb: object
    face: object
    hand: object


class TrackingWorker:
    def __init__(self, camera_index=0, low_resolution=False):
        self.camera_index = camera_index
        self.resolution = (424, 318) if low_resolution else (CAMERA_WIDTH, CAMERA_HEIGHT)
        self.lock = threading.Lock()
        self.stop = threading.Event()
        self.latest = None
        self.error = None
        self.thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self.thread.start()

    def snapshot(self):
        with self.lock:
            return self.latest, self.error

    def close(self):
        self.stop.set()
        if self.thread.ident is not None:
            self.thread.join(timeout=2)
        return not self.thread.is_alive()

    def _run(self):
        try:
            with ExitStack() as cleanup:
                face = FaceTracker()
                cleanup.callback(face.close)
                hand = HandTracker()
                cleanup.callback(hand.close)
                import cv2
                import mediapipe as mp
                from camera import open_camera, read_frame
                if self.stop.is_set():
                    return
                camera = open_camera(self.camera_index)
                cleanup.callback(camera.release)
                camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
                camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
                sequence, timestamp = 0, 0
                while not self.stop.is_set():
                    frame = read_frame(camera)
                    captured_at = time.monotonic()
                    frame = cv2.resize(cv2.flip(frame, 1), self.resolution)
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
                    timestamp = max(timestamp + 1, int(captured_at * 1000))
                    face_box = face.detect(image, timestamp)
                    landmarks = hand.detect(image, timestamp)
                    sequence += 1
                    with self.lock:
                        self.latest = TrackingFrame(sequence, captured_at, rgb, face_box, landmarks)
        except Exception as error:
            logging.exception("Camera/tracking worker failed")
            with self.lock:
                if getattr(error, "winerror", None) == 4551:
                    self.error = (
                        "Windows Application Control blocked MediaPipe's native tracking library "
                        "(error 4551). The library needs approval under your Windows security policy. "
                        "Press K to play with the keyboard instead."
                    )
                else:
                    self.error = str(error) or type(error).__name__
