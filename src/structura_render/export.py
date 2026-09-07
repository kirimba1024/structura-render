"""Export a structure through the same geometry and writers as the CLI."""

import argparse
from importlib import import_module
from pathlib import Path

from structura_core.limits import DEFAULT_MAX_BLOCKS

from .geometry import DEFAULT_MAX_ATLAS_SIZE, DEFAULT_MAX_VOXELS

FORMATS = {".glb": "gltf", ".gltf": "gltf", ".obj": "obj", ".stl": "stl", ".usdz": "usdz"}


def export_structure(source, output, *, texture_bank=None, region=None,
                     allow_flat_fallback=False, max_blocks=DEFAULT_MAX_BLOCKS,
                     max_voxels=DEFAULT_MAX_VOXELS, max_atlas_size=DEFAULT_MAX_ATLAS_SIZE):
    """Write GLB/glTF/OBJ/STL/USDZ from a path or Structure; return its absolute Path."""
    output = Path(output).expanduser().resolve()
    format_name = FORMATS.get(output.suffix.lower())
    if format_name is None:
        raise ValueError("output must end in .glb, .gltf, .obj, .stl or .usdz")
    from .legacy_input import load_structure
    from .textures import MISSING_ASSETS_MESSAGE, TextureBank

    try:
        if format_name == "usdz":
            import_module("pxr.Usd")
        else:
            import trimesh
        src = load_structure(source, region=region, max_blocks=max_blocks)
        bank = texture_bank if texture_bank is not None else TextureBank()
        if not bank.available() and not allow_flat_fallback:
            raise ValueError(MISSING_ASSETS_MESSAGE)
        if format_name == "usdz":
            from .usdz import export_usdz

            return export_usdz(src, output, bank, max_voxels=max_voxels, max_atlas_size=max_atlas_size)
        from .mesh import structure_export_parts

        parts = structure_export_parts(src, bank, max_voxels=max_voxels, max_atlas_size=max_atlas_size)
        if not parts:
            raise ValueError("structure produced no visible geometry")
        if format_name == "stl":
            from .stl import export_stl

            export_stl(parts, output)
        else:
            from .export_io import write_gltf, write_obj

            scene = trimesh.Scene()
            for name, part in parts:
                scene.add_geometry(part, node_name=name)
            writer = write_gltf if format_name == "gltf" else write_obj
            writer(scene, output)
    except ModuleNotFoundError as error:
        if error.name and error.name.split(".")[0] in {"trimesh", "networkx", "pxr"}:
            raise ModuleNotFoundError(
                f"{format_name} export needs: pip install 'structura-render[{format_name}]'",
                name=error.name,
            ) from error
        raise
    return output


def export_cli(format_name, argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("src")
    parser.add_argument("output")
    parser.add_argument("--region", help="one named Litematic region")
    parser.add_argument("--max-blocks", type=int, default=DEFAULT_MAX_BLOCKS)
    parser.add_argument("--max-voxels", type=int, default=DEFAULT_MAX_VOXELS)
    parser.add_argument("--max-atlas-size", type=int, default=DEFAULT_MAX_ATLAS_SIZE, help="maximum texture atlas side in pixels")
    parser.add_argument("--allow-flat-fallback", action="store_true", help="use coloured cubes when Minecraft assets are unavailable")
    args = parser.parse_args(argv)
    if FORMATS.get(Path(args.output).suffix.lower()) != format_name:
        parser.error(f"output extension must match {format_name}")
    try:
        output = export_structure(
            args.src, args.output, region=args.region, allow_flat_fallback=args.allow_flat_fallback,
            max_blocks=args.max_blocks, max_voxels=args.max_voxels, max_atlas_size=args.max_atlas_size,
        )
    except (ValueError, OSError, RuntimeError) as error:
        parser.error(str(error))
    except ModuleNotFoundError as error:
        if error.name and error.name.split(".")[0] in {"trimesh", "networkx", "pxr"}:
            parser.error(str(error))
        raise
    print(output)
