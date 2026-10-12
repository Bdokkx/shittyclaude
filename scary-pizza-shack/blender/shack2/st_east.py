"""The east wall, north to south: the brick chimney breast and the Oven (the hero), the
PeelRack, the CutTable, the Bin on the floor, the BoxStation. Same Models, markers and
moving parts as batch 1.

The oven: brick in three close reds on a dark mortar core (each brick a part, 0.15 proud),
two arched mouths with brick voussoirs and riveted steel surrounds, soot licking up over each
mouth, drop-down doors with a frame and a porthole (the fire glows through it), the Glow
deep in each deck, a log store in the base, a steel hood with its lamp, and a steel flue up
through the ceiling and out of the roof. The breast beside it carries the thermometer, the
oven brush and the mitts; its brick chimney stands on the roof (the Smoke attachment)."""
import math

import numpy as np

import spsgeo as G
from spsgeo import CF

from . import counters as C, interior as IP, items2, layout as L
from .kit import bevel_box, ccyl, col, rod
from .st_common import E, FACE, N, S_, W, board, moving, pivot, spot, stand, station, weld_all

X0 = L.E_FRONT            # 13, the oven's front face
X1 = L.IN_X1              # 17, the east wall
OZ = (-6.0, 1.0)          # oven span (Z)
BZ = (-10.0, -6.0)        # breast span (Z)
MZ = (-5.0, 0.0)          # mouths (Z)
DECKS = ((2.2, 3.0, 3.4), (5.0, 5.8, 6.2))     # (floor, springing, crown) of each mouth (Slot1 2.2, Slot2 5.0)
LOGS = (0.6, 1.8)         # log store opening (Y)
TOP = 7.8                 # top of the brick body (the hood sits on it)
BRICK_P = 0.6             # course pitch (0.4 brick + 0.2 mortar)
REDS = ("brick1", "brick2", "brick3")


def _arch(span, rise):
    """Radius and centre height (below the crown) of a segmental arch."""
    r = (span * span / 4 + rise * rise) / (2 * rise)
    return r, r


def _mouth_outline(z0, z1, yf, ys, yc, n=10, grow=0.0):
    """Outline (Z, Y) of an arched mouth: rectangle from the floor to the springing, a
    segmental arch to the crown; `grow` pushes it outwards."""
    r, below = _arch(z1 - z0, yc - ys)
    zc, cy = (z0 + z1) / 2, yc - r
    a0 = math.asin(((z1 - z0) / 2) / r)
    pts = [(z0 - grow, yf - grow), (z1 + grow, yf - grow), (z1 + grow, ys)]
    for i in range(n + 1):
        a = a0 - 2 * a0 * i / n
        pts.append((zc + (r + grow) * math.sin(a), cy + (r + grow) * math.cos(a)))
    pts.append((z0 - grow, ys))
    return pts


def _in_poly(p, poly):
    x, y = p
    inside = False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            inside = not inside
    return inside


def _brick_face(k, m, u0, u1, y0, y1, holes, xface, rng, name="Bricks", soot=(), key="Oven"):
    """Bevelled bricks (0.9 x 0.4, 0.1 joints, every other course offset by half a brick, half
    bricks at the ends) on a face in the YZ plane at X = xface, facing -X, 0.15 proud of the
    mortar; nothing over `holes` (polygons in (Z, Y)). One mesh per brick colour."""
    geos = {c: G.Geo() for c in REDS + ("soot", "brick_sooty")}
    j = 0
    y = y0 + 0.05
    while y + 0.4 <= y1 + 1e-6:
        z = u0 + 0.05 - (0.5 if j % 2 else 0.0)
        while z < u1 - 0.05:
            a, b = max(z, u0 + 0.05), min(z + 0.9, u1 - 0.05)
            if b - a >= 0.35:
                corners = [(a, y), (b, y), (a, y + 0.4), (b, y + 0.4), ((a + b) / 2, y + 0.2)]
                if not any(any(_in_poly(c, h) for c in corners) for h in holes):
                    zc, yc = (a + b) / 2, y + 0.2
                    c = REDS[int(rng.integers(0, 3))]
                    if any(_in_poly((zc, yc), s_) for s_ in soot):
                        c = "soot" if rng.random() < 0.5 else "brick_sooty"
                    geos[c].add(bevel_box(0.25, 0.4, b - a, 0.05, c=(-0.025, yc, zc)))
            z += 1.0
        y += 0.5
        j += 1
    out = []
    for c, g in geos.items():
        if g.f:
            out.append(k.mesh(m, name, "%s__%s_%s" % (key, name, c), g, CF((xface - 0.1, 0, 0)), c, solid=True,
                              shadow=True))
    return out


