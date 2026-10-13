"""The farm yard (the safe zone): the plot markers, the three stalls by the gate, the spawn pad,
and a real farm yard round the meeting place: a barn front, a windmill, a well, a tractor, a
scarecrow, hay bales, potato crates, flower beds, lamp posts and benches. The avenue
(X -20..20) stays clear from the south wall to the gate, and every plot stays bare."""
import math

import numpy as np

import spsgeo as G
from spsgeo import CF, T, RX, RY, RZ, S

from . import layout as L
from . import props as P
from .batch import Batcher
from .geo import bevel_box, ccyl, cfrustum, rod
from .kit import darker, facing, lighter

BARN_RED = (210, 56, 48)
TRIM = (250, 248, 240)
ROOF = (110, 74, 66)


def build(k, root, markers, rng):
    y = k.sc.folder(root, "Yard")
    b = Batcher(k, k.sc.folder(y, "Scenery"), "Yard")
    for name, (x, z), (dx, dz), _ in L.plots():
        k.marker(markers, name, CF((x, 0.0, z), facing(dx, dz)))
    k.marker(markers, "Spawn", CF((L.SPAWN[0], 0.0, L.SPAWN[1]), facing(0.0, -1.0)))
    spawn_pad(k, y)
    stall(k, y, "TrailShop", L.TRAIL_SHOP, 1.0, (150, 80, 220), trail_rack)
    stall(k, y, "SpeedShop", L.SPEED_SHOP, -1.0, (50, 130, 240), sneaker_roof)
    index_board(k, y)
    barn(k, y)
    windmill(k, y)
    well(k, y, b, (-42.0, 98.0))
    tractor(b, (44.0, 132.0), 200.0)
    scarecrow(b, (-48.0, 58.0), 120.0)
    for (x, z, a) in ((-54, 132, 10), (-50, 136, 80), (-57, 137, 35), (50, 170, 0), (54, 165, 90), (-30, 166, 20),
                      (28, 74, 60)):
        b.add_parts("Hay", P.hay_bale(), CF((x, 0.0, z), G.ry(a)))
    b.add_parts("Hay", [(n, c, g.xf(T(0, 2.4, 0))) for (n, c, g) in P.hay_bale()], CF((-53.0, 0.0, 134.0), G.ry(50)))
    for (x, z, a) in ((-31, 36, 15), (-28, 39, -10), (31, 38, 5), (60, 110, 40), (58, 114, 0), (-60, 172, 25),
                      (34, 150, 30)):
        b.add_parts("Crates", P.crate(rng=rng), CF((x, 0.0, z), G.ry(a)))
    for z in (50.0, 92.0, 150.0):
        for sx in (-1, 1):
            b.add_parts("FlowerBeds", P.flower_bed(9.0, 3.0, rng), CF((sx * 26.0, 0.0, z), G.ry(90)))
    lamps = k.sc.folder(y, "Lamps")
    for z in (14.0, 44.0, 76.0, 108.0, 140.0, 172.0):
        for sx in (-1, 1):
            lamp(k, lamps, (sx * 22.6, z))
    for sx in (-1, 1):
        b.add_parts("Benches", P.bench(6.0), CF((sx * 25.5, 0.0, 120.0), G.ry(-90 * sx)))
    for (x, z) in ((-100, 4), (-92, 5), (96, 4), (104, 5), (110, 3)):
        b.add_parts("Barrels", P.barrel(), CF((x, 0.0, z), G.ry(x * 7)))
    for (x, z) in ((-64, 8), (64, 8), (-64, 182), (64, 182)):
        b.add_parts("Bushes", P.bush(2.4, P.LEAF, rng), CF((x, 0.0, z)))
    for (x, z) in ((-36, 150), (36, 92), (-58, 96), (58, 58), (-26, 106)):
        b.add_parts("Flowers", P.flower_clump(rng, 6), CF((x, 0.0, z)))
    for (x, z) in ((-56.0, 178.0), (56.0, 92.0), (-34.0, 70.0), (50.0, 178.0), (-56.0, 16.0)):
        b.add_parts("Trees", P.tree_round(13.0 + rng.uniform(-1, 2), 4.6, fruit=P.RED, rng=rng),
                    CF((x, 0.0, z), G.ry(rng.uniform(0, 90))))
    for (x, z, a_) in ((-34.0, 128.0, 0.0), (36.0, 104.0, 90.0)):
        b.add_parts("Picnic", picnic_table(), CF((x, 0.0, z), G.ry(a_)))
    b.add_parts("PotatoPile", potato_pile(rng), CF((38.0, 0.0, 160.0)))
    b.add_parts("Signpost", signpost(), CF((-24.5, 0.0, 30.0), G.ry(90)))
    b.flush()
    return y


