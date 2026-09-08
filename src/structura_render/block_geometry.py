import math
from dataclasses import dataclass

import numpy as np
from structura_core import AIR_NAMES

from .atlas import cropped_uv, face_texture_key, face_uv, uv_for_rect
from .block_colours import block_color, family
from .full_cube import is_full_cube_shape, is_occluder as shape_is_occluder
from .geometry import (
    CUBE_CORNERS,
    CUBE_FACES,
    DEFAULT_MAX_VOXELS,
    FlatMesh,
    box_corners,
    connects_mask,
    exposed_mask,
    mask_surface,
)

FLOWER_NAMES = {
    "dandelion", "poppy", "blue_orchid", "allium", "azure_bluet",
    "red_tulip", "orange_tulip", "white_tulip", "pink_tulip",
    "oxeye_daisy", "cornflower", "lily_of_the_valley", "wither_rose",
    "lilac", "rose_bush", "peony", "dead_bush", "sunflower",
}


def is_cross(name):
    base = name.split(":", 1)[-1]
    if base.startswith("potted_"):
        return False
    if base in FLOWER_NAMES:
        return True
    if base.endswith("_leaves") or "vine" in base or "lichen" in base:
        return False
    return family(name) == "plant"


def is_fence(name):
    base = name.split(":", 1)[-1]
    return base.endswith("_fence")


def is_pane(name):
    return name.split(":", 1)[-1].endswith("_pane")


def is_wall(name):
    return name.split(":", 1)[-1].endswith("_wall")


def is_bars(name):
    return name.split(":", 1)[-1] == "iron_bars"


def is_fence_gate(name):
    return name.split(":", 1)[-1].endswith("_fence_gate")


def normalize_legacy(name, props):
    if name == "minecraft:double_stone_slab2":
        return "minecraft:red_sandstone", {}
    if name == "minecraft:stone_slab2":
        return "minecraft:red_sandstone_slab", {("type" if k == "half" else k): v for k, v in props.items()}
    return {
        "minecraft:grass": "minecraft:short_grass",
        "minecraft:portal": "minecraft:nether_portal",
        "minecraft:wooden_door": "minecraft:oak_door",
    }.get(name, name), props


def voxel_state(src, *, max_voxels=DEFAULT_MAX_VOXELS):
    if isinstance(max_voxels, bool) or not isinstance(max_voxels, int) or max_voxels <= 0:
        raise ValueError("max_voxels must be a positive integer")
    if math.prod(src.size) > max_voxels:
        raise ValueError(f"structure volume exceeds max_voxels={max_voxels:,}; choose a region or raise the limit")
    sx, sy, sz = src.size
    state = np.full((sx, sy, sz), -1, dtype=np.int32)
    for pos, index in src.present.items():
        if src.palette[index] not in AIR_NAMES:
            state[pos] = index
    solid = state >= 0

    index_names, index_props = {}, {}
    for index in np.unique(state[solid]):
        index = int(index)
        raw = src.palette_raw[index]
        props = (
            {str(k): str(v) for k, v in raw["Properties"].items()}
            if "Properties" in raw else {}
        )
        index_names[index], index_props[index] = normalize_legacy(src.palette[index], props)
    return state, solid, index_names, index_props


GLASS_ALPHA = 90


def flat_rgba(name, mode="family"):
    alpha = GLASS_ALPHA if family(name) == "glass" else 255
    return (*block_color(name, mode), alpha)


def is_occluder(name, props):
    if is_cross(name):
        return False
    base = name.split(":", 1)[-1]
    if base.endswith("_slab"):
        return props.get("type") == "double"
    return shape_is_occluder(name)


CROSS_PLANES = [
    np.array([[0, 0, 0], [1, 0, 1], [1, 1, 1], [0, 1, 0]], dtype=np.float32),
    np.array([[0, 0, 0], [0, 1, 0], [1, 1, 1], [1, 0, 1]], dtype=np.float32),
    np.array([[0, 0, 1], [1, 0, 0], [1, 1, 0], [0, 1, 1]], dtype=np.float32),
    np.array([[0, 0, 1], [0, 1, 1], [1, 1, 0], [1, 0, 0]], dtype=np.float32),
]

