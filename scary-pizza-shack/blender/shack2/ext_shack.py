"""The shack from outside: the PIZZA sign on its steel frame with chase bulbs, the striped
awning over the shutter box, the lit menu board, the rainwater goods, the meter and the
service drop, the rooftop (air conditioner, vents, aerial, patched membrane), the back door
step with its sand bucket, the log pile for the oven, the side window's outside sill, the
bench, bin and bollards at the front, and the string lights to their pole."""
import math

import numpy as np

import spsgeo as G
from spsgeo import CF

from . import layout as L, outkit as O
from .kit import bevel_box, ccyl, chamfer_slab, rod
from .st_common import FACE, board, weld_all

SX0, SX1 = L.OUT_X0 - 0.5, L.OUT_X1 + 0.5          # the skin's outer faces: X -18.5 .. 18.5
SZ0, SZ1 = L.OUT_Z0 - 0.5, L.OUT_Z1 + 0.5          # Z -11.5 .. 11.5
ROOF = L.ROOF_TOP                                  # 13.4


def face_slab(pts, h, b=0.08):
    return chamfer_slab([(x, -y) for (x, y) in pts], h, b).xf(G.M(G.rx(90))).xf(G.T(0, 0, -h / 2))


# ---------------------------------------------------------------- the PIZZA sign

STROKE = 0.9


def _strokes(ch):
    """Blocky letter strokes (x0, y0, x1, y1) in a 3.2 x 4.4 cell, plus diagonals."""
    s = STROKE
    if ch == "P":
        return [(0, 0, s, 4.4), (0, 4.4 - s, 2.7, 4.4), (0, 1.8, 2.7, 1.8 + s), (3.2 - s, 1.8, 3.2, 4.4)], []
    if ch == "I":
        return [(1.6 - s / 2, 0, 1.6 + s / 2, 4.4), (0.5, 4.4 - 0.8, 2.7, 4.4), (0.5, 0, 2.7, 0.8)], []
    if ch == "Z":
        return [(0, 4.4 - s, 3.2, 4.4), (0, 0, 3.2, s)], [((3.2 - 0.55, 4.4 - s), (0.55, s))]
    if ch == "A":
        return [(0, 0, s, 3.5), (3.2 - s, 0, 3.2, 3.5), (0.35, 4.4 - s, 2.85, 4.4), (0, 1.6, 3.2, 1.6 + s)], \
            [((0.25, 3.3), (0.75, 4.2)), ((2.95, 3.3), (2.45, 4.2))]
    raise KeyError(ch)


def _letters(text, cell=3.2, gap=0.8, grow=0.0, depth=0.6):
    g = G.Geo()
    width = len(text) * cell + (len(text) - 1) * gap
    x = -width / 2
    for ch in text:
        boxes, diags = _strokes(ch)
        for (x0, y0, x1, y1) in boxes:
            g.add(bevel_box(x1 - x0 + 2 * grow, y1 - y0 + 2 * grow, depth, 0.1,
                            c=(x + (x0 + x1) / 2, (y0 + y1) / 2, 0)))
        for (a, b) in diags:
            a, b = np.array(a, float), np.array(b, float)
            d = b - a
            ln = float(np.linalg.norm(d))
            ang = math.degrees(math.atan2(d[1], d[0]))
            box = bevel_box(ln + 0.4 + 2 * grow, STROKE + 2 * grow, depth, 0.1)
            g.add(box.xf(G.M(G.rz(ang))).xf(G.T(x + (a[0] + b[0]) / 2, (a[1] + b[1]) / 2, 0)))
        x += cell + gap
    return g, width


