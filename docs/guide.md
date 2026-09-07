# Rendering guide

[Quick start and formats](https://github.com/kirimba1024/structura-render#readme)
· [SVG, USD, VOX, WebP and Bedrock recipes](formats.md)

## Images and sections

```python
from structura_core import load_structure
from structura_render import render_hero, render_projection, render_projections, render_svg

structure = load_structure("house.litematic", region="Main")
image = render_projection(structure, view="top", scale=8, transparent=True)
image.save("top.webp", lossless=True, method=6)
render_projections(structure, "views.png", views=("top", "north"))
render_hero(structure, "house.png", transparent=True, orthographic=True)
render_svg(structure, "floor.svg", view="top", depth=(1, 4), title="Ground floor")
```

Image functions return Pillow images; `render_svg` returns text. Functions
accepting an output path write atomically. Calling Pillow's `image.save()`
directly uses its usual write semantics.

Projections show the nearest non-air block cell using family colours, without
textures or a graphics backend. `structure_void` is invisible. Ordinary
projections allocate by image area, without constructing a dense 3D volume.

`depth=(start, stop)` selects local coordinates including `start`, excluding
`stop`: Y for top/bottom, Z for north/south, X for west/east. A one-cell range
shows a layer. Bounds must lie inside the axis and `start < stop`. Opposite
views use the same range; image dimensions and alignment do not change.
On multi-axis sheets, the range applies separately to each selected view.

## Diagnostic overlays

```python
from structura_render import ProjectionOverlays

overlays = ProjectionOverlays(envelope=envelope_mask, cavern_aura=cavern_mask,
                              aura=aura_mask, ground_y=12)
render_projections(structure, "diagnostic.png", overlays=overlays)
```

`render_projection` and `render_svg` accept the same option. Masks are boolean
arrays matching the structure's local X/Y/Z size; inputs remain unchanged.
Envelope is purple with a contour, cavern aura translucent blue, aura cyan.
Side views show `ground_y` as a dashed line. Masks follow the selected depth;
computing them belongs to the caller's geometry layer.

CLI: `structura-render projections house.schem views.png --ground-y 12` or
`--overlays masks.npz`. Write the optional `envelope`, `aura`, `cavern_aura`
arrays with `numpy.savez_compressed`; object arrays and oversized archives
are rejected. All overlay fields are optional.

## Resources and caches

```python
from structura_render import AssetContext, TextureBank, export_structure

resources = AssetContext("/path/to/assets/minecraft")
bank = TextureBank(resources)
export_structure(structure, "house.glb", texture_bank=bank)
render_hero(structure, "house.png", texture_bank=bank)
```

A context owns JSON, texture, entity, item and font caches. Reuse it across
renders; use another context for another resource root. Independent renders
and nested calls keep resources separate. After changing files, call
`resources.clear()`; existing banks refresh too. Low-level helpers can use
`with resources.activate():`. Imports do not discover or extract assets.

Without a bank, `TextureBank()` resolves `STRUCTURA_MINECRAFT_ASSETS` (client
jar or extracted `assets/minecraft`), then a working-tree asset directory,
then a launcher-installed 1.21.1 client on macOS/Linux/Windows. Jars are cached
by path, size and modification time, and published only after extraction.
Resource-pack layering and arbitrary modded clients are outside the contract.
The supported asset layout is Minecraft 1.13+; end-to-end checks cover 1.21.1
and 26.2. Choose client resources matching your structure.

Textured exports fail when assets are missing. Diagnostic mesh exports can
request `allow_flat_fallback=True` / `--allow-flat-fallback`; hero images use
`no_textures=True` / `--no-textures`. These explicitly select coloured cubes.

## 3D export and portability

`export_structure` accepts a path or `Structure`, returns the absolute main
file `Path`, and selects the writer by `.glb`, `.gltf`, `.obj`, `.stl`, `.usd`,
`.usda`, `.usdc`, `.usdz` or `.vox`. VOX needs no texture bank. Other keywords:
`region`, `strict`, `allow_flat_fallback`, `max_blocks`, `max_voxels`,
`max_atlas_size`. Missing backends report the matching install command.

GLB, USDZ, STL and VOX are single files. glTF and plain USD use an adjacent
`<filename>.assets/` directory; OBJ also has an adjacent `.mtl`. Move these
together. Resource names are relative, ASCII-safe and content-derived. The
main file is published last; old resources remain because other models may
reference them. Failed exports preserve existing destinations.

## Notices, fidelity and limits

`RenderWarning` groups repeated mesh-render issues with capped examples:
missing textures/models, approximate entities, markers and omissions.
`strict=True` / `--strict` on hero and 3D exports rejects reported
approximations before writing. Reused banks retain notices. CLI warnings go
to stderr and successful paths to stdout. This checks known fallback paths,
not pixel-perfect fidelity or printability.

Bedrock input can additionally emit `ConversionWarning`; hero/export entry
points propagate strictness to translation. For strict Bedrock projections
or SVG, preload with `structura_core.load_structure(..., strict=True)`.
Java preview conversion retains bounds, authored air and entity payloads
without datapack cleanup. Litematic supports disjoint regions and signed
sizes; overlaps require `--region`. Legacy `.schematic` needs `[legacy]`;
other Amulet inputs are not verified.

Textured mesh outputs share `geometry.TexturedMesh` (NumPy points, quads, UVs,
alpha modes and RGBA atlas), built by `mesh.build_textured_geometry`.
`to_pyvista()` adapts it for hero rendering; `build_textured_meshes` retains
its existing PyVista interface. There is no separate editing/viewer framework.

Client blockstates, multipart models, parent models, rotations and UV locking
supply block geometry. Special blocks use textured models; entity rendering
is static. Animation, item predicates, glint, trims and arbitrary display
transforms are not evaluated. See [coverage](block-render-audit-26.2.md).

Atlases retain source texture pixels and crops with edge padding. Animated
block/item textures use the first frame specified by `.png.mcmeta`.
glTF requests nearest filtering; glTF/USD group alpha materials, and OBJ writes
an opacity map. STL removes duplicate triangles and welds vertices, but plants,
open planes and intersecting shapes may need repair/thickening for printing.

| Guard | Default | Override |
|---|---|---|
| Input / decompressed NBT bytes | 256 MiB each | preload with core's `max_nbt_bytes` |
| Decoded Litematic/Sponge/Bedrock cells | 2,000,000 | `max_blocks` / `--max-blocks` on applicable loaders/CLI |
| Image pixels | 16,000,000 | `max_pixels` / `--max-pixels` |
| Mesh bounding-box cells | 16,000,000 | `max_voxels` / `--max-voxels` |
| Atlas side | 2048 pixels | `max_atlas_size` / `--max-atlas-size` |
| Texture decode | 16,000,000 pixels | fixed |

Raise guards only for trusted inputs; they do not bound total process memory.
Atlas overflow fails without downsampling; multi-page atlases are unsupported.
SVG/VOX have additional [format-specific limits](formats.md).

## Installation diagnostics

```bash
structura-render doctor
structura-render doctor --json
structura-render doctor --assets /path/to/client.jar --render-test
```

Ordinary diagnostics inspect package metadata, resource layout and cache
permissions without importing graphics backends, extracting jars or writing
caches. `dependencies_present` does not certify imports/version compatibility;
layout checks do not validate every resource. Client version comes from
`version.json` when available. SVG/VOX and Bedrock have no separate report entries.

`--render-test` creates an offscreen image in a child with a 30-second timeout;
failed explicit tests return exit code 1. Ordinary reports return 0 even if an
optional backend is absent. JSON includes `schema_version`, package versions,
resource/cache details, backend output status and the graphics test result.

## Compact examples and showcase

`structura-render examples ./examples` copies the authored Java 1.21.1 demo.
Add `--showcase` for 1,195 non-air block IDs in the 26.2 reference and 162
entity IDs handled by the renderer. Use 26.2 resources for the catalogs.
They cover representative states and selected cases, not every dynamic variant
or a guarantee of fidelity; technical/invisible entities are included.

The three compressed inputs total about 48 KiB. `coverage.json` stores counts
and hashes. Repeated copying preserves modified files. The bundled README
explains regeneration; no rendered outputs or game assets are bundled.

## Command compatibility

The unified CLI and `python -m structura_render` accept `projections`, `png`,
`svg`, `glb`, `gltf`, `obj`, `stl`, `usd`, `usda`, `usdc`, `usdz`, `vox`, `doctor`
and `examples`. The existing dedicated render/export commands remain supported.
`--help` works without optional backends or game assets. For a temporary tool:

```bash
uvx --from 'structura-render[gltf]' structura-render glb house.litematic house.glb
```
