import pickle
from collections import Counter

import numpy as np
import pytest

from structura_render.geometry import TexturedMesh, mask_surface, triangulate_quads
from structura_render.lod_geometry import LodMesh, empty_lod, merge_lods
from structura_render.packets import lod_packets, polygon_packets, textured_packets


@pytest.mark.parametrize('width', [3, 4])
def test_packets_bound_buffers_and_preserve_polygons_and_attributes(width):
    points = np.arange(3600, dtype=np.float64).reshape(-1, 3)
    indices = np.arange(1200).reshape(-1, width)
    uv = points[:, :2] / 3600
    colors = (points[:, [0, 1, 2, 0]] % 256).astype(np.uint8)
    packets = list(polygon_packets(points, indices, 'BLEND', uv=uv, colors=colors, max_bytes=2048, max_vertices=50))
    assert len(packets) > 1
    rebuilt = pickle.loads(pickle.dumps(packets))
    for packet in rebuilt:
        assert packet.nbytes <= 2048 and len(packet.points) <= 50
        assert packet.indices.dtype == np.int32 and packet.points.dtype == np.float32
        assert packet.indices.flags.c_contiguous and packet.points.flags.c_contiguous
    assert np.array_equal(np.concatenate([p.points[p.indices] for p in rebuilt]), points[indices])
    assert np.allclose(np.concatenate([p.uv[p.indices] for p in rebuilt]), uv[indices])
    assert np.array_equal(np.concatenate([p.colors[p.indices] for p in rebuilt]), colors[indices])


def test_material_split_retains_uvs_and_shares_texture_identity():
    mesh = TexturedMesh(np.arange(36, dtype=np.float32).reshape(-1, 3), np.arange(12).reshape(-1, 4),
                        np.arange(24, dtype=np.float32).reshape(-1, 2), np.arange(3, dtype=np.uint8),
                        np.ones((4, 4, 4), dtype=np.uint8))
    packets = list(textured_packets(mesh))
    assert [p.mode for p in packets] == ['OPAQUE', 'MASK', 'BLEND']
    assert [p.cull for p in packets] == [True, True, False]
    assert all(p.image is mesh.image and p.texture_key == packets[0].texture_key for p in packets)
    assert np.array_equal(np.concatenate([p.uv[p.indices] for p in packets]), mesh.uv[mesh.quads])


def triangle_records(points, triangles, colors):
    return Counter(tuple(tuple(vertex) for vertex in np.column_stack((points[face], colors[face]))) for face in triangles)


def test_lod_quads_preserve_every_oriented_triangle_and_material_in_bounded_packets():
    points, quads = mask_surface(np.ones((48, 32, 48), bool))
    points = np.asarray(points, np.float32)
    triangles = triangulate_quads(quads).astype(np.uint32)
    parts = [(LodMesh(points, triangles, np.tile(color, (len(points), 1)).astype(np.uint8)), offset)
             for color, offset in [((60, 120, 30, 255), (-80, -32, -48)), ((30, 70, 200, 128), (48, 0, 48))]]
    mesh = merge_lods(parts)
    before = triangle_records(mesh.points, mesh.triangles, mesh.colors)
    packets = pickle.loads(pickle.dumps(list(lod_packets(mesh))))
    after = Counter()
    for packet in packets:
        assert packet.indices.shape[1] == 4
        assert packet.nbytes <= 1024**2 and len(packet.points) <= 65536
        assert packet.cull == (packet.mode == 'OPAQUE')
        after.update(triangle_records(packet.points, triangulate_quads(packet.indices), packet.colors))
    assert after == before
    assert sum(packet.indices.nbytes for packet in packets) == mesh.triangles.nbytes * 2 // 3
    assert triangle_records(mesh.points, mesh.triangles, mesh.colors) == before


