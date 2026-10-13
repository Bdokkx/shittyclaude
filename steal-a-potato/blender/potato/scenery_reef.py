"""Coral Cove: the hero, a pirate ship run aground with its potato captain, and the area's props.

The ship lies on a sand bank, listing towards the lane so its deck shows, bow up. Planked hull in
two browns with portholes, three cannons run out and a hole stove in near the stern; a stern castle
with lit windows and a lantern; the main mast with a crow's nest, a torn sail and the Jolly Roger at
the top; the foremast snapped and lying across the deck; a gangplank down to the sand (solid, so
players can walk aboard). On deck the captain: a potato in a tricorn hat with an eyepatch, a
cutlass and a parrot. Round it on the sand: an open treasure chest, coral, kelp, starfish, shells
and barrels.
"""
import math

import numpy as np

import spsgeo as G
from spsgeo import CF

from .scenery import (Area, Build, INK, bar, flame, grass, ori, palm, potato, prop_attrs, register, rock,
                      round3, shade, turn)

SAND = ("e8d49a", "f0e0b0", "dcc488", "d0b878")
HULL = ("8a5a2a", "7a4a22", "6e4424", "9a6a36")
DECK = ("c8945a", "b88450")
IRON = ("3a3f4a", "4a505c", "2a2a30")
GOLD = ("f5c518", "e0a800", "ffd447")
CORAL = ("ff7aa8", "ff9f3d", "b46bff", "ff5a6e", "ffc94d")
KELP = ("5a8a3a", "4a7a32", "6e9a44")
PALM_TRUNK = ("c8a070", "b89060", "d8b080")
PALM_LEAF = ("5dbb46", "4fa83a", "7ad155")


def coral(B, base, h, cols, n=3, name="Coral", heading=0.0):
    """A branching coral: a trunk and n branches rising out of it, a knob on each tip."""
    rng = B.rng
    base = np.asarray(base, float)
    top = base + (0, h, 0)
    out = [bar(B, name, base, top, 0.9, cols[0])]
    for k in range(n):
        a = math.radians(heading + 360.0 * k / n + float(rng.uniform(-20, 20)))
        y0 = h * (0.3 + 0.45 * k / max(1, n - 1))
        lean = math.radians(float(rng.uniform(32, 50)))
        L = h * float(rng.uniform(0.5, 0.66))
        s = base + (0, y0, 0)
        e = s + np.array((math.sin(a) * math.sin(lean), math.cos(lean), -math.cos(a) * math.sin(lean))) * L
        out.append(bar(B, name, s, e, 0.78 - 0.04 * k, cols[(k + 1) % len(cols)]))
        out.append(B.p(name, (1.0, 1.0, 1.0), e, ori(20, 45 * k, 15), cols[(k + 1) % len(cols)]))
    out.append(B.p(name, (1.15, 1.15, 1.15), top, ori(15, 30, 10), cols[0]))
    return out


def starfish(B, c, s, col="ff8a3d", heading=0.0, name="Starfish"):
    """Five arms flat on the ground."""
    c = np.asarray(c, float)
    out = []
    for k in range(5):
        a = math.radians(heading + 72 * k)
        d = np.array((math.sin(a), 0.0, -math.cos(a)))
        out.append(bar(B, name, c + d * 0.05, c + d * s, 0.46 * s, (col, shade(col, 0.15))[k % 2], t=0.24 + 0.01 * k,
                       n=(0, 1, 0)))
    return out


def barrel(B, c, R=None, name="Barrel", cols=("9a6a36", "8a5a2a"), band=IRON[1], h=2.2, band_y=0.22):
    """A barrel: a square body, the same turned 45 degrees, an iron band round the middle."""
    R = np.eye(3) if R is None else R
    c = np.asarray(c, float)
    return [B.p(name, (1.5, h, 1.5), c, R, cols[0]),
            B.p(name, (1.5, h - 0.06, 1.5), c, R @ G.ry(45), cols[1]),
            B.p(name, (1.74, h * 0.56, 1.74), c, R @ G.ry(22.5), cols[0]),
            B.p(name, (1.62, 0.2, 1.62), c + R @ (0, h * band_y + 0.28, 0), R @ G.ry(22.5), band),
            B.p(name, (1.62, 0.2, 1.62), c - R @ (0, h * band_y + 0.3, 0), R @ G.ry(22.5), band)]


