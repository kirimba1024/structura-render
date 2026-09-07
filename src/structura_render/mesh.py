"""Shared Minecraft block geometry for image and model exporters."""

import hashlib
import math

import numpy as np
from PIL import Image
from structura_core import AIR_NAMES

from .assets import current_context
from .block_model import AXIS_VEC, FACE_CORNERS, block_elements, post_texture
from .entities import structure_parts
from .entity_shapes import entity_decoration, entity_shape, nbt_sensitive, nbt_signature
from .full_cube import is_occluder as shape_is_occluder
from .geometry import DEFAULT_MAX_ATLAS_SIZE, DEFAULT_MAX_VOXELS, TexturedMesh
from .projections import block_color, family
from .textures import tint_for

GLASS_ALPHA = 90

CUBE_CORNERS = np.array([
    [0, 0, 0], [1, 0, 0], [1, 0, 1], [0, 0, 1],
    [0, 1, 0], [1, 1, 0], [1, 1, 1], [0, 1, 1],
], dtype=np.float32)

CUBE_FACES = {direction: list(corners) for direction, corners in FACE_CORNERS.items()}
FACE_STEP = AXIS_VEC
UV_CORNERS = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], dtype=np.float32)

CROSS_PLANES = [
    np.array([[0, 0, 0], [1, 0, 1], [1, 1, 1], [0, 1, 0]], dtype=np.float32),
    np.array([[0, 0, 0], [0, 1, 0], [1, 1, 1], [1, 0, 1]], dtype=np.float32),
    np.array([[0, 0, 1], [1, 0, 0], [1, 1, 0], [0, 1, 1]], dtype=np.float32),
    np.array([[0, 0, 1], [0, 1, 1], [1, 1, 0], [1, 0, 0]], dtype=np.float32),
]


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


class Atlas:
    def __init__(self, max_size=DEFAULT_MAX_ATLAS_SIZE):
        if isinstance(max_size, bool) or not isinstance(max_size, int) or max_size < 1:
            raise ValueError("max_atlas_size must be a positive integer")
        self.max_size = max_size
        self.images = []
        self.index = {}
        self.area = 0

    def add(self, image):
        key = (
            image.mode,
            image.size,
            hashlib.blake2b(image.tobytes(), digest_size=16).digest(),
        )
        if key not in self.index:
            area = image.width * image.height
            if self.area + area > self.max_size ** 2 or max(image.size) > self.max_size:
                raise ValueError(f"textures exceed max_atlas_size={self.max_size}; use a smaller pack or raise the limit")
            self.area += area
            self.index[key] = len(self.images)
            self.images.append(image)
        return self.index[key]

    def build(self, padding=2, *, max_size=None):
        max_size = self.max_size if max_size is None else max_size
        if isinstance(max_size, bool) or not isinstance(max_size, int) or max_size < 1:
            raise ValueError("max_atlas_size must be a positive integer")
        if isinstance(padding, bool) or not isinstance(padding, int) or padding < 0:
            raise ValueError("atlas padding must be a nonnegative integer")
        if not self.images:
            return np.zeros((1, 1, 4), dtype=np.uint8), []
        sizes = [(image.width + 2 * padding, image.height + 2 * padding) for image in self.images]
        area = sum(w * h for w, h in sizes)
        if area > max_size * max_size or any(max(size) > max_size for size in sizes):
            raise ValueError(f"textures exceed max_atlas_size={max_size}; use a smaller pack or raise the limit")
        width = min(max_size, max(max(w for w, h in sizes), math.ceil(math.sqrt(area))))
        order = sorted(range(len(sizes)), key=lambda i: (-sizes[i][1], -sizes[i][0], i))
        while True:
            positions = [None] * len(sizes)
            x = y = row_height = used_width = 0
            for i in order:
                w, h = sizes[i]
                if x + w > width:
                    y += row_height
                    x = row_height = 0
                positions[i] = (x, y)
                x += w
                used_width = max(used_width, x)
                row_height = max(row_height, h)
            height = y + row_height
            if height <= max_size:
                break
            if width == max_size:
                raise ValueError(f"textures do not fit max_atlas_size={max_size}; use a smaller pack or raise the limit")
            width = min(max_size, width * 2)
        atlas = np.zeros((height, used_width, 4), dtype=np.uint8)
        rects = []
        for image, (x, y), (w, h) in zip(self.images, positions, sizes):
            tile = np.pad(np.asarray(image.convert("RGBA")),
                          ((padding, padding), (padding, padding), (0, 0)), mode="edge")
            atlas[y:y + h, x:x + w] = tile
            rects.append(((x + padding) / used_width, (x + w - padding) / used_width,
                          1 - (y + h - padding) / height, 1 - (y + padding) / height))
        return atlas, rects