def oven(k):
    m = station(k, "Oven")
    rng = np.random.default_rng(41)
    z0, z1 = OZ
    # ---- the mortar core, with the mouths and the log store cut out
    holes = [(MZ[0], MZ[1], 0.2, LOGS[1])] + [(MZ[0], MZ[1], yf - 0.4, yc) for (yf, ys, yc) in DECKS]
    import mk
    for ua, ub, ya, yb, c in mk.wall_pieces(z0, z1, [(0.2, TOP, "mortar")], holes):
        if yb - ya > 0.01:
            k.box(m, "Core", (X0, ya, ua), (X1, yb, ub), "mortar", solid=True)
    # the corners of each arched mouth's rectangle above the arch: brick fill
    for (yf, ys, yc) in DECKS:
        r, _ = _arch(MZ[1] - MZ[0], yc - ys)
        zc, cy = (MZ[0] + MZ[1]) / 2, yc - r
        a0 = math.asin(((MZ[1] - MZ[0]) / 2) / r)
        for sg in (-1, 1):
            outline = [(zc + sg * 2.5, ys), (zc + sg * 2.5, yc)] + \
                      [(zc + r * math.sin(sg * a0 * i / 8), cy + r * math.cos(sg * a0 * i / 8)) for i in range(0, 8)]
            g = G.extrude(outline, X1 - X0, "x", (0, 0, 0))
            k.mesh(m, "ArchFill", "Oven__ArchFill%d%s" % (int(yf * 10), "R" if sg > 0 else "L"), g,
                   CF(((X0 + X1) / 2, 0, 0)), "soot", solid=True)
    # ---- the deck insides: a firebrick hearth, sooty walls, the Glow at the back
    glows = []
    for i, (yf, ys, yc) in enumerate(DECKS):
        k.box(m, "Hearth", (X0, yf - 0.4, MZ[0]), (X1, yf, MZ[1]), "hearth", solid=True)
        k.mesh(m, "DeckLining", "Oven__Lining%d" % i, _lining(yf, ys, yc), CF(((X0 + X1) / 2, 0, 0)), "soot", solid=True)
        g = k.part(m, "Glow", (1.0, 0.4, 4.0), CF((X1 - 0.5, yf + 0.2, (MZ[0] + MZ[1]) / 2)), "fire",
                   material="Neon", shadow=False)
        glows.append(g)
        embers = G.Geo()
        for j in range(7):
            embers.add(G.blob(0.28, 6, 4, (1.3, 0.6, 1.0), 0.2, 300 + 7 * i + j,
                              (0, 0.05, -2.0 + 0.66 * j), flat_bottom=0.0))
        k.mesh(m, "Embers", "Oven__Embers%d" % i, embers, CF((X1 - 1.1, yf, (MZ[0] + MZ[1]) / 2)), "ember", shadow=False)
        spot(k, m, "Slot%d" % (i + 1), X0 + 0.4 + 1.8, yf, (MZ[0] + MZ[1]) / 2, E)
    # ---- brick faces: the oven's front and south side, the breast's front
    margin = 0.15
    oven_holes = [_ring_outline(yf, ys, yc) for (yf, ys, yc) in DECKS]
    oven_holes.append([(MZ[0] - margin, LOGS[0] - margin), (MZ[1] + margin, LOGS[0] - margin),
                       (MZ[1] + margin, LOGS[1] + margin), (MZ[0] - margin, LOGS[1] + margin)])
    # the topping rail's counter covers the oven's north end below the worktop
    oven_holes.append([(z0 - 1, 0.0), (IP.N_FRONT + 0.1, 0.0), (IP.N_FRONT + 0.1, L.WORK + 0.05),
                       (z0 - 1, L.WORK + 0.05)])
    soot = [[(MZ[0] + 0.6, yc), (MZ[1] - 0.6, yc), (MZ[1] - 1.4, yc + 1.4), ((MZ[0] + MZ[1]) / 2, yc + 1.9),
             (MZ[0] + 1.2, yc + 1.2)] for (yf, ys, yc) in DECKS]
    _brick_face(k, m, z0, z1, 0.2, TOP, oven_holes, X0, rng, soot=soot, key="Oven")
    # the breast: brick from the worktop up (the counter covers it below), to the ceiling
    breast = k.box(m, "Breast", (X0, 0.2, BZ[0]), (X1, L.CEIL, BZ[1]), "mortar", solid=True)
    _brick_face(k, m, BZ[0] + 0.25, BZ[1], L.WORK - 0.05, L.CEIL - 0.25, [], X0, rng, name="BreastBricks",
                key="Breast")
    # ---- arches (voussoirs) and riveted steel surrounds round each mouth
    for (yf, ys, yc) in DECKS:
        k.mesh(m, "Arch", "Oven__Arch%d" % int(yf * 10), _voussoirs(yf, ys, yc), CF((X0, 0, 0)), "brick3",
               solid=True)
        k.mesh(m, "Surround", "Oven__Surround%d" % int(yf * 10), _surround(yf, ys, yc), CF((X0, 0, 0)), "iron",
               solid=True)
        k.mesh(m, "Rivets", "Oven__Rivets%d" % int(yf * 10), _rivets(yf, ys, yc), CF((X0, 0, 0)), "steel_dark",
               shadow=False)
    # ---- the doors: drop-down, hinged on the bottom edge; a frame, a porthole, the handle
    for i, (yf, ys, yc) in enumerate(DECKS):
        door = k.mesh(m, "Door%d" % (i + 1), "Oven__Door%d" % (i + 1), _door(yf, ys, yc), CF((X0, 0, 0)), "iron",
                      solid=True)
        zc = (MZ[0] + MZ[1]) / 2
        py = yf + 0.45
        port = k.part(m, "Porthole", (0.15, 0.8, 0.8), CF((X0 + 0.02, py, zc)), "glass_hot", material="Glass",
                      transparency=0.35, shape="Cylinder", grid=False, shadow=False)
        rim = k.mesh(m, "PortRim", "Oven__PortRim", G.torus(0.43, 0.09, 12, 4, "x", (0, 0, 0)),
                     CF((X0 - 0.04, py, zc)), "steel_light", shadow=False)
        hg = G.Geo()
        hg.add(rod((0, 0, -1.4), (0, 0, 1.4), 0.11, 8))
        for dz in (-1.25, 1.25):
            hg.add(rod((0, 0, dz), (0.42, 0, dz), 0.09, 6))
        hdl = k.mesh(m, "DoorHandle", "Oven__DoorHandle", hg, CF((X0 - 0.45, ys + 0.1, zc)), "steel_light",
                     solid=True)
        weld_all(k, door, [port, rim, hdl])
        pivot(door, CF((X0 + 0.4, yf, zc)))
        moving(m, "Door%d" % (i + 1), "drop-down door hinged on its bottom edge; rotate the pivot +90 deg about Z "
                                      "and it falls open towards the room, ending flush with the deck floor")
    # ---- the log store in the base
    k.mesh(m, "Logs", "Oven__Logs", _logs(rng), CF((X0 + 0.15, LOGS[0], (MZ[0] + MZ[1]) / 2)), "wood", solid=True)
    k.mesh(m, "LogEnds", "Oven__LogEnds", _log_ends(rng), CF((X0 + 0.15, LOGS[0], (MZ[0] + MZ[1]) / 2)),
           "wood_pale", shadow=False)
    k.box(m, "StoreFloor", (X0, 0.2, MZ[0]), (X1, LOGS[0], MZ[1]), "soot", solid=True)
    # (the lower deck's hearth is the log store's roof)
    # ---- the hood: a steel canopy over the mouths with its lamp, sitting on the brick top
    hood(k, m)
    # ---- the breast's dressing: thermometer, brush on its hook, mitts on hooks
    bf = X0 - 0.15
    k.prop(m, "OvenDial", CF((bf, 7.3, -7.6), G.ry(-90)), name="Thermometer")
    k.prop(m, "OvenBrush", CF((bf, 6.6, -6.55), G.ry(-90)), name="OvenBrush")
    for dz, seed in ((-8.9, 1), (-9.55, 2)):
        k.prop(m, "OvenMitt", CF((bf, 7.4, dz), G.ry(-90)), name="OvenMitt", seed=seed)
    k.prop(m, "AshBucket", CF((12.35, L.FLOOR, -0.5)), name="AshBucket")     # between the stands' clear boxes
    # ---- the old brick chimney on the roof (batch 1's Smoke attachment) and the steel flue
    ch = k.box(m, "Chimney", (X0 + 0.5, L.ROOF_TOP - 0.4, BZ[0] + 0.5), (X1 - 0.5, 18.6, BZ[1] - 0.5), "brick2",
               studs=False, solid=True)
    k.box(m, "ChimneyCap", (X0, 18.6, BZ[0]), (X1, 19.0, BZ[1]), "brick_sooty", solid=True)
    k.box(m, "ChimneyPot", (X0 + 1, 19.0, BZ[0] + 1), (X1 - 1, 20.2, BZ[1] - 1), "soot", solid=True)
    k.sc.attachment(ch, "Smoke", CF(((X0 + X1) / 2, 20.2, (BZ[0] + BZ[1]) / 2)))
    k.sc.attachment(ch, "Fx_Smoke", CF(((X0 + X1) / 2, 20.2, (BZ[0] + BZ[1]) / 2)))
    flue(k, m)
    stand(k, m, X0 - IP.STAND_GAP - 0.6, (MZ[0] + MZ[1]) / 2, E)
    return m


