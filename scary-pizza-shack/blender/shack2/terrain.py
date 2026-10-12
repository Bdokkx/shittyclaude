"""The ground: stepped stud terrain (never one sheet), the road on a low embankment with its
two bends, gravel shoulders, the ditch with a culvert, and the paved areas round the shack.

Heights are whole plates (0.4). Near the shack the ground is a mosaic of 8 x 8 cells in
three close greens, moss, leaf litter and dirt, each cell at its own height; further out the
cells grow to 16, and beyond the forest the hills (forest.py) take over. Along the straight
in front of the shack a corridor is built exactly: forecourt edge, road, shoulders, the
south bank, the ditch with its water and culvert, the far bank and the meadow's edge."""
import math

import numpy as np

import spsgeo as G
from spsgeo import CF

from . import layout as L

PLATE = 0.4


# ---------------------------------------------------------------- smooth noise

def _hash(ix, iz, seed):
    h = (ix * 374761393 + iz * 668265263 + seed * 2147483647) & 0xFFFFFFFF
    h = (h ^ (h >> 13)) * 1274126177 & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


def vnoise(x, z, scale, seed=1):
    gx, gz = x / scale, z / scale
    ix, iz = math.floor(gx), math.floor(gz)
    fx, fz = gx - ix, gz - iz
    sx, sz = fx * fx * (3 - 2 * fx), fz * fz * (3 - 2 * fz)
    a = _hash(ix, iz, seed)
    b = _hash(ix + 1, iz, seed)
    c = _hash(ix, iz + 1, seed)
    d = _hash(ix + 1, iz + 1, seed)
    return (a * (1 - sx) + b * sx) * (1 - sz) + (c * (1 - sx) + d * sx) * sz


def fbm(x, z, seed=1):
    return 0.6 * vnoise(x, z, 37.0, seed) + 0.3 * vnoise(x, z, 13.0, seed + 7) + 0.1 * vnoise(x, z, 5.0, seed + 11)


# ---------------------------------------------------------------- what is where

def in_corridor(x0, z0, x1, z1):
    cx0, cx1, cz0, cz1 = L.CORRIDOR
    return x0 < cx1 and x1 > cx0 and z0 < cz1 and z1 > cz0


def built_rects():
    """The paved / built areas the natural ground stops at (X0, X1, Z0, Z1)."""
    return [(L.OUT_X0, L.OUT_X1, L.OUT_Z0, L.OUT_Z1), L.FORECOURT, L.LOT,
            (L.YARD_X[0], L.YARD_X[1], L.YARD_Z[0], L.YARD_Z[1])]


def built(x0, z0, x1, z1):
    """True if the rectangle is wholly covered by the shack, the forecourt, the lot or the yard."""
    def inside(r):
        a0, a1, b0, b1 = r
        return x0 >= a0 and x1 <= a1 and z0 >= b0 and z1 <= b1
    return any(inside(r) for r in built_rects())


def subtract(rect, holes):
    """A rectangle (X0, X1, Z0, Z1) minus rectangles: the rectangles that are left."""
    out = [rect]
    for (a0, a1, b0, b1) in holes:
        nxt = []
        for (x0, x1, z0, z1) in out:
            if a0 >= x1 or a1 <= x0 or b0 >= z1 or b1 <= z0:
                nxt.append((x0, x1, z0, z1))
                continue
            if z0 < b0:
                nxt.append((x0, x1, z0, b0))
            if b1 < z1:
                nxt.append((x0, x1, b1, z1))
            zz0, zz1 = max(z0, b0), min(z1, b1)
            if x0 < a0:
                nxt.append((x0, a0, zz0, zz1))
            if a1 < x1:
                nxt.append((a1, x1, zz0, zz1))
        out = nxt
    return out


def base_height(x, z):
    r = math.hypot(x, z)
    if r < 44:
        return 0.0
    rise = max(0.0, r - 44) * (0.020 if z < 0 else 0.011)
    h = rise + 1.6 * (fbm(x, z, 3) - 0.5)
    if L.in_meadow(x, z):
        h = min(h, 0.6 * (fbm(x, z, 9) - 0.55))
    return h


def cell_height(x0, z0, cs):
    """Height of a ground cell (whole plates), kept below the road's shoulders near the road."""
    cx, cz = x0 + cs / 2, z0 + cs / 2
    h = base_height(cx, cz)
    d_c = L.dist_to_road(cx, cz)
    d_min = max(0.0, d_c - cs * 0.71)
    if d_min < 13.5:
        h = min(h, -0.8)
    elif d_min < 28:
        h = min(h, -0.4 + 0.08 * (d_min - 13.5))
    return round(h / PLATE) * PLATE


