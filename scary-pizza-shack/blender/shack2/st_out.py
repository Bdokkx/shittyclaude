"""The yard and street stations, rebuilt in the new style with batch 1's names, markers,
pivots and attachments: the Generator in its lean-to, the Dumpster with its wheelie bins
and TrashBag items, the YardGate, the StreetLamp and the YardLamp."""
import math

import numpy as np

import spsgeo as G
from spsgeo import CF

from . import layout as L, outkit as O
from .kit import bevel_box, ccyl, cfrustum, chamfer_slab, rod
from .st_common import E, N, S_, W, moving, pivot, stand, station, weld_all

PAD_Y = 0.4          # the generator shed's concrete pad (and so the Stand's height, as batch 1)


# ---------------------------------------------------------------- generator

def generator(k, gr):
    """A yellow open-frame generator on the shed's pad: tube cage on two wheels and two
    rubber feet, the engine with its fins and recoil starter (the T-Handle pulls out), the
    fuel tank on top (the FuelCap unscrews), the muffler (Exhaust), the control Panel with
    two sockets, a breaker, a dial and the indicator Bulb (off: lit colour in BulbOnColor)."""
    m = station(k, "Generator")
    k.attr(m, "BulbOnColor", "255,70,40")
    cx, cz = -20.0, -34.0
    base = CF((cx, PAD_Y, cz))
    # frame
    fr = G.Geo()
    hx, hz, yb, yt = 1.25, 0.9, 0.25, 2.15
    for y in (yb, yt):
        for sz in (-1, 1):
            fr.add(rod((-hx, y, sz * hz), (hx, y, sz * hz), 0.1, 6))
        for sx in (-1, 1):
            fr.add(rod((sx * hx, y, -hz), (sx * hx, y, hz), 0.1, 6))
    for sx in (-1, 1):
        for sz in (-1, 1):
            fr.add(rod((sx * hx, yb, sz * hz), (sx * hx, yt, sz * hz), 0.1, 6))
    for sx in (-1, 1):                                                   # carry handles
        fr.add(G.tube([(sx * 0.9, yt, -hz), (sx * 0.9, yt + 0.35, -hz + 0.3), (sx * 0.9, yt + 0.35, hz - 0.3),
                       (sx * 0.9, yt, hz)], 0.1, 6))
    fr.add(rod((-hx, 0.38, -hz - 0.25), (-hx, 0.38, hz + 0.25), 0.09, 6))            # axle
    for sz in (-1, 1):
        fr.add(bevel_box(0.4, 0.25, 0.3, 0.06, c=(hx - 0.1, 0.125, sz * (hz - 0.1))))  # rubber feet
    k.mesh(m, "Frame", "Generator__Frame", fr, base, "charcoal", solid=True)
    wh = G.Geo()
    for sz in (-1, 1):
        wh.add(ccyl(0.38, 0.3, 10, "z", (-hx, 0.38, sz * (hz + 0.3)), 0.06))
        wh.add(ccyl(0.18, 0.34, 8, "z", (-hx, 0.38, sz * (hz + 0.3)), 0.03))
    k.mesh(m, "Wheels", "Generator__Wheels", wh, base, "tyre", shadow=False)
    # engine block, fins, recoil starter housing, air filter
    en = G.Geo()
    en.add(bevel_box(1.3, 0.95, 1.1, 0.1, c=(0.25, 0.85, -0.15)))
    for i in range(4):                                                              # cylinder fins
        en.add(bevel_box(0.15, 0.5, 1.2, 0.04, c=(-0.2 + 0.3 * i, 1.45, -0.15)))
    en.add(bevel_box(0.5, 0.5, 0.6, 0.06, c=(0.45, 1.45, 0.45)))                       # air filter box
    k.mesh(m, "Engine", "Generator__Engine", en, base, "grey_dark", solid=True)
    k.mesh(m, "Starter", "Generator__Starter", ccyl(0.38, 0.25, 10, "x", (1.0, 0.85, -0.3), 0.06), base, "red",
           shadow=False)
    # Body: fuel tank on top and the round alternator at the west end, in yellow
    body = G.Geo()
    body.add(bevel_box(2.1, 0.55, 1.55, 0.18, c=(0.0, 1.88, 0.0)))
    body.add(ccyl(0.55, 0.85, 10, "x", (-0.65, 0.85, 0.3), 0.1))
    bpart = k.mesh(m, "Body", "Generator__Body", body, base, "gen_yellow", solid=True)
    k.mesh(m, "Decal", "Generator__Decal", bevel_box(1.2, 0.3, 0.15, 0.04, c=(0.0, 1.88, -0.78)), base, "black",
           shadow=False)
    # muffler with its heat shield; the exhaust points south out of the shed's open side
    mu = G.Geo()
    mu.add(ccyl(0.24, 0.9, 10, "z", (-0.75, 1.05, -0.4), 0.05))
    mu.add(rod((-0.75, 1.05, 0.05), (-0.75, 1.05, 0.6), 0.09, 6))
    k.mesh(m, "Muffler", "Generator__Muffler", mu, base, "steel_dark", shadow=False)
    shield = G.Geo()
    for i in range(3):
        shield.add(bevel_box(0.62, 0.15, 0.2, 0.03, c=(-0.75, 1.33, -0.75 + 0.35 * i)))
    k.mesh(m, "HeatShield", "Generator__Shield", shield, base, "steel", shadow=False)
    k.sc.attachment(bpart, "Exhaust", base * CF((-0.75, 1.05, 0.62)))
    k.sc.attachment(bpart, "Fx_Smoke", base * CF((-0.75, 1.05, 0.62)))
    # fuel cap (unscrews) on the tank
    cap = k.mesh(m, "FuelCap", "Generator__FuelCap", ccyl(0.22, 0.2, 10, "y", (0, 0, 0), 0.05),
                 base * CF((0.5, 2.25, 0.35)), "black", solid=False)
    pivot(cap, base * CF((0.5, 2.25, 0.35)))
    moving(m, "FuelCap", "unscrews: turn the pivot about Y and lift it")
    # control panel on the east face: sockets, breaker, dial, the indicator Bulb, the pull start
    pg = G.Geo()
    pg.add(bevel_box(0.15, 0.85, 1.2, 0.04, c=(0, 0, 0)))
    k.mesh(m, "Panel", "Generator__Panel", pg, base * CF((hx + 0.05, 1.2, 0.25)), "steel_dark", solid=False)
    kn = G.Geo()
    for dz in (0.0, 0.45):
        kn.add(ccyl(0.18, 0.15, 8, "x", (0.08, -0.1, dz), 0.03))
    kn.add(bevel_box(0.15, 0.2, 0.3, 0.03, c=(0.08, 0.25, 0.45)))
    k.mesh(m, "Sockets", "Generator__Sockets", kn, base * CF((hx + 0.05, 1.2, 0.25)), "cream", shadow=False)
    k.mesh(m, "Dial", "Generator__Dial", ccyl(0.2, 0.15, 10, "x", (0.08, 0.2, 0.0), 0.03),
           base * CF((hx + 0.05, 1.2, 0.25)), "paper", shadow=False)
    k.part(m, "Bulb", (0.4, 0.4, 0.4), base * CF((hx + 0.2, 1.25, -0.25)), (120, 30, 24), material="SmoothPlastic",
           shape="Ball", grid=False, shadow=False)
    hd = G.Geo()
    hd.add(bevel_box(0.15, 0.15, 0.6, 0.04, c=(0, 0, 0)))
    hd.add(rod((-0.05, 0, 0), (-0.25, 0, 0), 0.075, 4))
    h = k.mesh(m, "Handle", "Generator__Handle", hd, base * CF((1.45, 0.75, -0.55)), "black", solid=False)
    pivot(h, base * CF((1.45, 0.75, -0.55)))
    moving(m, "Handle", "the recoil starter's T-handle: pull the pivot out along +X (east) about 1.5 and let it "
                        "snap back")
    stand(k, m, -17.4, -34.0, W, y=PAD_Y)
    k.mark_used("Generator", "outside")
    return m


