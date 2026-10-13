"""The 46 hand-held items for the remade map: batch 1's, with the five hand tools rebuilt to
the brief's sizes (rolling pin 2.2, ladle 1.8, knife 1.4, cutter 1.3, peel 5) in the one mesh
language, and no Metal anywhere (SmoothPlastic, flat colour).

The peel: 5 long with a head 3.5 wide and 2.9 deep, not the 2.2 asked for -- the game carries
a 3.4-wide pizza on it (marker Carry), and a 2.2 head would leave the pizza hanging 0.6 off
each side. Everything else about the items (Handle at the grip, -Z forward, the Rest
attachment, markers, welds) is exactly as in batch 1."""
import math

import numpy as np

import map_items as I
import spsgeo as G
from spsgeo import CF, T, RX, RY, RZ, S

from .kit import bevel_box, ccyl, cfrustum, rod

Item = I.Item


def _zc(r, z0, z1, n=10, x=0.0, y=0.0, b=0.05):
    """Chamfered cylinder along Z from z0 to z1."""
    return ccyl(r, abs(z1 - z0), n, "z", (x, y, (z0 + z1) / 2), b)


def rolling_pin():
    """2.2 long: a 1.2 barrel and two handles; held by one handle, barrel forward."""
    it = Item("RollingPin", desc="held by one handle, barrel forward")
    it.add("Barrel", "wood_light", _zc(0.32, -1.5, -0.3, 12, b=0.08))
    h = _zc(0.15, -0.3, 0.05, 8)
    h.add(_zc(0.15, -1.85, -1.5, 8))
    h.add(ccyl(0.19, 0.15, 8, "z", (0, 0, 0.125), 0.04))
    h.add(ccyl(0.19, 0.15, 8, "z", (0, 0, -1.925), 0.04))
    it.add("Handles", "wood", h)
    return it


def knife():
    """1.4 long chef's knife, edge down, tip forward: a 0.85 blade and a 0.55 grip."""
    it = Item("Knife", desc="chef's knife, edge down, tip forward")
    out = [(-0.3, 0.12), (-0.95, 0.09), (-1.12, 0.0), (-0.98, -0.1), (-0.62, -0.2), (-0.32, -0.22), (-0.3, -0.2),
           (-0.3, 0.12)]
    blade = G.extrude(out, 0.15, "x")
    blade.add(bevel_box(0.2, 0.36, 0.12, 0.03, c=(0, -0.03, -0.27)))            # bolster
    it.add("Blade", "steel_light", blade)
    grip = bevel_box(0.2, 0.26, 0.55, 0.07, c=(0, -0.02, 0.02))
    for z in (-0.12, 0.14):
        grip.add(ccyl(0.05, 0.22, 6, "x", (0, -0.02, z), 0.01))
    it.add("Grip", "black", grip)
    it.rest_rot = G.rz(90)          # lies on its side
    return it


def pizza_cutter():
    """1.3 long wheel cutter, wheel forward."""
    it = Item("PizzaCutter", desc="wheel cutter, wheel forward")
    it.add("Wheel", "steel_light", ccyl(0.28, 0.15, 14, "x", (0, -0.18, -0.6), 0.03))
    fork = G.Geo()
    fork.add(bevel_box(0.15, 0.15, 0.45, 0.03, c=(0, -0.1, -0.38)).xf(RX(-12)))
    fork.add(ccyl(0.09, 0.3, 8, "x", (0, -0.18, -0.6), 0.02))
    it.add("Fork", "steel_dark", fork)
    hdl = _zc(0.13, -0.25, 0.27, 8)
    hdl.add(ccyl(0.16, 0.15, 8, "z", (0, 0, 0.345), 0.03))
    it.add("Grip", "red", hdl)
    it.rest_rot = G.rz(90)
    return it


def ladle():
    """1.8 long ladle, bowl forward and down."""
    it = Item("Ladle", desc="long ladle, bowl forward and down")
    bowl = G.lathe_loop([(0.0, -0.3), (0.26, -0.27), (0.37, -0.12), (0.39, 0.0), (0.3, 0.0), (0.29, -0.1),
                         (0.2, -0.2), (0.0, -0.22)], 12)
    bowl.weld()
    g = G.outward(bowl).xf(T(0, -0.3, -1.1))
    g.add(G.tube([(0, -0.3, -0.76), (0, -0.12, -0.62), (0, 0.06, -0.25), (0, 0.12, 0.12), (0, 0.06, 0.28)], 0.075, 6))
    it.add("Ladle", "steel_light", g)
    it.add("Grip", "black", _zc(0.11, -0.2, 0.3, 6, y=0.1))
    return it


def pizza_peel():
    """5 long: a 3.5 x 2.9 wooden head (a 3.4 pizza rides on it, marker Carry) on a 2.1 pole."""
    it = Item("PizzaPeel", desc="long wooden peel; a pizza rides on the blade (marker Carry)")
    hw, d = 1.75, 2.9
    pts = [(0.5, 0.25), (0.95, -0.05), (hw, -0.45), (hw, -(d - 0.55))]
    for k in range(1, 4):                                   # rounded front corners
        a = math.radians(90 * k / 4)
        pts.append((hw - 0.55 + 0.55 * math.cos(a), -(d - 0.55) - 0.55 * math.sin(a)))
    pts += [(hw - 0.55, -d), (-(hw - 0.55), -d)]
    for k in range(1, 4):
        a = math.radians(90 + 90 * k / 4)
        pts.append((-(hw - 0.55) + 0.55 * math.cos(a), -(d - 0.55) - 0.55 * math.sin(a)))
    pts += [(-hw, -(d - 0.55)), (-hw, -0.45), (-0.95, -0.05), (-0.5, 0.25)]
    blade = G.extrude(pts, 0.15, "y", (0, 0.075, 0))
    pole = _zc(0.15, 0.2, 1.85, 8, y=0.15)
    pole.add(G.sphere(0.18, 8, 4, c=(0, 0.15, 1.95)))
    m = T(0, -0.15, -1.6)                                   # grip near the handle end = origin
    it.add("Blade", "wood_light", blade.xf(m))
    it.add("Pole", "wood_dark", pole.xf(m))
    it.markers.append(("Carry", CF((0, 0.15 - 0.15, -1.5 - 1.6))))
    return it


