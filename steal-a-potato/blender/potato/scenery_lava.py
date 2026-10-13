"""Lava Furrows: the hero, a volcano with lava running down it, and the area's props.

The volcano is a stepped cone of nine rounded tiers (a core and two crossing slabs each, every tier
turned its own way and a different height), dark charcoal at the foot warming to red-brown at the
top, boulders lying on its ledges. Its crater opens towards the lane behind a jagged rim: a glowing
pool, a boiling dome of lava spurting up and splashing, embers flying and puffs of smoke rising
over it. Three streams of lava run down the front over the noses of the steps, each a run of short
orange Neon bars with a yellow core, widening as they go, two from the crater and one from a vent
in the flank, into a bubbling lava pool at the foot behind a low rock kerb. Glowing cracks split
the steps; lava bombs lie about. At the foot a potato in a silver fire-proof suit dips a long ladle
into the pool. The whole cone, the boulders on it and the kerb are solid.
"""
import math

import numpy as np

import spsgeo as G
from spsgeo import CF

from .scenery import (Area, Build, bar, flame, frame, ori, potato, prop_attrs, register, rock, round3, turn)

# charcoal at the foot of the cone, warming to red-brown at the top: three close shades a tier
TIER_COLS = (("2c2729", "342e32", "3c363a"), ("2f2a2d", "383135", "40383d"), ("362e33", "3f353a", "483c40"),
             ("3f3136", "49363a", "52393c"), ("49343a", "543a3c", "5e3e3c"), ("54383a", "603e3b", "6a433b"),
             ("603c37", "6c4339", "76483a"), ("6c4237", "794939", "844f3b"), ("79483a", "864f3b", "93563e"))
ROCK = ("2e292c", "383236", "423b40", "4c444a")          # charcoal
BASALT = ("4e3236", "5e3a36", "6e4236", "804c3a")        # red-brown
LAVA = ("ff6a1a", "ff8a1a", "ffb02e", "ffd23f")          # deep orange, orange, amber, yellow
EMBER = "ff4a1a"
SMOKE = ("8e8894", "a39eaa", "b8b3be", "cbc7d0")
STEAM = ("d6d2da", "e4e0e8", "f0edf2")
OBSIDIAN = ("17111e", "201729", "2a1e36", "342542")
SHEEN = ("6a4a9e", "9a7ad0")
BONE = ("f2ead8", "e4d8c0", "fff8e8", "d6c8ac")
CHAR = ("231e21", "2d2629", "383033", "433a3c")
WOOD = ("33241c", "402d22", "4e3828")                     # burnt wood
SUIT = ("c8ccd4", "aeb3bd", "e2e5ea")
SKIN = ("d9b07a", "c49a64", "e8c490")
GOLD = "e8b830"
IRON = ("3a3f4a", "4a505c", "2a2a30")
HAZARD = ("ffc21a", "1e1a22")

# the cone: width, depth, height, front edge, heading of each tier from the foot up
TIERS = ((42.0, 23.8, 2.8, -9.6, 0.0), (35.5, 21.0, 3.2, -7.6, 2.0), (30.0, 18.6, 2.9, -5.9, -2.5),
         (25.6, 16.6, 3.3, -4.4, 3.5), (22.0, 14.8, 2.8, -3.1, -4.5), (19.0, 13.2, 3.1, -1.9, 6.0),
         (16.6, 11.8, 2.7, -0.8, -8.0), (14.6, 10.6, 2.9, 0.2, 10.0), (13.0, 9.6, 2.7, 1.0, -12.0))
TIER_X = (0.0, 0.9, -0.7, 1.1, -1.0, 0.8, -0.9, 0.6, 0.2)
# jagged cracks, as (x, height up the face) steps: a fork, a zigzag and one running along the face
CRACKS = {"fork": ((0.0, 0.92), (0.45, 0.62), (0.1, 0.38), (0.6, 0.1)),
          "zig": ((0.0, 0.9), (-0.5, 0.66), (0.2, 0.4), (-0.3, 0.12)),
          "flat": ((-1.4, 0.55), (-0.5, 0.7), (0.3, 0.46), (1.3, 0.62))}


def neon(B, name, size, pos, R=None, col=LAVA[1], flicker=0.15, **kw):
    return B.p(name, size, pos, R, col, material="Neon", flicker=flicker, lamp=True, **kw)


def crack(B, pts, n, w=0.26, t=0.12, col=EMBER, name="Crack", flicker=0.2, lift=0.0):
    """A jagged glowing crack through pts, lying on a face whose outward normal is n; each bar a hair
    further out than the last so the joints never fight (a branch takes its own lift)."""
    n = np.asarray(n, float)
    out = []
    for i in range(len(pts) - 1):
        a, b = np.asarray(pts[i], float), np.asarray(pts[i + 1], float)
        o = n * (t / 2 - 0.02 + lift + 0.03 * (i % 2))
        out.append(bar(B, name, a + o, b + o, w, col, t=t, n=n, over=w * 0.45, material="Neon", flicker=flicker,
                       lamp=True))
    return out


def front_z(parts, x, y):
    """The front-most z of these parts (boxes) along the line through (x, y) parallel to Z."""
    best = None
    for q in parts:
        cf = q.p["cf"]
        hs = np.array(q.p["size"]) / 2
        Rt = cf.R.T
        l0 = Rt @ (np.array((x, y, 0.0)) - cf.p)
        r = Rt[:, 2]
        lo, hi, ok = -1e9, 1e9, True
        for i in range(3):
            if abs(r[i]) < 1e-9:
                ok = ok and abs(l0[i]) <= hs[i]
            else:
                t0, t1 = (-hs[i] - l0[i]) / r[i], (hs[i] - l0[i]) / r[i]
                lo, hi = max(lo, min(t0, t1)), min(hi, max(t0, t1))
        if ok and lo <= hi:
            best = lo if best is None else min(best, lo)
    return best


