# structura-render

**Turn a Minecraft Structure NBT into a real photo or a 3D file — using
your own game's actual textures and block shapes, not guesses.**

No fake textures, no hardcoded block shapes, no bundled game files. Point
it at your own Minecraft client and get pixel-accurate PNGs and a 3D file
(USDZ, glTF/GLB, OBJ or STL) out the other end.

**This isn't a lookup table of ~50 common blocks with guessed shapes.**
The resolver walks the same blockstate → multipart/variant → model → element
rotation → UV pipeline the Minecraft client itself uses, so ordinary vanilla
blocks — stairs, doors, fences, plants, redstone and the rest — come from the
game's data rather than per-block guesses. Vanilla's non-model renderers
(chests, banners, heads, shulker boxes, conduit, bell, decorated pots,
portals and fluids) share a compact textured compound-model layer.

<p>
  <img src="docs/screenshots/usdz-floating-island.png" width="49%" alt="USDZ export of a floating island structure, viewed in a 3D viewer">
  <img src="docs/screenshots/hero-render-detail.png" width="49%" alt="Close-up hero-render detail: windows, timber framing, flower pots">
</p>

## Why it's worth using

- **Data-driven where vanilla is.** JSON-modelled blocks use the same
  blockstate/model data and PNGs as the game. Dynamic blocks use their real
  entity textures on compact state-aware compound geometry.
- **One mesh, every output.** Geometry is resolved once and shared between
  PNG renders and every 3D export (USDZ, glTF, OBJ, STL), so what you
  preview is exactly what you get in 3D — nothing drifts between formats.
- **Clean by design.** Zero Mojang assets in this repo or its releases —
  can't, EULA forbids it. You always supply your own client, so there's no
  legal grey area to worry about.
- **Version-flexible.** Point it at a `.jar` from Minecraft 1.13 through
  the latest release and it just works — verified end to end on both
  1.21.1 and the newest 26.2. New blocks resolve automatically; no waiting
  on us to add support.
- **Light by default.** Core install is just NumPy, Pillow and SciPy.
  PyVista and the format-specific libraries (USD, trimesh) only get pulled
  in if you actually ask for hero renders or a given 3D export.
- **Self-updating classification.** Which blocks are solid cubes (for
  occlusion) is computed from real model geometry, not a hand-maintained
  name list — it doesn't go stale as new blocks ship.

## What it does

- **`block_model.py`** — generic blockstate/model resolver: variants,
  multipart conditions, parent chains, element rotations, UV rotation and
  UV locking. Builds real geometry for every JSON-modelled vanilla block.
- **`textures.py`** — resolves `#variable` texture references and samples
  the real PNG, including per-pixel alpha for correct occlusion (glass,
  leaves, iron bars).
- **`projections.py`** — six-view orthographic PNGs (top/bottom/N/S/E/W)
  with envelope/aura/terrain-pod/glass-dome mask overlays, for engineering
  QA rather than looks.
- **`hero.py`** (`hero` extra) — one real-textured, real-lit PyVista render
  of the finished structure — the kind of shot above.
- **`usdz.py`** (`usdz` extra) — a textured USDZ mesh for AR Quick Look,
  from the same mesh builder as the hero renderer.
- **`gltf.py`** (`gltf` extra) — a textured `.glb`, for the web
  (`<model-viewer>`, three.js), Android AR Scene Viewer, Blender and every
  other glTF-reading tool.
- **`obj.py`** (`obj` extra) — textured Wavefront OBJ + MTL, for Blender,
  MeshLab and any classic 3D tool.
- **`stl.py`** (`stl` extra) — binary STL geometry (no color/texture — the
  format doesn't have one), for 3D printing or any STL reader.
- **`build_full_cube_list.py` / `build_opaque_blocks.py`** — data-derived
  block classification, described above.
- **`docs/block-render-audit-26.2.md`** — one row for every vanilla
  blockstate, including explicit dynamic-render limitations.
- **`legacy_input.py`** (`legacy` extra) — every entry point also accepts a
  legacy `.schematic`, sponge `.schem`, `.litematic`, or anything else
  [amulet-core](https://github.com/Amulet-Team/Amulet-Core) recognizes, and
  converts it to Structure NBT on the fly. No manual conversion step.

## Quick start

```bash
export STRUCTURA_MINECRAFT_ASSETS="$HOME/Library/Application Support/minecraft/versions/1.21.1/1.21.1.jar"
pip install "structura-render[usdz]"
structura-render-hero structure.nbt preview.png
structura-export-usdz structure.nbt model.usdz
```

Swap `[usdz]` for `[gltf]`, `[obj]` or `[stl]` (or several, comma-separated)
for the other 3D formats — `structura-export-gltf`, `structura-export-obj`,
`structura-export-stl` follow the same `src dst` signature.

Have a legacy `.schematic`/`.schem`/`.litematic` instead of Structure NBT?
Add the `legacy` extra (`[usdz,legacy]`) and pass it straight in — no
separate conversion step:

```bash
structura-render-hero house.schematic preview.png
```

Point `STRUCTURA_MINECRAFT_ASSETS` at a client `.jar` (any version from
1.13 up) or an already-extracted `assets/minecraft` directory. A `.jar` is
extracted once into `$XDG_CACHE_HOME/structura-render/jar-assets`
(`~/.cache/...` if unset), keyed by its path, size and mtime, so repeat
runs and multiple installed versions don't re-extract or collide. When the
variable is unset, the package searches parent folders and the current
directory for `assets/minecraft`.

This project's own datapack targets Minecraft Java 1.21.1 specifically
(`structura_core.version.JAVA_VERSION`); if you're previewing *its*
structures, match that version for a guaranteed-correct result. Anything
older than 1.13 uses a different asset layout entirely (pre-"flattening")
and isn't supported. On load, the package checks for `heavy_core` (added
in 1.21) and warns on stderr if it's missing, as a cheap signal that the
pointed-at client predates 1.21 — not exhaustive, just a sanity check.

Use the lighter `hero` extra when no 3D export is needed; plain projection
rendering (`structura-render-projections`, no extra) skips PyVista and
every format-specific library entirely.
