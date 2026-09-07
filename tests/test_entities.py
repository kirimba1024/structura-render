from types import SimpleNamespace

import pytest
from PIL import Image

from structura_render import AssetContext, entities, entity_models, textures
from structura_render.entity_shapes import entity_shape, nbt_signature
from structura_render.item_models import _static_model, item_id


def test_modern_and_legacy_facing_numbers_are_not_conflated():
    assert entities.facing_of({"Facing": 2}) == "north"
    assert entities.facing_of({"Facing": 5}) == "east"
    assert entities.facing_of({"facing": 0}) == "south"
    assert entities.facing_of({"Direction": 1}) == "west"


def test_outer_structure_position_wins_over_stale_entity_pos():
    record = {
        "pos": [2.25, 3.5, 4.75],
        "blockPos": [2, 3, 4],
    }
    nbt = {"Pos": [92.0, 93.0, 94.0], "TileX": 92, "TileY": 93, "TileZ": 94}
    assert entities.anchor_of(record, nbt, exact=True) == (2.25, 3.5, 4.75)
    assert entities.anchor_of(record, nbt) == (2, 3, 4)


def test_outer_fractional_position_is_hanging_fallback_before_inner_nbt():
    record = {"pos": [2.25, 3.5, 4.75]}
    nbt = {"Pos": [92.0, 93.0, 94.0], "TileX": 92, "TileY": 93, "TileZ": 94}
    assert entities.anchor_of(record, nbt) == (2, 3, 4)


def test_item_frame_keeps_item_and_all_eight_rotations(monkeypatch):
    monkeypatch.setattr(entities, "stack_texture", lambda stack: "item/apple")
    base = {"facing": 0, "Item": {"id": "minecraft:apple", "count": 1}}
    straight = entities.item_frame_parts(base, glowing=False)
    diagonal = entities.item_frame_parts({**base, "ItemRotation": 1}, glowing=False)
    assert len(straight) == len(diagonal) == 2
    assert straight[1]["texture"] == "item/apple"
    assert straight[1]["quads"] != diagonal[1]["quads"]


def test_floor_item_frame_uses_full_direction_encoding(monkeypatch):
    monkeypatch.setattr(entities, "stack_texture", lambda stack: "item/apple")
    parts = entities.item_frame_parts(
        {"Facing": 1, "Item": {"id": "minecraft:apple", "Count": 1}},
        glowing=False,
    )
    assert parts[0]["only_faces"] == ("up",)
    assert all(point[1] > 1 for point in parts[1]["quads"][0])


def test_unresolved_legacy_item_still_marks_the_frame_slot(monkeypatch):
    monkeypatch.setattr(entities, "stack_texture", lambda stack: None)
    parts = entities.item_frame_parts(
        {"Direction": 0, "Item": {"id": 351, "Count": 1}}, glowing=False,
    )
    assert len(parts) == 2
    assert parts[1]["texture"].startswith("block/")


def test_static_entities_keep_fractional_placement(monkeypatch):
    monkeypatch.setitem(
        entities.HANDLERS, "pig",
        lambda nbt: [entities.box((0, 0, 0), (1, 1, 1), "x")],
    )
    structure = SimpleNamespace(entities=[{
        "pos": [1.25, 2.0, 3.75],
        "blockPos": [1, 2, 3],
        "nbt": {"id": "minecraft:pig", "Pos": [99, 99, 99]},
    }])
    assert entities.structure_parts(structure)[0][0] == (1.25, 2.0, 3.75)


def test_armor_stand_visibility_and_equipment(monkeypatch):
    monkeypatch.setattr(
        entities, "stack_texture",
        lambda stack: "item/apple" if item_id(stack) else None,
    )
    visible = entities.armor_stand_parts({"ShowArms": 1})
    invisible = entities.armor_stand_parts({
        "Invisible": 1,
        "HandItems": [{"id": "minecraft:apple", "count": 1}],
    })
    assert len(visible) == 10
    assert len(invisible) == 1
    assert "quads" in invisible[0]


