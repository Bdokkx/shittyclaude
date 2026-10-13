"""Cosmic Garden: the hero, a crashed retro rocket with its potato astronaut, and the area's props.

A big rocket, white with a red nose cone, a red band and three red fins, has come down nose first
into a crater: it leans out of a ring of dark slabs, its nose buried among boulders, glowing cracks
running across the scorched crater floor. Its engine points up at the sky and still burns (Neon
orange and blue that flicker and light up at night), puffs of smoke drifting out of it. Round
portholes glow along its side; the hatch hangs open, a ladder runs down from it and the potato
astronaut, in a glass-dome helmet of pale blue blocks, climbs down it waving. Torn hull panels and a
fin lie about and a little potato flag is planted on the crater rim.
"""
import math

import numpy as np

import spsgeo as G
from spsgeo import CF

from .scenery import (Area, Build, INK, bar, fern, ori, potato, prop_attrs, register, rock, shade, turn)
from .scenery_candy import T8, drum, ring

HULL = ("f4f4fa", "e2e4ee", "ffffff")
RED = ("e8303a", "c8202a", "ff4a4a")
STEEL = ("8a90a0", "6a7080", "b4bac8")
DARK = ("3a3f4a", "2a2e38", "4a505c")
GLASS = ("bfe8ff", "a8dcff", "d8f2ff")
ROCK = ("807c9c", "6e6a8a", "9490ae", "5c5878")
MOON = ("b9b4c8", "a3adeb", "8e89a0")
FLOOR = ("2a2842", "33304e")
FIRE = ("ff7a1a", "ffb02e", "ffe066")
JET = ("6ad8ff", "bfeeff")
SMOKE = ("f4f4fa", "ffffff", "e4e4ee")
SKIN = ("d9b07a", "c49a64", "e8c490")
SUIT = ("f4f4fa", "d8dae6", "ffffff")
GOLD = ("f5c518", "e0a800", "ffd447")
ALIEN = ("4fae3a", "3f962e", "62c24a")
NEON = ("ff5ad8", "40f0ff", "a8ff4a", "b67cff", "ffe14d")
PLANETS = (("ff9f3d", "f07412", "ffc078"), ("4fd8c8", "2fb8a8", "8ff0e4"), ("b47cff", "9a5ef0", "d4b0ff"),
           ("ff6f9f", "e8507f", "ffa4c4"))


# ==================================================================== shapes

def star8(B, name, c, w, h, cols, R=None, **kw):
    """A small round: a square and the same square turned 45 degrees, a hair apart in height."""
    R = np.eye(3) if R is None else R
    c = np.asarray(c, float)
    return [B.p(name, (w, h, w), c, R, cols[0], **kw),
            B.p(name, (w - 0.02, h - 0.04, w - 0.02), c, R @ G.ry(45), cols[1 % len(cols)], **kw)]


def star(B, c, r, col, R=None, name="Star", flicker=0.08, lamp=True, material="Neon", d=0.3):
    """A five-point star facing -Z of R: five rays round a turned centre block."""
    R = np.eye(3) if R is None else R
    c = np.asarray(c, float)
    kw = dict(material=material, lamp=lamp and material == "Neon")
    if material == "Neon" and flicker:
        kw["flicker"] = flicker
    out = [B.p(name, (r * 0.62, r * 0.62, d), c, R @ G.rz(45), col, **kw)]
    for i in range(5):
        Rr = R @ G.rz(72.0 * i)
        out.append(B.p(name, (r * 0.36, r, d - 0.06 + 0.012 * i), c + Rr @ (0, r * 0.62, 0), Rr, col, **kw))
    return out


def crater(B, c, r, n, h, cols, solid=False, tilt=24.0, depth=2.4, floor=FLOOR, name="Crater"):
    """A crater: a ring of slabs leaning in over it (their outer faces the outer slope of the rim),
    each turned to follow the ring and a little different in height (Folk Valley's turned slabs), a
    scorched floor inside."""
    rng = B.rng
    c = np.asarray(c, float)
    out = []
    L = 2 * math.pi * r / n * 1.14
    for k in range(n):
        a = 360.0 * k / n + float(rng.uniform(-5, 5))
        hk = h * float(rng.uniform(0.78, 1.22))
        R = G.ry(-a) @ G.rx(tilt + float(rng.uniform(-4, 4))) @ G.rz(float(rng.uniform(-5, 5)))
        out.append(B.p(name, (L + 0.04 * (k % 3), hk, depth + 0.04 * (k % 2)), c + G.ry(-a) @ (0.0, hk * 0.36, -r),
                       R, cols[k % len(cols)], solid=solid))
    if floor:
        out += star8(B, "Floor", c + (0, 0.05, 0), r * 1.3, 0.1, floor)
    return out


