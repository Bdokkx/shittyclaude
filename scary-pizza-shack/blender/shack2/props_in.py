"""Prop models for the inside, in the one mesh language (chunky, bevelled, 6..12 sided,
nothing thinner than 0.15). Each is registered with @prop and returns
[(part name, colour, Geo[, mesh options])] in its own space: origin on the surface it stands
on (or the wall it hangs on), +Y up, +Z = its front (towards whoever uses it). Sizes follow
the batch-1 items where the same thing exists as an item (cans, cheese, flour sacks, crates,
dough balls, the hand tools)."""
import math

import numpy as np

import spsgeo as G
from spsgeo import T, RX, RY, RZ, S

from .kit import bevel_box, ccyl, cfrustum, irregular, lathe, prop, rod, slab


def _lathe_loop(loop, n=12):
    g = G.lathe_loop(loop, n)
    g.weld()
    return G.outward(g)


def _cyl_z(r, z0, z1, n=8, b=0.02, x=0.0, y=0.0):
    """A cylinder along Z from z0 to z1 at (x, y)."""
    return ccyl(r, z1 - z0, n, "z", (x, y, (z0 + z1) / 2), b)


def _cyl_y(r, y0, y1, n=10, b=0.05, x=0.0, z=0.0):
    return ccyl(r, y1 - y0, n, "y", (x, (y0 + y1) / 2, z), b)


def _blob(r, scale, seed, c=(0, 0, 0), n=9, rings=5, jitter=0.1, flat=None):
    return G.blob(r, n, rings, scale, jitter, seed, c, flat)


# ---------------------------------------------------------------- the dough station

@prop("FlourBin")
def flour_bin(rng):
    """A white ingredient bin on castors (the kind that rolls under a bench): flour heaped
    inside, a scoop on it; a fixed lid strip at the back and a clear front lid that slides
    back over it (the station makes LidFront + LidGrip its openable Lid)."""
    w, d, h = 1.3, 2.2, 1.6
    body = G.Geo()
    body.add(bevel_box(w, 0.15, d, 0.04, c=(0, 0.3, 0)))                              # floor
    for sx in (-1, 1):
        body.add(bevel_box(0.15, h - 0.2, d, 0.04, c=(sx * (w / 2 - 0.075), 0.2 + (h - 0.2) / 2, 0)))
    for sz in (-1, 1):
        body.add(bevel_box(w, h - 0.2, 0.15, 0.04, c=(0, 0.2 + (h - 0.2) / 2, sz * (d / 2 - 0.075))))
    body.add(bevel_box(w + 0.1, 0.15, d + 0.1, 0.04, c=(0, h - 0.075, 0)).xf(S(1, 1, 1)))     # the rim
    flour = G.outward(G.lathe([(0.0, 0.0), (0.5, 0.0), (0.5, 0.05), (0.3, 0.25), (0.0, 0.32)], 10)).xf(
        S(1.0, 1.0, 1.7)).xf(T(0, 1.05, 0))
    flour.add(bevel_box(w - 0.3, 0.6, d - 0.3, 0.04, c=(0, 0.75, 0)))
    scoop = G.Geo()
    scoop.add(_lathe_loop([(0.0, -0.18), (0.24, -0.16), (0.27, 0.06), (0.2, 0.06), (0.19, -0.08), (0.0, -0.1)], 8))
    scoop.add(rod((0.24, 0.0, 0), (0.55, 0.1, 0), 0.08, 6))
    scoop = scoop.xf(T(-0.1, 1.38, 0.35) @ RY(60))
    rear = bevel_box(w + 0.1, 0.15, 0.8, 0.04, c=(0, h + 0.075, -d / 2 + 0.4))
    front = G.Geo()
    front.add(bevel_box(w + 0.1, 0.15, 1.55, 0.04, c=(0, h + 0.225, d / 2 - 0.725)))
    front.add(bevel_box(w + 0.1, 0.2, 0.15, 0.03, c=(0, h + 0.1, d / 2 + 0.05)))        # its front lip
    grip = bevel_box(0.6, 0.15, 0.2, 0.04, c=(0, h + 0.35, d / 2 - 0.25))
    cast = G.Geo()
    for sx in (-1, 1):
        for sz in (-1, 1):
            cast.add(ccyl(0.12, 0.15, 8, "x", (sx * (w / 2 - 0.2), 0.12, sz * (d / 2 - 0.25)), 0.03))
            cast.add(bevel_box(0.2, 0.15, 0.2, 0.03, c=(sx * (w / 2 - 0.2), 0.245, sz * (d / 2 - 0.25))))
    return [("Bin", "label_white", body), ("Flour", "flour", flour), ("Scoop", "steel", scoop),
            ("LidRear", "label_white", rear), ("LidFront", "glass", front, {"material": "Glass", "transparency": 0.35}),
            ("LidGrip", "label_blue", grip), ("Castors", "black", cast)]


@prop("Scale")
def kitchen_scale(rng):
    """Spring kitchen scale: red body, white dial face, steel pan."""
    body = bevel_box(1.1, 0.8, 0.9, 0.12, c=(0, 0.4, 0))
    face = ccyl(0.36, 0.15, 12, "z", (0, 0.42, 0.47), 0.03)
    needle = bevel_box(0.08, 0.3, 0.15, 0.02, c=(0.05, 0.5, 0.56)).xf(RZ(-25))
    stem = _cyl_y(0.1, 0.8, 0.95, 6)
    pan = _lathe_loop([(0.0, 0.95), (0.62, 0.98), (0.72, 1.12), (0.64, 1.12), (0.56, 1.04), (0.0, 1.03)], 12)
    return [("Body", "red", body), ("Face", "paper", face), ("Needle", "black", needle), ("Stem", "steel_dark", stem),
            ("Pan", "steel", pan)]


@prop("DoughTray")
def dough_tray(rng):
    """A stack of two blue proofing trays, dough balls in the top one."""
    g = G.Geo()
    for k in range(2):
        y = k * 0.5
        g.add(bevel_box(3.0, 0.5, 2.0, 0.08, c=(0, y + 0.25, 0)))
    balls = G.Geo()
    for i, (x, z) in enumerate(((-0.95, -0.45), (0.0, -0.45), (0.95, -0.45), (-0.95, 0.45), (0.0, 0.45))):
        balls.add(_blob(0.42, (1.0, 0.62, 1.0), i + 3, c=(x, 1.0, z), flat=-0.05))
    rim = G.Geo()
    for k in range(2):
        rim.add(bevel_box(3.1, 0.15, 2.1, 0.04, c=(0, k * 0.5 + 0.5 - 0.075, 0)))
    return [("Trays", "label_blue", g), ("Rims", (40, 72, 120), rim), ("Dough", "dough", balls)]


@prop("Scraper")
def bench_scraper(rng):
    """Bench scraper lying flat: steel blade, wooden grip."""
    blade = bevel_box(0.9, 0.15, 0.7, 0.03, c=(0, 0.075, 0))
    grip = ccyl(0.12, 0.95, 8, "x", (0, 0.27, 0.32), 0.04)
    return [("Blade", "steel", blade), ("Grip", "wood", grip)]


@prop("FlourDust")
def flour_dust(rng):
    """Flour spilt on a board: a thin irregular sheet and a few tiny heaps."""
    g = G.Geo()
    for k in range(5):
        pts = irregular(rng, rng.uniform(0.3, 0.7), 8, 0.35)
        cx, cz = rng.uniform(-1.1, 1.1), rng.uniform(-0.9, 0.9)
        # each patch a hair higher than the last: no two tops coplanar
        g.add(G.slab_poly([(x + cx, z + cz) for x, z in pts], 0.15, (0, -0.12 + 0.012 * k, 0)))
    for k in range(4):
        cx, cz = rng.uniform(-1.2, 1.2), rng.uniform(-1.0, 1.0)
        g.add(_blob(0.18, (1.0, 0.55, 1.0), 40 + k, c=(cx, 0.02, cz), flat=0.0))
    return [("Flour", "flour", g)]


