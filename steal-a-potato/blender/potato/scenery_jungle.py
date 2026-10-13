"""Jungle Ruins: the hero, a stepped temple with the golden idol on top, and the area's props.

The temple: four stone tiers getting lighter upwards, a steep solid staircase up the front between
two ramps, carved potato masks either side of it, moss and hanging vines, palms growing out of the
back corners, braziers at the foot and the top. On the top platform a small shrine with a dark
doorway and a roof comb, and in front of it the idol: a golden potato with a cute face, a
feather headdress and an emerald set in its gold band, on a pedestal with gold spilled at its feet.
"""
import math

import numpy as np

import spsgeo as G

from .scenery import (Area, Build, bar, bush, fern, flame, grass, ori, palm, potato, prop_attrs, register, rock,
                      round3, shade, stairs, turn, vine)

STONE = ("8c8471", "9a927e", "a8a08b", "b6ae99", "c4bda8")
MOSS = ("4f9a3a", "5db546", "3f8a34")
LEAF = ("3f9e3c", "55b848", "2e8a3a")
TRUNK = ("8a6a44", "7a5a38", "9a7a50")
GOLD = ("f5c518", "e0a800", "ffd447", "fff1a0")
EMERALD = "3bff8a"
DARK = "2c2a26"


def brazier(B, base, post_h, s=1.0):
    """A stone post with a bowl on top and a fire in it."""
    x, y, z = base
    out = [B.p("Brazier", (1.25 * s, post_h, 1.25 * s), (x, y + post_h / 2, z), None, STONE[0], solid=True)]
    top = y + post_h
    out.append(B.p("Brazier", (1.9 * s, 0.7 * s, 1.9 * s), (x, top + 0.35 * s, z), None, STONE[2]))
    out.append(B.p("Brazier", (2.05 * s, 0.32 * s, 2.05 * s), (x, top + 0.62 * s, z), G.ry(45), STONE[3]))
    out += flame(B, (x, top + 1.3 * s, z), 1.0 * s)
    return out


def mask(B, x, y, z, col):
    """A carved potato face on a tier's front (z is the face it sits on)."""
    B.p("Mask", (4.2, 2.6, 0.26), (x, y, z - 0.13), None, col)
    B.p("Mask", (3.3, 0.42, 0.48), (x, y + 1.0, z - 0.22), None, shade(col, 0.12))
    for s in (-1, 1):
        B.plate("Mask", (0.62, 0.86, 0.1), (x + s * 0.78, y + 0.22, z - 0.31), col=DARK)
    B.plate("Mask", (1.5, 0.34, 0.1), (x, y - 0.72, z - 0.31), col=DARK)


