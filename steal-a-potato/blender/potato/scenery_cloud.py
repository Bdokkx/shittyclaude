"""Cloud Kingdom: the hero, a rainbow over a palace of cloud, and the area's props.

A fluffy cloud base (solid; cloud steps climb to the gate) carries a white and gold palace: a keep
with a gold dome and a spire, two slim towers with gold roofs and flags, pale blue windows, a gold
gate with lamps either side. Behind and over it all a six-band rainbow arches from cloud to cloud.
Little clouds float about.
"""
import math

import numpy as np

import spsgeo as G

from .scenery import (Area, Build, INK, bar, ori, potato, prop_attrs, register, round3, shade)

CLOUD = ("ffffff", "f4f8ff", "e6eefa", "d8e4f4")
GOLD = ("ffd447", "f5c518", "ffe58a")
SKY = ("dff2ff", "bfe4ff", "a8d8ff")
RAINBOW = ("ff4d6d", "ff9f3d", "ffe14d", "5ee06a", "4da6ff", "a46bff")
PINK = "ffb4d8"


def puff(B, c, s, name="Cloud", solid=False, heading=0.0):
    """A cloud puff: a wide flat block, a crossing one, a turned one on top, all white and pale blue."""
    c = np.asarray(c, float)
    return [B.p(name, (s * 1.5, s * 0.62, s * 1.0), c + (0, s * 0.31, 0), G.ry(heading), CLOUD[0], solid=solid),
            B.p(name, (s * 1.0, s * 0.6, s * 1.35), c + (s * 0.1, s * 0.34, 0), G.ry(heading + 12), CLOUD[1], solid=solid),
            B.p(name, (s * 0.9, s * 0.58, s * 0.9), c + (-s * 0.1, s * 0.66, 0), G.ry(heading + 45), CLOUD[0],
                solid=solid)]


def rainbow(B, centre, r_out, bands=RAINBOW, width=1.2, depth=1.6, segs=9, name="Rainbow", a0=0.0, a1=180.0):
    """An arch of colour bands round centre (in the XY plane, facing -Z): each band a run of straight
    segments, the outer band red. Depths differ a hair band to band and segment to segment so no
    faces fight."""
    c = np.asarray(centre, float)
    out = []
    for k, col in enumerate(bands):
        r = r_out - width / 2 - width * k
        step = (a1 - a0) / segs
        for j in range(segs):
            a = math.radians(a0 + step * (j + 0.5))
            L = 2 * r * math.sin(math.radians(step / 2)) + 0.24
            p = c + (math.cos(a) * r, math.sin(a) * r, 0)
            d = depth + 0.04 * k + 0.02 * (j % 2)
            out.append(B.p(name, (L, width, d), p, G.rz(math.degrees(a) + 90.0), col))
    return out


# ==================================================================== the hero

