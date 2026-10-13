"""What is behind the doors: the things in the cupboards and drawers (pans, trays, plates,
tins, rags, cleaning bottles, cartons, a tool box, someone's lunch) and the few worth opening
a door for (one shoe, a mouse trap with the cheese gone). Same mesh language as the rest:
chunky, bevelled, origin on the shelf it stands on, +Z towards the door.

Cupboard things fit a level 1.0 tall (the bottom) or 0.8 (above the shelf); drawer things
lie flat, under 0.35."""
import math

import numpy as np

import spsgeo as G
from spsgeo import T, RX, RY, RZ

from .kit import bevel_box, ccyl, cfrustum, lathe, prop, rod

# ---------------------------------------------------------------- cupboards


@prop("LiddedPot")
def stock_pot(rng):
    """A dented aluminium stock pot with its lid on, two loop handles."""
    body = lathe([(0.0, 0.0), (0.5, 0.0), (0.55, 0.06), (0.55, 0.62), (0.0, 0.62)], 12)
    lid = lathe([(0.0, 0.6), (0.58, 0.6), (0.58, 0.66), (0.3, 0.72), (0.0, 0.74)], 12)
    lid.add(ccyl(0.12, 0.15, 8, "y", (0, 0.76, 0), 0.03))
    h = G.Geo()
    for sx in (-1, 1):
        h.add(rod((sx * 0.5, 0.48, -0.15), (sx * 0.68, 0.48, 0.0), 0.075, 4))
        h.add(rod((sx * 0.68, 0.48, 0.0), (sx * 0.5, 0.48, 0.15), 0.075, 4))
    return [("Pot", "steel", body), ("Lid", "steel_light", lid), ("Handles", "charcoal", h)]


@prop("FryPans")
def fry_pans(rng):
    """Two black frying pans nested, handles to one side."""
    g, hd = G.Geo(), G.Geo()
    for i, (r, a) in enumerate(((0.5, 0.0), (0.44, 18.0))):
        y = 0.16 * i
        g.add(lathe([(0.0, y), (r - 0.08, y), (r, y + 0.16), (r - 0.05, y + 0.18), (0.0, y + 0.06)], 12)
              .xf(RY(a)))
        hd.add(rod((r - 0.05, y + 0.12, 0.0), (r + 0.75, y + 0.2, 0.0), 0.08, 6).xf(RY(a)))
    return [("Pans", "iron", g), ("PanHandles", "wood_dark", hd)]


@prop("SheetTrays")
def sheet_trays(rng):
    """Three baking sheets stacked a little skew."""
    g = G.Geo()
    for i in range(3):
        g.add(bevel_box(1.5, 0.15, 1.1, 0.04, c=(rng.uniform(-0.05, 0.05), 0.075 + 0.15 * i, rng.uniform(-0.05, 0.05)))
              .xf(RY(rng.uniform(-3, 3))))
    return [("Trays", "steel_dark", g)]


@prop("PlateStack")
def plate_stack(rng):
    """Eight white plates, one with a chip out of its rim (the chip is just a darker plate)."""
    g, chip = G.Geo(), G.Geo()
    for i in range(8):
        p = lathe([(0.0, 0.0), (0.3, 0.0), (0.45, 0.07), (0.47, 0.1), (0.0, 0.05)], 12).xf(T(0, 0.075 * i, 0))
        (chip if i == 5 else g).add(p)
    return [("Plates", "cream", g), ("ChippedPlate", "cream_dark", chip)]


@prop("Tins")
def tins(rng):
    """Three catering tins: two standing, one on its side in front."""
    cans, labels = G.Geo(), G.Geo()
    for x in (-0.33, 0.33):
        cans.add(ccyl(0.28, 0.6, 10, "y", (x, 0.3, -0.1), 0.04))
        labels.add(ccyl(0.3, 0.3, 10, "y", (x, 0.3, -0.1), 0.02))
    cans.add(ccyl(0.28, 0.6, 10, "x", (0.0, 0.28, 0.35), 0.04))
    labels.add(ccyl(0.3, 0.3, 10, "x", (0.0, 0.28, 0.35), 0.02))
    return [("Cans", "steel_light", cans), ("Labels", "tomato", labels)]


