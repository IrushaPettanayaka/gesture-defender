# Install and distribute Gesture Defender

Gesture Defender is a Windows 11 x64 desktop game. Deploying it means distributing
the installer or portable folder; it does not need a web server, domain or database.
GitHub Pages cannot run this Python/Pygame desktop application in a browser.

## Install version 1.3.0

1. Sign in to GitHub and open
   https://github.com/IrushaPettanayaka/gesture-defender/releases/tag/v1.3.0.
2. Under **Assets**, download `GestureDefender-1.3.0-Setup.exe`.
3. Run the installer, then open **Gesture Defender** from the Start menu.
4. Choose **Play**, then **Set up camera** or **Play with keyboard**.
   In camera mode, keep your face and one full hand visible, calibrate if needed,
   then choose **Start Game**. Q exits.

Alternatively, download `GestureDefender-1.3.0-Windows-x64.zip`, extract the entire
ZIP into a folder, and run `GestureDefender.exe`. Keep `_internal` beside it.
The automatically generated **Source code** downloads are developer sources,
not the ready-to-run Windows game. Players need no Python installation or internet
connection after downloading the Windows package.

Optional integrity check in the download folder:

```powershell
Get-FileHash .\GestureDefender-1.3.0-Setup.exe -Algorithm SHA256
```

Compare the value with the matching filename in `SHA256SUMS-1.3.0.txt` from the release.

## Access and sharing

This repository is private. A release link is accessible only to GitHub accounts
with repository access. Invite trusted collaborators using the repository's
**Settings -> Collaborators** controls, or share the installer/portable ZIP directly
with your intended players. Uploading a release does not make the repository public.
Changing repository visibility is a separate decision.

Preserve the included notices and attribution. The supplied Freepik reference ZIP,
`2377.jpg` and `2377.eps` must not be uploaded or redistributed. The game's original
procedural artwork and attribution are included in the Windows package.

## Windows security and verification limits

The app and installer are unsigned. Windows can block unfamiliar executable or
native-library files. Do not disable antivirus or Smart App Control as an install
requirement; a trusted/signed distribution or security-policy review may be needed.

Version 1.3 passed 66 tests, 23 source UI-flow checks, the same UI checks in portable
and installed builds, and source/packaged model and camera startup checks. An initial
test-uninstaller policy block cleared on an ordinary retry; the final install/UI/
uninstall test passed. Human gesture accuracy, physical device switching,
multi-monitor DPI changes and clean second-PC acceptance remain manual checks.
See HANDOFF.md for details. No camera images were saved by diagnostics.

## Publish a future version

1. Update the version in `build_exe.py`, `packaging/installer.iss`,
   `packaging/version.txt`, `tools/verify_release.py` and the documentation.
2. From the project folder, validate and build:

   ```powershell
   .\.venv\Scripts\python.exe -m unittest discover -s tests -v
   .\.venv\Scripts\python.exe -m pip check
   .\.venv\Scripts\python.exe main.py --verify-ui artifacts\source-ui
   .\.venv\Scripts\python.exe build_exe.py --installer
   .\dist\GestureDefender\GestureDefender.exe --verify-ui artifacts\packaged-ui
   ```

   The build requires the existing virtual environment, tracking models and Inno
   Setup; see README.md for setup. Verify the real camera and installer as well.
3. Commit and push the intended source changes. Keep `.venv`, `artifacts`, model
   downloads, `dist`, `release` and restricted reference artwork out of Git commits.
4. On GitHub, open **Releases -> Draft a new release**. Create a new version tag
   at the tested source commit, give the release a title and describe changes and
   known limitations.
5. Upload that version's installer, portable ZIP and SHA-256 file from `release`.
   Check the uploaded names and sizes, then publish the release.
6. Download/install the release as a player and check its startup. Share the release
   URL with people who have access, or distribute the Windows files directly.

Releases do not automatically update copies already installed on players' PCs.
Players download and install a newer release when it is available.
