#!/usr/bin/env python3
"""Export a Structure NBT to textured USDZ, viewable natively via macOS
Quick Look (press space on the file in Finder) -- reuses render_hero.py's
own textured-mesh builder so the same blocks/shapes are covered."""
import argparse
import os
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image
from structura_core.litematic import DEFAULT_MAX_BLOCKS

from .camera import framing_distance
from .geometry import DEFAULT_MAX_ATLAS_SIZE, DEFAULT_MAX_VOXELS

# Match the image renderer's default orientation, fitting the camera's aperture.
CAMERA_AZIMUTH = 35.0
CAMERA_ELEVATION = 35.0
CAMERA_FOCAL_LENGTH = 45.0
CAMERA_HORIZONTAL_APERTURE = 36.0
CAMERA_VERTICAL_APERTURE = 24.0


def add_framing_camera(stage, root, size):
    from pxr import Gf, UsdGeom

    vertical_fov = np.degrees(2 * np.arctan(CAMERA_VERTICAL_APERTURE / (2 * CAMERA_FOCAL_LENGTH)))
    radius = framing_distance(size, vertical_fov, CAMERA_HORIZONTAL_APERTURE / CAMERA_VERTICAL_APERTURE)
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
    from pxr import Gf, Sdf, UsdShade

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
    from pxr import Gf, UsdGeom, UsdShade

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
    mesh.CreateFaceVertexCountsAttr(counts)
    mesh.CreateFaceVertexIndicesAttr(indices)
    mesh.CreateSubdivisionSchemeAttr("none")
    mesh.CreateDoubleSidedAttr(True)
    UsdShade.MaterialBindingAPI.Apply(mesh.GetPrim()).Bind(material)


def build_material(stage, root, texture_path, name="AtlasMaterial", *, alpha_mode="MASK"):
    from pxr import Gf, Sdf, UsdShade

    if alpha_mode not in {"OPAQUE", "MASK", "BLEND"}:
        raise ValueError(f"unknown alpha mode: {alpha_mode}")
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
    texture.CreateInput("minFilter", Sdf.ValueTypeNames.Token).Set("nearest")
    texture.CreateInput("magFilter", Sdf.ValueTypeNames.Token).Set("nearest")
    texture.CreateInput("sourceColorSpace", Sdf.ValueTypeNames.Token).Set("sRGB")
    texture.CreateOutput("rgb", Sdf.ValueTypeNames.Float3)
    texture.CreateOutput("a", Sdf.ValueTypeNames.Float)

    shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).ConnectToSource(
        texture.ConnectableAPI(), "rgb",
    )
    opacity = shader.CreateInput("opacity", Sdf.ValueTypeNames.Float)
    if alpha_mode == "OPAQUE":
        opacity.Set(1.0)
    else:
        opacity.ConnectToSource(texture.ConnectableAPI(), "a")
    shader.CreateInput("opacityThreshold", Sdf.ValueTypeNames.Float).Set(
        0.5 if alpha_mode == "MASK" else 0.0,
    )
    return material


def face_normal(points, quad):
    a, b, c = (np.asarray(points[i], dtype=np.float64) for i in quad[:3])
    normal = np.cross(b - a, c - a)
    length = np.linalg.norm(normal)
    return normal / length if length > 0 else np.array([0.0, 1.0, 0.0])


def unique_sided_quads(points, quads):
    groups = {}
    rounded = np.round(points, 4)
    for quad in quads:
        key = frozenset(tuple(rounded[i]) for i in quad)
        groups.setdefault(key, []).append(quad)

    result = []
    for group in groups.values():
        reference = face_normal(points, group[0])
        sided = {}
        for quad in group:
            side = 1 if np.dot(face_normal(points, quad), reference) >= 0 else -1
            sided.setdefault(side, quad)
        result.extend(sided.values())
        if len(sided) == 1:
            result.append(group[0][::-1])
    return result


