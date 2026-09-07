# Format recipes

## SVG plans and sections

```bash
structura-render svg house.nbt floor.svg --view top --depth 1 4 --title 'Ground floor'
structura-render svg house.nbt section.svg --view north --depth 4 5 --ground-y 1
```

```python
from structura_render import ProjectionOverlays, render_svg

svg = render_svg("house.nbt", "floor.svg", view="top", depth=(1, 4),
                 title="Ground floor", overlays=ProjectionOverlays(ground_y=1))
```

The function returns SVG text and optionally writes the file atomically. It
shares visibility, colours, local coordinates and half-open depth ranges with
PNG projections. One SVG coordinate unit represents one block. Adjacent equal
colours are merged into rectangles; no raster image is embedded.

`ProjectionOverlays` accepts existing envelope, aura and cavern-aura masks in
X/Y/Z order. Each mask has its own named SVG group, translucent fill and vector
outline. Ground level is a separate dashed path on side views. An optional
title remains text. The renderer does not compute the geometry masks.

SVG is useful when arranging plans in a graphics program or printing vector
annotations. It does not add textured 3D rendering or editing tools. Complex
plans can be larger than PNG: output is bounded by `max_elements=100_000` and
the existing `max_pixels=16_000_000` size guard. Failures retain an old output.

## USD scenes

```bash
pip install 'structura-render[usdz]'
structura-render usd house.nbt house.usdc
structura-render usda house.nbt house.usda
```

```python
from structura_render import export_structure

export_structure("house.nbt", "house.usdc", strict=True)
```

USD, USDA, USDC and USDZ share one scene builder, materials, camera and geometry.
USDA is text; USDC and default USD output are binary. The scene uses Y-up and
one metre per Minecraft block, centred like the existing USDZ output.

Plain USD stores textures in a sibling `filename.assets` directory, addressed
by relative, content-derived names. Move the scene and that directory together.
The scene is published last; a failed export cannot overwrite resources used
by the previous scene. Old unused resources are retained rather than deleting
files another scene could still reference. USDZ remains the single-file option.

## MagicaVoxel VOX

```bash
structura-render vox house.nbt house.vox
```

VOX requires only the base package. It writes one coloured voxel per visible
Minecraft block using the same family colours as diagnostic projections.
Textures, Minecraft block states and NBT are not embedded. Non-cube or unknown
shapes become full cubes; transparency becomes opaque; ordinary entity models
are omitted. These geometric
approximations emit `RenderWarning` and are rejected by `--strict`.

Sparse models are partitioned into at most 256 cells per axis and positioned
through a scene graph. The exporter never allocates the full bounding volume.
Minecraft `(x, y, z)` maps to VOX `(x, size_z - 1 - z, y)`; vertical is Z-up.
At most 255 colours are stored; palette reduction, if needed, is reported.
`max_blocks` bounds authored cell count, while mesh/atlas limits do not apply.

## Lossless WebP with the existing image API

```python
from structura_render import render_projection

image = render_projection("house.nbt", view="top", depth=(1, 4))
image.save("floor.webp", lossless=True, method=6)
```

No extra package is needed with a Pillow build supporting WebP. The direct
Pillow save above has Pillow's usual file-write semantics. CLI image output
uses the existing atomic writer; `.webp` there currently uses Pillow's default
encoding settings. Lossless WebP is not necessarily smaller than PNG; compare
the outputs for your content.

## SNBT, Sponge v1 and Bedrock input

SNBT files are accepted like Structure NBT. Normalize Sponge v1 with core and
an explicit source DataVersion first; render the resulting Structure or NBT.
The historical optional legacy-conversion fallback remains available.

For Bedrock, install `structura-render[bedrock]`. Direct `.mcstructure` input
uses the core adapter's Java 1.21.0 target. To choose another supported target
or enforce conversion diagnostics, call `structura_core.load_structure` with
`target_version` and `strict=True`, then pass its Structure to the renderer.
`export_structure` and `render_hero` also pass strictness to Bedrock input
conversion. Projection callers can preload with core's strict mode as above.
See the core package's format contract before translating
entities or block NBT. Native Bedrock copying does not need the extra.
