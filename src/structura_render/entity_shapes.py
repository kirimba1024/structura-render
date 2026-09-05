"""Compact models for blocks rendered outside block-model JSON."""

import json

from PIL import Image

from . import font

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


def box(lo, hi, texture, crop=None, tint=None, alpha=255, angle=0, faces=None, turns=None):
    return {
        "lo": lo, "hi": hi, "texture": texture, "crop": crop, "tint": tint,
        "alpha": alpha, "angle": angle, "faces": faces, "turns": turns,
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


OPPOSITE = {
    "up": "down", "down": "up", "north": "south",
    "south": "north", "east": "west", "west": "east",
}

# Which way an image runs once it is on a face: the direction of one step
# right across the crop, then one step down it. The first table is how
# Minecraft reads a model's own six faces -- its sheets are laid out for a
# model whose Y points down, which is why every one of these runs downward
# toward "up" -- and the second is how this renderer draws the world's six.
MODEL_UV = {
    "down": ("east", "north"), "up": ("east", "north"),
    "north": ("east", "up"), "south": ("west", "up"),
    "east": ("south", "up"), "west": ("north", "up"),
}
WORLD_UV = {
    "up": ("east", "north"), "down": ("east", "north"),
    "north": ("west", "down"), "south": ("east", "down"),
    "east": ("north", "down"), "west": ("south", "down"),
}

TURNS = {
    None: lambda right, down: (right, down),
    Image.FLIP_LEFT_RIGHT: lambda right, down: (OPPOSITE[right], down),
    Image.FLIP_TOP_BOTTOM: lambda right, down: (right, OPPOSITE[down]),
    Image.ROTATE_180: lambda right, down: (OPPOSITE[right], OPPOSITE[down]),
    Image.ROTATE_90: lambda right, down: (OPPOSITE[down], right),
    Image.ROTATE_270: lambda right, down: (down, OPPOSITE[right]),
    Image.TRANSPOSE: lambda right, down: (down, right),
    Image.TRANSVERSE: lambda right, down: (OPPOSITE[down], OPPOSITE[right]),
}

# Where each of a model's own faces ends up pointing once the game has set it
# in its block, before the block's own rotation. Every block entity drawn
# this way lands on one of these: the renderer rights a Y-down model with a
# half turn, and which axis it turns about decides everything downstream.
# Chests keep their Y and are turned to face the other way instead; a bed is
# the one that gets a quarter turn, onto its back.
HALF_TURN_X = {"up": "down", "down": "up", "north": "south", "south": "north",
               "east": "east", "west": "west"}
HALF_TURN_Y = {"up": "up", "down": "down", "north": "south", "south": "north",
               "east": "west", "west": "east"}
HALF_TURN_Z = {"up": "down", "down": "up", "north": "north", "south": "south",
               "east": "west", "west": "east"}
QUARTER_TURN_X = {"up": "south", "down": "north", "north": "up",
                  "south": "down", "east": "east", "west": "west"}
NO_TURN = {name: name for name in OPPOSITE}


# Banners and standing signs are drawn at two thirds scale, so one of their
# model pixels is smaller than one of the block's.
SMALL_SCALE = 2 / 3


def _px(units):
    """Model pixels of a two-thirds-scale entity, in blocks."""
    return units * SMALL_SCALE / 16


def cube_faces(offset, size):
    """The six crops of one entity-model box, keyed by the box's own faces.

    A box of w x h x d at (u, v) unwraps into a (2d + 2w) by (d + h)
    rectangle: its underside and its top side by side along the upper edge,
    then its four walls in a row beneath them, west to south. Straight out
    of ModelPart.Cube -- handing box() a single crop instead stretches that
    whole unwrap onto every face.
    """
    u, v = offset
    w, h, d = size
    return {
        "down":  (u + d,             v,     u + d + w,           v + d),
        "up":    (u + d + w,         v,     u + d + 2 * w,       v + d),
        "west":  (u,                 v + d, u + d,               v + d + h),
        "north": (u + d,             v + d, u + d + w,           v + d + h),
        "east":  (u + d + w,         v + d, u + 2 * d + w,       v + d + h),
        "south": (u + 2 * d + w,     v + d, u + 2 * d + 2 * w,   v + d + h),
    }


def unwrap(offset, size, pose):
    """One box's crops, keyed by the world face each of its own faces lands
    on, and the turn each of those needs to be read the way the game reads
    it. A pose maps directions as well as faces, so the same table that says
    where a face goes says where the image's own right and down go with it.
    """
    turns = {}
    for model, world in pose.items():
        right, down = (pose[axis] for axis in MODEL_UV[model])
        turn = next(t for t, moved in TURNS.items()
                    if moved(right, down) == WORLD_UV[world])
        if turn is not None:
            turns[world] = turn
    crops = cube_faces(offset, size)
    return {"faces": {pose[model]: crop for model, crop in crops.items()},
            "turns": turns}


def cube(origin, size, offset, texture, pose, **kwargs):
    """A box placed and unwrapped in the model's own 1/16 units."""
    lo = tuple(value / 16 for value in origin)
    hi = tuple((o + s) / 16 for o, s in zip(origin, size))
    return box(lo, hi, texture, **unwrap(offset, size, pose), **kwargs)


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
    """One chest: a body, a lid resting on it, and the latch between them.

    A double chest is not two singles -- each half is a 15-wide box that
    reaches a pixel past its own block into its partner, and carries the
    single-pixel half of the latch on the side it meets.
    """
    chest_type = props.get("type", "single")
    texture = chest_texture(base, chest_type)
    angle = angle_for(props)
    double = chest_type in ("left", "right")
    width = 15 if double else 14
    x = (1 if chest_type == "left" else 0) if double else 1
    latch_x, latch_width = ((15 if chest_type == "left" else 0), 1) if double else (7, 2)

    def part(origin, size, offset):
        return cube(origin, size, offset, texture, HALF_TURN_Y, angle=angle)

    return [
        part((x, 0, 1), (width, 10, 14), (0, 19)),
        part((x, 9, 1), (width, 5, 14), (0, 0)),
        part((latch_x, 7, 0), (latch_width, 4, 1), (0, 0)),
    ]


SIGN_LINES = 4
# The game floats the text a hair off the board: 0.0467 of a block from the
# board's own centre plane, against a board half a model pixel thick.
TEXT_DEPTH = 0.08 / 16


def sign_text_metrics(base):
    """Blocks per text pixel, pixels between lines, and the widest line the
    board takes. A hanging sign writes bigger letters on a smaller board, so
    it fits fewer of them: the game's own numbers, not a scaled guess.
    """
    if "hanging_sign" in base:
        return 0.9 / 64, 9, 60
    return 1 / 96, 10, 90


def _text_line_boxes(lines, board_lo, board_hi, face_z, direction, tint, angle, metrics):
    scale, line_height, max_width = metrics
    band = line_height * scale
    middle_x = (board_lo[0] + board_hi[0]) / 2
    middle_y = (board_lo[1] + board_hi[1]) / 2
    z0, z1 = (face_z, face_z + TEXT_DEPTH) if direction > 0 else (face_z - TEXT_DEPTH, face_z)
    outward = "south" if direction > 0 else "north"
    boxes = []
    for row, line in enumerate(lines[:SIGN_LINES]):
        glyphs = [font.glyph(char) for char in line]
        width = sum(advance for _, _, advance in glyphs) - 1 if glyphs else 0
        # The game wraps a line too wide for its board; shrinking it keeps
        # every character on the board instead of dropping the overflow.
        line_scale = scale * min(1, max_width / width) if width > 0 else scale
        top = middle_y + (SIGN_LINES / 2 - row) * band
        bottom = top - font.HEIGHT * line_scale
        cursor = middle_x - direction * width * line_scale / 2
        for texture, crop, advance in glyphs:
            if texture is not None:
                edge = cursor + direction * (advance - 1) * line_scale
                boxes.append(box(
                    (min(cursor, edge), bottom, z0), (max(cursor, edge), top, z1),
                    texture, tint=tint, angle=angle, faces={outward: crop},
                ))
            cursor += direction * advance * line_scale
    return boxes


def sign_text_boxes(content, board_lo, board_hi, angle, back, wall, metrics):
    """The text on one or both sides of a board.

    A standing board sits in the middle of its block and is read from the
    high-z side; a wall board is pushed back against the block it hangs on,
    so it is read from the low-z one. Reading the front off the wrong face
    puts the text inside the wall, which looks like no text at all rather
    than like a mistake.
    """
    sides = [("front_text", board_lo[2], -1)] if wall else [("front_text", board_hi[2], 1)]
    if back:
        sides.append(("back_text", board_lo[2], -1))
    boxes = []
    for side, face_z, direction in sides:
        parsed = content.get(side)
        if not parsed:
            continue
        lines, color, _glow = parsed
        boxes.extend(_text_line_boxes(lines, board_lo, board_hi, face_z, direction,
                                      DYES[color], angle, metrics))
    return boxes


def sign_board_bounds(base):
    """The board's own box, and the pose its model is set in.

    A sign has no block model -- the game draws it as an entity whose
    geometry lives in code -- so these come from that code. A standing
    board is the full width of its block and stands proud of the top; a
    wall board is pushed back against the block it hangs on, which at yaw 0
    means the far side, not the near one.
    """
    wall = "_wall_" in base
    if "hanging_sign" in base:
        return (1 / 16, 0, 7 / 16), (15 / 16, 10 / 16, 9 / 16), wall, HALF_TURN_X
    # The board is 24 wide and 12 tall in its own pixels, hung on the block's
    # centre; a wall one is then dropped 5/16 and pushed 7/16 back.
    lo = (0, 0.5 + _px(2), 0.5 - _px(1))
    hi = (1, 0.5 + _px(14), 0.5 + _px(1))
    if wall:
        lo = (lo[0], lo[1] - 5 / 16, lo[2] + 7 / 16)
        hi = (hi[0], hi[1] - 5 / 16, hi[2] + 7 / 16)
    return lo, hi, wall, HALF_TURN_Z if wall else HALF_TURN_X


def sign(base, props, content=None):
    hanging = "hanging_sign" in base
    wood = base.split("_wall", 1)[0].split("_hanging", 1)[0].removesuffix("_sign")
    texture = f"entity/signs/{'hanging/' if hanging else ''}{wood}"
    angle = angle_for(props)
    board_lo, board_hi, wall, pose = sign_board_bounds(base)
    board_size = (14, 10, 2) if hanging else (24, 12, 2)
    board_offset = (0, 12) if hanging else (0, 0)
    result = [box(board_lo, board_hi, texture, angle=angle,
                  **unwrap(board_offset, board_size, pose))]
    if hanging:
        # Two chains from the board's top corners up to the block's ceiling.
        for x in (3 / 16, 12 / 16):
            result.append(box((x, 10 / 16, 7 / 16), (x + 1 / 16, 1, 9 / 16),
                              "block/chain", angle=angle))
    elif not wall:
        stick = _px(1)
        result.append(box(
            (0.5 - stick, 0, 0.5 - stick), (0.5 + stick, board_lo[1], 0.5 + stick),
            texture, angle=angle, **unwrap((0, 14), (2, 14, 2), pose),
        ))
    if content:
        result.extend(sign_text_boxes(content, board_lo, board_hi, angle,
                                      not wall, wall, sign_text_metrics(base)))
    return result


def entity_decoration(name, props, content):
    base = name.split(":", 1)[-1]
    if base.endswith(("_sign", "_hanging_sign")):
        sides = content[1] if content and content[0] == "sign" else None
        if not sides:
            return []
        board_lo, board_hi, wall, _pose = sign_board_bounds(base)
        return sign_text_boxes(dict(sides), board_lo, board_hi, angle_for(props),
                               not wall, wall, sign_text_metrics(base))
    return []


def head(base, props):
    """A skull: one 8x8x8 cube, on the floor or pushed back against a wall."""
    wall = "_wall_" in base
    kind = base.replace("_wall", "").removesuffix("_skull").removesuffix("_head")
    texture = {
        "skeleton": "entity/skeleton/skeleton", "wither_skeleton": "entity/skeleton/wither_skeleton",
        "zombie": "entity/zombie/zombie", "creeper": "entity/creeper/creeper",
        "piglin": "entity/piglin/piglin", "dragon": "entity/enderdragon/dragon",
    }.get(kind, "entity/player/wide/steve")
    origin = (4, 4, 8) if wall else (4, 0, 4)
    return [cube(origin, (8, 8, 8), (0, 0), texture, HALF_TURN_Z, angle=angle_for(props))]


# Each bed leg is the same box spun about the bed's own upright before the
# bed is laid down -- a quarter turn about the model's Z, which the laying
# down then carries round with everything else. The game gives each of the
# four a different quarter so that one box definition serves all of them.
SPIN_Z = {"east": "up", "up": "west", "west": "down", "down": "east",
          "north": "north", "south": "south"}
BED_LEGS = {
    "head": ((0, 0, (50, 6), 1), (13, 0, (50, 18), 2)),
    "foot": ((0, 13, (50, 0), 0), (13, 13, (50, 12), 3)),
}


def leg_pose(quarters):
    spun = QUARTER_TURN_X
    for _ in range(quarters):
        spun = {face: SPIN_Z[direction] for face, direction in spun.items()}
    return {face: QUARTER_TURN_X[direction] for face, direction in spun.items()}


def bed(color, props):
    """A bed half: one 16x16x6 box tipped onto its back, plus two legs.

    Tipped onto its back is the whole difficulty. The head half's sheet at
    (0, 0) describes a box standing up: the mattress and its pillow on the
    box's front, the planks of the underside on its back, the two long
    sides at its flanks, and the head board on its bottom. A quarter turn
    about X lays it down -- the front becomes the sky, the bottom becomes
    the end the half points at -- and carries every crop's own right and
    down round with it. The foot half is the same sheet at (0, 22).

    Each half carries two legs, at its own outer end only; the four of them
    together are the bed's four corners.
    """
    texture = f"entity/bed/{color}"
    angle = angle_for(props)
    half = "head" if props.get("part") == "head" else "foot"
    body = box((0, 3 / 16, 0), (1, 9 / 16, 1), texture, angle=angle,
               **unwrap((0, 0) if half == "head" else (0, 22), (16, 16, 6),
                        QUARTER_TURN_X))
    legs = [
        cube((x, 0, z), (3, 3, 3), offset, texture, leg_pose(quarters), angle=angle)
        for x, z, offset, quarters in BED_LEGS[half]
    ]
    return [body, *legs]


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


def banner(color, wall, angle, layers):
    """Cloth on a pole, or cloth on a bar bolted to a wall.

    The model is 20x40x1 of cloth on a 2x42x2 pole with a 20x2x2 bar, all
    drawn at two thirds scale, so a standing banner stands 1.83 blocks tall
    and a wall one hangs 0.81 below its own floor: a banner does not fit in
    its block and was never meant to.

    The two are the same cloth on different hardware, and the game sets them
    in poses that differ by a half turn -- a standing banner keeps its own
    left and right, a wall one has them swapped -- so the cloth's unwrap
    cannot be shared between them.
    """
    pose = HALF_TURN_Z if wall else HALF_TURN_X
    half, thin = _px(10), _px(1)
    if wall:
        cloth = ((0.5 - half, -_px(19.5), 0.5 + _px(8.5)),
                 (0.5 + half, _px(20.5), 0.5 + _px(9.5)))
        hardware = [(((0.5 - half, _px(18.5), 0.5 + _px(9.5)),
                      (0.5 + half, _px(20.5), 0.5 + _px(11.5))), (0, 42), (20, 2, 2))]
    else:
        cloth = ((0.5 - half, _px(4), 0.5 + thin),
                 (0.5 + half, _px(44), 0.5 + _px(2)))
        hardware = [
            (((0.5 - thin, 0, 0.5 - thin), (0.5 + thin, _px(42), 0.5 + thin)),
             (44, 0), (2, 42, 2)),
            (((0.5 - half, _px(42), 0.5 - thin), (0.5 + half, _px(44), 0.5 + thin)),
             (0, 42), (20, 2, 2)),
        ]
    sheet = unwrap((0, 0), (20, 40, 1), pose)
    broad = ("north", "south")
    result = [box(*cloth, "entity/banner/banner_base", tint=DYES[color],
                  angle=angle, **sheet)]
    for depth, (pattern, layer_color) in enumerate(layers, start=1):
        grown = depth * BANNER_LAYER_STEP
        lo, hi = cloth
        # A pattern belongs on the cloth's two broad faces. Giving it the
        # thin sides as well stacks every layer's edge in the same sliver
        # of space, which z-fights along the whole outline.
        result.append(box(
            (lo[0], lo[1], lo[2] - grown), (hi[0], hi[1], hi[2] + grown),
            f"entity/banner/{pattern}", tint=DYES[layer_color], angle=angle,
            faces={face: sheet["faces"][face] for face in broad},
            turns={face: sheet["turns"][face] for face in broad if face in sheet["turns"]},
        ))
    for (lo, hi), offset, size in hardware:
        result.append(box(lo, hi, "entity/banner/banner_base", angle=angle,
                          **unwrap(offset, size, pose)))
    return result


def decorated_pot(angle):
    """A hollow pot: four sherd walls, a disc top and bottom, and a neck.

    Nothing here is a solid box. Each wall is one plane a pixel inside the
    block carrying a whole sherd square, the discs are flat 14x14 lids at
    the block's floor and ceiling, and the neck is a tube on a collar that
    stands clear above the block -- the pot is the one block entity the game
    lets out of its own cube.
    """
    base = "entity/decorated_pot/decorated_pot_base"
    sherd = "entity/decorated_pot/decorated_pot_side"
    near, far = 1 / 16, 15 / 16
    disc = {"down": (0, 13, 14, 27), "up": (14, 13, 28, 27)}
    wall = (1, 0, 15, 16)
    return [
        box((near, 0, near), (far, 1, near), sherd, faces={"north": wall}, angle=angle),
        box((near, 0, far), (far, 1, far), sherd, faces={"south": wall}, angle=angle),
        box((near, 0, near), (near, 1, far), sherd, faces={"west": wall}, angle=angle),
        box((far, 0, near), (far, 1, far), sherd, faces={"east": wall}, angle=angle),
        box((near, 0, near), (far, 0, far), base, faces=disc, angle=angle),
        box((near, 1, near), (far, 1, far), base, faces=disc, angle=angle),
        # Both neck boxes are deformed: the tube shrinks by a tenth of a
        # pixel and the collar swells by a fifth, so neither shares a plane
        # with the other or with the block's ceiling.
        box((4.1 / 16, 17.1 / 16, 4.1 / 16), (11.9 / 16, 19.9 / 16, 11.9 / 16), base,
            angle=angle, **unwrap((0, 0), (8, 3, 8), HALF_TURN_X)),
        box((4.8 / 16, 15.8 / 16, 4.8 / 16), (11.2 / 16, 17.2 / 16, 11.2 / 16), base,
            angle=angle, **unwrap((0, 5), (6, 1, 6), HALF_TURN_X)),
    ]


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
        return bed(color, props)
    color = colored(base, "wall_banner") or colored(base, "banner")
    if color:
        layers = content[1] if content and content[0] == "banner" else ()
        return banner(color, "wall_banner" in base, angle_for(props), layers)
    if base.endswith(("_sign", "_hanging_sign")):
        sides = content[1] if content and content[0] == "sign" else None
        return sign(base, props, dict(sides) if sides else None)
    color = colored(base, "shulker_box")
    if base == "shulker_box" or color:
        # Drawn as if it faced up. A shulker box can be stuck to any of the
        # six sides, and the other five are a tilt this file's yaw-only
        # angle cannot express.
        texture = f"entity/shulker/shulker{f'_{color}' if color else ''}"
        return [
            cube((0, 0, 0), (16, 8, 16), (0, 28), texture, HALF_TURN_X),
            cube((0, 4, 0), (16, 12, 16), (0, 0), texture, HALF_TURN_X),
        ]
    if name == "minecraft:bell":
        return [box((4 / 16, 3 / 16, 4 / 16), (12 / 16, 13 / 16, 12 / 16), "entity/bell/bell_body", (8, 6, 24, 22))]
    if name == "minecraft:conduit":
        return [box((5 / 16, 5 / 16, 5 / 16), (11 / 16, 11 / 16, 11 / 16), "entity/conduit/base", (0, 0, 16, 16))]
    if name == "minecraft:decorated_pot":
        return decorated_pot(angle_for(props))
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
