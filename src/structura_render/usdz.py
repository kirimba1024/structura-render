#!/usr/bin/env python3
"""Export a Structure NBT to textured USDZ, viewable natively via macOS
Quick Look (press space on the file in Finder) -- reuses render_hero.py's
own textured-mesh builder so the same blocks/shapes are covered."""
import argparse
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image
from pxr import Gf, Sdf, Usd, UsdGeom, UsdShade, UsdUtils

from structura_core import Structure

from .legacy_input import as_structure_nbt
from .mesh import build_textured_meshes, flat_rgba, mask_surface, upscale_atlas, voxel_state
from .textures import TextureBank

GROUND_LEVEL_COLOR = (1.0, 0.35, 0.65)
GROUND_LEVEL_OPACITY = 0.07
GROUND_LEVEL_LIFT = 0.04
GROUND_LEVEL_MARGIN = 6.0


def ground_level_mesh(size_x, size_z, ground_y):
    y = float(ground_y) + 1.0 - GROUND_LEVEL_LIFT
    x0, z0 = -GROUND_LEVEL_MARGIN, -GROUND_LEVEL_MARGIN
    x1, z1 = float(size_x) + GROUND_LEVEL_MARGIN, float(size_z) + GROUND_LEVEL_MARGIN
    points = [(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)]
    return points, [[0, 1, 2, 3]]

# Same 35/35 degree three-quarter angle and radius*1.1 fit hero.py's own
# PyVista camera uses (proven to look right across every hero render so
# far) -- reused here so a USDZ viewer's initial framing matches instead
# of defaulting to sitting at the origin with no back-off distance.
CAMERA_AZIMUTH = 35.0
CAMERA_ELEVATION = 35.0
CAMERA_FOCAL_LENGTH = 45.0
CAMERA_HORIZONTAL_APERTURE = 36.0
CAMERA_VERTICAL_APERTURE = 24.0


def add_framing_camera(stage, root, size):
    radius = float(np.linalg.norm(np.asarray(size, dtype=np.float64))) * 1.1
    azimuth, elevation = np.radians((CAMERA_AZIMUTH, CAMERA_ELEVATION))
    direction = np.array([
        np.cos(elevation) * np.sin(azimuth),
        np.sin(elevation),
        np.cos(elevation) * np.cos(azimuth),
    ])
    eye = radius * direction
    camera = UsdGeom.Camera.Define(stage, root.AppendPath("Camera"))
    camera.CreateFocalLengthAttr(CAMERA_FOCAL_LENGTH)
    camera.CreateHorizontalApertureAttr(CAMERA_HORIZONTAL_APERTURE)
    camera.CreateVerticalApertureAttr(CAMERA_VERTICAL_APERTURE)
    camera.CreateClippingRangeAttr(Gf.Vec2f(0.1, max(radius * 4.0, 10.0)))
    view = Gf.Matrix4d().SetLookAt(Gf.Vec3d(*eye), Gf.Vec3d(0, 0, 0), Gf.Vec3d(0, 1, 0))
    camera.AddTransformOp().Set(view.GetInverse())
    return camera


def build_flat_material(stage, root, name, color, opacity):
    material = UsdShade.Material.Define(stage, root.AppendPath(name))
    shader = UsdShade.Shader.Define(stage, material.GetPath().AppendPath("PBRShader"))
    shader.CreateIdAttr("UsdPreviewSurface")
    shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(1.0)
    shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.0)
    shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*color))
    shader.CreateInput("opacity", Sdf.ValueTypeNames.Float).Set(opacity)
    material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")
    return material


def add_flat_mesh(stage, root, name, points, faces, material, center):
    if not points:
        return
    mesh = UsdGeom.Mesh.Define(stage, root.AppendPath(name))
    mesh.CreatePointsAttr([
        Gf.Vec3f(float(p[0] - center[0]), float(p[1] - center[1]), float(p[2] - center[2]))
        for p in points
    ])
    counts = []
    indices = []
    for quad in faces:
        counts.append(4)
        indices.extend(quad)
        counts.append(4)
        indices.extend(quad[::-1])
    mesh.CreateFaceVertexCountsAttr(counts)
    mesh.CreateFaceVertexIndicesAttr(indices)
    mesh.CreateSubdivisionSchemeAttr("none")
    mesh.CreateDoubleSidedAttr(True)
    UsdShade.MaterialBindingAPI.Apply(mesh.GetPrim()).Bind(material)


