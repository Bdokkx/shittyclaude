"""Terrain in the reef-target style: big angled slabs and shelves, calm colours.

* ground tops: one base colour + one patch colour in large soft patches (>= 8x8 studs)
* cliffs: stacked slabs 6-14 wide, 2-5 thick, tilted 4-14 deg, overhanging 1-3 studs, coloured by
  HEIGHT BAND (light top / mid / dark base), with one continuous grass lip + sand strip on top
* beaches step into the water in wide shelves; reef shelves are the same slab stacks with sand tops
"""
import math
import random

from core import poly_contains, resample

CELL = 4


def _pnoise(x, z, seed):
    """Smooth value noise (0..1)."""
    def h(i, j):
        v = (i * 374761393 + j * 668265263 + seed * 982451653) & 0xFFFFFFFF
        v = ((v ^ (v >> 13)) * 1274126177) & 0xFFFFFFFF
        return ((v ^ (v >> 16)) & 0xFFFF) / 65535.0
    i, j = math.floor(x), math.floor(z)
    fx, fz = x - i, z - j
    sx, sz = fx * fx * (3 - 2 * fx), fz * fz * (3 - 2 * fz)
    a, b, c, d = h(i, j), h(i + 1, j), h(i, j + 1), h(i + 1, j + 1)
    return a + (b - a) * sx + (c - a) * sz + (a - b - c + d) * sx * sz


def noise2(x, z, seed, scale):
    return 0.65 * _pnoise(x / scale, z / scale, seed) + 0.35 * _pnoise(x / scale * 2.1, z / scale * 2.1, seed + 7)


def blob(cx, cz, r, seed, amp=0.14, n=120, stretch=(1.0, 1.0)):
    """Organic closed outline (counter-clockwise in x/z)."""
    rng = random.Random(seed)
    waves = [(k, rng.uniform(0, 6.283), amp / (1 + 0.55 * k)) for k in range(2, 7)]
    pts = []
    for i in range(n):
        a = i * 2 * math.pi / n
        rr = r * (1 + sum(w * math.sin(k * a + ph) for k, ph, w in waves))
        pts.append((cx + math.cos(a) * rr * stretch[0], cz + math.sin(a) * rr * stretch[1]))
    return pts


def grow(poly, d):
    """Push every outline point out from the polygon centroid by d studs."""
    cx = sum(p[0] for p in poly) / len(poly)
    cz = sum(p[1] for p in poly) / len(poly)
    out = []
    for x, z in poly:
        dx, dz = x - cx, z - cz
        L = math.hypot(dx, dz) or 1
        out.append((x + dx / L * d, z + dz / L * d))
    return out


def greedy(cells):
    """cells: {(i, j): key} -> rectangles (i0, j0, i1, j1, key)."""
    used, rects = set(), []
    for (i, j) in sorted(cells, key=lambda c: (c[1], c[0])):
        if (i, j) in used:
            continue
        key = cells[(i, j)]
        i1 = i
        while cells.get((i1 + 1, j)) == key and (i1 + 1, j) not in used:
            i1 += 1
        j1 = j
        while all(cells.get((k, j1 + 1)) == key and (k, j1 + 1) not in used for k in range(i, i1 + 1)):
            j1 += 1
        for jj in range(j, j1 + 1):
            for ii in range(i, i1 + 1):
                used.add((ii, jj))
        rects.append((i, j, i1, j1, key))
    return rects