TORCH_STANDING = ("minecraft:torch", "minecraft:soul_torch", "minecraft:redstone_torch")

TORCH_WALL = ("minecraft:wall_torch", "minecraft:soul_wall_torch", "minecraft:redstone_wall_torch")

WALL_TORCH_OFFSET = {
    "east": (-0.5, 0.0), "west": (0.5, 0.0), "south": (0.0, -0.5), "north": (0.0, 0.5),
}


def torch_boxes(offset=(0.0, 0.0)):
    ox, oz = offset
    plane_x = box_corners((0.4375 + ox, 0.0, 0.0 + oz), (0.5625 + ox, 1.0, 1.0 + oz))
    plane_z = box_corners((0.0 + ox, 0.0, 0.4375 + oz), (1.0 + ox, 1.0, 0.5625 + oz))
    return plane_x, plane_z


ARM_AXIS = {"north": 2, "south": 2, "east": 0, "west": 0}

ARM_SPAN = {"north": (0.0, 0.5625), "south": (0.4375, 1.0), "east": (0.4375, 1.0), "west": (0.0, 0.5625)}

ARM_SIDE_FACES = {"north": ("east", "west"), "south": ("east", "west"), "east": ("north", "south"), "west": ("north", "south")}

FENCE_POST = ((0.375, 0.0, 0.375), (0.625, 1.0, 0.625))

FENCE_BAR_Y = ((0.75, 0.9375), (0.375, 0.5625))

FENCE_BAR_THICKNESS = (0.4375, 0.5625)

PANE_POST = ((0.4375, 0.0, 0.4375), (0.5625, 1.0, 0.5625))

PANE_THICKNESS = (0.4375, 0.5625)

WALL_POST = ((0.25, 0.0, 0.25), (0.75, 1.0, 0.75))

WALL_THICKNESS = (0.3125, 0.6875)

WALL_LOW_TOP = 0.875


def arm_bounds(direction, y_range, thickness):
    axis = ARM_AXIS[direction]
    lo, hi = [thickness[0], y_range[0], thickness[0]], [thickness[1], y_range[1], thickness[1]]
    lo[axis], hi[axis] = ARM_SPAN[direction]
    return lo, hi


def is_post_family(name):
    return is_fence(name) or is_pane(name) or is_wall(name) or is_bars(name)


def flat_block_groups(state, index_names, textured_indices, occluder, *, color_mode="family", emit_bounds=None, emit_mask=None):
    combined_occluder = occluder.copy()
    color_masks = {}
    for index, name in index_names.items():
        if index in textured_indices:
            continue
        color = flat_rgba(name, color_mode)
        mask = state == index
        if color[3] == 255:
            combined_occluder |= mask
        else:
            combined_occluder &= ~mask
        if color in color_masks:
            color_masks[color] |= mask
        else:
            color_masks[color] = mask

    groups = []
    emitted = True
    if emit_bounds is not None:
        emitted = np.zeros(state.shape, dtype=bool)
        emitted[tuple(slice(lo, hi) for lo, hi in zip(*emit_bounds))] = True
    if emit_mask is not None:
        emitted = emitted & emit_mask
    for color, mask in color_masks.items():
        points, faces = mask_surface(mask & emitted, combined_occluder | mask)
        if points:
            groups.append(FlatMesh(color, np.asarray(points, dtype=np.float32), np.asarray(faces, dtype=np.int64)))
    return groups


@dataclass
class BlockMasks:
    occluder: np.ndarray
    fences: np.ndarray
    panes: np.ndarray
    walls: np.ndarray
    bars: np.ndarray
    wall_family: np.ndarray
    water: np.ndarray
    lava: np.ndarray


