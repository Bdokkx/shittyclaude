"""Toy Town: the hero, a castle of toy building blocks with a toy train, and the area's props.

The castle stands on a green baseplate: a keep of big bricks laid in a running bond in red, blue,
yellow and green, battlements on top, a gate with a yellow arch and a drawbridge, windows, a giant
wind-up key in its side that turns (Spin), a staircase of blocks up to the battlements, and two
round towers of stacked blocks with cone roofs and flags. Two potato toy soldiers guard the gate.
In front a toy train waits on its track: an engine with a smiling face and two wagons carrying
blocks. A spinning top and alphabet blocks lie about.
"""
import math

import numpy as np

import spsgeo as G

from .scenery import (Area, Build, INK, bar, ori, potato, prop_attrs, register, round3, shade)

RED, BLUE, YELLOW, GREEN = "e8403a", "3b8bff", "ffd23f", "4fc24a"
ORANGE, PURPLE, WHITE = "ff9f3d", "a46bff", "fff8ee"
TOY = (RED, BLUE, YELLOW, GREEN)
WOOD = ("c8945a", "b88450")
SILVER = "c8ccd4"


def block(B, c, s, col, mark, R=None, name="Block", solid=False):
    """An alphabet block: a cube with a coloured square on its front and top."""
    R = np.eye(3) if R is None else R
    c = np.asarray(c, float)
    return [B.p(name, (s, s, s), c, R, col, solid=solid),
            B.p(name, (s * 0.6, s * 0.6, 0.12), c + R @ (0, 0, -s / 2 - 0.06), R, mark, material="SmoothPlastic",
                shadow=False),
            B.p(name, (s * 0.6, 0.12, s * 0.6), c + R @ (0, s / 2 + 0.06, 0), R, mark, material="SmoothPlastic",
                shadow=False)]


def spinning_top(B, base, s=1.0, spin=None, name="Top"):
    """A spinning top on its point; every part is centred on its axis, so Spin turns it whole."""
    base = np.asarray(base, float)
    out = []
    y = 0.0
    for k, (w, h, col) in enumerate(((0.5, 0.7, INK), (1.6, 0.9, RED), (2.8, 0.8, YELLOW), (2.2, 0.7, BLUE),
                                     (0.5, 1.2, WHITE))):
        out.append(B.p(name, (w * s, h * s, w * s), base + (0, (y + h / 2) * s, 0), G.ry(45 * (k % 2)), col,
                       spin=spin))
        y += h - 0.02
    return out


def soldier(B, c, s=3.2, name="Soldier"):
    """A potato toy soldier: red coat, white cross-belt, a tall black bearskin, a rifle on its shoulder."""
    c = np.asarray(c, float)
    body = c + (0, s / 2, 0)
    out = potato(B, body, s, ("e8c490", "d9b07a", "f2d4a0"), name=name, glints=True, cheeks="ff9aa8")
    out.append(B.p(name, (s * 0.9, s * 0.42, s * 0.82), body + (0, -s * 0.3, 0), None, RED))
    out.append(B.p(name, (s * 0.14, s * 0.44, 0.12), body + (0, -s * 0.3, -s * 0.42), G.rz(35), WHITE,
                   material="SmoothPlastic", shadow=False))
    out.append(B.p(name, (s * 0.7, s * 0.9, s * 0.66), body + (0, s * 0.85, 0.05), None, INK))
    out.append(B.p(name, (s * 0.16, s * 0.16, 0.1), body + (0, s * 0.62, -s * 0.34), None, YELLOW,
                   material="SmoothPlastic", shadow=False))
    out.append(bar(B, name, body + (s * 0.5, -s * 0.5, -0.1), body + (s * 0.55, s * 0.75, -0.1), 0.3, "6b4226"))
    return out


