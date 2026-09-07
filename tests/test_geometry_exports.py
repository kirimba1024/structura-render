import json
from types import SimpleNamespace

import numpy as np
import pytest
import trimesh
from amulet_nbt import CompoundTag, StringTag
from PIL import Image

from structura_render import block_model, textures
from structura_render.export_io import write_gltf, write_obj
from structura_render.mesh import (
    build_textured_meshes,
    structure_export_parts,
    voxel_state,
    vtk_quads,
)
from structura_render.stl import export_stl


@pytest.fixture
def assets(tmp_path, monkeypatch):
    states = tmp_path / "blockstates"
    models = tmp_path / "models/block"
    images = tmp_path / "textures/block"
    for directory in (states, models, images):
        directory.mkdir(parents=True)
    monkeypatch.setattr(block_model, "BLOCKSTATES", states)
    monkeypatch.setattr(block_model, "MODELS", models)
    monkeypatch.setattr(block_model, "_blockstate_cache", {})
    monkeypatch.setattr(block_model, "_model_cache", {})
    monkeypatch.setattr(textures, "BLOCK_TEXTURES", images)
    monkeypatch.setattr(textures, "TEXTURES", images.parent)
    monkeypatch.setattr(textures, "ASSET_DIRECTORIES", (states, models, images))
    for name, alpha in (("stone", 255), ("cutout", 255), ("translucent", 128)):
        pixels = np.full((16, 16, 4), (100, 150, 200, alpha), dtype=np.uint8)
        if name == "cutout":
            pixels[:8, :, 3] = 0
        Image.fromarray(pixels).save(images / f"{name}.png")
        (states / f"{name}.json").write_text(json.dumps({
            "variants": {"": {"model": f"minecraft:block/{name}"}},
        }))
        (models / f"{name}.json").write_text(json.dumps({
            "textures": {"all": f"minecraft:block/{name}"},
            "elements": [{
                "from": [0, 0, 0], "to": [16, 16, 16],
                "faces": {direction: {"texture": "#all", "cullface": direction}
                          for direction in block_model.DIRECTIONS},
            }],
        }))
    (states / "hidden.json").write_text(json.dumps({
        "variants": {"": {"model": "minecraft:block/hidden"}},
    }))
    (models / "hidden.json").write_text('{"elements": []}')
    return textures.TextureBank()


def structure(*names):
    palette = [f"minecraft:{name}" for name in names]
    return SimpleNamespace(
        size=(2 * len(names) - 1, 1, 1), palette=palette,
        palette_raw=[CompoundTag({"Name": StringTag(name)}) for name in palette],
        present={(index * 2, 0, 0): index for index in range(len(names))},
        block_nbt={}, entities=[],
    )


def meshes_for(src, bank):
    state, solid, names, props = voxel_state(src)
    return build_textured_meshes(src, solid, state, names, props, bank)[0]


@pytest.mark.parametrize("textured", [False, True])
def test_exported_cube_is_closed_with_outward_faces(tmp_path, assets, textured):
    if not textured:
        # Exercise the explicit flat fallback as well as JSON model geometry.
        assets._read = lambda _name: None
    parts = structure_export_parts(structure("stone"), assets)
    output = tmp_path / "cube.stl"
    export_stl(parts, output)
    result = trimesh.load(output, force="mesh")

    assert len(result.faces) == 12
    assert result.is_watertight
    assert result.is_winding_consistent
    assert result.volume == pytest.approx(1.0)
    assert np.all(np.einsum("ij,ij->i", result.face_normals, result.triangles_center) > 0)


def test_top_face_winding_retains_texture_orientation(assets):
    mesh, _ = meshes_for(structure("stone"), assets)[0]
    top = next(quad for quad in vtk_quads(mesh.faces) if np.all(mesh.points[quad, 1] == 1))
    points = mesh.points[top]
    uv = mesh.active_texture_coordinates[top]
    normal = np.cross(points[1] - points[0], points[2] - points[0])
    np.testing.assert_allclose(normal, [0, 1, 0])
    for axis, component in ((0, 0), (2, 1)):
        low = uv[points[:, axis] == 0, component]
        high = uv[points[:, axis] == 1, component]
        assert np.all(high > low.max())


def test_mixed_scene_exports_distinct_alpha_modes(tmp_path, assets):
    parts = structure_export_parts(structure("stone", "cutout", "translucent"), assets)
    scene = trimesh.Scene()
    for name, part in parts:
        scene.add_geometry(part, node_name=name, geom_name=name)
    output = tmp_path / "mixed.gltf"
    write_gltf(scene, output)
    document = json.loads(output.read_text())

    materials = {material.get("alphaMode", "OPAQUE"): material
                 for material in document["materials"]}
    assert set(materials) == {"OPAQUE", "MASK", "BLEND"}
    assert materials["MASK"]["alphaCutoff"] == pytest.approx(.5)
    assert "alphaCutoff" not in materials["BLEND"]
    assert all(material["doubleSided"] for material in materials.values())
    assert sum(len(part.faces) for _, part in parts) == 36
    restored = trimesh.load(output, force="scene")
    blend = next(part for part in restored.geometry.values()
                 if part.visual.material.alphaMode == "BLEND")
    assert 128 in np.unique(np.asarray(blend.visual.material.baseColorTexture)[..., 3])


def test_empty_model_is_hidden_without_losing_visible_neighbors(assets):
    parts = structure_export_parts(structure("hidden", "stone", "barrier"), assets)
    assert sum(len(part.faces) for _, part in parts) == 12
    assert structure_export_parts(structure("hidden"), assets) == []


@pytest.mark.parametrize("model", [
    {"parent": "minecraft:block/missing_parent"},
    {"elements": [{"from": [0, 0, 0], "to": [16, 16, 16],
                   "faces": {"up": {"texture": "#missing_reference"}}}]},
])
def test_unresolved_model_does_not_silently_hide_a_block(assets, model):
    (block_model.MODELS / "stone.json").write_text(json.dumps(model))
    assert block_model.block_elements("minecraft:stone", {}) is None
    parts = structure_export_parts(structure("stone"), assets)
    assert sum(len(part.faces) for _, part in parts) == 12


def test_flat_fallback_keeps_transparency_and_two_sided_materials(tmp_path, assets):
    assets._read = lambda _name: None
    parts = structure_export_parts(structure("stone", "glass"), assets)
    output = write_gltf(trimesh.Scene([part for _, part in parts]), tmp_path / "flat.gltf")
    materials = json.loads(output.read_text())["materials"]

    assert {material.get("alphaMode", "OPAQUE") for material in materials} == {"OPAQUE", "BLEND"}
    assert all(material["doubleSided"] for material in materials)
    glass = next(material for material in materials if material["alphaMode"] == "BLEND")
    assert 0 < glass["pbrMetallicRoughness"]["baseColorFactor"][3] < 1


def test_obj_keeps_texture_brightness_and_flat_opacity(tmp_path, assets):
    textured = structure_export_parts(structure("stone"), assets)
    assets._read = lambda _name: None
    flat = structure_export_parts(structure("glass"), assets)
    output = write_obj(trimesh.Scene([part for _, part in textured + flat]), tmp_path / "model.obj")
    library = next(line[7:] for line in output.read_text().splitlines() if line.startswith("mtllib "))
    material = (tmp_path / library).read_text()

    assert "Kd 1.00000000 1.00000000 1.00000000" in material
    assert "d 0.35294118" in material  # 90/255, the flat glass material
