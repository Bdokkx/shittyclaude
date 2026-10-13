"""Candy Crops: the hero, a huge three-tier cake with a potato on top, and the area's props.

The cake stands on a round white board: a chocolate tier, a pink tier and a vanilla tier, each an
eight-sided drum (two crossing blocks and two more turned 45, Folk Valley's round grown to eight even
sides) under a lid of icing that overhangs it. Icing drips of different lengths run down every side
(white on the chocolate and the pink, pink on the vanilla), a band of sprinkles goes round each
middle and cherries on whipped cream sit along the rims. A slice has been cut out of the front of
the chocolate tier, showing the sponge with its layers of cream and jam. Striped candles burn on the
top tier (Neon flames that flicker and light up at night) round the cake-topper: a potato in a party
hat on little legs, cheering with a swirl lollipop held high. A giant candy cane and a giant
lollipop stand either side, gumdrops at the foot.
"""
import math

import numpy as np

import spsgeo as G
from spsgeo import CF

from .scenery import (Area, Build, bar, flame, ori, potato, prop_attrs, register, round3, shade)

T8 = math.tan(math.radians(22.5))          # half a flat of an eight-sided round, per unit of its radius

CHOC = ("6a3720", "7a4228", "5a2e1a")      # chocolate frosting
SPONGE = ("b0703f", "a06236")              # chocolate sponge, inside
PINK = ("ff8cc0", "ff78b2", "ffa6d0")
VANILLA = ("fff6ea", "fbe9d4", "fffcf6")
ICING = ("ffffff", "fff3f8")
PINKICE = ("ff5fa2", "ff4d94", "ff7ab4")
CREAM = "fff1dc"
JAM = "ff3d7f"
CHERRY = ("e8203a", "d0142e")
LEAF = ("4fb03a", "3f9a34")
BOARD = ("f4f2fc", "e2dcf6", "d0c8ee")
SPRINK = ("ff3b5c", "3b8bff", "ffd23f", "4fc24a", "a46bff", "ff9f3d")
SKIN = ("d9b07a", "c49a64", "e8c490")
RED, WHITE = "ee2f45", "fffaf6"
MINT = ("7de8c0", "5fd8aa", "a4f2d6")
LEMON = ("ffe14d", "ffd23f", "fff08a")
GRAPE = ("b47cff", "a066f0", "c89aff")
SKY = ("7ad1ff", "5cbcf5", "a4e2ff")
GINGER = ("b8743a", "a4642e", "c8864a")
DOUGH = ("e8a860", "d8944c", "f0bc78")
WAFER = ("e8b468", "d49a4c", "f2c884")


# ==================================================================== shapes

def drum(B, name, c, r, h, cols, R=None, solid=False, notch=0.0, foot=False, **kw):
    """An eight-sided drum r to its flats: two crossing slabs and two more turned 45 degrees (Folk
    Valley's round, grown to eight even sides), heights a hair apart so no tops fight. notch cuts that
    much off the slab facing the front (-Z), which leaves a wedge out of the front: a slice taken.
    With foot, c is the middle of its bottom and every slab stands on it (for drums on the ground).
    Every slab is centred on the drum's axis with its own Y along it, so spin= turns the whole drum."""
    R = np.eye(3) if R is None else R
    c = np.asarray(c, float)
    t = r * T8
    cols = tuple(cols) + (cols[-1],)
    out = []
    for k, (size, off, Rk, col) in enumerate((((2 * r, h, 2 * t), 0.0, R, cols[0]),
                                              ((2 * t, h - 0.04, 2 * r - notch), notch / 2, R, cols[0]),
                                              ((2 * r, h - 0.08, 2 * t), 0.0, R @ G.ry(45), cols[1]),
                                              ((2 * r, h - 0.12, 2 * t), 0.0, R @ G.ry(-45), cols[1]))):
        dy = size[1] / 2 if foot else 0.0
        out.append(B.p(name, size, c + R @ (0, dy, off), Rk, col, solid=solid, **kw))
    return out


def flat(c, theta):
    """The frame of a drum's flat at heading theta (0 the front, -Z; 90 is +X): its own -Z is the
    flat's outward normal, its own X runs along the flat."""
    return CF(np.asarray(c, float), G.ry(-theta))


