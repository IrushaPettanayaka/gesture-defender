# Third-party notices

Gesture Defender includes unmodified third-party runtime libraries and pretrained
models. Their original license and notice texts are collected from the installed
distributions into `_internal/notices` in the Windows build. Python's license is
included there too. This project was implemented with Codex assistance.

Principal dependencies: Python (PSF license), Pygame/SDL (see their LGPL and other
component notices), OpenCV contrib (Apache-2.0 and bundled component licenses),
MediaPipe (Apache-2.0), NumPy (BSD and bundled component notices), Pillow and the
other dependency licenses retained in the notices directory. Pygame's bundled font
is used; no fonts are fetched at runtime. PyInstaller's bootloader is distributed
under its license with the exception for generated applications.

Official MediaPipe model sources, downloaded without modification:

- https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task
- https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task
- MediaPipe repository/license: https://github.com/google-ai-edge/mediapipe
- Model documentation: https://ai.google.dev/edge/mediapipe/solutions/vision/face_landmarker
- Model documentation: https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker
- Terms: https://ai.google.dev/edge/mediapipe/legal/tos

The application makes no runtime network requests. No third party endorses this
game. The local installer is unsigned; it is not a signed public release.
