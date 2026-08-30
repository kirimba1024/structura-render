"""Minecraft client-asset discovery without a repository-relative import."""

import hashlib
import os
import sys
import zipfile
from pathlib import Path

_VERSION_MARKER_BLOCK = "heavy_core"


def _cache_root() -> Path:
    configured = os.environ.get("XDG_CACHE_HOME")
    base = Path(configured).expanduser() if configured else Path.home() / ".cache"
    return base / "structura-render" / "jar-assets"


def _extract_jar_assets(jar_path: Path) -> Path:
    stat = jar_path.stat()
    key = hashlib.sha1(
        f"{jar_path.resolve()}:{stat.st_mtime_ns}:{stat.st_size}".encode(),
    ).hexdigest()[:16]
    dest = _cache_root() / key
    marker = dest / ".extracted"
    target = dest / "assets" / "minecraft"
    if marker.is_file() and target.is_dir():
        return target

    with zipfile.ZipFile(jar_path) as archive:
        members = [
            name for name in archive.namelist()
            if name.startswith("assets/minecraft/") and not name.endswith("/")
        ]
        if not members:
            raise FileNotFoundError(
                f"{jar_path} has no assets/minecraft/ entries; "
                "is this a real Minecraft client jar?",
            )
        dest.mkdir(parents=True, exist_ok=True)
        archive.extractall(dest, members=members)
    marker.touch()
    return target


def _warn_if_version_mismatch(assets_root: Path) -> None:
    marker = assets_root / "models" / "block" / f"{_VERSION_MARKER_BLOCK}.json"
    if not marker.is_file():
        print(
            f"structura_render: WARNING: {assets_root} has no "
            f"{_VERSION_MARKER_BLOCK} model (added in Minecraft 1.21) -- "
            "these assets look older than the datapack's target version; "
            "renders may not match what actually spawns in-game.",
            file=sys.stderr,
        )


def minecraft_assets_root() -> Path:
    configured = os.environ.get("STRUCTURA_MINECRAFT_ASSETS")
    if configured:
        path = Path(configured).expanduser().resolve()
        if path.is_dir():
            _warn_if_version_mismatch(path)
            return path
        if path.is_file() and path.suffix == ".jar":
            extracted = _extract_jar_assets(path)
            _warn_if_version_mismatch(extracted)
            return extracted
        raise FileNotFoundError(
            f"STRUCTURA_MINECRAFT_ASSETS does not exist: {path} "
            "(point it at an assets/minecraft directory or a client .jar)",
        )

    candidates = [Path.cwd(), *Path(__file__).resolve().parents]
    for root in candidates:
        path = root / "assets" / "minecraft"
        if path.is_dir():
            _warn_if_version_mismatch(path)
            return path
    return Path.cwd() / "assets" / "minecraft"


ASSETS = minecraft_assets_root()
