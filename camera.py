"""Camera access only; no display, tracking, or image recording."""

import cv2


def open_camera(camera_index=0):
    """Open a camera by device number (0 is usually the built-in camera)."""
    camera = cv2.VideoCapture(camera_index)
    if not camera.isOpened():
        camera.release()
        raise RuntimeError(
            f"Could not open camera {camera_index}. Close other camera apps, "
            "check Windows camera permissions, and check the camera privacy shutter."
        )
    return camera


def read_frame(camera):
    """Return one image, or raise a readable error if capture fails."""
    success, frame = camera.read()
    if not success or frame is None or frame.size == 0:
        raise RuntimeError(
            "The camera stopped providing images. Check its connection "
            "and close other apps using it, then restart this program."
        )
    return frame
