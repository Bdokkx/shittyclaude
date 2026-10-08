"""October event arena "Pumpkin Hollow": haunted house on a hill, graveyard, giant jack-o'-lantern, witch's
cauldron, pumpkin patches, dead trees, ghosts, bats, string lights round the field and a big moon.
Built into the same arena frame as the other maps (see arenas.py); glow is Neon only (no light objects)."""
import math
import random

import autumn as A
import buildings as Bd
import props as P

THEME = dict(
    grass=("#6F8A3A", "#647D33", "#7A9440"), lip="#4F6B2A", dirt=("#6E4A2C", "#5A3A22"),
    rock=("#6B5B86", "#55476E", "#3F3456"), border="#4A3326", trim="#2E2230",
    field=((222, 124, 46), (200, 106, 36)), safe=((122, 74, 164), (106, 62, 146)),
    hang=("#4F6B2A", "#3E5520"), sign=("#2E2230", "#FF8A1F"))
DISPLAY = "PUMPKIN HOLLOW"
GLOW = "#FFB347"
PURPLE_GLOW = "#B67CFF"
GREEN_GLOW = "#9BE34A"
DARK = "#2B2233"


# ------------------------------------------------------------------ props

def dead_tree(m, size, seed):
    """Bare twisted tree: leaning trunk, forked branches, a few last orange leaves."""
    rng = random.Random(seed)
    h = (11, 15, 19)[size]
    bark = rng.choice(("#3A2A2E", "#463236", "#33262A"))
    x = z = y = 0.0
    for k in range(3):
        nx, nz = x + rng.uniform(-0.9, 0.9), z + rng.uniform(-0.9, 0.9)
        m.beam((x, y, z), (nx, y + h * 0.22 + 0.5, nz), 2.0 - 0.4 * k, bark)
        x, y, z = nx, y + h * 0.22, nz
    tips = []

    def branch(px, py, pz, ang, up, length, thick, depth):
        ex = px + math.cos(ang) * length * math.cos(up)
        ez = pz + math.sin(ang) * length * math.cos(up)
        ey = py + length * math.sin(up)
        m.beam((px, py, pz), (ex, ey, ez), thick, bark)
        if depth > 0:
            for d in (-0.6, 0.55):
                branch(ex, ey, ez, ang + d + rng.uniform(-0.2, 0.2), up + rng.uniform(-0.15, 0.25), length * 0.62,
                       thick * 0.65, depth - 1)
        else:
            tips.append((ex, ey, ez))
    for i in range(rng.randint(3, 4)):
        a = i * 2 * math.pi / 3.5 + rng.uniform(-0.4, 0.4)
        branch(x, y - rng.uniform(0, 2), z, a, rng.uniform(0.35, 0.8), h * 0.32, 1.0, 2)
    with m.ctx(collide=False, shadow=False):
        for tx, ty, tz in rng.sample(tips, min(len(tips), 4)):
            m.box((tx, ty, tz), (0.8, 0.12, 0.6), rng.choice(A.LEAVES), ry=rng.uniform(0, 180))


def tombstone(m, seed):
    rng = random.Random(seed)
    kind = rng.randint(0, 3)
    stone, dark = rng.choice((("#9A96A8", "#7C788C"), ("#8C93A6", "#6E7488"), ("#A7A2B5", "#878299")))
    m.box((0, 0.2, 1.4), (2.4, 0.4, 3.2), "#4A3326")                     # grave mound
    tilt = rng.uniform(-8, 8)
    with m.at((0, 0, 0), rz=tilt):
        m.box((0, 0.3, 0), (2.8, 0.6, 1.2), dark)
        if kind == 0:                                                      # round-top slab
            m.box((0, 1.9, 0), (2.2, 2.8, 0.6), stone)
            m.box((0, 3.5, 0), (1.6, 0.5, 0.6), stone)
            m.box((0, 3.8, 0), (0.9, 0.3, 0.6), stone)
        elif kind == 1:                                                    # cross
            m.box((0, 2.4, 0), (0.6, 3.8, 0.6), stone)
            m.box((0, 3.2, 0), (2.2, 0.6, 0.6), stone)
        elif kind == 2:                                                    # tall obelisk
            m.box((0, 2.6, 0), (1.2, 4.2, 1.2), stone)
            m.box((0, 5.0, 0), (0.7, 0.8, 0.7), stone, ry=45)
        else:                                                              # broken slab
            m.box((0, 1.4, 0), (2.2, 1.8, 0.6), stone, rz=6)
            m.box((1.4, 0.35, -0.8), (1.0, 0.5, 0.5), stone, ry=30)
        m.box((0, 2.0 if kind != 2 else 3.0, -0.32), (1.2, 0.2, 0.05), dark)   # carved line
    if rng.random() < 0.5:                                                 # candle
        with m.ctx(collide=False, shadow=False):
            m.box((1.0, 0.75, -0.9), (0.35, 0.7, 0.35), "#F2EFE6")
            m.box((1.0, 1.25, -0.9), (0.2, 0.3, 0.2), GLOW, mat="Neon")


