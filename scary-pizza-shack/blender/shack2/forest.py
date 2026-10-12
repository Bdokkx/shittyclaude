"""The forest and the horizon.

Plant models, each used at several sizes and turns: PineTall, PineMid, PineYoung (studded
tiers on real trunks with a root flare), Broadleaf, BareTree, DeadLean, Bush, Sapling, and
the floor: Fern, Tuft, Rock, Stump, FallenLog, Mushrooms.

Placement: a wall of forest three rows deep and more between 52 and 92 studs from the shack
on every side, undergrowth at its foot; inside the meadow wedge across the road (under the
moon) only a lower run of young trees far out; beyond 125 studs single dark tree meshes;
and a closed ring of big stepped hills from 215 to 330 that hides the edge of the world.
"""
import math

import numpy as np

import spsgeo as G
from spsgeo import CF, T

from . import layout as L
from . import terrain as TR
from .kit import bevel_box, ccyl, col, lathe

PINES = ("pine", "pine2", "pine3")


# ---------------------------------------------------------------- plant models (parts, stud style)

def _trunk(k, m, x, y, z, h, d, color="trunk", lean=None):
    R = np.eye(3) if lean is None else lean
    c = np.array((x, y, z)) + R @ np.array((0.0, h / 2, 0.0))       # a leaning trunk leans from its foot
    t = k.part(m, "Trunk", (h, d, d), CF(c, R @ G.rz(90)), color, shape="Cylinder", solid=True)
    return t


def _roots(k, m, x, y, z, d, rng, color="trunk2"):
    for a in rng.choice(8, 2, replace=False):
        yaw = 45.0 * a + rng.uniform(-10, 10)
        R = G.ry(yaw)
        off = R @ np.array((0, 0, -(d / 2 + 0.5)))
        k.wedge(m, "Root", (1, 1.2, 1), (x + off[0], y + 0.4, z + off[2]), R, color)


def pine(k, parent, x, y, z, h, rng, kind="PineTall", name="Pine"):
    """Studded tiers on a real trunk. h = overall height (12..46)."""
    m = k.sc.model(parent, name)
    tiers = {"PineTall": 6, "PineMid": 6, "PineYoung": 4}[kind]
    w0 = {"PineTall": 15, "PineMid": 13, "PineYoung": 8}[kind] * (0.8 + 0.25 * h / 40)
    d = 2.2 if h > 30 else (1.6 if h > 18 else 1.0)
    clear = h * (0.22 if kind != "PineYoung" else 0.16)          # bare trunk below the first tier
    _trunk(k, m, x, y - 0.4, z, h - 0.4, d)                      # up into the top tuft
    if h > 18:
        _roots(k, m, x, y, z, d, rng)
    span = h - clear - 1.6
    yaw0 = rng.uniform(0, 90)
    c0 = int(rng.integers(0, 3))
    for i in range(tiers):
        t = i / (tiers - 1)
        w = max(2.0, round(w0 * (1 - 0.82 * t) + rng.uniform(-0.6, 0.6)))
        th = 2.4 if w > 6 else 1.6
        yb = y + clear + span * t
        R = G.ry(yaw0 + (45.0 if i % 2 else 0.0) + rng.uniform(-8, 8))
        c = PINES[(c0 + i) % 3]
        k.boxr(m, "Needles", (w, th, w), (x, yb + th / 2, z), R, c, studs=True, shadow=True)
    k.boxr(m, "Top", (1, 1.6, 1), (x, y + h - 0.8, z), G.ry(yaw0), PINES[c0], studs=True)
    k.mark_used(kind, "outside")
    return m


def broadleaf(k, parent, x, y, z, h, rng, name="Broadleaf"):
    m = k.sc.model(parent, name)
    d = 1.8
    _trunk(k, m, x, y - 0.4, z, h * 0.55, d)
    _roots(k, m, x, y, z, d, rng)
    for a in (rng.uniform(0, 120), rng.uniform(150, 260)):
        R = G.ry(a) @ G.rx(-35)
        off = G.ry(a) @ np.array((0, 0, -2.2))
        k.boxr(m, "Branch", (1, 1.2, 5), (x + off[0], y + h * 0.42, z + off[2]), R, "trunk2")
    for j in range(6):
        a = rng.uniform(0, math.tau)
        r = rng.uniform(1.0, 4.0) if j else 0.0
        w = round(rng.uniform(6, 10))
        hh = round(rng.uniform(3, 5) / 0.4) * 0.4
        cy = y + h * 0.62 + rng.uniform(-1.0, 2.6) + (2.0 if j == 0 else 0.0)
        k.boxr(m, "Leaves", (w, hh, w), (x + r * math.cos(a), cy, z + r * math.sin(a)), G.ry(rng.uniform(0, 90)),
               ("leaf", "leaf2", "pine3")[j % 3], studs=True)
    k.mark_used("Broadleaf", "outside")
    return m


