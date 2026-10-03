"""Map layout generation for the Island and the Coral Reef.

Produces, per map:
  terrain: list of world-space boxes (x0, y0, z0, x1, y1, z1, color)
  props:   list of (asset, x, y, z, rotY, scale, tint, rotX, rotZ)
  water:   (x0, y0, z0, x1, y1, z1) or None
  spawn:   (x, y, z) or None
Everything is deterministic for a given seed.
"""
import math
import random

from assets import ASSETS
from palette import TINT_NAMES

CELL = 4  # studs per voxel column


# ---------------------------------------------------------------- noise

def _hash(i, j, seed):
    h = (i * 374761393 + j * 668265263 + seed * 982451653) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


def vnoise(x, z, seed):
    i, j = math.floor(x), math.floor(z)
    fx, fz = x - i, z - j
    sx, sz = fx * fx * (3 - 2 * fx), fz * fz * (3 - 2 * fz)
    a, b = _hash(i, j, seed), _hash(i + 1, j, seed)
    c, d = _hash(i, j + 1, seed), _hash(i + 1, j + 1, seed)
    return (a + (b - a) * sx) + ((c + (d - c) * sx) - (a + (b - a) * sx)) * sz


def fbm(x, z, seed, octaves=4):
    total, amp, freq, norm = 0.0, 1.0, 1.0, 0.0
    for o in range(octaves):
        total += vnoise(x * freq, z * freq, seed + o * 17) * amp
        norm += amp
        amp *= 0.5
        freq *= 2.0
    return total / norm


# ---------------------------------------------------------------- greedy meshing

def greedy(grid, w, h):
    """Merge equal-keyed cells into rectangles. grid[(i,j)] -> hashable key or None."""
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


def prop(name, x, y, z, rot=0, scale=1, tint=0, rx=0, rz=0):
    assert name in ASSETS or name == "SpawnLocation", name
    return (name, round(x, 2), round(y, 2), round(z, 2), round(rot, 1), round(scale, 2), tint,
            round(rx, 1), round(rz, 1))


# ================================================================ ISLAND

BED = -10          # bottom of every island column
WATER_Y = 0
BEACH_TOP = 4
TIER_STEP = 8      # tier k top = 4 + 8k
PLAZA_TOP = 20     # tier 2


def tier_top(t):
    return BEACH_TOP + TIER_STEP * t


