import json
import math
from functools import lru_cache
from pathlib import Path

from PIL import Image

from .assets import ASSETS
from .entity_shapes import box


_DIRECT_LAYERS = frozenset("""
allay armadillo axolotl bat bee blaze bogged breeze camel cat cave_spider chicken cod
copper_golem cow creaking creeper dolphin donkey drowned elder_guardian enderman
endermite ender_dragon evoker fox frog ghast giant glow_squid goat guardian happy_ghast
hoglin horse husk illusioner iron_golem llama magma_cube mooshroom mule nautilus ocelot
panda parched parrot phantom pig piglin piglin_brute pillager polar_bear rabbit ravager
salmon sheep shulker silverfish skeleton skeleton_horse slime sniffer snow_golem spider
squid stray strider sulfur_cube tadpole trader_llama turtle vex villager vindicator
wandering_trader warden witch wither wither_skeleton wolf zoglin zombie zombie_horse
zombie_nautilus zombie_villager zombified_piglin
""".split())

ENTITY_LAYERS = {kind: kind.upper() for kind in _DIRECT_LAYERS}
ENTITY_LAYERS.update({
    "camel_husk": "CAMEL",
    "pufferfish": "PUFFERFISH_BIG",
    "tropical_fish": "TROPICAL_FISH_SMALL",
    "player": "PLAYER",
    "mannequin": "PLAYER",
})

BABY_LAYERS = frozenset("""
armadillo axolotl bee camel cat chicken cow dolphin donkey drowned fox glow_squid goat
happy_ghast hoglin horse husk llama mooshroom mule nautilus ocelot panda pig piglin
polar_bear rabbit sheep skeleton_horse sniffer squid strider trader_llama turtle wolf
zoglin zombie zombie_horse zombie_villager zombified_piglin
""".split())

VARIANT_LAYERS = {
    ("chicken", "cold"): "COLD_CHICKEN",
    ("cow", "cold"): "COLD_COW",
    ("cow", "warm"): "WARM_COW",
    ("pig", "cold"): "COLD_PIG",
    ("zombie_nautilus", "coral"): "ZOMBIE_NAUTILUS_CORAL",
}

OBJECT_LAYERS = frozenset({
    "ARMOR_STAND", "ARROW", "BAMBOO_CHEST_RAFT", "BAMBOO_RAFT", "END_CRYSTAL",
    "EVOKER_FANGS", "LEASH_KNOT", "LLAMA_SPIT", "MINECART", "OAK_BOAT",
    "OAK_CHEST_BOAT", "SHULKER_BULLET", "TRIDENT", "WIND_CHARGE", "WITHER_SKULL",
})

REQUIRED_LAYERS = frozenset(ENTITY_LAYERS.values()) | OBJECT_LAYERS | frozenset(
    f"{ENTITY_LAYERS[kind]}_BABY" for kind in BABY_LAYERS
) | frozenset(VARIANT_LAYERS.values()) | frozenset({"COLD_COW_BABY", "WARM_COW_BABY"})

CATALOG_PATH = Path(__file__).with_name("data") / "entity_models_26_2.json"


@lru_cache(maxsize=1)
def _catalog():
    try:
        return json.loads(CATALOG_PATH.read_text())["layers"]
    except (OSError, KeyError, json.JSONDecodeError):
        return {}


def _is_baby(nbt):
    for key in ("IsBaby", "is_baby"):
        if key in nbt:
            try:
                return bool(int(str(nbt[key])))
            except ValueError:
                pass
    try:
        return float(str(nbt.get("Age", nbt.get("age", 0)))) < 0
    except (TypeError, ValueError):
        return False


def model_layer(kind, nbt):
    variant = str(nbt.get("variant", nbt.get("Variant", ""))).split(":")[-1].lower()
    layer = VARIANT_LAYERS.get((kind, variant), ENTITY_LAYERS.get(kind))
    if layer is None:
        return None
    if _is_baby(nbt):
        baby = f"{layer}_BABY"
        if baby in _catalog():
            return baby
    return layer