def build_material(stage, root, texture_path, name="AtlasMaterial"):
    material = UsdShade.Material.Define(stage, root.AppendPath(name))
    shader = UsdShade.Shader.Define(stage, material.GetPath().AppendPath("PBRShader"))
    shader.CreateIdAttr("UsdPreviewSurface")
    shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(1.0)
    shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.0)
    shader.CreateInput("useSpecularWorkflow", Sdf.ValueTypeNames.Int).Set(1)
    shader.CreateInput("specularColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(0.0, 0.0, 0.0))
    material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")

    st_reader = UsdShade.Shader.Define(stage, material.GetPath().AppendPath("stReader"))
    st_reader.CreateIdAttr("UsdPrimvarReader_float2")
    st_reader.CreateInput("varname", Sdf.ValueTypeNames.String).Set("st")
    st_reader.CreateOutput("result", Sdf.ValueTypeNames.Float2)

    texture = UsdShade.Shader.Define(stage, material.GetPath().AppendPath("DiffuseTexture"))
    texture.CreateIdAttr("UsdUVTexture")
    texture.CreateInput("file", Sdf.ValueTypeNames.Asset).Set(texture_path)
    texture.CreateInput("st", Sdf.ValueTypeNames.Float2).ConnectToSource(
        st_reader.ConnectableAPI(), "result",
    )
    texture.CreateInput("wrapS", Sdf.ValueTypeNames.Token).Set("clamp")
    texture.CreateInput("wrapT", Sdf.ValueTypeNames.Token).Set("clamp")
    texture.CreateInput("sourceColorSpace", Sdf.ValueTypeNames.Token).Set("sRGB")
    texture.CreateOutput("rgb", Sdf.ValueTypeNames.Float3)
    texture.CreateOutput("a", Sdf.ValueTypeNames.Float)

    shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).ConnectToSource(
        texture.ConnectableAPI(), "rgb",
    )
    opacity = shader.CreateInput("opacity", Sdf.ValueTypeNames.Float)
    opacity.ConnectToSource(texture.ConnectableAPI(), "a")
    shader.CreateInput("opacityThreshold", Sdf.ValueTypeNames.Float).Set(0.5)
    return material


def face_normal(points, quad):
    a, b, c = (np.asarray(points[i], dtype=np.float64) for i in quad[:3])
    normal = np.cross(b - a, c - a)
    length = np.linalg.norm(normal)
    return normal / length if length > 0 else np.array([0.0, 1.0, 0.0])


