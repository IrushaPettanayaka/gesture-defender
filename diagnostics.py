"""Opt-in packaged-build checks; writes metadata only, never camera frames."""
import json
from pathlib import Path
import sys
import time


def run_checks(output_path, check_camera=False):
    report = {"frozen": bool(getattr(sys, "frozen", False)), "python": sys.version,
              "camera_requested": check_camera, "success": False}
    try:
        import numpy as np
        import mediapipe as mp
        from face_tracking import FaceTracker
        from hand_tracking import HandTracker
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.zeros((240, 320, 3), dtype=np.uint8))
        face = FaceTracker()
        try:
            hand = HandTracker()
            try:
                face.detect(image, 1)
                hand.detect(image, 1)
                report["models_loaded"] = True
            finally:
                hand.close()
        finally:
            face.close()
        if check_camera:
            from tracking import TrackingWorker
            worker = TrackingWorker()
            worker.start()
            try:
                deadline = time.monotonic() + 20
                while time.monotonic() < deadline:
                    packet, error = worker.snapshot()
                    if error:
                        raise RuntimeError(error)
                    if packet:
                        report["camera_shape"] = list(packet.rgb.shape)
                        report["face_detected"] = packet.face is not None
                        report["hand_detected"] = packet.hand is not None
                        break
                    time.sleep(0.05)
                else:
                    raise RuntimeError("Camera check timed out")
            finally:
                report["worker_stopped"] = worker.close()
        report["success"] = True
    except Exception as error:
        report["error"] = str(error)
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0 if report["success"] else 1
