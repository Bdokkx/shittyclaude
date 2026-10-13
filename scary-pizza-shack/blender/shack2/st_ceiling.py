"""The ceiling: CeilingLamp1/2 and the Hatch (stations, as batch 1), the slow fan, the work
lamps where the work is (fluorescents over the prep line and the window, pendants over the
till and the cut table, caged lamps over the sink and the back door), and the steel conduit
that feeds them all from the fuse box, clipped along the beams."""
import math

import numpy as np

import spsgeo as G
from spsgeo import CF

from . import interior as IP, layout as L
from .kit import bevel_box, ccyl, rod
from .st_common import (N, S_, cage_lamp, moving, pendant_lamp, pivot, spot, stand, station, tube_lamp, weld_all)

CY = L.CEIL           # 9.4, the ceiling panels' underside


def ceiling_lamp(k, name, x, z):
    """An enamel pendant on a long cord: the Cord is the anchored root (pivot on the ceiling
    hook), Shade and Bulb welded to it so the whole lamp can sway."""
    m = station(k, name)
    drop = 2.2
    cord = G.Geo()
    cord.add(rod((0, 0, 0), (0, -(drop - 0.45), 0), 0.08, 6))
    cord.add(ccyl(0.32, 0.2, 10, "y", (0, -0.1, 0), 0.04))
    c = k.mesh(m, "Cord", "CeilingLamp__Cord", cord, CF((x, CY, z)), "black", shadow=False)
    sh = G.outward(G.lathe_loop([(0.0, 0.45), (0.22, 0.45), (0.3, 0.3), (1.0, -0.3), (1.0, -0.42), (0.86, -0.34),
                                 (0.2, 0.2), (0.0, 0.25)], 12))
    s = k.mesh(m, "Shade", "CeilingLamp__Shade", sh, CF((x, CY - drop + 0.3, z)), "shade_green")
    si = k.mesh(m, "ShadeInside", "CeilingLamp__ShadeIn",
                G.outward(G.lathe([(0.0, 0.2), (0.25, 0.18), (0.86, -0.32), (0.0, -0.1)], 12)),
                CF((x, CY - drop + 0.3, z)), "cream", shadow=False)
    b = k.part(m, "Bulb", (0.6, 0.6, 0.6), CF((x, CY - drop + 0.05, z)), (255, 222, 170), material="Neon",
               shape="Ball", grid=False, shadow=False)
    weld_all(k, c, [s, si, b])
    pivot(c, CF((x, CY, z)))
    moving(m, "Cord", "optional sway: the Cord is the anchored root (pivot on the ceiling hook); Shade and Bulb are "
                      "welded to it, so tilting the pivot a few degrees swings the whole lamp")
    k.lamp(m, b, IP.CIRCUIT.get(name, "Shack"), "Spot", 16.0, 1.0, (255, 196, 132), angle=120.0, on_model=False)
    k.attr(m, "Sway", 3.0)
    stand(k, m, x, z + 1.5, N)
    k.mark_used("CeilingLampPendant")
    return m


def hatch(k):
    """The attic hatch: a frame round the hole, the Door hinged along its north edge (it
    swings down into the room), a pull cord with a wooden toggle hanging from it."""
    m = station(k, "Hatch")
    hx0, hx1, hz0, hz1 = IP.HATCH
    door = k.box(m, "Door", (hx0, CY, hz0), (hx1, L.CEIL_TOP, hz1), "wood_light", solid=True)
    ring = G.Geo()
    ring.add(G.torus(0.22, 0.075, 10, 4, "z", (0, -0.32, 0)))
    ring.add(bevel_box(0.2, 0.15, 0.2, 0.03, c=(0, -0.075, 0)))
    rp = k.mesh(m, "PullRing", "Hatch__Ring", ring, CF(((hx0 + hx1) / 2, CY, hz1 - 0.6)), "steel_dark", shadow=False)
    cord = rod((0, -0.5, 0), (0, -2.6, 0), 0.075, 4)
    cp = k.mesh(m, "PullCord", "Hatch__Cord", cord, CF(((hx0 + hx1) / 2, CY, hz1 - 0.6)), "jute", shadow=False)
    tog = k.mesh(m, "Toggle", "Hatch__Toggle", ccyl(0.16, 0.6, 8, "y", (0, 0, 0), 0.05),
                 CF(((hx0 + hx1) / 2, CY - 2.9, hz1 - 0.6)), "wood", shadow=False)
    # an openable Model "Door": hinged along its north edge, +90 about X swings it down into the
    # room (the attic is above it); the panel is its Leaf, the pull cord and toggle ride with it
    from .opens import adopt
    door.name = "Leaf"
    pivot(door, CF(((hx0 + hx1) / 2, CY, hz0)))
    adopt(k, m, "Door", door, [rp, cp, tog], "Swing", "Lid", angle=90.0, axis="X", label="Pull")
    fr = G.Geo()
    w, d = hx1 - hx0, hz1 - hz0
    for (cx, cz, sx, sz) in ((0, -d / 2 - 0.25, w + 1.0, 0.5), (0, d / 2 + 0.25, w + 1.0, 0.5),
                             (-w / 2 - 0.25, 0, 0.5, d), (w / 2 + 0.25, 0, 0.5, d)):
        fr.add(bevel_box(sx, 0.3, sz, 0.06, c=(cx, -0.15, cz)))
    k.mesh(m, "Frame", "Hatch__Frame", fr, CF(((hx0 + hx1) / 2, CY, (hz0 + hz1) / 2)), "wood_dark", solid=True)
    stand(k, m, (hx0 + hx1) / 2, hz1 + 1.6, N)
    return m