def face_texture_key(direction, faces):
    if direction == "up" and "top" in faces:
        return "top"
    if direction == "down" and "bottom" in faces:
        return "bottom"
    if "side" in faces:
        return "side"
    if "all" in faces:
        return "all"
    return next(iter(faces))


def uv_for_rect(rect):
    u0, u1, v0, v1 = rect
    return np.array([[u0, v0], [u1, v0], [u1, v1], [u0, v1]], dtype=np.float32)


def face_uv(uv, direction):
    """Keep the texture attached to its vertices after fixing top-face winding."""
    return uv[[0, 3, 2, 1]] if direction == "up" else uv


ALPHA_MODES = ("OPAQUE", "MASK", "BLEND")


def alpha_mode(image):
    alpha = np.asarray(image)[..., 3]
    if np.any((alpha > 0) & (alpha < 255)):
        return "BLEND"
    return "MASK" if np.any(alpha == 0) else "OPAQUE"


def uv_pixel_bounds(image, uv):
    height, width = image.shape[:2]
    pixels = np.asarray(uv) * (width, -height) + (0, height)
    lo = np.clip(np.floor(pixels.min(axis=0) + 1e-4).astype(int), 0, (width - 1, height - 1))
    hi = np.clip(np.ceil(pixels.max(axis=0) - 1e-4).astype(int), lo + 1, (width, height))
    return int(lo[0]), int(lo[1]), int(hi[0]), int(hi[1])


def uv_points_for_rect(rect, points):
    u0, u1, v0, v1 = rect
    width, height = u1 - u0, v1 - v0
    return np.asarray([
        (u0 + width * u, v1 - height * v) for u, v in points
    ], dtype=np.float32)


FACE_UV_AXES = {
    "up": (0, False, 2, False), "down": (0, False, 2, False),
    "north": (0, True, 1, False), "south": (0, False, 1, False),
    "east": (2, True, 1, False), "west": (2, False, 1, False),
}


def atlas_uv(rect, uv):
    u0, v0, u1, v1 = uv
    v0, v1 = 1 - v1, 1 - v0
    ru0, ru1, rv0, rv1 = rect
    uspan, vspan = ru1 - ru0, rv1 - rv0
    return np.array([
        [ru0 + uspan * u0, rv0 + vspan * v0],
        [ru0 + uspan * u1, rv0 + vspan * v0],
        [ru0 + uspan * u1, rv0 + vspan * v1],
        [ru0 + uspan * u0, rv0 + vspan * v1],
    ], dtype=np.float32)


