"""Brick-toy props, each a list of (part, colour, Geo) in its own frame: ground at y = 0, the
front towards -Z. Built from stacked bevelled blocks like the photos' layered eggs and swan:
chunky, flat colours, nothing thinner than 0.2."""
import math

import numpy as np

import spsgeo as G
from spsgeo import T, RX, RY, RZ, S

from .geo import bevel_box, ccyl, cfrustum, rod, bent, irregular

# ---------------------------------------------------------------- shared colours
WOOD = (176, 112, 62)
WOOD_DARK = (122, 76, 42)
WOOD_LIGHT = (214, 160, 102)
LEAF = (70, 178, 58)
LEAF_DARK = (46, 140, 48)
LEAF_LIGHT = (120, 210, 70)
RED = (226, 54, 46)
WHITE = (248, 246, 240)
YELLOW = (255, 206, 46)
ORANGE = (250, 140, 40)
PINK = (250, 130, 170)
PURPLE = (160, 90, 220)
BLUE = (70, 140, 240)
CYAN = (60, 210, 230)
STONE = (150, 150, 158)
STONE_DARK = (108, 108, 118)
POTATO = (206, 160, 92)
POTATO_DARK = (160, 116, 62)
SOIL = (120, 80, 50)
BLACK = (34, 32, 36)
HAY = (240, 204, 92)
HAY_DARK = (206, 164, 62)
METAL = (170, 176, 186)
TERRACOTTA = (214, 112, 70)
SAND = (240, 210, 130)
BONE = (246, 240, 222)
CACTUS = (64, 170, 70)
CACTUS_DARK = (40, 130, 56)


def box(w, h, d, c=(0, 0, 0), b=0.15):
    return bevel_box(w, h, d, b, c)


def stack(levels, b=0.15, round_=False, n=10):
    """Stacked layers [(width, depth, y0, y1)] centred on the Y axis: the layered-egg look."""
    g = G.Geo()
    for (w, d, y0, y1) in levels:
        if round_:
            g.add(ccyl(w / 2, y1 - y0, n, "y", (0, (y0 + y1) / 2, 0), b).xf(S(1, 1, d / w)))
        else:
            g.add(bevel_box(w, y1 - y0, d, b, (0, (y0 + y1) / 2, 0)))
    return g


def blob_stack(r, h, layers=5, y0=0.0, squash=1.0, round_=False):
    """A layered ball (r wide, h tall) from `layers` slabs: a brick-built sphere."""
    lv = []
    for k in range(layers):
        a0, a1 = -1 + 2 * k / layers, -1 + 2 * (k + 1) / layers
        am = (a0 + a1) / 2
        w = 2 * r * math.sqrt(max(0.05, 1 - am * am))
        lv.append((w, w * squash, y0 + (a0 + 1) / 2 * h, y0 + (a1 + 1) / 2 * h))
    return stack(lv, round_=round_)


# ---------------------------------------------------------------- plants

def tree_round(h=14.0, r=5.0, trunk=WOOD, leaf=LEAF, fruit=None, rng=None):
    """A toy tree: a square trunk and a layered round crown; fruit = colour of a few apples."""
    rng = rng or np.random.default_rng(1)
    t = box(1.6, h * 0.5 + 1, 1.6, (0, (h * 0.5 + 1) / 2, 0))
    crown = blob_stack(r, r * 1.6, 5, h - r * 1.6)
    out = [("Trunk", trunk, t), ("Leaves", leaf, crown)]
    if fruit:
        f = G.Geo()
        for k in range(7):
            a = rng.uniform(0, math.tau)
            y = h - r * 0.8 + rng.uniform(-r * 0.5, r * 0.5)
            rr = r * math.sqrt(max(0.1, 1 - ((y - (h - r * 0.8)) / (r * 0.8)) ** 2)) * 0.98
            f.add(box(0.9, 0.9, 0.9, (rr * math.cos(a), y, rr * math.sin(a)), 0.2))
        out.append(("Fruit", fruit, f))
    return out


