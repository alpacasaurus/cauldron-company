"""Shared yard layout — scale these to resize the whole clearing."""

MAP_LIMIT = 38
HUB_RADIUS = 10

FORAGE_MIN = 14
FORAGE_MAX = 32
FORAGE_COUNT = 26

ENEMY_SPAWN_MIN = 26
ENEMY_SPAWN_MAX = 36

CAM_X_LIMIT = 18
CAM_Z_MIN = -12
CAM_Z_MAX = 24
CAMERA_HEIGHT = 16
CAMERA_BACK = 28

GROUND_SCALE = 180
CLEARING_SCALE = 28
TREE_RING_MIN = 24
TREE_RING_MAX = 58
TREE_HUB_GAP = 18
MUSHROOM_RING = 16

CRATE_POS = (10.0, 0.55, 6.0)
MOON_POS = (24, 32, -28)


def forage_spawn_ok(pos):
    """Keep pickups out of the hub, hut porch, and quota crate."""
    if pos.length() <= HUB_RADIUS:
        return False
    if abs(pos.x) < 5 and pos.z < -4:
        return False
    if abs(pos.x - CRATE_POS[0]) + abs(pos.z - CRATE_POS[2]) < 4:
        return False
    return True