# ---------------------------------------------------------------- drinks (V3)
# a can 0.74 wide and 1.28 tall: rolled bottom, a white label band with the flavour's stripe,
# a lid with a rim and a ring pull; a bottle for the cooler's top shelf, the same width.
SODA = {"Cola": (200, 32, 36), "Orange": (240, 132, 30), "Lime": (96, 190, 64), "Grape": (122, 62, 164)}


def can_parts(color):
    """[(part, colour, geo)] for a can standing on y = -0.64 (centre at the origin)."""
    body = G.outward(G.lathe([(0.0, -0.64), (0.26, -0.64), (0.34, -0.57), (0.355, -0.5), (0.355, 0.42),
                               (0.3, 0.52), (0.0, 0.52)], 14))
    band = G.ring(0.37, 0.3, 0.6, 14, "y", (0, -0.04, 0))
    stripe = G.ring(0.37, 0.3, 0.15, 14, "y", (0, 0.08, 0)).xf(S(1.002, 1.0, 1.002))
    lid = ccyl(0.3, 0.1, 14, "y", (0, 0.5, 0), 0.02)
    lid.add(G.torus(0.28, 0.075, 14, 4, "y", (0, 0.565, 0)))
    pull = G.torus(0.09, 0.075, 8, 4, "y", (0, 0.56, 0.1))
    pull.add(bevel_box(0.16, 0.15, 0.26, 0.04, c=(0, 0.565, -0.06)))
    return [("Body", color, body), ("Band", (238, 236, 228), band), ("Stripe", color, stripe),
            ("Lid", "steel_light", lid), ("Pull", (200, 204, 206), pull)]


def bottle_parts(color):
    """A plastic soda bottle 0.74 wide, 1.45 tall, standing on y = -0.65."""
    body = G.outward(G.lathe([(0.0, -0.65), (0.28, -0.65), (0.355, -0.55), (0.355, 0.12), (0.3, 0.3), (0.16, 0.5),
                               (0.15, 0.62), (0.0, 0.62)], 14))
    label = G.ring(0.37, 0.3, 0.45, 14, "y", (0, -0.2, 0))
    cap = ccyl(0.17, 0.18, 10, "y", (0, 0.71, 0), 0.04)
    return [("Body", color, body), ("Label", (238, 236, 228), label), ("Cap", color, cap)]


def soda_can(name, color):
    it = Item(name, mesh_prefix="SodaCan", desc="soda can 0.74 x 1.28 (one mesh, four colours)")
    for pname, c, g in can_parts(color):
        it.add(pname, c, g)
    return it


def soda_bottle(name, color):
    it = Item(name, mesh_prefix="SodaBottle", desc="soda bottle 0.74 x 1.45 for the cooler's top shelf")
    for pname, c, g in bottle_parts(color):
        it.add(pname, c, g)
    return it


NEW = {"RollingPin": rolling_pin, "Knife": knife, "PizzaCutter": pizza_cutter, "Ladle": ladle,
       "PizzaPeel": pizza_peel}
NEW.update({"SodaCan" + f: (lambda f=f: soda_can("SodaCan" + f, SODA[f])) for f in SODA})
ADDED = [lambda f=f: soda_bottle("SodaBottle" + f, SODA[f]) for f in SODA]


def _colour(c):
    """Batch 1's colour names stay as they were; the remake's own names become RGB."""
    import spslib
    from .kit import PAL
    if isinstance(c, str) and c not in spslib.C and c in PAL:
        return PAL[c]
    return c


def _no_metal(it):
    it.parts = [(n, _colour(c), ("SmoothPlastic" if mt == "Metal" else mt), tr, g) for (n, c, mt, tr, g) in it.parts]
    return it


_CACHE = None


def all_items():
    out = []
    for it in I.all_items():
        if it.name in NEW:
            it = NEW[it.name]()
        out.append(_no_metal(it))
    out += [_no_metal(f()) for f in ADDED]
    return out


def get(name):
    global _CACHE
    if _CACHE is None:
        _CACHE = {it.name: it for it in all_items()}
    return _CACHE[name]


def place(k, parent, name, world, **kw):
    """An item Model (Handle + welded MeshParts) with its Handle at `world`."""
    return I.place(k.sc, parent, get(name), world, **kw)


def place_on(k, parent, name, surface_cf, **kw):
    """An item resting on a surface frame (its Rest attachment on surface_cf)."""
    it = get(name)
    return I.place(k.sc, parent, it, surface_cf * it.rest().inv(), **kw)


def build_items(k):
    """The Items folder: every item Model as a template, in a tidy grid well under the map
    (Y -60), anchored Handle, welded meshes -- as batch 1."""
    folder = k.sc.root.get("Items")
    x, z, row_d = -60.0, -20.0, 0.0
    for it in all_items():
        lo, hi = it.bbox()
        w, d = hi[0] - lo[0] + 2.0, hi[2] - lo[2] + 2.0
        if x + w > 60:
            x, z, row_d = -60.0, z + row_d, 0.0
        I.place(k.sc, folder, it, CF((x - lo[0], -60.0 - lo[1], z - lo[2])))
        x += w
        row_d = max(row_d, d)
    return folder
