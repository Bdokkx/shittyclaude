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
| `BuildPlotKit.lua` | 4.2, the plot kit: four fence tiers, Soil, UpgradeBoard, Mound, eight Seeds |

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
  - An open doorway 8 wide (local X) and 6.7 high; the player runs through it along Z.
  - Two posts on plinths and a header beam in the tier's strong colour. Fence_Rainbow's header is six Neon stripes.
  - **`Board`** faces the front (-Z) and **`BoardBack`** the back, 8.4 × 2.9. Both are dark SmoothPlastic, so the owner's name in white reads from either side.
  - Attribute `OpeningWidth` = 8. Pivot on the ground at the centre.

**Pivots:**

- **Soil:** the top centre of the dirt, where the potato stands.
- **Mound:** the top centre of the dent, where the seed goes.
- **UpgradeBoard:** on the ground at its centre. `Board` and `Button` face -Z, and `Prompt` is 2.6 in front.

**Seeds.** Each seed is an egg about 1.7 wide; 2.2–2.8 tall with its topper. Pivot at the bottom. Every brick of the egg is named **`Body`** and is light grey (236, 236, 232) for you to tint. The rest comes coloured:

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

**Flags.** All of 4.2 is decoration: anchored, CanCollide, CanTouch and CanQuery off, and no shadow from parts under 2.5 studs. If you want solid fences, turn CanCollide on for the posts and bars.

**Previews:** `previews/plot/`

- `plot_tiers.jpg`: the four tiers side by side.
- `plot_Fence_<Tier>.jpg`: each tier, with Spud for scale.
- `plot_misc.jpg`: UpgradeBoard, Mound with a seed in its dent, and Soil with a potato on it.
- `plot_seeds.jpg`: the eight seeds as built, and tinted.