class Terrain:
    """Height regions (outline polygons with a top height), filled on a 4-stud grid."""

    def __init__(self, extent):
        self.extent = extent
        self.regions = []   # (name, poly, top)

    def add(self, name, poly, top):
        self.regions.append((name, poly, top))

    def region_at(self, x, z):
        best = None
        for name, poly, top in self.regions:
            if poly_contains(poly, x, z) and (best is None or top >= best[2]):
                best = (name, poly, top)
        return best

    def top_at(self, x, z, default=None):
        r = self.region_at(x, z)
        return r[2] if r else default

    def fill(self, m, colors, seed, body_color, patch_scale=34, patch_cut=0.6, floor=-2.0):
        """colors: region name -> (base, patch) colours. One top layer + one body per merged rectangle."""
        cells = {}
        n = int(self.extent / CELL)
        for i in range(-n, n):
            for j in range(-n, n):
                x, z = (i + 0.5) * CELL, (j + 0.5) * CELL
                r = self.region_at(x, z)
                if not r:
                    continue
                base, patch = colors[r[0]]
                tone = patch if (patch and noise2(x, z, seed, patch_scale) > patch_cut) else base
                cells[(i, j)] = (r[0], r[2], tone)
        lower = {name: top for name, _, top in self.regions}
        for i0, j0, i1, j1, (name, top, tone) in greedy(cells):
            x0, z0, x1, z1 = i0 * CELL, j0 * CELL, (i1 + 1) * CELL, (j1 + 1) * CELL
            m.span((x0, top - 1, z0), (x1, top, z1), tone)
        # bodies merged regardless of tone (hidden under the tops)
        body = {c: (v[0], v[1]) for c, v in cells.items()}
        for i0, j0, i1, j1, (name, top) in greedy(body):
            x0, z0, x1, z1 = i0 * CELL, j0 * CELL, (i1 + 1) * CELL, (j1 + 1) * CELL
            below = max([t for nm, t in lower.items() if t < top] + [floor])
            m.span((x0, below - 1, z0), (x1, top - 1, z1), body_color, shadow=False)
        return cells


def outward(poly, x, z, tx, tz):
    nx, nz = tz, -tx
    if poly_contains(poly, x + nx * 0.8, z + nz * 0.8):
        nx, nz = -nx, -nz
    return nx, nz


def cliff_ring(m, poly, y_top, low_fn, bands, lip, strip, seed, skip=None, step=(8, 12), inward=6.0,
               overhang=(1.2, 2.6), tilt=(4, 12), lip_thick=1.0, strip_thick=1.0):
    """Stacked slab cliff along a closed outline.
    bands: (light, mid, dark) rock colours by height; lip: top colour (grass/sand/snow); strip: band under the lip
    low_fn(x, z) -> height of the ground at the foot of the cliff at that point."""
    rng = random.Random(seed)
    pts = resample(poly, (step[0] + step[1]) / 2)
    for (x, z, tx, tz) in pts:
        if skip and skip(x, z):
            continue
        nx, nz = outward(poly, x, z, tx, tz)
        y_low = low_fn(x + nx * 4, z + nz * 4)
        if y_low is None or y_top - y_low < 1.0:
            continue
        w = rng.uniform(*step) + 2.5
        ry = math.degrees(math.atan2(nx, nz)) + rng.uniform(-6, 6)
        with m.at((x, 0, z), ry=ry):        # local +Z = out of the cliff, X along it
            o_lip = rng.uniform(*overhang)
            # grass lip + continuous sand strip (level, so the top surface stays flat)
            m.span((-w / 2, y_top - lip_thick + 0.2, -inward), (w / 2, y_top + 0.2, o_lip), lip)
            if strip:
                m.span((-w / 2 + 0.1, y_top - lip_thick - strip_thick + 0.2, -inward),
                       (w / 2 - 0.1, y_top - lip_thick + 0.2, o_lip - 0.35), strip)
            y = y_top - lip_thick - (strip_thick if strip else 0) + 0.2
            height = y_top - y_low
            k = 0
            while y > y_low - 0.5:
                th = min(rng.uniform(2.2, 4.6), y - (y_low - 1.2))
                if th < 0.6:
                    break
                yc = y - th / 2
                f = (yc - y_low) / max(height, 1e-3)
                col = bands[0] if f > 0.62 else bands[1] if f > 0.28 else bands[2]
                out = rng.uniform(-0.6, 2.0) if k else rng.uniform(0.0, o_lip - 0.4)
                ww = w + rng.uniform(-1.5, 1.0)
                a = rng.uniform(*tilt) * rng.choice((-1, 1))
                with m.at((rng.uniform(-1.0, 1.0), yc, 0), rx=a, rz=rng.uniform(-3, 3)):
                    m.span((-ww / 2, -th / 2, -inward), (ww / 2, th / 2, out), col)
                y -= th
                k += 1


