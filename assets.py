"""Locate bundled models without relying on the terminal's working directory."""

from pathlib import Path
import sys

ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))


def model_path(name):
    path = ROOT / "models" / name
    if not path.is_file():
        raise RuntimeError("Tracking models are missing. Run: python download_models.py")
    return path