def engine(B, c, name="Engine"):
    """A toy steam engine facing -X: chassis, a round boiler with a smiling face, a cab, a chimney,
    a cowcatcher and four wheels."""
    c = np.asarray(c, float)
    out = [B.p(name, (7.0, 0.8, 3.0), c + (0, 1.3, 0), None, RED)]
    out.append(B.p(name, (4.4, 2.5, 2.5), c + (-1.1, 3.0, 0), None, BLUE))
    out.append(B.p(name, (4.36, 2.5, 2.5), c + (-1.1, 3.0, 0), G.rx(45), shade(BLUE, -0.12)))
    out.append(B.p(name, (2.6, 3.4, 3.0), c + (2.2, 3.4, 0), None, RED))
    out.append(B.p(name, (3.2, 0.5, 3.6), c + (2.2, 5.35, 0), None, YELLOW))
    out.append(B.p(name, (1.2, 1.2, 0.12), c + (2.2, 3.9, -1.56), None, "a8e0ff", material="SmoothPlastic",
                   shadow=False))
    out.append(B.p(name, (0.9, 1.6, 0.9), c + (-2.3, 4.9, 0), None, INK))
    out.append(B.p(name, (1.3, 0.5, 1.3), c + (-2.3, 5.85, 0), G.ry(45), RED))
    out.append(B.p(name, (1.6, 1.6, 2.6), c + (-3.9, 1.2, 0), G.rz(45), YELLOW))
    zf = c[0] - 3.32
    for sz in (-1, 1):
        out.append(B.p(name, (0.12, 0.42, 0.32), (zf, c[1] + 3.3, c[2] + sz * 0.5), None, INK,
                       material="SmoothPlastic", shadow=False))
    out.append(B.p(name, (0.12, 0.2, 0.9), (zf, c[1] + 2.5, c[2]), None, INK, material="SmoothPlastic", shadow=False))
    for x in (-2.0, 2.0):
        for sz in (-1, 1):
            out.append(B.p(name, (0.5, 1.9, 1.9), c + (x, 0.95, sz * 1.65), G.ry(90), INK, shape="Cylinder"))
    return out


def wagon(B, c, cargo, name="Wagon"):
    c = np.asarray(c, float)
    out = [B.p(name, (5.0, 1.4, 3.0), c + (0, 1.7, 0), None, cargo[0])]
    out.append(B.p(name, (4.6, 0.3, 2.6), c + (0, 2.55, 0), None, shade(cargo[0], -0.15)))
    for k, (dx, col) in enumerate(((-1.2, cargo[1]), (1.2, cargo[2]))):
        out += block(B, c + (dx, 3.6 + 0.04 * k, 0), 1.9, col, WHITE, R=G.ry(10 * (-1) ** k), name="Cargo")
    for x in (-1.6, 1.6):
        for sz in (-1, 1):
            out.append(B.p(name, (0.45, 1.5, 1.5), c + (x, 0.85, sz * 1.6), G.ry(90), INK, shape="Cylinder"))
    return out


# ==================================================================== the hero