def bare_tree(k, parent, x, y, z, h, rng, name="BareTree"):
    m = k.sc.model(parent, name)
    _trunk(k, m, x, y - 0.4, z, h * 0.8, 1.6, "bark_grey")
    _roots(k, m, x, y, z, 1.6, rng, "bark_grey")
    for j in range(6):
        a = rng.uniform(0, 360)
        tilt = rng.uniform(25, 55)
        ln = round(rng.uniform(3, 7))
        yy = y + h * (0.4 + 0.45 * j / 6)
        R = G.ry(a) @ G.rx(-tilt)
        off = R @ np.array((0, 0, -ln / 2))
        k.boxr(m, "Branch", (1, 1.2, ln), (x + off[0], yy + off[1], z + off[2]), R, "bark_grey")
    k.mark_used("BareTree", "outside")
    return m


def dead_lean(k, parent, x, y, z, h, rng, name="DeadLean"):
    m = k.sc.model(parent, name)
    lean = G.ry(rng.uniform(0, 360)) @ G.rx(rng.uniform(9, 16))
    t = _trunk(k, m, x, y - 0.6, z, h, 1.8, "deadwood", lean=lean)
    top = np.array((x, y - 0.6, z)) + lean @ np.array((0, h, 0))
    for j in range(3):
        yy = 0.35 + 0.18 * j
        p = np.array((x, y - 0.6, z)) + lean @ np.array((0, h * yy, 0))
        R = lean @ G.ry(120 * j + 20) @ G.rx(-70)
        off = R @ np.array((0, 0, -1.5))
        k.boxr(m, "Snag", (1, 1.2, 3), p + off, R, "deadwood")
    k.boxr(m, "BrokenTop", (1, 1.6, 1), top + lean @ np.array((0.3, 0.4, 0)), lean @ G.rz(25), "deadwood")
    k.mark_used("DeadLean", "outside")
    return m


def bush(k, parent, x, y, z, s, rng, name="Bush"):
    m = k.sc.model(parent, name)
    for j in range(3 + int(rng.integers(0, 2))):
        a = rng.uniform(0, math.tau)
        r = rng.uniform(0.4, 1.4) * s
        w = max(1, round(s * rng.uniform(1.6, 2.6)))
        hh = max(0.8, round(s * rng.uniform(1.2, 2.0) / 0.4) * 0.4)
        k.boxr(m, "Leaves", (w, hh, w), (x + r * math.cos(a), y + hh / 2 - 0.2, z + r * math.sin(a)),
               G.ry(rng.uniform(0, 90)), ("leaf", "pine3", "leaf2", "grass2")[j % 4], studs=True,
               shadow=(s > 1.2))
    k.mark_used("Bush", "outside")
    return m


def sapling(k, parent, x, y, z, rng, name="Sapling"):
    m = k.sc.model(parent, name)
    h = 0.4 * round(rng.uniform(10, 17))
    k.box(m, "Stem", (x - 0.5, y - 0.4, z - 0.5), (x + 0.5, y + h, z + 0.5), "trunk2")
    for j, w in enumerate((4, 3, 2)):
        yy = y + h - 3.2 + 1.2 * j
        k.boxr(m, "Needles", (w, 1.2, w), (x, yy, z), G.ry(rng.uniform(0, 90)), PINES[j % 3], studs=True,
               shadow=False)
    k.mark_used("Sapling", "outside")
    return m


# ---------------------------------------------------------------- floor props (meshes)

_MESHES = {}


def _mesh_once(k, key, fn):
    if key not in _MESHES:
        _MESHES[key] = fn()
    return _MESHES[key]


