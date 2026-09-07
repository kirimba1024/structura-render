"""Perspective camera fitting shared by image and scene exporters."""

import math


def framing_distance(size, vertical_fov, aspect=1.0, margin=1.05):
    """Fit the bounding sphere in both camera axes, including perspective depth."""
    if not 0 < vertical_fov < 180 or aspect <= 0 or margin < 1:
        raise ValueError("camera needs a valid field of view, positive aspect and margin >= 1")
    radius = math.sqrt(sum(value * value for value in size)) / 2
    half_vertical = math.radians(vertical_fov) / 2
    half_horizontal = math.atan(math.tan(half_vertical) * aspect)
    return max(radius, 0.001) * margin / math.sin(min(half_vertical, half_horizontal))
