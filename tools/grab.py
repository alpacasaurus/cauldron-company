#!/usr/bin/env python3
"""Find the game window and screencapture it by id (dev helper, macOS only)."""

import subprocess
import sys

import Quartz

TARGET_OWNERS = ("Python", "python3", "CauldronCompany")


def windows():
    info = Quartz.CGWindowListCopyWindowInfo(
        Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements,
        Quartz.kCGNullWindowID,
    )
    for w in info:
        owner = w.get("kCGWindowOwnerName", "")
        bounds = w.get("kCGWindowBounds", {})
        yield {
            "id": w.get("kCGWindowNumber"),
            "owner": owner,
            "name": w.get("kCGWindowName", ""),
            "w": int(bounds.get("Width", 0)),
            "h": int(bounds.get("Height", 0)),
        }


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "/tmp/game.png"
    candidates = [w for w in windows() if w["owner"] in TARGET_OWNERS and w["w"] > 200]
    if not candidates:
        print("no game window found. all windows:")
        for w in windows():
            print(f"  {w['owner']!r} {w['name']!r} {w['w']}x{w['h']} id={w['id']}")
        return 1
    target = max(candidates, key=lambda w: w["w"] * w["h"])
    print(f"capturing {target['owner']!r} {target['w']}x{target['h']} id={target['id']}")
    subprocess.check_call(["screencapture", "-x", "-o", "-l", str(target["id"]), out])
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
