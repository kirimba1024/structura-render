"""Perspective and orthographic images from the shared Minecraft geometry."""

import argparse
import math

import numpy as np
from PIL import Image
from structura_core.litematic import DEFAULT_MAX_BLOCKS

from .camera import framing_distance, orthographic_scale
from .export_io import write_image
from .geometry import DEFAULT_MAX_ATLAS_SIZE, DEFAULT_MAX_VOXELS
from .projections import DEFAULT_MAX_PIXELS, _check_pixels


class PlottingUnavailableError(RuntimeError):
    pass


def render_hero(source, output=None, *, window=1600, azimuth=35.0, elevation=35.0,
                zoom=1.0, color_mode="family", no_textures=False, texture_bank=None,
                transparent=False, orthographic=False, max_pixels=DEFAULT_MAX_PIXELS,
                max_voxels=DEFAULT_MAX_VOXELS, max_atlas_size=DEFAULT_MAX_ATLAS_SIZE):
    """Return a Pillow image from a path or Structure; optionally save it atomically."""
    if isinstance(window, bool) or not isinstance(window, int) or window <= 0:
        raise ValueError("window must be a positive integer")
    _check_pixels((window, window), max_pixels)
    if not all(math.isfinite(v) for v in (azimuth, elevation, zoom)) or zoom <= 0:
        raise ValueError("camera angles must be finite and zoom must be finite and positive")
    if color_mode not in {"family", "block"}:
        raise ValueError("color_mode must be 'family' or 'block'")
    import pyvista as pv

    from .legacy_input import load_structure
    from .mesh import build_textured_meshes, flat_rgba, voxel_state
    from .textures import MISSING_ASSETS_MESSAGE, TextureBank

    if not pv.system_supports_plotting():
        raise PlottingUnavailableError("no supported plotting backend")
    src = load_structure(source)
    sx, sy, sz = src.size
    state, solid, index_names, index_props = voxel_state(src, max_voxels=max_voxels)

    textured_meshes, flat_entities, textured_indices = [], [], set()
    if not no_textures:
        bank = texture_bank if texture_bank is not None else TextureBank()
        if not bank.available():
            raise ValueError(MISSING_ASSETS_MESSAGE)
        textured_meshes, flat_entities, textured_indices, _ = build_textured_meshes(
            src, solid, state, index_names, index_props, bank, max_atlas_size=max_atlas_size,
        )
    if not solid.any() and not textured_meshes and not flat_entities:
        raise ValueError("structure produced no visible geometry")

    colors = np.zeros((sx, sy, sz, 4), dtype=np.uint8)
    flat_solid = np.zeros_like(solid)
    for index, name in index_names.items():
        if index in textured_indices:
            continue
        mask = state == index
        flat_solid |= mask
        colors[mask] = flat_rgba(name, color_mode)

    if not flat_solid.any() and not textured_meshes and not flat_entities:
        raise ValueError("structure produced no visible geometry")

    plotter = pv.Plotter(off_screen=True, window_size=(window, window))
    try:
        plotter.set_background("white")
        plotter.enable_depth_peeling(number_of_peels=12, occlusion_ratio=0.0)
        if flat_solid.any():
            grid = pv.ImageData(dimensions=(sx + 1, sy + 1, sz + 1))
            grid.cell_data["solid"] = flat_solid.ravel(order="F")
            grid.cell_data["color"] = colors.reshape(-1, 4, order="F")
            plotter.add_mesh(
                grid.threshold(0.5, scalars="solid"),
                scalars="color", rgba=True, show_edges=False,
            )
        for mesh, texture in textured_meshes:
            plotter.add_mesh(mesh, texture=texture)
        for points, faces, color, alpha in flat_entities:
            mesh = pv.PolyData(points, faces)
            mesh.cell_data["color"] = np.tile((*color, alpha), (mesh.n_cells, 1)).astype(np.uint8)
            plotter.add_mesh(mesh, scalars="color", rgba=True, show_edges=False)

        bounds = np.asarray(plotter.bounds).reshape(3, 2)
        center = bounds.mean(axis=1)
        radius = framing_distance(bounds[:, 1] - bounds[:, 0], plotter.camera.view_angle)
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
            plotter.camera.parallel_scale = orthographic_scale(bounds[:, 1] - bounds[:, 0])
        plotter.camera.zoom(zoom)
        plotter.reset_camera_clipping_range()
        pixels = plotter.screenshot(transparent_background=transparent, return_img=True)
        image = Image.fromarray(pixels)
        if output is not None:
            write_image(image, output)
        return image
    finally:
        plotter.close()


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
    args = parser.parse_args(argv)
    from .legacy_input import load_structure

    try:
        src = load_structure(args.src, region=args.region, max_blocks=args.max_blocks)
        render_hero(src, args.output, window=args.window, azimuth=args.azimuth,
                    elevation=args.elevation, zoom=args.zoom, color_mode=args.color_mode,
                    no_textures=args.no_textures, transparent=args.transparent,
                    orthographic=args.orthographic, max_pixels=args.max_pixels,
                    max_voxels=args.max_voxels, max_atlas_size=args.max_atlas_size)
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
