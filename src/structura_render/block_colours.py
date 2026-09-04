#!/usr/bin/env python3
"""Average colour per block, read from the real client textures.

Analysis wants colour and must not start depending on a renderer to get it,
so this lives here -- where the textures already are -- and hands out a
plain name-to-RGB table. structura_core.aesthetics takes that table as an
argument and works without it.
"""
import numpy as np

from .textures import TextureBank, tint_for


def _stem(name):
    return name.split(":", 1)[-1]


def average_colour(bank, name):
    """Mean RGB over the opaque pixels of a block's own texture.

    Falls back through the obvious suffixes, because a block's texture is
    frequently named after the material rather than the block: oak_stairs
    has no texture of its own and wears oak_planks."""
    stem = _stem(name)
    candidates = [stem]
    for suffix, replacement in (
        ("_stairs", "_planks"), ("_slab", "_planks"), ("_fence", "_planks"),
        ("_wall", ""), ("_door", ""), ("_trapdoor", ""),
    ):
        if stem.endswith(suffix):
            candidates.append(stem[: -len(suffix)] + replacement)
    candidates.append(stem + "_top")
    for candidate in candidates:
        image = bank.read_texture(candidate, tint_for(name))
        if image is None:
            continue
        pixels = np.asarray(image.convert("RGBA"), dtype=np.float64)
        opaque = pixels[..., 3] > 16
        if not opaque.any():
            continue
        return tuple(float(value) for value in pixels[..., :3][opaque].mean(axis=0))
    return None


def colour_table(names):
    """Name to RGB for every name that resolves. Names that do not are simply
    absent, and aesthetics.palette_colour reports how much of the mass it
    managed to cover so a thin table is visible rather than silent."""
    bank = TextureBank()
    if not bank.available():
        return {}
    table = {}
    for name in set(names):
        colour = average_colour(bank, name)
        if colour is not None:
            table[name] = colour
    return table
