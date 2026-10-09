"""Weapon designs. Each function receives a wlib.Weapon and fills in its parts.

Roblox space, relative to the Handle (the hand grips at the origin):
  +Y up the weapon, +X the cutting edge / hammer face, Z the thin side.
"""
import math

from mathutils import Vector

from wlib import (R, S, T, arc_pts, bar_x, bar_y, blade, box, catmull, circle_pts, cylinder, helix_ribbon, ico,
                  banded_blade, blade_face_z, bolt_pts, face_inlay, katana_blade, lathe, leaf_pts, lerp, profile_blade,
                  puff, rock, slab, sphere, split_by_tag, star_pts, surface_vein, sweep, sweep_band, sword_blade,
                  teardrop, torus, wheel_pommel, wrapped_grip)

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
    blade_p.add(sword_blade(0.60, 3.26, 4.16, w0=0.285, w1=0.25, h0=0.125, h1=0.10, ef=0.02,
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
