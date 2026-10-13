"""Pass 4: the dressing that tells the story, on the walls and the floor.

The inspection certificate with its grade scratched out, the DAYS SINCE LAST INSPECTION
sign with no number on its hooks, the employee-of-the-month frame with nobody in it, a
clock whose second hand runs backwards, two tired posters, a wet floor sign by the back
door, fly strips, the conduit dropping from the runs under the ceiling to the sockets on
the backsplash (the pipe runs that break up the paint), and the wear on the paint: patches
that were painted over in a slightly different green, clean ghosts where signs once hung,
grime round the door and the stove (always a darker shade of the colour it is on).

Everything here is decoration (no collision, no queries) and keeps out of the clear boxes
in front of the stations' markers."""
import math

import numpy as np

import spsgeo as G
from spsgeo import CF

from . import counters as C, interior as IP, layout as L
from .kit import bevel_box, ccyl, chamfer_slab, rod
from .st_common import board

# ---------------------------------------------------------------- helpers


def wf(w, u, y, d=0.0):
    """Wall frame: +X to the right of someone facing the wall, +Y up, +Z into the room."""
    return C.wcf(w, u, y, d)


def text(k, parent, frame, dx, dy, z, size, color, **kw):
    """A Board on a surface of a wall frame at depth z, its Front towards the room."""
    return board(k, parent, (size[0], size[1], 0.15), frame * CF((dx, dy, z + 0.075), G.ry(180)), color, **kw)


def frame_geo(w, h, bar=0.2, depth=0.2, b=0.05):
    """A picture frame (four bevelled bars), back at z = 0."""
    g = G.Geo()
    for (cx, cy, sx, sy) in ((0, h / 2 - bar / 2, w, bar), (0, -h / 2 + bar / 2, w, bar),
                             (-w / 2 + bar / 2, 0, bar, h - 2 * bar), (w / 2 - bar / 2, 0, bar, h - 2 * bar)):
        g.add(bevel_box(sx, sy, depth, b, c=(cx, cy, depth / 2)))
    return g


def tape_geo(pts):
    """Little strips of tape at the given (x, y) corners, turned 45 degrees."""
    g = G.Geo()
    for (x, y) in pts:
        a = 45 if x * y > 0 else -45
        g.add(bevel_box(0.4, 0.15, 0.05, 0.015).xf(G.M(G.rz(a))).xf(G.T(x, y, 0.025)))
    return g


# ---------------------------------------------------------------- the story pieces


def days_since(k, f):
    """Over the topping rail: DAYS SINCE LAST INSPECTION, and two empty hooks where the
    number card should hang."""
    m = k.sc.model(f, "DaysSinceSign")
    fr = wf("N", 9.9, 7.6)
    k.mesh(m, "Panel", "Dress__DaysPanel", bevel_box(4.4, 1.7, 0.2, 0.06, c=(0, 0, 0.1)), fr, "cream", shadow=False)
    k.mesh(m, "Frame", "Dress__DaysFrame", frame_geo(4.6, 1.9, 0.15, 0.3), fr, "red", shadow=False)
    text(k, m, fr, 0.0, 0.38, 0.2, (4.0, 0.8), "cream", text="DAYS SINCE LAST\nINSPECTION",
         text_color=(170, 32, 26), name="Heading")
    k.mesh(m, "NumberSlot", "Dress__DaysSlot", bevel_box(1.6, 0.7, 0.15, 0.03, c=(0, 0, 0.075)),
           fr * CF((0.0, -0.45, 0.2)), "charcoal", shadow=False)
    hooks = G.Geo()
    for dx in (-0.4, 0.4):
        hooks.add(G.tube([(dx, 0.15, 0.0), (dx, 0.15, 0.2), (dx, 0.3, 0.28)], 0.075, 5))
    k.mesh(m, "Hooks", "Dress__DaysHooks", hooks, fr * CF((0.0, -0.5, 0.35)), "steel_dark", shadow=False)
    # the number card in the slot: a Board for the number alone (the game writes it)
    text(k, m, fr * CF((0.0, -0.64, 0.2)), 0.0, 0.0, 0.2, (1.4, 0.5), "paper", text="0", text_color=(30, 30, 30),
         name="Number")
    k.mark_used("DaysSinceSign")


