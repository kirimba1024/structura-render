import numpy as np
import pytest

from structura_render.geometry import TexturedMesh, mask_surface, triangulate_quads
from structura_render.lod_geometry import LodMesh, average_rgba, colored_geometry, simplify_lod


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
    pytest.importorskip("meshoptimizer")
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
    pytest.importorskip("meshoptimizer")
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
