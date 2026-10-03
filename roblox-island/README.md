# Voxel Island + Coral Reef (Roblox)

Two blocky, studded maps based on the reference shots:

| | |
|---|---|
| **VoxelIsland** | terraced periwinkle-rock island with grass tops and yellow cliff bands, a mountain, a plaza (campfire, market stall, lamps, ruins), a stone stair path down to the beach, a dock with a lantern, a rowboat, an east-cliff banner, a rock arch, ~110 pines, offshore rock spires and sea water |
| **CoralReef** | sandy reef slab with sand-colour patches, rock shelves / pinnacles / arches, boulders, ruined pillars, a tilted shipwreck and ~190 corals (tube, branch, fan, seaweed) in 6 colours |

Previews (rendered in Blender from the same data): `previews/island.png`, `previews/reef.png`, `previews/assets_contact_sheet.png`.

## Use it in Roblox Studio

### Option A: drop in the finished maps (easiest)
1. In Studio, right-click **Workspace** → **Insert from File…**
2. Pick `roblox/VoxelIsland.rbxm`, then do the same for `roblox/CoralReef.rbxm` (the reef sits at Z = 700 so they don't overlap).
3. Water: the island ships with a see-through `Ocean` part so it works immediately.
   For real swimmable water, delete `VoxelIsland.Ocean` and run this in the **Command Bar**:
   ```lua
   workspace.Terrain:FillBlock(CFrame.new(0, -7, 0), Vector3.new(600, 14, 600), Enum.Material.Water)
   ```

### Option B: the builder script
`roblox/VoxelIslandBuilder.server.lua` builds both maps from code (all asset shapes and the layout are inside it).
- Right-click **ServerScriptService** → **Insert from File…** → `roblox/VoxelIslandBuilder.rbxmx`
  (or make a Script and paste the `.lua` file in).
- Press **Play**. It builds `Workspace.VoxelIsland` + `Workspace.CoralReef` and fills real terrain water.
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

PineTree, PineTreeTall, Bush, Rock, RockSpire, Boulder, Arch, Seaweed, TubeCoral, BranchCoral,
FanCoral, ReefPinnacle, ReefShelf, ReefArch, RuinPillar, Dock, Rowboat, Shipwreck, MarketStall,
Campfire (with light and fire), LampPost (light), FlagFrame (banner and lantern), Fence, CrateStack, WoodenStairs.

`roblox/VoxelAssetLibrary.rbxm` has all of them lined up as part-built models, ready to copy into any scene.
`blender/voxel_assets.blend` and `blender/voxel_maps.blend` are the Blender scenes.

## Changing things / regenerating

Everything comes from three Python files:

- `gen/assets.py`: asset shapes (lists of boxes)
- `gen/maps.py`: island and reef layout (seeded noise, terraces, path, prop scatter)
- `gen/palette.py`: colours

Then run `./build.sh` (needs `python3`, `blender` 4.x and [`lune`](https://github.com/lune-org/lune)).
It regenerates the Lua script, the `.rbxm` files (built by running the real Lua builder offline)
and the Blender exports and renders. Change `seed` in `build_island()` / `build_reef()` to get a new layout.

Part counts: island ≈ 5.5k, reef ≈ 5.1k (all anchored). That's fine for most games. Use the imported meshes if you need fewer.
