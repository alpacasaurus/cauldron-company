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
    python tools/shot.py --out /tmp/one-off.png --players 1
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

from ursina import Ursina, application, color, window  # noqa: E402

from witches.glfix import patch_ursina_shaders  # noqa: E402

SHOTS_DIR = ROOT / "screenshots"
ORIGIN = (60, 60)


def resolve_output(out, label):
    if out:
        return Path(out).expanduser().resolve()
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    safe = "".join(c if c.isalnum() or c in "-_" else "-" for c in label)
    return SHOTS_DIR / f"{stamp}-{safe}.png"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", help="explicit path; default saves into screenshots/")
    ap.add_argument("--label", default="shot", help="name suffix for the saved screenshot")
    ap.add_argument("--players", type=int, default=0, help="0 keeps the title screen")
    ap.add_argument("--frames", type=int, default=45)
    ap.add_argument("--size", default="1280x720")
    args = ap.parse_args()

    w, h = (int(v) for v in args.size.split("x"))
    out = resolve_output(args.out, args.label)
    out.parent.mkdir(parents=True, exist_ok=True)

    patch_ursina_shaders()

    app = Ursina(
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
    if args.players:
        director.start(args.players)

    base = application.base
    for _ in range(args.frames):
        base.taskMgr.step()

    subprocess.check_call(
        ["screencapture", "-x", "-R", f"{ORIGIN[0]},{ORIGIN[1]},{w},{h + 28}", out.as_posix()]
    )
    print(f"wrote {out}")
    application.quit()


if __name__ == "__main__":
    main()