def stream(B, pts, w0, w1, name="Lava", t=0.5, sink=0.14):
    """Lava running down through pts (top first), over the noses of the steps: each run a short
    orange Neon bar resting on the noses, a yellow core a hair proud of it, wider as it goes down."""
    out = []
    n_seg = len(pts) - 1
    for k in range(n_seg):
        a, b = np.asarray(pts[k], float), np.asarray(pts[k + 1], float)
        d = (b - a) / np.linalg.norm(b - a)
        side = np.array((1.0, 0.0, 0.0))
        side = side - d * (side @ d)
        nrm = np.cross(side, d)
        nrm /= np.linalg.norm(nrm)
        L = float(np.linalg.norm(b - a))
        w = w0 + (w1 - w0) * k / max(1, n_seg - 1)
        tk = t + 0.03 * (k % 2)
        mid = (a + b) / 2
        R = frame(d, nrm)
        over = w * 0.3
        out.append(B.p(name, (w, L + 2 * over, tk), mid + nrm * (tk / 2 - sink), R, LAVA[1 if k % 3 else 0],
                       material="Neon", flicker=0.12, lamp=True))
        tc = 0.3
        out.append(B.p(name, (w * 0.42, L + 2 * over - 0.3, tc), mid + nrm * (tk - sink + 0.06 - tc / 2), R,
                       LAVA[3] if k % 2 == 0 else LAVA[2], material="Neon", flicker=0.2, lamp=True))
    return out


def puff(B, c, s, cols, heading=0.0, name="Smoke"):
    """A puff of smoke: a wide flat block, a crossing one and a turned one on top, tilted a little."""
    c = np.asarray(c, float)
    return [B.p(name, (s * 1.4, s * 0.6, s * 1.0), c, ori(4, heading, -5), cols[0]),
            B.p(name, (s * 0.96, s * 0.66, s * 1.3), c + (s * 0.12, s * 0.05, 0), ori(-5, heading + 14, 4), cols[1]),
            B.p(name, (s * 0.84, s * 0.6, s * 0.84), c + (-s * 0.1, s * 0.42, 0.05 * s), ori(8, heading + 45, 6),
                cols[2])]


def lava_bomb(B, c, s, heading=0.0, name="LavaBomb"):
    """A lump of cooling lava: a dark crust, its glowing heart showing through."""
    c = np.asarray(c, float)
    return [B.p(name, (s, s * 0.8, s * 0.9), c + (0, s * 0.38, 0), ori(8, heading, -6), ROCK[1]),
            neon(B, name, (s * 0.7, s * 0.62, s * 1.0), c + (0, s * 0.42, 0), ori(-6, heading + 40, 10), LAVA[0],
                 flicker=0.25)]


def suited_spud(B, base, s, heading, ladle_to, name="FireSpud"):
    """A potato in a silver fire-proof suit: boots, a jacket and a hood framing its face, a gold
    visor flipped up, gloves; it dips a long ladle into the lava at ladle_to."""
    R = G.ry(heading)
    base = np.asarray(base, float)

    def at(v):
        return base + R @ np.asarray(v, float)
    leg = 1.0
    for sx in (-1, 1):
        B.p(name, (s * 0.24, leg + 0.12, s * 0.26), at((sx * s * 0.19, (leg + 0.12) / 2, 0.05)), R, SUIT[1])
        B.p(name, (s * 0.3, 0.5, s * 0.44 + 0.02 * (sx > 0)), at((sx * s * 0.19, 0.25, -0.14)), R, CHAR[2])
    c = at((0, leg + s / 2, 0))
    potato(B, c, s, SKIN, R=R, name=name, glints=True, cheeks="ff9aa8")
    B.p(name, (s * 0.92, s * 0.3, s * 0.84), c + R @ (0, -s * 0.36, 0), R, SUIT[0])              # the jacket
    B.p(name, (s * 0.3, s * 0.1, 0.12), c + R @ (0, -s * 0.3, -s * 0.42 - 0.05), R, GOLD, material="SmoothPlastic",
        shadow=False)                                                                            # its badge
    B.p(name, (s * 0.94, s * 0.3, s * 0.86), c + R @ (0, s * 0.43, 0.0), R, SUIT[0])              # the hood
    for sx in (-1, 1):                                                                           # its flaps
        B.p(name, (s * 0.12, s * 0.5, s * 0.76), c + R @ (sx * s * 0.48, s * 0.2, 0.02), R, SUIT[2])
    B.p(name, (s * 0.62, s * 0.14, s * 0.62), c + R @ (0, s * 0.63, 0.04), R @ G.ry(45), SUIT[2])
    B.p(name, (s * 0.8, s * 0.28, 0.24), c + R @ (0, s * 0.6, -s * 0.47), R @ G.rx(-34), GOLD)   # visor, up
    # the right arm holds the ladle out over the pool, the left waves
    sh = c + R @ (s * 0.42, -s * 0.05, -0.1)
    hand = c + R @ (s * 0.6, -s * 0.12, -s * 0.62)
    bar(B, name, sh, hand, s * 0.17, SUIT[1])
    B.p(name, (s * 0.24, s * 0.24, s * 0.24), hand, R @ G.ry(20), CHAR[2])
    tip = np.asarray(ladle_to, float)
    bar(B, "Ladle", hand + (0, 0.25, 0), tip + (0, 0.5, 0), 0.26, IRON[0], over=0.3)
    B.p("Ladle", (1.0, 0.6, 1.0), tip + (0, 0.25, 0), G.ry(20), IRON[1])
    sh2 = c + R @ (-s * 0.42, s * 0.0, -0.05)
    hand2 = c + R @ (-s * 0.66, s * 0.36, -s * 0.2)
    bar(B, name, sh2, hand2, s * 0.17, SUIT[1])
    B.p(name, (s * 0.26, s * 0.26, s * 0.22), hand2 + R @ (-0.05, 0.12, 0), R @ G.rz(-20), CHAR[2])