def iron_fence(m, a, b, h=3.6):
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    n = max(1, int(L / 1.1))
    ry = math.degrees(math.atan2(b[0] - a[0], b[1] - a[1]))
    with m.at(((a[0] + b[0]) / 2, 0, (a[1] + b[1]) / 2), ry=ry):
        m.box((0, h - 0.6, 0), (0.25, 0.25, L), "#1E1A22")
        m.box((0, 0.7, 0), (0.25, 0.25, L), "#1E1A22")
        for i in range(n + 1):
            z = -L / 2 + i * L / n
            m.box((0, h / 2, z), (0.2, h, 0.2), "#1E1A22")
            m.box((0, h + 0.2, z), (0.35, 0.35, 0.35), "#1E1A22", rx=45)
    for p in (a, b):
        m.box((p[0], h / 2 + 0.2, p[1]), (1.0, h + 0.4, 1.0), "#6E7488")
        m.box((p[0], h + 0.6, p[1]), (1.3, 0.4, 1.3), "#55476E")


def haunted_house(m):
    """Two storeys, a corner tower with a witch-hat roof, crooked shutters, glowing windows, porch."""
    wall, wall2, roof, trim = "#4A3B5C", "#3F3250", DARK, "#1E1A22"
    W, D, H1, H2 = 18.0, 13.0, 7.0, 6.0
    m.box((0, 0.6, 0), (W + 2, 1.2, D + 2), "#55476E")                       # stone footing
    Bd.plank_wall(m, -W / 2, W / 2, 1.2, H1 + H2, -D / 2, -D / 2 + 0.7, tones=(wall, wall2), vertical=True)
    Bd.plank_wall(m, -W / 2, W / 2, 1.2, H1 + H2, D / 2 - 0.7, D / 2, tones=(wall, wall2), vertical=True)
    Bd.plank_wall(m, -W / 2, -W / 2 + 0.7, 1.2, H1 + H2, -D / 2, D / 2, tones=(wall, wall2), vertical=True)
    Bd.plank_wall(m, W / 2 - 0.7, W / 2, 1.2, H1 + H2, -D / 2, D / 2, tones=(wall, wall2), vertical=True)
    m.box((0, H1 + 0.6, -D / 2 - 0.2), (W + 0.6, 0.6, 0.6), trim)             # floor band
    for x in (-W / 2, W / 2):
        for z in (-D / 2, D / 2):
            m.box((x, (H1 + H2) / 2 + 0.6, z), (1.0, H1 + H2, 1.0), trim)
    # glowing windows with crooked shutters
    for row, y in enumerate((4.2, H1 + 3.4)):
        for i, x in enumerate((-6.0, -1.5, 3.0, 6.5) if row else (-6.0, 6.0)):
            m.box((x, y, -D / 2 - 0.05), (2.2, 2.8, 0.2), GLOW if (i + row) % 3 else PURPLE_GLOW, mat="Neon")
            m.box((x, y + 1.6, -D / 2 - 0.3), (2.8, 0.4, 0.4), trim)
            m.box((x, y - 1.6, -D / 2 - 0.3), (2.8, 0.4, 0.4), trim)
            m.box((x, y, -D / 2 - 0.3), (0.25, 2.8, 0.2), trim)
            m.box((x - 1.6, y - 0.2, -D / 2 - 0.35), (0.9, 3.0, 0.2), "#2E2230", rz=8 if i % 2 else -4)
    # door + porch with a little roof on posts
    m.box((0, 3.3, -D / 2 - 0.1), (3.0, 4.2, 0.3), "#2E1E16")
    m.box((0, 5.6, -D / 2 - 0.2), (3.6, 0.5, 0.4), trim)
    m.box((0.9, 3.2, -D / 2 - 0.35), (0.3, 0.3, 0.2), GLOW, mat="Neon")
    m.box((0, 1.0, -D / 2 - 2.6), (8.0, 0.6, 4.6), "#5A3A22")
    for x in (-3.6, 3.6):
        m.box((x, 3.6, -D / 2 - 4.4), (0.6, 5.0, 0.6), trim)
    m.box((0, 6.4, -D / 2 - 2.6), (9.0, 0.5, 5.6), roof, rx=-12)
    # main roof + tower
    Bd.gable_roof(m, W, D, H1 + H2 + 1.2, 48, roof, trim, overhang=1.4, gable=wall)
    with m.at((W / 2 - 1.0, 0, -D / 2 + 1.0)):
        m.octagon(10.0, 3.4, 20.0, wall2)
        m.box((0, 15.0, -3.3), (1.8, 2.4, 0.2), GLOW, mat="Neon")
        m.octagon(20.4, 3.9, 0.8, trim)
        for i, (r, y) in enumerate(((3.6, 21.6), (2.8, 23.2), (2.0, 24.8), (1.2, 26.4), (0.6, 28.0))):
            m.octagon(y, r, 1.6, roof)
        m.box((0.4, 29.4, 0), (0.4, 1.6, 0.4), trim, rz=-20)
    # chimney, crooked
    m.box((-W / 2 + 3.5, H1 + H2 + 8.0, 2.0), (2.2, 6.0, 2.2), "#55476E", rz=4)


