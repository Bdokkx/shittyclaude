"""Neon City: the hero, a concert stage with speakers and beams of light on a glowing floor grid,
and the area's props.

A raised stage with glowing edges and steps at the sides; behind it a big screen with an
equaliser dancing across it, framed in neon tubes. A truss over the stage carries four spotlights
throwing coloured beams down onto the stage (see-through Neon) and a disco ball that turns. Speaker
stacks either side, a DJ booth with two turning records and the potato DJ in headphones. In front a
dance floor of dark tiles with a grid of glowing lines; two neon palms by the stage, a crowd
barrier, uplights.
"""
import math

import numpy as np

import spsgeo as G

from .scenery import (Area, Build, INK, bar, ori, palm, potato, prop_attrs, register, round3, shade)

DARK = ("1e1a2e", "2a2440", "16131f", "342c4e")
METAL = ("8a90a0", "6a7080", "b0b6c4")
CYAN, MAGENTA, YELLOW, GREEN, PURPLE, ORANGE = "00f0ff", "ff2bd6", "ffe14d", "5eff8a", "a46bff", "ff9f3d"
GLOWS = (CYAN, MAGENTA, YELLOW, GREEN, PURPLE, ORANGE)


def neon(B, name, size, pos, R=None, col=CYAN, flicker=0.1, **kw):
    return B.p(name, size, pos, R, col, material="Neon", flicker=flicker, lamp=True, **kw)


def speaker(B, c, s=1.0, R=None, name="Speaker"):
    """A speaker box facing -Z: a black cabinet, a big woofer cone and a tweeter, a glowing ring."""
    R = np.eye(3) if R is None else R
    c = np.asarray(c, float)
    zf = -1.0 * s - 0.06
    return [B.p(name, (2.6 * s, 2.6 * s, 2.0 * s), c, R, DARK[2]),
            B.p(name, (1.5 * s, 1.5 * s, 0.12), c + R @ (0, -0.3 * s, zf), R @ G.rz(45), METAL[1], material="SmoothPlastic",
                shadow=False),
            B.p(name, (1.1 * s, 1.1 * s, 0.12), c + R @ (0, -0.25 * s, zf - 0.03), R @ G.rz(45), DARK[1],
                material="SmoothPlastic", shadow=False),
            B.p(name, (0.6 * s, 0.6 * s, 0.12), c + R @ (0, 0.85 * s, zf - 0.02), R @ G.rz(45), METAL[2],
                material="SmoothPlastic", shadow=False)]


def neon_palm(B, base, h, cols=(MAGENTA, CYAN), name="NeonPalm", heading=0.0):
    out = palm(B, base, h, 1.4, (DARK[3], DARK[1], DARK[3]), cols, fronds=6, frond_len=5.0, coconuts=0, segs=5,
               heading=heading, name=name)
    for p in out:
        if p.p["color"] in [tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)) for c in cols]:
            p.p["material"] = "Neon"
            p.p["surfaces"] = "smooth"
            p.p.setdefault("attrs", {})["NightLamp"] = True
            p.p["attrs"]["Flicker"] = 0.06
    return out


def spotlight(B, at, aim, col, beam=True, name="Spotlight"):
    """A spotlight can hanging at `at`, pointing at `aim`; a see-through glowing beam down to it."""
    at, aim = np.asarray(at, float), np.asarray(aim, float)
    d = (aim - at) / np.linalg.norm(aim - at)
    out = [bar(B, name, at - d * 0.6, at + d * 0.9, 1.1, DARK[2], t=1.1)]
    out.append(B.p(name, (0.9, 0.12, 0.9), at + d * 0.96, None if abs(d[1]) > 0.99 else _flat(d), col,
                   material="Neon", flicker=0.1, lamp=True))
    if beam:
        out.append(bar(B, "Beam", at + d * 1.1, aim, 1.5, col, t=1.5, material="Neon", transparency=0.65,
                       flicker=0.15, lamp=True, shadow=False))
    return out


def _flat(d):
    from .scenery import frame
    return frame(d, None)


# ==================================================================== the hero