@prop("WallShelf")
def wall_shelf(rng):
    """A 4-wide, 1.8-deep wooden wall shelf on two steel brackets (origin at the wall, +Z out;
    the shelf's top at y 0.15)."""
    board = bevel_box(4.0, 0.3, 1.8, 0.06, c=(0, 0, 0.9))
    br = G.Geo()
    for x in (-1.5, 1.5):
        br.add(G.extrude([(0, 0), (1.5, 0), (0.15, -0.6), (0, -0.6)], 0.2, "x", (x, -0.15, 0)))
    return [("Board", "wood", board), ("Brackets", "steel_dark", br)]


@prop("PinRack")
def pin_rack(rng):
    """Wall shelf for the rolling pin: a board on two brackets (origin at the wall, +Z out)."""
    board = bevel_box(3.6, 0.3, 1.0, 0.06, c=(0, 0, 0.5))
    br = G.Geo()
    for x in (-1.68, 1.68):                                  # outside the tray stack under it
        br.add(G.extrude([(0, 0), (0.8, 0), (0, -0.8)], 0.2, "x", (x, -0.15, 0)).xf(T(0, 0, 0)))
    lip = bevel_box(3.6, 0.3, 0.15, 0.04, c=(0, 0.25, 0.92))
    return [("Board", "wood", board), ("Brackets", "wood_dark", br), ("Lip", "wood", lip)]


# ---------------------------------------------------------------- the sauce and cheese station

@prop("Burner")
def gas_ring(rng):
    """Cast-iron gas ring on a stand, its pilot glowing faintly blue."""
    base = bevel_box(1.9, 0.3, 1.9, 0.08, c=(0, 0.15, 0))
    legs = G.Geo()
    ring_ = G.torus(0.58, 0.12, 12, 6, "y", (0, 0.42, 0))
    for a in range(4):
        t = math.pi / 4 + a * math.pi / 2
        legs.add(rod((0.55 * math.cos(t), 0.3, 0.55 * math.sin(t)), (0.86 * math.cos(t), 0.55, 0.86 * math.sin(t)),
                     0.08, 4))
    knob = ccyl(0.18, 0.2, 8, "x", (1.05, 0.15, 0.5), 0.04)
    return [("Base", "charcoal", base), ("Ring", "black", ring_), ("PanSupports", "black", legs),
            ("Knob", "black", knob)]


@prop("StockPot")
def stock_pot(rng):
    """Big dented stock pot of tomato sauce with two side handles and a lid tipped against it."""
    pot = _lathe_loop([(0.0, 0.0), (0.76, 0.0), (0.84, 0.08), (0.84, 1.55), (0.9, 1.62), (0.78, 1.62), (0.74, 1.5),
                       (0.74, 0.12), (0.0, 0.12)], 14)
    for sx in (-1, 1):
        pot.add(G.torus(0.2, 0.075, 8, 4, "z", (sx * 0.98, 1.3, 0)))
    sauce = G.outward(G.lathe([(0, 1.24), (0.75, 1.24), (0.75, 1.32), (0.3, 1.38), (0, 1.36)], 14))
    drip = G.Geo()
    for a in (0.6, 2.1):
        drip.add(bevel_box(0.18, 0.5, 0.15, 0.04, c=(0.86 * math.cos(a), 1.3, 0.86 * math.sin(a))).xf(T(0, 0, 0)))
    return [("Pot", "steel", pot), ("Sauce", "sauce", sauce), ("Drips", "sauce", drip)]


@prop("LadleRest")
def ladle_rest(rng):
    """A steel spoon rest by the pot, sauce-stained."""
    dish = _lathe_loop([(0.0, 0.0), (0.42, 0.0), (0.48, 0.18), (0.4, 0.18), (0.36, 0.06), (0.0, 0.06)], 10)
    dish = dish.xf(S(1.0, 1.0, 1.6))
    stain = G.outward(G.lathe([(0, 0.06), (0.3, 0.06), (0.22, 0.11), (0, 0.12)], 10)).xf(S(1.0, 1.0, 1.5))
    return [("Dish", "steel", dish), ("Stain", "sauce", stain)]


def _can(label_col, rng, open_=False, h=1.3, r=0.5):
    can = _lathe_loop([(0.0, 0.0), (r - 0.04, 0.0), (r, 0.05), (r, h - 0.05), (r - 0.04, h), (0.0, h)], 12)
    label = G.ring(r + 0.02, r - 0.05, h * 0.62, 12, c=(0, h * 0.5, 0))
    ribs = G.Geo()
    for y in (0.15, h - 0.15):
        ribs.add(G.torus(r + 0.01, 0.075, 12, 4, "y", (0, y, 0)))
    parts = [("Can", "steel", can), ("Label", label_col, label), ("Ribs", "steel_dark", ribs)]
    if open_:
        parts.append(("Sauce", "sauce", G.outward(G.lathe([(0, h - 0.2), (r - 0.06, h - 0.2), (r - 0.06, h - 0.1),
                                                            (0, h - 0.08)], 12))))
        lid = ccyl(r - 0.02, 0.15, 12, "y", (0, 0, 0), 0.03).xf(T(r * 0.6, h + 0.25, -r * 0.3) @ RZ(70))
        parts.append(("Lid", "steel_light", lid))
    return parts


@prop("TomatoCan")
def tomato_can(rng):
    return _can("tomato", rng)


@prop("TomatoCanOpen")
def tomato_can_open(rng):
    return _can("tomato", rng, open_=True)


@prop("CanStack")
def can_stack(rng):
    """Three cans in a pyramid (two labels: tomato, and a yellow 'pizza sauce')."""
    out = []
    for i, (x, y, z, c) in enumerate(((-0.52, 0, 0, "tomato"), (0.52, 0, 0.05, "label_yellow"),
                                       (0.0, 1.32, 0.02, "tomato"))):
        for (n, cc, g) in _can(c, rng):
            out.append(("%s%d" % (n, i), cc, g.xf(T(x, y, z) @ RY(rng.uniform(-30, 30)))))
    return out


@prop("SpiceRack")
def spice_rack(rng):
    """Wooden wall rack, two rails, ten jars with coloured lids and contents (origin at the wall)."""
    frame = G.Geo()
    for sx in (-1, 1):
        frame.add(bevel_box(0.2, 2.4, 0.8, 0.05, c=(sx * 1.6, 1.2, 0.4)))
    for y in (0.0, 1.2):
        frame.add(bevel_box(3.4, 0.2, 0.8, 0.05, c=(0, y + 0.1, 0.4)))
        frame.add(bevel_box(3.4, 0.2, 0.15, 0.04, c=(0, y + 0.55, 0.78)))
    jars, lids, fill = G.Geo(), G.Geo(), [G.Geo(), G.Geo(), G.Geo()]
    for row, y in enumerate((0.2, 1.4)):
        for i in range(5):
            x = -1.2 + 0.6 * i
            jars.add(_lathe_loop([(0.0, 0.0), (0.22, 0.0), (0.24, 0.04), (0.24, 0.62), (0.18, 0.7), (0.0, 0.7)], 8)
                     .xf(T(x, y, 0.4)))
            lids.add(_cyl_y(0.2, y + 0.7, y + 0.85, 8, x=x, z=0.4))
            fill[(i + row) % 3].add(_cyl_y(0.2, y + 0.04, y + 0.04 + rng.uniform(0.25, 0.55), 8, x=x, z=0.4))
    return [("Frame", "wood", frame), ("Jars", "glass", jars, dict(transparency=0.35, material="Glass")),
            ("Lids", "red", lids), ("Oregano", (96, 110, 50), fill[0]), ("Chilli", (170, 52, 30), fill[1]),
            ("Garlic", (226, 214, 180), fill[2])]


