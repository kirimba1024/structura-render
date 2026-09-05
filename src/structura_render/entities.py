"""Entities a structure carries, drawn as geometry.

Structure NBT keeps paintings, item frames and mobs in `entities`, apart from
`blocks`, and nothing here ever read that list -- so a capture's paintings and
item frames rendered as empty air with nothing to say they had been dropped.

Only the two that are part of the build are drawn. A painting is a picture on
a wall and an item frame is a fitting on one; a pig that happened to wander
into the selection is not architecture, and a mob's model is a rig this
renderer has no business growing.

A painting's size is a registry entry rather than a property of its texture,
so both halves of the pack are needed: data/minecraft/painting_variant for
the width and height in blocks, assets/minecraft/textures/painting for the
picture itself.
"""

import json
from functools import lru_cache

from .assets import ASSETS, DATA
from .entity_shapes import box

FACINGS = ("south", "west", "north", "east")
AXIS = {"south": (2, 1), "north": (2, -1), "east": (0, 1), "west": (0, -1)}
DEPTH = 1 / 16  # stands proud of the block it hangs on, not flush with it
FRAME_SIDE = 12 / 16


def _plain(value):
    return str(value).split(":", 1)[-1].lower()


def facing_of(nbt):
    """Compass direction the entity's face points at.

    Stored as a byte in the order south, west, north, east -- the same order
    the game uses for a painting's `facing` and a hanging entity's `Facing`,
    and not the order the horizontal directions are usually listed in.
    """
    for key in ("facing", "Facing", "Direction"):
        if key in nbt:
            raw = nbt[key]
            try:
                return FACINGS[int(str(raw)) % 4]
            except ValueError:
                return _plain(raw)
    return "south"


@lru_cache(maxsize=None)
def painting_size(variant):
    """(width, height) in blocks, from the pack's own registry."""
    if DATA is None:
        return None
    path = DATA / "painting_variant" / f"{variant}.json"
    if not path.is_file():
        return None
    entry = json.loads(path.read_text())
    asset = _plain(entry.get("asset_id", variant))
    if not (ASSETS / "textures" / "painting" / f"{asset}.png").is_file():
        return None
    return int(entry.get("width", 1)), int(entry.get("height", 1)), asset


def _span(width, height, facing):
    """The picture's own corners, relative to the block it is anchored on.

    A painting wider or taller than one block grows away from its anchor the
    way the game centres it: the extra row or column of an even size goes up
    and to the right of centre, so a 2x1 hangs one block to the anchor's own
    side rather than straddling it evenly, which is not expressible on a
    lattice.
    """
    axis, sign = AXIS[facing]
    across = 2 - axis
    lo = [0.0, 0.0, 0.0]
    hi = [1.0, 1.0, 1.0]
    lo[across] = -((width - 1) // 2)
    hi[across] = lo[across] + width
    lo[1] = -((height - 1) // 2)
    hi[1] = lo[1] + height
    lo[axis], hi[axis] = (1.0, 1.0 + DEPTH) if sign > 0 else (-DEPTH, 0.0)
    return tuple(lo), tuple(hi)


def _facing_part(lo, hi, texture, facing):
    """A picture drawn on its outward face only.

    A painting is one image, not a cube skin, so putting it on all six faces
    squeezes the whole picture into each 1/16 side and reads as streaks along
    the edges. The other faces are against a wall in any case.
    """
    part = box(lo, hi, texture)
    part["only_faces"] = (facing,)
    return part


def painting_parts(nbt):
    variant = _plain(nbt.get("variant") or nbt.get("Motive") or "")
    size = painting_size(variant)
    if size is None:
        return []
    width, height, asset = size
    facing = facing_of(nbt)
    lo, hi = _span(width, height, facing)
    return [_facing_part(lo, hi, f"painting/{asset}", facing)]


def item_frame_parts(nbt, glowing):
    """The frame itself, without whatever it holds.

    An item in a frame is drawn from the item's own model, a second resolver
    this package does not have; the fitting is what makes the wall read as
    furnished, so it is drawn and the contents are left out rather than
    approximated.
    """
    facing = facing_of(nbt)
    axis, sign = AXIS[facing]
    across = 2 - axis
    inset = (1 - FRAME_SIDE) / 2
    lo = [inset, inset, inset]
    hi = [inset + FRAME_SIDE, inset + FRAME_SIDE, inset + FRAME_SIDE]
    lo[across], hi[across] = inset, inset + FRAME_SIDE
    lo[axis], hi[axis] = (1.0, 1.0 + DEPTH) if sign > 0 else (-DEPTH, 0.0)
    texture = "block/glow_item_frame" if glowing else "block/item_frame"
    return [_facing_part(tuple(lo), tuple(hi), texture, facing)]


HANDLERS = {
    "painting": lambda nbt: painting_parts(nbt),
    "item_frame": lambda nbt: item_frame_parts(nbt, glowing=False),
    "glow_item_frame": lambda nbt: item_frame_parts(nbt, glowing=True),
}


def anchor_of(nbt):
    for keys in (("TileX", "TileY", "TileZ"), ("block_pos",)):
        if all(key in nbt for key in keys):
            if len(keys) == 1:
                return tuple(int(str(v)) for v in nbt[keys[0]])
            return tuple(int(str(nbt[key])) for key in keys)
    if "Pos" in nbt:
        return tuple(int(float(str(v))) for v in nbt["Pos"])
    return None


def structure_parts(structure):
    """[(anchor block, boxes)] for every entity this renderer can draw."""
    result = []
    for entity in structure.entities:
        nbt = entity.get("nbt")
        if nbt is None:
            continue
        handler = HANDLERS.get(_plain(nbt.get("id", "")))
        if handler is None:
            continue
        anchor = anchor_of(nbt)
        if anchor is None:
            continue
        parts = handler(nbt)
        if parts:
            result.append((anchor, parts))
    return result
