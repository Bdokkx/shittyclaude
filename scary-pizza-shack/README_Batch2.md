# Scary Pizza Shack - batch 2: characters, vehicles, plushies, uniforms

Everything that goes on the R6 bodies, the three things that are not ordinary people, the
three vehicles, the seven plushies and the player uniforms. Same look and the same rules as
batch 1: real Parts where a box will do, chunky low-poly white meshes where it will not,
one unattended build script, Roblox axes, 1 unit = 1 stud.

| file | what |
|---|---|
| `out/ScaryPizzaShack_Batch2.fbx` | 210 low-poly meshes, one per colour part, white material, named `Model__Part`, plus the four `PSA_Axis` marker cubes |
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
   `PizzaShackAssets: built Workspace.PizzaShackAssets: 182 parts, 233 mesh parts, removed 1 import container(s)`.

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

| joint (in Part0) | standard R6 C0 / C1 position | Watcher C0 / C1 position | Inspector C0 / C1 position |
|---|---|---|---|
| HumanoidRootPart.RootJoint -> Torso | (0, 0, 0) / (0, 0, 0) | (0, 0, 0) / (0, 0, 0) | (0, 0, 0) / (0, 0, 0) |
| Torso.Neck -> Head | (0, 1, 0) / (0, -0.5, 0) | (0, 1.18, 0) / (0, -0.59, 0) | (0, 1.7, 0) / (0, -0.7, 0) |
| Torso.Right Shoulder -> Right Arm | (1, 0.5, 0) / (-0.5, 0.5, 0) | (1.18, 0.59, 0) / (-0.59, 0.94, 0) | (1.2, 0.85, 0) / (-0.43, 1.27, 0) |
| Torso.Left Shoulder -> Left Arm | (-1, 0.5, 0) / (0.5, 0.5, 0) | (-1.18, 0.59, 0) / (0.59, 0.94, 0) | (-1.2, 0.85, 0) / (0.43, 1.27, 0) |
| Torso.Right Hip -> Right Leg | (1, -1, 0) / (0.5, 1, 0) | (1.18, -1.18, 0) / (0.59, 1.18, 0) | (1.2, -1.7, 0) / (0.6, 1.7, 0) |
| Torso.Left Hip -> Left Leg | (-1, -1, 0) / (-0.5, 1, 0) | (-1.18, -1.18, 0) / (-0.59, 1.18, 0) | (-1.2, -1.7, 0) / (-0.6, 1.7, 0) |

Rotations are the standard R6 ones (RootJoint and Neck `CFrame.Angles(-90, 0, 180)` in degrees, the right side `0,0,1 / 0,1,0 / -1,0,0`, the left side mirrored).

| part | standard R6 | Watcher | Inspector |
|---|---|---|---|
| Torso | 2 x 2 x 1 | 2.36 x 2.36 x 1.18 | 2.4 x 3.4 x 1.2 |
| Head | 2 x 1 x 1 | 2.36 x 1.18 x 1.18 | 2.8 x 1.4 x 1.4 |
| Right Arm | 1 x 2 x 1 | 1.18 x 3.07 x 1.18 | 0.85 x 4.25 x 1 |
| Right Leg | 1 x 2 x 1 | 1.18 x 2.36 x 1.18 | 1.2 x 3.4 x 1.2 |

The Head is the classic head: a `Head` Part with a `SpecialMesh` (MeshType Head, Scale 1.25),
no face. Every R6 attachment a normal body has is there too (`HatAttachment`,
`HairAttachment`, `FaceFrontAttachment`, `NeckAttachment`, `BodyFrontAttachment`,
`BodyBackAttachment`, the collar, waist, shoulder, grip and foot attachments,
`RootAttachment`), scaled with the parts, so `Humanoid:AddAccessory` works on them.

## The models

### A. CustomerKit (Model, 33 pieces)

Every piece: a Model, PrimaryPart `Handle` (invisible 0.4 cube, anchored in the template) at the centre of the R6 part named in *sits on*; its parts are welded to the Handle. Attributes: `Category`, `BodyPart`, and `HidesHair` on the Hood.

