# Changelog

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
