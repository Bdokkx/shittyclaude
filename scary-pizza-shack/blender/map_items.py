"""Hand-held items (section D). Each item is modelled in its own HANDLE space:
the Handle (invisible, the grip) sits at the origin, -Z points away from the body,
+Y is up. Every item also gets an Attachment "Rest" in its Handle: the point the
item touches a surface when it is set down, with +Y = the surface normal, so
    item:PivotTo(marker.CFrame * item.Handle.Rest.CFrame:Inverse())
sets it on any item marker. Pizza layers share one origin (pizza centre, bottom)
so they stack by putting their Handles on the same CFrame.
"""
import math

import numpy as np

import spsgeo as G
from spsgeo import CF, T, RX, RY, RZ, S

PIZZA_R = 1.7          # 3.4 across
TOP_Y = 0.24           # melted cheese surface: where toppings sit


class Item:
    def __init__(self, name, mesh_prefix=None, desc=""):
        self.name = name
        self.prefix = mesh_prefix or name
        self.parts = []        # (part name, colour, material, transparency, Geo)
        self.markers = []      # (name, CF)
        self.attach = []       # (name, CF)
        self.motors = []       # (part name, motor name, hinge CF)
        self.welded_to = {}    # part name -> part name (instead of the Handle)
        self.attrs = {}
        self.rest_rot = np.eye(3)
        self.desc = desc
        self.moving = []       # README notes
        self.rest_override = None
        self.weld_names = {}   # part name -> weld name (default "Weld")

    def add(self, pname, color, geo, material="Plastic", transparency=0.0):
        self.parts.append((pname, color, material, transparency, geo))
        return self

    def tris(self):
        return sum(g.tris() for *_, g in self.parts)

    def bbox(self):
        vs = np.vstack([g.arr() for *_, g in self.parts])
        return vs.min(0), vs.max(0)

    def rest(self):
        """Rest attachment: lowest point of the item in its resting pose (rest_rot)."""
        if self.rest_override is not None:
            return self.rest_override
        R = self.rest_rot
        vs = np.vstack([g.arr() for *_, g in self.parts]) @ R.T
        lo, hi = vs.min(0), vs.max(0)
        # pose P (Handle in surface space) = translate(t) * R; Rest = P^-1
        t = np.array((-(lo[0] + hi[0]) / 2, -lo[1], -(lo[2] + hi[2]) / 2))
        P = CF(t, R)
        return P.inv()

    def size(self):
        lo, hi = self.bbox()
        return hi - lo

    def shift(self, m):
        self.parts = [(n, c, mt, tr, g.xf(m)) for (n, c, mt, tr, g) in self.parts]
        return self


def pizza_layer(it):
    it.rest_override = CF()
    it.attrs["PizzaLayer"] = True
    return it


# ---------------------------------------------------------------- helpers

def ycyl(r, y0, y1, n=12, x=0.0, z=0.0):
    return G.cyl(r, y1 - y0, n, "y", (x, (y0 + y1) / 2, z))


def zcyl(r, z0, z1, n=10, x=0.0, y=0.0):
    return G.cyl(r, z1 - z0, n, "z", (x, y, (z0 + z1) / 2))


def xcyl(r, x0, x1, n=10, y=0.0, z=0.0):
    return G.cyl(r, x1 - x0, n, "x", ((x0 + x1) / 2, y, z))


def lathe(profile, n=12, **kw):
    return G.outward(G.lathe(profile, n, **kw))


def wobble(k, amp):
    return lambda a: 1.0 + amp * math.sin(k * a) + amp * 0.5 * math.sin((k + 3) * a + 1.3)


# ---------------------------------------------------------------- pizza layers (origin = pizza centre, bottom)

def dough_ball():
    it = Item("DoughBall", desc="raw dough ball, ~1.5 across")
    g = G.blob(0.76, 10, 6, scale=(1, 0.66, 1), jitter=0.06, seed=3, flat_bottom=-0.42)
    lo, hi = g.bbox()
    it.add("Dough", "dough", g.xf(T(0, -lo[1], 0)))
    return pizza_layer(it)


def dough_base():
    it = Item("DoughBase", desc="rolled base with a raised crust rim, 3.4 across")
    it.add("Base", "dough", G.cyl(1.56, 0.14, 16, "y", (0, 0.07, 0)))
    rim = G.lathe_loop([(1.36, 0.0), (1.70, 0.0), (1.72, 0.15), (1.63, 0.30), (1.49, 0.33), (1.38, 0.2)], 16)
    it.add("Rim", "crust", rim)
    return pizza_layer(it)


def sauce_layer():
    it = Item("SauceLayer", desc="tomato sauce spread inside the rim")
    g = lathe([(0, 0.14), (1.38, 0.14), (1.36, 0.19), (0, 0.19)], 16, rmod=wobble(5, 0.025))
    it.add("Sauce", "sauce", g)
    return pizza_layer(it)