# ==================================================================== the hero

def hero(sc, parent):
    B = Build(sc, parent, "Lava", seed=211)
    # the cone: nine tiers, each a core and two crossing slabs, each tier turned its own way
    tiers, tops, y = [], [], 0.0
    for k, (W, D, h, zf, hd) in enumerate(TIERS):
        R = G.ry(hd)
        c = np.array((TIER_X[k], 0.0, zf + D / 2))
        cols = TIER_COLS[k]
        ps = [B.p("Cone", (W * 0.86, h, D * 0.86), c + (0, y + h / 2, 0), R, cols[0], solid=True),
              B.p("Cone", (W, h - 0.05, D * 0.6), c + (0, y + 0.03 + (h - 0.05) / 2, 0), R, cols[1], solid=True),
              B.p("Cone", (W * 0.6, h - 0.1, D), c + (0, y + 0.06 + (h - 0.1) / 2, 0), R, cols[2], solid=True)]
        tiers.append((ps, c, R, W, D, h, y))
        y += h
        tops.append(y)
    top = y

    def nose(k, x):
        return np.array((x, tops[k] - 0.04, front_z(tiers[k][0], x, tops[k] - 0.08)))

    # boulders lying on the ledges, breaking the outline of the steps
    for k, x, dz, s, cols in ((1, -15.6, -1.5, 3.4, (ROCK[2], BASALT[0], ROCK[1])),
                              (2, 12.8, -0.6, 3.1, (ROCK[3], BASALT[1], ROCK[2])),
                              (4, -10.2, 0.2, 2.8, (BASALT[1], ROCK[3], BASALT[0])),
                              (5, 8.9, 0.8, 2.5, (BASALT[2], BASALT[1], BASALT[3])),
                              (6, -7.8, 1.2, 2.1, (BASALT[2], BASALT[3], BASALT[1]))):
        c = tiers[k][1]
        rock(B, (x, tops[k] - 0.05, c[2] + dz), s, cols, solid=True)
    # the crater: a jagged rim open towards the lane, a glowing pool, a boiling dome spurting lava
    _ps, cc, _R, W8, D8, _h, _y = tiers[-1]
    a, b = W8 / 2 - 1.3, D8 / 2 - 1.0
    for k, (phi, hh, cols) in enumerate(((-140, 2.0, BASALT[3]), (-32, 2.4, BASALT[2]), (8, 2.8, BASALT[3]),
                                          (52, 2.2, BASALT[2]), (92, 2.6, BASALT[3]), (132, 2.0, BASALT[2]),
                                          (172, 2.5, BASALT[3]), (212, 1.8, BASALT[2]))):
        f = math.radians(phi)
        p = cc + (a * math.cos(f), top + hh / 2 - 0.2, b * math.sin(f))
        tx, tz = -a * math.sin(f), b * math.cos(f)
        hd = math.degrees(math.atan2(-tz, tx))
        B.p("Rim", (3.6 + 0.1 * (k % 2), hh, 1.7), p, G.ry(hd) @ G.rx(-10 - 3 * (k % 3)), cols, solid=True)
    neon(B, "Crater", (W8 - 3.0, 0.5, D8 - 2.4), cc + (0, top + 0.25, 0.2), G.ry(-12), LAVA[0], flicker=0.1)
    neon(B, "Crater", (5.0, 2.2, 3.8), cc + (0.3, top + 1.0, 0.1), G.ry(30), LAVA[1], flicker=0.2)
    neon(B, "Crater", (3.0, 1.6, 2.8), cc + (0.1, top + 2.3, 0.0), G.ry(72), LAVA[2], flicker=0.25)
    neon(B, "Spurt", (1.9, 3.2, 1.9), cc + (0.2, top + 3.9, 0.0), G.ry(20), LAVA[1], flicker=0.25)
    neon(B, "Spurt", (1.1, 3.6, 1.1), cc + (0.2, top + 4.2, 0.0), G.ry(65), LAVA[3], flicker=0.3)
    for k, (x, dy, z, s) in enumerate(((-1.6, 5.9, -0.6, 1.0), (1.9, 6.3, -0.2, 0.9), (0.4, 6.8, 0.8, 0.8),
                                       (-2.9, 4.1, -1.2, 0.7), (3.4, 4.6, -1.0, 0.6))):
        neon(B, "Splash", (s, s * 0.9, s * 0.8), cc + (x, top + dy, z), ori(25, 30 * k, 35), LAVA[(k + 1) % 4],
             flicker=0.3)
    # puffs of smoke rising over it, lighter as they go, drifting back
    for k, (x, dy, z, s, hd) in enumerate(((0.6, 7.0, 1.8, 3.4, 10.0), (-2.6, 8.7, 2.8, 4.2, 40.0),
                                           (2.5, 9.8, 3.6, 3.8, 70.0))):
        puff(B, cc + (x, top + dy, z), s, SMOKE[k:k + 3] if k < 2 else (SMOKE[2], SMOKE[3], SMOKE[3]), heading=hd)
    # three streams of lava down the front: two out of the crater, one out of a vent in the flank
    pool_z = -11.0
    for xs, xp, w0, w1 in (((-1.0, -1.5, -0.9, -1.7, -2.5, -2.1, -2.9, -3.5, -3.0), -3.6, 1.4, 2.6),
                           ((2.4, 3.0, 3.9, 4.5, 5.4, 6.3, 7.2, 8.0, 8.7), 9.4, 1.2, 2.3)):
        n8 = nose(8, xs[0])
        pts = [n8 + (0, 0.36, 1.6)] + [nose(8 - j, x) for j, x in enumerate(xs)] + [np.array((xp, 0.42, pool_z))]
        stream(B, pts, w0, w1)
    vent = nose(5, -5.4) + (0, -0.9, -0.05)
    B.p("Vent", (2.6, 1.0, 1.4), vent + (0, 0.95, 0.35), ori(0, 6, 4), BASALT[1], solid=True)
    neon(B, "Vent", (1.6, 1.1, 0.7), vent + (0, 0.05, 0.1), ori(0, 10, 45), LAVA[2], flicker=0.25)
    pts = [vent] + [nose(4 - j, x) for j, x in enumerate((-6.0, -6.8, -7.6, -8.3, -8.9))] + \
        [np.array((-9.4, 0.42, pool_z))]
    stream(B, pts, 1.0, 1.8)
    # glowing cracks splitting the steps: (tier, x, how deep the face lies, shape, which way)
    for k, x, f, shape, sg in ((0, 2.6, 0.5, "fork", 1), (0, -12.4, 0.5, "zig", 1), (0, 15.6, 0.43, "flat", 1),
                               (1, 1.8, 0.5, "zig", -1), (2, -11.2, 0.43, "flat", -1), (3, 1.6, 0.5, "fork", -1),
                               (5, 1.2, 0.5, "zig", 1), (6, -4.0, 0.5, "fork", -1)):
        _ps, c, R, W, D, h, y0 = tiers[k]
        with B.at(CF(c, R)):
            z = -D * f
            crack(B, [(x + sg * dx, y0 + h * fy, z) for dx, fy in CRACKS[shape]], (0, 0, -1),
                  flicker=0.2 if k % 2 else None)
    # the lava pool at the foot behind a low kerb of rock, bubbling
    neon(B, "Pool", (21.0, 0.42, 5.2), (0.0, 0.21, -11.2), None, LAVA[0], flicker=0.1)
    neon(B, "Pool", (16.0, 0.48, 6.4), (0.4, 0.24, -11.0), G.ry(4), LAVA[1], flicker=None)
    neon(B, "Pool", (8.0, 0.56, 2.6), (-0.6, 0.28, -12.0), G.ry(-6), LAVA[3], flicker=0.2)
    for k, (x, z, s) in enumerate(((-5.6, -12.4, 1.1), (4.4, -11.9, 0.9), (1.0, -12.9, 0.7))):
        neon(B, "Bubble", (s, s * 0.8, s), (x, 0.5 + s * 0.3, z), ori(0, 30 * k + 10, 0), LAVA[2 + k % 2],
             flicker=0.3)
    for k in range(8):
        f = math.pi * (k + 0.5) / 8
        p = np.array((11.4 * math.cos(f), 0.0, -10.2 - 4.25 * math.sin(f)))
        tx, tz = -11.4 * math.sin(f), -4.25 * math.cos(f)
        hd = math.degrees(math.atan2(-tz, tx))
        hh = 1.15 + 0.12 * (k % 3)
        B.p("Kerb", (3.9, hh, 1.4), p + (0, hh / 2 - 0.05, 0), G.ry(hd) @ G.rx(5 * (-1) ** k), ROCK[k % 3],
            solid=True)
    # lava bombs about the foot and on the steps, rocks
    lava_bomb(B, (17.4, 0.0, -12.6), 1.4, 20.0)
    lava_bomb(B, nose(1, 12.4) + (0, -0.04, 0.9), 1.2, 60.0)
    lava_bomb(B, nose(3, -8.6) + (0, -0.04, 0.7), 1.0, 10.0)
    rock(B, (-19.6, 0.0, -8.4), 2.8, (ROCK[1], ROCK[2], ROCK[0]), solid=True)
    rock(B, (19.0, 0.0, -9.6), 3.0, (ROCK[2], ROCK[1], ROCK[3]), solid=True)
    rock(B, (13.4, 0.0, -13.6), 1.5, (ROCK[0], ROCK[2], ROCK[1]))
    # the potato in its fire-proof suit, ladling lava
    suited_spud(B, (-14.6, 0.0, -11.8), 4.4, -34.0, (-9.6, 0.1, -11.8))
    return B.finish()


