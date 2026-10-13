"""Crystal Caverns: the hero, a giant crystal cluster bursting out of a mine mouth, and the area's
props.

A crag of violet rock (big turned blocks, darker at the foot, a lighter cap) with a mine cut into its
face: a dark opening framed in timber, big posts, a lintel, braces and a sign with a gem on it, a
second frame further in. Out of the top of the crag a cluster of crystals bursts upwards and outwards
like a fan: long faceted prisms (two crossing boxes each) in cyan, pink and gold with glowing Neon
points, the biggest cyan one 36 studs tall; small ones sprout from the rock face beside the entrance
and from the ground. Mine-cart tracks run out of the entrance towards the lane, a cart heaped with
gems on them, a lantern hangs from the frame and another from a post by the track. Beside the cart
a potato miner in a yellow hard hat with a lamp holds up a glowing gem, a pickaxe on its shoulder.
The rock, the timber frame and the big crystals are solid.
"""
import math

import numpy as np

import spsgeo as G

from .scenery import (Area, Build, bar, frame, ori, potato, prop_attrs, register, rock, round3)

ROCK = ("5e5672", "6a6280", "766e8e", "837b9c", "9088aa", "9e97b8")   # grey-violet, darker at the foot
CYAN = ("1fa4dc", "5ad6ff", "7ae8ff")      # body, its lighter turned facets, the glow
PINK = ("d43c9c", "ff74cc", "ff9ce2")
GOLD = ("e0901a", "ffbf3a", "ffd45a")
GEMS = (CYAN, PINK, GOLD)
WOOD = ("6b4226", "7a4a2a", "8a5a32", "9a6238")
IRON = ("3a3f4a", "4a505c", "5a6272", "2a2a30")
DARK = "120c1a"
GLOW = "ffd27a"
SKIN = ("d9b07a", "c49a64", "e8c490")
HAT = ("ffd23f", "f5c518", "ffe066")
OVERALL = ("3b6bd8", "2f5ab8")
VERTEX = G.rz(54.7356) @ G.ry(45.0)        # turns a cube to stand on its corner


def axis(heading, lean):
    """A direction leaning `lean` degrees from straight up towards `heading` (0 = the lane, 90 = +X)."""
    h, a = math.radians(heading), math.radians(lean)
    return np.array((math.sin(a) * math.sin(h), math.cos(a), -math.sin(a) * math.cos(h)))


def crystal(B, base, heading, lean, L, w, cols, lamp=False, solid=False, seg=0.0, name="Crystal", twist=0.0):
    """A crystal growing out of base: a faceted prism (a box and a narrower one turned 45 degrees about
    it) ending in a glowing point, a cube standing on its corner as wide as the prism; the big ones
    glow along a band below the point too."""
    d = axis(heading, lean)
    R = frame(d, None) @ G.ry(twist)
    base = np.asarray(base, float)
    c = base + d * (L / 2)
    out = [B.p(name, (w, L, w * 0.9), c, R, cols[0], solid=solid),
           B.p(name, (w * 0.8, L - 0.08, w * 0.8), c, R @ G.ry(45), cols[1], solid=solid)]
    top = base + d * L
    kw = dict(material="Neon", lamp=lamp, flicker=0.08 if lamp else None)
    if w >= 1.5:                                                   # a glint running up one edge
        g = 0.14 + 0.04 * w
        out.append(B.p(name, (g, L * 0.72, g), c + R @ (w / 2 - g / 2 + 0.05, L * 0.08, -w * 0.45 + g / 2 - 0.05), R,
                       cols[2], material="Neon"))
    if seg:
        out.append(B.p(name, (w * 0.9, seg + 0.1, w * 0.82), top + d * (seg / 2 - 0.05), R, cols[2], **kw))
        top = top + d * seg
    a = w * 0.86
    out.append(B.p(name, (a, a, a), top - d * (w * 0.05), R @ VERTEX, cols[2], **kw))
    return out


def gem(B, c, s, cols, glow=False, R=None, name="Gem"):
    """A loose gem: a cube on its corner (glowing if asked)."""
    R = VERTEX if R is None else R
    if glow:
        return B.p(name, (s, s, s), c, R, cols[2], material="Neon", lamp=True, flicker=0.1)
    return B.p(name, (s, s, s), c, R, cols[1])


