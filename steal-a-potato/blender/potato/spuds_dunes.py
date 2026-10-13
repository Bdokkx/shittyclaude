"""Sandy Dunes potatoes, worst to best: DustySpud, CactusTater, MummyMash, ScorpionSpud,
PharaohFry, SphinxSpud. Same rig, features and rules as the Meadow Patch kinds (spuds.py)."""
import math

import numpy as np

import spsgeo as G

from .bricks import ori, shade
from .spuds import (GLINT, INK, Kind, SpudKind, arms, crown, dimples, eyes, legs, mouth_smile, octo, sprout)

SAND = ("d8b67a", "bf9a5a", "ead08f")


def chamfer_frame(w, d, front, ch, y, out=0.0, side=1):
    """The middle of a front chamfer of an octo body (side +1 its right, -1 its left), pushed `out`
    along the chamfer's outward normal, and the turn about Y that faces a plate along that normal."""
    sd = d - 2 * ch
    ax, az = (w - front) / 2, (d - sd) / 2
    ln = math.hypot(ax, az)
    n = np.array((side * az, 0.0, -ax)) / ln
    mid = np.array((side * (front / 2 + w / 2) / 2, y, -(d / 2 + sd / 2) / 2))
    turn = math.degrees(math.atan2(-n[0], -n[2]))
    return mid + n * out, turn


class DustySpudKind(SpudKind):
    """A sandy tan spud with a little red desert scarf knotted at its neck, tails flying."""
    pid, display, rarity, area = "DustySpud", "Dusty Spud", "Common", "Dunes"
    skin = SAND
    limb = "bf9a5a"
    shoe = "8a5a32"

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 2.95, 3.2, 2.9, 2.0, 0.6, (mid, dark, light), core=True)
        sp.extra((2.3, 0.6, 2.1), (0.0, 0.3, 0.0), ori(0, 9, 0), dark)
        sp.extra((2.45, 0.8, 2.25), (0.0, 3.2, 0.05), ori(0, -8, 3), light)
        self.spots(sp, (((-1.3, 2.75, -0.95), ori(0, 45, -8), (0.34, 0.28, 0.1)),
                        ((1.62, 1.95, 0.25), ori(0, 90, 20), (0.36, 0.3, 0.1))), shade(dark, -0.25))
        # the scarf: a band across its front, the point hanging below, a knot on its right with two tails
        red, dred = "d7372c", "a82820"
        sp.extra((2.12, 0.34, 0.12), (0.0, 1.12, -1.5), None, red)
        sp.extra((0.72, 0.72, 0.1), (0.0, 0.79, -1.48), G.rz(45), dred)
        c, turn = chamfer_frame(3.2, 2.9, 2.0, 0.6, 1.12, out=0.12, side=1)
        sp.extra((0.4, 0.4, 0.3), c, G.ry(turn) @ G.rz(20), dred)
        for k, (dy, a) in enumerate(((0.05, -18.0), (-0.22, -40.0))):
            sp.extra((0.62, 0.17, 0.11), c + np.array((0.38, dy, 0.28)), G.ry(turn - 55) @ G.rz(a), red)


