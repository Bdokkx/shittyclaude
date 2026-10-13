"""The north wall, west to east: BackDoor, Fridge, DoughStation, SauceStation, ChopStation,
ToppingRail. Same Models, markers and moving parts as batch 1 (positions follow the 6-deep
counters: work spots at Z -6.4, stands at Z -2.6)."""
import math

import numpy as np

import spsgeo as G
from spsgeo import CF

from . import counters as C, interior as IP, items2, layout as L
from .kit import bevel_box, ccyl, chamfer_slab, rod
from .st_common import (E, FACE, N, S_, W, board, cage_lamp, moving, pivot, spot, stand, station,
                        wall_board, weld_all)

NZ = L.IN_Z0                 # -10, the north wall's inside face
FRONT = IP.N_FRONT           # -4, the counters' front edge
WZ = IP.N_WORK_Z             # -6.4
SZ = FRONT + IP.STAND_GAP    # -2.6


def _counter(k, m, x0, x1, **kw):
    return C.counter(k, m, "N", x0, x1, IP.N_DEPTH, **kw)


# ---------------------------------------------------------------- back door

def back_door(k):
    m = station(k, "BackDoor")
    x0, x1, y0, y1 = L.DOOR_X0, L.DOOR_X1, L.DOOR_Y0, L.DOOR_Y1        # -19..-15, 0.6..7.0
    zi = NZ                                                             # door's room face
    zd = zi - 0.4                                                       # its outer face
    xc = (x0 + x1) / 2
    # the door: a 0.4 steel slab with two raised panels below and a wired window above
    g = G.Geo()
    g.add(bevel_box(4.0, 4.2, 0.4, 0.06, c=(0, 0.6 + 2.1, 0)))           # below the window
    g.add(bevel_box(4.0, 0.8, 0.4, 0.06, c=(0, 6.6, 0)))                # above it
    for sx in (-1, 1):
        g.add(bevel_box(0.8, 1.6, 0.4, 0.06, c=(sx * 1.6, 5.6, 0)))     # stiles
    for yy in (1.7, 3.6):
        g.add(bevel_box(2.8, 1.5, 0.15, 0.05, c=(0, yy, 0.25)))          # raised panels (room side)
        g.add(bevel_box(2.8, 1.5, 0.15, 0.05, c=(0, yy, -0.25)))         # and yard side
    door = k.mesh(m, "Door", "BackDoor__Door", g, CF((xc, 0.0, zd + 0.2)), "door_green", solid=True)
    parts = []
    parts.append(k.part(m, "Window", (2.4, 0.15, 1.6), CF((xc, 5.6, zd + 0.2), G.rx(90)), "glass",
                        material="Glass", transparency=0.45, grid=False, shadow=False))
    wires = G.Geo()
    for i in range(1, 4):
        wires.add(rod((-1.2 + 0.6 * i, -0.8, 0), (-1.2 + 0.6 * i, 0.8, 0), 0.075, 4))
    for j in range(1, 3):
        wires.add(rod((-1.2, -0.8 + 0.533 * j, 0), (1.2, -0.8 + 0.533 * j, 0), 0.075, 4))
    parts.append(k.mesh(m, "WindowWire", "BackDoor__Wire", wires, CF((xc, 5.6, zd + 0.2)), "steel_dark", shadow=False))
    parts.append(k.mesh(m, "KickPlate", "BackDoor__Kick", bevel_box(3.4, 0.8, 0.15, 0.04),
                        CF((xc, 1.2, zi + 0.075)), "steel"))
    lever = G.Geo()
    for zz, sg in ((zi, 1), (zd, -1)):
        lever.add(ccyl(0.2, 0.15, 8, "z", (x1 - 0.6 - xc, 3.6, zz + sg * 0.075 - (zd + 0.2)), 0.03))
        lever.add(rod((x1 - 0.6 - xc, 3.6, zz + sg * 0.2 - (zd + 0.2)), (x1 - 1.3 - xc, 3.55, zz + sg * 0.3 - (zd + 0.2)),
                      0.09, 6))
    parts.append(k.mesh(m, "Lever", "BackDoor__Lever", lever, CF((xc, 0.0, zd + 0.2)), "steel_light"))
    bar = G.Geo()
    bar.add(rod((-1.5, 0, 0.35), (1.5, 0, 0.35), 0.1, 8))
    for sx in (-1, 1):
        bar.add(bevel_box(0.4, 0.5, 0.35, 0.06, c=(sx * 1.6, 0, 0.18)))
    parts.append(k.mesh(m, "PushBar", "BackDoor__PushBar", bar, CF((xc, 3.0, zi)), "steel_dark"))
    # an openable Model "Door": hinged on its west edge (outer face), +90 about Y swings it out
    # into the yard; the slab is its Leaf
    from .opens import adopt
    door.name = "Leaf"
    pivot(door, CF((x0, 3.8, zd)))
    adopt(k, m, "Door", door, parts, "Swing", "Metal", angle=90.0)
    # the frame: a jamb liner in the opening, the head casing inside, a threshold
    k.box(m, "Threshold", (x0, 0.2, L.OUT_Z0), (x1, y0, zi), "steel_dark", solid=True)
    k.mesh(m, "HeadTrim", "BackDoor__Head", bevel_box(4.0, 0.4, 0.3, 0.06), CF((xc, y1 + 0.2, zi + 0.15)), "beam")
    # EXIT sign over the door inside: a lit box sign (always on), lit from a neon strip under it
    ex = k.sc.model(m, "ExitSign")
    k.mesh(ex, "Box", "BackDoor__ExitBox", bevel_box(2.4, 0.9, 0.5, 0.08), CF((xc, 8.15, zi + 0.25)), "charcoal")
    board(k, ex, (2.1, 0.65, 0.15), CF((xc, 8.17, zi + 0.55), FACE["N"]), (40, 190, 90), text="EXIT",
          text_color=(245, 255, 245))
    bulb = k.part(ex, "Bulb", (2.0, 0.15, 0.3), CF((xc, 7.65, zi + 0.3)), (90, 240, 140), material="Neon",
                  grid=False, shadow=False)
    k.lamp(ex, bulb, "Always", "Point", 6.0, 0.6, (70, 230, 120), shadows=False)
    # outside: a bulkhead lamp over the door (its Bulb keeps batch 1's path, BackDoor.Bulb)
    lp = (xc, 8.8, L.OUT_Z0 - 0.5 - 0.55)             # its plate on the siding
    R = G.facing((0, 0, 1))
    k.mesh(m, "LampPlate", "Lamp__CagePlate", bevel_box(0.9, 0.9, 0.2, 0.05), CF(lp, R) * CF((0, 0, -0.45)),
           "charcoal")
    cage = G.Geo()
    for a in range(6):
        t = math.tau * a / 6
        cage.add(rod((0.32 * math.cos(t), 0.32 * math.sin(t), -0.35), (0.32 * math.cos(t), 0.32 * math.sin(t), 0.25),
                     0.075, 4))
    cage.add(G.torus(0.33, 0.075, 12, 4, "z", (0, 0, 0.25)))
    k.mesh(m, "LampCage", "Lamp__Cage", cage, CF(lp, R), "charcoal", shadow=False)
    ob = k.part(m, "Bulb", (0.45, 0.45, 0.45), CF(lp), (255, 222, 170), material="Neon", shape="Ball", grid=False,
                shadow=False)
    k.lamp(m, ob, "Shack", "Spot", 18.0, 1.0, (255, 196, 132), angle=130.0, on_model=False)
    # door mat inside
    k.prop(m, "DoorMat", CF((xc, L.FLOOR, zi + 1.3)), name="DoorMat")
    stand(k, m, xc + 1.0, zi + 1.6, N)
    return m


