"""Shared pieces for the outside: the height of the built ground under a point, sagging
wires, chain-link, corrugated sheet, and a few shapes several stations use."""
import math

import numpy as np

import spsgeo as G
from spsgeo import CF

from . import layout as L
from .kit import bevel_box, ccyl, rod

GROUND_NAMES = {"Ground", "Slab", "LotAsphalt", "YardGround", "Shoulder", "Asphalt", "Bank", "Verge", "Meadow",
                "DitchBed", "FarBank", "Apron", "Patch", "EdgeLine", "CentreLine", "Paver", "Path", "Kerb", "Walk",
                "Gravel", "Pad"}


class Ground:
    """Top of the ground-like parts (terrain, road, slabs) straight under a point."""

    def __init__(self, sc):
        import spslib
        self._ray = spslib._ray_down
        self.items = []
        for n in sc.nodes(("Part", "MeshPart")):
            if n.name not in GROUND_NAMES or n.top() != "Outside":
                continue
            p = n.p
            if n.kind == "Part":
                half = np.abs(p["cf"].R) @ (np.asarray(p["size"], float) / 2)
                self.items.append((p["cf"].p - half, p["cf"].p + half, n, None))
            else:
                g = sc.geoms[p["mesh"]]
                V = (p["cf"].R @ np.asarray(g.v, float).T).T + p["cf"].p
                self.items.append((V.min(0), V.max(0), n, (V, g.f)))
        self.lo = np.array([a for a, _, _, _ in self.items])
        self.hi = np.array([b for _, b, _, _ in self.items])

    def y(self, x, z, default=0.0):
        hit = np.where((self.lo[:, 0] <= x + 1e-6) & (self.hi[:, 0] >= x - 1e-6) &
                       (self.lo[:, 2] <= z + 1e-6) & (self.hi[:, 2] >= z - 1e-6))[0]
        best = None
        for i in hit:
            lo, hi, n, mesh = self.items[i]
            if mesh is None:
                top = self._box_top(n, x, z, hi[1])
            else:
                top = self._ray(mesh[0], mesh[1], x, z, hi[1] + 1.0, lo[1] - 1.0)
            if top is not None and (best is None or top > best):
                best = top
        return float(default if best is None else best)

    @staticmethod
    def _box_top(n, x, z, y_hi):
        """Where a ray straight down at (x, z) enters the (maybe turned) block, or None."""
        R, c = n.p["cf"].R, n.p["cf"].p
        h = np.asarray(n.p["size"], float) / 2
        o = R.T @ (np.array((x, y_hi + 1.0, z)) - c)
        d = R.T @ np.array((0.0, -1.0, 0.0))
        t0, t1 = -np.inf, np.inf
        for i in range(3):
            if abs(d[i]) < 1e-9:
                if abs(o[i]) > h[i] + 1e-6:
                    return None
                continue
            a, b = (-h[i] - o[i]) / d[i], (h[i] - o[i]) / d[i]
            t0, t1 = max(t0, min(a, b)), min(t1, max(a, b))
        if t0 > t1 + 1e-9:
            return None
        return y_hi + 1.0 - t0

    def lowest(self, pts, default=0.0):
        return min(self.y(x, z, default) for (x, z) in pts)


def catenary(p0, p1, sag, r=0.075, n=12, sides=4):
    """A wire hanging from p0 to p1, `sag` studs below the chord at its middle."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    pts = []
    for i in range(n + 1):
        t = i / n
        p = p0 + (p1 - p0) * t
        p[1] -= sag * 4 * t * (1 - t)
        pts.append(p)
    return G.tube(pts, max(r, 0.075), sides)


def chainlink(w, h, cell=0.9, r=0.075):
    """A chain-link panel w wide, h tall in the XY plane (centred), wires at +-45 degrees,
    diamonds `cell` across."""
    g = G.Geo()
    hw, hh = w / 2, h / 2
    dc = cell * math.sqrt(2)
    for sgn in (1, -1):
        c = -hw - hh + dc / 2
        while c < hw + hh:
            if sgn > 0:                       # y = x - c
                xa, xb = max(-hw, c - hh), min(hw, c + hh)
                pa, pb = (xa, xa - c), (xb, xb - c)
            else:                             # y = c - x
                xa, xb = max(-hw, c - hh), min(hw, c + hh)
                pa, pb = (xa, c - xa), (xb, c - xb)
            if xb - xa > 0.15:
                g.add(G.tube([(pa[0], pa[1], 0.0), (pb[0], pb[1], 0.0)], r, 4))
            c += dc
    return g


def corrugated(w, d, pitch=0.8, amp=0.15, t=0.15):
    """A corrugated sheet w across the ridges (X) and d along them (Z), centred, ridges up."""
    n = max(2, int(round(w / pitch)))
    top, bot = [], []
    for i in range(2 * n + 1):
        x = -w / 2 + w * i / (2 * n)
        y = amp if i % 2 else 0.0
        top.append((x, y + t))
        bot.append((x, y))
    outline = top + bot[::-1]
    return G.extrude(outline, d, "z", (0, 0, 0))


def flat_pole(h, r0, r1, n=8):
    """A tapered round pole from y 0 to h."""
    prof = [(0.0, 0.0), (r0, 0.0), (r1, h - 0.06), (r1 - 0.05, h), (0.0, h)]
    return G.outward(G.lathe(prof, n, phase=math.pi / n))


def cctv_geo(yaw=0.0, tilt=18.0):
    """A CCTV camera on a wall bracket (origin on the mount, +Z out of it): the body swivels
    `yaw` degrees about Y on the arm's knuckle (+ towards +X) and tilts `tilt` degrees down.
    Returns (geo, lens front, LED spot), the points in the same space."""
    g = G.Geo()
    g.add(bevel_box(0.7, 0.9, 0.2, 0.05, c=(0, 0, 0.1)))                         # wall plate
    g.add(rod((0, 0, 0.2), (0, 0.15, 0.9), 0.1, 6))                            # arm
    g.add(G.sphere(0.17, 8, 4, c=(0, 0.15, 0.9)))                             # knuckle
    body = G.Geo()
    body.add(bevel_box(0.6, 0.55, 1.4, 0.08, c=(0, 0, 0)))
    body.add(bevel_box(0.75, 0.15, 1.6, 0.04, c=(0, 0.35, 0.1)))               # sun hood
    body.add(ccyl(0.18, 0.15, 8, "z", (0, -0.02, 0.75), 0.03))                 # lens ring
    Mb = G.T(0, 0.15, 0.9) @ G.RY(yaw) @ G.RX(tilt) @ G.T(0, 0.3, 0.45)
    g.add(body.xf(Mb))
    lens = (Mb @ np.array((0.0, -0.02, 0.83, 1.0)))[:3]
    led = (Mb @ np.array((0.3, 0.05, 0.4, 1.0)))[:3]
    return g, lens, led
