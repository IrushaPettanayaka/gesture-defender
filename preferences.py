"""Validated local settings; no device data or images are persisted."""
import json
import os
from pathlib import Path
import tempfile

DEFAULTS = {"reduced_motion": False, "muted": False, "volume": 0.3,
            "low_resolution": False, "sensitivity": 1.0,
            "range_left": 0.08, "range_right": 0.92, "camera_index": 0}


class Preferences:
    def __init__(self, path=None):
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local" / "share"))
        self.path = Path(path) if path else base / "GestureDefender" / "settings.json"
        self.values = DEFAULTS.copy()
        self.error = ""
        try:
            saved = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(saved, dict):
                return
            for key in ("reduced_motion", "muted", "low_resolution"):
                if type(saved.get(key)) is bool:
                    self.values[key] = saved[key]
            for key, low, high in (("volume", 0, 1), ("sensitivity", 0.5, 2),
                                    ("range_left", 0, 0.8), ("range_right", 0.2, 1)):
                value = saved.get(key)
                if type(value) in (int, float) and low <= value <= high:
                    self.values[key] = value
            if self.values["range_right"] - self.values["range_left"] < 0.2:
                self.values["range_left"], self.values["range_right"] = 0.08, 0.92
            if type(saved.get("camera_index")) is int and 0 <= saved["camera_index"] <= 9:
                self.values["camera_index"] = saved["camera_index"]
        except (OSError, ValueError):
            pass

    def save(self):
        temporary = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=self.path.parent,
                                             delete=False, suffix=".tmp") as output:
                temporary = Path(output.name)
                json.dump(self.values, output)
            temporary.replace(self.path)
            self.error = ""
        except OSError:
            self.error = "Settings could not be saved."
        finally:
            if temporary:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    pass