class CactusTaterKind(Kind):
    """A tall green cactus of a potato, cream spines all over it and a pink flower on its head."""
    pid, display, rarity, area = "CactusTater", "Cactus Tater", "Uncommon", "Dunes"
    skin = ("5a9e48", "457f36", "7ab864")
    limb = "457f36"
    shoe = "c8643a"
    face = dict(z=-1.4, eye_y=2.45, eye_dx=0.48, mouth_y=1.68, cheek_dx=0.8)
    shoulder = (1.5, 1.95)
    head = (0.0, 3.85, 0.0)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        groove = shade(dark, -0.2)
        octo(sp, 0.3, 3.3, 3.0, 2.8, 2.0, 0.55, (light, mid, groove), core=True)
        sp.extra((2.2, 0.62, 1.5), (0.0, 3.45, 0.0), None, light)                    # a rounded top
        sp.extra((1.5, 0.64, 2.1), (0.0, 3.45, 0.0), None, mid)
        spine = "fffbea"
        for side in (-1, 1):                                                         # spines on the grooves
            for y, k in ((2.75, 0), (1.35, 1)):
                c, turn = chamfer_frame(3.0, 2.8, 2.0, 0.55, y, out=0.18, side=side)
                sp.extra((0.12, 0.62, 0.12), c, G.ry(turn) @ G.rx(-90 + 25 * (1 - 2 * k)) @ G.rz(side * 30), spine)
        # the pink flower, on the right of its head where everyone can see it
        c = np.array((1.0, 3.55, -1.0))
        Rf = ori(-62, -22, -10)                                                     # facing out and up
        sp.extra((1.15, 0.16, 0.42), c, Rf @ G.ry(45), "ff7eb6")
        sp.extra((0.42, 0.17, 1.15), c + Rf @ (0, 0.01, 0), Rf @ G.ry(45), "ff5ca8")
        sp.extra((0.34, 0.26, 0.34), c + Rf @ (0, 0.12, 0), Rf, "ffd447")

    def mouth(self, sp):
        mouth_smile(sp, width=0.6, tongue=False)


class MummyMashKind(Kind):
    """Wrapped up in old white bandages, one eye peeking out between them."""
    pid, display, rarity, area = "MummyMash", "Mummy Mash", "Rare", "Dunes"
    skin = ("ece4d0", "d4c9ae", "f8f2e2")
    limb = "d4c9ae"
    shoe = "b8ab88"
    face = dict(z=-1.45, eye_y=2.32, eye_dx=0.5, mouth_y=1.55)
    shoulder = (1.55, 1.8)
    head = (0.0, 3.45, 0.0)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 2.95, 3.2, 2.9, 2.0, 0.6, (mid, dark, light), core=True)
        sp.extra((2.5, 0.66, 1.66), (0.0, 3.05, 0.0), ori(0, 0, 3), light)
        sp.extra((1.7, 0.68, 2.4), (0.0, 3.05, 0.0), ori(0, 0, 3), mid)
        old = "c9bd9c"
        for y, rx_, rz_, col in ((0.95, 4, -7, dark), (1.95, -3, 6, old), (2.95, 5, -4, dark)):
            sp.extra((3.3, 0.2, 3.02), (0.0, y, 0.0), ori(rx_, 0, rz_), col)              # bandages round it
        sp.extra((1.3, 0.42, 0.13), (-0.42, 2.36, -1.58), G.rz(-14), light)             # over its left eye
        sp.extra((0.28, 1.1, 0.12), (1.66, 2.2, -0.62), ori(0, -35, 12), mid)          # a loose end
        self.spots(sp, (((0.75, 0.7, -1.47), ori(0, 0, 10), (0.36, 0.28, 0.1)),), "b8a682")

    def mouth(self, sp):
        mouth_smile(sp, width=0.5, cheeks=False)


