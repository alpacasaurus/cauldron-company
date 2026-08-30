"""Shared window size, HUD scale, and layout zones."""

from ursina import Entity, color

from witches.glfix import portable_unlit

WINDOW_SIZE = (1920, 1080)
HUD_SCALE = 1.28

# Normalized UI coordinates (Ursina camera.ui space).
Y_TOP = 0.47
Y_BARK = -0.24
Y_SUB = -0.33
Y_KEYS = -0.41
Y_PLAYER_NAME = -0.34
Y_PLAYER_POCKETS = -0.40
Y_PLAYER_CARRIED = -0.46
Y_PLAYER_ICONS = Y_PLAYER_POCKETS
Y_CAULDRON_ICONS = 0.30
Y_CAULDRON_META = 0.22

X_QUOTA = -0.88
X_TIME = 0.88
X_GOAL = 0.0
X_CAULDRON = -0.78
X_RECIPE = 0.73
X_PLAYER_L = -0.86
X_PLAYER_R = 0.58

# camera.ui draw order: more negative z renders on top.
Z_HUD_BACK = 0.02
Z_HUD_ICON = -0.01
Z_OVERLAY_BACK = -0.12
Z_OVERLAY_PANEL = -0.14
Z_OVERLAY_ICON = -0.16
Z_OVERLAY_TEXT = -0.18


def s(value):
    """Scale a HUD layout constant."""
    return value * HUD_SCALE


def hud_panel(parent, x, y, width, height, alpha=0.42, z=Z_HUD_BACK):
    """Dark translucent plate to separate HUD blocks from the world."""
    return Entity(
        parent=parent,
        model="quad",
        position=(x, y, z),
        scale=(width, height),
        color=color.rgba(0, 0, 0, alpha),
        shader=portable_unlit,
    )


def tinted_panel(parent, x, y, width, height, rgb, alpha=0.25, z=Z_OVERLAY_PANEL):
    """Colored translucent plate for overlay sections and rules."""
    r, g, b = rgb
    return Entity(
        parent=parent,
        model="quad",
        position=(x, y, z),
        scale=(width, height),
        color=color.rgba(r, g, b, alpha),
        shader=portable_unlit,
    )
