import hashlib
import json
from importlib.resources import files

import pytest
from structura_core import Structure, load_structure
from structura_core.export_schematic import export_schematic

from structura_render import render_projection
from structura_render.entities import SUPPORTED_ENTITY_TYPES
from structura_render.examples import copy_examples


def test_examples_are_compact_valid_and_complete(tmp_path):
    copied = copy_examples(tmp_path, showcase=True)
    assert sum(path.stat().st_size for path in copied) < 65536
    report = json.loads((tmp_path / 'coverage.json').read_text())
    for name, expected in report['files'].items():
        path = tmp_path / name
        src = Structure(path)
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected['sha256']
        assert len(src.present) == expected['blocks']
        assert render_projection(src, scale=1).size == (src.size[0], src.size[2])
    catalog = Structure(tmp_path / 'blocks.nbt')
    assert len({name.split('[')[0] for name in catalog.palette}) == 1195
    entities = Structure(tmp_path / 'entities.nbt')
    assert {str(entry['nbt']['id']).removeprefix('minecraft:') for entry in entities.entities} == SUPPORTED_ENTITY_TYPES
    assert catalog.data_version == entities.data_version == report['catalog_data_version'] == 4903


@pytest.mark.parametrize('name', ['demo.nbt', 'entities.nbt'])
def test_examples_have_exportable_block_entity_ids(tmp_path, name):
    copy_examples(tmp_path, showcase=True)
    source = Structure(tmp_path / name)
    restored = load_structure(export_schematic(source, tmp_path / f'{name}.schem'))
    assert len(restored.entities) == len(source.entities)
    for position, nbt in source.block_nbt.items():
        assert str(nbt['id']) == str(restored.block_nbt[position]['id'])


def test_copy_examples_is_idempotent_and_preserves_user_changes(tmp_path):
    paths = copy_examples(tmp_path)
    assert {path.name for path in paths} == {'demo.nbt', 'README.md'}
    assert copy_examples(tmp_path) == paths
    (tmp_path / 'demo.nbt').write_bytes(b'user changed this')
    with pytest.raises(FileExistsError):
        copy_examples(tmp_path, showcase=True)
    assert (tmp_path / 'demo.nbt').read_bytes() == b'user changed this'
    assert not (tmp_path / 'blocks.nbt').exists()


def test_bundled_demo_is_independent_of_minecraft_resources(tmp_path, monkeypatch):
    monkeypatch.setenv('STRUCTURA_MINECRAFT_ASSETS', str(tmp_path / 'missing'))
    data = files('structura_render').joinpath('data').joinpath('examples').joinpath('demo.nbt').read_bytes()
    result = render_projection(Structure.from_bytes(data), scale=4)
    assert result.size == (60, 52)