def cropped_uv(rect, direction, lo, hi):
    u_axis, u_flip, v_axis, v_flip = FACE_UV_AXES[direction]
    u_lo, u_hi = lo[u_axis], hi[u_axis]
    v_lo, v_hi = lo[v_axis], hi[v_axis]
    if u_flip:
        u_lo, u_hi = 1.0 - u_hi, 1.0 - u_lo
    if v_flip:
        v_lo, v_hi = 1.0 - v_hi, 1.0 - v_lo
    ru0, ru1, rv0, rv1 = rect
    uspan, vspan = ru1 - ru0, rv1 - rv0
    return np.array([
        [ru0 + uspan * u_lo, rv0 + vspan * v_lo],
        [ru0 + uspan * u_hi, rv0 + vspan * v_lo],
        [ru0 + uspan * u_hi, rv0 + vspan * v_hi],
        [ru0 + uspan * u_lo, rv0 + vspan * v_hi],
    ], dtype=np.float32)


def quads_from_positions(positions, corner_offsets, uv):
    count = len(positions)
    if count == 0:
        return None, None, None
    points = (positions[:, None, :] + corner_offsets[None, :, :]).reshape(-1, 3)
    idx = np.arange(count * 4).reshape(count, 4)
    faces = np.hstack([np.full((count, 1), 4), idx]).ravel()
    tcoords = np.tile(uv, (count, 1))
    return points, faces, tcoords


def shift_toward(mask, direction):
    dx, dy, dz = FACE_STEP[direction]
    shifted = np.zeros_like(mask)
    tx = slice(max(0, -dx), mask.shape[0] - max(0, dx))
    ty = slice(max(0, -dy), mask.shape[1] - max(0, dy))
    tz = slice(max(0, -dz), mask.shape[2] - max(0, dz))
    sx = slice(max(0, dx), mask.shape[0] + min(0, dx))
    sy = slice(max(0, dy), mask.shape[1] + min(0, dy))
    sz = slice(max(0, dz), mask.shape[2] + min(0, dz))
    shifted[tx, ty, tz] = mask[sx, sy, sz]
    return shifted


def exposed_mask(own_mask, solid, direction):
    return own_mask & ~shift_toward(solid, direction)


def connects_mask(own_mask, connectable, direction):
    return own_mask & shift_toward(connectable, direction)


def box_corners(lo, hi):
    lo = np.array(lo, dtype=np.float32)
    hi = np.array(hi, dtype=np.float32)
    return np.array([
        [lo[0], lo[1], lo[2]], [hi[0], lo[1], lo[2]], [hi[0], lo[1], hi[2]], [lo[0], lo[1], hi[2]],
        [lo[0], hi[1], lo[2]], [hi[0], hi[1], lo[2]], [hi[0], hi[1], hi[2]], [lo[0], hi[1], hi[2]],
    ], dtype=np.float32)


def rotate_y(points, degrees, pivot=(0.5, 0.5)):
    angle = np.radians(degrees)
    cosine, sine = np.cos(angle), np.sin(angle)
    result = points.copy()
    x, z = points[:, 0] - pivot[0], points[:, 2] - pivot[1]
    result[:, 0] = x * cosine - z * sine + pivot[0]
    result[:, 2] = x * sine + z * cosine + pivot[1]
    return result


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


def instance_groups(src, state, index, name):
    own = state == index
    by_signature = {}
    for pos in map(tuple, np.argwhere(own)):
        by_signature.setdefault(nbt_signature(name, src.block_nbt.get(pos)), []).append(pos)
    groups = {}
    for signature, positions in by_signature.items():
        mask = np.zeros_like(own)
        mask[tuple(np.array(positions).T)] = True
        groups[signature] = mask
    return groups


def resolve_special_parts(shape, bank, atlas):
    parts = []
    for part in shape:
        if part["faces"]:
            rect_by_face = {}
            turns = part.get("turns") or {}
            for direction, crop in part["faces"].items():
                image = bank.read_asset(part["texture"], part["tint"], crop, part["alpha"])
                if image is None:
                    continue
                if direction in turns:
                    image = image.transpose(turns[direction])
                rect_by_face[direction] = atlas.add(image)
            if rect_by_face:
                parts.append({**part, "rect_by_face": rect_by_face})
            continue
        image = bank.read_asset(part["texture"], part["tint"], part["crop"], part["alpha"])
        if image is not None:
            parts.append({**part, "rect_index": atlas.add(image)})
    return parts


