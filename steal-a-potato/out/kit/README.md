# Steal a Potato: bricks kit, piece 4.1 (Meadow Patch potatoes and clips)

**Run:** `BuildPotatoesMeadow.lua`, from the command bar or with `loadstring`. It runs unattended. It builds the items below inside **ReplicatedStorage.PotatoKit**, making the folder if it is missing and setting the attribute `Studs = true`:

| Path | What |
|---|---|
| `PotatoKit.Potatoes.Spud` | Common: plain russet with darker spots and a knobbly lump |
| `PotatoKit.Potatoes.TaterTot` | Common: short, wide, golden; crispy bits on top and sides |
| `PotatoKit.Potatoes.YukonGold` | Uncommon: pale gold egg with a shine and the little leaf it was born with |
| `PotatoKit.Potatoes.RedRascal` | Rare: round and red, one brow up, lopsided grin with a tooth |
| `PotatoKit.Potatoes.SweetPotato` | Epic: tall orange, pointed at both ends, pink bow |
| `PotatoKit.Potatoes.GoldenSpud` | Legendary: Spud in solid gold, two Neon star glints |
| `PotatoKit.PotatoAnimations.PotatoIdle` … `PotatoLevelUp` | six KeyframeSequences, see below |

Each item replaces whatever has the same name in the same folder, which is what an earlier run built. Nothing else in PotatoKit is touched, so it is safe to run twice. If your place still has the part-1 kit (meshes) in a folder called PotatoKit, its old pieces stay there until the brick pieces replace them.

## Parts

All of it is plain Parts:

- **Plastic, Inlet on all six faces:** the bodies, limbs, shoes, sprouts and crowns.
- **SmoothPlastic, Smooth faces:** the eyes, mouths, cheeks, glints and tongues.
- **Neon (Smooth):** only the crown jewels and Golden Spud's two star glints.
- **Flags:** everything except Root is unanchored, Massless, and has CanCollide, CanTouch and CanQuery off. CastShadow is off on parts under 2.5 studs.

Every potato is 43–45 Parts in total. That count includes Root and the invisible feature parts.

## The rig (the same in all 48)

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

## The clips

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

## Previews

These are in `previews/potatoes/`, rendered in Blender, where studs show as inlet rings:

- `lineup_Meadow_L10.jpg`: all six at level 10.
- `levels_Spud.jpg`: Spud at levels 1, 2, 4, 6, 8 and 10.
- `turn_<Id>.jpg`: each potato from the front, right, back and left.
- `clip_<Clip>.jpg`: six frames of each clip.
- `potato_clips_Meadow.mp4`: all six playing every clip.
