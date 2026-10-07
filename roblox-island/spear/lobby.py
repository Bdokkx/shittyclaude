"""Lobby island - a rebuild of the uploaded Lobby model (please_make_better.rbxm) in the spear style.

Everything the game scripts can see stays exactly where it was: the Lobby folder, Markers/LobbySpawn,
the SpawnLocation, CoinsBoard / StreakBoard (Board parts with the Leaderboard attribute, Header with the
SurfaceGui text). Those are kept from the original file by tools/export_lobby.luau; this file only builds
the new Island terrain and the Decor folder around them.

Local frame: origin = centre of the plaza on the grass top (world 0, 60, -340); +Z = towards the walk.

Fixed from the original:
  - rails hung past the island edge at both ends -> the fence now follows the rim
  - a flower stood inside a StreakBoard post, a bush inside a tree trunk, bushes overlapping each other
  - lone 1x1 flower bricks -> proper flower clusters on a leafy base
  - Walk and Plaza overlapped with coplanar tops (flicker) -> the walk starts at the plaza trim
  - the rock body had CanCollide off, so players fell into the cliffs -> cliffs collide
"""
import math
import random

import props as P
from core import Model, poly_contains
from terrain import greedy, noise2
from voxel_island import C, PRESET

ORIGIN = (0.0, 60.0, -340.0)
CELL = 4.0
GRASS = ("#6CCB4A", "#5EBE45")
LIP = "#4FA83A"
DIRT = ("#B07A4A", "#9A6238")
BANDS = (C["rock_light"], C["rock"], C["rock_dark"])
SAND = ("#F3E2B6", "#E9D29C")        # plaza tiles
TRIM = "#C9AE78"
STONE = "#B9B4C8"
STONE_DK = "#8E89A0"


def outline(r=49.0, seed=5, amp=0.035, p=3.2, n=160):
    """Rounded-square island rim with a little wobble (the walk side stays straight enough for the fence)."""
    rng = random.Random(seed)
    waves = [(k, rng.uniform(0, 6.283), amp / (1 + 0.5 * k)) for k in range(3, 8)]
    pts = []
    for i in range(n):
        a = i * 2 * math.pi / n
        c, s = math.cos(a), math.sin(a)
        rr = r / (abs(c) ** p + abs(s) ** p) ** (1 / p)
        rr *= 1 + sum(w * math.sin(k * a + ph) for k, ph, w in waves)
        pts.append((c * rr, s * rr))
    return pts


def scale(poly, f, dx=0.0, dz=0.0):
    return [(x * f + dx, z * f + dz) for x, z in poly]


def cells_in(poly):
    out = set()
    for i in range(-16, 16):
        for j in range(-16, 16):
            if poly_contains(poly, (i + 0.5) * CELL, (j + 0.5) * CELL):
                out.add((i, j))
    return out


def fill(m, cells, y0, y1, color_fn, name=None):
    keyed = {c: color_fn(c) for c in cells}
    first = None
    for i0, j0, i1, j1, col in greedy(keyed):
        p = m.span((i0 * CELL, y0, j0 * CELL), ((i1 + 1) * CELL, y1, (j1 + 1) * CELL), col)
        first = first or p
    return first


class Spots:
    """Simple footprint bookkeeping so decor never clips into boards, paths or each other."""

    def __init__(self, rim):
        self.rim = rim
        self.taken = []          # (x, z, r)

    def block(self, x, z, r):
        self.taken.append((x, z, r))

    def block_rect(self, x0, z0, x1, z1):
        step = 2.0
        x = x0
        while x <= x1:
            z = z0
            while z <= z1:
                self.taken.append((x, z, 1.2))
                z += step
            x += step

    def free(self, x, z, r, edge=3.0):
        if not poly_contains(scale(self.rim, 1 - edge / 49.0), x, z):
            return False
        return all(math.hypot(x - a, z - b) >= r + q for a, b, q in self.taken)

    def take(self, x, z, r, edge=3.0):
        if self.free(x, z, r, edge):
            self.block(x, z, r)
            return True
        return False