def cheese_raw():
    it = Item("CheeseRaw", desc="shredded cheese scattered on the sauce")
    g = G.Geo()
    g.add(lathe([(0, 0.185), (1.3, 0.185), (1.25, 0.205), (0, 0.205)], 14, rmod=wobble(7, 0.06)))
    rng = np.random.default_rng(11)
    k = 0
    while k < 34:
        r = 1.22 * math.sqrt(rng.random())
        a = rng.random() * math.tau
        x, z = r * math.cos(a), r * math.sin(a)
        strand = G.box(0.08, 0.05, 0.34).xf(T(x, 0.225 + 0.02 * rng.random(), z) @ RY(rng.random() * 180)
                                             @ RX((rng.random() - 0.5) * 20))
        g.add(strand)
        k += 1
    it.add("Cheese", "cheese", g)
    return pizza_layer(it)


def cheese_melted():
    it = Item("CheeseMelted", desc="melted cheese, bubbly edge")
    g = lathe([(0, 0.18), (1.42, 0.18), (1.41, 0.215), (1.1, 0.235), (0, 0.24)], 18, rmod=wobble(6, 0.035))
    rng = np.random.default_rng(5)
    for _ in range(6):
        r = 1.1 * math.sqrt(rng.random())
        a = rng.random() * math.tau
        b = G.sphere(0.1 + 0.05 * rng.random(), 6, 3, scale=(1, 0.45, 1), c=(r * math.cos(a), 0.235, r * math.sin(a)))
        g.add(b)
    it.add("Cheese", "cheese_melt", g)
    return pizza_layer(it)


def burnt():
    it = Item("Burnt", desc="charred overlay for an over-baked pizza (sits on the cheese and the rim)")
    g = G.Geo()
    rng = np.random.default_rng(21)
    for _ in range(7):
        r = 1.05 * math.sqrt(rng.random())
        a = rng.random() * math.tau
        pts = G.circle_pts(0.18 + 0.2 * rng.random(), 8)
        pts = [(x * (1 + 0.3 * (rng.random() - 0.5)), y * (1 + 0.3 * (rng.random() - 0.5))) for x, y in pts]
        g.add(G.slab_poly(pts, 0.012, (r * math.cos(a), 0.242, r * math.sin(a))))
    for k in range(9):
        a = math.tau * k / 9 + rng.random() * 0.3
        seg = G.box(0.22, 0.03, 0.42 + 0.3 * rng.random()).xf(
            T(1.56 * math.cos(a), 0.322, 1.56 * math.sin(a)) @ RY(-math.degrees(a)))
        g.add(seg)
    it.add("Char", "burnt", g)
    return pizza_layer(it)


def cut_lines():
    it = Item("CutLines", desc="8-slice cut marks across the top")
    g = G.Geo()
    r1, r2 = 1.35, 1.74
    outline = [(-r2, 0.33), (-1.45, 0.345), (-r1, 0.255), (r1, 0.255), (1.45, 0.345), (r2, 0.33),
               (r2, 0.36), (1.45, 0.375), (r1, 0.285), (-r1, 0.285), (-1.45, 0.375), (-r2, 0.36)]
    line = G.extrude(outline, 0.06, "z")
    for k in range(4):
        g.add(line.xf(RY(45 * k)))
    it.add("Lines", "burnt", g)
    return pizza_layer(it)


# ---------------------------------------------------------------- toppings (origin = bottom centre)

def pepperoni_slice():
    it = Item("PepperoniSlice", desc="topping")
    it.add("Slice", "pepperoni", G.cyl(0.3, 0.05, 10, "y", (0, 0.025, 0)))
    spots = G.Geo()
    for x, z in ((0.12, 0.05), (-0.1, 0.1), (0.0, -0.13), (-0.12, -0.05)):
        spots.add(G.cyl(0.045, 0.01, 6, "y", (x, 0.053, z)))
    it.add("Spots", (226, 150, 140), spots)
    return it


def mushroom_slice():
    it = Item("MushroomSlice", desc="topping")
    pts = []
    for k in range(9):
        a = math.pi * k / 8
        pts.append((0.3 * math.cos(a), -0.04 - 0.24 * math.sin(a)))
    pts = pts[::-1]          # left to right across the cap's top (toward -Z)
    pts = [(-0.3, -0.04)] + pts[1:-1] + [(0.3, -0.04), (0.1, -0.04), (0.1, 0.24), (-0.1, 0.24), (-0.1, -0.04)]
    it.add("Slice", "mushroom", G.extrude(pts, 0.05, "y", (0, 0.025, 0)))
    return it


def pepper_ring():
    it = Item("PepperRing", desc="topping")
    it.add("Ring", "pepper", G.lobed_ring(0.32, 0.25, 0.05, 16, 4, 0.1).xf(T(0, 0.025, 0)))
    return it


