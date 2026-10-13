"""The shell: the yard's ground and walls, the gate with its timers and Barrier, the safe-zone
line, and the corridor's ground, walls, caps, border strips, AreaSigns and Zones.

Ground and wall parts are big, solid, studded and carry Checker = 4."""
import math

import numpy as np

import spsgeo as G
from spsgeo import CF

from . import layout as L
from . import palette as PAL
from . import props as P
from .geo import bevel_box, ccyl
from .kit import darker, facing, lighter

GROUND_T = 2.0
SIGN_W, SIGN_H, SIGN_Y = 16.0, 9.0, 8.0


def yard_shell(k, f):
    c = PAL.YARD
    y0, y1 = -GROUND_T, 0.0
    a0, a1 = L.AVENUE_X
    x0, x1 = L.YARD_X
    z0, z1 = L.YARD_Z
    k.solid_box(f, "Ground", (x0, y0, z0), (a0, y1, z1), c["ground"], checker=True)
    k.solid_box(f, "Avenue", (a0, y0, z0), (a1, y1, z1), c["avenue"], checker=True)
    k.solid_box(f, "Ground", (a1, y0, z0), (x1, y1, z1), c["ground"], checker=True)
    T = L.WALL_T
    H = L.WALL_H
    walls = [((x0 - T, 0, z0 - T), (x0, H, z1 + T)),                  # west
             ((x1, 0, z0 - T), (x1 + T, H, z1 + T)),                  # east
             ((x0, 0, z1), (x1, H, z1 + T)),                          # south
             ((x0, 0, z0 - T), (L.GATE_X[0] - L.PILLAR, H, z0)),      # north, west of the gate
             ((L.GATE_X[1] + L.PILLAR, 0, z0 - T), (x1, H, z0))]      # north, east of the gate
    for lo, hi in walls:
        k.solid_box(f, "Wall", lo, hi, c["wall"], checker=True, studs=False)
        k.solid_box(f, "WallCap", (lo[0], H, lo[2]), (hi[0], H + L.CAP_H, hi[2]), c["cap"])


def gate(k, root, markers):
    """Pillars, the beam, TimerSouth / TimerNorth on it (frame and bulbs), the Barrier, the red
    safe-zone line with its LineBoard, and the SafeLine marker."""
    g = k.sc.model(root, "Gate")
    c = PAL.YARD
    H = L.WALL_H
    gx0, gx1 = L.GATE_X
    s = L.PILLAR / 2
    for sx in (-1, 1):
        cx = sx * (gx1 + s)
        k.solid_box(g, "Pillar", (cx - s, 0, -s), (cx + s, H, s), c["wall"], checker=True, studs=False)
        k.solid_box(g, "PillarCap", (cx - s - 0.5, H, -s - 0.5), (cx + s + 0.5, H + L.CAP_H, s + 0.5), c["cap"])
        # a big toy potato sitting on each pillar
        pg, eg = P.potato_geo(9.0, 6.0, 5.0)
        fr = CF((cx, H + L.CAP_H, 0.0), G.ry(90 + sx * 20))
        k.mesh(g, "PillarPotato", "Gate_PillarPotato", pg, fr, P.POTATO, solid=False)
        k.mesh(g, "PillarPotatoEyes", "Gate_PillarPotatoEyes", eg, fr, P.POTATO_DARK)
    b0, b1 = L.BEAM
    k.solid_box(g, "Beam", (gx0, b0, -s), (gx1, b1, s), c["wall"], checker=True, studs=False)
    k.solid_box(g, "BeamCap", (gx0 - s, b1, -s - 0.5), (gx1 + s, b1 + L.CAP_H, s + 0.5), c["cap"])
    # the two timer panels, a chunky frame round each and a row of bulbs over it
    W, Hh, y = L.TIMER_W, L.TIMER_H, L.TIMER_Y
    frame_col = (40, 46, 70)
    bulbs = (255, 220, 90)
    for name, face_z, d in (("TimerSouth", s, 1.0), ("TimerNorth", -s, -1.0)):
        cf_ = CF((0.0, y + Hh / 2, face_z + d * 0.5), facing(0.0, d))
        k.deco(g, name, (W, Hh, 0.6), cf_, (24, 26, 36), material="SmoothPlastic", studs=False)
        fr = G.Geo()
        t = 1.4
        for (fx, fy, fw, fh) in ((0, Hh / 2 + t / 2, W + 2 * t, t), (0, -Hh / 2 - t / 2, W + 2 * t, t),
                                 (W / 2 + t / 2, 0, t, Hh), (-W / 2 - t / 2, 0, t, Hh)):
            fr.add(bevel_box(fw, fh, 1.4, 0.25, (fx, fy, 0)))
        k.mesh(g, name + "Frame", "Gate_TimerFrame", fr, CF((0.0, y + Hh / 2, face_z + d * 0.6), facing(0.0, d)),
               frame_col)
        bl = G.Geo()
        n = 15
        for i in range(n):
            bl.add(ccyl(0.45, 0.6, 8, "z", (-W / 2 + W * i / (n - 1), Hh / 2 + t / 2, -0.75), 0.1))
        bp = k.mesh(g, name + "Bulbs", "Gate_TimerBulbs", bl, CF((0.0, y + Hh / 2, face_z + d * 0.6),
                                                                  facing(0.0, d)), bulbs, material="Neon")
        k.attr(bp, "Flicker", 0.2)
    # the Barrier: off by day (the game colours it and switches it on at night)
    k.sc.part(g, "Barrier", (gx1 - gx0, L.GATE_CLEAR, 1.0), CF((0.0, L.GATE_CLEAR / 2, L.BARRIER_Z)), (120, 200, 255),
              material="SmoothPlastic", transparency=1.0, collide=False, touch=False,
              query=False, shadow=False, grid=False, surfaces="smooth")
    # the red line and its LineBoard (lying on the ground just inside the yard)
    k.deco(g, "RedLine", (gx1 - gx0, 0.2, L.LINE_W), CF((0.0, 0.02, 0.0)), (232, 40, 40), studs=False)
    # LineBoard lies on the ground face up: its Front face (-Z) looks at the sky and its top edge
    # (+Y) points north, so text on the Front face reads right way up for someone walking north
    R_up = np.array(((-1.0, 0.0, 0.0), (0.0, 0.0, -1.0), (0.0, -1.0, 0.0)))
    k.deco(g, "LineBoard", (20.0, 3.0, 0.2), CF((0.0, 0.03, 3.6), R_up), (232, 40, 40), studs=False,
           material="SmoothPlastic")
    k.marker(markers, "SafeLine", CF((0.0, 0.0, 0.0), facing(0.0, -1.0)))
    return g