@prop("Rags")
def rags(rng):
    """A pile of folded blue-and-white cloths, the top one unfolded and hanging off."""
    g, top = G.Geo(), G.Geo()
    for i in range(3):
        g.add(bevel_box(0.9, 0.15, 0.7, 0.05, c=(rng.uniform(-0.04, 0.04), 0.075 + 0.15 * i, 0)).xf(RY(rng.uniform(-6, 6))))
    top.add(bevel_box(0.9, 0.15, 0.75, 0.05, c=(0.1, 0.52, 0.05)).xf(RY(12)))
    top.add(bevel_box(0.15, 0.4, 0.6, 0.05, c=(0.62, 0.36, 0.1)))
    return [("Cloths", "label_blue", g), ("Cloth", "label_white", top)]


@prop("SprayBottle")
def spray_bottle(rng):
    """A green trigger spray bottle, half full."""
    body = lathe([(0.0, 0.0), (0.18, 0.0), (0.2, 0.05), (0.2, 0.42), (0.1, 0.52), (0.0, 0.52)], 10)
    head = G.Geo()
    head.add(bevel_box(0.2, 0.22, 0.4, 0.05, c=(0, 0.63, 0.08)))
    head.add(bevel_box(0.15, 0.22, 0.15, 0.04, c=(0, 0.47, 0.2)).xf(G.M(G.rx(-20))))
    return [("Bottle", "label_green", body), ("Trigger", "white", head)]


@prop("BleachJug")
def bleach_jug(rng):
    """A white jug with a blue cap and a hollow handle."""
    body = bevel_box(0.55, 0.6, 0.45, 0.1, c=(0, 0.3, 0))
    body.add(rod((0.12, 0.5, 0.0), (0.12, 0.68, 0.0), 0.075, 4))
    body.add(rod((0.12, 0.68, 0.0), (-0.05, 0.64, 0.0), 0.075, 4))
    cap = ccyl(0.11, 0.15, 8, "y", (-0.15, 0.65, 0), 0.03)
    band = bevel_box(0.57, 0.25, 0.47, 0.03, c=(0, 0.28, 0))
    return [("Jug", "white", body), ("Cap", "label_blue", cap), ("JugLabel", "label_blue", band)]


@prop("Bucket")
def bucket(rng):
    """A grey bucket with a wire handle, a scrubbing brush in it."""
    b = lathe([(0.0, 0.0), (0.38, 0.0), (0.46, 0.7), (0.4, 0.7), (0.34, 0.15), (0.0, 0.15)], 12)
    h = G.Geo()
    h.add(rod((-0.45, 0.6, 0), (0.0, 0.72, 0), 0.075, 4))
    h.add(rod((0.0, 0.72, 0), (0.45, 0.6, 0), 0.075, 4))
    br = bevel_box(0.5, 0.2, 0.25, 0.05, c=(0.05, 0.62, 0.0)).xf(RZ(20))
    return [("Bucket", "grey", b), ("BucketHandle", "steel_dark", h), ("Brush", "mustard", br)]


@prop("Carton")
def carton(rng):
    """A cardboard carton of napkins, its flaps half open."""
    b = bevel_box(1.2, 0.55, 0.9, 0.05, c=(0, 0.275, 0))
    fl = G.Geo()
    fl.add(bevel_box(1.2, 0.15, 0.4, 0.03, c=(0, 0.6, 0.62)))
    fl.add(bevel_box(0.15, 0.2, 0.9, 0.03, c=(0.66, 0.6, 0)))
    nap = bevel_box(1.0, 0.15, 0.7, 0.03, c=(0, 0.56, 0))
    return [("Box", "cardboard", b), ("Flaps", "cardboard_dark", fl), ("Napkins", "paper", nap)]


