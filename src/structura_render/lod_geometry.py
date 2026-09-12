from dataclasses import dataclass

import numpy as np

from .geometry import ALPHA_MODES, triangulate_quads
from .atlas import uv_pixel_bounds
from .color_space import linear_to_srgb, srgb_to_linear


@dataclass
class LodMesh:
    points: np.ndarray
    triangles: np.ndarray
    colors: np.ndarray

    @property
    def nbytes(self):
        return self.points.nbytes + self.triangles.nbytes + self.colors.nbytes


def empty_lod():
    return LodMesh(np.empty((0, 3), np.float32), np.empty((0, 3), np.uint32), np.empty((0, 4), np.uint8))


def average_rgba(image):
    pixels = np.asarray(image, dtype=np.float64).reshape(-1, 4)
    alpha = pixels[:, 3]
    linear = srgb_to_linear(pixels[:, :3] / 255)
    color = linear_to_srgb(np.average(linear, axis=0, weights=alpha)) * 255 if alpha.sum() else np.zeros(3)
    return np.rint(np.append(color, alpha.mean())).astype(np.uint8)


def colored_geometry(meshes, flat):
    parts = []
    for mesh in meshes:
        colors = np.zeros((len(mesh.points), 4), np.uint8)
        cache = {}
        for quad, mode in zip(mesh.quads, mesh.alpha_modes):
            bounds = uv_pixel_bounds(mesh.image, mesh.uv[quad])
            if bounds not in cache:
                x0, y0, x1, y1 = bounds
                cache[bounds] = average_rgba(mesh.image[y0:y1, x0:x1])
            colors[quad] = cache[bounds]
            if ALPHA_MODES[mode] != 'BLEND':
                colors[quad, 3] = 255
        parts.append(LodMesh(mesh.points, triangulate_quads(mesh.quads), colors))
    for points, faces, color in flat:
        quads = np.asarray(faces).reshape(-1, 5)[:, 1:]
        parts.append(LodMesh(points, triangulate_quads(quads), np.tile(np.asarray(color, np.uint8), (len(points), 1))))
    return merge_lods((part, (0, 0, 0)) for part in parts)


def merge_lods(parts):
    vertices, triangles, colors = [], [], []
    offset = 0
    for mesh, translation in parts:
        if not len(mesh.triangles):
            continue
        vertices.append(mesh.points + np.asarray(translation, np.float32))
        triangles.append(mesh.triangles + offset)
        colors.append(mesh.colors)
        offset += len(mesh.points)
    if not vertices:
        return empty_lod()
    return LodMesh(np.concatenate(vertices).astype(np.float32), np.concatenate(triangles).astype(np.uint32),
                   np.concatenate(colors).astype(np.uint8))


def split_lod(mesh):
    opaque = (mesh.colors[mesh.triangles, 3] == 255).all(axis=1)
    result = []
    for mask, solid in ((opaque, True), (~opaque, False)):
        triangles = mesh.triangles[mask]
        if len(triangles):
            used, remap = np.unique(triangles, return_inverse=True)
            faces = np.column_stack((np.full(len(triangles), 3), remap.reshape(-1, 3))).ravel()
            result.append((solid, mesh.points[used], faces, mesh.colors[used]))
    return result


def spatially_order_lod(mesh, span=16):
    if not len(mesh.triangles):
        return mesh
    centers = mesh.points[mesh.triangles].mean(axis=1)
    cells = np.floor(centers / span).astype(np.int64)
    order = np.lexsort((cells[:, 2], cells[:, 1], cells[:, 0]))
    return LodMesh(mesh.points, mesh.triangles[order], mesh.colors)


def simplify_lod(mesh, span, *, target_ratio=0.35, error=0.5):
    from .lod_rectangles import merge_rectangles

    if not 0 <= target_ratio <= 1 or error < 0:
        raise ValueError("LOD ratio must be between zero and one, and error must be nonnegative")
    if not len(mesh.triangles):
        return mesh, 0.0
    points, triangles, colors = merge_rectangles(mesh.points, mesh.triangles, mesh.colors, span, target_ratio)
    return LodMesh(points, triangles, colors), 0.0
