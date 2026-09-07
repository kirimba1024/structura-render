import itertools

import numpy as np
import pytest

from structura_render.camera import framing_distance


@pytest.mark.parametrize("size", [(1, 1, 1), (1, 20, 2), (40, 1, 2)])
@pytest.mark.parametrize("aspect", [.5, 1., 1.5])
def test_fitted_camera_contains_every_corner_in_both_axes(size, aspect):
    vertical_fov = 30
    distance = framing_distance(size, vertical_fov, aspect)
    azimuth, elevation = np.radians([35, 35])
    direction = np.array([np.cos(elevation) * np.sin(azimuth), np.sin(elevation),
                          np.cos(elevation) * np.cos(azimuth)])
    forward = -direction
    right = np.cross(forward, [0, 1, 0])
    right /= np.linalg.norm(right)
    up = np.cross(right, forward)
    corners = np.asarray(list(itertools.product(*[(-v / 2, v / 2) for v in size])))
    relative = corners - distance * direction
    depth = relative @ forward
    vertical = np.tan(np.radians(vertical_fov) / 2)

    assert np.all(depth > 0)
    assert np.all(np.abs(relative @ up) < depth * vertical)
    assert np.all(np.abs(relative @ right) < depth * vertical * aspect)