def picnic_table():
    g = G.Geo()
    g.add(bevel_box(7.0, 0.5, 3.4, 0.12, (0, 2.9, 0)))
    for sz in (-1, 1):
        g.add(bevel_box(7.0, 0.4, 1.2, 0.1, (0, 1.6, sz * 2.6)))
    for sx in (-1, 1):
        for sg in (-1, 1):
            g.add(bevel_box(0.5, 3.4, 0.5, 0.1, (0, 0, 0)).xf(T(sx * 2.8, 1.5, 0) @ RX(sg * 32)))
    cloth = G.Geo()
    cloth.add(bevel_box(4.0, 0.2, 3.5, 0.06, (0, 3.2, 0)))
    return [("Picnic", P.WOOD_LIGHT, g), ("Cloth", (230, 70, 70), cloth)]


def potato_pile(rng):
    g = G.Geo()
    for i in range(26):
        layer = 0 if i < 13 else (1 if i < 21 else 2)
        r = (5.0, 3.4, 1.6)[layer] * math.sqrt(rng.random())
        a = rng.uniform(0, math.tau)
        pg, _ = P.potato_geo(2.0, 1.3, 1.1, eyes=False)
        g.add(pg.xf(T(r * math.cos(a), layer * 0.95, r * math.sin(a)) @ RY(rng.uniform(0, 180))))
    sack = G.Geo()
    sack.add(bevel_box(2.4, 3.0, 2.0, 0.5, (6.0, 1.5, 1.0)))
    sack.add(bevel_box(1.4, 0.8, 1.2, 0.3, (6.0, 3.3, 1.0)))
    return [("Potatoes", P.POTATO, g), ("Sack", (210, 186, 140), sack)]


def signpost():
    g = G.Geo()
    g.add(bevel_box(0.8, 9.0, 0.8, 0.15, (0, 4.5, 0)))
    arrows = G.Geo()
    for (y, a_, l) in ((7.6, 0, 5.0), (6.2, 160, 4.4), (4.8, 20, 4.8)):
        arr = G.Geo()
        arr.add(bevel_box(l, 1.0, 0.4, 0.1, (l / 2, 0, 0)))
        arr.add(bevel_box(1.0, 1.0, 0.4, 0.1, (0, 0, 0)).xf(T(l + 0.2, 0, 0) @ RZ(45) @ S(1.0, 1.0, 1.0)))
        arrows.add(arr.xf(T(0, y, 0) @ RY(a_)))
    return [("Signpost", P.WOOD_DARK, g), ("Arrows", P.WOOD_LIGHT, arrows)]


# ---------------------------------------------------------------- spawn pad

def spawn_pad(k, parent):
    x, z = L.SPAWN
    g = G.Geo()
    g.add(ccyl(7.0, 0.3, 16, "y", (0, 0.05, 0), 0.08))
    ring = G.lathe_loop([(5.4, 0.18), (6.4, 0.18), (6.4, 0.42), (5.4, 0.42)], 16)
    k.mesh(parent, "SpawnPad", "Yard_SpawnPad", g, CF((x, 0.0, z)), (255, 236, 150))
    k.mesh(parent, "SpawnRing", "Yard_SpawnRing", ring, CF((x, 0.0, z)), (250, 150, 50))


# ---------------------------------------------------------------- stalls

