import argparse
import re
from pathlib import Path

import numpy as np
import trimesh

from structura_core import Structure

from .legacy_input import as_structure_nbt
from .mesh import build_textured_meshes, export_parts, flat_block_groups, voxel_state
from .textures import TextureBank


def add_alpha_maps(obj_path):
    obj_text = obj_path.read_text()
    mtllib = re.search(r"^mtllib (.+)$", obj_text, re.MULTILINE)
    if not mtllib:
        return
    mtl_path = obj_path.parent / mtllib.group(1)
    mtl_text = mtl_path.read_text()
    mtl_text = re.sub(
        r"^(map_Kd (.+))$", r"\1\nmap_d \2", mtl_text, flags=re.MULTILINE,
    )
    mtl_path.write_text(mtl_text)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("src")
    parser.add_argument("output")
    args = parser.parse_args()

    src = Structure(as_structure_nbt(args.src))
    state, solid, index_names, index_props = voxel_state(src)
    if not solid.any():
        raise SystemExit("structure contains no solid blocks")

    bank = TextureBank()
    meshes, _, textured_indices, occluder = build_textured_meshes(
        src, solid, state, index_names, index_props, bank,
    )
    flat_groups = flat_block_groups(state, index_names, textured_indices, occluder)
    center = np.asarray(src.size, dtype=np.float32) / 2.0
    parts = export_parts(meshes, flat_groups, center)
    if not parts:
        raise SystemExit("structure produced no visible geometry")

    scene = trimesh.Scene()
    for name, part in parts:
        scene.add_geometry(part, node_name=name)

    out_path = Path(args.output).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    resolver = trimesh.resolvers.FilePathResolver(str(out_path.parent))
    scene.export(str(out_path), resolver=resolver, write_texture=True)
    add_alpha_maps(out_path)
    print(f"{out_path} parts={len(parts)}")


if __name__ == "__main__":
    main()
