"""Themed voxel island engine. One generator, four islands (see themes.py):

  voxel     VoxelIsland     terraced mountain, two mesas, village plaza, dock (the original)
  desert    DesertCoast     red sandstone mesas, oasis lake + waterfall, adobe village, ziggurat
  frost     FrostCoast      snowy mountain, frozen pond + frozen waterfall, log-cabin village, icebergs
  volcanic  VolcanicIsland  volcano with a lava crater and lava rivers/falls, basalt, stilt-hut village

Every island: stepped shallows, wide paths (wooden stairs to the dock, cobbles elsewhere,
spiral path up the big mountain), a rock arch the path walks through, crags half-buried at
cliff feet, sea stacks, trees and clutter everywhere. Cliffs are part facades (swapped for the
deformed Blender terrain mesh by MeshSwap) plus an "Accents" layer of chunky part ledges that
stays on top of the mesh, so meshes and parts blend like in the reference shots.

Output: dict(groups=[(name, boxes)], props=[...], water=..., spawn=..., mesh_cells=..., mats=...)
"""
import math
import random
from collections import deque

from noise import fbm, weighted
from themes import THEMES

CELL = 4
N = 124
K = 1.2       # layout scale (roomy map)
PATH_R = 2.3  # path half-width in cells (~20 studs wide)
BED = -10
BEACH_TOP = 3
TIER = 10
SEA = 600     # half-size of the water/seabed box around each island

DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))
FACING_ROT = {(0, 1): 0, (1, 0): 90, (0, -1): 180, (-1, 0): 270}


def tier_top(t):
    return BEACH_TOP + 1 + TIER * t if t > 0 else BEACH_TOP


def prop(name, x, y, z, rot=0, scale=1, tint=0, rx=0, rz=0):
    return (name, round(x, 2), round(y, 2), round(z, 2), round(rot % 360, 1), round(scale, 2), tint,
            round(rx, 1), round(rz, 1))


def wx(i):
    return (i - N / 2 + 0.5) * CELL


def greedy(grid, w, h):
    used = set()
    rects = []
    for j in range(h):
        for i in range(w):
            key = grid.get((i, j))
            if key is None or (i, j) in used:
                continue
            i1 = i
            while i1 + 1 < w and grid.get((i1 + 1, j)) == key and (i1 + 1, j) not in used:
                i1 += 1
            j1 = j
            while j1 + 1 < h and all(grid.get((k, j1 + 1)) == key and (k, j1 + 1) not in used
                                     for k in range(i, i1 + 1)):
                j1 += 1
            for jj in range(j, j1 + 1):
                for ii in range(i, i1 + 1):
                    used.add((ii, jj))
            rects.append((i, j, i1, j1, key))
    return rects


def cell_box(i0, j0, i1, j1, y0, y1, c):
    return ((i0 - N / 2) * CELL, y0, (j0 - N / 2) * CELL, (i1 + 1 - N / 2) * CELL, y1,
            (j1 + 1 - N / 2) * CELL, c)


def facade_boxes(out, rng, x0, z0, d, layers, size=CELL):
    """Chunky protruding blocks on one side (d = (dx, dz)) of the cell whose min
    corner is (x0, z0). layers: list of (y0, y1, palette|color, (pmin, pmax), chunk_heights)."""
    a, b = d
    x1, z1 = x0 + size, z0 + size
    half = size / 2
    splits = [(0, size)] if rng.random() < 0.7 else [(0, half), (half, size)]
    for u0, u1 in splits:
        for y0, y1, pal, (pmin, pmax), chunks in layers:
            y = y0
            while y < y1 - 0.2:
                h = rng.choice(chunks) if chunks else y1 - y
                yb = y1 if y1 - (y + h) < 0.8 else y + h
                p = rng.uniform(pmin, pmax)
                col = weighted(rng, pal) if isinstance(pal, list) else pal
                out.append(face_box(x0, z0, d, u0, u1, y, yb, 0, p, col, size))
                y = yb


def face_box(x0, z0, d, u0, u1, y0, y1, p0, p1, col, size=CELL):
    """Box on the outside of a cell face: along the face u0..u1, out from it p0..p1."""
    a, b = d
    x1, z1 = x0 + size, z0 + size
    if a == 1:
        return (x1 + p0, y0, z0 + u0, x1 + p1, y1, z0 + u1, col)
    if a == -1:
        return (x0 - p1, y0, z0 + u0, x0 - p0, y1, z0 + u1, col)
    if b == 1:
        return (x0 + u0, y0, z1 + p0, x0 + u1, y1, z1 + p1, col)
    return (x0 + u0, y0, z0 - p1, x0 + u1, y1, z0 - p0, col)


# ------------------------------------------------------------------ path helpers

def polyline_samples(pts, step=0.25):
    out = []
    total = 0.0
    for a, b in zip(pts, pts[1:]):
        seg = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(seg / step))
        for k in range(n):
            t = k / n
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, total + seg * t,
                        (b[0] - a[0]) / seg, (b[1] - a[1]) / seg))
        total += seg
    last = pts[-1]
    a = pts[-2]
    seg = math.hypot(last[0] - a[0], last[1] - a[1])
    out.append((last[0], last[1], total, (last[0] - a[0]) / seg, (last[1] - a[1]) / seg))
    return out, total


def bend_path(a, b, bend):
    """a -> b with one sideways bend in the middle (cells)."""
    mx, mz = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    dx, dz = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dz) or 1
    return [a, (mx - dz / L * bend, mz + dx / L * bend), b]


def spiral_path(start, centre, end_r, turn=1.6, steps=7):
    """Waypoints winding around `centre` from `start` in to radius end_r (cells)."""
    a0 = math.atan2(start[1] - centre[1], start[0] - centre[0])
    r0 = math.hypot(start[0] - centre[0], start[1] - centre[1])
    pts = [start]
    for k in range(1, steps + 1):
        t = k / steps
        a = a0 + turn * math.pi * t
        r = r0 + (end_r - r0) * t
        pts.append((centre[0] + math.cos(a) * r, centre[1] + math.sin(a) * r))
    return pts


# ------------------------------------------------------------------ height fields

def blob(dx, dz, cx, cz, r, h, i, j, seed, flat=5):
    d = math.hypot(dx - cx, dz - cz) / r + (fbm(i / 4, j / 4, seed + 5) - 0.5) * 0.3
    return h * min(1.0, (1 - d) * flat) if d < 1 else 0.0


