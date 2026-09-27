import math

import numpy as np

from .entity_models import (IDENTITY, _catalog, _matmul, _part_matrix, _texture_image, legacy_layout, model_layer,
                            uv_size)
from .entity_mobs import _mob_texture
from .mob_catalog import MOB_SPECS, _COMMON_MOBS

ICON_LIMIT = 24
OUTLINE = (20, 24, 22, 255)

_PROFILE = {"yaw": 90}
_SIDE = {"part": None, "yaw": 90}
_TOP = {"part": None, "pitch": 90}
_HORSE = {"part": "head_parts", "posed": True, "yaw": -90, "pitch": 35}
_LLAMA = {"height": 10}
_PIGLIN = {"without": {"left_ear", "right_ear"}}
_SQUID = {"part": None, "spread": ("tentacle", .7, .35)}
ICON_VIEWS = {
    "armadillo": _TOP, "endermite": _TOP, "phantom": _TOP, "silverfish": _TOP, "turtle": _TOP,
    "bee": {"part": None}, "parrot": {"part": None, "yaw": -90}, "shulker": {"part": None},
    "camel": _PROFILE, "camel_husk": _PROFILE, "dolphin": _PROFILE, "llama": _LLAMA, "trader_llama": _LLAMA,
    "horse": _HORSE, "donkey": _HORSE, "mule": _HORSE, "skeleton_horse": _HORSE, "zombie_horse": _HORSE,
    "cod": _SIDE, "salmon": _SIDE, "tadpole": _SIDE, "tropical_fish": _SIDE,
    "ghast": {"part": "body"}, "happy_ghast": {"part": "body"}, "strider": {"part": "body"},
    "piglin": _PIGLIN, "piglin_brute": _PIGLIN, "zombified_piglin": _PIGLIN,
    "ravager": {"without": {"left_horn", "right_horn"}}, "warden": {"without": {"left_tendril", "right_tendril"}},
    "wither": {"part": None, "without": {"ribcage", "tail"}},
    "squid": _SQUID, "glow_squid": _SQUID,
}


def _find(node, names):
    for name, child in node["children"].items():
        if name in names:
            return child
    return next((found for child in node["children"].values() if (found := _find(child, names)) is not None), None)


def _trimmed(node, without, spread):
    children = {}
    for name, child in node["children"].items():
        if name in without:
            continue
        child = _trimmed(child, without, spread)
        if spread and name.startswith(spread[0]):
            x, y, z, _, yaw, roll, width, _, depth = child["transform"]
            child = {**child, "transform": [x, y, z, spread[1], yaw, roll, width, spread[2], depth]}
        children[name] = child
    return {**node, "children": children}


def _icon_root(root, view):
    part = view.get("part", "head")
    node = root if part is None else _find(root, {part, "main_head"} if part == "head" else {part})
    if node is None and part == "head":
        node = root
    if node is None:
        return None
    if node is not root:
        rotation = node["transform"][3:6] if view.get("posed") else [0, 0, 0]
        node = {**node, "transform": [0, 0, 0, *rotation, *node["transform"][6:]]}
    return _trimmed(node, view.get("without", ()), view.get("spread"))


def _texel_quad(points, uv):
    center = points.mean(axis=0)
    offsets = points - center
    for edge, texels in ((points[1] - points[0], np.linalg.norm(uv[1] - uv[0])),
                         (points[3] - points[0], np.linalg.norm(uv[3] - uv[0]))):
        length = np.linalg.norm(edge)
        if texels < length <= texels + 1.01:
            direction = edge / length
            offsets += np.outer(offsets @ direction, direction) * (texels / length - 1)
    return center + offsets


def _visible(uv, alpha):
    left, top = np.floor(uv.min(axis=0) + 1e-6).astype(int)
    right, bottom = np.ceil(uv.max(axis=0) - 1e-6).astype(int)
    return alpha[max(0, top):bottom, max(0, left):right].any()


def _faces(node, texture_size, alpha, matrix=IDENTITY):
    matrix = _matmul(matrix, _part_matrix(node["transform"]))
    transform = np.asarray(matrix)
    for cube in node["cubes"]:
        for quad in cube["quads"]:
            vertices = np.asarray(quad, dtype=float)
            uv = vertices[:, 3:5] * texture_size
            if _visible(uv, alpha):
                points = _texel_quad(vertices[:, :3], uv)
                yield points @ transform[:3, :3].T + transform[:3, 3], uv
    for child in node["children"].values():
        yield from _faces(child, texture_size, alpha, matrix)


