"""Minecraft client-asset discovery without a repository-relative import."""

import hashlib
import json
import os
import re
import sys
import zipfile
from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
from pathlib import Path
from tempfile import TemporaryDirectory

_VERSION_MARKER_BLOCK = "heavy_core"
_LAYOUT = 2


def _cache_root() -> Path:
    configured = os.environ.get("XDG_CACHE_HOME")
    base = Path(configured).expanduser() if configured else Path.home() / ".cache"
    return base / "structura-render" / "jar-assets"


def _extract_jar_assets(jar_path: Path) -> Path:
    stat = jar_path.stat()
    key = hashlib.sha1(
        f"{jar_path.resolve()}:{stat.st_mtime_ns}:{stat.st_size}:{_LAYOUT}".encode(),
    ).hexdigest()[:16]
    dest = _cache_root() / key
    marker = dest / ".extracted"
    target = dest / "assets" / "minecraft"
    if marker.is_file() and target.is_dir():
        return target

    with zipfile.ZipFile(jar_path) as archive:
        members = [
            name for name in archive.namelist()
            if not name.endswith("/") and (
                name.startswith("assets/minecraft/")
                or name.startswith("data/minecraft/painting_variant/")
            )
        ]
        if not members:
            raise FileNotFoundError(
                f"{jar_path} has no assets/minecraft/ entries; "
                "is this a real Minecraft client jar?",
            )
        if any(".." in Path(name).parts or "\\" in name for name in members):
            raise ValueError("client jar contains an invalid resource path")
        dest.parent.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(dir=dest.parent, prefix=f".{key}.") as temporary:
            staging = Path(temporary) / key
            archive.extractall(staging, members=members)
            (staging / ".extracted").touch()
            try:
                staging.rename(dest)
            except OSError:
                if not marker.is_file() or not target.is_dir():
                    raise
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


def _installed_client_jar():
    """Find the project's Minecraft client without caller-side setup."""
    version = "1.21.1"
    roots = [
        Path.home() / "Library/Application Support/minecraft/versions",
        Path.home() / ".minecraft/versions",
    ]
    appdata = os.environ.get("APPDATA")
    if appdata:
        roots.append(Path(appdata) / ".minecraft/versions")
    for root in roots:
        jar = root / version / f"{version}.jar"
        if jar.is_file():
            return jar
    return None


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
    client_jar = _installed_client_jar()
    if client_jar is not None:
        extracted = _extract_jar_assets(client_jar)
        _warn_if_version_mismatch(extracted)
        return extracted
    return Path.cwd() / "assets" / "minecraft"


def _pack_data_root(assets_root):
    """Optional painting registry beside the asset directory."""
    if len(assets_root.parents) < 2:
        return None
    candidate = assets_root.parents[1] / "data/minecraft"
    return candidate if candidate.is_dir() else None


_active_context = ContextVar("structura_assets", default=None)
_RESOURCE = re.compile(r"(?:[a-z0-9_.-]+:)?[a-z0-9_./-]+\Z")


class AssetContext:
    """Own a resource root and its caches for one or more renders."""

    def __init__(self, source=None):
        root = minecraft_assets_root() if source is None else Path(source).expanduser().resolve()
        self.root = _extract_jar_assets(root) if root.is_file() and root.suffix == ".jar" else root
        self.data = _pack_data_root(self.root)
        self._caches = {}

    def path(self, directory, identifier, suffix=""):
        if not _RESOURCE.fullmatch(identifier):
            raise ValueError(f"invalid resource identifier: {identifier!r}")
        namespace, name = identifier.split(":", 1) if ":" in identifier else ("minecraft", identifier)
        if any(part in {"", ".", ".."} for part in name.split("/")):
            raise ValueError(f"invalid resource path: {identifier!r}")
        root = self.root if namespace == "minecraft" else self.root.parent / namespace
        return root / directory / f"{name}{suffix}"

    def cache(self, key):
        return self._caches.setdefault(key, {})

    def clear(self):
        """Discard cached data after changing files in this resource pack."""
        for cache in self._caches.values():
            cache.clear()

    @contextmanager
    def activate(self):
        token = _active_context.set(self)
        try:
            yield self
        finally:
            _active_context.reset(token)


def current_context():
    return _active_context.get() or AssetContext()


def context_cached(function):
    @wraps(function)
    def cached(*args, **kwargs):
        context = current_context()
        cache = context.cache(function)
        key = (args, tuple(sorted(kwargs.items())))
        if key not in cache:
            with context.activate():
                cache[key] = function(*args, **kwargs)
        return cache[key]
    return cached


@context_cached
def read_json(path):
    return json.loads(path.read_text()) if path.is_file() else None


def __getattr__(name):
    if name in {"ASSETS", "DATA"}:
        context = current_context()
        return context.root if name == "ASSETS" else context.data
    raise AttributeError(name)