def pizza_sign(k, f):
    """The sign on the roof's front edge: a steel lattice frame, a cream panel with a red
    border, red PIZZA letters outlined in cream, the PAPA STUD'S strip (a Board), 44 chase
    Bulbs round the border (Chase = their order), and two lamps on arms lighting it."""
    m = k.sc.model(f, "PizzaSign")
    z = SZ1 - 2.3                                     # behind the front parapet
    y0, y1 = 15.6, 22.2
    x0, x1 = -11.5, 11.5
    xc, yc = 0.0, (y0 + y1) / 2
    fr = G.Geo()
    for x in (-9.0, 0.0, 9.0):
        fr.add(bevel_box(0.5, y1 - ROOF + 0.2, 0.5, 0.06, c=(x, (ROOF + y1) / 2, -0.6)))
        fr.add(rod((x, ROOF, -3.4), (x, y0 + 1.5, -0.6), 0.14, 6))                      # back stay
        fr.add(bevel_box(1.2, 0.3, 3.6, 0.05, c=(x, ROOF + 0.15, -1.6)))                # foot plate
    for y in (y0 + 0.6, y1 - 0.6):
        fr.add(bevel_box(x1 - x0 - 1.0, 0.4, 0.4, 0.05, c=(0, y, -0.6)))
    k.mesh(m, "Brace", "PizzaSign__Frame", fr, CF((0, 0, z)), "galv_dark", solid=False)
    k.mesh(m, "Panel", "PizzaSign__Panel", bevel_box(x1 - x0, y1 - y0, 0.4, 0.1), CF((xc, yc, z - 0.1)), "cream",
           solid=True)
    k.mesh(m, "Border", "PizzaSign__Border", O_frame(x1 - x0 + 0.4, y1 - y0 + 0.4, 0.6, 0.5), CF((xc, yc, z - 0.2)),
           "red", shadow=False)
    lg, w = _letters("PIZZA")
    k.mesh(m, "Letters", "PizzaSign__Letters", lg, CF((xc, y0 + 1.7, z + 0.4)), "red", shadow=False)
    og, _ = _letters("PIZZA", grow=0.22, depth=0.4)
    k.mesh(m, "LetterOutline", "PizzaSign__Outline", og, CF((xc, y0 + 1.7, z + 0.25)), "red_dark", shadow=False)
    k.mesh(m, "Strip", "PizzaSign__Strip", bevel_box(12.0, 1.0, 0.3, 0.06), CF((xc, y0 + 1.0, z + 0.2)), "red",
           shadow=False)
    board(k, m, (11.4, 0.8, 0.15), CF((xc, y0 + 1.0, z + 0.42), FACE["N"]), "red", text="PAPA STUD'S",
          text_color=(250, 236, 200), name="Board")
    # chase bulbs clockwise from the top-left corner
    pts = [(x0 + 0.5 + i * (x1 - x0 - 1.0) / 17, y1 - 0.35) for i in range(18)]
    pts += [(x1 - 0.35, y1 - 0.35 - i * (y1 - y0 - 0.7) / 5) for i in range(1, 5)]
    pts += [(x1 - 0.5 - i * (x1 - x0 - 1.0) / 17, y0 + 0.35) for i in range(18)]
    pts += [(x0 + 0.35, y0 + 0.35 + i * (y1 - y0 - 0.7) / 5) for i in range(1, 5)]
    for i, (bx, by) in enumerate(pts):
        b = k.part(m, "Bulb", (0.5, 0.5, 0.5), CF((bx, by, z + 0.32)), (255, 220, 150), material="Neon",
                   shape="Ball", grid=False, shadow=False)
        k.attr(b, "Chase", i + 1)
    # two lamps on short stands on the coping, shining up at it
    zc_ = SZ1 - 0.6                                   # the front coping's middle
    for i, x in enumerate((-6.0, 6.0)):
        lm = k.sc.model(m, "SignLamp%d" % (i + 1))
        arm = G.Geo()
        arm.add(bevel_box(0.6, 0.2, 0.6, 0.05, c=(0, 0.1, 0)))
        arm.add(rod((0, 0.2, 0), (0, 0.9, -0.2), 0.1, 6))
        k.mesh(lm, "Arm", "PizzaSign__LampArm", arm, CF((x, L.COPING_TOP, zc_)), "galv_dark", shadow=False)
        hood = G.outward(G.lathe([(0.0, -0.3), (0.45, -0.25), (0.55, 0.25), (0.0, 0.3)], 8))
        k.mesh(lm, "Hood", "PizzaSign__LampHood", hood.xf(G.M(G.rx(-50))), CF((x, L.COPING_TOP + 1.2, zc_ - 0.35)),
               "charcoal", shadow=False)
        bulb = k.part(lm, "Bulb", (0.5, 0.5, 0.5), CF((x, L.COPING_TOP + 1.35, zc_ - 0.55)), (255, 232, 190),
                      material="Neon", shape="Ball", grid=False, shadow=False)
        k.lamp(lm, bulb, "Shack", "Spot", 22.0, 2.0, (255, 214, 160), angle=90.0, face="Top", shadows=False)
    k.mark_used("PizzaSign", "outside")


