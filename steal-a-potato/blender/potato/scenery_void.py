"""Glitch Void: the hero, a huge black cube with lit edges, and the area's props.

The cube stands on one corner, hovering over a cracked dark platform: black faces, glowing cyan
edges and a slice of it slipped sideways like a bad signal; glitch debris rises from under it. Glowing cracks run out across the platform from under it; pixels of static lie
about. Small cubes float round it, some turning (Spin); two checkered "missing texture" blocks and a
floating error window hang in the air; four little black obelisks with lit tops stand at the
platform's edge.
"""
import math

import numpy as np

import spsgeo as G

from .scenery import (Area, Build, INK, bar, ori, prop_attrs, register, rock, shade)

VOID = ("0e0c14", "16131f", "1e1a2e", "26223a")
CYAN, MAGENTA, PURPLE, WHITE = "00f0ff", "ff2bd6", "a46bff", "e8e8ff"


def glow(B, name, size, pos, R=None, col=CYAN, flicker=0.12, **kw):
    return B.p(name, size, pos, R, col, material="Neon", flicker=flicker, lamp=True, **kw)


def edged_cube(B, c, s, R, col=VOID[0], edge=CYAN, w=0.5, name="Cube", solid=False):
    """A black cube of side s at c turned by R, a glowing bar along each of its twelve edges."""
    c = np.asarray(c, float)
    out = [B.p(name, (s, s, s), c, R, col, solid=solid)]
    h = s / 2
    for ax in range(3):
        for a in (-1, 1):
            for b in (-1, 1):
                off = np.zeros(3)
                others = [i for i in range(3) if i != ax]
                off[others[0]] = a * (h - w / 2 + 0.06)
                off[others[1]] = b * (h - w / 2 + 0.06)
                size = [w + 0.01 * ax, w + 0.01 * ax, w + 0.01 * ax]
                size[ax] = s + w * 0.9 - 0.02 * (a + b + 2)
                out.append(B.p("Edge", tuple(size), c + R @ off, R, edge, material="Neon", flicker=0.1, lamp=True))
    return out


def checker(B, c, s, name="Missing", R=None, spin=None):
    """A 'missing texture' block: magenta and black squares by turns, 2 x 2 x 2."""
    R = np.eye(3) if R is None else R
    c = np.asarray(c, float)
    out = []
    q = s / 2
    for i in (-1, 1):
        for j in (-1, 1):
            for k in (-1, 1):
                if (i + j + k) % 4 == 1 or (i + j + k) == -3:
                    col = MAGENTA
                else:
                    col = VOID[0]
                mat = "Neon" if col == MAGENTA else "Plastic"
                out.append(B.p(name, (q, q, q), c + R @ (i * q / 2, j * q / 2, k * q / 2), R, col, material=mat,
                               lamp=mat == "Neon"))
    return out


def error_window(B, c, w=7.0, h=4.6, R=None, name="ErrorWindow"):
    """A floating error message: a pale window, a blue title bar, a red X, a yellow warning sign,
    two grey lines of text."""
    R = np.eye(3) if R is None else R
    c = np.asarray(c, float)
    out = [B.p(name, (w, h, 0.4), c, R, "e8ecf4"),
           B.p(name, (w + 0.04, 0.9, 0.46), c + R @ (0, h / 2 - 0.42, 0), R, "3b6bd8"),
           B.p(name, (0.7, 0.6, 0.12), c + R @ (w / 2 - 0.6, h / 2 - 0.45, -0.28), R, "e8403a", material="Neon",
               lamp=True),
           B.p(name, (1.3, 1.3, 0.12), c + R @ (-w / 2 + 1.2, -0.3, -0.26), R @ G.rz(45), "ffd23f",
               material="SmoothPlastic", shadow=False)]
    for k, L in enumerate((w * 0.55, w * 0.4)):
        out.append(B.p(name, (L, 0.32, 0.12), c + R @ (0.6 + (w * 0.55 - L) / -2 + 0.1, 0.1 - 0.7 * k, -0.26), R,
                       "8a90a0", material="SmoothPlastic", shadow=False))
    return out


# ==================================================================== the hero