def hero(sc, parent):
    B = Build(sc, parent, "Neon", seed=131)
    # the stage
    sz0, sz1 = -2.0, 12.0
    B.p("Stage", (32.0, 3.0, sz1 - sz0), (0.0, 1.5, (sz0 + sz1) / 2), None, DARK[1], solid=True)
    neon(B, "Stage", (32.2, 0.3, 0.3), (0.0, 2.8, sz0 - 0.1), col=CYAN)
    neon(B, "Stage", (32.2, 0.3, 0.3), (0.0, 0.45, sz0 - 0.1), col=MAGENTA)
    for sx in (-1, 1):
        for k in range(3):
            h = 1.0 * (k + 1)
            B.p("Step", (2.0, h, 3.0), (sx * (16.0 + 2.0 * (2 - k) + 1.0), h / 2, 3.0), None, DARK[k % 2 + 1],
                solid=True)
    # the screen with its equaliser, framed in neon
    sy0 = 3.0
    B.p("Screen", (18.0, 11.0, 1.0), (0.0, sy0 + 6.0, 10.6), None, DARK[2], solid=True)
    neon(B, "Screen", (16.4, 9.4, 0.12), (0.0, sy0 + 6.0, 10.04), col="1a2a6e", flicker=None)
    for k, h in enumerate((3.0, 6.2, 4.4, 7.6, 5.2, 2.6, 6.8)):
        x = -6.0 + 2.0 * k
        neon(B, "Equaliser", (1.3, h, 0.12), (x, sy0 + 1.6 + h / 2, 9.92), col=GLOWS[k % 6], flicker=0.25)
    for sx in (-1, 1):
        neon(B, "Tube", (0.4, 11.2, 0.4), (sx * 8.6, sy0 + 6.0, 9.9), col=MAGENTA)
    neon(B, "Tube", (17.8, 0.4, 0.46), (0.0, sy0 + 11.6, 9.9), col=CYAN)
    # the truss over the stage, four spotlights throwing beams, a disco ball
    ty = 22.0
    for sx in (-1, 1):
        for dz in (-0.6, 0.6):
            B.p("Truss", (0.5, ty - 3.0, 0.5), (sx * 14.0, 3.0 + (ty - 3.0) / 2, 4.0 + dz), None, METAL[0])
        for k in range(5):
            y = 5.0 + 3.6 * k
            B.p("Truss", (0.24, 1.6, 0.24), (sx * 14.0, y, 4.0), G.rx(48 * (-1) ** k), METAL[1])
    for dy in (-0.5, 0.5):
        B.p("Truss", (28.6, 0.5, 0.5 + 0.04 * (dy > 0)), (0.0, ty + dy, 4.0), None, METAL[0])
    for k, (x, col) in enumerate(((-9.0, CYAN), (-3.0, MAGENTA), (3.0, YELLOW), (9.0, GREEN))):
        spotlight(B, (x, ty - 1.2, 4.0), (x * 0.4 + (-1) ** k * 2.0, 3.05, 1.0 + 2.0 * (k % 2)), col)
    bar(B, "Disco", (0.0, ty - 0.75, 4.0), (0.0, ty - 3.0, 4.0), 0.12, INK)
    round3(B, "Disco", (0.0, ty - 4.2, 4.0), 2.4, 2.4, 2.4, (METAL[2], METAL[0], "e0e6f0"), spin=40.0)
    # speaker stacks either side
    for sx in (-1, 1):
        for k in range(3):
            speaker(B, (sx * 12.0, 3.0 + 1.3 + 2.6 * k, 6.0), 1.0 if k < 2 else 0.85)
        speaker(B, (sx * 19.5, 1.3, -4.0), 1.0, R=G.ry(-sx * 18))
    # the DJ booth: a desk, two turning records, the potato DJ in headphones
    B.p("Booth", (7.0, 3.0, 2.6), (0.0, 4.5, 4.0), None, DARK[3])
    neon(B, "Booth", (7.1, 0.3, 0.12), (0.0, 4.2, 2.66), col=MAGENTA)
    B.p("Booth", (7.4, 0.3, 2.9), (0.0, 6.15, 4.0), None, DARK[2])
    for sx in (-1, 1):
        B.p("Record", (2.0, 0.14, 2.0), (sx * 2.0, 6.37, 4.0), None, INK, spin=90.0)
        B.p("Record", (1.98, 0.17, 1.98), (sx * 2.0, 6.37, 4.0), G.ry(45), DARK[1], spin=90.0)
        B.p("Record", (0.7, 0.22, 0.7), (sx * 2.0, 6.39, 4.0), None, (CYAN, MAGENTA)[sx > 0], spin=90.0)
    s = 3.6
    dj = np.array((0.0, 6.36 + s / 2, 5.8))
    potato(B, dj, s, ("d9b07a", "c49a64", "e8c490"), name="DJ", glints=True, cheeks="ff9aa8")
    B.p("Headphones", (s * 0.98, 0.3, 0.6), dj + (0, s * 0.5, 0), None, INK)
    for sx in (-1, 1):
        B.p("Headphones", (0.5, 1.2, 1.2), dj + (sx * s * 0.47, s * 0.12, 0), None, MAGENTA)
    B.p("Glasses", (s * 0.66, 0.4, 0.12), dj + (0, s * 0.12, -s * 0.4 - 0.08), None, CYAN, material="Neon", lamp=True)
    # the dance floor: dark tiles, a grid of glowing lines
    fz0, fz1 = -13.3, -2.4
    B.p("Floor", (26.0, 0.3, fz1 - fz0), (0.0, 0.15, (fz0 + fz1) / 2), None, DARK[0], solid=True)
    for k in range(7):
        x = -12.0 + 4.0 * k
        neon(B, "Grid", (0.2, 0.12, fz1 - fz0 - 0.2), (x, 0.36, (fz0 + fz1) / 2), col=CYAN, flicker=None)
    for k in range(4):
        z = fz0 + 0.8 + 3.2 * k
        neon(B, "Grid", (25.6, 0.14, 0.2), (0.0, 0.38, z), col=MAGENTA, flicker=None)
    # neon palms by the stage, a crowd barrier, uplights
    neon_palm(B, (-16.6, 3.0, 8.6), 11.0, heading=120.0)
    neon_palm(B, (16.6, 3.0, 8.6), 10.0, cols=(CYAN, PURPLE), heading=-120.0)
    for sx in (-1, 1):
        B.p("Barrier", (10.0, 1.6, 0.4), (sx * 7.0, 1.1, -13.9), None, METAL[0])
        for dx in (-4.4, 0.0, 4.4):
            B.p("Barrier", (0.4, 2.0, 1.4), (sx * 7.0 + dx, 1.0, -13.9), None, METAL[1])
    for k, (x, col) in enumerate(((-14.5, YELLOW), (14.5, GREEN))):
        B.p("Uplight", (1.4, 1.0, 1.4), (x, 0.5, -1.0), None, DARK[2])
        neon(B, "Uplight", (1.0, 0.12, 1.0), (x, 1.06, -1.0), col=col)
    return B.finish()