| Piece | category | sits on | size (X x Y x Z) | tris | parts (mesh names) | notes |
|---|---|---|---|---|---|---|
| Short | Hair | Head | 1.38 x 0.91 x 1.43 | 80 | Hair (`KitShort__Hair`) | short crop |
| Side | Hair | Head | 1.43 x 1.09 x 1.56 | 80 | Hair (`KitSide__Hair`) | side parting, the fringe swept over one brow |
| Bowl | Hair | Head | 1.65 x 0.73 x 1.65 | 96 | Hair (`KitBowl__Hair`) | bowl cut, straight fringe all round |
| Long | Hair | Head | 1.6 x 2.16 x 1.59 | 120 | Hair (`KitLong__Hair`) | long, down the back to the shoulder blades |
| Bun | Hair | Head | 1.45 x 0.95 x 1.6 | 114 | Hair (`KitBun__Hair`) | pulled back into a bun |
| Ponytail | Hair | Head | 1.49 x 1.39 x 1.72 | 112 | Hair (`KitPonytail__Hair`), Band (`KitPonytail__Band`) | ponytail with a band |
| Curly | Hair | Head | 1.6 x 1.15 x 1.57 | 72 | Hair (`KitCurly__Hair`) | chunky curls |
| Mohawk | Hair | Head | 0.26 x 0.85 x 2.16 | 52 | Hair (`KitMohawk__Hair`) | a spiked crest front to back |
| BaldRing | Hair | Head | 1.43 x 0.52 x 0.96 | 84 | Hair (`KitBaldRing__Hair`) | bald on top, a ring of hair round the back and sides |
| Afro | Hair | Head | 1.82 x 1.52 x 1.98 | 96 | Hair (`KitAfro__Hair`) | big round afro |
| Cap | Hat | Head | 1.44 x 0.78 x 1.93 | 184 | Crown (`KitCap__Crown`), Peak (`KitCap__Peak`) | baseball cap |
| Beanie | Hat | Head | 1.55 x 1.03 x 1.55 | 192 | Knit (`KitBeanie__Knit`), Cuff (`KitBeanie__Cuff`) | knitted beanie with a turned-up cuff |
| Hood | Hat | Head | 1.61 x 1.84 x 1.67 | 512 | Hood (`KitHood__Hood`), Lining (`KitHood__Lining`) | hood up (hides the hair: attribute HidesHair) |
| TruckerCap | Hat | Head | 1.44 x 0.85 x 1.94 | 252 | Front (`KitTruckerCap__Front`), Mesh (`KitTruckerCap__Mesh`), Peak (`KitTruckerCap__Peak`) | trucker cap: foam front, mesh back |
| BucketHat | Hat | Head | 2.07 x 0.92 x 2.12 | 184 | Crown (`KitBucketHat__Crown`), Brim (`KitBucketHat__Brim`) | bucket hat |
| WoolHat | Hat | Head | 1.53 x 1.45 x 1.53 | 234 | Knit (`KitWoolHat__Knit`), Cuff (`KitWoolHat__Cuff`), Bobble (`KitWoolHat__Bobble`) | tall wool hat with a bobble |
| Headphones | Hat | Head | 1.72 x 1.08 x 0.52 | 196 | Band (`KitHeadphones__Band`), Cups (`KitHeadphones__Cups`) | over-ear headphones |
| Glasses | Face | Head | 1.37 x 0.26 x 0.8 | 236 | Frame (`KitGlasses__Frame`), Lenses (`KitGlasses__Lenses`) | glasses (clear lenses, Transparency 0.5) |
| Sunglasses | Face | Head | 1.37 x 0.28 x 0.8 | 236 | Frame (`KitSunglasses__Frame`), Lenses (`KitSunglasses__Lenses`) | dark sunglasses |
| Moustache | Face | Head | 0.72 x 0.31 x 0.25 | 60 | Moustache (`KitMoustache__Moustache`) | moustache |
| Beard | Face | Head | 1.38 x 1.05 x 1.02 | 100 | Beard (`KitBeard__Beard`) | full beard round the jaw |
| Scarf | Face | Torso | 1.6 x 1.32 x 1.36 | 144 | Scarf (`KitScarf__Scarf`), Stripes (`KitScarf__Stripes`) | scarf round the neck (sits on the Torso) |
| Backpack | Torso | Torso | 1.6 x 1.8 x 1.97 | 176 | Bag (`KitBackpack__Bag`), Pocket (`KitBackpack__Pocket`), Straps (`KitBackpack__Straps`) | backpack with shoulder straps |
| Satchel | Torso | Torso | 1.86 x 2.27 x 1.62 | 124 | Bag (`KitSatchel__Bag`), Flap (`KitSatchel__Flap`), Strap (`KitSatchel__Strap`) | satchel on a strap across the chest |
| Hoodie | Torso | Torso | 1.37 x 2.15 x 1.51 | 220 | Hood (`KitHoodie__Hood`), Pocket (`KitHoodie__Pocket`), Strings (`KitHoodie__Strings`) | hoodie: kangaroo pocket, drawstrings, hood down on the back |
| Tie | Torso | Torso | 0.8 x 1.48 x 0.08 | 44 | Tie (`KitTie__Tie`), Collar (`KitTie__Collar`) | shirt collar and tie |
| HiVisVest | Torso | Torso | 2.12 x 1.9 x 1.18 | 184 | Vest (`KitHiVisVest__Vest`), Stripes (`KitHiVisVest__Stripes`) | hi-vis vest with reflective stripes |
| RaincoatCollar | Torso | Torso | 1.62 x 1.94 x 1.37 | 148 | Collar (`KitRaincoatCollar__Collar`), Buttons (`KitRaincoatCollar__Buttons`) | turned-up raincoat collar with toggles |
| Umbrella | Hand | Right Arm | 0.55 x 1.77 x 3.33 | 216 | Canopy (`KitUmbrella__Canopy`), Crook (`KitUmbrella__Crook`), Tip (`KitUmbrella__Tip`) | closed umbrella carried like a walking stick: crook behind the fist, tip forward and 30 degrees down |
| Phone | Hand | Right Arm | 0.42 x 0.1 x 0.8 | 40 | Body (`KitPhone__Body`), Screen (`KitPhone__Screen`) | phone lying in the fist, pointing forward, screen up |
| CarKeys | Hand | Right Arm | 0.12 x 0.96 x 0.78 | 204 | Keys (`KitCarKeys__Keys`), Fob (`KitCarKeys__Fob`) | key fob in the fist with the key pointing forward, a second key hanging from the ring |
| DogLead | Hand | Right Arm | 1.14 x 0.97 x 2.09 | 124 | Lead (`KitDogLead__Lead`), Ring (`KitDogLead__Ring`) | dog lead: the hand loop round the fist and the first bit of lead, forward and down (Attachment LeadEnd on the Handle for a Beam/Rope to the dog) |
| Newspaper | Hand | Right Arm | 0.33 x 0.33 x 1.9 | 112 | Paper (`KitNewspaper__Paper`), Print (`KitNewspaper__Print`) | rolled-up newspaper gripped in the middle, pointing forward |