# ---------------------------------------------------------------- fridge

def fridge(k):
    """Reach-in chiller with two glass doors (FridgeDoor1/2, hinged at the outer edges, opening
    out into the room): charcoal cabinet with steel
    edges and a red stripe, cool-white liner with shelf standards, four steel shelves with
    blue price strips, the red canopy (COLD badge, thermometer, air-curtain grille, the night
    blind rolled up under it, the cold strip light), a kick grille at the foot, and a slow
    drip from the drain tray onto the floor."""
    m = station(k, "Fridge")
    x0, x1 = -13.0, -9.0
    z0, z1 = NZ, NZ + 5.0                              # 5 deep: front at -5
    xc = (x0 + x1) / 2
    k.box(m, "Base", (x0, L.FLOOR, z0), (x1, 0.8, z1 - 1.0), "black", solid=True)
    grille = G.Geo()
    for i in range(2):
        grille.add(bevel_box(3.0, 0.15, 0.15, 0.03, c=(0, -0.1 + 0.2 * i, 0)))
    k.mesh(m, "Grille", "Fridge__Grille", grille, CF((xc, 0.6, z1 - 1.0 + 0.075)), "steel_dark", shadow=False)
    # the cabinet's sides: charcoal panels, a steel nosing down the front edge, a red stripe
    side = G.Geo()
    side.add(bevel_box(0.5, 6.2, 5.0, 0.08))
    trim = G.Geo()
    trim.add(bevel_box(0.5, 6.4, 0.3, 0.08, c=(0, 0, 2.45)))
    for sx, xx in ((-1, x0 + 0.25), (1, x1 - 0.25)):
        k.mesh(m, "Side", "Fridge__Side", side, CF((xx, 1.2 + 3.1, (z0 + z1) / 2)), "fridge_body", solid=True)
        k.mesh(m, "Nosing", "Fridge__Nosing", trim, CF((xx, 1.2 + 3.1, (z0 + z1) / 2)), "steel", shadow=False,
               material="SmoothPlastic")
        if sx < 0:                                    # (the east side stands against the dough bench)
            k.mesh(m, "Stripe", "Fridge__Stripe", bevel_box(0.15, 0.6, 4.2, 0.03),
                   CF((xx + sx * 0.3, 2.4, (z0 + z1) / 2 - 0.2)), "red", shadow=False)
    k.box(m, "Back", (x0 + 0.5, 0.8, z0), (x1 - 0.5, 7.6, z0 + 1), "liner", solid=True)
    std = G.Geo()
    for dx in (-1.1, 1.1):
        std.add(bevel_box(0.3, 6.0, 0.15, 0.04, c=(dx, 0, 0)))
        for y in np.arange(-2.6, 2.8, 0.8):
            std.add(bevel_box(0.15, 0.3, 0.17, 0.02, c=(dx, y, -0.01)))
    k.mesh(m, "Standards", "Fridge__Standards", std, CF((xc, 4.3, z0 + 1.075)), "steel_dark", shadow=False)
    # (the canopy stops at 8.2 so the conduit along the wall clears it)
    k.box(m, "Deck", (x0 + 0.5, 0.8, z1 - 4.0), (x1 - 0.5, 1.2, z1), "steel_dark", solid=True)
    for i, y in enumerate((3.0, 4.6, 6.2)):
        sd = (z1 - 0.2) - (z0 + 1.15)                     # in front of the shelf standards
        k.mesh(m, "Shelf", "Fridge__Shelf", bevel_box(x1 - x0 - 1.0, 0.4, sd, 0.04),
               CF((xc, y - 0.2, (z0 + 1.15 + z1 - 0.2) / 2)), "steel_dark", solid=True)
        k.mesh(m, "ShelfLip", "Fridge__Lip", bevel_box(3.0, 0.3, 0.2, 0.04), CF((xc, y - 0.05, z1 - 0.1)),
               "label_blue", shadow=False)
        for j, dx in enumerate((-0.9, 0.35, 1.0)[: 2 + i % 2]):
            board(k, m, (0.5, 0.25, 0.15), CF((xc + dx, y - 0.05, z1 + 0.025), FACE["N"]), "label_white",
                  text=("$1.99", "$3.49", "$2.25", "$0.99")[(i + j) % 4], text_color=(30, 30, 30), name="PriceTag")
    k.mesh(m, "DeckLip", "Fridge__Lip", bevel_box(3.0, 0.3, 0.2, 0.04), CF((xc, 1.15, z1 - 0.1)), "label_blue",
           shadow=False)
    # canopy, badge, dial, the air-curtain grille and night blind under it, and the cold light
    k.box(m, "Header", (x0, 7.4, z0), (x1, 8.2, z1), "red", solid=True)
    k.mesh(m, "HeaderTrim", "Fridge__HeaderTrim", bevel_box(4.0, 0.3, 0.3, 0.06), CF((xc, 7.45, z1 + 0.1)),
           "steel_light", shadow=False, material="SmoothPlastic")
    board(k, m, (2.0, 0.5, 0.15), CF((xc - 0.5, 7.85, z1 + 0.075), FACE["N"]), "cream", text="COLD",
          text_color=(160, 30, 24), name="Badge")
    k.prop(m, "FridgeDial", CF((x1 - 0.65, 7.95, z1)), name="Thermometer")
    air = G.Geo()
    air.add(bevel_box(3.0, 0.2, 0.6, 0.04))
    for t in np.linspace(-1.3, 1.3, 9):
        air.add(bevel_box(0.15, 0.06, 0.5, 0.02, c=(t, -0.12, 0)))
    k.mesh(m, "AirGrille", "Fridge__AirGrille", air, CF((xc, 7.3, z1 - 0.9)), "charcoal", shadow=False)
    blind = G.Geo()
    blind.add(ccyl(0.2, 3.0, 8, "x", (0, 0, 0), 0.04))
    blind.add(bevel_box(0.4, 0.2, 0.15, 0.03, c=(0.6, -0.25, 0.1)))
    k.mesh(m, "NightBlind", "Fridge__NightBlind", blind, CF((xc, 7.15, z1 - 0.3)), "grey_dark", shadow=False)
    lm = k.sc.model(m, "ColdLight")
    bulb = k.part(lm, "Bulb", (3.0, 0.2, 0.4), CF((xc, 7.25, z1 - 1.5)), (220, 240, 255), material="Neon",
                  grid=False, shadow=False)
    k.lamp(lm, bulb, "Shack", "Surface", 7.0, 0.8, (210, 232, 255), shadows=False)
    # the two glass doors: steel frames, a glass pane, a long bar handle by the meeting edges
    from .opens import hinge, opener
    dy0, dy1 = 1.3, 7.3
    dz = z1 + 0.12                                     # the doors' back face, clear of the price strips
    half = (x1 - x0 - 1.0) / 2
    for j, (ha, hb) in enumerate(((x0 + 0.5, xc), (xc, x1 - 0.5))):
        left = j == 0
        hu = ha + 0.03 if left else hb - 0.03
        dw, dh = half - 0.06, dy1 - dy0
        dc = ((ha + hb) / 2, (dy0 + dy1) / 2, dz + 0.1)
        op = opener(k, m, "FridgeDoor%d" % (j + 1), "Swing", "Fridge", angle=-90.0 if left else 90.0)
        fr = G.Geo()
        for (cx, cy, sx, sy) in ((0, dh / 2 - 0.15, dw, 0.3), (0, -dh / 2 + 0.2, dw, 0.4),
                                 (-dw / 2 + 0.15, 0, 0.3, dh), (dw / 2 - 0.15, 0, 0.3, dh)):
            fr.add(bevel_box(sx, sy, 0.2, 0.05, c=(cx, cy, 0)))
        leaf = k.mesh(op, "Frame", "Fridge__DoorFrame", fr, CF(dc), "steel_light", material="SmoothPlastic")
        k.part(op, "Glass", (dw - 0.5, dh - 0.6, 0.15), CF((dc[0], dc[1] - 0.05, dc[2])), "glass", material="Glass",
               transparency=0.55, grid=False, shadow=False)
        hx = (hb - 0.3) if left else (ha + 0.3)
        hg = G.Geo()
        hg.add(rod((0, -1.2, 0.3), (0, 1.2, 0.3), 0.1, 6))
        for yy in (-1.05, 1.05):
            hg.add(rod((0, yy, 0.0), (0, yy, 0.3), 0.08, 6))
        k.mesh(op, "Handle", "Fridge__DoorHandle", hg, CF((hx, 4.2, dz + 0.2)), "steel_dark")
        hinge(op, leaf, CF((hu, (dy0 + dy1) / 2, dz + 0.2)))
    # the drain tray drips: a puddle on the floor in front of the kick grille
    k.mesh(m, "Puddle", "Fridge__Puddle", chamfer_slab([(-0.8, -0.3), (-0.2, -0.55), (0.6, -0.4), (0.9, 0.1),
                                                         (0.3, 0.45), (-0.5, 0.35)], 0.04, 0.015),
           CF((xc + 0.6, L.FLOOR, z1 - 0.4)), "puddle", shadow=False, material="Glass", transparency=0.3)
    _fx(k, m, "Base", "Fx_Drip", (xc + 0.6, 0.45, z1 - 1.05))
    # Slot1/2 (dough, cheese) at eye level on the second shelf, Slot3/4 on the third, 5/6 top, 7/8 bottom
    sz = z1 - 1.2
    kk = 1
    for y in (4.6, 3.0, 6.2, 1.2):
        for x in (x0 + 1.2, x1 - 1.2):
            spot(k, m, "Slot%d" % kk, x, y, sz, N)
            kk += 1
    # stock at the backs of the shelves, clear of the slots
    for (y, kind, dx) in ((1.2, "CheeseLog", -0.6), (1.2, "SauceTub", 0.85), (3.0, "SauceTub", -0.85),
                          (3.0, "CheeseLog", 0.6), (4.6, "MilkCrate", 0.0),
                          (6.2, "CheeseLog", -0.6), (6.2, "SauceTub", 0.9)):
        k.prop(m, kind, CF((xc + dx, y, z0 + 1.8)), name=kind)
    stand(k, m, xc - 0.3, z1 + IP.STAND_GAP, N)
    return m


