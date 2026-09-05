"""Check every entity unwrap against Minecraft's own model arithmetic.

These shapes fail silently. A crop on the wrong face or an image turned the
wrong way still renders -- as a bed with its pillow at the seam, a skull
looking backwards, a chest whose halves leave a gap -- and nothing complains.
So this file rebuilds the arithmetic the game does, from ModelPart.Cube and
each block entity renderer's own transform, and asserts that entity_shapes
lands every crop on the same face, the same way round.

Nothing here reads a texture or a jar: it is one box definition and one
matrix per shape, taken from the game's source, against our tables.
"""

import numpy as np
import pytest
from PIL import Image

from structura_render.entity_shapes import (
    HALF_TURN_X, HALF_TURN_Y, HALF_TURN_Z, NO_TURN, QUARTER_TURN_X, TURNS,
    WORLD_UV, after, leg_pose, unwrap,
)
from structura_render.entity_shapes import SHULKER_SPIN as SHULKER_SPIN_POSE

AXES = {"east": (1, 0, 0), "west": (-1, 0, 0), "up": (0, 1, 0),
        "down": (0, -1, 0), "south": (0, 0, 1), "north": (0, 0, -1)}


def direction(vector):
    length = np.linalg.norm(vector)
    if length == 0:
        return None
    unit = np.asarray(vector, dtype=float) / length
    return next((name for name, ref in AXES.items() if np.allclose(unit, ref, atol=1e-4)), None)


def translate(x, y, z):
    matrix = np.eye(4)
    matrix[:3, 3] = (x, y, z)
    return matrix


def scale(x, y, z):
    return np.diag([x, y, z, 1.0])


def rotate(axis, degrees):
    cos, sin = np.cos(np.radians(degrees)), np.sin(np.radians(degrees))
    matrix = np.eye(4)
    rows = {"x": (1, 2), "y": (2, 0), "z": (0, 1)}[axis]
    a, b = rows
    matrix[a, a] = matrix[b, b] = cos
    matrix[a, b], matrix[b, a] = -sin, sin
    return matrix


def part_pose(x=0, y=0, z=0, xrot=0, yrot=0, zrot=0):
    """PartPose, applied the way ModelPart.translateAndRotate applies it."""
    return (translate(x / 16, y / 16, z / 16)
            @ rotate("z", zrot) @ rotate("y", yrot) @ rotate("x", xrot))


def around(matrix, x, y, z):
    return translate(x, y, z) @ matrix @ translate(-x, -y, -z)


# ModelPart.Cube: which corners each polygon uses, and the corners of the
# texture rectangle they are given, in the order the Polygon constructor
# assigns them.
CORNERS = {
    "t0": ("min", "min", "min"), "t1": ("max", "min", "min"),
    "t2": ("max", "max", "min"), "t3": ("min", "max", "min"),
    "l0": ("min", "min", "max"), "l1": ("max", "min", "max"),
    "l2": ("max", "max", "max"), "l3": ("min", "max", "max"),
}
POLYGONS = {
    "down":  (("l1", "l0", "t0", "t1"), "u1", "v0", "u2", "v1"),
    "up":    (("t2", "t3", "l3", "l2"), "u2", "v1", "u22", "v0"),
    "west":  (("t0", "l0", "l3", "t3"), "u0", "v1", "u1", "v2"),
    "north": (("t1", "t0", "t3", "t2"), "u1", "v1", "u2", "v2"),
    "east":  (("l1", "t1", "t2", "l2"), "u2", "v1", "u3", "v2"),
    "south": (("l0", "l1", "l2", "l3"), "u3", "v1", "u4", "v2"),
}


