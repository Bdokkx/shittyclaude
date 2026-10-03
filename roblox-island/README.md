# Voxel Island + Coral Reef (Roblox)

Two blocky, studded maps based on the reference shots:

| | |
|---|---|
| **VoxelIsland** | terraced rocky mountain with a winding stair path and summit lookout, two cliff mesas (west with a rock arch, east with a banner and a cave entrance below), an open cobblestone village plaza (campfire, market stall, lantern frame, well, statue, signpost, benches, lamps), wooden stairs with railings down to the dock, a rowboat, stepped turquoise shallows and mossy rock stacks offshore. Every cliff is covered in chunky multi-shade blocks with a yellow band and grass lip, and the ground has grass tufts, flowers, ferns, mushrooms, bushes, rocks, fences and torches everywhere |
| **CoralReef** | sandy reef slab with sand-colour patches, rock shelves / pinnacles / arches, boulders, ruined pillars, a tilted shipwreck and ~190 corals (tube, branch, fan, seaweed) in 6 colours |

Previews (rendered in Blender from the same data): `previews/island.png`, `previews/island_village.png`, `previews/reef.png`, `previews/assets_contact_sheet.png`.

## Use it in Roblox Studio

### Option A: drop in the finished maps (easiest)
1. In Studio, right-click **Workspace** → **Insert from File…**
2. Pick `roblox/VoxelIsland.rbxm`, then do the same for `roblox/CoralReef.rbxm` (the reef sits at Z = 700 so they don't overlap).
3. Open **View → Command Bar**, paste in everything from `roblox/LightingAndWater.lua` and press Enter.
   That swaps the placeholder ocean for real terrain water and sets up the bright, saturated lighting
   (Future lighting, atmosphere, color correction, bloom). **This makes a big difference.** Studio's default
   lighting washes the colors out.

### Option B: the builder script
`roblox/VoxelIslandBuilder.server.lua` builds both maps from code (all asset shapes and the layout are inside it).
- Right-click **ServerScriptService** → **Insert from File…** → `roblox/VoxelIslandBuilder.rbxmx`
  (or make a Script and paste the `.lua` file in).
- Press **Play**. It builds `Workspace.VoxelIsland` + `Workspace.CoralReef`, fills real terrain water and applies the lighting preset.
- Settings live in the `CONFIG` table at the top (origins, studs on/off, terrain water, reef underwater, …).
- The script also exposes `Builder.spawnAsset("PineTree", CFrame.new(x, y, z), scale, tint, parent)`
  if you want to place assets from your own code.

Option B rebuilds the map every time the game starts. If you want the map saved in your place
file, use Option A (or press Play, copy the built models, Stop, and paste them).

### Using the Blender meshes instead of parts
Every asset is also a real mesh in `exports/` (FBX, GLB and OBJ, coloured by one small palette
texture `voxel_palette.png`). Coral assets have a file per colour (`TubeCoral_Pink.fbx`, …).

1. **File → Import 3D** in Studio and pick e.g. `exports/fbx/PineTree.fbx`.
2. Put the imported models in a folder `ReplicatedStorage.IslandAssets`, each named exactly like the
   asset (`PineTree`, `Dock`, `Shipwreck`, …).
3. With `CONFIG.UseImportedMeshes = true` (default) the builder script clones your meshes instead of
   building the part versions, so you get far fewer parts. (Tinted corals still use parts.)

## Assets

PineTree, PineTreeTall, PineTreeSmall, Bush, GrassTuft, Flowers, Fern, Mushrooms, SmallRock, RockOutcrop, RockOutcropBig, RockOutcropSmall, Boulder, Arch, Seaweed, TubeCoral, BranchCoral, FanCoral, ReefPinnacle, ReefShelf, ReefArch, RuinPillar, Dock, Rowboat, Shipwreck, MarketStall, Campfire, LampPost, Torch, WoodFrame, Statue, Signpost, Bench, Well, FlagFrame, Fence, CrateStack, Barrels, LogPile, CaveEntrance, WoodenStairs.

`roblox/VoxelAssetLibrary.rbxm` has all of them lined up as part-built models, ready to copy into any scene.
`blender/voxel_assets.blend` and `blender/voxel_maps.blend` are the Blender scenes.

## Changing things / regenerating

Everything comes from three Python files:

- `gen/assets.py`: asset shapes (lists of boxes)
- `gen/island.py`: island layout (height field, mesas, paths, cliff facades, prop scatter)
- `gen/maps.py`: reef layout
- `gen/palette.py`: colours

Then run `./build.sh` (needs `python3`, `blender` 4.x and [`lune`](https://github.com/lune-org/lune)).
It regenerates the Lua script, the `.rbxm` files (built by running the real Lua builder offline)
and the Blender exports and renders. Change `seed` in `build_island()` / `build_reef()` to get a new layout.

Part counts: island ≈ 25k, reef ≈ 11.6k (all anchored, static). That's fine on PC and console. On low-end phones, use
StreamingEnabled, or swap trees and rocks for the imported meshes.
