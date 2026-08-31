"""Accept legacy schematic formats wherever a Structure NBT path is expected.

Delegates the actual format detection and legacy-block translation to
structura_core.convert_legacy (amulet-core underneath), which already
handles .schematic, sponge .schem, .litematic and anything else amulet's
level loader recognizes. Only imported lazily, so plain .nbt input never
needs amulet-core installed.
"""
import tempfile
from pathlib import Path

NATIVE_SUFFIXES = {".nbt"}


def as_structure_nbt(path):
    path = Path(path)
    if path.suffix.lower() in NATIVE_SUFFIXES:
        return path
    try:
        from structura_core.convert_legacy import convert
        from structura_core.version import DATA_VERSION, JAVA_VERSION
    except ImportError as exc:
        raise ImportError(
            f"{path} is not a .nbt file; converting {path.suffix} input needs "
            "the 'legacy' extra (amulet-core): pip install '.[legacy]'",
        ) from exc

    tmp_dir = Path(tempfile.mkdtemp(prefix="structura-render-legacy-"))
    dst = tmp_dir / (path.stem + ".nbt")
    convert(str(path), str(dst), DATA_VERSION, JAVA_VERSION)
    return dst