def heightfield(theme, seed):
    """-> (tier dict, info). info carries landmark positions in cell offsets from centre."""
    c = N / 2
    tier, info = {}, {"lake": set(), "pond": set(), "crater": set()}
    if theme == "voxel":
        MESAS = [(-27 * K, -3 * K, 10.5 * K, 4.4), (27 * K, 2 * K, 9.5 * K, 4.4)]
        MOUNT = (1, -11 * K)
        info.update(mount=MOUNT, mount_r=20 * K, mesas=MESAS, plaza=(1, 11 * K), plaza_t=2, plaza_r=8.5)
        for j in range(N):
            for i in range(N):
                dx, dz = i + 0.5 - c, j + 0.5 - c
                r = math.hypot(dx, dz * 1.08) / (37.5 * K) + (fbm(i / 12, j / 12, seed + 1) - 0.5) * 0.42
                land = 1 - r
                n = (fbm(i / 7, j / 7, seed + 2) - 0.5) * 1.3
                base = land * 6.0 + n
                md = math.hypot(dx - MOUNT[0], dz - MOUNT[1]) / (20 * K)
                mount = 8.8 * max(0.0, 1 - md) ** 1.05 + n * 0.45
                mesa = max(blob(dx, dz, mx, mz, mr, mh, i, j, seed) for mx, mz, mr, mh in MESAS)
                if land <= 0 and mesa <= 0:
                    continue
                h = max(base, mount, mesa)
                if h < 0.15 and mesa <= 0:
                    continue
                tier[(i, j)] = 0 if h < 0.5 else min(9, int(h))
        return tier, info

    if theme == "desert":
        MESAS = [(-30 * K, -6 * K, 10 * K, 4.4), (30 * K, -10 * K, 9 * K, 3.4), (4 * K, -22 * K, 9 * K, 4.4),
                 (24 * K, 20 * K, 7 * K, 2.4), (-26 * K, 20 * K, 8 * K, 2.4)]
        LAKE = (4 * K, -6 * K, 6.5 * K)
        info.update(mesas=MESAS, lake_c=LAKE, plaza=(2, 15 * K), plaza_t=1, plaza_r=8.5,
                    targets=[0, 1], landmarks=[(0, "Ziggurat"), (1, "Obelisk"), (2, "Obelisk"), (3, "SandstonePillar")])
        for j in range(N):
            for i in range(N):
                dx, dz = i + 0.5 - c, j + 0.5 - c
                r = math.hypot(dx * 1.05, dz) / (39 * K) + (fbm(i / 11, j / 11, seed + 1) - 0.5) * 0.5
                land = 1 - r
                n = (fbm(i / 8, j / 8, seed + 2) - 0.5) * 1.1
                base = land * 3.4 + n
                mesa = max(blob(dx, dz, mx, mz, mr, mh, i, j, seed, flat=6) for mx, mz, mr, mh in MESAS)
                lake = math.hypot(dx - LAKE[0], dz - LAKE[1]) / LAKE[2] + (fbm(i / 3, j / 3, seed + 7) - 0.5) * 0.35
                if lake < 1 and mesa <= 0.5:
                    info["lake"].add((i, j))
                    continue
                if land <= 0 and mesa <= 0:
                    continue
                h = max(base, mesa)
                if h < 0.15 and mesa <= 0:
                    continue
                t = 0 if h < 0.55 else min(9, int(h))
                if lake < 1.45 and mesa <= 0.5:
                    t = min(t, 1)      # low, green-ish oasis banks
                tier[(i, j)] = t
        return tier, info

    if theme == "frost":
        MOUNT = (-2, -8 * K)
        MESAS = [(-30 * K, 10 * K, 10 * K, 3.4), (29 * K, 4 * K, 9 * K, 4.4)]
        POND = (-12 * K, 10 * K, 5.5 * K)
        info.update(mount=MOUNT, mount_r=23 * K, mesas=MESAS, pond_c=POND, plaza=(14, 17 * K), plaza_t=1,
                    plaza_r=8.5, targets=[0, 1], landmarks=[(0, "FlagFrame"), (1, "LogCabin")])
        for j in range(N):
            for i in range(N):
                dx, dz = i + 0.5 - c, j + 0.5 - c
                r = math.hypot(dx, dz * 1.04) / (38 * K) + (fbm(i / 12, j / 12, seed + 1) - 0.5) * 0.45
                land = 1 - r
                n = (fbm(i / 7, j / 7, seed + 2) - 0.5) * 1.3
                base = land * 5.0 + n
                md = math.hypot(dx - MOUNT[0], dz - MOUNT[1]) / (23 * K)
                mount = 10.4 * max(0.0, 1 - md) ** 0.95 + n * 0.5
                mesa = max(blob(dx, dz, mx, mz, mr, mh, i, j, seed) for mx, mz, mr, mh in MESAS)
                if land <= 0 and mesa <= 0:
                    continue
                h = max(base, mount, mesa)
                pond = math.hypot(dx - POND[0], dz - POND[1]) / POND[2]
                if pond < 1 and mesa <= 0:
                    info["pond"].add((i, j))
                    tier[(i, j)] = 0
                    continue
                if h < 0.15 and mesa <= 0:
                    continue
                tier[(i, j)] = 0 if h < 0.5 else min(10, int(h))
        return tier, info

    if theme == "volcanic":
        MOUNT = (0, -5 * K)
        MESAS = [(-31 * K, 14 * K, 9 * K, 2.4), (29 * K, 16 * K, 8 * K, 2.4), (-26 * K, -22 * K, 7 * K, 3.4)]
        info.update(mount=MOUNT, mount_r=26 * K, mesas=MESAS, plaza=(4, 22 * K), plaza_t=1, plaza_r=8,
                    targets=[0, 1], landmarks=[(0, "StiltHut"), (1, "VolcanicBrazier"), (2, "BasaltColumns")])
        for j in range(N):
            for i in range(N):
                dx, dz = i + 0.5 - c, j + 0.5 - c
                r = math.hypot(dx, dz) / (39 * K) + (fbm(i / 10, j / 10, seed + 1) - 0.5) * 0.48
                land = 1 - r
                n = (fbm(i / 6, j / 6, seed + 2) - 0.5) * 1.2
                base = land * 4.2 + n
                md = math.hypot(dx - MOUNT[0], dz - MOUNT[1])
                cone = 9.8 * max(0.0, 1 - md / (26 * K)) ** 0.85 + n * 0.35
                if md < 4.6 * K:          # crater: lava pool sunk into the summit
                    cone = 6.4
                    info["crater"].add((i, j))
                mesa = max(blob(dx, dz, mx, mz, mr, mh, i, j, seed) for mx, mz, mr, mh in MESAS)
                if land <= 0 and mesa <= 0:
                    continue
                h = max(base, cone, mesa) if (i, j) not in info["crater"] else cone
                if h < 0.15 and mesa <= 0:
                    continue
                tier[(i, j)] = 0 if h < 0.5 else min(9, int(h))
        return tier, info
    raise ValueError(theme)


# ------------------------------------------------------------------ the engine

