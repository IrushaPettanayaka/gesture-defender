"""One face's normalized MediaPipe landmarks for presence checks and overlays."""

from assets import model_path


class FaceTracker:
    def __init__(self):
        from mediapipe.tasks import python
        from mediapipe.tasks.python import vision
        options = vision.FaceLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_path=str(model_path("face_landmarker.task"))),
            running_mode=vision.RunningMode.VIDEO,
            num_faces=1,
        )
        self.detector = vision.FaceLandmarker.create_from_options(options)

    def detect(self, image, timestamp):
        result = self.detector.detect_for_video(image, timestamp)
        if not result.face_landmarks:
            return None
        points = result.face_landmarks[0]
        return [(p.x, p.y) for p in points]

    def close(self):
        self.detector.close()