def stall(k, parent, name, pos, face_x, awning_col, extra):
    """A market stall facing the avenue (+X when face_x = 1): a counter, four posts, a striped
    awning, a sign Board over it and an invisible Prompt at chest height in front."""
    m = k.sc.model(parent, name)
    x0, z0 = pos
    R = facing(face_x, 0.0)
    fr = CF((x0, 0.0, z0), R)                      # stall space: front -Z = towards the avenue
    W, D, Hp = 14.0, 8.0, 9.0
    wood = P.WOOD
    g = G.Geo()
    for (px, pz) in ((-W / 2 + 0.6, -D / 2 + 0.6), (W / 2 - 0.6, -D / 2 + 0.6), (-W / 2 + 0.6, D / 2 - 0.6),
                     (W / 2 - 0.6, D / 2 - 0.6)):
        g.add(bevel_box(1.0, Hp, 1.0, 0.15, (px, Hp / 2, pz)))
    k.mesh(m, "Posts", "Stall_Posts", g, fr, wood)
    counter = k.solid(m, "Counter", (W - 1.2, 3.6, 2.6), fr * CF((0.0, 1.8, -D / 2 + 1.6)), P.WOOD_LIGHT)
    k.mesh(m, "CounterTop", "Stall_CounterTop", bevel_box(W - 0.4, 0.5, 3.2, 0.12), fr * CF((0.0, 3.85, -D / 2 + 1.6)),
           lighter(awning_col, 0.5))
    k.mesh(m, "Back", "Stall_Back", bevel_box(W - 1.2, Hp - 1.0, 0.6, 0.1, (0, (Hp - 1.0) / 2, D / 2 - 0.6)), fr,
           darker(P.WOOD_LIGHT, 0.9))
    # striped awning, sloping down to the front
    stripes_a, stripes_b = G.Geo(), G.Geo()
    n = 7
    for i in range(n):
        sx = -W / 2 - 0.5 + (W + 1.0) * (i + 0.5) / n
        piece = bevel_box((W + 1.0) / n + 0.02, 0.4, D + 2.0, 0.08, (0, 0, 0)).xf(T(sx, Hp + 0.9, -0.5) @ RX(-14))
        (stripes_a if i % 2 == 0 else stripes_b).add(piece)
        scal = bevel_box((W + 1.0) / n + 0.02, 1.2, 0.4, 0.08, (sx, Hp - 0.3, -D / 2 - 1.55))
        (stripes_a if i % 2 == 0 else stripes_b).add(scal)
    k.mesh(m, "Awning", "Stall_AwningA", stripes_a, fr, awning_col)
    k.mesh(m, "AwningStripes", "Stall_AwningB", stripes_b, fr, P.WHITE)
    board_cf = fr * CF((0.0, Hp + 3.4, 0.6))
    k.mesh(m, "SignFrame", "Stall_SignFrame", bevel_box(11.0, 3.8, 0.6, 0.15), board_cf * CF((0, 0, 0.35)),
           darker(awning_col, 0.7))
    bd = k.board(m, 10.0, 3.0, board_cf)
    k.prompt(m, fr * CF((0.0, 3.2, -D / 2 - 2.5)))
    m.p["primary"] = counter
    extra(k, m, fr, W, D, Hp)
    return m


def trail_rack(k, m, fr, W, D, Hp):
    """A rack of coloured ribbons and streamers on the stall's back, swaying."""
    bar = G.Geo()
    bar.add(bevel_box(W - 2.0, 0.4, 0.4, 0.1, (0, Hp - 1.6, D / 2 - 1.6)))
    k.mesh(m, "RibbonBar", "TrailShop_Bar", bar, fr, P.WOOD_DARK)
    cols = [(240, 60, 60), (250, 150, 40), (255, 220, 50), (70, 200, 80), (60, 150, 250), (170, 90, 230),
            (250, 120, 190)]
    for i, c in enumerate(cols):
        x = -W / 2 + 1.8 + i * (W - 3.6) / (len(cols) - 1)
        g = G.Geo()
        ln = 3.2 + 0.6 * (i % 3)
        g.add(bevel_box(0.9, ln, 0.2, 0.06, (x, Hp - 1.6 - ln / 2, D / 2 - 1.6)))
        g.add(bevel_box(0.9, 0.6, 0.2, 0.06, (x + 0.3, Hp - 1.6 - ln - 0.25, D / 2 - 1.6)).xf(
            T(x + 0.3, Hp - 1.9 - ln, D / 2 - 1.6) @ RZ(18) @ T(-x - 0.3, -(Hp - 1.9 - ln), -(D / 2 - 1.6))))
        rb = k.mesh(m, "Ribbon", "TrailShop_Ribbon%d" % (i + 1), g, fr, c)
        k.attr(rb, "Sway", 6.0)
    # spools of ribbon on the counter
    sp = G.Geo()
    for i, x in enumerate((-4.0, -1.5, 1.5, 4.0)):
        sp.add(ccyl(0.8, 0.8, 10, "z", (x, 4.5, -D / 2 + 1.6), 0.1))
    k.mesh(m, "Spools", "TrailShop_Spools", sp, fr, (250, 120, 190))


