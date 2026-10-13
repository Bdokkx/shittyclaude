# Steal a Potato: the bricks kit

One unattended build script per piece. Run it from the command bar or with `loadstring`. It merges into **ReplicatedStorage.PotatoKit**, making the folder if it is missing and setting the attribute `Studs = true`. Each item it lists replaces whatever has that name in that folder; nothing else is touched, so every script is safe to run twice.

Every Part is a plain Roblox Part:

- **Plastic, Inlet on all six faces:** the default.
- **SmoothPlastic, Smooth faces:** flat surfaces that carry text or a face.
- **Neon (Smooth):** only what glows.

**The map** (4.6) is separate: `out/map/BuildPotatoMap.lua` builds `Workspace.PotatoMap` with all eighteen areas dressed with these heroes and props. See `out/map/README.md`.

The pieces so far:

| Script | Piece |
|---|---|
| `BuildPotatoesMeadow.lua` | 4.1, the Meadow Patch potatoes and the six potato clips |
| `BuildPlotKit.lua` | 4.2, the plot kit: four fence tiers (GateArch 14 wide), SoilHeap and SoilPatch (instead of Soil), UpgradeBoard, the new Mound, the 18 Seeds |
| `BuildQuestNpc.lua` | Farmer Spud, the quest NPC, and his four clips |
| `BuildFuseMachine.lua` | The Fuse Machine |
| `BuildGuardians1.lua`, `BuildGuardians2.lua`, `BuildGuardians3.lua` | The 18 guardians, six per script, and their Sleep, Wake and Run clips |
| `BuildRootMonster.lua` | 4.3, the RootMonster in bricks with its four clips |
| `BuildPotatoesDunes.lua` | The Sandy Dunes potatoes |
| `BuildPotatoesMarsh.lua` | The Mushroom Marsh potatoes |
| `BuildPotatoesFrost.lua` | The Frost Fields potatoes |
| `BuildPotatoesLava.lua` | The Lava Furrows potatoes |
| `BuildPotatoesCrystal.lua` | The Crystal Caverns potatoes |
| `BuildPotatoesCandy.lua` | The Candy Crops potatoes |
| `BuildPotatoesCosmic.lua` | The Cosmic Garden potatoes |
| `BuildPotatoesJungle.lua` | The Jungle Ruins potatoes |
| `BuildPotatoesReef.lua` | The Coral Cove potatoes |
| `BuildPotatoesHaunt.lua` | The Haunted Hollow potatoes |
| `BuildPotatoesDino.lua` | The Dino Valley potatoes |
| `BuildPotatoesToy.lua` | The Toy Town potatoes |
| `BuildPotatoesClock.lua` | The Clockwork Yard potatoes |
| `BuildPotatoesNeon.lua` | The Neon City potatoes |
| `BuildPotatoesCloud.lua` | The Cloud Kingdom potatoes |
| `BuildPotatoesVoid.lua` | The Glitch Void potatoes |
| `BuildPotatoesOlympus.lua` | The Spud Olympus potatoes |
| `BuildSceneryMeadow.lua` | The Meadow Patch hero and props |
| `BuildSceneryDunes.lua` | The Sandy Dunes hero and props |
| `BuildSceneryMarsh.lua` | The Mushroom Marsh hero and props |
| `BuildSceneryJungle.lua` | The Jungle Ruins hero and props |
| `BuildSceneryReef.lua` | The Coral Cove hero and props |
| `BuildSceneryFrost.lua` | The Frost Fields hero and props |
| `BuildSceneryHaunt.lua` | The Haunted Hollow hero and props |
| `BuildSceneryLava.lua` | The Lava Furrows hero and props |
| `BuildSceneryCrystal.lua` | The Crystal Caverns hero and props |
| `BuildSceneryDino.lua` | The Dino Valley hero and props |
| `BuildSceneryToy.lua` | The Toy Town hero and props |
| `BuildSceneryCandy.lua` | The Candy Crops hero and props |
| `BuildSceneryClock.lua` | The Clockwork Yard hero and props |
| `BuildSceneryNeon.lua` | The Neon City hero and props |
| `BuildSceneryCloud.lua` | The Cloud Kingdom hero and props |
| `BuildSceneryCosmic.lua` | The Cosmic Garden hero and props |
| `BuildSceneryVoid.lua` | The Glitch Void hero and props |
| `BuildSceneryOlympus.lua` | The Spud Olympus hero and props |

---

## 4.1 Meadow Patch potatoes and clips

`BuildPotatoesMeadow.lua` builds:

| Path | What |
|---|---|
| `PotatoKit.Potatoes.Spud` | Common: plain russet with darker spots and a knobbly lump |
| `PotatoKit.Potatoes.TaterTot` | Common: short, wide, golden; crispy bits on top and sides |
| `PotatoKit.Potatoes.YukonGold` | Uncommon: pale gold egg with a shine and the little leaf it was born with |
| `PotatoKit.Potatoes.RedRascal` | Rare: round and red, one brow up, lopsided grin with a tooth |
| `PotatoKit.Potatoes.SweetPotato` | Epic: tall orange, pointed at both ends, pink bow |
| `PotatoKit.Potatoes.GoldenSpud` | Legendary: Spud in solid gold, two Neon star glints |
| `PotatoKit.PotatoAnimations.PotatoIdle` … `PotatoLevelUp` | six KeyframeSequences, see below |

If your place still has the part-1 kit (meshes) in a folder called PotatoKit, its old pieces stay there until the brick pieces replace them.

### Parts

All of it is plain Parts:

- **Plastic, Inlet on all six faces:** the bodies, limbs, shoes, sprouts and crowns.
- **SmoothPlastic, Smooth faces:** the eyes, mouths, cheeks, glints and tongues.
- **Neon (Smooth):** only the crown jewels and Golden Spud's two star glints.
- **Flags:** everything except Root is unanchored, Massless, and has CanCollide, CanTouch and CanQuery off. CastShadow is off on parts under 2.5 studs.

Every potato is 43–45 Parts in total. That count includes Root and the invisible feature parts.

### The rig (the same in all 48)

- **Model `<Id>`**
  - PrimaryPart is Root.
  - The pivot is the middle of the footprint on the ground; the front is -Z.
  - Number attribute **LegHeight**: Spud 1.2, TaterTot 1.0, YukonGold 1.2, RedRascal 1.15, SweetPotato 1.3, GoldenSpud 1.2.
- **Root:** invisible, anchored, 2 × 0.4 × 2, sitting on the ground (PivotOffset puts the pivot at its bottom).
- **Body:** the body's core brick, on Motor6D **Body** (Root → Body), hinged on the ground under the body. Every other brick of the body, and everything the kind always wears (spots, lump, bow, shine, star glints, Yukon's leaf), is a child of Body named **Extra** and welded to it.
- **Features:** each has its own Motor6D, named like its part and parented to that part.

| Feature | Shown from | Joint on | Parts |
|---|---|---|---|
| Dimples | level 1 only | Body | holder + 2 dark dots |
| Eyes | 2 | Body | holder + 2 eyes + 2 glints (Red Rascal also 2 brows) |
| Mouth | 3 | Body | holder + mouth, tongue, 2 cheeks |
| ArmL, ArmR | 4 | Body (shoulder) | the arm brick |
| HandL, HandR | 5 | the arm (wrist) | a white glove brick |
| LegL, LegR | 6 | **Root** (hip at X = ±0.75) | the leg brick |
| FootL, FootR | 7 | the leg (ankle) | a shoe brick |
| Sprout | 8 | Body (top of the head) | holder + stem + 2 leaves |
| Crown | 10 | Body (top of the head) | holder + band, 3 points, Neon jewel |

**Holders.** A feature made of several bricks hangs on a "holder": an invisible 0.2 part that carries the feature's name and its Motor6D. The bricks are the holder's **children** and are welded to it. To hide a feature, hide the holder's BasePart descendants. A one-brick feature is the brick itself.

**Legs.** The legs are built for the raised body. When they show, raise the body by LegHeight:

```lua
bodyMotor.C0 = bodyMotor.C0 * CFrame.new(0, LegHeight, 0)
```

`bodyMotor` is the Motor6D inside Body. Without legs the body sits on the ground and the hidden legs are inside it.

### The clips

All clips run at 30 fps on the joint names above, so one set fits every kind. Easing is Linear, with the motion baked into every frame. A clip keys only the joints it moves, so a lower-priority clip can still drive the others; for example, the Idle blink carries on under Wave.

| KeyframeSequence | Length | Loop | Priority | Marker | What it does |
|---|---|---|---|---|---|
| PotatoIdle | 2.0 s | yes | Idle | – | Breathes, sways and twists a little, then one blink at 1.4 s |
| PotatoHop | 0.8 s | yes | Movement | – | Squash, spring 1.5 up with arms up and toes pointed, land, squash |
| PotatoWave | 1.2 s | no | Action | – | Raises its right arm beside its head and waves three times |
| PotatoDance | 2.4 s | yes | Movement | – | Four beats: bounce, sway, twist; arms pump in turn, feet step |
| PotatoHatch | 0.8 s | no | Action | **Out** at 0.2 s | Pops up out of the ground with a twist, eyes shut; overshoots, settles |
| PotatoLevelUp | 0.7 s | no | Action | **Top** at 0.33 s | Crouch, jump 2.2 up, spin once (legs go round with it), land |

**Blink.** Poses can't scale, so a blink turns the Eyes joint 90° about X. The eye plates fold flat into a dark line for two frames.

**Hatch.** It starts 7 studs under the pivot, deep enough to hide even a level-10 potato with legs and crown. Out is the moment it is fully out of the ground. If you would rather grow it from nothing in code, tween its scale up to the Out marker. The clip still reads.

### Previews

These are in `previews/potatoes/`, rendered in Blender, where studs show as inlet rings:

- `lineup_Meadow_L10.jpg`: all six at level 10.
- `levels_Spud.jpg`: Spud at levels 1, 2, 4, 6, 8 and 10.
- `turn_<Id>.jpg`: each potato from the front, right, back and left.
- `clip_<Clip>.jpg`: six frames of each clip.
- `potato_clips_Meadow.mp4`: all six playing every clip.

---

## 4.2 The plot kit (`BuildPlotKit.lua`)

| Path | What |
|---|---|
| `PotatoKit.Fences.Fence_Wood` | Starter. Dark brown posts with a plain cap; bright wood rails. |
| `PotatoKit.Fences.Fence_Gold` | 10 slots. Gold posts with cream bands and a round gold knob; gold rails with a cream strip on top. |
| `PotatoKit.Fences.Fence_Diamond` | 20 slots. White posts with cyan bands and a Neon cyan jewel; cyan and white rails with little diamonds between them. |
| `PotatoKit.Fences.Fence_Rainbow` | 30 slots. Dark posts with a Neon star; two Neon rails for you to cycle through the rainbow. |
| `PotatoKit.SoilHeap` | A heap of dug soil 4.5 across and 1 high, for a seed planted in a pen: three Folk Valley rounds stacked in steps, four lumps on its sides and a pebble. 13 parts. |
| `PotatoKit.SoilPatch` | A flat patch of dug soil 3.6 across and 0.22 high, under a grown potato: a low round with four lumps round its edge and a pebble. 8 parts. |
| `PotatoKit.UpgradeBoard` | Folk Valley sign, small: legs on stone plinths, a gold header, the dark `Board`, a green `Button` under it and an invisible `Prompt`. |
| `PotatoKit.Mound` | The seed bed in the fields, after the owner's photo: a heap of dug soil with a hollow in its top and a lip of six lumps round it, a ring of eight clods (three with a smaller clod on top), three potato-plant leaves drooping over the edge, a little stake with a yellow pennant, a pebble. About 6.5 across; the hollow is 0.84 up and 0.4 deep. 41 parts. |
| `PotatoKit.Seeds.Seed_Meadow` … `Seed_Olympus` | Eighteen seeds, one per area, see below. |

Each fence tier is a Folder, replaced as a whole. It holds three Models, built the same way in every tier:

- **`Post`**
  - 4.4 tall to the top of its cap; the tier's topper rises above that.
  - Pivot on the ground at its centre.
- **`Rail`**
  - 7 long between post centres (local X −3.5..3.5), tucked 0.18 into each post.
  - Every brick runs along X or sits square to it, so you can stretch it 10% by scaling X.
  - The rail bricks are named `Bar`. In Fence_Rainbow they are Neon, with a `Hue` attribute (0 and 0.5) as a suggested phase.
  - Pivot on the ground halfway between the posts.
- **`GateArch`**
  - An open doorway **14 wide** (local X) and 6.7 high; the player runs through it along Z. The posts are 1.6 square at X = ±7.8.
  - Two posts on plinths and a header beam in the tier's strong colour. Fence_Rainbow's header is six Neon stripes.
  - **`Board`** faces the front (-Z) and **`BoardBack`** the back, **12.2 × 2.8**, framed by trim either side. Both are dark SmoothPlastic, so the owner's name in white reads from either side.
  - Attribute `OpeningWidth` = 14. Pivot on the ground at the centre.

**Pivots:**

- **SoilHeap:** the top centre of the heap (Y 1.0), where the seed stands.
- **SoilPatch:** the top centre of the patch (Y 0.22), where the potato stands.
- **Mound:** the top centre of the hollow (Y 0.84), where the seed sits.
- **UpgradeBoard:** on the ground at its centre. `Board` and `Button` face -Z, and `Prompt` is 2.6 in front.

**Tinting the soil, the leaves and the flag.** In SoilHeap, SoilPatch and the Mound every soil brick is named **`Soil`**, every brick of the three leaves (stalks too) **`Leaf`** and the two pennant bricks **`Flag`**. They come in a few close shades so they read as soil and leaves when untouched. Each of them carries a number attribute **`Shade`**: how far its own colour is from its piece's base colour (negative is darker, positive is lighter). Set `part.Color = tint` and the shading flattens out; to keep it, shade each brick by its own Shade:

```lua
local function shaded(tint, k)
	if k < 0 then return tint:Lerp(Color3.new(0, 0, 0), -k) end
	return tint:Lerp(Color3.new(1, 1, 1), k)
end
-- for each part p named Soil, Leaf or Flag: p.Color = shaded(areaTint, p:GetAttribute("Shade") or 0)
```

The stake (`Stake`) and the pebbles (`Pebble`) keep their colours. The map's 252 Mounds come already tinted for their areas this way (see `out/map/README.md`).

**The old Soil.** `PotatoKit.Soil` (the 5 × 5 bed) is no longer built. A Soil left by an earlier run of this script stays where it is, because the script never removes what it does not build: delete it by hand if you like.

**Seeds.** Each seed is an egg about 1.7 wide; 2.4–3.1 tall with its topper (toppers are 30% bigger than in the first cut). Pivot at the bottom. Every brick of the egg is named **`Body`** and is light grey (236, 236, 232) for you to tint. The rest comes coloured:

| Seed | Topper and details |
|---|---|
| Meadow | Green sprout with two leaves; two dark specks |
| Dunes | A sand band round it; a tiny cactus with a pink flower |
| Marsh | A red toadstool with white dots; a lily pad at its foot |
| Frost | A snow cap, three icicles, a twig |
| Lava | A Neon flame on top (red, orange, yellow); two Neon cracks |
| Crystal | Three crystal shards (purple, cyan, lilac); a purple gem |
| Candy | A lollipop on a stick; three sprinkles |
| Cosmic | A gold ring round it; a Neon star on top |
| Jungle | Three palm fronds on a stub; a vine wound round it |
| Reef | An orange starfish on top; pink coral and a blue gem on its side |
| Haunt | A tiny jack-o'-lantern with Neon eyes; a purple band |
| Dino | A spotted dino egg with a crack on top and a fern curl |
| Toy | A wind-up key; red and blue stripes |
| Clock | A brass gear on top; a clock face on its front |
| Neon | A Neon antenna ball; cyan and magenta Neon stripes |
| Cloud | A little white cloud; two raindrops |
| Void | Glitch cubes, black and Neon; a Neon magenta crack |
| Olympus | A laurel wreath; a gold band |

**Flags.** All of 4.2 is decoration: anchored, CanCollide, CanTouch and CanQuery off, and no shadow from parts under 2.5 studs. If you want solid fences, turn CanCollide on for the posts and bars.

