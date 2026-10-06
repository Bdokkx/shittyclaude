"""Terraced islands: keeps the SHAPE of the original generated islands (gen/island.py: terraces,
spiral stair path to the summit, mesas, arch, dock spot, plaza) and rebuilds every surface in the
reef-target style from the prompt pack:

* ground tops: one base colour + one patch colour in big soft patches (no per-block noise)
* cliffs: runs of big slabs (8-16 wide, 2.5-6 thick, tilted, overhanging) coloured by height band,
  with one continuous grass lip + sand strip on top
* no scattered clutter: trees in clumps, flowers/bushes only in clusters at path edges and rock bases
* new gameplay buildings (Fish Market, Spear Shop, Upgrade Station), landmark, T-dock, travel boat,
  shallow reef ring, Tier1/Tier2/Tier3
"""
import math
import os
import random
import sys
from collections import deque

import buildings as Bd
import props as P
from core import Model
from terrain import greedy, noise2, slab_stack

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "gen"))
from island import build_island as old_island  # noqa: E402

DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


class Grid:
    """Cell heights + kinds from the original generator."""

    def __init__(self, theme):
        self.old = old_island(theme)
        o = self.old
        self.N, self.S = o["N"], o["cell"]
        dbg = o["debug"]
        self.path = dbg["path"]
        self.plaza = set(dbg["plaza"])
        self.top, self.kind, self.surf = {}, {}, {}
        for i, j, top, kind, surf in o["mesh_cells"]:
            c = (i, j)
            self.kind[c] = kind
            self.surf[c] = surf
            # path steps rounded to half studs so runs of equal steps merge into one tile
            self.top[c] = round(self.path[c][0] * 2) / 2 if kind == "path" and c in self.path else top
        self.props = o["props"]
        self.landmarks = o["landmarks"]

    def wx(self, i):
        return (i - self.N / 2 + 0.5) * self.S

    def cell_of(self, x, z):
        return (int(math.floor(x / self.S + self.N / 2)), int(math.floor(z / self.S + self.N / 2)))

    def top_at(self, x, z):
        return self.top.get(self.cell_of(x, z))


