"""Haunted Hollow: the hero, a crooked haunted manor with a giant jack-o'-lantern, and the area's props.

The manor leans a little: two storeys of upright purple planks on a stone footing, a steep gable
roof with a dormer and a crooked chimney, lit windows (orange and purple, flickering) and dark
ones, shutters hanging askew, a porch with steps and a purple lantern. A round tower beside it
with a pointed roof, purple windows and a bat on its spire, a ghost drifting past it. In front: a
giant jack-o'-lantern with a glowing face, three graves behind a spiky iron fence, and a dead tree
with a lantern hanging from it.
"""
import math

import numpy as np

import spsgeo as G
from spsgeo import CF

from .scenery import (Area, Build, INK, bar, flame, ori, prop_attrs, register, rock, round3, shade, turn)

WALL = ("5a4870", "4c3c62", "665480")
TRIM = ("2b2233", "1e1a22", "241c2c")
STONE = ("6e6680", "5a5470", "7c7690")
GLOW = ("ffb347", "b67cff", "9be34a")
PUMPKIN = ("f07412", "ff8a1f", "ffa23f")
STEM = ("4f8a2e", "5e9e34", "3f7a24")
BARK = ("4a3a36", "3e302c", "56463e")


def octagon6(B, name, c, w, h, cols, solid=False):
    """Folk Valley's eight-sided drum: two crossing blocks and four corner blocks turned 45."""
    c = np.asarray(c, float)
    s = w * math.tan(math.radians(22.5))
    out = [B.p(name, (w, h, s), c, None, cols[0], solid=solid),
           B.p(name, (s, h - 0.04, w), c, None, cols[0], solid=solid)]
    r = (w / 2 + s / 2) / 2 * 1.0
    for k in range(4):
        a = math.radians(45 + 90 * k)
        p = c + (math.cos(a) * r * 1.0, 0.0, math.sin(a) * r * 1.0)
        out.append(B.p(name, (s, h - 0.08 - 0.02 * k, s / 2), p, G.ry(-45 - 90 * k), cols[1], solid=solid))
    return out


def window(B, x, y, z, w=2.2, h=2.8, glow=GLOW[0], lit=True, name="Window"):
    """A window on a wall facing -Z (z is the wall face): a pane (glowing or dark), a cross of bars,
    a sill."""
    if lit:
        B.p(name, (w, h, 0.12), (x, y, z - 0.06), None, glow, material="Neon", flicker=0.15, lamp=True)
    else:
        B.plate(name, (w, h, 0.12), (x, y, z - 0.06), col="1a1420")
    B.p(name, (0.26, h + 0.1, 0.16), (x, y, z - 0.18), None, TRIM[1])
    B.p(name, (w + 0.1, 0.26, 0.24), (x, y + 0.1, z - 0.2), None, TRIM[1])
    B.p(name, (w + 0.7, 0.32, 0.6), (x, y - h / 2 - 0.16, z - 0.3), None, TRIM[0])


def jack(B, c, s, R=None, name="Pumpkin", face=True, lit=True):
    """A pumpkin s wide: Folk Valley's round with two ribs, a stem and a leaf; a carved face that
    glows."""
    R = np.eye(3) if R is None else R
    c = np.asarray(c, float)
    h, d = s * 0.78, s * 0.9
    out = round3(B, name, c, s, h, d, PUMPKIN, R=R)
    for sx in (-1, 1):
        out.append(B.p(name, (s * 0.2, h * 0.92, d * 0.96), c + R @ (sx * s * 0.33, 0, 0), R, PUMPKIN[1]))
    out.append(B.p(name, (s * 0.14, s * 0.26, s * 0.14), c + R @ (0.05 * s, h / 2 + s * 0.1, 0), R @ ori(8, 20, -10),
                   STEM[0]))
    out.append(B.p(name, (s * 0.32, 0.12, s * 0.2), c + R @ (0.22 * s, h / 2 + 0.03, 0.08 * s), R @ ori(0, 30, -8), STEM[1]))
    if face:
        zf = -d / 2 - 0.05
        mat = "Neon" if lit else "SmoothPlastic"
        col = "ffc93c" if lit else INK
        kw = dict(flicker=0.18, lamp=True) if lit else dict(shadow=False)
        for sx in (-1, 1):
            out.append(B.p(name, (s * 0.15, s * 0.15, 0.12), c + R @ (sx * s * 0.2, h * 0.14, zf), R @ G.rz(45), col,
                           material=mat, **kw))
        out.append(B.p(name, (s * 0.46, s * 0.12, 0.12), c + R @ (0, -h * 0.16, zf), R, col, material=mat, **kw))
        out.append(B.p(name, (s * 0.1, s * 0.06, 0.1), c + R @ (-s * 0.08, -h * 0.11, zf - 0.05), R, PUMPKIN[0]))
        out.append(B.p(name, (s * 0.1, s * 0.06, 0.1), c + R @ (s * 0.1, -h * 0.21, zf - 0.05), R, PUMPKIN[0]))
    return out