@prop("CheeseWheel")
def cheese_wheel(rng):
    """A wheel of cheese with a wedge cut out, on its paper, the wedge lying beside it."""
    R, H, cut = 0.75, 0.75, 0.75
    angs = [cut + (2 * math.pi - cut) * i / 14 for i in range(15)]
    wheel = G.slab_poly([(0.0, 0.0)] + [(R * math.cos(a), R * math.sin(a)) for a in angs], H)
    rind = G.slab_poly([(0.0, 0.0)] + [(R * 1.02 * math.cos(a), R * 1.02 * math.sin(a)) for a in angs], 0.15,
                       (0, H * 0.45, 0))
    wedge = G.extrude([(0, 0), (R * 0.95, 0), (R * 0.95 * math.cos(cut * 0.8), R * 0.95 * math.sin(cut * 0.8))],
                      0.6, "y", (0, 0.3, 0)).xf(T(0.55, 0.0, 0.35) @ RY(-60))
    paper = G.slab_poly([(-0.95, -0.85), (1.05, -0.9), (1.15, 0.8), (-0.9, 0.9)], 0.15, (0, -0.15, 0))
    return [("Wheel", "cheese", wheel), ("Rind", (214, 160, 60), rind), ("Wedge", "cheese", wedge),
            ("Paper", "paper_old", paper)]


@prop("GraterTray")
def grater_tray(rng):
    """Steel tray with a heap of grated cheese (the Grater item stands on it)."""
    tray = G.Geo()
    tray.add(bevel_box(1.6, 0.15, 1.3, 0.04, c=(0, 0.075, 0)))
    for (cx, cz, sx, sz) in ((0, -0.6, 1.6, 0.15), (0, 0.6, 1.6, 0.15), (-0.75, 0, 0.15, 1.3), (0.75, 0, 0.15, 1.3)):
        tray.add(bevel_box(sx, 0.3, sz, 0.04, c=(cx, 0.15, cz)))
    heap = G.Geo()
    for k in range(4):
        heap.add(_blob(0.22, (1.0, 0.5, 1.0), 60 + k, c=(rng.uniform(-0.55, -0.15), 0.15, rng.uniform(-0.35, 0.35)),
                       flat=0.0))
    return [("Tray", "steel", tray), ("Cheese", "cheese", heap)]


# ---------------------------------------------------------------- the chop station

@prop("KnifeStrip")
def knife_strip(rng):
    """Magnetic knife strip on the wall with five knives of different sizes hanging from it
    (origin at the wall, +Z out). The Knife item is the second from the left."""
    bar = bevel_box(3.6, 0.5, 0.3, 0.08, c=(0, 0, 0.15))
    screws = G.Geo()
    for x in (-1.6, 1.6):
        screws.add(ccyl(0.1, 0.15, 6, "z", (x, 0, 0.33), 0.02))
    blades, grips = G.Geo(), G.Geo()
    # (x, blade length, blade width, grip length) -- cleaver, chef (=item size), utility, bread, paring
    for x, bl, bw, gl, shape in ((-1.3, 0.9, 0.7, 0.55, "cleaver"), (-0.4, 0.85, 0.32, 0.6, "chef"),
                                 (0.35, 0.7, 0.24, 0.5, "chef"), (1.05, 1.05, 0.26, 0.55, "bread"),
                                 (1.6, 0.45, 0.2, 0.45, "chef")):
        z = 0.38
        if shape == "cleaver":
            blades.add(bevel_box(bw, bl, 0.15, 0.03, c=(x, -bl / 2 + 0.2, z)))
        else:
            pts = [(-bw / 2, 0.2), (bw / 2, 0.2), (bw / 2, 0.2 - bl * 0.75), (0.0, 0.2 - bl), (-bw / 2, 0.2 - bl * 0.7)]
            blades.add(G.extrude(pts, 0.15, "z", (x, 0, z)))
        grips.add(bevel_box(0.22, gl, 0.22, 0.06, c=(x, 0.2 + gl / 2 + 0.05, z)))
    return [("Strip", "black", bar), ("Screws", "steel", screws), ("Blades", "steel_light", blades),
            ("Grips", "wood_dark", grips)]


@prop("ChopBoard")
def chop_board(rng):
    """Thick end-grain board with a juice groove round the edge and a handle hole."""
    W, D, H = 3.4, 3.0, 0.4
    g = G.Geo()
    # body in four strips round the hole (the hole is a gap between them at one end)
    g.add(bevel_box(W, H, D - 0.9, 0.08, c=(0, H / 2, -0.45)))
    g.add(bevel_box(W, H, 0.3, 0.06, c=(0, H / 2, D / 2 - 0.15)))
    g.add(bevel_box(W / 2 - 0.4, H, 0.62, 0.06, c=(-(W / 4 + 0.2), H / 2, D / 2 - 0.6)))
    g.add(bevel_box(W / 2 - 0.4, H, 0.62, 0.06, c=((W / 4 + 0.2), H / 2, D / 2 - 0.6)))
    groove = G.Geo()
    for (cx, cz, sx, sz) in ((0, -D / 2 + 0.3, W - 0.5, 0.15), (-W / 2 + 0.25, -0.4, 0.15, D - 1.4),
                             (W / 2 - 0.25, -0.4, 0.15, D - 1.4)):
        groove.add(bevel_box(sx, 0.15, sz, 0.03, c=(cx, H - 0.06, cz)))
    return [("Board", "wood_light", g), ("Groove", "wood", groove)]


@prop("BoardUpright")
def board_upright(rng):
    """A spare board stood on edge against the backsplash (origin on the counter at the wall)."""
    b = bevel_box(2.8, 2.0, 0.3, 0.08).xf(T(0, 1.0, 0.0))
    hole = ccyl(0.2, 0.32, 8, "z", (0.0, 1.6, 0.0), 0.02)
    return [("Board", "wood", b.xf(RX(-5))), ("Hole", "cab_inside", hole.xf(RX(-5)))]