def pine(h=16.0, r=5.0, trunk=WOOD_DARK, leaf=(40, 140, 80), snow=None):
    t = box(1.4, h * 0.3, 1.4, (0, h * 0.15, 0))
    tiers = G.Geo()
    sn = G.Geo()
    n = 4
    for k in range(n):
        y0 = h * 0.2 + k * (h * 0.75 / n)
        w = 2 * r * (1 - k / (n + 0.6))
        tiers.add(bevel_box(w, h * 0.75 / n * 0.9, w, 0.2, (0, y0 + h * 0.75 / n * 0.45, 0)).xf(G.M(G.ry(45 * (k % 2)))))
        if snow:
            sn.add(bevel_box(w * 0.82, 0.5, w * 0.82, 0.15, (0, y0 + h * 0.75 / n * 0.9 + 0.1, 0)).xf(
                G.M(G.ry(45 * (k % 2)))))
    tiers.add(box(1.6, 1.6, 1.6, (0, h - 0.4, 0)))
    out = [("Trunk", trunk, t), ("Needles", leaf, tiers)]
    if snow:
        out.append(("Snow", snow, sn))
    return out


def palm(h=16.0, lean=8.0, trunk=(196, 150, 96), leaf=(60, 180, 70), coco=(130, 84, 46)):
    g = G.Geo()
    seg = 6
    pts = []
    for k in range(seg + 1):
        t_ = k / seg
        pts.append((math.sin(t_ * 1.4) * lean * 0.5, t_ * h, 0.0))
    for k in range(seg):
        a, b = np.array(pts[k]), np.array(pts[k + 1])
        c = (a + b) / 2
        w = 1.6 - 0.3 * k / seg
        g.add(bevel_box(w, h / seg * 0.95, w, 0.15, (0, 0, 0)).xf(T(*c) @ RZ(-math.degrees(math.atan2(b[0] - a[0], b[1] - a[1])))))
    top = np.array(pts[-1])
    fr = G.Geo()
    for k in range(6):
        a = k * 60 + 15
        leafg = bevel_box(1.6, 0.4, 7.0, 0.15, (0, 0, 3.4))
        fr.add(leafg.xf(T(*top) @ RY(a) @ RX(22)))
    co = G.Geo()
    for k in range(3):
        a = math.radians(k * 120)
        co.add(box(1.0, 1.0, 1.0, (top[0] + 0.8 * math.cos(a), top[1] - 0.6, 0.8 * math.sin(a)), 0.25))
    return [("Trunk", trunk, g), ("Fronds", leaf, fr), ("Coconuts", coco, co)]


def hedge(length=10.0, h=3.2, d=3.0, color=LEAF_DARK):
    g = G.Geo()
    n = max(1, int(round(length / 3.2)))
    w = length / n
    for k in range(n):
        x = -length / 2 + w * (k + 0.5)
        hh = h * (0.92 + 0.08 * ((k * 37) % 5) / 4)
        g.add(bevel_box(w + 0.05, hh, d, 0.3, (x, hh / 2, 0)))
    return [("Hedge", color, g)]


def bush(r=2.2, color=LEAF, rng=None):
    rng = rng or np.random.default_rng(3)
    g = G.Geo()
    for k in range(3):
        a = k * 2.1
        rr = r * (0.7 + 0.3 * rng.random())
        g.add(blob_stack(rr, rr * 1.4, 3, 0.0).xf(T(math.cos(a) * r * 0.5, 0, math.sin(a) * r * 0.5)))
    return [("Bush", color, g)]


def flower_clump(rng, n=5, petals=(RED, YELLOW, PINK, WHITE, PURPLE)):
    """A few toy flowers: a green stem block and a 4-petal head with a yellow middle."""
    stems, heads, mids = G.Geo(), G.Geo(), G.Geo()
    out = {}
    for k in range(n):
        x, z = rng.uniform(-1.6, 1.6), rng.uniform(-1.6, 1.6)
        h = rng.uniform(0.9, 1.8)
        stems.add(box(0.3, h, 0.3, (x, h / 2, z), 0.1))
        col = petals[int(rng.integers(0, len(petals)))]
        hd = G.Geo()
        for (dx, dz) in ((0.4, 0), (-0.4, 0), (0, 0.4), (0, -0.4)):
            hd.add(box(0.5, 0.3, 0.5, (x + dx, h + 0.1, z + dz), 0.1))
        out.setdefault(col, G.Geo()).add(hd)
        mids.add(box(0.4, 0.4, 0.4, (x, h + 0.2, z), 0.1))
    parts = [("Stems", LEAF_DARK, stems), ("Middles", YELLOW, mids)]
    for col, g in out.items():
        parts.append(("Petals", col, g))
    return parts