@prop("ToolBox")
def tool_box(rng):
    """A red steel tool box, its catch undone, a screwdriver left on top."""
    b = bevel_box(1.4, 0.55, 0.6, 0.06, c=(0, 0.275, 0))
    lid = bevel_box(1.44, 0.15, 0.64, 0.04, c=(0, 0.6, 0))
    h = G.Geo()
    h.add(rod((-0.35, 0.68, 0), (-0.35, 0.74, 0), 0.075, 4))
    h.add(rod((0.35, 0.68, 0), (0.35, 0.74, 0), 0.075, 4))
    h.add(rod((-0.35, 0.74, 0), (0.35, 0.74, 0), 0.075, 4))
    sd = G.Geo()
    sd.add(ccyl(0.08, 0.35, 6, "x", (0.4, 0.75, 0.15), 0.02))
    sd.add(rod((0.57, 0.75, 0.15), (0.75, 0.75, 0.15), 0.075, 4))
    return [("Box", "red", b), ("Lid", "red_dark", lid), ("ToolHandle", "black", h), ("Screwdriver", "mustard", sd)]


@prop("LunchBox")
def lunch_box(rng):
    """A dented tin lunch box and a tartan flask: somebody's lunch, never collected."""
    b = bevel_box(0.9, 0.5, 0.6, 0.06, c=(-0.2, 0.25, 0))
    b.add(rod((-0.4, 0.5, 0), (0.0, 0.5, 0), 0.075, 4))
    fl = ccyl(0.17, 0.6, 10, "y", (0.5, 0.3, 0.05), 0.04)
    cap = ccyl(0.19, 0.2, 10, "y", (0.5, 0.7, 0.05), 0.04)
    return [("Tin", "shade_green", b), ("Flask", "red_faded", fl), ("FlaskCap", "black", cap)]


@prop("OneShoe")
def one_shoe(rng):
    """One black work shoe, the laces still tied. Just the one."""
    sole = bevel_box(0.45, 0.15, 1.0, 0.05, c=(0, 0.075, 0))
    up = G.Geo()
    up.add(bevel_box(0.42, 0.35, 0.65, 0.12, c=(0, 0.32, -0.15)))
    up.add(bevel_box(0.4, 0.25, 0.4, 0.1, c=(0, 0.25, 0.28)))
    lace = G.Geo()
    for z in (0.05, 0.2):
        lace.add(bevel_box(0.36, 0.15, 0.15, 0.03, c=(0, 0.45, z)))
    return [("Sole", "rubber", sole), ("Upper", "black", up), ("Laces", "cream", lace)]


@prop("MouseTrap")
def mouse_trap(rng):
    """A wooden snap trap, sprung, the bait gone."""
    b = bevel_box(0.4, 0.15, 0.8, 0.03, c=(0, 0.075, 0))
    w = G.Geo()
    w.add(rod((-0.15, 0.2, 0.25), (0.15, 0.2, 0.25), 0.075, 4))
    w.add(rod((-0.15, 0.2, 0.25), (-0.15, 0.2, -0.1), 0.075, 4))
    w.add(rod((0.15, 0.2, 0.25), (0.15, 0.2, -0.1), 0.075, 4))
    return [("Base", "wood_light", b), ("Spring", "steel", w)]


@prop("SinkTrap")
def sink_trap(rng):
    """The pipework under a sink: tail pipe, U-bend, the run to the wall; a slow drip tray."""
    g = G.Geo()                                     # origin on the bay floor under the plughole
    g.add(rod((0, 1.32, 0), (0, 0.95, 0), 0.15, 8))
    g.add(rod((0, 0.95, 0), (0.45, 0.95, 0), 0.15, 8))
    g.add(rod((0.45, 0.95, 0), (0.45, 1.15, 0), 0.15, 8))
    g.add(rod((0.45, 1.15, 0), (0.45, 1.15, -1.75), 0.15, 8))
    nut = G.Geo()
    for c in ((0, 1.25, 0), (0.45, 1.15, -1.45)):
        nut.add(ccyl(0.2, 0.15, 8, "y", c, 0.03))
    return [("Pipes", "grey_light", g), ("Nuts", "steel_dark", nut)]


