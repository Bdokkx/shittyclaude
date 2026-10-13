"""Counters and cabinets, built the way a real kitchen run is: a dark carcass (so the gaps
between doors read as shadow lines), a recessed black plinth, shaker doors and drawer fronts
with bar pulls and hinges, red end panels, and a steel worktop with a rolled front edge that
runs right to the wall (the tile row stands on it, no gap).

Wall-relative helpers: d is the distance from the wall's inside face into the room, u the
position along the wall (X on N / S, Z on W / E), Y as usual."""
import math

import numpy as np

import spsgeo as G
from spsgeo import CF

from . import interior as IP, layout as L
from .kit import bevel_box, rod

# ---------------------------------------------------------------- wall-relative placement


def wlohi(w, u0, u1, y0, y1, d0, d1):
    """World corners of a box spanning u0..u1, y0..y1 and d0..d1 from wall w's face."""
    if w == "N":
        return (u0, y0, L.IN_Z0 + d0), (u1, y1, L.IN_Z0 + d1)
    if w == "S":
        return (u0, y0, L.IN_Z1 - d1), (u1, y1, L.IN_Z1 - d0)
    if w == "W":
        return (L.IN_X0 + d0, y0, u0), (L.IN_X0 + d1, y1, u1)
    return (L.IN_X1 - d1, y0, u0), (L.IN_X1 - d0, y1, u1)


def wbox(k, parent, name, w, u0, u1, y0, y1, d0, d1, color, **kw):
    lo, hi = wlohi(w, u0, u1, y0, y1, d0, d1)
    return k.box(parent, name, lo, hi, color, **kw)


ROT = {"N": np.eye(3), "S": G.ry(180), "W": G.ry(90), "E": G.ry(-90)}


def wpt(w, u, y, d):
    """World point at (u, y, d) of wall w."""
    if w == "N":
        return np.array((u, y, L.IN_Z0 + d))
    if w == "S":
        return np.array((u, y, L.IN_Z1 - d))
    if w == "W":
        return np.array((L.IN_X0 + d, y, u))
    return np.array((L.IN_X1 - d, y, u))


def wcf(w, u, y, d, R=None):
    """Frame at (u, y, d) of wall w: local +Z points into the room, +Y up (local +X runs along
    u on N and E, against it on S and W). R is an extra local rotation."""
    Rw = ROT[w] if R is None else ROT[w] @ R
    return CF(wpt(w, u, y, d), Rw)


def sgn(w):
    """+1 where a wall frame's local +X runs along u (N, E), -1 where it runs against (S, W)."""
    return 1.0 if w in ("N", "E") else -1.0


def facing_room(w):
    """Unit vector from wall w into the room."""
    return {"N": (0, 0, 1), "S": (0, 0, -1), "W": (1, 0, 0), "E": (-1, 0, 0)}[w]


def toward_wall(w):
    return tuple(-v for v in facing_room(w))


# ---------------------------------------------------------------- pieces (meshes, shared by size)

def door_geo(w_, h_, t=0.2, frame=0.28):
    """Shaker door: a bevelled frame and a recessed panel; local origin at the door's centre,
    back face at z = 0, front at z = t."""
    g = G.Geo()
    fz = t / 2
    g.add(bevel_box(w_, frame, t, 0.05, c=(0, h_ / 2 - frame / 2, fz)))
    g.add(bevel_box(w_, frame, t, 0.05, c=(0, -h_ / 2 + frame / 2, fz)))
    g.add(bevel_box(frame, h_ - 2 * frame + 0.02, t, 0.05, c=(-w_ / 2 + frame / 2, 0, fz)))
    g.add(bevel_box(frame, h_ - 2 * frame + 0.02, t, 0.05, c=(w_ / 2 - frame / 2, 0, fz)))
    g.add(bevel_box(w_ - 2 * frame + 0.04, h_ - 2 * frame + 0.04, t - 0.06, 0.03, c=(0, 0, (t - 0.06) / 2)))
    return g


def pull_geo(length=0.9, standoff=0.16, r=0.08):
    """Bar pull: a chunky rod on two standoffs, along local X, standing off +Z."""
    g = G.Geo()
    g.add(rod((-length / 2, 0, standoff), (length / 2, 0, standoff), r, 6))
    for x in (-length / 2 + 0.1, length / 2 - 0.1):
        g.add(rod((x, 0, 0.0), (x, 0, standoff), r * 0.9, 6))
    return g


