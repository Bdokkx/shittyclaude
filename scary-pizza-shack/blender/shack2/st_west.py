"""The west wall, south to north: StorageShelf, DrinksCooler, the staff lockers under the
side window (with its glass, sill and half-open blind), the FuseBox by the back door with the
light switch, and the broom leaning on the fridge's side. Same Models, markers and moving
parts as batch 1."""
import math

import numpy as np

import spsgeo as G
from spsgeo import CF

from . import counters as C, interior as IP, items2, layout as L
from .kit import bevel_box, ccyl, rod
from .st_common import E, FACE, N, S_, W, board, moving, pivot, spot, stand, station, wall_board, weld_all

WX = L.IN_X0          # -17, the west wall's inside face


# ---------------------------------------------------------------- storage shelf

def storage_shelf(k):
    """A heavy wooden shelving unit: Slot1/2 on the middle shelf, Slot3/4 on the bottom deck,
    Slot5/6 on the shelf above; stock on the top board (tins, tubs, a box of hairnets)."""
    m = station(k, "StorageShelf")
    z0, z1 = 2.0, 6.0
    x0, x1 = WX, WX + 2
    xc = (x0 + x1) / 2
    k.box(m, "Base", (x0, L.FLOOR, z0), (x1, 1.2, z1), "wood_dark", solid=True)
    for zz in (z0 + 0.2, z1 - 0.2):
        k.mesh(m, "Upright", "StorageShelf__Upright", bevel_box(2.0, 7.0, 0.4, 0.06), CF((xc, 1.2 + 3.5, zz)), "wood",
               solid=True)
    for y in (4.0, 6.8, 8.2):
        k.box(m, "Shelf", (x0, y - 0.4, z0), (x1, y, z1), "wood", solid=True)
        k.mesh(m, "ShelfEdge", "StorageShelf__Edge", bevel_box(0.2, 0.3, 4.0, 0.04), CF((x1 + 0.1, y - 0.15, (z0 + z1) / 2)),
               "wood_dark", shadow=False)
    kk = 1
    for y in (4.0, 1.2, 6.8):
        for z in (z1 - 1.4, z0 + 1.3):              # clear of the sink counter and the cooler
            spot(k, m, "Slot%d" % kk, x0 + 1.0, y, z, W)
            kk += 1
    # more stock at the backs of the shelves, behind the slots (out of their clear boxes)
    xb = x0 + 0.4
    k.prop(m, "SackPile", CF((xb, 1.2, (z0 + z1) / 2 + 0.2), G.ry(3)), name="Sacks")
    k.prop(m, "JarRow", CF((xb + 0.05, 4.0, z0 + 1.0), G.ry(90)), name="Jars")
    k.prop(m, "TinPair", CF((xb + 0.05, 4.0, z1 - 1.3), G.ry(90)), name="BackTins")
    k.prop(m, "JarRow", CF((xb + 0.05, 6.8, (z0 + z1) / 2), G.ry(90)), name="Jars", seed=2)
    # stock on the top board
    k.prop(m, "TinRow", CF((xc, 8.2, z1 - 1.0), G.ry(90)), name="Tins")
    k.prop(m, "HairnetBox", CF((xc, 8.2, z0 + 1.1), G.ry(90)), name="Hairnets")
    k.prop(m, "LabelStrip", CF((x1 + 0.28, 3.75, (z0 + z1) / 2), G.ry(90)), name="Labels")
    stand(k, m, x1 + IP.STAND_GAP + 0.4, (z0 + z1) / 2, W)
    return m


# ---------------------------------------------------------------- drinks cooler

