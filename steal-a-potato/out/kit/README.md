# Steal a Potato: the bricks kit

One unattended build script per piece. Run it from the command bar or with `loadstring`. It merges into **ReplicatedStorage.PotatoKit**, making the folder if it is missing and setting the attribute `Studs = true`. Each item it lists replaces whatever has that name in that folder; nothing else is touched, so every script is safe to run twice.

Every Part is a plain Roblox Part:

- **Plastic, Inlet on all six faces:** the default.
- **SmoothPlastic, Smooth faces:** flat surfaces that carry text or a face.
- **Neon (Smooth):** only what glows.

The pieces so far:

| Script | Piece |
|---|---|
| `BuildPotatoesMeadow.lua` | 4.1, the Meadow Patch potatoes and the six potato clips |
| `BuildPlotKit.lua` | 4.2, the plot kit: four fence tiers, Soil, UpgradeBoard, Mound, the Seeds (now 18, with 30% bigger toppers; GateArch now 14 wide) |
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
| `PotatoKit.Soil` | Raised bed 5 × 5: wooden border with corner posts, dirt with two furrows and clods. |
| `PotatoKit.UpgradeBoard` | Folk Valley sign, small: legs on stone plinths, a gold header, the dark `Board`, a green `Button` under it and an invisible `Prompt`. |
| `PotatoKit.Mound` | A heap of dug soil about 5 wide and 1 high, with a dark dent on top, clods and pebbles. |
| `PotatoKit.Seeds.Seed_Meadow` … `Seed_Cosmic` | Eight seeds, see below. |

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

- **Soil:** the top centre of the dirt, where the potato stands.
- **Mound:** the top centre of the dent, where the seed goes.
- **UpgradeBoard:** on the ground at its centre. `Board` and `Button` face -Z, and `Prompt` is 2.6 in front.

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
- `plot_misc.jpg`: UpgradeBoard, Mound with a seed in its dent, and Soil with a potato on it.
- `plot_seeds.jpg`: the eight seeds as built, and tinted.

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