def inspection_certificate(k, f):
    """Framed over the shutter button: the health inspection certificate, its grade stamp
    scratched out with a key."""
    m = k.sc.model(f, "InspectionCertificate")
    fr = wf("S", -6.1, 7.95)
    k.mesh(m, "Frame", "Dress__CertFrame", frame_geo(1.8, 1.2, 0.16, 0.22), fr, "black", shadow=False)
    k.mesh(m, "Backing", "Dress__CertBacking", bevel_box(1.5, 0.95, 0.1, 0.02, c=(0, 0, 0.05)), fr, "paper_old",
           shadow=False)
    text(k, m, fr, 0.0, 0.14, 0.1, (1.3, 0.6), "paper_old", text="HEALTH DEPT.\nFOOD SAFETY\nINSPECTION",
         text_color=(40, 40, 40), name="Heading")
    text(k, m, fr, -0.3, -0.3, 0.1, (0.6, 0.25), "paper_old", text="GRADE", text_color=(40, 40, 40), name="Grade")
    k.mesh(m, "Stamp", "Dress__CertStamp", G.torus(0.18, 0.075, 10, 4, "z", (0, 0, 0.0)), fr * CF((0.3, -0.28, 0.17)),
           "red_dark", shadow=False)
    sc_ = G.Geo()
    for a, dy in ((25, 0.06), (-20, -0.02), (35, -0.1), (-30, 0.12)):
        sc_.add(bevel_box(0.62, 0.15, 0.05, 0.015).xf(G.M(G.rz(a))).xf(G.T(0.0, dy, 0.0)))
    k.mesh(m, "Scratches", "Dress__CertScratches", sc_, fr * CF((0.3, -0.28, 0.27)), "charcoal", shadow=False)
    k.mark_used("InspectionCertificate")


def employee_frame(k, f):
    """On the south wall over the open corner: EMPLOYEE OF THE MONTH, the photo gone, its
    clean ghost and four bits of tape left on the backing."""
    m = k.sc.model(f, "EmployeeOfTheMonth")
    fr = wf("S", 15.4, 7.4)
    k.mesh(m, "Frame", "Dress__EmpFrame", frame_geo(1.7, 2.1, 0.22, 0.22), fr, "wood_dark", shadow=False)
    k.mesh(m, "Backing", "Dress__EmpBacking", bevel_box(1.3, 1.7, 0.1, 0.02, c=(0, 0, 0.05)), fr, "paper_old",
           shadow=False)
    k.mesh(m, "Ghost", "Dress__EmpGhost", bevel_box(0.9, 1.15, 0.05, 0.015, c=(0, 0.1, 0.125)), fr, "paper",
           shadow=False)
    k.mesh(m, "Tape", "Dress__EmpTape", tape_geo([(-0.45, 0.68), (0.45, 0.68), (-0.45, -0.48), (0.45, -0.48)]),
           fr * CF((0, 0, 0.15)), "tape", shadow=False)
    k.mesh(m, "Plate", "Dress__EmpPlate", bevel_box(1.7, 0.5, 0.1, 0.03, c=(0, 0, 0.05)), fr * CF((0, -1.35, 0.0)),
           "brass", shadow=False)
    text(k, m, fr, 0.0, -1.35, 0.1, (1.55, 0.36), "brass", text="EMPLOYEE OF THE MONTH", text_color=(50, 36, 16),
         name="Nameplate")
    k.mark_used("EmployeeOfTheMonth")