def game_faces(matrix, offset, origin, size, grow=0.0):
    """{world face: (crop, image right, image down)} for one posed box."""
    u, v = offset
    (x, y, z), (w, h, d) = origin, size
    edge = {
        "minX": x - grow, "minY": y - grow, "minZ": z - grow,
        "maxX": x + w + grow, "maxY": y + h + grow, "maxZ": z + d + grow,
    }
    span = {"u0": u, "u1": u + d, "u2": u + d + w, "u22": u + d + 2 * w,
            "u3": u + 2 * d + w, "u4": u + 2 * d + 2 * w,
            "v0": v, "v1": v + d, "v2": v + d + h}
    result = {}
    for keys, left, top, right, bottom in POLYGONS.values():
        points = np.array([
            [matrix @ np.array([edge[f"{end}{axis}"] / 16 for end, axis
                                in zip(CORNERS[key], "XYZ")] + [1.0])][0][:3]
            for key in keys
        ])
        u0, u1 = span[left], span[right]
        v0, v1 = span[top], span[bottom]
        world = direction(np.cross(points[1] - points[0], points[2] - points[1]))
        if world is None:
            continue
        result[world] = (
            (min(u0, u1), min(v0, v1), max(u0, u1), max(v0, v1)),
            direction(points[0] - points[1]),
            direction((points[2] - points[1]) * (1 if v1 > v0 else -1)),
        )
    return result


YAW = {"south": 0, "west": 90, "north": 180, "east": 270}
FACING = "north"

BED_BASE = (translate(0, 0.5625, 0) @ rotate("x", 90)
            @ around(rotate("z", 180 + YAW[FACING]), 0.5, 0.5, 0.5))
CHEST_BASE = around(rotate("y", -YAW[FACING]), 0.5, 0.0, 0.5)
SKULL_BASE = translate(0.5, 0, 0.5) @ scale(-1, -1, 1)
BANNER_BASE = translate(0.5, 0, 0.5) @ scale(2 / 3, -2 / 3, -2 / 3)
WALL_BANNER_BASE = (translate(0.5, 0, 0.5) @ rotate("y", -YAW[FACING])
                    @ scale(2 / 3, -2 / 3, -2 / 3))
SIGN_BASE = translate(0.5, 0.5, 0.5) @ scale(2 / 3, -2 / 3, -2 / 3)
WALL_SIGN_BASE = (translate(0.5, 0.5, 0.5) @ rotate("y", -YAW[FACING])
                  @ translate(0, -0.3125, -0.4375) @ scale(2 / 3, -2 / 3, -2 / 3))
HANGING_SIGN_BASE = (translate(0.5, 0.9375, 0.5) @ translate(0, -0.3125, 0)
                     @ scale(1, -1, -1))
# Direction.getRotation(), composed the way JOML's rotationXYZ does: X, then
# Y, then Z, with Z reaching the point first.
SHULKER_SPIN = {
    "up": np.eye(4),
    "down": rotate("x", 180),
    "north": rotate("x", 90) @ rotate("z", 180),
    "south": rotate("x", 90),
    "west": rotate("x", 90) @ rotate("z", 90),
    "east": rotate("x", 90) @ rotate("z", -90),
}


def shulker_base(facing):
    return (translate(0.5, 0.5, 0.5) @ SHULKER_SPIN[facing]
            @ scale(1, -1, -1) @ translate(0, -1, 0))


SHULKER_BASE = shulker_base("up")
POT_BASE = around(rotate("y", 180 - YAW[FACING]), 0.5, 0.5, 0.5)

