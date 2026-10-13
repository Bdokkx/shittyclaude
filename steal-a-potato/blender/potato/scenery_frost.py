"""Frost Fields: the hero, the gate of an ice castle, and the area's props.

Two round ice towers in three close shades, lighter upwards, on wide plinths: an overhanging ring of
white merlons at the top, stepped blue spires with glowing cyan crystals on their tips, crystals
growing out of the battlements, royal blue banners with a white snowflake, slit windows and icicles
hanging from every ledge. Between them the gatehouse of big ice blocks: an arch framed in white with
a glowing crystal keystone, a half-raised portcullis over a deep blue passage, a snowy walkway with
merlons and, on a plinth in the middle of it, the frozen statue of the potato king in a golden crown
and a royal blue stole, holding up a crystal sceptre. Snow drifts round its foot.
"""
import math

import numpy as np

import spsgeo as G

from .scenery import (Area, Build, INK, bar, ori, potato, prop_attrs, register, round3)
from .scenery_marsh import facets, facing, octo

ICE = ("c4e3ff", "acd6fb", "dcf0ff")
DRUMS = (("a6d2fa", "a6d2fa", "c0e1fe"), ("bcdeff", "bcdeff", "d4ecff"), ("d4ecff", "d4ecff", "eaf6ff"))
PLINTH = ("9ccaf2", "9ccaf2", "a8d2f6")
SNOW = ("f4f9ff", "ffffff", "e4eef8")
ROOF = ("4f8fe0", "3f7ed0", "68a6ef")
DEEP = ("1e2f5a", "2a4078")
CRYSTAL = ("3ff0ff", "8ffaff", "20d8ff")
ICICLE = ("e2f5ff", "ffffff")
BANNER = ("2f5fc8", "244fb0")
GOLD = ("f5c518", "ffd447", "e0a800")
IRON = ("b4c8e0", "9ab0cc")
RED = ("e8403a", "d6352e", "f25a46")
WOOD = ("6b4226", "9a6238", "c8743a", "a0572b")


def icicle(B, top, L, w=0.6, name="Icicle"):
    """An icicle hanging from top: a thick upper block and a thin tip, both turned 45 degrees."""
    top = np.asarray(top, float)
    return [B.p(name, (w, L * 0.6, w), top - (0, L * 0.3, 0), G.ry(45), ICICLE[0]),
            B.p(name, (w * 0.5, L * 0.5, w * 0.5), top - (0, L * 0.72, 0), G.ry(45), ICICLE[1])]


def shards(B, base, dirs, name="Crystal", neon=True, w=0.8, cols=CRYSTAL, **kw):
    """Crystal shards out of one point: each a bar along its direction (length = the vector's
    length), glowing cyan if neon."""
    base = np.asarray(base, float)
    out = []
    for k, d in enumerate(dirs):
        d = np.asarray(d, float)
        mat = dict(material="Neon", lamp=True, flicker=0.08) if neon else {}
        mat.update(kw)
        out.append(bar(B, name, base - d / np.linalg.norm(d) * 0.3, base + d, w * (1.0 - 0.15 * k), cols[k % len(cols)],
                       t=w * (0.9 - 0.12 * k), **mat))
    return out


def snowflake(B, c, R, s, name="Snowflake", col="ffffff"):
    """A snowflake on a face whose outward normal is R's -Z: three thin bars crossing at 60 degrees,
    each a hair thicker than the last."""
    c = np.asarray(c, float)
    return [B.p(name, (0.28 * s, s, 0.1 + 0.02 * k), c + R @ (0, 0, -0.08), R @ G.rz(60 * k), col) for k in range(3)]


# ==================================================================== the hero