def _ring_outline(yf, ys, yc, side=0.38, ring=0.86):
    """What a mouth takes up on the face: the surround at the sides and sill, the voussoir ring
    over the arch."""
    r, _ = _arch(MZ[1] - MZ[0], yc - ys)
    zc, cy = (MZ[0] + MZ[1]) / 2, yc - r
    a0 = math.asin(2.5 / r) + 0.1
    pts = [(MZ[0] - side, yf - side), (MZ[1] + side, yf - side), (MZ[1] + side, ys - 0.2)]
    for i in range(13):
        a = a0 - 2 * a0 * i / 12
        pts.append((zc + (r + ring) * math.sin(a), cy + (r + ring) * math.cos(a)))
    pts.append((MZ[0] - side, ys - 0.2))
    return pts


def _lining(yf, ys, yc):
    """The deck's sooty inside: two side walls, the back, and the arched roof."""
    g = G.Geo()
    zc = (MZ[0] + MZ[1]) / 2
    d = X1 - X0 - 0.4
    g.add(bevel_box(d, yc - yf, 0.3, 0.03, c=(0.2, (yf + yc) / 2, MZ[0] + 0.15)))
    g.add(bevel_box(d, yc - yf, 0.3, 0.03, c=(0.2, (yf + yc) / 2, MZ[1] - 0.15)))
    g.add(bevel_box(0.3, yc - yf, MZ[1] - MZ[0], 0.03, c=((X1 - X0) / 2 - 0.15, (yf + yc) / 2, zc)))
    # roof: the arch, extruded along X, as a band 0.3 thick under the core
    r, _ = _arch(MZ[1] - MZ[0], yc - ys)
    cy = yc - r
    a0 = math.asin(2.5 / r)
    inner, outer = [], []
    for i in range(9):
        a = -a0 + 2 * a0 * i / 8
        inner.append((zc + (r - 0.3) * math.sin(a), cy + (r - 0.3) * math.cos(a)))
        outer.append((zc + r * math.sin(a), cy + r * math.cos(a)))
    poly = outer + inner[::-1]
    g.add(G.extrude(poly, d, "x", (0.2, 0, 0)))
    return g


