"""Generic vanilla block-model resolver: blockstate -> model -> parent chain,
real elements/uv/rotation from assets/minecraft, no per-block guessing. This
is the single source of block shape+texture-mapping for both render_hero.py
(PyVista PNG) and export_usdz.py (USDZ) -- render only consumes its output,
never re-derives geometry of its own for blocks this module can resolve.

An element's own (non-blockstate) "rotation" -- a per-element tilt at an
arbitrary angle, used for cross-plants, potted plants and coral fans -- is
ignored rather than applied: the element renders at its un-tilted from/to.
Fine for already-thin/degenerate elements (a coral fan's near-zero-height
wafer, a plant's thin diagonal blade), which is what this ever appears on."""
import json
from functools import wraps
from pathlib import Path

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
    textures = {**base["textures"], **data.get("textures", {})}
    elements = data.get("elements", base["elements"])
    return {"elements": elements, "textures": textures}


def resolve_texture(ref, textures, depth=0):
    if ref is None or depth > 10:
        return None
    key = ref[1:] if ref.startswith("#") else ref
    if key in textures:
        return resolve_texture(textures[key], textures, depth + 1)
    if not ref.startswith("#"):
        return strip_ns(ref)
    return None


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
    if matches:
        return max(matches, key=lambda item: item[0])[1]
    return parsed[0][1] if parsed else None


def rotate_point(x, y, z, x_deg, y_deg):
    for _ in range(round(x_deg / 90) % 4):
        y, z = 16 - z, y
    for _ in range(round(y_deg / 90) % 4):
        x, z = 16 - z, x
    return x, y, z


def rotate_direction(direction, x_deg, y_deg):
    dx, dy, dz = AXIS_VEC[direction]
    for _ in range(round(x_deg / 90) % 4):
        dy, dz = -dz, dy
    for _ in range(round(y_deg / 90) % 4):
        dx, dz = -dz, dx
    return VEC_AXIS[(dx, dy, dz)]


@safe
def post_texture(name):
    model = resolve_model(f"{strip_ns(name)}_post")
    return resolve_texture(model["textures"].get("particle"), model["textures"])


@safe
def block_elements(name, props):
    blockstate = load_blockstate(name)
    if blockstate is None or "variants" not in blockstate:
        return None
    entry = matching_variant(blockstate["variants"], props)
    if isinstance(entry, list):
        entry = entry[0]
    if entry is None:
        return None
    model = resolve_model(entry["model"])
    if not model["elements"]:
        return None
    x_deg, y_deg = entry.get("x", 0), entry.get("y", 0)
    textures = model["textures"]

    result = []
    for element in model["elements"]:
        lo_raw, hi_raw = element["from"], element["to"]
        corners = [
            rotate_point(x, y, z, x_deg, y_deg)
            for x in (lo_raw[0], hi_raw[0])
            for y in (lo_raw[1], hi_raw[1])
            for z in (lo_raw[2], hi_raw[2])
        ]
        lo = tuple(min(c[i] for c in corners) / 16 for i in range(3))
        hi = tuple(max(c[i] for c in corners) / 16 for i in range(3))

        faces = {}
        for raw_direction, face in element.get("faces", {}).items():
            texture = resolve_texture(face.get("texture"), textures)
            if texture is None:
                continue
            uv = face.get("uv")
            if uv is None:
                uv = default_uv(raw_direction, lo_raw, hi_raw)
            cullface = face.get("cullface")
            world_direction = rotate_direction(raw_direction, x_deg, y_deg)
            faces[world_direction] = {
                "texture": texture,
                "uv": tuple(v / 16 for v in uv),
                "cullface": rotate_direction(cullface, x_deg, y_deg) if cullface else None,
                "tinted": "tintindex" in face,
            }
        result.append({"lo": lo, "hi": hi, "faces": faces})
    return result


FACE_UV_PLANE = {
    "up": (0, 2), "down": (0, 2),
    "north": (0, 1), "south": (0, 1),
    "east": (2, 1), "west": (2, 1),
}


def default_uv(direction, lo, hi):
    a, b = FACE_UV_PLANE[direction]
    lo_b, hi_b = lo[b], hi[b]
    if b == 1:
        lo_b, hi_b = 16 - hi[b], 16 - lo[b]
    return lo[a], lo_b, hi[a], hi_b