def build_island(theme="voxel"):
    T = THEMES[theme]
    seed = T["seed"]
    rng = random.Random(seed)
    c = N / 2
    tier, info = heightfield(theme, seed)
    MESAS = info["mesas"]

    # ------------------------------------------------------------ village plaza
    pi, pj = int(c + info["plaza"][0]), int(c + info["plaza"][1])
    PLAZA_T = info["plaza_t"]
    plaza_r = info["plaza_r"]
    PS = plaza_r / 6.6
    plaza = set()
    for (i, j) in list(tier):
        d = math.hypot(i - pi, j - pj)
        if d <= plaza_r:
            tier[(i, j)] = PLAZA_T
            plaza.add((i, j))
        elif d <= plaza_r + 3.5 and tier[(i, j)] > PLAZA_T + 1:
            tier[(i, j)] = PLAZA_T + 1
        elif d <= plaza_r + 1.5 and tier[(i, j)] < PLAZA_T:
            tier[(i, j)] = PLAZA_T
    for cell in plaza:
        info["pond"].discard(cell)

    top = {cell: tier_top(t) for cell, t in tier.items()}

    # ------------------------------------------------------------ paths
    shore_j = next(jj for jj in range(pj, N) if (pi, jj) not in tier)
    mesa_cells = [(int(c + mx), int(c + mz)) for mx, mz, mr, mh in MESAS]
    for k, mc in enumerate(mesa_cells):  # make sure the target cell is land
        if mc not in tier:
            mesa_cells[k] = min(tier, key=lambda cc: (cc[0] - mc[0]) ** 2 + (cc[1] - mc[1]) ** 2)
    PT = tier_top(PLAZA_T)
    dock_path = ("wood", [(pi + 0.5, pj + plaza_r - 0.5), (pi + 0.5, shore_j - 1.5)], PT, BEACH_TOP)
    peak = None
    if "mount" in info:
        mx, mz = info["mount"]
        cand = [cc for cc in tier if abs(cc[0] - c - mx) < 6 and abs(cc[1] - c - mz) < 6
                and cc not in info["crater"]]
        peak = max(cand, key=lambda k: (tier[k], -abs(k[0] - c - mx) - abs(k[1] - c - mz)))
    if theme == "voxel":
        west, east = mesa_cells[0], mesa_cells[1]
        PATHS = [
            dock_path,
            ("cobble", [(pi + 0.5, pj - plaza_r + 0.5), (pi + 13, pj - 17), (pi + 10, pj - 31),
                        (pi - 3, pj - 38), (peak[0] - 6.5, peak[1] - 3.5),
                        (peak[0] + 0.5, peak[1] + 0.5)], PT, top[peak]),
            ("cobble", [(pi - plaza_r + 0.5, pj + 0.5), (pi - 15, pj - 1), (pi - 23, pj - 7),
                        (west[0] + 0.5, west[1] + 0.5)], PT, top[west]),
            ("cobble", [(pi + plaza_r - 0.5, pj + 1.5), (pi + 16, pj - 1), (pi + 23, pj - 7),
                        (east[0] + 0.5, east[1] + 0.5)], PT, top[east]),
        ]
    else:
        PATHS = [dock_path]
        if peak is not None:
            mcx, mcz = c + info["mount"][0], c + info["mount"][1]
            end_r = 6.5 * K if theme == "volcanic" else 2.5
            pts = spiral_path((pi + 0.5, pj - plaza_r + 0.5), (mcx, mcz), end_r,
                              turn=1.1 if theme == "volcanic" else 0.95, steps=6)
            if theme == "volcanic":   # end on the crater rim
                rim = min((cc for cc in tier if cc not in info["crater"]),
                          key=lambda cc: (cc[0] + 0.5 - pts[-1][0]) ** 2 + (cc[1] + 0.5 - pts[-1][1]) ** 2)
                peak = rim
            else:
                pts.append((peak[0] + 0.5, peak[1] + 0.5))
            PATHS.append(("cobble", pts, PT, top[peak]))
        for k, mi in enumerate(info["targets"]):
            tgt = mesa_cells[mi]
            ang = math.atan2(tgt[1] - pj, tgt[0] - pi)
            start = (pi + 0.5 + math.cos(ang) * (plaza_r - 0.5), pj + 0.5 + math.sin(ang) * (plaza_r - 0.5))
            PATHS.append(("cobble", bend_path(start, (tgt[0] + 0.5, tgt[1] + 0.5), 5 if k % 2 else -5),
                          PT, top[tgt]))

    path = {}       # cell -> (top, style, dir(dx,dz), dist-from-centre)
    near = {}       # cells beside a path -> (dist, path height): their walls get cut back
    for style, pts, h0, h1 in PATHS:
        samples, total = polyline_samples(pts)
        for sx, sz, s, dx, dz in samples:
            h = h0 + (h1 - h0) * (s / total)
            h = round(h / (1.5 if style == "wood" else 2)) * (1.5 if style == "wood" else 2)
            for jj in range(int(sz) - 6, int(sz) + 7):
                for ii in range(int(sx) - 6, int(sx) + 7):
                    d = math.hypot(ii + 0.5 - sx, jj + 0.5 - sz)
                    if d <= 5.5 and ((ii, jj) not in near or d < near[(ii, jj)][0]):
                        near[(ii, jj)] = (d, h)
                    if d > PATH_R or (ii, jj) in plaza or (ii, jj) in info["crater"]:
                        continue
                    old = path.get((ii, jj))
                    if old is None or d < old[3]:
                        path[(ii, jj)] = (h, style, (dx, dz), d)
    for cell, (h, style, _, _) in path.items():
        tier.setdefault(cell, 0)
        top[cell] = h
        info["lake"].discard(cell)
        info["pond"].discard(cell)
    for cell, (d, h) in near.items():
        if cell in tier and cell not in path and cell not in plaza and cell not in info["crater"]:
            limit = h + 6 + max(0.0, d - PATH_R - 2) * 4
            if top[cell] > limit:
                top[cell] = limit

    for jj in range(shore_j - 4, shore_j):  # beach landing around the dock
        for ii in range(pi - 7, pi + 9):
            if (ii, jj) not in path and (ii, jj) in tier and tier[(ii, jj)] > 0:
                tier[(ii, jj)] = 0
                top[(ii, jj)] = BEACH_TOP

    # ------------------------------------------------------------ special surfaces
    lava = set(info["crater"])
    if theme == "volcanic":   # lava rivers from the crater rim down to the sea
        mcx, mcz = c + info["mount"][0], c + info["mount"][1]
        for ang in (200, 330, 122):
            a = math.radians(ang)
            pts = []
            for k in range(0, 9):
                r = 4.0 * K + k * 5.2 * K
                wob = math.sin(k * 1.3 + ang) * 2.2
                pts.append((mcx + math.cos(a) * r - math.sin(a) * wob, mcz + math.sin(a) * r + math.cos(a) * wob))
            samples, _ = polyline_samples(pts)
            for sx, sz, _, _, _ in samples:
                for jj in range(int(sz) - 2, int(sz) + 3):
                    for ii in range(int(sx) - 2, int(sx) + 3):
                        cell = (ii, jj)
                        if (cell in tier and cell not in path and cell not in plaza
                                and math.hypot(ii + 0.5 - sx, jj + 0.5 - sz) <= 1.2):
                            lava.add(cell)
    for cell in lava:
        if cell in tier:
            top[cell] = tier_top(tier[cell])
    pond = {cc for cc in info["pond"] if cc in tier}
    for cell in pond:
        top[cell] = BEACH_TOP

    surface = {}
    for cell, t in tier.items():
        i, j = cell
        if cell in path or cell in plaza:
            continue
        if cell in lava:
            surface[cell] = "lava"
            continue
        if cell in pond:
            surface[cell] = "ice"
            continue
        if t == 0:
            surface[cell] = "sand"
            continue
        mountainish = "mount" in info and math.hypot(i - c - info["mount"][0], j - c - info["mount"][1]) < 17
        if t >= 3 and mountainish and fbm(i / 3.5, j / 3.5, seed + 8) > 0.47:
            surface[cell] = "rocktop"
        else:
            surface[cell] = "grass"
        if fbm(i / 3, j / 3, seed + 9) > 0.7 and not any(
                (i + a, j + b) in path or (i + a, j + b) in plaza or (i + a, j + b) in lava
                for a in (-1, 0, 1) for b in (-1, 0, 1)):
            top[cell] += 2  # small raised ledge

    # ------------------------------------------------------------ shallows (stepped)
    depth = {}
    q = deque((cell, 0) for cell in tier)
    seen = set(tier)
    while q:
        (i, j), d = q.popleft()
        if d >= 7:
            continue
        for a, b in DIRS:
            nb = (i + a, j + b)
            if nb in seen or not (0 <= nb[0] < N and 0 <= nb[1] < N):
                continue
            seen.add(nb)
            depth[nb] = d + 1
            q.append((nb, d + 1))
    SHALLOW_Y = {1: -1, 2: -2, 3: -3.5, 4: -5, 5: -6, 6: -7.5, 7: -9}

    def top_of(cell):
        if cell in top:
            return top[cell]
        if cell in depth:
            return SHALLOW_Y[depth[cell]]
        return None

    cobble_rng = random.Random(seed + 40)

    def patch(cell, pal, sd):
        if cobble_rng.random() < 0.08:
            return weighted(cobble_rng, pal)
        v = fbm(cell[0] / 4.5, cell[1] / 4.5, seed + sd)
        k = min(len(pal) - 1, int(max(0.0, (v - 0.3) / 0.4) * len(pal)))
        order = sorted(pal, key=lambda kv: -kv[1])
        return order[min(k, 2)][0]

    # ------------------------------------------------------------ terrain columns
    terrain, body, band, cap, tiles = [], {}, {}, {}, []
    for cell, t in tier.items():
        Tc = top[cell]
        if cell in path or cell in plaza:
            style = path[cell][1] if cell in path else "cobble"
            body[cell] = (T["body"], Tc - 3)
            band[cell] = (T["path_band"], Tc - 3, Tc - 1)
            i, j = cell
            x0, z0 = (i - N / 2) * CELL, (j - N / 2) * CELL
            if style == "wood":
                dx, dz = path[cell][2]
                along_x = abs(dx) > abs(dz)
                for k in range(2):
                    cc = "plank" if (i + j + k) % 2 else "wood"
                    jit = cobble_rng.choice((0, 0.1))
                    if along_x:
                        tiles.append((x0 + 2 * k, Tc - 1, z0, x0 + 2 * k + 2, Tc + jit, z0 + 4, cc))
                    else:
                        tiles.append((x0, Tc - 1, z0 + 2 * k, x0 + 4, Tc + jit, z0 + 2 * k + 2, cc))
            else:
                if cobble_rng.random() < 0.5:
                    rects = [(2 * a, 2 * b, 2 * a + 2, 2 * b + 2) for a in range(2) for b in range(2)]
                elif cobble_rng.random() < 0.5:
                    rects = [(0, 0, 4, 2), (0, 2, 4, 4)]
                else:
                    rects = [(0, 0, 2, 4), (2, 0, 4, 4)]
                for u0, v0, u1, v1 in rects:
                    jit = cobble_rng.choice((0, 0, 0.12, 0.25))
                    tiles.append((x0 + u0, Tc - 1, z0 + v0, x0 + u1, Tc + jit, z0 + v1,
                                  weighted(cobble_rng, T["cobble"])))
            continue
        if surface[cell] == "lava":
            body[cell] = (T["body"], Tc - 2)
            band[cell] = ("magma_crust", Tc - 2, Tc - 1)
            cap[cell] = ("lava" if (cell[0] + cell[1]) % 5 else "lava_core", Tc - 1, Tc)
        elif surface[cell] == "ice":
            body[cell] = (T["beach_body"], Tc - 1)
            cap[cell] = ("ice", Tc - 1, Tc)
        elif t == 0:
            body[cell] = (T["beach_body"], Tc - 1)
            cap[cell] = (patch(cell, T["sand_top"], 21), Tc - 1, Tc)
        else:
            body[cell] = (T["body"], Tc - 3)
            band[cell] = (T["band"], Tc - 3, Tc - 1.5)
            pal = T["rocktop"] if surface[cell] == "rocktop" else T["top"]
            cap[cell] = (patch(cell, pal, 23), Tc - 1.5, Tc)
    shallow_body = {}
    sh = T["shallow"]
    for cell, d in depth.items():
        shallow_body[cell] = (sh[0] if d <= 2 else sh[1] if d <= 4 else sh[2], SHALLOW_Y[d])

    def emit(grid_items, lo_fn, out):
        for i0, j0, i1, j1, key in greedy(dict(grid_items), N, N):
            out.append(cell_box(i0, j0, i1, j1, lo_fn(key), key[-1], key[0]))

    shallows = []
    emit(body, lambda key: BED, terrain)
    emit(band, lambda key: key[1], terrain)
    emit(cap, lambda key: key[1], terrain)
    emit(shallow_body, lambda key: BED, shallows)
    shallows.append((-SEA, BED - 2, -SEA, SEA, BED, SEA, T["seabed"]))
    paths = list(tiles)
    cliffs, accents = [], []

    # ------------------------------------------------------------ cliff facades
    reserved = set()
    facade_rng = random.Random(seed + 50)
    props = []

    STRATA = 3.5   # rock cliffs are stacked slab layers (like the reef shelves) that line up around the island

    def facade(cell, d, layers):
        x0, z0 = (cell[0] - N / 2) * CELL, (cell[1] - N / 2) * CELL
        rest = []
        for (y0, y1, pal, pr, chunks) in layers:
            if pal is not ROCK:
                rest.append((y0, y1, pal, pr, chunks))
                continue
            fx, fz = x0 + 2 + d[0] * 2, z0 + 2 + d[1] * 2
            k = math.floor((y0 + 40) / STRATA)
            y = y0
            while y < y1 - 0.3:
                yt = min(y1, (k + 1) * STRATA - 40)
                if y1 - yt < 1.2:
                    yt = y1
                n = fbm(fx / 46 + k * 1.7, fz / 46 - k * 2.3, seed + 70 + k, octaves=2)
                p = 0.3 + 1.9 * max(0.0, n - 0.25) * 1.6
                lr = random.Random(hash((k, int(fx // 28), int(fz // 28), seed)) & 0xFFFFFFFF)
                cliffs.append(face_box(x0, z0, d, 0, CELL, y, yt, 0, round(p, 2), weighted(lr, ROCK)))
                y = yt
                k += 1
        facade_boxes(cliffs, facade_rng, x0, z0, d, rest)

    cave = None
    if theme == "voxel":   # cave entrance in a clean cliff face on the east side
        for (i, j), t in sorted(tier.items(), key=lambda kv: (-kv[0][0], kv[0][1])):
            if t != 0 or i < c + 8 or (i, j) in path:
                continue
            for d in ((0, 1), (1, 0), (-1, 0)):
                cliff = (i - d[0], j - d[1])
                side = [(i + d[1], j + d[0]), (i - d[1], j - d[0])]
                if (tier.get(cliff, 0) >= 2 and cliff not in path
                        and all(tier.get(sc, -1) == 0 for sc in side)):
                    cave = (i, j)
                    reserved.add((cliff, d))
                    props.append(prop("CaveEntrance", wx(i) - d[0] * 2, BEACH_TOP, wx(j) - d[1] * 2,
                                      FACING_ROT[d]))
                    break
            if cave:
                break

    ROCK = T["rock"]
    for cell, t in tier.items():
        Tc = top[cell]
        for d in DIRS:
            nb = (cell[0] + d[0], cell[1] + d[1])
            if (cell, d) in reserved:
                continue
            nt = top_of(nb)
            lo = max(nt if nt is not None else BED, -1.5)
            if Tc - lo < 1.6:
                continue
            if cell in path or cell in plaza:
                layers = [(lo, Tc - 3, ROCK, (0.25, 1.0), (3, 4, 5)),
                          (Tc - 3, Tc - 1, T["path_band"], (0.15, 0.35), None)]
            elif surface[cell] == "lava":
                layers = [(lo, Tc - 2, ROCK, (0.25, 1.0), (3, 4, 5)),
                          (Tc - 2, Tc, "magma_crust", (0.2, 0.4), None)]
            elif t == 0:
                layers = [(lo, Tc, T["sand_side"], (0.15, 0.4), (1.5, 2))]
            else:
                cap_col = cap[cell][0]
                if facade_rng.random() < 0.3:
                    layers = [(lo, Tc - 3, ROCK, (0.25, 1.0), (3, 4, 5)), (Tc - 3, Tc, cap_col, (0.45, 0.7), None)]
                else:
                    layers = [(lo, Tc - 3, ROCK, (0.25, 1.0), (3, 4, 5)),
                              (Tc - 3, Tc - 1.5, T["band_side"], (0.2, 0.4), None),
                              (Tc - 1.5, Tc, cap_col, (0.12, 0.3), None)]
            facade(cell, d, [(max(y0, lo), y1, p, pr, ch) for (y0, y1, p, pr, ch) in layers
                             if y1 - max(y0, lo) > 0.3])

    # ------------------------------------------------------------ accents (stay on top of the mesh)
    # chunky part ledges + block clumps sticking out of the cliffs, clear of the mesh bulge
    acc_rng = random.Random(seed + 60)
    for cell, t in sorted(tier.items()):
        if t == 0 or cell in plaza:
            continue
        Tc = top[cell]
        for d in DIRS:
            nb = (cell[0] + d[0], cell[1] + d[1])
            if (cell, d) in reserved or nb in path or nb in plaza:
                continue
            nt = top_of(nb)
            lo = max(nt if nt is not None else BED, -1.5)
            height = Tc - lo
            if height < 6:
                continue
            x0, z0 = (cell[0] - N / 2) * CELL, (cell[1] - N / 2) * CELL
            r = acc_rng.random()
            if r < 0.06:   # ledge slab with a cap, partly set into the cliff
                y = acc_rng.uniform(lo + 2, Tc - 4)
                th = acc_rng.choice((1.5, 2, 2.5))
                p = acc_rng.uniform(2.6, 3.8)
                u0, u1 = (0, 4) if acc_rng.random() < 0.6 else ((0, 2) if acc_rng.random() < 0.5 else (2, 4))
                accents.append(face_box(x0, z0, d, u0 - 0.6, u1 + 0.6, y, y + th, -1.0, p,
                                        weighted(acc_rng, ROCK)))
                accents.append(face_box(x0, z0, d, u0 - 0.3, u1 + 0.3, y + th, y + th + 0.5, -0.6, p - 0.3,
                                        T["accent_top"]))
            elif r < 0.08:  # block clump at the cliff foot
                for k in range(acc_rng.choice((2, 3))):
                    s = acc_rng.uniform(2.2, 3.4)
                    u = acc_rng.uniform(0, 4 - s)
                    y = lo + (k * 1.2 if k else 0)
                    accents.append(face_box(x0, z0, d, u, u + s, y - 0.5, y + s, -1.0, s * 0.9 + 1.4,
                                            weighted(acc_rng, ROCK)))
            elif r < 0.10 and height >= 10:  # big jutting block near the top edge
                s = acc_rng.uniform(3, 4.5)
                accents.append(face_box(x0, z0, d, 0, 4, Tc - 3 - s, Tc - 3, -1.0, 3.2, weighted(acc_rng, ROCK)))
                accents.append(face_box(x0, z0, d, 0, 4, Tc - 3, Tc - 2.4, -0.6, 3.0, T["accent_top"]))

    # ------------------------------------------------------------ props
    blocked = set(plaza) | set(path) | lava | pond
    if cave:
        for a in range(-2, 3):
            for b in range(0, 3):
                blocked.add((cave[0] + a, cave[1] + b))

    def block(ci, cj, r):
        for jj in range(cj - r, cj + r + 1):
            for ii in range(ci - r, ci + r + 1):
                blocked.add((ii, jj))

    def edge_cell(cell):
        t = top[cell]
        for d in DIRS:
            nt = top_of((cell[0] + d[0], cell[1] + d[1]))
            if nt is None or nt < t - 1.5:
                return True
        return False

    def safe_xy(cell, x, z, margin=1.4):
        """Keep a prop `margin` studs clear of edges that drop away (the terrain mesh pulls
        those edges in). None if the cell is too narrow."""
        cx, cz = wx(cell[0]), wx(cell[1])
        t = top[cell]
        drops = []
        for d in DIRS:
            nt = top_of((cell[0] + d[0], cell[1] + d[1]))
            if nt is None or nt < t - 1.5:
                drops.append(d)
        limit = 2 - margin
        for d in drops:
            if d[0] and (x - cx) * d[0] > limit:
                x = cx + limit * d[0]
            elif d[1] and (z - cz) * d[1] > limit:
                z = cz + limit * d[1]
        for d in drops:
            off = ((x - cx) * d[0]) if d[0] else ((z - cz) * d[1])
            if off > limit + 1e-6:
                return None
        return x, z

    px, pz = wx(pi), wx(pj)
    spawn = (px - 6, PT, pz + 18 * PS)
    village(theme, props, px, pz, PT, PS, rng)

    # torches along the paths, fences where a path runs along a drop
    count = 0
    for cell in sorted(path):
        h, style, (dx, dz), dist = path[cell]
        i, j = cell
        for d in DIRS:
            nb = (i + d[0], j + d[1])
            if nb in path or nb in plaza:
                continue
            nt = top_of(nb)
            drop = h - (nt if nt is not None else BED)
            side_of_travel = abs(d[0] * dx + d[1] * dz) < 0.5
            if (style == "wood" and side_of_travel and drop > -2) or drop >= 3.5:
                props.append(prop("Fence", wx(i) + d[0] * 1.6, h, wx(j) + d[1] * 1.6, 90 if d[0] else 0))
        count += 1
        if style == "cobble" and count % 23 == 0 and dist > PATH_R - 0.8:
            spot = safe_xy(cell, wx(i), wx(j))
            if spot:
                props.append(prop(T["torch"], spot[0], h, spot[1], 0))

    # dock + boat + beach clutter
    dock_z = (shore_j - N / 2) * CELL - 6
    props += [prop("Dock", px + 2, BEACH_TOP + 0.4, dock_z, 0), prop("Rowboat", px - 10, 0, dock_z + 22, -14),
              prop("Barrels", px - 8, BEACH_TOP, dock_z - 3, 20), prop("CrateStack", px + 12, BEACH_TOP, dock_z - 4, -10),
              prop(T["lamp"], px + 8, BEACH_TOP, dock_z + 1, 0, 0.9)]
    block(pi, shore_j - 1, 3)

    feature = []

    def clear_of(x, z, r):
        return all(math.hypot(x - a, z - b) > r + rr for a, b, rr in feature)

    def near_path(cell, r):
        return any((cell[0] + a, cell[1] + b) in path or (cell[0] + a, cell[1] + b) in plaza
                   for a in range(-r, r + 1) for b in range(-r, r + 1))

    # landmarks on the mesa tops
    if theme == "voxel":
        east = mesa_cells[1]
        flag = (east[0] + 1, east[1] - 3)
        props.append(prop("FlagFrame", wx(flag[0]), top[flag], wx(flag[1]), 90))
        block(flag[0], flag[1], 2)
    else:
        for mi, what in info.get("landmarks", []):
            if not what:
                continue
            mc = mesa_cells[mi]
            # stand it just beside where the path arrives
            spot = min((cc for cc in tier if cc not in path and cc not in lava and tier[cc] == tier[mc]
                        and not edge_cell(cc) and 2.5 < math.hypot(cc[0] - mc[0], cc[1] - mc[1]) < 6),
                       key=lambda cc: math.hypot(cc[0] - mc[0], cc[1] - mc[1]), default=None)
            if spot is None:
                continue
            props.append(prop(what, wx(spot[0]), top[spot], wx(spot[1]), rng.choice((0, 90, 180, 270))))
            block(spot[0], spot[1], 5 if what == "Ziggurat" else 2)
            feature.append((wx(spot[0]), wx(spot[1]), 20 if what == "Ziggurat" else 6))

    # the rock arch: a gateway where a path cuts between the highest ground on both sides
    best = None
    for idx in range(1, len(PATHS)):
        style, pts, h0, h1 = PATHS[idx]
        samples, total = polyline_samples(pts, step=1.0)
        for sx, sz, sdist, dx, dz in samples:
            f = sdist / total
            if not 0.3 < f < 0.8:
                continue
            h = h0 + (h1 - h0) * f
            walls = []
            for side in (-1, 1):
                cx_ = int(sx + side * -dz * (PATH_R + 1.5))
                cz_ = int(sz + side * dx * (PATH_R + 1.5))
                walls.append(top.get((cx_, cz_), BED) - h)
            score = min(walls) + (4 if idx == 2 else 0)
            if best is None or score > best[0]:
                best = (score, sx, sz, dx, dz, h)
    if best:
        _, sx, sz, dx, dz, h = best
        ax, az = (sx - N / 2) * CELL, (sz - N / 2) * CELL
        props.append(prop(T["rocks"]["arch"], ax, h - 0.5, az, math.degrees(math.atan2(dx, dz)), 1.1))
        block(int(sx), int(sz), 3)
        props[:] = [p for p in props if not (p[0] in ("Fence", T["torch"]) and math.hypot(p[1] - ax, p[3] - az) < 18)]

    # water/lava falls down the tallest cliff next to the lake / pond, and wherever lava drops
    falls = []
    if theme in ("desert", "frost"):
        basin = info["lake"] if theme == "desert" else pond
        best = None
        for cell, t in tier.items():
            if cell in path or cell in plaza or t < 2:
                continue
            for d in DIRS:
                nb = (cell[0] + d[0], cell[1] + d[1])
                for k in range(1, 4):  # the basin within a few cells
                    if (cell[0] + d[0] * k, cell[1] + d[1] * k) in basin:
                        drop = top[cell] - (top_of(nb) if top_of(nb) is not None else 0)
                        if drop > 12 and (best is None or drop > best[0]):
                            best = (drop, cell, d)
                        break
        if best:
            falls.append((best[1], best[2], 2))
    if theme == "volcanic":
        for cell in sorted(lava):
            for d in DIRS:
                nb = (cell[0] + d[0], cell[1] + d[1])
                nt = top_of(nb)
                if nt is not None and top[cell] - nt >= 6 and nb not in path and acc_rng.random() < 0.4:
                    falls.append((cell, d, 1))
    fall_spots = []
    for cell, d, width in falls:
        build_fall(accents, cell, d, width, top, top_of, T, acc_rng)
        block(cell[0], cell[1], 2)
        fall_spots.append((wx(cell[0]) + d[0] * 2, top[cell], wx(cell[1]) + d[1] * 2, d))
    if theme == "volcanic":   # glow along the lava
        for k, cell in enumerate(sorted(lava)):
            if k % 9 == 0:
                props.append(prop("LavaGlow", wx(cell[0]), top[cell], wx(cell[1]), 0))

    # crags and clusters half-buried at the foot of tall cliffs
    R = T["rocks"]
    feet = []
    for cell, t in tier.items():
        if cell in blocked or near_path(cell, 1) or edge_cell(cell):
            continue
        for d in DIRS:
            nb = (cell[0] + d[0], cell[1] + d[1])
            if nb in top and nb not in path and top[nb] - top[cell] >= 7:
                feet.append((top[nb] - top[cell] + rng.random() * 6, cell, d))
    feet.sort(key=lambda f: -f[0])
    placed_feet = 0
    for score, cell, d in feet:
        if placed_feet >= 70:
            break
        drop = top[(cell[0] + d[0], cell[1] + d[1])] - top[cell]
        x, z = wx(cell[0]) + d[0] * 1.8, wx(cell[1]) + d[1] * 1.8   # big rock wraps into the cliff face
        if drop >= 16:
            name, sc = R["crag"], max(0.7, min(1.6, drop / 24))
        else:
            name, sc = rng.choice((R["rocks"], R["ledge"])), max(0.9, min(1.7, drop / 8))
        if not clear_of(x, z, 9 * sc + 2):
            continue
        props.append(prop(name, x, top[cell] - 1.5, z, rng.uniform(0, 360), sc))
        feature.append((x, z, 9 * sc))
        block(cell[0], cell[1], 1)
        placed_feet += 1
        if theme == "volcanic" and rng.random() < 0.5:   # basalt column clusters next to the crags
            side = rng.choice((-1, 1)) * rng.uniform(6, 9)   # beside the crag, along the cliff foot
            bx, bz = x + d[1] * side - d[0] * 1.5, z + d[0] * side - d[1] * 1.5
            bc = (round((bx / CELL) + N / 2 - 0.5), round((bz / CELL) + N / 2 - 0.5))
            if top.get(bc) == top[cell]:
                props.append(prop("BasaltColumns", bx, top[cell] - 1, bz, rng.uniform(0, 360), rng.uniform(0.7, 1.1)))

    if "mount" in info:  # craggy spires up the mountain
        mcells = [cell for cell, t in tier.items()
                  if t >= 4 and math.hypot(cell[0] - c - info["mount"][0], cell[1] - c - info["mount"][1]) < 15
                  and cell not in blocked and not near_path(cell, 2) and not edge_cell(cell)]
        rng.shuffle(mcells)
        for cell in mcells[:40]:
            x, z = wx(cell[0]), wx(cell[1])
            sc = rng.uniform(0.6, 1.0)
            if clear_of(x, z, 9 * sc + 14):
                props.append(prop(R["crag"], x, top[cell] - 2, z, rng.uniform(0, 360), sc))
                feature.append((x, z, 9 * sc))
                block(cell[0], cell[1], 1)

    fcells = [cell for cell, t in tier.items()
              if 1 <= t <= 3 and surface.get(cell) == "grass" and cell not in blocked and not near_path(cell, 2)]
    rng.shuffle(fcells)
    n_field = 0
    for cell in fcells:   # rock clusters out in the open terraces
        if n_field >= 12:
            break
        x, z = wx(cell[0]), wx(cell[1])
        sc = rng.uniform(0.9, 1.4)
        if clear_of(x, z, 9 * sc + 30):
            props.append(prop(rng.choice((R["rocks"], R["ledge"])), x, top[cell] - 1.5, z, rng.uniform(0, 360), sc))
            feature.append((x, z, 9 * sc))
            block(cell[0], cell[1], 1)
            n_field += 1

    if peak is not None:   # lookout at the top of the spiral path
        lookout = {"voxel": [("RuinPillar", 2, 1), ("Signpost", 1, -2)],
                   "frost": [("FlagFrame", 2, 2), ("Signpost", -1, -2)],
                   "volcanic": [("VolcanicBrazier", 1, 1), ("Signpost", -1, 1)]}.get(theme, [])
        for name, ox, oz in lookout:
            spot = safe_xy(peak, wx(peak[0]) + ox * 1.2, wx(peak[1]) + oz * 1.2, margin=3.0)
            if spot:
                props.append(prop(name, spot[0], top[peak], spot[1], 120))
        if theme == "voxel":
            spot = safe_xy(peak, wx(peak[0]) - 1.5, wx(peak[1]) - 1.5, margin=3.2)
            if spot:
                props.append(prop("Torch", spot[0], top[peak], spot[1], 0))
        block(peak[0], peak[1], 2)

    # trees and ground clutter
    trees = set()
    lake_cells = info["lake"]
    cells = sorted(tier)
    rng.shuffle(cells)
    tree_names = T["trees"]
    for cell in cells:
        if cell in blocked:
            continue
        i, j = cell
        t = tier[cell]
        Tc = top[cell]
        jx, jz = rng.uniform(-1.1, 1.1), rng.uniform(-1.1, 1.1)
        safe = safe_xy(cell, wx(i) + jx, wx(j) + jz)
        if safe is None:
            continue
        x, z = safe
        npath = any((i + a, j + b) in path or (i + a, j + b) in plaza
                    for a in (-2, -1, 0, 1, 2) for b in (-2, -1, 0, 1, 2))
        r = rng.random()
        if t >= 1 and surface[cell] == "grass":
            dense = fbm(i / 7, j / 7, seed + 4)
            p_tree = (0.03 + max(0, dense - 0.4) * 0.3) * T["tree_density"]
            if theme == "desert":  # palms crowd around the oasis
                if any((i + a, j + b) in lake_cells for a in range(-3, 4) for b in range(-3, 4)):
                    p_tree = 0.35
            if (not npath and r < p_tree
                    and not any((i + a, j + b) in trees for a in (-2, -1, 0, 1, 2) for b in (-2, -1, 0, 1, 2))):
                props.append(prop(weighted(rng, tree_names), x, Tc, z,
                                  rng.choice((0, 90, 180, 270)) + rng.uniform(-6, 6), rng.uniform(0.9, 1.2)))
                trees.add(cell)
                continue
            r = rng.random()
            acc = 0
            for name, pr, (s0, s1) in T["clutter"]:
                acc += pr
                if r < acc:
                    props.append(prop(name, x, Tc, z, rng.uniform(0, 360), rng.uniform(s0, s1),
                                      rng.choice((1, 2, 3, 6)) if name == "Flowers" else 0))
                    break
        elif t >= 1:  # bare rock tops
            if r < 0.12:
                props.append(prop(T["rock_clutter"], x, Tc, z, rng.uniform(0, 360), rng.uniform(1, 1.8)))
            elif r < 0.22:
                props.append(prop(T["tuft"], x, Tc, z, rng.uniform(0, 360), rng.uniform(0.8, 1.2)))
            elif r < 0.25 and not npath:
                props.append(prop(T["rocktop_tree"], x, Tc, z, rng.uniform(0, 360), rng.uniform(0.8, 1)))
        elif t == 0:
            near_water = theme == "desert" and any((i + a, j + b) in lake_cells for a in (-2, -1, 0, 1, 2)
                                                    for b in (-2, -1, 0, 1, 2))
            if near_water and r < 0.3 and not any((i + a, j + b) in trees for a in (-2, -1, 0, 1, 2)
                                                  for b in (-2, -1, 0, 1, 2)):
                props.append(prop(weighted(rng, tree_names), x, Tc, z, rng.uniform(0, 360), rng.uniform(0.9, 1.2)))
                trees.add(cell)
            elif r < 0.035:
                props.append(prop(T["beach_clutter"][0], x, Tc, z, rng.uniform(0, 360), rng.uniform(1, 2)))
            elif r < 0.05:
                props.append(prop(T["beach_clutter"][1], x, Tc, z, rng.uniform(0, 360), 1))
            elif theme == "desert" and r < 0.065:
                props.append(prop(weighted(rng, tree_names), x, Tc, z, rng.uniform(0, 360), rng.uniform(0.8, 1.1)))

    for cell in sorted(path):   # path-side clutter
        i, j = cell
        for d in DIRS:
            nb = (i + d[0], j + d[1])
            if nb in path or nb in plaza or nb in blocked or nb not in tier:
                continue
            if rng.random() < 0.08 and abs(top[nb] - path[cell][0]) < 3:
                safe = safe_xy(nb, wx(i) + d[0] * 2.6 + rng.uniform(-1, 1) * (d[1] != 0),
                               wx(j) + d[1] * 2.6 + rng.uniform(-1, 1) * (d[0] != 0))
                if safe is None:
                    continue
                name = rng.choice(T["path_clutter"])
                props.append(prop(name, safe[0], top[nb], safe[1], rng.uniform(0, 360), 1,
                                  rng.choice((1, 3, 6)) if name == "Flowers" else 0))

    # sea stacks at the shoreline (icebergs drift further out)
    placed = []
    shore = [cell for cell in sorted(depth) if depth[cell] <= (5 if theme == "frost" else 2)]
    rng.shuffle(shore)
    n_stacks = 12 if theme == "frost" else 7
    for cell in shore:
        if len(placed) >= n_stacks:
            break
        x, z = wx(cell[0]), wx(cell[1])
        if abs(cell[0] - pi) < 9 and cell[1] > shore_j - 3:
            continue
        if cell in lake_cells:
            continue
        if any(math.hypot(x - a, z - b) < (50 if theme == "frost" else 70) for a, b in placed) or not clear_of(x, z, 14):
            continue
        name = weighted(rng, [(R["stack"], 3), (R["stack_big"], 2)])
        y = -1.5 if theme == "frost" else SHALLOW_Y[depth[cell]] - 0.5
        props.append(prop(name, x, y, z, rng.uniform(0, 360), rng.uniform(1.1, 1.5) * (0.8 if theme == "frost" else 1)))
        placed.append((x, z))
    for cell in shore:
        if depth[cell] == 1 and rng.random() < 0.02 and cell not in lake_cells:
            props.append(prop(R["stack_small"], wx(cell[0]), -1.5, wx(cell[1]), rng.uniform(0, 360),
                              rng.uniform(1.0, 1.5)))

    # what the Blender terrain mesh is built from: every non-underwater column
    mesh_cells = []
    for cell in tier:
        if cell in path or cell in plaza:
            kind = "path"
        elif surface.get(cell) in ("lava", "ice"):
            kind = surface[cell]
        else:
            kind = "beach" if tier[cell] == 0 else "land"
        mesh_cells.append((cell[0], cell[1], top[cell] - (1 if kind == "path" else 0), kind, surface.get(cell, "")))
    groups = [("Ground", terrain), ("Shallows", shallows), ("Paths", paths), ("Cliffs", cliffs),
              ("Accents", accents)]
    return {"terrain": terrain + shallows + paths + cliffs + accents, "groups": groups, "props": props,
            "water": (-SEA, BED - 2, -SEA, SEA, 0, SEA), "spawn": spawn, "mesh_cells": mesh_cells,
            "N": N, "cell": CELL, "theme": theme, "map": T["map"], "mats": T["mats"],
            "landmarks": {"plaza": (px, PT, pz), "falls": fall_spots,
                          "peak": (wx(peak[0]), top[peak], wx(peak[1])) if peak else None,
                          "crater": ((wx(int(c + info["mount"][0])), tier_top(6), wx(int(c + info["mount"][1])))
                                     if info["crater"] else None)},
            "debug": {"tier": tier, "path": path, "plaza": plaza, "N": N, "lava": lava,
                      "lake": info["lake"], "pond": pond}}


def build_fall(out, cell, d, width, top, top_of, T, rng):
    """Waterfall / frozen fall / lava fall down the cliff face on side d of `cell`, built from
    parts that stand proud of the deformed mesh. width in cells (spreads sideways)."""
    nb = (cell[0] + d[0], cell[1] + d[1])
    hi = top[cell]
    lo = top_of(nb)
    lo = 0 if lo is None else max(lo, -0.5)
    col, foam = T.get("fall", "oasis_water"), T.get("fall_foam", "snow")
    side = (d[1], d[0])
    for k in range(-(width // 2), width - width // 2):
        c2 = (cell[0] + side[0] * k, cell[1] + side[1] * k)
        x0, z0 = (c2[0] - N / 2) * CELL, (c2[1] - N / 2) * CELL
        out.append(face_box(x0, z0, d, 0.3, 3.7, lo - 0.3, hi + 0.4, -0.8, 2.9, col))          # sheet
        y = lo + 1
        while y < hi - 2:                                                                    # streaks
            h = rng.uniform(1.5, 4)
            u = rng.uniform(0.5, 2.8)
            out.append(face_box(x0, z0, d, u, u + 0.7, y, min(hi, y + h), 2.9, 3.15, foam))
            y += h + rng.uniform(1, 3)
        # lip: the stream running over the edge on the top
        ix0, iz0 = (c2[0] - N / 2) * CELL, (c2[1] - N / 2) * CELL
        back = (-d[0], -d[1])
        out.append(face_box(ix0 + d[0] * 4, iz0 + d[1] * 4, back, 0.6, 3.4, hi - 0.3, hi + 0.35, 0, 6, col))
        # splash at the bottom
        out.append(face_box(x0, z0, d, -0.8, 4.8, lo - 0.3, lo + 0.6, 2.4, 7.5, foam))
        out.append(face_box(x0, z0, d, 0.2, 3.8, lo + 0.6, lo + 1.6, 2.8, 5.5, foam))


def village(theme, props, px, pz, PT, PS, rng):
    """Furniture of each theme's village plaza."""
    def add(name, ox, oz, rot=0, sc=1):
        props.append(prop(name, px + ox * PS, PT, pz + oz * PS, rot, sc))

    if theme == "voxel":
        add("Campfire", 0, 2, 15)
        add("MarketStall", -13, -10, 12)
        add("CrateStack", -21, -4, -30)
        add("WoodFrame", 12, -13, -20)
        add("Barrels", 19, -6, 40)
        add("Statue", -18, 11, 35)
        add("Well", 17, 11, 0)
        add("Bench", -7, 14, 180)
        add("Bench", 7, 9, 160)
        add("Signpost", 6, 22, 200)
        add("LogPile", 4, -20, 75)
        for a in (30, 150, 210, 330):
            add("LampPost", 23 * math.cos(math.radians(a)), 23 * math.sin(math.radians(a)), -a)
    elif theme == "desert":
        add("DesertWell", 0, 0, 0)
        add("AdobeHouseBig", -17, -14, 30)
        add("AdobeHouse", 16, -16, -35)
        add("AdobeHouse", -22, 6, 80)
        add("AdobeHouse", 21, 7, -90)
        add("DesertStall", -6, -18, 0)
        add("DesertStall", 8, 14, 190)
        add("Pots", 11, -4, 20)
        add("Pots", -10, 9, 70)
        add("CrateStack", 5, -9, 15)
        add("SandstonePillar", -15, 18, 0)
        add("Obelisk", 18, 20, 0, 0.8)
        for a in (45, 135, 225, 315):
            add("Brazier", 13 * math.cos(math.radians(a)), 13 * math.sin(math.radians(a)), 0)
    elif theme == "frost":
        add("Campfire", 0, 0, 0)
        add("LogCabin", -16, -15, 30)
        add("LogCabin", 17, -14, -30)
        add("LogCabin", -21, 9, 95)
        add("LogCabin", 21, 9, -95, 0.9)
        add("Snowman", 7, 8, 200)
        add("Snowman", -9, -4, 150, 0.8)
        add("CrateStack", 6, -9, 10)
        add("Barrels", -5, 13, 40)
        add("LogPile", 11, 2, 80)
        add("Well", -11, 3, 0)
        for a in (30, 150, 210, 330):
            add("LampPost", 23 * math.cos(math.radians(a)), 23 * math.sin(math.radians(a)), -a)
    elif theme == "volcanic":
        add("VolcanicBrazier", 0, 0, 0, 1.3)
        add("StiltHut", -16, -13, 25)
        add("StiltHut", 16, -14, -25)
        add("StiltHut", -19, 10, 90)
        add("StiltHut", 19, 10, -90)
        add("CrateStack", 6, -8, 10)
        add("Barrels", -6, 9, 40)
        add("LogPile", 9, 6, 80)
        add("BasaltColumns", -6, -15, 0, 0.6)
        for a in (45, 135, 225, 315):
            add("VolcanicBrazier", 12 * math.cos(math.radians(a)), 12 * math.sin(math.radians(a)), 0)


if __name__ == "__main__":
    import sys
    from assets import ASSETS
    theme = sys.argv[1] if len(sys.argv) > 1 else "voxel"
    m = build_island(theme)
    dbg = m["debug"]
    tier, path, plaza = dbg["tier"], dbg["path"], dbg["plaza"]
    for j in range(N):
        row = ""
        for i in range(N):
            cell = (i, j)
            if cell in path:
                row += "=" if path[cell][1] == "wood" else "#"
            elif cell in plaza:
                row += "@"
            elif cell in dbg["lava"]:
                row += "~"
            elif cell in dbg["pond"]:
                row += "o"
            elif cell in dbg["lake"]:
                row += "w"
            elif cell in tier:
                t = tier[cell]
                row += ":" if t == 0 else str(t % 10)
            else:
                row += " "
        if row.strip():
            print(row)
    missing = sorted({p[0] for p in m["props"]} - set(ASSETS))
    nprop = sum(len(ASSETS[p[0]]["boxes"]) for p in m["props"] if p[0] in ASSETS)
    print(theme, {g: len(b) for g, b in m["groups"]}, "props", len(m["props"]), "prop parts", nprop,
          "missing assets", missing)