def tower(B, x, z, sx):
    """One round ice tower at (x, z); sx is the side it stands on (-1 left, +1 right)."""
    c = np.array((x, 0.0, z))
    octo(B, "Tower", c + (0, 0.8, 0), 12.4, 12.4, 1.6, PLINTH, solid=True)
    for k, (w, y0, h) in enumerate(((10.6, 1.6, 8.0), (10.2, 9.6, 8.0), (9.8, 17.6, 7.4))):
        octo(B, "Tower", c + (0, y0 + h / 2, 0), w, w, h, DRUMS[k], solid=True)
    top = 25.0
    octo(B, "Battlement", c + (0, top + 0.7, 0), 12.4, 12.4, 1.4, (SNOW[2], SNOW[2], SNOW[0]), solid=True)
    for i, (m, n, _w) in enumerate(facets(12.4, 12.4)):
        B.p("Battlement", (1.9, 1.8, 1.1), c + (m[0], top + 1.4 + 0.9, m[1]) - n * 0.62, facing(n),
            (SNOW[1], ICE[2])[i % 2])
    # the stepped spire and the crystal on its tip
    y = top + 1.2
    for k, (w, h) in enumerate(((8.4, 2.6), (6.6, 2.4), (4.8, 2.3), (3.0, 2.2), (1.5, 1.8))):
        B.p("Roof", (w, h, w), c + (0, y + h / 2, 0), G.ry(22.5 + 45 * (k % 2)), ROOF[(0, 2)[k % 2]])
        y += h - 0.05
    B.p("Crystal", (1.0, 2.8, 1.0), c + (0, y + 1.1, 0), ori(0, 45, 0), CRYSTAL[0], material="Neon", flicker=0.1,
        lamp=True)
    B.p("Crystal", (0.6, 1.6, 0.6), c + (sx * 0.5, y + 0.4, -0.3), ori(18, 30, -sx * 24), CRYSTAL[1], material="Neon",
        flicker=0.1, lamp=True)
    # crystals growing out of the battlement on the outer front
    d = np.array((sx * 0.924, 0.0, -0.383))
    shards(B, c + d * 5.1 + (0, top + 1.5, 0), (d * 1.0 + (0, 2.6, 0), d * 1.8 + (0, 1.4, 0) + (0, 0, -0.6),
                                                  d * 0.4 + (0, 1.8, 0) + (0, 0, 0.9)))
    # icicles under the overhanging ring
    for k, (fi, along, L) in enumerate(((0, -2.8 * sx, 1.6), (1, 0.4, 2.4), (7, -0.3, 2.0),
                                        (2 if sx < 0 else 6, 0.5, 2.6))):
        m, n, _w = facets(12.4, 12.4)[fi]
        t = np.cross((0.0, 1.0, 0.0), n)
        icicle(B, c + (m[0], top + 0.02, m[1]) - n * 0.55 + t * along, L)
    # a banner hanging on the front, a slit window on the outer front
    fz = z - 4.9
    bar(B, "Banner", (x - 2.2, 24.3, fz - 0.4), (x + 2.2, 24.3, fz - 0.4), 0.3, GOLD[0])
    B.p("Banner", (3.0, 5.7, 0.2), (x, 21.35, fz - 0.3), None, BANNER[0])
    B.p("Banner", (2.12, 2.12, 0.16), (x, 18.5, fz - 0.3), G.rz(45), BANNER[1])
    snowflake(B, (x, 21.7, fz - 0.4), np.eye(3), 2.4)
    m, n, _w = facets(10.2, 10.2)[1 if sx < 0 else 7]
    R = facing(n)
    p = c + (m[0], 13.2, m[1])
    B.plate("Window", (1.0, 3.6, 0.12), p + R @ (0, 0, -0.06), R, col=DEEP[0])
    B.p("Window", (1.9, 0.5, 0.6), p + R @ (0, 2.05, -0.25), R, SNOW[1])
    B.p("Window", (1.9, 0.4, 0.7), p + R @ (0, -2.0, -0.3), R, SNOW[0])
    icicle(B, p + R @ (0.35 * sx, -2.18, -0.45), 1.3, w=0.42)