def grave(B, c, heading=0.0, s=1.0, name="Grave"):
    """A headstone, a little crooked, with a cross on it and a mound of earth in front."""
    c = np.asarray(c, float)
    R = G.ry(heading) @ G.rz(float(B.rng.uniform(-8, 8))) @ G.rx(float(B.rng.uniform(-6, 4)))
    out = [B.p(name, (2.2 * s, 2.6 * s, 0.6 * s), c + R @ (0, 1.3 * s, 0), R, STONE[0]),
           B.p(name, (1.56 * s, 1.56 * s, 0.56 * s), c + R @ (0, 2.6 * s, 0), R @ G.rz(45), STONE[2]),
           B.plate(name, (0.3 * s, 1.3 * s, 0.1), c + R @ (0, 1.9 * s, -0.33 * s), R, col="3a3448"),
           B.plate(name, (0.9 * s, 0.3 * s, 0.1), c + R @ (0, 2.15 * s, -0.34 * s), R, col="3a3448"),
           B.p(name, (2.0 * s, 0.4 * s, 2.4 * s), c + np.array((0, 0.2 * s, -1.5 * s)), G.ry(heading), "4a3a2c")]
    return out


def bat(B, c, s=1.0, heading=0.0, name="Bat"):
    c = np.asarray(c, float)
    R = G.ry(heading)
    out = [B.p(name, (0.8 * s, 0.8 * s, 0.7 * s), c, R, TRIM[1])]
    for sx in (-1, 1):
        out.append(B.p(name, (1.4 * s, 0.12, 0.66 * s), c + R @ (sx * 0.95 * s, 0.25 * s, 0), R @ G.rz(sx * 25), TRIM[2]))
    out.append(B.p(name, (0.5 * s, 0.14 * s, 0.1), c + R @ (0, 0.12 * s, -0.36 * s), R, "ff4d6d", material="Neon",
                   lamp=True))
    return out


def ghost(B, c, s=1.0, name="Ghost", tr=0.25):
    """A friendly ghost, a little see-through: a body, a wavy tail, two dark eyes and a mouth."""
    c = np.asarray(c, float)
    out = [B.p(name, (2.4 * s, 2.4 * s, 1.8 * s), c, G.rz(-6), "f4f4ff", transparency=tr),
           B.p(name, (2.0 * s, 0.6 * s, 1.5 * s), c + (0.15 * s, 1.35 * s, 0), G.rz(-6), "ffffff", transparency=tr),
           B.p(name, (1.6 * s, 1.0 * s, 1.4 * s), c + (0.6 * s, -1.4 * s, 0.1 * s), G.rz(22), "eeeefc", transparency=tr),
           B.p(name, (0.9 * s, 0.8 * s, 1.0 * s), c + (1.4 * s, -2.0 * s, 0.2 * s), G.rz(40), "e6e6f6", transparency=tr)]
    for sx in (-1, 1):
        out.append(B.plate(name, (0.36 * s, 0.56 * s, 0.1), c + (sx * 0.48 * s, 0.3 * s, -0.95 * s), G.rz(-6)))
    out.append(B.plate(name, (0.5 * s, 0.34 * s, 0.1), c + (0.05 * s, -0.45 * s, -0.95 * s), G.rz(-6)))
    return out


