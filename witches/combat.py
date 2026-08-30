"""Cauldron-made weapons, projectiles, and disposable night creatures."""

import math
import random

from ursina import Entity, Text, Vec3, color, destroy, time

from witches.barks import (
    ENEMY_ATTACK,
    ENEMY_DEATH,
    ENEMY_HURT,
    ENEMY_SPOTTED,
    pick,
)
from witches.catalog import DIALOGUE_AMBIENT, DIALOGUE_MILESTONE
from witches.glfix import portable_unlit
from witches.iconart import ensure_hud_icons, icon_texture
from witches.map import ENEMY_SPAWN_MAX, ENEMY_SPAWN_MIN
from witches.meshes import mesh


WEAPONS = {
    "bow": {
        "name": "Union Bow",
        "cooldown": 0.55,
        "damage": 1,
        "speed": 19,
        "range": 18,
        "color": color.hsv(35, 0.75, 0.72),
    },
    "pistol": {
        "name": "Dewpoint Pistol",
        "cooldown": 0.28,
        "damage": 1,
        "speed": 29,
        "range": 20,
        "color": color.hsv(190, 0.65, 1),
    },
}

BROOM = {
    "name": "Work Broom",
    "cooldown": 0.62,
    "damage": 1,
    "reach": 2.85,
    "arc": 110,
    "swing_time": 0.28,
}


def broom_targets(bus, owner):
    """Enemies standing in the broom arc in front of the witch."""
    half = math.radians(BROOM["arc"] / 2)
    cos_limit = math.cos(half)
    forward = Vec3(owner.facing)
    forward.y = 0
    if forward.length() < 0.1:
        forward = Vec3(0, 0, 1)
    forward = forward.normalized()
    hits = []
    for enemy in list(bus.enemies):
        if enemy.dead:
            continue
        delta = enemy.position - owner.position
        delta.y = 0
        dist = delta.length()
        if dist > BROOM["reach"] or dist < 0.25:
            continue
        if forward.dot(delta.normalized()) >= cos_limit:
            hits.append(enemy)
    return hits


def try_broom_sweep(bus, owner):
    hits = broom_targets(bus, owner)
    for enemy in hits:
        enemy.hit(BROOM["damage"], owner)
    return hits


class Projectile(Entity):
    def __init__(self, bus, owner, weapon):
        spec = WEAPONS[weapon]
        direction = Vec3(owner.facing)
        direction.y = 0
        if direction.length() < 0.1:
            direction = Vec3(0, 0, 1)
        direction = direction.normalized()
        is_arrow = weapon == "bow"
        super().__init__(
            model="cube",
            color=spec["color"],
            position=owner.position + direction * 0.9 + Vec3(0, 1.15, 0),
            scale=(0.07, 0.07, 0.8 if is_arrow else 0.2),
            rotation_y=math.degrees(math.atan2(direction.x, direction.z)),
            unlit=True,
        )
        self.bus = bus
        self.owner = owner
        self.weapon = weapon
        self.velocity = direction * spec["speed"]
        self.distance_left = spec["range"]
        self.damage = spec["damage"]
        bus.projectiles.append(self)

    def remove(self):
        if self in self.bus.projectiles:
            self.bus.projectiles.remove(self)
        destroy(self)

    def update(self):
        dt = time.dt
        step = self.velocity * dt
        self.position += step
        self.distance_left -= step.length()
        for enemy in list(self.bus.enemies):
            if not enemy.dead and (enemy.position + Vec3(0, 0.7, 0) - self.position).length() < 0.9:
                enemy.hit(self.damage, self.owner)
                self.remove()
                return
        if self.distance_left <= 0:
            self.remove()