# ==================================================================== props

def spike(B, base, h, w, heading, lean, cols, name="Spike"):
    """A rock spike: four blocks stacked along a leaning axis, narrowing to a point, each turned 45
    degrees from the last; dark at the foot, red-brown at the tip."""
    R0 = G.ry(heading) @ G.rx(lean)
    base = np.asarray(base, float) - (0, w * 0.5 * math.sin(math.radians(abs(lean))) + 0.05, 0)
    out, y = [], 0.0
    for k, (fh, fw) in enumerate(((0.4, 1.0), (0.28, 0.7), (0.2, 0.44), (0.12, 0.22))):
        hh = h * fh
        out.append(B.p(name, (w * fw, hh + 0.12, w * fw * 0.9), base + R0 @ (0, y + hh / 2, 0),
                       R0 @ G.ry(45.0 * k + 6.0 * k), cols[min(k, 2)]))
        y += hh
    return out


def p_spikes(sc, parent):
    B = Build(sc, parent, "RockSpikes", seed=221)
    rock(B, (0.2, 0.0, 0.3), 3.4, (ROCK[0], ROCK[1], ROCK[2]))
    for k, (x, z, h, w, hd, lean) in enumerate(((0.0, 0.2, 9.4, 2.6, 10.0, 5.0), (2.0, 0.6, 6.4, 2.0, 80.0, 15.0),
                                                (-1.9, 0.1, 5.6, 1.9, -70.0, 14.0), (0.6, -1.7, 3.8, 1.6, 170.0, 20.0),
                                                (-1.2, 1.9, 4.6, 1.6, 20.0, -13.0))):
        spike(B, (x, 0.0, z), h, w, hd, lean, (ROCK[k % 2], BASALT[1 + k % 2], BASALT[3]))
    rock(B, (2.9, 0.0, -1.6), 1.2, (ROCK[1], ROCK[2], ROCK[0]))
    return B.finish()