def giant_pumpkin(m, s=5.0):
    A.pumpkin(m, s, 77, carved=True, light=False)
    with m.ctx(collide=False, shadow=False):                                # vines around the base
        for a in range(0, 360, 60):
            r = 1.4 * s
            m.beam((math.cos(math.radians(a)) * r * 0.8, 0.3, math.sin(math.radians(a)) * r * 0.8),
                   (math.cos(math.radians(a + 25)) * r * 1.4, 0.2, math.sin(math.radians(a + 25)) * r * 1.4), 0.5, A.VINE)
            m.box((math.cos(math.radians(a + 25)) * r * 1.4, 0.3, math.sin(math.radians(a + 25)) * r * 1.4),
                  (1.6, 0.2, 1.2), A.LEAF, ry=a)


def cauldron(m):
    m.octagon(1.6, 2.6, 3.0, "#1E1A22")
    m.octagon(3.2, 2.9, 0.5, "#2B2233")
    m.octagon(3.25, 2.3, 0.3, GREEN_GLOW, mat="Neon")
    with m.ctx(collide=False, shadow=False):
        for i, (x, z, s) in enumerate(((0.5, 0.3, 0.7), (-0.8, -0.4, 0.5), (0.2, -0.9, 0.4))):
            m.box((x, 3.6 + 0.4 * i, z), (s, s, s), GREEN_GLOW, mat="Neon", ry=30 * i)
        for a in (0, 120, 240):                                              # fire under it
            m.box((math.cos(math.radians(a)) * 1.4, 0.3, math.sin(math.radians(a)) * 1.4), (3.0, 0.6, 0.6), "#5A3A22",
                  ry=-a)
        m.box((0, 0.5, 0), (1.4, 0.8, 1.4), "#FF8A1F", mat="Neon", ry=45)
    for x in (-2.6, 2.6):                                                    # legs/stand
        m.box((x, 1.0, 0), (0.4, 2.0, 0.4), "#1E1A22")
    # broom leaning on it and a witch hat on the ground
    m.beam((3.0, 0.2, 1.8), (2.0, 5.0, 1.0), 0.3, "#6B4226")
    m.box((3.1, 0.6, 1.9), (1.0, 1.4, 1.0), "#D9B77E")
    with m.at((-4.2, 0, 1.5), rz=12):
        m.box((0, 0.15, 0), (3.0, 0.3, 3.0), DARK)
        m.box((0, 1.0, 0), (1.6, 1.6, 1.6), DARK)
        m.box((0.2, 2.2, 0), (1.0, 1.2, 1.0), DARK, rz=-10)
        m.box((0.5, 3.0, 0), (0.5, 0.8, 0.5), DARK, rz=-25)
        m.box((0, 0.5, 0), (1.7, 0.4, 1.7), "#B67CFF")


def ghost(m, seed):
    rng = random.Random(seed)
    with m.ctx(collide=False, shadow=False):
        y = rng.uniform(7, 14)
        m.box((0, y, 0), (2.6, 2.6, 2.2), "#F4F1FF", transparency=0.15)
        m.box((0, y - 1.8, 0.2), (2.2, 1.4, 1.8), "#F4F1FF", transparency=0.25, rx=12)
        m.box((0.3, y - 3.0, 0.6), (1.4, 1.2, 1.2), "#F4F1FF", transparency=0.35, rx=24)
        for x in (-0.5, 0.5):
            m.box((x, y + 0.4, -1.12), (0.45, 0.7, 0.05), "#1E1A22")
        m.box((0, y - 0.4, -1.12), (0.5, 0.5, 0.05), "#1E1A22")
        for s in (-1, 1):
            m.box((s * 1.6, y - 0.3, 0), (0.8, 1.6, 0.8), "#F4F1FF", transparency=0.2, rz=s * 35)


