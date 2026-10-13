"""Mushroom Marsh: the hero, a giant toadstool house, and the area's props.

The house is a fat cream stem in three eight-sided drums, getting lighter upwards, under a huge red
cap that steps up in three eight-sided layers to a lid, with big white dots on its faces and ledges
and pink gills under its rim. A round wooden door in a dark frame on a plank porch with three steps;
round windows glowing warm; a balcony on two posts over the porch with a lantern hanging under it; a
crooked stone chimney puffing smoke out of the cap. A potato in a little toadstool hat waves from
the porch. Toadstools in red, purple and blue grow at its foot, spore lamps glow by the steps and a
murky pond with lily pads and cattails lies to one side.
"""
import math

import numpy as np

import spsgeo as G
from spsgeo import CF

from .scenery import (Area, Build, INK, bar, grass, ori, potato, prop_attrs, register, round3)

CAP = ("e8403a", "d6352e", "f25a46")
DOT = ("ffffff", "f4eee4")
STEM = ("ecc88c", "f4d8a2", "fbe8c4")
GILL = ("f4c4b4", "e8b0a0")
WOOD = ("6b4226", "9a6238", "c8743a", "a0572b")
STONE = ("8e89a0", "a3a0b8", "b9b4c8")
SMOKE = ("f2f0f8", "e2e0ee", "d2d0e2")
GLOW = "ffd27a"
SPORE = ("6dffc4", "c6ff5a", "8ff0ff")
WATER = ("2b5d73", "24526a", "34708a")
MOSS = ("55b848", "3f9e3c", "6cc04a")
LILY = ("4fa83a", "5dbb46", "3f9a32")
PINK = ("ff8fc7", "ff6fb0", "ffb4dc")
PURPLE = ("8a4ad8", "7a3ac8", "a46bff")
BLUE = ("3b8bff", "2f74e0", "5aa0ff")
REED = ("6e9a3a", "5a8a32", "82b04a")
BROWN = ("7a4a26", "6b4226", "8a5a30")
SKIN = ("d9b07a", "c49a64", "e8c490")
BARK = ("5a4a40", "4a3c34", "6a5a4c")


def facing(n):
    """A turn whose own -Z points along n (horizontal) and whose own Y is up."""
    n = np.asarray(n, float)
    n = n / np.linalg.norm(n)
    z = -n
    y = np.array((0.0, 1.0, 0.0))
    return np.column_stack((np.cross(y, z), y, z))


def octo(B, name, c, w, d, h, cols, solid=False, dh=0.04):
    """An eight-sided drum w along X and d along Z, flat faces square to the axes: two crossing
    blocks and four corner blocks, one on each slanted face. The blocks are a hair different in
    height so no two tops meet."""
    c = np.asarray(c, float)
    t = math.tan(math.radians(22.5))
    fx, fz = w * t, d * t
    cols = tuple(cols) + (cols[-1],) * (3 - len(cols))
    out = [B.p(name, (w, h, fz), c, None, cols[0], solid=solid),
           B.p(name, (fx, h - dh, d), c, None, cols[1], solid=solid)]
    for k, (sx, sz) in enumerate(((1, -1), (-1, -1), (-1, 1), (1, 1))):
        p0 = np.array((sx * w / 2, 0.0, sz * fz / 2))
        p1 = np.array((sx * fx / 2, 0.0, sz * d / 2))
        L = float(np.linalg.norm(p1 - p0))
        u = (p1 - p0) / L
        n = np.array((u[2], 0.0, -u[0]))
        if n @ p0 < 0:
            n = -n
        q = np.array((sx * fx / 2, 0.0, sz * fz / 2))
        T = float(n @ (p0 - q))
        R = np.column_stack((u, (0.0, 1.0, 0.0), np.cross(u, (0.0, 1.0, 0.0))))
        out.append(B.p(name, (L, h - 2 * dh - 0.03 * (k % 2), T), c + (p0 + p1) / 2 - n * T / 2, R, cols[2],
                       solid=solid))
    return out


def facets(w, d):
    """The eight faces of an octo(w, d): [(middle (x, z), outward normal, width)], front first, then
    front-left, left, back-left, back, back-right, right, front-right."""
    t = math.tan(math.radians(22.5))
    fx, fz = w * t, d * t
    out = []
    corners = [(fx / 2, -d / 2), (-fx / 2, -d / 2), (-w / 2, -fz / 2), (-w / 2, fz / 2), (-fx / 2, d / 2),
               (fx / 2, d / 2), (w / 2, fz / 2), (w / 2, -fz / 2)]
    for k in range(8):
        a, b = np.array(corners[k]), np.array(corners[(k + 1) % 8])
        m = (a + b) / 2
        e = b - a
        n = np.array((e[1], -e[0]))
        n /= np.linalg.norm(n)
        if n @ m < 0:
            n = -n
        out.append((m, np.array((n[0], 0.0, n[1])), float(np.linalg.norm(e))))
    return out


def dot(B, c, R, s, name="Dot", t=0.3, cols=DOT):
    """A round white dot on a face whose outward normal is R's -Z: two fat crossing plates a hair
    apart, sunk a little into the face."""
    c = np.asarray(c, float)
    m = c + R @ (0, 0, -t / 2 + 0.05)
    return [B.p(name, (s, s * 0.72, t), m, R, cols[0]),
            B.p(name, (s * 0.72, s, t + 0.06), m, R, cols[1])]