def hero(sc, parent):
    B = Build(sc, parent, "Jungle", seed=11)
    cz = 1.0
    tiers = ((40.0, 26.0), (32.0, 21.0), (24.0, 16.0), (17.0, 11.0))
    for i, (W, D) in enumerate(tiers):
        y = 4.0 * i
        col = STONE[i]
        B.p("Tier", (W - 0.2, 0.8, D - 0.2), (0.0, y + 0.4, cz), None, shade(col, -0.1), solid=True)
        B.p("Tier", (W - 0.6, 3.1, D - 0.6), (0.0, y + 0.8 + 1.55, cz), None, col, solid=True)
        B.p("Tier", (W, 0.7, D), (0.0, y + 3.65, cz), None, STONE[i + 1], solid=True)
    # the staircase up the front, between two ramps
    stairs(B, -4.0, 4.0, -14.4, -4.5, 0.0, 16.05, 16, (STONE[3], STONE[2]))
    for s in (-1, 1):
        bar(B, "Ramp", (s * 4.6, -0.4, -14.85), (s * 4.6, 16.45, -4.1), 1.2, STONE[1], t=1.5, n=(0, 1, 0), solid=True)
    # carved masks on the first two tiers
    for s in (-1, 1):
        mask(B, s * 11.5, 2.05, cz - 12.7, STONE[1])
        mask(B, s * 9.2, 6.05, cz - 10.2, STONE[2])
    # the shrine on the top platform
    B.p("Shrine", (11.0, 6.0, 6.0), (0.0, 19.0, 3.4), None, STONE[4], solid=True)
    B.plate("Door", (3.2, 4.25, 0.12), (0.0, 18.175, 0.35), col="231f1a")
    for s in (-1, 1):
        B.p("Shrine", (0.7, 4.54, 0.5), (s * 1.95, 18.33, 0.22), None, STONE[2])
    B.p("Shrine", (4.7, 0.8, 0.6), (0.0, 20.95, 0.2), None, STONE[2])
    B.p("Roof", (12.2, 0.8, 7.2), (0.0, 22.4, 3.4), None, STONE[3], solid=True)
    B.p("Roof", (9.0, 0.8, 5.1), (0.0, 23.2, 3.6), None, STONE[4], solid=True)
    for s in (-1, 0, 1):
        B.p("Comb", (0.9 + 0.1 * (s == 0), 3.6, 0.9), (s * 3.1, 25.4, 4.2), None, STONE[3])
    B.p("Comb", (7.0, 0.6, 0.8), (0.0, 25.2, 4.2), None, STONE[2])
    B.p("Comb", (8.0, 0.5, 1.3), (0.0, 27.45, 4.2), None, STONE[4])
    # the idol: a golden potato on a pedestal, emerald eyes, feathers, an emerald in its hands
    B.p("Pedestal", (3.6, 1.0, 3.6), (0.0, 16.5, -2.0), None, STONE[2], solid=True)
    B.p("Pedestal", (3.0, 0.7, 3.0), (0.0, 17.35, -2.0), G.ry(45), STONE[4], solid=True)
    s = 5.2
    ic = np.array((0.0, 17.7 + s / 2, -2.0))
    potato(B, ic, s, GOLD, name="Idol", glints=True)
    B.p("Idol", (s * 0.94, 0.55, s * 0.84), ic + (0, s * 0.37, 0), None, GOLD[1])                # a gold band
    B.p("Emerald", (1.05, 1.05, 0.5), ic + (0, s * 0.37, -s * 0.42 - 0.12), G.rz(45), EMERALD, material="Neon",
        flicker=0.12, lamp=True)                                                                  # its emerald
    for k, (a, col) in enumerate(((-34, "2fbf5a"), (-17, "e8403a"), (0, "3b8bff"), (17, "e8403a"), (34, "2fbf5a"))):
        R = G.rz(a) @ G.rx(-12)
        B.p("Feather", (0.8, 2.6, 0.16 + 0.02 * (k % 2)), ic + (0, s * 0.42, 0.9) + R @ (0, 1.3, 0), R, col)
    for sx in (-1, 1):                                                              # arms on its knees
        bar(B, "Idol", ic + (sx * s * 0.4, s * 0.02, -0.2), ic + (sx * s * 0.56, -s * 0.34, -s * 0.22), 0.95, GOLD[1])
    for k in range(5):                                                              # gold spilled at its feet
        a = math.radians(-150 + 30 * k)
        B.p("Gold", (0.8, 0.18 + 0.02 * k, 0.8), (math.cos(a) * 2.75, 16.11 + 0.01 * k, -2.0 + math.sin(a) * 2.2),
            G.ry(20 * k), GOLD[k % 3])
    # braziers at the foot of the stairs and either side of the idol
    for sx in (-1, 1):
        brazier(B, (sx * 6.6, 0.0, -13.6), 2.6)
        brazier(B, (sx * 5.6, 16.0, -2.4), 1.4, 0.85)
    # moss on the ledges, vines hanging from them
    moss = ((-15.0, 0, 3.5), (13.5, 0, 2.8), (-9.0, 1, 2.6), (11.0, 1, 3.4), (-7.5, 2, 2.4), (6.5, 2, 3.0),
            (-6.8, 3, 2.2), (17.5, 0, 2.0), (-12.5, 1, 2.0), (8.8, 3, 1.8))
    for k, (x, i, w) in enumerate(moss):
        W, D = tiers[i]
        y = 4.0 * i + 4.0
        zf = cz - D / 2
        B.p("Moss", (w, 0.28 + 0.03 * (k % 3), 1.6), (x, y + 0.12, zf + 0.55), G.rx(-6), MOSS[k % 3])
    vines = ((-16.8, 0, 3.0), (-12.2, 0, 2.6), (14.6, 0, 3.2), (9.6, 0, 2.2), (-10.6, 1, 2.8), (12.8, 1, 3.0),
             (-7.6, 2, 2.6), (7.2, 2, 2.2), (-5.6, 3, 2.4), (6.1, 3, 2.8))
    for k, (x, i, L) in enumerate(vines):
        W, D = tiers[i]
        top = (x, 4.0 * i + 3.85, cz - D / 2 - 0.12 - 0.02 * (k % 3))
        vine(B, top, L, ("3f8a34", "2e7a2e"), leaves=1, leaf_cols=("55b848", "6cc04a"))
    # palms out of the back corners, ferns round the foot, fallen stones
    for sx in (-1, 1):
        palm(B, (sx * 15.6, 4.0, 8.4), 12.5, 2.0, TRUNK, LEAF, fronds=6, frond_len=5.4, coconuts=2,
             heading=sx * 70.0)
    for k, (x, z) in enumerate(((-18.0, -11.8), (17.6, -12.2), (-13.4, -13.2), (12.8, -13.4))):
        fern(B, (x, 0.15, z), 5, LEAF, length=2.8, rise=35, heading=30 * k)
    for k, (x, y, z, sz) in enumerate(((-16.4, 4.0, -10.6, 2.3), (15.2, 4.0, -10.7, 2.1), (-12.6, 8.0, -8.2, 2.0),
                                       (12.0, 12.0, -5.9, 1.7))):
        bush(B, (x, y, z), sz, LEAF[k % 2:] + LEAF[:k % 2])
    for k, (x, z) in enumerate(((-9.6, -5.6), (8.4, -5.5))):
        fern(B, (x, 12.15, z), 5, ("55b848", "6cc04a", "3f9e3c"), length=2.0, rise=40, heading=50 * k)
    for k, (x, z, sz) in enumerate(((-20.0, -6.0, 2.2), (19.8, -3.0, 1.9), (-8.6, -14.0, 1.4), (20.2, 6.0, 1.6))):
        B.p("Rubble", (sz * 1.3, sz * 0.8, sz), (x, sz * 0.32, z), turn(B.rng, (4, 14)), STONE[1 + k % 3])
    return B.finish()