def chest(B, c, heading=0.0, name="Chest"):
    """An open treasure chest heaped with gold, two gems glowing in it, coins spilled in front."""
    R = G.ry(heading)
    c = np.asarray(c, float)

    def at(v):
        return c + R @ np.asarray(v, float)
    out = [B.p(name, (2.8, 1.5, 1.9), at((0, 0.75, 0)), R, "8a5a2a"),
           B.p(name, (2.86, 0.28, 1.96), at((0, 0.42, 0)), R, IRON[1]),
           B.p(name, (0.36, 1.56, 1.98), at((0, 0.8, 0)), R, GOLD[1]),
           B.p(name, (2.9, 0.42, 2.0), at((0, 1.62 + 0.62, 1.05)), R @ G.rx(-62), "7a4a22"),
           B.p(name, (2.6, 0.4, 1.6), at((0, 1.62, -0.02)), R @ G.rz(4), GOLD[0])]
    for k, (x, z, col) in enumerate(((-0.6, -0.1, GOLD[2]), (0.55, 0.2, GOLD[0]))):
        out.append(B.p(name, (0.9, 0.55, 0.9), at((x, 1.95 + 0.04 * k, z)), R @ ori(10, 30 + 20 * k, 8), col))
    out.append(B.p(name, (0.55, 0.55, 0.55), at((0.15, 2.3, -0.3)), R @ ori(35.26, 45, 0), "ff3b5c", material="Neon",
                   flicker=0.1, lamp=True))
    out.append(B.p(name, (0.45, 0.45, 0.45), at((-0.85, 2.15, 0.35)), R @ ori(35.26, 45, 0), "3b8bff", material="Neon",
                   flicker=0.1, lamp=True))
    for k, (x, z) in enumerate(((-1.6, -1.6), (0.3, -1.85), (1.5, -1.4))):
        out.append(B.p(name, (0.75, 0.16 + 0.02 * k, 0.75), at((x, 0.09 + 0.01 * k, z)), R @ G.ry(25 * k), GOLD[k]))
    return out


def kelp(B, c, n, hgt, cols=KELP, name="Kelp", heading=0.0):
    """Tall swaying fronds, a leaf on each."""
    rng = B.rng
    c = np.asarray(c, float)
    out = []
    for k in range(n):
        a = math.radians(heading + 360.0 * k / n)
        b = c + (0.5 * math.sin(a), 0, -0.5 * math.cos(a))
        h = hgt * float(rng.uniform(0.75, 1.1))
        out_d = np.array((math.sin(a), 0.0, -math.cos(a)))
        mid = b + (0, h * 0.5, 0) + out_d * h * 0.12
        tip = b + (0, h, 0) + out_d * h * 0.06 + np.array((0.0, 0.0, 0.0))
        out.append(bar(B, name, b - (0, 0.2, 0), mid, 0.6 + 0.03 * k, cols[k % len(cols)], t=0.3, n=(0, 0, -1)))
        out.append(bar(B, name, mid - (0, 0.15, 0), tip, 0.52 + 0.03 * k, cols[(k + 1) % len(cols)], t=0.28,
                       n=(0, 0, -1)))
        for j, f in enumerate((0.35, 0.72)):
            m = b + (tip - b) * f
            out.append(B.p(name, (1.3, 0.55, 0.14), m + out_d * 0.45 + (0, 0, -0.1 * j),
                           ori(0, -math.degrees(a), (35 + 10 * j) * (-1) ** (k + j)), cols[(k + j + 2) % len(cols)]))
    return out


# ==================================================================== the hero

