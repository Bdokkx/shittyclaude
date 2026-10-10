"""Weapon designs. Each function receives a wlib.Weapon and fills in its parts.

Roblox space, relative to the Handle (the hand grips at the origin):
  +Y up the weapon, +X the cutting edge / hammer face, Z the thin side.
"""
import math

from mathutils import Vector

from wlib import (R, S, T, arc_pts, bar_x, bar_y, blade, box, catmull, circle_pts, cylinder, helix_ribbon, ico,
                  banded_blade, bat_wing_pts, blade_face_z, bolt_pts, crescent_pts, face_inlay, fuller_blade, hex_rmod,
                  katana_blade, lathe, leaf_pts, lerp, octagon_pts, profile_blade, puff, pyramid, ring_slab, rock,
                  rounded_rect_pts, saber_blade, slab, slab_holes, sphere, spiral_band_pts, split_by_tag, star_pts,
                  surface_vein, sweep, sweep_band, sword_blade, teardrop, text_slab, torus, wheel_pommel, wrapped_grip,
                  capsule, loft, merge_into, snowflake, boolean, projected_slab, star3d, drop_facing, xform)

WEAPONS = {}

# display names from the game's weapon list
NAMES = {
    "Wooden": "Wooden Sword", "Steel": "Steel Sword", "Baguette": "Baguette", "PencilSword": "Giant Pencil",
    "Katana": "Katana", "Cutlass": "Cutlass", "Rapier": "Rapier", "FishSlapper": "Fish Slapper",
    "ScissorBlade": "Scissor Blade", "Claymore": "Claymore", "Scimitar": "Scimitar", "ThornBlade": "Thorn Blade",
    "CrystalSword": "Crystal Sword", "LavaBlade": "Lava Blade", "IceBrand": "Ice Brand", "LaserBlade": "Laser Blade",
    "RainbowEdge": "Rainbow Edge", "GoldenSword": "Golden Sword", "VoidEdge": "Void Edge",
    "PumpkinCarver": "Pumpkin Carver", "BoneSaber": "Bone Saber", "WitchBroom": "Witch's Broom",
    "ButterKnife": "Butter Knife", "IronDagger": "Iron Dagger", "Stiletto": "Stiletto", "Screwdriver": "Screwdriver",
    "Fork": "Giant Fork", "Kunai": "Kunai", "Sai": "Sai", "Carrot": "Carrot", "StraightRazor": "Straight Razor",
    "Karambit": "Karambit", "Icicle": "Icicle", "FrostFang": "Frost Fang", "ToxicFang": "Toxic Fang",
    "EmberKnife": "Ember Knife", "FolkFang": "Golden Folk Fang", "StarShard": "Star Shard",
    "CandyCornDagger": "Candy Corn Dagger", "VampireFang": "Vampire Fang", "SpiderStinger": "Spider Stinger",
    "Mallet": "Wooden Mallet", "Gavel": "Gavel", "FryingPan": "Frying Pan", "Plunger": "Plunger",
    "SqueakyHammer": "Squeaky Hammer", "Sledgehammer": "Sledgehammer", "MeatTenderizer": "Meat Tenderizer",
    "StopSign": "Stop Sign", "WarHammer": "War Hammer", "Lollipop": "Giant Lollipop", "AnvilHammer": "Anvil on a Stick",
    "GoldMallet": "Gold Mallet", "MagmaMaul": "Magma Maul", "IceMallet": "Ice Mallet", "CrystalMaul": "Crystal Maul",
    "ThunderHammer": "Thunder Hammer", "StarHammer": "Star Hammer", "PumpkinSmasher": "Pumpkin Smasher",
    "CauldronMaul": "Cauldron Maul", "TombstoneHammer": "Tombstone Hammer",
    "PhoenixBlade": "Phoenix Blade", "StarfallBlade": "Starfall Blade", "UnicornHorn": "Unicorn Horn",
    "Moonfang": "Moonfang", "MeteorSmash": "Meteor Smash", "KrakenAnchor": "Kraken Anchor",
}


# the order of the game's weapon list (sheets, the FBX layout and the rig follow it), Mythics last in each class
ORDER = [
    "Wooden", "Steel", "Baguette", "PencilSword", "Katana", "Cutlass", "Rapier", "FishSlapper", "ScissorBlade",
    "Claymore", "Scimitar", "ThornBlade", "CrystalSword", "LavaBlade", "IceBrand", "LaserBlade", "RainbowEdge",
    "GoldenSword", "VoidEdge", "PumpkinCarver", "BoneSaber", "WitchBroom", "PhoenixBlade", "StarfallBlade",
    "ButterKnife", "IronDagger", "Stiletto", "Screwdriver", "Fork", "Kunai", "Sai", "Carrot", "StraightRazor",
    "Karambit", "Icicle", "FrostFang", "ToxicFang", "EmberKnife", "FolkFang", "StarShard", "CandyCornDagger",
    "VampireFang", "SpiderStinger", "UnicornHorn", "Moonfang",
    "Mallet", "Gavel", "FryingPan", "Plunger", "SqueakyHammer", "Sledgehammer", "MeatTenderizer", "StopSign",
    "WarHammer", "Lollipop", "AnvilHammer", "GoldMallet", "MagmaMaul", "IceMallet", "CrystalMaul", "ThunderHammer",
    "StarHammer", "PumpkinSmasher", "CauldronMaul", "TombstoneHammer", "MeteorSmash", "KrakenAnchor",
]


def weapon(wid, rarity, kind):
    def deco(fn):
        WEAPONS[wid] = (rarity, kind, fn)
        return fn
    return deco


# ---------------------------------------------------------------- shared hilt pieces

def ringed_grip(y0, y1, r, rings=3, bump=0.025, segs=20):
    """Grip along Y with soft raised rings."""
    prof = [(0, y0), (r * 0.9, y0), (r, y0 + 0.03)]
    n = rings * 2 + 1
    for i in range(1, n):
        y = lerp(y0 + 0.03, y1 - 0.03, i / n)
        prof.append((r + (bump if i % 2 else 0.0), y))
    prof += [(r, y1 - 0.03), (r * 0.9, y1), (0, y1)]
    return lathe(prof, segs=segs)


def knob(y_center, r, squash=1.0, segs=20):
    """Round pommel knob centred on y_center."""
    prof = [(0, y_center - r * squash)]
    for i in range(1, 8):
        a = -90 + 180 * i / 8
        import math
        prof.append((r * math.cos(math.radians(a)), y_center + r * squash * math.sin(math.radians(a))))
    prof.append((0, y_center + r * squash))
    return lathe(prof, segs=segs)


# ================================================================ SWORDS

@weapon("Wooden", "Common", "Sword")
def wooden(w):
    """Ash practice sword with walnut fittings, like a real wooden arming sword."""
    blade_p = w.part("Blade", (226, 204, 160), "Wood", smooth=12)
    fit = w.part("Fittings", (104, 62, 36), "Wood")
    grip = w.part("Grip", (118, 64, 34), "Fabric", smooth=70)
    blade_p.add(sword_blade(0.60, 3.26, 4.16, w0=0.31, w1=0.27, h0=0.13, h1=0.105, ef=0.02,
                            point_curve=0.30, n_point=6))
    # straight crossguard, square section, chamfered, with squared flared ends
    fit.add(bar_x([(-0.80, 0.18, 0.20), (-0.77, 0.24, 0.27), (-0.62, 0.21, 0.24), (-0.19, 0.20, 0.23),
                   (-0.15, 0.27, 0.31), (0.15, 0.27, 0.31), (0.19, 0.20, 0.23), (0.62, 0.21, 0.24),
                   (0.77, 0.24, 0.27), (0.80, 0.18, 0.20)], chamfer=0.05, y=0.60))
    grip.add(wrapped_grip(-0.50, 0.50, 0.125, 0.14, pitch=0.21, amp=0.024, around=14, sz=0.9))
    grip.add(cylinder(0.13, 0.05, segs=14), T(0, -0.50, 0))
    fit.add(cylinder(0.085, 0.14, segs=12), T(0, -0.55, 0))
    fit.add(wheel_pommel(-0.78, 0.27, 0.095, 0.15, 0.045))


@weapon("Katana", "Uncommon", "Sword")
def katana(w):
    """Curved katana: steel blade with a wavy white hamon edge, gold habaki / lobed
    tsuba / collar / end cap, red cord wrap in diamonds over cream rayskin."""
    steel = w.part("Blade", (190, 198, 216), "Metal", smooth=14)
    hamon = w.part("Hamon", (246, 249, 255), "SmoothPlastic", smooth=14)
    fit = w.part("Fittings", (238, 184, 54), "Metal")
    cord = w.part("Wrap", (204, 36, 44), "Fabric", smooth=55)
    ray = w.part("Grip", (238, 230, 210), "SmoothPlastic", smooth=55)
    b = katana_blade(0.50, 4.74, w0=0.50, w1=0.41, h0=0.085, h1=0.066, sori=0.30, kissaki=0.60, x0=-0.22)
    parts = split_by_tag(b, {0: "body", -1: "body", 1: "hamon"})
    steel.add(parts["body"])
    hamon.add(parts["hamon"])
    # habaki: tapered gold collar around the blade base
    fit.add(bar_y([(0.49, 0.56, 0.23, 0.05), (0.66, 0.54, 0.21, 0.05), (0.80, 0.51, 0.18, 0.045)], x=0.03))
    # tsuba: lobed (mokko) guard with a raised rim, plus thin seppa spacers
    lobes = lambda a: 1 + 0.075 * math.cos(4 * a)
    fit.add(lathe([(0, 0.395), (0.33, 0.395), (0.36, 0.375), (0.42, 0.375), (0.455, 0.40), (0.455, 0.47),
                   (0.42, 0.495), (0.36, 0.495), (0.33, 0.475), (0, 0.475)], segs=32, sz=0.9, rmod=lobes))
    fit.add(lathe([(0, 0.35), (0.22, 0.35), (0.235, 0.36), (0.235, 0.375), (0, 0.375)], segs=24, sz=0.78))
    fit.add(lathe([(0, 0.495), (0.235, 0.495), (0.235, 0.51), (0.22, 0.52), (0, 0.52)], segs=24, sz=0.78))
    # fuchi collar and kashira end cap
    fit.add(lathe([(0, 0.24), (0.175, 0.24), (0.19, 0.255), (0.19, 0.335), (0.18, 0.35), (0, 0.35)],
                  segs=24, sz=0.8))
    fit.add(lathe([(0, -1.00), (0.10, -0.995), (0.16, -0.975), (0.185, -0.945), (0.19, -0.90), (0.18, -0.86),
                   (0, -0.86)], segs=24, sz=0.8))
    # tsuka: red cord-wrapped oval grip with a row of cream rayskin diamonds on each face
    rx, rz = 0.17, 0.122
    cord.add(lathe([(0, -0.88), (rx, -0.88), (rx - 0.008, -0.31), (rx, 0.25), (0, 0.25)], segs=20, sz=rz / rx))
    diamond = [(0, -0.115), (0.118, 0), (0, 0.115), (-0.118, 0)]
    for cy in (-0.69, -0.41, -0.13, 0.15):
        for side in (1, -1):
            ray.add(face_inlay(diamond, cy, rx, rz, t=0.03, side=side))
    w.smooth_angle = 30.0


def _clamp_to_face(points, stations, margin=0.012):
    out = []
    for x, y in points:
        st = min(stations, key=lambda s_: abs(s_[0] - y))
        inner = st[1] - st[3] - margin
        out.append((max(-inner, min(inner, x)), y))
    return out


@weapon("LavaBlade", "Epic", "Sword")
def lava_blade(w):
    """Glossy obsidian blade with a molten edge and branching lava cracks, rock
    horn guard with a magma gem, charred leather grip, magma orb in claws."""
    obs = w.part("Obsidian", (46, 32, 40), "Metal", smooth=14)
    lava = w.part("Lava", (255, 98, 18), "Neon")
    core = w.part("Core", (255, 216, 92), "Neon")
    grip = w.part("Grip", (56, 36, 30), "Fabric", smooth=70)
    def base_w(y):
        return lerp(0.30, 0.36, smooth01((y - 0.62) / 1.9)) if y < 2.5 else lerp(0.36, 0.27, (y - 2.5) / 1.2)

    # flame-tooth serrations: each tooth widens toward the tip, then steps back in
    st = [(0.62, base_w(0.62) * 0.86, 0.125, 0.07)]
    y, tooth = 0.70, 0.56
    while y + tooth < 3.62:
        st.append((y, base_w(y) * 0.80, lerp(0.125, 0.10, (y - 0.62) / 3.1), 0.072))
        st.append((y + tooth - 0.04, base_w(y + tooth) * 1.0, lerp(0.125, 0.10, (y + tooth - 0.62) / 3.1), 0.08))
        y += tooth
    st.append((3.70, 0.26, 0.095, 0.07))
    b = profile_blade(st, 4.66, n_point=6, point_curve=0.25, ef=0.022)
    parts = split_by_tag(b, {0: "body", -1: "body", 1: "edge"})
    obs.add(parts["body"])
    lava.add(parts["edge"])
    crack = [(0.0, 0.70), (0.035, 1.05), (-0.03, 1.42), (0.04, 1.85), (-0.025, 2.28), (0.035, 2.72),
             (-0.01, 3.12), (0.0, 3.52)]
    branches = [[(0.035, 1.05), (0.12, 1.22), (0.17, 1.36), (0.25, 1.43)],
                [(-0.03, 1.42), (-0.12, 1.62), (-0.19, 1.74), (-0.26, 1.80)],
                [(0.04, 1.85), (0.13, 2.02), (0.20, 2.12), (0.27, 2.18)],
                [(-0.025, 2.28), (-0.13, 2.45), (-0.21, 2.56), (-0.28, 2.62)],
                [(0.035, 2.72), (0.12, 2.90), (0.19, 3.00), (0.25, 3.06)]]
    for side in (1, -1):
        lava.add(surface_vein(crack, 0.06, st, side=side, lift=0.004, taper=False))
        for br in branches:
            lava.add(surface_vein(_clamp_to_face(br, st), 0.042, st, side=side, lift=0.004))
        core.add(surface_vein(crack[:-1], 0.022, st, side=side, lift=0.012, taper=False))
    # guard: faceted rock block with two horns sweeping up like flames
    obs.add(rock(0.26, seed=3, jitter=0.10, subdiv=1, scale=(1.55, 0.78, 0.9)), T(0, 0.60, 0))
    for sx in (1, -1):
        path = [Vector((sx * x, y, 0)) for x, y in ((0.22, 0.58), (0.50, 0.64), (0.73, 0.80), (0.87, 1.04),
                                                    (0.93, 1.32))]
        obs.add(sweep(path, [0.30, 0.25, 0.19, 0.12, 0.0], [0.30, 0.24, 0.18, 0.11, 0.0], sides=6))
    core.add(ico(0.125, subdiv=1, scale=(1.0, 1.25, 2.1)), T(0, 0.60, 0))
    # charred leather grip
    grip.add(wrapped_grip(-0.54, 0.42, 0.13, 0.145, pitch=0.21, amp=0.022, around=14, sz=0.9))
    # pommel: obsidian collar and three claws holding a magma orb
    obs.add(lathe([(0, -0.62), (0.15, -0.62), (0.17, -0.58), (0.15, -0.53), (0, -0.53)], segs=8))
    core.add(sphere(0.155, segs=14, rings=10), T(0, -0.78, 0))
    for k in range(3):
        a = math.radians(90 + 120 * k)
        ca, sa = math.cos(a), math.sin(a)
        path = [Vector((r * ca, y, r * sa)) for r, y in ((0.10, -0.60), (0.19, -0.70), (0.185, -0.84),
                                                         (0.10, -0.95))]
        obs.add(sweep(path, [0.10, 0.085, 0.06, 0.0], [0.08, 0.07, 0.05, 0.0], sides=5))
    w.fx = (0, 4.50, 0)