# label, model transform, texture offset, box origin, box size, our pose, grow
BOXES = [
    ("skull", SKULL_BASE, (0, 0), (-4, -8, -4), (8, 8, 8), HALF_TURN_Z, 0),
    ("chest body", CHEST_BASE, (0, 19), (1, 0, 1), (14, 10, 14), HALF_TURN_Y, 0),
    ("chest lid", CHEST_BASE @ part_pose(0, 9, 1), (0, 0), (1, 0, 0), (14, 5, 14),
     HALF_TURN_Y, 0),
    ("chest latch", CHEST_BASE @ part_pose(0, 9, 1), (0, 0), (7, -2, 14), (2, 4, 1),
     HALF_TURN_Y, 0),
    ("double chest left", CHEST_BASE, (0, 19), (0, 0, 1), (15, 10, 14), HALF_TURN_Y, 0),
    ("double chest right", CHEST_BASE, (0, 19), (1, 0, 1), (15, 10, 14), HALF_TURN_Y, 0),
    ("bed head", BED_BASE, (0, 0), (0, 0, 0), (16, 16, 6), QUARTER_TURN_X, 0),
    ("bed foot", BED_BASE, (0, 22), (0, 0, 0), (16, 16, 6), QUARTER_TURN_X, 0),
    ("bed head left leg", BED_BASE @ part_pose(0, 0, 0, 90, 0, 90), (50, 6),
     (0, 6, 0), (3, 3, 3), leg_pose(1), 0),
    ("bed head right leg", BED_BASE @ part_pose(0, 0, 0, 90, 0, 180), (50, 18),
     (-16, 6, 0), (3, 3, 3), leg_pose(2), 0),
    ("bed foot left leg", BED_BASE @ part_pose(0, 0, 0, 90, 0, 0), (50, 0),
     (0, 6, -16), (3, 3, 3), leg_pose(0), 0),
    ("bed foot right leg", BED_BASE @ part_pose(0, 0, 0, 90, 0, 270), (50, 12),
     (-16, 6, -16), (3, 3, 3), leg_pose(3), 0),
    ("banner cloth", BANNER_BASE @ part_pose(0, -44, 0), (0, 0), (-10, 0, -2),
     (20, 40, 1), HALF_TURN_X, 0),
    ("banner pole", BANNER_BASE, (44, 0), (-1, -42, -1), (2, 42, 2), HALF_TURN_X, 0),
    ("banner bar", BANNER_BASE, (0, 42), (-10, -44, -1), (20, 2, 2), HALF_TURN_X, 0),
    ("wall banner cloth", WALL_BANNER_BASE @ part_pose(0, -20.5, 10.5), (0, 0),
     (-10, 0, -2), (20, 40, 1), HALF_TURN_Z, 0),
    ("wall banner bar", WALL_BANNER_BASE, (0, 42), (-10, -20.5, 9.5), (20, 2, 2),
     HALF_TURN_Z, 0),
    ("sign board", SIGN_BASE, (0, 0), (-12, -14, -1), (24, 12, 2), HALF_TURN_X, 0),
    ("sign stick", SIGN_BASE, (0, 14), (-1, -2, -1), (2, 14, 2), HALF_TURN_X, 0),
    ("wall sign board", WALL_SIGN_BASE, (0, 0), (-12, -14, -1), (24, 12, 2),
     HALF_TURN_Z, 0),
    ("hanging sign board", HANGING_SIGN_BASE, (0, 12), (-7, 0, -1), (14, 10, 2),
     HALF_TURN_X, 0),
    ("shulker lid", SHULKER_BASE @ part_pose(0, 24, 0), (0, 0), (-8, -16, -8),
     (16, 12, 16), HALF_TURN_X, 0),
    ("shulker base", SHULKER_BASE @ part_pose(0, 24, 0), (0, 28), (-8, -8, -8),
     (16, 8, 16), HALF_TURN_X, 0),
    ("pot neck", POT_BASE @ part_pose(0, 37, 16, 180, 0, 0), (0, 0), (4, 17, 4),
     (8, 3, 8), HALF_TURN_X, -0.1),
    ("pot collar", POT_BASE @ part_pose(0, 37, 16, 180, 0, 0), (0, 5), (5, 20, 5),
     (6, 1, 6), HALF_TURN_X, 0.2),
    ("pot disc", POT_BASE @ part_pose(1, 16, 1), (-14, 13), (0, 0, 0), (14, 0, 14),
     NO_TURN, 0),
    *[(f"shulker {name} {facing}", shulker_base(facing) @ part_pose(0, 24, 0),
       offset, origin, size, after(HALF_TURN_X, SHULKER_SPIN_POSE[facing]), 0)
      for facing in SHULKER_SPIN
      for name, offset, origin, size in (
          ("lid", (0, 0), (-8, -16, -8), (16, 12, 16)),
          ("base", (0, 28), (-8, -8, -8), (16, 8, 16)))],
    ("bell body", part_pose(8, 12, 8), (0, 0), (-3, -6, -3), (6, 7, 6), NO_TURN, 0),
    ("bell lip", part_pose(8, 12, 8) @ part_pose(-8, -12, -8), (0, 13), (4, 4, 4),
     (8, 2, 8), NO_TURN, 0),
]


