"""Accept legacy schematic formats wherever a Structure NBT path is expected.

Delegates the actual format detection and legacy-block translation to
structura_core.convert_legacy (amulet-core underneath), which already
handles .schematic and Sponge .schem. Other Amulet input formats are not
verified here. Only imported lazily, so plain .nbt input never
needs amulet-core installed.
"""
import tempfile
from pathlib import Path

from structura_core import Structure

NATIVE_SUFFIXES = {".nbt"}


def _convert(path, directory):
    path = Path(path)
    try:
        from structura_core.convert_legacy import convert
        from structura_core.version import DATA_VERSION, JAVA_VERSION
    except ImportError as exc:
        raise ImportError(
            f"{path} is not a .nbt file; converting {path.suffix} input needs "
            "the 'legacy' extra (amulet-core): "
            "pip install 'structura-render[legacy]'",
        ) from exc

    dst = Path(directory) / f"{path.stem}.nbt"
    convert(
        str(path), str(dst), DATA_VERSION, JAVA_VERSION,
        preserve_all_entities=True,
        prepare_for_placement=False,
    )
    return dst


def as_structure_nbt(path):
    path = Path(path)
    if path.suffix.lower() in NATIVE_SUFFIXES:
        return path
    directory = tempfile.mkdtemp(prefix="structura-render-legacy-")
    return _convert(path, directory)


def load_structure(path):
    path = Path(path)
    if path.suffix.lower() in NATIVE_SUFFIXES:
        return Structure(path)
    with tempfile.TemporaryDirectory(prefix="structura-render-legacy-") as directory:
        return Structure(_convert(path, directory))
