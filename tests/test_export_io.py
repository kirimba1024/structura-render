import hashlib
import json
import os
import subprocess
import sys

import numpy as np
import pytest
import trimesh
from PIL import Image

from structura_render.export_io import write_gltf, write_obj


def scene(color):
    mesh = trimesh.creation.box()
    mesh.visual = trimesh.visual.TextureVisuals(
        uv=np.zeros((len(mesh.vertices), 2)), image=Image.new("RGBA", (2, 2), color),
    )
    return trimesh.Scene(mesh)


@pytest.mark.parametrize("suffix,writer", [("gltf", write_gltf), ("obj", write_obj)])
def test_second_export_preserves_every_file_of_the_first(tmp_path, suffix, writer):
    first = writer(scene("red"), tmp_path / f"first.{suffix}")
    files = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in tmp_path.rglob("*") if p.is_file()}

    second = writer(scene("blue"), tmp_path / f"second.{suffix}")

    assert all(hashlib.sha256(p.read_bytes()).hexdigest() == digest for p, digest in files.items())
    for path, expected in [(first, (255, 0, 0)), (second, (0, 0, 255))]:
        loaded = trimesh.load(path, force="scene")
        material = next(iter(loaded.geometry.values())).visual.material
        image = material.baseColorTexture if hasattr(material, "baseColorTexture") else material.image
        assert image is not None
        assert image.convert("RGB").getpixel((0, 0)) == expected


def test_obj_materials_have_valid_alpha_map_paths(tmp_path):
    output = write_obj(scene((100, 50, 0, 127)), tmp_path / "пример with spaces.obj")
    material_name = next(line[7:] for line in output.read_text().splitlines() if line.startswith("mtllib "))
    material = tmp_path / material_name
    maps = [line.split(" ", 1)[1] for line in material.read_text().splitlines() if line.startswith(("map_Kd ", "map_d "))]
    assert len(maps) == 2 and maps[0] != maps[1]
    assert all((material.parent / name).is_file() for name in maps)
    with Image.open(material.parent / maps[1]) as opacity:
        assert opacity.mode == "L"
        assert opacity.getextrema() == (127, 127)


def test_gltf_explicitly_requests_nearest_filtering(tmp_path):
    output = write_gltf(scene("red"), tmp_path / "image.gltf")
    tree = json.loads(output.read_text())
    for texture in tree["textures"]:
        sampler = tree["samplers"][texture["sampler"]]
        assert sampler["minFilter"] == sampler["magFilter"] == 9728


@pytest.mark.parametrize("module", ["structura_render.hero", "structura_render.usdz"])
def test_image_and_usdz_imports_do_not_require_trimesh(module):
    script = """
import importlib, importlib.abc, sys
class NoTrimesh(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == 'trimesh' or fullname.startswith('trimesh.'):
            raise ModuleNotFoundError('trimesh must not be imported')
sys.meta_path.insert(0, NoTrimesh())
importlib.import_module(sys.argv[1])
importlib.import_module('structura_render.mesh')
"""
    run = subprocess.run([sys.executable, "-c", script, module], capture_output=True, text=True)
    assert run.returncode == 0, run.stderr


@pytest.mark.parametrize("module", ["hero", "gltf", "obj", "stl", "usdz"])
def test_help_works_without_optional_backends_or_assets(module, tmp_path):
    script = """
import importlib.abc, runpy, sys
class NoBackends(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'pyvista', 'vtk', 'vtkmodules', 'trimesh', 'pxr', 'amulet'}:
            raise ModuleNotFoundError('optional backend must not be imported: ' + fullname)
sys.meta_path.insert(0, NoBackends())
module = sys.argv[1]
sys.argv = [module, '--help']
runpy.run_module(module, run_name='__main__')
"""
    env = {**os.environ, "STRUCTURA_MINECRAFT_ASSETS": str(tmp_path / "missing")}
    run = subprocess.run(
        [sys.executable, "-c", script, f"structura_render.{module}"],
        env=env, capture_output=True, text=True,
    )
    assert run.returncode == 0, run.stderr
    assert "--help" in run.stdout


@pytest.mark.parametrize("writer,suffix", [(write_gltf, "gltf"), (write_obj, "obj")])
def test_failed_publication_preserves_existing_model(tmp_path, monkeypatch, writer, suffix):
    from structura_render import export_io

    output = writer(scene("red"), tmp_path / f"scene.{suffix}")
    files = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    original = export_io.atomic_write

    def interrupt(path, data):
        if path == output:
            raise OSError("interrupted before publication")
        original(path, data)

    monkeypatch.setattr(export_io, "atomic_write", interrupt)
    with pytest.raises(OSError, match="interrupted"):
        writer(scene("blue"), output)

    assert all(p.read_bytes() == data for p, data in files.items())
