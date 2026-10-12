# Scary Pizza Shack - batch 1: the shack map, its stations and the hand-held items

A lonely roadside pizza shack at night, built brick by brick in the classic Roblox stud
style. This batch is the map, every station inside and outside, all the markers your
code reads, and the 46 hand-held items.

| file | what |
|---|---|
| `out/ScaryPizzaShack_Batch1.fbx` | 156 low-poly meshes, one per colour part, white material, named `Model__Part`, plus the four `FV_Axis` marker cubes |
| `out/BuildPizzaShack.lua` | the self-contained build script (runs unattended, safe to run twice) |
| `previews/plan_inside.jpg` | top-down plan of the inside with every station, Stand and item marker labelled |
| `previews/plan_site.jpg`, `previews/plan_world.jpg` | site plan (yard, front, road) and the whole map, with the Markers folder labelled |
| `previews/interior.jpg`, `previews/interior_2.jpg`, `previews/front_night.jpg`, `previews/yard_night.jpg`, `previews/aerial.jpg` | the look: the kitchen from both ends, the front and the yard at night, and a daytime aerial for reading the layout |
| `previews/stations_sheet.jpg`, `previews/items_sheet.jpg` | every station seen from its Stand, every item |

## Running it

1. Upload `ScaryPizzaShack_Batch1.fbx` with Open Cloud (asset type Model), load it with
   `InsertService:LoadAsset(id)` and parent the result anywhere under Workspace.
2. Run `BuildPizzaShack.lua` with `loadstring` from the command-bar context. It prints
   `PizzaShack: built Workspace.PizzaShack: @@NPARTS@@ parts, @@NMESH@@ mesh parts, @@NMARK@@ markers, removed 1 import container(s)`.

What it does, in order:

* finds the imported MeshParts **by name anywhere under Workspace** (also ServerStorage
  and ReplicatedStorage; exact name first, then case/punctuation-insensitive);
* measures the four `FV_Axis` cubes to undo any scale or turn the importer applied;
* keeps a clean copy of every mesh in `ServerStorage.PizzaShackMeshes` (so it can be run
  again later without importing; delete that folder whenever you like, a fresh import
  rebuilds it);
* builds a new `Workspace.PizzaShack` with the folders `Shack`, `Outside`, `Stations`,
  `Items`, `Markers`, then deletes the one an earlier run built;
* deletes the import container (the outermost ancestor that holds nothing but imported
  meshes) and the marker cubes.

If any mesh is missing it warns and changes nothing. No Selection, no paste steps, no
plugins. Because a re-run replaces `Workspace.PizzaShack` completely, keep anything you add
in Studio (scripts, prompts, sounds) outside that folder or add it from code at run time.

It has been run in a strict Studio stand-in (`tools/mock_studio.lua`, unknown
classes / properties / enum members are errors) for a plain import, an import scaled by
0.01, an import turned on the CFrames, one turned inside the meshes, a second run with no
import (uses the cache) and a third with a new turned import: every one of the 3,000-odd
instances was compared with the source data (class, name, size, CFrame, colour, material,
flags, surfaces, PivotOffset, welds, joints, attachments, lights, attributes): 0 problems.

## Conventions (what your code can rely on)

* **Units and axes.** 1 stud; Roblox axes everywhere: +X east, +Y up, +Z south (towards
  the road). Ground top is Y 0, the shack floor top is Y 0.4, the road surface Y -0.4.
* **Markers** are invisible anchored 1 x 1 x 1 Parts (Transparency 1, CanCollide /
  CanQuery / CanTouch / CastShadow false). Their **-Z is the facing direction** and their
  **Position lies exactly on the surface they mark** (floor, ground, counter top, board,
  shelf, tub floor, deck floor), so half the cube is sunk into it. Character markers:
  put the character's feet at the marker. Camera markers: the camera's position, -Z = the
  view direction.
* **Item markers** (`Work`, `WorkSauce`, `WorkCheese`, `Handover`, `Slot..`, `Tub..`,
  `Delivery_Drop`, and the items' own `Carry` / `Inside`) face the same way as the
  station's `Stand`, so an item set down keeps the orientation it had in the player's
  hand. All 47 station item markers are checked by the build to sit exactly on their
  surface.
* **Brick grid.** Every Block and Wedge Part has X and Z in whole studs and Y in multiples
  of 0.4 (checked: 0 exceptions). Blocks are Plastic with TopSurface Studs, BottomSurface
  Inlet and Smooth sides; wedges have an Inlet bottom and a smooth slope. Deliberate
  exceptions: markers, the items' invisible Handles (0.4 cubes), the two display faces
  (`RulesBoard.Face` 7 x 5 x 0.2 and the monitor `Screen`s 2.4 x 1.8 x 0.2, SmoothPlastic),
  glass panes and Neon light strips; cylinders and balls are sized by their diameter.
  Thin upright panels (fridge and cooler sides, oven doors, glass) are 0.4 plates turned
  on their side, with smooth faces. Parts may overlap where bricks meet (counters run
  0.6 into walls, walls sink 0.2 into the ground); nothing z-fights (checked).
* **Moving pieces** are one anchored Part or MeshPart each, with **PivotOffset on the
  hinge or slide axis** and a pivot frame that is aligned with the world axes when the
  piece is at rest. Small things that move with them (handles, slats, a window) are
  welded to them (WeldConstraint, unanchored, massless), so `piece:PivotTo(...)` or
  setting its CFrame carries everything along. Example for a hinge:
  `door:PivotTo(door:GetPivot() * CFrame.Angles(0, math.rad(90), 0))`. Every moving piece,
  its direction and its distance is in the station table below.
* **Lights.** The bulbs that should light something carry a light named `Light`
  (PointLight / SpotLight / SurfaceLight): the PIZZA sign (3 of its 28 Bulbs), the two
  ceiling lamps, both oven Glows, fridge and cooler strips, the back-door lamp, street
  lamp, yard lamp and bus-stop tube. Change, flicker or delete them freely; everything
  named `Bulb` is a separate Neon ball you can recolour or switch to SmoothPlastic.
* **Items** live in `Workspace.PizzaShack.Items` as templates, well under the map (Y -60).
  Each is a Model whose PrimaryPart is an invisible `Handle` at the item's grip; -Z points
  away from the body, +Y up. The Handle is anchored; every other part is welded to it
  (unanchored, massless, CanCollide false), so clone the Model, set `Handle.Anchored =
  false` and weld the Handle to the hand. Every Handle has an Attachment **`Rest`**: where
  (and which way up) the item touches a surface when it is set down, so
  `item:PivotTo(marker.CFrame * item.Handle.Rest.CFrame:Inverse())` puts any item on any
  item marker. The pizza layers share one origin (pizza centre, bottom): stack them by
  giving their Handles the same CFrame; toppings sit at Y +0.24 above it (on the melted
  cheese) with their own Handle at their bottom.