# ---------------------------------------------------------------- drawers (lying flat, under 0.35)

@prop("CutleryTray")
def cutlery_tray(rng):
    """A plastic organiser, three bays of forks, knives and spoons."""
    tray = G.Geo()
    tray.add(bevel_box(1.2, 0.15, 1.5, 0.03, c=(0, 0.075, 0)))
    for x in (-0.6, -0.2, 0.2, 0.6):
        tray.add(bevel_box(0.15, 0.3, 1.5, 0.03, c=(min(max(x, -0.525), 0.525), 0.15, 0)))
    for z in (-0.675, 0.675):
        tray.add(bevel_box(1.2, 0.3, 0.15, 0.03, c=(0, 0.15, z)))
    cut = G.Geo()
    for i, x in enumerate((-0.4, 0.0, 0.4)):
        for j in range(2):
            cut.add(bevel_box(0.15, 0.15, 1.1, 0.03, c=(x - 0.05 + 0.1 * j, 0.22, 0)))
    return [("Organiser", "grey_light", tray), ("Cutlery", "steel_light", cut)]


@prop("Utensils")
def utensils(rng):
    """A ladle, tongs and a whisk thrown in loose."""
    g = G.Geo()
    g.add(rod((-0.4, 0.1, -0.8), (-0.3, 0.1, 0.5), 0.075, 4))
    g.add(lathe([(0.0, 0.0), (0.25, 0.05), (0.27, 0.15), (0.0, 0.08)], 8).xf(T(-0.3, 0.0, 0.7)))
    g.add(rod((0.1, 0.1, -0.7), (0.3, 0.1, 0.5), 0.075, 4))
    g.add(rod((0.2, 0.18, -0.7), (0.38, 0.18, 0.5), 0.075, 4))
    wh = G.Geo()
    wh.add(ccyl(0.08, 0.6, 6, "z", (0.55, 0.1, -0.5), 0.02))
    wh.add(G.sphere(0.2, 6, 4, (1.0, 0.6, 1.4), (0.55, 0.15, 0.1)))
    return [("Tools", "steel", g), ("Whisk", "steel_light", wh)]


@prop("Paperwork")
def paperwork(rng):
    """Takeaway menus, a receipt roll, an elastic band round the lot."""
    g = G.Geo()
    for i in range(4):
        g.add(bevel_box(0.9, 0.15, 1.2, 0.03, c=(rng.uniform(-0.05, 0.05), 0.075 + 0.04 * i, 0)).xf(RY(rng.uniform(-8, 8))))
    roll = ccyl(0.18, 0.4, 10, "x", (0.0, 0.18, 0.85), 0.03)
    band = bevel_box(0.95, 0.15, 0.15, 0.03, c=(0, 0.2, 0))
    return [("Menus", "paper", g), ("ReceiptRoll", "paper_old", roll), ("Band", "red", band)]


@prop("Odds")
def odds(rng):
    """The drawer everyone has: tape, batteries, a lighter, string, a key on a fob."""
    tape = G.ring(0.25, 0.12, 0.2, 10, "y", (-0.35, 0.1, -0.3))
    bat = G.Geo()
    for i in range(3):
        bat.add(ccyl(0.08, 0.5, 6, "x", (0.2, 0.08, -0.4 + 0.17 * i), 0.02))
    st = G.torus(0.2, 0.08, 8, 4, "y", (-0.3, 0.08, 0.4))
    key = G.Geo()
    key.add(bevel_box(0.15, 0.15, 0.45, 0.03, c=(0.35, 0.075, 0.45)))
    key.add(bevel_box(0.3, 0.15, 0.3, 0.05, c=(0.35, 0.075, 0.8)))
    return [("Tape", "tape", tape), ("Batteries", "mustard", bat), ("String", "jute", st), ("Key", "brass", key)]


