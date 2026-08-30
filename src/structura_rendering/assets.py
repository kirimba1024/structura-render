"""Minecraft client-asset discovery without a repository-relative import."""

import os
from pathlib import Path


def minecraft_assets_root() -> Path:
    configured = os.environ.get("STRUCTURA_MINECRAFT_ASSETS")
    if configured:
        path = Path(configured).expanduser().resolve()
        if not path.is_dir():
            raise FileNotFoundError(f"STRUCTURA_MINECRAFT_ASSETS does not exist: {path}")
        return path

    candidates = [Path.cwd(), *Path(__file__).resolve().parents]
    for root in candidates:
        path = root / "assets" / "minecraft"
        if path.is_dir():
            return path
    return Path.cwd() / "assets" / "minecraft"


ASSETS = minecraft_assets_root()
