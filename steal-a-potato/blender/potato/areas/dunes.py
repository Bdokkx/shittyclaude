"""Area 2, Sandy Dunes: sand yellow, tan sandstone walls. Cacti, bones, clay pots, palm trees, a
dry well, low dune steps along the east wall (1 stud each, solid). Hero: a stepped pyramid
against the west wall with a big potato carved on its lane face."""
import math

import numpy as np

import spsgeo as G
from spsgeo import CF, T, RX, RY, RZ, S

from .. import props as P
from ..geo import bevel_box, ccyl, cfrustum
from ..kit import darker, lighter
from .common import Area

SANDSTONE = (230, 184, 112)
SANDSTONE_DARK = (204, 150, 88)
DUNE = (232, 194, 108)
HERO = (-41.0, 112.0)


def build(k, n, folder, markers, rng):
    a = Area(k, n, folder, markers, rng)
    pyramid(a)
    for (u0, u1, x0) in ((24.0, 74.0, 40.0), (150.0, 200.0, 42.0)):
        dune_steps(a, u0, u1, x0)
    for (x, u) in ((46, 98), (-46, 26), (52, 128), (-48, 186), (36, 210), (30, 18)):
        a.put("Palms", P.palm(15.0 + rng.uniform(-2, 3), rng.uniform(5, 9)), x, u, rng.uniform(0, 360), r=4.0)
        a.tuck(x + (9 if x < 0 else -9), u - 3)
    dry_well(a, -36.0, 166.0)
    bones(a, 33.0, 84.0)
    for (x, u) in ((-30, 60), (34, 140), (-28, 206)):
        pots(a, x, u)
    for (x, u) in a.scatter(12, 2.6):
        a.put("Cacti", P.cactus(rng.uniform(4.5, 7.5), int(rng.integers(0, 3)), rng), x, u, rng.uniform(0, 90), r=2.4)
    for (x, u) in a.scatter(6, 2.4):
        a.put("Rocks", P.rock(rng, rng.uniform(1.4, 2.4), SANDSTONE_DARK), x, u, r=2.4)
    for (x, u) in a.scatter(4, 1.6, lane_too=4):
        a.put("Bones", small_bones(rng), x, u, rng.uniform(0, 180), r=1.4)
    a.flush()
    return a


def pyramid(a):
    """Five solid stepped tiers (4 high each), a sandstone band on every step, and a potato
    carved on the lane (east) face: a raised potato with eyes and a smile, with sprouts."""
    k = a.k
    x, u = HERO
    zc = a.z(u)
    m = k.sc.model(a.f, "Pyramid")
    tiers = []
    widths = (34.0, 28.0, 22.0, 16.0, 10.0)
    for i, w in enumerate(widths):
        y0 = i * 4.0
        col = SANDSTONE if i % 2 == 0 else lighter(SANDSTONE, 0.1)
        tiers.append(k.solid(m, "Tier", (w, 4.0, w), CF((x, y0 + 2.0, zc)), col, checker=True))
    m.p["primary"] = tiers[0]
    cap = G.Geo()
    cap.add(bevel_box(6.0, 2.0, 6.0, 0.25, (0, 21.0, 0)))
    cap.add(bevel_box(3.0, 2.0, 3.0, 0.25, (0, 23.0, 0)))
    k.mesh(m, "Capstone", "A2_PyramidCap", cap, CF((x, 0.0, zc)), (250, 210, 80))
    band = G.Geo()
    for i, w in enumerate(widths):
        band.add(bevel_box(w + 0.4, 0.6, w + 0.4, 0.1, (0, i * 4.0 + 3.7, 0)))
    k.mesh(m, "Bands", "A2_PyramidBands", band, CF((x, 0.0, zc)), SANDSTONE_DARK)
    # the carving: a thick potato slab standing on the first step, against the third tier's
    # east face, looking at the lane (+X)
    fr = CF((x + 13.0, 4.0, zc), G.ry(-90))       # local -Z = +X, local X = the lane's direction
    pg, _ = P.potato_geo(12.0, 3.0, 7.0, eyes=False)
    k.mesh(m, "Carving", "A2_PyramidPotato", pg, fr, (196, 140, 76))
    face = G.Geo()
    for sx in (-1, 1):
        face.add(bevel_box(1.4, 1.4, 0.6, 0.2, (sx * 2.2, 4.7, -1.45)))
    for i in range(7):
        fx = -2.4 + i * 0.8
        face.add(bevel_box(0.6, 0.5, 0.6, 0.12, (fx, 2.9 - 0.7 * (1 - (fx / 2.4) ** 2), -1.45)))
    k.mesh(m, "CarvingFace", "A2_PyramidFace", face, fr, (120, 70, 40))
    sprout = G.Geo()
    sprout.add(bevel_box(0.8, 3.0, 0.6, 0.15, (0.4, 8.2, 0)))
    sprout.add(bevel_box(2.6, 1.0, 0.6, 0.2, (0, 0, 0)).xf(T(1.6, 9.4, 0) @ RZ(25)))
    sprout.add(bevel_box(2.0, 0.9, 0.6, 0.2, (0, 0, 0)).xf(T(-0.6, 9.0, 0) @ RZ(-30)))
    k.mesh(m, "CarvingSprout", "A2_PyramidSprout", sprout, fr, (70, 170, 70))
    a.take(x, u, 25.0)
    for du in (-22.0, 22.0):
        a.tuck(x + 22.0, u + du)