def knob_geo():
    return G.outward(G.lathe([(0, 0), (0.1, 0), (0.08, 0.08), (0.14, 0.14), (0.12, 0.22), (0, 0.24)], 8)).xf(
        G.M(G.rx(90)))


def hinge_geo():
    return bevel_box(0.15, 0.4, 0.15, 0.03)


EDGE_GEO = {}


def edge_geo(length):
    """The worktop's rolled front edge (a bevelled bar 0.4 tall, 0.2 proud)."""
    if length not in EDGE_GEO:
        EDGE_GEO[length] = bevel_box(length, 0.4, 0.2, 0.08)
    return EDGE_GEO[length]


# ---------------------------------------------------------------- a counter run
#
# A run is built in two steps. counter() lays the worktop, plinth, end panels and a HOLLOW
# carcass per section (back, bottom, sides, top, a shelf behind doors) with an invisible
# blocker across its front, and queues the fronts. finish() (after every station has put
# its Stand) builds the fronts as openable Models: each door hinged on the side away from
# the nearest Stand, each drawer a box that slides out with what is in it, and fills the
# cupboards and drawers (opens.py has the contract).

PANEL = 0.2                  # carcass panels
SHELF_SET = 0.2              # shelves stop short of the doors


def counter(k, m, w, u0, u1, depth, top="steel", door="red", fronts=None, ajar=(), body_col="cab_inside",
            end_left=True, end_right=True, owner="Counter", plinth=True, top_y=None, top_name="Top", shelf=None,
            open_sides=True, top_hole=None, insides=None, notes=None, stock="kitchen", door_sound="Cabinet",
            noshelf=(), hinges=None):
    """A cabinet run on wall w from u0 to u1, `depth` deep, worktop at 3.4 running to the wall.
    fronts: [(width, kind)] along u covering u0..u1, kind in 'doors2', 'door', 'drawers',
    'drawers3', 'open'; defaults to pairs of doors 2 wide. shelf: {section index: y} adds a
    shelf in an open bay. insides: {section index: [...]} what goes in a section: for doors a
    list of prop kinds, "|" moving on to the shelf above; for drawers one entry per drawer
    (bottom first, None = empty). notes: {section index: text} taped inside its first door.
    Kinds also 'slide2' (two doors sliding past each other) and 'blind' (a plain panel where
    something stands in front). hinges: {section index: 'a' | 'b' | ['a', 'b']} forces the
    hinge edge (a = the low-u edge) where the Stand rule would put a door into a wall.
    stock picks the defaults ('kitchen', 'cleaning', 'front', 'office'); noshelf: door sections
    left one tall space. Returns the worktop."""
    top_y = top_y or L.WORK
    D = depth
    y_body = top_y - 0.4                       # carcass top = worktop underside
    fronts = fronts or _default_fronts(u1 - u0)
    assert abs(sum(wd for wd, _ in fronts) - (u1 - u0)) < 1e-6, (owner, fronts, u0, u1)
    if plinth:
        wbox(k, m, "Plinth", w, u0, u1, 0.2, 0.6, 0.0, D - 1.0, "black", solid=True)
    tmat = "SmoothPlastic" if top.startswith("steel") else "Plastic"   # flat colour only: no Metal texture
    if top_hole is None:
        t = wbox(k, m, top_name, w, u0, u1, top_y - 0.4, top_y, 0.0, D, top, solid=True, material=tmat)
    else:
        from .terrain import subtract
        ha, hb, hd0, hd1 = top_hole
        t = None
        for (a, b, d0, d1) in subtract((u0, u1, 0.0, D), [(ha, hb, hd0, hd1)]):
            p_ = wbox(k, m, top_name, w, a, b, top_y - 0.4, top_y, d0, d1, top, solid=True, material=tmat)
            t = t or p_
    ln = u1 - u0
    k.mesh(m, "TopEdge", "Counter__Edge%d" % int(round(ln * 10)), edge_geo(ln),
           wcf(w, (u0 + u1) / 2, top_y - 0.2, D), "steel_dark", shadow=False)
    u = u0
    fy0, fy1 = 0.7, y_body - 0.1
    queue = getattr(k, "fronts_queue", None)
    if queue is None:
        queue = k.fronts_queue = []
    for si, (wd, kind) in enumerate(fronts):
        a, b = u, u + wd
        el = end_left and abs(a - u0) < 1e-6
        er = end_right and abs(b - u1) < 1e-6
        ia = a + (0.4 if el else 0.0)
        ib = b - (0.4 if er else 0.0)
        if kind == "blind":
            # a blind corner (something stands in front of it): a carcass and a plain panel, no door
            _carcass(k, m, w, a, b, 0.6, y_body, D - 0.6, body_col, owner, side_a=not el, side_b=not er)
            k.mesh(m, "BlindPanel", "%s__Blind%d" % (owner, int(round((ib - ia) * 10))),
                   bevel_box(ib - ia - 0.12, fy1 - fy0 - 0.12, 0.2, 0.05), wcf(w, (ia + ib) / 2, (fy0 + fy1) / 2, D - 0.5),
                   door, solid=True)
        elif kind == "open":
            _bay(k, m, w, a, b, 0.6, y_body, D - 0.6, body_col, owner, shelf_y=(shelf or {}).get(si),
                 side_a=open_sides and (abs(a - u0) > 1e-6 or not end_left),
                 side_b=open_sides and (abs(b - u1) > 1e-6 or not end_right))
        else:
            sh = (0.6 + y_body) / 2 if kind in ("doors2", "door", "slide2") and si not in noshelf else None
            _carcass(k, m, w, a, b, 0.6, y_body, D - 0.6, body_col, owner, side_a=not el, side_b=not er,
                     shelf_y=sh)
            # the carcass is hollow: an invisible blocker across its front keeps players out of it
            wbox(k, m, "Blocker", w, a, b, 0.6, y_body, D - 0.6 - 0.3, D - 0.6, "black", solid=True,
                 transparency=1.0, query=False, touch=False, shadow=False, grid=False)
            queue.append(dict(m=m, w=w, a=a, b=b, ia=ia + (0.0 if el else PANEL), ib=ib - (0.0 if er else PANEL),
                              fa=ia, fb=ib, kind=kind, fy0=fy0, fy1=fy1, d=D - 0.6, color=door, owner=owner,
                              y_body=y_body, shelf_y=sh, insides=(insides or {}).get(si),
                              note=(notes or {}).get(si), stock=stock, sound=door_sound,
                              hinges=(hinges or {}).get(si)))
        u = b
    # end panels where the run ends in the open
    for e, on in ((u0, end_left), (u1, end_right)):
        if not on:
            continue
        a, b = (e, e + 0.4) if e == u0 else (e - 0.4, e)
        k.mesh(m, "EndPanel", "Counter__End%dx%d" % (int(D * 10), int(y_body * 10)),
               bevel_box(0.4, y_body - 0.2, D - 0.4, 0.06), wcf(w, (a + b) / 2, (0.2 + y_body) / 2, (D - 0.4) / 2),
               door, solid=True)
    return t