def p_stump(sc, parent):
    B = Build(sc, parent, "CharredStump", seed=222)
    for k in range(5):                                                    # thick roots into the ground
        a = math.radians(20 + 72 * k + 10 * (-1) ** k)
        d = np.array((math.sin(a), 0.0, -math.cos(a)))
        bar(B, "Root", d * 1.0 + (0, 1.1, 0), d * (2.8 + 0.25 * (k % 2)) + (0, 0.12, 0), 0.85, (CHAR[0], WOOD[0])[k % 2],
            t=0.7, n=(0, 1, 0))
    # the trunk: two crossing blocks, burnt brown under black char
    c1, R1 = np.array((0.0, 1.8, 0.0)), ori(0, 15, 2)
    B.p("Stump", (2.8, 3.6, 2.5), c1, R1, CHAR[1])
    B.p("Stump", (2.4, 3.5, 2.9), (0.0, 1.75, 0.0), ori(0, 62, -2), WOOD[1])
    with B.at(CF(c1, R1)):
        crack(B, [(0.65, 1.4, -1.25), (1.0, 0.6, -1.25), (0.6, -0.2, -1.25), (0.95, -1.4, -1.25)], (0, 0, -1),
              w=0.22, flicker=0.2)
    # snapped off: a tall splinter on one side, shorter teeth round the rest
    B.p("Stump", (1.3, 2.8, 1.0), (0.75, 4.8, 0.55), ori(-6, 20, -8), WOOD[2])
    B.p("Stump", (0.7, 1.5, 0.6), (0.98, 6.6, 0.62), ori(4, 50, -14), WOOD[1])
    for k, (x, z, hh, w) in enumerate(((-1.0, -0.6, 1.1, 0.9), (0.2, -1.0, 0.7, 1.0), (-0.9, 0.8, 0.8, 0.8))):
        B.p("Stump", (w, hh, w * 0.8), (x, 3.5 + hh / 2, z), ori(9 * (-1) ** k, 30 * k + 10, 7),
            (CHAR[2], WOOD[0], CHAR[3])[k])
    B.p("Stump", (1.8, 0.24, 1.7), (-0.2, 3.62, -0.1), G.ry(40), "4a4246")                   # grey ash on top
    neon(B, "Ember", (1.0, 0.2, 0.9), (-0.3, 3.72, -0.15), G.ry(12), LAVA[0], flicker=0.25)  # smouldering
    bar(B, "Branch", (-1.0, 2.6, -0.2), (-2.6, 3.7, -0.5), 0.7, CHAR[2], over=0.1)          # a stub of a branch
    for k, (dx, y, dz, s) in enumerate(((-0.5, 4.6, -0.2, 0.9), (-1.0, 5.6, -0.1, 1.25))):  # a wisp of smoke
        B.p("Smoke", (s, s * 0.8, s), (dx, y, dz), ori(14, 25 * k, 10), SMOKE[2 + k])
    # the top of the tree, fallen beside it, its broken end still glowing
    R = G.ry(-28)
    c = np.array((2.8, 0.85, 2.0))
    B.p("Log", (5.2, 1.7, 1.7), c, R, CHAR[1])
    B.p("Log", (5.1, 1.7, 1.7), c, R @ G.rx(45), WOOD[1])
    neon(B, "Ember", (0.12, 1.2, 1.2), c + R @ (-2.62, 0, 0), R @ G.rx(45), LAVA[0], flicker=0.2)
    bar(B, "Log", c + R @ (0.8, 0.6, 0.3), c + R @ (1.6, 2.4, 0.9), 0.55, CHAR[3])
    return B.finish()


