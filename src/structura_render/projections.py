"""Render six colored diagnostic projections of a Structure NBT."""

import argparse
import math
from os import PathLike
from pathlib import Path
from typing import Iterable, Literal, Optional, Tuple, Union

import numpy as np
from PIL import Image, ImageDraw
from structura_core import Structure
from structura_core.limits import DEFAULT_MAX_BLOCKS

from .block_colours import (
    COLORS as COLORS,
    block_color as block_color,
    family as family,
)
from .export_io import write_image
from .legacy_input import load_structure
from .overlays import ProjectionOverlays, draw_overlays, load_overlays
from .projection_grid import (
    DEFAULT_MAX_PIXELS as DEFAULT_MAX_PIXELS,
    VIEWS as VIEWS,
    check_pixels as _check_pixels,
    depth_range as _depth_range,
    frontmost as frontmost,
    orient as orient,
    projection_cells as projection_cells,
    projection_size as _projection_size,
)


def render_view(states, palette, view, color_mode):
    axis, reverse = VIEWS[view]
    visible = orient(frontmost(states, axis, reverse), view)
    canvas = np.full((*visible.shape, 3), 246.0)

    for index in np.unique(visible[visible >= 0]):
        canvas[visible == index] = block_color(palette[int(index)], color_mode)
    return np.clip(canvas, 0, 255).astype(np.uint8)


def panel(image, title, scale):
    rendered = Image.fromarray(image).resize(
        (image.shape[1] * scale, image.shape[0] * scale), Image.Resampling.NEAREST,
    )
    panel_image = Image.new("RGB", (rendered.width + 16, rendered.height + 38), "white")
    panel_image.paste(rendered, (8, 30))
    ImageDraw.Draw(panel_image).text((8, 8), title.upper(), fill=(24, 27, 32))
    return panel_image


def _layout(sizes, caption=None):
    if not sizes:
        raise ValueError("at least one projection is required")
    columns = min(3, len(sizes))
    row_count = math.ceil(len(sizes) / columns)
    widths = [
        max(sizes[i][0] for i in range(col, len(sizes), columns))
        for col in range(columns)
    ]
    rows = [
        max(size[1] for size in sizes[row * columns:(row + 1) * columns])
        for row in range(row_count)
    ]
    return widths, rows, (
        sum(widths) + 18 * (columns + 1),
        sum(rows) + 18 * (row_count + 1) + (22 if caption else 0),
    )


def compose(panels, output=None, caption=None):
    widths, rows, size = _layout([p.size for p in panels], caption)
    columns, gap = len(widths), 18
    caption_height = 22 if caption else 0
    canvas = Image.new("RGB", size, (238, 240, 243))
    for index, item in enumerate(panels):
        row, col = divmod(index, columns)
        x = gap + sum(widths[:col]) + gap * col
        y = gap + sum(rows[:row]) + gap * row + caption_height
        canvas.paste(item, (x, y))

    draw = ImageDraw.Draw(canvas)
    if caption:
        draw.text((gap, 4), caption, fill=(60, 64, 72))
    if output is not None:
        write_image(canvas, output)
    return canvas


def render_projection(source: Union[str, PathLike[str], Structure], *,
                      view: Literal["top", "bottom", "north", "south", "west", "east"] = "top",
                      scale: int = 16, color_mode: Literal["family", "block"] = "family",
                      transparent: bool = False, max_pixels: int = DEFAULT_MAX_PIXELS,
                      overlays: Optional[ProjectionOverlays] = None,
                      depth: Optional[Tuple[int, int]] = None) -> Image.Image:
    """Return one unframed Pillow image from a path or in-memory Structure."""
    if color_mode not in {"family", "block"}:
        raise ValueError("color_mode must be 'family' or 'block'")
    src = load_structure(source)
    return _projection_image(src, view=view, scale=scale, color_mode=color_mode, transparent=transparent,
                             max_pixels=max_pixels, overlays=overlays, depth=depth)


