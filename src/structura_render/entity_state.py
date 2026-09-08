import math


def _plain(value):
    return str(value).split(":", 1)[-1].lower()


def _number(value, default=0.0):
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return default


def _flag(nbt, key):
    return key in nbt and bool(int(_number(nbt[key])))


def _values(container, key):
    values = container.get(key) if hasattr(container, "get") else None
    if values is None:
        return None
    try:
        return tuple(_number(value) for value in values)
    except TypeError:
        return None


def _yaw(nbt):
    values = _values(nbt, "Rotation") or _values(nbt, "rotation")
    return -values[0] if values else 0.0


def _is_baby(nbt):
    return (_flag(nbt, "IsBaby") or _flag(nbt, "is_baby")
            or _number(nbt.get("Age", nbt.get("age", 0))) < 0)


HANGING = frozenset({"painting", "item_frame", "glow_item_frame"})


def anchor_of(record, nbt=None, *, exact=False):
    nbt = record if nbt is None else nbt
    keys = ("pos", "Pos") if exact else ("blockPos", "block_pos")
    for key in keys:
        values = _values(record, key)
        if values and len(values) == 3:
            return values if exact else tuple(int(value) for value in values)
    if not exact:
        for key in ("pos", "Pos"):
            values = _values(record, key)
            if values and len(values) == 3:
                return tuple(math.floor(value) for value in values)
        for key in ("blockPos", "block_pos"):
            values = _values(nbt, key)
            if values and len(values) == 3:
                return tuple(int(value) for value in values)
        if all(key in nbt for key in ("TileX", "TileY", "TileZ")):
            return tuple(int(_number(nbt[key])) for key in ("TileX", "TileY", "TileZ"))
    for key in ("Pos", "pos"):
        values = _values(nbt, key)
        if values and len(values) == 3:
            return values if exact else tuple(math.floor(value) for value in values)
    return None
