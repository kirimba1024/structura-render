from functools import partial

from .assets import texture_asset as _asset
from .diagnostics import report_issue
from .entity_mobs import (
    _int_variant as _int_variant,
    _mob_texture as _mob_texture,
    _opaque_texture_tiles as _opaque_texture_tiles,
    _safe_texture_crop as _safe_texture_crop,
    dummy_parts as dummy_parts,
    source_mob_parts as source_mob_parts,
)
from .entity_models import model_parts
from .entity_objects import (
    AXIS as AXIS,
    DEPTH as DEPTH,
    DIRECTION as DIRECTION,
    FRAME_SIDE as FRAME_SIDE,
    HORIZONTAL as HORIZONTAL,
    NORMAL as NORMAL,
    _crossed_texture_parts as _crossed_texture_parts,
    _equipment_parts as _equipment_parts,
    _facing_part as _facing_part,
    _frame_bounds as _frame_bounds,
    _item_quad as _item_quad,
    _item_stack as _item_stack,
    _model_box as _model_box,
    _quad as _quad,
    _rotate_x as _rotate_x,
    _span as _span,
    _x_pose as _x_pose,
    armor_stand_parts as armor_stand_parts,
    baked_object_parts as baked_object_parts,
    block_carrier_parts as block_carrier_parts,
    boat_parts as boat_parts,
    end_crystal_parts as end_crystal_parts,
    facing_of as facing_of,
    item_frame_parts as item_frame_parts,
    loose_item_parts as loose_item_parts,
    marker_parts as marker_parts,
    minecart_parts as minecart_parts,
    painting_parts as painting_parts,
    painting_size as painting_size,
    primed_tnt_parts as primed_tnt_parts,
    sprite_entity_parts as sprite_entity_parts,
)
from .entity_state import (
    HANGING as HANGING,
    _flag as _flag,
    _is_baby as _is_baby,
    _number as _number,
    _plain as _plain,
    _values as _values,
    _yaw as _yaw,
    anchor_of as anchor_of,
)
from .mob_catalog import (
    _COMMON_MOBS as _COMMON_MOBS,
    COMMON_DUMMY_RIGS as COMMON_DUMMY_RIGS,
    DUMMY_RIGS as DUMMY_RIGS,
    MOB_SPECS as MOB_SPECS,
    RIG_HEAD_PARTS as RIG_HEAD_PARTS,
    _mob_specs as _mob_specs,
)
from .shape_geometry import (
    _scale_parts as _scale_parts,
    box as box,
)

HANDLERS = {
    "painting": painting_parts,
    "item_frame": lambda nbt: item_frame_parts(nbt, glowing=False),
    "glow_item_frame": lambda nbt: item_frame_parts(nbt, glowing=True),
    "armor_stand": armor_stand_parts,
    "player": lambda nbt: model_parts(
        "player", nbt, _asset("entity/player/wide/steve"), angle=_yaw(nbt),
    ),
    "mannequin": lambda nbt: model_parts(
        "mannequin", nbt, _asset("entity/player/wide/steve"), angle=_yaw(nbt),
    ),
    "item": loose_item_parts,
    "item_display": loose_item_parts,
}

for _kind, (_family, _textures, _scale) in {**MOB_SPECS, **_COMMON_MOBS}.items():
    HANDLERS[_kind] = partial(
        source_mob_parts, kind=_kind, family=_family, textures=_textures,
        fallback_scale=_scale,
    )

HANDLERS["creaking_transient"] = partial(
    dummy_parts,
    kind="creaking_transient",
    family="golem",
    textures=("entity/creaking/creaking",),
)