def fern_geo():
    g = G.Geo()
    for j in range(6):
        a = math.tau * j / 6 + 0.3
        pts = [(0, 0, 0), (0.55, 0.9, 0.0), (1.2, 1.15, 0.0), (1.7, 0.85, 0.0)]
        frond = G.tube([(p[0] * math.cos(a), p[1], p[0] * math.sin(a)) for p in pts], 0.12, 4)
        for t in (0.35, 0.6, 0.85):
            px, py = 1.7 * t, 1.1 * math.sin(math.pi * t) + 0.1
            for s in (-1, 1):
                b = a + s * 0.5
                frond.add(G.tube([(px * math.cos(a), py, px * math.sin(a)),
                                  (px * math.cos(a) + 0.45 * math.cos(b), py - 0.15, px * math.sin(a) + 0.45 * math.sin(b))],
                                 0.08, 4))
        g.add(frond)
    return g


def tuft_geo(seed):
    rng = np.random.default_rng(seed)
    g = G.Geo()
    for j in range(7):
        a = rng.uniform(0, math.tau)
        r = rng.uniform(0, 0.35)
        h = rng.uniform(0.6, 1.2)
        lean = rng.uniform(0.1, 0.4)
        base = (r * math.cos(a), 0, r * math.sin(a))
        tip = (base[0] + lean * math.cos(a), h, base[2] + lean * math.sin(a))
        g.add(G.frustum(0.09, 0.0, h, 4, "y", (0, 0, 0)).xf(_aim(base, tip)))
    return g


def _aim(base, tip):
    """4x4 placing a +Y-up shape (centred) between base and tip."""
    b, t = np.asarray(base, float), np.asarray(tip, float)
    d = t - b
    L_ = np.linalg.norm(d)
    y = d / L_
    x = np.cross(y, (0, 0, 1.0))
    if np.linalg.norm(x) < 1e-6:
        x = np.array((1.0, 0, 0))
    x /= np.linalg.norm(x)
    z = np.cross(x, y)
    m = np.eye(4)
    m[:3, :3] = np.column_stack((x, y, z))
    m[:3, 3] = (b + t) / 2
    return m


def rock_geo(seed, s=1.0):
    rng = np.random.default_rng(seed)
    g = G.blob(1.0 * s, 7, 4, scale=(1.3, 0.7, 1.0), jitter=0.22, seed=seed, flat_bottom=-0.25 * s)
    return g


def stump_geo():
    g = ccyl(0.9, 1.4, 8, c=(0, 0.6, 0), b=0.15)
    for a in range(3):
        yaw = 120 * a + 15
        g.add(bevel_box(0.5, 0.6, 1.2, 0.12, c=(0, 0.2, -0.9)).xf(G.RY(yaw)))
    return g


def log_geo():
    g = ccyl(0.7, 9.0, 8, "x", (0, 0.65, 0), b=0.15)
    g.add(ccyl(0.25, 1.4, 6, "y", (2.0, 1.4, 0.2)).xf(np.eye(4)))
    g.add(ccyl(0.22, 1.2, 6, "z", (-2.6, 0.9, 0.7)))
    return g


def mushroom_geo():
    g = G.Geo()
    for (x, z, s) in ((0, 0, 1.0), (0.35, 0.2, 0.7), (-0.25, 0.3, 0.55)):
        g.add(ccyl(0.08 * s + 0.05, 0.35 * s, 6, c=(x, 0.17 * s, z), b=0.02))
        g.add(lathe([(0, 0.3 * s), (0.28 * s, 0.3 * s), (0.22 * s, 0.45 * s), (0, 0.5 * s)], 8).xf(T(x, 0, z)))
    return g


