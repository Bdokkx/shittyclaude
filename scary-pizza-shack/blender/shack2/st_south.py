"""The south wall, east to west: PlushieShelf and RulesBoard (above), Register,
ServingWindow (with the PlayerBlock in its opening), ShutterButton, CCTVDesk, Sink, and the
Extinguisher bracket on the west wall over the sink. Same Models, markers and moving parts
as batch 1."""
import math

import numpy as np

import spsgeo as G
from spsgeo import CF

from . import counters as C, interior as IP, items2, layout as L
from .kit import bevel_box, ccyl, rod
from .st_common import (E, FACE, N, S_, W, board, cage_lamp, moving, pendant_lamp, pivot, spot, stand, station,
                        wall_board, weld_all)

SZ = L.IN_Z1                    # 10, the south wall's inside face
FRONT = SZ - 4.0                # 6, the counters' front edge
STZ = FRONT - IP.STAND_GAP      # 4.6, stands


def _counter(k, m, x0, x1, **kw):
    return C.counter(k, m, "S", x0, x1, 4.0, **kw)


# ---------------------------------------------------------------- plushie shelf + rules board

def plushie_shelf(k):
    """A wooden shelf on two brackets above the till; Slot1..4 along it for the plushies, a
    price card at the end."""
    m = station(k, "PlushieShelf")
    x0, x1 = 5.0, 9.2
    y = 6.8
    k.mesh(m, "Shelf", "PlushieShelf__Shelf", bevel_box(x1 - x0, 0.4, 2.0, 0.05), CF(((x0 + x1) / 2, y - 0.2, SZ - 1.0)),
           "wood", solid=True)
    k.mesh(m, "Lip", "PlushieShelf__Lip", bevel_box(x1 - x0, 0.3, 0.2, 0.05), CF(((x0 + x1) / 2, y + 0.1, SZ - 1.95)),
           "wood_dark", shadow=False)
    br = G.Geo()
    br.add(G.extrude([(0, 0), (1.6, 0), (0.2, -1.2), (0, -1.2)], 0.3, "x", (0, 0, 0)))
    for x in (x0 + 0.35, x1 - 0.35):
        k.mesh(m, "Bracket", "PlushieShelf__Bracket", br.xf(G.M(G.ry(180))), CF((x, y - 0.4, SZ)), "wood_dark",
               solid=True)
    for i in range(4):
        spot(k, m, "Slot%d" % (i + 1), x0 + 0.55 + 1.03 * i, y, SZ - 0.9, N)
    board(k, m, (1.2, 0.8, 0.15), CF((x1 - 0.7, y + 0.45, SZ - 1.85), G.rx(-15)), "cream",
          text="PLUSHIES $4.99", text_color=(150, 30, 24), name="PriceCard")
    stand(k, m, (x0 + x1) / 2, STZ, S_)
    return m


def rules_board(k):
    """The staff rules chalkboard (Face 7 x 5, its Front towards the room) in a wooden frame,
    standing off the wall on two cleats over the box station's corner, with a chalk ledge."""
    m = station(k, "RulesBoard")
    x0, x1 = 9.5, 16.5                               # the frame stays clear of the east dado rail
    xc, yc = (x0 + x1) / 2, 6.25                    # its frame clear above the worktops, under the ceiling
    zf = SZ - 0.75                                  # the face, 0.75 off the wall (clear of dado and cornice)
    k.part(m, "Face", (7.0, 5.0, 0.2), CF((xc, yc, zf)), "chalkboard", material="SmoothPlastic", grid=False)
    fr = G.Geo()
    for (cx, cy, sx, sy) in ((0, 2.6, 7.6, 0.3), (0, -2.6, 7.6, 0.3), (-3.65, 0, 0.3, 5.5), (3.65, 0, 0.3, 5.5)):
        fr.add(bevel_box(sx, sy, 0.4, 0.06, c=(cx, cy, 0.0)))
    k.mesh(m, "Frame", "RulesBoard__Frame", fr, CF((xc, yc, zf)), "wood_dark", solid=True)
    for x in (x0 + 1.0, x1 - 1.0):
        k.mesh(m, "Cleat", "RulesBoard__Cleat", bevel_box(0.6, 3.0, 0.6, 0.05), CF((x, yc, SZ - 0.3)),
               "wood_dark", solid=True)
    k.mesh(m, "Ledge", "RulesBoard__Ledge", bevel_box(6.0, 0.15, 0.4, 0.04), CF((xc, yc - 2.6, zf - 0.4)), "wood",
           shadow=False)
    chalk = G.Geo()
    for i, (dx, c) in enumerate(((-1.5, 0), (-1.2, 1), (1.8, 2))):
        chalk.add(ccyl(0.075, 0.4, 6, "x", (dx, 0, 0), 0.02))
    k.mesh(m, "Chalk", "RulesBoard__Chalk", chalk, CF((xc, yc - 2.45, zf - 0.45)), "paper", shadow=False)
    for x in (x0 + 0.4, x1 - 0.4):
        k.part(m, "Pin", (0.4, 0.4, 0.4), CF((x, yc + 2.25, zf - 0.25)), "red", shape="Ball", grid=False)
    st = np.array((11.2, L.FLOOR, 7.7))
    d = np.array((xc, L.FLOOR, zf)) - st
    k.sc.marker(m, "Stand", CF(st, G.facing(d / np.linalg.norm(d))))
    return m


