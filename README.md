# Pribambase

Pribambase links Aseprite and Blender for pixel-art heavy workflows, with live texture sync, UV display, sprite helpers, and animation tooling.

## Fork Direction

This fork is being reorganized as an independently maintained codebase.

- Target: Blender 4.2+ extension workflow.

## Repository Layout

- `blender/pribambase/` contains the Blender extension package.
- `aseprite-extension/` contains the separately installed Aseprite extension package and install notes.

## Current State

The repository split and Aseprite source recovery are done. The Blender package now has extension metadata and bundled Windows x64 and Linux x64 wheels for Blender 4.2+.

- The Blender extension root is `blender/pribambase/`.
- `blender_manifest.toml` and `wheels/` are in place for Blender's extension system.
- Windows x64 and Linux x64 wheel bundles cover both Python 3.11 and Python 3.13 builds.
- The Aseprite companion source now lives directly in `aseprite-extension/`.
- Release artifacts should be generated from source instead of stored in the repository.

## Build Notes

- Downloaded wheel sources are pinned in `blender/requirements-wheels.txt`.
- The extension package currently targets Windows x64 and Linux x64.
- Build the Blender extension from `blender/pribambase/`.
- Use `blender --command extension build --split-platforms` to generate platform-specific zip files.
- Use `scripts/build-release.ps1` to build the Blender extension and package the Aseprite extension into one release output directory.

## Release Packaging

From the repo root:

```powershell
.\scripts\build-release.ps1
```

- Default output is `dist/release/`.
- Pass `-BlenderPath 'C:\path\to\blender.exe'` to override Blender discovery.
- Pass `-Clean` to remove previous release artifacts before rebuilding.

## Legacy Links

- [Original wiki](https://github.com/lampysprites/pribambase/wiki/How-Do-I...)
- [Archived project page](https://www.illusionofmana.art/Pribambase.html)
- [Original setup video](https://www.youtube.com/watch?v=70wyQhKyxFw)

## License

The repository keeps the original license files at the root: [LICENSE](LICENSE) and [COPYING](COPYING).