def smoke(B, c, s, heading=0.0, name="Smoke", tr=0.55):
    """A puff of smoke: a wide block, a crossing one and a turned one on top, pale and see-through."""
    c = np.asarray(c, float)
    return [B.p(name, (s * 1.3, s * 0.7, s * 0.9), c, ori(6, heading, 8), SMOKE[0], transparency=tr),
            B.p(name, (s * 0.85, s * 0.66, s * 1.2), c + (s * 0.12, s * 0.06, 0), ori(-7, heading + 20, -5), SMOKE[1],
                transparency=tr),
            B.p(name, (s * 0.75, s * 0.6, s * 0.75), c + (-s * 0.1, s * 0.46, -s * 0.05), ori(-10, heading + 45, 6),
                SMOKE[2], transparency=tr)]


def glass_dome(B, c, r, h, R=None, cols=GLASS, name="Helmet", tr=0.45, clear=0.72):
    """A glass dome: eight thin panes round an eight-sided ring and a lid, pale blue and see-through,
    one pane deep; the three panes in front (-Z of R) clearer, so the face inside shows."""
    R = np.eye(3) if R is None else R
    c = np.asarray(c, float)
    w = 2 * r * T8 + 0.12
    kw = dict(transparency=tr, shadow=False)
    out = []
    for k in range(8):
        Rk = R @ G.ry(45 * k)
        t = clear if k in (0, 1, 7) else tr
        out.append(B.p(name, (w, h - 0.04 * (k % 2), 0.14), c + Rk @ (0, 0, -r), Rk, cols[k % 2], transparency=t,
                       shadow=False))
    out += drum(B, name, c + R @ (0, h / 2 + 0.08, 0), r + 0.12, 0.2, (cols[2], cols[1]), R=R, **kw)
    out += star8(B, name, c + R @ (0, h / 2 + 0.3, 0), r * 1.2, 0.36, (cols[1], cols[2]), R=R, **kw)
    return out


def porthole(B, c, s=1.9, lit=True, name="Porthole"):
    """A round porthole on a face facing -Z (c is its middle on the face): a steel rim of two
    squares, one turned, and the glass (Neon if lit)."""
    c = np.asarray(c, float)
    out = star8(B, name, c + (0, 0, -0.12), s, 0.3, (STEEL[2], STEEL[0]), R=G.rx(90))
    if lit:
        out.append(B.p(name, (s * 0.64, s * 0.64, 0.12), c + (0, 0, -0.33), G.rz(22.5), JET[1], material="Neon",
                       lamp=True))
    else:
        out.append(B.plate(name, (s * 0.64, s * 0.64, 0.12), c + (0, 0, -0.33), G.rz(22.5), col=GLASS[1]))
    return out


def potato_flag(B, base, h=7.0, heading=0.0, cloth="3b6bd8", name="Flag"):
    """A flag on a pole, stiff as on the moon: a blue cloth with a smiling potato on it."""
    base = np.asarray(base, float)
    out = [B.p(name, (0.3, h + 0.3, 0.3), base + (0, h / 2 - 0.15, 0), None, STEEL[2]),
           B.p(name, (0.55, 0.55, 0.55), base + (0, h + 0.1, 0), ori(35.26, 45, 0), GOLD[0])]
    with B.at(CF(base + (0, h - 1.4, 0), G.ry(heading))):
        out.append(B.p(name, (3.6, 2.4, 0.14), (1.95, 0.0, 0.0), G.rz(-3), cloth))
        out.append(B.p(name, (3.8, 0.24, 0.24), (1.95, 1.25, 0.0), None, STEEL[2]))
        out.append(B.plate(name, (1.2, 1.5, 0.1), (1.95, -0.1, -0.11), G.rz(-3), col=SKIN[0]))
        for sx in (-1, 1):
            out.append(B.plate(name, (0.18, 0.32, 0.1), (1.95 + sx * 0.26, 0.12, -0.17), G.rz(-3), col=INK))
        out.append(B.plate(name, (0.5, 0.14, 0.1), (1.94, -0.36, -0.17), G.rz(-3), col=INK))
    return out