# ---------------------------------------------------------------- register

def register(k):
    """The till: a compact 80s register (keys, display, the Drawer that slides out, cash
    welded inside), the TipJar with coins in it, a card imprinter and the napkin box."""
    m = station(k, "Register")
    x0, x1 = 5.0, 10.0
    _counter(k, m, x0, x1, fronts=[(2, "drawers3"), (3, "doors2")], end_left=False, end_right=True,
             owner="Register")
    tx0, tx1 = x0 + 0.5, x0 + 3.1
    tz0, tz1 = FRONT + 1.0, FRONT + 3.0
    txc = (tx0 + tx1) / 2
    W_ = WORK = L.WORK
    k.mesh(m, "TillBase", "Register__Base", bevel_box(tx1 - tx0, 0.9, tz1 - tz0, 0.08),
           CF((txc, W_ + 0.45, (tz0 + tz1) / 2)), "charcoal", solid=True)
    body = G.Geo()
    body.add(G.extrude([(0, 0), (2.0, 0), (2.0, 0.6), (0.9, 1.2), (0, 1.2)], tx1 - tx0, "x", (0, 0, 0)))
    k.mesh(m, "TillTop", "Register__Top", body, CF((txc, W_ + 0.9, tz0)), "till_cream", solid=True)
    keys = G.Geo()
    for i in range(4):
        for j in range(3):
            keys.add(bevel_box(0.4, 0.15, 0.3, 0.04, c=(-0.75 + 0.5 * i, 0.0, 0.35 * j)))
    k.mesh(m, "Keys", "Register__Keys", keys.xf(G.M(G.rx(-31))), CF((txc, W_ + 1.32, tz0 + 0.75)), "cream",
           shadow=False)
    k.mesh(m, "Display", "Register__Display", bevel_box(1.6, 0.6, 0.4, 0.06), CF((txc, W_ + 2.4, tz0 + 1.6)),
           "black", solid=True)
    k.part(m, "DisplayGlow", (1.2, 0.3, 0.15), CF((txc, W_ + 2.42, tz0 + 1.38)), (110, 230, 140), material="Neon",
           grid=False, shadow=False)
    drawer = k.mesh(m, "Drawer", "Register__Drawer", bevel_box(tx1 - tx0 - 0.4, 0.5, tz1 - tz0 - 0.1, 0.05),
                    CF((txc, W_ + 0.45, (tz0 + tz1) / 2 - 0.06)), "mustard", solid=True)
    cash = G.Geo()
    for i in range(3):
        cash.add(bevel_box(0.6, 0.15, 1.1, 0.03, c=(-0.75 + 0.75 * i, 0, 0)))
    cm = k.mesh(m, "DrawerCash", "Register__Cash", cash, CF((txc, W_ + 0.72, (tz0 + tz1) / 2)), (104, 150, 96),
                shadow=False)
    pull = k.mesh(m, "DrawerPull", "Register__Pull", bevel_box(0.8, 0.15, 0.15, 0.04),
                  CF((txc, W_ + 0.45, tz0 - 0.08)), "black", shadow=False)
    weld_all(k, drawer, [cm, pull])
    pivot(drawer, CF((txc, W_ + 0.45, tz0 - 0.1)))
    moving(m, "Drawer", "slides straight out towards the player (-Z) by 1.2; the cash inside is welded to it")
    # the tip jar (a Model as batch 1) with coins and a curling TIPS label
    tj = k.sc.model(m, "TipJar")
    c = (x1 - 0.85, W_, FRONT + 1.0)
    jar = G.outward(G.lathe([(0, 0.0), (0.4, 0.0), (0.44, 0.9), (0.36, 1.0), (0.38, 1.1), (0, 1.1)], 10))
    k.mesh(tj, "Jar", "TipJar__Jar", jar, CF(c), "glass", material="Glass", transparency=0.45, shadow=False)
    coins = G.Geo()
    for i in range(7):
        coins.add(ccyl(0.16, 0.15, 8, "y", (0.12 * math.cos(i * 2.1), 0.08 + 0.07 * i, 0.12 * math.sin(i * 2.1)),
                       0.02))
    k.mesh(tj, "Coins", "TipJar__Coins", coins, CF(c), "mustard", shadow=False)
    board(k, tj, (0.6, 0.4, 0.15), CF((c[0], c[1] + 0.55, c[2] - 0.46), G.rx(8)), "paper", text="TIPS",
          text_color=(40, 40, 40), name="Board")
    k.prop(m, "CardImprinter", CF((9.0, W_, FRONT + 2.5), G.ry(180)), name="CardMachine")
    stand(k, m, (x0 + x1) / 2, STZ, S_)
    return m


