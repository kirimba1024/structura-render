# Small, reproducible render inputs

`demo.nbt` is an authored house with stairs, windows, leaves, water, a chest and
a bilingual sign. It targets Java 1.21.1 and needs no resources for projections:

```sh
structura-render projections demo.nbt demo.png
```

Install `[hero]` or `[gltf]` and point at a matching Minecraft client for textures:

```sh
structura-render png demo.nbt house.png --orthographic --transparent
structura-render glb demo.nbt house.glb
```

The `--showcase` option additionally copies two compact diagnostic catalogs:

- `blocks.nbt`: all 1,195 non-air block IDs from the Java 26.2 reference assets,
  plus selected slab/stair orientations and shapes. This is one representative
  per ID and selected edge cases, not every combination of block properties.
- `entities.nbt`: all 162 entity IDs handled by this renderer, with labels,
  signs, banners, paintings, item frames and equipment. Legacy aliases and
  technical markers are intentionally included as renderer fixtures.

Use Java 26.2 assets for the full catalogs. Paintings also need the adjacent
`data/minecraft/painting_variant` registry (included when a client jar is used).
The catalog DataVersion is 4903, verified against the official 26.2 client.
These are static render probes; game-valid placement of every technical or
legacy entity is not claimed. Invisible technical blocks can remain invisible.
Catalog membership does not certify exact geometry, animation or every variant.

`coverage.json` records counts, dimensions and file hashes. PNGs, atlases and
3D exports are generated only on request. No client textures or models are bundled.
Copying the same examples again is harmless; modified files are not overwritten.

The existing Structura repository tools `build_block_gallery.py` and
`build_render_probe.py` remain the sources of the full catalogs;
`tools/build_examples.py` rebuilds this compact package from their saved inputs.
The probe generator's optional `--pages` produces smaller review pages on demand.
