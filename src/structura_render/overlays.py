"""Optional diagnostic masks in the structure's local X/Y/Z coordinates."""

from dataclasses import dataclass
from numbers import Integral
from typing import Optional
from zipfile import BadZipFile, ZipFile

import numpy as np

from .projection_grid import VIEWS, depth_range, orient

OVERLAY_STYLES = (
    ("cavern_aura", (88, 132, 235), .14),
    ("aura", (56, 192, 224), .22),
    ("envelope", (190, 76, 226), .26),
)


@dataclass(frozen=True)
class ProjectionOverlays:
    envelope: Optional[np.ndarray] = None
    aura: Optional[np.ndarray] = None
    cavern_aura: Optional[np.ndarray] = None
    ground_y: Optional[int] = None

    def validate(self, size):
        for name in ("envelope", "aura", "cavern_aura"):
            mask = getattr(self, name)
            if mask is not None and (not isinstance(mask, np.ndarray)
                                     or mask.dtype != np.bool_ or mask.shape != tuple(size)):
                raise ValueError(f"{name} must be a boolean array with shape {tuple(size)} in X/Y/Z order")
        if self.ground_y is not None and (
            isinstance(self.ground_y, (bool, np.bool_)) or not isinstance(self.ground_y, Integral)
            or not 0 <= self.ground_y < size[1]
        ):
            raise ValueError(f"ground_y must be an integer in [0, {size[1]})")


def _blend(canvas, mask, color, opacity):
    if canvas.shape[2] == 3:
        canvas[mask] = canvas[mask] * (1 - opacity) + np.asarray(color) * opacity
    else:
        pixels = canvas[mask]
        old_alpha = pixels[:, 3:4] / 255
        alpha = opacity + old_alpha * (1 - opacity)
        canvas[mask, :3] = (np.asarray(color) * opacity + pixels[:, :3] * old_alpha * (1 - opacity)) / alpha
        canvas[mask, 3] = alpha[:, 0] * 255


def projected_overlays(overlays, view, size, depth=None):
    if not isinstance(overlays, ProjectionOverlays):
        raise ValueError("overlays must be ProjectionOverlays")
    overlays.validate(size)
    axis = VIEWS[view][0]
    selection = [slice(None)] * 3
    selection[axis] = slice(*depth_range(depth, size, axis))
    for name, color, opacity in OVERLAY_STYLES:
        mask = getattr(overlays, name)
        if mask is not None:
            yield name, color, opacity, orient(mask[tuple(selection)].any(axis=axis), view)


def draw_overlays(canvas, overlays, view, size, *, depth=None):
    canvas = canvas.astype(np.float64)
    for name, color, opacity, plane in projected_overlays(overlays, view, size, depth):
        _blend(canvas, plane, color, opacity)
        if name == "envelope":
            inside = np.zeros_like(plane)
            inside[1:-1, 1:-1] = (plane[1:-1, 1:-1] & plane[:-2, 1:-1] & plane[2:, 1:-1]
                                  & plane[1:-1, :-2] & plane[1:-1, 2:])
            _blend(canvas, plane & ~inside, np.asarray(color) * .8, 1)
    if overlays.ground_y is not None and VIEWS[view][0] != 1:
        dash = np.zeros(canvas.shape[:2], dtype=bool)
        dash[size[1] - 1 - overlays.ground_y, (np.arange(canvas.shape[1]) // 2) % 2 == 0] = True
        _blend(canvas, dash, (0, 0, 0), .45)
    return np.clip(canvas, 0, 255).astype(np.uint8)


def load_overlays(path, size, *, max_blocks, ground_y=None):
    from structura_core.limits import check_volume

    check_volume(int(size[0]) * int(size[1]) * int(size[2]), max_blocks)
    try:
        with ZipFile(path) as archive:
            members = archive.infolist()
            names = {member.filename for member in members}
            if len(names) != len(members) or names - {"envelope.npy", "aura.npy", "cavern_aura.npy"}:
                raise ValueError("overlays NPZ accepts only envelope, aura and cavern_aura")
            if any(member.file_size > max_blocks + 16384 for member in members):
                raise ValueError("overlay array exceeds max_blocks")
        with np.load(path, allow_pickle=False) as archive:
            result = ProjectionOverlays(**{name: archive[name] for name in archive.files}, ground_y=ground_y)
    except (BadZipFile, EOFError) as error:
        raise ValueError("invalid overlays NPZ archive") from error
    result.validate(size)
    return result
