"""PotatoKit.Guardians.<AreaId>: one guardian per area, and their clips
(PotatoKit.GuardianAnimations.<AreaId>.Sleep / Wake / Run).

Each guardian is a Model named after its area, 6-10 studs tall, at most 60 parts:
  * Root: anchored, invisible, 2 x 0.4 x 2 on the ground; the PrimaryPart. Front -Z, +X its right.
  * Every other part is unanchored and Massless, with CanCollide, CanTouch and CanQuery off. Parts are
    welded into groups and the groups hang off Root by Motor6Ds. Each group's main part carries its
    Motor6D's own name, so a Pose, its Motor6D and the Motor6D's Part1 share one name.
  * EyeOpen / EyeShut: the two sets of eye parts. EyeOpen shows; EyeShut is built with Transparency 1.
  * Attributes: Gait (Stomp, Scuttle, Hop, Float or Gallop), Height, RunSpeed (studs a second that
    the Run clip's feet are made for).
Joint frames have model axes (as in Farmer Spud), so a clip reads the same on every guardian.
"""
import math

import numpy as np

import spsgeo as G

from .bricks import ori, shade
from .rig import Rig

INK = "1e1a22"
WHITE = "fafafa"
GLINT = "ffffff"
SHUT_DY = -0.06


def frame_y(d, xhint=(1.0, 0.0, 0.0)):
    """A rotation whose Y axis runs along d (X kept close to xhint)."""
    y = np.asarray(d, float)
    y = y / np.linalg.norm(y)
    x = np.asarray(xhint, float)
    x = x - x.dot(y) * y
    if np.linalg.norm(x) < 1e-6:
        x = np.array((0.0, 0.0, 1.0)) - y[2] * y
    x = x / np.linalg.norm(x)
    z = np.cross(x, y)
    return np.column_stack((x, y, z))


class Beast(Rig):
    """A Rig with the guardians' helpers. Groups whose main part is a real brick: joint();
    invisible holders: hold()."""

    def __init__(self, sc, parent, area, gait, base=None):
        super().__init__(sc, parent, area, base)
        self.area, self.gait = area, gait

    def joint(self, name, part0, hinge, size, pos, col, R=None, material="Plastic"):
        return self.group(name, part0, hinge, name, size=size, pos=pos, R=R, color=col, material=material,
                          visible=True)

    def hold(self, name, part0, hinge):
        return self.group(name, part0, hinge, name)

    def add(self, g, name, size, pos, col, R=None, **kw):
        return self.brick(g, name, size, pos, R, col, **kw)

    def glow(self, g, name, size, pos, col, R=None):
        return self.brick(g, name, size, pos, R, col, material="Neon", shadow=False)

    def pl(self, g, name, size, pos, col=INK, R=None):
        return self.plate(g, name, size, pos, R, col)

    def seg(self, g, name, a, b, w, d, col, extra=0.0, xhint=(1.0, 0.0, 0.0)):
        """A box from point a to point b (w x d across)."""
        a, b = np.asarray(a, float), np.asarray(b, float)
        L = float(np.linalg.norm(b - a)) + extra
        return self.add(g, name, (w, L, d), (a + b) / 2, col, frame_y(b - a, xhint))

    def rnd(self, g, name, w, h, d, pos, cols, R=None, cross=0.58, turned=0.88):
        """Folk Valley's round in three parts: two crossing slabs and a block turned 45 degrees whose
        corners poke out a little past the slabs (as their pumpkins do). A long round (w and d far
        apart) gets an upright core block in place of the turned one."""
        R = np.eye(3) if R is None else R
        p = np.asarray(pos, float)
        cols = cols if isinstance(cols, (tuple, list)) else (cols, cols, cols)
        dh = max(0.024, 0.015 * h)
        out = [self.add(g, name, (w, h, d * cross), p, cols[0], R),
               self.add(g, name, (w * cross, h - dh, d), p, cols[1 % len(cols)], R)]
        if max(w, d) / min(w, d) < 1.25:
            s = math.sqrt(w * d) * turned
            out.append(self.add(g, name, (s, h - 2 * dh, s), p, cols[2 % len(cols)], R @ G.ry(45)))
        else:
            out.append(self.add(g, name, (w * 0.84, h - 2 * dh, d * 0.84), p, cols[2 % len(cols)], R))
        return out

    def eye(self, g, x, y, fz, w, h, pupil=(0.34, 0.5), pdx=0.0, pdy=-0.05, white=WHITE, dark=INK, glint=0.16,
            R=None, glow=None, pupil_glow=False, shut=None, shut_col=INK, shut_glow=False):
        """One eye on a face whose front is at z = fz (turned by R about the eye's middle).
        EyeOpen: the white (Neon when glow is a colour), the pupil (Neon when pupil_glow) and a glint.
        EyeShut: a line (Neon when shut_glow), built with Transparency 1."""
        R = np.eye(3) if R is None else R
        c = np.array((x, y, fz))

        def at(dx, dy, dz):
            return c + R @ np.array((dx, dy, dz))
        if glow:
            self.glow(g, "EyeOpen", (w, h, 0.1), at(0, 0, -0.05), glow, R)
        else:
            self.pl(g, "EyeOpen", (w, h, 0.1), at(0, 0, -0.05), white, R)
        if pupil:
            if pupil_glow:
                self.glow(g, "EyeOpen", (pupil[0], pupil[1], 0.1), at(pdx, pdy, -0.1), dark, R)
            else:
                self.pl(g, "EyeOpen", (pupil[0], pupil[1], 0.1), at(pdx, pdy, -0.1), dark, R)
            if glint:
                gx = pdx + pupil[0] / 2 - glint / 2 - 0.03
                gy = pdy + pupil[1] / 2 - glint / 2 - 0.03
                self.pl(g, "EyeOpen", (glint, glint, 0.1), at(gx, gy, -0.15), GLINT, R)
        sw, sh = shut if shut else (w * 1.05, 0.16)
        self.brick(g, "EyeShut", (sw, sh, 0.1), at(0, SHUT_DY, -0.06), R, shut_col,
                   material="Neon" if shut_glow else "SmoothPlastic", shadow=False, transparency=1.0)

    def done(self, height=None, run_speed=None):
        """Finish the rig and set Gait, Height (its top above the ground) and RunSpeed."""
        from .guardian_anim import RUN_SPEED
        m = self.finish()
        top = 0.0
        for p in m.walk():
            if p.kind == "Part" and p.p["transparency"] < 0.99:
                cf = p.p["cf"]
                top = max(top, float((cf.p + np.abs(cf.R) @ (np.array(p.p["size"]) / 2))[1]))
        self.sc.attr(m, "Gait", self.gait)
        self.sc.attr(m, "Height", round(top, 2))
        self.sc.attr(m, "RunSpeed", RUN_SPEED[self.area])
        return m


# ==================================================================== 1. Meadow: the scarecrow (Hop)

