## Budgets

* **Shack shell** (`Shack` folder: floor, walls, roof, sign, awning, trims): @@SHELL@@ parts (budget 900).
* **Whole map**: @@TOTAL@@ parts, Parts + MeshParts + markers (budget 7,000). The forest is
  @@TREEPARTS@@ of them (210 trees x 6); there is room for more trees if you want it denser.
* **Meshes**: 156 in the FBX; the largest station/prop mesh is 324 triangles (the sauce
  pot; budget 1,500); the heaviest hand-held item is 476 triangles in total (the BasilPot;
  budget 600). Every item's count is in the item table.

## Rebuilding from source

Everything is generated; nothing was placed by hand. The scripts run on Python 3.13 with
the `bpy` module (Blender 5.2 as a Python package) plus numpy, Pillow and, for the mock,
lupa; the Cycles render setup is shared with the Folk Valley weapons
(`folk-valley-weapons/blender/rbxscene.py`).

```
python blender/build_map.py out                 # scene -> checks -> out/map.json + out/ScaryPizzaShack_Batch1.fbx
python tools/gen_build.py out/map.json out/BuildPizzaShack.lua
python tools/mock_shack.py out/map.json out/BuildPizzaShack.lua   # dry run in the Studio stand-in
python blender/render_plan.py previews           # labelled plans
python blender/render_final.py previews          # interior / front at night / aerial / yard
python blender/render_sheets.py previews         # station and item sheets
python tools/make_readme.py
```

`blender/build_map.py` refuses to write anything if a check fails: parts off the brick
grid, z-fighting faces, budgets, mesh-name clashes, a missing station, marker or Stand,
or an item marker that is not exactly on its surface.

| module | what it builds |
|---|---|
| `blender/layout.py` | every shared coordinate (room, counters, openings, road, yard) |
| `blender/map_shell.py` | floor, walls, ceiling, attic, roof, PIZZA sign, awning, menu board, side window |
| `blender/map_stations.py` | the inside stations, their markers and moving pieces |
| `blender/map_outside.py` | ground, road, ditch, yard, fence, outside stations, billboard, forest, the Markers folder |
| `blender/map_items.py` | the 46 items (geometry, Handle, Rest, item markers) |
| `blender/spslib.py`, `spsgeo.py`, `spsblend.py` | the scene model and its checks, low-poly geometry, Blender preview + FBX export |

## Next

Batch 2 (customers, the Health Inspector, the inspection car, the delivery truck) can stand
on these markers as they are: `Queue1..3` / `Customer`, `Inspector_Rise`, `Car_Start /
Stop / End`, `Truck_Stop`, `Delivery_Drop`, `Inspection_Stand1..4`, `Watcher_Window` and the
spawns. Send your notes on this batch and I will fold them in before starting it.
