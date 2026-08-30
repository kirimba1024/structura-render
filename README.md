# structura-render

Renderer and 3D exporter for vanilla Minecraft Structure NBT. It resolves
real blockstate/model JSON into mesh geometry once and shares that geometry
between every output format, instead of guessing block shapes from a name.

<p>
  <img src="docs/screenshots/usdz-floating-island.png" width="49%" alt="USDZ export of a floating island structure, viewed in a 3D viewer">
  <img src="docs/screenshots/hero-render-detail.png" width="49%" alt="Close-up hero-render detail: windows, timber framing, flower pots">
</p>

## What it does

- **Generic blockstate/model resolution** (`block_model.py`) — walks real
  vanilla blockstate JSON (variants and multipart) and model JSON (parent
  chains, element cuboids, per-face UV and rotation) to build actual block
  geometry: doors, stairs, slabs, cross-plants, chests, signs, decorated
  pots, shulker boxes and everything else, not a per-block-name special case.
- **Real texture lookup** (`textures.py`) — resolves `#variable` texture
  references through the model's parent chain and samples the real PNG,
  including per-pixel alpha for correct occlusion (glass, leaves, iron bars).
- **Diagnostic projections** (`projections.py`) — six-view orthographic PNGs
  (top/bottom/N/S/E/W) with envelope, aura, terrain-pod and glass-dome mask
  overlays, for engineering QA of generated geometry rather than looks.
- **Hero rendering** (`hero.py`, needs the `hero` extra) — a single
  real-textured, real-lit PyVista render of the finished structure, the kind
  of shot in this README.
- **USDZ export** (`usdz.py`, needs the `usdz` extra) — a textured 3D mesh
  for AR Quick Look / any USDZ-capable viewer, sharing the same mesh builder
  as the hero renderer.
- **Data-derived block classification** (`build_full_cube_list.py`,
  `build_opaque_blocks.py`) — which blocks are full opaque cubes (for
  occlusion culling) is computed from real model geometry, not a hand-kept
  name list, so it stays correct as new blocks are added upstream.

Useful for: visually reviewing generated/procedural Minecraft structures,
building preview images or AR previews for a build/structure library, and
any tool that needs real vanilla block geometry without shipping a game
copy.

## Setup

Point it at a **Minecraft Java 1.21.1** client, either the `.jar` directly
or an already-extracted `assets/minecraft` directory:

```bash
export STRUCTURA_MINECRAFT_ASSETS="$HOME/Library/Application Support/minecraft/versions/1.21.1/1.21.1.jar"
pip install 'git+https://github.com/kirimba1024/structura-core.git'
pip install -e '.[usdz]'
structura-render-hero structure.nbt preview.png
```

**The version matters, not just "some Minecraft install."** This package
targets Minecraft Java **1.21.1** specifically (see
`structura_core.version.JAVA_VERSION`); the asset layout changed
significantly across versions (e.g. the pre/post-1.13 "flattening" of
texture and blockstate paths), so pointing at a mismatched jar can silently
resolve the wrong texture or geometry for a given block. On load, the
package checks for `heavy_core` (a block added in 1.21) and prints a
warning to stderr if it's missing, as a cheap sanity check against an
obviously-wrong version — but it can't detect every mismatch, so use 1.21.1.

Neither this repository nor its releases contain any Mojang texture, model,
or sound file. Minecraft's client assets are copyrighted and Mojang's EULA
does not permit redistributing them, so `structura-render` never bundles
or vendors them — you always point it at your own licensed client via
`STRUCTURA_MINECRAFT_ASSETS`, as above.

A `.jar` is extracted once into `$XDG_CACHE_HOME/structura-render/jar-assets`
(`~/.cache/...` if unset), keyed by its path, size and mtime, so different
client versions and later runs against the same jar don't re-extract. Point
at an `assets/minecraft` directory directly to skip that step entirely. When
the environment variable is absent, the package searches parent folders and
the current directory for `assets/minecraft`.

Use the lighter `hero` extra when USDZ export is not needed; plain
projection rendering does not install PyVista or OpenUSD.