def lantern(B, top, name="Lantern"):
    """A lantern hanging from top: a hook, an iron cap, a glowing body, an iron foot."""
    top = np.asarray(top, float)
    return [B.p(name, (0.14, 0.7, 0.14), top - (0, 0.35, 0), None, IRON[3]),
            B.p(name, (1.0, 0.3, 1.0), top - (0, 0.85, 0), G.ry(45), IRON[1]),
            B.p(name, (0.74, 0.95, 0.74), top - (0, 1.45, 0), None, GLOW, material="Neon", flicker=0.1, lamp=True),
            B.p(name, (0.9, 0.26, 0.9), top - (0, 2.05, 0), G.ry(45), IRON[0])]


def cart(B, c, heading=0.0, name="Cart", full=True):
    """A mine cart on rails along its own Z: an iron tub with a band and a rim, four wheels, a heap
    of gems in it, one glowing."""
    R = G.ry(heading)
    c = np.asarray(c, float)

    def at(v):
        return c + R @ np.asarray(v, float)
    out = [B.p(name, (3.6, 2.0, 4.4), at((0, 2.4, 0)), R, IRON[2]),
           B.p(name, (3.7, 0.36, 4.5), at((0, 1.9, 0)), R, IRON[0]),
           B.p(name, (3.9, 0.3, 4.7), at((0, 3.5, 0)), R, IRON[1])]
    for sx in (-1, 1):
        for sz in (-1, 1):
            out.append(B.p(name, (0.45, 1.3, 1.3), at((sx * 1.1, 1.29, sz * 1.4)), R, IRON[3], shape="Cylinder"))
    if full:
        for k, (x, y, z, s, col) in enumerate(((-0.9, 3.75, -1.2, 1.2, CYAN), (0.8, 3.8, -1.0, 1.1, GOLD),
                                               (0.0, 3.85, 0.3, 1.3, PINK), (-1.0, 3.7, 1.3, 1.0, GOLD),
                                               (1.0, 3.7, 1.4, 1.1, CYAN), (-0.2, 4.4, -0.6, 1.0, GOLD))):
            out.append(gem(B, at((x, y, z)), s, col, R=R @ ori(20 * k, 30 * k, 35)))
        out.append(gem(B, at((0.3, 4.6, 0.7)), 1.2, PINK, glow=True, R=R @ VERTEX))
    return out


def track(B, x, z0, z1, name="Track", n=8):
    """Two iron rails on wooden sleepers from z0 back to z1, centred on x."""
    out = []
    L = z1 - z0
    for k in range(n):
        z = z0 + 0.4 + (L - 0.8) * k / (n - 1)
        out.append(B.p("Sleeper", (3.6, 0.28 + 0.02 * (k % 2), 0.7), (x, 0.14 + 0.01 * (k % 2), z), G.ry(3 * (-1) ** k),
                       WOOD[k % 2]))
    for sx in (-1, 1):
        out.append(B.p(name, (0.32, 0.34, L), (x + sx * 1.1, 0.47, (z0 + z1) / 2), None, IRON[1]))
    return out