def build_island(seed=7):
    rng = random.Random(seed)
    N = 100
    cx = cz = N / 2
    R = 31.0

    tier = {}  # (i,j) -> -2 deep, -1 shallow, 0 beach, 1..6 land
    for j in range(N):
        for i in range(N):
            dx, dz = (i + 0.5 - cx) / R, (j + 0.5 - cz) / R
            wob = (fbm(i / 9, j / 9, seed + 1) - 0.5) * 0.42
            r = math.hypot(dx, dz) + wob
            land = 1 - r
            m = math.exp(-((i - cx) ** 2 + (j - (cz - 8)) ** 2) / (2 * 9 ** 2))
            n = (fbm(i / 5, j / 5, seed + 2) - 0.5) * 0.35
            v = land * 1.1 + m * 0.75 + n
            if v < -0.12:
                t = -2
            elif v < 0:
                t = -1
            elif v < 0.07:
                t = 0
            else:
                t = min(8, 1 + int((v - 0.07) / 0.19))
            tier[(i, j)] = t

    # ---- plaza (flattened, path-surfaced) south of the mountain
    pci, pcj = int(cx), int(cz + 13)
    plaza_r = 7.5
    surf = {}
    tops = {}
    for (i, j), t in tier.items():
        d = math.hypot(i - pci, j - pcj)
        if d <= plaza_r:
            tier[(i, j)] = 2
            surf[(i, j)] = "path"
        elif d <= plaza_r + 2.5 and tier[(i, j)] < 2:
            tier[(i, j)] = 2

    # ---- stair path from the plaza south to the beach
    path_cells = set()
    j = pcj + int(plaza_r)
    shore_j = None
    for jj in range(j, N):
        if tier[(pci, jj)] < 0:
            shore_j = jj
            break
    assert shore_j is not None
    top = PLAZA_TOP
    path_top = {}
    for jj in range(j, shore_j):
        if jj > j:
            top = max(BEACH_TOP, top - 2)
        for ii in (pci - 1, pci, pci + 1):
            path_top[(ii, jj)] = top
            path_cells.add((ii, jj))
    # widen the beach around the landing
    for jj in range(shore_j - 3, shore_j):
        for ii in range(pci - 4, pci + 5):
            if (ii, jj) not in path_cells and tier[(ii, jj)] >= 0:
                tier[(ii, jj)] = 0

    # ---- grid of column keys
    grid = {}
    for (i, j), t in tier.items():
        if (i, j) in path_top:
            pt = path_top[(i, j)]
            kind = "beach" if pt == BEACH_TOP else "land"
            grid[(i, j)] = (kind, pt, "sand" if kind == "beach" else "cobble")
            tops[(i, j)] = pt
            continue
        if t == -2:
            continue
        if t == -1:
            grid[(i, j)] = ("shallow", -4, "sand")
            tops[(i, j)] = -4
        elif t == 0:
            grid[(i, j)] = ("beach", BEACH_TOP, "sand")
            tops[(i, j)] = BEACH_TOP
        else:
            s = surf.get((i, j))
            if s is None:
                s = "grass_dark" if fbm(i / 6, j / 6, seed + 9) > 0.58 else "grass"
            grid[(i, j)] = ("land", tier_top(t), s)
            tops[(i, j)] = tier_top(t)

    def wx(i):
        return (i - N / 2 + 0.5) * CELL

    terrain = []
    for i0, j0, i1, j1, (kind, top, s) in greedy(grid, N, N):
        x0, z0 = (i0 - N / 2) * CELL, (j0 - N / 2) * CELL
        x1, z1 = (i1 + 1 - N / 2) * CELL, (j1 + 1 - N / 2) * CELL
        if kind in ("shallow", "beach"):
            terrain.append((x0, BED, z0, x1, top, z1, s))
        else:
            terrain.append((x0, BED, z0, x1, top - 3, z1, "rock"))
            terrain.append((x0, top - 3, z0, x1, top - 1.5, z1, "sand"))
            terrain.append((x0, top - 1.5, z0, x1, top, z1, s))
    half = 300
    terrain.append((-half, BED - 4, -half, half, BED, half, "seabed"))

    # ---- props
    props = []
    blocked = set()

    def block(ci, cj, r):
        for jj in range(cj - r, cj + r + 1):
            for ii in range(ci - r, ci + r + 1):
                blocked.add((ii, jj))

    for (i, j) in path_cells:
        block(i, j, 1)
    for (i, j), s in surf.items():
        if s == "path":
            block(i, j, 1)

    px, pz = wx(pci), wx(pcj)
    props.append(prop("Campfire", px, PLAZA_TOP, pz, 15))
    props.append(prop("MarketStall", px - 14, PLAZA_TOP, pz - 12, 10))
    props.append(prop("CrateStack", px + 13, PLAZA_TOP, pz - 13, -20))
    props.append(prop("RuinPillar", px + 21, PLAZA_TOP, pz + 4, 30))
    props.append(prop("RuinPillar", px - 22, PLAZA_TOP, pz + 2, -15, 0.9))
    for a in (45, 135, 225, 315):
        props.append(prop("LampPost", px + 24 * math.cos(math.radians(a)), PLAZA_TOP,
                          pz + 24 * math.sin(math.radians(a)), -a))
    props.append(prop("Fence", px - 10, PLAZA_TOP, pz - 27, 0))
    props.append(prop("Fence", px + 10, PLAZA_TOP, pz - 27, 0))
    spawn = (px, PLAZA_TOP, pz + 18)

    # lamps along the stair path, alternating sides
    rows = sorted({jj for (_, jj) in path_cells})
    for k, jj in enumerate(rows[1::3]):
        ii = pci - 1 if k % 2 else pci + 1
        props.append(prop("LampPost", wx(ii) + (-1.2 if ii < pci else 1.2), path_top[(ii, jj)],
                          wx(jj), 180 if ii < pci else 0, 0.8))

    # dock + boat at the landing
    dock_z = (shore_j - N / 2) * CELL - 6
    props.append(prop("Dock", px, BEACH_TOP + 0.4, dock_z, 0))
    props.append(prop("Rowboat", px + 12, WATER_Y, dock_z + 26, 12))
    block(pci, shore_j, 3)

    # flag frame on the highest flat spot on the east side
    best = None
    for (i, j), t in tier.items():
        if i < cx + 10 or t < 2 or (i, j) in blocked:
            continue
        if all(tier.get((i + a, j + b)) == t for a in (-1, 0, 1) for b in (-1, 0, 1)):
            if best is None or t > best[0]:
                best = (t, i, j)
    if best:
        t, i, j = best
        props.append(prop("FlagFrame", wx(i), tier_top(t), wx(j), 90))
        block(i, j, 2)

    # rock arch on the west side
    for i in range(N):
        t = tier[(i, int(cz) + 4)]
        if t >= 1:
            ai = i + 5
            at = tier[(ai, int(cz) + 4)]
            props.append(prop("Arch", wx(ai), tier_top(max(at, 1)), wx(int(cz) + 4), 90))
            block(ai, int(cz) + 4, 3)
            break

    # trees, bushes, rocks
    trees = set()
    cells = sorted(tier.keys())
    rng.shuffle(cells)
    for (i, j) in cells:
        t = tier[(i, j)]
        if (i, j) in blocked or (i, j) in path_top:
            continue
        r = rng.random()
        jitter = lambda: rng.uniform(-1.2, 1.2)
        if t >= 1:
            dense = fbm(i / 8, j / 8, seed + 4)
            if r < 0.02 + dense * 0.075 and not any((i + a, j + b) in trees
                                                    for a in (-1, 0, 1) for b in (-1, 0, 1)):
                name = "PineTreeTall" if rng.random() < 0.3 else "PineTree"
                props.append(prop(name, wx(i) + jitter(), tier_top(t), wx(j) + jitter(),
                                  rng.choice((0, 90, 180, 270)) + rng.uniform(-8, 8),
                                  rng.uniform(0.75, 1.25)))
                trees.add((i, j))
            elif r < 0.30 and r > 0.27:
                props.append(prop("Bush", wx(i), tier_top(t), wx(j), rng.uniform(0, 360),
                                  rng.uniform(0.7, 1.2)))
            elif r > 0.992:
                props.append(prop("Rock", wx(i), tier_top(t), wx(j), rng.uniform(0, 360),
                                  rng.uniform(0.6, 1.0)))
        elif t == 0 and r < 0.025:
            props.append(prop("Rock", wx(i), BEACH_TOP, wx(j), rng.uniform(0, 360),
                              rng.uniform(0.7, 1.3)))
        elif t == -1 and r < 0.022:
            if rng.random() < 0.55:
                props.append(prop("RockSpire", wx(i), -4, wx(j), rng.uniform(0, 360),
                                  rng.uniform(0.6, 1.05)))
            else:
                props.append(prop("Rock", wx(i), -4, wx(j), rng.uniform(0, 360),
                                  rng.uniform(1.5, 2.4)))

    water = (-half, BED - 4, -half, half, WATER_Y, half)
    return {"terrain": terrain, "props": props, "water": water, "spawn": spawn,
            "debug": (tier, path_top, N)}