def fan(k, parent):
    """A slow ceiling fan: rose, downrod, motor, four wooden blades (Spin)."""
    m = k.sc.model(parent, "CeilingFan")
    x, z = IP.FAN
    k.mesh(m, "Rose", "Fan__Rose", ccyl(0.35, 0.3, 10, "y", (0, -0.15, 0), 0.05), CF((x, CY, z)), "cream_dark",
           shadow=False)
    k.mesh(m, "Rod", "Fan__Rod", rod((0, -0.3, 0), (0, -1.1, 0), 0.1, 6), CF((x, CY, z)), "cream_dark", shadow=False)
    hub = k.mesh(m, "Hub", "Fan__Motor", G.outward(G.lathe([(0, 0.25), (0.45, 0.2), (0.55, 0.0), (0.45, -0.2),
                                                             (0.0, -0.25)], 12)), CF((x, CY - 1.35, z)), "cream_dark",
                 solid=False)
    bl = G.Geo()
    for i in range(4):
        a = 90 * i + 12
        blade = bevel_box(IP.FAN_R - 0.4, 0.15, 0.75, 0.05, c=((IP.FAN_R - 0.4) / 2 + 0.45, 0, 0))
        blade = blade.xf(G.M(G.rx(8)))
        bl.add(blade.xf(G.M(G.ry(a))))
        bl.add(bevel_box(0.5, 0.15, 0.2, 0.03, c=(0.45, 0.05, 0)).xf(G.M(G.ry(a))))
    blades = k.mesh(m, "Blades", "Fan__Blades", bl, CF((x, CY - 1.55, z)), "wood", solid=False)
    weld_all(k, hub, [blades])
    pivot(hub, CF((x, CY - 1.35, z)))
    k.attr(hub, "Spin", 120.0)                   # degrees a second about the Hub's own Y (up): slow
    # the pull chain from the switch housing under the motor, on the axis (inside the blades'
    # roots): a Model the player pulls (Pull = true); the game toggles the fan
    pc = k.sc.model(m, "PullChain")
    k.attr(pc, "Pull", True)
    ch = G.Geo()
    ch.add(rod((0, 0, 0), (0, -1.3, 0), 0.075, 4))
    k.mesh(pc, "Chain", "Fan__Chain", ch, CF((x, CY - 1.6, z)), "brass", shadow=False)
    bob = k.mesh(pc, "Bob", "Fan__ChainBob", G.sphere(0.16, 8, 5, (1.0, 1.4, 1.0)), CF((x, CY - 3.0, z)), "wood_light",
                 shadow=False)
    pc.p["primary"] = bob
    pivot(bob, CF((x, CY - 1.6, z)))
    k.mark_used("CeilingFan")
    return m


def work_lamps(k, parent):
    for name, (x, z, kind) in IP.WORK_LAMPS.items():
        grp = IP.CIRCUIT.get(name, "Shack")
        if kind == "tube":
            tube_lamp(k, parent, name, x, z, length=4.0, flicker=0.25 if name == "PrepLamp3" else 0.0, group=grp)
        elif kind == "pendant":
            pendant_lamp(k, parent, name, x, z, drop=2.4, group=grp)
        elif kind == "cage":
            cage_lamp(k, parent, name, (x, CY - 0.55, z), wall=(0, -1, 0), group=grp)


def conduit(k, parent):
    """Steel conduit from the fuse box's corner: one run along the north wall under the beam
    ends, one along the south wall, and a drop up each bay to every lamp, clipped as it goes."""
    g = G.Geo()
    clips = G.Geo()
    y_wall = 8.4                                          # the wall runs: under the beam ends, over the tall things
    y_bay = CY - 0.3                                      # the bay runs: just under the T-bars
    r = 0.1
    zn, zs = L.IN_Z0 + 0.75, L.IN_Z1 - 0.75
    xw = L.IN_X0 + 0.55
    for zr in (zn, zs):
        g.add(rod((xw, y_wall, zr), (12.0, y_wall, zr), r, 6))
        for x in np.arange(xw + 1.0, 12.0, 3.0):
            clips.add(bevel_box(0.3, 0.3, 0.3, 0.05, c=(x, y_wall, zr)))
    g.add(rod((xw, y_wall, zn), (xw, y_wall, zs), r, 6))
    lamps = [(x, z, kind) for (x, z, kind) in IP.WORK_LAMPS.values()] + \
            [(x, z, "pendant") for (x, z) in IP.CEILING_LAMPS.values()]
    for (x, z, kind) in lamps:
        if x > 12.0:
            continue                                      # the hood corner is fed from the oven side
        zr = zn if z < 0 else zs
        stop = z - math.copysign(0.45 if kind == "tube" else 0.4, z - zr)
        xc = x + 0.6 if kind == "tube" else x
        g.add(rod((xc, y_wall, zr), (xc, y_bay, zr), r, 6))
        g.add(rod((xc, y_bay, zr), (xc, y_bay, stop), r, 6))
        for zz in np.arange(min(zr, stop) + 1.5, max(zr, stop), 2.5):
            clips.add(bevel_box(0.3, 0.15, 0.3, 0.04, c=(xc, y_bay + 0.15, zz)))
    k.mesh(parent, "Conduit", "Ceiling__Conduit", g, CF(), "steel_dark", shadow=False)
    k.mesh(parent, "ConduitClips", "Ceiling__Clips", clips, CF(), "charcoal", shadow=False)


def build(k):
    st = [ceiling_lamp(k, n, x, z) for n, (x, z) in IP.CEILING_LAMPS.items()]
    st.append(hatch(k))
    f = k.sc.folder(k.sc.root.get("Shack"), "Fixtures")
    fan(k, f)
    work_lamps(k, f)
    conduit(k, f)
    return st
