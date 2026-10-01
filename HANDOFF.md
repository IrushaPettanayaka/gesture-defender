# Gesture Defender 1.3.0 - cartoon space UI handoff

## Changes

The reference artwork was inspected before implementation. Version 1.3 replaces
1.2's minimal navy style with an indigo/purple illustrated space interface:
curved glossy orange buttons, cyan controls, lavender pause controls, luminous
blue panels, dimensional live lettering, planets, a saucer and a rocket.

All application code remains Python/Pygame/OpenCV/MediaPipe. No new dependency,
Blender, network runtime asset loading, image recording or upload was introduced.
`space_art.py` creates original transparent procedural illustrations and caches
skins, preview masks and gradients. `ui_components.py` owns live text and reusable
buttons/panels/meters/icons. The camera frame clips the preview to curved corners.
`arena_view.py` draws projected world positions with native-size text/strokes,
removing the earlier world-bitmap stretch while preserving simulation/hitboxes.

The menu, mode selection, setup, calibration, gameplay, pause, results, controls
and settings all share the theme. Combat rules and tracking thresholds are
unchanged. H hides only the preview; K releases camera ownership and selects the
keyboard. Timers freeze while paused; recovery/settings never auto-resume. No
currency/reward/shop systems were added. HUD and result values use real state.

Mouse buttons activate on release over the original enabled control. Dragging
away or changing scenes cancels a pending press. Focus, hover, pressed and disabled
states are visible. Reduced motion removes decorative bobbing and transitions.

## Reference rights and offline assets

Designed by vectorpouch / Freepik — https://www.freepik.com

Both supplied license files were read; premium rights are not assumed. The JPG
was visually inspected and EPS metadata inspected. No EPS extraction tool was
available, so original procedural recreation was used as requested. Reference
JPG/EPS/license files remain in ignored `artifacts/reference-space`; no reference
pixels/paths or source artwork are bundled. `ART_ATTRIBUTION.md` and bundled
notices retain attribution. Its linked online terms could not be retrieved by
the browser; no independent redistribution clearance is claimed.

## Verification

- 66 tests passed, including existing gameplay/tracking tests and new pointer
  cancellation, disabled buttons, projection and saved visual-preference tests.
- 23 native source UI-flow checks passed with a synthetic camera worker. The flow
  covers menu -> mode -> setup -> calibration/default -> play -> pause -> settings
  -> resume -> menu -> keyboard -> fullscreen/windowed -> game over/restart/exit.
  Press state and drag cancellation are exercised through actual Pygame events.
- Synthetic screenshots rendered at 1366x768, 1920x1080 and 1066x600; main menu,
  setup, play, pause, game over, boss warnings, controls and settings inspected.
  Camera corner clipping and text contrast were corrected from those reviews.
- `pip check` passed. Source keyboard smoke launch exited successfully.
- PyInstaller and Inno Setup production builds completed. All 23 UI-flow checks
  also passed in the packaged executable, launched from C:\Windows. Packaged menu,
  setup and gameplay screenshots were inspected. Offline procedural art and the
  bundled Pygame font loaded correctly.
- Both source and packaged model/camera diagnostics passed: face/hand models
  initialized, a 640x480 RGB camera frame was received and the worker stopped.
  The source check observed a face but no hand; the packaged check observed neither.
  These startup checks do not verify human gesture actions or accuracy.
- Installer deployment and matching executable/document checks passed. Windows
  App Control initially blocked the test uninstaller; one ordinary retry of the
  same uninstaller succeeded and removed the temporary installed executable.
  No security settings were changed. Earlier 1.2 runtime blocks did not recur in
  these 1.3 source/packaged startup checks, but the unsigned release can still be
  blocked by Windows policy on this or another machine.
- ZIP integrity, bundled font/models/attribution and SHA-256 checks passed.
  The supplied reference artwork/license files are excluded. Standard dependency
  assets (including Python's base_library.zip and Tk's own logos) remain bundled.

Evidence: `artifacts/ui-1.3-tests.log`, `artifacts/source-ui-1.3/report.json`,
`artifacts/packaged-ui-1.3/report.json`, `artifacts/ui-1.3/`,
`artifacts/release-1.3-build.log`, `artifacts/source-camera-1.3.json`,
`artifacts/packaged-camera-1.3.json`, `artifacts/archive-1.3.json`,
`artifacts/ui-1.3-installer-verification.json` and `artifacts/ui-1.3-uninstall-retry.json`.
All captured camera previews are synthetic and labelled; no real camera images
were saved. Gallery scores are samples, not claims about a live run.

## Run/build

```powershell
.\.venv\Scripts\python.exe main.py
.\.venv\Scripts\python.exe main.py --verify-ui artifacts\source-ui-1.3
.\.venv\Scripts\python.exe tools\render_preview.py
.\.venv\Scripts\python.exe build_exe.py --installer
```

Outputs are `release/GestureDefender-1.3.0-Setup.exe`,
`release/GestureDefender-1.3.0-Windows-x64.zip` and
`release/SHA256SUMS-1.3.0.txt`. Earlier release files remain available.
This is an unsigned Windows distribution. The redesign was initially verified
locally; the user subsequently authorized committing/uploading the project and
publishing version 1.3.0 to the existing private GitHub repository. See DEPLOYMENT.md.

## Remaining manual checks

Actual webcam gesture feel/accuracy (especially fist), physical camera switching
or disconnection, audio playback, clean second-PC installation and changing actual
Windows display scaling between monitors require manual acceptance. The native
window test exercises fullscreen, resizing/minimum-size enforcement and letterbox
mapping; it does not change Windows DPI settings. No Windows security settings
were changed to enable verification.