def gate(B):
    """The gatehouse between the towers: piers of big ice blocks, the arch, the portcullis, the
    walkway with its merlons, icicles."""
    zf, zb = -1.0, 5.0
    D = zb - zf
    zc = (zf + zb) / 2
    for sx in (-1, 1):
        B.p("Wall", (5.8, 9.0, D), (sx * 7.3, 4.5, zc), None, ICE[1], solid=True)
        B.p("Wall", (5.8, 9.0, D - 0.12), (sx * 7.3, 13.5, zc + 0.06), None, ICE[0], solid=True)
    B.p("Wall", (9.2, 5.56, D - 0.1), (0.0, 12.4 + 2.78, zc + 0.03), None, ICE[2], solid=True)
    B.p("Passage", (8.8, 12.4, 1.0), (0.0, 6.2, zb - 0.5), None, DEEP[0], solid=True)
    # the walkway on top, merlons along its front
    B.p("Walk", (21.0, 1.2, D + 1.4), (0.0, 18.6, zc - 0.2), None, SNOW[0], solid=True)
    for k, x in enumerate((-8.8, -5.4, 5.4, 8.8)):
        B.p("Merlon", (2.0, 2.0, 1.2), (x, 20.2, zf - 0.3), None, (SNOW[1], ICE[2])[k % 2])
    # the arch: its top corners cut off, a white trim following the opening, a glowing crystal keystone
    for sx in (-1, 1):
        B.p("Arch", (3.4, 3.4, D - 0.3), (sx * 4.4, 12.4, zc + 0.1), G.rz(45), ICE[2])
        B.p("Arch", (0.9, 10.3, 0.3), (sx * 4.85, 5.15, zf - 0.15), None, SNOW[1])
        bar(B, "Arch", (sx * 4.72, 10.32, zf - 0.15), (sx * 2.32, 12.72, zf - 0.15), 0.9, SNOW[0], t=0.34, over=0.32,
            n=(0, 0, -1))
    B.p("Arch", (4.64, 0.9, 0.3), (0.0, 12.85, zf - 0.15), None, SNOW[1])
    B.p("Keystone", (1.5, 1.5, 0.4), (0.0, 13.5, zf - 0.42), G.rz(45), CRYSTAL[0], material="Neon", flicker=0.1,
        lamp=True)
    # the portcullis, half raised: bars with spiked feet, cross bars in front
    pz = 0.4
    for k in range(5):
        x = -3.4 + 1.7 * k
        B.p("Portcullis", (0.42, 7.6, 0.42), (x, 8.6, pz), None, IRON[0])
        B.p("Portcullis", (0.42, 0.42, 0.36), (x, 4.8, pz), G.rz(45), IRON[1])
    for k, y in enumerate((6.0, 8.6, 11.2)):
        B.p("Portcullis", (8.6, 0.36, 0.36), (0.0, y, pz - 0.39), None, IRON[1])
    # icicles under the walkway and the arch
    for k, (x, L) in enumerate(((-9.1, 2.2), (-6.9, 1.5), (-2.6, 2.6), (2.9, 1.8), (6.6, 2.4), (8.9, 1.6))):
        icicle(B, (x, 18.02, zf - 0.45), L, w=0.62)
    for k, (x, L) in enumerate(((-1.5, 1.6), (0.3, 1.1), (1.8, 1.8))):
        icicle(B, (x, 12.42, zf + 0.3), L, w=0.5)
    # a step of ice up to the gate
    B.p("Step", (10.0, 0.5, 2.4), (0.0, 0.25, zf - 1.25), None, ICE[0], solid=True)