def wall_clock(k, f):
    """A school clock over the sauce station. Its second hand turns the wrong way (Spin)."""
    m = k.sc.model(f, "WallClock")
    fr = wf("N", -0.35, 7.6)
    k.mesh(m, "Case", "Dress__ClockCase", ccyl(0.8, 0.3, 12, "z", (0, 0, 0.15), 0.06), fr, "red", shadow=False)
    k.mesh(m, "Face", "Dress__ClockFace", ccyl(0.66, 0.06, 12, "z", (0, 0, 0.33), 0.02), fr, "paper", shadow=False)
    k.mesh(m, "Bezel", "Dress__ClockBezel", G.torus(0.7, 0.08, 12, 4, "z", (0, 0, 0.34)), fr, "steel_light",
           shadow=False)
    ticks = G.Geo()
    for i in range(12):
        big = i % 3 == 0
        t = bevel_box(0.15, 0.26 if big else 0.16, 0.04, 0.015, c=(0, 0.5, 0.38))
        ticks.add(t.xf(G.M(G.rz(30.0 * i))))
    k.mesh(m, "Ticks", "Dress__ClockTicks", ticks, fr, "black", shadow=False)
    # HourHand and MinuteHand: each its own part, pivot at the centre with its Y out of the
    # face (as the SecondHand), so the game sets the time by turning them about Y; ten past ten
    axis = fr * CF((0, 0, 0.42), G.rx(90))            # local -Z points to twelve
    for nm, ln, ang, zoff in (("HourHand", 0.36, -60.0, 0.0), ("MinuteHand", 0.52, 60.0, 0.03)):
        hg = G.Geo()
        hg.add(bevel_box(0.15, 0.04, ln, 0.015, c=(0, zoff, -ln / 2 + 0.05)))
        hg.add(ccyl(0.1, 0.04, 8, "y", (0, zoff, 0), 0.015))
        hp = k.mesh(m, nm, "Dress__Clock" + nm, hg.xf(G.M(G.ry(ang))), axis, "black", shadow=False)
        hp.p["pivot"] = hp.p["cf"].inv() * axis
    sec = G.Geo()                                                     # its own Y is the clock's axis
    sec.add(bevel_box(0.15, 0.04, 1.1, 0.015))
    sec.add(ccyl(0.08, 0.06, 8, "y", (0, 0, 0), 0.02))
    sh = k.mesh(m, "SecondHand", "Dress__ClockSecond", sec, fr * CF((0, 0, 0.47), G.rx(90)), "red", shadow=False)
    k.attr(sh, "Spin", 6.0)            # degrees a second about its own Y (out of the wall): anticlockwise
    k.mark_used("WallClock")


def posters(k, f):
    """A safety poster beside the clock and a faded promo over the sink corner, taped up,
    one corner come loose."""
    m = k.sc.model(f, "SafetyPoster")
    fr = wf("N", 1.75, 7.55)
    k.mesh(m, "Sheet", "Dress__PosterA", bevel_box(1.6, 1.4, 0.05, 0.015, c=(0, 0, 0.025)), fr, "paper",
           shadow=False)
    text(k, m, fr, 0.0, 0.42, 0.05, (1.5, 0.4), "red", text="SAFETY FIRST!", text_color=(250, 240, 220), name="Heading")
    text(k, m, fr, 0.0, -0.22, 0.05, (1.3, 0.75), "paper", text="LIFT WITH\nYOUR KNEES", text_color=(40, 40, 40),
         name="Body")
    k.mesh(m, "Tape", "Dress__PosterTape", tape_geo([(-0.72, 0.62), (0.72, 0.62), (-0.72, -0.62)]),
           fr * CF((0, 0, 0.05)), "tape", shadow=False)
    curl = chamfer_slab([(0.0, 0.0), (0.42, 0.0), (0.0, 0.42)], 0.05, 0.015)
    k.mesh(m, "Curl", "Dress__PosterCurl", curl.xf(G.M(G.rx(-90))).xf(G.M(G.rz(180))),
           fr * CF((0.8, -0.7, 0.06), G.ry(-35)), "paper_old", shadow=False)
    k.mark_used("Poster")

    m = k.sc.model(f, "PromoPoster")            # outside, on the front wall over the bench
    fr = CF((-11.4, 6.4, L.OUT_Z1 + 0.5), G.ry(0))
    k.mesh(m, "Sheet", "Dress__PosterB", bevel_box(1.8, 2.4, 0.05, 0.015, c=(0, 0, 0.025)), fr, "red_faded",
           shadow=False)
    text(k, m, fr, 0.0, 0.7, 0.05, (1.6, 0.7), "red_faded", text="NEW!", text_color=(250, 226, 150), name="Heading")
    text(k, m, fr, 0.0, -0.25, 0.05, (1.6, 1.0), "red_faded", text="DOUBLE\nCHEESE\nCRUST", text_color=(250, 240, 220),
         name="Body")
    text(k, m, fr, 0.0, -0.98, 0.05, (1.4, 0.3), "mustard", text="ONLY $5.99", text_color=(60, 30, 20), name="Price")
    k.mesh(m, "Tape", "Dress__PosterTapeB", tape_geo([(-0.82, 1.12), (0.82, 1.12), (0.82, -1.12), (-0.82, -1.12)]),
           fr * CF((0, 0, 0.05)), "tape", shadow=False)
    k.mark_used("PromoPoster")