def add_mesh(stage, root, name, points, faces, uv, material, center):
    mesh = UsdGeom.Mesh.Define(stage, root.AppendPath(name))
    mesh.CreatePointsAttr([
        Gf.Vec3f(float(p[0] - center[0]), float(p[1] - center[1]), float(p[2] - center[2]))
        for p in points
    ])
    quads = [tuple(int(v) for v in faces[i + 1:i + 5]) for i in range(0, len(faces), 5)]
    rounded = np.round(np.asarray(points, dtype=np.float64), 4)
    quad_keys = [frozenset(tuple(rounded[i]) for i in quad) for quad in quads]
    coverage = {}
    for key in quad_keys:
        coverage[key] = coverage.get(key, 0) + 1

    counts = []
    indices = []
    normals = []
    for quad, key in zip(quads, quad_keys):
        counts.append(4)
        indices.extend(quad)
        normal = face_normal(points, quad)
        normals.append(Gf.Vec3f(*normal))
        if coverage[key] < 2:
            counts.append(4)
            indices.extend(quad[::-1])
            normals.append(Gf.Vec3f(*(-normal)))
    mesh.CreateFaceVertexCountsAttr(counts)
    mesh.CreateFaceVertexIndicesAttr(indices)
    mesh.CreateNormalsAttr(normals)
    mesh.SetNormalsInterpolation(UsdGeom.Tokens.uniform)
    mesh.CreateSubdivisionSchemeAttr("none")
    mesh.CreateDoubleSidedAttr(True)
    primvars = UsdGeom.PrimvarsAPI(mesh)
    st = primvars.CreatePrimvar(
        "st", Sdf.ValueTypeNames.TexCoord2fArray, UsdGeom.Tokens.vertex,
    )
    st.Set([Gf.Vec2f(float(c[0]), float(c[1])) for c in uv])
    UsdShade.MaterialBindingAPI.Apply(mesh.GetPrim()).Bind(material)
    return mesh


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("src")
    parser.add_argument("output")
    parser.add_argument(
        "--ground-y", type=float,
        help="Y of the topmost ground block (the structure's own "
             "coordinates, matching the base_y saved by envelope.py/"
             "terrain_pod.py) -- draws a faint translucent plane at its "
             "top face, where a player's feet would stand, for visually "
             "confirming detect_base_y instead of guessing from a render",
    )
    args = parser.parse_args()

    src = Structure(as_structure_nbt(args.src))
    state, solid, index_names, index_props = voxel_state(src)

    bank = TextureBank()
    meshes, flat_entities, textured_indices, occluder = build_textured_meshes(
        src, solid, state, index_names, index_props, bank,
    )
    if not solid.any():
        raise SystemExit("structure contains no solid blocks")

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        usda_path = tmp / "model.usda"
        stage = Usd.Stage.CreateNew(str(usda_path))
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
        stage.SetMetadata("metersPerUnit", 1.0)
        root = Sdf.Path("/Model")
        UsdGeom.Xform.Define(stage, root)
        stage.SetDefaultPrim(stage.GetPrimAtPath(root))
        center = np.asarray(src.size, dtype=np.float32) / 2.0
        add_framing_camera(stage, root, src.size)

        if meshes:
            mesh_obj, texture = meshes[0]
            texture_path = tmp / "atlas.png"
            atlas_image = upscale_atlas(Image.fromarray(texture.to_array()))
            atlas_image.save(texture_path)
            material = build_material(stage, root, "atlas.png")
            add_mesh(
                stage, root, "Blocks",
                mesh_obj.points, mesh_obj.faces,
                mesh_obj.active_texture_coordinates, material, center,
            )

        for i, (points, faces, color, alpha) in enumerate(flat_entities):
            quads = [tuple(int(v) for v in faces[j + 1:j + 5]) for j in range(0, len(faces), 5)]
            entity_material = build_flat_material(
                stage, root, f"Entity{i}Material",
                tuple(c / 255 for c in color), alpha / 255,
            )
            add_flat_mesh(stage, root, f"Entity{i}", points.tolist(), quads, entity_material, center)

        flat_solid = np.zeros_like(solid)
        for index in index_names:
            if index not in textured_indices:
                flat_solid |= state == index
        flat_occluder = occluder | flat_solid

        flat_point_count = 0
        for index, name in index_names.items():
            if index in textured_indices:
                continue
            mask = state == index
            points, faces = mask_surface(mask, flat_occluder)
            if not points:
                continue
            flat_point_count += len(points)
            r, g, b, a = flat_rgba(name)
            flat_material = build_flat_material(
                stage, root, f"Flat{index}Material", (r / 255, g / 255, b / 255), a / 255,
            )
            add_flat_mesh(stage, root, f"Flat{index}", points, faces, flat_material, center)

        if args.ground_y is not None:
            points, faces = ground_level_mesh(src.size[0], src.size[2], args.ground_y)
            ground_material = build_flat_material(
                stage, root, "GroundLevelMaterial", GROUND_LEVEL_COLOR, GROUND_LEVEL_OPACITY,
            )
            add_flat_mesh(stage, root, "GroundLevel", points, faces, ground_material, center)

        stage.GetRootLayer().Save()

        out_path = Path(args.output).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        ok = UsdUtils.CreateNewUsdzPackage(Sdf.AssetPath(str(usda_path)), str(out_path))
        if not ok:
            raise SystemExit("USDZ packaging failed")

    total_points = (
        sum(len(m.points) for m, _ in meshes)
        + sum(len(p) for p, *_ in flat_entities)
        + flat_point_count
    )
    print(f"{args.output} points={total_points} entities={len(flat_entities)}")


if __name__ == "__main__":
    main()
