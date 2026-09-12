from collections import Counter
from types import SimpleNamespace

import numpy as np
import pytest
from structura_core import parse_state

from structura_render.mesh import build_scene_geometry
from structura_render.packets import textured_packets
from structura_render.textures import TextureBank


@pytest.mark.parametrize('state', [
    'sculk_vein[up=true,down=true,north=true,south=true,east=true,west=true]',
    'pointed_dripstone[vertical_direction=up,thickness=tip,waterlogged=false]',
    'pointed_dripstone[vertical_direction=down,thickness=middle,waterlogged=false]',
    'short_grass',
])
def test_cutout_planes_have_only_one_visible_side_at_any_angle(state):
    bank = TextureBank()
    if not bank.available():
        pytest.skip('Minecraft client assets are unavailable')
    raw = parse_state('minecraft:' + state)
    source = SimpleNamespace(size=(1, 1, 1), present={(0, 0, 0): 0}, palette=[str(raw['Name'])],
                             palette_raw=[raw], block_nbt={}, entities=[])
    geometry = build_scene_geometry(source, bank)
    packets = [packet for mesh in geometry.meshes for packet in textured_packets(mesh)]
    assert packets and all(packet.mode == 'MASK' for packet in packets)
    for direction in ((1, .2, .3), (-1, -.2, -.3), (.3, 1, -.2), (-.3, -1, .2)):
        visible = Counter()
        for packet in packets:
            for points in packet.points[packet.indices]:
                normal = np.cross(points[1] - points[0], points[2] - points[0])
                if not packet.cull or normal @ direction > 1e-6:
                    visible[tuple(sorted(map(tuple, np.round(points, 5))))] += 1
        assert visible and max(visible.values()) == 1
