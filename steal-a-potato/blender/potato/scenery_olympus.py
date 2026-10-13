"""Spud Olympus: the hero, a temple with a potato Zeus, and the area's props.

A marble temple on three steps, rising out of clouds: six columns across the front with gold
capitals (the middle pair set wide), an architrave and a frieze of gold squares, a stepped pediment
with a glowing thunderbolt in it and gold ornaments at its corners, a low roof, the cella wall with
a dark doorway behind. Between the middle columns, on a pedestal, the potato Zeus: marble, a white
beard and brows, a gold laurel crown, one arm raising a glowing thunderbolt. Gold braziers burn on
the steps; two olive trees and clouds round the foot.
"""
import math

import numpy as np

import spsgeo as G

from .scenery import (Area, Build, INK, FLAME, bar, flame, ori, potato, prop_attrs, register, round3, shade, tree)
from .scenery_cloud import puff

MARBLE = ("f0eee8", "e4e0d6", "faf8f2", "d8d2c4")
GOLD = ("f5c518", "e0a800", "ffd447")
BOLT = "ffe83a"
OLIVE = ("8aa068", "9cb07a", "7a9058")


def column(B, x, z, y0, h, d=2.2, solid=True, name="Column"):
    """A marble column: a square base, an eight-sided shaft (two blocks), a gold capital and its
    abacus."""
    out = [B.p(name, (d + 0.8, 0.7, d + 0.8), (x, y0 + 0.35, z), None, MARBLE[1], solid=solid)]
    sh = h - 0.7 - 1.3
    out.append(B.p(name, (d, sh, d), (x, y0 + 0.7 + sh / 2, z), None, MARBLE[0], solid=solid))
    out.append(B.p(name, (d - 0.02, sh - 0.04, d - 0.02), (x, y0 + 0.7 + sh / 2, z), G.ry(45), MARBLE[2], solid=solid))
    out.append(B.p(name, (d + 0.6, 0.7, d + 0.6), (x, y0 + 0.7 + sh + 0.35, z), G.ry(45), GOLD[0]))
    out.append(B.p(name, (d + 1.0, 0.6, d + 1.0), (x, y0 + h - 0.3, z), None, MARBLE[2], solid=solid))
    return out


def bolt(B, base, s=1.0, name="Thunderbolt", R=None):
    """A glowing zigzag thunderbolt pointing up from base."""
    R = np.eye(3) if R is None else R
    base = np.asarray(base, float)
    pts = [base + R @ (np.array(p) * s) for p in ((0.0, 0.0, 0.0), (-0.7, 1.9, 0.0), (0.5, 2.3, 0.0), (-0.3, 4.4, 0.0))]
    out = []
    for k in range(3):
        out.append(bar(B, name, pts[k], pts[k + 1], (0.62 - 0.1 * k) * s, BOLT, t=(0.4 + 0.06 * k) * s, over=0.2 * s,
                       n=R @ (0, 0, -1), material="Neon", flicker=0.15, lamp=True))
    return out


