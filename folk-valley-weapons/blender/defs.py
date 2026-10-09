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
                  capsule, loft, merge_into, snowflake)

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
}


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
    fit.add(bar_y([(0.50, 0.56, 0.23, 0.05), (0.66, 0.54, 0.21, 0.05), (0.80, 0.51, 0.18, 0.045)], x=0.03))
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
        path = [Vector((sx * x, y, 0)) for x, y in ((0.22, 0.58), (0.46, 0.64), (0.64, 0.80), (0.75, 1.04),
                                                    (0.79, 1.32))]
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
                        (-0.20, 0.86, 0.17, (1.1, 0.9, 0.62))):
        cloud.add(puff(r, sc, segs=12, rings=8), T(x, y, 0))
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
    hilt.add(bar_x([(-0.74, 0.20, 0.22), (0.74, 0.20, 0.22)], chamfer=0.055, y=0.56))
    for sx in (1, -1):
        hilt.add(sphere(0.145, 14, 9), T(sx * 0.80, 0.56, 0))
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
    gold.add(lathe([(0, 0.50), (0.14, 0.50), (0.40, 0.55), (0.50, 0.63), (0.53, 0.69), (0.48, 0.71),
                    (0.38, 0.63), (0.14, 0.58), (0, 0.58)], segs=36, sz=0.8, rmod=shell))
    # D-guard: a gold plate band wrapping round the knuckles from the shell to the pommel
    bow = [Vector(p) for p in ((0.42, 0.58, 0), (0.52, 0.30, 0), (0.54, -0.10, 0), (0.48, -0.46, 0),
                               (0.32, -0.74, 0), (0.12, -0.86, 0))]
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
        arm = [Vector((sx * x, y, 0)) for x, y in ((0.14, 0.72), (0.42, 0.88), (0.72, 1.10), (0.86, 1.22))]
        hilt.add(sweep(arm, [0.21, 0.19, 0.18, 0.17], [0.23, 0.21, 0.19, 0.18], sides=8, point_end=False))
        cx, cy = sx * 0.98, 1.34
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
        leaf = slab(leaf_pts(0.78, 0.36, n=7, tip_sharp=1.3), 0.08, 0.03, seg=1)
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
    blue.add(snowflake(0.66, 0.13, arm_w=0.12, bevel=0.0, branches=1), T(0, 0.58, 0))
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
        curl = [Vector((sx * (0.10 + 0.5 * t), 0.56 + 0.08 * t, 0)) for t in (0, 0.35, 0.7, 1.0)]
        for k in range(1, 9):
            a = math.radians(-90 + 45 * k)
            curl.append(Vector((sx * (0.60 + 0.14 * math.cos(a)), 0.78 + 0.14 * math.sin(a), 0)))
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
    handle = w.part("Handle", (246, 232, 204), "SmoothPlastic", smooth=50)
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
    butter.add(box(0.30, 0.26, 0.16, 0.06, 2), T(0.0, 2.45, 0.11) @ R("Z", 8))


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
    gold.add(bar_x([(-0.46, 0.13, 0.15), (0.46, 0.13, 0.15)], chamfer=0.035, y=0.40))
    for sx in (1, -1):
        gold.add(sphere(0.10, 12, 8), T(sx * 0.50, 0.40, 0))
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
    red.add(lathe([(0, -0.78), (0.20, -0.78), (0.26, -0.70), (0.27, -0.2), (0.25, 0.25), (0.20, 0.42), (0.10, 0.48),
                   (0, 0.48)], segs=32, rmod=flutes))
    for y in (-0.42, -0.06):
        black.add(lathe([(0.255, y), (0.285, y + 0.025), (0.285, y + 0.115), (0.255, y + 0.14)], segs=32, close=False))
    black.add(lathe([(0, -0.80), (0.21, -0.80), (0.23, -0.76), (0.21, -0.72), (0, -0.72)], segs=24))