def olive_ring():
    it = Item("OliveRing", desc="topping")
    it.add("Ring", "olive", G.ring(0.16, 0.07, 0.06, 10, c=(0, 0.03, 0)))
    return it


def onion_ring():
    it = Item("OnionRing", desc="topping")
    g = G.ring(0.3, 0.25, 0.05, 14, c=(0, 0.025, 0))
    g.add(G.ring(0.19, 0.15, 0.05, 12, c=(0, 0.025, 0)))
    it.add("Ring", "onion", g)
    return it


def pineapple_chunk():
    it = Item("PineappleChunk", desc="topping")
    pts = [(0.14 * math.cos(a), 0.14 * math.sin(a)) for a in np.radians((-22, 22))]
    pts += [(0.4 * math.cos(a), 0.4 * math.sin(a)) for a in np.radians((22, 0, -22))]
    g = G.extrude(pts, 0.16, "y", (-0.27, 0.08, 0))
    it.add("Chunk", "pineapple", g)
    return it


def sausage_bit():
    it = Item("SausageBit", desc="topping")
    g = G.blob(0.17, 7, 4, scale=(1.1, 0.7, 1), jitter=0.25, seed=7, flat_bottom=-0.1)
    lo, hi = g.bbox()
    it.add("Bit", "sausage", g.xf(T(0, -lo[1], 0)))
    return it


def basil_leaf():
    it = Item("BasilLeaf", desc="topping")
    g = G.slab_poly(G.leaf_pts(0.6, 0.36, 6), 0.03)
    lo, hi = g.bbox()
    g = g.xf(T(0, 0, -(lo[2] + hi[2]) / 2))
    vs = g.arr()
    vs[:, 1] += 0.18 * (vs[:, 0] / 0.18) ** 2 * 0.25        # edges curl up
    g.v = [tuple(p) for p in vs]
    it.add("Leaf", "basil", g)
    return it


# ---------------------------------------------------------------- whole ingredients (origin = centre)

def pepperoni_stick():
    it = Item("PepperoniStick", desc="whole salami stick, chop it for PepperoniSlice")
    prof = [(0, -1.05), (0.18, -1.03), (0.25, -0.95), (0.27, -0.7), (0.27, 0.7), (0.25, 0.95), (0.18, 1.03), (0, 1.05)]
    g = lathe(prof, 10).xf(RX(90))
    it.add("Stick", "pepperoni", g)
    it.add("Tie", "paper", G.torus(0.27, 0.035, 10, 4, "z", (0, 0, 0.9)))
    return it


def mushroom():
    it = Item("Mushroom", desc="whole mushroom")
    cap = lathe([(0, 0.02), (0.2, 0.0), (0.52, -0.04), (0.58, 0.12), (0.46, 0.33), (0.22, 0.44), (0, 0.46)], 12)
    stem = lathe([(0, -0.45), (0.2, -0.45), (0.17, -0.1), (0.15, 0.06), (0, 0.06)], 10)
    it.add("Cap", "mushroom_cap", cap)
    it.add("Stem", "mushroom", stem)
    return it


def bell_pepper():
    it = Item("BellPepper", desc="whole green pepper")
    prof = [(0, -0.48), (0.28, -0.47), (0.44, -0.3), (0.5, 0.0), (0.48, 0.24), (0.34, 0.42), (0.14, 0.46),
            (0, 0.4)]
    body = lathe(prof, 12, rmod=lambda a: 1 + 0.1 * math.cos(4 * a))
    it.add("Body", "pepper", body)
    stem = G.tube([(0, 0.38, 0), (0, 0.56, 0), (0.08, 0.68, 0.04)], 0.06, 5)
    it.add("Stem", "green_dark", stem)
    return it


def olive_jar():
    it = Item("OliveJar", desc="jar of olives, chop for OliveRing")
    glass = lathe([(0, -0.62), (0.38, -0.62), (0.42, -0.55), (0.42, 0.3), (0.34, 0.42), (0.34, 0.5), (0, 0.5)], 10)
    it.add("Glass", (170, 200, 170), glass, material="Glass", transparency=0.45)
    ol = G.Geo()
    rng = np.random.default_rng(4)
    for k in range(7):
        a = math.tau * k / 7
        r = 0.2 if k else 0.0
        ol.add(G.sphere(0.13, 5, 3, scale=(1, 1.25, 1), c=(r * math.cos(a), -0.45 + 0.24 * (k % 3), r * math.sin(a))))
    it.add("Olives", "olive", ol)
    it.add("Label", "cream", G.ring(0.435, 0.4, 0.34, 10, c=(0, -0.16, 0)))
    it.add("Lid", "green", ycyl(0.37, 0.48, 0.64, 10))
    return it


