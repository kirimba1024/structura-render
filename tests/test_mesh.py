import numpy as np
import pytest
from PIL import Image

from structura_render.mesh import (
    MAX_ATLAS_SIZE,
    Atlas,
    upscale_atlas,
    uv_points_for_rect,
)
from structura_render.textures import WATER_ALPHA, TextureBank


@pytest.mark.parametrize("neighbor, faces", [("stone", 5), ("glass", 6), ("water", 5)])
def test_water_culls_only_shared_opaque_or_fluid_faces(tmp_path, neighbor, faces):
    from types import SimpleNamespace
    from structura_core.nbt import parse_state
    from structura_render.assets import AssetContext
    from structura_render.mesh import build_textured_geometry, voxel_state

    images = tmp_path / "textures/block"
    images.mkdir(parents=True)
    for name in ("water_still", "water_flow", "stone", "glass"):
        Image.new("RGBA", (16, 16), (100, 150, 200, 90 if name == "glass" else 255)).save(images / f"{name}.png")
    source = SimpleNamespace(size=(2, 1, 1), present={(0, 0, 0): 0, (1, 0, 0): 1},
                             palette=["minecraft:water", "minecraft:" + neighbor],
                             palette_raw=[parse_state("minecraft:water"), parse_state("minecraft:" + neighbor)],
                             block_nbt={}, entities=[])
    state, solid, names, props = voxel_state(source)
    geometry = build_textured_geometry(source, solid, state, names, props, TextureBank(AssetContext(tmp_path)))[0][0]
    quads = geometry.points[geometry.quads]
    water = quads[(quads[:, :, 0].max(axis=1) <= 1) & (quads[:, :, 0].min(axis=1) < 1)]
    boundary = quads[(quads[:, :, 0] == 1).all(axis=1)]
    assert len(water) == 5
    assert len(boundary) == (2 if neighbor == "glass" else 1 if neighbor == "stone" else 0)
    assert len(water) + (neighbor == "glass") == faces


def test_atlas_deduplicates_equal_pixels_from_distinct_images():
    atlas = Atlas()
    first = Image.new("RGBA", (8, 8), (1, 2, 3, 4))
    duplicate = first.copy()

    assert atlas.add(first) == atlas.add(duplicate)
    assert len(atlas.images) == 1


def test_atlas_upscale_stays_within_common_gpu_texture_limit():
    image = Image.new("RGBA", (600, 500))

    result = upscale_atlas(image)

    assert max(result.size) <= MAX_ATLAS_SIZE
    assert result.size == (1800, 1500)


def test_model_uv_points_keep_vertex_order_inside_atlas_tile():
    result = uv_points_for_rect((.25, .5, .1, .3), ((0, 0), (1, 0), (1, 1), (0, 1)))

    np.testing.assert_allclose(result, [
        [.25, .3], [.5, .3], [.5, .1], [.25, .1],
    ])


def test_water_stays_visible_against_a_light_preview_background(monkeypatch):
    bank = TextureBank()
    water = Image.new("RGBA", (16, 16), (220, 240, 255, 180))
    monkeypatch.setattr(bank, "_read", lambda _stem: water)

    image = bank.resolve("minecraft:water")["all"]

    assert np.asarray(image)[..., 3].min() == WATER_ALPHA


def test_atlas_preserves_hd_pixels_rectangular_images_and_padding():
    atlas = Atlas()
    pixels = np.arange(64 * 32 * 4, dtype=np.uint8).reshape(32, 64, 4)
    atlas.add(Image.fromarray(pixels))
    atlas.add(Image.new('RGBA', (8, 24), (11, 22, 33, 44)))
    image, rects = atlas.build(max_size=128)
    for original, (u0, u1, v0, v1) in zip(atlas.images, rects):
        x0, x1 = round(u0 * image.shape[1]), round(u1 * image.shape[1])
        y0, y1 = round((1 - v1) * image.shape[0]), round((1 - v0) * image.shape[0])
        np.testing.assert_array_equal(image[y0:y1, x0:x1], original)
        np.testing.assert_array_equal(image[y0 - 1, x0:x1], np.asarray(original)[0])


def test_atlas_overflow_rejected_before_output_allocation(monkeypatch):
    import pytest
    atlas = Atlas()
    atlas.add(Image.new('RGBA', (128, 128)))
    def forbidden(*args, **kwargs):
        raise AssertionError('oversized allocation')
    monkeypatch.setattr(np, 'zeros', forbidden)
    with pytest.raises(ValueError, match='max_atlas_size'):
        atlas.build(max_size=128)


@pytest.mark.parametrize("model", [False, True])
@pytest.mark.parametrize("first,second", [
    ("oak_leaves[distance=1,persistent=false]", "oak_leaves[distance=7,persistent=true]"),
    ("oak_leaves", "birch_leaves"),
    ("glass", "glass[custom=true]"),
    ("ice", "ice[custom=true]"),
    ("water[level=0]", "water[level=1]"),
])
def test_transparent_neighbor_states_do_not_emit_coincident_internal_faces(tmp_path, model, first, second):
    import json
    from types import SimpleNamespace
    from structura_core import parse_state
    from structura_render.assets import AssetContext
    from structura_render.mesh import build_textured_geometry, voxel_state

    textures = tmp_path / "textures/block"
    textures.mkdir(parents=True)
    names = [value.split("[", 1)[0] for value in (first, second)]
    for name in set(names):
        texture = "water_still" if name == "water" else name
        Image.new("RGBA", (16, 16), (110, 160, 130, 128)).save(textures / f"{texture}.png")
        if model and name != "water":
            states = tmp_path / "blockstates"
            models = tmp_path / "models/block"
            states.mkdir(exist_ok=True)
            models.mkdir(parents=True, exist_ok=True)
            (states / f"{name}.json").write_text(json.dumps({"variants": {"": {"model": "block/" + name}}}))
            (models / f"{name}.json").write_text(json.dumps({"textures": {"all": "block/" + name}, "elements": [{
                "from": [0, 0, 0], "to": [16, 16, 16], "faces": {
                    direction: {"texture": "#all", "cullface": direction} for direction in ("up", "down", "north", "south", "east", "west")}}]}))
    source = SimpleNamespace(size=(2, 1, 1), present={(0, 0, 0): 0, (1, 0, 0): 1},
                             palette=["minecraft:" + name for name in names],
                             palette_raw=[parse_state("minecraft:" + value) for value in (first, second)], block_nbt={}, entities=[])
    state, solid, names, props = voxel_state(source)
    geometry = build_textured_geometry(source, solid, state, names, props, TextureBank(AssetContext(tmp_path)))[0][0]
    quads = geometry.points[geometry.quads]
    assert not (quads[:, :, 0] == 1).all(axis=1).any()
    assert len(quads) == 10
