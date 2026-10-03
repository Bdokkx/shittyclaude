"""Voxel island generator, modelled on the reference render:

  * a rocky terraced mountain in the middle with a stair path winding to the top
  * two flat-topped mesas (west with a rock arch, east with a banner + cave below)
  * an open cobblestone village plaza south of the mountain
  * wooden stairs from the plaza down to a beach with a dock and rowboat
  * stepped turquoise shallows and mossy rock outcrops offshore
  * every cliff face covered in chunky, multi-shade protruding blocks with a
    yellow band and grass lip, plus clutter everywhere (tufts, flowers, ferns,
    mushrooms, rocks, bushes, fences, torches)

Output: dict(terrain=[boxes], props=[...], water=..., spawn=...)
"""
import math
import random
from collections import deque

from noise import fbm, weighted

CELL = 4
N = 124
K = 1.2       # layout scale: everything spreads out by this much (roomier map)
PATH_R = 2.3  # path half-width in cells (~5 cells / 20 studs wide)
BED = -10
BEACH_TOP = 3
TIER = 10


def tier_top(t):
    return BEACH_TOP + 1 + TIER * t if t > 0 else BEACH_TOP


ROCK = [("rock", 3), ("rock_dark", 2.2), ("rock_light", 1.3), ("rock_gray", 1.2),
        ("rock_deep", 1.1), ("moss", 0.3), ("moss_dark", 0.2)]
BAND = [("sand", 4), ("sand_dark", 2), ("sand_light", 1)]
SAND_TOP = [("sand", 5), ("sand_light", 2), ("sand_dark", 1)]
SAND_SIDE = [("sand", 3), ("sand_dark", 2), ("sand_wet", 1.5)]
GRASS = [("grass", 6), ("grass_dark", 2.5), ("grass_light", 2), ("moss", 0.6)]
COBBLE = [("cobble", 4), ("cobble_dark", 2), ("cobble_light", 2), ("path", 1.4), ("stone", 1)]
ROCKTOP = [("rock", 2), ("rock_light", 2), ("rock_gray", 1.5), ("moss", 1.4), ("moss_dark", 0.8)]

DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


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
                if a == 1:
                    out.append((x1, y, z0 + u0, x1 + p, yb, z0 + u1, col))
                elif a == -1:
                    out.append((x0 - p, y, z0 + u0, x0, yb, z0 + u1, col))
                elif b == 1:
                    out.append((x0 + u0, y, z1, x0 + u1, yb, z1 + p, col))
                else:
                    out.append((x0 + u0, y, z0 - p, x0 + u1, yb, z0, col))
                y = yb


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


