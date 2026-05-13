# Blender Extension

The Blender extension package root is `blender/pribambase/`.

- `blender_manifest.toml` lives in that package root and replaces legacy `bl_info` metadata.
- Third-party dependencies should live under `pribambase/wheels/` and be listed in the manifest.
- Build from inside `blender/pribambase/` with Blender's extension CLI.
- `pribambase/scripts/start.lua` remains part of the Blender package because Blender passes it to Aseprite on launch.
