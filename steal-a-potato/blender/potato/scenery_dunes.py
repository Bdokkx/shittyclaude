"""Sandy Dunes: the hero, a stepped pyramid with a potato pharaoh, and the area's props.

The pyramid: eight sandstone tiers, three shades getting lighter upwards, each capped with cream
trim and with a few stones standing proud of its face, a gold capstone on top. Set into its lane
face is a giant potato pharaoh: a golden potato face (kohl-lined eyes, a smile, pink cheeks) in a
blue-and-gold striped nemes with a gold band and a cobra rising from it, the nemes falling in
striped lappets either side of a striped beard and a broad collar. At its foot a gateway with a
dark doorway, hieroglyph cartouches on its jambs and a winged sun on its lintel; torches with
flickering flames either side; sand drifted against the bottom tier.
"""
import math

import numpy as np

import spsgeo as G

from .scenery import (Area, Build, INK, bar, flame, ori, potato, prop_attrs, register, round3, shade, turn)

SANDSTONE = ("e3b072", "ebbf86", "f3d09c")
TRIM = "fbe8c6"
SAND = ("e8c470", "f6dc96", "dcb460")
GOLD = ("f5c518", "e0a800", "ffd447")
BLUE = ("2f5fd0", "244ca8", "3b74e8")
FACE = ("e6b04c", "d49c3c", "f0c264")
TATER = ("d39a50", "c48a40", "dfaa62")
TERRA = ("c8643a", "d87a48", "b85a32")
GRANITE = ("d08a6a", "c47c5c", "dc9a7a")
CACTUS = ("4f9a3a", "5aa844", "448a34")
WATER = ("4ac0e8", "7ad4f0", "2fa0d0")
WOOD = ("8a5a2a", "a0703a", "c8945a")
SCARAB = ("2a9a8a", "238076", "3ab4a2")
RED = "c8302a"
CHEEK = "ff9aa8"
MUMMY = ("f2ecd8", "e2dac2", "faf6ea")
DARK = "2a2018"

TIERS, TH = 8, 4.0


def tier(i):
    """Width, front z and back z of tier i: the front steps back further than the back."""
    return 42.0 - 4.8 * i, -12.0 + 1.75 * i, 13.0 - 0.9 * i


def flower(B, c, s=1.0, col="ff6b9a", name="Flower"):
    """A flat flower: two squares turned 45 degrees from each other and a yellow middle."""
    c = np.asarray(c, float)
    return [B.p(name, (s, 0.3 * s, s), c, None, col),
            B.p(name, (s, 0.28 * s, s), c + (0.0, 0.02 * s, 0.0), G.ry(45), shade(col, 0.15)),
            B.p(name, (0.42 * s, 0.32 * s, 0.42 * s), c + (0.0, 0.08 * s, 0.0), G.ry(20), GOLD[2])]


def spud(B, c, s=1.0, col=TATER[0], name="Potato", heading=0.0):
    """A loose potato: a long block and a shorter one turned 45 degrees round it."""
    c = np.asarray(c, float)
    R = ori(8, heading, -6)
    return [B.p(name, (1.1 * s, 0.7 * s, 0.75 * s), c, R, col),
            B.p(name, (0.82 * s, 0.62 * s, 0.82 * s), c + R @ (0.0, 0.03 * s, 0.0), R @ G.ry(45), shade(col, 0.1))]


# ==================================================================== the pharaoh

