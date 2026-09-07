import numpy as np
from PIL import Image

from structura_render.mesh import (
    MAX_ATLAS_SIZE,
    Atlas,
    upscale_atlas,
    uv_points_for_rect,
)
from structura_render.textures import WATER_ALPHA, TextureBank


def test_atlas_deduplicates_equal_pixels_from_distinct_images():
    atlas = Atlas()
    first = Image.new("RGBA", (8, 8), (1, 2, 3, 4))
    duplicate = first.copy()

    assert atlas.add(first) == atlas.add(duplicate)
    assert len(atlas.images) == 1


def test_atlas_upscale_stays_within_common_gpu_texture_limit():
    image = Image.new("RGBA", (600, 500))

    result = upscale_atlas(image)

    assert max(result.size) <= MAX_ATLAS_SIZE
    assert result.size == (1800, 1500)


def test_model_uv_points_keep_vertex_order_inside_atlas_tile():
    result = uv_points_for_rect((.25, .5, .1, .3), ((0, 0), (1, 0), (1, 1), (0, 1)))

    np.testing.assert_allclose(result, [
        [.25, .3], [.5, .3], [.5, .1], [.25, .1],
    ])


def test_water_stays_visible_against_a_light_preview_background(monkeypatch):
    bank = TextureBank()
    water = Image.new("RGBA", (16, 16), (220, 240, 255, 180))
    monkeypatch.setattr(bank, "_read", lambda _stem: water)

    image = bank.resolve("minecraft:water")["all"]

    assert np.asarray(image)[..., 3].min() == WATER_ALPHA


def test_atlas_preserves_hd_pixels_rectangular_images_and_padding():
    atlas = Atlas()
    pixels = np.arange(64 * 32 * 4, dtype=np.uint8).reshape(32, 64, 4)
    atlas.add(Image.fromarray(pixels))
    atlas.add(Image.new('RGBA', (8, 24), (11, 22, 33, 44)))
    image, rects = atlas.build(max_size=128)
    for original, (u0, u1, v0, v1) in zip(atlas.images, rects):
        x0, x1 = round(u0 * image.shape[1]), round(u1 * image.shape[1])
        y0, y1 = round((1 - v1) * image.shape[0]), round((1 - v0) * image.shape[0])
        np.testing.assert_array_equal(image[y0:y1, x0:x1], original)
        np.testing.assert_array_equal(image[y0 - 1, x0:x1], np.asarray(original)[0])


def test_atlas_overflow_rejected_before_output_allocation(monkeypatch):
    import pytest
    atlas = Atlas()
    atlas.add(Image.new('RGBA', (128, 128)))
    def forbidden(*args, **kwargs):
        raise AssertionError('oversized allocation')
    monkeypatch.setattr(np, 'zeros', forbidden)
    with pytest.raises(ValueError, match='max_atlas_size'):
        atlas.build(max_size=128)