def p_vent(sc, parent):
    B = Build(sc, parent, "SteamVent", seed=223)
    B.p("Mound", (4.8, 0.7, 4.2), (0.0, 0.35, 0.0), G.ry(10), ROCK[1])
    B.p("Mound", (3.9, 0.76, 4.9), (0.0, 0.38, 0.0), G.ry(55), ROCK[0])
    for k in range(7):                                                      # a ring of rocks, leaning out
        a = 2 * math.pi * k / 7 + 0.2
        p = np.array((1.6 * math.cos(a), 1.2, 1.6 * math.sin(a)))
        hd = math.degrees(math.atan2(-math.cos(a), -math.sin(a)))
        hh = 1.2 + 0.25 * (k % 3)
        B.p("Ring", (1.55, hh, 0.95), p + (0, hh / 2 - 0.5, 0), G.ry(hd) @ G.rx(-14), (ROCK[2], BASALT[1],
                                                                                    ROCK[3])[k % 3])
    neon(B, "Glow", (2.3, 0.3, 2.3), (0.0, 1.0, 0.0), G.ry(20), LAVA[0], flicker=0.2)
    neon(B, "Glow", (1.3, 0.38, 1.3), (0.0, 1.06, 0.0), G.ry(65), LAVA[3], flicker=0.3)
    B.p("Steam", (1.2, 1.1, 1.2), (0.0, 2.1, 0.0), ori(8, 20, 6), STEAM[0])                  # steam billowing up
    puff(B, (0.2, 3.1, 0.1), 1.8, STEAM, heading=15.0, name="Steam")
    puff(B, (0.7, 4.9, 0.3), 2.4, (STEAM[1], STEAM[2], STEAM[2]), heading=50.0, name="Steam")
    return B.finish()


def slab(B, base, size, R, col, name="Obsidian", edges=("top",)):
    """A slab of obsidian standing on base (its foot sunk a little) turned by R, a glossy lighter
    bar along the edges asked for."""
    w, h, t = size
    c = np.asarray(base, float) + R @ (0, h / 2 - 0.25, 0)
    out = [B.p(name, size, c, R, col)]
    if "top" in edges:
        out.append(B.p(name, (w - 0.2, 0.2, 0.22), c + R @ (0, h / 2 - 0.08, -t / 2 + 0.09), R, SHEEN[0]))
    if "side" in edges:
        out.append(B.p(name, (0.22, h - 0.6, 0.2), c + R @ (-w / 2 + 0.09, -0.1, -t / 2 + 0.08), R, SHEEN[0]))
    return out


def p_obsidian(sc, parent):
    B = Build(sc, parent, "ObsidianSlabs", seed=224)
    B.p("Rubble", (5.4, 0.5, 3.8), (0.2, 0.25, 0.3), G.ry(12), ROCK[0])
    Ra = G.ry(8) @ G.rx(9)
    slab(B, (-0.3, 0.0, 0.9), (3.8, 6.0, 1.3), Ra, OBSIDIAN[1], edges=("top", "side"))
    slab(B, (2.2, 0.0, 0.2), (2.6, 4.4, 1.1), G.ry(-34) @ G.rz(-17), OBSIDIAN[2])
    slab(B, (-2.4, 0.0, 1.1), (2.0, 3.4, 0.9), G.ry(28) @ G.rz(15), OBSIDIAN[3], edges=("side",))
    B.p("Obsidian", (2.2, 2.2, 2.2), (-1.9, 1.0, -0.6), ori(18, 35, 22), OBSIDIAN[0])          # a block, half sunk
    B.p("Obsidian", (3.2, 0.7, 2.1), (0.9, 0.35, -1.5), ori(3, 25, -3), OBSIDIAN[3])          # a slab lying flat
    B.p("Obsidian", (2.4, 0.2, 0.22), (0.9, 0.78, -2.45), ori(3, 25, -3), SHEEN[0])
    cA = np.array((-0.3, 0.0, 0.9)) + Ra @ (0, 2.75, 0)
    B.p("Sheen", (0.26, 2.8, 0.1), cA + Ra @ (0.6, 0.4, -0.7), Ra @ G.rz(-24), SHEEN[1])      # a glint on the big one
    for k, (x, z, s) in enumerate(((-2.9, -1.7, 0.8), (3.2, -1.3, 0.7))):                   # chips
        B.p("Chip", (s, s * 0.7, s * 0.8), (x, s * 0.3, z), ori(20, 40 * k, 15), OBSIDIAN[k + 1])
    return B.finish()


