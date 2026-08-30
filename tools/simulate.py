#!/usr/bin/env python3
"""Drive a full forage -> dump -> stir -> brew -> deliver loop without a human.

Run: python tools/simulate.py
Exits non-zero if any stage of the core loop fails.
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Synthetic runs must not pollute the player's diagnostic log.
os.environ.setdefault("CAULDRON_LOG", "0")

from panda3d.core import loadPrcFileData

loadPrcFileData("", "window-type offscreen")

from ursina import Ursina, Vec3, application, time  # noqa: E402

from witches.glfix import patch_ursina_shaders  # noqa: E402

FAILURES = []


def check(label, condition, detail=""):
    status = "ok  " if condition else "FAIL"
    print(f"[{status}] {label} {detail}")
    if not condition:
        FAILURES.append(label)


def step(base, n=2):
    for _ in range(n):
        base.taskMgr.step()


def main():
    patch_ursina_shaders()
    app = Ursina(
        window_type="offscreen",
        development_mode=False,
        editor_ui_enabled=False,
        size=(640, 360),
        vsync=False,
    )

    from witches.session import QUOTA_GOAL, boot

    director = boot()
    director.start(2)
    base = application.base
    step(base, 3)

    bus = director.bus
    p1, p2 = bus.players
    check("two witches spawned", len(bus.players) == 2)
    check("forageables exist", len(bus.forage) > 0, f"({len(bus.forage)})")

    # Plant a known potion pair. Left to chance, the first two forageables can
    # roll a food or weapon recipe, which correctly produces a meal or a bow and
    # then fails the flask check below for no good reason.
    from witches.forage import Forage  # noqa: E402

    for kind, spot in (("screamstool", Vec3(9, 0.4, 9)), ("dew", Vec3(-9, 0.4, 9))):
        bus.forage.insert(0, Forage(bus, kind, spot))

    # forage two ingredients with witch 1
    for i in range(2):
        target = bus.forage[0]
        p1.position = Vec3(target.x, 0, target.z)
        p1.facing = Vec3(0, 0, 1)
        before = len(p1.inventory)
        director._try_pickup(p1)
        check(f"picked up ingredient {i + 1}", len(p1.inventory) == before + 1,
              f"-> {[x['name'] for x in p1.inventory]}")

    # dump both into the cauldron
    cauldron = director.cauldron
    p1.position = cauldron.position + Vec3(0, 0, 1.5)
    step(base)
    while p1.inventory:
        director.interact(p1)
    check("cauldron holds two ingredients", len(cauldron.contents) == 2,
          f"-> {[c['name'] for c in cauldron.contents]}")

    # a second witch dumping soon after should trigger the friendship bonus path
    check("cauldron mood raised by dumping", cauldron.mood > 0.5, f"mood={cauldron.mood:.2f}")

    # stir until it brews
    for _ in range(8):
        director.interact(p1)
    time.dt = 0.7
    cauldron.update()
    check("brewed a potion", p1.flask is not None,
          f"-> {p1.flask['name'] if p1.flask else None}")

    if p1.flask:
        effect = p1.flask["effect"]
        value = p1.flask["value"]
        check("potion has an effect", isinstance(effect, str) and effect)
        check("potion has quota value", value >= 1, f"value={value}")

        # deliver to the crate
        crate = director.world.quota
        p1.position = crate.position + Vec3(0, 0, 1.5)
        step(base)
        director.interact(p1)
        check("crate accepted the flask", bus.quota >= value, f"quota={bus.quota}/{QUOTA_GOAL}")
        check("flask consumed on delivery", p1.flask is None)

    # drinking applies a status effect
    p2.apply_effect("tiny", 5)
    step(base)
    check("effect applied to witch 2", p2.has("tiny"), f"scale={p2.scale_x}")

    # the familiar should be able to steal and be appeased
    p2.inventory.append({"id": "dew", "name": "Suspicious Dew"})
    director.cat.position = p2.position + Vec3(0.5, 0, 0)
    director.cat.steal_cd = 0
    director.cat.target = p2
    step(base, 8)
    stolen = getattr(director.cat, "stolen", None)
    check("familiar stole an ingredient", stolen is not None or not p2.inventory,
          f"stolen={stolen['name'] if stolen else None}")

    # cauldron tantrum on over-stirring
    p1.position = cauldron.position + Vec3(0, 0, 1.5)
    step(base)
    cauldron.contents = [{"id": "dew", "name": "Suspicious Dew"}] * 2
    cauldron.stir = 19
    cauldron.brew_lock = 0
    for _ in range(20):
        cauldron.start_stir(p1)
    check("over-stir triggers tantrum", cauldron.stir == 0 and not cauldron.contents)

    print()
    if FAILURES:
        print(f"{len(FAILURES)} failure(s): {', '.join(FAILURES)}")
    else:
        print("core loop OK")
    # application.quit() is sys.exit(), which would discard this exit code.
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
