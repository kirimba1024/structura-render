"""Minecraft Structure NBT renderers and reusable mesh construction."""

__all__ = ["ProjectionOverlays", "AssetContext", "TextureBank", "tint_for", "render_projection", "render_projections", "render_svg", "render_hero", "export_structure", "RenderWarning"]
__version__ = "0.8.0"


def __getattr__(name):
    if name not in __all__:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from importlib import import_module

    module = {
        "ProjectionOverlays": "overlays", "AssetContext": "assets", "TextureBank": "textures", "tint_for": "textures",
        "render_projection": "projections", "render_projections": "projections",
        "render_svg": "svg",
        "render_hero": "hero",
        "export_structure": "export",
        "RenderWarning": "diagnostics",
    }[name]
    return getattr(import_module(f".{module}", __name__), name)
