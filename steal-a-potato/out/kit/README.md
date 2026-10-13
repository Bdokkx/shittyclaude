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
