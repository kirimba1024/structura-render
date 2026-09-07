"""Minecraft Structure NBT renderers and reusable mesh construction."""

__all__ = ["TextureBank", "tint_for"]
__version__ = "0.3.2"


def __getattr__(name):
    if name not in __all__:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from .textures import TextureBank, tint_for
    return {"TextureBank": TextureBank, "tint_for": tint_for}[name]