def wet_floor_sign(k, f):
    """The yellow A-frame folded shut and leant against the wall in the corner by the back door,
    ready for when the rain comes in: out of the way in (the door is never blocked) and of the
    locker doors, its words to the room."""
    m = k.sc.model(f, "WetFloorSign")
    k.attr(m, "Loose", True)                          # the game may knock it about
    base = CF((L.IN_X0 + 0.6, L.FLOOR, -7.4), G.ry(90) @ G.rx(-10))          # top leaning on the west wall
    ang, h = 2.0, 2.2
    top = h * math.cos(math.radians(ang))
    leaf = G.Geo()
    leaf.add(bevel_box(1.2, h, 0.15, 0.05))
    leaf.add(bevel_box(0.5, 0.2, 0.17, 0.03, c=(0, h / 2 - 0.35, 0)))
    feet = G.Geo()
    for sz in (-1, 1):
        R = G.rx(-sz * ang)
        for dx in (-0.5, 0.5):
            p = R @ np.array((dx, -h + 0.05, sz * 0.075))
            feet.add(bevel_box(0.2, 0.15, 0.3, 0.04, c=(p[0], 0.075, p[2])))
    for sz in (-1, 1):
        cf = base * CF((0, top, 0), G.rx(-sz * ang)) * CF((0, -h / 2, sz * 0.075))
        k.mesh(m, "Leaf", "Dress__WetLeaf", leaf, cf, "mustard_bright", shadow=False)
        face = cf * CF((0, -0.15, sz * 0.075)) * (CF() if sz < 0 else CF((0, 0, 0), G.ry(180)))
        board(k, m, (1.0, 1.0, 0.15), face * CF((0, 0, -0.075)), "mustard_bright", text="CAUTION\nWET\nFLOOR",
              text_color=(20, 20, 20), name="Warning")
    k.mesh(m, "Hinge", "Dress__WetHinge", rod((-0.55, 0, 0), (0.55, 0, 0), 0.09, 6), base * CF((0, top - 0.05, 0)),
           "grey_dark", shadow=False)
    k.mesh(m, "Feet", "Dress__WetFeet", feet, base, "black", shadow=False)
    k.mark_used("WetFloorSign")


def fly_strips(k, f):
    """Sticky fly papers hanging from the ceiling by the bin and by the back door (Sway), with
    the flies they have not caught yet."""
    for i, (x, z) in enumerate(((2.0, 4.0), (-13.6, -3.4))):
        m = k.sc.model(f, "FlyStrip%d" % (i + 1))
        k.mesh(m, "Canister", "Dress__FlyCan", ccyl(0.16, 0.4, 8, "y", (0, -0.2, 0), 0.03), CF((x, L.CEIL, z)),
               "red_dark", shadow=False)
        strip = G.Geo()
        for j in range(6):
            strip.add(bevel_box(0.22, 0.32, 0.04, 0.012, c=(0, -0.55 - 0.3 * j, 0)).xf(G.M(G.ry(28 * j))))
        s = k.mesh(m, "Strip", "Dress__FlyStrip", strip, CF((x, L.CEIL, z)), "fly_amber", shadow=False)
        dots = G.Geo()
        for j in (1, 3, 4):
            dots.add(bevel_box(0.15, 0.15, 0.05, 0.02, c=(0.03, -0.55 - 0.3 * j, 0.03)).xf(G.M(G.ry(28 * j))))
        k.mesh(m, "Caught", "Dress__FlyDots", dots, CF((x, L.CEIL, z)), "black", shadow=False)
        k.attr(m, "Sway", 2.0)
        k.sc.attachment(s, "Fx_Flies", CF((x, L.CEIL - 1.6, z)))
    k.mark_used("FlyStrip")


# ---------------------------------------------------------------- conduit drops and sockets

def _blockers(sc):
    """World AABBs of what is on or near the walls (stations, fixtures, dressing)."""
    from .checks import Boxes
    skip = ("Conduit", "ConduitClips")

    def keep(n):
        if n.name in skip:
            return False
        path = n.path()
        return n.top() == "Stations" or "/Shack/Fixtures/" in path or "/Shack/Dressing/" in path
    b = Boxes(sc, keep=keep)
    return b.lo, b.hi


