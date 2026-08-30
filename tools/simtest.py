#!/usr/bin/env python3
"""Drive the core loop without a player: forage -> dump -> stir -> brew -> deliver."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from panda3d.core import loadPrcFileData

loadPrcFileData("", "window-type offscreen")

from ursina import Ursina, Vec3, time  # noqa: E402

from witches.glfix import patch_ursina_shaders  # noqa: E402

FAILURES = []


def check(label, condition, detail=""):
    status = "ok  " if condition else "FAIL"
    print(f"  [{status}] {label} {detail}")
    if not condition:
        FAILURES.append(label)


def main():
    patch_ursina_shaders()
    Ursina(window_type="offscreen", development_mode=False, editor_ui_enabled=False)

    from witches.session import QUOTA_GOAL, boot

    director = boot()
    director.start(2)
    bus = director.bus
    p1, p2 = bus.players
    cauldron = director.cauldron
    crate = director.world.quota

    print("forage pickup")
    for _ in range(3):
        target = bus.forage[0]
        p1.position = Vec3(target.x, 0, target.z)
        before = len(p1.inventory)
        director.interact(p1)
        check("picked up an ingredient", len(p1.inventory) == before + 1, f"{p1.inventory}")

    print("dump into cauldron")
    p1.position = cauldron.position + Vec3(0, 0, 1.8)
    check("cauldron in range", cauldron.in_range(p1))
    for _ in range(2):
        director.interact(p1)
    check("cauldron holds 2 items", len(cauldron.contents) == 2, f"{cauldron.contents}")

    print("compliment affects mood")
    cauldron.mood = 0.4
    cauldron.compliment(p1)
    check("mood rose", cauldron.mood > 0.4, f"mood={cauldron.mood:.2f}")

    print("stir to brew")
    for _ in range(8):
        cauldron.start_stir(p1)
    time.dt = 0.7
    cauldron.update()
    got_flask = p1.flask or p2.flask
    check("a flask was bottled", bool(got_flask), f"{got_flask}")
    check("cauldron emptied", cauldron.contents == [])

    print("deliver to crate")
    holder = p1 if p1.flask else p2
    value = holder.flask["value"]
    holder.position = Vec3(crate.x, 0, crate.z + 1)
    director.interact(holder)
    check("quota increased", bus.quota == value, f"quota={bus.quota} expected={value}")
    check("flask consumed", holder.flask is None)

    print("drinking applies an effect")
    p2.flask = {"name": "Test Sludge", "effect": "tiny", "value": 1}
    p2.apply_effect(p2.flask["effect"])
    check("effect active", p2.has("tiny"), f"{dict(p2.effects)}")
    check("scale changed", p2.scale_x != 1, f"scale={p2.scale_x}")

    print("familiar steals and returns")
    p1.inventory.append({"id": "dew", "name": "Suspicious Dew"})
    cat = director.cat
    cat.stolen = p1.inventory.pop()
    cat.position = p1.position + Vec3(0, 0, 1)
    cat.yarn = 0
    cat.steal_cd = 0
    cat.scritch(p1)
    check("loot recovered", any(i["id"] == "dew" for i in p1.inventory), f"{p1.inventory}")

    print("cauldron tantrum on over-stir")
    for _ in range(2):
        director.interact(p1) if p1.inventory else None
    p1.position = cauldron.position + Vec3(0, 0, 1.8)
    p1.inventory = [{"id": "dew", "name": "Dew"}, {"id": "moonslug", "name": "Slug"}]
    director.interact(p1)
    director.interact(p1)
    cauldron.brew_lock = 0
    for _ in range(20):
        cauldron.start_stir(p1)
    check("tantrum cleared the pot", cauldron.contents == [], f"stir={cauldron.stir}")

    print("named recipe is recognised")
    cauldron.brew_lock = 0
    cauldron.stir = 0
    cauldron.mood = 0.9
    cauldron.contents = [
        {"id": "screamstool", "name": "Screamstool"},
        {"id": "dew", "name": "Suspicious Dew"},
    ]
    cauldron.last_dump = []
    p1.flask = None
    p2.flask = None
    p1.position = cauldron.position + Vec3(0, 0, 1.8)
    p2.position = Vec3(30, 0, 30)
    cauldron._brew(p1)
    brewed = p1.flask or p2.flask
    check(
        "screamstool + dew -> Voice of Unreasonable Confidence",
        brewed and "Voice of Unreasonable Confidence" in brewed["name"],
        f"{brewed}",
    )

    print("co-op dumping grants the Besties bonus")
    cauldron.brew_lock = 0
    cauldron.stir = 0
    cauldron.mood = 0.9
    p1.flask = None
    p2.flask = None
    p1.inventory = [{"id": "dew", "name": "Dew"}]
    p2.inventory = [{"id": "moonslug", "name": "Moon Slug"}]
    p1.position = cauldron.position + Vec3(0, 0, 1.8)
    p2.position = cauldron.position + Vec3(1.8, 0, 0)
    cauldron.dump(p1)
    cauldron.dump(p2)
    cauldron._brew(p1)
    brewed = p1.flask or p2.flask
    check("besties potion brewed", brewed and brewed["name"].startswith("Besties"), f"{brewed}")
    check("besties is worth more", brewed and brewed["value"] >= 3, f"{brewed}")

    print("winning ends the shift")
    bus.quota = QUOTA_GOAL - 1
    winner = bus.players[0]
    winner.flask = {"name": "Closer", "effect": "honk", "value": 3}
    winner.position = Vec3(crate.x, 0, crate.z + 1)
    director.interact(winner)
    check("shift ended on quota", bus.over and not bus.playing, f"quota={bus.quota}")

    print()
    if FAILURES:
        print(f"{len(FAILURES)} failed: {FAILURES}")
        return 1
    print("all core loop checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
