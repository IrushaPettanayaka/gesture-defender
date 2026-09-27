# Gesture Defender 1.1.0 - release handoff

Source repository: https://github.com/IrushaPettanayaka/gesture-defender (private).

## Implemented

Retained Python/Pygame/OpenCV/MediaPipe and procedural assets. Added fist shield
(0.35-second hold, 2-second duration, 8-second cooldown after expiry), palm-center
steering during fists, keyboard shield, armored/zigzag enemies, hit feedback,
timed combo multipliers and every-fifth-wave bosses with warned lance/fan attacks.

Added unified camera setup with live preview, immediate camera selection, saved
calibration, heuristic feedback and keyboard fallback. Switching waits for the
old camera worker to exit. Input expires after 0.20 seconds independently of the
0.65-second pause grace. Restart clears combat, gesture holds and steering offsets.

Fists use MediaPipe world-coordinate finger bends/reach with a 2D fallback and
hysteresis for uncertain fingertips. Movement still uses mirrored image positions.
The gesture verification window waits for Space before its 30-second timer begins.

Startup import/runtime failures now have rotating logs and a windowed error dialog.
Tracking errors are logged and remain recoverable in the UI. OS-level blocks that
happen before Python starts cannot be caught by application logging.

## Launch investigation and actual verification

The previous handoff recorded Windows Application Control blocking an unsigned
executable/native library (error 4551). Before this update, the old packaged game
launched and initialized both models successfully. That historical launch failure
could not be reproduced; it is not claimed to be a code bug fixed by this update.
No Windows security policy was modified or bypassed.

- **45 automated tests pass:** simulation/input/persistence plus fist holds,
  rearm/conflicts, jitter and 3D rotation/projection; shield timers; stale firing;
  armor health; zigzag bounds; combos; boss scheduling/patterns/scoring;
  paused timers; restart; camera switching; startup reporting.
- Dependency check: no broken requirements. Python syntax compilation passed.
  No separate static type checker is configured in this project.
- Synthetic-only visual review: setup/error, enemy variety, shield/combo HUD and
  both boss warnings. No webcam images saved.
- **Real source camera controls:** one live run recorded 792 face frames, 607 hand
  frames, 16 pinch-driven shots, two palm state transitions and a 0.412 normalized
  steering span. Other runs also registered movement/shots/palm transitions.
- **Portable 1.1.0:** actual keyboard window smoke exited 0; frozen diagnostics
  loaded both bundled models and ran inference; ZIP CRC and required assets passed.
- **Installed 1.1.0:** silent per-user installation exited 0. Installed executable
  hash matched the build. Keyboard window smoke exited 0. Both models loaded;
  actual 640 x 480 camera capture and face detection passed; worker stopped cleanly.
  Executables were launched with `C:\Windows` as their working directory.
- The first automated test-uninstaller launch was blocked with Windows error 4551.
  Retrying that same uninstaller directly from Windows succeeded with exit 0.
  This is an intermittent policy result, not proof that every unsigned build will
  be permitted. Prefer the portable ZIP if local installation policy interferes.

## Remaining human/hardware checks

**The final 3D fist shield has not been verified with a person.** Early tests did
not sustain a detected fist for the hold duration. The user missed the focused
pose prompt, so those aggregate measurements were not a valid fist test. A later
packaged verification attempt never started its timer; the user chose to finish
and test later. Do not count these attempts as successful packaged gesture tests.

Run from the extracted release directory:

```powershell
.\GestureDefender.exe --verify-controls live-controls.json
```

The window waits up to two minutes for Space with face and hand visible. Then test
fist first while running, move left/right, pinch, palm-pause, relax and palm-resume.
The report contains metadata-only action counts/ranges, never images. Check the
feel of mirrored movement/calibration and shield rearm/cooldown as well.

Camera disconnect/reconnect and switching between multiple physical cameras,
extended balance, audible sound quality, installer wizard interaction and a clean
second-PC installation remain manual checks. Mocked switching tests cannot prove
every native driver. Native driver hangs use bounded joins then process exit.
The release is unsigned and targets Windows 11 x64.

## Deliverables and rebuild

- `release/GestureDefender-1.1.0-Setup.exe`
- `release/GestureDefender-1.1.0-Windows-x64.zip`
- `release/SHA256SUMS-1.1.0.txt`
- README with installation, controls, VS Code/source setup and troubleshooting.
- Source and commit history pushed to the user-requested private GitHub repository.
  Environments, model downloads, local diagnostics and binaries stay out of Git.

```powershell
.\.venv\Scripts\python.exe main.py
.\.venv\Scripts\python.exe main.py --webcam
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe build_exe.py --installer
```

Use the pinned `requirements.lock`. Inno Setup 6.7.3 ISCC must be on PATH or at
`.tools/innosetup/ISCC.exe`. PyInstaller 6.22.0 bundles models, dependencies and
notices. No public publication or GitHub release upload was requested.