# ==================================================================== props

def p_sign(sc, parent):
    B = Build(sc, parent, "NeonSign", seed=141)
    for sx in (-1, 1):
        B.p("Post", (0.6, 9.0, 0.6), (sx * 3.6, 4.5, 0.3), None, METAL[1])
    B.p("Board", (8.4, 5.2, 0.5), (0.0, 6.8, 0.3), None, DARK[2])
    pts = ((-1.6, 5.2), (-2.2, 6.6), (-1.4, 8.3), (0.4, 8.8), (1.9, 7.8), (2.2, 6.1), (1.2, 4.8))
    for k in range(len(pts)):
        a = np.array((pts[k][0], pts[k][1], -0.1))
        b = np.array((pts[(k + 1) % len(pts)][0], pts[(k + 1) % len(pts)][1], -0.1))
        bar(B, "Tube", a, b, 0.3, YELLOW if k % 2 else ORANGE, t=0.2 + 0.03 * k, over=0.12, n=(0, 0, -1),
            material="Neon", flicker=0.1, lamp=True)
    neon(B, "Tube", (8.6, 0.3, 0.2), (0.0, 9.5, 0.1), col=MAGENTA)
    for sx in (-1, 1):
        neon(B, "Tube", (0.36, 0.6, 0.12), (sx * 0.65, 7.3, -0.12), col=CYAN)
    neon(B, "Tube", (1.2, 0.26, 0.12), (0.0, 6.2, -0.12), col=CYAN)
    return B.finish()


