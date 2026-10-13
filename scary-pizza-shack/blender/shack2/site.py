"""The ground round the shack, dressed: cracks, oil and puddles on the forecourt, the
parking bays with their wheel stops and the old pickup that has not moved in years, the
picnic table, payphone, news box, ice chest and the lit vending machine, the lot lamp, and
the yard: chain-link fence with one sagging panel, the generator's lean-to, worn dirt paths,
the extension lead, pallets, crates, tyres, the broken chair, the dog's bowl and chain."""
import math

import numpy as np

import spsgeo as G
from spsgeo import CF

from . import layout as L, outkit as O
from .kit import bevel_box, ccyl, cfrustum, chamfer_slab, irregular, rod
from .st_common import FACE, board


def yaw_to(dx, dz):
    """The rotation turning a prop's +Z (its front) towards (dx, dz)."""
    return G.ry(math.degrees(math.atan2(dx, dz)))


# ---------------------------------------------------------------- forecourt and lot

def forecourt(k, f, gr, rng):
    m = k.sc.model(f, "ForecourtDressing")
    # cracks: dark joints wandering across the slabs, let into them
    cracks = G.Geo()
    for (x0, z0, ang, ln) in ((-27.5, 12.2, -5, 5.0), (-8.0, 18.5, -35, 6.0), (2.5, 15.0, 70, 5.0), (12.0, 19.5, 5, 8.0),
                              (-16.0, 20.2, -10, 5.0), (17.0, 13.5, 50, 4.0)):
        pts = [(0.0, 0.0)]
        for i in range(4):
            pts.append((pts[-1][0] + ln / 4, pts[-1][1] + float(rng.uniform(-0.6, 0.6))))
        path = [(x0 + px * math.cos(math.radians(ang)) - pz * math.sin(math.radians(ang)), -0.02,
                 z0 + px * math.sin(math.radians(ang)) + pz * math.cos(math.radians(ang))) for (px, pz) in pts]
        cracks.add(G.tube(path, 0.12, 4))
    k.mesh(m, "Cracks", "Site__Cracks", cracks, CF(), "tar", shadow=False)
    for (x, z, s) in ((-6.0, 16.5, 1), (8.0, 18.0, 2), (-20.0, 19.0, 3)):
        k.prop(m, "OilStain", CF((x, 0.0, z), G.ry(rng.uniform(0, 360))), where="outside", name="OilStain", seed=s)
    for i, (x, z) in enumerate(L.PUDDLES):
        k.prop(m, "Puddle", CF((x, gr.y(x, z), z), G.ry(rng.uniform(0, 360))), where="outside", name="Puddle", seed=i)
    fp = L.FORECOURT_PROPS
    face_road = G.ry(0)
    k.prop(m, "PicnicTable", CF((fp["PicnicTable"][0], 0.0, fp["PicnicTable"][1]), G.ry(8)), where="outside",
           name="PicnicTable")
    k.prop(m, "Litter", CF((fp["PicnicTable"][0] + 2.5, 0.0, fp["PicnicTable"][1] + 3.0)), where="outside",
           name="Litter", seed=5)
    py = CF((fp["Payphone"][0], 0.0, fp["Payphone"][1]), face_road)
    k.prop(m, "Payphone", py, where="outside", name="Payphone")
    board(k, m.get("Payphone"), (1.5, 0.45, 0.15), py * CF((0, 6.65, 0.9), G.ry(180)), "label_blue",
          text="PHONE", text_color=(250, 250, 250), name="Sign")
    nb = CF((fp["NewsBox"][0], 0.0, fp["NewsBox"][1]), face_road)
    nbm = k.prop(m, "NewsBox", nb, where="outside", name="NewsBox")
    from .opens import from_prop, stash
    from_prop(k, nbm, "Door", ["DoorFrame", "Window"], nb * CF((0, 1.72, 0.7)), "Swing", "Metal", angle=75.0,
              axis="X")
    stash(k, nbm, nb * CF((0, 1.75, 0.0), G.facing((0, 0, 1))), (1.2, 1.0, 1.0), behind="Door")
    board(k, m.get("NewsBox"), (1.6, 0.4, 0.15), nb * CF((0, 3.42, 0.6), G.ry(180)), "label_white",
          text="THE GAZETTE", text_color=(30, 40, 90), name="Masthead")
    ic = CF((fp["IceChest"][0], 0.0, fp["IceChest"][1] + 1.0), face_road)      # its lid clear of the menu board
    icm = k.prop(m, "IceChest", ic, where="outside", name="IceChest")
    from_prop(k, icm, "Lid", ["Lid"], ic * CF((0, 3.05, -0.95)), "Swing", "Lid", angle=-90.0, axis="X")
    stash(k, icm, ic * CF((1.2, 2.2, 0.3), G.facing((0, 0, 1))), (1.0, 0.5, 0.9), behind="Lid")
    board(k, m.get("IceChest"), (2.2, 0.5, 0.15), ic * CF((0, 2.1, 1.01), G.ry(180)), "label_blue", text="ICE",
          text_color=(250, 250, 250), name="Sign")
    vm = CF((fp["Vending"][0], 0.0, fp["Vending"][1] + 0.6), face_road)
    k.prop(m, "VendingMachine", vm, where="outside", name="VendingMachine")
    board(k, m.get("VendingMachine"), (1.7, 0.7, 0.15), vm * CF((-0.4, 5.55, 1.29), G.ry(180)), "vending_red",
          text="ICE COLD", text_color=(250, 240, 220), name="Header")
    lamp = k.sc.model(m.get("VendingMachine"), "Glow")
    b = k.part(lamp, "Bulb", (1.4, 3.6, 0.15), vm * CF((-0.4, 3.6, 1.15)), (255, 240, 220), material="Neon",
               grid=False, shadow=False, transparency=1.0)
    k.lamp(lamp, b, "Shack", "Surface", 10.0, 0.9, (240, 236, 255), face="Front", shadows=False)
    k.sc.attachment(b, "Fx_Moths", vm * CF((-0.4, 5.0, 2.0)))
    k.prop(m, "PlanterBarrel", CF((5.9, 0.0, 12.9)), where="outside", name="Planter")