def king(B, c0):
    """The frozen statue of the potato king on its plinth: a golden crown with a crystal in it, a
    royal blue stole, one hand raising a crystal sceptre."""
    c0 = np.asarray(c0, float)
    B.p("Plinth", (4.8, 1.4, 4.2), c0 + (0, 0.7, 0), None, ICE[1])
    B.p("Plinth", (5.2, 0.4, 4.6), c0 + (0, 1.6, 0), None, SNOW[1])
    s = 6.2
    c = c0 + (0, 1.8 + s / 2, 0)
    potato(B, c, s, (ICE[2], ICE[0], SNOW[1]), name="King", eyes=DEEP[1], glints=True)
    hy = c[1] + s / 2
    B.p("Crown", (s * 0.8, 0.9, s * 0.72), (c[0], hy + 0.3, c[2]), None, GOLD[0])
    for k, (dx, dz) in enumerate(((-1.8, -1.5), (0.0, -1.7), (1.8, -1.5), (-1.8, 1.4), (1.8, 1.4))):
        B.p("Crown", (0.75, 1.0, 0.75), (c[0] + dx, hy + 1.1 + 0.04 * k, c[2] + dz), G.ry(45), GOLD[1 + k % 2])
    B.p("Crown", (0.62, 0.62, 0.2), (c[0], hy + 0.3, c[2] - s * 0.36 - 0.06), G.rz(45), CRYSTAL[0], material="Neon",
        flicker=0.1, lamp=True)
    B.p("Stole", (s * 0.92, s * 0.16, s * 0.84), c + (0, -s * 0.3, 0), None, BANNER[0])
    B.p("Stole", (s * 0.94, s * 0.07, s * 0.86), c + (0, -s * 0.19, 0), None, SNOW[1])
    sh = c + (s * 0.4, -0.02 * s, -0.1)
    hand = c + (s * 0.64, s * 0.16, -s * 0.36)
    bar(B, "King", sh, hand, s * 0.15, ICE[0])
    bar(B, "Sceptre", hand + (0, -1.5, 0), hand + (0, 2.5, 0), 0.32, GOLD[0])
    B.p("Sceptre", (0.95, 1.4, 0.95), hand + (0, 3.15, 0), ori(0, 45, 0), CRYSTAL[0], material="Neon", flicker=0.1,
        lamp=True)
    bar(B, "King", c + (-s * 0.4, -0.02 * s, 0), c + (-s * 0.58, -s * 0.3, -s * 0.22), s * 0.15, ICE[0])


def hero(sc, parent):
    B = Build(sc, parent, "Frost", seed=401)
    for sx in (-1, 1):
        tower(B, sx * 14.5, 2.0, sx)
    gate(B)
    king(B, (0.0, 19.2, 1.4))
    for k, (x, z, w, d, h, ht) in enumerate(((-8.2, -3.0, 5.4, 3.2, 12, 1.3), (8.6, -2.8, 4.6, 2.8, -14, 1.1),
                                             (-19.0, -5.4, 5.2, 3.4, 28, 1.5), (19.2, -5.0, 4.8, 3.0, -22, 1.3))):
        B.p("Snow", (w, ht, d), (x, ht / 2, z), G.ry(h), SNOW[k % 3])
    for sx in (-1, 1):
        shards(B, (sx * 6.3, 0.45, -2.9), ((sx * 0.5, 2.6, -0.4), (sx * 1.5, 1.5, -0.6)), w=0.9)
    return B.finish()


# ==================================================================== props

def p_igloo(sc, parent):
    B = Build(sc, parent, "Igloo", seed=411)
    y = 0.0
    for k, (w, h) in enumerate(((8.6, 2.0), (7.6, 1.9), (6.0, 1.8), (3.8, 1.5))):
        round3(B, "Igloo", (0.0, y + h / 2, 0.8), w, h, w, (SNOW[k % 2], SNOW[2], ICE[2] if k % 2 else SNOW[0]),
               R=G.ry(22.5 * (k % 2)))
        y += h - 0.05
    B.p("Tunnel", (3.6, 2.9, 3.2), (0.0, 1.45, -3.6), None, SNOW[0])
    B.p("Tunnel", (4.0, 0.6, 3.4), (0.0, 3.1, -3.6), None, SNOW[2])
    B.p("Door", (2.0, 1.9, 0.12), (0.0, 0.95, -5.26), None, "ffd27a", material="Neon", flicker=0.08, lamp=True)
    B.p("Door", (1.4, 0.56, 0.14), (0.0, 2.16, -5.24), None, "ffc45a", material="Neon", flicker=0.08, lamp=True)
    for k, (x, z, s) in enumerate(((3.4, -3.6, 1.1), (-3.0, -4.2, 0.9))):
        B.p("Snow", (s, s * 0.8, s), (x, s * 0.4, z), ori(0, 25 * k + 10, 0), SNOW[k % 3])
    return B.finish()