@pytest.mark.parametrize(
    "kind,minimum", [("pig", 7), ("sheep", 6), ("chicken", 8), ("cow", 9)],
)
def test_requested_mob_dummies_are_compound_models(kind, minimum):
    assert len(entities.HANDLERS[kind]({})) >= minimum


def test_approximate_rig_uses_an_opaque_crop_instead_of_the_whole_uv_sheet(
    tmp_path, monkeypatch,
):
    texture_path = tmp_path / "textures/entity/test.png"
    texture_path.parent.mkdir(parents=True)
    image = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
    for x in range(4):
        for y in range(4):
            image.putpixel((x, y), (30 + x, 60 + y, 90, 255))
    image.save(texture_path)
    monkeypatch.setenv("STRUCTURA_MINECRAFT_ASSETS", str(tmp_path))

    (part,) = entities.dummy_parts(
        {}, kind="test", family="cube", textures=("entity/test",),
    )

    assert part["crop"] == (0, 0, 4, 4)
    assert min(image.crop(part["crop"]).getchannel("A").getdata()) == 255


def test_official_zombie_layer_has_both_legacy_mirrored_legs():
    root = entity_models._catalog()["ZOMBIE"]
    assert {"left_leg", "right_leg"} <= root["children"].keys()
    for name in ("left_leg", "right_leg"):
        uv = [vertex[3:5] for cube in root["children"][name]["cubes"]
              for quad in cube["quads"] for vertex in quad]
        assert max(v for _, v in uv) <= .5


def test_bundled_model_catalog_covers_every_declared_layer():
    catalog = entity_models._catalog()
    assert entity_models.REQUIRED_LAYERS <= catalog.keys()
    assert all(
        entity_models.model_layer(kind, {}) in catalog
        for kind in entities.VANILLA_MOB_TYPES_26_2
    )


def test_baked_model_quads_keep_per_face_uv_and_giant_scale(tmp_path, monkeypatch):
    texture = tmp_path / "textures/entity/zombie/zombie.png"
    texture.parent.mkdir(parents=True)
    Image.new("RGBA", (64, 64), (40, 120, 60, 255)).save(texture)
    minecart_texture = tmp_path / "textures/entity/minecart/minecart.png"
    minecart_texture.parent.mkdir(parents=True)
    Image.new("RGBA", (64, 32), (80, 80, 80, 255)).save(minecart_texture)
    with AssetContext(tmp_path).activate():
        zombie = entity_models.model_parts("zombie", {}, "entity/zombie/zombie")
        giant = entity_models.model_parts("giant", {}, "entity/zombie/zombie")
        minecart = entity_models.model_parts(
            "minecart", {}, "entity/minecart/minecart", layer="MINECART", ground=True,
        )

    assert zombie and all("quad_uvs" in part for part in zombie)
    points = [point for part in giant for quad in part["quads"] for point in quad]
    assert 11.5 < max(point[1] for point in points) - min(point[1] for point in points) < 13
    grounded = [point[1] for part in minecart for quad in part["quads"] for point in quad]
    assert min(grounded) == pytest.approx(0)


