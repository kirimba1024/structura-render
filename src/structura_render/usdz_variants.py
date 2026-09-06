#!/usr/bin/env python3
import argparse
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

from pxr import Sdf, Usd, UsdGeom, UsdUtils


def variant(value):
    name, separator, source = value.partition("=")
    if not separator or not name or not source:
        raise argparse.ArgumentTypeError("expected Name=source.usdz")
    path = Path(source).resolve()
    if not path.is_file():
        raise argparse.ArgumentTypeError(f"file not found: {path}")
    return name, path


def package(output, variants, set_name="Building", default=None):
    variants = list(variants)
    names = [name for name, _ in variants]
    if not variants:
        raise ValueError("at least one variant is required")
    if len(names) != len(set(names)):
        raise ValueError("variant names must be unique")
    invalid = [name for name in names if not Sdf.Path.IsValidIdentifier(name)]
    if invalid:
        raise ValueError(f"invalid variant names: {invalid}")
    default = default or variants[0][0]
    if default not in names:
        raise ValueError(f"unknown default variant: {default}")

    with tempfile.TemporaryDirectory() as directory:
        directory = Path(directory)
        references = []
        for index, (name, source) in enumerate(variants):
            target = directory / str(index)
            with zipfile.ZipFile(source) as archive:
                members = archive.infolist()
                if not members:
                    raise ValueError(f"empty USDZ: {source}")
                paths = [PurePosixPath(member.filename) for member in members]
                if any(path.is_absolute() or ".." in path.parts for path in paths):
                    raise ValueError(f"unsafe USDZ member path: {source}")
                root_layer = paths[0]
                if len(root_layer.parts) != 1 or root_layer.suffix not in {
                    ".usd", ".usda", ".usdc",
                }:
                    raise ValueError(f"USDZ root layer must be its first root file: {source}")
                archive.extractall(target)
            source_stage = Usd.Stage.Open(str(target / str(root_layer)))
            if source_stage is None or not source_stage.GetDefaultPrim():
                raise ValueError(f"USDZ has no valid default prim: {source}")
            references.append((
                name, f"{index}/{root_layer}", source_stage.GetDefaultPrim().GetPath(),
            ))

        root_layer = directory / "variants.usda"
        stage = Usd.Stage.CreateNew(str(root_layer))
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
        stage.SetMetadata("metersPerUnit", 1.0)
        root = UsdGeom.Xform.Define(stage, "/Model").GetPrim()
        stage.SetDefaultPrim(root)
        choices = root.GetVariantSets().AddVariantSet(set_name)
        for name, asset, prim_path in references:
            choices.AddVariant(name)
            choices.SetVariantSelection(name)
            with choices.GetVariantEditContext():
                child = UsdGeom.Xform.Define(stage, "/Model/Building").GetPrim()
                child.GetReferences().AddReference(asset, prim_path)
        choices.SetVariantSelection(default)
        stage.GetRootLayer().Save()

        output = Path(output).resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        if not UsdUtils.CreateNewUsdzPackage(Sdf.AssetPath(str(root_layer)), str(output)):
            raise RuntimeError("USDZ packaging failed")
        return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output")
    parser.add_argument("variants", nargs="+", type=variant, metavar="Name=source.usdz")
    parser.add_argument("--set-name", default="Building")
    parser.add_argument("--default")
    args = parser.parse_args()
    print(package(args.output, args.variants, args.set_name, args.default))


if __name__ == "__main__":
    main()