def ground_and_cliffs(m, g, C, seed, water_levels):
    """Tops, hidden bodies and slab cliffs for every land / beach / path cell, then the sea shelves."""
    S = g.S
    rng = random.Random(seed)

    def top_color(c):
        k, s = g.kind[c], g.surf[c]
        x, z = g.wx(c[0]), g.wx(c[1])
        if k == "path":
            style = g.path[c][1] if c in g.path else "cobble"
            if c in g.plaza:
                return C["path_border"]
            if style == "wood":       # plank stripes run across the stair, alternating per step
                return C["wood"] if int(round(g.top[c] * 2)) % 2 else C["wood_dark"]
            return C["path"]
        if k == "beach":
            return C["sand2"] if noise2(x, z, seed + 1, 48) > 0.64 else C["sand"]
        return C["grass2"] if noise2(x, z, seed + 2, 52) > 0.62 else C["grass"]

    def is_edge(c):
        """Cell at the top of a visible cliff: its sides need rock colour under the top tile."""
        t = g.top[c]
        return g.kind[c] != "path" and any(g.top.get((c[0] + d[0], c[1] + d[1]), -9) < t - 1.5 for d in DIRS)

    edge = {c: False for c in g.top}     # cliff faces are covered by the slab runs: one solid part per tile
    tops = {c: (round(g.top[c], 2), top_color(c), edge[c]) for c in g.top}
    with m.ctx(stage="terrain", folder="Terrain"):
        for i0, j0, i1, j1, (t, col, e) in greedy(tops):
            # interior cells and stair steps are one solid part; cliff-edge cells get a 1-stud top + rock body
            m.span((g.wx(i0) - S / 2, (t - 1) if e else -2.0, g.wx(j0) - S / 2),
                   (g.wx(i1) + S / 2, t, g.wx(j1) + S / 2), col)
        bodies = {c: round(g.top[c], 2) for c in g.top if edge[c]}
        for i0, j0, i1, j1, t in greedy(bodies):
            m.span((g.wx(i0) - S / 2, -2.0, g.wx(j0) - S / 2), (g.wx(i1) + S / 2, t - 1, g.wx(j1) + S / 2),
                   C["rock_dark"], shadow=False)

    # sea: distance from land in cells -> shelf1 / shelf2 / floor
    N = g.N
    dist = {}
    q = deque()
    for c in g.top:
        dist[c] = 0
        q.append(c)
    while q:
        c = q.popleft()
        if dist[c] >= 200:
            continue
        for d in DIRS:
            nb = (c[0] + d[0], c[1] + d[1])
            if nb not in dist and -4 <= nb[0] < N + 4 and -4 <= nb[1] < N + 4:
                dist[nb] = dist[c] + 1
                q.append(nb)
    levels = {}
    for c, dd in dist.items():
        if dd == 0:
            continue
        levels[c] = water_levels[0] if dd <= 2 else water_levels[1] if dd <= 5 else water_levels[2]
    sea_cells = {}
    for c, lv in levels.items():
        x, z = g.wx(c[0]), g.wx(c[1])
        if lv == water_levels[0]:      # the shallow shelf you see from the dock keeps soft sand patches
            tone = C["sand2"] if noise2(x, z, seed + 4, 30) > 0.62 else C["sand"]
        else:
            tone = C["sea_sand"]
        sea_cells[c] = (lv, tone)
    with m.ctx(stage="reef", folder="Reef"):
        for i0, j0, i1, j1, (lv, col) in greedy(sea_cells):   # one solid part per shelf rectangle
            m.span((g.wx(i0) - S / 2, water_levels[2] - 1, g.wx(j0) - S / 2),
                   (g.wx(i1) + S / 2, lv, g.wx(j1) + S / 2), col)
        # open sea floor beyond the grid
        lo, hi = g.wx(-4) - S / 2, g.wx(N + 3) + S / 2
        for a, b in (((-400, -400), (400, lo)), ((-400, hi), (400, 400)), ((-400, lo), (lo, hi)), ((hi, lo), (400, hi))):
            m.span((a[0], water_levels[2] - 1, a[1]), (b[0], water_levels[2], b[1]), C["sea_sand"])

    def height(c):
        if c in g.top:
            return g.top[c]
        return levels.get(c, water_levels[2])

    # ---- cliff edges -> runs of slabs
    edges = {}
    for c, t in g.top.items():
        for d in DIRS:
            nb = (c[0] + d[0], c[1] + d[1])
            t2 = height(nb)
            if t - t2 < 1.6:
                continue
            if g.kind[c] == "path" and g.kind.get(nb) == "path":
                continue          # stair steps on the path show as steps
            edges[(c, d)] = round(t2, 1)
    done = set()
    runs = []

    def rkey(c):
        return (round(g.top[c], 2), g.kind[c] if g.kind[c] != "land" else g.surf[c])

    for (c, d) in sorted(edges):
        if (c, d) in done:
            continue
        u = (abs(d[1]), abs(d[0]))
        key = rkey(c)
        start = c
        while True:
            pc = (start[0] - u[0], start[1] - u[1])
            if (pc, d) in edges and (pc, d) not in done and rkey(pc) == key:
                start = pc
            else:
                break
        run, cur = [], start
        while (cur, d) in edges and (cur, d) not in done and rkey(cur) == key:
            run.append(cur)
            done.add((cur, d))
            cur = (cur[0] + u[0], cur[1] + u[1])
        runs.append((d, run, key))

    with m.ctx(stage="terrain", folder="Terrain"):
        for d, run, (t, kind) in runs:
            k = 0
            while k < len(run):
                n = 4 if len(run) - k >= 6 else len(run) - k   # 16-stud slabs, no slivers at the end
                seg = run[k:k + n]
                k += n
                t2 = min(edges[(c, d)] for c in seg)
                cx = sum(g.wx(c[0]) for c in seg) / n + d[0] * S / 2
                cz = sum(g.wx(c[1]) for c in seg) / n + d[1] * S / 2
                w = n * S + 1.6
                c0 = seg[0]
                if kind == "beach":
                    lip, strip, bands = C["sand"], None, (C["sand"], C["sand2"], C["sand2"])
                elif kind == "path":
                    lip, strip, bands = tops[c0][1], None, (C["rock_light"], C["rock"], C["rock_dark"])
                else:
                    lip, strip, bands = C["grass"], C["sand"], (C["rock_light"], C["rock"], C["rock_dark"])
                slab_face(m, cx, cz, d, w, t, t2, lip, strip, bands, rng)
    return levels, height


