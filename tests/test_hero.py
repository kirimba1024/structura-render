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


def test_plotter_is_closed_when_image_encoding_fails(monkeypatch):
    import pyvista as pv
    from structura_render import hero, legacy_input, mesh

    closed = []

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
            pass

        def reset_camera_clipping_range(self):
            pass

        def screenshot(self, **kwargs):
            return np.full((4, 4, 3), 255, dtype=np.uint8)

        def close(self):
            closed.append(True)

    monkeypatch.setattr(pv, "system_supports_plotting", lambda: True)
    monkeypatch.setattr(pv, "Plotter", Plotter)
    monkeypatch.setattr(legacy_input, "load_structure", lambda src, **kwargs: SimpleNamespace(size=(1, 1, 1)))
    monkeypatch.setattr(mesh, "voxel_state", lambda *args, **kwargs: (
        np.zeros((1, 1, 1), dtype=int), np.ones((1, 1, 1), dtype=bool), {0: "minecraft:stone"}, {},
    ))

    def fail(*args):
        raise OSError("encoding failed")

    monkeypatch.setattr(hero, "write_image", fail)
    with pytest.raises(OSError, match="encoding failed"):
        render_hero("source.nbt", "out.png", no_textures=True, window=4)
    assert closed == [True]
