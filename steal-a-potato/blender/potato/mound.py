"""The seed Mound (kit piece and the 14 per area) and where the mounds go in an area."""
import math

import numpy as np

import spsgeo as G
from spsgeo import CF

from . import layout as L
from .geo import bevel_box

SOIL = (134, 88, 56)
SOIL_DARK = (104, 66, 42)
PEBBLE = (168, 164, 158)
DENT_Y = 0.75          # the seed sits here (the top centre of the dent)


def heap_geo():
    """A low heap of dug soil, 5 wide and 1.2 high, with a dent in the top: chunky rings."""
    rmod = lambda a: 1.0 + 0.07 * math.sin(3 * a) + 0.04 * math.sin(7 * a + 1.0)
    prof = [(0.0, DENT_Y - 0.05), (0.55, DENT_Y), (0.95, 1.12), (1.25, 1.2), (1.75, 0.98), (2.2, 0.55), (2.5, 0.12),
            (2.5, 0.0), (0.0, 0.0)]
    g = G.lathe(prof, 12, rmod=rmod)
    return G.outward(g)


def clods_geo():
    """A few darker clods on the heap's rim."""
    g = G.Geo()
    for k, a in enumerate((0.3, 1.9, 3.4, 4.9)):
        r = 1.6 + 0.2 * (k % 2)
        g.add(bevel_box(0.7, 0.5, 0.6, 0.15, (r * math.cos(a), 1.0 - 0.25 * (r - 1.6), r * math.sin(a))).xf(
            G.M(G.ry(30 * k))))
    return g


def pebbles_geo():
    g = G.Geo()
    for k, (a, r, s) in enumerate(((0.8, 2.75, 0.5), (2.6, 2.9, 0.4), (4.1, 2.7, 0.55), (5.5, 2.95, 0.35))):
        g.add(bevel_box(s, s * 0.6, s * 0.8, 0.1, (r * math.cos(a), s * 0.3, r * math.sin(a))).xf(G.M(G.ry(40 * k))))
    return g


def mound(k, parent, cf_ground, name="Mound"):
    """Model Mound standing at cf_ground (ground level); its pivot (PrimaryPart Heap's pivot) is
    the top centre of the dent, so Mound:GetPivot() is where the seed goes."""
    m = k.sc.model(parent, name)
    heap = k.mesh(m, "Heap", "Mound_Heap", heap_geo(), cf_ground, SOIL)
    k.mesh(m, "Clods", "Mound_Clods", clods_geo(), cf_ground, SOIL_DARK)
    k.mesh(m, "Pebbles", "Mound_Pebbles", pebbles_geo(), cf_ground, PEBBLE)
    heap.p["pivot"] = heap.p["cf"].inv() * (cf_ground * CF((0.0, DENT_Y, 0.0)))
    m.p["primary"] = heap
    return m


def place(n, rng, tucked=(), avoid=()):
    """14 mound spots (x, z) in area n: at least 16 apart, 12 from the walls, 20 from the area's
    ends. `tucked` are preferred spots beside props (taken first if they fit); `avoid` is a list
    of (x, z, r) circles to keep out of (props, the hero)."""
    zs, zn = L.area_z(n)
    xlim = L.FIELD_X[1] - L.MOUND_WALL - 2.5
    z_hi, z_lo = zs - L.MOUND_BORDER, zn + L.MOUND_BORDER

    def ok(x, z, chosen):
        if abs(x) > xlim or not (z_lo <= z <= z_hi):
            return False
        if any(math.hypot(x - ax, z - az) < ar for (ax, az, ar) in avoid):
            return False
        return all(math.hypot(x - cx, z - cz) >= L.MOUND_GAP for (cx, cz) in chosen)

    chosen = []
    for (x, z) in tucked:
        if len(chosen) < L.MOUND_COUNT and ok(x, z, chosen):
            chosen.append((x, z))
    # the rest spread evenly (best-candidate sampling: of 40 tries, the one farthest from the others)
    bands = L.MOUND_COUNT - len(chosen)
    for _ in range(bands):
        best, best_d = None, -1.0
        for _t in range(400):
            x = rng.uniform(-xlim, xlim)
            z = rng.uniform(z_lo, z_hi)
            if not ok(x, z, chosen):
                continue
            d = min([math.hypot(x - cx, z - cz) for (cx, cz) in chosen] + [1e9])
            if d > best_d:
                best, best_d = (x, z), d
            if _t > 40 and best is not None:
                break
        if best is not None:
            chosen.append(best)
    assert len(chosen) == L.MOUND_COUNT, ("area %d: only %d mounds fit" % (n, len(chosen)), bands)
    return chosen
