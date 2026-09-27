# Gesture Defender 1.1.0

A Windows 11 x64 arcade game built with Python, Pygame, OpenCV and MediaPipe.
All tracking runs locally. No camera images are recorded or uploaded.

## Install and play

- `release/GestureDefender-1.1.0-Setup.exe`: per-user installer, Start Menu shortcut,
  optional desktop shortcut and uninstaller.
- `release/GestureDefender-1.1.0-Windows-x64.zip`: extract the entire folder, then
  run `GestureDefender.exe`. Keep `_internal` beside it.
- `release/SHA256SUMS-1.1.0.txt`: checksums for the release downloads.

End users do not need Python, developer tools, a server or an internet connection.
The installer defaults to `%LOCALAPPDATA%\Programs\Gesture Defender`.
Settings, best score and rotating startup logs live in
`%LOCALAPPDATA%\GestureDefender`; uninstall retains this user data.

The game opens in **keyboard mode with the camera off**. Press **K** or click
**Switch input** to open camera setup. Space starts play. Q exits.
This is an unsigned local build; Windows policy may require approval. See the
handoff for the actual package checks and remaining hardware checks.

## Controls

| Input | Action |
| --- | --- |
| Arrows / A-D | Move horizontally (also available in webcam mode) |
| Space | Start/resume; hold during play to fire |
| Index fingertip | Steer in webcam mode |
| Hold thumb/index pinch | Fire; separate fingers to stop |
| Hold open palm for 0.65 seconds | Start/pause/resume; relax before repeating |
| Hold fist for 0.35 seconds | Activate shield; open hand before reusing |
| S / Shift | Activate shield with keyboard |
| P | Pause/resume |
| Escape | Pause/exit menu |
| R | Restart, clearing combat and gesture state |
| K / Tab | Switch keyboard/webcam mode |
| F1 | Settings |
| Q / close button | Quit |

Fist detection uses MediaPipe 3D finger bends, with a 2D fallback, and takes priority over pinch and palm. While making a fist, palm-center
steering preserves the current position with an offset, then smoothly returns to
index-finger steering when you open your hand. The shield lasts **2 seconds**.
Its **8-second cooldown starts when the shield ends**. Holding a fist cannot
reactivate it. Pause freezes both timers.

Settings shortcuts: M mute, V volume, E reduced motion, L lower tracking resolution,
[ / ] camera index, - / + sensitivity, C recalibrate, T retry camera.
Camera and resolution changes apply immediately after the old worker releases its
camera. A stalled camera driver cannot start a second overlapping capture worker.

## Camera setup

1. Press K. Camera selection, mirrored live preview, face/hand status, calibration
   and Start are on the same screen. [ / ] or the buttons select indices 0-9.
2. Keep your face and one complete hand visible. Detection is local. Frame-edge,
   apparent size and landmark-jump hints are labelled **Hint**: they are measured
   heuristics, not confidence percentages or diagnoses of a detection failure.
3. Click Calibrate (C). Hold your index finger at a comfortable left edge for two
   seconds, then at your right edge. A range that is too narrow is rejected.
   Enter cancels calibration and selects defaults. Previously saved calibration
   can be used directly.
4. Click Start or press Space once face and hand are detected. An open palm also
   starts play. Start waits until calibration is complete or cancelled.

Settings and calibration save on normal exit. Recalibration is always available.
Camera errors leave Retry, camera selection and Keyboard mode accessible.
After tracking loss, relax your hand before repeating a gesture. Movement and
firing stop when a result is missing or older than **0.20 seconds**. Loss lasting
more than **0.65 seconds** pauses play; recovery requires explicit resume. Focus
loss also pauses. Keyboard mode works without tracking models or camera access.

## Enemies, scoring and boss waves

Three lives; damage gives 1.2 seconds of invulnerability. Shields block damage.

| Enemy | Appears | Behavior | Health | Destruction points |
| --- | --- | --- | --- | --- |
| Coral asteroid | Wave 1 onward | Straight fall | 1 | 25 |
| Gold armored square | Wave 2 onward | Slower, remaining health shown | 3 | 75 |
| Purple zigzag diamond | Wave 3 onward | Faster, smooth predictable side-to-side motion | 1 | 40 |
| Boss | Every fifth wave | Alternating warned lance lanes and fan shots | 20 initially; +8 per boss, capped at 60 | 500 |

Successful bullet hits within **2 seconds** build a streak. The multiplier is
`min(4, 1 + hits // 5)`: hits 1-4 give 1x, 5-9 give 2x, 10-14 give 3x, 15+ give 4x.
Each successful hit refreshes the timer. Destruction uses the multiplier after
that hit and is awarded once per enemy. Taking damage or timer expiry resets the
streak. Pause freezes the combo timer. Dodging a falling enemy gives 10 points,
without a multiplier. Best score saves at game over, restart and clean exit.

Normal waves last 20 seconds. Speed caps at 250 pixels/second for normal enemies,
162.5 for armored and 312.5 for zigzag. Spawn interval bottoms out at 0.28 seconds;
close entry clusters are skipped. Boss fights suspend normal spawning and remove
remaining falling enemies. Every attack has a 1.2-second visible warning, followed
by openings to counterattack. Boss defeat clears hazards and advances once.

