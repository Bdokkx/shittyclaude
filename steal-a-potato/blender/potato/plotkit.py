"""4.2, the plot kit in bricks: PotatoKit.Fences (four tiers), Soil, UpgradeBoard, Mound, Seeds.

Every piece is a Model built at the origin. Its pivot is where the game puts it: the ground under
a post, the middle of a rail on the ground, the top centre of the soil and the mound, the bottom
of a seed. All decoration: anchored, CanCollide / CanTouch / CanQuery off, no shadow under 2.5.

Fences, in Folk Valley's idiom (posts 0.8-1.0 square on a wider plinth, rails 0.4-0.55 square),
each tier clearly richer than the one before:
  Fence_Wood     dark posts, bright wood rails
  Fence_Gold     gold posts with cream bands and round gold knobs, gold rails with a cream strip
  Fence_Diamond  white posts with cyan bands, a Neon jewel on each post, cyan rails, little
                 diamonds between the rails
  Fence_Rainbow  dark posts with a Neon star on each, Neon rails (the game cycles their colour)
"""
import math

import numpy as np

import spsgeo as G
from spsgeo import CF

from . import scenery as SC
from .bricks import Bricks, hexc, ori, shade

POST_H = 4.4
SPAN = 7.0
TINT = "ececE8"            # seed bodies: light grey, tinted by the game

TIERS = {
    "Fence_Wood": dict(plinth="5a3a22", post="6b4226", cap="9a6238", band=None, top="c8743a", rail="c8743a",
                       rail2="a0572b", pw=0.8, rw=0.5, header="c8743a", board="22232b", trim="9a6238"),
    "Fence_Gold": dict(plinth="b8860b", post="e0a800", cap="ffd447", band="fff1c1", top="ffe58a", rail="ffc72c",
                       rail2="f5b700", pw=0.95, rw=0.55, header="ffd447", board="22232b", trim="fff1c1"),
    "Fence_Diamond": dict(plinth="b9c6dc", post="f4f8ff", cap="dff6ff", band="7fe3ff", top="6ff3ff", rail="4fc3f7",
                          rail2="dff6ff", pw=0.95, rw=0.55, header="7fe3ff", board="1d2433", trim="4fc3f7"),
    "Fence_Rainbow": dict(plinth="1e1a2e", post="2b2233", cap="4a3b5c", band="3f3250", top="ffe14d", rail="ff4d6d",
                          rail2="4da6ff", pw=0.95, rw=0.55, header="2b2233", board="15121c", trim="3f3250"),
}
TIER_ORDER = ("Fence_Wood", "Fence_Gold", "Fence_Diamond", "Fence_Rainbow")
RAINBOW = ("ff4d6d", "ff9f3d", "ffe14d", "5ee06a", "4da6ff", "a46bff")


def deco(sc, base=None):
    return Bricks(sc, base, anchored=True, collide=False, touch=False, query=False, massless=False)


def finish(m, primary, pivot_world):
    """PrimaryPart and its PivotOffset so the Model's pivot is pivot_world."""
    m.p["primary"] = primary
    primary.p["pivot"] = primary.p["cf"].inv() * pivot_world
    return m


# ---------------------------------------------------------------- toppers

def round_knob(b, m, c, s, cols, name="Knob"):
    """Folk Valley's round: two crossing blocks, one turned 45 degrees, a lid."""
    c = np.asarray(c, float)
    out = [b.part(m, name, (s, s * 0.8, s * 0.6), c, None, cols[0]),
           b.part(m, name, (s * 0.6, s * 0.84, s), c, None, cols[0]),
           b.part(m, name, (s * 0.82, s * 0.66, s * 0.82), c, G.ry(45), cols[1]),
           b.part(m, name, (s * 0.5, s * 0.16, s * 0.5), c + (0, s * 0.45, 0), None, cols[2])]
    return out


def jewel(b, m, c, s, col, name="Jewel"):
    """A cut gem standing on its point: a cube turned 45 about Y and tipped 35 to sit on a corner."""
    return b.part(m, name, (s, s, s), np.asarray(c, float), ori(35.26, 45, 0), col, material="Neon")


def star(b, m, c, r, col, name="Star", material="Neon", R=None):
    """A five-point star facing -Z: five rays round a centre block."""
    R = np.eye(3) if R is None else R
    c = np.asarray(c, float)
    out = [b.part(m, name, (r * 0.62, r * 0.62, 0.3), c, R @ G.rz(45), col, material=material)]
    for i in range(5):
        a = i * 72.0
        Rr = R @ G.rz(a)
        out.append(b.part(m, name, (r * 0.36, r, 0.24 + 0.012 * i), c + Rr @ (0, r * 0.62, 0), Rr, col,
                          material=material))
    return out


# ---------------------------------------------------------------- fences

