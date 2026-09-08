"""NumPy geometry shared by file exporters and the optional image backend."""

from dataclasses import dataclass
from typing import NamedTuple

import numpy as np

DEFAULT_MAX_VOXELS = 16_000_000

DEFAULT_MAX_ATLAS_SIZE = 2048


@dataclass
class TexturedMesh:
    points: np.ndarray
    quads: np.ndarray
    uv: np.ndarray
    alpha_modes: np.ndarray
    image: np.ndarray

    def to_pyvista(self):
        import pyvista as pv

        faces = np.column_stack((np.full(len(self.quads), 4), self.quads)).ravel()
        mesh = pv.PolyData(self.points, faces)
        mesh.active_texture_coordinates = self.uv
        mesh.cell_data["alpha_mode"] = self.alpha_modes
        texture = pv.Texture(self.image)
        texture.SetInterpolate(False)
        texture.mipmap = False
        return mesh, texture


@dataclass
class SceneGeometry:
    meshes: list[TexturedMesh]
    flat_groups: list["FlatMesh"]

    def __bool__(self):
        return bool(self.meshes or self.flat_groups)


class FlatMesh(NamedTuple):
    color: tuple[int, int, int, int]
    points: np.ndarray
    quads: np.ndarray


AXIS_VEC = {
    "up": (0, 1, 0), "down": (0, -1, 0),
    "north": (0, 0, -1), "south": (0, 0, 1),
    "east": (1, 0, 0), "west": (-1, 0, 0),
}

FACE_CORNERS = {
    "up": (4, 7, 6, 5), "down": (0, 1, 2, 3),
    "north": (1, 0, 4, 5), "south": (3, 2, 6, 7),
    "east": (2, 1, 5, 6), "west": (0, 3, 7, 4),
}

CUBE_CORNERS = np.array([
    [0, 0, 0], [1, 0, 0], [1, 0, 1], [0, 0, 1],
    [0, 1, 0], [1, 1, 0], [1, 1, 1], [0, 1, 1],
], dtype=np.float32)

CUBE_FACES = {direction: list(corners) for direction, corners in FACE_CORNERS.items()}

FACE_STEP = AXIS_VEC

UV_CORNERS = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], dtype=np.float32)

ALPHA_MODES = ("OPAQUE", "MASK", "BLEND")


def alpha_mode(image):
    alpha = np.asarray(image)[..., 3]
    if np.any((alpha > 0) & (alpha < 255)):
        return "BLEND"
    return "MASK" if np.any(alpha == 0) else "OPAQUE"


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


def exposed_positions(positions, direction, *occluders):
    neighbors = positions + FACE_STEP[direction]
    inside = ((neighbors >= 0) & (neighbors < occluders[0].shape)).all(axis=1)
    hidden = np.zeros(len(positions), dtype=bool)
    coordinates = tuple(neighbors[inside].T)
    for occluder in occluders:
        hidden[inside] |= occluder[coordinates]
    return positions[~hidden]


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


def double_sided_triangles(tris):
    tris = np.asarray(tris, dtype=np.int64)
    if len(tris) == 0:
        return tris
    return np.concatenate([tris, tris[:, [0, 2, 1]]], axis=0)


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
