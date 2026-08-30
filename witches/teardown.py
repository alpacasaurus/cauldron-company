"""Scene cleanup shared by the menu flow.

Ursina's destroy() detaches an entity's Panda3D node but leaves its child
entities in scene.entities forever, so every discarded hut, witch, and mushroom
would pile up in the update loop each time a shift restarts.
"""

from ursina import destroy


def destroy_tree(entity):
    """Destroy an entity along with every child it owns."""
    if not entity:
        return
    for child in list(getattr(entity, "children", [])):
        destroy_tree(child)
    destroy(entity)