def dead_tree(B, base, h=12.0, name="DeadTree", lantern=True):
    """A bare crooked tree: a trunk of three turned blocks, crooked branches, a lantern on one."""
    rng = B.rng
    base = np.asarray(base, float)
    seg = h / 3
    out = []
    x = np.zeros(3)
    for i, w in enumerate((1.9, 1.5, 1.1)):
        lean = np.array((0.45 * (-1) ** i, 0, 0.25))
        a, b = base + x, base + x + np.array((0, seg, 0)) + lean
        out.append(bar(B, name, a, b, w, BARK[i % 3], over=0.25, n=(0, 0, -1)))
        x = b - base
    top = base + x
    specs = ((140, 50, 4.2, 0.62, 0.55), (20, 40, 3.8, 0.58, 0.75), (250, 55, 3.2, 0.5, 0.95), (80, 35, 3.0, 0.45, 1.0),
             (320, 60, 2.6, 0.42, 0.5))
    tips = []
    for k, (hd, lean, L, w, f) in enumerate(specs):
        s = base + (top - base) * f
        a, l = math.radians(hd), math.radians(lean)
        d = np.array((math.sin(a) * math.sin(l), math.cos(l), -math.cos(a) * math.sin(l)))
        e = s + d * L
        out.append(bar(B, name, s, e, w, BARK[(k + 1) % 3], n=(0, 0, -1)))
        e2 = e + np.array((math.sin(a + 0.8) * 0.9, 0.9, -math.cos(a + 0.8) * 0.9))
        out.append(bar(B, name, e - d * 0.15, e2, w * 0.6, BARK[k % 3], n=(0, 0, -1)))
        tips.append(e)
    if lantern:
        t = tips[0]
        out.append(bar(B, "Lantern", t, t - (0, 1.4, 0), 0.12, INK))
        out.append(B.p("Lantern", (0.7, 0.9, 0.7), t - (0, 1.9, 0), G.ry(45), GLOW[1], material="Neon", flicker=0.15,
                       lamp=True))
    return out


# ==================================================================== the hero

def hero(sc, parent):
    B = Build(sc, parent, "Haunt", seed=51)
    with B.at(CF(np.array((-4.0, 0.0, 2.0)), G.rz(1.8))):
        manor(B)
    with B.at(CF(np.array((8.8, 0.0, 1.4)), G.rz(-2.2))):
        tower(B)
    ghost(B, (14.2, 13.0, -4.2), 1.1)
    # the giant jack-o'-lantern, the graves behind their fence, the dead tree
    jack(B, (-15.6, 2.75, -7.8), 7.0, R=G.ry(18))
    for k, (x, z, h) in enumerate(((12.8, -8.6, -8.0), (16.4, -7.4, 10.0), (19.6, -9.2, 4.0))):
        grave(B, (x, 0.0, z), heading=h, s=1.0 + 0.08 * k)
    for k in range(5):                                                           # a spiky iron fence
        x = 11.0 + 2.6 * k
        B.p("Fence", (0.36, 3.2, 0.36), (x, 1.6, -12.0), None, INK)
        B.p("Fence", (0.5, 0.5, 0.5), (x, 3.4, -12.0), ori(0, 45, 45), TRIM[0])
    for y in (1.0, 2.5):
        B.p("Fence", (10.8 + 0.1 * (y > 2), 0.24, 0.26), (16.2, y, -12.0), None, INK)
    dead_tree(B, (-19.8, 0.0, 6.0), 13.0)
    for k, (x, z, w) in enumerate(((-4.0, -7.6, 3.4), (-4.4, -10.4, 3.0), (-3.7, -12.9, 2.6))):
        B.p("Path", (w, 0.3 + 0.04 * k, 2.4), (x, 0.15, z), G.ry(8 * (-1) ** k), STONE[1 + k % 2])
    return B.finish()


