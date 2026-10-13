# STEAL A POTATO: the map in bricks (4.6), `BuildPotatoMap.lua`

`BuildPotatoMap.lua` builds **`Workspace.PotatoMap`**, a Model with the attribute `Studs = true`. It contains:

- the walled farm yard (the safe zone) with its **twelve bare 60 × 60 pens**;
- the gate;
- the corridor of all **eighteen areas**: each has its hero, its own props, Folk Valley's props recoloured for it, fourteen Mounds, an AreaSign and a Zone.

The contract is part 1's: `Workspace.PotatoMap`, `Markers`, fourteen Mounds per area, the gate, the boards and the zones. Where the order changed it, the changes are marked **new** below.

**27,078 parts** in all. The 280 pieces that repeat (Mounds, props, heroes, signs, lamps) are each written once in the script and copied 1,124 times, so the script is only 831 KB.

## Put it in the game

Run `BuildPotatoMap.lua` unattended: `loadstring` it from the command-bar context, or paste it into the Command Bar.

- It builds the whole map in a loose Model, then swaps it in as `Workspace.PotatoMap`.
- It replaces `Workspace.PotatoMap` only if one of my build scripts made it: this one (attribute `Studs`) or the part 1 map (attribute `Batch`).
- If a `PotatoMap` made by anything else is there, it changes nothing and warns once. Rename that one and run it again.
- Nothing else in the place is touched. It is safe to run twice.
- It needs nothing else: no FBX and no kit. Every part is made from the script's own table.

I dry-ran it in the strict Studio mock four ways: into an empty place, again on top of itself, over the part 1 map with somebody else's things beside it, and over a `PotatoMap` made by something else (where it must refuse). **0 problems**: every part's class, name, size, CFrame, colour, material, surfaces, flags, pivot, attribute and PrimaryPart, and every attachment, matches the data.

## Rules the map keeps (checked on every build)

- **Parts only.**
  - Every part is a plain Part: Plastic with Inlet on all six faces.
  - Neon is used only for glow. SmoothPlastic is used only for boards and faces.
  - No meshes, unions, textures or decals.
- **Collisions.** These collide, with CanCollide and CanQuery on and CanTouch off:
  - the ground, the walls and the gate;
  - the stall counters and the sign and board posts;
  - the heroes' solid parts (bases, steps, platforms);
  - Lava Furrows' kerbs and Spud Olympus' columns;
  - the big parts (2 studs or more) of the solid props: rocks, mesas, logs, stumps, the barn and so on.

  Everything else is decoration, with all three off. No part under 2.5 studs casts a shadow.
- **Running lane.** Nothing that collides stands inside **X −22..22** anywhere in the fields. Mounds and small "Any" clutter (grass, flowers, bones, sweets) may lie in it, but none of it collides.
- **Avenue.** Nothing stands in **X −20..20** of the yard between the gate and the south pens. Only flat marks lie there: the spawn pad and the red line. The gate's timer boards hang overhead at Y 31.
- **Pens.** Every pen's 60 × 60 is bare ground.
- **Gate.** The opening is clear from the ground to **Y 30** across the full 120 width.
- **Mounds.** There are 14 per area. They are at least 16 apart, at least 12 from the walls and at least 20 from the area's ends.
- **Steps.** Nothing solid in the fields makes a step: the heroes' own steps and Lava Furrows' 1-high kerbs stand against the walls, off the lane.
- **Pieces.** My own pieces are checked for z-fighting (faces flickering against each other). The heroes and props were already checked when they were built.

**Budget.** The brief's 14,000 parts was for the yard and eight areas. There are now eighteen areas, and the Mounds are the new 41-part ones (252 of them, about 10,300 parts). The whole map is **27,078 parts**; see the table below.

- Turn on **StreamingEnabled** if you haven't, so a phone only loads the areas near the player.
- If you want fewer parts, the Mounds are the place to save. `Mound` is the same model as `PotatoKit.Mound`, so you can swap in a lighter one by name.

## Layout

All sizes are in studs. Roblox axes: X runs east, Y up, and the fields run north towards −Z. The ground's top is at Y 0.

### The yard (the safe zone)