def reeds(rng, n=3, color=(52, 160, 70), h=(3.0, 6.0)):
    """Tall square reeds standing in a little cyan base (the photos' green sticks)."""
    g = G.Geo()
    for k in range(n):
        x, z = rng.uniform(-0.8, 0.8), rng.uniform(-0.8, 0.8)
        hh = rng.uniform(*h)
        g.add(box(0.5, hh, 0.5, (x, hh / 2, z), 0.12).xf(T(x, 0, z) @ RZ(rng.uniform(-8, 8)) @ T(-x, 0, -z)))
    base = box(3.0, 0.3, 1.6, (0, 0.15, 0), 0.1)
    return [("Reeds", color, g), ("ReedBase", (60, 190, 230), base)]


def cactus(h=6.0, arms=2, rng=None):
    rng = rng or np.random.default_rng(5)
    g = G.Geo()
    g.add(bevel_box(1.6, h, 1.6, 0.3, (0, h / 2, 0)))
    for k in range(arms):
        sx = 1 if k % 2 == 0 else -1
        y = h * rng.uniform(0.35, 0.6)
        ln = rng.uniform(1.2, 1.8)
        up = rng.uniform(1.4, 2.4)
        g.add(bevel_box(ln, 1.1, 1.1, 0.25, (sx * (0.8 + ln / 2), y, 0)))
        g.add(bevel_box(1.1, up, 1.1, 0.25, (sx * (0.8 + ln - 0.3), y + up / 2, 0)))
    sp = G.Geo()
    for k in range(6):
        sp.add(box(0.2, 0.2, 0.5, (rng.choice((-0.9, 0.9)), rng.uniform(1.0, h - 0.6), rng.uniform(-0.5, 0.5)), 0.05))
    return [("Cactus", CACTUS, g), ("Flower", PINK, box(0.8, 0.5, 0.8, (0, h + 0.2, 0), 0.15))]


def rock(rng, r=2.0, color=STONE, flat=0.7):
    g = G.Geo()
    for k in range(2):
        rr = r * (1 - 0.3 * k)
        g.add(bevel_box(rr * 2, rr * flat * 1.4, rr * 1.7, 0.3, (rng.uniform(-0.3, 0.3) * k, rr * flat * 0.7 + k * r * 0.5,
                                                               0)).xf(G.M(G.ry(rng.uniform(0, 90)))))
    return [("Rock", color, g)]


# ---------------------------------------------------------------- farm things

def potato_geo(l=2.0, w=1.4, h=1.2, eyes=True):
    """A potato from layered blocks, long along X; its eyes (little dents shown as dark bumps)."""
    lv = []
    n = 5
    for k in range(n):
        a0, a1 = -1 + 2 * k / n, -1 + 2 * (k + 1) / n
        am = (a0 + a1) / 2
        f = math.sqrt(max(0.15, 1 - am * am))
        lv.append((l * (0.82 + 0.18 * f), w * f, (a0 + 1) / 2 * h, (a1 + 1) / 2 * h))
    g = G.Geo()
    for (ll, ww, y0, y1) in lv:
        g.add(bevel_box(ll * 0.9, y1 - y0, ww, min(0.2, ww * 0.3), (0, (y0 + y1) / 2, 0)))
        g.add(bevel_box(ll, (y1 - y0) * 0.8, ww * 0.75, min(0.2, ww * 0.25), (0, (y0 + y1) / 2, 0)))
    e = G.Geo()
    if eyes:
        for (x, y, z) in ((-0.4 * l, 0.6 * h, -0.45 * w), (0.15 * l, 0.75 * h, -0.42 * w), (0.3 * l, 0.4 * h, 0.4 * w)):
            e.add(box(0.2, 0.2, 0.2, (x, y, z), 0.05))
    return g, e


def crate(potatoes=True, rng=None, size=3.0):
    rng = rng or np.random.default_rng(7)
    s = size
    g = G.Geo()
    for y in (0.35, s * 0.45, s * 0.78):
        g.add(bevel_box(s, 0.6, s, 0.1, (0, y, 0)))
    for (x, z) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        g.add(bevel_box(0.5, s * 0.95, 0.5, 0.1, (x * (s / 2 - 0.25), s * 0.475, z * (s / 2 - 0.25))))
    inner = bevel_box(s - 0.5, s * 0.85, s - 0.5, 0.1, (0, s * 0.45, 0))
    out = [("Crate", WOOD, g), ("CrateInside", WOOD_DARK, inner)]
    if potatoes:
        p = G.Geo()
        for k in range(5):
            pg, _ = potato_geo(1.2, 0.85, 0.7, eyes=False)
            p.add(pg.xf(T(rng.uniform(-0.6, 0.6), s * 0.85, rng.uniform(-0.6, 0.6)) @ RY(rng.uniform(0, 180))))
        out.append(("Potatoes", POTATO, p))
    return out


