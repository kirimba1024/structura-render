import json
import math
from functools import partial

from PIL import Image

from .assets import context_cached, current_context
from .diagnostics import report_issue
from .entity_models import model_parts
from .entity_shapes import HALF_TURN_X, QUARTER_TURN_X, after, box, unwrap
from .item_models import item_id, item_texture, stack_texture

HORIZONTAL = ("south", "west", "north", "east")
DIRECTION = ("down", "up", "north", "south", "west", "east")
AXIS = {"south": (2, 1), "north": (2, -1), "east": (0, 1), "west": (0, -1)}
NORMAL = {
    "down": (0, -1, 0), "up": (0, 1, 0), "north": (0, 0, -1),
    "south": (0, 0, 1), "west": (-1, 0, 0), "east": (1, 0, 0),
}
DEPTH = 1 / 16
FRAME_SIDE = 12 / 16


def _plain(value):
    return str(value).split(":", 1)[-1].lower()


def _number(value, default=0.0):
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return default


def _flag(nbt, key):
    return key in nbt and bool(int(_number(nbt[key])))


def _values(container, key):
    values = container.get(key) if hasattr(container, "get") else None
    if values is None:
        return None
    try:
        return tuple(_number(value) for value in values)
    except TypeError:
        return None


def facing_of(nbt):
    for key in ("facing", "Facing", "Direction"):
        if key not in nbt:
            continue
        raw = str(nbt[key])
        try:
            value = int(raw)
        except ValueError:
            direction = _plain(raw)
            return direction if direction in NORMAL else "south"
        if key == "Facing" and 0 <= value < len(DIRECTION):
            return DIRECTION[value]
        return HORIZONTAL[value % len(HORIZONTAL)]
    return "south"


@context_cached
def painting_size(variant):
    data_root = current_context().data
    if data_root is None:
        return None
    path = data_root / "painting_variant" / f"{variant}.json"
    if not path.is_file():
        return None
    try:
        entry = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    asset = _plain(entry.get("asset_id", variant))
    if not (current_context().path("textures/painting", asset, ".png")).is_file():
        return None
    return int(entry.get("width", 1)), int(entry.get("height", 1)), asset