def hero(sc, parent):
    B = Build(sc, parent, "Cloud", seed=151)
    # the cloud base and the little clouds the rainbow rests on
    for k, (x, z, s, h) in enumerate(((-10.0, 1.0, 9.0, 0.0), (0.0, 3.0, 10.0, 30.0), (10.0, 1.4, 8.6, 60.0),
                                      (-4.0, -4.0, 6.4, 15.0), (6.0, -4.2, 6.0, 75.0))):
        puff(B, (x, 0.0, z), s, name="Base", solid=True, heading=h)
    for sx in (-1, 1):
        puff(B, (sx * 17.4, 0.0, 6.0), 3.6, heading=20 * sx)
    for k, (x, y, z, s) in enumerate(((-14.6, 0.0, -2.6, 3.4), (13.8, 0.0, -2.8, 3.0), (-8.8, 3.6, -3.2, 2.6),
                                       (9.6, 3.2, -3.4, 2.4))):
        puff(B, (x, y, z), s, heading=25 * k + 10)
    for k in range(4):
        B.p("Step", (4.6 - 0.2 * k, 0.9, 2.2), (0.0, 0.45 + 0.9 * k, -10.2 + 1.8 * k), G.ry(4 * (-1) ** k),
            CLOUD[k % 2], solid=True)
    top = 4.8
    # the keep: white walls, gold bands, a gold dome and spire
    B.p("Keep", (9.0, 9.0, 7.0), (0.0, top + 4.5, 3.0), None, CLOUD[0], solid=True)
    for y in (top + 0.45, top + 8.8):
        B.p("Keep", (9.4, 0.6, 7.4), (0.0, y, 3.0), None, GOLD[1])
    y = top + 9.1
    for k, (w, h) in enumerate(((7.6, 1.6), (6.4, 1.8), (4.8, 1.8), (3.0, 1.6), (1.4, 1.4))):
        B.p("Dome", (w, h, w), (0.0, y + h / 2, 3.0), G.ry(45 * (k % 2)), GOLD[k % 3])
        y += h - 0.05
    bar(B, "Spire", (0.0, y - 0.1, 3.0), (0.0, y + 3.0, 3.0), 0.3, GOLD[1])
    B.p("Spire", (0.9, 0.9, 0.9), (0.0, y + 3.2, 3.0), ori(35.26, 45, 0), "fff4b0", material="Neon", lamp=True)
    zf = 3.0 - 3.5
    B.plate("Gate", (3.2, 4.6, 0.12), (0.0, top + 2.3, zf - 0.06), col=SKY[2])
    B.p("Gate", (4.2, 0.8, 0.6), (0.0, top + 5.0, zf - 0.3), None, GOLD[0])
    B.p("Gate", (2.4, 2.4, 0.5), (0.0, top + 5.6, zf - 0.28), G.rz(45), GOLD[2])
    for sx in (-1, 1):
        B.p("Gate", (0.6, 4.9, 0.7), (sx * 1.9, top + 2.55, zf - 0.3), None, GOLD[1])
        for yy in (2.6, 6.6):
            B.plate("Window", (1.4, 2.0, 0.12), (sx * 3.0, top + yy, zf - 0.06), col=SKY[1])
            B.p("Window", (1.8, 0.3, 0.4), (sx * 3.0, top + yy + 1.15, zf - 0.2), None, GOLD[0])
        B.p("Lamp", (0.4, 2.2, 0.4), (sx * 2.6, top + 1.1, zf - 1.6), None, GOLD[1])
        B.p("Lamp", (0.8, 0.8, 0.8), (sx * 2.6, top + 2.6, zf - 1.6), G.ry(45), "fff4b0", material="Neon", flicker=0.08,
            lamp=True)
    # two slim towers with gold roofs and flags
    for sx, flag in ((-1, PINK), (1, SKY[2])):
        tx = sx * 7.6
        B.p("Tower", (3.6, 13.0, 3.6), (tx, top + 6.5, 3.5), None, CLOUD[1], solid=True)
        B.p("Tower", (3.4, 12.96, 3.4), (tx, top + 6.5, 3.5), G.ry(45), CLOUD[0], solid=True)
        B.plate("Window", (1.0, 1.8, 0.12), (tx, top + 9.0, 3.5 - 2.47), col=SKY[2])
        y = top + 13.0
        for k, (w, h) in enumerate(((4.6, 1.2), (3.4, 1.6), (2.2, 1.6), (1.0, 1.6))):
            B.p("Roof", (w, h, w), (tx, y + h / 2, 3.5), G.ry(45 * ((k + 1) % 2)), GOLD[k % 3])
            y += h - 0.05
        bar(B, "Flag", (tx, y - 0.1, 3.5), (tx, y + 2.6, 3.5), 0.18, GOLD[1])
        B.p("Flag", (1.8, 1.1, 0.12), (tx + sx * 0.95, y + 2.0, 3.5), None, flag)
    # the rainbow arching over it all, from cloud to cloud
    rainbow(B, (0.0, 3.0, 7.6), 19.2)
    # little clouds floating about
    for k, (x, y, z, s) in enumerate(((-15.0, 15.0, 2.0, 2.2), (14.0, 18.0, 4.0, 2.6), (-6.0, 24.0, 9.0, 1.8))):
        puff(B, (x, y, z), s, heading=30 * k)
    return B.finish()


