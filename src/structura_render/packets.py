from dataclasses import dataclass
from collections import defaultdict
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
    shading: Optional[np.ndarray] = None

    @property
    def nbytes(self):
        return sum(array.nbytes for array in (self.points, self.indices, self.uv, self.colors, self.shading) if array is not None)


def polygon_packets(points, indices, mode, *, uv=None, colors=None, image=None, color=(255, 255, 255, 255),
                    cull=False, texture_key=None, shading=None, max_bytes=PACKET_BYTES, max_vertices=PACKET_VERTICES):
    indices = np.asarray(indices)
    width = indices.shape[1]
    vertex_bytes = 12 + (8 if uv is not None else 0) + (4 if colors is not None else 0) + (2 if shading is not None else 0)
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
            np.ascontiguousarray(shading[used], dtype=np.uint8) if shading is not None else None,
        )


def textured_packets(mesh):
    from .shading import shaded_triangles

    digest = sha256(repr(mesh.image.shape).encode())
    digest.update(memoryview(np.ascontiguousarray(mesh.image)))
    identity = digest.digest()
    for value in np.unique(mesh.alpha_modes):
        mode = ALPHA_MODES[int(value)]
        indices = mesh.quads[mesh.alpha_modes == value]
        if mesh.shading is not None:
            indices = shaded_triangles(indices, mesh.shading)
        yield from polygon_packets(mesh.points, indices, mode, shading=mesh.shading,
                                   uv=mesh.uv, image=mesh.image, texture_key=identity, cull=mode != "BLEND")


def lod_packets(mesh, span=16):
    from .lod_rectangles import rectangle_pairs

    quads, _, rectangular = rectangle_pairs(mesh.points, mesh.triangles)
    colors = mesh.colors[quads]
    selected = rectangular & (colors == colors[:, :1]).all(axis=(1, 2))
    retained = np.r_[np.repeat(~selected, 2), np.ones(len(mesh.triangles) % 2, bool)]
    for indices in (quads[selected], mesh.triangles[retained]):
        if not len(indices):
            continue
        cells = np.floor(mesh.points[indices].mean(axis=1) / span).astype(np.int64)
        indices = indices[np.lexsort((cells[:, 2], cells[:, 1], cells[:, 0]))]
        opaque = (mesh.colors[indices, 3] == 255).all(axis=1)
        for mask, mode in ((opaque, 'OPAQUE'), (~opaque, 'BLEND')):
            yield from polygon_packets(mesh.points, indices[mask], mode, colors=mesh.colors, cull=mode == 'OPAQUE')


def merge_packets(packets):
    groups = defaultdict(list)
    for packet in packets:
        groups[(packet.mode, packet.indices.shape[1], packet.cull, packet.texture_key,
                packet.color, packet.uv is not None, packet.colors is not None, packet.shading is not None)].append(packet)
    for parts in groups.values():
        batch, size, vertices = [], 0, 0
        for packet in parts:
            if batch and (size + packet.nbytes > PACKET_BYTES or vertices + len(packet.points) > PACKET_VERTICES):
                yield _joined_packet(batch)
                batch, size, vertices = [], 0, 0
            batch.append(packet)
            size += packet.nbytes
            vertices += len(packet.points)
        if batch:
            yield _joined_packet(batch)


def _joined_packet(parts):
    if len(parts) == 1:
        return parts[0]
    indices, offset = [], 0
    for packet in parts:
        indices.append(packet.indices + offset)
        offset += len(packet.points)
    first = parts[0]
    return RenderPacket(np.concatenate([p.points for p in parts]), np.concatenate(indices), first.mode,
                        uv=np.concatenate([p.uv for p in parts]) if first.uv is not None else None,
                        colors=np.concatenate([p.colors for p in parts]) if first.colors is not None else None,
                        shading=np.concatenate([p.shading for p in parts]) if first.shading is not None else None,
                        image=first.image, texture_key=first.texture_key, color=first.color, cull=first.cull)


merge_lod_packets = merge_packets
