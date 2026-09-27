import unittest
from gestures import GestureInterpreter


def palm():
    points = [(0.5, 0.8)] * 21
    points[4] = (0.2, 0.45)
    for base, x in ((5, 0.40), (9, 0.5), (13, 0.60), (17, 0.70)):
        points[base] = (x, 0.60)
        points[base + 1] = (x, 0.45)
        points[base + 2] = (x, 0.30)
        points[base + 3] = (x, 0.15)
    return points


class GestureTests(unittest.TestCase):
    def test_pinch_requires_hold_release_and_survives_detection_flicker(self):
        gesture = GestureInterpreter()
        points = palm()
        points[4] = points[8]
        self.assertFalse(gesture.update(points, 0).shoot)
        self.assertTrue(gesture.update(points, 0.08).shoot)
        self.assertFalse(gesture.update(points, 1).shoot)
        gesture.update(None, 1.1)
        self.assertFalse(gesture.update(points, 1.2).shoot)
        gesture.update(palm(), 1.3)
        self.assertFalse(gesture.update(points, 1.4).shoot)
        self.assertTrue(gesture.update(points, 1.5).shoot)

    def test_palm_requires_hold_and_rearms_after_release(self):
        gesture = GestureInterpreter()
        points = palm()
        self.assertFalse(gesture.update(points, 0).toggle)
        self.assertTrue(gesture.update(points, 0.7).toggle)
        self.assertFalse(gesture.update(points, 2).toggle)
        gesture.update(None, 2.1)
        self.assertFalse(gesture.update(points, 2.2).toggle)
        self.assertFalse(gesture.update(points, 3).toggle)
        fist = [(0.5, 0.8)] * 21
        gesture.update(fist, 3.1)
        gesture.update(points, 3.2)
        self.assertTrue(gesture.update(points, 4).toggle)

    def test_smoothing_and_missing_hand_keeps_position(self):
        gesture = GestureInterpreter()
        points = palm()
        points[8] = (1.0, 0.2)
        first = gesture.update(points, 0).x
        self.assertTrue(0.5 < first < 1)
        second = gesture.update(points, 0.1).x
        self.assertTrue(first < second < 1)
        self.assertEqual(gesture.update(None, 0.2).x, second)


if __name__ == "__main__":
    unittest.main()