def O_frame(w, h, bar, depth):
    """A rectangular frame of four bevelled bars (centred, depth along Z)."""
    g = G.Geo()
    for (cx, cy, sx, sy) in ((0, h / 2 - bar / 2, w, bar), (0, -h / 2 + bar / 2, w, bar),
                             (-w / 2 + bar / 2, 0, bar, h - 2 * bar), (w / 2 - bar / 2, 0, bar, h - 2 * bar)):
        g.add(bevel_box(sx, sy, depth, 0.06, c=(cx, cy, 0)))
    return g


# ---------------------------------------------------------------- awning, menu board

def awning(k, f):
    """Red and cream striped canvas over the shutter box, a scalloped valance, steel arms."""
    m = k.sc.model(f, "Awning")
    za, zb = SZ1 + 1.8, SZ1 + 5.2                  # from the shutter box's top edge out over the queue
    ya, yb = 11.95, 10.5
    xa, xb = -7.5, 7.5
    ln = math.hypot(zb - za, ya - yb)
    tilt = math.degrees(math.atan2(ya - yb, zb - za))
    # the canvas is modelled flat in a frame tilted with it (so its bounds hug it), the valance
    # hangs plumb from the front edge
    frame = CF((0, (ya + yb) / 2, (za + zb) / 2), G.rx(tilt))
    red, cream, vred, vcream = G.Geo(), G.Geo(), G.Geo(), G.Geo()
    n = 15
    for i in range(n):
        x = xa + (i + 0.5) * (xb - xa) / n
        strip = bevel_box((xb - xa) / n, 0.2, ln, 0.04, c=(x, 0, 0))
        val = face_slab([(-0.5, 0.0), (0.5, 0.0), (0.5, -0.35), (0.3, -0.6), (0.0, -0.68), (-0.3, -0.6), (-0.5, -0.35)],
                        0.15, 0.04).xf(G.T(x, 0, 0))
        (red if i % 2 == 0 else cream).add(strip)
        (vred if i % 2 == 0 else vcream).add(val.xf(G.T(0, yb - 0.05, zb + 0.08)))
    k.mesh(m, "Stripe", "Awning__Red", red, frame, "canvas_red", shadow=True)
    k.mesh(m, "Stripe", "Awning__Cream", cream, frame, "canvas_cream", shadow=True)
    k.mesh(m, "Valance", "Awning__ValanceRed", vred, CF(), "canvas_red", shadow=False)
    k.mesh(m, "Valance", "Awning__ValanceCream", vcream, CF(), "canvas_cream", shadow=False)
    arms = G.Geo()
    for x in (-5.0, 5.0):                             # from the shutter box's front to the front bar
        arms.add(rod((x, 10.4, SZ1 + 1.85), (x, yb + 0.05, zb), 0.12, 6))
        arms.add(bevel_box(0.6, 0.8, 0.2, 0.05, c=(x, 10.4, SZ1 + 1.85)))
    arms.add(rod((xa, yb + 0.05, zb), (xb, yb + 0.05, zb), 0.12, 6))
    k.mesh(m, "Arms", "Awning__Arms", arms, CF(), "charcoal", shadow=False)
    k.mark_used("Awning", "outside")