def bone(B, a, b, w, col=BONE[0], name="Bone"):
    """A bone from a to b: a shaft and a knob at each end."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    k = w * 1.8
    out = [bar(B, name, a, b, w, col)]
    d = (b - a) / np.linalg.norm(b - a)
    for e, s in ((a, 1), (b, -1)):
        out.append(B.p(name, (k, k * 0.8, k), e + d * s * k * 0.15, ori(0, 30, 45), BONE[3]))
    return out


def p_bones(sc, parent):
    B = Build(sc, parent, "BonePile", seed=225)
    B.p("Ash", (5.6, 0.2, 4.2), (0.3, 0.1, 0.2), G.ry(8), "48424c")
    # a horned skull looking at the lane
    sk = np.array((-0.6, 1.25, -0.2))
    R = G.ry(-12) @ G.rx(-8)
    B.p("Skull", (2.2, 1.7, 1.9), sk, R, BONE[0])
    B.p("Skull", (1.5, 1.1, 1.4), sk + R @ (0, -0.42, -1.2), R, BONE[2])
    B.p("Skull", (2.4, 0.5, 1.6), sk + R @ (0, 0.82, 0.1), R, BONE[1])
    for sx in (-1, 1):
        B.plate("Skull", (0.52, 0.5, 0.1), sk + R @ (sx * 0.5, 0.2, -0.99), R, col="2a2226")
        B.plate("Skull", (0.2, 0.26, 0.1), sk + R @ (sx * 0.28, -0.55, -1.94), R, col="2a2226")
        h0 = sk + R @ (sx * 1.0, 0.6, 0.1)
        h1 = h0 + R @ (sx * 1.0, 0.4, 0.0)
        bar(B, "Horn", h0, h1, 0.5, BONE[3], over=0.15)
        bar(B, "Horn", h1, h1 + R @ (sx * 0.3, 1.0, -0.2), 0.38, BONE[1], over=0.1)
    # bones crossed about it
    bone(B, (1.0, 0.32, -1.2), (3.0, 0.34, 0.2), 0.42)
    bone(B, (0.6, 0.62, 0.9), (2.9, 0.3, 1.6), 0.4, col=BONE[2])
    bone(B, (-3.0, 0.3, 0.8), (-1.2, 0.33, 1.9), 0.38)
    for k in range(3):                                                          # a few ribs
        x = 1.4 + 0.6 * k
        bar(B, "Rib", (x, 0.25, -0.3 + 0.1 * k), (x + 0.4, 1.0 - 0.15 * k, -1.6), 0.28, BONE[k % 2], t=0.3)
    return B.finish()


def p_pool(sc, parent):
    B = Build(sc, parent, "LavaPool", seed=226)
    neon(B, "Pool", (5.4, 0.3, 4.2), (0.0, 0.15, 0.0), G.ry(8), LAVA[0], flicker=0.1)
    neon(B, "Pool", (4.2, 0.36, 5.2), (0.0, 0.18, 0.0), G.ry(-6), LAVA[1], flicker=None)
    neon(B, "Pool", (3.8, 0.42, 3.8), (0.0, 0.21, 0.0), G.ry(45), LAVA[1], flicker=0.15)
    neon(B, "Pool", (1.8, 0.5, 1.4), (-0.5, 0.25, 0.4), G.ry(20), LAVA[3], flicker=0.25)
    neon(B, "Bubble", (0.7, 0.5, 0.7), (1.0, 0.45, -0.6), ori(0, 30, 0), LAVA[2], flicker=0.3)
    B.p("Crust", (1.2, 0.2, 0.9), (0.6, 0.52, 0.9), ori(4, 40, -3), ROCK[1])
    for k in range(9):                                                       # the kerb of rocks round it
        a = 2 * math.pi * k / 9 + 0.15
        p = np.array((3.25 * math.cos(a), 0.0, 2.8 * math.sin(a)))
        hd = math.degrees(math.atan2(-2.8 * math.cos(a), -3.25 * math.sin(a)))
        hh = 0.9 + 0.18 * (k % 3)
        B.p("Kerb", (2.4, hh, 1.1), p + (0, hh / 2 - 0.05, 0), G.ry(hd) @ G.rx(6 * (-1) ** k), ROCK[k % 4])
    return B.finish()


def p_boulder(sc, parent):
    B = Build(sc, parent, "MagmaBoulder", seed=227)
    c0, R0 = np.array((0.0, 1.75, 0.0)), ori(5, 20, -4)
    B.p("Boulder", (2.9, 2.4, 3.1), (1.7, 1.15, 0.7), ori(-8, 52, 10), ROCK[2])                  # lumps round it
    B.p("Boulder", (2.5, 2.1, 2.7), (-1.8, 1.0, 0.6), ori(10, -16, 8), ROCK[0])
    B.p("Boulder", (2.9, 1.3, 2.7), (0.2, 3.4, 0.3), ori(-6, 64, 6), ROCK[3])
    with B.at(CF(c0, R0)):                                       # the big one, split by glowing cracks
        B.p("Boulder", (4.6, 3.5, 4.0), (0, 0, 0), None, ROCK[1])
        crack(B, [(-0.9, 1.6, -2.0), (-0.3, 0.7, -2.0), (-0.95, -0.1, -2.0), (-0.4, -1.5, -2.0)], (0, 0, -1),
              w=0.32, flicker=0.2)
        crack(B, [(-0.3, 0.7, -2.0), (0.6, 0.3, -2.0), (1.5, 0.75, -2.0)], (0, 0, -1), w=0.26, flicker=None,
              lift=0.07)
        crack(B, [(2.3, 1.2, -1.2), (2.3, 0.2, -0.4), (2.3, -0.4, -1.0), (2.3, -1.4, -0.5)], (1, 0, 0), w=0.28,
              flicker=0.25)
    neon(B, "Ember", (0.8, 0.3, 0.7), (-2.6, 0.15, -1.9), G.ry(30), LAVA[0], flicker=0.3)
    neon(B, "Ember", (0.5, 0.24, 0.6), (1.6, 0.12, -2.7), G.ry(70), LAVA[2], flicker=0.3)
    rock(B, (3.6, 0.0, -1.6), 1.3, (ROCK[2], ROCK[0], ROCK[1]))
    return B.finish()


def p_firepit(sc, parent):
    B = Build(sc, parent, "FirePit", seed=228)
    for k in range(8):                                                       # a ring of stones
        a = 2 * math.pi * k / 8
        p = np.array((1.9 * math.cos(a), 0.0, 1.9 * math.sin(a)))
        s = 0.9 + 0.12 * (k % 3)
        B.p("Stone", (s * 1.2, s * 0.8, s), p + (0, s * 0.36, 0), ori(6, -math.degrees(a), -5), ROCK[1 + k % 3])
    for k in range(3):                                                       # charred logs, crossed
        a = math.radians(30 + 120 * k)
        d = np.array((math.cos(a), 0.0, math.sin(a)))
        bar(B, "Log", d * 1.2 + (0, 0.3, 0), -d * 0.3 + (0, 1.2, 0), 0.5, ("4a2e1e", "3a2418", "5a3a24")[k],
            t=0.52 + 0.03 * k)
    neon(B, "Embers", (1.5, 0.2, 1.5), (0.0, 0.1, 0.0), G.ry(20), LAVA[0], flicker=0.25)
    flame(B, (0.0, 1.6, 0.0), 1.1)
    flame(B, (0.45, 1.25, 0.3), 0.7)
    # a spit across it with a potato baking in foil
    for sx in (-1, 1):
        B.p("Spit", (0.3, 3.3, 0.3), (sx * 2.4, 1.65, 0.0), None, CHAR[2])
        B.p("Spit", (0.24, 0.7, 0.26), (sx * 2.4 - 0.18, 3.4, 0.0), G.rz(25), CHAR[2])
        B.p("Spit", (0.24, 0.7, 0.34), (sx * 2.4 + 0.18, 3.4, 0.0), G.rz(-25), CHAR[3])
    B.p("Spit", (5.4, 0.18, 0.18), (0.0, 3.3, 0.0), None, IRON[1])
    round3(B, "Foil", (0.0, 3.3, 0.0), 2.3, 1.6, 1.7, (SUIT[0], SUIT[1], SUIT[2]))
    B.p("Foil", (0.5, 0.3, 0.5), (0.7, 4.1, -0.1), ori(10, 30, 20), SUIT[2])                   # a crimp of foil
    return B.finish()


def p_sign(sc, parent):
    B = Build(sc, parent, "WarningSign", seed=229)
    for sx in (-1, 1):                                                     # two posts on wider bases
        B.p("Post", (0.9, 5.4, 0.9), (sx * 2.4, 2.7, 0.0), None, BASALT[1])
        B.p("Post", (1.5, 0.6, 1.5), (sx * 2.4, 0.3, 0.0), None, ROCK[1])
    B.p("Header", (6.0, 0.9, 0.7), (0.0, 5.6, 0.0), None, HAZARD[0])          # hazard stripes on the header
    for k in range(4):
        B.p("Header", (0.45, 1.0, 0.1), (-2.1 + 1.4 * k, 5.6, -0.39), G.rz(35), HAZARD[1], material="SmoothPlastic",
            shadow=False)
    B.plate("Panel", (3.9, 3.6, 0.2), (0.0, 3.1, 0.0), col="241e28")           # the dark panel
    B.plate("Panel", (2.5, 2.5, 0.1), (0.0, 3.1, -0.14), G.rz(45), col=HAZARD[1])
    B.plate("Panel", (2.1, 2.1, 0.1), (0.0, 3.1, -0.18), G.rz(45), col=HAZARD[0])
    B.plate("Panel", (0.32, 1.1, 0.1), (0.0, 3.35, -0.22))                     # an exclamation mark
    B.plate("Panel", (0.34, 0.32, 0.1), (0.0, 2.48, -0.22))
    neon(B, "Drip", (0.5, 0.9, 0.3), (1.2, 4.7, -0.36), ori(0, 0, 8), LAVA[1], flicker=0.2)  # lava dripped on it
    B.p("Scorch", (2.8, 0.12, 2.0), (0.6, 0.06, -0.9), G.ry(14), "26222a")
    return B.finish()


def p_cooled(sc, parent):
    B = Build(sc, parent, "CooledLava", seed=230)
    for k, (x, z, w, d, h, hd) in enumerate(((0.0, 0.0, 3.6, 2.8, 0.7, 10.0), (2.4, 0.8, 2.6, 2.2, 0.5, 40.0),
                                             (-2.3, 0.5, 2.8, 2.0, 0.56, -20.0), (0.8, -1.8, 2.4, 1.8, 0.44, 70.0),
                                             (-1.2, 1.9, 2.2, 1.6, 0.4, 25.0), (2.9, -1.2, 1.6, 1.4, 0.36, -35.0))):
        B.p("Crust", (w, h, d), (x, h / 2, z), ori(2 * (-1) ** k, hd, -2 * (-1) ** k), ROCK[k % 4])
        if k < 4:                                                           # ropy folds on top
            B.p("Crust", (w * 0.6, h * 0.5, d * 0.35), (x + 0.1, h + h * 0.18, z - 0.1), ori(0, hd + 15, 3),
                ROCK[(k + 1) % 4])
    crack(B, [(-1.3, 0.72, -0.6), (0.0, 0.72, -0.1), (1.0, 0.72, 0.5)], (0, 1, 0), w=0.22, col=LAVA[0],
          flicker=0.3)
    neon(B, "Glow", (0.5, 0.2, 0.6), (-0.6, 0.62, -1.15), G.ry(20), EMBER, flicker=0.3)
    return B.finish()


AREA = register(Area("Lava", "Lava Furrows", hero, [
    (p_spikes, prop_attrs(6, 0.85, 1.3, "Side", True)),
    (p_stump, prop_attrs(5, 0.85, 1.25, "Side", True)),
    (p_vent, prop_attrs(5, 0.9, 1.3, "Side", False)),
    (p_obsidian, prop_attrs(4, 0.9, 1.3, "Edge", True)),
    (p_bones, prop_attrs(6, 0.8, 1.2, "Any", False)),
    (p_pool, prop_attrs(4, 0.9, 1.3, "Side", False)),
    (p_boulder, prop_attrs(5, 0.85, 1.3, "Side", True)),
    (p_firepit, prop_attrs(3, 0.9, 1.15, "Side", False)),
    (p_sign, prop_attrs(3, 0.95, 1.15, "Side", True)),
    (p_cooled, prop_attrs(8, 0.8, 1.4, "Any", False)),
], ground="3c383e"))
