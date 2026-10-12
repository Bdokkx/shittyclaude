"""The roadside stations, rebuilt with batch 1's names, markers and pivots: the BusStop
(moved east past the lot, its markers with it) and the RoadSign with the pizza-slice
mascot, plus the four CCTV cameras behind the Cam_ markers."""
import math

import numpy as np

import spsgeo as G
from spsgeo import CF

from . import layout as L, outkit as O
from .kit import bevel_box, ccyl, cfrustum, chamfer_slab, rod
from .st_common import E, FACE, N, S_, W, board, moving, pivot, stand, station, weld_all

BX0, BX1 = 50.0, 56.0          # the bus shelter
BZ0, BZ1 = 19.0, 21.4


def _pad(k, m, gr, x0, x1, z0, z1, name="Pad", color="concrete"):
    y = max(gr.y(x, z) for x in (x0, x1) for z in (z0, z1))
    k.mesh(m, name, "BusStop__%s" % name, bevel_box(x1 - x0, 0.8, z1 - z0, 0.1), CF(((x0 + x1) / 2, y, (z0 + z1) / 2)),
           color, solid=True)
    return y + 0.4


# ---------------------------------------------------------------- bus stop

def bus_stop(k, gr):
    """A steel bus shelter on a concrete pad: four posts, a sloping roof with a fascia, a
    glass back and west side, a wooden bench, the flickering tube Light under the roof, the
    timetable, a lit advert box at the east end, a litter bin on a post, and the BUS STOP
    flag at the kerb."""
    m = station(k, "BusStop")
    y = _pad(k, m, gr, BX0 - 0.5, BX1 + 2.2, BZ0 - 0.5, BZ1 + 0.3)
    xc = (BX0 + BX1) / 2
    for x in (BX0 + 0.2, BX1 - 0.2):
        for z in (BZ0 + 0.2, BZ1 - 0.2):
            k.mesh(m, "Post", "BusStop__Post", bevel_box(0.3, 7.0, 0.3, 0.05), CF((x, y + 3.5, z)), "shelter",
                   solid=True)
    roof = G.Geo()
    roof.add(bevel_box(BX1 - BX0 + 0.8, 0.3, BZ1 - BZ0 + 0.8, 0.08))
    roof.add(bevel_box(BX1 - BX0 + 0.9, 0.6, 0.2, 0.05, c=(0, -0.15, (BZ1 - BZ0) / 2 + 0.4)))   # fascia
    k.mesh(m, "Roof", "BusStop__Roof", roof, CF((xc, y + 7.15, (BZ0 + BZ1) / 2), G.rx(-4)), "shelter", solid=True)
    board(k, m, (3.0, 0.45, 0.15), CF((xc, y + 6.95, BZ1 + 0.62), FACE["N"]), "red", text="BUS SHELTER",
          text_color=(250, 240, 220), name="Fascia")
    # glass back and side, in thin frames
    gl = dict(material="Glass", transparency=0.55, grid=False, shadow=False)
    k.part(m, "BackPanel", (BX1 - BX0 - 0.4, 5.0, 0.15), CF((xc, y + 3.6, BZ0 + 0.2)), "glass", solid=True, **gl)
    k.part(m, "SidePanel", (0.15, 5.0, BZ1 - BZ0 - 0.4), CF((BX0 + 0.2, y + 3.6, (BZ0 + BZ1) / 2)), "glass", solid=True,
           **gl)
    fr = G.Geo()
    for yy in (1.05, 6.15):
        fr.add(bevel_box(BX1 - BX0 - 0.4, 0.2, 0.2, 0.04, c=(xc, y + yy, BZ0 + 0.2)))
        fr.add(bevel_box(0.2, 0.2, BZ1 - BZ0 - 0.4, 0.04, c=(BX0 + 0.2, y + yy, (BZ0 + BZ1) / 2)))
    k.mesh(m, "Frames", "BusStop__Frames", fr, CF(), "shelter", shadow=False)
    k.mesh(m, "Sticker", "BusStop__Sticker", bevel_box(0.6, 0.6, 0.15, 0.03, c=(0, 0, 0)),
           CF((BX1 - 1.4, y + 2.6, BZ0 + 0.35)), "mustard", shadow=False)
    # bench
    be = G.Geo()
    for i in range(3):
        be.add(bevel_box(4.2, 0.15, 0.3, 0.04, c=(0, 0, -0.35 + 0.35 * i)))
    be.add(bevel_box(4.2, 0.3, 0.15, 0.04, c=(0, 0.45, -0.55)))
    k.mesh(m, "Seat", "BusStop__Seat", be, CF((xc, y + 1.6, BZ0 + 0.9)), "wood", solid=True)
    legs = G.Geo()
    for dx in (-1.6, 1.6):
        legs.add(bevel_box(0.2, 1.5, 0.9, 0.04, c=(dx, 0.75, 0)))
    k.mesh(m, "SeatLeg", "BusStop__Legs", legs, CF((xc, y, BZ0 + 0.9)), "shelter", solid=True)
    # the tube light under the roof (Model "Light" holding its Bulb)
    lm = k.sc.model(m, "Light")
    k.mesh(lm, "Housing", "BusStop__LightBox", bevel_box(3.6, 0.3, 0.6, 0.06), CF((xc, y + 6.87, (BZ0 + BZ1) / 2)),
           "grey_light", shadow=False)
    bulb = k.part(lm, "Bulb", (3.2, 0.3, 0.3), CF((xc, y + 6.62, (BZ0 + BZ1) / 2)), (220, 236, 255),
                  material="Neon", shape="Cylinder", grid=False, shadow=False)
    k.lamp(lm, bulb, "Street", "Spot", 22.0, 1.4, (220, 236, 255), angle=140.0, shadows=True, flicker=0.35)
    k.sc.attachment(bulb, "Fx_Moths", CF((xc, y + 6.1, (BZ0 + BZ1) / 2)))
    # timetable on the west front post
    tt = k.sc.model(m, "Timetable")
    k.mesh(tt, "Case", "BusStop__TimetableCase", bevel_box(1.6, 2.2, 0.3, 0.06), CF((BX0 + 1.3, y + 4.2, BZ0 + 0.45)),
           "shelter", shadow=False)
    board(k, tt, (1.3, 1.9, 0.15), CF((BX0 + 1.3, y + 4.2, BZ0 + 0.66), FACE["N"]), "timetable",
          text="ROUTE 9\nTOWN  6:10\n7:40  9:10\n10:40\nLAST BUS\n11:52", text_color=(30, 40, 60))
    # the lit advert box at the east end (faces the traffic from the east)
    ad = k.sc.model(m, "Advert")
    k.mesh(ad, "Box", "BusStop__AdBox", bevel_box(0.5, 4.6, BZ1 - BZ0 - 0.1, 0.08),
           CF((BX1 + 0.05, y + 3.5, (BZ0 + BZ1) / 2)), "shelter", solid=True)
    k.part(ad, "Glow", (0.15, 4.0, BZ1 - BZ0 - 0.6), CF((BX1 + 0.32, y + 3.5, (BZ0 + BZ1) / 2)), (255, 236, 200),
           material="Neon", grid=False, shadow=False)
    board(k, ad, (BZ1 - BZ0 - 0.7, 3.8, 0.15), CF((BX1 + 0.46, y + 3.5, (BZ0 + BZ1) / 2), FACE["W"]), "red",
          text="PAPA\nSTUD'S\nPIZZA\n\nOPEN\nLATE", text_color=(250, 226, 150))
    # litter bin on its post, the flag pole at the kerb
    k.prop(m, "PostBin", CF((BX1 + 1.4, y, BZ0 + 0.7)), where="outside", name="Bin")
    k.mesh(m, "SignPole", "BusStop__SignPole", O.flat_pole(8.4, 0.18, 0.15, 8), CF((BX0 - 1.4, y - 0.4, BZ1 + 0.3)),
           "galv", solid=True)
    fl = k.sc.model(m, "Flag")
    k.mesh(fl, "Disc", "BusStop__FlagDisc", ccyl(1.1, 0.2, 12, "z", (0, 0, 0), 0.05),
           CF((BX0 - 1.4, y + 7.3, BZ1 + 0.55)), "red", shadow=False)
    board(k, fl, (1.5, 1.0, 0.15), CF((BX0 - 1.4, y + 7.3, BZ1 + 0.72), FACE["N"]), "red", text="BUS\nSTOP",
          text_color=(250, 240, 220))
    k.mesh(fl, "Plate", "BusStop__FlagPlate", bevel_box(1.2, 0.6, 0.15, 0.03), CF((BX0 - 1.4, y + 6.0, BZ1 + 0.53)),
           "timetable", shadow=False)
    stand(k, m, (BX0 + BX1) / 2, 21.6, S_, y=y)
    k.mark_used("BusShelter", "outside")
    return m


