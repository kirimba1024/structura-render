import json
import math

from .assets import context_cached, current_context, texture_asset as _asset
from .diagnostics import report_issue
from .entity_models import model_parts
from .entity_state import _flag, _number, _plain, _yaw
from .item_models import item_id, item_texture, stack_texture
from .shape_geometry import HALF_TURN_X, QUARTER_TURN_X, _scale_parts, after, box, unwrap

HORIZONTAL = ("south", "west", "north", "east")

DIRECTION = ("down", "up", "north", "south", "west", "east")

AXIS = {"south": (2, 1), "north": (2, -1), "east": (0, 1), "west": (0, -1)}

NORMAL = {
    "down": (0, -1, 0), "up": (0, 1, 0), "north": (0, 0, -1),
    "south": (0, 0, 1), "west": (-1, 0, 0), "east": (1, 0, 0),
}

DEPTH = 1 / 16

FRAME_SIDE = 12 / 16


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
