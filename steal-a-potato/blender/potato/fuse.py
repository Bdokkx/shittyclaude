"""PotatoKit.FuseMachine: three potatoes go in, one better potato comes out.

A chunky blue machine about 28 wide, 20 deep and 22 tall on a grey stone step, front -Z:
  * the body: a blue cabinet with lighter corner pillars, a dark skirt, glowing conduits up its sides,
    vents, and a hatch with a red valve wheel on the back
  * Screen: a big lit white screen (Neon) in a dark bezel on the front ("?" goes there)
  * a panel left of the screen as you face it (+X): a lever with a red knob, a big red button, three red lights
  * a low dark dome on top with a glowing cyan ring round its foot and a light on its tip (DomeLight)
  * a fat dark pipe that arches from the dome down into a control block on the machine's left (-X):
    dials, a vent, an amber lamp and the aerial with a red light on its tip
  * three round sockets on the step in front with glowing rims, and a lamp above each on the cabinet
  * Board: the dark sign over the top (22 x 5) for FUSE MACHINE, in a frame of yellow bulbs
  * Prompt: invisible, in front of the step at a player's chest height
The dome and the pipe stay low enough that the whole Board shows from a player's eye level.
Big pieces (the step, the cabinet, the control block, the dome, the pipe) are solid; trim is decoration.
Pivot: middle of the footprint on the ground.
"""
import math

import numpy as np

import spsgeo as G
from spsgeo import CF

from .bricks import Bricks, ori

