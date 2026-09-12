from collections import Counter

import numpy as np
import pytest

from structura_render.geometry import TexturedMesh, mask_surface, triangulate_quads
from structura_render.lod_geometry import LodMesh, average_rgba, colored_geometry, merge_lods, simplify_lod


def test_far_colors_preserve_linear_brightness_and_cutout_density():
    image = np.array([[(0, 0, 0, 255), (255, 255, 255, 255)]], np.uint8)
    assert tuple(average_rgba(image)) == (188, 188, 188, 255)
    image[0, 0] = (255, 0, 0, 0)
    assert tuple(average_rgba(image)) == (255, 255, 255, 128)
    points = np.array(((0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)), np.float32)
    mesh = TexturedMesh(points, np.array(((0, 1, 2, 3),)), points[:, :2], np.array([1], np.uint8), image)
    assert (colored_geometry([mesh], []).colors[:, 3] == 255).all()
    mesh.alpha_modes[:] = 2
    assert (colored_geometry([mesh], []).colors[:, 3] == 128).all()


def test_simplification_preserves_all_spatial_boundary_vertices():
    mask = np.zeros((16, 16, 16), bool)
    mask[:, :8, :] = True
    points, faces = mask_surface(mask)
    points = np.asarray(points, np.float32)
    original = LodMesh(points, triangulate_quads(faces).astype(np.uint32), np.full((len(points), 4), 255, np.uint8))
    simplified, error = simplify_lod(original, 16)
    boundary = (np.isclose(points, 0) | np.isclose(points, 16)).any(axis=1)
    expected = {tuple(point) for point in points[boundary]}
    assert expected <= {tuple(point) for point in simplified.points}
    assert len(simplified.triangles) < len(original.triangles)
    assert error >= 0 and simplified.triangles.max() < len(simplified.points)


def test_neighboring_levels_keep_the_same_geometric_seam():
    mask = np.zeros((32, 16, 16), bool)
    for x in range(32):
        for z in range(16):
            mask[x, :4 + z // 3, z] = True
    points, faces = mask_surface(mask)
    points = np.asarray(points, np.float32)
    triangles = triangulate_quads(faces).astype(np.uint32)
    left = triangles[(points[triangles][:, :, 0].mean(axis=1) < 16)]
    right = triangles[(points[triangles][:, :, 0].mean(axis=1) > 16)]
    source = LodMesh(points, left, np.full((len(points), 4), 255, np.uint8))
    simplified, _ = simplify_lod(source, 16)
    def seam(vertices, indices):
        edges = set()
        for triangle in vertices[indices]:
            for first, second in ((0, 1), (1, 2), (2, 0)):
                a, b = triangle[first], triangle[second]
                if a[0] == b[0] == 16:
                    edges.add(tuple(sorted((tuple(a), tuple(b)))))
        return edges
    assert seam(points, right) == seam(simplified.points, simplified.triangles)


def voxel_faces(mesh):
    result = Counter()
    for indices in mesh.triangles:
        triangle = mesh.points[indices]
        normal = np.cross(triangle[1] - triangle[0], triangle[2] - triangle[0])
        assert np.count_nonzero(normal) == 1
        axis = int(np.argmax(abs(normal)))
        axes = [(axis + 1) % 3, (axis + 2) % 3]
        polygon = triangle[:, axes]
        lower, upper = polygon.min(axis=0).astype(int), polygon.max(axis=0).astype(int)
        assert (mesh.colors[indices] == mesh.colors[indices[0]]).all()
        for u in range(lower[0], upper[0]):
            for v in range(lower[1], upper[1]):
                point = np.array((u + 0.37, v + 0.61))
                edges = np.roll(polygon, -1, axis=0) - polygon
                delta = point - polygon
                sides = edges[:, 0] * delta[:, 1] - edges[:, 1] * delta[:, 0]
                if (sides >= 0).all() or (sides <= 0).all():
                    result[axis, np.sign(normal[axis]), triangle[0, axis], u, v, tuple(mesh.colors[indices[0]])] += 1
    return result


@pytest.mark.parametrize("alpha", [128, 255])
def test_trees_steps_and_overhangs_keep_every_voxel_face_through_all_levels(alpha):
    mask = np.zeros((16, 16, 16), bool)
    mask[1:15, 1:3, 1:15] = True
    mask[3:5, 3:10, 3:5] = True
    mask[1:8, 8:11, 1:8] = True
    mask[2:7, 11:13, 2:7] = True
    mask[10:14, 6:8, 2:14] = True
    for z in range(5, 14):
        mask[8:14, 2:2 + z // 3, z] = True
    points, quads = mask_surface(mask)
    original = LodMesh(np.asarray(points, np.float32), triangulate_quads(quads).astype(np.uint32),
                       np.tile(np.array((75, 130, 40, alpha), np.uint8), (len(points), 1)))
    expected = voxel_faces(original)
    mesh = original
    for level in range(1, 7):
        mesh, error = simplify_lod(mesh, 16 * 2**level, target_ratio=0, error=2**level)
        assert voxel_faces(mesh) == expected
        assert error == 0
    assert len(mesh.triangles) < len(original.triangles) / 2


def test_touching_materials_keep_sharp_colors_without_interpolated_triangles():
    parts = []
    for translation, color in [((2, 2, 2), (60, 140, 30, 255)), ((6, 2, 2), (160, 80, 35, 255))]:
        points, quads = mask_surface(np.ones((4, 4, 4), bool))
        parts.append((LodMesh(np.asarray(points, np.float32), triangulate_quads(quads).astype(np.uint32),
                              np.tile(np.array(color, np.uint8), (len(points), 1))), translation))
    original = merge_lods(parts)
    simplified, _ = simplify_lod(original, 16, target_ratio=0, error=16)
    assert voxel_faces(simplified) == voxel_faces(original)
    assert {tuple(color) for color in simplified.colors} == {(60, 140, 30, 255), (160, 80, 35, 255)}


def test_nonrectangular_models_and_unpaired_triangles_are_retained():
    points = np.array(((2, 2, 2), (5, 3, 2), (5, 6, 2), (2, 5, 2), (8, 2, 5), (9, 2, 7), (8, 4, 6)), np.float32)
    triangles = np.array(((0, 1, 2), (0, 2, 3), (4, 5, 6)), np.uint32)
    colors = np.tile(np.array((90, 150, 65, 255), np.uint8), (len(points), 1))
    original = LodMesh(points, triangles, colors)
    simplified, error = simplify_lod(original, 16, target_ratio=0, error=100)
    np.testing.assert_array_equal(simplified.points[simplified.triangles], points[triangles])
    assert error == 0
