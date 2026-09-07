import json
import os
import subprocess
import sys
import zipfile
from concurrent.futures import ThreadPoolExecutor

import pytest
from PIL import Image

from structura_render import (
    AssetContext,
    TextureBank,
    block_model,
    entities,
    entity_models,
    font,
    item_models,
)
from structura_render.assets import current_context


def pack(directory, color, advance):
    root = directory / 'assets/minecraft'
    for name in ('blockstates', 'models/block', 'textures/block', 'textures/entity', 'items', 'font'):
        (root / name).mkdir(parents=True)
    (root / 'blockstates/stone.json').write_text(json.dumps({'variants': {'': {'model': 'block/stone'}}}))
    (root / 'models/block/stone.json').write_text(json.dumps({'textures': {'all': 'block/stone'}, 'elements': [
        {'from': [0, 0, 0], 'to': [advance, 16, 16], 'faces': {'north': {'texture': '#all'}}}
    ]}))
    (root / 'items/apple.json').write_text(json.dumps({'model': {'type': 'minecraft:model', 'model': 'block/stone'}}))
    (root / 'font/default.json').write_text(json.dumps({'providers': [{'type': 'space', 'advances': {' ': advance}}]}))
    Image.new('RGBA', (32, 32), color).save(root / 'textures/block/stone.png')
    Image.new('RGBA', (32, 32), color).save(root / 'textures/entity/test.png')
    data = directory / 'data/minecraft/painting_variant'
    data.mkdir(parents=True)
    (data / 'test.json').write_text(json.dumps({'width': advance, 'height': 1, 'asset_id': 'minecraft:test'}))
    (root / 'textures/painting').mkdir()
    Image.new('RGBA', (16, 16), color).save(root / 'textures/painting/test.png')
    return AssetContext(root)


def observe(context):
    with context.activate():
        return (
            TextureBank().read_texture('stone').getpixel((0, 0)),
            block_model.block_elements('minecraft:stone', {})[0]['hi'][0],
            item_models.item_texture('minecraft:apple'),
            font.glyph(' ')[2],
            entity_models._texture_image('entity/test').getpixel((0, 0)),
            entities.painting_size('test'),
        )


def test_packs_isolate_blocks_items_entities_fonts_and_nested_calls(tmp_path):
    first = pack(tmp_path / 'first', (11, 22, 33, 255), 4)
    second = pack(tmp_path / 'second', (44, 55, 66, 128), 8)
    expected = [observe(first), observe(second)]
    assert expected[0][0] != expected[1][0]
    assert expected[0][1] == .25 and expected[1][1] == .5
    assert expected[0][3] == 4 and expected[1][3] == 8
    assert expected[0][4] != expected[1][4]
    assert expected[0][5] != expected[1][5]
    with first.activate():
        with pytest.raises(RuntimeError):
            with second.activate():
                assert current_context() is second
                raise RuntimeError('interrupted')
        assert current_context() is first
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(observe, [first, second] * 12))
    assert results == expected * 12


def test_default_bank_follows_environment_at_construction_only(tmp_path, monkeypatch):
    first = pack(tmp_path / 'first', (11, 22, 33, 255), 4)
    second = pack(tmp_path / 'second', (44, 55, 66, 255), 8)
    monkeypatch.setenv('STRUCTURA_MINECRAFT_ASSETS', str(first.root))
    old = TextureBank()
    monkeypatch.setenv('STRUCTURA_MINECRAFT_ASSETS', str(second.root))
    new = TextureBank()
    assert old.read_texture('stone').getpixel((0, 0)) == (11, 22, 33, 255)
    assert new.read_texture('stone').getpixel((0, 0)) == (44, 55, 66, 255)


def test_clear_refreshes_existing_banks_and_derived_caches(tmp_path):
    context = pack(tmp_path, (11, 22, 33, 255), 4)
    bank = TextureBank(context)
    before = observe(context)
    bank.read_texture('stone')
    Image.new('RGBA', (32, 32), (55, 66, 77, 255)).save(context.root / 'textures/block/stone.png')
    (context.root / 'font/default.json').write_text(json.dumps({'providers': [{'type': 'space', 'advances': {' ': 12}}]}))
    assert observe(context) == before
    context.clear()
    assert observe(context)[3] == 12
    assert bank.read_texture('stone').getpixel((0, 0)) == (55, 66, 77, 255)


def test_imports_do_not_resolve_assets_or_extract_jars(tmp_path):
    env = {**os.environ, 'STRUCTURA_MINECRAFT_ASSETS': str(tmp_path / 'does-not-exist')}
    code = 'from structura_render import AssetContext, TextureBank; from structura_render import mesh, entities, item_models, font'
    subprocess.run([sys.executable, '-c', code], env=env, check=True, capture_output=True)


@pytest.mark.parametrize('identifier', ['../secret', 'minecraft:../secret', 'a//b', '/absolute', 'minecraft:foo/../bar', '..:secret', '.:secret'])
def test_resource_paths_cannot_traverse_outside_pack(tmp_path, identifier):
    with pytest.raises(ValueError):
        AssetContext(tmp_path).path('models', identifier, '.json')


def test_concurrent_jar_extraction_publishes_complete_cache(tmp_path, monkeypatch):
    monkeypatch.setenv('XDG_CACHE_HOME', str(tmp_path / 'cache'))
    jar = tmp_path / 'client.jar'
    with zipfile.ZipFile(jar, 'w') as archive:
        archive.writestr('assets/minecraft/models/block/stone.json', '{"elements": []}')
        archive.writestr('assets/minecraft/textures/block/stone.png', b'fixture')
    with ThreadPoolExecutor(max_workers=4) as executor:
        contexts = list(executor.map(AssetContext, [jar] * 8))
    assert len({context.root for context in contexts}) == 1
    assert (contexts[0].root / 'textures/block/stone.png').read_bytes() == b'fixture'
    assert not list((tmp_path / 'cache/structura-render/jar-assets').glob('.*'))
