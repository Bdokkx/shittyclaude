#!/usr/bin/env bash
# Regenerates everything from gen/*.py.
#   needs: python3, blender (4.x, with numpy), lune (https://github.com/lune-org/lune)
set -euo pipefail
cd "$(dirname "$0")"
python3 gen/emit_lua.py                       # -> roblox/VoxelIslandBuilder.server.lua
lune run tools/export_models.luau .           # -> roblox/*.rbxm + builder .rbxmx
blender -b -P tools/blender_build.py -- . "$@" # -> exports/, blender/, previews/  (--no-render to skip renders)
