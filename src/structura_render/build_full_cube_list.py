#!/usr/bin/env python3
"""Determine, for every vanilla block, whether it's a real full opaque
cube (occupies [0,0,0]-[16,16,16] with all 6 faces defined) by resolving
its actual blockstate -> model -> parent chain from the game's own
files -- not a name/substring guess. Writes structura_render/data/full_cube_blocks.json,
loaded by full_cube.is_full_cube_shape()."""
import json
from pathlib import Path

from .assets import ASSETS
from .block_model import DIRECTIONS

BLOCKSTATES = ASSETS / "blockstates"
MODELS = ASSETS / "models/block"

MULTIPART_SOLID_FULL_CUBES = {
    "minecraft:brown_mushroom_block",
    "minecraft:red_mushroom_block",
    "minecraft:mushroom_stem",
    "minecraft:chiseled_bookshelf",
}

_model_cache = {}


def load_model(name):
    name = name.split(":", 1)[-1]
    if name.startswith("block/"):
        name = name[len("block/"):]
    if name in _model_cache:
        return _model_cache[name]
    path = MODELS / f"{name}.json"
    data = json.loads(path.read_text()) if path.exists() else None
    _model_cache[name] = data
    return data


def resolve_elements(model_name, depth=0):
    if depth > 10:
        return None
    data = load_model(model_name)
    if data is None:
        return None
    if "elements" in data:
        return data["elements"]
    parent = data.get("parent")
    return resolve_elements(parent, depth + 1) if parent else None


def is_full_cube_element(element):
    if element.get("from") != [0, 0, 0] or element.get("to") != [16, 16, 16]:
        return False
    faces = element.get("faces", {})
    return all(d in faces for d in DIRECTIONS)


def is_full_cube_elements(elements):
    return bool(elements) and any(is_full_cube_element(el) for el in elements)


def variant_model_name(blockstate):
    first = next(iter(blockstate["variants"].values()))
    if isinstance(first, list):
        first = first[0]
    return first.get("model")


def classify_full_cube(name, blockstate):
    if "multipart" in blockstate:
        return name in MULTIPART_SOLID_FULL_CUBES
    model_name = variant_model_name(blockstate)
    return is_full_cube_elements(resolve_elements(model_name))


def main():
    results = {}
    for path in sorted(BLOCKSTATES.glob("*.json")):
        name = f"minecraft:{path.stem}"
        blockstate = json.loads(path.read_text())
        results[name] = classify_full_cube(name, blockstate)

    out_dir = Path(__file__).resolve().parent / "data"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "full_cube_blocks.json"
    out_path.write_text(json.dumps(results, indent=1, sort_keys=True) + "\n")
    print(f"{out_path} full_cubes={sum(results.values())}/{len(results)}")


if __name__ == "__main__":
    main()