# ==================================================================== props

def p_palm(sc, parent):
    B = Build(sc, parent, "JunglePalm", seed=21)
    palm(B, (0.0, 0.0, 0.0), 15.0, 2.6, TRUNK, LEAF, fronds=7, frond_len=6.6, coconuts=3, heading=30.0)
    grass(B, (0.3, 0.0, 0.2), 4, ("5dbb46", "4fa83a", "7ad155"), h=(1.0, 1.8), r=1.4)
    return B.finish()


def p_banana(sc, parent):
    B = Build(sc, parent, "BananaPlant", seed=22)
    B.p("Stalk", (1.1, 3.4, 1.1), (0.0, 1.7, 0.0), ori(4, 20, 0), "6fa04a")
    B.p("Stalk", (0.85, 2.6, 0.85), (0.1, 4.5, 0.0), ori(-5, 65, 3), "82b356")
    top = np.array((0.15, 5.6, 0.0))
    for k in range(7):
        a = math.radians(360.0 / 7 * k + 15)
        r = math.radians((62, 30, 50, 22, 58, 36, 44)[k])
        d = np.array((math.sin(a) * math.cos(r), math.sin(r), -math.cos(a) * math.cos(r)))
        L = (4.8, 5.2, 4.4, 5.0, 4.6, 5.4, 4.2)[k]
        bar(B, "Leaf", top + d * 0.2, top + d * L, 1.9 + 0.06 * (k % 3), LEAF[k % 3], t=0.16 + 0.02 * (k % 2),
            n=(0, 1, 0))
    c = np.array((0.95, 3.7, -0.95))
    bar(B, "Bananas", top + (0.2, -0.3, -0.2), c + (0, 0.5, 0), 0.32, "6fa04a")
    for k, (dx, dy, dz) in enumerate(((0.0, 0.0, 0.0), (0.5, -0.12, 0.12), (-0.45, -0.06, 0.15), (0.06, -0.62, 0.08),
                                      (0.42, -0.7, -0.1))):
        B.p("Bananas", (0.42, 1.15, 0.42), c + (dx, dy, dz), ori(-12, 30 * k, 16 * (-1) ** k),
            ("ffd23f", "f5c518")[k % 2])
    B.p("Bud", (0.7, 1.0, 0.7), c + (0.05, -1.45, 0.0), ori(0, 45, 0), "8a2a5a")
    return B.finish()