def onion():
    it = Item("Onion", desc="whole onion")
    body = lathe([(0, -0.46), (0.28, -0.42), (0.48, -0.16), (0.5, 0.08), (0.36, 0.34), (0.13, 0.5), (0.05, 0.62),
                   (0, 0.66)], 12)
    it.add("Body", "onion_skin", body)
    root = G.Geo()
    for k in range(5):
        a = math.tau * k / 5
        root.add(G.frustum(0.0, 0.03, 0.18, 4, "y", (0.07 * math.cos(a), -0.52, 0.07 * math.sin(a))))
    it.add("Root", "mushroom", root)
    return it


def pineapple():
    it = Item("Pineapple", desc="whole pineapple, chop for PineappleChunk")
    body = G.sphere(0.55, 8, 6, scale=(1, 1.45, 1))
    vs = body.arr()
    for i in range(len(vs)):          # faceted, diamond-like skin
        if 0 < i < len(vs) - 1:
            vs[i, 0] *= 1.0 + 0.06 * ((i % 2) * 2 - 1)
            vs[i, 2] *= 1.0 + 0.06 * ((i % 2) * 2 - 1)
    body.v = [tuple(p) for p in vs]
    it.add("Body", "pineapple_skin", G.outward(body))
    crown = G.Geo()
    leaf = G.extrude(G.leaf_pts(0.85, 0.22, 4), 0.04, "z")
    for k in range(7):
        crown.add(leaf.xf(T(0, 0.7, 0) @ RY(360 * k / 7) @ RX(22 + 12 * (k % 2)) @ T(0, 0, 0.08)))
    crown.add(G.extrude(G.leaf_pts(0.95, 0.24, 4), 0.04, "z").xf(T(0, 0.72, 0)))
    it.add("Crown", "leaf", crown)
    return it


def sausage():
    it = Item("Sausage", desc="sausage links, chop for SausageBit")
    g = G.Geo()
    for z0, z1, bend in ((-1.0, -0.06, 0.08), (0.06, 1.0, -0.08)):
        path = [(bend * math.sin(math.pi * t), 0, z0 + (z1 - z0) * t) for t in np.linspace(0, 1, 5)]
        tube = G.tube(path, 0.21, 8)
        g.add(tube)
        g.add(G.sphere(0.21, 8, 4, c=path[0]))
        g.add(G.sphere(0.21, 8, 4, c=path[-1]))
    it.add("Links", "sausage", g)
    return it


def basil_pot():
    it = Item("BasilPot", desc="potted basil, pick for BasilLeaf")
    pot = lathe([(0, -0.62), (0.34, -0.62), (0.44, 0.08), (0.52, 0.1), (0.52, 0.26), (0, 0.26)], 10)
    it.add("Pot", "terracotta", pot)
    it.add("Soil", "soil", ycyl(0.44, 0.24, 0.3, 10))
    leaves = G.Geo()
    stems = G.Geo()
    leaf = G.slab_poly(G.leaf_pts(0.42, 0.26, 4), 0.03)
    rng = np.random.default_rng(9)
    for k in range(9):
        a = 360 * k / 9 + 20 * rng.random()
        h = 0.45 + 0.35 * rng.random()
        tilt = 25 + 20 * rng.random()
        top = (0.12 * math.cos(math.radians(a)), 0.3 + h, 0.12 * math.sin(math.radians(a)))
        stems.add(G.tube([(0, 0.28, 0), top], 0.03, 4))
        leaves.add(leaf.xf(T(*top) @ RY(-a + 90) @ RX(-tilt)))
    it.add("Leaves", "basil", leaves)
    it.add("Stems", "green", stems)
    return it


# ---------------------------------------------------------------- tools (origin = grip)

def rolling_pin():
    it = Item("RollingPin", desc="held by one handle, barrel forward")
    it.add("Barrel", "wood_light", zcyl(0.34, -2.95, -0.35, 12))
    h = zcyl(0.15, -0.35, 0.35, 8)
    h.add(zcyl(0.15, -3.65, -2.95, 8))
    h.add(zcyl(0.19, 0.35, 0.45, 8))
    h.add(zcyl(0.19, -3.75, -3.65, 8))
    it.add("Handles", "wood", h)
    return it


def knife():
    it = Item("Knife", desc="chef's knife, edge down, tip forward")
    out = [(-0.5, 0.16), (-2.2, 0.12), (-2.65, 0.0), (-2.4, -0.1), (-1.7, -0.28), (-0.6, -0.34), (-0.48, -0.3),
           (-0.48, 0.16)]
    blade = G.extrude(out, 0.06, "x")
    blade.add(G.box(0.12, 0.3, 0.12, (0, 0.0, -0.44)))      # bolster
    for z in (-0.05, 0.3):
        blade.add(xcyl(0.04, -0.11, 0.11, 6, y=-0.02, z=z))
    it.add("Blade", "steel", blade, material="Metal")
    hdl = G.box(0.18, 0.26, 0.95, (0, -0.02, 0.06))
    it.add("Grip", "black", hdl)
    it.rest_rot = G.rz(90)          # lies on its side
    return it