# ---------------------------------------------------------------- dumpster

def _dumpster_body():
    g = G.Geo()
    # a trapezoid body: wider at the top, bevelled
    pts = [(-1.75, 0.0), (1.75, 0.0), (2.05, 2.9), (-2.05, 2.9)]
    body = G.extrude(pts, 6.0, "z", (0, 0, 0))
    g.add(body)
    for z in (-2.2, -0.75, 0.75, 2.2):                               # stiffener ribs round it
        g.add(G.extrude([(-1.85, 0.2), (1.85, 0.2), (2.15, 2.75), (-2.15, 2.75)], 0.3, "z", (0, 0, z)))
    for sx in (-1, 1):                                              # lifting sleeves
        g.add(bevel_box(0.4, 0.6, 5.0, 0.08, c=(sx * 2.1, 2.2, 0)))
    g.add(bevel_box(4.4, 0.25, 6.3, 0.08, c=(0, 2.95, 0)))          # top rim
    return g


def dumpster(k, old):
    """A battered green steel dumpster on casters, its black plastic Lid hinged at the back,
    a dent and rust in a darker green, two wheelie bins beside it, the TrashBag items."""
    m = station(k, "Dumpster")
    cx, cz = 19.9, -31.0
    y0 = 0.0
    base = CF((cx, y0 + 0.55, cz))
    body = k.mesh(m, "Body", "Dumpster__Body", _dumpster_body(), base, "dumpster", solid=True)
    rust = G.Geo()
    for (z, y, w, h) in ((-1.5, 0.6, 1.2, 0.9), (1.4, 1.5, 0.9, 0.7), (2.4, 0.4, 0.8, 0.6)):
        rust.add(chamfer_slab([(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2 + 0.1, h / 2), (-w / 2, h / 2 - 0.1)], 0.15,
                              0.04).xf(G.M(G.rz(90))).xf(G.T(-1.93, y + h / 2, z)))
    k.mesh(m, "Rust", "Dumpster__Rust", rust, base, "dumpster_dark", shadow=False)
    wh = G.Geo()
    for sx in (-1, 1):
        for sz in (-1, 1):
            wh.add(bevel_box(0.4, 0.3, 0.4, 0.06, c=(sx * 1.4, -0.12, sz * 2.4)))
            wh.add(ccyl(0.22, 0.25, 8, "x", (sx * 1.4, -0.33, sz * 2.4), 0.04))
    k.mesh(m, "Wheels", "Dumpster__Wheels", wh, base, "black", solid=True)
    lid = G.Geo()
    lid.add(bevel_box(4.5, 0.3, 6.4, 0.1, c=(0, 0, 0)))
    for z in (-2.0, 0.0, 2.0):
        lid.add(bevel_box(4.3, 0.15, 0.4, 0.05, c=(0, 0.2, z)))
    lid.add(bevel_box(0.3, 0.2, 5.6, 0.06, c=(-2.15, 0.15, 0)))                        # the front lip to lift by
    lp = k.mesh(m, "Lid", "Dumpster__Lid", lid, base * CF((0.0, 3.25, 0.0)), "bin_black", solid=True)
    pivot(lp, base * CF((2.25, 3.2, 0.0)))
    moving(m, "Lid", "hinged along its east (back) edge; rotate the pivot about Z (+ lifts the west lip) up to 100 deg")
    k.sc.attachment(body, "Fx_Flies", base * CF((0.0, 3.8, 0.0)))
    # the wheelie bins, as batch 1 (Models WheelieBin1/2: Body, Lid on a pivot)
    for i, (bx, col) in enumerate(((17.0, "bin_green"), (19.5, "bin_black"))):
        wb = k.sc.model(m, "WheelieBin%d" % (i + 1))
        g = G.Geo()
        g.add(G.extrude([(-0.75, 0.0), (0.75, 0.0), (0.85, 2.6), (-0.85, 2.6)], 1.6, "z", (0, 0, 0)))
        g.add(bevel_box(1.9, 0.2, 0.25, 0.05, c=(0, 2.5, 0.85)))                  # handle bar at the back
        g.add(bevel_box(1.7, 0.25, 1.8, 0.06, c=(0, 2.6, 0)))                     # rim
        k.mesh(wb, "Body", "WheelieBin__Body", g, CF((bx, y0 + 0.3, -26.5)), col, solid=True)
        w2 = G.Geo()
        for sx in (-1, 1):
            w2.add(ccyl(0.3, 0.2, 8, "x", (sx * 0.75, 0.3, 0.7), 0.04))
        k.mesh(wb, "Wheels", "WheelieBin__Wheels", w2, CF((bx, y0, -26.5)), "black", shadow=False)
        lid2 = G.Geo()
        lid2.add(bevel_box(1.85, 0.2, 1.95, 0.06, c=(0, 0, 0)))
        lid2.add(bevel_box(0.8, 0.15, 0.25, 0.04, c=(0, 0.15, -0.9)))
        l2 = k.mesh(wb, "Lid", "WheelieBin__Lid", lid2, CF((bx, y0 + 3.0, -26.5)), col, solid=True)
        pivot(l2, CF((bx, y0 + 3.0, -26.5 + 0.95)))
        k.mark_used("WheelieBin", "outside")
    moving(m, "WheelieBin1/2.Lid", "hinged at the back (+Z edge): rotate the pivot about X to flip it open")
    # the TrashBag items exactly as batch 1 (the game picks them up)
    from .build import _copy_tree
    bags = [c for c in old.root.get("Stations").get("Dumpster").children if c.name == "TrashBag"]
    for tb, (bx, bz) in zip(bags, ((18.0, -35.3), (19.8, -35.6), (21.5, -35.2))):
        new = _copy_tree(tb, m, k.sc, old)
        ref = next(n for n in new.walk() if n.kind == "Attachment" and n.name == "Rest").p["cf"].p
        d = np.array((bx - ref[0], y0 - ref[1], bz - ref[2]))
        for n in new.walk():
            if n.p.get("cf") is not None:
                n.p["cf"] = CF(n.p["cf"].p + d, n.p["cf"].R)
    stand(k, m, 15.8, cz, E, y=y0)
    k.mark_used("Dumpster", "outside")
    return m