def miner(B, base, s, heading, name="Miner"):
    """A potato miner: boots, blue overalls, a yellow hard hat with a lamp on it, a pickaxe on its
    shoulder and a glowing gem held up in the other hand."""
    R = G.ry(heading)
    base = np.asarray(base, float)

    def at(v):
        return base + R @ np.asarray(v, float)
    leg = 1.0
    for sx in (-1, 1):
        B.p(name, (s * 0.24, leg + 0.12, s * 0.26), at((sx * s * 0.19, (leg + 0.12) / 2, 0.05)), R, OVERALL[1])
        B.p(name, (s * 0.3, 0.5, s * 0.44 + 0.02 * (sx > 0)), at((sx * s * 0.19, 0.25, -0.14)), R, WOOD[0])
    c = at((0, leg + s / 2, 0))
    potato(B, c, s, SKIN, R=R, name=name, glints=True, cheeks="ff9aa8")
    B.p(name, (s * 0.92, s * 0.3, s * 0.84), c + R @ (0, -s * 0.36, 0), R, OVERALL[0])            # overalls
    B.p(name, (s * 0.34, s * 0.16, 0.12), c + R @ (0, -s * 0.31, -s * 0.42 - 0.05), R, OVERALL[1],
        material="SmoothPlastic", shadow=False)                                                    # its pocket
    # the hard hat: a dome, a brim, a lamp on its front
    B.p(name, (s * 0.88, s * 0.3, s * 0.82), c + R @ (0, s * 0.62, 0.02), R, HAT[0])
    B.p(name, (s * 0.6, s * 0.16, s * 0.6), c + R @ (0, s * 0.82, 0.02), R @ G.ry(45), HAT[2])
    B.p(name, (s * 1.02, s * 0.08, s * 0.96), c + R @ (0, s * 0.49, -0.04), R, HAT[1])
    B.p(name, (s * 0.3, s * 0.24, s * 0.16), c + R @ (0, s * 0.64, -s * 0.45), R, IRON[0])
    B.p(name, (s * 0.2, s * 0.16, 0.12), c + R @ (0, s * 0.64, -s * 0.53 - 0.04), R, "fff6c8", material="Neon",
        lamp=True, flicker=0.06)
    # the right arm holds a pickaxe over its shoulder, the left holds up a glowing gem
    sh, hand = c + R @ (s * 0.42, -s * 0.04, -0.1), c + R @ (s * 0.58, s * 0.22, -s * 0.5)
    bar(B, name, sh, hand, s * 0.17, SKIN[1])
    a, b = hand + R @ (0.0, -0.9, -0.4), hand + R @ (0.2, 2.6, 1.6)
    bar(B, "Pickaxe", a, b, 0.4, WOOD[3])
    d = (b - a) / np.linalg.norm(b - a)
    side = R @ (1.0, 0.0, 0.0)
    bar(B, "Pickaxe", b - d * 0.3 - np.cross(side, d) * 1.6, b - d * 0.3 + np.cross(side, d) * 1.6, 0.5, "a8b0c0",
        t=0.42, over=0.0)
    sh2, hand2 = c + R @ (-s * 0.42, 0.0, -0.05), c + R @ (-s * 0.62, s * 0.42, -s * 0.22)
    bar(B, name, sh2, hand2, s * 0.17, SKIN[1])
    B.p("Gem", (1.0, 1.0, 1.0), hand2 + (0, 0.75, 0), VERTEX, PINK[2], material="Neon", lamp=True, flicker=0.1)


# ==================================================================== the hero