### B. Passenger, Watcher, Inspector, InspectorHole

| Model | PrimaryPart | size (X x Y x Z) | tris | parts | moving parts |
|---|---|---|---|---|---|
| Passenger | Handle | 2.24 x 2.25 x 1.84 | 438 | Handle, Body, Arms, Neck, Head, Eye | **Head**: on the Motor6D Neck (in the Handle; Part1 = Head): turn it with Neck.Transform, e.g. CFrame.Angles(0, math.rad(-40), 0) to look round at the camera. The Eyes are welded to it |
| Watcher | HumanoidRootPart | 4.72 x 5.9 x 1.38 | 0 | HumanoidRootPart, Torso, Head, Left Arm, Right Arm, Left Leg, Right Leg, Eye | R6 joints (RootJoint, Neck, Left/Right Shoulder, Left/Right Hip) |
| Inspector | HumanoidRootPart | 4.44 x 9.81 x 4.05 | 978 | HumanoidRootPart, Torso, Head, Left Arm, Right Arm, Left Leg, Right Leg, Shirt, Tie, Lapels, Buttons, PocketSquare, LeftCuff, LeftHand, RightCuff, RightHand, LeftShoe, RightShoe, HatBrim, HatCrown, HatBand, Clipboard, Clip, Paper, Pen | R6 joints (RootJoint, Neck, Left/Right Shoulder, Left/Right Hip) |
| InspectorHole | Dark | 8.37 x 1.66 x 8.37 | 488 | Dark, TilesLight, TilesDark, Shard1, Shard2, Shard3, Shard4, Shard5, Shard6, Shard7, Shard8 | the whole Model scales (Model:ScaleTo(width / 8)); Shard1..8 are loose pieces to throw about |

### C. Vehicles

Sizes are X (width) x Y (height) x Z (length). *body* leaves out the mirrors and the Van's ramp; *overall* is everything.