def zeus(B, c, s, R=None, name="Zeus", skin=("f0d8b8", "dcc09a", "f8e6cc")):
    """The potato Zeus: warm skin, a great white beard, moustache, brows and hair, a gold laurel
    crown, his right arm raising a glowing thunderbolt."""
    R = np.eye(3) if R is None else R
    c = np.asarray(c, float)
    out = potato(B, c, s, skin, R=R, name=name, glints=True, cheeks="ff9aa8")
    for sx in (-1, 1):
        out.append(B.p(name, (s * 0.16, s * 0.5, s * 0.6), c + R @ (sx * s * 0.42, s * 0.1, s * 0.05), R, "ffffff"))
    zf = -s * 0.39 - 0.05
    out.append(B.p(name, (s * 0.62, s * 0.36, 0.3), c + R @ (0, -s * 0.29, zf - 0.08), R, "ffffff"))
    out.append(B.p(name, (s * 0.42, s * 0.2, 0.32), c + R @ (0, -s * 0.5, zf - 0.04), R, "f4f4f8"))
    out.append(B.p(name, (s * 0.46, s * 0.07, 0.34), c + R @ (0, -s * 0.06, zf - 0.12), R, "ffffff"))
    for sx in (-1, 1):
        out.append(B.p(name, (s * 0.2, s * 0.06, 0.14), c + R @ (sx * s * 0.17, s * 0.27, zf - 0.04), R @ G.rz(-sx * 8),
                       "ffffff", material="SmoothPlastic", shadow=False))
    out.append(B.p(name, (s * 0.94, s * 0.1, s * 0.86), c + R @ (0, s * 0.43, 0), R, GOLD[1]))
    for k in range(4):
        a = math.radians(-60 + 40 * k)
        out.append(B.p(name, (s * 0.24, s * 0.08, s * 0.12), c + R @ (math.sin(a) * s * 0.42, s * 0.47, -math.cos(a) * s * 0.4),
                       R @ G.ry(-math.degrees(a)) @ G.rz(25), GOLD[(k % 2) * 2]))
    sh = c + R @ (s * 0.36, s * 0.05, -s * 0.2)
    hand = c + R @ (s * 0.42, s * 0.56, -s * 0.5)
    out.append(bar(B, name, sh, hand, s * 0.15, skin[1]))
    out += bolt(B, hand + R @ (0, s * 0.02, -0.25), s * 0.16, R=R)
    out.append(bar(B, name, c + R @ (-s * 0.42, s * 0.05, 0), c + R @ (-s * 0.55, -s * 0.3, -s * 0.12), s * 0.15,
                   skin[1]))
    return out


# ==================================================================== the hero

