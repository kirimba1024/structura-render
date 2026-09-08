# Render 0.8.1 release verification

Verified on 2026-09-08 with core 0.6.1. The base, legacy and Bedrock dependency
ranges require core >=0.6.1,<0.7. Publish core before render.

The shared scene pipeline and projection refactoring retain the existing Python
API and CLI. Missing-texture geometry, transparent surfaces and entity placement
have export regression coverage. Diagnostics now use the actual base
dependencies and include SVG, VOX and all USD encodings.

| Check | Result |
|---|---|
| Combined core/render source suites | 598 passed, two validator tests run separately |
| Combined installed-wheel suites outside source checkout | 598 passed, two validator tests run separately |
| Khronos glTF/GLB validation of installed exports | 2 passed |
| Fresh base installation: core suite and render integration | 290 passed, 51 optional translation tests skipped |
| Edit session, formats, selection, spatial, sections and preview | 52 passed |
| Both installed public APIs with Pyright | Zero errors and warnings |
| Wheel/sdist builds, Twine, Ruff, whitespace checks | Passed |
| Fresh base dependency consistency | pip check passed |

The fresh environment contains neither SciPy, geo, Amulet Core nor any graphics
backend. The packaged demo produces projection PNG, SVG and VOX through the CLI.
VOX reports its expected shape/transparency approximations. Strict Sponge export
correctly rejects the demo's sparse missing cells becoming air.

CI verifies installed wheels on Linux (Python 3.9 and 3.11), macOS and Windows,
checks extras independently, validates public types and glTF interoperability.
The base-extra job also exercises projections, vector/voxel exports, packaged
examples and diagnostics without analysis or graphics dependencies. Publication
depends on these checks and on matching the release tag to package metadata.