def p_sled(sc, parent):
    B = Build(sc, parent, "SledPresents", seed=412)
    for sx in (-1, 1):
        x = sx * 1.25
        B.p("Runner", (0.32, 0.3, 5.6), (x, 0.15, 0.2), None, RED[0])
        bar(B, "Runner", (x, 0.15, -2.6), (x, 1.2, -3.2), 0.3, RED[1], t=0.3, over=0.1)
        bar(B, "Runner", (x, 1.2, -3.2), (x, 1.5, -2.7), 0.27, RED[2], t=0.3, over=0.1)
        for z in (-1.6, 1.8):
            B.p("Runner", (0.26, 0.72, 0.26), (x, 0.66, z), None, WOOD[0])
    for k in range(3):
        B.p("Sled", (3.0, 0.28 + 0.02 * (k % 2), 1.36), (0.0, 1.15, -1.5 + 1.42 * k), None, WOOD[2 + (k % 2)])
    presents = (((0.0, 1.29, 0.4), (2.2, 1.8, 2.0), "e8403a", GOLD[0], 8),
                ((-0.2, 3.09, 0.3), (1.6, 1.4, 1.5), "4fa83a", "e8403a", -14),
                ((0.15, 4.49, 0.25), (1.1, 1.0, 1.1), "3b8bff", "ffffff", 20))
    for k, (p, size, col, rib, h) in enumerate(presents):
        p = np.asarray(p, float) + (0, size[1] / 2, 0)
        R = G.ry(h)
        B.p("Present", size, p, R, col)
        B.p("Present", (size[0] + 0.06, size[1] + 0.04, 0.36), p, R, rib)
        B.p("Present", (0.36, size[1] + 0.08, size[2] + 0.06), p, R, rib)
        if k == 2:
            for sx in (-1, 1):
                B.p("Present", (0.62, 0.42, 0.285 + 0.025 * sx), p + R @ (sx * 0.3, size[1] / 2 + 0.2, 0.0),
                    R @ G.rz(sx * 30), rib)
    bar(B, "Rope", (-1.25, 1.5, -2.7), (0.0, 0.25, -5.0), 0.16, "c8a070")
    bar(B, "Rope", (1.25, 1.5, -2.7), (0.0, 0.25, -5.0), 0.16, "b89060")
    return B.finish()


def p_penguin(sc, parent):
    B = Build(sc, parent, "PenguinStatue", seed=413)
    B.p("Plinth", (3.8, 1.4, 3.6), (0.0, 0.7, 0.0), None, ICE[1])
    B.p("Plinth", (4.2, 0.4, 4.0), (0.0, 1.6, 0.0), None, SNOW[1])
    B.p("Plinth", (1.6, 0.5, 1.2), (1.3, 2.05, 1.2), G.ry(20), SNOW[0])
    s = 3.8
    c = np.array((0.0, 1.8 + s / 2 + 0.3, 0.0))
    black = ("2b2b33", "1e1e26", "3a3a44")
    round3(B, "Penguin", c, s * 0.86, s, s * 0.78, black)
    zf = c[2] - s * 0.39
    B.p("Belly", (s * 0.6, s * 0.72, 0.16), (0.0, c[1] - s * 0.08, zf - 0.06), None, "f6f6f6")
    for sx in (-1, 1):
        B.plate("Eye", (0.42, 0.62, 0.1), (sx * 0.62, c[1] + s * 0.14, zf - 0.19))
        B.plate("Eye", (0.18, 0.18, 0.1), (sx * 0.62 + 0.08, c[1] + s * 0.14 + 0.17, zf - 0.23), col="ffffff")
        B.plate("Cheek", (0.5, 0.24, 0.1), (sx * 0.98, c[1] - s * 0.02, zf - 0.18), col="ff9aa8")
        B.p("Flipper", (0.5, s * 0.6, s * 0.4), c + (sx * s * 0.47, -s * 0.06, 0.1), G.rz(sx * 18), black[1])
        B.p("Foot", (1.1, 0.4, 1.3), (sx * 0.75, 2.0 + 0.1, zf + 0.2), G.ry(sx * 12), "ff8a1f")
    B.p("Beak", (0.7, 0.36, 0.6), (0.0, c[1] - s * 0.02, zf - 0.38), None, "ff8a1f")
    B.p("Beak", (0.5, 0.2, 0.44), (0.0, c[1] - s * 0.11, zf - 0.31), None, "f07412")
    B.p("Scarf", (s * 0.9, 0.55, s * 0.82), c + (0, -s * 0.33, 0), None, RED[0])
    B.p("Scarf", (0.6, 1.4, 0.3), c + (s * 0.24, -s * 0.47, -s * 0.43), G.rz(-10), RED[1])
    B.p("Hat", (s * 0.6, 0.5, s * 0.56), c + (0, s * 0.5 + 0.2, 0), None, RED[0])
    B.p("Hat", (0.7, 0.7, 0.7), c + (0.3, s * 0.5 + 0.75, 0.0), ori(35.26, 45, 0), "ffffff")
    return B.finish()