@prop("BadgeTray")
def badge_tray(rng):
    """A shallow card tray the name badges lie in (the badges themselves are Boards)."""
    g = G.Geo()
    g.add(bevel_box(1.3, 0.15, 1.1, 0.03, c=(0, 0.075, 0)))
    return [("Tray", "cardboard", g)]


INSIDE_PROPS = ("LiddedPot", "FryPans", "SheetTrays", "PlateStack", "Tins", "Rags", "SprayBottle", "BleachJug",
                "Bucket", "Carton", "ToolBox", "LunchBox", "OneShoe", "MouseTrap", "CutleryTray", "Utensils",
                "Paperwork", "Odds")


@prop("Pens")
def pens(rng):
    """Three biros, a pencil stub and a ball of rubber bands."""
    g = G.Geo()
    for i, (x, a) in enumerate(((-0.12, 4), (0.0, -6), (0.12, 10))):
        g.add(ccyl(0.075, 0.75, 6, "z", (x, 0.075, -0.05), 0.02).xf(RY(a)))
    pen = ccyl(0.075, 0.4, 6, "z", (0.0, 0.075, 0.0), 0.02).xf(T(0.15, 0.0, 0.42))
    ball = G.sphere(0.15, 8, 5, (1, 1, 1), (-0.15, 0.15, 0.4))
    return [("Biros", "label_blue", g), ("Pencil", "mustard", pen), ("BandBall", "red_light", ball)]


@prop("Spatulas")
def spatulas(rng):
    """Two spatulas and a pastry brush, for the narrow drawers."""
    g = G.Geo()
    for x, a in ((-0.15, -3), (0.12, 4)):
        g.add(bevel_box(0.3, 0.15, 0.55, 0.04, c=(x, 0.075, 0.45)).xf(RY(a)))
        g.add(rod((x, 0.09, 0.15), (x, 0.09, -0.65), 0.075, 4).xf(RY(a)))
    br = G.Geo()
    br.add(rod((0.0, 0.09, -0.7), (0.05, 0.09, 0.3), 0.075, 4).xf(T(0.0, 0.0, 0.0)))
    br.add(bevel_box(0.2, 0.15, 0.25, 0.04, c=(0.06, 0.09, 0.45)))
    return [("Spatulas", "black", g), ("Brush", "wood_light", br)]


# ---------------------------------------------------------------- Little Papa

