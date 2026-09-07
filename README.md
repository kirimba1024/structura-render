# structura-render

**Minecraft structures, rendered like Minecraft.**

Turn a Java Edition Structure NBT into a polished PNG or a portable 3D model.
`structura-render` reads the blockstates, models and textures from your own
Minecraft client, so stairs stay stairs, doors keep their state, glass keeps
its alpha and every export agrees with the preview.

<p align="center">
  <img src="https://raw.githubusercontent.com/kirimba1024/structura-render/main/docs/screenshots/usdz-floating-island.png" width="49%" alt="Floating island exported to USDZ">
  <img src="https://raw.githubusercontent.com/kirimba1024/structura-render/main/docs/screenshots/hero-render-detail.png" width="49%" alt="Textured Minecraft structure rendered as a PNG">
</p>

## Quick start

Install only the output you need:

```bash
pip install "structura-render[usdz]"
```

Render a showcase image and export the same geometry:

```bash
structura-render-hero house.nbt house.png
structura-export-usdz house.nbt house.usdz
```

For Minecraft 1.21.1, the standard launcher installation is detected
automatically on macOS, Linux and Windows. To use another client or resource
pack, point the renderer at its `.jar` or extracted `assets/minecraft` folder:

```bash
export STRUCTURA_MINECRAFT_ASSETS="$HOME/.minecraft/versions/1.21.1/1.21.1.jar"
```

The jar is extracted once into the user cache. Mojang assets are never bundled,
copied into the package or redistributed.

## Outputs

| Result | Install | Command |
|---|---|---|
| Six-view technical PNG | base package | `structura-render-projections in.nbt out.png` |
| Perspective PNG | `[hero]` | `structura-render-hero in.nbt out.png` |
| USDZ / Apple Quick Look | `[usdz]` | `structura-export-usdz in.nbt out.usdz` |
| GLB or glTF | `[gltf]` | `structura-export-gltf in.nbt out.glb` |
| Wavefront OBJ | `[obj]` | `structura-export-obj in.nbt out.obj` |
| Binary STL | `[stl]` | `structura-export-stl in.nbt out.stl` |

Extras can be combined:

```bash
pip install "structura-render[hero,usdz,gltf,obj,stl]"
```

Every command accepts `.nbt`. Legacy `.schematic` and Sponge `.schem` inputs
are available through the `legacy` extra:

```bash
pip install "structura-render[hero,legacy]"
structura-render-hero castle.schematic castle.png
```

Preview conversion preserves the selection's bounds, authored air, block
materials, connections and all entities. It does not apply datapack placement
cleanup. Other Amulet input formats, including `.litematic`, are not currently
verified by this library's conversion tests.

Texture-backed exporters fail clearly when client assets are unavailable,
instead of silently producing a misleading result. For diagnostics only, the
3D exporters can retain the old coloured-cube fallback with
`--allow-flat-fallback`. Hero renders expose the same choice as `--no-textures`.

The five 3D commands support `--help` without optional backends or Minecraft
assets. PNG and USDZ do not require trimesh.

GLB and USDZ are single-file exports. For `.gltf` or `.obj`, keep the model
together with its generated resources when moving or sharing it:

- glTF uses a `<filename>.assets/` directory;
- OBJ uses an adjacent `.mtl` file and a `<filename>.assets/` directory;
- resource filenames are derived from their contents, so exporting another
  model into the same directory does not overwrite the first model's assets.

The main glTF/OBJ file is published after its resources are written. Old
resources are retained when a model is replaced, since another exported model
may still reference them. Paths inside the export use relative, ASCII-safe
resource names, including when the model's filename contains spaces or Unicode.

## What makes the output faithful

- **Client-driven models.** Blockstate variants, multipart conditions, parent
  models, element rotations, UV rotation and UV locking come from the game.
- **One geometry pipeline.** PNG, USDZ, glTF, OBJ and STL share the same mesh
  builder, so format-specific implementations do not drift apart.
- **State-aware special blocks.** Chests, signs, banners, beds, heads, shulker
  boxes, bells, decorated pots, fluids and portals use compact textured models.
- **Structure entities.** Paintings, populated item frames, armor stands,
  dropped items and the vanilla entity catalog through 26.2 remain visible.
- **Correct transparency.** Per-pixel alpha is preserved for glass, foliage,
  bars, panes, water and other cutout or translucent surfaces. glTF and USDZ
  group geometry into opaque, cutout and blended materials. glTF explicitly
  requests nearest texture filtering; OBJ includes a grayscale opacity map.
- **No stale cube list.** Occlusion data is derived from client model geometry.

The generic resolver follows the client data rather than a short table of
guessed blocks. New JSON-modelled blocks therefore work without adding another
hardcoded shape to the renderer.

## Choosing Minecraft assets

`STRUCTURA_MINECRAFT_ASSETS` accepts either:

- a Minecraft client `.jar`;
- an extracted `assets/minecraft` directory.

When the variable is unset, the renderer first looks for `assets/minecraft` in
the working tree and then for a launcher-installed 1.21.1 client. Cached jar
content is keyed by the jar path, size and modification time, so different
versions do not collide.

Minecraft 1.13 and newer use the supported asset layout. The renderer is
verified end to end with 1.21.1 and 26.2. This repository's own datapack targets
Java 1.21.1, so use that client when exact project parity matters.

## Honest limits

Entity rendering is static. The renderer does not evaluate animation, AI,
item predicates, enchantment glint, armor trims or arbitrary display
transforms. Entity previews preserve identity and silhouette; they are not a
replacement for Minecraft's animated renderer. Block geometry still follows
the client model pipeline described above.

The base install contains `structura-core`, NumPy and Pillow. PyVista, OpenUSD
and trimesh are installed only by the output extras that need them.

STL contains geometry only. Its exporter welds vertices and removes duplicate
triangles; an isolated solid cube produces a closed, outward-facing surface.
Plants, intersecting shapes and open planes may still require repair or
thickening before 3D printing. STL does not retain textures or transparency.

For implementation coverage and explicit dynamic-render limitations, see
[`docs/block-render-audit-26.2.md`](https://github.com/kirimba1024/structura-render/blob/main/docs/block-render-audit-26.2.md).
