#!/usr/bin/env bash
# Regenerates everything from gen/*.py.
#   needs: python3 (+ Pillow for the poster images), blender (4.x, with numpy),
#          lune (https://github.com/lune-org/lune) on PATH or at $LUNE
set -euo pipefail
cd "$(dirname "$0")"
LUNE="${LUNE:-lune}"
python3 gen/emit_lua.py                         # -> roblox/builders/<Map>Builder.server.lua + AssetLibrary.lua
"$LUNE" run tools/export_models.luau .          # -> roblox/<Map>.rbxm, builder .rbxmx, VoxelAssetLibrary.rbxm
blender -b -P tools/blender_meshes.py -- .      # -> exports/meshes/ rock meshes + <Map>_Terrain.fbx, roblox/MeshSwap.lua
"$LUNE" run tools/test_meshswap.luau            # offline check of MeshSwap on every map
"$LUNE" run tools/test_meshswap.luau lying
"$LUNE" run tools/test_meshswap.luau terrain
blender -b -P tools/qa_island.py -- .           # no floating props on any island
blender -b -P tools/blender_build.py -- . "$@"  # -> previews/ renders + tiles (--no-render to skip)
python3 tools/compose_previews.py               # -> previews/*_poster.png, *_assets.png, AllIslands.png