def menu_board(k, f):
    """The menu on the front wall east of the window: a framed blackboard with the prices, a
    red title strip, and a gooseneck lamp over it."""
    m = k.sc.model(f, "MenuBoard")
    xc, yc, w, h = 9.0, 6.4, 4.8, 3.8
    z = SZ1
    k.mesh(m, "Frame", "MenuBoard__Frame", O_frame(w + 0.5, h + 0.5, 0.35, 0.4), CF((xc, yc, z + 0.2)), "wood_dark",
           solid=True)
    k.mesh(m, "Back", "MenuBoard__Back", bevel_box(w, h, 0.2, 0.04), CF((xc, yc, z + 0.1)), "chalkboard", solid=True)
    board(k, m, (w - 0.2, 0.7, 0.15), CF((xc, yc + h / 2 - 0.55, z + 0.28), FACE["N"]), "red", text="TODAY'S MENU",
          text_color=(250, 236, 200), name="Title")
    board(k, m, (w - 0.4, h - 1.3, 0.15), CF((xc, yc - 0.45, z + 0.28), FACE["N"]), "chalkboard",
          text="PEPPERONI ....... 8.99\nCHEESE ............. 7.49\nHAWAIIAN ......... 9.25\n"
               "GARLIC KNOTS ... 3.50\nSODA .................. 1.25", text_color=(236, 232, 214), name="Board")
    lm = k.sc.model(m, "Lamp")
    neck = G.tube([(0, 0, 0.1), (0, 0.6, 0.6), (0, 0.7, 1.3), (0, 0.4, 1.7)], 0.1, 6)
    k.mesh(lm, "Neck", "MenuBoard__Neck", neck, CF((xc, yc + h / 2 + 0.3, z)), "charcoal", shadow=False)
    shade = G.outward(G.lathe([(0.0, 0.25), (0.25, 0.25), (0.6, -0.2), (0.0, -0.1)], 10))
    k.mesh(lm, "Shade", "MenuBoard__Shade", shade.xf(G.M(G.rx(30))), CF((xc, yc + h / 2 + 0.55, z + 1.85)),
           "trim_green", shadow=False)
    bulb = k.part(lm, "Bulb", (0.4, 0.4, 0.4), CF((xc, yc + h / 2 + 0.25, z + 2.0)), (255, 226, 170), material="Neon",
                  shape="Ball", grid=False, shadow=False)
    k.lamp(lm, bulb, "Shack", "Spot", 12.0, 1.3, (255, 206, 150), angle=100.0)
    k.mark_used("MenuBoard", "outside")


# ---------------------------------------------------------------- walls: rainwater, meter, drop, sill

def rainwater(k, f):
    """Scuppers through the parapet with rain heads and downpipes to the ground (brackets
    every 2.4, a shoe at the foot): two on the back wall, one at the front west corner."""
    m = k.sc.model(f, "Rainwater")
    pipes, heads = G.Geo(), G.Geo()
    for (x, z, sgn) in ((-12.0, SZ0, -1), (12.0, SZ0, -1), (-17.0, SZ1, 1)):
        zo = z + sgn * 0.45
        heads.add(bevel_box(1.0, 1.0, 0.8, 0.08, c=(x, ROOF - 0.2, zo)))
        heads.add(bevel_box(0.5, 0.4, 0.8, 0.05, c=(x, ROOF + 0.4, z + sgn * 0.2)))            # scupper spout
        pipes.add(ccyl(0.25, ROOF - 0.9, 8, "y", (x, (ROOF - 0.7) / 2 + 0.2, zo), 0.04))
        pipes.add(G.tube([(x, 0.9, zo), (x, 0.45, zo + sgn * 0.2), (x, 0.3, zo + sgn * 0.7)], 0.25, 8))  # shoe
        for y in np.arange(2.4, ROOF - 1.0, 2.4):
            heads.add(bevel_box(0.7, 0.2, 0.55, 0.04, c=(x, y, z + sgn * 0.27)))
    k.mesh(m, "Downpipes", "Rain__Pipes", pipes, CF(), "trim_green", shadow=False)
    k.mesh(m, "Heads", "Rain__Heads", heads, CF(), "trim_green", shadow=False)
    k.mark_used("Downpipe", "outside")


