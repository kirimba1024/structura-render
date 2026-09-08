from types import SimpleNamespace

import numpy as np
import pytest
from PIL import Image
from structura_core.nbt import parse_state

from structura_render.assets import AssetContext
from structura_render.mesh import build_textured_geometry, voxel_state


@pytest.mark.parametrize("name, single_faces, connected_faces", [
    ("stone", 6, 14),
    ("oak_fence", 6, 39),
    ("glass_pane", 6, 21),
    ("cobblestone_wall", 6, 27),
    ("iron_bars", 4, 20),
    ("torch", 4, 14),
    ("wall_torch[facing=east]", 4, 14),
    ("dandelion", 4, 14),
])
@pytest.mark.parametrize("adjacent", [False, True])
def test_fallback_shapes_keep_faces_and_connections(tmp_path, name, single_faces, connected_faces, adjacent):
    image = Image.new("RGBA", (16, 16), (100, 150, 200, 255))
    bank = SimpleNamespace(
        context=AssetContext(tmp_path),
        read_texture=lambda *args: image,
        resolve=lambda name: {"all": image},
    )
    palette = [parse_state("minecraft:" + name), parse_state("minecraft:stone")]
    source = SimpleNamespace(
        size=(3, 2, 3), present={(0, 0, 0): 0}, palette_raw=palette,
        palette=[str(entry["Name"]) for entry in palette], block_nbt={}, entities=[],
    )
    if adjacent:
        source.present.update({(1, 0, 0): 0, (0, 0, 1): 1})
    state, solid, names, props = voxel_state(source)
    meshes, flat, textured, occluder = build_textured_geometry(source, solid, state, names, props, bank)

    assert len(meshes) == 1
    mesh = meshes[0]
    assert len(mesh.quads) == (connected_faces if adjacent else single_faces)
    assert mesh.quads.min() == 0
    assert mesh.quads.max() == len(mesh.points) - 1
    assert len(mesh.uv) == len(mesh.points)
    assert np.isfinite(mesh.points).all()
    assert ((mesh.uv >= 0) & (mesh.uv <= 1)).all()
    assert (mesh.alpha_modes == 0).all()
    assert textured == ({0, 1} if adjacent else {0})
    assert occluder.shape == state.shape
    assert flat == []
