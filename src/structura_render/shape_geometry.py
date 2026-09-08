from PIL import Image


def box(lo, hi, texture, crop=None, tint=None, alpha=255, angle=0, faces=None, turns=None):
    return {
        "lo": lo, "hi": hi, "texture": texture, "crop": crop, "tint": tint,
        "alpha": alpha, "angle": angle, "faces": faces, "turns": turns,
    }


def angle_for(props):
    if "rotation" in props:
        return int(props["rotation"]) * 22.5
    return {"north": 0, "east": 90, "south": 180, "west": 270}.get(props.get("facing"), 0)


OPPOSITE = {
    "up": "down", "down": "up", "north": "south",
    "south": "north", "east": "west", "west": "east",
}

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
    Image.ROTATE_90: lambda right, down: (down, OPPOSITE[right]),
    Image.ROTATE_270: lambda right, down: (OPPOSITE[down], right),
    Image.TRANSPOSE: lambda right, down: (down, right),
    Image.TRANSVERSE: lambda right, down: (OPPOSITE[down], OPPOSITE[right]),
}

HALF_TURN_X = {"up": "down", "down": "up", "north": "south", "south": "north",
               "east": "east", "west": "west"}

HALF_TURN_Y = {"up": "up", "down": "down", "north": "south", "south": "north",
               "east": "west", "west": "east"}

HALF_TURN_Z = {"up": "down", "down": "up", "north": "north", "south": "south",
               "east": "west", "west": "east"}

QUARTER_TURN_X = {"up": "south", "down": "north", "north": "up",
                  "south": "down", "east": "east", "west": "west"}

NO_TURN = {name: name for name in OPPOSITE}

SPIN_Z = {"east": "up", "up": "west", "west": "down", "down": "east",
          "north": "north", "south": "south"}

MODEL_AXES = ("east", "up", "south")

SIGNED_AXIS = {"east": (0, 1), "west": (0, -1), "up": (1, 1),
               "down": (1, -1), "south": (2, 1), "north": (2, -1)}


def after(first, second):
    """The pose of a model turned by `first` and then by `second`."""
    return {face: second[direction] for face, direction in first.items()}


def spin_z(quarters):
    pose = NO_TURN
    for _ in range(quarters):
        pose = after(pose, SPIN_Z)
    return pose


def turned_box(pose, lo, hi):
    """Where a box given about its block's centre ends up once turned."""
    low, high = [0.0] * 3, [0.0] * 3
    for index, model_axis in enumerate(MODEL_AXES):
        axis, sign = SIGNED_AXIS[pose[model_axis]]
        low[axis], high[axis] = ((lo[index], hi[index]) if sign > 0
                                 else (-hi[index], -lo[index]))
    return tuple(v + 0.5 for v in low), tuple(v + 0.5 for v in high)


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


def _scale_parts(parts, factor):
    if factor == 1:
        return parts
    for part in parts:
        part["lo"] = tuple(value * factor for value in part["lo"])
        part["hi"] = tuple(value * factor for value in part["hi"])
        if "quads" in part:
            part["quads"] = tuple(
                tuple(tuple(value * factor for value in point) for point in quad)
                for quad in part["quads"]
            )
    return parts