def swirl(B, c, r, R=None, cols=(PINK[1], WHITE), th=0.6, turns=1.15, segs=6, name="Lollipop"):
    """A swirl lollipop's disc facing -Z of R: an eight-sided round, a spiral of the second colour
    wound out from its middle (bars a little thicker than the disc, so the swirl shows both sides)."""
    R = np.eye(3) if R is None else R
    c = np.asarray(c, float)
    out = drum(B, name, c, r, th, (cols[0], shade(cols[0], -0.06)), R=R @ G.rx(90))
    pts = []
    for i in range(segs + 1):
        f = i / segs
        a = 2 * math.pi * turns * f
        rho = r * (0.12 + 0.72 * f)
        pts.append(c + R @ (rho * math.cos(a), rho * math.sin(a), 0.0))
    for i in range(segs):
        out.append(bar(B, name, pts[i], pts[i + 1], r * 0.26, cols[1], t=th + 0.16 + 0.05 * (i % 2),
                       n=R @ (0, 0, -1), over=r * 0.06))
    return out


def cane(B, base, h, heading=90.0, hook=2.2, w=1.3, cols=(RED, WHITE), bands=5, name="CandyCane", hook_segs=5,
         tilt=0.0):
    """A candy cane standing in the ground: a white shaft with red bands wound round it (blocks a
    little wider, tipped so they run slantwise), a hook of turned blocks curling over towards heading."""
    base = np.asarray(base, float)
    hd = np.array((math.sin(math.radians(heading)), 0.0, -math.cos(math.radians(heading))))
    side = np.cross(hd, (0.0, 1.0, 0.0))
    up = np.array((0.0, math.cos(math.radians(tilt)), 0.0)) + hd * math.sin(math.radians(tilt))
    Rs = G.ry(-heading) @ G.rx(-tilt)
    top = base + up * h
    out = [B.p(name, (w, h + 0.2, w), base + up * (h / 2 - 0.1), Rs, cols[1])]
    for k in range(bands):
        out.append(B.p(name, (w + 0.16, w * 0.62, w + 0.16), base + up * (h * (k + 0.55) / (bands + 0.3)),
                       Rs @ G.rx(24) @ G.rz(24), cols[0]))
    cc = top + hd * hook
    pts = []
    for i in range(hook_segs + 1):
        a = math.pi * 1.12 * i / hook_segs
        pts.append(cc - hd * hook * math.cos(a) + up * hook * math.sin(a))
    for i in range(hook_segs):
        out.append(bar(B, name, pts[i], pts[i + 1], w, cols[i % 2], t=w + (-0.08, 0.08, 0.16)[i % 3], n=side,
                       over=w * 0.32))
    return out


def ring(B, name, c, R, rad, tube, depth, cols, n=8, phase=0.0, step=0.04):
    """A ring of n blocks round the own Y of R (a doughnut, its icing): each block a chord of the
    circle; depths alternate a hair so no faces fight at the joints."""
    c = np.asarray(c, float)
    L = 2 * rad * math.tan(math.pi / n) + tube * 0.44
    out = []
    for k in range(n):
        Rk = R @ G.ry(phase + 360.0 * k / n)
        out.append(B.p(name, (L, depth + step * (k % 2), tube), c + Rk @ (0, 0, -rad), Rk, cols[k % len(cols)]))
    return out


def gumdrop(B, c, s, cols, heading=0.0, name="Gumdrop", sugar=0):
    """A gumdrop: a dome of four blocks narrowing upwards, each turned from the last and tipped a
    little; sugar crystals stuck to it."""
    c = np.asarray(c, float)
    out = []
    y = 0.0
    for k, (w, h) in enumerate(((1.0, 0.4), (0.86, 0.34), (0.64, 0.28), (0.36, 0.2))):
        out.append(B.p(name, (s * w, s * h + 0.04, s * w), c + (0, s * (y + h / 2), 0),
                       ori(3 * (-1) ** k, heading + 45 * (k % 2) + 8 * k, -2 * (-1) ** k), cols[min(k, 2)]))
        y += h
    for k in range(sugar):
        a = math.radians(heading + 70 * k + 20)
        yy = (0.2, 0.55, 0.85)[k % 3]
        rr = s * (0.5, 0.43, 0.32)[k % 3] + 0.04
        out.append(B.p(name, (0.26, 0.26, 0.26), c + (math.sin(a) * rr, s * yy, -math.cos(a) * rr),
                       ori(35, 45 + 10 * k, 0), "ffffff"))
    return out