| Model | body | overall | parts | lights | moving parts |
|---|---|---|---|---|---|
| InspectorCar | 8.16 x 6.5 x 19 | 8.16 x 6.5 x 19 | Base, Body, Sill, Corner, Fin, Deck, Cabin, Windscreen, RearWindow, Roof, Bumper, Pillars, Trim, Grille, DoorLines, Headlight, TailLight, Beacon, BeaconBase, Wheel, Hub, Whitewall | Beacon, Headlight, TailLight | **Wheel x4**: cylinders on their axles: spin each about its own X axis (wheel.CFrame = wheel.CFrame * CFrame.Angles(a, 0, 0)); Hub and Whitewall are welded on |
| DeliveryTruck | 9.4 x 11.6 x 24.2 | 10.68 x 11.6 x 24.2 | Base, Bumper, Nose, NoseSide, Fender, Step, Hood, Windscreen, Cab, CabFloor, CabRoof, Chassis, BoxFloor, BoxFront, BoxSide, BoxRoof, Header, RearBumper, RearDoor, Stripe, SideL, SideR, Windows, Grille, Mirrors, Headlight, TailLight, Wheel, Hub | Headlight, TailLight | **RearDoor**: roll-up door, pivot on its top edge. It slides up 7.0 to open, but straight up it would come out through the roof, so roll it: tween Size.Y from 7.0 down to 0.6 and keep the top edge (the pivot) where it is; it is one ribbed mesh, so the ribs squash like a door rolling up; **Wheel x6**: cylinders on their axles (twin wheels at the back): spin about their own X axis |
| Van | 8.8 x 10.6 x 20.2 | 9.46 x 10.6 x 24 | Base, Floor, Wall, WheelHousing, Bulkhead, Roof, Header, DoorL, DoorHandle, Stripe, DoorR, Seam, Gate, Zone, Sign, Ramp, TailLight, Bumper, Nose, NoseSide, Fender, Sill, CabDoor, RoofRail, CabWindows, CabFloor, Windscreen, CabRoof, SeatL, SeatR, Dashboard, SteeringWheel, SideL, SideR, Grille, Mirrors, Headlight, Housing, Bulb, Crate, CrateSlats, PizzaBox, Wheel, Hub | Bulb, Headlight, TailLight | **DoorL**: back door, modelled shut, pivot on its outer hinge (x -4.2, back face); rotate the pivot -135 deg about +Y (attribute OpenAngle) to swing it open round the side; handle and stripe are welded to it; **DoorR**: back door, modelled shut, pivot on its outer hinge (x +4.2, back face); rotate the pivot +135 deg about +Y (attribute OpenAngle) to swing it open round the side; handle and stripe are welded to it; **Wheel x4**: cylinders on their axles: spin about their own X axis |

### D. Plushies (Model holding seven Models)