def hero(sc, parent):
    B = Build(sc, parent, "Reef", seed=31)
    # the sand bank under it
    for k, (size, pos, h) in enumerate((((34.0, 1.4, 14.0), (1.0, 0.55, -1.5), 3), ((22.0, 1.0, 10.0), (-6.0, 1.3, 3.0), -5),
                                        ((16.0, 1.6, 6.0), (8.0, 0.66, -8.6), 8), ((12.0, 1.2, 6.5), (-12.0, 0.5, -8.4), -6),
                                        ((10.0, 2.0, 7.0), (14.5, 0.95, 6.5), 12))):
        B.p("Sand", size, pos, G.ry(h), SAND[k % 4], solid=True)
    S = CF(np.array((1.4, 1.5, 2.6)), G.rz(-5) @ G.rx(-12))
    with B.at(S):
        ship(B)
    # the gangplank from the rail down to the sand
    top = S * CF(np.array((-6.0, 7.75, -6.3)))
    a, b = top.p, np.array((-7.4, 1.25, -13.3))
    bar(B, "Gangplank", a, b, 2.4, "b88450", t=0.35, n=(0, 1, 0), solid=True)
    d = (b - a) / np.linalg.norm(b - a)
    for k in (0.25, 0.5, 0.75):
        p = a + (b - a) * k + np.array((0, 0.25, 0))
        B.p("Gangplank", (2.2, 0.2, 0.3), p, G.ry(math.degrees(math.atan2(d[0], d[2]))), "8a5a2a")
    # treasure on the sand, coral, kelp, starfish, shells, barrels
    chest(B, (-15.5, 1.1, -10.2), heading=15.0)
    for k, (x, z, h, cols) in enumerate(((17.0, -11.2, 4.4, (CORAL[0], CORAL[4], CORAL[3])),
                                         (-19.4, -10.6, 3.6, (CORAL[1], CORAL[0], CORAL[4])),
                                         (19.6, 3.6, 5.2, (CORAL[2], CORAL[0], CORAL[1])),
                                         (-19.6, 4.8, 4.6, (CORAL[3], CORAL[2], CORAL[4])))):
        coral(B, (x, 0.0, z), h, cols, n=3, heading=40 * k)
    kelp(B, (12.4, 0.0, -12.6), 3, 6.5)
    kelp(B, (-20.0, 0.0, -2.5), 3, 7.5, heading=40)
    starfish(B, (-2.5, 1.26, -12.6), 1.1, heading=10)
    starfish(B, (11.5, 1.47, -11.0), 0.9, col="ff5a6e", heading=40)
    for k, (x, z) in enumerate(((5.2, -12.9), (-9.6, -12.8))):
        B.p("Shell", (1.1, 0.5, 0.9), (x, 1.47 - 0.21 * k, z), ori(0, 30 + 40 * k, 12), ("fff1e0", "ffd8c0")[k])
        B.p("Shell", (0.7, 0.42, 0.6), (x + 0.3, 1.6 - 0.21 * k, z - 0.2), ori(0, 75 + 40 * k, -10), ("ffd8c0", "fff1e0")[k])
    barrel(B, (19.6, 1.1, -6.4), G.ry(20))
    barrel(B, (17.0, 0.95, -8.6), G.rz(90) @ G.ry(30))
    return B.finish()