def _view_matrix(pitch, yaw):
    pitch, yaw = math.radians(pitch), math.radians(yaw)
    turn = np.array(((math.cos(yaw), 0, math.sin(yaw)), (0, 1, 0), (-math.sin(yaw), 0, math.cos(yaw))))
    tilt = np.array(((1, 0, 0), (0, math.cos(pitch), -math.sin(pitch)), (0, math.sin(pitch), math.cos(pitch))))
    return tilt @ turn


def _draw(canvas, corners, uv, texture):
    origin, basis = corners[0], np.column_stack((corners[1] - corners[0], corners[3] - corners[0]))
    if abs(np.linalg.det(basis)) < 1e-6:
        return
    left, top = np.floor(corners.min(axis=0)).astype(int)
    right, bottom = np.ceil(corners.max(axis=0)).astype(int)
    ys, xs = np.mgrid[top:bottom, left:right]
    local = (np.stack((xs + .5, ys + .5), axis=-1) - origin) @ np.linalg.inv(basis).T
    inside = np.all((local >= 0) & (local < 1), axis=-1)
    texel = uv[0] + local[..., :1] * (uv[1] - uv[0]) + local[..., 1:] * (uv[3] - uv[0])
    height, width = texture.shape[:2]
    column = np.clip(np.floor(texel[..., 0]).astype(int), 0, width - 1)
    row = np.clip(np.floor(texel[..., 1]).astype(int), 0, height - 1)
    color = texture[row, column] / 255.0
    alpha = color[..., 3:] * inside[..., None]
    region = canvas[top:bottom, left:right]
    region[...] = np.concatenate((color[..., :3] * alpha + region[..., :3] * (1 - alpha),
                                  alpha + region[..., 3:] * (1 - alpha)), axis=-1)


def _outlined(canvas):
    solid = canvas[..., 3] > .1
    grown = solid.copy()
    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)):
        grown |= np.roll(np.roll(solid, dy, axis=0), dx, axis=1)
    image = np.round(canvas * 255).astype(np.uint8)
    image[grown & ~solid] = OUTLINE
    rows, columns = np.flatnonzero(grown.any(axis=1)), np.flatnonzero(grown.any(axis=0))
    return np.ascontiguousarray(image[rows[0]:rows[-1] + 1, columns[0]:columns[-1] + 1])


def _pixel_scale(extent):
    if extent <= ICON_LIMIT / 2:
        return 2
    return 1 / math.ceil(extent / ICON_LIMIT)


def entity_icon(kind, nbt):
    root = _catalog().get(model_layer(kind, nbt))
    spec = _COMMON_MOBS.get(kind, MOB_SPECS.get(kind))
    defaults = spec[1] if spec else ('entity/player/wide/steve', 'entity/steve') if kind == 'player' else ()
    if root is None or not defaults:
        return None
    image = _texture_image(_mob_texture(kind, nbt, defaults))
    view = ICON_VIEWS.get(kind, {})
    node = _icon_root(root, view)
    if image is None or node is None or legacy_layout(kind, image):
        return None
    texture = np.asarray(image)
    rotation = _view_matrix(view.get("pitch", 0), view.get("yaw", 0))
    faces = []
    for points, uv in _faces(node, np.asarray(uv_size(kind, image), dtype=float), texture[..., 3] > 0):
        points = points @ rotation.T
        if np.cross(points[1] - points[0], points[2] - points[0])[2] < -1e-5:
            faces.append((points, uv))
    if not faces:
        return None
    flat = np.concatenate([points[:, :2] for points, _ in faces])
    low, high = flat.min(axis=0), flat.max(axis=0)
    high[1] = min(high[1], low[1] + view.get("height", math.inf))
    scale = _pixel_scale(float(np.max(high - low)))
    screens = [np.floor((points[:, :2] - low) * scale + .5) + 1 for points, _ in faces]
    size = np.max(np.concatenate(screens), axis=0).astype(int) + 2
    canvas = np.zeros((size[1], size[0], 4))
    for (points, uv), corners in sorted(zip(faces, screens), key=lambda item: -item[0][0][:, 2].mean()):
        _draw(canvas, corners, uv, texture)
    canvas[int(np.floor((high[1] - low[1]) * scale + .5)) + 1:] = 0
    return _outlined(canvas)