Hit flashes, bounded short particles and shaded procedural graphics use Pygame.
Reduced-motion mode removes particles and banking and simplifies ship effects.
All shield/combo/boss timers freeze on pause; restart clears combat state.

## Source setup in VS Code / PowerShell

Tested environment: Windows x64, Python 3.13.14, Pygame 2.6.1, MediaPipe Tasks
0.10.32, OpenCV contrib 4.13.0.92, NumPy 2.5.2. `requirements.lock` pins the whole
runtime/build environment; `requirements.txt` contains direct runtime dependencies.

```powershell
cd "C:\path\to\PYTHON GAME W OPENCV"
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
.\.venv\Scripts\python.exe download_models.py
.\.venv\Scripts\python.exe main.py
```

In VS Code, use **Python: Select Interpreter** and choose
`.venv\Scripts\python.exe`, then run `main.py`. Explicit interpreter paths work
without activating the environment. Launch with `--webcam` or `--camera 1` for
camera setup directly, or `--keyboard` for keyboard mode.
Install only `opencv-contrib-python`, which supplies `cv2`; do not also install
`opencv-python` into this environment.

## Build and verify

Install official Inno Setup 6.7.3, with ISCC on PATH or the portable compiler at
`.tools\innosetup\ISCC.exe`. The build uses PyInstaller 6.22.0.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe build_exe.py --installer
```

The build bundles both tracking models, native dependencies, icon, fonts and
license notices; creates a ZIP; compiles the installer; writes SHA-256 checksums.
Omit `--installer` to produce the app folder and ZIP only. No network is used by
build/runtime; the explicit setup model downloader uses official Google URLs.

```powershell
.\.venv\Scripts\python.exe main.py --keyboard --smoke-frames 120
.\.venv\Scripts\python.exe main.py --diagnostics artifacts\models.json
.\.venv\Scripts\python.exe main.py --diagnostics artifacts\camera.json --check-camera
.\.venv\Scripts\python.exe main.py --verify-controls artifacts\live-controls.json
```

The same arguments work on `GestureDefender.exe`. Diagnostics load both models
on a synthetic image; `--check-camera` also captures a real frame, reporting only
metadata. The separate **verify-controls** window waits up to two minutes for you to press Space, then starts a 30-second check. It requires a person:
move left/right, pinch to fire, open palm to pause, relax then open palm to resume,
and hold a fist to shield. Its report counts actual webcam-driven actions and
records a normalized movement range. No images are saved. Exit 0 means the action
counts passed; exit 2 means some gestures were not observed. This does not replace
checking whether the movement feels correct and the thresholds work for your hand.
Smoke mode exits automatically and does not save preferences or scores.

## Troubleshooting

- **Startup failure:** inspect `%LOCALAPPDATA%\GestureDefender\logs\startup.log`.
  Python import/runtime failures are logged with tracebacks; windowed builds also
  show a message with the log location. Logs rotate at 250 KB with two backups.
  Tracking failures remain in the game with keyboard fallback.
- **Blocked before any log is created:** an OS-level application-control block
  happens before Python can report it. An earlier build encountered error 4551.
  That failure did not recur in baseline executable/model tests for this update.
  If it recurs, have the security-policy owner review it; do not disable protections.
- **Camera unavailable:** check shutter and desktop-camera permission, close other
  camera applications, select the proper index and use Retry. K keeps play available.
- **Hand searching:** use steady lighting and keep the full hand in view. Hints
  are heuristics; the game cannot infer an exact cause from missing landmarks.
- **Delayed controls:** try L for 424 x 318 tracking (default 640 x 480), lower
  effects with E, and close heavy applications. Old results are deliberately ignored.
- **Missing/corrupt model:** reinstall the release, or from source remove only
  the damaged model then run `download_models.py`.
- **Audio/save error:** gameplay continues without audio or saved progress. M/V
  control synthesized sound; malformed settings/scores recover to defaults.

## Architecture and privacy

`main.py` handles entry and startup reporting; `app.py` coordinates the loop and
menus; `game.py` owns combat; `controls.py`/`gestures.py` interpret input;
`calibration.py` measures range; `tracking.py`, `camera.py` and face/hand wrappers
own capture/inference; `ui.py`/`effects.py` draw; audio/settings/scores are separate.
Application source is Python; the installer uses an Inno Setup packaging script.

A worker publishes only its latest result, avoiding a growing frame queue. RGB
conversion and horizontal mirroring precede MediaPipe and preview display. The UI
targets 60 FPS; actual performance depends on hardware. Simulation uses elapsed
time with small substeps. Normal exit releases camera/models. A native driver hang
has a bounded worker join, with process exit as a final fallback.

The game requests no microphone, has no accounts, analytics, image recording or
uploading. Saved data is settings, score, logs and opt-in metadata reports.
See `THIRD_PARTY_NOTICES.md` for bundled dependency/model licenses and `HANDOFF.md`
for verification results and explicitly untested hardware behavior.