def ship(B):
    """The ship in its own frame: keel at Y 0, bow towards -X, the lane side -Z."""
    B.p("Hull", (32.0, 6.6, 11.0), (0.0, 3.3, 0.0), None, HULL[2], solid=True)
    for k, (y0, L) in enumerate(((0.4, 26.0), (1.8, 29.0), (3.2, 31.0), (4.6, 32.0), (6.0, 33.0))):
        B.p("Hull", (L, 1.4, 0.6), (0.0, y0 + 0.7, -5.8), None, HULL[k % 2], solid=True)
    B.p("Hull", (33.0, 4.2, 0.6), (0.0, 5.3, 5.8), None, HULL[1], solid=True)
    B.p("Hull", (7.8, 6.5, 7.8), (-16.0, 3.3, 0.0), G.ry(45), HULL[1], solid=True)                 # the bow
    for k, y0 in enumerate((3.2, 4.6, 6.0)):
        B.p("Hull", (7.9, 1.36, 0.6), (-18.97, y0 + 0.7, -2.97), G.ry(-135), HULL[(k + 1) % 2], solid=True)
    B.p("Deck", (5.4, 0.44, 5.4), (-16.8, 6.85, 0.0), G.ry(45), DECK[1], solid=True)
    for k in range(4):
        B.p("Deck", (32.6, 0.4 + 0.02 * (k % 2), 2.7), (0.0, 6.8, -4.05 + 2.7 * k), None, DECK[k % 2], solid=True)
    for z in (-5.8, 5.8):
        B.p("Rail", (33.4, 0.5, 0.8), (0.0, 7.65, z), None, HULL[3], solid=True)
    B.p("Hull", (0.8, 7.1, 11.6), (16.4, 3.9, 0.0), None, HULL[0], solid=True)                    # the stern
    # stern castle: lit windows, a door, a lantern
    B.p("Castle", (6.5, 4.0, 10.6), (12.75, 9.0, 0.0), None, HULL[0], solid=True)
    B.p("Castle", (7.3, 0.5, 11.4), (12.75, 11.25, 0.0), None, HULL[3], solid=True)
    for x in (11.1, 14.4):
        B.p("Window", (1.3, 1.5, 0.12), (x, 9.3, -5.36), None, "ffd27a", material="Neon", lamp=True)
    B.plate("Door", (0.12, 2.8, 1.8), (9.44, 8.45, -1.6), col="2a1a10")
    B.p("Lantern", (0.3, 1.6, 0.3), (16.2, 12.3, -4.6), None, IRON[2])
    B.p("Lantern", (0.8, 1.0, 0.8), (16.2, 13.6, -4.6), G.ry(45), "ffcf6a", material="Neon", flicker=0.1, lamp=True)
    # the main mast: crow's nest, a torn sail, the Jolly Roger; broken off at the top
    bar(B, "Mast", (2.0, 7.0, 0.0), (2.0, 22.5, 0.0), 1.0, "7a5030")
    bar(B, "Mast", (2.0, 22.3, 0.0), (3.3, 24.9, -0.7), 0.9, "6e4a2a")
    B.p("Nest", (2.6, 1.0, 2.6), (2.0, 17.6, 0.0), None, HULL[0])
    B.p("Nest", (2.9, 0.5, 2.9), (2.0, 18.35, 0.0), G.ry(45), HULL[3])
    a = math.radians(35.0)
    d = np.array((math.sin(a), 0.0, math.cos(a)))
    n = np.array((-math.cos(a), 0.0, math.sin(a)))
    bar(B, "Yard", (2.0, 15.5, 0.0) - d * 4.8, (2.0, 15.5, 0.0) + d * 4.8, 0.5, "6e4a2a")
    Rs = np.column_stack((d, (0, 1, 0), n))
    B.p("Sail", (8.6, 4.0, 0.15), np.array((2.0, 13.3, 0.0)) + n * -0.55, Rs, "f4ecd8")
    B.p("Sail", (4.6, 3.0, 0.16), np.array((2.0, 9.9, 0.0)) + n * -0.55 + d * -1.9, Rs @ G.rz(-6), "e8dcc0")
    B.plate("Flag", (3.6, 2.4, 0.12), (3.85, 21.0, 0.0), col=INK)
    B.plate("Flag", (1.0, 0.85, 0.1), (3.85, 21.25, -0.11), col="f4f4f0")
    B.plate("Flag", (0.62, 0.32, 0.1), (3.85, 20.65, -0.11), col="f4f4f0")
    for s in (-1, 1):
        B.plate("Flag", (0.24, 0.26, 0.1), (3.85 + s * 0.22, 21.3, -0.16), col=INK)
        B.plate("Flag", (1.9, 0.22, 0.1), (3.85, 21.0, -0.085 + 0.01 * s), G.rz(s * 32), col="f4f4f0")
    # the foremast snapped off, its top lying across the deck
    bar(B, "Mast", (-9.0, 7.0, 0.0), (-9.0, 11.4, 0.0), 0.95, "7a5030")
    B.p("Mast", (0.4, 0.3, 0.5), (-9.0, 11.45, 0.0), G.ry(30), "c8945a")
    bar(B, "Mast", (-13.0, 8.2, 4.6), (-4.0, 8.4, -5.0), 0.85, "6e4a2a")
    # rigging, bowsprit, a gold figurehead
    for e in ((-21.0, 7.6, 0.0), (16.0, 11.6, 0.4), (-3.0, 7.9, -5.8)):
        bar(B, "Rope", (2.0, 22.0, 0.0), e, 0.18, "5a3e22")
    bar(B, "Bowsprit", (-20.0, 6.6, 0.0), (-23.0, 8.3, 0.0), 0.7, "7a5030")
    B.p("Figurehead", (1.3, 1.6, 1.3), (-21.2, 5.4, 0.0), G.ry(30), GOLD[0])
    B.p("Figurehead", (0.9, 0.5, 0.9), (-21.2, 6.4, 0.0), None, GOLD[1])
    # portholes, cannons run out, a hole stove in
    for x in (-12.0, -6.5, 6.0):
        B.plate("Porthole", (1.1, 1.1, 0.1), (x, 5.3, -6.15), col="c8a040")
        B.plate("Porthole", (0.72, 0.72, 0.1), (x, 5.3, -6.2), col="1e2a36")
    for x in (-10.5, -3.5, 3.5):
        B.plate("Gunport", (1.5, 1.4, 0.1), (x, 3.9, -6.15), col="1e1a16")
        B.p("Cannon", (0.8, 0.8, 2.2), (x, 3.9, -6.65), None, IRON[2])
        B.p("Cannon", (1.05, 1.05, 0.35), (x, 3.9, -7.6), None, IRON[0])
    B.plate("Hole", (3.0, 2.2, 0.1), (9.0, 2.3, -6.15), col="1e1a16")
    for k, (x, y) in enumerate(((-13.5, 1.5), (-11.8, 0.9), (13.2, 1.2), (-1.0, 0.8))):
        B.p("Barnacle", (0.55, 0.45, 0.4), (x, y, -6.25 - 0.02 * k), G.rz(45), ("d8d4c8", "c8c4b8")[k % 2])
    for k, x in enumerate((-7.5, 12.4)):
        bar(B, "Weed", (x, 7.95, -5.95), (x + 0.6, 4.2 + 0.6 * k, -6.35), 0.5, KELP[k], t=0.18, n=(0, 0, -1))
    bar(B, "Hull", (7.5, 3.2, -6.2), (8.7, 1.9, -6.9), 0.5, HULL[3], t=0.25)
    bar(B, "Hull", (10.5, 1.4, -6.2), (9.5, 2.6, -6.85), 0.5, HULL[0], t=0.25)
    # the captain on deck: tricorn hat, eyepatch, cutlass, parrot
    s = 4.6
    c = np.array((6.0, 7.0 + s / 2, -2.2))
    potato(B, c, s, ("d9b07a", "c49a64", "e8c490"), name="Captain", glints=True, cheeks="ff9aa8")
    zf = c[2] - s * 0.39 - 0.02
    ex = c[0] + s * 0.17
    B.plate("Eyepatch", (0.95, 1.2, 0.1), (ex, c[1] + s * 0.12, zf - 0.1), col=INK)
    bar(B, "Eyepatch", (ex - 0.6, c[1] + s * 0.36, zf - 0.08), (ex + 1.1, c[1] - 0.05, zf - 0.08), 0.2, INK, t=0.1,
        material="SmoothPlastic", shadow=False)
    hy = c[1] + s / 2
    B.p("Hat", (3.2, 1.0, 2.6), (c[0], hy + 0.42, c[2]), None, "2a2430")
    B.p("Hat", (4.6, 1.5, 0.32), (c[0], hy + 0.95, c[2] - 1.35), G.rx(18), INK)
    B.p("Hat", (4.4, 1.3, 0.3), (c[0], hy + 0.85, c[2] + 1.35), G.rx(-18), INK)
    B.p("Hat", (4.7, 0.18, 0.4), (c[0], hy + 1.72, c[2] - 1.12), G.rx(18), GOLD[1])
    B.plate("Hat", (0.8, 0.7, 0.1), (c[0], hy + 1.0, c[2] - 1.58), G.rx(18), col="f4f4f0")
    bar(B, "Captain", c + (-s * 0.36, -0.2, 0.0), c + (-s * 0.6, s * 0.18, -0.7), 0.85, "c49a64")
    bar(B, "Captain", c + (s * 0.36, -0.3, 0.0), c + (s * 0.56, -s * 0.28, -0.4), 0.85, "c49a64")
    hand = c + (-s * 0.62, s * 0.2, -0.75)
    B.p("Cutlass", (0.3, 2.8, 0.12), hand + (-0.35, 1.55, 0.0), G.rz(14), "d8dce6")
    B.p("Cutlass", (1.0, 0.22, 0.34), hand + (-0.05, 0.2, 0.0), G.rz(14), GOLD[1])
    pc = c + (s * 0.42, s * 0.62, 0.3)
    B.p("Parrot", (0.8, 1.15, 0.8), pc, G.rz(-8), "e8403a")
    B.p("Parrot", (0.66, 0.6, 0.66), pc + (0.05, 0.85, -0.05), None, "f05a48")
    B.p("Parrot", (0.32, 0.3, 0.42), pc + (0.05, 0.8, -0.5), None, "ffd23f")
    B.p("Parrot", (0.22, 0.8, 0.6), pc + (0.46, -0.05, 0.05), G.rz(-10), "3b8bff")


