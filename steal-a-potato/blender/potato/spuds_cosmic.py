"""Cosmic Garden potatoes, worst to best: MoonRockSpud, CometTater, AlienSpud, NebulaMash, BlackHoleTuber,
GalacticOverlord. Same rig, features and rules as the Meadow Patch kinds (spuds.py).

The dark ones (nebula, black hole, deep space) have white or glowing eyes so their faces read."""
import math

import numpy as np

import spsgeo as G

from .bricks import ori
from .spuds import (INK, Kind, arms, crown, dimples, eyes, legs, mouth_smile, octo, sprout, star)
from .spuds_lava import chamfer_normal, crack, glow_eyes, glow_mouth, soot_eyes, stick


def ring(sp, centre, radius, n, w, t, R, cols, material="Plastic"):
    """A ring of n bars round centre in the plane of R's local X and Z (an n-sided polygon), each w
    wide and t thick; every other bar a little thicker so their corners never fight."""
    c = np.asarray(centre, float)
    side = 2 * (radius + w / 2) * math.tan(math.pi / n)
    up = np.array((0.0, 1.0, 0.0))
    for i in range(n):
        a = 2 * math.pi * (i + 0.5) / n
        radial = np.array((math.cos(a), 0.0, math.sin(a)))
        Rb = np.column_stack((radial, up, np.cross(radial, up)))
        sp.extra((w, t * (1.0 if i % 2 == 0 else 1.08), side), c + R @ (radial * radius), R @ Rb,
                 cols[i % len(cols)], material=material)


def alien_eyes(sp, w=0.86, hgt=0.8, tilt=10.0, col="0e0e12"):
    """Two big black alien eyes, tipped up a little at their outer corners, a big and a small white
    glint in each."""
    f = sp.kind.face
    z, y, dx = f["z"], f["eye_y"], f["eye_dx"]
    h = sp.holder("Eyes", (0.0, y, z))
    for s in (1, -1):
        ex = s * dx
        R = G.rz(s * tilt)
        sp.plate(h, "Eye", (w, hgt, 0.1), (ex, y, z - 0.04), R, color=col)
        for (gx, gy), k in (((0.16, 0.16), 0.24), ((-0.14, -0.18), 0.12)):
            sp.plate(h, "Glint", (k, k, 0.1), np.array((ex, y, z - 0.09)) + R @ (s * gx, gy, 0.0), R, color="ffffff")
    return h


class MoonRockSpudKind(Kind):
    """A grey moon rock of a potato, pitted with craters, a little flag planted in its head."""
    pid, display, rarity, area = "MoonRockSpud", "Moon Rock Spud", "Epic", "Cosmic"
    skin = ("b8b6b0", "9c9a94", "cccac4")
    limb = "9c9a94"
    shoe = "5a5a62"
    face = dict(z=-1.45, eye_y=2.32, eye_dx=0.5, mouth_y=1.55, cheek_dx=0.84)
    shoulder = (1.55, 1.8)
    head = (-0.2, 3.62, -0.05)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        W, D, F, C = 3.2, 2.9, 2.0, 0.6
        octo(sp, 0.35, 2.95, W, D, F, C, (mid, dark, light), core=True)
        sp.extra((2.45, 0.7, 2.2), (0.0, 3.1, 0.05), ori(0, -8, 3), light)
        rim, pit = "d8d6d0", "7e7c76"                                                         # craters
        n, mid_ = chamfer_normal(W, D, F, C, -1)
        for c, nrm, R, k in (((0.68, 0.78, -D / 2), np.array((0.0, 0.0, -1.0)), None, 0.6),
                             (mid_ + (0.0, 2.25, 0.0), n, G.ry(45), 0.62),
                             ((W / 2, 1.35, -0.15), np.array((1.0, 0.0, 0.0)), G.ry(90), 0.8)):
            c = np.asarray(c, float)
            sp.extra((k, k, 0.1), c + nrm * 0.03, R, rim)
            sp.extra((k * 0.6, k * 0.6, 0.1), c + nrm * 0.05, R, pit)
        sp.extra((0.12, 2.2, 0.12), (0.88, 4.1, 0.5), None, "ffffff")                          # a little flag
        sp.extra((0.9, 0.58, 0.06), (1.38, 4.88, 0.5), None, "e8403a")

    def features(self, sp):
        dimples(sp)
        eyes(sp)
        mouth_smile(sp)
        arms(sp, self.limb)
        legs(sp, self.limb, self.shoe)
        sprout(sp, at=(-0.2, 3.5, -0.05))
        crown(sp, jewel="6ff3ff")


