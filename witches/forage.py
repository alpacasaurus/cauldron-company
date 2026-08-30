"""Forageables with cowardice, screaming, and poor labor practices."""

import math
import random

from ursina import Entity, Vec3, color, time

from witches.catalog import INGREDIENTS
from witches.glfix import portable_unlit
from witches.iconart import ensure_hud_icons, icon_texture
from witches.map import FORAGE_COUNT, FORAGE_MAX, FORAGE_MIN, HUB_RADIUS, MAP_LIMIT, forage_spawn_ok
from witches.meshes import mesh
from witches.teardown import destroy_tree

FORAGE_SPRITE_SCALE = 1.25


class Forage(Entity):
    def __init__(self, bus, kind, position):
        spec = INGREDIENTS[kind]
        ensure_hud_icons()
        self.sprite_scale = FORAGE_SPRITE_SCALE
        super().__init__(
            model="quad",
            texture=icon_texture(kind),
            color=color.white,
            position=position,
            scale=self.sprite_scale,
            collider="box",
            unlit=True,
            shader=portable_unlit,
            billboard=True,
            double_sided=True,
        )
        self.bus = bus
        self.kind = kind
        self.spec = spec
        self.behavior = spec["behavior"]
        self.base_y = 0.4
        self.phase = random.random() * math.tau
        self.y = self.base_y
        self.scream_cd = 0
        # A ground pad so small pickups read against the dark grass. It lives in
        # the scene rather than as a child so the item's bob and spin don't drag
        # it into the air.
        self.pad = Entity(
            model=mesh("circle"),
            color=spec["color"].tint(0.25),
            rotation_x=90,
            position=(position.x, 0.06, position.z),
            scale=1.5,
            unlit=True,
        )

    def as_item(self):
        return {"id": self.kind, "name": self.spec["name"]}

    def remove(self):
        """Take the pickup, its glow, and its ground pad out of the scene together."""
        destroy_tree(self.pad)
        destroy_tree(self)

    def update(self):
        dt = time.dt
        self.phase += dt
        self.scream_cd = max(0, self.scream_cd - dt)
        self.y = self.base_y + math.sin(self.phase * 2.2) * 0.08
        self.rotation_y += 20 * dt

        players = self.bus.players
        if not players:
            return
        nearest = min(players, key=lambda p: (p.position - self.position).length())
        delta = nearest.position - self.position
        delta.y = 0
        dist = delta.length()

        if self.behavior == "flee" and dist < 7:
            self.position -= delta.normalized() * 3.5 * dt
            self.y = self.base_y
        elif self.behavior == "hop":
            self.y = self.base_y + abs(math.sin(self.phase * 6)) * 0.55
            if dist < 6:
                self.position += Vec3(-delta.z, 0, delta.x).normalized() * 2 * dt
        elif self.behavior == "roll":
            self.rotation_x += 90 * dt
            if dist < 8:
                # rolls toward the cat energy (hut) then away
                self.position += Vec3(delta.z, 0, -delta.x).normalized() * 2.5 * dt
        elif self.behavior == "scream" and dist < 3.5:
            # Goes hoarse between screams, so proximity can never hold a witch
            # frozen forever.
            if self.scream_cd <= 0:
                nearest.stun = max(nearest.stun, 0.35)
                self.scream_cd = 2.2
            pulse = 1.0 + math.sin(self.phase * 20) * 0.12
            self.scale = self.sprite_scale * pulse
        elif self.behavior == "scream":
            self.scale = self.sprite_scale
        elif self.behavior == "shy":
            # mandrake intern: screams if you FACE it
            toward_mandrake = -delta.normalized()
            eye_contact = dist < 5 and dist > 0.2 and nearest.facing.dot(toward_mandrake) > 0.55
            if eye_contact and self.scream_cd <= 0:
                nearest.stun = max(nearest.stun, 0.8)
                self.scream_cd = 3.0
                self.bus.say("The intern files a scream with HR.")

        # stay in woods-ish bounds
        if self.position.xz.length() < HUB_RADIUS:
            self.position *= 1.02
        self.x = max(-MAP_LIMIT, min(MAP_LIMIT, self.x))
        self.z = max(-MAP_LIMIT, min(MAP_LIMIT, self.z))
        self.pad.x, self.pad.z = self.x, self.z


def spawn_forage(bus, n=FORAGE_COUNT):
    kinds = list(INGREDIENTS.keys())
    out = []
    for _ in range(n):
        for _try in range(24):
            ang = random.random() * math.tau
            dist = random.uniform(FORAGE_MIN, FORAGE_MAX)
            pos = Vec3(math.cos(ang) * dist, 0.4, math.sin(ang) * dist)
            if forage_spawn_ok(pos):
                break
        out.append(Forage(bus, random.choice(kinds), pos))
    return out
