# Gesture Defender 1.1.0 - release handoff

## Delivered changes

Retained Python/Pygame/OpenCV/MediaPipe and procedural assets. Added fist shield
(0.35-second hold, 2-second duration, 8-second post-expiry cooldown), palm-center
steering during fists, keyboard shield, armored/zigzag enemies, hit feedback,
timed combo multipliers and every-fifth-wave bosses with warned lance/fan attacks.

Added unified camera setup with live preview, immediate camera selection, saved
calibration, heuristic feedback and keyboard fallback. Camera switching waits for
the old worker to exit. Tracking input expires after 0.20 seconds independently
of the 0.65-second pause grace. Restart clears gesture offsets/holds and combat.

Added rotating startup logs and windowed error dialogs. Import failures are caught
by the entry point; tracking errors remain recoverable in the UI. OS blocks that
happen before Python starts cannot be caught by application logging.

## Launch investigation

The previous handoff recorded Windows Application Control blocking the unsigned
executable and a native library (error 4551). Before editing this update, the old
packaged executable launched successfully (120-frame keyboard smoke, exit 0),
and its two bundled models loaded successfully (frozen diagnostic, exit 0).
The historical block could not be reproduced; it is not represented as a code bug
that this update fixed. No security policy was modified or bypassed.

## Source verification completed

- 45 automated tests pass: prior simulation/input/persistence checks plus shield
  hold/rearm/conflicts/steering, stale firing, armor health, bounded zigzag motion,
  combos, boss scheduling/patterns/scoring, frozen timers, restart cleanup, camera
  switching and startup error reporting.
- `pip check`: no broken requirements.
- Synthetic-only UI renders reviewed for setup/error, enemy variety, shield,
  combo HUD and both boss warnings. No webcam frames saved.
- Baseline packaged keyboard launch and actual bundled model initialization pass.

Final 1.1.0 build/installed runtime results are recorded below after verification.

## User-deferred and external checks

Real webcam checks have confirmed movement, pinch shots and palm pause/resume.
The fist check is still being completed. Run:

```powershell
.\GestureDefender.exe --verify-controls live-controls.json
```

The 30-second window records metadata-only counts for actual camera-driven
movement/shots/palm transitions/shields. Move, pinch, palm-pause, relax then
palm-resume, and fist-shield. Also check calibration comfort, mirrored direction,
loss/resume behavior, disconnect/reconnect, and switching available real cameras.
Mocked switching tests cannot validate every native camera driver.

Extended play balance, audible sound quality, installer wizard interaction and a
clean second-PC install remain manual acceptance checks. The release is unsigned.
The pinned build uses Windows 11 x64 / Python 3.13.14. Source is being pushed to the user-requested private GitHub repository.
Native camera-driver hangs use bounded joins followed by process shutdown.

## Files and rebuild

- `release/GestureDefender-1.1.0-Setup.exe`
- `release/GestureDefender-1.1.0-Windows-x64.zip`
- `release/SHA256SUMS-1.1.0.txt`
- README: source/VS Code setup, controls, privacy, build and diagnostics.

```powershell
.\.venv\Scripts\python.exe main.py
.\.venv\Scripts\python.exe main.py --webcam
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe build_exe.py --installer
```

Inno Setup 6.7.3 ISCC must be on PATH or `.tools/innosetup/ISCC.exe`. Dependencies,
models, generated builds and local diagnostics remain ignored by Git. Existing unrelated changes are preserved. The user requested repository creation and commits.