class CometTaterKind(Kind):
    """An icy blue comet of a potato, frost on its head and a bright tail streaming away behind it."""
    pid, display, rarity, area = "CometTater", "Comet Tater", "Legendary", "Cosmic"
    skin = ("7fd4ff", "5fbaf0", "a8e4ff")
    limb = "5fbaf0"
    shoe = "2f7fc8"
    face = dict(z=-1.45, eye_y=2.32, eye_dx=0.5, mouth_y=1.55, cheek_dx=0.84)
    shoulder = (1.55, 1.8)
    head = (0.0, 3.62, 0.0)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 2.95, 3.2, 2.9, 2.0, 0.6, (mid, dark, light), core=True)
        sp.extra((2.45, 0.7, 2.2), (0.0, 3.1, 0.05), ori(0, -8, 3), "eef9ff")                 # frost
        for pos, R in (((-0.9, 3.45, 0.2), ori(0, 45, 20)), ((0.95, 3.4, -0.1), ori(10, 45, -24))):
            sp.extra((0.3, 0.7, 0.3), pos, R, "ffffff")                                        # ice
        o = np.array((0.15, 2.85, 1.0))                                                       # its tail
        for d, L, k, cols in (((-1.0, 0.35, 0.8), 3.7, 0.6, ("e6f8ff", "ffffff")),
                              ((-1.2, 0.0, 0.7), 3.0, 0.48, ("8fdcff", "c6efff")),
                              ((-0.7, 0.75, 0.8), 2.7, 0.44, ("bfeaff", "e6f8ff"))):
            d = np.array(d) / np.linalg.norm(d)
            mid_ = o + d * L * 0.55
            stick(sp, o, mid_, k, cols[0], n=np.cross(d, (0, 1, 0)), t=k)
            stick(sp, mid_ - d * 0.1, o + d * L, k * 0.6, cols[1], n=np.cross(d, (0, 1, 0)) + (0, 0.3, 0), t=k * 0.6)

    def features(self, sp):
        dimples(sp)
        eyes(sp)
        mouth_smile(sp)
        arms(sp, self.limb, hand="eef9ff")
        legs(sp, self.limb, self.shoe)
        sprout(sp)
        crown(sp, jewel="6ff3ff")


class AlienSpudKind(Kind):
    """A lime green alien of a potato: two antennae with glowing bobbles and big black alien eyes."""
    pid, display, rarity, area = "AlienSpud", "Alien Spud", "Mythic", "Cosmic"
    skin = ("9be22d", "7cc21e", "b8f04e")
    limb = "7cc21e"
    shoe = "5a3c8a"
    face = dict(z=-1.45, eye_y=2.3, eye_dx=0.5, mouth_y=1.5, cheek_dx=0.9, cheek_y=1.78)
    shoulder = (1.55, 1.8)
    head = (0.0, 3.62, 0.0)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 2.95, 3.2, 2.9, 2.0, 0.6, (mid, dark, light), core=True)
        sp.extra((2.45, 0.7, 2.2), (0.0, 3.1, 0.05), ori(0, -8, 3), light)
        for s in (-1, 1):                                                                    # antennae
            base = np.array((s * 0.72, 3.3, 0.2))
            R = G.rz(-s * 16)
            sp.extra((0.14, 1.35, 0.14), base + R @ (0, 0.67, 0), R, dark)
            sp.extra((0.42, 0.42, 0.42), base + R @ (0, 1.42, 0), ori(35, 45, 0), "e8ff6a", material="Neon")
        for pos, R in (((1.62, 2.1, 0.3), G.ry(90)), ((-1.62, 1.1, -0.2), G.ry(-90))):
            sp.extra((0.5, 0.36, 0.1), pos, R, dark)                                            # spots

    def features(self, sp):
        dimples(sp)
        alien_eyes(sp)
        mouth_smile(sp, width=0.42)
        arms(sp, self.limb)
        legs(sp, self.limb, self.shoe)
        sprout(sp)
        crown(sp, jewel="e8ff6a")