def manor(B):
    """The house in its own frame: footprint x -9..9, z -6..6, front -Z."""
    B.p("Footing", (19.0, 1.2, 13.0), (0.0, 0.6, 0.0), None, STONE[1], solid=True)
    for k in range(15):                                                       # upright planks on the front
        x = -8.4 + 1.2 * k
        top = 16.2 + 0.25 * math.sin(k * 1.7)
        B.p("Wall", (1.2, top - 1.2, 0.5), (x, 1.2 + (top - 1.2) / 2, -5.75), None, WALL[k % 2], solid=True)
    for sx in (-1, 1):
        B.p("Wall", (0.6, 14.9, 11.4), (sx * 9.2, 8.65, 0.3), None, WALL[1], solid=True)
        B.p("Wall", (0.8, 15.3, 0.8), (sx * 9.25, 8.95, -6.05), None, TRIM[0])
    B.p("Wall", (17.8, 14.8, 0.6), (0.0, 8.6, 6.2), None, WALL[1], solid=True)
    B.p("Wall", (19.2, 0.6, 0.7), (0.0, 8.6, -6.2), None, TRIM[0])
    # the roof: two steep slopes, a strip of shingles along each eave, a ridge, stepped gables
    ang = 42.0
    for sz, col in ((-1, TRIM[0]), (1, TRIM[2])):
        R = G.rx(sz * ang)
        c = np.array((0.0, 16.2 + 3.0 * math.tan(math.radians(ang)) - 0.1, sz * 3.0))
        B.p("Roof", (20.6 - 0.2 * (sz > 0), 0.9, 9.4), c, R, col)
        B.p("Roof", (20.9, 0.5, 2.2), c + R @ (0, 0.55, sz * 3.4), R, shade(col, 0.2))
    B.p("Roof", (21.0, 0.8, 0.8), (0.0, 16.2 + 6.0 * math.tan(math.radians(ang)) + 0.35, 0.0), None, TRIM[1])
    for sx in (-1, 1):
        for k, (w, y) in enumerate(((10.4, 16.8), (7.4, 18.1), (4.4, 19.4), (1.6, 20.7))):
            B.p("Gable", (0.56, 1.3, w), (sx * 9.2, y, 0.0), None, WALL[k % 2])
    B.p("Dormer", (3.2, 3.2, 3.0), (-3.6, 19.0, -2.6), None, WALL[0])
    for sx in (-1, 1):
        B.p("Dormer", (2.4, 0.4, 3.4 - 0.1 * (sx > 0)), (-3.6 + sx * 0.9, 21.0, -2.5), G.rz(sx * -40), TRIM[1])
    B.p("Dormer", (1.6, 1.6, 0.12), (-3.6, 19.0, -4.16), G.rz(45), GLOW[1], material="Neon", flicker=0.15, lamp=True)
    B.p("Chimney", (2.0, 6.0, 2.0), (6.0, 20.6, 3.4), ori(0, 0, -6), STONE[0])
    B.p("Chimney", (2.6, 0.5, 2.6), (6.3, 23.7, 3.4), ori(0, 0, -6), STONE[2])
    # windows: two lit downstairs, upstairs one orange, one purple and a dark one with crooked shutters
    z = -6.0
    window(B, -5.6, 5.0, z)
    window(B, 5.6, 5.0, z, lit=False)
    window(B, -5.6, 12.0, z, glow=GLOW[1])
    window(B, 0.0, 12.0, z)
    window(B, 5.6, 12.0, z, lit=False)
    for sx, rz in ((-1, 8.0), (1, -14.0)):
        B.p("Shutter", (1.1, 3.0, 0.2), (5.6 + sx * 1.75, 11.9 - 0.2 * (sx > 0), z - 0.3), G.rz(rz), TRIM[0])
    # the door and its porch
    B.plate("Door", (3.0, 4.7, 0.12), (0.0, 4.05, z - 0.06), col="2e1e16")
    for sx in (-1, 1):
        B.p("Door", (0.5, 4.9, 0.3), (sx * 1.75, 4.15, z - 0.15), None, TRIM[0])
    B.p("Door", (4.2, 0.6, 0.3), (0.0, 6.5, z - 0.19), None, TRIM[0])
    B.p("Door", (0.35, 0.35, 0.2), (0.95, 3.6, z - 0.2), None, "c8a040")
    B.p("Porch", (8.0, 0.5, 3.6), (0.0, 1.48, z - 1.7), None, TRIM[2], solid=True)
    for k in range(2):
        B.p("Porch", (4.6, 0.6, 1.0), (0.0, 0.3 + 0.6 * k, z - 4.1 + 0.95 * k), None, STONE[k], solid=True)
    for sx in (-1, 1):
        B.p("Porch", (0.5, 5.4, 0.5), (sx * 3.6, 4.4, z - 3.3), None, TRIM[1])
    B.p("Porch", (9.0, 0.5, 4.4), (0.0, 7.4, z - 2.0), G.rx(-14), TRIM[0])
    B.p("Lantern", (0.12, 0.8, 0.12), (2.4, 6.6, z - 3.0), None, INK)
    B.p("Lantern", (0.6, 0.8, 0.6), (2.4, 5.9, z - 3.0), G.ry(45), GLOW[1], material="Neon", flicker=0.12, lamp=True)


