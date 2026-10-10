# FOLK VALLEY [RUN]: weapon models

All 61 of the hunters' cosmetic weapons, remade in Blender, plus six new **Mythics**: two swords, two daggers and two hammers. They keep the old models' structure, so they drop into the game unchanged. BanHammer is left alone.

![Swords](previews/sheet_swords_hero.png)
![Daggers](previews/sheet_daggers_hero.png)
![Hammers](previews/sheet_hammers_hero.png)
![Mythics](previews/sheet_mythics_hero.png)

| Preview | What it shows |
|---|---|
| `previews/sheet_<class>_hero.png` | every weapon in a class at the same scale (swords, daggers, hammers, mythics) |
| `previews/ba_<class>.png` | each old model next to its remake, under the same lights |
| `previews/sheet_<class>_hand.png` | each one held by a 5-stud R6 avatar |
| `previews/sheet_<class>_phone.png` | a whole class 60 studs from a 70° Roblox camera, framed like a phone screen |
| `previews/hero/` | one image per weapon |

## The six Mythics

| Id | Name | Class | Look |
|---|---|---|---|
| PhoenixBlade | Phoenix Blade | Sword | a giant phoenix feather: crimson blade with blazing edges and a glowing quill, flame-tipped wings for a guard, embers and loose feathers drifting around it |
| StarfallBlade | Starfall Blade | Sword | a blade cut from the night sky: navy steel full of glowing stars, a cyan edge, a gold north-star guard with comet quillons, a little ringed planet orbiting |
| UnicornHorn | Unicorn Horn | Dagger | a spiralled pearl horn wound with a glowing pink stripe, a glowing tip, a gold crown with heart gems, white wings, sparkles and hearts floating around it |
| Moonfang | Moonfang | Dagger | a moon-silver fang with a soft moonlight edge, rising out of a cratered crescent moon that holds a violet star |
| MeteorSmash | Meteor Smash | Hammer | a cratered space rock with glowing cracks, gripped in gold claws, trailing a tail of blue-white star fire, with little meteorites orbiting |
| KrakenAnchor | Kraken Anchor | Hammer | a gold ship's anchor with glowing trident flukes and barnacles, a kraken tentacle with glowing suckers coiled round it, a rope grip and the anchor ring for a pommel |

Mythic is a new rarity, a step above Legendary: two Neon colours, the biggest silhouette in its class, bits floating around it and an Fx attachment. **The game's weapon list needs entries for these six Ids (and the "Mythic" rarity) before players can get them.** The models don't add themselves.

## Put them in Studio

New meshes have to be uploaded to Roblox by your account, and Studio does that while it imports them. A `.rbxm` file can't carry new mesh files, so getting them in takes one import and one script:

1. **File → Import 3D →** `out/FolkValley_Weapons.fbx` **→ Import.** The default settings are fine. Leave "Merge Meshes" off.
   - The file has 284 meshes (all 67 weapons), so the upload takes a minute or two.
2. **View → Command Bar:** paste all of `out/BuildWeapons.lua` and press Enter.
   - It builds `ServerStorage.Weapons` with one Model per weapon. If a `Weapons` folder is already there, the new one is called `Weapons (new)`.
   - It then deletes the imported model. Ctrl+Z undoes everything.
3. Right-click the folder **→ Save to File…** to get the `.rbxm`, or drag it to wherever the game keeps its weapons. BanHammer is not included, so copy it over from the old folder.

The script reads four small marker cubes in the FBX to work out the importer's scale and orientation. Whatever import settings you use, every part ends up at the right size and position.

## How each weapon is built (unchanged contract)

- One Model per weapon, named by its Id.
- `PrimaryPart` is a Part named **Handle**:
  - 0.4 × 0.4 × 0.4 studs, Transparency 1.
  - Placed where the hand grips.
  - The weapon points along its +Y, with the edge or hammer face toward +X and the thin side along Z.