def block_masks(state, names, properties):
    occluder = np.zeros_like(state, dtype=bool)
    fence_family = np.zeros_like(state, dtype=bool)
    pane_family = np.zeros_like(state, dtype=bool)
    wall_family = np.zeros_like(state, dtype=bool)
    bars_family = np.zeros_like(state, dtype=bool)
    fence_gate_family = np.zeros_like(state, dtype=bool)
    for index, name in names.items():
        if is_occluder(name, properties.get(index, {})):
            occluder |= state == index
        if is_fence(name):
            fence_family |= state == index
        if is_pane(name):
            pane_family |= state == index
        if is_wall(name):
            wall_family |= state == index
        if is_bars(name):
            bars_family |= state == index
        if is_fence_gate(name):
            fence_gate_family |= state == index
    fence_connectable = occluder | fence_family | fence_gate_family
    pane_connectable = occluder | pane_family
    wall_connectable = occluder | wall_family | fence_gate_family
    bars_connectable = occluder | bars_family

    water = np.zeros_like(occluder)
    lava = np.zeros_like(occluder)
    for index, name in names.items():
        if name in ("minecraft:water", "minecraft:bubble_column"):
            water |= state == index
        elif name == "minecraft:lava":
            lava |= state == index
    return BlockMasks(occluder, fence_connectable, pane_connectable,
                      wall_connectable, bars_connectable, wall_family, water, lava)


def _emit_cross(props, own, face_ids, buffer):
    positions = np.argwhere(own).astype(np.float32)
    if "top" in face_ids and "bottom" in face_ids:
        key = "top" if props.get("half") == "upper" else "bottom"
    else:
        key = next(iter(face_ids))
    uv = uv_for_rect(buffer.rects[face_ids[key]])
    reverse_uv = uv[[0, 3, 2, 1]]
    for i, plane in enumerate(CROSS_PLANES):
        buffer.append(positions, plane, reverse_uv if i % 2 else uv)


def _emit_post(name, own, face_ids, masks, buffer):
    key = next(iter(face_ids))
    rect = buffer.rects[face_ids[key]]
    if is_fence(name):
        connectable, (post_lo, post_hi) = masks.fences, FENCE_POST
    elif is_pane(name):
        connectable, (post_lo, post_hi) = masks.panes, PANE_POST
    else:
        connectable, (post_lo, post_hi) = masks.walls, WALL_POST
    post_corners = box_corners(post_lo, post_hi)
    connects = {d: connects_mask(own, connectable, d) for d in ARM_AXIS}
    for direction in ("up", "down"):
        mask = exposed_mask(own, connectable, direction)
        pos = np.argwhere(mask).astype(np.float32)
        buffer.append(pos, post_corners[CUBE_FACES[direction]], face_uv(cropped_uv(rect, direction, post_lo, post_hi), direction))
    for direction in ARM_AXIS:
        pos = np.argwhere(own & ~connects[direction]).astype(np.float32)
        buffer.append(pos, post_corners[CUBE_FACES[direction]], cropped_uv(rect, direction, post_lo, post_hi))
    if is_fence(name):
        for direction, mask in connects.items():
            pos = np.argwhere(mask).astype(np.float32)
            for y_range in FENCE_BAR_Y:
                lo, hi = arm_bounds(direction, y_range, FENCE_BAR_THICKNESS)
                corners = box_corners(lo, hi)
                for face in ("up", "down", *ARM_SIDE_FACES[direction]):
                    buffer.append(pos, corners[CUBE_FACES[face]], face_uv(cropped_uv(rect, face, lo, hi), face))
    elif is_pane(name):
        for direction, mask in connects.items():
            pos = np.argwhere(mask).astype(np.float32)
            lo, hi = arm_bounds(direction, (0.0, 1.0), PANE_THICKNESS)
            corners = box_corners(lo, hi)
            for face in ARM_SIDE_FACES[direction]:
                buffer.append(pos, corners[CUBE_FACES[face]], cropped_uv(rect, face, lo, hi))
    else:
        tall_connects = {d: connects_mask(own, masks.wall_family, d) for d in ARM_AXIS}
        for direction, mask in connects.items():
            for sub_mask, y_top in (
                (mask & tall_connects[direction], 1.0),
                (mask & ~tall_connects[direction], WALL_LOW_TOP),
            ):
                pos = np.argwhere(sub_mask).astype(np.float32)
                lo, hi = arm_bounds(direction, (0.0, y_top), WALL_THICKNESS)
                corners = box_corners(lo, hi)
                for face in ("up", "down", *ARM_SIDE_FACES[direction]):
                    buffer.append(pos, corners[CUBE_FACES[face]], face_uv(cropped_uv(rect, face, lo, hi), face))


