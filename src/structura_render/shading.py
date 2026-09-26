from dataclasses import dataclass, replace

import numpy as np


@dataclass(frozen=True)
class Shading:
    ao: bool = True
    directional: bool = True


def sample_grid(grid, positions, default):
    shape = positions.shape[:-1]
    positions = positions.reshape(-1, 3)
    result = np.full(len(positions), default, dtype=grid.dtype)
    inside = ((positions >= 0) & (positions < grid.shape[:3])).all(axis=1)
    result[inside] = grid[tuple(positions[inside].T)]
    return result.reshape(shape)


def directional_brightness(normals):
    normals = np.asarray(normals, np.float64)
    return (normals[..., 0]**2 * .82 + normals[..., 1]**2 * np.where(normals[..., 1] >= 0, 1, .65)
            + normals[..., 2]**2 * .9)


def face_normals(points, indices):
    corners = points[indices]
    normals = np.cross(corners[:, 1] - corners[:, 0], corners[:, 2] - corners[:, 0])
    return normals / np.maximum(np.linalg.norm(normals, axis=1)[:, None], 1e-12)


def flat_packet_shading(packet):
    normals = face_normals(packet.points, packet.indices)
    values = np.rint(directional_brightness(normals) * 255).astype(np.int32)
    keys = np.column_stack((packet.indices.ravel(), np.repeat(values, packet.indices.shape[1])))
    vertices, inverse = np.unique(keys, axis=0, return_inverse=True)
    used = vertices[:, 0]
    shading = np.column_stack((np.full(len(used), 255), vertices[:, 1])).astype(np.uint8)
    return replace(packet, points=packet.points[used], indices=inverse.reshape(packet.indices.shape).astype(np.int32),
                   uv=packet.uv[used] if packet.uv is not None else None,
                   colors=packet.colors[used] if packet.colors is not None else None, shading=shading)


def face_shading(positions, offsets, occluder=None):
    normal = np.cross(offsets[1] - offsets[0], offsets[2] - offsets[0])
    length = np.linalg.norm(normal)
    normal = normal / length if length else np.zeros(3)
    directional = directional_brightness(normal)
    result = np.full((len(positions), 4, 2), 255, np.uint8)
    result[:, :, 1] = round((directional if length else 1) * 255)
    aligned = np.count_nonzero(np.abs(normal) > .001) == 1
    boundary = np.all(np.isclose(offsets, 0) | np.isclose(offsets, 1))
    if occluder is not None and aligned and boundary:
        axis = int(np.argmax(np.abs(normal)))
        tangents = [i for i in range(3) if i != axis]
        base = positions.astype(np.int32) + np.rint(normal).astype(np.int32)
        for vertex in range(4):
            first, second = np.zeros(3, np.int32), np.zeros(3, np.int32)
            first[tangents[0]] = 1 if offsets[vertex, tangents[0]] > .5 else -1
            second[tangents[1]] = 1 if offsets[vertex, tangents[1]] > .5 else -1
            a = sample_grid(occluder, base + first, False)
            b = sample_grid(occluder, base + second, False)
            corner = sample_grid(occluder, base + first + second, False)
            level = np.where(a & b, 0, 3 - a.astype(np.int8) - b - corner)
            result[:, vertex, 0] = np.rint(255 * (.55 + .15 * level)).astype(np.uint8)
    return result.reshape(-1, 2)


def shaded_triangles(quads, shading):
    quads = np.asarray(quads)
    values = shading[quads, 0].astype(np.int32)
    flip = values[:, 0] + values[:, 2] > values[:, 1] + values[:, 3]
    ordered = quads.copy()
    ordered[flip] = ordered[flip][:, [1, 2, 3, 0]]
    return ordered[:, [[0, 1, 2], [0, 2, 3]]].reshape(-1, 3)


def polygon_shading(points, indices, *, occluder=None):
    corners = points[indices]
    normals = face_normals(points, indices)
    centers = corners.mean(axis=1)
    values = np.full((len(indices), indices.shape[1], 2), 255, np.uint8)
    directions = directional_brightness(normals)
    values[:, :, 1] = np.rint(directions * 255).astype(np.uint8)[:, None]
    if occluder is not None and indices.shape[1] == 4:
        anchors = np.floor(centers - normals * .001).astype(np.int32)
        offsets = corners - anchors[:, None, :]
        shapes, groups = np.unique(offsets.reshape(-1, 12), axis=0, return_inverse=True)
        for index, shape in enumerate(shapes):
            selected = groups == index
            values[selected, :, 0] = face_shading(anchors[selected], shape.reshape(4, 3), occluder)[:, 0].reshape(-1, 4)
    counts = np.bincount(indices.ravel(), minlength=len(points))
    result = np.empty((len(points), 2), np.uint8)
    for channel in range(2):
        total = np.bincount(indices.ravel(), weights=values[:, :, channel].ravel(), minlength=len(points))
        result[:, channel] = np.rint(total / np.maximum(counts, 1)).astype(np.uint8)
    return result


def shade_colors(packet, settings=Shading()):
    colors = np.full((len(packet.points), 4), packet.color, np.uint8) if packet.colors is None else packet.colors.copy()
    shading = packet.shading
    if shading is None:
        return colors
    brightness = np.ones(len(colors), np.float32)
    if settings.ao:
        brightness *= shading[:, 0] / 255
    if settings.directional:
        brightness *= shading[:, 1] / 255
    colors[:, :3] = np.rint(colors[:, :3] * brightness[:, None]).astype(np.uint8)
    return colors
