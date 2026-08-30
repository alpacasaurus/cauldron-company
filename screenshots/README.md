# Screenshot log

Every dev capture is kept here rather than overwritten, so the visual history of
the build stays intact. New captures are written automatically by:

```bash
python tools/shot.py --label some-name --players 2 --frames 90
python tools/capture_readme_shots.py
```

Names are `YYYY-MM-DD_HHMMSS-label.png`.

## Rendering bug hunt (macOS)

macOS was the whole fight. Panda3D's default context is OpenGL 2.1 / GLSL 120,
but Ursina's stock shaders declare GLSL 130/140, so nothing drew. Forcing a
3.2+/4.1 *core* profile made the shaders legal but broke Panda3D's GUI path, so
the window stayed black either way. The fix was supplying GLSL 120 shaders
(`witches/glfix.py`) and leaving the default context alone.

| Screenshot | What it shows |
|---|---|
| `2205-offscreen-render-blank` | Panda3D offscreen buffer returns a blank frame on macOS |
| `2206-offscreen-render-blank-gameplay` | Same, with the scene loaded — offscreen capture is unusable here |
| `2207-window-id-capture-black` | `screencapture -l <window-id>` returns black for an OpenGL surface |
| `2208-black-window-core-profile-bug` | GL 4.1 core profile: shaders compile, nothing renders |
| `2209-probe-black-composited` | Composited capture confirms the black window is a real bug, not a capture artifact |
| `2210-probe-glsl120-works` | GLSL 120 on the default context: cube, sphere, text, and clear colour all draw |

## Game

| Screenshot | What it shows |
|---|---|
| `2212-title-screen` | Title screen and controls |
| `2213-gameplay-hut-offscreen` | First playable frame — camera faced away, hut behind the camera |
| `2214-gameplay-reframed` | Camera turned around, hut moved to the back of the clearing |
| `2215-gameplay-tightened` | Play area tightened so forageables stay on camera |
| `221711-gameplay-verified` | Playable look after the scripted loop test passed |
| `232630-npc-barks-verified` | NPC bark line (red) sharing the screen with an Eric subtitle |
| `001407-menu-main` | Main menu: play, how to play, quit |
| `001903-menu-play` | Witch-count screen behind Play |
| `001900-menu-controls` | How to play, with the key table as aligned columns |
| `001901-menu-pause` | Esc pause overlay dimming a live shift |
| `001902-menu-endscreen` | End-of-shift results with replay buttons |

## Recipe HUD, wider map (2026-08-30)

Captured with `python tools/capture_readme_shots.py` after recipe guidance UI,
Tab overlay, and yard scaling landed in `witches/map.py`.

| Screenshot | What it shows |
|---|---|
| `114536-menu-main` | Main menu |
| `114536-menu-play` | Witch-count screen |
| `114536-menu-controls` | How to play with Recipe list button and Tab note |
| `114536-menu-recipes` | Full in-game recipe reference |
| `114536-menu-pause` | Pause menu with Recipes entry |
| `114536-menu-endscreen` | Shift cleared overlay |
| `114536-gameplay-hud-recipes` | Cauldron panel, cheat sheet, delivery banner, pair hints |
| `114536-gameplay-recipe-overlay` | Tab recipe book over live gameplay |
| `114536-gameplay-wide-map` | Expanded clearing — hub fixed, forage pushed to treeline |
