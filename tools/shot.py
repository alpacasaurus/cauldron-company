#!/usr/bin/env python3
"""Render the game to a PNG for eyeballing (macOS dev helper).

Every capture is kept in screenshots/ with a timestamped name so the visual
history of the build is never overwritten.

Panda3D's offscreen buffers come back blank on macOS, and window-id captures of
an OpenGL surface come back black, so this opens a real always-on-top window at
a known position, steps a few frames, then captures that screen region.

Usage:
    python tools/shot.py --label title
    python tools/shot.py --label gameplay --players 2 --frames 90
    python tools/shot.py --screen hud --label gameplay-hud-recipes --frames 90
    python tools/shot.py --out /tmp/one-off.png --players 1
    python tools/capture_readme_shots.py
"""

import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Screenshot runs are synthetic; keep them out of the player's log.
os.environ.setdefault("CAULDRON_LOG", "0")

from ursina import Ursina, Vec3, application, color, window  # noqa: E402

from witches.glfix import patch_ursina_shaders  # noqa: E402

SHOTS_DIR = ROOT / "screenshots"
ORIGIN = (60, 60)


def resolve_output(out, label):
    if out:
        return Path(out).expanduser().resolve()
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    safe = "".join(c if c.isalnum() or c in "-_" else "-" for c in label)
    return SHOTS_DIR / f"{stamp}-{safe}.png"


def prepare_screen(director, screen):
    """Put the director into a named UI state for capture."""
    if screen in (None, "", "main"):
        director.main_menu()
        return
    if screen == "play":
        director.play_menu()
        return
    if screen == "controls":
        director.controls_menu()
        return
    if screen == "recipes":
        director.recipes_menu()
        return
    if screen == "pause":
        director.start(2)
        director.pause()
        return
    if screen == "end-win":
        director.start(1)
        director._end(True)
        return
    if screen == "end-loss":
        director.start(1)
        director._end(False)
        return
    if screen == "gameplay":
        director.start(2)
        return
    if screen == "overlay":
        director.start(2)
        director.toggle_recipe_overlay()
        return
    if screen == "hud":
        director.start(2)
        p1, p2 = director.bus.players
        director.cauldron.contents.append(
            {"id": "screamstool", "name": "Screamstool"}
        )
        director.cauldron.contents.append(
            {"id": "gossipmoss", "name": "Gossip Moss"}
        )
        director.cauldron.stir = 5
        p1.inventory.append({"id": "dew", "name": "Suspicious Dew"})
        p2.inventory.append({"id": "breadbone", "name": "Probably a Breadstick"})
        p2.inventory.append({"id": "yarncurse", "name": "Cursed Yarnball"})
        p1.position = Vec3(2.2, 0, -1.2)
        p2.position = Vec3(-2.0, 0, 0.5)
        p1.flask = {
            "name": "Voice of Unreasonable Confidence",
            "effect": "honk",
            "value": 2,
        }
        director.bus.quota = 4
        director.bus.remaining = 142
        director._update_frame()
        return
    raise ValueError(f"unknown screen {screen!r}")


def capture(out, frames=45, size="1280x720", screen=None, players=0):
    w, h = (int(v) for v in size.split("x"))
    out = Path(out).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    os.chdir(ROOT)
    patch_ursina_shaders()

    Ursina(
        title="Cauldron Company (shot)",
        development_mode=False,
        editor_ui_enabled=False,
        size=(w, h),
        vsync=False,
    )
    window.color = color.hsv(250, 0.45, 0.07)
    window.always_on_top = True
    window.position = ORIGIN

    from witches.session import boot

    director = boot()
    window.update_aspect_ratio()
    if screen:
        prepare_screen(director, screen)
    elif players:
        director.start(players)

    base = application.base
    for _ in range(frames):
        base.taskMgr.step()

    subprocess.check_call(
        ["screencapture", "-x", "-R", f"{ORIGIN[0]},{ORIGIN[1]},{w},{h + 28}", out.as_posix()]
    )
    print(f"wrote {out}")
    application.quit()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", help="explicit path; default saves into screenshots/")
    ap.add_argument("--label", default="shot", help="name suffix for the saved screenshot")
    ap.add_argument(
        "--screen",
        choices=[
            "main",
            "play",
            "controls",
            "recipes",
            "pause",
            "end-win",
            "end-loss",
            "gameplay",
            "overlay",
            "hud",
        ],
        help="named UI state to capture",
    )
    ap.add_argument("--players", type=int, default=0, help="0 keeps the title screen")
    ap.add_argument("--frames", type=int, default=45)
    ap.add_argument("--size", default="1920x1080")
    args = ap.parse_args()

    out = resolve_output(args.out, args.label)
    capture(
        out,
        frames=args.frames,
        size=args.size,
        screen=args.screen,
        players=args.players if not args.screen else 0,
    )


if __name__ == "__main__":
    main()
