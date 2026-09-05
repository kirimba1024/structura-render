"""Compact models for blocks rendered outside block-model JSON."""

import json
from functools import lru_cache

import numpy as np
from PIL import Image

from . import font
from .assets import ASSETS

DYES = {
    "white": (249, 255, 254), "orange": (249, 128, 29),
    "magenta": (199, 78, 189), "light_blue": (58, 179, 218),
    "yellow": (254, 216, 61), "lime": (128, 199, 31),
    "pink": (243, 139, 170), "gray": (71, 79, 82),
    "light_gray": (157, 157, 151), "cyan": (22, 156, 156),
    "purple": (137, 50, 184), "blue": (60, 68, 170),
    "brown": (131, 84, 50), "green": (94, 124, 22),
    "red": (176, 46, 38), "black": (29, 29, 33),
}

INVISIBLE = {
    "minecraft:barrier", "minecraft:light", "minecraft:moving_piston",
    "minecraft:structure_void",
}


def box(lo, hi, texture, crop=None, tint=None, alpha=255, angle=0, faces=None):
    return {
        "lo": lo, "hi": hi, "texture": texture, "crop": crop,
        "tint": tint, "alpha": alpha, "angle": angle, "faces": faces,
    }


def angle_for(props):
    if "rotation" in props:
        return int(props["rotation"]) * 22.5
    return {"north": 0, "east": 90, "south": 180, "west": 270}.get(props.get("facing"), 0)


def colored(base, suffix):
    return next((color for color in DYES if base == f"{color}_{suffix}"), None)




def _plain_text(component):
    """A text component flattened to the characters it actually shows.

    A component is a tree: its own `text` followed by its `extra` children,
    each of which is another component. Reading only the root's `text` renders
    a sign as blank whenever an editor wrote the line as a list or wrapped it
    in a formatting child, which is common and gives no hint that anything
    was lost.
    """
    if isinstance(component, str):
        return component
    if isinstance(component, list):
        return "".join(_plain_text(child) for child in component)
    if isinstance(component, dict):
        return str(component.get("text", "")) + "".join(
            _plain_text(child) for child in component.get("extra", [])
        )
    return ""


def _sign_side(component):
    lines = []
    for raw in component.get("messages", []):
        raw = str(raw)
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = raw
        lines.append(_plain_text(parsed))
    if not any(lines):
        return None
    color = str(component.get("color", "black"))
    return (tuple(lines), color if color in DYES else "black", bool(component.get("has_glowing_text", 0)))


def nbt_sensitive(name):
    base = name.split(":", 1)[-1]
    return base.endswith(("_sign", "_hanging_sign")) or "banner" in base


def nbt_signature(name, nbt):
    if nbt is None:
        return None
    base = name.split(":", 1)[-1]
    if base.endswith(("_sign", "_hanging_sign")):
        sides = {}
        for side in ("front_text", "back_text"):
            if side in nbt:
                parsed = _sign_side(nbt[side])
                if parsed:
                    sides[side] = parsed
        return ("sign", tuple(sorted(sides.items()))) if sides else None
    if "banner" in base and "patterns" in nbt:
        layers = []
        for entry in nbt["patterns"]:
            if "pattern" not in entry or "color" not in entry:
                continue
            pattern = str(entry["pattern"]).rsplit(":", 1)[-1]
            color = str(entry["color"])
            if color in DYES:
                layers.append((pattern, color))
        return ("banner", tuple(layers)) if layers else None
    return None


def chest_texture(base, chest_type):
    side = f"_{chest_type}" if chest_type in ("left", "right") else ""
    if base == "ender_chest":
        return "entity/chest/ender"
    if base == "trapped_chest":
        return f"entity/chest/trapped{side}"
    copper = base.removeprefix("waxed_").removesuffix("_chest")
    if copper in ("exposed_copper", "weathered_copper", "oxidized_copper"):
        stage, _ = copper.split("_", 1)
        copper = f"copper_{stage}"
    elif copper != "copper":
        copper = None
    return f"entity/chest/{copper}{side}" if copper else f"entity/chest/normal{side}"