def p_lamp(sc, parent):
    B = Build(sc, parent, "CyberLamp", seed=142)
    B.p("Lamp", (1.6, 0.5, 1.6), (0.0, 0.25, 0.0), G.ry(45), DARK[2])
    B.p("Lamp", (0.5, 10.0, 0.5), (0.0, 5.3, 0.0), None, METAL[1])
    bar(B, "Lamp", (0.0, 10.0, 0.0), (2.6, 11.0, 0.0), 0.4, METAL[1])
    B.p("Lamp", (3.0, 0.5, 1.0), (2.8, 10.9, 0.0), G.rz(18), DARK[1])
    neon(B, "Lamp", (2.8, 0.14, 0.7), (2.8, 10.62, 0.0), G.rz(18), col=CYAN)
    neon(B, "Lamp", (0.14, 6.0, 0.14), (0.0, 5.0, -0.3), col=MAGENTA)
    neon(B, "Lamp", (1.0, 0.14, 1.0), (0.0, 0.56, 0.0), G.ry(45), col=CYAN)
    B.p("Lamp", (0.8, 0.4, 0.8), (0.0, 10.2, 0.0), None, METAL[2])
    B.p("Lamp", (1.0, 1.2, 0.3), (0.0, 3.0, 0.4), None, DARK[3])
    neon(B, "Lamp", (0.7, 0.9, 0.12), (0.0, 3.0, 0.2), col=GREEN)
    return B.finish()


def p_speakers(sc, parent):
    B = Build(sc, parent, "SpeakerStack", seed=143)
    speaker(B, (-1.4, 1.3, 0.0), 1.0)
    speaker(B, (1.4, 1.3, 0.1), 1.0, R=G.ry(-8))
    speaker(B, (0.0, 3.9, 0.0), 1.0, R=G.ry(6))
    return B.finish()


def p_arcade(sc, parent):
    B = Build(sc, parent, "ArcadeMachine", seed=144)
    B.p("Cabinet", (3.0, 6.4, 2.6), (0.0, 3.2, 0.2), None, PURPLE)
    B.p("Cabinet", (3.2, 1.2, 1.2), (0.0, 3.0, -1.4), G.rx(-20), DARK[1])
    neon(B, "Screen", (2.3, 1.8, 0.12), (0.0, 4.6, -1.17), G.rx(-12), col="2a6aff", flicker=0.12)
    neon(B, "Screen", (0.5, 0.5, 0.1), (-0.4, 4.7, -1.25), G.rx(-12), col=YELLOW, flicker=None)
    neon(B, "Marquee", (2.8, 0.9, 0.12), (0.0, 6.0, -1.13), col=MAGENTA)
    for k, (x, col) in enumerate(((-0.8, "e8403a"), (0.3, YELLOW), (0.9, GREEN))):
        B.p("Button", (0.36, 0.2, 0.36), (x, 3.42, -1.55 + 0.02 * k), G.rx(-20), col)
    B.p("Stick", (0.16, 0.6, 0.16), (-0.8, 3.75, -1.62), G.rx(-20), INK)
    B.p("Cabinet", (3.1, 0.3, 2.7), (0.0, 6.55, 0.2), None, DARK[2])
    B.p("Cabinet", (2.2, 1.0, 0.12), (0.0, 1.0, -1.16), None, DARK[3])
    neon(B, "Coin", (0.3, 0.5, 0.1), (0.0, 1.1, -1.24), col=ORANGE)
    return B.finish()


def p_vending(sc, parent):
    B = Build(sc, parent, "VendingMachine", seed=145)
    B.p("Machine", (3.6, 7.0, 2.6), (0.0, 3.5, 0.0), None, "e8403a")
    neon(B, "Window", (2.4, 4.6, 0.12), (-0.4, 4.0, -1.36), col="b8f4ff", flicker=None)
    for r in range(3):
        for c in range(3):
            B.p("Can", (0.5, 0.9, 0.12), (-1.1 + 0.7 * c, 2.6 + 1.4 * r, -1.46),
                None, GLOWS[(r * 3 + c) % 6], material="SmoothPlastic", shadow=False)
    neon(B, "Panel", (0.6, 2.0, 0.12), (1.3, 4.6, -1.36), col=YELLOW)
    B.p("Machine", (2.6, 0.8, 0.3), (-0.4, 1.0, -1.4), None, DARK[2])
    neon(B, "Machine", (3.7, 0.4, 0.2), (0.0, 7.1, -1.25), col=MAGENTA)
    return B.finish()


