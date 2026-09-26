from dataclasses import replace

import numpy as np
import pytest

from structura_render.atlas import compact_packet_atlas
from structura_render.packets import RenderPacket


def sample(image, uv):
    height, width = image.shape[:2]
    pixels = uv * (width, -height) + (-.5, height - .5)
    lower = np.floor(pixels).astype(int)
    blend = pixels - lower
    colors = np.zeros((*uv.shape[:-1], 4))
    for dx, dy in ((0, 0), (0, 1), (1, 0), (1, 1)):
        weight = (blend[..., 0] if dx else 1 - blend[..., 0]) * (blend[..., 1] if dy else 1 - blend[..., 1])
        colors += image[np.clip(lower[..., 1] + dy, 0, height - 1),
                        np.clip(lower[..., 0] + dx, 0, width - 1)] * weight[..., None]
    return colors


def packet(image, offset, mode, *, shared=False):
    x, y = offset
    pixels = np.array(((x + 1, y + 1), (x + 9, y + 1), (x + 9, y + 9), (x + 1, y + 9),
                       (x + 5, y + 5)), np.float32)
    points = np.column_stack((pixels, np.zeros(5))).astype(np.float32)
    uv = (pixels / image.shape[1::-1] * (1, -1) + (0, 1)).astype(np.float32)
    faces = ((0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4)) if shared else ((0, 1, 2), (0, 2, 3))
    return RenderPacket(points, np.array(faces, np.int32), mode, uv=uv, image=image, cull=mode != 'BLEND',
                        colors=np.arange(20, dtype=np.uint8).reshape(5, 4),
                        shading=np.arange(10, dtype=np.uint8).reshape(5, 2))


@pytest.mark.parametrize('shared', [False, True])
def test_compaction_preserves_samples_winding_and_attributes_with_shared_vertices(shared):
    rng = np.random.default_rng(42)
    tile = rng.integers(0, 256, (10, 10, 4), np.uint8)
    inputs = []
    for mode, offset in zip(('OPAQUE', 'MASK', 'BLEND'), ((2, 3), (30, 20), (40, 35))):
        image = rng.integers(0, 256, (64, 96, 4), np.uint8)
        x, y = offset
        image[y:y + 10, x:x + 10] = tile
        inputs.append(packet(image, offset, mode, shared=shared))
    inputs[1].uv = inputs[1].uv[[2, 1, 0, 3, 4]].copy()
    before = [(p.points.copy(), p.indices.copy(), p.uv.copy(), p.image.copy()) for p in inputs]
    output = compact_packet_atlas(inputs)
    assert output is not None and len(output) == len(inputs)
    assert all(p.image is output[0].image and p.texture_key == output[0].texture_key for p in output)
    assert output[0].image.nbytes < sum(p.image.nbytes for p in inputs) / 10
    weights = np.vstack((np.eye(3), rng.dirichlet((1, 1, 1), 100)))
    for old, new, arrays in zip(inputs, output, before):
        assert (new.mode, new.color, new.cull) == (old.mode, old.color, old.cull)
        for name in ('points', 'colors', 'shading'):
            np.testing.assert_array_equal(getattr(old, name)[old.indices], getattr(new, name)[new.indices])
        expected = sample(old.image, np.einsum('wv,fvd->fwd', weights, old.uv[old.indices]))
        actual = sample(new.image, np.einsum('wv,fvd->fwd', weights, new.uv[new.indices]))
        np.testing.assert_allclose(actual, expected, atol=.003, rtol=0)
        for name, array in zip(('points', 'indices', 'uv', 'image'), arrays):
            np.testing.assert_array_equal(getattr(old, name), array)


def test_compaction_preserves_clamped_texture_edges_and_flat_packets():
    image = np.random.default_rng(0).integers(0, 256, (64, 64, 4), np.uint8)
    original = packet(image, (-1, -1), 'BLEND')
    flat = replace(original, image=None, uv=None)
    compact = compact_packet_atlas([original, flat])
    assert compact is not None and compact[1] is flat
    weights = np.vstack((np.eye(3), np.full((1, 3), 1 / 3)))
    np.testing.assert_allclose(sample(original.image, np.einsum('wv,fvd->fwd', weights, original.uv[original.indices])),
                               sample(compact[0].image, np.einsum('wv,fvd->fwd', weights, compact[0].uv[compact[0].indices])),
                               atol=.003, rtol=0)


def test_compaction_falls_back_when_unprofitable_too_large_or_uv_repeats():
    image = np.ones((10, 10, 4), np.uint8)
    original = packet(image, (0, 0), 'OPAQUE')
    assert compact_packet_atlas([original]) is None
    assert compact_packet_atlas([original], max_size=4) is None
    original.uv += 1
    assert compact_packet_atlas([original]) is None
    assert compact_packet_atlas([]) is None


@pytest.mark.parametrize('limit', ['PACKET_VERTICES', 'PACKET_BYTES'])
def test_compaction_does_not_expand_packets_beyond_their_budget(monkeypatch, limit):
    from structura_render import atlas

    original = packet(np.zeros((64, 64, 4), np.uint8), (8, 8), 'MASK', shared=True)
    maximum = len(original.points) if limit == 'PACKET_VERTICES' else original.nbytes
    monkeypatch.setattr(atlas, limit, maximum)
    assert atlas.compact_packet_atlas([original]) is None