def candle(B, base, h, col, stripe=WHITE, w=1.0, heading=20.0, name="Candle"):
    """A birthday candle: a stick with two slanted stripes, a wick and a Neon flame (it flickers and
    lights up at night)."""
    base = np.asarray(base, float)
    out = [B.p(name, (w, h + 0.1, w), base + (0, h / 2 - 0.05, 0), G.ry(heading), col)]
    for k in range(2):
        out.append(B.p(name, (w + 0.16, 0.42, w + 0.16), base + (0, h * (0.3 + 0.36 * k), 0),
                       G.ry(heading) @ G.rz(22), stripe))
    out += flame(B, base + (0, h + 0.95, 0), 1.05 * w)
    return out


def cherry(B, p, heading=0.0, stem=True, cream=True):
    """A cherry on a dollop of whipped cream."""
    p = np.asarray(p, float)
    out = []
    y = p[1]
    if cream:
        out.append(B.p("Cream", (1.7, 0.9, 1.7), p + (0, 0.42, 0), G.ry(heading + 45), ICING[0]))
        y += 0.84
    out.append(B.p("Cherry", (1.05, 1.0, 1.05), (p[0], y + 0.46, p[2]), ori(8, heading + 30, 10), CHERRY[0]))
    if stem:
        hd = np.array((math.sin(math.radians(heading + 60)), 0.0, -math.cos(math.radians(heading + 60))))
        out.append(bar(B, "Stem", (p[0], y + 0.8, p[2]), np.array((p[0], y + 1.85, p[2])) + hd * 0.45, 0.18,
                       LEAF[0]))
    return out


def sprinkle(B, pos, ang, col, d=0.24, R=None, name="Sprinkle", size=(0.34, 1.0)):
    """One sprinkle: a little bright stick lying on a face (pos is its middle on the face, the face
    facing -Z of R)."""
    R = np.eye(3) if R is None else R
    return B.p(name, (size[0], size[1], d), np.asarray(pos, float) + R @ (0, 0, -d / 2), R @ G.rz(ang), col)


# ==================================================================== the hero

def tier(B, y0, r, h, body, lid, cz, notch=0.0, lt=0.7, over=0.3):
    """One tier from y0 up: the drum (solid) and its lid of icing overhanging it. Returns (the height
    of the tier's top under the lid, the height of the lid's top)."""
    drum(B, "Tier", (0.0, y0 + h / 2, cz), r, h, body, solid=True, notch=notch)
    top = y0 + h
    drum(B, "Icing", (0.0, top - 0.06 + lt / 2, cz), r + over, lt, lid, solid=True, notch=notch)
    return top, top - 0.06 + lt


def dress(B, cz, y0, top, r, flats, drip_col, lmax, rng, wmax=1.2, drops=2):
    """Icing drips hanging from the lid down the flats and a band of sprinkles round the middle.
    flats: (heading, drips, sprinkles) each; the longest `drops` drips end in a fat drop."""
    t = r * T8
    h = top - y0
    runs = []
    for th, nd, ns in flats:
        xm = t - 0.12 - wmax / 2
        xs = np.linspace(-xm, xm, nd) if nd > 1 else np.zeros(1)
        for x in xs:
            runs.append((th, float(x + rng.uniform(-0.15, 0.15)), float(rng.uniform(0.3, 1.0)) * lmax,
                         float(rng.uniform(wmax - 0.4, wmax))))
    fat = sorted(range(len(runs)), key=lambda i: -runs[i][2])[:drops]
    for i, (th, x, L, w) in enumerate(runs):
        with B.at(flat((0.0, top - 0.06, cz), th)):
            B.p("Drip", (w, L + 0.16, 0.28), (x, -L / 2 + 0.08, -r - 0.14), None, drip_col)
            if i in fat:
                B.p("Drip", (w + 0.18, 0.62, 0.32 + 0.04 * (i % 2)), (x, -L + 0.12, -r - 0.15), None, drip_col)
    k = 0
    for th, nd, ns in flats:
        if not ns:
            continue
        with B.at(flat((0.0, y0, cz), th)):
            xm = t - 0.62
            xs = np.linspace(-xm, xm, ns) if ns > 1 else np.zeros(1)
            for x in xs:
                y = h * float(rng.uniform(0.24, 0.42))
                sprinkle(B, (float(x + rng.uniform(-0.12, 0.12)), y, -r), float(rng.uniform(0, 180)),
                         SPRINK[k % len(SPRINK)], d=0.18 + 0.04 * (k % 3))
                k += 1