def p_fern(sc, parent):
    B = Build(sc, parent, "BigFern", seed=23)
    B.p("Fern", (0.7, 0.5, 0.7), (0.0, 0.25, 0.0), G.ry(20), "3f8a34")
    fern(B, (0.0, 0.3, 0.0), 8, LEAF, length=3.4, rise=28)
    fern(B, (0.0, 0.45, 0.0), 5, ("6cc04a", "55b848"), length=2.4, rise=58, heading=22)
    return B.finish()


def p_pillar(sc, parent):
    B = Build(sc, parent, "RuinPillar", seed=24)
    B.p("Pillar", (2.7, 0.8, 2.7), (0.0, 0.4, 0.0), G.ry(8), STONE[0])
    y = 0.8
    for k, h in enumerate((2.3, 2.2, 1.7)):
        R = G.ry(8 + 13 * k) @ G.rz(4.0 * k) @ G.rx(-3.0 * k)
        c = np.array((0.08 * k, y + h / 2, -0.05 * k))
        B.p("Pillar", (1.9, h, 1.9), c, R, STONE[1 + k % 2])
        B.p("Pillar", (1.92, h - 0.06, 1.92), c, R @ G.ry(45), STONE[2 + k % 2])
        y += h - 0.08
    B.p("Capital", (2.9, 0.9, 2.9), (2.6, 0.45, -1.0), ori(18, 30, 9), STONE[3])
    B.p("Moss", (1.8, 0.25, 1.5), (0.18, y + 0.04, -0.1), ori(-6, 12, 9), MOSS[0])
    B.p("Moss", (2.1, 0.22, 1.2), (1.6, 0.92, -1.0), ori(16, 30, 9), MOSS[1])
    bar(B, "Vine", (-0.98, 5.8, -0.4), (-0.4, 1.0, -1.05), 0.35, "3f8a34", t=0.2, n=(0, 0, -1))
    bar(B, "Vine", (0.9, 4.9, -0.9), (1.05, 2.2, 0.6), 0.32, "2e7a2e", t=0.2, n=(1, 0, 0))
    fern(B, (-1.2, 0.1, -1.4), 3, LEAF, length=1.8, rise=40)
    return B.finish()


