from copy import deepcopy
from types import SimpleNamespace

import numpy as np
import pytest
from PIL import Image

from structura_render.atlas import Atlas
from structura_render.model_textures import ModelTextures
from structura_render.textures import GRASS_TINT, _tint


@pytest.mark.parametrize("rotation", range(4))
def test_coincident_grass_layers_become_one_tinted_surface(rotation):
    base = Image.new("RGBA", (2, 2), (90, 60, 30, 255))
    overlay = Image.new("RGBA", (2, 2), (255, 255, 255, 0))
    overlay.putpixel((0, 0), (255, 255, 255, 255))
    images = {"side": base, "overlay": overlay}
    bank = SimpleNamespace(read_texture=lambda texture, tint: _tint(images[texture], tint) if tint else images[texture])
    face = dict(vertices=((0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)), uv=(0, 0, 1, 1),
                uv_rotation=rotation, cullface="north", tinted=False, texture="side")
    layers = [{"faces": {"north": face}}, {"faces": {"north": dict(face, tinted=True, texture="overlay")}}]
    atlas = Atlas()
    faces = ModelTextures(bank, atlas).faces(layers, "minecraft:grass_block", {})
    assert len(faces) == 1
    image = atlas.images[faces[0].rect_index]
    assert image.getpixel((0, 0)) == (*GRASS_TINT, 255)
    assert image.getpixel((1, 1)) == (90, 60, 30, 255)
    np.testing.assert_array_equal(faces[0].vertices, face["vertices"])
    assert faces[0].cullface == "north"
    assert base.getpixel((0, 0)) == (90, 60, 30, 255)


def test_different_faces_and_uv_mappings_stay_separate():
    face = dict(vertices=((0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)), uv=(0, 0, 1, 1),
                uv_rotation=0, cullface="north", tinted=False, texture="side")
    other = deepcopy(face)
    other["vertices"] = tuple((x, y, z + .1) for x, y, z in face["vertices"])
    layers = [{"faces": {"north": value}} for value in (face, other, dict(face, uv_rotation=1))]
    bank = SimpleNamespace(read_texture=lambda *_: Image.new("RGBA", (2, 2), (90, 60, 30, 255)))
    assert len(ModelTextures(bank, Atlas()).faces(layers, "minecraft:stone", {})) == 3