def p_crystals(sc, parent):
    B = Build(sc, parent, "IceCrystals", seed=414)
    B.p("Snow", (3.6, 0.5, 3.0), (0.0, 0.25, 0.0), G.ry(15), SNOW[0])
    B.p("Snow", (2.4, 0.42, 2.6), (0.6, 0.45, 0.4), G.ry(55), SNOW[2])
    for k, (d, L, w) in enumerate((((0.1, 1.0, -0.1), 4.4, 1.1), ((0.6, 0.8, -0.4), 3.2, 0.9),
                                    ((-0.7, 0.7, 0.2), 3.0, 0.85), ((0.3, 0.7, 0.8), 2.4, 0.8),
                                    ((-0.4, 0.6, -0.8), 2.0, 0.7))):
        d = np.asarray(d, float)
        d /= np.linalg.norm(d)
        base = np.array((0.15 * k - 0.3, 0.3, 0.1 * k - 0.2))
        tip = base + d * L
        bar(B, "Crystal", base, tip, w, ("8ec8f8", "a6d4fb", "74b8f4")[k % 3], t=w * 0.92)
        bar(B, "Crystal", tip - d * 0.5, tip + d * 0.6, w * 0.62, CRYSTAL[k % 3], t=w * 0.6, material="Neon",
            flicker=0.08, lamp=True)
    return B.finish()


def p_fountain(sc, parent):
    B = Build(sc, parent, "FrozenFountain", seed=415)
    round3(B, "Basin", (0.0, 0.8, 0.0), 7.4, 1.6, 7.4, ("a3a0b8", "8e89a0", "b9b4c8"))
    B.p("Ice", (5.8, 0.2, 5.8), (0.0, 1.62, 0.0), G.ry(22.5), "e8f8ff")
    B.p("Column", (1.2, 3.0, 1.2), (0.0, 3.1, 0.0), G.ry(45), ICE[0])
    B.p("Bowl", (3.2, 0.7, 3.2), (0.0, 4.75, 0.0), None, ICE[1])
    B.p("Bowl", (3.0, 0.66, 3.0), (0.0, 4.75, 0.0), G.ry(45), ICE[0])
    B.p("Spray", (0.7, 2.2, 0.7), (0.0, 6.2, 0.0), G.ry(45), ICICLE[0])
    B.p("Spray", (0.4, 1.0, 0.4), (0.0, 7.6, 0.0), G.ry(20), CRYSTAL[1], material="Neon", flicker=0.08, lamp=True)
    for k in range(4):
        a = math.radians(45 + 90 * k)
        d = np.array((math.cos(a), 0.0, math.sin(a)))
        bar(B, "Spray", np.array((0.0, 5.2, 0.0)) + d * 1.4, np.array((0.0, 1.75, 0.0)) + d * 2.5, 0.36 + 0.02 * k,
            ICICLE[k % 2])
    for k in range(4):
        a = math.radians(90 * k)
        d = np.array((math.cos(a), 0.0, math.sin(a)))
        icicle(B, np.array((0.0, 4.4, 0.0)) + d * 1.4, 1.2 + 0.25 * (k % 2), w=0.4)
    return B.finish()