def round_window(B, c, R, d, name="Window"):
    """A round window on a face whose outward normal is R's -Z: a glowing pane (two crossing Neon
    plates and a square core, Folk Valley's round seen face on) in a wooden frame made the same way,
    a cross of bars over it."""
    c = np.asarray(c, float)

    def at(v):
        return c + R @ np.asarray(v, float)
    f = d + 0.9
    fm, pm = at((0, 0, -0.1)), at((0, 0, -0.34))
    neon = dict(material="Neon", lamp=True)
    return [B.p(name, (f, f * 0.6, 0.3), fm, R, WOOD[0]),
            B.p(name, (f * 0.6, f, 0.36), fm, R, WOOD[0]),
            B.p(name, (f * 0.84, f * 0.84, 0.24), fm, R, WOOD[0]),
            B.p(name, (d, d * 0.6, 0.2), pm, R, GLOW, **neon),
            B.p(name, (d * 0.6, d, 0.26), pm, R, GLOW, **neon),
            B.p(name, (d * 0.84, d * 0.84, 0.16), pm, R, GLOW, **neon),
            B.p(name, (0.26, d - 0.14, 0.2), at((0, 0, -0.55)), R, WOOD[0]),
            B.p(name, (d - 0.14, 0.26, 0.26), at((0, 0, -0.55)), R, WOOD[0])]


def toadstool(B, base, h, cw, cols, stem=STEM[1], tilt=(0.0, 0.0), heading=0.0, dots=1, name="Toadstool",
              dot_col=DOT[0], dot_kw=None, lid=False):
    """A toadstool: a stem leaning a little, a cap of two crossing slabs and a block turned 45 (and a
    lid if asked), white dots on its front and top."""
    base = np.asarray(base, float)
    R = ori(tilt[0], heading, tilt[1])
    sw = max(0.36, cw * 0.27)
    out = [B.p(name, (sw, h + 0.1, sw * 1.04), base + R @ (0, h / 2 - 0.05, 0), R, stem)]
    ch = cw * 0.38
    c = base + R @ (0, h + ch * 0.25, 0)
    out.append(B.p(name, (cw, ch * 0.8, cw * 0.64), c, R, cols[0]))
    out.append(B.p(name, (cw * 0.64, ch * 0.76, cw), c, R, cols[1]))
    out.append(B.p(name, (cw * 0.72, ch * 0.72, cw * 0.72), c + R @ (0, ch * 0.13, 0), R @ G.ry(45), cols[2]))
    if lid:
        out.append(B.p(name, (cw * 0.44, ch * 0.3, cw * 0.44), c + R @ (0, ch * 0.62, 0), R @ G.ry(20), cols[1]))
    kw = dict(dot_kw or {})
    ds = cw * 0.2
    spots = [(0.0, -0.02, -cw / 2 - 0.08 + 0.03, "front"), (cw * 0.2, ch * 0.49, cw * 0.12, "top"),
             (-cw * 0.22, ch * 0.49, -cw * 0.1, "top")]
    for k in range(dots):
        x, y, z, kind = spots[k]
        if kind == "front":
            out.append(B.p(name, (ds * 1.4, ds * 1.1, 0.16), c + R @ (x + cw * 0.1, y, z), R, dot_col, **kw))
        else:
            out.append(B.p(name, (ds, 0.14, ds), c + R @ (x, y + 0.07, z), R @ G.ry(30 * k), dot_col, **kw))
    return out


def spore_lamp(B, base, h=6.0, heading=0.0, name="SporeLamp", pods=2, s=1.0):
    """A stalk curling over like a shepherd's crook, a glowing spore pod hanging from the crook and
    smaller ones on short shoots (Neon, Flicker, NightLamp)."""
    base = np.asarray(base, float)
    R = G.ry(heading)
    pts = [base + R @ np.array(p) for p in ((0.0, 0.0, 0.0), (0.25, h * 0.42, 0.0), (0.05, h * 0.78, 0.0),
                                             (0.6, h * 1.0, 0.0), (1.5, h * 1.04, 0.0), (2.0, h * 0.9, 0.0))]
    out = []
    for k in range(len(pts) - 1):
        out.append(bar(B, name, pts[k], pts[k + 1], (0.46 - 0.04 * k) * s, REED[k % 2], t=(0.42 - 0.03 * k) * s,
                       over=0.12))
    tip = pts[-1]
    out.append(B.p(name, (1.1 * s, 1.3 * s, 1.1 * s), tip - (0, 0.85 * s, 0), ori(0, heading + 45, 0), SPORE[0],
                   material="Neon", flicker=0.12, lamp=True))
    out.append(B.p(name, (0.6 * s, 0.6 * s, 0.6 * s), tip - (0, 1.75 * s, 0), ori(0, heading + 20, 0), SPORE[1],
                   material="Neon", flicker=0.12, lamp=True))
    for k in range(pods - 1):
        b0 = pts[1] + R @ np.array((0.0, h * 0.12 * k, 0.0))
        e = b0 + R @ np.array((-1.1, 0.7, 0.3 * (-1) ** k)) * s
        out.append(bar(B, name, b0, e, 0.36 * s, REED[2]))
        out.append(B.p(name, (0.7 * s, 0.8 * s, 0.7 * s), e + (0, -0.35 * s, 0), ori(0, heading + 30 * k, 0), SPORE[2],
                       material="Neon", flicker=0.12, lamp=True))
    return out


def pool(B, c, w, d, heading=0.0, name="Water", cols=WATER, y=0.1):
    """A patch of murky water laid on the ground: two crossing plates and a turned one, a hair apart."""
    c = np.asarray(c, float)
    R = G.ry(heading)
    k = min(w, d) * 0.64
    return [B.p(name, (w, 0.2, d * 0.56), c + (0, y, 0), R, cols[0]),
            B.p(name, (w * 0.56, 0.24, d), c + (0, y + 0.02, 0), R, cols[1]),
            B.p(name, (k, 0.22, k), c + (0, y + 0.01, 0), R @ G.ry(45), cols[2])]


