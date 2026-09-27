import numpy as np
import pytest

from structura_render.voxel_lod import block_voxels, empty_voxels, reduce_voxels, voxel_colors, voxel_mesh


@pytest.mark.parametrize('pattern', ['stairs', 'isolated', 'wall', 'water', 'cave'])
def test_every_distant_face_stays_on_the_cube_grid_through_repeated_reduction(pattern):
    blocks = np.full((32, 32, 32), -1, np.int32)
    if pattern == 'stairs':
        for x in range(32):
            blocks[x, :x + 1, :] = 0
    elif pattern == 'isolated':
        blocks[::3, ::3, ::3] = 0
    elif pattern == 'wall':
        blocks[:, 4:5, :] = 0
        blocks[10:20, 4, 10:20] = -1
    elif pattern == 'water':
        blocks[:, :8, :] = 1
    else:
        blocks[:] = 0
        blocks[:, 6:18, 6:18] = -1
    palette = np.array([(100, 150, 80, 255), (40, 80, 160, 110)], np.uint8)
    samples = block_voxels(blocks, palette, factor=2)
    for step in (2, 4, 8):
        mesh = voxel_mesh(samples, step)
        corners = mesh.points[mesh.triangles]
        normals = np.cross(corners[:, 1] - corners[:, 0], corners[:, 2] - corners[:, 0])
        assert len(normals) and (np.count_nonzero(normals, axis=1) == 1).all()
        assert (mesh.points % step == 0).all()
        assert (mesh.points >= 0).all() and (mesh.points <= 32).all()
        colors = mesh.colors[mesh.triangles]
        assert (colors == colors[:, :1]).all()
        repeated = voxel_mesh(samples, step)
        np.testing.assert_array_equal(repeated.points, mesh.points)
        np.testing.assert_array_equal(repeated.triangles, mesh.triangles)
        samples = reduce_voxels(samples)


def test_sparse_features_survive_and_known_air_is_distinct_from_unknown():
    blocks = np.full((16, 16, 16), -1, np.int32)
    blocks[1, 2, 3] = 0
    samples = block_voxels(blocks, np.array([(200, 80, 40, 255)], np.uint8))
    assert samples[..., 0].sum() == 1 and samples[..., 10].sum() == 4096
    assert not empty_voxels(4)[..., 10].any()
    coarse = reduce_voxels(reduce_voxels(samples))
    assert tuple(voxel_colors(coarse)[0, 0, 0]) == (200, 80, 40, 255)
    mesh = voxel_mesh(coarse, 16)
    assert len(mesh.triangles) == 12
    assert set(map(tuple, mesh.points)) == {(x, y, z) for x in (0, 16) for y in (0, 16) for z in (0, 16)}


def test_opaque_and_blended_samples_are_never_averaged_together():
    blocks = np.ones((8, 8, 8), np.int32)
    blocks[0, 0, 0] = 0
    samples = block_voxels(blocks, np.array([(255, 0, 0, 255), (0, 0, 255, 100)], np.uint8))
    colors = voxel_colors(samples)
    assert tuple(colors[0, 0, 0]) == (255, 0, 0, 255)
    assert tuple(colors[-1, -1, -1]) == (0, 0, 255, 100)
    assert set(voxel_mesh(samples, 4).colors[:, 3]) == {100, 255}


def test_solid_volume_has_no_internal_faces_and_all_six_sides_are_closed():
    samples = block_voxels(np.zeros((16, 16, 16), np.int32), np.array([(50, 100, 150, 255)], np.uint8))
    mesh = voxel_mesh(samples, 4)
    corners = mesh.points[mesh.triangles]
    normals = np.cross(corners[:, 1] - corners[:, 0], corners[:, 2] - corners[:, 0])
    assert np.linalg.norm(normals, axis=1).sum() / 2 == 6 * 16**2
    for axis in range(3):
        for sign in (-1, 1):
            assert (normals[:, axis] * sign > 0).any()
    empty = voxel_mesh(empty_voxels(4), 4)
    assert empty.points.shape == empty.triangles.shape == (0, 3)


def test_reduction_is_additive_across_sections():
    random = np.random.default_rng(4)
    blocks = random.integers(-1, 2, (32, 32, 32), dtype=np.int32)
    palette = np.array([(255, 10, 20, 255), (30, 80, 200, 90)], np.uint8)
    expected = block_voxels(blocks, palette, factor=8)
    assembled = empty_voxels(8)
    for x in range(2):
        for y in range(2):
            for z in range(2):
                source = tuple(slice(p * 16, (p + 1) * 16) for p in (x, y, z))
                target = tuple(slice(p * 4, (p + 1) * 4) for p in (x, y, z))
                assembled[target] = block_voxels(blocks[source], palette, origin_y=y * 16)
    actual = reduce_voxels(assembled)
    np.testing.assert_array_equal(actual[..., [0, 5, 10]], expected[..., [0, 5, 10]])
    np.testing.assert_allclose(actual, expected, rtol=4e-6)
    np.testing.assert_array_equal(voxel_colors(actual), voxel_colors(expected))



def test_emit_bounds_uses_halo_for_culling_without_emitting_neighbor_faces():
    import numpy as np
    from structura_render.voxel_lod import block_voxels, voxel_mesh

    blocks = np.zeros((6, 6, 6), np.int32)
    palette = np.array(((80, 100, 120, 255),), np.uint8)
    bounds = ((1, 1, 1), (2, 2, 2))
    assert len(voxel_mesh(block_voxels(blocks, palette, factor=2), 2, emit_bounds=bounds).triangles) == 0
    blocks[:2] = -1
    mesh = voxel_mesh(block_voxels(blocks, palette, factor=2), 2, emit_bounds=bounds)
    assert len(mesh.triangles) == 2
    assert np.all(mesh.points[:, 0] == 2)
    assert np.all(mesh.points[:, 1:] >= 2) and np.all(mesh.points[:, 1:] <= 4)


@pytest.mark.parametrize('surface', [1, 5, 7, 15, 23])
@pytest.mark.parametrize('origin_y', [-64, 0, 80])
def test_water_keeps_its_surface_and_bottom_through_all_reductions(surface, origin_y):
    blocks = np.full((32, 32, 32), -1, np.int32)
    blocks[:, :surface] = 0
    samples = block_voxels(blocks, np.array([(40, 80, 160, 110)], np.uint8), factor=2, origin_y=origin_y)
    for step in (2, 4, 8, 16, 32):
        mesh = voxel_mesh(samples, step, origin_y=origin_y)
        triangles = mesh.points[mesh.triangles]
        normals = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
        np.testing.assert_array_equal(triangles[normals[:, 1] > 0, :, 1], surface)
        np.testing.assert_array_equal(triangles[normals[:, 1] < 0, :, 1], 0)
        assert np.isclose(np.linalg.norm(normals, axis=1).sum() / 2, 2 * 32**2 + 4 * 32 * surface)
        samples = reduce_voxels(samples) if step < 32 else samples


def test_blended_steps_emit_only_the_exposed_vertical_strip():
    blocks = np.full((4, 4, 4), -1, np.int32)
    blocks[:2, :3] = 0
    blocks[2:, :2] = 0
    samples = block_voxels(blocks, np.array([(40, 80, 160, 110)], np.uint8), factor=2)
    mesh = voxel_mesh(samples, 2)
    triangles = mesh.points[mesh.triangles]
    side = triangles[np.all(triangles[..., 0] == 2, axis=1)]
    assert len(side) and side[..., 1].min() == 2 and side[..., 1].max() == 3
