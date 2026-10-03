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
from island import ROCK as ROCK_FACADE
from island import build_island  # noqa: F401  (re-exported)
from island import facade_boxes
from palette import TINT_NAMES

REEF_LIP = [("reef_sand", 4), ("reef_sand_dk", 1.5), ("sand_light", 1)]

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

    # chunky multi-shade blocks on every exposed edge of the reef slab
    frng = random.Random(seed + 3)
    profile = {"main": (-4, 1, 2), "rim": (-8, -3, -2)}
    for (i, j), (k, s, _) in kind.items():
        bot, band, top = profile[k]
        for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nb = kind.get((i + d[0], j + d[1]))
            lo = bot if nb is None else profile[nb[0]][2]
            if top - lo < 1:
                continue
            layers = [(lo, band, ROCK_FACADE, (0.25, 0.8), (1.5, 2, 2.5)),
                      (max(band, lo), top, REEF_LIP, (0.15, 0.35), None)]
            facade_boxes(terrain, frng, (i - W / 2) * CELL, (j - H / 2) * CELL, d,
                         [ly for ly in layers if ly[1] - ly[0] > 0.3])
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
    for name, m in (("island", build_island()), ("reef", build_reef())):
        nparts = len(m["terrain"]) + sum(len(ASSETS[p[0]]["boxes"]) for p in m["props"])
        print(name, "terrain boxes", len(m["terrain"]), "props", len(m["props"]), "parts", nparts)