def p_fort(sc, parent):
    B = Build(sc, parent, "SnowFort", seed=416)
    for row in range(2):
        n = 5 - row
        for k in range(n):
            a = math.radians(-36 + 18 * k + 9 * row)
            r = 6.0
            if row == 1 and k == 2:
                continue
            hh = 1.4 + 0.05 * (k % 2)
            y0 = 1.38 * row + 0.03 * (k % 2) * row
            p = np.array((math.sin(a) * r, y0 + hh / 2, 6.0 - math.cos(a) * r - 1.0))
            B.p("Fort", (2.1, hh, 1.6 - 0.04 * (k % 2)), p, G.ry(-math.degrees(a) + 3 * (-1) ** k),
                (SNOW[0], "d4e8fb", ICE[0])[(k + row) % 3])
    for k, (x, z, s) in enumerate(((-1.4, -2.4, 0.9), (-0.4, -2.6, 0.95), (-0.9, -2.5, 0.85), (0.9, -2.2, 0.8),
                                   (1.9, -2.6, 0.9))):
        y = s / 2 if k != 2 else 0.95 + s / 2
        if k == 2:
            z += 0.1
        B.p("Snowball", (s, s, s), (x, y, z), ori(20, 30 * k, 15), SNOW[k % 2])
        B.p("Snowball", (s * 0.8, s * 1.02, s * 0.8), (x, y, z), ori(-15, 30 * k + 45, -10), SNOW[(k + 1) % 2])
    bar(B, "Flag", (2.6, 2.0, 0.2), (2.7, 5.4, 0.2), 0.16, WOOD[0])
    B.p("Flag", (1.6, 1.0, 0.1), (3.5, 4.9, 0.2), None, RED[0])
    bar(B, "Shovel", (-3.2, 0.2, -0.6), (-3.6, 3.6, -0.4), 0.22, WOOD[2])
    B.p("Shovel", (1.0, 1.2, 0.14), (-3.15, 0.55, -0.62), G.rz(-6), "3b8bff")
    return B.finish()


def p_lamp(sc, parent):
    B = Build(sc, parent, "SnowLamp", seed=417)
    iron = ("2b3550", "39446a")
    B.p("Lamp", (1.5, 0.5, 1.5), (0.0, 0.25, 0.0), G.ry(45), iron[0])
    B.p("Lamp", (1.0, 0.6, 1.0), (0.0, 0.8, 0.0), None, iron[1])
    B.p("Lamp", (0.5, 6.4, 0.5), (0.0, 4.3, 0.0), None, iron[0])
    B.p("Lamp", (0.9, 0.4, 0.9), (0.0, 7.55, 0.0), G.ry(45), iron[1])
    B.p("Lamp", (1.4, 0.24, 1.4), (0.0, 7.85, 0.0), None, iron[0])
    B.p("Light", (1.0, 1.4, 1.0), (0.0, 8.67, 0.0), None, "ffd27a", material="Neon", flicker=0.08, lamp=True)
    for sx in (-1, 1):
        for sz in (-1, 1):
            B.p("Lamp", (0.16, 1.44, 0.16), (sx * 0.58, 8.67, sz * 0.58), None, iron[0])
    B.p("Lamp", (1.7, 0.3, 1.7), (0.0, 9.52, 0.0), G.ry(45), iron[1])
    B.p("Lamp", (1.1, 0.5, 1.1), (0.0, 9.9, 0.0), None, iron[0])
    B.p("Snow", (2.0, 0.5, 1.9), (0.08, 10.35, -0.05), ori(0, 20, 3), SNOW[1])
    B.p("Snow", (1.3, 0.45, 1.2), (-0.1, 10.7, 0.08), ori(0, 50, -4), SNOW[0])
    B.p("Snow", (1.6, 0.3, 1.5), (0.0, 7.98, 0.0), ori(0, 30, 0), SNOW[2])
    B.p("Wreath", (1.3, 1.3, 0.3), (0.0, 5.6, -0.4), G.rz(45), "3f9e3c")
    B.p("Wreath", (1.3, 1.3, 0.32), (0.0, 5.6, -0.4), None, "55b848")
    B.p("Wreath", (0.7, 0.45, 0.3), (0.0, 5.05, -0.62), None, RED[0])
    for k, (x, z, s) in enumerate(((0.9, -0.9, 1.0), (-1.0, 0.6, 0.8))):
        B.p("Snow", (s * 1.4, s * 0.6, s), (x, s * 0.3, z), G.ry(30 * k + 15), SNOW[k % 3])
    return B.finish()