def hero(sc, parent):
    B = Build(sc, parent, "Toy", seed=91)
    B.p("Baseplate", (40.0, 0.6, 18.0), (2.0, 0.3, 6.0), None, GREEN, solid=True)
    y0 = 0.6
    cx, cz = 2.0, 7.0
    # the keep: four rows of big bricks in a running bond
    rows = ((4.0, 4.0, 4.0, 4.0), (2.0, 4.0, 4.0, 4.0, 2.0), (4.0, 4.0, 4.0, 4.0), (2.0, 4.0, 4.0, 4.0, 2.0))
    k = 0
    for r, widths in enumerate(rows):
        x = cx - 8.0
        for w in widths:
            B.p("Brick", (w, 3.5, 11.0 - 0.04 * (r % 2)), (x + w / 2, y0 + 3.5 * r + 1.75, cz), None, TOY[k % 4],
                solid=True)
            x += w
            k += 1
        k += 1
    top = y0 + 14.0
    for j in range(5):                                                         # battlements
        B.p("Battlement", (2.0, 1.8, 1.6), (cx - 7.0 + 3.5 * j, top + 0.9, cz - 4.7), None, TOY[(j + 1) % 4],
            solid=True)
    for sx in (-1, 1):
        B.p("Battlement", (1.6, 1.8, 2.0), (cx + sx * 7.2, top + 0.9, cz - 0.5), None, TOY[(sx + 2) % 4], solid=True)
    # the gate: a dark opening under a yellow arch, a drawbridge down to the baseplate
    zf = cz - 5.5
    B.plate("Gate", (4.4, 6.0, 0.12), (cx, y0 + 3.0, zf - 0.06), col="2a2030")
    B.p("Gate", (3.3, 3.3, 1.0), (cx, y0 + 6.2, zf - 0.3), G.rz(45), YELLOW)
    B.p("Gate", (5.4, 0.9, 1.3), (cx, y0 + 7.0, zf - 0.4), None, ORANGE)
    bar(B, "Drawbridge", (cx, y0 + 0.1, zf - 0.2), (cx, 0.15, zf - 5.2), 4.2, WOOD[0], t=0.4, n=(0, 1, 0), solid=True)
    for sx in (-1, 1):
        bar(B, "Drawbridge", (cx + sx * 2.3, y0 + 6.6, zf - 0.3), (cx + sx * 2.1, 0.5, zf - 5.0), 0.16, INK)
    # windows
    for x, y in ((-5.0, 10.0), (5.0, 10.0), (-5.0, 3.6), (5.0, 3.6)):
        B.p("Window", (2.4, 2.4, 0.16), (cx + x, y0 + y, zf - 0.08), None, WHITE)
        B.p("Window", (1.8, 1.8, 0.12), (cx + x, y0 + y, zf - 0.18), None, "a8e0ff", material="SmoothPlastic",
            shadow=False)
    # the wind-up key in the keep's side: every part centred on the axle, its own Y along it
    axle = np.array((cx - 8.0 - 1.4, y0 + 8.0, cz + 3.6))
    Rk = G.rz(90)
    B.p("Key", (0.9, 2.8, 0.9), axle, Rk, "c8a040", spin=40.0)
    B.p("Key", (1.6, 0.6, 1.6), axle + (-1.0, 0, 0), Rk @ G.ry(45), "b8902a", spin=40.0)
    B.p("Key", (5.2, 0.7, 2.2), axle + (-1.6, 0, 0), Rk, "e0b84a", spin=40.0)
    # the towers: stacked blocks turning 45 each, cone roofs, flags
    for sx, flag in ((-1, RED), (1, BLUE)):
        tx, tz = cx + sx * 10.6, cz - 2.0
        y = y0 - 0.3
        for j in range(5):
            h = 4.0
            B.p("Tower", (5.4, h - 0.02 * (j % 2), 5.4), (tx, y + h / 2, tz), G.ry(45 * (j % 2)),
                TOY[(j + (sx > 0) * 2) % 4], solid=True)
            y += h
        for j, (w, h) in enumerate(((6.4, 1.6), (4.6, 1.8), (3.0, 1.8), (1.4, 1.6))):
            B.p("Roof", (w, h, w), (tx, y + h / 2, tz), G.ry(45 * ((j + 1) % 2)), (RED, BLUE)[(j + (sx > 0)) % 2])
            y += h - 0.05
        bar(B, "Flag", (tx, y - 0.1, tz), (tx, y + 3.2, tz), 0.22, INK)
        B.p("Flag", (2.4, 1.5, 0.14), (tx + sx * 1.3, y + 2.4, tz), None, flag)
    # a staircase of blocks up the right side to the battlements
    for j in range(4):
        h = 3.5 * (j + 1)
        B.p("Stair", (3.0, h, 3.0), (cx + 19.0 - 3.0 * j, y0 + h / 2, cz + 3.5), None, TOY[(j + 2) % 4], solid=True)
    # two potato toy soldiers at the gate
    for sx in (-1, 1):
        soldier(B, (cx + sx * 4.0, y0, zf - 2.0))
    # the train on its track in front
    tz = -11.0
    for sz in (-1, 1):
        B.p("Rail", (38.0, 0.3, 0.4), (0.0, 0.15, tz + sz * 1.6), None, SILVER)
    for j in range(7):
        B.p("Sleeper", (1.0, 0.2 + 0.02 * (j % 2), 4.4), (-16.0 + 5.3 * j, 0.1, tz), None, WOOD[1])
    engine(B, (-10.5, 0.0, tz))
    wagon(B, (-3.0, 0.0, tz), (YELLOW, RED, BLUE))
    wagon(B, (3.0, 0.0, tz), (PURPLE, GREEN, ORANGE))
    # a spinning top and alphabet blocks lying about
    spinning_top(B, (16.5, 0.0, -6.0), 1.1, spin=120.0)
    for j, (x, z, s, col, mk) in enumerate(((-17.5, -5.0, 2.6, RED, YELLOW), (-15.0, -6.4, 2.2, BLUE, WHITE),
                                            (-16.2, -5.6, 2.0, YELLOW, RED))):
        y = s / 2 + (2.725 if j == 2 else 0.0)
        block(B, (x, y, z), s, col, mk, R=G.ry(15 * j - 10))
    return B.finish()


# ==================================================================== props

def p_blocks(sc, parent):
    B = Build(sc, parent, "ABCBlocks", seed=101)
    block(B, (-1.3, 1.25, 0.0), 2.5, RED, YELLOW, R=G.ry(8))
    block(B, (1.3, 1.2, 0.2), 2.4, BLUE, WHITE, R=G.ry(-12))
    block(B, (0.0, 3.6, 0.1), 2.3, YELLOW, RED, R=G.ry(30))
    block(B, (2.6, 0.9, -2.4), 1.8, GREEN, WHITE, R=ori(0, 40, 0))
    return B.finish()