def bat(m, seed):
    rng = random.Random(seed)
    with m.ctx(collide=False, shadow=False):
        m.box((0, 0, 0), (0.7, 0.6, 0.9), "#1E1A22")
        for s in (-1, 1):
            m.box((s * 1.0, 0.15, 0), (1.4, 0.15, 0.8), "#1E1A22", rz=s * rng.uniform(15, 35))
            m.box((s * 0.25, 0.45, -0.3), (0.2, 0.3, 0.2), "#1E1A22")


def string_lights(m, pts, y=7.0, every=1.8):
    """Posts at each point with a sagging wire of alternating orange/purple neon bulbs between them."""
    for x, z in pts:
        m.box((x, y / 2 - 0.5, z), (0.6, y + 1.4, 0.6), "#3A2A1E")
        m.box((x, y + 0.4, z), (0.9, 0.4, 0.9), "#2B2233")
    with m.ctx(collide=False, shadow=False):
        for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
            L = math.hypot(x1 - x0, z1 - z0)
            n = max(2, int(L / every))
            prev = None
            for i in range(n + 1):
                t = i / n
                sag = 2.2 * 4 * t * (1 - t)
                p = (x0 + (x1 - x0) * t, y - sag, z0 + (z1 - z0) * t)
                if prev:
                    m.beam(prev, p, 0.12, "#1E1A22")
                if 0 < i < n:
                    m.box((p[0], p[1] - 0.45, p[2]), (0.5, 0.7, 0.5), (GLOW, PURPLE_GLOW, "#FF8A1F")[i % 3], mat="Neon")
                prev = p


def moon(m):
    with m.ctx(collide=False, shadow=False):
        m.octagon(0, 34, 2, "#FFF4C2", mat="Neon")
        m.octagon(0.6, 9, 1.2, "#F2E4A6", mat="Neon")
        with m.at((12, 0.6, -10)):
            m.octagon(0, 5, 1.2, "#F2E4A6", mat="Neon")
        with m.at((-14, 0.6, 12)):
            m.octagon(0, 4, 1.2, "#F2E4A6", mat="Neon")


def lantern_pumpkin_post(m, seed):
    m.box((0, 2.0, 0), (0.6, 4.0, 0.6), "#3A2A1E")
    with m.at((0, 4.0, 0)):
        A.pumpkin(m, 0.6, seed, carved=True, light=False)


# ------------------------------------------------------------------ scenery

