from dataclasses import dataclass
from typing import Optional

import numpy as np
from PIL import Image

from .block_geometry import flat_rgba
from .textures import tint_for


@dataclass(frozen=True)
class ModelFace:
    rect_index: int
    vertices: np.ndarray
    uv: np.ndarray
    cullface: Optional[str]


def _model_face(face, rect_index):
    u0, v0, u1, v1 = face["uv"]
    uv = np.array([[u0, 1 - v1], [u1, 1 - v1], [u1, 1 - v0], [u0, 1 - v0]])
    uv = np.roll(uv, face["uv_rotation"], axis=0)[list(face.get("uv_order", (0, 1, 2, 3)))]
    return ModelFace(rect_index, np.asarray(face["vertices"], dtype=np.float32), uv, face["cullface"])


class ModelTextures:
    def __init__(self, bank, atlas):
        self.bank = bank
        self.atlas = atlas
        self.block_tiles = {}

    def block_tile(self, texture, tint):
        key = texture, tint
        if key not in self.block_tiles:
            image = self.bank.read_texture(texture, tint)
            self.block_tiles[key] = self.atlas.add(image) if image is not None else None
        return self.block_tiles[key]

    def faces(self, elements, name, props):
        layers = {}
        for element in elements:
            for face in element["faces"].values():
                tint = tint_for(name, props) if face["tinted"] else None
                key = (tuple(map(tuple, face["vertices"])), tuple(face["uv"]), face["uv_rotation"],
                       tuple(face.get("uv_order", (0, 1, 2, 3))), face["cullface"])
                layers.setdefault(key, []).append((face, self.block_tile(face["texture"], tint)))
        if not any(tile is not None for group in layers.values() for _, tile in group):
            return []
        result = []
        fallback = None
        for group in layers.values():
            tiles = []
            for face, tile in group:
                if tile is None:
                    if fallback is None:
                        fallback = self.atlas.add(Image.new("RGBA", (1, 1), flat_rgba(name)))
                    tile = fallback
                tiles.append(tile)
            tile = tiles[0]
            if len(tiles) > 1:
                images = [self.atlas.images[index] for index in tiles]
                size = tuple(max(image.size[axis] for image in images) for axis in (0, 1))
                combined = Image.new("RGBA", size)
                for image in images:
                    combined.alpha_composite(image.resize(size, Image.Resampling.NEAREST))
                tile = self.atlas.add(combined)
            result.append(_model_face(group[0][0], tile))
        return result

    def special_tile(self, part, crop, turn=None):
        image = self.bank.read_asset(part["texture"], part["tint"], crop, part["alpha"])
        if image is None:
            image = Image.new("RGBA", (1, 1), (*(part["tint"] or (180, 185, 190)), part["alpha"]))
        if turn is not None:
            image = image.transpose(turn)
        return self.atlas.add(image)

    def parts(self, shape):
        result = []
        for part in shape:
            if part["faces"]:
                turns = part.get("turns") or {}
                tiles = {direction: self.special_tile(part, crop, turns.get(direction))
                         for direction, crop in part["faces"].items()}
                result.append({**part, "rect_by_face": tiles})
            else:
                result.append({**part, "rect_index": self.special_tile(part, part["crop"])})
        return result


def resolve_special_parts(shape, bank, atlas):
    return ModelTextures(bank, atlas).parts(shape)