def _free(lo, hi, w, ua, ub, ya, yb, d0, d1, pad=0.05):
    """Nothing (stations, fixtures, dressing) and no opening in this wall-relative box."""
    from .shell import WALLS
    for (oa, ob, oy0, oy1) in WALLS[w]:
        if ua < ob + 0.6 and ub > oa - 0.6 and ya < oy1 + 0.6 and yb > oy0 - 0.6:
            return False
    a, b = (np.asarray(v, float) for v in C.wlohi(w, ua, ub, ya, yb, d0, d1))
    a, b = np.minimum(a, b) - pad, np.maximum(a, b) + pad
    hit = np.all(lo < b, axis=1) & np.all(hi > a, axis=1)
    return not hit.any()


Y_RUN = 8.4               # the conduit runs under the beam ends (st_ceiling.conduit)
D_RUN = 0.75


def conduit_drops(k, f, sc):
    """Double sockets on the backsplash over the worktops, about one a station (at least 3.5
    apart); where the wall above one is clear all the way up, its conduit drops to it from the
    run under the ceiling, clipped with saddles."""
    lo, hi = _blockers(sc)
    tops = [n for n in sc.nodes(("Part",)) if n.name == "Top" and n.top() == "Stations"
            and n.path().split("/")[2] != "BoxStation"]          # an open box's lid stands against that wall
    tlo = np.array([n.p["cf"].p - np.abs(n.p["cf"].R) @ (np.asarray(n.p["size"]) / 2) for n in tops])
    thi = np.array([n.p["cf"].p + np.abs(n.p["cf"].R) @ (np.asarray(n.p["size"]) / 2) for n in tops])
    g, boxes = G.Geo(), G.Geo()
    m = k.sc.model(f, "Sockets")
    n_sock, n_drop = 0, 0
    for w in ("N", "S", "E", "W"):
        ua, ub = IP.wall_rect(w)
        last = -1e9
        for u in np.arange(ua + 1.0, ub - 1.0, 0.2):
            u = round(float(u), 2)
            if u - last < 3.5:
                continue
            if _free(tlo, thi, w, u - 0.6, u + 0.6, 3.1, 3.3, 0.0, 1.0):     # no worktop under it
                continue
            if not _free(lo, hi, w, u - 0.65, u + 0.65, 3.5, 4.3, 0.0, 0.45):
                continue
            k.prop(m, "Socket", C.wcf(w, u, 3.9, 0.0), name="Socket")
            n_sock += 1
            last = u
            if w in ("N", "S", "W") and _free(lo, hi, w, u - 0.3, u + 0.3, 4.2, Y_RUN + 0.15, 0.0, 0.4):
                p_top, p_run, p_bot = C.wpt(w, u, Y_RUN, 0.15), C.wpt(w, u, Y_RUN, D_RUN), C.wpt(w, u, 4.2, 0.15)
                g.add(rod(p_run, p_top, 0.1, 6))
                g.add(rod(p_top, p_bot, 0.1, 6))
                for yy in np.arange(5.4, Y_RUN - 0.4, 1.6):
                    boxes.add(bevel_box(0.3, 0.15, 0.3, 0.04).xf(G.M(C.ROT[w])).xf(G.T(*C.wpt(w, u, yy, 0.1))))
                n_drop += 1
            a_, b_ = C.wlohi(w, u - 0.7, u + 0.7, 3.5, 4.3, 0.0, 0.45)
            lo = np.vstack((lo, np.minimum(a_, b_)))
            hi = np.vstack((hi, np.maximum(a_, b_)))
    if g.f:
        k.mesh(m, "Conduit", "Dress__ConduitDrops", g, CF(), "steel_dark", shadow=False)
        k.mesh(m, "Saddles", "Dress__ConduitSaddles", boxes, CF(), "charcoal", shadow=False)
    return n_sock, n_drop


# ---------------------------------------------------------------- wear on the paint

PAINT_Y = (4.75, 8.45)