def hero(sc, parent):
    B = Build(sc, parent, "Crystal", seed=311)
    # the crag: big blocks, each turned and tipped a little, darker at the foot, lighter towards the
    # top; two buttresses lean in either side of the mine like the mouth of a cave
    for pos, size, R, col in (((-1.0, 4.4, 9.8), (34.0, 8.8, 8.0), ori(0, 4, 0), ROCK[0]),          # the back
                              ((-2.0, 5.75, 3.5), (16.0, 11.5, 10.0), None, ROCK[1]),           # the mine's face
                              ((-11.5, 4.65, 1.8), (7.5, 9.5, 9.0), ori(0, -22, 2.5), ROCK[2]),  # buttresses
                              ((7.5, 5.15, 1.8), (7.5, 10.5, 9.0), ori(0, 22, -2.5), ROCK[2]),
                              ((-16.6, 3.1, 5.5), (9.0, 6.5, 12.0), ori(2, 14, 0), ROCK[0]),     # shoulders
                              ((15.5, 3.35, 5.5), (9.0, 7.0, 12.0), ori(-2, -12, 0), ROCK[0]),
                              ((-18.6, 1.7, 0.8), (5.6, 3.6, 7.0), ori(3, 30, 0), ROCK[1]),      # low ends
                              ((18.6, 1.9, 1.2), (5.6, 4.0, 7.0), ori(-3, -26, 0), ROCK[1]),
                              ((-1.5, 13.0, 5.5), (13.0, 3.0, 9.0), ori(2, 8, -1.5), ROCK[3]),   # upper ledges
                              ((-10.5, 10.9, 5.0), (7.0, 3.5, 7.0), ori(-3, 25, 3), ROCK[3]),
                              ((8.5, 11.9, 5.0), (7.0, 3.8, 7.0), ori(3, -22, -3), ROCK[3]),
                              ((-0.5, 15.4, 6.5), (9.0, 2.4, 7.0), ori(-2, -12, 2), ROCK[4])):   # the cap
        B.p("Rock", size, pos, R, col, solid=True)
    for c, s, cols in (((-15.4, 0.0, -5.4), 2.6, (ROCK[1], ROCK[2], ROCK[0])),
                       ((13.4, 0.0, -5.2), 2.4, (ROCK[2], ROCK[1], ROCK[3])),
                       ((18.4, 0.0, -7.6), 1.9, (ROCK[1], ROCK[3], ROCK[2])),
                       ((-18.2, 0.0, -7.6), 2.0, (ROCK[2], ROCK[0], ROCK[3])),
                       ((-17.6, 6.2, 5.6), 2.6, (ROCK[2], ROCK[3], ROCK[1])),           # on the ledges
                       ((16.2, 6.7, 6.2), 2.4, (ROCK[3], ROCK[2], ROCK[4])),
                       ((-12.6, 9.2, 1.4), 2.0, (ROCK[3], ROCK[4], ROCK[2])),
                       ((8.4, 10.2, 1.0), 1.9, (ROCK[4], ROCK[3], ROCK[2]))):
        rock(B, c, s, cols, solid=s > 2.2)
    # the mine: a dark opening framed in timber, a second frame further in, a sign with a gem
    ex, zf = -2.0, -1.5
    B.plate("Opening", (6.2, 7.6, 0.12), (ex, 3.8, zf - 0.06), col=DARK)
    for sx in (-1, 1):
        B.p("Inner", (0.5, 6.4, 0.12), (ex + sx * 2.2, 3.2, zf - 0.14), None, "3a2616")
    B.p("Inner", (5.0, 0.5, 0.18), (ex, 6.4, zf - 0.16), None, "33210f")
    for sx in (-1, 1):
        B.p("Frame", (1.5, 8.6, 1.5), (ex + sx * 3.85, 4.3, zf - 0.6), None, WOOD[1 + (sx > 0)], solid=True)
        bar(B, "Frame", (ex + sx * 3.85, 6.9, zf - 1.1), (ex + sx * 1.9, 8.7, zf - 1.1), 0.7, WOOD[3])
    B.p("Frame", (10.6, 1.6, 1.8), (ex, 9.4, zf - 0.6), None, WOOD[2], solid=True)
    B.p("Sign", (4.4, 1.6, 0.3), (ex, 11.2, zf - 0.15), G.rz(-3), WOOD[3])
    B.p("Sign", (0.9, 0.9, 0.12), (ex, 11.2, zf - 0.36), G.rz(42), PINK[2], material="Neon", lamp=True)
    # the cluster bursting out of the top: (base, heading, lean, length, width, colour, lamp, solid, band)
    for k, (base, hd, ln, L, w, cols, lamp, solid, seg) in enumerate((
            ((0.5, 13.0, 7.0), 95.0, 8.0, 19.0, 5.6, CYAN, True, True, 2.6),
            ((3.5, 12.0, 7.4), 80.0, 30.0, 13.5, 4.0, PINK, True, True, 1.8),
            ((-4.5, 11.5, 7.0), 265.0, 33.0, 12.5, 3.7, GOLD, True, True, 1.6),
            ((-2.5, 12.0, 9.5), 215.0, 20.0, 12.0, 3.2, CYAN, False, False, 0.0),
            ((4.0, 12.5, 9.0), 140.0, 16.0, 10.0, 2.8, PINK, False, False, 0.0),
            ((7.5, 10.5, 5.0), 100.0, 55.0, 9.0, 2.6, CYAN, False, False, 0.0),
            ((-8.0, 9.5, 6.5), 255.0, 52.0, 9.5, 2.7, PINK, False, False, 0.0),
            ((-1.0, 12.0, 4.8), 350.0, 24.0, 7.5, 2.4, GOLD, True, False, 0.0),
            ((9.5, 12.5, 8.0), 60.0, 25.0, 7.0, 2.2, GOLD, False, False, 0.0),
            ((-11.0, 11.8, 7.5), 300.0, 26.0, 7.5, 2.3, CYAN, False, False, 0.0),
            ((-9.6, 1.2, -1.0), 330.0, 38.0, 4.6, 1.6, CYAN, False, False, 0.0),
            ((-10.4, 0.4, -0.6), 300.0, 18.0, 3.2, 1.3, PINK, False, False, 0.0),
            ((5.2, 1.6, -0.9), 30.0, 34.0, 4.2, 1.5, GOLD, False, False, 0.0),
            ((6.2, 0.4, -1.0), 50.0, 12.0, 2.8, 1.2, CYAN, False, False, 0.0),
            ((-15.0, 8.6, 3.0), 300.0, 26.0, 5.0, 1.8, PINK, False, False, 0.0),
            ((11.4, 9.0, 3.0), 70.0, 28.0, 5.6, 1.9, CYAN, False, False, 0.0),
            ((18.6, 0.4, -7.4), 60.0, 14.0, 3.6, 1.6, GOLD, False, False, 0.0),
            ((-18.2, 0.4, -7.2), 290.0, 16.0, 4.2, 1.7, CYAN, False, False, 0.0),
            ((-17.0, -0.3, -8.6), 250.0, 25.0, 2.8, 1.2, PINK, False, False, 0.0))):
        crystal(B, base, hd, ln, L, w, cols, lamp=lamp, solid=solid, seg=seg, twist=17.0 * k)
    # the track out of the mine, the cart heaped with gems, lanterns
    track(B, ex, -14.4, -1.6)
    cart(B, (ex, 0.0, -8.6))
    B.p("Lantern", (0.3, 0.3, 1.2), (ex + 3.85, 7.4, zf - 1.75), None, IRON[3])
    lantern(B, (ex + 3.85, 7.3, zf - 2.2))
    B.p("Post", (0.7, 6.2, 0.7), (ex - 3.6, 3.1, -12.8), None, WOOD[1])
    B.p("Post", (1.1, 0.5, 1.1), (ex - 3.6, 0.25, -12.8), G.ry(45), WOOD[0])
    bar(B, "Post", (ex - 3.6, 5.8, -12.8), (ex - 2.3, 6.3, -12.8), 0.32, IRON[3], over=0.15)
    lantern(B, (ex - 2.3, 6.2, -12.8))
    # loose gems about the foot
    for k, (x, z, s, cols, glow) in enumerate(((2.4, -5.0, 0.9, GOLD, False), (-6.6, -6.2, 0.8, CYAN, True),
                                               (3.4, -12.2, 0.7, PINK, False), (-7.6, -3.4, 0.7, GOLD, False))):
        gem(B, (x, s * 0.45, z), s, cols, glow=glow, R=ori(25, 30 * k, 40))
    # the potato miner beside the cart
    miner(B, (4.4, 0.0, -9.4), 4.2, 25.0)
    return B.finish()