- **Size and walls.** X −198..198, Z 0..332. Walls are 44 high and 8 thick, in Meadow Patch's brick, with a bright green cap 4 high. The ground and walls carry `Checker = 4`.
- **The twelve pens (new: 60 × 60).** They stand along three walls. Each pen runs 60 back from its marker and 30 either side.

| Marker | Entrance centre (X, Z) | LookVector (into the pen) | The pen |
|---|---|---|---|
| `Plot1`–`Plot4` | (−136, 40 / 104 / 168 / 232) | west | X −196..−136 |
| `Plot5`–`Plot8` | (136, 40 / 104 / 168 / 232) | east | X 136..196 |
| `Plot9`–`Plot12` | (−96 / −32 / 32 / 96, 270) | south | Z 270..330 |

  They keep part 1's order: 1–4 on the west wall north to south, 5–8 on the east wall, 9–12 on the south wall west to east. The pens are bare, so your code puts up the fences, the GateArch and the UpgradeBoard. There are 2 studs between each pen and the wall behind it, and 4 between neighbours.
- **The avenue.** It runs X −20..20 from the gate (Z 0) to the south pens (Z 270), cream with a darker trim. A cream path 8 wide runs from the avenue to every pen's gateway, and another runs along the front of the south pens.
- **The stalls,** each facing the avenue:
  - `TrailShop` at (−40, 26), facing east;
  - `SpeedShop` at (40, 26), facing west;
  - `IndexBoard` at (52, 60), facing west.
- **The spawn.** `Spawn` is at (0, 0, 120), with a flat `SpawnPad` round it.
- **New: suggested spots** for the pieces you place yourself. Use them or ignore them.
  - `FuseMachine` at (−80, 0, 120), front to +X. Its 28 × 20 footprint is clear.
  - `QuestNpc` at (34, 0, 92), front to −X, by the spawn.
- **Around the meeting place:**
  - the barn, silo, tractor, crates and hay against the north wall west of the gate;
  - the windmill, scarecrow and hay east of it;
  - a vegetable garden (soil rows and corn), a well, two fenced pumpkin patches and a pond;
  - picnic tables, benches, apple trees and big shade trees, bushes, flower clumps and grass along the avenue;
  - 18 lamp posts along the avenue.

  The barn, silo, windmill, well and rocks collide.

### The gate (at Z 0)

- **Pillars.** Two pillars 12 × 12 and 44 high stand in the wall line at X ±66. Each has a cap and a big brick potato sitting on top.
- **Beam.** It spans Y 30..44 across the 120-wide opening.
- **`TimerSouth` and `TimerNorth`.** Each is 44 × 10, bottom edge at Y 31, with its front face to the yard and to the fields respectively. Each has a chunky frame and a row of nine Neon bulbs (`…Bulbs`, `Flicker`, `NightLamp`).
- **`Barrier`.** It spans X −60..60, Y 0..30, 1 thick at Z −1. It is delivered **off** (Transparency 1, CanCollide off): you colour it and switch it on at night.
- **`RedLine`.** It is 1.2 wide across the opening at Z 0.
- **`LineBoard`.** It is 20 × 3, lying face up just inside the yard. Write on its Front face, which looks at the sky. Its top edge points north, so the text reads right way up for someone walking north.
- **`Markers/SafeLine`** is at (0, 0, 0), LookVector north.

### The fields

- **Size.** X −60..60 from Z 0 to Z **−3,960**: eighteen areas of 220 each. Area *n* runs from Z −220(*n*−1) to Z −220*n*. A back wall closes area 18.
- **Walls.** Both side walls are 44 high and 8 thick, in each area's brick, with a cap 4 high in the area's ground colour. The ground and walls carry `Checker = 4`.
- **Borders.** A pale `Border` strip 2 wide lies across the corridor at each area boundary.
- **Each area holds:**
  - **`Hero`**: the area's hero piece (the same as `PotatoKit.Heroes.<AreaId>`), against its wall with its front to the lane, a little north of the area's middle.
  - **`Scenery`**: the area's props (the same as `PotatoKit.Props.<AreaId>.<Name>`, up to three copies of each, scaled within their ScaleMin..ScaleMax). It also holds Folk Valley's own props, recoloured to suit the area. Props with Band Edge stand against the walls, Band Side between the wall and the lane, and Band Any anywhere.
  - **The area's own touch** on its walls (see the table).
  - **`Fx_*` attachments** on the `Ground` part, where the game can hang particles.
  - **In `Markers/AreaN`**:
    - `Zone`;
    - fourteen `Mound`s, some tucked beside props and the rest spread over the area;
    - the `AreaSign` on the west side just inside the area's south end.

