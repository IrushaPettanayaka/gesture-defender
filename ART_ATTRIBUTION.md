# Cartoon space UI - reference and provenance

**Designed by vectorpouch / Freepik** — https://www.freepik.com

The user supplied `graphic-user-interface-space-adventure-game.zip`, containing
`2377.jpg`, `2377.eps`, `License free.txt` and `License premium.txt`, as the visual
reference for Gesture Defender's 1.3 redesign. The JPG was visually inspected.
The EPS is an Adobe Illustrator EPSF 3.0 document with an 800 x 400 bounding box;
no EPS/vector-export tool was available in the working environment.

Both supplied license texts were read. Premium entitlement is **not** assumed.
The free license requires the credit above. It allows application/design use
subject to its terms and prohibits reselling, sublicensing, renting or placing
the artwork in archives/databases. Its linked full terms take precedence:
https://www.freepik.com/terms_of_use

The linked terms could not be retrieved by the browsing tool during this task
(the link redirected to an inaccessible endpoint). The statements above describe
the supplied license text, not an independent clearance of redistribution rights.

The supplied source files stay in the ignored local `artifacts/reference-space`
folder. They are not copied into `art`, version control, the portable ZIP, or
the Windows installer. Do not publish that folder or the original ZIP.

## Runtime artwork

`space_art.py` contains original Pygame geometry for individual planets, a rocket,
a saucer, asteroids, curved skins and gradients. `ui_components.py` draws live
button labels, dimensional text and icons. `arena_view.py` draws combat objects
directly in viewport coordinates. No JPG crops, source EPS paths or baked-in
reference labels are included. This follows the requested procedural-recreation
fallback and takes the supplied artwork's colors and visual direction as reference.

The attribution is visible on the main menu and included in the bundled notices.
All illustrations and skins are reproducible from Python source at runtime;
bounded caches retain generated transparent surfaces. No image preparation
software, network access, Blender or additional dependency is needed.
Pygame's locally bundled font supplies all live text.

To reproduce review screenshots, run:

```powershell
.\.venv\Scripts\python.exe tools\render_preview.py
```

Only synthetic camera previews are saved by that tool. Gameplay never records
camera images. Screenshots are verification artifacts rather than runtime assets.