# ==================================================================== props

def p_giant(sc, parent):
    B = Build(sc, parent, "GiantCluster", seed=321)
    B.p("Rock", (6.4, 1.6, 5.4), (0.0, 0.8, 0.0), G.ry(12), ROCK[1])
    B.p("Rock", (5.2, 1.4, 6.2), (0.2, 1.0, 0.1), G.ry(52), ROCK[2])
    for k, (x, z, hd, ln, L, w, cols, lamp) in enumerate(((0.0, 0.3, 30.0, 6.0, 9.5, 2.6, CYAN, True),
                                                       (1.2, 0.6, 85.0, 30.0, 6.5, 2.0, PINK, True),
                                                       (-1.3, 0.2, 275.0, 34.0, 6.0, 1.9, GOLD, True),
                                                       (0.4, -1.0, 350.0, 32.0, 4.2, 1.6, PINK, False),
                                                       (-0.6, 1.4, 200.0, 26.0, 5.0, 1.7, CYAN, False),
                                                       (1.6, -0.6, 120.0, 50.0, 3.4, 1.3, GOLD, False),
                                                       (-1.8, -0.8, 300.0, 55.0, 3.0, 1.2, CYAN, False))):
        crystal(B, (x, 1.2, z), hd, ln, L, w, cols, lamp=lamp, twist=23.0 * k)
    return B.finish()