@weapon("Fork", "Common", "Dagger")
def giant_fork(w):
    """Giant dinner fork: four rounded tines on a curved head, a slim neck and a
    flat handle that widens to a rounded end."""
    steel = w.part("Fork", (214, 220, 232), "Metal", smooth=35)
    head = catmull([(-0.06, 1.05), (-0.20, 1.35), (-0.30, 1.75), (-0.32, 2.25), (0.32, 2.25), (0.30, 1.75), (0.20, 1.35),
                    (0.06, 1.05)], samples=3, closed=False)
    steel.add(slab(head + [(0.06, 0.95), (-0.06, 0.95)], 0.12, 0.04, seg=1))
    for x in (-0.24, -0.08, 0.08, 0.24):
        tine = rounded_rect_pts(0.11, 1.30, 0.055, n=3)
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
    st = [(0.42, 0.14, 0.09, 0.0), (0.95, 0.36, 0.11, 0.0), (1.9, 0.30, 0.10, 0.0)]
    steel.add(profile_blade(st, 3.02, n_point=6, point_curve=0.5))
    wrap.add(wrapped_grip(-0.92, 0.42, 0.115, 0.125, pitch=0.16, amp=0.02, sz=0.95))
    steel.add(cylinder(0.08, 0.12, segs=10), T(0, -0.96, 0))
    steel.add(torus(0.21, 0.06, segs=22, rsegs=8, axis="Z"), T(0, -1.24, 0))
    # ribbon knotted through the ring with two fluttering tails
    ribbon.add(sphere(0.08, 10, 7, scale=(1.2, 1.0, 0.8)), T(0, -1.47, 0))
    for sx, L in ((1, 0.62), (-1, 0.50)):
        tail = [Vector((sx * 0.03, -1.50, 0)), Vector((sx * 0.14, -1.70, 0.05)), Vector((sx * 0.10, -1.90, -0.04)),
                Vector((sx * 0.20, -1.50 - L, 0.02))]
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
        path = [Vector((sx * x, y, 0)) for x, y in ((0.08, 0.46), (0.30, 0.50), (0.46, 0.66), (0.52, 0.95), (0.50, 1.30))]
        steel.add(sweep(path, [0.14, 0.13, 0.12, 0.10, 0.0], [0.14, 0.13, 0.12, 0.10, 0.0], sides=8))
    gold.add(lathe([(0, 0.30), (0.16, 0.30), (0.18, 0.34), (0.18, 0.46), (0.16, 0.50), (0, 0.50)], segs=16))
    wrap.add(wrapped_grip(-0.70, 0.32, 0.125, 0.135, pitch=0.18, amp=0.02, sz=1.0))
    gold.add(lathe([(0, -0.92), (0.10, -0.92), (0.17, -0.84), (0.18, -0.76), (0.15, -0.70), (0, -0.68)], segs=16))


@weapon("Carrot", "Uncommon", "Dagger")
def carrot(w):
    """A giant crunchy carrot held at its top: bumpy orange root with darker
    growth rings, and a bushy green leaf top sprouting out the bottom."""
    orange = w.part("Carrot", (255, 138, 30), "SmoothPlastic", smooth=45)
    rings = w.part("Rings", (226, 102, 16), "SmoothPlastic", smooth=45)
    leaves = w.part("Leaves", (72, 182, 62), "SmoothPlastic", smooth=40)
    prof = [(0, -0.62), (0.22, -0.60), (0.30, -0.48)]
    for k in range(12):
        t = k / 11
        y = lerp(-0.40, 3.10, t)
        r = lerp(0.33, 0.06, t ** 1.15) * (1.0 + 0.04 * math.sin(k * 2.1))
        prof.append((r, y))
    prof += [(0.03, 3.30), (0, 3.36)]
    orange.add(lathe(prof, segs=16))
    for y, r in ((0.45, 0.31), (1.05, 0.27), (1.65, 0.22), (2.25, 0.165), (2.75, 0.115)):
        rings.add(lathe([(r - 0.02, y - 0.03), (r + 0.012, y - 0.015), (r + 0.012, y + 0.015), (r - 0.02, y + 0.03)],
                        segs=16, close=False))
    # leafy top: stems fanning downward with leaflets
    for ang, L in ((-25, 0.62), (0, 0.70), (25, 0.60), (180 - 15, 0.5), (180 + 15, 0.55)):
        a = math.radians(ang)
        d = Vector((math.sin(a) * 0.5, -1.0, math.cos(a) * 0.35)).normalized()
        base = Vector((0, -0.60, 0))
        stem = [base, base + d * L * 0.5, base + d * L]
        leaves.add(sweep(stem, [0.07, 0.06, 0.0], [0.07, 0.06, 0.0], sides=6))
        for t in (0.55, 0.85):
            p = base + d * L * t
            leaves.add(slab(leaf_pts(0.26, 0.14, n=5), 0.04, 0.012, seg=1),
                       T(p.x, p.y, p.z) @ R("Y", ang) @ R("Z", 180 + (35 if t < 0.7 else -35)))