## Names

### Workspace.PotatoMap

| Name | Where / what |
|---|---|
| `Markers/Plot1` … `Plot12` | On the ground at each pen's entrance centre, LookVector into the pen (see the layout). |
| `Markers/SafeLine` | (0, 0, 0), LookVector north |
| `Markers/Spawn` | (0, 0, 120). The visible pad round it is `Yard/SpawnPad`, which is flat and does not collide. |
| `Markers/FuseMachine`, `Markers/QuestNpc` | **New**, optional: where the Fuse Machine and Farmer Spud could stand, LookVector to their front |
| `Markers/Area1` … `Area18` | One Folder per area, holding the three items below |
| `…/AreaN/Zone` | Invisible, 120 × 60 × 220 over the area's floor. CanCollide, CanTouch and CanQuery are off. Attributes `Area` (number) and `AreaName`. |
| `…/AreaN/Mound` × 14 | The kit's new Mound, tinted for the area. `Mound:GetPivot()` is the top centre of the hollow, where the seed sits. |
| `…/AreaN/AreaSign` | Folk Valley's sign: brick posts on bases, a header beam in the area's colour, and the dark **`Board`** (16 × 9, bottom edge at Y 8, front face south). Attribute `Area`. |
| `Gate/TimerSouth`, `TimerNorth`, `Barrier`, `RedLine`, `LineBoard` | As above. The rest of `Gate` is `Pillar`, `PillarCap`, `PillarPotato`, `Beam`, `BeamCap` and the timer frames and bulbs. |
| `Yard/TrailShop`, `Yard/SpeedShop` | Market stalls, each with a flat dark **`Board`** in its header (its front faces the avenue) and an invisible **`Prompt`** at chest height in front. TrailShop has a rack of rainbow `Ribbon`s (attribute `Sway`). SpeedShop has a big sneaker on its roof. |
| `Yard/IndexBoard` | The big green chalkboard on legs with a little roof. **`Board`** is the 16 × 10 chalk surface, plus a **`Prompt`**. |
| `Yard/Lamps/LampPost` × 18 | Folk Valley's lantern post, each with a Neon **`Bulb`** (`NightLamp`) |
| `Yard/Scenery/*` | Barn, Silo, Tractor, Windmill, Scarecrow, Well, Pond, Picnic, HayBale, Pumpkins, Crates, Tree, BigTree, Bush, Flowers, Grass, Rock, Bench, SoilRows, CornRow, PumpkinPatch |
| `Yard/Ground`, `Avenue`, `Wall`, `WallCap`, `Path`, `PathTrim`, `AvenueTrim` | The yard's shell. `Avenue` is the map's PrimaryPart. |
| `Fields/AreaN/Ground`, `Wall`, `WallCap`, `Border` | Big studded parts. Ground and walls carry `Checker = 4`. Area 18 also has `BackWall` and `BackWallCap`. |
| `Fields/AreaN/Hero` | The area's hero |
| `Fields/AreaN/Scenery/*` | The area's props, each a Model named by its kind |
| `Fields/AreaN/Icicles`, `LavaChannels`, `Icing`, `Stars`, `NeonStrips`, `Water`, `Columns`, `Blocks`, `Glitch` | Each area's own touch (see the table) |

**Attributes you can animate** (as before):

- `Spin`: degrees a second about the part's own Y.
- `Sway`: on hanging things.
- `Flicker`: on Neon.
- `NightLamp`: on Neon that should light up at night.

The Mounds' `Soil`, `Leaf` and `Flag` bricks carry `Shade` (see the kit README).

**Attachments**, on each area's `Ground`:

- `Fx_Snow`: Frost Fields, high up.
- `Fx_Embers`: Lava Furrows, on the lava channels.
- `Fx_Bubbles`: Coral Cove, and the water in Mushroom Marsh.
- `Fx_Stars`: Cosmic Garden and Glitch Void.
- `Fx_Sparkle`: Crystal Caverns, Candy Crops, Cloud Kingdom, Spud Olympus and Neon City.
- `Fx_Smoke`: Haunted Hollow, as mist.