def lot(k, f, gr, rng):
    """The side lot: faded bay lines, wheel stops, oil in bay A, the old pickup in bay B."""
    m = k.sc.model(f, "LotDressing")
    lines = G.Geo()
    for x in (24.0, 34.0, 44.0):
        for z0 in np.arange(-6.0, 12.0, 3.0):
            if rng.random() < 0.8:
                lines.add(bevel_box(0.4, 0.15, 2.6 - float(rng.uniform(0, 0.8)), 0.03, c=(x, 0.0, z0 + 1.3)))
    lines.add(bevel_box(20.4, 0.15, 0.4, 0.03, c=(34.0, 0.0, -6.2)))
    k.mesh(m, "BayLines", "Site__BayLines", lines, CF(), "line_white", shadow=False)
    for (x, s) in ((29.0, 1), (39.0, 2)):
        k.prop(m, "WheelStop", CF((x, 0.0, -4.6)), where="outside", name="WheelStop", seed=s)
    for i, (x, z) in enumerate(((29.0, -1.0), (27.5, 3.5), (30.5, 7.0))):
        k.prop(m, "OilStain", CF((x, 0.0, z), G.ry(40 * i)), where="outside", name="OilStain", seed=10 + i)
    pickup(k, m, L.PICKUP["x"], L.PICKUP["z"])
    lot_lamp(k, m, gr)