def _emit_bars(own, face_ids, connectable, buffer):
    key = next(iter(face_ids))
    uv = uv_for_rect(buffer.rects[face_ids[key]])
    plane_x, plane_z = torch_boxes((0.0, 0.0))
    positions = np.argwhere(own).astype(np.float32)
    for direction in ("west", "east"):
        buffer.append(positions, plane_x[CUBE_FACES[direction]], uv)
    for direction in ("north", "south"):
        buffer.append(positions, plane_z[CUBE_FACES[direction]], uv)
    connects = {d: connects_mask(own, connectable, d) for d in ARM_AXIS}
    for direction, mask in connects.items():
        pos = np.argwhere(mask).astype(np.float32)
        lo, hi = arm_bounds(direction, (0.0, 1.0), PANE_THICKNESS)
        corners = box_corners(lo, hi)
        for face in ARM_SIDE_FACES[direction]:
            buffer.append(pos, corners[CUBE_FACES[face]], cropped_uv(buffer.rects[face_ids[key]], face, lo, hi))


def _emit_torch(name, props, own, face_ids, buffer):
    positions = np.argwhere(own).astype(np.float32)
    offset = WALL_TORCH_OFFSET.get(props.get("facing", ""), (0.0, 0.0)) if name in TORCH_WALL else (0.0, 0.0)
    plane_x, plane_z = torch_boxes(offset)
    key = next(iter(face_ids))
    uv = uv_for_rect(buffer.rects[face_ids[key]])
    for direction in ("west", "east"):
        buffer.append(positions, plane_x[CUBE_FACES[direction]], uv)
    for direction in ("north", "south"):
        buffer.append(positions, plane_z[CUBE_FACES[direction]], uv)


def surface_neighbors(state, index, names, occluder, own):
    name = names[index]
    if shape_is_occluder(name):
        return occluder
    if name.endswith("_leaves"):
        indices = [other for other, value in names.items() if value.endswith("_leaves")]
    elif is_full_cube_shape(name):
        indices = [other for other, value in names.items() if value == name]
    else:
        indices = [index]
    return occluder | (own if len(indices) == 1 else np.isin(state, indices))


def _emit_cube(own, face_ids, occluder, buffer):
    for direction in CUBE_FACES:
        mask = exposed_mask(own, occluder | own, direction)
        pos = np.argwhere(mask).astype(np.float32)
        key = face_texture_key(direction, face_ids)
        rect = buffer.rects[face_ids.get(key, face_ids.get("all"))]
        buffer.append(pos, CUBE_CORNERS[CUBE_FACES[direction]], face_uv(uv_for_rect(rect), direction))


def emit_fallback_blocks(resolved, state, names, properties, masks, buffer):
    for index, face_ids in resolved.items():
        name = names[index]
        own = state == index
        if not own.any():
            continue
        props = properties.get(index, {})
        if is_cross(name):
            _emit_cross(props, own, face_ids, buffer)
        elif is_fence(name) or is_pane(name) or is_wall(name):
            _emit_post(name, own, face_ids, masks, buffer)
        elif is_bars(name):
            _emit_bars(own, face_ids, masks.bars, buffer)
        elif name in TORCH_STANDING or name in TORCH_WALL:
            _emit_torch(name, props, own, face_ids, buffer)
        else:
            _emit_cube(own, face_ids, surface_neighbors(state, index, names, masks.occluder, own), buffer)
