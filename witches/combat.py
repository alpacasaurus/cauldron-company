"""Cauldron-made weapons, projectiles, and disposable night creatures."""

import math
import random

from ursina import Entity, Vec3, color, destroy, time

from witches.barks import (
    ENEMY_ATTACK,
    ENEMY_DEATH,
    ENEMY_HURT,
    ENEMY_SPOTTED,
    pick,
)
from witches.catalog import DIALOGUE_AMBIENT, DIALOGUE_MILESTONE
from witches.map import ENEMY_SPAWN_MAX, ENEMY_SPAWN_MIN


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

    def __init__(self, bus, position):
        super().__init__(
            model="cube",
            color=color.hsv(random.choice((0, 15, 95, 275)), 0.72, 0.62),
            position=position,
            scale=(0.8, 1.35, 0.7),
            collider="box",
        )
        self.bus = bus
        self.display_name = random.choice(self.NAMES)
        self.hp = 2
        self.dead = False
        self.attack_cd = 0
        # Stagger the opening insult so a fresh pair does not shout in unison.
        self.heckle_cd = random.uniform(0.5, 3.0)
        Entity(
            parent=self,
            model="sphere",
            color=color.hsv(35, 0.35, 0.8),
            position=(0, 0.72, 0),
            scale=0.7,
        )
        bus.enemies.append(self)

    def hit(self, damage, owner):
        if self.dead:
            return
        self.hp -= damage
        self.scale *= 1.12
        if self.hp > 0:
            self.bus.bark(self.display_name, pick(ENEMY_HURT))
        else:
            self.dead = True
            if self in self.bus.enemies:
                self.bus.enemies.remove(self)
            self.bus.kills += 1
            self.bus.bark(self.display_name, pick(ENEMY_DEATH), force=True)
            self.bus.say(
                f"{owner.display_name} fired {self.display_name} from employment. "
                f"Night pests defeated: {self.bus.kills}.",
                rank=DIALOGUE_MILESTONE,
            )
            destroy(self)

    def update(self):
        if self.dead or not self.bus.playing or not self.bus.players:
            return
        dt = time.dt
        self.attack_cd = max(0, self.attack_cd - dt)
        self.heckle_cd = max(0, self.heckle_cd - dt)
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
