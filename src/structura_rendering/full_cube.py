"""Lookup for whether a block's default shape is a full [0,0,0]-[16,16,16]
cube (build_full_cube_list.py) and, for those that are, whether its real
texture is actually fully opaque there (build_opaque_blocks.py, reads real
alpha channels) -- leaves/glass/ice/honey/slime/copper grates etc. are a
full-cube shape but not opaque, and must not occlude neighbor faces."""
import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
_shape_table = json.loads((DATA_DIR / "full_cube_blocks.json").read_text())
_opaque_table = json.loads((DATA_DIR / "opaque_blocks.json").read_text())


def is_full_cube_shape(name):
    return _shape_table.get(name, False)


def is_opaque_shape(name):
    return _opaque_table.get(name, True)


def is_occluder(name):
    return is_full_cube_shape(name) and is_opaque_shape(name)