def p_cluster(sc, parent):
    B = Build(sc, parent, "CrystalCluster", seed=322)
    rock(B, (0.0, 0.0, 0.0), 2.6, (ROCK[1], ROCK[2], ROCK[0]))
    for k, (x, z, hd, ln, L, w, cols) in enumerate(((0.0, 0.0, 20.0, 8.0, 5.4, 1.7, CYAN),
                                                    (0.8, 0.4, 95.0, 34.0, 3.8, 1.3, PINK),
                                                    (-0.9, 0.3, 260.0, 30.0, 4.2, 1.4, CYAN),
                                                    (0.3, -0.8, 340.0, 38.0, 2.8, 1.1, PINK),
                                                    (-0.4, 0.9, 180.0, 28.0, 3.2, 1.1, CYAN))):
        crystal(B, (x, 1.0, z), hd, ln, L, w, cols, lamp=k == 0, twist=31.0 * k)
    return B.finish()


def p_gold(sc, parent):
    B = Build(sc, parent, "GoldCrystals", seed=323)
    B.p("Rock", (3.0, 0.7, 2.6), (0.0, 0.35, 0.0), G.ry(20), ROCK[2])
    B.p("Rock", (2.4, 0.66, 3.0), (0.1, 0.33, 0.0), G.ry(65), ROCK[1])
    for k, (x, z, hd, ln, L, w) in enumerate(((0.0, 0.0, 40.0, 10.0, 3.8, 1.5), (0.7, 0.3, 110.0, 38.0, 2.5, 1.1),
                                              (-0.7, 0.2, 250.0, 35.0, 2.7, 1.1), (0.1, -0.7, 0.0, 42.0, 1.9, 0.9))):
        crystal(B, (x, 0.5, z), hd, ln, L, w, GOLD, lamp=k == 0, twist=29.0 * k)
    return B.finish()


def p_cart(sc, parent):
    B = Build(sc, parent, "MineCart", seed=324)
    track(B, 0.0, -4.6, 4.6, n=6)
    for sx in (-1, 1):                                                   # a buffer at the end of the line
        B.p("Buffer", (0.5, 1.4, 0.5), (sx * 1.1, 0.7, 4.3), None, WOOD[2])
    B.p("Buffer", (3.2, 0.6, 0.6), (0.0, 1.3, 4.3), None, "e8403a")
    cart(B, (0.0, 0.0, -0.6), heading=0.0)
    return B.finish()


def p_lantern(sc, parent):
    B = Build(sc, parent, "MineLantern", seed=325)
    B.p("Post", (1.6, 0.6, 1.6), (0.0, 0.3, 0.0), G.ry(45), ROCK[1])
    B.p("Post", (0.8, 7.0, 0.8), (0.0, 3.6, 0.0), G.ry(4), WOOD[1])
    B.p("Post", (1.0, 0.4, 1.0), (0.0, 7.2, 0.0), None, WOOD[3])
    bar(B, "Post", (0.0, 6.6, 0.0), (1.8, 7.1, 0.0), 0.34, IRON[3], over=0.15)
    bar(B, "Post", (0.0, 5.4, 0.0), (1.2, 6.9, 0.0), 0.24, IRON[0], t=0.26)
    lantern(B, (1.8, 7.0, 0.0))
    crystal(B, (0.4, 0.4, -0.5), 330.0, 25.0, 2.2, 0.9, CYAN, twist=15.0)
    gem(B, (-0.9, 0.4, -0.7), 0.7, PINK, R=ori(20, 30, 35))
    return B.finish()


def p_stalagmites(sc, parent):
    B = Build(sc, parent, "Stalagmites", seed=326)
    B.p("Rock", (5.0, 0.6, 4.0), (0.0, 0.3, 0.0), G.ry(14), ROCK[0])
    for k, (x, z, h, w, hd) in enumerate(((0.0, 0.0, 8.0, 2.4, 10.0), (1.9, 0.5, 5.4, 1.9, 40.0),
                                          (-1.8, 0.4, 4.6, 1.8, 70.0), (0.6, -1.4, 3.0, 1.4, 20.0))):
        y = 0.4
        for j, (fh, fw) in enumerate(((0.4, 1.0), (0.3, 0.7), (0.2, 0.44), (0.1, 0.22))):
            hh = h * fh
            lean = (2.0 + 2.0 * j) * (-1) ** k
            B.p("Stalagmite", (w * fw, hh + 0.12, w * fw * 0.92), (x + 0.06 * j * (-1) ** k, y + hh / 2, z),
                ori(lean, hd + 45 * j, -lean * 0.6), ROCK[min(1 + j, 5)])
            y += hh
    crystal(B, (-0.9, 0.5, -1.3), 320.0, 30.0, 1.8, 0.7, PINK, twist=10.0)
    return B.finish()