**Previews:** `previews/plot/`

- `plot_tiers.jpg`: the four tiers side by side.
- `plot_Fence_<Tier>.jpg`: each tier, with Spud for scale.
- `plot_misc.jpg`: SoilHeap with a seed on it, SoilPatch with a potato on it, the Mound with a seed in its hollow, and the UpgradeBoard.
- `plot_soil.jpg`: SoilHeap and SoilPatch close up, empty and in use.
- `plot_mound.jpg`: the Mound with a seed, empty, and tinted for Sandy Dunes and Frost Fields with the `shaded()` code above.
- `plot_seeds.jpg`: the eighteen seeds as built; `plot_seeds_tinted.jpg`: the same with their bodies tinted.

---

## Farmer Spud, the quest NPC (`BuildQuestNpc.lua`)

| Path | What |
|---|---|
| `PotatoKit.QuestNpc` | Farmer Spud, 11.6 tall, 120 parts (attribute `Height` = 11.6) |
| `PotatoKit.QuestNpcAnimations.Idle`, `Wave`, `Talk`, `Cheer` | KeyframeSequences |

**What he is.**

- **Head:** a big potato head, wider in the middle, under a straw hat with a red band and straw sticking out of the brim.
- **Face:** bushy white brows, a big round nose with a rosy tip, pink cheeks, and a bushy white moustache with a wheat stalk poking out of it.
- **Clothes:** a red neckerchief, a cream shirt with rolled sleeves, blue overalls with gold buttons, a pencil in the bib pocket, and a cross-stitched red patch on the left knee.
- **Boots, hands, hoe:** brown boots with dark soles, hands with three fingers and a thumb, and a hoe held upright in his left hand.

**The rig.**

- **Root:** Model `QuestNpc`, PrimaryPart **Root** (invisible, anchored, 2 × 0.4 × 2 on the ground). The pivot is the middle of his footprint on the ground; he faces -Z.
- **One name per joint.** Every Motor6D drives an invisible holder at its hinge, and the holder **has the Motor6D's own name**. The visible bricks of that group are the holder's children, welded to it. So a Pose, its Motor6D and the Motor6D's Part1 all share one name, however your player looks joints up.
- **Flags:** everything is unanchored and Massless except Root and the Prompt. CanCollide and CanTouch are off throughout. Eyes, glints, cheeks, mouth and stitches are SmoothPlastic; there is no Neon.

| Motor6D | Part0 → Part1 | Moves |
|---|---|---|
| **Waist** | Root → Waist | torso: shirt, overalls, collar, neckerchief, straps, buttons, pocket |
| **Neck** | Waist → Neck | the head, nose, cheeks, mouth |
| **ShoulderL**, **ShoulderR** | Waist → ShoulderL / ShoulderR | upper arms (sleeves) |
| ElbowL, ElbowR | ShoulderL → ElbowL, ShoulderR → ElbowR | forearm, cuff, hand with fingers; the hoe is in ElbowL |
| HipL, HipR | Root → HipL / HipR | legs, cuffs, boots (the knee patch is on HipL) |
| **Brow** | Neck → Brow | the bushy brows |
| **Moustache** | Neck → Moustache | the moustache and its wheat stalk |
| Eyes | Neck → Eyes | the eyes and glints. Turned 90° about X they fold into a line: a blink |
| Hat | Neck → Hat | the straw hat |

**`Prompt`**: an invisible, anchored 4 × 4 × 2 part at chest height (Y 6), 3.4 in front of him, with CanCollide, CanTouch and CanQuery off.

**Clips.** 30 fps, Linear keys, poses named after the joints above.

| KeyframeSequence | Length | Loop | Priority | What he does |
|---|---|---|---|---|
| Idle | 4.0 s | yes | Idle | Two breaths; looks slowly to his left, then right, brows lifting as he looks; two blinks; one twitch of the moustache |
| Wave | 1.6 s | no | Action | Raises his right arm beside his head and waves three times from the elbow, leaning away and tilting his head, brows up, moustache up in a smile |
| Talk | 2.0 s | loop | Movement | Nods and turns his head, gestures with his right hand (the hoe hand moves a little), moustache twitching as if he's talking, brows working |
| Cheer | 1.6 s | no | Action | Both arms up (the hoe goes up too), two small hops with the legs leaving the ground, hat bouncing, eyes shut with joy at the top of each hop |

Wave and Cheer start and end at rest, so they fall back into Idle cleanly.

**Previews:** `previews/npc/`

- `turn_FarmerSpud.jpg`, `face_FarmerSpud.jpg`
- `clip_FarmerSpud_<Clip>.jpg`
- `FarmerSpud_clips.mp4`

---

## The Fuse Machine (`BuildFuseMachine.lua`)

| Path | What |
|---|---|
| `PotatoKit.FuseMachine` | The machine: 28 wide, 20 deep, 23 tall, 170 parts |

**What it is.** A chunky blue cabinet on a two-tier grey stone step, with:

- **Front:** a big lit white screen in a dark bezel. Left of the screen as you face it (+X), a panel with three red lights, a big round red button and a lever with a red knob.
- **Top:** a low dark dome ringed by glowing cyan bars, with a light on its tip. A fat dark pipe arches from the dome down into a control block on the machine's left (-X), which is your right as you face the screen. The control block has two dials, a vent, an amber lamp and the aerial with its red light.
- **Sign:** a dark sign over the top in a blue frame of yellow bulbs.
- **Sockets:** three round sockets on the step in front, each with a glowing cyan ring and a cyan lamp above it on the cabinet.
- **Around it:** yellow and black hazard stripes along the step's front edge, glowing conduits up both sides, and a hatch with a red valve wheel on the back.

The dome and the pipe stay low enough that the whole sign shows from a player's eye level as they walk up (`face_FuseMachine_eye.jpg`).

**Pivot.** PrimaryPart **Step** (the lower stone slab) has a PivotOffset, so the pivot is the middle of the footprint on the ground. The front is -Z.

**Flags.** Everything is anchored with CanTouch off.

- **Solid** (CanCollide and CanQuery on): the step, cabinet, skirt, top trim, the dome's lower tier, the pipe and the control block.
- **Decoration** (CanCollide, CanTouch and CanQuery off): everything else. CastShadow is off on decoration under 2.5 studs.

**Parts you will use.**

| Name | What |
|---|---|
| **Board** | SmoothPlastic, 22 × 5 × 0.3, centred at Y 19.3, its front face (-Z) at Z 5.13. For FUSE MACHINE. |
| **Screen** | Neon f4fbff, 9.2 × 6.4 × 0.2 at (-2.2, 7.4, -4.68), front face at Z -4.78. For the "?". |
| **Prompt** | Invisible and anchored, 8 × 5 × 2 at (0, 3, -11), just in front of the step at chest height. CanCollide, CanTouch and CanQuery are off. |
| **Socket1**, **Socket2**, **Socket3** | The pads the three potatoes stand on, left to right as you face the machine: Socket1 at X 6, Socket2 at X 0, Socket3 at X -6, all at Z -6.8. Their tops are at Y 2.31. Each is 1.7 × 0.22 × 1.7, turned 45°. |

**Parts you may want to light up or move during a fuse.** All Neon except the lever and the button.

| Name | What |
|---|---|
| `Ring` (8) | The cyan bars round the dome |
| `DomeLight` | The light on the dome's tip |
| `SocketGlow` (4 per socket) | The cyan rings round the sockets |
| `SocketLamp` (3) | The lamps over the sockets, at X -6, 0, 6 |
| `Bulb` (24) | The sign's bulbs |
| `Light` (3) | The red lights on the panel |
| `Lamp` | The amber lamp on the control block |
| `AerialLight` | The aerial's tip |
| `ConduitGlow` (2) | The strips up the sides |
| `Lever`, `LeverKnob` | The lever, leaning to your left as you face it. It pivots at the bottom end of `Lever`, at (6.08, 4.98, -5.25). |
| `Button` (4) | The red button |

**Every name.** Each name is followed by how many parts carry it.

- **Step and cabinet:** Step 2, Stone 4, Stripe 11, Cabinet, Skirt, TopTrim, Pillar 4, Conduit 2, ConduitGlow 2, Vent 10, Hatch 2, Hinge 2, Valve 4.
- **Front:** Bezel 2, Screen, Panel 2, Light 3, ButtonBase, Button 4, LeverBase, Lever, LeverKnob, SocketLamp 3.
- **Dome and pipe:** Dome 7, DomeLight, Ring 8, Pipe 5, Collar 5.
- **Control block and aerial:** Control 3, Dial 4, Needle 2, LampBase, Lamp, Aerial 4, AerialLight.
- **Sign:** SignPost 2, SignFrame, Board, SignTop, Bulb 24.
- **Sockets and prompt:** SocketRim 12, SocketGlow 12, SocketPad 6, Socket1, Socket2, Socket3, Prompt.

**Previews:** `previews/fuse/`

- `turn_FuseMachine.jpg`: front, right, back, left
- `face_FuseMachine.jpg`: three-quarter view
- `face_FuseMachine_eye.jpg`: from a player's eye level, 34 studs out

---

## The 18 guardians (`BuildGuardians1.lua`, `BuildGuardians2.lua`, `BuildGuardians3.lua`)

| Script | Areas | Size |
|---|---|---|
| `BuildGuardians1.lua` | Meadow, Dunes, Marsh, Jungle, Reef, Frost | 257 KB |
| `BuildGuardians2.lua` | Haunt, Lava, Crystal, Dino, Toy, Candy | 223 KB |
| `BuildGuardians3.lua` | Clock, Neon, Cloud, Cosmic, Void, Olympus | 208 KB |

Each script builds its six into these paths, and leaves the other areas' guardians alone:

| Path | What |
|---|---|
| `PotatoKit.Guardians.<AreaId>` | The guardian (a Model) |
| `PotatoKit.GuardianAnimations.<AreaId>.Sleep`, `Wake`, `Run` | Its clips (KeyframeSequences) |

**Every guardian.**

- **Root:** the PrimaryPart. Anchored and invisible, 2 × 0.4 × 2, on the ground in the middle of its footprint. The front is -Z. Move the guardian by moving Root (its pivot is on the ground).
- **The other parts:** unanchored and Massless, with CanCollide, CanTouch and CanQuery off.
- **Joints:** as on Farmer Spud. Parts are welded into groups, and the groups are joined by Motor6Ds. Each Motor6D's Part1 carries the Motor6D's own name, so a Pose, its Motor6D and its Part1 share one name. A few groups hang off small invisible parts at their hinge, named the same way.
- **Eyes:**
  - **EyeOpen:** every part of the open eyes (whites, pupils, glints).
  - **EyeShut:** the closed-eye lines.
  - The models are built awake: EyeOpen at Transparency 0, EyeShut at 1. Swap them for sleep.
  - Some eyes glow (Neon): Frost's pupils, Lava, Toy, Clock, Neon, and both sets on Void (its shut eyes are magenta lines).
- **Attributes:**
  - `Gait`: Stomp, Scuttle, Hop, Float or Gallop.
  - `Height`: its top above the ground in the rest pose.
  - `RunSpeed`: the speed in studs a second that Run's feet are made for (see below).
- **Parts:** 34 to 56 each, Root included.

| Area | Guardian | Gait | Height | Parts | RunSpeed | Motor6Ds (Part0 → Part1 is Root → Body → … unless noted) |
|---|---|---|---|---|---|---|
| Meadow | Scarecrow on a pole, crow on its hat | Hop | 9.6 | 51 | 7 | Body; LegL, LegR, ArmL, ArmR, Head (on Body); Hat (on Head); Crow (on Hat) |
| Dunes | Scorpion | Scuttle | 6.5 | 56 | 8.5 | Body; Head, ClawL, ClawR, LegL1–3, LegR1–3, Tail (on Body); Sting (on Tail) |
| Marsh | Bog frog with a mushroom | Hop | 6.1 | 48 | 8 | Body; Head, LegL, LegR, ArmL, ArmR (on Body); Jaw (on Head) |
| Jungle | Tiger | Gallop | 7.0 | 48 | 15 | Body; Head, LegFL, LegFR, LegBL, LegBR, Tail (on Body); Jaw (on Head) |
| Reef | Giant crab with an eyepatch | Scuttle | 6.2 | 51 | 7.7 | Body; Head (eye stalks), ClawL, ClawR, LegL1–3, LegR1–3 (on Body) |
| Frost | Snow golem | Stomp | 9.8 | 47 | 6.5 | LegL, LegR, Body (on Root); Head, ArmL, ArmR (on Body) |
| Haunt | Ghost with a lantern | Float | 7.8 | 34 | 8 | Body; Head, ArmL, ArmR, Tail (on Body) |
| Lava | Magma golem | Stomp | 9.7 | 36 | 6.7 | LegL, LegR, Body (on Root); Head, ArmL, ArmR (on Body) |
| Crystal | Crystal spider | Scuttle | 6.9 | 53 | 11.7 | Body; Head, LegL1–4, LegR1–4 (on Body) |
| Dino | Raptor | Gallop | 8.3 | 43 | 16.1 | Body; Head, ArmL, ArmR, LegL, LegR, Tail (on Body); Jaw (on Head); TailTip (on Tail) |
| Toy | Wind-up tin robot | Stomp | 9.4 | 47 | 9.5 | LegL, LegR, Body (on Root); Head, ArmL, ArmR, Key (on Body) |
| Candy | Jelly slime with a cherry | Hop | 6.5 | 36 | 6 | Body; Top (on Body); Head (on Top: the face) |
| Clock | Clockwork beetle | Scuttle | 6.6 | 52 | 8.5 | Body; Head, Gear, LegL1–3, LegR1–3 (on Body) |
| Neon | Patrol drone | Float | 7.5 | 34 | 12 | Body; Head (the eye), RotorFL, RotorFR, RotorBL, RotorBR (on Body) |
| Cloud | Storm cloud | Float | 8.3 | 40 | 7 | Body; Head (the face), PuffL, PuffR, Bolt, Rain (on Body) |
| Cosmic | Star hound | Gallop | 6.4 | 42 | 14.6 | Body; Head, LegFL, LegFR, LegBL, LegBR, Tail (on Body); Jaw (on Head) |
| Void | Glitch cube | Hop | 7.7 | 38 | 6 | Body; SliceMid, SliceTop, Bits (on Body); Head (on SliceTop: the face) |
| Olympus | Marble lion with a laurel | Gallop | 8.1 | 39 | 13.4 | Body; Head, LegFL, LegFR, LegBL, LegBR, Tail (on Body); Jaw (on Head) |

**The clips.** They are in `PotatoKit.GuardianAnimations.<AreaId>` and are posed on the guardian's own Motor6Ds, like Farmer Spud's. Keys are Linear.

| Clip | Length | Loop | Keys a second | Priority | What it does |
|---|---|---|---|---|---|
| **Sleep** | 3.0 s | yes | 10 | Movement | The sleeping pose, breathing, with a `Snore` marker at 1.5 s. Animals lie down, the golems and the robot slump where they stand, the crawlers settle onto the ground, the ghost and the cloud sink low, and the drone powers down onto the ground. |
| **Wake** | 1.5 s | no | 30 | Action | Starts in Sleep's first pose. The head comes up first: open the eyes at **0.25 s** (marker `EyesOpen`). It gets up between 0.25 and 0.8 s, roars or threatens around **1.0 s** (marker `Roar`), and settles into its rest pose by 1.5 s. |
| **Run** | 0.4–1.0 s | yes | 30 | Movement | Its gait, in place, with `Step` markers on footfalls (`Land` for the hoppers). |

**Playing them.**

- **The order:** Sleep while it sleeps (show EyeShut), then Wake once (show EyeOpen at 0.25 s), then Run while it chases. Wake ends in the rest pose, and Run starts close to it. Run leans forward a little, so a 0.1–0.2 s blend into it is smoother if your player has one.
- **Speed:**
  - `RunSpeed` is how fast Run's feet are made for. If you move a guardian at V studs a second, play Run at V / RunSpeed speed, and its feet won't slide.
  - The animals run near a player's speed: the tiger at 15, the raptor at 16.
  - The golems are slow, at 6.5. The hoppers and floaters don't touch the ground much, so any speed looks right for them.
