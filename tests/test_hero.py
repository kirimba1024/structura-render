from types import SimpleNamespace

import numpy as np
import pytest

from structura_render.hero import render_hero


@pytest.mark.parametrize("options", [
    {"window": 0}, {"window": True}, {"window": 1.2}, {"window": 100_000},
    {"zoom": 0}, {"zoom": float("nan")}, {"azimuth": float("inf")},
    {"elevation": float("nan")}, {"color_mode": "missing"},
])
def test_invalid_options_fail_without_loading_a_source(options):
    with pytest.raises(ValueError):
        render_hero("does-not-exist.nbt", **options)


@pytest.mark.parametrize("entity_only", [False, True])
def test_plotter_is_closed_when_image_encoding_fails(monkeypatch, tmp_path, entity_only):
    import pyvista as pv
    from amulet_nbt import CompoundTag, DoubleTag, IntTag, ListTag, StringTag
    from structura_core import Structure, parse_state
    from structura_render import AssetContext, hero

    closed = []
    meshes = []

    class Plotter:
        bounds = (0, 1, 0, 1, 0, 1)
        camera = SimpleNamespace(view_angle=30, zoom=lambda value: None)

        def __init__(self, **kwargs):
            pass

        def set_background(self, *args):
            pass

        def enable_depth_peeling(self, **kwargs):
            pass

        def add_mesh(self, *args, **kwargs):
            meshes.append(args[0])

        def reset_camera_clipping_range(self):
            pass

        def screenshot(self, **kwargs):
            return np.full((4, 4, 3), 255, dtype=np.uint8)

        def close(self):
            closed.append(True)

    monkeypatch.setattr(pv, "system_supports_plotting", lambda: True)
    monkeypatch.setattr(pv, "Plotter", Plotter)
    source = Structure.from_root(CompoundTag({
        "DataVersion": IntTag(3955),
        "size": ListTag([IntTag(1)] * 3),
        "palette": ListTag([parse_state("minecraft:stone")]),
        "blocks": ListTag(), "entities": ListTag(),
    }))
    source.present = {(0, 0, 0): 0}
    if entity_only:
        source.present.clear()
        source.entities = [CompoundTag({
            "pos": ListTag([DoubleTag(.5), DoubleTag(0), DoubleTag(.5)]),
            "blockPos": ListTag([IntTag(0)] * 3),
            "nbt": CompoundTag({"id": StringTag("minecraft:tnt")}),
        })]

    def fail(*args):
        raise OSError("encoding failed")

    monkeypatch.setattr(hero, "write_image", fail)
    with AssetContext(tmp_path).activate(), pytest.raises(OSError, match="encoding failed"):
        render_hero(source, "out.png", no_textures=True, window=4)
    assert closed == [True]
    assert sum(mesh.n_cells for mesh in meshes) == 6