def tower(B):
    """The round tower in its own frame: centred on X 0, Z 0."""
    octagon6(B, "Tower", (0.0, 11.0, 0.0), 7.0, 22.0, (WALL[0], WALL[1]), solid=True)
    from .scenery import octagon
    octagon(B, "Tower", (0.0, 22.4, 0.0), 7.8, 0.8, (TRIM[0], TRIM[1], TRIM[0]))
    y = 22.8
    for k, (w, h) in enumerate(((6.4, 2.2), (5.0, 2.2), (3.7, 2.2), (2.5, 2.2), (1.3, 2.4))):
        B.p("Spire", (w, h, w), (0.0, y + h / 2, 0.0), G.ry(45 * (k % 2)), TRIM[k % 2])
        y += h - 0.05
    bar(B, "Spire", (0.0, y - 0.1, 0.0), (0.0, y + 2.2, 0.0), 0.25, INK)
    bat(B, (0.0, y + 2.6, 0.0), 0.9)
    z = -3.5
    for k, yy in enumerate((8.0, 15.5)):
        B.p("Window", (1.6, 3.2, 0.12), (0.0, yy, z - 0.06), None, GLOW[1] if k else GLOW[0], material="Neon",
            flicker=0.15, lamp=True)
        B.p("Window", (2.2, 0.5, 0.36), (0.0, yy + 1.85, z - 0.18), None, TRIM[1])
        B.p("Window", (2.2, 0.36, 0.5), (0.0, yy - 1.82, z - 0.25), None, TRIM[0])


# ==================================================================== props

def p_tree(sc, parent):
    B = Build(sc, parent, "DeadTree", seed=61)
    B.p("Roots", (3.2, 0.5, 3.0), (0.0, 0.25, 0.0), G.ry(20), BARK[1])
    dead_tree(B, (0.0, 0.3, 0.0), 11.0)
    bat(B, (2.2, 9.0, -0.6), 0.8, heading=20)
    return B.finish()


def p_graves(sc, parent):
    B = Build(sc, parent, "Graves", seed=62)
    for k, (x, z, h) in enumerate(((-2.4, 0.4, -8.0), (0.4, -0.3, 6.0), (2.9, 0.6, 14.0))):
        grave(B, (x, 0.0, z), heading=h, s=0.95 + 0.07 * k)
    B.p("Candle", (0.4, 0.8, 0.4), (-1.1, 0.42, -2.2), None, "f4ecd8")
    B.p("Candle", (0.24, 0.36, 0.24), (-1.1, 1.0, -2.2), G.ry(45), GLOW[0], material="Neon", flicker=0.25, lamp=True)
    return B.finish()


def p_pumpkins(sc, parent):
    B = Build(sc, parent, "JackOLanterns", seed=63)
    jack(B, (0.0, 1.4, 0.0), 3.6)
    jack(B, (3.05, 1.0, 0.65), 2.6, R=G.ry(-20))
    jack(B, (-2.2, 0.75, -0.8), 1.9, R=G.ry(25), face=False)
    return B.finish()