def dune_steps(a, u0, u1, x0):
    """Low dunes against the east wall: solid stepped sand, each step 1 stud, so nobody is
    trapped and nothing is higher than a hop."""
    k = a.k
    m = k.sc.model(a.f, "Dune")
    z0, z1 = a.z(u1), a.z(u0)
    xw = 60.0
    steps = ((x0, z0, z1, 1.0), (x0 + 5.0, z0 + 5.0, z1 - 5.0, 2.0), (x0 + 10.0, z0 + 10.0, z1 - 10.0, 3.0))
    first = None
    for (sx0, sz0, sz1, h) in steps:
        p = k.solid_box(m, "Step", (sx0, h - 1.0, sz0), (xw, h, sz1), DUNE if h != 2.0 else lighter(DUNE, 0.12),
                        checker=True)
        first = first or p
    m.p["primary"] = first
    a.take((x0 + xw) / 2, (u0 + u1) / 2, (u1 - u0) / 2 + 2.0)


def dry_well(a, x, u):
    fr = a.cf(x, u)
    ring = G.Geo()
    for i in range(8):
        ring.add(bevel_box(2.4, 3.0, 1.0, 0.25, (0, 1.5, 2.6)).xf(G.M(G.ry(i * 45))))
    a.b.add("Well", SANDSTONE_DARK, ring, fr)
    dark = ccyl(2.2, 0.3, 10, "y", (0, 2.0, 0), 0.05)
    a.b.add("Well", (90, 60, 40), dark, fr)
    wood = G.Geo()
    for sx in (-1, 1):
        wood.add(bevel_box(0.8, 7.0, 0.8, 0.15, (sx * 3.0, 3.5, 0)))
    wood.add(bevel_box(7.0, 0.8, 0.8, 0.15, (0, 7.0, 0)))
    wood.add(ccyl(0.35, 0.3, 6, "y", (0, 5.6, 0), 0.05))
    a.b.add("Well", P.WOOD_DARK, wood, fr)
    a.b.add("Well", P.WOOD, cfrustum(0.7, 0.9, 1.2, 8, "y", (0, 4.6, 0), 0.1), fr)
    a.take(x, u, 4.5)
    a.tuck(x + 9.0, u + 2.0)


def small_bones(rng):
    g = G.Geo()
    for i in range(2):
        b = G.Geo()
        b.add(bevel_box(2.4, 0.4, 0.4, 0.1, (0, 0.2, 0)))
        for sx in (-1, 1):
            b.add(bevel_box(0.5, 0.6, 0.8, 0.15, (sx * 1.3, 0.3, 0)))
        g.add(b.xf(T(rng.uniform(-0.8, 0.8), 0, rng.uniform(-0.8, 0.8)) @ RY(rng.uniform(0, 180))))
    return [("Bones", P.BONE, g)]


def bones(a, x, u):
    """A big ribcage arching out of the sand and a horned skull beside it."""
    fr = a.cf(x, u, 15)
    g = G.Geo()
    g.add(bevel_box(0.9, 0.9, 12.0, 0.2, (0, 0.45, 0)))
    for i in range(5):
        z = -4.4 + i * 2.2
        h = 5.0 - abs(i - 2) * 0.8
        for sx in (-1, 1):
            g.add(bevel_box(0.7, h, 0.7, 0.15, (0, 0, 0)).xf(T(sx * 1.6, h / 2, z) @ RZ(-sx * 22)))
            g.add(bevel_box(0.7, 0.7, 0.7, 0.15, (sx * (1.6 + h * 0.4), h * 0.95, z)))
    skull = G.Geo()
    skull.add(bevel_box(2.6, 2.0, 3.0, 0.4, (4.6, 1.0, 7.2)))
    skull.add(bevel_box(1.8, 1.2, 1.6, 0.3, (4.6, 0.6, 9.0)))
    for sx in (-1, 1):
        skull.add(bevel_box(0.6, 0.6, 2.4, 0.15, (0, 0, 0)).xf(T(4.6 + sx * 1.6, 2.0, 7.0) @ RY(sx * 30) @ RX(-30)))
    eyes = G.Geo()
    for sx in (-1, 1):
        eyes.add(bevel_box(0.7, 0.7, 0.3, 0.1, (4.6 + sx * 0.6, 1.3, 8.6)))
    a.b.add("Ribcage", P.BONE, g, fr)
    a.b.add("Ribcage", P.BONE, skull, fr)
    a.b.add("Ribcage", (60, 44, 36), eyes, fr)
    a.take(x, u, 8.0)
    a.tuck(x - 12.0, u + 4.0)


def pots(a, x, u):
    """A cluster of clay pots, one on its side."""
    rng = a.rng
    g, rims = G.Geo(), G.Geo()
    spots = ((0, 0, 1.4, 2.6), (2.2, 0.8, 1.1, 2.0), (-1.6, 1.8, 0.9, 1.6))
    for (px, pz, r, h) in spots:
        g.add(cfrustum(r * 0.7, r, h * 0.6, 10, "y", (px, h * 0.3, pz), 0.15))
        g.add(cfrustum(r, r * 0.6, h * 0.4, 10, "y", (px, h * 0.8, pz), 0.15))
        rims.add(ccyl(r * 0.7, 0.4, 10, "y", (px, h + 0.1, pz), 0.08))
    side = G.Geo()
    side.add(cfrustum(0.7, 1.0, 1.6, 10, "y", (0, 0, 0), 0.12))
    g.add(side.xf(T(-2.0, 1.0, -1.6) @ RZ(90)))
    fr = a.cf(x, u, rng.uniform(0, 360))
    a.b.add("Pots", P.TERRACOTTA, g, fr)
    a.b.add("Pots", darker(P.TERRACOTTA, 0.8), rims, fr)
    a.take(x, u, 3.5)
