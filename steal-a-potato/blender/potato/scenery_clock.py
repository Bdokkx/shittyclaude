"""Clockwork Yard: the hero, a clock tower with turning gears, and the area's props.

A brass and copper tower on a stone base with steps: copper panels in two shades between brass
bands, a big clock face at the top (hands at ten past ten), a glass case below it with the
pendulum, an open cupola on top with a bell and a weathervane. Gears turn on its front and sides
(Spin; meshing gears turn opposite ways). A workshop beside it with a chimney, a round window and
its own gear; copper pipes with valves and steam; gas lamps at the foot.
"""
import math

import numpy as np

import spsgeo as G

from .scenery import (Area, Build, INK, bar, ori, potato, prop_attrs, register, round3, shade)

BRASS = ("d4a43a", "c8962a", "e8c060")
COPPER = ("b87333", "a0622a", "c88a4a")
STEEL = ("8a9098", "6a7078", "a8aeb6")
STONE = ("6e6660", "5e5650", "7e7670")
IRON = "3a3f4a"
FACE = "f4ecd8"
STEAM = "e8eef4"


def axle_frame(axis):
    """A turn whose own Y runs along axis (a unit vector)."""
    y = np.asarray(axis, float)
    y = y / np.linalg.norm(y)
    ref = np.array((0.0, 1.0, 0.0)) if abs(y[1]) < 0.9 else np.array((1.0, 0.0, 0.0))
    x = np.cross(ref, y)
    x /= np.linalg.norm(x)
    z = np.cross(x, y)
    return np.column_stack((x, y, z))


def gear(B, c, r, axis, cols=BRASS, spin=None, t=0.6, teeth=4, name="Gear", phase=0.0):
    """A gear of radius r turning about axis through c: an eight-sided body, teeth from bars through
    the middle, a hub. Every part is centred on the axle with its own Y along it, so Spin turns it."""
    c = np.asarray(c, float)
    A = axle_frame(axis) @ G.ry(phase)
    k = 2 * r * 0.84
    out = [B.p(name, (k, t, k), c, A, cols[0], spin=spin),
           B.p(name, (k, t - 0.02, k), c, A @ G.ry(45), cols[1], spin=spin)]
    for j in range(teeth):
        out.append(B.p(name, (2 * r + 0.7, t - 0.06 - 0.01 * j, 0.62), c, A @ G.ry(22.5 + 180.0 / teeth * j), cols[2],
                       spin=spin))
    out.append(B.p(name, (r * 0.55, t + 0.25, r * 0.55), c, A @ G.ry(45), IRON, spin=spin))
    return out


