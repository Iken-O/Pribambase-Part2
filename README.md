# Pribambase

Pribambase links Aseprite and Blender for pixel-art heavy workflows, with live texture sync, UV display, sprite helpers, and animation tooling.

## Fork Direction

This fork is being reorganized as an independently maintained codebase.

- Target: Blender 4.2+ extension workflow.

## Repository Layout

- `blender/pribambase/` contains the Blender add-on package.
- `aseprite-extension/` contains the separately installed Aseprite extension package and install notes.
- `tasks.py` is a legacy build script from the previous layout and is not yet the source of truth for the new packaging flow.

## Current State

The repository split is the first restructuring step.

- The Blender add-on still uses the legacy bundled-wheel layout under `blender/pribambase/thirdparty/`.
- The Blender 4.2+ `blender_manifest.toml` migration is the next step.
- The editable Aseprite extension source tree has not been reconstructed yet; the packaged `.aseprite-extension` file is stored in `aseprite-extension/`.

## Legacy Links

- [Original wiki](https://github.com/lampysprites/pribambase/wiki/How-Do-I...)
- [Archived project page](https://www.illusionofmana.art/Pribambase.html)
- [Original setup video](https://www.youtube.com/watch?v=70wyQhKyxFw)

## License

The repository keeps the original license files at the root: [LICENSE](LICENSE) and [COPYING](COPYING).
