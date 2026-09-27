import unittest
from calibration import Calibration
from preferences import Preferences
from pathlib import Path
import tempfile


class CalibrationTests(unittest.TestCase):
    def test_two_holds_and_loss_reset(self):
        calibration = Calibration()
        for _ in range(15):
            calibration.update(0.2, 0.1)
        calibration.update(None, 0.1)
        self.assertEqual(calibration.elapsed, 0)
        for _ in range(20):
            calibration.update(0.2, 0.1)
        self.assertEqual(calibration.stage, 1)
        for _ in range(20):
            calibration.update(0.8, 0.1)
        self.assertEqual(calibration.result, (0.2, 0.8))

    def test_narrow_range_retries(self):
        calibration = Calibration()
        for _ in range(40):
            calibration.update(0.5, 0.1)
        self.assertIsNone(calibration.result)
        self.assertEqual(calibration.stage, 0)

    def test_settings_save_validation_and_recovery(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "settings.json"
            settings = Preferences(path)
            settings.values["muted"] = True
            settings.save()
            self.assertTrue(Preferences(path).values["muted"])
            path.write_text('{"volume": 999, "range_left": 0.8, "range_right": 0.2}')
            values = Preferences(path).values
            self.assertEqual(values["volume"], 0.3)
            self.assertLess(values["range_left"], values["range_right"])
            path.write_text('not json')
            self.assertFalse(Preferences(path).values["muted"])
