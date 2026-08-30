"""Hand-authored bounding shapes for vanilla blocks whose real geometry is
built by a Java BlockEntityRenderer, not the blockstate/model JSON system
block_model.py reads -- there is no local file for these to read. Chest/skull/
bed use the block's well-established, long-unchanged real hitbox, not a guess;
banner is a deliberate rough stand-in (thin post/plate), not its real hanging-
cloth shape -- not worth the extra fidelity here. Rendered as a plain flat
color, not textured -- the real per-family texture atlases (entity/chest,
entity/skull, entity/banner) aren't part of this project's data yet."""

CHEST_BOX = ((0.0625, 0.0, 0.0625), (0.9375, 0.875, 0.9375))
SKULL_BOX = ((0.25, 0.0, 0.25), (0.75, 0.5, 0.75))
WALL_SKULL_BOX = ((0.25, 0.25, 0.5), (0.75, 0.75, 1.0))
BED_BOX = ((0.0, 0.0, 0.0), (1.0, 0.5625, 1.0))
BANNER_BOX = ((0.4375, 0.0, 0.4375), (0.5625, 1.0, 0.5625))
WALL_BANNER_BOX = ((0.125, 0.125, 0.75), (0.875, 0.875, 1.0))
DECORATED_POT_BOX = ((0.0625, 0.0, 0.0625), (0.9375, 1.0, 0.9375))
HANGING_SIGN_BOX = ((0.0, 0.25, 0.375), (1.0, 0.75, 0.625))
FULL_BOX = ((0.0, 0.0, 0.0), (1.0, 1.0, 1.0))
SIGN_BOX = ((0.4375, 0.0, 0.4375), (0.5625, 0.75, 0.5625))
WALL_SIGN_BOX = ((0.0, 0.3125, 0.875), (1.0, 0.75, 1.0))

CHEST_NAMES = {"minecraft:chest", "minecraft:trapped_chest", "minecraft:ender_chest"}
SKULL_SUFFIXES = ("_skull", "_head")
WALL_SKULL_SUFFIXES = ("_wall_skull", "_wall_head")


def entity_shape(name, props):
    base = name.split(":", 1)[-1]
    if name in CHEST_NAMES:
        return CHEST_BOX
    if base.endswith(WALL_SKULL_SUFFIXES):
        return WALL_SKULL_BOX
    if base.endswith(SKULL_SUFFIXES):
        return SKULL_BOX
    if base.endswith("_bed"):
        return BED_BOX
    if base.endswith("_wall_banner"):
        return WALL_BANNER_BOX
    if base.endswith("_banner"):
        return BANNER_BOX
    if name == "minecraft:decorated_pot":
        return DECORATED_POT_BOX
    if base.endswith("_hanging_sign"):
        return HANGING_SIGN_BOX
    if base.endswith("_wall_sign"):
        return WALL_SIGN_BOX
    if base.endswith("_sign"):
        return SIGN_BOX
    if name == "minecraft:chiseled_bookshelf":
        return FULL_BOX
    return None
