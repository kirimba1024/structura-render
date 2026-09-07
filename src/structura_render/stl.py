import argparse
from pathlib import Path

from .export_io import atomic_write


def export_stl(parts, output):
    """Export a single oriented surface; no artificial back-face duplication."""
    import trimesh

    if not parts:
        raise ValueError("structure produced no visible geometry")
    combined = trimesh.util.concatenate([part for _, part in parts])
    # Welding removes per-face UV seams, which STL cannot represent. Coincident
    # triangles (including reverse sides of sprites) are one geometric surface.
    combined.visual = trimesh.visual.ColorVisuals()
    combined.merge_vertices()
    combined.update_faces(combined.unique_faces())
    atomic_write(output, combined.export(file_type="stl"))
    return combined


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("src")
    parser.add_argument("output")
    parser.add_argument(
        "--allow-flat-fallback", action="store_true",
        help="use coloured cubes when Minecraft assets are unavailable",
    )
    args = parser.parse_args()
    from .legacy_input import load_structure
    from .mesh import structure_export_parts
    from .textures import texture_bank_or_exit

    src = load_structure(args.src)
    parts = structure_export_parts(src, texture_bank_or_exit(args.allow_flat_fallback))
    if not parts:
        raise SystemExit("structure produced no visible geometry")

    out_path = Path(args.output).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    combined = export_stl(parts, out_path)
    print(f"{out_path} triangles={len(combined.faces)}")


if __name__ == "__main__":
    main()