def p_gems(sc, parent):
    B = Build(sc, parent, "GemPile", seed=327)
    B.p("Sack", (2.2, 1.8, 2.0), (0.6, 0.9, 0.6), ori(0, 20, 4), "b88450")
    B.p("Sack", (1.4, 0.5, 1.3), (0.6, 2.0, 0.6), ori(0, 50, 0), "a07040")
    B.p("Sack", (0.3, 0.3, 1.6), (0.6, 1.66, 0.6), G.ry(50), "6b4226")
    for k, (x, y, z, s, cols, glow) in enumerate(((-1.0, 0.45, -0.6, 1.0, CYAN, False),
                                                  (-0.2, 0.42, -1.4, 0.9, GOLD, False),
                                                  (-1.6, 0.4, 0.5, 0.8, PINK, False),
                                                  (-0.6, 1.2, -0.3, 0.9, PINK, True),
                                                  (0.8, 0.35, -1.0, 0.7, CYAN, False),
                                                  (-1.9, 0.35, -0.9, 0.7, GOLD, False),
                                                  (1.6, 0.3, -0.3, 0.6, GOLD, True),
                                                  (-0.9, 0.3, 1.5, 0.6, CYAN, False))):
        gem(B, (x, y, z), s, cols, glow=glow, R=ori(20 + 9 * k, 37 * k, 35 + 5 * k))
    for k, (x, z) in enumerate(((0.2, -0.4), (-1.2, -1.5), (1.4, 1.6))):                  # gold coins
        B.p("Coin", (0.6, 0.14 + 0.02 * k, 0.6), (x, 0.08 + 0.01 * k, z), G.ry(20 * k), GOLD[1])
    return B.finish()


def p_pickaxe(sc, parent):
    B = Build(sc, parent, "PickaxeRock", seed=328)
    rock(B, (0.0, 0.0, 0.0), 3.4, (ROCK[1], ROCK[2], ROCK[0]))
    head = np.array((0.1, 2.75, -0.5))
    h = np.array((0.88, -0.47, 0.0))                              # the head, its right point in the rock
    d = np.array((0.42, 0.79, -0.44))                             # the handle, up and out
    d /= np.linalg.norm(d)
    bar(B, "Pickaxe", head - h * 1.9, head + h * 1.7, 0.6, "a8b0c0", t=0.5, n=(0, 0, -1))
    B.p("Pickaxe", (0.8, 0.8, 0.8), head, frame(d, None), IRON[1])
    top = head + d * 5.0
    bar(B, "Pickaxe", head + d * 0.2, top, 0.5, WOOD[3])
    bar(B, "Pickaxe", top - d * 0.6, top + d * 0.25, 0.62, WOOD[0], t=0.64)                    # the grip
    crystal(B, (-1.0, 1.2, -0.9), 300.0, 30.0, 2.4, 1.0, CYAN, twist=20.0)
    crystal(B, (1.4, 0.6, -0.8), 60.0, 34.0, 1.8, 0.8, GOLD, twist=50.0)
    for k, (x, z) in enumerate(((-2.0, -1.6), (2.2, -1.3), (0.6, -2.2))):              # chips knocked off
        B.p("Chip", (0.5, 0.36, 0.44), (x, 0.18, z), ori(10, 40 * k, 12), ROCK[2 + k % 2])
    return B.finish()


