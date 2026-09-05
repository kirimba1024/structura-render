"""Glyph metrics taken from the pack's own font providers.

A Minecraft font is an ordered list of providers rather than one sheet. A
`space` provider gives advances for characters that draw nothing; a `bitmap`
provider is a texture cut into a grid by the rows of its `chars` field. Every
glyph is drawn `height` pixels tall -- 8 unless the provider says otherwise --
so a sheet with taller cells is scaled down rather than drawn larger, and a
glyph's advance is its own inked width at that scale plus one pixel of
tracking.

Reading that is what lets a sign carry anything outside ASCII. Assuming a
single 16x16 ASCII sheet, as this module used to, renders every other script
as a row of question marks: 1.21.1 keeps Cyrillic and Greek in
nonlatin_european.png and the accented Latin in accented.png, on grids of a
different size from ascii.png's.
"""

import json
from functools import lru_cache

import numpy as np
from PIL import Image

from .assets import ASSETS

HEIGHT = 8
MISSING = "?"
DEFAULT_FONT = "minecraft:default"


def _providers(font_id, seen=None):
    seen = set() if seen is None else seen
    if font_id in seen:
        return []
    seen.add(font_id)
    path = ASSETS / "font" / f"{font_id.split(':', 1)[-1]}.json"
    if not path.is_file():
        return []
    result = []
    for provider in json.loads(path.read_text()).get("providers", []):
        if provider.get("type") == "reference":
            result.extend(_providers(provider["id"], seen))
        else:
            result.append(provider)
    return result


def _bitmap_glyphs(provider):
    file_id = provider["file"].split(":", 1)[-1]
    path = ASSETS / "textures" / file_id
    if not path.is_file():
        return
    alpha = np.asarray(Image.open(path).convert("RGBA"))[:, :, 3]
    rows = provider["chars"]
    cell_h = alpha.shape[0] // len(rows)
    cell_w = alpha.shape[1] // len(rows[0])
    scale = provider.get("height", HEIGHT) / cell_h
    for row, line in enumerate(rows):
        top = row * cell_h
        for col, char in enumerate(line):
            if char == "\u0000":
                continue
            left = col * cell_w
            ink = np.argwhere(alpha[top:top + cell_h, left:left + cell_w] > 0)
            if not len(ink):
                continue
            width = int(ink[:, 1].max()) + 1
            crop = (left, top, left + width, top + cell_h)
            yield char, (file_id.removesuffix(".png"), crop, round(width * scale) + 1)


@lru_cache(maxsize=1)
def _glyphs():
    table = {}
    for provider in _providers(DEFAULT_FONT):
        kind = provider.get("type")
        if kind == "space":
            for char, advance in provider.get("advances", {}).items():
                table.setdefault(char, (None, None, float(advance)))
        elif kind == "bitmap":
            for char, entry in _bitmap_glyphs(provider):
                table.setdefault(char, entry)
    return table


def glyph(char):
    """(texture, crop, advance) for one character.

    The advance is in the font's own pixel units, where a glyph is HEIGHT
    tall whatever grid it came from, so a caller can lay out a line without
    knowing which sheet each character was found on. A character the pack has
    no glyph for falls back to '?', matching the game.
    """
    table = _glyphs()
    return table.get(char) or table.get(MISSING) or (None, None, HEIGHT)
