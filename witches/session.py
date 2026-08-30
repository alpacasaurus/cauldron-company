"""Title screen, shared camera, HUD, and the night shift."""

import math
import random
import traceback
from pathlib import Path

from ursina import (
    Button,
    Entity,
    Text,
    Vec3,
    application,
    camera,
    color,
    destroy,
    music_system,
    time,
    window,
)
from ursina.prefabs.sky import Sky

from witches.actors import Familiar, Witch
from witches.brew import REACH, SOUP_RIM, Cauldron
from witches.catalog import (
    DIALOGUE_ACTION,
    DIALOGUE_AMBIENT,
    DIALOGUE_MILESTONE,
    GOSSIP,
    cauldron_hud_text,
    deliver_hud_text,
    format_recipe_options,
    hud_quick_recipes,
    needed_ingredient_id_set,
    outcome_for_pair,
    player_pair_hint,
    recipe_menu_text,
)
from witches.debuglog import banner, log, log_path
from witches.map import (
    CAM_X_LIMIT,
    CAM_Z_MAX,
    CAM_Z_MIN,
    CAMERA_BACK,
    CAMERA_HEIGHT,
    FORAGE_COUNT,
)
from witches.forage import spawn_forage
from witches.glfix import portable_unlit
from witches.combat import WEAPONS, spawn_enemy
from witches.teardown import destroy_tree
from witches.world import World

P1 = {
    "up": "w",
    "down": "s",
    "left": "a",
    "right": "d",
    "interact": "e",
    "dash": "left shift",
    "jump": "space",
    "drink": "f",
    "scritch": "q",
    "compliment": "c",
    "fire": "r",
    "stick": "gamepad",
}
P2 = {
    "up": "up arrow",
    "down": "down arrow",
    "left": "left arrow",
    "right": "right arrow",
    "interact": "enter",
    "dash": "right shift",
    "jump": "/",
    "drink": "'",
    "scritch": "p",
    "compliment": "]",
    "fire": "right control",
    "stick": "gamepad_1",
}

SHIFT_LEN = 180
QUOTA_GOAL = 8
MUSIC_DIR = Path(__file__).resolve().parent.parent / "assets" / "music"
TITLE_MUSIC = MUSIC_DIR / "lonely_witch.ogg"
SHIFT_MUSIC = MUSIC_DIR / "night_shift.ogg"
LINE_HOLD = 3.6
MILESTONE_HOLD = 4.6
# A milestone owns the subtitle briefly, then routine feedback may replace it.
MILESTONE_LOCK = 1.2
AMBIENT_GAP = 14
# NPC mouth-off gets its own HUD line, so a heckling goblin can never bury the
# hint telling you which key to press.
BARK_HOLD = 3.4
BARK_GAP = 2.2
ERIC_INVOCATIONS = [
    "As Eric foretold:",
    "By Eric's impossible beard!",
    "The old Eric-song says:",
    "Eric, who sleeps beneath the soup, whispers:",
    "According to the Seventh Extremely Reliable Legend of Eric:",
]


class Bus:
    def __init__(self):
        self.players = []
        self.forage = []
        self.clock = 0
        self.cam_forward = Vec3(0, 0, 1)
        self.cam_roll = 0
        self.subtitle = ""
        self.sub_raw = ""
        self.sub_t = 0
        self.sub_rank = 0
        self.sub_lock = 0
        self.ambient_chatter = False
        self.ambient_cd = 0
        self.bark_line = ""
        self.bark_t = 0
        self.bark_cd = 0
        self.quota = 0
        self.overflow = []
        self.meal_overflow = []
        self.enemies = []
        self.projectiles = []
        self.kills = 0
        self.enemy_spawn_timer = 0
        self.remaining = SHIFT_LEN
        self.playing = False
        self.over = False

    def say(self, msg, rank=DIALOGUE_ACTION, verbatim=False):
        """Speak a line, unless something more important is already talking."""
        if rank <= DIALOGUE_AMBIENT:
            if not self.ambient_chatter or self.ambient_cd > 0 or self.sub_t > 0:
                return False
            self.ambient_cd = AMBIENT_GAP
        elif self.sub_lock > 0 and rank < self.sub_rank:
            return False

        milestone = rank >= DIALOGUE_MILESTONE
        self.sub_rank = rank
        self.sub_t = MILESTONE_HOLD if milestone else LINE_HOLD
        self.sub_lock = MILESTONE_LOCK if milestone else 0
        # A repeat keeps the omen it was first given. Re-rolling the preamble
        # every time makes recurring events read as looping dialogue.
        if msg != self.sub_raw:
            self.sub_raw = msg
            if not verbatim and "eric" not in msg.lower():
                msg = f"{random.choice(ERIC_INVOCATIONS)} {msg}"
            self.subtitle = msg
        return True

    def bark(self, speaker, line, force=False):
        """An NPC runs its mouth in its own voice, on its own HUD line.

        Last words are forced: a goblin dying two seconds after it whined about
        its spleen should still get the punchline.
        """
        if self.bark_cd > 0 and not force:
            return False
        self.bark_line = f'{speaker}: "{line}"'
        self.bark_t = BARK_HOLD
        self.bark_cd = BARK_GAP
        return True

    @property
    def speaking(self):
        return self.sub_t > 0

    @property
    def barking(self):
        return self.bark_t > 0

    def tick_dialogue(self, dt):
        self.ambient_cd = max(0, self.ambient_cd - dt)
        self.sub_lock = max(0, self.sub_lock - dt)
        self.sub_t = max(0, self.sub_t - dt)
        if self.sub_t <= 0:
            self.sub_rank = 0
        self.bark_cd = max(0, self.bark_cd - dt)
        self.bark_t = max(0, self.bark_t - dt)
        if self.bark_t <= 0:
            self.bark_line = ""

    def standing_on_moss(self, pos):
        for f in self.forage:
            if f.kind == "gossipmoss" and (f.position - pos).length() < 1.4:
                return True
        return False


