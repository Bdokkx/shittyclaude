"""Area 1, Meadow Patch: bright green, orange-brown brick. Hedges along the walls, flower clumps,
apple trees, a wooden cart of potatoes, a pond with lily pads and reeds, potato crates.
Hero: a big red-and-white windmill-style scarecrow tower against the east wall."""
import math

import numpy as np

import spsgeo as G
from spsgeo import CF, T, RX, RY, RZ, S

from .. import props as P
from ..geo import bevel_box, ccyl, cfrustum
from ..kit import darker
from .common import Area

HERO = (47.0, 112.0)          # (x, u)


def build(k, n, folder, markers, rng):
    a = Area(k, n, folder, markers, rng)
    hero(a)
    # hedges along both walls, with gaps
    for sx, spans in ((-1, ((6, 58), (74, 104), (136, 214))), (1, ((6, 88), (140, 214)))):
        for (u0, u1) in spans:
            ln = u1 - u0
            a.b.add_parts("Hedges", P.hedge(ln, 3.2, 3.0), a.cf(sx * 57.5, (u0 + u1) / 2, 90))
    # apple trees
    for (x, u) in ((-42, 36), (-47, 118), (-38, 190), (40, 28), (46, 176), (-30, 88)):
        a.put("Trees", P.tree_round(14.0 + rng.uniform(-1.5, 2.0), 5.0, fruit=P.RED, rng=rng), x, u,
              rng.uniform(0, 90), r=6.0)
        a.tuck(x + (8 if x < 0 else -8), u + 4)
    cart(a, -38.0, 64.0)
    pond(a, -40.0, 150.0)
    for (x, u, ang) in ((36, 96, 10), (33, 100, -15), (36, 92, 40), (-31, 166, 0)):
        a.put("Crates", P.crate(rng=rng), x, u, ang, r=2.4)
    for (x, u) in a.scatter(8, 3.0):
        a.put("Bushes", P.bush(2.0 + rng.uniform(0, 0.8), P.LEAF, rng), x, u, r=2.6)
    for (x, u) in a.scatter(6, 2.0, xs=(28.0, 52.0)):
        a.put("Reeds", P.reeds(rng, 3), x, u, rng.uniform(0, 180), r=1.8)
    for (x, u) in a.scatter(16, 2.2, lane_too=5):
        a.put("Flowers", P.flower_clump(rng, 5), x, u, r=2.0)
    # a little fence by the cart and the pond
    a.b.add_parts("Fence", P.fence_run(18.0), a.cf(-50.0, 64.0, 90))
    a.b.add_parts("Fence", P.fence_run(12.0), a.cf(-27.0, 150.0, 90))
    a.flush()
    return a


def hero(a):
    """The scarecrow tower: stacked red and white tiers (solid), turning windmill sails on its
    lane side, and a big scarecrow with a potato-sack head standing on top."""
    k = a.k
    x, u = HERO
    zc = a.z(u)
    m = k.sc.model(a.f, "ScarecrowTower")
    y = 0.0
    tiers = []
    for i in range(6):
        w = 12.0 - i * 1.0
        h = 5.0
        col = (226, 52, 46) if i % 2 == 0 else (250, 246, 238)
        tiers.append(k.solid(m, "Tier", (w, h, w), CF((x, y + h / 2, zc)), col))
        y += h
    m.p["primary"] = tiers[0]
    top = y
    # a red roof rim and a platform
    k.mesh(m, "Rim", "A1_TowerRim", bevel_box(9.0, 1.0, 9.0, 0.2, (0, 0.5, 0)), CF((x, top, zc)), (200, 40, 36))
    # windmill sails on the west face, turning about their own Y (pointing west at the lane)
    sails = G.Geo()
    sails.add(ccyl(1.4, 1.6, 10, "y", (0, 0, 0), 0.25))
    for i in range(4):
        arm = G.Geo()
        arm.add(bevel_box(0.9, 0.6, 13.0, 0.12, (0, 0.6, 7.2)))
        arm.add(bevel_box(3.8, 0.4, 8.5, 0.1, (1.5, 0.8, 9.0)))
        sails.add(arm.xf(G.M(G.ry(i * 90 + 20))))
    sp = k.mesh(m, "Sails", "A1_TowerSails", sails, CF((x - 6.2, 20.0, zc), G.rz(90)), (250, 240, 220))
    k.attr(sp, "Spin", 30.0)
    k.mesh(m, "Hub", "A1_TowerHub", ccyl(1.0, 1.4, 8, "x", (0, 0, 0), 0.2), CF((x - 5.6, 20.0, zc)), (200, 40, 36))
    # the scarecrow on top, facing the lane (west)
    fr = CF((x, top + 1.0, zc), G.ry(90))
    post = G.Geo()
    post.add(bevel_box(1.2, 12.0, 1.2, 0.2, (0, 6.0, 0.6)))
    post.add(bevel_box(12.0, 1.0, 1.0, 0.2, (0, 8.6, 0.6)))
    k.mesh(m, "Post", "A1_ScarecrowPost", post, fr, P.WOOD)
    shirt = G.Geo()
    shirt.add(bevel_box(5.0, 5.0, 2.4, 0.4, (0, 7.2, 0)))
    for sx in (-1, 1):
        shirt.add(bevel_box(4.0, 2.0, 2.0, 0.35, (sx * 4.2, 8.6, 0)))
    k.mesh(m, "Shirt", "A1_ScarecrowShirt", shirt, fr, (70, 120, 220))
    patch = G.Geo()
    patch.add(bevel_box(1.4, 1.4, 0.3, 0.1, (1.2, 6.4, -1.25)))
    patch.add(bevel_box(1.2, 1.0, 0.3, 0.1, (-3.8, 8.9, -1.05)))
    k.mesh(m, "Patches", "A1_ScarecrowPatches", patch, fr, (250, 200, 60))
    straw = G.Geo()
    for sx in (-1, 1):
        straw.add(bevel_box(1.2, 1.4, 1.4, 0.3, (sx * 6.7, 8.4, 0)))
    straw.add(bevel_box(3.6, 1.4, 2.0, 0.3, (0, 4.2, 0)))
    k.mesh(m, "Straw", "A1_ScarecrowStraw", straw, fr, P.HAY)
    pg, _ = P.potato_geo(4.6, 3.8, 4.0, eyes=False)
    k.mesh(m, "Head", "A1_ScarecrowHead", pg, fr * CF((0, 11.0, 0), G.rz(90)) * CF((0, -2.0, 0)), (220, 186, 124))
    face = G.Geo()
    for sx in (-1, 1):
        face.add(bevel_box(0.8, 0.8, 0.3, 0.12, (sx * 0.8, 11.6, -1.85)))
    for i in range(5):                                       # a stitched smile
        fx = -1.2 + i * 0.6
        face.add(bevel_box(0.4, 0.3, 0.3, 0.08, (fx, 10.4 - 0.25 * (1 - (fx / 1.2) ** 2), -1.85)))
    k.mesh(m, "Face", "A1_ScarecrowFace", face, fr, P.BLACK)
    hat = G.Geo()
    hat.add(ccyl(3.8, 0.4, 14, "y", (0, 13.3, 0), 0.1))
    hat.add(cfrustum(2.2, 1.8, 2.6, 12, "y", (0, 14.8, 0), 0.15))
    k.mesh(m, "Hat", "A1_ScarecrowHat", hat, fr, (236, 186, 70))
    k.mesh(m, "HatBand", "A1_ScarecrowHatBand", ccyl(2.24, 0.6, 12, "y", (0, 13.9, 0), 0.08), fr, (220, 50, 50))
    a.take(x, u, 10.0)
    a.tuck(x - 14.0, u + 6.0)


