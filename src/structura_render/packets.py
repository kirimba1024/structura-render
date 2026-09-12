from dataclasses import dataclass
from hashlib import sha256
from typing import Optional

import numpy as np

from .geometry import ALPHA_MODES


PACKET_BYTES = 1024 * 1024
PACKET_VERTICES = 65536


@dataclass
class RenderPacket:
    points: np.ndarray
    indices: np.ndarray
    mode: str
    uv: Optional[np.ndarray] = None
    colors: Optional[np.ndarray] = None
    image: Optional[np.ndarray] = None
    texture_key: Optional[bytes] = None
    color: tuple = (255, 255, 255, 255)
    cull: bool = False

    @property
    def nbytes(self):
        return sum(array.nbytes for array in (self.points, self.indices, self.uv, self.colors) if array is not None)


def polygon_packets(points, indices, mode, *, uv=None, colors=None, image=None, color=(255, 255, 255, 255),
                    cull=False, texture_key=None, max_bytes=PACKET_BYTES, max_vertices=PACKET_VERTICES):
    indices = np.asarray(indices)
    width = indices.shape[1]
    vertex_bytes = 12 + (8 if uv is not None else 0) + (4 if colors is not None else 0)
    count = min(max_bytes // (width * (vertex_bytes + 4)), max_vertices // width)
    if count < 1:
        raise ValueError("A render packet must fit at least one polygon")
    for start in range(0, len(indices), count):
        used, inverse = np.unique(indices[start:start + count], return_inverse=True)
        yield RenderPacket(
            np.ascontiguousarray(points[used], dtype=np.float32),
            np.ascontiguousarray(inverse.reshape(-1, width), dtype=np.int32), mode,
            np.ascontiguousarray(uv[used], dtype=np.float32) if uv is not None else None,
            np.ascontiguousarray(colors[used], dtype=np.uint8) if colors is not None else None,
            image, texture_key, tuple(color), cull,
        )


def textured_packets(mesh):
    digest = sha256(repr(mesh.image.shape).encode())
    digest.update(memoryview(np.ascontiguousarray(mesh.image)))
    identity = digest.digest()
    for value in np.unique(mesh.alpha_modes):
        mode = ALPHA_MODES[int(value)]
        yield from polygon_packets(mesh.points, mesh.quads[mesh.alpha_modes == value], mode,
                                   uv=mesh.uv, image=mesh.image, texture_key=identity, cull=mode != "BLEND")