def lily(B, c, s, heading=0.0, name="LilyPad", col=LILY[0]):
    """A lily pad: a flat plate turned, a notch cut (a darker plate) at its edge."""
    c = np.asarray(c, float)
    return [B.p(name, (s, 0.12, s), c, G.ry(heading), col),
            B.p(name, (s * 0.3, 0.1, s * 0.3), c + G.ry(heading) @ (s * 0.36, 0.03, -s * 0.36), G.ry(heading + 45),
                LILY[2])]


def cattails(B, c, n, h=6.0, heading=0.0, name="Cattail", heads=None):
    """A clump of reeds: thin stems leaning a little, brown cattail heads on some, long blades."""
    rng = B.rng
    c = np.asarray(c, float)
    heads = n if heads is None else heads
    out = []
    for k in range(n):
        a = math.radians(heading + 360.0 * k / n + float(rng.uniform(-20, 20)))
        r = 0.35 + 0.25 * (k % 2)
        b = c + (r * math.sin(a), 0.0, -r * math.cos(a))
        hh = h * float(rng.uniform(0.75, 1.05))
        lean = math.radians(float(rng.uniform(4, 12)))
        top = b + (math.sin(a) * math.sin(lean) * hh, hh, -math.cos(a) * math.sin(lean) * hh)
        out.append(bar(B, name, b, top, 0.3, REED[k % 3], t=0.32))
        if k < heads:
            d = (top - b) / np.linalg.norm(top - b)
            hc = top - d * 1.0
            out.append(bar(B, name, hc - d * 0.85, hc + d * 0.85, 0.72, BROWN[k % 3], t=0.74))
    return out


def blades(B, c, n, L=4.5, heading=0.0, name="Reed", cols=REED, w=0.55, rise=(62, 80)):
    """Long flat blades rising out of a point and leaning out."""
    rng = B.rng
    c = np.asarray(c, float)
    out = []
    for k in range(n):
        a = math.radians(heading + 360.0 * k / n + float(rng.uniform(-15, 15)))
        r = math.radians(float(rng.uniform(*rise)))
        d = np.array((math.sin(a) * math.cos(r), math.sin(r), -math.cos(a) * math.cos(r)))
        LL = L * float(rng.uniform(0.8, 1.1))
        out.append(bar(B, name, c, c + d * LL, w, cols[k % len(cols)], t=0.14 + 0.02 * (k % 2),
                       n=(math.cos(a), 0.0, math.sin(a))))
    return out


# ==================================================================== the hero

