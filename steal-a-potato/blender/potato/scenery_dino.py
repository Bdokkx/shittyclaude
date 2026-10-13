"""Dino Valley: the hero, a huge T-rex skeleton on a dig site, and the area's props.

The skeleton stands side-on to the lane on a layered rock mound (solid, players can climb it):
a big skull with its jaw open and teeth, a curved neck, a row of vertebrae with spines along the
back, ribs either side, tiny arms, long three-boned legs with clawed feet, and a long tail curving
down. Two iron posts hold it up. Behind it a little volcano glows; round it cycads, ferns and
horsetails, a nest of spotted eggs, a lump of amber, loose bones, a pickaxe, a shovel and a crate.
"""
import math

import numpy as np

import spsgeo as G

from .scenery import (Area, Build, INK, bar, fern, flame, grass, ori, prop_attrs, register, rock, round3, shade,
                      turn)

BONE = ("f2ead8", "e6dcc4", "fff8e8", "d8ccb0")
EARTH = ("8a6a48", "a4825a", "c09a6a", "e8d4a8")
ROCKC = ("6a5a50", "7a6a5e", "5a4a44")
LAVA = ("ff5a1a", "ff8a1a", "ffc93c")
FROND = ("4f9a3a", "5db546", "3f8a34", "6cbf48")
TRUNK = ("7a5a38", "8a6a44", "6e5030")
AMBER = "ffa21a"


