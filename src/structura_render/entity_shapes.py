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



def cube_faces(offset, size):
    """The six crops of one entity-model box, from its texture offset.

    A box of w x h x d at (u, v) unwraps into a (2d + 2w) by (d + h)
    rectangle: top and bottom side by side along the upper edge, then the
    four walls in a row beneath them. Handing box() a single crop instead
    stretches that whole unwrap onto every face, which is why a chest lid
    smeared, a bed had no shape and a banner showed holes -- the sliver of
    texture that happened to land on a thin side was transparent.

    The face names are this renderer's world directions, not the model's
    own: yaw 0 faces south here, so the model's front is south and its left
    is east. Verified against the head table this replaces, which resolves
    identically for an 8x8x8 box at (0, 0).
    """
    u, v = offset
    w, h, d = size
    return {
        "up":    (u + d,             v,     u + d + w,           v + d),
        "down":  (u + d + w,         v,     u + d + 2 * w,       v + d),
        "west":  (u,                 v + d, u + d,               v + d + h),
        "south": (u + d,             v + d, u + d + w,           v + d + h),
        "east":  (u + d + w,         v + d, u + 2 * d + w,       v + d + h),
        "north": (u + 2 * d + w,     v + d, u + 2 * d + 2 * w,   v + d + h),
    }


def lidded_cube_faces(offset, size):
    """cube_faces with up and down swapped, for a box whose unwrap is lidded.

    Read off the chest texture rather than argued: at offset (0, 0) for its
    14x5x14 lid the first square is a dark inset and the second is plain
    planks, and a closed chest shows planks from above and the dark inside
    only when open. The skin-shaped boxes this file also draws -- a head at
    (0, 0) on a player skin -- put the top first, so the two conventions are
    kept apart instead of one being forced onto both.
    """
    faces = cube_faces(offset, size)
    faces["up"], faces["down"] = faces["down"], faces["up"]
    return faces