# ---------------------------------------------------------------- serving window

def serving_window(k):
    """The hatch: a steel counter running out through the window onto the outside ledge, a
    timber frame round the opening, the TicketPrinter, the TicketRail (Ticket1..5) above,
    the desk bell, napkins, a pen on a chain, the neon OPEN sign hanging in the window, the
    roll-down Shutter in its housing outside, and the invisible PlayerBlock in the opening."""
    m = station(k, "ServingWindow")
    x0, x1 = L.WIN_X0, L.WIN_X1                   # -5..5
    _counter(k, m, x0, x1, fronts=[(4, "doors2"), (2, "drawers"), (4, "doors2")], end_left=False, end_right=False,
             owner="ServingWindow")
    W_ = L.WORK
    # the hatch's steel lining: jambs and head line the opening right through the wall, a raised
    # sill plate runs from the counter out over the wall to the ledge
    zl0, zl1 = SZ - 0.1, L.OUT_Z1 + 0.5
    lin = G.Geo()
    for sx in (-1, 1):
        lin.add(bevel_box(0.3, L.WIN_Y1 - W_, zl1 - zl0, 0.04, c=(sx * (x1 - 0.15), (W_ + L.WIN_Y1) / 2, 0)))
    lin.add(bevel_box(x1 - x0, 0.3, zl1 - zl0, 0.04, c=(0, L.WIN_Y1 - 0.15, 0)))
    lin.add(bevel_box(x1 - x0, 0.15, zl1 - zl0 + 0.15, 0.04, c=(0, W_ + 0.075, 0.075)))
    k.mesh(m, "Lining", "ServingWindow__Lining", lin, CF((0.0, 0.0, (zl0 + zl1) / 2)), "steel", solid=True)
    k.box(m, "Ledge", (x0 - 1, W_ - 0.8, L.OUT_Z1 + 0.5), (x1 + 1, W_, L.OUT_Z1 + 2.5), "steel", solid=True)
    k.mesh(m, "LedgeEdge", "ServingWindow__LedgeEdge", bevel_box(12.0, 0.4, 0.2, 0.06),
           CF((0.0, W_ - 0.2, L.OUT_Z1 + 2.6)), "steel_dark", shadow=False)
    for x in (x0 + 0.5, x1 - 0.5):
        br = G.extrude([(0, 0), (1.9, 0), (0.25, -1.4), (0, -1.4)], 0.3, "x", (0, 0, 0))
        k.mesh(m, "LedgeBracket", "ServingWindow__Bracket", br, CF((x, W_ - 0.8, L.OUT_Z1 + 0.5)), "mustard",
               solid=True)
    spot(k, m, "Handover", 0.0, W_, (FRONT + SZ) / 2, S_)
    k.sc.marker(m, "Customer", CF((0.0, 0.0, L.QUEUE_Z), G.facing(N)))
    # desk bell, napkins, the pen on its chain
    bc = (x1 - 1.0, W_, FRONT + 1.0)
    bell = G.outward(G.lathe([(0, 0.15), (0.42, 0.15), (0.4, 0.25), (0.3, 0.45), (0.12, 0.55), (0, 0.57)], 12))
    bell.add(ccyl(0.08, 0.2, 6, "y", (0, 0.65, 0), 0.02))
    k.mesh(m, "Bell", "ServingWindow__Bell", bell, CF(bc), "mustard", shadow=False)
    k.mesh(m, "BellBase", "ServingWindow__BellBase", ccyl(0.48, 0.15, 12, "y", (0, 0.075, 0), 0.03), CF(bc), "black",
           shadow=False)
    k.prop(m, "NapkinBox", CF((x0 + 3.6, W_, FRONT + 1.0)), name="Napkins")
    k.prop(m, "PenOnChain", CF((x1 - 2.4, W_, FRONT + 1.2)), name="PenOnChain")
    # ticket printer (a Model, as batch 1)
    tp = k.sc.model(m, "TicketPrinter")
    px0, px1 = x0 + 0.6, x0 + 2.6
    k.mesh(tp, "Body", "TicketPrinter__Body", bevel_box(2.0, 1.2, 2.0, 0.12), CF(((px0 + px1) / 2, W_ + 0.6, FRONT + 2.4)),
           "grey_dark", solid=True)
    k.mesh(tp, "Top", "TicketPrinter__Top", bevel_box(2.0, 0.4, 1.0, 0.08), CF(((px0 + px1) / 2, W_ + 1.4, FRONT + 2.9)),
           "grey", solid=True)
    paper = bevel_box(1.0, 0.15, 0.8, 0.03).xf(G.M(G.rx(-25)))
    k.mesh(tp, "Paper", "TicketPrinter__Paper", paper, CF(((px0 + px1) / 2, W_ + 1.32, FRONT + 2.05)), "paper",
           shadow=False)
    k.part(tp, "Led", (0.4, 0.2, 0.15), CF((px1 - 0.4, W_ + 0.9, FRONT + 1.38)), (90, 255, 120), material="Neon",
           grid=False, shadow=False)
    # ticket rail above the window, inside (Ticket1..5 hang from it)
    tr = k.sc.model(m, "TicketRail")
    k.mesh(tr, "Rail", "TicketRail__Rail", bevel_box(8.0, 0.4, 0.6, 0.08), CF((0.0, 8.2, SZ - 0.75)), "steel",
           solid=True)
    for x in (-3.6, 3.6):
        k.mesh(tr, "Bracket", "TicketRail__Bracket", bevel_box(0.3, 0.3, 0.7, 0.05), CF((x, 8.2, SZ - 0.35)),
               "steel_dark", shadow=False)
    for i in range(5):
        spot(k, tr, "Ticket%d" % (i + 1), -3.2 + 1.6 * i, 8.0, SZ - 1.05, N)
    # neon OPEN sign hanging in the window (always lit), chains to the frame head
    op = k.sc.model(m, "OpenSign")
    bulb = k.part(op, "Bulb", (3.0, 1.0, 0.15), CF((2.6, 6.0, SZ + 0.35)), (255, 70, 60), material="Neon",
                  grid=False, shadow=False)
    board(k, op, (3.4, 1.4, 0.15), CF((2.6, 6.0, SZ + 0.5), FACE["N"]), (30, 20, 24), text="OPEN",
          text_color=(255, 90, 80), name="Board")
    ch = G.Geo()
    for x in (-1.4, 1.4):
        ch.add(rod((x, 0.7, 0), (x, 1.0, 0), 0.075, 4))
    k.mesh(op, "Chains", "OpenSign__Chains", ch, CF((2.6, 6.0, SZ + 0.4)), "steel_dark", shadow=False)
    k.lamp(op, bulb, "Always", "Point", 10.0, 0.8, (255, 70, 60), shadows=False, flicker=0.15)
    # the roll-down shutter (open: rolled up into the housing over the window, outside)
    sh = []
    zs0 = L.OUT_Z1 + 0.65
    for i in range(9):
        y0 = L.WIN_Y1 + 0.4 * i
        dz = 0.0 if i % 2 == 0 else 0.1
        col_ = "steel_dark" if i == 0 else ("grey" if i % 2 else "steel")
        sh.append(k.box(m, "Shutter" if i == 0 else "Slat", (x0, y0, zs0 + dz), (x1, y0 + 0.4, zs0 + 1 + dz), col_,
                        solid=True))
    weld_all(k, sh[0], sh[1:])
    sh[0].p["anchored"] = True
    sh[0].p["massless"] = False
    pivot(sh[0], CF((0.0, L.WIN_Y1, zs0 + 0.5)))
    moving(m, "Shutter", "starts OPEN (rolled up into the housing over the window). Slide it straight down 3.6 to "
                         "close: pivot Y 7.0 = open, Y 3.4 = closed (resting on the sill). The 8 slats are welded to it")
    hz0 = L.OUT_Z1 + 0.5
    k.mesh(m, "ShutterHousing", "ServingWindow__Housing", _housing(), CF((0.0, L.WIN_Y1, hz0)), "steel_dark",
           solid=True)
    # the PlayerBlock: invisible, collides, fills the opening so nobody climbs through
    k.part(m, "PlayerBlock", (x1 - x0, L.WIN_Y1 - W_, 1.0), CF((0.0, (W_ + L.WIN_Y1) / 2, (SZ + L.OUT_Z1) / 2)),
           (255, 255, 255), transparency=1.0, solid=True, shadow=False, collide=True, touch=False, query=False,
           grid=False)
    stand(k, m, 0.0, STZ, S_)
    return m


