# Render architecture

Render consumes Core structures and produces images or model files. Geometry
is represented by NumPy arrays; PyVista, trimesh and OpenUSD are loaded by the
operations that need them.

## Geometry pipeline

| Module | Responsibility |
|---|---|
| `geometry` | `TexturedMesh`, `FlatMesh`, `SceneGeometry`, cube coordinates, mask surfaces, triangulation and material grouping. |
| `atlas` | Image deduplication, bounded atlas packing, padding and UV mapping. |
| `lod_geometry` | Convert surfaces to colors, combine them and spatially order triangles for bounded packets. |
| `lod_rectangles` | Lossless coplanar rectangle merging with exact tile boundaries and hard color edges. |
| `block_model` | Resolve blockstate/model JSON into textured faces. |
| `block_geometry` | Voxel state, neighbor masks and approximate block shapes when model data is unavailable. |
| `model_textures` | Resolve model textures and special-part crops into atlas tiles, preserving shapes when a texture is missing. |
| `mesh_models` | Choose JSON models, NBT variants, special shapes and fallbacks; keep explicit hidden indices. |
| `mesh` | Build scene geometry: model preparation, atlas packing, quad emission and flat surfaces. |
| `mesh_export` | Adapt completed geometry to trimesh materials and meshes. |
| `usd_scene` | Adapt completed geometry to USD meshes, materials and a framing camera. |
| `usdz` | Stage and atomically publish USD or package USDZ. |
| `hero` | Adapt completed geometry to PyVista, frame the camera and save the image. |
| `block_colours` | Shared block classification, diagnostic colors, texture averages and dye colors. |

`mesh` prepares models once, calculates neighbor masks, packs the atlas, then
emits ordinary model faces, special block faces, fallback shapes and entities.
`QuadBuffer` owns vertex offsets, accumulated arrays and alpha classification.