def chest(base, props):
    chest_type = props.get("type", "single")
    texture = chest_texture(base, chest_type)
    angle = angle_for(props)
    left = 0 if chest_type == "left" else 1 / 16
    right = 1 if chest_type == "right" else 15 / 16
    return [
        box((left, 0, 1 / 16), (right, 10 / 16, 15 / 16), texture, (14, 33, 28, 43), angle=angle),
        box((left, 10 / 16, 1 / 16), (right, 14 / 16, 15 / 16), texture, (14, 14, 28, 19), angle=angle),
        box((7 / 16, 7 / 16, 0), (9 / 16, 11 / 16, 2 / 16), texture, (1, 1, 3, 5), angle=angle),
    ]


SIGN_LINES = 4
SIGN_INSET_X = 1.5 / 16
SIGN_INSET_Y = 1 / 16
SIGN_NATURAL_SCALE = (1 / 16) / 6
TEXT_DEPTH = 0.4 / 16


def _text_line_boxes(lines, board_lo, board_hi, face_z, direction, tint, angle):
    boxes = []
    x_lo, x_hi = board_lo[0] + SIGN_INSET_X, board_hi[0] - SIGN_INSET_X
    y_lo, y_hi = board_lo[1] + SIGN_INSET_Y, board_hi[1] - SIGN_INSET_Y
    usable_width = max(x_hi - x_lo, 0.01)
    band = (y_hi - y_lo) / SIGN_LINES
    z0, z1 = (face_z, face_z + TEXT_DEPTH) if direction > 0 else (face_z - TEXT_DEPTH, face_z)
    center_x = (x_lo + x_hi) / 2
    for row, line in enumerate(lines[:SIGN_LINES]):
        glyphs = [font.glyph(char) for char in line]
        pixel_total = sum(advance for _, _, advance in glyphs) - 1 if glyphs else 0
        scale = SIGN_NATURAL_SCALE if pixel_total <= 0 else min(SIGN_NATURAL_SCALE, usable_width / pixel_total)
        glyph_h = font.HEIGHT * scale
        top = y_hi - row * band - (band - glyph_h) / 2
        bottom = top - glyph_h
        cursor = center_x - direction * (pixel_total * scale) / 2
        for texture, crop, advance in glyphs:
            if texture is not None:
                edge = cursor + direction * (advance - 1) * scale
                boxes.append(box(
                    (min(cursor, edge), bottom, z0), (max(cursor, edge), top, z1),
                    texture, crop, tint, angle=angle,
                ))
            cursor += direction * advance * scale
    return boxes


def sign_text_boxes(content, board_lo, board_hi, angle, back):
    boxes = []
    sides = [("front_text", board_hi[2], 1)]
    if back:
        sides.append(("back_text", board_lo[2], -1))
    for side, face_z, direction in sides:
        parsed = content.get(side)
        if not parsed:
            continue
        lines, color, _glow = parsed
        boxes.extend(_text_line_boxes(lines, board_lo, board_hi, face_z, direction, DYES[color], angle))
    return boxes


def sign_board_bounds(base):
    wall = "_wall_" in base
    if "hanging_sign" in base:
        return (2 / 16, 3 / 16, 7 / 16), (14 / 16, 12 / 16, 9 / 16), wall
    if wall:
        return (0, 5 / 16, 14 / 16), (1, 12 / 16, 1), wall
    return (2 / 16, 8 / 16, 7 / 16), (14 / 16, 14 / 16, 9 / 16), wall


