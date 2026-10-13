"""Lava Furrows potatoes, worst to best: CharredChip, MagmaMash, PepperPotato, EmberImp, VolcanoSpud,
InfernoTuber. Same rig, features and rules as the Meadow Patch kinds (spuds.py).

The dark ones (charcoal, rock) have light or glowing eyes so their faces read, and everything that
should show at level 10 (flames, lava, horns) stands clear of the crown."""
import numpy as np

import spsgeo as G

from .bricks import ori
from .spuds import (INK, Kind, arms, crown, dimples, eyes, legs, mouth_smile, octo, sprout)

EMBER = ("ff7a1a", "ffb02a", "ff4a1a")


def stick(sp, a, b, w, col, n=(0.0, 0.0, -1.0), t=0.1, material="Neon"):
    """A bar from a to b, w wide and t thick, its thin side facing n (a crack, a lava run, a tail)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = b - a
    L = float(np.linalg.norm(d))
    y = d / L
    z = np.asarray(n, float)
    z = z - y * (z @ y)
    z /= np.linalg.norm(z)
    x = np.cross(y, z)
    return sp.extra((w, L, t), (a + b) / 2, np.column_stack((x, y, z)), col, material=material)


def crack(sp, pts, n, w=0.13, col=EMBER[0], out=0.03):
    """A jagged glowing crack through the points (on a face whose outward normal is n), each bar a
    hair further out than the last so the joints never fight."""
    n = np.asarray(n, float)
    for i in range(len(pts) - 1):
        o = n * (out + 0.012 * (i % 2))
        a, b = np.asarray(pts[i], float), np.asarray(pts[i + 1], float)
        e = (b - a) / np.linalg.norm(b - a) * (w * 0.4)
        stick(sp, a - e + o, b + e + o, w, col, n=n)


def glow_eyes(sp, col, glint_col=INK, w=0.5, hgt=0.66, glint=0.2):
    """Two glowing eyes (Neon) with a dark glint each, on the face like eyes()."""
    f = sp.kind.face
    z, y, dx = f["z"], f["eye_y"], f["eye_dx"]
    h = sp.holder("Eyes", (0.0, y, z))
    for s in (1, -1):
        ex = s * dx
        sp.plate(h, "Eye", (w, hgt, 0.1), (ex, y, z - 0.04), color=col, material="Neon")
        sp.plate(h, "Glint", (glint, glint, 0.1), (ex - w / 2 + glint / 2 + 0.06, y - hgt / 2 + glint / 2 + 0.07,
                                                   z - 0.09), color=glint_col)
    return h


def soot_eyes(sp, w=0.52, hgt=0.62, pupil=(0.26, 0.32), col="fff4e0"):
    """Wide white eyes with dark pupils glancing to one side: a sooty face after a bang."""
    f = sp.kind.face
    z, y, dx = f["z"], f["eye_y"], f["eye_dx"]
    h = sp.holder("Eyes", (0.0, y, z))
    for s in (1, -1):
        ex = s * dx
        sp.plate(h, "Eye", (w, hgt, 0.1), (ex, y, z - 0.04), color=col)
        sp.plate(h, "Pupil", (pupil[0], pupil[1], 0.1), (ex - 0.08, y - 0.05, z - 0.09))
    return h


def glow_mouth(sp, col, width=0.6, hgt=0.26, cheeks=None):
    f = sp.kind.face
    z, y = f["z"], f["mouth_y"]
    h = sp.holder("Mouth", (0.0, y, z))
    sp.plate(h, "Mouth", (width, hgt, 0.1), (0.0, y, z - 0.04), color=col, material="Neon")
    if cheeks:
        for s in (-1, 1):
            sp.plate(h, "Cheek", (0.42, 0.22, 0.1), (s * f.get("cheek_dx", 0.84), y + 0.36, z - 0.025), color=cheeks)
    return h


def chamfer_normal(w, d, front, chamfer, side=1):
    """Outward normal of an octo's front chamfer (side +1 its right, -1 its left) and the middle of
    that face in plan (x, z)."""
    sd = d - 2 * chamfer
    ax, az = (w - front) / 2, (d - sd) / 2
    ln = float(np.hypot(ax, az))
    n = np.array((side * az / ln, 0.0, -ax / ln))
    mid = np.array((side * (front / 2 + w / 2) / 2, 0.0, -(d / 2 + sd / 2) / 2))
    return n, mid


class CharredChipKind(Kind):
    """A chunky chip burnt black as charcoal: square-cut, its top crusted with ash, embers glowing
    orange all over it, a wisp of smoke, and wide white eyes in its sooty face."""
    pid, display, rarity, area = "CharredChip", "Charred Chip", "Rare", "Lava"
    skin = ("2e2828", "221e1e", "4a4242")
    limb = "221e1e"
    shoe = "4a3c38"
    face = dict(z=-1.1, eye_y=2.5, eye_dx=0.5, mouth_y=1.72)
    shoulder = (1.25, 2.2)
    head = (0.0, 3.86, 0.0)
    leg_h = 1.0

    def body(self, sp):
        mid, dark, light = self.skin
        sp.core((2.5, 3.3, 2.2), (0.0, 1.85, 0.0), None, mid)                               # the chip
        sp.extra((2.64, 3.04, 1.9), (0.0, 1.82, 0.04), None, dark)                         # its burnt sides
        sp.extra((2.58, 0.44, 2.3), (0.0, 3.56, 0.0), G.rz(-5), light)                     # the cut end, crusted
        sp.extra((0.66, 0.1, 0.5), (-0.42, 3.83, 0.25), ori(0, 20, -5), "a8a2a0")          # ash
        for pos, n, sz, col in (((0.82, 0.62, -1.1), (0, 0, -1), 0.34, EMBER[0]),         # embers
                                ((-0.78, 1.02, -1.1), (0, 0, -1), 0.26, EMBER[1]),
                                ((0.93, 3.08, -1.1), (0, 0, -1), 0.22, EMBER[1]),
                                ((-0.46, 0.46, -1.1), (0, 0, -1), 0.18, EMBER[2]),
                                ((1.32, 2.3, 0.15), (1, 0, 0), 0.36, EMBER[0]),
                                ((1.32, 1.05, -0.45), (1, 0, 0), 0.24, EMBER[1]),
                                ((-1.32, 1.5, -0.3), (-1, 0, 0), 0.32, EMBER[0])):
            n = np.asarray(n, float)
            R = G.rz(45) if n[2] else G.ry(90 * n[0]) @ G.rz(45)
            sp.extra((sz, sz, 0.1), np.asarray(pos) + n * 0.03, R, col, material="Neon")
        sp.extra((0.52, 0.46, 0.52), (0.78, 4.25, 0.62), ori(10, 30, 15), "8a8484")         # a wisp of smoke
        sp.extra((0.36, 0.34, 0.36), (1.02, 4.78, 0.8), ori(-10, 60, -10), "b4aeae")

    def features(self, sp):
        dimples(sp, col="5a4c48")
        soot_eyes(sp)
        glow_mouth(sp, EMBER[0], width=0.56, hgt=0.24)
        arms(sp, self.limb, hand="4a3c38")
        legs(sp, self.limb, self.shoe)
        sprout(sp, at=(-0.2, 3.86, 0.0))
        crown(sp, jewel=EMBER[0])


class MagmaMashKind(Kind):
    """A lump of dark rock split by glowing lava cracks, rocks heaped on its head, its eyes and mouth
    glowing like the lava inside."""
    pid, display, rarity, area = "MagmaMash", "Magma Mash", "Epic", "Lava"
    skin = ("3e3434", "2c2525", "524644")
    limb = "2c2525"
    shoe = "5a4038"
    face = dict(z=-1.45, eye_y=2.32, eye_dx=0.5, mouth_y=1.52)
    shoulder = (1.6, 1.8)
    head = (0.0, 3.6, 0.0)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        W, D, F, C = 3.2, 2.9, 2.0, 0.6
        octo(sp, 0.35, 2.95, W, D, F, C, (mid, dark, light), core=True)
        sp.extra((2.45, 0.7, 2.2), (0.0, 3.1, 0.0), ori(0, -8, 3), light)
        sp.extra((1.3, 0.9, 1.35), (-0.95, 3.22, 0.35), ori(8, 32, 12), mid)                 # rocks heaped on top
        sp.extra((1.0, 0.72, 1.05), (1.05, 3.16, 0.15), ori(-6, -24, -14), dark)
        z = -D / 2                                                                         # lava cracks
        crack(sp, [(1.0, 2.0, z), (0.78, 1.55, z), (0.9, 1.05, z), (0.58, 0.4, z)], (0, 0, -1))
        crack(sp, [(-0.3, 0.38, z), (-0.6, 0.66, z), (-1.0, 0.8, z)], (0, 0, -1), col=EMBER[1])
        for s, (t0, t1, y0, y1), col in ((1, (-0.4, 0.15, 2.0, 2.9), EMBER[0]), (-1, (-0.4, 0.2, 0.8, 1.55), EMBER[1])):
            n, mid_ = chamfer_normal(W, D, F, C, s)                                         # on round the corners
            u = np.array((-n[2], 0.0, n[0])) * s
            crack(sp, [mid_ + u * t0 + (0, y0, 0), mid_ + u * t1 + (0, y1, 0)], n, col=col)
        crack(sp, [(W / 2, 2.6, 0.55), (W / 2, 1.45, 0.25)], (1, 0, 0), col=EMBER[2])
        crack(sp, [(-W / 2, 2.45, -0.3), (-W / 2, 1.55, 0.2)], (-1, 0, 0), col=EMBER[0])

    def features(self, sp):
        dimples(sp, col="5a4038")
        glow_eyes(sp, "ffc83a", w=0.52, hgt=0.5)
        glow_mouth(sp, EMBER[0], width=0.7)
        arms(sp, self.limb, hand="5a4038")
        legs(sp, self.limb, self.shoe)
        sprout(sp, at=(0.1, 3.5, 0.0))
        crown(sp, jewel=EMBER[0])


class PepperPotatoKind(Kind):
    """A bright red chilli pepper of a potato: tall and glossy, narrowing to a point that curls away
    behind it, a star-shaped green calyx on top and its stem burning like a fuse."""
    pid, display, rarity, area = "PepperPotato", "Pepper Potato", "Epic", "Lava"
    skin = ("e8302a", "c0221e", "ff5a48")
    limb = "c0221e"
    shoe = "4c8030"
    face = dict(z=-1.2, eye_y=2.8, eye_dx=0.45, mouth_y=2.05, cheek_dx=0.8)
    shoulder = (1.35, 2.25)
    head = (0.0, 3.98, 0.0)
    leg_h = 1.35

    def body(self, sp):
        mid, dark, light = self.skin
        W, D, F, C = 2.7, 2.4, 1.7, 0.5
        octo(sp, 1.0, 3.65, W, D, F, C, (mid, dark, light), core=True)
        sp.extra((2.0, 0.78, 1.8), (0.0, 0.64, 0.0), None, dark)                            # narrowing
        sp.extra((0.62, 0.56, 1.1), (0.15, 0.52, 1.05), ori(-28, 12, 0), dark)              # to a point curled back
        n, mid_ = chamfer_normal(W, D, F, C, 1)
        sp.extra((0.2, 1.5, 0.1), mid_ + (0, 2.5, 0) + n * 0.03, G.ry(-45), "ffbcb2",
                 material="SmoothPlastic")                                                    # glossy
        sp.extra((2.3, 0.34, 2.1), (0.0, 3.72, 0.0), G.ry(20), "4c8030")                    # star-shaped calyx
        sp.extra((2.3, 0.3, 2.1), (0.0, 3.69, 0.0), G.ry(65), "3e6a2a")
        sp.extra((0.42, 0.95, 0.42), (0.06, 4.25, 0.0), G.rz(-10), "3e6a2a")                # its stem
        sp.extra((0.52, 0.8, 0.52), (0.17, 5.02, 0.0), ori(0, 45, -6), EMBER[0], material="Neon")   # alight
        sp.extra((0.3, 0.5, 0.3), (0.17, 4.9, -0.2), ori(0, 45, -6), EMBER[1], material="Neon")

    def features(self, sp):
        dimples(sp)
        eyes(sp, w=0.46, hgt=0.64)
        mouth_smile(sp, width=0.54)
        arms(sp, self.limb)
        legs(sp, self.limb, self.shoe)
        sprout(sp, at=(-0.62, 3.84, 0.3), lean=-16)
        crown(sp, jewel=EMBER[0])


class EmberImpKind(Kind):
    """A little red imp of a potato: two black horns, a pointed tail with a spade tip, one brow
    cocked and a lopsided grin."""
    pid, display, rarity, area = "EmberImp", "Ember Imp", "Legendary", "Lava"
    skin = ("d7372c", "b02a22", "f05a48")
    limb = "b02a22"
    shoe = "2b1e18"
    face = dict(z=-1.45, eye_y=2.28, eye_dx=0.5, mouth_y=1.5, cheek_dx=0.84)
    shoulder = (1.55, 1.8)
    head = (0.0, 3.55, 0.05)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 2.95, 3.2, 2.9, 2.0, 0.6, (mid, dark, light), core=True)
        sp.extra((2.45, 0.7, 2.2), (0.0, 3.1, 0.05), ori(0, -8, 3), light)
        horn = "1e1a22"
        for s in (-1, 1):                                                                # horns, out then up
            base = np.array((s * 0.98, 3.28, -0.25))
            Rb = G.rz(-s * 32)
            sp.extra((0.44, 0.64, 0.44), base + Rb @ (0, 0.32, 0), Rb @ G.ry(45), horn)
            top = base + Rb @ (0, 0.58, 0)
            Rt = G.rz(-s * 6)
            sp.extra((0.26, 0.52, 0.26), top + Rt @ (0, 0.22, 0), Rt @ G.ry(45), horn)
        stick(sp, (0.35, 0.95, 1.3), (1.78, 1.72, 2.05), 0.28, dark, n=(0, 0, 1), t=0.28,
              material="Plastic")                                                         # its pointed tail
        sp.extra((0.64, 0.64, 0.16), (1.92, 1.86, 2.1), ori(0, -25, 45), horn)            # its spade tip

    def features(self, sp):
        dimples(sp)
        eyes(sp, w=0.5, hgt=0.6, brows=(24.0, -16.0), brow_dy=(-0.02, 0.12))
        f = self.face
        z, y = f["z"], f["mouth_y"]
        h = sp.holder("Mouth", (0.0, y, z))                                             # a lopsided grin
        sp.plate(h, "Mouth", (0.9, 0.24, 0.1), (0.0, y, z - 0.04), G.rz(-6))
        sp.plate(h, "Mouth", (0.3, 0.22, 0.1), (0.52, y + 0.14, z - 0.03), G.rz(38))
        sp.plate(h, "Tooth", (0.18, 0.16, 0.1), (-0.2, y + 0.03, z - 0.09), G.rz(-6), color="ffffff")
        sp.plate(h, "Tooth", (0.18, 0.16, 0.1), (0.2, y - 0.01, z - 0.09), G.rz(-6), color="ffffff")
        arms(sp, self.limb, hand="2b1e18")
        legs(sp, self.limb, self.shoe)
        sprout(sp)
        crown(sp, jewel=EMBER[0])


class VolcanoSpudKind(Kind):
    """A small brown volcano of a potato: sloping flanks up to a crater full to the brim with lava,
    lava running down its sides and bubbles of it jumping out of the top."""
    pid, display, rarity, area = "VolcanoSpud", "Volcano Spud", "Mythic", "Lava"
    skin = ("8a5a3a", "6e4428", "a87050")
    limb = "6e4428"
    shoe = "3a2a22"
    face = dict(z=-1.6, eye_y=1.62, eye_dx=0.5, mouth_y=0.92, cheek_dx=0.86)
    shoulder = (2.12, 1.5)
    head = (0.0, 3.42, 0.0)
    leg_h = 1.1

    def body(self, sp):
        mid, dark, light = self.skin
        W, D, F, C = 3.4, 3.2, 2.2, 0.7
        octo(sp, 0.25, 2.3, W, D, F, C, (mid, dark, light), core=True)
        for s in (-1, 1):                                                                  # its sloping flanks
            R = G.rz(s * 18)
            c = np.array((s * 1.75, 1.45, 0.05))
            sp.extra((1.0, 2.6, 2.5), c, R, dark)
            top, bot = c + R @ (s * 0.26, 1.12, 0.0), c + R @ (s * 0.26, -1.1, 0.0)
            z = c[2] - 1.25 - 0.035
            stick(sp, (top[0], top[1], z), (bot[0], bot[1], z), 0.32, EMBER[0])             # lava running down
        sp.extra((2.5, 0.62, 2.3), (0.0, 2.55, 0.0), G.ry(12), light)                      # the cone narrowing
        sp.extra((1.85, 0.5, 1.7), (0.0, 3.08, 0.0), G.ry(-10), mid)                       # the crater's rim
        sp.extra((1.4, 0.28, 1.25), (0.0, 3.24, 0.0), G.ry(30), EMBER[1], material="Neon")  # lava to the brim
        sp.extra((0.5, 0.5, 0.5), (0.22, 4.22, -0.1), ori(20, 45, 10), EMBER[0], material="Neon")   # bubbles
        sp.extra((0.32, 0.32, 0.32), (-0.28, 4.8, 0.1), ori(-15, 30, 25), EMBER[1], material="Neon")

    def features(self, sp):
        dimples(sp)
        eyes(sp, w=0.5, hgt=0.62)
        mouth_smile(sp, width=0.6)
        arms(sp, self.limb)
        legs(sp, self.limb, self.shoe, shoe_size=(1.05, 0.56, 1.4))
        sprout(sp, at=(-0.55, 3.25, 0.45), lean=-12)
        crown(sp, jewel=EMBER[0])


def tongue(sp, base, leans, sizes, cols):
    """A tongue of flame: diamond-turned bricks stacked up from base, each leaning its own way
    (rz, rx) and narrower than the last."""
    p = np.asarray(base, float)
    for (lz, lx), (w, h), col in zip(leans, sizes, cols):
        R = G.rz(lz) @ G.rx(lx)
        sp.extra((w, h, w), p + R @ (0, h / 2, 0), R @ G.ry(45), col, material="Neon")
        p = p + R @ (0, h * 0.78, 0)


class InfernoTuberKind(Kind):
    """Made of blue and white flame: it glows all over, a mane of flame leaps up behind its crown,
    flames lick up its sides and its eyes glow white."""
    pid, display, rarity, area = "InfernoTuber", "Inferno Tuber", "Secret", "Lava"
    skin = ("2f74ff", "245ee0", "4a90ff")
    limb = "245ee0"
    shoe = "1a3fae"
    face = dict(z=-1.45, eye_y=2.32, eye_dx=0.5, mouth_y=1.52)
    shoulder = (1.55, 1.8)
    head = (0.0, 3.08, 0.0)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 2.95, 3.2, 2.9, 2.0, 0.6, (mid, dark, light), core=True, material="Neon")
        blue, cyan, white = "4a9cff", "8fd2ff", "e6f6ff"
        tongue(sp, (0.05, 2.9, 0.45), ((4, -8), (-12, -6), (14, -4)), ((1.1, 1.2), (0.75, 1.1), (0.42, 0.95)),
               (blue, cyan, white))                                                       # a mane of flame
        tongue(sp, (-0.82, 2.85, 0.3), ((20, -6), (-6, -4)), ((0.75, 1.0), (0.42, 0.9)), (blue, white))
        tongue(sp, (0.82, 2.85, 0.25), ((-18, -6), (5, -4)), ((0.7, 0.95), (0.4, 0.85)), (blue, white))
        for s in (-1, 1):                                                                  # flames up its sides
            tongue(sp, (s * 1.36, 2.55, -0.15), ((-s * 12, 0), (s * 8, 0)), ((0.55, 0.8), (0.3, 0.66)), (cyan, white))

    def features(self, sp):
        dimples(sp, col="1a3fae")
        glow_eyes(sp, "ffffff", glint_col="245ee0")
        mouth_smile(sp, width=0.6, cheeks=False)
        arms(sp, self.limb, hand="cfe6ff")
        legs(sp, self.limb, self.shoe)
        sprout(sp, at=(-0.3, 3.0, 0.0))
        crown(sp, jewel="2f74ff")


LAVA = [CharredChipKind(), MagmaMashKind(), PepperPotatoKind(), EmberImpKind(), VolcanoSpudKind(), InfernoTuberKind()]