def fence_post(sc, parent, name, st, base=None):
    """About 4.4 tall (the topper rises above); pivot on the ground at its centre."""
    base = base or CF()
    b = deco(sc, base)
    m = sc.model(parent, "Post")
    pw = st["pw"]
    pl = b.part(m, "Plinth", (pw + 0.5, 0.5, pw + 0.5), (0, 0.25, 0), None, st["plinth"])
    b.part(m, "Post", (pw, POST_H - 0.85, pw), (0, 0.5 + (POST_H - 0.85) / 2 - 0.02, 0), None, st["post"])
    b.part(m, "Cap", (pw + 0.3, 0.38, pw + 0.3), (0, POST_H - 0.19 - 0.02, 0), None, st["cap"])
    if st["band"]:
        for y in (1.15, POST_H - 0.85):
            b.part(m, "Band", (pw + 0.12, 0.26, pw + 0.12), (0, y, 0), None, st["band"])
    if name == "Fence_Wood":
        b.part(m, "Top", (pw * 0.62, 0.22, pw * 0.62), (0, POST_H + 0.08, 0), None, st["top"])
    elif name == "Fence_Gold":
        round_knob(b, m, (0, POST_H + 0.44, 0), 0.95, ("ffd447", "ffe58a", "fff1c1"))
    elif name == "Fence_Diamond":
        b.part(m, "Setting", (0.66, 0.25, 0.66), (0, POST_H + 0.1, 0), G.ry(45), st["band"])
        jewel(b, m, (0, POST_H + 0.82, 0), 0.72, st["top"])
    else:
        b.part(m, "Stem", (0.3, 0.55, 0.3), (0, POST_H + 0.25, 0), None, st["band"])
        star(b, m, (0, POST_H + 1.05, 0), 0.62, st["top"])
    return finish(m, pl, base)


def fence_rail(sc, parent, name, st, base=None):
    """7 long between post centres (local X -3.5..3.5); every piece runs along X or sits square to
    it, so the Model stretches cleanly. Pivot on the ground halfway between the posts."""
    base = base or CF()
    b = deco(sc, base)
    m = sc.model(parent, "Rail")
    rw = st["rw"]
    L = SPAN - st["pw"] + 0.36                   # tucked 0.18 into each post
    neon = name == "Fence_Rainbow"
    mat = "Neon" if neon else "Plastic"
    top = b.part(m, "Bar", (L, rw, rw), (0, POST_H * 0.78, 0), None, st["rail"], material=mat)
    b.part(m, "Bar", (L - 0.04, rw * 0.84, rw * 0.84), (0, POST_H * 0.36, 0), None, st["rail2"], material=mat)
    if name == "Fence_Gold":
        b.part(m, "Trim", (L - 0.1, 0.14, rw * 0.5), (0, POST_H * 0.78 + rw / 2 + 0.06, 0), None, "fff1c1")
    elif name == "Fence_Diamond":
        for x in (-1.6, 1.6):
            b.part(m, "Diamond", (0.78, 0.78, 0.32), (x, POST_H * 0.57, 0), G.rz(45), "dff6ff")
            b.part(m, "Diamond", (0.42, 0.42, 0.4), (x, POST_H * 0.57, 0), G.rz(45), "7fe3ff")
    if neon:
        for i, p in enumerate((n for n in m.children if n.name == "Bar")):
            sc.attr(p, "Hue", round(i * 0.5, 2))
    return finish(m, top, base)


def gate_arch(sc, parent, name, st, base=None):
    """An open doorway 14 wide (local X) and 6.7 high the player runs through along Z: two posts on
    wider plinths, a header beam in the tier's strong colour and the dark Board above the opening
    (front, -Z, 12.2 x 2.8) with BoardBack on the other side, framed by trim. Pivot on the ground at
    its centre."""
    base = base or CF()
    b = deco(sc, base)
    m = sc.model(parent, "GateArch")
    W, H = 14.0, 10.2
    pw = 1.6
    px = W / 2 + pw / 2
    pls = []
    for s in (-1, 1):
        pls.append(b.part(m, "Plinth", (pw + 0.8, 0.8, pw + 0.8), (s * px, 0.4, 0), None, st["plinth"]))
        b.part(m, "Post", (pw, H - 0.8, pw), (s * px, 0.8 + (H - 0.8) / 2 - 0.02, 0), None, st["post"])
        if st["band"]:
            for y in (1.6, 6.4):
                b.part(m, "Band", (pw + 0.14, 0.34, pw + 0.14), (s * px, y, 0), None, st["band"])
    hw = W + 2 * pw + 1.2
    if name == "Fence_Rainbow":
        seg = hw / len(RAINBOW)
        for i, col in enumerate(RAINBOW):
            b.part(m, "Header", (seg + 0.01, 1.3 + 0.04 * (i % 2), 2.0 + 0.04 * (i % 2)),
                   (-hw / 2 + seg * (i + 0.5), H + 0.63, 0), None, col, material="Neon")
    else:
        b.part(m, "Header", (hw, 1.3, 2.0), (0, H + 0.63, 0), None, st["header"])
        b.part(m, "HeaderCap", (hw - 0.9, 0.3, 1.5), (0, H + 1.43, 0), None, shade(st["header"], 0.3))
    # the name board: two dark panels back to back, trim under them and either side
    BW, BH = 12.2, 2.8
    by0 = 7.2
    bc = by0 + BH / 2
    b.plate(m, "Board", (BW, BH, 0.25), (0, bc, -0.125), None, st["board"])
    b.plate(m, "BoardBack", (BW, BH, 0.25), (0, bc, 0.125), G.ry(180), st["board"])
    b.part(m, "Trim", (W + 0.2, 0.5, 0.9), (0, by0 - 0.25, 0), None, st["trim"])
    side_w = (W - BW) / 2 + 0.1
    for s in (-1, 1):
        b.part(m, "Trim", (side_w, H - by0 - 0.1, 0.8), (s * (BW / 2 + side_w / 2 - 0.05), (by0 + H) / 2 - 0.03, 0),
               None, st["trim"])
    for s in (-1, 1):
        x = s * px
        if name == "Fence_Wood":
            b.part(m, "Cap", (pw + 0.46, 0.4, pw + 0.46), (x, H + 1.45, 0), None, st["cap"])
        elif name == "Fence_Gold":
            round_knob(b, m, (x, H + 1.95, 0), 1.4, ("ffd447", "ffe58a", "fff1c1"))
        elif name == "Fence_Diamond":
            b.part(m, "Setting", (0.94, 0.3, 0.94), (x, H + 1.62, 0), G.ry(45), st["band"])
            jewel(b, m, (x, H + 2.35, 0), 1.0, st["top"])
        else:
            star(b, m, (x, H + 2.6, 0), 0.95, st["top"])
    sc.attr(m, "OpeningWidth", W)
    finish(m, pls[0], base)
    return m