def clock_face(B, c, r, R=None, name="Clock", hands=(305.0, 60.0)):
    """A clock face facing -Z of R: brass rim, cream dial, twelve marks, two hands at ten past ten."""
    R = np.eye(3) if R is None else R
    c = np.asarray(c, float)
    w = 2 * r * 0.9 + 0.8
    out = [B.p(name, (w, w, 0.5 - 0.04 * j), c, R @ G.rz(30 * j), BRASS[j % 2]) for j in range(3)]
    out += [B.p(name, (2 * r * 0.9, 2 * r * 0.9, 0.12), c + R @ (0, 0, -0.28 - 0.01 * j), R @ G.rz(30 * j), FACE,
                material="SmoothPlastic", shadow=False) for j in range(3)]
    k = min(1.0, r / 2.4)
    n = 12 if r >= 1.5 else 4
    for j in range(n):
        a = math.radians(360.0 / n * j)
        big = (j * 12 // n) % 3 == 0
        p = c + R @ (math.sin(a) * r * 0.82, math.cos(a) * r * 0.82, -0.36)
        out.append(B.p(name, ((0.32 if big else 0.2) * k + 0.05, (0.7 if big else 0.42) * k + 0.05, 0.1), p,
                       R @ G.rz(-360.0 / n * j), INK, material="SmoothPlastic", shadow=False))
    for j, (ang, L, w) in enumerate(((hands[0], r * 0.55, 0.42 * k + 0.08), (hands[1], r * 0.8, 0.3 * k + 0.06))):
        a = math.radians(ang)
        d = np.array((math.sin(a), math.cos(a), 0.0))
        p = c + R @ (d * (L / 2 - 0.08 * j) + np.array((0, 0, -0.42 - 0.05 * j)))
        out.append(B.p(name, (w, L, 0.1), p, R @ G.rz(-ang), INK, material="SmoothPlastic", shadow=False))
    out.append(B.p(name, (0.6, 0.6, 0.2), c + R @ (0, 0, -0.5), R @ G.rz(45), BRASS[2]))
    return out


def gas_lamp(B, base, h=7.0, name="Lamp"):
    base = np.asarray(base, float)
    out = [B.p(name, (1.3, 0.6, 1.3), base + (0, 0.3, 0), G.ry(45), IRON),
           B.p(name, (0.4, h, 0.4), base + (0, h / 2 + 0.5, 0), None, IRON),
           B.p(name, (1.2, 0.3, 1.2), base + (0, h + 0.4, 0), G.ry(45), BRASS[1]),
           B.p(name, (0.9, 1.2, 0.9), base + (0, h + 1.15, 0), None, "ffd27a", material="Neon", flicker=0.08,
               lamp=True),
           B.p(name, (1.3, 0.5, 1.3), base + (0, h + 2.0, 0), G.ry(45), IRON),
           B.p(name, (0.4, 0.5, 0.4), base + (0, h + 2.45, 0), None, BRASS[0])]
    return out


def steam(B, c, n=2, s=1.0, name="Steam"):
    c = np.asarray(c, float)
    return [B.p(name, ((1.3 - 0.2 * k) * s, (1.1 - 0.15 * k) * s, (1.3 - 0.2 * k) * s),
                c + (0.2 * k * s, 1.3 * k * s, 0.1 * k * s), ori(12, 30 * k, 10), STEAM, transparency=0.35)
            for k in range(n)]


# ==================================================================== the hero

def hero(sc, parent):
    B = Build(sc, parent, "Clock", seed=111)
    # the stone base and steps up to it
    B.p("Base", (16.0, 3.0, 13.0), (0.0, 1.5, 3.0), None, STONE[0], solid=True)
    B.p("Base", (16.6, 0.6, 13.6), (0.0, 3.2, 3.0), None, STONE[2], solid=True)
    for k in range(3):
        h = 1.0 * (k + 1)
        B.p("Step", (7.0, h, 1.2), (0.0, h / 2, -3.5 - 1.2 * (2 - k) - 0.6), None, STONE[k % 2], solid=True)
    # the tower: copper panels between brass bands
    y0, H = 3.5, 22.0
    zf = 3.0 - 4.0
    for k in range(8):
        x = -4.375 + 1.25 * k
        B.p("Tower", (1.25, H, 8.0 - 0.04 * (k % 2)), (x, y0 + H / 2, 3.0), None, COPPER[k % 2], solid=True)
    for y in (y0 + 0.4, y0 + 8.0, y0 + 15.0, y0 + H - 0.3):
        B.p("Band", (10.6, 0.7, 8.6), (0.0, y, 3.0), None, BRASS[1])
    # the clock face, the pendulum in its glass case
    clock_face(B, (0.0, y0 + 18.6, zf - 0.55), 3.6)
    B.p("Case", (3.4, 6.0, 0.12), (0.0, y0 + 11.4, zf - 0.36), None, "1e2a30", material="SmoothPlastic", shadow=False)
    B.p("Case", (3.6, 6.2, 0.14), (0.0, y0 + 11.4, zf - 0.5), None, "a8e0ff", transparency=0.55,
        material="SmoothPlastic", shadow=False)
    bar(B, "Pendulum", (0.0, y0 + 14.0, zf - 0.42), (0.6, y0 + 9.6, zf - 0.42), 0.2, BRASS[0], t=0.1)
    B.p("Pendulum", (1.3, 1.3, 0.16), (0.7, y0 + 9.2, zf - 0.44), G.rz(45), BRASS[2])
    for sx in (-1, 1):
        B.p("Case", (0.4, 6.6, 0.5), (sx * 1.95, y0 + 11.4, zf - 0.3), None, BRASS[1])
    B.p("Door", (3.0, 5.0, 0.12), (0.0, y0 + 2.6, zf - 0.06), None, "4a2a1a", material="SmoothPlastic", shadow=False)
    B.p("Door", (3.8, 0.6, 0.5), (0.0, y0 + 5.4, zf - 0.25), None, BRASS[1])
    # the cupola: four posts, a roof stepping up, a bell, a weathervane
    top = y0 + H
    for sx in (-1, 1):
        for sz in (-1, 1):
            B.p("Cupola", (0.8, 5.0, 0.8), (sx * 4.2, top + 2.5, 3.0 + sz * 3.2), None, BRASS[0])
    y = top + 5.0
    for k, (w, d, h) in enumerate(((11.0, 8.8, 0.8), (8.4, 6.6, 1.2), (5.6, 4.4, 1.2), (2.8, 2.2, 1.2))):
        B.p("Roof", (w, h, d), (0.0, y + h / 2, 3.0), None, (COPPER[2], "4a8a7a", "5a9a8a", "4a8a7a")[k])
        y += h - 0.02
    B.p("Bell", (2.6, 2.0, 2.6), (0.0, top + 2.4, 3.0), None, BRASS[0])
    B.p("Bell", (2.56, 1.96, 2.56), (0.0, top + 2.4, 3.0), G.ry(45), BRASS[2])
    B.p("Bell", (3.2, 0.5, 3.2), (0.0, top + 1.25, 3.0), G.ry(22.5), BRASS[1])
    bar(B, "Vane", (0.0, y - 0.1, 3.0), (0.0, y + 3.0, 3.0), 0.25, IRON)
    B.p("Vane", (2.6, 0.9, 0.12), (0.6, y + 2.6, 3.0), None, BRASS[2])
    # gears turning on the front and the sides
    gear(B, (-4.6, y0 + 4.6, zf - 0.6), 2.8, (0, 0, 1), spin=30.0)
    gear(B, (-1.0, y0 + 7.8, zf - 1.0), 1.7, (0, 0, 1), cols=(COPPER[0], COPPER[1], COPPER[2]), spin=-49.0, phase=10)
    gear(B, (4.5, y0 + 5.6, zf - 0.6), 2.2, (0, 0, 1), cols=(STEEL[0], STEEL[1], STEEL[2]), spin=-38.0, phase=5)
    gear(B, (-5.5, y0 + 14.0, 3.0), 2.6, (1, 0, 0), spin=24.0)
    gear(B, (5.5, y0 + 12.0, 3.0), 2.4, (1, 0, 0), cols=(COPPER[0], COPPER[1], COPPER[2]), spin=-26.0)
    # the workshop beside it: brick walls, a round window, a chimney with steam
    wx = 14.5
    B.p("Workshop", (9.0, 9.0, 9.0), (wx, 4.5, 4.0), None, "8a4a3a", solid=True)
    for k in range(4):
        B.p("Workshop", (9.2, 0.5, 9.2 - 0.05 * (k % 2)), (wx, 1.5 + 2.2 * k, 4.0), None, "7a3e30")
    B.p("Workshop", (10.2, 0.8, 10.2), (wx, 9.4, 4.0), None, STONE[1], solid=True)
    clock_face(B, (wx, 5.8, -0.68), 1.8, name="Window", hands=(0.0, 180.0))
    B.p("Chimney", (2.0, 5.0, 2.0), (wx + 2.5, 12.3, 6.5), None, "7a3e30")
    B.p("Chimney", (2.6, 0.6, 2.6), (wx + 2.5, 15.0, 6.5), None, IRON)
    steam(B, (wx + 2.6, 16.2, 6.5), 3, 1.2)
    gear(B, (wx - 4.7, 5.2, 4.0), 2.0, (1, 0, 0), cols=(STEEL[0], STEEL[1], STEEL[2]), spin=35.0)
    # copper pipes up the other side, valves, a steam vent
    px = -7.2
    for k, (z, h) in enumerate(((0.6, 18.0), (2.0, 14.0))):
        B.p("Pipe", (0.9 + 0.1 * k, h, 0.9), (px - 0.3 * k, y0 + h / 2, z), None, COPPER[k])
        B.p("Pipe", (1.3, 0.5, 1.3), (px - 0.3 * k, y0 + h * 0.6, z), G.ry(45), BRASS[0])
    bar(B, "Pipe", (px, y0 + 18.0, 0.6), (px + 2.6, y0 + 18.0, 0.6), 0.8, COPPER[0])
    gear(B, (px - 1.0, y0 + 6.0, 0.2), 0.8, (-1, 0, 0), cols=("c8202a", "a81a22", "e8403a"), teeth=2, t=0.3)
    steam(B, (px - 0.3, y0 + 18.8, 2.0), 2)
    for sx in (-1, 1):
        gas_lamp(B, (sx * 6.2, 0.0, -6.0), 6.0)
    # a frame of great gears on the other side
    fx = -15.5
    for dx in (-3.6, 3.6):
        B.p("Frame", (1.0, 13.0, 1.0), (fx + dx, 6.5, 5.0), None, IRON, solid=True)
    B.p("Frame", (8.6, 1.0, 1.2), (fx, 13.4, 5.0), None, BRASS[1])
    B.p("Frame", (8.4, 1.0, 3.0), (fx, 0.5, 5.0), None, STONE[1], solid=True)
    gear(B, (fx + 0.6, 8.0, 4.0), 3.6, (0, 0, 1), spin=18.0, teeth=4)
    gear(B, (fx - 2.4, 3.6, 3.8), 1.8, (0, 0, 1), cols=(COPPER[0], COPPER[1], COPPER[2]), spin=-36.0, teeth=3)
    return B.finish()


# ==================================================================== props

def p_gear(sc, parent):
    B = Build(sc, parent, "GearStand", seed=121)
    B.p("Stand", (3.6, 0.8, 2.4), (0.0, 0.4, 0.0), None, STONE[0])
    for sx in (-1, 1):
        B.p("Stand", (0.5, 4.6, 0.6), (sx * 1.0, 3.0, 0.0), None, IRON)
    gear(B, (0.0, 5.0, -0.3), 2.8, (0, 0, 1), spin=30.0)
    gear(B, (2.9, 2.4, -0.9), 1.3, (0, 0, 1), cols=(COPPER[0], COPPER[1], COPPER[2]), spin=-62.0, teeth=3)
    return B.finish()


def p_pipes(sc, parent):
    B = Build(sc, parent, "SteamPipes", seed=122)
    for k, (x, z, h, col) in enumerate(((-1.4, 0.0, 6.0, COPPER[0]), (0.2, 0.6, 8.0, COPPER[1]), (1.6, -0.2, 4.6,
                                                                                                  COPPER[2]))):
        B.p("Pipe", (1.0 + 0.1 * k, h, 1.0 + 0.1 * k), (x, h / 2, z), None, col)
        B.p("Pipe", (1.4, 0.4, 1.4), (x, h * 0.4, z), G.ry(45), BRASS[k % 2])
    bar(B, "Pipe", (-1.4, 6.0, 0.0), (0.2, 6.6, 0.6), 0.9, COPPER[0])
    bar(B, "Pipe", (1.6, 4.6, -0.2), (0.2, 5.4, 0.6), 0.9, COPPER[2])
    gear(B, (1.6, 3.2, -0.95), 0.75, (0, 0, -1), cols=("c8202a", "a81a22", "e8403a"), teeth=2, t=0.3, name="Valve")
    clock_face(B, (-1.4, 3.6, -0.8), 0.6, name="Gauge", hands=(40.0, 40.0))
    steam(B, (0.2, 8.6, 0.6), 2)
    return B.finish()


def p_lamp(sc, parent):
    B = Build(sc, parent, "GasLamp", seed=123)
    gas_lamp(B, (0.0, 0.0, 0.0), 7.0)
    for sx in (-1, 1):
        bar(B, "Lamp", (0.0, 6.2, 0.0), (sx * 1.4, 6.9, 0.0), 0.2 + 0.04 * (sx > 0), IRON)
    B.p("Lamp", (0.8, 0.8, 0.8), (0.0, 7.6 - 3.6, 0.0), G.ry(45), BRASS[1])
    gear(B, (0.0, 2.2, -0.35), 0.6, (0, 0, -1), cols=BRASS, teeth=2, t=0.2, name="Badge")
    return B.finish()


def p_boiler(sc, parent):
    B = Build(sc, parent, "Boiler", seed=124)
    for sx in (-1, 1):
        for sz in (-1, 1):
            B.p("Leg", (0.5, 1.4, 0.5), (sx * 1.6, 0.7, sz * 1.3), None, IRON)
    round3(B, "Boiler", (0.0, 3.6, 0.0), 4.4, 4.4, 4.0, COPPER)
    for k, y in enumerate((2.2, 3.6, 5.0)):
        B.p("Band", (4.2, 0.3, 3.7), (0.0, y, 0.0), G.ry(45 * (k % 2) + 22.5), BRASS[k % 2])
    B.p("Fire", (1.4, 1.0, 0.12), (0.0, 2.5, -2.06), None, "ff8a1a", material="Neon", flicker=0.2, lamp=True)
    clock_face(B, (1.2, 4.5, -2.15), 0.55, name="Gauge", hands=(70.0, 70.0))
    B.p("Chimney", (1.0, 3.0, 1.0), (-0.8, 7.2, 0.4), None, IRON)
    steam(B, (-0.7, 9.2, 0.4), 2)
    return B.finish()


def p_gearpile(sc, parent):
    B = Build(sc, parent, "GearPile", seed=125)
    gear(B, (0.0, 0.35, 0.0), 2.2, (0, 1, 0), teeth=3, t=0.5)
    gear(B, (1.4, 0.95, 0.6), 1.4, (0.2, 1, 0.1), cols=(COPPER[0], COPPER[1], COPPER[2]), teeth=2, t=0.4)
    gear(B, (-1.9, 1.4, -0.4), 1.2, (1, 0.3, 0.6), cols=(STEEL[0], STEEL[1], STEEL[2]), teeth=2, t=0.4)
    return B.finish()


def p_watch(sc, parent):
    B = Build(sc, parent, "PocketWatch", seed=126)
    R = G.rx(-14)
    c = np.array((0.0, 3.0, 0.4))
    clock_face(B, c, 2.4, R=R, name="Watch", hands=(300.0, 45.0))
    B.p("Watch", (5.4, 5.4, 0.7), c + R @ (0, 0, 0.45), R, BRASS[0])
    B.p("Watch", (1.1, 1.0, 0.9), c + R @ (0, 3.1, 0.15), R, BRASS[1])
    B.p("Watch", (1.6, 0.4, 0.5), c + R @ (0, 3.7, 0.2), R, BRASS[2])
    B.p("Stand", (4.4, 0.6, 2.8), (0.0, 0.3, 0.9), None, "6a3a2a")
    return B.finish()


def p_streetclock(sc, parent):
    B = Build(sc, parent, "StreetClock", seed=127)
    B.p("Post", (1.6, 0.8, 1.6), (0.0, 0.4, 0.0), G.ry(45), STONE[0])
    B.p("Post", (0.6, 8.0, 0.6), (0.0, 4.6, 0.0), None, IRON)
    B.p("Post", (2.8, 2.8, 1.4), (0.0, 9.4, 0.0), None, IRON)
    clock_face(B, (0.0, 9.4, -0.75), 1.2)
    B.p("Post", (0.8, 0.8, 0.8), (0.0, 11.2, 0.0), G.ry(45), BRASS[0])
    return B.finish()


def p_spring(sc, parent):
    B = Build(sc, parent, "GiantSpring", seed=128)
    B.p("Crate", (3.2, 1.6, 3.2), (0.0, 0.8, 0.0), G.ry(10), "b88450")
    for k in range(8):
        y = 1.8 + 0.7 * k
        B.p("Spring", (2.6, 0.3 + 0.02 * (k % 2), 0.36), (0.0, y, -1.1 + 0.03 * (k % 2)), G.rx(8), STEEL[k % 2])
        B.p("Spring", (2.6, 0.3 + 0.02 * (k % 2), 0.36), (0.0, y + 0.35, 1.1 - 0.03 * (k % 2)), G.rx(-8),
            STEEL[(k + 1) % 2])
    return B.finish()


AREA = register(Area("Clock", "Clockwork Yard", hero, [
    (p_gear, prop_attrs(6, 0.85, 1.25, "Side", True)),
    (p_pipes, prop_attrs(5, 0.9, 1.3, "Edge", True)),
    (p_lamp, prop_attrs(6, 0.95, 1.15, "Side", False)),
    (p_boiler, prop_attrs(4, 0.9, 1.2, "Side", True)),
    (p_gearpile, prop_attrs(8, 0.8, 1.3, "Any", False)),
    (p_watch, prop_attrs(3, 0.9, 1.2, "Side", True)),
    (p_streetclock, prop_attrs(4, 0.95, 1.15, "Side", False)),
    (p_spring, prop_attrs(5, 0.85, 1.2, "Any", True)),
], ground="a89a80"))
