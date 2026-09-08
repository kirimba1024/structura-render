from pxr import Sdf, Usd, UsdGeom, UsdShade

import numpy as np
import pytest

from structura_render.usdz import (
    add_flat_mesh, add_mesh, build_flat_material, build_material, package_usdz,
)


def test_pixel_atlas_never_blends_with_transparent_neighbour_tiles():
    stage = Usd.Stage.CreateInMemory()
    build_material(stage, Sdf.Path("/Model"), "atlas.png")
    texture = UsdShade.Shader.Get(stage, "/Model/AtlasMaterial/DiffuseTexture")

    assert texture.GetInput("minFilter").Get() == "nearest"
    assert texture.GetInput("magFilter").Get() == "nearest"


def test_coincident_faces_are_deduplicated_without_moving_their_edges():
    stage = Usd.Stage.CreateInMemory()
    root = Sdf.Path("/Model")
    material = build_material(stage, root, "atlas.png")
    points = np.asarray([
        (0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0),
        (0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0),
        (0, 1, 0), (1, 1, 0), (1, 0, 0), (0, 0, 0),
    ], dtype=float)
    faces = np.column_stack((np.full(3, 4), np.arange(12).reshape(-1, 4))).ravel()
    uv = points[:, :2]
    mesh = add_mesh(stage, root, "Quad", points, faces, uv, material, (0, 0, 0))

    assert mesh.GetFaceVertexCountsAttr().Get() == [4]
    assert mesh.GetDoubleSidedAttr().Get()
    assert set(map(tuple, mesh.GetPointsAttr().Get())) == {
        (0.0, 0.0, 0.0), (1.0, 0.0, 0.0),
        (1.0, 1.0, 0.0), (0.0, 1.0, 0.0),
    }


def test_flat_mesh_uses_double_sided_material_without_duplicate_geometry():
    stage = Usd.Stage.CreateInMemory()
    root = Sdf.Path("/Model")
    material = build_flat_material(stage, root, "Flat", (1, 1, 1), 1)
    add_flat_mesh(
        stage, root, "Quad",
        [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)],
        [(0, 1, 2, 3)], material, (0, 0, 0),
    )
    mesh = UsdGeom.Mesh.Get(stage, "/Model/Quad")

    assert mesh.GetFaceVertexCountsAttr().Get() == [4]
    assert mesh.GetDoubleSidedAttr().Get()


def test_translucent_material_does_not_apply_cutout_threshold():
    stage = Usd.Stage.CreateInMemory()
    root = Sdf.Path("/Model")
    build_material(stage, root, "atlas.png", name="Water", alpha_mode="BLEND")
    build_material(stage, root, "atlas.png", name="Leaves", alpha_mode="MASK")
    water = UsdShade.Shader.Get(stage, "/Model/Water/PBRShader")
    leaves = UsdShade.Shader.Get(stage, "/Model/Leaves/PBRShader")

    assert water.GetInput("opacityThreshold").Get() == 0.0
    assert water.GetInput("opacity").HasConnectedSource()
    assert leaves.GetInput("opacityThreshold").Get() == 0.5


def test_coincident_faces_with_different_uvs_are_preserved():
    stage = Usd.Stage.CreateInMemory()
    root = Sdf.Path("/Model")
    material = build_material(stage, root, "atlas.png")
    points = np.tile([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)], (3, 1))
    uv = np.asarray([(0, 0), (.5, 0), (.5, .5), (0, .5)] * 3)
    uv[4:8] += .5
    faces = np.asarray([4, 0, 1, 2, 3, 4, 4, 5, 6, 7, 4, 11, 10, 9, 8])

    result = add_mesh(stage, root, "Layers", points, faces, uv, material, (0, 0, 0))

    assert result.GetFaceVertexCountsAttr().Get() == [4, 4]
    assert result.GetDoubleSidedAttr().Get()


def test_failed_packaging_preserves_existing_usdz(tmp_path, monkeypatch):
    from pathlib import Path
    from pxr import UsdUtils

    output = tmp_path / "saved.usdz"
    output.write_bytes(b"existing model")

    def fail(_source, destination):
        Path(destination).write_bytes(b"incomplete archive")
        return False

    monkeypatch.setattr(UsdUtils, "CreateNewUsdzPackage", fail)
    with pytest.raises(RuntimeError, match="packaging failed"):
        package_usdz(tmp_path / "source.usda", output)

    assert output.read_bytes() == b"existing model"
    assert list(tmp_path.iterdir()) == [output]