def _voussoirs(yf, ys, yc):
    """The brick ring over a mouth: wedge-shaped bricks with mortar gaps, proud 0.25."""
    r, _ = _arch(MZ[1] - MZ[0], yc - ys)
    zc, cy = (MZ[0] + MZ[1]) / 2, yc - r
    a0 = math.asin(2.5 / r) + 0.08
    n = 9
    g = G.Geo()
    for i in range(n):
        a = -a0 + 2 * a0 * (i + 0.06) / n
        b = -a0 + 2 * a0 * (i + 0.94) / n
        r0, r1 = r + 0.32, r + 0.8
        poly = [(zc + r0 * math.sin(a), cy + r0 * math.cos(a)), (zc + r1 * math.sin(a), cy + r1 * math.cos(a)),
                (zc + r1 * math.sin(b), cy + r1 * math.cos(b)), (zc + r0 * math.sin(b), cy + r0 * math.cos(b))]
        g.add(G.extrude(poly, 0.5, "x", (0.0, 0, 0)))
    return g


def _surround(yf, ys, yc):
    """Steel surround: a band 0.36 wide round the mouth (sides, sill, arch), proud 0.3."""
    r, _ = _arch(MZ[1] - MZ[0], yc - ys)
    zc, cy = (MZ[0] + MZ[1]) / 2, yc - r
    a0 = math.asin(2.5 / r)
    g = G.Geo()
    w = 0.3
    g.add(bevel_box(0.3, ys - yf + w, w, 0.05, c=(-0.1, (yf - w + ys) / 2, MZ[0] - w / 2)))
    g.add(bevel_box(0.3, ys - yf + w, w, 0.05, c=(-0.1, (yf - w + ys) / 2, MZ[1] + w / 2)))
    g.add(bevel_box(0.3, w, MZ[1] - MZ[0] + 2 * w, 0.05, c=(-0.1, yf - w / 2, zc)))
    inner, outer = [], []
    for i in range(11):
        a = -a0 + 2 * a0 * i / 10
        inner.append((zc + r * math.sin(a), cy + r * math.cos(a)))
        outer.append((zc + (r + w) * math.sin(a), cy + (r + w) * math.cos(a)))
    g.add(G.extrude(outer + inner[::-1], 0.3, "x", (-0.1, 0, 0)))
    return g