def p_palm(sc, parent):
    B = Build(sc, parent, "NeonPalm", seed=146)
    B.p("Pot", (2.6, 1.2, 2.6), (0.0, 0.6, 0.0), G.ry(45), DARK[1])
    neon(B, "Pot", (2.7, 0.2, 2.7), (0.0, 1.0, 0.0), G.ry(45), col=CYAN)
    neon_palm(B, (0.0, 1.2, 0.0), 11.0, heading=30.0)
    return B.finish()


def p_holo(sc, parent):
    B = Build(sc, parent, "Hologram", seed=147)
    B.p("Base", (3.4, 0.8, 3.4), (0.0, 0.4, 0.0), G.ry(45), DARK[2])
    B.p("Base", (3.2, 0.7, 3.2), (0.0, 0.42, 0.0), None, METAL[1])
    neon(B, "Base", (2.4, 0.12, 2.4), (0.0, 0.86, 0.0), G.ry(45), col=CYAN)
    neon(B, "Base", (3.6, 0.2, 0.3), (0.0, 0.5, -1.72), col=MAGENTA)
    for k, (w, y) in enumerate(((2.6, 2.4), (3.0, 3.6), (2.4, 4.8))):
        B.p("Holo", (w, 1.2, w * 0.9), (0.0, y, 0.0), G.ry(20 * k), CYAN, material="Neon", transparency=0.55,
            spin=30.0, lamp=True, shadow=False)
    for sx in (-1, 1):
        B.p("Holo", (0.36, 0.6, 0.36), (sx * 0.55, 4.0, 0.0), None, "e0ffff", material="Neon", transparency=0.3,
            lamp=True, shadow=False)
    B.p("Holo", (1.0, 0.24, 0.3), (0.0, 3.2, -0.0), None, "e0ffff", material="Neon", transparency=0.3, lamp=True,
        shadow=False)
    return B.finish()


def p_bike(sc, parent):
    B = Build(sc, parent, "HoverBike", seed=148)
    c = np.array((0.0, 2.2, 0.0))
    B.p("Bike", (6.0, 1.2, 1.6), c, None, DARK[3])
    B.p("Bike", (3.0, 1.0, 1.4), c + (-1.6, 0.8, 0), G.rz(-12), MAGENTA)
    B.p("Bike", (2.2, 0.6, 1.2), c + (1.0, 0.9, 0), None, DARK[2])
    B.p("Bike", (0.3, 1.6, 0.3), c + (-2.6, 1.5, 0), G.rz(20), METAL[1])
    B.p("Bike", (0.3, 0.3, 2.2), c + (-2.85, 2.25, 0), None, METAL[2])
    neon(B, "Glow", (5.0, 0.14, 1.2), c + (0, -0.66, 0), col=CYAN)
    neon(B, "Glow", (0.6, 0.6, 0.12), c + (-3.0, 0.2, -0.75), col=YELLOW)
    neon(B, "Glow", (0.5, 0.4, 1.0), c + (3.04, 0.1, 0), col=MAGENTA)
    neon(B, "Glow", (6.1, 0.14, 0.12), c + (0, 0.3, -0.82), col=MAGENTA)
    B.p("Shadow", (4.0, 0.1, 1.6), (0.0, 0.05, 0.0), None, "2a3a6e", transparency=0.4, shadow=False)
    return B.finish()


AREA = register(Area("Neon", "Neon City", hero, [
    (p_sign, prop_attrs(5, 0.9, 1.2, "Edge", True)),
    (p_lamp, prop_attrs(8, 0.95, 1.15, "Side", False)),
    (p_speakers, prop_attrs(4, 0.9, 1.2, "Side", True)),
    (p_arcade, prop_attrs(4, 0.95, 1.15, "Side", True)),
    (p_vending, prop_attrs(4, 0.95, 1.15, "Side", True)),
    (p_palm, prop_attrs(6, 0.85, 1.25, "Side", True)),
    (p_holo, prop_attrs(3, 0.9, 1.2, "Any", False)),
    (p_bike, prop_attrs(4, 0.9, 1.2, "Any", False)),
], ground="2a2a3a"))