def p_tops(sc, parent):
    B = Build(sc, parent, "SpinningTops", seed=102)
    spinning_top(B, (0.0, 0.0, 0.0), 1.2, spin=120.0)
    R = G.rz(70) @ G.ry(20)
    base = np.array((3.2, 1.25, -0.6))
    for k, (w, h, col) in enumerate(((0.45, 0.6, INK), (1.4, 0.8, GREEN), (2.4, 0.7, ORANGE), (1.9, 0.6, PURPLE),
                                     (0.45, 1.0, WHITE))):
        y = sum(v[1] for v in ((0.45, 0.6), (1.4, 0.8), (2.4, 0.7), (1.9, 0.6), (0.45, 1.0))[:k]) + h / 2 - 1.6
        B.p("Top", (w, h, w), base + R @ (0, y, 0), R @ G.ry(45 * (k % 2)), col)
    return B.finish()


def p_soldier(sc, parent):
    B = Build(sc, parent, "ToySoldier", seed=103)
    B.p("Stand", (3.4, 0.5, 3.0), (0.0, 0.25, 0.0), None, GREEN)
    for sx in (-1, 1):
        B.p("Leg", (0.9, 1.6, 0.9), (sx * 0.6, 1.3, 0.0), None, BLUE)
    soldier(B, (0.0, 2.0, 0.0), s=3.4)
    B.p("Drum", (1.4, 1.1, 1.4), (-1.6, 3.0, -0.8), None, WHITE)
    B.p("Drum", (1.5, 0.2, 1.5), (-1.6, 3.6, -0.8), G.ry(45), RED)
    return B.finish()


def p_duck(sc, parent):
    B = Build(sc, parent, "RubberDuck", seed=104)
    B.p("Water", (5.6, 0.2, 4.6), (0.0, 0.1, 0.0), G.ry(10), "7fd8ff", transparency=0.3)
    round3(B, "Duck", (0.0, 1.5, 0.3), 4.4, 2.6, 3.4, (YELLOW, "ffc93c", "ffe066"))
    B.p("Duck", (1.6, 1.4, 1.0), (0.0, 2.6, 2.0), G.rx(-30), "ffc93c")
    B.p("Duck", (2.4, 2.2, 2.2), (0.0, 4.0, -0.9), None, YELLOW)
    B.p("Duck", (2.2, 2.1, 2.36), (0.0, 4.0, -0.9), G.ry(45), "ffe066")
    B.p("Beak", (1.4, 0.5, 1.2), (0.0, 3.8, -2.4), None, ORANGE)
    B.p("Beak", (1.2, 0.3, 1.0), (0.0, 3.4, -2.3), None, "ff8a1a")
    for sx in (-1, 1):
        B.plate("Eye", (0.42, 0.6, 0.1), (sx * 0.62, 4.45, -2.06))
        B.p("Wing", (0.4, 1.2, 2.0), (sx * 2.2, 1.8, 0.4), G.rz(sx * -12), "ffc93c")
    return B.finish()


def p_jack(sc, parent):
    B = Build(sc, parent, "JackInTheBox", seed=105)
    B.p("Box", (3.4, 3.4, 3.4), (0.0, 1.7, 0.0), None, RED)
    for k, col in enumerate((YELLOW, BLUE)):
        B.p("Box", (3.5, 0.5, 3.5), (0.0, 0.8 + 1.8 * k, 0.0), None, col)
    B.p("Box", (3.4, 0.3, 3.4), (-0.4, 4.6, 1.6), G.rx(-75), BLUE)
    bar(B, "Crank", (1.8, 2.2, 0.0), (2.8, 2.2, 0.0), 0.3, SILVER)
    bar(B, "Crank", (2.8, 2.2, 0.0), (2.8, 1.2, 0.0), 0.3, SILVER, t=0.36)
    pts = [np.array(p) for p in ((0.0, 3.4, 0.0), (0.6, 4.2, 0.0), (-0.6, 5.0, 0.0), (0.6, 5.8, 0.0), (0.0, 6.4, 0.0))]
    for k in range(4):
        bar(B, "Spring", pts[k], pts[k + 1], 0.28 + 0.06 * (k % 2), SILVER, t=0.3, over=0.1)
    head = np.array((0.0, 7.6, 0.0))
    potato(B, head, 2.4, ("e8c490", "d9b07a", "f2d4a0"), name="Clown", glints=True, cheeks="ff6a8a")
    B.p("Clown", (0.6, 0.6, 0.6), head + (0, 0.0, -1.05), G.ry(45), RED)
    B.p("Clown", (1.4, 1.2, 1.4), head + (0, 1.6, 0), G.ry(45), PURPLE)
    B.p("Clown", (0.5, 0.5, 0.5), head + (0, 2.4, 0), None, YELLOW)
    return B.finish()