## The eighteen areas

| # | Area | Ground / walls | Hero (wall) | Its own touch | Parts |
|---|---|---|---|---|---|
| 1 | Meadow Patch (`Meadow`) | `68D03E` / `CE7C4E` | the red-and-white windmill with turning sails and a potato scarecrow (east) | none | 1,809 |
| 2 | Sandy Dunes (`Dunes`) | `F2D280` / `D6A86C` | the stepped pyramid with a potato pharaoh (west) | none | 1,588 |
| 3 | Mushroom Marsh (`Marsh`) | `2C7A6A` / `34603A` | the giant toadstool house (east) | four patches of murky water, flush with the ground and walk-through | 1,738 |
| 4 | Jungle Ruins (`Jungle`) | `4FA83A` / `7D8F62` | the stepped temple with the golden idol (west) | none | 1,515 |
| 5 | Coral Cove (`Reef`) | `E8D49A` / `3AA6B0` | the shipwreck with the pirate potato (east) | none | 1,437 |
| 6 | Frost Fields (`Frost`) | `ECF4FC` / `9CC8EC` | the ice castle gate (west) | icicles under both caps | 1,500 |
| 7 | Haunted Hollow (`Haunt`) | `3E5A3A` / `4A3B5C` | the haunted manor and the giant jack-o'-lantern (east) | none | 1,478 |
| 8 | Lava Furrows (`Lava`) | `3C383E` / `7C2220` | the volcano with lava running down it (west) | glowing lava channels along both walls behind low rock kerbs (not walkable) | 1,453 |
| 9 | Crystal Caverns (`Crystal`) | `4C3468` / `46247C` | the giant crystal cluster bursting out of a mine mouth (east) | none | 1,464 |
| 10 | Dino Valley (`Dino`) | `7AB24A` / `8B6A4A` | the huge dinosaur skeleton (west) | none | 1,229 |
| 11 | Toy Town (`Toy`) | `8FD0FF` / `E04A3A` | the castle of building blocks and the toy train (east) | toy-block bands in four colours along the foot of both walls | 1,267 |
| 12 | Candy Crops (`Candy`) | `FCB0CE` / `F278AC` | the three-tier cake (west) | white icing drips under both caps and a red-and-white stripe band on top | 1,811 |
| 13 | Clockwork Yard (`Clock`) | `A89A80` / `7A5A3A` | the clock tower with its turning gears (east) | none | 1,336 |
| 14 | Neon City (`Neon`) | `2A2A3A` / `15121C` | the stage with speakers and beams of light on a floor grid (west) | Neon strips along both walls and Neon lines at the lane's edges | 1,070 |
| 15 | Cloud Kingdom (`Cloud`) | `BFE4FF` / `E8ECFF` | the rainbow over the palace of cloud (east) | none | 1,174 |
| 16 | Cosmic Garden (`Cosmic`) | `1A1E46` / `28163A` | the crashed rocket (west) | Neon star specks on both walls, glowing star tiles on the ground | 1,428 |
| 17 | Glitch Void (`Void`) | `1A1726` / `2B2233` | the huge black cube with lit edges (east) | glitch squares flickering on both walls | 972 |
| 18 | Spud Olympus (`Olympus`) | `D8E8C0` / `F2EFE6` | the temple with the potato Zeus (west) | white columns with gold capitals along both walls | 1,162 |

Each row's parts count everything in `Fields/AreaN` and `Markers/AreaN`: the hero, the props, the Mounds, the sign and the shell. The yard has 1,582 parts and the gate 65.

## Previews (`previews/map/`)

The pictures show the kit's fences, a few potatoes and seeds in some pens, so the yard looks as it will in the game. **The map itself leaves the pens bare.**

- `map_overview.jpg`: from (0, 60, 200) looking at (0, 0, −100), the view asked for in part 1.
- `map_corridor.jpg`: from (0, 7, −40) looking north up the corridor.
- `map_yard.jpg`: the yard from high over its south wall.
- `map_gate.jpg`: the gate, the stalls and the avenue from the spawn.
- `map_aerial.jpg`: high over the yard, looking up the whole corridor.
- `map_area01_Meadow.jpg` … `map_area18_Olympus.jpg`: each area at eye height, from just inside its south end looking north.