def _matmul(left, right):
    return tuple(tuple(sum(left[row][k] * right[k][column] for k in range(4))
                       for column in range(4)) for row in range(4))


def _part_matrix(values):
    x, y, z, xr, yr, zr, xs, ys, zs = values
    cx, sx = math.cos(xr), math.sin(xr)
    cy, sy = math.cos(yr), math.sin(yr)
    cz, sz = math.cos(zr), math.sin(zr)
    translate = ((1, 0, 0, x), (0, 1, 0, y), (0, 0, 1, z), (0, 0, 0, 1))
    rotate_x = ((1, 0, 0, 0), (0, cx, -sx, 0), (0, sx, cx, 0), (0, 0, 0, 1))
    rotate_y = ((cy, 0, sy, 0), (0, 1, 0, 0), (-sy, 0, cy, 0), (0, 0, 0, 1))
    rotate_z = ((cz, -sz, 0, 0), (sz, cz, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1))
    scale = ((xs, 0, 0, 0), (0, ys, 0, 0), (0, 0, zs, 0), (0, 0, 0, 1))
    return _matmul(translate, _matmul(rotate_z, _matmul(rotate_y, _matmul(rotate_x, scale))))


IDENTITY = ((1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1))


def _point(matrix, point):
    value = (*point, 1.0)
    return tuple(sum(matrix[row][i] * value[i] for i in range(4)) for row in range(3))


def _quads(node, parent=IDENTITY):
    matrix = _matmul(parent, _part_matrix(node["transform"]))
    for cube in node["cubes"]:
        for quad in cube["quads"]:
            yield tuple(_point(matrix, vertex[:3]) for vertex in quad), tuple(
                (vertex[3], vertex[4]) for vertex in quad
            )
    for child in node["children"].values():
        yield from _quads(child, matrix)


@lru_cache(maxsize=None)
def _texture_image(texture):
    try:
        with Image.open(ASSETS / "textures" / f"{texture}.png") as source:
            return source.convert("RGBA")
    except OSError:
        return None


def model_parts(kind, nbt, texture, *, layer=None, baseline=24.016, ground=False,
                scale=1.0, outer_y_rotation=0.0, angle=0.0):
    layer = layer or model_layer(kind, nbt)
    root = _catalog().get(layer)
    image = _texture_image(texture)
    if root is None or image is None:
        return []

    width, height = image.size
    alpha = image.getchannel("A")
    turn = math.radians(outer_y_rotation)
    cosine, sine = math.cos(turn), math.sin(turn)
    quads = list(_quads(root))
    if not quads:
        return []
    if ground:
        baseline = max(y for vertices, _ in quads for _, y, _ in vertices)
    parts = []
    for vertices, uv in quads:
        pixel_uv = tuple((u * width, v * height) for u, v in uv)
        x0 = max(0, int(math.floor(min(u for u, _ in pixel_uv) + 1e-6)))
        y0 = max(0, int(math.floor(min(v for _, v in pixel_uv) + 1e-6)))
        x1 = min(width, int(math.ceil(max(u for u, _ in pixel_uv) - 1e-6)))
        y1 = min(height, int(math.ceil(max(v for _, v in pixel_uv) - 1e-6)))
        if x1 <= x0 or y1 <= y0 or alpha.crop((x0, y0, x1, y1)).getbbox() is None:
            continue
        world = []
        for x, y, z in vertices:
            x, z = x * cosine + z * sine, -x * sine + z * cosine
            world.append((x * scale / 16, (baseline - y) * scale / 16,
                          -z * scale / 16))
        relative_uv = tuple(((u - x0) / (x1 - x0), (v - y0) / (y1 - y0))
                            for u, v in pixel_uv)
        part = box((0, 0, 0), (0, 0, 0), texture, crop=(x0, y0, x1, y1), angle=angle)
        part["quads"] = (tuple(world),)
        part["quad_uvs"] = (relative_uv,)
        part["pivot"] = (0.0, 0.0)
        parts.append(part)
    return parts