class ScorpionSpudKind(Kind):
    """Orange-brown and armoured, a scorpion's tail curling up behind it and pincers for hands."""
    pid, display, rarity, area = "ScorpionSpud", "Scorpion Spud", "Epic", "Dunes"
    skin = ("c8743a", "a85a28", "e08e50")
    limb = "a85a28"
    shoe = "5e321a"
    face = dict(z=-1.5, eye_y=2.3, eye_dx=0.5, mouth_y=1.52, cheek_dx=0.8)
    shoulder = (1.6, 1.8)
    head = (-0.2, 3.55, -0.2)
    leg_h = 1.15

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 2.95, 3.3, 3.0, 2.1, 0.62, (mid, dark, light), core=True)
        sp.extra((2.55, 0.66, 2.3), (0.0, 3.1, 0.05), ori(0, 10, 0), light)
        # the tail: segments rising behind it and curling forward, a stinger on the end
        pts = [(0.55, 1.2, 1.35), (0.9, 2.65, 1.95), (1.12, 4.05, 1.7), (1.15, 5.0, 0.85)]
        for i, (a, b) in enumerate(zip(pts, pts[1:])):
            a, b = np.array(a), np.array(b)
            d = b - a
            L = float(np.linalg.norm(d))
            y = d / L
            x = np.cross(y, (0.0, 0.0, 1.0)) if abs(y[2]) < 0.9 else np.cross(y, (1.0, 0.0, 0.0))
            x /= np.linalg.norm(x)
            z = np.cross(x, y)
            w = 0.9 - 0.12 * i
            sp.extra((w, L + 0.3, w), (a + b) / 2, np.column_stack((x, y, z)), dark if i % 2 else mid)
        sp.extra((0.7, 0.7, 0.7), (1.15, 5.2, 0.3), ori(30, 45, 0), "8a3a1e")         # the stinger's bulb
        sp.extra((0.2, 0.7, 0.2), (1.15, 4.92, -0.15), ori(-60, 0, 0), "2b1e18")      # and its sting

    def features(self, sp):
        dimples(sp)
        eyes(sp)
        mouth_smile(sp, width=0.6, tongue=False)
        pincer_arms(sp, self.limb, ("8a3a1e", "a84a26"))
        legs(sp, self.limb, self.shoe)
        sprout(sp, at=(-0.35, 3.45, -0.35))
        crown(sp, at=(-0.25, 3.55, -0.3))


def pincer_arms(sp, col, claw, length=1.45, thick=0.52, spread=38.0):
    """Arms like arms() whose hands are a scorpion's pincers: two jaws opening forward."""
    sx, sy = sp.kind.shoulder
    for s, side in ((-1, "L"), (1, "R")):
        hinge = np.array((s * sx, sy, 0.0))
        R = G.rz(s * spread)
        down = R @ np.array((0.0, -1.0, 0.0))
        c = hinge + down * (length / 2 - 0.15)
        arm = sp.single("Arm" + side, (thick, length, thick), c, R, col, hinge, sp.body)
        wrist = hinge + down * (length - 0.2)
        h = sp.holder("Hand" + side, tuple(wrist), part0=arm)
        for k, (tilt, size, cc) in enumerate(((24.0, (0.5, 0.36, 1.0), claw[0]), (-20.0, (0.44, 0.3, 0.85), claw[1]))):
            Rj = R @ G.rx(tilt)
            sp.brick(h, "Pincer", size, wrist + R @ (0.0, -0.12 - 0.1 * k, 0.0) + Rj @ (0.0, 0.0, -size[2] / 2 + 0.2),
                     Rj, cc)


class PharaohFryKind(Kind):
    """A tall golden fry in a pharaoh's striped blue and gold headdress, with a little beard."""
    pid, display, rarity, area = "PharaohFry", "Pharaoh Fry", "Legendary", "Dunes"
    skin = ("f0c050", "d4a038", "f8dc80")
    limb = "d4a038"
    shoe = "2f57b0"
    face = dict(z=-1.2, eye_y=2.7, eye_dx=0.46, mouth_y=1.95, cheek_dx=0.78)
    shoulder = (1.4, 2.1)
    head = (0.0, 4.55, 0.0)
    leg_h = 1.3

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.3, 3.9, 2.7, 2.4, 2.2, 0.25, (mid, dark, light), core=True)
        sp.extra((2.2, 0.3, 1.9), (0.0, 0.15, 0.0), None, dark)
        blue, dblue, gold = "2f57b0", "1e3a80", "ffd447"
        sp.extra((3.0, 0.6, 2.7), (0.0, 4.15, 0.08), None, blue)                         # the headdress
        sp.extra((2.84, 0.3, 0.14), (0.0, 3.68, -1.27), None, gold)                      # its gold brow band
        for s in (-1, 1):                                                                # lappets either side
            sp.extra((0.62, 2.1, 0.5), (s * 1.28, 2.95, -0.85), ori(0, 0, -s * 4), dblue)
            sp.extra((0.66, 0.24, 0.54), (s * 1.3, 2.7, -0.85), ori(0, 0, -s * 4), gold)
        sp.extra((0.3, 0.55, 0.24), (0.0, 4.0, -1.33), None, gold)                      # the cobra
        sp.extra((0.36, 0.62, 0.3), (0.0, 1.38, -1.28), None, dblue)                     # the beard

    def features(self, sp):
        dimples(sp)
        eyes(sp, w=0.46, hgt=0.66)
        mouth_smile(sp, width=0.5, tongue=False)
        arms(sp, self.limb, hand="ffd447")
        legs(sp, self.limb, self.shoe)
        sprout(sp)
        crown(sp, cols=("ffd447", "fff1a8", "e0a800"), jewel="3ff0e0")