def build_island(seed=7):
    rng = random.Random(seed)
    c = N / 2

    # ------------------------------------------------------------ 1. height field (tiers)
    MESAS = [(-27 * K, -3 * K, 10.5 * K, 4.4), (27 * K, 2 * K, 9.5 * K, 4.4)]
    MOUNT = (1, -11 * K)
    tier = {}
    for j in range(N):
        for i in range(N):
            dx, dz = i + 0.5 - c, j + 0.5 - c
            r = math.hypot(dx, dz * 1.08) / (37.5 * K) + (fbm(i / 12, j / 12, seed + 1) - 0.5) * 0.42
            land = 1 - r
            n = (fbm(i / 7, j / 7, seed + 2) - 0.5) * 1.3
            base = land * 6.0 + n
            md = math.hypot(dx - MOUNT[0], dz - MOUNT[1]) / (20 * K)
            mount = 8.8 * max(0.0, 1 - md) ** 1.05 + n * 0.45
            mesa = 0.0
            for mx, mz, mr, mh in MESAS:
                d = math.hypot(dx - mx, dz - mz) / mr + (fbm(i / 4, j / 4, seed + 5) - 0.5) * 0.3
                if d < 1:
                    mesa = max(mesa, mh * min(1.0, (1 - d) * 5))
            if land <= 0 and mesa <= 0:
                continue
            h = max(base, mount, mesa)
            if h < 0.15 and mesa <= 0:
                continue  # water
            tier[(i, j)] = 0 if h < 0.5 else min(9, int(h))

    # ------------------------------------------------------------ 2. village plaza
    pi, pj = int(c) + 1, int(c + 11 * K)
    PLAZA_T = 2
    plaza_r = 8.5
    PS = plaza_r / 6.6  # spread the plaza furniture to match
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

    top = {cell: tier_top(t) for cell, t in tier.items()}

    # ------------------------------------------------------------ 3. paths
    shore_j = next(jj for jj in range(pj, N) if (pi, jj) not in tier)
    peak = max(((i, j) for (i, j) in tier if abs(i - c - MOUNT[0]) < 5 and abs(j - c - MOUNT[1]) < 5),
               key=lambda k: tier[k])
    west = (int(c - 27 * K), int(c - 3 * K))
    east = (int(c + 27 * K), int(c + 2 * K))
    PATHS = [
        # (style, waypoints, start height, end height)
        ("wood", [(pi + 0.5, pj + plaza_r - 0.5), (pi + 0.5, shore_j - 1.5)], tier_top(PLAZA_T), BEACH_TOP),
        ("cobble", [(pi + 0.5, pj - plaza_r + 0.5), (pi + 13, pj - 17), (pi + 10, pj - 31),
                    (pi - 3, pj - 38), (peak[0] - 6.5, peak[1] - 3.5),
                    (peak[0] + 0.5, peak[1] + 0.5)], tier_top(PLAZA_T), top[peak]),
        ("cobble", [(pi - plaza_r + 0.5, pj + 0.5), (pi - 15, pj - 1), (pi - 23, pj - 7),
                    (west[0] + 0.5, west[1] + 0.5)], tier_top(PLAZA_T), top[west]),
        ("cobble", [(pi + plaza_r - 0.5, pj + 1.5), (pi + 16, pj - 1), (pi + 23, pj - 7),
                    (east[0] + 0.5, east[1] + 0.5)], tier_top(PLAZA_T), top[east]),
    ]
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
                    if d > PATH_R or (ii, jj) in plaza:
                        continue
                    old = path.get((ii, jj))
                    if old is None or d < old[3]:
                        path[(ii, jj)] = (h, style, (dx, dz), d)
    for cell, (h, style, _, _) in path.items():
        tier.setdefault(cell, 0)
        top[cell] = h
    # no narrow canyons: terrain right beside a path is at most one ledge (6 studs) above it
    for cell, (d, h) in near.items():
        if cell in tier and cell not in path and cell not in plaza:
            limit = h + 6 + max(0.0, d - PATH_R - 2) * 4
            if top[cell] > limit:
                top[cell] = limit

    # beach landing around the dock
    for jj in range(shore_j - 4, shore_j):
        for ii in range(pi - 7, pi + 9):
            if (ii, jj) not in path and (ii, jj) in tier and tier[(ii, jj)] > 0:
                tier[(ii, jj)] = 0
                top[(ii, jj)] = BEACH_TOP

    # ------------------------------------------------------------ 4. surfaces + bumps
    surface = {}
    for cell, t in tier.items():
        i, j = cell
        if cell in path or cell in plaza:
            continue
        if t == 0:
            surface[cell] = "sand"
            continue
        mountainish = math.hypot(i - c - MOUNT[0], j - c - MOUNT[1]) < 17
        if t >= 3 and mountainish and fbm(i / 3.5, j / 3.5, seed + 8) > 0.47:
            surface[cell] = "rocktop"
        else:
            surface[cell] = "grass"
        if fbm(i / 3, j / 3, seed + 9) > 0.7 and not any(
                (i + a, j + b) in path or (i + a, j + b) in plaza
                for a in (-1, 0, 1) for b in (-1, 0, 1)):
            top[cell] += 2  # small raised ledge

    # ------------------------------------------------------------ 5. shallows (stepped)
    depth = {}
    q = deque()
    for cell in tier:
        q.append((cell, 0))
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

    def patch(cell, pal, sd):
        """Colour from smooth noise patches (neighbours merge into bigger parts) plus a
        sprinkle of single-cell accents."""
        if cobble_rng.random() < 0.08:
            return weighted(cobble_rng, pal)
        v = fbm(cell[0] / 4.5, cell[1] / 4.5, seed + sd)
        k = min(len(pal) - 1, int(max(0.0, (v - 0.3) / 0.4) * len(pal)))
        order = sorted(pal, key=lambda kv: -kv[1])
        return order[min(k, 2)][0]

    # ------------------------------------------------------------ 6. terrain columns
    terrain = []
    body, band, cap = {}, {}, {}
    tiles = []
    cobble_rng = random.Random(seed + 40)
    for cell, t in tier.items():
        T = top[cell]
        if cell in path or cell in plaza:
            style = path[cell][1] if cell in path else "cobble"
            body[cell] = ("rock", T - 3)
            band[cell] = ("path_dirt", T - 3, T - 1)
            i, j = cell
            x0, z0 = (i - N / 2) * CELL, (j - N / 2) * CELL
            if style == "wood":
                dx, dz = path[cell][2]
                along_x = abs(dx) > abs(dz)
                for k in range(2):
                    cc = "plank" if (i + j + k) % 2 else "wood"
                    jit = cobble_rng.choice((0, 0.1))
                    if along_x:
                        tiles.append((x0 + 2 * k, T - 1, z0, x0 + 2 * k + 2, T + jit, z0 + 4, cc))
                    else:
                        tiles.append((x0, T - 1, z0 + 2 * k, x0 + 4, T + jit, z0 + 2 * k + 2, cc))
            else:
                if cobble_rng.random() < 0.5:   # four 2x2 cobbles
                    rects = [(2 * a, 2 * b, 2 * a + 2, 2 * b + 2) for a in range(2) for b in range(2)]
                elif cobble_rng.random() < 0.5:  # two 4x2 slabs
                    rects = [(0, 0, 4, 2), (0, 2, 4, 4)]
                else:
                    rects = [(0, 0, 2, 4), (2, 0, 4, 4)]
                for u0, v0, u1, v1 in rects:
                    jit = cobble_rng.choice((0, 0, 0.12, 0.25))
                    tiles.append((x0 + u0, T - 1, z0 + v0, x0 + u1, T + jit, z0 + v1,
                                  weighted(cobble_rng, COBBLE)))
            continue
        if t == 0:
            body[cell] = ("sand", T - 1)
            cap[cell] = (patch(cell, SAND_TOP, 21), T - 1, T)
        else:
            body[cell] = ("rock", T - 3)
            band[cell] = ("sand", T - 3, T - 1.5)
            pal = ROCKTOP if surface[cell] == "rocktop" else GRASS
            cap[cell] = (patch(cell, pal, 23), T - 1.5, T)
    shallow_body = {}
    for cell, d in depth.items():
        y = SHALLOW_Y[d]
        shallow_body[cell] = ("sand_wet" if d <= 2 else "sand" if d <= 4 else "sand_dark", y)

    def emit(grid_items, lo_fn, out):  # noqa: E306
        grid = {cell: key for cell, key in grid_items.items()}
        for i0, j0, i1, j1, key in greedy(grid, N, N):
            out.append(cell_box(i0, j0, i1, j1, lo_fn(key), key[-1], key[0]))

    # Ground = land/beach columns (swapped for the deformed terrain mesh later, kept as
    # invisible collision); Shallows = underwater sand; Paths = cobbles/planks; Cliffs = facades
    shallows = []
    emit(body, lambda key: BED, terrain)
    emit(band, lambda key: key[1], terrain)
    emit(cap, lambda key: key[1], terrain)
    emit(shallow_body, lambda key: BED, shallows)
    shallows.append((-1000, BED - 2, -1000, 1000, BED, 1000, "seabed"))
    paths = list(tiles)
    cliffs = []

    # ------------------------------------------------------------ 7. cliff facades
    reserved = set()  # (cell, dir) faces kept clear for set pieces
    facade_rng = random.Random(seed + 50)

    def facade(cell, d, layers):
        x0, z0 = (cell[0] - N / 2) * CELL, (cell[1] - N / 2) * CELL
        facade_boxes(cliffs, facade_rng, x0, z0, d, layers)

    # set pieces that need a clean cliff face: cave entrance on the east side
    props = []
    cave = None
    FACING_ROT = {(0, 1): 0, (1, 0): 90, (0, -1): 180, (-1, 0): 270}
    for (i, j), t in sorted(tier.items(), key=lambda kv: (-kv[0][0], kv[0][1])):
        if t != 0 or i < c + 8 or (i, j) in path:
            continue
        for d in ((0, 1), (1, 0), (-1, 0)):  # direction the cave mouth faces
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

    for cell, t in tier.items():
        T = top[cell]
        for d in DIRS:
            nb = (cell[0] + d[0], cell[1] + d[1])
            if (cell, d) in reserved:
                continue
            nt = top_of(nb)
            lo = max(nt if nt is not None else BED, -1.5)
            if T - lo < 1.6:
                continue
            if cell in path or cell in plaza:
                layers = [(lo, T - 3, ROCK, (0.25, 1.0), (3, 4, 5)),
                          (T - 3, T - 1, "path_dirt", (0.15, 0.35), None)]
                facade(cell, d, [(max(y0, lo), y1, p, pr, ch) for (y0, y1, p, pr, ch) in layers
                                 if y1 - max(y0, lo) > 0.3])
            elif t == 0:
                facade(cell, d, [(lo, T, SAND_SIDE, (0.15, 0.4), (1.5, 2))])
            else:
                cap_col = cap[cell][0]
                if facade_rng.random() < 0.3:  # grass lip draping over the band
                    layers = [(lo, T - 3, ROCK, (0.25, 1.0), (3, 4, 5)),
                              (T - 3, T, cap_col, (0.45, 0.7), None)]
                else:
                    layers = [(lo, T - 3, ROCK, (0.25, 1.0), (3, 4, 5)),
                              (T - 3, T - 1.5, BAND, (0.2, 0.4), None),
                              (T - 1.5, T, cap_col, (0.12, 0.3), None)]
                facade(cell, d, [(max(y0, lo), y1, p, pr, ch) for (y0, y1, p, pr, ch) in layers
                                 if y1 - max(y0, lo) > 0.3])

    # ------------------------------------------------------------ 8. props
    blocked = set(plaza) | set(path)
    if cave:
        for a in range(-2, 3):
            for b in range(0, 3):
                blocked.add((cave[0] + a, cave[1] + b))

    def block(ci, cj, r):
        for jj in range(cj - r, cj + r + 1):
            for ii in range(ci - r, ci + r + 1):
                blocked.add((ii, jj))

    PT = tier_top(PLAZA_T)
    px, pz = wx(pi), wx(pj)
    props += [
        prop("Campfire", px, PT, pz + 2 * PS, 15),
        prop("MarketStall", px - 13 * PS, PT, pz - 10 * PS, 12),
        prop("CrateStack", px - 21 * PS, PT, pz - 4 * PS, -30),
        prop("WoodFrame", px + 12 * PS, PT, pz - 13 * PS, -20),
        prop("Barrels", px + 19 * PS, PT, pz - 6 * PS, 40),
        prop("Statue", px - 18 * PS, PT, pz + 11 * PS, 35),
        prop("Well", px + 17 * PS, PT, pz + 11 * PS, 0),
        prop("Bench", px - 7 * PS, PT, pz + 14 * PS, 180),
        prop("Bench", px + 7 * PS, PT, pz + 9 * PS, 160),
        prop("Signpost", px + 6 * PS, PT, pz + 22 * PS, 200),
        prop("LogPile", px + 4 * PS, PT, pz - 20 * PS, 75),
    ]
    for a in (30, 150, 210, 330):
        props.append(prop("LampPost", px + 23 * PS * math.cos(math.radians(a)), PT,
                          pz + 23 * PS * math.sin(math.radians(a)), -a))
    spawn = (px - 6, PT, pz + 18 * PS)

    def edge_cell(cell):
        t = top[cell]
        for d in DIRS:
            nt = top_of((cell[0] + d[0], cell[1] + d[1]))
            if nt is None or nt < t - 1.5:
                return True
        return False

    def safe_xy(cell, x, z, margin=2.8):
        """Move a prop inside its cell so it stays `margin` studs clear of every edge that
        drops away (the terrain mesh pulls those edges in). None if the cell is too narrow."""
        cx, cz = wx(cell[0]), wx(cell[1])
        t = top[cell]
        for d in DIRS:
            nt = top_of((cell[0] + d[0], cell[1] + d[1]))
            if nt is None or nt < t - 1.5:
                limit = 2 - margin               # max offset from centre towards that edge
                if d[0]:
                    off = (x - cx) * d[0]
                    if off > limit:
                        x = cx + limit * d[0]
                else:
                    off = (z - cz) * d[1]
                    if off > limit:
                        z = cz + limit * d[1]
        # opposite drops can't both be satisfied
        for d in DIRS:
            nt = top_of((cell[0] + d[0], cell[1] + d[1]))
            if nt is None or nt < t - 1.5:
                off = ((x - cx) * d[0]) if d[0] else ((z - cz) * d[1])
                if off > 2 - margin + 1e-6:
                    return None
        return x, z

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
                x = wx(i) + d[0] * 1.6
                z = wx(j) + d[1] * 1.6
                props.append(prop("Fence", x, h, z, 90 if d[0] else 0))
        count += 1
        if style == "cobble" and count % 23 == 0 and dist > PATH_R - 0.8:
            spot = safe_xy(cell, wx(i), wx(j))
            if spot:
                props.append(prop("Torch", spot[0], h, spot[1], 0))

    # dock + boat + beach clutter
    dock_z = (shore_j - N / 2) * CELL - 6
    props.append(prop("Dock", px + 2, BEACH_TOP + 0.4, dock_z, 0))
    props.append(prop("Rowboat", px - 10, 0, dock_z + 22, -14))
    props.append(prop("Barrels", px - 8, BEACH_TOP, dock_z - 3, 20))
    props.append(prop("CrateStack", px + 12, BEACH_TOP, dock_z - 4, -10))
    props.append(prop("LampPost", px + 8, BEACH_TOP, dock_z + 1, 0, 0.9))
    block(pi, shore_j - 1, 3)

    # banner on the east mesa, arch in front of the west mesa
    flag = (east[0] + 1, east[1] - 3)
    props.append(prop("FlagFrame", wx(flag[0]), top[flag], wx(flag[1]), 90))
    block(flag[0], flag[1], 2)
    # ---- the rock arch is a gateway the west/east path walks through: pick the spot
    # where the path cuts between the highest ground on both sides
    best = None
    for idx in (2, 3, 1):
        style, pts, h0, h1 = PATHS[idx]
        samples, total = polyline_samples(pts, step=1.0)
        for sx, sz, sdist, dx, dz in samples:
            f = sdist / total
            if not 0.3 < f < 0.8:
                continue
            h = h0 + (h1 - h0) * f
            px_, pz_ = -dz, dx  # perpendicular
            walls = []
            for side in (-1, 1):
                cx_ = int(sx + side * px_ * (PATH_R + 1.5))
                cz_ = int(sz + side * pz_ * (PATH_R + 1.5))
                walls.append(top.get((cx_, cz_), BED) - h)
            score = min(walls) + (4 if idx == 2 else 0)
            if best is None or score > best[0]:
                best = (score, sx, sz, dx, dz, h)
    _, sx, sz, dx, dz, h = best
    ax, az = (sx - N / 2) * CELL, (sz - N / 2) * CELL
    props.append(prop("Arch", ax, h - 0.5, az, math.degrees(math.atan2(dx, dz)), 1.1))
    block(int(sx), int(sz), 3)
    props[:] = [p for p in props if not (p[0] in ("Torch", "Fence") and math.hypot(p[1] - ax, p[3] - az) < 18)]

    # ---- rocks that grow out of the island (cliff-coloured, grassy tops)
    # (edge_cell: the deformed terrain mesh pulls cliff edges in by up to ~2.5 studs, so nothing
    # small gets placed on a cell that drops off on any side - it would float)
    feature = []

    def clear_of(x, z, r):
        return all(math.hypot(x - a, z - b) > r + rr for a, b, rr in feature)

    def near_path(cell, r):
        return any((cell[0] + a, cell[1] + b) in path or (cell[0] + a, cell[1] + b) in plaza
                   for a in range(-r, r + 1) for b in range(-r, r + 1))

    # crags and clusters half-buried at the foot of tall cliffs
    feet = []
    for cell, t in tier.items():
        if cell in blocked or near_path(cell, 1) or edge_cell(cell):
            continue
        for d in DIRS:
            nb = (cell[0] + d[0], cell[1] + d[1])
            if nb in top and nb not in path and top[nb] - top[cell] >= 9:
                feet.append((top[nb] - top[cell] + rng.random() * 6, cell, d))
    feet.sort(key=lambda f: -f[0])
    placed_feet = 0
    for score, cell, d in feet:
        if placed_feet >= 22:
            break
        drop = top[(cell[0] + d[0], cell[1] + d[1])] - top[cell]
        x, z = wx(cell[0]) + d[0] * 1.5, wx(cell[1]) + d[1] * 1.5
        if drop >= 16:
            name, sc = "CliffCrag", max(0.6, min(1.5, drop / 30))
        else:
            name, sc = rng.choice(("CliffRocks", "LedgeRock")), rng.uniform(0.9, 1.3)
        if not clear_of(x, z, 9 * sc + 8):
            continue
        props.append(prop(name, x, top[cell] - 1.5, z, rng.uniform(0, 360), sc))
        feature.append((x, z, 9 * sc))
        block(cell[0], cell[1], 1)
        placed_feet += 1

    # craggy spires up on the mountain
    mcells = [cell for cell, t in tier.items()
              if t >= 4 and math.hypot(cell[0] - c - MOUNT[0], cell[1] - c - MOUNT[1]) < 15
              and cell not in blocked and not near_path(cell, 2)]
    rng.shuffle(mcells)
    for cell in mcells[:40]:
        x, z = wx(cell[0]), wx(cell[1])
        sc = rng.uniform(0.6, 1.0)
        if clear_of(x, z, 9 * sc + 14):
            props.append(prop("CliffCrag", x, top[cell] - 2, z, rng.uniform(0, 360), sc))
            feature.append((x, z, 9 * sc))
            block(cell[0], cell[1], 1)

    # rock clusters out in the open terraces
    fcells = [cell for cell, t in tier.items()
              if 1 <= t <= 3 and surface.get(cell) == "grass" and cell not in blocked
              and not near_path(cell, 2)]
    rng.shuffle(fcells)
    n_field = 0
    for cell in fcells:
        if n_field >= 12:
            break
        x, z = wx(cell[0]), wx(cell[1])
        sc = rng.uniform(0.9, 1.4)
        if clear_of(x, z, 9 * sc + 30):
            props.append(prop(rng.choice(("CliffRocks", "LedgeRock")), x, top[cell] - 1.5, z,
                              rng.uniform(0, 360), sc))
            feature.append((x, z, 9 * sc))
            block(cell[0], cell[1], 1)
            n_field += 1

    # lookout on the summit
    props.append(prop("RuinPillar", wx(peak[0] + 2), top[peak], wx(peak[1] + 1), 20))
    spot = safe_xy(peak, wx(peak[0]) - 1.5, wx(peak[1]) - 1.5, margin=3.2)
    if spot:
        props.append(prop("Torch", spot[0], top[peak], spot[1], 0))
    props.append(prop("Signpost", wx(peak[0] + 1), top[peak], wx(peak[1] - 2), 120))
    block(peak[0], peak[1], 2)

    # trees and ground clutter
    trees = set()
    cells = sorted(tier)
    rng.shuffle(cells)
    for cell in cells:
        if cell in blocked:
            continue
        i, j = cell
        t = tier[cell]
        T = top[cell]
        jx, jz = rng.uniform(-1.1, 1.1), rng.uniform(-1.1, 1.1)
        safe = safe_xy(cell, wx(i) + jx, wx(j) + jz)
        if safe is None:
            continue
        x, z = safe
        near_path = any((i + a, j + b) in path or (i + a, j + b) in plaza
                        for a in (-2, -1, 0, 1, 2) for b in (-2, -1, 0, 1, 2))
        r = rng.random()
        if t >= 1 and surface[cell] == "grass":
            dense = fbm(i / 7, j / 7, seed + 4)
            if (not near_path and r < 0.03 + max(0, dense - 0.4) * 0.3
                    and not any((i + a, j + b) in trees for a in (-2, -1, 0, 1, 2) for b in (-2, -1, 0, 1, 2))):
                name = weighted(rng, [("PineTree", 5), ("PineTreeTall", 3), ("PineTreeSmall", 2)])
                props.append(prop(name, x, T, z, rng.choice((0, 90, 180, 270)) + rng.uniform(-6, 6),
                                  rng.uniform(0.9, 1.2)))
                trees.add(cell)
                continue
            r = rng.random()
            if r < 0.13:
                props.append(prop("GrassTuft", x, T, z, rng.uniform(0, 360), rng.uniform(0.9, 1.5)))
            elif r < 0.165:
                props.append(prop("Flowers", x, T, z, rng.uniform(0, 360), rng.uniform(0.9, 1.3),
                                  rng.choice((1, 2, 3, 6))))
            elif r < 0.215:
                props.append(prop("Fern", x, T, z, rng.uniform(0, 360), rng.uniform(1, 1.5)))
            elif r < 0.255:
                props.append(prop("Bush", x, T, z, rng.uniform(0, 360), rng.uniform(0.7, 1.1)))
            elif r < 0.275:
                props.append(prop("SmallRock", x, T, z, rng.uniform(0, 360), rng.uniform(0.9, 1.6)))
            elif r < 0.29:
                props.append(prop("Mushrooms", x, T, z, rng.uniform(0, 360), rng.uniform(0.9, 1.3)))
        elif t >= 1:  # bare rock tops on the mountain
            if r < 0.12:
                props.append(prop("SmallRock", x, T, z, rng.uniform(0, 360), rng.uniform(1, 1.8)))
            elif r < 0.22:
                props.append(prop("GrassTuft", x, T, z, rng.uniform(0, 360), rng.uniform(0.8, 1.2)))
            elif r < 0.25 and not near_path:
                props.append(prop("PineTreeSmall", x, T, z, rng.uniform(0, 360), rng.uniform(0.8, 1)))
        elif t == 0:
            if r < 0.035:
                props.append(prop("SmallRock", x, T, z, rng.uniform(0, 360), rng.uniform(1, 2)))
            elif r < 0.045:
                props.append(prop("GrassTuft", x, T, z, rng.uniform(0, 360), 1))

    # path-side clutter
    for cell in sorted(path):
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
                x, z = safe
                props.append(prop(rng.choice(("GrassTuft", "SmallRock", "Flowers", "Fern")), x, top[nb],
                                  z, rng.uniform(0, 360), 1, rng.choice((1, 3, 6))))

    # a few sea stacks right at the shoreline, rising out of the shallows next to the land
    placed = []
    shore = [cell for cell in sorted(depth) if depth[cell] <= 2]
    rng.shuffle(shore)
    for cell in shore:
        if len(placed) >= 7:
            break
        x, z = wx(cell[0]), wx(cell[1])
        if abs(cell[0] - pi) < 9 and cell[1] > shore_j - 3:
            continue  # keep the dock approach clear
        if any(math.hypot(x - a, z - b) < 70 for a, b in placed) or not clear_of(x, z, 14):
            continue
        name = weighted(rng, [("RockOutcrop", 3), ("RockOutcropBig", 2)])
        props.append(prop(name, x, SHALLOW_Y[depth[cell]] - 0.5, z, rng.uniform(0, 360), rng.uniform(1.1, 1.5)))
        placed.append((x, z))
    for cell in shore:
        if depth[cell] == 1 and rng.random() < 0.02:
            props.append(prop("RockOutcropSmall", wx(cell[0]), -1.5, wx(cell[1]), rng.uniform(0, 360),
                              rng.uniform(1.0, 1.5)))

    water = (-1000, BED - 2, -1000, 1000, 0, 1000)
    debug = {"tier": tier, "path": path, "plaza": plaza, "N": N}
    # what the Blender terrain mesh is built from: every non-underwater column
    mesh_cells = []
    for cell in tier:
        kind = "path" if (cell in path or cell in plaza) else ("beach" if tier[cell] == 0 else "land")
        mesh_cells.append((cell[0], cell[1], top[cell] - (1 if kind == "path" else 0), kind,
                           surface.get(cell, "")))
    groups = [("Ground", terrain), ("Shallows", shallows), ("Paths", paths), ("Cliffs", cliffs)]
    return {"terrain": terrain + shallows + paths + cliffs, "groups": groups, "props": props,
            "water": water, "spawn": spawn, "debug": debug, "mesh_cells": mesh_cells, "N": N,
            "cell": CELL}


if __name__ == "__main__":
    from assets import ASSETS
    m = build_island()
    tier, path, plaza = m["debug"]["tier"], m["debug"]["path"], m["debug"]["plaza"]
    for j in range(N):
        row = ""
        for i in range(N):
            if (i, j) in path:
                row += "=" if path[(i, j)][1] == "wood" else "#"
            elif (i, j) in plaza:
                row += "@"
            elif (i, j) in tier:
                t = tier[(i, j)]
                row += ":" if t == 0 else str(t % 10)
            else:
                row += " "
        print(row)
    nprop = sum(len(ASSETS[p[0]]["boxes"]) for p in m["props"])
    print("terrain boxes", len(m["terrain"]), "props", len(m["props"]), "prop parts", nprop,
          "total", len(m["terrain"]) + nprop)