def p_teddy(sc, parent):
    B = Build(sc, parent, "TeddyBear", seed=106)
    fur = ("b8804a", "a87040", "c8905a")
    round3(B, "Teddy", (0.0, 1.8, 0.2), 3.4, 3.2, 3.0, fur)
    B.p("Teddy", (2.2, 2.0, 0.2), (0.0, 1.7, -1.42), None, "e8c49a")
    head = np.array((0.0, 4.6, 0.0))
    B.p("Teddy", (3.0, 2.6, 2.6), head, None, fur[0])
    B.p("Teddy", (2.6, 2.5, 2.9), head, None, fur[2])
    for sx in (-1, 1):
        B.p("Teddy", (1.0, 1.0, 0.7), head + (sx * 1.25, 1.4, 0.2), None, fur[1])
        B.plate("Eye", (0.4, 0.5, 0.1), head + (sx * 0.55, 0.35, -1.5))
        B.p("Teddy", (1.0, 2.2, 1.0), (sx * 1.9, 2.4, -0.2), G.rz(sx * 30), fur[1])
        B.p("Teddy", (1.2, 1.1, 2.0), (sx * 1.0, 0.55, -1.0), None, fur[1])
    B.p("Teddy", (1.2, 0.9, 0.6), head + (0, -0.45, -1.4), None, "e8c49a")
    B.plate("Nose", (0.5, 0.36, 0.1), head + (0, -0.3, -1.75))
    B.p("Bow", (1.6, 0.6, 0.4), head + (0, -1.45, -1.32), None, RED)
    return B.finish()


def p_car(sc, parent):
    B = Build(sc, parent, "ToyCar", seed=107)
    B.p("Car", (6.0, 1.4, 3.2), (0.0, 1.5, 0.0), None, BLUE)
    B.p("Car", (6.2, 0.5, 3.0), (0.0, 0.95, 0.0), None, shade(BLUE, -0.2))
    B.p("Car", (3.2, 1.6, 2.8), (0.5, 2.95, 0.0), None, BLUE)
    B.p("Car", (3.3, 0.3, 2.9), (0.5, 3.9, 0.0), None, WHITE)
    for sz in (-1, 1):
        B.p("Window", (2.4, 1.0, 0.12), (0.5, 3.0, sz * 1.44), None, "a8e0ff", material="SmoothPlastic", shadow=False)
        for x in (-1.9, 1.9):
            B.p("Wheel", (0.55, 1.8, 1.8), (x, 0.9, sz * 1.62), G.ry(90), INK, shape="Cylinder")
    for sz in (-1, 1):
        B.p("Light", (0.14, 0.5, 0.6), (-3.04, 1.6, sz * 1.0), None, YELLOW, material="Neon", lamp=True)
    return B.finish()


def p_crayons(sc, parent):
    B = Build(sc, parent, "Crayons", seed=108)
    for k, (col, x, lean) in enumerate(((RED, -1.6, 10.0), (BLUE, 0.0, -6.0), (GREEN, 1.6, 14.0))):
        R = G.rz(lean) @ G.rx(6 * (-1) ** k)
        base = np.array((x, 0.0, 0.0))
        L = 6.0 - 0.6 * k
        B.p("Crayon", (1.2, L, 1.2), base + R @ (0, L / 2, 0), R, col)
        B.p("Crayon", (1.18, L * 0.6, 1.18), base + R @ (0, L * 0.45, 0), R @ G.ry(45), WHITE)
        B.p("Crayon", (0.8, 0.9, 0.8), base + R @ (0, L + 0.4, 0), R @ G.ry(45), col)
        B.p("Crayon", (0.36, 0.5, 0.36), base + R @ (0, L + 1.0, 0), R, col)
    return B.finish()


AREA = register(Area("Toy", "Toy Town", hero, [
    (p_blocks, prop_attrs(8, 0.8, 1.3, "Any", True)),
    (p_tops, prop_attrs(6, 0.8, 1.3, "Any", False)),
    (p_soldier, prop_attrs(5, 0.9, 1.2, "Side", True)),
    (p_duck, prop_attrs(4, 0.9, 1.3, "Any", True)),
    (p_jack, prop_attrs(4, 0.9, 1.2, "Side", True)),
    (p_teddy, prop_attrs(4, 0.9, 1.2, "Side", True)),
    (p_car, prop_attrs(5, 0.9, 1.2, "Any", True)),
    (p_crayons, prop_attrs(6, 0.85, 1.3, "Side", False)),
], ground="8fd0ff"))