def sign(base, props, content=None):
    wall = "_wall_" in base
    hanging = "hanging_sign" in base
    wood = base.split("_wall", 1)[0].split("_hanging", 1)[0].removesuffix("_sign")
    texture = f"entity/signs/{'hanging/' if hanging else ''}{wood}"
    angle = angle_for(props)
    board_lo, board_hi, wall = sign_board_bounds(base)
    if hanging:
        result = [
            box(board_lo, board_hi, texture, (0, 12, 32, 24), angle=angle),
            box((3 / 16, 12 / 16, 7 / 16), (4 / 16, 1, 9 / 16), "block/chain", angle=angle),
            box((12 / 16, 12 / 16, 7 / 16), (13 / 16, 1, 9 / 16), "block/chain", angle=angle),
        ]
    else:
        result = [box(board_lo, board_hi, texture, (0, 0, 24, 14), angle=angle)]
        if not wall:
            result.append(
                box((7.5 / 16, 0, 7.5 / 16), (8.5 / 16, 8 / 16, 8.5 / 16), texture, (0, 16, 8, 30), angle=angle),
            )
    if content:
        result.extend(sign_text_boxes(content, board_lo, board_hi, angle, back=not wall))
    return result


def entity_decoration(name, props, content):
    base = name.split(":", 1)[-1]
    if base.endswith(("_sign", "_hanging_sign")):
        sides = content[1] if content and content[0] == "sign" else None
        if not sides:
            return []
        board_lo, board_hi, wall = sign_board_bounds(base)
        return sign_text_boxes(dict(sides), board_lo, board_hi, angle_for(props), back=not wall)
    return []


# The entity skin's head cube, unwrapped: front/back/top/bottom/right/left
# are six distinct 8x8 regions of the same texture, not one tile repeated on
# every face -- south is the model's front by the same yaw=0-faces-south
# convention the player model itself uses.
HEAD_FACES = {
    "south": (8, 8, 16, 16), "north": (24, 8, 32, 16),
    "up": (8, 0, 16, 8), "down": (16, 0, 24, 8),
    "west": (0, 8, 8, 16), "east": (16, 8, 24, 16),
}


def head(base, props):
    wall = "_wall_" in base
    kind = base.replace("_wall", "").removesuffix("_skull").removesuffix("_head")
    texture = {
        "skeleton": "entity/skeleton/skeleton", "wither_skeleton": "entity/skeleton/wither_skeleton",
        "zombie": "entity/zombie/zombie", "creeper": "entity/creeper/creeper",
        "piglin": "entity/piglin/piglin", "dragon": "entity/enderdragon/dragon",
    }.get(kind, "entity/player/wide/steve")
    lo, hi = (
        ((4 / 16, 4 / 16, 8 / 16), (12 / 16, 12 / 16, 1))
        if wall else ((4 / 16, 0, 4 / 16), (12 / 16, 8 / 16, 12 / 16))
    )
    return [box(lo, hi, texture, faces=HEAD_FACES, angle=angle_for(props))]


def copper_golem(base, props):
    stage = next((stage for stage in ("exposed", "weathered", "oxidized") if stage in base), None)
    texture = "entity/copper_golem/copper_golem" + (f"_{stage}" if stage else "")
    angle = angle_for(props)
    body = (20, 20, 28, 30)
    return [
        box((4 / 16, 10 / 16, 4 / 16), (12 / 16, 1, 12 / 16), texture, (8, 8, 16, 16), angle=angle),
        box((5 / 16, 4 / 16, 5 / 16), (11 / 16, 10 / 16, 11 / 16), texture, body, angle=angle),
        box((2 / 16, 4 / 16, 6 / 16), (5 / 16, 10 / 16, 10 / 16), texture, body, angle=angle),
        box((11 / 16, 4 / 16, 6 / 16), (14 / 16, 10 / 16, 10 / 16), texture, body, angle=angle),
        box((5 / 16, 0, 5 / 16), (8 / 16, 4 / 16, 10 / 16), texture, body, angle=angle),
        box((8 / 16, 0, 5 / 16), (11 / 16, 4 / 16, 10 / 16), texture, body, angle=angle),
    ]


BANNER_LAYER_STEP = 0.15 / 16