# ---------------------------------------------------------------- road sign with the mascot

def face_slab(pts, h, b=0.08):
    """A front-view outline (x, y) given thickness h along Z (centred), front edge chamfered."""
    return chamfer_slab([(x, -y) for (x, y) in pts], h, b).xf(G.M(G.rx(90))).xf(G.T(0, 0, -h / 2))


def _slice_body():
    """The mascot's body: a slice of pizza, tip down, chunky and bevelled."""
    return face_slab([(0.0, 0.0), (2.9, 6.0), (-2.9, 6.0)], 0.9, 0.12)


def road_sign(k, gr):
    """The pole sign at the lot entrance: steel posts on footings, a red sign box with the
    Board (PAPA STUD'S PIZZA) on both faces and chase Bulbs round the road face, the arrow
    pointing to the shack, and the slice mascot on top waving, its Head on a pivot."""
    m = station(k, "RoadSign")
    xc, z = 26.0, 21.0
    y0 = min(gr.y(22.5, z), gr.y(29.5, z))
    for x in (22.5, 29.5):
        k.mesh(m, "Footing", "RoadSign__Footing", ccyl(0.8, 0.6, 10, "y", (0, 0.1, 0), 0.08), CF((x, y0, z)),
               "concrete_dark", solid=True)
        post = G.Geo()
        post.add(bevel_box(0.8, 9.0, 0.2, 0.04, c=(0, 4.5, -0.3)))
        post.add(bevel_box(0.8, 9.0, 0.2, 0.04, c=(0, 4.5, 0.3)))
        post.add(bevel_box(0.2, 9.0, 0.6, 0.04, c=(0, 4.5, 0)))
        k.mesh(m, "Post", "RoadSign__Post", post, CF((x, y0 + 0.3, z)), "galv_dark", solid=True)
    yb = y0 + 8.4                                      # the sign box from here up
    box = G.Geo()
    box.add(bevel_box(10.4, 5.2, 1.0, 0.12, c=(0, 2.6, 0)))
    k.mesh(m, "SignBox", "RoadSign__Box", box, CF((xc, yb, z)), "red", solid=True)
    trims = G.Geo()
    trims.add(bevel_box(11.0, 0.4, 1.4, 0.08, c=(0, 0.0, 0)))
    k.mesh(m, "BoardTrim", "RoadSign__Trim", trims, CF((xc, yb + 5.3, z)), "cream", shadow=False)
    k.mesh(m, "BoardTrim", "RoadSign__Trim", trims, CF((xc, yb - 0.1, z)), "cream", shadow=False)
    board(k, m, (9.4, 4.2, 0.15), CF((xc, yb + 2.6, z + 0.575), FACE["N"]), "cream", text="PAPA STUD'S\nPIZZA",
          text_color=(170, 32, 26), name="Board")
    board(k, m, (9.4, 4.2, 0.15), CF((xc, yb + 2.6, z - 0.575), FACE["S"]), "cream", text="PAPA STUD'S\nPIZZA",
          text_color=(170, 32, 26), name="BoardBack")
    # chase bulbs round the road face (south), clockwise from the top left
    pts = []
    for i in range(10):
        pts.append((-4.75 + i * 1.055, 4.95))
    for i in range(1, 4):
        pts.append((4.95, 4.95 - i * 1.2))
    for i in range(10):
        pts.append((4.75 - i * 1.055, 0.25))
    for i in range(1, 4):
        pts.append((-4.95, 0.25 + i * 1.2))
    for i, (bx, by) in enumerate(pts):
        b = k.part(m, "Bulb", (0.45, 0.45, 0.45), CF((xc + bx, yb + by, z + 0.62)), (255, 222, 150), material="Neon",
                   shape="Ball", grid=False, shadow=False)
        k.attr(b, "Chase", i + 1)
    # the arrow under the box, pointing west to the shack, on two brackets, a row of bulbs
    arrow = face_slab([(-4.8, 0.0), (-2.9, 1.7), (-2.9, 0.8), (4.3, 0.8), (4.3, -0.8), (-2.9, -0.8), (-2.9, -1.7)],
                      0.5, 0.1)
    k.mesh(m, "Arrow", "RoadSign__Arrow", arrow, CF((xc, yb - 2.4, z)), "mustard", solid=False)
    br = G.Geo()
    for dx in (-1.5, 2.5):
        br.add(bevel_box(0.3, 1.0, 0.3, 0.04, c=(dx, 0, 0)))
    k.mesh(m, "ArrowBrackets", "RoadSign__ArrowBrackets", br, CF((xc, yb - 1.1, z)), "galv_dark", shadow=False)
    board(k, m, (4.6, 0.7, 0.15), CF((xc + 0.6, yb - 2.05, z + 0.32), FACE["N"]), "mustard", text="OPEN LATE",
          text_color=(40, 24, 16), name="ArrowText")
    for i, dx in enumerate((3.8, 2.6, 1.4, 0.2, -1.0, -2.2, -4.0)):
        b = k.part(m, "Bulb", (0.4, 0.4, 0.4), CF((xc + dx, yb - 2.4 - (0.45 if i < 6 else 0.0), z + 0.3)),
                   (255, 222, 150), material="Neon", shape="Ball", grid=False, shadow=False)
        k.attr(b, "Chase", len(pts) + i + 1)
    # the mascot on top: slice body, crust, pepperoni, arms, and the Head (Face, Hat welded)
    ys = yb + 5.5
    k.mesh(m, "Slice", "RoadSign__Slice", _slice_body(), CF((xc, ys, z)), "cheese", solid=False)
    k.mesh(m, "Crust", "RoadSign__Crust", bevel_box(6.6, 1.1, 1.3, 0.3), CF((xc, ys + 6.35, z)), "dough", shadow=False)
    pep = G.Geo()
    for (px, py) in ((-0.9, 4.6), (1.0, 3.7), (0.0, 2.2), (-1.6, 5.4), (1.9, 5.3)):
        pep.add(ccyl(0.5, 0.2, 10, "z", (px, py, 0.5), 0.05))
    k.mesh(m, "Pepperoni", "RoadSign__Pepperoni", pep, CF((xc, ys, z)), "sauce", shadow=False)
    arms = G.Geo()
    arms.add(G.tube([(-2.2, 4.4, 0.2), (-3.2, 4.0, 0.3), (-4.0, 4.8, 0.4), (-4.4, 5.8, 0.4)], 0.28, 8))   # waving
    arms.add(G.tube([(2.2, 4.4, 0.2), (3.1, 3.7, 0.3), (3.5, 2.8, 0.4)], 0.28, 8))
    arms.add(G.outward(G.lathe([(0, -0.4), (0.4, -0.3), (0.45, 0.1), (0.3, 0.4), (0, 0.45)], 8)).xf(G.T(-4.5, 6.2, 0.4)))
    arms.add(G.outward(G.lathe([(0, -0.4), (0.4, -0.3), (0.45, 0.1), (0.3, 0.4), (0, 0.45)], 8)).xf(G.T(3.6, 2.4, 0.4)))
    k.mesh(m, "Arm", "RoadSign__Arms", arms, CF((xc, ys, z)), "white_glove", shadow=False)
    hy = ys + 8.0
    head = k.mesh(m, "Head", "RoadSign__Head", G.outward(G.lathe([(0, -1.1), (0.8, -1.0), (1.15, -0.3), (1.1, 0.5),
                                                                    (0.7, 1.0), (0, 1.1)], 12)),
                  CF((xc, hy, z)), "skin_cartoon", solid=False)
    face = G.Geo()
    for dx in (-0.42, 0.42):
        face.add(ccyl(0.2, 0.15, 8, "z", (dx, 0.25, 1.08), 0.04))
    face.add(G.tube([(-0.55, -0.3, 1.02), (-0.25, -0.55, 1.12), (0.25, -0.55, 1.12), (0.55, -0.3, 1.02)], 0.1, 6))
    face.add(ccyl(0.22, 0.3, 8, "z", (0.0, -0.05, 1.12), 0.06))                                 # nose
    fc = k.mesh(m, "Face", "RoadSign__Face", face, CF((xc, hy, z)), "black", shadow=False)
    hat = G.Geo()
    hat.add(ccyl(0.95, 0.5, 12, "y", (0, 1.05, 0), 0.08))
    for (dx, dz) in ((-0.5, 0.0), (0.5, 0.0), (0.0, 0.0), (0.0, -0.4), (0.0, 0.4)):
        hat.add(G.outward(G.lathe([(0, 0), (0.45, 0.05), (0.55, 0.45), (0.4, 0.8), (0, 0.9)], 8)).xf(G.T(dx, 1.25, dz)))
    ht = k.mesh(m, "Hat", "RoadSign__Hat", hat, CF((xc, hy, z)), "paper", shadow=False)
    weld_all(k, head, [fc, ht])
    pivot(head, CF((xc, hy - 1.1, z)))
    moving(m, "Head", "turns about Y at the neck (the pivot); Face and Hat are welded to it")
    stand(k, m, xc, 18.5, S_, y=gr.y(xc, 18.5))
    k.mark_used("RoadSign", "outside")
    return m