def astronaut(B, c, s=4.2, R=None, name="Astronaut"):
    """A potato astronaut, c the middle of the potato: white boots, a white collar, a backpack with a
    light, one arm waving and one holding on, a glass-dome helmet of pale blue blocks over it all and
    an aerial with a glowing tip."""
    R = np.eye(3) if R is None else R
    c = np.asarray(c, float)
    potato(B, c, s, SKIN, R=R, name=name, glints=True, cheeks="ff9aa8")
    for sx in (-1, 1):
        B.p("Suit", (1.15, 1.1, 1.35), c + R @ (sx * s * 0.2, -s / 2 - 0.35, -0.08), R, SUIT[0])
    drum(B, "Suit", c + R @ (0, -s * 0.36, 0), s * 0.5, s * 0.2, (SUIT[0], SUIT[1]), R=R)
    B.p("Suit", (s * 0.62, s * 0.58, 1.0), c + R @ (0, -s * 0.12, s * 0.56 + 0.45), R, SUIT[1])
    B.p("Suit", (0.5, 0.5, 0.14), c + R @ (s * 0.16, 0.0, s * 0.56 + 1.0), R, "ff4d6d", material="Neon", flicker=0.3,
        lamp=True)
    sh = s * 0.5
    bar(B, "Suit", c + R @ (-sh, -s * 0.3, 0), c + R @ (-s * 0.82, s * 0.32, -0.3), 0.8, SUIT[0])     # waving
    B.p("Suit", (0.95, 0.95, 0.95), c + R @ (-s * 0.86, s * 0.42, -0.32), R @ G.rz(20), SUIT[2])
    bar(B, "Suit", c + R @ (sh, -s * 0.3, 0), c + R @ (s * 0.78, -s * 0.05, 0.45), 0.8, SUIT[0])        # holding on
    B.p("Suit", (0.9, 0.9, 0.9), c + R @ (s * 0.8, 0.0, 0.5), R, SUIT[2])
    glass_dome(B, c + R @ (0, s * 0.14, 0), s * 0.6, s * 0.8 + 0.3, R=R)
    top = c + R @ (s * 0.18, s * 0.6, 0.1)
    bar(B, "Aerial", top, top + R @ (0.2, 1.3, 0), 0.16, STEEL[2])
    B.p("Aerial", (0.42, 0.42, 0.42), top + R @ (0.21, 1.45, 0), R @ ori(35.26, 45, 0), "ff5ad8", material="Neon",
        flicker=0.2, lamp=True)


# ==================================================================== the hero