def scarecrow(sc, parent, base=None):
    r = Beast(sc, parent, "Meadow", "Hop", base)
    WOOD = ("8a5a32", "6b4226", "a06c3e")
    SHIRT = ("c9402a", "9a2a1e", "e05a40")
    SACK = ("d9b77a", "c9a568", "e8c890")
    STRAW = ("e8c25a", "d9ae45", "f2d27a")
    HAT = ("7a5230", "6b4426", "8e6438")
    DENIM = ("4a6aa8", "3a5a92")
    # the pole he hops on, and his shirt: one group
    body = r.joint("Body", "Root", (0.0, 0.0, 0.0), (0.45, 5.6, 0.45), (0.0, 2.8, 0.45), WOOD[0])
    r.add(body, "Foot", (1.2, 0.36, 1.2), (0.0, 0.18, 0.45), WOOD[1])
    r.add(body, "Shirt", (2.4, 2.5, 1.5), (0.0, 4.85, 0.0), SHIRT[0])
    for y in (4.35, 5.35):                                         # the plaid
        r.add(body, "Plaid", (2.44, 0.26, 1.54), (0.0, y, 0.0), SHIRT[1])
    r.add(body, "Plaid", (0.26, 2.54, 1.57), (0.45, 4.85, 0.0), SHIRT[1])
    r.add(body, "Patch", (0.7, 0.66, 0.12), (-0.55, 4.0, -0.78), DENIM[0], G.rz(8))
    r.add(body, "Belt", (2.5, 0.3, 1.6), (0.0, 3.72, 0.0), "c8a060")
    r.add(body, "Straw", (0.5, 0.7, 0.3), (0.55, 3.4, -0.68), STRAW[0], G.rz(-14))
    r.add(body, "Straw", (0.45, 0.6, 0.3), (-0.4, 3.38, -0.66), STRAW[2], G.rz(12))
    r.add(body, "Straw", (1.7, 0.4, 1.2), (0.0, 6.22, 0.0), STRAW[1], G.ry(20))      # out of the collar
    # dangling trouser legs, straw for feet
    for s, side in ((-1, "L"), (1, "R")):
        leg = r.joint("Leg" + side, body, (s * 0.6, 3.7, 0.0), (0.95, 2.1, 0.95), (s * 0.6, 2.75, 0.0), DENIM[0])
        r.add(leg, "Cuff", (1.05, 0.34, 1.05), (s * 0.6, 1.75, 0.0), DENIM[1])
        r.add(leg, "Straw", (0.7, 0.6, 0.5), (s * 0.62, 1.32, -0.05), STRAW[0], G.rz(s * 10))
    # arms out along the crossbar
    for s, side in ((-1, "L"), (1, "R")):
        arm = r.joint("Arm" + side, body, (s * 1.15, 5.6, 0.0), (2.3, 0.85, 0.85), (s * 2.25, 5.6, 0.0), SHIRT[0])
        r.add(arm, "Cuff", (0.34, 0.95, 0.95), (s * 3.3, 5.6, 0.0), SHIRT[1])
        r.add(arm, "Straw", (0.7, 0.55, 0.5), (s * 3.75, 5.66, 0.0), STRAW[0], G.rz(s * 12))
        r.add(arm, "Straw", (0.55, 0.4, 0.4), (s * 3.78, 5.32, -0.08), STRAW[2], G.rz(-s * 25))
    # the sack head with a carrot nose, button eyes and a stitched smile
    head = r.joint("Head", body, (0.0, 6.2, 0.0), (2.3, 2.0, 1.6), (0.0, 7.25, 0.0), SACK[0])
    r.add(head, "Head", (1.6, 1.98, 2.3), (0.0, 7.25, 0.0), SACK[1])
    r.add(head, "Head", (1.95, 1.96, 1.95), (0.0, 7.25, 0.0), SACK[2], G.ry(45))
    r.add(head, "Rope", (1.5, 0.26, 1.5), (0.0, 6.28, 0.0), "c8a060", G.ry(45))
    fz = -1.15
    for s in (-1, 1):
        r.eye(head, s * 0.5, 7.45, fz, 0.52, 0.52, pupil=None, white=INK)
        r.pl(head, "EyeOpen", (0.14, 0.14, 0.1), (s * 0.5 + 0.12, 7.57, fz - 0.1), GLINT)
    r.add(head, "Nose", (0.32, 0.32, 0.7), (0.0, 7.05, fz - 0.3), "ff8a1f", ori(-6, 0, 45))
    for i, (x, y, a) in enumerate(((-0.42, 6.62, -18), (0.0, 6.55, 0), (0.42, 6.62, 18))):
        r.pl(head, "Mouth", (0.46, 0.1, 0.1), (x, y, fz - 0.03 - 0.005 * i), INK, G.rz(a))
    for s in (-1, 1):                                              # straw hair under the hat
        r.add(head, "Straw", (0.5, 0.75, 0.4), (s * 1.22, 7.95, -0.25), STRAW[1 if s < 0 else 0], G.rz(s * 32))
    # the floppy hat, a crow on its brim
    hat = r.joint("Hat", head, (0.0, 8.2, 0.0), (3.3, 0.2, 2.4), (0.0, 8.3, 0.0), HAT[0], ori(-4, 10, 4))
    r.add(hat, "Hat", (2.4, 0.22, 3.3), (0.0, 8.3, 0.0), HAT[0], ori(-4, 10, 4))
    r.add(hat, "Hat", (1.6, 1.1, 1.6), (0.05, 8.92, 0.05), HAT[1], ori(-4, 22, 6))
    r.add(hat, "Band", (1.66, 0.3, 1.66), (0.03, 8.55, 0.03), "4a6aa8", ori(-4, 22, 6))
    crow = r.joint("Crow", hat, (1.1, 8.45, 0.4), (0.62, 0.55, 0.95), (1.1, 8.72, 0.45), "2a2a33", G.ry(-25))
    r.add(crow, "Crow", (0.48, 0.44, 0.48), (1.32, 9.12, 0.0), "2a2a33", G.ry(-25))
    r.add(crow, "Beak", (0.14, 0.14, 0.34), (1.43, 9.08, -0.32), "ffb21f", G.ry(-25))
    r.add(crow, "Tail", (0.4, 0.12, 0.6), (0.92, 8.75, 0.98), "1e1e26", ori(-20, -25, 0))
    r.pl(crow, "Glint", (0.1, 0.1, 0.1), (1.56, 9.2, -0.08), GLINT, G.ry(-25))
    return r.done(9.4, 4.5)


# ==================================================================== 2. Dunes: the scorpion (Scuttle)

def scorpion(sc, parent, base=None):
    r = Beast(sc, parent, "Dunes", "Scuttle", base)
    SH = ("d98a3a", "c0722a", "eaa860")
    DK = ("7a4420", "5e321a")
    body = r.joint("Body", "Root", (0.0, 1.6, 0.0), (3.2, 1.2, 3.0), (0.0, 1.7, 0.0), SH[0])
    for i, (w, h, z) in enumerate(((2.9, 1.06, 1.85), (2.6, 0.98, 2.9), (2.2, 0.9, 3.85))):
        y = 1.68 - 0.06 * i
        r.add(body, "Shell", (w, h, 1.1), (0.0, y, z), SH[i % 2])
        r.add(body, "Ridge", (w * 0.55, 0.12, 0.8), (0.0, y + h / 2 + 0.04, z), DK[0])
    r.add(body, "Ridge", (1.8, 0.12, 3.02), (0.0, 2.34, 0.0), DK[0])
    # head: eyes and mouthparts
    head = r.joint("Head", body, (0.0, 1.7, -1.5), (2.6, 1.1, 1.6), (0.0, 1.75, -2.3), SH[2])
    fz = -3.1
    for s in (-1, 1):
        r.eye(head, s * 0.58, 1.92, fz, 0.6, 0.62, pupil=(0.32, 0.42), pdx=-s * 0.04)
        r.pl(head, "Brow", (0.7, 0.14, 0.1), (s * 0.58, 2.33, fz - 0.03), DK[1], G.rz(-s * 16))
    for s in (-1, 1):
        r.add(head, "Fang", (0.36, 0.42, 0.5), (s * 0.34, 1.3, -3.2), DK[1])
    # claws
    for s, side in ((-1, "L"), (1, "R")):
        claw = r.joint("Claw" + side, body, (s * 1.25, 1.6, -2.6), (0.7, 0.62, 1.9), (s * 1.85, 1.62, -3.4), SH[1],
                       G.ry(-s * 30))
        r.add(claw, "Pincer", (1.7, 1.15, 1.8), (s * 2.55, 1.8, -4.65), SH[0], G.ry(-s * 12))
        r.add(claw, "Pincer", (0.5, 0.52, 1.6), (s * 2.1, 1.95, -6.05), SH[2], G.ry(-s * 2))
        r.add(claw, "Pincer", (0.48, 0.46, 1.4), (s * 3.05, 1.7, -5.85), DK[0], G.ry(-s * 24))
    # six legs
    for s, side in ((-1, "L"), (1, "R")):
        for i, z in enumerate((-0.9, 0.2, 1.3)):
            hip = np.array((s * 1.5, 1.45, z))
            knee = np.array((s * 2.7, 2.1, z - 0.15 + 0.15 * i))
            foot = np.array((s * 3.5, 0.05, z - 0.4 + 0.3 * i))
            leg = r.hold("Leg%s%d" % (side, i + 1), body, hip)
            r.seg(leg, "Leg", hip, knee, 0.42, 0.42, SH[1], 0.3)
            r.seg(leg, "Leg", knee, foot, 0.36, 0.36, DK[0], 0.2)
    # the tail, curling up and over in two joints
    pts = [(0.0, 1.65, 4.3), (0.0, 2.6, 5.15), (0.0, 3.95, 5.45), (0.0, 5.25, 5.0), (0.0, 6.0, 4.0)]
    tail = r.hold("Tail", body, pts[0])
    for a, b_, w in zip(pts[:2], pts[1:3], (1.05, 0.95)):
        r.seg(tail, "Tail", a, b_, w, w, SH[0], 0.35, xhint=(1, 0, 0))
    sting = r.hold("Sting", tail, pts[2])
    for a, b_, w in zip(pts[2:4], pts[3:5], (0.9, 0.85)):
        r.seg(sting, "Tail", a, b_, w, w, SH[1], 0.35)
    r.add(sting, "Sting", (1.0, 0.95, 1.1), (0.0, 5.75, 3.35), "b5402a", G.rx(30))
    r.seg(sting, "Sting", (0.0, 5.55, 2.95), (0.0, 4.95, 2.45), 0.32, 0.32, "3a2420", 0.1)
    return r.done(6.5, 6.0)


# ==================================================================== 3. Marsh: the bog frog (Hop)