def smooth01(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


RAINBOW = [("Red", (236, 50, 62)), ("Orange", (255, 138, 34)), ("Yellow", (255, 212, 46)),
           ("Green", (64, 200, 92)), ("Blue", (58, 138, 244))]


@weapon("RainbowEdge", "Legendary", "Sword")
def rainbow_edge(w):
    """Broad hero sword: five rainbow chevron bands with a glowing white Neon edge
    and tip, a puffy white cloud guard and grip, a star pommel and Neon sparkles
    floating around the blade."""
    bands = [w.part("Blade" + n, c, "SmoothPlastic", smooth=14) for n, c in RAINBOW]
    glow = w.part("Glow", (255, 255, 255), "Neon")
    cloud = w.part("Cloud", (250, 251, 255), "SmoothPlastic", smooth=60)

    def wfun(y):
        if y < 2.6:
            return lerp(0.33, 0.42, smooth01((y - 0.80) / 1.8))
        return lerp(0.42, 0.36, (y - 2.6) / 1.0)

    def hfun(y):
        return lerp(0.13, 0.095, (y - 0.8) / 3.0)

    b = banded_blade(0.80, 5.18, wfun, hfun, bounds=[1.52, 2.26, 3.00, 3.74, 4.40], slope=0.75,
                     groove=0.04, inset=0.80, y_shoulder=3.62, n_point=8, edge_band=0.07)
    mapping = {i: str(i) for i in range(6)}
    mapping[100] = "edge"
    parts = split_by_tag(b, mapping)
    for i in range(5):
        bands[i].add(parts[str(i)])
    glow.add(parts["5"])      # glowing tip
    glow.add(parts["edge"])   # glowing cutting edges
    # puffy cloud guard (blade base sits inside it)
    for x, y, r, sc in ((0.0, 0.70, 0.29, (1.2, 0.86, 0.66)), (0.37, 0.64, 0.23, (1.1, 0.85, 0.64)),
                        (-0.37, 0.64, 0.23, (1.1, 0.85, 0.64)), (0.65, 0.70, 0.16, (1.05, 0.95, 0.62)),
                        (-0.65, 0.70, 0.16, (1.05, 0.95, 0.62)), (0.20, 0.86, 0.17, (1.1, 0.9, 0.62)),
                        (-0.20, 0.86, 0.17, (1.1, 0.9, 0.62)), (0.86, 0.74, 0.13, (1.05, 0.95, 0.62)),
                        (-0.86, 0.74, 0.13, (1.05, 0.95, 0.62))):
        cloud.add(puff(r, sc, segs=12 if r > 0.15 else 10, rings=8 if r > 0.15 else 6), T(x, y, 0))
    cloud.add(wrapped_grip(-0.56, 0.48, 0.13, 0.145, pitch=0.21, amp=0.02, around=14, sz=0.9))
    cloud.add(puff(0.12, (1.2, 0.8, 1.0), segs=12, rings=7), T(0, -0.60, 0))
    # star pommel (yellow band colour)
    bands[2].add(slab(star_pts(5, 0.27, 0.12), 0.14, 0.04, seg=2), T(0, -0.88, 0))
    # glowing sparkles floating around the blade
    sparkle = slab(star_pts(4, 0.17, 0.055, rot=90), 0.07, 0.022, seg=1)
    for x, y, z, rz_ in ((0.74, 1.95, 0.10, 12), (-0.76, 2.85, -0.08, -10), (0.70, 3.80, -0.12, 20),
                         (-0.60, 4.55, 0.10, -15)):
        glow.add(sparkle, T(x, y, z) @ R("Z", rz_))
    w.fx = (0, 5.0, 0)



# ================================================================ DAGGERS

@weapon("FolkFang", "Legendary", "Dagger")
def folk_fang(w):
    """Golden Folk Fang: a big curved golden wolf fang held in a navy paw (pink toe
    beans, gold claws, a red gem as the palm pad), gold-banded navy grip, gem pommel
    and two glowing paw prints floating beside the blade."""
    gold = w.part("Fang", (255, 196, 52), "Metal", smooth=50)
    shine = w.part("Shine", (255, 240, 160), "Neon")
    paw = w.part("Paw", (36, 50, 120), "SmoothPlastic", smooth=50)
    beans = w.part("Beans", (255, 150, 184), "SmoothPlastic", smooth=60)
    gem = w.part("Gem", (255, 40, 72), "Neon")
    wrap = w.part("Grip", (32, 42, 104), "Fabric", smooth=70)
    # the fang: a curved, swelling cone rising from between the toes, sweeping back toward -X
    key = [(0.02, 0.80), (0.05, 1.44), (0.0, 2.13), (-0.11, 2.82), (-0.27, 3.38), (-0.44, 3.88)]
    path = [Vector((x, y, 0)) for x, y in catmull(key, samples=3)]
    n = len(path)
    widths = [lerp(0.70, 0.0, (i / (n - 1)) ** 1.2) * (1 + 0.14 * math.sin(math.pi * min(i / (n - 1) * 2.2, 1)))
              for i in range(n)]
    thicks = [v * 0.62 for v in widths]
    widths[-1] = thicks[-1] = 0.0
    gold.add(sweep(path, widths, thicks, sides=12))
    # cartoon highlight streaks down both faces
    a, b = int(n * 0.14), int(n * 0.84)
    for p0, p1 in ((22, 62), (-62, -22)):
        shine.add(sweep_band(path[a:b], widths[a:b], thicks[a:b], p0, p1, lift=0.004, rise=0.012))
    # the paw: palm below, four toes in an arc above holding the fang's root
    pc = 0.58
    palm = catmull([(0, -0.29), (0.33, -0.21), (0.43, 0.02), (0.30, 0.20), (0, 0.24), (-0.30, 0.20),
                    (-0.43, 0.02), (-0.33, -0.21)], samples=3, closed=True)
    paw.add(slab(palm, 0.36, 0.10, seg=2), T(0, pc, 0))
    toe = circle_pts(0.16, n=12, sx=0.9)
    for ang in (150, 111, 69, 30):
        ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        cx, cy = 0.40 * ca, pc + 0.36 * sa
        paw.add(slab(toe, 0.44, 0.10, seg=1), T(cx, cy, 0) @ R("Z", ang - 90))
        for side in (1, -1):
            beans.add(sphere(0.085, segs=8, rings=5, scale=(1.0, 0.9, 0.45)), T(cx, cy + 0.01, side * 0.215))
        base = Vector((cx + 0.12 * ca, cy + 0.12 * sa, 0))
        d = Vector((ca, sa + 0.35, 0)).normalized()
        claw = [base, base + d * 0.10 + Vector((0, 0.01, 0)), base + d * 0.19 + Vector((0, 0.05, 0))]
        gold.add(sweep(claw, [0.10, 0.065, 0.0], [0.08, 0.05, 0.0], sides=6))
    gem.add(lathe([(0, -0.25), (0.14, -0.15), (0.17, 0.0), (0.14, 0.15), (0, 0.25)], segs=8, sx=1.2),
            T(0, pc - 0.03, 0) @ R("X", 90))
    # navy grip between gold bands, gold cup pommel with a gem
    wrap.add(wrapped_grip(-0.58, 0.30, 0.13, 0.142, pitch=0.22, amp=0.02, around=12, sz=0.9))
    gold.add(lathe([(0, 0.27), (0.155, 0.27), (0.17, 0.29), (0.17, 0.34), (0.155, 0.36), (0, 0.36)], segs=14))
    gold.add(lathe([(0, -0.80), (0.10, -0.80), (0.17, -0.70), (0.175, -0.62), (0.16, -0.56), (0, -0.56)],
                   segs=14))
    gem.add(lathe([(0, -0.17), (0.10, -0.10), (0.12, 0.0), (0.10, 0.10), (0, 0.17)], segs=8),
            T(0, -0.86, 0) @ R("X", 90))
    # two glowing paw prints floating beside the fang (Neon is unlit: no bevels needed)
    for (x, y, z, rot, sc) in ((0.68, 2.15, 0.08, 18, 1.0), (-0.72, 3.00, -0.06, -24, 0.85)):
        m = T(x, y, z) @ R("Z", rot) @ S(sc)
        shine.add(slab(catmull([(0, -0.09), (0.11, -0.05), (0.10, 0.06), (0, 0.08), (-0.10, 0.06),
                                (-0.11, -0.05)], samples=2, closed=True), 0.05, 0.0), m)
        for tx, ty in ((-0.12, 0.13), (-0.045, 0.19), (0.045, 0.19), (0.12, 0.13)):
            shine.add(slab(circle_pts(0.045, n=8), 0.05, 0.0), m @ T(tx, ty, 0))
    w.fx = (-0.40, 3.74, 0)


# ================================================================ HAMMERS

@weapon("ThunderHammer", "Legendary", "Hammer")
def thunder_hammer(w):
    """Winged thunder hammer: chamfered gold head with blue steel faces and a big
    glowing lightning bolt on each side, white feathered wings, blue shaft with gold
    rings, white leather grip, gem pommel and sparks floating around the head."""
    gold = w.part("Head", (255, 200, 56), "Metal")
    trim = w.part("Trim", (46, 92, 210), "Metal")
    bolt = w.part("Bolt", (70, 224, 255), "Neon")
    wings = w.part("Wings", (248, 250, 255), "SmoothPlastic", smooth=40)
    grip = w.part("Grip", (246, 246, 250), "Fabric", smooth=70)
    hy = 4.36
    gold.add(bar_x([(-1.10, 0.98, 0.94, 0.12), (-0.96, 1.18, 1.12, 0.15), (0.96, 1.18, 1.12, 0.15),
                    (1.10, 0.98, 0.94, 0.12)], y=hy))
    for sx in (1, -1):
        trim.add(bar_x([(1.06, 1.06, 1.00, 0.13), (1.22, 1.06, 1.00, 0.13), (1.31, 0.84, 0.78, 0.10)], y=hy),
                 S(sx, 1, 1))
    emblem = slab(bolt_pts(0.92), 0.08, 0.025, seg=2)
    bolt.add(emblem, T(0, hy, 0.575))
    bolt.add(emblem, T(0, hy, -0.575) @ R("Y", 180))
    # big feathered wings fanning up and out from the top of the head
    feathers = [(1.62, 0.42, -4, 0.0), (1.42, 0.41, -24, -0.045), (1.18, 0.39, -44, 0.045), (0.92, 0.36, -64, -0.02)]
    for sx in (1, -1):
        for L, W_, ang, dz in feathers:
            f = slab(leaf_pts(L, W_, n=5), 0.10, 0.035, seg=1)
            wings.add(f, S(sx, 1, 1) @ T(0.70, hy + 0.44, dz) @ R("Z", ang))
        # covert: a rounded wing base tying the feathers together
        wings.add(slab(leaf_pts(0.78, 0.62, n=6, tip_sharp=1.2), 0.16, 0.05, seg=1),
                  S(sx, 1, 1) @ T(0.64, hy + 0.40, 0.0) @ R("Z", -30))
    # sparks orbiting the head (Neon is unlit: no bevels needed)
    for x, y, z, rot, sc in ((0.0, hy + 1.30, 0.0, 10, 0.50), (1.85, hy + 0.10, 0.25, -25, 0.42),
                             (-1.85, hy - 0.55, -0.25, 155, 0.42)):
        bolt.add(slab(bolt_pts(sc), 0.06, 0.0), T(x, y, z) @ R("Z", rot))
    # shaft, collar, rings
    trim.add(bar_y([(hy - 0.80, 0.40, 0.40, 0.07), (hy - 0.56, 0.46, 0.46, 0.08)]))
    trim.add(cylinder(0.165, hy - 0.55 + 0.62, segs=20), T(0, (hy - 0.55 - 0.62) / 2, 0))
    for ry in (1.25, 2.20, 3.15):
        gold.add(lathe([(0, ry - 0.07), (0.2, ry - 0.07), (0.215, ry - 0.045), (0.215, ry + 0.045),
                        (0.2, ry + 0.07), (0, ry + 0.07)], segs=16))
    grip.add(wrapped_grip(-0.64, 0.64, 0.165, 0.175, pitch=0.22, amp=0.022, around=12, sz=1.0))
    gold.add(lathe([(0, 0.62), (0.19, 0.62), (0.205, 0.65), (0.205, 0.70), (0.19, 0.72), (0, 0.72)], segs=16))
    # pommel: gold knob with a glowing gem
    gold.add(lathe([(0, -1.02), (0.11, -1.02), (0.20, -0.92), (0.22, -0.80), (0.19, -0.68), (0.17, -0.64),
                    (0, -0.64)], segs=16))
    bolt.add(ico(0.12, subdiv=1, scale=(1.0, 1.2, 1.0)), T(0, -1.10, 0))
    w.fx = (0, hy, 0)



# ================================================================ SWORDS: commons and uncommons

def knob_pommel(cy, r=0.17, h=0.30, segs=8, flat=0.35):
    """Faceted pommel (8 sides by default) centred on cy."""
    return lathe([(0, cy - h / 2), (r * 0.55, cy - h / 2), (r, cy - h * flat / 2 - 0.02), (r, cy + h * flat / 2),
                  (r * 0.7, cy + h / 2 - 0.01), (r * 0.45, cy + h / 2), (0, cy + h / 2)], segs=segs)


@weapon("Steel", "Common", "Sword")
def steel(w):
    """Classic steel arming sword: broad blade with a darker fuller down the middle,
    dark steel crossguard with ball ends, brown leather wrap, faceted pommel."""
    blade_p = w.part("Blade", (216, 222, 234), "Metal", smooth=14)
    fuller = w.part("Fuller", (150, 160, 182), "Metal", smooth=14)
    hilt = w.part("Hilt", (84, 90, 110), "Metal")
    grip = w.part("Grip", (112, 66, 38), "Fabric", smooth=70)
    st = [(0.62, 0.335, 0.115, 0.0, 0.105, 0.05), (2.10, 0.315, 0.11, 0.0, 0.10, 0.048),
          (3.50, 0.28, 0.10, 0.0, 0.08, 0.04)]
    b = fuller_blade(st, 4.40, n_point=6, point_curve=0.28)
    parts = split_by_tag(b, {0: "body", 1: "body", -1: "body", 3: "fuller"})
    blade_p.add(parts["body"])
    fuller.add(parts["fuller"])
    hilt.add(bar_x([(-0.82, 0.20, 0.22), (0.82, 0.20, 0.22)], chamfer=0.055, y=0.56))
    for sx in (1, -1):
        hilt.add(sphere(0.15, 14, 9), T(sx * 0.88, 0.56, 0))
    hilt.add(bar_y([(0.46, 0.36, 0.28, 0.06), (0.68, 0.40, 0.30, 0.06)]))
    grip.add(wrapped_grip(-0.56, 0.47, 0.135, 0.15, pitch=0.22, amp=0.022, sz=0.9))
    hilt.add(cylinder(0.095, 0.10, segs=10), T(0, -0.60, 0))
    hilt.add(knob_pommel(-0.80, r=0.22, h=0.34, segs=8))


@weapon("Baguette", "Common", "Sword")
def baguette(w):
    """A crusty French baguette in a paper wrap, with lighter slashes along its top."""
    bread = w.part("Bread", (212, 146, 66), "SmoothPlastic", smooth=50)
    scores = w.part("Scores", (246, 214, 150), "SmoothPlastic", smooth=50)
    wrap = w.part("Wrap", (244, 240, 228), "Fabric", smooth=40)
    rx, rz = 0.36, 0.31
    prof = [(0, -0.45), (0.30, -0.45), (rx, -0.30), (rx, 3.70), (0.34, 3.98), (0.27, 4.16), (0.15, 4.28), (0, 4.31)]
    bread.add(lathe(prof, segs=20, sz=rz / rx))
    leaf = leaf_pts(0.58, 0.15, n=6, tip_sharp=1.3)
    for k, cy in enumerate((0.95, 1.55, 2.15, 2.75, 3.35)):
        rot = [(x * math.cos(math.radians(-38)) - (y - 0.29) * math.sin(math.radians(-38)),
                x * math.sin(math.radians(-38)) + (y - 0.29) * math.cos(math.radians(-38))) for x, y in leaf]
        scores.add(face_inlay(rot, cy, rx, rz, t=0.05, side=1, sink=0.012, bevel=0.012))
        scores.add(face_inlay(rot, cy + 0.3, rx, rz, t=0.05, side=-1, sink=0.012, bevel=0.012))
    # paper sleeve with a torn zig-zag top edge
    n = 24
    rings = []
    for y, r, zig in ((-0.64, 0.385, 0.0), (0.40, 0.40, 0.0), (0.56, 0.405, 1.0)):
        ring = []
        for i in range(n):
            a = math.tau * i / n
            yy = y + (0.06 if i % 2 else -0.02) * zig
            ring.append(Vector((r * math.cos(a), yy, r * (rz / rx + 0.08) * math.sin(a))))
        rings.append(ring)
    from wlib import loft as _loft
    wrap.add(_loft(rings, cap_start=True, cap_end=True))


@weapon("PencilSword", "Common", "Sword")
def pencil_sword(w):
    """Giant yellow pencil: hexagonal barrel, sharpened wood cone with a graphite
    point, metal ferrule and a pink eraser at the end you hold."""
    barrel = w.part("Barrel", (255, 202, 40), "SmoothPlastic", smooth=35)
    wood = w.part("Wood", (238, 204, 156), "Wood", smooth=35)
    lead = w.part("Lead", (54, 54, 62), "SmoothPlastic", smooth=35)
    ferrule = w.part("Ferrule", (192, 198, 210), "Metal", smooth=35)
    eraser = w.part("Eraser", (255, 140, 178), "SmoothPlastic", smooth=50)
    R_ = 0.29
    hexf = hex_rmod(0.05)
    y_base, y_apex, r_base = 3.42, 4.42, 0.335      # sharpened cone: radius r_base at y_base, 0 at y_apex
    n = 36
    from wlib import loft as _loft
    rings = []
    for y_of in (lambda a: -0.10, lambda a: 3.40,
                 lambda a: y_apex - R_ * hexf(a) * (y_apex - y_base) / r_base):
        rings.append([Vector((R_ * hexf(math.tau * i / n) * math.cos(math.tau * i / n), y_of(math.tau * i / n),
                              R_ * hexf(math.tau * i / n) * math.sin(math.tau * i / n))) for i in range(n)])
    rings.append([Vector((0, 3.40, 0))])
    barrel.add(_loft(rings, cap_start=True, cap_end=False))
    wood.add(lathe([(0, 3.40), (r_base, 3.40), (r_base, y_base), (0.085, 4.17), (0, 4.19)], segs=24))
    lead.add(lathe([(0, 4.12), (0.092, 4.12), (0.086, 4.17), (0.0, 4.64)], segs=14))
    prof = [(0, -0.36), (0.31, -0.36), (0.32, -0.33)]
    for k in range(4):
        y = -0.33 + k * 0.065
        prof += [(0.32, y + 0.012), (0.335, y + 0.03), (0.32, y + 0.05)]
    prof += [(0.32, -0.06), (0.31, -0.04), (0, -0.04)]
    ferrule.add(lathe(prof, segs=24))
    eraser.add(lathe([(0, -0.67), (0.20, -0.67), (0.27, -0.63), (0.29, -0.56), (0.29, -0.34), (0, -0.34)], segs=20))


@weapon("Cutlass", "Uncommon", "Sword")
def cutlass(w):
    """Pirate cutlass: broad curved steel blade with a clipped point, gold scallop
    shell guard with a knuckle bow, red leather grip."""
    blade_p = w.part("Blade", (214, 220, 232), "Metal", smooth=14)
    gold = w.part("Guard", (240, 186, 56), "Metal")
    grip = w.part("Grip", (150, 32, 34), "Fabric", smooth=70)
    blade_p.add(saber_blade(0.55, 3.92, w0=0.50, w1=0.64, h0=0.09, h1=0.07, curve=0.36, xb0=-0.27,
                            clip=0.95, tip_bias=0.18, n=20))
    shell = lambda a: 1 + 0.06 * math.cos(9 * a)
    gold.add(lathe([(0, 0.50), (0.15, 0.50), (0.45, 0.55), (0.56, 0.63), (0.60, 0.69), (0.54, 0.71),
                    (0.43, 0.63), (0.15, 0.58), (0, 0.58)], segs=36, sz=0.8, rmod=shell))
    # D-guard: a gold plate band wrapping round the knuckles from the shell to the pommel
    bow = [Vector(p) for p in ((0.46, 0.58, 0), (0.57, 0.30, 0), (0.59, -0.10, 0), (0.52, -0.46, 0),
                               (0.34, -0.74, 0), (0.12, -0.86, 0))]
    gold.add(sweep(bow, [0.07] * 6, [0.62, 0.58, 0.52, 0.44, 0.32, 0.18], sides=10, point_end=False))
    for zz in (0.27, -0.27):
        rim = [Vector((p.x * 1.02, p.y, zz * (1 - 0.6 * i / 5))) for i, p in enumerate(bow)]
        gold.add(sweep(rim, [0.075] * 6, [0.05] * 6, sides=6, point_end=False))
    grip.add(wrapped_grip(-0.74, 0.50, 0.125, 0.14, pitch=0.21, amp=0.02, sz=0.9))
    gold.add(lathe([(0, -0.98), (0.10, -0.98), (0.16, -0.92), (0.17, -0.84), (0.14, -0.76), (0, -0.74)], segs=14))


@weapon("Rapier", "Uncommon", "Sword")
def rapier(w):
    """Duelist's rapier: long needle blade, gold cup guard with long ball-ended
    quillons and a knuckle bow, navy grip bound in spiral gold wire, egg pommel."""
    blade_p = w.part("Blade", (226, 232, 242), "Metal", smooth=14)
    gold = w.part("Hilt", (240, 186, 56), "Metal")
    grip = w.part("Grip", (34, 40, 66), "Fabric", smooth=60)
    blade_p.add(sword_blade(0.60, 3.90, 4.52, w0=0.12, w1=0.085, h0=0.055, h1=0.045, ef=0.012,
                            point_curve=0.05, n_point=4))
    gold.add(lathe([(0, 0.42), (0.12, 0.42), (0.34, 0.50), (0.46, 0.64), (0.48, 0.72), (0.43, 0.73),
                    (0.32, 0.59), (0.12, 0.49), (0, 0.49)], segs=28, sz=0.88))
    path = [Vector((x, 0.48 + 0.10 * math.sin(math.pi * x / 1.5), 0)) for x in
            [lerp(-0.74, 0.74, i / 12) for i in range(13)]]
    gold.add(sweep(path, [0.075] * 13, [0.075] * 13, sides=8, point_end=False))
    for sx in (1, -1):
        gold.add(sphere(0.085, 10, 7), T(sx * 0.74, 0.48 + 0.10 * math.sin(math.pi * sx * 0.74 / 1.5), 0))
    bow = [Vector(p) for p in ((0.36, 0.52, 0), (0.46, 0.25, 0), (0.46, -0.20, 0), (0.36, -0.58, 0),
                               (0.18, -0.80, 0), (0.06, -0.86, 0))]
    gold.add(sweep(bow, [0.06] * 6, [0.06] * 6, sides=8, point_end=False))
    grip.add(lathe([(0, -0.66), (0.12, -0.66), (0.135, -0.12), (0.12, 0.44), (0, 0.44)], segs=16, sz=0.92))
    gold.add(helix_ribbon(-0.64, 0.42, 0.13, 0.12, 6.0, 0.032, 0.018, samples_per_turn=12))
    gold.add(lathe([(0, -1.06), (0.09, -1.04), (0.17, -0.96), (0.20, -0.86), (0.17, -0.76), (0.10, -0.69),
                    (0, -0.66)], segs=16))


@weapon("FishSlapper", "Uncommon", "Sword")
def fish_slapper(w):
    """A big surprised fish held by the tail: blue body, pale belly, darker fins,
    googly eyes and a round open mouth."""
    fish = w.part("Fish", (78, 158, 226), "SmoothPlastic", smooth=50)
    belly = w.part("Belly", (220, 240, 255), "SmoothPlastic", smooth=50)
    fins = w.part("Fins", (36, 98, 190), "SmoothPlastic", smooth=40)
    eyes = w.part("Eyes", (250, 250, 250), "SmoothPlastic", smooth=60)
    pupils = w.part("Pupils", (26, 26, 34), "SmoothPlastic", smooth=60)
    ys = [0.40, 0.70, 1.10, 1.60, 2.10, 2.60, 3.05, 3.45, 3.80, 4.02, 4.12]
    ws = [0.26, 0.40, 0.70, 1.00, 1.18, 1.22, 1.16, 1.00, 0.78, 0.50, 0.0]
    ts = [0.18, 0.25, 0.40, 0.52, 0.58, 0.60, 0.58, 0.52, 0.42, 0.30, 0.0]
    path = [Vector((0.06 * math.sin(i * 0.5), y, 0)) for i, y in enumerate(ys)]
    fish.add(sweep(path, ws, ts, sides=14))
    a, b = 2, 9
    belly.add(sweep_band(path[a:b], ws[a:b], ts[a:b], -55, 55, lift=0.004, rise=0.02, n_across=5))
    # tail fin = the grip end; tail stalk is the grip
    fish.add(lathe([(0, -0.56), (0.15, -0.56), (0.16, 0.0), (0.15, 0.45), (0, 0.45)], segs=14, sz=0.75))
    tail = catmull([(0, -0.46), (0.55, -1.0), (0.36, -0.70), (0.0, -0.62), (-0.36, -0.70), (-0.55, -1.0)],
                   samples=3, closed=True)
    fins.add(slab(tail, 0.12, 0.04, seg=1))
    dorsal = catmull([(-0.40, 1.50), (-0.80, 1.95), (-0.86, 2.55), (-0.62, 2.95), (-0.45, 2.70), (-0.48, 2.10)],
                     samples=3, closed=True)
    fins.add(slab(dorsal, 0.10, 0.035, seg=1))
    anal = catmull([(0.40, 1.35), (0.70, 1.55), (0.72, 1.95), (0.46, 1.95)], samples=3, closed=True)
    fins.add(slab(anal, 0.09, 0.03, seg=1))
    for side in (1, -1):
        pec = catmull([(0.0, 0.0), (0.38, -0.12), (0.50, -0.35), (0.20, -0.30)], samples=3, closed=True)
        fins.add(slab(pec, 0.07, 0.025, seg=1), T(0.16, 3.05, side * 0.24) @ R("Y", side * 20))
        eyes.add(sphere(0.23, 16, 10, scale=(1.0, 1.0, 0.72)), T(-0.12, 3.48, side * 0.25))
        pupils.add(sphere(0.105, 12, 8, scale=(1.0, 1.0, 0.6)), T(-0.05, 3.52, side * 0.40))
    # round surprised mouth at the very top: dark inside, fin-coloured lips
    pupils.add(lathe([(0, 4.08), (0.13, 4.10), (0.15, 4.15), (0, 4.14)], segs=14, sz=0.8))
    fins.add(torus(0.14, 0.05, segs=16, rsegs=6), T(0, 4.14, 0) @ S(1.0, 1.0, 0.8))



# ================================================================ SWORDS: rares and epics

@weapon("ScissorBlade", "Rare", "Sword")
def scissor_blade(w):
    """Giant closed scissors: two bevelled steel blades, a gold pivot screw, and
    chunky red handle loops you hold."""
    steel = w.part("Blade", (214, 220, 234), "Metal", smooth=20)
    red = w.part("Handles", (222, 48, 44), "SmoothPlastic", smooth=45)
    gold = w.part("Screw", (244, 190, 56), "Metal")
    outline = catmull([(-0.33, 0.55), (0.0, 0.46), (0.33, 0.62), (0.33, 1.6), (0.27, 2.8), (0.15, 3.80), (0.0, 4.40),
                       (-0.09, 3.80), (-0.17, 2.8), (-0.23, 1.6), (-0.30, 0.95)], samples=2, closed=True)
    for zs, mx in ((0.065, 1), (-0.065, -1)):
        steel.add(slab(outline, 0.12, 0.035, seg=1), T(0, 0, zs) @ S(mx, 1, 1))
    # tangs from the pivot down into the handles
    for zs, mx in ((0.05, 1), (-0.05, -1)):
        tang = [Vector((mx * x, y, zs)) for x, y in ((0.0, 0.70), (0.06, 0.40), (0.17, 0.10))]
        steel.add(sweep(tang, [0.15, 0.13, 0.12], [0.09, 0.09, 0.09], sides=6, point_end=False))
    gold.add(lathe([(0, -0.19), (0.13, -0.19), (0.16, -0.15), (0.16, 0.15), (0.13, 0.19), (0, 0.19)], segs=16),
             T(0, 0.74, 0) @ R("X", 90))
    gold.add(box(0.20, 0.045, 0.03), T(0, 0.74, 0.195))
    # handle loops (thumb loop and the bigger finger loop), offset front / back
    red.add(ring_slab(0.42, 0.21, 0.24, 0.07, n=26), T(-0.28, -0.32, 0.06))
    red.add(ring_slab(0.48, 0.26, 0.24, 0.07, n=26), T(0.30, -0.44, -0.06) @ S(1.0, 1.12, 1.0))
    for zs, x0 in ((0.06, -0.14), (-0.06, 0.16)):
        neck = [Vector((x0 * 0.4, 0.34, zs)), Vector((x0, 0.04, zs)), Vector((x0 * 1.6, -0.04, zs))]
        red.add(sweep(neck, [0.22, 0.22, 0.22], [0.20, 0.20, 0.20], sides=8, point_end=False))


@weapon("Claymore", "Rare", "Sword")
def claymore(w):
    """Highland claymore: long broad fullered blade, quillons angled toward the blade
    ending in four-ring quatrefoils, a sapphire in the guard, long leather grip."""
    blade_p = w.part("Blade", (214, 220, 234), "Metal", smooth=14)
    fuller = w.part("Fuller", (150, 160, 182), "Metal", smooth=14)
    hilt = w.part("Hilt", (82, 88, 108), "Metal")
    grip = w.part("Grip", (64, 40, 24), "Fabric", smooth=70)
    gem = w.part("Gem", (40, 110, 255), "Glass", transparency=0.15, smooth=10)
    st = [(0.78, 0.40, 0.125, 0.0, 0.11, 0.055), (2.5, 0.38, 0.12, 0.0, 0.105, 0.052),
          (4.25, 0.33, 0.105, 0.0, 0.085, 0.045)]
    b = fuller_blade(st, 5.12, n_point=6, point_curve=0.25)
    parts = split_by_tag(b, {0: "body", 1: "body", -1: "body", 3: "fuller"})
    blade_p.add(parts["body"])
    fuller.add(parts["fuller"])
    hilt.add(bar_y([(0.58, 0.50, 0.34, 0.07), (0.88, 0.56, 0.36, 0.07)]))
    for sx in (1, -1):
        arm = [Vector((sx * x, y, 0)) for x, y in ((0.14, 0.72), (0.44, 0.88), (0.76, 1.10), (0.91, 1.22))]
        hilt.add(sweep(arm, [0.21, 0.19, 0.18, 0.17], [0.23, 0.21, 0.19, 0.18], sides=8, point_end=False))
        cx, cy = sx * 1.03, 1.34
        for k in range(4):
            a = math.radians(45 + 90 * k)
            hilt.add(ring_slab(0.13, 0.06, 0.10, 0.0, n=10), T(cx + 0.135 * math.cos(a), cy + 0.135 * math.sin(a), 0))
    for side in (1, -1):
        gem.add(lathe([(0, 0.0), (0.15, 0.04), (0.16, 0.07), (0.09, 0.12), (0, 0.12)], segs=8),
                T(0, 0.73, side * 0.175) @ R("X", side * 90))
    grip.add(wrapped_grip(-1.02, 0.60, 0.14, 0.155, pitch=0.24, amp=0.024, sz=0.9))
    hilt.add(knob_pommel(-1.12, r=0.20, h=0.30, segs=10))


@weapon("Scimitar", "Rare", "Sword")
def scimitar(w):
    """Desert scimitar: deeply curved steel blade flaring wide toward the tip, gold
    crossguard with curled ends, turquoise gem, navy grip, gold hooked pommel."""
    blade_p = w.part("Blade", (220, 226, 238), "Metal", smooth=14)
    gold = w.part("Guard", (242, 188, 56), "Metal")
    grip = w.part("Grip", (30, 46, 112), "Fabric", smooth=70)
    gem = w.part("Gem", (40, 214, 230), "Glass", transparency=0.12, smooth=10)
    blade_p.add(saber_blade(0.52, 4.30, w0=0.44, w1=0.80, h0=0.09, h1=0.07, curve=0.62, xb0=-0.22,
                            clip=0.70, tip_bias=0.05, n=22, flare_at=0.85))
    for sx in (1, -1):
        curl = [Vector((sx * (0.12 + 0.55 * t), 0.50 + 0.12 * t * t, 0)) for t in (0, 0.33, 0.66, 1.0)]
        for k in range(1, 7):
            a = math.radians(-90 + 55 * k)
            curl.append(Vector((sx * (0.67 + 0.13 * math.cos(a) * 0 + 0.11 * math.sin(math.radians(55 * k))),
                                0.62 + 0.11 * (1 - math.cos(math.radians(55 * k))), 0)))
        gold.add(sweep(curl, [0.17] * len(curl), [0.18] * len(curl), sides=8, point_end=False))
    gold.add(bar_y([(0.38, 0.40, 0.30, 0.07), (0.64, 0.46, 0.32, 0.07)]))
    for side in (1, -1):
        gem.add(lathe([(0, 0.0), (0.12, 0.035), (0.13, 0.06), (0.08, 0.10), (0, 0.10)], segs=8),
                T(0, 0.51, side * 0.155) @ R("X", side * 90))
    grip.add(wrapped_grip(-0.62, 0.40, 0.125, 0.14, pitch=0.21, amp=0.02, sz=0.9))
    hook = [Vector(p) for p in ((0.0, -0.60, 0), (-0.04, -0.74, 0), (-0.14, -0.86, 0), (-0.28, -0.88, 0))]
    gold.add(sweep(hook, [0.20, 0.20, 0.17, 0.0], [0.18, 0.18, 0.15, 0.0], sides=10))


@weapon("ThornBlade", "Rare", "Sword")
def thorn_blade(w):
    """Living rose-stem blade: a long green leaf blade with a raised vein and thorns
    along its edges, a thorny vine winding up it, leaf guard, a pink rose bloom and a
    vine-wrapped wooden grip."""
    green = w.part("Blade", (78, 186, 74), "SmoothPlastic", smooth=14)
    vine = w.part("Vine", (36, 112, 46), "SmoothPlastic", smooth=40)
    rose = w.part("Rose", (238, 66, 118), "SmoothPlastic", smooth=35)
    wood = w.part("Grip", (122, 80, 44), "Wood", smooth=50)
    st = [(0.70, 0.36, 0.115, 0.07), (1.6, 0.47, 0.11, 0.08), (2.6, 0.45, 0.105, 0.08), (3.45, 0.33, 0.095, 0.07)]
    green.add(profile_blade(st, 4.32, n_point=6, point_curve=0.45))
    # midrib
    vine.add(surface_vein([(0, 0.78), (0, 3.6)], 0.06, st, side=1, lift=0.004, thick=0.02, taper=True))
    vine.add(surface_vein([(0, 0.78), (0, 3.6)], 0.06, st, side=-1, lift=0.004, thick=0.02, taper=True))
    # thorns along both edges, pointing up the blade
    for y in (1.0, 1.45, 1.9, 2.35, 2.8, 3.2):
        st_w = min(st, key=lambda q: abs(q[0] - y))[1]
        for sx in (1, -1):
            thorn = [Vector((sx * (st_w - 0.03), y, 0)), Vector((sx * (st_w + 0.06), y + 0.07, 0)),
                     Vector((sx * (st_w + 0.12), y + 0.17, 0))]
            vine.add(sweep(thorn, [0.10, 0.05, 0.0], [0.06, 0.035, 0.0], sides=5))
    # leaf crossguard
    for sx in (1, -1):
        leaf = slab(leaf_pts(0.90, 0.38, n=7, tip_sharp=1.3), 0.08, 0.03, seg=1)
        vine.add(leaf, T(sx * 0.10, 0.62, 0) @ R("Z", -sx * 72))
    # rose bloom on the guard: a petalled cup facing out on both faces with a swirled bud
    petals = lambda a: 1 + 0.16 * abs(math.cos(2.5 * a))
    for side in (1, -1):
        base = T(0, 0.66, side * 0.10) @ R("X", side * 90)
        rose.add(lathe([(0, 0.0), (0.16, 0.02), (0.26, 0.10), (0.27, 0.16), (0.22, 0.15), (0.14, 0.10), (0, 0.10)],
                       segs=20, rmod=petals), base)
        rose.add(sphere(0.12, 12, 8, scale=(1.0, 0.9, 1.0)), base @ T(0, 0.14, 0))
    wood.add(wrapped_grip(-0.68, 0.52, 0.125, 0.14, pitch=0.24, amp=0.018, sz=0.9))
    vine.add(helix_ribbon(-0.64, 0.50, 0.15, 0.135, 2.2, 0.06, 0.03, samples_per_turn=14))
    vine.add(sphere(0.15, 12, 8), T(0, -0.86, 0))
    vine.add(slab(leaf_pts(0.36, 0.20, n=6), 0.06, 0.02, seg=1), T(0.05, -0.92, 0) @ R("Z", 140))


@weapon("CrystalSword", "Epic", "Sword")
def crystal_sword(w):
    """A blade grown from one faceted cyan crystal with a glowing core, silver guard
    sprouting crystal shards, navy grip and a crystal pommel."""
    crystal = w.part("Crystal", (110, 228, 255), "Glass", transparency=0.28, smooth=5)
    core = w.part("Core", (214, 252, 255), "Neon")
    silver = w.part("Guard", (230, 236, 248), "Metal")
    grip = w.part("Grip", (28, 44, 110), "Fabric", smooth=70)
    crystal.add(lathe([(0, 0.60), (0.40, 0.66), (0.44, 1.5), (0.38, 3.45), (0, 4.46)], segs=6, sz=0.36, phase=math.pi / 6))
    core.add(lathe([(0, 0.70), (0.10, 0.78), (0.10, 3.3), (0, 4.10)], segs=6, sz=0.62, phase=math.pi / 6))
    silver.add(bar_x([(-0.56, 0.16, 0.20), (-0.44, 0.22, 0.26), (0.44, 0.22, 0.26), (0.56, 0.16, 0.20)], chamfer=0.05, y=0.58))
    for sx in (1, -1):
        for ang, L, r in ((-25, 0.78, 0.13), (-62, 0.56, 0.10), (12, 0.48, 0.09)):
            shard = lathe([(0, 0.0), (r, 0.04), (r * 0.95, L * 0.65), (0, L)], segs=6)
            crystal.add(shard, T(sx * 0.50, 0.60, 0) @ S(sx, 1, 1) @ R("Z", ang))
    grip.add(wrapped_grip(-0.62, 0.50, 0.125, 0.14, pitch=0.21, amp=0.02, sz=0.9))
    silver.add(lathe([(0, -0.70), (0.14, -0.70), (0.17, -0.66), (0.15, -0.60), (0, -0.60)], segs=12))
    crystal.add(lathe([(0, -1.0), (0.14, -0.84), (0.13, -0.72), (0, -0.66)], segs=6))
    core.add(ico(0.06, 1), T(0, -0.82, 0))
    w.fx = (0, 4.3, 0)


@weapon("IceBrand", "Epic", "Sword")
def ice_brand(w):
    """Frozen blade of clear blue ice with a glowing frost core and frost veins,
    a blue steel snowflake guard, white grip and snowflake pommel."""
    ice = w.part("Ice", (186, 232, 255), "Glass", transparency=0.18, smooth=10)
    frost = w.part("Frost", (224, 248, 255), "Neon")
    blue = w.part("Guard", (54, 132, 230), "Metal")
    grip = w.part("Grip", (244, 248, 252), "Fabric", smooth=70)
    st = [(0.66, 0.37, 0.13, 0.055)]
    y = 0.75
    # icy facets: irregular steps along the edges
    for k, (dy, f) in enumerate(((0.42, 1.0), (0.38, 0.86), (0.46, 1.05), (0.40, 0.88), (0.44, 1.02), (0.38, 0.9))):
        st.append((y + dy, 0.44 * f, 0.13, 0.055))
        y += dy
    st.append((3.55, 0.35, 0.115, 0.055))
    ice.add(profile_blade(st, 4.46, n_point=5, point_curve=0.15))
    frost.add(surface_vein([(0, 0.75), (0.02, 1.6), (-0.02, 2.5), (0.0, 3.45)], 0.085, st, side=1, lift=0.006, taper=True))
    frost.add(surface_vein([(0, 0.75), (0.02, 1.6), (-0.02, 2.5), (0.0, 3.45)], 0.085, st, side=-1, lift=0.006, taper=True))
    for y0, sx in ((1.25, 1), (1.85, -1), (2.45, 1), (2.95, -1)):
        br = [(0.0, y0), (sx * 0.10, y0 + 0.10), (sx * 0.17, y0 + 0.12)]
        for side in (1, -1):
            frost.add(surface_vein(br, 0.035, st, side=side, lift=0.006))
    blue.add(snowflake(0.94, 0.13, arm_w=0.13, bevel=0.0, branches=1), T(0, 0.58, 0) @ R("Z", 30))
    grip.add(wrapped_grip(-0.60, 0.46, 0.125, 0.14, pitch=0.21, amp=0.02, sz=0.9))
    blue.add(snowflake(0.22, 0.09, arm_w=0.07, bevel=0.0, branches=1), T(0, -0.82, 0))
    blue.add(cylinder(0.08, 0.16, segs=10), T(0, -0.64, 0))
    w.fx = (0, 4.3, 0)


@weapon("LaserBlade", "Epic", "Sword")
def laser_blade(w):
    """Sci-fi laser sword: a glowing green beam inside a soft glass glow, chrome hilt
    with a notched emitter, black rubber grip ridges, a button and a ringed pommel."""
    beam = w.part("Beam", (96, 255, 128), "Neon")
    glow = w.part("Glow", (96, 255, 128), "Glass", transparency=0.62, smooth=60)
    chrome = w.part("Hilt", (196, 202, 216), "Metal", smooth=30)
    black = w.part("Bands", (30, 30, 36), "SmoothPlastic", smooth=40)
    beam.add(capsule(0.125, 0.50, 4.50, segs=14))
    glow.add(capsule(0.22, 0.52, 4.58, segs=16))
    notch = lambda a: 1 + 0.05 * (1 if math.cos(6 * a) > 0.5 else 0)
    chrome.add(lathe([(0.10, 0.30), (0.20, 0.30), (0.23, 0.40), (0.24, 0.62), (0.21, 0.62), (0.16, 0.48),
                      (0.10, 0.48)], segs=24, rmod=notch))
    chrome.add(lathe([(0, -0.66), (0.17, -0.66), (0.19, -0.60), (0.19, 0.30), (0, 0.30)], segs=20))
    for k in range(5):
        y = -0.45 + k * 0.17
        black.add(lathe([(0.185, y), (0.21, y + 0.02), (0.21, y + 0.09), (0.185, y + 0.11)], segs=20, close=False))
    black.add(box(0.10, 0.14, 0.06, 0.02), T(0, 0.12, 0.20))
    beam.add(box(0.06, 0.06, 0.04, 0.01), T(0, 0.12, 0.235))
    chrome.add(torus(0.13, 0.035, segs=18, rsegs=6, axis="Z"), T(0, -0.80, 0))
    w.fx = (0, 4.4, 0)



# ================================================================ SWORDS: legendaries

@weapon("GoldenSword", "Legendary", "Sword")
def golden_sword(w):
    """The golden hero sword: broad ridged gold blade with a glowing white-gold
    inlay, deep-gold winged guard with a big glowing ruby, white grip bound in gold
    wire, ruby pommel, a gold halo ring and sparkles floating around the blade."""
    blade_p = w.part("Blade", (255, 214, 84), "Metal", smooth=14)
    shine = w.part("Shine", (255, 246, 196), "Neon")
    guard = w.part("Guard", (232, 160, 34), "Metal", smooth=30)
    gem = w.part("Gem", (255, 34, 64), "Neon")
    grip = w.part("Grip", (246, 246, 250), "Fabric", smooth=70)
    st = [(0.82, 0.40, 0.14, 0.09), (2.6, 0.44, 0.13, 0.10), (4.10, 0.38, 0.115, 0.09)]
    blade_p.add(profile_blade(st, 5.20, n_point=7, point_curve=0.3))
    for side in (1, -1):
        shine.add(surface_vein([(0, 0.95), (0, 4.6)], 0.10, st, side=side, lift=0.005, thick=0.016, taper=True))
    # winged crossguard: three stacked feathers per side sweeping up and out
    for sx in (1, -1):
        for L, W_, ang, dz, y0 in ((1.18, 0.38, -60, 0.0, 0.64), (0.98, 0.34, -40, 0.045, 0.69), (0.76, 0.30, -20, -0.045, 0.74)):
            f = slab(leaf_pts(L, W_, n=6, tip_sharp=1.4), 0.13, 0.045, seg=1)
            guard.add(f, S(sx, 1, 1) @ T(0.22, y0, dz) @ R("Z", ang))
    guard.add(bar_y([(0.52, 0.56, 0.40, 0.08), (0.88, 0.62, 0.42, 0.08)]))
    for side in (1, -1):
        gem.add(lathe([(0, 0.0), (0.16, 0.05), (0.18, 0.08), (0.10, 0.15), (0, 0.15)], segs=8),
                T(0, 0.70, side * 0.20) @ R("X", side * 90))
    grip.add(lathe([(0, -0.66), (0.135, -0.66), (0.15, -0.10), (0.135, 0.52), (0, 0.52)], segs=16, sz=0.9))
    guard.add(helix_ribbon(-0.64, 0.50, 0.145, 0.13, 5.0, 0.035, 0.02, samples_per_turn=12))
    guard.add(lathe([(0, -1.02), (0.12, -1.02), (0.20, -0.94), (0.22, -0.82), (0.18, -0.70), (0.12, -0.66),
                     (0, -0.64)], segs=16))
    gem.add(ico(0.11, 1), T(0, -1.10, 0))
    # floating halo ring around the blade and sparkles
    guard.add(torus(0.62, 0.05, segs=28, rsegs=6), T(0, 1.6, 0) @ R("Z", -12) @ S(1.0, 1.0, 0.55))
    sparkle = slab(star_pts(4, 0.16, 0.05, rot=90), 0.06, 0.0)
    for x, y, z, rz_ in ((0.78, 2.6, 0.1, 10), (-0.80, 3.4, -0.1, -15), (0.66, 4.3, 0.0, 20)):
        shine.add(sparkle, T(x, y, z) @ R("Z", rz_))
    w.fx = (0, 5.05, 0)


@weapon("VoidEdge", "Legendary", "Sword")
def void_edge(w):
    """A blade cut from the void: near-black purple shard blade with glowing violet
    rifts and edges, a guard of dark crystal spikes around a glowing void orb, and
    dark shards orbiting the blade."""
    void = w.part("Blade", (30, 18, 50), "SmoothPlastic", smooth=14)
    rift = w.part("Rift", (178, 82, 255), "Neon")
    orb = w.part("Orb", (246, 196, 255), "Neon")
    shards = w.part("Shards", (92, 46, 150), "Glass", transparency=0.15, smooth=5)
    grip = w.part("Grip", (24, 14, 40), "Fabric", smooth=70)
    st = [(0.76, 0.40, 0.14, 0.08)]
    y = 0.84
    for dy, f in ((0.5, 1.0), (0.45, 0.82), (0.55, 1.08), (0.5, 0.86), (0.55, 1.1), (0.45, 0.84)):
        st.append((y + dy - 0.04, 0.53 * f, 0.13, 0.085))
        st.append((y + dy, 0.53 * f * 0.80, 0.13, 0.08))
        y += dy
    st.append((3.95, 0.38, 0.11, 0.08))
    b = profile_blade(st, 5.14, n_point=6, point_curve=0.2)
    parts = split_by_tag(b, {0: "body", -1: "body", 1: "edge"})
    void.add(parts["body"])
    rift.add(parts["edge"])
    rifts = [[(0.0, 0.9), (0.05, 1.5), (-0.04, 2.1), (0.06, 2.8), (-0.02, 3.5), (0.0, 4.1)],
             [(0.05, 1.5), (0.16, 1.75), (0.26, 1.9)], [(-0.04, 2.1), (-0.17, 2.35), (-0.27, 2.5)],
             [(0.06, 2.8), (0.18, 3.0), (0.27, 3.12)]]
    for side in (1, -1):
        for r_ in rifts:
            rift.add(surface_vein(r_, 0.085, st, side=side, lift=0.005, taper=True))
    # guard: dark crystal spikes fanning out around a glowing orb
    for sx in (1, -1):
        for ang, L, r in ((-72, 1.10, 0.17), (-44, 0.86, 0.15), (-16, 0.62, 0.12), (-102, 0.66, 0.13)):
            sp = lathe([(0, 0.0), (r, 0.06), (r * 0.9, L * 0.6), (0, L)], segs=6)
            shards.add(sp, T(sx * 0.18, 0.66, 0) @ S(sx, 1, 1) @ R("Z", ang))
    shards.add(rock(0.30, seed=7, jitter=0.12, subdiv=1, scale=(1.35, 0.85, 0.9)), T(0, 0.66, 0))
    orb.add(sphere(0.19, 14, 10), T(0, 0.66, 0.19))
    orb.add(sphere(0.19, 14, 10), T(0, 0.66, -0.19))
    grip.add(wrapped_grip(-0.64, 0.50, 0.13, 0.145, pitch=0.21, amp=0.022, sz=0.9))
    shards.add(lathe([(0, -1.08), (0.15, -0.90), (0.14, -0.72), (0, -0.62)], segs=6))
    orb.add(ico(0.08, 1), T(0, -0.86, 0))
    # orbiting void shards
    for x, y, z, rz_, sc in ((0.95, 2.2, 0.15, 30, 1.25), (-1.0, 3.1, -0.12, -25, 1.1), (0.86, 4.0, -0.1, 15, 0.95)):
        sh = lathe([(0, -0.18), (0.08, -0.06), (0.07, 0.10), (0, 0.22)], segs=5)
        shards.add(sh, T(x, y, z) @ R("Z", rz_) @ S(sc))
        rift.add(ico(0.035, 1), T(x * 1.12, y + 0.25, z))
    w.fx = (0, 4.95, 0)



# ================================================================ SWORDS: limited (Halloween)

def pumpkin_lathe(r, h, lobes=8, depth=0.08, segs=32, cy=0.0):
    """Ribbed pumpkin body (centred on cy) with a dimple top and bottom."""
    prof = [(0, cy - h * 0.40), (r * 0.30, cy - h * 0.47), (r * 0.72, cy - h * 0.42), (r * 0.95, cy - h * 0.22),
            (r, cy), (r * 0.95, cy + h * 0.22), (r * 0.72, cy + h * 0.42), (r * 0.30, cy + h * 0.47), (0, cy + h * 0.40)]
    return lathe(prof, segs=segs, rmod=lambda a: 1 - depth * (0.5 - 0.5 * math.cos(lobes * a)) ** 0.6)


def pumpkin_leaf(size):
    """Lobed pumpkin / vine leaf outline (points), base at the origin, pointing +Y."""
    pts = []
    for i in range(25):
        t = i / 24
        a = math.pi * t
        r = size * (0.55 + 0.45 * abs(math.sin(2.5 * a)) ** 0.7)
        pts.append((r * math.cos(a) * 0.9, r * math.sin(a) * 1.0))
    return [(0, -size * 0.1)] + pts[1:-1]


@weapon("PumpkinCarver", "Limited", "Sword")
def pumpkin_carver(w):
    """Halloween carving knife: chunky orange blade with a glowing jack-o'-lantern
    face, curly vine guard with pumpkin leaves, vine-wrapped wooden grip and a
    mini pumpkin pommel."""
    blade_p = w.part("Blade", (255, 128, 28), "Metal", smooth=30)
    face = w.part("Face", (255, 214, 70), "Neon")
    vine = w.part("Vine", (88, 190, 58), "SmoothPlastic", smooth=45)
    pumpkin = w.part("Pumpkin", (255, 136, 30), "SmoothPlastic", smooth=50)
    wood = w.part("Grip", (96, 60, 32), "Wood", smooth=50)
    edge = catmull([(-0.30, 0.56), (0.36, 0.56), (0.40, 1.3), (0.40, 2.6), (0.30, 3.6), (0.12, 4.14), (-0.12, 4.42)],
                   samples=3)
    spine = [(-0.20, 4.02), (-0.27, 3.70)]
    y = 3.62
    while y > 1.0:                     # saw teeth down the spine, pointing toward the tip
        spine += [(-0.40, y - 0.06), (-0.30, y - 0.30)]
        y -= 0.34
    spine += [(-0.32, 0.90)]
    blade_p.add(slab(edge + spine, 0.17, 0.05, seg=2))
    # jack-o'-lantern face on both sides of the blade
    eye = [(-0.11, -0.07), (0.11, -0.07), (0.0, 0.12)]
    nose = [(-0.06, -0.05), (0.06, -0.05), (0.0, 0.06)]
    mouth = [(-0.25, 0.06), (-0.17, -0.02), (-0.11, 0.04), (-0.05, -0.04), (0.02, 0.03), (0.09, -0.05), (0.15, 0.03),
             (0.21, -0.03), (0.27, 0.07), (0.18, -0.11), (0.0, -0.15), (-0.18, -0.11)]
    for side in (1, -1):
        z = side * 0.088
        for pts, x, y in ((eye, -0.13, 3.02), (eye, 0.15, 3.02), (nose, 0.01, 2.74), (mouth, 0.02, 2.44)):
            face.add(slab(pts, 0.03, 0.0), T(x, y, z))
    # vine guard: two curls and two leaves
    for sx in (1, -1):
        curl = [Vector((sx * (0.10 + 0.62 * t), 0.56 + 0.06 * t, 0)) for t in (0, 0.35, 0.7, 1.0)]
        for k in range(1, 9):
            a = math.radians(-90 + 45 * k)
            curl.append(Vector((sx * (0.72 + 0.16 * math.cos(a)), 0.78 + 0.16 * math.sin(a), 0)))
        vine.add(sweep(curl, [0.09] * len(curl), [0.10] * len(curl), sides=8, point_end=False))
        vine.add(slab(pumpkin_leaf(0.44), 0.07, 0.025, seg=1), T(sx * 0.30, 0.50, 0.0) @ R("Z", -sx * 112))
    vine.add(bar_y([(0.46, 0.34, 0.26, 0.06), (0.64, 0.38, 0.28, 0.06)]))
    wood.add(lathe([(0, -0.70), (0.135, -0.70), (0.15, -0.10), (0.135, 0.48), (0, 0.48)], segs=16, sz=0.9))
    vine.add(helix_ribbon(-0.68, 0.46, 0.15, 0.135, 2.4, 0.06, 0.03, samples_per_turn=14))
    pumpkin.add(pumpkin_lathe(0.26, 0.40, lobes=8, depth=0.10, segs=32, cy=-0.92))
    vine.add(lathe([(0.06, -0.75), (0.07, -0.72), (0.05, -0.66), (0, -0.66)], segs=8))
    tendril = [Vector((0.05 + 0.10 * math.cos(math.radians(30 * k)), -0.70 + 0.012 * k, 0.10 * math.sin(math.radians(30 * k))))
               for k in range(10)]
    vine.add(sweep(tendril, [0.03] * 10, [0.03] * 10, sides=5, point_end=False))
    w.fx = (-0.12, 4.30, 0)


@weapon("BoneSaber", "Limited", "Sword")
def bone_saber(w):
    """A big cartoon bone blade with a knobbly tip, a little rib-cage guard, glowing
    green slime oozing over the guard and a purple bandage grip."""
    bone = w.part("Bone", (244, 238, 218), "SmoothPlastic", smooth=40)
    ribs = w.part("Ribs", (214, 204, 174), "SmoothPlastic", smooth=40)
    slime = w.part("Slime", (120, 255, 66), "Neon")
    wrap = w.part("Wrap", (132, 58, 196), "Fabric", smooth=70)
    # curved bone shaft with a slight flat (blade-like) cross-section
    key = [(0.0, 0.62), (0.03, 1.5), (0.02, 2.4), (-0.04, 3.3), (-0.10, 3.85)]
    path = [Vector((x, y, 0)) for x, y in catmull(key, samples=3)]
    n = len(path)
    widths = [0.46 - 0.10 * math.sin(math.pi * i / (n - 1)) for i in range(n)]
    thicks = [v * 0.62 for v in widths]
    bone.add(sweep(path, widths, thicks, sides=10, point_end=False))
    # the classic double-knob bone end at the tip
    tip = path[-1]
    for dx in (-0.18, 0.18):
        bone.add(sphere(0.25, 12, 8, scale=(1.0, 1.0, 0.8)), T(tip.x + dx, tip.y + 0.18, 0))
    bone.add(sphere(0.21, 12, 8, scale=(1.3, 0.9, 0.75)), T(tip.x, tip.y + 0.02, 0))
    # rib-cage guard: a spine block and three pairs of curved ribs
    ribs.add(bar_y([(0.46, 0.34, 0.30, 0.08), (0.70, 0.30, 0.28, 0.08)]))
    for k, (y0, span) in enumerate(((0.52, 0.62), (0.62, 0.70), (0.72, 0.56))):
        for sx in (1, -1):
            arc = [Vector((sx * (0.12 + span * math.sin(math.radians(a))), y0 + 0.30 * (1 - math.cos(math.radians(a))) - 0.05 * k,
                           0)) for a in range(0, 141, 20)]
            ribs.add(sweep(arc, [0.14] * len(arc), [0.15] * len(arc), sides=7, point_end=False))
    # slime oozing over the guard with drips
    slime.add(lathe([(0, 0.64), (0.27, 0.65), (0.31, 0.74), (0.26, 0.84), (0, 0.84)], segs=16, sz=0.85,
                    rmod=lambda a: 1 + 0.22 * max(0.0, math.sin(3 * a))))
    for x, z, L, r in ((0.22, 0.12, 0.36, 0.07), (-0.18, -0.13, 0.28, 0.065), (0.04, 0.22, 0.22, 0.06),
                       (-0.06, -0.22, 0.32, 0.06)):
        slime.add(teardrop(r, L, segs=10), T(x, 0.69, z))
    wrap.add(wrapped_grip(-0.68, 0.46, 0.13, 0.145, pitch=0.2, amp=0.022, sz=0.9))
    for dx in (-0.11, 0.11):
        bone.add(sphere(0.16, 10, 7, scale=(1.0, 1.0, 0.8)), T(dx, -0.84, 0))
    w.fx = (-0.10, 4.05, 0)


@weapon("WitchBroom", "Limited", "Sword")
def witch_broom(w):
    """Witch's broom: gnarled wooden stick, a flared bundle of straw bristles with
    ragged tips, purple binding and an orange ribbon bow."""
    stick = w.part("Stick", (118, 74, 40), "Wood", smooth=45)
    straw = w.part("Bristles", (236, 188, 88), "Fabric", smooth=30)
    band = w.part("Binding", (130, 56, 200), "Fabric", smooth=50)
    bow = w.part("Bow", (255, 128, 28), "SmoothPlastic", smooth=45)
    key = [(0.0, -1.0), (0.03, -0.2), (-0.03, 0.6), (0.04, 1.5), (-0.02, 2.3), (0.0, 3.1)]
    path = [Vector((x, y, 0)) for x, y in catmull(key, samples=3)]
    n = len(path)
    stick.add(sweep(path, [0.25] * n, [0.24] * n, sides=12, point_end=False))
    stick.add(sphere(0.15, 12, 8), T(0.0, -1.0, 0))
    for y, dx, dz in ((0.25, 0.10, 0.04), (1.05, -0.10, -0.03), (1.9, 0.10, 0.02)):
        stick.add(sphere(0.07, 8, 6, scale=(1.0, 1.4, 1.0)), T(dx, y, dz))
    # bristles: flared straw bundle with grooves and a ragged top
    ridges = lambda a: 1 + 0.06 * abs(math.cos(13 * a))
    nseg = 40
    rings = []
    for y, r, rag in ((2.95, 0.21, 0.0), (3.2, 0.38, 0.0), (3.65, 0.58, 0.0), (4.20, 0.72, 0.0), (4.56, 0.70, 1.0)):
        ring = []
        for i in range(nseg):
            a = math.tau * i / nseg
            yy = y + rag * (0.11 * math.sin(7 * a) + 0.06 * math.sin(17 * a + 1.0))
            ring.append(Vector((r * ridges(a) * math.cos(a), yy, r * 0.82 * ridges(a) * math.sin(a))))
        rings.append(ring)
    straw.add(loft(rings, cap_start=True, cap_end=True))
    for a, L in ((20, 0.45), (100, 0.38), (160, 0.5), (250, 0.42), (320, 0.36)):
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        strand = [Vector((0.66 * ca, 4.25, 0.54 * sa)), Vector((0.74 * ca, 4.25 + L * 0.6, 0.6 * sa)),
                  Vector((0.82 * ca, 4.25 + L, 0.66 * sa))]
        straw.add(sweep(strand, [0.05, 0.04, 0.0], [0.05, 0.04, 0.0], sides=5))
    band.add(lathe([(0.0, 2.92), (0.27, 2.92), (0.30, 2.96), (0.30, 3.08), (0.27, 3.12), (0, 3.12)], segs=20, sz=0.85))
    band.add(lathe([(0.0, 3.30), (0.40, 3.30), (0.43, 3.33), (0.43, 3.41), (0.40, 3.44), (0, 3.44)], segs=24, sz=0.84))
    for sx in (1, -1):
        loop = catmull([(0, 0), (0.30, 0.16), (0.36, -0.02), (0.26, -0.14)], samples=3, closed=True)
        bow.add(slab(loop, 0.08, 0.025, seg=1), T(0, 3.02, 0.27) @ S(sx, 1, 1))
        tail = catmull([(0.02, -0.02), (0.14, -0.34), (0.06, -0.36), (-0.02, -0.06)], samples=2, closed=True)
        bow.add(slab(tail, 0.06, 0.02, seg=1), T(0, 3.0, 0.27) @ S(sx, 1, 1))
    bow.add(sphere(0.07, 10, 7, scale=(1.0, 1.0, 0.7)), T(0, 3.02, 0.29))
    w.fx = (0, 4.5, 0)



# ================================================================ DAGGERS: commons and uncommons

@weapon("ButterKnife", "Common", "Dagger")
def butter_knife(w):
    """Giant butter knife: round-tipped steel blade with a little serrated edge,
    a fat pat of butter on it, cream handle with a steel bolster."""
    steel = w.part("Blade", (214, 220, 232), "Metal", smooth=25)
    handle = w.part("Grip", (246, 232, 204), "SmoothPlastic", smooth=50)
    butter = w.part("Butter", (255, 222, 96), "SmoothPlastic", smooth=35)
    edge = [(0.25, 0.60), (0.27, 1.6)]
    for k in range(6):                  # little serrations along the upper edge
        y = 1.75 + k * 0.13
        edge += [(0.29, y), (0.265, y + 0.07)]
    edge += catmull([(0.27, 2.55), (0.22, 2.85), (0.0, 3.0), (-0.20, 2.88), (-0.24, 2.55)], samples=3)
    edge += [(-0.22, 1.2), (-0.22, 0.60)]
    steel.add(slab(edge, 0.10, 0.03, seg=1))
    steel.add(lathe([(0, 0.40), (0.15, 0.40), (0.17, 0.46), (0.16, 0.62), (0, 0.62)], segs=16, sz=0.7))
    handle.add(lathe([(0, -0.80), (0.14, -0.80), (0.18, -0.70), (0.19, -0.40), (0.16, 0.05), (0.15, 0.40), (0, 0.40)],
                     segs=18, sz=0.72))
    butter.add(box(0.36, 0.30, 0.18, 0.07, 2), T(0.0, 2.42, 0.12) @ R("Z", 8))


@weapon("IronDagger", "Common", "Dagger")
def iron_dagger(w):
    """Plain iron dagger: leaf-shaped ridged blade, dark iron guard and pommel,
    brown leather grip."""
    blade_p = w.part("Blade", (200, 206, 218), "Metal", smooth=14)
    hilt = w.part("Hilt", (84, 90, 110), "Metal")
    grip = w.part("Grip", (112, 66, 38), "Fabric", smooth=70)
    st = [(0.50, 0.24, 0.10, 0.0), (1.30, 0.30, 0.095, 0.0), (2.20, 0.24, 0.085, 0.0)]
    blade_p.add(profile_blade(st, 3.02, n_point=6, point_curve=0.35))
    hilt.add(bar_x([(-0.52, 0.15, 0.19), (-0.42, 0.20, 0.24), (0.42, 0.20, 0.24), (0.52, 0.15, 0.19)], chamfer=0.05, y=0.44))
    grip.add(wrapped_grip(-0.58, 0.36, 0.125, 0.14, pitch=0.2, amp=0.02, sz=0.9))
    hilt.add(knob_pommel(-0.76, r=0.18, h=0.30, segs=8))


@weapon("Stiletto", "Common", "Dagger")
def stiletto(w):
    """Slim stiletto: long square needle blade, gold crossguard with ball ends,
    black ribbed grip, gold ball pommel."""
    blade_p = w.part("Blade", (226, 232, 242), "Metal", smooth=20)
    gold = w.part("Guard", (242, 188, 56), "Metal")
    grip = w.part("Grip", (32, 34, 46), "SmoothPlastic", smooth=40)
    blade_p.add(lathe([(0, 0.40), (0.15, 0.42), (0.13, 1.6), (0.07, 2.7), (0, 3.20)], segs=4, phase=math.pi / 4))
    gold.add(bar_x([(-0.50, 0.18, 0.20), (0.50, 0.18, 0.20)], chamfer=0.05, y=0.40))
    gold.add(bar_y([(0.30, 0.30, 0.24, 0.05), (0.50, 0.32, 0.25, 0.05)]))
    for sx in (1, -1):
        gold.add(sphere(0.13, 12, 8), T(sx * 0.56, 0.40, 0))
    prof = [(0, -0.66)]
    for k in range(7):
        y = -0.66 + k * 0.145
        prof += [(0.13, y + 0.01), (0.15, y + 0.07)]
    prof += [(0.13, 0.33), (0, 0.33)]
    grip.add(lathe(prof, segs=16))
    gold.add(sphere(0.15, 14, 9), T(0, -0.82, 0))


@weapon("Screwdriver", "Common", "Dagger")
def screwdriver(w):
    """Giant flathead screwdriver: steel shank with a flat tip, chunky red fluted
    handle with black rubber bands."""
    steel = w.part("Shank", (214, 220, 232), "Metal", smooth=30)
    red = w.part("Grip", (226, 46, 44), "SmoothPlastic", smooth=35)
    black = w.part("Stripes", (30, 30, 36), "SmoothPlastic", smooth=40)
    steel.add(lathe([(0, 0.40), (0.10, 0.40), (0.10, 2.80), (0, 2.80)], segs=12))
    steel.add(loft([[Vector((x, y, z)) for x, z in ((0.10, 0.0), (0.0, 0.10), (-0.10, 0.0), (0.0, -0.10))]
                    for y in ()] or [[Vector((0.10 * c, 2.78, 0.10 * s_)) for c, s_ in ((1, 0), (0, 1), (-1, 0), (0, -1))],
                                    [Vector((0.15 * c, 3.12, 0.025 * s_)) for c, s_ in ((1, 0), (0, 1), (-1, 0), (0, -1))]],
                   cap_start=True, cap_end=True))
    flutes = lambda a: 1 - 0.07 * (0.5 + 0.5 * math.cos(8 * a)) ** 2
    red.add(lathe([(0, -0.78), (0.25, -0.78), (0.32, -0.70), (0.33, -0.2), (0.30, 0.25), (0.24, 0.42), (0.12, 0.48),
                   (0, 0.48)], segs=32, rmod=flutes))
    for y in (-0.42, -0.06):
        black.add(lathe([(0.31, y), (0.345, y + 0.025), (0.345, y + 0.115), (0.31, y + 0.14)], segs=32, close=False))
    black.add(lathe([(0, -0.80), (0.26, -0.80), (0.28, -0.76), (0.26, -0.72), (0, -0.72)], segs=24))


@weapon("Fork", "Common", "Dagger")
def giant_fork(w):
    """Giant dinner fork: four rounded tines on a curved head, a slim neck and a
    flat handle that widens to a rounded end."""
    steel = w.part("Fork", (214, 220, 232), "Metal", smooth=35)
    head = catmull([(-0.07, 1.05), (-0.25, 1.35), (-0.38, 1.75), (-0.44, 2.25), (0.44, 2.25), (0.38, 1.75), (0.25, 1.35),
                    (0.07, 1.05)], samples=3, closed=False)
    steel.add(slab(head + [(0.07, 0.95), (-0.07, 0.95)], 0.12, 0.04, seg=1))
    for x in (-0.33, -0.11, 0.11, 0.33):
        tine = rounded_rect_pts(0.14, 1.30, 0.07, n=3)
        steel.add(slab(tine, 0.11, 0.035, seg=1), T(x, 2.85, 0))
    handle = catmull([(-0.07, 1.0), (-0.09, 0.4), (-0.17, -0.3), (-0.20, -0.65), (0.0, -0.84), (0.20, -0.65),
                      (0.17, -0.3), (0.09, 0.4), (0.07, 1.0)], samples=3, closed=True)
    steel.add(slab(handle, 0.12, 0.045, seg=1))


@weapon("Kunai", "Uncommon", "Dagger")
def kunai(w):
    """Ninja kunai: dark steel leaf blade, white cloth wrap, ring pommel with a red
    ribbon tied through it."""
    steel = w.part("Blade", (62, 68, 84), "Metal", smooth=14)
    wrap = w.part("Wrap", (244, 244, 248), "Fabric", smooth=70)
    ribbon = w.part("Ribbon", (224, 44, 46), "Fabric", smooth=40)
    st = [(0.42, 0.16, 0.09, 0.0), (0.95, 0.46, 0.115, 0.0), (1.9, 0.38, 0.10, 0.0)]
    steel.add(profile_blade(st, 3.02, n_point=6, point_curve=0.5))
    wrap.add(wrapped_grip(-0.80, 0.42, 0.115, 0.125, pitch=0.16, amp=0.02, sz=0.95))
    steel.add(cylinder(0.08, 0.12, segs=10), T(0, -0.84, 0))
    steel.add(torus(0.23, 0.065, segs=22, rsegs=8, axis="Z"), T(0, -1.14, 0))
    # ribbon knotted through the ring with two fluttering tails
    ribbon.add(sphere(0.08, 10, 7, scale=(1.2, 1.0, 0.8)), T(0, -1.35, 0))
    for sx, L in ((1, 0.46), (-1, 0.38)):
        tail = [Vector((sx * 0.03, -1.38, 0)), Vector((sx * 0.14, -1.52, 0.05)), Vector((sx * 0.10, -1.66, -0.04)),
                Vector((sx * 0.20, -1.38 - L, 0.02))]
        ribbon.add(sweep(tail, [0.13, 0.13, 0.12, 0.10], [0.03, 0.03, 0.03, 0.03], sides=4, point_end=False))


@weapon("Sai", "Uncommon", "Dagger")
def sai(w):
    """Sai: octagonal steel center prong, two curved side prongs, red grip wrap
    with gold collar and pommel."""
    steel = w.part("Prongs", (196, 204, 220), "Metal", smooth=30)
    wrap = w.part("Wrap", (214, 40, 42), "Fabric", smooth=70)
    gold = w.part("Trim", (242, 188, 56), "Metal")
    steel.add(lathe([(0, 0.38), (0.11, 0.40), (0.10, 2.6), (0.06, 3.1), (0, 3.32)], segs=8, phase=math.pi / 8))
    for sx in (1, -1):
        path = [Vector((sx * x, y, 0)) for x, y in ((0.08, 0.46), (0.40, 0.50), (0.62, 0.68), (0.71, 1.0), (0.69, 1.42))]
        steel.add(sweep(path, [0.16, 0.15, 0.14, 0.12, 0.0], [0.16, 0.15, 0.14, 0.12, 0.0], sides=8))
    gold.add(lathe([(0, 0.30), (0.16, 0.30), (0.18, 0.34), (0.18, 0.46), (0.16, 0.50), (0, 0.50)], segs=16))
    wrap.add(wrapped_grip(-0.70, 0.32, 0.125, 0.135, pitch=0.18, amp=0.02, sz=1.0))
    gold.add(lathe([(0, -0.92), (0.10, -0.92), (0.17, -0.84), (0.18, -0.76), (0.15, -0.70), (0, -0.68)], segs=16))


@weapon("Carrot", "Uncommon", "Dagger")
def carrot(w):
    """A giant crunchy carrot held by its leafy top: a fat bumpy orange root with
    darker growth rings above the hand, a twisted bundle of green stalks to hold,
    and a bushy leaf top sprouting out the bottom."""
    orange = w.part("Carrot", (255, 138, 30), "SmoothPlastic", smooth=45)
    rings = w.part("Rings", (226, 102, 16), "SmoothPlastic", smooth=45)
    leaves = w.part("Leaves", (72, 182, 62), "SmoothPlastic", smooth=40)

    def root_r(y):
        return lerp(0.49, 0.06, max(0.0, min(1.0, (y - 0.56) / 2.54)) ** 1.1)
    prof = [(0, 0.16), (0.22, 0.18), (0.38, 0.26), (0.46, 0.40)]
    for k in range(12):
        y = lerp(0.56, 3.10, k / 11)
        prof.append((root_r(y) * (1.0 + 0.04 * math.sin(k * 2.1)), y))
    prof += [(0.03, 3.30), (0, 3.36)]
    orange.add(lathe(prof, segs=18))
    for y in (0.78, 1.32, 1.86, 2.36, 2.80):
        r = root_r(y)
        rings.add(lathe([(r - 0.02, y - 0.03), (r + 0.012, y - 0.015), (r + 0.012, y + 0.015), (r - 0.02, y + 0.03)],
                        segs=18, close=False))
    # the stalks you hold: three twisted together
    for k in range(3):
        stalk = []
        for i in range(9):
            t = i / 8
            a = math.radians(120 * k + 200 * t)
            stalk.append(Vector((0.075 * math.cos(a), lerp(0.30, -0.66, t), 0.075 * math.sin(a))))
        leaves.add(sweep(stalk, [0.15] * 9, [0.15] * 9, sides=7, point_end=False))
    # leafy top: stems fanning downward with leaflets
    for ang, L, spread in ((-30, 0.62, 0.55), (0, 0.72, 0.25), (30, 0.62, 0.55), (180 - 25, 0.58, 0.55),
                           (180 + 25, 0.60, 0.55), (90, 0.50, 0.7), (-90, 0.50, 0.7)):
        a = math.radians(ang)
        d = Vector((math.sin(a) * spread, -1.0, math.cos(a) * spread * 0.7)).normalized()
        base = Vector((0, -0.60, 0))
        stem = [base, base + d * L * 0.5, base + d * L]
        leaves.add(sweep(stem, [0.08, 0.065, 0.0], [0.08, 0.065, 0.0], sides=6))
        for t, side in ((0.45, 1), (0.65, -1), (0.88, 1)):
            p = base + d * L * t
            leaves.add(slab(leaf_pts(0.34, 0.20, n=5), 0.045, 0.0),
                       T(p.x, p.y, p.z) @ R("Y", ang) @ R("Z", 180 + side * 38))



# ================================================================ DAGGERS: rares, epics, legendary

def twisted_icicle(y0, y1, r0, lobes=6, twist=1.2, segs=24, rings=10, wobble=0.05, sz=1.0):
    """A ridged icicle cone from y0 (radius r0) to a point at y1, its ridges
    twisting `twist` turns along the length."""
    rs_ = []
    for i in range(rings + 1):
        t = i / rings
        y = lerp(y0, y1, t)
        r = r0 * (1 - t) ** 0.85 * (1 + wobble * math.sin(9 * t))
        if i == rings:
            rs_.append([Vector((0, y1, 0))])
            break
        ring = []
        for j in range(segs):
            a = math.tau * j / segs
            k = 1 + 0.12 * math.cos(lobes * (a + twist * math.tau * t / lobes))
            ring.append(Vector((r * k * math.cos(a), y, r * k * sz * math.sin(a))))
        rs_.append(ring)
    return loft(rs_, cap_start=True, cap_end=False)


def fang_sweep(y0, y1, w0, curve, t_ratio=0.6, n=14, sides=10, bulge=0.1, x0=0.0):
    """A curved, swelling fang cone from y0 (width w0) to a point at y1, bending
    toward -X by `curve`. Returns (bmesh, path, widths, thicks)."""
    path, widths = [], []
    for i in range(n + 1):
        t = i / n
        path.append(Vector((x0 - curve * t ** 2, lerp(y0, y1, t), 0)))
        widths.append(w0 * (1 - t) ** 1.15 * (1 + bulge * math.sin(math.pi * min(t * 2.2, 1))))
    widths[-1] = 0.0
    thicks = [v * t_ratio for v in widths]
    return sweep(path, widths, thicks, sides=sides), path, widths, thicks


@weapon("StraightRazor", "Rare", "Dagger")
def straight_razor(w):
    """Barber's straight razor flipped open: broad steel blade with a darker
    spine, cream scales riveted with gold pins."""
    steel = w.part("Blade", (220, 226, 238), "Metal", smooth=20)
    spine = w.part("Spine", (150, 160, 182), "Metal", smooth=30)
    scales = w.part("Scales", (246, 240, 226), "SmoothPlastic", smooth=45)
    pins = w.part("Pins", (244, 190, 56), "Metal")
    outline = catmull([(-0.20, 0.50), (0.54, 0.56), (0.56, 1.6), (0.54, 2.62), (0.40, 2.90), (0.10, 2.93),
                       (-0.22, 2.80), (-0.24, 1.2)], samples=3, closed=True)
    steel.add(slab(outline, 0.11, 0.035, seg=1))
    back = [Vector((-0.22, y, 0)) for y in (0.36, 0.9, 1.6, 2.3, 2.78)]
    spine.add(sweep(back, [0.12] * 5, [0.17] * 5, sides=8, point_end=False))
    tang = [Vector((x, y, 0)) for x, y in ((-0.16, 0.56), (-0.10, 0.36), (0.0, 0.26))]
    spine.add(sweep(tang, [0.16, 0.15, 0.14], [0.12, 0.12, 0.12], sides=8, point_end=False))
    sc = catmull([(-0.20, 0.42), (0.16, 0.46), (0.21, 0.1), (0.20, -0.6), (0.12, -1.0), (-0.12, -1.0), (-0.20, -0.6),
                  (-0.21, 0.1)], samples=3, closed=True)
    scales.add(slab(sc, 0.26, 0.08, seg=2))
    for y in (0.30, -0.86):
        for side in (1, -1):
            pins.add(lathe([(0, 0.0), (0.07, 0.0), (0.075, 0.02), (0.05, 0.04), (0, 0.045)], segs=12),
                     T(0, y, side * 0.13) @ R("X", side * 90))


@weapon("Karambit", "Rare", "Dagger")
def karambit(w):
    """Karambit: a dark steel claw blade hooking forward with the edge on its
    inside curve, red grip with silver bolts, and the finger ring at the end."""
    steel = w.part("Blade", (62, 68, 84), "Metal", smooth=16)
    grip = w.part("Grip", (220, 46, 44), "SmoothPlastic", smooth=40)
    bolts = w.part("Bolts", (214, 220, 232), "Metal")
    steel.add(saber_blade(0.30, 2.90, w0=0.44, w1=0.48, h0=0.10, h1=0.08, curve=-1.05, xb0=-0.24,
                          clip=0.85, tip_bias=0.85, n=20))
    g = catmull([(-0.24, 0.36), (0.22, 0.36), (0.22, -0.2), (0.16, -0.62), (-0.10, -0.68), (-0.26, -0.40), (-0.26, 0.0)],
                samples=3, closed=True)
    grip.add(slab(g, 0.26, 0.08, seg=2))
    steel.add(torus(0.25, 0.075, segs=24, rsegs=8, axis="Z"), T(-0.02, -0.98, 0))
    steel.add(slab([(-0.12, -0.60), (0.12, -0.60), (0.10, -0.78), (-0.10, -0.78)], 0.14, 0.03), T(0, 0, 0))
    for y in (0.12, -0.36):
        for side in (1, -1):
            bolts.add(lathe([(0, 0.0), (0.06, 0.0), (0.065, 0.02), (0.045, 0.035), (0, 0.04)], segs=10),
                      T(0, y, side * 0.13) @ R("X", side * 90))


@weapon("Icicle", "Rare", "Dagger")
def icicle(w):
    """A long twisted icicle blade, frosty blue steel guard of little icicles,
    white grip and an ice crystal pommel."""
    ice = w.part("Ice", (186, 232, 255), "Glass", transparency=0.15, smooth=25)
    blue = w.part("Guard", (60, 140, 232), "Metal")
    grip = w.part("Grip", (244, 248, 252), "Fabric", smooth=70)
    ice.add(twisted_icicle(0.44, 3.44, 0.45, lobes=6, twist=1.1, segs=24, rings=12, sz=0.78))
    blue.add(lathe([(0, 0.28), (0.36, 0.28), (0.50, 0.35), (0.52, 0.44), (0.44, 0.52), (0, 0.52)], segs=6,
                   sz=0.66, phase=math.pi / 6))
    for sx in (1, -1):
        for dx, L in ((0.30, 0.34), (0.48, 0.26)):
            blue.add(lathe([(0, 0.0), (0.06, -0.01), (0, -L)], segs=6), T(sx * dx, 0.32, 0))
    grip.add(wrapped_grip(-0.66, 0.32, 0.125, 0.135, pitch=0.18, amp=0.02, sz=0.95))
    blue.add(lathe([(0, -0.76), (0.15, -0.76), (0.17, -0.70), (0.15, -0.64), (0, -0.64)], segs=12))
    ice.add(lathe([(0, -1.0), (0.13, -0.86), (0.12, -0.76), (0, -0.72)], segs=6))


@weapon("FrostFang", "Epic", "Dagger")
def frost_fang(w):
    """A curved fang of clear ice with a glowing frost core, blue steel guard
    crowned with ice spikes, white grip with blue wraps, ice crystal pommel."""
    ice = w.part("Ice", (186, 232, 255), "Glass", transparency=0.2, smooth=20)
    core = w.part("Core", (226, 250, 255), "Neon")
    blue = w.part("Guard", (56, 132, 232), "Metal")
    grip = w.part("Grip", (244, 248, 252), "Fabric", smooth=70)
    bm, path, widths, thicks = fang_sweep(0.46, 3.20, 0.98, curve=0.62, t_ratio=0.5, n=14, sides=8, bulge=0.2)
    ice.add(bm)
    core.add(sweep(path[1:-2], [v * 0.42 for v in widths[1:-2]], [v * 0.42 for v in thicks[1:-2]], sides=6))
    blue.add(bar_x([(-0.62, 0.20, 0.26), (-0.48, 0.28, 0.34), (0.48, 0.28, 0.34), (0.62, 0.20, 0.26)], chamfer=0.07, y=0.40))
    for sx in (1, -1):
        for dx, L, ang in ((0.20, 0.36, 12), (0.42, 0.44, 26), (0.60, 0.32, 42)):
            blue.add(lathe([(0, 0.0), (0.06, 0.02), (0, L)], segs=6), T(sx * dx, 0.48, 0) @ R("Z", -sx * ang))
    grip.add(wrapped_grip(-0.64, 0.30, 0.125, 0.135, pitch=0.18, amp=0.02, sz=0.95))
    for y in (-0.42, 0.08):
        blue.add(lathe([(0.13, y), (0.15, y + 0.02), (0.15, y + 0.08), (0.13, y + 0.10)], segs=14, close=False))
    ice.add(lathe([(0, -0.98), (0.14, -0.84), (0.13, -0.72), (0, -0.66)], segs=6))
    core.add(ico(0.06, 1), T(0, -0.82, 0))
    w.fx = (-0.50, 3.0, 0)


@weapon("ToxicFang", "Epic", "Dagger")
def toxic_fang(w):
    """Snake-fang dagger: dark curved blade with a glowing toxic-green venom groove
    and drips at the tip, green snake-jaw guard, black grip, bubbling venom pommel."""
    dark = w.part("Blade", (54, 58, 66), "Metal", smooth=18)
    venom = w.part("Venom", (120, 255, 64), "Neon")
    green = w.part("Guard", (46, 112, 50), "Metal")
    grip = w.part("Grip", (28, 28, 34), "Fabric", smooth=70)
    bm, path, widths, thicks = fang_sweep(0.44, 3.12, 0.92, curve=0.58, t_ratio=0.5, n=14, sides=10, bulge=0.2)
    dark.add(bm)
    a, b = 1, 12
    for p0, p1 in ((60, 120), (-120, -60)):
        venom.add(sweep_band(path[a:b], widths[a:b], thicks[a:b], p0, p1, lift=0.004, rise=0.012))
    tip = path[-3]
    venom.add(teardrop(0.05, 0.16, segs=10), T(tip.x + 0.02, tip.y - 0.05, 0))
    # snake-jaw guard: two curved fangs pointing up on each side of a rounded block
    green.add(bar_x([(-0.40, 0.20, 0.24), (-0.30, 0.30, 0.30), (0.30, 0.30, 0.30), (0.40, 0.20, 0.24)], chamfer=0.07, y=0.38))
    for sx in (1, -1):
        jaw = [Vector((sx * x, y, 0)) for x, y in ((0.30, 0.42), (0.56, 0.60), (0.60, 0.90), (0.50, 1.12))]
        green.add(sweep(jaw, [0.20, 0.16, 0.10, 0.0], [0.20, 0.16, 0.10, 0.0], sides=8))
    grip.add(wrapped_grip(-0.66, 0.30, 0.125, 0.135, pitch=0.18, amp=0.02, sz=0.95))
    for y in (-0.44, 0.06):
        venom.add(lathe([(0.13, y), (0.15, y + 0.02), (0.15, y + 0.06), (0.13, y + 0.08)], segs=14, close=False))
    green.add(lathe([(0, -0.74), (0.15, -0.74), (0.17, -0.70), (0.15, -0.64), (0, -0.64)], segs=12))
    venom.add(sphere(0.14, 14, 9), T(0, -0.86, 0))
    for x, y, z, r in ((0.10, -0.98, 0.06, 0.045), (-0.08, -1.0, -0.05, 0.035)):
        venom.add(sphere(r, 8, 6), T(x, y, z))
    for x, y, r in ((0.52, 1.7, 0.07), (0.62, 2.0, 0.05), (0.50, 2.25, 0.035)):     # toxic bubbles rising
        venom.add(sphere(r, 10, 7), T(x, y, 0.05))
    w.fx = (tip.x, tip.y, 0)


@weapon("EmberKnife", "Epic", "Dagger")
def ember_knife(w):
    """A charcoal leaf blade split by a glowing ember core, dark iron guard with
    flame-shaped quillons, smouldering grip and an ember pommel."""
    char = w.part("Blade", (50, 36, 34), "SmoothPlastic", smooth=14)
    ember = w.part("Ember", (255, 120, 26), "Neon")
    iron = w.part("Guard", (64, 56, 58), "Metal")
    grip = w.part("Grip", (40, 28, 26), "Fabric", smooth=70)
    st = [(0.46, 0.27, 0.11, 0.06), (1.25, 0.34, 0.105, 0.065), (2.2, 0.27, 0.095, 0.06)]
    b = profile_blade(st, 3.08, n_point=6, point_curve=0.4)
    parts = split_by_tag(b, {0: "body", -1: "body", 1: "edge"})
    char.add(parts["body"])
    ember.add(parts["edge"])
    for side in (1, -1):
        ember.add(surface_vein([(0, 0.55), (0.0, 1.0), (0.0, 2.05), (0, 2.6)], 0.20, st, side=side, lift=0.004,
                               thick=0.02, taper=True))
        for br in ([(0.0, 1.0), (0.12, 1.18), (0.20, 1.24)], [(0.0, 1.55), (-0.12, 1.75), (-0.20, 1.82)]):
            ember.add(surface_vein(br, 0.05, st, side=side, lift=0.004))
    for sx in (1, -1):
        flame = catmull([(0.0, 0.0), (0.20, 0.06), (0.42, 0.24), (0.50, 0.52), (0.40, 0.40), (0.34, 0.62), (0.22, 0.32),
                         (0.10, 0.20)], samples=2, closed=True)
        iron.add(slab(flame, 0.18, 0.05, seg=1), S(sx, 1, 1) @ T(0.10, 0.30, 0) @ S(1.3))
    iron.add(bar_y([(0.28, 0.34, 0.26, 0.06), (0.48, 0.38, 0.28, 0.06)]))
    grip.add(wrapped_grip(-0.64, 0.30, 0.125, 0.135, pitch=0.18, amp=0.02, sz=0.95))
    iron.add(lathe([(0, -0.74), (0.15, -0.74), (0.17, -0.70), (0.15, -0.64), (0, -0.64)], segs=12))
    ember.add(ico(0.13, 1, scale=(1.0, 1.2, 1.0)), T(0, -0.86, 0))
    w.fx = (0, 2.95, 0)


@weapon("StarShard", "Legendary", "Dagger")
def star_shard(w):
    """A long faceted gold shard of a fallen star with a glowing four-point star
    set at its base and a light streak up its core, navy grip with gold trim,
    star pommel and little stars orbiting the blade."""
    gold = w.part("Shard", (255, 204, 56), "Metal", smooth=8)
    light = w.part("Light", (255, 252, 230), "Neon")
    stars = w.part("Stars", (255, 236, 120), "Neon")
    grip = w.part("Grip", (28, 40, 106), "Fabric", smooth=70)
    gold.add(lathe([(0, 0.50), (0.42, 0.62), (0.46, 1.2), (0.31, 2.6), (0, 3.78)], segs=4, sz=0.45))
    for side in (1, -1):
        light.add(lathe([(0, 1.0), (0.05, 1.08), (0.04, 2.6), (0, 3.2)], segs=4, sz=0.5), T(0, 0, side * 0.115))
    big = slab(star_pts(4, 0.74, 0.15, rot=90), 0.10, 0.0)
    light.add(big, T(0, 0.86, 0.20))
    light.add(big, T(0, 0.86, -0.20))
    gold.add(bar_x([(-0.34, 0.16, 0.26), (0.34, 0.16, 0.26)], chamfer=0.06, y=0.42))
    grip.add(wrapped_grip(-0.64, 0.34, 0.125, 0.135, pitch=0.18, amp=0.02, sz=0.95))
    gold.add(lathe([(0, -0.74), (0.15, -0.74), (0.17, -0.70), (0.15, -0.64), (0, -0.64)], segs=12))
    stars.add(slab(star_pts(5, 0.22, 0.09), 0.10, 0.0), T(0, -0.92, 0))
    sm = slab(star_pts(5, 0.13, 0.055), 0.06, 0.0)
    for x, y, z, r in ((0.98, 1.55, 0.1, 15), (-0.98, 2.25, -0.1, -20), (0.66, 3.10, 0.0, 30), (-0.86, 1.15, 0.12, 5)):
        stars.add(sm, T(x, y, z) @ R("Z", r))
    w.fx = (0, 0.86, 0)


# ================================================================ DAGGERS: limited (Halloween)

@weapon("CandyCornDagger", "Limited", "Dagger")
def candy_corn_dagger(w):
    """A giant glossy candy corn on a candy stick: yellow, orange and white bands,
    a purple ribbon bow and purple swirl stripes down the white stick."""
    yellow = w.part("Base", (255, 208, 52), "SmoothPlastic", smooth=40)
    orange = w.part("Mid", (255, 134, 30), "SmoothPlastic", smooth=40)
    white = w.part("Tip", (250, 248, 240), "SmoothPlastic", smooth=40)
    purple = w.part("Ribbon", (140, 62, 206), "SmoothPlastic", smooth=45)

    def band(y0, y1, w0, w1):
        pts = catmull([(-w0, y0), (w0, y0), (lerp(w0, w1, 0.5) + 0.02, (y0 + y1) / 2), (w1, y1), (-w1, y1),
                       (-lerp(w0, w1, 0.5) - 0.02, (y0 + y1) / 2)], samples=2, closed=True)
        return slab(pts, 0.40, 0.14, seg=3)
    yellow.add(band(0.46, 1.42, 0.56, 0.44))
    orange.add(band(1.42, 2.46, 0.44, 0.26))
    tip = catmull([(-0.26, 2.46), (0.26, 2.46), (0.17, 2.86), (0.06, 3.18), (0.0, 3.24), (-0.06, 3.18), (-0.17, 2.86)],
                  samples=2, closed=True)
    white.add(slab(tip, 0.36, 0.13, seg=3))
    white.add(lathe([(0, -0.92), (0.10, -0.92), (0.13, -0.88), (0.13, 0.50), (0, 0.50)], segs=16))
    purple.add(helix_ribbon(-0.86, 0.40, 0.13, 0.13, 3.5, 0.07, 0.012, samples_per_turn=12))
    for sx in (1, -1):
        loop = catmull([(0, 0), (0.30, 0.15), (0.34, -0.04), (0.24, -0.14)], samples=3, closed=True)
        purple.add(slab(loop, 0.09, 0.03, seg=1), T(0, 0.46, 0.21) @ S(sx, 1, 1))
        tail = catmull([(0.02, -0.02), (0.13, -0.30), (0.05, -0.32), (-0.02, -0.06)], samples=2, closed=True)
        purple.add(slab(tail, 0.07, 0.02, seg=1), T(0, 0.44, 0.21) @ S(sx, 1, 1))
    purple.add(sphere(0.075, 10, 7, scale=(1.0, 1.0, 0.7)), T(0, 0.46, 0.23))
    w.fx = (0, 3.1, 0)


@weapon("VampireFang", "Limited", "Dagger")
def vampire_fang(w):
    """A big glossy vampire fang, cute scalloped bat wings spreading from a glowing
    purple gem, purple grip and a little bat-ear pommel."""
    fang = w.part("Fang", (250, 246, 236), "SmoothPlastic", smooth=45)
    wings = w.part("Wings", (44, 30, 60), "SmoothPlastic", smooth=35)
    gem = w.part("Gem", (196, 92, 255), "Neon")
    grip = w.part("Grip", (88, 40, 132), "Fabric", smooth=70)
    bm, path, widths, thicks = fang_sweep(0.42, 3.02, 0.70, curve=0.48, t_ratio=0.55, n=14, sides=12)
    fang.add(bm)
    for sx in (1, -1):
        wing = slab(bat_wing_pts(1.16, 0.78, scallops=3), 0.09, 0.025, seg=1)
        wings.add(wing, S(sx, 1, 1) @ T(0.12, 0.34, 0) @ R("Z", 18))
        wings.add(lathe([(0, 0.0), (0.05, 0.03), (0, 0.16)], segs=6), T(sx * 0.13, 0.62, 0) @ R("Z", -sx * 15))
    wings.add(sphere(0.20, 14, 9, scale=(1.1, 0.9, 0.9)), T(0, 0.42, 0))
    gem.add(lathe([(0, 0.0), (0.13, 0.04), (0.14, 0.07), (0.08, 0.12), (0, 0.12)], segs=8), T(0, 0.42, 0.15) @ R("X", 90))
    gem.add(lathe([(0, 0.0), (0.13, 0.04), (0.14, 0.07), (0.08, 0.12), (0, 0.12)], segs=8), T(0, 0.42, -0.15) @ R("X", -90))
    grip.add(wrapped_grip(-0.62, 0.26, 0.125, 0.135, pitch=0.18, amp=0.02, sz=0.95))
    wings.add(lathe([(0, -0.80), (0.15, -0.78), (0.17, -0.70), (0.15, -0.62), (0, -0.62)], segs=12))
    for sx in (1, -1):
        wings.add(lathe([(0, 0.0), (0.06, 0.02), (0, -0.15)], segs=6), T(sx * 0.09, -0.78, 0) @ R("Z", sx * 20))
    w.fx = (path[-2].x, path[-2].y, 0)


@weapon("SpiderStinger", "Limited", "Dagger")
def spider_stinger(w):
    """A black stinger needle with a glowing purple venom stripe, a cute round
    spider with big googly eyes hugging the guard, purple grip, egg-sac pommel."""
    needle = w.part("Needle", (40, 40, 48), "Metal", smooth=20)
    venom = w.part("Venom", (190, 90, 255), "Neon")
    spider = w.part("Spider", (36, 34, 44), "SmoothPlastic", smooth=45)
    eyes = w.part("Eyes", (250, 250, 250), "SmoothPlastic", smooth=50)
    grip = w.part("Grip", (128, 56, 196), "Fabric", smooth=70)
    needle.add(lathe([(0, 0.48), (0.20, 0.52), (0.18, 1.2), (0.10, 2.4), (0, 3.20)], segs=6, sz=0.6, phase=math.pi / 6))
    for side in (1, -1):
        venom.add(lathe([(0, 0.70), (0.05, 0.76), (0.04, 2.2), (0, 2.75)], segs=4, sz=0.5), T(0, 0, side * 0.105))
    # the spider: round body and head with eight bent legs
    spider.add(sphere(0.34, 16, 10, scale=(1.0, 0.85, 0.85)), T(0, 0.36, 0))
    spider.add(sphere(0.21, 14, 9), T(0, 0.68, 0.10))
    for sx in (1, -1):
        for k, (ang, L) in enumerate(((-40, 0.62), (-12, 0.66), (14, 0.64), (40, 0.58))):
            a = math.radians(ang)
            base = Vector((sx * 0.26, 0.44 - 0.08 * k, 0.0))
            knee = base + Vector((sx * 0.38, 0.26, 0.06 * math.sin(a)))
            foot = knee + Vector((sx * 0.20, -0.46 - 0.06 * k, 0.15 * math.sin(a)))
            leg = [base, knee, foot]
            spider.add(sweep(leg, [0.09, 0.08, 0.04], [0.09, 0.08, 0.04], sides=6, point_end=False))
        eyes.add(sphere(0.105, 12, 8), T(sx * 0.09, 0.75, 0.27))
        spider.add(sphere(0.05, 8, 6), T(sx * 0.088, 0.76, 0.37))
    grip.add(wrapped_grip(-0.66, 0.18, 0.125, 0.135, pitch=0.18, amp=0.02, sz=0.95))
    venom.add(sphere(0.14, 14, 9, scale=(1.0, 1.25, 1.0)), T(0, -0.80, 0))
    w.fx = (0, 3.05, 0)



# ================================================================ HAMMERS: commons and uncommons

def lathe_x(profile, segs=24, sy=1.0, sz=1.0, rmod=None, close=True):
    """Surface of revolution around the X axis (profile = [(r, x), ...]); for
    hammer heads, barrels and bellows lying across the top of a shaft."""
    bm = lathe(profile, segs=segs, sx=sy, sz=sz, rmod=rmod, close=close)
    from wlib import xform as _xf
    return _xf(bm, R("Z", -90))


def lathe_z(profile, segs=24, sx=1.0, sy=1.0, rmod=None):
    """Surface of revolution around the Z axis (faces toward the viewer): pans,
    signs, lollipops. profile = [(r, z), ...]."""
    bm = lathe(profile, segs=segs, sx=sx, sz=sy, rmod=rmod)
    from wlib import xform as _xf
    return _xf(bm, R("X", 90))


def shaft(r, y0, y1, segs=16, taper=1.0):
    return lathe([(0, y0), (r, y0), (r * taper, y1), (0, y1)], segs=segs)


@weapon("Mallet", "Common", "Hammer")
def mallet(w):
    """Wooden mallet: a chunky barrel head with dark wooden end bands, a turned
    wooden shaft and a leather-wrapped grip."""
    head = w.part("Head", (206, 146, 80), "Wood", smooth=40)
    bands = w.part("Bands", (126, 80, 40), "Wood", smooth=40)
    wood = w.part("Shaft", (176, 118, 62), "Wood", smooth=40)
    grip = w.part("Grip", (98, 60, 28), "Fabric", smooth=70)
    hy = 2.40
    head.add(lathe_x([(0, -0.76), (0.47, -0.76), (0.53, -0.70), (0.555, -0.40), (0.565, 0.0), (0.555, 0.40),
                      (0.53, 0.70), (0.47, 0.76), (0, 0.76)], segs=28), T(0, hy, 0))
    for x in (-0.56, 0.56):
        bands.add(lathe_x([(0.53, -0.07), (0.585, -0.05), (0.585, 0.05), (0.53, 0.07)], segs=28), T(x, hy, 0))
    wood.add(shaft(0.13, 0.55, hy - 0.3, taper=1.08))
    grip.add(wrapped_grip(-0.66, 0.60, 0.15, 0.16, pitch=0.22, amp=0.022, sz=1.0))
    bands.add(lathe([(0, -0.80), (0.12, -0.80), (0.19, -0.74), (0.20, -0.66), (0.17, -0.62), (0, -0.62)], segs=16))
    bands.add(lathe([(0.15, 0.58), (0.18, 0.62), (0.18, 0.70), (0.15, 0.74)], segs=16, close=False))


@weapon("Gavel", "Common", "Hammer")
def gavel(w):
    """Judge's gavel: a turned wooden head with wide ringed striking ends and gold
    bands, a beaded turned shaft and a leather grip."""
    head = w.part("Head", (142, 88, 44), "Wood", smooth=35)
    gold = w.part("Bands", (242, 188, 56), "Metal")
    wood = w.part("Shaft", (112, 68, 34), "Wood", smooth=35)
    grip = w.part("Grip", (62, 38, 22), "Fabric", smooth=70)
    hy = 2.40
    head.add(lathe_x([(0, -0.72), (0.38, -0.72), (0.42, -0.68), (0.42, -0.42), (0.34, -0.36), (0.30, -0.18), (0.36, 0.0),
                      (0.30, 0.18), (0.34, 0.36), (0.42, 0.42), (0.42, 0.68), (0.38, 0.72), (0, 0.72)], segs=28),
             T(0, hy, 0))
    for x in (-0.48, 0.48, -0.66, 0.66):
        gold.add(lathe_x([(0.41, -0.025), (0.435, -0.015), (0.435, 0.015), (0.41, 0.025)], segs=24), T(x, hy, 0))
    prof = [(0, 0.55), (0.12, 0.55)]
    for k in range(6):
        y = 0.62 + k * 0.22
        prof += [(0.115, y), (0.145, y + 0.06), (0.115, y + 0.12)]
    prof += [(0.11, hy - 0.2), (0, hy - 0.2)]
    wood.add(lathe(prof, segs=12))
    grip.add(wrapped_grip(-0.66, 0.58, 0.14, 0.15, pitch=0.21, amp=0.02, sz=1.0))
    gold.add(lathe([(0, -0.82), (0.11, -0.82), (0.17, -0.76), (0.18, -0.68), (0.15, -0.62), (0, -0.62)], segs=16))
    gold.add(lathe([(0.14, 0.56), (0.165, 0.59), (0.165, 0.66), (0.14, 0.69)], segs=16, close=False))


@weapon("FryingPan", "Common", "Hammer")
def frying_pan(w):
    """Cast iron frying pan with a sunny-side-up egg in it and a wooden handle."""
    iron = w.part("Pan", (48, 48, 56), "Metal", smooth=35)
    egg = w.part("Egg", (250, 250, 246), "SmoothPlastic", smooth=40)
    yolk = w.part("Yolk", (255, 196, 36), "SmoothPlastic", smooth=50)
    wood = w.part("Grip", (112, 70, 36), "Wood", smooth=45)
    py = 2.74
    iron.add(lathe_z([(0, -0.14), (0.86, -0.14), (0.94, -0.12), (1.0, 0.06), (1.0, 0.12), (0.96, 0.13), (0.90, 0.0),
                      (0.84, -0.06), (0, -0.06)], segs=40), T(0, py, 0))
    white = catmull([(0.0, 0.46), (0.36, 0.38), (0.52, 0.06), (0.38, -0.32), (0.06, -0.44), (-0.30, -0.36),
                     (-0.48, -0.04), (-0.40, 0.30)], samples=3, closed=True)
    egg.add(slab(white, 0.06, 0.02, seg=1), T(0.04, py, -0.035))
    yolk.add(sphere(0.20, 16, 9, scale=(1.0, 1.0, 0.55)), T(0.08, py + 0.06, -0.02))
    # neck from the rim and the wooden handle
    neck = [Vector((0, y, 0)) for y in (py - 0.92, py - 1.3, 0.62)]
    iron.add(sweep(neck, [0.22, 0.18, 0.18], [0.10, 0.10, 0.10], sides=8, point_end=False))
    wood.add(lathe([(0, -0.80), (0.12, -0.80), (0.17, -0.74), (0.18, 0.40), (0.15, 0.66), (0, 0.66)], segs=16, sz=0.75))
    iron.add(torus(0.07, 0.025, segs=12, rsegs=5, axis="Z"), T(0, -0.66, 0.0))


@weapon("Plunger", "Common", "Hammer")
def plunger(w):
    """A big red rubber plunger: ribbed cup on top, wooden stick, rubber grip."""
    cup = w.part("Cup", (198, 52, 44), "SmoothPlastic", smooth=45)
    wood = w.part("Shaft", (226, 170, 94), "Wood", smooth=40)
    grip = w.part("Grip", (64, 40, 30), "SmoothPlastic", smooth=45)
    cup.add(lathe([(0, 2.02), (0.12, 2.02), (0.30, 2.14), (0.60, 2.40), (0.80, 2.80), (0.86, 3.04), (0.88, 3.12),
                   (0.80, 3.12), (0.74, 2.92), (0.52, 2.62), (0.20, 2.46), (0, 2.42)], segs=32,
                  rmod=lambda a: 1 + 0.015 * math.cos(12 * a)))
    cup.add(lathe([(0.16, 2.06), (0.19, 2.0), (0.19, 1.92), (0.15, 1.88)], segs=16, close=False))
    wood.add(shaft(0.12, 0.40, 2.05))
    prof = [(0, -0.80), (0.15, -0.80), (0.17, -0.74)]
    for k in range(6):
        y = -0.70 + k * 0.18
        prof += [(0.165, y), (0.18, y + 0.06), (0.165, y + 0.12)]
    prof += [(0.15, 0.44), (0, 0.44)]
    grip.add(lathe(prof, segs=16))


@weapon("SqueakyHammer", "Uncommon", "Hammer")
def squeaky_hammer(w):
    """Toy squeaky hammer: red pleated bellows head with bright yellow end caps
    and a chunky blue handle."""
    red = w.part("Head", (232, 42, 40), "SmoothPlastic", smooth=35)
    yellow = w.part("Caps", (255, 206, 46), "SmoothPlastic", smooth=45)
    blue = w.part("Grip", (52, 140, 250), "SmoothPlastic", smooth=45)
    hy = 2.30
    prof = [(0, -0.64), (0.42, -0.64)]
    n = 7
    for k in range(n + 1):
        x = lerp(-0.64, 0.64, k / n)
        prof.append((0.50 if k % 2 == 0 else 0.42, x))
    prof += [(0.42, 0.64), (0, 0.64)]
    red.add(lathe_x(prof, segs=28), T(0, hy, 0))
    for sx in (1, -1):
        yellow.add(lathe_x([(0, 0.0), (0.54, 0.0), (0.56, 0.06), (0.52, 0.16), (0.36, 0.24), (0, 0.27)], segs=28),
                   T(sx * 0.62, hy, 0) @ S(sx, 1, 1))
    blue.add(lathe([(0, -0.86), (0.13, -0.86), (0.21, -0.78), (0.22, -0.60), (0.17, -0.40), (0.16, 0.40),
                    (0.15, hy - 0.45), (0.20, hy - 0.38), (0, hy - 0.30)], segs=18))
    yellow.add(lathe([(0.15, 0.30), (0.19, 0.34), (0.19, 0.46), (0.15, 0.50)], segs=18, close=False))


@weapon("Sledgehammer", "Uncommon", "Hammer")
def sledgehammer(w):
    """Sledgehammer: chamfered steel double-faced head with polished domed faces,
    dark steel collar, long hickory handle and black rubber grip."""
    steel = w.part("Head", (146, 154, 172), "Metal", smooth=25)
    faces = w.part("Faces", (214, 220, 232), "Metal", smooth=40)
    collar = w.part("Collar", (70, 76, 94), "Metal", smooth=30)
    wood = w.part("Shaft", (176, 118, 62), "Wood", smooth=40)
    grip = w.part("Grip", (40, 40, 48), "SmoothPlastic", smooth=45)
    hy = 3.80
    steel.add(bar_x([(-1.0, 0.92, 0.90, 0.14), (-0.76, 1.10, 1.06, 0.16), (0.76, 1.10, 1.06, 0.16),
                     (1.0, 0.92, 0.90, 0.14)], y=hy))
    for sx in (1, -1):
        faces.add(lathe_x([(0, 0.0), (0.42, 0.0), (0.44, 0.04), (0.40, 0.10), (0.23, 0.14), (0, 0.15)], segs=8,
                          rmod=lambda a: 1.0 / max(abs(math.cos(a)), abs(math.sin(a))) ** 0.6),
                  T(sx * 1.0, hy, 0) @ S(sx, 1, 1))
    # dark steel band round the middle of the head, with a wedge collar under it
    collar.add(bar_x([(-0.26, 1.15, 1.11, 0.05), (0.26, 1.15, 1.11, 0.05)], y=hy))
    collar.add(bar_y([(hy - 0.86, 0.40, 0.38, 0.06), (hy - 0.50, 0.48, 0.46, 0.06)]))
    wood.add(lathe([(0, -0.40), (0.15, -0.40), (0.16, 0.6), (0.14, 2.0), (0.15, hy - 0.46), (0, hy - 0.46)], segs=16,
                   sz=0.85))
    prof = [(0, -1.16), (0.17, -1.16), (0.20, -1.10)]
    for k in range(7):
        y = -1.04 + k * 0.17
        prof += [(0.19, y), (0.205, y + 0.06), (0.19, y + 0.11)]
    prof += [(0.18, 0.20), (0.15, 0.28), (0, 0.28)]
    grip.add(lathe(prof, segs=16, sz=0.85))


@weapon("MeatTenderizer", "Uncommon", "Hammer")
def meat_tenderizer(w):
    """Meat tenderizer: steel head with a grid of pyramid studs on each face,
    wooden handle with a steel hanging ring."""
    steel = w.part("Head", (220, 226, 238), "Metal", smooth=30)
    studs = w.part("Studs", (150, 160, 182), "Metal", smooth=10)
    wood = w.part("Shaft", (200, 140, 76), "Wood", smooth=40)
    grip = w.part("Grip", (138, 90, 44), "Fabric", smooth=70)
    hy = 2.38
    steel.add(bar_x([(-0.60, 0.88, 0.88, 0.10), (0.60, 0.88, 0.88, 0.10)], y=hy))
    for sx in (1, -1):
        for iy in range(4):
            for iz in range(4):
                y = hy - 0.30 + iy * 0.20
                z = -0.30 + iz * 0.20
                studs.add(pyramid(0.17, 0.14), T(sx * 0.60, y, z) @ R("Z", -sx * 90))
    wood.add(lathe([(0, 0.45), (0.13, 0.45), (0.14, 1.2), (0.13, hy - 0.40), (0, hy - 0.40)], segs=16))
    grip.add(wrapped_grip(-0.66, 0.50, 0.15, 0.16, pitch=0.21, amp=0.02, sz=1.0))
    steel.add(torus(0.13, 0.035, segs=16, rsegs=6, axis="Z"), T(0, -0.84, 0))
    steel.add(lathe([(0, -0.74), (0.14, -0.74), (0.16, -0.70), (0.14, -0.64), (0, -0.64)], segs=14))


@weapon("StopSign", "Uncommon", "Hammer")
def stop_sign(w):
    """A real stop sign on its pole: red octagon with a white border ring and big
    white STOP letters, metal pole and bracket, black rubber grip."""
    red = w.part("Sign", (224, 26, 32), "SmoothPlastic", smooth=30)
    white = w.part("Letters", (250, 250, 250), "SmoothPlastic", smooth=30)
    pole = w.part("Pole", (176, 184, 198), "Metal", smooth=40)
    grip = w.part("Grip", (32, 32, 38), "SmoothPlastic", smooth=45)
    sy = 2.90
    red.add(slab(octagon_pts(1.0), 0.14, 0.045, seg=1), T(0, sy, 0))
    for side in (1, -1):
        ring = [list(reversed(octagon_pts(0.84)))]
        white.add(slab_holes(octagon_pts(0.92), ring, 0.03, 0.0), T(0, sy, side * 0.075))
        txt = drop_facing(text_slab("STOP", 0.60, 0.03, 0.0, spacing=0.95, res=3), (0, 0, -1))
        white.add(txt, T(0, sy - 0.02, side * 0.075) @ R("Y", 0 if side > 0 else 180))
    # the pole stops at the sign's bottom edge, gripped by a clamp, so both faces stay clean
    pole.add(shaft(0.09, -1.02, sy - 0.86, segs=12))
    pole.add(bar_y([(sy - 1.08, 0.30, 0.24, 0.04), (sy - 0.74, 0.30, 0.24, 0.04)]))
    for side in (1, -1):
        for x in (-0.08, 0.08):
            pole.add(cylinder(0.035, 0.04, segs=8), T(x, sy - 0.86, side * 0.12) @ R("X", 90))
    prof = [(0, -1.06), (0.15, -1.06), (0.17, -1.0)]
    for k in range(7):
        y = -0.96 + k * 0.20
        prof += [(0.165, y), (0.18, y + 0.07), (0.165, y + 0.14)]
    prof += [(0.15, 0.48), (0, 0.48)]
    grip.add(lathe(prof, segs=16))


# ================================================================ HAMMERS: rares

def aim(d, up=(0, 1, 0)):
    """Rotation taking +Y to direction d with +Z turned as close to `up` as it can go."""
    from mathutils import Matrix
    d = Vector(d).normalized()
    n = Vector(up)
    n = (n - d * n.dot(d)).normalized()
    x = d.cross(n)
    m = Matrix.Identity(4)
    for i in range(3):
        m[i][0], m[i][1], m[i][2] = x[i], d[i], n[i]
    return m


def densify(points, step=0.06, closed=True):
    """Insert points along each edge of an outline so no edge is longer than `step`."""
    out = []
    n = len(points)
    for i in range(n if closed else n - 1):
        (xa, ya), (xb, yb) = points[i], points[(i + 1) % n]
        k = max(1, int(math.ceil(math.hypot(xb - xa, yb - ya) / step)))
        for j in range(k):
            out.append((lerp(xa, xb, j / k), lerp(ya, yb, j / k)))
    if not closed:
        out.append(points[-1])
    return out


def band(r0, y0, y1, r1=None, segs=16):
    """An open ring band around the Y axis (a raised collar on a shaft)."""
    r1 = r0 + 0.03 if r1 is None else r1
    h = y1 - y0
    return lathe([(r0, y0), (r1, y0 + h * 0.2), (r1, y1 - h * 0.2), (r0, y1)], segs=segs, close=False)


@weapon("WarHammer", "Rare", "Hammer")
def war_hammer(w):
    """Knight's war hammer: a blued-steel head flaring into a big gold striking face,
    a curved crow's-beak spike at the back and a gold top spike, rubies set in gold
    bosses on both sides, steel langets down an oak shaft, a leather grip and a
    faceted gold pommel."""
    steel = w.part("Head", (62, 70, 92), "Metal", smooth=25)
    gold = w.part("Trim", (255, 198, 56), "Metal", smooth=30)
    gem = w.part("Gem", (236, 34, 66), "Glass", transparency=0.12, smooth=10)
    wood = w.part("Shaft", (120, 74, 38), "Wood", smooth=40)
    grip = w.part("Grip", (142, 90, 44), "Fabric", smooth=70)
    hy = 3.80
    steel.add(bar_x([(-0.50, 1.00, 0.90, 0.10), (0.20, 1.04, 0.94, 0.12), (0.80, 1.22, 1.06, 0.15)], y=hy))
    gold.add(bar_x([(0.78, 1.28, 1.12, 0.16), (1.02, 1.36, 1.18, 0.18), (1.12, 1.36, 1.18, 0.18),
                    (1.20, 1.22, 1.04, 0.14)], y=hy))
    # crow's-beak spike curving down at the back
    beak = [Vector((x, hy + y, 0)) for x, y in ((-0.44, 0.02), (-0.82, 0.0), (-1.16, -0.08), (-1.42, -0.24),
                                                 (-1.56, -0.42))]
    steel.add(sweep(beak, [0.80, 0.60, 0.40, 0.20, 0.0], [0.72, 0.54, 0.36, 0.18, 0.0], sides=4))
    gold.add(bar_x([(-0.56, 1.08, 0.98, 0.08), (-0.40, 1.08, 0.98, 0.08)], y=hy))
    # gold centre band with a ruby in a gold boss on each side
    gold.add(bar_x([(-0.16, 1.10, 1.00, 0.08), (0.16, 1.10, 1.00, 0.08)], y=hy))
    for side in (1, -1):
        gold.add(lathe([(0, 0.0), (0.25, 0.0), (0.26, 0.03), (0.22, 0.08), (0, 0.08)], segs=16),
                 T(0, hy, side * 0.48) @ R("X", side * 90))
        gem.add(lathe([(0, 0.0), (0.17, 0.0), (0.17, 0.035), (0.11, 0.10), (0, 0.11)], segs=8),
                T(0, hy, side * 0.54) @ R("X", side * 90))
    # gold top spike on a square base
    gold.add(bar_y([(hy + 0.46, 0.50, 0.50, 0.05), (hy + 0.60, 0.44, 0.44, 0.05)]))
    gold.add(lathe([(0, hy + 0.58), (0.26, hy + 0.58), (0, 5.12)], segs=4, phase=math.pi / 4))
    # langets riveted down the shaft
    for side in (1, -1):
        lang = [(-0.08, 0.0), (0.08, 0.0), (0.08, -0.80), (0.0, -0.96), (-0.08, -0.80)]
        steel.add(slab(lang, 0.05, 0.015, seg=1), T(0, hy - 0.46, side * 0.165))
        for ry in (-0.28, -0.64):
            gold.add(sphere(0.04, 8, 5, scale=(1, 1, 0.6)), T(0, hy - 0.46 + ry, side * 0.192))
    wood.add(lathe([(0, 0.34), (0.15, 0.34), (0.155, 1.6), (0.15, hy - 0.4), (0, hy - 0.4)], segs=16))
    gold.add(band(0.15, 1.92, 2.06, 0.172))
    gold.add(band(0.15, 0.34, 0.49, 0.18))
    grip.add(wrapped_grip(-0.98, 0.38, 0.16, 0.172, pitch=0.22, amp=0.022, around=12))
    gold.add(lathe([(0, -1.37), (0.09, -1.36), (0.20, -1.24), (0.22, -1.12), (0.19, -1.02), (0.16, -0.98),
                    (0, -0.98)], segs=8))


@weapon("Lollipop", "Rare", "Hammer")
def lollipop(w):
    """Giant swirl lollipop: a thick pink candy disc with a raised white spiral on
    both faces, a white stick wound with a pink candy stripe, and a shiny gold foil
    bow tied under the candy."""
    pink = w.part("Candy", (255, 118, 168), "SmoothPlastic", smooth=40)
    white = w.part("Swirl", (252, 250, 252), "SmoothPlastic", smooth=40)
    stick = w.part("Stick", (246, 244, 248), "SmoothPlastic", smooth=45)
    gold = w.part("Bow", (255, 202, 64), "Metal", smooth=45)
    cy = 2.72
    pink.add(lathe_z([(0, -0.21), (0.90, -0.21), (0.965, -0.185), (1.0, -0.11), (1.0, 0.11), (0.965, 0.185),
                      (0.90, 0.21), (0, 0.21)], segs=36), T(0, cy, 0))
    swirl = drop_facing(slab(spiral_band_pts(0.06, 0.80, 2.6, 0.17, n=66), 0.05, 0.0), (0, 0, -1))
    for side in (1, -1):
        white.add(swirl, T(0, cy, side * 0.222) @ R("Y", 0 if side > 0 else 180))
    stick.add(lathe([(0, -0.75), (0.095, -0.75), (0.125, -0.72), (0.125, cy - 0.6), (0, cy - 0.6)], segs=16))
    pink.add(helix_ribbon(-0.62, cy - 1.32, 0.125, 0.125, 4.0, 0.09, 0.014, samples_per_turn=14))
    # gold foil bow just under the candy
    by = cy - 1.24
    gold.add(band(0.125, by - 0.07, by + 0.07, 0.16))
    for sx in (1, -1):
        loop = catmull([(0.0, 0.0), (0.26, 0.24), (0.54, 0.20), (0.57, -0.03), (0.32, -0.12)], samples=2, closed=True)
        gold.add(slab(loop, 0.12, 0.035, seg=1), T(0, by, 0) @ S(sx, 1, 1))
        tail = catmull([(0.05, -0.05), (0.24, -0.42), (0.14, -0.50), (0.0, -0.12)], samples=2, closed=True)
        gold.add(slab(tail, 0.09, 0.025, seg=1), T(0, by, 0) @ S(sx, 1, 1))
    gold.add(sphere(0.14, 10, 6, scale=(1.0, 0.9, 1.0)), T(0, by, 0))


@weapon("AnvilHammer", "Rare", "Hammer")
def anvil_hammer(w):
    """Anvil on a stick: a proper blacksmith's anvil in dark iron with a polished
    steel working face (hardy and pritchel holes), a long tapering horn toward +X,
    a waisted body on arched feet, gold rivets, an oak shaft and a dark grip."""
    iron = w.part("Anvil", (58, 64, 82), "Metal", smooth=25)
    face = w.part("Top", (188, 196, 212), "Metal", smooth=25)
    gold = w.part("Rivets", (242, 186, 56), "Metal", smooth=30)
    wood = w.part("Shaft", (120, 76, 38), "Wood", smooth=40)
    grip = w.part("Grip", (44, 44, 54), "Fabric", smooth=70)
    ty = 4.40      # top of the iron table
    iron.add(bar_x([(-1.00, 0.30, 0.84, 0.05), (0.74, 0.30, 0.84, 0.05)], y=ty - 0.15))
    horn = [Vector((x, ty + dy, 0)) for x, dy in ((0.60, -0.20), (0.92, -0.15), (1.22, -0.09), (1.42, -0.05),
                                                   (1.60, -0.02))]
    iron.add(sweep(horn, [0.44, 0.31, 0.19, 0.11, 0.0], [0.58, 0.40, 0.24, 0.13, 0.0], sides=12))
    iron.add(bar_y([(ty - 1.00, 1.30, 0.84, 0.06), (ty - 0.86, 0.96, 0.66, 0.06), (ty - 0.66, 0.78, 0.58, 0.05),
                    (ty - 0.46, 1.04, 0.66, 0.06), (ty - 0.28, 1.56, 0.80, 0.05)], x=-0.12))
    base = [(-1.02, 0.0), (-0.40, 0.0), (-0.32, 0.10), (-0.18, 0.17), (0.0, 0.19), (0.16, 0.17), (0.28, 0.10),
            (0.36, 0.0), (0.86, 0.0), (0.82, 0.10), (0.68, 0.30), (0.62, 0.46), (-0.74, 0.46), (-0.80, 0.30),
            (-0.96, 0.10)]
    iron.add(slab(base, 0.96, 0.05, seg=1), T(-0.08, ty - 1.40, 0))
    # polished working face with the square hardy hole and round pritchel hole
    hardy = [(-0.62, -0.07), (-0.48, -0.07), (-0.48, 0.07), (-0.62, 0.07)]
    pritchel = circle_pts(0.05, n=10, cx=-0.32)
    face.add(slab_holes(rounded_rect_pts(1.72, 0.78, 0.05, n=2), [list(reversed(hardy)), list(reversed(pritchel))],
                        0.07, 0.02), T(-0.13, ty + 0.025, 0) @ R("X", -90))
    # socket under the base, gold rivets
    iron.add(bar_y([(ty - 1.70, 0.40, 0.40, 0.05), (ty - 1.21, 0.46, 0.46, 0.05)]))
    for side in (1, -1):
        gold.add(sphere(0.05, 8, 6, scale=(1, 1, 0.6)), T(0, ty - 1.50, side * 0.235))
        for x in (-0.82, 0.58):
            gold.add(sphere(0.055, 8, 6, scale=(1, 1, 0.6)), T(x, ty - 1.18, side * 0.48))
    wood.add(lathe([(0, 0.30), (0.15, 0.30), (0.155, 1.6), (0.15, ty - 1.5), (0, ty - 1.5)], segs=16))
    grip.add(wrapped_grip(-1.02, 0.32, 0.17, 0.18, pitch=0.22, amp=0.022, around=12))
    gold.add(band(0.15, 0.28, 0.43, 0.185))
    iron.add(lathe([(0, -1.15), (0.10, -1.15), (0.19, -1.08), (0.20, -1.0), (0.17, -0.98), (0, -0.98)], segs=10))


@weapon("GoldMallet", "Rare", "Hammer")
def gold_mallet(w):
    """Polished gold mallet: a barrel head with flared rims, deep-gold bands, a
    raised star on each pale-gold striking face and rubies round the middle band,
    a white shaft with gold fittings and a red velvet grip."""
    gold = w.part("Head", (255, 204, 62), "Metal", smooth=35)
    deep = w.part("Bands", (216, 148, 20), "Metal", smooth=35)
    caps = w.part("Caps", (255, 238, 156), "Metal", smooth=35)
    gem = w.part("Gems", (236, 30, 66), "Glass", transparency=0.12, smooth=10)
    shaft = w.part("Shaft", (246, 246, 250), "SmoothPlastic", smooth=45)
    grip = w.part("Grip", (184, 30, 44), "Fabric", smooth=70)
    hy = 2.36
    gold.add(lathe_x([(0, -0.80), (0.47, -0.80), (0.535, -0.76), (0.545, -0.68), (0.50, -0.60), (0.495, -0.30),
                      (0.51, 0.0), (0.495, 0.30), (0.50, 0.60), (0.545, 0.68), (0.535, 0.76), (0.47, 0.80),
                      (0, 0.80)], segs=28), T(0, hy, 0))
    for x in (-0.42, 0.42):
        deep.add(lathe_x([(0.49, -0.05), (0.53, -0.035), (0.53, 0.035), (0.49, 0.05)], segs=24, close=False),
                 T(x, hy, 0))
    deep.add(lathe_x([(0.50, -0.16), (0.545, -0.13), (0.545, 0.13), (0.50, 0.16)], segs=24, close=False), T(0, hy, 0))
    for m in (T(0, hy, 0.53) @ R("X", 90), T(0, hy, -0.53) @ R("X", -90), T(0, hy + 0.53, 0)):
        deep.add(lathe([(0.11, 0.0), (0.145, 0.0), (0.145, 0.04), (0.115, 0.055)], segs=12, close=False), m)
        gem.add(lathe([(0, 0.0), (0.12, 0.0), (0.12, 0.03), (0.08, 0.075), (0, 0.085)], segs=8), m)
    for sx in (1, -1):
        caps.add(lathe_x([(0, 0.0), (0.45, 0.0), (0.47, 0.025), (0.44, 0.07), (0, 0.09)], segs=28),
                 T(sx * 0.79, hy, 0) @ S(sx, 1, 1))
        deep.add(slab(star_pts(5, 0.27, 0.115), 0.08, 0.025, seg=1), T(sx * 0.88, hy, 0) @ R("Y", sx * 90))
    shaft.add(lathe([(0, 0.38), (0.12, 0.38), (0.125, 1.2), (0.12, hy - 0.42), (0, hy - 0.42)], segs=16))
    deep.add(lathe([(0.12, hy - 0.66), (0.15, hy - 0.62), (0.16, hy - 0.52), (0.20, hy - 0.46), (0.12, hy - 0.44)],
                   segs=16, close=False))
    deep.add(band(0.12, 0.36, 0.48, 0.16))
    grip.add(wrapped_grip(-0.70, 0.40, 0.145, 0.155, pitch=0.21, amp=0.02, around=12))
    gold.add(lathe([(0, -0.80), (0.09, -0.80), (0.16, -0.74), (0.17, -0.68), (0.15, -0.66), (0, -0.66)], segs=16))


# ================================================================ HAMMERS: epics

@weapon("MagmaMaul", "Epic", "Hammer")
def magma_maul(w):
    """A huge obsidian maul split by lava: molten glowing striking faces, glowing
    cracks running over the chunky head, obsidian crags on top, a shaft with
    glowing bands, a charred grip and a magma orb held in claws (like the Lava Blade)."""
    obs = w.part("Obsidian", (46, 32, 40), "Metal", smooth=20)
    lava = w.part("Lava", (255, 98, 18), "Neon")
    core = w.part("Core", (255, 216, 92), "Neon")
    grip = w.part("Grip", (58, 40, 38), "Fabric", smooth=70)
    hy = 3.86
    hh, hd = 1.52, 1.36
    obs.add(bar_x([(-1.04, hh - 0.22, hd - 0.22, 0.20), (-0.88, hh, hd, 0.26), (0.88, hh, hd, 0.26),
                   (1.04, hh - 0.22, hd - 0.22, 0.20)], y=hy))
    # molten striking faces with a white-hot core
    for sx in (1, -1):
        lava.add(bar_x([(0.98, 0.92, 0.76, 0.12), (1.09, 0.86, 0.70, 0.10)], y=hy), S(sx, 1, 1))
        core.add(sphere(0.25, 14, 9, scale=(0.34, 1.0, 0.8)), T(sx * 1.09, hy, 0))

    def crack(pts, z, w0, taper=True, up=Vector((0, 0, 1))):
        path = [Vector((x, hy + y, z)) for x, y in catmull(pts, samples=2)]
        n = len(path)
        ws = [w0 * ((1 - 0.75 * i / (n - 1)) if taper else 1.0) for i in range(n)]
        return sweep(path, ws, [0.05] * n, sides=4, point_end=False, up=up)
    main = [(-0.84, 0.06), (-0.58, -0.08), (-0.30, 0.10), (-0.02, -0.05), (0.28, 0.12), (0.56, -0.03), (0.84, 0.07)]
    branches = [[(-0.30, 0.10), (-0.40, 0.30), (-0.33, 0.47)], [(0.28, 0.12), (0.40, 0.30), (0.34, 0.47)],
                [(-0.02, -0.05), (0.08, -0.26), (-0.03, -0.47)], [(0.56, -0.03), (0.64, -0.28), (0.60, -0.46)],
                [(-0.58, -0.08), (-0.66, -0.30), (-0.60, -0.46)]]
    for side in (1, -1):
        m = S(1, 1, side)
        lava.add(crack(main, hd / 2, 0.10, taper=False), m)
        core.add(crack(main[1:-1], hd / 2 + 0.012, 0.035, taper=False), m)
        for br in branches:
            lava.add(crack(br, hd / 2, 0.075), m)
    # a crack across the top between obsidian crags
    top = [Vector((x, hy + hh / 2, z)) for x, z in ((-0.84, 0.08), (-0.40, -0.10), (0.0, 0.06), (0.42, -0.08),
                                                     (0.84, 0.04))]
    lava.add(sweep(top, [0.09] * 5, [0.05] * 5, sides=4, point_end=False, up=Vector((0, 1, 0))))
    for x, z, ang, L, r in ((-0.48, 0.20, 22, 0.44, 0.25), (0.04, -0.20, -4, 0.38, 0.23), (0.50, 0.22, -24, 0.42, 0.24),
                            (-0.18, 0.30, 8, 0.24, 0.16), (0.30, -0.30, -12, 0.26, 0.16)):
        sp = lathe([(0, 0.0), (r, 0.05), (r * 0.82, L * 0.5), (0, L)], segs=5, phase=x * 3)
        obs.add(sp, T(x, hy + hh / 2 - 0.08, z) @ R("Z", ang) @ R("X", 40 * z))
    # shaft with a rocky collar and glowing bands
    obs.add(lathe([(0, 0.38), (0.17, 0.38), (0.175, 1.8), (0.17, hy - 0.6), (0, hy - 0.6)], segs=12))
    obs.add(rock(0.30, seed=5, jitter=0.12, subdiv=1, scale=(1.3, 0.75, 1.1)), T(0, hy - 0.80, 0))
    for y0 in (hy - 1.20, hy - 1.42):
        lava.add(band(0.17, y0 - 0.05, y0 + 0.05, 0.195, segs=12))
    lava.add(band(0.17, 0.36, 0.48, 0.20, segs=12))
    grip.add(wrapped_grip(-1.0, 0.38, 0.17, 0.18, pitch=0.22, amp=0.022, around=12))
    obs.add(lathe([(0, -1.06), (0.17, -1.06), (0.20, -1.02), (0.18, -0.97), (0, -0.97)], segs=8))
    core.add(sphere(0.17, 14, 10), T(0, -1.21, 0))
    for k in range(3):
        a = math.radians(90 + 120 * k)
        ca, sa = math.cos(a), math.sin(a)
        path = [Vector((r * ca, y, r * sa)) for r, y in ((0.12, -1.04), (0.21, -1.14), (0.20, -1.30), (0.11, -1.40))]
        obs.add(sweep(path, [0.11, 0.095, 0.07, 0.0], [0.09, 0.08, 0.055, 0.0], sides=5))
    w.fx = (0, hy, 0)


@weapon("IceMallet", "Epic", "Hammer")
def ice_mallet(w):
    """A block of clear blue ice with a glowing snowflake frozen inside, a puffy
    snow cap on top, icicles hanging underneath, a frosty blue shaft with snowy
    rings, a white grip and an ice-crystal pommel."""
    ice = w.part("Ice", (178, 228, 255), "Glass", transparency=0.35, smooth=12)
    core = w.part("Core", (226, 250, 255), "Neon")
    snow = w.part("Snow", (250, 252, 255), "SmoothPlastic", smooth=60)
    blue = w.part("Shaft", (58, 142, 236), "Metal", smooth=40)
    grip = w.part("Grip", (238, 244, 252), "Fabric", smooth=70)
    hy = 2.24
    ice.add(bar_x([(-0.84, 0.84, 0.82, 0.12), (-0.68, 0.98, 0.96, 0.17), (-0.12, 0.94, 0.94, 0.15),
                   (0.40, 1.0, 0.97, 0.17), (0.70, 0.97, 0.95, 0.16), (0.84, 0.82, 0.80, 0.12)], y=hy))
    core.add(snowflake(0.34, 0.07, arm_w=0.075, bevel=0.0, branches=1), T(0, hy, 0))
    top = hy + 0.49
    for x, z, r, sy in ((-0.56, 0.06, 0.26, 0.50), (-0.20, -0.10, 0.30, 0.55), (0.18, 0.08, 0.29, 0.55),
                        (0.54, -0.04, 0.25, 0.50), (0.0, 0.22, 0.20, 0.45), (-0.36, 0.24, 0.18, 0.45),
                        (0.36, -0.26, 0.18, 0.45)):
        snow.add(sphere(r, 10, 6, scale=(1.25, sy, 1.15)), T(x, top - 0.02, z))
    bot = hy - 0.47
    for x, z, L, r in ((-0.66, 0.22, 0.42, 0.10), (-0.44, -0.20, 0.56, 0.12), (-0.22, 0.24, 0.34, 0.09),
                       (0.24, -0.22, 0.46, 0.11), (0.46, 0.22, 0.58, 0.12), (0.68, -0.18, 0.36, 0.09)):
        ice.add(lathe([(0, -L), (r * 0.8, -L * 0.35), (r, -0.02), (0, 0.04)], segs=6, phase=0.3), T(x, bot, z))
    blue.add(lathe([(0, 0.38), (0.12, 0.38), (0.125, 1.2), (0.12, hy - 0.4), (0, hy - 0.4)], segs=14))
    snow.add(band(0.12, hy - 0.64, hy - 0.46, 0.165, segs=14))
    snow.add(band(0.12, 1.30, 1.40, 0.15, segs=14))
    grip.add(wrapped_grip(-0.72, 0.40, 0.145, 0.155, pitch=0.21, amp=0.02, around=12))
    blue.add(band(0.14, 0.36, 0.48, 0.17, segs=14))
    blue.add(lathe([(0, -0.74), (0.15, -0.74), (0.165, -0.70), (0.15, -0.66), (0, -0.66)], segs=12))
    ice.add(lathe([(0, -0.98), (0.12, -0.86), (0.13, -0.78), (0.09, -0.72), (0, -0.72)], segs=6))
    w.fx = (0, hy, 0)


@weapon("CrystalMaul", "Epic", "Hammer")
def crystal_maul(w):
    """A cluster of big violet crystals bursting from a glowing magenta heart gem
    held in a dark iron cradle, with glowing cores in the three big points, a dark
    purple shaft with iron rings, a purple grip and a crystal pommel."""
    crystal = w.part("Crystals", (172, 116, 255), "Glass", transparency=0.3, smooth=5)
    heart = w.part("Heart", (240, 136, 255), "Neon")
    iron = w.part("Cradle", (78, 82, 104), "Metal", smooth=30)
    shaft = w.part("Shaft", (56, 34, 92), "Metal", smooth=40)
    grip = w.part("Grip", (38, 22, 64), "Fabric", smooth=70)
    cy = 3.86

    def prism(L, r):
        return lathe([(0, 0.0), (r * 0.85, 0.0), (r, 0.10), (r * 0.96, L * 0.58), (0, L)], segs=6, phase=math.pi / 6)
    # (angle from +Y toward +X, tilt toward +Z, length, radius)
    spec = [(0, 0, 1.40, 0.38), (-72, 0, 1.18, 0.36), (72, 0, 1.18, 0.36), (-36, 16, 1.0, 0.30),
            (36, -16, 1.0, 0.30), (-14, -40, 0.84, 0.26), (16, 40, 0.84, 0.26), (-118, 24, 0.62, 0.22),
            (118, -24, 0.62, 0.22), (-56, -32, 0.78, 0.24), (56, 32, 0.78, 0.24)]
    for ang, tilt, L, r in spec:
        m = T(0, cy, 0) @ R("X", tilt) @ R("Z", -ang) @ T(0, 0.26, 0)
        crystal.add(prism(L, r), m)
        if L > 1.1:
            heart.add(lathe([(0, 0.10), (0.09, 0.18), (0.09, L * 0.55), (0, L * 0.80)], segs=6), m)
    heart.add(ico(0.38, subdiv=1, scale=(1.0, 1.08, 1.0)), T(0, cy, 0))
    # iron cradle with four claws
    iron.add(lathe([(0, cy - 0.62), (0.22, cy - 0.62), (0.36, cy - 0.48), (0.46, cy - 0.28), (0.48, cy - 0.18),
                    (0.42, cy - 0.16), (0.32, cy - 0.30), (0, cy - 0.34)], segs=8, phase=math.pi / 8))
    for k in range(4):
        a = math.radians(45 + 90 * k)
        ca, sa = math.cos(a), math.sin(a)
        path = [Vector((r * ca, y, r * sa)) for r, y in ((0.40, cy - 0.24), (0.50, cy - 0.04), (0.44, cy + 0.20),
                                                         (0.30, cy + 0.34))]
        iron.add(sweep(path, [0.12, 0.10, 0.08, 0.0], [0.10, 0.09, 0.07, 0.0], sides=5))
    shaft.add(lathe([(0, 0.30), (0.15, 0.30), (0.155, 1.6), (0.15, cy - 0.55), (0, cy - 0.55)], segs=14))
    for y0 in (1.70, 2.70):
        iron.add(band(0.15, y0 - 0.06, y0 + 0.06, 0.175, segs=14))
    iron.add(band(0.15, 0.26, 0.42, 0.185, segs=14))
    grip.add(wrapped_grip(-1.0, 0.30, 0.17, 0.18, pitch=0.22, amp=0.022, around=12))
    iron.add(lathe([(0, -1.04), (0.17, -1.04), (0.20, -1.0), (0.18, -0.96), (0, -0.96)], segs=8))
    crystal.add(lathe([(0, -1.22), (0.13, -1.12), (0.14, -1.05), (0, -1.0)], segs=6))
    w.fx = (0, cy, 0)


# ================================================================ HAMMERS: legendary

@weapon("StarHammer", "Legendary", "Hammer")
def star_hammer(w):
    """The Star Hammer: a huge chunky faceted gold star with a glowing star set into
    each face, held in a gold cup on a royal-blue shaft with gold rings, a white
    grip, a star pommel, and little stars and sparkles orbiting the head on a
    glowing ring."""
    gold = w.part("Star", (255, 200, 48), "Metal", smooth=20)
    glow = w.part("Glow", (255, 242, 150), "Neon")
    blue = w.part("Shaft", (44, 92, 220), "Metal", smooth=40)
    grip = w.part("Grip", (246, 246, 250), "Fabric", smooth=70)
    sy = 4.40
    ro, ri = 1.60, 0.70
    gold.add(star3d(ro, ri, 0.17, 0.50), T(0, sy, 0))
    glow.add(star3d(ro * 0.56, ri * 0.56, 0.34, 0.57), T(0, sy, 0))
    gold.add(lathe([(0, 3.28), (0.17, 3.28), (0.20, 3.36), (0.30, 3.62), (0.36, 3.80), (0.32, 3.82), (0.22, 3.70),
                    (0, 3.66)], segs=16))
    # orbit ring with little stars and sparkles riding on it
    ring_m = T(0, sy, 0) @ R("Z", 18) @ R("X", 24)
    glow.add(torus(1.95, 0.045, segs=48, rsegs=5), ring_m)
    for ang, sc in ((20, 0.30), (150, 0.24), (250, 0.27)):
        a = math.radians(ang)
        p = ring_m @ Vector((1.95 * math.cos(a), 0, 1.95 * math.sin(a)))
        gold.add(star3d(sc, sc * 0.44, sc * 0.22, sc * 0.5), T(*p) @ R("Z", ang * 0.5))
    sparkle = slab(star_pts(4, 0.17, 0.05, rot=90), 0.06, 0.0)
    for x, y, z in ((-1.10, sy + 1.25, 0.15), (1.25, sy + 1.32, -0.10), (-1.50, sy - 1.10, -0.12),
                    (1.55, sy - 0.85, 0.12)):
        glow.add(sparkle, T(x, y, z))
    blue.add(lathe([(0, 0.36), (0.16, 0.36), (0.165, 1.8), (0.16, 3.40), (0, 3.40)], segs=16))
    for y0 in (1.55, 2.45):
        gold.add(band(0.16, y0 - 0.07, y0 + 0.07, 0.19))
    gold.add(band(0.16, 0.34, 0.48, 0.195))
    grip.add(wrapped_grip(-0.98, 0.38, 0.16, 0.17, pitch=0.22, amp=0.022, around=12))
    gold.add(band(0.16, -1.02, -0.92, 0.19))
    gold.add(star3d(0.30, 0.13, 0.08, 0.16), T(0, -1.10, 0))
    w.fx = (0, sy, 0)


# ================================================================ HAMMERS: limited (Halloween)

def pumpkin_profile(R0, H0, n=12):
    """Outer profile [(r, y)] of a squat round pumpkin (centred on 0) with sunken poles."""
    prof = []
    for i in range(n + 1):
        t = math.radians(-90 + 180 * i / n)
        c, sn = max(math.cos(t), 0.0), math.sin(t)
        r = R0 * c ** 0.62
        y = 0.5 * H0 * sn - math.copysign(0.10 * H0 * max(0.0, 1 - r / (0.3 * R0)) ** 2, sn)
        prof.append((r, y))
    return prof


def pumpkin_body(R0, H0, lobes=8, depth=0.11, segs=48, cy=0.0):
    rm = lambda a: 1 - depth * (0.5 - 0.5 * math.cos(lobes * a)) ** 0.6
    return lathe([(r, y + cy) for r, y in pumpkin_profile(R0, H0)], segs=segs, rmod=rm)


def pumpkin_zsurf(R0, H0, lobes, depth):
    """Height of a pumpkin_body surface on its +Z side at (x, y) (centred on 0)."""
    prof = [(y, r) for r, y in pumpkin_profile(R0, H0)[1:-1]]

    def rp(y):
        if y <= prof[0][0]:
            return prof[0][1]
        for (ya, ra), (yb, rb) in zip(prof, prof[1:]):
            if y <= yb:
                return lerp(ra, rb, (y - ya) / (yb - ya))
        return prof[-1][1]

    def zs(x, y):
        r0 = rp(y)
        z = math.sqrt(max(r0 * r0 - x * x, 1e-6))
        for _ in range(6):
            k = 1 - depth * (0.5 - 0.5 * math.cos(lobes * math.atan2(z, x))) ** 0.6
            z = math.sqrt(max((r0 * k) ** 2 - x * x, 1e-6))
        return z
    return zs


@weapon("PumpkinSmasher", "Limited", "Hammer")
def pumpkin_smasher(w):
    """A jack-o'-lantern on a stick: a big ribbed pumpkin with a face carved into
    each side and glowing from inside (a toothy grin, and a happy face on the back),
    a curly green stem with a leaf and tendril, a wooden shaft, a purple-wrapped
    grip and a mini pumpkin pommel."""
    orange = w.part("Pumpkin", (255, 132, 26), "SmoothPlastic", smooth=40)
    glow = w.part("Face", (255, 214, 58), "Neon")
    green = w.part("Stem", (78, 176, 52), "SmoothPlastic", smooth=45)
    wood = w.part("Shaft", (110, 70, 36), "Wood", smooth=40)
    grip = w.part("Grip", (124, 52, 190), "Fabric", smooth=70)
    cy, R0, H0 = 2.56, 1.0, 1.52
    zs = pumpkin_zsurf(R0, H0, 8, 0.11)
    depth = 0.10

    def ytop(x):
        return -0.10 - 0.14 * (1 - (x / 0.56) ** 2)
    grin = [(-0.56, -0.10), (-0.48, -0.26), (-0.34, -0.38), (-0.16, -0.44), (-0.07, -0.45), (-0.07, -0.32),
            (0.07, -0.32), (0.07, -0.45), (0.16, -0.44), (0.34, -0.38), (0.48, -0.26), (0.56, -0.10),
            (0.42, ytop(0.42)), (0.28, ytop(0.28)), (0.28, -0.34), (0.14, -0.34), (0.14, ytop(0.14)),
            (0.0, ytop(0.0)), (-0.14, ytop(-0.14)), (-0.14, -0.34), (-0.28, -0.34), (-0.28, ytop(-0.28)),
            (-0.42, ytop(-0.42))]
    front = [[(-0.48, 0.10), (-0.12, 0.05), (-0.27, 0.37)], [(0.48, 0.10), (0.27, 0.37), (0.12, 0.05)],
             [(-0.08, -0.08), (0.08, -0.08), (0.0, 0.05)], grin]
    smile = [(0.36 * math.cos(math.radians(a)), -0.12 + 0.30 * math.sin(math.radians(a))) for a in range(180, 361, 15)]
    back = [circle_pts(0.115, n=14, cx=-0.27, cy=0.17), circle_pts(0.115, n=14, cx=0.27, cy=0.17), smile]
    cutters, fills = bmesh_new(), bmesh_new()
    for shapes, m in ((front, S(1, 1, 1)), (back, S(1, 1, -1))):
        for pts in shapes:
            pts = densify(pts, 0.08)
            merge_into(cutters, projected_slab(pts, lambda x, y: 2.0, lambda x, y: zs(x, y) - depth, spacing=0.09), m)
            merge_into(fills, projected_slab(pts, lambda x, y: zs(x, y) - depth + 0.008,
                                             lambda x, y: zs(x, y) - depth - 0.07, spacing=0.09), m)
    body = boolean(pumpkin_body(R0, H0, lobes=8, depth=0.11, segs=48), cutters)
    orange.add(body, T(0, cy, 0))
    glow.add(fills, T(0, cy, 0))
    # curly stem, a leaf and a tendril
    ty = cy + H0 * 0.40
    stem = [Vector((x, ty + y, z)) for x, y, z in ((0, -0.08, 0), (0.02, 0.14, 0), (0.08, 0.30, 0.0), (0.18, 0.40, 0.02),
                                                   (0.28, 0.42, 0.04))]
    green.add(sweep(stem, [0.27, 0.22, 0.19, 0.17, 0.16], [0.27, 0.22, 0.19, 0.17, 0.16], sides=7, point_end=False))
    green.add(slab(pumpkin_leaf(0.40), 0.06, 0.02, seg=1), T(-0.12, ty + 0.03, 0.10) @ aim((-0.55, 0.12, 0.80)))
    curl = []
    for i in range(22):
        t = i / 21 * 2.4 * math.pi
        r = 0.15 * (1 - t / (3.2 * math.pi))
        curl.append(Vector((-0.22 + r * math.cos(t), ty + 0.04 + 0.10 * i / 21, -0.22 + r * math.sin(t))))
    green.add(sweep(curl, [0.045] * 22, [0.045] * 22, sides=5, point_end=False))
    wood.add(lathe([(0, 0.38), (0.13, 0.38), (0.135, 1.2), (0.13, cy - 0.6), (0, cy - 0.6)], segs=14))
    grip.add(wrapped_grip(-0.70, 0.40, 0.145, 0.155, pitch=0.21, amp=0.02, around=12))
    orange.add(pumpkin_body(0.17, 0.26, lobes=8, depth=0.10, segs=16, cy=-0.80))
    w.fx = (0, cy, 0)


def bmesh_new():
    import bmesh as _bm
    return _bm.new()


@weapon("CauldronMaul", "Limited", "Hammer")
def cauldron_maul(w):
    """A witch's cauldron on a stick: a round black iron pot on stubby feet with a
    thick purple rim and ring handles, bubbling glowing green brew with bubbles
    floating up, slime dripping down the sides, a wooden shaft and a purple grip."""
    iron = w.part("Pot", (42, 42, 54), "Metal", smooth=35)
    brew = w.part("Brew", (112, 255, 64), "Neon")
    purple = w.part("Rim", (142, 58, 222), "Metal", smooth=35)
    wood = w.part("Shaft", (86, 56, 32), "Wood", smooth=40)
    grip = w.part("Grip", (122, 46, 196), "Fabric", smooth=70)
    by = 3.02
    iron.add(lathe([(0, by), (0.42, by), (0.70, by + 0.10), (0.90, by + 0.32), (1.0, by + 0.64), (0.97, by + 0.94),
                    (0.88, by + 1.14), (0.82, by + 1.24), (0.80, by + 1.30), (0.70, by + 1.30), (0.68, by + 1.20),
                    (0, by + 1.20)], segs=24))
    purple.add(torus(0.88, 0.12, segs=24, rsegs=6), T(0, by + 1.30, 0))
    brew.add(lathe([(0, by + 1.20), (0.80, by + 1.20), (0.80, by + 1.32), (0.50, by + 1.36), (0, by + 1.38)], segs=24))
    for x, y, z, r in ((0.30, 1.36, 0.20, 0.16), (-0.32, 1.35, -0.12, 0.13), (0.05, 1.38, -0.38, 0.11),
                       (-0.12, 1.37, 0.40, 0.10), (0.20, 1.68, 0.10, 0.09), (-0.10, 1.80, -0.06, 0.06)):
        brew.add(sphere(r, 8, 5), T(x, by + y, z))
    # slime drips over the rim and down the belly
    prof = [(by + 0.64, 1.0), (by + 0.94, 0.97), (by + 1.14, 0.88), (by + 1.24, 0.82)]

    def pot_r(y):
        for (ya, ra), (yb, rb) in zip(prof, prof[1:]):
            if y <= yb:
                return lerp(ra, rb, (y - ya) / (yb - ya))
        return prof[-1][1]
    for ang, L in ((90, 0.56), (48, 0.34), (132, 0.44), (220, 0.32), (320, 0.48)):
        a = math.radians(ang)
        rd = Vector((math.cos(a), 0, math.sin(a)))
        pts = [(0.88, by + 1.44), (1.005, by + 1.34), (1.02, by + 1.24)]
        for k in range(1, 4):
            y = by + 1.20 - L * k / 3
            pts.append((pot_r(y) + 0.035, y))
        path = [Vector((rd.x * r, y, rd.z * r)) for r, y in pts]
        brew.add(sweep(path, [0.16, 0.15, 0.13, 0.11, 0.10, 0.10], [0.07, 0.07, 0.06, 0.06, 0.06, 0.06], sides=6,
                       point_end=False, up=rd))
        r_end, y_end = pts[-1]
        brew.add(sphere(0.07, 6, 4, scale=(1.0, 1.15, 0.8)), T(rd.x * (r_end + 0.01), y_end - 0.02, rd.z * (r_end + 0.01))
                 @ aim((0, 1, 0), up=tuple(rd)))
    for k in range(3):
        a = math.radians(90 + 120 * k)
        iron.add(lathe([(0, 0.0), (0.10, 0.0), (0.13, 0.10), (0.11, 0.20), (0, 0.22)], segs=6),
                 T(0.52 * math.cos(a), by - 0.10, 0.52 * math.sin(a)))
    for sx in (1, -1):
        iron.add(box(0.12, 0.14, 0.12), T(sx * 0.96, by + 1.02, 0))
        purple.add(torus(0.14, 0.04, segs=10, rsegs=4, axis="Z"), T(sx * 1.08, by + 0.90, 0))
    wood.add(lathe([(0, 0.30), (0.15, 0.30), (0.155, 1.6), (0.15, by + 0.10), (0, by + 0.10)], segs=14))
    purple.add(band(0.15, by - 0.40, by - 0.28, 0.18, segs=14))
    purple.add(band(0.15, 0.26, 0.40, 0.185, segs=14))
    grip.add(wrapped_grip(-1.0, 0.30, 0.17, 0.18, pitch=0.24, amp=0.022, around=10))
    purple.add(lathe([(0, -1.15), (0.10, -1.15), (0.19, -1.08), (0.20, -1.0), (0.17, -0.97), (0, -0.97)], segs=10))
    w.fx = (0, by + 1.36, 0)


@weapon("TombstoneHammer", "Limited", "Hammer")
def tombstone_hammer(w):
    """A cartoon tombstone on a stick: a round-topped grey headstone with RIP carved
    into both faces above two carved lines, a crack running from a chipped corner,
    slime-green moss creeping over the top and corners, a dark stone plinth with
    grass tufts, a wooden shaft and a purple grip."""
    stone = w.part("Stone", (152, 158, 176), "SmoothPlastic", smooth=30)
    dark = w.part("Carving", (70, 74, 92), "SmoothPlastic", smooth=30)
    moss = w.part("Moss", (112, 214, 72), "SmoothPlastic", smooth=50)
    wood = w.part("Shaft", (80, 52, 30), "Wood", smooth=40)
    grip = w.part("Grip", (112, 48, 172), "Fabric", smooth=70)
    sb, st, hw, ay = 3.20, 4.94, 0.86, 0.60
    ys = st - ay
    outline = [(-hw, sb), (hw, sb), (hw, ys)]
    chip = {20: 1.0, 27: 0.84, 33: 0.90, 39: 0.82, 46: 1.0}
    angles = sorted(set(list(range(12, 180, 12)) + list(chip)))
    angles = [a for a in angles if not (20 < a < 46 and a not in chip)]
    for a in angles:
        k = chip.get(a, 1.0)
        outline.append((hw * k * math.cos(math.radians(a)), ys + ay * k * math.sin(math.radians(a))))
    outline.append((-hw, ys))
    T_ = 0.56
    stone_bm = slab(outline, T_, 0.07, seg=1)
    # carving: RIP, two lines and a crack, cut into both faces with a dark floor
    face = T_ / 2
    cut_d = 0.05
    # (cutter, fill, position, back side turned round so it reads the right way)
    shapes = [(text_slab("RIP", 0.60, 0.30, res=2), drop_facing(text_slab("RIP", 0.60, 0.10, res=2), (0, 0, -1)),
               (0, 4.30), True)]
    for wl, y in ((0.84, 3.84), (0.58, 3.66)):
        r = rounded_rect_pts(wl, 0.07, 0.03, n=2)
        shapes.append((slab(r, 0.30, 0.0), slab(r, 0.10, 0.0), (0, y), True))
    crack_c = [(0.74, 4.66), (0.58, 4.48), (0.68, 4.32), (0.54, 4.14), (0.62, 3.98)]
    left = [(x - 0.022, y) for x, y in crack_c]
    right = [(x + 0.022, y) for x, y in reversed(crack_c)]
    crack = left + [(crack_c[-1][0], crack_c[-1][1] - 0.04)] + right
    shapes.append((slab(crack, 0.30, 0.0), slab(crack, 0.10, 0.0), (0, 0), False))
    cutters, fills = bmesh_new(), bmesh_new()
    for cutter, fill, (x, y), turn in shapes:
        for side_m in (Matrix_I(), R("Y", 180) if turn else S(1, 1, -1)):
            merge_into(cutters, cutter, side_m @ T(x, y, face - cut_d + 0.15))
            merge_into(fills, fill, side_m @ T(x, y, face - cut_d + 0.006 - 0.05))
    stone.add(boolean(stone_bm, cutters))
    dark.add(fills)
    dark.add(bar_y([(sb - 0.30, 1.96, 0.76, 0.06), (sb + 0.04, 1.86, 0.70, 0.06)]))
    # moss over the top-left of the arch, the corners and a few spots
    for a, r in ((168, 0.13), (150, 0.17), (128, 0.18), (106, 0.13)):
        x, y = hw * 0.97 * math.cos(math.radians(a)), ys + ay * 0.97 * math.sin(math.radians(a))
        moss.add(sphere(r, 8, 5, scale=(1.25, 0.85, 1.85)), T(x, y, 0))
    for x, y, r in ((-0.80, sb + 0.10, 0.14), (0.80, sb + 0.06, 0.11), (-0.84, sb + 0.30, 0.09)):
        moss.add(sphere(r, 8, 5, scale=(1.0, 1.0, 2.2)), T(x, y, 0))
    for x in (-0.86, 0.86):
        for dz, ang, L in ((0.22, -18, 0.20), (0.26, 8, 0.26), (-0.22, 16, 0.18), (-0.26, -10, 0.24)):
            blade_ = lathe([(0, 0.0), (0.035, 0.0), (0, L)], segs=4)
            moss.add(blade_, T(x, sb + 0.02, dz) @ R("Z", ang if x < 0 else -ang))
    wood.add(lathe([(0, 0.30), (0.15, 0.30), (0.155, 1.6), (0.15, sb - 0.2), (0, sb - 0.2)], segs=14))
    grip.add(wrapped_grip(-1.0, 0.30, 0.17, 0.18, pitch=0.24, amp=0.022, around=10))
    dark.add(band(0.15, 0.26, 0.40, 0.185, segs=14))
    stone.add(sphere(0.17, 12, 8), T(0, -1.0, 0))
    w.fx = (0, 4.10, 0)


def Matrix_I():
    from mathutils import Matrix
    return Matrix.Identity(4)


# ================================================================ MYTHICS (new: two per class)

def bend_x(bm, fn):
    """Shift every vertex along X by fn(y): bends a straight blade (and anything
    laid on its faces) the same way."""
    for v in bm.verts:
        v.co.x += fn(v.co.y)
    return bm


def clip_halfplane(points, nx, ny, d):
    """The part of a closed outline where nx * x + ny * y >= d."""
    out = []
    n = len(points)
    for i in range(n):
        (ax, ay), (bx, by) = points[i], points[(i + 1) % n]
        fa, fb = nx * ax + ny * ay - d, nx * bx + ny * by - d
        if fa >= 0:
            out.append((ax, ay))
        if (fa >= 0) != (fb >= 0):
            t = fa / (fa - fb)
            out.append((ax + (bx - ax) * t, ay + (by - ay) * t))
    return out


def offset_outline(points, d):
    """Grow a closed outline outward by d (mitred corners, capped so spikes stay sane)."""
    n = len(points)
    area = sum(points[i][0] * points[(i + 1) % n][1] - points[(i + 1) % n][0] * points[i][1] for i in range(n))
    sgn = 1.0 if area > 0 else -1.0
    out = []
    for i in range(n):
        (ax, ay), (bx, by), (cx, cy) = points[i - 1], points[i], points[(i + 1) % n]
        n1 = Vector((by - ay, -(bx - ax))) * sgn
        n2 = Vector((cy - by, -(cx - bx))) * sgn
        n1 = n1.normalized() if n1.length > 1e-9 else n2.normalized()
        n2 = n2.normalized() if n2.length > 1e-9 else n1
        m = (n1 + n2)
        m = m.normalized() if m.length > 1e-9 else n1
        k = d / max(m.dot(n1), 0.35)
        out.append((bx + m.x * k, by + m.y * k))
    return out


def flame_pts(s=1.0):
    """A cartoon flame / ember outline pointing +Y, about 0.7 x 1.1 at s=1."""
    pts = [(0.0, -0.45), (0.30, -0.32), (0.37, -0.02), (0.22, 0.30), (0.04, 0.66), (-0.10, 0.34), (-0.30, 0.06),
           (-0.34, -0.26)]
    return [(x * s, y * s) for x, y in catmull(pts, samples=2, closed=True)]


def heart_pts(s=1.0, n=14):
    """Heart outline (point down), about s wide, centred on the origin."""
    pts = []
    for i in range(n * 2):
        t = math.tau * i / (n * 2)
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((x / 32 * s, (y + 2.5) / 32 * s))
    return pts


def station_at(stations, y):
    """Interpolated (half_width, half_thick, bevel) of profile_blade stations at y."""
    if y <= stations[0][0]:
        return stations[0][1:]
    for a, b in zip(stations, stations[1:]):
        if y <= b[0]:
            t = (y - a[0]) / (b[0] - a[0])
            return tuple(lerp(a[i], b[i], t) for i in range(1, 4))
    return stations[-1][1:]


def surface_hits(target, center, dirs, lift=0.0):
    """Cast rays from far outside toward `center` along each direction; return the
    points where they hit `target` (a bmesh), lifted off the surface by `lift`."""
    from mathutils.bvhtree import BVHTree
    tree = BVHTree.FromBMesh(target)
    out = []
    for d in dirs:
        d = Vector(d).normalized()
        loc, nrm, _i, _dist = tree.ray_cast(center + d * 10.0, -d)
        out.append((loc + nrm * lift, nrm) if loc is not None else (center + d, d))
    return out


def sph(az, el):
    """Unit direction from an azimuth (degrees, in XZ from +X toward +Z) and an elevation."""
    a, e = math.radians(az), math.radians(el)
    return Vector((math.cos(e) * math.cos(a), math.sin(e), math.cos(e) * math.sin(a)))


@weapon("PhoenixBlade", "Mythic", "Sword")
def phoenix_blade(w):
    """Mythic. A blade shaped like a giant phoenix feather: a crimson vane with
    blazing edges, a glowing white-gold quill and gold barbs, huge phoenix wings with
    flaming tips as the guard around a glowing sun gem, a crimson grip, a tail of
    flame feathers at the pommel, and embers and loose feathers drifting around it."""
    red = w.part("Blade", (204, 32, 44), "Metal", smooth=14)
    flame = w.part("Flame", (255, 112, 20), "Neon")
    core = w.part("Core", (255, 226, 110), "Neon")
    gold = w.part("Gold", (255, 194, 60), "Metal", smooth=30)
    grip = w.part("Grip", (112, 24, 34), "Fabric", smooth=70)
    tip_y = 5.24
    st = [(0.80, 0.25, 0.125, 0.075), (1.30, 0.36, 0.12, 0.085), (1.86, 0.44, 0.118, 0.09), (1.98, 0.36, 0.118, 0.085),
          (2.10, 0.45, 0.115, 0.09), (2.80, 0.49, 0.112, 0.095), (3.28, 0.47, 0.108, 0.09), (3.40, 0.39, 0.106, 0.085),
          (3.52, 0.46, 0.104, 0.09), (4.10, 0.40, 0.10, 0.085), (4.46, 0.31, 0.09, 0.075)]

    def curve(y):
        return -0.14 * smooth01((y - 2.6) / (tip_y - 2.6)) ** 1.6
    b = profile_blade(st, tip_y, n_point=7, point_curve=0.35)
    parts = split_by_tag(b, {0: "body", -1: "body", 1: "edge"})
    red.add(bend_x(parts["body"], curve))
    flame.add(bend_x(parts["edge"], curve))
    for side in (1, -1):
        core.add(bend_x(surface_vein([(0, 0.86), (0, 4.50)], 0.085, st, side=side, lift=0.006, thick=0.02, taper=True),
                        curve))
        for y0 in (1.12, 1.52, 2.30, 2.68, 3.70, 4.02):
            wy = station_at(st, y0)[0]
            for sx in (1, -1):
                barb = [(sx * 0.04, y0), (sx * wy * 0.45, y0 + 0.14), (sx * wy * 0.74, y0 + 0.30)]
                gold.add(bend_x(surface_vein(barb, 0.036, st, side=side, lift=0.004, thick=0.014), curve))

    def feather(L, W_, thick, m, tip_frac=0.56):
        out = leaf_pts(L, W_, n=7, tip_sharp=1.4)
        red.add(slab(out, thick, min(0.03, thick * 0.3), seg=0), m)
        tip = clip_halfplane(clip_halfplane(out, -0.9, 1.0, L * tip_frac), 0.9, 1.0, L * tip_frac)
        # grown a hair past the feather's own edge so the two walls never coincide (no flicker)
        flame.add(slab(offset_outline(tip, 0.006), thick + 0.024, 0.0), m)
    # phoenix wings
    for sx in (1, -1):
        for L, W_, ang, dz in ((1.46, 0.42, -30, 0.05), (1.30, 0.40, -46, -0.045), (1.12, 0.38, -62, 0.04),
                               (0.92, 0.34, -78, -0.035), (0.70, 0.30, -94, 0.0)):
            feather(L, W_, 0.10, S(sx, 1, 1) @ T(0.28, 0.66, dz) @ R("Z", ang))
    # gold guard with a glowing sun gem on both faces
    gold.add(bar_y([(0.50, 0.60, 0.32, 0.08), (0.86, 0.64, 0.34, 0.08)]))
    for side in (1, -1):
        gold.add(slab(star_pts(12, 0.34, 0.24, rot=90), 0.08, 0.02, seg=1), T(0, 0.70, side * 0.17))
        core.add(lathe([(0, 0.0), (0.17, 0.0), (0.17, 0.04), (0.11, 0.10), (0, 0.12)], segs=10),
                 T(0, 0.70, side * 0.20) @ R("X", side * 90))
    grip.add(wrapped_grip(-0.70, 0.50, 0.13, 0.145, pitch=0.21, amp=0.022, around=12, sz=0.9))
    gold.add(band(0.13, 0.46, 0.56, 0.16))
    gold.add(lathe([(0, -0.86), (0.12, -0.86), (0.17, -0.80), (0.17, -0.72), (0.14, -0.68), (0, -0.68)], segs=12))
    # a tail of flame feathers at the pommel
    for ang, L, W_ in ((180, 0.30, 0.20), (148, 0.30, 0.18), (212, 0.30, 0.18)):
        feather(L, W_, 0.07, T(0, -0.82, 0) @ R("Z", ang), tip_frac=0.45)
    # embers and loose feathers drifting around the blade
    for x, y, z, sc, rot, part in ((0.84, 1.55, 0.10, 0.20, -12, flame), (-0.90, 2.30, -0.08, 0.17, 10, core),
                                   (0.80, 3.20, -0.12, 0.15, -18, core), (-0.74, 3.95, 0.10, 0.14, 14, flame),
                                   (0.56, 4.62, 0.06, 0.11, -8, flame), (-0.98, 1.25, 0.05, 0.12, 8, flame)):
        part.add(slab(flame_pts(sc), 0.05, 0.0), T(x, y, z) @ R("Z", rot))
    for x, y, z, ang, L in ((1.12, 2.55, 0.15, -28, 0.52), (-1.18, 3.45, -0.12, 32, 0.46)):
        feather(L, L * 0.30, 0.05, T(x, y, z) @ R("Z", ang), tip_frac=0.5)
    w.fx = (round(curve(5.0), 3), 5.0, 0)


@weapon("StarfallBlade", "Mythic", "Sword")
def starfall_blade(w):
    """Mythic. A blade cut from the night sky: deep-space navy steel scattered with
    glowing stars, a shimmering cyan edge, a faceted gold north star at the guard
    with comet streaks for quillons, a navy grip bound in gold wire, a star pommel
    trailing a comet tail, and a tiny ringed planet and sparkles orbiting the blade."""
    navy = w.part("Blade", (30, 26, 84), "Metal", smooth=14)
    edge = w.part("Edge", (86, 224, 255), "Neon")
    stars = w.part("Stars", (255, 246, 196), "Neon")
    gold = w.part("Gold", (255, 200, 64), "Metal", smooth=20)
    grip = w.part("Grip", (26, 30, 86), "Fabric", smooth=70)
    planet = w.part("Planet", (168, 104, 255), "SmoothPlastic", smooth=40)
    st = [(0.84, 0.43, 0.14, 0.10), (2.6, 0.47, 0.135, 0.11), (4.18, 0.41, 0.12, 0.10)]
    b = profile_blade(st, 5.26, n_point=7, point_curve=0.3)
    parts = split_by_tag(b, {0: "body", -1: "body", 1: "edge"})
    navy.add(parts["body"])
    edge.add(parts["edge"])
    # stars scattered over both faces, hugging the ridged faces
    import random
    rng = random.Random(11)
    for side in (1, -1):
        placed = []
        tries = 0
        while len(placed) < 15 and tries < 400:
            tries += 1
            y = rng.uniform(1.0, 4.35)
            hw, _h, e = station_at(st, y)
            lim = hw - e - 0.07
            r = rng.choice((0.05, 0.06, 0.07, 0.08, 0.10, 0.12))
            x = rng.uniform(-lim + r, lim - r)
            if any((x - px) ** 2 + (y - py) ** 2 < ((r + pr) * 1.6) ** 2 for px, py, pr in placed):
                continue
            placed.append((x, y, r))
            pts = star_pts(4, r, r * 0.34) if rng.random() < 0.6 else star_pts(5, r, r * 0.45)
            pts = [(x + px, y + py) for px, py in pts]
            star = projected_slab(pts, lambda u, v: blade_face_z(u, v, st) + 0.012,
                                  lambda u, v: blade_face_z(u, v, st) - 0.02, spacing=1.0)
            stars.add(drop_facing(star, (0, 0, -1), 0.5), S(1, 1, side))
    # guard: a faceted gold north star with comet-streak quillons
    gold.add(bar_y([(0.50, 0.40, 0.30, 0.07), (0.86, 0.46, 0.32, 0.07)]))
    gold.add(star3d(0.50, 0.17, 0.09, 0.26, n=4, rot=90), T(0, 0.70, 0))
    stars.add(star3d(0.26, 0.09, 0.20, 0.31, n=4, rot=90), T(0, 0.70, 0))
    for sx in (1, -1):
        path = [Vector((sx * x, y, 0)) for x, y in ((0.30, 0.70), (0.62, 0.74), (0.92, 0.82), (1.12, 0.92))]
        gold.add(sweep(path, [0.20, 0.16, 0.12, 0.08], [0.20, 0.16, 0.12, 0.08], sides=8, point_end=False))
        gold.add(star3d(0.20, 0.08, 0.05, 0.11), T(sx * 1.18, 0.95, 0) @ R("Z", -sx * 12))
        for dy, L, wd in ((0.13, 0.80, 0.07), (-0.11, 0.66, 0.06)):
            streak = [Vector((sx * x, y + dy, 0)) for x, y in ((0.36, 0.70), (0.62, 0.73), (0.90, 0.80),
                                                               (0.36 + L, 0.84))]
            edge.add(sweep(streak, [wd, wd * 0.9, wd * 0.6, 0.0], [wd, wd * 0.9, wd * 0.6, 0.0], sides=6))
    grip.add(lathe([(0, -0.68), (0.135, -0.68), (0.15, -0.10), (0.135, 0.52), (0, 0.52)], segs=16, sz=0.9))
    gold.add(helix_ribbon(-0.66, 0.50, 0.15, 0.135, 4.0, 0.035, 0.02, samples_per_turn=12))
    gold.add(band(0.13, 0.48, 0.58, 0.16))
    # star pommel with a comet tail
    gold.add(star3d(0.27, 0.11, 0.07, 0.14), T(0, -0.84, 0))
    tail = [Vector(p) for p in ((0.0, -0.86, 0), (-0.10, -0.98, 0), (-0.24, -1.05, 0), (-0.42, -1.06, 0))]
    edge.add(sweep(tail, [0.16, 0.12, 0.08, 0.0], [0.08, 0.07, 0.05, 0.0], sides=6))
    # a little ringed planet and sparkles orbiting the blade
    planet.add(sphere(0.20, 16, 10), T(0.88, 3.70, 0.12))
    gold.add(torus(0.34, 0.03, segs=28, rsegs=5), T(0.88, 3.70, 0.12) @ R("Z", 22) @ R("X", 16))
    sparkle = slab(star_pts(4, 1.0, 0.30, rot=90), 0.05, 0.0)
    for x, y, z, sc in ((-0.86, 2.10, -0.08, 0.16), (0.78, 1.60, 0.10, 0.13), (-0.72, 4.30, 0.06, 0.14),
                        (0.44, 4.95, -0.05, 0.11), (-0.94, 3.20, 0.0, 0.09)):
        stars.add(sparkle, T(x, y, z) @ S(sc, sc, 1))
    w.fx = (0, 5.0, 0)


@weapon("UnicornHorn", "Mythic", "Dagger")
def unicorn_horn(w):
    """Mythic. A spiralled pearl unicorn horn wound with a glowing pink stripe and
    tipped with a glowing cyan point, rising from a little gold crown with heart gems
    between white feathered wings; a lavender grip, a gold heart pommel and pastel
    sparkles floating around it."""
    pearl = w.part("Horn", (250, 242, 255), "SmoothPlastic", smooth=35)
    pink = w.part("Glow", (255, 118, 206), "Neon")
    cyan = w.part("Sparkle", (120, 236, 255), "Neon")
    gold = w.part("Gold", (255, 204, 70), "Metal", smooth=30)
    wings = w.part("Wings", (255, 255, 255), "SmoothPlastic", smooth=40)
    grip = w.part("Grip", (184, 148, 255), "Fabric", smooth=70)
    y0, y1, r0, turns = 0.56, 3.84, 0.36, 3.2
    N, segs = 26, 20
    rings = []
    for i in range(N + 1):
        t = i / N
        y = lerp(y0, y1, t)
        if i == N:
            rings.append([Vector((0, y1, 0))])
            break
        r = r0 * (1 - t) ** 0.9
        phi = math.tau * turns * t
        rings.append([Vector((r * (1 + 0.10 * math.cos(2 * (a - phi))) * math.cos(a), y,
                              r * (1 + 0.10 * math.cos(2 * (a - phi))) * math.sin(a)))
                      for a in (math.tau * j / segs for j in range(segs))])
    pearl.add(loft(rings, cap_start=True, cap_end=False))
    # glowing pink stripe wound down one groove
    path, widths = [], []
    for i in range(31):
        t = lerp(0.02, 0.84, i / 30)
        r = r0 * (1 - t) ** 0.9
        a = math.tau * turns * t + math.pi / 2
        rr = r * 0.90 + 0.012
        path.append(Vector((rr * math.cos(a), lerp(y0, y1, t), rr * math.sin(a))))
        widths.append(lerp(0.085, 0.03, t / 0.84))
    pink.add(sweep(path, widths, widths, sides=6, point_end=False))
    cyan.add(lathe([(0, 3.34), (0.085, 3.38), (0, 3.88)], segs=10))
    # gold crown (a solid ring) with heart gems
    gold.add(lathe([(0.26, 0.44), (0.38, 0.44), (0.395, 0.48), (0.385, 0.62), (0.35, 0.65), (0.26, 0.65)], segs=20))
    for k in range(8):
        a = math.tau * (k + 0.5) / 8
        gold.add(lathe([(0, 0.0), (0.06, 0.0), (0, 0.18)], segs=4), T(0.36 * math.cos(a), 0.63, 0.36 * math.sin(a)))
        gold.add(sphere(0.04, 6, 4), T(0.36 * math.cos(a), 0.82, 0.36 * math.sin(a)))
    for side in (1, -1):
        pink.add(slab(heart_pts(0.22, n=10), 0.05, 0.0), T(0, 0.54, side * 0.385))
    # white feathered wings
    for sx in (1, -1):
        # feather depths chosen so no feather face lies in the covert's face planes (z = +/-0.075)
        for L, W_, ang, dz in ((1.10, 0.34, -40, 0.05), (0.96, 0.32, -60, -0.02), (0.80, 0.29, -80, 0.01),
                               (0.60, 0.25, -100, -0.05)):
            wings.add(slab(leaf_pts(L, W_, n=6, tip_sharp=1.4), 0.08, 0.03, seg=0),
                      S(sx, 1, 1) @ T(0.28, 0.56, dz) @ R("Z", ang))
        wings.add(slab(leaf_pts(0.60, 0.46, n=6, tip_sharp=1.2), 0.15, 0.04, seg=1),
                  S(sx, 1, 1) @ T(0.24, 0.52, 0) @ R("Z", -62))
    grip.add(wrapped_grip(-0.66, 0.42, 0.13, 0.14, pitch=0.20, amp=0.02, around=12, sz=0.95))
    gold.add(band(0.13, 0.40, 0.48, 0.16))
    gold.add(band(0.13, -0.70, -0.62, 0.16))
    # gold heart pommel with a glowing heart
    gold.add(slab(heart_pts(0.38, n=10), 0.14, 0.04, seg=1), T(0, -0.82, 0))
    for side in (1, -1):
        pink.add(slab(heart_pts(0.20, n=10), 0.05, 0.0), T(0, -0.81, side * 0.07))
    sparkle = slab(star_pts(4, 1.0, 0.30, rot=90), 0.05, 0.0)
    for x, y, z, sc, part in ((0.76, 1.55, 0.08, 0.14, cyan), (-0.74, 2.15, -0.06, 0.13, pink),
                              (0.56, 2.90, -0.08, 0.11, pink), (-0.48, 3.45, 0.06, 0.10, cyan)):
        part.add(sparkle, T(x, y, z) @ S(sc, sc, 1))
    for x, y, z, sc in ((-0.72, 1.30, 0.10, 0.16), (0.52, 3.50, 0.0, 0.13)):
        pink.add(slab(heart_pts(sc, n=10), 0.05, 0.0), T(x, y, z) @ R("Z", 12 if x > 0 else -12))
    w.fx = (0, 3.75, 0)


@weapon("Moonfang", "Mythic", "Dagger")
def moonfang(w):
    """Mythic. A curved fang of pale moon-silver with a soft glowing moonlight edge
    and a violet glow down its spine, rising out of a crescent moon (with craters)
    that holds a glowing violet star; a midnight-blue grip bound in silver, a little
    crescent pommel, and tiny stars orbiting the blade."""
    silver = w.part("Blade", (214, 222, 242), "Metal", smooth=16)
    moonlight = w.part("Moonlight", (124, 200, 255), "Neon")
    violet = w.part("Gem", (178, 110, 255), "Neon")
    moon = w.part("Moon", (232, 236, 246), "SmoothPlastic", smooth=35)
    crater = w.part("Craters", (172, 180, 204), "SmoothPlastic", smooth=35)
    grip = w.part("Grip", (30, 36, 104), "Fabric", smooth=70)
    st = [(0.70, 0.34, 0.125, 0.085), (1.40, 0.37, 0.12, 0.09), (2.30, 0.31, 0.105, 0.085), (2.90, 0.23, 0.09, 0.075)]

    def curve(y):
        return -0.42 * smooth01((y - 0.7) / 3.16) ** 1.5
    b = profile_blade(st, 3.86, n_point=6, point_curve=0.35)
    parts = split_by_tag(b, {0: "body", -1: "body", 1: "edge"})
    silver.add(bend_x(parts["body"], curve))
    moonlight.add(bend_x(parts["edge"], curve))
    for side in (1, -1):
        violet.add(bend_x(surface_vein([(0, 0.80), (0, 2.95)], 0.07, st, side=side, lift=0.006, thick=0.018,
                                       taper=True), curve))
    # the crescent moon guard, horns up, with craters on both faces
    cy, k = 1.06, 1.14
    cres = [(-y * k, x * k) for x, y in crescent_pts(0.70, 0.58, 0.26, n=36)]
    moon.add(slab(cres, 0.32, 0.03, seg=2), T(0, cy, 0))
    for x, y, r in ((-0.44, 0.62, 0.065), (0.42, 0.62, 0.06), (-0.58, 0.88, 0.04), (0.595, 0.95, 0.035),
                    (0.30, 0.48, 0.04), (-0.30, 0.47, 0.04)):
        for side in (1, -1):
            crater.add(slab(circle_pts(r * k, n=12), 0.03, 0.0), T(x * k, cy + (y - 1.0) * k, side * 0.162))
    for side in (1, -1):
        violet.add(star3d(0.18, 0.07, 0.04, 0.09, n=4), T(0, cy + (0.50 - 1.0) * k, side * 0.16))
    silver.add(bar_y([(0.28, 0.36, 0.26, 0.05), (0.42, 0.40, 0.28, 0.05)]))
    grip.add(wrapped_grip(-0.66, 0.36, 0.13, 0.14, pitch=0.20, amp=0.02, around=12, sz=0.95))
    silver.add(band(0.13, -0.70, -0.62, 0.16))
    # little crescent pommel, horns down, with a violet star
    pom = [(y, -x) for x, y in crescent_pts(0.22, 0.17, 0.09, n=20)]
    silver.add(slab(pom, 0.12, 0.012, seg=1), T(0, -0.80, 0))
    for side in (1, -1):
        violet.add(slab(star_pts(4, 0.08, 0.03, rot=90), 0.03, 0.0), T(0, -0.80, side * 0.065))
    sparkle = slab(star_pts(4, 1.0, 0.30, rot=90), 0.05, 0.0)
    for x, y, z, sc, part in ((0.62, 1.75, 0.08, 0.13, violet), (-0.88, 2.40, -0.06, 0.12, moonlight),
                              (0.40, 2.95, -0.08, 0.10, violet), (-0.80, 3.55, 0.06, 0.11, violet),
                              (0.84, 1.30, 0.05, 0.09, moonlight)):
        part.add(sparkle, T(x, y, z) @ S(sc, sc, 1))
    w.fx = (round(curve(3.75), 3), 3.75, 0)


@weapon("MeteorSmash", "Mythic", "Hammer")
def meteor_smash(w):
    """Mythic. A blazing blue comet for a head: a cratered space rock split by
    glowing cracks, trailing a huge layered tail of blue-white star fire, gripped by
    gold claws on a dark steel shaft with glowing bands; a deep blue grip, a gold
    pommel cradling a glowing shard, and little meteorites orbiting the head."""
    rock_p = w.part("Rock", (46, 40, 74), "Metal", smooth=22)
    fire = w.part("Fire", (70, 206, 255), "Neon")
    core = w.part("Core", (226, 248, 255), "Neon")
    gold = w.part("Gold", (255, 196, 60), "Metal", smooth=30)
    steel = w.part("Shaft", (62, 66, 90), "Metal", smooth=35)
    grip = w.part("Grip", (36, 46, 116), "Fabric", smooth=70)
    hc = Vector((0.0, 5.30, 0))
    R0 = 0.92
    rk = rock(R0, seed=4, jitter=0.07, subdiv=2, scale=(1.0, 0.96, 0.92))
    xform(rk, T(*hc))
    # craters
    for az, el, rr in ((70, 20, 0.17), (110, 48, 0.12), (30, -28, 0.14), (250, 22, 0.16), (290, -30, 0.12),
                       (5, 30, 0.11)):
        (p, nrm), = surface_hits(rk, hc, [sph(az, el)])
        rock_p.add(torus(rr, rr * 0.28, segs=12, rsegs=4), T(*(p - nrm * 0.02)) @ aim(nrm, up=(0, 1, 0.01)))
    rock_p.add(rk)

    def crack(pts, wd):
        dirs = []
        for (a1, e1), (a2, e2) in zip(pts, pts[1:]):
            for k in range(3):
                t = k / 3
                dirs.append(sph(lerp(a1, a2, t), lerp(e1, e2, t)))
        dirs.append(sph(*pts[-1]))
        hits = surface_hits(rk, hc, dirs, lift=0.0)
        path = [p for p, _n in hits]
        n = len(path)
        ws = [wd * (1 - 0.6 * i / (n - 1)) for i in range(n)]
        return sweep(path, ws, ws, sides=4, point_end=False)
    for pts, wd in (([(40, 30), (60, 18), (78, 26), (95, 10), (112, 18), (130, 4), (150, 12)], 0.09),
                    ([(78, 26), (84, 45), (76, 62)], 0.07), ([(112, 18), (120, -8), (110, -30), (122, -48)], 0.07),
                    ([(220, 20), (245, 5), (262, 22), (285, 8), (305, 25), (325, 12)], 0.09),
                    ([(262, 22), (268, -10), (258, -35)], 0.07),
                    ([(-20, -30), (-5, -10), (8, -22), (15, 5), (5, 25), (-12, 40)], 0.08)):
        fire.add(crack(pts, wd))
    # the comet tail: flat layers of flame licks streaming back toward -X (a white-hot core inside the
    # blue fire), plus two layers fanned out in Z so it has volume from every side
    def comet(L, H, rise, waves, amp, x0=0.30, n=40):
        top, bot = [], []
        for i in range(n + 1):
            t = i / n
            x = lerp(x0, -L, t)
            h = H * (1 - t ** 1.25)
            yc = rise * t * t
            top.append((x, yc + h * (1 + amp * ((t * waves) % 1.0) ** 3)))
            bot.append((x, yc - h * (1 + amp * 0.7 * ((t * waves + 0.5) % 1.0) ** 3)))
        return top + list(reversed(bot[1:-1]))
    fire.add(slab(comet(2.35, 0.86, 0.55, 3.5, 0.55, n=32), 0.30, 0.0), T(*hc))
    core.add(slab(comet(1.75, 0.44, 0.42, 3.0, 0.45, n=28), 0.38, 0.0), T(*hc))
    for tilt in (32, -32):
        fire.add(slab(comet(1.95, 0.62, 0.45, 3.0, 0.50, n=28), 0.14, 0.0), T(*hc) @ R("X", tilt))
    # gold cup and claws
    cup_y = hc.y - R0 * 0.96
    gold.add(lathe([(0, cup_y - 0.26), (0.20, cup_y - 0.26), (0.30, cup_y - 0.12), (0.42, cup_y + 0.06),
                    (0.38, cup_y + 0.10), (0.26, cup_y), (0, cup_y - 0.02)], segs=12))
    for k in range(4):
        th = 45 + 90 * k
        hits = surface_hits(rk, hc, [sph(th, e) for e in (-72, -52, -32, -14, 0)], lift=0.03)
        path = [p for p, _n in hits]
        gold.add(sweep(path, [0.17, 0.15, 0.12, 0.08, 0.0], [0.13, 0.12, 0.10, 0.07, 0.0], sides=6))
    # shaft
    steel.add(lathe([(0, 0.38), (0.17, 0.38), (0.175, 1.8), (0.17, cup_y - 0.2), (0, cup_y - 0.2)], segs=14))
    for y0 in (cup_y - 0.55, cup_y - 0.80):
        fire.add(band(0.17, y0 - 0.05, y0 + 0.05, 0.195, segs=14))
    gold.add(band(0.17, 2.20, 2.34, 0.195, segs=14))
    gold.add(band(0.17, 0.34, 0.48, 0.20, segs=14))
    grip.add(wrapped_grip(-1.0, 0.38, 0.17, 0.18, pitch=0.22, amp=0.022, around=12))
    # pommel: gold claws cradling a glowing shard
    gold.add(lathe([(0, -1.08), (0.16, -1.08), (0.20, -1.03), (0.18, -0.98), (0, -0.98)], segs=10))
    core.add(ico(0.13, subdiv=1, scale=(1.0, 1.3, 1.0)), T(0, -1.18, 0))
    for k in range(3):
        a = math.radians(90 + 120 * k)
        ca, sa = math.cos(a), math.sin(a)
        path = [Vector((r * ca, y, r * sa)) for r, y in ((0.10, -1.05), (0.17, -1.13), (0.15, -1.24), (0.06, -1.31))]
        gold.add(sweep(path, [0.08, 0.07, 0.05, 0.0], [0.07, 0.06, 0.04, 0.0], sides=5))
    # little meteorites orbiting the head, each with a tiny fire trail
    for x, y, z, r, seed in ((1.28, 6.12, 0.22, 0.19, 7), (1.25, 4.48, -0.24, 0.16, 9), (-0.62, 6.28, -0.26, 0.15, 3)):
        rock_p.add(rock(r, seed=seed, jitter=0.08, subdiv=1), T(x, y, z))
        fire.add(slab(comet(r * 4.2, r * 0.95, r * 0.6, 2.0, 0.5, x0=0.0, n=16), r * 1.2, 0.0), T(x, y, z))
        core.add(slab(comet(r * 2.6, r * 0.5, r * 0.4, 2.0, 0.4, x0=0.0, n=12), r * 1.45, 0.0), T(x, y, z))
    w.fx = tuple(round(v, 3) for v in hc)


@weapon("KrakenAnchor", "Mythic", "Hammer")
def kraken_anchor(w):
    """Mythic. A great gold ship's anchor swung by its shank: curved arms ending in
    big spade flukes carved with glowing tridents, a glowing sea-eye on the crown,
    barnacles crusted on, and a purple kraken tentacle with glowing pink suckers
    coiling up the shank and over the crown; a rope-wrapped grip, the anchor stock
    and its ring for a pommel."""
    gold = w.part("Anchor", (232, 180, 64), "Metal", smooth=30)
    runes = w.part("Runes", (64, 255, 196), "Neon")
    tent = w.part("Tentacle", (126, 58, 186), "SmoothPlastic", smooth=50)
    suck = w.part("Suckers", (255, 116, 206), "Neon")
    shell = w.part("Barnacles", (240, 232, 214), "SmoothPlastic", smooth=35)
    rope = w.part("Grip", (196, 160, 108), "Fabric", smooth=70)
    yc = 6.05
    # shank and crown
    gold.add(lathe([(0, -0.86), (0.21, -0.86), (0.21, -0.70), (0.19, -0.62), (0.19, 0.5), (0.24, yc - 0.3),
                    (0.26, yc)], segs=8, phase=math.pi / 8))
    gold.add(lathe([(0, yc - 0.14), (0.36, yc - 0.02), (0.36, yc + 0.08), (0.24, yc + 0.22), (0, yc + 0.32)], segs=8,
                   phase=math.pi / 8))
    # arms curving down from the crown, and the flukes
    Ra = 1.55
    fluke = catmull([(0, 0.66), (0.26, 0.30), (0.38, 0.04), (0.20, -0.06), (0, 0.02), (-0.20, -0.06), (-0.38, 0.04),
                     (-0.26, 0.30)], samples=2, closed=True)
    for sx in (1, -1):
        angs = list(range(0, 71, 10))
        path = [Vector((sx * Ra * math.sin(math.radians(a)), yc - Ra * (1 - math.cos(math.radians(a))), 0))
                for a in angs]
        n = len(path)
        gold.add(sweep(path, [lerp(0.46, 0.32, i / (n - 1)) for i in range(n)],
                       [lerp(0.38, 0.27, i / (n - 1)) for i in range(n)], sides=8, point_end=False))
        a = math.radians(70)
        d = (sx * math.cos(a), -math.sin(a), 0)
        m = T(*path[-1]) @ aim(d, up=(0, 0, 1)) @ S(1.22, 1.22, 1.0)
        gold.add(slab(fluke, 0.24, 0.05, seg=1), m)
        for side in (1, -1):
            mm = m @ T(0, 0.26, side * 0.125)
            runes.add(slab(rounded_rect_pts(0.045, 0.30, 0.02, n=1), 0.03, 0.0), mm @ T(0, -0.02, 0))
            runes.add(slab(rounded_rect_pts(0.24, 0.045, 0.02, n=1), 0.03, 0.0), mm @ T(0, 0.08, 0))
            for px in (-0.10, 0.0, 0.10):
                runes.add(slab([(-0.025, 0.0), (0.025, 0.0), (0.0, 0.12)], 0.03, 0.0), mm @ T(px, 0.10, 0))
    # glowing sea-eye on both faces of the crown
    for side in (1, -1):
        runes.add(ring_slab(0.20, 0.12, 0.04, 0.0, n=16), T(0, yc + 0.05, side * 0.335))
        runes.add(sphere(0.06, 8, 5, scale=(1, 1, 0.5)), T(0, yc + 0.05, side * 0.335))
    # barnacles
    bar = lathe([(0.0, 0.0), (0.075, 0.0), (0.06, 0.06), (0.032, 0.07), (0.022, 0.035), (0, 0.035)], segs=6)
    for sx, ang, side, sc in ((-1, 28, 1, 1.2), (-1, 40, 1, 0.9), (-1, 34, -1, 1.0), (1, 52, 1, 1.1), (1, 60, -1, 0.9),
                              (1, 46, -1, 1.25)):
        a = math.radians(ang)
        p = Vector((sx * Ra * math.sin(a), yc - Ra * (1 - math.cos(a)), side * 0.15))
        shell.add(bar, T(*p) @ R("X", side * 90) @ S(sc * 1.5))
    shell.add(bar, T(-0.20, yc + 0.20, 0.20) @ R("X", 60) @ S(1.4))
    # the kraken tentacle: coils up the shank, over the crown and curls in the air
    key = []
    for i in range(13):
        t = i / 12
        ang = math.radians(-330 + 720 * t)
        rad = 0.22 + lerp(0.17, 0.11, t)
        key.append((rad * math.cos(ang), lerp(1.20, 5.10, t), rad * math.sin(ang)))
    key += [(0.30, 5.55, 0.26), (0.58, 5.98, 0.30), (0.90, 6.20, 0.16), (1.12, 6.22, 0.0), (1.22, 6.04, -0.02),
            (1.10, 5.92, 0.0), (0.99, 6.02, 0.02)]
    path = [Vector(p) for p in catmull(key, samples=3)]
    n = len(path)
    radii = [lerp(0.19, 0.04, (i / (n - 1)) ** 1.2) for i in range(n)]
    tent.add(sweep(path, [r * 2 for r in radii], [r * 2 for r in radii], sides=7, point_end=False))
    tent.add(sphere(0.035, 6, 4), T(*path[-1]))
    for i in range(2, n - 3, 4):
        p = path[i]
        tan = (path[i + 1] - path[i - 1]).normalized()
        out = Vector((p.x, 0, p.z))
        out = out.normalized() if out.length > 1e-3 else Vector((0, 0, 1))
        if p.y > 5.3:
            out = Vector((0, 0, 1)) if i % 2 else Vector((0, 0, -1))
        out = (out - tan * out.dot(tan)).normalized()
        rs_ = radii[i] * 0.5
        suck.add(sphere(rs_, 6, 3, scale=(1.0, 0.35, 1.0)), T(*(p + out * radii[i] * 0.9)) @ aim(out, up=tuple(tan)))
    # rope grip, the stock and the ring
    rope.add(wrapped_grip(-0.70, 0.42, 0.215, 0.225, pitch=0.17, amp=0.03, around=12))
    gold.add(lathe_z([(0, -0.56), (0.07, -0.56), (0.085, -0.50), (0.075, -0.44), (0.065, 0.0), (0.075, 0.44),
                      (0.085, 0.50), (0.07, 0.56), (0, 0.56)], segs=10), T(0, -0.80, 0))
    for side in (1, -1):
        gold.add(sphere(0.09, 10, 6), T(0, -0.80, side * 0.60))
    gold.add(torus(0.24, 0.065, segs=24, rsegs=6, axis="Z"), T(0, -1.06, 0))
    w.fx = (0, yc, 0)