# ================================================================ REEF

def build_reef(seed=11):
    rng = random.Random(seed)
    W, H = 110, 84
    cx, cz = W / 2, H / 2

    kind = {}
    for j in range(H):
        for i in range(W):
            x, z = abs(i + 0.5 - cx) / (W * 0.47), abs(j + 0.5 - cz) / (H * 0.45)
            se = (x ** 3 + z ** 3) ** (1 / 3)
            v = 1 - se + (fbm(i / 9, j / 9, seed + 1) - 0.5) * 0.45
            if v < 0:
                continue
            k = "rim" if v < 0.07 else "main"
            s = "reef_sand"
            pn = fbm(i / 6, j / 6, seed + 5)
            if pn > 0.62:
                s = "reef_sand_dk"
            kind[(i, j)] = (k, s, v)

    grid = {c: (k, s) for c, (k, s, _) in kind.items()}
    terrain = []
    for i0, j0, i1, j1, (k, s) in greedy(grid, W, H):
        x0, z0 = (i0 - W / 2) * CELL, (j0 - H / 2) * CELL
        x1, z1 = (i1 + 1 - W / 2) * CELL, (j1 + 1 - H / 2) * CELL
        if k == "main":
            terrain.append((x0, -4, z0, x1, 1, z1, "rock"))
            terrain.append((x0, 1, z0, x1, 2, z1, s))
        else:
            terrain.append((x0, -8, z0, x1, -3, z1, "rock"))
            terrain.append((x0, -3, z0, x1, -2, z1, s))
    FLOOR = 2

    def wx(i):
        return (i - W / 2 + 0.5) * CELL

    def wz(j):
        return (j - H / 2 + 0.5) * CELL

    props = []
    ship = prop("Shipwreck", 4, -1.5, 0, 35, 1.0, 0, -4, 14)
    props.append(ship)
    ship_rot = math.radians(35)

    def near_ship(x, z, pad):
        # into ship-local space (Roblox: +rotY turns +Z toward +X)
        c, s = math.cos(ship_rot), math.sin(ship_rot)
        lx = (x - 4) * c - z * s
        lz = (x - 4) * s + z * c
        return abs(lx) < 10 + pad and abs(lz) < 34 + pad

    interior = [(i, j) for (i, j), (k, s, v) in kind.items() if v > 0.22]
    support = []  # (x0, z0, x1, z1, top)
    placed = []   # (x, z, radius)

    def free(x, z, r):
        return all(math.hypot(x - a, z - b) > r + rr for a, b, rr in placed)

    def place_formation(name, count, radius, rot90=True, scale=(1, 1)):
        tries = 0
        n = 0
        while n < count and tries < 4000:
            tries += 1
            i, j = rng.choice(interior)
            x, z = wx(i), wz(j)
            if near_ship(x, z, radius * 0.6) or not free(x, z, radius):
                continue
            rot = rng.choice((0, 90, 180, 270)) if rot90 else rng.uniform(0, 360)
            sc = round(rng.uniform(*scale), 2)
            props.append(prop(name, x, FLOOR, z, rot, sc))
            placed.append((x, z, radius))
            if rot90:
                for (x0, y0, z0, x1, y1, z1, _) in ASSETS[name]["boxes"]:
                    pts = [(x0, z0), (x1, z1)]
                    rp = []
                    for (ax, az) in pts:
                        r = math.radians(rot)
                        rx = ax * math.cos(r) + az * math.sin(r)
                        rz = -ax * math.sin(r) + az * math.cos(r)
                        rp.append((x + rx * sc, z + rz * sc))
                    support.append((min(rp[0][0], rp[1][0]), min(rp[0][1], rp[1][1]),
                                    max(rp[0][0], rp[1][0]), max(rp[0][1], rp[1][1]),
                                    FLOOR + y1 * sc))
            n += 1

    place_formation("ReefShelf", 5, 20, scale=(0.9, 1.2))
    place_formation("ReefPinnacle", 6, 11, scale=(0.9, 1.3))
    place_formation("ReefArch", 2, 16)
    place_formation("Boulder", 7, 7, scale=(0.8, 1.4))
    place_formation("RuinPillar", 5, 5, rot90=False, scale=(0.8, 1.2))

    def surface_at(x, z):
        top = FLOOR
        for (x0, z0, x1, z1, t) in support:
            if x0 + 1 <= x <= x1 - 1 and z0 + 1 <= z <= z1 - 1:
                top = max(top, t)
        return top

    kinds = [("TubeCoral", 0.36), ("BranchCoral", 0.22), ("FanCoral", 0.12), ("Seaweed", 0.30)]
    coral_pts = []
    tries = 0
    while len(coral_pts) < 190 and tries < 6000:
        tries += 1
        i, j = rng.choice(list(kind.keys()))
        if kind[(i, j)][0] != "main":
            continue
        x, z = wx(i) + rng.uniform(-1.5, 1.5), wz(j) + rng.uniform(-1.5, 1.5)
        if near_ship(x, z, 2):
            continue
        if any(math.hypot(x - a, z - b) < 6 for a, b in coral_pts):
            continue
        y = surface_at(x, z)
        if y == FLOOR and not free(x, z, 1):
            continue  # under an overhang edge / inside a boulder footprint
        r = rng.random()
        acc = 0
        for name, p in kinds:
            acc += p
            if r <= acc:
                break
        tint = 0 if name == "Seaweed" else rng.randrange(1, len(TINT_NAMES) + 1)
        sc = rng.uniform(1.0, 1.6) if name == "Seaweed" else rng.uniform(0.9, 1.5)
        props.append(prop(name, x, y, z, rng.uniform(0, 360), sc, tint))
        coral_pts.append((x, z))

    return {"terrain": terrain, "props": props, "water": None,
            "spawn": (wx(int(W * 0.2)), FLOOR, wz(int(H * 0.5)))}


if __name__ == "__main__":
    isl = build_island()
    tier, path_top, N = isl["debug"]
    ch = {-2: " ", -1: ".", 0: ":"}
    for j in range(N):
        print("".join("#" if (i, j) in path_top else ch.get(tier[(i, j)], str(tier[(i, j)]))
                      for i in range(N)))
    reef = build_reef()
    for name, m in (("island", isl), ("reef", reef)):
        nparts = len(m["terrain"]) + sum(len(ASSETS[p[0]]["boxes"]) for p in m["props"]
                                          if p[0] in ASSETS)
        print(name, "terrain boxes", len(m["terrain"]), "props", len(m["props"]), "≈parts", nparts)
