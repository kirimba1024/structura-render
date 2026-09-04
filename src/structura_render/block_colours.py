#!/usr/bin/env python3
import numpy as np

from .textures import TextureBank, tint_for


def _stem(name):
    return name.split(":", 1)[-1]


def average_colour(bank, name):
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
    bank = TextureBank()
    if not bank.available():
        return {}
    table = {}
    for name in set(names):
        colour = average_colour(bank, name)
        if colour is not None:
            table[name] = colour
    return table
