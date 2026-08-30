#!/usr/bin/env python3
"""Capture the README screenshot set with stable filenames."""

import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STAMP = datetime.now().strftime("%Y-%m-%d_%H%M%S")
FRAMES = 90
PYTHON = ROOT / ".venv" / "bin" / "python"
SHOT = ROOT / "tools" / "shot.py"
OUT_DIR = ROOT / "screenshots"

SHOTS = [
    ("menu-main", "main"),
    ("menu-play", "play"),
    ("menu-controls", "controls"),
    ("menu-recipes", "recipes"),
    ("menu-pause", "pause"),
    ("menu-endscreen", "end-win"),
    ("gameplay-hud-recipes", "hud"),
    ("gameplay-recipe-overlay", "overlay"),
    ("gameplay-wide-map", "gameplay"),
]


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    written = []
    for label, screen in SHOTS:
        out = OUT_DIR / f"{STAMP}-{label}.png"
        subprocess.check_call(
            [
                str(PYTHON),
                str(SHOT),
                "--screen",
                screen,
                "--out",
                str(out),
                "--frames",
                str(FRAMES),
            ],
            cwd=ROOT,
        )
        written.append(out)
    print("\nREADME set:")
    for path in written:
        print(f"  {path.name}")


if __name__ == "__main__":
    main()