def fields_shell(k, fields, markers):
    """Ground, side walls and caps per area, the back wall, border strips, AreaSigns, Zones."""
    T = L.WALL_T
    H = L.WALL_H
    x0, x1 = L.FIELD_X
    out = {}
    for n in range(1, L.N_AREAS + 1):
        c = PAL.AREA[n]
        zs, zn = L.area_z(n)
        af = k.sc.folder(fields, "Area%d" % n)
        k.solid_box(af, "Ground", (x0, -GROUND_T, zn), (x1, 0.0, zs), c["ground"], checker=True)
        ws = zs if n > 1 else -L.PILLAR / 2           # area 1's walls start behind the gate pillars
        for sx in (-1, 1):
            wx0, wx1 = (x0 - T, x0) if sx < 0 else (x1, x1 + T)
            k.solid_box(af, "Wall", (wx0, 0.0, zn), (wx1, H, ws), c["wall"], checker=True, studs=False)
            k.solid_box(af, "WallCap", (wx0, H, zn), (wx1, H + L.CAP_H, ws), c["cap"])
        if n == L.N_AREAS:
            k.solid_box(af, "BackWall", (x0 - T, 0.0, zn - T), (x1 + T, H, zn), c["wall"], checker=True, studs=False)
            k.solid_box(af, "BackWallCap", (x0 - T, H, zn - T), (x1 + T, H + L.CAP_H, zn), c["cap"])
        if n > 1:
            k.deco(af, "Border", (x1 - x0, 0.2, 2.0), CF((0.0, 0.02, zs)), PAL.AREA[n]["border"], studs=False)
        am = k.sc.folder(markers, "Area%d" % n)
        zone = k.sc.part(am, "Zone", (x1 - x0, 60.0, L.AREA_LEN), CF((0.0, 30.0, (zs + zn) / 2)), (255, 255, 255),
                         material="SmoothPlastic", transparency=1.0, collide=False, touch=False, query=False,
                         shadow=False, grid=False, surfaces="smooth")
        k.attr(zone, "Area", n)
        k.attr(zone, "AreaName", L.AREAS[n - 1])
        area_sign(k, am, n, zs - (4.0 if n > 1 else 10.0))
        out[n] = (af, am)
    return out


def area_sign(k, parent, n, z):
    """Model AreaSign on the west side: two posts, a frame and a little roof round the Board
    (16 x 9, bottom edge at Y 8, front face south)."""
    m = k.sc.model(parent, "AreaSign")
    m.p["primary"] = None
    c = PAL.AREA[n]
    xc = L.FIELD_X[0] + 14.0
    post = darker(c["wall"], 0.7)
    trim = lighter(c["wall"], 0.15)
    g = G.Geo()
    for dx in (-SIGN_W / 2 + 1.0, SIGN_W / 2 - 1.0):
        g.add(bevel_box(1.2, SIGN_Y + SIGN_H + 1.0, 1.2, 0.2, (dx, (SIGN_Y + SIGN_H + 1.0) / 2, -1.0)))
    k.mesh(m, "Posts", "AreaSign_Posts", g, CF((xc, 0.0, z)), post)
    fr = G.Geo()
    t = 0.8
    for (fx, fy, fw, fh) in ((0, SIGN_H / 2 + t / 2, SIGN_W + 2 * t, t), (0, -SIGN_H / 2 - t / 2, SIGN_W + 2 * t, t),
                             (SIGN_W / 2 + t / 2, 0, t, SIGN_H), (-SIGN_W / 2 - t / 2, 0, t, SIGN_H)):
        fr.add(bevel_box(fw, fh, 1.0, 0.2, (fx, fy, 0)))
    roof = G.Geo()
    roof.add(bevel_box(SIGN_W + 3.0, 0.8, 3.0, 0.2, (0, SIGN_H / 2 + t + 0.6, 0.3)))
    roof.add(bevel_box(SIGN_W + 1.6, 0.8, 2.0, 0.2, (0, SIGN_H / 2 + t + 1.4, 0.3)))
    fcf = CF((xc, SIGN_Y + SIGN_H / 2, z), facing(0.0, 1.0))
    k.mesh(m, "Frame", "AreaSign_Frame", fr, fcf, trim)
    k.mesh(m, "Roof", "AreaSign_Roof", roof, fcf, darker(c["wall"], 0.85))
    bd = k.board(m, SIGN_W, SIGN_H, fcf, color=(250, 248, 236))
    m.p["primary"] = bd
    k.attr(m, "Area", n)
    return m
