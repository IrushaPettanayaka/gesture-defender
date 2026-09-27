import unittest
from unittest.mock import Mock, patch
import numpy as np
import camera


class CameraTests(unittest.TestCase):
    def test_failed_open_releases_handle(self):
        capture = Mock()
        capture.isOpened.return_value = False
        with patch.object(camera.cv2, "VideoCapture", return_value=capture):
            with self.assertRaisesRegex(RuntimeError, "Could not open"):
                camera.open_camera()
        capture.release.assert_called_once()

    def test_failed_or_empty_frame_is_rejected(self):
        for result in ((False, None), (True, None), (True, np.zeros((0, 0, 3)))):
            capture = Mock()
            capture.read.return_value = result
            with self.assertRaises(RuntimeError):
                camera.read_frame(capture)


if __name__ == "__main__":
    unittest.main()