The overview uses the same exact model mesher for 16³ leaves. `lod_geometry`
provides colored parent meshes with unchanged block surfaces; it does not select camera detail.
Only adjacent axis-aligned rectangles with identical RGBA merge. Vertices never move;
faces touching a spatial tile boundary retain their original subdivision. Materials
are welded by position and color, so different faces do not acquire interpolated
colors. Nonrectangular model faces remain intact. Geometry error is zero; distant
texture averaging still loses texture detail. Tests compare oriented unit-face coverage
and neighboring seams across six hierarchy levels. This follows
[greedy voxel meshing](https://0fps.net/2012/06/30/meshing-in-a-minecraft-game/).
The [blocky LOD analysis](https://0fps.net/2018/03/03/a-level-of-detail-method-for-blocky-voxels/)
explains quantized geometry and seams; this implementation does not use POP geomorphing.
The historical overview extra remains installable without a native simplifier.
`atlas.merge_mesh_atlases` combines prepared textured meshes through the existing
atlas packer, remapping UV coordinates without changing their sampled pixels.
Snapshot persistence, memory selection and worker scheduling belong to the editor.
`packets` separates materials and compacts/splits immutable geometry into bounded
float32/int32 buffers before any GUI/backend call. It contains no Qt/VTK dependency.
`color_space` shares the linear/sRGB conversion used for HLOD colors and map reduction.
Cutout parent surfaces stay opaque; true blend retains averaged alpha.

Transparent full-cube neighbor culling groups states by block identity instead of
palette index. Leaves retain both oppositely wound internal faces, including their own UV orientation.
Opaque and cutout packets enable backface culling; only the front-facing side of
a coincident pair is drawn. Grass, dripstone and sculk vein use this same rule,
while BLEND remains double-sided. This preserves canopy density without drawing
coincident front and back faces together. Glass/ice states and
fluid levels likewise share the appropriate group; distinct materials retain their
boundary. Model-backed and fallback geometry use the same neighbor rule.
The water neighbor mask includes seagrass, both tall-seagrass halves, kelp and
waterlogged states, so adjacent water does not emit internal faces around them.
This mask only culls fluid faces; plant models and their cutout textures remain
visible, and dry transparent blocks keep their boundary with water.
Fallback shape functions receive the data needed by each shape family.
Coplanar model base/overlay faces with matching UV are composited into one texture
before emission. This avoids grass overlays fighting their base quad.

`PreparedModels` groups resolved models. Each `SpecialModel` owns its palette
index, integer instance positions and parts. NBT variants retain only their
positions; emission reuses one scratch volume and samples neighboring cells
at those positions. Hidden models have a separate set of indices rather than
an empty geometry sentinel mixed with failed texture resolution.

`ModelTextures` owns the operation-local block tile cache. A missing special
texture uses a solid tile with the part's tint and opacity; its geometry stays
visible, and the resource warning still causes strict rendering to fail.

`build_scene_geometry` produces `SceneGeometry` for hero, USD and trimesh.
Both textured and flat meshes have NumPy point and quad arrays. `FlatMesh`
also unpacks as the historical `(color, points, quads)` tuple. Callers choose
a backend after building geometry; backend code has no independent rules for
block visibility or NBT variants. A missing bank explicitly selects diagnostic
cubes and flat entities. Technical invisible blocks remain hidden. Flat
transparent colors do not occlude opaque neighbors; equal colors share a mesh.

The exporter imports shared operations from `geometry` and `atlas`, so it does
not import the mesh assembly module. `mesh.export_parts` retains the historical
entry point and loads the exporter lazily. Existing mesh helper imports remain
available through explicit re-exports. Internal low-level modules import their
dependencies directly rather than going through this compatibility surface.

Prepared JSON block geometry is a flat list of `ModelFace` records per palette
index. Each face has its vertices, tile-local UV coordinates, atlas tile index
and optional culling direction. Element bounds and raw texture references stay
at the JSON resolution boundary; the emitter does not reconstruct these maps.
UV rotation is applied before atlas placement. When only some block textures
are missing, the unresolved faces receive a flat-color tile; when none resolve,
the existing complete-block fallback remains available.

## Projections and SVG

| Module | Responsibility |
|---|---|
| `projection_grid` | View axes, orientation, dimensions, depth selection, visible cells, merged rectangles and contour segments. |
| `overlays` | Validate and project masks, share layer colours/opacity, blend raster layers and load NPZ inputs. |
| `projections` | Paint cells into Pillow images and compose labelled sheets. |
| `svg` | Write XML metadata, block and overlay layers under one document-wide element budget. |

Raster and vector outputs use the same visibility and projected overlay planes.
SVG draws vector outlines; raster keeps the existing envelope edge treatment.
`render_projections` loads and validates a source once before rendering its
views. Geometry helpers do not import the raster or vector writer. Historical
imports such as `projections.VIEWS`, `orient`, `projection_cells`, pixel/depth
helpers and `svg.rectangles` remain available as direct aliases.

The SVG writer separates option validation, block painting, overlay painting
and bounded XML creation. Its element limit includes the root and metadata.
Invalid output extensions are rejected before reading the source.

## Special blocks and entities

| Module | Responsibility |
|---|---|
| `shape_geometry` | Box descriptors, face orientation, model UV unfolding and transformations. |
| `signs` | Sign text parsing, glyph placement, boards and hanging attachments. |
| `entity_shapes` | Factories for special blocks such as chests, beds, banners, pots and fluids. |
| `entity_state` | Entity NBT values, orientation, age and placement coordinates. |
| `mob_catalog` | Supported mob families, texture candidates and approximate rig specifications. |
| `entity_mobs` | Skin selection and source-model/fallback construction for mobs. |
| `entity_objects` | Paintings, item frames, equipment, vehicles and other non-mob objects. |
| `entities` | Handler registry and dispatch of structure entity records. |
| `entity_models` | Read and transform the bundled model-layer catalog. |

Model primitives do not depend on a block or entity catalog. Add a mob's static
specification to `mob_catalog`, its exceptional skin rules to `entity_mobs`, or
a new non-mob renderer to `entity_objects` and register it in `entities`.
Additional sign behavior belongs in `signs`; ordinary special block factories
remain together in `entity_shapes`.

## Resources and checks

`AssetContext` owns the resource source and caches; `TextureBank` reads and
transforms images. The top-level geometry operation activates that context and
the diagnostics scope. Existing atlas limits, strict-mode failures, face order,
alpha modes and colored fallback behavior remain shared by image and model
outputs.

Tests cover atlas bounds, fallback connections, transparent faces, model UVs,
entity placement, sign geometry and exports through installed wheels. When
moving implementation functions, tests patch dependencies in their owning
module while continuing to exercise the existing public entry points.

## Вода в растениях и waterlogged-моделях

`contains_water` определяет жидкость независимо от основной модели блока. SpecialModel хранит отдельную fluid-геометрию. Общие внутренние грани соседних жидкостей скрываются; внешние грани wet/waterlogged-клетки сохраняются даже у модели растения. Граница участка рендера использует halo соседей. Проверки сравнивают площадь, материалы и геометрию на всех шести внешних границах, а edit дополнительно проверяет стыки участков 16³/32³.