class SphinxSpudKind(Kind):
    """Carved from sandstone like the sphinx, its eyes glowing turquoise; lion's paws for feet."""
    pid, display, rarity, area = "SphinxSpud", "Sphinx Spud", "Mythic", "Dunes"
    skin = ("d9b98a", "c2a06e", "ead2a8")
    limb = "c2a06e"
    shoe = "ead2a8"
    face = dict(z=-1.45, eye_y=2.3, eye_dx=0.5, mouth_y=1.52, cheek_dx=0.82)
    shoulder = (1.55, 1.8)
    head = (0.0, 3.6, 0.05)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        carve = "a8865a"
        octo(sp, 0.35, 2.95, 3.2, 2.9, 2.0, 0.6, (mid, dark, light), core=True)
        sp.extra((2.9, 0.55, 2.7), (0.0, 3.2, 0.08), None, light)                         # the headcloth
        for s in (-1, 1):                                                                # its lappets
            c, turn = chamfer_frame(3.2, 2.9, 2.0, 0.6, 2.0, out=0.16, side=s)
            Rl = G.ry(turn) @ G.rz(-s * 4)
            sp.extra((0.78, 2.2, 0.36), c, Rl, mid)
            for y in (0.45, -0.35):
                sp.extra((0.82, 0.14, 0.4), c + Rl @ (0, y, 0), Rl, carve)               # carved stripes
        sp.extra((2.3, 0.14, 0.12), (0.0, 3.0, -1.47), None, carve)
        sp.extra((0.1, 0.9, 0.12), (0.8, 1.0, -1.47), G.rz(14), carve)                   # cracks
        sp.extra((0.1, 0.6, 0.12), (-0.95, 1.2, -1.47), G.rz(-24), carve)

    def features(self, sp):
        dimples(sp)
        f = self.face
        z, y, dx = f["z"], f["eye_y"], f["eye_dx"]
        h = sp.holder("Eyes", (0.0, y, z))
        for s in (1, -1):                                                               # glowing turquoise eyes
            sp.plate(h, "Eye", (0.5, 0.62, 0.1), (s * dx, y, z - 0.04), color="3ff0e0", material="Neon")
            sp.plate(h, "Glint", (0.18, 0.18, 0.1), (s * dx + 0.11, y + 0.16, z - 0.09), color=GLINT)
        mouth_smile(sp, width=0.56, tongue=False, cheek_col="e8b098")
        arms(sp, self.limb, hand="ead2a8")
        legs(sp, self.limb, self.shoe, shoe_size=(1.05, 0.6, 1.6))
        sprout(sp)
        crown(sp, cols=("ffd447", "fff1a8", "e0a800"), jewel="3ff0e0")


DUNES = [DustySpudKind(), CactusTaterKind(), MummyMashKind(), ScorpionSpudKind(), PharaohFryKind(), SphinxSpudKind()]