def _span(width, height, facing):
    axis, sign = AXIS[facing]
    across = 2 - axis
    lo, hi = [0.0, 0.0, 0.0], [1.0, 1.0, 1.0]
    lo[across] = -((width - 1) // 2)
    hi[across] = lo[across] + width
    lo[1] = -((height - 1) // 2)
    hi[1] = lo[1] + height
    lo[axis], hi[axis] = (1.0, 1.0 + DEPTH) if sign > 0 else (-DEPTH, 0.0)
    return tuple(lo), tuple(hi)


def _facing_part(lo, hi, texture, facing):
    part = box(lo, hi, texture)
    part["only_faces"] = (facing,)
    return part


def _quad(texture, vertices, *, tint=None, angle=0, pivot=(0.0, 0.0)):
    part = box((0, 0, 0), (0, 0, 0), texture, tint=tint, angle=angle)
    part["quads"] = (tuple(vertices),)
    part["pivot"] = pivot
    return part


def painting_parts(nbt):
    variant = _plain(nbt.get("variant") or nbt.get("Motive") or "")
    size = painting_size(variant)
    facing = facing_of(nbt)
    if size is None or facing not in AXIS:
        return []
    width, height, asset = size
    return [_facing_part(*_span(width, height, facing), f"painting/{asset}", facing)]


def _frame_bounds(facing):
    inset = (1 - FRAME_SIDE) / 2
    lo, hi = [inset] * 3, [inset + FRAME_SIDE] * 3
    axis = next(i for i, value in enumerate(NORMAL[facing]) if value)
    sign = NORMAL[facing][axis]
    lo[axis], hi[axis] = (1.0, 1.0 + DEPTH) if sign > 0 else (-DEPTH, 0.0)
    return tuple(lo), tuple(hi)


def _item_stack(nbt):
    for key in ("Item", "item", "item_stack"):
        if key in nbt:
            return nbt[key]
    return None


def _item_quad(stack, center, side, *, facing="south", rotation=0, angle=0):
    texture = stack_texture(stack)
    if texture is None:
        if item_id(stack) is None:
            return None
        texture = _asset("block/structure_block", "block/red_wool")
    normal = NORMAL[facing]
    if facing in ("up", "down"):
        right, upward = (1, 0, 0), (0, 0, -1 if facing == "up" else 1)
    else:
        right = {
            "south": (-1, 0, 0), "north": (1, 0, 0),
            "east": (0, 0, 1), "west": (0, 0, -1),
        }[facing]
        upward = (0, 1, 0)
    radians = math.radians(rotation)
    cosine, sine = math.cos(radians), math.sin(radians)
    vertices = []
    for u, v in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        ru = (u * cosine - v * sine) * side / 2
        rv = (u * sine + v * cosine) * side / 2
        vertices.append(tuple(center[i] + right[i] * ru + upward[i] * rv
                              + normal[i] / 1024 for i in range(3)))
    return _quad(texture, vertices, angle=angle)


def item_frame_parts(nbt, glowing):
    facing = facing_of(nbt)
    lo, hi = _frame_bounds(facing)
    texture = "block/glow_item_frame" if glowing else "block/item_frame"
    result = [_facing_part(lo, hi, texture, facing)]
    stack = _item_stack(nbt)
    identifier = item_id(stack)
    if identifier:
        center = tuple((a + b) / 2 for a, b in zip(lo, hi))
        steps = int(_number(nbt.get("ItemRotation", nbt.get("item_rotation", 0)))) % 8
        side = 7 / 8 if _plain(identifier) == "filled_map" else 1 / 2
        item = _item_quad(stack, center, side, facing=facing, rotation=steps * 45)
        if item:
            result.append(item)
    return result


def _asset(*stems):
    return next((stem for stem in stems
                 if (current_context().path("textures", stem, ".png")).is_file()), stems[0])


@context_cached
def _opaque_texture_tiles(path):
    try:
        with Image.open(path) as source:
            image = source.convert("RGBA")
    except OSError:
        return ()

    visible = [pixel for pixel in image.getdata() if pixel[3] > 0]
    if not visible:
        return ()
    mean = tuple(sum(pixel[channel] for pixel in visible) / len(visible)
                 for channel in range(3))

    candidates = []
    pixels = image.load()
    for threshold in (255, 1):
        for size in (4, 2, 1):
            for y in range(0, image.height - size + 1, size):
                for x in range(0, image.width - size + 1, size):
                    tile = [pixels[x + dx, y + dy]
                            for dy in range(size) for dx in range(size)]
                    if min(pixel[3] for pixel in tile) < threshold:
                        continue
                    average = tuple(sum(pixel[channel] for pixel in tile) / len(tile)
                                    for channel in range(3))
                    candidates.append((average, (x, y, x + size, y + size)))
            if candidates:
                break
        if candidates:
            break
    if not candidates:
        return ()

    def distance(left, right):
        return sum((left[channel] - right[channel]) ** 2 for channel in range(3))

    primary = min(candidates, key=lambda candidate: distance(candidate[0], mean))
    accent = max(candidates, key=lambda candidate: distance(candidate[0], primary[0]))
    return primary[1], accent[1]


RIG_HEAD_PARTS = {
    "humanoid": {0}, "villager": {0}, "quadruped": {1}, "horse": {1},
    "camel": {1}, "creeper": {0}, "bird": {1}, "flying": {0}, "bat": {0},
    "bee": {0}, "fish": {0}, "squid": {0}, "arthropod": {0}, "cube": {0},
    "ghast": {0}, "golem": {0}, "turtle": {1}, "frog": {1}, "blaze": {0},
    "shulker": {0}, "dragon": {1}, "wither": {1, 2, 3},
}


def _safe_texture_crop(texture, *, accent=False):
    tiles = _opaque_texture_tiles(current_context().path("textures", texture, ".png"))
    if not tiles:
        return None
    return tiles[1 if accent and len(tiles) > 1 else 0]


def _x_pose(quarters):
    pose = {key: key for key in NORMAL}
    for _ in range(quarters % 4):
        pose = after(pose, QUARTER_TURN_X)
    return pose


def _rotate_x(point, degrees):
    radians = math.radians(degrees)
    x, y, z = point
    return (x, y * math.cos(radians) - z * math.sin(radians),
            y * math.sin(radians) + z * math.cos(radians))


def _model_box(texture, offset, origin, size, *, pivot=(0, 0, 0), xrot=0,
               angle=0, tint=None):
    x, y, z = origin
    w, h, d = size
    points = []
    for px in (x, x + w):
        for py in (y, y + h):
            for pz in (z, z + d):
                rx, ry, rz = _rotate_x((px, py, pz), xrot)
                points.append((rx + pivot[0], ry + pivot[1], rz + pivot[2]))
    lo_model = tuple(min(point[i] for point in points) for i in range(3))
    hi_model = tuple(max(point[i] for point in points) for i in range(3))
    lo = (lo_model[0] / 16, (24 - hi_model[1]) / 16, -hi_model[2] / 16)
    hi = (hi_model[0] / 16, (24 - lo_model[1]) / 16, -lo_model[2] / 16)
    pose = after(_x_pose(round(xrot / 90)), HALF_TURN_X)
    part = box(lo, hi, texture, angle=angle, tint=tint, **unwrap(offset, size, pose))
    part["pivot"] = (0.0, 0.0)
    return part


def _yaw(nbt):
    values = _values(nbt, "Rotation") or _values(nbt, "rotation")
    return -values[0] if values else 0.0


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


def _equipment_parts(nbt, angle, scale):
    equipment = nbt.get("equipment")
    if equipment is not None and hasattr(equipment, "get"):
        armor = [equipment.get(slot, {}) for slot in ("feet", "legs", "chest", "head")]
        hands = [equipment.get(slot, {}) for slot in ("mainhand", "offhand")]
    else:
        armor = list(nbt.get("ArmorItems", nbt.get("armor_items", ())))
        hands = list(nbt.get("HandItems", nbt.get("hand_items", ())))
    if not armor and not hands and "Equipment" in nbt:
        legacy = list(nbt["Equipment"])
        hands, armor = legacy[:1], legacy[1:5]
    slots = [
        *((stack, center) for stack, center in zip(armor, (
            (0, .22, .2), (0, .62, .2), (0, 1.08, .2), (0, 1.62, .2),
        ))),
        *((stack, center) for stack, center in zip(hands, (
            (-.48, .82, .12), (.48, .82, .12),
        ))),
    ]
    result = []
    for stack, center in slots:
        center = tuple(value * scale for value in center)
        item = _item_quad(stack, center, .34 * scale, angle=angle)
        if item:
            item["pivot"] = (0.0, 0.0)
            result.append(item)
    return result


def armor_stand_parts(nbt):
    angle = _yaw(nbt)
    scale = .5 if _flag(nbt, "Small") or _flag(nbt, "small") else 1
    texture = _asset("entity/armorstand/armorstand", "entity/armorstand/wood")
    parts = []
    if not (_flag(nbt, "Invisible") or _flag(nbt, "invisible")):
        specs = [
            ((0, 0), (-1, -7, -1), (2, 7, 2), (0, 1, 0)),
            ((0, 26), (-6, 0, -1.5), (12, 3, 3), (0, 0, 0)),
            ((8, 0), (-1, 0, -1), (2, 11, 2), (-1.9, 12, 0)),
            ((40, 16), (-1, 0, -1), (2, 11, 2), (1.9, 12, 0)),
            ((16, 0), (-3, 3, -1), (2, 7, 2), (0, 0, 0)),
            ((48, 16), (1, 3, -1), (2, 7, 2), (0, 0, 0)),
            ((0, 48), (-4, 10, -1), (8, 2, 2), (0, 0, 0)),
        ]
        if _flag(nbt, "ShowArms") or _flag(nbt, "show_arms"):
            specs += [
                ((24, 0), (-2, -2, -1), (2, 12, 2), (-5, 2, 0)),
                ((32, 16), (0, -2, -1), (2, 12, 2), (5, 2, 0)),
            ]
        if not (_flag(nbt, "NoBasePlate") or _flag(nbt, "no_base_plate")):
            specs.append(((0, 32), (-6, 11, -6), (12, 1, 12), (0, 12, 0)))
        parts = [_model_box(texture, offset, origin, size, pivot=pivot, angle=angle)
                 for offset, origin, size, pivot in specs]
        _scale_parts(parts, scale)
    return [*parts, *_equipment_parts(nbt, angle, scale)]


DUMMY_RIGS = {
    "humanoid": (
        ((-.25, 1.45, -.25), (.25, 1.95, .25)),
        ((-.3, .65, -.18), (.3, 1.45, .18)),
        ((-.52, .65, -.14), (-.3, 1.4, .14)), ((.3, .65, -.14), (.52, 1.4, .14)),
        ((-.27, 0, -.14), (-.03, .65, .14)), ((.03, 0, -.14), (.27, .65, .14)),
    ),
    "villager": (
        ((-.28, 1.35, -.25), (.28, 1.95, .25)),
        ((-.08, 1.52, -.39), (.08, 1.72, -.25)),
        ((-.36, .35, -.22), (.36, 1.35, .22)),
        ((-.25, 0, -.16), (-.02, .35, .16)), ((.02, 0, -.16), (.25, .35, .16)),
    ),
    "quadruped": (
        ((-.42, .45, -.5), (.42, 1.05, .5)),
        ((-.34, .58, -.82), (.34, 1.12, -.5)),
        ((-.36, 0, -.42), (-.16, .5, -.2)), ((.16, 0, -.42), (.36, .5, -.2)),
        ((-.36, 0, .22), (-.16, .5, .44)), ((.16, 0, .22), (.36, .5, .44)),
    ),
    "horse": (
        ((-.42, .72, -.72), (.42, 1.42, .55)),
        ((-.3, 1.1, -.98), (.3, 1.75, -.58)),
        ((-.36, 0, -.58), (-.16, .78, -.36)), ((.16, 0, -.58), (.36, .78, -.36)),
        ((-.36, 0, .3), (-.16, .78, .52)), ((.16, 0, .3), (.36, .78, .52)),
    ),
    "camel": (
        ((-.5, .8, -.72), (.5, 1.55, .7)),
        ((-.28, 1.25, -.98), (.28, 2.35, -.58)),
        ((-.43, 0, -.58), (-.2, .9, -.34)), ((.2, 0, -.58), (.43, .9, -.34)),
        ((-.43, 0, .34), (-.2, .9, .58)), ((.2, 0, .34), (.43, .9, .58)),
    ),
    "creeper": (
        ((-.28, 1.25, -.28), (.28, 1.82, .28)), ((-.24, .45, -.2), (.24, 1.25, .2)),
        ((-.36, 0, -.35), (-.05, .48, -.05)), ((.05, 0, -.35), (.36, .48, -.05)),
        ((-.36, 0, .05), (-.05, .48, .35)), ((.05, 0, .05), (.36, .48, .35)),
    ),
    "bird": (
        ((-.22, .3, -.22), (.22, .82, .25)), ((-.17, .55, -.43), (.17, .88, -.2)),
        ((-.5, .46, -.08), (-.2, .72, .2)), ((.2, .46, -.08), (.5, .72, .2)),
        ((-.16, 0, -.04), (-.04, .34, .08)), ((.04, 0, -.04), (.16, .34, .08)),
    ),
    "flying": (
        ((-.22, .7, -.2), (.22, 1.18, .2)), ((-.28, .18, -.16), (.28, .7, .16)),
        ((-.7, .28, .04), (-.26, .9, .08)), ((.26, .28, .04), (.7, .9, .08)),
    ),
    "bat": (
        ((-.22, .35, -.18), (.22, .75, .18)),
        ((-.85, .25, -.04), (-.2, .75, .04)), ((.2, .25, -.04), (.85, .75, .04)),
    ),
    "bee": (
        ((-.35, .35, -.38), (.35, .9, .38)),
        ((-.68, .48, -.18), (-.32, .72, .2)), ((.32, .48, -.18), (.68, .72, .2)),
    ),
    "fish": (
        ((-.22, .25, -.55), (.22, .7, .55)), ((-.04, .3, .52), (.04, .65, .9)),
        ((-.45, .35, -.05), (.45, .42, .35)),
    ),
    "squid": (
        ((-.42, .7, -.42), (.42, 1.5, .42)),
        *((((x - .06, 0, z - .06), (x + .06, .75, z + .06))
           for x, z in ((-.3, -.3), (0, -.36), (.3, -.3), (-.36, 0),
                        (.36, 0), (-.3, .3), (0, .36), (.3, .3)))),
    ),
    "arthropod": (
        ((-.32, .2, -.58), (.32, .58, .15)), ((-.4, .18, .12), (.4, .62, .58)),
        *((((-.78, .1 + row * .1, z), (-.3, .2 + row * .1, z + .08))
           for row, z in enumerate((-.38, -.18, .08, .3)))),
        *((((.3, .1 + row * .1, z), (.78, .2 + row * .1, z + .08))
           for row, z in enumerate((-.38, -.18, .08, .3)))),
    ),
    "cube": (((-.45, 0, -.45), (.45, .9, .45)),),
    "ghast": (
        ((-.75, .8, -.75), (.75, 2.3, .75)),
        *((((x - .05, 0, z - .05), (x + .05, .85, z + .05))
           for x in (-.5, 0, .5) for z in (-.5, 0, .5))),
    ),
    "golem": (
        ((-.35, 1.45, -.32), (.35, 2.15, .32)), ((-.5, .65, -.28), (.5, 1.5, .28)),
        ((-.75, .45, -.2), (-.5, 1.45, .2)), ((.5, .45, -.2), (.75, 1.45, .2)),
        ((-.42, 0, -.22), (-.08, .7, .22)), ((.08, 0, -.22), (.42, .7, .22)),
    ),
    "turtle": (
        ((-.55, .18, -.65), (.55, .55, .65)), ((-.25, .2, -.92), (.25, .52, -.62)),
        ((-.85, .12, -.45), (-.5, .32, -.05)), ((.5, .12, -.45), (.85, .32, -.05)),
        ((-.8, .12, .1), (-.5, .32, .48)), ((.5, .12, .1), (.8, .32, .48)),
    ),
    "frog": (
        ((-.38, .18, -.35), (.38, .6, .35)), ((-.3, .35, -.58), (.3, .7, -.32)),
        ((-.55, 0, -.15), (-.22, .25, .35)), ((.22, 0, -.15), (.55, .25, .35)),
    ),
    "blaze": (
        ((-.28, 1.05, -.28), (.28, 1.62, .28)),
        *((((x - .05, .2 + row * .35, z - .05), (x + .05, .75 + row * .35, z + .05))
           for row, radius in enumerate((.55, .42, .55))
           for x, z in ((radius, 0), (0, radius), (-radius, 0), (0, -radius)))),
    ),
    "shulker": (
        ((-.48, 0, -.48), (.48, .42, .48)), ((-.48, .45, -.48), (.48, 1, .48)),
    ),
    "dragon": (
        ((-.55, .55, -.8), (.55, 1.35, .75)), ((-.42, .75, -1.35), (.42, 1.45, -.72)),
        ((-.08, .45, .65), (.08, 1.05, 1.8)),
        ((-2.2, .72, -.35), (-.5, .82, .9)), ((.5, .72, -.35), (2.2, .82, .9)),
        ((-.48, 0, -.35), (-.18, .65, .05)), ((.18, 0, -.35), (.48, .65, .05)),
    ),
    "wither": (
        ((-.75, 1.35, -.3), (.75, 1.7, .3)),
        ((-.25, 1.6, -.28), (.25, 2.1, .28)),
        ((-.95, 1.45, -.25), (-.55, 1.9, .25)), ((.55, 1.45, -.25), (.95, 1.9, .25)),
        ((-.12, .3, -.12), (.12, 1.4, .12)),
    ),
}

COMMON_DUMMY_RIGS = {
    "pig": (
        *DUMMY_RIGS["quadruped"],
        ((-.22, .68, -.94), (.22, .93, -.8)),
    ),
    "chicken": (
        *DUMMY_RIGS["bird"],
        ((-.12, .63, -.53), (.12, .78, -.42)),
        ((-.18, .42, .22), (.18, .7, .42)),
    ),
    "cow": (
        *DUMMY_RIGS["quadruped"],
        ((-.25, .65, -.94), (.25, .9, -.8)),
        ((-.38, .98, -.72), (-.27, 1.18, -.62)),
        ((.27, .98, -.72), (.38, 1.18, -.62)),
    ),
}


def _is_baby(nbt):
    return (_flag(nbt, "IsBaby") or _flag(nbt, "is_baby")
            or _number(nbt.get("Age", nbt.get("age", 0))) < 0)


def _int_variant(nbt, key, names):
    try:
        return names[int(_number(nbt.get(key, 0))) % len(names)]
    except (TypeError, ValueError, ZeroDivisionError):
        return names[0]


def _mob_texture(kind, nbt, defaults):
    variant = _plain(nbt.get("variant", nbt.get("Variant", "")))
    if variant.lstrip("-").isdigit():
        variant = ""
    stem = None
    if kind in {"chicken", "cow", "pig"}:
        stem = f"entity/{kind}/{kind}_{variant or 'temperate'}"
    elif kind == "axolotl":
        value = _int_variant(nbt, "Variant", ("lucy", "wild", "gold", "cyan", "blue"))
        stem = f"entity/axolotl/axolotl_{value}"
    elif kind == "cat":
        value = variant or _int_variant(nbt, "CatType", (
            "tabby", "black", "red", "siamese", "british_shorthair", "calico",
            "persian", "ragdoll", "white", "jellie", "all_black",
        ))
        stem = f"entity/cat/cat_{value}"
    elif kind == "fox":
        value = variant or _int_variant(nbt, "Type", ("red", "snow"))
        stem = "entity/fox/fox_snow" if value == "snow" else "entity/fox/fox"
    elif kind == "frog":
        stem = f"entity/frog/frog_{variant or 'temperate'}"
    elif kind == "horse":
        names = (
            "white", "creamy", "chestnut", "brown", "black", "gray", "darkbrown",
        )
        value = names[min(int(_number(nbt.get("Variant", 0))) & 255, len(names) - 1)]
        stem = f"entity/horse/horse_{value}"
    elif kind in ("llama", "trader_llama"):
        value = _int_variant(nbt, "Variant", ("creamy", "white", "brown", "gray"))
        stem = f"entity/llama/llama_{value}"
    elif kind == "mooshroom":
        value = _plain(nbt.get("Type", variant or "red"))
        stem = f"entity/cow/mooshroom_{value}"
    elif kind == "parrot":
        value = _int_variant(nbt, "Variant", ("red_blue", "blue", "green", "yellow_blue", "grey"))
        stem = f"entity/parrot/parrot_{value}"
    elif kind == "rabbit":
        rabbit_type = int(_number(nbt.get("RabbitType", 0)))
        names = ("brown", "white", "black", "white_splotched", "gold", "salt")
        value = "caerbannog" if rabbit_type == 99 else names[min(max(rabbit_type, 0), 5)]
        if "toast" in str(nbt.get("CustomName", "")).lower():
            value = "toast"
        stem = f"entity/rabbit/rabbit_{value}"
    elif kind == "sniffer" and _is_baby(nbt):
        stem = "entity/sniffer/snifflet"
    elif kind == "wolf" and variant:
        stem = "entity/wolf/wolf" if variant == "pale" else f"entity/wolf/wolf_{variant}"
    elif kind == "zombie_nautilus" and "coral" in variant:
        stem = "entity/nautilus/zombie_nautilus_coral"

    candidates = []
    if stem:
        if _is_baby(nbt):
            candidates.append(stem + "_baby")
        candidates.append(stem)
    if _is_baby(nbt):
        candidates.extend(default + "_baby" for default in defaults)
    return _asset(*candidates, *defaults, "block/structure_block", "block/red_wool")


def dummy_parts(nbt, *, kind, family, textures, scale=1.0):
    texture = _mob_texture(kind, nbt, textures)
    angle = _yaw(nbt)
    parts = []
    rig = COMMON_DUMMY_RIGS.get(kind, DUMMY_RIGS[family])
    for index, (lo, hi) in enumerate(rig):
        part = box(
            lo, hi, texture,
            crop=_safe_texture_crop(texture, accent=index in RIG_HEAD_PARTS[family]),
            angle=angle,
        )
        part["pivot"] = (0.0, 0.0)
        parts.append(part)
    if family == "cube" and "Size" in nbt:
        scale *= max(.5, min(4.0, (_number(nbt["Size"]) + 1) / 2))
    if _is_baby(nbt):
        scale *= .55
    return _scale_parts(parts, scale)


def source_mob_parts(nbt, *, kind, family, textures, fallback_scale=1.0):
    texture = _mob_texture(kind, nbt, textures)
    parts = model_parts(kind, nbt, texture, angle=_yaw(nbt))
    if parts:
        return parts
    report_issue("approximate entity model", kind)
    return dummy_parts(
        nbt, kind=kind, family=family, textures=textures, scale=fallback_scale,
    )


def _mob_specs():
    specs = {}

    def add(family, entries, scale=1.0):
        for kind, stems in entries.items():
            specs[kind] = (family, (stems,) if isinstance(stems, str) else stems, scale)

    add("flying", {
        "allay": "entity/allay/allay", "vex": "entity/illager/vex",
    })
    add("quadruped", {
        "armadillo": "entity/armadillo/armadillo", "goat": "entity/goat/goat",
        "mooshroom": ("entity/cow/mooshroom_red", "entity/cow/red_mooshroom"),
    })
    add("fish", {
        "axolotl": "entity/axolotl/axolotl_lucy", "cod": "entity/fish/cod",
        "dolphin": "entity/dolphin/dolphin", "elder_guardian": "entity/guardian/guardian_elder",
        "guardian": "entity/guardian/guardian", "nautilus": "entity/nautilus/nautilus",
        "pufferfish": "entity/fish/pufferfish", "salmon": "entity/fish/salmon",
        "tadpole": "entity/tadpole/tadpole", "tropical_fish": "entity/fish/tropical_a",
        "zombie_nautilus": "entity/nautilus/zombie_nautilus",
    })
    add("bat", {"bat": "entity/bat/bat"})
    add("bee", {"bee": "entity/bee/bee"})
    add("blaze", {"blaze": "entity/blaze/blaze", "breeze": "entity/breeze/breeze"})
    add("camel", {
        "camel": "entity/camel/camel", "camel_husk": "entity/camel/camel_husk",
    })
    add("quadruped", {
        "cat": "entity/cat/cat_tabby", "fox": "entity/fox/fox",
        "ocelot": "entity/cat/ocelot", "wolf": "entity/wolf/wolf",
    }, .72)
    add("arthropod", {
        "cave_spider": "entity/spider/cave_spider", "spider": "entity/spider/spider",
    })
    add("arthropod", {
        "endermite": "entity/endermite/endermite", "silverfish": "entity/silverfish/silverfish",
    }, .5)
    add("golem", {
        "copper_golem": "entity/copper_golem/copper_golem",
        "creaking": "entity/creaking/creaking",
        "iron_golem": "entity/iron_golem/iron_golem",
        "snow_golem": "entity/snow_golem/snow_golem", "warden": "entity/warden/warden",
    })
    add("creeper", {"creeper": "entity/creeper/creeper"})
    add("dragon", {"ender_dragon": "entity/enderdragon/dragon"}, 2.4)
    add("humanoid", {"enderman": "entity/enderman/enderman"}, 1.45)
    add("villager", {
        "evoker": "entity/illager/evoker", "illusioner": "entity/illager/illusioner",
        "pillager": "entity/illager/pillager", "vindicator": "entity/illager/vindicator",
        "villager": "entity/villager/villager",
        "wandering_trader": "entity/wandering_trader/wandering_trader",
        "witch": "entity/witch/witch", "zombie_villager": "entity/zombie_villager/zombie_villager",
    })
    add("ghast", {
        "ghast": "entity/ghast/ghast", "happy_ghast": "entity/ghast/happy_ghast",
    })
    add("humanoid", {"giant": "entity/zombie/zombie"}, 6.0)
    add("squid", {"glow_squid": "entity/squid/glow_squid", "squid": "entity/squid/squid"})
    add("quadruped", {
        "hoglin": "entity/hoglin/hoglin", "panda": "entity/panda/panda",
        "polar_bear": "entity/bear/polarbear", "ravager": "entity/illager/ravager",
        "sniffer": "entity/sniffer/sniffer", "zoglin": "entity/hoglin/zoglin",
    }, 1.35)
    add("horse", {
        "donkey": "entity/horse/donkey", "horse": "entity/horse/horse_brown",
        "mule": "entity/horse/mule", "skeleton_horse": "entity/horse/horse_skeleton",
        "zombie_horse": "entity/horse/horse_zombie",
    })
    add("horse", {
        "llama": "entity/llama/llama_brown", "trader_llama": "entity/llama/llama_creamy",
    }, 1.08)
    add("cube", {
        "magma_cube": "entity/slime/magmacube", "slime": "entity/slime/slime",
        "sulfur_cube": "entity/sulfur_cube/sulfur_cube_outer",
    })
    add("bird", {"parrot": "entity/parrot/parrot_red_blue"}, .75)
    add("flying", {"phantom": "entity/phantom/phantom"}, 1.5)
    add("humanoid", {
        "bogged": "entity/skeleton/bogged", "drowned": "entity/zombie/drowned",
        "husk": "entity/zombie/husk", "parched": "entity/skeleton/parched",
        "piglin": "entity/piglin/piglin", "piglin_brute": "entity/piglin/piglin_brute",
        "skeleton": "entity/skeleton/skeleton", "stray": "entity/skeleton/stray",
        "wither_skeleton": "entity/skeleton/wither_skeleton",
        "zombified_piglin": "entity/piglin/zombified_piglin",
    })
    add("quadruped", {"rabbit": "entity/rabbit/rabbit_brown"}, .55)
    add("shulker", {"shulker": "entity/shulker/shulker"})
    add("bird", {"strider": "entity/strider/strider"}, 1.15)
    add("frog", {"frog": ("entity/frog/frog_temperate", "entity/frog/temperate_frog")})
    add("turtle", {"turtle": "entity/turtle/turtle"})
    add("wither", {"wither": "entity/wither/wither"}, 1.5)
    return specs


MOB_SPECS = _mob_specs()


def _crossed_texture_parts(texture, *, side=.5, y=.25, angle=0):
    half = side / 2
    return [
        _quad(texture, ((-half, y - half, 0), (half, y - half, 0),
                        (half, y + half, 0), (-half, y + half, 0)), angle=angle),
        _quad(texture, ((0, y - half, -half), (0, y - half, half),
                        (0, y + half, half), (0, y + half, -half)), angle=angle),
    ]


def sprite_entity_parts(nbt, *, textures=(), item=None, side=.5):
    texture = item_texture(f"minecraft:{item}") if item else None
    texture = texture or (
        _asset(*textures, "block/structure_block", "block/red_wool") if textures else None
    )
    return marker_parts(nbt) if texture is None else _crossed_texture_parts(
        texture, side=side, y=side / 2, angle=_yaw(nbt),
    )


def baked_object_parts(nbt, *, layer, textures, scale=1.0):
    texture = _asset(*textures, "block/structure_block", "block/red_wool")
    parts = model_parts(
        "", nbt, texture, layer=layer, ground=True, scale=scale, angle=_yaw(nbt),
    )
    return parts or _crossed_texture_parts(texture, angle=_yaw(nbt))


def boat_parts(nbt, *, wood=None, chest=False):
    wood = wood or _plain(nbt.get("Type", nbt.get("type", "oak")))
    folder = "chest_boat" if chest else "boat"
    texture = _asset(f"entity/{folder}/{wood}", f"entity/{folder}/oak")
    angle = _yaw(nbt)
    raft = wood == "bamboo"
    layer = (
        "BAMBOO_CHEST_RAFT" if raft and chest else
        "BAMBOO_RAFT" if raft else
        "OAK_CHEST_BOAT" if chest else "OAK_BOAT"
    )
    parts = model_parts(
        "boat", nbt, texture, layer=layer, ground=True,
        outer_y_rotation=90.0, angle=angle,
    )
    return parts or marker_parts(nbt)


def minecart_parts(nbt):
    texture = _asset("entity/minecart/minecart")
    return model_parts(
        "minecart", nbt, texture, layer="MINECART", ground=True, angle=_yaw(nbt),
    ) or marker_parts(nbt)


def block_carrier_parts(nbt):
    state = nbt.get("block_state") or nbt.get("BlockState") or nbt.get("block")
    name = str(state.get("Name", "")) if hasattr(state, "get") else ""
    base = _plain(name)
    texture = _asset(f"block/{base}", "block/structure_block") if base else _asset(
        "block/structure_block", "block/red_wool",
    )
    part = box((0, 0, 0), (1, 1, 1), texture, angle=_yaw(nbt))
    part["pivot"] = (.5, .5)
    return [part]


def primed_tnt_parts(nbt):
    part = box((-.49, 0, -.49), (.49, .98, .49), _asset("block/tnt_side"), angle=_yaw(nbt))
    part["pivot"] = (0.0, 0.0)
    return [part]


def end_crystal_parts(nbt):
    texture = _asset("entity/end_crystal/end_crystal")
    return model_parts(
        "end_crystal", nbt, texture, layer="END_CRYSTAL", ground=True,
        angle=_yaw(nbt),
    ) or marker_parts(nbt)


def marker_parts(nbt):
    report_issue("entity shown as marker", _plain(nbt.get("id", "unknown")))
    texture = _asset("block/structure_block", "block/red_wool")
    part = box((-.2, 0, -.2), (.2, .4, .2), texture, angle=_yaw(nbt))
    part["pivot"] = (0.0, 0.0)
    return [part]


def loose_item_parts(nbt):
    stack = _item_stack(nbt)
    texture = stack_texture(stack)
    if texture is None:
        return marker_parts(nbt)
    return _crossed_texture_parts(texture)


HANDLERS = {
    "painting": painting_parts,
    "item_frame": lambda nbt: item_frame_parts(nbt, glowing=False),
    "glow_item_frame": lambda nbt: item_frame_parts(nbt, glowing=True),
    "armor_stand": armor_stand_parts,
    "player": lambda nbt: model_parts(
        "player", nbt, _asset("entity/player/wide/steve"), angle=_yaw(nbt),
    ),
    "mannequin": lambda nbt: model_parts(
        "mannequin", nbt, _asset("entity/player/wide/steve"), angle=_yaw(nbt),
    ),
    "item": loose_item_parts,
    "item_display": loose_item_parts,
}

_COMMON_MOBS = {
    "chicken": ("bird", ("entity/chicken/chicken_temperate", "entity/chicken"), 1.0),
    "cow": ("quadruped", ("entity/cow/cow_temperate", "entity/cow/cow"), 1.0),
    "pig": ("quadruped", ("entity/pig/pig_temperate", "entity/pig/pig"), 1.0),
    "sheep": ("quadruped", ("entity/sheep/sheep",), 1.0),
    "zombie": ("humanoid", ("entity/zombie/zombie",), 1.0),
}

for _kind, (_family, _textures, _scale) in {**MOB_SPECS, **_COMMON_MOBS}.items():
    HANDLERS[_kind] = partial(
        source_mob_parts, kind=_kind, family=_family, textures=_textures,
        fallback_scale=_scale,
    )

HANDLERS["creaking_transient"] = partial(
    dummy_parts,
    kind="creaking_transient",
    family="golem",
    textures=("entity/creaking/creaking",),
)

for _kind, (_layer, _textures) in {
    "arrow": ("ARROW", ("entity/projectiles/arrow",)),
    "spectral_arrow": (
        "ARROW", ("entity/projectiles/arrow_spectral", "entity/projectiles/arrow"),
    ),
    "trident": ("TRIDENT", ("entity/trident/trident",)),
    "wind_charge": ("WIND_CHARGE", ("entity/projectiles/wind_charge",)),
    "breeze_wind_charge": ("WIND_CHARGE", ("entity/projectiles/wind_charge",)),
    "evoker_fangs": ("EVOKER_FANGS", ("entity/illager/evoker_fangs",)),
    "llama_spit": ("LLAMA_SPIT", ("entity/llama/llama_spit",)),
    "shulker_bullet": ("SHULKER_BULLET", ("entity/shulker/spark",)),
    "wither_skull": ("WITHER_SKULL", ("entity/skeleton/wither_skeleton",)),
    "leash_knot": ("LEASH_KNOT", ("entity/lead_knot/lead_knot",)),
}.items():
    HANDLERS[_kind] = partial(
        baked_object_parts, layer=_layer, textures=_textures,
    )

for _kind, _texture in {
    "dragon_fireball": ("entity/enderdragon/dragon_fireball",),
    "experience_orb": ("entity/experience/experience_orb",),
    "fishing_bobber": ("entity/fishing/fishing_hook",),
}.items():
    HANDLERS[_kind] = partial(sprite_entity_parts, textures=_texture)

for _kind, _item in {
    "egg": "egg", "ender_pearl": "ender_pearl", "experience_bottle": "experience_bottle",
    "eye_of_ender": "ender_eye", "fireball": "fire_charge", "firework_rocket": "firework_rocket",
    "lingering_potion": "lingering_potion", "potion": "splash_potion",
    "small_fireball": "fire_charge", "snowball": "snowball",
    "splash_potion": "splash_potion",
}.items():
    HANDLERS[_kind] = partial(sprite_entity_parts, item=_item)

for _wood in ("acacia", "birch", "cherry", "dark_oak", "jungle", "mangrove",
              "oak", "pale_oak", "spruce"):
    HANDLERS[f"{_wood}_boat"] = partial(boat_parts, wood=_wood)
    HANDLERS[f"{_wood}_chest_boat"] = partial(boat_parts, wood=_wood, chest=True)
HANDLERS.update({
    "boat": boat_parts,
    "chest_boat": partial(boat_parts, chest=True),
    "bamboo_raft": partial(boat_parts, wood="bamboo"),
    "bamboo_chest_raft": partial(boat_parts, wood="bamboo", chest=True),
})

for _kind in (
    "minecart", "chest_minecart", "command_block_minecart", "furnace_minecart",
    "hopper_minecart", "spawner_minecart", "tnt_minecart",
):
    HANDLERS[_kind] = minecart_parts

HANDLERS.update({
    "block_display": block_carrier_parts,
    "falling_block": block_carrier_parts,
    "tnt": primed_tnt_parts,
    "end_crystal": end_crystal_parts,
    "ominous_item_spawner": marker_parts,
    "area_effect_cloud": marker_parts,
    "interaction": marker_parts,
    "lightning_bolt": marker_parts,
    "marker": marker_parts,
    "text_display": marker_parts,
})

VANILLA_MOB_TYPES_26_2 = frozenset(MOB_SPECS) | frozenset(_COMMON_MOBS)
VANILLA_CREATURE_RIG_TYPES_26_2 = VANILLA_MOB_TYPES_26_2 | {
    "armor_stand", "mannequin", "player",
}
LEGACY_COMPAT_ENTITY_TYPES = frozenset({
    "boat", "chest_boat", "creaking_transient", "player",
})
SUPPORTED_ENTITY_TYPES = frozenset(HANDLERS)

HANGING = frozenset({"painting", "item_frame", "glow_item_frame"})


def anchor_of(record, nbt=None, *, exact=False):
    nbt = record if nbt is None else nbt
    keys = ("pos", "Pos") if exact else ("blockPos", "block_pos")
    for key in keys:
        values = _values(record, key)
        if values and len(values) == 3:
            return values if exact else tuple(int(value) for value in values)
    if not exact:
        for key in ("pos", "Pos"):
            values = _values(record, key)
            if values and len(values) == 3:
                return tuple(math.floor(value) for value in values)
        for key in ("blockPos", "block_pos"):
            values = _values(nbt, key)
            if values and len(values) == 3:
                return tuple(int(value) for value in values)
        if all(key in nbt for key in ("TileX", "TileY", "TileZ")):
            return tuple(int(_number(nbt[key])) for key in ("TileX", "TileY", "TileZ"))
    for key in ("Pos", "pos"):
        values = _values(nbt, key)
        if values and len(values) == 3:
            return values if exact else tuple(math.floor(value) for value in values)
    return None


def structure_parts(structure):
    result = []
    for record in structure.entities:
        nbt = record.get("nbt") if hasattr(record, "get") else None
        if nbt is None:
            continue
        kind = _plain(nbt.get("id", ""))
        if not kind:
            report_issue("entity omitted", "missing id")
            continue
        handler = HANDLERS.get(kind, marker_parts)
        origin = anchor_of(record, nbt, exact=kind not in HANGING)
        if origin is None:
            report_issue("entity omitted; missing position", kind)
            continue
        parts = handler(nbt)
        if parts:
            result.append((origin, parts))
        else:
            report_issue("entity omitted; model/resources unavailable", kind)
    return result
