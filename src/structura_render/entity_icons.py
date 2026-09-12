import numpy as np
from PIL import Image, ImageDraw

from .entity_models import _catalog, _quads, _texture_image, model_layer
from .entity_mobs import _mob_texture
from .mob_catalog import MOB_SPECS, _COMMON_MOBS


def _head(node):
    for name, child in node['children'].items():
        if name in ('head', 'main_head'):
            return child
    return next((found for child in node['children'].values() if (found := _head(child)) is not None), None)


def entity_icon(kind, nbt, size=16):
    root = _catalog().get(model_layer(kind, nbt))
    spec = _COMMON_MOBS.get(kind, MOB_SPECS.get(kind))
    defaults = spec[1] if spec else ('entity/player/wide/steve', 'entity/steve') if kind == 'player' else ()
    if root is None or not defaults:
        return None
    texture = _texture_image(_mob_texture(kind, nbt, defaults))
    if texture is None:
        return None
    texture_size = (texture.width, texture.width) if kind in ("pig", "cow") else texture.size
    faces = []
    for vertices, uv in _quads(_head(root) or root):
        points = np.asarray(vertices)
        normal = np.cross(points[1] - points[0], points[2] - points[0])
        if normal[2] < -1e-5:
            faces.append((points, np.asarray(uv)))
    if not faces:
        return None
    points = np.concatenate([face[0][:, :2] for face in faces])
    lo, hi = points.min(axis=0), points.max(axis=0)
    scale = (size - 2) / max(1, *(hi - lo))
    offset = (np.array((size, size)) - (hi - lo) * scale) / 2
    result = Image.new('RGBA', (size, size))
    for points, uv in sorted(faces, key=lambda face: -face[0][:, 2].mean()):
        screen = (points[:, :2] - lo) * scale + offset
        matrix = np.column_stack((screen, np.ones(4)))
        transform = np.linalg.lstsq(matrix, uv * texture_size, rcond=None)[0].T.ravel()
        layer = texture.transform((size, size), Image.Transform.AFFINE, tuple(transform), Image.Resampling.NEAREST)
        mask = Image.new('L', (size, size))
        ImageDraw.Draw(mask).polygon([tuple(p) for p in screen], fill=255)
        layer.putalpha(Image.fromarray(np.minimum(np.asarray(layer.getchannel('A')), np.asarray(mask))))
        result.alpha_composite(layer)
    return np.asarray(result)
