import numpy as np
import pytest
from amulet_nbt import CompoundTag, IntTag, ListTag
from PIL import Image

from structura_core import Structure, parse_state
from structura_render import render_projection, render_projections
from structura_render.projections import VIEWS, render_view


def sample(size=(3, 4, 5)):
    src = Structure.from_root(CompoundTag({
        "DataVersion": IntTag(3955), "size": ListTag([IntTag(v) for v in size]),
        "palette": ListTag([parse_state(f"minecraft:{name}") for name in ("stone", "dirt", "air")]),
        "blocks": ListTag(), "entities": ListTag(),
    }))
    src.present = {(0, 0, 0): 0, (2, 0, 0): 1, (0, 3, 4): 1, (2, 3, 4): 0, (1, 1, 2): 2}
    return src


@pytest.mark.parametrize("view", VIEWS)
@pytest.mark.parametrize("mode", ["family", "block"])
def test_sparse_projection_matches_existing_dense_reference(view, mode):
    src = sample()
    dense = np.full(src.size, -1, dtype=np.int32)
    for pos, index in src.present.items():
        if index != 2:
            dense[pos] = index
    expected = render_view(dense, src.palette, view, mode)
    actual = render_projection(src, view=view, color_mode=mode, scale=1)
    np.testing.assert_array_equal(np.asarray(actual), expected)


def test_projection_does_not_allocate_a_volume():
    src = sample((3, 1_000_000_000, 5))
    image = render_projection(src, view="top", scale=1)
    assert image.size == (3, 5)


@pytest.mark.parametrize("options", [
    {"scale": 0}, {"scale": True}, {"scale": 1.2}, {"view": "missing"},
    {"color_mode": "missing"}, {"max_pixels": 0}, {"max_pixels": 3},
])
def test_invalid_or_oversized_images_fail_before_allocation(options):
    with pytest.raises(ValueError):
        render_projection(sample(), **options)


def test_sheet_matches_expected_layout_and_saves_atomically(tmp_path):
    output = tmp_path / "images/sheet.png"
    image = render_projections(sample(), output, scale=2)
    assert image.size == (146, 148)
    with Image.open(output) as saved:
        np.testing.assert_array_equal(saved, image)
    before = output.read_bytes()
    with pytest.raises(ValueError, match="max_pixels"):
        render_projections(sample(), output, scale=2, max_pixels=image.width * image.height - 1)
    assert output.read_bytes() == before


def test_empty_view_list_is_rejected():
    with pytest.raises(ValueError, match="at least one"):
        render_projections(sample(), views=[])


def test_transparent_projection_uses_alpha_for_empty_cells():
    image = render_projection(sample(), view="top", scale=1, transparent=True)
    assert image.mode == "RGBA"
    assert image.getpixel((0, 0))[3] == 255
    assert image.getpixel((1, 2)) == (0, 0, 0, 0)


def test_structure_void_is_not_visible():
    src = sample()
    src.palette_raw.append(parse_state("minecraft:structure_void"))
    src.present[1, 1, 2] = 3
    src.validate()
    assert render_projection(src, scale=1, transparent=True).getpixel((1, 2))[3] == 0