@prop("VegCrate")
def veg_crate(rng):
    """Slatted wooden crate of peppers, onions and mushrooms."""
    W, H, D = 2.2, 1.1, 1.5
    slats = G.Geo()
    for y in (0.25, 0.75):
        for z in (-D / 2 + 0.08, D / 2 - 0.08):
            slats.add(bevel_box(W, 0.35, 0.15, 0.04, c=(0, y, z)))
        for x in (-W / 2 + 0.08, W / 2 - 0.08):
            slats.add(bevel_box(0.15, 0.35, D, 0.04, c=(x, y, 0)))
    posts = G.Geo()
    for x in (-W / 2 + 0.15, W / 2 - 0.15):
        for z in (-D / 2 + 0.15, D / 2 - 0.15):
            posts.add(bevel_box(0.3, H, 0.3, 0.05, c=(x, H / 2, z)))
    posts.add(bevel_box(W - 0.2, 0.15, D - 0.2, 0.03, c=(0, 0.08, 0)))
    peppers, onions, mush = G.Geo(), G.Geo(), G.Geo()
    for i in range(4):
        peppers.add(_blob(0.36, (1.0, 1.1, 1.0), 70 + i, c=(-0.6 + 0.4 * (i % 2), 1.0, -0.35 + 0.6 * (i // 2))))
    for i in range(3):
        onions.add(_blob(0.34, (1.0, 1.0, 1.0), 80 + i, c=(0.45 + 0.1 * i, 0.95 + 0.12 * (i % 2), -0.4 + 0.4 * i)))
    for i in range(3):
        mush.add(G.outward(G.lathe([(0.0, 0.0), (0.12, 0.0), (0.12, 0.15), (0.3, 0.18), (0.26, 0.3), (0.0, 0.36)], 8))
                 .xf(T(0.0 + 0.3 * i, 1.0, 0.45)))
    return [("Slats", "wood_pale", slats), ("Posts", "wood", posts), ("Peppers", "pepper", peppers),
            ("Onions", (196, 150, 110), onions), ("Mushrooms", (222, 210, 190), mush)]


# ---------------------------------------------------------------- the topping rail

@prop("Tongs")
def tongs(rng):
    g = G.Geo()
    g.add(rod((0, 0.1, 0), (-0.2, 0.12, -1.1), 0.075, 4))
    g.add(rod((0, 0.1, 0), (0.2, 0.12, -1.1), 0.075, 4))
    g.add(G.torus(0.14, 0.075, 8, 4, "x", (0, 0.1, 0.1)))
    return [("Tongs", "steel_light", g)]


# ---------------------------------------------------------------- the fridge's stock

@prop("TubStack")
def tub_stack(rng):
    """Deli tubs with coloured lids, stacked two and three high."""
    tubs, lids = G.Geo(), G.Geo()
    for i, (x, z, n) in enumerate(((-0.5, 0.0, 3), (0.5, 0.1, 2))):
        for j in range(n):
            y = j * 0.62
            tubs.add(_lathe_loop([(0, y), (0.38, y), (0.44, y + 0.5), (0, y + 0.5)], 10).xf(T(x, 0, z)))
            lids.add(_cyl_y(0.47, y + 0.5, y + 0.62, 10, x=x, z=z))
    return [("Tubs", (230, 226, 214), tubs), ("Lids", "label_blue", lids)]


@prop("MilkCrate")
def milk_crate(rng):
    """A blue plastic crate with slotted sides holding a row of capped bottles."""
    crate = G.Geo()
    crate.add(bevel_box(1.6, 0.15, 1.0, 0.04, c=(0, 0.075, 0)))
    for sz in (-1, 1):
        for y in (0.3, 0.75):
            crate.add(bevel_box(1.6, 0.2, 0.15, 0.04, c=(0, y, sz * 0.425)))
    for sx in (-1, 1):
        for y in (0.3, 0.75):
            crate.add(bevel_box(0.15, 0.2, 1.0, 0.04, c=(sx * 0.725, y, 0)))
    for sx in (-1, 0, 1):
        for sz in (-1, 1):
            crate.add(bevel_box(0.15, 0.85, 0.15, 0.03, c=(sx * 0.725, 0.425, sz * 0.425)))
    bottles, caps = G.Geo(), G.Geo()
    for i in range(3):
        x = -0.45 + 0.45 * i
        for z in (-0.2, 0.2):
            bottles.add(_lathe_loop([(0, 0.15), (0.16, 0.15), (0.18, 0.7), (0.1, 0.9), (0, 0.9)], 8).xf(T(x, 0, z)))
            caps.add(_cyl_y(0.09, 0.9, 1.0, 8, x=x, z=z))
    return [("Crate", "crate_blue", crate), ("Bottles", "tub_white", bottles), ("Caps", "red", caps)]


@prop("SauceTub")
def sauce_tub(rng):
    """A catering tub of sauce: white tub, coloured lid, a printed label band."""
    lid = "tub_lid_red" if rng.random() < 0.6 else "tub_lid_green"
    tub = _lathe_loop([(0, 0), (0.38, 0), (0.46, 0.7), (0, 0.7)], 10)
    cap = _cyl_y(0.5, 0.7, 0.85, 10)
    band = _lathe_loop([(0.4, 0.2), (0.43, 0.2), (0.45, 0.5), (0.42, 0.5)], 10)
    return [("Tub", "tub_white", tub), ("Lid", lid, cap), ("Label", "paper_old", band)]


@prop("JarRow")
def jar_row(rng):
    """Three big glass jars in a row (pickles, olives, peppers) with coloured lids, along X."""
    jars, lids, fills = G.Geo(), G.Geo(), {}
    cols = ("pickle", "olive", "pepper_red")
    for i, x in enumerate((-0.5, 0.0, 0.5)):
        h = (0.62, 0.55, 0.66)[i]
        jars.add(_lathe_loop([(0, 0), (0.2, 0), (0.22, 0.08), (0.22, h - 0.12), (0.16, h - 0.05), (0, h - 0.05)],
                             10).xf(T(x, 0, 0)))
        fills.setdefault(cols[i], G.Geo()).add(_cyl_y(0.17, 0.06, h - 0.2, 8, x=x))
        lids.add(_cyl_y(0.18, h - 0.06, h + 0.06, 8, x=x))
    out = [("Jars", "glass", jars, {"material": "Glass", "transparency": 0.45})]
    for c, g in fills.items():
        out.append(("Fill_" + c, c, g))
    out.append(("Lids", "red_dark", lids))
    return out


@prop("SackPile")
def sack_pile(rng):
    """Two paper sacks of flour lying one on the other, tied necks, printed bands; along Z."""
    sacks, bands, ties = G.Geo(), G.Geo(), G.Geo()
    for i, (y, a) in enumerate(((0.0, 4.0), (0.48, -7.0))):
        R = RY(a)
        sacks.add(bevel_box(0.7, 0.5, 1.3, 0.16, c=(0, y + 0.25, 0)).xf(R))
        bands.add(bevel_box(0.72, 0.18, 0.4, 0.04, c=(0, y + 0.3, -0.1)).xf(R))
        ties.add(_cyl_y(0.12, 0.0, 0.3, 6).xf(RX(90)).xf(T(0, y + 0.25, 0.6)).xf(R))
    return [("Sacks", "paper_old", sacks), ("Bands", "red", bands), ("Ties", "cardboard_dark", ties)]


@prop("CheeseLog")
def cheese_log(rng):
    """Wrapped block of cheese (the CheeseBlock item's size) in yellow film."""
    b = bevel_box(1.6, 0.9, 1.1, 0.15, c=(0, 0.45, 0))
    band = bevel_box(1.65, 0.3, 1.15, 0.05, c=(0, 0.45, 0))
    return [("Block", "cheese", b), ("Label", "label_white", band)]


@prop("SquirtBottle")
def squirt_bottle(rng):
    b = _lathe_loop([(0, 0), (0.28, 0), (0.3, 0.9), (0.2, 1.05), (0.08, 1.2), (0.08, 1.4), (0, 1.45)], 8)
    return [("Bottle", "sauce", b)]


@prop("DoughBallTray")
def dough_ball_tray(rng):
    """One low tray of six dough balls (DoughBall item size) under film."""
    tray = bevel_box(3.0, 0.4, 2.2, 0.08, c=(0, 0.2, 0))
    balls = G.Geo()
    for i in range(6):
        balls.add(_blob(0.5, (1.0, 0.6, 1.0), 90 + i, c=(-1.0 + 1.0 * (i % 3), 0.45, -0.5 + 1.0 * (i // 3)), flat=-0.1))
    return [("Tray", (210, 200, 180), tray), ("Dough", "dough", balls)]


# ---------------------------------------------------------------- doors, walls, signs

@prop("DoorMat")
def door_mat(rng):
    """Coir mat, its border dark and worn."""
    mat = bevel_box(3.4, 0.15, 2.0, 0.05, c=(0, 0.075, 0))
    border = G.Geo()
    for (cx, cz, sx, sz) in ((0, -0.9, 3.4, 0.25), (0, 0.9, 3.4, 0.25), (-1.6, 0, 0.25, 2.0), (1.6, 0, 0.25, 2.0)):
        border.add(bevel_box(sx, 0.17, sz, 0.04, c=(cx, 0.085, cz)))
    return [("Mat", (150, 112, 70), mat), ("Border", (84, 62, 44), border)]


@prop("Apron")
def apron(rng):
    """A red striped apron hanging from a hook (origin at the hook on the wall, +Z out)."""
    bib = G.extrude([(-0.45, 0), (0.45, 0), (0.55, -1.0), (0.75, -1.05), (0.7, -2.6), (-0.7, -2.6), (-0.75, -1.05),
                     (-0.55, -1.0)], 0.15, "z", (0, -0.15, 0.2))
    strap = G.Geo()
    strap.add(rod((-0.4, -0.1, 0.22), (0, 0.15, 0.22), 0.075, 4))
    strap.add(rod((0.4, -0.1, 0.22), (0, 0.15, 0.22), 0.075, 4))
    stripe = bevel_box(1.42, 0.25, 0.17, 0.03, c=(0, -1.6, 0.21))
    return [("Apron", "red", bib), ("Strap", "red_dark", strap), ("Stripe", "cream", stripe)]


@prop("CoatHooks")
def coat_hooks(rng):
    """A short board with two steel hooks 0.8 apart (origin at the wall, +Z out)."""
    b = bevel_box(1.5, 0.4, 0.2, 0.05, c=(0, 0, 0.1))
    h = G.Geo()
    for x in (-0.4, 0.4):
        h.add(G.tube([(x, 0, 0.2), (x, 0, 0.45), (x, 0.2, 0.55)], 0.075, 5))
    return [("Board", "wood_dark", b), ("Hooks", "steel_dark", h)]


@prop("TeaTowel")
def tea_towel(rng):
    """A striped tea towel folded over a hook (origin at the hook on the wall, +Z out)."""
    cloth = G.Geo()
    cloth.add(bevel_box(0.6, 1.5, 0.15, 0.04, c=(0, -0.65, 0.25)))
    cloth.add(bevel_box(0.6, 0.6, 0.15, 0.04, c=(0, -0.2, 0.42)))
    stripes = G.Geo()
    for y in (-0.95, -1.15):
        stripes.add(bevel_box(0.62, 0.12, 0.17, 0.02, c=(0, y, 0.25)))
    return [("Cloth", "cream", cloth), ("Stripes", "label_blue", stripes)]


@prop("FridgeDial")
def fridge_dial(rng):
    """A round thermometer on the fridge header (origin on the face, +Z out)."""
    rim = G.torus(0.32, 0.075, 12, 4, "z", (0, 0, 0.08))
    face = ccyl(0.3, 0.15, 12, "z", (0, 0, 0.075), 0.02)
    needle = bevel_box(0.06, 0.22, 0.15, 0.01, c=(0.04, 0.08, 0.16)).xf(RZ(20))
    return [("Rim", "steel_light", rim), ("Face", "paper", face), ("Needle", "red", needle)]


@prop("Socket")
def socket(rng):
    """A double wall socket (origin on the wall, +Z out)."""
    plate = bevel_box(1.0, 0.6, 0.15, 0.04, c=(0, 0, 0.075))
    holes = G.Geo()
    for x in (-0.25, 0.25):
        holes.add(bevel_box(0.2, 0.2, 0.15, 0.02, c=(x, 0, 0.1)))
    return [("Plate", "cream", plate), ("Switches", "cream_dark", holes)]


@prop("JunctionBox")
def junction_box(rng):
    """A square steel junction box where the conduit ends (origin on the wall, +Z out)."""
    box = bevel_box(0.7, 0.7, 0.3, 0.05, c=(0, 0, 0.15))
    lid = bevel_box(0.55, 0.55, 0.06, 0.02, c=(0, 0, 0.32))
    screws = G.Geo()
    for x in (-0.2, 0.2):
        for y in (-0.2, 0.2):
            screws.add(_cyl_z(0.075, 0.33, 0.38, 6, x=x, y=y))
    return [("Box", "steel_dark", box), ("Lid", "grey", lid), ("Screws", "steel_light", screws)]


@prop("LightSwitch")
def light_switch(rng):
    plate = bevel_box(0.6, 0.8, 0.15, 0.04, c=(0, 0, 0.075))
    rocker = bevel_box(0.2, 0.32, 0.15, 0.03, c=(0, 0.04, 0.17)).xf(RX(-10))
    return [("Plate", "cream", plate), ("Rocker", "cream_dark", rocker)]


# ---------------------------------------------------------------- the oven corner

@prop("OvenDial")
def oven_dial(rng):
    """Big oven thermometer on the breast: chrome rim, cream face with a red zone, needle."""
    rim = G.torus(0.62, 0.1, 14, 4, "z", (0, 0, 0.12))
    face = ccyl(0.6, 0.15, 14, "z", (0, 0, 0.075), 0.03)
    zone = G.slab_poly([(0.5 * math.cos(a), 0.5 * math.sin(a)) for a in np.linspace(-0.6, 0.5, 6)] + [(0, 0)],
                       0.15, (0, 0, 0)).xf(RX(90)).xf(T(0, 0, 0.17))
    needle = bevel_box(0.08, 0.5, 0.15, 0.02, c=(0, 0.22, 0.2)).xf(RZ(-35))
    hub = ccyl(0.1, 0.15, 8, "z", (0, 0, 0.24), 0.02)
    return [("Rim", "steel_light", rim), ("Face", "cream", face), ("Zone", "red", zone), ("Needle", "black", needle),
            ("Hub", "steel_dark", hub)]


@prop("OvenBrush")
def oven_brush(rng):
    """Oven brush hanging from a hook: long wooden handle, brass-wire head at the bottom
    (origin at the hook on the wall, +Z out)."""
    hook = G.tube([(0, 0, 0.0), (0, 0, 0.35), (0, 0.2, 0.45)], 0.075, 5)
    pole = rod((0, -0.05, 0.38), (0, -4.6, 0.38), 0.1, 6)
    head = bevel_box(1.2, 0.4, 0.3, 0.06, c=(0, -4.8, 0.38))
    bristles = G.Geo()
    for i in range(6):
        bristles.add(bevel_box(0.15, 0.35, 0.3, 0.03, c=(-0.5 + 0.2 * i, -5.15, 0.38)))
    return [("Hook", "steel_dark", hook), ("Pole", "wood", pole), ("Head", "wood_dark", head),
            ("Bristles", (196, 156, 72), bristles)]


@prop("OvenMitt")
def oven_mitt(rng):
    """A thick quilted mitt hanging by its loop from a hook (origin at the hook, +Z out)."""
    hook = G.tube([(0, 0, 0.0), (0, 0, 0.3), (0, 0.15, 0.38)], 0.075, 5)
    mitt = G.Geo()
    mitt.add(bevel_box(0.75, 1.3, 0.3, 0.12, c=(0, -0.95, 0.35)))
    mitt.add(bevel_box(0.3, 0.55, 0.28, 0.1, c=(0.42, -0.85, 0.35)).xf(T(0.05, 0.1, 0) @ RZ(-20)))
    cuff = bevel_box(0.82, 0.35, 0.34, 0.06, c=(0, -0.3, 0.35))
    loop = G.torus(0.14, 0.075, 8, 4, "z", (0, -0.02, 0.35))
    col_ = ("red", "mustard")[int(rng.integers(0, 2))]
    return [("Hook", "steel_dark", hook), ("Mitt", col_, mitt), ("Cuff", "cream", cuff), ("Loop", "cream", loop)]


@prop("AshBucket")
def ash_bucket(rng):
    """Small galvanised bucket of ash (a rolled rim, a wire handle) with a hand shovel in it."""
    b = _lathe_loop([(0.0, 0.0), (0.34, 0.0), (0.41, 0.8), (0.48, 0.84), (0.48, 0.95), (0.32, 0.95),
                     (0.28, 0.12), (0.0, 0.12)], 12)
    ash = G.outward(G.lathe([(0, 0.66), (0.36, 0.66), (0.26, 0.78), (0, 0.84)], 12))
    handle = G.tube([(-0.48, 0.88, 0), (-0.34, 1.2, 0), (0, 1.32, 0), (0.34, 1.2, 0), (0.48, 0.88, 0)], 0.075, 4)
    shovel = G.Geo()
    shovel.add(bevel_box(0.4, 0.15, 0.45, 0.04, c=(0, 0, 0)).xf(T(0.08, 0.72, 0.06) @ RX(70)))
    shovel.add(rod((0.08, 0.85, 0.0), (0.2, 1.95, -0.32), 0.08, 6))
    return [("Bucket", "steel", b), ("Ash", "ash", ash), ("Handle", "steel_dark", handle),
            ("Shovel", "charcoal", shovel)]


def _peel_geo(head_w, head_d, pole_len, burnt=False):
    """A peel standing head-down: head in the XY plane (bottom edge at y 0), pole above."""
    hw = head_w / 2
    pts = [(-hw + 0.4, 0.0), (hw - 0.4, 0.0), (hw, 0.4), (hw, head_d - 0.3), (0.6, head_d + 0.3),
           (-0.6, head_d + 0.3), (-hw, head_d - 0.3), (-hw, 0.4)]
    head = G.extrude(pts, 0.15, "z", (0, 0, 0))
    pole = rod((0, head_d + 0.2, 0), (0, head_d + 0.3 + pole_len, 0), 0.14, 8)
    knob = G.sphere(0.18, 8, 4, c=(0, head_d + 0.35 + pole_len, 0))
    out = [("Head", "wood_light" if not burnt else "wood", head), ("Pole", "wood_dark", pole),
           ("Knob", "wood_dark", knob)]
    if burnt:
        edge = G.extrude([(-hw + 0.4, -0.01), (hw - 0.4, -0.01), (hw - 0.1, 0.45), (-hw + 0.1, 0.45)], 0.18, "z",
                         (0, 0, 0))
        out.append(("Scorch", "soot", edge))
    return out


@prop("OldPeel")
def old_peel(rng):
    return _peel_geo(3.6, 3.0, 2.0, burnt=True)


@prop("OldPeelSteel")
def old_peel_steel(rng):
    out = _peel_geo(3.4, 2.8, 2.2)
    out[0] = ("Head", "steel", out[0][2])
    return out


# ---------------------------------------------------------------- cut table, bin, boxes

@prop("RoundBoard")
def round_board(rng):
    """Round wooden cutting board, 3.6 across, worn with knife marks, its handle tab."""
    g = ccyl(1.8, 0.4, 14, "y", (0, 0.2, 0), 0.08)
    tab = bevel_box(0.8, 0.4, 0.6, 0.08, c=(-2.05, 0.2, 0))
    marks = G.Geo()
    for i in range(5):
        a = rng.uniform(0, math.pi)
        marks.add(bevel_box(2.2, 0.15, 0.15, 0.03, c=(0, 0.35, 0)).xf(RY(math.degrees(a)) @ T(rng.uniform(-0.3, 0.3),
                                                                                             0.0, 0)))
    return [("Board", "wood", g), ("Tab", "wood", tab), ("Marks", "wood_dark", marks)]


@prop("ToolRail")
def tool_rail(rng):
    """A steel rail with S-hooks on the wall (origin at the wall, +Z out)."""
    rail = rod((-1.6, 0, 0.3), (1.6, 0, 0.3), 0.09, 8)
    for x in (-1.4, 1.4):
        rail.add(bevel_box(0.3, 0.3, 0.3, 0.05, c=(x, 0, 0.15)))
    hooks = G.Geo()
    for x in (-0.9, 0.0, 0.9):
        hooks.add(G.tube([(x, 0.05, 0.3), (x, -0.25, 0.42), (x, -0.45, 0.3)], 0.075, 4))
    return [("Rail", "steel_light", rail), ("Hooks", "steel_dark", hooks)]


@prop("SliceGuide")
def slice_guide(rng):
    """The slice guide: a round plastic template with radial ribs, hung on the wall."""
    disc = ccyl(1.6, 0.15, 16, "z", (0, 0, 0.1), 0.03)
    ribs = G.Geo()
    for i in range(4):
        ribs.add(bevel_box(3.0, 0.15, 0.15, 0.03, c=(0, 0, 0.22)).xf(RZ(45 * i)))
    hub = ccyl(0.25, 0.2, 8, "z", (0, 0, 0.25), 0.04)
    return [("Disc", (230, 230, 220), disc, dict(transparency=0.15)), ("Ribs", "red", ribs), ("Hub", "red_dark", hub)]


@prop("LitterFloor")
def litter_floor(rng):
    """A screwed-up napkin and a dropped receipt by the bin."""
    ball = _blob(0.25, (1.0, 0.8, 1.0), 120, c=(0, 0.2, 0), flat=-0.15)
    slip = bevel_box(0.5, 0.15, 0.8, 0.03, c=(0.6, 0.075, 0.3)).xf(RY(30))
    return [("Napkin", "paper", ball), ("Receipt", "paper_old", slip)]


def _flat_boxes(rng, n, assembled_top=0):
    g, edges, prints = G.Geo(), G.Geo(), G.Geo()
    y = 0.0
    for i in range(n):
        a = rng.uniform(-1.5, 1.5)                       # squared up: the stack fills its bay
        dx, dz = rng.uniform(-0.05, 0.05), rng.uniform(-0.05, 0.05)
        g.add(bevel_box(3.6, 0.15, 3.6, 0.03, c=(dx, y + 0.075, dz)).xf(RY(a)))
        y += 0.17
    for i in range(assembled_top):
        a = 0.0
        g.add(bevel_box(3.6, 0.7, 3.6, 0.08, c=(0, y + 0.35, 0)).xf(RY(a)))
        edges.add(bevel_box(3.64, 0.15, 3.64, 0.03, c=(0, y + 0.62, 0)).xf(RY(a)))
        prints.add(ccyl(1.2, 0.15, 12, "y", (0, y + 0.72, 0), 0.03).xf(RY(a)))
        y += 0.72
    out = [("Boxes", "cardboard", g)]
    if assembled_top:
        out += [("Lids", "cardboard_dark", edges), ("Print", "red", prints)]
    return out


@prop("FlatBoxStack")
def flat_box_stack(rng):
    """Seven flat boxes and a folded one on top (the PAPA STUD'S print on its lid; the
    station puts the name on its side as a Board)."""
    return _flat_boxes(rng, 7, assembled_top=1)


@prop("StickerRoll")
def sticker_roll(rng):
    """A roll of red PAPA STUD'S stickers on a little dispenser."""
    base = bevel_box(0.9, 0.3, 0.6, 0.06, c=(0, 0.15, 0))
    arms = G.Geo()
    for x in (-0.35, 0.35):
        arms.add(bevel_box(0.15, 0.6, 0.4, 0.04, c=(x, 0.5, 0)))
    roll = ccyl(0.38, 0.55, 12, "x", (0, 0.7, 0), 0.04)
    core = ccyl(0.15, 0.6, 8, "x", (0, 0.7, 0), 0.02)
    tail = bevel_box(0.5, 0.15, 0.5, 0.03, c=(0, 0.33, 0.45)).xf(RX(-25))
    return [("Base", "charcoal", base), ("Arms", "charcoal", arms), ("Roll", "red", roll), ("Core", "cream", core),
            ("Tail", "red", tail)]


# ---------------------------------------------------------------- the window counter and till

@prop("CardImprinter")
def card_imprinter(rng):
    """A manual card imprinter (the 1986 'zip-zap'): a flat steel bed with its sliding handle."""
    bed = bevel_box(1.6, 0.3, 1.0, 0.06, c=(0, 0.15, 0))
    rail = bevel_box(1.5, 0.15, 0.15, 0.03, c=(0, 0.37, -0.35))
    slider = bevel_box(0.4, 0.3, 0.9, 0.06, c=(0.4, 0.45, 0))
    knob = ccyl(0.12, 0.3, 8, "y", (0.4, 0.75, 0.3), 0.03)
    return [("Bed", "steel", bed), ("Rail", "steel_dark", rail), ("Slider", "charcoal", slider),
            ("Knob", "black", knob)]


@prop("NapkinBox")
def napkin_box(rng):
    """A chrome napkin dispenser with paper napkins showing."""
    body = bevel_box(1.0, 0.9, 0.6, 0.12, c=(0, 0.45, 0))
    nap = bevel_box(0.75, 0.15, 0.5, 0.03, c=(0, 0.95, 0))
    face = bevel_box(0.75, 0.6, 0.15, 0.03, c=(0, 0.45, 0.31))
    return [("Body", "steel_light", body), ("Napkins", "paper", nap), ("Napkin", "paper", face)]


@prop("PenOnChain")
def pen_on_chain(rng):
    """A pen on a bead chain, the chain screwed to the counter."""
    base = ccyl(0.15, 0.15, 6, "y", (0, 0.075, 0), 0.03)
    chain = G.Geo()
    pts = [(0, 0.15, 0), (0.25, 0.08, 0.15), (0.55, 0.08, 0.2), (0.8, 0.1, 0.1)]
    for a, b in zip(pts, pts[1:]):
        chain.add(rod(a, b, 0.075, 4))
    pen = rod((0.8, 0.1, 0.1), (1.6, 0.1, -0.15), 0.08, 6)
    cap = rod((1.45, 0.1, -0.1), (1.62, 0.1, -0.16), 0.09, 6)
    return [("Base", "steel_dark", base), ("Chain", "steel_light", chain), ("Pen", "label_blue", pen),
            ("Cap", "black", cap)]


# ---------------------------------------------------------------- the camera desk

@prop("VCRStack")
def vcr_stack(rng):
    """Two VCRs stacked under the left monitor, a tape half in the top one."""
    out = []
    g, slots, leds = G.Geo(), G.Geo(), G.Geo()
    for i in range(2):
        y = 0.6 * i
        g.add(bevel_box(2.6, 0.55, 2.4, 0.06, c=(0, y + 0.3, 0)))
        slots.add(bevel_box(1.2, 0.15, 0.15, 0.03, c=(-0.4, y + 0.38, -1.21)))
        leds.add(bevel_box(0.4, 0.15, 0.15, 0.03, c=(0.8, y + 0.38, -1.21)))
    tape = bevel_box(1.0, 0.15, 0.6, 0.03, c=(-0.4, 0.98, -1.3))
    return [("Bodies", "charcoal", g), ("Slots", "black", slots), ("Clocks", (90, 255, 140), leds),
            ("Tape", "black", tape)]


@prop("Keyboard")
def keyboard(rng):
    body = bevel_box(2.2, 0.3, 0.9, 0.08, c=(0, 0.15, 0)).xf(RX(-4))
    keys = G.Geo()
    for i in range(7):
        for j in range(3):
            keys.add(bevel_box(0.22, 0.15, 0.2, 0.03, c=(-0.9 + 0.3 * i, 0.33 + 0.012 * j, -0.25 + 0.25 * j)))
    return [("Body", "crt_cream", body), ("Keys", "cream_dark", keys)]


@prop("Mug")
def mug(rng):
    """A chipped mug with the dregs of coffee."""
    body = _lathe_loop([(0.0, 0.0), (0.3, 0.0), (0.32, 0.65), (0.25, 0.65), (0.24, 0.08), (0.0, 0.08)], 10)
    handle = G.torus(0.2, 0.075, 8, 4, "z", (0.36, 0.35, 0))
    coffee = _cyl_y(0.24, 0.3, 0.45, 10)
    return [("Mug", "label_white", body), ("Handle", "label_white", handle), ("Coffee", (70, 44, 30), coffee)]


@prop("WallShelfSmall")
def wall_shelf_small(rng):
    board = bevel_box(1.8, 0.3, 1.2, 0.06, c=(0, -0.15, 0.6))
    br = G.Geo()
    for x in (-0.7, 0.7):
        br.add(G.extrude([(0, 0), (1.0, 0), (0.15, -0.8), (0, -0.8)], 0.15, "x", (x, -0.3, 0)))
    return [("Board", "wood", board), ("Brackets", "steel_dark", br)]


@prop("CorkBoard")
def cork_board(rng):
    """Cork board crowded with notes, a yellowed newspaper cutting, a photo, a delivery map,
    pinned with coloured pins (origin at the wall, +Z out)."""
    board_ = bevel_box(2.6, 2.4, 0.2, 0.05, c=(0, 0, 0.1))
    frame = G.Geo()
    for (cx, cy, sx, sy) in ((0, 1.25, 2.8, 0.2), (0, -1.25, 2.8, 0.2), (-1.35, 0, 0.2, 2.6), (1.35, 0, 0.2, 2.6)):
        frame.add(bevel_box(sx, sy, 0.3, 0.05, c=(cx, cy, 0.15)))
    notes = {"paper": G.Geo(), "paper_old": G.Geo(), "label_yellow": G.Geo(), (150, 200, 230): G.Geo()}
    pins = G.Geo()
    spots = [(-0.8, 0.6, 0.7, 0.9, "paper_old", -6), (0.2, 0.55, 0.9, 0.7, "paper", 4), (0.9, -0.2, 0.6, 0.6,
             "label_yellow", 9), (-0.6, -0.5, 0.9, 0.7, (150, 200, 230), -3), (0.4, -0.65, 0.5, 0.5, "paper", 12)]
    for (x, y, w, h, c, a) in spots:
        notes[c].add(bevel_box(w, h, 0.15, 0.02, c=(0, 0, 0)).xf(T(x, y, 0.27) @ RZ(a)))
        pins.add(G.sphere(0.1, 6, 3, c=(x, y + h / 2 - 0.12, 0.38)))
    out = [("Cork", "cork", board_), ("Frame", "wood", frame), ("Pins", "red", pins)]
    for i, (c, g) in enumerate(notes.items()):
        out.append(("Note%d" % i, c, g))
    return out


@prop("Calendar")
def calendar(rng):
    """A wall calendar with the days crossed off in red, the page curling (origin at the wall)."""
    page = bevel_box(1.2, 1.6, 0.15, 0.03, c=(0, -0.8, 0.08))
    top = bevel_box(1.2, 0.5, 0.15, 0.03, c=(0, 0.25, 0.1))
    grid = G.Geo()
    crosses = G.Geo()
    for i in range(5):
        for j in range(4):
            x, y = -0.45 + 0.22 * i, -0.35 - 0.3 * j
            grid.add(bevel_box(0.16, 0.2, 0.15, 0.02, c=(x, y, 0.12)))
            if j * 5 + i < 13:
                crosses.add(bevel_box(0.22, 0.15, 0.15, 0.02, c=(x, y, 0.16)).xf(T(0, 0, 0) @ RZ(35)).xf(T(0, 0, 0)))
    nail = ccyl(0.08, 0.2, 6, "z", (0, 0.5, 0.1), 0.02)
    return [("Page", "paper", page), ("Picture", (110, 150, 120), top), ("Days", "paper_old", grid),
            ("Crosses", "red", crosses), ("Nail", "steel_dark", nail)]


@prop("SwivelStool")
def swivel_stool(rng):
    """Swivel stool: five-star base on castors, gas column, round padded seat at 1.6."""
    g = G.Geo()
    for i in range(5):
        a = math.tau * i / 5
        g.add(rod((0, 0.35, 0), (0.95 * math.cos(a), 0.25, 0.95 * math.sin(a)), 0.1, 6))
    castors = G.Geo()
    for i in range(5):
        a = math.tau * i / 5
        castors.add(ccyl(0.12, 0.15, 6, "x", (0.95 * math.cos(a), 0.12, 0.95 * math.sin(a)), 0.03))
    col_ = _cyl_y(0.12, 0.35, 1.3, 8)
    seat = _cyl_y(0.85, 1.3, 1.6, 12, b=0.1)
    return [("Base", "charcoal", g), ("Castors", "black", castors), ("Column", "steel_dark", col_),
            ("Seat", "red_dark", seat)]


# ---------------------------------------------------------------- the sink corner

@prop("MopBucket")
def mop_bucket(rng):
    """A yellow mop bucket with its wringer and the mop stood in it (it lives under the sink)."""
    b = _lathe_loop([(0.0, 0.0), (0.7, 0.0), (0.78, 0.9), (0.84, 0.95), (0.7, 0.95), (0.64, 0.08), (0.0, 0.08)], 10)
    b = b.xf(S(1.2, 1.0, 1.0))
    water = _cyl_y(0.66, 0.55, 0.6, 10).xf(S(1.2, 1.0, 1.0))
    wringer = bevel_box(0.6, 0.4, 0.9, 0.06, c=(0.6, 1.05, 0))
    mop = G.Geo()
    mop.add(rod((-0.3, 0.6, 0.0), (0.25, 1.1, -0.85), 0.08, 6))
    mop.add(_blob(0.35, (1.0, 0.7, 1.0), 140, c=(-0.3, 0.55, 0.0)))
    return [("Bucket", "label_yellow", b), ("Water", (110, 120, 110), water), ("Wringer", "charcoal", wringer),
            ("Mop", "wood_pale", mop)]


@prop("DryingRack")
def drying_rack(rng):
    """A wire drying rack with three plates and a bowl on the draining side of the sink."""
    frame = G.Geo()
    for z in (-0.45, 0.45):
        frame.add(rod((-0.9, 0.15, z), (0.9, 0.15, z), 0.075, 4))
    for x in np.linspace(-0.8, 0.8, 6):
        frame.add(G.tube([(x, 0.15, -0.45), (x, 0.6, -0.45), (x, 0.6, 0.45), (x, 0.15, 0.45)], 0.075, 4))
    plates = G.Geo()
    for i, x in enumerate((-0.5, -0.2, 0.1)):
        plates.add(ccyl(0.5, 0.15, 12, "x", (x, 0.6, 0), 0.03).xf(T(0, 0, 0)))
    bowl = _lathe_loop([(0.0, 0.0), (0.2, 0.0), (0.38, 0.32), (0.32, 0.34), (0.16, 0.08), (0.0, 0.08)], 10)
    return [("Rack", "steel_light", frame), ("Plates", "label_white", plates),
            ("Bowl", "label_blue", bowl.xf(T(0.6, 0.15, 0)))]


@prop("SoapDispenser")
def soap_dispenser(rng):
    body = bevel_box(0.6, 0.9, 0.4, 0.1, c=(0, 0, 0.2))
    window = bevel_box(0.3, 0.4, 0.15, 0.03, c=(0, 0.05, 0.42))
    push = bevel_box(0.4, 0.2, 0.2, 0.05, c=(0, -0.35, 0.45))
    return [("Body", "label_white", body), ("Soap", (230, 140, 170), window), ("Push", "label_blue", push)]


@prop("TowelDispenser")
def towel_dispenser(rng):
    body = bevel_box(1.4, 1.2, 0.6, 0.15, c=(0, 0, 0.3))
    towel = bevel_box(0.9, 0.5, 0.15, 0.03, c=(0, -0.75, 0.45)).xf(RX(10))
    return [("Body", "grey_light", body), ("Towel", "paper", towel)]


@prop("FirstAid")
def first_aid(rng):
    box = bevel_box(1.0, 0.9, 0.4, 0.1, c=(0, 0, 0.2))
    cross = G.Geo()
    cross.add(bevel_box(0.5, 0.15, 0.15, 0.03, c=(0, 0, 0.42)))
    cross.add(bevel_box(0.15, 0.5, 0.15, 0.03, c=(0, 0, 0.42)))
    clasp = bevel_box(0.2, 0.15, 0.15, 0.03, c=(0, -0.38, 0.42))
    return [("Box", "label_white", box), ("Cross", (40, 150, 70), cross), ("Clasp", "steel_dark", clasp)]


# ---------------------------------------------------------------- the west end

@prop("TinRow")
def tin_row(rng):
    """A row of catering tins (the SauceCan item's size) and a jar of olives on the top shelf."""
    out = []
    for i, (z, c) in enumerate(((-1.1, "tomato"), (0.0, "label_yellow"), (1.1, "tomato"))):
        for (n, cc, g) in _can(c, rng):
            out.append(("%s%d" % (n, i), cc, g.xf(T(z, 0, 0))))
    return out


@prop("HairnetBox")
def hairnet_box(rng):
    """A box of hairnets, its lid torn open, a net hanging out."""
    box = bevel_box(1.2, 0.8, 0.9, 0.06, c=(0, 0.4, 0))
    lid = bevel_box(1.2, 0.15, 0.9, 0.04, c=(0, 0.85, -0.5)).xf(T(0, 0.0, 0.0) @ RX(-60)).xf(T(0, 0.35, -0.2))
    net = _blob(0.3, (1.2, 0.5, 1.0), 150, c=(0.2, 0.85, 0.2))
    return [("Box", "label_blue", box), ("Lid", "label_blue", lid), ("Net", (230, 230, 236), net,
                                                                     dict(transparency=0.2))]


@prop("LabelStrip")
def label_strip(rng):
    """Shelf labels: a strip of curling white cards along a shelf edge."""
    g = G.Geo()
    for i in range(4):
        g.add(bevel_box(0.6, 0.35, 0.15, 0.03, c=(-1.2 + 0.8 * i, 0, 0)).xf(RZ(rng.uniform(-6, 6))))
    return [("Labels", "paper", g)]


@prop("CanRowBack")
def can_row_back(rng):
    """Spare soda cans in a row at the back of a cooler shelf (the soda can item's size)."""
    cols = ((200, 32, 36), (240, 132, 30), (96, 190, 64), (130, 60, 160))
    g = {c: G.Geo() for c in cols}
    for i in range(4):
        z = -1.2 + 0.8 * i
        c = cols[(i + int(rng.integers(0, 4))) % 4]
        g[c].add(_lathe_loop([(0, 0), (0.3, 0), (0.37, 0.08), (0.37, 1.1), (0.3, 1.2), (0, 1.2)], 10).xf(T(z, 0, 0)))
    return [("Cans%d" % i, c, gg) for i, (c, gg) in enumerate(g.items()) if gg.f]


@prop("Newspaper")
def newspaper(rng):
    g = bevel_box(1.4, 0.15, 1.0, 0.03, c=(0, 0.075, 0))
    fold = bevel_box(1.4, 0.15, 0.5, 0.03, c=(0, 0.2, -0.2)).xf(RX(8))
    print_ = bevel_box(1.1, 0.15, 0.3, 0.02, c=(0, 0.17, 0.25))
    return [("Paper", "paper_old", g), ("Fold", "paper_old", fold), ("Headline", "charcoal", print_)]


@prop("Broom")
def broom(rng):
    """A broom leaning back into a corner: bristles on the floor, handle up."""
    lean = math.radians(7)
    top = (5.2 * math.sin(lean), 5.2 * math.cos(lean), 0.0)
    head = bevel_box(0.5, 0.4, 1.4, 0.06, c=(0, 0.75, 0))
    bristles = G.Geo()
    for i in range(6):
        bristles.add(bevel_box(0.4, 0.6, 0.18, 0.03, c=(0, 0.3, -0.6 + 0.24 * i)))
    handle = rod((0.05, 0.9, 0), top, 0.1, 6)
    return [("Head", "red", head), ("Bristles", (210, 190, 120), bristles), ("Handle", "wood", handle)]


@prop("CanPair")
def can_pair(rng):
    """Two catering cans stacked, the top one turned."""
    out = []
    for i, (y, c, a) in enumerate(((0.0, "tomato", 0), (1.32, "label_yellow", 35))):
        for (n, cc, g) in _can(c, rng):
            out.append(("%s%d" % (n, i), cc, g.xf(T(0, y, 0) @ RY(a))))
    return out


@prop("TinPair")
def tin_pair(rng):
    """Two small tins of olives and anchovies on the cheese shelf."""
    out = []
    for i, (x, c) in enumerate(((-0.35, (60, 70, 40)), (0.35, "label_blue"))):
        for (n, cc, g) in _can(c, rng, h=0.8, r=0.32):
            out.append(("%s%d" % (n, i), cc, g.xf(T(x, 0, 0))))
    return out


@prop("WallShelf3")
def wall_shelf3(rng):
    """A 3-wide, 1.4-deep wooden wall shelf on two steel brackets (origin at the wall)."""
    board = bevel_box(3.0, 0.3, 1.4, 0.06, c=(0, 0, 0.7))
    br = G.Geo()
    for x in (-1.1, 1.1):
        br.add(G.extrude([(0, 0), (1.2, 0), (0.15, -0.6), (0, -0.6)], 0.2, "x", (x, -0.15, 0)))
    return [("Board", "wood", board), ("Brackets", "steel_dark", br)]