- **Hoppers and floaters:** Root stays on the ground the whole time. For a hopper, the clip lifts the body into the air (Body, or Body and Top for the slime). A floater hovers on its Body joint.
- **Moving bits:**
  - Neon's four rotors spin in Wake and Run.
  - Toy's wind-up key turns as it runs.
  - Clock's gear spins.
  - Cloud's Rain falls and its Bolt jumps down out of the cloud as it wakes. The Bolt stays tucked inside the cloud while it sleeps.
  - Void's slices twist and glitch, and its Bits orbit.
  - The scarecrow's crow pecks while its master sleeps, and flies up off the hat when it wakes.

**Previews:** `previews/guardians/`

- `guardians_grid_*.jpg`: all 18, awake
- `guardians_sleep_*.jpg`: all 18 with their eyes shut
- `clips_<AreaId>.jpg`: six frames each of Sleep, Wake and Run

---

## 4.3 The RootMonster in bricks (`BuildRootMonster.lua`)

| Path | What |
|---|---|
| `PotatoKit.RootMonster` | The RootMonster, 167 parts |
| `PotatoKit.RootAnimations.RootEmerge`, `RootChase`, `RootGrab`, `RootWither` | Its four clips (KeyframeSequences) |

The script replaces part 1's mesh RootMonster and its four sequences under the same names. It leaves everything else in `PotatoKit.RootAnimations` and the kit alone.

**The same rig, joint for joint.** Your code needs no changes.

- **Root:** the PrimaryPart, as before. Anchored and invisible, 4 × 0.4 × 4, with CanTouch on and its pivot on the ground in the middle. The front is -Z.
- **Motor6Ds:**
  - `Heap` joins Root → Heap.
  - Six chains of five: `Tentacle1Seg1` → … → `Tentacle1Seg5`, the same for `Tentacle2` … `Tentacle6`.
  - Each Motor6D carries its Part1's name and still lives in its Part0.
  - Every joint frame is exactly part 1's, and the build checks this.
- **The four clips** are baked by the same code as part 1's, so their keys are the same. The build checks the ground clearances:
  - RootEmerge starts with its highest brick 3.9 under the ground.
  - RootWither ends with it 4.8 under.
  - RootChase's claws dig at most 1.8 into the soil, as before.
- **Attachments and eyes:**
  - `Fx_Dirt` is on Root and `Fx_Eyes` on Heap.
  - A `Claw` attachment sits on each front root's tip (Tentacle1Seg5, Tentacle2Seg5).
  - The two `Eye` parts are Neon with `Flicker` = 0.1.
- **Animation:** an AnimationController with an Animator.
- **Flags:** everything but Root is unanchored and Massless, with CanCollide, CanTouch and CanQuery off.

**What it looks like now.**

- **The heap:** three stacked Folk Valley rounds of dug soil with lumps on its flanks. It carries a dark `EyeHole` with two glowing yellow diamond `Eye`s under a brow of soil. Nine dark `Clods` and seven grey `Pebbles` sit round its foot.
- **The roots:** each segment is a tapering eight-sided brick, made of a block and the same block turned 45° about the root (`Bark`). Every segment has a `Knob`. `Hairs` grow from the third segment on.
- **Colours and tips:** the roots are brown and paler towards the tips. The front roots end in a two-pronged `Fork`, and the others in a point (`Tip`).

| Clip | Length | Loop | Priority | Markers |
|---|---|---|---|---|
| `RootEmerge` | 1.0 s | no | Action | `Out` at 0.3 s |
| `RootChase` | 0.7 s | yes | Movement | none |
| `RootGrab` | 0.6 s | no | Action | `Hit` at 0.32 s |
| `RootWither` | 1.2 s | no | Action | none |

**Previews:** `previews/roots_bricks/`

- `turn_RootMonster.jpg`, `face_RootMonster.jpg`
- `clip_RootMonster_<Clip>.jpg`
- `RootMonster_clips.mp4`

---

## Sandy Dunes potatoes (`BuildPotatoesDunes.lua`)

| Path | Rarity | What |
|---|---|---|
| `PotatoKit.Potatoes.DustySpud` | Common | A sandy tan spud with a little red desert scarf knotted at its neck, tails flying, and dust spots |
| `PotatoKit.Potatoes.CactusTater` | Uncommon | A tall green cactus potato: dark grooves with white spines on them and a pink flower on its head |
| `PotatoKit.Potatoes.MummyMash` | Rare | Wrapped in old bandages, one of them over its left eye, so only its right eye peeks out; a loose end hanging |
| `PotatoKit.Potatoes.ScorpionSpud` | Epic | Orange-brown, a segmented scorpion tail arching up over its right shoulder with a stinger, and pincers for hands |
| `PotatoKit.Potatoes.PharaohFry` | Legendary | A tall golden fry in a pharaoh's blue headdress with a gold band, gold-striped lappets, a gold cobra and a little beard |
| `PotatoKit.Potatoes.SphinxSpud` | Mythic | Carved sandstone in a sphinx's headdress with carved stripes and cracks, glowing turquoise eyes (Neon) and lion's paws for feet |

**Same rig and rules as the Meadow Patch six.**

- **Rig:** Root, Body, Extra, the feature Motor6Ds and LegHeight.
- **Levels:** each feature shows at the level it always has.
- **Parts:** 42 to 45 each.
- **Clips:** the six in `PotatoKit.PotatoAnimations` (from `BuildPotatoesMeadow.lua`) play on these as they are. This script doesn't touch them.

A few features are dressed for their potato:

- ScorpionSpud's `HandL` and `HandR` are pincers: an invisible part at the wrist with two jaw bricks welded to it, as for any feature of several bricks.
- SphinxSpud's `FootL` and `FootR` are big sandstone lion's paws, and its `Eyes` glow turquoise.
- PharaohFry's and SphinxSpud's crowns have a turquoise Neon jewel.

**Previews:** `previews/potatoes/`

- `lineup_Dunes_L10.jpg`
- `levels_SphinxSpud.jpg`
- `turn_<Id>.jpg` for each of the six

---

## Mushroom Marsh potatoes (`BuildPotatoesMarsh.lua`)

| Path | Rarity | What |
|---|---|---|
| `PotatoKit.Potatoes.MossyTater` | Uncommon | A brown spud with green moss over its top half, creeping down its sides and brow, and a tiny leaf on its head |
| `PotatoKit.Potatoes.ToadstoolTot` | Rare | A short cream stalk under a big red toadstool cap with white dots |
| `PotatoKit.Potatoes.FroggySpud` | Rare | A bright green frog of a potato: big frog eyes up on top, a wide grin, a pale belly and webbed green feet |
| `PotatoKit.Potatoes.SwampThing` | Epic | Dark swamp green and grumpy, draped in bright vines, with a lily pad and its pink flower on its head and another pad on its shoulder |
| `PotatoKit.Potatoes.Glowshroom` | Legendary | A dark blue stalk under a glowing cyan mushroom cap (Neon), with glowing spots on its body |
| `PotatoKit.Potatoes.HydraTuber` | Mythic | Purple and green, with three heads: the big purple one in the middle and two little green ones on its shoulders |

The rig, rules and clips are the same as the Meadow Patch six. Each has 44 or 45 parts.

- FroggySpud's `Eyes` sit on the two bumps on top of its head, and its `Mouth` is a wide frog grin.
- HydraTuber's face (`Eyes`, `Mouth`) is on the middle head. The two side heads are part of its body (`Extra`).
- Glowshroom's cap and spots, and its crown jewel, are Neon.

**Previews:** `previews/potatoes/`

- `lineup_Marsh_L10.jpg`
- `levels_HydraTuber.jpg`
- `turn_<Id>.jpg` for each of the six

---

## Frost Fields potatoes (`BuildPotatoesFrost.lua`)

| Path | Rarity | What |
|---|---|---|
| `PotatoKit.Potatoes.SnowballSpud` | Uncommon | A round white snowball with a carrot nose, coal buttons and a twig on its head; twig arms with red mittens, blue boots |
| `PotatoKit.Potatoes.FrostbiteFry` | Rare | A tall icy-blue fry with icicles hanging over its eyes and frost specks, in a red woolly hat with a white pompom |
| `PotatoKit.Potatoes.PenguinPotato` | Epic | A black potato with a white front: an orange beak, flat black flippers, orange feet and a red bow tie |
| `PotatoKit.Potatoes.YetiYam` | Legendary | Shaggy white fur in tufts, a pale blue face and two little blue horns; big grey-blue feet |
| `PotatoKit.Potatoes.GlacierSpud` | Mythic | A light blue ice crystal: sharp facets, a faceted crown of ice and crystal shards on top, Neon light along its facets and a glint |
| `PotatoKit.Potatoes.AuroraTuber` | Secret | Dark teal like the polar night, glowing green and purple aurora ribbons swirling round it (Neon), a star glint |

The rig, rules and clips are the same as the Meadow Patch six. Each has 42 to 45 parts.

- PenguinPotato's `Mouth` is its beak, and its arms (`ArmL`, `ArmR`) are flat flippers.
- SnowballSpud's arms are twigs.

**Previews:** `previews/potatoes/`

- `lineup_Frost_L10.jpg`
- `levels_AuroraTuber.jpg`
- `turn_<Id>.jpg` for each of the six

---

## Lava Furrows potatoes (`BuildPotatoesLava.lua`)

| Path | Rarity | What |
|---|---|---|
| `PotatoKit.Potatoes.CharredChip` | Rare | A chunky square-cut chip burnt black, its cut end crusted with ash, orange embers glowing all over it and a wisp of smoke; wide white eyes in its sooty face and a glowing mouth |
| `PotatoKit.Potatoes.MagmaMash` | Epic | A lump of dark rock with rocks heaped on its head, split by glowing lava cracks that run on round its corners; its eyes and mouth glow like the lava |
| `PotatoKit.Potatoes.PepperPotato` | Epic | A tall, glossy red chilli narrowing to a point that curls away behind it, a star-shaped green calyx on top and its stem alight like a fuse |
| `PotatoKit.Potatoes.EmberImp` | Legendary | A red imp: two black horns, a pointed tail with a black spade tip, one brow cocked and a lopsided grin with two teeth |
| `PotatoKit.Potatoes.VolcanoSpud` | Mythic | A brown volcano: sloping flanks up to a crater full of lava, lava running down both flanks and bubbles of it jumping out of the top |
| `PotatoKit.Potatoes.InfernoTuber` | Secret | Made of blue flame: its whole body glows, a mane of blue and white flame leaps up behind its crown, flames lick up its sides and its eyes glow white |

The rig, rules and clips are the same as the Meadow Patch six. Each has 42 to 45 parts.

- **Neon parts:** the embers, cracks, lava, bubbles and flames. Also:
  - CharredChip's and MagmaMash's mouths
  - MagmaMash's and InfernoTuber's eyes
  - InfernoTuber's `Body` and all of its flames, so it glows with no light of yours
- **CharredChip's eyes:** white, with a dark `Pupil` each where the others have a `Glint`.
- **Above the crown at level 10:** PepperPotato's flame, VolcanoSpud's lava bubbles, EmberImp's horns and InfernoTuber's flames all stand clear of it.

**Previews:** `previews/potatoes/`

- `lineup_Lava_L10.jpg`
- `levels_InfernoTuber.jpg`
- `turn_<Id>.jpg` for each of the six

---

## Crystal Caverns potatoes (`BuildPotatoesCrystal.lua`)

| Path | Rarity | What |
|---|---|---|
| `PotatoKit.Potatoes.GeodeSpud` | Rare | A grey rock cracked open across the top: a jagged broken edge, a white lining and purple crystals bursting out, one of them glowing |
| `PotatoKit.Potatoes.AmethystTater` | Epic | A purple potato with a ridge of amethyst crystal spikes growing out of its back, the two tallest tipped with light |
| `PotatoKit.Potatoes.EmeraldFry` | Legendary | A tall emerald-cut emerald stood on end: corners cut off, facets in three greens round a raised table where its face is, star glints |
| `PotatoKit.Potatoes.DiamondSpud` | Mythic | Cut like a diamond: a narrow flat table on top, widest at its girdle, then tapering away underneath; white and cyan facets, star glints |
| `PotatoKit.Potatoes.PrismPotato` | Secret | Clear glass: a beam of white light shines in at one side and fans out of the other as a rainbow, and you can see it split through the glass |
| `PotatoKit.Potatoes.ObsidianOverlord` | Secret | Black volcanic glass with glowing purple cracks, glass shards jutting from its shoulders and back, a purple glare and a jagged obsidian crown |

The rig, rules and clips are the same as the Meadow Patch six. Each has 41 to 45 parts.

- **PrismPotato** is the kit's only see-through piece:
  - Its `Body` and the glass block on its top are Plastic at Transparency 0.4.
  - The light and the rainbow are Neon bars that run from outside it to a point inside it.
- **ObsidianOverlord's `Crown`** is its own jagged crown of black glass:
  - It has the usual `Band`, four `Point`s of different heights and a Neon purple `Jewel`.
  - It still shows only at level 10.
- **ObsidianOverlord's eyes:** Neon slanting `Eye`s with a dark `Pupil` each. Its `Mouth` is a thin Neon line.
- **GeodeSpud** wears its crown towards its back right, so the crystals stay in front of it.
- **EmeraldFry's `Body`** is turned to face forward, so the emerald cut shows from the front.

**Previews:** `previews/potatoes/`

- `lineup_Crystal_L10.jpg`
- `levels_ObsidianOverlord.jpg`
- `turn_<Id>.jpg` for each of the six

---

## Candy Crops potatoes (`BuildPotatoesCandy.lua`)

| Path | Rarity | What |
|---|---|---|
| `PotatoKit.Potatoes.GumdropSpud` | Epic | A green gumdrop: a squat dome, wide at the bottom, coated in sugar |
| `PotatoKit.Potatoes.LollipopTater` | Legendary | Pink with white facets and a swirl of candy on its head, holding up a big round swirl lollipop |
| `PotatoKit.Potatoes.CottonCandyMash` | Legendary | A puff of cotton candy, fluffy pink and blue all over, its face peeping out of the fluff |
| `PotatoKit.Potatoes.ChocolateChip` | Mythic | Dipped all over in milk chocolate: white chocolate drizzled across its top, dark chocolate chips and a wafer stick poking out of its head |
| `PotatoKit.Potatoes.JawbreakerSpud` | Secret | A round jawbreaker of rainbow layers, red at the bottom up to purple on top, with a shine |
| `PotatoKit.Potatoes.SugarKing` | Divine | Pastel pink, a peppermint cape striped red and white with a fluffy collar, a candy-cane sceptre and, at level 10, a crown of candy |

The rig, rules and clips are the same as the Meadow Patch six. Each has 43 to 45 parts.

- **Held items:** LollipopTater's lollipop (`Stick` and `Candy` bricks) and SugarKing's candy cane (`Cane` bricks) are held in the **left** hand. The right is free to wave.
  - Those bricks are children of `HandL`, welded to it, so they move with the hand in every clip.
  - Hand them the same treatment as a holder's descendants: when `HandL` hides below level 5, hide its BasePart descendants too.
  - These are the only one-brick features with children.
- **SugarKing's `Crown`:**
  - A crown of candy: a pink `Band`, three gumdrop `Point`s and a Neon peppermint `Jewel`.
  - It still shows only at level 10.
- **SugarKing's cape and collar** are part of his body (`Extra`), so he wears them at every level.

**Previews:** `previews/potatoes/`

- `lineup_Candy_L10.jpg`
- `levels_SugarKing.jpg`
- `turn_<Id>.jpg` for each of the six

---

## Cosmic Garden potatoes (`BuildPotatoesCosmic.lua`)

| Path | Rarity | What |
|---|---|---|
| `PotatoKit.Potatoes.MoonRockSpud` | Epic | A grey moon rock pitted with craters, a little red flag planted in its head beside its crown |
| `PotatoKit.Potatoes.CometTater` | Legendary | Icy blue with frost and ice on its head, a bright glowing tail streaming away behind it and out to one side |
| `PotatoKit.Potatoes.AlienSpud` | Mythic | Lime green, two antennae with glowing bobbles, and big black alien eyes with a big and a small glint |
| `PotatoKit.Potatoes.NebulaMash` | Secret | Deep purple space: glowing clouds of pink, lilac and blue gas, a galaxy's arm swirling across it and a sky of stars |
| `PotatoKit.Potatoes.BlackHoleTuber` | Divine | Pitch black, framed by a glowing orange ring of light with sparks caught in it; glowing eyes and mouth |
| `PotatoKit.Potatoes.GalacticOverlord` | Divine | Deep space blue, a ring like Saturn's tilted round its middle, small stars orbiting it and, at level 10, a bigger gold crown |