BLUE = ("3e6fd6", "2f57b0", "5a8cf0", "1e3a80")
DARK = ("2b2b3a", "3c3c50", "1d1d28")
STONE = ("8e89a0", "a3a0b5", "7c788c", "b9b4c8")
CYAN = "4ff0ff"
RED = ("e8403a", "ff3b3b", "b52a26")
AMBER = "ffb21f"
BULB = "ffd447"
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

    def glow(name, size, pos, R=None, col=CYAN):
        return deco.part(m, name, size, pos, R, col, material="Neon", shadow=False)

    # -------------------------------------------------------------- the stone step
    step = s_("Step", (28.0, 0.8, 20.0), (0, 0.4, 0), None, STONE[2])
    s_("Step", (27.0, 0.82, 19.0), (0, 1.19, 0), None, STONE[0])
    for x in (-13.5, 13.5):                                        # corner stones
        for z in (-9.5, 9.5):
            d("Stone", (1.6, 1.0, 1.6), (x * 0.965, 1.25, z * 0.95), G.ry(12 if x * z > 0 else -9), STONE[3])
    d("Stripe", (26.0, 0.1, 0.8), (0, 1.65, -9.0), None, DARK[2])  # hazard stripes along the front edge
    for i in range(10):
        d("Stripe", (1.3, 0.12, 0.84), (-11.7 + i * 2.6, 1.67, -9.0), None, BULB)

    # -------------------------------------------------------------- the cabinet
    y0, y1 = 1.6, 12.6
    zc, D = 1.5, 11.0                                              # front face at z = -4.0, back at 7.0
    W = 18.0
    s_("Cabinet", (W, y1 - y0, D), (0, (y0 + y1) / 2, zc), None, BLUE[0])
    s_("Skirt", (W + 0.6, 1.2, D + 0.6), (0, y0 + 0.58, zc), None, BLUE[3])
    s_("TopTrim", (W + 0.8, 0.8, D + 0.8), (0, y1 - 0.38, zc), None, BLUE[1])
    for x in (-W / 2, W / 2):                                      # lighter corner pillars
        for z in (zc - D / 2, zc + D / 2):
            d("Pillar", (1.4, y1 - y0 - 1.0, 1.4), (x, (y0 + y1) / 2 + 0.1, z), None, BLUE[2])
    for sd in (-1, 1):                                             # both sides: a glowing conduit and vents
        d("Conduit", (0.6, 8.6, 1.4), (sd * (W / 2 + 0.3), 7.2, -2.0), None, DARK[0])
        glow("ConduitGlow", (0.3, 8.0, 0.6), (sd * (W / 2 + 0.65), 7.2, -2.0))
        for k in range(3):
            d("Vent", (0.2, 0.32, 3.2), (sd * (W / 2 + 0.12), 9.4 + k * 0.7, zc + 2.8), None, DARK[2])
    # the back: a hatch with a red valve wheel
    bk = zc + D / 2                                                # 7.0
    d("Hatch", (6.6, 7.6, 0.2), (0, 6.6, bk + 0.1), None, BLUE[3])
    d("Hatch", (6.0, 7.0, 0.3), (0, 6.6, bk + 0.2), None, BLUE[1])
    for y in (4.0, 9.2):
        d("Hinge", (0.5, 1.0, 0.5), (-3.3, y, bk + 0.3), None, DARK[1])
    d("Valve", (2.6, 1.4, 0.3), (0, 7.0, bk + 0.45), None, RED[0])
    d("Valve", (1.4, 2.6, 0.32), (0, 7.0, bk + 0.45), None, RED[0])
    d("Valve", (2.3, 2.3, 0.34), (0, 7.0, bk + 0.45), G.rz(45), RED[2])
    d("Valve", (0.8, 0.8, 0.6), (0, 7.0, bk + 0.62), G.rz(45), DARK[1])

    # front face details: bezel and Screen, a panel with lever / button / lights, socket lamps
    fz = zc - D / 2                                                # -4.0
    sy = 7.4                                                       # the screen's middle
    d("Bezel", (10.4, 7.6, 0.6), (-2.2, sy, fz - 0.3), None, DARK[0])
    d("Bezel", (11.0, 0.6, 0.84), (-2.2, sy + 4.05, fz - 0.4), None, DARK[1])
    deco.part(m, "Screen", (9.2, 6.4, 0.2), (-2.2, sy, fz - 0.68), None, SCREEN, material="Neon", shadow=False)
    d("Panel", (4.4, 7.6, 0.5), (6.0, sy, fz - 0.25), None, DARK[0])
    d("Panel", (3.8, 7.0, 0.1), (6.0, sy, fz - 0.55), None, DARK[1])
    for k in range(3):                                             # three red lights
        glow("Light", (0.6, 0.6, 0.4), (4.9 + k * 1.1, sy + 2.9, fz - 0.68), G.rz(45), RED[1])
    # the big red button: Folk Valley's round on a dark housing
    bx, by = 6.0, sy + 0.6
    d("ButtonBase", (2.2, 2.2, 0.56), (bx, by, fz - 0.75), G.rz(45), DARK[2])
    d("Button", (1.9, 1.3, 0.5), (bx, by, fz - 1.1), None, RED[0])
    d("Button", (1.3, 1.9, 0.52), (bx, by, fz - 1.1), None, RED[0])
    d("Button", (1.7, 1.7, 0.54), (bx, by, fz - 1.1), G.rz(45), RED[2])
    d("Button", (0.9, 0.9, 0.2), (bx - 0.2, by + 0.2, fz - 1.42), G.rz(45), "ff8a80")
    # the lever
    d("LeverBase", (2.4, 0.9, 1.0), (6.0, sy - 2.4, fz - 0.9), None, DARK[2])
    d("Lever", (0.32, 2.2, 0.32), (6.6, sy - 1.45, fz - 1.25), G.rz(-28), "b9b4c8")
    d("LeverKnob", (0.8, 0.8, 0.8), (7.15, sy - 0.5, fz - 1.25), ori(0, 45, 0), RED[0])
    for x in (-6.0, 0.0, 6.0):                                     # a lamp over each socket
        glow("SocketLamp", (0.5, 0.5, 0.2), (x, 3.19, fz - 0.1), G.rz(45))

    # -------------------------------------------------------------- the low dome with its glowing ring
    dz, dy = zc + 0.5, y1
    s_("Dome", (8.0, 1.4, 6.4), (0, dy + 0.7, dz), None, DARK[0])
    s_("Dome", (6.4, 1.42, 8.0), (0, dy + 0.7, dz), None, DARK[0])
    s_("Dome", (7.4, 1.44, 7.4), (0, dy + 0.7, dz), G.ry(45), DARK[1])
    d("Dome", (5.6, 1.1, 4.4), (0, dy + 1.85, dz), None, DARK[0])
    d("Dome", (4.4, 1.12, 5.6), (0, dy + 1.85, dz), None, DARK[0])
    d("Dome", (5.0, 1.14, 5.0), (0, dy + 1.85, dz), G.ry(45), DARK[1])
    d("Dome", (3.0, 0.6, 3.0), (0, dy + 2.65, dz), G.ry(22), DARK[1])
    glow("DomeLight", (1.2, 0.7, 1.2), (0, dy + 3.25, dz), G.ry(45))
    # the ring: eight Neon bars round the dome's foot (a regular octagon)
    a = 4.35                                                       # its apothem
    side = 2 * a * math.tan(math.radians(22.5))
    for i in range(8):
        R = G.ry(i * 45.0)
        glow("Ring", (side + 0.32, 0.42 + 0.03 * (i % 2), 0.4), np.array((0, dy + 0.25, dz)) + R @ (0, 0, -a), R)

    # -------------------------------------------------------------- the pipe: an arch from the dome into the control block
    cx = -11.5                                                     # the control block's middle (on the step)
    ctop = 1.6 + 9.4                                               # its top
    pcol, band = DARK[0], DARK[1]
    path = [(-3.3, dy + 0.9), (-6.0, dy + 2.0), (-8.8, dy + 2.2), (-10.8, dy + 1.5), (-11.5, dy - 0.1),
            (-11.45, ctop + 0.3)]
    for i, ((xa, ya), (xb, yb)) in enumerate(zip(path, path[1:])):
        L = math.hypot(xb - xa, yb - ya)
        ang = math.degrees(math.atan2(yb - ya, xb - xa))
        s_("Pipe", (L + 0.6, 1.7 - 0.02 * (i % 2), 1.7 + 0.02 * (i % 2)), ((xa + xb) / 2, (ya + yb) / 2, dz),
           G.rz(ang), pcol)
    for i, (x, y) in enumerate(path[1:-1]):                         # a collar on every bend
        (xa, ya), (xb, yb) = path[i], path[i + 2]
        ang = math.degrees(math.atan2(yb - ya, xb - xa))
        d("Collar", (0.6, 2.1, 2.1), (x, y, dz), G.rz(ang), band)
    d("Collar", (2.3, 0.6, 2.3), (-3.3, dy + 0.9, dz), G.rz(-68), band)          # where it leaves the dome

    # -------------------------------------------------------------- the control block on the left
    s_("Control", (3.6, 9.4, 5.6), (cx, 1.6 + 4.7, dz), None, BLUE[1])
    d("Control", (3.9, 0.6, 6.0), (cx, ctop + 0.25, dz), None, BLUE[3])
    d("Control", (3.9, 0.8, 6.0), (cx, 1.6 + 0.41, dz), None, BLUE[3])
    cf = dz - 2.8                                                  # its front face
    for k, y in enumerate((8.8, 6.0)):                             # two dials
        d("Dial", (1.8, 1.8, 0.3), (cx, y, cf - 0.15), G.rz(45 * k), DARK[2])
        d("Dial", (1.4, 1.4, 0.2), (cx, y, cf - 0.32), None, "fff7ec", material="SmoothPlastic", shadow=False)
        d("Needle", (0.12, 0.62, 0.1), (cx + 0.12, y + 0.18, cf - 0.44), G.rz(-35 + 70 * k), RED[2],
          material="SmoothPlastic", shadow=False)
    for k in range(4):
        d("Vent", (2.6, 0.24, 0.24), (cx, 3.2 + k * 0.55, cf - 0.1), None, DARK[2])
    d("LampBase", (1.0, 0.4, 1.0), (cx - 0.9, ctop + 0.75, dz - 2.0), None, DARK[1])  # an amber lamp on top
    glow("Lamp", (0.7, 0.7, 0.7), (cx - 0.9, ctop + 1.3, dz - 2.0), ori(35, 45, 0), AMBER)
    # the aerial, on the control block's back corner, leaning out
    ax, az = cx - 0.8, dz + 1.9
    d("Aerial", (1.2, 0.6, 1.2), (ax, ctop + 0.85, az), None, DARK[1])
    lean = G.rz(6)
    top = np.array((ax, ctop + 1.15, az))
    up = lean @ np.array((0.0, 1.0, 0.0))
    d("Aerial", (0.3, 5.4, 0.3), top + up * 2.7, lean, "b9b4c8")
    for h in (2.6, 3.9):
        d("Aerial", (1.1, 0.2, 0.2), top + up * h, lean, "b9b4c8")
    glow("AerialLight", (0.7, 0.7, 0.7), top + up * 5.6, ori(35, 45, 0), RED[1])

    # -------------------------------------------------------------- the sign over the top, in a frame of bulbs
    bz, sy2 = zc + 4.2, 19.3
    for x in (-9.5, 9.5):
        d("SignPost", (0.9, 3.9, 0.9), (x, y1 + 1.95, bz), None, DARK[1])
    d("SignFrame", (24.2, 6.4, 0.6), (0, sy2, bz), None, BLUE[1])
    deco.plate(m, "Board", (22.0, 5.0, 0.3), (0, sy2, bz - 0.42), None, "15121c")
    d("SignTop", (24.6, 0.5, 1.0), (0, sy2 + 3.45, bz), None, BLUE[2])
    for i in range(9):
        for y in (sy2 + 2.85, sy2 - 2.85):
            glow("Bulb", (0.45, 0.45, 0.25), (-10.4 + i * 2.6, y, bz - 0.4), G.rz(45), BULB)
    for x in (-11.55, 11.55):
        for y in (sy2 - 1.4, sy2, sy2 + 1.4):
            glow("Bulb", (0.45, 0.45, 0.25), (x, y, bz - 0.4), G.rz(45), BULB)

    # -------------------------------------------------------------- three round sockets on the step in front
    for i, x in enumerate((6.0, 0.0, -6.0)):                      # Socket1 on the left as you face it
        z = -6.8
        for k in range(4):                                         # an octagonal rim and a glowing ring
            d("SocketRim", (3.4, 0.5 + 0.01 * k, 1.42), (x, 1.85, z), G.ry(45 * k), DARK[k % 2])
            glow("SocketGlow", (2.66, 0.2 + 0.01 * k, 1.12), (x, 2.12, z), G.ry(45 * k))
        d("SocketPad", (1.9, 0.2, 1.1), (x, 2.2, z), None, DARK[2])
        d("SocketPad", (1.1, 0.21, 1.9), (x, 2.2, z), None, DARK[2])
        d("Socket%d" % (i + 1), (1.7, 0.22, 1.7), (x, 2.2, z), G.ry(45), "15121c")  # a potato stands here

    # -------------------------------------------------------------- where players use it
    deco.part(m, "Prompt", (8.0, 5.0, 2.0), (0, 3.0, -11.0), None, "ffffff", material="SmoothPlastic",
              transparency=1.0, shadow=False)
    m.p["primary"] = step
    step.p["pivot"] = step.p["cf"].inv() * base
    return m