def test_every_vanilla_26_2_mob_has_a_non_marker_rig():
    expected = set("""
        allay armadillo axolotl bat bee blaze bogged breeze camel camel_husk
        cat cave_spider chicken cod copper_golem cow creaking creeper dolphin donkey drowned
        elder_guardian ender_dragon enderman endermite evoker fox frog ghast giant glow_squid
        goat guardian happy_ghast hoglin horse husk illusioner iron_golem llama magma_cube
        mooshroom mule nautilus ocelot panda parched parrot phantom pig piglin
        piglin_brute pillager polar_bear pufferfish rabbit ravager salmon sheep shulker
        silverfish skeleton skeleton_horse slime sniffer snow_golem spider squid stray strider
        sulfur_cube tadpole trader_llama tropical_fish turtle vex villager vindicator
        wandering_trader warden witch wither wither_skeleton wolf zoglin zombie zombie_horse
        zombie_nautilus zombie_villager zombified_piglin
    """.split())
    assert expected == entities.VANILLA_MOB_TYPES_26_2
    assert expected <= entities.SUPPORTED_ENTITY_TYPES
    marker_bounds = ((-.2, 0, -.2), (.2, .4, .2))
    for kind in expected:
        parts = entities.HANDLERS[kind]({})
        assert parts, kind
        assert any((part["lo"], part["hi"]) != marker_bounds for part in parts), kind

    assert {"armor_stand", "mannequin", "player"} <= (
        entities.VANILLA_CREATURE_RIG_TYPES_26_2 - expected
    )
    assert "creaking_transient" not in entities.VANILLA_CREATURE_RIG_TYPES_26_2
    assert "creaking_transient" in entities.LEGACY_COMPAT_ENTITY_TYPES


def test_every_vanilla_non_mob_entity_has_an_explicit_handler():
    expected = set("""
        area_effect_cloud arrow bamboo_chest_raft bamboo_raft block_display boat
        breeze_wind_charge chest_boat chest_minecart command_block_minecart dragon_fireball
        egg end_crystal ender_pearl evoker_fangs experience_bottle experience_orb eye_of_ender
        falling_block fireball firework_rocket fishing_bobber furnace_minecart glow_item_frame
        hopper_minecart interaction item item_display item_frame leash_knot lightning_bolt
        lingering_potion llama_spit marker minecart ominous_item_spawner painting potion
        shulker_bullet small_fireball snowball spawner_minecart spectral_arrow splash_potion
        text_display tnt tnt_minecart trident wind_charge wither_skull
    """.split())
    woods = {"acacia", "birch", "cherry", "dark_oak", "jungle", "mangrove",
             "oak", "pale_oak", "spruce"}
    expected |= {f"{wood}_boat" for wood in woods}
    expected |= {f"{wood}_chest_boat" for wood in woods}
    assert expected <= entities.SUPPORTED_ENTITY_TYPES


def test_common_mob_skin_variants_are_selected_from_nbt(monkeypatch):
    monkeypatch.setattr(entities, "_asset", lambda *stems: stems[0])
    assert entities._mob_texture(
        "cat", {"variant": "minecraft:calico"}, ("entity/cat/cat_tabby",),
    ) == "entity/cat/cat_calico"
    assert entities._mob_texture(
        "horse", {"Variant": 256}, ("entity/horse/horse_brown",),
    ) == "entity/horse/horse_white"
    assert entities._mob_texture(
        "rabbit", {"RabbitType": 99}, ("entity/rabbit/rabbit_brown",),
    ) == "entity/rabbit/rabbit_caerbannog"
    assert entities._mob_texture(
        "wolf", {"variant": "minecraft:ashen", "Age": -1}, ("entity/wolf/wolf",),
    ) == "entity/wolf/wolf_ashen_baby"


def test_unknown_entity_still_leaves_a_visible_marker():
    structure = SimpleNamespace(entities=[{
        "pos": [1.5, 2.0, 3.5],
        "nbt": {"id": "minecraft:future_entity"},
    }])
    origin, parts = entities.structure_parts(structure)[0]
    assert origin == (1.5, 2.0, 3.5)
    assert parts[0]["texture"].startswith("block/")


def test_record_without_entity_id_is_ignored():
    structure = SimpleNamespace(entities=[{"pos": [1, 2, 3], "nbt": {}}])
    assert entities.structure_parts(structure) == []


