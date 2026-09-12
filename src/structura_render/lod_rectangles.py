import numpy as np

from .geometry import triangulate_quads


def compact_geometry(points, triangles, colors):
    used, indices = np.unique(triangles, return_inverse=True)
    vertices = np.column_stack((points[used], colors[used]))
    _, selected, remap = np.unique(vertices, axis=0, return_index=True, return_inverse=True)
    return (np.ascontiguousarray(points[used[selected]], np.float32),
            remap[indices].reshape(-1, 3).astype(np.uint32), colors[used[selected]])


def join_rectangles(rectangles, axis):
    other = 1 - axis
    columns = (0, 1, 2, 3, 4, 5, 6, 7 + other, 9 + other)
    order = np.lexsort((rectangles[:, 7 + axis], *(rectangles[:, i] for i in reversed(columns))))
    rectangles = rectangles[order]
    groups = rectangles[:, columns]
    connected = ((groups[1:] == groups[:-1]).all(axis=1)
                 & (rectangles[1:, 7 + axis] == rectangles[:-1, 9 + axis]))
    starts = np.flatnonzero(np.r_[True, ~connected])
    stops = np.r_[starts[1:] - 1, len(rectangles) - 1]
    result = rectangles[starts].copy()
    result[:, 9 + axis] = rectangles[stops, 9 + axis]
    return result


def rectangle_points(rectangles):
    axes = rectangles[:, 0].astype(int)
    points = np.zeros((len(rectangles), 4, 3), np.float32)
    rows, corners = np.arange(len(points))[:, None], np.arange(4)[None, :]
    points[rows, corners, axes[:, None]] = rectangles[:, 2, None]
    points[rows, corners, ((axes + 1) % 3)[:, None]] = rectangles[:, [7, 9, 9, 7]]
    points[rows, corners, ((axes + 2) % 3)[:, None]] = rectangles[:, [8, 8, 10, 10]]
    reverse = rectangles[:, 1] < 0
    points[reverse] = points[reverse, ::-1]
    return points.reshape(-1, 3)


def merge_rectangles(points, triangles, colors, span, target_ratio):
    count = len(triangles) // 2
    pairs = triangles[:count * 2].reshape(-1, 2, 3)
    quads = np.column_stack((pairs[:, 0], pairs[:, 1, 2]))
    corners, shades = points[quads], colors[quads]
    lower, upper = corners.min(axis=1), corners.max(axis=1)
    normals = np.cross(corners[:, 1] - corners[:, 0], corners[:, 2] - corners[:, 0])
    second = np.cross(corners[:, 2] - corners[:, 0], corners[:, 3] - corners[:, 0])
    paired = (pairs[:, 0, 0] == pairs[:, 1, 0]) & (pairs[:, 0, 2] == pairs[:, 1, 1])
    rectangular = ((np.count_nonzero(normals, axis=1) == 1) & (normals == second).all(axis=1)
                   & ((corners == lower[:, None]) | (corners == upper[:, None])).all(axis=(1, 2)))
    uniform = (shades == shades[:, :1]).all(axis=(1, 2))
    boundary = (np.isclose(corners, 0, atol=1e-6, rtol=0)
                | np.isclose(corners, span, atol=1e-6, rtol=0)).any(axis=(1, 2))
    eligible = paired & rectangular & uniform & ~boundary
    selected = np.flatnonzero(eligible)
    if not len(selected):
        return compact_geometry(points, triangles, colors)
    axes = np.argmax(abs(normals[selected]), axis=1)
    uv = np.column_stack(((axes + 1) % 3, (axes + 2) % 3))
    rectangles = np.column_stack((axes, np.sign(normals[selected, axes]), lower[selected, axes], shades[selected, 0],
                                 np.take_along_axis(lower[selected], uv, axis=1),
                                 np.take_along_axis(upper[selected], uv, axis=1)))
    target = max(1, int(count * target_ratio) - (count - len(rectangles)))
    while len(rectangles) > target:
        previous = len(rectangles)
        rectangles = join_rectangles(join_rectangles(rectangles, 0), 1)
        if len(rectangles) == previous:
            break
    retained = np.r_[np.repeat(~eligible, 2), np.ones(len(triangles) % 2, bool)]
    merged = rectangle_points(rectangles)
    indices = triangulate_quads(np.arange(len(merged)).reshape(-1, 4)) + len(points)
    shades = np.repeat(rectangles[:, 3:7], 4, axis=0).astype(np.uint8)
    return compact_geometry(np.concatenate((points, merged)), np.concatenate((triangles[retained], indices)),
                            np.concatenate((colors, shades)))