def pickup(k, parent, x, z):
    """An old pickup, nose in, that has not moved in years: faded blue, rust on the sills,
    one flat tyre (it lists), a tarp in the bed, leaves on the windscreen, weeds round it."""
    m = k.sc.model(parent, "Pickup")
    base = CF((x, 0.0, z), G.ry(180) @ G.rz(1.2))                 # faces north (nose to the bay's head); lists
    body = G.Geo()
    body.add(bevel_box(6.6, 1.6, 16.0, 0.3, c=(0, 2.0, 0)))                      # chassis and sills
    body.add(bevel_box(6.8, 1.4, 5.4, 0.35, c=(0, 3.4, 5.1)))                    # bonnet
    body.add(bevel_box(6.6, 2.6, 4.2, 0.35, c=(0, 4.1, 0.6)))                    # cab
    for sx in (-1, 1):
        body.add(bevel_box(0.4, 1.6, 7.0, 0.1, c=(sx * 3.1, 3.4, -4.4)))         # bed sides
    body.add(bevel_box(6.6, 1.6, 0.4, 0.1, c=(0, 3.4, -7.8)))                    # tailgate
    for (sx, sz) in ((-1, 1), (1, 1), (-1, -1), (1, -1)):
        body.add(G.outward(G.lathe([(0.0, 0.0), (1.55, 0.0), (1.7, 0.6), (1.6, 1.2), (0.0, 1.25)], 10))
                 .xf(G.M(G.rz(90 * sx))).xf(G.T(sx * 3.2, 1.9, sz * 5.0)))       # wheel arches
    k.mesh(m, "Body", "Pickup__Body", body, base, "pickup_blue", solid=True)
    win = G.Geo()
    win.add(bevel_box(5.8, 1.6, 0.15, 0.06, c=(0, 4.6, 2.75)).xf(G.M(G.rx(-18))))
    win.add(bevel_box(5.8, 1.3, 0.15, 0.06, c=(0, 4.7, -1.45)))
    for sx in (-1, 1):
        win.add(bevel_box(0.15, 1.3, 3.2, 0.06, c=(sx * 3.32, 4.7, 0.6)))
    k.mesh(m, "Windows", "Pickup__Windows", win, base, "glass", material="Glass", transparency=0.45, shadow=False)
    chrome = G.Geo()
    for sz in (-1, 1):
        chrome.add(bevel_box(7.0, 0.7, 0.5, 0.15, c=(0, 1.3, sz * 8.1)))
    chrome.add(bevel_box(4.6, 0.9, 0.2, 0.08, c=(0, 3.1, 7.85)))                 # grille
    k.mesh(m, "Chrome", "Pickup__Chrome", chrome, base, "chrome", shadow=False)
    lamps = G.Geo()
    for sx in (-1, 1):
        lamps.add(ccyl(0.4, 0.2, 10, "z", (sx * 2.6, 3.1, 7.95), 0.05))
    k.mesh(m, "Headlamps", "Pickup__Lamps", lamps, base, "cream", shadow=False)
    tail = G.Geo()
    for sx in (-1, 1):
        tail.add(bevel_box(0.5, 0.8, 0.15, 0.04, c=(sx * 2.9, 3.4, -8.05)))
    k.mesh(m, "TailLamps", "Pickup__Tail", tail, base, "red_dark", shadow=False)
    rust = G.Geo()
    for (sx, sz, w) in ((-1, 3.5, 2.0), (1, -2.0, 1.4), (-1, -6.0, 1.6)):
        rust.add(bevel_box(0.15, 0.7, w, 0.04, c=(sx * 3.32, 1.6, sz)))
    k.mesh(m, "Rust", "Pickup__Rust", rust, base, "rust", shadow=False)
    wh = G.Geo()
    flat = G.Geo()
    for (sx, sz) in ((-1, 5.0), (1, 5.0), (-1, -5.0), (1, -5.0)):
        tyre = G.torus(1.05, 0.55, 12, 6, "x", (sx * 3.0, 1.6, sz))
        if (sx, sz) == (1, -5.0):
            flat.add(tyre.xf(G.T(-sx * 3.0, -1.6, -sz)).xf(G.M(np.diag((1.0, 0.72, 1.12)))).xf(G.T(sx * 3.0, 1.15, sz)))
        else:
            wh.add(tyre)
    hubs = G.Geo()
    for (sx, sz) in ((-1, 5.0), (1, 5.0), (-1, -5.0), (1, -5.0)):
        hubs.add(ccyl(0.6, 0.5, 10, "x", (sx * 3.05, 1.6 if (sx, sz) != (1, -5.0) else 1.2, sz), 0.06))
    k.mesh(m, "Tyres", "Pickup__Tyres", wh, base, "tyre", solid=False)
    k.mesh(m, "FlatTyre", "Pickup__FlatTyre", flat, base, "tyre", shadow=False)
    k.mesh(m, "Hubs", "Pickup__Hubs", hubs, base, "steel_dark", shadow=False)
    k.prop(m, "Tarp", base * CF((0, 2.8, -4.4), G.ry(90)), where="outside", name="BedTarp", seed=3)
    leaves = G.Geo()
    for i in range(6):
        leaves.add(bevel_box(0.4, 0.15, 0.3, 0.04, c=(-2.2 + 0.8 * i, 0, 0.1 * (i % 2))).xf(G.M(G.ry(30 * i))))
    k.mesh(m, "Leaves", "Pickup__Leaves", leaves.xf(G.M(G.rx(-18))).xf(G.T(0, 3.9, 3.1)), base, "litter",
           shadow=False)
    for (sx, sz) in ((-1, 5.0), (1, -5.0)):
        p = base * CF((sx * 4.5, 0.0, sz))
        k.prop(m, "Weeds", p, where="outside", name="Weeds", seed=int(abs(sz)) + (1 if sx > 0 else 0))
    k.mark_used("Pickup", "outside")


