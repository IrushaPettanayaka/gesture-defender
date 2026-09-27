"""One-time model download. The game itself never accesses the network."""

from pathlib import Path
import urllib.request

MODELS = {
    "face_landmarker.task": "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task",
    "hand_landmarker.task": "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task",
}


def main():
    directory = Path(__file__).resolve().parent / "models"
    directory.mkdir(exist_ok=True)
    for name, url in MODELS.items():
        destination = directory / name
        if destination.is_file():
            print(f"Already installed: {name}")
            continue
        temporary = destination.with_suffix(".download")
        print(f"Downloading {name} from Google...", flush=True)
        try:
            with urllib.request.urlopen(url, timeout=60) as response:
                with temporary.open("wb") as output:
                    while chunk := response.read(1024 * 256):
                        output.write(chunk)
            temporary.replace(destination)
        finally:
            temporary.unlink(missing_ok=True)
    print("Models ready. Run: python main.py")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as error:
        raise SystemExit(f"Model download failed: {error}. Check your connection and retry.")