def sneaker_roof(k, m, fr, W, D, Hp):
    """A big sneaker sitting on the stall's roof."""
    base = fr * CF((0.0, Hp + 5.5, 1.8), G.ry(90))
    sole = G.Geo()
    sole.add(bevel_box(10.0, 1.0, 4.0, 0.3, (0, 0.5, 0)))
    sole.add(bevel_box(2.0, 1.0, 3.6, 0.3, (-5.4, 0.8, 0)))
    upper = G.Geo()
    upper.add(bevel_box(7.0, 2.6, 3.8, 0.5, (0.8, 2.3, 0)))
    upper.add(bevel_box(3.6, 2.4, 3.6, 0.5, (-3.6, 1.9, 0)).xf(T(-3.6, 1.0, 0) @ RZ(-12) @ T(3.6, -1.0, 0)))
    upper.add(bevel_box(3.0, 2.6, 3.4, 0.4, (2.6, 4.6, 0)))
    stripe = G.Geo()
    for sz in (-1, 1):
        stripe.add(bevel_box(4.0, 0.6, 0.2, 0.08, (0.2, 2.6, sz * 1.95)).xf(T(0.2, 2.6, sz * 1.95) @ RZ(25) @
                                                                           T(-0.2, -2.6, -sz * 1.95)))
    laces = G.Geo()
    for i in range(4):
        laces.add(bevel_box(0.4, 0.3, 3.0, 0.08, (-1.2 + i * 1.1, 3.75 + 0.25 * i, 0)))
    k.mesh(m, "SneakerSole", "SpeedShop_Sole", sole, base, P.WHITE)
    k.mesh(m, "Sneaker", "SpeedShop_Upper", upper, base, (230, 60, 50))
    k.mesh(m, "SneakerStripe", "SpeedShop_Stripe", stripe, base, P.WHITE)
    k.mesh(m, "SneakerLaces", "SpeedShop_Laces", laces, base, (255, 220, 60))
    # roof planks under it
    k.mesh(m, "Roof", "SpeedShop_Roof", bevel_box(W + 1.0, 0.6, 4.0, 0.12, (0, Hp + 4.9, 1.8)), fr, P.WOOD_DARK)


def index_board(k, parent):
    """A big green chalkboard on legs with a little roof, facing the avenue (west)."""
    m = k.sc.model(parent, "IndexBoard")
    x0, z0 = L.INDEX_BOARD
    fr = CF((x0, 0.0, z0), facing(-1.0, 0.0))
    W, H, y0 = 16.0, 10.0, 4.0
    legs = G.Geo()
    for sx in (-1, 1):
        legs.add(bevel_box(1.2, y0 + H + 2.0, 1.2, 0.2, (sx * (W / 2 + 0.4), (y0 + H + 2.0) / 2, 0.6)))
        legs.add(bevel_box(1.0, 0.8, 4.0, 0.15, (sx * (W / 2 + 0.4), 0.4, 0.6)))
    k.mesh(m, "Legs", "IndexBoard_Legs", legs, fr, P.WOOD)
    frame = G.Geo()
    t = 1.0
    for (fx, fy, fw, fh) in ((0, H + t / 2, W + 2 * t, t), (0, -t / 2, W + 2 * t, t), (W / 2 + t / 2, H / 2, t, H),
                             (-W / 2 - t / 2, H / 2, t, H)):
        frame.add(bevel_box(fw, fh, 1.0, 0.2, (fx, y0 + fy, 0)))
    frame.add(bevel_box(W, 0.5, 1.4, 0.12, (0, y0 - 0.2, -0.6)))          # chalk ledge
    k.mesh(m, "Frame", "IndexBoard_Frame", frame, fr, P.WOOD_LIGHT)
    roof = G.Geo()
    for sg in (-1, 1):
        roof.add(bevel_box(W + 4.0, 0.6, 3.0, 0.15, (0, 0, 0)).xf(T(0, y0 + H + 2.6, sg * 1.2 + 0.6) @ RX(sg * 22)))
    k.mesh(m, "Roof", "IndexBoard_Roof", roof, fr, (220, 70, 60))
    chalk = G.Geo()
    for i, x in enumerate((-5.0, -4.2, 3.0)):
        chalk.add(bevel_box(0.8, 0.3, 0.3, 0.06, (x, y0 + 0.2, -0.8)))
    k.mesh(m, "Chalk", "IndexBoard_Chalk", chalk, fr, P.WHITE)
    bd = k.board(m, W, H, fr * CF((0.0, y0 + H / 2, -0.2)), color=(40, 110, 70))
    k.prompt(m, fr * CF((0.0, 3.2, -4.0)))
    m.p["primary"] = bd
    return m


