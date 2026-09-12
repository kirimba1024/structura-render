import pickle

import numpy as np
import pytest

from structura_render.geometry import TexturedMesh
from structura_render.packets import polygon_packets, textured_packets


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