def _rivets(yf, ys, yc):
    r, _ = _arch(MZ[1] - MZ[0], yc - ys)
    zc, cy = (MZ[0] + MZ[1]) / 2, yc - r
    a0 = math.asin(2.5 / r)
    g = G.Geo()
    pts = []
    for y in np.arange(yf - 0.15, ys, 0.6):
        pts += [(MZ[0] - 0.15, y), (MZ[1] + 0.15, y)]
    for z in np.arange(MZ[0] + 0.3, MZ[1], 0.75):
        pts.append((z, yf - 0.15))
    for i in range(7):
        a = -a0 + 2 * a0 * i / 6
        pts.append((zc + (r + 0.15) * math.sin(a), cy + (r + 0.15) * math.cos(a)))
    for (z, y) in pts:
        g.add(G.sphere(0.1, 6, 3, c=(-0.27, y, z)))
    return g


def _door(yf, ys, yc):
    """A door filling the mouth (inset 0.06), 0.4 thick with a raised frame on its face."""
    outline = _mouth_outline(MZ[0] + 0.06, MZ[1] - 0.06, yf, ys, yc - 0.06, n=10)
    g = G.extrude(outline, 0.4, "x", (0.2, 0, 0))
    # the raised frame, as segments (left, right, bottom, arch band)
    g.add(G.extrude([(MZ[0] + 0.12, yf + 0.06), (MZ[0] + 0.4, yf + 0.06), (MZ[0] + 0.4, ys),
                     (MZ[0] + 0.12, ys)], 0.15, "x", (-0.075, 0, 0)))
    g.add(G.extrude([(MZ[1] - 0.4, yf + 0.06), (MZ[1] - 0.12, yf + 0.06), (MZ[1] - 0.12, ys),
                     (MZ[1] - 0.4, ys)], 0.15, "x", (-0.075, 0, 0)))
    g.add(G.extrude([(MZ[0] + 0.12, yf + 0.06), (MZ[1] - 0.12, yf + 0.06), (MZ[1] - 0.12, yf + 0.34),
                     (MZ[0] + 0.12, yf + 0.34)], 0.15, "x", (-0.075, 0, 0)))
    r, _ = _arch(MZ[1] - MZ[0] - 0.24, (yc - 0.12) - ys)
    zc, cy = (MZ[0] + MZ[1]) / 2, (yc - 0.12) - r
    a0 = math.asin(((MZ[1] - MZ[0] - 0.24) / 2) / r)
    inner_a, outer_a = [], []
    for i in range(11):
        a = -a0 + 2 * a0 * i / 10
        outer_a.append((zc + r * math.sin(a), cy + r * math.cos(a)))
        inner_a.append((zc + (r - 0.28) * math.sin(a), cy + (r - 0.28) * math.cos(a)))
    g.add(G.extrude(outer_a + inner_a[::-1], 0.15, "x", (-0.075, 0, 0)))
    # a little draught slider under the porthole
    g.add(bevel_box(0.15, 0.25, 1.0, 0.04, c=(-0.075, yf + 0.6, zc - 1.0)))
    return g