def drinks_cooler(k):
    """A red glass-door drinks cooler, lit inside, three shelves of cans (Slot1..12 at the
    front, more cans behind), its door hinged on the north edge."""
    m = station(k, "DrinksCooler")
    z0, z1 = -2.0, 2.0
    x0, x1 = WX, WX + 3
    zc = (z0 + z1) / 2
    k.box(m, "Base", (x0, L.FLOOR, z0), (x1, 1.2, z1), "black", solid=True)
    k.mesh(m, "Grille", "DrinksCooler__Grille", _grille(4.0), CF((x1 + 0.05, 0.8, zc)), "steel_dark", shadow=False)
    for zz in (z0 + 0.2, z1 - 0.2):
        k.mesh(m, "Side", "DrinksCooler__Side", bevel_box(3.0, 6.4, 0.4, 0.06), CF(((x0 + x1) / 2, 1.2 + 3.2, zz)), "red",
               solid=True)
    k.box(m, "Back", (x0, 1.2, z0 + 0.5), (x0 + 1, 7.6, z1 - 0.5), "label_white", solid=True)
    k.box(m, "Header", (x0, 7.4, z0), (x1, 8.2, z1), "red", solid=True)
    wall_board(k, m, "W", zc, 7.8, (3.2, 0.6), "label_white", d=x1 - x0 + 0.075, text="ICE COLD SODA",
               text_color=(170, 30, 24), name="Band")
    lm = k.sc.model(m, "CoolerLight")
    bulb = k.part(lm, "Bulb", (2.0, 0.2, 3.2), CF((x0 + 2.0, 7.3, zc)), (220, 240, 255), material="Neon", grid=False,
                  shadow=False)
    k.lamp(lm, bulb, "Shack", "Surface", 6.0, 0.8, (210, 232, 255), shadows=False)
    for y in (6.0, 4.4, 2.8):
        k.box(m, "Shelf", (x0 + 1, y - 0.4, z0 + 0.5), (x1, y, z1 - 0.5), "steel", solid=True)
    kk = 1
    for y in (6.0, 4.4, 2.8, 1.2):
        for z in (z1 - 1.0, zc, z0 + 1.0):
            spot(k, m, "Slot%d" % kk, x0 + 2.0, y, z, W)
            kk += 1
        k.prop(m, "CanRowBack", CF((x0 + 1.3, y, zc), G.ry(90)), name="Stock", seed=int(y * 10))
    door = k.part(m, "Door", (6.0, 0.4, 4.0), CF((x1 + 0.2, 4.2, zc), G.rz(90)), "glass", material="Glass",
                  transparency=0.7, solid=True, shadow=False)
    frame = []
    fr = G.Geo()
    for (cy, cz, sy, sz) in ((-2.85, 0, 0.3, 4.0), (2.85, 0, 0.3, 4.0), (0, -1.85, 6.0, 0.3), (0, 1.85, 6.0, 0.3)):
        fr.add(bevel_box(0.5, sy, sz, 0.06, c=(0, cy, cz)))
    frame.append(k.mesh(m, "DoorFrame", "DrinksCooler__DoorFrame", fr, CF((x1 + 0.25, 4.2, zc)), "red", solid=False))
    hdl = G.Geo()
    hdl.add(rod((0.4, -1.0, 0), (0.4, 1.0, 0), 0.1, 8))
    for dy in (-0.9, 0.9):
        hdl.add(rod((0.0, dy, 0), (0.4, dy, 0), 0.08, 6))
    frame.append(k.mesh(m, "DoorHandle", "DrinksCooler__Handle", hdl, CF((x1 + 0.45, 4.4, z1 - 0.45)), "steel_light"))
    weld_all(k, door, frame)
    pivot(door, CF((x1 + 0.4, 4.4, z0)))
    moving(m, "Door", "glass door hinged on its north edge; rotate the pivot +90 deg about Y to swing it open into "
                      "the room. Frame strips and handle are welded to it")
    stand(k, m, x1 + IP.STAND_GAP + 0.6, zc, W)
    return m


def _grille(w):
    g = G.Geo()
    for i in range(3):
        g.add(bevel_box(0.15, 0.15, w - 0.6, 0.03, c=(0, -0.25 + 0.25 * i, 0)))
    return g


# ---------------------------------------------------------------- lockers + side window

def lockers(k, parent):
    """Two narrow staff lockers under the south half of the side window (the north half stays
    open: the way in from the back door keeps the door's full width), louvred doors, name-tape
    labels, a padded cushion on top so they double as the break bench; one door not quite shut."""
    m = k.sc.model(parent, "Lockers")
    z0, z1 = -6.0, -2.0
    x0, x1 = WX, WX + 1.6
    lw = (z1 - z0) / 2                                   # 1.2 a locker
    k.mesh(m, "Body", "Lockers__Body", bevel_box(x1 - x0, 3.2, z1 - z0, 0.06),
           CF(((x0 + x1) / 2, L.FLOOR + 1.6, (z0 + z1) / 2)), "locker_grey", solid=True)
    for i, (za, zb) in enumerate(((z0, z0 + lw), (z0 + lw, z1))):
        zc = (za + zb) / 2
        dg = G.Geo()
        dg.add(bevel_box(0.2, 3.0, lw - 0.1, 0.06, c=(0, 0, 0)))
        for j in range(4):
            dg.add(bevel_box(0.15, 0.15, lw - 0.5, 0.03, c=(0.12, 1.1 - 0.18 * j, 0)))
        if i == 1:
            R = G.ry(14)
            cf = CF((x1 + 0.1, L.FLOOR + 1.6, zb - 0.05)) * CF(R=R) * CF((0, 0, -(lw - 0.1) / 2))
        else:
            cf = CF((x1 + 0.1, L.FLOOR + 1.6, zc))
        k.mesh(m, "LockerDoor", "Lockers__Door", dg, cf, "locker_door", solid=True)
        k.mesh(m, "Handle", "Lockers__Handle", bevel_box(0.2, 0.5, 0.2, 0.05), cf * CF((0.2, 0.1, -(lw / 2 - 0.3))),
               "steel_dark", shadow=False)
        board(k, m, (0.8, 0.3, 0.15), cf * CF((0.18, 1.15, 0.0), G.ry(-90)), "paper",
              text=("DEB", "MARCO")[i], text_color=(30, 30, 30), name="NameTape")
    k.mesh(m, "Cushion", "Lockers__Cushion", bevel_box(x1 - x0, 0.4, z1 - z0, 0.15),
           CF(((x0 + x1) / 2, L.FLOOR + 3.4, (z0 + z1) / 2)), "red_dark", solid=True)
    k.prop(m, "Newspaper", CF(((x0 + x1) / 2 + 0.1, L.FLOOR + 3.6, -4.9), G.ry(20)), name="Newspaper")
    k.mark_used("Lockers")
    return m


