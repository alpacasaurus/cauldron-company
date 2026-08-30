"""HUD pixel-art icon textures."""

from pathlib import Path

from ursina import load_texture

ICON_DIR = Path(__file__).resolve().parent / "assets" / "textures" / "hud"

INGREDIENT_ICONS = (
    "screamstool",
    "moonslug",
    "gossipmoss",
    "frogchoir",
    "yarncurse",
    "mandrake",
    "dew",
    "breadbone",
    "gnomecap",
    "nightmilk",
)

OUTCOME_ICONS = (
    "potion",
    "bow",
    "pistol",
    "food",
    "arrow",
    "warning",
    "crate",
)

ALL_ICONS = INGREDIENT_ICONS + OUTCOME_ICONS
_TEXTURES = {}


def _crisp(texture):
    texture.filtering = False
    return texture


def ensure_hud_icons():
    if _TEXTURES:
        return
    for name in ALL_ICONS:
        _TEXTURES[name] = _crisp(load_texture(name, ICON_DIR))


def icon_texture(name):
    ensure_hud_icons()
    return _TEXTURES.get(name)
