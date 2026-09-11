"""Sparse coloured voxel export with a MagicaVoxel scene graph."""

import struct
import warnings
from pathlib import Path

import numpy as np
from PIL import Image
from structura_core import AIR_NAMES
from structura_core.limits import DEFAULT_MAX_BLOCKS, check_volume

from .block_colours import block_color
from .diagnostics import RenderWarning
from .export_io import atomic_write
from .full_cube import is_full_cube_shape, is_opaque_shape


def _ints(*values):
    return struct.pack("<" + "i" * len(values), *values)


def _dict(**values):
    data = _ints(len(values))
    for key, value in values.items():
        for text in (key, str(value)):
            encoded = text.encode("utf-8")
            data += _ints(len(encoded)) + encoded
    return data


def _chunk(name, data=b"", children=b""):
    return name.encode("ascii") + _ints(len(data), len(children)) + data + children


def export_vox(src, output, *, max_blocks=DEFAULT_MAX_BLOCKS, strict=False):
    """Export one coloured cube per visible block; omit Minecraft entity models."""
    src.validate()
    check_volume(len(src.present), max_blocks)
    output = Path(output)
    if output.suffix.lower() != ".vox":
        raise ValueError("VOX output must end in .vox")
    used = sorted({index for index in src.present.values()
                   if src.palette[index] not in AIR_NAMES | {"minecraft:structure_void"}})
    if not used:
        raise ValueError("structure produced no visible voxels")
    colors = [block_color(src.palette[index], "family") for index in used]
    losses = []
    shapes = sorted({src.palette[index] for index in used if not is_full_cube_shape(src.palette[index])})
    if shapes:
        losses.append(f"{len(shapes)} non-cube or unknown block type(s) become full cubes ({', '.join(shapes[:5])})")
    if any(not is_opaque_shape(src.palette[index]) for index in used):
        losses.append("transparency replaced by opaque palette colours")
    if src.entities:
        losses.append(f"{len(src.entities)} entity model(s) omitted")
    if len(set(colors)) > 255:
        image = Image.fromarray(np.asarray([colors], dtype=np.uint8))
        reduced = image.quantize(colors=255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        colors = [tuple(color) for color in np.asarray(reduced.convert("RGB"))[0]]
        losses.append("colours quantized to at most 255 palette entries")
    if losses:
        message = "VOX approximation: " + "; ".join(losses)
        if strict:
            raise ValueError(message)
        warnings.warn(message, RenderWarning, stacklevel=2)
    palette = {color: index + 1 for index, color in enumerate(dict.fromkeys(colors))}
    indices = {index: palette[color] for index, color in zip(used, colors)}
    chunks = {}
    size = src.size[0], src.size[2], src.size[1]
    for (x, y, z), state in sorted(src.present.items()):
        if state not in indices:
            continue
        position = x, src.size[2] - 1 - z, y
        origin = tuple(value // 256 * 256 for value in position)
        chunks.setdefault(origin, bytearray()).extend((*[value % 256 for value in position], indices[state]))
    models, nodes, children = [], [], []
    for model_id, (origin, voxels) in enumerate(sorted(chunks.items())):
        extent = tuple(min(256, limit - start) for start, limit in zip(origin, size))
        models.extend((_chunk("SIZE", _ints(*extent)), _chunk("XYZI", _ints(len(voxels) // 4) + voxels)))
        transform, shape = 2 + model_id * 2, 3 + model_id * 2
        children.append(transform)
        translation = " ".join(str(start + length // 2) for start, length in zip(origin, extent))
        nodes.append(_chunk("nTRN", _ints(transform) + _dict(_name=f"Part {model_id + 1}") +
                            _ints(shape, -1, -1, 1) + _dict(_t=translation)))
        nodes.append(_chunk("nSHP", _ints(shape) + _dict() + _ints(1, model_id) + _dict()))
    graph = [_chunk("nTRN", _ints(0) + _dict(_name="Structure") + _ints(1, -1, -1, 1) + _dict()),
             _chunk("nGRP", _ints(1) + _dict() + _ints(len(children), *children))]
    rgba = b"".join(bytes((*color, 255)) for color in palette)
    rgba += bytes(1024 - len(rgba))
    data = b"VOX " + _ints(150) + _chunk("MAIN", children=b"".join(models + graph + nodes + [_chunk("RGBA", rgba)]))
    atomic_write(output, data)
    return output


def main(argv=None):
    from .export import export_cli

    export_cli("vox", argv)