def add_mesh(stage, root, name, points, faces, uv, material, center):
    from pxr import Gf, Sdf, UsdGeom, UsdShade

    mesh = UsdGeom.Mesh.Define(stage, root.AppendPath(name))
    points = np.asarray(points, dtype=np.float64)
    quads = [tuple(int(v) for v in faces[i + 1:i + 5]) for i in range(0, len(faces), 5)]
    # A geometric coincidence is not enough: overlays may use another texture.
    # Double-sided materials handle reverse visibility without reverse copies.
    distinct = {}
    for quad in quads:
        key = frozenset((tuple(points[i]), tuple(uv[i])) for i in quad)
        distinct.setdefault(key, quad)
    quads = list(distinct.values())

    counts = []
    indices = []
    normals = []
    for quad in quads:
        counts.append(4)
        indices.extend(quad)
        normal = face_normal(points, quad)
        normals.append(Gf.Vec3f(*normal))
    mesh.CreatePointsAttr([
        Gf.Vec3f(float(p[0] - center[0]), float(p[1] - center[1]), float(p[2] - center[2]))
        for p in points
    ])
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


def package_usdz(source, output):
    """Publish a completed archive without damaging an existing destination."""
    from pxr import Sdf, UsdUtils

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent, prefix=".structura-usdz-") as directory:
        prepared = Path(directory) / "model.usdz"
        if not UsdUtils.CreateNewUsdzPackage(Sdf.AssetPath(str(source)), str(prepared)):
            raise RuntimeError("USDZ packaging failed")
        os.replace(prepared, output)
    return output


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("src")
    parser.add_argument("output")
    parser.add_argument("--region", help="one named Litematic region")
    parser.add_argument("--max-blocks", type=int, default=DEFAULT_MAX_BLOCKS)
    parser.add_argument("--max-voxels", type=int, default=DEFAULT_MAX_VOXELS)
    parser.add_argument("--max-atlas-size", type=int, default=DEFAULT_MAX_ATLAS_SIZE, help="maximum texture atlas side in pixels")
    parser.add_argument(
        "--allow-flat-fallback", action="store_true",
        help="use coloured cubes when Minecraft assets are unavailable",
    )
    args = parser.parse_args(argv)
    from pxr import Sdf, Usd, UsdGeom

    from .legacy_input import load_structure
    from .mesh import (
        build_textured_geometry,
        flat_rgba,
        mask_surface,
        material_groups,
        upscale_atlas,
        voxel_state,
    )
    from .textures import texture_bank_or_exit

    src = load_structure(args.src, region=args.region, max_blocks=args.max_blocks)
    state, solid, index_names, index_props = voxel_state(src, max_voxels=args.max_voxels)

    bank = texture_bank_or_exit(args.allow_flat_fallback)
    meshes, flat_entities, textured_indices, occluder = build_textured_geometry(
        src, solid, state, index_names, index_props, bank, max_atlas_size=args.max_atlas_size,
    )
    if not solid.any() and not meshes and not flat_entities:
        raise SystemExit("structure produced no visible geometry")

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

        for mesh_index, mesh_obj in enumerate(meshes):
            texture_path = tmp / f"atlas{mesh_index}.png"
            atlas_image = upscale_atlas(Image.fromarray(mesh_obj.image))
            atlas_image.save(texture_path)
            for mode, points, quads, uv in material_groups(mesh_obj):
                name = f"Blocks{mesh_index}_{mode}"
                material = build_material(
                    stage, root, texture_path.name, name=f"{name}Material", alpha_mode=mode,
                )
                faces = np.column_stack((np.full(len(quads), 4), quads)).ravel()
                add_mesh(stage, root, name, points, faces, uv, material, center)

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

        if not meshes and not flat_entities and not flat_point_count:
            raise ValueError("structure produced no visible geometry")
        stage.GetRootLayer().Save()

        out_path = Path(args.output).resolve()
        try:
            package_usdz(usda_path, out_path)
        except RuntimeError as error:
            raise SystemExit(str(error)) from error

    total_points = (
        sum(len(m.points) for m in meshes)
        + sum(len(p) for p, *_ in flat_entities)
        + flat_point_count
    )
    print(f"{args.output} points={total_points} source_entities={len(src.entities)}")


if __name__ == "__main__":
    main()