def cube(origin, size, offset, texture, **kwargs):
    """A box placed and unwrapped in the model's own 1/16 units."""
    lo = tuple(value / 16 for value in origin)
    hi = tuple((o + s) / 16 for o, s in zip(origin, size))
    return box(lo, hi, texture, faces=cube_faces(offset, size), **kwargs)


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
    left = 0 if chest_type == "left" else 1
    width = 16 if chest_type in ("left", "right") else 14
    def part(origin, size, offset):
        lo = tuple(v / 16 for v in origin)
        hi = tuple((o + s) / 16 for o, s in zip(origin, size))
        return box(lo, hi, texture, angle=angle, faces=lidded_cube_faces(offset, size))
    return [
        part((left, 0, 1), (width, 10, 14), (0, 19)),
        part((left, 10, 1), (width, 5, 14), (0, 0)),
        part((7, 7, 0), (2, 4, 1), (0, 0)),
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
        outward = "south" if direction > 0 else "north"
        for texture, crop, advance in glyphs:
            if texture is not None:
                edge = cursor + direction * (advance - 1) * scale
                boxes.append(box(
                    (min(cursor, edge), bottom, z0), (max(cursor, edge), top, z1),
                    texture, tint=tint, angle=angle, faces={outward: crop},
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
    """The board's own box, sized from the texture's unwrap.

    A sign has no block model -- the game draws it as an entity whose
    geometry lives in code -- so the only description of it shipped with the
    pack is the atlas. A box unwraps to (2*depth + 2*width) by (depth +
    height), which reads back as 24x12x2 for a standing board from its
    (0,0,24,14) region and 14x10x2 for a hanging one from (0,12,32,24).
    Guessing 12x9 for the hanging board instead is what pushed its text up:
    the lines centre on the board, so a board short by a pixel carries them
    with it.
    """
    wall = "_wall_" in base
    if "hanging_sign" in base:
        return (1 / 16, 2 / 16, 7 / 16), (15 / 16, 12 / 16, 9 / 16), wall
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
            box(board_lo, board_hi, texture, angle=angle,
                faces=cube_faces((0, 12), (14, 10, 2))),
            box((3 / 16, 12 / 16, 7 / 16), (4 / 16, 1, 9 / 16), "block/chain", angle=angle),
            box((12 / 16, 12 / 16, 7 / 16), (13 / 16, 1, 9 / 16), "block/chain", angle=angle),
        ]
    else:
        result = [box(board_lo, board_hi, texture, angle=angle,
                      faces=cube_faces((0, 0), (24, 12, 2)))]
        if not wall:
            result.append(box(
                (7.5 / 16, 0, 7.5 / 16), (8.5 / 16, 8 / 16, 8.5 / 16), texture,
                angle=angle, faces=cube_faces((0, 14), (2, 14, 2)),
            ))
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
    return [box(lo, hi, texture, faces=cube_faces((0, 0), (8, 8, 8)), angle=angle_for(props))]


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
# The banner model is 20x40x1 of cloth on a 2x42x2 pole with a 20x2x2 bar,
# drawn at two thirds scale, so a standing one stands about 1.75 blocks tall
# and its cloth is wider than it is deep -- it does not fit in its own block
# and was never meant to. The cloth size is confirmed by this file's own
# long-standing crop of (1, 1, 21, 41), which is exactly that box's south
# face unwrapped at texture offset (0, 0).
BANNER_SCALE = 2 / 3


def _banner_px(units):
    return units * BANNER_SCALE / 16


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
        # A bed's own box is 16x16x6 laid on its back, so its unwrap does not
        # line up with anything this file can derive without the rotation, and
        # a guess at it rendered as debris. Left as the plain slab it was.
        return [box((0, 0, 0), (1, 9 / 16, 1), f"entity/bed/{color}", angle=angle_for(props))]
    color = colored(base, "wall_banner") or colored(base, "banner")
    if color:
        wall = "wall_banner" in base
        angle = angle_for(props)
        half_width = _banner_px(20) / 2
        cloth_height = _banner_px(40)
        pole_height = _banner_px(42)
        thickness = _banner_px(1)
        centre = 0.5
        top = pole_height - _banner_px(2) if not wall else 1.0
        post = _banner_px(2) / 2
        # The cloth hangs in front of the pole, not through it.
        depth = (1 - thickness, 1.0) if wall else (centre + post, centre + post + thickness)
        cloth = (
            (centre - half_width, top - cloth_height, depth[0]),
            (centre + half_width, top, depth[1]),
        )
        cloth_faces = cube_faces((0, 0), (20, 40, 1))
        result = [box(*cloth, "entity/banner/banner_base", tint=DYES[color],
                      angle=angle, faces=cloth_faces)]
        layers = content[1] if content and content[0] == "banner" else ()
        for i, (pattern, layer_color) in enumerate(layers, start=1):
            layer_cloth = _grown_cloth(cloth, i * BANNER_LAYER_STEP)
            # A pattern belongs on the cloth's two broad faces. Giving it the
            # thin sides as well stacks every layer's edge in the same sliver
            # of space, which z-fights along the whole outline.
            result.append(box(
                *layer_cloth, f"entity/banner/{pattern}", tint=DYES[layer_color],
                angle=angle,
                faces={face: cloth_faces[face] for face in ("north", "south")},
            ))
        if not wall:
            result.append(box(
                (centre - post, 0, centre - post), (centre + post, pole_height, centre + post),
                "entity/banner/banner_base", angle=angle,
                faces=cube_faces((44, 0), (2, 42, 2)),
            ))
            bar = _banner_px(2)
            result.append(box(
                (centre - half_width, pole_height - bar, centre - post),
                (centre + half_width, pole_height, centre + post),
                "entity/banner/banner_base", angle=angle,
                faces=cube_faces((0, 42), (20, 2, 2)),
            ))
        return result
    if base.endswith(("_sign", "_hanging_sign")):
        sides = content[1] if content and content[0] == "sign" else None
        return sign(base, props, dict(sides) if sides else None)
    color = colored(base, "shulker_box")
    if base == "shulker_box" or color:
        texture = f"entity/shulker/shulker{f'_{color}' if color else ''}"
        return [
            cube((0, 0, 0), (16, 8, 16), (0, 28), texture),
            cube((0, 8, 0), (16, 12, 16), (0, 0), texture),
        ]
    if name == "minecraft:bell":
        return [box((4 / 16, 3 / 16, 4 / 16), (12 / 16, 13 / 16, 12 / 16), "entity/bell/bell_body", (8, 6, 24, 22))]
    if name == "minecraft:conduit":
        return [box((5 / 16, 5 / 16, 5 / 16), (11 / 16, 11 / 16, 11 / 16), "entity/conduit/base", (0, 0, 16, 16))]
    if name == "minecraft:decorated_pot":
        # Same as the bed: the pot's own neck/body split and its sherd faces
        # are not derivable from the pack, and guessing produced holes.
        return [
            box((1 / 16, 0, 1 / 16), (15 / 16, 12 / 16, 15 / 16),
                "entity/decorated_pot/decorated_pot_side"),
            box((4 / 16, 12 / 16, 4 / 16), (12 / 16, 1, 12 / 16),
                "entity/decorated_pot/decorated_pot_base", (0, 0, 16, 16)),
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
