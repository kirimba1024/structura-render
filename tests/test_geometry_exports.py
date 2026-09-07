import json
import os
import subprocess
import sys
from types import SimpleNamespace

import numpy as np
import pytest
import trimesh
from amulet_nbt import CompoundTag, StringTag
from PIL import Image
from structura_core import Structure, export_litematic, save_structure
from structura_core.export_schematic import export_schematic

from structura_render import block_model, textures
from structura_render import AssetContext, export_structure
from structura_render.export_io import write_gltf, write_obj
from structura_render.mesh import (
    build_textured_geometry,
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
    monkeypatch.setenv("STRUCTURA_MINECRAFT_ASSETS", str(tmp_path))
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


@pytest.mark.parametrize('format_name', ['glb', 'gltf'])
@pytest.mark.skipif(not os.environ.get('STRUCTURA_GLTF_VALIDATOR'), reason='Khronos validator runs in interoperability CI')
def test_khronos_validator_accepts_exported_materials(tmp_path, assets, format_name):
    src = structure('stone', 'cutout', 'translucent')
    src.data_version = 3955
    source = tmp_path / 'source.nbt'
    save_structure(src, source, src.size)
    output = export_structure(source, tmp_path / f'model.{format_name}', texture_bank=assets, strict=True)
    result = subprocess.run([
        os.environ.get('STRUCTURA_NODE', 'node'), os.environ['STRUCTURA_GLTF_VALIDATOR'], str(output),
    ], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert report['issues']['numErrors'] == report['issues']['numWarnings'] == 0


@pytest.mark.parametrize('format_name', ['glb', 'gltf', 'obj', 'stl', 'usdz'])
def test_strict_export_preserves_file_and_replays_cached_notices(tmp_path, assets, format_name):
    from structura_render import RenderWarning

    src = structure('stone')
    src.data_version = 3955
    source = tmp_path / 'source.nbt'
    save_structure(src, source, src.size)
    (assets.context.root / 'textures/block/stone.png').unlink()
    output = tmp_path / f'existing.{format_name}'
    output.write_bytes(b'previous')
    for _ in range(2):
        with pytest.raises(ValueError, match='missing texture.*stone'):
            export_structure(source, output, texture_bank=assets, strict=True)
        assert output.read_bytes() == b'previous'
    with pytest.warns(RenderWarning) as notices:
        export_structure(source, output, texture_bank=assets)
    assert len(notices) == 1 and str(notices[0].message).count('minecraft:block/stone') == 1


def test_diagnostics_do_not_cross_resource_contexts(tmp_path, assets):
    from structura_render import RenderWarning
    from structura_render.textures import TextureBank

    src = structure('stone')
    src.data_version = 3955
    source = tmp_path / 'source.nbt'
    save_structure(src, source, src.size)
    missing = TextureBank(AssetContext(tmp_path / 'missing'))
    with pytest.warns(RenderWarning, match='approximate shape'):
        export_structure(source, tmp_path / 'fallback.glb', texture_bank=missing, allow_flat_fallback=True)
    export_structure(source, tmp_path / 'complete.glb', texture_bank=assets, strict=True)


@pytest.mark.parametrize('kind', ['unknown_entity', 'painting'])
def test_entity_approximation_is_reported_before_output(tmp_path, assets, kind):
    from amulet_nbt import DoubleTag, IntTag, ListTag

    src = structure('stone')
    src.data_version = 3955
    src.entities = [CompoundTag({
        'pos': ListTag([DoubleTag(0)] * 3), 'blockPos': ListTag([IntTag(0)] * 3),
        'nbt': CompoundTag({'id': StringTag(f'minecraft:{kind}'), 'variant': StringTag('minecraft:unavailable')}),
    })]
    source = tmp_path / 'source.nbt'
    save_structure(src, source, src.size)
    output = tmp_path / 'existing.glb'
    output.write_bytes(b'previous')
    with pytest.raises(ValueError, match=kind):
        export_structure(source, output, texture_bank=assets, strict=True)
    assert output.read_bytes() == b'previous'


def test_strict_hero_rejects_before_creating_plotter(tmp_path, assets, monkeypatch):
    import pyvista as pv
    from structura_render import render_hero

    src = structure('stone')
    src.data_version = 3955
    source = tmp_path / 'source.nbt'
    save_structure(src, source, src.size)
    (assets.context.root / 'textures/block/stone.png').unlink()
    monkeypatch.setattr(pv, 'system_supports_plotting', lambda: True)
    monkeypatch.setattr(pv, 'Plotter', lambda *args, **kwargs: pytest.fail('plotter created before strict validation'))
    output = tmp_path / 'existing.png'
    output.write_bytes(b'previous')
    with pytest.raises(ValueError, match='missing texture'):
        render_hero(source, output, texture_bank=assets, strict=True)
    assert output.read_bytes() == b'previous'


@pytest.mark.parametrize('format_name', ['glb', 'gltf', 'obj', 'stl', 'usdz'])
def test_python_export_matches_cli_and_preserves_source(tmp_path, assets, format_name):
    src = structure('stone', 'cutout', 'translucent')
    src.data_version = 3955
    source_path = tmp_path / 'source.nbt'
    save_structure(src, source_path, src.size)
    source = Structure(source_path)
    before = source._root.to_snbt()
    api_output = export_structure(source, tmp_path / f'api.{format_name}', texture_bank=assets)
    path_output = export_structure(source_path, tmp_path / f'path.{format_name}', texture_bank=assets)
    cli_output = tmp_path / f'cli.{format_name}'
    result = subprocess.run([sys.executable, '-m', 'structura_render', format_name, str(source_path), str(cli_output)],
                            capture_output=True, text=True, check=True,
                            env={**os.environ, 'STRUCTURA_MINECRAFT_ASSETS': str(assets.context.root)})
    assert str(cli_output) in result.stdout
    assert api_output == (tmp_path / f'api.{format_name}').resolve()
    assert source._root.to_snbt() == before
    if format_name == 'usdz':
        from pxr import Usd, UsdGeom

        def geometry(path):
            stage = Usd.Stage.Open(str(path))
            meshes = [UsdGeom.Mesh(prim) for prim in stage.Traverse() if prim.GetTypeName() == 'Mesh']
            return [(list(mesh.GetPointsAttr().Get()), list(mesh.GetFaceVertexIndicesAttr().Get())) for mesh in meshes]

        assert geometry(api_output) == geometry(path_output) == geometry(cli_output)
    else:
        scenes = [trimesh.load(path, force='scene') for path in (api_output, path_output, cli_output)]
        assert [sum(len(mesh.faces) for mesh in scene.geometry.values()) for scene in scenes] == [36] * 3
        for scene in scenes[1:]:
            np.testing.assert_array_equal(scenes[0].bounds, scene.bounds)


@pytest.mark.parametrize('format_name', ['glb', 'gltf', 'obj', 'stl', 'usdz'])
def test_python_export_atlas_failure_preserves_existing_file(tmp_path, assets, format_name):
    src = structure('stone')
    src.data_version = 3955
    source_path = tmp_path / 'source.nbt'
    save_structure(src, source_path, src.size)
    output = tmp_path / f'existing.{format_name}'
    output.write_bytes(b'previous output')
    with pytest.raises(ValueError, match='atlas'):
        export_structure(Structure(source_path), output, texture_bank=assets, max_atlas_size=8)
    assert output.read_bytes() == b'previous output'


def test_python_export_invalid_output_never_loads_source(tmp_path):
    with pytest.raises(ValueError, match='output must end'):
        export_structure('missing.nbt', tmp_path / 'output.png')


def test_python_export_missing_resources_raises_valueerror_not_systemexit(tmp_path, assets):
    src = structure('stone')
    src.data_version = 3955
    path = tmp_path / 'source.nbt'
    save_structure(src, path, src.size)
    bank = textures.TextureBank(AssetContext(tmp_path / 'missing'))
    with pytest.raises(ValueError, match='Minecraft assets'):
        export_structure(path, tmp_path / 'out.glb', texture_bank=bank)
    assert export_structure(path, tmp_path / 'out.glb', texture_bank=bank, allow_flat_fallback=True).is_file()


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
    (assets.context.root / "models/block/stone.json").write_text(json.dumps(model))
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


def test_numpy_geometry_and_compatibility_adapter_keep_identical_buffers(assets):
    src = structure("stone", "cutout", "translucent")
    state, solid, names, props = voxel_state(src)
    geometry = build_textured_geometry(src, solid, state, names, props, assets)[0][0]
    mesh, texture = build_textured_meshes(src, solid, state, names, props, assets)[0][0]
    np.testing.assert_array_equal(geometry.points, mesh.points)
    np.testing.assert_array_equal(geometry.quads, vtk_quads(mesh.faces))
    np.testing.assert_array_equal(geometry.uv, mesh.active_texture_coordinates)
    np.testing.assert_array_equal(geometry.alpha_modes, mesh.cell_data["alpha_mode"])
    np.testing.assert_array_equal(geometry.image, texture.to_array())


@pytest.mark.parametrize("output_format", ["glb", "gltf", "obj", "stl", "usdz"])
@pytest.mark.parametrize("input_format", ["litematic", "schem"])
def test_native_cli_export_works_with_plotting_imports_blocked(tmp_path, assets, output_format, input_format):
    src = structure("stone", "cutout", "translucent")
    src.data_version = 3955
    nbt = tmp_path / "input.nbt"
    save_structure(src, nbt, src.size)
    export = export_litematic if input_format == "litematic" else export_schematic
    source = export(Structure(nbt), tmp_path / f"input.{input_format}")
    output = tmp_path / f"model.{output_format}"
    script = """
import importlib.abc, runpy, sys
class NoPlotting(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'pyvista', 'vtk', 'vtkmodules', 'amulet'}:
            raise AssertionError('file export imported a plotting backend: ' + fullname)
sys.meta_path.insert(0, NoPlotting())
sys.argv = ['structura-render', *sys.argv[1:]]
runpy.run_module('structura_render', run_name='__main__')
"""
    env = {**os.environ, "STRUCTURA_MINECRAFT_ASSETS": str(tmp_path)}
    result = subprocess.run(
        [sys.executable, "-c", script, output_format, str(source), str(output)],
        env=env, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert output.stat().st_size > 100
    if output_format == "usdz":
        from pxr import Usd

        stage = Usd.Stage.Open(str(output))
        assert sum(prim.GetTypeName() == "Mesh" for prim in stage.Traverse()) == 3
    else:
        scene = trimesh.load(output, force="scene")
        assert sum(len(part.faces) for part in scene.geometry.values()) == 36


def test_volume_guard_rejects_distant_regions_before_numpy_allocation():
    src = structure("stone")
    src.size = (1_000_000_000, 1, 1)
    with pytest.raises(ValueError, match="max_voxels"):
        voxel_state(src)
