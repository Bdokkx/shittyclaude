# Scary Pizza Shack: the remade map (work in progress: passes 1-5)

This is a snapshot of the remade map. Passes 1 to 5 are done (plan, structure, stations,
dressing, the outside). Pass 6 (the fault-finding pass) and the before/after pairs are
still to come.

## Files

| file | what |
|---|---|
| `ScaryPizzaShack_Remake.fbx` | every mesh, one white mesh per `Model__Part`, plus the four `FV_Axis` cubes |
| `BuildPizzaShack.lua` | the unattended build script (safe to run again) |
| `map.json` / `stats.json` | the source data the script was generated from, and part and mesh counts |
| `ScaryPizzaShack_Remake_src.zip` | the generator source (Python + Blender), see "Rebuilding" |

## Running it

1. Upload `ScaryPizzaShack_Remake.fbx` with Open Cloud (asset type Model), load it with
   `InsertService:LoadAsset(id)` and parent the result anywhere under Workspace.
2. Run `BuildPizzaShack.lua` with `loadstring` from the command-bar context. It prints
   `PizzaShack: built Workspace.PizzaShack: 6151 parts, 2715 mesh parts, 147 markers, ...`.

It works the same way as the batch-1 script: it finds the meshes by name, undoes any import
scale or turn using the `FV_Axis` cubes, and caches the meshes in
`ServerStorage.PizzaShackMeshes`. It then replaces `Workspace.PizzaShack` completely. It
passed the strict Studio stand-in (`tools/mock_shack.py`) for these cases: a plain import, an
import scaled by 0.01, a turned import, a second run without an import, and a third run with
a new turned import. That run found 0 problems.

## What changed for your code

* **The room is 4 studs wider to the west** (the drinks cooler's side). Inside it is now
  X -21..17, Z -10..10 (38 x 20); outside it is X -22..18. Everything on the west wall moved
  out with it: the lockers, DrinksCooler, StorageShelf, FuseBox and side window. Their
  markers moved with them.
* **The back door moved 2 west, to X -19..-15.** There is now wall on both sides of it.
  Nothing stands in front of it on either side, and it still swings out into the yard
  (`BackDoor.Door`, pivot on its west edge).
* **Markers that moved:**
  * `Watcher_Window` moved 4 west, to stay outside the side window.
  * `Queue3` is at (0, 0.36, 21.5), on the road's gravel shoulder.
  * Every ground marker from batch 1 now sits on the new ground: `Truck_Stop`,
    `TreeLine1..6`, `Spawn_Forest*` and `Delivery_Drop`.
  * The road ends are now `Spawn_RoadWest` and `Spawn_RoadEast`.
  * The road bends, so the cars follow `Car_Path1..N`, with `Car_Start`, `Car_Stop` and
    `Car_End` among them.
* **Camera markers:** each `Cam_` marker now sits just in front of its camera's lens and looks
  where the camera body is aimed. The four cameras are:
  * `Cam_Front`: on the shutter box, looking at the queue.
  * `Cam_Back`: on the street lamp, looking at the front of the shack.
  * `Cam_Yard`: on the back wall, looking at the yard.
  * `Cam_Road`: on the end of the road sign, looking at oncoming cars.
* Station names, item markers, Stands, Rest attachments and moving parts are otherwise as
  in batch 1. The checks compare them against batch 1 and find nothing missing or changed.

## Conventions

* **Text:** every piece of text is a flat part named `Board`, with its words in the
  attributes `BoardText`, `BoardTextColor` and `BoardFont`. The text goes on the Front face
  (-Z), and `\n` marks a line break.
* **Lamps:** a lamp is a Model with a part named `Bulb` carrying `LampGroup`, `LampKind`,
  `LampRange`, `LampBrightness`, `LampColor`, `LampAngle` and `LampShadows`, plus
  `LampFlicker` when it flickers. A Spot shines from the Bulb's `LampFace` (Bottom = its -Y).
  There are no Light objects.
* **Life:**
  * `Spin` (degrees per second about the part's own Y) is on the ceiling fan hub, the
    air-conditioner fans and the clock's second hand.
  * `Flicker` is on Neon parts.
  * `Chase` (the order number) is on the sign bulbs. These are parts named `Bulb` with no
    Lamp attributes.
  * The Fx attachments are `Fx_Steam`, `Fx_Smoke`, `Fx_Drip`, `Fx_Flies` and `Fx_Moths`.
* Decoration has CanCollide, CanTouch and CanQuery off. A few invisible blockers handle
  collision instead.

## Checks on this build

* The parts are on the brick grid.
* No part floats, no part passes through another, and there is no z-fighting.
* The 3 x 3 box in front of every marker is clear.
* The ceiling is closed and the PlayerBlock is in place.
* Every item marker sits on its surface.
* Part budget: 1,232 parts inside (limit 6,000) and 7,492 outside (limit 12,000).
* Prop models: 84 inside and 87 outside.
* Two kinds of large flat area are still left for pass 6: the attic lining, and a few
  outdoor ground plates just over 12 x 12.

## Rebuilding

Run these from the repo root, using Python 3.13 with `bpy` (Blender as a module), numpy and
Pillow:

```
python blender/build_remake.py out/remake          # scene -> checks -> map.json + FBX
python tools/gen_build.py out/remake/map.json out/remake/BuildPizzaShack.lua remake
python tools/mock_shack.py out/remake/map.json out/remake/BuildPizzaShack.lua remake
python -m shack2.checks                            # (from blender/) the full check report
python blender/render_views.py <dir> map=new light=neutral,night sheet=1   # V1..V16
```

The map is built by `blender/shack2/`:

| module | what it builds |
|---|---|
| `build.py` | the build order and the moved markers |
| `layout.py` and `interior.py` | the shared numbers |
| `shell.py` | the shell |
| `st_*.py` | the stations |
| `dressing.py` | the story props and the wall dressing |
| `props_in.py` and `props_out.py` | the prop models |
| `ext_shack.py` | the shack's outside |
| `site.py` | the forecourt, lot and yard |
| `road_dress.py` | the road dressing |
| `terrain.py` and `forest.py` | the ground and the trees |
| `checks.py` | every check above |