def kept_parts(m):
    """The original boards (exported as-is from the uploaded file; here only so the renders show them)."""
    with m.ctx(stage="keep", folder="Keep", collide=True):
        for side, head, label in ((-1, "#F5B700", "TOP COINS"), (1, "#F0352B", "TOP STREAKS")):
            cx = 13.0 * side
            for px in (cx - 8.4, cx + 8.4):
                m.box((px, 10.0, -34.0), (1.8, 20.0, 1.8), "#C8743A")
                m.box((px, 1.1, -34.0), (3.0, 2.2, 3.0), "#A0572B")
            m.box((cx, 10.4, -34.0), (15.0, 15.0, 0.8), "#22232B")
            h = m.box((cx, 19.8, -34.0), (18.6, 3.4, 1.8), head)
            m.text(h, label, "#FFFFFF", "Back")


def terrain(m, rim):
    top = cells_in(rim)
    with m.ctx(stage="terrain", folder="Island", tag=None, collide=True):
        # grass top in two tones, a darker lip one cell wider at the rim, then dirt
        def grass(c):
            return GRASS[1] if noise2(c[0] * 4, c[1] * 4, 3, 22) > 0.62 else GRASS[0]
        core = {c for c in top if abs(c[0] + 0.5) < 6 and abs(c[1] + 0.5) < 6}
        g = fill(m, core, -1.2, 0.0, lambda c: GRASS[0])
        g["name"] = "Grass"
        fill(m, top - core, -1.2, 0.0, grass)
        fill(m, top, -2.4, -1.2, lambda c: LIP)
        fill(m, top, -5.0, -2.4, lambda c: DIRT[0] if (c[0] + c[1]) % 3 else DIRT[1])

        # stepped rock body tapering to a point (voxel layers + colour bands)
        layers = [(-5, -10, 0.96, 0), (-10, -16, 0.86, 0), (-16, -23, 0.74, 1), (-23, -31, 0.6, 1),
                  (-31, -40, 0.46, 1), (-40, -50, 0.33, 2), (-50, -61, 0.22, 2), (-61, -74, 0.12, 2)]
        for k, (y1, y0, f, band) in enumerate(layers):
            poly = scale(rim, f, dx=math.sin(k * 1.3) * 2.0, dz=math.cos(k * 0.9) * 2.0)
            cs = cells_in(poly) or {(-1, -1), (0, -1), (-1, 0), (0, 0)}
            fill(m, cs, y0, y1, lambda c, b=band: BANDS[b] if (c[0] * 7 + c[1] * 3) % 5 else BANDS[min(2, b + 1)])
        m.span((-2, -82, -2), (2, -74, 2), BANDS[2])

        # chunky tilted slabs around the cliff so the sides are not plain steps
        rng = random.Random(21)
        n = len(rim)
        for k, (y_mid, f, th) in enumerate(((-7.5, 0.97, 5.0), (-19, 0.79, 5.5), (-34, 0.55, 6.0), (-52, 0.3, 5.0))):
            step = (7, 9, 12, 18)[k]
            for i in range(0, n, step):
                x, z = rim[(i + k * 3) % n]
                a = math.atan2(z, x)
                rr = math.hypot(x, z) * f
                w = rng.uniform(8, 14) * (1.0 if k < 2 else 0.8)
                col = BANDS[min(2, k // 2 + rng.choice((0, 0, 1)))]
                with m.at((math.cos(a) * rr, y_mid + rng.uniform(-1.5, 1.5), math.sin(a) * rr),
                          ry=-math.degrees(a) + 90 + rng.uniform(-12, 12)):
                    m.box((0, 0, 0), (w, th, 4.0), col, rx=rng.uniform(6, 14), rz=rng.uniform(-8, 8))


def plaza(m, sp):
    with m.ctx(stage="terrain", folder="Island", collide=True):
        m.box((0, 0.175, 0), (48, 0.35, 48), TRIM)["name"] = "PlazaTrim"
        m.box((0, 0.3, 0), (44, 0.6, 44), SAND[0])["name"] = "Plaza"
        # walk from the trim edge to the rim (no overlap with the plaza any more)
        m.box((0, 0.3, 35.0), (16, 0.6, 22.0), SAND[0])["name"] = "Walk"
    with m.ctx(stage="props", folder="Decor", tag="PlazaInlay:0", collide=False, shadow=False):
        # checker tiles around the edge of the plaza, a ring + compass in the middle (flat, nothing to trip on)
        for i in range(-5, 6):
            for j in range(-5, 6):
                if max(abs(i), abs(j)) >= 4 and (i + j) % 2 == 0:
                    m.box((i * 4, 0.65, j * 4), (3.6, 0.1, 3.6), SAND[1])
        m.octagon(0.66, 13.0, 0.12, TRIM)
        m.octagon(0.70, 11.6, 0.12, SAND[0])
        m.octagon(0.74, 4.0, 0.12, C["roof"])
        for ry in (0, 90):
            m.box((0, 0.76, 0), (1.6, 0.12, 18.0), C["roof_trim"], ry=ry)
        m.box((0, 0.8, -8.5), (2.6, 0.12, 2.6), "#FFD447", ry=45)           # north marker
        # walk: darker edges + stepping tiles
        for x in (-7.5, 7.5):
            m.box((x, 0.65, 35.0), (1.0, 0.1, 22.0), TRIM)
        for z in range(26, 46, 4):
            m.box((0, 0.65, z), (5.0, 0.1, 2.6), SAND[1])
    sp.block_rect(-26, -26, 26, 26)           # plaza + trim
    sp.block_rect(-10, 22, 10, 50)            # walk


def boards_decor(m, sp, k):
    """Lanterns and a trophy around the leaderboards (the boards themselves are untouched; nothing tall
    stands in front of them so the bottom rows stay readable)."""
    sp.block_rect(-24, -37, 24, -31)
    with m.ctx(stage="props", folder="Decor", tag="BoardTrophy:0"):
        with m.at((0, 0, -34)):
            m.box((0, 0.8, 0), (4.4, 1.6, 4.4), STONE_DK)
            m.box((0, 1.8, 0), (3.6, 0.4, 3.6), STONE)
            m.box((0, 2.6, 0), (1.0, 1.2, 1.0), "#E0A800")
            m.box((0, 4.0, 0), (2.6, 2.0, 2.0), "#FFD447")
            for s in (-1, 1):
                m.box((s * 1.6, 4.3, 0), (0.5, 1.2, 0.5), "#FFD447")
            m.box((0, 5.1, 0), (2.9, 0.3, 2.3), "#FFE58A", collide=False)
            m.box((0, 2.1, 0), (2.0, 0.4, 1.6), "#E0A800")
    for s in (-1, 1):
        with m.ctx(stage="props", folder="Decor", tag="Lantern:%d" % next(k)):
            with m.at((s * 25.0, 0, -32.5), ry=90 if s < 0 else -90):
                P.lantern_post(m, h=9)
        sp.block(s * 25.0, -32.5, 2.5)


def plaza_ring(m, sp, k):
    # lanterns on the plaza corners (outside the 30x30 spawn zone)
    for x in (-21, 21):
        for z in (-21, 21):
            with m.ctx(stage="props", folder="Decor", tag="Lantern:%d" % next(k)):
                with m.at((x, 0.6, z), ry=math.degrees(math.atan2(-x, -z)) + 90):
                    P.lantern_post(m, h=8)
    # benches facing the plaza from east and west, with a planter either side
    for s in (-1, 1):
        for z in (-6, 6):
            with m.ctx(stage="props", folder="Decor", tag="Bench:%d" % next(k)):
                with m.at((s * 28.5, 0, z), ry=90 * s):
                    P.bench(m)
            sp.block(s * 28.5, z, 3.6)
        for z in (-15, 15):
            with m.ctx(stage="props", folder="Decor", tag="Planter:%d" % next(k)):
                with m.at((s * 28.5, 0, z), ry=90):
                    P.planter(m, 60 + z + s, colors=("pink", "yellow", "white"))
            sp.block(s * 28.5, z, 3.2)
    # lanterns along the walk and a pair of stone pillars at the walk end
    for z in (30, 40):
        for s in (-1, 1):
            with m.ctx(stage="props", folder="Decor", tag="Lantern:%d" % next(k)):
                with m.at((s * 10.0, 0, z), ry=180 if s < 0 else 0):
                    P.lantern_post(m, h=8)
            sp.block(s * 10.0, z, 2.0)


def fence(m, rim, sp, k):
    """Fence along the south rim (the old rails stuck out past the island at both ends), gap at the walk."""
    inset = scale(rim, 1 - 2.2 / 49.0)
    south = [(x, z) for x, z in inset if z > 26]
    south.sort(key=lambda p: p[0])
    for side in (-1, 1):
        pts = [p for p in south if p[0] * side > 9.5]
        pts.sort(key=lambda p: abs(p[0]))
        pts = pts[::3] + ([pts[-1]] if (len(pts) - 1) % 3 else [])
        with m.ctx(stage="props", folder="Decor", tag="Fence:%d" % next(k)):
            for a, b in zip(pts, pts[1:]):
                P_rail(m, a, b)
        for x, z in pts:
            sp.block(x, z, 1.5)
    # gate posts at the walk opening
    for s in (-1, 1):
        x, z = s * 9.6, south and max(z for x2, z in south if abs(x2) < 12) or 46
        with m.ctx(stage="props", folder="Decor", tag="GatePost:%d" % next(k)):
            m.box((x, 1.6, z), (2.0, 3.2, 2.0), STONE)
            m.box((x, 3.4, z), (2.4, 0.4, 2.4), STONE_DK)
            m.box((x, 4.1, z), (1.2, 1.0, 1.2), C["lamp"], mat="Neon", light=("PointLight", 1.2, 14, C["lamp"]),
                  collide=False, shadow=False)


def P_rail(m, a, b):
    from buildings import rail_line
    rail_line(m, a, b, 0.0, color=(C["wood"], C["wood_dark"]), every=4.5, h=3.0)


def plants(m, rim, sp, k):
    rng = random.Random(9)
    trees = [  # hand placed: framing the boards, the plaza sides and the walk
        (P.cherry, 1, -38, -30), (P.oak, 2, 37, -31), (P.birch, 1, -42, -12), (P.pine, 1, 42, -14),
        (P.apple, 1, -38, 12), (P.oak, 1, 39, 10), (P.poplar, 1, -18, 40), (P.poplar, 1, 18, 40),
        (P.pine, 0, -30, -42), (P.birch, 0, 30, -42), (P.cherry, 0, 36, 30), (P.birch, 0, -36, 30),
    ]
    for i, (fn, size, x, z) in enumerate(trees):
        if not sp.take(x, z, 4.0, edge=4.0):
            continue
        with m.ctx(stage="props", folder="Decor", tag="Tree:%d" % next(k)):
            with m.at((x, 0, z), ry=rng.uniform(0, 360)):
                fn(m, size, 100 + i)
    # bushes, flower clusters and grass tufts on the free lawn
    cand = [(rng.uniform(-46, 46), rng.uniform(-46, 46)) for _ in range(900)]
    nb = nf = nt = 0
    for x, z in cand:
        if nb < 14 and sp.take(x, z, 3.2, edge=4.0):
            with m.ctx(stage="props", folder="Decor", tag="Bush:%d" % next(k)):
                with m.at((x, 0, z)):
                    P.bush(m, 300 + nb, berry=rng.choice((P.ACCENTS["red"], P.ACCENTS["pink"], None)))
            nb += 1
        elif nf < 18 and sp.take(x, z, 2.2, edge=3.0):
            with m.ctx(stage="props", folder="Decor", tag="Flowers:%d" % next(k)):
                with m.at((x, 0, z)):
                    P.flowers(m, 400 + nf, rng.choice((("red", "yellow"), ("pink", "white"), ("purple", "yellow"),
                                                      ("orange", "red"))))
            nf += 1
        elif nt < 40 and sp.take(x, z, 1.6, edge=2.5):
            with m.ctx(stage="props", folder="Decor", tag="Grass:%d" % next(k)):
                with m.at((x, 0, z)):
                    P.tuft_cluster(m, 500 + nt, flower=rng.choice((None, None, P.ACCENTS["yellow"], P.ACCENTS["white"])))
            nt += 1


def hanging(m, rim, k):
    """Vines and roots hanging from the grass lip, and floating islets below the lobby."""
    rng = random.Random(33)
    with m.ctx(stage="props", folder="Decor", tag="Vines:%d" % next(k), collide=False, shadow=False):
        for i in range(0, len(rim), 5):
            x, z = rim[i]
            a = math.atan2(z, x)
            r = math.hypot(x, z) - 0.6
            L = rng.uniform(3, 9)
            col = rng.choice((LIP, "#3E8F33", "#5EBE45"))
            m.box((math.cos(a) * r, -2.0 - L / 2, math.sin(a) * r), (0.6, L, 0.6), col, ry=-math.degrees(a))
            if rng.random() < 0.4:
                m.box((math.cos(a) * r, -2.0 - L, math.sin(a) * r), (1.2, 1.0, 1.2), col)
    for i, (x, y, z, s) in enumerate(((-62, -30, 24, 1.0), (58, -38, -30, 0.8), (-34, -52, -64, 0.6),
                                      (40, -22, 58, 0.55))):
        with m.ctx(stage="props", folder="Decor", tag="FloatingRock:%d" % next(k), collide=False):
            with m.at((x, y, z), ry=rng.uniform(0, 90)):
                w = 14 * s
                m.box((0, -0.6, 0), (w, 1.2, w * 0.9), GRASS[0])
                m.box((0, -1.6, 0), (w + 0.4, 0.8, w * 0.9 + 0.4), LIP)
                m.box((0, -4.0, 0), (w * 0.9, 4.0, w * 0.8), DIRT[0])
                m.box((0.5, -8.5, 0.3), (w * 0.62, 5.0, w * 0.56), BANDS[1], rx=4)
                m.box((-0.3, -12.5, 0), (w * 0.34, 3.6, w * 0.3), BANDS[2], rz=6)
                if s >= 0.8:
                    with m.at((w * 0.15, 0, 0)):
                        P.pine(m, 0, 700 + i)
                else:
                    with m.at((0, 0, 0)):
                        P.tuft_cluster(m, 720 + i, flower=P.ACCENTS["pink"])


def build():
    m = Model("Lobby")
    rim = outline()
    sp = Spots(rim)
    counter = iter(range(1, 100000))
    with m.at(ORIGIN):
        kept_parts(m)
        terrain(m, rim)
        plaza(m, sp)
        boards_decor(m, sp, counter)
        plaza_ring(m, sp, counter)
        fence(m, rim, sp, counter)
        plants(m, rim, sp, counter)
        hanging(m, rim, counter)
    ox, oy, oz = ORIGIN
    cams = {
        "overview": ((ox + 95, oy + 55, oz + 120), (ox, oy - 10, oz), 32),
        "plaza": ((ox + 0, oy + 14, oz + 62), (ox, oy + 6, oz - 30), 24),
        "boards": ((ox - 26, oy + 8, oz + 8), (ox + 4, oy + 9, oz - 34), 24),
        "under": ((ox - 120, oy - 40, oz + 90), (ox, oy - 25, oz), 32),
    }
    return m, cams


if __name__ == "__main__":
    import json
    import os
    m, cams = build()
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data = dict(name="Lobby", origin=ORIGIN, water=(-400, 0, -800, 400, 0, 100), preset=PRESET, cameras=cams,
                parts=[dict(size=p["size"], pos=p["pos"], R=p["R"], color=p["color"], mat=p["mat"],
                            light=p["light"], stage=p["stage"], folder=p["folder"], tier=p["tier"],
                            tag=p["tag"], collide=p["collide"], shadow=p["shadow"], name=p.get("name"),
                            transparency=p.get("transparency", 0.0), effect=p.get("effect")) for p in m.parts],
                texts=m.texts)
    os.makedirs(os.path.join(root, "build"), exist_ok=True)
    json.dump(data, open(os.path.join(root, "build", "Lobby.json"), "w"))
    print("Lobby: %d parts (%d new)" % (len(m.parts), sum(p["stage"] != "keep" for p in m.parts)))