def pharaoh(B, hc, w=13.0, h=12.0, d=8.0):
    """The giant potato pharaoh's head, centred at hc, face to -Z: a golden potato with a happy face
    in a striped nemes, a gold band and a cobra, lappets, a beard and a broad collar under it."""
    hc = np.asarray(hc, float)
    B.p("Pharaoh", (w * 0.82, h, d * 0.82), hc, None, FACE[0], solid=True)
    B.p("Pharaoh", (w, h * 0.8, d * 0.68), hc + (0.0, -h * 0.04, 0.0), None, FACE[1], solid=True)
    B.p("Pharaoh", (w * 0.68, h * 0.8 + 0.04, d), hc + (0.0, -h * 0.04, 0.0), None, FACE[2], solid=True)
    zf = hc[2] - d / 2 - 0.02

    def at(x, y, dz=0.0):
        return np.array((hc[0] + x, hc[1] + y, zf + dz))
    # the face: kohl-lined eyes with a glint, blue brows, a smile, pink cheeks
    for sx in (-1, 1):
        B.plate("Eye", (1.7, 2.5, 0.12), at(sx * 2.15, 0.8))
        B.plate("Eye", (0.7, 0.7, 0.1), at(sx * 2.15 + 0.35, 1.55, -0.05), col="ffffff")
        B.plate("Eye", (1.7, 0.38, 0.1), at(sx * 3.55, -0.2), G.rz(sx * 12))
        B.plate("Brow", (2.4, 0.4, 0.1), at(sx * 2.15, 2.65), col=BLUE[1])
        B.plate("Cheek", (1.7, 0.8, 0.1), at(sx * 3.4, -1.3), col=CHEEK)
        B.plate("Mouth", (0.9, 0.55, 0.12), at(sx * 1.95, -2.15, -0.03), G.rz(sx * 30))
    B.plate("Mouth", (3.4, 0.7, 0.12), at(0.0, -2.45))
    for x, y, sz in ((-3.3, 2.0, 0.55), (3.6, -3.4, 0.45), (-1.2, -4.3, 0.4)):
        B.plate("Freckle", (sz, sz, 0.1), at(x, y), G.rz(20), col=FACE[1])
    # the nemes: a gold band, stripes over the top stepping back like a dome, a cobra rising
    B.p("Nemes", (w + 1.0, 0.9, d + 0.8), hc + (0.0, 3.6, 0.0), None, GOLD[0])
    y = 4.05
    for k, (dw, hh, dd) in enumerate(((0.8, 1.0, 0.6), (0.5, 1.0, 0.4), (-0.2, 1.0, -0.2), (-2.0, 0.8, -1.6),
                                      (-4.6, 0.6, -3.4))):
        B.p("Nemes", (w + dw, hh, d + dd), hc + (0.0, y + hh / 2, 0.0), None, (BLUE[0], GOLD[0])[k % 2])
        y += hh
    bar(B, "Cobra", at(0.0, 3.3, -0.45), at(0.0, 5.2, -0.95), 0.55, GOLD[1])
    B.p("Cobra", (1.4, 1.6, 0.25), at(0.0, 5.0, -1.05), None, BLUE[2])
    B.p("Cobra", (0.7, 0.55, 0.9), at(0.0, 5.95, -1.0), None, GOLD[0])
    B.plate("Cobra", (0.4, 0.4, 0.1), at(0.0, 5.0, -1.22), col=RED)
    # the sides of the nemes falling past the face into lappets, flaring out, striped
    for sx in (-1, 1):
        for k in range(8):
            yk = 2.35 - 1.6 * k
            B.p("Nemes", (3.0, 1.6, 4.0), at(sx * (6.0 + 0.2 * k), yk, 2.0 - 0.5), None, (BLUE[0], GOLD[0])[k % 2])
    # a striped beard under the chin, a broad collar on the tier below
    for k, col in enumerate((GOLD[0], BLUE[0], GOLD[1])):
        B.p("Beard", (1.4 - 0.1 * k, 1.2, 1.2), np.array((hc[0], hc[1] - h / 2 - 0.4 - 1.2 * k, zf - 0.3)), None, col)
    return hc


# ==================================================================== the hero

