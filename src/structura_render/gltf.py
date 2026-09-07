import argparse
from pathlib import Path

from .export_io import write_gltf


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
    write_gltf(scene, out_path)
    print(f"{out_path} parts={len(parts)}")


if __name__ == "__main__":
    main()