def p_cauldron(sc, parent):
    B = Build(sc, parent, "Cauldron", seed=64)
    for k in range(3):
        a = math.radians(120 * k + 30)
        bar(B, "Cauldron", (math.cos(a) * 1.7, 0.0, math.sin(a) * 1.7), (math.cos(a) * 1.2, 1.4, math.sin(a) * 1.2), 0.35,
            INK)
    round3(B, "Cauldron", (0.0, 2.2, 0.0), 3.6, 2.4, 3.6, (TRIM[1], TRIM[0], TRIM[2]))
    B.p("Cauldron", (3.4, 0.4, 3.4), (0.0, 3.5, 0.0), G.ry(22.5), TRIM[0])
    B.p("Brew", (2.7, 0.2, 2.7), (0.0, 3.62, 0.0), G.ry(22.5), GLOW[2], material="Neon", flicker=0.12, lamp=True)
    for k, (x, z, s) in enumerate(((0.4, -0.3, 0.6), (-0.6, 0.4, 0.45), (0.1, 0.7, 0.35))):
        B.p("Bubble", (s, s, s), (x, 3.85 + 0.1 * k, z), ori(20, 30 * k, 15), "c8ff7a", material="Neon", lamp=True)
    flame(B, (0.0, 0.55, 0.0), 1.0)
    bar(B, "Ladle", (0.8, 3.5, 0.6), (1.9, 5.6, 1.2), 0.22, "8a6a44")
    for k in range(3):
        a = math.radians(120 * k + 90)
        B.p("Log", (1.7, 0.4, 0.45), (math.cos(a) * 0.9, 0.22 + 0.01 * k, math.sin(a) * 0.9), G.ry(-120 * k), BARK[k])
    return B.finish()


def p_lamp(sc, parent):
    B = Build(sc, parent, "CrookedLamp", seed=65)
    B.p("Lamp", (1.4, 0.5, 1.4), (0.0, 0.25, 0.0), G.ry(45), TRIM[0])
    B.p("Lamp", (0.9, 0.6, 0.9), (0.0, 0.8, 0.0), None, TRIM[1])
    pts = [np.array(p) for p in ((0.0, 1.0, 0.0), (0.3, 4.6, 0.0), (-0.2, 7.8, 0.0), (0.9, 9.4, 0.0), (2.1, 9.5, 0.0))]
    for k in range(4):
        bar(B, "Lamp", pts[k], pts[k + 1], 0.4 - 0.04 * k, INK, over=0.12)
    top = pts[-1]
    bar(B, "Lamp", top, top - (0, 0.7, 0), 0.12, INK)
    B.p("Lamp", (1.0, 0.25, 1.0), top - (0, 0.8, 0), G.ry(45), TRIM[0])
    B.p("Lamp", (0.8, 1.0, 0.8), top - (0, 1.45, 0), None, GLOW[0], material="Neon", flicker=0.15, lamp=True)
    B.p("Lamp", (1.0, 0.25, 1.0), top - (0, 2.05, 0), G.ry(45), TRIM[0])
    bat(B, (-0.25, 8.0, -0.1), 0.6, heading=-20)
    return B.finish()


def p_fence(sc, parent):
    B = Build(sc, parent, "IronFence", seed=66)
    for k in range(5):
        x = -5.2 + 2.6 * k
        tall = k in (0, 4)
        h = 4.2 if tall else 3.2
        B.p("Fence", (0.36 if not tall else 0.7, h, 0.36 if not tall else 0.7), (x, h / 2, 0.0), None, INK)
        B.p("Fence", (0.5, 0.5, 0.5) if not tall else (0.9, 0.9, 0.9), (x, h + 0.2, 0.0), ori(0, 45, 45), TRIM[0])
    for y in (1.0, 2.6):
        B.p("Fence", (10.2, 0.24, 0.26), (0.0, y, 0.0), None, INK)
    for k in range(4):
        x = -3.9 + 2.6 * k
        B.p("Fence", (0.2, 2.6, 0.2), (x, 1.8, 0.0), None, TRIM[1])
    return B.finish()


