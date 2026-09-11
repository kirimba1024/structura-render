"""Textures and static animation frames from an isolated resource context."""

import json
from typing import Dict, Mapping, Optional, Tuple

import numpy as np
from PIL import Image

from .assets import AssetContext, current_context
from .diagnostics import report_issue

MISSING_ASSETS_MESSAGE = (
    "Minecraft assets were not found; set STRUCTURA_MINECRAFT_ASSETS to a "
    "client jar or extracted assets/minecraft directory"
)

GRASS_TINT = (145, 189, 89)
FOLIAGE_TINT = (95, 158, 62)
WATER_TINT = (63, 118, 228)
WATER_ALPHA = 220
SPRUCE_LEAVES_TINT = (97, 153, 97)
BIRCH_LEAVES_TINT = (128, 167, 85)

STRIP_SUFFIXES = (
    "_stairs", "_slab", "_fence_gate", "_fence", "_wall_sign", "_wall",
    "_door", "_trapdoor", "_pressure_plate", "_button", "_sign", "_carpet",
    "_pane",
)


def _tint(image, color):
    if image is None:
        return None
    array = np.asarray(image).astype(np.float32)
    factor = np.array([*color, 255], dtype=np.float32) / 255.0
    return Image.fromarray(np.clip(array * factor, 0, 255).astype(np.uint8))


def _readable_water(image):
    image = _tint(image, WATER_TINT)
    array = np.asarray(image).copy()
    alpha = array[..., 3]
    array[..., 3] = np.where(alpha, np.maximum(alpha, WATER_ALPHA), 0)
    return Image.fromarray(array)


def tint_for(name: str, props: Optional[Mapping[str, str]] = None) -> Optional[Tuple[int, int, int]]:
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
    def __init__(self, context: Optional[AssetContext] = None) -> None:
        self.context = context if context is not None else current_context()
        self._cache = self.context.cache("block_textures")
        self._asset_cache = self.context.cache("asset_textures")

    def available(self) -> bool:
        return all((self.context.root / directory).is_dir()
                   for directory in ("blockstates", "models/block", "textures/block"))

    def read_texture(self, stem: str, tint: Optional[Tuple[int, int, int]] = None) -> Optional[Image.Image]:
        image = self._read(stem)
        if image is None:
            report_issue("missing texture", stem if ":" in stem else f"minecraft:block/{stem}")
        return _tint(image, tint) if image and tint else image

    def read_asset(self, stem: str, tint: Optional[Tuple[int, int, int]] = None,
                   crop: Optional[Tuple[int, int, int, int]] = None, alpha: int = 255) -> Optional[Image.Image]:
        key = (stem, crop, tint, alpha)
        if key in self._asset_cache:
            if self._asset_cache[key] is None:
                report_issue("missing texture", stem)
            return self._asset_cache[key]
        if stem.startswith("effect/"):
            image = self._effect(stem)
        else:
            path = self.context.path("textures", stem, ".png")
            if not path.exists() and stem == "entity/banner/banner_base":
                path = self.context.path("textures", "entity/banner_base", ".png")
            if (not path.exists()
                    and stem.startswith("entity/decorated_pot/")
                    and stem.endswith("_pottery_pattern")):
                path = self.context.path("textures", "entity/decorated_pot/decorated_pot_side", ".png")
            image = self._open(path)
        if image is not None and crop:
            image = image.crop(crop)
        if image is not None and tint:
            image = _tint(image, tint)
        if image is not None and alpha < 255:
            values = np.asarray(image).copy()
            values[..., 3] = values[..., 3].astype(np.uint16) * alpha // 255
            image = Image.fromarray(values)
        self._asset_cache[key] = image
        if image is None:
            report_issue("missing texture", stem)
        return image

    @staticmethod
    def _open(path):
        if not path.exists():
            return None
        with Image.open(path) as source:
            if source.width * source.height > 16_000_000:
                raise ValueError(f"texture exceeds 16,000,000 pixels: {path}")
            image = source.convert("RGBA")
        metadata_path = path.with_suffix(path.suffix + ".mcmeta")
        metadata = json.loads(metadata_path.read_text()) if metadata_path.is_file() else {}
        if not isinstance(metadata, dict):
            raise ValueError(f"invalid texture metadata: {metadata_path}")
        animation = metadata.get("animation")
        if animation is not None and "entity" not in path.parts:
            if not isinstance(animation, dict):
                raise ValueError(f"invalid texture animation: {metadata_path}")
            default = min(image.size)
            width = animation.get("width", image.width if "height" in animation else default)
            height = animation.get("height", image.height if "width" in animation else default)
            if any(isinstance(v, bool) or not isinstance(v, int) or v < 1 for v in (width, height)):
                raise ValueError(f"invalid animation frame size: {metadata_path}")
            if image.width % width or image.height % height:
                raise ValueError(f"animation frame size does not divide texture: {metadata_path}")
            frames = animation.get("frames", [])
            if not isinstance(frames, list):
                raise ValueError(f"invalid animation frames: {metadata_path}")
            first = frames[0] if frames else 0
            index = first.get("index") if isinstance(first, dict) else first
            if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < image.width // width * (image.height // height):
                raise ValueError(f"invalid animation frame index: {metadata_path}")
            row, column = divmod(index, image.width // width)
            image = image.crop((column * width, row * height, (column + 1) * width, (row + 1) * height))
        return image

    @staticmethod
    def _effect(stem):
        image = np.zeros((16, 16, 4), dtype=np.uint8)
        image[:] = (8, 4, 18, 245) if stem.endswith("end_portal") else (18, 3, 34, 245)
        colors = ((104, 92, 210, 255), (71, 170, 210, 255), (225, 225, 255, 255))
        for i in range(22):
            x, y = (i * 7 + 3) % 16, (i * 11 + i // 3) % 16
            image[y, x] = colors[i % len(colors)]
        return Image.fromarray(image)

    def _read(self, stem):
        if stem in self._cache:
            return self._cache[stem]
        image = self._open(self.context.path("textures", stem if ":" in stem else f"block/{stem}", ".png"))
        self._cache[stem] = image
        return image

    def resolve(self, block_name: str) -> Optional[Dict[str, Image.Image]]:
        base = block_name.split(":", 1)[-1]
        base = base.replace("wall_torch", "torch")
        base = "water" if base == "bubble_column" else base
        if base == "grass_block":
            faces = {
                "top": _tint(self._read("grass_block_top"), GRASS_TINT),
                "side": self._read("grass_block_side"),
                "bottom": self._read("dirt"),
            }
            return faces if all(faces.values()) else None
        if base == "dirt_path":
            faces = {
                "top": self._read("dirt_path_top"),
                "side": self._read("dirt_path_side"),
                "bottom": self._read("dirt"),
            }
            return faces if all(faces.values()) else None
        if base == "farmland":
            faces = {
                "top": self._read("farmland"),
                "side": self._read("dirt"),
                "bottom": self._read("dirt"),
            }
            return faces if all(faces.values()) else None
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
            return {"all": _readable_water(image)} if image else None
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


def texture_bank_or_exit(allow_flat_fallback=False):
    bank = TextureBank()
    if not bank.available() and not allow_flat_fallback:
        raise SystemExit(MISSING_ASSETS_MESSAGE)
    return bank