def fence_tier(sc, parent, name):
    f = sc.folder(parent, name)
    st = TIERS[name]
    fence_post(sc, f, name, st)
    fence_rail(sc, f, name, st)
    gate_arch(sc, f, name, st)
    return f


# ---------------------------------------------------------------- SoilHeap, SoilPatch, Mound

WOOD = ("9a6238", "a0572b", "6b4226", "c8743a")
SOIL = "7a4e2e"            # the base colours of the bricks the game tints (named Soil, Leaf, Flag);
LEAF = "4a9a3c"            # each of those carries Shade, how far its own colour is from the base
FLAG = "ffcf3a"
PEBBLE = "b9b4c8"


def out(h):
    """The way out from the middle at heading h (degrees): 0 is the front (-Z), 90 is +X."""
    a = math.radians(h)
    return np.array((math.sin(a), 0.0, -math.cos(a)))


def facing(h):
    """A turn about Y whose own Z points out(h) and own X runs round the circle."""
    return G.ry(180.0 - h)


def tone(B, name, base_col, k, size, pos, R=None):
    """A brick the game tints. Its colour is shade(base_col, k) and it carries Shade = k, so a tint
    keeps the shading as shade(tint, Shade): k < 0 is that much darker, k > 0 that much towards
    white."""
    p = B.p(name, size, pos, R, shade(base_col, k))
    p.p["attrs"]["Shade"] = round(float(k), 2)
    return p


def tone_bar(B, name, base_col, k, a, b, w, t=None, n=None, over=0.0):
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = b - a
    L = float(np.linalg.norm(d))
    return tone(B, name, base_col, k, (w, L + 2 * over, t if t is not None else w), (a + b) / 2, SC.frame(d, n))


def leaflet(B, k, root, d, size):
    """A flat leaflet from root along d, its broad side up."""
    d = np.asarray(d, float)
    d = d / np.linalg.norm(d)
    return tone(B, "Leaf", LEAF, k, size, np.asarray(root, float) + d * size[1] / 2, SC.frame(d, (0.0, 1.0, 0.0)))


def soil_heap(sc, parent, base=None):
    """A heap of dug soil about 4.5 across and 1 high for a seed planted in a pen: three of Folk
    Valley's rounds stacked in steps, lumps on its sides and a pebble. Pivot at the top centre,
    where the seed stands."""
    base = base or CF()
    B = SC.Build(sc, parent, "SoilHeap", seed=11)
    with B.at(base):
        low = tone(B, "Soil", SOIL, 0.0, (4.5, 0.5, 3.0), (0, 0.25, 0), G.ry(12))
        tone(B, "Soil", SOIL, 0.0, (3.0, 0.48, 4.5), (0, 0.24, 0), G.ry(12))
        tone(B, "Soil", SOIL, -0.12, (3.95, 0.46, 3.95), (0, 0.23, 0), G.ry(57))
        mid = np.array((0.08, 0.6, -0.05))
        tone(B, "Soil", SOIL, 0.08, (3.3, 0.4, 2.3), mid, G.ry(-6))
        tone(B, "Soil", SOIL, 0.08, (2.3, 0.38, 3.3), mid, G.ry(-6))
        tone(B, "Soil", SOIL, -0.06, (2.85, 0.36, 2.85), mid, G.ry(39))
        tone(B, "Soil", SOIL, 0.18, (2.0, 0.26, 2.0), (0, 0.87, 0), G.ry(20))
        tone(B, "Soil", SOIL, 0.1, (1.6, 0.24, 1.6), (0, 0.87, 0), G.ry(65))
        for h, r, s, k in ((30, 1.95, 0.72, 0.16), (128, 2.05, 0.62, -0.2), (212, 1.92, 0.68, 0.1),
                           (300, 2.0, 0.58, -0.16)):
            tone(B, "Soil", SOIL, k, (s, s * 0.7, s * 0.86), out(h) * r + (0, 0.42, 0),
                 SC.turn(B.rng, (8.0, 18.0), heading=180.0 - h))
        B.p("Pebble", (0.4, 0.3, 0.36), out(250) * 2.45 + (0, 0.12, 0), ori(6, 30, -8), PEBBLE)
    return finish(B.m, low, base * CF((0, 1.0, 0)))