def frog(sc, parent, base=None):
    r = Beast(sc, parent, "Marsh", "Hop", base)
    GR = ("5f9a3a", "4c8030", "7cb850")
    BE = ("dfe8a0", "c8d488")
    SPOT = "3d6a26"
    body = r.joint("Body", "Root", (0.0, 0.9, 0.9), (4.2, 2.6, 3.0), (0.0, 2.3, 0.5), GR[0], G.rx(-14))
    r.add(body, "Body", (3.0, 2.56, 4.2), (0.0, 2.3, 0.5), GR[1], G.rx(-14))
    r.add(body, "Body", (3.7, 2.5, 3.7), (0.0, 2.3, 0.5), GR[2], G.rx(-14))
    r.add(body, "Belly", (2.8, 2.1, 0.5), (0.0, 2.15, -1.55), BE[0], G.rx(-14))
    for (x, y, z, a) in ((0.9, 3.75, 0.9, 10), (-0.7, 3.55, 1.6, -20), (0.1, 3.4, 2.3, 30)):
        r.add(body, "Spot", (0.7, 0.14, 0.6), (x, y, z), SPOT, G.rx(-14) @ G.ry(a))
    head = r.joint("Head", body, (0.0, 3.6, -0.7), (4.0, 1.4, 2.8), (0.0, 4.15, -1.5), GR[0])
    r.add(head, "Head", (3.3, 1.38, 3.3), (0.0, 4.15, -1.35), GR[2])
    jaw = r.joint("Jaw", head, (0.0, 3.6, -0.4), (3.8, 0.6, 2.7), (0.0, 3.35, -1.6), BE[1])
    r.pl(jaw, "Mouth", (3.4, 0.1, 2.2), (0.0, 3.66, -1.62), "c0405a")
    r.pl(head, "Mouth", (3.7, 0.14, 0.1), (0.0, 3.62, -2.97), INK)
    for s in (-1, 1):
        r.pl(head, "Nostril", (0.2, 0.12, 0.1), (s * 0.35, 4.55, -2.96), INK)
        bump = np.array((s * 1.2, 5.0, -1.6))
        r.rnd(head, "EyeBump", 1.4, 1.2, 1.4, bump, (GR[0], GR[1], GR[2]))
        r.eye(head, s * 1.2, 5.05, -2.39, 0.95, 0.8, pupil=(0.62, 0.3), pdy=-0.04)
    # a mushroom growing on its head
    r.add(head, "Mushroom", (0.4, 0.8, 0.4), (0.55, 5.2, -0.4), "f2e8d0", G.rz(-12))
    r.rnd(head, "Mushroom", 1.3, 0.5, 1.3, (0.65, 5.7, -0.4), ("e04a3a", "c9402a", "e85a48"), R=G.rz(-12))
    r.pl(head, "Spot", (0.24, 0.1, 0.24), (0.5, 5.99, -0.62), "fff7ec", G.rz(-12))
    # big back legs folded at its sides, small front legs
    for s, side in ((-1, "L"), (1, "R")):
        leg = r.joint("Leg" + side, body, (s * 1.7, 1.5, 1.2), (1.4, 1.7, 2.6), (s * 2.3, 1.45, 0.9), GR[1],
                      G.ry(s * 6))
        r.add(leg, "Leg", (0.9, 0.9, 1.9), (s * 2.55, 0.6, 0.0), GR[0], G.ry(s * 10))
        r.add(leg, "Foot", (1.5, 0.3, 1.7), (s * 2.75, 0.15, -1.1), GR[2], G.ry(s * 18))
        for k in (-1, 1):
            r.add(leg, "Toe", (0.34, 0.22, 0.7), (s * 2.75 + k * 0.5, 0.11, -2.0), GR[2], G.ry(s * 18 + k * 14))
        arm = r.joint("Arm" + side, body, (s * 1.35, 2.2, -1.3), (0.62, 2.0, 0.62), (s * 1.5, 1.2, -1.7), GR[0],
                      G.rz(s * 8))
        r.add(arm, "Hand", (1.2, 0.26, 1.0), (s * 1.65, 0.13, -2.0), GR[2], G.ry(-s * 15))
    return r.done(6.3, 4.0)


# ==================================================================== 4. Jungle: the tiger (Gallop)

def tiger(sc, parent, base=None):
    r = Beast(sc, parent, "Jungle", "Gallop", base)
    OR = ("e8862a", "d4721c", "f5a04a")
    ST = "2b2420"
    WH = ("f4ecdc", "e2d6c0")
    body = r.joint("Body", "Root", (0.0, 3.4, 0.4), (3.0, 2.6, 6.0), (0.0, 3.5, 0.6), OR[0])
    r.add(body, "Chest", (3.2, 2.9, 1.9), (0.0, 3.6, -2.3), OR[1])
    r.add(body, "Belly", (2.6, 0.8, 5.0), (0.0, 2.25, 0.3), WH[0])
    for i, z in enumerate((-1.2, 0.2, 1.6, 3.0)):
        r.add(body, "Stripe", (3.06, 1.5 - 0.1 * i, 0.38), (0.0, 4.1, z), ST, ori(10 - 6 * i, 0, 0))
    r.add(body, "Stripe", (3.26, 1.1, 0.38), (0.0, 4.3, -2.2), ST, G.rx(-8))
    head = r.joint("Head", body, (0.0, 4.3, -3.0), (2.8, 2.3, 2.4), (0.0, 5.0, -3.9), OR[0])
    r.add(head, "Muzzle", (1.9, 1.0, 1.0), (0.0, 4.4, -5.3), WH[0])
    r.add(head, "Nose", (0.76, 0.5, 0.3), (0.0, 4.95, -5.72), "e07a8a")
    for s in (-1, 1):
        r.add(head, "Ear", (0.8, 0.8, 0.32), (s * 1.0, 6.4, -3.5), OR[1], G.rz(-s * 14))
        r.add(head, "Ear", (0.44, 0.44, 0.1), (s * 1.0, 6.36, -3.71), WH[1], G.rz(-s * 14))
        r.add(head, "Cheek", (0.4, 1.0, 1.1), (s * 1.48, 4.6, -4.4), WH[0], G.rz(s * 10))
        r.eye(head, s * 0.62, 5.35, -5.1, 0.62, 0.7, pupil=(0.34, 0.5), pdx=-s * 0.03)
        r.pl(head, "Stripe", (0.18, 0.62, 0.1), (s * 0.55, 6.0, -5.13), ST, G.rz(s * 18))
    r.pl(head, "Stripe", (0.2, 0.7, 0.1), (0.0, 5.95, -5.13), ST)
    for s in (-1, 1):
        r.add(head, "Fang", (0.2, 0.42, 0.2), (s * 0.45, 3.77, -5.6), WH[0])
    jaw = r.joint("Jaw", head, (0.0, 4.1, -4.3), (1.6, 0.5, 1.2), (0.0, 3.8, -5.05), WH[1])
    r.pl(jaw, "Mouth", (1.3, 0.1, 0.9), (0.0, 4.07, -5.05), "b03a3a")
    for s in (-1, 1):
        for f, z, side in ((0, -2.4, "F"), (1, 2.5, "B")):
            name = "Leg%s%s" % (side, "L" if s < 0 else "R")
            leg = r.joint(name, body, (s * 1.0, 3.2, z), (0.95, 2.7, 1.05), (s * 1.0, 1.75, z), OR[0 if f else 1])
            r.add(leg, "Paw", (1.15, 0.5, 1.4), (s * 1.0, 0.25, z - 0.15), WH[0])
            r.add(leg, "Stripe", (1.0, 0.3, 1.1), (s * 1.0, 1.9 - 0.2 * f, z), ST)
    tail = r.joint("Tail", body, (0.0, 4.3, 3.5), (0.55, 0.55, 1.8), (0.0, 4.6, 4.3), OR[0], G.rx(-20))
    r.seg(tail, "Tail", (0.0, 4.9, 5.0), (0.0, 6.1, 5.7), 0.5, 0.5, OR[1], 0.2)
    r.seg(tail, "Tail", (0.0, 6.05, 5.65), (0.0, 6.9, 5.75), 0.52, 0.52, ST, 0.1)
    return r.done(6.8, 9.0)


# ==================================================================== 5. Reef: the giant crab, a pirate (Scuttle)

def crab(sc, parent, base=None):
    r = Beast(sc, parent, "Reef", "Scuttle", base)
    RD = ("d9442e", "b8361f", "f06a4a")
    BE = "f2dcb0"
    DK = "6a2018"
    body = r.joint("Body", "Root", (0.0, 2.4, 0.0), (6.0, 1.8, 3.0), (0.0, 2.6, 0.2), RD[0])
    r.add(body, "Shell", (4.0, 1.78, 4.4), (0.0, 2.6, 0.2), RD[1])
    r.add(body, "Shell", (4.4, 1.76, 4.4), (0.0, 2.6, 0.2), RD[2], G.ry(45))
    r.add(body, "Shell", (4.2, 0.5, 2.8), (0.0, 3.62, 0.25), RD[0])
    r.add(body, "Belly", (4.6, 0.6, 3.4), (0.0, 1.62, 0.2), BE)
    for s in (-1, 1):
        r.add(body, "Spike", (0.5, 0.5, 0.5), (s * 2.95, 3.0, -0.6), RD[2], ori(0, 45, 45))
    r.pl(body, "Mouth", (1.2, 0.14, 0.1), (0.0, 2.05, -2.04), INK)
    r.pl(body, "Mouth", (0.5, 0.12, 0.1), (0.4, 2.12, -2.045), INK, G.rz(25))
    head = r.hold("Head", body, (0.0, 3.5, -1.4))
    for s in (-1, 1):
        r.add(head, "Stalk", (0.36, 2.0, 0.36), (s * 0.87, 4.55, -1.55), RD[1], G.rz(-s * 10))
        r.rnd(head, "EyeBall", 1.0, 0.95, 1.0, (s * 1.05, 5.7, -1.6), (RD[0], RD[2], RD[0]))
    r.eye(head, 1.05, 5.73, -2.13, 0.72, 0.72, pupil=(0.36, 0.46), pdx=-0.05)
    r.pl(head, "EyePatch", (0.74, 0.74, 0.1), (-1.05, 5.73, -2.18), INK, G.rz(45))
    r.pl(head, "Strap", (1.15, 0.12, 0.1), (-1.05, 5.73, -2.2), INK, G.rz(-30))
    for s, side, k in ((-1, "L", 1.0), (1, "R", 1.25)):                # the right claw is the big one
        claw = r.joint("Claw" + side, body, (s * 2.5, 2.4, -1.4), (0.8, 0.8, 2.0), (s * 3.1, 2.55, -2.2), RD[1],
                       ori(10, -s * 30, 0))
        r.add(claw, "Claw", (1.7 * k, 1.6 * k, 2.0 * k), (s * 3.75, 2.9, -3.55), RD[0], G.ry(-s * 8))
        r.add(claw, "Claw", (0.7 * k, 0.6 * k, 1.6 * k), (s * (3.45 - 0.1 * k), 3.35 + 0.1 * k, -4.95 - 0.5 * (k - 1)),
            RD[2], G.ry(-s * 4))
        r.add(claw, "Claw", (0.6 * k, 0.5 * k, 1.3 * k), (s * (4.1 + 0.15 * k), 2.6, -4.75 - 0.4 * (k - 1)), DK,
            G.ry(-s * 22))
    for s, side in ((-1, "L"), (1, "R")):
        for i, z in enumerate((-0.4, 0.8, 2.0)):
            hip = np.array((s * 2.6, 2.1, z))
            knee = np.array((s * 4.1, 2.9, z + 0.25 * i))
            foot = np.array((s * 4.9, 0.05, z + 0.5 * i - 0.2))
            leg = r.hold("Leg%s%d" % (side, i + 1), body, hip)
            r.seg(leg, "Leg", hip, knee, 0.55, 0.55, RD[1], 0.35)
            r.seg(leg, "Leg", knee, foot, 0.45, 0.45, RD[0], 0.2)
    return r.done(6.0, 5.5)