def hero(sc, parent):
    B = Build(sc, parent, "Dunes", seed=401)
    rng = B.rng
    # the tiers: lighter upwards, a cream trim on each, stones standing proud of the face
    for i in range(TIERS):
        W, zf, zb = tier(i)
        y = TH * i
        col = SANDSTONE[i * 3 // TIERS]
        B.p("Tier", (W, TH - 0.5, zb - zf), (0.0, y + (TH - 0.5) / 2, (zf + zb) / 2), None, col, solid=True)
        B.p("Tier", (W + 0.5, 0.5, zb - zf + 0.25), (0.0, y + TH - 0.25, (zf + zb) / 2 - 0.125), None, TRIM, solid=True)
        lo = 6.0 if i < 2 else 9.8
        hi = W / 2 - 1.4
        if hi - lo > 2.2:
            for sx in (-1, 1):
                w = float(rng.uniform(1.8, min(3.6, hi - lo - 0.2)))
                x = sx * float(rng.uniform(lo + w / 2, hi - w / 2))
                B.p("Stone", (w, TH - 1.4, 0.3), (x, y + 1.6, zf - 0.1 - 0.04 * (sx > 0)), None,
                    shade(col, 0.07 if (i + sx) % 2 else -0.06))
        if i < 5:
            for sx in (-1, 1):
                d = float(rng.uniform(2.4, 3.6))
                z = float(rng.uniform(zf + 1.5 + d / 2, zb - 1.5 - d / 2))
                B.p("Stone", (0.3, TH - 1.4, d), (sx * (W / 2 + 0.1 + 0.04 * (i % 2)), y + 1.6, z), None,
                    shade(col, -0.06 if (i + sx) % 2 else 0.07))
    # the gateway: jambs, lintel and cornice round a dark doorway, a step; cartouches, a winged sun
    zg = tier(0)[1]
    for sx in (-1, 1):
        B.p("Gate", (1.5, 7.2, 3.4), (sx * 3.2, 3.6, zg + 0.3), None, SANDSTONE[1], solid=True)
        B.plate("Cartouche", (1.0, 5.0, 0.12), (sx * 3.2, 3.8, zg - 1.46), col=TRIM)
        B.p("Gate", (1.9, 0.5, 3.6), (sx * 3.2, 6.9, zg + 0.3), None, GOLD[1])
        for k, (gy, sz, col, rot) in enumerate(((5.4, (0.5, 0.9), INK, 0.0), (3.9, (0.7, 0.4), BLUE[0], 0.0),
                                                (2.4, (0.45, 0.45), RED, 45.0))):
            B.plate("Glyph", sz + (0.1,), (sx * 3.2, gy, zg - 1.55), G.rz(rot), col=col)
    B.p("Gate", (8.2, 1.6, 5.2), (0.0, 8.0, zg + 1.0), None, SANDSTONE[2], solid=True)
    B.p("Gate", (9.0, 0.6, 5.4), (0.0, 9.1, zg + 0.9), None, TRIM, solid=True)
    B.plate("Door", (4.86, 7.2, 0.12), (0.0, 3.6, zg - 0.32), col=DARK)
    B.p("Step", (5.6, 0.5, 1.6), (0.0, 0.25, zg - 2.2), None, SANDSTONE[0], solid=True)
    for k, R in enumerate((None, G.rz(45))):
        B.p("Sun", (1.5, 1.5, 0.3), (0.0, 8.0, zg - 1.75 - 0.04 * k), R, GOLD[k])
    for sx in (-1, 1):
        B.p("Sun", (2.6, 0.7, 0.2), (sx * 2.15, 8.15, zg - 1.7), G.rz(sx * 10), BLUE[0])
    # hieroglyph panels on the bottom tier either side of the gate
    for sx in (-1, 1):
        px = sx * 12.6
        B.p("Panel", (5.2, 2.7, 0.24), (px, 1.75, zg - 0.12), None, TRIM)
        for k, (dx, sz, col, rot) in enumerate(((-1.7, (0.5, 1.2), INK, 0.0), (-0.6, (0.8, 0.5), BLUE[0], 0.0),
                                                (0.55, (0.6, 0.6), RED, 45.0), (1.7, (0.45, 1.1), BLUE[1], 0.0))):
            B.plate("Glyph", sz + (0.1,), (px + dx * sx, 1.75 + 0.1 * (k % 2), zg - 0.29), G.rz(rot), col=col)
    # painted clay pots at the foot
    pot(B, (17.6, 0.0, -13.6), 0.95, TERRA, band=BLUE[0])
    pot(B, (-17.4, 0.0, -13.5), 0.9, (TERRA[1], TERRA[0], TERRA[2]), band=INK)
    pot(B, (-15.5, 0.0, -14.4), 0.6, (TERRA[2], TERRA[1], TERRA[0]), band=BLUE[0])
    # a little mummy potato peeking out of the doorway
    mc = np.array((1.25, 1.5, zg - 0.55))
    potato(B, mc, 2.9, MUMMY, R=G.ry(-20), name="Mummy", glints=True)
    for k, (dy, rz) in enumerate(((0.75, 14.0), (-0.45, -10.0))):
        B.p("Bandage", (2.7, 0.32, 2.5 - 0.04 * k), mc + (0.0, dy, 0.0), G.ry(-20) @ G.rz(rz), MUMMY[2])
    bar(B, "Mummy", mc + (-1.0, -0.1, -0.4), mc + (-1.7, 0.1, -1.6), 0.6, MUMMY[1])
    # torches either side of the gate
    for sx in (-1, 1):
        tx, tz = sx * 5.8, zg - 2.4
        B.p("Torch", (1.6, 0.6, 1.6), (tx, 0.3, tz), G.ry(45), SANDSTONE[0])
        B.p("Torch", (0.8, 4.4, 0.8), (tx, 2.8, tz), None, WOOD[0])
        B.p("Torch", (1.8, 0.7, 1.8), (tx, 5.2, tz), G.ry(45), GOLD[1])
        B.p("Torch", (1.9, 0.3, 1.9), (tx, 5.6, tz), None, GOLD[0])
        flame(B, (tx, 6.5, tz), 1.2)
    # the pharaoh set into the face above the gate, its collar on the tier below
    pharaoh(B, (0.0, 18.06, -4.6))
    z2 = tier(2)[1]
    for k, (w, col) in enumerate(((8.6, GOLD[0]), (7.2, BLUE[0]), (5.6, RED))):
        B.p("Collar", (w, 0.75, 0.25), (0.0, 11.45 - 0.75 * k, z2 - 0.12 - 0.02 * k), None, col)
    # a gold ankh on the top tier
    W, zf, zb = tier(TIERS - 1)
    z7 = zf - 0.12
    B.p("Ankh", (0.7, 1.8, 0.24), (0.0, 29.0, z7), None, GOLD[1])
    B.p("Ankh", (2.0, 0.55, 0.26), (0.0, 30.0, z7 - 0.03), None, GOLD[0])
    B.p("Ankh", (1.3, 1.3, 0.24), (0.0, 30.95, z7), G.rz(45), GOLD[0])
    B.p("Ankh", (0.6, 0.6, 0.1), (0.0, 30.95, z7 - 0.16), G.rz(45), SANDSTONE[2])
    # the capstone
    y = TH * TIERS
    for k, (s, h) in enumerate(((6.0, 1.3), (4.4, 1.2), (2.8, 1.1), (1.3, 1.0))):
        B.p("Capstone", (s, h, s * 0.86), (0.0, y + h / 2, (zf + zb) / 2), G.ry(45.0 * (k == 3)), GOLD[(k + 1) % 3],
            solid=k < 2)
        y += h - 0.03
    # sand drifted against the foot, a fallen stone
    for k, (x, z, w, d, a) in enumerate(((-15.5, -13.0, 7.0, 3.0, 10.0), (15.0, -13.2, 6.0, 2.6, -12.0),
                                         (-20.4, -4.0, 2.6, 7.0, 4.0), (20.4, 2.0, 2.4, 6.0, -6.0))):
        B.p("Sand", (w, 0.35 + 0.04 * k, d), (x, 0.17 + 0.02 * k, z), G.ry(a), SAND[k % 3])
    B.p("Rubble", (2.6, 1.4, 2.0), (11.6, 0.62, -14.2), ori(6, 30, 8), SANDSTONE[1])
    B.p("Rubble", (1.2, 0.8, 1.0), (9.8, 0.36, -14.8), ori(-8, 60, 5), SANDSTONE[0])
    return B.finish()


# ==================================================================== props

def pot(B, c, s, cols, band=None, R=None, name="Pot"):
    """A clay pot: a foot, a wide round belly (Folk Valley's round) with a painted band, a turned
    shoulder, a neck and a round rim."""
    R = np.eye(3) if R is None else R
    c = np.asarray(c, float)
    w = 2.3 * s
    belly = c + R @ (0.0, 1.3 * s, 0.0)
    out = [B.p(name, (1.3 * s, 0.32 * s, 1.3 * s), c + R @ (0.0, 0.16 * s, 0.0), R @ G.ry(45), cols[2])]
    out += round3(B, name, belly, w, 2.0 * s, w, cols, R=R)
    if band:
        out.append(B.p(name, (w + 0.04, 0.3 * s, w * 0.68 + 0.04), belly + R @ (0.0, 0.25 * s, 0.0), R, band))
        out.append(B.p(name, (w * 0.68 + 0.04, 0.32 * s, w + 0.04), belly + R @ (0.0, 0.25 * s, 0.0), R, band))
    out.append(B.p(name, (1.6 * s, 0.45 * s, 1.6 * s), c + R @ (0.0, 2.45 * s, 0.0), R @ G.ry(45), cols[1]))
    out.append(B.p(name, (0.85 * s, 0.8 * s, 0.85 * s), c + R @ (0.0, 2.9 * s, 0.0), R, cols[0]))
    out.append(B.p(name, (1.35 * s, 0.3 * s, 1.35 * s), c + R @ (0.0, 3.35 * s, 0.0), R, cols[2]))
    out.append(B.p(name, (1.3 * s, 0.28 * s, 1.3 * s), c + R @ (0.0, 3.39 * s, 0.0), R @ G.ry(45), cols[2]))
    return out


def p_obelisk(sc, parent):
    B = Build(sc, parent, "Obelisk", seed=411)
    B.p("Base", (3.8, 0.8, 3.8), (0.0, 0.4, 0.0), None, SANDSTONE[0])
    B.p("Base", (3.0, 0.6, 3.0), (0.0, 1.1, 0.0), None, TRIM)
    y = 1.4
    for k, (s, h) in enumerate(((2.0, 4.2), (1.8, 4.0), (1.6, 3.8))):
        B.p("Obelisk", (s, h, s), (0.0, y + h / 2, 0.0), None, GRANITE[k])
        y += h
    B.p("Tip", (1.6, 0.7, 1.6), (0.0, y + 0.35, 0.0), None, GOLD[1])
    B.p("Tip", (1.1, 0.7, 1.1), (0.0, y + 1.0, 0.0), G.ry(45), GOLD[0])
    B.p("Tip", (0.5, 0.5, 0.5), (0.0, y + 1.55, 0.0), None, GOLD[2])
    for k, (gy, sz, col, rot, z) in enumerate(((11.2, (0.5, 0.9), INK, 0.0, -0.85), (9.0, (0.8, 0.4), BLUE[0], 0.0, -0.95),
                                               (7.2, (0.5, 0.5), RED, 45.0, -0.95), (5.0, (0.4, 1.0), INK, 0.0, -1.05),
                                               (3.0, (0.8, 0.5), BLUE[1], 0.0, -1.05))):
        B.plate("Glyph", sz + (0.1,), (0.0, gy, z - 0.05), G.rz(rot), col=col)
    return B.finish()


def p_pots(sc, parent):
    B = Build(sc, parent, "ClayPots", seed=412)
    pot(B, (-1.0, 0.0, 0.3), 1.0, TERRA, band=BLUE[0])
    pot(B, (1.5, 0.0, -0.1), 0.72, (TERRA[1], TERRA[0], TERRA[2]), band=INK)
    pot(B, (0.4, 0.75, -2.3), 0.5, (TERRA[2], TERRA[1], TERRA[0]), R=G.ry(-30) @ G.rz(-80))
    for k, (x, z, a) in enumerate(((-2.6, -1.8, 20.0), (2.9, -1.7, -35.0))):
        B.p("Shard", (0.9, 0.16 + 0.02 * k, 0.6), (x, 0.08 + 0.01 * k, z), G.ry(a), TERRA[k])
    return B.finish()


def p_saguaro(sc, parent):
    B = Build(sc, parent, "Saguaro", seed=413)
    B.p("Sand", (3.4, 0.4, 3.0), (0.0, 0.2, 0.0), G.ry(15), SAND[0])
    y = 0.3
    for k, (w, h) in enumerate(((2.0, 3.2), (1.9, 3.2), (1.8, 2.8))):
        B.p("Cactus", (w, h + 0.05, w), (0.05 * k, y + h / 2, 0.0), ori(0, 8 * k, 2 * (-1) ** k), CACTUS[k % 3])
        y += h
    B.p("Cactus", (1.4, 0.6, 1.4), (0.1, y + 0.2, 0.0), G.ry(20), CACTUS[1])
    for sx, y0, up in ((-1, 3.6, 3.0), (1, 5.4, 2.4)):
        bar(B, "Arm", (sx * 0.8, y0, 0.0), (sx * 2.4, y0 + 0.2, 0.0), 1.2, CACTUS[0])
        bar(B, "Arm", (sx * 2.4, y0 - 0.4, 0.0), (sx * 2.5, y0 + up, 0.0), 1.2, CACTUS[2], t=1.26)
        B.p("Arm", (0.9, 0.4, 0.9), (sx * 2.5, y0 + up + 0.1, 0.0), G.ry(30), CACTUS[1])
    flower(B, (0.1, y + 0.6, 0.0), 1.1)
    flower(B, (2.5, 5.4 + 2.4 + 0.45, 0.0), 0.7)
    for k, (x, yy, z) in enumerate(((-0.6, 2.2, -1.05), (0.5, 4.9, -1.0), (-0.5, 7.4, -0.95), (-2.3, 5.4, -0.65))):
        B.p("Spine", (0.2, 0.2, 0.2), (x, yy, z), G.ry(45), "fff4dc")
    return B.finish()


def p_oasis(sc, parent):
    B = Build(sc, parent, "OasisPool", seed=414)
    B.p("Water", (6.0, 0.2, 4.0), (0.0, 0.1, 0.0), None, WATER[0])
    B.p("Water", (4.0, 0.22, 6.0), (0.0, 0.11, 0.0), None, WATER[0])
    B.p("Water", (4.6, 0.24, 4.6), (0.0, 0.12, 0.0), G.ry(45), WATER[2])
    B.p("Water", (2.0, 0.26, 1.4), (0.9, 0.13, -0.9), G.ry(20), WATER[1])
    for k in range(8):
        a = math.radians(22.5 + 45 * k)
        p = np.array((math.cos(a) * 3.5, 0.25 + 0.05 * (k % 3), math.sin(a) * 3.5))
        t = np.array((-math.sin(a), 0.0, math.cos(a)))
        bar(B, "Rim", p - t * 1.0, p + t * 1.0, 1.0, (SANDSTONE[0], TRIM, SANDSTONE[1])[k % 3], t=0.5 + 0.1 * (k % 3),
            n=(0, 1, 0))
    for c, hd in (((-2.6, 0.0, 2.4), 20.0), ((3.0, 0.0, 1.6), 140.0)):
        c = np.array(c)
        for j in range(3):
            a = math.radians(hd + 120 * j)
            b = c + (0.4 * math.cos(a), 0.0, 0.4 * math.sin(a))
            h = 2.6 + 0.5 * j
            tip = b + (0.5 * math.cos(a), h, 0.5 * math.sin(a))
            bar(B, "Reed", b, tip, 0.24 + 0.02 * j, CACTUS[j % 3])
            if j < 2:
                B.p("Reed", (0.42, 1.0, 0.42), b + (tip - b) * 0.82, None, WOOD[0])
    B.p("Lily", (1.4, 0.1, 1.2), (-1.0, 0.3, -0.8), G.ry(25), CACTUS[1])
    B.p("Lily", (0.45, 0.45, 0.45), (-0.9, 0.55, -0.8), ori(35.26, 45, 0), "ff7aa8")
    return B.finish()


def p_stall(sc, parent):
    B = Build(sc, parent, "MarketStall", seed=415)
    for sx in (-1, 1):
        for sz in (-1, 1):
            h = 6.0 if sz > 0 else 5.2
            B.p("Post", (0.5, h, 0.5), (sx * 2.8, h / 2, sz * 1.3), None, WOOD[0])
    B.p("Counter", (5.6, 2.4, 1.8), (0.0, 1.2, -0.5), None, WOOD[1])
    B.p("Counter", (6.4, 0.4, 2.2), (0.0, 2.6, -0.5), None, WOOD[2])
    for k in range(4):
        B.plate("Cloth", (1.4, 2.0, 0.1), (-2.1 + 1.4 * k, 1.3, -1.45), col=("e8403a", "fff1d0")[k % 2])
    for k in range(6):
        x = -2.75 + 1.1 * k
        B.p("Awning", (1.1, 0.16 + 0.02 * (k % 2), 3.9), (x, 5.75, 0.0), G.rx(-17), ("e8403a", "fff1d0")[k % 2])
    B.p("Basket", (1.8, 0.8, 1.3), (-1.4, 3.2, -0.6), G.ry(8), WOOD[2])
    for k, (x, z) in enumerate(((-1.9, -0.7), (-1.1, -0.5), (-1.5, -0.6))):
        spud(B, (x, 3.75 + 0.2 * (k == 2), z), 0.85, TATER[k], heading=40 * k)
    pot(B, (1.5, 2.8, -0.6), 0.5, TERRA, band=BLUE[0])
    bar(B, "Lantern", (0.3, 5.5, -1.0), (0.3, 4.6, -1.0), 0.12, INK)
    B.p("Lantern", (0.6, 0.8, 0.6), (0.3, 4.25, -1.0), G.ry(45), "ffb347", material="Neon", flicker=0.12, lamp=True)
    return B.finish()


def p_scarab(sc, parent):
    B = Build(sc, parent, "Scarab", seed=416)
    B.p("Plinth", (7.0, 1.0, 3.8), (0.0, 0.5, 0.0), None, SANDSTONE[0])
    B.p("Plinth", (7.4, 0.4, 4.2), (0.0, 1.2, 0.0), None, TRIM)
    top = 1.4
    bc = np.array((-1.3, top + 1.35, 0.0))
    round3(B, "Scarab", bc, 3.6, 1.8, 3.0, SCARAB, lid=(2.6, 0.4, 2.2))
    B.p("Scarab", (3.0, 0.14, 0.2), bc + (-0.1, 1.27, 0.0), None, GOLD[0])
    B.p("Scarab", (1.3, 1.3, 2.5), bc + (2.0, -0.1, 0.0), None, SCARAB[1])
    B.p("Scarab", (0.8, 0.7, 1.7), bc + (2.9, -0.35, 0.0), None, SCARAB[2])
    B.p("Scarab", (0.4, 0.4, 1.5), bc + (3.4, -0.4, 0.0), None, GOLD[0])
    for sz in (-1, 1):
        for k, dx in enumerate((-1.1, 0.2, 1.7)):
            a = bc + (dx, -0.5, sz * 1.1)
            bar(B, "Leg", a, (a[0] + 0.5 * (k - 1), top, sz * 1.85), 0.3, INK)
    potato(B, (3.6, top + 1.5, 0.0), 3.0, TATER, R=G.ry(-15), name="Potato", glints=True, cheeks=CHEEK)
    return B.finish()


def p_camel(sc, parent):
    B = Build(sc, parent, "Camel", seed=417)
    fur = ("d8a868", "c8945a", "e6b87a")
    B.p("Camel", (5.0, 2.2, 2.2), (0.0, 4.4, 0.0), None, fur[0])
    B.p("Camel", (4.2, 0.8, 2.0), (0.0, 3.3, 0.0), None, fur[1])
    B.p("Hump", (2.6, 1.4, 1.9), (-0.4, 5.9, 0.0), None, fur[2])
    B.p("Hump", (1.6, 0.8, 1.5), (-0.4, 6.8, 0.0), G.ry(45), fur[0])
    for sx in (-1, 1):
        for sz in (-1, 1):
            B.p("Leg", (0.7, 3.4, 0.7), (sx * 1.8, 1.7, sz * 0.6), None, fur[1 + (sx > 0)])
    bar(B, "Neck", (2.0, 4.6, 0.0), (3.4, 6.8, 0.0), 1.0, fur[0])
    B.p("Head", (1.8, 1.0, 1.1), (3.9, 7.1, 0.0), None, fur[2])
    B.p("Head", (0.9, 0.8, 0.9), (4.75, 6.85, 0.0), None, fur[1])
    for sz in (-1, 1):
        B.p("Ear", (0.3, 0.5, 0.3), (3.4, 7.75, sz * 0.35), None, fur[1])
        B.plate("Eye", (0.36, 0.36, 0.1), (4.1, 7.3, sz * 0.6))
    bar(B, "Tail", (-2.5, 4.9, 0.0), (-2.9, 3.4, 0.0), 0.3, fur[1])
    B.p("Tail", (0.5, 0.6, 0.5), (-2.95, 3.2, 0.0), None, WOOD[0])
    B.p("Saddle", (1.6, 0.2, 2.5), (1.3, 5.56, 0.0), None, "e8403a")
    for sz in (-1, 1):
        B.p("Saddle", (1.5, 1.4, 0.15), (1.3, 4.9, sz * 1.18), None, ("e8403a", BLUE[0])[sz > 0])
        B.p("Saddle", (1.6, 0.3, 0.17), (1.3, 4.3, sz * 1.2), None, GOLD[0])
    return B.finish()


def p_scorpion(sc, parent):
    B = Build(sc, parent, "Scorpion", seed=418)
    col = ("c86a3a", "b05a30", "d88050")
    B.p("Scorpion", (1.8, 0.6, 1.4), (0.0, 0.6, 0.0), None, col[0])
    B.p("Scorpion", (1.4, 0.5, 1.2), (-1.4, 0.58, 0.0), None, col[1])
    B.p("Scorpion", (1.0, 0.5, 1.1), (1.3, 0.58, 0.0), None, col[2])
    pts = [np.array(p) for p in ((-2.0, 0.6, 0.0), (-2.8, 1.4, 0.0), (-3.0, 2.6, 0.0), (-2.5, 3.6, 0.0), (-1.6, 4.0, 0.0))]
    for k in range(4):
        bar(B, "Tail", pts[k], pts[k + 1], 0.55 - 0.05 * k, col[k % 2], over=0.15)
    B.p("Sting", (0.4, 0.8, 0.46), (-1.15, 3.7, 0.0), G.rz(40), INK)
    for sz in (-1, 1):
        bar(B, "Claw", (1.6, 0.6, sz * 0.5), (2.6, 0.7, sz * 1.2), 0.36, col[1])
        B.p("Claw", (0.9, 0.42, 0.6), (3.1, 0.75, sz * 1.35), G.ry(-sz * 20), col[2])
        B.p("Claw", (0.6, 0.3, 0.3), (3.7, 0.75, sz * 1.15), G.ry(-sz * 35), col[0])
        for k, x in enumerate((-1.0, -0.2, 0.6)):
            bar(B, "Leg", (x, 0.5, sz * 0.6), (x - 0.4, 0.0, sz * 1.6), 0.18, col[1])
        B.p("Eye", (0.2, 0.2, 0.2), (1.6, 0.9, sz * 0.25), None, INK)
    return B.finish()


AREA = register(Area("Dunes", "Sandy Dunes", hero, [
    (p_obelisk, prop_attrs(3, 0.9, 1.2, "Edge", True)),
    (p_stall, prop_attrs(3, 0.9, 1.1, "Edge", True)),
    (p_saguaro, prop_attrs(6, 0.85, 1.3, "Side", True)),
    (p_oasis, prop_attrs(3, 0.9, 1.2, "Side", False)),
    (p_scarab, prop_attrs(3, 0.9, 1.2, "Side", True)),
    (p_camel, prop_attrs(3, 0.9, 1.15, "Side", True)),
    (p_pots, prop_attrs(6, 0.8, 1.2, "Any", False)),
    (p_scorpion, prop_attrs(5, 0.9, 1.4, "Any", False)),
], ground="f2d280"))
