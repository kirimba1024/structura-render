"""Native NBT/Litematic/Sponge input, with optional translation of legacy schematics."""
import shutil
import tempfile
from pathlib import Path

from structura_core import Structure, save_structure
from structura_core import load_structure as load_native
from structura_core.litematic import DEFAULT_MAX_BLOCKS
from structura_core.schematic import UnsupportedSchematicVersion

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
    try:
        if path.suffix.lower() in {".litematic", ".schem"}:
            src = load_structure(path)
            output = Path(directory) / f"{path.stem}.nbt"
            save_structure(src, output, src.size)
            return output
        return _convert(path, directory)
    except BaseException:
        shutil.rmtree(directory, ignore_errors=True)
        raise


def load_structure(path, *, region=None, max_blocks=DEFAULT_MAX_BLOCKS):
    if isinstance(path, Structure):
        if region is not None:
            raise ValueError("region applies only to Litematic files")
        return path
    path = Path(path)
    if path.suffix.lower() in {".litematic", ".schem"}:
        try:
            return load_native(path, region=region, max_blocks=max_blocks)
        except UnsupportedSchematicVersion as error:
            if error.version != 1:
                raise
    if region is not None:
        raise ValueError("region applies only to Litematic files")
    if path.suffix.lower() in NATIVE_SUFFIXES:
        return Structure(path)
    with tempfile.TemporaryDirectory(prefix="structura-render-legacy-") as directory:
        return Structure(_convert(path, directory))
