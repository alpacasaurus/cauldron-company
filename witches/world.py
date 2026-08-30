"""Hut, woods, lights, quota crate, talking door."""

import math
import random
from pathlib import Path

from ursina import Entity, Vec3, color, load_texture

from witches.barks import HUT_BARKS, pick
from witches.catalog import HUT_LINES
from witches.meshes import mesh
from witches.teardown import destroy_tree

TEXTURE_DIR = Path(__file__).resolve().parent / "assets" / "textures"


class World:
    def __init__(self, bus):
        self.bus = bus
        self.trees = []
        self.hut_lines_cd = 0
        # Every top-level entity is tracked so returning to the menu can strip
        # the clearing completely instead of stacking a second one on top.
        self.entities = []

        self._track(
            Entity(
                model="plane",
                scale=120,
                texture=load_texture("forest_ground", TEXTURE_DIR),
                texture_scale=(18, 18),
                color=color.rgba32(170, 190, 175, 255),
                collider="box",
            )
        )
        # dirt ring around the hut
        self._track(
            Entity(
                model=mesh("circle"),
                rotation_x=90,
                y=0.02,
                scale=22,
                texture=load_texture("dirt_clearing", TEXTURE_DIR),
                texture_scale=(5, 5),
                color=color.rgba32(205, 185, 160, 255),
            )
        )

        self._build_hut()
        self._plant_woods()
        self._fence_mushrooms()
        self.quota = self._track(
            Entity(
                model="cube",
                color=color.hsv(40, 0.7, 0.42),
                position=(6.5, 0.55, 2.5),
                scale=(1.6, 1.1, 1.2),
                collider="box",
            )
        )
        Entity(
            parent=self.quota,
            model="cube",
            color=color.hsv(45, 0.8, 0.15),
            position=(0, 0.62, 0),
            scale=(1.05, 0.12, 0.7),
        )
        # moon
        self._track(
            Entity(
                model="sphere",
                color=color.hsv(50, 0.1, 1),
                position=(18, 28, -22),
                scale=6,
                unlit=True,
            )
        )

    def _track(self, entity):
        self.entities.append(entity)
        return entity

    def _build_hut(self):
        self.hut = self._track(Entity(position=(0, 0, -9)))
        Entity(
            parent=self.hut,
            model="cube",
            texture=load_texture("hut_wood", TEXTURE_DIR),
            texture_scale=(2, 1),
            color=color.rgba32(210, 190, 175, 255),
            position=(0, 1.6, 0),
            scale=(5.2, 3.2, 5.2),
            collider="box",
        )
        Entity(
            parent=self.hut,
            model=mesh("cone"),
            color=color.hsv(345, 0.65, 0.45),
            position=(0, 4.3, 0),
            scale=(6.4, 2.8, 6.4),
        )
        self.door = Entity(
            parent=self.hut,
            model="cube",
            color=color.hsv(20, 0.6, 0.18),
            position=(0, 1.1, 2.62),
            scale=(1.4, 2.2, 0.15),
        )
        self.door_mouth = Entity(
            parent=self.door,
            model="cube",
            color=color.hsv(0, 0.7, 0.35),
            position=(0, -0.15, 0.2),
            scale=(0.7, 0.18, 0.2),
        )
        # glowing windows
        for x in (-1.6, 1.6):
            Entity(
                parent=self.hut,
                model="cube",
                color=color.hsv(40, 0.8, 1),
                position=(x, 1.7, 2.62),
                scale=(0.8, 0.8, 0.12),
                unlit=True,
            )
        # chimney
        Entity(
            parent=self.hut,
            model="cube",
            color=color.hsv(0, 0.05, 0.25),
            position=(1.8, 4.6, -1.4),
            scale=(0.7, 1.6, 0.7),
        )

    def _plant_woods(self):
        rng = random.Random(13)
        for _ in range(55):
            ang = rng.random() * math.tau
            dist = rng.uniform(16, 42)
            pos = Vec3(math.cos(ang) * dist, 0, math.sin(ang) * dist)
            if pos.length() < 14:
                continue
            trunk = self._track(
                Entity(
                    model=mesh("cylinder"),
                    color=color.hsv(25, 0.55, rng.uniform(0.18, 0.32)),
                    position=pos + Vec3(0, 1.6, 0),
                    scale=(rng.uniform(0.5, 1.0), 3.4, rng.uniform(0.5, 1.0)),
                    collider="box",
                )
            )
            self._track(
                Entity(
                    model="sphere",
                    color=color.hsv(rng.uniform(95, 155), 0.5, rng.uniform(0.42, 0.62)),
                    position=pos + Vec3(0, 4.1, 0),
                    scale=rng.uniform(2.2, 3.6),
                )
            )
            self.trees.append(trunk)

        # a few dead snags closer in
        for _ in range(8):
            ang = rng.random() * math.tau
            dist = rng.uniform(10, 15)
            pos = Vec3(math.cos(ang) * dist, 0.9, math.sin(ang) * dist)
            self._track(
                Entity(
                    model=mesh("cylinder"),
                    color=color.hsv(20, 0.3, 0.2),
                    position=pos,
                    scale=(0.25, 1.8, 0.25),
                    rotation=(rng.uniform(-20, 20), rng.uniform(0, 360), 0),
                )
            )

    def _fence_mushrooms(self):
        for i in range(18):
            a = i / 18 * math.tau
            r = 12.5
            self._track(
                Entity(
                    model=mesh("cylinder"),
                    color=color.hsv(20, 0.4, 0.85),
                    position=(math.cos(a) * r, 0.2, math.sin(a) * r),
                    scale=(0.12, 0.4, 0.12),
                )
            )
            self._track(
                Entity(
                    model="sphere",
                    color=color.hsv(350, 0.5, 0.45) if i % 2 == 0 else color.hsv(50, 0.5, 0.5),
                    position=(math.cos(a) * r, 0.5, math.sin(a) * r),
                    scale=0.3,
                )
            )

    def chat(self, player):
        """Knock on the door. The hut answers, if it is done sulking."""
        if (player.position - self.door.world_position).length() >= 4:
            return False
        if self.hut_lines_cd > 0:
            return False
        self.hut_lines_cd = 2
        # The door speaks for itself when the bark line is free, and falls back
        # to a narrated Eric omen when a louder NPC is already using it.
        if not self.bus.bark("The hut door", pick(HUT_BARKS)):
            self.bus.say(random.choice(HUT_LINES))
        return True

    def update(self, dt):
        self.hut_lines_cd = max(0, self.hut_lines_cd - dt)
        # door chews
        self.door_mouth.scale_y = 0.18 + math.sin(self.bus.clock * 3) * 0.08

    def destroy(self):
        for entity in self.entities:
            destroy_tree(entity)
        self.entities.clear()
        self.trees.clear()