- Every visible part is a MeshPart:
  - One mesh per colour, with a plain white material. Colour and Material are set on the part.
  - Named for what it is: Blade, Guard, Grip, Head, Glow…
  - Welded to the Handle with a WeldConstraint.
  - Anchored, CanCollide, CanTouch and CanQuery are false. Massless is true.
- Number attributes **Top** and **Bottom**: how far the model reaches above and below the Handle along Y.
- An Attachment named **Fx** under the Handle on Epic, Legendary, Limited and Mythic weapons, at the blade tip or hammer head.
- At most 8 parts including the Handle. Materials are only SmoothPlastic, Metal, Neon, Glass, Wood and Fabric, with no textures.
- Lengths stay in range: swords 4.7–6.4 studs, daggers 3.7–4.9, hammers 3.6–7.8. No remake is shorter or narrower than its old model by more than 0.02 studs. Several Legendaries grew by up to a fifth so they stand out.
- Triangles: 57 of the 67 are at 3,000 or fewer (2,103 on average). Rainbow Edge (3,083), Folk Fang (3,012), Thunder Hammer (3,020) and Tombstone Hammer (3,134) are just over. Pumpkin Smasher (4,004) keeps its rounder, more detailed pumpkin. Five Mythics run 3,244–4,616.

## Checks

- `blender/validate.py` builds every weapon and checks it against the contract above:
  - length within its class range; parts, names and materials allowed
  - Fx on the right rarities
  - no z-fighting: faces of two different parts lying in the same plane, which Roblox would flicker between
- `tools/mock_studio.py` runs `BuildWeapons.lua` against a small mock of the Roblox API, standing in for an imported FBX. It checks every resulting Model: Handle, welds, flags, attributes, Fx, and each part's size and position. It tries a plain import, a scaled one and a turned one.
- I couldn't open Roblox Studio from here. The first real import is the one thing still untested.

## Weapons

### Swords (24)

| Id | Name | Rarity | Parts | Triangles | Top | Bottom | Length |
|---|---|---|---|---|---|---|---|
| Wooden | Wooden Sword | Common | 3 | 1,464 | 4.16 | -1.05 | 5.21 |
| Steel | Steel Sword | Common | 4 | 1,284 | 4.40 | -0.97 | 5.37 |
| Baguette | Baguette | Common | 3 | 2,660 | 4.31 | -0.64 | 4.95 |
| PencilSword | Giant Pencil | Common | 5 | 1,342 | 4.64 | -0.67 | 5.31 |
| Katana | Katana | Uncommon | 5 | 2,386 | 4.74 | -1.00 | 5.74 |
| Cutlass | Cutlass | Uncommon | 3 | 1,654 | 3.92 | -0.98 | 4.90 |
| Rapier | Rapier | Uncommon | 3 | 1,834 | 4.52 | -1.06 | 5.58 |
| FishSlapper | Fish Slapper | Uncommon | 5 | 2,414 | 4.18 | -1.00 | 5.18 |
| ScissorBlade | Scissor Blade | Rare | 3 | 2,060 | 4.40 | -0.97 | 5.37 |
| Claymore | Claymore | Rare | 5 | 1,842 | 5.12 | -1.27 | 6.39 |
| Scimitar | Scimitar | Rare | 4 | 1,202 | 4.30 | -0.93 | 5.23 |
| ThornBlade | Thorn Blade | Rare | 4 | 2,526 | 4.32 | -1.20 | 5.52 |
| CrystalSword | Crystal Sword | Epic | 4 | 912 | 4.46 | -1.00 | 5.46 |
| LavaBlade | Lava Blade | Epic | 4 | 1,838 | 4.66 | -0.95 | 5.61 |
| IceBrand | Ice Brand | Epic | 4 | 2,616 | 4.46 | -1.04 | 5.50 |
| LaserBlade | Laser Blade | Epic | 4 | 1,964 | 4.58 | -0.96 | 5.54 |
| RainbowEdge | Rainbow Edge | Legendary | 7 | 3,083 | 5.18 | -1.10 | 6.28 |
| GoldenSword | Golden Sword | Legendary | 5 | 2,338 | 5.20 | -1.19 | 6.39 |
| VoidEdge | Void Edge | Legendary | 5 | 1,978 | 5.14 | -1.08 | 6.22 |
| PumpkinCarver | Pumpkin Carver | Limited | 5 | 2,666 | 4.42 | -1.11 | 5.53 |
| BoneSaber | Bone Saber | Limited | 4 | 2,982 | 4.28 | -1.00 | 5.28 |
| WitchBroom | Witch's Broom | Limited | 4 | 2,210 | 4.75 | -1.15 | 5.90 |
| PhoenixBlade | Phoenix Blade | Mythic | 5 | 4,616 | 5.24 | -1.13 | 6.37 |
| StarfallBlade | Starfall Blade | Mythic | 6 | 2,694 | 5.26 | -1.09 | 6.35 |