def floor_prop(k, parent, kind, x, y, z, rng, yaw=None):
    yaw = rng.uniform(0, 360) if yaw is None else yaw
    cf = CF((x, y, z), G.ry(yaw))
    if kind == "Fern":
        g = _mesh_once(k, "Fern", fern_geo)
        k.mesh(parent, "Fern", "Fern__Fronds", g, cf, "leaf", shadow=False)
    elif kind == "Tuft":
        v = int(rng.integers(0, 3))
        g = _mesh_once(k, "Tuft%d" % v, lambda: tuft_geo(v + 3))
        k.mesh(parent, "Tuft", "Tuft%d__Blades" % v, g, cf, ("grass3", "grass_dry", "leaf2")[v], shadow=False)
    elif kind == "Rock":
        v = int(rng.integers(0, 4))
        g = _mesh_once(k, "Rock%d" % v, lambda: rock_geo(40 + v, (0.8, 1.2, 1.7, 2.4)[v]))
        k.mesh(parent, "Rock", "Rock%d__Stone" % v, g, cf, ("rock", "rock_dark")[v % 2], solid=v >= 2)
    elif kind == "Stump":
        g = _mesh_once(k, "Stump", stump_geo)
        k.mesh(parent, "Stump", "Stump__Wood", g, cf, "trunk2", solid=True)
        k.mesh(parent, "StumpTop", "Stump__Rings", ccyl(0.75, 0.16, 8, c=(0, 0, 0), b=0.03),
               cf * CF((0, 1.38, 0)), "wood_pale", shadow=False)
    elif kind == "FallenLog":
        g = _mesh_once(k, "Log", log_geo)
        k.mesh(parent, "FallenLog", "FallenLog__Wood", g, cf, "trunk", solid=True)
        k.mesh(parent, "Moss", "FallenLog__Moss", _mesh_once(k, "LogMoss", lambda: G.Geo().add(
            [bevel_box(2.4, 0.3, 1.2, 0.1, c=(-1.0, 1.32, 0)), bevel_box(1.6, 0.3, 1.0, 0.1, c=(2.8, 1.3, -0.1))])),
               cf, "moss", shadow=False)
    elif kind == "Mushrooms":
        g = _mesh_once(k, "Mushrooms", mushroom_geo)
        k.mesh(parent, "Mushrooms", "Mushrooms__Caps", g, cf, (196, 120, 80), shadow=False)
    k.mark_used(kind, "outside")


# ---------------------------------------------------------------- far trees (single dark meshes)

def far_tree_geo(h, w, tiers, seed):
    rng = np.random.default_rng(seed)
    g = G.Geo()
    g.add(G.box(1.6, h * 0.3, 1.6, (0, h * 0.15, 0)))
    for i in range(tiers):
        t = i / (tiers - 1)
        ww = max(2.0, w * (1 - 0.8 * t))
        yb = h * 0.22 + (h * 0.75) * t
        g.add(G.box(ww, 2.4, ww, (0, yb + 1.2, 0)).xf(G.RY(45.0 * (i % 2) + rng.uniform(-6, 6))))
    return g


FAR_KINDS = [(30.0, 13.0, 6, 1), (38.0, 15.0, 7, 2), (24.0, 11.0, 5, 3), (44.0, 16.0, 7, 4)]


# ---------------------------------------------------------------- hills (closing the horizon)

def hill_geo(rng, r, h, steps):
    """A stepped hill: stacked irregular slabs, each smaller than the one below."""
    g = G.Geo()
    pts0 = []
    n = 9
    for j in range(n):
        a = math.tau * j / n + rng.uniform(-0.15, 0.15)
        pts0.append((math.cos(a) * r * rng.uniform(0.8, 1.15), math.sin(a) * r * rng.uniform(0.8, 1.15)))
    for s in range(steps):
        f = 1.0 - 0.8 * s / steps
        pts = [(x * f, z * f) for x, z in pts0]
        y0 = -4.0 if s == 0 else h * s / steps
        y1 = h * (s + 1) / steps
        g.add(G.slab_poly(pts, y1 - y0, (0, y0, 0)))
    return g


# ---------------------------------------------------------------- placement

def _discs():
    """Things standing in the forest's edge that trees must keep their crowns off: the
    billboard, the roadside signs, the telegraph poles, the road lamps (x, z, radius)."""
    d = [(L.BILLBOARD["x"], L.BILLBOARD["z"], 21.0)]
    for s in L.ROAD_SIGNS.values():
        d.append((s["x"], s["z"], 11.0))
    for x in L.POLE_X:
        d.append((x, L.POLE_Z, 10.0))
    d += [(-46.0, 20.0, 9.0), (68.0, 17.0, 9.0), (L.CULVERT_X + 4.2, 58.5, 6.0), (10.0, -47.5, 10.0)]
    return d


DISCS = None


