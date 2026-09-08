# Changelog

## 0.8.1

- Require core 0.6.1 and align diagnostics with its SciPy-free base install.
  Report SVG, VOX and USD dependencies alongside the other supported outputs.

- Share projection geometry and overlay rules between PNG and SVG; load a
  projection sheet's source once. Split SVG validation, layers and XML output.
- Count all SVG elements against the output limit, including root and metadata.
- Prepare block faces as explicit geometry records. Preserve surfaces with
  partially missing textures and resource namespaces in fence-post lookups.
- Share complete NumPy scene geometry between hero images, USD and trimesh
  exports; separate model texture resolution and USD stage construction.
- Store NBT variants as instance coordinates instead of one dense volume per
  variant. Accumulate native quads without intermediate VTK face arrays.
- Preserve special blocks and entities when their textures are missing,
  retaining strict diagnostics. Include entities in diagnostic hero images.
- Keep opaque fallback faces visible behind glass, and hide technical blocks
  in diagnostic scenes. Use the same flat surface rules for every exporter.

## 0.8.0

- Add standalone vector SVG plans with merged cells, labelled overlays and bounded output.
- Export USD/USDA/USDC through the existing USDZ scene builder.
- Export sparse MagicaVoxel scenes with explicit approximation diagnostics.
- Accept SNBT and optionally translated Bedrock input; document lossless WebP.

## 0.7.0

- Add `depth=(start, stop)` / `--depth START STOP` to 2D projections for layers
  and cross-sections. Retain full image alignment and clip overlays consistently.
- Report geometry fallbacks through bounded, operation-local `RenderWarning`
  notices. Add opt-in strict PNG/3D export that fails before writing; preserve
  cache isolation and replay notices on warm caches.
- Ship type information for public APIs and lazy exports. Require core 0.5
  with bounded NBT reads and the typed native conversion API.
- Validate GLB/glTF using the official Khronos Validator, run packaged demo
  commands in CI, and verify public types against the installed wheel.

## 0.6.0

- Add `export_structure(source, output, ...)` for GLB/glTF/OBJ/STL/USDZ from
  paths or in-memory Structure objects. Reuse a supplied TextureBank and
  keep optional backend imports lazy. Return the absolute output Path.
- Route existing 3D commands through the same API and shared argument parser;
  keep the existing low-level writers. CLI success output is the model path.
- Add `structura-render doctor` with human-readable/JSON diagnostics for
  package metadata, resource layout, Minecraft version and cache permissions.
  Ordinary checks do not extract jars or import graphics backends. Optional
  `--render-test` uses a child process with a 30-second timeout.
- Separate resource discovery from jar extraction, preserving existing lookup order.
- Add `structura-render examples [directory] [--showcase]`: a small authored
  demo and catalogs of 1,195 block IDs / 162 handled entity types, approximately
  48 KiB of compressed NBT. Include coverage metadata and avoid overwriting
  modified files. Client assets and generated renders are not bundled.

## 0.5.1

- Reject `.` and `..` resource namespaces before filesystem resolution,
  complementing the existing checks on resource path components.

## 0.5.0

- Add `AssetContext`; bind resource-dependent caches to a render's context.
  Keep default `TextureBank()` calls, support reuse and explicit cache clearing,
  isolate nested/concurrent contexts and remove runtime import-time discovery.
- Publish extracted client assets only after extraction completes.
- Add optional `ProjectionOverlays` for envelope, aura, cavern aura and a dashed
  building level, with validated Python masks and bounded NPZ CLI input.
- Accept native Sponge v2/v3 input in all render/export commands; require
  structura-core 0.4.0. Legacy `.schematic` conversion remains available.
- Preserve HD texture pixels and rectangular crops in a bounded atlas instead
  of resizing every image to 16×16. Add `--max-atlas-size` / `max_atlas_size`.
- Distinguish tall static textures from animations; honor the first `.mcmeta`
  frame and its dimensions. Keep UV and material regression checks.

## 0.4.0

- Accept native `.litematic` input in every output, with `--region` and
  `--max-blocks`; require structura-core 0.3.0.
- Store shared geometry as NumPy buffers. OBJ, STL, glTF/GLB and USDZ no longer
  install or import PyVista/VTK. PNG still uses `[hero]`; applications rendering
  PNG and USDZ should install `[hero,usdz]`. Existing mesh adapters remain.
- Add `render_projection`, `render_projections` and `render_hero` Python APIs
  accepting paths or Structures and returning Pillow images.
- Compute plain projection visibility without dense 3D arrays. Add configurable
  output-pixel and 3D-volume guards before allocation.
- Add transparent images and orthographic cameras; handle vertical camera
  directions, close plotting resources on failures and publish images atomically.
- Add `structura-render` and `python -m structura_render` format dispatch while
  preserving all existing commands and their help without graphics backends.
- Verify Litematic-to-model exports with plotting imports blocked; retain
  regression checks for outward STL faces, UVs and alpha materials.

## 0.3.2

- Isolate trimesh from PNG/USDZ imports. All five 3D commands support `--help`
  without optional backends or Minecraft assets.
- Publish glTF/OBJ resources under content-derived filenames so separate exports
  cannot overwrite one another. Keep sidecars together with the model; existing
  resources are retained when an output is replaced.
- Fix top-face orientation while keeping UVs attached to the same vertices.
  Use double-sided materials instead of artificial reverse triangles; weld and
  deduplicate STL geometry. An isolated cube exports as a closed 12-triangle mesh.
- Separate opaque, cutout and blended material groups in glTF/USDZ, explicitly
  request nearest glTF sampling, and preserve OBJ opacity with alpha maps and
  scalar dissolve. Textured OBJ materials no longer darken the atlas by default.
- Handle intentional empty models without crashing and distinguish unresolved
  parents/texture references from intentionally invisible models.
- Preview legacy inputs with bounds, air, materials and entities preserved;
  require structura-core 0.2.3. Conversion temporary directories are cleaned up.
- Cover all mesh groups in export and avoid quadratic vertex-offset summation.
- Fit PNG cameras to visible bounds and USDZ cameras to their field of view,
  avoiding clipped models at default zoom. Publish USDZ archives atomically.
- Test installed wheels before publishing and check the release tag/version.

Hero PNG requires a working graphics backend; `--allow-skip` is an explicit
opt-in to skipping an image. STL may still need repair/thickening for printing
open planes or intersecting shapes. HD atlas packing and independent resource
contexts remain future work; this release does not claim those improvements.
