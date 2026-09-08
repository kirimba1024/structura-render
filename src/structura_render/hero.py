"""Perspective and orthographic images from the shared Minecraft geometry."""

import argparse
import math
import warnings
from os import PathLike
from typing import Literal, Optional, Union

import numpy as np
from PIL import Image
from structura_core import Structure
from structura_core.limits import DEFAULT_MAX_BLOCKS

from .camera import framing_distance, orthographic_scale
from .diagnostics import RenderWarning
from .export_io import write_image
from .geometry import DEFAULT_MAX_ATLAS_SIZE, DEFAULT_MAX_VOXELS
from .projection_grid import DEFAULT_MAX_PIXELS, check_pixels
from .textures import TextureBank


class PlottingUnavailableError(RuntimeError):
    pass


def render_hero(source: Union[str, PathLike[str], Structure], output: Optional[Union[str, PathLike[str]]] = None, *,
                window: int = 1600, azimuth: float = 35.0, elevation: float = 35.0,
                zoom: float = 1.0, color_mode: Literal["family", "block"] = "family",
                no_textures: bool = False, texture_bank: Optional[TextureBank] = None,
                transparent: bool = False, orthographic: bool = False, max_pixels: int = DEFAULT_MAX_PIXELS,
                max_voxels: int = DEFAULT_MAX_VOXELS, max_atlas_size: int = DEFAULT_MAX_ATLAS_SIZE,
                strict: bool = False) -> Image.Image:
    """Return a Pillow image from a path or Structure; optionally save it atomically."""
    if isinstance(window, bool) or not isinstance(window, int) or window <= 0:
        raise ValueError("window must be a positive integer")
    check_pixels((window, window), max_pixels)
    if not all(math.isfinite(v) for v in (azimuth, elevation, zoom)) or zoom <= 0:
        raise ValueError("camera angles must be finite and zoom must be finite and positive")
    if color_mode not in {"family", "block"}:
        raise ValueError("color_mode must be 'family' or 'block'")
    import pyvista as pv

    from .legacy_input import load_structure
    from .mesh import build_scene_geometry
    from .textures import MISSING_ASSETS_MESSAGE

    if not pv.system_supports_plotting():
        raise PlottingUnavailableError("no supported plotting backend")
    src = load_structure(source, strict=strict)
    bank = None
    if not no_textures:
        bank = texture_bank if texture_bank is not None else TextureBank()
        if not bank.available():
            raise ValueError(MISSING_ASSETS_MESSAGE)
    geometry = build_scene_geometry(src, bank, color_mode=color_mode, max_voxels=max_voxels,
                                    max_atlas_size=max_atlas_size, strict=strict)
    if not geometry:
        raise ValueError("structure produced no visible geometry")

    plotter = pv.Plotter(off_screen=True, window_size=(window, window))
    try:
        plotter.set_background("white")
        plotter.enable_depth_peeling(number_of_peels=12, occlusion_ratio=0.0)
        _add_geometry(plotter, geometry)
        _frame_camera(plotter, azimuth, elevation, zoom, orthographic)
        pixels = plotter.screenshot(transparent_background=transparent, return_img=True)
        image = Image.fromarray(pixels)
        if output is not None:
            write_image(image, output)
        return image
    finally:
        plotter.close()


def _add_geometry(plotter, geometry):
    import pyvista as pv

    for item in geometry.meshes:
        mesh, texture = item.to_pyvista()
        plotter.add_mesh(mesh, texture=texture)
    for color, points, quads in geometry.flat_groups:
        faces = np.column_stack((np.full(len(quads), 4), quads)).ravel()
        mesh = pv.PolyData(np.asarray(points, dtype=np.float32), faces)
        mesh.cell_data["color"] = np.tile(color, (mesh.n_cells, 1)).astype(np.uint8)
        plotter.add_mesh(mesh, scalars="color", rgba=True, show_edges=False)


def _frame_camera(plotter, azimuth, elevation, zoom, orthographic):
    bounds = np.asarray(plotter.bounds).reshape(3, 2)
    center = bounds.mean(axis=1)
    size = bounds[:, 1] - bounds[:, 0]
    radius = framing_distance(size, plotter.camera.view_angle)
    azimuth, elevation = np.radians((azimuth, elevation))
    offset = radius * np.array([
        np.cos(elevation) * np.sin(azimuth),
        np.sin(elevation),
        np.cos(elevation) * np.cos(azimuth),
    ])
    plotter.camera.up = (0, 0, 1) if abs(np.cos(elevation)) < 1e-8 else (0, 1, 0)
    plotter.camera.focal_point = tuple(center)
    plotter.camera.position = tuple(center + offset)
    if orthographic:
        plotter.enable_parallel_projection()
        plotter.camera.parallel_scale = orthographic_scale(size)
    plotter.camera.zoom(zoom)
    plotter.reset_camera_clipping_range()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("src")
    parser.add_argument("output")
    parser.add_argument("--region", help="one named Litematic region")
    parser.add_argument("--max-blocks", type=int, default=DEFAULT_MAX_BLOCKS)
    parser.add_argument("--color-mode", choices=("family", "block"), default="family")
    parser.add_argument("--window", type=int, default=1600)
    parser.add_argument("--azimuth", type=float, default=35.0)
    parser.add_argument("--elevation", type=float, default=35.0)
    parser.add_argument("--zoom", type=float, default=1.0)
    parser.add_argument("--no-textures", action="store_true")
    parser.add_argument("--transparent", action="store_true", help="save an RGBA image")
    parser.add_argument("--orthographic", action="store_true", help="parallel projection without perspective")
    parser.add_argument("--max-pixels", type=int, default=DEFAULT_MAX_PIXELS)
    parser.add_argument("--max-voxels", type=int, default=DEFAULT_MAX_VOXELS)
    parser.add_argument("--max-atlas-size", type=int, default=DEFAULT_MAX_ATLAS_SIZE, help="maximum texture atlas side in pixels")
    parser.add_argument("--allow-skip", action="store_true", help="succeed without an image if plotting is unavailable")
    parser.add_argument("--strict", action="store_true", help="reject reported approximations before writing")
    args = parser.parse_args(argv)
    from .legacy_input import load_structure

    try:
        src = load_structure(args.src, region=args.region, max_blocks=args.max_blocks, strict=args.strict)
        with warnings.catch_warnings(record=True) as notices:
            warnings.simplefilter("always", RenderWarning)
            render_hero(src, args.output, window=args.window, azimuth=args.azimuth,
                        elevation=args.elevation, zoom=args.zoom, color_mode=args.color_mode,
                        no_textures=args.no_textures, transparent=args.transparent,
                        orthographic=args.orthographic, max_pixels=args.max_pixels,
                        max_voxels=args.max_voxels, max_atlas_size=args.max_atlas_size, strict=args.strict)
        for notice in notices:
            parser._print_message(f"warning: {notice.message}\n")
    except PlottingUnavailableError as error:
        if args.allow_skip:
            print(f"hero render skipped: {error}")
            return
        parser.error(str(error))
    except (ValueError, OSError) as error:
        parser.error(str(error))
    print(args.output)


if __name__ == "__main__":
    main()