def keep_out(x, z):
    """Where trees may not stand."""
    global DISCS
    if DISCS is None:
        DISCS = _discs()
    if any((x - a) ** 2 + (z - b) ** 2 < r * r for (a, b, r) in DISCS):
        return True
    if abs(x) < 34 and -14 < z < 25:                 # shack, forecourt
        return True
    if L.YARD_X[0] - 4 < x < L.YARD_X[1] + 4 and L.YARD_Z[0] - 5 < z < L.YARD_Z[1]:
        return True
    if L.LOT[0] - 2 < x < L.LOT[1] + 4 and L.LOT[2] - 4 < z < L.LOT[3] + 2:
        return True
    if L.BUS_STOP_X[0] - 6 < x < L.BUS_STOP_X[1] + 6 and 8 < z < 24:
        return True
    if -68 < x < -44 and 54 < z < 72:                 # billboard
        return True
    if L.CULVERT_X - 5 < x < L.CULVERT_X + 5 and 40 < z < 140:   # the farm track into the meadow
        return True
    if 8 < x < 12 and -110 < z < -45:                  # the dirt path from the yard gate
        return True
    return False


def poisson(rng, n_try, rmin, rmax, spacing, accept, existing=()):
    pts = list(existing)
    out = []
    for _ in range(n_try):
        a = rng.uniform(0, math.tau)
        r = math.sqrt(rng.uniform(rmin ** 2, rmax ** 2))
        x, z = r * math.sin(a), r * math.cos(a)
        if not accept(x, z):
            continue
        sp = spacing(x, z)
        if any((x - px) ** 2 + (z - pz) ** 2 < sp * sp for px, pz in pts[-400:]) or \
                any((x - px) ** 2 + (z - pz) ** 2 < sp * sp for px, pz in pts):
            continue
        pts.append((x, z))
        out.append((x, z))
    return out


def ground_y(x, z):
    """Top of the natural ground under a point (approximately: the cell's height)."""
    if max(abs(x), abs(z)) >= L.GROUND_R:
        return 0.0
    X0, Z0 = math.floor(x / 16) * 16, math.floor(z / 16) * 16
    cs = 8 if max(abs(X0 + 8), abs(Z0 + 8)) < 104 else 16
    x0, z0 = math.floor(x / cs) * cs, math.floor(z / cs) * cs
    return TR.cell_height(x0, z0, cs)