def _housing():
    """The shutter box over the window outside: a steel case round the rolled slats with a
    sloped top and end caps (local origin at the window head, the wall face)."""
    g = G.Geo()
    g.add(bevel_box(11.0, 3.9, 0.2, 0.05, c=(0, 2.05, 1.65)))          # front
    g.add(G.extrude([(0, 0), (1.75, 0), (1.75, 0.3), (0, 0.9)], 11.0, "x", (0, 3.9, 0)).xf(G.M(np.eye(3))))
    for sx in (-1, 1):
        g.add(bevel_box(0.5, 4.2, 1.8, 0.05, c=(sx * 5.25, 2.1, 0.85)))
    return g


# ---------------------------------------------------------------- shutter button

def shutter_button(k):
    """A big red mushroom button on a yellow-and-black hazard plate, by the window."""
    m = station(k, "ShutterButton")
    x = -6.0
    y = 5.6
    base = k.mesh(m, "Base", "ShutterButton__Base", bevel_box(2.0, 2.0, 0.6, 0.1), CF((x, y, SZ - 0.3)), "mustard",
                  solid=True)
    stripes = G.Geo()                                   # diagonal hazard stripes kept inside the plate
    for c in (-1.4, -0.7, 0.0, 0.7, 1.4):
        ln = (2.0 - abs(c)) * 1.414 - 0.35
        stripes.add(bevel_box(0.3, ln, 0.15, 0.03).xf(G.M(G.rz(45))).xf(G.T(c / 2, c / 2, 0)))
    k.mesh(m, "Stripes", "ShutterButton__Stripes", stripes, CF((x, y, SZ - 0.62)), "black", shadow=False)
    k.mesh(m, "Collar", "ShutterButton__Collar", G.ring(0.62, 0.48, 0.2, 12, "z", (0, 0, 0)), CF((x, y, SZ - 0.72)),
           "grey_dark", shadow=False)
    dome = G.outward(G.lathe([(0, 0.0), (0.5, 0.0), (0.52, 0.12), (0.44, 0.3), (0.22, 0.42), (0, 0.45)], 12))
    btn = k.mesh(m, "Button", "ShutterButton__Button", dome.xf(G.M(G.rx(-90))), CF((x, y, SZ - 0.72)), "red",
                 solid=True)
    pivot(btn, CF((x, y, SZ - 0.72)))
    moving(m, "Button", "presses in: move it +Z (towards the wall) by 0.2, then back")
    board(k, m, (1.8, 0.5, 0.15), CF((x, y + 1.35, SZ - 0.075)), "black", text="SHUTTER", text_color=(240, 200, 60),
          name="Label")
    stand(k, m, x, FRONT - 0.8, S_)
    return m


