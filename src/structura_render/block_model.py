"""Resolve vanilla blockstate/model JSON into textured quads."""
import json
import math
from functools import wraps

from .assets import ASSETS

BLOCKSTATES = ASSETS / "blockstates"
MODELS = ASSETS / "models/block"

DIRECTIONS = ("up", "down", "north", "south", "east", "west")
AXIS_VEC = {
    "up": (0, 1, 0), "down": (0, -1, 0),
    "north": (0, 0, -1), "south": (0, 0, 1),
    "east": (1, 0, 0), "west": (-1, 0, 0),
}
VEC_AXIS = {v: k for k, v in AXIS_VEC.items()}

FACE_CORNERS = {
    "up": (4, 5, 6, 7), "down": (0, 1, 2, 3),
    "north": (1, 0, 4, 5), "south": (3, 2, 6, 7),
    "east": (2, 1, 5, 6), "west": (0, 3, 7, 4),
}
FACE_UV_BASIS = {
    "up": ((1, 0, 0), (0, 0, 1)), "down": ((1, 0, 0), (0, 0, 1)),
    "north": ((-1, 0, 0), (0, 1, 0)), "south": ((1, 0, 0), (0, 1, 0)),
    "east": ((0, 0, -1), (0, 1, 0)), "west": ((0, 0, 1), (0, 1, 0)),
}
FACE_UV_PLANE = {
    "up": (0, 2), "down": (0, 2),
    "north": (0, 1), "south": (0, 1),
    "east": (2, 1), "west": (2, 1),
}

_blockstate_cache = {}
_model_cache = {}
_RESOLUTION_ERRORS = (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError)