def test_legacy_armor_stand_equipment_is_kept(monkeypatch):
    monkeypatch.setattr(
        entities, "stack_texture",
        lambda stack: "item/apple" if item_id(stack) else None,
    )
    parts = entities.armor_stand_parts({
        "Invisible": 1,
        "Equipment": [{"id": "minecraft:apple", "Count": 1}, {}, {}, {}, {}],
    })
    assert len(parts) == 1
    assert parts[0]["texture"] == "item/apple"


def test_modern_equipment_compound_is_kept(monkeypatch):
    monkeypatch.setattr(
        entities, "stack_texture",
        lambda stack: "item/apple" if item_id(stack) else None,
    )
    parts = entities.armor_stand_parts({
        "Invisible": 1,
        "equipment": {
            "head": {"id": "minecraft:apple", "count": 1},
            "mainhand": {"id": "minecraft:apple", "count": 1},
        },
    })
    assert len(parts) == 2


def test_item_stack_accepts_both_eras_and_rejects_empty_slots():
    assert item_id({"id": "minecraft:stone", "count": 1}) == "minecraft:stone"
    assert item_id({"id": "apple", "Count": 1}) == "minecraft:apple"
    assert item_id({"id": "minecraft:air", "count": 0}) is None


def test_modern_item_definition_uses_its_static_fallback():
    node = {
        "type": "minecraft:condition",
        "on_true": {"type": "minecraft:model", "model": "minecraft:item/raised"},
        "on_false": {"type": "minecraft:model", "model": "minecraft:item/base"},
    }
    assert _static_model(node) == "minecraft:item/base"


def test_decorated_pot_signature_preserves_four_ordered_sides():
    signature = nbt_signature("minecraft:decorated_pot", {
        "sherds": ["minecraft:angler_pottery_sherd", "minecraft:brick",
                   "minecraft:archer_pottery_sherd", "minecraft:brick"],
    })
    assert signature[0] == "pot"
    parts = entity_shape("minecraft:decorated_pot", {"facing": "north"}, signature)
    assert [part["texture"] for part in parts[:4]] == [
        "entity/decorated_pot/angler_pottery_pattern",
        "entity/decorated_pot/decorated_pot_side",
        "entity/decorated_pot/archer_pottery_pattern",
        "entity/decorated_pot/decorated_pot_side",
    ]


def test_unknown_sherd_pattern_falls_back_to_plain_pot_side(tmp_path, monkeypatch):
    plain = tmp_path / "textures/entity/decorated_pot/decorated_pot_side.png"
    plain.parent.mkdir(parents=True)
    Image.new("RGBA", (16, 16), (12, 34, 56, 255)).save(plain)
    monkeypatch.setenv("STRUCTURA_MINECRAFT_ASSETS", str(tmp_path))

    image = textures.TextureBank().read_asset(
        "entity/decorated_pot/future_pottery_pattern"
    )

    assert image is not None
    assert image.getpixel((0, 0)) == (12, 34, 56, 255)


def test_conduit_is_unwrapped_per_face_instead_of_stretching_its_sheet():
    (part,) = entity_shape("minecraft:conduit", {})
    assert set(part["faces"]) == {"up", "down", "north", "south", "east", "west"}
    assert part["lo"] == (5 / 16, 5 / 16, 5 / 16)
    assert part["hi"] == (11 / 16, 11 / 16, 11 / 16)


def test_unattached_hanging_sign_has_four_diagonal_chain_planes():
    parts = entity_shape("minecraft:oak_hanging_sign", {"rotation": "1", "attached": "false"})
    chains = parts[1:]
    assert len(chains) == 4
    assert all("corners" in part and part["angle"] == 22.5 for part in chains)
    assert all(set(part["faces"]) == {"north", "south"} for part in chains)


def test_attached_hanging_sign_uses_one_vertical_chain_sheet():
    parts = entity_shape("minecraft:oak_hanging_sign", {"rotation": "0", "attached": "true"})
    assert len(parts) == 2
    assert parts[1]["faces"] == {"north": (14, 6, 26, 12), "south": (26, 6, 38, 12)}
