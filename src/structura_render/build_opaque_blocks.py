#!/usr/bin/env python3
"""For every block classified as a full cube (structura_render/data/full_cube_blocks.json),
determine whether it's actually fully opaque by reading the real alpha channel
of its real texture(s) -- not by name or by shape. A full-cube block whose
texture has any non-255 alpha (leaves, ice, honey, slime...) must not occlude
neighbor faces even though its shape is a full cube. Writes
structura_render/data/opaque_blocks.json, loaded by full_cube.is_opaque_shape()."""
import json
from pathlib import Path

import numpy as np
from PIL import Image

from .assets import ASSETS
from .block_model import DIRECTIONS, block_elements
from .build_full_cube_list import MULTIPART_SOLID_FULL_CUBES

TEXTURES = ASSETS / "textures/block"
FULL_CUBE_DATA = Path(__file__).resolve().parent / "data/full_cube_blocks.json"

_texture_opacity_cache = {}


def texture_is_opaque(texture_name):
    if texture_name not in _texture_opacity_cache:
        path = TEXTURES / f"{texture_name}.png"
        if not path.exists():
            _texture_opacity_cache[texture_name] = True
        else:
            image = Image.open(path).convert("RGBA")
            array = np.asarray(image)
            if array.shape[0] > array.shape[1]:
                array = array[: array.shape[1]]
            _texture_opacity_cache[texture_name] = bool((array[..., 3] == 255).all())
    return _texture_opacity_cache[texture_name]


def element_is_opaque_cube(element):
    if element["lo"] != (0.0, 0.0, 0.0) or element["hi"] != (1.0, 1.0, 1.0):
        return False
    faces = element["faces"]
    return all(d in faces and texture_is_opaque(faces[d]["texture"]) for d in DIRECTIONS)


def block_is_opaque(name):
    elements = block_elements(name, {})
    if elements is None:
        return name in MULTIPART_SOLID_FULL_CUBES
    return any(element_is_opaque_cube(element) for element in elements)


def main():
    full_cubes = json.loads(FULL_CUBE_DATA.read_text())
    results = {
        name: block_is_opaque(name)
        for name, is_full_cube in full_cubes.items()
        if is_full_cube
    }
    out_path = Path(__file__).resolve().parent / "data/opaque_blocks.json"
    out_path.write_text(json.dumps(results, indent=1, sort_keys=True) + "\n")
    print(f"{out_path} opaque={sum(results.values())}/{len(results)}")


if __name__ == "__main__":
    main()