# ---------------------------------------------------------------- camera desk

def cctv_desk(k):
    """The camera desk: a low desk on two pedestals, two CRTs (one on a stack of VCRs) with
    bezels and knobs (Monitor1/2.Screen), the SwitchBox, a keyboard, a mug, cables running
    down behind the desk to a socket; the cork board, calendar, the Radio on its shelf and the
    wall phone above; a swivel stool pushed aside."""
    m = station(k, "CCTVDesk")
    x0, x1 = -13.0, -7.0
    top = IP.DESK[4]                                   # 2.6
    k.box(m, "Top", (x0, top - 0.4, FRONT), (x1, top, SZ), "wood_dark", solid=True)
    k.mesh(m, "TopEdge", "CCTVDesk__Edge", bevel_box(6.0, 0.4, 0.2, 0.06), CF(((x0 + x1) / 2, top - 0.2, FRONT - 0.05)),
           "wood", shadow=False)
    for (a, b) in ((x0, x0 + 2), (x1 - 2, x1)):
        k.mesh(m, "Pedestal", "CCTVDesk__Pedestal", bevel_box(2.0, top - 0.4 - L.FLOOR, SZ - FRONT - 0.4, 0.06),
               CF(((a + b) / 2, (L.FLOOR + top - 0.4) / 2, (FRONT + 0.4 + SZ) / 2)), "wood", solid=True)
        for i, (ya, yb) in enumerate(((0.5, 1.2), (1.3, 2.1))):
            k.mesh(m, "DrawerFront", "CCTVDesk__Drawer%d" % i, C.door_geo(1.8, yb - ya - 0.06, frame=0.18),
                   CF(((a + b) / 2, (ya + yb) / 2, FRONT + 0.4), G.ry(180)), "wood_light", shadow=False)
            k.mesh(m, "Pull", "Counter__Pull6", C.pull_geo(0.6), CF(((a + b) / 2, yb - 0.25, FRONT + 0.2), G.ry(180)),
                   "steel_light", shadow=False)
    k.box(m, "Modesty", (x0 + 2, 0.6, SZ - 1), (x1 - 2, top - 0.4, SZ), "wood", solid=True)
    W_ = top
    for i, (a, b, base_y) in enumerate(((x0 + 0.3, x0 + 2.9, W_ + 1.2), (x1 - 2.9, x1 - 0.3, W_))):
        mon = k.sc.model(m, "Monitor%d" % (i + 1))
        xc = (a + b) / 2
        k.mesh(mon, "Body", "Monitor__Body", _crt(), CF((xc, base_y, FRONT + 1.4)), "crt_cream", solid=True)
        k.part(mon, "Screen", (2.4, 1.8, 0.2), CF((xc, base_y + 1.25, FRONT + 1.35)), "screen", material="SmoothPlastic",
               grid=False)
        knobs = G.Geo()
        for dx in (0.75, 1.05):
            knobs.add(ccyl(0.1, 0.15, 6, "z", (dx, 0, 0), 0.02))
        k.mesh(mon, "Knobs", "CCTVDesk__Knobs", knobs, CF((xc - 0.1, base_y + 0.2, FRONT + 1.12)), "black",
               shadow=False)
    k.prop(m, "VCRStack", CF((x0 + 1.6, W_, FRONT + 2.4)), name="VCRs")
    # switch box (a Model, as batch 1)
    sb = k.sc.model(m, "SwitchBox")
    k.mesh(sb, "Box", "SwitchBox__Box", bevel_box(2.0, 0.4, 1.0, 0.06), CF((x0 + 3.0, W_ + 0.2, FRONT + 0.75)),
           "grey_dark", solid=True)
    btns = G.Geo()
    for i in range(4):
        btns.add(bevel_box(0.3, 0.15, 0.3, 0.03, c=(-0.6 + 0.4 * i, 0.075, 0)))
    k.mesh(sb, "Buttons", "SwitchBox__Buttons", btns, CF((x0 + 3.1, W_ + 0.4, FRONT + 0.8)), "red", shadow=False)
    k.part(sb, "Lamp", (0.4, 0.2, 0.2), CF((x0 + 2.25, W_ + 0.5, FRONT + 0.55)), (120, 255, 120), material="Neon",
           grid=False, shadow=False)
    k.prop(m, "Keyboard", CF((x1 - 1.9, W_, FRONT + 0.75)), name="Keyboard")
    k.prop(m, "Mug", CF((x1 - 0.45, W_, FRONT + 0.55)), name="Mug")
    cables = G.Geo()
    for xs in (x0 + 1.6, x1 - 1.6):
        cables.add(G.tube([(xs, W_ + 0.6, FRONT + 3.6), (xs + 0.2, W_ + 0.2, SZ - 0.25), (xs + 0.3, W_ - 0.6, SZ - 0.2),
                           (xs + 0.2, 0.9, SZ - 0.2), (-10.0, 0.6, SZ - 0.2)], 0.075, 4))
    k.mesh(m, "Cables", "CCTVDesk__Cables", cables, CF(), "black", shadow=False)
    k.prop(m, "Socket", C.wcf("S", -10.0, 0.9, 0.0), name="Socket")
    # the wall over the desk: radio shelf + Radio, cork board, calendar, the phone
    # the radio's shelf at head height on the west wall, just round the corner from the desk
    k.prop(m, "WallShelfSmall", C.wcf("W", 8.0, 5.75, 0.0), name="RadioShelf")
    radio(k, m, C.wcf("W", 8.0, 5.75, 0.6) * CF((0, 0, 0), G.ry(180)))
    k.prop(m, "CorkBoard", C.wcf("S", -9.7, 6.2, 0.0), name="CorkBoard")
    k.prop(m, "Calendar", C.wcf("S", -12.0, 7.6, 0.0), name="Calendar")
    ph = k.sc.model(m, "Phone")
    px = -7.8
    k.mesh(ph, "Base", "Phone__Base", bevel_box(1.0, 1.6, 0.6, 0.12), CF((px, 6.2, SZ - 0.3)), "red", solid=True)
    dial = G.Geo()
    dial.add(ccyl(0.36, 0.15, 12, "z", (0, 0, 0), 0.03))
    for i in range(8):
        a = math.tau * i / 10 + 0.5
        dial.add(ccyl(0.06, 0.15, 6, "z", (0.24 * math.cos(a), 0.24 * math.sin(a), -0.06), 0.02))
    k.mesh(ph, "Dial", "Phone__Dial", dial, CF((px, 6.0, SZ - 0.68)), "cream", shadow=False)
    hs = G.Geo()
    hs.add(bevel_box(0.25, 1.1, 0.25, 0.08))
    for sy in (-1, 1):
        hs.add(bevel_box(0.32, 0.36, 0.44, 0.08, c=(0, sy * 0.62, -0.12)))
    hsp = k.mesh(ph, "Handset", "Phone__Handset", hs, CF((px + 0.68, 6.35, SZ - 0.5)), "red", solid=False)
    pivot(hsp, hsp.p["cf"])
    moving(ph, "Handset", "free part: lift it off the hook (move it where you like); pivot at its centre")
    cord = G.tube([(px + 0.55, 5.55, SZ - 0.4), (px + 0.6, 4.9, SZ - 0.35), (px + 0.75, 4.7, SZ - 0.4),
                   (px + 0.82, 5.1, SZ - 0.42), (px + 0.72, 5.8, SZ - 0.45)], 0.075, 5)
    k.mesh(ph, "Cord", "Phone__Cord", cord, CF(), "black", shadow=False)
    k.prop(m, "SwivelStool", CF((x0 + 1.0, L.FLOOR, FRONT - 0.75), G.ry(25)), name="Stool")
    # the desk's lamp: an enamel pendant over the monitors
    pendant_lamp(k, m, "DeskLamp", -9.5, 8.4, drop=2.2, bright=0.9, rng=11.0)
    stand(k, m, (x0 + x1) / 2, STZ, S_)
    return m


