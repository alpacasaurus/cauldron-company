"""Witches, the unionized familiar, and goofy status effects."""

import math
import random

from ursina import Entity, Vec3, color, destroy, held_keys, time

from witches.meshes import mesh

from witches.barks import FAMILIAR_SCRITCH, FAMILIAR_THEFT, pick
from witches.catalog import DIALOGUE_AMBIENT, DIALOGUE_MILESTONE


class Witch(Entity):
    def __init__(self, bus, name, robe, hat, controls, spawn):
        super().__init__(position=spawn, collider="box", scale=1)
        self.bus = bus
        self.display_name = name
        self.controls = controls
        self.inventory = []
        self.flask = None
        self.meal = None
        self.weapon = None
        self.weapon_cooldown = 0
        self.weapon_model = None
        self.vy = 0
        self.grounded = True
        self.stun = 0
        self.dash_cd = 0
        self.slip = Vec3(0, 0, 0)
        self.effects = {}  # name -> time left
        self.honk_t = 0
        self.base_scale = 1
        self.facing = Vec3(0, 0, 1)
        self.in_soup = False
        self.max_health = 5
        self.health = self.max_health

        self.body = Entity(
            parent=self,
            model="cube",
            color=robe,
            position=(0, 0.9, 0),
            scale=(0.7, 1.1, 0.55),
        )
        self.head = Entity(
            parent=self,
            model="sphere",
            color=color.hsv(25, 0.45, 0.92),
            position=(0, 1.7, 0),
            scale=0.62,
        )
        Entity(
            parent=self.head,
            model="sphere",
            color=color.hsv(20, 0.5, 0.8),
            position=(0, -0.05, 0.45),
            scale=(0.22, 0.22, 0.35),
        )
        self.hat = Entity(
            parent=self,
            model=mesh("cone"),
            color=hat,
            position=(0, 2.5, 0),
            scale=(0.62, 1.1, 0.62),
        )
        Entity(
            parent=self.hat,
            model="cube",
            color=hat,
            position=(0, -0.42, 0),
            scale=(1.5, 0.09, 1.5),
        )
        self.hat_base_scale = Vec3(self.hat.scale)
        self.broom = Entity(
            parent=self,
            model="cube",
            color=color.hsv(30, 0.5, 0.4),
            position=(0.5, 1.0, 0.15),
            scale=(0.09, 1.7, 0.09),
            rotation=(0, 0, 18),
        )
        Entity(
            parent=self.broom,
            model="sphere",
            color=color.hsv(42, 0.5, 0.62),
            position=(0, -0.55, 0),
            scale=(2.6, 0.22, 2.6),
        )

    def equip_weapon(self, weapon):
        from witches.combat import WEAPONS

        self.weapon = weapon
        if self.weapon_model:
            destroy(self.weapon_model)
        spec = WEAPONS[weapon]
        if weapon == "bow":
            self.weapon_model = Entity(
                parent=self,
                model="cube",
                color=spec["color"],
                position=(-0.55, 1.15, 0.3),
                scale=(0.08, 1.05, 0.08),
                rotation_z=-18,
            )
            Entity(
                parent=self.weapon_model,
                model="cube",
                color=color.hsv(40, 0.15, 0.95),
                position=(0, 0, 0.08),
                scale=(0.18, 0.9, 0.05),
            )
        else:
            self.weapon_model = Entity(
                parent=self,
                model="cube",
                color=spec["color"],
                position=(-0.48, 1.15, 0.45),
                scale=(0.18, 0.18, 0.75),
            )
        self.bus.say(f"{self.display_name} equipped the {spec['name']}. Fire away.")

    def try_fire(self):
        if not self.weapon:
            self.bus.say(f"{self.display_name} points an accusing finger. Brew a weapon first.")
            return False
        if self.weapon_cooldown > 0 or self.stun > 0:
            return False
        from witches.combat import Projectile, WEAPONS

        Projectile(self.bus, self, self.weapon)
        self.weapon_cooldown = WEAPONS[self.weapon]["cooldown"]
        return True

    def heal(self, amount):
        before = self.health
        self.health = min(self.max_health, self.health + amount)
        restored = self.health - before
        self.bus.say(
            f"{self.display_name} ate cauldron cuisine and recovered {restored} health "
            f"({self.health}/{self.max_health})."
        )
        return restored

    def take_damage(self, amount, attacker):
        self.health = max(0, self.health - amount)
        self.bus.say(
            f"{attacker} bit {self.display_name}. Health {self.health}/{self.max_health}."
        )
        if self.health <= 0:
            self.health = self.max_health
            self.position = Vec3(0, 0, 5)
            self.inventory.clear()
            self.bus.say(
                f"{self.display_name} was union-mandated back to life, but dropped their ingredients.",
                rank=DIALOGUE_MILESTONE,
            )

    def has(self, effect):
        return self.effects.get(effect, 0) > 0

    def apply_effect(self, effect, duration=12):
        self.effects[effect] = duration
        self._refresh_visuals()
        if effect == "honk":
            self.bus.say(f"{self.display_name} honks with corporate confidence.")

    def _refresh_visuals(self):
        if self.has("giant"):
            self.scale = 1.85
        elif self.has("tiny"):
            self.scale = 0.45
        else:
            self.scale = 1
        if not self.has("honk"):
            self.hat.scale = self.hat_base_scale

    def input_axes(self):
        c = self.controls
        x = (held_keys.get(c["right"], 0) - held_keys.get(c["left"], 0))
        z = (held_keys.get(c["up"], 0) - held_keys.get(c["down"], 0))
        # analog sticks
        stick = c.get("stick")
        if stick:
            x += held_keys.get(f"{stick} left stick x", 0)
            z += held_keys.get(f"{stick} left stick y", 0)
        if self.has("reverse"):
            x, z = -x, -z
        if self.has("shuffle") and random.random() < 0.02:
            x, z = -z, x
        mag = math.sqrt(x * x + z * z)
        if mag > 1:
            x, z = x / mag, z / mag
        return x, z

    def update(self):
        dt = time.dt
        self.stun = max(0, self.stun - dt)
        self.dash_cd = max(0, self.dash_cd - dt)
        self.weapon_cooldown = max(0, self.weapon_cooldown - dt)
        for k in list(self.effects):
            self.effects[k] -= dt
            if self.effects[k] <= 0:
                del self.effects[k]
                self._refresh_visuals()

        if self.has("hiccup") and random.random() < 0.015:
            self.x += random.uniform(-4, 4)
            self.z += random.uniform(-4, 4)
            self.bus.say(
                f"{self.display_name} hiccups through a hedge.", rank=DIALOGUE_AMBIENT
            )

        if self.has("honk"):
            self.honk_t += dt
            self.hat.scale = self.hat_base_scale * (1 + math.sin(self.honk_t * 12) * 0.15)

        speed = 7.5
        if self.has("sticky"):
            speed *= 0.45
        if self.has("giant"):
            speed *= 0.8
        elif self.has("tiny"):
            speed *= 1.25

        x, z = self.input_axes()
        cam_fwd = Vec3(self.bus.cam_forward.x, 0, self.bus.cam_forward.z)
        if cam_fwd.length() < 0.1:
            cam_fwd = Vec3(0, 0, 1)
        cam_fwd = cam_fwd.normalized()
        cam_right = Vec3(cam_fwd.z, 0, -cam_fwd.x)

        aim = cam_right * x + cam_fwd * z
        # A stunned witch can still turn. Looking away is the only escape from a
        # screaming intern, so freezing the facing too would be a deadlock.
        if aim.length() > 0.1:
            self.facing = aim.normalized()
            self.rotation_y = math.degrees(math.atan2(self.facing.x, self.facing.z))

        move = Vec3(0, 0, 0) if self.stun > 0 else aim
        if self.has("ice") or self.bus.standing_on_moss(self.position):
            self.slip = self.slip * (1 - dt * 0.8) + move * speed * dt * 6
            self.position += self.slip * dt
        else:
            self.slip *= 1 - dt * 8
            self.position += move * speed * dt

        # hop
        grav = 22 if not self.has("moonjump") else 8
        self.vy -= grav * dt
        self.y += self.vy * dt
        if self.y <= 0:
            self.y = 0
            self.vy = 0
            self.grounded = True
        else:
            self.grounded = False

        # world bounds
        lim = 22
        self.x = max(-lim, min(lim, self.x))
        self.z = max(-lim, min(lim, self.z))

        # crude hut collision (hut body spans z -11.6..-6.4 around x 0)
        if abs(self.x) < 2.9 and -11.8 < self.z < -6.2 and self.y < 3:
            push = Vec3(self.x, 0, self.z + 9)
            if push.length() < 0.1:
                push = Vec3(0, 0, 1)
            self.position += push.normalized() * 8 * dt

        cauldron = getattr(self.bus, "cauldron", None)
        shoved = bool(cauldron) and cauldron.keep_bodies_out(self, dt)
        if shoved and not self.in_soup:
            self.bus.say(
                f"{self.display_name} recoils. The soup has a workplace-violence policy.",
                rank=DIALOGUE_AMBIENT,
            )
        self.in_soup = shoved

        # wobble walk
        if move.length() > 0.2 and self.grounded:
            self.body.rotation_z = math.sin(time.time() * 10) * 8
        else:
            self.body.rotation_z *= 1 - dt * 8

        if self.has("spin"):
            self.rotation_y += 220 * dt
            self.bus.cam_roll = math.sin(time.time() * 3) * 12

    def try_jump(self):
        if self.grounded and self.stun <= 0:
            self.vy = 9 if not self.has("moonjump") else 16
            self.grounded = False

    def try_dash(self):
        if self.dash_cd > 0 or self.stun > 0:
            return
        self.dash_cd = 1.1
        roll = random.random()
        direction = self.facing if self.facing.length() > 0.1 else Vec3(0, 0, 1)
        if roll < 0.12:
            direction = -direction
            self.bus.say(f"{self.display_name}'s broom ghosted them. Therapy?")
        elif roll < 0.18:
            self.vy = 18
            self.bus.say(f"{self.display_name}'s broom clocked in for orbital.")
        self.position += direction.normalized() * 4
        self.slip += direction.normalized() * 10
        cauldron = getattr(self.bus, "cauldron", None)
        if cauldron:
            cauldron.keep_bodies_out(self, 0.016)