def slice_cut(B, cz, y0, h, r, notch):
    """The cut faces where a slice was taken out of the front of a tier: chocolate sponge, a layer of
    cream and one of jam across each face."""
    t = r * T8
    lx0 = (r - notch) * math.sqrt(2.0) - t                 # where each side face meets the back face
    L = r - lx0
    yc = y0 + h / 2
    for sx in (-1, 1):                                     # the two slanted faces of the cut
        Rk = G.ry(45 * sx)
        with B.at(CF(np.array((0.0, yc, cz)), Rk)):
            mid = sx * (lx0 + L / 2)
            B.p("Sponge", (L - 0.1, h - 0.2, 0.12), (mid, 0.0, -t - 0.06), None, SPONGE[0])
            for j, (yy, col) in enumerate(((-h * 0.16, CREAM), (h * 0.18, JAM))):
                B.p("Filling", (L - 0.06, 0.55, 0.12 + 0.04 * j), (mid, yy, -t - 0.12 - 0.02 * j), None, col)
    zb = cz - r + notch
    wb = 2 * max(0.4, (r - notch) - math.sqrt(2.0) * t)
    B.p("Sponge", (wb + 0.3, h - 0.26, 0.12), (0.0, yc, zb - 0.06), None, SPONGE[1])
    for j, (yy, col) in enumerate(((-h * 0.16, CREAM), (h * 0.18, JAM))):
        B.p("Filling", (wb + 0.34, 0.61, 0.12 + 0.04 * j), (0.0, yc + yy, zb - 0.12 - 0.02 * j), None, col)


def topper(B, base, s=5.0):
    """The cake-topper: a potato on little legs in a party hat, cheering, a swirl lollipop held high."""
    base = np.asarray(base, float)
    for sx in (-1, 1):
        B.p("Topper", (0.95, 1.2, 0.95), base + (sx * s * 0.2, 0.55, 0.15), None, SKIN[1])
        B.p("Topper", (1.15, 0.52, 1.45), base + (sx * s * 0.2, 0.23, -0.14), None, PINKICE[0])
    c = base + (0.0, 1.0 + s / 2, 0.0)
    potato(B, c, s, SKIN, name="Topper", glints=True, cheeks="ff8aa8")
    hy = c[1] + s / 2
    for k, (w, h, col) in enumerate(((2.3, 1.1, PINKICE[0]), (1.6, 1.1, LEMON[0]), (0.9, 1.0, PINKICE[2]))):
        B.p("PartyHat", (w, h, w), (c[0] + 0.2 * k - 0.2, hy - 0.05 + 1.05 * k + h / 2, c[2] + 0.1),
            ori(0, 45 * k + 10, -8), col)
    B.p("PartyHat", (0.7, 0.7, 0.7), (c[0] + 0.45, hy + 3.4, c[2] + 0.1), ori(35, 30, 0), WHITE)
    hand_r = c + (s * 0.5, s * 0.74, -0.45)
    bar(B, "Topper", c + (s * 0.36, s * 0.05, 0.0), hand_r, 0.78, SKIN[1])
    bar(B, "Topper", c + (-s * 0.36, s * 0.05, 0.0), c + (-s * 0.52, s * 0.62, -0.55), 0.78, SKIN[1])
    bar(B, "Lollipop", hand_r - (0, 0.5, 0), hand_r + (0, 2.6, 0), 0.36, WHITE)
    swirl(B, hand_r + (0.2, 2.6 + 2.0, -0.11), 2.1, R=G.rz(-10), cols=(SKY[0], WHITE), th=0.5, segs=4, turns=0.9)