def _carcass(k, m, w, a, b, y0, y1, d1, col_, owner, side_a=True, side_b=True, shelf_y=None):
    """A hollow cabinet box: back, bottom, top, sides (where no end panel stands), a shelf set
    back from the doors; open at the front."""
    wd, ht = b - a, y1 - y0
    P = PANEL
    key = "%s__Carcass%dx%dx%d" % (owner, int(round(wd * 10)), int(round(ht * 10)), int(round(d1 * 10)))
    g = G.Geo()
    g.add(bevel_box(wd, ht, P, 0.03, c=(0, 0, -d1 / 2 + P / 2)))                         # back
    g.add(bevel_box(wd, P, d1, 0.03, c=(0, -ht / 2 + P / 2, 0)))                         # bottom
    g.add(bevel_box(wd, P, d1, 0.03, c=(0, ht / 2 - P / 2, 0)))                          # top
    if side_a:
        g.add(bevel_box(P, ht, d1, 0.03, c=(-wd / 2 + P / 2, 0, 0)))
    if side_b:
        g.add(bevel_box(P, ht, d1, 0.03, c=(wd / 2 - P / 2, 0, 0)))
    if shelf_y is not None:
        sd = d1 - P - SHELF_SET
        g.add(bevel_box(wd, P, sd, 0.03, c=(0, shelf_y - (y0 + y1) / 2, -d1 / 2 + P + sd / 2)))
    key += ("a" if side_a else "") + ("b" if side_b else "") + ("s" if shelf_y is not None else "")
    if sgn(w) < 0:
        g = g.xf(G.M(np.diag((-1.0, 1.0, 1.0))))
    k.mesh(m, "Carcass", key, g, wcf(w, (a + b) / 2, (y0 + y1) / 2, d1 / 2), col_, solid=True)