def p_stonehead(sc, parent):
    B = Build(sc, parent, "StoneHead", seed=25)
    c = np.array((0.0, 3.0, 0.0))
    round3(B, "Head", c, 6.0, 6.4, 5.4, (STONE[2], STONE[1], STONE[3]))
    B.p("Helmet", (5.6, 1.5, 5.0), c + (0, 2.6, 0.1), None, STONE[0])
    B.p("Helmet", (4.6, 1.36, 4.6), c + (0, 2.64, 0.1), G.ry(45), STONE[1])
    zf = c[2] - 2.7
    B.p("Brow", (3.6, 0.5, 0.6), c + (0, 1.3, -2.85), None, STONE[3])
    for s in (-1, 1):
        B.plate("Eye", (0.9, 1.25, 0.12), (s * 0.95, c[1] + 0.35, zf - 0.06), col=DARK)
        B.p("Ear", (0.7, 1.8, 1.2), c + (s * 3.0, -0.2, 0.0), None, STONE[1])
    B.p("Nose", (0.9, 1.0, 0.7), c + (0, -0.4, -2.95), None, STONE[3])
    B.plate("Mouth", (1.8, 0.42, 0.12), (0.0, c[1] - 1.32, zf - 0.06), col=DARK)
    B.p("Moss", (3.2, 0.3, 2.6), c + (-0.6, 3.42, 0.6), ori(5, 18, -6), MOSS[1])
    B.p("Moss", (2.2, 0.26, 1.2), c + (1.4, 3.36, -1.5), ori(-10, -12, 7), MOSS[0])
    vine(B, c + (1.7, 3.2, -2.85), 3.4, ("3f8a34", "2e7a2e"), leaves=1)
    return B.finish()


def p_tiki(sc, parent):
    B = Build(sc, parent, "TikiTotem", seed=26)
    B.p("Totem", (2.8, 0.6, 2.8), (0.0, 0.3, 0.0), G.ry(10), STONE[0])
    woods = ("8a5a2a", "a0703a", "7a4a22")
    y = 0.6
    for k, h in enumerate((2.7, 2.5, 2.3)):
        w = 2.3 - 0.1 * k
        c = np.array((0.0, y + h / 2, 0.0))
        wood = woods[k]
        B.p("Totem", (w, h, w * 0.9), c, G.ry(3 * (-1) ** k), wood)
        zf = -w * 0.45
        B.p("Totem", (w + 0.3, 0.42, 0.5), c + (0, h * 0.3, zf - 0.1), None, shade(wood, -0.25))      # brow
        for s in (-1, 1):
            B.plate("Eye", (0.62, 0.58, 0.1), c + (s * 0.5, h * 0.08, zf - 0.06), col="f4e4bc")
            B.plate("Eye", (0.28, 0.32, 0.1), c + (s * 0.5, h * 0.06, zf - 0.11), col=DARK)
        B.p("Totem", (0.5, 0.62, 0.4), c + (0, -h * 0.08, zf - 0.12), None, shade(wood, 0.15))         # nose
        B.plate("Mouth", (1.36, 0.46, 0.1), c + (0, -h * 0.3, zf - 0.06), col=DARK)
        B.plate("Mouth", (1.0, 0.16, 0.1), c + (0, -h * 0.3 + 0.1, zf - 0.11), col="f4e4bc")
        y += h
    B.p("Totem", (2.5, 0.4, 2.5), (0.0, y + 0.2, 0.0), G.ry(45), woods[1])
    flame(B, (0.0, y + 1.05, 0.0), 1.1)
    return B.finish()


def p_rocks(sc, parent):
    B = Build(sc, parent, "MossyRocks", seed=27)
    rock(B, (0.0, 0.0, 0.0), 3.4, (STONE[1], STONE[2], STONE[0]))
    rock(B, (2.9, 0.0, -1.2), 2.2, (STONE[2], STONE[3], STONE[1]))
    rock(B, (-2.4, 0.0, -1.4), 1.6, (STONE[0], STONE[2], STONE[1]))
    B.p("Moss", (2.4, 0.25, 1.9), (0.2, 2.55, 0.1), ori(6, 20, -5), MOSS[0])
    B.p("Moss", (1.4, 0.22, 1.2), (2.8, 1.62, -1.1), ori(-7, 40, 8), MOSS[1])
    grass(B, (-1.0, 0.0, -2.3), 3, ("5dbb46", "4fa83a", "7ad155"), h=(1.0, 1.6))
    return B.finish()


