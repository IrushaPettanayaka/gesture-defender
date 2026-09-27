"""Atomic, best-effort best-score storage in the local user's data directory."""
import json
import os
from pathlib import Path
import tempfile


class ScoreStore:
    def __init__(self, path=None):
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local" / "share"))
        self.path = Path(path) if path is not None else base / "GestureDefender" / "best.json"
        self.error = ""
        self.best = self.load()

    def load(self):
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))["best"]
            return value if type(value) is int and 0 <= value <= 2_000_000_000 else 0
        except (OSError, ValueError, KeyError, TypeError):
            return 0

    def save(self, score):
        if score <= self.best:
            return True
        temporary = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".tmp",
                                             dir=self.path.parent, delete=False) as output:
                temporary = Path(output.name)
                json.dump({"best": int(score)}, output)
            temporary.replace(self.path)
            self.best, self.error = int(score), ""
            return True
        except OSError:
            self.error = "Best score could not be saved (folder not writable)."
            return False
        finally:
            if temporary is not None:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    pass