# ==================================================================== props

def p_palm(sc, parent):
    B = Build(sc, parent, "BeachPalm", seed=41)
    B.p("Sand", (4.6, 0.5, 4.2), (0.0, 0.25, 0.0), G.ry(12), SAND[0])
    B.p("Sand", (3.2, 0.42, 3.0), (0.4, 0.62, 0.2), G.ry(40), SAND[1])
    palm(B, (0.0, 0.8, 0.0), 13.5, 3.2, PALM_TRUNK, PALM_LEAF, fronds=7, frond_len=6.4, coconuts=3, heading=-40.0)
    starfish(B, (-1.4, 0.52, -1.6), 0.7, heading=20)
    return B.finish()


def p_coral(sc, parent):
    B = Build(sc, parent, "CoralTree", seed=42)
    rock(B, (0.0, 0.0, 0.0), 2.6, ("b8a88a", "a89878", "c8b89a"))
    coral(B, (0.2, 1.4, 0.0), 4.8, (CORAL[0], CORAL[4], CORAL[3]), n=3, heading=10)
    coral(B, (-1.5, 0.0, -0.6), 3.2, (CORAL[2], CORAL[0], CORAL[2]), n=2, heading=200)
    return B.finish()


def p_brain(sc, parent):
    B = Build(sc, parent, "BrainCoral", seed=43)
    round3(B, "Coral", (0.0, 1.0, 0.0), 3.4, 2.0, 3.2, ("ff8aa8", "f07090", "ffa4bc"), lid=(2.3, 0.55, 2.2))
    for k, x in enumerate((-0.6, 0.0, 0.6)):
        B.p("Coral", (0.24, 0.18 + 0.03 * k, 2.0), (x, 2.27, 0.0), ori(0, 12 * (-1) ** k, 0), "d85a7a")
    for k, (h, x) in enumerate(((2.0, 2.1), (1.4, 2.6))):
        B.p("Sponge", (0.8, h, 0.8), (x, h / 2, -0.9 + 0.8 * k), G.ry(20 * k), ("ffc94d", "ff9f3d")[k])
    from .scenery import fern
    fern(B, (-2.1, 0.1, -1.2), 5, ("b46bff", "d08aff"), length=1.3, rise=55, w=0.3)
    return B.finish()