def p_skis(sc, parent):
    B = Build(sc, parent, "SkiStand", seed=418)
    B.p("Snow", (3.8, 1.2, 2.8), (0.0, 0.6, 0.0), G.ry(10), SNOW[0])
    B.p("Snow", (2.6, 0.9, 2.2), (0.4, 1.3, 0.2), G.ry(40), SNOW[2])
    B.p("Snow", (1.6, 0.6, 1.4), (-0.3, 1.9, 0.1), G.ry(70), SNOW[1])
    for k, (x, rz, col) in enumerate(((-0.55, 8.0, RED[0]), (0.55, -6.0, "3b8bff"))):
        R = G.rz(rz) @ G.rx(-6)
        base = np.array((x, 0.9, 0.2))
        B.p("Ski", (0.6, 6.4, 0.18), base + R @ (0, 3.2, 0), R, col)
        B.p("Ski", (0.56, 0.8, 0.18), base + R @ (0, 6.55, -0.2), R @ G.rx(-30), col)
        B.p("Ski", (0.64, 0.5, 0.24), base + R @ (0, 3.0, 0), R, "ffffff")
    for k, (a, b) in enumerate((((-1.6, 0.8, -0.4), (0.9, 5.0, -0.7)), ((1.7, 0.8, -0.3), (-0.8, 5.1, -0.8)))):
        a, b = np.asarray(a, float), np.asarray(b, float)
        bar(B, "Pole", a, b, 0.16, "c8ccd4")
        d = (b - a) / np.linalg.norm(b - a)
        B.p("Pole", (0.3, 0.8, 0.3), b - d * 0.3, G.rz(-math.degrees(math.atan2(d[0], d[1]))), INK)
        B.p("Pole", (0.7, 0.1, 0.7), a + d * 0.6, G.ry(45 * k), INK)
    B.p("Hat", (1.1, 0.7, 1.1), (0.95, 5.35, -0.7), ori(0, 20, -10), RED[0])
    B.p("Hat", (1.2, 0.3, 1.2), (0.95, 5.0, -0.7), ori(0, 20, -10), "ffffff")
    B.p("Hat", (0.5, 0.5, 0.5), (0.85, 5.85, -0.7), ori(35.26, 45, 0), "ffffff")
    return B.finish()


AREA = register(Area("Frost", "Frost Fields", hero, [
    (p_igloo, prop_attrs(3, 0.9, 1.2, "Side", True)),
    (p_sled, prop_attrs(4, 0.9, 1.2, "Any", False)),
    (p_penguin, prop_attrs(3, 0.9, 1.2, "Side", True)),
    (p_crystals, prop_attrs(8, 0.8, 1.4, "Any", False)),
    (p_fountain, prop_attrs(2, 0.9, 1.15, "Side", True)),
    (p_fort, prop_attrs(4, 0.9, 1.2, "Edge", True)),
    (p_lamp, prop_attrs(6, 0.95, 1.15, "Side", False)),
    (p_skis, prop_attrs(4, 0.9, 1.2, "Side", False)),
], ground="ecf4fc"))