def _fx(k, m, part_name, fx, world_pos):
    """An Fx_ attachment in the named part of model m, at a world position."""
    k.sc.attachment(m.get(part_name), fx, CF(world_pos))


# ---------------------------------------------------------------- dough

def dough_station(k):
    """Bench with the flour bin in the open bay under it, the dough board with spilt flour and
    a scraper, the scale at the back of the bench, dough trays on the wall shelf above, the
    rolling pin on its own little rack above that."""
    m = station(k, "DoughStation")
    x0, x1 = -9.0, -5.0
    xc = (x0 + x1) / 2
    _counter(k, m, x0, x1, fronts=[(2.4, "open"), (1.6, "drawers3")], end_left=True, end_right=False,
             owner="DoughStation")
    fcf = C.wcf("N", x0 + 1.25, 0.9, 3.4)
    fb = k.prop(m, "FlourBin", fcf, name="FlourBin")
    from .opens import from_prop, stash
    from_prop(k, fb, "Lid", ["LidFront", "LidGrip"], fcf * CF((0.0, 1.75, 1.1)), "Slide", "Lid",
              offset=(0.0, 0.0, -1.0), label="Slide lid")
    stash(k, m, fcf * CF((0.0, 1.37, 0.6), G.facing((0, 0, 1))), (0.9, 0.35, 0.8), behind="FlourBin/Lid")
    # dough board on the bench
    wx = xc + 0.2
    k.mesh(m, "Board", "DoughStation__Board", bevel_box(3.6, 0.4, 3.6, 0.08), CF((wx, L.WORK + 0.2, WZ)),
           "wood_light", solid=True)
    spot(k, m, "Work", wx, L.WORK + 0.4, WZ, N)
    k.prop(m, "FlourDust", CF((wx, L.WORK + 0.48, WZ), G.ry(20)), name="FlourDust", seed=3)
    k.prop(m, "Scraper", CF((x1 - 1.0, L.WORK, NZ + 0.75), G.ry(10)), name="Scraper")       # at the back, off the board
    k.prop(m, "Scale", CF((x0 + 0.95, L.WORK, NZ + 0.85)), name="Scale")
    # wall shelf with the dough trays, the pin's rack above
    k.prop(m, "WallShelf", C.wcf("N", xc, 5.8, 0.0), name="TrayShelf")
    k.prop(m, "DoughTray", CF((xc, 5.8 + 0.15, NZ + 0.95)), name="DoughTrays")
    rack = C.wcf("N", xc, 7.5, 0.0)                   # the pin just under the conduit along the wall
    k.prop(m, "PinRack", rack, name="PinRack")
    items2.place(k, m, "RollingPin", CF((xc - 0.6, 7.5 + 0.15 + 0.32, NZ + 0.5), G.facing(E)))    # handle west
    stand(k, m, xc, SZ, N)
    return m


