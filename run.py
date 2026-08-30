#!/usr/bin/env python3
"""Cauldron Company — run from the repo root (or the packaged executable)."""

from ursina import Ursina, color, window

from witches.glfix import patch_ursina_shaders

patch_ursina_shaders()

app = Ursina(
    title="Cauldron Company",
    borderless=False,
    fullscreen=False,
    development_mode=False,
    editor_ui_enabled=False,
    size=(1280, 720),
    vsync=True,
)
window.color = color.hsv(250, 0.45, 0.07)

# Ursina sizes the UI lens from Panda3D's 'aspectRatioChanged' event, which does
# not fire in a packaged build, leaving the HUD zoomed in. Size it up front.
window.update_aspect_ratio()

from witches.session import boot  # noqa: E402

boot()
app.run()
