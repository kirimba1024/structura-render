import numpy as np
import pytest
from amulet_nbt import CompoundTag, DoubleTag, IntTag, ListTag, StringTag
from PIL import Image
from structura_core import Structure, parse_state

from structura_render import AssetContext, RenderWarning, TextureBank
from structura_render.block_geometry import flat_block_groups, voxel_state
from structura_render.mesh import build_scene_geometry, build_textured_geometry


def source_with_blocks(*names):
    source = Structure.from_root(CompoundTag({
        "DataVersion": IntTag(3955),
        "size": ListTag([IntTag(max(1, len(names))), IntTag(1), IntTag(1)]),
        "palette": ListTag([parse_state("minecraft:" + name) for name in names]),
        "blocks": ListTag(), "entities": ListTag(),
    }))
    source.present = {(i, 0, 0): i for i in range(len(names))}
    return source


@pytest.mark.parametrize("all_solid", [False, True])
def test_flat_glass_does_not_remove_the_opaque_face_behind_it(all_solid):
    source = source_with_blocks("stone", "glass")
    state, solid, names, _ = voxel_state(source)
    occluder = solid if all_solid else np.zeros_like(solid)
    groups = flat_block_groups(state, names, set(), occluder)
    _, points, faces = next(group for group in groups if group[0][3] == 255)
    quads = np.asarray(points)[faces]

    assert len(quads) == 6
    assert np.any((quads[:, :, 0] == 1).all(axis=1))


@pytest.mark.parametrize("name", ["chest", "conduit", "oak_sign", "decorated_pot"])
def test_missing_special_texture_preserves_geometry_and_strict_failure(tmp_path, name):
    source = source_with_blocks(name)
    state, solid, names, props = voxel_state(source)
    bank = TextureBank(AssetContext(tmp_path))

    with pytest.warns(RenderWarning, match="missing texture"):
        meshes, _, indices, _ = build_textured_geometry(source, solid, state, names, props, bank)

    assert meshes and len(meshes[0].quads) > 0
    assert indices == {0}
    assert np.isfinite(meshes[0].points).all()
    with pytest.raises(ValueError, match="missing texture"):
        build_textured_geometry(source, solid, state, names, props, bank, strict=True)


@pytest.mark.parametrize("textured", [False, True])
def test_entity_only_scene_keeps_fractional_coordinates_without_textures(tmp_path, textured):
    source = source_with_blocks("air")
    source.entities = [CompoundTag({
        "pos": ListTag([DoubleTag(2.25), DoubleTag(1.5), DoubleTag(3.75)]),
        "blockPos": ListTag([IntTag(2), IntTag(1), IntTag(3)]),
        "nbt": CompoundTag({"id": StringTag("minecraft:tnt")}),
    })]
    context = AssetContext(tmp_path)
    with context.activate():
        if textured:
            with pytest.warns(RenderWarning, match="missing texture"):
                scene = build_scene_geometry(source, TextureBank(context))
            points = scene.meshes[0].points
        else:
            scene = build_scene_geometry(source)
            points = np.concatenate([points for _, points, _ in scene.flat_groups])

    np.testing.assert_allclose(points.min(axis=0), [1.76, 1.5, 3.26], atol=1e-6)
    np.testing.assert_allclose(points.max(axis=0), [2.74, 2.48, 4.24], atol=1e-6)


def test_diagnostic_scene_hides_technical_blocks_without_hiding_neighbors():
    scene = build_scene_geometry(source_with_blocks("barrier", "structure_void", "light", "stone"))
    points = np.concatenate([points for _, points, _ in scene.flat_groups])

    np.testing.assert_array_equal(points.min(axis=0), [3, 0, 0])
    np.testing.assert_array_equal(points.max(axis=0), [4, 1, 1])


def test_nbt_variants_keep_their_own_surfaces_and_textures(tmp_path):
    textures = tmp_path / "textures/entity/decorated_pot"
    textures.mkdir(parents=True)
    colors = ((180, 120, 60, 255), (220, 20, 30, 255), (20, 30, 220, 255))
    for name, color in zip(("decorated_pot_side", "angler_pottery_pattern", "archer_pottery_pattern"), colors):
        Image.new("RGBA", (32, 32), color).save(textures / f"{name}.png")
    Image.new("RGBA", (32, 32), (120, 120, 120, 255)).save(textures / "decorated_pot_base.png")
    source = source_with_blocks("decorated_pot")
    source.size = (7, 1, 1)
    source.present = {(x, 0, 0): 0 for x in (0, 2, 4, 6)}
    source.block_nbt = {
        (x, 0, 0): {"sherds": [f"minecraft:{name}_pottery_sherd"] * 4}
        for x, name in ((2, "angler"), (4, "archer"), (6, "angler"))
    }
    scene = build_scene_geometry(source, TextureBank(AssetContext(tmp_path)), strict=True)
    mesh = scene.meshes[0]
    centers = mesh.points[mesh.quads].mean(axis=1)
    uv = mesh.uv[mesh.quads].mean(axis=1)
    pixels = mesh.image[(mesh.image.shape[0] * (1 - uv[:, 1])).astype(int),
                        (mesh.image.shape[1] * uv[:, 0]).astype(int)]
    wall = np.isclose(centers[:, 1], .5)
    for x, color in zip((0, 2, 4, 6), (colors[0], colors[1], colors[2], colors[1])):
        selected = wall & (centers[:, 0] > x) & (centers[:, 0] < x + 1)
        assert selected.sum() == 4
        np.testing.assert_array_equal(pixels[selected], [color] * 4)