### Daggers (21)

| Id | Name | Rarity | Parts | Triangles | Top | Bottom | Length |
|---|---|---|---|---|---|---|---|
| ButterKnife | Butter Knife | Common | 3 | 728 | 3.00 | -0.80 | 3.80 |
| IronDagger | Iron Dagger | Common | 3 | 708 | 3.02 | -0.91 | 3.93 |
| Stiletto | Stiletto | Common | 3 | 1,120 | 3.20 | -0.97 | 4.17 |
| Screwdriver | Screwdriver | Common | 3 | 972 | 3.12 | -0.80 | 3.92 |
| Fork | Giant Fork | Common | 1 | 1,260 | 3.50 | -0.84 | 4.34 |
| Kunai | Kunai | Uncommon | 3 | 1,412 | 3.02 | -1.86 | 4.88 |
| Sai | Sai | Uncommon | 3 | 992 | 3.32 | -0.92 | 4.24 |
| Carrot | Carrot | Uncommon | 3 | 2,392 | 3.36 | -1.49 | 4.85 |
| StraightRazor | Straight Razor | Rare | 4 | 1,072 | 2.96 | -1.04 | 4.00 |
| Karambit | Karambit | Rare | 3 | 1,214 | 2.90 | -1.30 | 4.21 |
| Icicle | Icicle | Rare | 3 | 1,312 | 3.44 | -1.00 | 4.44 |
| FrostFang | Frost Fang | Epic | 4 | 1,226 | 3.20 | -0.98 | 4.18 |
| ToxicFang | Toxic Fang | Epic | 4 | 2,186 | 3.12 | -1.03 | 4.16 |
| EmberKnife | Ember Knife | Epic | 4 | 1,290 | 3.08 | -0.99 | 4.07 |
| FolkFang | Golden Folk Fang | Legendary | 6 | 3,012 | 3.88 | -0.98 | 4.86 |
| StarShard | Star Shard | Legendary | 4 | 938 | 3.78 | -1.10 | 4.88 |
| CandyCornDagger | Candy Corn Dagger | Limited | 4 | 1,768 | 3.24 | -0.92 | 4.16 |
| VampireFang | Vampire Fang | Limited | 4 | 1,714 | 3.02 | -0.92 | 3.94 |
| SpiderStinger | Spider Stinger | Limited | 5 | 2,024 | 3.20 | -0.97 | 4.17 |
| UnicornHorn | Unicorn Horn | Mythic | 6 | 4,570 | 3.88 | -0.99 | 4.87 |
| Moonfang | Moonfang | Mythic | 6 | 3,244 | 3.86 | -0.95 | 4.81 |

### Hammers (22)