def _bay(k, m, w, a, b, y0, y1, d1, col_, owner, shelf_y=None, side_a=True, side_b=True):
    """The hollow of an open bay: back, floor, sides (where no end panel closes it), shelf."""
    wd = b - a
    key = "%s__Bay%dx%dx%d" % (owner, int(round(wd * 10)), int(round((y1 - y0) * 10)), int(round(d1 * 10)))
    g = G.Geo()
    g.add(bevel_box(wd, y1 - y0, 0.3, 0.03, c=(0, 0, -d1 / 2 + 0.15)))                 # back
    g.add(bevel_box(wd, 0.3, d1, 0.03, c=(0, -(y1 - y0) / 2 + 0.15, 0)))               # floor
    if side_a:
        g.add(bevel_box(0.3, y1 - y0, d1, 0.03, c=(-wd / 2 + 0.15, 0, 0)))
    if side_b:
        g.add(bevel_box(0.3, y1 - y0, d1, 0.03, c=(wd / 2 - 0.15, 0, 0)))
    if shelf_y is not None:
        g.add(bevel_box(wd, 0.3, d1 - 0.3, 0.03, c=(0, shelf_y - (y0 + y1) / 2 - 0.15, 0.15)))
    key += ("a" if side_a else "") + ("b" if side_b else "") + ("s%d" % int(shelf_y * 10) if shelf_y else "")
    # local X along u: mirror for the walls whose frame runs against u
    if sgn(w) < 0:
        g = g.xf(G.M(np.diag((-1.0, 1.0, 1.0))))
    uc = (a + b) / 2
    k.mesh(m, "Bay", key, g, wcf(w, uc, (y0 + y1) / 2, d1 / 2), col_, solid=True)


def _default_fronts(ln):
    n = max(1, int(round(ln / 4)))
    return [(ln / n, "doors2")] * n


def _ualign(w):
    """Rotation so a mesh's local X runs along u, Z into the room (mirror-free)."""
    return np.eye(3)


def _mid(w, u0, u1, y0, y1, d0, d1):
    lo, hi = wlohi(w, u0, u1, y0, y1, d0, d1)
    return tuple((np.array(lo) + np.array(hi)) / 2)


def _place(k, m, name, mesh_name, geo, w, u, y, d, color, R=None, **kw):
    return k.mesh(m, name, mesh_name, geo, wcf(w, u, y, d, R), color, **kw)


# ---------------------------------------------------------------- fronts: doors and drawers

def _next_name(k, m, base):
    cnt = getattr(k, "open_names", None)
    if cnt is None:
        cnt = k.open_names = {}
    key = (id(m), base)
    cnt[key] = cnt.get(key, 0) + 1
    return "%s%d" % (base, cnt[key])


def door_model(k, m, w, a, b, y0, y1, d, color, hinge_left, owner="Counter", name=None, sound="Cabinet",
               angle=90.0):
    """A shaker door between u = a..b (a 0.06 gap all round), its back on the carcass face at
    d, as an openable Model: Leaf, Pull, Hinge; pivot on the hinge edge's front corner (so the
    leaf never cuts into the carcass or its neighbour as it swings)."""
    from .opens import hinge, opener
    gap = 0.06
    wd, ht = (b - a) - 2 * gap, (y1 - y0) - 2 * gap
    uc, yc = (a + b) / 2, (y0 + y1) / 2
    s = sgn(w)
    hu = a + gap if hinge_left else b - gap            # hinge edge, in u
    x_free = (uc - hu) * s                             # door centre from the hinge, in the wall frame
    op = opener(k, m, name or _next_name(k, m, "CabinetDoor"), "Swing", sound,
                angle=-angle if x_free > 0 else angle)
    frame = wcf(w, uc, yc, d)
    dname = "%s__Door%dx%d" % (owner, int(round(wd * 100)), int(round(ht * 100)))
    leaf = k.mesh(op, "Leaf", dname, door_geo(round(wd, 2), round(ht, 2)), frame, color)
    pu = (b - gap - 0.35) if hinge_left else (a + gap + 0.35)
    k.mesh(op, "Pull", "Counter__Pull", pull_geo(0.6), frame * CF(((pu - uc) * s, ht / 2 - 0.55, 0.2)) * CF(R=G.rz(90)),
           "steel_light", shadow=False)
    for dy in (ht / 2 - 0.45, -ht / 2 + 0.45):
        k.mesh(op, "Hinge", "Counter__Hinge", hinge_geo(), frame * CF((-x_free + 0.06 * (1 if x_free > 0 else -1), dy,
                                                                        0.075)), "charcoal", shadow=False)
    hinge(op, leaf, wcf(w, hu, yc, d + 0.2))
    return op