# ---------------------------------------------------------------- the big farm pieces

def barn(k, parent):
    """A barn front against the south wall in the south-west corner, facing north."""
    m = k.sc.model(parent, "Barn")
    x0, x1 = -118.0, -90.0
    z1 = L.YARD_Z[1]
    zf = z1 - 12.0
    xc, W = (x0 + x1) / 2, x1 - x0
    Hw = 20.0
    body = k.solid_box(m, "Body", (x0, 0.0, zf), (x1, Hw, z1), BARN_RED, studs=False)
    m.p["primary"] = body
    fr = CF((xc, 0.0, zf))
    # the gable: stacked bricks stepping in, and the roof edges
    gab = G.Geo()
    for i in range(6):
        w = W - i * 4.4
        gab.add(bevel_box(w, 2.0, 11.6, 0.15, (0, Hw + 1.0 + i * 2.0, 6.0)))
    k.mesh(m, "Gable", "Barn_Gable", gab, fr, BARN_RED, solid=False)
    roof = G.Geo()
    for sg in (-1, 1):
        ln = math.hypot(W / 2 + 1.5, 13.0)
        ang = math.degrees(math.atan2(13.0, W / 2 + 1.5))
        roof.add(bevel_box(ln, 1.2, 13.0, 0.25, (0, 0, 0)).xf(T(sg * (W / 4 + 0.75), Hw + 6.6, 6.0) @ RZ(-sg * ang)))
    k.mesh(m, "Roof", "Barn_Roof", roof, fr, ROOF)
    trim = G.Geo()
    dw, dh = 12.0, 14.0
    for (cx, cy, w, h) in ((0, dh + 0.5, dw + 2, 1.0), (-dw / 2 - 0.5, dh / 2, 1.0, dh), (dw / 2 + 0.5, dh / 2, 1.0, dh)):
        trim.add(bevel_box(w, h, 0.6, 0.12, (cx, cy, -0.3)))
    for sg in (-1, 1):                                 # the X on each door leaf
        for a in (-1, 1):
            ln = math.hypot(dw / 2, dh) - 1.2
            trim.add(bevel_box(ln, 0.8, 0.4, 0.1, (0, 0, 0)).xf(T(sg * dw / 4, dh / 2, -0.35) @
                                                               RZ(a * math.degrees(math.atan2(dh, dw / 2)))))
        trim.add(bevel_box(dw / 2 - 0.2, 0.8, 0.4, 0.1, (sg * dw / 4, 0.6, -0.35)))
    for sx in (-1, 1):                                 # corner boards
        trim.add(bevel_box(1.0, Hw, 0.6, 0.12, (sx * (W / 2 - 0.5), Hw / 2, -0.3)))
    trim.add(bevel_box(6.0, 5.0, 0.6, 0.12, (0, Hw + 4.0, -0.3)))   # hay-loft door frame
    k.mesh(m, "Trim", "Barn_Trim", trim, fr, TRIM)
    doors = G.Geo()
    doors.add(bevel_box(dw, dh, 0.4, 0.1, (0, dh / 2, -0.15)))
    k.mesh(m, "Doors", "Barn_Doors", doors, fr, darker(BARN_RED, 0.8))
    loft = G.Geo()
    loft.add(bevel_box(5.0, 4.0, 0.4, 0.1, (0, Hw + 4.0, -0.4)))
    k.mesh(m, "Loft", "Barn_Loft", loft, fr, (60, 36, 30))
    hay = G.Geo()
    for (hx, hy, hz) in ((-1.2, Hw + 2.6, -0.6), (1.0, Hw + 2.8, -0.8)):
        hay.add(bevel_box(2.2, 1.4, 1.6, 0.25, (hx, hy, hz)))
    k.mesh(m, "LoftHay", "Barn_LoftHay", hay, fr, P.HAY)
    return m


