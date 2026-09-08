import colorsys
import hashlib

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


DYES = {
    "white": (249, 255, 254), "orange": (249, 128, 29),
    "magenta": (199, 78, 189), "light_blue": (58, 179, 218),
    "yellow": (254, 216, 61), "lime": (128, 199, 31),
    "pink": (243, 139, 170), "gray": (71, 79, 82),
    "light_gray": (157, 157, 151), "cyan": (22, 156, 156),
    "purple": (137, 50, 184), "blue": (60, 68, 170),
    "brown": (131, 84, 50), "green": (94, 124, 22),
    "red": (176, 46, 38), "black": (29, 29, 33),
}
