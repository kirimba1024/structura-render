import math

import numpy as np
from structura_core import AIR_NAMES

VIEWS = {
    "top": (1, True), "bottom": (1, False),
    "north": (2, False), "south": (2, True),
    "west": (0, False), "east": (0, True),
}

DEFAULT_MAX_PIXELS = 16_000_000


def frontmost(states, axis, reverse):
    data = np.moveaxis(states, axis, -1)
    if reverse:
        data = data[..., ::-1]
    present = data >= 0
    index = present.argmax(axis=-1)
    result = np.take_along_axis(data, index[..., None], axis=-1)[..., 0]
    result[~present.any(axis=-1)] = -1
    return result


def orient(image, view):
    if view in ("top", "bottom"):
        return image.T
    if view == "north":
        return image.T[::-1]
    if view == "south":
        return image.T[::-1, ::-1]
    if view == "west":
        return image[::-1]
    return image[::-1, ::-1]


def check_pixels(size, max_pixels):
    if isinstance(max_pixels, bool) or not isinstance(max_pixels, int) or max_pixels <= 0:
        raise ValueError("max_pixels must be a positive integer")
    if math.prod(size) > max_pixels:
        raise ValueError(f"image size {size} exceeds max_pixels={max_pixels:,}; reduce scale")


def projection_size(size, view, scale):
    if view not in VIEWS:
        raise ValueError(f"unknown view {view!r}; expected one of {tuple(VIEWS)}")
    if isinstance(scale, bool) or not isinstance(scale, int) or scale < 1:
        raise ValueError("scale must be a positive integer")
    axis = VIEWS[view][0]
    plane = tuple(size[i] for i in range(3) if i != axis)
    width, height = plane[::-1] if axis == 0 else plane
    return width * scale, height * scale


def depth_range(depth, size, axis):
    if depth is None:
        return 0, size[axis]
    if (not isinstance(depth, (tuple, list)) or len(depth) != 2
            or any(isinstance(v, (bool, np.bool_)) or not isinstance(v, (int, np.integer)) for v in depth)
            or not 0 <= depth[0] < depth[1] <= size[axis]):
        raise ValueError(f"depth must be (start, stop) with 0 <= start < stop <= {size[axis]} along {'XYZ'[axis]}")
    return tuple(int(v) for v in depth)


def projection_cells(src, view, depth=None):
    axis, reverse = VIEWS[view]
    start, stop = depth_range(depth, src.size, axis)
    plane_axes = tuple(i for i in range(3) if i != axis)
    plane_size = tuple(src.size[i] for i in plane_axes)
    visible = np.full(plane_size, -1, dtype=np.int32)
    visible_depth = np.full(plane_size, -1 if reverse else src.size[axis], dtype=np.int64)
    for pos, index in src.present.items():
        if not start <= pos[axis] < stop:
            continue
        if src.palette[index] in AIR_NAMES or src.palette[index] == "minecraft:structure_void":
            continue
        cell = tuple(pos[i] for i in plane_axes)
        closer = pos[axis] > visible_depth[cell] if reverse else pos[axis] < visible_depth[cell]
        if closer:
            visible[cell], visible_depth[cell] = index, pos[axis]
    return orient(visible, view)


def rectangles(cells):
    active = {}
    for y, row in enumerate(cells):
        edges = np.flatnonzero(np.r_[True, row[1:] != row[:-1], True])
        current = {}
        for x, stop in zip(edges[:-1], edges[1:]):
            value = int(row[x])
            if value < 0:
                continue
            key = int(x), int(stop), value
            current[key] = active.pop(key, y)
        for (x, stop, value), start in active.items():
            yield x, start, stop - x, y - start, value
        active = current
    for (x, stop, value), start in active.items():
        yield x, start, stop - x, len(cells) - start, value


def boundary_segments(plane):
    for swapped in (False, True):
        data = plane.T if swapped else plane
        padded = np.pad(data, ((1, 1), (0, 0)))
        edges = padded[1:] != padded[:-1]
        for y, row in enumerate(edges):
            changes = np.flatnonzero(np.diff(np.r_[False, row, False]))
            for start, stop in zip(changes[::2], changes[1::2]):
                yield (y, start, y, stop) if swapped else (start, y, stop, y)