def pizza_cutter():
    it = Item("PizzaCutter", desc="wheel cutter, wheel forward")
    it.add("Wheel", "steel", xcyl(0.42, -0.03, 0.03, 14, y=-0.28, z=-1.25), material="Metal")
    fork = G.box(0.14, 0.1, 0.8).xf(T(0, -0.13, -0.85) @ RX(-20))
    fork.add(xcyl(0.1, -0.09, 0.09, 8, y=-0.28, z=-1.25))
    it.add("Fork", "steel_dark", fork, material="Metal")
    hdl = zcyl(0.14, -0.45, 0.55, 8)
    hdl.add(zcyl(0.17, 0.55, 0.65, 8))
    it.add("Grip", "red", hdl)
    it.rest_rot = G.rz(90)
    return it


def ladle():
    it = Item("Ladle", desc="long ladle, bowl forward and down")
    bowl = G.lathe_loop([(0.0, -0.36), (0.3, -0.33), (0.43, -0.15), (0.45, 0.0), (0.41, 0.0), (0.39, -0.12),
                         (0.28, -0.29), (0.0, -0.31)], 12)
    bowl.weld()
    g = bowl.xf(T(0, -0.42, -2.75))
    path = [(0, -0.42, -2.32), (0, -0.2, -2.1), (0, 0.05, -1.4), (0, 0.15, -0.4), (0, 0.2, 0.3), (0, 0.14, 0.55),
            (0, 0.0, 0.62)]
    g.add(G.tube(path, 0.06, 6))
    it.add("Ladle", "steel", G.outward(g), material="Metal")
    it.add("Grip", "black", zcyl(0.1, -0.35, 0.3, 6, y=0.17))
    return it


def pizza_peel():
    it = Item("PizzaPeel", desc="long wooden peel; a pizza rides on the blade (marker Carry)")
    pts = [(0.55, 0.4), (0.95, 0.0), (1.85, -0.45), (1.85, -3.05)]
    for k in range(1, 4):                                   # rounded front corners
        a = math.radians(90 * k / 4)
        pts.append((1.15 + 0.7 * math.cos(a), -3.05 - 0.7 * math.sin(a)))
    pts += [(1.15, -3.75), (-1.15, -3.75)]
    for k in range(1, 4):
        a = math.radians(90 + 90 * k / 4)
        pts.append((-1.15 + 0.7 * math.cos(a), -3.05 - 0.7 * math.sin(a)))
    pts += [(-1.85, -3.05), (-1.85, -0.45), (-0.95, 0.0), (-0.55, 0.4)]
    blade = G.extrude(pts, 0.12, "y", (0, 0.06, 0))
    hdl = zcyl(0.15, 0.2, 3.4, 8, y=0.15)
    hdl.add(G.sphere(0.2, 8, 4, c=(0, 0.15, 3.45)))
    m = T(0, -0.15, -2.8)                                   # grip near the handle end = origin
    it.add("Blade", "wood_light", blade.xf(m))
    it.add("Pole", "wood_dark", hdl.xf(m))
    it.markers.append(("Carry", CF((0, 0.12 - 0.15, -1.85 - 2.8))))
    return it


def grater():
    it = Item("Grater", desc="box grater, held by the top handle")
    body = G.frustum(0.62, 0.42, 1.4, 4, "y", (0, -0.85, 0), phase=math.pi / 4)
    it.add("Body", "steel", body, material="Metal")

    def ap(y):                                              # face distance from the axis at height y
        t = (y + 1.55) / 1.4
        return (0.62 + (0.42 - 0.62) * t) * math.cos(math.pi / 4)
    holes = G.Geo()
    for side in range(4):
        for k in range(3):
            y = -1.3 + 0.36 * k
            for j in (-1, 1):
                holes.add(G.box(0.16, 0.07, 0.03, (0.12 * j, y, -ap(y) - 0.006)).xf(RY(90 * side)))
    it.add("Holes", "black", holes)
    handle = G.tube([(-0.25, -0.15, 0), (-0.22, 0.12, 0), (0.0, 0.2, 0), (0.22, 0.12, 0), (0.25, -0.15, 0)],
                    0.07, 5, close_ends=True)
    it.add("Grip", "black", handle)
    return it.shift(T(0, -0.2, 0))


# ---------------------------------------------------------------- boxes, packs and other carryables