The rig, rules and clips are the same as the Meadow Patch six. Each has 43 to 45 parts.

- **The glow is Neon:** the comet's tail, the bobbles, the gas clouds, the galaxy's arm, the stars, and BlackHoleTuber's ring and sparks.
- **The dark three:**
  - NebulaMash and GalacticOverlord have white eyes with a dark `Pupil` each, and a glowing `Mouth`.
  - BlackHoleTuber's eyes and mouth glow.
- **The rings** are part of the body (`Extra`). They pass through the space the arms swing in, so the arms cross them in some clips.
- **GalacticOverlord's crown** is the usual gold `Crown`, 1.2 times the size.

**Previews:** `previews/potatoes/`

- `lineup_Cosmic_L10.jpg`
- `levels_GalacticOverlord.jpg`
- `turn_<Id>.jpg` for each of the six

---

## Jungle Ruins potatoes (`BuildPotatoesJungle.lua`)

**About the new 60.** Your order gave only their names, worst to best. I drew each from its name and its area.
- The rarities in these tables are my own labels: each kind's place in your list and its area's place along the corridor (Uncommon to Mythic here, rising to Divine by Spud Olympus).
- They show only in the previews. No model carries a rarity, so use yours.

| Path | Rarity | What |
|---|---|---|
| `PotatoKit.Potatoes.VineSpud` | Uncommon | A brown potato wrapped in green jungle vines, leaves sprouting from them |
| `PotatoKit.Potatoes.BananaTater` | Rare | A yellow banana peeled at the top: the cream fruit showing, three strips of peel flopping open round it, brown spots |
| `PotatoKit.Potatoes.ParrotPotato` | Rare | A red parrot: white patches round its eyes, a hooked beak, a crest of red, yellow and blue feathers, blue wings tipped yellow, a long tail |
| `PotatoKit.Potatoes.MonkeyMash` | Epic | A brown monkey: a tan face, big round ears with tan middles and a curly tail |
| `PotatoKit.Potatoes.TikiTuber` | Legendary | A carved wooden tiki: a heavy brow over wide white eyes, a broad nose, a big toothy grin, painted bands and a headdress of palm fronds |
| `PotatoKit.Potatoes.GoldenIdol` | Mythic | Solid gold: a carved headband set with a glowing red gem, gold discs in its ears, glowing green gem eyes and glints |

The rig, rules and clips are the same as the Meadow Patch six. Each has 42 to 45 parts.

- **ParrotPotato's `Mouth`** is its beak (three `Beak` bricks).
- **TikiTuber's mouth and eyes:** its `Mouth` has `Mouth` and `Teeth` plates. Its eyes are white with a dark `Pupil` each.
- **GoldenIdol's eyes** glow (Neon).

**Previews:** `previews/potatoes/`

- `lineup_Jungle_L10.jpg`
- `levels_GoldenIdol.jpg`
- `turn_<Id>.jpg` for each of the six

---

## Coral Cove potatoes (`BuildPotatoesReef.lua`)

| Path | Rarity | What |
|---|---|---|
| `PotatoKit.Potatoes.SandySpud` | Uncommon | A sandy beach: speckled with sand, a pink starfish on its front, a little spiral shell on its head |
| `PotatoKit.Potatoes.BubbleTater` | Rare | Aqua, blowing bubbles: see-through bubbles float round it, one just leaving its pursed mouth |
| `PotatoKit.Potatoes.ClamChip` | Epic | Pink, a big scallop shell standing up behind its head like a crest, white ridges running out from it; at level 10 its crown's jewel is a pearl |
| `PotatoKit.Potatoes.PufferPotato` | Epic | A pufferfish puffed up round: yellow with spines sticking out all over and a little pout |
| `PotatoKit.Potatoes.CaptainSpud` | Legendary | A pirate captain: a black tricorn with a white skull, a patch over one eye, a bushy ginger beard, a red coat's sleeves and a silver hook for a left hand |
| `PotatoKit.Potatoes.KrakenTuber` | Mythic | A deep red-purple kraken with great tentacles curling out from under it, paler at their tips |

The rig, rules and clips are the same as the Meadow Patch six. Each has 43 to 45 parts.

- **BubbleTater's bubbles** are Plastic at Transparency 0.45, like PrismPotato's glass.
- **CaptainSpud's hook** (two `Hook` bricks) is held in the left hand like the Candy Crops' lollipop:
  - The bricks are children of `HandL`, welded to it.
  - Hide them with it below level 5.
- **CaptainSpud's tricorn, eye patch and beard** are part of his body (`Extra`), so he wears them at every level. His crown sits on top of the hat.

**Previews:** `previews/potatoes/`

- `lineup_Reef_L10.jpg`
- `levels_KrakenTuber.jpg`
- `turn_<Id>.jpg` for each of the six

---

## Haunted Hollow potatoes (`BuildPotatoesHaunt.lua`)

| Path | Rarity | What |
|---|---|---|
| `PotatoKit.Potatoes.PumpkinSpud` | Rare | A jack-o'-lantern: ribbed orange, a curly green stem and a leaf, carved triangle eyes and a jagged grin glowing from inside |
| `PotatoKit.Potatoes.GhostTater` | Rare | A sheet ghost: white and a little see-through, a wavy hem, big dark eyes and an "oo" mouth, a wisp trailing behind |
| `PotatoKit.Potatoes.BatSpud` | Epic | A bat: dusky purple, big wings spread behind it, pointed ears, glowing yellow eyes and two little fangs |
| `PotatoKit.Potatoes.WitchFry` | Legendary | A tall green witch: a tall black pointed hat with a crooked tip and a purple band, straggly purple hair, a long nose with a wart |
| `PotatoKit.Potatoes.FrankenSpud` | Mythic | Frankenstein's monster: grey-green, a flat top of black hair with a ragged fringe, bolts in its neck and a stitched scar down one cheek |
| `PotatoKit.Potatoes.ReaperTuber` | Secret | A grim reaper in a black hooded cloak, eyes glowing out of the hood's shadow, a ghostly glow about it and a scythe in its left hand |

The rig, rules and clips are the same as the Meadow Patch six. Each has 39 to 45 parts.

- **GhostTater's sheet** (its `Body`, the other body bricks and the hem) is at Transparency 0.2.
- **ReaperTuber's scythe** (`Scythe` bricks) is held in the left hand: children of `HandL`, welded to it. Hide them with it below level 5.
- **PumpkinSpud's face glows.** Its `Eyes` are Neon triangles, each with a shadow plate named `Glint` under it. Its `Mouth` is Neon with two `Tooth` plates.
- **BatSpud's `Mouth`** has two white `Fang`s.
- **WitchFry's crown** sits on her hat brim, round the hat like a band.
- **The glowing eyes:** BatSpud's and ReaperTuber's eyes glow (Neon), and so does ReaperTuber's mouth.

**Previews:** `previews/potatoes/`

- `lineup_Haunt_L10.jpg`
- `levels_ReaperTuber.jpg`
- `turn_<Id>.jpg` for each of the six

---

## Dino Valley potatoes (`BuildPotatoesDino.lua`)

| Path | Rarity | What |
|---|---|---|
| `PotatoKit.Potatoes.FossilFry` | Epic | A tall lump of fossil stone: a dinosaur bone stuck in its head, an ammonite's coil and a little bone set in its front |
| `PotatoKit.Potatoes.DinoEggSpud` | Epic | A speckled dinosaur egg, round-topped, cracked down one side, a piece of shell perched on top like a cap |
| `PotatoKit.Potatoes.RaptorTater` | Legendary | A velociraptor: green with dark stripes down its back, yellow slit eyes, a toothy grin, a crest of red quills and a long stiff tail |
| `PotatoKit.Potatoes.TriceraTot` | Mythic | A triceratops: teal, a great orange frill fanned up behind its head with knobs round its edge, two long horns and a little one on its nose |
| `PotatoKit.Potatoes.PteroSpud` | Secret | A pterodactyl: rusty orange, great pointed wings spread behind it, a long crest sweeping back from its head and a long pointed beak |
| `PotatoKit.Potatoes.RexOverlord` | Secret | Tyrannosaurus rex: big and dark green, a great jaw of teeth, tiny arms, spikes down its back, a heavy tail and a bigger gold crown |

The rig, rules and clips are the same as the Meadow Patch six. Each has 42 to 45 parts.

- **Reptile eyes:** RaptorTater's and RexOverlord's `Eyes` are yellow or orange with a dark slit `Pupil`.
- **Toothy mouths:** RaptorTater's and RexOverlord's `Mouth` carry white `Tooth` plates.
- **PteroSpud's `Mouth`** is its beak (two `Beak` bricks).
- **RexOverlord's arms** are the usual `ArmL`, `ArmR`, `HandL` and `HandR`, only tiny.
- **RexOverlord's crown** is the usual gold `Crown`, 1.2 times the size.

**Previews:** `previews/potatoes/`

- `lineup_Dino_L10.jpg`
- `levels_RexOverlord.jpg`
- `turn_<Id>.jpg` for each of the six

---

## Toy Town potatoes (`BuildPotatoesToy.lua`)

| Path | Rarity | What |
|---|---|---|
| `PotatoKit.Potatoes.BlockSpud` | Epic | A toy building brick: square and bright red, four big studs on top |
| `PotatoKit.Potatoes.TeddyTater` | Legendary | A teddy bear: soft brown, round ears with tan middles, a tan muzzle with a black nose and a red bow tie |
| `PotatoKit.Potatoes.DuckySpud` | Legendary | A rubber duck: bright yellow, a flat orange beak, a curl of a tuft, a little tail cocked up behind and bath bubbles |
| `PotatoKit.Potatoes.RoboSpud` | Mythic | A tin toy robot: riveted silver, glowing square eyes, a grille for a mouth, a chest screen with a glowing heartbeat, side bolts and an antenna with a red light |
| `PotatoKit.Potatoes.JackSpud` | Secret | A jack-in-the-box's jester: purple and yellow, a three-pointed jester's hat with gold bells, a red clown's nose and harlequin diamonds |
| `PotatoKit.Potatoes.GeneralTater` | Secret | A toy soldier general: a red coat with a white cross-belt, gold buttons, gold epaulettes and a medal, a tall black busby with a gold badge and a red plume, a black moustache |

The rig, rules and clips are the same as the Meadow Patch six. Each has 40 to 45 parts.

- **DuckySpud's `Mouth`** is its beak (two `Beak` bricks). Its bubbles are see-through (Transparency 0.45).
- **RoboSpud's face:**
  - Its `Eyes` glow (Neon).
  - Its `Mouth` is a grille: a dark plate with three `Grille` bars.
- **Hats and crowns:**
  - JackSpud's hat and GeneralTater's busby are part of the body (`Extra`), so they wear them at every level.
  - The crown sits on top of the hat.

**Previews:** `previews/potatoes/`

- `lineup_Toy_L10.jpg`
- `levels_GeneralTater.jpg`
- `turn_<Id>.jpg` for each of the six

---

## Clockwork Yard potatoes (`BuildPotatoesClock.lua`)

| Path | Rarity | What |
|---|---|---|
| `PotatoKit.Potatoes.RustyBolt` | Epic | A rusty old bolt: a grey hex head on top, the thread's ridges round it and patches of orange rust |
| `PotatoKit.Potatoes.GearTater` | Legendary | Brass clockwork: a cog set in its front and a big one turning behind its head |
| `PotatoKit.Potatoes.SteamFry` | Mythic | A tall copper steam engine: brass goggles pushed up on its forehead, a smokestack puffing steam and a brass pipe down its side |
| `PotatoKit.Potatoes.TickTockSpud` | Mythic | An alarm clock: bright red, its face on a white clock dial with ticks at twelve and six, two gold bells on top and the hammer between them |
| `PotatoKit.Potatoes.TeslaTuber` | Secret | A Tesla coil: copper wound with darker coils, a silver sphere on its head, lightning crackling from it and glowing electric-blue eyes |
| `PotatoKit.Potatoes.ChronoKing` | Divine | The king of time: gold, a royal purple cape with an ermine collar, a cog turning beside its head, an hourglass in its left hand and a bigger crown |

The rig, rules and clips are the same as the Meadow Patch six. Each has 42 to 45 parts.

- **ChronoKing's hourglass** (`Hourglass` bricks) is held in the left hand: children of `HandL`, welded to it.
  - Hide them with it below level 5.
  - Its top bulb is see-through (Transparency 0.4).
- **TickTockSpud's face** sits a little further forward than usual (Z = -1.5), on its clock dial.
- **TeslaTuber's eyes and lightning** glow (Neon).

**Previews:** `previews/potatoes/`

- `lineup_Clock_L10.jpg`
- `levels_ChronoKing.jpg`
- `turn_<Id>.jpg` for each of the six

---

## Neon City potatoes (`BuildPotatoesNeon.lua`)

| Path | Rarity | What |
|---|---|---|
| `PotatoKit.Potatoes.PixelSpud` | Epic | An 8-bit potato: square-cut magenta like an old game's sprite, highlight pixels in cyan and yellow, loose glowing pixels floating round it |
| `PotatoKit.Potatoes.GlowTater` | Legendary | A glow stick: tall and glowing lime green all over, a dark cap on top with a loop to hang it by, sparks of light |
| `PotatoKit.Potatoes.DJSpud` | Mythic | A DJ: purple, big headphones over its head, dark shades with a pink shine and a glowing music note in the air |
| `PotatoKit.Potatoes.HoverFry` | Secret | A tall chrome potato of the future: glowing cyan stripes, a see-through visor over its eyes and a jetpack with glowing jets |
| `PotatoKit.Potatoes.LaserTuber` | Secret | A laser show: dark with glowing pink edges, red glowing eyes and a laser on its head throwing red, green, cyan and pink beams into the sky |
| `PotatoKit.Potatoes.CyberOverlord` | Divine | Part potato, part machine: dark chrome with glowing circuit traces, a steel plate over one side of its face with a red cyber eye, chrome shoulder pads and a bigger crown |

The rig, rules and clips are the same as the Meadow Patch six. Each has 41 to 45 parts.

- **GlowTater's `Body`** and the rest of its body are Neon.
- **HoverFry's visor** is see-through (Transparency 0.35).
- **DJSpud's shades** are part of its body (`Extra`), so it wears them at every level. Its eyes blink behind them.
- **CyberOverlord's eyes:** one white `Eye` with a `Pupil`, and one Neon red `Eye` with a glowing `Glint`. Its `Mouth` is a thin Neon line.

**Previews:** `previews/potatoes/`

- `lineup_Neon_L10.jpg`
- `levels_CyberOverlord.jpg`
- `turn_<Id>.jpg` for each of the six

---

## Cloud Kingdom potatoes (`BuildPotatoesCloud.lua`)

| Path | Rarity | What |
|---|---|---|
| `PotatoKit.Potatoes.CloudPuff` | Epic | A little white cloud: puff upon soft puff, a face peeping out of the middle |
| `PotatoKit.Potatoes.RainySpud` | Legendary | Dressed for the rain: a yellow raincoat with its hood up, blue wellies, a red umbrella held up in its left hand and raindrops falling |
| `PotatoKit.Potatoes.SunnyTater` | Mythic | A little sun: warm yellow, glowing rays fanned round its head and shoulders |
| `PotatoKit.Potatoes.RainbowFry` | Secret | A tall fry under its own rainbow: a glowing arc of seven colours over its head, a little cloud at each end |
| `PotatoKit.Potatoes.ThunderTuber` | Secret | A thundercloud: dark storm grey, piled with dark cloud, glowing yellow eyes and bolts of lightning striking down beside it |
| `PotatoKit.Potatoes.SeraphSpud` | Divine | An angel: soft white, a glowing gold halo over its head and white feathered wings |

