"""Compact models for blocks rendered outside block-model JSON."""

from .block_colours import (
    DYES as DYES,
)
from .shape_geometry import (
    HALF_TURN_X as HALF_TURN_X,
    HALF_TURN_Y as HALF_TURN_Y,
    HALF_TURN_Z as HALF_TURN_Z,
    MODEL_AXES as MODEL_AXES,
    MODEL_UV as MODEL_UV,
    NO_TURN as NO_TURN,
    OPPOSITE as OPPOSITE,
    QUARTER_TURN_X as QUARTER_TURN_X,
    SIGNED_AXIS as SIGNED_AXIS,
    SMALL_SCALE as SMALL_SCALE,
    SPIN_Z as SPIN_Z,
    TURNS as TURNS,
    WORLD_UV as WORLD_UV,
    _px as _px,
    after as after,
    angle_for as angle_for,
    box as box,
    cube as cube,
    cube_faces as cube_faces,
    spin_z as spin_z,
    turned_box as turned_box,
    unwrap as unwrap,
)
from .signs import (
    SIGN_LINES as SIGN_LINES,
    TEXT_DEPTH as TEXT_DEPTH,
    _hanging_plane as _hanging_plane,
    _plain_text as _plain_text,
    _sign_side as _sign_side,
    _text_line_boxes as _text_line_boxes,
    entity_decoration as entity_decoration,
    sign as sign,
    sign_board_bounds as sign_board_bounds,
    sign_text_boxes as sign_text_boxes,
    sign_text_metrics as sign_text_metrics,
)

INVISIBLE = {
    "minecraft:barrier", "minecraft:light", "minecraft:moving_piston",
    "minecraft:structure_void",
}


def colored(base, suffix):
    return next((color for color in DYES if base == f"{color}_{suffix}"), None)


def nbt_sensitive(name):
    base = name.split(":", 1)[-1]
    return (base.endswith(("_sign", "_hanging_sign")) or "banner" in base
            or base == "decorated_pot")


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
    if base == "decorated_pot" and "sherds" in nbt:
        sherds = tuple(str(item) for item in nbt["sherds"])
        plain = all(item.split(":", 1)[-1] == "brick" for item in sherds)
        return None if plain or len(sherds) != 4 else ("pot", sherds)
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


BED_LEGS = {
    "head": ((0, 0, (50, 6), 1), (13, 0, (50, 18), 2)),
    "foot": ((0, 13, (50, 0), 0), (13, 13, (50, 12), 3)),
}


def leg_pose(quarters):
    return after(QUARTER_TURN_X, after(spin_z(quarters), QUARTER_TURN_X))


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


SHULKER_SPIN = {
    "up": NO_TURN,
    "down": HALF_TURN_X,
    "south": QUARTER_TURN_X,
    "north": after(spin_z(2), QUARTER_TURN_X),
    "west": after(spin_z(1), QUARTER_TURN_X),
    "east": after(spin_z(3), QUARTER_TURN_X),
}

SHULKER_PARTS = (
    (((-0.5, -0.25, -0.5), (0.5, 0.5, 0.5)), (0, 0), (16, 12, 16)),
    (((-0.5, -0.5, -0.5), (0.5, 0.0, 0.5)), (0, 28), (16, 8, 16)),
)


def shulker_box(color, facing):
    """A lid over a base, stuck to whichever face of the block it was placed
    on -- which is a turn in three axes, not the yaw the rest of this file
    gets away with, so the boxes are turned here rather than by an angle.
    """
    texture = f"entity/shulker/shulker{f'_{color}' if color else ''}"
    spin = SHULKER_SPIN.get(facing, NO_TURN)
    pose = after(HALF_TURN_X, spin)
    return [
        box(*turned_box(spin, lo, hi), texture, **unwrap(offset, size, pose))
        for (lo, hi), offset, size in SHULKER_PARTS
    ]


PLAIN_SHERD = "entity/decorated_pot/decorated_pot_side"


def sherd_texture(item):
    name = str(item).split(":", 1)[-1]
    return (f"entity/decorated_pot/{name.removesuffix('_pottery_sherd')}_pottery_pattern"
            if name.endswith("_pottery_sherd") else PLAIN_SHERD)


def decorated_pot(angle, sherds=None):
    """A hollow pot: four sherd walls, a disc top and bottom, and a neck.

    Nothing here is a solid box. Each wall is one plane a pixel inside the
    block carrying a whole sherd square, the discs are flat 14x14 lids at
    the block's floor and ceiling, and the neck is a tube on a collar that
    stands clear above the block -- the pot is the one block entity the game
    lets out of its own cube.

    The four sherds are stored back, left, right, front, which at this
    file's yaw of zero is north, west, east, south.
    """
    base = "entity/decorated_pot/decorated_pot_base"
    walls = [sherd_texture(item) for item in sherds] if sherds else [PLAIN_SHERD] * 4
    near, far = 1 / 16, 15 / 16
    disc = {"down": (0, 13, 14, 27), "up": (14, 13, 28, 27)}
    wall = (1, 0, 15, 16)
    sides = (
        ("north", (near, 0, near), (far, 1, near)),
        ("west", (near, 0, near), (near, 1, far)),
        ("east", (far, 0, near), (far, 1, far)),
        ("south", (near, 0, far), (far, 1, far)),
    )
    return [
        box(lo, hi, texture, faces={face: wall}, angle=angle)
        for (face, lo, hi), texture in zip(sides, walls)
    ] + [
        box((near, 0, near), (far, 0, far), base, faces=disc, angle=angle),
        box((near, 1, near), (far, 1, far), base, faces=disc, angle=angle),

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
        return shulker_box(color, props.get("facing", "up"))
    if name == "minecraft:bell":
        texture = "entity/bell/bell_body"
        return [
            cube((5, 6, 5), (6, 7, 6), (0, 0), texture, NO_TURN),
            cube((4, 4, 4), (8, 2, 8), (0, 13), texture, NO_TURN),
        ]
    if name == "minecraft:conduit":
        return [cube((5, 5, 5), (6, 6, 6), (0, 0), "entity/conduit/base", NO_TURN)]
    if name == "minecraft:decorated_pot":
        sherds = content[1] if content and content[0] == "pot" else None
        return decorated_pot(angle_for(props), sherds)
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
