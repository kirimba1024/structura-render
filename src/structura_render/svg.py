"""Vector plans sharing the raster renderer's visibility and coordinates."""

import argparse
from os import PathLike
from pathlib import Path
from typing import Literal, Optional, Tuple, Union
from xml.etree.ElementTree import Element, SubElement, tostring

import numpy as np
from structura_core import Structure
from structura_core.limits import DEFAULT_MAX_BLOCKS

from .block_colours import block_color
from .export_io import atomic_write
from .legacy_input import load_structure
from .overlays import ProjectionOverlays, load_overlays, projected_overlays
from .projection_grid import (
    DEFAULT_MAX_PIXELS, VIEWS, boundary_segments, check_pixels, projection_cells,
    projection_size, rectangles as rectangles,
)


class _SvgDocument:
    def __init__(self, size, viewbox, max_elements):
        self.root = Element("svg", xmlns="http://www.w3.org/2000/svg", width=str(size[0]), height=str(size[1]),
                            viewBox=viewbox, role="img")
        self.count = 1
        self.max_elements = max_elements

    def add(self, parent, tag, **attributes):
        if self.count >= self.max_elements:
            raise ValueError(f"SVG exceeds max_elements={self.max_elements:,}; choose a smaller region or use PNG")
        self.count += 1
        return SubElement(parent, tag, {key.replace('_', '-'): str(value) for key, value in attributes.items()})


def _validate_options(output, title, color_mode, max_elements):
    if output is not None and Path(output).suffix.lower() != ".svg":
        raise ValueError("SVG output must end in .svg")
    if isinstance(max_elements, bool) or not isinstance(max_elements, int) or max_elements < 1:
        raise ValueError("max_elements must be a positive integer")
    if color_mode not in {"family", "block"}:
        raise ValueError("color_mode must be 'family' or 'block'")
    if title is not None and (not isinstance(title, str) or any(
        not (c in "\t\r\n" or 32 <= ord(c) <= 0xD7FF or 0xE000 <= ord(c) <= 0xFFFD or
             0x10000 <= ord(c) <= 0x10FFFF) for c in title
    )):
        raise ValueError("title must be valid XML text")


def _draw_blocks(document, cells, palette, color_mode):
    group = document.add(document.root, "g", id="blocks", shape_rendering="crispEdges")
    colors = [block_color(name, color_mode) for name in palette]
    unique = {color: i for i, color in enumerate(dict.fromkeys(colors))}
    color_indices = np.asarray([unique[color] for color in colors])
    merged = np.full_like(cells, -1)
    visible = cells >= 0
    merged[visible] = color_indices[cells[visible]]
    paints = ["#%02x%02x%02x" % color for color in unique]
    for x, y, width, height, value in rectangles(merged):
        document.add(group, "rect", x=x, y=y, width=width, height=height, fill=paints[value])


def _draw_overlays(document, overlays, view, size, depth, width):
    for name, rgb, opacity, plane in projected_overlays(overlays, view, size, depth):
        color = "#%02x%02x%02x" % rgb
        group = document.add(document.root, "g", id=name, fill=color)
        for x, y, w, h, _ in rectangles(np.where(plane, 0, -1)):
            document.add(group, "rect", x=x, y=y, width=w, height=h, fill_opacity=opacity)
        border = document.add(group, "g", fill="none", stroke=color, stroke_width=.08)
        for segment in boundary_segments(plane):
            document.add(border, "path", d="M%s %sL%s %s" % segment)
    if overlays.ground_y is not None and VIEWS[view][0] != 1:
        y = size[1] - overlays.ground_y - .5
        document.add(document.root, "path", id="ground", d=f"M0 {y}H{width}", stroke="#000", stroke_opacity=.45,
                     stroke_width=.12, stroke_dasharray="2 2", fill="none")


def render_svg(source: Union[str, PathLike[str], Structure],
               output: Optional[Union[str, PathLike[str]]] = None, *,
               view: Literal["top", "bottom", "north", "south", "west", "east"] = "top",
               scale: int = 16, color_mode: Literal["family", "block"] = "family",
               transparent: bool = False, overlays: Optional[ProjectionOverlays] = None,
               depth: Optional[Tuple[int, int]] = None, max_pixels: int = DEFAULT_MAX_PIXELS,
               max_elements: int = 100_000, title: Optional[str] = None) -> str:
    """Return a standalone SVG plan; optionally save it atomically."""
    _validate_options(output, title, color_mode, max_elements)
    src = load_structure(source)
    width, height = projection_size(src.size, view, 1)
    size = projection_size(src.size, view, scale)
    caption_height = 2 if title is not None else 0
    size = size[0], size[1] + caption_height * scale
    check_pixels(size, max_pixels)
    cells = projection_cells(src, view, depth)
    document = _SvgDocument(size, f"0 {-caption_height} {width} {height + caption_height}", max_elements)
    root = document.root
    document.add(root, "title").text = title if title is not None else f"{view.upper()} — {width} × {height} blocks"
    document.add(root, "desc").text = f"Local coordinates; depth {depth if depth is not None else 'all'}. One SVG unit per block."
    if not transparent:
        document.add(root, "rect", y=-caption_height, width=width, height=height + caption_height, fill="#f6f6f6")
    if title is not None:
        document.add(root, "text", id="caption", x=.25, y=-.65, font_family="sans-serif",
                     font_size=min(1, (width - .5) / max(1, len(title))), fill="#181b20").text = title
    _draw_blocks(document, cells, src.palette, color_mode)
    if overlays is not None:
        _draw_overlays(document, overlays, view, src.size, depth, width)
    result = tostring(root, encoding="unicode") + "\n"
    if output is not None:
        atomic_write(output, result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("src")
    parser.add_argument("output")
    parser.add_argument("--view", choices=VIEWS, default="top")
    parser.add_argument("--region")
    parser.add_argument("--scale", type=int, default=16)
    parser.add_argument("--depth", type=int, nargs=2, metavar=("START", "STOP"))
    parser.add_argument("--color-mode", choices=("family", "block"), default="family")
    parser.add_argument("--transparent", action="store_true")
    parser.add_argument("--title")
    parser.add_argument("--overlays", type=Path)
    parser.add_argument("--ground-y", type=int)
    parser.add_argument("--max-blocks", type=int, default=DEFAULT_MAX_BLOCKS)
    parser.add_argument("--max-pixels", type=int, default=DEFAULT_MAX_PIXELS)
    parser.add_argument("--max-elements", type=int, default=100_000)
    args = parser.parse_args(argv)
    try:
        src = load_structure(args.src, region=args.region, max_blocks=args.max_blocks)
        overlays = (load_overlays(args.overlays, src.size, max_blocks=args.max_blocks, ground_y=args.ground_y)
                    if args.overlays else ProjectionOverlays(ground_y=args.ground_y))
        render_svg(src, args.output, view=args.view, scale=args.scale, depth=args.depth,
                   color_mode=args.color_mode, transparent=args.transparent, overlays=overlays,
                   max_pixels=args.max_pixels, max_elements=args.max_elements, title=args.title)
    except (ValueError, OSError) as error:
        parser.error(str(error))
    print(Path(args.output).resolve())