@pytest.mark.parametrize(
    "label,matrix,offset,origin,size,pose,grow",
    BOXES, ids=[row[0] for row in BOXES],
)
def test_unwrap_matches_the_game(label, matrix, offset, origin, size, pose, grow):
    ours = unwrap(offset, size, pose)
    for world, (crop, right, down) in game_faces(matrix, offset, origin, size, grow).items():
        assert ours["faces"][world] == crop, f"{label}: {world} crop"
        turn = ours["turns"].get(world)
        assert TURNS[turn](right, down) == WORLD_UV[world], f"{label}: {world} turn"


def game_box(matrix, origin, size, grow=0.0):
    """The world corners of one posed box, low and high."""
    (x, y, z), (w, h, d) = origin, size
    lo = np.array([x - grow, y - grow, z - grow]) / 16
    hi = np.array([x + w + grow, y + h + grow, z + d + grow]) / 16
    corners = np.array([[matrix @ np.array([a, b, c, 1.0])][0][:3]
                        for a in (lo[0], hi[0]) for b in (lo[1], hi[1])
                        for c in (lo[2], hi[2])])
    return tuple(np.round(corners.min(axis=0), 6)), tuple(np.round(corners.max(axis=0), 6))


# The same boxes again, as the world volumes each one should occupy, against
# the state that draws it. A crop landing on the right face of a box in the
# wrong place is still wrong.
PLACEMENTS = [
    ("minecraft:player_head", {"rotation": "0"}, [
        (SKULL_BASE, (-4, -8, -4), (8, 8, 8), 0)]),
    ("minecraft:chest", {"facing": FACING, "type": "single"}, [
        (CHEST_BASE, (1, 0, 1), (14, 10, 14), 0),
        (CHEST_BASE @ part_pose(0, 9, 1), (1, 0, 0), (14, 5, 14), 0),
        (CHEST_BASE @ part_pose(0, 9, 1), (7, -2, 14), (2, 4, 1), 0)]),
    ("minecraft:chest", {"facing": FACING, "type": "left"}, [
        (CHEST_BASE, (0, 0, 1), (15, 10, 14), 0),
        (CHEST_BASE @ part_pose(0, 9, 1), (0, 0, 0), (15, 5, 14), 0),
        (CHEST_BASE @ part_pose(0, 9, 1), (0, -2, 14), (1, 4, 1), 0)]),
    ("minecraft:chest", {"facing": FACING, "type": "right"}, [
        (CHEST_BASE, (1, 0, 1), (15, 10, 14), 0),
        (CHEST_BASE @ part_pose(0, 9, 1), (1, 0, 0), (15, 5, 14), 0),
        (CHEST_BASE @ part_pose(0, 9, 1), (15, -2, 14), (1, 4, 1), 0)]),
    ("minecraft:red_bed", {"facing": FACING, "part": "head"}, [
        (BED_BASE, (0, 0, 0), (16, 16, 6), 0),
        (BED_BASE @ part_pose(0, 0, 0, 90, 0, 90), (0, 6, 0), (3, 3, 3), 0),
        (BED_BASE @ part_pose(0, 0, 0, 90, 0, 180), (-16, 6, 0), (3, 3, 3), 0)]),
    ("minecraft:red_bed", {"facing": FACING, "part": "foot"}, [
        (BED_BASE, (0, 0, 0), (16, 16, 6), 0),
        (BED_BASE @ part_pose(0, 0, 0, 90, 0, 0), (0, 6, -16), (3, 3, 3), 0),
        (BED_BASE @ part_pose(0, 0, 0, 90, 0, 270), (-16, 6, -16), (3, 3, 3), 0)]),
    ("minecraft:white_banner", {"rotation": "0"}, [
        (BANNER_BASE @ part_pose(0, -44, 0), (-10, 0, -2), (20, 40, 1), 0),
        (BANNER_BASE, (-1, -42, -1), (2, 42, 2), 0),
        (BANNER_BASE, (-10, -44, -1), (20, 2, 2), 0)]),
    ("minecraft:white_wall_banner", {"facing": FACING}, [
        (WALL_BANNER_BASE @ part_pose(0, -20.5, 10.5), (-10, 0, -2), (20, 40, 1), 0),
        (WALL_BANNER_BASE, (-10, -20.5, 9.5), (20, 2, 2), 0)]),
    ("minecraft:oak_sign", {"rotation": "0"}, [
        (SIGN_BASE, (-12, -14, -1), (24, 12, 2), 0),
        (SIGN_BASE, (-1, -2, -1), (2, 14, 2), 0)]),
    ("minecraft:oak_wall_sign", {"facing": FACING}, [
        (WALL_SIGN_BASE, (-12, -14, -1), (24, 12, 2), 0)]),
    ("minecraft:bell", {"facing": FACING, "attachment": "floor"}, [
        (part_pose(8, 12, 8), (-3, -6, -3), (6, 7, 6), 0),
        (part_pose(8, 12, 8) @ part_pose(-8, -12, -8), (4, 4, 4), (8, 2, 8), 0)]),
    *[("minecraft:red_shulker_box", {"facing": facing}, [
        (shulker_base(facing) @ part_pose(0, 24, 0), (-8, -8, -8), (16, 8, 16), 0),
        (shulker_base(facing) @ part_pose(0, 24, 0), (-8, -16, -8), (16, 12, 16), 0)])
      for facing in SHULKER_SPIN],
]