def hero(sc, parent):
    B = Build(sc, parent, "Void", seed=171)
    # the cracked platform: three dark slabs making a hexagon, glowing cracks, static
    for k in range(3):
        B.p("Platform", (26.0 - 0.3 * k, 1.2 + 0.1 * k, 15.0), (0.0, 0.6 + 0.05 * k, 1.0), G.ry(60 * k), VOID[1 + k % 2],
            solid=True)
    top = 1.3
    for k in range(6):
        a = math.radians(30 + 60 * k + 8 * (-1) ** k)
        d = np.array((math.cos(a), 0, math.sin(a)))
        p0 = np.array((0.0, top + 0.02 * (k % 2), 1.0)) + d * 2.5
        p1 = p0 + d * (8.0 + 1.5 * (k % 2)) + np.array((0, 0, 0)) + np.cross((0, 1, 0), d) * 1.2 * (-1) ** k
        bar(B, "Crack", p0, p1, 0.4, (MAGENTA, CYAN)[k % 2], t=0.12, n=(0, 1, 0), material="Neon", flicker=0.2,
            lamp=True)
    for k in range(8):
        a = math.radians(45 * k + 20)
        r = 9.5 + 2.0 * (k % 3)
        B.p("Static", (0.9, 0.14 + 0.01 * k, 0.9), (math.cos(a) * r, top + 0.06, 1.0 + math.sin(a) * r * 0.55),
            G.ry(15 * k), ("8a90a0", "e8e8ff", "4a4e5a")[k % 3])
    # the cube on its corner, a slipped slice, a ghost of it
    s = 15.0
    R = G.ry(20) @ G.rx(35.264) @ G.rz(45)
    c = np.array((0.0, top + 2.5 + s * math.sqrt(3) / 2, 1.0))
    edged_cube(B, c, s, R, solid=True)
    B.p("Slice", (s + 1.6, 1.8, s * 0.9), c + R @ (1.1, 1.0, 0), R, VOID[3])
    glow(B, "Slice", (s + 1.62, 0.3, s * 0.92), c + R @ (1.1, 1.0 + 0.8, 0), R, col=MAGENTA)
    for k in range(8):                                                  # glitch debris rising from under it
        a = math.radians(45 * k + 10)
        r = 3.2 + 1.1 * (k % 3)
        p = np.array((math.cos(a) * r, top + 0.8 + 1.4 * k, 1.0 + math.sin(a) * r * 0.7))
        sz = 0.7 + 0.15 * (k % 3)
        if k % 2:
            glow(B, "Debris", (sz, sz, sz), p, ori(15 * k, 30 * k, 10), col=(CYAN, MAGENTA, PURPLE)[k % 3])
        else:
            B.p("Debris", (sz, sz, sz), p, ori(15 * k, 30 * k, 10), VOID[0])
    # cubes floating round it, some turning
    for k, (x, y, z, sz, col) in enumerate(((-13.0, 8.0, -4.0, 2.2, None), (12.6, 11.0, -3.0, 1.8, MAGENTA),
                                             (-10.5, 18.0, 3.0, 1.4, CYAN), (11.0, 22.0, 5.0, 2.0, None),
                                             (-6.0, 27.0, -2.0, 1.2, PURPLE), (7.4, 4.6, -6.0, 1.0, CYAN))):
        if col is None:
            B.p("Pixel", (sz, sz, sz), (x, y, z), G.ry(15 * k), VOID[0], spin=25.0 + 10 * k)
            glow(B, "Pixel", (sz * 0.7, 0.12, sz * 0.7), (x, y + sz / 2 + 0.06, z), G.ry(15 * k), col=CYAN,
                 spin=25.0 + 10 * k)
        else:
            glow(B, "Pixel", (sz, sz, sz), (x, y, z), ori(20, 30 * k, 10), col=col, spin=30.0 + 8 * k)
    # missing-texture blocks and an error window hanging in the air
    checker(B, (-15.0, 14.0, 6.0), 3.2, R=ori(10, 25, 15))
    checker(B, (16.0, 15.0, 7.0), 2.6, R=ori(-12, -30, 20))
    error_window(B, (13.0, 26.0, 6.0), R=ori(0, -12, 6))
    # four little obelisks with lit tops at the platform's edge
    for k, (x, z) in enumerate(((-14.0, -5.0), (14.0, -5.0), (-12.0, 9.0), (12.0, 9.0))):
        B.p("Obelisk", (1.6, 6.0, 1.6), (x, top + 3.0, z), G.ry(45 * (k % 2)), VOID[0], solid=True)
        glow(B, "Obelisk", (1.0, 1.0, 1.0), (x, top + 6.6, z), ori(35.26, 45, 0), col=(CYAN, MAGENTA)[k % 2])
    return B.finish()


# ==================================================================== props