The rig, rules and clips are the same as the Meadow Patch six. Each has 42 to 45 parts.

- **RainySpud's umbrella** (`Umbrella` bricks) is held in the left hand: children of `HandL`, welded to it. Hide them with it below level 5.
- **Glowing (Neon):** SunnyTater's rays, RainbowFry's rainbow, ThunderTuber's eyes and lightning, and SeraphSpud's halo.
- **SeraphSpud's halo** is part of its body (`Extra`), so it wears it at every level. It floats above the crown at level 10.

**Previews:** `previews/potatoes/`

- `lineup_Cloud_L10.jpg`
- `levels_SeraphSpud.jpg`
- `turn_<Id>.jpg` for each of the six

---

## Glitch Void potatoes (`BuildPotatoesVoid.lua`)

| Path | Rarity | What |
|---|---|---|
| `PotatoKit.Potatoes.StaticSpud` | Legendary | TV static: speckled grey, black and white noise across it, an old set's rabbit-ear aerial on its head |
| `PotatoKit.Potatoes.ErrorTater` | Mythic | An error message: a pale window with a blue title bar on top, a red X to close it and a yellow warning sign on its front |
| `PotatoKit.Potatoes.ShadowFry` | Secret | A shadow standing up on its own: tall, dark and a little see-through, wisps of shadow curling off it, only its glowing white eyes and mouth showing |
| `PotatoKit.Potatoes.GlitchSpud` | Secret | A glitch: slices of it slipped sideways, red and cyan fringes down its edges like a bad signal, stray glowing pixels floating off it |
| `PotatoKit.Potatoes.VoidWalker` | Divine | A walker between worlds: void black with stars inside it, glowing purple edges, a portal ring glowing behind it and glowing eyes |
| `PotatoKit.Potatoes.KingNull` | Divine | The king of nothing: void black, a glowing white zero on its chest, a cape lined with glowing purple, black cubes orbiting it, glowing white eyes and a jagged black crown |

The rig, rules and clips are the same as the Meadow Patch six. Each has 38 to 45 parts.

- **ShadowFry's body** is at Transparency 0.25.
- **KingNull's `Crown`** is a jagged crown like ObsidianOverlord's, in black with a glowing white `Jewel`. It shows at level 10.
- **The glowing faces:** ShadowFry's, VoidWalker's and KingNull's eyes and mouths glow (Neon).

**Previews:** `previews/potatoes/`

- `lineup_Void_L10.jpg`
- `levels_KingNull.jpg`
- `turn_<Id>.jpg` for each of the six

## Spud Olympus potatoes (`BuildPotatoesOlympus.lua`)

| Path | Rarity | What |
|---|---|---|
| `PotatoKit.Potatoes.MarbleSpud` | Legendary | A statue in white marble: grey veins through the stone and a gold circlet with a Greek key round its head |
| `PotatoKit.Potatoes.LaurelTater` | Mythic | A Greek champion: a wreath of laurel leaves round its head and the torch held high, its flame glowing |
| `PotatoKit.Potatoes.HeroFry` | Secret | A hero of old: a bronze helmet with cheek guards and a tall red horsehair crest, a red cape and a round bronze shield |
| `PotatoKit.Potatoes.PegasusSpud` | Divine | Pegasus: white, great feathered wings tipped gold, a pale blue mane down the back of its head and gold hooves |
| `PotatoKit.Potatoes.PoseidonTuber` | Divine | The god of the sea: sea green, dark teal hair, white brows, a beard and moustache of surf and a golden trident |
| `PotatoKit.Potatoes.ZeusSpud` | Divine | The king of the gods: white hair, bushy white brows, a great white beard and moustache, gold sandals and a glowing thunderbolt |

The rig, rules and clips are the same as the Meadow Patch six. Each has 44 or 45 parts.

- **The held things are in the left hand:** LaurelTater's torch (`Torch` bricks), HeroFry's shield (`Shield` bricks), PoseidonTuber's trident (`Trident` bricks) and ZeusSpud's thunderbolt (`Thunderbolt` bricks).
  - They are children of `HandL`, welded to it, so they move with the hand in every clip.
  - Hide them with it below level 5.
- **The torch flame and the thunderbolt glow** (Neon).
- **On the body:** the wreath, HeroFry's helmet, crest and cape, Pegasus's wings and mane, and the gods' hair, beards and moustaches are body `Extra` bricks. They show at every level.

**Previews:** `previews/potatoes/`

- `lineup_Olympus_L10.jpg`
- `levels_ZeusSpud.jpg`
- `turn_<Id>.jpg` for each of the six

---

## Heroes and props of the eighteen areas

Each area gets one script, `BuildScenery<Area>.lua`. It builds:

- `PotatoKit.Heroes.<AreaId>`: the hero, one Model.
- `PotatoKit.Props.<AreaId>.<Name>`: the props, one Model each.

**The hero**

- It stands against a wall of the corridor, front (-Z) to the lane. Its footprint is at most 46 along X and 30 deep, and its pivot is the middle of that footprint on the ground.
- The parts a player can stand on are solid: CanCollide and CanQuery on, CanTouch off.
- Everything else is decoration: anchored, with CanCollide, CanTouch and CanQuery off.
- No part under 2.5 studs casts a shadow.

**The props**

- Each is 10 to 40 parts of decoration. Its pivot is the middle of its footprint on the ground, front -Z.
- Each carries the scatter attributes: `Count`, `ScaleMin`, `ScaleMax`, `Band` and `Solid`.
- `Solid = true` marks the props players should bump into. Their parts are built non-colliding like all decoration, so turn CanCollide on for the big ones when you scatter them.
- `Band = Any` props are small clutter you may scatter into the running lane, so **none of them is Solid**. Thirteen props of the ten areas sent before were both; they are `Band = Side` now. Only that attribute changed in those scripts: `Clock.GiantSpring`, `Cloud`'s cloud puffs, `Dino`'s amber rock, `Haunt.Coffin`, `Jungle`'s rocks, `Olympus.Amphora`, `Reef`'s treasure chest and giant clam, `Toy`'s blocks, duck and car, and `Void`'s TV.

**Attributes on parts**

