# Optional future asset pass

Current release uses original procedural Pygame geometry and synthesized sound.
Blender was not used, and no imported 3D assets are required. Keep the current
renderer as the fallback if a future native 3D renderer is introduced.

For a future Astra/Blender pass: player_ship, enemy_scout, asteroid, shield_pickup.
Use 1 unit as the player hull length, +Y forward, +Z up, origin at collision center.
Budgets: 1,500 triangles/player, 800/enemy, 300/asteroid, 200/pickup. Colors: dark
navy, cyan player, coral enemies. Avoid transparent textures and heavy materials.
Optional clips: engine_idle (loop), bank_left/right (0.2 s), damage_flash (0.15 s).
Export individual GLB files with transforms applied and no external textures;
retain `.blend` sources and reproducible generation scripts. No runtime Blender
dependency. This optional work is not part of the current packaged release.
