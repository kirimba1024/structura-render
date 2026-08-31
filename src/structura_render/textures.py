"""Resolve vanilla block textures, extracted once from the player's own
licensed client jar into assets/minecraft/textures/block/ (not redistributed,
just a local convenience cache for this private project's own renders)."""
from pathlib import Path

import numpy as np
from PIL import Image

from .assets import ASSETS

BLOCK_TEXTURES = ASSETS / "textures/block"
TEXTURES = ASSETS / "textures"

GRASS_TINT = (145, 189, 89)
FOLIAGE_TINT = (95, 158, 62)
WATER_TINT = (63, 118, 228)
SPRUCE_LEAVES_TINT = (97, 153, 97)
BIRCH_LEAVES_TINT = (128, 167, 85)

STRIP_SUFFIXES = (
    "_stairs", "_slab", "_fence_gate", "_fence", "_wall_sign", "_wall",
    "_door", "_trapdoor", "_pressure_plate", "_button", "_sign", "_carpet",
    "_pane",
)


def _tint(image, color):
    array = np.asarray(image).astype(np.float32)
    factor = np.array([*color, 255], dtype=np.float32) / 255.0
    return Image.fromarray(np.clip(array * factor, 0, 255).astype(np.uint8), "RGBA")


def tint_for(name, props=None):
    props = props or {}
    base = name.split(":", 1)[-1]
    if base.startswith("potted_"):
        base = base[len("potted_"):]
    if base == "grass_block":
        return GRASS_TINT
    if base == "spruce_leaves":
        return SPRUCE_LEAVES_TINT
    if base == "birch_leaves":
        return BIRCH_LEAVES_TINT
    if base.endswith("_leaves") and "azalea" not in base:
        return FOLIAGE_TINT
    if base in (
        "short_grass", "fern", "grass", "tall_grass", "large_fern", "sugar_cane",
        "bush", "pink_petals", "wildflowers",
    ):
        return GRASS_TINT
    if base in ("vine", "bamboo", "bamboo_sapling", "leaf_litter"):
        return FOLIAGE_TINT
    if base == "lily_pad":
        return 32, 128, 48
    if base == "water_cauldron":
        return WATER_TINT
    if base == "redstone_wire":
        power = int(props.get("power", 0)) / 15
        return tuple(round(255 * value) for value in (
            power * 0.6 + (0.4 if power else 0.3),
            max(0, power * power * 0.7 - 0.5),
            max(0, power * power * 0.6 - 0.7),
        ))
    if base in ("melon_stem", "pumpkin_stem"):
        age = int(props.get("age", 0))
        return age * 32, 255 - age * 8, age * 4
    if base in ("attached_melon_stem", "attached_pumpkin_stem"):
        return 224, 199, 0
    if base in ("lava_cauldron", "powder_snow_cauldron", "stonecutter"):
        return 255, 255, 255
    return None


class TextureBank:
    def __init__(self):
        self._cache = {}
        self._asset_cache = {}

    def available(self):
        return BLOCK_TEXTURES.is_dir()

    def read_texture(self, stem, tint=None):
        image = self._read(stem)
        return _tint(image, tint) if image and tint else image

    def read_asset(self, stem, tint=None, crop=None, alpha=255):
        key = (stem, crop, tint, alpha)
        if key in self._asset_cache:
            return self._asset_cache[key]
        if stem.startswith("effect/"):
            image = self._effect(stem)
        else:
            path = TEXTURES / f"{stem}.png"
            if not path.exists() and stem == "entity/banner/banner_base":
                path = TEXTURES / "entity/banner_base.png"
            image = self._open(path)
        if image is not None and crop:
            image = image.crop(crop)
        if image is not None and tint:
            image = _tint(image, tint)
        if image is not None and alpha < 255:
            values = np.asarray(image).copy()
            values[..., 3] = values[..., 3].astype(np.uint16) * alpha // 255
            image = Image.fromarray(values, "RGBA")
        self._asset_cache[key] = image
        return image

    @staticmethod
    def _open(path):
        if not path.exists():
            return None
        image = Image.open(path).convert("RGBA")
        if image.height > image.width and "entity" not in path.parts:
            image = image.crop((0, 0, image.width, image.width))
        return image

    @staticmethod
    def _effect(stem):
        image = np.zeros((16, 16, 4), dtype=np.uint8)
        image[:] = (8, 4, 18, 245) if stem.endswith("end_portal") else (18, 3, 34, 245)
        colors = ((104, 92, 210, 255), (71, 170, 210, 255), (225, 225, 255, 255))
        for i in range(22):
            x, y = (i * 7 + 3) % 16, (i * 11 + i // 3) % 16
            image[y, x] = colors[i % len(colors)]
        return Image.fromarray(image, "RGBA")

    def _read(self, stem):
        if stem in self._cache:
            return self._cache[stem]
        image = self._open(BLOCK_TEXTURES / f"{stem}.png")
        self._cache[stem] = image
        return image

    def resolve(self, block_name):
        base = block_name.split(":", 1)[-1]
        base = base.replace("wall_torch", "torch")
        base = "water" if base == "bubble_column" else base
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
            return {"all": _tint(image, tint_for(block_name))} if image else None
        if base in ("short_grass", "fern", "grass", "sugar_cane"):
            image = self._read(base)
            return {"all": _tint(image, GRASS_TINT)} if image else None
        if base in ("tall_grass", "large_fern"):
            top, bottom = self._read(f"{base}_top"), self._read(f"{base}_bottom")
            if top and bottom:
                return {"top": _tint(top, GRASS_TINT), "bottom": _tint(bottom, GRASS_TINT)}
        if base == "vine":
            image = self._read("vine")
            return {"all": _tint(image, FOLIAGE_TINT)} if image else None
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