# ==================================================================== props

def p_puff(sc, parent):
    B = Build(sc, parent, "CloudPuff", seed=161)
    puff(B, (0.0, 0.0, 0.0), 4.0)
    puff(B, (2.8, 0.0, 0.8), 2.6, heading=40)
    puff(B, (-2.6, 0.0, 0.5), 2.2, heading=70)
    B.p("Cloud", (2.0, 1.4, 2.0), (0.4, 2.9, 0.2), G.ry(20), CLOUD[1])
    return B.finish()


def p_tree(sc, parent):
    B = Build(sc, parent, "CloudTree", seed=162)
    for k, (w, y) in enumerate(((1.4, 1.5), (1.2, 4.4), (1.0, 7.1))):
        B.p("Trunk", (w, 3.0, w), (0.1 * k, y, 0.0), ori(5 * (-1) ** k, 30 * k, 0), ("e8d8b8", "f0e2c4", "dcc8a4")[k])
    for k, (dx, dy, dz, s) in enumerate(((0.0, 9.6, 0.0, 3.6), (2.4, 8.4, 0.6, 2.6), (-2.3, 8.6, -0.4, 2.6))):
        puff(B, (dx, dy, dz), s, heading=30 * k)
    return B.finish()


def p_rainbow(sc, parent):
    B = Build(sc, parent, "RainbowArch", seed=163)
    rainbow(B, (0.0, 0.6, 0.0), 6.4, width=0.8, depth=1.2, segs=5)
    for sx in (-1, 1):
        puff(B, (sx * 5.6, 0.0, 0.0), 2.2, heading=30 * sx)
    return B.finish()


def p_harp(sc, parent):
    B = Build(sc, parent, "GoldenHarp", seed=164)
    puff(B, (0.0, 0.0, 0.0), 2.6)
    base = np.array((0.0, 1.9, 0.0))
    B.p("Harp", (2.8, 0.5, 1.0), base + (0, 0.25, 0), None, GOLD[1])
    bar(B, "Harp", base + (1.2, 0.3, 0), base + (0.9, 5.2, 0), 0.5, GOLD[0], n=(0, 0, -1))
    bar(B, "Harp", base + (0.9, 5.2, 0), base + (-1.4, 3.4, 0), 0.5, GOLD[2], t=0.56, n=(0, 0, -1))
    bar(B, "Harp", base + (-1.4, 3.4, 0), base + (-1.2, 0.3, 0), 0.5, GOLD[1], t=0.62, n=(0, 0, -1))
    for k in range(4):
        x = -0.8 + 0.5 * k
        top = 3.6 + 0.4 * k
        B.p("String", (0.08 + 0.01 * k, top - 0.5, 0.08), base + (x, 0.5 + (top - 0.5) / 2, 0), None, "fff8e0")
    return B.finish()


def p_pillar(sc, parent):
    B = Build(sc, parent, "CloudPillar", seed=165)
    puff(B, (0.0, 0.0, 0.0), 3.0)
    B.p("Pillar", (2.4, 0.6, 2.4), (0.0, 2.3, 0.0), None, GOLD[1])
    B.p("Pillar", (1.6, 6.0, 1.6), (0.0, 5.6, 0.0), None, CLOUD[0])
    B.p("Pillar", (1.56, 5.96, 1.56), (0.0, 5.6, 0.0), G.ry(45), CLOUD[2])
    B.p("Pillar", (2.6, 0.7, 2.6), (0.0, 8.95, 0.0), None, GOLD[0])
    B.p("Pillar", (2.2, 0.66, 2.2), (0.0, 8.95, 0.0), G.ry(45), GOLD[2])
    B.p("Pillar", (1.8, 0.3, 1.8), (0.0, 5.6, 0.0), G.ry(22.5), GOLD[1])
    B.p("Pillar", (1.0, 1.0, 1.0), (0.0, 9.9, 0.0), ori(35.26, 45, 0), "fff4b0", material="Neon", flicker=0.06, lamp=True)
    return B.finish()


