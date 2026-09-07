from pathlib import Path

from structura_render import legacy_input


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

    monkeypatch.setattr(legacy_input, "_convert", convert)
    monkeypatch.setattr(legacy_input, "Structure", LoadedStructure)

    structure = legacy_input.load_structure(tmp_path / "source.schematic")

    assert structure.content == "structure"
    assert converted_directory is not None
    assert not converted_directory.exists()