def hero(sc, parent):
    B = Build(sc, parent, "Marsh", seed=301)
    cz = 3.0                                                    # the stem's middle
    # the stem: three eight-sided drums, lighter upwards
    octo(B, "Stem", (0.0, 1.1, cz), 18.0, 18.0, 2.2, (STEM[0], STEM[0], STEM[1]), solid=True)
    octo(B, "Stem", (0.0, 6.7, cz), 16.0, 16.0, 9.0, (STEM[1], STEM[1], STEM[0]), solid=True)
    octo(B, "Stem", (0.0, 15.4, cz), 14.6, 14.6, 8.4, (STEM[2], STEM[2], STEM[1]), solid=True)
    # the cap: three eight-sided layers stepping in, a lid, white dots on the faces and ledges
    layers = ((34.0, 29.4, 3.2), (27.6, 23.8, 3.4), (20.4, 17.6, 3.0))
    y = 19.4
    ys = []
    for k, (w, d, h) in enumerate(layers):
        octo(B, "Cap", (0.0, y + h / 2, 0.0), w, d, h, (CAP[k % 2], CAP[(k + 1) % 2], CAP[2]))
        ys.append(y + h / 2)
        y += h - 0.2
    lid_y = y
    B.p("Cap", (12.0, 1.5, 5.0), (0.0, lid_y + 0.75, 0.0), None, CAP[2])
    B.p("Cap", (5.0, 1.46, 10.4), (0.0, lid_y + 0.75, 0.0), None, CAP[0])
    B.p("Cap", (7.6, 1.4, 7.6), (0.0, lid_y + 0.75, 0.0), G.ry(45), CAP[1])
    # dots on the faces: (layer, face, along, up, size); faces 0 front, 1 front-left, 2 left, 7 front-right, 6 right
    spots = ((0, 0, -3.4, 0.1, 2.5), (0, 0, 3.6, -0.15, 2.3), (0, 1, 0.6, 0.0, 2.4), (0, 7, -0.4, 0.1, 2.5),
             (0, 2, -1.2, 0.0, 2.3), (0, 6, 1.0, 0.0, 2.3), (1, 0, 0.6, 0.05, 2.3), (1, 1, -1.4, 0.0, 2.1),
             (1, 7, 1.8, -0.05, 2.1), (2, 0, -1.0, 0.0, 2.0), (2, 7, 0.4, 0.0, 1.9))
    for li, fi, along, up, s in spots:
        w, d, h = layers[li]
        m, n, _wid = facets(w, d)[fi]
        R = facing(n)
        c = np.array((m[0], ys[li] + up, m[1])) + R @ (along, 0, 0)
        dot(B, c, R, s)
    for k, (x, z, s, yy) in enumerate(((10.9, -9.6, 2.2, 0), (-11.6, -8.4, 2.0, 0), (-3.0, -11.3, 1.9, 0),
                                       (8.0, -7.6, 1.8, 1), (-7.4, -7.2, 1.7, 1), (2.6, -3.6, 1.8, 2))):
        top = ys[yy] + layers[yy][2] / 2
        B.p("Dot", (s, 0.2, s * 0.9), (x, top + 0.08, z), G.ry(20 + 35 * k), DOT[k % 2])
    # pink gills under the rim
    gy = 19.4 - 0.18
    B.p("Gills", (27.0, 0.3, 10.6), (0.0, gy, 0.0), None, GILL[0])
    B.p("Gills", (11.2, 0.34, 23.4), (0.0, gy, 0.0), None, GILL[0])
    B.p("Gills", (17.4, 0.32, 17.4), (0.0, gy, 0.0), G.ry(45), GILL[1])
    for k in range(6):
        a = math.radians(-112.5 + 45 * k)
        dr = np.array((math.sin(a), 0.0, -math.cos(a)))
        bar(B, "Gills", np.array((0.0, gy - 0.3, cz * 0.4)) + dr * 7.0, np.array((0.0, gy - 0.3, 0.0)) + dr * 12.6, 0.5,
            GILL[1], t=0.36, n=(0, 1, 0))
    # the chimney through the cap, smoke puffing out of it
    B.p("Chimney", (2.4, 6.6, 2.4), (8.6, 29.6, 0.6), ori(0, 12, -6), STONE[0])
    B.p("Chimney", (3.0, 0.7, 3.0), (8.95, 32.9, 0.6), ori(0, 12, -6), STONE[2])
    for k, (dx, dy, s) in enumerate(((0.4, 34.1, 1.9), (1.6, 35.4, 2.4), (3.1, 36.6, 1.8))):
        B.p("Smoke", (s, s * 0.9, s), (9.0 + dx, dy, 0.6 - 0.3 * k), ori(14, 25 * k + 10, 12), SMOKE[k % 3])
    # the round door in its frame
    zf = cz - 8.0
    dy = 4.6
    for k, (sx, sy, t, col) in enumerate(((6.2, 3.7, 0.24, WOOD[0]), (3.7, 6.2, 0.28, WOOD[0]))):
        B.p("DoorFrame", (sx, sy, t), (0.0, dy, zf - 0.08), None, col)
    B.p("DoorFrame", (5.2, 5.14, 0.2), (0.0, dy + 0.03, zf - 0.08), None, WOOD[0])
    for k, (sx, sy, t) in enumerate(((5.0, 3.0, 0.3), (3.0, 5.0, 0.36), (4.2, 4.2, 0.26))):
        B.p("Door", (sx, sy, t), (0.0, dy, zf - 0.3), None, (WOOD[1], WOOD[1], WOOD[1])[k])
    for sx in (-1, 1):
        B.p("Door", (0.16, 4.2, 0.12), (sx * 0.85, dy - 0.2, zf - 0.54), None, WOOD[0])
    B.p("Door", (0.5, 0.5, 0.3), (1.45, dy - 0.1, zf - 0.62), G.rz(45), "f5c518")
    B.p("Door", (0.9, 0.9, 0.12), (0.0, dy + 1.5, zf - 0.56), G.rz(45), GLOW, material="Neon", lamp=True)
    # the porch: a plank deck on a base, three stone steps
    B.p("Porch", (12.0, 2.0, 4.6), (0.0, 1.0, zf - 1.8), None, WOOD[0], solid=True)
    for k in range(3):
        B.p("Porch", (12.4, 0.3 + 0.04 * (k % 2), 1.54), (0.0, 2.15 + 0.01 * (k % 2), zf - 3.62 + 1.55 * k), None,
            WOOD[1 + k % 2], solid=True)
    rise = 2.26 / 3
    for k in range(3):
        z0 = zf - 4.1 - 3.6 + 1.2 * k
        B.p("Step", (6.0 - 0.04 * (k % 2), rise, zf - 4.1 - z0), (0.0, rise * (k + 0.5), (z0 + zf - 4.1) / 2), None,
            STONE[1 + k % 2], solid=True)
    B.p("Path", (3.0, 0.2, 1.8), (0.4, 0.1, zf - 9.0), G.ry(6), "c9ae78")
    B.p("Path", (2.5, 0.3, 1.3), (0.4, 0.15, zf - 9.0), G.ry(6), "f3e2b6")
    # the balcony over the porch on two posts, a railing, a lantern hanging under it
    by = 11.6
    B.p("Balcony", (11.4, 0.5, 6.3), (0.0, by - 0.25, zf - 2.9 + 3.15), None, WOOD[1], solid=True)
    bz = zf - 2.75
    for sx in (-1, 1):
        B.p("Post", (0.7, by - 0.5 - 2.3, 0.7), (sx * 5.05, 2.3 + (by - 0.5 - 2.3) / 2, bz + 0.3), None, WOOD[3])
        B.p("Railing", (0.4, 6.0, 0.36), (sx * 5.5, by + 2.1, bz + 3.0), G.rx(90), WOOD[2])
    for x in (-5.5, -1.9, 1.9, 5.5):
        B.p("Railing", (0.42, 2.24, 0.42), (x, by + 1.12, bz + 0.1), None, WOOD[3])
    B.p("Railing", (11.6, 0.4, 0.44), (0.0, by + 2.1, bz + 0.1), None, WOOD[2])
    B.p("Railing", (11.4, 0.3, 0.3), (0.0, by + 1.0, bz + 0.1), None, WOOD[1])
    B.p("Lantern", (0.16, 0.8, 0.16), (3.0, by - 0.9, bz + 0.9), None, INK)
    B.p("Lantern", (1.2, 0.3, 1.2), (3.0, by - 1.42, bz + 0.9), G.ry(45), INK)
    B.p("Lantern", (0.95, 1.2, 0.95), (3.0, by - 2.17, bz + 0.9), None, GLOW, material="Neon", flicker=0.1, lamp=True)
    # round windows: two on the lower drum's slanted faces, one upstairs over the balcony
    for sx in (-1, 1):
        n = np.array((sx * 0.7071, 0.0, -0.7071))
        round_window(B, np.array((0.0, 6.6, cz)) + n * 8.0, facing(n), 3.2)
    round_window(B, (0.0, 16.0, cz - 7.3), np.eye(3), 3.6)
    # the potato at the door, in a little toadstool hat, waving
    s = 3.3
    pc = np.array((-3.15, 2.3 + s / 2, zf - 2.2))
    potato(B, pc, s, SKIN, name="Potato", glints=True, cheeks="ff9aa8")
    bar(B, "Potato", pc + (-s * 0.38, -0.1, 0.0), pc + (-s * 0.62, s * 0.42, -0.25), 0.62, SKIN[1])
    B.p("Potato", (2.9, 0.75, 2.6), pc + (0.0, s * 0.5 + 0.3, 0.0), ori(0, 10, -6), CAP[0])
    B.p("Potato", (1.8, 0.6, 1.7), pc + (-0.05, s * 0.5 + 0.85, 0.0), ori(0, 40, -6), CAP[2])
    B.p("Potato", (0.6, 0.45, 0.16), pc + (0.55, s * 0.5 + 0.3, -1.36), ori(0, 10, -6), DOT[0])
    # toadstools at its foot
    toadstool(B, (-8.8, 0.0, -9.4), 3.4, 3.6, CAP, tilt=(-6, 4), heading=10)
    toadstool(B, (9.6, 0.0, -9.2), 4.6, 4.4, PURPLE, stem="eee4fa", tilt=(-4, -6), heading=-15, dot_col="e6d4ff")
    for k, (x, z, w, d, h) in enumerate(((-7.6, -6.4, 3.4, 2.2, 20), (8.4, -5.6, 2.8, 2.0, -25))):
        B.p("Moss", (w, 0.3 + 0.04 * k, d), (x, 0.15, z), G.ry(h), MOSS[k % 2])
        grass(B, (x + 0.6 * (-1) ** k, 0.2, z - 0.3), 3, MOSS, h=(1.2, 2.0), r=0.6)
    toadstool(B, (16.4, 0.0, -2.0), 7.0, 5.6, BLUE, stem="e4eefc", tilt=(-3, -7), heading=-25, dots=2,
              dot_col="8ff0ff", dot_kw=dict(material="Neon", lamp=True), lid=True)
    toadstool(B, (-14.4, 0.0, 1.0), 6.0, 5.0, PURPLE, stem="eee4fa", tilt=(-4, 6), heading=20, dots=2, lid=True,
              dot_col="e6d4ff")
    # spore lamps by the steps
    spore_lamp(B, (5.6, 0.0, -12.6), 6.4, heading=-20, s=1.15)
    spore_lamp(B, (-6.2, 0.0, -12.0), 5.2, heading=200, pods=1, s=1.1)
    # the murky pond: lily pads and a pink bud, cattails at its edge
    pool(B, (-16.4, 0.0, -9.0), 8.6, 7.0, heading=8)
    lily(B, (-18.0, 0.28, -10.2), 1.9, heading=20)
    lily(B, (-14.6, 0.29, -7.6), 1.5, heading=60, col=LILY[1])
    B.p("Bud", (0.6, 0.6, 0.6), (-17.6, 0.62, -9.8), ori(0, 45, 0), PINK[0])
    cattails(B, (-20.2, 0.0, -6.0), 4, h=5.6, heading=30, heads=3)
    return B.finish()