def windmill(k, parent):
    """A windmill in the south-east corner: a stepped white tower, a red cap, sails that turn
    (part Sails, attribute Spin, its own Y the axle, pointing north at the yard)."""
    m = k.sc.model(parent, "Windmill")
    xc, zc = 104.0, 220.0
    tower = G.Geo()
    for i in range(6):
        w = 14.0 - i * 1.4
        tower.add(bevel_box(w, 5.0, w, 0.25, (0, 2.5 + i * 5.0, 0)).xf(G.M(G.ry(45 * (i % 2)))))
    base = k.solid_box(m, "Base", (xc - 7.0, 0.0, zc - 7.0), (xc + 7.0, 5.0, zc + 7.0), (240, 236, 226), studs=False)
    m.p["primary"] = base
    k.mesh(m, "Tower", "Windmill_Tower", tower, CF((xc, 0.0, zc)), (244, 240, 230))
    cap = G.Geo()
    cap.add(bevel_box(9.0, 3.0, 9.0, 0.3, (0, 31.5, 0)))
    cap.add(bevel_box(6.0, 2.4, 6.0, 0.3, (0, 34.2, 0)))
    cap.add(bevel_box(3.0, 2.0, 3.0, 0.3, (0, 36.4, 0)))
    k.mesh(m, "Cap", "Windmill_Cap", cap, CF((xc, 0.0, zc)), (220, 60, 50))
    win = G.Geo()
    for i in (1, 3):
        win.add(bevel_box(2.0, 3.0, 0.4, 0.1, (0, 2.5 + i * 5.0, -(14.0 - i * 1.4) / 2 - 0.1)))
    win.add(bevel_box(4.0, 5.0, 0.4, 0.1, (0, 2.5, -7.1)))
    k.mesh(m, "Windows", "Windmill_Windows", win, CF((xc, 0.0, zc)), (80, 120, 180))
    # the sails: modelled about their own Y (the axle); the part's Y points north at the yard
    sails = G.Geo()
    sails.add(ccyl(1.2, 1.6, 10, "y", (0, 0, 0), 0.2))
    for i in range(4):
        a = i * 90 + 15
        arm = G.Geo()
        arm.add(bevel_box(0.8, 0.6, 16.0, 0.12, (0, 0.6, 8.6)))
        arm.add(bevel_box(3.6, 0.3, 11.0, 0.08, (1.4, 0.8, 10.8)))
        sails.add(arm.xf(G.M(G.ry(a))))
    sail_cf = CF((xc, 30.0, zc - 6.4), G.rx(-90))        # local Y -> world -Z (north)
    sp = k.mesh(m, "Sails", "Windmill_Sails", sails, sail_cf, (250, 246, 236))
    k.attr(sp, "Spin", 20.0)
    return m


def well(k, parent, b, pos):
    x, z = pos
    fr = CF((x, 0.0, z))
    ring = G.Geo()
    for i in range(8):
        a = i * 45
        ring.add(bevel_box(2.4, 2.8, 1.0, 0.2, (0, 1.4, 2.6)).xf(G.M(G.ry(a))))
    b.add("Well", P.STONE, ring, fr)
    k.solid(k.sc.folder(parent, "Well"), "WellBody", (6.0, 2.8, 6.0), CF((x, 1.4, z)), P.STONE_DARK, studs=False,
            transparency=1.0)
    wood = G.Geo()
    for sx in (-1, 1):
        wood.add(bevel_box(0.8, 7.0, 0.8, 0.15, (sx * 2.9, 3.5, 0)))
    wood.add(ccyl(0.4, 6.2, 8, "x", (0, 5.0, 0), 0.08))
    b.add("Well", P.WOOD, wood, fr)
    roof = G.Geo()
    for sg in (-1, 1):
        roof.add(bevel_box(8.0, 0.5, 4.2, 0.12, (0, 0, 0)).xf(T(0, 7.6, sg * 1.6) @ RX(sg * 28)))
    b.add("Well", (200, 70, 56), roof, fr)
    bucket = cfrustum(0.7, 0.9, 1.2, 8, "y", (0, 3.0, 0), 0.1)
    b.add("Well", P.WOOD_DARK, bucket, fr)
    b.add("Well", (70, 140, 230), ccyl(2.0, 0.3, 10, "y", (0, 2.2, 0), 0.05), fr)