def p_tree(sc, parent):
    B = Build(sc, parent, "GlitchTree", seed=181)
    B.p("Trunk", (1.4, 6.0, 1.4), (0.0, 3.0, 0.0), None, VOID[2])
    glow(B, "Trunk", (0.24, 5.4, 0.24), (0.66, 3.1, -0.66), col=CYAN)
    for k, (x, y, z, s, col) in enumerate(((0.0, 7.6, 0.0, 4.0, "2a6a4a"), (2.2, 6.8, 0.6, 2.4, "1e5a3a"),
                                            (-2.0, 7.0, -0.4, 2.6, "2a6a4a"), (0.6, 9.8, -0.2, 2.2, "3a8a5a"),
                                            (-1.0, 9.0, 1.4, 1.6, "1e5a3a"))):
        B.p("Leaves", (s, s * 0.9, s), (x + 0.4 * (k % 2), y, z), G.ry(10 * k), col)
    for k, (x, y, z, col) in enumerate(((3.4, 9.6, -0.4, MAGENTA), (-3.2, 10.4, 0.6, CYAN), (1.6, 11.6, 1.0, MAGENTA))):
        glow(B, "Glitch", (0.8, 0.8, 0.8), (x, y, z), G.ry(20 * k), col=col)
    B.p("Root", (2.4, 0.4, 2.4), (0.0, 0.2, 0.0), G.ry(45), VOID[1])
    return B.finish()


def p_cubes(sc, parent):
    B = Build(sc, parent, "FloatingCubes", seed=182)
    B.p("Base", (3.4, 0.4, 3.4), (0.0, 0.2, 0.0), G.ry(20), VOID[2])
    glow(B, "Base", (2.4, 0.12, 2.4), (0.0, 0.46, 0.0), G.ry(65), col=PURPLE)
    glow(B, "Pixel", (0.5, 0.5, 0.5), (1.3, 0.85, -1.0), G.ry(30), col=MAGENTA)
    for k, (x, y, z, s, col) in enumerate(((0.0, 2.6, 0.0, 1.6, None), (1.6, 4.4, 0.6, 1.0, CYAN), (-1.4, 5.2, -0.4,
                                                                                                  1.2, MAGENTA),
                                            (0.4, 6.8, 0.2, 0.9, None), (-0.6, 8.0, 0.8, 0.7, CYAN))):
        if col is None:
            B.p("Pixel", (s, s, s), (x, y, z), ori(20, 30 * k, 15), VOID[0])
            glow(B, "Pixel", (s * 0.6, 0.1, s * 0.6), (x, y + s / 2 + 0.05, z), None, col=CYAN, flicker=0.2)
        else:
            glow(B, "Pixel", (s, s, s), (x, y, z), ori(20, 30 * k, 15), col=col, spin=40.0 + 10 * k)
    return B.finish()


def p_error(sc, parent):
    B = Build(sc, parent, "ErrorSign", seed=183)
    B.p("Post", (0.5, 6.0, 0.5), (0.0, 3.0, 0.4), None, VOID[2])
    B.p("Post", (1.6, 0.5, 1.6), (0.0, 0.25, 0.4), G.ry(45), VOID[1])
    error_window(B, (0.0, 7.6, 0.0), w=6.0, h=4.0, R=ori(0, 0, 4))
    glow(B, "Post", (0.2, 5.0, 0.2), (0.3, 3.0, 0.1), col=MAGENTA)
    B.p("Post", (0.9, 0.9, 0.9), (1.4, 0.45, -0.6), ori(0, 30, 0), VOID[0])
    return B.finish()


def p_crystal(sc, parent):
    B = Build(sc, parent, "VoidCrystal", seed=184)
    rock(B, (0.0, 0.0, 0.0), 2.4, (VOID[1], VOID[2], VOID[3]))
    for k, (x, z, h, lean, w) in enumerate(((0.0, 0.0, 6.0, 0.0, 1.6), (1.4, 0.4, 4.0, 22.0, 1.1),
                                             (-1.3, -0.3, 4.6, -18.0, 1.2), (0.4, -1.2, 3.0, 14.0, 0.9))):
        R = G.rz(lean) @ G.rx(6 * (-1) ** k) @ G.ry(45)
        base = np.array((x, 1.0, z))
        B.p("Shard", (w, h, w), base + R @ (0, h / 2, 0), R, VOID[0])
        glow(B, "Shard", (0.16, h * 0.8, 0.16), base + R @ (w / 2 - 0.02, h / 2, 0), R, col=(PURPLE, MAGENTA)[k % 2])
    return B.finish()


