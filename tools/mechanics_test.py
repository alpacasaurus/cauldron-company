#!/usr/bin/env python3
"""Exercise every player-facing mechanic without manual input."""

import os
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Keep harness runs out of the player's diagnostic log; this suite boots the
# game repeatedly and would bury a real session in synthetic events.
os.environ.setdefault("CAULDRON_LOG", "0")

from panda3d.core import loadPrcFileData

loadPrcFileData("", "window-type offscreen")

from ursina import Ursina, Vec3, application, held_keys, time  # noqa: E402

from witches.glfix import patch_ursina_shaders  # noqa: E402

FAILURES = []


def check(label, condition, detail=""):
    status = "ok  " if condition else "FAIL"
    print(f"[{status}] {label} {detail}")
    if not condition:
        FAILURES.append(label)


def clear_keys():
    for key in list(held_keys):
        held_keys[key] = 0


def main():
    patch_ursina_shaders()
    Ursina(window_type="offscreen", development_mode=False, editor_ui_enabled=False)

    from witches.actors import Witch
    from witches.catalog import (
        DIALOGUE_AMBIENT,
        DIALOGUE_MILESTONE,
        EFFECTS,
        FOOD_RECIPES,
        INGREDIENTS,
        RECIPES,
        WEAPON_RECIPES,
    )
    from witches.combat import Enemy
    from witches.forage import Forage
    from witches.session import P1, P2, boot

    director = boot()
    director.start(2)
    bus = director.bus
    p1, p2 = bus.players
    cauldron = director.cauldron
    crate = director.world.quota
    time.dt = 0.1

    print("\nplayers and controls")
    check("two witches spawn", len(bus.players) == 2)
    check("P1 controls are distinct", P1["up"] == "w" and P1["interact"] == "e")
    check("P2 controls are distinct", P2["up"] == "up arrow" and P2["interact"] == "enter")
    clear_keys()
    held_keys["w"] = 1
    before = Vec3(p1.position)
    p1.update()
    check("P1 keyboard movement works", (p1.position - before).length() > 0)
    clear_keys()
    held_keys["up arrow"] = 1
    before = Vec3(p2.position)
    p2.update()
    check("P2 keyboard movement works", (p2.position - before).length() > 0)
    clear_keys()
    director.update()
    check("P1 inventory HUD renders", "Hex:" in director.txt_p1.text)
    check("P2 inventory HUD renders", "Jinx:" in director.txt_p2.text)

    print("\nforaging and inventory")
    p1.inventory.clear()
    target = bus.forage[0]
    p1.position = Vec3(target.x, 0, target.z)
    check("nearby forage can be pocketed", director._try_pickup(p1))
    p1.inventory = [{"id": "dew", "name": "Dew"}] * 3
    target_count = len(bus.forage)
    check("inventory cap is enforced", not director._try_pickup(p1) and len(bus.forage) == target_count)

    print("\nforage behaviors")
    p1.inventory.clear()
    p1.position = Vec3(0, 0, 2)
    cases = {}
    for kind, spec in INGREDIENTS.items():
        cases.setdefault(spec["behavior"], kind)

    fleeing = Forage(bus, cases["flee"], Vec3(0, 0.4, 0))
    before = Vec3(fleeing.position)
    fleeing.update()
    check("fleeing forage runs away", fleeing.z < before.z)
    fleeing.remove()

    hopper = Forage(bus, cases["hop"], Vec3(0, 0.4, 0))
    hopper.phase = 0.2
    hopper.update()
    check("frog forage hops", hopper.y > hopper.base_y)
    hopper.remove()

    roller = Forage(bus, cases["roll"], Vec3(0, 0.4, 0))
    before_rot = roller.rotation_x
    roller.update()
    check("yarn forage rolls", roller.rotation_x != before_rot)
    roller.remove()

    screamer = Forage(bus, cases["scream"], Vec3(0, 0.4, 0))
    p1.stun = 0
    screamer.update()
    check("screamstool stuns nearby witch", p1.stun > 0)
    screamer.remove()

    mandrake = Forage(bus, cases["shy"], Vec3(0, 0.4, 0))
    p1.stun = 0
    p1.facing = Vec3(0, 0, -1)
    mandrake.update()
    check("mandrake screams when faced", p1.stun >= 0.8)
    p1.stun = 0
    p1.facing = Vec3(0, 0, 1)
    mandrake.update()
    check("mandrake stays quiet when faced away", p1.stun == 0)
    mandrake.remove()

    # Regression: a stunned witch could not turn, so it kept staring at the
    # screamer, got re-stunned every frame, and WASD did nothing forever.
    p1.inventory = [{"id": "dew", "name": "Suspicious Dew"}] * 3  # block pickup
    p1.position = Vec3(0, 0, 6)
    p1.stun = 0
    p1.facing = Vec3(0, 0, -1)
    intern = Forage(bus, cases["shy"], Vec3(0, 0.4, 3))
    clear_keys()
    held_keys["w"] = 1
    start = Vec3(p1.position)
    for _ in range(50):
        intern.update()
        p1.update()
    check(
        "a screamer cannot freeze a witch forever",
        (p1.position - start).length() > 2,
        f"moved {(p1.position - start).length():.1f}",
    )
    intern.remove()
    clear_keys()

    p1.stun = 1.0
    bus.tick_dialogue(30)
    director.update()
    check("frozen witches are told why", "frozen" in director.txt_sub.text.lower(), director.txt_sub.text)
    p1.stun = 0
    p1.inventory.clear()

    print("\ncauldron safety and brewing")
    pot_body = cauldron.children[0]
    check("cauldron body has no solid collider", pot_body.collider is None)
    p1.position = Vec3(cauldron.position)
    check("center is not interaction range", not cauldron.in_range(p1))
    check("cauldron ejects bodies from soup", cauldron.keep_bodies_out(p1, time.dt))
    flat = p1.position - cauldron.position
    flat.y = 0
    check(
        "ejected witch lands at safe rim",
        1.44 <= flat.length() <= 1.46,
        f"distance={flat.length():.2f}",
    )
    check("safe rim remains in interaction range", cauldron.in_range(p1))
    p1.position = cauldron.position + Vec3(0, 0, 1.8)
    p1.inventory = [{"id": "dew", "name": "Dew"}, {"id": "moonslug", "name": "Moon Slug"}]
    director.interact(p1)
    director.interact(p1)
    check("two ingredients dump into cauldron", len(cauldron.contents) == 2)
    for _ in range(8):
        director.interact(p1)
    check("eight stirs enter settling phase", cauldron.stir == 8 and cauldron.brew_ready > 0)
    time.dt = 0.7
    cauldron.update()
    check("settled potion is bottled", p1.flask is not None)

    print("\nquota and overflow")
    value = p1.flask["value"]
    p1.position = crate.position + Vec3(0, 0, 1)
    before_quota = bus.quota
    director.interact(p1)
    check("crate accepts potion", bus.quota == before_quota + value and p1.flask is None)
    p1.flask = {"name": "Occupied One", "effect": "tiny", "value": 1}
    p2.flask = {"name": "Occupied Two", "effect": "giant", "value": 1}
    p1.position = cauldron.position + Vec3(0, 0, 1.8)
    p2.position = cauldron.position + Vec3(1.8, 0, 0)
    cauldron.contents = [{"id": "dew", "name": "Dew"}, {"id": "moonslug", "name": "Slug"}]
    cauldron.brew_lock = 0
    cauldron._brew(p1)
    check("full hands send potion to crate overflow", len(bus.overflow) == 1)
    p1.position = crate.position + Vec3(0, 0, 1)
    director.interact(p1)  # deliver occupied flask
    director.interact(p1)  # recover overflow
    check("overflow potion can be recovered", p1.flask is not None and not bus.overflow)

    print("\nall named recipes")
    for ingredients, (expected_name, expected_effect, expected_value) in RECIPES.items():
        ids = list(ingredients)
        if len(ids) == 1:
            ids *= 2
        cauldron.contents = [
            {"id": item_id, "name": INGREDIENTS[item_id]["name"]} for item_id in ids
        ]
        cauldron.mood = 0.5
        cauldron.brew_lock = 0
        cauldron.last_dump = []
        bus.overflow.clear()
        p1.flask = None
        p2.flask = None
        p1.position = cauldron.position + Vec3(0, 0, 1.8)
        p2.position = Vec3(15, 0, 15)
        cauldron._brew(p1)
        potion = p1.flask
        check(
            f"recipe: {expected_name}",
            potion
            and potion["name"] == expected_name
            and potion["effect"] == expected_effect
            and potion["value"] == expected_value,
            str(potion),
        )

    cauldron.contents = [{"id": "dew", "name": "Dew"}, {"id": "breadbone", "name": "Bread"}]
    cauldron.mood = 0.1
    cauldron.brew_lock = 0
    p1.flask = None
    cauldron._brew(p1)
    check("ignored cauldron makes spiteful potion", p1.flask["name"].startswith("Spiteful "))

    cauldron.contents = [
        {"id": "screamstool", "name": "Screamstool"},
        {"id": "dew", "name": "Dew"},
    ]
    cauldron.mood = 0.1
    cauldron.brew_lock = 0
    p1.flask = None
    cauldron._brew(p1)
    check("spiteful named recipe keeps promised effect", p1.flask["effect"] == "honk")

    cauldron.contents = [{"id": "dew", "name": "Dew"}] * 2
    cauldron.stir = 0
    cauldron.brew_lock = 1
    cauldron.start_stir(p1)
    check("cooldown blocks stirring without tantrum progress", cauldron.stir == 0)
    cauldron.brew_lock = 0
    for _ in range(20):
        cauldron.start_stir(p1)
    check("deliberate over-stir triggers tantrum", cauldron.stir == 0 and not cauldron.contents)

    print("\nweapons, enemies, and cooked food")
    p1.position = cauldron.position + Vec3(0, 0, 1.8)
    bow_ingredients = next(ids for ids, weapon in WEAPON_RECIPES.items() if weapon == "bow")
    cauldron.contents = [
        {"id": item_id, "name": INGREDIENTS[item_id]["name"]}
        for item_id in bow_ingredients
    ]
    cauldron.brew_lock = 0
    cauldron._brew(p1)
    check("weapon recipe equips a bow", p1.weapon == "bow")

    p1.position = Vec3(10, 0, 10)
    p1.facing = Vec3(0, 0, 1)
    enemy = Enemy(bus, p1.position + Vec3(0, 0.65, 2))
    for _ in range(2):
        p1.weapon_cooldown = 0
        check("equipped bow fires an arrow", p1.try_fire())
        projectile = bus.projectiles[-1]
        time.dt = 0.05
        projectile.update()
    check("arrows can defeat an enemy", enemy.dead and bus.kills >= 1)

    pistol_ingredients = next(ids for ids, weapon in WEAPON_RECIPES.items() if weapon == "pistol")
    cauldron.contents = [
        {"id": item_id, "name": INGREDIENTS[item_id]["name"]}
        for item_id in pistol_ingredients
    ]
    p1.position = cauldron.position + Vec3(0, 0, 1.8)
    cauldron.brew_lock = 0
    cauldron._brew(p1)
    p1.weapon_cooldown = 0
    check("firearm recipe equips a pistol", p1.weapon == "pistol")
    check("equipped pistol fires", p1.try_fire())
    bus.projectiles[-1].remove()

    food_ingredients = next(iter(FOOD_RECIPES))
    cauldron.contents = [
        {"id": item_id, "name": INGREDIENTS[item_id]["name"]}
        for item_id in food_ingredients
    ]
    p1.position = cauldron.position + Vec3(0, 0, 1.8)
    p1.meal = None
    p1.flask = None
    p1.health = 2
    cauldron.brew_lock = 0
    cauldron._brew(p1)
    check("food recipe produces a carried meal", p1.meal is not None)
    director._handle_key(P1["drink"])
    check("eating cooked food restores health", p1.health > 2 and p1.meal is None)

    print("\npotion effects")
    for effect in EFFECTS:
        p1.effects.clear()
        p1.scale = 1
        p1.apply_effect(effect, 2)
        check(f"{effect} effect activates", p1.has(effect))

    p1.effects.clear()
    p1.apply_effect("tiny", 2)
    check("tiny shrinks witch", abs(p1.scale_x - 0.45) < 0.01)
    p1.apply_effect("giant", 2)
    check("giant overrides tiny", abs(p1.scale_x - 1.85) < 0.01)
    del p1.effects["giant"]
    p1._refresh_visuals()
    check("tiny resumes after giant expires", abs(p1.scale_x - 0.45) < 0.01)

    p1.effects.clear()
    p1.apply_effect("reverse")
    clear_keys()
    held_keys["d"] = 1
    x, _ = p1.input_axes()
    check("reverse reverses controls", x < 0)
    p1.effects.clear()
    p1.apply_effect("shuffle")
    with patch("witches.actors.random.random", return_value=0):
        x, z = p1.input_axes()
    check("shuffle rotates controls", abs(x) < 0.01 and z > 0)
    clear_keys()

    p1.effects.clear()
    p1.position = Vec3(10, 0, 10)
    held_keys["w"] = 1
    before = Vec3(p1.position)
    p1.update()
    normal_distance = (p1.position - before).length()
    p1.position = Vec3(10, 0, 10)
    p1.apply_effect("sticky")
    before = Vec3(p1.position)
    p1.update()
    sticky_distance = (p1.position - before).length()
    check("sticky slows movement", sticky_distance < normal_distance)

    p1.effects.clear()
    p1.slip = Vec3(0, 0, 0)
    p1.position = Vec3(10, 0, 10)
    p1.apply_effect("ice")
    p1.update()
    clear_keys()
    before = Vec3(p1.position)
    p1.update()
    check("ice preserves momentum after key release", (p1.position - before).length() > 0)

    p1.effects.clear()
    p1.grounded = True
    p1.apply_effect("moonjump")
    p1.try_jump()
    check("moonjump jumps higher", p1.vy == 16)
    p1.effects.clear()
    p1.grounded = True
    p1.try_jump()
    check("normal hop works", p1.vy == 9)

    p1.effects.clear()
    p1.position = Vec3(10, 0, 10)
    p1.apply_effect("hiccup")
    with (
        patch("witches.actors.random.random", return_value=0),
        patch("witches.actors.random.uniform", return_value=2),
    ):
        before = Vec3(p1.position)
        p1.update()
    check("hiccup teleports witch", (p1.position - before).length() > 1)

    p1.effects.clear()
    p1.apply_effect("spin")
    before_rot = p1.rotation_y
    p1.update()
    check("spin rotates witch", p1.rotation_y != before_rot)

    p1.effects.clear()
    base_hat = Vec3(p1.hat_base_scale)
    p1.apply_effect("honk")
    p1.update()
    check("honk animates hat", p1.hat.scale != base_hat)
    p1.effects.clear()
    p1._refresh_visuals()
    check("hat restores after honk", p1.hat.scale == base_hat)

    p1.effects.clear()
    p1.apply_effect("tiny", 0.05)
    time.dt = 0.1
    p1.update()
    check("effects expire and restore visuals", not p1.has("tiny") and p1.scale_x == 1)

    print("\nbroom chaos")
    p1.effects.clear()
    p1.stun = 0
    p1.dash_cd = 0
    p1.facing = Vec3(0, 0, 1)
    before = Vec3(p1.position)
    with patch("witches.actors.random.random", return_value=0.5):
        p1.try_dash()
    check("normal broom dash moves forward", p1.z > before.z)
    p1.dash_cd = 0
    before = Vec3(p1.position)
    with patch("witches.actors.random.random", return_value=0.05):
        p1.try_dash()
    check("betrayal dash moves backward", p1.z < before.z)
    p1.dash_cd = 0
    with patch("witches.actors.random.random", return_value=0.15):
        p1.try_dash()
    check("orbital broom launches witch", p1.vy == 18)

    print("\nfamiliar")
    cat = director.cat
    p2.inventory = [{"id": "dew", "name": "Dew"}]
    cat.target = p2
    cat.position = Vec3(p2.position)
    cat.steal_cd = 0
    cat.update()
    check("familiar steals ingredients", getattr(cat, "stolen", None) is not None)
    p1.inventory = []
    p1.position = Vec3(cat.position)
    cat.scritch(p1)
    check("scritch recovers stolen ingredient", p1.inventory and cat.stolen is None)
    cat.stolen = {"id": "dew", "name": "Dew"}
    p1.inventory = [{"id": "dew", "name": "Dew"}] * 3
    cat.scritch(p1)
    check("full pockets do not delete stolen loot", cat.stolen is not None)

    print("\ndialogue and timing")
    bus.tick_dialogue(10)
    bus.say("A plain gameplay message.")
    check("all dialogue invokes mythical Eric", "eric" in bus.subtitle.lower(), bus.subtitle)

    bus.tick_dialogue(10)
    quiet = bus.subtitle
    check(
        "idle scenery chatter stays muted",
        not bus.say("The ferns are gossiping.", rank=DIALOGUE_AMBIENT)
        and bus.subtitle == quiet,
    )
    check(
        "milestones always speak",
        bus.say("Crate ate a potion.", rank=DIALOGUE_MILESTONE)
        and "crate ate" in bus.subtitle.lower(),
    )
    milestone_line = bus.subtitle
    check(
        "routine lines do not stomp a fresh milestone",
        not bus.say("Hex stirs the pot.") and bus.subtitle == milestone_line,
    )
    bus.tick_dialogue(2)
    check(
        "player actions speak once the milestone settles",
        bus.say("Hex stirs the pot.") and "stirs the pot" in bus.subtitle.lower(),
    )
    repeat = bus.subtitle
    bus.tick_dialogue(30)
    bus.say("Hex stirs the pot.")
    check("a repeated line keeps its original omen", bus.subtitle == repeat, bus.subtitle)

    # Regression: ambient events used to roll a random chance every frame, which
    # flickered a new Eric line several times a second.
    p1.effects.clear()
    p1.inventory.clear()
    clear_keys()
    p1.position = Vec3(cauldron.position)
    mandrake = Forage(bus, "mandrake", Vec3(p1.x + 2, 0, p1.z))
    p1.facing = (mandrake.position - p1.position).normalized()
    bus.tick_dialogue(10)
    lines, changes, last = set(), 0, ""
    for _ in range(240):
        p1.update()
        mandrake.update()
        bus.tick_dialogue(time.dt)
        showing = bus.subtitle if bus.speaking else ""
        if showing and showing != last:
            lines.add(showing)
            changes += 1
        last = showing
    mandrake.remove()
    check(
        "hazards say their piece once, not every frame",
        len(lines) <= 1 and changes <= 2,
        f"{changes} appearances, {len(lines)} distinct: {sorted(lines)}",
    )

    print("\nNPC trash talk")
    bus.bark_cd = 0
    bus.tick_dialogue(10)
    heckler = Enemy(bus, Vec3(14, 0.65, 14))
    heckler.heckle_cd = 0
    p1.position = Vec3(14, 0, 16)
    p2.position = Vec3(30, 0, 30)
    time.dt = 0.1
    heckler.update()
    check(
        "goblins heckle witches on sight",
        bus.barking and heckler.display_name in bus.bark_line,
        bus.bark_line,
    )
    check("barks are quoted, not narrated as Eric omens", "eric" not in bus.bark_line.lower())

    subtitle_before = bus.subtitle
    bus.bark_cd = 0
    bus.bark("Soup Auditor", "Test line.")
    check(
        "barks never overwrite the Eric subtitle channel",
        bus.subtitle == subtitle_before,
        bus.subtitle,
    )

    bus.bark_cd = 0
    heckler.attack_cd = 0
    heckler.position = Vec3(p1.x, 0.65, p1.z + 1)
    heckler.update()
    check("goblins bark while biting", bus.barking and "Test line." not in bus.bark_line)

    bus.bark_cd = 5
    held = bus.bark_line
    heckler.hit(1, p1)
    check("routine barks respect the cooldown", bus.bark_line == held, bus.bark_line)
    bus.bark_cd = 0
    heckler.hit(0, p1)
    check("wounded goblins yelp", bus.bark_line != held, bus.bark_line)

    bus.bark_cd = 5
    heckler.hit(5, p1)
    check("last words are never swallowed", heckler.dead and bus.barking, bus.bark_line)

    bus.bark_cd = 0
    bus.tick_dialogue(10)
    cat.position = Vec3(p1.position)
    p1.inventory = []
    cat.stolen = None
    cat.scritch(p1)
    check("the familiar mouths off when scritched", "familiar" in bus.bark_line.lower(), bus.bark_line)

    bus.bark_cd = 0
    director.update()
    check("barks render on their own HUD line", director.txt_bark.text == bus.bark_line)
    bus.tick_dialogue(10)
    director.update()
    check("barks clear when the NPC shuts up", director.txt_bark.text == "")

    door = director.world.door.world_position
    p1.position = Vec3(door.x, 0, door.z + 3)
    bus.tick_dialogue(10)
    director.world.hut_lines_cd = 0
    check("talking to the hut starts a conversation", director.world.chat(p1))
    check("the hut will not repeat itself instantly", not director.world.chat(p1))

    cauldron.contents = [{"id": "dew", "name": "Dew"}, {"id": "dew", "name": "Dew"}]
    cauldron.stir = 3
    cauldron.stir_window = 0.05
    time.dt = 0.1
    cauldron.update()
    check("abandoned stirring fizzles", cauldron.stir == 0)

    print("\nstart menu")
    from ursina import application, scene

    menu = boot()
    check("the game boots into the main menu", menu.menu_screen == "main" and not menu.bus.playing)
    check("main menu offers play, how to play, and quit", len(menu.menu_bits) == 6)
    menu.play_menu()
    check("play opens the witch-count screen", menu.menu_screen == "play")
    menu.controls_menu()
    check("how to play opens the controls screen", menu.menu_screen == "controls")
    menu._handle_key("escape")
    check("escape backs out of a submenu instead of quitting", menu.menu_screen == "main")

    # Drive the real Button callbacks, not just the methods behind them, so a
    # miswired on_click cannot pass the suite and still strand players.
    def click(label):
        target = next(b for b in menu.menu_bits if label in str(getattr(b, "text", "")))
        target.on_click()

    click("PLAY")
    check("clicking PLAY opens the witch-count screen", menu.menu_screen == "play")
    click("Back")
    check("clicking Back returns to the main menu", menu.menu_screen == "main")
    click("PLAY")
    click("2 witches")
    check("clicking a witch count starts the shift", menu.bus.playing)
    check("play starts a shift", len(menu.bus.players) == 2)
    check("the menu clears once the shift starts", not menu.menu_bits)

    menu._handle_key("escape")
    check("escape pauses a shift instead of quitting", menu.paused and application.paused)
    check("pausing opens the pause menu", menu.menu_screen == "pause")
    p1_paused = menu.bus.players[0]
    clear_keys()
    held_keys["w"] = 1
    before = Vec3(p1_paused.position)
    menu.update()
    menu._handle_key(P1["interact"])
    check("paused witches ignore gameplay keys", (p1_paused.position - before).length() == 0)
    menu._handle_key("escape")
    check("escape unpauses", not menu.paused and not application.paused and not menu.menu_bits)
    clear_keys()

    # Regression guard: the world used to leak every entity it built, so each
    # trip through the menu stacked a second clearing on top of the first.
    def settle():
        for _ in range(3):
            application.base.taskMgr.step()

    shift_entities = list(menu.world.entities)
    shift_entities += [menu.cauldron, menu.cauldron.mat, menu.cat]
    shift_entities += list(menu.bus.players) + list(menu.bus.forage)
    hut_walls = list(menu.world.hut.children)
    menu.to_menu()
    settle()
    check(
        "returning to the menu tears the shift down",
        menu.world is None and menu.cauldron is None and not menu.bus.players,
    )
    leaked = [e for e in shift_entities if e in scene.entities]
    check(
        "no shift entity survives the trip back to the menu",
        not leaked,
        f"{len(leaked)}/{len(shift_entities)} leaked",
    )
    orphans = [e for e in hut_walls if e in scene.entities]
    check("child entities die with their parent", not orphans, f"{len(orphans)} orphans")

    menu.start(2)
    settle()
    check("the menu can start a second shift", menu.bus.playing and menu.world is not None)
    check(
        "the second shift builds exactly one clearing",
        len([e for e in scene.entities if e in menu.world.entities]) == len(menu.world.entities),
    )
    menu.to_menu()
    settle()

    print("\nloss state")
    # Use a fresh session because the previous quota may be near completion.
    director2 = boot()
    director2.start(1)
    director2.bus.remaining = 0.01
    time.dt = 0.1
    director2.update()
    check("rooster timer ends shift", director2.bus.over and not director2.bus.playing)

    print()
    # Do not call application.quit() here: it is sys.exit(), which would skip
    # the summary below and force exit code 0 even when checks failed.
    if FAILURES:
        print(f"{len(FAILURES)} failure(s): {', '.join(FAILURES)}")
        return 1
    print("all mechanics passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