for _kind, (_layer, _textures) in {
    "arrow": ("ARROW", ("entity/projectiles/arrow",)),
    "spectral_arrow": (
        "ARROW", ("entity/projectiles/arrow_spectral", "entity/projectiles/arrow"),
    ),
    "trident": ("TRIDENT", ("entity/trident/trident",)),
    "wind_charge": ("WIND_CHARGE", ("entity/projectiles/wind_charge",)),
    "breeze_wind_charge": ("WIND_CHARGE", ("entity/projectiles/wind_charge",)),
    "evoker_fangs": ("EVOKER_FANGS", ("entity/illager/evoker_fangs",)),
    "llama_spit": ("LLAMA_SPIT", ("entity/llama/llama_spit",)),
    "shulker_bullet": ("SHULKER_BULLET", ("entity/shulker/spark",)),
    "wither_skull": ("WITHER_SKULL", ("entity/skeleton/wither_skeleton",)),
    "leash_knot": ("LEASH_KNOT", ("entity/lead_knot/lead_knot",)),
}.items():
    HANDLERS[_kind] = partial(
        baked_object_parts, layer=_layer, textures=_textures,
    )

for _kind, _texture in {
    "dragon_fireball": ("entity/enderdragon/dragon_fireball",),
    "experience_orb": ("entity/experience/experience_orb",),
    "fishing_bobber": ("entity/fishing/fishing_hook",),
}.items():
    HANDLERS[_kind] = partial(sprite_entity_parts, textures=_texture)

for _kind, _item in {
    "egg": "egg", "ender_pearl": "ender_pearl", "experience_bottle": "experience_bottle",
    "eye_of_ender": "ender_eye", "fireball": "fire_charge", "firework_rocket": "firework_rocket",
    "lingering_potion": "lingering_potion", "potion": "splash_potion",
    "small_fireball": "fire_charge", "snowball": "snowball",
    "splash_potion": "splash_potion",
}.items():
    HANDLERS[_kind] = partial(sprite_entity_parts, item=_item)

for _wood in ("acacia", "birch", "cherry", "dark_oak", "jungle", "mangrove",
              "oak", "pale_oak", "spruce"):
    HANDLERS[f"{_wood}_boat"] = partial(boat_parts, wood=_wood)
    HANDLERS[f"{_wood}_chest_boat"] = partial(boat_parts, wood=_wood, chest=True)

HANDLERS.update({
    "boat": boat_parts,
    "chest_boat": partial(boat_parts, chest=True),
    "bamboo_raft": partial(boat_parts, wood="bamboo"),
    "bamboo_chest_raft": partial(boat_parts, wood="bamboo", chest=True),
})

for _kind in (
    "minecart", "chest_minecart", "command_block_minecart", "furnace_minecart",
    "hopper_minecart", "spawner_minecart", "tnt_minecart",
):
    HANDLERS[_kind] = minecart_parts

HANDLERS.update({
    "block_display": block_carrier_parts,
    "falling_block": block_carrier_parts,
    "tnt": primed_tnt_parts,
    "end_crystal": end_crystal_parts,
    "ominous_item_spawner": marker_parts,
    "area_effect_cloud": marker_parts,
    "interaction": marker_parts,
    "lightning_bolt": marker_parts,
    "marker": marker_parts,
    "text_display": marker_parts,
})

VANILLA_MOB_TYPES_26_2 = frozenset(MOB_SPECS) | frozenset(_COMMON_MOBS)

VANILLA_CREATURE_RIG_TYPES_26_2 = VANILLA_MOB_TYPES_26_2 | {
    "armor_stand", "mannequin", "player",
}

LEGACY_COMPAT_ENTITY_TYPES = frozenset({
    "boat", "chest_boat", "creaking_transient", "player",
})

SUPPORTED_ENTITY_TYPES = frozenset(HANDLERS)


def structure_parts(structure):
    result = []
    for record in structure.entities:
        nbt = record.get("nbt") if hasattr(record, "get") else None
        if nbt is None:
            continue
        kind = _plain(nbt.get("id", ""))
        if not kind:
            report_issue("entity omitted", "missing id")
            continue
        handler = HANDLERS.get(kind, marker_parts)
        origin = anchor_of(record, nbt, exact=kind not in HANGING)
        if origin is None:
            report_issue("entity omitted; missing position", kind)
            continue
        parts = handler(nbt)
        if parts:
            result.append((origin, parts))
        else:
            report_issue("entity omitted; model/resources unavailable", kind)
    return result
