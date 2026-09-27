import numpy as np
from PIL import Image

from structura_render import AssetContext
from structura_render.entity_icons import OUTLINE, entity_icon


def opaque(height, width, value):
    pixels = np.full((height, width, 4), value, np.uint8)
    pixels[..., 3] = 255
    return pixels


def save_texture(root, name, pixels):
    path = root / f"textures/{name}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(pixels).save(path)


def test_player_icon_keeps_whole_texels_inside_a_silhouette_outline(tmp_path):
    texture = np.zeros((64, 64, 4), np.uint8)
    face = np.random.default_rng(3).integers(0, 255, (8, 8, 4), dtype=np.uint8)
    face[..., 3] = 255
    texture[8:16, 8:16] = face
    save_texture(tmp_path, "entity/player/wide/steve", texture)
    with AssetContext(tmp_path).activate():
        icon = entity_icon("player", {"id": "minecraft:player"})
    assert icon.shape == (18, 18, 4)
    assert np.array_equal(icon[1:17, 1:17], np.repeat(np.repeat(face, 2, axis=0), 2, axis=1))
    ring = np.ones((18, 18), bool)
    ring[1:17, 1:17] = False
    assert (icon[ring] == OUTLINE).all()


def test_icons_use_pre_26_texture_names_and_skip_reshaped_layouts(tmp_path):
    save_texture(tmp_path, "entity/cat/tabby", opaque(32, 64, 200))
    save_texture(tmp_path, "entity/rabbit/brown", opaque(32, 64, 200))
    save_texture(tmp_path, "block/structure_block", opaque(16, 16, 0))
    with AssetContext(tmp_path).activate():
        cat = entity_icon("cat", {"id": "minecraft:cat"})
        rabbit = entity_icon("rabbit", {"id": "minecraft:rabbit"})
    assert cat is not None and (cat[1:-1, 1:-1, :3] == 200).any()
    assert rabbit is None


def test_squid_icon_shows_spread_tentacles_below_the_body(tmp_path):
    save_texture(tmp_path, "entity/squid/squid", opaque(32, 64, 90))
    with AssetContext(tmp_path).activate():
        icon = entity_icon("squid", {"id": "minecraft:squid"})
    solid = icon[..., 3] > 0
    body = solid[1:17].sum(axis=1).max()
    assert solid[-3].sum() > body