# ---------------------------------------------------------------- cameras

def cameras(k, sc):
    """A CCTV camera just behind each Cam_ marker, looking the marker's way."""
    f = sc.folder(sc.root.get("Outside"), "Cameras")
    mk = sc.root.get("Markers")
    geo = O.cctv_geo()
    for c in mk.children:
        if not c.name.startswith("Cam_"):
            continue
        cf = c.p["cf"]
        look = -cf.R[:, 2]
        flat = np.array((look[0], 0.0, look[2]))
        flat /= np.linalg.norm(flat)
        R = G.facing(-flat)                           # local +Z = the look direction (the lens)
        base = CF(cf.p - flat * 1.6 + np.array((0, 0.25, 0)), R)
        m = k.sc.model(f, "Camera_" + c.name[4:])
        k.mesh(m, "Camera", "Cam__Body", geo, base, "grey_light", shadow=False)
        k.part(m, "Led", (0.15, 0.15, 0.15), base * CF((0.2, 0.55, 1.6)), (255, 40, 30), material="Neon", grid=False,
               shadow=False)
        plate = base.p + base.R @ np.array((0.0, 0.0, 0.1))
        if c.name == "Cam_Front":                      # hangs on a rod from the awning
            top = 11.95 - (plate[2] - (L.OUT_Z1 + 0.5 + 1.8)) / 3.4 * 1.45 - 0.13
            k.mesh(m, "Hanger", "Cam__Hanger", rod(plate + (0, 0.45, 0), (plate[0], top, plate[2]), 0.1, 6), CF(),
                   "charcoal", shadow=False)
        elif c.name == "Cam_Back":                     # a clamp arm round the street lamp's pole
            pole = np.array((-9.0, plate[1], 21.6))
            k.mesh(m, "PipeClamp", "Cam__Clamp", rod(plate, pole, 0.12, 6), CF(), "charcoal", shadow=False)
    k.mark_used("CCTVCamera", "outside")


def build(k, gr):
    return [bus_stop(k, gr), road_sign(k, gr)]