def _crt():
    """A chunky CRT: a bevelled box front with the bezel, the tapering back (local origin at
    the bottom of the front face, +Z away from the viewer)."""
    g = G.Geo()
    g.add(bevel_box(2.6, 2.3, 0.6, 0.12, c=(0, 1.15, 0.3)))
    g.add(G.outward(G.loft([[(-1.2, 0.1, 0.6), (1.2, 0.1, 0.6), (1.2, 2.2, 0.6), (-1.2, 2.2, 0.6)],
                            [(-0.7, 0.4, 2.2), (0.7, 0.4, 2.2), (0.7, 1.8, 2.2), (-0.7, 1.8, 2.2)]])))
    return g


def radio(k, m, base):
    """The Radio (a Model with parts Speaker and Dial): an 80s radio-cassette on its shelf.
    base: a frame on the shelf top, -Z towards the room (the speaker side)."""
    r = k.sc.model(m, "Radio")
    k.mesh(r, "Body", "Radio__Body", bevel_box(1.6, 0.9, 0.6, 0.12), base * CF((0, 0.45, 0)), "charcoal", solid=True)
    k.mesh(r, "Speaker", "Radio__Speaker", ccyl(0.3, 0.15, 10, "z", (0, 0, 0), 0.03), base * CF((-0.4, 0.42, -0.33)),
           "black", shadow=False)
    k.mesh(r, "Dial", "Radio__Dial", bevel_box(0.6, 0.3, 0.15, 0.03), base * CF((0.35, 0.55, -0.33)), "cream",
           shadow=False)
    k.mesh(r, "Handle", "Radio__Handle", G.tube([(-0.6, 0.9, 0), (-0.5, 1.15, 0), (0.5, 1.15, 0), (0.6, 0.9, 0)],
                                                 0.075, 4), base, "steel_dark", shadow=False)
    k.mesh(r, "Aerial", "Radio__Aerial", rod((0.6, 0.9, 0), (1.2, 2.2, -0.1), 0.075, 4), base, "steel_light",
           shadow=False)
    k.mark_used("Radio")
    return r