def side_window(k, parent):
    """The side window: glass, an inside sill, and a venetian blind let down half way."""
    m = k.sc.model(parent, "SideWindow")
    z0, z1, y0, y1 = L.SIDE_Z0, L.SIDE_Z1, L.SIDE_Y0, L.SIDE_Y1
    k.part(m, "Glass", (0.15, y1 - y0, z1 - z0), CF((WX - 0.5, (y0 + y1) / 2, (z0 + z1) / 2)), "glass",
           material="Glass", transparency=0.6, grid=False, shadow=False)
    k.mesh(m, "Sill", "SideWindow__Sill", bevel_box(1.0, 0.3, 4.0, 0.06), CF((WX + 0.1, y0 + 0.0, (z0 + z1) / 2)),
           "wood", solid=True)
    blind = G.Geo()
    blind.add(bevel_box(0.4, 0.3, 4.0, 0.06, c=(0, 0, 0)))                     # headrail
    for i in range(7):
        blind.add(bevel_box(0.5, 0.15, 3.9, 0.03, c=(0, -0.25 - 0.2 * i, 0)).xf(G.M(G.rz(18))))
    blind.add(bevel_box(0.4, 0.2, 3.9, 0.04, c=(0, -1.75, 0)))                 # bottom bar
    for z in (-1.2, 1.2):
        blind.add(rod((0.05, 0, z), (0.05, -1.7, z), 0.075, 4))
    blind.add(rod((0.15, -0.1, 1.7), (0.15, -2.6, 1.7), 0.075, 4))              # the pull cord
    k.mesh(m, "Blind", "SideWindow__Blind", blind, CF((WX + 0.3, y1 - 0.15, (z0 + z1) / 2)), "blind", shadow=True)
    return m


# ---------------------------------------------------------------- fuse box

def fuse_box(k):
    """A grey steel fuse box with its red Lever (up = ON), a hazard sticker, conduit going up
    to the ceiling; the light switch for the room beside it."""
    m = station(k, "FuseBox")
    z = -8.4
    x0 = WX
    k.mesh(m, "Box", "FuseBox__Box6", bevel_box(0.6, 2.2, 2.0, 0.1), CF((x0 + 0.3, 5.7, z)), "grey", solid=True)
    k.mesh(m, "Door", "FuseBox__Door", bevel_box(0.15, 1.8, 1.6, 0.05), CF((x0 + 0.65, 5.7, z - 0.1)), "grey_light",
           shadow=False)
    wall_board(k, m, "W", z - 0.5, 6.25, (0.6, 0.6), "mustard", d=0.78, text="DANGER", text_color=(20, 20, 20),
               name="Sticker")
    k.part(m, "Hub", (0.4, 0.8, 0.8), CF((x0 + 0.8, 5.4, z + 0.5)), "black", shape="Cylinder", grid=False)
    lev = G.Geo()
    lev.add(bevel_box(0.2, 1.2, 0.2, 0.05, c=(0, 0.6, 0)))
    lev.add(G.sphere(0.22, 8, 4, c=(0, 1.25, 0)))
    lv = k.mesh(m, "Lever", "FuseBox__Lever", lev, CF((x0 + 1.1, 5.4, z + 0.5)), "red", solid=True)
    pivot(lv, CF((x0 + 1.1, 5.4, z + 0.5)))
    moving(m, "Lever", "pointing up = ON. Rotate the pivot about X (the wall's normal): +120 deg swings it down = OFF")
    cond = G.Geo()
    for dz in (-0.5, 0.0, 0.5):
        cond.add(rod((x0 + 0.3, 6.8, z + dz), (x0 + 0.3, L.CEIL, z + dz), 0.1, 6))
    k.mesh(m, "Conduit", "FuseBox__Conduit", cond, CF(), "steel_dark", shadow=False)
    k.prop(m, "LightSwitch", C.wcf("W", -6.9, 4.9, 0.0), name="LightSwitch")
    stand(k, m, x0 + 2.4, z, W)
    return m


def build(k):
    st = [storage_shelf(k), drinks_cooler(k), fuse_box(k)]
    dress = k.sc.folder(k.sc.root.get("Shack"), "Dressing")
    lockers(k, dress)
    side_window(k, dress)
    # the broom leans on the cooler's side by the lockers, out of the way in
    k.prop(dress, "Broom", CF((WX + 2.55, L.FLOOR, -2.75), G.ry(-90)), name="Broom")
    return st