def service(k, f, sc):
    """The meter on the east wall, its conduit up to a weatherhead mast over the parapet, and
    the service drop sagging over the lot to the nearest telegraph pole."""
    m = k.sc.model(f, "Service")
    xm = -15.2
    k.prop(m, "ElectricMeter", CF((xm, 4.4, SZ1)), where="outside", name="Meter")
    g = G.Geo()
    g.add(rod((xm, 5.4, SZ1 + 0.3), (xm, 11.4, SZ1 + 0.3), 0.18, 8))
    g.add(G.tube([(xm, 11.4, SZ1 + 0.3), (xm, 12.4, SZ1 + 0.6), (xm, 13.4, SZ1 + 0.85)], 0.18, 8))
    g.add(rod((xm, 13.4, SZ1 + 0.85), (xm, 17.5, SZ1 + 0.85), 0.18, 8))
    for y in np.arange(6.4, 11.0, 2.0):
        g.add(bevel_box(0.6, 0.2, 0.4, 0.04, c=(xm, y, SZ1 + 0.15)))
    g.add(bevel_box(0.5, 0.3, 0.75, 0.04, c=(xm, 15.6, SZ1 + 0.55)))          # strap to the coping's edge
    k.mesh(m, "Mast", "Service__Mast", g, CF(), "galv_dark", shadow=False)
    hood = G.outward(G.lathe([(0.0, 0.0), (0.35, 0.0), (0.4, 0.3), (0.0, 0.55)], 8))
    k.mesh(m, "Weatherhead", "Service__Head", hood, CF((xm, 17.5, SZ1 + 0.85)), "galv_dark", shadow=False)
    pole = (L.POLE_X[2], L.POLE_Z)                                  # the pole at X 2 across the road
    p0 = np.array((xm, 17.3, SZ1 + 0.85))
    p1 = np.array((pole[0] - 0.4, L.POLE_H - 2.6, pole[1]))
    k.mesh(m, "DropWire", "Service__Drop", O.catenary(p0, p1, 3.2, 0.08, 18), CF(), "black", shadow=False)
    k.mark_used("ServiceDrop", "outside")


def side_sill(k, f):
    """The side window's outside sill (where the Watcher stands and looks in)."""
    m = k.sc.model(f, "SideWindowOut")
    z0, z1, y0 = L.SIDE_Z0 - 0.7, L.SIDE_Z1 + 0.7, L.SIDE_Y0 - 0.4
    k.mesh(m, "SillOut", "SideWindow__SillOut", bevel_box(1.0, 0.4, z1 - z0, 0.08),
           CF((SX0 - 0.3, y0 + 0.2, (z0 + z1) / 2)), "concrete", solid=True)
    hd = bevel_box(0.6, 0.4, z1 - z0, 0.06)
    k.mesh(m, "HeadOut", "SideWindow__HeadOut", hd, CF((SX0 - 0.1, L.SIDE_Y1 + 0.6, (z0 + z1) / 2)), "red",
           shadow=False)


# ---------------------------------------------------------------- roof

def rooftop(k, f, rng):
    """The roof the cameras and the road both see: the air conditioner with its slow fan
    (Spin), three vents, the old TV aerial, tar patches and a puddle on the membrane."""
    m = k.sc.model(f, "Rooftop")
    k.prop(m, "RoofAC", CF((-7.0, ROOF, -5.0)), where="outside", name="AirConditioner")
    ac = m.get("AirConditioner")
    fan = G.Geo()
    for a in (0, 120, 240):
        fan.add(bevel_box(0.8, 0.15, 0.35, 0.04, c=(0.45, 0, 0)).xf(G.M(G.ry(a))))
    fan.add(ccyl(0.2, 0.2, 8, "y", (0, 0, 0), 0.04))
    fp = k.mesh(ac, "Fan", "Roof__ACFan", fan, CF((-7.0, ROOF + 2.5, -5.0)), "charcoal", shadow=False)
    k.attr(fp, "Spin", 240.0)
    for (x, z) in ((4.0, -7.0), (8.5, 3.0), (-12.5, 4.0)):
        k.prop(m, "RoofVent", CF((x, ROOF, z)), where="outside", name="Vent")
    k.prop(m, "TVAerial", CF((-14.0, ROOF, -7.5), G.ry(20)), where="outside", name="Aerial")
    patches = G.Geo()
    for (x, z, w, d) in ((-2.0, 2.0, 3.5, 2.5), (6.0, -4.0, 2.5, 3.0), (-10.0, -2.0, 3.0, 2.0), (11.0, 7.0, 2.0, 2.0)):
        pts = [(x - w / 2, z - d / 2), (x + w / 2, z - d / 2 + 0.2), (x + w / 2 - 0.2, z + d / 2), (x - w / 2 + 0.3, z + d / 2)]
        patches.add(chamfer_slab(pts, 0.15, 0.04))
    k.mesh(m, "Patch", "Roof__Patches", patches, CF((0, ROOF, 0)), "tar", shadow=False)
    k.prop(m, "Puddle", CF((-5.0, ROOF + 0.1, 8.0)), where="outside", name="Puddle", seed=7)
    k.mark_used("Rooftop", "outside")