def p_kelp(sc, parent):
    B = Build(sc, parent, "Kelp", seed=44)
    rock(B, (0.0, 0.0, 0.0), 1.6, ("8a8478", "9a9488", "7a7468"))
    kelp(B, (0.0, 0.0, 0.0), 4, 7.5)
    return B.finish()


def p_anchor(sc, parent):
    B = Build(sc, parent, "Anchor", seed=45)
    B.p("Sand", (4.8, 0.6, 3.6), (0.0, 0.3, 0.0), G.ry(8), SAND[2])
    R = G.rz(-18)
    base = np.array((-0.6, 0.6, 0.0))

    def at(v):
        return base + R @ np.asarray(v, float)
    B.p("Anchor", (0.8, 7.0, 0.8), at((0, 3.5, 0)), R, IRON[0])
    B.p("Anchor", (4.0, 0.6, 0.6), at((0, 5.9, 0)), R, IRON[1])
    for k, (dx, dy, sx, sy) in enumerate(((0, 7.55, 1.4, 0.35), (0, 8.75, 1.4, 0.35), (-0.55, 8.15, 0.35, 1.2),
                                          (0.55, 8.15, 0.35, 1.2))):
        B.p("Ring", (sx, sy, 0.36 + 0.02 * k), at((dx, dy, 0)), R, IRON[1])
    for s in (-1, 1):
        a, b = at((0, 0.7, 0)), at((s * 2.4, 2.2, 0))
        bar(B, "Anchor", a, b, 0.75, IRON[0], t=0.77 + 0.04 * s, n=(0, 0, -1))
        B.p("Anchor", (1.3, 1.3, 0.45), b + R @ (s * 0.2, 0.2, 0), R @ G.rz(45), IRON[1])
    ring = at((0.0, 8.75, 0.0))
    end = np.array((ring[0] + 3.4, 0.62, -0.9))
    pts = [ring + (end - ring) * t + np.array((0.0, -2.2 * t * (1 - t), 0.0)) for t in np.linspace(0.08, 1.0, 6)]
    for k in range(5):
        a, b = pts[k], pts[k + 1]
        bar(B, "Chain", a, b, 0.5 if k % 2 == 0 else 0.22, IRON[2], t=0.22 if k % 2 == 0 else 0.5, over=0.2,
            n=(0, 0, -1))
    return B.finish()


