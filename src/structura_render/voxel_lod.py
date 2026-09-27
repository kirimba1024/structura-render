import numpy as np

from .color_space import linear_to_srgb, srgb_to_linear
from .geometry import CUBE_CORNERS, CUBE_FACES, shift_toward, triangulate_quads
from .lod_geometry import LodMesh, empty_lod, simplify_lod


FAR_VERSION = 5
FAR_MIN_LEVEL = 3
VOXEL_SPAN = 32
SAMPLE_CHANNELS = 13


def empty_voxels(span=VOXEL_SPAN):
    result = np.zeros((span, span, span, SAMPLE_CHANNELS), np.float32)
    result[..., 11] = np.inf
    result[..., 12] = -np.inf
    return result


def reduce_voxels(samples, factor=2):
    shape = samples.shape[:3]
    if factor < 1 or any(size % factor for size in shape):
        raise ValueError('Voxel reduction must divide each axis')
    nx, ny, nz = (size // factor for size in shape)
    groups = samples.reshape(nx, factor, ny, factor, nz, factor, SAMPLE_CHANNELS)
    result = np.empty((nx, ny, nz, SAMPLE_CHANNELS), np.float32)
    result[..., :11] = groups[..., :11].sum(axis=(1, 3, 5))
    result[..., 11] = groups[..., 11].min(axis=(1, 3, 5))
    result[..., 12] = groups[..., 12].max(axis=(1, 3, 5))
    return result


def block_voxels(blocks, palette, factor=4, *, origin_y=0):
    colors = np.vstack((palette, np.zeros((1, 4), np.uint8)))
    rgba = colors
    linear = srgb_to_linear(rgba[..., :3] / 255)
    result = np.zeros((len(colors), SAMPLE_CHANNELS), np.float32)
    for channel, mask in ((0, rgba[..., 3] == 255), (5, (rgba[..., 3] > 0) & (rgba[..., 3] < 255))):
        result[..., channel] = mask
        result[..., channel + 1:channel + 4] = linear * mask[..., None]
        result[..., channel + 4] = rgba[..., 3] / 255 * mask
    result[..., 10] = 1
    samples = result[blocks]
    heights = np.arange(blocks.shape[1], dtype=np.float32)[None, :, None] + origin_y
    blended = samples[..., 5] > 0
    samples[..., 11] = np.where(blended, heights, np.inf)
    samples[..., 12] = np.where(blended, heights + 1, -np.inf)
    return reduce_voxels(samples, factor)


def voxel_colors(samples):
    opaque = samples[..., 0] > 0
    values = np.where(opaque[..., None], samples[..., :5], samples[..., 5:10])
    count = values[..., :1]
    rgba = values[..., 1:] / np.maximum(count, 1)
    rgba[..., :3] = linear_to_srgb(rgba[..., :3])
    return np.rint(rgba.clip(0, 1) * 255).astype(np.uint8)


def voxel_mesh(samples, step, *, emit_bounds=None, origin_y=0, occluders=None):
    if not np.isfinite(step) or step <= 0:
        raise ValueError('Voxel size must be finite and positive')
    colors = voxel_colors(samples)
    active = colors[..., 3] > 0
    if emit_bounds is not None:
        allowed = np.zeros(active.shape, bool)
        allowed[tuple(slice(lo, hi) for lo, hi in zip(*emit_bounds))] = True
        active &= allowed
    opaque = colors[..., 3] == 255
    blended = bool(np.any(active & ~opaque))
    bottom = np.broadcast_to(np.arange(colors.shape[1])[None, :, None] * step, active.shape)
    low = np.where(opaque, bottom, samples[..., 11] - origin_y)
    high = np.where(opaque, bottom + step, samples[..., 12] - origin_y)
    vertices, faces, shades = [], [], []
    count = 0

    def append(mask, corners, lower=low, upper=high):
        nonlocal count
        if not mask.any():
            return
        positions = np.argwhere(mask)
        points = (positions[:, None, :] + CUBE_CORNERS[corners]) * step
        coordinates = tuple(positions.T)
        if blended:
            points[..., 1] = np.where(CUBE_CORNERS[corners, 1], upper[coordinates][:, None], lower[coordinates][:, None])
        points = points.reshape(-1, 3)
        vertices.append(points)
        faces.append(np.arange(count, count + len(points)).reshape(-1, 4))
        shades.append(np.repeat(colors[coordinates], 4, axis=0))
        count += len(points)

    for direction, corners in CUBE_FACES.items():
        neighbor = shift_toward(colors, direction)
        hiding = shift_toward(opaque, direction)
        if occluders is not None:
            hiding &= ~opaque | shift_toward(occluders, direction)
        if not blended:
            append(active & ~hiding, corners)
            continue
        same_blend = ~opaque & (neighbor == colors).all(axis=-1)
        neighbor_low, neighbor_high = shift_toward(low, direction), shift_toward(high, direction)
        if direction == 'up':
            hiding &= high == bottom + step
            same_blend &= high == neighbor_low
        elif direction == 'down':
            hiding &= low == bottom
            same_blend &= low == neighbor_high
        else:
            append(active & same_blend & (low < neighbor_low), corners, low, np.minimum(high, neighbor_low))
            append(active & same_blend & (high > neighbor_high), corners, np.maximum(low, neighbor_high), high)
        append(active & ~hiding & ~same_blend, corners)
    if not vertices:
        return empty_lod()
    mesh = LodMesh(np.concatenate(vertices).astype(np.float32),
                   triangulate_quads(np.concatenate(faces)).astype(np.uint32), np.concatenate(shades))
    return simplify_lod(mesh, samples.shape[0] * step, target_ratio=0)[0]
