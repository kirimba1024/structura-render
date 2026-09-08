import os
import tempfile
from pathlib import Path

from .geometry import DEFAULT_MAX_ATLAS_SIZE, DEFAULT_MAX_VOXELS
from .mesh import build_scene_geometry
from .usd_scene import (
    CAMERA_AZIMUTH as CAMERA_AZIMUTH,
    CAMERA_ELEVATION as CAMERA_ELEVATION,
    CAMERA_FOCAL_LENGTH as CAMERA_FOCAL_LENGTH,
    CAMERA_HORIZONTAL_APERTURE as CAMERA_HORIZONTAL_APERTURE,
    CAMERA_VERTICAL_APERTURE as CAMERA_VERTICAL_APERTURE,
    add_flat_mesh as add_flat_mesh,
    add_framing_camera as add_framing_camera,
    add_mesh as add_mesh,
    build_flat_material as build_flat_material,
    build_material as build_material,
    build_stage,
    face_normal as face_normal,
)


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


def publish_usd(stage, directory, output):
    from pxr import Sdf

    from .export_io import _ResourceWriter, atomic_write

    output = Path(output)
    writer = _ResourceWriter(output)
    for prim in stage.Traverse():
        for attribute in prim.GetAttributes():
            if attribute.GetTypeName() != Sdf.ValueTypeNames.Asset:
                continue
            asset = attribute.Get()
            if asset and asset.path:
                source = directory / asset.path
                name = writer.add(source.name, source.read_bytes())
                attribute.Set(Sdf.AssetPath(f"{writer.directory.name}/{name}"))
    prepared = directory / ("export" + output.suffix.lower())
    if not stage.GetRootLayer().Export(str(prepared)):
        raise RuntimeError("USD serialization failed")
    atomic_write(output, prepared.read_bytes())
    return output


def export_usdz(src, output, bank, *, max_voxels=DEFAULT_MAX_VOXELS, max_atlas_size=DEFAULT_MAX_ATLAS_SIZE, strict=False):
    geometry = build_scene_geometry(src, bank, max_voxels=max_voxels, max_atlas_size=max_atlas_size, strict=strict)
    if not geometry:
        raise ValueError("structure produced no visible geometry")
    with tempfile.TemporaryDirectory() as directory:
        directory = Path(directory)
        source = directory / "model.usda"
        stage = build_stage(source, geometry, src.size)
        stage.GetRootLayer().Save()
        if Path(output).suffix.lower() == ".usdz":
            return package_usdz(source, output)
        return publish_usd(stage, directory, output)


def main(argv=None):
    from .export import export_cli

    export_cli("usdz", argv)


if __name__ == "__main__":
    main()