def ground_colour(x, z):
    r = math.hypot(x, z)
    n = fbm(x * 1.7 + 300, z * 1.7 - 200, 5)
    n2 = _hash(int(x // 8), int(z // 8), 77)
    if L.in_meadow(x, z):
        return ("grass", "grass3", "grass_dry", "grass", "grass2")[min(4, int((0.6 * n + 0.4 * n2) * 5))]
    if r < 48:
        return ("grass", "grass2", "grass3", "grass", "dirt")[min(4, int((0.6 * n + 0.4 * n2) * 5))]
    return ("moss", "litter", "grass2", "moss", "litter", "grass")[min(5, int((0.5 * n + 0.5 * n2) * 6))]


# ---------------------------------------------------------------- the natural ground

def ground(k, f):
    R = L.GROUND_R
    cells = {}
    # 16-stud cells filling the square +-R exactly (the far ground frame starts at R), split
    # into four 8-stud cells near the shack: no overlaps, no holes
    n = int(R / 16)
    for ix in range(-n, n):
        for iz in range(-n, n):
            X0, Z0 = ix * 16, iz * 16
            rr = max(abs(X0 + 8), abs(Z0 + 8))
            subs = [(X0, Z0, 16)] if rr >= 104 else [(X0 + a, Z0 + b, 8) for a in (0, 8) for b in (0, 8)]
            for (x0, z0, cs) in subs:
                if in_corridor(x0, z0, x0 + cs, z0 + cs) or built(x0, z0, x0 + cs, z0 + cs):
                    continue
                cells[(x0, z0, cs)] = (cell_height(x0, z0, cs), ground_colour(x0 + cs / 2, z0 + cs / 2))
    done, count = set(), 0
    holes = built_rects()
    for (x0, z0, cs), (h, c) in sorted(cells.items()):
        if (x0, z0, cs) in done:
            continue
        pieces = subtract((x0, x0 + cs, z0, z0 + cs), holes)
        if pieces != [(x0, x0 + cs, z0, z0 + cs)]:       # a cell cut by a paved area: no merging
            done.add((x0, z0, cs))
            for (a0, a1, b0, b1) in pieces:
                k.box(f, "Ground", (a0, -2.8, b0), (a1, h, b1), c, studs=True, solid=True)
                count += 1
            continue
        x1 = x0 + cs
        while (x1, z0, cs) in cells and cells[(x1, z0, cs)] == (h, c) and x1 - x0 < 32 and \
                subtract((x1, x1 + cs, z0, z0 + cs), holes) == [(x1, x1 + cs, z0, z0 + cs)]:
            done.add((x1, z0, cs))
            x1 += cs
        done.add((x0, z0, cs))
        k.box(f, "Ground", (x0, -2.8, z0), (x1, h, z0 + cs), c, studs=True, solid=True)
        count += 1
    return count


# ---------------------------------------------------------------- the road

def _seg_frame(a, b):
    dx, dz = b[0] - a[0], b[1] - a[1]
    return (a[0] + b[0]) / 2, (a[1] + b[1]) / 2, math.hypot(dx, dz), math.degrees(math.atan2(-dz, dx))


def centre_line():
    pts = [(x, z) for (x, z, _) in L.road_path(4.0)]
    (we, wd, wl), (ee, ed, el) = L.road_ends()
    west = [(we[0] + wd[0] * t, we[1] + wd[1] * t) for t in np.arange(wl, 0.1, -4.0)]
    east = [(ee[0] + ed[0] * t, ee[1] + ed[1] * t) for t in np.arange(4.0, el + 0.1, 4.0)]
    return west + pts + east


def offset_line(pts, off):
    """The polyline moved sideways by `off`: + is to the right of the direction of travel
    (west -> east), which is south (+Z) on the straight."""
    out = []
    for i, (x, z) in enumerate(pts):
        a, b = pts[max(i - 1, 0)], pts[min(i + 1, len(pts) - 1)]
        dx, dz = b[0] - a[0], b[1] - a[1]
        n = math.hypot(dx, dz) or 1.0
        out.append((x - dz / n * off, z + dx / n * off))
    return out


def _normals(P):
    """Unit right-hand normals (+Z on the straight) at every point, averaged at the joints."""
    n = len(P)
    N = np.zeros((n, 2))
    for i in range(n):
        a, b = P[max(i - 1, 0)], P[min(i + 1, n - 1)]
        d = (b - a) / np.linalg.norm(b - a)
        N[i] = (-d[1], d[0])
    return N


def ribbon(k, f, name, pts, section, color, group=4, keep=None, solid=True, material="Plastic", **kw):
    """Sweep a cross-section along a polyline: `section` is a convex polygon of (offset, y)
    (offset + to the right of travel). Consecutive pieces share their end faces exactly (no
    overlaps, no gaps), each piece a MeshPart over `group` segments; pieces with the same
    shape (all of one bend) share one mesh."""
    P = np.asarray(pts, float)
    N = _normals(P)
    S = np.asarray(section, float)
    # wind the section counter-clockwise in (offset, y)
    if 0.5 * np.sum(S[:, 0] * np.roll(S[:, 1], -1) - np.roll(S[:, 0], -1) * S[:, 1]) < 0:
        S = S[::-1]
    m = len(S)
    out = []
    for i0 in range(0, len(P) - 1, group):
        i1 = min(i0 + group, len(P) - 1)
        mid = (P[i0] + P[i1]) / 2
        if keep is not None and not keep(mid[0], mid[1]):
            continue
        ch = P[i1] - P[i0]
        hd = math.atan2(ch[1], ch[0])
        c, s_ = math.cos(hd), math.sin(hd)
        V = []
        for i in range(i0, i1 + 1):
            for off, y in S:
                x = P[i, 0] + N[i, 0] * off - mid[0]
                z = P[i, 1] + N[i, 1] * off - mid[1]
                # into the piece's frame (local +X along the chord)
                V.append((round(x * c + z * s_, 4), y, round(-x * s_ + z * c, 4)))
        nsec = i1 - i0 + 1
        F = []
        for a in range(nsec - 1):
            for j in range(m):
                q = (a * m + j, a * m + (j + 1) % m, (a + 1) * m + (j + 1) % m, (a + 1) * m + j)
                F.append(q)
        F.append(tuple(range(m))[::-1])
        F.append(tuple((nsec - 1) * m + j for j in range(m)))
        g = G.Geo(V, F)
        # orient: side faces must point away from the sweep's axis
        v0, v1, v2 = (np.array(V[i]) for i in F[0][:3])
        nrm = np.cross(v1 - v0, v2 - v0)
        cen = np.array(V[F[0][0]]) * 0 + np.mean([V[i] for i in range(m)], 0)
        if np.dot(nrm, (v0 + v1) / 2 - cen) < 0:
            g.f = [t[::-1] for t in g.f]
        key = "%s_%08x" % (name, abs(hash(tuple(V))) % (1 << 32))
        frame = CF((mid[0], 0.0, mid[1]), G.ry(-math.degrees(hd)))
        out.append(k.mesh(f, name, "Road__" + key, g, frame, color, solid=solid, material=material, **kw))
    return out


def arclength_points(pts, s0, s1, step=1.0):
    """Points along the polyline between arclengths s0 and s1."""
    P = np.asarray(pts, float)
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
    cum = np.concatenate(([0.0], np.cumsum(seg)))
    out = []
    for s in np.arange(s0, s1 + 1e-6, step):
        i = min(np.searchsorted(cum, s, side="right") - 1, len(seg) - 1)
        t = (s - cum[i]) / seg[i]
        out.append(tuple(P[i] + (P[i + 1] - P[i]) * t))
    return out, cum[-1]


def road(k, f, rng):
    pts = centre_line()
    top = L.ROAD_TOP
    ribbon(k, f, "Asphalt", pts, [(-10, top - 1.2), (10, top - 1.2), (10, top), (-10, top)], "asphalt", group=4)
    # shoulders, a hair below the road, and the embankment's sides outside the corridor
    for sg in (-1, 1):
        sec = [(sg * 10, top - 1.2), (sg * 13, top - 1.2), (sg * 13, top - 0.04), (sg * 10, top - 0.04)]
        ribbon(k, f, "Shoulder", pts, sec, "gravel", group=4)

        def out_of_corridor(x, z):
            return not (L.CORRIDOR[0] < x < L.CORRIDOR[1] and L.CORRIDOR[2] - 4 < z < L.CORRIDOR[3])
        sec = [(sg * 13, -2.8), (sg * 17.5, -2.8), (sg * 17.5, -1.4), (sg * 13, top - 0.04)]
        ribbon(k, f, "Bank", pts, sec, "grass2", group=4, keep=out_of_corridor)
    # edge lines and the centre dashes, a hair proud of the road
    for off in (-9.0, 9.0):
        ribbon(k, f, "EdgeLine", pts, [(off - 0.5, top - 0.4), (off + 0.5, top - 0.4), (off + 0.5, top + 0.04),
                                        (off - 0.5, top + 0.04)], "line_white", group=4, solid=False, shadow=False)
    _, total = arclength_points(pts, 0, 0)
    s = 2.0
    while s < total - 6:
        if rng.random() > 0.12:
            seg, _ = arclength_points(pts, s, s + 4.0, 1.0)
            ribbon(k, f, "CentreLine", seg, [(-0.5, top - 0.4), (0.5, top - 0.4), (0.5, top + 0.04), (-0.5, top + 0.04)],
                   "line_yellow", group=8, solid=False, shadow=False)
        s += 9.0
    # patches of newer and older asphalt, each a different hair proud of the road (no two coplanar)
    s, j = 6.0, 0
    while s < total - 16:
        if rng.random() < 0.5:
            ln = float(rng.integers(4, 13))
            seg, _ = arclength_points(pts, s, s + ln, 2.0)
            lane = 1 if rng.random() < 0.5 else -1
            o0 = lane * float(rng.uniform(1.5, 5.5))
            w = float(rng.integers(2, 5))
            y1 = top + 0.012 + 0.004 * (j % 4)
            ribbon(k, f, "Patch", seg, [(o0 - w / 2, top - 0.4), (o0 + w / 2, top - 0.4), (o0 + w / 2, y1),
                                         (o0 - w / 2, y1)], ("asphalt_patch", "asphalt_new")[j % 2], group=8,
                   solid=False, shadow=False)
            j += 1
            s += ln + 4.0
        s += float(rng.integers(6, 14))
    return pts


# ---------------------------------------------------------------- the corridor in front of the shack

def corridor(k, f, rng):
    x0, x1, z0, z1 = L.CORRIDOR
    top = L.ROAD_TOP
    # north of the road, either side of the forecourt and the lot: grass at Y 0, then the bank
    for (a, b) in ((x0, L.FORECOURT[0]), (L.LOT[1], x1)):
        for x in np.arange(a, b, 4.0):
            c = ("grass", "grass2", "grass3")[int(rng.integers(0, 3))]
            k.box(f, "Verge", (x, -2.8, z0), (min(x + 4, b), 0.0, 21.0 - 3.0), c, studs=True, solid=True)
            k.wedge(f, "Bank", (int(min(x + 4, b) - x), 0.4, 3), ((x + min(x + 4, b)) / 2, 0.2, 19.5), np.eye(3),
                    "grass2", solid=True)
    # the forecourt and the lot meet the shoulder with a concrete lip
    k.wedge(f, "Apron", (int(L.LOT[1] - L.FORECOURT[0]), 0.4, 1), ((L.FORECOURT[0] + L.LOT[1]) / 2, 0.2, 20.5),
            np.eye(3), "concrete", solid=True)
    # south bank, ditch bed, far bank, meadow edge
    sb0, sb1 = L.SOUTH_BANK
    d0, d1 = L.DITCH
    fb0, fb1 = L.FAR_BANK
    for x in np.arange(x0, x1, 8.0):
        xb = min(x + 8, x1)
        k.wedge(f, "Bank", (int(xb - x), 2.4, 3), ((x + xb) / 2, -0.84, (sb0 + sb1) / 2), G.ry(180), "grass2",
                solid=True)
        k.box(f, "DitchBed", (x, -3.2, d0), (xb, L.DITCH_BOTTOM, d1), ("mud", "dirt")[int(rng.integers(0, 2))],
              solid=True)
        k.wedge(f, "FarBank", (int(xb - x), 2.0, 3), ((x + xb) / 2, -1.0, (fb0 + fb1) / 2), np.eye(3),
                ("grass2", "grass")[int(rng.integers(0, 2))], solid=True)
        for z in np.arange(fb1, z1, 6.0):
            k.box(f, "Meadow", (x, -2.8, z), (xb, 0.0, min(z + 6, z1)),
                  ("grass", "grass3", "grass_dry")[int(rng.integers(0, 3))], studs=True, solid=True)
    # standing water in the ditch: dark glossy plates in long puddles
    x = x0 + 2
    while x < x1 - 6:
        ln = int(rng.integers(5, 14))
        if rng.random() < 0.65 and not (x <= L.CULVERT_X + 3 and x + ln >= L.CULVERT_X - 3):
            k.box(f, "Water", (x, L.DITCH_BOTTOM - 0.38, d0 + 1), (x + ln, L.DITCH_BOTTOM + 0.02, d1 - 1), "water",
                  material="SmoothPlastic", reflectance=0.18, shadow=False)
        x += ln + int(rng.integers(2, 7))
    culvert(k, k.sc.model(f, "Culvert"))


def culvert(k, m):
    """A farm track crosses the ditch on an earth causeway with a concrete pipe through it."""
    cx = L.CULVERT_X
    d0, d1 = L.DITCH
    sb0 = L.SOUTH_BANK[0]
    fb1 = L.FAR_BANK[1]
    # the causeway: dirt, level with the shoulder at the road end, the meadow at the other
    k.box(m, "Track", (cx - 3, -2.8, sb0), (cx + 3, 0.0, fb1), "dirt", studs=True, solid=True)
    k.wedge(m, "TrackRamp", (6, 0.4, 2), (cx, 0.2, sb0 + 1.0), G.ry(180), "dirt", solid=True)
    # concrete headwalls on both faces of the causeway, the pipe mouth in each
    for xf, sgn in ((cx - 3, -1), (cx + 3, 1)):
        k.box(m, "Headwall", (xf - (1 if sgn < 0 else 0), -2.4, d0 - 0.5), (xf + (0 if sgn < 0 else 1), -0.4, d1 + 0.5),
              "concrete_dark", solid=True)
        k.cyl(m, "PipeMouth", 1.2, 2.2, (xf + sgn * 0.3, -1.3, (d0 + d1) / 2), (1, 0, 0), "concrete")
        k.cyl(m, "PipeDark", 0.4, 1.6, (xf + sgn * 0.8, -1.3, (d0 + d1) / 2), (1, 0, 0), "black", shadow=False)


# ---------------------------------------------------------------- paved areas

def forecourt(k, f, rng):
    x0, x1, z0, z1 = L.FORECOURT
    shades = ("concrete", "concrete2", "concrete_dark", "concrete")
    for x in np.arange(x0, x1, 4.0):
        for z in np.arange(z0, z1, 4.0):
            k.box(f, "Slab", (x, -0.8, z), (min(x + 4, x1), 0.0, min(z + 4, z1)), shades[int(rng.integers(0, 4))],
                  solid=True)


def lot(k, f, rng):
    x0, x1, z0, z1 = L.LOT
    for x in np.arange(x0, x1, 6.0):
        for z in np.arange(z0, z1, 6.0):
            k.box(f, "LotAsphalt", (x, -0.8, z), (min(x + 6, x1), 0.0, min(z + 6, z1)),
                  ("asphalt", "asphalt_patch")[int(rng.integers(0, 2))], solid=True)


YARD_DRIVE = (4.0, 16.0)          # X of the gravel drive from the gate up to the apron
YARD_APRON = 8.0                   # depth of the gravel apron along the back of the shack


def yard_ground(k, f, rng):
    """The yard in 4 x 4 plates: a studded gravel apron along the back of the shack and a
    gravel drive from the gate up to it; beaten dirt round the rest, darker mud where the
    water sits, dry leaf litter blown against the fences."""
    x0, x1 = L.YARD_X
    z0, z1 = L.YARD_Z
    rng = np.random.default_rng(77)                 # its own stream: the forest's stays as it was
    for x in np.arange(x0, x1, 4.0):
        for z in np.arange(z0, z1, 4.0):
            cx, cz = x + 2.0, z + 2.0
            n = fbm(x * 2.0, z * 2.0, 21)
            hard = cz > z1 - YARD_APRON or YARD_DRIVE[0] < cx < YARD_DRIVE[1]
            edge = min(cx - x0, x1 - cx, cz - z0) < 4.0
            if hard:
                c = ("gravel", "gravel2")[int(rng.integers(0, 2))]
            elif edge and n > 0.42:
                c = "litter"
            elif n < 0.4:
                c = "mud"
            else:
                c = "dirt"
            k.box(f, "YardGround", (x, -0.8, z), (min(x + 4, x1), 0.0, min(z + 4, z1)), c, solid=True,
                  studs=c.startswith("gravel"))


def build(k, out, rng):
    n = ground(k, k.sc.folder(out, "Ground"))
    rf = k.sc.folder(out, "Road")
    road(k, rf, rng)
    corridor(k, k.sc.folder(out, "RoadSide"), rng)
    forecourt(k, k.sc.folder(out, "Forecourt"), rng)
    lot(k, k.sc.folder(out, "Lot"), rng)
    yard_ground(k, k.sc.folder(out, "YardGround"), rng)
    return n
