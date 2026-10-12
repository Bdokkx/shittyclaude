"""Building helpers shared by the map modules (all Roblox space)."""
import numpy as np

import spsgeo as G
from spsgeo import CF

# vertical panel orientations for plates turned on their side (Size = (a, 0.4, b))
#   PANEL_X: thin along world X; local X -> world Y (height a), local Z -> world Z (width b)
#   PANEL_Z: thin along world Z; local X -> world X (width a), local Z -> world -Y (height b)
PANEL_X = G.rz(90)
PANEL_Z = G.rx(90)


def panel_x(scene, parent, name, x_mid, y0, y1, z0, z1, color, **kw):
    """Upright 0.4-thick panel facing +-X. Height and width must be whole studs."""
    kw.setdefault("surfaces", "smooth")
    return scene.part(parent, name, (y1 - y0, 0.4, z1 - z0), CF((x_mid, (y0 + y1) / 2, (z0 + z1) / 2), PANEL_X),
                      color, **kw)


def panel_z(scene, parent, name, z_mid, x0, x1, y0, y1, color, **kw):
    """Upright 0.4-thick panel facing +-Z. Width and height must be whole studs."""
    kw.setdefault("surfaces", "smooth")
    return scene.part(parent, name, (x1 - x0, 0.4, y1 - y0), CF(((x0 + x1) / 2, (y0 + y1) / 2, z_mid), PANEL_Z),
                      color, **kw)


def wall_pieces(u0, u1, courses, openings):
    """Split a wall (along-wall range u0..u1, horizontal courses [(y0, y1, colour)]) around
    rectangular openings [(ua, ub, ya, yb)]. Returns [(ua, ub, ya, yb, colour)] with pieces
    of one course merged vertically where their spans match."""
    out = []
    for y0, y1, col in courses:
        ys = sorted({y0, y1} | {y for (_, _, ya, yb) in openings for y in (ya, yb) if y0 < y < y1})
        bands = []
        for ya, yb in zip(ys, ys[1:]):
            spans = [(u0, u1)]
            for (oa, ob, oy0, oy1) in openings:
                if oy0 < yb - 1e-9 and oy1 > ya + 1e-9:
                    nxt = []
                    for (a, b) in spans:
                        if ob <= a or oa >= b:
                            nxt.append((a, b))
                            continue
                        if oa > a:
                            nxt.append((a, oa))
                        if ob < b:
                            nxt.append((ob, b))
                    spans = nxt
            bands.append((ya, yb, spans))
        # merge identical spans across consecutive bands
        open_ = {}
        for ya, yb, spans in bands:
            nxt = {}
            for s in spans:
                if s in open_:
                    nxt[s] = (open_[s][0], yb)
                else:
                    nxt[s] = (ya, yb)
            for s, (a, b) in open_.items():
                if s not in nxt:
                    out.append((s[0], s[1], a, b, col))
            open_ = nxt
        for s, (a, b) in open_.items():
            out.append((s[0], s[1], a, b, col))
    return out


def merge_cells(cells):
    """Greedy merge of grid cells {(i, j): key} into rectangles [(i0, i1, j0, j1, key)] (half-open)."""
    left = dict(cells)
    out = []
    for (i, j) in sorted(cells):
        if (i, j) not in left:
            continue
        k = left[(i, j)]
        i1 = i + 1
        while left.get((i1, j)) == k:
            i1 += 1
        j1 = j + 1
        while all(left.get((ii, j1)) == k for ii in range(i, i1)):
            j1 += 1
        for ii in range(i, i1):
            for jj in range(j, j1):
                del left[(ii, jj)]
        out.append((i, i1, j, j1, k))
    return out


def partition(bounds, regions, background):
    """Split the rectangle bounds=(x0, x1, z0, z1) into non-overlapping rectangles.
    regions = [(x0, x1, z0, z1, key)], later ones win. Returns [(x0, x1, z0, z1, key)]."""
    X0, X1, Z0, Z1 = bounds
    xs = sorted({X0, X1} | {v for r in regions for v in (r[0], r[1]) if X0 < v < X1})
    zs = sorted({Z0, Z1} | {v for r in regions for v in (r[2], r[3]) if Z0 < v < Z1})
    cells = {}
    for i, (xa, xb) in enumerate(zip(xs, xs[1:])):
        for j, (za, zb) in enumerate(zip(zs, zs[1:])):
            cx, cz = (xa + xb) / 2, (za + zb) / 2
            key = background
            for r in regions:
                if r[0] <= cx <= r[1] and r[2] <= cz <= r[3]:
                    key = r[4]
            cells[(i, j)] = key
    out = []
    for i0, i1, j0, j1, k in merge_cells(cells):
        out.append((xs[i0], xs[i1], zs[j0], zs[j1], k))
    return out


