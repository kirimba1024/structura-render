#!/usr/bin/env python3
"""Render one perspective PNG using the shared mesh builder."""

import argparse
from pathlib import Path

import numpy as np
import pyvista as pv

from structura_structures import Structure

from .mesh import build_textured_meshes, flat_rgba, voxel_state
from .textures import TextureBank


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("src")
    parser.add_argument("output")
    parser.add_argument("--color-mode", choices=("family", "block"), default="family")
    parser.add_argument("--window", type=int, default=1600)
    parser.add_argument("--azimuth", type=float, default=35.0)
    parser.add_argument("--elevation", type=float, default=35.0)
    parser.add_argument("--zoom", type=float, default=1.0)
    parser.add_argument("--no-textures", action="store_true")
    parser.add_argument(
        "--allow-skip", action="store_true",
        help="return successfully without a PNG when no plotting backend is available",
    )
    args = parser.parse_args()
    if args.window <= 0 or args.zoom <= 0:
        parser.error("--window and --zoom must be positive")
    if not pv.system_supports_plotting():
        message = "hero render skipped: no supported plotting backend"
        if args.allow_skip:
            print(message)
            return
        raise SystemExit(message)

    src = Structure(args.src)
    sx, sy, sz = src.size
    state, solid, index_names, index_props = voxel_state(src)

    textured_meshes, flat_entities, textured_indices = [], [], set()
    bank = TextureBank()
    if not args.no_textures and bank.available():
        textured_meshes, flat_entities, textured_indices, _ = build_textured_meshes(
            src, solid, state, index_names, index_props, bank,
        )

    colors = np.zeros((sx, sy, sz, 4), dtype=np.uint8)
    flat_solid = np.zeros_like(solid)
    for index, name in index_names.items():
        if index in textured_indices:
            continue
        mask = state == index
        flat_solid |= mask
        colors[mask] = flat_rgba(name, args.color_mode)

    plotter = pv.Plotter(off_screen=True, window_size=(args.window, args.window))
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

    center = np.array([sx, sy, sz]) / 2
    radius = float(np.linalg.norm([sx, sy, sz])) * 1.1
    azimuth, elevation = np.radians((args.azimuth, args.elevation))
    offset = radius * np.array([
        np.cos(elevation) * np.sin(azimuth),
        np.sin(elevation),
        np.cos(elevation) * np.cos(azimuth),
    ])
    plotter.camera.up = (0, 1, 0)
    plotter.camera.focal_point = tuple(center)
    plotter.camera.position = tuple(center + offset)
    plotter.camera.zoom(args.zoom)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    plotter.screenshot(str(output))
    plotter.close()
    print(f"{args.output} size={src.size} solid={int(solid.sum())} textured={len(textured_indices)}")


if __name__ == "__main__":
    main()
