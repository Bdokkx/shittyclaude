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

## VoxelIsland: what changed

**Kept:** the island's shape, meaning the terraces, mesas, spiral stair path to the summit, the stone arch at the
top left, the dock at the bottom left, the plaza in the middle and the sandy beach with sea stacks.

**Rebuilt to the style bible:**
- **Cliffs:** big slabs (16 wide, 4.5-6 thick, tilted 3-10 degrees) with a grass lip, one continuous sand strip
  and 3 height bands (lavender top, periwinkle middle, deep periwinkle base). No more per-block colour noise.
- **Ground:** 2 tones in large soft patches, with sand, path stone and wood planks for the paths.
- **Clutter:** no scattered tufts, rocks, ferns or mushrooms. Trees stand in clumps, and flowers and bushes are
  in clusters at path edges and tree clumps. About 89% of the walkable ground is open.
- **Hero rocks:** 3 sea stacks as tall slab towers with grass caps. No lumpy mesh rocks.
- **Gameplay layout:**
  - **Hub plaza:** fish fountain, benches in pairs, spawn.
  - **Fish Market:** striped awning, ice trays, hanging fish, scale, big fish sign.
  - **Spear Shop:** timber-frame cottage with recessed windows, blue gable roof, chimney, spear rack and target board.
  - **Upgrade Station:** shed, logs, sawhorse, blueprint easel, scaffolding.
  - **Lighthouse landmark** on the summit.
  - **T-dock:** a 34 x 18 platform with spear rack, buckets, lanterns and a SPEARFISHING sign, over a coral reef.
  - **Travel Boat:** a sailboat with a green sail, at a second pier past the arch.
- **Upgrade tiers:**
  - `Tier1`: short pier, simple stalls, dirt plaza with a well.
  - `Tier2`: T-pier, shop buildings, stone plaza with fountain, lanterns.
  - `Tier3`: second fishing platform, bunting, spinning lighthouse beam.
- **Part count:** 11.8k parts including all tiers (budget 12,000). Small decor has CanCollide and CastShadow off.

The review sheet with every view, the build stages, the tiers and the checklist is
`previews/spear/VoxelIsland_review.png`.

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
