import numpy as np

from structura_render.geometry import CUBE_CORNERS, CUBE_FACES
from structura_render.shading import Shading, face_shading, shaded_triangles, shade_colors
from structura_render.packets import RenderPacket, merge_packets, polygon_packets


def test_cube_corner_ao_two_sides_and_diagonal_preserves_winding():
    occluder = np.zeros((4, 4, 4), bool)
    positions = np.asarray([[1, 1, 1]], np.float32)
    offsets = CUBE_CORNERS[CUBE_FACES['up']]
    clear = face_shading(positions, offsets, occluder)
    assert (clear[:, :2] == 255).all()
    occluder[0, 2, 1] = occluder[1, 2, 0] = True
    values = face_shading(positions, offsets, occluder)
    assert values[0, 0] == round(.55 * 255)
    assert values[2, 0] == 255
    triangles = shaded_triangles(np.arange(4).reshape(1, 4), values)
    corners = offsets[triangles]
    assert (np.cross(corners[:, 1] - corners[:, 0], corners[:, 2] - corners[:, 0])[:, 1] > 0).all()


def test_partial_face_is_not_treated_as_a_full_cube():
    offsets = CUBE_CORNERS[CUBE_FACES['up']].copy()
    offsets[:, 1] = .5
    values = face_shading(np.asarray([[1, 1, 1]]), offsets, np.ones((4, 4, 4), bool))
    assert (values[:, 0] == 255).all()


def test_modes_preserve_albedo_alpha_uv_and_packet_merge():
    points = CUBE_CORNERS[CUBE_FACES['up']]
    colors = np.tile([200, 100, 50, 120], (4, 1)).astype(np.uint8)
    shade = np.tile([140, 200], (4, 1)).astype(np.uint8)
    packet = RenderPacket(points, np.arange(4).reshape(1, 4), 'BLEND', colors=colors, shading=shade)
    assert np.array_equal(shade_colors(packet, Shading(False, False)), colors)
    assert (shade_colors(packet)[:, 3] == 120).all()
    assert np.array_equal(packet.colors, colors)
    parts = list(polygon_packets(points, packet.indices, 'BLEND', colors=colors, shading=shade))
    merged = list(merge_packets(parts * 2))[0]
    assert np.array_equal(merged.shading, np.concatenate([shade, shade]))


def test_ao_diagonal_preserves_affine_texture_coordinates():
    points = np.array(((0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)), np.float32)
    uv = points[:, :2] * (.6, .4) + (.1, .2)
    for values in ((255, 140, 255, 140), (140, 255, 140, 255)):
        shading = np.column_stack((values, [255] * 4)).astype(np.uint8)
        triangles = shaded_triangles(np.array([[0, 1, 2, 3]]), shading)
        for indices in triangles:
            for weights in ((.2, .3, .5), (.6, .1, .3), (1 / 3,) * 3):
                point = np.asarray(weights) @ points[indices]
                mapped = np.asarray(weights) @ uv[indices]
                assert np.allclose(mapped, point[:2] * (.6, .4) + (.1, .2))


def test_shared_cube_vertices_keep_uniform_face_shading_and_source_colors():
    from structura_render.shading import flat_packet_shading

    points = np.asarray(CUBE_CORNERS, np.float32)
    faces = np.asarray(list(CUBE_FACES.values()), np.int32)
    colors = np.full((len(points), 4), (120, 150, 180, 200), np.uint8)
    original = RenderPacket(points, faces, 'BLEND', colors=colors)
    shaded = flat_packet_shading(original)
    assert np.array_equal(shaded.points[shaded.indices], original.points[original.indices])
    values = shaded.shading[shaded.indices, 1]
    assert (values == values[:, :1]).all()
    assert set(values.ravel()) == {166, 209, 230, 255}
    assert np.all(shaded.colors == (120, 150, 180, 200))
    assert original.shading is None and len(original.points) == 8
