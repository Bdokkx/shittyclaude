"""Shared station helpers: the station Model, Stand and item markers (as batch 1: -Z is the
facing, the position lies on the surface), pivots and welds for moving pieces, text Boards,
and the lamp fixtures (Models holding a Bulb with Lamp* attributes, no Light objects)."""
import math

import numpy as np

import spsgeo as G
from spsgeo import CF

from . import layout as L
from .kit import bevel_box, ccyl, cfrustum, col, lathe, rod

N, S_, E, W = (0, 0, -1), (0, 0, 1), (1, 0, 0), (-1, 0, 0)
MOVING = []          # (model, part, how it moves) for the README


def station(k, name):
    return k.sc.model(k.sc.root.get("Stations"), name)


def stand(k, m, x, z, d, name="Stand", y=None):
    return k.sc.marker(m, name, CF((x, L.FLOOR if y is None else y, z), G.facing(d)))


def spot(k, m, name, x, y, z, d):
    return k.sc.marker(m, name, CF((x, y, z), G.facing(d)))


def pivot(node, world_cf):
    node.p["pivot"] = node.p["cf"].inv() * world_cf


def moving(m, part, how):
    MOVING.append((m.name if hasattr(m, "name") else m, part, how))


def weld_all(k, root, parts):
    for p in parts:
        p.p["anchored"] = False
        p.p["massless"] = True
        k.sc.weld(root, p, "Weld")


def board(k, parent, size, cf_, color, text="", text_color=(30, 30, 30), name="Board", font="Arcade", **kw):
    """A flat part named Board for a piece of text (the game puts a SurfaceGui on its Front
    face, -Z). The text it should carry is in the attributes BoardText / BoardTextColor /
    BoardFont. A name other than Board makes a small Model of that name holding the Board, so
    every text part is called Board and a station's own work Board stays its only direct one."""
    if name != "Board":
        parent = k.sc.model(parent, name)
    b = k.part(parent, "Board", size, cf_, color, material="SmoothPlastic", grid=False, shadow=False, **kw)
    if text:
        k.attr(b, "BoardText", text)
        k.attr(b, "BoardTextColor", "%d,%d,%d" % tuple(col(text_color)))
        k.attr(b, "BoardFont", font)
    return b


def wall_board(k, parent, w, u, y, size, color, d=None, **kw):
    """A Board on wall w at (u, y), its Front face towards the room; size = (width, height)."""
    from . import counters as C
    d = 0.075 if d is None else d
    R = G.facing(C.facing_room(w))
    return board(k, parent, (size[0], size[1], 0.15), CF(C.wpt(w, u, y, d), R), color, **kw)


FACE = {"N": G.facing((0, 0, 1)), "S": G.facing((0, 0, -1)), "W": G.facing((1, 0, 0)), "E": G.facing((-1, 0, 0))}


# ---------------------------------------------------------------- lamp fixtures

WARM = (255, 196, 132)


def _lamp_model(k, parent, name):
    return k.sc.model(parent, name)


def tube_lamp(k, parent, name, x, z, length=4.0, along="x", y_top=None, group="Shack", bright=1.0, rng=16.0,
              flicker=0.0):
    """A fluorescent fitting under the ceiling: a cream steel box with end caps, the tube (Bulb)
    in a clear diffuser underneath; warm spot pointing down."""
    y_top = L.CEIL if y_top is None else y_top
    m = _lamp_model(k, parent, name)
    R = np.eye(3) if along == "x" else G.ry(90)
    body = G.Geo()
    body.add(bevel_box(length, 0.4, 0.9, 0.08, c=(0, -0.2, 0)))
    for sx in (-1, 1):
        body.add(bevel_box(0.3, 0.3, 0.8, 0.06, c=(sx * (length / 2 - 0.15), -0.55, 0)))
    k.mesh(m, "Housing", "Lamp__TubeHousing%d" % int(length * 10), body, CF((x, y_top, z), R), "cream_dark")
    bulb = k.part(m, "Bulb", (length - 0.6, 0.3, 0.3), CF((x, y_top - 0.55, z), R @ G.rz(90) @ G.rz(-90)),
                  (255, 236, 200), material="Neon", shape="Cylinder", grid=False, shadow=False)
    k.part(m, "Diffuser", (length - 0.6, 0.15, 0.7), CF((x, y_top - 0.8, z), R), "glass", material="Glass",
           transparency=0.55, grid=False, shadow=False)
    k.lamp(m, bulb, group, "Spot", rng, bright, WARM, angle=120.0, flicker=flicker)
    k.mark_used("TubeLamp")
    return m