def p_chest(sc, parent):
    B = Build(sc, parent, "TreasureChest", seed=46)
    B.p("Sand", (5.0, 0.4, 4.4), (0.0, 0.2, 0.0), G.ry(10), SAND[0])
    chest(B, (0.0, 0.4, 0.3))
    return B.finish()


def p_clam(sc, parent):
    B = Build(sc, parent, "GiantClam", seed=47)
    B.p("Clam", (4.2, 0.9, 3.4), (0.0, 0.45, 0.0), None, "c8b8e8")
    B.p("Clam", (3.4, 0.84, 3.4), (0.0, 0.47, 0.0), G.ry(45), "b8a8d8")
    B.p("Clam", (3.4, 0.2, 2.6), (0.0, 0.98, -0.1), None, "ffb4c8")
    B.p("Clam", (4.0, 0.7, 3.2), (0.0, 2.0, 1.45), G.rx(-58), "d0c0f0")
    B.p("Clam", (3.3, 0.66, 3.3), (0.0, 2.0, 1.45), G.rx(-58) @ G.ry(45), "c0b0e0")
    for k, x in enumerate((-1.0, 0.0, 1.0)):
        B.p("Clam", (0.28, 0.2, 2.8), (x, 2.3 + 0.04 * k, 1.25), G.rx(-58), "a898c8")
    B.p("Pearl", (0.95, 0.95, 0.95), (0.0, 1.55, -0.2), ori(35.26, 45, 0), "fff4fa", material="Neon", flicker=0.08,
        lamp=True)
    rock(B, (2.8, 0.0, -1.2), 1.0, ("8a8478", "9a9488", "7a7468"))
    return B.finish()


