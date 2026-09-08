from pathlib import Path

from structura_render import legacy_input
from structura_core.schematic import MissingSchematicDataVersion


def test_legacy_conversion_directory_is_removed_after_loading(tmp_path, monkeypatch):
    converted_directory = None

    def convert(_source, directory):
        nonlocal converted_directory
        converted_directory = Path(directory)
        output = converted_directory / "converted.nbt"
        output.write_text("structure")
        return output

    class LoadedStructure:
        def __init__(self, path):
            self.content = Path(path).read_text()

    def missing_version(*args, **kwargs):
        raise MissingSchematicDataVersion("unknown source version")

    monkeypatch.setattr(legacy_input, "_convert", convert)
    monkeypatch.setattr(legacy_input, "Structure", LoadedStructure)
    monkeypatch.setattr(legacy_input, "load_native", missing_version)

    structure = legacy_input.load_structure(tmp_path / "source.schem")

    assert structure.content == "structure"
    assert converted_directory is not None
    assert not converted_directory.exists()