| Plush | size (X x Y x Z) | tris | parts (mesh names) | moving parts |
|---|---|---|---|---|
| Watchdog | 0.94 x 1.32 x 1.2 | 714 | Body (`Watchdog__Body`), Belly (`Watchdog__Belly`), Tail (`Watchdog__Tail`), Collar (`Watchdog__Collar`), Tag (`Watchdog__Tag`), Head (`Watchdog__Head`), Muzzle (`Watchdog__Muzzle`), Nose (`Watchdog__Nose`), Eyes (`Watchdog__Eyes`), Ears (`Watchdog__Ears`), Stitches (`Watchdog__Stitches`) | **Head**: on the Motor6D Neck (in the Body): shake it with Neck.Transform, e.g. CFrame.Angles(0, 0, math.rad(15)) back and forth; ears, eyes, muzzle and nose are welded to the Head |
| LuckyCat | 0.95 x 1.47 x 0.82 | 616 | Body (`LuckyCat__Body`), Collar (`LuckyCat__Collar`), Bell (`LuckyCat__Bell`), EarsInner (`LuckyCat__EarsInner`), Eyes (`LuckyCat__Eyes`), Nose (`LuckyCat__Nose`), Whiskers (`LuckyCat__Whiskers`), Stitches (`LuckyCat__Stitches`) | - |
| LittleInspector | 1.03 x 1.45 x 0.96 | 624 | Body (`LittleInspector__Body`), Head (`LittleInspector__Head`), Hands (`LittleInspector__Hands`), Shoes (`LittleInspector__Shoes`), Shirt (`LittleInspector__Shirt`), Tie (`LittleInspector__Tie`), Hat (`LittleInspector__Hat`), HatBand (`LittleInspector__HatBand`), Stitches (`LittleInspector__Stitches`) | - |
| NightOwl | 0.96 x 1.4 x 0.72 | 596 | Body (`NightOwl__Body`), Belly (`NightOwl__Belly`), Wings (`NightOwl__Wings`), Feet (`NightOwl__Feet`), Head (`NightOwl__Head`), EyeDiscs (`NightOwl__EyeDiscs`), Eyes (`NightOwl__Eyes`), Beak (`NightOwl__Beak`), Stitches (`NightOwl__Stitches`) | **Head**: on the Motor6D Neck (in the Body): turn it about Y with Neck.Transform (an owl can go well past 90 deg); eyes, beak and tufts turn with it |
| MedicBear | 1.11 x 1.4 x 0.87 | 764 | Body (`MedicBear__Body`), Muzzle (`MedicBear__Muzzle`), Nose (`MedicBear__Nose`), Eyes (`MedicBear__Eyes`), EarsInner (`MedicBear__EarsInner`), Cross (`MedicBear__Cross`), Stitches (`MedicBear__Stitches`) | - |
| SleepySloth | 0.88 x 1.17 x 0.85 | 524 | Body (`SleepySloth__Body`), Face (`SleepySloth__Face`), EyeStripes (`SleepySloth__EyeStripes`), Eyes (`SleepySloth__Eyes`), Nose (`SleepySloth__Nose`), Claws (`SleepySloth__Claws`), Stitches (`SleepySloth__Stitches`) | - |
| PiggyBank | 0.86 x 1.29 x 1.26 | 476 | Body (`PiggyBank__Body`), Snout (`PiggyBank__Snout`), Nostrils (`PiggyBank__Nostrils`), Eyes (`PiggyBank__Eyes`), Slot (`PiggyBank__Slot`), Tail (`PiggyBank__Tail`), Stitches (`PiggyBank__Stitches`) | - |

### E. Uniforms (Model of Accessories)

| Accessory | attachment (in Handle) | worn on | size (X x Y x Z) | tris | parts (mesh names) | notes |
|---|---|---|---|---|---|---|
| PizzaCap | `HatAttachment` | Head | 1.44 x 0.79 x 1.93 | 264 | Crown (`UniPizzaCap__Crown`), Peak (`UniPizzaCap__Peak`), Slice (`UniPizzaCap__Slice`), Crust (`UniPizzaCap__Crust`), Pepperoni (`UniPizzaCap__Pepperoni`) | peaked cap with a pizza slice on the front |
| ChefHat | `HatAttachment` | Head | 1.76 x 1.62 x 1.72 | 252 | Band (`UniChefHat__Band`), Puff (`UniChefHat__Puff`) | tall white chef's hat |
| PaperHat | `HatAttachment` | Head | 1.2 x 0.56 x 1.52 | 76 | Hat (`UniPaperHat__Hat`), Stripe (`UniPaperHat__Stripe`) | folded paper diner hat, worn front to back like a garrison cap |
| Visor | `HatAttachment` | Head | 1.43 x 0.27 x 1.95 | 180 | Band (`UniVisor__Band`), Peak (`UniVisor__Peak`) | sun visor (band and peak, open top) |
| Bandana | `HatAttachment` | Head | 1.44 x 1.23 x 1.6 | 412 | Cloth (`UniBandana__Cloth`), Knot (`UniBandana__Knot`), Dots (`UniBandana__Dots`) | bandana tied on the head, knot at the back |
| DeliveryHelmet | `HatAttachment` | Head | 1.63 x 1.65 x 1.76 | 320 | Shell (`UniDeliveryHelmet__Shell`), Stripe (`UniDeliveryHelmet__Stripe`), Visor (`UniDeliveryHelmet__Visor`), Strap (`UniDeliveryHelmet__Strap`) | open-face scooter helmet with a centre stripe |
| Apron | `BodyFrontAttachment` | Torso | 2.16 x 3.35 x 1.29 | 164 | Apron (`UniApron__Apron`), Pocket (`UniApron__Pocket`), Straps (`UniApron__Straps`) | plain bib apron with a front pocket |
| ApronStriped | `BodyFrontAttachment` | Torso | 2.16 x 3.35 x 1.3 | 272 | Apron (`UniApronStriped__Apron`), Stripes (`UniApronStriped__Stripes`), Straps (`UniApronStriped__Straps`) | striped bib apron |
| ApronStained | `BodyFrontAttachment` | Torso | 2.16 x 3.35 x 1.29 | 368 | Apron (`UniApronStained__Apron`), Flour (`UniApronStained__Flour`), Sauce (`UniApronStained__Sauce`), Straps (`UniApronStained__Straps`) | bib apron with flour and sauce marks |
| HiVisVest | `BodyFrontAttachment` | Torso | 2.12 x 1.9 x 1.18 | 184 | Vest (`KitHiVisVest__Vest`), Stripes (`KitHiVisVest__Stripes`) | hi-vis vest (same shape as the customer one) |
| NameTag | `BodyFrontAttachment` | Torso | 0.68 x 0.37 x 0.05 | 36 | Tag (`UniNameTag__Tag`), Border (`UniNameTag__Border`) | name tag on the chest; Tag's Front face is flat for a SurfaceGui |
| OvenMitts.OvenMittL | `LeftGripAttachment` | Left Arm | 1.26 x 1.15 x 1.56 | 160 | Mitt (`UniOvenMitt__Mitt`), Cuff (`UniOvenMitt__Cuff`) | left oven mitt (the pair lives in the Model OvenMitts) |
| OvenMitts.OvenMittR | `RightGripAttachment` | Right Arm | 1.26 x 1.15 x 1.56 | 160 | Mitt (`UniOvenMitt__Mitt`), Cuff (`UniOvenMitt__Cuff`) | right oven mitt |
| Headset | `HairAttachment` | Head | 1.59 x 1.16 x 0.98 | 212 | Band (`UniHeadset__Band`), Earpiece (`UniHeadset__Earpiece`), Mic (`UniHeadset__Mic`) | headset: band, one ear cup and a mic boom |