def rocket(B):
    """The rocket in its own frame: its nose tip at the origin, its axis up its own Y, the side with
    the portholes and the hatch facing -Z. Returns the hatch's sill (in this frame)."""
    nose = ((1.0, 0.0, 2.0, RED[1]), (2.0, 1.8, 4.2, RED[0]), (2.9, 4.0, 6.7, RED[2]), (3.6, 6.5, 9.2, RED[0]))
    for k, (r, y0, y1, col) in enumerate(nose):
        drum(B, "Nose", (0.0, (y0 + y1) / 2, 0.0), r, y1 - y0, (col, shade(col, -0.1)), solid=k >= 2)
    drum(B, "Body", (0.0, 18.05, 0.0), 4.0, 18.0, HULL, solid=True)                   # 9.05 .. 27.05
    drum(B, "Band", (0.0, 16.6, 0.0), 4.2, 2.4, RED)
    drum(B, "Band", (0.0, 26.9, 0.0), 4.18, 1.4, (RED[1], RED[0]))
    drum(B, "Nozzle", (0.0, 28.3, 0.0), 2.6, 1.8, DARK)
    drum(B, "Nozzle", (0.0, 30.0, 0.0), 3.3, 2.0, (DARK[2], DARK[0]))                  # the bell, 29.0 .. 31.0
    fire = dict(material="Neon", flicker=0.18, lamp=True)
    drum(B, "Engine", (0.0, 30.9, 0.0), 2.85, 0.5, (FIRE[0], FIRE[1]), **fire)
    star8(B, "Engine", (0.0, 31.2, 0.0), 2.7, 0.6, (JET[0], JET[1]), **fire)
    for k, (w, hh, y, col, a) in enumerate(((3.0, 3.0, 32.6, FIRE[0], 10), (2.1, 2.6, 34.2, FIRE[1], -14),
                                             (1.3, 2.0, 35.7, FIRE[2], 20))):
        B.p("Engine", (w, hh, w), (0.25 * k, y, -0.15 * k), ori(a, 45 * k + 20, a * 0.6), col, **fire)
    # three fins at the tail, swept back past the engine; none on the side facing -Z
    for k, phi in enumerate((330.0, 210.0, 90.0)):
        with B.at(CF(np.zeros(3), G.ry(-phi))):
            B.p("Fin", (3.0, 6.4, 0.7), (5.4, 25.6, 0.0), None, RED[0])
            B.p("Fin", (2.3, 7.4, 0.66), (7.3, 29.0, 0.0), G.rz(-14), RED[1])
            bar(B, "Fin", (3.8, 20.2, 0.0), (6.6, 24.6, 0.0), 1.6, RED[2], t=0.74, n=(0, 0, 1))
    # the hatch below the band, portholes above it, on the side facing -Z
    for k, y in enumerate((20.4, 24.0)):
        porthole(B, (0.0, y, -4.0), lit=True)
    hy = 12.2
    B.p("Hatch", (2.9, 3.9, 0.16), (0.0, hy, -4.06), None, STEEL[0])
    B.plate("Hatch", (2.4, 3.3, 0.12), (0.0, hy, -4.16), col="141428")
    with B.at(CF(np.array((1.3, hy, -4.15)), G.ry(-112))):
        B.p("Door", (2.5, 3.5, 0.3), (-1.28, 0.0, 0.0), None, HULL[1])
        B.p("Door", (2.54, 0.5, 0.34), (-1.28, 0.9, 0.0), None, RED[0])
        B.p("Door", (0.9, 0.9, 0.36), (-1.28, -0.3, 0.0), G.rz(45), JET[1], material="Neon", lamp=True)
    return np.array((0.0, hy - 1.8, -4.25))


