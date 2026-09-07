"""Convert Minecraft structures into images and 3D files."""

import argparse
import importlib

FORMATS = {
    "projections": "projections", "png": "hero", "gltf": "gltf",
    "glb": "gltf", "obj": "obj", "stl": "stl", "usdz": "usdz", "doctor": "doctor", "examples": "examples",
}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("format", choices=FORMATS)
    parser.add_argument("arguments", nargs=argparse.REMAINDER, help="source, output and format options")
    args = parser.parse_args(argv)
    module = FORMATS[args.format]
    try:
        importlib.import_module(f".{module}", __package__).main(args.arguments)
    except ModuleNotFoundError as error:
        if error.name and error.name.split(".")[0] in {"pyvista", "vtk", "vtkmodules", "trimesh", "networkx", "pxr"}:
            parser.error(f"{args.format} needs: pip install 'structura-render[{module}]'")
        raise
    except (ValueError, OSError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
