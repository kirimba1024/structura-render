"""Vector plans sharing the raster renderer's visibility and coordinates."""

import argparse
from os import PathLike
from pathlib import Path
from typing import Literal, Optional, Tuple, Union
from xml.etree.ElementTree import Element, SubElement, tostring

import numpy as np
from structura_core import Structure

from .export_io import atomic_write
from .legacy_input import load_structure
from .overlays import ProjectionOverlays, load_overlays
from .projections import (
    DEFAULT_MAX_PIXELS, VIEWS, _check_pixels, _depth_range, _projection_size,
    block_color, orient, projection_cells,
)


def rectangles(cells):
    active = {}
    for y, row in enumerate(cells):
        edges = np.flatnonzero(np.r_[True, row[1:] != row[:-1], True])
        current = {}
        for x, stop in zip(edges[:-1], edges[1:]):
            value = int(row[x])
            if value < 0:
                continue
            key = int(x), int(stop), value
            current[key] = active.pop(key, y)
        for (x, stop, value), start in active.items():
            yield x, start, stop - x, y - start, value
        active = current
    for (x, stop, value), start in active.items():
        yield x, start, stop - x, len(cells) - start, value


def render_svg(source: Union[str, PathLike[str], Structure],
               output: Optional[Union[str, PathLike[str]]] = None, *,
               view: Literal["top", "bottom", "north", "south", "west", "east"] = "top",
               scale: int = 16, color_mode: Literal["family", "block"] = "family",
               transparent: bool = False, overlays: Optional[ProjectionOverlays] = None,
               depth: Optional[Tuple[int, int]] = None, max_pixels: int = DEFAULT_MAX_PIXELS,
               max_elements: int = 100_000, title: Optional[str] = None) -> str:
    """Return a standalone SVG plan; optionally save it atomically."""
    src = load_structure(source)
    size = _projection_size(src.size, view, scale)
    if title is not None:
        if not isinstance(title, str) or any(
            not (c in "\t\r\n" or 32 <= ord(c) <= 0xD7FF or 0xE000 <= ord(c) <= 0xFFFD or
                 0x10000 <= ord(c) <= 0x10FFFF) for c in title
        ):
            raise ValueError("title must be valid XML text")
        size = size[0], size[1] + 2 * scale
    _check_pixels(size, max_pixels)
    if isinstance(max_elements, bool) or not isinstance(max_elements, int) or max_elements < 1:
        raise ValueError("max_elements must be a positive integer")
    if color_mode not in {"family", "block"}:
        raise ValueError("color_mode must be 'family' or 'block'")
    if overlays is not None:
        if not isinstance(overlays, ProjectionOverlays):
            raise ValueError("overlays must be ProjectionOverlays")
        overlays.validate(src.size)
    cells = projection_cells(src, view, depth)
    height, width = cells.shape
    root = Element("svg", xmlns="http://www.w3.org/2000/svg", width=str(size[0]), height=str(size[1]),
                   viewBox=f"0 {-2 if title is not None else 0} {width} {height + (2 if title is not None else 0)}", role="img")
    SubElement(root, "title").text = title if title is not None else f"{view.upper()} — {width} × {height} blocks"
    SubElement(root, "desc").text = f"Local coordinates; depth {depth if depth is not None else 'all'}. One SVG unit per block."
    count = 0

    def add(parent, tag, **attributes):
        nonlocal count
        count += 1
        if count > max_elements:
            raise ValueError(f"SVG exceeds max_elements={max_elements:,}; choose a smaller region or use PNG")
        return SubElement(parent, tag, {key.replace('_', '-'): str(value) for key, value in attributes.items()})

    if not transparent:
        add(root, "rect", y=-2 if title is not None else 0, width=width,
            height=height + (2 if title is not None else 0), fill="#f6f6f6")
    if title is not None:
        add(root, "text", id="caption", x=.25, y=-.65, font_family="sans-serif",
            font_size=min(1, (width - .5) / max(1, len(title))),
            fill="#181b20").text = title
    group = add(root, "g", id="blocks", shape_rendering="crispEdges")
    colors = [block_color(name, color_mode) for name in src.palette]
    unique = {color: i for i, color in enumerate(dict.fromkeys(colors))}
    palette = np.asarray([unique[color] for color in colors])
    merged = np.full_like(cells, -1)
    visible = cells >= 0
    merged[visible] = palette[cells[visible]]
    paints = ["#%02x%02x%02x" % color for color in unique]
    for x, y, w, h, value in rectangles(merged):
        add(group, "rect", x=x, y=y, width=w, height=h, fill=paints[value])
    if overlays is not None:
        axis = VIEWS[view][0]
        start, stop = _depth_range(depth, src.size, axis)
        selection = [slice(None)] * 3
        selection[axis] = slice(start, stop)
        for name, color, opacity in (("cavern_aura", "#5884eb", .14), ("aura", "#38c0e0", .22),
                                     ("envelope", "#be4ce2", .26)):
            mask = getattr(overlays, name)
            if mask is None:
                continue
            plane = orient(mask[tuple(selection)].any(axis=axis), view)
            group = add(root, "g", id=name, fill=color)
            for x, y, w, h, _ in rectangles(np.where(plane, 0, -1)):
                add(group, "rect", x=x, y=y, width=w, height=h, fill_opacity=opacity)
            border = add(group, "g", fill="none", stroke=color, stroke_width=.08)
            for swapped in (False, True):
                data = plane.T if swapped else plane
                padded = np.pad(data, ((1, 1), (0, 0)))
                edges = padded[1:] != padded[:-1]
                for y, row in enumerate(edges):
                    changes = np.flatnonzero(np.diff(np.r_[False, row, False]))
                    for a, b in zip(changes[::2], changes[1::2]):
                        values = (y, a, y, b) if swapped else (a, y, b, y)
                        add(border, "path", d="M%s %sL%s %s" % values)
        if overlays.ground_y is not None and axis != 1:
            y = src.size[1] - overlays.ground_y - .5
            add(root, "path", id="ground", d=f"M0 {y}H{width}", stroke="#000", stroke_opacity=.45,
                stroke_width=.12, stroke_dasharray="2 2", fill="none")
    result = tostring(root, encoding="unicode") + "\n"
    if output is not None:
        if Path(output).suffix.lower() != ".svg":
            raise ValueError("SVG output must end in .svg")
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
    parser.add_argument("--max-blocks", type=int, default=2_000_000)
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