# ---------------------------------------------------------------- sauce + cheese

def _leaning(it, bowl, r, foot, wall_z):
    """Handle frame for a long-handled item standing in a dish and leaning on the north wall:
    the bowl (item-space centre `bowl`, radius r) over foot's X and Z with its lowest point at
    foot's Y, opening towards the room, the handle tipped back until its end is at wall_z."""
    V = np.vstack([g.arr() for *_, g in it.parts])
    B = np.array(bowl)
    near = np.linalg.norm(V - B, axis=1) <= r + 0.05
    flip = np.diag((-1.0, -1.0, 1.0))                        # opening towards the room
    best = None
    for deg in range(91, 170):
        a = math.radians(-deg)
        c, s_ = math.cos(a), math.sin(a)
        R = np.array(((1.0, 0.0, 0.0), (0.0, c, -s_), (0.0, s_, c))) @ flip
        W_ = V @ R.T
        b = R @ B
        t = np.array((foot[0] - b[0], foot[1] - W_[near, 1].min(), foot[2] - b[2]))
        back = (W_[:, 2] + t[2]).min()
        if best is None or abs(back - wall_z) < best[0]:
            best = (abs(back - wall_z), R, t)
    return CF(best[2], best[1])



def sauce_station(k):
    """Sauce on the left (stock pot on a gas ring with its gas pipe, the ladle in its rest
    leaning on the wall, an open can and a stack of cans, the spice rack above), cheese on the
    right (the CheeseBlock, the grater on its tray, the wheel with a wedge cut out on a wall
    shelf above)."""
    m = station(k, "SauceStation")
    x0, x1 = -5.0, 3.0
    xs, xch = x0 + 2.0, x0 + 6.0
    _counter(k, m, x0, x1, fronts=[(4, "doors2"), (4, "doors2")], end_left=False, end_right=False,
             notes={0: "STOCK CHECK:\n14 TINS. 13 TINS.\n14 TINS??"},
             owner="SauceStation")
    spot(k, m, "WorkSauce", xs, L.WORK, WZ + 0.3, N)     # a pizza here clears the burner behind
    spot(k, m, "WorkCheese", xch, L.WORK, WZ, N)
    bz = NZ + 1.05                                   # the back strip's centre line
    pc = (x0 + 1.0, L.WORK, bz + 0.15)
    k.prop(m, "Burner", CF(pc), name="Burner")
    k.prop(m, "StockPot", CF((pc[0], L.WORK + 0.55, pc[2])), name="Pot")
    gas = G.Geo()
    gas.add(rod((pc[0] - 0.7, L.WORK + 0.15, NZ + 0.1), (pc[0] - 0.7, L.WORK + 0.15, pc[2] - 1.04), 0.09, 6))
    gas.add(rod((pc[0] - 0.7, L.WORK + 0.15, NZ + 0.1), (pc[0] - 0.7, 0.2, NZ + 0.1), 0.09, 6))       # in the back
    k.mesh(m, "GasPipe", "SauceStation__Gas", gas, CF(), "mustard_dark", shadow=False)
    # the ladle: bowl down in its rest, handle leaning back against the wall
    rest = (x0 + 2.9, L.WORK, bz)
    k.prop(m, "LadleRest", CF(rest), name="LadleRest")
    items2.place(k, m, "Ladle", _leaning(items2.get("Ladle"), (0.0, -0.45, -1.1), 0.39,
                                         (rest[0], L.WORK + 0.07, rest[2]), NZ + 0.3))
    k.prop(m, "TomatoCanOpen", CF((x0 + 4.0, L.WORK, bz)), name="OpenCan")     # (the spare tins are in the cupboard)
    k.prop(m, "SpiceRack", C.wcf("N", x0 + 2.0, 5.75, 0.0), name="SpiceRack")
    # cheese: the grater on its tray, the CheeseBlock item, the wheel up on a shelf
    k.prop(m, "GraterTray", CF((x0 + 5.85, L.WORK, bz + 0.1)), name="GraterTray")
    items2.place_on(k, m, "Grater", CF((x0 + 6.25, L.WORK + 0.15, bz + 0.1)))
    items2.place_on(k, m, "CheeseBlock", CF((x0 + 7.45, L.WORK, bz), G.ry(90)))
    k.prop(m, "WallShelf3", C.wcf("N", 1.5, 5.6, 0.0), name="CheeseShelf")
    k.prop(m, "CheeseWheel", CF((1.1, 5.6 + 0.3, NZ + 0.85), G.ry(200)), name="CheeseWheel")
    stand(k, m, (x0 + x1) / 2, SZ, N)
    stand(k, m, xs, SZ, N, name="StandSauce")
    stand(k, m, xch, SZ, N, name="StandCheese")
    return m