def hero(sc, parent):
    B = Build(sc, parent, "Olympus", seed=191)
    # clouds round the foot
    for k, (x, z, s, h) in enumerate(((-16.0, -9.0, 4.0, 10.0), (16.4, -8.6, 3.6, 40.0), (-17.6, 4.0, 3.4, 70.0),
                                      (17.4, 5.0, 3.6, 20.0), (0.0, 11.5, 4.6, 55.0))):
        puff(B, (x, 0.0, z), s, heading=h)
    # three marble steps
    for k in range(3):
        B.p("Step", (38.0 - 2.2 * k, 1.0, 22.0 - 2.2 * k), (0.0, 0.5 + 1.0 * k, 1.0 + 0.0 * k), None, MARBLE[k % 2 + 1],
            solid=True)
    y0 = 3.0
    zf = 1.0 - (22.0 - 4.4) / 2 + 1.6
    # the cella wall and its doorway
    B.p("Cella", (22.0, 13.0, 9.0), (0.0, y0 + 6.5, 4.0), None, MARBLE[1], solid=True)
    B.plate("Door", (5.0, 8.0, 0.12), (0.0, y0 + 4.0, -0.56), col="3a3026")
    # the columns across the front, the middle pair set wide; four more down each side
    H = 14.0
    for x in (-15.0, -9.8, -4.6, 4.6, 9.8, 15.0):
        column(B, x, zf, y0, H)
    for x in (-15.0, 15.0):
        for z in (zf + 5.4, zf + 10.8):
            column(B, x, z, y0, H)
    # architrave, frieze with gold squares, cornice
    yt = y0 + H
    B.p("Architrave", (33.4, 1.4, 16.4), (0.0, yt + 0.7, zf + 7.0), None, MARBLE[0], solid=True)
    B.p("Frieze", (33.0, 1.6, 16.0), (0.0, yt + 2.2, zf + 7.0), None, MARBLE[2], solid=True)
    for k in range(7):
        B.p("Frieze", (1.4, 1.2, 0.12), (-12.0 + 4.0 * k, yt + 2.2, zf - 1.06), None, GOLD[k % 2])
    B.p("Cornice", (34.4, 0.8, 17.4), (0.0, yt + 3.4, zf + 7.0), None, MARBLE[1], solid=True)
    # the pediment: steps of marble, a thunderbolt in it, gold at its corners; the roof behind
    yp = yt + 3.8
    for k, (w, h) in enumerate(((30.0, 1.4), (23.0, 1.4), (16.0, 1.4), (9.0, 1.3))):
        B.p("Pediment", (w, h, 1.2), (0.0, yp + 1.4 * k + h / 2, zf - 0.3), None, MARBLE[k % 2 * 2], solid=True)
    for sx in (-1, 1):
        a = math.degrees(math.atan2(5.6, 17.0))
        B.p("Pediment", (18.2, 0.7, 1.6 + 0.04 * (sx > 0)), (sx * 8.4, yp + 2.9, zf - 0.4), G.rz(-sx * a), MARBLE[1])
        B.p("Roof", (18.2, 0.6, 16.6 + 0.04 * (sx > 0)), (sx * 8.4, yp + 2.6, zf + 7.2), G.rz(-sx * a), MARBLE[3],
            solid=True)
        B.p("Acroterion", (1.4, 1.4, 1.4), (sx * 16.6, yp + 0.5, zf - 0.5), ori(0, 45, 0), GOLD[0])
    B.p("Acroterion", (1.6, 1.6, 1.6), (0.0, yp + 6.0, zf - 0.5), ori(35.26, 45, 0), GOLD[2])
    bolt(B, (0.4, yp + 0.4, zf - 1.0), 1.0, R=G.rz(-8))
    # the potato Zeus on his pedestal between the middle columns
    B.p("Pedestal", (6.0, 1.6, 4.4), (0.0, y0 + 0.8, zf + 0.8), None, MARBLE[1], solid=True)
    B.p("Pedestal", (5.2, 0.5, 3.8), (0.0, y0 + 1.85, zf + 0.8), None, GOLD[1])
    s = 7.4
    zeus(B, (0.0, y0 + 2.1 + s / 2, zf + 0.8), s)
    # gold braziers on the steps, olive trees at the back corners
    for sx in (-1, 1):
        bx, bz = sx * 12.4, zf - 4.2
        B.p("Brazier", (0.7, 3.4, 0.7), (bx, 1.0 + 1.7, bz), None, GOLD[1])
        B.p("Brazier", (2.0, 0.8, 2.0), (bx, 1.0 + 3.8, bz), G.ry(45), GOLD[0])
        flame(B, (bx, 1.0 + 4.8, bz), 1.2)
    for sx in (-1, 1):
        tree(B, (sx * 17.4, 0.0, 9.0), ("8a7a60", "7a6a50"), OLIVE, h=7.0, canopy=(4.4, 3.4, 3.4), branches=1,
             w=(1.4, 1.2, 1.0), name="OliveTree")
    return B.finish()


# ==================================================================== props

def p_column(sc, parent):
    B = Build(sc, parent, "BrokenColumn", seed=201)
    B.p("Column", (3.2, 0.8, 3.2), (0.0, 0.4, 0.0), None, MARBLE[1])
    for k, h in enumerate((3.0, 2.4)):
        y = 0.8 + 3.0 * k + h / 2
        R = G.rz(3.0 * k)
        B.p("Column", (2.2, h, 2.2 + 0.04 * k), (0.1 * k, y, 0.0), R, MARBLE[0])
        B.p("Column", (2.18, h - 0.04, 2.18), (0.1 * k, y, 0.0), R @ G.ry(45), MARBLE[2])
    B.p("Column", (2.2, 2.4, 2.2), (2.6, 1.1, -1.2), ori(90, 20, 0), MARBLE[0])
    B.p("Capital", (3.0, 0.76, 3.0), (-2.4, 0.38, -1.4), G.ry(30), GOLD[0])
    B.p("Capital", (3.4, 0.6, 3.4), (-2.4, 1.15, -1.4), G.ry(30), MARBLE[2])
    B.p("Column", (0.8, 0.5, 0.9), (-0.6, 0.25, 2.0), ori(0, 40, 6), MARBLE[2])
    B.p("Column", (1.0, 0.6, 1.2), (1.4, 0.3, 1.6), ori(0, 20, 8), MARBLE[3])
    return B.finish()


