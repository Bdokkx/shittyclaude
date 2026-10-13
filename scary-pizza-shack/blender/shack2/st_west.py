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
    x0, x1 = WX, WX + 4                          # as deep as the cooler: no recess beside it
    xc = (x0 + x1) / 2
    k.box(m, "Base", (x0, L.FLOOR, z0), (x1, 1.2, z1), "wood_dark", solid=True)
    for zz in (z0 + 0.2, z1 - 0.2):
        k.mesh(m, "Upright", "StorageShelf__Upright", bevel_box(x1 - x0, 7.0, 0.4, 0.06), CF((xc, 1.2 + 3.5, zz)), "wood",
               solid=True)
    for y in (4.0, 6.8, 8.2):
        k.box(m, "Shelf", (x0, y - 0.4, z0), (x1, y, z1), "wood", solid=True)
        k.mesh(m, "ShelfEdge", "StorageShelf__Edge", bevel_box(0.2, 0.3, 4.0, 0.04), CF((x1 + 0.1, y - 0.15, (z0 + z1) / 2)),
               "wood_dark", shadow=False)
    kk = 1
    for y in (4.0, 1.2, 6.8):
        for z in (z1 - 1.4, z0 + 1.3):              # clear of the sink counter and the cooler
            spot(k, m, "Slot%d" % kk, x1 - 1.0, y, z, W)
            kk += 1
    # more stock at the backs of the shelves, behind the slots (out of their clear boxes)
    xb = x0 + 0.7
    k.prop(m, "SackPile", CF((xb, 1.2, (z0 + z1) / 2 + 0.2), G.ry(3)), name="Sacks")
    k.prop(m, "JarRow", CF((xb + 0.05, 4.0, z0 + 1.0), G.ry(90)), name="Jars")
    k.prop(m, "TinPair", CF((xb + 0.05, 4.0, z1 - 1.3), G.ry(90)), name="BackTins")
    k.prop(m, "JarRow", CF((xb + 0.05, 6.8, (z0 + z1) / 2), G.ry(90)), name="Jars", seed=2)
    # stock on the top board
    k.prop(m, "TinRow", CF((xc, 8.2, z1 - 1.0), G.ry(90)), name="Tins")
    k.prop(m, "HairnetBox", CF((xc, 8.2, z0 + 1.1), G.ry(90)), name="Hairnets")
    k.prop(m, "LabelStrip", CF((x1 + 0.28, 3.75, (z0 + z1) / 2), G.ry(90)), name="Labels")
    stand(k, m, x1 + IP.STAND_GAP, (z0 + z1) / 2, W)
    return m


# ---------------------------------------------------------------- drinks cooler

COOLER_SHELVES = (6.05, 4.3, 2.55, 0.8)            # shelf tops, top first: 1.75 apart
COOLER_ROWS = (("Cola", "Orange", "Lime"), ("Grape", "Cola", "Orange"), ("Lime", "Grape", "Cola"),
               ("Orange", "Lime", "Grape"))           # per shelf, south to north; three rows of each flavour
ROW_PITCH = 0.8