# ==================================================================== 6. Frost: the snow golem (Stomp)

def snow_golem(sc, parent, base=None):
    r = Beast(sc, parent, "Frost", "Stomp", base)
    SN = ("e6eff7", "cddceb", "f7fbff", "b4c8dc")
    IC = ("9fd8ff", "7cc4f5", "c6ecff")
    ROCK = ("8a8f9a", "6e7380")
    for s, side in ((-1, "L"), (1, "R")):
        leg = r.joint("Leg" + side, "Root", (s * 1.2, 2.6, 0.0), (1.7, 2.3, 1.8), (s * 1.2, 1.55, 0.0), SN[1])
        r.add(leg, "Foot", (2.0, 0.66, 2.4), (s * 1.25, 0.33, -0.2), SN[3])
    body = r.joint("Body", "Root", (0.0, 2.9, 0.0), (5.0, 3.6, 2.6), (0.0, 4.7, 0.0), SN[0])
    r.add(body, "Body", (3.6, 3.58, 3.6), (0.0, 4.7, 0.0), SN[1])
    r.add(body, "Body", (4.4, 3.56, 3.2), (0.0, 4.7, 0.0), SN[2])
    r.add(body, "Body", (4.6, 0.6, 3.3), (0.0, 3.05, 0.0), SN[3])                  # its dirty underside
    for (x, y, a) in ((-1.4, 5.6, 20), (1.5, 3.9, -15)):                            # stones frozen in it
        r.add(body, "Stone", (0.8, 0.6, 0.3), (x, y, -1.72), ROCK[0], G.rz(a))
    r.add(body, "Core", (1.25, 1.25, 0.24), (0.15, 4.7, -1.7), IC[1], G.rz(45))     # a glowing ice heart
    r.glow(body, "Core", (0.8, 0.8, 0.2), (0.15, 4.7, -1.8), "8fe4ff", G.rz(45))
    for s in (-1, 1):
        r.add(body, "Shard", (0.7, 1.9, 0.7), (s * 2.0, 6.75, 0.35), IC[0], ori(0, 30, -s * 28))
        r.add(body, "Shard", (0.5, 1.3, 0.5), (s * 1.4, 6.9, 0.9), IC[2], ori(15, 0, -s * 12))
        r.add(body, "Snow", (1.5, 0.6, 1.5), (s * 2.45, 6.25, 0.0), SN[2], G.ry(s * 20))
    head = r.joint("Head", body, (0.0, 6.5, -0.2), (2.8, 2.0, 2.4), (0.0, 7.7, -0.3), SN[0])
    r.add(head, "Jaw", (2.5, 0.8, 2.3), (0.0, 6.9, -0.45), SN[1])
    fz = -1.5
    for s in (-1, 1):
        r.eye(head, s * 0.62, 7.85, fz, 0.66, 0.74, pupil=(0.32, 0.4), pdx=-s * 0.04, white=INK, dark="6fd8ff",
              pupil_glow=True)
        r.add(head, "Brow", (0.95, 0.3, 0.45), (s * 0.66, 8.42, fz - 0.05), IC[1], G.rz(-s * 18))
    r.pl(head, "Mouth", (1.5, 0.42, 0.1), (0.0, 7.0, -1.6), INK)
    for x in (-0.4, 0.4):
        r.pl(head, "Tooth", (0.26, 0.26, 0.1), (x, 7.15, -1.65), IC[2], G.rz(45))
    for (x, z, a, h) in ((-0.7, 0.1, 18, 0.9), (0.05, -0.2, -6, 1.2), (0.75, 0.15, -20, 0.85)):
        r.add(head, "Crown", (0.5, h, 0.5), (x, 8.7 + h / 2 - 0.1, z), IC[0], ori(0, 45, a))
    for s, side in ((-1, "L"), (1, "R")):
        arm = r.joint("Arm" + side, body, (s * 2.55, 5.7, 0.0), (1.4, 2.5, 1.4), (s * 2.95, 4.6, 0.0), SN[1],
                      G.rz(s * 10))
        r.rnd(arm, "Fist", 2.0, 1.8, 2.0, (s * 3.25, 2.95, -0.1), (SN[0], SN[2], SN[3]))
        r.add(arm, "Shard", (0.45, 1.1, 0.45), (s * 3.55, 4.4, 0.55), IC[1], ori(25, 0, -s * 30))
    return r.done(9.6, 4.5)


# ==================================================================== 7. Haunt: the ghost with a lantern (Float)

def ghost(sc, parent, base=None):
    r = Beast(sc, parent, "Haunt", "Float", base)
    SH = ("eef0fc", "dcdff3", "fbfbff", "c9c6ee")
    body = r.joint("Body", "Root", (0.0, 3.2, 0.0), (3.8, 2.6, 2.4), (0.0, 3.1, 0.0), SH[0])
    r.add(body, "Sheet", (2.6, 2.58, 3.6), (0.0, 3.1, 0.0), SH[1])
    r.add(body, "Sheet", (3.3, 2.56, 3.2), (0.0, 3.1, 0.0), SH[2])
    for i in range(6):                                             # the hem: flaps hanging round the bottom
        a = math.radians(30 + 60 * i)
        R = G.ry(-(30 + 60 * i)) @ G.rx(-12)
        r.add(body, "Hem", (1.15, 1.1 - 0.2 * (i % 2), 0.6), (1.45 * math.sin(a), 1.55 + 0.1 * (i % 2),
                                                             -1.35 * math.cos(a)), SH[3 if i % 2 else 0], R)
    head = r.joint("Head", body, (0.0, 4.4, 0.0), (3.4, 2.4, 2.2), (0.0, 5.5, 0.0), SH[0])
    r.add(head, "Head", (2.2, 2.38, 3.1), (0.0, 5.5, 0.0), SH[1])
    r.add(head, "Head", (2.9, 2.36, 2.8), (0.0, 5.5, 0.0), SH[2])
    r.add(head, "Head", (2.1, 0.7, 2.0), (0.0, 6.95, 0.05), SH[0])
    r.add(head, "Head", (1.0, 0.5, 1.0), (0.12, 7.5, 0.15), SH[2], G.ry(30))
    fz = -1.6
    for s in (-1, 1):
        r.eye(head, s * 0.62, 5.75, fz, 0.62, 0.95, pupil=(0.22, 0.22), pdx=0.1, pdy=0.24, white=INK, dark=GLINT,
              glint=None)
        r.pl(head, "Cheek", (0.5, 0.24, 0.1), (s * 1.05, 5.15, fz - 0.03), "f2a6c8")
    r.pl(head, "Mouth", (0.6, 0.7, 0.1), (0.0, 4.85, fz - 0.03), INK)
    for s, side in ((-1, "L"), (1, "R")):
        arm = r.joint("Arm" + side, body, (s * 1.6, 4.3, 0.0), (1.7, 0.8, 0.9), (s * 2.3, 4.0, 0.0), SH[1],
                      G.rz(-s * 25))
        r.add(arm, "Arm", (0.75, 0.6, 0.75), (s * 3.05, 3.55, 0.0), SH[0], G.rz(-s * 40))
    # a lantern in its right hand
    r.add("ArmR", "Lantern", (0.12, 0.7, 0.12), (3.2, 2.95, -0.1), "3a3040")
    r.add("ArmR", "Lantern", (0.85, 0.22, 0.85), (3.2, 2.55, -0.1), "3a3040")
    r.glow("ArmR", "LanternLight", (0.62, 0.72, 0.62), (3.2, 2.08, -0.1), "ffb02a")
    r.add("ArmR", "Lantern", (0.85, 0.22, 0.85), (3.2, 1.61, -0.1), "3a3040")
    tail = r.joint("Tail", body, (0.0, 2.2, 1.4), (0.9, 0.7, 1.6), (0.0, 2.05, 2.05), SH[0], G.rx(20))
    r.add(tail, "Tail", (0.55, 0.5, 0.9), (0.0, 1.62, 2.95), SH[3], G.rx(35))
    return r.done(7.75, 6.0)


# ==================================================================== 8. Lava: the magma golem (Stomp)