def _projection_image(src, *, view, scale, color_mode, transparent, max_pixels, overlays, depth):
    size = _projection_size(src.size, view, scale)
    _check_pixels(size, max_pixels)
    visible = projection_cells(src, view, depth)
    channels = 4 if transparent else 3
    background = (0, 0, 0, 0) if transparent else (246, 246, 246)
    canvas = np.full((*visible.shape, channels), background, dtype=np.uint8)
    colors = np.asarray([block_color(name, color_mode) for name in src.palette], dtype=np.uint8)
    present = visible >= 0
    if present.any():
        canvas[present, :3] = colors[visible[present]]
        if transparent:
            canvas[present, 3] = 255
    if overlays is not None:
        canvas = draw_overlays(canvas, overlays, view, src.size, depth=depth)
    return Image.fromarray(canvas).resize(size, Image.Resampling.NEAREST)


def render_projections(source: Union[str, PathLike[str], Structure], output: Optional[Union[str, PathLike[str]]] = None, *,
                       views: Iterable[Literal["top", "bottom", "north", "south", "west", "east"]] = tuple(VIEWS),
                       scale: int = 16, color_mode: Literal["family", "block"] = "family",
                       max_pixels: int = DEFAULT_MAX_PIXELS, overlays: Optional[ProjectionOverlays] = None,
                       depth: Optional[Tuple[int, int]] = None) -> Image.Image:
    """Return a sheet of named projections; optionally save it atomically."""
    if color_mode not in {"family", "block"}:
        raise ValueError("color_mode must be 'family' or 'block'")
    src = load_structure(source)
    views = tuple(views)
    sizes = [_projection_size(src.size, view, scale) for view in views]
    for view in views:
        _depth_range(depth, src.size, VIEWS[view][0])
    _, _, size = _layout([(w + 16, h + 38) for w, h in sizes])
    _check_pixels(size, max_pixels)
    panels = [
        panel(np.asarray(_projection_image(src, view=view, scale=1, color_mode=color_mode, transparent=False,
                                            max_pixels=max_pixels, overlays=overlays, depth=depth)), view, scale)
        for view in views
    ]
    return compose(panels, output)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("src")
    parser.add_argument("output")
    parser.add_argument("--region", help="one named Litematic region")
    parser.add_argument("--max-blocks", type=int, default=DEFAULT_MAX_BLOCKS)
    parser.add_argument("--max-pixels", type=int, default=DEFAULT_MAX_PIXELS)
    parser.add_argument("--ground-y", type=int, help="local building level, drawn as a dashed line")
    parser.add_argument("--overlays", type=Path, help="NPZ with boolean envelope/aura/cavern_aura arrays")
    parser.add_argument("--scale", type=int, default=16, help="pixels per block")
    parser.add_argument("--depth", type=int, nargs=2, metavar=("START", "STOP"),
                        help="local depth range [START, STOP) along each selected view's axis")
    parser.add_argument("--color-mode", choices=("family", "block"), default="family")
    parser.add_argument(
        "--views", nargs="+",
        choices=("top", "bottom", "north", "south", "west", "east"),
        default=("top", "bottom", "north", "south", "west", "east"),
        help="render only a subset of views, e.g. --views top",
    )
    args = parser.parse_args(argv)
    if args.scale < 1:
        parser.error("--scale must be positive")

    output = Path(args.output)
    try:
        structure = load_structure(args.src, region=args.region, max_blocks=args.max_blocks)
        overlays = (load_overlays(args.overlays, structure.size, max_blocks=args.max_blocks, ground_y=args.ground_y)
                    if args.overlays is not None else ProjectionOverlays(ground_y=args.ground_y))
        render_projections(structure, output, views=args.views, scale=args.scale,
                           color_mode=args.color_mode, max_pixels=args.max_pixels, overlays=overlays, depth=args.depth)
    except (ValueError, OSError) as error:
        parser.error(str(error))
    print(output)


if __name__ == "__main__":
    main()
