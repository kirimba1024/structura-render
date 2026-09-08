from PIL import Image

from .assets import context_cached, current_context, texture_asset as _asset
from .diagnostics import report_issue
from .entity_models import model_parts
from .entity_state import _is_baby, _number, _plain, _yaw
from .mob_catalog import COMMON_DUMMY_RIGS, DUMMY_RIGS, RIG_HEAD_PARTS
from .shape_geometry import _scale_parts, box


@context_cached
def _opaque_texture_tiles(path):
    try:
        with Image.open(path) as source:
            image = source.convert("RGBA")
    except OSError:
        return ()

    visible = [pixel for pixel in image.getdata() if pixel[3] > 0]
    if not visible:
        return ()
    mean = tuple(sum(pixel[channel] for pixel in visible) / len(visible)
                 for channel in range(3))

    candidates = []
    pixels = image.load()
    for threshold in (255, 1):
        for size in (4, 2, 1):
            for y in range(0, image.height - size + 1, size):
                for x in range(0, image.width - size + 1, size):
                    tile = [pixels[x + dx, y + dy]
                            for dy in range(size) for dx in range(size)]
                    if min(pixel[3] for pixel in tile) < threshold:
                        continue
                    average = tuple(sum(pixel[channel] for pixel in tile) / len(tile)
                                    for channel in range(3))
                    candidates.append((average, (x, y, x + size, y + size)))
            if candidates:
                break
        if candidates:
            break
    if not candidates:
        return ()

    def distance(left, right):
        return sum((left[channel] - right[channel]) ** 2 for channel in range(3))

    primary = min(candidates, key=lambda candidate: distance(candidate[0], mean))
    accent = max(candidates, key=lambda candidate: distance(candidate[0], primary[0]))
    return primary[1], accent[1]


def _safe_texture_crop(texture, *, accent=False):
    tiles = _opaque_texture_tiles(current_context().path("textures", texture, ".png"))
    if not tiles:
        return None
    return tiles[1 if accent and len(tiles) > 1 else 0]


def _int_variant(nbt, key, names):
    try:
        return names[int(_number(nbt.get(key, 0))) % len(names)]
    except (TypeError, ValueError, ZeroDivisionError):
        return names[0]


def _mob_texture(kind, nbt, defaults):
    variant = _plain(nbt.get("variant", nbt.get("Variant", "")))
    if variant.lstrip("-").isdigit():
        variant = ""
    stem = None
    if kind in {"chicken", "cow", "pig"}:
        stem = f"entity/{kind}/{kind}_{variant or 'temperate'}"
    elif kind == "axolotl":
        value = _int_variant(nbt, "Variant", ("lucy", "wild", "gold", "cyan", "blue"))
        stem = f"entity/axolotl/axolotl_{value}"
    elif kind == "cat":
        value = variant or _int_variant(nbt, "CatType", (
            "tabby", "black", "red", "siamese", "british_shorthair", "calico",
            "persian", "ragdoll", "white", "jellie", "all_black",
        ))
        stem = f"entity/cat/cat_{value}"
    elif kind == "fox":
        value = variant or _int_variant(nbt, "Type", ("red", "snow"))
        stem = "entity/fox/fox_snow" if value == "snow" else "entity/fox/fox"
    elif kind == "frog":
        stem = f"entity/frog/frog_{variant or 'temperate'}"
    elif kind == "horse":
        names = (
            "white", "creamy", "chestnut", "brown", "black", "gray", "darkbrown",
        )
        value = names[min(int(_number(nbt.get("Variant", 0))) & 255, len(names) - 1)]
        stem = f"entity/horse/horse_{value}"
    elif kind in ("llama", "trader_llama"):
        value = _int_variant(nbt, "Variant", ("creamy", "white", "brown", "gray"))
        stem = f"entity/llama/llama_{value}"
    elif kind == "mooshroom":
        value = _plain(nbt.get("Type", variant or "red"))
        stem = f"entity/cow/mooshroom_{value}"
    elif kind == "parrot":
        value = _int_variant(nbt, "Variant", ("red_blue", "blue", "green", "yellow_blue", "grey"))
        stem = f"entity/parrot/parrot_{value}"
    elif kind == "rabbit":
        rabbit_type = int(_number(nbt.get("RabbitType", 0)))
        names = ("brown", "white", "black", "white_splotched", "gold", "salt")
        value = "caerbannog" if rabbit_type == 99 else names[min(max(rabbit_type, 0), 5)]
        if "toast" in str(nbt.get("CustomName", "")).lower():
            value = "toast"
        stem = f"entity/rabbit/rabbit_{value}"
    elif kind == "sniffer" and _is_baby(nbt):
        stem = "entity/sniffer/snifflet"
    elif kind == "wolf" and variant:
        stem = "entity/wolf/wolf" if variant == "pale" else f"entity/wolf/wolf_{variant}"
    elif kind == "zombie_nautilus" and "coral" in variant:
        stem = "entity/nautilus/zombie_nautilus_coral"

    candidates = []
    if stem:
        if _is_baby(nbt):
            candidates.append(stem + "_baby")
        candidates.append(stem)
    if _is_baby(nbt):
        candidates.extend(default + "_baby" for default in defaults)
    return _asset(*candidates, *defaults, "block/structure_block", "block/red_wool")


def dummy_parts(nbt, *, kind, family, textures, scale=1.0):
    texture = _mob_texture(kind, nbt, textures)
    angle = _yaw(nbt)
    parts = []
    rig = COMMON_DUMMY_RIGS.get(kind, DUMMY_RIGS[family])
    for index, (lo, hi) in enumerate(rig):
        part = box(
            lo, hi, texture,
            crop=_safe_texture_crop(texture, accent=index in RIG_HEAD_PARTS[family]),
            angle=angle,
        )
        part["pivot"] = (0.0, 0.0)
        parts.append(part)
    if family == "cube" and "Size" in nbt:
        scale *= max(.5, min(4.0, (_number(nbt["Size"]) + 1) / 2))
    if _is_baby(nbt):
        scale *= .55
    return _scale_parts(parts, scale)


def source_mob_parts(nbt, *, kind, family, textures, fallback_scale=1.0):
    texture = _mob_texture(kind, nbt, textures)
    parts = model_parts(kind, nbt, texture, angle=_yaw(nbt))
    if parts:
        return parts
    report_issue("approximate entity model", kind)
    return dummy_parts(
        nbt, kind=kind, family=family, textures=textures, scale=fallback_scale,
    )