def p_tv(sc, parent):
    B = Build(sc, parent, "StaticTV", seed=185)
    B.p("TV", (5.0, 4.0, 3.4), (0.0, 2.4, 0.0), G.rz(4), "6a5a48")
    B.p("TV", (4.0, 3.0, 0.12), (-0.3, 2.45, -1.76), G.rz(4), "4a4e5a", material="SmoothPlastic", shadow=False)
    for k in range(6):
        x = -1.6 + 0.65 * k
        y = 2.0 + 0.9 * ((k * 7) % 3) * 0.4
        B.p("Static", (0.6, 0.5, 0.1), (x, y, -1.84 - 0.005 * k), G.rz(4), (WHITE, "8a90a0", "c8ccd4")[k % 3],
            material="Neon" if k % 2 == 0 else "SmoothPlastic", shadow=False)
    for k in (0, 1):
        B.p("Knob", (0.5, 0.5, 0.2), (2.0, 2.9 - 1.0 * k, -1.86), G.rz(45), "2a2a30")
    for sx in (-1, 1):
        bar(B, "Aerial", (0.2 * sx, 4.3, 0.2), (1.6 * sx, 7.0, 0.6), 0.16 + 0.02 * (sx > 0), "8a90a0")
    B.p("Leg", (4.0, 0.4, 2.6), (0.0, 0.2, 0.0), None, "4a3a2c")
    return B.finish()


def p_pillar(sc, parent):
    B = Build(sc, parent, "BrokenPillar", seed=186)
    B.p("Pillar", (3.0, 0.8, 3.0), (0.0, 0.4, 0.0), None, VOID[2])
    y = 0.8
    for k, (h, dx) in enumerate(((2.6, 0.0), (2.2, 0.7), (2.4, -0.4), (1.8, 0.9))):
        B.p("Pillar", (2.0, h, 2.0), (dx, y + h / 2, 0.06 * k), G.ry(8 * k), VOID[k % 2])
        glow(B, "Seam", (2.06, 0.16, 2.06), (dx, y + h - 0.05, 0.06 * k), G.ry(8 * k), col=(CYAN, MAGENTA)[k % 2])
        y += h + 0.25 * (k % 2)
    B.p("Pillar", (2.0, 1.4, 2.0), (2.4, 0.7, -1.4), ori(8, 30, 12), VOID[1])
    return B.finish()


def p_portal(sc, parent):
    B = Build(sc, parent, "PortalRing", seed=187)
    c = np.array((0.0, 5.2, 0.0))
    for k in range(8):
        a = math.radians(22.5 + 45 * k)
        p = c + (math.cos(a) * 3.7, math.sin(a) * 3.7, 0)
        B.p("Ring", (0.9, 3.2, 0.9 + 0.04 * (k % 2)), p, G.rz(math.degrees(a)), VOID[k % 2 + 1])
    Ra = G.rx(90)
    glow(B, "Swirl", (6.0, 0.14, 6.0), c, Ra, col=PURPLE, flicker=0.15, transparency=0.35, spin=60.0)
    glow(B, "Swirl", (4.0, 0.16, 4.0), c, Ra @ G.ry(45), col=MAGENTA, flicker=0.15, transparency=0.25, spin=60.0)
    B.p("Base", (5.0, 1.2, 2.4), (0.0, 0.6, 0.0), None, VOID[1])
    return B.finish()


def p_bush(sc, parent):
    B = Build(sc, parent, "PixelBush", seed=188)
    for k, (x, y, z, s, col) in enumerate(((0.0, 1.0, 0.0, 2.0, "2a6a4a"), (1.4, 0.8, 0.4, 1.6, "1e5a3a"),
                                            (-1.3, 0.85, -0.2, 1.7, "3a8a5a"), (0.4, 2.2, 0.2, 1.4, "1e5a3a"),
                                            (-0.5, 1.9, 0.9, 1.2, "2a6a4a"), (1.0, 1.6, -1.0, 1.0, "3a8a5a"),
                                            (-1.0, 2.0, -1.0, 0.9, "1e5a3a"), (0.0, 0.5, 1.4, 1.0, "2a6a4a"))):
        B.p("Bush", (s, s, s), (x, y, z), G.ry(5 * k), col)
    glow(B, "Glitch", (0.7, 0.7, 0.7), (1.6, 2.4, -0.4), None, col=MAGENTA)
    glow(B, "Glitch", (0.5, 0.5, 0.5), (-1.7, 1.7, 0.8), None, col=CYAN)
    return B.finish()


AREA = register(Area("Void", "Glitch Void", hero, [
    (p_tree, prop_attrs(6, 0.85, 1.25, "Side", True)),
    (p_cubes, prop_attrs(6, 0.8, 1.3, "Any", False)),
    (p_error, prop_attrs(4, 0.9, 1.2, "Side", False)),
    (p_crystal, prop_attrs(6, 0.8, 1.3, "Side", True)),
    (p_tv, prop_attrs(4, 0.9, 1.2, "Side", True)),
    (p_pillar, prop_attrs(5, 0.9, 1.25, "Side", True)),
    (p_portal, prop_attrs(3, 0.9, 1.2, "Edge", True)),
    (p_bush, prop_attrs(8, 0.8, 1.3, "Any", False)),
], ground="1a1726"))