def slab_face(m, cx, cz, d, w, y_top, y_low, lip, strip, bands, rng, inward=3.0):
    ry = math.degrees(math.atan2(d[0], d[1]))
    with m.at((cx, 0, cz), ry=ry):        # local +Z points out of the cliff
        o = rng.uniform(0.6, 1.4)
        jit = rng.uniform(-0.03, 0.03)
        m.span((-w / 2, y_top - 0.8 + jit, -inward), (w / 2, y_top + 0.2 + jit, o), lip)
        y = y_top - 0.8
        if strip and y_top - y_low >= 4:
            m.span((-w / 2 + 0.15, y - 0.9, -inward), (w / 2 - 0.15, y, o - 0.4), strip)
            y -= 0.9
        height = y_top - y_low
        if height <= 5.5:      # low step: one slab fills everything under the lip (nothing floats)
            m.span((-w / 2 + 0.2, y_low - 0.6, -inward), (w / 2 - 0.2, y, max(0.3, o - 0.25)), bands[1])
            return
        k = 0
        while y > y_low - 0.4:
            th = min(rng.uniform(4.5, 6.0), y - (y_low - 1.0))
            if th < 0.5:
                break
            yc = y - th / 2
            f = (yc - y_low) / max(height, 1e-3)
            col = bands[0] if f > 0.62 else bands[1] if f > 0.28 else bands[2]
            out = rng.uniform(0.0, 1.6) if k else max(0.3, o - 0.25)     # first layer always under the lip
            ww = w + rng.uniform(-1.2, 0.8)
            with m.at((rng.uniform(-0.8, 0.8), yc, 0), rx=rng.uniform(3, 10) * rng.choice((-1, 1)),
                      rz=rng.uniform(-2.5, 2.5)):
                m.span((-ww / 2, -th / 2, -inward), (ww / 2, th / 2, max(0.3, out)), col)
            y -= th
            k += 1


def find_spot(g, center, r, level, avoid, prefer=None, rmin=26, rmax=80, taken=()):
    """Flat land spot (all cells within r at `level`, not path) near `center`."""
    best = None
    for c, t in g.top.items():
        if abs(t - level) > 0.3 or g.kind[c] != "land":
            continue
        x, z = g.wx(c[0]), g.wx(c[1])
        dd = math.hypot(x - center[0], z - center[1])
        if not rmin <= dd <= rmax:
            continue
        if any(math.hypot(x - a, z - b) < rr + r for (a, b), rr in avoid):
            continue
        if any(math.hypot(x - a, z - b) < 30 for a, b in taken):
            continue
        ok = True
        rc = int(math.ceil(r / g.S))
        for a in range(-rc, rc + 1):
            for b in range(-rc, rc + 1):
                if math.hypot(a, b) * g.S > r:
                    continue
                cc = (c[0] + a, c[1] + b)
                if cc not in g.top or abs(g.top[cc] - level) > 0.3 or g.kind[cc] != "land":
                    ok = False
                    break
            if not ok:
                break
        if not ok:
            continue
        score = dd + (prefer(x, z) if prefer else 0)
        if best is None or score < best[0]:
            best = (score, (x, z))
    return best[1] if best else None


def fence(m, x, y, z, ry, wood, dark):
    with m.at((x, y, z), ry=ry):
        for s in (-1.8, 1.8):
            m.box((s, 1.6, 0), (0.6, 3.2, 0.6), dark)
        m.box((0, 2.4, 0), (4.2, 0.6, 0.35), wood)


def rowboat(m, wood, dark, stripe):
    m.box((0, -0.5, 0), (2.2, 1.0, 8.0), dark)
    for s in (-1, 1):
        m.box((s * 1.6, 0.3, 0), (0.7, 1.6, 7.6), wood)
        m.box((s * 0.9, 0.3, -4.1), (1.4, 1.6, 1.4), wood, ry=s * 30)
    m.box((0, 0.3, 3.9), (3.6, 1.6, 0.6), wood)
    m.box((0, 1.15, 0), (3.9, 0.3, 7.4), stripe, collide=False)
    m.box((0, 0.6, 0.8), (2.6, 0.4, 1.0), dark)
    for s in (-1, 1):
        m.box((s * 2.6, 0.9, 0.8), (3.0, 0.3, 0.4), dark, rz=s * 20)


def stair_rails(m, g, C):
    """Wooden stairs (wood-style path cells): a post + rail on every open side of every step, so the
    stair reads as one continuous railed staircase instead of loose fences."""
    for c, (h, style, (dx, dz), dist) in g.path.items():
        if style != "wood" or c not in g.top:
            continue
        t = g.top[c]
        tx, tz = (1, 0) if abs(dx) >= abs(dz) else (0, 1)          # travel axis
        for s in (-1, 1):
            side = (tz * s, tx * s)                                 # perpendicular
            nb = (c[0] + side[0], c[1] + side[1])
            if g.kind.get(nb) == "path":
                continue
            ex = g.wx(c[0]) + side[0] * (g.S / 2 - 0.4)
            ez = g.wx(c[1]) + side[1] * (g.S / 2 - 0.4)
            with m.ctx(stage="dock", folder="Dock"):
                m.box((ex, t + 1.6, ez), (0.7, 3.2, 0.7), C["wood_dark"])
                m.box((ex, t + 3.0, ez), (0.5 + abs(tx) * 3.9, 0.5, 0.5 + abs(tz) * 3.9), C["wood"])
