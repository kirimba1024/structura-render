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


@pytest.mark.parametrize('view', VIEWS)
def test_overlay_masks_use_same_axis_orientation_as_blocks(view):
    from structura_render import ProjectionOverlays
    from structura_render.projections import orient
    src = sample()
    mask = np.zeros(src.size, dtype=bool)
    mask[0, 2, 3] = True
    before = np.asarray(render_projection(src, view=view, scale=1))
    overlays = ProjectionOverlays(cavern_aura=mask)
    after = np.asarray(render_projection(src, view=view, scale=1, overlays=overlays))
    expected_mask = orient(mask.any(axis=VIEWS[view][0]), view)
    np.testing.assert_array_equal(np.any(before != after, axis=2), expected_mask)
    np.testing.assert_array_equal(after[expected_mask],
                                  (before[expected_mask] * .86 + np.array([88, 132, 235]) * .14).astype(np.uint8))
    assert mask.sum() == 1


def test_envelope_contour_and_translucent_background():
    from structura_render import ProjectionOverlays
    src = sample()
    src.present.clear()
    envelope = np.ones(src.size, dtype=bool)
    image = render_projection(src, scale=1, transparent=True, overlays=ProjectionOverlays(envelope=envelope))
    assert image.getpixel((0, 0)) == (152, 60, 180, 255)
    assert image.getpixel((1, 2)) == (190, 76, 226, 66)


@pytest.mark.parametrize('view', ['north', 'south', 'west', 'east'])
def test_ground_level_is_two_cells_on_two_off(view):
    from structura_render import ProjectionOverlays
    src = sample((7, 4, 9))
    src.present.clear()
    before = np.asarray(render_projection(src, view=view, scale=1))
    after = np.asarray(render_projection(src, view=view, scale=1, overlays=ProjectionOverlays(ground_y=1)))
    changed = np.any(before != after, axis=2)
    expected = np.zeros(changed.shape, dtype=bool)
    expected[2, (np.arange(changed.shape[1]) // 2) % 2 == 0] = True
    np.testing.assert_array_equal(changed, expected)


@pytest.mark.parametrize('options', [
    {'envelope': np.zeros((1, 2, 3), dtype=bool)},
    {'aura': np.zeros((3, 4, 5), dtype=np.uint8)}, {'ground_y': True},
    {'ground_y': -1}, {'ground_y': 4}, {'ground_y': 1.5},
])
def test_malformed_overlays_are_rejected(options):
    from structura_render import ProjectionOverlays
    with pytest.raises(ValueError):
        render_projection(sample(), overlays=ProjectionOverlays(**options))


def test_overlay_cli_and_oversized_archive_preserve_existing_output(tmp_path):
    from structura_core import save_structure

    from structura_render.projections import main
    src = sample()
    source, masks, output = [tmp_path / name for name in ('scene.nbt', 'masks.npz', 'out.png')]
    save_structure(src, source, src.size)
    np.savez_compressed(masks, envelope=np.ones(src.size, dtype=bool))
    main([str(source), str(output), '--overlays', str(masks), '--ground-y', '1'])
    before = output.read_bytes()
    np.savez_compressed(masks, envelope=np.ones(100_000, dtype=bool))
    with pytest.raises(SystemExit):
        main([str(source), str(output), '--overlays', str(masks), '--max-blocks', '60'])
    assert output.read_bytes() == before


def test_invalid_overlay_archive_reports_a_value_error(tmp_path):
    from structura_render.overlays import load_overlays
    path = tmp_path / 'broken.npz'
    path.write_bytes(b'broken zip')
    with pytest.raises(ValueError, match='NPZ'):
        load_overlays(path, (1, 1, 1), max_blocks=1)