# ==================================================================== props

def p_toadstool(sc, parent):
    B = Build(sc, parent, "GiantToadstool", seed=311)
    B.p("Moss", (3.6, 0.5, 3.2), (0.0, 0.25, 0.0), G.ry(15), MOSS[1])
    B.p("Moss", (2.4, 0.42, 2.8), (0.5, 0.45, 0.3), G.ry(55), MOSS[0])
    y = 0.4
    for k, (w, h) in enumerate(((2.4, 3.8), (2.1, 3.6), (1.9, 3.2))):
        R = ori(3 * (-1) ** k, 15 + 40 * k, 2.5 * (-1) ** (k + 1))
        B.p("Stem", (w, h + 0.1, w), (0.22 * k, y + h / 2, -0.1 * k), R, STEM[k % 3])
        y += h
    B.p("Stem", (3.4, 0.45, 3.4), (0.45, y - 1.5, -0.2), G.ry(45), STEM[2])
    # the cap, tipped a little: two eight-sided layers and a lid, dots on its faces and on top
    with B.at(CF(np.array((0.5, y + 0.8, -0.2)), ori(5, 20, -4))):
        octo(B, "Cap", (0.0, 0.0, 0.0), 9.8, 9.4, 2.4, (CAP[0], CAP[1], CAP[2]))
        octo(B, "Cap", (0.0, 1.75, 0.0), 6.8, 6.6, 1.5, (CAP[2], CAP[0], CAP[1]))
        B.p("Cap", (3.4, 0.7, 3.3), (0.0, 2.75, 0.0), G.ry(22.5), CAP[1])
        B.p("Gills", (7.6, 0.24, 7.2), (0.0, -1.28, 0.0), None, GILL[0])
        for fi, along, up, sz in ((0, -0.5, 0.0, 2.1), (1, 0.3, 0.05, 1.6), (7, -0.2, -0.05, 1.5), (2, 0.4, 0.0, 1.5),
                                  (6, -0.6, 0.0, 1.4)):
            m, n, _w = facets(9.8, 9.4)[fi]
            R = facing(n)
            dot(B, np.array((m[0], up, m[1])) + R @ (along, 0, 0), R, sz)
        for k, (x, yy, z) in enumerate(((3.5, 1.2, -2.2), (-3.5, 1.2, 2.2), (-0.3, 3.1, 0.4))):
            B.p("Dot", (1.0, 0.2, 1.0), (x, yy + 0.08, z), G.ry(25 * k), DOT[k % 2])
    grass(B, (-1.4, 0.4, -1.3), 3, MOSS, h=(0.9, 1.5), r=0.5)
    return B.finish()