def hero(sc, parent):
    B = Build(sc, parent, "Candy", seed=301)
    rng = B.rng
    cz = 1.2
    # the board
    drum(B, "Board", (0.0, 0.0, cz), 12.6, 0.8, BOARD, solid=True, foot=True)
    # three tiers, getting lighter upwards; a slice cut out of the bottom one
    r1, h1, r2, h2, r3, h3 = 10.0, 8.0, 7.2, 7.0, 4.9, 5.6
    notch = 0.35 * r1
    t1, l1 = tier(B, 0.74, r1, h1, CHOC, ICING, cz, notch=notch)
    t2, l2 = tier(B, l1 - 0.06, r2, h2, PINK, ICING, cz)
    t3, l3 = tier(B, l2 - 0.06, r3, h3, VANILLA, PINKICE, cz)
    slice_cut(B, cz, 0.74, h1, r1, notch)
    dress(B, cz, 0.74, t1, r1, ((-90, 3, 3), (-45, 3, 3), (45, 3, 3), (90, 3, 3)), ICING[0], h1 * 0.42, rng,
          drops=3)
    dress(B, cz, l1 - 0.06, t2, r2, ((-90, 2, 2), (-45, 3, 2), (0, 3, 2), (45, 3, 2), (90, 2, 2)), ICING[0],
          h2 * 0.42, rng, drops=3)
    dress(B, cz, l2 - 0.06, t3, r3, ((-90, 2, 0), (-45, 2, 2), (0, 2, 2), (45, 2, 2), (90, 2, 0)), PINKICE[0],
          h3 * 0.42, rng, wmax=1.0, drops=2)
    # cherries on cream along the rims
    for th in (-90, -45, 45, 90):
        ro = (r1 + 0.3 + r2 + 0.3) / 2
        cherry(B, (math.sin(math.radians(th)) * ro, l1, cz - math.cos(math.radians(th)) * ro), heading=th)
    for th in (-90, -45, 0, 45, 90):
        ro = (r2 + 0.3 + r3 + 0.3) / 2
        cherry(B, (math.sin(math.radians(th)) * ro, l2, cz - math.cos(math.radians(th)) * ro), heading=th,
               stem=th == 0)
    # candles round the topper
    for k, (th, col) in enumerate(((-100, SKY[0]), (100, LEMON[0]), (-150, MINT[0]), (150, GRAPE[0]))):
        rr = r3 - 1.0 - 0.15 * (k // 2)
        candle(B, (math.sin(math.radians(th)) * rr, l3 - 0.04, cz - math.cos(math.radians(th)) * rr),
               5.0 - 0.4 * (k % 2) + 0.6 * (k // 2), col, w=1.3, heading=15 * k)
    topper(B, (0.0, l3 - 0.04, cz - 0.2), 5.0)
    # a giant candy cane and a giant lollipop either side, gumdrops at the foot
    cane(B, (-19.6, 0.0, cz + 2.5), 17.0, heading=90.0, hook=2.6, w=1.6, bands=5)
    lx = 17.6
    bar(B, "Lollipop", (lx, 0.0, cz + 2.8), (lx, 15.0, cz + 2.8), 0.8, WHITE)
    swirl(B, (lx, 18.6, cz + 2.8), 4.0, R=G.rz(10), cols=(PINK[1], WHITE), th=0.8, segs=6)
    B.p("Ribbon", (1.8, 0.8, 1.0), (lx, 14.2, cz + 2.4), G.rz(30), PINKICE[1])
    B.p("Ribbon", (1.8, 0.8, 1.04), (lx, 14.2, cz + 2.4), G.rz(-30), PINKICE[2])
    for k, (x, z, s, cols) in enumerate(((-14.4, cz - 9.6, 2.4, MINT), (14.6, cz - 8.6, 2.8, LEMON),
                                          (-17.0, cz - 5.0, 1.9, GRAPE))):
        gumdrop(B, (x, 0.0, z), s, cols, heading=25 * k)
    return B.finish()


# ==================================================================== props

def p_cane(sc, parent):
    B = Build(sc, parent, "CandyCane", seed=311)
    cane(B, (0.0, 0.0, 0.0), 9.0, heading=60.0, hook=1.5, w=1.0, bands=5)
    cane(B, (2.6, 0.0, 1.0), 5.6, heading=-120.0, hook=1.0, w=0.8, bands=3, cols=("3fbf6a", WHITE), tilt=8.0)
    B.p("Sugar", (3.2, 0.36, 2.6), (0.9, 0.18, 0.4), G.ry(15), "fff4fa")
    B.p("Sugar", (2.2, 0.3, 2.0), (1.4, 0.15, 1.3), G.ry(50), "ffe4f0")
    return B.finish()


def p_lollipops(sc, parent):
    B = Build(sc, parent, "LollipopTree", seed=312)
    gumdrop(B, (0.0, 0.0, 0.0), 2.6, ("ff9ad0", "ff86c4", "ffb4dc"))
    for k, (x, z, h, r, cols, rz, hd) in enumerate(((0.0, 0.1, 8.4, 2.6, (PINK[1], WHITE), 6, 0),
                                                    (0.5, 0.3, 5.6, 1.8, (SKY[0], WHITE), -24, 40),
                                                    (-0.5, 0.2, 4.4, 1.6, (LEMON[1], "ff8a3d"), 26, -35))):
        R = G.ry(hd) @ G.rz(rz)
        axis = R @ (0.0, 1.0, 0.0)
        base = np.array((x, 1.2, z))
        bar(B, "Stick", base, base + axis * h, 0.4, WHITE)
        swirl(B, base + axis * (h + r * 0.95), r, R=R, cols=cols, th=0.5, segs=5)
    return B.finish()


def p_doughnut(sc, parent):
    B = Build(sc, parent, "Doughnut", seed=313)
    rad, tube = 2.6, 1.8
    c = np.array((0.0, rad + tube / 2, 0.0))
    R = G.rx(90)
    ring(B, "Doughnut", c, R, rad, tube, 1.9, DOUGH)
    ring(B, "Icing", c + (0, 0, -1.0), R, rad, tube * 1.04, 0.3, (PINKICE[0], PINKICE[2]))
    rng = B.rng
    for k in range(11):
        a = 2 * math.pi * k / 11 + 0.2
        rr = rad + (0.45 if k % 2 else -0.4)
        sprinkle(B, c + (math.cos(a) * rr, math.sin(a) * rr, -1.16), float(rng.uniform(0, 180)), SPRINK[k % 6],
                 d=0.16 + 0.04 * (k % 3), size=(0.28, 0.8))
    for k, (x, z) in enumerate(((-2.4, -1.6), (2.2, -1.4), (0.6, -2.3))):
        B.p("Sprinkle", (0.3, 0.24, 0.85), (x, 0.12, z), G.ry(40 * k + 20), SPRINK[(k + 2) % 6])
    return B.finish()


def p_gumdrops(sc, parent):
    B = Build(sc, parent, "Gumdrops", seed=314)
    gumdrop(B, (0.0, 0.0, 0.0), 2.8, ("ff4d6d", "e83a5a", "ff7088"), heading=10, sugar=3)
    gumdrop(B, (2.6, 0.0, 0.8), 2.1, MINT, heading=40, sugar=2)
    gumdrop(B, (-2.3, 0.0, 1.0), 1.8, LEMON, heading=-20, sugar=2)
    gumdrop(B, (0.7, 0.0, -2.3), 1.5, GRAPE, heading=65, sugar=1)
    return B.finish()


def p_cupcake(sc, parent):
    B = Build(sc, parent, "Cupcake", seed=315)
    drum(B, "Wrapper", (0.0, 0.0, 0.0), 2.0, 2.6, ("4fc8ff", "ffffff"), foot=True)
    drum(B, "Wrapper", (0.0, 2.55, 0.0), 2.2, 0.4, ("3bb4f0", "e8f6ff"))
    drum(B, "Cake", (0.0, 3.1, 0.0), 2.35, 0.9, ("c8844a", "b87440"))
    y = 3.5
    tops = []
    for k, (w, h) in enumerate(((4.0, 1.1), (3.1, 1.0), (2.2, 0.9), (1.3, 0.8))):
        B.p("Frosting", (w, h, w), (0.08 * k, y + h / 2, -0.05 * k), ori(0, 45 * k + 10, 0),
            (PINK[0], PINK[2], PINK[1], PINK[2])[k])
        tops.append((y + h, w))
        y += h - 0.08
    rng = B.rng
    for k in range(8):
        a = math.radians(45 * k + 15)
        yt, w = tops[k % 2]
        rr = (w + tops[k % 2 + 1][1]) / 4 + 0.05
        B.p("Sprinkle", (0.28, 0.24, 0.8), (math.sin(a) * rr + 0.08 * (k % 2), yt + 0.1, -math.cos(a) * rr),
            ori(0, float(rng.uniform(0, 180)), 0), SPRINK[k % 6])
    cherry(B, (0.1, y - 0.1, 0.0), heading=20, cream=False)
    return B.finish()


def p_fence(sc, parent):
    B = Build(sc, parent, "GingerbreadFence", seed=316)
    for k, x in enumerate((-4.0, 0.0, 4.0)):
        B.p("Post", (1.0, 3.8, 1.0), (x, 1.9, 0.0), None, GINGER[0])
        B.p("Post", (1.2, 0.36, 1.2), (x, 3.9, 0.0), None, ICING[0])
        gumdrop(B, (x, 4.0, 0.0), 1.1, (("ff4d6d", "e83a5a", "ff7088"), MINT, LEMON)[k], heading=15 * k)
    for k, y in enumerate((1.0, 2.7)):
        B.p("Rail", (8.0, 0.5, 0.5 + 0.04 * k), (0.0, y, 0.12), None, GINGER[1 + k % 2])
    for bay in (-2.0, 2.0):
        for j, dx in enumerate((-0.9, 0.9)):
            x = bay + dx
            B.p("Picket", (0.9, 2.8, 0.36), (x, 1.5, -0.24), None, GINGER[2 * (j % 2)])
            B.p("Picket", (0.64, 0.64, 0.4 + 0.04 * j), (x, 2.9, -0.24), G.rz(45), GINGER[2 * (j % 2)])
            B.p("Icing", (0.18, 1.0, 0.12), (x, 1.9, -0.47), G.rz(55 * (-1) ** j), ICING[0])
            B.p("Icing", (0.3, 0.3, 0.12), (x, 0.9, -0.47), None, ICING[0])
    return B.finish()


def p_icecream(sc, parent):
    B = Build(sc, parent, "IceCreamCone", seed=317)
    B.p("Puddle", (2.8, 0.14, 2.2), (0.3, 0.07, -0.2), G.ry(20), PINK[2])
    y = 0.0
    for k, (w, h) in enumerate(((0.7, 1.4), (1.3, 1.5), (1.9, 1.5), (2.5, 1.5), (3.1, 1.3))):
        B.p("Cone", (w, h + 0.08, w), (0.0, y + h / 2, 0.0), G.ry(45 * (k % 2) + 5 * k), WAFER[k % 2])
        y += h
    B.p("Cone", (3.4, 0.4, 3.4), (0.0, y + 0.1, 0.0), G.ry(22.5), WAFER[2])
    y += 0.2
    round3(B, "Scoop", (0.0, y + 1.25, 0.0), 3.6, 2.6, 3.4, (PINK[0], PINK[1], PINK[2]))
    round3(B, "Scoop", (0.15, y + 3.3, 0.1), 2.9, 2.2, 2.8, MINT, R=G.ry(30))
    for k, (x, z, L) in enumerate(((-1.0, -1.72, 1.2), (0.7, -1.72, 0.8))):
        B.p("Drip", (0.6, L, 0.3), (x, y + 0.35 - L / 2 + 0.3, z - 0.02 * k), None, PINK[1])
    B.p("Wafer", (0.5, 2.2, 1.2), (1.0, y + 4.6, 0.3), ori(0, 20, -24), WAFER[2])
    cherry(B, (0.1, y + 4.3, 0.1), heading=40, cream=False)
    return B.finish()


def sweet(B, c, s, cols, heading=0.0, name="Sweet"):
    """A wrapped sweet lying on the ground: a round body along its own X, stripes round it, the
    wrapper twisted at both ends and fanned out."""
    c = np.asarray(c, float)
    R = G.ry(heading)
    out = drum(B, name, c, s * 0.5, s * 1.25, (cols[0], cols[1]), R=R @ G.rz(90))
    for sx in (-1, 1):
        out.append(B.p(name, (s * 0.36, s * 0.34, s * 0.34), c + R @ (sx * s * 0.74, 0, 0), R @ G.rx(45), cols[1]))
        for j in (-1, 1):
            Rf = R @ G.rz(sx * j * 24) @ G.rx(12 * j)
            out.append(B.p(name, (s * 0.62, s * 0.86, 0.14 + 0.04 * (j > 0)), c + R @ (sx * s * 1.05, j * s * 0.12, 0),
                           Rf, cols[2 if j > 0 else 0]))
    return out


def p_sweets(sc, parent):
    B = Build(sc, parent, "WrappedSweets", seed=318)
    sweet(B, (0.0, 0.86, 0.0), 1.7, (PINKICE[0], PINKICE[1], "fff4fa"), heading=15)
    sweet(B, (0.6, 0.66, -2.3), 1.3, (SKY[0], SKY[1], LEMON[0]), heading=-40)
    return B.finish()


def bar_of_chocolate(B, c, heading, cols, wrap=None, name="Chocolate"):
    """A chocolate bar lying flat: a slab and two rows of raised squares; a wrapper over one end."""
    c = np.asarray(c, float)
    R = G.ry(heading)
    out = [B.p(name, (6.0, 0.8, 3.0), c + R @ (0, 0.4, 0), R, cols[0])]
    for i in range(3):
        for j in range(2):
            if wrap and i == 2:
                continue
            out.append(B.p(name, (1.7, 0.3, 1.25), c + R @ (-1.9 + 1.9 * i, 0.94, -0.7 + 1.4 * j), R,
                           cols[1 + (i + j) % 2]))
    if wrap:
        out.append(B.p("Wrapper", (2.6, 1.3, 3.3), c + R @ (2.0, 0.6, 0), R, wrap[0]))
        out.append(B.p("Wrapper", (2.64, 0.5, 3.34), c + R @ (2.0, 0.6, 0), R, wrap[1]))
        out.append(B.p("Wrapper", (0.7, 0.16, 3.2), c + R @ (0.55, 1.3, 0), R @ G.rz(-30), "dfe4ee"))
    return out


def p_chocolate(sc, parent):
    B = Build(sc, parent, "ChocolateStack", seed=319)
    bar_of_chocolate(B, (0.0, 0.0, 0.0), 0.0, ("5a2e1a", "6a3720", "7a4228"))
    bar_of_chocolate(B, (0.3, 1.06, 0.1), 32.0, ("7a4228", "8a4e2e", "6a3720"))
    bar_of_chocolate(B, (-0.2, 2.12, 0.0), -18.0, ("f0e2c8", "fff4e0", "e8d6b8"), wrap=(RED, "f5c518"))
    return B.finish()


def p_mushroom(sc, parent):
    B = Build(sc, parent, "CandyMushroom", seed=320)
    for k, (x, z, h, s, cols) in enumerate(((0.0, 0.0, 2.6, 3.4, (PINK[1], PINK[0], PINK[2])),
                                             (2.4, 0.9, 1.5, 2.1, (MINT[1], MINT[0], MINT[2])))):
        R = ori(5 * (-1) ** k, 20 * k, 4)
        B.p("Stem", (0.9 * s / 3.4 + 0.2, h, 0.9 * s / 3.4 + 0.2), (x, h / 2, z), R, "fff1e4")
        B.p("Stem", (0.8 * s / 3.4 + 0.2, h * 0.9, 0.8 * s / 3.4 + 0.2), (x, h / 2, z), R @ G.ry(45), "f8e6d4")
        c = np.array((x, h + s * 0.2, z))
        round3(B, "Cap", c, s, s * 0.52, s, cols, R=R, lid=(s * 0.6, s * 0.16, s * 0.6))
        for j in range(4):
            a = math.radians(90 * j + 30 * k + 20)
            p = c + R @ (math.sin(a) * s * 0.36, s * 0.27, -math.cos(a) * s * 0.36)
            B.p("Dot", (s * 0.18, s * 0.08, s * 0.18), p, R @ G.ry(15 * j), "ffffff")
    return B.finish()


AREA = register(Area("Candy", "Candy Crops", hero, [
    (p_cane, prop_attrs(6, 0.85, 1.3, "Edge", False)),
    (p_lollipops, prop_attrs(6, 0.85, 1.25, "Side", False)),
    (p_doughnut, prop_attrs(4, 0.9, 1.25, "Side", True)),
    (p_gumdrops, prop_attrs(10, 0.8, 1.4, "Any", False)),
    (p_cupcake, prop_attrs(4, 0.9, 1.25, "Side", True)),
    (p_fence, prop_attrs(5, 0.9, 1.1, "Edge", True)),
    (p_icecream, prop_attrs(4, 0.9, 1.2, "Side", True)),
    (p_sweets, prop_attrs(10, 0.8, 1.3, "Any", False)),
    (p_chocolate, prop_attrs(4, 0.9, 1.2, "Side", True)),
    (p_mushroom, prop_attrs(8, 0.8, 1.3, "Any", False)),
], ground="fcb0ce"))