def hay_bale(l=4.0, w=2.6, h=2.4):
    g = bevel_box(l, h, w, 0.25, (0, h / 2, 0))
    bands = G.Geo()
    for x in (-l * 0.25, l * 0.25):
        bands.add(bevel_box(0.3, h + 0.1, w + 0.1, 0.08, (x, h / 2, 0)))
    return [("Hay", HAY, g), ("HayBand", HAY_DARK, bands)]


def lamp_post(h=10.0, pole=BLACK, glass=(255, 236, 160)):
    """A park lamp: the pole and arm, and the glowing lantern head (part Bulb, Neon)."""
    g = G.Geo()
    g.add(bevel_box(1.4, 0.8, 1.4, 0.15, (0, 0.4, 0)))
    g.add(bevel_box(0.6, h, 0.6, 0.12, (0, h / 2, 0)))
    g.add(bevel_box(1.6, 0.5, 1.6, 0.12, (0, h + 0.25, 0)))
    g.add(bevel_box(1.2, 0.4, 1.2, 0.12, (0, h + 2.3, 0)))
    bulb = bevel_box(1.0, 1.6, 1.0, 0.15, (0, h + 1.3, 0))
    return [("Lamp", pole, g), ("Bulb", glass, bulb, "Neon")]


def fence_run(length, h=3.0, color=WOOD, x_brace=True):
    """A low X-braced farm fence along X (decoration)."""
    g = G.Geo()
    n = max(1, int(round(length / 6.0)))
    step = length / n
    for k in range(n + 1):
        x = -length / 2 + k * step
        g.add(bevel_box(0.6, h, 0.6, 0.12, (x, h / 2, 0)))
    g.add(bevel_box(length, 0.4, 0.3, 0.1, (0, h * 0.85, 0)))
    g.add(bevel_box(length, 0.4, 0.3, 0.1, (0, h * 0.3, 0)))
    if x_brace:
        for k in range(n):
            x = -length / 2 + (k + 0.5) * step
            ang = math.degrees(math.atan2(h * 0.55, step))
            ln = math.hypot(step, h * 0.55) - 0.3
            for sg in (-1, 1):
                g.add(bevel_box(ln, 0.3, 0.25, 0.08, (0, 0, 0)).xf(T(x, h * 0.575, 0) @ RZ(sg * ang)))
    return [("Fence", color, g)]


def bench(l=5.0):
    g = G.Geo()
    g.add(bevel_box(l, 0.4, 1.4, 0.1, (0, 1.6, 0)))
    g.add(bevel_box(l, 1.0, 0.3, 0.1, (0, 2.6, 0.6)))
    for x in (-l / 2 + 0.5, l / 2 - 0.5):
        g.add(bevel_box(0.5, 1.4, 1.2, 0.1, (x, 0.7, 0)))
    return [("Bench", WOOD, g)]


def barrel(h=3.0, r=1.2, color=WOOD, band=BLACK):
    g = cfrustum(r * 0.9, r * 0.9, h, 10, "y", (0, h / 2, 0), 0.15)
    g.add(ccyl(r, h * 0.5, 10, "y", (0, h / 2, 0), 0.15))
    bands = G.Geo()
    for y in (h * 0.2, h * 0.8):
        bands.add(ccyl(r * 0.96, 0.25, 10, "y", (0, y, 0), 0.05))
    return [("Barrel", color, g), ("Bands", band, bands)]


def flower_bed(l=8.0, w=3.0, rng=None):
    rng = rng or np.random.default_rng(11)
    border = G.Geo()
    for (x, z, sx, sz) in ((0, -w / 2, l, 0.5), (0, w / 2, l, 0.5), (-l / 2, 0, 0.5, w), (l / 2, 0, 0.5, w)):
        border.add(bevel_box(sx, 0.8, sz, 0.1, (x, 0.4, z)))
    soil = bevel_box(l - 0.4, 0.5, w - 0.4, 0.1, (0, 0.3, 0))
    out = [("BedBorder", WOOD_LIGHT, border), ("BedSoil", SOIL, soil)]
    for k in range(int(l / 2.5)):
        x = -l / 2 + 1.4 + k * 2.5
        for p in flower_clump(rng, 2):
            out.append((p[0], p[1], p[2].xf(T(x, 0.5, 0) @ S(0.6, 0.8, 0.5))))
    return out
