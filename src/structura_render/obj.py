import argparse
import re
from pathlib import Path

from .export_io import write_obj


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
    parser.add_argument(
        "--allow-flat-fallback", action="store_true",
        help="use coloured cubes when Minecraft assets are unavailable",
    )
    args = parser.parse_args()
    import trimesh

    from .legacy_input import load_structure
    from .mesh import structure_export_parts
    from .textures import texture_bank_or_exit

    src = load_structure(args.src)
    parts = structure_export_parts(src, texture_bank_or_exit(args.allow_flat_fallback))
    if not parts:
        raise SystemExit("structure produced no visible geometry")

    scene = trimesh.Scene()
    for name, part in parts:
        scene.add_geometry(part, node_name=name)

    out_path = Path(args.output).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    write_obj(scene, out_path)
    print(f"{out_path} parts={len(parts)}")


if __name__ == "__main__":
    main()
