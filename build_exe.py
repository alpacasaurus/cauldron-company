#!/usr/bin/env python3
"""Build a native folder/app for the OS you are on. PyInstaller cannot cross-compile."""

import subprocess
import sys
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    spec = ROOT / "CauldronCompany.spec"
    cache = ROOT / ".pyinstaller-cache"
    shutil.rmtree(cache, ignore_errors=True)
    env = os.environ.copy()
    env["PYINSTALLER_CONFIG_DIR"] = str(cache)
    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", str(spec)]
    print(" ".join(cmd))
    subprocess.check_call(cmd, cwd=ROOT, env=env)
    dist = ROOT / "dist"
    print("\nBuild finished.")
    print(f"  macOS app:     {dist / 'CauldronCompany.app'}")
    print(f"  folder build:  {dist / 'CauldronCompany'}")
    print("Run the packaged binary on this same OS. To ship Windows, run this script on a PC.")


if __name__ == "__main__":
    main()