def pizza_box_flat():
    it = Item("PizzaBoxFlat", desc="flat-packed box, fold it at the BoxStation")
    it.add("Card", "cardboard", G.box(4.0, 0.16, 4.0, (0, 0, 0)))
    pr = G.ring(1.15, 0.85, 0.01, 18, c=(0, 0.085, 0))
    pr.add(G.cyl(0.62, 0.01, 14, "y", (0, 0.085, 0)))
    it.add("Print", "red", pr)
    return it


def pizza_box():
    it = Item("PizzaBox", desc="box with a hinged lid (Motor6D LidHinge), pizza goes on marker Inside")
    t = 0.08
    base = G.box(4.0, t, 4.0, (0, t / 2, 0))
    for (sx, sz, cx, cz) in ((4.0, t, 0, 2 - t / 2), (4.0, t, 0, -2 + t / 2), (t, 4.0, 2 - t / 2, 0),
                             (t, 4.0, -2 + t / 2, 0)):
        base.add(G.box(sx, 0.56, sz, (cx, t + 0.28, cz)))
    it.add("Base", "cardboard", base)
    lid = G.box(4.04, t, 4.04, (0, 0.64 + t / 2, 0))
    lid.add(G.box(4.04, 0.32, t, (0, 0.64 - 0.16 + t, 2.02 - t / 2)))
    it.add("Lid", "cardboard", lid)
    pr = G.ring(1.2, 0.9, 0.01, 18, c=(0, 0.725, 0))
    pr.add(G.cyl(0.65, 0.01, 14, "y", (0, 0.725, 0)))
    it.add("LidPrint", "red", pr)
    it.welded_to["LidPrint"] = "Lid"
    it.motors.append(("Lid", "LidHinge", CF((0, 0.68, -2.0))))
    it.markers.append(("Inside", CF((0, t, 0))))
    return it


SODA = {"SodaCanCola": (200, 32, 36), "SodaCanOrange": (240, 132, 30), "SodaCanLime": (96, 190, 64),
        "SodaCanGrape": (122, 62, 164)}


def soda_can(name, color):
    it = Item(name, mesh_prefix="SodaCan", desc="soda can (one mesh, four colours)")
    body = lathe([(0, -0.62), (0.3, -0.62), (0.38, -0.54), (0.38, 0.48), (0.3, 0.58), (0, 0.58)], 12)
    it.add("Body", color, body)
    top = ycyl(0.3, 0.56, 0.63, 12)
    top.add(G.box(0.14, 0.03, 0.26, (0, 0.645, 0.06)))
    it.add("Lid", "steel", top, material="Metal")
    it.add("Stripe", "white", G.ring(0.385, 0.36, 0.22, 12, c=(0, 0.0, 0)))
    return it


def ingredient_crate():
    it = Item("IngredientCrate", desc="wooden crate, two-handed; the Lid is held by WeldConstraint LidWeld")
    W, H, D = 3.0, 1.8, 2.2
    slats = G.Geo()
    for y in (-0.55, 0.2):
        for z in (-D / 2 + 0.06, D / 2 - 0.06):
            slats.add(G.box(W - 0.3, 0.55, 0.1, (0, y, z)))
        for x in (-W / 2 + 0.06, W / 2 - 0.06):
            slats.add(G.box(0.1, 0.55, D - 0.3, (x, y, 0)))
    slats.add(G.box(W - 0.2, 0.1, D - 0.2, (0, -H / 2 + 0.06, 0)))
    it.add("Slats", "wood", slats)
    frame = G.Geo()
    for x in (-W / 2 + 0.14, W / 2 - 0.14):
        for z in (-D / 2 + 0.14, D / 2 - 0.14):
            frame.add(G.box(0.28, H - 0.2, 0.28, (x, -0.1, z)))
    it.add("Frame", "wood_dark", frame)
    lid = G.Geo()
    for k in range(3):
        lid.add(G.box(W, 0.14, 0.68, (0, H / 2 - 0.13, -0.72 + 0.72 * k)))
    lid.add(G.box(W - 0.4, 0.1, 0.24, (0, H / 2 - 0.0, 0)))
    it.add("Lid", "wood_light", lid)
    it.weld_names["Lid"] = "LidWeld"
    it.attrs["TwoHanded"] = True
    return it