def soil_patch(sc, parent, base=None):
    """A flat patch of dug soil about 3.6 across under a grown potato: a low round with a few lumps
    round its edge. Pivot at the top centre, where the potato stands."""
    base = base or CF()
    B = SC.Build(sc, parent, "SoilPatch", seed=12)
    top = 0.22
    with B.at(base):
        low = tone(B, "Soil", SOIL, 0.0, (3.6, top, 2.4), (0, top / 2, 0), G.ry(10))
        tone(B, "Soil", SOIL, 0.0, (2.4, top - 0.01, 3.6), (0, (top - 0.01) / 2, 0), G.ry(10))
        tone(B, "Soil", SOIL, -0.12, (3.15, top - 0.02, 3.15), (0, (top - 0.02) / 2, 0), G.ry(55))
        for h, r, s, k in ((20, 1.62, 0.56, 0.16), (105, 1.7, 0.48, -0.18), (200, 1.6, 0.52, 0.1),
                           (290, 1.68, 0.46, -0.14)):
            tone(B, "Soil", SOIL, k, (s, s * 0.6, s * 0.85), out(h) * r + (0, 0.14, 0),
                 SC.turn(B.rng, (6.0, 16.0), heading=180.0 - h))
        B.p("Pebble", (0.34, 0.24, 0.3), out(150) * 1.95 + (0, 0.08, 0), ori(5, 20, -6), PEBBLE)
    return finish(B.m, low, base * CF((0, top, 0)))


MOUND_FLOOR = 0.84          # the top of the hollow: the seed sits here
LEAVES = (40.0, 200.0, 300.0)
STAKE = 140.0


def mound(sc, parent, base=None):
    """The seed bed in the fields, 14 in every area: a heap of dug soil with a hollow in its top, a
    ring of clods round it, three potato-plant leaves drooping over its edge and a little stake
    with a flag. The game tints the bricks named Soil, Leaf and Flag. Pivot at the top centre of
    the hollow, where the seed sits."""
    base = base or CF()
    B = SC.Build(sc, parent, "Mound", seed=5)
    rng = B.rng
    fl = MOUND_FLOOR
    with B.at(base):
        heap = tone(B, "Soil", SOIL, 0.0, (4.4, 0.6, 3.0), (0, 0.3, 0), G.ry(8))
        tone(B, "Soil", SOIL, 0.0, (3.0, 0.58, 4.4), (0, 0.29, 0), G.ry(8))
        tone(B, "Soil", SOIL, -0.1, (3.9, 0.56, 3.9), (0, 0.28, 0), G.ry(53))
        tone(B, "Soil", SOIL, -0.45, (2.1, fl, 2.1), (0, fl / 2, 0), G.ry(8))              # the hollow
        tone(B, "Soil", SOIL, -0.4, (2.1, fl - 0.02, 2.1), (0, (fl - 0.02) / 2, 0), G.ry(53))
        for i in range(6):                                                                  # its rim
            h = i * 60.0 + 20.0 + rng.uniform(-6, 6)
            L = 1.45 + rng.uniform(-0.08, 0.1)
            ht = 0.62 + rng.uniform(-0.06, 0.06)
            tone(B, "Soil", SOIL, 0.12 if i % 2 else 0.02, (L, ht, 0.8), out(h) * 1.45 + (0, 0.86, 0),
                 facing(h) @ G.rx(14.0))
        for j in range(8):                                                                  # the clods
            h = j * 45.0 + 10.0 + rng.uniform(-8, 8)
            if abs((h - STAKE + 180.0) % 360.0 - 180.0) < 14.0:
                h += 16.0
            r = 2.45 + rng.uniform(-0.12, 0.15)
            s = rng.uniform(0.85, 1.1)
            c = out(h) * r + (0, 0.3, 0)
            tone(B, "Soil", SOIL, -0.18 if j % 2 else 0.14, (s, s * 0.72, s * 0.86), c,
                 SC.turn(rng, (8.0, 20.0), heading=180.0 - h))
            if j in (1, 4, 6):
                t = s * 0.6
                tone(B, "Soil", SOIL, 0.22, (t, t * 0.8, t), c + out(h) * 0.12 + (0, s * 0.42, 0),
                     SC.turn(rng, (10.0, 24.0)))
        for h in LEAVES:                                                                    # the leaves
            d = out(h)
            t = np.cross((0.0, 1.0, 0.0), d)
            o = d * 1.2 + (0, 0.98, 0)
            p1 = o + d * 0.78 + (0, 0.44, 0)
            p2 = p1 + d * 0.95 + (0, -0.4, 0)
            tone_bar(B, "Leaf", LEAF, -0.22, o, p1, 0.2, over=0.06)
            tone_bar(B, "Leaf", LEAF, -0.22, p1, p2, 0.18, over=0.06)
            leaflet(B, 0.0, p2 - d * 0.05, d * 0.75 + (0, -0.62, 0), (0.78, 1.15, 0.1))
            q = (p1 + p2) / 2
            for s in (-1.0, 1.0):
                leaflet(B, 0.12, q, s * 0.9 * t + d * 0.2 + (0, -0.36, 0), (0.58, 0.95, 0.09))
        sp = out(STAKE) * 2.2                                                               # the stake
        B.p("Stake", (0.22, 2.7, 0.22), sp + (0, 1.15, 0), None, WOOD[2])
        top = sp + (0, 2.5, 0)
        tone(B, "Flag", FLAG, 0.0, (0.95, 0.62, 0.07), top + (0.585, -0.31, 0), None)
        tone(B, "Flag", FLAG, -0.12, (0.44, 0.38, 0.07), top + (1.25, -0.31, 0.02), G.ry(-12))
        B.p("Pebble", (0.42, 0.32, 0.38), out(250) * 3.0 + (0, 0.12, 0), ori(0, 40, 6), PEBBLE)
    return finish(B.m, heap, base * CF((0, fl, 0)))


