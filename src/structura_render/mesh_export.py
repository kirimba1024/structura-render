"""Adapt shared geometry to trimesh without importing it for PNG or USDZ."""

import numpy as np
import trimesh
from PIL import Image

from .mesh import material_groups, triangulate_quads, upscale_atlas


def export_parts(meshes, flat_groups, center):
    parts = []
    for mesh_index, (mesh, texture) in enumerate(meshes):
        image = upscale_atlas(Image.fromarray(texture.to_array()))
        for mode, points, quads, uv in material_groups(mesh, texture):
            options = {"alphaCutoff": 0.5} if mode == "MASK" else {}
            material = trimesh.visual.material.PBRMaterial(
                name=f"Atlas{mesh_index}_{mode}", baseColorTexture=image,
                baseColorFactor=(1.0, 1.0, 1.0, 1.0),
                metallicFactor=0.0, roughnessFactor=1.0, alphaMode=mode,
                doubleSided=True, **options,
            )
            visual = trimesh.visual.TextureVisuals(uv=uv, material=material)
            part = trimesh.Trimesh(
                vertices=np.asarray(points, dtype=np.float32) - center,
                faces=triangulate_quads(quads), visual=visual, process=False,
            )
            parts.append((f"Blocks{mesh_index}_{mode}", part))

    for index, (color, points, faces) in enumerate(flat_groups):
        material = trimesh.visual.material.PBRMaterial(
            name=f"Flat{index}", baseColorFactor=np.asarray(color, dtype=np.uint8),
            metallicFactor=0.0, roughnessFactor=1.0,
            alphaMode="BLEND" if color[3] < 255 else "OPAQUE", doubleSided=True,
        )
        part = trimesh.Trimesh(
            vertices=np.asarray(points, dtype=np.float32) - center,
            faces=triangulate_quads(faces),
            visual=trimesh.visual.TextureVisuals(material=material), process=False,
        )
        parts.append((f"Flat{index}", part))
    return parts