def magma_golem(sc, parent, base=None):
    r = Beast(sc, parent, "Lava", "Stomp", base)
    RK = ("3a3030", "2a2222", "4a3c38", "5a4038")
    LV = ("ff6a1a", "ffb02a", "ff3b1a")
    for s, side in ((-1, "L"), (1, "R")):
        leg = r.joint("Leg" + side, "Root", (s * 1.25, 2.7, 0.0), (1.8, 2.3, 1.9), (s * 1.25, 1.6, 0.0), RK[0])
        r.add(leg, "Foot", (2.2, 0.7, 2.6), (s * 1.3, 0.35, -0.2), RK[1])
        r.glow(leg, "Crack", (0.16, 1.1, 0.1), (s * 1.25 + 0.2, 1.8, -0.98), LV[0], G.rz(15))
    body = r.joint("Body", "Root", (0.0, 3.0, 0.0), (5.2, 3.8, 2.6), (0.0, 4.9, 0.0), RK[0])
    r.add(body, "Body", (3.8, 3.78, 3.6), (0.0, 4.9, 0.0), RK[2])
    r.add(body, "Body", (4.6, 3.76, 3.2), (0.0, 4.9, 0.0), RK[1])
    r.add(body, "Core", (1.9, 1.9, 0.2), (0.0, 5.1, -1.85), RK[3], G.rz(45))
    r.glow(body, "Core", (1.3, 1.3, 0.2), (0.0, 5.1, -1.92), LV[1], G.rz(45))
    for a in (35, 145, 265):
        rad = math.radians(a)
        r.glow(body, "Crack", (0.14, 1.1, 0.1), (1.45 * math.cos(rad), 5.1 + 1.45 * math.sin(rad), -1.85), LV[0],
               G.rz(a - 90))
    for s in (-1, 1):
        r.add(body, "Boulder", (1.9, 1.5, 1.9), (s * 2.6, 6.75, 0.1), RK[2], G.ry(s * 20))
        r.glow(body, "Ember", (0.34, 0.34, 0.34), (s * 2.3, 7.6, -0.2), LV[1], ori(35, 45, 0))
    head = r.joint("Head", body, (0.0, 6.8, -0.3), (2.6, 2.0, 2.4), (0.0, 7.8, -0.4), RK[0])
    r.add(head, "Brow", (2.9, 0.6, 0.8), (0.0, 8.45, -1.27), RK[1])
    for s in (-1, 1):
        r.add(head, "Horn", (0.5, 1.3, 0.5), (s * 1.15, 9.0, -0.2), RK[3], G.rz(-s * 25))
        r.eye(head, s * 0.6, 8.0, -1.6, 0.62, 0.34, pupil=None, glow=LV[1], R=G.rz(s * 12), shut_col="5a1a0a")
    r.glow(head, "Mouth", (1.3, 0.32, 0.1), (0.0, 7.2, -1.65), LV[0])
    for x in (-0.3, 0.3):
        r.pl(head, "Tooth", (0.22, 0.22, 0.1), (x, 7.3, -1.71), RK[1], G.rz(45))
    for s, side in ((-1, "L"), (1, "R")):
        arm = r.joint("Arm" + side, body, (s * 2.75, 6.0, 0.0), (1.7, 2.8, 1.7), (s * 3.1, 4.8, 0.0), RK[2],
                      G.rz(s * 8))
        r.add(arm, "Fist", (2.3, 2.1, 2.3), (s * 3.35, 2.95, -0.1), RK[0], G.ry(s * 10))
        r.glow(arm, "Crack", (0.12, 0.9, 0.1), (s * 3.25, 3.0, -1.31), LV[0], G.ry(s * 10) @ G.rz(-20))
    return r.done(9.6, 4.5)


# ==================================================================== 9. Crystal: the crystal spider (Scuttle)

def crystal_spider(sc, parent, base=None):
    r = Beast(sc, parent, "Crystal", "Scuttle", base)
    BD = ("4a3a6a", "3a2c58", "5c4a80")
    CR = ("b58cff", "8ce8ff", "d8b8ff")
    body = r.joint("Body", "Root", (0.0, 2.5, 0.3), (2.6, 1.6, 2.2), (0.0, 2.6, -0.4), BD[0])
    r.add(body, "Abdomen", (3.6, 2.8, 3.0), (0.0, 3.2, 2.4), BD[1])
    r.add(body, "Abdomen", (3.0, 2.78, 4.0), (0.0, 3.2, 2.4), BD[2])
    r.add(body, "Abdomen", (3.4, 2.76, 3.6), (0.0, 3.2, 2.4), BD[0])
    for i, (x, z, rx_, rz_, h, c) in enumerate(((0.0, 2.0, -10, 0, 2.2, 0), (-0.9, 2.8, 12, 18, 1.7, 1),
                                                (0.9, 2.9, 10, -20, 1.8, 2), (-0.5, 1.4, -18, 12, 1.4, 1),
                                                (0.6, 1.6, -15, -14, 1.3, 0))):
        R = ori(rx_, 45, rz_)
        base_ = np.array((x, 4.5, z))
        r.add(body, "Crystal", (0.62, h, 0.62), base_ + R @ (0, h / 2 - 0.2, 0), CR[c], R)
        if i < 2:
            r.glow(body, "CrystalTip", (0.4, 0.5, 0.4), base_ + R @ (0, h - 0.05, 0), "e0b0ff", R)
    head = r.joint("Head", body, (0.0, 2.6, -1.5), (2.0, 1.5, 1.4), (0.0, 2.6, -2.1), BD[2])
    fz = -2.8
    for s in (-1, 1):
        r.eye(head, s * 0.5, 2.6, fz, 0.56, 0.62, pupil=(0.3, 0.4), pdx=-s * 0.03)
        r.eye(head, s * 0.38, 3.18, fz, 0.3, 0.26, pupil=(0.11, 0.11), pdx=0.04, pdy=0.04, white=INK, dark=GLINT,
              glint=None, shut=(0.3, 0.1))
        r.add(head, "Fang", (0.26, 0.62, 0.26), (s * 0.36, 1.78, -2.55), CR[2], G.rz(s * 8))
    for s, side in ((-1, "L"), (1, "R")):
        for i, z in enumerate((-1.3, -0.55, 0.2, 0.95)):
            hip = np.array((s * 1.1, 2.5, z))
            knee = np.array((s * 3.0, 4.3, z * 1.5 - 0.1))
            foot = np.array((s * 4.6, 0.05, z * 2.4 - 0.2))
            leg = r.hold("Leg%s%d" % (side, i + 1), body, hip)
            r.seg(leg, "Leg", hip, knee, 0.44, 0.44, BD[0], 0.3)
            r.seg(leg, "Leg", knee, foot, 0.36, 0.36, BD[2], 0.2)
    return r.done(5.9, 6.0)


# ==================================================================== 10. Dino: the raptor (Gallop)

def raptor(sc, parent, base=None):
    r = Beast(sc, parent, "Dino", "Gallop", base)
    GR = ("3f9a6a", "2f7a52", "5ab884")
    BE, ST, CL = "e8e0c0", "e8862a", "f2ead8"
    Rb = G.rx(-10)
    bc = np.array((0.0, 4.6, 0.0))
    body = r.joint("Body", "Root", (0.0, 4.3, 0.6), (2.4, 2.4, 4.4), bc, GR[0], Rb)
    r.add(body, "Belly", (2.0, 0.6, 3.6), bc + Rb @ (0, -1.05, -0.2), BE, Rb)
    for z in (-1.1, 0.1, 1.3):
        r.add(body, "Stripe", (2.46, 0.9, 0.4), bc + Rb @ (0, 0.8, z), ST, Rb)
    head = r.joint("Head", body, (0.0, 5.4, -1.9), (1.8, 1.6, 2.2), (0.0, 7.0, -3.5), GR[0])
    r.seg(head, "Neck", (0.0, 5.1, -1.9), (0.0, 6.7, -3.0), 1.3, 1.3, GR[1], 0.4)
    r.add(head, "Snout", (1.4, 1.0, 1.5), (0.0, 6.75, -4.9), GR[2])
    r.add(head, "Crest", (0.3, 0.6, 1.0), (0.0, 7.95, -3.4), ST, G.rx(12))
    r.add(head, "Crest", (0.26, 0.5, 0.8), (0.0, 7.8, -2.6), ST, G.rx(20))
    for s in (-1, 1):
        r.eye(head, s * 0.5, 7.5, -4.6, 0.5, 0.56, pupil=(0.26, 0.42), pdx=-s * 0.03, R=G.ry(s * 16))
        r.pl(head, "Brow", (0.6, 0.14, 0.1), (s * 0.5, 7.9, -4.66), INK, G.ry(s * 16) @ G.rz(-s * 18))
        r.pl(head, "Nostril", (0.18, 0.12, 0.1), (s * 0.3, 7.05, -5.68), INK)
        r.add(head, "Tooth", (0.2, 0.32, 0.2), (s * 0.45, 6.15, -5.4), CL)
    jaw = r.joint("Jaw", head, (0.0, 6.3, -3.4), (1.2, 0.45, 2.0), (0.0, 6.0, -4.6), BE)
    r.pl(jaw, "Mouth", (1.0, 0.1, 1.6), (0.0, 6.24, -4.6), "b03a3a")
    for s, side in ((-1, "L"), (1, "R")):
        arm = r.joint("Arm" + side, body, (s * 0.95, 4.7, -1.6), (0.42, 1.3, 0.42), (s * 1.05, 4.15, -1.85), GR[1],
                      G.rx(25))
        r.add(arm, "Claw", (0.26, 0.42, 0.42), (s * 1.05, 3.5, -2.2), CL, G.rx(40))
        leg = r.joint("Leg" + side, body, (s * 1.0, 4.3, 0.8), (1.1, 2.0, 1.5), (s * 1.05, 3.5, 0.8), GR[1])
        r.seg(leg, "Shin", (s * 1.05, 2.7, 1.25), (s * 1.05, 0.45, 0.6), 0.62, 0.62, GR[0], 0.3)
        r.add(leg, "Foot", (0.9, 0.4, 1.7), (s * 1.05, 0.2, -0.05), GR[2])
        r.add(leg, "Claw", (0.22, 0.6, 0.22), (s * 0.78, 0.55, -0.65), CL, G.rx(-30))
    tail = r.joint("Tail", body, (0.0, 4.9, 2.1), (1.3, 1.2, 2.3), (0.0, 5.1, 3.15), GR[0], G.rx(-11))
    r.add(tail, "Stripe", (1.36, 0.6, 0.4), (0.0, 5.55, 3.4), ST, G.rx(-11))
    tip = r.joint("TailTip", tail, (0.0, 5.3, 4.2), (0.85, 0.8, 2.3), (0.0, 5.5, 5.3), GR[1], G.rx(-9))
    r.add(tip, "Stripe", (0.9, 0.4, 0.35), (0.0, 5.82, 5.5), ST, G.rx(-9))
    return r.done(8.3, 9.0)


# ==================================================================== 11. Toy: the wind-up tin robot (Stomp)

