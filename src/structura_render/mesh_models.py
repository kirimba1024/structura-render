from dataclasses import dataclass, field

import numpy as np

from .block_geometry import ARM_AXIS, contains_water, is_post_family
from .block_model import block_elements, post_texture
from .diagnostics import report_issue
from .entities import structure_parts
from .entity_shapes import entity_decoration, entity_shape, nbt_sensitive, nbt_signature
from .model_textures import ModelFace, ModelTextures, resolve_special_parts as resolve_special_parts


@dataclass
class SpecialModel:
    index: int
    positions: np.ndarray
    parts: list[dict]
    fluid: str = ""


@dataclass
class PreparedModels:
    fallback: dict[int, dict[str, int]] = field(default_factory=dict)
    blocks: dict[int, list[ModelFace]] = field(default_factory=dict)
    specials: list[SpecialModel] = field(default_factory=list)
    entities: list = field(default_factory=list)
    hidden: set[int] = field(default_factory=set)

    @property
    def textured_indices(self):
        return set(self.fallback) | set(self.blocks) | {item.index for item in self.specials} | self.hidden


def instance_positions(src, state, index, name):
    groups = {}
    for pos in map(tuple, np.argwhere(state == index)):
        signature = nbt_signature(name, src.block_nbt.get(pos))
        groups.setdefault(signature, []).append(pos)
    return {signature: np.asarray(positions, dtype=np.intp) for signature, positions in groups.items()}


def instance_groups(src, state, index, name):
    groups = {}
    for signature, positions in instance_positions(src, state, index, name).items():
        mask = np.zeros(state.shape, dtype=bool)
        mask[tuple(positions.T)] = True
        groups[signature] = mask
    return groups


def _special_shapes(src, state, index, name, props, elements):
    if nbt_sensitive(name):
        groups = instance_positions(src, state, index, name)
        if set(groups) != {None}:
            factory = entity_decoration if elements else entity_shape
            return [(positions, factory(name, props, signature)) for signature, positions in groups.items()]
    shape = entity_shape(name, props) if not elements or name == "minecraft:bell" else None
    return [(np.argwhere(state == index), shape)] if shape is not None else []


def _fallback_faces(name, bank, atlas, *, post=False):
    if post:
        texture = post_texture(name)
        image = bank.read_texture(texture) if texture else None
        faces = {"all": image} if image is not None else bank.resolve(name)
        if not faces:
            report_issue("post texture unavailable; coloured fallback", name)
    else:
        report_issue("block model unavailable; approximate shape", name)
        faces = bank.resolve(name)
    return {key: atlas.add(image) for key, image in faces.items()} if faces else None


def prepare_models(src, state, index_names, index_props, bank, atlas):
    models = PreparedModels()
    textures = ModelTextures(bank, atlas)
    for index, name in index_names.items():
        props = index_props.get(index, {})
        if contains_water(name, props) and name not in ("minecraft:water", "minecraft:bubble_column"):
            water = textures.parts(entity_shape("minecraft:water", {}))
            models.specials.append(SpecialModel(index, np.argwhere(state == index), water, "minecraft:water"))
        post = is_post_family(name) and not all(direction in props for direction in ARM_AXIS)
        if post:
            faces = _fallback_faces(name, bank, atlas, post=True)
            if faces:
                models.fallback[index] = faces
            continue
        elements = block_elements(name, props)
        specials = _special_shapes(src, state, index, name, props, elements)
        for positions, shape in specials:
            if shape:
                models.specials.append(SpecialModel(index, positions, textures.parts(shape)))
            elif not elements:
                models.hidden.add(index)
        if elements:
            built = textures.faces(elements, name, props)
            if built:
                models.blocks[index] = built
        elif specials:
            continue
        elif elements == []:
            models.hidden.add(index)
        else:
            faces = _fallback_faces(name, bank, atlas)
            if faces:
                models.fallback[index] = faces
    models.entities = [(anchor, part) for anchor, parts in structure_parts(src)
                       for part in textures.parts(parts)]
    return models
