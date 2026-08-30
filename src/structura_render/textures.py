"""Resolve vanilla block textures, extracted once from the player's own
licensed client jar into assets/minecraft/textures/block/ (not redistributed,
just a local convenience cache for this private project's own renders)."""
from pathlib import Path

import numpy as np
from PIL import Image

from .assets import ASSETS

BLOCK_TEXTURES = ASSETS / "textures/block"

GRASS_TINT = (145, 189, 89)
FOLIAGE_TINT = (95, 158, 62)
WATER_TINT = (63, 118, 228)

STRIP_SUFFIXES = (
    "_stairs", "_slab", "_fence_gate", "_fence", "_wall_sign", "_wall",
    "_door", "_trapdoor", "_pressure_plate", "_button", "_sign", "_carpet",
    "_pane",
)


def _tint(image, color):
    array = np.asarray(image).astype(np.float32)
    factor = np.array([*color, 255], dtype=np.float32) / 255.0
    return Image.fromarray(np.clip(array * factor, 0, 255).astype(np.uint8), "RGBA")


def tint_for(name):
    base = name.split(":", 1)[-1]
    if base == "grass_block":
        return GRASS_TINT
    if base.endswith("_leaves") and "azalea" not in base:
        return FOLIAGE_TINT
    if base in ("short_grass", "fern", "grass", "tall_grass", "large_fern"):
        return GRASS_TINT
    return None


class TextureBank:
    def __init__(self):
        self._cache = {}

    def available(self):
        return BLOCK_TEXTURES.is_dir()

    def read_texture(self, stem, tint=None):
        image = self._read(stem)
        return _tint(image, tint) if image and tint else image

    def _read(self, stem):
        if stem in self._cache:
            return self._cache[stem]
        image = None
        path = BLOCK_TEXTURES / f"{stem}.png"
        if path.exists():
            image = Image.open(path).convert("RGBA")
            if image.height > image.width:
                image = image.crop((0, 0, image.width, image.width))
        self._cache[stem] = image
        return image

    def resolve(self, block_name):
        base = block_name.split(":", 1)[-1]
        base = base.replace("wall_torch", "torch")
        if base == "grass_block":
            return {
                "top": _tint(self._read("grass_block_top"), GRASS_TINT),
                "side": self._read("grass_block_side"),
                "bottom": self._read("dirt"),
            }
        if base == "dirt_path":
            return {
                "top": self._read("dirt_path_top"),
                "side": self._read("dirt_path_side"),
                "bottom": self._read("dirt"),
            }
        if base == "farmland":
            return {
                "top": self._read("farmland"),
                "side": self._read("dirt"),
                "bottom": self._read("dirt"),
            }
        if base.endswith("_leaves") and "azalea" not in base:
            image = self._read(base)
            return {"all": _tint(image, FOLIAGE_TINT)} if image else None
        if base in ("short_grass", "fern", "grass"):
            image = self._read(base)
            return {"all": _tint(image, GRASS_TINT)} if image else None
        if base in ("tall_grass", "large_fern"):
            top, bottom = self._read(f"{base}_top"), self._read(f"{base}_bottom")
            if top and bottom:
                return {"top": _tint(top, GRASS_TINT), "bottom": _tint(bottom, GRASS_TINT)}
        if base == "water":
            image = self._read("water_still")
            return {"all": _tint(image, WATER_TINT)} if image else None
        if base == "lava":
            image = self._read("lava_still")
            return {"all": image} if image else None
        if base.endswith(("_log", "_stem")):
            side = self._read(base)
            top = self._read(f"{base}_top")
            if side and top:
                return {"top": top, "bottom": top, "side": side}
            if side:
                return {"all": side}
        if not base.endswith(("_door", "_trapdoor")):
            top, bottom = self._read(f"{base}_top"), self._read(f"{base}_bottom")
            if top and bottom:
                return {"top": top, "bottom": bottom}
        stripped = base
        for suffix in STRIP_SUFFIXES:
            if stripped.endswith(suffix):
                stripped = stripped[: -len(suffix)]
                break
        for candidate in (base, stripped, f"{stripped}s", f"{stripped}_planks", f"{stripped}_block"):
            image = self._read(candidate)
            if image:
                return {"all": image}
        return None