def _grown_cloth(cloth, amount):
    lo, hi = cloth
    return (lo[0], lo[1], lo[2] - amount), (hi[0], hi[1], hi[2] + amount)


def entity_shape(name, props, content=None):
    base = name.split(":", 1)[-1]
    if name in INVISIBLE:
        return []
    if base.endswith("_chest") or base == "chest":
        return chest(base, props)
    if "copper_golem_statue" in base:
        return copper_golem(base, props)
    if base.endswith(("_skull", "_head")):
        return head(base, props)
    color = colored(base, "bed")
    if color:
        return [box((0, 0, 0), (1, 9 / 16, 1), f"entity/bed/{color}", angle=angle_for(props))]
    color = colored(base, "wall_banner") or colored(base, "banner")
    if color:
        wall = "wall_banner" in base
        angle = angle_for(props)
        cloth = (
            ((2 / 16, 2 / 16, 15 / 16), (14 / 16, 14 / 16, 1))
            if wall else ((2 / 16, 2 / 16, 7.5 / 16), (14 / 16, 14 / 16, 8.5 / 16))
        )
        result = [box(*cloth, "entity/banner/banner_base", (1, 1, 21, 41), DYES[color], angle=angle)]
        layers = content[1] if content and content[0] == "banner" else ()
        for i, (pattern, layer_color) in enumerate(layers, start=1):
            layer_cloth = _grown_cloth(cloth, i * BANNER_LAYER_STEP)
            result.append(box(
                *layer_cloth, f"entity/banner/{pattern}", (1, 1, 21, 41),
                DYES[layer_color], angle=angle,
            ))
        if not wall:
            result.append(box((7.5 / 16, 0, 7.5 / 16), (8.5 / 16, 1, 8.5 / 16), "block/oak_planks", angle=angle))
        return result
    if base.endswith(("_sign", "_hanging_sign")):
        sides = content[1] if content and content[0] == "sign" else None
        return sign(base, props, dict(sides) if sides else None)
    color = colored(base, "shulker_box")
    if base == "shulker_box" or color:
        texture = f"entity/shulker/shulker{f'_{color}' if color else ''}"
        return [
            box((0, 0, 0), (1, 0.5, 1), texture, (16, 44, 32, 52)),
            box((0, 0.5, 0), (1, 1, 1), texture, (16, 16, 32, 28)),
        ]
    if name == "minecraft:bell":
        return [box((4 / 16, 3 / 16, 4 / 16), (12 / 16, 13 / 16, 12 / 16), "entity/bell/bell_body", (8, 6, 24, 22))]
    if name == "minecraft:conduit":
        return [box((5 / 16, 5 / 16, 5 / 16), (11 / 16, 11 / 16, 11 / 16), "entity/conduit/base", (0, 0, 16, 16))]
    if name == "minecraft:decorated_pot":
        return [
            box((1 / 16, 0, 1 / 16), (15 / 16, 12 / 16, 15 / 16), "entity/decorated_pot/decorated_pot_side"),
            box(
                (4 / 16, 12 / 16, 4 / 16), (12 / 16, 1, 12 / 16),
                "entity/decorated_pot/decorated_pot_base", (0, 0, 16, 16),
            ),
        ]
    if name in ("minecraft:end_portal", "minecraft:end_gateway"):
        portal = name.endswith("end_portal")
        return [box((0, 12 / 16 if portal else 0, 0), (1, 12.1 / 16 if portal else 1, 1), f"effect/{base}")]
    if name in ("minecraft:water", "minecraft:lava", "minecraft:bubble_column"):
        level = int(props.get("level", 0))
        height = 1 if level == 0 or level >= 8 else (8 - level) / 9
        water = name != "minecraft:lava"
        return [box(
            (0, 0, 0), (1, height, 1),
            "block/water_still" if water else "block/lava_still",
            tint=(63, 118, 228) if water else None,
            alpha=170 if water else 235,
        )]
    return None