# 3 x 5 pixel letters, top row first
FONT = {
    "P": ["###", "#.#", "###", "#..", "#.."],
    "I": ["###", ".#.", ".#.", ".#.", "###"],
    "Z": ["###", "..#", ".#.", "#..", "###"],
    "A": [".#.", "#.#", "###", "#.#", "#.#"],
    "S": ["###", "#..", "###", "..#", "###"],
    "H": ["#.#", "#.#", "###", "#.#", "#.#"],
    "C": ["###", "#..", "#..", "#..", "###"],
    "K": ["#.#", "#.#", "##.", "#.#", "#.#"],
    "O": ["###", "#.#", "#.#", "#.#", "###"],
    "N": ["#.#", "###", "###", "###", "#.#"],
    "E": ["###", "#..", "##.", "#..", "###"],
    "L": ["#..", "#..", "#..", "#..", "###"],
    "D": ["##.", "#.#", "#.#", "#.#", "##."],
    "T": ["###", ".#.", ".#.", ".#.", ".#."],
    "U": ["#.#", "#.#", "#.#", "#.#", "###"],
    "R": ["###", "#.#", "##.", "#.#", "#.#"],
    "M": ["#.#", "###", "###", "#.#", "#.#"],
    "V": ["#.#", "#.#", "#.#", "#.#", ".#."],
    "Y": ["#.#", "#.#", ".#.", ".#.", ".#."],
    "B": ["##.", "#.#", "##.", "#.#", "##."],
    "G": ["###", "#..", "#.#", "#.#", "###"],
    "W": ["#.#", "#.#", "###", "###", "#.#"],
    "F": ["###", "#..", "##.", "#..", "#.."],
    "1": [".#.", "##.", ".#.", ".#.", "###"],
    "2": ["###", "..#", "###", "#..", "###"],
    "4": ["#.#", "#.#", "###", "..#", "..#"],
    " ": ["...", "...", "...", "...", "..."],
}


def pixel_runs(text, gap=1):
    """Rectangles (col0, col1, row0, row1) in pixel units for a text, rows counted from the TOP."""
    cells = {}
    x = 0
    for ch in text:
        glyph = FONT[ch]
        for r, row in enumerate(glyph):
            for c, v in enumerate(row):
                if v == "#":
                    cells[(x + c, r)] = 1
        x += 3 + gap
    width = x - gap
    # merge vertically first (columns) then horizontally: prefer tall strokes
    rects = []
    left = dict(cells)
    for (c, r) in sorted(cells, key=lambda t: (t[0], t[1])):
        if (c, r) not in left:
            continue
        r1 = r + 1
        while (c, r1) in left:
            r1 += 1
        c1 = c + 1
        while all((c1, rr) in left for rr in range(r, r1)):
            c1 += 1
        for cc in range(c, c1):
            for rr in range(r, r1):
                del left[(cc, rr)]
        rects.append((c, c1, r, r1))
    return rects, width


def scatter_poisson(rng, bounds, n_target, min_dist_fn, accept_fn, tries=60000):
    """Dart throwing with a position-dependent minimum distance."""
    x0, x1, z0, z1 = bounds
    pts = []
    for _ in range(tries):
        if len(pts) >= n_target:
            break
        x, z = rng.uniform(x0, x1), rng.uniform(z0, z1)
        if not accept_fn(x, z):
            continue
        d = min_dist_fn(x, z)
        ok = True
        for (px, pz, pd) in pts:
            if (px - x) ** 2 + (pz - z) ** 2 < (max(d, pd)) ** 2:
                ok = False
                break
        if ok:
            pts.append((x, z, d))
    return [(x, z) for x, z, _ in pts]


def v(*a):
    return np.array(a, float)
