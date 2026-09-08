"""Read-only installation diagnostics, with an optional isolated graphics test."""

import argparse
import json
import os
import platform
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from zipfile import BadZipFile, ZipFile

from .assets import _cache_root, _pack_data_root, minecraft_assets_source

BASE_PACKAGES = ("structura-core", "structura-render", "amulet-nbt", "numpy", "Pillow")
BACKEND_PACKAGES = {
    "hero": ("pyvista", "vtk"), "usdz": ("usd-core",),
    "gltf": ("trimesh", "networkx"), "obj": ("trimesh", "networkx"), "stl": ("trimesh", "networkx"),
}
RESOURCE_DIRECTORIES = ("blockstates", "models/block", "textures/block")


def _version(package):
    try:
        return version(package)
    except PackageNotFoundError:
        return None


def _client_version(raw):
    document = json.loads(raw)
    if isinstance(document, dict):
        value = document.get("id") or document.get("name")
        if isinstance(value, str):
            return value
    return None


def _assets(source):
    result = {"path": str(source), "kind": None, "layout_ok": False, "minecraft_version": None,
              "painting_registry": False}
    try:
        if source.is_dir():
            result["kind"] = "directory"
            data = _pack_data_root(source)
            result["painting_registry"] = data is not None and (data / 'painting_variant').is_dir()
            result["missing"] = [name for name in RESOURCE_DIRECTORIES if not (source / name).is_dir()]
            result["unreadable"] = [name for name in RESOURCE_DIRECTORIES
                                    if (source / name).is_dir() and not os.access(source / name, os.R_OK | os.X_OK)]
            result["layout_ok"] = not result["missing"] and not result["unreadable"]
        elif source.is_file() and source.suffix == ".jar":
            result["kind"] = "jar"
            with ZipFile(source) as archive:
                names = archive.namelist()
                result["painting_registry"] = any(name.startswith('data/minecraft/painting_variant/') and name.endswith('.json') for name in names)
                resources = [name for name in names if name.startswith(("assets/minecraft/", "data/minecraft/painting_variant/"))]
                if any(".." in Path(name).parts or "\\" in name for name in resources):
                    raise ValueError("client jar contains an invalid resource path")
                result["missing"] = [directory for directory in RESOURCE_DIRECTORIES if not any(
                    name.startswith(f"assets/minecraft/{directory}/") and not name.endswith("/") for name in resources
                )]
                result["layout_ok"] = not result["missing"]
                if "version.json" in names and archive.getinfo("version.json").file_size <= 65536:
                    try:
                        result["minecraft_version"] = _client_version(archive.read("version.json"))
                    except (ValueError, UnicodeError):
                        result["version_error"] = "invalid version.json"
        else:
            result["error"] = "set STRUCTURA_MINECRAFT_ASSETS to a client jar or assets/minecraft directory"
    except (OSError, ValueError, BadZipFile, RuntimeError) as error:
        result.update(layout_ok=False, error=str(error))
    return result


def _cache():
    path = _cache_root()
    try:
        ancestor = path
        while not ancestor.exists() and ancestor != ancestor.parent:
            ancestor = ancestor.parent
        return {"path": str(path), "exists": path.is_dir(),
                "writable_by_permissions": ancestor.is_dir() and os.access(ancestor, os.W_OK | os.X_OK)}
    except OSError as error:
        return {"path": str(path), "exists": None, "writable_by_permissions": False, "error": str(error)}


def _render_test():
    script = """
import numpy as np
import pyvista as pv
plotter = pv.Plotter(off_screen=True, window_size=(32, 32))
try:
    plotter.set_background('white')
    plotter.add_mesh(pv.Cube(), color='red')
    pixels = plotter.screenshot(return_img=True)
    assert pixels.shape[:2] == (32, 32) and np.ptp(pixels[..., :3]) > 0
finally:
    plotter.close()
"""
    try:
        result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired) as error:
        return {"status": "failed", "error": str(error)}
    if result.returncode:
        return {"status": "failed", "returncode": result.returncode, "error": result.stderr[-2000:]}
    return {"status": "passed"}


def diagnose(*, source=None, render_test=False):
    packages = dict.fromkeys((*BASE_PACKAGES, *(name for group in BACKEND_PACKAGES.values() for name in group)))
    packages = {name: _version(name) for name in packages}
    try:
        assets = _assets(Path(source).expanduser().resolve() if source is not None else minecraft_assets_source())
    except OSError as error:
        assets = {"path": None, "layout_ok": False, "error": str(error), "minecraft_version": None}
    report = {"schema_version": 1, "python": platform.python_version(), "packages": packages,
              "assets": assets, "cache": _cache(), "outputs": {}, "render_test": {"status": "not_run"}}
    for output, extra in (("projections", None), ("svg", None), ("vox", None),
                          ("png", "hero"), ("glb", "gltf"), ("gltf", "gltf"),
                          ("obj", "obj"), ("stl", "stl"), ("usd", "usdz"),
                          ("usda", "usdz"), ("usdc", "usdz"), ("usdz", "usdz")):
        required = (*BASE_PACKAGES, *BACKEND_PACKAGES.get(extra, ()))
        missing = [name for name in required if packages[name] is None]
        status = "dependencies_missing" if missing else "dependencies_present"
        if not missing and extra and not assets["layout_ok"]:
            status = "assets_missing"
        if status == "dependencies_present" and output == "png":
            status = "render_unchecked"
        report["outputs"][output] = {"status": status, "missing": missing}
        if missing:
            requirement = f"structura-render[{extra}]" if extra else "structura-render"
            report["outputs"][output]["install"] = f'pip install "{requirement}"'
    if render_test:
        report["render_test"] = _render_test()
        if report["outputs"]["png"]["status"] == "render_unchecked":
            report["outputs"]["png"]["status"] = "render_passed" if report["render_test"]["status"] == "passed" else "render_failed"
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="write structured diagnostics")
    parser.add_argument("--assets", help="inspect a specific client jar or assets/minecraft directory")
    parser.add_argument("--render-test", action="store_true", help="test offscreen PNG in a child process (30 second timeout)")
    args = parser.parse_args(argv)
    report = diagnose(source=args.assets, render_test=args.render_test)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f'Python {report["python"]}')
        for package in ("structura-core", "structura-render"):
            print(f'{package}: {report["packages"][package] or "not installed"}')
        assets = report["assets"]
        print(f'Assets: {assets["path"]} (layout: {"found" if assets["layout_ok"] else "incomplete"})')
        print(f'Minecraft version: {assets["minecraft_version"] or "unknown"}')
        print(f'Painting registry: {assets.get("painting_registry", False)}')
        if "error" in assets:
            print(assets["error"])
        cache = report["cache"]
        print(f'Cache: {cache["path"]} (writable by permissions: {cache["writable_by_permissions"]})')
        for output, result in report["outputs"].items():
            print(f'{output}: {result["status"]}' + (f' — {result["install"]}' if "install" in result else ""))
        print(f'Graphics test: {report["render_test"]["status"]}')
        if "error" in report["render_test"]:
            print(report["render_test"]["error"])
    if report["render_test"]["status"] == "failed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
