"""Procedural meshes Ursina does not ship as named files."""

import math

from ursina import Cone, Cylinder, Mesh


def textured_circle(resolution=24):
    """A flat disc with UVs, unlike Ursina's built-in ngon Circle."""
    vertices = [(0, 0, 0)]
    uvs = [(0.5, 0.5)]
    for i in range(resolution):
        angle = math.tau * i / resolution
        x, y = math.sin(angle) * 0.5, math.cos(angle) * 0.5
        vertices.append((x, y, 0))
        uvs.append((x + 0.5, y + 0.5))
    triangles = [
        (0, ((i + 1) % resolution) + 1, i + 1)
        for i in range(resolution)
    ]
    return Mesh(vertices=vertices, triangles=triangles, uvs=uvs, mode="triangle")


def mesh(name):
    if name == "cone":
        return Cone(8)
    if name == "cylinder":
        return Cylinder(12, start=-0.5)
    if name == "circle":
        return textured_circle()
    return name