### Part counts

| Model | parts + mesh parts |
|---|---|
| CustomerKit | 94 |
| Passenger | 7 |
| Watcher | 9 |
| Inspector | 25 |
| InspectorHole | 11 |
| InspectorCar | 39 |
| DeliveryTruck | 45 |
| Van | 74 |
| Plushies | 58 |
| Uniforms | 53 |
| **total** | **415** |

## What I built differently from the order, and why

The names, the R6 parts and the six joint names are exactly as ordered. These are the places
where I chose something the order did not spell out, or did it another way:

1. **Inspector: 1.7 times as tall, but slim.** A uniform 1.7x R6 is a wide friendly block,
   so he is 1.7x in height only: Torso 2.4 x 3.4 x 1.2 (a plain 1.7x would be 3.4 x 3.4 x
   1.7), legs 1.2 x 3.4 x 1.2, arms 0.85 thick and 4.25 long (1.7 x 1.25 x 2, so his hands
   hang at his knees), long-fingered hands under white cuffs. The Head part is 1.4x (2.8 x
   1.4 x 1.4) so that the black hat with its wide brim (4.1 across) tops out at exactly 9.8;
   `HumanoidRootPart` is at 5.1, as ordered. The joints are the standard R6 ones moved to
   these part sizes (table above), so R6 animations play on him; the Watcher works the
   same way at 1.18x with 1.3x arms.
2. **Humanoid and Animator** inside the Watcher and the Inspector (RigType R6, name and
   health display off), so batch-3 animations load straight onto them. Delete the Humanoid
   if your code adds its own.
3. **Hand items** sit on a grip line through the fist (Right Arm, y = -0.82) and point
   forward out of the front of the fist, as ordered. The one exception is the Umbrella: it
   points forward and 30 degrees down, carried like a walking stick, so its tip stays off the
   ground instead of sticking out 2.7 studs at hip height.
4. **Attributes on the kit pieces:** `Category` (Hair, Hat, Face, Torso, Hand) and
   `BodyPart` (Head, Torso, Right Arm) on every piece, and `HidesHair = true` on the Hood, so
   your code can pick and fit pieces without a name list. The DogLead has an Attachment
   `LeadEnd` in its Handle at the end of the lead, for your Beam or RopeConstraint to the
   dog.
