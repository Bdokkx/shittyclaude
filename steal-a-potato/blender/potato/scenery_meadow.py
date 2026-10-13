"""Meadow Patch: the hero, a red-and-white windmill with a potato scarecrow, and the area's props.

The windmill: an eight-sided tower of upright planks in two reds, leaning in as it rises, with white
corner trim, on a stone plinth; a wooden stage round it with a white railing on struts, a door with
a white brace under it and a lantern hanging from it, a lit window above, a small one in the side;
a white eave and a grey cap stepping up to a red finial. Four big sails on its front turn slowly
(Spin): white cloth in a red frame with red rungs, a dark stock down each, a hub boss in the middle.
Every sail part is centred on the axle with its own Y along it, so each turning about its own Y
turns the whole. In front, in its own potato patch, a potato scarecrow: a straw hat with a red
band, a stitched smile, a patched blue shirt with straw at the cuffs, arms out along a crossbar,
a crow on one arm. Hay (a rolled bale, a square one with a pitchfork), sacks of potatoes and a
cream path to the door round it off.
"""
import math

import numpy as np

import spsgeo as G
from spsgeo import CF

from .scenery import (Area, Build, INK, bar, frame, grass, ori, potato, prop_attrs, register, round3, shade, turn)

RED = ("b5452b", "a33d26", "c4573a")
WHITE = ("fff7ec", "f4e8d4", "ffffff")
CLOTH = ("fff6e6", "f6e0b0")
SLATE = ("6e7a96", "7c88a4", "8a96b2", "98a4be", "a6b0c8")
STONE = ("b9b4c8", "a39eb4", "8e89a0")
WOOD = ("6b4226", "9a6238", "c8743a", "a0572b")
HAY = ("e8c25a", "d9ae45", "b98f32", "f0d070")
SOIL = ("6e4a2c", "5a3a22", "7a5434")
SPUD = ("d9b07a", "c49a64", "e8c490")
LEAF = ("55b848", "3f9e3c", "6cc04a")
GRASS = ("5dbb46", "7ad155", "4fa83a")
SACK = ("d8bc86", "c8a670", "e4cc9a", "ecdab0")
TATER = ("d39a50", "c48a40", "dfaa62")
PATH = ("f3e2b6", "c9ae78")
SHIRT = ("3f78d8", "3368c4", "5a8ee8")
ROPE = "8a6a44"
IRON = "4a4f5c"
GLOW = "ffd27a"
SPIN = 20.0
TAN = math.tan(math.radians(22.5))

# the tower: an octagon of apothem A0 at its foot T0 leaning in to A1 at its top T1
XT, ZT = -5.0, 5.0
T0, T1 = 1.2, 21.2
A0, A1 = 6.2, 4.4
LEAN = math.degrees(math.atan2(A0 - A1, T1 - T0))
HUB = np.array((XT, 24.0, ZT - 7.6))
SAIL_L, SAIL_W = 13.0, 3.4


def apo(y):
    return A0 + (A1 - A0) * (y - T0) / (T1 - T0)


def face(th):
    """Outward normal and across direction of the tower face at heading th (0 = the front, -Z)."""
    a = math.radians(th)
    return np.array((math.sin(a), 0.0, -math.cos(a))), np.array((math.cos(a), 0.0, math.sin(a)))


def face_frame(th):
    """A frame on the tower face at heading th: x across, y up the face, -z out of it."""
    n, _ = face(th)
    return CF(np.array((XT, 0.0, ZT)) + n * apo(0.0), G.ry(-th) @ G.rx(LEAN))


def octa(B, name, c, a, h, cols, solid=False, ground=False):
    """An eight-sided slab of apothem a: four bars, each spanning two opposite flats, a hair apart in
    height (on the ground they all stand on it)."""
    c = np.asarray(c, float)
    s = 2 * a * TAN + 0.02
    out = []
    for k in range(4):
        hh = h - 0.04 * k
        p = np.array((c[0], hh / 2, c[2])) if ground else c
        out.append(B.p(name, (2 * a, hh, s), p, G.ry(45.0 * k), cols[k % len(cols)], solid=solid))
    return out


def spud(B, c, s=1.0, col=None, name="Potato", heading=0.0):
    """A loose potato: a long block and a shorter one turned 45 degrees round it."""
    c = np.asarray(c, float)
    col = col or TATER[0]
    R = ori(8, heading, -6)
    return [B.p(name, (1.1 * s, 0.7 * s, 0.75 * s), c, R, col),
            B.p(name, (0.82 * s, 0.62 * s, 0.82 * s), c + R @ (0.0, 0.03 * s, 0.0), R @ G.ry(45), shade(col, 0.1))]


# ==================================================================== the windmill

def planks(B, th, n, w, cols):
    """n upright planks on the face at heading th, leaning in with it; every other one a hair out."""
    nrm, acr = face(th)
    c = np.array((XT, 0.0, ZT))
    out = []
    for j in range(n):
        f = (j + 0.5) / n - 0.5
        lift = 0.05 * (j % 2)
        a, b = [c + nrm * (ap - 0.25 + lift) + acr * f * 2 * ap * TAN + (0.0, y, 0.0) for y, ap in ((T0, A0), (T1, A1))]
        out.append(bar(B, "Wall", a, b, w, cols[j % 2], t=0.5, n=nrm, over=0.12, solid=True))
    return out


