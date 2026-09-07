#!/usr/bin/env python3
"""Render six colored diagnostic projections of a Structure NBT."""
import argparse
import colorsys
import hashlib
import math
from os import PathLike
from pathlib import Path
from typing import Iterable, Literal, Optional, Tuple, Union

import numpy as np
from PIL import Image, ImageDraw
from structura_core import AIR_NAMES, Structure
from structura_core.litematic import DEFAULT_MAX_BLOCKS

from .export_io import write_image
from .legacy_input import load_structure
from .overlays import ProjectionOverlays, draw_overlays, load_overlays

VIEWS = {
    "top": (1, True), "bottom": (1, False),
    "north": (2, False), "south": (2, True),
    "west": (0, False), "east": (0, True),
}
DEFAULT_MAX_PIXELS = 16_000_000

COLORS = {
    "air": (0, 0, 0),
    "grass": (92, 151, 72),
    "plant": (81, 132, 71),
    "dirt": (133, 91, 57),
    "sand": (210, 190, 133),
    "log": (91, 62, 39),
    "wood": (151, 105, 61),
    "stone": (143, 149, 157),
    "brick": (119, 123, 132),
    "glass": (104, 188, 205),
    "terracotta": (174, 112, 86),
    "metal": (104, 112, 125),
    "light": (244, 187, 68),
}


def family(name):
    plant_parts = ("grass", "leaves", "flower", "sapling", "vine", "fern", "lichen")
    if any(part in name for part in plant_parts):
        return "plant" if "grass_block" not in name else "grass"
    if any(part in name for part in ("dirt", "mud", "podzol", "mycelium")):
        return "dirt"
    if any(part in name for part in ("sand", "gravel")):
        return "sand"
    if any(part in name for part in ("_log", "_stem", "hyphae")):
        return "log"
    if any(part in name for part in ("planks", "wood", "fence", "door", "ladder")):
        return "wood"
    if "glass" in name:
        return "glass"
    if "terracotta" in name:
        return "terracotta"
    if any(part in name for part in ("brick", "cobble", "deepslate")):
        return "brick"
    if any(part in name for part in ("stone", "andesite", "diorite", "granite", "slate")):
        return "stone"
    if any(part in name for part in ("iron", "copper", "gold", "chain", "bars")):
        return "metal"
    if any(part in name for part in ("torch", "lantern", "light", "candle")):
        return "light"
    return None


def block_color(name, mode):
    group = family(name)
    if mode == "family" and group:
        return COLORS[group]
    digest = hashlib.blake2b(name.encode(), digest_size=2).digest()
    hue = int.from_bytes(digest, "big") / 65535
    return tuple(round(value * 255) for value in colorsys.hsv_to_rgb(hue, 0.48, 0.78))


def frontmost(states, axis, reverse):
    data = np.moveaxis(states, axis, -1)
    if reverse:
        data = data[..., ::-1]
    present = data >= 0
    index = present.argmax(axis=-1)
    result = np.take_along_axis(data, index[..., None], axis=-1)[..., 0]
    result[~present.any(axis=-1)] = -1
    return result


def orient(image, view):
    if view in ("top", "bottom"):
        return image.T
    if view == "north":
        return image.T[::-1]
    if view == "south":
        return image.T[::-1, ::-1]
    if view == "west":
        return image[::-1]
    return image[::-1, ::-1]


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


def _check_pixels(size, max_pixels):
    if isinstance(max_pixels, bool) or not isinstance(max_pixels, int) or max_pixels <= 0:
        raise ValueError("max_pixels must be a positive integer")
    if math.prod(size) > max_pixels:
        raise ValueError(f"image size {size} exceeds max_pixels={max_pixels:,}; reduce scale")


def _projection_size(size, view, scale):
    if view not in VIEWS:
        raise ValueError(f"unknown view {view!r}; expected one of {tuple(VIEWS)}")
    if isinstance(scale, bool) or not isinstance(scale, int) or scale < 1:
        raise ValueError("scale must be a positive integer")
    axis = VIEWS[view][0]
    plane = tuple(size[i] for i in range(3) if i != axis)
    width, height = plane[::-1] if axis == 0 else plane
    return width * scale, height * scale


def _depth_range(depth, size, axis):
    if depth is None:
        return 0, size[axis]
    if (not isinstance(depth, (tuple, list)) or len(depth) != 2
            or any(isinstance(v, (bool, np.bool_)) or not isinstance(v, (int, np.integer)) for v in depth)
            or not 0 <= depth[0] < depth[1] <= size[axis]):
        raise ValueError(f"depth must be (start, stop) with 0 <= start < stop <= {size[axis]} along {'XYZ'[axis]}")
    return tuple(int(v) for v in depth)


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
    size = _projection_size(src.size, view, scale)
    _check_pixels(size, max_pixels)
    axis, reverse = VIEWS[view]
    start, stop = _depth_range(depth, src.size, axis)
    plane_axes = tuple(i for i in range(3) if i != axis)
    plane_size = tuple(src.size[i] for i in plane_axes)
    visible = np.full(plane_size, -1, dtype=np.int32)
    visible_depth = np.full(plane_size, -1 if reverse else src.size[axis], dtype=np.int64)
    for pos, index in src.present.items():
        if not start <= pos[axis] < stop:
            continue
        if src.palette[index] in AIR_NAMES or src.palette[index] == "minecraft:structure_void":
            continue
        cell = tuple(pos[i] for i in plane_axes)
        closer = pos[axis] > visible_depth[cell] if reverse else pos[axis] < visible_depth[cell]
        if closer:
            visible[cell], visible_depth[cell] = index, pos[axis]
    visible = orient(visible, view)
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
        if not isinstance(overlays, ProjectionOverlays):
            raise ValueError("overlays must be ProjectionOverlays")
        canvas = draw_overlays(canvas, overlays, view, src.size, axis, orient, depth=(start, stop))
    return Image.fromarray(canvas).resize(size, Image.Resampling.NEAREST)


def render_projections(source: Union[str, PathLike[str], Structure], output: Optional[Union[str, PathLike[str]]] = None, *,
                       views: Iterable[Literal["top", "bottom", "north", "south", "west", "east"]] = tuple(VIEWS),
                       scale: int = 16, color_mode: Literal["family", "block"] = "family",
                       max_pixels: int = DEFAULT_MAX_PIXELS, overlays: Optional[ProjectionOverlays] = None,
                       depth: Optional[Tuple[int, int]] = None) -> Image.Image:
    """Return a sheet of named projections; optionally save it atomically."""
    src = load_structure(source)
    views = tuple(views)
    sizes = [_projection_size(src.size, view, scale) for view in views]
    for view in views:
        _depth_range(depth, src.size, VIEWS[view][0])
    _, _, size = _layout([(w + 16, h + 38) for w, h in sizes])
    _check_pixels(size, max_pixels)
    panels = [
        panel(np.asarray(render_projection(src, view=view, scale=1, color_mode=color_mode,
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