def slab_stack(m, seed, height, width, bands, cap=None, cap_strip=None, taper=0.75, tilt=(4, 13), depth=None,
               layers=None):
    """Free-standing formation of stacked, offset, tilted slabs (sea stacks, hero rocks, reef pillars).
    Origin at its base. cap: colour of the top slab surface (grass / sand / snow)."""
    rng = random.Random(seed)
    depth = depth or width * 0.8
    y = 0.0
    k = 0
    while y < height - 0.5:
        th = min(rng.uniform(2.4, 5.0), height - y)
        f = y / max(height, 1)
        w = width * (1 - (1 - taper) * f) * rng.uniform(0.85, 1.12)
        d = depth * (1 - (1 - taper) * f) * rng.uniform(0.85, 1.12)
        col = bands[0] if f > 0.62 else bands[1] if f > 0.3 else bands[2]
        with m.at((rng.uniform(-1.4, 1.4), y + th / 2, rng.uniform(-1.4, 1.4)), ry=rng.uniform(-25, 25),
                  rx=rng.uniform(*tilt) * rng.choice((-1, 1)) * 0.6, rz=rng.uniform(*tilt) * rng.choice((-1, 1)) * 0.6):
            m.box((0, 0, 0), (w, th, d), col)
            top_slab = (w, d)
        y += th * 0.86
        k += 1
    if cap:
        w, d = top_slab
        with m.at((0, y + 0.3, 0), ry=rng.uniform(-20, 20)):
            if cap_strip:
                m.box((0, -0.25, 0), (w * 0.95 + 0.6, 0.8, d * 0.95 + 0.6), cap_strip)
            m.box((0, 0.45, 0), (w * 0.95 + 0.8, 1.0, d * 0.95 + 0.8), cap)
    return y


def stairs(m, start, end_y, direction, width, step_d, color, side, rail=None, lantern_every=0, lantern_fn=None,
           base_y=None):
    """Wide stairs from `start` (x, y, z) climbing to end_y along unit `direction` (dx, dz).
    Solid stone sides; optional rail callback(m, length) built in the stair's local frame."""
    x0, y0, z0 = start
    rise = end_y - y0
    nsteps = max(1, int(round(abs(rise))))
    dy = rise / nsteps
    ry = math.degrees(math.atan2(direction[0], direction[1]))
    base = (base_y if base_y is not None else min(y0, end_y)) - 1
    with m.at((x0, 0, z0), ry=ry):     # local +Z = up the stairs
        for k in range(nsteps):
            top = y0 + dy * (k + 1)
            zc = step_d * (k + 0.5)
            m.span((-width / 2, base, zc - step_d / 2), (width / 2, top, zc + step_d / 2 + 0.01),
                   color[k % 2] if isinstance(color, tuple) else color)
        length = step_d * nsteps
        for s in (-1, 1):   # side walls
            for k in range(0, nsteps, 3):
                top = y0 + dy * (min(nsteps, k + 3)) + 0.8
                m.span((s * width / 2 - (0.0 if s > 0 else 1.2), base, step_d * k),
                       (s * width / 2 + (1.2 if s > 0 else 0.0), top, step_d * min(nsteps, k + 3) + 0.01), side)
        if rail:
            rail(m, length, nsteps, dy, y0)
    return nsteps * step_d


def path_strip(m, pts, width, color, border, y_fn, thick=0.6):
    """Bordered path along a polyline [(x, z), ...]; y_fn(x, z) gives the ground height."""
    for (ax, az), (bx, bz) in zip(pts, pts[1:]):
        L = math.hypot(bx - ax, bz - az)
        n = max(1, int(L / 10))
        for k in range(n):
            t0, t1 = k / n, (k + 1) / n
            sx, sz = ax + (bx - ax) * t0, az + (bz - az) * t0
            ex, ez = ax + (bx - ax) * t1, az + (bz - az) * t1
            cx, cz = (sx + ex) / 2, (sz + ez) / 2
            y = y_fn(cx, cz)
            ry = math.degrees(math.atan2(bx - ax, bz - az))
            seg = L / n + 1.2
            with m.at((cx, y, cz), ry=ry):
                m.box((0, 0.15, 0), (width + 1.2, 0.5, seg + 0.6), border)
                m.box((0, 0.3, 0), (width, 0.6, seg), color)
    for (x, z) in pts[1:-1]:   # round joints
        y = y_fn(x, z)
        with m.at((x, y, z)):
            m.octagon(0.155, width / 2 + 0.6, 0.5, border)
            m.octagon(0.305, width / 2, 0.6, color)
