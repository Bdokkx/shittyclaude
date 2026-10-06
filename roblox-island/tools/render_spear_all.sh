#!/usr/bin/env bash
# Full preview set for one island: stage-by-stage, tiers, and every camera view.
set -euo pipefail
MAP="${1:-VoxelIsland}"
R="blender -b -P tools/render_spear.py -- . $MAP"
$R --views=overhead --stages=terrain --suffix=_stage1_terrain --samples=32
$R --views=overhead --stages=terrain,dock,reef --suffix=_stage2_dock_reef --samples=32
$R --views=overhead --stages=terrain,dock,reef,buildings --suffix=_stage3_buildings --samples=32
$R --views=overhead --tier=1 --suffix=_tier1 --samples=32
$R --views=overhead --tier=2 --suffix=_tier2 --samples=32
$R --views=overhead --tier=3 --beam=1 --suffix=_tier3 --samples=32
$R --samples=48