def build_textured_geometry(src, solid, state, index_names, index_props, bank, *, max_atlas_size=DEFAULT_MAX_ATLAS_SIZE):
    context = getattr(bank, "context", None) or current_context()
    with context.activate():
        return _build_textured_geometry(src, solid, state, index_names, index_props, bank,
                                        max_atlas_size=max_atlas_size)


def _build_textured_geometry(src, solid, state, index_names, index_props, bank, *, max_atlas_size):
    atlas = Atlas(max_size=max_atlas_size)
    resolved = {}
    generic = {}
    specials = {}
    special_masks = {}
    element_texture_cache = {}

    def element_rect_index(texture_name, tinted, block_name, props):
        tint_color = tint_for(block_name, props) if tinted else None
        cache_key = (texture_name, tint_color)
        if cache_key not in element_texture_cache:
            image = bank.read_texture(texture_name, tint_color)
            element_texture_cache[cache_key] = atlas.add(image) if image is not None else None
        return element_texture_cache[cache_key]

    for index, name in index_names.items():
        props = index_props.get(index, {})
        if is_post_family(name) and not all(direction in props for direction in ARM_AXIS):
            texture_name = post_texture(name)
            image = bank.read_texture(texture_name) if texture_name else None
            faces = {"all": image} if image is not None else bank.resolve(name)
            if faces:
                resolved[index] = {key: atlas.add(image) for key, image in faces.items()}
            continue
        elements = block_elements(name, props)
        if nbt_sensitive(name):
            groups = instance_groups(src, state, index, name)
            if set(groups) != {None}:
                for signature, mask in groups.items():
                    group_shape = (
                        entity_decoration(name, props, signature) if elements
                        else entity_shape(name, props, signature)
                    )
                    parts = resolve_special_parts(group_shape, bank, atlas)
                    if parts:
                        specials[(index, signature)] = parts
                        special_masks[(index, signature)] = mask
                if not elements:
                    continue
        shape = entity_shape(name, props) if not elements or name == "minecraft:bell" else None
        if shape is not None:
            parts = resolve_special_parts(shape, bank, atlas)
            specials[index] = parts
            special_masks[index] = state == index
        if elements == []:
            if name in ("minecraft:water", "minecraft:lava", "minecraft:bubble_column"):
                elements = None
            else:
                if shape is None:
                    specials[index] = []
                    special_masks[index] = state == index
                continue
        if elements is None:
            if shape is not None:
                continue
            faces = bank.resolve(name)
            if faces:
                resolved[index] = {key: atlas.add(image) for key, image in faces.items()}
            continue
        built = []
        for element in elements:
            faces = {}
            for direction, face in element["faces"].items():
                rect_index = element_rect_index(face["texture"], face["tinted"], name, props)
                if rect_index is None:
                    continue
                faces[direction] = {
                    "rect_index": rect_index,
                    "uv": face["uv"],
                    "uv_rotation": face["uv_rotation"],
                    "uv_order": face.get("uv_order", (0, 1, 2, 3)),
                    "vertices": face["vertices"],
                    "cullface": face["cullface"],
                }
            if faces:
                built.append({"lo": element["lo"], "hi": element["hi"], "faces": faces})
        if built:
            generic[index] = built
    entity_geometry = []
    for anchor, parts in structure_parts(src):
        for part in resolve_special_parts(parts, bank, atlas):
            entity_geometry.append((anchor, part))

    if not resolved and not generic and not specials and not entity_geometry:
        return [], [], set(), np.zeros_like(solid)

    occluder = np.zeros_like(solid)
    fence_family = np.zeros_like(solid)
    pane_family = np.zeros_like(solid)
    wall_family = np.zeros_like(solid)
    bars_family = np.zeros_like(solid)
    fence_gate_family = np.zeros_like(solid)
    for index, name in index_names.items():
        if is_occluder(name, index_props.get(index, {})):
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

    atlas_image = None
    rects = []
    if atlas.images:
        atlas_image, rects = atlas.build(max_size=max_atlas_size)

    points_all, faces_all, uv_all = [], [], []
    material_modes, mode_cache = [], {}
    vertex_count = 0

    def append(positions, offsets, uv):
        nonlocal vertex_count
        points, faces, tcoords = quads_from_positions(positions, offsets, uv)
        if points is None:
            return
        base = vertex_count
        vertex_count += len(points)
        faces = faces.reshape(-1, 5)
        faces[:, 1:] += base
        points_all.append(points)
        faces_all.append(faces.ravel())
        uv_all.append(tcoords)
        bounds = uv_pixel_bounds(atlas_image, uv)
        if bounds not in mode_cache:
            x0, y0, x1, y1 = bounds
            mode_cache[bounds] = ALPHA_MODES.index(alpha_mode(atlas_image[y0:y1, x0:x1]))
        material_modes.append(np.full(len(points) // 4, mode_cache[bounds], dtype=np.uint8))

    for index, elements in generic.items():
        own = state == index
        if not own.any():
            continue
        for element in elements:
            for direction, face in element["faces"].items():
                mask = exposed_mask(own, occluder | own, face["cullface"]) if face["cullface"] else own
                pos = np.argwhere(mask).astype(np.float32)
                uv = atlas_uv(rects[face["rect_index"]], face["uv"])
                uv = np.roll(uv, face["uv_rotation"], axis=0)
                uv = uv[list(face["uv_order"])]
                append(pos, np.asarray(face["vertices"], dtype=np.float32), uv)

    water_mask = np.zeros_like(solid)
    lava_mask = np.zeros_like(solid)
    for index, name in index_names.items():
        if name in ("minecraft:water", "minecraft:bubble_column"):
            water_mask |= state == index
        elif name == "minecraft:lava":
            lava_mask |= state == index

    for key, parts in specials.items():
        own = special_masks[key]
        if not own.any():
            continue
        name = index_names[key[0] if isinstance(key, tuple) else key]
        for part in parts:
            lo, hi = part["lo"], part["hi"]
            raw_corners = np.asarray(part.get("corners", box_corners(lo, hi)), dtype=np.float32)
            corners = rotate_y(raw_corners, part["angle"])
            for direction, indices in CUBE_FACES.items():
                axis = next(i for i, value in enumerate(FACE_STEP[direction]) if value)
                edge = lo[axis] == 0 if FACE_STEP[direction][axis] < 0 else hi[axis] == 1
                if name in ("minecraft:water", "minecraft:bubble_column"):
                    neighbors = water_mask
                elif name == "minecraft:lava":
                    neighbors = lava_mask
                else:
                    neighbors = occluder | own
                mask = exposed_mask(own, neighbors, direction) if edge and part["angle"] % 90 == 0 else own
                if "rect_by_face" in part:
                    if direction not in part["rect_by_face"]:
                        continue
                    rect_index = part["rect_by_face"][direction]
                else:
                    rect_index = part["rect_index"]
                append(np.argwhere(mask).astype(np.float32), corners[indices], face_uv(uv_for_rect(rects[rect_index]), direction))

    for index, face_ids in resolved.items():
        name = index_names[index]
        own = state == index
        if not own.any():
            continue
        props = index_props.get(index, {})
        if is_cross(name):
            positions = np.argwhere(own).astype(np.float32)
            if "top" in face_ids and "bottom" in face_ids:
                key = "top" if props.get("half") == "upper" else "bottom"
            else:
                key = next(iter(face_ids))
            uv = uv_for_rect(rects[face_ids[key]])
            reverse_uv = uv[[0, 3, 2, 1]]
            for i, plane in enumerate(CROSS_PLANES):
                append(positions, plane, reverse_uv if i % 2 else uv)
        elif is_fence(name) or is_pane(name) or is_wall(name):
            key = next(iter(face_ids))
            rect = rects[face_ids[key]]
            if is_fence(name):
                connectable, (post_lo, post_hi) = fence_connectable, FENCE_POST
            elif is_pane(name):
                connectable, (post_lo, post_hi) = pane_connectable, PANE_POST
            else:
                connectable, (post_lo, post_hi) = wall_connectable, WALL_POST
            post_corners = box_corners(post_lo, post_hi)
            connects = {d: connects_mask(own, connectable, d) for d in ARM_AXIS}
            for direction in ("up", "down"):
                mask = exposed_mask(own, connectable, direction)
                pos = np.argwhere(mask).astype(np.float32)
                append(pos, post_corners[CUBE_FACES[direction]], face_uv(cropped_uv(rect, direction, post_lo, post_hi), direction))
            for direction in ARM_AXIS:
                pos = np.argwhere(own & ~connects[direction]).astype(np.float32)
                append(pos, post_corners[CUBE_FACES[direction]], cropped_uv(rect, direction, post_lo, post_hi))
            if is_fence(name):
                for direction, mask in connects.items():
                    pos = np.argwhere(mask).astype(np.float32)
                    for y_range in FENCE_BAR_Y:
                        lo, hi = arm_bounds(direction, y_range, FENCE_BAR_THICKNESS)
                        corners = box_corners(lo, hi)
                        for face in ("up", "down", *ARM_SIDE_FACES[direction]):
                            append(pos, corners[CUBE_FACES[face]], face_uv(cropped_uv(rect, face, lo, hi), face))
            elif is_pane(name):
                for direction, mask in connects.items():
                    pos = np.argwhere(mask).astype(np.float32)
                    lo, hi = arm_bounds(direction, (0.0, 1.0), PANE_THICKNESS)
                    corners = box_corners(lo, hi)
                    for face in ARM_SIDE_FACES[direction]:
                        append(pos, corners[CUBE_FACES[face]], cropped_uv(rect, face, lo, hi))
            else:
                tall_connects = {d: connects_mask(own, wall_family, d) for d in ARM_AXIS}
                for direction, mask in connects.items():
                    for sub_mask, y_top in (
                        (mask & tall_connects[direction], 1.0),
                        (mask & ~tall_connects[direction], WALL_LOW_TOP),
                    ):
                        pos = np.argwhere(sub_mask).astype(np.float32)
                        lo, hi = arm_bounds(direction, (0.0, y_top), WALL_THICKNESS)
                        corners = box_corners(lo, hi)
                        for face in ("up", "down", *ARM_SIDE_FACES[direction]):
                            append(pos, corners[CUBE_FACES[face]], face_uv(cropped_uv(rect, face, lo, hi), face))
        elif is_bars(name):
            key = next(iter(face_ids))
            uv = uv_for_rect(rects[face_ids[key]])
            plane_x, plane_z = torch_boxes((0.0, 0.0))
            positions = np.argwhere(own).astype(np.float32)
            for direction in ("west", "east"):
                append(positions, plane_x[CUBE_FACES[direction]], uv)
            for direction in ("north", "south"):
                append(positions, plane_z[CUBE_FACES[direction]], uv)
            connects = {d: connects_mask(own, bars_connectable, d) for d in ARM_AXIS}
            for direction, mask in connects.items():
                pos = np.argwhere(mask).astype(np.float32)
                lo, hi = arm_bounds(direction, (0.0, 1.0), PANE_THICKNESS)
                corners = box_corners(lo, hi)
                for face in ARM_SIDE_FACES[direction]:
                    append(pos, corners[CUBE_FACES[face]], cropped_uv(rects[face_ids[key]], face, lo, hi))
        elif name in TORCH_STANDING or name in TORCH_WALL:
            positions = np.argwhere(own).astype(np.float32)
            offset = WALL_TORCH_OFFSET.get(props.get("facing", ""), (0.0, 0.0)) if name in TORCH_WALL else (0.0, 0.0)
            plane_x, plane_z = torch_boxes(offset)
            key = next(iter(face_ids))
            uv = uv_for_rect(rects[face_ids[key]])
            for direction in ("west", "east"):
                append(positions, plane_x[CUBE_FACES[direction]], uv)
            for direction in ("north", "south"):
                append(positions, plane_z[CUBE_FACES[direction]], uv)
        else:
            for direction in CUBE_FACES:
                mask = exposed_mask(own, occluder | own, direction)
                pos = np.argwhere(mask).astype(np.float32)
                key = face_texture_key(direction, face_ids)
                rect = rects[face_ids.get(key, face_ids.get("all"))]
                append(pos, CUBE_CORNERS[CUBE_FACES[direction]], face_uv(uv_for_rect(rect), direction))

    for anchor, part in entity_geometry:
        origin = np.array([anchor], dtype=np.float32)
        pivot = part.get("pivot", (0.5, 0.5))
        angle = part.get("angle", 0)
        if "quads" in part:
            rect = rects[part["rect_index"]]
            mapped_uv = part.get("quad_uvs")
            for index, quad in enumerate(part["quads"]):
                uv = (
                    uv_points_for_rect(rect, mapped_uv[index])
                    if mapped_uv else uv_for_rect(rect)
                )
                vertices = rotate_y(np.asarray(quad, dtype=np.float32), angle, pivot)
                append(origin, vertices, uv)
            continue
        corners = rotate_y(box_corners(part["lo"], part["hi"]), angle, pivot)
        directions = part.get("only_faces") or CUBE_FACES
        for direction in directions:
            if "rect_by_face" in part:
                if direction not in part["rect_by_face"]:
                    continue
                rect_index = part["rect_by_face"][direction]
            else:
                rect_index = part["rect_index"]
            append(origin, corners[CUBE_FACES[direction]], face_uv(uv_for_rect(rects[rect_index]), direction))

    flat_entities = []
    special_indices = {key[0] if isinstance(key, tuple) else key for key in specials}
    textured_indices = set(resolved) | set(generic) | special_indices
    if not points_all:
        return [], flat_entities, textured_indices, occluder

    if atlas_image is None:
        raise RuntimeError("textured geometry was built without an atlas")
    mesh = TexturedMesh(
        np.vstack(points_all), vtk_quads(np.concatenate(faces_all)),
        np.vstack(uv_all), np.concatenate(material_modes), atlas_image,
    )
    return [mesh], flat_entities, textured_indices, occluder


def build_textured_meshes(src, solid, state, index_names, index_props, bank, *, max_atlas_size=DEFAULT_MAX_ATLAS_SIZE):
    """Compatibility adapter returning PyVista meshes and textures."""
    meshes, entities, indices, occluder = build_textured_geometry(
        src, solid, state, index_names, index_props, bank, max_atlas_size=max_atlas_size,
    )
    return [mesh.to_pyvista() for mesh in meshes], entities, indices, occluder


def mask_surface(mask, occluder=None, lift=0.0):
    occluder = mask if occluder is None else occluder
    points, faces = [], []
    for direction in CUBE_FACES:
        exposed = mask & ~shift_toward(occluder, direction)
        positions = np.argwhere(exposed).astype(np.float32)
        if len(positions) == 0:
            continue
        offsets = box_corners((0.0, 0.0, 0.0), (1.0, 1.0, 1.0))[CUBE_FACES[direction]]
        quad_points = (positions[:, None, :] + offsets[None, :, :]).reshape(-1, 3)
        if lift:
            quad_points = quad_points + np.asarray(AXIS_VEC[direction], dtype=np.float32) * lift
        base = len(points)
        points.extend(quad_points.tolist())
        for i in range(len(positions)):
            start = base + i * 4
            faces.append([start, start + 1, start + 2, start + 3])
    return points, faces


def flat_block_groups(state, index_names, textured_indices, occluder):
    flat_solid = np.zeros_like(occluder)
    for index in index_names:
        if index not in textured_indices:
            flat_solid |= state == index
    combined_occluder = occluder | flat_solid

    color_masks = {}
    for index, name in index_names.items():
        if index in textured_indices:
            continue
        color = flat_rgba(name)
        mask = state == index
        color_masks[color] = color_masks.get(color, np.zeros_like(mask)) | mask

    groups = []
    for color, mask in color_masks.items():
        points, faces = mask_surface(mask, combined_occluder)
        if points:
            groups.append((color, points, faces))
    return groups


def vtk_quads(faces):
    return np.asarray(faces, dtype=np.int64).reshape(-1, 5)[:, 1:5]


def triangulate_quads(quads):
    quads = np.asarray(quads, dtype=np.int64)
    if len(quads) == 0:
        return quads.reshape(0, 3)
    tris = np.empty((len(quads), 2, 3), dtype=quads.dtype)
    tris[:, 0] = quads[:, [0, 1, 2]]
    tris[:, 1] = quads[:, [0, 2, 3]]
    return tris.reshape(-1, 3)


ATLAS_UPSCALE = 8
MAX_ATLAS_SIZE = DEFAULT_MAX_ATLAS_SIZE


def upscale_atlas(image):
    factor = min(
        ATLAS_UPSCALE,
        max(1, MAX_ATLAS_SIZE // max(image.width, image.height)),
    )
    return image.resize(
        (image.width * factor, image.height * factor), Image.NEAREST,
    )


def double_sided_triangles(tris):
    tris = np.asarray(tris, dtype=np.int64)
    if len(tris) == 0:
        return tris
    return np.concatenate([tris, tris[:, [0, 2, 1]]], axis=0)


def double_sided_trimesh(points, tris, visual=None):
    import trimesh

    return trimesh.Trimesh(
        vertices=points, faces=double_sided_triangles(tris), visual=visual, process=False,
    )


def material_groups(mesh, texture=None):
    """Yield compact quad buffers for each alpha mode, retaining vertex UVs."""
    if isinstance(mesh, TexturedMesh):
        quads, modes, coordinates = mesh.quads, mesh.alpha_modes, mesh.uv
    else:
        quads, coordinates = vtk_quads(mesh.faces), np.asarray(mesh.active_texture_coordinates)
        modes = mesh.cell_data.get("alpha_mode")
        if modes is None:
            modes = np.full(len(quads), ALPHA_MODES.index(alpha_mode(texture.to_array())))
    for mode in np.unique(modes):
        selected = quads[modes == mode]
        used, indices = np.unique(selected.ravel(), return_inverse=True)
        yield (
            ALPHA_MODES[int(mode)], mesh.points[used], indices.reshape(-1, 4),
            coordinates[used],
        )


def export_parts(meshes, flat_groups, center):
    """Compatibility entry point; trimesh is loaded only for its exporters."""
    from .mesh_export import export_parts as export

    return export(meshes, flat_groups, center)


def structure_export_parts(src, bank, *, max_voxels=DEFAULT_MAX_VOXELS, max_atlas_size=DEFAULT_MAX_ATLAS_SIZE):
    state, solid, index_names, index_props = voxel_state(src, max_voxels=max_voxels)
    meshes, _, textured_indices, occluder = build_textured_geometry(
        src, solid, state, index_names, index_props, bank, max_atlas_size=max_atlas_size,
    )
    flat_groups = flat_block_groups(state, index_names, textured_indices, occluder)
    center = np.asarray(src.size, dtype=np.float32) / 2.0
    return export_parts(meshes, flat_groups, center)
