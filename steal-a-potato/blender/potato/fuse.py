"""PotatoKit.FuseMachine: three potatoes go in, one better potato comes out.

A chunky blue machine about 28 wide, 20 deep and 22 tall on a grey stone step, front -Z:
  * the body: a planked blue cabinet with lighter corner pillars, a dark skirt, rivets and vents
  * Screen: a big lit white screen (Neon) in a dark bezel on the front ("?" goes there)
  * a panel on the right of the screen: a lever with a red knob, a big red button, three red lights
  * a dark dome on top with a glowing cyan ring round its foot
  * a fat dark pipe that loops from the dome down into a control block on the left (dials, a vent)
  * an aerial with a red light on its tip
  * three round sockets on the step in front, glowing cyan, where the potatoes sit
  * Board: the dark sign over the top (22 x 5) for FUSE MACHINE
  * Prompt: invisible, in front of the step at a player's chest height
Big pieces (the step, the cabinet, the control block, the dome) are solid; trim is decoration.
Pivot: middle of the footprint on the ground.
"""
import math

import numpy as np

import spsgeo as G
from spsgeo import CF

from .bricks import Bricks, ori, shade

BLUE = ("3e6fd6", "2f57b0", "5a8cf0", "1e3a80")
DARK = ("2b2b3a", "3c3c50", "1d1d28")
STONE = ("8e89a0", "a3a0b5", "7c788c", "b9b4c8")
CYAN = "4ff0ff"
RED = ("e8403a", "ff3b3b", "b52a26")
SCREEN = "f4fbff"