# ---------------------------------------------------------------- yard gate

def yard_gate(k):
    """A galvanised tube gate with chain-link and a brace, hung on the west post, a D-latch
    and padlock on the east end. The fence runs on from both posts (yard dressing)."""
    m = station(k, "YardGate")
    z = L.YARD_Z[0] + 0.4                       # the yard's north edge (Z -46.6), on the yard's ground
    y0 = 0.0
    for x in (7.5, 12.5):
        g = G.Geo()
        g.add(ccyl(0.3, 7.0, 10, "y", (0, 3.5, 0), 0.05))
        g.add(cfrustum(0.36, 0.2, 0.3, 10, "y", (0, 7.1, 0), 0.04))
        k.mesh(m, "GatePost", "YardGate__Post", g, CF((x, y0, z)), "galv", solid=True)
        k.mesh(m, "Footing", "YardGate__Footing", ccyl(0.6, 0.3, 10, "y", (0, -0.1, 0), 0.06), CF((x, y0, z)),
               "concrete_dark", solid=True)
    x0, x1 = 7.85, 12.15
    w, h, yb = x1 - x0, 5.4, 0.4
    cx = (x0 + x1) / 2
    fr = G.Geo()
    for y in (0.0, h):
        fr.add(rod((-w / 2, y, 0), (w / 2, y, 0), 0.12, 6))
    for x in (-w / 2, w / 2):
        fr.add(rod((x, 0, 0), (x, h, 0), 0.12, 6))
    gate = k.mesh(m, "Gate", "YardGate__Gate", fr, CF((cx, y0 + yb, z)), "galv", solid=True)
    brace = rod((-w / 2 + 0.15, 0.15, 0), (w / 2 - 0.15, h - 0.15, 0), 0.1, 6)
    b = k.mesh(m, "GateBrace", "YardGate__Brace", brace, CF((cx, y0 + yb, z)), "galv", shadow=False)
    mesh = k.mesh(m, "Mesh", "YardGate__Mesh", O.chainlink(w - 0.3, h - 0.3, 0.9), CF((cx, y0 + yb + h / 2, z - 0.05)),
                  "galv_dark", shadow=False)
    la = G.Geo()
    la.add(bevel_box(0.5, 0.6, 0.3, 0.05, c=(0, 0, 0)))
    la.add(G.torus(0.25, 0.08, 10, 4, "z", (0.35, -0.25, 0.0)))
    latch = k.mesh(m, "Latch", "YardGate__Latch", la, CF((x1 - 0.1, y0 + yb + 3.0, z + 0.2)), "steel_dark",
                   shadow=False)
    pl = G.Geo()
    pl.add(bevel_box(0.4, 0.5, 0.2, 0.06, c=(0, 0, 0)))
    pl.add(G.torus(0.14, 0.075, 8, 4, "z", (0, 0.32, 0)))
    lock = k.mesh(m, "Padlock", "YardGate__Padlock", pl, CF((x1 + 0.27, y0 + yb + 2.45, z + 0.2)), "brass",
                  shadow=False)
    weld_all(k, gate, [b, mesh, latch, lock])
    pivot(gate, CF((x0, y0 + yb, z)))
    moving(m, "Gate", "hinged on the west post: rotate the pivot about Y (+90 swings it into the yard); brace, "
                      "chain-link, latch and padlock are welded to it")
    stand(k, m, 10.0, -44.0, N, y=y0)
    k.mark_used("YardGate", "outside")
    return m