def pendant_lamp(k, parent, name, x, z, drop=1.6, y_top=None, group="Shack", bright=1.0, rng=14.0, shade="shade_green",
                 flicker=0.0):
    """An enamel pendant: ceiling rose, cord, green shade with a white inside, bulb."""
    y_top = L.CEIL if y_top is None else y_top
    m = _lamp_model(k, parent, name)
    yb = y_top - drop
    k.mesh(m, "Rose", "Lamp__Rose", ccyl(0.35, 0.2, 10), CF((x, y_top - 0.1, z)), "cream_dark", shadow=False)
    k.mesh(m, "Cord", "Lamp__Cord%d" % int(drop * 10), rod((0, 0, 0), (0, -(drop - 0.5), 0), 0.08, 6),
           CF((x, y_top - 0.2, z)), "black", shadow=False)
    sh = G.outward(G.lathe_loop([(0.0, 0.45), (0.22, 0.45), (0.3, 0.3), (0.95, -0.25), (0.95, -0.38), (0.82, -0.3),
                                 (0.2, 0.2), (0.0, 0.25)], 12))
    k.mesh(m, "Shade", "Lamp__Shade", sh, CF((x, yb + 0.25, z)), shade)
    k.mesh(m, "ShadeInside", "Lamp__ShadeIn", G.outward(lathe([(0.0, 0.2), (0.25, 0.18), (0.82, -0.28),
                                                                 (0.0, -0.1)], 12)), CF((x, yb + 0.25, z)), "cream",
           shadow=False)
    bulb = k.part(m, "Bulb", (0.5, 0.5, 0.5), CF((x, yb, z)), (255, 222, 170), material="Neon", shape="Ball",
                  grid=False, shadow=False)
    k.lamp(m, bulb, group, "Spot", rng, bright, WARM, angle=110.0, flicker=flicker)
    k.mark_used("PendantLamp")
    return m


def cage_lamp(k, parent, name, pos, normal=(0, -1, 0), group="Shack", bright=0.9, rng=12.0, wall=None, flicker=0.0):
    """A bulkhead lamp in a wire cage on a wall plate (wall = the direction from the wall into
    the room); points down."""
    m = _lamp_model(k, parent, name)
    x, y, z = pos
    d = np.asarray(wall if wall is not None else (0, 0, 1), float)
    if abs(d[1]) > 0.9:                      # on the ceiling: +Z down (or up)
        R = G.rx(90.0 if d[1] < 0 else -90.0)
    else:
        R = G.facing(-d)                     # local -Z towards the wall -> +Z into the room
    k.mesh(m, "Plate", "Lamp__CagePlate", bevel_box(0.9, 0.9, 0.2, 0.05), CF((x, y, z), R) * CF((0, 0, -0.45)),
           "charcoal")
    cage = G.Geo()
    for a in range(6):
        t = math.tau * a / 6
        cage.add(rod((0.32 * math.cos(t), 0.32 * math.sin(t), -0.35), (0.32 * math.cos(t), 0.32 * math.sin(t), 0.25),
                     0.075, 4))
    cage.add(G.torus(0.33, 0.075, 12, 4, "z", (0, 0, 0.25)))
    k.mesh(m, "Cage", "Lamp__Cage", cage, CF((x, y, z), R), "charcoal", shadow=False)
    bulb = k.part(m, "Bulb", (0.45, 0.45, 0.45), CF((x, y, z)), (255, 222, 170), material="Neon", shape="Ball",
                  grid=False, shadow=False)
    k.lamp(m, bulb, group, "Spot", rng, bright, WARM, angle=130.0, flicker=flicker)
    k.mark_used("CageLamp")
    return m
