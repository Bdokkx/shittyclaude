## Budgets

* **Hair:** 30 to 120 triangles per piece, as ordered (checked by the build; the counts are
  in the kit table).
* **Meshes:** @@NMESH@@ in the FBX; the largest is @@LARGEST@@ (every mesh is checked to be
  under 1,500).
* **Parts:** @@TOTAL@@ Parts and MeshParts across the ten Models (counts above). A worn
  kit piece adds 2 to 4 parts to a customer (its Handle and 1 to 3 meshes), a uniform
  piece 3 to 6.

## Rebuilding from source

Everything is generated; nothing was placed by hand. Same tools as batch 1 (Python 3.13
with the `bpy` module, numpy, Pillow and, for the mock, lupa).

```
python blender/build_assets.py out             # scene -> checks -> out/assets.json + out/ScaryPizzaShack_Batch2.fbx
python tools/gen_build.py out/assets.json out/BuildPizzaShackAssets.lua assets
python tools/mock_shack.py out/assets.json out/BuildPizzaShackAssets.lua assets   # dry run in the Studio stand-in
python tools/fbx_roundtrip.py out/ScaryPizzaShack_Batch2.fbx out/assets.json PSA_Axis   # read the FBX back
python blender/render_assets.py previews/batch2 # characters, kit, vehicles, plushies, uniforms (samples=N)
python tools/make_readme_b2.py
```

`blender/build_assets.py` refuses to write anything if a check fails: the ten Model names
and their order, the R6 parts and joints (each in its Part0, wired to the right parts),
anchoring, the Inspector's 5.1 and 9.8, wheels, lights and the other named vehicle parts,
the Van contract (OpenAngle and pivots, Zone at least 7.6 x 8.2 x 11 on a floor at 1.6,
VanLamp.Bulb), the plushie heights and Neck joints, every Accessory's attachment, exactly
one `Handle` per kit piece and accessory, hair triangle counts, parts off the brick grid,
z-fighting faces, mesh budgets and mesh-name clashes (with batch 1 too).

| module | what it builds |
|---|---|
| `blender/assets_r6.py` | the R6 body at any scale: part sizes, the six joints, the attachments, the classic head |
| `blender/assets_chars.py` | Inspector, Watcher, Passenger, InspectorHole |
| `blender/assets_kit.py` | the 33 CustomerKit pieces |
| `blender/assets_vehicles.py` | InspectorCar, DeliveryTruck, Van |
| `blender/assets_plush.py` | the seven plushies |
| `blender/assets_uniforms.py` | the uniform Accessories |
| `blender/assets_common.py` | palette, Handle and detail helpers, the moving-part notes used in the tables |
| `blender/build_assets.py` | lays out the ten Models, runs the checks, writes the JSON and the FBX |
| `blender/render_assets.py` | the preview renders |

## Next

Batch 3 is the animations for these models, made on exactly these rigs: the six R6 joints
(for players, customers, the Watcher and the Inspector), the Passenger's `Neck`, and the
Watchdog's and NightOwl's `Neck`. Send your notes on this batch and I will fold them in
before starting it.