def p_timber(sc, parent):
    B = Build(sc, parent, "TimberSupport", seed=329)
    for sx in (-1, 1):
        B.p("Post", (1.2, 7.4, 1.2), (sx * 3.2, 3.7, 0.0), G.rz(sx * 2.0), WOOD[1 + (sx > 0)])
        B.p("Post", (1.6, 0.5, 1.6), (sx * 3.25, 0.25, 0.0), G.ry(10 * sx), ROCK[1])
        bar(B, "Brace", (sx * 3.2, 5.0, -0.1), (sx * 1.6, 7.0, -0.1), 0.5, WOOD[3], t=0.52)
    B.p("Beam", (8.6, 1.2, 1.5), (0.0, 7.75, 0.0), None, WOOD[0])
    B.p("Beam", (7.0, 0.3, 1.2), (0.0, 8.5, 0.1), G.ry(2), WOOD[3])
    for k, (x, y, z, s) in enumerate(((-2.4, 8.9, 0.2, 1.4), (1.6, 8.85, -0.1, 1.2), (3.6, 8.7, 0.3, 0.9))):
        B.p("Rubble", (s * 1.3, s * 0.7, s), (x, y, z), ori(6, 30 * k, -5), ROCK[2 + k % 3])     # rock it holds up
    lantern(B, (1.6, 7.15, -0.1))
    B.p("Lantern", (0.3, 0.3, 0.3), (1.6, 7.2, -0.1), None, IRON[3])
    crystal(B, (-3.6, -0.3, -0.9), 300.0, 30.0, 2.6, 0.9, PINK, twist=20.0)
    return B.finish()


def p_geode(sc, parent):
    B = Build(sc, parent, "Geode", seed=330)
    from spsgeo import CF
    with B.at(CF(np.array((0.0, 2.3, 0.3)), G.rx(18))):           # tipped back to show the inside
        B.p("Shell", (4.4, 4.4, 1.3), (0.0, 0.0, 1.1), None, ROCK[2])
        for k in range(8):                                          # the broken rim, round
            a = 2 * math.pi * k / 8 + 0.2
            B.p("Shell", (1.95, 1.0, 2.0 + 0.04 * (k % 2)), (2.1 * math.cos(a), 2.1 * math.sin(a), 0.2),
                G.rz(math.degrees(a) + 90.0), ROCK[(1, 3)[k % 2]])
        B.p("Lining", (3.4, 3.4, 0.24), (0.0, 0.0, 0.42), None, "e6dcf6")
        B.p("Lining", (3.3, 3.3, 0.26), (0.0, 0.0, 0.42), G.rz(45), "d8ccee")
        for k, (x, y, hd, ln, L, w, cols) in enumerate(((0.0, -0.9, 0.0, 70.0, 1.9, 0.9, CYAN),
                                                       (-1.0, -0.3, 330.0, 62.0, 1.6, 0.8, PINK),
                                                       (1.0, -0.2, 30.0, 64.0, 1.5, 0.8, PINK),
                                                       (-0.5, 0.8, 340.0, 80.0, 1.3, 0.7, GOLD),
                                                       (0.6, 0.8, 20.0, 82.0, 1.4, 0.7, CYAN),
                                                       (0.0, 0.0, 0.0, 88.0, 1.7, 0.85, PINK))):
            crystal(B, (x, y, 0.5), hd, ln, L, w, cols, lamp=k in (0, 5), twist=25.0 * k)
    B.p("Shell", (2.6, 1.4, 2.4), (3.0, 0.55, -2.0), ori(10, 35, 8), ROCK[2])               # the half knocked off
    B.p("Lining", (2.0, 0.2, 1.8), (3.0, 1.28, -2.0), ori(10, 35, 8), "e6dcf6")
    return B.finish()


AREA = register(Area("Crystal", "Crystal Caverns", hero, [
    (p_giant, prop_attrs(3, 0.9, 1.25, "Edge", True)),
    (p_cluster, prop_attrs(6, 0.8, 1.3, "Side", False)),
    (p_gold, prop_attrs(6, 0.8, 1.3, "Any", False)),
    (p_cart, prop_attrs(3, 0.95, 1.15, "Side", True)),
    (p_lantern, prop_attrs(5, 0.95, 1.15, "Side", False)),
    (p_stalagmites, prop_attrs(6, 0.8, 1.35, "Side", True)),
    (p_gems, prop_attrs(6, 0.8, 1.2, "Any", False)),
    (p_pickaxe, prop_attrs(3, 0.9, 1.2, "Side", True)),
    (p_timber, prop_attrs(3, 0.95, 1.15, "Edge", True)),
    (p_geode, prop_attrs(4, 0.85, 1.25, "Side", True)),
], ground="4c3468"))
