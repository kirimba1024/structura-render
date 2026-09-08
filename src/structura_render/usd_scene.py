import numpy as np
from PIL import Image

from .atlas import upscale_atlas
from .camera import framing_distance
from .geometry import material_groups

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


def _quad_mesh(stage, root, name, points, quads, material, center):
    from pxr import Gf, UsdGeom, UsdShade

    mesh = UsdGeom.Mesh.Define(stage, root.AppendPath(name))
    mesh.CreatePointsAttr([Gf.Vec3f(*map(float, point)) for point in np.asarray(points) - center])
    mesh.CreateFaceVertexCountsAttr([4] * len(quads))
    mesh.CreateFaceVertexIndicesAttr(np.asarray(quads, dtype=np.int32).ravel().tolist())
    mesh.CreateSubdivisionSchemeAttr("none")
    mesh.CreateDoubleSidedAttr(True)
    UsdShade.MaterialBindingAPI.Apply(mesh.GetPrim()).Bind(material)
    return mesh


def add_flat_mesh(stage, root, name, points, faces, material, center):
    if len(points):
        return _quad_mesh(stage, root, name, points, faces, material, center)


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


def add_mesh(stage, root, name, points, faces, uv, material, center):
    from pxr import Gf, Sdf, UsdGeom

    points = np.asarray(points, dtype=np.float64)
    quads = [tuple(int(v) for v in faces[i + 1:i + 5]) for i in range(0, len(faces), 5)]
    distinct = {}
    for quad in quads:
        key = frozenset((tuple(points[i]), tuple(uv[i])) for i in quad)
        distinct.setdefault(key, quad)
    quads = list(distinct.values())

    mesh = _quad_mesh(stage, root, name, points, quads, material, center)
    mesh.CreateNormalsAttr([Gf.Vec3f(*face_normal(points, quad)) for quad in quads])
    mesh.SetNormalsInterpolation(UsdGeom.Tokens.uniform)
    primvars = UsdGeom.PrimvarsAPI(mesh)
    st = primvars.CreatePrimvar(
        "st", Sdf.ValueTypeNames.TexCoord2fArray, UsdGeom.Tokens.vertex,
    )
    st.Set([Gf.Vec2f(float(c[0]), float(c[1])) for c in uv])
    return mesh


def build_stage(path, geometry, size):
    from pxr import Sdf, Usd, UsdGeom

    stage = Usd.Stage.CreateNew(str(path))
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    root = Sdf.Path("/Model")
    UsdGeom.Xform.Define(stage, root)
    stage.SetDefaultPrim(stage.GetPrimAtPath(root))
    center = np.asarray(size, dtype=np.float32) / 2.0
    add_framing_camera(stage, root, size)
    for index, mesh in enumerate(geometry.meshes):
        texture_path = path.parent / f"atlas{index}.png"
        upscale_atlas(Image.fromarray(mesh.image)).save(texture_path)
        for mode, points, quads, uv in material_groups(mesh):
            name = f"Blocks{index}_{mode}"
            material = build_material(stage, root, texture_path.name, name=f"{name}Material", alpha_mode=mode)
            faces = np.column_stack((np.full(len(quads), 4), quads)).ravel()
            add_mesh(stage, root, name, points, faces, uv, material, center)
    for index, (color, points, quads) in enumerate(geometry.flat_groups):
        name = f"Flat{index}"
        material = build_flat_material(stage, root, f"{name}Material", tuple(c / 255 for c in color[:3]), color[3] / 255)
        add_flat_mesh(stage, root, name, points, quads, material, center)
    return stage