def desk_lamp(k, m, pos):
    lm = k.sc.model(m, "DeskLamp")
    x, y, z = pos
    k.mesh(lm, "Base", "DeskLamp__Base", ccyl(0.45, 0.2, 10, "y", (0, 0.1, 0), 0.05), CF((x, y, z)), "shade_green")
    k.mesh(lm, "Neck", "DeskLamp__Neck", G.tube([(0, 0.2, 0), (0, 1.0, 0.1), (-0.3, 1.6, -0.3), (-0.6, 1.7, -0.8)],
                                                 0.075, 5), CF((x, y, z)), "steel_dark", shadow=False)
    sh = G.outward(G.lathe([(0.0, 0.3), (0.2, 0.3), (0.45, -0.1), (0.4, -0.15), (0.0, 0.1)], 10))
    k.mesh(lm, "Shade", "DeskLamp__Shade", sh, CF((x - 0.65, y + 1.6, z - 0.9), G.rx(-20)), "shade_green")
    bulb = k.part(lm, "Bulb", (0.3, 0.3, 0.3), CF((x - 0.65, y + 1.5, z - 0.95)), (255, 222, 170), material="Neon",
                  shape="Ball", grid=False, shadow=False)
    k.lamp(lm, bulb, "Shack", "Spot", 9.0, 0.8, (255, 196, 132), angle=100.0)
    k.mark_used("DeskLamp")


# ---------------------------------------------------------------- sink + extinguisher