def _logs(rng):
    """Split logs stacked in the base, ends out: two rows of hexagonal billets."""
    g = G.Geo()
    for row, y in enumerate((0.28, 0.82)):
        for i in range(8):
            z = -2.2 + 0.62 * i + (0.31 if row else 0.0)
            if z > 2.25:
                continue
            ln = 2.2 + rng.uniform(-0.2, 0.2)
            g.add(ccyl(0.3, ln, 6, "x", (ln / 2 + 0.15, y, z), 0.04))
    return g


def _log_ends(rng):
    g = G.Geo()
    for row, y in enumerate((0.28, 0.82)):
        for i in range(8):
            z = -2.2 + 0.62 * i + (0.31 if row else 0.0)
            if z > 2.25:
                continue
            g.add(ccyl(0.22, 0.15, 6, "x", (0.06, y, z), 0.02))
    return g


def hood(k, m):
    """Steel canopy over the mouths: sloped front, a filter band, side cheeks, its lamp."""
    hz0, hz1 = OZ[0], OZ[1]
    zc = (hz0 + hz1) / 2
    y0, y1 = TOP, TOP + 0.8
    g = G.Geo()
    g.add(bevel_box(X1 - X0, 0.8, hz1 - hz0, 0.06, c=((X0 + X1) / 2 - X0, (y0 + y1) / 2, 0)))
    front = G.extrude([(0.0, y0), (1.0, y0), (1.0, y1), (0.6, y1)], hz1 - hz0, "z", (0, 0, 0))
    g.add(front.xf(G.M(np.eye(3), (-1.0, 0, 0))))
    lip = bevel_box(0.3, 0.3, hz1 - hz0 + 0.1, 0.06, c=(-0.85, y0 + 0.15, 0))
    g.add(lip)
    k.mesh(m, "Hood", "Oven__Hood", g, CF((X0, 0, zc)), "steel", solid=True)
    filt = G.Geo()
    for i in range(9):
        filt.add(bevel_box(0.15, 0.15, hz1 - hz0 - 0.6, 0.03, c=(-0.75 + 0.08 * i, y0 + 0.02, 0)))
    k.mesh(m, "Filter", "Oven__Filter", filt, CF((X0, 0, zc)), "steel_dark", shadow=False)
    # the oven lamp in the hood's underside, warm, pointing down at the mouths
    lm = k.sc.model(m, "OvenLamp")
    bulb = k.part(lm, "Bulb", (0.5, 0.3, 0.5), CF((X0 - 0.45, y0 - 0.12, zc)), (255, 222, 170), material="Neon",
                  grid=False, shadow=False)
    k.mesh(lm, "Guard", "Oven__LampGuard", G.torus(0.33, 0.075, 10, 4, "y", (0, 0, 0)),
           CF((X0 - 0.45, y0 - 0.12, zc)), "steel_dark", shadow=False)
    k.lamp(lm, bulb, "Shack", "Spot", 12.0, 1.0, (255, 196, 132), angle=110.0)


def flue(k, m):
    """The steel flue: out of the hood's top, through the ceiling (a collar hides the cut),
    through the attic and the roof (a flashing collar), up to a coned rain cap."""
    fx, fz = X0 + 2.2, (OZ[0] + OZ[1]) / 2 + 0.2
    y0 = TOP + 0.8
    top = L.ROOF_TOP + 4.6
    g = ccyl(0.6, top - y0, 12, "y", (0, (top - y0) / 2, 0), 0.05)
    for y in np.arange(1.2, top - y0, 1.6):                 # seams
        g.add(G.torus(0.62, 0.075, 12, 4, "y", (0, y, 0)))
    f = k.mesh(m, "Flue", "Oven__Flue", g, CF((fx, y0, fz)), "steel_dark", solid=True)
    k.mesh(m, "FlueCollar", "Oven__FlueCollar", ccyl(0.95, 0.15, 12, "y", (0, 0, 0), 0.04),
           CF((fx, L.CEIL - 0.075, fz)), "steel", shadow=False)
    k.mesh(m, "FlueFlashing", "Oven__FlueFlash", G.outward(G.lathe([(0, 0), (1.2, 0), (1.0, 0.3), (0.7, 0.6),
                                                                    (0, 0.6)], 12)),
           CF((fx, L.ROOF_TOP, fz)), "charcoal", shadow=False)
    cap = G.Geo()
    cap.add(G.outward(G.lathe([(0, 0), (1.1, 0), (1.1, 0.15), (0, 0.9)], 12)))
    for a in range(3):
        t = a * math.tau / 3
        cap.add(rod((0.55 * math.cos(t), -0.6, 0.55 * math.sin(t)), (0.75 * math.cos(t), 0.05, 0.75 * math.sin(t)),
                    0.08, 4))
    capm = k.mesh(m, "FlueCap", "Oven__FlueCap", cap, CF((fx, top + 0.6, fz)), "steel_dark", solid=True)
    k.sc.attachment(f, "Fx_Smoke", CF((fx, top + 0.3, fz)))


