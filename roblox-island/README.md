# Voxel Island + Coral Reef (Roblox)

Two blocky, studded maps based on the reference shots:

| | |
|---|---|
| **VoxelIsland** | terraced rocky mountain with a winding stair path and summit lookout, two cliff mesas (west with a rock arch, east with a banner and a cave entrance below), an open cobblestone village plaza (campfire, market stall, lantern frame, well, statue, signpost, benches, lamps), wooden stairs with railings down to the dock, a rowboat, stepped turquoise shallows and mossy rock stacks offshore. Every cliff is covered in chunky multi-shade blocks with a yellow band and grass lip, and the ground has grass tufts, flowers, ferns, mushrooms, bushes, rocks, fences and torches everywhere |
| **CoralReef** | sandy reef slab with sand-colour patches, rock shelves / pinnacles / arches, boulders, ruined pillars, a tilted shipwreck and ~190 corals (tube, branch, fan, seaweed) in 6 colours |

Previews (rendered in Blender from the same data, with the mesh rocks): `previews/island.png`, `previews/island_village.png`, `previews/reef.png`, `previews/rock_meshes.png`, `previews/rock_meshes_closeup.png`, `previews/assets_contact_sheet.png`.

## Use it in Roblox Studio

### Option A: drop in the finished maps (easiest)
1. In Studio, right-click **Workspace** → **Insert from File…**
2. Pick `roblox/VoxelIsland.rbxm`, then do the same for `roblox/CoralReef.rbxm` (the reef sits at Z = 700 so they don't overlap).
3. Open **View → Command Bar**, paste in everything from `roblox/LightingAndWater.lua` and press Enter.
   That swaps the placeholder ocean for real terrain water and sets up the bright, saturated lighting
   (Future lighting, atmosphere, color correction, bloom). **This makes a big difference.** Studio's default
   lighting washes the colors out.

4. **Optional: deformed mesh rocks (the look from the reference screenshots).**
   - **File → Import 3D** → `exports/meshes/VoxelRockMeshes.fbx` (keep the defaults; it lands in Workspace).
   - Paste everything from `roblox/MeshSwap.lua` into the Command Bar and press Enter.
   - It swaps every reef pinnacle, shelf, arch, boulder, seaweed, offshore rock and the island arch for the
     Blender meshes. These are lumpy and faceted, with studs baked into the texture and sand/grass/moss tops.
     The old part versions go to `ServerStorage.VoxelPartRocks`, and Ctrl+Z undoes it. Afterwards you can delete
     the imported `VoxelRockMeshes` model.

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

### How the mesh rocks are made
`tools/blender_meshes.py` runs in Blender. It takes each rock's blocky base shape from `gen/assets.py`,
fuses it with a voxel remesh, **deforms** it with two layers of noise displacement and decimates it into big
facets. Faces pointing up become a separate sand, grass or moss mesh. Everything gets box-projected UVs
(1 UV unit = 4 studs) on a tiling stud texture (`exports/meshes/studs_*.png`), so the studs line up across
faces. Each rock is exported as `<Name>_Rock` + `<Name>_Top` mesh parts, both one by one and all together
in `VoxelRockMeshes.fbx`. Tune `disp` (how lumpy), `noise` (size of the lumps) and `faces` (how faceted) in
`MESH_SOURCES` in `gen/assets.py`.

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

Part counts: island ≈ 30k, reef ≈ 13k (all anchored, static; MeshSwap lowers them). That's fine on PC and console. On low-end phones, use
StreamingEnabled, or swap trees and rocks for the imported meshes.
