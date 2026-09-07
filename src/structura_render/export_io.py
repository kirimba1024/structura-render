"""Write complete exports without changing resources of an older model."""

import hashlib
import json
import os
import re
import tempfile
from io import BytesIO
from pathlib import Path


def atomic_write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, str):
        data = data.encode("utf-8")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(data)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def write_image(image, output):
    """Encode an image completely before replacing its destination."""
    from PIL import Image

    output = Path(output)
    image_format = Image.registered_extensions().get(output.suffix.lower())
    if image_format is None:
        raise ValueError(f"unknown image output extension: {output.suffix!r}")
    buffer = BytesIO()
    image.save(buffer, format=image_format)
    atomic_write(output, buffer.getvalue())
    return output


def nearest_samplers(tree):
    """Preserve pixel-art sampling in glTF instead of relying on viewer defaults."""
    samplers = tree.setdefault("samplers", [])
    for texture in tree.get("textures", []):
        sampler = {"magFilter": 9728, "minFilter": 9728, "wrapS": 33071, "wrapT": 33071}
        if "sampler" in texture:
            sampler.update(samplers[texture["sampler"]])
            sampler.update(magFilter=9728, minFilter=9728)
        texture["sampler"] = len(samplers)
        samplers.append(sampler)
    if not samplers:
        tree.pop("samplers", None)


class _ResourceWriter:
    def __init__(self, output):
        self.directory = output.parent / (re.sub(r"[^a-zA-Z0-9_.-]", "_", output.name) + ".assets")

    def add(self, name, data, *, directory=None):
        if isinstance(data, str):
            data = data.encode("utf-8")
        suffix = Path(name).suffix.lower()
        name = hashlib.sha256(data).hexdigest() + suffix
        path = (self.directory if directory is None else directory) / name
        if not path.is_file() or path.read_bytes() != data:
            atomic_write(path, data)
        return name


def write_gltf(scene, output):
    """Write GLB or glTF; sidecars have immutable content-derived filenames."""
    output = Path(output)
    if output.suffix.lower() == ".glb":
        atomic_write(output, scene.export(file_type="glb", tree_postprocessor=nearest_samplers))
        return output
    if output.suffix.lower() != ".gltf":
        raise ValueError("glTF output must end in .gltf or .glb")

    files = scene.export(file_type="gltf", tree_postprocessor=nearest_samplers)
    tree = json.loads(files.pop("model.gltf"))
    writer = _ResourceWriter(output)
    names = {name: writer.add(name, data) for name, data in files.items()}
    for entry in (*tree.get("buffers", []), *tree.get("images", [])):
        if entry.get("uri") in names:
            entry["uri"] = f"{writer.directory.name}/{names[entry['uri']]}"
    atomic_write(output, json.dumps(tree, separators=(",", ":")))
    return output


def write_obj(scene, output):
    """Write OBJ, materials and alpha maps, publishing the OBJ last."""
    from PIL import Image

    output = Path(output)
    if output.suffix.lower() != ".obj":
        raise ValueError("OBJ output must end in .obj")
    text, files = scene.export(file_type="obj", return_texture=True, write_texture=False)
    opacities = {}
    for geometry in scene.geometry.values():
        material = getattr(geometry.visual, "material", None)
        if material is not None and hasattr(material, "main_color"):
            opacity = float(material.main_color[3]) / 255
            if getattr(material, "alphaMode", None) == "OPAQUE":
                opacity = 1.0
            opacities[material.name] = opacity
    writer = _ResourceWriter(output)
    textures = {name: writer.add(name, data) for name, data in files.items() if not name.endswith(".mtl")}
    textures = {name: f"{writer.directory.name}/{value}" for name, value in textures.items()}
    for name, data in files.items():
        if not name.endswith(".mtl"):
            continue
        material = data.decode("utf-8") if isinstance(data, bytes) else data
        lines = []
        for line in material.splitlines():
            command, _, value = line.partition(" ")
            if command.startswith("map_") and value in textures:
                line = f"{command} {textures[value]}"
            lines.append(line)
            if command == "newmtl" and value in opacities:
                lines.append(f"d {opacities[value]:.8f}")
            if command == "map_Kd" and value in files:
                # map_d is a scalar opacity map. A separate grayscale image
                # avoids readers interpreting the RGB colour as opacity.
                with Image.open(BytesIO(files[value])) as image:
                    opacity = image.convert("RGBA").getchannel("A")
                buffer = BytesIO()
                opacity.save(buffer, format="PNG")
                alpha_name = writer.add("opacity.png", buffer.getvalue())
                lines.append(f"map_d {writer.directory.name}/{alpha_name}")
        # Keep MTL beside OBJ: consumers disagree on the base for texture paths
        # when the material file lives in a subdirectory.
        material_name = writer.add(name, "\n".join(lines) + "\n", directory=output.parent)
        text = text.replace(f"mtllib {name}\n", f"mtllib {material_name}\n")
    atomic_write(output, text)
    return output