class Director(Entity):
    def __init__(self):
        # The menu has to keep taking input while the game is paused, and
        # Ursina skips paused entities entirely.
        super().__init__(ignore_paused=True)
        self.bus = Bus()
        self.world = None
        self.cauldron = None
        self.cat = None
        self.hud = []
        self.menu_bits = []
        self.end_bits = []
        self.menu_screen = None
        self.paused = False
        self.player_count = 1
        self._update_broken = False
        self.recipe_overlay = False
        self.recipe_overlay_bits = []
        self.cam_pos = Vec3(0, 14, 24)
        camera.fov = 60
        window.color = color.hsv(250, 0.45, 0.07)
        Sky(color=color.hsv(250, 0.4, 0.12), shader=portable_unlit, texture=None)
        try:
            from ursina import gamepad as _gp

            _gp.connect_all()
        except Exception:
            pass
        self.main_menu()
        play_music(TITLE_MUSIC, 0.8)

    # ------------------------------------------------------------------ menus

    def _clear_menu(self):
        for e in self.menu_bits:
            destroy_tree(e)
        self.menu_bits.clear()
        self.menu_screen = None

    def _label(self, text, y, scale=1.0, hue=40, sat=0.2, value=0.9, z=0):
        return Text(
            text=text,
            parent=camera.ui,
            y=y,
            z=z,
            origin=(0, 0),
            scale=scale,
            color=color.hsv(hue, sat, value),
            ignore_paused=True,
        )

    def _backdrop(self):
        """Dim the live scene so overlay text stays readable against the clearing."""
        return Entity(
            parent=camera.ui,
            model="quad",
            scale=(2, 1),
            z=-0.1,
            color=color.rgba32(6, 2, 14, 215),
            shader=portable_unlit,
            ignore_paused=True,
        )

    def _button(self, text, y, on_click, hue=280, sat=0.5, value=0.35, z=0):
        return Button(
            text=text,
            parent=camera.ui,
            y=y,
            z=z,
            scale=(0.55, 0.085),
            color=color.hsv(hue, sat, value),
            shader=portable_unlit,
            on_click=on_click,
            ignore_paused=True,
        )

    def main_menu(self):
        self._clear_menu()
        self.menu_bits = [
            self._label("CAULDRON COMPANY", 0.33, scale=2.2, hue=300, sat=0.4, value=1),
            self._label(
                "Friendslop for 1–2 witches. Forage. Brew. Disappoint the moon.",
                0.22,
                scale=1.1,
            ),
            self._button("PLAY", 0.06, self.play_menu),
            self._button("HOW TO PLAY", -0.04, self.controls_menu, hue=200, sat=0.45, value=0.32),
            self._button("QUIT", -0.14, quit_game, hue=0, sat=0.5, value=0.3),
            self._label(
                "Esc quits from here. During a shift, Esc pauses.",
                -0.3,
                scale=0.8,
                hue=0,
                sat=0,
                value=0.6,
            ),
        ]
        self.menu_screen = "main"

    def play_menu(self):
        self._clear_menu()
        self.menu_bits = [
            self._label("HOW MANY WITCHES?", 0.3, scale=1.8, hue=300, sat=0.4, value=1),
            self._label("Everyone shares one keyboard. That is the bit.", 0.2, scale=0.95),
            self._button("1 witch (plus a theft-based cat)", 0.05, lambda: self.start(1)),
            self._button(
                "2 witches (share the blame)",
                -0.05,
                lambda: self.start(2),
                hue=20,
                sat=0.6,
                value=0.4,
            ),
            self._button("Back", -0.17, self.main_menu, hue=250, sat=0.2, value=0.25),
        ]
        self.menu_screen = "play"

    def _column(self, text, x, y, scale=0.85, hue=0, sat=0, value=0.82, z=0):
        return Text(
            text=text,
            parent=camera.ui,
            x=x,
            y=y,
            z=z,
            origin=(-0.5, 0.5),
            scale=scale,
            color=color.hsv(hue, sat, value),
            ignore_paused=True,
        )

    def controls_menu(self):
        self._clear_menu()
        # The font is proportional, so the key table is built from three real
        # columns instead of space-padded lines.
        rows = [
            ("Move", "WASD", "Arrow keys"),
            ("Interact / dump / stir", "E", "Enter"),
            ("Broom dash", "Left Shift", "Right Shift"),
            ("Hop", "Space", "/"),
            ("Drink or eat", "F", "'"),
            ("Fire weapon", "R", "Right Ctrl"),
            ("Scritch the cat", "Q", "P"),
            ("Compliment the pot", "C", "]"),
            ("Recipe overlay", "Tab", "Tab"),
        ]
        self.menu_bits = [
            self._label("HOW TO PLAY", 0.4, scale=1.8, hue=300, sat=0.4, value=1),
            self._label(
                "Forage glowing snacks, dump two into the cauldron from its green mat,\n"
                "mash interact to stir, then run the flask to the quota crate.\n"
                "Eight points before the rooster. Known recipes pay more than sludge.",
                0.27,
                scale=0.9,
            ),
            self._column("Witch 1 (Hex)", 0.0, 0.1, hue=280, sat=0.35, value=1),
            self._column("Witch 2 (Jinx)", 0.23, 0.1, hue=20, sat=0.45, value=1),
            self._column("\n".join(r[0] for r in rows), -0.36, 0.04),
            self._column("\n".join(r[1] for r in rows), 0.0, 0.04),
            self._column("\n".join(r[2] for r in rows), 0.23, 0.04),
            self._label(
                "Tab toggles the full recipe list mid-shift. Esc pauses (Recipes there too).",
                -0.29,
                scale=0.85,
            ),
            self._button("Recipe list", -0.38, self.recipes_menu, hue=110, sat=0.45, value=0.32),
            self._button("Back", -0.48, self.main_menu, hue=250, sat=0.2, value=0.25),
        ]
        self.menu_screen = "controls"

    def recipes_menu(self, back=None):
        self._clear_menu()
        if back is None:
            back = self.controls_menu
        self.recipes_back = back
        self.menu_bits = [
            self._backdrop(),
            self._label("RECIPES", 0.46, scale=1.8, hue=300, sat=0.4, value=1, z=-0.2),
            self._column(recipe_menu_text(), 0.0, 0.38, scale=0.58, z=-0.2),
            self._button("Back", -0.46, back, hue=250, sat=0.2, value=0.25, z=-0.2),
        ]
        self.menu_screen = "recipes"

    # ------------------------------------------------------------- shift flow

    def start(self, n_players):
        self._teardown()
        play_music(SHIFT_MUSIC, 0.8)
        self.player_count = n_players
        self.bus.playing = True
        self.world = World(self.bus)
        self.cauldron = Cauldron(self.bus)
        self.bus.world = self.world
        self.bus.cauldron = self.cauldron

        # camera looks along -z, so +x renders on the left; keep Hex on the left
        spawns = [Vec3(2.5, 0, 5), Vec3(-2.5, 0, 5)]
        robes = [color.hsv(280, 0.55, 0.55), color.hsv(18, 0.7, 0.55)]
        hats = [color.hsv(280, 0.4, 0.2), color.hsv(18, 0.4, 0.18)]
        names = ["Hex", "Jinx"]
        ctrls = [P1, P2]
        for i in range(n_players):
            self.bus.players.append(
                Witch(self.bus, names[i], robes[i], hats[i], ctrls[i], spawns[i])
            )
        self.cat = Familiar(self.bus)
        log(
            f"shift started, {n_players} player(s). "
            f"cauldron at {tuple(round(v, 2) for v in self.cauldron.position)}, "
            f"crate at {tuple(round(v, 2) for v in self.world.quota.position)}, "
            f"spawns {[tuple(round(v, 2) for v in p.position) for p in self.bus.players]}"
        )
        self.bus.forage = spawn_forage(self.bus, FORAGE_COUNT)
        for _ in range(2):
            spawn_enemy(self.bus)
        self.bus.enemy_spawn_timer = 14
        self.bus.say(
            "Night shift is open. The moon wants eight points of slop. Pests are clocking in.",
            rank=DIALOGUE_MILESTONE,
        )
        self._hud()

    def _teardown(self):
        """Strip the scene back to nothing so the next shift starts clean."""
        application.paused = False
        self.paused = False
        self._clear_recipe_overlay()
        self._clear_menu()
        for e in self.end_bits:
            destroy_tree(e)
        self.end_bits.clear()
        for e in self.hud:
            destroy_tree(e)
        self.hud.clear()
        for projectile in list(self.bus.projectiles):
            projectile.remove()
        for enemy in list(self.bus.enemies):
            destroy_tree(enemy)
        for item in list(self.bus.forage):
            item.remove()
        for witch in self.bus.players:
            destroy_tree(witch)
        if self.cat:
            destroy_tree(self.cat)
            self.cat = None
        if self.cauldron:
            self.cauldron.remove()
            self.cauldron = None
        if self.world:
            self.world.destroy()
            self.world = None
        self.bus = Bus()

    def to_menu(self):
        self._teardown()
        play_music(TITLE_MUSIC, 0.8)
        self.main_menu()

    def restart(self):
        self.start(self.player_count)

    # ------------------------------------------------------------------ pause

    def toggle_pause(self):
        self.resume() if self.paused else self.pause()

    def pause(self):
        if self.paused or not self.bus.playing:
            return
        self.paused = True
        application.paused = True
        self._clear_recipe_overlay()
        self._show_pause_menu()

    def _show_pause_menu(self):
        self._clear_menu()
        self.menu_bits = [
            self._backdrop(),
            self._label("PAUSED", 0.28, scale=2.0, hue=300, sat=0.4, value=1, z=-0.2),
            self._label("The soup waits. It is patient. It is judging.", 0.19, scale=0.95, z=-0.2),
            self._button("Resume", 0.04, self.resume, z=-0.2),
            self._button("Recipes", -0.04, lambda: self.recipes_menu(self._show_pause_menu), hue=110, sat=0.45, value=0.32, z=-0.2),
            self._button("Restart shift", -0.14, self.restart, hue=200, sat=0.45, value=0.32, z=-0.2),
            self._button("Main menu", -0.24, self.to_menu, hue=250, sat=0.25, value=0.28, z=-0.2),
            self._button("Quit", -0.34, quit_game, hue=0, sat=0.5, value=0.3, z=-0.2),
        ]
        self.menu_screen = "pause"

    def resume(self):
        if not self.paused:
            return
        self._clear_menu()
        self.paused = False
        application.paused = False

    def _clear_recipe_overlay(self):
        for entity in self.recipe_overlay_bits:
            destroy_tree(entity)
        self.recipe_overlay_bits.clear()
        self.recipe_overlay = False

    def toggle_recipe_overlay(self):
        if self.recipe_overlay:
            self._clear_recipe_overlay()
            return
        self.recipe_overlay = True
        self.recipe_overlay_bits = [
            Entity(
                parent=camera.ui,
                model="quad",
                scale=(0.52, 0.92),
                x=-0.48,
                z=-0.05,
                color=color.rgba32(6, 2, 14, 210),
                shader=portable_unlit,
            ),
            Text(
                text=recipe_menu_text(),
                parent=camera.ui,
                x=-0.72,
                y=0.4,
                origin=(-0.5, 0.5),
                scale=0.5,
                color=color.hsv(50, 0.25, 0.95),
            ),
            Text(
                text="Tab close  |  Esc pause",
                parent=camera.ui,
                x=-0.72,
                y=-0.44,
                origin=(-0.5, 0),
                scale=0.62,
                color=color.hsv(0, 0, 0.65),
            ),
        ]

    def _hud(self):
        for e in self.hud:
            destroy(e)
        self.hud = []
        self._clear_recipe_overlay()
        self.txt_quota = Text(parent=camera.ui, origin=(-0.5, 0.5), position=(-0.86, 0.48), scale=1.15)
        self.txt_time = Text(parent=camera.ui, origin=(0.5, 0.5), position=(0.86, 0.48), scale=1.15)
        self.txt_goal = Text(
            parent=camera.ui,
            origin=(0, 0.5),
            position=(0, 0.48),
            scale=0.82,
            color=color.hsv(45, 0.55, 1),
        )
        self.txt_cauldron = Text(
            parent=camera.ui,
            origin=(0, 0.5),
            position=(0, 0.38),
            scale=0.72,
            color=color.hsv(110, 0.35, 0.95),
        )
        self.txt_recipes = Text(
            parent=camera.ui,
            origin=(0.5, 0.5),
            position=(0.84, 0.18),
            scale=0.48,
            color=color.hsv(200, 0.25, 0.88),
        )
        self.txt_keys = Text(
            parent=camera.ui,
            origin=(0, 0),
            position=(0, -0.44),
            scale=0.62,
            color=color.hsv(0, 0, 0.62),
        )
        self.txt_sub = Text(
            parent=camera.ui,
            origin=(0, 0),
            position=(0, -0.35),
            scale=0.95,
            color=color.hsv(50, 0.4, 1),
        )
        self.txt_bark = Text(
            parent=camera.ui,
            origin=(0, 0),
            position=(0, -0.27),
            scale=0.88,
            color=color.hsv(0, 0.45, 1),
        )
        self.txt_p1 = Text(
            parent=camera.ui, origin=(-0.5, -0.5), position=(-0.86, -0.42), scale=0.82
        )
        self.txt_p2 = Text(
            parent=camera.ui, origin=(0.5, -0.5), position=(0.86, -0.42), scale=0.82
        )
        self.hud = [
            self.txt_quota,
            self.txt_time,
            self.txt_goal,
            self.txt_cauldron,
            self.txt_recipes,
            self.txt_keys,
            self.txt_sub,
            self.txt_bark,
            self.txt_p1,
            self.txt_p2,
        ]

    def _inv(self, p):
        bits = ", ".join(i["name"] for i in p.inventory) or "pockets full of nothing"
        if p.flask:
            flask = f"{p.flask['name']} (+{p.flask['value']}) → crate"
        else:
            flask = "no flask"
        meal = p.meal["name"] if p.meal else "no meal"
        weapon = WEAPONS[p.weapon]["name"] if p.weapon else "no weapon"
        fx = ",".join(p.effects) or "sober"
        lines = (
            f"{p.display_name}: {bits} | HP {p.health}/{p.max_health}\n"
            f"{flask} | {meal} | {weapon} | {fx}"
        )
        hint = player_pair_hint(p.inventory, self.cauldron.contents if self.cauldron else [])
        if hint:
            lines += f"\n  ↳ {hint}"
        return lines

    def _flat_dist(self, a, b):
        d = a - b
        d.y = 0
        return d.length()

    def _nearest_forage(self, player, radius):
        near = [f for f in self.bus.forage if self._flat_dist(f.position, player.position) < radius]
        if not near:
            return None
        return min(near, key=lambda e: self._flat_dist(e.position, player.position))

    def _try_pickup(self, player, radius=3.4, silent=False):
        if len(player.inventory) >= 3:
            return False
        f = self._nearest_forage(player, radius)
        if not f:
            return False
        if silent:
            log(
                f"walk-over pickup: {player.display_name} got {f.spec['name']} "
                f"at {tuple(round(v, 2) for v in player.position)}"
            )
        player.inventory.append(f.as_item())
        self.bus.forage.remove(f)
        f.remove()
        if not silent:
            item = player.inventory[-1]
            pairs = format_recipe_options([item["id"]], max_items=2)
            msg = f"{player.display_name} pocketed {item['name']}."
            if pairs:
                msg += f" Pairs with: {pairs}"
            self.bus.say(msg)
        self.bus.forage.extend(spawn_forage(self.bus, 1))
        return True

    def _log_interact_state(self, player, outcome):
        pot = self.cauldron
        pot_d = self._flat_dist(player.position, pot.position)
        crate_d = self._flat_dist(player.position, self.world.quota.position)
        log(
            f"interact {player.display_name}: {outcome}\n"
            f"    pos={tuple(round(v, 2) for v in player.position)} "
            f"pot_dist={pot_d:.2f} (need {SOUP_RIM} < d < {REACH}) "
            f"in_range={pot.in_range(player)}\n"
            f"    carrying={[i['name'] for i in player.inventory]} "
            f"flask={player.flask['name'] if player.flask else None} "
            f"stun={player.stun:.2f}\n"
            f"    crate_dist={crate_d:.2f} (crate branch if < 3.2) "
            f"pot_contents={[c['name'] for c in pot.contents]} "
            f"stir={pot.stir} brew_lock={pot.brew_lock:.2f}"
        )

    def interact(self, player):
        bus = self.bus
        crate = self.world.quota
        self._log_interact_state(player, "PRESSED")
        if self._flat_dist(player.position, crate.position) < 3.2:
            if player.flask:
                bus.quota += player.flask["value"]
                bus.say(
                    f"Crate ate {player.flask['name']} (+{player.flask['value']}). "
                    f"Quota {bus.quota}/{QUOTA_GOAL}.",
                    rank=DIALOGUE_MILESTONE,
                )
                player.flask = None
                log(f"    -> delivered to crate, quota now {bus.quota}/{QUOTA_GOAL}")
                if bus.quota >= QUOTA_GOAL:
                    self._end(True)
                return
            if bus.overflow:
                player.flask = bus.overflow.pop(0)
                bus.say(f"{player.display_name} recovered spilled {player.flask['name']} from the crate.")
                log("    -> recovered overflow flask from crate")
                return
            if bus.meal_overflow and player.meal is None:
                player.meal = bus.meal_overflow.pop(0)
                bus.say(f"{player.display_name} recovered boxed {player.meal['name']} from the crate.")
                log("    -> recovered boxed meal from crate")
                return
        if self.cauldron.in_range(player) and player.inventory:
            ok = self.cauldron.dump(player)
            log(f"    -> DUMP {'ok' if ok else 'REFUSED by dump()'}")
            return
        if self.cauldron.in_range(player) and len(self.cauldron.contents) >= 2:
            self.cauldron.start_stir(player)
            log(f"    -> STIR {self.cauldron.stir}/8")
            return
        if self._try_pickup(player):
            log(f"    -> picked up {player.inventory[-1]['name']}")
            return
        if self._flat_dist(player.position, self.cat.position) < 2.2:
            self.cat.scritch(player)
            log("    -> scritched the familiar (it was closer than the cauldron)")
            return
        if self.world.chat(player):
            log("    -> talked to the hut door")
            return
        if bus.standing_on_moss(player.position):
            bus.say(random.choice(GOSSIP))
            log("    -> moss gossip")
            return
        # Nothing in reach is not worth a line. The context hint below the HUD
        # already says what to aim for.
        log("    -> nothing in reach, no action")

    def input(self, key):
        # Panda3D swallows handler tracebacks into a console the packaged app
        # does not have, which looks exactly like "the key does nothing".
        try:
            self._handle_key(key)
        except Exception:
            log(f"EXCEPTION handling key {key!r}\n{traceback.format_exc()}")

    def _handle_key(self, key):
        if key == "escape":
            if self.bus.playing:
                # Quitting the whole app on a stray Esc is brutal for a game
                # played on one shared keyboard.
                self.toggle_pause()
            elif self.menu_screen == "recipes":
                (self.recipes_back or self.controls_menu)()
            elif self.bus.over or self.menu_screen in ("play", "controls"):
                self.to_menu()
            else:
                quit_game()
            return
        if key == "tab" and self.bus.playing and not self.paused:
            self.toggle_recipe_overlay()
            return
        if self.paused:
            return
        if not self.bus.playing:
            log(f"key {key!r} ignored: not playing (menu or shift over)")
            return
        # 'x up' / 'x hold' repeats would drown the log; key-downs are enough.
        if not (key.endswith(" up") or key.endswith(" hold")):
            owners = [
                p.display_name
                for p in self.bus.players
                if key in p.controls.values()
            ]
            log(f"key {key!r} -> controls for {owners or 'nobody'}")
        for p in self.bus.players:
            c = p.controls
            if key == c["interact"] or key == f"{c.get('stick')} a":
                self.interact(p)
            elif key == c["dash"] or key == f"{c.get('stick')} b":
                p.try_dash()
            elif key == c["jump"] or key == f"{c.get('stick')} x":
                p.try_jump()
            elif key == c["drink"] or key == f"{c.get('stick')} y":
                if p.flask:
                    p.apply_effect(p.flask["effect"])
                    self.bus.say(f"{p.display_name} chugged {p.flask['name']}. Quota does not care.")
                    p.flask = None
                else:
                    if p.meal:
                        meal = p.meal
                        p.meal = None
                        p.heal(meal["healing"])
                    else:
                        self.bus.say(f"{p.display_name} drinks dew off the lawn.")
            elif key == c["scritch"]:
                self.cat.scritch(p)
            elif key == c["compliment"]:
                self.cauldron.compliment(p)
            elif key == c["fire"] or key == f"{c.get('stick')} right trigger":
                p.try_fire()

    def _end(self, won):
        self.bus.playing = False
        self.bus.over = True
        play_music(TITLE_MUSIC, 1.2)
        msg = (
            "ERIC DESCENDS FROM MYTH. THE MOON IS SATISFIED. Clock out, goblins."
            if won
            else "Eric turns his legendary face away. You are unpaid interns of failure."
        )
        self.bus.say(msg, rank=DIALOGUE_MILESTONE)
        self.end_bits = [
            self._backdrop(),
            Text(
                text="SHIFT CLEARED" if won else "SHIFT FAILED",
                parent=camera.ui,
                origin=(0, 0),
                y=0.3,
                z=-0.2,
                scale=2.0,
                color=color.hsv(50, 0.6, 1) if won else color.hsv(0, 0.7, 1),
            ),
            self._label(msg, 0.2, scale=1.0, z=-0.2),
            self._label(
                f"Moon quota: {self.bus.quota}/{QUOTA_GOAL}   |   "
                f"Night pests fired: {self.bus.kills}",
                0.12,
                scale=0.9,
                hue=0,
                sat=0,
                value=0.7,
                z=-0.2,
            ),
            self._button("Play again", -0.02, self.restart, z=-0.2),
            self._button("Main menu", -0.12, self.to_menu, hue=250, sat=0.25, value=0.28, z=-0.2),
            self._button("Quit", -0.22, quit_game, hue=0, sat=0.5, value=0.3, z=-0.2),
        ]

    def update(self):
        # One raise here kills Ursina's whole entity update loop, which freezes
        # every witch while the scene keeps rendering. Log it and keep going.
        try:
            self._update_frame()
        except Exception:
            if not self._update_broken:
                self._update_broken = True
                log(f"EXCEPTION in update loop\n{traceback.format_exc()}")

    def _update_frame(self):
        if self.paused:
            return
        dt = time.dt
        self.bus.clock += dt
        self.bus.cam_roll *= 1 - dt * 3
        if not self.bus.playing:
            return

        self.bus.remaining -= dt
        if self.bus.remaining <= 0:
            self._end(False)
            return

        self.world.update(dt)
        self.bus.enemy_spawn_timer -= dt
        if self.bus.enemy_spawn_timer <= 0 and len(self.bus.enemies) < 4:
            spawn_enemy(self.bus)
            self.bus.enemy_spawn_timer = random.uniform(12, 18)

        # walk-over forage so you do not have to pixel-hunt the interact key.
        # Silent: the inventory HUD already shows the haul, and narrating every
        # step would talk over anything worth reading.
        for p in self.bus.players:
            self._try_pickup(p, radius=1.7, silent=True)

        # camera looks north over the clearing, so the hut sits in the background
        if self.bus.players:
            mid = sum((p.position for p in self.bus.players), Vec3(0, 0, 0)) / len(self.bus.players)
        else:
            mid = Vec3(0, 0, 0)
        mid = Vec3(max(-CAM_X_LIMIT, min(CAM_X_LIMIT, mid.x)), 0, max(CAM_Z_MIN, min(CAM_Z_MAX, mid.z)))
        target = mid + Vec3(0, 0, -3)
        desired = target + Vec3(0, CAMERA_HEIGHT, CAMERA_BACK)
        self.cam_pos = lerp3(self.cam_pos, desired, min(1, dt * 3.5))
        camera.position = self.cam_pos
        camera.look_at(target + Vec3(0, 1, 0))
        camera.rotation_z = self.bus.cam_roll
        fwd = target - camera.position
        fwd.y = 0
        self.bus.cam_forward = fwd.normalized() if fwd.length() > 0.1 else Vec3(0, 0, 1)

        self.bus.tick_dialogue(dt)
        self.txt_quota.text = f"MOON QUOTA  {self.bus.quota}/{QUOTA_GOAL}"
        m, s = divmod(max(0, int(self.bus.remaining)), 60)
        self.txt_time.text = f"ROOSTER {m}:{s:02d}"
        goal = deliver_hud_text(self.bus.players)
        self.txt_goal.text = goal
        self.txt_goal.enabled = bool(goal)
        pot = self.cauldron
        self.txt_cauldron.text = cauldron_hud_text(
            pot.contents,
            pot.stir,
            pot.brew_ready,
            pot.brew_lock,
        )
        self.txt_recipes.text = hud_quick_recipes()
        self.txt_recipes.enabled = not self.recipe_overlay
        self.txt_keys.text = "Tab recipe book | Esc pause | E interact dump/stir | F drink/eat | R fire"
        if self.bus.speaking:
            hint = self.bus.subtitle
        else:
            hint = self._context_hint()
        self.txt_sub.text = hint
        self.txt_bark.text = self.bus.bark_line if self.bus.barking else ""
        self.txt_p1.text = self._inv(self.bus.players[0])
        self.txt_p2.text = (
            self._inv(self.bus.players[1])
            if len(self.bus.players) > 1
            else "cat is not a coworker"
        )

    def _context_hint(self):
        if not self.bus.players:
            return ""
        p = self.bus.players[0]
        key = "E" if p.controls["interact"] == "e" else "Enter"
        if p.stun > 0:
            return f"{p.display_name} is frozen stiff. Turn away from the screamer."
        if p.flask and self._flat_dist(p.position, self.world.quota.position) < 3.2:
            return f"{key} deliver {p.flask['name']} to the crate"
        if self.bus.overflow and self._flat_dist(p.position, self.world.quota.position) < 3.2:
            return f"{key} recover spilled {self.bus.overflow[0]['name']} from the crate"
        cauldron_ids = [c["id"] for c in self.cauldron.contents]
        if self.cauldron.in_range(p) and p.inventory:
            held = p.inventory[-1]
            if cauldron_ids:
                outcome = outcome_for_pair(cauldron_ids[0], held["id"])
                if len(cauldron_ids) >= 2:
                    outcome = outcome_for_pair(cauldron_ids[0], cauldron_ids[1])
                if outcome:
                    return f"{key} dump {held['name']} → brews {outcome}"
            return f"{key} dump {held['name']} into the cauldron"
        if self.cauldron.in_range(p) and len(self.cauldron.contents) >= 2:
            if self.cauldron.stir >= 8:
                return "Hands off! Eric says the potion is settling."
            soup = ", ".join(c["name"] for c in self.cauldron.contents[:2])
            outcome = outcome_for_pair(cauldron_ids[0], cauldron_ids[1])
            batch = f" → {outcome}" if outcome else ""
            return f"{key} stir  ({self.cauldron.stir}/8)  {soup}{batch}"
        if p.inventory:
            pot_dist = self._flat_dist(p.position, self.cauldron.position)
            held = p.inventory[-1]
            if cauldron_ids:
                outcome = outcome_for_pair(cauldron_ids[0], held["id"])
                if outcome:
                    return (
                        f"Cauldron has {self.cauldron.contents[0]['name']}. "
                        f"Bring {held['name']} → {outcome} ({pot_dist:.0f} steps)"
                    )
            pairs = format_recipe_options([held["id"]], max_items=2)
            if pot_dist < 9:
                base = f"Stand on the cauldron's mat, then {key} to dump {held['name']}"
                return f"{base} | {pairs}" if pairs else base
            base = (
                f"Carrying {held['name']}. Cauldron mat is {pot_dist:.0f} steps away"
            )
            return f"{base} | {pairs}" if pairs else base
        if self.cauldron.contents:
            soup = ", ".join(c["name"] for c in self.cauldron.contents)
            known = cauldron_ids
            snack = self._nearest_forage(p, 3.4)
            needed = needed_ingredient_id_set(known)
            if snack and snack.kind in needed:
                outcome = outcome_for_pair(known[0], snack.kind)
                if outcome:
                    return f"Cauldron: {soup} | {key} grab {snack.spec['name']} → {outcome}"
            pairs = format_recipe_options(known)
            if snack:
                return f"Cauldron: {soup} | {key} grab {snack.spec['name']}" + (
                    f" | need {pairs}" if pairs else ""
                )
            if pairs:
                return f"Cauldron: {soup} | need {pairs}"
            return f"Cauldron: {soup}   |   need 2 to stir"
        snack = self._nearest_forage(p, 3.4)
        if snack:
            pairs = format_recipe_options([snack.kind], max_items=2)
            if pairs:
                return f"{key} grab {snack.spec['name']} | pairs: {pairs}"
            return f"{key} grab {snack.spec['name']}"
        return "Wander the glowing pads. Esc → Recipes lists every combo."


def lerp3(a, b, t):
    return a + (b - a) * t


def quit_game():
    application.quit()


def play_music(track, fade_out_duration):
    """Music must never be able to take the game down.

    ursina's music_system.play() warns when a track fails to load but then
    falls through to tracks[current_track], raising KeyError. Called from
    start(), that would abort the shift before the world was even built.
    """
    try:
        music_system.play(track, fade_out_duration=fade_out_duration)
    except Exception:
        log(f"music failed for {getattr(track, 'name', track)}\n{traceback.format_exc()}")


def boot():
    banner("session start")
    log(f"log file: {log_path()}")
    log(f"cauldron reach: {SOUP_RIM} < dist < {REACH}")
    log(f"music dir {MUSIC_DIR} exists={MUSIC_DIR.is_dir()}")
    for track in (TITLE_MUSIC, SHIFT_MUSIC):
        log(f"  track {track.name} exists={track.is_file()}")
    return Director()
