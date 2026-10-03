# Voxel Islands + Coral Reef (Roblox)

Four themed blocky, studded islands plus an underwater reef, built from the reference shots.
The islands are built the same way as the coral reef:
- **Parts** make up the terrain: ground, stacked slab cliffs with sand, grass or snow lips, paths, stairs, buildings and falls.
- **Deformed Blender meshes** are only used where they make it look good: crags, rock clusters, ledges,
  sea stacks and arches tucked into the part cliffs so they blend in.

| Map | Origin | What's on it |
|---|---|---|
| **VoxelIsland** | 0, 0, 0 | green terraced mountain with a stair path spiralling to a summit lookout, two cliff mesas (banner, cave), rock arch, cobblestone village plaza, dock + rowboat, waterfall, turquoise shallows, sea stacks |
| **DesertCoast** | 1300, 0, 0 | red sandstone mesas around an oasis lake with a waterfall, a ziggurat, obelisks and sandstone pillars, an adobe village with market stalls, pots and a well, palms and cacti, desert rock stacks offshore |
| **FrostCoast** | 2600, 0, 0 | snowy mountain with a spiral path to a flag lookout, ice cliffs, a frozen pond and frozen waterfall, log-cabin village with snowmen, snow pines, ice crystals, icebergs out at sea |
| **VolcanicIsland** | 3900, 0, 0 | volcano cone with a glowing crater lava pool, lava rivers and lava falls down the terraces, basalt columns, obsidian shards, charred pines, stilt-hut village with braziers |
| **CoralReef** | 0, 0, 900 | sandy reef slab, rock shelves / pinnacles / arches, boulders, ruined pillars, a tilted shipwreck and ~190 corals |

## Previews (`previews/`)

- `AllIslands.png`: the four islands side by side.
- `<Map>_poster.png`: overview, top view, village, detail and falls close-ups for each island.
- `<Map>_assets.png`: every custom asset for that island, rendered in Blender and labelled.
- The single renders are also there: `<Map>.png`, `_top`, `_village`, `_detail`, `_falls`, `CoralReef.png`.
- `assets_contact_sheet.png` shows the shared asset set.

## Use it in Roblox Studio

### Option A: drop in the finished maps (easiest)
1. In Studio, right-click **Workspace** → **Insert from File…** and pick any of `roblox/VoxelIsland.rbxm`,
   `DesertCoast.rbxm`, `FrostCoast.rbxm`, `VolcanicIsland.rbxm`, `CoralReef.rbxm`. They sit side by side,
   so you can insert all of them.
2. Open **View → Command Bar**, paste in all of `roblox/LightingAndWater.lua` and press Enter.
   It fills real terrain water around every inserted island and moves the default **Baseplate** to
   ServerStorage (it sits at water level and flickers). It also sets the lighting: Future lighting,
   atmosphere, colour correction and bloom. **This makes a big difference.**
3. **Deformed mesh rocks (recommended).**
   - **File → Import 3D** → `exports/meshes/VoxelRockMeshes.fbx` (the rocks, crags, stacks and arches for every theme).
   - Paste all of `roblox/MeshSwap.lua` into the Command Bar and press Enter.
   - Every part rock on every map becomes its deformed mesh. The part terrain stays as it is, so the meshes
     sit in the slab cliffs like the reef. The part rocks are kept in `ServerStorage.VoxelPartRocks`.
   - **Placement details:**
     - Pieces are placed from their exact baked bounds, so the importer's scale and `.001` names don't matter.
     - Meshes the importer laid on their side are stood back up.
     - Running it again is safe. Set `UNDO = true` to go back to parts.
   - **Optional (not the default look):** set `TERRAIN_MESH = true` and import `exports/meshes/<Map>_Terrain.fbx`.
     This covers the whole island's cliffs with one deformed mesh, and the part ground becomes invisible collision.

**Updating from an older version?** First delete the old maps, the imported meshes and `ServerStorage.VoxelPartRocks`.
Then do the steps above again.

### Option B: builder scripts
`roblox/builders/<Map>Builder.server.lua` builds one map from code (assets and layout are inside it).
- **Set it up:** right-click **ServerScriptService** → **Insert from File…** → `roblox/builders/<Map>Builder.rbxmx`
  (or paste the `.lua` file into a Script).
- **Run it:** press **Play**. `CONFIG` at the top sets the origin, studs, water, lighting and so on.
- `roblox/AssetLibrary.lua` holds all 101 asset shapes for your own code:
  `Builder.spawnAsset("PalmTree", CFrame.new(x, y, z), scale, tint, parent)`.

## How it's made
- **`gen/`** (Python) is the single source of truth:
  - `assets.py` + `theme_assets.py`: asset shapes as box lists.
  - `themes.py`: colours, trees, clutter and rocks for each theme.
  - `island.py`: the layout engine. It builds the height field, mesas, spiral and bent paths, and slab cliffs
    whose layers line up around the island. It also places the mesh rocks tucked into cliff feet, the accents,
    falls, village and props.
  - `maps.py`: the reef.
- **`tools/blender_meshes.py`**: each rock's blocky shape goes through voxel remesh, noise **deformation** and
  decimation into facets. The up-facing faces become a separate top mesh, and everything gets a tiling stud
  texture with box-projected UVs.
- **`tools/terrainmesh.py`** (optional `TERRAIN_MESH` look): does the same for each whole island. It wobbles and bulges the cliffs while the
  tops snap back to their exact heights, colours each face (grass, sand band, rock, beach, lava, ice) and splits
  the result into 64-stud chunks.
- **`tools/blender_build.py`**: renders the previews and the per-asset tiles. `tools/compose_previews.py`
  builds the posters and sheets from them.
- **Checks:**
  - `tools/qa_island.py`: no prop floats (0 of ~3,600 across the four islands).
  - `tools/check_zfight.py`: no overlapping coplanar faces in any asset.
  - `tools/test_meshswap.luau`: runs MeshSwap offline on every map, in all four modes: normal, lying-on-side import, and each of those with `TERRAIN_MESH`.

Run `./build.sh` to regenerate everything. It needs `python3` + Pillow, `blender` 4.x and
[`lune`](https://github.com/lune-org/lune). Change a theme's `seed` in `gen/themes.py` to get a new layout.

Part counts are about 32–35k for each island (mostly clutter, all anchored and static) and 13k for the reef.
MeshSwap lowers them. For phones, turn on StreamingEnabled.