def toy_robot(sc, parent, base=None):
    r = Beast(sc, parent, "Toy", "Stomp", base)
    TIN = ("c0c8d4", "9aa4b2", "dfe5ee")
    RD = ("e8403a", "b52a26")
    BL, YE, DK = "3e6fd6", "ffd447", "3a3a44"
    for s, side in ((-1, "L"), (1, "R")):
        leg = r.joint("Leg" + side, "Root", (s * 0.9, 2.7, 0.0), (1.1, 2.0, 1.1), (s * 0.9, 1.75, 0.0), TIN[1])
        r.add(leg, "Foot", (1.7, 0.75, 2.3), (s * 0.95, 0.375, -0.25), RD[0])
    body = r.joint("Body", "Root", (0.0, 2.8, 0.0), (3.4, 3.0, 2.4), (0.0, 4.4, 0.0), TIN[0])
    r.add(body, "Belt", (3.5, 0.4, 2.5), (0.0, 3.05, 0.0), BL)
    r.pl(body, "Panel", (2.2, 1.5, 0.1), (0.0, 4.75, -1.24), DK)
    for i, c in enumerate(("ff3b3b", "ffd447", "5ff07a")):
        r.glow(body, "Light", (0.32, 0.32, 0.1), (-0.6 + 0.6 * i, 5.15, -1.3), c)
    r.pl(body, "Dial", (0.55, 0.55, 0.1), (-0.5, 4.35, -1.3), "fff7ec")
    for y in (4.45, 4.2):
        r.pl(body, "Grille", (0.9, 0.12, 0.1), (0.45, y, -1.3), TIN[2])
    for x in (-1.45, 1.45):
        for y in (3.55, 5.65):
            r.pl(body, "Rivet", (0.22, 0.22, 0.1), (x, y, -1.24), YE)
    key = r.joint("Key", body, (0.0, 4.6, 1.2), (0.3, 0.3, 0.9), (0.0, 4.6, 1.6), TIN[1])
    r.add(key, "Key", (1.8, 1.0, 0.25), (0.0, 4.6, 2.15), YE)
    for x in (-0.45, 0.45):
        r.pl(key, "Key", (0.4, 0.4, 0.27), (x, 4.6, 2.15), DK)
    head = r.joint("Head", body, (0.0, 5.9, 0.0), (2.6, 2.0, 2.2), (0.0, 7.0, 0.0), TIN[2])
    for s in (-1, 1):
        r.eye(head, s * 0.55, 7.25, -1.1, 0.7, 0.7, pupil=(0.3, 0.3), glow="ffe34a")
        r.add(head, "Ear", (0.4, 0.8, 0.8), (s * 1.5, 7.0, 0.0), RD[0])
    r.pl(head, "Mouth", (1.2, 0.42, 0.1), (0.0, 6.45, -1.14), DK)
    for x in (-0.3, 0.0, 0.3):
        r.pl(head, "Mouth", (0.08, 0.36, 0.1), (x, 6.45, -1.18), TIN[0])
    r.add(head, "Antenna", (0.16, 1.0, 0.16), (0.0, 8.5, 0.0), DK)
    r.glow(head, "AntennaLight", (0.45, 0.45, 0.45), (0.0, 9.1, 0.0), "ff3b3b", ori(35, 45, 0))
    for s, side in ((-1, "L"), (1, "R")):
        arm = r.joint("Arm" + side, body, (s * 1.95, 5.4, 0.0), (1.2, 1.0, 1.2), (s * 2.1, 5.45, 0.0), RD[0])
        r.add(arm, "Arm", (0.8, 2.0, 0.8), (s * 2.15, 4.2, 0.0), TIN[1])
        for k in (-1, 1):
            r.add(arm, "Claw", (0.3, 0.7, 0.55), (s * 2.15 + k * 0.22, 2.85, 0.0), RD[1], G.rz(k * 12))
    return r.done(9.35, 4.0)


# ==================================================================== 12. Candy: the jelly slime (Hop)

def jelly_slime(sc, parent, base=None):
    r = Beast(sc, parent, "Candy", "Hop", base)
    PK = ("ff6fae", "e8559a", "ff9ccc", "ffd0e8")
    SPR = ("ffd447", "4ff0ff", "7cd860", "ffffff", "8a5cff", "ff8a1f")
    body = r.joint("Body", "Root", (0.0, 0.0, 0.0), (5.2, 2.2, 3.2), (0.0, 1.1, 0.0), PK[1])
    r.add(body, "Jelly", (3.2, 2.18, 5.0), (0.0, 1.1, 0.0), PK[1])
    r.add(body, "Jelly", (4.5, 2.16, 4.4), (0.0, 1.1, 0.0), PK[0])
    for (x, z, a) in ((-2.45, -1.3, 20), (2.2, -1.7, -15), (0.9, 2.45, 40)):
        r.add(body, "Drip", (0.9, 0.42, 0.9), (x, 0.21, z), PK[2], G.ry(a))
    top = r.joint("Top", body, (0.0, 2.2, 0.0), (4.2, 2.0, 2.8), (0.0, 3.1, 0.0), PK[0])
    r.add(top, "Jelly", (2.8, 1.98, 4.0), (0.0, 3.1, 0.0), PK[0])
    r.add(top, "Jelly", (3.7, 1.96, 3.5), (0.0, 3.1, 0.0), PK[2])
    r.add(top, "Jelly", (3.0, 1.0, 2.0), (0.0, 4.55, 0.05), PK[2])
    r.add(top, "Jelly", (2.0, 0.98, 3.0), (0.0, 4.55, 0.05), PK[2])
    r.add(top, "Jelly", (2.6, 0.96, 2.6), (0.0, 4.55, 0.05), PK[3])
    r.pl(top, "Shine", (0.8, 0.3, 0.1), (-1.2, 4.0, -2.04), PK[3], G.rz(20))
    r.pl(top, "Shine", (0.3, 0.3, 0.1), (-0.65, 4.2, -2.04), PK[3])
    for i, (x, z, a) in enumerate(((-0.8, -0.6, 20), (0.5, -0.8, -40), (1.0, 0.3, 75), (-0.9, 0.6, -10),
                                   (0.1, 0.0, 50), (-0.2, 1.0, 110))):
        r.add(top, "Sprinkle", (0.18, 0.18, 0.55), (x, 5.12, z + 0.1), SPR[i], ori(0, a, 0))
    r.add(top, "Cherry", (0.9, 0.9, 0.9), (0.35, 5.5, 0.25), "e8303a", ori(20, 45, 0))
    r.add(top, "Stem", (0.12, 0.8, 0.12), (0.5, 6.15, 0.3), "4c8030", G.rz(-20))
    head = r.hold("Head", top, (0.0, 3.2, -2.0))
    for s in (-1, 1):
        r.eye(head, s * 0.85, 3.5, -2.0, 0.9, 1.05, pupil=(0.5, 0.66), pdx=-s * 0.05)
        r.pl(head, "Cheek", (0.5, 0.26, 0.1), (s * 1.55, 2.95, -2.02), PK[1])
    r.pl(head, "Mouth", (1.3, 0.45, 0.1), (0.0, 2.65, -2.03), "5a1030")
    r.pl(head, "Tongue", (0.6, 0.22, 0.1), (0.15, 2.52, -2.07), "ff3b6b")
    return r.done(6.55, 4.0)


# ==================================================================== 13. Clock: the clockwork beetle (Scuttle)

def clock_beetle(sc, parent, base=None):
    r = Beast(sc, parent, "Clock", "Scuttle", base)
    BR = ("c9a24a", "a8842e", "e6c46a")
    CU = ("b8733a", "9a5a2a")
    STL = ("5a5a66", "3a3a44")
    body = r.joint("Body", "Root", (0.0, 2.2, 0.4), (4.0, 1.9, 3.4), (0.0, 2.85, 0.6), BR[0])
    r.add(body, "Shell", (2.8, 1.88, 5.0), (0.0, 2.85, 0.6), BR[1])
    r.add(body, "Shell", (3.6, 1.86, 4.4), (0.0, 2.85, 0.6), BR[2])
    r.add(body, "Shell", (2.6, 0.5, 3.6), (0.0, 3.95, 0.75), BR[0])
    r.add(body, "Seam", (0.16, 0.12, 3.62), (0.0, 4.25, 0.7), STL[1])
    r.add(body, "Under", (3.4, 0.7, 4.2), (0.0, 1.75, 0.6), STL[0])
    for (x, z) in ((-1.0, -0.6), (1.0, -0.6), (-1.0, 2.0), (1.0, 2.0)):
        r.add(body, "Rivet", (0.3, 0.12, 0.3), (x, 4.24, z), CU[0])
    gc = np.array((0.0, 5.0, 1.2))                                 # a gear standing up out of its back
    gear = r.joint("Gear", body, gc, (0.3, 2.4, 1.4), gc, BR[2])
    r.add(gear, "Gear", (0.32, 1.4, 2.4), gc, BR[2])
    r.add(gear, "Gear", (0.31, 2.0, 2.0), gc, BR[0], G.rx(45))
    for k in range(8):                                              # its teeth
        a_ = math.radians(22.5 + 45 * k)
        r.add(gear, "Tooth", (0.26, 0.5, 0.5), gc + np.array((0.0, 1.38 * math.cos(a_), 1.38 * math.sin(a_))), BR[1],
              G.rx(math.degrees(a_)))
    r.add(gear, "Hub", (0.5, 0.7, 0.7), gc, CU[0], G.rx(45))
    head = r.joint("Head", body, (0.0, 2.6, -1.6), (2.4, 1.5, 1.5), (0.0, 2.6, -2.3), STL[0])
    r.seg(head, "Horn", (0.0, 3.1, -2.6), (0.0, 4.1, -3.4), 0.5, 0.5, CU[0], 0.3)
    r.seg(head, "Horn", (0.0, 4.05, -3.35), (0.0, 4.75, -3.1), 0.38, 0.38, CU[1], 0.2)
    for s in (-1, 1):
        r.eye(head, s * 0.58, 2.75, -3.05, 0.58, 0.58, pupil=(0.24, 0.3), glow="ffc94a", dark=INK, glint=None)
        r.add(head, "Mandible", (0.28, 0.28, 0.8), (s * 0.5, 1.95, -3.2), BR[1], G.ry(s * 20))
    for s, side in ((-1, "L"), (1, "R")):
        for i, z in enumerate((-0.9, 0.6, 2.1)):
            hip = np.array((s * 1.6, 2.0, z))
            knee = np.array((s * 2.9, 2.6, z - 0.3 + 0.3 * i))
            foot = np.array((s * 3.6, 0.05, z - 0.6 + 0.6 * i))
            leg = r.hold("Leg%s%d" % (side, i + 1), body, hip)
            r.seg(leg, "Leg", hip, knee, 0.42, 0.42, STL[0], 0.3)
            r.seg(leg, "Leg", knee, foot, 0.36, 0.36, CU[1], 0.2)
    return r.done(6.25, 5.5)