# ---------------------------------------------------------------- street lamp and yard lamp

def street_lamp(k, gr):
    """A galvanised street lamp on the kerb west of the queue: tapered pole on a concrete
    base, the arm curving out over the forecourt, a cobra head with the Bulb (sodium)."""
    m = station(k, "StreetLamp")
    x, z = -9.0, 21.6
    y0 = gr.y(x, z, 0.0)
    k.mesh(m, "Base", "StreetLamp__Base", ccyl(0.75, 0.8, 10, "y", (0, 0.2, 0), 0.08), CF((x, y0, z)), "concrete",
           solid=True)
    k.mesh(m, "Pole", "StreetLamp__Pole", O.flat_pole(11.0, 0.32, 0.2, 10), CF((x, y0 + 0.6, z)), "galv", solid=True)
    arm = G.tube([(0, 11.2, 0), (0, 12.0, -0.6), (0, 12.2, -1.6), (0, 12.05, -2.6), (0, 11.9, -3.0)], 0.15, 8)
    k.mesh(m, "ArmPipe", "StreetLamp__Arm", arm, CF((x, y0, z)), "galv", shadow=False)
    hd = G.Geo()
    hd.add(G.outward(G.lathe([(0.0, -0.35), (0.55, -0.3), (0.7, 0.0), (0.5, 0.3), (0.0, 0.35)], 10, sz=1.6)))
    k.mesh(m, "Head", "StreetLamp__Head", hd, CF((x, y0 + 11.75, z - 3.6)), "galv_dark", solid=False)
    bulb = k.part(m, "Bulb", (1.0, 0.4, 1.6), CF((x, y0 + 11.35, z - 3.6)), "sodium", material="Neon", grid=False,
                  shadow=False)
    k.lamp(m, bulb, "Street", "Spot", 44.0, 2.4, (255, 184, 110), angle=125.0, shadows=True)
    k.sc.attachment(bulb, "Fx_Moths", CF((x, y0 + 10.8, z - 3.6)))
    stand(k, m, -7.0, 20.6, N, y=y0)
    k.mark_used("StreetLamp", "outside")
    return m


