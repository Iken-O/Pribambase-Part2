# Pribambase Aseprite Extension

This directory contains the source for the separately installed Aseprite companion used by Pribambase.

## Install

- End users should install a packaged `pribambase_aseprite.aseprite-extension` file from a release artifact.
- In Aseprite, use `Edit > Preferences > Extensions > Add Extension`, or open the packaged file directly.
- The Aseprite companion is installed separately from the Blender extension.

## Source Layout

- `package.json` defines the Aseprite extension metadata.
- `Commands.lua`, `Settings.lua`, and `Sync.lua` are the editable source files.
- `COPYING` is kept with the extension source because it is also included in the packaged artifact.

## Packaging

- Package the contents of this directory into a zip archive.
- Rename the archive to `pribambase_aseprite.aseprite-extension`.
- Zip the files in this directory directly, not the parent folder.

## Relationship to Blender

- The Blender extension source lives in `blender/pribambase/`.
- Blender launches Aseprite with `blender/pribambase/scripts/start.lua`, while this directory contains the Aseprite-side extension itself.