# ---------------------------------------------------------------- back, front

def back_door(k, f):
    """Outside the back door: a concrete step, the sand bucket, the log pile for the oven,
    gas bottles in their cage, the hose reel and the ladder up to the roof."""
    m = k.sc.model(f, "BackYardWall")
    k.mesh(m, "Step", "Back__Step", bevel_box(5.0, 0.6, 1.6, 0.08), CF((-15.0, 0.3, SZ0 - 0.8)), "concrete", solid=True)
    k.prop(m, "SandBucket", CF((-10.9, 0.0, SZ0 - 0.75)), where="outside", name="SandBucket")
    k.prop(m, "LogPile", CF((-7.5, 0.0, SZ0 - 1.6), G.ry(180)), where="outside", name="LogPile")
    k.prop(m, "GasBottles", CF((-1.2, 0.0, SZ0 - 0.75), G.ry(180)), where="outside", name="GasBottles")
    k.prop(m, "HoseReel", CF((4.5, 3.4, SZ0), G.ry(180)), where="outside", name="HoseReel")
    k.prop(m, "WallLadder", CF((14.5, 0.0, SZ0), G.ry(180)), where="outside", name="Ladder")


def front(k, f):
    """At the front: the bench and the bin against the wall, two bollards at the kerb, the
    bug zapper on its bracket, the string lights from the corner to their pole."""
    m = k.sc.model(f, "Front")
    k.prop(m, "Bench", CF((-11.0, 0.0, SZ1 + 1.4)), where="outside", name="Bench")
    k.prop(m, "LitterBin", CF((-14.9, 0.0, SZ1 + 1.2)), where="outside", name="LitterBin")
    k.prop(m, "Litter", CF((-14.0, 0.0, SZ1 + 2.8)), where="outside", name="Litter", seed=3)
    for x in (-4.5, 4.5):
        k.prop(m, "Bollard", CF((x, 0.0, 19.4)), where="outside", name="Bollard")
    zap = CF((7.8, 8.6, SZ1 + 1.6))
    k.mesh(m, "ZapperArm", "Front__ZapperArm", rod((0, 0, -1.6), (0, 0, 0.2), 0.1, 6), zap * CF((0, 2.7, 0)),
           "charcoal", shadow=False)
    k.prop(m, "BugZapper", zap, where="outside", name="BugZapper")
    k.sc.attachment(m.get("BugZapper").children[0], "Fx_Moths", zap * CF((0, 1.0, 0.6)))
    # string lights: from the shack's west front corner to the pole by the picnic table
    sp = L.FORECOURT_PROPS["StringLightPole"]
    sp = (sp[0], 19.2)
    k.prop(m, "StringLightPole", CF((sp[0], 0.0, sp[1])), where="outside", name="StringLightPole")
    p0 = np.array((SX0 - 1.0, 11.0, SZ1 + 0.6))
    p1 = np.array((sp[0] + 0.6, 8.8, sp[1]))
    sl = k.sc.model(m, "StringLights")
    k.mesh(sl, "Wire", "Front__StringWire", O.catenary(p0, p1, 1.4, 0.075, 16), CF(), "black", shadow=False)
    cols = ((255, 190, 90), (255, 90, 70), (120, 220, 120), (255, 236, 200))
    n = 11
    for i in range(1, n):
        t = i / n
        p = p0 + (p1 - p0) * t
        p[1] -= 1.4 * 4 * t * (1 - t) + 0.35
        b = k.part(sl, "Bulb" if i == n // 2 else "Light", (0.4, 0.5, 0.4), CF(p), cols[i % 4], material="Neon",
                   shape="Ball", grid=False, shadow=False)
        k.attr(b, "Flicker", 0.15)
        if i == n // 2:
            k.lamp(sl, b, "Shack", "Point", 18.0, 0.8, (255, 206, 150), shadows=False)
    k.mark_used("StringLights", "outside")


def build(k, sc):
    f = sc.folder(sc.root.get("Shack"), "Outside")
    rng = np.random.default_rng(7)
    pizza_sign(k, f)
    awning(k, f)
    menu_board(k, f)
    rainwater(k, f)
    service(k, f, sc)
    side_sill(k, f)
    rooftop(k, f, rng)
    back_door(k, f)
    front(k, f)
    return f