def bone(B, a, b, w, col=BONE[0], knob=None, name="Bone"):
    """A bone from a to b: a shaft and a knob at each end."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    k = knob or w * 1.7
    out = [bar(B, name, a, b, w, col)]
    d = (b - a) / np.linalg.norm(b - a)
    for e, s in ((a, 1), (b, -1)):
        out.append(B.p(name, (k, k * 0.8, k), e + d * s * k * 0.2, ori(0, 30, 45), BONE[3]))
    return out


def cycad(B, base, h=4.0, n=8, frond=4.2, name="Cycad"):
    """A cycad: a stout scaly trunk of turned blocks and a crown of stiff fronds."""
    base = np.asarray(base, float)
    out = []
    y = 0.0
    for k, w in enumerate((1.9, 1.7, 1.5)):
        hh = h / 3
        out.append(B.p(name, (w, hh + 0.1, w), base + (0, y + hh / 2, 0), G.ry(45 * k + 10), TRUNK[k % 3]))
        y += hh
    top = base + (0, y, 0)
    out += fern(B, top, n, FROND, length=frond, rise=32, w=0.75, name=name)
    out.append(B.p(name, (0.9, 1.1, 0.9), top + (0, 0.45, 0), G.ry(20), "c8a040"))
    return out


def egg(B, c, s, col="f4ecd8", spots="7a9a5a", name="Egg", R=None):
    """A spotted egg standing up: two crossing blocks and a turned one, two spots."""
    R = np.eye(3) if R is None else R
    c = np.asarray(c, float)
    out = [B.p(name, (s, s * 1.3, s * 0.78), c, R, col),
           B.p(name, (s * 0.78, s * 1.26, s), c, R @ G.ry(45), shade(col, -0.05)),
           B.p(name, (s * 0.26, s * 0.26, 0.1), c + R @ (s * 0.18, s * 0.2, -s * 0.5 - 0.02), R, spots,
               material="SmoothPlastic", shadow=False),
           B.p(name, (s * 0.2, s * 0.2, 0.1), c + R @ (-s * 0.2, -s * 0.18, -s * 0.5 - 0.02), R, spots,
               material="SmoothPlastic", shadow=False)]
    return out


def volcano(B, c, s=1.0, name="Volcano", solid=False):
    """A small volcano: stacked rock slabs narrowing upwards, a glowing crater and two lava runs."""
    c = np.asarray(c, float)
    out = []
    y = 0.0
    for k, (w, h, d) in enumerate(((10.0, 2.6, 9.0), (8.0, 2.5, 7.2), (6.0, 2.4, 5.4), (4.6, 1.2, 4.2))):
        out.append(B.p(name, (w * s, h * s, d * s), c + (0, (y + h / 2) * s, 0), ori(2 * (-1) ** k, 12 * k, 0),
                       ROCKC[k % 3], solid=solid))
        y += h - 0.05
    out.append(B.p("Lava", (3.2 * s, 0.4, 2.8 * s), c + (0, (y - 0.1) * s, 0), G.ry(36), LAVA[0], material="Neon",
                   flicker=0.15, lamp=True))
    for k, (dx, dz, L) in enumerate(((0.6, -1.6, 4.2), (-1.4, -1.2, 3.4))):
        a = c + np.array((dx * s, (y - 0.4) * s, dz * s))
        b = a + np.array((dx * 0.5 * s, -L * s, -2.6 * s))
        out.append(bar(B, "Lava", a, b, 0.7 * s, LAVA[1 + k], t=0.3, n=(0, 0.6, -1), material="Neon", flicker=0.15,
                       lamp=True))
    return out


# ==================================================================== the hero

def hero(sc, parent):
    B = Build(sc, parent, "Dino", seed=71)
    # the dig site: three layers of rock, darker at the foot, a cream cap
    for k, (w, h, d, y, col) in enumerate(((34.0, 1.6, 21.0, 0.8, EARTH[0]), (30.0, 1.2, 18.0, 2.2, EARTH[1]),
                                           (27.0, 0.42, 15.6, 3.0, EARTH[3]))):
        B.p("Ground", (w, h, d), (1.0, y, 2.0), ori(1.0 * (-1) ** k, 3.0 * k - 2.0, 0), col, solid=True)
    top = 3.2
    skeleton(B, top)
    # behind: a small volcano; round about: plants, eggs, amber, bones and tools
    volcano(B, (16.6, 0.0, 10.6), 1.12, solid=True)
    cycad(B, (-17.6, 0.0, -9.8), 4.4)
    cycad(B, (19.0, 0.0, -6.8), 3.4, n=7)
    for k, (x, z) in enumerate(((-12.0, -11.6), (9.0, -11.8), (-19.4, 6.0))):
        fern(B, (x, 0.15, z), 5, FROND, length=2.6, rise=38, heading=40 * k)
    grass(B, (5.2, 0.0, -12.4), 4, ("5a8a3a", "6e9a44", "4a7a32"), h=(2.6, 3.8), r=0.8, name="Horsetail")
    nest = np.array((-8.6, top, -4.8))
    B.p("Nest", (3.4, 0.5, 3.0), nest + (0, 0.25, 0), G.ry(20), "8a6a3a")
    B.p("Nest", (3.0, 0.62, 3.2), nest + (0, 0.3, 0), G.ry(65), "7a5a30")
    for k, (dx, dz, a) in enumerate(((-0.6, 0.2, 0), (0.55, -0.1, 12), (0.0, 0.7, -10))):
        egg(B, nest + (dx, 1.25, dz), 1.15, R=G.ry(a) @ G.rz(6 * (-1) ** k))
    B.p("Amber", (1.2, 1.5, 1.0), (11.8, top + 0.75, -5.0), ori(10, 30, 20), AMBER, material="Neon", flicker=0.08,
        lamp=True)
    B.p("Amber", (0.3, 0.2, 0.3), (11.8, top + 0.85, -5.55), ori(0, 30, 20), "3a2a1a")
    bone(B, (-3.0, top + 0.35, -6.8), (0.6, top + 0.35, -6.2), 0.55)
    bone(B, (5.4, 0.35, -11.4), (8.0, 0.35, -9.6), 0.5)
    bone(B, (-20.4, 0.35, -3.6), (-17.6, 0.35, -2.4), 0.5)
    bar(B, "Pickaxe", (-14.2, 0.0, -6.6), (-13.0, 3.6, -6.2), 0.3, "8a6a44")
    B.p("Pickaxe", (2.6, 0.32, 0.32), (-13.0, 3.6, -6.2), ori(0, 15, 72), "9aa0aa")
    bar(B, "Shovel", (15.6, 0.6, -7.4), (16.2, 4.6, -7.6), 0.28, "8a6a44")
    B.p("Shovel", (1.1, 1.4, 0.16), (15.5, 0.75, -7.36), ori(0, 0, -8), "9aa0aa")
    B.p("Crate", (2.2, 1.9, 2.2), (17.6, 0.95, -2.2), G.ry(14), "b88450")
    B.p("Crate", (2.3, 0.3, 2.3), (17.6, 1.5, -2.2), G.ry(14), "8a5a2a")
    return B.finish()


def skeleton(B, y0):
    """The T-rex, side-on (head towards -X), feet on y0."""
    lift = y0 - 3.2
    spine = [np.array(p) + (0, lift, 0) for p in ((-6.5, 15.8, 0), (-3.5, 15.4, 0), (-0.5, 15.2, 0), (2.5, 15.0, 0),
                                                  (5.5, 14.6, 0), (8.5, 13.8, 0), (11.5, 12.6, 0), (14.5, 11.2, 0),
                                                  (17.2, 9.8, 0), (19.6, 8.6, 0))]
    sizes = (1.9, 1.95, 2.0, 2.2, 1.8, 1.6, 1.4, 1.2, 1.0, 0.8)
    for k, (p, s) in enumerate(zip(spine, sizes)):
        nxt = spine[min(k + 1, len(spine) - 1)] - spine[max(k - 1, 0)]
        R = G.rz(math.degrees(math.atan2(nxt[1], nxt[0])))
        L = float(np.linalg.norm(nxt)) / (2 if 0 < k < len(spine) - 1 else 1) + 0.25
        B.p("Spine", (max(L, s * 1.35), s, s * 1.05), p, R, BONE[k % 2], solid=True)
        if k < 7:
            h = 1.6 - 0.12 * k
            B.p("Spine", (0.45, h, 0.4 + 0.02 * k), p + R @ (0, s / 2 + h / 2 - 0.1, 0), R @ G.rz(-12), BONE[2])
        if 5 <= k <= 8:
            B.p("Spine", (0.4, 1.4 - 0.2 * (k - 5), 0.36), p + R @ (0.2, -s / 2 - 0.5, 0), R @ G.rz(20), BONE[1])
    neck = [np.array(p) + (0, lift, 0) for p in ((-7.6, 16.9, 0), (-8.6, 17.9, 0), (-9.5, 18.7, 0))]
    for k, p in enumerate(neck):
        B.p("Neck", (1.5, 1.4, 1.3 + 0.04 * k), p, G.rz(-40 + 8 * k), BONE[(k + 1) % 2])
    # the skull: cranium, snout, open jaw, an eye and a nostril, teeth
    sk = np.array((-12.2, 19.8 + lift, 0.0))
    B.p("Skull", (5.0, 3.4, 3.2), sk, G.rz(-6), BONE[0], solid=True)
    B.p("Skull", (4.4, 2.4, 2.6), sk + (-3.9, -0.7, 0), G.rz(-4), BONE[2], solid=True)
    B.p("Skull", (3.4, 0.7, 3.4), sk + (0.6, 1.8, 0), G.rz(-6), BONE[1])
    B.p("Skull", (1.6, 1.1, 3.5), sk + (0.4, -1.0, 0), G.rz(-6), BONE[3])
    jaw_hinge = sk + (1.6, -1.7, 0)
    Rj = G.rz(16)
    B.p("Jaw", (6.6, 0.9, 2.3), jaw_hinge + Rj @ (-3.3, 0, 0), Rj, BONE[1])
    B.plate("Skull", (1.4, 1.3, 0.12), sk + (-0.4, 0.3, -1.66), G.rz(-6), col="3a3026")
    B.plate("Skull", (0.6, 0.4, 0.12), sk + (-5.4, -0.2, -1.36), G.rz(-4), col="3a3026")
    for k in range(5):
        x = -5.6 + 0.85 * k
        B.p("Tooth", (0.36, 0.6, 0.36), sk + (x, -2.15 + 0.06 * k, -0.9), None, BONE[2])
    for k in range(4):
        t = 1.2 + 1.1 * k
        p = jaw_hinge + Rj @ (-t - 0.8, 0.62, -0.75)
        B.p("Tooth", (0.34, 0.5, 0.34), p, Rj, BONE[2])
    # ribs either side
    for k in range(6):
        x = -6.0 + 1.6 * k
        yb = 15.0 + lift - 0.05 * k
        L = 4.8 - 0.2 * abs(k - 2.5)
        for sz in (-1, 1):
            bar(B, "Rib", (x, yb, sz * 0.7), (x + 1.0, yb - L, sz * (2.3 - 0.1 * abs(k - 2.5))), 0.42,
                BONE[(k + (sz > 0)) % 2], t=0.5, n=(0, 0, sz))
    # pelvis, tiny arms, legs
    hip = np.array((3.0, 14.2 + lift, 0.0))
    B.p("Pelvis", (4.6, 2.6, 3.6), hip, G.rz(8), BONE[1], solid=True)
    bar(B, "Pelvis", hip + (-0.6, -1.0, 0), hip + (-1.8, -4.4, 0), 1.0, BONE[0], t=2.0)
    for sz in (-1, 1):
        sh = np.array((-5.2, 13.0 + lift, sz * 1.6))
        el = sh + (-1.2, -1.6, sz * 0.3)
        bar(B, "Arm", sh, el, 0.5, BONE[0])
        bar(B, "Arm", el, el + (-1.0, 0.2, 0), 0.32, BONE[2])
        z = sz * 1.9
        h_ = np.array((3.0, 13.4 + lift, z))
        kn = np.array((0.4, 8.6 + lift, z))
        an = np.array((3.4, 5.0 + lift, z))
        ft = np.array((1.2, y0 + 0.5, z))
        bar(B, "Leg", h_, kn, 1.5, BONE[0], over=0.3, solid=True)
        bar(B, "Leg", kn, an, 1.15, BONE[1], over=0.25, solid=True)
        bar(B, "Leg", an, ft, 0.9, BONE[0], over=0.2, solid=True)
        B.p("Leg", (1.3, 1.3, 1.3), kn, ori(0, 45, 20), BONE[3])
        for k, dz in enumerate((-0.55, 0.0, 0.55)):
            bar(B, "Toe", ft + (0, 0, dz), ft + (-2.0 + 0.4 * abs(dz), -0.3, dz * 1.4), 0.4, BONE[2], t=0.4 + 0.02 * k)
    # iron posts holding it up
    for x, ytop in ((-1.0, 12.2), (10.5, 11.8)):
        B.p("Post", (0.32, ytop + lift - y0, 0.32), (x, y0 + (ytop + lift - y0) / 2, 0.0), None, INK)


# ==================================================================== props

def p_cycad(sc, parent):
    B = Build(sc, parent, "Cycad", seed=81)
    cycad(B, (0.0, 0.0, 0.0), 4.4, n=9, frond=4.6)
    return B.finish()


def p_treefern(sc, parent):
    B = Build(sc, parent, "TreeFern", seed=82)
    pts = [np.array(p) for p in ((0.0, 0.0, 0.0), (0.3, 3.4, 0.1), (0.1, 6.6, -0.2), (0.5, 9.4, 0.0))]
    for k in range(3):
        bar(B, "Trunk", pts[k], pts[k + 1], 1.2 - 0.12 * k, TRUNK[k], over=0.2)
    fern(B, pts[-1] + (0, 0.2, 0), 9, FROND, length=5.2, rise=-12, w=0.9)
    B.p("Trunk", (1.3, 0.8, 1.3), pts[-1] + (0, 0.3, 0), G.ry(45), "6a8a3a")
    return B.finish()


def p_ribs(sc, parent):
    B = Build(sc, parent, "BoneArch", seed=83)
    for k in range(5):
        x = -4.0 + 2.0 * k
        h = 9.5 - 0.6 * abs(k - 2)
        B.p("Spine", (1.6, 1.3, 1.5), (x, h, 0.0), None, BONE[k % 2])
        for sz in (-1, 1):
            mid = np.array((x, h - 3.6, sz * 3.2))
            bar(B, "Rib", (x, h - 0.3, sz * 0.5), mid, 0.6, BONE[(k + 1) % 2], t=0.7)
            bar(B, "Rib", mid, (x + 0.3, 0.0, sz * 3.8), 0.55, BONE[k % 2], t=0.66, over=0.2)
    rock(B, (5.8, 0.0, -2.6), 1.4, ROCKC)
    return B.finish()


def p_nest(sc, parent):
    B = Build(sc, parent, "DinoNest", seed=84)
    for k in range(3):
        B.p("Nest", (4.0 - 0.3 * k, 0.6, 3.6 - 0.2 * k), (0.0, 0.3 + 0.02 * k, 0.0), G.ry(30 * k), ("8a6a3a", "7a5a30",
                                                                                                   "9a7a48")[k])
    egg(B, (-0.8, 1.35, 0.3), 1.3, R=G.rz(6))
    egg(B, (0.85, 1.3, 0.1), 1.2, col="dfe8c8", R=G.rz(-8))
    # a cracked egg with a baby dino peeking out
    c = np.array((0.0, 1.0, -1.1))
    B.p("Egg", (1.3, 0.9, 1.1), c, None, "f4ecd8")
    B.p("Egg", (1.1, 0.88, 1.3), c, G.ry(45), "ece2cc")
    B.p("Baby", (0.9, 0.9, 0.9), c + (0, 0.75, 0.0), G.rz(8), "6cbf48")
    for sx in (-1, 1):
        B.plate("Baby", (0.16, 0.24, 0.1), c + (sx * 0.2, 0.86, -0.6), G.rz(8))
    B.p("Egg", (0.6, 0.3, 0.5), c + (0.5, 1.35, 0.1), ori(0, 20, 30), "f4ecd8")
    return B.finish()


def p_volcano(sc, parent):
    B = Build(sc, parent, "MiniVolcano", seed=85)
    volcano(B, (0.0, 0.0, 0.0), 0.8)
    for k in range(2):
        B.p("Smoke", (1.6 - 0.3 * k, 1.4 - 0.2 * k, 1.6 - 0.3 * k), (0.2 * k, 8.6 + 1.5 * k, 0.1 * k),
            ori(10, 30 * k, 15), ("9a9490", "b0aaa6")[k], transparency=0.35)
    rock(B, (4.4, 0.0, -2.8), 1.4, ROCKC)
    return B.finish()


def p_amber(sc, parent):
    B = Build(sc, parent, "AmberRock", seed=86)
    rock(B, (0.0, 0.0, 0.0), 3.0, ROCKC)
    rock(B, (2.4, 0.0, -0.8), 1.6, ROCKC)
    B.p("Amber", (1.4, 1.9, 1.2), (0.3, 2.6, -0.9), ori(12, 30, 18), AMBER, material="Neon", flicker=0.08, lamp=True)
    B.p("Amber", (0.9, 1.2, 0.8), (-0.9, 2.1, -1.0), ori(-10, 50, -15), "ffb84a", material="Neon", lamp=True)
    B.p("Amber", (0.36, 0.24, 0.36), (0.3, 2.7, -1.55), ori(0, 30, 18), "3a2a1a")
    B.p("Amber", (0.6, 0.5, 0.5), (-1.9, 0.25, -2.1), ori(0, 20, 10), "ffb84a", material="Neon", lamp=True)
    return B.finish()


def p_prints(sc, parent):
    B = Build(sc, parent, "Footprints", seed=87)
    for k, (x, z, a) in enumerate(((-3.4, 1.2, -8.0), (0.2, -1.4, 4.0), (3.8, 1.0, -6.0))):
        R = G.ry(a + 90)
        c = np.array((x, 0.06, z))
        B.p("Print", (1.8, 0.12, 1.6), c, R, "5a4630")
        for j, t in enumerate((-35.0, 0.0, 35.0)):
            Rt = R @ G.ry(t)
            B.p("Print", (0.6, 0.14 + 0.01 * j, 1.5), c + Rt @ (0, 0.012 + 0.005 * j, -1.4), Rt, "4e3c28")
    return B.finish()


def p_skull(sc, parent):
    B = Build(sc, parent, "FossilSkull", seed=88)
    B.p("Ground", (6.4, 0.6, 4.4), (0.0, 0.3, 0.0), G.ry(6), EARTH[1])
    sk = np.array((0.8, 1.9, 0.0))
    R = G.rz(-10) @ G.rx(6)
    B.p("Skull", (4.2, 2.8, 2.7), sk, R, BONE[0])
    B.p("Skull", (3.6, 2.0, 2.2), sk + R @ (-3.3, -0.5, 0), R, BONE[2])
    B.p("Skull", (2.8, 0.6, 2.8), sk + R @ (0.5, 1.5, 0), R, BONE[1])
    B.plate("Skull", (1.2, 1.1, 0.12), sk + R @ (-0.3, 0.3, -1.4), R, col="3a3026")
    B.plate("Skull", (0.5, 0.36, 0.12), sk + R @ (-4.5, -0.1, -1.16), R, col="3a3026")
    for k in range(4):
        B.p("Tooth", (0.3, 0.5, 0.3), sk + R @ (-4.6 + 0.8 * k, -1.65, -0.75), R, BONE[2])
    B.p("Jaw", (5.4, 0.7, 2.0), (-0.6, 0.85, 0.3), G.ry(12) @ G.rz(4), BONE[1])
    return B.finish()


def p_horsetails(sc, parent):
    B = Build(sc, parent, "Horsetails", seed=89)
    rock(B, (0.0, 0.0, 0.0), 1.4, ROCKC)
    grass(B, (0.3, 0.0, -0.2), 6, ("5a8a3a", "6e9a44", "4a7a32"), h=(3.0, 5.2), r=1.2, name="Horsetail", w=0.42)
    for k in range(3):
        B.p("Horsetail", (0.55, 0.4, 0.55), (-0.6 + 0.7 * k, 0.2, -1.4 + 0.3 * k), G.ry(45), "8a6a3a")
    return B.finish()


AREA = register(Area("Dino", "Dino Valley", hero, [
    (p_cycad, prop_attrs(8, 0.85, 1.3, "Side", True)),
    (p_treefern, prop_attrs(6, 0.85, 1.3, "Side", True)),
    (p_ribs, prop_attrs(3, 0.9, 1.2, "Side", True)),
    (p_nest, prop_attrs(5, 0.9, 1.3, "Any", False)),
    (p_volcano, prop_attrs(3, 0.9, 1.2, "Edge", True)),
    (p_amber, prop_attrs(5, 0.85, 1.25, "Any", True)),
    (p_prints, prop_attrs(6, 0.9, 1.4, "Any", False)),
    (p_skull, prop_attrs(3, 0.9, 1.2, "Side", True)),
    (p_horsetails, prop_attrs(8, 0.8, 1.3, "Any", False)),
], ground="7ab24a"))