def lot_lamp(k, parent, gr):
    """A tall lamp at the lot's east edge with a single head over the bays."""
    m = k.sc.model(parent, "LotLamp")
    x, z = 47.0, 6.0
    y0 = gr.y(x, z)
    k.mesh(m, "Base", "LotLamp__Base", ccyl(0.7, 0.8, 10, "y", (0, 0.2, 0), 0.08), CF((x, y0, z)), "concrete",
           solid=True)
    k.mesh(m, "Pole", "LotLamp__Pole", O.flat_pole(15.0, 0.3, 0.2, 10), CF((x, y0 + 0.6, z)), "galv", solid=True)
    arm = G.tube([(0, 15.2, 0), (-0.8, 16.0, 0), (-2.6, 16.1, 0), (-3.4, 15.9, 0)], 0.15, 8)
    k.mesh(m, "ArmPipe", "LotLamp__Arm", arm, CF((x, y0, z)), "galv", shadow=False)
    hd = G.outward(G.lathe([(0.0, -0.3), (0.6, -0.25), (0.75, 0.0), (0.5, 0.3), (0.0, 0.35)], 10, sx=1.5))
    k.mesh(m, "Head", "LotLamp__Head", hd, CF((x - 3.9, y0 + 15.8, z)), "galv_dark")
    bulb = k.part(m, "Bulb", (1.6, 0.4, 1.0), CF((x - 3.9, y0 + 15.45, z)), "sodium", material="Neon", grid=False,
                  shadow=False)
    k.lamp(m, bulb, "Street", "Spot", 50.0, 2.4, (255, 184, 110), angle=125.0)
    k.sc.attachment(bulb, "Fx_Moths", CF((x - 3.9, y0 + 14.9, z)))
    k.mark_used("LotLamp", "outside")


# ---------------------------------------------------------------- the yard

FENCE_H = 5.6