def sails(B, hub, angle):
    """Four sails in two pairs, each pair a stack of plates centred on the hub: frame, cloth, rung,
    cloth ... shortest in front, so the cloth shows in panels between red rungs; a stock in front."""
    AX = frame((0.0, 0.0, -1.0))
    ax = np.array((0.0, 0.0, -1.0))
    t, e, s = 0.18, 0.45, 0.36
    L, W = SAIL_L, SAIL_W
    r1, r2, r3 = 4.6, 7.5, 10.4
    layers = ((L, True), (L - e, False), (r3 + e / 2, True), (r3 - e / 2, False), (r2 + e / 2, True),
              (r2 - e / 2, False), (r1 + e / 2, True), (r1 - e / 2, False))
    out = []
    for p in range(2):
        R = AX @ G.ry(angle + 90.0 * p)
        for k, (half, rim) in enumerate(layers):
            d = -0.2 + t / 2 + k * t + p * t / 2
            w = (W + 2 * s if rim else W) - 0.02 * (k // 2)
            col = RED[1] if rim else CLOTH[(k // 2) % 2]
            out.append(B.p("Sail", (2 * half, t, w), hub + ax * d, R, col, spin=SPIN))
        d = -0.2 + 8 * t + 0.15 + p * t / 2
        out.append(B.p("Stock", (2 * L + 0.6, 0.3, 0.62), hub + ax * d, R, WOOD[0], spin=SPIN))
    d = -0.2 + 9 * t + 0.35
    out.append(B.p("Hub", (4.4, 0.5, 4.4), hub + ax * d, AX @ G.ry(angle + 45.0), IRON, spin=SPIN))
    out.append(B.p("Hub", (2.8, 0.4, 2.8), hub + ax * (d + 0.4), AX @ G.ry(angle), RED[2], spin=SPIN))
    out.append(B.p("Hub", (1.2, 0.4, 1.2), hub + ax * (d + 0.75), AX @ G.ry(angle + 45.0), WHITE[0], spin=SPIN))
    return out


def windmill(B):
    c = np.array((XT, 0.0, ZT))
    octa(B, "Plinth", c, 7.2, 1.2, STONE, solid=True, ground=True)
    B.p("Step", (3.4, 0.6, 1.3), (XT, 0.3, ZT - 7.8), None, STONE[1], solid=True)
    # the tower: planks on every face, white trim up the corners we see
    for th in (-90.0, -45.0, 0.0, 45.0, 90.0):
        planks(B, th, 4, 1.34, (RED[0], RED[1]))
    for th in (135.0, -135.0):
        planks(B, th, 2, 2.7, (RED[1], RED[0]))
    planks(B, 180.0, 1, 5.2, (RED[1],))
    k = 1.0 / math.cos(math.radians(22.5))
    for th in (-112.5, -67.5, -22.5, 22.5, 67.5, 112.5):
        n, _ = face(th)
        a, b = [c + n * (ap * k - 0.1) + (0.0, y, 0.0) for y, ap in ((T0, A0), (T1, A1))]
        bar(B, "Trim", a, b, 0.8, WHITE[0], t=0.8, n=n, over=0.3)
    # the stage: a deck on struts, a white railing round the front
    octa(B, "Stage", (XT, 7.15, ZT), 9.0, 0.5, (WOOD[3], WOOD[1]), solid=True)
    posts = {}
    for th in (-112.5, -67.5, -22.5, 22.5, 67.5, 112.5):
        n, _ = face(th)
        posts[th] = c + n * (9.0 * k - 0.45)
        B.p("Railing", (0.45, 2.4, 0.45), posts[th] + (0.0, 8.6, 0.0), G.ry(-th), WHITE[0])
    for j, (a, b) in enumerate(((-112.5, -67.5), (-67.5, -22.5), (-22.5, 22.5), (22.5, 67.5), (67.5, 112.5))):
        for y, w in ((9.55, 0.36), (8.45, 0.28)):
            dy = 0.03 * (j % 2)
            bar(B, "Railing", posts[a] + (0.0, y + dy, 0.0), posts[b] + (0.0, y + dy, 0.0), w, WHITE[0], n=(0, 1, 0))
    for th in (-45.0, 45.0):
        n, _ = face(th)
        bar(B, "Strut", c + n * (apo(3.4) - 0.2) + (0.0, 3.4, 0.0), c + n * 8.3 + (0.0, 6.95, 0.0), 0.5, WOOD[0], n=n)
    # the door and its white brace, the lit window, a small window in the side
    with B.at(face_frame(0.0)):
        B.plate("Door", (2.8, 5.0, 0.12), (0.0, T0 + 2.5, -0.13), col="5a3422")
        for y in (T0 + 0.8, T0 + 4.2):
            B.p("Door", (2.6, 0.32, 0.14), (0.0, y, -0.26), None, WHITE[0])
        bar(B, "Door", (-1.0, T0 + 0.95, -0.27), (1.0, T0 + 4.05, -0.27), 0.3, WHITE[0], t=0.14, n=(0, 0, -1))
        for sx in (-1, 1):
            B.p("Door", (0.5, 5.5, 0.45), (sx * 1.62, T0 + 2.75, -0.2), None, WHITE[1])
        B.p("Door", (4.0, 0.55, 0.55), (0.0, T0 + 5.5, -0.27), None, WHITE[0])
        B.p("Door", (0.35, 0.35, 0.3), (0.95, T0 + 2.5, -0.4), None, "e0a800")
        wy = 13.8
        B.p("Window", (2.7, 3.3, 0.24), (0.0, wy, -0.1), None, WHITE[0])
        B.p("Window", (2.0, 2.6, 0.12), (0.0, wy, -0.26), None, GLOW, material="Neon", lamp=True)
        B.p("Window", (0.24, 2.56, 0.14), (0.0, wy, -0.36), None, WHITE[1])
        B.p("Window", (1.96, 0.24, 0.16), (0.0, wy + 0.1, -0.38), None, WHITE[1])
        B.p("Window", (3.0, 0.7, 0.8), (0.0, wy - 2.0, -0.42), None, WOOD[2])
        for k, (x, col) in enumerate(((-0.9, "e8403a"), (0.05, "ff6b8a"), (0.95, "ffd23f"))):
            B.p("Flower", (0.62, 0.55, 0.62), (x, wy - 1.45 + 0.04 * k, -0.45), G.ry(45), col)
    for th in (-90.0, 90.0):
        with B.at(face_frame(th)):
            B.p("Window", (2.1, 2.5, 0.24), (0.0, 15.5, -0.1), None, WHITE[0])
            B.plate("Window", (1.5, 1.9, 0.12), (0.0, 15.5, -0.26), col="7ec8f0")
    # a lantern hanging from the stage by the door
    lp = np.array((XT + 2.6, 0.0, ZT - 8.1))
    B.p("Lantern", (0.16, 0.9, 0.16), lp + (0.0, 6.45, 0.0), None, INK)
    B.p("Lantern", (0.95, 0.3, 0.95), lp + (0.0, 6.0, 0.0), G.ry(45), INK)
    B.p("Lantern", (0.7, 0.9, 0.7), lp + (0.0, 5.45, 0.0), G.ry(45), GLOW, material="Neon", flicker=0.08, lamp=True)
    # the eave, the stepped cap, a finial
    octa(B, "Eave", (XT, T1 + 0.25, ZT), 5.0, 0.8, (WHITE[0], WHITE[1]))
    octa(B, "Cap", (XT, 22.45, ZT), 5.6, 1.2, (SLATE[0], SLATE[1]))
    y = 23.05
    for k, (s, h) in enumerate(((8.2, 1.2), (6.6, 1.1), (4.8, 1.0), (3.0, 0.9))):
        B.p("Cap", (s, h, s), (XT, y + h / 2, ZT), G.ry(45.0 * ((k + 1) % 2)), SLATE[k + 1])
        y += h - 0.04
    weathervane(B, (XT, y - 0.05, ZT))
    # the windshaft and the sails
    z0, z1 = ZT - 4.6, HUB[2] + 0.2
    B.p("Shaft", (1.0, z0 - z1, 1.0), (XT, HUB[1], (z0 + z1) / 2), frame((0.0, 0.0, -1.0)) @ G.ry(45), WOOD[0],
        spin=SPIN)
    sails(B, HUB, 35.0)


# ==================================================================== the scarecrow

def scarecrow(B):
    """The scarecrow in its potato patch, in its own frame: the pole at the origin, front -Z."""
    rng = B.rng
    B.p("Patch", (9.0, 0.5, 6.6), (0.0, 0.25, 0.0), None, SOIL[1], solid=True)
    for k, z in enumerate((-2.0, 2.0)):
        B.p("Patch", (8.2, 0.45, 1.4), (0.0, 0.7, z), None, (SOIL[2], SOIL[0])[k], solid=True)
    for k, (x, z) in enumerate(((-3.0, -2.0), (3.1, -2.0), (-2.4, 2.1))):
        B.p("Plant", (2.0, 1.3, 1.6), (x, 1.5, z), turn(rng, (5, 12)), LEAF[k % 2])
        B.p("Plant", (1.5, 1.2, 2.0), (x + 0.1, 1.95, z + 0.05), turn(rng, (5, 12)), LEAF[(k + 1) % 2 + 1])
    for k, x in enumerate((-0.9, 1.1)):
        spud(B, (x, 0.95, -2.55), 0.9, TATER[k], heading=30 * k)
    # pole and crossbar, the patched shirt hanging on them
    B.p("Pole", (0.7, 10.8, 0.7), (0.0, 5.75, 0.35), None, WOOD[1])
    B.p("Crossbar", (10.2, 0.6, 0.6), (0.0, 8.68, 0.35), None, WOOD[0])
    B.p("Shirt", (4.0, 4.3, 1.8), (0.0, 7.25, 0.2), None, SHIRT[0])
    B.p("Shirt", (4.5, 1.1, 2.0), (0.0, 8.95, 0.2), None, SHIRT[2])
    B.p("Shirt", (4.1, 0.35, 1.9), (0.0, 5.6, 0.2), None, ROPE)
    B.p("Shirt", (1.2, 1.1, 0.14), (-0.95, 6.6, -0.78), G.rz(-6), "ffd23f")
    B.p("Shirt", (1.0, 1.0, 0.14), (1.0, 7.6, -0.78), G.rz(10), "e8403a")
    for sx in (-1, 1):
        B.p("Shirt", (3.1, 1.5, 1.5), (sx * 3.6, 8.7, 0.3), G.rz(-sx * 4), SHIRT[1])
        cuff = np.array((sx * 5.0, 8.5, 0.3))
        for j, (dy, dz) in enumerate(((0.55, -0.5), (-0.45, 0.4))):
            bar(B, "Straw", cuff, cuff + (sx * 1.3, dy, dz), 0.3, HAY[j % 2])
    for x, dx in ((-0.8, -0.35), (0.9, 0.4)):
        bar(B, "Straw", (x, 5.6, 0.0), (x + dx, 4.3, -0.2), 0.3, HAY[1])
    # the potato head: a stitched smile, straw hair, a straw hat with a red band
    s = 4.4
    hc = np.array((0.0, 11.72, 0.15))
    potato(B, hc, s, SPUD, name="Head", glints=True, cheeks="ff9aa8")
    zf = hc[2] - s * 0.39 - 0.02
    for sx in (-1, 1):
        B.plate("Head", (0.42, 0.26, 0.12), hc + (sx * 0.7, -s * 0.14 + 0.1, 0) + (0, 0, zf - hc[2] - 0.03),
                G.rz(sx * 32))
    for x in (-0.36, 0.0, 0.36):
        B.plate("Head", (0.09, 0.62, 0.1), (x, hc[1] - s * 0.14, zf - 0.06))
    for sx in (-1, 1):
        bar(B, "Straw", hc + (sx * 1.6, 1.0, 0.3), hc + (sx * 2.8, 0.1, -0.1), 0.34, HAY[1])
    Rh = G.rz(-7.0) @ G.rx(-6.0)
    hb = hc + np.array((0.0, s / 2 - 0.05, 0.05))
    B.p("Hat", (6.2, 0.32, 5.8), hb, Rh, HAY[0])
    B.p("Hat", (5.0, 0.3, 5.0), hb + Rh @ (0.0, 0.02, 0.0), Rh @ G.ry(45), HAY[1])
    B.p("Hat", (3.3, 1.9, 3.1), hb + Rh @ (0.0, 1.1, 0.1), Rh, HAY[0])
    B.p("Hat", (3.42, 0.5, 3.22), hb + Rh @ (0.0, 0.42, 0.1), Rh, "e8403a")
    B.p("Hat", (0.7, 0.7, 0.3), hb + Rh @ (0.9, 0.45, -1.62), Rh @ G.rz(45), "ffd23f")
    # a crow perched on its left arm
    cr = np.array((-3.9, 9.85, 0.25))
    Rc = G.ry(15.0)
    B.p("Crow", (0.9, 0.85, 1.5), cr, Rc @ G.rx(-8), "2a2633")
    B.p("Crow", (0.72, 0.7, 0.72), cr + Rc @ (0.0, 0.55, -0.72), Rc, "36313f")
    B.p("Crow", (0.26, 0.22, 0.6), cr + Rc @ (0.0, 0.45, -1.3), Rc, "ffb02e")
    B.p("Crow", (0.7, 0.14, 1.0), cr + Rc @ (0.0, 0.2, 1.0), Rc @ G.rx(-20), "2a2633")


# ==================================================================== hay, sacks

def hay_roll(B, c, dia, length, R=None, name="HayRoll"):
    """A rolled bale on its side: Folk Valley's round, its end to the front with a spiral on it."""
    R = np.eye(3) if R is None else R
    c = np.asarray(c, float)
    Rr = R @ G.rx(90.0)
    out = round3(B, name, c, dia, length, dia, HAY, R=Rr)
    f = c + Rr @ (0.0, -length / 2, 0.0)
    out.append(B.p(name, (dia * 0.56, 0.14, dia * 0.56), f + Rr @ (0.0, -0.06, 0.0), Rr @ G.ry(45), HAY[3]))
    out.append(B.p(name, (dia * 0.28, 0.14, dia * 0.28), f + Rr @ (0.0, -0.12, 0.0), Rr, HAY[2]))
    return out


def hay_bale(B, c, heading=0.0, name="HayBale"):
    R = G.ry(heading)
    c = np.asarray(c, float)
    out = [B.p(name, (4.4, 2.3, 2.9), c + (0.0, 1.15, 0.0), R, HAY[0])]
    for sx in (-1, 1):
        out.append(B.p(name, (0.32, 2.36, 2.96), c + R @ (sx * 1.2, 1.15, 0.0), R, HAY[2]))
    for k, (x, z, a) in enumerate(((-0.6, -0.4, 30), (0.9, 0.5, -40))):
        out.append(B.p(name, (0.2, 0.2, 1.8), c + R @ (x, 2.36 + 0.02 * k, z), R @ G.ry(a), HAY[1]))
    return out


def pitchfork(B, base, top, name="Pitchfork"):
    base, top = np.asarray(base, float), np.asarray(top, float)
    d = (top - base) / np.linalg.norm(top - base)
    out = [bar(B, name, base, top, 0.28, WOOD[1])]
    side = np.cross(d, (0.0, 0.0, -1.0))
    side /= np.linalg.norm(side)
    out.append(bar(B, name, top - side * 0.7, top + side * 0.7, 0.26, "8a8f9c"))
    for j in (-1, 0, 1):
        a = top + side * 0.6 * j
        out.append(bar(B, name, a, a + d * 1.5, 0.16 + 0.02 * (j == 0), "c8ccd4"))
    return out


def sack(B, c, R=None, tied=True, stamp=True, h=2.5, name="Sack"):
    """A burlap sack: a round body (Folk Valley's round), its neck gathered, tied with rope and
    flaring into a tuft (or an open rolled rim), a red potato stamp on its front."""
    R = np.eye(3) if R is None else R
    c = np.asarray(c, float)
    out = round3(B, name, c + R @ (0.0, h / 2, 0.0), 2.1, h, 1.7, SACK, R=R)
    top = c + R @ (0.0, h, 0.0)
    if tied:
        out.append(B.p(name, (0.95, 0.6, 0.8), top + R @ (0.0, 0.18, 0.0), R @ G.ry(10), SACK[1]))
        out.append(B.p(name, (1.1, 0.28, 0.95), top + R @ (0.0, 0.32, 0.0), R @ G.ry(10), WOOD[0]))
        for sx in (-1, 1):
            out.append(B.p(name, (1.0, 0.7, 0.46), top + R @ (sx * 0.32, 0.78, 0.04 * sx), R @ G.ry(10) @ G.rz(-sx * 28),
                           SACK[3 - (sx > 0)]))
    else:
        out.append(B.p(name, (2.0, 0.32, 1.6), top + R @ (0.0, -0.05, 0.0), R @ G.ry(-6), SACK[3]))
    if stamp:
        out.append(B.plate(name, (0.9, 0.7, 0.1), c + R @ (0.0, h * 0.55, -0.91), R @ G.rz(8), col=RED[2]))
    return out


def weathervane(B, base, name="Vane"):
    """A red knob on the cap, a pole, an arrow with a tail and a little potato riding on it."""
    base = np.asarray(base, float)
    out = [B.p(name, (1.0, 0.8, 1.0), base + (0.0, 0.4, 0.0), G.ry(45), RED[2]),
           B.p(name, (0.26, 3.2, 0.26), base + (0.0, 2.2, 0.0), None, INK)]
    a = base + (0.0, 3.2, 0.0)
    R = G.ry(-30.0)
    out.append(B.p(name, (3.4, 0.22, 0.22), a, R, INK))
    out.append(B.p(name, (0.6, 0.6, 0.16), a + R @ (1.8, 0.0, 0.0), R @ G.rz(45), INK))
    out.append(B.p(name, (0.9, 0.9, 0.12), a + R @ (-1.6, 0.25, 0.0), R @ G.rz(45), RED[2]))
    out.append(B.p(name, (1.2, 0.9, 0.3), a + R @ (0.0, 0.5, 0.0), R @ G.rz(10), SPUD[0]))
    return out


# ==================================================================== the hero

def hero(sc, parent):
    B = Build(sc, parent, "Meadow", seed=301)
    windmill(B)
    with B.at(CF(np.array((12.6, 0.0, -6.4)), G.ry(10.0))):
        scarecrow(B)
    # hay on the other side: a rolled bale and a square one with a pitchfork against it
    hay_roll(B, (-19.0, 2.2, -4.2), 4.4, 4.2, G.ry(-24.0))
    hay_bale(B, (-15.6, 0.0, -9.4), heading=12.0)
    pitchfork(B, (-18.6, 0.0, -10.6), (-17.2, 5.4, -9.6))
    # sacks of potatoes by the path: a tied one, an open one heaped with potatoes, two spilled
    sack(B, (-0.2, 0.0, -5.4), G.ry(-14))
    sack(B, (2.0, 0.0, -6.9), G.ry(-30), tied=False, stamp=False)
    for k, (x, y, z) in enumerate(((1.7, 2.55, -7.0), (2.4, 2.6, -6.6), (2.0, 2.9, -6.6), (0.6, 0.36, -8.6),
                                   (3.5, 0.36, -8.4))):
        spud(B, (x, y, z), 0.95, TATER[k % 3], heading=40 * k)
    # a cream path from the door
    for k, (x, z, w, d, a) in enumerate(((XT + 0.2, -3.9, 2.6, 1.9, 6), (XT - 0.3, -6.2, 2.4, 1.8, -8),
                                         (XT + 0.4, -8.4, 2.5, 1.7, 12))):
        B.p("Path", (w, 0.2 + 0.03 * k, d), (x, 0.1 + 0.015 * k, z), G.ry(a), PATH[k % 2])
    return B.finish()


# ==================================================================== props

def p_hayrolls(sc, parent):
    B = Build(sc, parent, "HayRolls", seed=311)
    r = 2.2
    for k, (x, y, z, h) in enumerate(((-2.3, r, 0.2, 8.0), (2.3, r - 0.05, -0.1, -6.0), (0.0, r + 3.78, 0.3, 4.0))):
        hay_roll(B, (x, y, z), 2 * r - 0.1 * (k == 1), 4.2, G.ry(h))
    for k, (x, z, a) in enumerate(((-3.6, -2.8, 30), (1.4, -2.9, -50), (4.4, -2.0, 70))):
        B.p("Straw", (0.24, 0.2 + 0.02 * k, 1.8), (x, 0.1 + 0.01 * k, z), G.ry(a), HAY[k % 3])
    return B.finish()


def p_fence(sc, parent):
    B = Build(sc, parent, "PicketFence", seed=312)
    for k, x in enumerate((-5.6, -1.75, 1.75, 5.6)):
        h = 3.8 if k in (1, 2) else 3.4
        B.p("Post", (0.7, h, 0.7), (x, h / 2, 0.0), None, WHITE[0])
        B.p("Post", (0.95, 0.35, 0.95), (x, h + 0.15, 0.0), None, WHITE[1])
    for sx in (-1, 1):
        for j, y in enumerate((1.0, 2.2)):
            B.p("Rail", (3.3, 0.36, 0.3), (sx * 3.675, y + 0.02 * j, 0.25), None, WHITE[1])
        for j in range(3):
            x = sx * (2.7 + 0.95 * j)
            B.p("Picket", (0.55, 2.7, 0.22), (x, 1.45, -0.05), None, WHITE[j % 2])
            B.p("Picket", (0.4, 0.4, 0.2), (x, 2.8, -0.05), G.rz(45), WHITE[j % 2])
    # the gate, swung a little open
    hinge = np.array((-1.35, 0.0, -0.1))
    Rg = G.ry(28.0)
    for y in (1.0, 2.3):
        B.p("Gate", (2.75, 0.32, 0.26), hinge + Rg @ (1.4, y, 0.0), Rg, WHITE[1])
    for j in range(3):
        x = 0.45 + 0.95 * j
        B.p("Gate", (0.5, 2.6, 0.2), hinge + Rg @ (x, 1.55, -0.23), Rg, WHITE[0])
        B.p("Gate", (0.36, 0.36, 0.18), hinge + Rg @ (x, 2.85, -0.23), Rg @ G.rz(45), WHITE[0])
    bar(B, "Gate", hinge + Rg @ (0.4, 1.05, -0.12), hinge + Rg @ (2.5, 2.25, -0.12), 0.26, WHITE[1], t=0.2,
        n=Rg @ (0, 0, -1))
    B.p("Latch", (0.3, 0.5, 0.2), (1.55, 1.9, -0.45), None, INK)
    for k, (x, col) in enumerate(((-4.2, "ff6b8a"), (4.6, "ffd23f"))):
        B.p("Flower", (0.35, 1.0, 0.35), (x, 0.5, -0.7), G.ry(20 * k), GRASS[0])
        B.p("Flower", (0.7, 0.4, 0.7), (x, 1.1, -0.7), G.ry(45), col)
    return B.finish()


def p_cart(sc, parent):
    B = Build(sc, parent, "PotatoCart", seed=313)
    B.p("Cart", (4.7, 0.4, 2.9), (0.0, 2.3, 0.0), None, WOOD[1])
    for k, sz in enumerate((-1, 1)):
        B.p("Cart", (4.8, 1.3, 0.3), (0.0, 3.1, sz * 1.35), None, WOOD[2 + k])
    for k, sx in enumerate((-1, 1)):
        B.p("Cart", (0.3, 1.3, 2.4), (sx * 2.25, 3.1 + 0.02 * k, 0.0), None, WOOD[3 - k])
    B.p("Cart", (4.2, 0.8, 2.4), (0.0, 3.3, 0.0), None, SPUD[1])
    heap = ((-1.4, 0.0, -0.6), (-0.2, 0.15, -0.7), (1.1, 0.0, -0.5), (-0.8, 0.25, 0.5), (0.5, 0.35, 0.3),
            (1.5, 0.1, 0.6), (-0.1, 0.65, -0.1))
    for k, (x, y, z) in enumerate(heap):
        spud(B, (x, 4.0 + y, z), 1.0, TATER[k % 3], heading=37 * k)
    for sz in (-1, 1):
        B.p("Wheel", (0.5, 3.2, 3.2), (0.5, 1.6, sz * 1.8), G.ry(90), WOOD[0], shape="Cylinder")
        for j in range(2):
            B.p("Wheel", (0.28, 2.9, 0.14), (0.5, 1.6, sz * (2.1 + 0.04 * j)), G.rz(45 + 90 * j), WOOD[2])
        B.p("Wheel", (0.7, 0.7, 0.7), (0.5, 1.6, sz * 2.15), G.rz(45), "8a8f9c")
    B.p("Axle", (0.4, 0.4, 3.7), (0.5, 1.6, 0.0), None, IRON)
    B.p("Leg", (0.4, 2.1, 0.4), (-1.9, 1.05, 0.0), None, WOOD[0])
    for sz in (-1, 1):
        bar(B, "Handle", (-2.2, 2.6, sz * 1.0), (-5.4, 3.0, sz * 0.8), 0.34, WOOD[0])
    B.p("Handle", (0.34, 0.34, 2.0), (-5.3, 3.0, 0.0), None, WOOD[1])
    return B.finish()


def p_beehive(sc, parent):
    B = Build(sc, parent, "Beehive", seed=314)
    B.p("Stand", (1.4, 0.3, 1.4), (0.0, 0.15, 0.0), G.ry(45), WOOD[0])
    B.p("Stand", (0.7, 2.8, 0.7), (0.0, 1.6, 0.0), None, WOOD[1])
    B.p("Stand", (4.8, 0.4, 4.0), (0.4, 3.2, 0.0), None, WOOD[2])
    for sx in (-1, 1):
        bar(B, "Stand", (sx * 0.2, 1.6, 0.0), (sx * 1.6, 3.05, 0.0), 0.3, WOOD[0])
    y = 3.4
    for k, (s, h) in enumerate(((3.7, 0.8), (3.6, 0.8), (3.3, 0.75), (2.8, 0.7), (2.1, 0.65), (1.3, 0.55))):
        B.p("Skep", (s, h, s), (-0.3, y + h / 2, 0.0), G.ry(45.0 * (k % 2)), HAY[k % 3])
        y += h - 0.03
    B.plate("Skep", (0.9, 0.6, 0.1), (-0.3, 3.8, -1.9), col="2a1a10")
    B.p("Skep", (1.4, 0.16, 0.6), (-0.3, 3.48, -2.18), None, WOOD[2])
    B.p("Honey", (0.7, 0.8, 0.7), (2.2, 3.8, -1.3), None, "ffb02e")
    B.p("Honey", (0.8, 0.2, 0.8), (2.2, 4.3, -1.3), G.ry(45), "e8403a")
    for k, (x, y, z, h) in enumerate(((-2.3, 6.8, -1.4, 30.0), (1.9, 5.6, -2.4, -40.0), (0.6, 8.6, -0.8, 160.0))):
        R = G.ry(h)
        c = np.array((x, y, z))
        B.p("Bee", (0.55, 0.5, 0.75), c, R, "ffd23f")
        B.p("Bee", (0.57, 0.52, 0.2), c, R, INK)
        for sx in (-1, 1):
            B.p("Bee", (0.5, 0.08, 0.36), c + R @ (sx * 0.38, 0.32, 0.05), R @ G.rz(sx * 25), "f4f8ff")
    return B.finish()


def p_sunflowers(sc, parent):
    B = Build(sc, parent, "Sunflowers", seed=315)
    for k, (x, z, h, lean, tilt) in enumerate(((-1.5, 0.3, 6.6, -0.6, -14.0), (0.4, -0.2, 8.2, 0.3, -10.0),
                                               (2.0, 0.5, 5.4, 0.7, -18.0))):
        top = np.array((x + lean, h, z))
        bar(B, "Stem", (x, 0.0, z), top, 0.45, GRASS[2])
        for j, (f, sx) in enumerate(((0.35, -1), (0.6, 1))):
            p = np.array((x, 0.0, z)) + (top - np.array((x, 0.0, z))) * f
            B.p("Leaf", (1.6, 0.16, 0.9), p + (sx * 0.8, 0.0, 0.0), G.ry(20 * k) @ G.rz(sx * 22), LEAF[j])
        R = G.ry(-10.0 * (k - 1)) @ G.rx(tilt)
        hc = top + R @ (0.0, 0.0, -0.25)
        B.p("Flower", (2.2, 2.2, 0.3), hc, R, LEAF[1])
        B.p("Petals", (2.8, 2.8, 0.24), hc + R @ (0.0, 0.0, -0.24), R, "ffd23f")
        B.p("Petals", (2.8, 2.8, 0.24), hc + R @ (0.0, 0.0, -0.28), R @ G.rz(45), "ffc21a")
        B.p("Centre", (1.5, 1.5, 0.3), hc + R @ (0.0, 0.0, -0.46), R, "7a4a22")
        B.p("Centre", (0.95, 0.95, 0.3), hc + R @ (0.0, 0.0, -0.58), R @ G.rz(45), "5a3418")
    grass(B, (0.2, 0.0, -0.4), 3, GRASS, h=(1.0, 1.6), r=1.2)
    return B.finish()


def p_signpost(sc, parent):
    B = Build(sc, parent, "Signpost", seed=316)
    B.p("Base", (1.8, 0.5, 1.8), (0.0, 0.25, 0.0), G.ry(45), STONE[1])
    B.p("Post", (0.8, 8.2, 0.8), (0.0, 4.1, 0.0), None, WOOD[1])
    B.p("Post", (1.2, 0.4, 1.2), (0.0, 8.4, 0.0), None, WOOD[0])
    B.p("Post", (0.7, 0.5, 0.7), (0.0, 8.8, 0.0), G.ry(45), RED[2])
    for k, (y, hd, col) in enumerate(((7.0, 15.0, WOOD[2]), (5.7, 160.0, "dc9a52"), (4.4, -25.0, WOOD[3]))):
        R = G.ry(hd)
        c = np.array((0.0, y, 0.0)) + R @ (2.1, 0.0, 0.0)
        B.p("Arrow", (3.4, 0.9, 0.26), c, R, col)
        B.p("Arrow", (0.66, 0.66, 0.24), c + R @ (1.7, 0.0, 0.0), R @ G.rz(45), col)
        for sz in (-1, 1):
            B.plate("Arrow", (2.2, 0.2, 0.1), c + R @ (-0.2, 0.0, sz * 0.17), R, col="fff1d0")
    bc = np.array((0.0, 9.05, 0.0))
    B.p("Bird", (0.7, 0.6, 1.0), bc + (0.0, 0.3, 0.0), G.ry(-20), "3b8bff")
    B.p("Bird", (0.5, 0.5, 0.5), bc + (0.1, 0.75, -0.4), G.ry(-20), "5aa0ff")
    B.p("Bird", (0.2, 0.18, 0.35), bc + (0.2, 0.7, -0.75), G.ry(-20), "ffb02e")
    grass(B, (0.3, 0.0, -0.9), 3, GRASS, h=(0.9, 1.5))
    return B.finish()


def p_mailbox(sc, parent):
    B = Build(sc, parent, "Mailbox", seed=317)
    B.p("Post", (1.3, 0.4, 1.3), (0.0, 0.2, 0.0), None, WOOD[0])
    B.p("Post", (0.7, 3.8, 0.7), (0.0, 2.1, 0.0), None, WOOD[1])
    B.p("Post", (1.2, 0.3, 2.4), (0.0, 4.05, 0.0), None, WOOD[0])
    c = np.array((0.0, 4.95, 0.0))
    B.p("Box", (1.76, 0.94, 2.84), c, None, "e8403a")
    round3(B, "Box", c + (0.0, 0.45, 0.0), 1.8, 2.9, 1.8, ("e8403a", "d93a30", "f05a48"), R=G.rx(90))
    B.p("Door", (1.6, 1.8, 0.14), c + (0.0, 0.35, -1.5), None, "c8302a")
    B.p("Door", (0.3, 0.3, 0.24), c + (0.0, 0.5, -1.62), None, "c8ccd4")
    B.plate("Letter", (1.1, 0.12, 0.8), c + (0.25, 1.2, -1.2), G.ry(15) @ G.rx(-30), col="fff7ec")
    B.p("Flag", (0.18, 1.6, 0.14), c + (1.0, 0.75, 0.2), None, "8a8f9c")
    B.p("Flag", (0.14, 0.6, 0.9), c + (1.0, 1.2, -0.2), None, "ffd23f")
    for k, (x, z, col) in enumerate(((-0.8, -0.8, "ff6b8a"), (0.6, -1.0, "b46bff"), (0.9, 0.7, "ffd23f"))):
        B.p("Flower", (0.3, 0.9 + 0.2 * k, 0.3), (x, 0.45 + 0.1 * k, z), None, GRASS[2])
        B.p("Flower", (0.6, 0.35, 0.6), (x, 0.95 + 0.2 * k, z), G.ry(45), col)
    return B.finish()


def p_sacks(sc, parent):
    B = Build(sc, parent, "PotatoSacks", seed=318)
    sack(B, (-1.3, 0.0, 0.5), G.ry(10))
    sack(B, (0.8, 0.0, 1.2), G.ry(-25) @ G.rz(8), stamp=False, h=2.3)
    sack(B, (1.5, 0.0, -1.5), G.ry(-35), tied=False, stamp=False, h=2.2)
    for k, (x, y, z) in enumerate(((1.2, 2.25, -1.6), (1.9, 2.3, -1.3), (1.5, 2.6, -1.1), (3.2, 0.36, -2.6),
                                   (0.1, 0.36, -2.8))):
        spud(B, (x, y, z), 0.95, TATER[k % 3], heading=50 * k)
    return B.finish()


AREA = register(Area("Meadow", "Meadow Patch", hero, [
    (p_hayrolls, prop_attrs(4, 0.9, 1.2, "Edge", True)),
    (p_fence, prop_attrs(5, 0.9, 1.1, "Edge", True)),
    (p_cart, prop_attrs(3, 0.9, 1.2, "Side", True)),
    (p_beehive, prop_attrs(4, 0.9, 1.2, "Side", False)),
    (p_sunflowers, prop_attrs(6, 0.85, 1.25, "Side", False)),
    (p_signpost, prop_attrs(3, 0.9, 1.15, "Side", False)),
    (p_mailbox, prop_attrs(3, 0.9, 1.15, "Side", False)),
    (p_sacks, prop_attrs(6, 0.8, 1.2, "Any", False)),
], ground="68d03e"))
