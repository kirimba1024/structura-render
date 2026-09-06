from pxr import Sdf, Usd, UsdShade

import numpy as np

from structura_render.usdz import build_material, face_normal, unique_sided_quads


def test_pixel_atlas_never_blends_with_transparent_neighbour_tiles():
    stage = Usd.Stage.CreateInMemory()
    build_material(stage, Sdf.Path("/Model"), "atlas.png")
    texture = UsdShade.Shader.Get(stage, "/Model/AtlasMaterial/DiffuseTexture")

    assert texture.GetInput("minFilter").Get() == "nearest"
    assert texture.GetInput("magFilter").Get() == "nearest"


def test_coincident_faces_are_deduplicated_without_moving_their_edges():
    points = np.asarray([
        (0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0),
        (0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0),
        (0, 1, 0), (1, 1, 0), (1, 0, 0), (0, 0, 0),
    ], dtype=float)
    quads = unique_sided_quads(points, [
        (0, 1, 2, 3), (4, 5, 6, 7), (8, 9, 10, 11),
    ])

    assert len(quads) == 2
    assert np.dot(face_normal(points, quads[0]), face_normal(points, quads[1])) < 0
    assert set(map(tuple, points)) == {
        (0.0, 0.0, 0.0), (1.0, 0.0, 0.0),
        (1.0, 1.0, 0.0), (0.0, 1.0, 0.0),
    }