def p_olive(sc, parent):
    B = Build(sc, parent, "OliveTree", seed=202)
    tree(B, (0.0, 0.0, 0.0), ("8a7a60", "7a6a50"), OLIVE, h=7.5, canopy=(5.0, 3.8, 3.8, 3.4), branches=2,
         w=(1.6, 1.3, 1.1), fruit=1, fruit_col="4a3a5a", name="OliveTree")
    return B.finish()


def p_amphora(sc, parent):
    B = Build(sc, parent, "Amphora", seed=203)
    terra, black = "d8743a", "2a201c"
    B.p("Amphora", (1.4, 0.5, 1.4), (0.0, 0.25, 0.0), G.ry(45), black)
    round3(B, "Amphora", (0.0, 2.3, 0.0), 2.8, 3.4, 2.8, (terra, "c8642a", "e88a4a"))
    B.p("Amphora", (2.6, 0.5, 2.6), (0.0, 2.6, 0.0), G.ry(22.5), black)
    B.p("Amphora", (1.2, 1.4, 1.2), (0.0, 4.6, 0.0), None, terra)
    B.p("Amphora", (1.6, 0.4, 1.6), (0.0, 5.45, 0.0), G.ry(45), black)
    for sx in (-1, 1):
        bar(B, "Amphora", (sx * 0.5, 5.0, 0.0), (sx * 1.5, 4.4, 0.0), 0.3, black)
        bar(B, "Amphora", (sx * 1.5, 4.4, 0.0), (sx * 1.3, 3.4, 0.0), 0.3, black, t=0.34)
    return B.finish()


def p_brazier(sc, parent):
    B = Build(sc, parent, "GoldBrazier", seed=204)
    for k in range(3):
        a = math.radians(120 * k + 90)
        bar(B, "Brazier", (math.cos(a) * 1.3, 0.0, math.sin(a) * 1.3), (math.cos(a) * 0.4, 3.0, math.sin(a) * 0.4), 0.3,
            GOLD[1])
    B.p("Brazier", (0.8, 3.0, 0.8), (0.0, 1.5, 0.0), None, GOLD[0])
    B.p("Brazier", (2.4, 0.9, 2.4), (0.0, 3.4, 0.0), G.ry(45), GOLD[0])
    B.p("Brazier", (2.6, 0.4, 2.6), (0.0, 3.95, 0.0), None, GOLD[2])
    B.p("Brazier", (1.2, 0.3, 1.2), (0.0, 1.0, 0.0), G.ry(45), GOLD[2])
    flame(B, (0.0, 4.9, 0.0), 1.4)
    B.p("Ember", (1.6, 0.2, 1.6), (0.0, 4.2, 0.0), G.ry(20), FLAME[0], material="Neon", lamp=True)
    return B.finish()


def p_statue(sc, parent):
    B = Build(sc, parent, "HeroStatue", seed=205)
    B.p("Plinth", (3.6, 2.4, 3.6), (0.0, 1.2, 0.0), None, MARBLE[1])
    B.p("Plinth", (4.0, 0.5, 4.0), (0.0, 2.65, 0.0), None, MARBLE[2])
    B.p("Plinth", (2.6, 0.5, 0.12), (0.0, 1.4, -1.86), None, GOLD[0], material="SmoothPlastic", shadow=False)
    s = 3.6
    c = np.array((0.0, 2.9 + s / 2, 0.0))
    potato(B, c, s, MARBLE, name="Statue", glints=True)
    B.p("Statue", (s * 0.94, s * 0.1, s * 0.86), c + (0, s * 0.43, 0), None, GOLD[1])
    bar(B, "Statue", c + (s * 0.42, 0.1, 0), c + (s * 0.68, s * 0.55, -0.2), s * 0.16, MARBLE[1])
    B.p("Discus", (1.2, 0.3, 1.2), c + (s * 0.72, s * 0.72, -0.2), G.rx(80), GOLD[2])
    return B.finish()


