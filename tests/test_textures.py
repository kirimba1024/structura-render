import pytest

from structura_render.textures import TextureBank, _tint, texture_bank_or_exit


def test_missing_texture_tint_and_composite_resolve_to_fallback(monkeypatch):
    bank = TextureBank()
    monkeypatch.setattr(bank, "_read", lambda stem: None)

    assert _tint(None, (1, 2, 3)) is None
    assert bank.resolve("minecraft:grass_block") is None
    assert bank.resolve("minecraft:dirt_path") is None
    assert bank.resolve("minecraft:farmland") is None


def test_flat_fallback_must_be_explicit_when_assets_are_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("STRUCTURA_MINECRAFT_ASSETS", str(tmp_path))

    with pytest.raises(SystemExit, match="STRUCTURA_MINECRAFT_ASSETS"):
        texture_bank_or_exit()

    assert isinstance(texture_bank_or_exit(allow_flat_fallback=True), TextureBank)


def test_tall_static_texture_is_not_treated_as_an_animation(tmp_path):
    from PIL import Image
    path = tmp_path / 'static.png'
    Image.new('RGBA', (16, 48), (12, 34, 56, 255)).save(path)
    assert TextureBank._open(path).size == (16, 48)


def test_animation_uses_declared_first_frame_without_resizing(tmp_path):
    from PIL import Image
    path = tmp_path / 'animated.png'
    image = Image.new('RGBA', (32, 64), (12, 34, 56, 255))
    image.paste((44, 55, 66, 255), (0, 32, 32, 64))
    image.save(path)
    path.with_suffix('.png.mcmeta').write_text('{"animation":{"frames":[{"index":1,"time":2},0]}}')
    result = TextureBank._open(path)
    assert result.size == (32, 32) and result.getpixel((0, 0)) == (44, 55, 66, 255)


@pytest.mark.parametrize('animation', [
    {'width': 0}, {'height': True}, {'width': 7}, {'frames': [999]},
])
def test_invalid_animation_metadata_fails_explicitly(tmp_path, animation):
    import json

    from PIL import Image
    path = tmp_path / 'broken.png'
    Image.new('RGBA', (16, 32)).save(path)
    path.with_suffix('.png.mcmeta').write_text(json.dumps({'animation': animation}))
    with pytest.raises(ValueError, match='animation'):
        TextureBank._open(path)
