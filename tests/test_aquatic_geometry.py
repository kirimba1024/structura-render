import json
from itertools import product
from types import SimpleNamespace

import numpy as np
import pytest
from PIL import Image
from structura_core import parse_state

from structura_render.assets import AssetContext
from structura_render.mesh import build_scene_geometry
from structura_render.textures import TextureBank


@pytest.mark.parametrize("position", [(1, 1, 1), (0, 1, 1), (2, 1, 1), (1, 0, 1), (1, 2, 1), (1, 1, 0), (1, 1, 2)])
@pytest.mark.parametrize("block, internal_faces", [
    ("seagrass", 0),
    ("tall_seagrass[half=lower]", 0),
    ("tall_seagrass[half=upper]", 0),
    ("kelp[age=25]", 0),
    ("kelp_plant", 0),
    ("oak_slab[type=bottom,waterlogged=true]", 0),
    ("oak_slab[type=bottom,waterlogged=false]", 6),
    ("short_grass", 6),
    ("air", 6),
])
def test_water_preserves_outer_surface_without_boxes_around_wet_blocks(tmp_path, block, internal_faces, position):
    textures = tmp_path / "textures/block"
    models = tmp_path / "models/block"
    states = tmp_path / "blockstates"
    for directory in (textures, models, states):
        directory.mkdir(parents=True)
    Image.new("RGBA", (16, 16), (100, 150, 200, 255)).save(textures / "water_still.png")
    plant = Image.new("RGBA", (16, 16), (30, 120, 40, 255))
    plant.putpixel((0, 0), (0, 0, 0, 0))
    plant.save(textures / "plant.png")
    model = {
        "textures": {"all": "block/plant"},
        "elements": [{
            "from": [0, 0, 8], "to": [16, 16, 8],
            "faces": {direction: {"texture": "#all"} for direction in ("north", "south")},
        }],
    }
    (models / "plant.json").write_text(json.dumps(model))
    name = block.split("[", 1)[0]
    (states / f"{name}.json").write_text(json.dumps({"variants": {"": {"model": "block/plant"}}}))
    present = dict.fromkeys(product(range(3), repeat=3), 0)
    present[position] = 1
    source = SimpleNamespace(
        size=(3, 3, 3), present=present,
        palette=["minecraft:water", "minecraft:" + name],
        palette_raw=[parse_state("minecraft:water"), parse_state("minecraft:" + block)],
        block_nbt={}, entities=[],
    )

    scene = build_scene_geometry(source, TextureBank(AssetContext(tmp_path)), strict=True)

    mesh, = scene.meshes
    quads = mesh.points[mesh.quads]
    water = quads[mesh.alpha_modes == 2]
    exterior = np.any(np.all(water == 0, axis=1) | np.all(water == 3, axis=1), axis=1)
    boundary = position != (1, 1, 1)
    assert exterior.sum() == 54 - (boundary and internal_faces > 0)
    assert (~exterior).sum() == internal_faces - (boundary and internal_faces > 0)
    assert (mesh.alpha_modes == 1).sum() == (0 if name == "air" else 2)
    assert not scene.flat_groups