def sink(k):
    """A deep steel sink in a counter with an open bay under it (the trap, the mop bucket);
    the tap, a drying rack with plates, soap dispenser, paper towels, the hand-wash notice,
    the first-aid box and a caged lamp over it."""
    m = station(k, "Sink")
    x0, x1 = -17.0, -13.0                             # the sink's own bay; a cupboard runs on into the corner
    hx0, hx1, hz0, hz1 = x0 + 1.0, x1 - 1.0, FRONT + 1.0, SZ - 1.0
    _counter(k, m, L.IN_X0, x1, fronts=[(x0 - L.IN_X0, "doors2"), (4, "open")], end_left=False, end_right=True,
             owner="Sink", top_name="Top", top_hole=(hx0, hx1, SZ - hz1, SZ - hz0))
    k.mesh(m, "Basin", "Sink__Basin", _basin(hx1 - hx0, hz1 - hz0), CF(((hx0 + hx1) / 2, L.WORK + 0.02, (hz0 + hz1) / 2)),
           "steel_light", solid=True)
    tap = G.Geo()
    tap.add(G.tube([(0, 0, 0), (0, 1.0, 0), (0, 1.35, -0.3), (0, 1.15, -0.8), (0, 0.95, -0.85)], 0.1, 6))
    tap.add(ccyl(0.22, 0.15, 8, "y", (0, 0.075, 0), 0.03))
    for sx in (-1, 1):
        tap.add(bevel_box(0.4, 0.15, 0.15, 0.03, c=(sx * 0.4, 0.4, 0.05)))
    k.mesh(m, "Faucet", "Sink__Tap", tap, CF(((hx0 + hx1) / 2, L.WORK, SZ - 0.55)), "steel_light", shadow=False)
    k.prop(m, "MopBucket", C.wcf("S", -15.0, 0.9, 1.9), name="MopBucket")
    k.prop(m, "DryingRack", CF((x1 - 0.55, L.WORK, FRONT + 1.6), G.ry(90)), name="DryingRack")
    k.prop(m, "SoapDispenser", C.wcf("S", x0 + 1.0, 5.0, 0.0), name="Soap")
    k.prop(m, "TowelDispenser", C.wcf("S", x0 + 2.6, 5.6, 0.0), name="PaperTowels")
    wall_board(k, m, "S", x0 + 2.2, 7.6, (1.6, 1.2), "paper", text="EMPLOYEES MUST WASH HANDS",
               text_color=(30, 60, 140), name="HandWashNotice")
    k.prop(m, "FirstAid", C.wcf("S", x1 - 0.55, 7.4, 0.0), name="FirstAid")
    stand(k, m, (x0 + x1) / 2 + 1.2, STZ, S_)
    return m


def _basin(w, d):
    g = G.Geo()
    h = 1.2
    g.add(bevel_box(w, 0.15, d, 0.04, c=(0, -h, 0)))
    g.add(bevel_box(w, h, 0.15, 0.04, c=(0, -h / 2, d / 2 - 0.075)))
    g.add(bevel_box(w, h, 0.15, 0.04, c=(0, -h / 2, -d / 2 + 0.075)))
    for sx in (-1, 1):
        g.add(bevel_box(0.15, h, d, 0.04, c=(sx * (w / 2 - 0.075), -h / 2, 0)))
    g.add(G.ring(w / 2 + 0.2, w / 2 - 0.05, 0.15, 4, c=(0, 0, 0)).xf(G.M(G.ry(45)) @ G.S(1.0, 1.0, d / w)))
    g.add(ccyl(0.22, 0.15, 8, "y", (0, -h + 0.1, 0), 0.03))
    return g


def extinguisher(k):
    """The extinguisher by the back door: a bracket and cradle on the fridge's side facing the
    door, the FIRE sign above, and the Slot where the FireExtinguisher item stands (Slot faces
    into the room, as batch 1)."""
    m = station(k, "Extinguisher")
    xf, zc = -13.0, -6.4                              # the fridge's west side, by the door
    br = G.Geo()
    br.add(bevel_box(0.2, 0.4, 0.9, 0.05, c=(0.1, 0, 0)))
    br.add(bevel_box(0.6, 0.15, 0.9, 0.04, c=(0.4, -0.15, 0)))
    k.mesh(m, "Bracket", "Extinguisher__Bracket", br.xf(G.M(G.ry(180))), CF((xf, 6.8, zc)), "black", shadow=False)
    k.box(m, "Cradle", (xf - 1, 4.4, zc - 0.5), (xf, 4.8, zc + 0.5), "black", solid=True)
    board(k, m, (1.0, 0.6, 0.15), CF((xf - 0.075, 7.8, zc), FACE["E"]), "red", text="FIRE",
          text_color=(255, 255, 255), name="Sign")
    fe = items2.get("FireExtinguisher")
    held = CF((xf - 0.55, 6.85, zc), G.facing(W))
    slot = held * fe.rest()
    k.sc.marker(m, "Slot", CF((slot.p[0], 4.8, slot.p[2]), slot.R))
    st = np.array((-14.8, L.FLOOR, zc - 0.2))
    d = np.array((slot.p[0], L.FLOOR, zc)) - st
    k.sc.marker(m, "Stand", CF(st, G.facing(d / np.linalg.norm(d))))
    return m


def build(k):
    return [plushie_shelf(k), rules_board(k), register(k), serving_window(k), shutter_button(k), cctv_desk(k),
            sink(k), extinguisher(k)]