def p_purple(sc, parent):
    B = Build(sc, parent, "PurpleShroom", seed=312)
    B.p("Moss", (3.2, 0.45, 3.0), (0.0, 0.22, 0.0), G.ry(30), MOSS[1])
    pts = [np.array(p) for p in ((0.0, 0.2, 0.0), (0.3, 3.4, 0.0), (1.2, 6.6, -0.2), (2.4, 9.4, -0.3),
                                 (3.0, 11.6, -0.3))]
    for k in range(4):
        bar(B, "Stem", pts[k], pts[k + 1], 1.7 - 0.12 * k, ("eee4fa", "e2d4f4")[k % 2], over=0.25)
    c = pts[-1] + (0, 0.7, 0)
    R = ori(-4, 10, -7)
    B.p("Cap", (11.0, 1.4, 7.0), c, R, PURPLE[0])
    B.p("Cap", (7.0, 1.36, 11.0), c, R, PURPLE[1])
    B.p("Cap", (8.2, 1.3, 8.2), c + R @ (0, 0.06, 0), R @ G.ry(45), PURPLE[2])
    B.p("Cap", (5.6, 0.9, 5.6), c + R @ (0, 1.1, 0), R @ G.ry(22), PURPLE[0])
    B.p("Cap", (2.2, 0.8, 2.2), c + R @ (0, 1.9, 0), R @ G.ry(10), PURPLE[2])
    B.p("Glow", (8.6, 0.2, 8.6), c + R @ (0, -0.8, 0), R @ G.ry(45), "e0b4ff", material="Neon", lamp=True)
    B.p("Glow", (7.8, 0.26, 7.8), c + R @ (0, -0.8, 0), R, "d49cff", material="Neon", lamp=True)
    for k, (x, z, s) in enumerate(((-3.4, -1.0, 1.3), (2.6, -2.4, 1.1), (1.0, 2.8, 1.2), (-1.6, 2.2, 0.9),
                                   (3.6, 0.9, 0.9))):
        inner = abs(x) < 2.7 and abs(z) < 2.7
        B.p("Spot", (s, 0.2, s), c + R @ (x, 1.64 if inner else 0.8, z), R @ G.ry(30 * k), "e6d4ff")
    toadstool(B, (-1.9, 0.3, -1.4), 1.6, 2.0, PURPLE, stem="eee4fa", tilt=(-6, 10), heading=30, dot_col="e6d4ff")
    return B.finish()


def p_blue(sc, parent):
    B = Build(sc, parent, "BlueShrooms", seed=313)
    B.p("Moss", (4.4, 0.45, 3.4), (0.0, 0.22, 0.0), G.ry(-10), MOSS[1])
    B.p("Moss", (2.6, 0.4, 2.4), (-1.0, 0.45, 0.4), G.ry(30), MOSS[2])
    neon = dict(material="Neon", lamp=True, flicker=0.06)
    toadstool(B, (0.8, 0.3, 0.3), 9.0, 6.4, BLUE, stem="e4eefc", tilt=(-3, -8), heading=-10, dots=3, lid=True,
              dot_col="8ff0ff", dot_kw=neon)
    toadstool(B, (-1.6, 0.3, -0.5), 5.4, 4.4, BLUE, stem="dce8f8", tilt=(4, 12), heading=25, dots=3, lid=True,
              dot_col="8ff0ff", dot_kw=neon)
    toadstool(B, (1.9, 0.3, -1.7), 1.4, 1.5, BLUE, stem="dce8f8", tilt=(-8, -6), heading=60, dots=0)
    toadstool(B, (-2.4, 0.3, 1.3), 1.1, 1.2, BLUE, stem="dce8f8", tilt=(6, 8), heading=10, dots=0)
    grass(B, (0.2, 0.4, -1.6), 3, MOSS, h=(0.8, 1.3), r=0.6)
    return B.finish()


def p_ring(sc, parent):
    B = Build(sc, parent, "FairyRing", seed=314)
    caps = (CAP, ("f4ecd8", "e8dcc4", "fff8ea"), PURPLE, ("ff9f3d", "f07412", "ffb45a"))
    for k in range(9):
        a = math.radians(40 * k + float(B.rng.uniform(-8, 8)))
        r = 3.2 + float(B.rng.uniform(-0.3, 0.3))
        h = float(B.rng.uniform(0.7, 1.5))
        cw = float(B.rng.uniform(0.9, 1.5))
        p = np.array((math.sin(a) * r, 0.0, -math.cos(a) * r))
        R = ori(float(B.rng.uniform(-10, 10)), 40 * k, float(B.rng.uniform(-10, 10)))
        col = caps[k % 4]
        B.p("Stem", (0.36, h, 0.36), p + R @ (0, h / 2, 0), R, STEM[1 + k % 2])
        B.p("Cap", (cw, cw * 0.4, cw), p + R @ (0, h + cw * 0.12, 0), R @ G.ry(45 * (k % 2)), col[k % 2])
    for k in range(4):
        a = math.radians(45 * k + 22.5)
        B.p("Grass", (6.6, 0.14 + 0.02 * k, 0.9), (0.0, 0.07 + 0.01 * k, 0.0), G.ry(math.degrees(a)), MOSS[2] if k % 2
            else MOSS[0])
    B.p("Sparkle", (0.5, 0.5, 0.5), (0.3, 1.6, -0.2), ori(35.26, 45, 0), SPORE[1], material="Neon", flicker=0.25,
        lamp=True)
    B.p("Sparkle", (0.36, 0.36, 0.36), (-0.6, 2.3, 0.5), ori(35.26, 20, 0), SPORE[2], material="Neon", flicker=0.25,
        lamp=True)
    return B.finish()