class Enemy(Entity):
    """A small melee nuisance that exists to be dramatically perforated."""

    NAMES = ["Tax Goblin", "Moon Rat", "Compliance Imp", "Soup Auditor"]
    HOSTILE_HUES = (0, 5, 350, 345)

    def __init__(self, bus, position):
        hue = random.choice(self.HOSTILE_HUES)
        body = color.hsv(hue, 0.82, 0.52)
        super().__init__(
            model="cube",
            color=body,
            position=position,
            scale=(0.75, 1.15, 0.62),
            collider="box",
            unlit=True,
        )
        self.bus = bus
        self.display_name = random.choice(self.NAMES)
        self.hp = 2
        self.dead = False
        self.attack_cd = 0
        self.heckle_cd = random.uniform(0.5, 3.0)
        self.pulse_t = random.random() * math.tau

        Entity(
            parent=self,
            model="sphere",
            color=color.hsv(hue, 0.65, 0.42),
            position=(0, 0.62, 0),
            scale=0.62,
            unlit=True,
        )
        for x in (-0.17, 0.17):
            Entity(
                parent=self,
                model="sphere",
                color=color.hsv(0, 0.95, 1),
                position=(x, 0.68, 0.28),
                scale=0.11,
                unlit=True,
            )
        for x, tilt in ((-0.14, 18), (0.14, -18)):
            Entity(
                parent=self,
                model=mesh("cone"),
                color=color.hsv(hue, 0.55, 0.32),
                position=(x, 0.92, 0),
                scale=(0.11, 0.22, 0.11),
                rotation_z=tilt,
                unlit=True,
            )

        self.aura = Entity(
            model=mesh("circle"),
            color=color.hsv(0, 0.8, 0.85),
            rotation_x=90,
            position=(position.x, 0.05, position.z),
            scale=1.45,
            unlit=True,
        )
        ensure_hud_icons()
        self.marker = Entity(
            model="quad",
            texture=icon_texture("warning"),
            color=color.white,
            billboard=True,
            double_sided=True,
            position=(position.x, 1.55, position.z),
            scale=0.32,
            shader=portable_unlit,
            unlit=True,
        )
        self.label = Text(
            text=f"FOE  {self.display_name}",
            origin=(0, 0),
            scale=0.55,
            color=color.hsv(0, 0.85, 1),
            background=True,
            billboard=True,
            position=(position.x, 1.85, position.z),
        )
        bus.enemies.append(self)

    def remove(self):
        if self in self.bus.enemies:
            self.bus.enemies.remove(self)
        for extra in (self.aura, self.marker, self.label):
            if extra:
                destroy(extra)
        destroy(self)

    def hit(self, damage, owner):
        if self.dead:
            return
        self.hp -= damage
        self.scale *= 1.12
        if self.hp > 0:
            self.bus.bark(self.display_name, pick(ENEMY_HURT))
        else:
            self.dead = True
            self.bus.kills += 1
            self.bus.bark(self.display_name, pick(ENEMY_DEATH), force=True)
            verb = "fired" if owner.weapon else "swatted"
            self.bus.say(
                f"{owner.display_name} {verb} {self.display_name} from employment. "
                f"Night pests defeated: {self.bus.kills}.",
                rank=DIALOGUE_MILESTONE,
            )
            self.remove()

    def update(self):
        if self.dead or not self.bus.playing or not self.bus.players:
            return
        dt = time.dt
        self.attack_cd = max(0, self.attack_cd - dt)
        self.heckle_cd = max(0, self.heckle_cd - dt)
        self.pulse_t += dt * 5
        pulse = 1.0 + math.sin(self.pulse_t) * 0.1
        self.aura.position = Vec3(self.x, 0.05, self.z)
        self.aura.scale = 1.45 * pulse
        self.aura.color = color.hsv(0, 0.8, 0.65 + pulse * 0.25)
        self.marker.position = Vec3(self.x, 1.55, self.z)
        self.label.position = Vec3(self.x, 1.85, self.z)
        target = min(
            self.bus.players,
            key=lambda player: (player.position - self.position).length(),
        )
        delta = target.position - self.position
        delta.y = 0
        distance = delta.length()
        if distance < 8 and self.heckle_cd <= 0:
            self.heckle_cd = random.uniform(9, 16)
            self.bus.bark(self.display_name, pick(ENEMY_SPOTTED))
        if distance > 1.15:
            direction = delta.normalized()
            self.position += direction * 1.25 * dt
            self.rotation_y = math.degrees(math.atan2(direction.x, direction.z))
        elif self.attack_cd <= 0:
            target.take_damage(1, self.display_name)
            target.stun = max(target.stun, 0.45)
            away = target.position - self.position
            away.y = 0
            target.slip += (away.normalized() if away.length() > 0.1 else Vec3(0, 0, 1)) * 4
            self.attack_cd = 3.5
            self.heckle_cd = max(self.heckle_cd, 4)
            self.bus.bark(self.display_name, pick(ENEMY_ATTACK), force=True)
            self.bus.say(
                f"{self.display_name} issued {target.display_name} a bite-sized warning.",
                rank=DIALOGUE_AMBIENT,
            )


def spawn_enemy(bus):
    angle = random.uniform(0, math.tau)
    radius = random.uniform(ENEMY_SPAWN_MIN, ENEMY_SPAWN_MAX)
    return Enemy(bus, Vec3(math.cos(angle) * radius, 0.65, math.sin(angle) * radius))