def little_papa_geo():
    """Little Papa: a stuffed toy of Papa Stud's mask, 1.3 tall, sitting. A slice of pizza for
    a face (crust on top, the point down), round white eyes with small pupils, red cheeks, a
    wide stitched grin and two pepperoni; a little chef's hat; a white jacket body; stubby
    arms and legs. Origin at its underside, +Z its front."""
    out = []
    body = G.blob(0.36, 10, 6, (1.0, 0.85, 0.85), 0.04, 7, (0, 0.34, -0.02), -0.3)
    out.append(("Body", "white", body))
    legs, arms = G.Geo(), G.Geo()
    for sx in (-1, 1):
        legs.add(ccyl(0.13, 0.36, 8, "z", (sx * 0.17, 0.13, 0.25), 0.05))
        legs.add(G.sphere(0.15, 8, 5, (1.0, 0.8, 1.1), (sx * 0.17, 0.12, 0.45)))
        arms.add(rod((sx * 0.33, 0.48, 0.0), (sx * 0.47, 0.3, 0.12), 0.11, 6))
        arms.add(G.sphere(0.13, 8, 5, (1, 1, 1), (sx * 0.48, 0.28, 0.14)))
    out.append(("Legs", "grey_dark", legs))
    out.append(("Arms", "white", arms))
    # the face: a slice, crust up, point down, a thick moulded slab
    face = G.extrude([(-0.4, 0.42), (0.4, 0.42), (0.06, -0.3), (-0.06, -0.3)], 0.22, "z", (0, 0.86, 0.12))
    out.append(("Face", "cheese", face))
    crust = G.Geo()
    crust.add(ccyl(0.12, 0.92, 8, "x", (0, 1.3, 0.12), 0.05))
    out.append(("Crust", "crust", crust))
    eyes, pupils = G.Geo(), G.Geo()
    for sx in (-1, 1):
        eyes.add(ccyl(0.11, 0.15, 10, "z", (sx * 0.16, 1.14, 0.24), 0.03))
        pupils.add(ccyl(0.045, 0.15, 6, "z", (sx * 0.15, 1.13, 0.29), 0.01))
    out.append(("Eyes", "white", eyes))
    out.append(("Pupils", "black", pupils))
    cheeks = G.Geo()
    for sx in (-1, 1):
        cheeks.add(ccyl(0.07, 0.15, 8, "z", (sx * 0.27, 1.0, 0.22), 0.02))
    out.append(("Cheeks", "red_light", cheeks))
    grin = G.Geo()
    for i in range(7):
        x = -0.24 + 0.08 * i
        y = 0.96 - 0.12 * (1 - (x / 0.26) ** 2)
        grin.add(bevel_box(0.1, 0.15, 0.15, 0.02, c=(x, y, 0.27)))
    out.append(("Grin", "black", grin))
    pep = G.Geo()
    for (x, y) in ((0.02, 0.78), (-0.1, 1.27)):
        pep.add(ccyl(0.06, 0.15, 8, "z", (x, y - 0.1 if y > 1.2 else y, 0.24), 0.02))
    out.append(("Pepperoni", "pepperoni", pep))
    hat = G.Geo()
    hat.add(ccyl(0.2, 0.15, 10, "y", (0, 1.42, 0.0), 0.03))
    hat.add(G.sphere(0.24, 10, 5, (1.0, 0.75, 1.0), (0, 1.52, 0.0)))
    out.append(("Hat", "white", hat))
    return out


@prop("LittlePapa")
def little_papa(rng):
    sc = 1.3 / 1.7                                   # modelled at 1.7, the toy is 1.3 tall
    return [(n, c, g.xf(G.S(sc))) for (n, c, g) in little_papa_geo()]


# ---------------------------------------------------------------- the drinks cooler's stock

def _row(parts_fn, n, pitch, h):
    """n drinks one behind the other (going -Z from the origin), standing on y = 0."""
    out = {}
    for i in range(n):
        for pname, c, g in parts_fn((200, 32, 36)):
            out.setdefault(pname, (c, G.Geo()))[1].add(g.xf(T(0, h, -pitch * i)))
    return [(pname, c, g) for pname, (c, g) in out.items()]


@prop("CanRow")
def can_row(rng):
    """Two cans one behind the other (the row's front place is the Slot); recoloured per flavour."""
    from .items2 import can_parts
    return _row(can_parts, 2, 0.8, 0.64)


@prop("BottleRow")
def bottle_row(rng):
    from .items2 import bottle_parts
    return _row(bottle_parts, 2, 0.8, 0.65)


@prop("TicketSpike")
def ticket_spike(rng):
    """The order spike on the pass: a weighted base, the steel Spike, done tickets on it."""
    base = ccyl(0.35, 0.2, 10, "y", (0, 0.1, 0), 0.05)
    spike = G.Geo()
    spike.add(rod((0, 0.2, 0), (0, 1.3, 0), 0.075, 5))
    tickets = G.Geo()
    for i in range(5):
        tickets.add(bevel_box(0.55, 0.15, 0.85, 0.03, c=(0.02 * (i % 2), 0.3 + 0.16 * i, 0.1)).xf(RY(17 * i - 30)))
    return [("Base", "black", base), ("Spike", "steel_light", spike), ("Tickets", "paper", tickets)]