def safe(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except _RESOLUTION_ERRORS:
            return None
    return wrapper


def strip_ns(name):
    name = name.split(":", 1)[-1]
    return name[len("block/"):] if name.startswith("block/") else name


def load_blockstate(name):
    name = strip_ns(name)
    if name not in _blockstate_cache:
        path = BLOCKSTATES / f"{name}.json"
        _blockstate_cache[name] = json.loads(path.read_text()) if path.exists() else None
    return _blockstate_cache[name]


def load_model(name):
    name = strip_ns(name)
    if name not in _model_cache:
        path = MODELS / f"{name}.json"
        _model_cache[name] = json.loads(path.read_text()) if path.exists() else None
    return _model_cache[name]


def resolve_model(name, depth=0):
    if depth > 10:
        return {"elements": None, "textures": {}}
    data = load_model(name)
    if data is None:
        return {"elements": None, "textures": {}}
    parent = data.get("parent")
    base = resolve_model(parent, depth + 1) if parent else {"elements": None, "textures": {}}
    return {
        "elements": data.get("elements", base["elements"]),
        "textures": {**base["textures"], **data.get("textures", {})},
    }


def resolve_texture(ref, textures, depth=0):
    if ref is None or depth > 10:
        return None
    if isinstance(ref, dict):
        return resolve_texture(ref.get("sprite"), textures, depth + 1)
    key = ref[1:] if ref.startswith("#") else ref
    if key in textures:
        return resolve_texture(textures[key], textures, depth + 1)
    return strip_ns(ref) if not ref.startswith("#") else None


def matching_variant(variants, props):
    parsed = []
    for key, value in variants.items():
        pairs = tuple(pair.split("=", 1) for pair in key.split(",")) if key else ()
        parsed.append((dict(pairs), value))
    matches = [
        (len(wanted), value)
        for wanted, value in parsed
        if all(props.get(k) == v for k, v in wanted.items())
    ]
    return max(matches, key=lambda item: item[0])[1] if matches else (parsed[0][1] if parsed else None)


def condition_matches(condition, props):
    if "OR" in condition:
        return any(condition_matches(part, props) for part in condition["OR"])
    if "AND" in condition:
        return all(condition_matches(part, props) for part in condition["AND"])
    return all(props.get(key) in str(wanted).split("|") for key, wanted in condition.items())


def selected_models(blockstate, props):
    if "variants" in blockstate:
        entries = [matching_variant(blockstate["variants"], props)]
    else:
        entries = [
            part["apply"] for part in blockstate.get("multipart", ())
            if "when" not in part or condition_matches(part["when"], props)
        ]
    return [entry[0] if isinstance(entry, list) else entry for entry in entries if entry]


def _rotate(point, origin, axis, degrees):
    angle = math.radians(degrees)
    cosine, sine = math.cos(angle), math.sin(angle)
    x, y, z = (point[i] - origin[i] for i in range(3))
    if axis == "x":
        y, z = y * cosine - z * sine, y * sine + z * cosine
    elif axis == "y":
        x, z = x * cosine - z * sine, x * sine + z * cosine
    else:
        x, y = x * cosine - y * sine, x * sine + y * cosine
    return x + origin[0], y + origin[1], z + origin[2]


def rotate_vector(vector, x_deg, y_deg):
    rotated = _rotate(vector, (0, 0, 0), "x", x_deg)
    return tuple(round(v) for v in _rotate(rotated, (0, 0, 0), "y", y_deg))


def rotate_direction(direction, x_deg, y_deg):
    return VEC_AXIS[rotate_vector(AXIS_VEC[direction], x_deg, y_deg)]


def rotate_element(point, rotation):
    if not rotation:
        return point
    origin = rotation.get("origin", (8, 8, 8))
    if "axis" not in rotation:
        for axis in "xyz":
            point = _rotate(point, origin, axis, rotation.get(axis, 0))
        return point
    axis, angle = rotation["axis"], rotation["angle"]
    if rotation.get("rescale"):
        scale = 1 / math.cos(math.radians(angle))
        point = tuple(
            origin[i] + (point[i] - origin[i]) * (1 if "xyz"[i] == axis else scale)
            for i in range(3)
        )
    return _rotate(point, origin, axis, angle)


def rotate_blockstate(point, x_deg, y_deg):
    point = _rotate(point, (8, 8, 8), "x", x_deg)
    return _rotate(point, (8, 8, 8), "y", y_deg)


def box_corners(lo, hi):
    return (
        (lo[0], lo[1], lo[2]), (hi[0], lo[1], lo[2]),
        (hi[0], lo[1], hi[2]), (lo[0], lo[1], hi[2]),
        (lo[0], hi[1], lo[2]), (hi[0], hi[1], lo[2]),
        (hi[0], hi[1], hi[2]), (lo[0], hi[1], hi[2]),
    )


def _neg(vector):
    return tuple(-v for v in vector)


def uvlock_quarters(direction, x_deg, y_deg):
    world_direction = rotate_direction(direction, x_deg, y_deg)
    u, v = (rotate_vector(axis, x_deg, y_deg) for axis in FACE_UV_BASIS[direction])
    target_u, target_v = FACE_UV_BASIS[world_direction]
    choices = ((u, v), (v, _neg(u)), (_neg(u), _neg(v)), (_neg(v), u))
    return next((i for i, basis in enumerate(choices) if basis == (target_u, target_v)), 0)


@safe
def post_texture(name):
    model = resolve_model(f"{strip_ns(name)}_post")
    return resolve_texture(model["textures"].get("particle"), model["textures"])


@safe
def block_elements(name, props):
    blockstate = load_blockstate(name)
    if blockstate is None:
        return None
    entries = selected_models(blockstate, props)
    result = []
    for entry in entries:
        model = resolve_model(entry["model"])
        if not model["elements"]:
            continue
        x_deg, y_deg = entry.get("x", 0), entry.get("y", 0)
        for element in model["elements"]:
            lo, hi = element["from"], element["to"]
            corners = [
                rotate_blockstate(rotate_element(point, element.get("rotation")), x_deg, y_deg)
                for point in box_corners(lo, hi)
            ]
            faces = {}
            for direction, face in element.get("faces", {}).items():
                texture = resolve_texture(face.get("texture"), model["textures"])
                if texture is None:
                    continue
                uv = face.get("uv", default_uv(direction, lo, hi))
                world_direction = rotate_direction(direction, x_deg, y_deg)
                cullface = face.get("cullface")
                cullface = {"top": "up", "bottom": "down"}.get(cullface, cullface)
                faces[world_direction] = {
                    "texture": texture,
                    "uv": tuple(value / 16 for value in uv),
                    "uv_rotation": (
                        face.get("rotation", 0) // 90
                        + (uvlock_quarters(direction, x_deg, y_deg) if entry.get("uvlock") else 0)
                    ) % 4,
                    "vertices": tuple(
                        tuple(value / 16 for value in corners[i])
                        for i in FACE_CORNERS[direction]
                    ),
                    "cullface": rotate_direction(cullface, x_deg, y_deg) if cullface else None,
                    "tinted": "tintindex" in face,
                }
            if faces:
                result.append({
                    "lo": tuple(min(point[i] for point in corners) / 16 for i in range(3)),
                    "hi": tuple(max(point[i] for point in corners) / 16 for i in range(3)),
                    "faces": faces,
                })
    return result if result else ([] if entries else None)


def default_uv(direction, lo, hi):
    a, b = FACE_UV_PLANE[direction]
    lo_b, hi_b = lo[b], hi[b]
    if b == 1:
        lo_b, hi_b = 16 - hi[b], 16 - lo[b]
    return lo[a], lo_b, hi[a], hi_b
