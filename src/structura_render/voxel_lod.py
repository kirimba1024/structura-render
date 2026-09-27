import numpy as np

from .color_space import linear_to_srgb, srgb_to_linear
from .geometry import CUBE_CORNERS, CUBE_FACES, shift_toward, triangulate_quads
from .lod_geometry import LodMesh, simplify_lod


FAR_VERSION = 4
FAR_MIN_LEVEL = 3
VOXEL_SPAN = 32
SAMPLE_CHANNELS = 11


def empty_voxels(span=VOXEL_SPAN):
    return np.zeros((span, span, span, SAMPLE_CHANNELS), np.float32)


def reduce_voxels(samples, factor=2):
    shape = samples.shape[:3]
    if factor < 1 or any(size % factor for size in shape):
        raise ValueError('Voxel reduction must divide each axis')
    nx, ny, nz = (size // factor for size in shape)
    return samples.reshape(nx, factor, ny, factor, nz, factor, SAMPLE_CHANNELS).sum(axis=(1, 3, 5))


def block_voxels(blocks, palette, factor=4):
    colors = np.vstack((palette, np.zeros((1, 4), np.uint8)))
    rgba = colors
    linear = srgb_to_linear(rgba[..., :3] / 255)
    result = np.zeros((len(colors), SAMPLE_CHANNELS), np.float32)
    for channel, mask in ((0, rgba[..., 3] == 255), (5, (rgba[..., 3] > 0) & (rgba[..., 3] < 255))):
        result[..., channel] = mask
        result[..., channel + 1:channel + 4] = linear * mask[..., None]
        result[..., channel + 4] = rgba[..., 3] / 255 * mask
    result[..., 10] = 1
    return reduce_voxels(result[blocks], factor)


def voxel_colors(samples):
    opaque = samples[..., 0] > 0
    values = np.where(opaque[..., None], samples[..., :5], samples[..., 5:10])
    count = values[..., :1]
    rgba = values[..., 1:] / np.maximum(count, 1)
    rgba[..., :3] = linear_to_srgb(rgba[..., :3])
    return np.rint(rgba.clip(0, 1) * 255).astype(np.uint8)


def voxel_mesh(samples, step, *, emit_bounds=None):
    if not np.isfinite(step) or step <= 0:
        raise ValueError('Voxel size must be finite and positive')
    colors = voxel_colors(samples)
    active = colors[..., 3] > 0
    if emit_bounds is not None:
        allowed = np.zeros(active.shape, bool)
        allowed[tuple(slice(lo, hi) for lo, hi in zip(*emit_bounds))] = True
        active &= allowed
    opaque = colors[..., 3] == 255
    vertices, faces, shades = [], [], []
    count = 0
    for direction, corners in CUBE_FACES.items():
        neighbor = shift_toward(colors, direction)
        same_blend = ~opaque & (neighbor == colors).all(axis=-1)
        visible = active & ~shift_toward(opaque, direction) & ~same_blend
        positions = np.argwhere(visible)
        points = ((positions[:, None, :] + CUBE_CORNERS[corners]) * step).reshape(-1, 3)
        vertices.append(points)
        faces.append(np.arange(count, count + len(points)).reshape(-1, 4))
        shades.append(np.repeat(colors[tuple(positions.T)], 4, axis=0))
        count += len(points)
    mesh = LodMesh(np.concatenate(vertices).astype(np.float32),
                   triangulate_quads(np.concatenate(faces)).astype(np.uint32), np.concatenate(shades))
    return simplify_lod(mesh, samples.shape[0] * step, target_ratio=0)[0]