# ==================================================================== 14. Neon: the patrol drone (Float)

def patrol_drone(sc, parent, base=None):
    r = Beast(sc, parent, "Neon", "Float", base)
    DK = ("2b2b3a", "1d1d28", "3c3c50")
    MG, CY = "ff2bd6", "2bf0ff"
    body = r.joint("Body", "Root", (0.0, 4.6, 0.0), (3.6, 1.8, 2.2), (0.0, 4.6, 0.0), DK[0])
    r.add(body, "Body", (2.2, 1.78, 3.6), (0.0, 4.6, 0.0), DK[0])
    r.add(body, "Body", (3.1, 1.76, 3.1), (0.0, 4.6, 0.0), DK[2], G.ry(45))
    r.add(body, "Cap", (2.4, 0.6, 2.4), (0.0, 5.75, 0.0), DK[2])
    r.glow(body, "Band", (3.66, 0.24, 2.26), (0.0, 4.6, 0.0), CY)
    r.glow(body, "Band", (2.26, 0.25, 3.66), (0.0, 4.6, 0.0), CY)
    r.add(body, "Light", (1.4, 0.6, 1.4), (0.0, 3.5, 0.0), DK[1])
    r.glow(body, "Searchlight", (1.0, 0.12, 1.0), (0.0, 3.16, 0.0), "e8faff")
    for s in (-1, 1):
        r.add(body, "Fin", (0.2, 1.1, 1.2), (s * 0.7, 5.9, 1.3), DK[2], G.rz(-s * 20))
    r.add(body, "Antenna", (0.14, 1.2, 0.14), (0.6, 6.6, 0.4), DK[2])
    r.glow(body, "AntennaLight", (0.36, 0.36, 0.36), (0.6, 7.3, 0.4), MG, ori(35, 45, 0))
    for (sx, sz, nm) in ((-1, -1, "RotorFL"), (1, -1, "RotorFR"), (-1, 1, "RotorBL"), (1, 1, "RotorBR")):
        c = np.array((sx * 2.7, 5.05, sz * 2.7))
        r.seg(body, "Arm", (sx * 1.1, 4.8, sz * 1.1), c - np.array((sx * 0.5, 0.0, sz * 0.5)), 0.4, 0.3, DK[2],
              xhint=(0, 1, 0))
        r.add(body, "Rotor", (1.2, 0.36, 1.2), c, DK[1], G.ry(45))
        rotor = r.joint(nm, body, c, (2.6, 0.08, 0.36), c + np.array((0, 0.25, 0)), MG if sz < 0 else CY, G.ry(20))
        r.add(rotor, "Blade", (0.36, 0.09, 2.6), c + np.array((0, 0.25, 0)), DK[2], G.ry(20))
    head = r.joint("Head", body, (0.0, 4.4, -1.4), (1.7, 1.5, 1.0), (0.0, 4.4, -1.9), DK[1])
    r.eye(head, 0.0, 4.45, -2.4, 0.95, 0.95, pupil=(0.24, 0.72), glow="ff3b5c", dark=INK, glint=0.18,
          shut=(1.0, 0.2))
    return r.done(7.5, 7.0)


# ==================================================================== 15. Cloud: the storm cloud (Float)

def storm_cloud(sc, parent, base=None):
    r = Beast(sc, parent, "Cloud", "Float", base)
    CL = ("6a7080", "556070", "8a92a2", "a6aebc")
    body = r.joint("Body", "Root", (0.0, 5.2, 0.0), (4.6, 3.0, 2.2), (0.0, 5.6, 0.0), CL[0])
    r.add(body, "Puff", (2.8, 2.98, 3.6), (0.0, 5.6, 0.0), CL[1])
    r.add(body, "Puff", (4.0, 2.96, 3.2), (0.0, 5.6, 0.0), CL[2])
    r.rnd(body, "Puff", 2.6, 2.0, 2.4, (-0.9, 7.3, 0.3), (CL[2], CL[3], CL[0]))
    r.rnd(body, "Puff", 2.0, 1.6, 2.0, (1.1, 7.15, 0.0), (CL[0], CL[2], CL[3]))
    for s, side in ((-1, "L"), (1, "R")):
        puff = r.joint("Puff" + side, body, (s * 2.0, 5.2, 0.0), (2.6, 2.2, 1.8), (s * 2.6, 5.0, -0.36), CL[1])
        r.add(puff, "Puff", (1.8, 2.18, 2.6), (s * 2.6, 5.0, -0.36), CL[2])
        r.add(puff, "Puff", (2.3, 2.16, 2.3), (s * 2.6, 5.0, -0.36), CL[0])
    head = r.hold("Head", body, (0.0, 5.6, -1.8))
    fz = -1.8
    for s in (-1, 1):
        r.eye(head, s * 0.75, 6.0, fz, 0.7, 0.62, pupil=(0.36, 0.42), pdx=-s * 0.05, pdy=-0.08)
        r.pl(head, "Brow", (0.85, 0.2, 0.1), (s * 0.72, 6.5, fz - 0.03), "2b2f3a", G.rz(s * 22))
    r.pl(head, "Mouth", (0.6, 0.18, 0.1), (-0.27, 5.05, fz - 0.02), "2b2f3a", G.rz(12))
    r.pl(head, "Mouth", (0.6, 0.18, 0.1), (0.27, 5.05, fz - 0.025), "2b2f3a", G.rz(-12))
    bolt = r.hold("Bolt", body, (0.6, 4.1, -0.2))
    for i, (a, b_, ) in enumerate((((0.7, 4.2, -0.2), (0.1, 3.0, -0.2)), ((0.1, 3.05, -0.2), (0.75, 2.4, -0.2)),
                                   ((0.7, 2.45, -0.2), (0.1, 1.2, -0.2)))):
        r.seg(bolt, "Bolt", a, b_, 0.36, 0.26 if i == 1 else 0.3, "ffe34a", 0.18)
    for p_ in r.groups["Bolt"].children:
        if p_.kind == "Part" and p_.name == "Bolt":
            p_.p["material"] = "Neon"
            p_.p["surfaces"] = "smooth"
            p_.p["shadow"] = False
    rain = r.hold("Rain", body, (0.0, 3.6, 0.0))
    for (x, y, z) in ((-1.6, 3.2, -0.6), (-0.8, 2.5, 0.7), (-2.3, 2.2, 0.4), (1.7, 2.9, 0.6), (2.4, 2.3, -0.4),
                      (-1.2, 2.0, -0.2)):
        r.add(rain, "Rain", (0.18, 0.55, 0.18), (x, y, z), "8cc8ff")
    return r.done(8.4, 7.0)


# ==================================================================== 16. Cosmic: the star hound (Gallop)

def star_hound(sc, parent, base=None):
    r = Beast(sc, parent, "Cosmic", "Gallop", base)
    NV = ("2a2a6a", "3a3a8a", "1e1e4a")
    PU, PK, ST = "8a5cff", "ff6fd8", "ffe34a"
    body = r.joint("Body", "Root", (0.0, 3.3, 0.4), (2.6, 2.4, 5.4), (0.0, 3.4, 0.5), NV[0])
    r.add(body, "Chest", (2.8, 2.6, 1.6), (0.0, 3.55, -2.1), NV[1])
    r.add(body, "Belly", (2.0, 0.6, 4.2), (0.0, 2.15, 0.4), PU)
    for (z, k) in ((-0.9, 1.0), (0.9, 0.8), (2.4, 0.9)):               # stars on its back
        r.glow(body, "Star", (0.22 * k, 0.1, 1.1 * k), (0.15 * z, 4.66, z), ST, G.ry(20 * z))
        r.glow(body, "Star", (1.1 * k, 0.11, 0.22 * k), (0.15 * z, 4.68, z), ST, G.ry(20 * z))
    r.add(body, "Collar", (2.9, 0.5, 1.5), (0.0, 4.3, -2.35), PK, G.rx(-15))
    r.glow(body, "Tag", (0.5, 0.5, 0.12), (0.0, 3.8, -3.15), ST, G.rz(45))
    head = r.joint("Head", body, (0.0, 4.2, -2.6), (2.4, 2.2, 2.2), (0.0, 4.95, -3.5), NV[0])
    r.add(head, "Snout", (1.4, 1.0, 1.4), (0.0, 4.45, -4.9), NV[1])
    r.add(head, "Nose", (0.6, 0.4, 0.3), (0.0, 4.95, -5.6), "101020")
    for s in (-1, 1):
        r.add(head, "Ear", (0.7, 1.4, 0.4), (s * 1.25, 5.6, -3.3), NV[2], G.rz(s * 28))
        r.add(head, "Ear", (0.4, 0.9, 0.1), (s * 1.27, 5.55, -3.52), PU, G.rz(s * 28))
        r.eye(head, s * 0.58, 5.4, -4.6, 0.6, 0.66, pupil=(0.34, 0.46), pdx=-s * 0.03, dark=PU)
        r.glow(head, "Freckle", (0.14, 0.14, 0.1), (s * 0.95, 4.75, -4.62), ST, G.rz(45))
    jaw = r.joint("Jaw", head, (0.0, 4.1, -4.1), (1.2, 0.45, 1.2), (0.0, 3.85, -4.95), NV[1])
    r.pl(jaw, "Tongue", (0.5, 0.1, 0.7), (0.15, 4.1, -5.1), PK)
    for s in (-1, 1):
        for z, side in ((-2.2, "F"), (2.3, "B")):
            name = "Leg%s%s" % (side, "L" if s < 0 else "R")
            leg = r.joint(name, body, (s * 0.9, 3.1, z), (0.85, 2.6, 0.95), (s * 0.9, 1.65, z), NV[1])
            r.add(leg, "Paw", (1.05, 0.5, 1.3), (s * 0.9, 0.25, z - 0.15), PU)
    tail = r.joint("Tail", body, (0.0, 4.2, 3.2), (0.7, 0.7, 1.8), (0.0, 4.55, 3.95), NV[1], G.rx(-30))
    r.add(tail, "Tail", (0.6, 0.6, 1.2), (0.0, 5.3, 4.8), NV[0], G.rx(-50))
    r.glow(tail, "TailStar", (0.75, 0.75, 0.3), (0.0, 5.75, 5.3), ST, G.rz(45))
    return r.done(6.6, 9.0)