5. **DeliveryTruck `RearDoor`** is a roll-up door, but it cannot slide straight up: the box
   has no room above the opening, so a 7-stud slide would come out through the roof. It is
   one ribbed mesh with its pivot on its top edge and the attribute `OpenTravel = 7`. To
   open it, shrink it from the bottom and keep the top edge where it is (the ribs bunch up
   like a door rolling into the roof):

   ```lua
   local door = truck.RearDoor
   local full = door.Size.Y                                 -- read these while it is shut
   local top = door.CFrame * CFrame.new(0, full / 2, 0)     -- its top edge
   local function setOpen(t)                                -- 0 = shut, 1 = open
       local h = full - (full - 0.6) * t
       door.Size = Vector3.new(door.Size.X, h, door.Size.Z)
       door.CFrame = top * CFrame.new(0, -h / 2, 0)
   end
   ```
6. **Van:** the back opening is 7.6 wide and 6 tall (floor 1.6 to 7.6), not the full inside
   height: the `Sign` you asked for needs a header above the opening to hang on (the header
   runs from 7.6 to 10.6, and the Sign sits on it). Inside, the box is exactly 7.6 wide, 8.2
   tall and 11 long, which is what `Zone` fills. The rear wheels come up through the floor
   as two low boxed benches along the walls (`WheelHousing`), at the back half; the crates
   and pizza boxes stand against the front wall (`Bulkhead`), so the middle of the floor is
   clear for four R6. The `Ramp` is a WedgePart from the ground up to the floor lip, 6 wide
   and 4 long, behind the doors; the doors close above it. `DoorR` carries a thin seam
   strip (welded) that covers the gap between the shut doors. The shell is 8.4 wide and 19
   long as ordered, 10.2 to the roof; the header over the doors stands 0.4 higher (10.6:
   a whole-stud plate, for the brick grid). The side boards and wheel hubs stand 0.2 proud
   of the shell on each side, and the bumper, floor lip and tail lights add a little at the
   ends (the table gives both sizes).
7. **OvenMitts** are two Accessories, `OvenMittL` (LeftGripAttachment) and `OvenMittR`
   (RightGripAttachment), inside a Model `OvenMitts`: an Accessory has one Handle and one
   attachment, so one Accessory cannot follow both hands. Put the pair on with
   `for _, a in Uniforms.OvenMitts:GetChildren() do humanoid:AddAccessory(a:Clone()) end`.
8. **Uniform HiVisVest** uses the same meshes as the CustomerKit HiVisVest
   (`KitHiVisVest__*`), as an Accessory on BodyFrontAttachment. The **Headset** uses
   `HairAttachment` (on an R6 head that is the same point as HatAttachment), so it reads as
   something worn under a hat rather than a hat. The **NameTag**'s `Tag` part has a flat
   Front face for a SurfaceGui with the player's name.
9. **Vehicle `Base`** is an invisible 4 x 0.4 x 8 Part with no collisions, and the vehicle's
   pivot is on the ground under the middle, so
   `van:PivotTo(CFrame.new(x, groundY, z) * CFrame.Angles(0, yaw, 0))` stands the wheels on
   the ground. The lights are lit: each `Headlight` holds a SpotLight `Light` (shining
   forward, range 40), the `Beacon` a red PointLight, the Van's `Bulb` a warm PointLight;
   switch them with `Light.Enabled`.
10. **Flat parts for your text** (`SideL` / `SideR` on the truck and the van, the van's
    `Sign`) are 0.2 thick, have their Front face pointing outwards and their top edge up,
    so a SurfaceGui with Face = Front reads the right way round.
11. **The Passenger's Head** is a separate part on a Motor6D `Neck` (in its Handle), so it
    can turn its head towards the camera; the two `Eye` parts are welded to the Head. The
    Watchdog's and the NightOwl's heads are on a Motor6D `Neck` in the plush's `Body` in
    the same way, with the pivot at the neck as ordered.
12. **InspectorHole** scales with `Model:ScaleTo(width / 8)`, 3 to 8 studs. `Dark` is the
    PrimaryPart, a black Neon disc (Neon, so no light ever greys it), and the Model's pivot
    is at floor level in the middle, so `hole:PivotTo(CFrame.new(x, floorY, z))` sits it on
    the floor. The tiles are two meshes (`TilesLight`, `TilesDark`, one per checker colour)
    lifted at the inner edge as if pushed up from below.

## Budgets

* **Hair:** 30 to 120 triangles per piece, as ordered (checked by the build; the counts are
  in the kit table).
* **Meshes:** 210 in the FBX; the largest is 336 triangles (`MedicBear__Body`) (every mesh is checked to be
  under 1,500).
* **Parts:** 415 Parts and MeshParts across the ten Models (counts above). A worn
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