def drawer_model(k, m, w, a, b, y0, y1, d, depth_in, color, owner="Counter", name=None, slide=None, box_col="cab_inside"):
    """A drawer between u = a..b, y0..y1, its front's back face at d: the Front, its Pull and
    the Box behind it (sides, back, bottom) that slides out `slide` (default 1.8, never more
    than 70% of the box). Returns (model, floor frame at the box's front-centre, inside size)."""
    from .opens import hinge, opener
    gap = 0.06
    wd, ht = (b - a) - 2 * gap, (y1 - y0) - 2 * gap
    uc, yc = (a + b) / 2, (y0 + y1) / 2
    depth_in = min(depth_in, 3.2)
    slide = min(slide or 1.8, round(depth_in * 0.7, 1))
    op = opener(k, m, name or _next_name(k, m, "CabinetDrawer"), "Slide", "Drawer", offset=(0.0, 0.0, slide))
    frame = wcf(w, uc, yc, d)
    fname = "%s__Drawer%dx%d" % (owner, int(round(wd * 100)), int(round(ht * 100)))
    front = k.mesh(op, "Front", fname, door_geo(round(wd, 2), round(ht, 2), frame=0.2), frame, color)
    pl = round(min(1.2, wd - 0.6), 1)
    k.mesh(op, "Pull", "Counter__Pull%d" % int(pl * 10), pull_geo(pl), wcf(w, uc, yc + ht / 2 - 0.3, d + 0.2),
           "steel_light", shadow=False)
    # the box: 0.15 walls, its top 0.2 under the front's top edge
    bw = wd - 0.4                                    # 0.06 clear of the carcass sides
    bh = ht - 0.15
    by0 = y0 + gap + 0.08                            # box bottom (world y)
    T_ = 0.15
    g = G.Geo()
    zc = -depth_in / 2
    g.add(bevel_box(bw, T_, depth_in, 0.03, c=(0, T_ / 2, zc)))                       # bottom
    g.add(bevel_box(T_, bh, depth_in, 0.03, c=(-bw / 2 + T_ / 2, bh / 2, zc)))
    g.add(bevel_box(T_, bh, depth_in, 0.03, c=(bw / 2 - T_ / 2, bh / 2, zc)))
    g.add(bevel_box(bw, bh, T_, 0.03, c=(0, bh / 2, -depth_in + T_ / 2)))             # back
    k.mesh(op, "Box", "%s__DrawerBox%dx%dx%d" % (owner, int(round(bw * 100)), int(round(bh * 100)),
                                                  int(round(depth_in * 100))),
           g, wcf(w, uc, by0, d), box_col, shadow=False)
    hinge(op, front, wcf(w, uc, yc, d))
    floor = wcf(w, uc, by0 + T_, d)
    inside = (bw - 2 * T_, bh - T_, depth_in - T_)
    return op, floor, inside


def slide_pair(k, m, w, a, b, y0, y1, d, color, owner="Counter"):
    """Two steel doors that slide past each other (a prep fridge's): the west/left one on the
    front track, the other behind it, each overlapping the middle by 0.1; each slides over the
    other by half the opening, so nothing ever swings out into the room."""
    from .opens import hinge, opener
    s = sgn(w)
    half = (b - a) / 2
    lw, ht = half + 0.1, (y1 - y0) - 0.12
    yc = (y0 + y1) / 2
    out = []
    for j, (uc, dd, dirn) in enumerate(((a + lw / 2, d + 0.2, +1), (b - lw / 2, d, -1))):
        op = opener(k, m, _next_name(k, m, "SlidingDoor"), "Slide", "Metal", offset=(dirn * s * (half - 0.1), 0.0, 0.0))
        frame = wcf(w, uc, yc, dd)
        leaf = k.mesh(op, "Leaf", "%s__Slide%dx%d" % (owner, int(round(lw * 100)), int(round(ht * 100))),
                      door_geo(round(lw, 2), round(ht, 2), t=0.18, frame=0.22), frame, color)
        ge = (uc - lw / 2 + 0.3) if dirn > 0 else (uc + lw / 2 - 0.3)       # a grip at the outer edge
        if dirn > 0:                                     # the front door: a bar grip standing proud
            k.mesh(op, "Pull", "Counter__SlideGrip", bevel_box(0.2, 1.0, 0.18, 0.05),
                   wcf(w, ge, yc + 0.2, dd + 0.27), "steel_dark", shadow=False)
        else:                                            # the back one slides behind it: a flush finger slot
            k.mesh(op, "Pull", "Counter__SlideSlot", bevel_box(0.2, 1.0, 0.15, 0.04),
                   wcf(w, ge, yc + 0.2, dd + 0.11), "black", shadow=False)
        hinge(op, leaf, wcf(w, uc, yc, dd))
        out.append(op)
    # the tracks top and bottom
    for yy in (y0 - 0.02, y1 + 0.02):
        k.mesh(m, "Track", "%s__Track%d" % (owner, int(round((b - a) * 10))), bevel_box(b - a, 0.15, 0.4, 0.03),
               wcf(w, (a + b) / 2, yy, d + 0.2), "steel_dark", shadow=False)
    return out