def hero(sc, parent):
    B = Build(sc, parent, "Cosmic", seed=401)
    # the crater: a ring of dark slabs round a scorched floor, glowing cracks, boulders round the nose
    cx, cz = 7.8, -1.4
    crater(B, (cx, 0.0, cz), 7.6, 13, 2.5, ROCK, solid=True, depth=2.8)
    for k, (a, L) in enumerate(((-82.0, 4.2), (-8.0, 4.6), (52.0, 4.4), (112.0, 3.8))):       # cracks out of the rim
        p0 = np.array((cx, 0.0, cz))
        pts = []
        for j, (rr, da) in enumerate(((7.4, 0.0), (7.4 + L * 0.5, 7.0 * (-1) ** k), (7.4 + L, -3.0 * (-1) ** k))):
            ang = math.radians(a + da)
            pts.append(p0 + (math.sin(ang) * rr, 0.13 + 0.02 * j, -math.cos(ang) * rr))
        for j in range(2):
            bar(B, "Crack", pts[j], pts[j + 1], 0.5 - 0.12 * j, FIRE[(k + j) % 2], t=0.14 + 0.03 * j, n=(0, 1, 0),
                over=0.15, material="Neon", flicker=0.25, lamp=True)
    for k, (x, z, s, h) in enumerate(((cx + 3.2, cz - 2.6, 3.8, 20.0), (cx - 0.4, cz - 3.9, 3.0, 70.0),
                                      (cx + 2.8, cz + 3.0, 3.4, 40.0), (cx - 2.8, cz + 2.6, 2.8, 10.0),
                                      (cx - 1.8, cz - 7.9, 2.6, 30.0), (cx + 7.9, cz - 1.8, 3.4, 55.0))):
        rock(B, (x, 0.0, z), s, (ROCK[2], ROCK[0], ROCK[1]), name="Boulder", solid=True, heading=h)
    # the rocket, nose first in the crater, leaning out of it
    S = CF(np.array((cx + 0.8, -0.5, cz + 0.2)), G.rz(36.0) @ G.rx(7.0))
    with B.at(S):
        sill = rocket(B)
    # smoke from the engine, drifting off; dust over the crater
    tail = S * np.array((0.0, 35.4, 0.0))
    for k, (dx, dy, s) in enumerate(((-1.6, 1.2, 2.4), (-4.0, 3.0, 3.0), (-6.8, 4.2, 3.4))):
        smoke(B, tail + (dx, dy, 0.8 * k), s, heading=30 * k)
    smoke(B, (cx - 4.6, 0.8, cz - 4.2), 2.2, heading=15)
    # the ladder from the hatch, the astronaut climbing down it, waving
    top = S * sill
    foot = np.array((top[0] - 0.4, 0.0, top[2] - 4.8))
    along = (top - foot) / np.linalg.norm(top - foot)
    side = np.cross(along, (0.0, 0.0, -1.0))
    side /= np.linalg.norm(side)
    for sx in (-1, 1):
        bar(B, "Ladder", foot + side * sx * 0.95, top + side * sx * 0.95 + along * 0.6, 0.3, STEEL[2],
            t=0.3 + 0.04 * (sx > 0), n=(0, 0, -1))
    L = float(np.linalg.norm(top - foot))
    n = 5
    for j in range(n):
        p = foot + along * (1.0 + (L - 1.6) * j / (n - 1))
        bar(B, "Ladder", p - side * 0.95, p + side * 0.95, 0.24, STEEL[0], t=0.24, over=0.1)
    s = 4.2
    astronaut(B, foot + along * 2.2 + np.array((0.0, s * 0.5 + 0.35, -0.95)), s, R=G.ry(8))
    # the flag on the rim, panels and a fin torn off
    potato_flag(B, (cx + 5.0, 0.7, cz - 7.4), h=7.4, heading=-20)
    for k, (x, z, h, tilt, roll) in enumerate(((-9.6, -8.6, 30.0, 14, -8), (cx + 9.6, cz + 2.0, -40.0, -18, 10),
                                              (-16.4, -1.0, 75.0, 22, 6))):
        R = ori(tilt, h, roll)
        B.p("Panel", (3.0, 0.3, 2.2), (x, 0.55, z), R, HULL[k % 2])
        B.p("Panel", (3.04, 0.34, 0.5), (x, 0.55, z) + R @ (0, 0, -0.7), R, RED[k % 2])
    with B.at(CF(np.array((-13.0, 0.0, -6.4)), G.ry(35) @ G.rz(-62))):
        B.p("Fin", (2.6, 5.0, 0.7), (0.0, 2.6, 0.0), None, RED[0])
        B.p("Fin", (1.8, 3.4, 0.66), (1.4, 5.4, 0.0), G.rz(-14), RED[1])
    # the garden coming up through it: glowing alien plants
    for k, (x, z, h) in enumerate(((17.6, -7.6, 0.0), (-5.4, -10.2, 140.0))):
        b = np.array((x, 0.15, z))
        fern(B, b, 4, ("2fbfa0", "1f9f84", "3fd8b8"), length=2.0, rise=26, w=0.5, name="AlienPlant", heading=h)
        alien_stem(B, b, (b + (0.4, 2.2, -0.2), b + (1.1, 3.8, 0.1), b + (0.7, 5.0, 0.3)), 0.4, "8a5ad8", NEON[k % 2])
        alien_stem(B, b + (0.1, 0.0, 0.2), (b + (-0.8, 1.6, 0.3), b + (-1.5, 2.6, 0.0)), 0.36, "2fbfa0", NEON[2 + k],
                   s=0.7)
    return B.finish()


# ==================================================================== props

def p_planet(sc, parent):
    B = Build(sc, parent, "RingPlanet", seed=411)
    star8(B, "Base", (0.0, 0.3, 0.0), 2.6, 0.6, (ROCK[1], ROCK[0]))
    bar(B, "Pole", (0.0, 0.5, 0.0), (0.15, 6.0, 0.0), 0.4, STEEL[1])
    c = np.array((0.2, 7.8, 0.0))
    A = G.rz(-22.0) @ G.rx(12.0)
    col = PLANETS[0]
    spin = dict(spin=24.0)
    drum(B, "Planet", c, 2.1, 3.0, (col[0], col[1]), R=A, **spin)
    for sy in (-1, 1):
        star8(B, "Planet", c + A @ (0, sy * 1.65, 0), 2.9, 0.7, (col[2], col[0]), R=A, **spin)
    drum(B, "Ring", c, 3.6, 0.2, ("f8e8c8", "e8d4b0"), R=A, **spin)
    drum(B, "Ring", c, 2.95, 0.36, ("c8a0ff", "b48cf0"), R=A, **spin)
    return B.finish()