def p_lily(sc, parent):
    B = Build(sc, parent, "LilyPads", seed=315)
    pool(B, (0.0, 0.0, 0.0), 8.4, 6.4, heading=10)
    for k, (x, z, s, h) in enumerate(((-1.8, -0.8, 2.2, 20), (1.6, 0.9, 1.8, 70), (2.2, -1.6, 1.3, 10),
                                      (-0.6, 1.9, 1.4, 45))):
        lily(B, (x, 0.28 + 0.01 * k, z), s, heading=h, col=LILY[k % 2])
    fc = np.array((-1.9, 0.4, -0.9))
    for k in range(4):
        a = math.radians(90 * k + 20)
        B.p("Flower", (0.7, 0.36, 0.42), fc + (math.sin(a) * 0.42, 0.18, -math.cos(a) * 0.42),
            G.ry(-90 * k - 20) @ G.rx(25), PINK[k % 2])
    B.p("Flower", (0.42, 0.4, 0.42), fc + (0, 0.32, 0), G.ry(45), "ffd23f")
    B.p("Bud", (0.6, 0.7, 0.6), (1.7, 0.7, 0.8), ori(0, 45, 8), PINK[2])
    blades(B, (3.4, 0.1, 1.6), 3, L=2.6, heading=40, w=0.4)
    fly = np.array((0.4, 2.2, -1.0))
    B.p("Dragonfly", (1.3, 0.22, 0.24), fly, G.ry(20), BLUE[0])
    for sx in (-1, 1):
        B.p("Dragonfly", (0.3, 0.06, 1.0), fly + G.ry(20) @ (0.2 * sx, 0.12, 0.0), G.ry(20) @ G.rx(8 * sx), "dff6ff")
    return B.finish()


def p_cattails(sc, parent):
    B = Build(sc, parent, "Cattails", seed=316)
    B.p("Mud", (3.0, 0.4, 2.6), (0.0, 0.2, 0.0), G.ry(20), MOSS[1])
    B.p("Mud", (2.0, 0.36, 2.2), (0.6, 0.38, 0.3), G.ry(60), MOSS[0])
    cattails(B, (0.0, 0.3, 0.0), 6, h=6.4, heading=10, heads=4)
    blades(B, (0.2, 0.4, 0.0), 6, L=4.4, heading=25)
    return B.finish()


def p_log(sc, parent):
    B = Build(sc, parent, "MossyLog", seed=317)
    R = G.ry(-6)
    c = np.array((0.0, 1.15, 0.0))
    B.p("Log", (9.0, 2.3, 2.3), c, R, BROWN[1])
    B.p("Log", (8.9, 2.3, 2.3), c, R @ G.rx(45), BROWN[0])
    for sx in (-1, 1):
        e = c + R @ (sx * 4.5, 0, 0)
        B.p("Log", (0.1, 1.8, 1.8), e + R @ (sx * 0.04, 0, 0), R, "d8b07a", shadow=False)
        B.p("Log", (0.1, 1.8, 1.8), e + R @ (sx * 0.05, 0, 0), R @ G.rx(45), "c8a070", shadow=False)
    B.p("Log", (0.12, 0.9, 0.9), c + R @ (-4.58, 0, 0), R @ G.rx(45), "3a2a1e", shadow=False)
    for k, (x, w, d) in enumerate(((-2.0, 3.6, 2.0), (1.4, 2.8, 1.8), (3.1, 1.6, 1.5))):
        B.p("Moss", (w, 0.3 + 0.03 * k, d), c + R @ (x, 1.47 + 0.02 * k, 0.1 * (-1) ** k), R @ G.ry(5 * (-1) ** k),
            MOSS[k % 3])
    for k, (x, y, s, col) in enumerate(((-0.6, 0.3, 1.6, "ff9f3d"), (0.5, -0.4, 1.3, "f4d8a0"),
                                        (2.4, 0.1, 1.1, "ffb45a"))):
        B.p("Fungus", (s, 0.26, s * 0.62), c + R @ (x, y, -1.55), R @ G.rz(4 * (-1) ** k), col)
    bar(B, "Log", c + R @ (1.0, 0.8, 0.4), c + R @ (2.2, 2.9, 1.1), 0.75, BROWN[2])
    toadstool(B, c + R @ (-3.2, 1.6, 0.3), 0.9, 1.3, BLUE, stem="dce8f8", tilt=(-6, 8), heading=20, dots=0)
    toadstool(B, c + R @ (-2.4, 1.62, -0.4), 0.6, 0.9, BLUE, stem="dce8f8", tilt=(8, -6), heading=50, dots=0)
    blades(B, (4.6, 0.1, 1.2), 3, L=2.2, heading=140, cols=MOSS, w=0.5, rise=(30, 50))
    return B.finish()


def p_lamp(sc, parent):
    B = Build(sc, parent, "SporeLamp", seed=318)
    B.p("Moss", (2.6, 0.5, 2.4), (0.0, 0.25, 0.0), G.ry(20), MOSS[1])
    B.p("Moss", (1.7, 0.42, 1.8), (-0.5, 0.5, 0.4), G.ry(60), MOSS[0])
    spore_lamp(B, (0.0, 0.4, 0.0), 7.6, heading=0.0, pods=3, s=1.35)
    for k, (y, a) in enumerate(((2.6, 30.0), (4.2, 210.0))):
        d = np.array((math.sin(math.radians(a)), 0.25, -math.cos(math.radians(a))))
        bar(B, "Leaf", np.array((0.2, y, 0.0)), np.array((0.2, y, 0.0)) + d * 1.8, 0.9, MOSS[k % 2], t=0.14,
            n=(0, 1, 0))
    blades(B, (0.4, 0.5, -0.6), 3, L=1.8, heading=-30, cols=MOSS, w=0.4)
    return B.finish()


