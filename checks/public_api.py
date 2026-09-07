from __future__ import annotations

from pathlib import Path
import warnings
from PIL import Image
from structura_core import Structure
from structura_render import AssetContext, ProjectionOverlays, RenderWarning, TextureBank, export_structure, render_hero, render_projection, render_projections, tint_for


def use_api(source: Structure, assets: Path) -> tuple[Image.Image, Path]:
    warnings.filterwarnings("default", category=RenderWarning)
    bank = TextureBank(AssetContext(assets))
    tint: tuple[int, int, int] | None = tint_for("minecraft:stone")
    image = render_projection(source, view="top", depth=(0, 1), overlays=ProjectionOverlays(ground_y=0))
    image = render_projections(source, views=["top", "bottom"], depth=(0, 1))
    if tint is None:
        image = render_hero(source, texture_bank=bank, strict=True)
    result = export_structure(source, "demo.glb", texture_bank=bank, strict=True)
    return image, result
