# Format recipes

[Output table](https://github.com/kirimba1024/structura-render#outputs)
· [Rendering guide](guide.md)

## SVG plans and sections

```bash
structura-render svg house.nbt floor.svg --view top --depth 1 4 --title 'Ground floor'
structura-render svg house.nbt section.svg --view north --depth 4 5 --ground-y 1
```

`render_svg(source, output=None, view="top", depth=(1, 4), title="Ground floor")`
returns SVG text and optionally writes atomically. Visibility, colours,
coordinates and half-open depth ranges match PNG projections. One coordinate
unit is one block; adjacent equal colours merge into rectangles without an
embedded raster image. Titles remain text.

`ProjectionOverlays` gives each mask a named group, translucent fill and vector
outline; ground level is a dashed path. Masks are supplied by the caller.
SVG supports vector plans/annotations, not textured 3D rendering. Complex
plans can exceed PNG size: `max_elements=100_000` and `max_pixels=16_000_000`
bound output. Failures preserve an existing file.

## USD scenes

```bash
pip install 'structura-render[usdz]'
structura-render usd house.nbt house.usdc
structura-render usda house.nbt house.usda
```

Python: `export_structure("house.nbt", "house.usdc", strict=True)`.
USD/USDA/USDC/USDZ share scene building, materials, camera and geometry. USDA is
text; USDC/default USD are binary. Scenes are centred, Y-up, one metre per
block. Plain USD uses [adjacent texture resources](guide.md#3d-export-and-portability);
USDZ is a single file.

## MagicaVoxel VOX

```bash
structura-render vox house.nbt house.vox
```

Base-package export writes one coloured voxel per visible block using
projection family colours. It embeds no textures, Minecraft states or NBT.
Non-cube/unknown shapes become cubes, transparency becomes opaque and ordinary
entities are omitted. `RenderWarning` reports approximations; `--strict`
rejects them. At most 255 colours fit; palette reduction is reported.

Sparse models are split into chunks of at most 256 cells per axis, positioned
by scene-graph transforms. No full bounding volume is allocated. Minecraft
`(x, y, z)` maps to VOX `(x, size_z - 1 - z, y)` (Z-up). `max_blocks` bounds
authored cells; mesh/atlas limits do not apply.

## Lossless WebP

```python
from structura_render import render_projection

image = render_projection("house.nbt", view="top", depth=(1, 4))
image.save("floor.webp", lossless=True, method=6)
```

Needs only Pillow with WebP support. Direct `image.save()` has Pillow's normal
write semantics; CLI `.webp` output is atomic with default encoding settings.
Lossless WebP is not always smaller than PNG; compare for your content.

## SNBT, Sponge v1 and Bedrock input

SNBT is accepted like Structure NBT. Normalize Sponge v1 without a DataVersion
with core's `--source-data-version` first; this declares the source game
version, not an upgrade. The historical `[legacy]` fallback remains available.

Bedrock input requires `[bedrock]` and defaults to a Java 1.21.0 target. To
select another supported target, use `structura_core.load_structure` with
`target_version`. For strict input conversion, see
[rendering notices](guide.md#notices-fidelity-and-limits); for losses and version
rules, see the [core contract](https://github.com/kirimba1024/structura-core/blob/main/docs/formats.md).
Native Bedrock copying needs no translation extra.
