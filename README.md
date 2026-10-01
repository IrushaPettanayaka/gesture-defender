# Gesture Defender 1.3.0

> **AI-assisted project disclosure:** Approximately **95% of the implementation
> was done by OpenAI Codex**, with ChatGPT assistance. I directed the project,
> tested the game, and made small edits using my current Python knowledge.
> I did not write the main implementation from scratch. The 95% figure is my
> estimate, not a measured breakdown of individual lines of code.

A Windows 11 x64 arcade game built with Python, Pygame, OpenCV and MediaPipe.
Source: [IrushaPettanayaka/gesture-defender](https://github.com/IrushaPettanayaka/gesture-defender) (private).
All tracking runs locally. No camera images are recorded or uploaded.

## Install and play

Download the Windows installer or portable ZIP from the
[1.3.0 release](https://github.com/IrushaPettanayaka/gesture-defender/releases/tag/v1.3.0).
The repository is private, so sign in with an account that has access.
See [DEPLOYMENT.md](DEPLOYMENT.md) for installation, sharing and future releases.

- `release/GestureDefender-1.3.0-Setup.exe`: per-user installer, Start Menu shortcut,
  optional desktop shortcut and uninstaller.
- `release/GestureDefender-1.3.0-Windows-x64.zip`: extract the entire folder, then
  run `GestureDefender.exe`. Keep `_internal` beside it.
- `release/SHA256SUMS-1.3.0.txt`: checksums for the release downloads.

End users do not need Python, developer tools, a server or an internet connection.
The installer defaults to `%LOCALAPPDATA%\Programs\Gesture Defender`.
Settings, best score and rotating startup logs live in
`%LOCALAPPDATA%\GestureDefender`; uninstall retains this user data.

The game opens at the **main menu with the camera off**. Choose **Play**, then
**Set up camera** or **Play with keyboard**. Q exits.
This is an unsigned Windows build; Windows policy may require approval. See the
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
| Escape | Pause/resume during play; back from menus/settings |
| R | Restart, clearing combat and gesture state |
| K | Switch keyboard/webcam mode; keyboard mode stops the camera |
| Tab / Shift+Tab / menu arrows | Move visible button focus |
| Enter | Activate the focused enabled button |
| H | Hide/show preview while tracking continues |
| F2 | Toggle FPS and detailed tracking landmarks |
| F11 | Toggle fullscreen/windowed |
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

1. Choose Play, then Set up camera (or press K). Camera selection, mirrored live preview, face/hand status, calibration
   and Start are on the same screen. [ / ] or the buttons select indices 0-9.
2. Keep your face and one complete hand visible. Detection is local. Frame-edge,
   apparent size and landmark-jump hints are labelled **Hint**: they are measured
   heuristics, not confidence percentages or diagnoses of a detection failure.
3. Click Recalibrate (C). Hold your index finger at a comfortable left edge for two
   seconds, then at your right edge. A range that is too narrow is rejected.
   Use default range cancels calibration and selects defaults. Previously saved calibration
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
| Gold armored enemy | Wave 2 onward | Slower, remaining health shown | 3 | 75 |
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
  happens before Python can report it. Previous 1.2.0 verification encountered an
  executable block and a blocked `_image` DLL in the MediaPipe import chain. See
  HANDOFF.md for the current release's results. Have the security-policy owner
  review a block rather than changing camera permissions or disabling protections.
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

`main.py` handles entry and startup reporting; `app.py` owns window events;
`session.py` owns navigation, input guards and camera lifecycle; `game.py` owns combat; `controls.py`/`gestures.py` interpret input;
`calibration.py` measures range; `tracking.py`, `camera.py` and face/hand wrappers
own capture/inference; `ui.py` draws screens; `ui_components.py` supplies shared styles/navigation;
`arena_view.py` projects unchanged combat positions/hitboxes and draws native-size details;
`space_art.py` generates cached original cartoon illustrations and component skins;
`effects.py` draws procedural graphics; audio/settings/scores are separate.
Application source is Python; the installer uses an Inno Setup packaging script.

A worker publishes only its latest result, avoiding a growing frame queue. RGB
conversion and horizontal mirroring precede MediaPipe and preview display. The UI targets 60 FPS; F2 shows actual performance. Simulation uses elapsed
time with small substeps. Normal exit releases camera/models. A native driver hang
has a bounded worker join, with process exit as a final fallback.

The game requests no microphone, has no accounts, analytics, image recording or
uploading. Saved data is settings, score, logs and opt-in metadata reports.
See `THIRD_PARTY_NOTICES.md` for bundled dependency/model licenses and `HANDOFF.md`
for verification results and explicitly untested hardware behavior.

## Cartoon space UI, accessibility and verification (1.3)

The UI follows the supplied vectorpouch / Freepik space-game reference: indigo and
purple space, illustrated planets/rocket/saucer, dimensional cyan/lavender lettering,
curved glossy orange primary buttons and luminous blue panels. Text remains live.
Each screen uses separate interactive components; no reference-sheet backdrop or
JPG crops are used. Gameplay has quieter decoration and explicit shield meters.

**Designed by vectorpouch / Freepik** — https://www.freepik.com

See `ART_ATTRIBUTION.md` for the supplied free-license requirements and provenance.
No premium rights are assumed. The original JPG, EPS and pack are kept outside
the repository/distribution in ignored local reference artifacts. Runtime artwork
is generated from original Python geometry with bounded caches; it works offline.

The main menu shows the real saved best score. The game-over screen labels New Best
only when the run beats the record from its start. Pause distinguishes user/focus
and tracking-loss causes, offers Resume/Recalibrate/Settings/Main Menu, and never
resumes simply because tracking recovered or Settings closed.

The gameplay HUD places score/combo on the left, wave/boss health in the centre,
and lives/shield state on the right. The preview sits below the playfield; it never
covers collision space. H hides only the preview. Use K or the explicit Keyboard
mode button to stop camera tracking. F2 exposes FPS and detailed landmarks.

Buttons brighten on hover and compress while pressed. Mouse activation occurs on
release over the same enabled button; dragging away cancels. Buttons have visible
mouse/keyboard focus and disabled states. Tab, Shift+Tab and
menu arrow keys move focus; Enter activates it. Space used to resume and menu
clicks cannot also fire: release held fire/gestures before playing. Status guidance
uses a short stability delay; readiness still follows current tracking immediately.

The UI uses a 1366 x 768 logical canvas and scales/letterboxes both drawing and
mouse hit tests. Window size is at least 1066 x 600 and starts within the desktop.
F11 switches fullscreen; display, preview, volume, mute, sensitivity and reduced
motion settings persist. SDL per-monitor DPI awareness is requested before video
initialization. Pygame's packaged default font, icons and procedural assets work
offline; no new styling dependency or downloaded art is required.

```powershell
.\.venv\Scripts\python.exe main.py --verify-ui artifacts\ui-flow
.\.venv\Scripts\python.exe tools\render_preview.py
```

`--verify-ui` also works in the executable. It exercises the actual window/event
loop with a **synthetic camera worker**, covering menus, setup, calibration cancel,
play/pause/restart, hiding preview, keyboard fallback, fullscreen and minimum size.
It writes a JSON report and synthetic screenshots. It does not prove webcam gesture
accuracy and never opens a real camera. Normal gameplay never saves screenshots.
The render tool creates a synthetic gallery at 1366 x 768, 1920 x 1080 and 1066 x 600.
Actual DPI settings are not changed by these tests; a second-monitor scale change
still needs a manual check. See HANDOFF.md for exact source/packaged results.
