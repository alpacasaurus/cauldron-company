#!/usr/bin/env python3
"""Minimal onscreen render probe: cube + text, with and without custom shaders."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ursina import Entity, Text, Ursina, camera, color, window  # noqa: E402

MODE = sys.argv[1] if len(sys.argv) > 1 else "patched"

if MODE == "patched":
    from witches.glfix import patch_ursina_shaders

    patch_ursina_shaders()

app = Ursina(
    title="probe",
    development_mode=False,
    editor_ui_enabled=False,
    size=(800, 500),
    vsync=False,
)
window.color = color.hsv(250, 0.45, 0.15)
window.always_on_top = True
window.position = (60, 60)

Entity(model="cube", color=color.orange, position=(0, 0, 0), scale=2)
Entity(model="sphere", color=color.azure, position=(3, 0, 0), scale=2)
Text(text="PROBE TEXT VISIBLE", parent=camera.ui, origin=(0, 0), y=0.3, scale=2)
camera.position = (0, 2, -10)
camera.look_at((0, 0, 0))

print(f"probe mode={MODE} entities={len(__import__('ursina').scene.entities)}")
app.run()
