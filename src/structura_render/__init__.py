"""Minecraft Structure NBT renderers and reusable mesh construction."""

__all__ = ["ProjectionOverlays", "AssetContext", "TextureBank", "tint_for", "render_projection", "render_projections", "render_hero"]
__version__ = "0.5.0"


def __getattr__(name):
    if name not in __all__:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from importlib import import_module

    module = {
        "ProjectionOverlays": "overlays", "AssetContext": "assets", "TextureBank": "textures", "tint_for": "textures",
        "render_projection": "projections", "render_projections": "projections",
        "render_hero": "hero",
    }[name]
    return getattr(import_module(f".{module}", __name__), name)