def _fence_run(k, m, a, b, gr, sag_panel=None, name="Fence", skip=()):
    """A chain-link run from a to b (x, z): galvanised posts about every 6, a top rail, the
    mesh between, tension wire at the foot. sag_panel = index of a panel that sags."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    ln = float(np.linalg.norm(b - a))
    n = max(1, int(round(ln / 6.0)))
    d = (b - a) / ln
    ang = math.degrees(math.atan2(-d[1], d[0]))
    posts, rail, meshg = G.Geo(), G.Geo(), G.Geo()
    for i in range(n + 1):
        if (i == 0 and "start" in skip) or (i == n and "end" in skip):
            continue                                       # the gate post stands there instead
        p = a + (b - a) * i / n
        y = gr.y(p[0], p[1])
        posts.add(ccyl(0.2, FENCE_H + 0.4, 8, "y", (p[0], y + (FENCE_H + 0.4) / 2 - 0.2, p[1]), 0.04))
        posts.add(cfrustum(0.26, 0.15, 0.25, 8, "y", (p[0], y + FENCE_H + 0.3, p[1]), 0.03))
    pw = ln / n
    for i in range(n):
        p = a + (b - a) * (i + 0.5) / n
        y = gr.y(p[0], p[1])
        sag = i == sag_panel
        top = FENCE_H - (0.9 if sag else 0.0)
        R = G.ry(ang)
        cl = O.chainlink(pw - 0.4, top - 0.4, 0.9)
        if sag:
            cl = cl.xf(G.M(G.rx(-9)))
        meshg.add(cl.xf(G.M(R)).xf(G.T(p[0], y + top / 2 + 0.05, p[1])))
        p0, p1 = a + (b - a) * i / n, a + (b - a) * (i + 1) / n
        if sag:
            mid = (p0 + p1) / 2
            rail.add(G.tube([(p0[0], y + FENCE_H - 0.1, p0[1]), (mid[0], y + FENCE_H - 1.0, mid[1]),
                             (p1[0], y + FENCE_H - 0.1, p1[1])], 0.12, 6))
        else:
            rail.add(rod((p0[0], y + FENCE_H - 0.1, p0[1]), (p1[0], y + FENCE_H - 0.1, p1[1]), 0.12, 6))
        rail.add(rod((p0[0], y + 0.25, p0[1]), (p1[0], y + 0.25, p1[1]), 0.075, 4))
    k.mesh(m, name + "Posts", "Yard__%sPosts%d" % (name, len(m.children)), posts, CF(), "galv", solid=False)
    k.mesh(m, name + "Rail", "Yard__%sRail%d" % (name, len(m.children)), rail, CF(), "galv", shadow=False)
    k.mesh(m, name + "Mesh", "Yard__%sMesh%d" % (name, len(m.children)), meshg, CF(), "galv_dark", shadow=False)
    # one invisible blocker for the whole run (the mesh pieces don't collide)
    c = (a + b) / 2
    y = gr.y(c[0], c[1])
    k.part(m, "Blocker", (ln, FENCE_H, 0.4), CF((c[0], y + FENCE_H / 2, c[1]), G.ry(ang)), "galv",
           transparency=1.0, solid=True, grid=False, shadow=False)


def yard(k, f, gr, rng):
    m = k.sc.model(f, "YardDressing")
    x0, x1 = L.YARD_X
    z0, z1 = L.YARD_Z
    g0, g1 = 7.5, 12.5                                    # the gate posts
    zf = z0 + 0.4                                         # on the yard's own ground
    _fence_run(k, m, (x0 + 0.4, zf), (g0 - 0.3, zf), gr, skip=("end",))
    _fence_run(k, m, (g1 + 0.3, zf), (x1 - 0.4, zf), gr, skip=("start",))
    _fence_run(k, m, (x0 + 0.4, zf), (x0 + 0.4, z1 - 4.0), gr, sag_panel=2)
    _fence_run(k, m, (x1 - 0.4, zf), (x1 - 0.4, z1 - 4.0), gr)
    _fence_run(k, m, (x0 + 0.4, z1 - 4.0), (-26.6, z1 - 4.0), gr)  # side returns (a walk-round gap by the shack)
    _fence_run(k, m, (24.5, z1 - 4.0), (x1 - 0.4, z1 - 4.0), gr)
    shed(k, m, gr)
    yp = L.YARD_PROPS
    for i, dz in enumerate((0.0, 0.62, 1.24)):
        k.prop(m, "Pallet", CF((24.5, dz, -43.5), G.ry(4 * i)), where="outside", name="Pallet")
    k.prop(m, "Pallet", CF((19.0, 0.0, -43.8), G.ry(23)), where="outside", name="Pallet")
    for i, (x, y, z) in enumerate(((21.8, 0.0, -38.6), (24.4, 0.0, -38.3), (23.1, 2.05, -38.5))):
        k.prop(m, "Crate", CF((x, y, z), G.ry(4 * i)), where="outside", name="Crate", seed=i)
    k.prop(m, "TyreStack", CF((yp["Tyres"][0], 0.0, yp["Tyres"][1])), where="outside", name="Tyres")
    k.prop(m, "BrokenChair", CF((-4.5, 0.0, -17.5), G.ry(35)), where="outside",
           name="BrokenChair")
    k.prop(m, "DogBowl", CF((yp["DogBowl"][0], 0.0, yp["DogBowl"][1]), G.ry(-20)), where="outside", name="DogBowl")
    for i, (dx, dz) in enumerate(((0.0, 0.0), (1.1, 0.3), (0.5, 1.2))):
        k.prop(m, "FuelCan", CF((yp["FuelCans"][0] + dx, 0.0, yp["FuelCans"][1] + dz), G.ry(15 * i)), where="outside",
               name="FuelCan")
    k.prop(m, "OilDrum", CF((-16.5, 0.4, -39.2)), where="outside", name="OilDrum")
    k.prop(m, "Wheelbarrow", CF((15.5, 0.0, -40.5), G.ry(-30)), where="outside", name="Wheelbarrow")
    k.prop(m, "Tarp", CF((-22.0, 0.0, -20.0), G.ry(10)), where="outside", name="Tarp", seed=8)
    k.prop(m, "Cone", CF((13.6, 0.0, -44.6)), where="outside", name="Cone")
    for i in range(14):
        side = i % 3
        if side == 0:
            p = (x0 + 2.6, float(rng.uniform(z0 + 3, z1 - 6)))
        elif side == 1:
            p = (x1 - 2.6, float(rng.uniform(z0 + 3, z1 - 6)))
        else:
            p = (float(rng.uniform(x0 + 3, x1 - 3)), z0 + 2.6)
            if g0 - 1 < p[0] < g1 + 1:
                continue
        if L.SHED[0] - 2.5 < p[0] < L.SHED[1] + 2.5 and L.SHED[2] - 2.5 < p[1] < L.SHED[3] + 2.5:
            continue
        if p[0] > 14 and p[1] < -33:                  # the pallets and crates corner
            continue
        k.prop(m, "Weeds", CF((p[0], 0.0, p[1]), G.ry(rng.uniform(0, 360))), where="outside", name="Weeds", seed=i)
    paths(k, m, rng)
    ruts(k, m, rng)
    for i, (x, z) in enumerate(((7.9, -27.5), (12.1, -39.0))):
        k.prop(m, "Puddle", CF((x, 0.03, z), G.ry(90 + 8 * i)), where="outside", name="Puddle", seed=40 + i)
    for i, (x, z) in enumerate(((-8.5, -31.0), (-2.0, -40.5), (1.5, -34.0), (-12.5, -44.0), (-22.0, -33.5),
                                (19.5, -27.0), (24.0, -22.5), (-5.5, -22.5))):
        k.prop(m, "Stones", CF((x, 0.0, z), G.ry(37 * i)), where="outside", name="Stones", seed=60 + i)
    lead(k, m)
    k.mark_used("ChainLinkFence", "outside")


def shed(k, parent, gr):
    """The generator's lean-to: a concrete pad, timber posts, a plank back wall and half
    walls, a corrugated roof falling to the east, a bench with an oil can and rags."""
    m = k.sc.model(parent, "GeneratorShed")
    x0, x1, z0, z1 = L.SHED
    k.mesh(m, "Pad", "Shed__Pad", bevel_box(x1 - x0, 0.8, z1 - z0, 0.1), CF(((x0 + x1) / 2, 0.0, (z0 + z1) / 2)),
           "concrete_dark", solid=True)
    posts = G.Geo()
    hb, hf = 8.2, 6.6                                     # roof height at the back (west) and front (east)
    for x, h in ((x0 + 0.4, hb), (x1 - 0.4, hf)):
        for z in (z0 + 0.4, (z0 + z1) / 2, z1 - 0.4):
            posts.add(bevel_box(0.6, h, 0.6, 0.06, c=(x, 0.4 + h / 2, z)))
    k.mesh(m, "Posts", "Shed__Posts", posts, CF(), "wood_dark", solid=False)
    for x, h in ((x0 + 0.4, hb), (x1 - 0.4, hf)):
        for z in (z0 + 0.4, (z0 + z1) / 2, z1 - 0.4):
            k.part(m, "PostBlock", (1, 4, 1), CF((x, 2.4, z)), "wood_dark", transparency=1.0, solid=True, shadow=False)
    planks = G.Geo()
    for i, z in enumerate(np.arange(z0 + 0.4, z1 - 0.3, 0.9)):
        planks.add(bevel_box(0.3, hb - 0.2 - 0.2 * (i % 3 == 1), 0.85, 0.05, c=(x0 + 0.15, 0.4 + (hb - 0.2) / 2, z + 0.45)))
    for i, x in enumerate(np.arange(x0 + 0.8, x1 - 0.5, 0.9)):
        planks.add(bevel_box(0.85, 3.4, 0.3, 0.05, c=(x + 0.45, 0.4 + 1.7, z0 + 0.15)))
    k.mesh(m, "Planks", "Shed__Planks", planks, CF(), "wood", solid=True)
    w, d = x1 - x0 + 1.4, z1 - z0 + 1.2
    tilt = math.degrees(math.atan2(hb - hf, x1 - x0))
    roof = O.corrugated(d, w, 0.8, 0.15).xf(G.M(G.ry(90))).xf(G.M(G.rz(-tilt)))
    k.mesh(m, "Roof", "Shed__Roof", roof, CF(((x0 + x1) / 2, 0.4 + (hb + hf) / 2 + 0.1, (z0 + z1) / 2)), "galv_dark",
           solid=True)
    bench = G.Geo()
    bench.add(bevel_box(1.6, 0.3, 5.0, 0.05, c=(x0 + 1.2, 3.4, (z0 + z1) / 2 - 2.5)))
    for dz in (-4.6, -0.4):
        bench.add(bevel_box(1.2, 3.0, 0.3, 0.04, c=(x0 + 1.2, 1.9, (z0 + z1) / 2 + dz)))
    k.mesh(m, "Bench", "Shed__Bench", bench, CF(), "wood_light", solid=True)
    k.prop(m, "FuelCan", CF((x0 + 1.4, 3.55, (z0 + z1) / 2 - 1.6), G.ry(80)), where="outside", name="FuelCan")
    k.prop(m, "CableReel", CF((x0 + 4.2, 0.4, z1 - 2.2), G.ry(30)), where="outside", name="CableReel")
    k.mark_used("GeneratorShed", "outside")


def paths(k, m, rng):
    """Worn dirt paths: back door to the shed, back door to the gate. Each is one ragged
    strip, wider where people stop, worn into the gravel (a plate let in, 0.03 proud)."""
    for i, pts in enumerate(([(-17.0, -12.8), (-17.4, -17.0), (-18.0, -22.5), (-17.0, -27.0)],
                             [(-14.0, -13.2), (-7.0, -19.0), (-1.0, -24.0), (2.8, -27.2)])):   # to the drive
        P = np.asarray(pts, float)
        left, right = [], []
        for j in range(len(P) - 1):
            a, b = P[j], P[j + 1]
            d = (b - a) / np.linalg.norm(b - a)
            nrm = np.array((-d[1], d[0]))
            for t in np.linspace(0.0, 1.0, 4, endpoint=(j == len(P) - 2)):
                q = a + (b - a) * t
                w = 1.3 + 0.35 * math.sin(3.1 * (j + t) + i) + float(rng.uniform(-0.15, 0.15))
                left.append(q + nrm * w)
                right.append(q - nrm * w * float(rng.uniform(0.85, 1.1)))
        outline = [tuple(p) for p in left] + [tuple(p) for p in right[::-1]]
        g = chamfer_slab(outline, 0.15, 0.05).xf(G.T(0, -0.12, 0))
        k.mesh(m, "Path", "Yard__Path%d" % i, g, CF(), ("mud", "dirt")[i % 2], shadow=False)


def ruts(k, m, rng):
    """Two wheel ruts worn into the drive from the gate up to the apron, mud in the bottom."""
    from .terrain import YARD_APRON, YARD_DRIVE
    xc = (YARD_DRIVE[0] + YARD_DRIVE[1]) / 2
    za, zb = L.YARD_Z[0] + 0.6, L.YARD_Z[1] - YARD_APRON - 0.4
    for i, dx in enumerate((-2.1, 2.1)):
        zs = np.linspace(za, zb, 12)
        left, right = [], []
        for j, z in enumerate(zs):
            x = xc + dx + 0.25 * math.sin(z * 0.21 + i)
            w = 0.45 + 0.08 * math.sin(z * 0.5 + 2 * i) + float(rng.uniform(-0.04, 0.04))
            left.append((x - w, z))
            right.append((x + w, z))
        outline = left + right[::-1]
        g = chamfer_slab(outline, 0.15, 0.05).xf(G.T(0, -0.12, 0))
        k.mesh(m, "Rut", "Yard__Rut%d" % i, g, CF(), "mud", shadow=False)


def lead(k, m):
    """The extension lead from the reel by the generator across the yard to the back wall,
    lying on the ground, kinked."""
    pts = [(-23.0, 0.12, -29.8), (-19.0, 0.12, -26.5), (-17.5, 0.12, -22.0), (-14.0, 0.12, -18.0),
           (-11.0, 0.12, -14.5), (-9.5, 0.12, -12.6), (-9.5, 1.0, SZ0() - 0.62)]
    lead = G.Geo()                                    # one rod a stretch, so each stretch is its own piece
    for a, b in zip(pts, pts[1:]):
        lead.add(rod(a, b, 0.1, 5))
    k.mesh(m, "LeadCable", "Yard__Lead", lead, CF(), "mustard", shadow=False)


def SZ0():
    return L.OUT_Z0 - 0.5


def build(k, sc):
    gr = sc.kit_ground
    rng = np.random.default_rng(31)
    f = sc.folder(sc.root.get("Outside"), "Site")
    forecourt(k, f, gr, rng)
    lot(k, f, gr, rng)
    yard(k, f, gr, rng)
    return f