def upgrade_board(sc, parent, base=None):
    """Folk Valley's sign, small: two legs on plinths, a gold header beam, the dark Board between
    (front -Z) and a bright green Button under it for the price; an invisible Prompt in front.
    Pivot on the ground at its centre."""
    base = base or CF()
    b = deco(sc, base)
    m = sc.model(parent, "UpgradeBoard")
    pls = []
    for s in (-1, 1):
        pls.append(b.part(m, "Plinth", (1.3, 0.5, 1.3), (s * 2.6, 0.25, 0), None, "8e89a0"))
        b.part(m, "Leg", (0.8, 5.6, 0.8), (s * 2.6, 0.5 + 2.8 - 0.02, 0), None, WOOD[2])
    b.part(m, "Header", (6.6, 1.0, 1.2), (0, 6.6, 0), None, "f5b700")
    b.part(m, "HeaderCap", (6.0, 0.28, 0.8), (0, 7.24, 0), None, "ffd447")
    b.plate(m, "Board", (4.42, 2.9, 0.3), (0, 4.6, -0.05), None, "22232b")
    b.part(m, "Frame", (4.42, 0.4, 0.7), (0, 2.95, 0), None, WOOD[0])
    b.part(m, "ButtonBase", (3.0, 1.0, 0.7), (0, 2.25, -0.25), None, "3f9e3c")
    b.plate(m, "Button", (2.6, 0.72, 0.2), (0, 2.27, -0.66), None, "5dbb46")
    b.part(m, "Prompt", (4.0, 4.0, 2.0), (0, 3.0, -2.6), None, "ffffff", material="SmoothPlastic",
           transparency=1.0, shadow=False)
    return finish(m, pls[0], base)


# ---------------------------------------------------------------- Seeds

def seed_body(b, m, c=(0.0, 0.0, 0.0)):
    """An egg 1.7 wide and 1.9 tall, stacked like Folk Valley's rounds and narrowing to the top;
    every brick named Body (the game tints them)."""
    c = np.asarray(c, float)
    return [b.part(m, "Body", (1.25, 0.32, 1.25), c + (0, 0.16, 0), G.ry(45), TINT),           # foot
            b.part(m, "Body", (1.7, 0.9, 1.1), c + (0, 0.74, 0), None, TINT),                  # wide middle,
            b.part(m, "Body", (1.1, 0.92, 1.7), c + (0, 0.74, 0), None, TINT),                 # crossing
            b.part(m, "Body", (1.36, 0.94, 1.36), c + (0, 0.74, 0), G.ry(45), TINT),           # and turned
            b.part(m, "Body", (1.3, 0.56, 0.86), c + (0, 1.42, 0), None, TINT),                # shoulders
            b.part(m, "Body", (0.86, 0.58, 1.3), c + (0, 1.42, 0), None, TINT),
            b.part(m, "Body", (0.74, 0.3, 0.74), c + (0, 1.78, 0), G.ry(45), TINT)]            # tip