def paint_wear(k, f, sc, rng):
    """Patches painted over in a slightly different green, the clean ghosts of signs that
    came down, and grime: always a shade of the paint itself. Each patch is let 0.1 into the
    wall and stands 0.05 proud of it."""
    lo, hi = _blockers(sc)
    m = k.sc.model(f, "PaintWear")
    looks = (("paint_patch", (1.6, 3.2), (1.0, 2.0)), ("paint_ghost", (1.2, 2.0), (0.9, 1.6)),
             ("paint_grime", (1.0, 2.6), (0.8, 1.6)))
    n = 0
    for w in ("N", "S", "E", "W"):
        u0, u1 = IP.wall_rect(w)
        tries = 0
        placed = 0
        while placed < 3 and tries < 400:
            tries += 1
            kind, (wa, wb), (ha, hb) = looks[int(rng.integers(0, 3))]
            wd, ht = float(rng.uniform(wa, wb)), float(rng.uniform(ha, hb))
            u = float(rng.uniform(u0 + wd / 2 + 0.3, u1 - wd / 2 - 0.3))
            y = float(rng.uniform(PAINT_Y[0] + ht / 2, PAINT_Y[1] - ht / 2))
            if not _free(lo, hi, w, u - wd / 2 - 0.2, u + wd / 2 + 0.2, y - ht / 2 - 0.2, y + ht / 2 + 0.2, 0.0, 2.2):
                continue                                  # (nothing standing in front of it either)
            geo = chamfer_slab(_blob(rng, wd, ht), 0.15, 0.04).xf(G.M(G.rx(90)))
            k.mesh(m, "Paint", "Dress__Wear%d" % n, geo, C.wcf(w, u, y, -0.1), kind, shadow=False)
            # keep the next one clear of this one
            a, b = C.wlohi(w, u - wd / 2, u + wd / 2, y - ht / 2, y + ht / 2, 0.0, 0.6)
            lo = np.vstack((lo, np.minimum(a, b)))
            hi = np.vstack((hi, np.maximum(a, b)))
            placed += 1
            n += 1
    k.mark_used("PaintWear")
    return n


def _blob(rng, w, h, ragged=0.12):
    """A roller-painted rectangle about w x h with ragged edges (top view (x, z); it is turned
    onto the wall). The corners are cut a little; each side wanders by up to `ragged`."""
    pts = []
    hw, hh = w / 2, h / 2
    sides = (((-hw, -hh), (hw, -hh)), ((hw, -hh), (hw, hh)), ((hw, hh), (-hw, hh)), ((-hw, hh), (-hw, -hh)))
    for (x0, z0), (x1, z1) in sides:
        ln = math.hypot(x1 - x0, z1 - z0)
        n = max(2, int(ln / 0.5))
        nx, nz = (z1 - z0) / ln, -(x1 - x0) / ln            # outward normal (counter-clockwise outline)
        for i in range(n):
            t = (i + (0.18 if i == 0 else 0.0)) / n
            off = float(rng.uniform(-ragged, ragged)) if i else -0.05
            pts.append((x0 + (x1 - x0) * t + nx * off, z0 + (z1 - z0) * t + nz * off))
    return pts


# ---------------------------------------------------------------- fx on the stations


def station_fx(k, sc):
    """Steam off the stock pot, a drip from the sink tap, flies over the bin."""
    st = sc.root.get("Stations")
    pot = st.get("SauceStation").get("Pot")
    part = next(c for c in pot.children if c.is_part())
    p = part.p["cf"].p
    k.sc.attachment(part, "Fx_Steam", CF((p[0], L.WORK + 1.9, p[2])))
    sink = st.get("Sink")
    tap = sink.get("Faucet")
    tp = tap.p["cf"].p
    k.sc.attachment(tap, "Fx_Drip", CF((tp[0], L.WORK + 0.9, tp[2] - 0.85)))
    b = st.get("Bin").get("Body")
    bp = b.p["cf"].p
    k.sc.attachment(b, "Fx_Flies", CF((bp[0], 3.2, bp[2])))


def build(k):
    sc = k.sc
    f = sc.folder(sc.root.get("Shack"), "Dressing")
    rng = np.random.default_rng(1986)
    days_since(k, f)
    inspection_certificate(k, f)
    employee_frame(k, f)
    wall_clock(k, f)
    posters(k, f)
    wet_floor_sign(k, f)
    fly_strips(k, f)
    station_fx(k, sc)
    conduit_drops(k, f, sc)
    paint_wear(k, f, sc, rng)
    return f