def flour_bag():
    it = Item("FlourBag", desc="paper sack of flour")
    rings = []
    for (y, w, d) in ((-1.0, 1.36, 0.82), (-0.6, 1.5, 0.94), (0.4, 1.5, 0.92), (0.75, 1.46, 0.56), (0.95, 1.5, 0.14)):
        rings.append([(sx * w / 2, y, sz * d / 2) for (sx, sz) in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
    bag = G.outward(G.loft(rings))
    it.add("Bag", "paper", bag)
    lab = G.box(1.1, 0.7, 0.02, (0, -0.25, -0.48))
    lab.add(G.box(1.1, 0.7, 0.02, (0, -0.25, 0.48)))
    it.add("Label", "red", lab)
    it.add("Stripe", "mustard", G.box(1.12, 0.14, 0.99, (0, 0.15, 0)))
    return it


def sauce_can():
    it = Item("SauceCan", desc="big tin of tomato sauce")
    can = lathe([(0, -0.66), (0.47, -0.66), (0.5, -0.6), (0.5, 0.6), (0.47, 0.66), (0, 0.66)], 12)
    it.add("Can", "steel", can, material="Metal")
    it.add("Label", "red", G.ring(0.515, 0.49, 0.9, 12, c=(0, -0.02, 0)))
    tom = G.cyl(0.2, 0.02, 8, "z", (0, -0.02, -0.525))
    tom.add(G.extrude(G.leaf_pts(0.16, 0.1, 3), 0.02, "z", (0, 0.16, -0.53)))
    it.add("Tomato", "mustard", tom)
    return it


def cheese_block():
    it = Item("CheeseBlock", desc="block of cheese for the grater")
    it.add("Block", "cheese", G.box(1.6, 0.9, 1.1))
    holes = G.Geo()
    for (x, y, face) in ((-0.4, 0.15, 1), (0.35, -0.2, 1), (0.1, 0.25, -1), (-0.45, -0.18, -1)):
        holes.add(G.cyl(0.13, 0.02, 8, "z", (x, y, face * 0.551)))
    holes.add(G.cyl(0.12, 0.02, 8, "y", (0.3, 0.451, 0.2)))
    holes.add(G.cyl(0.1, 0.02, 8, "y", (-0.35, 0.451, -0.15)))
    holes.add(G.cyl(0.11, 0.02, 8, "x", (0.801, 0.1, 0.0)))
    it.add("Holes", (214, 162, 58), holes)
    return it


def trash_bag():
    it = Item("TrashBag", desc="tied bin bag, held by the knot")
    bag = G.blob(0.82, 10, 6, scale=(1, 1.05, 0.95), jitter=0.13, seed=12, flat_bottom=-0.7)
    neck = G.frustum(0.38, 0.1, 0.5, 8, "y", (0, 0.98, 0))
    knot = G.blob(0.16, 6, 4, jitter=0.2, seed=2, c=(0, 1.3, 0))
    g = G.Geo().add([bag, neck, knot])
    lo, hi = g.bbox()
    m = T(0, -1.3, 0)                      # grip = the knot
    it.add("Bag", "black", g.xf(m))
    it.add("Tie", "mustard", G.torus(0.12, 0.03, 8, 4, "y", (0, 1.16, 0)).xf(m))
    return it


def fuel_can():
    it = Item("FuelCan", desc="red jerry can, held by the top handle")
    body = G.extrude(G.rounded_rect_pts(1.3, 1.6, 0.18, 2), 0.62, "x")
    body = body.xf(T(0, -1.05, 0))
    hdl = G.box(0.16, 0.12, 0.7, (0, 0.06, 0.1))
    for z in (-0.18, 0.38):
        hdl.add(G.box(0.16, 0.25, 0.1, (0, -0.1, z)))
    it.add("Body", "red", G.Geo().add([body, hdl]))
    cap = G.cyl(0.13, 0.3, 8, "y", (0, -0.12, -0.5)).xf(RX(0))
    it.add("Cap", "mustard", cap)
    return it


def flashlight():
    it = Item("Flashlight", desc="torch pointing forward; Lens is the front glass")
    it.add("Body", "black", zcyl(0.16, -0.35, 0.65, 10))
    head = G.frustum(0.27, 0.17, 0.42, 10, "z", (0, 0, -0.56))
    it.add("Head", "mustard", head)
    it.add("Lens", (255, 244, 210), zcyl(0.23, -0.8, -0.76, 10), material="SmoothPlastic")
    it.add("Switch", "red", G.box(0.1, 0.06, 0.18, (0, 0.17, -0.05)))
    return it


def fire_extinguisher():
    it = Item("FireExtinguisher", desc="held by the top lever")
    body = lathe([(0, -2.05), (0.36, -2.05), (0.4, -1.95), (0.4, -0.75), (0.32, -0.52), (0.14, -0.42), (0, -0.4)], 12)
    it.add("Body", "red", body)
    valve = ycyl(0.12, -0.45, -0.18, 8)
    valve.add(G.box(0.3, 0.14, 0.2, (0, -0.12, 0)))
    it.add("Valve", "steel", valve, material="Metal")
    lever = G.box(0.12, 0.08, 0.8, (0, 0.0, 0.32)).xf(RX(-8))
    lever.add(G.box(0.12, 0.06, 0.6, (0, -0.24, 0.26)))
    hose = G.tube([(0, -0.15, -0.12), (0, -0.25, -0.45), (0.05, -0.9, -0.48), (0.08, -1.5, -0.45)], 0.06, 5)
    hose.add(G.frustum(0.07, 0.1, 0.3, 6, "y", (0.08, -1.62, -0.45)))
    it.add("Hose", "black", G.Geo().add([lever, hose]))
    it.add("Label", "white", G.ring(0.415, 0.395, 0.5, 12, c=(0, -1.2, 0)))
    return it


def ticket():
    it = Item("Ticket", desc="order slip; the Handle is its top edge (clips to the TicketRail)")
    it.add("Paper", "paper", G.box(0.8, 1.2, 0.02, (0, -0.6, 0)))
    pr = G.Geo()
    for k, w in enumerate((0.5, 0.36, 0.44, 0.3, 0.4)):
        for z in (-0.012, 0.012):
            pr.add(G.box(w, 0.05, 0.006, (-0.25 + w / 2 - 0.0, -0.2 - 0.17 * k, z)))
    it.add("Print", "black", pr)
    it.rest_rot = G.rx(-90)        # lies face up
    return it


def cash_stack():
    it = Item("CashStack", desc="banded stack of notes")
    it.add("Notes", (104, 150, 96), G.box(1.2, 0.34, 0.6))
    it.add("Band", "mustard", G.box(0.3, 0.36, 0.62))
    return it


def coin_pile():
    it = Item("CoinPile", desc="small pile of coins")
    gold, silver = G.Geo(), G.Geo()
    spots = [(0, 0, 0), (0.02, 0.06, 0.01), (-0.01, 0.12, 0.0), (0.3, 0, 0.1), (-0.26, 0, 0.16), (0.12, 0, -0.3),
             (-0.2, 0.0, -0.22), (0.3, 0.06, 0.12), (-0.1, 0.18, 0.02)]
    for k, (x, y, z) in enumerate(spots):
        g = G.cyl(0.18, 0.06, 10, "y", (x, y + 0.03, z))
        (silver if k % 3 == 1 else gold).add(g)
    it.add("Coins", "mustard", gold, material="Metal")
    it.add("Silver", "steel", silver, material="Metal")
    return it


# ---------------------------------------------------------------- registry

def all_items():
    out = [dough_ball(), dough_base(), sauce_layer(), cheese_raw(), cheese_melted(), burnt(), cut_lines(),
           pepperoni_slice(), pepperoni_stick(), mushroom_slice(), mushroom(), pepper_ring(), bell_pepper(),
           olive_ring(), olive_jar(), onion_ring(), onion(), pineapple_chunk(), pineapple(), sausage_bit(), sausage(),
           basil_leaf(), basil_pot(),
           rolling_pin(), knife(), pizza_cutter(), ladle(), pizza_peel(), grater(),
           pizza_box_flat(), pizza_box()]
    out += [soda_can(n, c) for n, c in SODA.items()]
    out += [ingredient_crate(), flour_bag(), sauce_can(), cheese_block(), trash_bag(), fuel_can(), flashlight(),
            fire_extinguisher(), ticket(), cash_stack(), coin_pile()]
    return out


ITEMS = None


def get(name):
    global ITEMS
    if ITEMS is None:
        ITEMS = {it.name: it for it in all_items()}
    return ITEMS[name]


# ---------------------------------------------------------------- placing an item model in the scene

HANDLE_SIZE = (0.4, 0.4, 0.4)


def place(sc, parent, item, world, name=None, anchored=True):
    """Build `item` as a Model (Handle + MeshParts welded to it) with its Handle at `world`."""
    m = sc.model(parent, name or item.name)
    h = sc.part(m, "Handle", HANDLE_SIZE, world, "white", material="SmoothPlastic", transparency=1.0,
                anchored=anchored, collide=False, touch=False, query=False, shadow=False, massless=True,
                surfaces="smooth", grid=False)
    m.p["primary"] = h
    parts = {}
    for pname, color, mat, tr, geo in item.parts:
        mp = sc.mesh(m, pname, item.prefix + "__" + pname, geo, world, color, material=mat, transparency=tr,
                     anchored=False, collide=False, touch=True, query=True, massless=True, kind="item",
                     owner=item.name)
        parts[pname] = mp
    for pname, mp in parts.items():
        if any(pname == mm[0] for mm in item.motors):
            continue
        other = item.welded_to.get(pname)
        sc.weld(parts[other] if other else h, mp, item.weld_names.get(pname, "Weld"))
    for pname, mname, hinge in item.motors:
        sc.motor(h, parts[pname], mname, world * hinge)
    for mname, mcf in item.markers:
        mk_ = sc.marker(m, mname, world * mcf)
        mk_.p["anchored"] = False
        sc.weld(h, mk_, "Weld")
    sc.attachment(h, "Rest", world * item.rest())
    for k, v in item.attrs.items():
        sc.attr(m, k, v)
    return m
