"""Best-effort rotating startup/crash logs for source and windowed releases."""
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import sys


def configure():
    folder = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "GestureDefender" / "logs"
    try:
        folder.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(folder / "startup.log", maxBytes=250_000, backupCount=2, encoding="utf-8")
        logging.basicConfig(level=logging.INFO, handlers=[handler],
                            format="%(asctime)s %(levelname)s %(message)s", force=True)
        logging.info("Start frozen=%s executable=%s cwd=%s", getattr(sys, "frozen", False), sys.executable, Path.cwd())
        return folder / "startup.log"
    except OSError:
        return None


def report_failure(log_path):
    logging.exception("Application failed")
    message = "Gesture Defender could not start."
    if log_path:
        message += f"\nDetails: {log_path}"
    if sys.stderr is not None:
        print(message, file=sys.stderr)
    if getattr(sys, "frozen", False) and os.name == "nt":
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, message, "Gesture Defender startup error", 0x10)