def p_crater(sc, parent):
    B = Build(sc, parent, "Crater", seed=412)
    crater(B, (0.0, 0.0, 0.0), 3.2, 9, 1.1, (MOON[2], MOON[0], ROCK[2]), tilt=28.0, depth=1.8)
    for k, (x, z, s) in enumerate(((0.9, -0.6, 0.7), (-1.1, 0.4, 0.55), (0.2, 1.2, 0.45))):
        B.p("Pebble", (s, s * 0.7, s), (x, s * 0.3, z), turn(B.rng), MOON[k % 3])
    B.p("Ember", (0.8, 1.1, 0.8), (-0.2, 0.45, -0.3), ori(20, 30, 15), NEON[1], material="Neon", flicker=0.15,
        lamp=True)
    B.p("Ember", (0.5, 0.7, 0.5), (0.3, 0.35, 0.2), ori(-25, 10, 20), NEON[3], material="Neon", flicker=0.15, lamp=True)
    return B.finish()


def p_dish(sc, parent):
    B = Build(sc, parent, "SatelliteDish", seed=413)
    star8(B, "Base", (0.0, 0.5, 0.0), 2.8, 1.0, (STEEL[1], STEEL[0]))
    B.p("Mast", (0.8, 3.2, 0.8), (0.0, 2.6, 0.0), None, STEEL[0])
    B.p("Mast", (1.4, 1.0, 1.4), (0.0, 4.3, 0.0), G.ry(45), STEEL[2])
    D = CF(np.array((0.0, 5.6, 0.0)), G.ry(15) @ G.rx(42))
    with B.at(D):
        drum(B, "Dish", (0.0, 0.0, 0.0), 3.0, 0.4, (HULL[0], HULL[1]), R=G.rx(90))
        ring(B, "Dish", (0.0, 0.0, -0.35), G.rx(90), 2.9, 0.5, 0.6, (HULL[2], HULL[1]))
        feed = np.array((0.0, 0.0, -3.0))
        for k in range(3):
            a = math.radians(90 + 120 * k)
            bar(B, "Strut", (math.cos(a) * 2.6, math.sin(a) * 2.6, -0.5), feed, 0.2, STEEL[1], t=0.2 + 0.03 * k)
        B.p("Feed", (0.7, 0.7, 0.9), feed + (0, 0, -0.2), None, STEEL[2])
        B.p("Light", (0.42, 0.42, 0.42), feed + (0, 0, -0.85), ori(35.26, 45, 0), "ff3b5c", material="Neon",
            flicker=0.5, lamp=True)
    return B.finish()


def alien_stem(B, base, pts, w, col, bulb, s=0.9, name="AlienPlant"):
    """A curling stem through pts (from base) with a glowing bulb at its tip."""
    p = [np.asarray(base, float)] + [np.asarray(q, float) for q in pts]
    for i in range(len(p) - 1):
        bar(B, name, p[i], p[i + 1], w * (1 - 0.15 * i), col, over=0.12, t=w * (1 - 0.15 * i) + 0.03 * (i % 2))
    tip = p[-1]
    B.p("Bulb", (s, s, s), tip, ori(35.26, 45, 0), bulb, material="Neon", flicker=0.12, lamp=True)
    B.p("Bulb", (s * 0.6, s * 0.6, s * 0.6), tip + (0, s * 0.55, 0), ori(20, 20, 0), shade(bulb, 0.4), material="Neon",
        lamp=True)


def p_plants(sc, parent):
    B = Build(sc, parent, "AlienPlants", seed=414)
    fern(B, (0.0, 0.1, 0.0), 6, ("2fbfa0", "1f9f84", "3fd8b8"), length=2.2, rise=28, w=0.55)
    alien_stem(B, (0.0, 0.2, 0.0), ((0.4, 2.4, -0.2), (1.2, 4.2, 0.1), (0.8, 5.6, 0.4)), 0.42, "8a5ad8", NEON[0])
    alien_stem(B, (0.1, 0.2, 0.2), ((-0.8, 1.8, 0.3), (-1.6, 3.0, 0.0)), 0.38, "2fbfa0", NEON[1], s=0.75)
    alien_stem(B, (0.0, 0.2, 0.1), ((0.3, 1.6, 1.0), (0.2, 2.6, 1.8)), 0.34, "6a46c0", NEON[2], s=0.65)
    alien_stem(B, (0.1, 0.2, -0.1), ((0.9, 1.4, -0.9), (1.9, 2.2, -1.2), (2.3, 3.4, -0.9)), 0.36, "2fbfa0", NEON[4],
               s=0.7)
    return B.finish()