def p_laurel(sc, parent):
    B = Build(sc, parent, "LaurelBush", seed=206)
    from .scenery import bush
    bush(B, (0.0, 0.0, 0.0), 3.2, ("4f8a3a", "5e9e44", "6cae52"))
    bush(B, (2.2, 0.0, 0.8), 2.2, ("5e9e44", "4f8a3a", "6cae52"), heading=30)
    for k, (x, y, z) in enumerate(((-0.8, 2.6, -1.2), (0.9, 2.2, -1.3), (2.4, 2.0, -0.4), (-1.4, 1.6, -0.6))):
        B.p("Berry", (0.42, 0.42, 0.42), (x, y, z), G.ry(20 * k), GOLD[k % 2])
    return B.finish()


def p_fountain(sc, parent):
    B = Build(sc, parent, "Fountain", seed=207)
    B.p("Basin", (6.0, 1.2, 6.0), (0.0, 0.6, 0.0), G.ry(22.5), MARBLE[1])
    B.p("Basin", (5.96, 1.16, 5.96), (0.0, 0.6, 0.0), G.ry(67.5), MARBLE[0])
    B.p("Water", (5.0, 0.2, 5.0), (0.0, 1.3, 0.0), G.ry(22.5), "6ac8ff", transparency=0.3)
    B.p("Spout", (1.0, 3.6, 1.0), (0.0, 2.6, 0.0), None, MARBLE[2])
    B.p("Spout", (2.4, 0.5, 2.4), (0.0, 4.6, 0.0), G.ry(45), MARBLE[1])
    B.p("Spout", (1.6, 0.6, 1.6), (0.0, 5.1, 0.0), None, GOLD[0])
    for k in range(4):
        a = math.radians(45 + 90 * k)
        d = np.array((math.cos(a), 0, math.sin(a)))
        bar(B, "Water", np.array((0.0, 4.8, 0.0)) + d * 1.0, np.array((0.0, 1.3, 0.0)) + d * 2.0, 0.3 + 0.03 * k,
            "9ad8ff", transparency=0.35)
    return B.finish()


def p_lyre(sc, parent):
    B = Build(sc, parent, "GoldenLyre", seed=208)
    B.p("Plinth", (3.0, 1.6, 2.2), (0.0, 0.8, 0.0), None, MARBLE[1])
    base = np.array((0.0, 1.6, 0.0))
    B.p("Lyre", (2.4, 0.5, 0.6), base + (0, 0.25, 0), None, GOLD[1])
    for sx in (-1, 1):
        bar(B, "Lyre", base + (sx * 0.9, 0.4, 0), base + (sx * 1.5, 3.0, 0), 0.4, GOLD[0], n=(0, 0, -1))
        bar(B, "Lyre", base + (sx * 1.5, 3.0, 0), base + (sx * 1.1, 4.3, 0), 0.4, GOLD[2], t=0.46, n=(0, 0, -1))
    B.p("Lyre", (2.8, 0.36, 0.5), base + (0, 3.7, 0), None, GOLD[1])
    for k in range(4):
        x = -0.75 + 0.5 * k
        B.p("String", (0.08 + 0.01 * k, 3.2, 0.08), base + (x, 2.1, 0), None, "fff8e0")
    return B.finish()


AREA = register(Area("Olympus", "Spud Olympus", hero, [
    (p_column, prop_attrs(6, 0.85, 1.3, "Side", True)),
    (p_olive, prop_attrs(6, 0.85, 1.25, "Side", True)),
    (p_amphora, prop_attrs(6, 0.8, 1.3, "Side", True)),
    (p_brazier, prop_attrs(5, 0.9, 1.2, "Side", False)),
    (p_statue, prop_attrs(3, 0.9, 1.2, "Side", True)),
    (p_laurel, prop_attrs(8, 0.8, 1.3, "Any", False)),
    (p_fountain, prop_attrs(3, 0.9, 1.2, "Side", True)),
    (p_lyre, prop_attrs(3, 0.9, 1.2, "Side", True)),
], ground="d8e8c0"))