# ---------------------------------------------------------------- peel rack

def peel_rack(k):
    """Peels standing on their poles between the oven and the cut table, heads down, held by a
    wooden rack on the wall and a steel cup rail on the floor: the PizzaPeel item and an old
    one with a wide head, burnt along its edge."""
    m = station(k, "PeelRack")
    z0, z1 = 1.0, 2.0
    zc = (z0 + z1) / 2
    xb = X1
    # peels stand head-down on a rubber-lined floor rail; a wall arm holds their poles
    xp = X1 - 1.95                                        # the peels' centre line (heads 3.5 wide)
    k.mesh(m, "Backboard", "PeelRack__Board", bevel_box(0.3, 1.2, 1.0, 0.05), CF((X1 - 0.15, 5.0, zc)), "wood_dark",
           solid=True)
    arm = G.Geo()
    for dz in (-0.42, 0.42):
        arm.add(bevel_box(2.1, 0.3, 0.16, 0.05, c=(-1.05, 0, dz)))
    for dx in (-0.3, -1.95):
        arm.add(bevel_box(0.2, 0.3, 1.0, 0.05, c=(dx, 0, 0)))
    k.mesh(m, "Arm", "PeelRack__Arm", arm, CF((X1 - 0.3, 5.0, zc)), "wood", solid=True)
    rail = G.Geo()
    rail.add(bevel_box(3.5, 0.3, 1.0, 0.05, c=(-0.15, 0.15, 0)))
    for dz in (-0.45, 0.45):
        rail.add(bevel_box(3.5, 0.3, 0.15, 0.04, c=(-0.15, 0.45, dz)))
    k.mesh(m, "FloorRail", "PeelRack__Rail", rail, CF((xp, L.FLOOR, zc)), "steel_dark", solid=True)
    R_down = np.column_stack(((-1, 0, 0), (0, 0, 1), (0, 1, 0)))     # head down, pole up, flat to the oven
    peel = items2.get("PizzaPeel")
    lo, hi = peel.bbox()
    # the two poles side by side in the arm's opening (Z 1.16..1.84)
    items2.place(k, m, "PizzaPeel", CF((xp, L.FLOOR + 0.3 - lo[2], z0 + 0.35), R_down))
    k.prop(m, "OldPeel", CF((xp, L.FLOOR + 0.3, z1 - 0.3)), name="OldPeel")
    stand(k, m, X0 - IP.STAND_GAP, zc, E)
    return m


# ---------------------------------------------------------------- cut table

def cut_table(k):
    """Counter with a butcher-block top, the round cutting board, the slice guide hung on the
    wall, the PizzaCutter item on its hook on a tool rail."""
    m = station(k, "CutTable")
    z0, z1 = 2.0, 6.0
    zc = (z0 + z1) / 2
    C.counter(k, m, "E", z0, z1, 4.0, top="wood", fronts=[(2, "drawers"), (2, "door")], end_left=True,
              end_right=False, owner="CutTable")
    k.prop(m, "RoundBoard", CF((15.0, L.WORK, zc), G.ry(90)), name="Board")
    spot(k, m, "Work", 15.0, L.WORK + 0.4, zc, E)
    k.prop(m, "ToolRail", C.wcf("E", zc, 7.1, 0.0), name="ToolRail")
    R = np.column_stack(((1, 0, 0), (0, 0, -1), (0, 1, 0)))     # hanging wheel-down, flat to the wall
    items2.place(k, m, "PizzaCutter", CF((X1 - 0.4, 7.1 - 0.9, zc + 0.9), R))     # grip in the hook
    k.prop(m, "SliceGuide", C.wcf("E", zc - 0.8, 5.2, 0.0), name="SliceGuide")
    stand(k, m, X0 - IP.STAND_GAP, zc, E)
    return m


