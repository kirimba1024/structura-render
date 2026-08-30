# structura-rendering

Reusable renderer extracted from Structura. Blockstate/model JSON is resolved
into mesh geometry once and shared by PNG and USDZ exporters. The package does
not redistribute Mojang textures or models.

Point it at assets extracted from the matching licensed Minecraft client:

```bash
export STRUCTURA_MINECRAFT_ASSETS=/path/to/assets/minecraft
pip install 'git+https://github.com/kirimba1024/structura-structures.git'
pip install -e '.[usdz]'
structura-render-hero structure.nbt preview.png
```

When the environment variable is absent, the package searches parent folders
and the current directory for `assets/minecraft`.

Both repositories are private, so Git must be authenticated for the first
install command. Use the lighter `hero` extra when USDZ export is not needed;
plain projection rendering does not install PyVista or OpenUSD.
