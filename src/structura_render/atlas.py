import hashlib
import math

import numpy as np
from PIL import Image

from .geometry import DEFAULT_MAX_ATLAS_SIZE


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


def map_uv(rect, points):
    u0, u1, v0, v1 = rect
    return (np.asarray(points) * (u1 - u0, v1 - v0) + (u0, v0)).astype(np.float32)


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