def p_log(sc, parent):
    B = Build(sc, parent, "FallenLog", seed=28)
    R = G.ry(8)
    c = np.array((0.0, 0.95, 0.0))
    B.p("Log", (8.0, 1.9, 1.9), c, R, "7a5a38")
    B.p("Log", (7.9, 1.9, 1.9), c, R @ G.rx(45), "8a6a44")
    for s in (-1, 1):
        e = c + R @ (s * 4.0, 0, 0)
        B.p("Log", (0.1, 1.5, 1.5), e + R @ (s * 0.04, 0, 0), R, "d8b07a", shadow=False)
        B.p("Log", (0.1, 1.5, 1.5), e + R @ (s * 0.05, 0, 0), R @ G.rx(45), "c8a070", shadow=False)
    bar(B, "Log", c + R @ (1.4, 0.6, 0.2), c + R @ (2.4, 2.6, 0.8), 0.7, "6e5030")
    for k, (x, z, sz, col) in enumerate(((-1.6, -0.75, 1.0, "e8403a"), (0.2, -0.85, 0.8, "f07412"),
                                         (-2.7, 0.7, 0.7, "e8403a"))):
        p = c + R @ (x, 0.0, z)
        B.p("Mushroom", (0.3, 0.6 * sz, 0.3), p + (0, 0.95 + 0.3 * sz, 0), None, "f4ecd8")
        B.p("Mushroom", (0.9 * sz, 0.35 * sz, 0.9 * sz), p + (0, 0.98 + 0.65 * sz, 0), G.ry(45), col)
    B.p("Moss", (2.4, 0.24, 1.3), c + R @ (-0.4, 1.05, 0.1), R @ G.rz(3), MOSS[0])
    fern(B, (1.0, 0.1, 1.6), 3, LEAF, length=1.8, rise=40, heading=160)
    return B.finish()


def p_flower(sc, parent):
    B = Build(sc, parent, "JungleFlower", seed=29)
    for k in range(4):
        a = math.radians(45 + 90 * k)
        d = np.array((math.sin(a), 0.12, -math.cos(a)))
        bar(B, "Leaf", (0, 0.2, 0) + d * 0.3, (0, 0.2, 0) + d * 3.3, 1.3, LEAF[k % 3], t=0.16, n=(0, 1, 0))
    for k in range(5):
        a = math.radians(72 * k)
        d = np.array((math.sin(a), 0.0, -math.cos(a)))
        R = G.ry(-72 * k) @ G.rx(16)
        c = np.array((0, 0.75, 0)) + d * 1.25
        B.p("Petal", (1.6, 0.3 + 0.02 * (k % 2), 1.9), c, R, ("e8403a", "d93a30")[k % 2])
        B.p("Petal", (0.42, 0.1, 0.42), c + R @ (0.25, 0.2, -0.2), R, "fff1e0", shadow=False)
    B.p("Centre", (1.5, 0.7, 1.5), (0.0, 0.9, 0.0), G.ry(45), "5a1a24")
    B.p("Centre", (0.9, 0.3, 0.9), (0.0, 1.32, 0.0), None, "ffd23f")
    return B.finish()


AREA = register(Area("Jungle", "Jungle Ruins", hero, [
    (p_palm, prop_attrs(8, 0.85, 1.25, "Side", True)),
    (p_banana, prop_attrs(6, 0.9, 1.3, "Side", False)),
    (p_fern, prop_attrs(12, 0.8, 1.4, "Any", False)),
    (p_pillar, prop_attrs(5, 0.9, 1.3, "Side", True)),
    (p_stonehead, prop_attrs(3, 0.9, 1.2, "Edge", True)),
    (p_tiki, prop_attrs(4, 0.9, 1.2, "Side", True)),
    (p_rocks, prop_attrs(6, 0.8, 1.3, "Side", True)),
    (p_log, prop_attrs(4, 0.9, 1.2, "Side", True)),
    (p_flower, prop_attrs(8, 0.8, 1.3, "Any", False)),
], ground="4fa83a"))