def leaf_sprout(b, m, top, cols=("3f9e3c", "55b848", "7ad155")):
    t = np.asarray(top, float)
    b.part(m, "Sprout", (0.22, 0.5, 0.22), t + (0, 0.2, 0), G.rz(-8), cols[0])
    for s in (-1, 1):
        R = G.ry(s * 15) @ G.rz(s * 30)
        b.part(m, "Sprout", (0.55, 0.12, 0.34), t + (s * 0.24, 0.42, 0), R, cols[1 if s < 0 else 2])


TOP_K = 1.3                 # toppers 30% bigger than the first cut: they tell the areas apart in the field
TOP = np.array((0.0, 1.85, 0.0))


def seed(sc, parent, area, base=None):
    base = base or CF()
    b = deco(sc, base)
    m = sc.model(parent, "Seed_" + area)
    body = seed_body(b, m)
    k = TOP_K

    def tp(name, size, pos, R=None, col="ffffff", material="Plastic"):
        """A topper brick: sized and placed TOP_K times bigger about the top of the egg."""
        pos = TOP + (np.asarray(pos, float) - TOP) * k
        return b.part(m, name, tuple(v * k for v in size), pos, R, col, material=material)

    def dt(name, size, pos, R=None, col="ffffff", material="Plastic"):
        return b.part(m, name, size, pos, R, col, material=material)
    if area == "Meadow":
        tp("Sprout", (0.22, 0.5, 0.22), (0, 2.1, 0), G.rz(-8), "3f9e3c")
        for s_ in (-1, 1):
            R = G.ry(s_ * 15) @ G.rz(s_ * 30)
            tp("Sprout", (0.55, 0.12, 0.34), (s_ * 0.24, 2.32, 0), R, "55b848" if s_ < 0 else "7ad155")
        dt("Detail", (0.24, 0.2, 0.1), (0.4, 1.0, -0.82), None, "8a6a40")
        dt("Detail", (0.2, 0.16, 0.1), (-0.3, 0.55, -0.82), None, "8a6a40")
    elif area == "Dunes":
        dt("Detail", (1.76, 0.22, 1.12), (0, 0.45, 0), None, "e8c27a")                    # sand band
        dt("Detail", (1.12, 0.23, 1.76), (0, 0.45, 0), None, "e8c27a")
        tp("Sprout", (0.3, 0.62, 0.3), (0, 2.12, 0), None, "4fa83a")                       # a tiny cactus
        tp("Sprout", (0.2, 0.32, 0.2), (0.26, 2.12, 0), None, "4fa83a")
        tp("Sprout", (0.2, 0.3, 0.2), (-0.24, 2.02, 0), None, "4fa83a")
        tp("Detail", (0.2, 0.14, 0.2), (0, 2.5, 0), G.ry(45), "ff8fc7")                    # its flower
    elif area == "Marsh":
        tp("Sprout", (0.26, 0.4, 0.26), (0, 2.02, 0), None, "f2efe6")                      # a toadstool
        tp("Detail", (0.9, 0.3, 0.9), (0, 2.3, 0), G.ry(45), "e8403a")
        tp("Detail", (0.62, 0.2, 0.62), (0, 2.48, 0), G.ry(45), "e8403a")
        tp("Dots", (0.2, 0.08, 0.2), (0.18, 2.6, 0.05), None, "ffffff")
        tp("Dots", (0.16, 0.08, 0.16), (-0.25, 2.47, -0.25), G.ry(30), "ffffff")
        dt("Detail", (0.42, 0.1, 0.42), (-0.5, 0.06, -0.62), G.ry(20), "4fa83a")           # a lily pad
    elif area == "Frost":
        tp("Detail", (1.06, 0.22, 1.06), (0, 1.86, 0), G.ry(45), "ffffff")                 # snow cap
        tp("Detail", (0.7, 0.2, 0.7), (0.05, 2.02, 0), G.ry(10), "ffffff")
        for x, z, h in ((-0.55, -0.6, 0.5), (0.2, -0.78, 0.38), (0.62, -0.42, 0.45)):
            dt("Icicle", (0.16, h, 0.16), (x, 1.5 - h / 2, z), None, "a9d8ff")
        tp("Sprout", (0.16, 0.36, 0.16), (0, 2.25, 0), G.rz(-15), "6b4226")                # a twig
    elif area == "Lava":
        dt("Detail", (0.12, 0.7, 0.1), (0.25, 0.9, -0.82), G.rz(20), "ff6a1a", material="Neon")
        dt("Detail", (0.5, 0.1, 0.1), (-0.2, 1.15, -0.82), G.rz(-10), "ff6a1a", material="Neon")
        for y, s_, col in ((2.0, 0.6, "ff5a1f"), (2.35, 0.42, "ff9f1a"), (2.62, 0.24, "ffe14d")):
            tp("Flame", (s_, 0.4, s_), (0, y, 0), G.ry(45 * (y > 2.2)), col, material="Neon")
    elif area == "Crystal":
        for (x, z, h, rz_, rx_, col) in ((0, 0, 0.9, 0, 0, "b67cff"), (0.32, 0.1, 0.62, -22, 8, "7fe3ff"),
                                         (-0.3, -0.1, 0.55, 24, -6, "d8b4ff")):
            tp("Crystal", (0.3, h, 0.3), (x, 1.84 + h / 2 - 0.08, z), ori(rx_, 45, rz_), col)
        dt("Detail", (0.3, 0.3, 0.1), (0.35, 0.95, -0.82), G.rz(45), "b67cff")
    elif area == "Candy":
        tp("Sprout", (0.16, 0.6, 0.16), (0, 2.12, 0), None, "ffffff")                      # a lollipop
        tp("Detail", (0.7, 0.7, 0.18), (0, 2.65, 0), None, "ff7eb6")
        tp("Detail", (0.5, 0.5, 0.2), (0, 2.65, 0), G.rz(45), "ffffff")
        for (x, y, rz_, col) in ((-0.4, 1.1, 20, "5ee06a"), (0.35, 0.7, -30, "4da6ff"), (0.15, 1.35, 70, "ffe14d")):
            dt("Sprinkle", (0.3, 0.1, 0.1), (x, y, -0.83), G.rz(rz_), col)
    elif area == "Cosmic":
        for i in range(4):                                                                 # a ring round it
            R = G.rz(14) @ G.ry(i * 90)
            dt("Ring", (2.1, 0.12 + 0.04 * (i % 2), 0.3), R @ (0, 0, 1.0) + (0, 0.85, 0), R, "ffd447")
        star(b, m, TOP + (np.array((0, 2.25, 0)) - TOP) * k, 0.32 * k, "fffbe6")
    elif area == "Jungle":
        dt("Vine", (1.78, 0.18, 1.14), (0, 1.0, 0), G.rz(-8), "2f8a3c")                     # a vine wound round it
        dt("Vine", (1.14, 0.19, 1.78), (0, 1.1, 0), G.rz(6), "3fae4a")
        for i, (yaw, col) in enumerate(((0, "3fae4a"), (120, "55b848"), (240, "2f8a3c"))):    # three fronds
            R = G.ry(yaw) @ G.rx(-38)
            tp("Leaf", (0.36, 0.1, 0.9), (0, 2.05, 0) + R @ (0, 0, -0.38), R, col)
        tp("Sprout", (0.2, 0.36, 0.2), (0, 2.02, 0), None, "6b4226")
    elif area == "Reef":
        tp("Shell", (0.5, 0.16, 0.5), (0, 2.0, 0), G.ry(45), "ff8a3d")                     # a starfish
        for i in range(5):
            R = G.ry(i * 72)
            tp("Shell", (0.16, 0.13, 0.42), (0, 2.0, 0) + R @ (0, 0, -0.3), R, "ff8a3d")
        dt("Coral", (0.16, 0.5, 0.16), (-0.62, 0.55, -0.55), G.rz(12), "ff6fa8")
        dt("Coral", (0.14, 0.3, 0.14), (-0.75, 0.75, -0.45), G.rz(-30), "ff6fa8")
        dt("Detail", (0.3, 0.3, 0.1), (0.4, 1.05, -0.82), G.rz(45), "4fc3f7")
    elif area == "Haunt":
        tp("Pumpkin", (0.62, 0.42, 0.42), (0, 2.12, 0), None, "f07412")                    # a tiny jack-o'-lantern
        tp("Pumpkin", (0.42, 0.43, 0.62), (0, 2.12, 0), None, "f07412")
        tp("Pumpkin", (0.52, 0.38, 0.52), (0, 2.12, 0), G.ry(45), "ffa23f")
        tp("Sprout", (0.12, 0.22, 0.12), (0, 2.4, 0), G.rz(12), "5b7a2e")
        tp("Face", (0.12, 0.12, 0.1), (-0.12, 2.16, -0.33), G.rz(45), "ffc93c", material="Neon")
        tp("Face", (0.12, 0.12, 0.1), (0.12, 2.16, -0.33), G.rz(45), "ffc93c", material="Neon")
        dt("Band", (1.78, 0.2, 1.14), (0, 0.6, 0), None, "6b3fa0")
        dt("Band", (1.14, 0.21, 1.78), (0, 0.6, 0), None, "6b3fa0")
    elif area == "Dino":
        for (x, y, z, sz, col) in ((-0.5, 1.2, -0.79, 0.42, "6aa84f"), (0.45, 0.65, -0.86, 0.34, "6aa84f"),
                                   (0.82, 1.3, -0.3, 0.3, "4f8a3a"), (-0.75, 0.6, 0.45, 0.36, "4f8a3a")):
            dt("Spot", (sz, sz, 0.1), (x, y, z), G.ry(-math.degrees(math.atan2(x, -z))), col)  # a spotted egg
        tp("Crack", (0.5, 0.1, 0.1), (-0.1, 2.0, -0.32), G.rz(30), "3a2a1e")
        tp("Crack", (0.4, 0.1, 0.1), (0.24, 1.98, -0.335), G.rz(-35), "3a2a1e")
        tp("Sprout", (0.18, 0.4, 0.18), (0.1, 2.12, 0.05), G.rz(-12), "4f8a3a")             # a fern curl
        tp("Leaf", (0.45, 0.1, 0.25), (-0.1, 2.32, 0.05), G.rz(25), "6aa84f")
    elif area == "Toy":
        tp("Key", (0.16, 0.4, 0.16), (0, 2.08, 0.25), G.rx(-20), "8e89a0")                  # a wind-up key
        for s_ in (-1, 1):
            tp("Key", (0.36, 0.42, 0.12), (s_ * 0.26, 2.38, 0.33), G.rx(-20) @ G.rz(s_ * 12), "b9b4c8")
        dt("Stripe", (1.78, 0.22, 1.14), (0, 0.8, 0), None, "e8403a")
        dt("Stripe", (1.14, 0.23, 1.78), (0, 0.8, 0), None, "3e7bd6")
    elif area == "Clock":
        tp("Gear", (0.7, 0.7, 0.18), (0, 2.25, 0), None, "c9a227")                         # a brass gear
        tp("Gear", (0.7, 0.7, 0.17), (0, 2.25, 0), G.rz(45), "c9a227")
        tp("Gear", (0.32, 0.32, 0.22), (0, 2.25, 0), None, "8a6a1e")
        tp("Sprout", (0.16, 0.3, 0.16), (0, 1.95, 0), None, "8a6a1e")
        dt("Face", (0.5, 0.5, 0.1), (0, 0.92, -0.83), None, "fff7ec")                     # a clock face
        dt("Hand", (0.06, 0.22, 0.1), (0, 1.0, -0.88), None, "1e1a22")
        dt("Hand", (0.17, 0.06, 0.1), (0.07, 0.92, -0.895), None, "1e1a22")
    elif area == "Neon":
        dt("Stripe", (1.78, 0.14, 1.14), (0, 0.55, 0), None, "00f0ff", material="Neon")
        dt("Stripe", (1.14, 0.15, 1.78), (0, 1.05, 0), None, "ff2bd6", material="Neon")
        tp("Antenna", (0.12, 0.5, 0.12), (0, 2.1, 0), None, "3a3a46")
        tp("Antenna", (0.3, 0.3, 0.3), (0, 2.42, 0), G.ry(45), "00f0ff", material="Neon")
    elif area == "Cloud":
        for (x, y, z, sz) in ((0, 2.15, 0, 0.62), (-0.36, 2.05, 0.05, 0.46), (0.38, 2.06, -0.04, 0.5),
                              (0.05, 2.38, 0.02, 0.4)):
            tp("Cloud", (sz, sz * 0.8, sz), (x, y, z), G.ry(20), "ffffff")
        dt("Drop", (0.12, 0.2, 0.12), (-0.35, 1.0, -0.84), None, "7fc4ff")
        dt("Drop", (0.12, 0.2, 0.12), (0.3, 0.7, -0.86), None, "7fc4ff")
    elif area == "Void":
        for (x, y, z, sz, col, mat) in ((0, 2.2, 0, 0.36, "1e1a22", "Plastic"), (0.36, 2.45, -0.1, 0.22, "ff2bd6", "Neon"),
                                        (-0.32, 2.36, 0.12, 0.2, "00f0ff", "Neon"), (0.1, 2.62, 0.2, 0.16, "1e1a22", "Plastic")):
            tp("Glitch", (sz, sz, sz), (x, y, z), ori(20, 30, 10), col, material=mat)
        dt("Crack", (0.1, 0.6, 0.1), (0.3, 0.9, -0.84), G.rz(25), "ff2bd6", material="Neon")
    elif area == "Olympus":
        for i in range(6):                                                                 # a laurel wreath
            R = G.ry(i * 60 + 15)
            tp("Laurel", (0.42, 0.1, 0.22), (0, 1.98, 0) + R @ (0, 0, -0.42), R @ G.rz(15), "6aa84f")
        dt("Band", (1.78, 0.22, 1.14), (0, 0.5, 0), None, "ffd447")
        dt("Band", (1.14, 0.23, 1.78), (0, 0.5, 0), None, "ffd447")
    return finish(m, body[0], base)


AREAS = ("Meadow", "Dunes", "Marsh", "Jungle", "Reef", "Frost", "Haunt", "Lava", "Crystal", "Dino", "Toy",
         "Candy", "Clock", "Neon", "Cloud", "Cosmic", "Void", "Olympus")


def build(sc):
    """The whole of 4.2 under the scene root (PotatoKit)."""
    fences = sc.container(sc.root, "Fences")
    for name in TIER_ORDER:
        f = fence_tier(sc, fences, name)
        f.p["item"] = True
    soil_heap(sc, sc.root)
    soil_patch(sc, sc.root)
    upgrade_board(sc, sc.root)
    mound(sc, sc.root)
    seeds = sc.container(sc.root, "Seeds")
    for a in AREAS:
        seed(sc, seeds, a)
    return sc