@pytest.mark.parametrize('kind', ['gradient', 'sloped', 'unpaired', 'degenerate'])
def test_lod_keeps_faces_that_cannot_safely_become_rectangles(kind):
    points = np.array(((0, 0, 0), (2, 0, 0), (2, 2, 0), (0, 2, 0)), np.float32)
    triangles = np.array(((0, 1, 2), (0, 2, 3)), np.uint32)
    colors = np.full((4, 4), 255, np.uint8)
    if kind == 'gradient':
        colors[1, 0] = 0
    elif kind == 'sloped':
        points[1, 2] = 1
    elif kind == 'unpaired':
        triangles = triangles[:1]
    else:
        points[:] = 0
    mesh = LodMesh(points, triangles, colors)
    packets = list(lod_packets(mesh))
    assert all(packet.indices.shape[1] == 3 for packet in packets)
    actual = sum((triangle_records(p.points, p.indices, p.colors) for p in packets), Counter())
    assert actual == triangle_records(points, triangles, colors)


def test_empty_lod_has_no_packets():
    assert list(lod_packets(empty_lod())) == []


def test_prepared_lod_join_preserves_attributes_and_respects_both_packet_limits(monkeypatch):
    from structura_render import packets as module

    monkeypatch.setattr(module, 'PACKET_BYTES', 512)
    monkeypatch.setattr(module, 'PACKET_VERTICES', 20)
    inputs = []
    for width, mode in ((3, 'OPAQUE'), (4, 'BLEND'), (4, 'OPAQUE')):
        points = np.arange(width * 48, dtype=np.float32).reshape(-1, 3)
        colors = (points[:, [0, 1, 2, 0]] % 256).astype(np.uint8)
        inputs.extend(polygon_packets(points, np.arange(len(points)).reshape(-1, width), mode,
                                      colors=colors, cull=mode == 'OPAQUE', max_vertices=width))
    before = [(p.points.copy(), p.indices.copy(), p.colors.copy()) for p in inputs]
    result = list(module.merge_packets(inputs))
    assert len(result) < len(inputs)
    for width, mode in ((3, 'OPAQUE'), (4, 'BLEND'), (4, 'OPAQUE')):
        old = [p for p in inputs if p.mode == mode and p.indices.shape[1] == width]
        new = [p for p in result if p.mode == mode and p.indices.shape[1] == width]
        for name in ('points', 'colors'):
            np.testing.assert_array_equal(np.concatenate([getattr(p, name)[p.indices] for p in old]),
                                          np.concatenate([getattr(p, name)[p.indices] for p in new]))
    for packet in result:
        assert packet.nbytes <= 512 and len(packet.points) <= 20
        assert packet.cull == (packet.mode == 'OPAQUE')
    for packet, arrays in zip(inputs, before):
        for name, array in zip(('points', 'indices', 'colors'), arrays):
            np.testing.assert_array_equal(getattr(packet, name), array)
    assert list(module.merge_packets([inputs[0]]))[0] is inputs[0]


def test_joined_textured_packets_preserve_uv_alpha_material_and_source_buffers():
    from structura_render.packets import RenderPacket, merge_packets

    image = np.arange(64, dtype=np.uint8).reshape(4, 4, 4)
    points = np.array(((0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)), np.float32)
    indices = np.array(((0, 1, 2, 3),), np.int32)
    uv = points[:, :2].copy()
    packets = [RenderPacket(points + offset, indices.copy(), mode, uv=uv.copy(), image=image,
                            texture_key=key, cull=mode != 'BLEND')
               for offset, mode, key in ((0, 'MASK', 'a'), (2, 'MASK', 'a'), (4, 'BLEND', 'a'), (6, 'MASK', 'b'))]
    joined = list(merge_packets(packets))
    assert len(joined) == 3
    assert joined[0].mode == 'MASK' and joined[0].cull
    assert joined[0].image is image and joined[0].texture_key == 'a'
    assert np.array_equal(joined[0].points[joined[0].indices], np.concatenate([p.points[p.indices] for p in packets[:2]]))
    assert np.array_equal(joined[0].uv[joined[0].indices], np.concatenate([p.uv[p.indices] for p in packets[:2]]))
    assert joined[1] is packets[2] and joined[2] is packets[3]
    assert all(np.array_equal(p.indices, indices) and np.array_equal(p.uv, uv) for p in packets)