def p_barrels(sc, parent):
    B = Build(sc, parent, "BarrelStack", seed=48)
    barrel(B, (-0.95, 1.1, 0.2), G.ry(10))
    barrel(B, (0.95, 1.07, 0.4), G.ry(35), cols=("8a5a2a", "9a6a36"), band_y=0.27, h=2.14)
    barrel(B, (0.0, 3.25, 0.3), G.ry(20), cols=("a07040", "8a5a2a"), h=2.1)
    barrel(B, (0.3, 0.82, -2.1), G.rz(90) @ G.ry(15), h=2.0)
    B.p("Crate", (1.8, 1.6, 1.8), (2.6, 0.8, -1.4), G.ry(25), "b88450")
    B.p("Crate", (1.9, 0.2, 0.3), (2.6, 1.0, -1.4), G.ry(25) @ G.rz(40), "8a5a2a")
    return B.finish()


def p_dock(sc, parent):
    B = Build(sc, parent, "DockPosts", seed=49)
    posts = ((-2.4, 0.2, 5.2), (0.0, -0.3, 6.0), (2.5, 0.25, 4.6))
    for k, (x, z, h) in enumerate(posts):
        B.p("Post", (1.1, h, 1.1), (x, h / 2, z), G.ry(8 * k), HULL[k % 2])
        B.p("Post", (1.1, h - 0.06, 1.1), (x, h / 2, z), G.ry(45 + 8 * k), HULL[(k + 1) % 2])
    for k in range(2):
        a, b = posts[k], posts[k + 1]
        bar(B, "Rope", (a[0], 3.6 - 0.3 * k, a[1]), (b[0], 3.5 - 0.3 * k, b[1]), 0.22, "c8a070")
    c = np.array((0.0, 3.2, -0.95))
    for k in range(8):
        a = math.radians(22.5 + 45 * k)
        p = c + (math.cos(a) * 0.9, math.sin(a) * 0.9, 0)
        B.p("Lifebuoy", (0.42, 0.78, 0.46 + 0.04 * (k % 2)), p, G.rz(math.degrees(a)), ("e8403a", "fff4f0")[k % 2])
    g = np.array((2.5, 4.6, 0.25))
    B.p("Gull", (0.7, 0.6, 1.2), g + (0, 0.3, 0), None, "f4f4f0")
    B.p("Gull", (2.2, 0.12, 0.6), g + (0, 0.55, 0.15), G.rz(6), "c8ccd4")
    B.p("Gull", (0.5, 0.5, 0.5), g + (0, 0.75, -0.65), None, "ffffff")
    B.p("Gull", (0.2, 0.18, 0.4), g + (0, 0.7, -1.05), None, "ffb02e")
    return B.finish()


AREA = register(Area("Reef", "Coral Cove", hero, [
    (p_palm, prop_attrs(8, 0.85, 1.25, "Side", True)),
    (p_coral, prop_attrs(8, 0.8, 1.3, "Side", False)),
    (p_brain, prop_attrs(6, 0.8, 1.3, "Any", False)),
    (p_kelp, prop_attrs(8, 0.8, 1.3, "Side", False)),
    (p_anchor, prop_attrs(3, 0.9, 1.2, "Side", True)),
    (p_chest, prop_attrs(4, 0.9, 1.2, "Any", True)),
    (p_clam, prop_attrs(5, 0.8, 1.3, "Any", True)),
    (p_barrels, prop_attrs(4, 0.9, 1.2, "Side", True)),
    (p_dock, prop_attrs(4, 0.9, 1.2, "Edge", True)),
], ground="e8d49a"))
