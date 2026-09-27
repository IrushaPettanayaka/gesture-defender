from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scores import ScoreStore


class ScoreTests(unittest.TestCase):
    def test_missing_corrupt_and_roundtrip(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "best.json"
            store = ScoreStore(path)
            self.assertEqual(store.best, 0)
            self.assertTrue(store.save(250))
            self.assertEqual(ScoreStore(path).best, 250)
            store.save(100)
            self.assertEqual(ScoreStore(path).best, 250)
            for content in ('broken', '{}', '[]', '{"best": -1}', '{"best": true}'):
                path.write_text(content)
                self.assertEqual(ScoreStore(path).best, 0)

    def test_failed_save_is_nonfatal(self):
        with tempfile.TemporaryDirectory() as folder:
            store = ScoreStore(Path(folder) / "best.json")
            with patch("scores.tempfile.NamedTemporaryFile", side_effect=PermissionError):
                self.assertFalse(store.save(25))
            self.assertTrue(store.error)