def scenery(m, g, sp, k, place, scatter, seed):
    """Hero set pieces at fixed spots, then trees and small props scattered on the rest."""
    from arenas import FX, FZ
    place("HauntedHouse", -110, 72, 17, haunted_house, ry=-90)
    place("GiantPumpkin", 104, 78, 10, lambda m_: giant_pumpkin(m_, 5.0), ry=90)
    place("Cauldron", -100, -58, 6, cauldron, ry=-90)

    def graveyard(m_):
        w, d = 30.0, 44.0
        rng = random.Random(seed)
        corners = [(-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2)]
        iron_fence(m_, corners[1], corners[2])
        iron_fence(m_, corners[2], corners[3])
        iron_fence(m_, corners[3], corners[0])
        iron_fence(m_, corners[0], (-3.0, -d / 2))                       # gate gap facing the field
        iron_fence(m_, (3.0, -d / 2), corners[1])
        m_.box((0, 0.05, 0), (w - 1, 0.1, d - 1), "#4A3326")
        for i, zz in enumerate(range(-16, 20, 7)):
            for j, xx in enumerate((-10, -4, 4, 10)):
                if (i + j) % 5 == 4:
                    continue
                with m_.at((xx + rng.uniform(-0.8, 0.8), 0.1, zz + rng.uniform(-0.6, 0.6)), ry=rng.uniform(-10, 10)):
                    tombstone(m_, seed * 31 + i * 7 + j)
        with m_.at((0, 0, 18)):
            dead_tree(m_, 2, seed + 5)
    place("Graveyard", 108, -62, 26, graveyard, ry=90)

    for i, (x, z) in enumerate(((-104, -112), (98, 140))):
        place("PumpkinPatch", x, z, 11, lambda m_, i=i: (A.soil_row(m_, 14, i), pumpkin_rows(m_, i)))
    for i, (x, z) in enumerate(((-96, 20), (96, 20), (-100, 128), (100, -128))):
        place("Scarecrow", x, z, 3, lambda m_: A.scarecrow(m_), ry=90 if x < 0 else -90)

    # string lights along both long sides, just outside the walls
    for s in (-1, 1):
        pts = [(s * 83.0, z) for z in range(-150, 151, 30)]
        with m.ctx(stage="props", folder="Scenery", tag="StringLights:%d" % next(k), collide=False):
            string_lights(m, [(x, z) for x, z in pts if g.at(x, z) is not None], y=7.0)
        for x, z in pts:
            sp.taken.append((x, z, 1.5))
    # jack-o'-lantern posts along the short ends
    for s in (-1, 1):
        for x in (-60, -30, 30, 60):
            place("PumpkinPost", x, s * 160, 1.5, lambda m_, x=x: lantern_pumpkin_post(m_, x), ry=0 if s > 0 else 180)

    with m.ctx(stage="props", folder="Scenery", tag="Moon:%d" % next(k), collide=False):
        with m.at((-290, 150, 362), ry=148, rx=90):
            moon(m)
    rng = random.Random(seed + 9)
    for i in range(8):
        for _ in range(100):
            x, z = rng.uniform(-125, 125), rng.uniform(-200, 200)
            h = g.at(x, z)
            if h is not None and abs(x) > FX + 10 and sp.free(x, z, 2.0):
                with m.ctx(stage="props", folder="Scenery", tag="Ghost:%d" % next(k), collide=False):
                    with m.at((x, h, z), ry=rng.uniform(0, 360)):
                        ghost(m, i)
                break
    with m.ctx(stage="props", folder="Scenery", tag="Bats:%d" % next(k), collide=False):
        for i in range(10):
            with m.at((-110 + rng.uniform(-14, 14), 34 + rng.uniform(-4, 8), 72 + rng.uniform(-14, 14)),
                      ry=rng.uniform(0, 360), rz=rng.uniform(-15, 15)):
                bat(m, i)

    def maple(m_, size, s):
        P.oak(m_, size, s, greens=("#D7372C", "#B82C24"))

    def orange_oak(m_, size, s):
        P.oak(m_, size, s, greens=("#F28C28", "#E2582A"))
    trees = [(dead_tree, 5), (orange_oak, 2), (maple, 2),
             (lambda m_, sz, s: P.birch(m_, sz, s, greens=("#FFC83D", "#F2A922")), 1)]
    extras = [(lambda m_, s: A.pumpkin_pile(m_, s, n=3, carved_first=s % 2 == 0), 3.0, 22, "Pumpkins"),
              (lambda m_, s: A.hay_bale(m_, ry=random.Random(s).uniform(0, 90), seed=s,
                                        top=(lambda m2: A.pumpkin(m2, 0.7, s, carved=True, light=False))), 3.0, 12, "HayBale"),
              (lambda m_, s: tombstone(m_, s), 2.2, 14, "Tombstone"),
              (lambda m_, s: A.leaf_litter(m_, s), 1.6, 70, "Leaves"),
              (lambda m_, s: A.corn_stalk(m_, s), 1.0, 30, "Corn"),
              (lambda m_, s: P.tuft_cluster(m_, s, greens=("#6F8A3A", "#8A9A44", "#4F6B2A")), 1.5, 60, "Grass")]
    scatter(m, g, sp, k, seed, trees, 70, extras)


def pumpkin_rows(m, seed):
    rng = random.Random(seed)
    for x in (-5.0, -1.5, 2.0, 5.5):
        with m.at((x, 0.4, rng.uniform(-0.4, 0.4)), ry=rng.uniform(0, 360)):
            A.pumpkin(m, rng.uniform(0.7, 1.1), rng.randint(0, 9999), carved=rng.random() < 0.3, light=False)


def pumpkin_obstacles(m, k, obstacle):
    """Giant pumpkins as obstacles: same spots as the Farm hay bales, collider 6 x 4.6 x 6."""
    for x, z in ((-38, -55), (38, -55), (-38, 55), (38, 55), (0, -28), (0, 28)):
        tag = obstacle(m, "Pumpkin", k, (x, 2.3, z), (6, 4.6, 6), "#FF8A1F")
        with m.ctx(stage="obstacle", folder="Obstacles", tag=tag, collide=False, shadow=True):
            with m.at((x, 0, z), ry=0 if z < 0 else 180):          # carved face looks towards the nearer end
                A.pumpkin(m, 2.35, int(x * 3 + z), carved=True, light=False)
