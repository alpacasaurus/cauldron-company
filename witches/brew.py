"""Cauldron mood, stirring, and legally distinct potions."""

import random

from ursina import Entity, Vec3, color, time

from witches.meshes import mesh

from witches.barks import CAULDRON_COMPLIMENT, CAULDRON_REFUSAL, pick
from witches.teardown import destroy_tree
from witches.catalog import (
    DIALOGUE_MILESTONE,
    EFFECTS,
    FOOD_RECIPES,
    POTION_PREFIX,
    POTION_SUFFIX,
    RECIPES,
    WEAPON_RECIPES,
)


# The pot is a big object viewed from a steep camera, so depth is easy to
# misjudge. Reach generously and draw the zone on the ground.
SOUP_RIM = 1.35
REACH = 4.2


class Cauldron(Entity):
    def __init__(self, bus):
        super().__init__(position=(0, 0, -1.5))
        self.bus = bus
        self.contents = []
        self.stir = 0
        self.stir_window = 0
        self.brew_ready = 0
        self.stirrer = None
        self.mood = 0.5
        self.brew_lock = 0
        self.last_dump = []

        Entity(
            parent=self,
            model=mesh("cylinder"),
            color=color.hsv(80, 0.2, 0.12),
            position=(0, 0.55, 0),
            scale=(1.6, 1.1, 1.6),
        )
        self.soup = Entity(
            parent=self,
            model=mesh("cylinder"),
            color=color.hsv(120, 0.8, 0.45),
            position=(0, 1.05, 0),
            scale=(1.35, 0.15, 1.35),
        )
        Entity(
            parent=self,
            model="cube",
            color=color.hsv(25, 0.5, 0.25),
            position=(0, 0.15, 0),
            scale=(0.35, 0.4, 0.35),
        )
        # Spilled-slop mat marking where the pot can be worked from. It brightens
        # while a witch is in reach, so "why is E doing nothing" is answerable at
        # a glance.
        self.mat = Entity(
            model=mesh("circle"),
            rotation_x=90,
            position=(self.x, 0.05, self.z),
            scale=REACH * 2,
            color=color.hsv(110, 0.45, 0.22),
            unlit=True,
        )
        # compliment aura
        self.heart = Entity(
            parent=self,
            model="sphere",
            color=color.hsv(320, 0.6, 1),
            position=(0, 2.2, 0),
            scale=0.15,
        )

    def remove(self):
        """The reach mat lives in the scene, not on the pot, so it needs killing too."""
        destroy_tree(self.mat)
        destroy_tree(self)

    def in_range(self, player):
        """Close enough to dump or stir, but still outside the soup."""
        delta = player.position - self.position
        delta.y = 0
        return SOUP_RIM < delta.length() < REACH

    def keep_bodies_out(self, entity, dt):
        """The pot is boiling. Nobody stands in it — OSHA, and also the soup."""
        delta = entity.position - self.position
        delta.y = 0
        dist = delta.length()
        rim = 1.45
        if dist >= rim:
            return False
        if dist < 0.05:
            delta = Vec3(0, 0, 1)
            dist = 1
        entity.x = self.x + delta.x / dist * rim
        entity.z = self.z + delta.z / dist * rim
        if hasattr(entity, "slip"):
            entity.slip -= delta.normalized() * 4
        return True

    def dump(self, player):
        if not player.inventory or not self.in_range(player):
            return False
        item = player.inventory.pop()
        self.contents.append(item)
        self.last_dump.append((player, time.time()))
        self.mood = min(1, self.mood + 0.08)
        self.soup.color = color.hsv(random.uniform(80, 160), 0.8, 0.5)
        self.bus.say(f"{player.display_name} yeeted {item['name']} into the gossip pot.")
        return True

    def compliment(self, player):
        if not self.in_range(player):
            return
        self.mood = min(1, self.mood + 0.2)
        if not self.bus.bark("The cauldron", pick(CAULDRON_COMPLIMENT)):
            self.bus.say("The cauldron blushes. 'Stop. I look like a pot.'")

    def start_stir(self, player):
        if not self.in_range(player):
            return
        if self.brew_lock > 0:
            self.bus.say("Eric commands patience. The cauldron is still cooling down.")
            return
        if len(self.contents) < 2:
            if not self.bus.bark("The cauldron", pick(CAULDRON_REFUSAL)):
                self.bus.say("The cauldron yawns. 'That's not a recipe, that's a snack.'")
            return
        self.stir += 1
        self.stir_window = 3.5
        self.soup.scale_y = 0.15 + min(self.stir, 12) * 0.02
        if self.stir >= 20:
            self._tantrum()
        elif self.stir >= 8:
            self.brew_ready = 0.65
            self.stirrer = player
            self.bus.say("Eric says STOP STIRRING. Let the potion settle!")

    def _friendship(self):
        now = time.time()
        recent = [p for p, t in self.last_dump if now - t < 4]
        return len({id(p) for p in recent}) >= 2

    def _brew(self, player):
        if self.brew_lock > 0:
            return
        ids = [c["id"] for c in self.contents]
        key = frozenset(ids[:2]) if len(ids) == 2 else frozenset(ids)
        food = FOOD_RECIPES.get(key)
        if not food and len(set(ids)) >= 2:
            food = FOOD_RECIPES.get(frozenset(list(dict.fromkeys(ids))[:2]))
        if food:
            name, healing = food
            eaters = [p for p in self.bus.players if self.in_range(p) and p.meal is None]
            lucky = eaters[0] if eaters else player
            meal = {"name": name, "healing": healing}
            if lucky.meal is None:
                lucky.meal = meal
                destination = f"{lucky.display_name}'s lunch pocket"
            else:
                self.bus.meal_overflow.append(meal)
                destination = "a takeaway box by the quota crate"
            self.bus.say(
                f"Cooked {name} (+{healing} health) into {destination}.",
                rank=DIALOGUE_MILESTONE,
            )
            self._reset_batch()
            return

        weapon = WEAPON_RECIPES.get(key)
        if not weapon and len(set(ids)) >= 2:
            weapon = WEAPON_RECIPES.get(frozenset(list(dict.fromkeys(ids))[:2]))
        if weapon:
            from witches.combat import WEAPONS

            wielders = [p for p in self.bus.players if self.in_range(p)]
            lucky = wielders[0] if wielders else player
            lucky.equip_weapon(weapon)
            self.bus.say(
                f"The cauldron coughed up a {WEAPONS[weapon]['name']} for {lucky.display_name}.",
                rank=DIALOGUE_MILESTONE,
            )
            self._reset_batch()
            return

        # try exact 2-set of first two unique
        recipe = None
        if len(ids) >= 2:
            recipe = RECIPES.get(frozenset(ids[:2]))
            if not recipe and len(set(ids)) >= 2:
                recipe = RECIPES.get(frozenset(list(dict.fromkeys(ids))[:2]))

        friends = self._friendship() and len(self.bus.players) > 1
        if recipe:
            name, effect, value = recipe
        else:
            name = f"{random.choice(POTION_PREFIX)} {random.choice(POTION_SUFFIX)}"
            effect = random.choice(EFFECTS)
            value = 1 + int(self.mood > 0.75)

        if friends:
            name = f"Besties {name}"
            value += 2
            self.bus.say("Synchronized dumping detected. HR hates this energy.")

        if self.mood < 0.25:
            name = f"Spiteful {name}"
            if not recipe:
                effect = random.choice(EFFECTS)
            value = max(1, value - 1)
            self.bus.say("You forgot to compliment the cauldron. It sabotaged the batch.")

        potion = {"name": name, "effect": effect, "value": value}
        # give flask to nearest witch without one, else stirrer
        holders = [p for p in self.bus.players if self.in_range(p) and p.flask is None]
        lucky = holders[0] if holders else player
        if lucky.flask:
            self.bus.overflow.append(potion)
            self.bus.say(
                f"{name} splashed into a spare bottle by the quota crate!",
                rank=DIALOGUE_MILESTONE,
            )
        else:
            lucky.flask = potion
            self.bus.say(
                f"Bottled {name}. Deliver it (crate) or drink it like a coward.",
                rank=DIALOGUE_MILESTONE,
            )

        self._reset_batch()

    def _reset_batch(self):
        self.contents.clear()
        self.stir = 0
        self.stir_window = 0
        self.brew_ready = 0
        self.stirrer = None
        self.brew_lock = 1.2
        self.mood *= 0.7
        self.soup.color = color.hsv(140, 0.7, 0.35)
        self.soup.scale_y = 0.15

    def _tantrum(self):
        self.bus.say(
            "The cauldron got dizzy and filed a workplace incident.",
            rank=DIALOGUE_MILESTONE,
        )
        for p in self.bus.players:
            away = p.position - self.position
            away.y = 0
            if away.length() < 0.1:
                away = Vec3(0, 0, 1)
            p.slip += away.normalized() * 28
            p.vy = 12
        self.contents.clear()
        self.stir = 0
        self.brew_ready = 0
        self.stirrer = None
        self.mood = 0.1
        self.soup.color = color.hsv(0, 0.8, 0.5)

    def update(self):
        dt = time.dt
        self.brew_lock = max(0, self.brew_lock - dt)
        if self.brew_ready > 0:
            self.brew_ready -= dt
            if self.brew_ready <= 0 and 8 <= self.stir < 20 and self.contents:
                self._brew(self.stirrer)
        if self.stir_window > 0:
            self.stir_window -= dt
            if self.stir_window <= 0:
                self.stir = 0
                self.bus.say("Stirring fizzled. The soup unclenched.")
        reachable = any(self.in_range(p) for p in self.bus.players)
        self.mat.color = color.hsv(110, 0.5, 0.42 if reachable else 0.28)
        self.soup.y = 1.05 + abs(time.time() * 2 % 2 - 1) * 0.08
        self.heart.scale = 0.12 + self.mood * 0.25
        self.heart.y = 2.0 + self.mood * 0.4
        # mood decay if ignored
        if self.contents:
            self.mood = max(0, self.mood - dt * 0.02)