# ---------------------------------------------------------------- chop

def chop_station(k):
    """A thick board with handle hole and juice groove, a spare board stood against the
    backsplash, knives of five sizes on a magnetic strip (the Knife item among them), a crate
    of vegetables in the open bay under the bench."""
    m = station(k, "ChopStation")
    x0, x1 = 3.0, 7.0
    xc = (x0 + x1) / 2
    _counter(k, m, x0, x1, fronts=[(2, "door"), (2, "open")], end_left=False, end_right=False, open_sides=False,
             insides={0: ["OneShoe", "|", "PlateStack"]},
             owner="ChopStation")
    k.prop(m, "VegCrate", C.wcf("N", x1 - 1.0, 0.9, 3.2, G.ry(90)), name="VegCrate")
    k.prop(m, "ChopBoard", CF((xc, L.WORK, WZ)), name="Board")
    spot(k, m, "Work", xc, L.WORK + 0.4, WZ, N)
    k.prop(m, "BoardUpright", C.wcf("N", xc - 0.3, L.WORK, 0.45), name="SpareBoard")
    k.prop(m, "KnifeStrip", C.wcf("N", xc, 6.9, 0.0), name="KnifeStrip")
    # the Knife item hangs on the strip, second from the left
    items2.place(k, m, "Knife", CF((xc - 0.4, 6.9 - 0.75, NZ + 0.52), np.column_stack(((1, 0, 0), (0, 0, 1),
                                                                                        (0, -1, 0)))))
    stand(k, m, xc, SZ, N)
    return m


