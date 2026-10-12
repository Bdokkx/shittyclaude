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

def counter(k, m, w, u0, u1, depth, top="steel", door="red", fronts=None, ajar=(), body_col="cab_inside",
            end_left=True, end_right=True, owner="Counter", plinth=True, top_y=None, top_name="Top", shelf=None,
            open_sides=True, top_hole=None):
    """A cabinet run on wall w from u0 to u1, `depth` deep, worktop at 3.4 running to the wall.
    fronts: [(width, kind)] along u covering u0..u1, kind in 'doors2', 'door', 'drawers',
    'drawers3', 'open'; defaults to pairs of doors 2 wide. ajar: indices of doors left ajar.
    shelf: {section index: y} adds a shelf in an open bay. Returns the worktop part.
    The carcass is dark (gaps between fronts read as shadow lines); an open bay is hollow (a
    dark back, floor and sides) for the station to fill."""
    top_y = top_y or L.WORK
    D = depth
    y_body = top_y - 0.4                       # carcass top = worktop underside
    fronts = fronts or _default_fronts(u1 - u0)
    assert abs(sum(wd for wd, _ in fronts) - (u1 - u0)) < 1e-6, (owner, fronts, u0, u1)
    if plinth:
        wbox(k, m, "Plinth", w, u0, u1, 0.2, 0.6, 0.0, D - 1.0, "black", solid=True)
    tmat = "Metal" if top.startswith("steel") else "Plastic"      # stainless tops read as brushed steel
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
           wcf(w, (u0 + u1) / 2, top_y - 0.2, D), "steel_dark", shadow=False, material="Metal")
    u = u0
    di = 0
    fy0, fy1 = 0.7, y_body - 0.1
    sections = []
    for si, (wd, kind) in enumerate(fronts):
        a, b = u, u + wd
        sections.append((a, b, kind))
        ia = a + (0.4 if (end_left and abs(a - u0) < 1e-6) else 0.0)
        ib = b - (0.4 if (end_right and abs(b - u1) < 1e-6) else 0.0)
        if kind == "open":
            _bay(k, m, w, a, b, 0.6, y_body, D - 0.6, body_col, owner, shelf_y=(shelf or {}).get(si),
                 side_a=open_sides and (abs(a - u0) > 1e-6 or not end_left),
                 side_b=open_sides and (abs(b - u1) > 1e-6 or not end_right))
        else:
            k.mesh(m, "Carcass", "%s__Carcass%dx%d" % (owner, int(round(wd * 10)), int(round(D * 10))),
                   bevel_box(wd, y_body - 0.6, D - 0.6, 0.03), wcf(w, (a + b) / 2, (0.6 + y_body) / 2, (D - 0.6) / 2),
                   body_col, solid=True)
        if kind in ("doors2", "door"):
            n = 2 if kind == "doors2" else 1
            dw = (ib - ia) / n
            for j in range(n):
                hinge_left = (j == 0) if n == 2 else True
                _door(k, m, w, ia + j * dw, ia + (j + 1) * dw, fy0, fy1, D - 0.6, door, hinge_left,
                      ajar=di in ajar, owner=owner)
                di += 1
        elif kind in ("drawers", "drawers3"):
            n = 2 if kind == "drawers" else 3
            hs = (fy1 - fy0) / n
            for j in range(n):
                _drawer(k, m, w, ia, ib, fy0 + j * hs, fy0 + (j + 1) * hs, D - 0.6, door, owner=owner)
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


def _door(k, m, w, a, b, y0, y1, d, color, hinge_left, ajar=False, owner="Counter"):
    """A shaker door between u = a..b (a 0.06 gap all round), its back on the carcass face at
    d; a vertical bar pull by the opening edge, two hinges on the hinge edge. An ajar door is
    swung 28 degrees into the room about its hinge."""
    gap = 0.06
    wd, ht = (b - a) - 2 * gap, (y1 - y0) - 2 * gap
    uc, yc = (a + b) / 2, (y0 + y1) / 2
    s = sgn(w)
    hu = a + gap if hinge_left else b - gap            # hinge edge, in u
    x_free = (uc - hu) * s                             # door centre from the hinge, in the wall frame
    if ajar:
        frame = wcf(w, hu, yc, d) * CF(R=G.ry(-28.0 * (1 if x_free > 0 else -1))) * CF((x_free, 0.0, 0.0))
    else:
        frame = wcf(w, uc, yc, d)
    name = "%s__Door%dx%d" % (owner, int(round(wd * 100)), int(round(ht * 100)))
    dr = k.mesh(m, "CabinetDoor", name, door_geo(round(wd, 2), round(ht, 2)), frame, color)
    pu = (b - gap - 0.35) if hinge_left else (a + gap + 0.35)
    k.mesh(m, "Pull", "Counter__Pull", pull_geo(0.6), frame * CF(((pu - uc) * s, ht / 2 - 0.55, 0.2)) * CF(R=G.rz(90)),
           "steel_light", shadow=False)
    for dy in (ht / 2 - 0.45, -ht / 2 + 0.45):
        k.mesh(m, "Hinge", "Counter__Hinge", hinge_geo(), frame * CF((-x_free + 0.06 * (1 if x_free > 0 else -1), dy,
                                                                        0.075)), "charcoal", shadow=False)
    return dr


def _drawer(k, m, w, a, b, y0, y1, d, color, owner="Counter"):
    gap = 0.06
    wd, ht = (b - a) - 2 * gap, (y1 - y0) - 2 * gap
    uc, yc = (a + b) / 2, (y0 + y1) / 2
    geo = door_geo(round(wd, 2), round(ht, 2), frame=0.2)
    name = "%s__Drawer%dx%d" % (owner, int(round(wd * 100)), int(round(ht * 100)))
    dr = _place(k, m, "DrawerFront", name, geo, w, uc, yc, d, color)
    pl = round(min(1.2, wd - 0.6), 1)
    k.mesh(m, "Pull", "Counter__Pull%d" % int(pl * 10), pull_geo(pl), wcf(w, uc, yc + ht / 2 - 0.3, d + 0.2),
           "steel_light", shadow=False)
    return dr
