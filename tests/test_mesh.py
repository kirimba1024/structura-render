import numpy as np
from PIL import Image

from structura_render.mesh import Atlas, MAX_ATLAS_SIZE, upscale_atlas, uv_points_for_rect


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
