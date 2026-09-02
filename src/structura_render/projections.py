#!/usr/bin/env python3
"""Render six colored diagnostic projections of a Structure NBT."""
import argparse
import colorsys
import hashlib
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

from structura_core import AIR_NAMES, Structure
from structura_core.voxel import dilation

from .legacy_input import as_structure_nbt

DIAGNOSTIC_CAVERN_RADIUS = 4.0


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
POD_COLORS = {
    "minecraft:grass_block": (91, 145, 67),
    "minecraft:dirt": (116, 76, 47),
    "minecraft:stone": (92, 98, 108),
}
AURA = (56, 192, 224)
CAVERN_AURA = (88, 132, 235)
BUBBLE_AURA = (142, 174, 242)
ENVELOPE = (190, 76, 226)
GLASS_DOME = (116, 220, 240)


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


def place_mask(target_shape, mask, shift):
    target = np.zeros(target_shape, dtype=bool)
    if any(delta < 0 for delta in shift):
        raise ValueError("mask shift must be non-negative")
    slices = tuple(slice(delta, delta + length) for delta, length in zip(shift, mask.shape))
    if any(part.stop > limit for part, limit in zip(slices, target_shape)):
        raise ValueError("mask does not fit the target NBT")
    target[slices] = mask
    return target


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


def blend(image, mask, color, alpha):
    image[mask] = image[mask] * (1 - alpha) + np.asarray(color) * alpha


def render_view(
    states, palette, pod, envelope, aura, cavern_aura, bubble_aura,
    glass_dome, view, color_mode,
):
    axis, reverse = {
        "top": (1, True), "bottom": (1, False),
        "north": (2, False), "south": (2, True),
        "west": (0, False), "east": (0, True),
    }[view]
    visible = orient(frontmost(np.where(glass_dome, -1, states), axis, reverse), view)
    canvas = np.full((*visible.shape, 3), 246.0)

    for index in np.unique(visible[visible >= 0]):
        canvas[visible == index] = block_color(palette[int(index)], color_mode)

    pod_visible = orient(frontmost(np.where(pod, states, -1), axis, reverse), view)
    for index in np.unique(pod_visible[pod_visible >= 0]):
        name = palette[int(index)]
        canvas[pod_visible == index] = POD_COLORS.get(name, (102, 91, 75))

    aura_2d = orient(aura.any(axis=axis), view)
    cavern_2d = orient(cavern_aura.any(axis=axis), view)
    bubble_2d = orient(bubble_aura.any(axis=axis), view)
    envelope_2d = orient(envelope.any(axis=axis), view)
    glass_2d = orient(glass_dome.any(axis=axis), view)
    blend(canvas, bubble_2d, BUBBLE_AURA, 0.12)
    blend(canvas, cavern_2d, CAVERN_AURA, 0.14)
    blend(canvas, aura_2d, AURA, 0.22)
    blend(canvas, envelope_2d, ENVELOPE, 0.26)
    blend(canvas, glass_2d, GLASS_DOME, 0.28)

    edge = envelope_2d & ~ndimage.binary_erosion(envelope_2d)
    canvas[edge] = np.asarray(ENVELOPE) * 0.8
    glass_edge = glass_2d & ~ndimage.binary_erosion(glass_2d)
    canvas[glass_edge] = np.asarray(GLASS_DOME) * 0.82
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
    legend_height = 52
    caption_height = 22 if caption else 0
    legend = [
        (GLASS_DOME, "glass dome"),
        (BUBBLE_AURA, "bubble aura"),
        (CAVERN_AURA, "cavern aura"), (AURA, "aura"),
        (ENVELOPE, "envelope"),
        (POD_COLORS["minecraft:grass_block"], "pod grass"),
        (POD_COLORS["minecraft:dirt"], "pod dirt"),
        (POD_COLORS["minecraft:stone"], "pod stone"),
    ]
    measure = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    legend_width = gap + sum(
        22 + measure.textlength(label) + 24 for _color, label in legend
    )
    canvas = Image.new(
        "RGB",
        (
            max(sum(widths) + gap * (columns + 1), int(legend_width) + gap),
            sum(rows) + gap * (row_count + 1) + legend_height + caption_height,
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
    x, y = gap, canvas.height - 34
    for color, label in legend:
        draw.rectangle((x, y, x + 16, y + 16), fill=color)
        draw.text((x + 22, y + 2), label, fill=(35, 38, 44))
        x += 22 + draw.textlength(label) + 24
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("src")
    parser.add_argument("output")
    parser.add_argument("--envelope-masks")
    parser.add_argument("--pod-masks")
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

    structure = Structure(as_structure_nbt(args.src))
    states = np.full(structure.size, -1, dtype=np.int32)
    for pos, index in structure.present.items():
        if structure.palette[index] not in AIR_NAMES:
            states[pos] = index

    pod = np.zeros(structure.size, dtype=bool)
    envelope = np.zeros(structure.size, dtype=bool)
    aura = np.zeros(structure.size, dtype=bool)
    cavern_aura = np.zeros(structure.size, dtype=bool)
    bubble_aura = np.zeros(structure.size, dtype=bool)
    glass_dome = np.zeros(structure.size, dtype=bool)
    pod_shift = (0, 0, 0)
    ground_y = None
    caption_parts = []
    if args.pod_masks:
        masks = np.load(args.pod_masks)
        pod = place_mask(structure.size, masks["pod"], (0, 0, 0))
        pod_shift = tuple(int(value) for value in masks["shift"])
        if "base_y" in masks:
            ground_y = int(masks["base_y"])
        if "profile" in masks:
            profile = masks["profile"]
            caption_parts.append(
                f"pod top={profile[0]:.1f} peak={profile.max():.1f} tail={profile[-1]:.1f}",
            )
    if args.envelope_masks:
        masks = np.load(args.envelope_masks)
        envelope = place_mask(structure.size, masks["surface"], pod_shift)
        aura = place_mask(structure.size, masks["aura"], pod_shift)
        full_envelope = place_mask(structure.size, masks["envelope"], pod_shift)
        if ground_y is None and "base_y" in masks:
            ground_y = int(masks["base_y"])
        cavern_aura = dilation(full_envelope, DIAGNOSTIC_CAVERN_RADIUS) & ~full_envelope
        if ground_y is not None:
            cavern_aura[:, :ground_y, :] = False
        if "glass_dome" in masks:
            glass_dome = place_mask(
                structure.size, masks["glass_dome"], pod_shift,
            )
        if "bubble_aura" in masks:
            bubble_aura = place_mask(
                structure.size, masks["bubble_aura"], pod_shift,
            )
        if "envelope_radius" in masks:
            caption_parts.insert(0, (
                f"envelope={float(masks['envelope_radius']):.1f} "
                f"aura={float(masks['aura_radius']):.1f} "
                f"cavern={float(masks['cavern_aura_radius']):.1f} "
                f"(viz cavern={DIAGNOSTIC_CAVERN_RADIUS:.1f}) "
                f"glass_dome={'on' if glass_dome.any() else 'off'}"
            ))

    views = tuple(args.views)
    rendered = [
        render_view(
            states, structure.palette, pod, envelope, aura, cavern_aura,
            bubble_aura, glass_dome, view, args.color_mode,
        )
        for view in views
    ]

    output = Path(args.output)
    compose(
        [panel(image, view, args.scale) for image, view in zip(rendered, views)],
        output,
        caption=" | ".join(caption_parts) or None,
    )
    print(output)


if __name__ == "__main__":
    main()