def drinks_cooler(k):
    """A red glass-door drinks cooler: four wire shelves 1.75 apart, three rows of one flavour
    on each, three deep (the front place of every row is its Slot, Slot1..12 top shelf first,
    south to north; bottles on the top shelf), a price card on each shelf edge, a strip light
    inside, the lit brand header, the glass Door hinged on its north edge (an openable Model)."""
    from .items2 import SODA
    from .opens import hinge, opener
    m = station(k, "DrinksCooler")
    z0, z1 = -2.0, 2.0
    x0, x1 = WX, WX + 3
    zc = (z0 + z1) / 2
    k.attr(m, "RowDepth", 3)                          # drinks a row holds, front to back
    k.attr(m, "RowPitch", ROW_PITCH)                  # studs between them (going back from the Slot)
    k.box(m, "Base", (x0, L.FLOOR, z0), (x1, 0.8, z1), "black", solid=True)
    k.mesh(m, "Grille", "DrinksCooler__Grille", _grille(4.0), CF((x1 + 0.05, 0.6, zc)), "steel_dark", shadow=False)
    for zz in (z0 + 0.2, z1 - 0.2):
        k.mesh(m, "Side", "DrinksCooler__Side", bevel_box(3.0, 7.4, 0.4, 0.06), CF(((x0 + x1) / 2, 0.8 + 3.7, zz)),
               "red", solid=True)
    k.mesh(m, "Back", "DrinksCooler__Back", bevel_box(0.3, 7.4, 3.2, 0.05), CF((x0 + 0.15, 0.8 + 3.7, zc)),
           "label_white", solid=True)
    k.mesh(m, "Top", "DrinksCooler__Top", bevel_box(3.0, 0.6, 4.0, 0.08), CF(((x0 + x1) / 2, 7.9, zc)), "red",
           solid=True)
    # the lit header: the brand on a glowing panel across the top
    hd = k.sc.model(m, "Header")
    board(k, hd, (3.4, 0.55, 0.15), CF((x1 + 0.08, 7.9, zc), G.facing((1, 0, 0))), (255, 244, 226),
          text="PAPA'S POP", text_color=(176, 30, 24), name="Board", material="Neon")
    # the strip light inside, under the top
    lm = k.sc.model(m, "CoolerLight")
    bulb = k.part(lm, "Bulb", (0.4, 0.15, 3.0), CF((x1 - 0.5, 7.53, zc)), (220, 240, 255), material="Neon", grid=False,
                  shadow=False)
    k.lamp(lm, bulb, "Shack", "Surface", 7.0, 0.9, (210, 232, 255), shadows=False)
    # wire shelves on side ledges; price cards on their front bars
    wire = G.Geo()
    sd, sw = x1 - x0 - 0.45, z1 - z0 - 0.8
    for zz in (-sw / 2, sw / 2):
        wire.add(rod((-sd / 2, -0.075, zz), (sd / 2, -0.075, zz), 0.075, 4))
    for xx in (-sd / 2, sd / 2):
        wire.add(rod((xx, -0.075, -sw / 2), (xx, -0.075, sw / 2), 0.075, 4))
    for zz in np.arange(-sw / 2 + 0.4, sw / 2 - 0.2, 0.4):
        wire.add(rod((-sd / 2, -0.075, zz), (sd / 2, -0.075, zz), 0.075, 4))
    sxc = x0 + 0.3 + sd / 2
    kk = 1
    for si, y in enumerate(COOLER_SHELVES):
        if y > 1.0:
            k.mesh(m, "Shelf", "DrinksCooler__WireShelf", wire, CF((sxc, y, zc)), "steel_light", solid=True)
            for zz in (z0 + 0.4, z1 - 0.4):
                k.mesh(m, "Ledge", "DrinksCooler__Ledge", bevel_box(sd, 0.15, 0.2, 0.03),
                       CF((sxc, y - 0.225, zz + (0.1 if zz < zc else -0.1))), "steel_dark", shadow=False)
        board(k, m, (1.0, 0.35, 0.15), CF((x1 - 0.12, y - 0.3, zc), G.facing((1, 0, 0))), "label_white",
              text=("$2.50", "$1.25", "$1.25", "$1.25")[si], text_color=(160, 30, 24), name="PriceCard")
        for ri, z in enumerate((z1 - 1.0, zc, z0 + 1.0)):
            flav = COOLER_ROWS[si][ri]
            col = SODA[flav]
            sx = x1 - 0.55
            sl = spot(k, m, "Slot%d" % kk, sx, y, z, W)
            k.attr(sl, "Holds", ("SodaBottle" if si == 0 else "SodaCan") + flav)
            kk += 1
            if si == 0:
                k.prop(m, "BottleRow", CF((sx - ROW_PITCH, y, z), G.ry(90)), name="Bottles",
                       colors={"Body": col, "Cap": col})
            else:
                k.prop(m, "CanRow", CF((sx - ROW_PITCH, y, z), G.ry(90)), name="Cans",
                       colors={"Body": col, "Stripe": col})
    # the glass door, an openable Model: hinged on its north edge, +90 about Y swings it into the room
    dm = opener(k, m, "Door", "Swing", "Fridge", angle=90.0)
    dz0, dz1 = z0 + 0.25, z1 - 0.25
    dy0, dy1 = 0.85, 7.55
    dzc, dyc = (dz0 + dz1) / 2, (dy0 + dy1) / 2
    fr = G.Geo()
    for (cy, cz, sy, sz) in ((dy1 - dyc - 0.15, 0, 0.3, dz1 - dz0), (dy0 - dyc + 0.2, 0, 0.4, dz1 - dz0),
                             (0, dz0 - dzc + 0.15, dy1 - dy0, 0.3), (0, dz1 - dzc - 0.15, dy1 - dy0, 0.3)):
        fr.add(bevel_box(0.3, sy, sz, 0.06, c=(0, cy, cz)))
    frame = k.mesh(dm, "DoorFrame", "DrinksCooler__DoorFrame2", fr, CF((x1 + 0.15, dyc, dzc)), "red")
    k.part(dm, "Glass", (0.15, dy1 - dy0 - 0.6, dz1 - dz0 - 0.5), CF((x1 + 0.15, dyc + 0.05, dzc)), "glass",
           material="Glass", transparency=0.65, grid=False, shadow=False)
    hdl = G.Geo()
    hdl.add(rod((0.35, -1.3, 0), (0.35, 1.3, 0), 0.1, 8))
    for dy in (-1.15, 1.15):
        hdl.add(rod((0.0, dy, 0), (0.35, dy, 0), 0.08, 6))
    k.mesh(dm, "DoorHandle", "DrinksCooler__Handle", hdl, CF((x1 + 0.3, 4.2, dz1 - 0.4)), "steel_light")
    hinge(dm, frame, CF((x1 + 0.3, dyc, dz0)))
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
    labels, a padded cushion on top so they double as the break bench. Each opens (LockerDoor1/2,
    hinged at the outer edges): a shelf, the owner's things, a Stash on the floor; a photo
    taped inside Deb's door."""
    from . import insides
    from .opens import hinge, opener
    m = k.sc.model(parent, "Lockers")
    z0, z1 = -6.0, -2.0
    x0, x1 = WX, WX + 1.6
    lw = (z1 - z0) / 2                                   # 2 a locker
    k.box(m, "Plinth", (x0, 0.2, z0), (x1 - 0.6, 0.6, z1), "black", solid=True)
    wants = (["LunchBox", "|", "Rags"], ["ToolBox", "|", "Pens"])
    for i, (za, zb) in enumerate(((z0, z0 + lw), (z0 + lw, z1))):
        zc = (za + zb) / 2
        C._carcass(k, m, "W", za, zb, 0.6, 3.6, x1 - x0, "locker_grey", "Lockers", shelf_y=2.4)
        C.wbox(k, m, "Blocker", "W", za, zb, 0.6, 3.6, x1 - x0 - 0.3, x1 - x0, "black", solid=True,
               transparency=1.0, query=False, touch=False, shadow=False, grid=False)
        dg = G.Geo()
        dg.add(bevel_box(0.2, 3.0, lw - 0.1, 0.06, c=(0, 0, 0)))
        for j in range(4):
            dg.add(bevel_box(0.15, 0.15, lw - 0.5, 0.03, c=(0.12, 1.1 - 0.18 * j, 0)))
        cf = CF((x1 + 0.1, 2.1, zc))
        north_hinge = True                                # both hinged at the north edge: neither swings into
                                                          # the cooler's side, nor into the other
        op = opener(k, m, "LockerDoor%d" % (i + 1), "Swing", "Locker", angle=90.0 if north_hinge else -90.0)
        leaf = k.mesh(op, "Leaf", "Lockers__Door", dg, cf, "locker_door")
        free = 1 if north_hinge else -1                   # which way the free edge is from the centre (+Z / -Z)
        k.mesh(op, "Handle", "Lockers__Handle", bevel_box(0.2, 0.5, 0.2, 0.05),
               cf * CF((0.2, 0.1, free * (lw / 2 - 0.3))), "steel_dark", shadow=False)
        board(k, op, (0.8, 0.3, 0.15), cf * CF((0.18, 1.15, 0.0), G.ry(-90)), "paper",
              text=("DEB", "MARCO")[i], text_color=(30, 30, 30), name="NameTape")
        if i == 0:
            board(k, op, (0.9, 0.7, 0.15), cf * CF((-0.18, 0.6, 0.0), G.ry(90)), "paper_old",
                  text="DEB + PAPA\nOPENING DAY\n1987", text_color=(60, 50, 40), name="Photo")
        hz = (za + 0.05) if north_hinge else (zb - 0.05)
        hinge(op, leaf, CF((x1 + 0.2, 2.1, hz)))
        q = dict(w="W", m=m, ia=za + C.PANEL, ib=zb - C.PANEL, d=x1 - x0, shelf_y=2.4, y_body=3.6, insides=wants[i],
                 stock="office", note=None)
        insides.fill_cupboard(k, q, [op])
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
    to the ceiling; on the north wall between the back door and the fridge, where anyone
    coming in from the yard finds it, the light switch under it."""
    m = station(k, "FuseBox")
    x = -14.0                                     # the 2 studs of wall between the door (X -15) and the fridge
    z0 = L.IN_Z0
    k.mesh(m, "Box", "FuseBox__Box", bevel_box(1.8, 2.2, 0.45, 0.1), CF((x, 5.7, z0 + 0.225)), "grey", solid=True)
    # behind the door: a row of breakers and their hand-written labels
    br = G.Geo()
    for i in range(6):
        br.add(bevel_box(0.15, 0.45, 0.15, 0.03, c=(-0.4 + 0.15 * i, 0.0, 0.0)))
    k.mesh(m, "Breakers", "FuseBox__Breakers", br, CF((x - 0.3, 6.0, z0 + 0.525)), "black", shadow=False)
    board(k, m, (1.0, 0.5, 0.15), CF((x - 0.3, 5.3, z0 + 0.525), G.facing((0, 0, 1))),
          "paper_old", text="OVEN FRDG FRNT\nBACK SIGN ???", text_color=(40, 40, 40), name="FuseLabels")
    from .opens import hinge, opener
    dm = opener(k, m, "Door", "Swing", "Metal", angle=-90.0)
    leaf = k.mesh(dm, "Leaf", "FuseBox__Door", bevel_box(1.1, 1.8, 0.15, 0.05), CF((x - 0.3, 5.7, z0 + 0.675)),
                  "grey_light", shadow=False)
    board(k, dm, (0.6, 0.6, 0.15), CF((x - 0.3, 6.1, z0 + 0.825), G.facing((0, 0, 1))), "mustard", text="DANGER",
          text_color=(20, 20, 20), name="Sticker")
    k.mesh(dm, "Catch", "FuseBox__Catch", bevel_box(0.15, 0.4, 0.15, 0.03), CF((x + 0.12, 5.7, z0 + 0.825)), "black",
           shadow=False)
    hinge(dm, leaf, CF((x - 0.85, 5.7, z0 + 0.75)))
    k.part(m, "Hub", (0.4, 0.8, 0.8), CF((x + 0.55, 5.4, z0 + 0.65), G.ry(90)), "black", shape="Cylinder", grid=False)
    lev = G.Geo()
    lev.add(bevel_box(0.2, 1.2, 0.2, 0.05, c=(0, 0.6, 0)))
    lev.add(G.sphere(0.22, 8, 4, c=(0, 1.25, 0)))
    lv = k.mesh(m, "Lever", "FuseBox__Lever", lev, CF((x + 0.55, 5.4, z0 + 0.95)), "red", solid=True)
    pivot(lv, CF((x + 0.55, 5.4, z0 + 0.95), G.ry(-90)))
    moving(m, "Lever", "pointing up = ON. Rotate the pivot about X (the wall's normal): +120 deg swings it down = OFF")
    cond = G.Geo()
    for dx in (-0.5, 0.0, 0.5):
        cond.add(rod((x + dx, 6.8, z0 + 0.3), (x + dx, L.CEIL, z0 + 0.3), 0.1, 6))
    k.mesh(m, "Conduit", "FuseBox__Conduit", cond, CF(), "steel_dark", shadow=False)
    k.prop(m, "LightSwitch", C.wcf("N", x, 3.6, 0.0), name="LightSwitch")
    stand(k, m, x, z0 + 2.4, N)
    return m


def build(k):
    st = [storage_shelf(k), drinks_cooler(k), fuse_box(k)]
    dress = k.sc.folder(k.sc.root.get("Shack"), "Dressing")
    lockers(k, dress)
    side_window(k, dress)
    # the staff hooks on the west wall beside the lockers: an apron and a tea towel
    hk = C.wcf("W", -8.0, 6.8, 0.0)
    k.prop(dress, "CoatHooks", hk, name="CoatHooks")
    k.prop(dress, "Apron", hk * CF((-0.4, 0.15, 0.3)), name="Apron", seed=1)
    k.prop(dress, "TeaTowel", hk * CF((0.45, 0.15, 0.42)), name="TeaTowel")
    # the broom leans in the corner by the back door, clear of the locker doors
    k.prop(dress, "Broom", CF((WX + 0.85, L.FLOOR, -9.0), G.ry(180)), name="Broom")
    return st