def tractor(b, pos, ang):
    x, z = pos
    fr = CF((x, 0.0, z), G.ry(ang))
    red = (226, 50, 44)
    body = G.Geo()
    body.add(bevel_box(4.0, 3.0, 7.0, 0.4, (0, 3.2, -1.5)))
    body.add(bevel_box(5.0, 1.0, 9.0, 0.3, (0, 1.9, -0.6)))
    body.add(bevel_box(4.6, 4.4, 3.6, 0.4, (0, 5.2, 2.2)))
    b.add("Tractor", red, body, fr)
    glass = bevel_box(4.0, 2.6, 3.0, 0.2, (0, 6.2, 2.2))
    b.add("Tractor", (160, 220, 250), glass, fr)
    b.add("Tractor", (226, 50, 44), bevel_box(5.2, 0.6, 4.2, 0.2, (0, 7.8, 2.2)), fr)
    wheels, hubs = G.Geo(), G.Geo()
    for sx in (-1, 1):
        wheels.add(ccyl(2.6, 1.6, 12, "x", (sx * 3.2, 2.6, 2.4), 0.3))
        hubs.add(ccyl(1.2, 1.8, 10, "x", (sx * 3.2, 2.6, 2.4), 0.2))
        wheels.add(ccyl(1.5, 1.2, 10, "x", (sx * 2.6, 1.5, -4.0), 0.25))
        hubs.add(ccyl(0.7, 1.4, 8, "x", (sx * 2.6, 1.5, -4.0), 0.15))
    b.add("Tractor", P.BLACK, wheels, fr)
    b.add("Tractor", P.YELLOW, hubs, fr)
    b.add("Tractor", (90, 90, 96), ccyl(0.35, 3.0, 8, "y", (1.2, 6.0, -3.0), 0.08), fr)


def scarecrow(b, pos, ang):
    x, z = pos
    fr = CF((x, 0.0, z), G.ry(ang))
    wood = G.Geo()
    wood.add(bevel_box(0.8, 9.0, 0.8, 0.15, (0, 4.5, 0.4)))
    wood.add(bevel_box(8.0, 0.7, 0.7, 0.15, (0, 6.6, 0.4)))
    b.add("Scarecrow", P.WOOD, wood, fr)
    shirt = G.Geo()
    shirt.add(bevel_box(3.4, 3.6, 1.6, 0.3, (0, 5.4, 0)))
    for sx in (-1, 1):
        shirt.add(bevel_box(2.6, 1.3, 1.3, 0.25, (sx * 2.6, 6.6, 0)))
    b.add("Scarecrow", (90, 130, 220), shirt, fr)
    straw = G.Geo()
    for sx in (-1, 1):
        straw.add(bevel_box(0.8, 0.9, 0.9, 0.2, (sx * 4.1, 6.4, 0)))
    straw.add(bevel_box(2.6, 0.8, 1.4, 0.2, (0, 3.4, 0)))
    b.add("Scarecrow", P.HAY, straw, fr)
    pg, eg = P.potato_geo(2.6, 2.2, 2.4, eyes=False)
    b.add("Scarecrow", (214, 180, 120), pg, fr * CF((0, 8.6, 0), G.rz(90)) * CF((0, -1.2, 0)))
    face = G.Geo()
    for sx in (-1, 1):
        face.add(bevel_box(0.4, 0.4, 0.2, 0.08, (sx * 0.45, 8.7, -1.05)))
    face.add(bevel_box(1.2, 0.25, 0.2, 0.06, (0, 8.0, -1.05)))
    b.add("Scarecrow", P.BLACK, face, fr)
    hat = G.Geo()
    hat.add(ccyl(2.4, 0.3, 12, "y", (0, 9.8, 0), 0.08))
    hat.add(cfrustum(1.3, 1.0, 1.6, 10, "y", (0, 10.7, 0), 0.1))
    b.add("Scarecrow", (230, 180, 70), hat, fr)
    b.add("Scarecrow", (210, 50, 50), ccyl(1.33, 0.4, 10, "y", (0, 10.1, 0), 0.06), fr)


def lamp(k, parent, pos):
    """A lamp post: a Model with its glowing Bulb (Neon)."""
    x, z = pos
    m = k.sc.model(parent, "LampPost")
    parts = P.lamp_post(10.0)
    pole = k.mesh(m, "Post", "Yard_LampPost", parts[0][2], CF((x, 0.0, z)), parts[0][1])
    bulb = k.mesh(m, "Bulb", "Yard_LampBulb", parts[1][2], CF((x, 0.0, z)), parts[1][1], material="Neon")
    m.p["primary"] = pole
    return m
