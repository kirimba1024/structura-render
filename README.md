# structura-rendering

Reusable renderer extracted from Structura. Blockstate/model JSON is resolved
into mesh geometry once and shared by PNG and USDZ exporters. The package does
not redistribute Mojang textures or models.

Point it at a licensed Minecraft client, either the `.jar` directly or an
already-extracted `assets/minecraft` directory:

```bash
export STRUCTURA_MINECRAFT_ASSETS="$HOME/Library/Application Support/minecraft/versions/1.21.1/1.21.1.jar"
pip install 'git+https://github.com/kirimba1024/structura-structures.git'
pip install -e '.[usdz]'
structura-render-hero structure.nbt preview.png
```

A `.jar` is extracted once into `$XDG_CACHE_HOME/structura-rendering/jar-assets`
(`~/.cache/...` if unset), keyed by its path, size and mtime, so different
client versions and later runs against the same jar don't re-extract. Point
at an `assets/minecraft` directory directly to skip that step entirely. When
the environment variable is absent, the package searches parent folders and
the current directory for `assets/minecraft`.

`structura-structures` is private, so Git must be authenticated for the
first install command. Use the lighter `hero` extra when USDZ export is not
needed; plain projection rendering does not install PyVista or OpenUSD.