def p_rockring(sc, parent):
    B = Build(sc, parent, "FloatingRocks", seed=415)
    rock(B, (0.0, 0.0, 0.0), 2.8, (ROCK[0], ROCK[2], ROCK[1]))
    c = np.array((0.0, 6.3, 0.0))
    Rr = G.ry(20)
    for k in range(8):
        a = 2 * math.pi * k / 8
        s = (2.0, 1.8, 1.9, 1.7, 2.1, 1.8, 1.9, 1.7)[k]
        B.p("Rock", (s, s * 0.84, s * 0.92), c + Rr @ (math.sin(a) * 2.7, math.cos(a) * 2.7, 0.0),
            turn(B.rng, (8, 22), heading=20 + 45 * k), (MOON[0], ROCK[2], MOON[2], ROCK[0])[k % 4])
    B.p("Orb", (1.3, 1.3, 1.3), c, ori(35.26, 45, 0), NEON[3], material="Neon", flicker=0.1, lamp=True)
    B.p("Orb", (0.8, 0.8, 0.8), c, ori(0, 20, 45), "f0e0ff", material="Neon", lamp=True)
    B.p("Pole", (0.16, c[1] - 1.4, 0.16), (0.0, (c[1] + 1.4) / 2, 0.06), None, "1a1e46")
    return B.finish()


def p_starlamp(sc, parent):
    B = Build(sc, parent, "StarLamp", seed=416)
    star8(B, "Base", (0.0, 0.3, 0.0), 2.2, 0.6, (ROCK[3], ROCK[1]))
    B.p("Post", (0.6, 7.0, 0.6), (0.0, 4.2, 0.0), G.ry(10), "4a4664")
    B.p("Post", (1.1, 0.4, 1.1), (0.0, 7.6, 0.0), G.ry(45), GOLD[1])
    star(B, (0.0, 9.0, 0.0), 1.6, NEON[4])
    bar(B, "Post", (0.0, 5.6, 0.0), (1.8, 6.6, 0.0), 0.3, "4a4664")
    star(B, (1.9, 7.3, -0.05), 0.8, NEON[0], R=G.rz(15), d=0.26)
    return B.finish()


def p_moonrocks(sc, parent):
    B = Build(sc, parent, "MoonRocks", seed=417)
    rock(B, (0.0, 0.0, 0.0), 3.0, MOON)
    rock(B, (2.6, 0.0, 0.8), 1.9, (MOON[2], MOON[0], MOON[1]))
    rock(B, (-2.0, 0.0, 1.0), 1.4, (MOON[1], MOON[2], MOON[0]))
    for k, (x, y, z, h, a, col) in enumerate(((0.6, 2.0, -0.6, 2.4, 18, NEON[1]), (-0.5, 1.8, -0.3, 1.7, -24, NEON[3]),
                                              (2.5, 1.2, 0.3, 1.5, 30, NEON[1]))):
        B.p("Crystal", (0.55, h, 0.55), (x, y, z), ori(a * 0.4, 45 + 20 * k, a), col, material="Neon", flicker=0.1,
            lamp=True)
    return B.finish()


def p_statue(sc, parent):
    B = Build(sc, parent, "AlienStatue", seed=418)
    star8(B, "Plinth", (0.0, 0.9, 0.0), 3.6, 1.8, (ROCK[1], ROCK[0]))
    B.p("Plinth", (3.9, 0.4, 3.9), (0.0, 2.0, 0.0), G.ry(22.5), ROCK[2])
    B.plate("Plinth", (1.8, 0.6, 0.1), (0.0, 1.0, -1.82), col=GOLD[0])
    s = 3.6
    c = np.array((0.0, 2.2 + s / 2, 0.0))
    potato(B, c, s, ALIEN, name="Alien", glow=0.1, eyes="b6ff4a", eye_mat="Neon", cheeks="3f9a2a")
    for sx in (-1, 1):
        a = c + (sx * 0.6, s * 0.48, 0.0)
        b = a + (sx * 0.7, 1.6, 0.0)
        bar(B, "Alien", a, b, 0.24, ALIEN[1])
        B.p("Alien", (0.5, 0.5, 0.5), b + (sx * 0.05, 0.2, 0), ori(35.26, 45, 0), NEON[0], material="Neon", flicker=0.1,
            lamp=True)
    bar(B, "Alien", c + (s * 0.4, 0.0, 0.0), c + (s * 0.62, s * 0.55, -0.3), 0.7, ALIEN[1])
    bar(B, "Alien", c + (-s * 0.4, 0.0, 0.0), c + (-s * 0.56, -s * 0.3, -0.25), 0.7, ALIEN[1])
    return B.finish()