def build(k, out, rng):
    sc = k.sc
    f = sc.folder(out, "Forest")
    near = sc.folder(f, "Trees")
    under = sc.folder(f, "Undergrowth")
    far = sc.folder(f, "FarTrees")
    hills = sc.folder(f, "Hills")
    road_d = lambda x, z: L.dist_to_road(x, z)

    def ok_tree(x, z):
        return not keep_out(x, z) and road_d(x, z) > 17.0 and not L.in_meadow(x, z)

    # the wall: dense, trunks overlapping, bigger trees further back
    pts = poisson(rng, 9000, L.FOREST_R[0], L.FOREST_R[1] + 8, lambda x, z: 6.4, ok_tree)
    trees = []
    for (x, z) in pts:
        r = math.hypot(x, z)
        y = ground_y(x, z)
        u = rng.random()
        if u < 0.08:
            m = dead_lean(k, near, x, y, z, float(rng.uniform(16, 26)), rng)
        elif u < 0.15:
            m = bare_tree(k, near, x, y, z, float(rng.uniform(20, 30)), rng)
        elif u < 0.24:
            m = broadleaf(k, near, x, y, z, float(rng.uniform(20, 28)), rng)
        else:
            h = float(rng.uniform(28, 45)) if r > 62 else float(rng.uniform(22, 34))
            kind = "PineTall" if h > 35 else ("PineMid" if h > 26 else "PineYoung")
            m = pine(k, near, x, y, z, h, rng, kind)
        trees.append((x, z))
    # the lower run inside the meadow wedge, far out under the moon
    def ok_low(x, z):
        return L.in_meadow(x, z) and not keep_out(x, z) and road_d(x, z) > 20
    for (x, z) in poisson(rng, 2500, 118, 175, lambda x, z: 9.0, ok_low):
        y = ground_y(x, z)
        if rng.random() < 0.7:
            pine(k, near, x, y, z, float(rng.uniform(11, 18)), rng, "PineYoung")
        else:
            bush(k, near, x, y, z, float(rng.uniform(1.4, 2.4)), rng)
    # undergrowth at the forest's foot and through it
    def ok_under(x, z):
        return not keep_out(x, z) and road_d(x, z) > 18.5
    for (x, z) in poisson(rng, 6000, 46, 96, lambda x, z: 4.5, ok_under, existing=trees):
        y = ground_y(x, z)
        u = rng.random()
        if L.in_meadow(x, z):
            floor_prop(k, under, "Tuft" if u < 0.8 else "Rock", x, y, z, rng)
        elif u < 0.3:
            bush(k, under, x, y, z, float(rng.uniform(1.0, 2.0)), rng)
        elif u < 0.45:
            sapling(k, under, x, y, z, rng)
        elif u < 0.65:
            floor_prop(k, under, "Fern", x, y, z, rng)
        elif u < 0.8:
            floor_prop(k, under, "Tuft", x, y, z, rng)
        elif u < 0.88:
            floor_prop(k, under, "Rock", x, y, z, rng)
        elif u < 0.93:
            floor_prop(k, under, "Stump", x, y, z, rng)
        elif u < 0.96:
            floor_prop(k, under, "FallenLog", x, y, z, rng)
        else:
            floor_prop(k, under, "Mushrooms", x, y, z, rng)
    # meadow cover: tufts and a few rocks
    for (x, z) in poisson(rng, 3000, 60, 150, lambda x, z: 5.0, lambda x, z: L.in_meadow(x, z) and road_d(x, z) > 24
                          and not keep_out(x, z)):
        floor_prop(k, under, "Tuft" if rng.random() < 0.85 else "Rock", x, ground_y(x, z), z, rng)
    # far trees: one mesh each, dark, no shadows
    geos = [far_tree_geo(h, w, t, s) for (h, w, t, s) in FAR_KINDS]
    def ok_far(x, z):
        if any(math.hypot(x - px, z - L.POLE_Z) < 16.0 for px in L.POLE_X):     # wide crowns: keep off the poles
            return False
        return not keep_out(x, z) and road_d(x, z) > 16.0 and not (L.in_meadow(x, z) and math.hypot(x, z) < 180)
    for (x, z) in poisson(rng, 7000, L.FOREST_R[1] + 8, L.FAR_R[1], lambda x, z: 10.0, ok_far, existing=trees):
        j = int(rng.integers(0, len(geos)))
        y = ground_y(x, z) if max(abs(x), abs(z)) < L.FAR_R[0] + 20 else 0.0
        k.mesh(far, "FarTree", "FarTree%d__Mass" % j, geos[j], CF((x, y - 0.4, z), G.ry(rng.uniform(0, 90))),
               ("far_trees", "pine_dark", "pine2")[j % 3], shadow=False)
    k.mark_used("FarTree", "outside")
    # the far ground under them, and the ring of hills closing the horizon
    R0 = L.GROUND_R
    W = L.WORLD[1]
    for (x0, x1, z0, z1) in ((-W, W, -W, -R0), (-W, W, R0, W), (-W, -R0, -R0, R0), (R0, W, -R0, R0)):
        k.box(far, "FarGround", (x0, -4.0, z0), (x1, 0.0, z1), "moss", studs=True, solid=True, shadow=False)
    n = 26
    for j in range(n):
        a = math.tau * j / n + rng.uniform(-0.05, 0.05)
        r = rng.uniform(*L.HILLS_R)
        az_deg = math.degrees(math.atan2(math.sin(a), math.cos(a)))
        h = rng.uniform(34, 70)
        if L.MEADOW["az0"] < az_deg < L.MEADOW["az1"]:
            h *= 0.75                     # a lower ridge under the moon, with the mast on it
        g = hill_geo(rng, rng.uniform(58, 86), h, int(rng.integers(3, 6)))
        x, z = r * math.sin(a), r * math.cos(a)
        k.mesh(hills, "Hill", "Hill%d__Terraces" % j, g, CF((x, 0, z)), ("hill", "hill2", "hill3")[j % 3],
               shadow=False, solid=False)
        # tree masses on the hill's shoulders
        for q in range(5):
            b = rng.uniform(0, math.tau)
            rr = rng.uniform(0, 30)
            jj = int(rng.integers(0, len(geos)))
            tx, tz = x + rr * math.cos(b), z + rr * math.sin(b)
            if min(math.hypot(tx - L.MAST[0], tz - L.MAST[1]), math.hypot(tx - L.HILL_WINDOW[0],
                                                                           tz - L.HILL_WINDOW[1])) < 22.0:
                continue                          # the mast and the lit house stand clear
            k.mesh(hills, "HillTree", "FarTree%d__Mass" % jj, geos[jj],
                   CF((x + rr * math.cos(b), h * 0.55, z + rr * math.sin(b))), "far_trees", shadow=False)
    k.mark_used("Hill", "outside")
    return trees