@pytest.mark.parametrize(
    "name,props,parts", PLACEMENTS,
    ids=[f"{name.split(':')[1]} {'/'.join(sorted(props.values()))}"
         for name, props, _ in PLACEMENTS],
)
def test_boxes_sit_where_the_game_puts_them(name, props, parts):
    from structura_render.entity_shapes import entity_shape

    drawn = [(tuple(np.round(part["lo"], 6)), tuple(np.round(part["hi"], 6)))
             for part in entity_shape(name, props)]
    expected = [game_box(matrix, origin, size, grow) for matrix, origin, size, grow in parts]
    assert sorted(drawn) == sorted(expected)


def test_turns_match_pillow():
    """The turn table has to say what Pillow actually does.

    Every entry but the two 90-degree rotations is its own inverse, so a
    table written back to front still passes every other check in this file
    -- both sides of the comparison would be wrong the same way. This is the
    one place the table meets the library it describes.
    """
    from structura_render.entity_shapes import OPPOSITE, TURNS

    width, height = 4, 2
    pixels = np.array([[10 * x + y for x in range(width)] for y in range(height)],
                      dtype=np.uint8)
    source = Image.fromarray(pixels)
    step = {(1, 0): "east", (-1, 0): "west", (0, 1): "down", (0, -1): "up"}
    for turn, moves in TURNS.items():
        if turn is None:
            continue
        out = np.asarray(source.transpose(turn))
        where = {int(v): (row, col) for row, line in enumerate(out)
                 for col, v in enumerate(line)}
        origin, along_x, along_y = where[0], where[10], where[1]
        right = step[(along_x[1] - origin[1], along_x[0] - origin[0])]
        down = step[(along_y[1] - origin[1], along_y[0] - origin[0])]
        # Read the turned image the ordinary way, and see which way a crop
        # drawn right=east, down=down now runs.
        frame = {right: "east", OPPOSITE[right]: "west",
                 down: "down", OPPOSITE[down]: "up"}
        assert moves("east", "down") == (frame["east"], frame["down"]), turn
