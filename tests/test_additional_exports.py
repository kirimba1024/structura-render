import struct
from xml.etree import ElementTree as ET

import numpy as np
import pytest
from PIL import Image, features
from amulet_nbt import CompoundTag, IntTag, ListTag, StringTag

from structura_core import Mcstructure, Structure, convert_structure, parse_state
from structura_render import ProjectionOverlays, RenderWarning, export_structure, render_projection, render_svg


def source(size=(3, 4, 5)):
    src = Structure.from_root(CompoundTag({
        "DataVersion": IntTag(3955), "size": ListTag([IntTag(v) for v in size]),
        "palette": ListTag([parse_state(name) for name in ("minecraft:stone", "minecraft:oak_planks")]),
        "blocks": ListTag(), "entities": ListTag(),
    }))
    src.present = {(0, 0, 0): 0, (2, 3, 4): 1}
    return src


@pytest.mark.parametrize("view", ["top", "bottom", "north", "south", "west", "east"])
@pytest.mark.parametrize("depth", [None, (0, 1)])
def test_svg_cells_match_raster_visibility_and_orientation(view, depth):
    src = source()
    image = render_projection(src, scale=1, view=view, depth=depth)
    root = ET.fromstring(render_svg(src, scale=1, view=view, depth=depth))
    width, height = image.size
    assert root.attrib["viewBox"] == f"0 0 {width} {height}"
    canvas = np.full((height, width, 3), 246, dtype=np.uint8)
    group = root.find("{*}g[@id='blocks']")
    for element in group:
        x, y, w, h = (int(element.attrib[key]) for key in ("x", "y", "width", "height"))
        color = bytes.fromhex(element.attrib["fill"][1:])
        canvas[y:y+h, x:x+w] = tuple(color)
    np.testing.assert_array_equal(canvas, image)
    assert root.find(".//{*}image") is None


def test_svg_merges_a_solid_plan_and_keeps_editable_overlay_groups():
    src = source((40, 4, 40))
    src.present = {(x, 0, z): 0 for x in range(40) for z in range(40)}
    mask = np.zeros(src.size, dtype=bool)
    mask[2:8, 1:3, 4:10] = True
    root = ET.fromstring(render_svg(src, overlays=ProjectionOverlays(envelope=mask, cavern_aura=mask, ground_y=0)))
    assert len(root.find("{*}g[@id='blocks']")) == 1
    assert root.find("{*}g[@id='envelope']/{*}g/{*}path") is not None
    assert root.find("{*}g[@id='cavern_aura']") is not None
    side = ET.fromstring(render_svg(src, view="north", overlays=ProjectionOverlays(ground_y=0)))
    assert side.find("{*}path[@id='ground']").attrib["stroke-dasharray"] == "2 2"


@pytest.mark.parametrize("options", [{"max_elements": 1}, {"max_pixels": 1}, {"depth": (0, 0)}, {"max_elements": True}])
def test_svg_failure_preserves_existing_output(tmp_path, options):
    output = tmp_path / "plan.svg"
    output.write_text("previous")
    with pytest.raises(ValueError):
        render_svg(source(), output, **options)
    assert output.read_text() == "previous"


def test_svg_clips_overlays_and_escapes_text():
    src = source()
    mask = np.zeros(src.size, dtype=bool)
    mask[0, 3, 0] = True
    root = ET.fromstring(render_svg(src, transparent=True, depth=(0, 2), overlays=ProjectionOverlays(envelope=mask)))
    group = root.find("{*}g[@id='envelope']")
    assert group.find("{*}rect") is None
    assert root.find("{*}rect") is None