class NebulaMashKind(Kind):
    """Deep purple space with a pink galaxy swirling round it, its arms glowing, stars twinkling."""
    pid, display, rarity, area = "NebulaMash", "Nebula Mash", "Secret", "Cosmic"
    skin = ("4a1f8a", "2e1260", "8a2aa8")
    limb = "2e1260"
    shoe = "ff5ec8"
    face = dict(z=-1.45, eye_y=2.32, eye_dx=0.5, mouth_y=1.55)
    shoulder = (1.55, 1.8)
    head = (0.0, 3.07, 0.0)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        W, D, F, C = 3.2, 2.9, 2.0, 0.6
        octo(sp, 0.35, 2.95, W, D, F, C, (mid, dark, light), core=True)
        pink, lilac, blue = "ff5ec8", "c58cff", "5ec8ff"
        n1, m1 = chamfer_normal(W, D, F, C, 1)
        n2, m2 = chamfer_normal(W, D, F, C, -1)
        for pos, nrm, R, k, col in ((m1 + (0, 2.3, 0), n1, G.ry(-45) @ G.rz(30), 0.78, pink),          # glowing gas
                                    ((-W / 2, 1.25, 0.2), np.array((-1.0, 0, 0)), G.ry(-90) @ G.rz(20), 0.95, blue),
                                    (m2 + (0, 0.9, 0), n2, G.ry(45) @ G.rz(-15), 0.7, lilac)):
            sp.extra((k, k, 0.1), np.asarray(pos) + nrm * 0.03, R, col, material="Neon")
        z = -D / 2                                                                            # a galaxy's arm
        crack(sp, [(-0.95, 0.5, z), (-0.2, 0.62, z), (0.55, 0.9, z)], (0, 0, -1), w=0.2, col=pink)
        for pos, k in (((0.86, 2.86, -1.47), 0.2), ((-0.75, 2.95, -1.47), 0.16), ((0.75, 0.48, -1.47), 0.15),
                       ((-0.35, 1.08, -1.47), 0.14)):
            sp.extra((k, k, 0.1), pos, G.rz(45), "ffffff", material="Neon")                    # stars
        for pos, k in (((0.45, 3.02, 0.55), 0.22), ((-1.2, 3.05, -0.4), 0.18), ((1.62, 1.55, -0.3), 0.18)):
            sp.extra((k, k, k), pos, ori(35, 45, 0), "ffffff", material="Neon")

    def features(self, sp):
        dimples(sp, col="ff5ec8")
        soot_eyes(sp, col="ffffff")
        glow_mouth(sp, "ff5ec8", width=0.56, hgt=0.22)
        arms(sp, self.limb, hand="c58cff")
        legs(sp, self.limb, self.shoe)
        sprout(sp)
        crown(sp, jewel="ff5ec8")


class BlackHoleTuberKind(Kind):
    """Pitch black, framed by a glowing orange ring of light with sparks caught in it, its eyes and
    mouth glowing."""
    pid, display, rarity, area = "BlackHoleTuber", "Black Hole Tuber", "Divine", "Cosmic"
    skin = ("0e0c10", "08070a", "16131a")
    limb = "08070a"
    shoe = "16131a"
    face = dict(z=-1.45, eye_y=2.32, eye_dx=0.5, mouth_y=1.55)
    shoulder = (1.55, 1.8)
    head = (0.0, 3.07, 0.0)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 2.95, 3.2, 2.9, 2.0, 0.6, (mid, dark, light), core=True)
        ring(sp, (0.0, 2.2, 0.9), 2.0, 8, 0.36, 0.3, G.rx(90), ("ff8a1f", "ffb02a"), material="Neon")   # its ring
        for pos, k in (((-1.55, 3.95, 0.9), 0.3), ((1.95, 0.75, 0.9), 0.24)):                 # sparks caught in it
            sp.extra((k, k, k), pos, ori(35, 45, 0), "ffe9a8", material="Neon")

    def features(self, sp):
        dimples(sp, col="3a2a1a")
        glow_eyes(sp, "ffd27a", glint_col=INK)
        glow_mouth(sp, "ff8a1f", width=0.56, hgt=0.22)
        arms(sp, self.limb, hand="16131a")
        legs(sp, self.limb, self.shoe)
        sprout(sp)
        crown(sp, jewel="ff8a1f")


class GalacticOverlordKind(Kind):
    """Deep space blue and grand: a ring like Saturn's tilted round its middle, small stars orbiting
    it and, at the top level, a big gold crown."""
    pid, display, rarity, area = "GalacticOverlord", "Galactic Overlord", "Divine", "Cosmic"
    skin = ("1b2a6b", "142057", "26388a")
    limb = "142057"
    shoe = "e8c88a"
    face = dict(z=-1.45, eye_y=2.32, eye_dx=0.5, mouth_y=1.55)
    shoulder = (1.55, 1.8)
    head = (0.0, 3.07, 0.0)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 2.95, 3.2, 2.9, 2.0, 0.6, (mid, dark, light), core=True)
        ring(sp, (0.0, 1.45, 0.0), 2.55, 6, 0.6, 0.14, G.rz(14) @ G.rx(10), ("e8c88a", "c9a46a"))   # its ring
        star(sp, sp.extra, (2.2, 3.4, -0.4), 0.7, "fff6c0")                                    # stars orbiting
        star(sp, sp.extra, (-2.05, 2.6, 0.5), 0.55, "fff6c0", ori(0, 30, 45))
        sp.extra((0.24, 0.24, 0.24), (-1.2, 3.75, -0.7), ori(35, 45, 0), "ffffff", material="Neon")

    def features(self, sp):
        dimples(sp, col="e8c88a")
        soot_eyes(sp, col="ffffff")
        glow_mouth(sp, "ffd447", width=0.52, hgt=0.2)
        arms(sp, self.limb, hand="e8c88a")
        legs(sp, self.limb, self.shoe)
        sprout(sp)
        crown(sp, jewel="6ff3ff", size=1.2)


COSMIC = [MoonRockSpudKind(), CometTaterKind(), AlienSpudKind(), NebulaMashKind(), BlackHoleTuberKind(),
          GalacticOverlordKind()]
