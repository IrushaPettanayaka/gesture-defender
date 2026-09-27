"""MediaPipe tracking for a single hand; points use normalized image coordinates."""

from assets import model_path

CONNECTIONS = ((0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 6), (6, 7),
               (7, 8), (5, 9), (9, 10), (10, 11), (11, 12), (9, 13),
               (13, 14), (14, 15), (15, 16), (13, 17), (0, 17),
               (17, 18), (18, 19), (19, 20))


class HandPoints(list):
    """2D drawing/steering points with optional 3D geometry for curled fingers."""
    def __init__(self, points, world=None):
        super().__init__(points)
        self.world = world


class HandTracker:
    def __init__(self):
        from mediapipe.tasks import python
        from mediapipe.tasks.python import vision
        options = vision.HandLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_path=str(model_path("hand_landmarker.task"))),
            running_mode=vision.RunningMode.VIDEO, num_hands=1,
        )
        self.detector = vision.HandLandmarker.create_from_options(options)
        self.last_wrist = None
        self.last_label = None
        self.last_seen = -1000

    def detect(self, image, timestamp):
        result = self.detector.detect_for_video(image, timestamp)
        if not result.hand_landmarks:
            return None
        world = [(p.x, p.y, p.z) for p in result.hand_world_landmarks[0]] if result.hand_world_landmarks else None
        points = HandPoints([(p.x, p.y) for p in result.hand_landmarks[0]], world)
        label = result.handedness[0][0].category_name
        if self.last_wrist is not None and timestamp - self.last_seen < 800:
            jump = ((points[0][0] - self.last_wrist[0]) ** 2
                    + (points[0][1] - self.last_wrist[1]) ** 2) ** 0.5
            if label != self.last_label or jump > 0.35:
                return None
        self.last_wrist, self.last_label, self.last_seen = points[0], label, timestamp
        return points

    def close(self):
        self.detector.close()