def test_svg_caption_escapes_xml_and_counts_towards_pixel_limit(tmp_path):
    title = '<Дом> & "план"'
    root = ET.fromstring(render_svg(source(), scale=1, title=title, max_pixels=21))
    assert root.find("{*}text[@id='caption']").text == title
    assert root.find("{*}title").text == title
    assert root.attrib["viewBox"] == "0 -2 3 7"
    with pytest.raises(ValueError, match="max_pixels"):
        render_svg(source(), scale=1, title=title, max_pixels=20)
    output = tmp_path / "title.svg"
    output.write_text("previous")
    for invalid in ("bad\x00", "bad\ud800", "bad\ufffe"):
        with pytest.raises(ValueError, match="XML"):
            render_svg(source(), output, title=invalid)
        assert output.read_text() == "previous"


def vox_chunks(data):
    assert data[:8] == b"VOX " + struct.pack("<i", 150)
    assert data[8:12] == b"MAIN"
    assert struct.unpack_from("<ii", data, 12) == (0, len(data) - 20)
    offset = 20
    while offset < len(data):
        name = data[offset:offset + 4].decode("ascii")
        size, children = struct.unpack_from("<ii", data, offset + 4)
        assert children == 0
        yield name, data[offset + 12:offset + 12 + size]
        offset += 12 + size
    assert offset == len(data)


def test_vox_preserves_sparse_grid_across_256_cell_model_boundaries(tmp_path):
    src = source((600, 4, 600))
    src.present = {(0, 0, 0): 0, (599, 3, 599): 1}
    output = export_structure(src, tmp_path / "large.vox", strict=True, max_blocks=2, max_voxels=1)
    data = output.read_bytes()
    chunks = list(vox_chunks(data))
    dimensions = [struct.unpack("<iii", payload) for name, payload in chunks if name == "SIZE"]
    assert dimensions == [(256, 88, 4), (88, 256, 4)]
    models = [payload for name, payload in chunks if name == "XYZI"]
    assert all(struct.unpack_from("<i", model)[0] == 1 for model in models)
    assert tuple(models[0][4:7]) == (0, 87, 0)
    assert tuple(models[1][4:7]) == (87, 0, 3)
    assert len([1 for name, _ in chunks if name == "nTRN"]) == 3
    assert len([1 for name, _ in chunks if name == "nSHP"]) == 2
    assert len(data) < 2000
    export_structure(src, output, strict=True)
    assert output.read_bytes() == data


def test_vox_approximations_are_reported_and_strict_is_atomic(tmp_path):
    src = source()
    src.palette_raw[0] = parse_state("minecraft:oak_stairs[facing=north]")
    src.validate()
    output = tmp_path / "model.vox"
    output.write_bytes(b"previous")
    with pytest.raises(ValueError, match="full cubes"):
        export_structure(src, output, strict=True)
    assert output.read_bytes() == b"previous"
    with pytest.warns(RenderWarning, match="full cubes"):
        export_structure(src, output)
    assert output.read_bytes().startswith(b"VOX ")


def test_vox_reports_loss_of_transparency(tmp_path):
    src = source()
    src.palette_raw[0] = parse_state("minecraft:glass")
    with pytest.raises(ValueError, match="transparency"):
        export_structure(src, tmp_path / "glass.vox", strict=True)


def test_strict_export_rejects_bedrock_input_losses_before_writing(tmp_path):
    pytest.importorskip("amulet")
    path = convert_structure(source(), tmp_path / "native.mcstructure", strict=True)
    document = Mcstructure(path)
    document.entities.append(CompoundTag({"identifier": StringTag("minecraft:pig")}))
    document.save(path)
    output = tmp_path / "model.vox"
    output.write_bytes(b"previous")
    with pytest.raises(ValueError, match="entities omitted"):
        export_structure(path, output, strict=True)
    assert output.read_bytes() == b"previous"


def test_lossless_webp_recipe_preserves_projection_pixels(tmp_path):
    if not features.check("webp"):
        pytest.skip("Pillow was built without WebP")
    image = render_projection(source(), view="north", scale=2)
    output = tmp_path / "floor.webp"
    image.save(output, lossless=True, method=6)
    with Image.open(output) as restored:
        assert restored.format == "WEBP"
        np.testing.assert_array_equal(restored.convert("RGB"), image)