def _resolve_hinges(k, leaves, stands):
    """Hinge each leaf on its edge away from the nearest Stand, then move any two hinges that
    meet on a shared edge (their open leaves would clash) apart."""
    def su_of(L_):
        mid = wpt(L_["w"], (L_["a"] + L_["b"]) / 2, 1.0, L_["d"])
        own = [p for (st, p) in stands if st is L_["m"]] or [p for (_, p) in stands]
        near = min(own, key=lambda p: np.hypot(p[0] - mid[0], p[2] - mid[2]))
        return near[0] if L_["w"] in ("N", "S") else near[2]
    for L_ in leaves:
        if L_["force"] is not None:
            L_["left"] = L_["force"] == "a"
        else:
            su = su_of(L_)
            L_["left"] = abs(su - L_["a"]) >= abs(su - L_["b"])
    by_wall = {}
    for L_ in leaves:
        by_wall.setdefault(L_["w"], []).append(L_)
    for w, lst in by_wall.items():
        lst.sort(key=lambda L_: L_["a"])
        for x, y in zip(lst, lst[1:]):
            if abs(x["b"] - y["a"]) <= 0.3 and not x["left"] and y["left"]:
                # both hinged on the shared edge: each stops short of square so the pulls pass
                x["angle"] = y["angle"] = 75.0


def finish(k):
    """Build every queued front, now the Stands are down, and fill them."""
    from . import insides
    stands = []
    for st in k.sc.root.get("Stations").children:
        for n in st.walk():
            if n.kind == "Marker" and n.name.startswith("Stand"):
                stands.append((st, n.p["cf"].p))
    queue = getattr(k, "fronts_queue", [])
    leaves = []
    for q in queue:
        if q["kind"] in ("doors2", "door"):
            fa, fb = q["fa"], q["fb"]
            spans = [(fa, (fa + fb) / 2), ((fa + fb) / 2, fb)] if q["kind"] == "doors2" else [(fa, fb)]
            force = q.get("hinges")
            if not isinstance(force, (list, tuple)):
                force = [force] * len(spans)
            q["leaves"] = []
            for (a, b), f in zip(spans, force):
                L_ = dict(m=q["m"], w=q["w"], a=a, b=b, d=q["d"], force=f)
                q["leaves"].append(L_)
                leaves.append(L_)
    _resolve_hinges(k, leaves, stands)
    for q in queue:
        w, kind = q["w"], q["kind"]
        fa, fb, fy0, fy1, d = q["fa"], q["fb"], q["fy0"], q["fy1"], q["d"]
        if kind in ("doors2", "door"):
            doors = [door_model(k, q["m"], w, L_["a"], L_["b"], fy0, fy1, d, q["color"], L_["left"], owner=q["owner"],
                                sound=q["sound"], angle=L_.get("angle", 90.0)) for L_ in q["leaves"]]
            insides.fill_cupboard(k, q, doors)
        elif kind == "slide2":
            doors = slide_pair(k, q["m"], w, fa, fb, fy0, fy1, d, q["color"], owner=q["owner"])
            insides.fill_cupboard(k, q, doors)
        else:
            n = 2 if kind == "drawers" else 3
            hs = (fy1 - fy0) / n
            depth_in = q["d"] - PANEL - 0.2
            wants = q["insides"] or insides.default_drawers(q["stock"], n, q["m"].name)
            for j in range(n):
                op, floor, inside = drawer_model(k, q["m"], w, fa, fb, fy0 + j * hs, fy0 + (j + 1) * hs, d, depth_in,
                                                 q["color"], owner=q["owner"])
                insides.fill_drawer(k, op, floor, inside, wants[j] if j < len(wants) else None, w, q["stock"])