class Familiar(Entity):
    """A cat with a theft-based business model."""

    def __init__(self, bus):
        super().__init__(
            model="cube",
            color=color.hsv(30, 0.55, 0.12),
            position=(3, 0.25, 3),
            scale=(0.55, 0.35, 0.8),
            collider="box",
        )
        Entity(parent=self, model="sphere", color=self.color, position=(0, 0.35, -0.45), scale=(0.7, 0.9, 0.7))
        Entity(parent=self, model="cube", color=self.color, position=(-0.15, 0.7, -0.5), scale=(0.15, 0.4, 0.1))
        Entity(parent=self, model="cube", color=self.color, position=(0.15, 0.7, -0.5), scale=(0.15, 0.4, 0.1))
        self.bus = bus
        self.target = None
        self.steal_cd = 6
        self.yarn = 0

    def update(self):
        dt = time.dt
        self.steal_cd = max(0, self.steal_cd - dt)
        self.yarn = max(0, self.yarn - dt)
        victims = [p for p in self.bus.players if p.inventory]
        if victims and self.steal_cd <= 0:
            self.target = min(victims, key=lambda p: (p.position - self.position).length())
        elif not self.target:
            self.target = random.choice(self.bus.players) if self.bus.players else None

        if self.target:
            dest = self.target.position
            if self.yarn > 0:
                dest = Vec3(8, 0, -6)
            delta = dest - self.position
            delta.y = 0
            if delta.length() > 0.4:
                self.position += delta.normalized() * 5.5 * dt
                self.rotation_y = math.degrees(math.atan2(delta.x, delta.z))
            elif self.yarn <= 0 and self.target.inventory and self.steal_cd <= 0:
                loot = self.target.inventory.pop()
                self.bus.bark("The familiar", pick(FAMILIAR_THEFT), force=True)
                self.bus.say(
                    f"The familiar embezzled {loot['name']}. Scritch it (Q / P)!",
                    rank=DIALOGUE_MILESTONE,
                )
                self.stolen = loot
                self.steal_cd = 10

        self.y = 0.25 + abs(math.sin(time.time() * 8)) * 0.08
        cauldron = getattr(self.bus, "cauldron", None)
        if cauldron:
            cauldron.keep_bodies_out(self, dt)

    def scritch(self, player):
        if (player.position - self.position).length() > 2.2:
            return
        self.yarn = 4
        self.bus.bark("The familiar", pick(FAMILIAR_SCRITCH))
        if getattr(self, "stolen", None):
            if len(player.inventory) < 3:
                player.inventory.append(self.stolen)
                self.bus.say(f"{player.display_name} recovered {self.stolen['name']} via chin skritches.")
                self.stolen = None
                self.steal_cd = 8
            else:
                self.bus.say(f"{player.display_name}'s pockets are full. The familiar keeps the evidence.")
        else:
            self.bus.say("The familiar accepts tribute. It will consider not suing.")
