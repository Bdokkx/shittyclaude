# Scary Pizza Shack - batch 2: characters, vehicles, plushies, uniforms

Everything that goes on the R6 bodies, the three things that are not ordinary people, the
three vehicles, the seven plushies and the player uniforms. Same look and the same rules as
batch 1: real Parts where a box will do, chunky low-poly white meshes where it will not,
one unattended build script, Roblox axes, 1 unit = 1 stud.

| file | what |
|---|---|
| `out/ScaryPizzaShack_Batch2.fbx` | @@NMESH@@ low-poly meshes, one per colour part, white material, named `Model__Part`, plus the four `PSA_Axis` marker cubes |
| `out/BuildPizzaShackAssets.lua` | the self-contained build script (runs unattended, safe to run twice) |
| `previews/batch2/characters_front.jpg`, `characters_back.jpg` | the line-up: R6 dummy, a customer with the Passenger on its back, Watcher, Inspector, and the InspectorHole with an Inspector rising out of it |
| `previews/batch2/kit_sheet.jpg` | all 33 CustomerKit pieces, each on a plain R6 dummy |
| `previews/batch2/vehicles_front.jpg`, `vehicles_back.jpg`, `van_back.jpg` | the three vehicles with an R6 dummy, and the Van's back with the doors at their OpenAngle and four R6 inside |
| `previews/batch2/plushies.jpg` | the seven plushies |
| `previews/batch2/uniforms_front.jpg`, `uniforms_back.jpg` | every uniform piece worn by R6 dummies |

## Running it

1. Upload `ScaryPizzaShack_Batch2.fbx` with Open Cloud (asset type Model), load it with
   `InsertService:LoadAsset(id)` and parent the result anywhere under Workspace.
2. Run `BuildPizzaShackAssets.lua` with `loadstring` from the command-bar context. It prints
   `PizzaShackAssets: built Workspace.PizzaShackAssets: @@NPARTS@@ parts, @@NMESHPARTS@@ mesh parts, removed 1 import container(s)`.

It works exactly like the batch-1 script, with its own names so the two never touch each
other's things: it finds the imported MeshParts by name anywhere under Workspace (also
ServerStorage and ReplicatedStorage), measures the four `PSA_Axis` cubes to undo any scale or
turn the importer applied, keeps a clean copy of every mesh in
`ServerStorage.PizzaShackAssetMeshes` (so it can run again without an import), builds a new
`Workspace.PizzaShackAssets`, deletes the one an earlier run built, and deletes the import
container and the marker cubes. If any mesh is missing it warns and changes nothing. No
mesh name is shared with batch 1 (checked by the build), so both files can sit in Workspace
at the same time.

`Workspace.PizzaShackAssets` holds ten Models, in this order: `CustomerKit`, `Passenger`,
`Watcher`, `Inspector`, `InspectorHole`, `InspectorCar`, `DeliveryTruck`, `Van`, `Plushies`,
`Uniforms`. They stand in a row 120 studs below the map origin (Y -120), out of the way
until you move them to `ReplicatedStorage.Assets`.

The script has been run in the same strict Studio stand-in as batch 1
(`tools/mock_studio.lua`: unknown classes, properties or enum members are errors) for a plain
import, an import scaled by 0.01, an import turned on the CFrames, one turned inside the
meshes, and for each of those a second run with no import (from the cache) and a third with
a new turned import. Every instance was compared with the source data (class, name, size,
CFrame, colour, material, flags, surfaces, PivotOffset, welds, Motor6D C0 / C1 / Part0 /
Part1 / parent, attachments, Humanoid, Animator, SpecialMesh, Accessory, lights,
attributes): 0 problems. The FBX was also read back and every mesh compared with the
source, vertex for vertex: 0 differences.

## Conventions (what your code can rely on)

* **Axes.** Roblox axes, 1 stud. Everything faces **-Z**: characters, plushies, the front of
  every vehicle. +X is the character's right.
* **Things that get worn or animated have one anchored part, their PrimaryPart**:
  `HumanoidRootPart` (Watcher, Inspector), `Handle` (every CustomerKit piece, the
  Passenger, every uniform), `Body` (plushies). Everything else in them is unanchored and
  held by a `WeldConstraint` (named `Weld`, inside the part it holds) or by a `Motor6D`
  where it moves. When you weld a clone onto a character, set its `Handle.Anchored = false`
  first.
* **Vehicles and the InspectorHole are scenery and anchored throughout.** Move a vehicle
  with `Model:PivotTo` (its pivot is the `Base`, on the ground under the middle). Its moving
  parts (`Wheel`, `DoorL` / `DoorR`, `RearDoor`) are anchored on their own, so setting their
  CFrame turns just that part, and the few bits welded to them (hubs, door handles, the
  door stripes) go with them. Unanchor the hole's `Shard`s when you throw them.
* **Collisions.** Details have `CanCollide`, `CanTouch` and `CanQuery` off, and on the kit
  and the uniforms `Massless` on, so they never push a character about. On the Watcher and
  the Inspector only `Torso` and `Head` collide, as on a normal R6. Vehicle bodies, wheels,
  doors and the Van's ramp collide; lights, the Van's `Zone` and `Gate` do not (`Zone` has
  `CanTouch` on for your crew check).
* **Colours.** Every mesh is white in the FBX and gets its colour from the part's `Color`,
  set by the script. Part names say what they are (`Crown`, `Peak`, `Band`, `Lens` ...), so
  recolouring is `for each part named X: part.Color = ...`.
* **Moving parts** are listed in the tables below with how to move them. Hinged or sliding
  parts carry a `PivotOffset` on their hinge; Motor6D-driven parts are moved with
  `Motor6D.Transform`.

## The R6 rig (Watcher and Inspector)

Both are the classic R6 body: `HumanoidRootPart` (invisible, anchored, PrimaryPart),
`Torso`, `Head`, `Left Arm`, `Right Arm`, `Left Leg`, `Right Leg`, with the six Motor6Ds in
the standard places (`HumanoidRootPart.RootJoint`, `Torso.Neck`, `Torso["Right Shoulder"]`,
`Torso["Left Shoulder"]`, `Torso["Right Hip"]`, `Torso["Left Hip"]`), the standard R6 joint
rotations and a `Humanoid` (RigType R6, no name or health bar) with an `Animator`, so the
same R6 animations play on them as on players and customers. Their C0 / C1 are the standard
ones moved to the bigger part sizes:

@@JOINTS@@
The Head is the classic head: a `Head` Part with a `SpecialMesh` (MeshType Head, Scale 1.25),
no face. Every R6 attachment a normal body has is there too (`HatAttachment`,
`HairAttachment`, `FaceFrontAttachment`, `NeckAttachment`, `BodyFrontAttachment`,
`BodyBackAttachment`, the collar, waist, shoulder, grip and foot attachments,
`RootAttachment`), scaled with the parts, so `Humanoid:AddAccessory` works on them.