def build(sc, parent, base=None):
    base = base or CF()
    deco = Bricks(sc, base, anchored=True, collide=False, touch=False, query=False)
    solid = Bricks(sc, base, anchored=True, collide=True, touch=False, query=True)
    m = sc.model(parent, "FuseMachine")

    def d(name, size, pos, R=None, col="ffffff", material="Plastic", **kw):
        return deco.part(m, name, size, pos, R, col, material=material, **kw)

    def s_(name, size, pos, R=None, col="ffffff", material="Plastic", **kw):
        return solid.part(m, name, size, pos, R, col, material=material, **kw)

    # -------------------------------------------------------------- the stone step
    step = s_("Step", (28.0, 0.8, 20.0), (0, 0.4, 0), None, STONE[2])
    s_("Step", (27.0, 0.82, 19.0), (0, 1.19, 0), None, STONE[0])
    for x in (-13.5, 13.5):                                        # corner stones
        for z in (-9.5, 9.5):
            d("Stone", (1.6, 1.0, 1.6), (x * 0.985, 1.12, z * 0.98), G.ry(12 if x * z > 0 else -9), STONE[3])
    for i in range(10):                                            # hazard stripes along the front edge
        x = -11.7 + i * 2.6
        d("Stripe", (1.3, 0.12, 1.0), (x, 1.66, -8.95), G.ry(0), "ffd447" if i % 2 == 0 else "2b2b3a")

    # -------------------------------------------------------------- the cabinet
    y0, y1 = 1.6, 13.6
    zc, D = 1.5, 11.0                                              # front face at z = -4.0
    W = 18.0
    s_("Cabinet", (W, y1 - y0, D), (0, (y0 + y1) / 2, zc), None, BLUE[0])
    s_("Skirt", (W + 0.6, 1.2, D + 0.6), (0, y0 + 0.58, zc), None, BLUE[3])
    s_("TopTrim", (W + 0.8, 0.8, D + 0.8), (0, y1 - 0.38, zc), None, BLUE[1])
    for x in (-W / 2, W / 2):                                      # lighter corner pillars
        for z in (zc - D / 2, zc + D / 2):
            d("Pillar", (1.4, y1 - y0 - 1.0, 1.4), (x, (y0 + y1) / 2 + 0.1, z), None, BLUE[2])
    for x in (-5.0, 0.0, 5.0):                                     # planks up the sides
        for sd in (-1, 1):
            d("Plank", (0.5, y1 - y0 - 2.4, 0.3), (sd * (W / 2 + 0.16), (y0 + y1) / 2, zc + x * 0.8), G.ry(90),
              BLUE[1])
    for sd in (-1, 1):                                             # vents on both sides
        for k in range(3):
            d("Vent", (0.2, 0.32, 3.2), (sd * (W / 2 + 0.12), 10.0 + k * 0.7, zc + 2.8), None, DARK[2])
    # front face details: bezel and Screen, a panel with lever / button / lights, rivets
    fz = zc - D / 2                                                # -4.0
    d("Bezel", (10.4, 7.6, 0.6), (-2.2, 8.0, fz - 0.3), None, DARK[0])
    d("Bezel", (11.0, 0.6, 0.84), (-2.2, 12.05, fz - 0.4), None, DARK[1])
    scr = deco.part(m, "Screen", (9.2, 6.4, 0.2), (-2.2, 8.0, fz - 0.68), None, SCREEN, material="Neon",
                    shadow=False)
    d("Panel", (4.4, 7.6, 0.5), (6.0, 8.0, fz - 0.25), None, DARK[0])
    d("Panel", (3.8, 7.0, 0.1), (6.0, 8.0, fz - 0.55), None, DARK[1])
    for k in range(3):                                             # three red lights
        d("Light", (0.6, 0.6, 0.4), (4.9 + k * 1.1, 10.9, fz - 0.68), G.rz(45), RED[1], material="Neon")
    # the big red button: Folk Valley's round on a dark housing
    bx, by = 6.0, 8.6
    d("ButtonBase", (2.2, 2.2, 0.56), (bx, by, fz - 0.75), G.rz(45), DARK[2])
    d("Button", (1.9, 1.3, 0.5), (bx, by, fz - 1.1), None, RED[0])
    d("Button", (1.3, 1.9, 0.52), (bx, by, fz - 1.1), None, RED[0])
    d("Button", (1.7, 1.7, 0.54), (bx, by, fz - 1.1), G.rz(45), RED[2])
    d("Button", (0.9, 0.9, 0.2), (bx - 0.2, by + 0.2, fz - 1.42), G.rz(45), "ff8a80")
    # the lever
    d("LeverBase", (2.4, 0.9, 1.0), (6.0, 5.6, fz - 0.9), None, DARK[2])
    d("Lever", (0.32, 2.2, 0.32), (6.6, 6.55, fz - 1.25), G.rz(-28), "b9b4c8")
    d("LeverKnob", (0.8, 0.8, 0.8), (7.15, 7.5, fz - 1.25), ori(0, 45, 0), RED[0])
    for (x, y) in ((-8.3, 2.9), (8.3, 2.9), (-8.3, 12.4), (8.3, 12.4), (-2.2, 3.4)):
        d("Rivet", (0.4, 0.4, 0.2), (x, y, fz - 0.12), None, STONE[3])

    # -------------------------------------------------------------- the dome with its glowing ring
    dz, dy = zc + 0.5, y1
    s_("Dome", (8.0, 1.6, 6.4), (0, dy + 0.8, dz), None, DARK[0])
    s_("Dome", (6.4, 1.62, 8.0), (0, dy + 0.8, dz), None, DARK[0])
    s_("Dome", (7.4, 1.64, 7.4), (0, dy + 0.8, dz), G.ry(45), DARK[1])
    d("Dome", (5.6, 1.3, 4.4), (0, dy + 2.2, dz), None, DARK[0])
    d("Dome", (4.4, 1.32, 5.6), (0, dy + 2.2, dz), None, DARK[0])
    d("Dome", (5.0, 1.34, 5.0), (0, dy + 2.2, dz), G.ry(45), DARK[1])
    d("Dome", (3.0, 0.7, 3.0), (0, dy + 3.1, dz), G.ry(22), DARK[1])
    d("Dome", (1.2, 0.5, 1.2), (0, dy + 3.6, dz), G.ry(45), DARK[2])
    # the ring: eight Neon bars round the dome's foot (a regular octagon)
    a = 4.35                                                       # its apothem
    side = 2 * a * math.tan(math.radians(22.5))
    for i in range(8):
        R = G.ry(i * 45.0)
        d("Ring", (side + 0.32, 0.42 + 0.03 * (i % 2), 0.4), np.array((0, dy + 0.45, dz)) + R @ (0, 0, -a), R, CYAN,
          material="Neon")

    # -------------------------------------------------------------- the pipe: dome -> out left -> down -> control block
    cx = -13.2
    pcol, band = DARK[0], DARK[1]
    s_("Pipe", (1.5, 1.5, 1.5), (-3.9, dy + 1.4, dz), None, pcol)
    s_("Pipe", (7.6, 1.3, 1.3), (-7.9, dy + 1.4, dz), None, pcol)                      # out to the left
    s_("Pipe", (1.7, 1.7, 1.7), (-11.9, dy + 1.4, dz), G.rz(45), band)                 # the elbow
    s_("Pipe", (1.3, 4.4, 1.34), (-12.4, dy - 1.0, dz), G.rz(-12), pcol)               # and down
    for (x, y) in ((-6.0, dy + 1.4), (-9.6, dy + 1.4)):
        d("Collar", (0.5, 1.6, 1.6), (x, y, dz), None, band)
    d("Collar", (1.6, 0.5, 1.6), (-12.62, dy - 2.2, dz), G.rz(-12), band)

    # -------------------------------------------------------------- the control block on the left
    s_("Control", (4.6, 9.4, 5.6), (cx, 1.6 + 4.7, dz), None, BLUE[1])
    d("Control", (5.0, 0.6, 6.0), (cx, 1.6 + 9.4 + 0.25, dz), None, BLUE[3])
    d("Control", (5.0, 0.8, 6.0), (cx, 1.6 + 0.38, dz), None, BLUE[3])
    for k, (y, col) in enumerate(((8.8, "fff7ec"), (6.0, "fff7ec"))):                    # two dials
        d("Dial", (1.8, 1.8, 0.3), (cx, y, dz - 2.95), G.rz(45 * k), DARK[2])
        d("Dial", (1.4, 1.4, 0.2), (cx, y, dz - 3.12), None, col, material="SmoothPlastic", shadow=False)
        d("Needle", (0.12, 0.62, 0.1), (cx + 0.12, y + 0.18, dz - 3.24), G.rz(-35 + 70 * k), RED[2],
          material="SmoothPlastic", shadow=False)
    for k in range(4):
        d("Vent", (3.2, 0.24, 0.24), (cx, 3.2 + k * 0.55, dz - 2.9), None, DARK[2])

    # -------------------------------------------------------------- the aerial, on the right
    ax = 7.6
    d("Aerial", (1.2, 0.6, 1.2), (ax, y1 + 0.3, zc + 3.6), None, DARK[1])
    d("Aerial", (0.3, 5.4, 0.3), (ax, y1 + 3.3, zc + 3.6), G.rz(-6), "b9b4c8")
    d("AerialLight", (0.7, 0.7, 0.7), (ax + 0.29, y1 + 6.2, zc + 3.6), ori(35, 45, 0), RED[1], material="Neon")

    # -------------------------------------------------------------- the sign over the top
    bz = zc + 4.2
    for x in (-9.5, 9.5):
        d("SignPost", (0.9, 6.2, 0.9), (x, y1 + 3.1, bz), None, DARK[1])
    d("SignFrame", (23.0, 5.8, 0.6), (0, 20.0, bz), None, BLUE[1])
    board = deco.plate(m, "Board", (22.0, 5.0, 0.3), (0, 20.0, bz - 0.42), None, "15121c")
    d("SignTop", (23.4, 0.5, 1.0), (0, 23.15, bz), None, BLUE[2])

    # -------------------------------------------------------------- three sockets on the step in front
    for i, x in enumerate((-6.0, 0.0, 6.0)):
        z = -6.8
        d("SocketRim", (3.2, 0.5, 2.0), (x, 1.85, z), None, DARK[1])
        d("SocketRim", (2.0, 0.52, 3.2), (x, 1.85, z), None, DARK[1])
        d("SocketRim", (2.8, 0.54, 2.8), (x, 1.85, z), G.ry(45), DARK[0])
        d("SocketGlow", (2.0, 0.12, 2.0), (x, 2.16, z), G.ry(45), CYAN, material="Neon", shadow=False)
        d("Socket%d" % (i + 1), (1.6, 0.14, 1.6), (x, 2.18, z), None, "1d1d28")           # a potato stands here

    # -------------------------------------------------------------- where players use it
    deco.part(m, "Prompt", (8.0, 5.0, 2.0), (0, 3.0, -11.0), None, "ffffff", material="SmoothPlastic",
              transparency=1.0, shadow=False)
    m.p["primary"] = step
    step.p["pivot"] = step.p["cf"].inv() * base
    return m