| Id | Name | Rarity | Parts | Triangles | Top | Bottom | Length |
|---|---|---|---|---|---|---|---|
| Mallet | Wooden Mallet | Common | 4 | 1,692 | 2.98 | -0.80 | 3.79 |
| Gavel | Gavel | Common | 4 | 2,660 | 2.83 | -0.82 | 3.65 |
| FryingPan | Frying Pan | Common | 4 | 1,392 | 3.74 | -0.80 | 4.54 |
| Plunger | Plunger | Common | 3 | 1,472 | 3.12 | -0.80 | 3.92 |
| SqueakyHammer | Squeaky Hammer | Uncommon | 3 | 1,312 | 2.86 | -0.86 | 3.72 |
| Sledgehammer | Sledgehammer | Uncommon | 5 | 1,172 | 4.38 | -1.16 | 5.54 |
| MeatTenderizer | Meat Tenderizer | Uncommon | 4 | 1,146 | 2.82 | -1.00 | 3.82 |
| StopSign | Stop Sign | Uncommon | 4 | 2,152 | 3.82 | -1.06 | 4.88 |
| WarHammer | War Hammer | Rare | 5 | 1,868 | 5.12 | -1.37 | 6.49 |
| Lollipop | Giant Lollipop | Rare | 4 | 2,392 | 3.72 | -0.75 | 4.47 |
| AnvilHammer | Anvil on a Stick | Rare | 5 | 2,078 | 4.46 | -1.15 | 5.61 |
| GoldMallet | Gold Mallet | Rare | 6 | 2,948 | 2.98 | -0.80 | 3.78 |
| MagmaMaul | Magma Maul | Epic | 4 | 2,714 | 4.94 | -1.40 | 6.34 |
| IceMallet | Ice Mallet | Epic | 5 | 2,742 | 2.88 | -0.98 | 3.85 |
| CrystalMaul | Crystal Maul | Epic | 5 | 1,692 | 5.52 | -1.22 | 6.74 |
| ThunderHammer | Thunder Hammer | Legendary | 5 | 3,020 | 6.42 | -1.22 | 7.64 |
| StarHammer | Star Hammer | Legendary | 4 | 2,122 | 6.00 | -1.34 | 7.34 |
| PumpkinSmasher | Pumpkin Smasher | Limited | 5 | 4,004 | 3.66 | -0.93 | 4.59 |
| CauldronMaul | Cauldron Maul | Limited | 5 | 2,892 | 4.88 | -1.15 | 6.03 |
| TombstoneHammer | Tombstone Hammer | Limited | 5 | 3,134 | 5.01 | -1.17 | 6.18 |
| MeteorSmash | Meteor Smash | Mythic | 6 | 4,366 | 6.42 | -1.32 | 7.75 |
| KrakenAnchor | Kraken Anchor | Mythic | 6 | 4,270 | 6.37 | -1.36 | 7.74 |

## Rebuild

Everything is generated from code:

- `blender/defs.py` holds one function per weapon, the display names and the weapon order.
- `blender/wlib.py` is the modelling toolkit:
  - ridged, banded and fullered blades, katana and saber blades
  - spiral leather wraps, wheel pommels, chamfered crossguards
  - lathes, sweeps and slabs, 3D text, faceted stars
  - boolean carving, and slabs that bend over curved surfaces
- `blender/build.py` builds the weapons, renders tiles and exports the FBX.
- `blender/validate.py` checks the contract (see Checks).
- `tools/gen_rig.py` writes `BuildWeapons.lua` from `weapons.json`, and `tools/mock_studio.py` dry-runs it.
- `blender/present.py` renders the review sheets.
- `blender/render_original.py` renders the old `.rbxm` models, rebuilding their Unions from the source parts stored inside them. It uses `tools/rbxtool`, a small Rust converter between `.rbxm` and JSON.

```sh
python3 -m venv .venv && .venv/bin/pip install bpy==5.2.2 pillow lupa
.venv/bin/python blender/validate.py
.venv/bin/python blender/build.py /tmp/w --no-render --fbx=$PWD/out/FolkValley_Weapons.fbx
cp /tmp/w/weapons.json out/ && python3 tools/gen_rig.py out/weapons.json out/BuildWeapons.lua
.venv/bin/python tools/mock_studio.py out/BuildWeapons.lua out/weapons.json
.venv/bin/python blender/present.py /tmp/p
```