def p_coffin(sc, parent):
    B = Build(sc, parent, "Coffin", seed=67)
    B.p("Mound", (4.2, 0.5, 3.4), (0.0, 0.25, 0.4), G.ry(8), "4a3a2c")
    R = G.rx(-12)
    base = np.array((0.0, 0.5, 0.6))

    def at(v):
        return base + R @ np.asarray(v, float)
    B.p("Coffin", (2.0, 5.4, 1.0), at((0, 2.7, 0)), R, "3a2a24")
    B.p("Coffin", (2.6, 2.0, 0.98), at((0, 3.6, 0)), R, "4a3428")
    B.p("Coffin", (1.6, 4.9, 0.1), at((0, 2.7, -0.52)), R, "6a2a5a", material="SmoothPlastic", shadow=False)
    B.p("Coffin", (2.1, 1.6, 0.1), at((0, 3.6, -0.51)), R, "7a3a6a", material="SmoothPlastic", shadow=False)
    hinge = at((1.3, 0, -0.55))
    Rl = R @ G.ry(-70)
    B.p("Lid", (2.0, 5.4, 0.4), hinge + Rl @ (1.0, 2.7, -0.2), Rl, "2e2220")
    B.p("Lid", (2.6, 2.0, 0.38), hinge + Rl @ (1.0, 3.6, -0.2), Rl, "382824")
    B.p("Lid", (0.3, 1.6, 0.12), hinge + Rl @ (1.0, 3.5, -0.46), Rl, "c8a040")
    B.p("Lid", (1.0, 0.3, 0.12), hinge + Rl @ (1.0, 3.8, -0.48), Rl, "c8a040")
    for sx in (-1, 1):
        B.p("Eye", (0.32, 0.22, 0.12), at((sx * 0.38, 4.1, -0.6)), R, "ff4d6d", material="Neon", flicker=0.2,
            lamp=True)
    return B.finish()


def p_mushrooms(sc, parent):
    B = Build(sc, parent, "GlowShrooms", seed=68)
    for k, (x, z, h, s) in enumerate(((0.0, 0.0, 2.6, 2.2), (1.9, 0.8, 1.6, 1.4), (-1.6, 0.6, 1.2, 1.1),
                                       (0.9, -1.4, 0.9, 0.9))):
        B.p("Stem", (0.5 * s, h, 0.5 * s), (x, h / 2, z), ori(0, 20 * k, 4 * (-1) ** k), "e8e0f4")
        B.p("Cap", (s, 0.5 * s, s), (x, h + 0.2 * s, z), G.ry(45 + 10 * k), ("8a4ad8", "b67cff")[k % 2],
            material="Neon", flicker=0.08, lamp=True)
        B.p("Cap", (s * 0.74, 0.46 * s, s * 0.74), (x, h + 0.48 * s, z), G.ry(10 * k), ("b67cff", "d8a8ff")[k % 2],
            material="Neon", lamp=True)
    return B.finish()


def p_ghost(sc, parent):
    B = Build(sc, parent, "Ghost", seed=69)
    ghost(B, (0.0, 3.4, 0.0), 1.0)
    B.p("Ghost", (0.3, 0.9, 0.3), (-1.65, 3.0, -0.6), G.rz(-30), "eeeefc", transparency=0.25)
    B.p("Ghost", (0.3, 0.9, 0.3), (1.65, 3.4, -0.4), G.rz(40), "eeeefc", transparency=0.25)
    bar(B, "Lantern", (2.0, 3.85, -0.45), (2.0, 3.1, -0.45), 0.1, INK)
    B.p("Lantern", (0.55, 0.7, 0.55), (2.0, 2.7, -0.45), G.ry(45), GLOW[0], material="Neon", flicker=0.2, lamp=True)
    return B.finish()


AREA = register(Area("Haunt", "Haunted Hollow", hero, [
    (p_tree, prop_attrs(6, 0.85, 1.3, "Side", True)),
    (p_graves, prop_attrs(6, 0.9, 1.2, "Side", True)),
    (p_pumpkins, prop_attrs(6, 0.8, 1.3, "Any", False)),
    (p_cauldron, prop_attrs(3, 0.9, 1.2, "Side", True)),
    (p_lamp, prop_attrs(6, 0.9, 1.15, "Side", False)),
    (p_fence, prop_attrs(5, 0.9, 1.1, "Edge", True)),
    (p_coffin, prop_attrs(3, 0.9, 1.2, "Any", True)),
    (p_mushrooms, prop_attrs(8, 0.8, 1.4, "Any", False)),
    (p_ghost, prop_attrs(4, 0.8, 1.3, "Any", False)),
], ground="3e5a3a"))