def yard_lamp(k, gr):
    """A creosoted pole in the yard with a crossarm and insulators, a floodlight on an arm
    (the Bulb) and the Cable sagging over from the shack's back wall."""
    m = station(k, "YardLamp")
    x, z = 3.0, -27.0
    y0 = gr.y(x, z, 0.0)
    k.mesh(m, "Pole", "YardLamp__Pole", O.flat_pole(13.0, 0.42, 0.3, 10), CF((x, y0 - 0.4, z)), "pole_wood",
           solid=True)
    ca = G.Geo()
    ca.add(bevel_box(4.0, 0.4, 0.4, 0.06, c=(0, 0, 0)))
    for dx in (-1.6, 1.6):
        ca.add(ccyl(0.15, 0.4, 8, "y", (dx, 0.4, 0), 0.03))
        ca.add(ccyl(0.22, 0.3, 8, "y", (dx, 0.65, 0), 0.04))
    k.mesh(m, "CrossArm", "YardLamp__CrossArm", ca, CF((x, y0 + 11.6, z)), "pole_wood_dark", shadow=False)
    k.mesh(m, "Insulators", "YardLamp__Insulators", ccyl(0.2, 0.3, 8, "y", (0, 0, 0), 0.04),
           CF((x - 1.6, y0 + 12.4, z)), "insulator", shadow=False)
    arm = G.Geo()
    arm.add(rod((0, 0, 0.35), (0, 0.0, 1.8), 0.12, 6))
    arm.add(rod((0, -0.8, 0.35), (0, 0.0, 1.2), 0.1, 6))
    k.mesh(m, "Arm", "YardLamp__Arm", arm, CF((x, y0 + 10.2, z)), "galv_dark", shadow=False)
    hd = G.Geo()
    hd.add(bevel_box(1.6, 0.8, 1.2, 0.12, c=(0, 0.0, 0)))
    hd.add(bevel_box(1.7, 0.15, 1.3, 0.04, c=(0, 0.45, 0)))
    k.mesh(m, "Head", "YardLamp__Head", hd.xf(G.M(G.rx(-25))), CF((x, y0 + 10.0, z + 2.3)), "grey_dark")
    bulb = k.part(m, "Bulb", (1.2, 0.2, 0.8), CF((x, y0 + 9.6, z + 2.45), G.rx(-25)), (255, 236, 200),
                  material="Neon", grid=False, shadow=False)
    k.lamp(m, bulb, "Shack", "Spot", 46.0, 2.2, (255, 226, 180), angle=120.0, shadows=True)
    k.sc.attachment(bulb, "Fx_Moths", CF((x, y0 + 9.2, z + 2.6)))
    # the cable from the shack's back wall (a bracket under the parapet) to the pole
    p0 = np.array((-2.0, 9.8, L.OUT_Z0 - 0.6))
    p1 = np.array((x - 0.2, y0 + 10.4, z + 0.45))
    k.mesh(m, "Cable", "YardLamp__Cable", O.catenary(p0, p1, 1.1, 0.08, 14), CF(), "black", shadow=False)
    k.mesh(m, "CableHook", "YardLamp__Hook", rod((0, 0, 0), (0, 0, -0.6), 0.1, 6), CF((p0[0], p0[1], L.OUT_Z0)),
           "steel_dark", shadow=False)
    stand(k, m, 1.5, -24.0, N, y=y0)
    k.mark_used("YardLamp", "outside")
    return m


def build(k, old, gr):
    return [generator(k, gr), dumpster(k, old), yard_gate(k), street_lamp(k, gr), yard_lamp(k, gr)]
