import pytest

from structura_render import textures
from structura_render.textures import TextureBank, _tint, texture_bank_or_exit


def test_missing_texture_tint_and_composite_resolve_to_fallback(monkeypatch):
    bank = TextureBank()
    monkeypatch.setattr(bank, "_read", lambda stem: None)

    assert _tint(None, (1, 2, 3)) is None
    assert bank.resolve("minecraft:grass_block") is None
    assert bank.resolve("minecraft:dirt_path") is None
    assert bank.resolve("minecraft:farmland") is None


def test_flat_fallback_must_be_explicit_when_assets_are_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(textures, "ASSET_DIRECTORIES", (tmp_path / "missing",))

    with pytest.raises(SystemExit, match="STRUCTURA_MINECRAFT_ASSETS"):
        texture_bank_or_exit()

    assert isinstance(texture_bank_or_exit(allow_flat_fallback=True), TextureBank)