def p_balloon(sc, parent):
    B = Build(sc, parent, "HotAirBalloon", seed=166)
    c = np.array((0.0, 9.0, 0.0))
    round3(B, "Balloon", c, 5.4, 6.0, 5.4, (RAINBOW[0], RAINBOW[2], RAINBOW[4]), lid=(3.0, 0.6, 3.0))
    B.p("Balloon", (3.4, 1.4, 3.4), c + (0, -3.4, 0), G.ry(45), RAINBOW[1])
    B.p("Basket", (2.2, 1.6, 2.2), (0.0, 1.6, 0.0), None, "b88450")
    B.p("Basket", (2.4, 0.3, 2.4), (0.0, 2.45, 0.0), None, "8a5a2a")
    for sx in (-1, 1):
        for sz in (-1, 1):
            bar(B, "Rope", (sx * 0.95, 2.5, sz * 0.95), (sx * 1.4, 5.3, sz * 1.4), 0.12 + 0.02 * (sz > 0), "6b4226")
    return B.finish()


def p_lantern(sc, parent):
    B = Build(sc, parent, "StarLantern", seed=167)
    puff(B, (0.0, 0.0, 0.0), 1.8)
    B.p("Post", (0.4, 7.0, 0.4), (0.0, 4.6, 0.0), None, GOLD[1])
    from .plotkit import star
    star(B.deco, B.m, (0.0, 8.8, 0.0), 1.1, "ffe14d")
    for p in [n for n in B.m.walk() if n.kind == "Part" and n.name == "Star"]:
        p.p.setdefault("attrs", {})["NightLamp"] = True
        p.p["attrs"]["Flicker"] = 0.08
    return B.finish()


def p_windmill(sc, parent):
    B = Build(sc, parent, "CloudMill", seed=168)
    puff(B, (0.0, 0.0, 0.0), 2.8)
    for k, (w, h, y) in enumerate(((2.6, 3.0, 3.0), (2.2, 3.0, 5.9), (1.8, 2.4, 8.5))):
        B.p("Mill", (w, h, w), (0.0, y, 0.0), G.ry(45 * (k % 2)), (CLOUD[0], CLOUD[2], CLOUD[1])[k])
    B.p("Mill", (2.4, 1.2, 2.4), (0.0, 10.2, 0.0), G.ry(45), PINK)
    axle = np.array((0.0, 8.6, -1.4))
    Ra = G.rx(90)
    for k, (L, col) in enumerate(((7.0, SKY[1]), (6.96, SKY[0]))):
        B.p("Sails", (L, 0.2 + 0.03 * k, 0.9), axle, Ra @ G.ry(90 * k), col, spin=40.0)
    B.p("Sails", (0.8, 0.5, 0.8), axle + (0, 0, -0.1), Ra @ G.ry(45), GOLD[0], spin=40.0)
    return B.finish()


AREA = register(Area("Cloud", "Cloud Kingdom", hero, [
    (p_puff, prop_attrs(10, 0.8, 1.4, "Side", True)),
    (p_tree, prop_attrs(6, 0.85, 1.25, "Side", True)),
    (p_rainbow, prop_attrs(3, 0.9, 1.3, "Side", True)),
    (p_harp, prop_attrs(3, 0.9, 1.2, "Side", True)),
    (p_pillar, prop_attrs(5, 0.9, 1.2, "Side", True)),
    (p_balloon, prop_attrs(3, 0.9, 1.3, "Edge", False)),
    (p_lantern, prop_attrs(6, 0.9, 1.2, "Side", False)),
    (p_windmill, prop_attrs(3, 0.9, 1.2, "Edge", True)),
], ground="bfe4ff"))