def cart(a, x, u):
    """A wooden hand cart loaded with potatoes, two big wheels, its handles on the ground."""
    k = a.k
    fr = a.cf(x, u, 90)
    g = G.Geo()
    g.add(bevel_box(5.0, 0.6, 8.0, 0.12, (0, 2.6, 0)))
    for sx in (-1, 1):
        g.add(bevel_box(0.5, 2.0, 8.0, 0.1, (sx * 2.3, 3.8, 0)))
    for sz in (-1, 1):
        g.add(bevel_box(5.0, 2.0, 0.5, 0.1, (0, 3.8, sz * 3.8)))
    for sx in (-1, 1):
        g.add(bevel_box(0.5, 0.5, 6.0, 0.1, (0, 0, 0)).xf(T(sx * 1.6, 1.4, -6.4) @ RX(-18)))
    a.b.add("Cart", P.WOOD, g, fr)
    w = G.Geo()
    for sx in (-1, 1):
        w.add(ccyl(2.4, 0.8, 12, "x", (sx * 3.0, 2.4, 1.0), 0.2))
    a.b.add("Cart", P.WOOD_DARK, w, fr)
    hubs = G.Geo()
    for sx in (-1, 1):
        hubs.add(ccyl(0.7, 1.0, 8, "x", (sx * 3.0, 2.4, 1.0), 0.15))
    a.b.add("Cart", P.METAL, hubs, fr)
    load = G.Geo()
    for i in range(10):
        pg, _ = P.potato_geo(1.5, 1.0, 0.9, eyes=False)
        load.add(pg.xf(T(a.rng.uniform(-1.6, 1.6), 4.4 + 0.3 * (i % 3), a.rng.uniform(-3.0, 3.0)) @
                       RY(a.rng.uniform(0, 180))))
    a.b.add("Cart", P.POTATO, load, fr)
    a.take(x, u, 6.0)
    a.tuck(x + 9.0, u + 12.0)


def pond(a, x, u):
    """A small round pond (flush with the ground, walk-through), a stone rim, lily pads with a
    flower or two, reeds at the back."""
    k = a.k
    fr = a.cf(x, u)
    r = 7.5
    a.b.add("Pond", (80, 170, 240), ccyl(r, 0.2, 16, "y", (0, 0.06, 0), 0.05), fr, material="SmoothPlastic")
    rim = G.Geo()
    for i in range(14):
        ang = i * 360 / 14
        rim.add(bevel_box(2.6, 0.8, 1.6, 0.25, (0, 0.3, r + 0.4)).xf(G.M(G.ry(ang + a.rng.uniform(-5, 5)))))
    a.b.add("Pond", P.STONE, rim, fr)
    pads = G.Geo()
    fl = G.Geo()
    for (px, pz, pr) in ((-2.0, 1.5, 1.4), (2.5, -1.0, 1.2), (0.5, 3.6, 1.0), (-3.2, -2.6, 1.1), (3.4, 2.8, 0.9)):
        pads.add(ccyl(pr, 0.2, 10, "y", (px, 0.22, pz), 0.05))
    for (px, pz) in ((-2.0, 1.5), (3.4, 2.8)):
        fl.add(bevel_box(0.7, 0.5, 0.7, 0.15, (px + 0.3, 0.5, pz)))
    a.b.add("Pond", (60, 170, 70), pads, fr)
    a.b.add("Pond", P.PINK, fl, fr)
    for i, ang in enumerate((200, 240, 290)):
        rx, rz = (r + 1.6) * math.cos(math.radians(ang)), (r + 1.6) * math.sin(math.radians(ang))
        a.b.add_parts("Reeds", P.reeds(a.rng, 4), fr * CF((rx, 0, rz)))
    a.take(x, u, r + 3.0)
    a.tuck(x + r + 8.0, u - 6.0)