def p_frog(sc, parent):
    B = Build(sc, parent, "FrogStatue", seed=319)
    jade = ("4fa86a", "3f9a5c", "62bc7c")
    # the stump: round, cut rings on top, roots
    round3(B, "Stump", (0.0, 1.3, 0.0), 4.2, 2.6, 4.0, (BROWN[0], BROWN[1], BROWN[2]))
    B.p("Stump", (3.4, 0.14, 3.2), (0.0, 2.65, 0.0), None, "d8b07a")
    B.p("Stump", (2.4, 0.16, 2.4), (0.0, 2.67, 0.0), G.ry(45), "c8a070")
    for k in range(3):
        a = math.radians(120 * k + 30)
        bar(B, "Stump", (math.sin(a) * 1.6, 1.2, -math.cos(a) * 1.6), (math.sin(a) * 2.8, 0.15, -math.cos(a) * 2.8),
            0.7, BROWN[k % 2])
    # the frog: a round body, eyes on top, a wide smile, legs folded at its sides
    c = np.array((0.0, 3.85, 0.1))
    round3(B, "Frog", c, 3.4, 2.4, 3.0, jade)
    for sx in (-1, 1):
        e = c + (sx * 0.85, 1.25, -0.7)
        B.p("Frog", (1.1, 1.0, 1.0), e, G.ry(10 * sx), jade[2])
        B.p("Eye", (0.7, 0.7, 0.1), e + (0, 0.05, -0.55), G.ry(10 * sx), "ffffff", material="SmoothPlastic",
            shadow=False)
        B.p("Eye", (0.32, 0.4, 0.1), e + (0, 0.02, -0.62), G.ry(10 * sx), INK, material="SmoothPlastic", shadow=False)
        B.p("Cheek", (0.5, 0.26, 0.1), c + (sx * 1.05, 0.15, -1.53), None, "ff9aa8", material="SmoothPlastic",
            shadow=False)
        B.p("Leg", (1.0, 1.2, 2.16), c + (sx * 1.75, -0.5, 0.4), G.rz(sx * 12), jade[1])
        B.p("Leg", (0.8, 0.9, 1.0), c + (sx * 0.9, -0.85, -1.4), None, jade[0])
    B.p("Mouth", (2.0, 0.22, 0.1), c + (0, -0.15, -1.53), None, INK, material="SmoothPlastic", shadow=False)
    B.p("Crown", (1.5, 0.5, 1.3), c + (0, 1.35, 0.5), G.ry(10), "f5c518")
    for k in range(3):
        B.p("Crown", (0.36, 0.5, 0.36), c + (-0.5 + 0.5 * k, 1.8, 0.0), G.ry(45), ("ffd447", "e0a800")[k % 2])
    B.p("Crown", (0.3, 0.3, 0.12), c + (0.0, 1.38, -0.18), G.rz(45), "ff3b5c", material="Neon", lamp=True)
    return B.finish()


def p_moss(sc, parent):
    B = Build(sc, parent, "HangingMoss", seed=320)
    B.p("Roots", (3.0, 0.5, 2.6), (0.0, 0.25, 0.0), G.ry(25), BARK[1])
    pts = [np.array(p) for p in ((0.0, 0.3, 0.0), (0.4, 3.6, 0.1), (0.2, 6.6, -0.1), (1.4, 8.8, -0.2),
                                 (3.8, 9.8, -0.3), (6.4, 9.4, -0.3), (7.8, 8.2, -0.2))]
    for k in range(6):
        bar(B, "Branch", pts[k], pts[k + 1], 1.7 - 0.2 * k, BARK[k % 3], over=0.2)
    bar(B, "Branch", pts[2] + (0, 0.4, 0), pts[2] + (-1.8, 2.6, 0.2), 0.6, BARK[2])
    for k, (t, L) in enumerate(((0.15, 2.4), (0.45, 3.4), (0.7, 2.0), (0.9, 3.0))):
        i = 3 + int(t * 3)
        p = pts[i] + (pts[i + 1] - pts[i]) * ((t * 3) % 1.0) - (0, 0.3, 0)
        bar(B, "Moss", p, p - (0.2 * (-1) ** k, L, 0.1), 0.5 + 0.05 * (k % 2), ("a8c48a", "8fb070", "c0d8a0")[k % 3],
            t=0.3 + 0.02 * k)
        B.p("Moss", (0.9, 0.8, 0.5), p - (0.2 * (-1) ** k, L, 0.1), ori(0, 20 * k, 15 * (-1) ** k),
            ("8fb070", "c0d8a0", "a8c48a")[k % 3])
    for k, (i, w) in enumerate(((3, 1.6), (4, 2.0), (5, 1.4))):
        B.p("Moss", (w, 0.5, 1.4), (pts[i] + pts[i + 1]) / 2 + (0, 0.65, 0), ori(0, 10 * k, 8 * (-1) ** k),
            MOSS[k % 3])
    blades(B, (0.6, 0.4, -1.0), 3, L=1.8, heading=-20, cols=MOSS, w=0.45)
    return B.finish()


AREA = register(Area("Marsh", "Mushroom Marsh", hero, [
    (p_toadstool, prop_attrs(5, 0.85, 1.25, "Side", False)),
    (p_purple, prop_attrs(4, 0.85, 1.2, "Side", False)),
    (p_blue, prop_attrs(5, 0.85, 1.25, "Side", False)),
    (p_ring, prop_attrs(6, 0.8, 1.3, "Any", False)),
    (p_lily, prop_attrs(6, 0.8, 1.3, "Any", False)),
    (p_cattails, prop_attrs(8, 0.8, 1.3, "Side", False)),
    (p_log, prop_attrs(4, 0.9, 1.2, "Side", True)),
    (p_lamp, prop_attrs(6, 0.9, 1.2, "Side", False)),
    (p_frog, prop_attrs(3, 0.9, 1.2, "Side", True)),
    (p_moss, prop_attrs(4, 0.9, 1.2, "Edge", False)),
], ground="2c7a6a"))
