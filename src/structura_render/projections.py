#!/usr/bin/env python3
"""Render six colored diagnostic projections of a Structure NBT."""
import argparse
import colorsys
import hashlib
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from structura_core import AIR_NAMES

from .legacy_input import load_structure


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
    axis, reverse = {
        "top": (1, True), "bottom": (1, False),
        "north": (2, False), "south": (2, True),
        "west": (0, False), "east": (0, True),
    }[view]
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


def compose(panels, output, caption=None):
    columns = min(3, len(panels))
    row_count = math.ceil(len(panels) / columns)
    gap = 18
    widths = [
        max((panels[i].width for i in range(col, len(panels), columns)), default=0)
        for col in range(columns)
    ]
    rows = [
        max((panel.height for panel in panels[row * columns:(row + 1) * columns]), default=0)
        for row in range(row_count)
    ]
    caption_height = 22 if caption else 0
    canvas = Image.new(
        "RGB",
        (
            sum(widths) + gap * (columns + 1),
            sum(rows) + gap * (row_count + 1) + caption_height,
        ),
        (238, 240, 243),
    )
    for index, item in enumerate(panels):
        row, col = divmod(index, columns)
        x = gap + sum(widths[:col]) + gap * col
        y = gap + sum(rows[:row]) + gap * row + caption_height
        canvas.paste(item, (x, y))

    draw = ImageDraw.Draw(canvas)
    if caption:
        draw.text((gap, 4), caption, fill=(60, 64, 72))
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("src")
    parser.add_argument("output")
    parser.add_argument("--scale", type=int, default=16, help="pixels per block")
    parser.add_argument("--color-mode", choices=("family", "block"), default="family")
    parser.add_argument(
        "--views", nargs="+",
        choices=("top", "bottom", "north", "south", "west", "east"),
        default=("top", "bottom", "north", "south", "west", "east"),
        help="render only a subset of views, e.g. --views top",
    )
    args = parser.parse_args()
    if args.scale < 1:
        parser.error("--scale must be positive")

    structure = load_structure(args.src)
    states = np.full(structure.size, -1, dtype=np.int32)
    for pos, index in structure.present.items():
        if structure.palette[index] not in AIR_NAMES:
            states[pos] = index

    views = tuple(args.views)
    rendered = [
        render_view(states, structure.palette, view, args.color_mode)
        for view in views
    ]

    output = Path(args.output)
    compose(
        [panel(image, view, args.scale) for image, view in zip(rendered, views)],
        output,
        caption=None,
    )
    print(output)


if __name__ == "__main__":
    main()