# ---------------------------------------------------------------- bin

def kitchen_bin(k):
    """Pedal bin on the floor against the counters between the cut table and the box
    station; its Lid is hinged at the back."""
    m = station(k, "Bin")
    c = (X0 - 0.95, L.FLOOR, 6.0)
    body = G.outward(G.lathe([(0, 0.0), (0.62, 0.0), (0.7, 0.1), (0.76, 2.1), (0, 2.1)], 12))
    k.mesh(m, "Body", "Bin__Body", body, CF(c), "steel_dark", solid=True)
    k.mesh(m, "Band", "Bin__Band", G.ring(0.8, 0.7, 0.3, 12, c=(0, 1.95, 0)), CF(c), "red", shadow=False)
    k.mesh(m, "Foot", "Bin__Foot", G.ring(0.7, 0.5, 0.15, 12, c=(0, 0.075, 0)), CF(c), "black", shadow=False)
    lid = G.outward(G.lathe([(0, 0.0), (0.82, 0.0), (0.82, 0.15), (0.6, 0.35), (0, 0.42)], 12))
    lid.add(bevel_box(0.3, 0.15, 0.4, 0.04, c=(0.82, 0.1, 0)))
    lidp = k.mesh(m, "Lid", "Bin__Lid", lid, CF((c[0], c[1] + 2.1, c[2])), "steel", solid=True)
    pivot(lidp, CF((c[0] + 0.8, c[1] + 2.1, c[2])))
    moving(m, "Lid", "hinged at the back (counter side); rotate the pivot -90 deg about Z to flip it up")
    ped = G.Geo()
    ped.add(bevel_box(0.5, 0.15, 0.7, 0.04, c=(-0.95, 0.2, 0)))
    ped.add(rod((-0.7, 0.2, 0), (-0.55, 0.35, 0), 0.08, 4))
    k.mesh(m, "Pedal", "Bin__Pedal", ped, CF(c), "black", shadow=False)
    k.prop(m, "LitterFloor", CF((c[0] - 1.3, L.FLOOR, c[2] + 0.5)), name="Litter")
    st = np.array((c[0] - 1.2, L.FLOOR, c[2] - 1.5))
    d = np.array((c[0], L.FLOOR, c[2])) - st
    k.sc.marker(m, "Stand", CF(st, G.facing(d / np.linalg.norm(d))))
    return m


# ---------------------------------------------------------------- box station

def box_station(k):
    """Counter with its open bay stacked to the top with flat boxes, a folded box with the
    PAPA STUD'S print on top of the pile, and the roll of stickers on the worktop."""
    m = station(k, "BoxStation")
    z0, z1 = 6.0, 10.0
    zc = (z0 + z1) / 2
    C.counter(k, m, "E", z0, z1, 4.0, top="wood_light", fronts=[(4, "open")], end_left=False, end_right=False,
              owner="BoxStation", open_sides=False)
    k.prop(m, "FlatBoxStack", CF((14.85, 0.9, zc)), name="FlatBoxes", seed=5)     # 7 flat + 1 folded: 0.9 .. 2.9
    board(k, m, (3.0, 0.45, 0.15), CF((13.05 - 0.08, 0.9 + 7 * 0.17 + 0.35, zc), FACE["E"]), "cardboard",
          text="PAPA STUD'S PIZZA", text_color=(170, 32, 26), name="BoxPrint")
    zw = zc - 0.6                       # the work spot clear of the rules board in the corner
    spot(k, m, "Work", 15.0, L.WORK, zw, E)
    k.prop(m, "StickerRoll", CF((16.1, L.WORK, z1 - 1.6)), name="StickerRoll")
    stand(k, m, X0 - IP.STAND_GAP, zw, E)
    return m


def build(k):
    return [oven(k), peel_rack(k), cut_table(k), kitchen_bin(k), box_station(k)]