def p_flag(sc, parent):
    B = Build(sc, parent, "SpaceFlag", seed=419)
    star8(B, "Mound", (0.0, 0.25, 0.0), 2.4, 0.5, (MOON[2], MOON[0]))
    potato_flag(B, (0.0, 0.4, 0.0), h=6.6, heading=-15, cloth="e8303a")
    for k, (x, z) in enumerate(((-1.6, -1.8), (-0.9, -3.0), (-1.8, -4.1), (-1.0, -5.3))):
        B.plate("Print", (0.6, 0.1, 0.95), (x, 0.05, z), G.ry(-10 + 8 * k), col=FLOOR[1])
    return B.finish()


def p_rover(sc, parent):
    B = Build(sc, parent, "Rover", seed=420)
    B.p("Rover", (3.8, 1.2, 2.4), (0.0, 1.9, 0.0), None, HULL[0])
    B.p("Rover", (3.6, 0.6, 2.2), (0.1, 2.8, 0.0), None, GOLD[0])
    B.p("Panel", (4.4, 0.16, 3.0), (0.0, 3.2, 0.2), G.rz(-4), "3b6bd8")
    B.p("Panel", (0.14, 0.2, 3.04), (0.0, 3.23, 0.2), G.rz(-4), STEEL[2])
    for x in (-1.5, 0.0, 1.5):
        for sz in (-1, 1):
            B.p("Wheel", (0.6, 1.3, 1.3), (x, 0.65, sz * 1.55), G.ry(90), DARK[1], shape="Cylinder")
    for sz in (-1, 1):
        bar(B, "Rover", (-1.5, 0.75, sz * 1.25), (0.0, 1.6, sz * 1.25), 0.3, STEEL[1])
        bar(B, "Rover", (0.0, 1.6, sz * 1.25), (1.5, 0.75, sz * 1.25), 0.34, STEEL[1], t=0.34)
    bar(B, "Mast", (-1.2, 3.0, -0.6), (-1.2, 5.0, -0.6), 0.3, STEEL[0])
    head = np.array((-1.2, 5.4, -0.6))
    B.p("Head", (1.4, 0.8, 0.9), head, G.ry(-20), HULL[1])
    for sx in (-1, 1):
        B.p("Eye", (0.36, 0.36, 0.12), head + G.ry(-20) @ (sx * 0.34, 0.0, -0.5), G.ry(-20), JET[0], material="Neon",
            lamp=True)
    bar(B, "Aerial", (1.4, 3.2, 0.8), (1.6, 5.0, 0.9), 0.14, STEEL[2])
    B.p("Aerial", (0.4, 0.4, 0.4), (1.62, 5.2, 0.9), ori(35.26, 45, 0), "ff3b5c", material="Neon", flicker=0.5,
        lamp=True)
    return B.finish()


AREA = register(Area("Cosmic", "Cosmic Garden", hero, [
    (p_planet, prop_attrs(5, 0.85, 1.25, "Side", False)),
    (p_crater, prop_attrs(6, 0.8, 1.4, "Any", False)),
    (p_dish, prop_attrs(3, 0.9, 1.2, "Edge", True)),
    (p_plants, prop_attrs(10, 0.8, 1.3, "Any", False)),
    (p_rockring, prop_attrs(4, 0.9, 1.2, "Side", True)),
    (p_starlamp, prop_attrs(6, 0.9, 1.15, "Edge", False)),
    (p_moonrocks, prop_attrs(8, 0.8, 1.3, "Any", True)),
    (p_statue, prop_attrs(3, 0.9, 1.2, "Side", True)),
    (p_flag, prop_attrs(3, 0.9, 1.2, "Side", False)),
    (p_rover, prop_attrs(3, 0.9, 1.2, "Side", True)),
], ground="1a1e46"))