# ==================================================================== 17. Void: the glitch cube (Hop)

def glitch_cube(sc, parent, base=None):
    r = Beast(sc, parent, "Void", "Hop", base)
    BK = ("1a1a22", "24242e", "101016")
    MG, CY, WH = "ff2bd6", "2bf0ff", "ffffff"
    S, H, y0 = 5.0, 1.8, 0.3
    body = r.joint("Body", "Root", (0.0, 0.0, 0.0), (S, H, S), (0.0, y0 + H / 2, 0.0), BK[0])
    mid = r.joint("SliceMid", body, (0.0, y0 + H, 0.0), (S, H - 0.02, S), (0.0, y0 + 1.5 * H, 0.0), BK[1])
    top = r.joint("SliceTop", body, (0.0, y0 + 2 * H, 0.0), (S, H - 0.04, S), (0.0, y0 + 2.5 * H, 0.0), BK[0])
    for g, k in ((body, 0), (mid, 1), (top, 2)):                    # lit edges, magenta and cyan
        y = y0 + (k + 0.5) * H
        for sx in (-1, 1):
            for sz in (-1, 1):
                r.glow(g, "Edge", (0.24, H - 0.05 - 0.01 * k, 0.24), (sx * (S / 2 - 0.08), y, sz * (S / 2 - 0.08)),
                       MG if (sx * sz > 0) == (k % 2 == 0) else CY)
    for i, (x, z, w, d) in enumerate(((0.0, -S / 2 + 0.08, S - 0.2, 0.2), (0.0, S / 2 - 0.08, S - 0.2, 0.2),
                                      (-S / 2 + 0.08, 0.0, 0.2, S - 0.2), (S / 2 - 0.08, 0.0, 0.2, S - 0.2))):
        r.glow(top, "Edge", (w, 0.22 if i < 2 else 0.2, d), (x, y0 + 3 * H - 0.1, z), CY if i < 2 else MG)
    head = r.hold("Head", top, (0.0, y0 + 2.5 * H, -S / 2))
    fz = -S / 2
    for s in (-1, 1):
        r.eye(head, s * 0.95, y0 + 2.5 * H, fz, 0.8, 0.8, pupil=(0.32, 0.32), pdx=-s * 0.12, pdy=-0.1, glow=WH,
              dark=BK[2], glint=None, shut_col=MG, shut_glow=True, shut=(0.8, 0.2))
    for i, x in enumerate((-0.6, -0.2, 0.2, 0.6)):
        r.glow(mid, "Mouth", (0.36, 0.36, 0.1), (x, y0 + 1.6 * H + (0.18 if i % 2 else 0.0), fz - 0.05), CY)
    bits = r.hold("Bits", body, (0.0, y0 + 3 * H + 0.8, 0.0))
    for (x, y, z, w, c) in ((-2.2, 6.6, -1.0, 0.6, MG), (1.9, 6.9, 0.4, 0.5, CY), (0.4, 7.4, 1.6, 0.45, WH),
                            (-1.0, 7.1, 1.9, 0.5, BK[1]), (2.9, 4.6, -1.4, 0.55, MG), (-3.0, 3.5, 1.2, 0.5, CY)):
        if c == BK[1]:
            r.add(bits, "Bit", (w, w, w), (x, y, z), c, ori(20, 30, 10))
        else:
            r.glow(bits, "Bit", (w, w, w), (x, y, z), c, ori(20, 30, 10))
    return r.done(7.6, 4.0)


# ==================================================================== 18. Olympus: the marble lion (Gallop)

def marble_lion(sc, parent, base=None):
    r = Beast(sc, parent, "Olympus", "Gallop", base)
    MB = ("f0ece4", "ddd6ca", "faf8f2", "c8c0b4")
    GD = ("ffd447", "e0a800")
    LF = "9ab84a"
    body = r.joint("Body", "Root", (0.0, 3.5, 0.5), (2.8, 2.6, 5.4), (0.0, 3.6, 0.6), MB[0])
    r.add(body, "Chest", (3.0, 2.8, 1.6), (0.0, 3.75, -2.0), MB[1])
    r.add(body, "Belly", (2.2, 0.6, 4.2), (0.0, 2.3, 0.6), MB[3])
    r.pl(body, "Vein", (0.1, 0.9, 2.2), (1.42, 3.9, 1.2), MB[3], G.rx(30))
    r.pl(body, "Vein", (0.1, 0.7, 1.6), (-1.42, 3.4, 0.2), MB[3], G.rx(-25))
    head = r.joint("Head", body, (0.0, 4.6, -2.4), (2.4, 2.2, 2.2), (0.0, 5.3, -3.4), MB[0])
    MN = ("e2cfa8", "cdb68a", "eedcb8")                             # the mane in warmer, sandier marble
    r.add(head, "Mane", (4.2, 3.4, 2.0), (0.0, 5.35, -2.65), MN[0])
    r.add(head, "Mane", (3.4, 4.2, 1.98), (0.0, 5.35, -2.65), MN[1])
    r.add(head, "Mane", (3.9, 3.9, 1.96), (0.0, 5.35, -2.65), MN[2], G.rz(45))
    r.add(head, "Muzzle", (1.6, 1.0, 1.0), (0.0, 4.75, -4.85), MB[2])
    r.add(head, "Nose", (0.7, 0.42, 0.3), (0.0, 5.18, -5.4), GD[1])
    for s in (-1, 1):
        r.eye(head, s * 0.56, 5.75, -4.5, 0.58, 0.62, pupil=(0.32, 0.44), pdx=-s * 0.03, white=GD[0], dark=INK)
        r.pl(head, "Brow", (0.66, 0.16, 0.1), (s * 0.56, 6.22, -4.53), MB[3], G.rz(-s * 14))
        for k, a in enumerate((25, 60)):                         # a golden laurel round the brow
            r.add(head, "Laurel", (0.9, 0.18, 0.45), (s * (0.7 + 0.45 * k), 6.75 - 0.25 * k, -3.7 + 0.2 * k),
                  GD[0] if k == 0 else LF, ori(0, s * a, -s * 20))
    r.add(head, "Laurel", (0.5, 0.5, 0.2), (0.0, 6.75, -4.0), GD[0], G.rz(45))
    jaw = r.joint("Jaw", head, (0.0, 4.4, -4.2), (1.3, 0.45, 1.1), (0.0, 4.1, -4.85), MB[1])
    r.pl(jaw, "Mouth", (1.0, 0.1, 0.8), (0.0, 4.36, -4.85), "b04a4a")
    for s in (-1, 1):
        for z, side in ((-2.0, "F"), (2.5, "B")):
            name = "Leg%s%s" % (side, "L" if s < 0 else "R")
            leg = r.joint(name, body, (s * 1.0, 3.3, z), (0.95, 2.8, 1.05), (s * 1.0, 1.75, z), MB[0])
            r.add(leg, "Paw", (1.2, 0.55, 1.45), (s * 1.0, 0.275, z - 0.15), MB[2])
    tail = r.joint("Tail", body, (0.0, 4.4, 3.4), (0.45, 0.45, 2.2), (0.0, 4.9, 4.3), MB[1], G.rx(-28))
    r.add(tail, "Tuft", (0.9, 0.9, 0.9), (0.0, 5.55, 5.35), GD[0], ori(20, 45, 0))
    return r.done(7.2, 9.0)


AREAS = [("Meadow", "Meadow Patch", scarecrow), ("Dunes", "Sandy Dunes", scorpion), ("Marsh", "Mushroom Marsh", frog),
         ("Jungle", "Jungle Ruins", tiger), ("Reef", "Coral Cove", crab), ("Frost", "Frost Fields", snow_golem),
         ("Haunt", "Haunted Hollow", ghost), ("Lava", "Lava Furrows", magma_golem),
         ("Crystal", "Crystal Caverns", crystal_spider), ("Dino", "Dino Valley", raptor), ("Toy", "Toy Town", toy_robot),
         ("Candy", "Candy Crops", jelly_slime), ("Clock", "Clockwork Yard", clock_beetle),
         ("Neon", "Neon City", patrol_drone), ("Cloud", "Cloud Kingdom", storm_cloud),
         ("Cosmic", "Cosmic Garden", star_hound), ("Void", "Glitch Void", glitch_cube),
         ("Olympus", "Spud Olympus", marble_lion)]