- `Flicker` (how much it flickers) on Neon fires, gems and lamps.
- `NightLamp = true` on everything to light at night.
- `Spin` (degrees a second about the part's own Y). Every part of a spinning thing is centred on its axle with its own Y along it, so spinning each part about its own Y turns the whole thing.

**Previews.** In the hero pictures, the yellow and blue figure is a 5-stud player and the potato is Spud at level 10. They are there for scale and are not in the scripts.

### Meadow Patch (`BuildSceneryMeadow.lua`)

**`PotatoKit.Heroes.Meadow`**: 219 parts, 40.6 wide, 35.9 tall, 25.3 deep.

- **The windmill:** an eight-sided tower of upright planks in two reds, leaning in as it rises, with white corner trim, on a stone plinth.
  - It has a wooden balcony with a white railing, a door with a white brace, and a lantern hanging under the balcony.
  - It has a lit window with a flower box, small side windows, and a grey stepped cap with a potato weathervane.
- **The sails:** four sails of white and cream cloth in red frames on dark beams, round a hub facing the lane.
  - Every sail part, the hub and the windshaft carry **`Spin` = 20** and are centred on one axle, so turning each part about its own Y turns the whole sail.
  - Their lowest point (10.7) clears the railing.
- **The scarecrow:** a potato scarecrow stands in a potato patch in front of the windmill. It has a stitched happy face, straw hair, a straw hat with a red band and a patched blue shirt. Its arms are out along a crossbar, with a crow on one arm.
- **Round its foot:** a rolled hay bale, a square bale with a pitchfork, potato sacks, and stepping stones to the door.
- **Solid (37 parts):** the plinth, the door step, the tower walls, the balcony deck and the potato patch.
- **Glow:** NightLamp on the lit window; Flicker and NightLamp on the hanging lantern.

| `PotatoKit.Props.Meadow.<Name>` | Parts | W × H × D | Count | Scale | Band | Solid | What |
|---|---|---|---|---|---|---|---|
| `HayRolls` | 21 | 10.0 × 8.2 × 6.2 | 5 | 0.9–1.2 | Edge | yes | Three stacked rolled bales with spiral ends and loose straw |
| `PicketFence` | 38 | 12.1 × 4.1 × 2.1 | 6 | 0.9–1.1 | Edge | yes | A white picket fence with a gate swung open, and flowers |
| `PotatoCart` | 33 | 7.9 × 5.1 × 5.0 | 3 | 0.9–1.2 | Side | yes | A two-wheeled hand cart heaped with potatoes |
| `Beehive` | 27 | 5.7 × 9.1 × 5.4 | 4 | 0.9–1.2 | Side | no | A straw beehive on a stand with a honey pot and three bees |
| `Sunflowers` | 27 | 8.9 × 10.2 × 2.6 | 8 | 0.85–1.25 | Side | no | Three tall sunflowers facing the lane |
| `Signpost` | 22 | 8.2 × 10.1 × 3.5 | 3 | 0.9–1.15 | Side | no | A wooden post with three arrows and a bluebird on top |
| `Mailbox` | 19 | 2.5 × 6.6 × 3.4 | 3 | 0.9–1.15 | Side | no | A red round-topped mailbox with its flag up, a letter and flowers |
| `PotatoSacks` | 32 | 6.3 × 3.9 × 5.6 | 7 | 0.8–1.2 | Any | no | Two tied sacks and an open heaped one, with spilled potatoes |

These stand beside Folk Valley's own apple trees, flowers, bushes, rocks, pond and picnic table, which the map uses too.

**Previews:** `previews/scenery/`

- `hero_Meadow.jpg`: from the lane
- `hero_Meadow_corner.jpg`: from the corner
- `props_Meadow.jpg`: the props in a row
- `props_Meadow_top.jpg`: the props from above

### Sandy Dunes (`BuildSceneryDunes.lua`)

**`PotatoKit.Heroes.Dunes`**: 186 parts, 43.8 wide, 36.9 tall, 28.8 deep.

- **The pyramid:** eight sandstone tiers, each 4 high, in three shades getting lighter upwards.
  - Each tier has a cream trim and a few stones standing proud of its faces.
  - The back is nearly straight up, against the wall.
  - A gold stepped capstone sits on top, with a gold ankh on the top tier.
- **The potato pharaoh:** a giant golden potato face set into the lane face of the pyramid. It has kohl-lined eyes, a smile, pink cheeks and freckles.
  - It wears a blue-and-gold striped headdress with a gold band and a small cobra, striped flaps falling beside the face, a striped beard and a broad collar.
- **At its foot:** a gateway with hieroglyph panels and gold tops on its posts, and a winged sun above. The doorway is dark inside, and a little mummy potato peeks out.
  - Round the gateway: more hieroglyph panels, torches either side, painted pots, sand drifts and fallen stones.
- **Solid (26 parts):** the tiers and their trims, the gateway and its step, the head's body blocks and the lower capstone.
- **Glow:** the two torch flames have Flicker and NightLamp.

| `PotatoKit.Props.Dunes.<Name>` | Parts | W × H × D | Count | Scale | Band | Solid | What |
|---|---|---|---|---|---|---|---|
| `Obelisk` | 13 | 3.8 × 15.2 × 3.8 | 4 | 0.9–1.2 | Edge | yes | A rose-granite obelisk on a stepped base, with a gold tip and hieroglyphs |
| `MarketStall` | 36 | 6.6 × 6.4 × 3.8 | 3 | 0.9–1.1 | Edge | yes | A striped awning over a counter with potatoes, a pot and a lantern (Flicker, NightLamp) |
| `Saguaro` | 21 | 6.2 × 10.4 × 3.8 | 7 | 0.85–1.3 | Side | yes | A chunky cactus with two arms, pink flowers and spines |
| `OasisPool` | 24 | 8.2 × 3.7 × 8.2 | 3 | 0.9–1.2 | Side | no | A round pool with a stone rim, reeds with cattails and a lily pad |
| `Scarab` | 28 | 8.8 × 4.4 × 4.2 | 3 | 0.9–1.2 | Side | yes | A teal scarab on a plinth, pushing a potato with a face |
| `Camel` | 25 | 8.4 × 8.0 × 2.6 | 3 | 0.9–1.15 | Side | yes | A camel with a round hump and a saddle cloth |
| `ClayPots` | 33 | 6.6 × 3.5 × 4.2 | 7 | 0.8–1.2 | Any | no | Three painted clay pots, one tipped over, and shards |
| `Scorpion` | 22 | 7.3 × 4.3 × 3.6 | 5 | 0.9–1.4 | Any | no | An orange scorpion with its tail raised |

These stand beside Folk Valley's own mesas, palms, cacti, rocks, bones, tumbleweed and crates, which the map uses too.

**Previews:** `previews/scenery/`

- `hero_Dunes.jpg`: from the lane
- `hero_Dunes_corner.jpg`: from the corner
- `props_Dunes.jpg`: the props in a row
- `props_Dunes_top.jpg`: the props from above

### Mushroom Marsh (`BuildSceneryMarsh.lua`)

**`PotatoKit.Heroes.Marsh`**: 216 parts, 41.9 wide, 38.0 tall, 29.8 deep.

- **The toadstool house:** the fat cream stem is the house, three eight-sided drums getting lighter upwards.
  - The red cap steps up in three eight-sided layers to a lid. It has round white dots on its faces and ledges, and pink gills underneath.
- **On its front:**
  - a round plank door in a dark frame, on a plank porch with three stone steps;
  - a railed balcony on two posts over the porch, with a lantern hanging under it;
  - three round glowing windows;
  - a crooked stone chimney with smoke.
- **The potato:** a waving potato in a little toadstool hat stands at the door.
- **Round its foot:** red, purple and blue toadstools, two spore lamps by the steps, moss and grass, and a murky pond with lily pads, a pink bud and cattails.
- **Solid (26 parts):** the stem drums, the porch, the steps and the balcony deck.
- **Glow:**
  - **NightLamp:** the window panes, the door's little window and the spots on the tall blue toadstool.
  - **Flicker and NightLamp:** the lantern and the spore-lamp pods.

| `PotatoKit.Props.Marsh.<Name>` | Parts | W × H × D | Count | Scale | Band | Solid | What |
|---|---|---|---|---|---|---|---|
| `GiantToadstool` | 36 | 10.7 × 15.1 × 10.3 | 5 | 0.85–1.25 | Side | no | A tall red toadstool to run under: a turned stem with a ring, and a tilted dotted cap with gills |
| `PurpleShroom` | 22 | 12.6 × 14.9 × 12.1 | 4 | 0.85–1.2 | Side | no | A bent stem under a wide flat purple cap with lilac spots and a glowing underside (NightLamp), with a baby shroom |
| `BlueShrooms` | 29 | 11.0 × 11.9 × 7.1 | 5 | 0.85–1.25 | Side | no | Two blue mushrooms leaning apart, with glowing cyan spots (Flicker, NightLamp) |
| `FairyRing` | 24 | 8.0 × 2.6 × 8.1 | 6 | 0.8–1.3 | Any | no | Nine tiny mushrooms of mixed colours in a ring on grass, with two sparkles (Flicker, NightLamp) |
| `LilyPads` | 23 | 8.9 × 2.7 × 7.1 | 6 | 0.8–1.3 | Any | no | A patch of murky water with four pads, a pink lotus, a bud, reeds and a dragonfly |
| `Cattails` | 18 | 3.9 × 7.0 × 3.8 | 8 | 0.8–1.3 | Side | no | Reeds with brown cattail heads and long blades on a mossy tuft |
| `MossyLog` | 25 | 10.3 × 4.7 × 5.3 | 4 | 0.9–1.2 | Side | yes | A hollow log with moss on top, bracket fungi, blue mushrooms and a broken branch |
| `SporeLamp` | 18 | 4.9 × 8.6 × 3.6 | 6 | 0.9–1.2 | Side | no | A shepherd's-crook stalk with glowing spore pods hanging from it (Flicker, NightLamp) |
| `FrogStatue` | 31 | 5.4 × 6.0 × 5.6 | 3 | 0.9–1.2 | Side | yes | A jade frog in a gold crown with a glowing gem (NightLamp), on a stump with roots |
| `HangingMoss` | 22 | 10.1 × 10.7 × 3.6 | 4 | 0.9–1.2 | Edge | no | A crooked dead tree arching over, with strands of moss hanging from it |

**Previews:** `previews/scenery/`

- `hero_Marsh.jpg`: from the lane
- `hero_Marsh_corner.jpg`: from the corner
- `props_Marsh.jpg`: the props in a row
- `props_Marsh_top.jpg`: the props from above

### Jungle Ruins (`BuildSceneryJungle.lua`)

**`PotatoKit.Heroes.Jungle`**: 211 parts, 44.4 wide, 28.5 tall, 29.5 deep.

- **The temple:** four stone tiers getting lighter upwards, with carved potato faces on the first two.
- **The stairs:** a staircase of 16 one-stud steps climbs the front from the lane to the top platform, between two ramps.
- **The shrine:** on the platform, with a dark doorway and a roof comb.
- **The idol:** in front of the shrine sits a gold potato with a feather crown and a glowing emerald set in its gold band. It is on a pedestal, with gold spilled at its feet.
- **The braziers:** four, with fires: two at the foot of the stairs and two beside the idol.
- **The jungle:** moss, vines, bushes and ferns all over it, and palms growing out of the back corners.
- **Solid (39 parts):** the tiers, the steps and ramps, the shrine and its roof, the pedestal and the brazier posts. Players can climb to the idol and walk round the terraces.
- **Glow:** the four `Flame` fires have Flicker 0.2 and NightLamp; the `Emerald` has Flicker 0.12 and NightLamp.

| `PotatoKit.Props.Jungle.<Name>` | Parts | W × H × D | Count | Scale | Band | Solid | What |
|---|---|---|---|---|---|---|---|
| `JunglePalm` | 20 | 11.9 × 15.6 × 12.3 | 8 | 0.85–1.25 | Side | yes | A tall palm bending over: seven fronds, coconuts, grass at its foot |
| `BananaPlant` | 16 | 9.0 × 9.9 × 7.8 | 6 | 0.9–1.3 | Side | no | A thick stalk, seven big paddle leaves, a bunch of bananas and a purple bud hanging below |
| `BigFern` | 14 | 5.8 × 2.7 × 5.5 | 12 | 0.8–1.4 | Any | no | Two layers of fronds |
| `RuinPillar` | 15 | 7.4 × 7.8 × 4.5 | 5 | 0.9–1.3 | Side | yes | A broken stone column, its drums knocked askew, the capital fallen beside it; moss and vines |
| `StoneHead` | 17 | 6.7 × 7.0 × 6.7 | 3 | 0.9–1.2 | Edge | yes | A giant carved potato head in a stone helmet, mossy, a vine down its face |
| `TikiTotem` | 31 | 3.5 × 10.3 × 3.5 | 4 | 0.9–1.2 | Side | yes | Three carved wooden faces stacked, a fire on top (`Flame`: Flicker, NightLamp) |
| `MossyRocks` | 14 | 8.1 × 3.3 × 5.7 | 6 | 0.8–1.3 | Side | yes | Three mossy rocks and a tuft of grass |
| `FallenLog` | 17 | 8.4 × 4.1 × 4.8 | 4 | 0.9–1.2 | Side | yes | An eight-sided log with cut ends, a broken branch, red mushrooms, moss and a fern |
| `JungleFlower` | 16 | 5.6 × 1.3 × 5.6 | 8 | 0.8–1.3 | Any | no | A giant red flower with white spots, flat on the ground on four leaves |

**Previews:** `previews/scenery/`

- `hero_Jungle.jpg`: from the lane
- `hero_Jungle_corner.jpg`: from the corner
- `props_Jungle.jpg`: the props in a row
- `props_Jungle_top.jpg`: the props from above

### Coral Cove (`BuildSceneryReef.lua`)

**`PotatoKit.Heroes.Reef`**: 200 parts, 44.4 wide, 26.7 tall, 25.0 deep.

- **The ship:** a pirate ship run aground on a sand bank, listing towards the lane so its deck shows, bow up.
- **The hull:** planked in two browns, with brass portholes, three cannons run out, a hole stove in near the stern, barnacles and weed.
- **The stern castle:** lit windows and a lantern on a post.
- **The masts:** the main mast has a crow's nest, a torn sail and the Jolly Roger, and its top is snapped. The foremast is broken and lies across the deck.
- **The gangplank:** it runs from the rail down to the sand, so players can walk aboard.
- **The captain:** a potato on deck in a pirate hat with a skull, an eyepatch, a cutlass and a parrot on his shoulder.
- **On the sand:** an open treasure chest with two glowing gems, coral, kelp, starfish, shells and barrels.
- **Solid (27 parts):** the sand bank, the hull, the deck and rails, the stern castle and the gangplank.
- **Glow:** the castle `Window`s have NightLamp; the `Lantern` and the chest's gems have Flicker 0.1 and NightLamp.

| `PotatoKit.Props.Reef.<Name>` | Parts | W × H × D | Count | Scale | Band | Solid | What |
|---|---|---|---|---|---|---|---|
| `BeachPalm` | 23 | 11.4 × 14.7 × 10.8 | 8 | 0.85–1.25 | Side | yes | A palm on a sand mound, coconuts, a starfish at its foot |
| `CoralTree` | 17 | 4.6 × 8.7 × 5.0 | 8 | 0.8–1.3 | Side | no | Two branching corals, pink-gold and purple, on a rock |
| `BrainCoral` | 15 | 6.1 × 2.5 × 3.6 | 6 | 0.8–1.3 | Any | no | A pink dome of brain coral, two sponges, a purple anemone |
| `Kelp` | 19 | 3.4 × 8.4 × 3.2 | 8 | 0.8–1.3 | Side | no | Four tall bent fronds of kelp with leaves, on a stone |
| `Anchor` | 16 | 9.0 × 9.3 × 4.2 | 3 | 0.9–1.2 | Side | yes | A big iron anchor stuck in the sand, its chain hanging from the ring |
| `TreasureChest` | 13 | 5.7 × 3.6 × 5.2 | 4 | 0.9–1.2 | Side | yes | An open chest heaped with gold, two glowing gems (Flicker, NightLamp), coins spilled |
| `GiantClam` | 12 | 5.8 × 4.3 × 5.4 | 5 | 0.8–1.3 | Side | yes | An open clam with a glowing pearl (`Pearl`: Flicker, NightLamp) |
| `BarrelStack` | 22 | 5.9 × 4.7 × 4.9 | 4 | 0.9–1.2 | Side | yes | Three barrels stacked, one on its side, and a crate |
| `DockPosts` | 20 | 6.8 × 6.0 × 2.2 | 4 | 0.9–1.2 | Edge | yes | Three dock posts roped together, a lifebuoy, a gull on top |

**Previews:** `previews/scenery/`

- `hero_Reef.jpg`: from the lane
- `hero_Reef_corner.jpg`: from the corner
- `props_Reef.jpg`: the props in a row
- `props_Reef_top.jpg`: the props from above

### Frost Fields (`BuildSceneryFrost.lua`)

**`PotatoKit.Heroes.Frost`**: 217 parts, 44.1 wide, 39.8 tall, 16.3 deep.

- **The ice castle gate:** two eight-sided ice towers in three close pale blues, getting lighter upwards (no transparency).
  - Each tower has a white battlement ring and a stepped blue spire with a cyan crystal on its tip.
  - Each also has a crystal cluster on the battlements, a royal blue banner with a white snowflake, and a slit window.
- **The gatehouse:** piers of big ice blocks and a chamfered arch framed in white, with a glowing keystone. A half-raised portcullis hangs over a deep blue passage, and a snowy walkway with battlements runs over the top.
- **The ice king:** a frozen potato king on a plinth in the middle of the walkway. He wears a gold crown with a crystal gem and a royal blue stole, and raises a crystal sceptre.
- **Icicles** hang under the battlements, the walkway, the arch and the window sills. Snow drifts and crystal clusters lie at the gate's foot.
- **Solid (68 parts):** the towers, the gate piers and lintel, the walkway and the step. The arch is a walk-in niche about 4 deep: the portcullis is decoration and the dark wall at its back is solid.
- **Glow:** the crystals, the keystone, the crown gem and the sceptre have Flicker and NightLamp.

| `PotatoKit.Props.Frost.<Name>` | Parts | W × H × D | Count | Scale | Band | Solid | What |
|---|---|---|---|---|---|---|---|
| `Igloo` | 22 | 9.0 × 7.0 × 10.6 | 3 | 0.9–1.2 | Side | yes | A snow-block dome with an entrance tunnel and a warm glowing doorway (Flicker, NightLamp) |
| `SledPresents` | 26 | 3.0 × 6.0 × 8.1 | 4 | 0.9–1.2 | Any | no | A red sled with curled runners, three stacked presents with ribbons, and a pull rope |
| `PenguinStatue` | 24 | 4.8 × 7.1 × 4.2 | 3 | 0.9–1.2 | Side | yes | A penguin potato on an ice plinth, in a red scarf and bobble hat |
| `IceCrystals` | 12 | 5.1 × 5.3 × 4.4 | 8 | 0.8–1.4 | Any | no | Five blue ice shards with glowing cyan tips (Flicker, NightLamp) on a snow base |
| `FrozenFountain` | 22 | 7.6 × 8.1 × 7.6 | 2 | 0.9–1.15 | Side | yes | A stone basin with a frozen pool, a frozen stream from its bowl, icicles and a glowing tip |
| `SnowFort` | 22 | 9.7 × 5.6 × 4.8 | 4 | 0.9–1.2 | Edge | yes | A curved wall of snow blocks with a pile of snowballs, a red flag and a shovel |
| `SnowLamp` | 20 | 3.4 × 11.0 × 2.8 | 6 | 0.95–1.15 | Side | no | A dark iron lamp post with a warm lantern (Flicker, NightLamp), a snow cap and a holly wreath |
| `SkiStand` | 18 | 4.2 × 7.8 × 3.6 | 4 | 0.9–1.2 | Side | no | Two skis and crossed poles stuck in a snow pile, with a bobble hat on a pole |

These stand beside Folk Valley's own snowy pines, ice shards, rocks, snow piles, snowmen, frozen pond and cabin, which the map uses too.

**Previews:** `previews/scenery/`

- `hero_Frost.jpg`: from the lane
- `hero_Frost_corner.jpg`: from the corner
- `props_Frost.jpg`: the props in a row
- `props_Frost_top.jpg`: the props from above

### Haunted Hollow (`BuildSceneryHaunt.lua`)

**`PotatoKit.Heroes.Haunt`**: 166 parts, 44.6 wide, 37.3 tall, 24.2 deep.

- **The manor:** it leans a little. Two storeys of upright purple planks on a stone footing, a steep gable roof with a glowing dormer and a crooked chimney.
- **The windows:** some are lit orange or purple and flicker; some are dark, one with its shutters hanging askew.
- **The porch:** steps up to it, a door, and a purple lantern.
- **The tower:** round, beside the manor, with a pointed roof, two lit windows and a bat on the spire. A ghost drifts past it.
- **In front:** a giant jack-o'-lantern with a glowing face, three graves behind a spiky iron fence, and a dead tree with a lantern hanging from it.
- **Solid (28 parts):** the footing, the walls, the tower, the porch and its steps.
- **Glow:** Flicker and NightLamp on the `Window`s (the dormer's is named `Dormer`), the pumpkin's face (`Pumpkin`, Neon parts only), both `Lantern`s and the bat's eyes (`Bat`, NightLamp only).
- **The ghost:** its parts are at Transparency 0.25.

| `PotatoKit.Props.Haunt.<Name>` | Parts | W × H × D | Count | Scale | Band | Solid | What |
|---|---|---|---|---|---|---|---|
| `DeadTree` | 20 | 6.5 × 14.9 × 6.2 | 6 | 0.85–1.3 | Side | yes | A bare crooked tree, a lantern hanging from a branch, a bat on another |
| `Graves` | 17 | 7.8 × 4.1 × 4.6 | 6 | 0.9–1.2 | Side | yes | Three crooked headstones with crosses and mounds, a lit candle |
| `JackOLanterns` | 34 | 7.9 × 3.7 × 4.0 | 6 | 0.8–1.3 | Any | no | Three pumpkins, two carved with glowing faces |
| `Cauldron` | 18 | 4.4 × 5.9 × 4.4 | 3 | 0.9–1.2 | Side | yes | A black pot on three legs over a fire, green brew bubbling, a ladle |
| `CrookedLamp` | 14 | 4.0 × 9.6 × 2.0 | 6 | 0.9–1.15 | Side | no | A bent iron lamp post with a lantern and a bat on it |
| `IronFence` | 16 | 11.9 × 5.0 × 1.5 | 5 | 0.9–1.1 | Edge | yes | A spiky iron fence between two big posts |
| `Coffin` | 11 | 4.8 × 6.1 × 4.0 | 3 | 0.9–1.2 | Side | yes | A coffin standing on a mound, its lid swung open, two red eyes glowing inside |
| `GlowShrooms` | 12 | 5.2 × 4.2 × 3.7 | 8 | 0.8–1.4 | Any | no | Four mushrooms with glowing purple caps |
| `Ghost` | 11 | 4.4 × 4.3 × 1.9 | 4 | 0.8–1.3 | Any | no | A friendly ghost floating above the ground with a lantern (Transparency 0.25) |

**Previews:** `previews/scenery/`

- `hero_Haunt.jpg`: from the lane
- `hero_Haunt_corner.jpg`: from the corner
- `props_Haunt.jpg`: the props in a row
- `props_Haunt_top.jpg`: the props from above

### Lava Furrows (`BuildSceneryLava.lua`)

**`PotatoKit.Heroes.Lava`**: 205 parts, 42.5 wide, 39.9 tall (26.5 to the crater rim, the rest is smoke), 29.5 deep.

- **The volcano:** a stepped cone of nine rounded tiers, each turned its own way, charcoal at the foot and red-brown at the top, with boulders on the ledges.
- **The crater:** a jagged rim open towards the lane, with a glowing pool, a boiling dome and a short spurt of lava with splashes, and grey smoke puffs over it.
- **The lava:** three Neon streams run down the front over the step edges, orange with yellow cores and widening as they go. Two come from the crater and one from a vent in the flank. They end in a lava pool with bursting bubbles, behind a low kerb of stones. Glowing cracks zig-zag across the steps and three lava bombs lie about.
- **The potato:** in a silver fire-proof suit with a gold visor flipped up, dipping a long ladle into the pool.
- **Solid (65 parts):** every tier of the cone, the crater rim, the ledge boulders, the big rocks at the foot, the vent lip and the kerb stones. A player can climb the lower steps but not walk into the upper ones.
- **Glow:** all its Neon (the streams, the pool, the crater, the cracks, the bombs) has NightLamp, and nearly all of it Flicker.

| `PotatoKit.Props.Lava.<Name>` | Parts | W × H × D | Count | Scale | Band | Solid | What |
|---|---|---|---|---|---|---|---|
| `RockSpikes` | 26 | 7.6 × 9.9 × 6.1 | 6 | 0.85–1.3 | Side | yes | Five leaning stacked spikes, charcoal at the foot and red-brown at the tips |
| `CharredStump` | 24 | 8.6 × 7.8 × 7.0 | 5 | 0.85–1.25 | Side | yes | A burnt stump with a snapped splinter and a smouldering top, a fallen log with a glowing end, and a wisp of smoke |
| `SteamVent` | 18 | 6.3 × 6.9 × 6.0 | 5 | 0.9–1.3 | Side | no | A ring of leaning rocks with a glow inside and white steam rising |
| `ObsidianSlabs` | 14 | 8.7 × 6.5 × 5.9 | 4 | 0.9–1.3 | Edge | yes | Leaning purple-black slabs with glossy edges |
| `BonePile` | 24 | 7.0 × 3.6 × 4.9 | 6 | 0.8–1.2 | Any | no | A horned skull, crossed bones and ribs on ash |
| `LavaPool` | 15 | 8.1 × 1.4 × 7.0 | 4 | 0.9–1.3 | Side | no | A round glowing pool with a bubble and a crust, in a kerb of rocks |
| `MagmaBoulder` | 17 | 8.0 × 4.8 × 5.9 | 5 | 0.85–1.3 | Side | yes | A lumpy boulder split by branching glowing cracks, with embers round it |
| `FirePit` | 28 | 5.7 × 4.5 × 5.1 | 3 | 0.9–1.15 | Side | no | A stone ring of crossed charred logs and flames, with a foil-wrapped baked potato (no face) on a spit |
| `WarningSign` | 16 | 6.3 × 6.1 × 3.0 | 3 | 0.95–1.15 | Side | yes | A hazard-striped sign with a yellow "!" diamond and a lava drip |
| `CooledLava` | 13 | 8.1 × 1.2 × 6.3 | 8 | 0.8–1.4 | Any | no | Flat crusts of cooled lava with a faint glowing crack |

**Previews:** `previews/scenery/`

- `hero_Lava.jpg`: from the lane
- `hero_Lava_corner.jpg`: from the corner
- `props_Lava.jpg`: the props in a row
- `props_Lava_top.jpg`: the props from above

### Crystal Caverns (`BuildSceneryCrystal.lua`)

**`PotatoKit.Heroes.Crystal`**: 194 parts, 45.5 wide, 38.8 tall, 29.4 deep.

- **The crag and the mine:** a grey-violet crag of big turned blocks, darker at the foot, with lighter ledges. Two angled buttresses frame the cave mouth.
  - The mine has a dark opening, two big timber posts with a lintel and braces, and a sign with a glowing pink gem.
- **The crystals:** a fan of nineteen crystals bursts out of the top, the rock face and the ground. Each is a faceted prism with a glowing point.
  - The giant cyan one reaches 38.8.
  - Big pink and gold ones lean out to the sides.
- **The track:** rails on sleepers run out of the mine towards the lane, with a cart heaped with gems on them. Lanterns hang from a post and the frame, and loose gems lie about.
- **The potato miner:** on the buttress ledge about 10 up, in a yellow hard hat with a headlamp and blue overalls, a pickaxe on its shoulder, holding up a glowing gem.
- **Solid (33 parts):** the crag, the bigger rocks, the timber frame and the bodies of the three biggest crystals.
- **Glow:**
  - **Neon:** the crystal points and glints.
  - **NightLamp:** the lanterns, the gems, the headlamp and four of the crystals. All of these but the sign gem also flicker.

| `PotatoKit.Props.Crystal.<Name>` | Parts | W × H × D | Count | Scale | Band | Solid | What |
|---|---|---|---|---|---|---|---|
| `GiantCluster` | 30 | 11.3 × 12.4 × 8.9 | 3 | 0.9–1.25 | Edge | yes | Seven cyan, pink and gold crystals fanning out of a rock base |
| `CrystalCluster` | 19 | 7.5 × 7.9 × 6.2 | 6 | 0.8–1.3 | Side | no | Five cyan and pink crystals growing out of a rock |
| `GoldCrystals` | 19 | 5.7 × 5.4 × 4.3 | 6 | 0.8–1.3 | Side | no | Four gold crystals with glowing tips on a flat rock |
| `MineCart` | 25 | 3.9 × 5.6 × 9.3 | 3 | 0.95–1.15 | Side | yes | A cart heaped with gems on a short track with a red buffer |
| `MineLantern` | 13 | 4.0 × 7.6 × 3.1 | 5 | 0.95–1.15 | Side | no | A timber post with a hanging lantern (NightLamp) and a crystal at its foot |
| `Stalagmites` | 20 | 6.2 × 8.5 × 5.1 | 6 | 0.8–1.35 | Side | yes | Four tapering rock spires and a pink crystal |
| `GemPile` | 14 | 4.4 × 2.6 × 4.1 | 6 | 0.8–1.2 | Any | no | A sack spilling gems and gold coins |
| `PickaxeRock` | 17 | 5.6 × 7.7 × 5.8 | 3 | 0.9–1.2 | Side | yes | A pickaxe bitten into a rock, with crystals and chips |
| `TimberSupport` | 19 | 9.7 × 10.1 × 3.2 | 3 | 0.95–1.15 | Edge | yes | Posts, a beam and braces holding up rubble, with a hanging lantern |
| `Geode` | 32 | 7.5 × 5.8 × 6.5 | 4 | 0.85–1.25 | Side | yes | A round geode cracked open towards the lane, crystals inside, its other half beside it |

**Previews:** `previews/scenery/`

- `hero_Crystal.jpg`: from the lane
- `hero_Crystal_corner.jpg`: from the corner
- `props_Crystal.jpg`: the props in a row
- `props_Crystal_top.jpg`: the props from above

### Dino Valley (`BuildSceneryDino.lua`)

**`PotatoKit.Heroes.Dino`**: 157 parts, 43.7 wide, 22.3 tall, 29.4 deep.

- **The skeleton:** a huge T-rex standing side-on to the lane on a layered rock dig site. It has a big skull with its jaw open and teeth, a curved neck, a spine with spines along the back, ribs, tiny arms, long legs with clawed feet and a long tail curving down. Two iron posts hold it up.
- **Behind it:** a small volcano with a glowing crater and two lava runs.
- **Round about:** cycads, ferns and horsetails, a nest of three spotted eggs, a glowing lump of amber with a mosquito in it, loose bones, a pickaxe, a shovel and a crate.
- **Solid (26 parts):** the three rock layers, the volcano, and the skeleton's spine, skull, pelvis and leg bones. Players can climb the dig site and jump onto the T-rex's back. Ribs, teeth and arms are decoration.
- **Glow:** `Lava` (the crater and the two runs) and `Amber` have Flicker and NightLamp.

| `PotatoKit.Props.Dino.<Name>` | Parts | W × H × D | Count | Scale | Band | Solid | What |
|---|---|---|---|---|---|---|---|
| `Cycad` | 13 | 8.4 × 7.6 × 7.7 | 8 | 0.85–1.3 | Side | yes | A stout scaly trunk, a crown of nine stiff fronds, a gold cone |
| `TreeFern` | 13 | 10.3 × 10.4 × 9.2 | 6 | 0.85–1.3 | Side | yes | A tall tree fern, its fronds drooping |
| `BoneArch` | 28 | 11.6 × 10.4 × 8.3 | 3 | 0.9–1.2 | Side | yes | A giant ribcage you can walk through |
| `DinoNest` | 17 | 4.9 × 2.6 × 4.8 | 5 | 0.9–1.3 | Any | no | A nest of spotted eggs, one cracked open with a baby dino peeking out |
| `MiniVolcano` | 12 | 9.6 × 11.2 × 7.5 | 3 | 0.9–1.2 | Edge | yes | A small volcano: a glowing crater, two lava runs (`Lava`: Flicker, NightLamp), smoke (Transparency 0.35) |
| `AmberRock` | 10 | 6.0 × 4.3 × 5.0 | 5 | 0.85–1.25 | Side | yes | Rocks with glowing amber in them (`Amber`, NightLamp), a mosquito in the biggest piece |
| `Footprints` | 12 | 10.3 × 0.2 × 5.2 | 6 | 0.9–1.4 | Any | no | A trail of three giant three-toed footprints, flat on the ground |
| `FossilSkull` | 11 | 7.9 × 4.0 × 5.0 | 3 | 0.9–1.2 | Side | yes | A T-rex skull and jaw half dug out of the earth |
| `Horsetails` | 12 | 2.7 × 5.3 × 2.7 | 8 | 0.8–1.3 | Any | no | A clump of tall horsetail reeds by a rock |

**Previews:** `previews/scenery/`

- `hero_Dino.jpg`: from the lane
- `hero_Dino_corner.jpg`: from the corner
- `props_Dino.jpg`: the props in a row
- `props_Dino_top.jpg`: the props from above

### Toy Town (`BuildSceneryToy.lua`)

**`PotatoKit.Heroes.Toy`**: 164 parts, 41.5 wide, 30.1 tall, 28.2 deep.

- **The castle:** toy building blocks on a green baseplate. The keep is big bricks laid in a running bond in red, blue, yellow and green, with battlements on top, four windows, a gate under a yellow arch and a drawbridge.
- **The towers:** two round towers of stacked blocks, each block turned 45 degrees from the last, with cone roofs and flags.
- **The key:** a giant wind-up key in the keep's left side that turns. Its three `Key` parts have `Spin` = 40, each centred on the axle.
- **The staircase:** blocks up the right side to the top of the keep, each about 3.5 high, so players jump up them.
- **The soldiers:** two potato toy soldiers with bearskins and rifles guard the gate.
- **The train:** a toy train waits on its track in front. The engine has a smiling face, and two wagons carry alphabet blocks. Its wheels are Cylinder parts.
- **Round about:** a spinning top, with `Spin` = 120 on its five `Top` parts, and three alphabet blocks.
- **Solid (41 parts):** the baseplate, the keep's bricks and battlements, the towers, the drawbridge and the staircase.

| `PotatoKit.Props.Toy.<Name>` | Parts | W × H × D | Count | Scale | Band | Solid | What |
|---|---|---|---|---|---|---|---|
| `ABCBlocks` | 12 | 6.6 × 4.9 × 5.3 | 8 | 0.8–1.3 | Side | yes | Four alphabet blocks, one stacked on the others |
| `SpinningTops` | 10 | 6.7 × 5.3 × 4.0 | 6 | 0.8–1.3 | Any | no | One top spinning on its point (`Spin` = 120 on its five parts) and one fallen over |
| `ToySoldier` | 21 | 4.7 × 8.1 × 3.4 | 5 | 0.9–1.2 | Side | yes | A potato toy soldier on a stand, with a bearskin, a rifle and a drum |
| `RubberDuck` | 14 | 6.3 × 5.1 × 5.8 | 4 | 0.9–1.3 | Side | yes | A giant rubber duck on a puddle (Transparency 0.3) |
| `JackInTheBox` | 24 | 5.0 × 10.2 × 3.9 | 4 | 0.9–1.2 | Side | yes | A striped box with its lid open, a crank and a clown potato on a spring |
| `TeddyBear` | 18 | 5.8 × 6.5 × 3.7 | 4 | 0.9–1.2 | Side | yes | A sitting teddy bear with a red bow tie |
| `ToyCar` | 12 | 6.2 × 4.0 × 3.8 | 5 | 0.9–1.2 | Side | yes | A blue toy car with cylinder wheels and glowing headlights (`Light`, NightLamp) |
| `Crayons` | 12 | 5.6 × 7.4 × 2.6 | 6 | 0.85–1.3 | Side | no | Three giant crayons standing up, leaning |

**Previews:** `previews/scenery/`

- `hero_Toy.jpg`: from the lane
- `hero_Toy_corner.jpg`: from the corner
- `props_Toy.jpg`: the props in a row
- `props_Toy_top.jpg`: the props from above

### Candy Crops (`BuildSceneryCandy.lua`)

**`PotatoKit.Heroes.Candy`**: 217 parts, 42.6 wide, 37.3 tall, 25.2 deep.

- **The cake:** three tiers on a round white board, getting lighter upwards: chocolate, then pink, then vanilla.
  - Each tier is an eight-sided drum under an overhanging icing lid.
  - Drips of different lengths run down every side: white on the lower two tiers, pink on the top one. The longest end in a fat drop.
  - Each tier has a band of sprinkles, and the lower rims have cherries on whipped cream.
- **The slice:** a wedge is cut out of the front of the chocolate tier. It shows lighter sponge with a cream layer and a jam layer.
- **On top:** a potato cake-topper with a party hat and both arms up, holding a blue swirl lollipop high. Four big striped candles stand round it.
- **Beside the cake:** a giant candy cane curling towards it, a giant swirl lollipop with a ribbon bow, and gumdrops at the foot.
- **Solid (28 parts):** the board, the three tier drums and their icing lids.
- **Glow:** the candles' eight flame parts have Flicker and NightLamp.

| `PotatoKit.Props.Candy.<Name>` | Parts | W × H × D | Count | Scale | Band | Solid | What |
|---|---|---|---|---|---|---|---|
| `CandyCane` | 22 | 4.3 × 11.3 × 5.2 | 6 | 0.85–1.3 | Edge | no | A tall red-and-white cane and a shorter leaning green-and-white one on a sugar drift |
| `LollipopTree` | 34 | 8.6 × 14.8 × 4.6 | 6 | 0.85–1.25 | Side | no | Three swirl lollipops (pink, blue, lemon) on sticks out of a pink gumdrop |
| `Doughnut` | 30 | 7.1 × 7.1 × 3.5 | 4 | 0.9–1.25 | Side | yes | A giant doughnut on its edge, with pink icing and sprinkles |
| `Gumdrops` | 24 | 7.6 × 3.6 × 5.6 | 10 | 0.8–1.4 | Any | no | Four sugared gumdrops |
| `Cupcake` | 26 | 4.7 × 8.8 × 4.7 | 4 | 0.9–1.25 | Side | yes | A pleated blue-and-white wrapper, a pink frosting swirl, sprinkles and a cherry |
| `GingerbreadFence` | 36 | 9.4 × 5.4 × 1.5 | 5 | 0.9–1.1 | Edge | yes | Gingerbread posts and pickets with icing and gumdrops on the posts |
| `IceCreamCone` | 20 | 4.4 × 13.6 × 4.4 | 4 | 0.9–1.2 | Side | yes | A waffle cone standing on its tip in a melted puddle: two scoops, drips, a wafer and a cherry |
| `WrappedSweets` | 20 | 5.0 × 2.2 × 4.8 | 10 | 0.8–1.3 | Any | no | Two wrapped sweets with twisted wrapper ends |
| `ChocolateStack` | 22 | 7.2 × 3.7 × 5.7 | 4 | 0.9–1.2 | Side | yes | Three crossed bars (dark, milk, white), the top one half unwrapped |
| `CandyMushroom` | 22 | 5.4 × 4.9 × 3.9 | 8 | 0.8–1.3 | Any | no | Pink and mint mushrooms with white sugar dots |

**Previews:** `previews/scenery/`

- `hero_Candy.jpg`: from the lane
- `hero_Candy_corner.jpg`: from the corner
- `props_Candy.jpg`: the props in a row
- `props_Candy_top.jpg`: the props from above

### Clockwork Yard (`BuildSceneryClock.lua`)

**`PotatoKit.Heroes.Clock`**: 174 parts, 39.6 wide, 37.9 tall, 16.9 deep.

- **The tower:** brass and copper on a stone base with steps. Copper panels in two shades sit between brass bands.
- **The clock:** a big clock face at the top, its hands at ten past ten.
- **Below the clock:** a glass case (Transparency 0.55) with the pendulum, then a door.
- **On top:** an open cupola with a bell, a green stepped roof and a weathervane.
- **The gears:** eight of them turn: three on the front, one on each side, one on the workshop and two in an iron frame on the far side.
  - Every `Gear` part has `Spin`. The parts of one gear share a value and are all centred on its axle.
  - Gears that mesh turn opposite ways (negative Spin).
- **Beside it:** a brick workshop with a chimney letting off steam and a round clock window; copper pipes with a red valve and steam; and two gas lamps at the foot.
- **Solid (18 parts):** the base and steps, the tower, the workshop and its roof, and the gear frame's posts and footing.
- **Glow:** the two gas lamps (`Lamp`) have Flicker 0.08 and NightLamp. The steam is Transparency 0.35.

| `PotatoKit.Props.Clock.<Name>` | Parts | W × H × D | Count | Scale | Band | Solid | What |
|---|---|---|---|---|---|---|---|
| `GearStand` | 16 | 7.9 × 8.3 × 2.5 | 6 | 0.85–1.25 | Side | yes | A big brass gear on an iron stand meshing with a copper one (`Spin` 30 and -62) |
| `SteamPipes` | 28 | 5.4 × 10.6 × 3.0 | 5 | 0.9–1.3 | Edge | yes | Three copper pipes with brass collars, a red valve, a pressure gauge and steam |
| `GasLamp` | 14 | 2.9 × 9.7 × 1.8 | 6 | 0.95–1.15 | Side | no | A Victorian gas lamp (`Lamp`: Flicker, NightLamp) |
| `Boiler` | 28 | 5.3 × 11.2 × 5.4 | 4 | 0.9–1.2 | Side | yes | A copper boiler on legs with brass bands, a fire glowing in its door (`Fire`), a gauge, a chimney and steam |
| `GearPile` | 16 | 5.9 × 3.1 × 5.2 | 8 | 0.8–1.3 | Any | no | Three loose gears in a heap |
| `PocketWatch` | 25 | 7.0 × 7.3 × 3.1 | 3 | 0.9–1.2 | Side | yes | A giant brass pocket watch leaning back on a stand |
| `StreetClock` | 17 | 4.0 × 11.6 × 2.5 | 4 | 0.95–1.15 | Side | no | A clock on a tall iron post |
| `GiantSpring` | 17 | 3.7 × 7.2 × 3.7 | 5 | 0.85–1.2 | Side | yes | A giant steel spring coiled on a crate |

**Previews:** `previews/scenery/`

- `hero_Clock.jpg`: from the lane
- `hero_Clock_corner.jpg`: from the corner
- `props_Clock.jpg`: the props in a row
- `props_Clock_top.jpg`: the props from above

### Neon City (`BuildSceneryNeon.lua`)

**`PotatoKit.Heroes.Neon`**: 156 parts (48 of them Neon), 44.0 wide, 22.8 tall, 28.6 deep.

- **The stage:** raised, with glowing cyan and magenta edges and steps up at both sides.
- **The screen:** a big screen behind the stage with a seven-bar equaliser across it (`Equaliser`, Flicker 0.25), framed in neon tubes.
- **The truss:** it carries four spotlights throwing cyan, magenta, yellow and green beams onto the stage, and a disco ball that turns.
  - Each `Beam` is see-through Neon (Transparency 0.65, Flicker 0.15).
  - The four `Disco` parts have `Spin` = 40.
- **The music:** speaker stacks on both sides and two more on the floor in front. The DJ booth has two records that turn (`Record`, `Spin` = 90) and the potato DJ in headphones and glowing glasses.
- **In front:** a dance floor of dark tiles with a grid of glowing lines, a crowd barrier and two uplights. Two neon palms stand by the stage.
- **Solid (9 parts):** the stage, its steps, the screen and the dance floor.
- **Glow:** every Neon part has NightLamp. The beams, spotlights, equaliser and stage edges also have Flicker.

| `PotatoKit.Props.Neon.<Name>` | Parts | W × H × D | Count | Scale | Band | Solid | What |
|---|---|---|---|---|---|---|---|
| `NeonSign` | 14 | 8.6 × 9.7 × 0.9 | 5 | 0.9–1.2 | Edge | yes | A dark board on posts with a glowing potato outline and face in neon tube |
| `CyberLamp` | 10 | 5.4 × 11.6 × 2.3 | 8 | 0.95–1.15 | Side | no | A tall street lamp with a glowing head, a neon strip down the pole and a glowing panel |
| `SpeakerStack` | 12 | 5.5 × 5.3 × 2.5 | 4 | 0.9–1.2 | Side | yes | Three speaker boxes stacked |
| `ArcadeMachine` | 12 | 3.2 × 6.7 × 3.7 | 4 | 0.95–1.15 | Side | yes | A purple arcade cabinet with a glowing screen and marquee, buttons and a joystick |
| `VendingMachine` | 14 | 3.7 × 7.3 × 2.8 | 4 | 0.95–1.15 | Side | yes | A red drinks machine with a lit window of coloured cans |
| `NeonPalm` | 13 | 9.3 × 12.5 × 9.1 | 6 | 0.85–1.25 | Side | yes | A dark palm with glowing pink and cyan fronds in a lit pot |
| `Hologram` | 10 | 4.8 × 5.4 × 4.8 | 3 | 0.9–1.2 | Any | no | A projector throwing a see-through potato head that turns (`Holo`, `Spin` = 30) |
| `HoverBike` | 10 | 6.6 × 4.6 × 2.2 | 4 | 0.9–1.2 | Any | no | A hover bike floating over a glow, with a see-through shadow under it |

**Previews:** `previews/scenery/`

- `hero_Neon.jpg`: from the lane
- `hero_Neon_corner.jpg`: from the corner
- `props_Neon.jpg`: the props in a row
- `props_Neon_top.jpg`: the props from above

### Cloud Kingdom (`BuildSceneryCloud.lua`)

**`PotatoKit.Heroes.Cloud`**: 145 parts, 41.1 wide, 26.2 tall, 22.8 deep.

- **The cloud:** a fluffy base of white and pale blue puffs, with cloud steps up to the gate.
- **The palace:** a white keep with gold bands and a stepped gold dome. A spire on top carries a glowing star.
- **Its front:** pale blue windows, a gold gate and two glowing lamps.
- **The towers:** two slim white towers with gold roofs and pink and blue flags.
- **The rainbow:** a six-band rainbow arches over it all from cloud to cloud, with little clouds floating about.
- **Solid (24 parts):** the cloud base, the steps, the keep and the towers.
- **Glow:** the gate `Lamp`s have Flicker 0.08 and NightLamp; the `Spire` star has NightLamp.

| `PotatoKit.Props.Cloud.<Name>` | Parts | W × H × D | Count | Scale | Band | Solid | What |
|---|---|---|---|---|---|---|---|
| `CloudPuff` | 10 | 9.4 × 3.8 × 6.1 | 10 | 0.8–1.4 | Side | yes | A fluffy cloud resting on the ground |
| `CloudTree` | 12 | 9.2 × 13.1 × 5.5 | 6 | 0.85–1.25 | Side | yes | A pale trunk with a canopy of cloud |
| `RainbowArch` | 36 | 15.2 × 7.0 × 3.7 | 3 | 0.9–1.3 | Side | yes | A small rainbow from one cloud to another, high enough to walk under |
| `GoldenHarp` | 11 | 3.9 × 7.3 × 4.0 | 3 | 0.9–1.2 | Side | yes | A golden harp on a cloud |
| `CloudPillar` | 10 | 4.5 × 10.6 × 4.6 | 5 | 0.9–1.2 | Side | yes | A white column with gold rings on a cloud, a glowing gem on top |
| `HotAirBalloon` | 12 | 5.4 × 11.8 × 5.4 | 3 | 0.9–1.3 | Edge | no | A red, yellow and blue balloon with a wicker basket on ropes |
| `StarLantern` | 10 | 2.7 × 10.0 × 2.8 | 6 | 0.9–1.2 | Side | no | A gold post on a cloud with a glowing yellow star (`Star`: Flicker, NightLamp) |
| `CloudMill` | 10 | 7.0 × 12.1 × 4.3 | 3 | 0.9–1.2 | Edge | yes | A little white windmill on a cloud, its sails turning (`Sails`, `Spin` = 40) |

**Previews:** `previews/scenery/`

- `hero_Cloud.jpg`: from the lane
- `hero_Cloud_corner.jpg`: from the corner
- `props_Cloud.jpg`: the props in a row
- `props_Cloud_top.jpg`: the props from above

### Cosmic Garden (`BuildSceneryCosmic.lua`)

**`PotatoKit.Heroes.Cosmic`**: 206 parts, 40.7 wide, 36.2 tall, 25.6 deep.

- **The rocket:** a big retro rocket crashed nose first into a crater, tilted so it stays inside the footprint.
  - Its body is white and eight-sided, with a stepped red nose cone, red bands and three swept red fins.
  - It has two round portholes and an open hatch with its door swung out.
- **The crater:** a ring of turned grey slabs over a scorched floor, with boulders round the buried nose. Glowing cracks zig-zag out across the ground.
- **The engine end** points up: a dark nozzle with an orange and pale blue Neon glow and flame blocks, and see-through smoke puffs drifting off it.
- **The potato astronaut:** it waves from the ladder that runs from the hatch to the ground. It wears white boots, a backpack with a red light, an aerial with a glowing tip, and a glass dome of pale blue panes.
- **Round it:** a potato flag on the crater rim, torn hull panels, a torn-off fin, and two clumps of glowing alien plants.
- **Solid (43 parts):** the crater slabs, the boulders and the rocket's big lower sections.
- **Glow:**
  - **Flicker and NightLamp:** the engine, the cracks, the backpack light, the aerial tip and half the plant bulbs.
  - **NightLamp only:** the other bulbs, the portholes and the door window.

| `PotatoKit.Props.Cosmic.<Name>` | Parts | W × H × D | Count | Scale | Band | Solid | What |
|---|---|---|---|---|---|---|---|
| `RingPlanet` | 19 | 7.0 × 10.4 × 7.1 | 5 | 0.85–1.25 | Side | no | A tilted orange planet with a cream-and-lilac ring on a pole. `Spin` 24 on the planet and ring, all centred on its axis. |
| `Crater` | 16 | 8.8 × 2.2 × 8.7 | 6 | 0.8–1.4 | Any | no | A ring of turned moon-grey slabs round a dark floor, with two glowing crystals |
| `SatelliteDish` | 21 | 6.7 × 8.5 × 5.5 | 3 | 0.9–1.2 | Edge | yes | A rimmed white dish on a mast, with a blinking red light on its feed |
| `AlienPlants` | 24 | 5.1 × 6.5 × 4.3 | 10 | 0.8–1.3 | Any | no | Teal fronds and curling stems with Neon bulbs |
| `FloatingRocks` | 14 | 7.8 × 10.8 × 4.7 | 4 | 0.9–1.2 | Side | yes | An upright ring of rocks hovering round a glowing orb on a thin dark pole |
| `StarLamp` | 17 | 4.5 × 10.8 × 3.1 | 6 | 0.9–1.15 | Edge | no | A post with a big yellow Neon star and a small pink one on a branch |
| `MoonRocks` | 12 | 6.9 × 3.7 × 5.1 | 8 | 0.8–1.3 | Side | yes | Lavender moon rocks with glowing cyan and purple crystals |
| `AlienStatue` | 19 | 5.1 × 7.9 × 5.1 | 3 | 0.9–1.2 | Side | yes | A green alien potato on a plinth with a gold plaque, glowing eyes and antenna tips |
| `SpaceFlag` | 14 | 5.9 × 7.5 × 7.5 | 3 | 0.9–1.2 | Side | no | A red potato flag in a mound of moon rock, with boot prints leading to it |
| `Rover` | 20 | 4.4 × 5.8 × 3.7 | 3 | 0.9–1.2 | Side | yes | A six-wheeled rover with a gold deck, a blue solar panel and a camera head with glowing eyes |

**Previews:** `previews/scenery/`

- `hero_Cosmic.jpg`: from the lane
- `hero_Cosmic_corner.jpg`: from the corner
- `props_Cosmic.jpg`: the props in a row
- `props_Cosmic_top.jpg`: the props from above

### Glitch Void (`BuildSceneryVoid.lua`)

**`PotatoKit.Heroes.Void`**: 78 parts (42 of them Neon), 35.4 wide, 30.0 tall, 29.8 deep.

- **The cube:** a huge black cube, 15 on a side, standing on one corner. It hovers 2.5 studs over a cracked dark platform, and its twelve edges glow cyan (`Edge`).
- **The glitch:** a slice of the cube has slipped sideways like a bad signal, and glitch debris rises from under it.
- **The platform:** glowing cracks run out across it, with pixels of static lying about.
- **In the air:** small cubes float round it and turn (`Pixel`, each with its own `Spin`). Two checkered magenta and black "missing texture" blocks (`Missing`) and an error window hang near it.
- **The obelisks:** four little black obelisks with glowing tops stand at the platform's edge.
- **Solid (8 parts):** the platform, the cube and the obelisks. The cube's upper faces slope at 35 degrees, so players can climb onto it.
- **Glow:** every Neon part has NightLamp; the edges, cracks and pixels also flicker.

| `PotatoKit.Props.Void.<Name>` | Parts | W × H × D | Count | Scale | Band | Solid | What |
|---|---|---|---|---|---|---|---|
| `GlitchTree` | 11 | 7.7 × 12.0 × 4.6 | 6 | 0.85–1.25 | Side | yes | A tree of pixel blocks with glowing glitch pixels and a cyan seam down its trunk |
| `FloatingCubes` | 10 | 4.6 × 8.5 × 4.4 | 6 | 0.8–1.3 | Any | no | Cubes floating over a lit base, the glowing ones turning (`Pixel`, Spin) |
| `ErrorSign` | 10 | 6.3 × 9.8 × 2.7 | 4 | 0.9–1.2 | Side | no | An error window on a post |
| `VoidCrystal` | 11 | 4.2 × 7.5 × 3.9 | 6 | 0.8–1.3 | Side | yes | Black crystal shards with glowing purple and magenta seams, on dark rocks |
| `StaticTV` | 13 | 5.3 × 7.0 × 3.7 | 4 | 0.9–1.2 | Side | yes | An old TV full of static, with knobs and rabbit-ear aerials |
| `BrokenPillar` | 10 | 5.5 × 10.4 × 4.4 | 5 | 0.9–1.25 | Side | yes | A pillar of slipped, floating slices with glowing seams, and a fallen chunk |
| `PortalRing` | 11 | 8.9 × 9.6 × 2.4 | 3 | 0.9–1.2 | Edge | yes | An eight-sided dark ring with a glowing swirl inside that turns (`Swirl`, `Spin` = 60) |
| `PixelBush` | 10 | 4.6 × 2.9 × 3.8 | 8 | 0.8–1.3 | Any | no | A bush of pixel cubes with two glowing glitch pixels |

**Previews:** `previews/scenery/`

- `hero_Void.jpg`: from the lane
- `hero_Void_corner.jpg`: from the corner
- `props_Void.jpg`: the props in a row
- `props_Void_top.jpg`: the props from above

### Spud Olympus (`BuildSceneryOlympus.lua`)

**`PotatoKit.Heroes.Olympus`**: 146 parts, 42.9 wide, 28.0 tall, 27.9 deep.

- **The temple:** marble, on three steps, rising out of clouds.
- **The columns:** six across the front with gold capitals (the middle pair set wide apart) and two more down each side.
- **Above them:** an architrave and a frieze with gold squares, then a stepped pediment with a glowing thunderbolt in it, gold ornaments at its corners and a low roof. The cella wall with a dark doorway stands behind.
- **The potato Zeus:** on a pedestal between the middle columns. He has warm skin, a great white beard, moustache, brows and hair, and a gold laurel crown, and he raises a glowing thunderbolt in his right hand.
- **Round the foot:** gold braziers with fires on the steps, two olive trees and clouds.
- **Solid (54 parts):** the steps, the columns, the cella, the beams, the pediment, the roof and Zeus's pedestal. Players can climb the steps and walk the colonnade.
- **Glow:** both `Thunderbolt`s and the brazier `Flame`s have Flicker and NightLamp.

| `PotatoKit.Props.Olympus.<Name>` | Parts | W × H × D | Count | Scale | Band | Solid | What |
|---|---|---|---|---|---|---|---|
| `BrokenColumn` | 10 | 8.8 × 6.3 × 6.3 | 6 | 0.85–1.3 | Side | yes | A broken marble column, one drum and its gold capital fallen beside it |
| `OliveTree` | 12 | 8.3 × 12.3 × 8.1 | 6 | 0.85–1.25 | Side | yes | A silvery-green olive tree with olives |
| `Amphora` | 12 | 3.4 × 5.7 × 3.4 | 6 | 0.8–1.3 | Side | yes | A terracotta amphora with black bands and handles |
| `GoldBrazier` | 10 | 3.4 × 6.4 × 3.4 | 5 | 0.9–1.2 | Side | no | A gold brazier on three legs with a fire burning (`Flame`, `Ember`: NightLamp) |
| `HeroStatue` | 15 | 5.2 × 7.9 × 4.0 | 3 | 0.9–1.2 | Side | yes | A marble potato athlete with a gold crown and discus, on a plinth |
| `LaurelBush` | 10 | 5.4 × 3.6 × 4.1 | 8 | 0.8–1.3 | Any | no | A laurel bush with gold berries |
| `Fountain` | 10 | 7.8 × 5.4 × 7.8 | 3 | 0.9–1.2 | Side | yes | A marble fountain with water falling into its basin (Transparency 0.3) |
| `GoldenLyre` | 11 | 3.4 × 6.0 × 2.2 | 3 | 0.9–1.2 | Side | yes | A golden lyre on a marble plinth |

**Previews:** `previews/scenery/`

- `hero_Olympus.jpg`: from the lane
- `hero_Olympus_corner.jpg`: from the corner
- `props_Olympus.jpg`: the props in a row
- `props_Olympus_top.jpg`: the props from above
