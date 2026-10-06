# Spearfishing Islands (Roblox)

Islands for a stud-style spearfishing game, rebuilt to the **SpearFish_Map_Prompts** pack
(`SpearFish_Map_Promptsdddd.zip`: style bible, problem list, one prompt per map, reference images).

Order from the pack: **VoxelIsland first (for approval)**, then DesertCoast, FrostCoast, VolcanicIsland.

| Island | Origin | Status |
|---|---|---|
| **VoxelIsland** (grass, starter) | 0, 0, 0 | **rebuilt, waiting for approval** |
| DesertCoast | 1300, 0, 0 | next, after VoxelIsland is approved (old version still in `roblox/`) |
| FrostCoast | 2600, 0, 0 | after that |
| VolcanicIsland | 3900, 0, 0 | after that |

## VoxelIsland (compact version)

A hand-laid island about 290 studs across (`spear/small_island.py`). The earlier full-size
version is still available as `spear/voxel_island.py` (`python3 spear/build.py VoxelIslandLarge`).

- **Terraces:** a beach ring (y=3), the main lawn (y=12) and a hill (y=24). The cliffs between them are
  banded slabs with grass lips.
- **Hub:** a plain stone floor with no centerpiece. Fish Market, Spear Shop and Upgrades stalls stand
  around it, each with a glowing pad (`ShopPad_*`).
- **Portal:** a ledge west of the hub holds the Blender portal (`exports/portal/Portal.fbx`, snapped onto
  `PortalSpot` by `roblox/PlacePortal.lua`).
- **Lighthouse:** on the hill with its keeper's cottage, reached by stone stairs. A waterfall runs from
  the hill into a pond.
- **Dock:** wooden stairs lead down to a T-dock with rails over a coral reef. Tier 3 adds fishing wings
  and a canopy.
- **Nature:** clumps of six tree types, palm pairs around the beach, a beach camp, grass tufts and
  flower clusters.
- **Size:** about 10,000 parts. Four open **quest clearings** on the lawn (invisible `QuestClearing_1..4` markers, each with a QUEST sign) are kept free for your quests. The self-review checklist passes 10/10.
- **Tiers:**
  - Tier 1: short pier, dirt hub floor.
  - Tier 2: T-dock, stone floor, lanterns.
  - Tier 3: wings, canopy, pennants, lighthouse beam.

## Use it in Roblox Studio
1. Right-click **Workspace** → **Insert from File…** → `roblox/VoxelIsland.rbxm`.
2. **View → Command Bar**, paste all of `roblox/LightingAndWater.lua` and press Enter. This:
   - moves the island into `Workspace/Islands`
   - fills clear terrain water
   - moves the Baseplate away
   - applies the island's lighting preset (ClockTime 14, atmosphere, colour correction, bloom, water `#2E9BE6`)
3. **Studs:** every Plastic part uses Roblox's built-in **Inlet** surface (an inset square per stud, the same size
   everywhere). To use a MaterialVariant instead:
   - Upload `exports/studs/StudInset_color.png`.
   - Run the builder with `StudMode = "Variant"` and the asset id filled in.
4. **Tiers:** the island ships at tier 3. To switch:
   `require(workspace.Islands.VoxelIsland.IslandTiers).SetTier(workspace.Islands.VoxelIsland, 1)`.
5. **Teleports:** call `require(island.IslandLighting).Apply(island)` to switch the lighting.

**Builder script instead of the .rbxm:** `roblox/builders/VoxelIslandBuilder.server.lua` is a standalone Luau
builder. Put it in ServerScriptService and press Play, or paste it into the Command Bar. It builds the same model.

Folder layout: `Workspace/Islands/VoxelIsland/{Terrain, Dock, Reef, Buildings, Props, Lighting, Spawns, Tier1, Tier2, Tier3}`.

## How it's built
- `spear/` (Python) generates everything:
  - `core.py`: parts with full rotations in nested frames, plus exact octagons.
  - `terrain.py`: slab stacks, stairs, paths.
  - `terraced.py`: takes the island shape from the original generator (`gen/island.py`) and rebuilds the surfaces,
    cliffs, sea shelves and reef ring.
  - `props.py`, `buildings.py`: the asset and building kits.
  - `voxel_island.py`: the VoxelIsland layout.
  - `emit.py` + `builder_template.lua`: write the standalone Luau builder.
- `tools/export_spear.luau` (Lune) runs that builder offline, writes `roblox/<Map>.rbxm` and tests the tier toggle.
- `tools/render_spear.py` (Blender) renders the previews from the same data, one inset stud per world stud.
  `tools/render_spear_all.sh` renders the full set.
- `tools/check_spear.py` runs the self-review checklist. `tools/compose_spear.py` makes the review sheet.

```
python3 spear/build.py VoxelIsland
lune run tools/export_spear.luau . VoxelIsland
python3 tools/check_spear.py VoxelIsland
./tools/render_spear_all.sh VoxelIsland && python3 tools/compose_spear.py VoxelIsland
```

## Older pipeline
`gen/`, `tools/blender_*.py`, `roblox/MeshSwap.lua` and the other `roblox/*.rbxm` files are the previous generator.
The new islands reuse its island shapes only. DesertCoast, FrostCoast and VolcanicIsland will move to the new
pipeline after VoxelIsland is approved.
