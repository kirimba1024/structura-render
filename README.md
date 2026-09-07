# structura-render

**Minecraft structures, rendered like Minecraft.**

Create textured previews, vector plans and portable 3D models from Minecraft
structures. Textured previews and mesh exports share one geometry pipeline.
Install only the output backends you need.

![Seven Minecraft structures with textured renders and six-view projections](https://raw.githubusercontent.com/kirimba1024/structura-render/main/docs/screenshots/structure-gallery.webp)

<sub>Builds: ProMcEngineering, Ohnoitswoody, Arolas, EdCr0w, GameBreaker, Zeira4424, DaveGR.</sub>

## Quick start

No Minecraft resources or graphics backend are needed for projections and SVG:

```bash
pip install structura-render
structura-render examples demo
structura-render projections demo/demo.nbt demo/views.png
structura-render svg demo/demo.nbt demo/floor.svg --view top --depth 1 4
```

For textured previews and 3D export:

```bash
pip install "structura-render[hero,usdz]"
structura-render png demo/demo.nbt demo/house.png --orthographic
structura-render usdz demo/demo.nbt demo/house.usdz
```

A launcher-installed Minecraft 1.21.1 client is detected automatically. For
another client or resource pack, set `STRUCTURA_MINECRAFT_ASSETS` to its `.jar`
or extracted `assets/minecraft` directory. Game assets are not bundled.

## Outputs

| Result | Install | Command |
|---|---|---|
| Six-view technical PNG | base | `structura-render projections in.nbt out.png` |
| SVG plan / cross-section | base | `structura-render svg in.nbt out.svg --view top` |
| WebP image | base for projections; `[hero]` for perspective | `structura-render projections in.nbt out.webp` |
| Perspective / orthographic PNG | `[hero]` | `structura-render png in.nbt out.png` |
| USDZ / Apple Quick Look | `[usdz]` | `structura-render usdz in.nbt out.usdz` |
| USD / USDA / USDC scene | `[usdz]` | `structura-render usd in.nbt out.usdc` |
| GLB / glTF | `[gltf]` | `structura-render gltf in.nbt out.glb` |
| Wavefront OBJ | `[obj]` | `structura-render obj in.nbt out.obj` |
| Binary STL | `[stl]` | `structura-render stl in.nbt out.stl` |
| MagicaVoxel VOX | base | `structura-render vox in.nbt out.vox` |

The glTF/USD output extension selects the encoding. WebP uses Pillow's default
encoding in the CLI; lossless saving is shown below. SVG and VOX need no game
assets. Only `[hero]` needs PyVista/VTK. Extras can be combined, for example
`pip install "structura-render[hero,gltf,usdz]"`.

## Inputs

| Input | Requirement |
|---|---|
| Java Structure `.nbt` / text `.snbt` | base |
| Litematic `.litematic`, v5–v7 | base; `--region Main` selects one region |
| Sponge `.schem`, v1–v3 | base; v1 without a DataVersion needs normalization with core first |
| Bedrock `.mcstructure` | `[bedrock]`; translation can omit or approximate data |
| Legacy `.schematic` | `[legacy]` |

These are structure-to-image/model conversions; 3D models and images are not
accepted as input. Native Java loading retains the source game version.

## Python

```python
from structura_render import export_structure, render_hero, render_projection, render_svg

image = render_projection("house.nbt", view="top", depth=(1, 4))
image.save("floor.webp", lossless=True, method=6)
render_svg("house.nbt", "floor.svg", view="top", depth=(1, 4))
render_hero("house.nbt", "house.png", orthographic=True)
export_structure("house.nbt", "house.glb")
```

The same functions accept an in-memory `structura_core.Structure`. PNG, SVG
and 3D entry points can write outputs atomically; `render_projection` returns
a Pillow image. WebP requires a Pillow build with WebP support.

Reported render approximations produce `RenderWarning`; use `--strict` or
`strict=True` on hero/3D exports to reject them before writing. VOX uses coloured
cubes; STL has no textures and may need repair for printing. Entities are static
approximations. Keep generated resource directories with glTF, OBJ and plain USD.

## Documentation

- [Rendering guide](https://github.com/kirimba1024/structura-render/blob/main/docs/guide.md): Python API, layers, overlays, resource caches and output limits.
- [Format recipes](https://github.com/kirimba1024/structura-render/blob/main/docs/formats.md): SVG, USD, VOX, WebP and Bedrock input.
- [Diagnostics and showcase](https://github.com/kirimba1024/structura-render/blob/main/docs/guide.md#installation-diagnostics): `structura-render doctor`, `doctor --render-test`, `examples --showcase`.
- [Rendering coverage](https://github.com/kirimba1024/structura-render/blob/main/docs/block-render-audit-26.2.md): supported blocks/entities and fidelity limits.

Every command supports `--help`. `python -m structura_render` is equivalent to
`structura-render`; existing dedicated render/export commands remain supported.