# ---------------------------------------------------------------- topping rail

def topping_rail(k):
    """Refrigerated prep table: stainless doors under a steel top, the cold rail at the back
    -- a steel well with six steel tubs set in it (Tub1..6 on the tub floors, nothing over or
    in front of them) -- its hinged lid standing open against the wall, a glass guard on wall
    brackets over the rail only (no post anywhere near Tub1), tongs on the rail's lip."""
    m = station(k, "ToppingRail")
    x0, x1 = 7.0, 12.0                               # a hand's gap to the hot oven
    _counter(k, m, x0, x1, top="steel", door="steel", fronts=[(5, "slide2")], end_left=False,
             end_right=True, owner="ToppingRail")
    y0, y1 = L.WORK, L.WORK + 0.8                  # the well's rim at 4.2
    z0, z1 = NZ, NZ + 1.9
    well = G.Geo()
    W_, D_ = x1 - x0 + 0.2, z1 - z0
    well.add(bevel_box(W_, 0.8, 0.25, 0.05, c=(0, 0.4, D_ / 2 - 0.125)))           # front wall
    well.add(bevel_box(W_, 0.8, 0.2, 0.05, c=(0, 0.4, -D_ / 2 + 0.1)))             # back wall
    for sx in (-1, 1):
        well.add(bevel_box(0.2, 0.8, D_, 0.05, c=(sx * (W_ / 2 - 0.1), 0.4, 0)))    # ends
    k.mesh(m, "Rail", "ToppingRail__Well", well, CF(((x0 + x1) / 2 - 0.3, y0, (z0 + z1) / 2)), "steel_dark",
           solid=True)
    tub = G.Geo()
    tw, td, th = 0.8, 1.2, 0.75
    tub.add(bevel_box(tw, 0.15, td, 0.04, c=(0, 0.075, 0)))
    tub.add(bevel_box(tw, th, 0.15, 0.04, c=(0, th / 2, td / 2 - 0.075)))
    tub.add(bevel_box(tw, th, 0.15, 0.04, c=(0, th / 2, -td / 2 + 0.075)))
    for sx in (-1, 1):
        tub.add(bevel_box(0.15, th, td, 0.04, c=(sx * (tw / 2 - 0.075), th / 2, 0)))
    tub.add(bevel_box(tw + 0.1, 0.15, td + 0.1, 0.03, c=(0, th - 0.075, 0)).xf(G.S(1, 1, 1)))
    zc = (z0 + z1) / 2 + 0.05
    for i in range(6):
        cx = 7.15 + 0.82 * i                        # six slimmer tubs in the shorter rail
        k.mesh(m, "Tub", "ToppingRail__Tub", tub, CF((cx, y1 - th + 0.05, zc)), "steel_light", shadow=False)
        spot(k, m, "Tub%d" % (i + 1), cx, y1 - th + 0.05 + 0.15, zc, N)
    # the rail's steel lid, shut over the tubs: hinged along its back edge, it lifts up to stand
    # against the wall (the openable Model "Lid")
    from .opens import hinge, opener
    lid_m = opener(k, m, "Lid", "Swing", "Lid", angle=-90.0, axis="X")
    lz0, lz1 = NZ + 0.3, z1 + 0.1
    lid = G.Geo()
    lw_ = W_ - 0.4                                   # clear of the chop station's board
    lid.add(bevel_box(lw_, 0.2, lz1 - lz0, 0.06, c=(0, 0.1, 0)))
    lid.add(bevel_box(lw_, 0.3, 0.15, 0.04, c=(0, 0.0, (lz1 - lz0) / 2 - 0.075)))      # the front lip
    lc = ((x0 + x1) / 2 - 0.3, y1 + 0.1, (lz0 + lz1) / 2)
    leaf = k.mesh(lid_m, "Leaf", "ToppingRail__LidShut", lid, CF(lc), "steel", material="SmoothPlastic")
    k.mesh(lid_m, "Grip", "ToppingRail__LidGrip", bevel_box(1.2, 0.15, 0.2, 0.04),
           CF((lc[0], y1 + 0.28, lz1 - 0.25)), "steel_dark", shadow=False)
    hinge(lid_m, leaf, CF((lc[0], y1 + 0.3, lz0)))
    k.prop(m, "Tongs", CF((x1 - 0.5, L.WORK + 0.1, z1 + 0.9), G.ry(160)), name="Tongs")     # on the top, by the lid
    spot(k, m, "Work", (x0 + x1) / 2 - 0.5, L.WORK, WZ + 0.4, N)
    stand(k, m, (x0 + x1) / 2 - 0.5, SZ, N)
    return m


def build(k):
    return [back_door(k), fridge(k), dough_station(k), sauce_station(k), chop_station(k), topping_rail(k)]
