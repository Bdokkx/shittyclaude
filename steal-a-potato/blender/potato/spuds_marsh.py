"""Mushroom Marsh potatoes, worst to best: MossyTater, ToadstoolTot, FroggySpud, SwampThing,
Glowshroom, HydraTuber. Same rig, features and rules as the Meadow Patch kinds (spuds.py)."""
import numpy as np

import spsgeo as G

from .bricks import ori, shade
from .spuds import (CHEEK, GLINT, INK, Kind, SpudKind, arms, crown, dimples, eyes, legs, mouth_smile, octo,
                    sprout)

MOSS = ("5a9a3a", "4a8430", "6aae46")


def cap(sp, c, w, h, cols, lid=None, material="Plastic", turn=0.0):
    """Folk Valley's round as a mushroom cap: two crossing slabs, a block turned 45 degrees whose
    corners poke out a little, and an optional lid (w, h, d) on top."""
    c = np.asarray(c, float)
    R = G.ry(turn)
    out = [sp.extra((w, h, w * 0.6), c, R, cols[0], material=material),
           sp.extra((w * 0.6, h - 0.03, w), c, R, cols[1], material=material),
           sp.extra((w * 0.84, h - 0.06, w * 0.84), c, R @ G.ry(45), cols[2], material=material)]
    if lid:
        lw, lh, ld = lid
        out.append(sp.extra((lw, lh, ld), c + np.array((0.0, h / 2 + lh / 2 - 0.04, 0.0)), R, cols[1],
                            material=material))
    return out


class MossyTaterKind(SpudKind):
    """A brown spud with green moss over its top half and a tiny leaf on its head."""
    pid, display, rarity, area = "MossyTater", "Mossy Tater", "Uncommon", "Marsh"
    skin = ("a87a4a", "8a6038", "c09060")
    limb = "8a6038"
    shoe = "4e8048"

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 2.95, 3.2, 2.9, 2.0, 0.6, (mid, dark, light), core=True)
        sp.extra((2.3, 0.6, 2.1), (0.0, 0.3, 0.0), ori(0, 9, 0), dark)
        sp.extra((3.3, 0.8, 3.0), (0.0, 3.05, 0.0), ori(0, -6, 2), MOSS[0])            # the moss over its top
        sp.extra((1.9, 0.36, 1.75), (0.08, 3.6, 0.05), ori(0, 14, 3), MOSS[2])
        for pos, R, sz in (((-1.35, 2.42, -1.12), ori(0, 45, -6), (0.95, 0.62, 0.14)),    # moss creeping down
                           ((1.64, 2.3, 0.3), ori(0, 90, 8), (1.1, 0.7, 0.14)),
                           ((0.55, 2.84, -1.5), ori(0, 0, -4), (0.62, 0.26, 0.12))):
            sp.extra(sz, pos, R, MOSS[1])
        sp.extra((0.12, 0.42, 0.12), (0.7, 3.95, 0.3), G.rz(-14), "6b4a2a")             # a tiny leaf
        sp.extra((0.52, 0.1, 0.3), (0.92, 4.16, 0.3), ori(0, -20, 24), MOSS[2])
        self.spots(sp, (((0.62, 0.95, -1.47), ori(0, 0, 12), (0.42, 0.34, 0.1)),), shade(dark, -0.3))


class ToadstoolTotKind(Kind):
    """A short cream stalk of a potato under a big red toadstool cap with white dots."""
    pid, display, rarity, area = "ToadstoolTot", "Toadstool Tot", "Rare", "Marsh"
    skin = ("f2e8d0", "dcd0b4", "fff8e8")
    limb = "dcd0b4"
    shoe = "c9402a"
    face = dict(z=-1.35, eye_y=1.5, eye_dx=0.46, mouth_y=0.9, cheek_dx=0.78)
    shoulder = (1.45, 1.25)
    head = (0.0, 3.62, 0.0)
    leg_h = 1.0

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.12, 2.25, 2.9, 2.7, 1.8, 0.6, (mid, dark, light), core=True)
        sp.extra((3.0, 0.14, 2.8), (0.0, 2.3, 0.0), ori(0, 22, 0), "e8dcc0")              # the gills
        red = ("e04a3a", "c9402a", "f06a58")
        cap(sp, (0.0, 2.8, 0.0), 3.9, 0.92, red, lid=(2.5, 0.42, 2.3), turn=8)
        for pos, sz in (((1.55, 3.29, -0.4), 0.5), ((-0.6, 3.27, -1.4), 0.48), ((-1.45, 3.29, 0.5), 0.44),
                        ((0.3, 3.68, -0.35), 0.5)):
            sp.extra((sz, 0.1, sz), pos, G.ry(30), "fffaf0")                               # white dots


class FroggySpudKind(Kind):
    """A bright green frog of a potato: big frog eyes up on top, a wide grin, a pale belly."""
    pid, display, rarity, area = "FroggySpud", "Froggy Spud", "Rare", "Marsh"
    skin = ("6cc24a", "52a238", "8ad866")
    limb = "52a238"
    shoe = "4a9a32"
    face = dict(z=-1.48, eye_y=2.95, eye_dx=0.75, mouth_y=1.62, cheek_dx=1.12, cheek_y=1.95)
    shoulder = (1.7, 1.55)
    head = (0.0, 2.62, 0.72)
    leg_h = 1.05

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.3, 2.62, 3.4, 3.0, 2.2, 0.62, (mid, dark, light), core=True)
        sp.extra((2.5, 0.45, 2.2), (0.0, 0.25, 0.0), ori(0, 20, 0), dark)
        sp.extra((1.8, 1.0, 0.1), (0.0, 1.0, -1.52), None, "d8f0a0")                     # its pale belly
        for s in (-1, 1):                                                                # the eye bumps
            c = np.array((s * 0.75, 2.9, -0.72))
            sp.extra((1.25, 1.0, 1.0), c, None, light)
            sp.extra((1.0, 0.98, 1.25), c, None, mid)
        for pos in ((-0.9, 2.66, 0.85), (0.7, 2.66, 0.25)):
            sp.extra((0.6, 0.1, 0.5), pos, G.ry(30), dark)                                  # spots on its back

    def features(self, sp):
        dimples(sp)
        eyes(sp, w=0.66, hgt=0.66)
        f = self.face
        z, y = f["z"], f["mouth_y"]
        h = sp.holder("Mouth", (0.0, y, z))
        sp.plate(h, "Mouth", (1.7, 0.16, 0.1), (0.0, y, z - 0.04))                        # a wide frog grin
        for s in (-1, 1):
            sp.plate(h, "Mouth", (0.3, 0.16, 0.1), (s * 0.92, y + 0.08, z - 0.035), G.rz(s * 30))
            sp.plate(h, "Cheek", (0.36, 0.22, 0.1), (s * f["cheek_dx"], f["cheek_y"], z - 0.025), color=CHEEK)
        arms(sp, self.limb, hand="8ad866")
        legs(sp, self.limb, self.shoe, shoe_size=(1.1, 0.5, 1.4))
        sprout(sp)
        crown(sp)


class SwampThingKind(Kind):
    """Dark swamp green, draped in vines, a lily pad (with its flower) on its head and one on its shoulder."""
    pid, display, rarity, area = "SwampThing", "Swamp Thing", "Epic", "Marsh"
    skin = ("3e6a3a", "2e5430", "4e8048")
    limb = "2e5430"
    shoe = "5a4a2a"
    face = dict(z=-1.5, eye_y=2.3, eye_dx=0.5, mouth_y=1.5, cheek_dx=0.8)
    shoulder = (1.6, 1.8)
    head = (-0.1, 3.66, 0.1)
    leg_h = 1.15
    brows = (-12.0, 12.0)

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 2.95, 3.3, 3.0, 2.1, 0.62, (mid, dark, light), core=True)
        sp.extra((2.6, 0.7, 2.4), (0.0, 3.1, 0.0), ori(0, -10, 2), light)
        vine = "9ad86e"
        for pos, R, ln in (((-1.1, 2.0, -1.38), ori(-4, 0, 24), 2.2), ((1.66, 1.9, -0.35), ori(0, 90, -14), 2.1),
                           ((0.55, 2.95, -1.36), ori(-6, 0, -50), 1.2)):
            sp.extra((0.2, ln, 0.16), pos, R, vine)                                            # vines
        pad = "4ea83a"
        sp.extra((1.3, 0.1, 1.3), (0.15, 3.48, 0.1), ori(0, 40, -4), pad)                      # lily pads
        sp.extra((1.0, 0.1, 1.0), (1.45, 2.98, -0.15), ori(0, 15, -20), pad)
        sp.extra((0.6, 0.18, 0.24), (0.55, 3.62, -0.3), ori(0, 45, 0), "ff9ccc")              # its lily flower
        sp.extra((0.24, 0.19, 0.6), (0.55, 3.62, -0.3), ori(0, 45, 0), "ff7eb6")

    def mouth(self, sp):
        mouth_smile(sp, width=0.66, tongue=False, cheek_col="7ab864")


class GlowshroomKind(Kind):
    """A dark blue stalk under a glowing cyan mushroom cap, glowing spots on its body."""
    pid, display, rarity, area = "Glowshroom", "Glowshroom", "Legendary", "Marsh"
    skin = ("2a3a7a", "1e2c60", "3a4e96")
    limb = "1e2c60"
    shoe = "141c40"
    face = dict(z=-1.4, eye_y=1.62, eye_dx=0.46, mouth_y=1.0, cheek_dx=0.78)
    shoulder = (1.5, 1.35)
    head = (0.0, 3.78, 0.0)
    leg_h = 1.05

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.2, 2.4, 3.0, 2.8, 1.9, 0.6, (mid, dark, light), core=True)
        sp.extra((2.3, 0.4, 2.1), (0.0, 0.2, 0.0), ori(0, 22, 0), dark)
        glow = ("4ff0ff", "2bd8f0", "9ffaff")
        cap(sp, (0.0, 2.95, 0.0), 4.0, 0.95, glow, lid=(2.6, 0.45, 2.3), material="Neon", turn=-10)
        for pos, R, sz in (((-1.0, 1.95, -1.42), ori(0, 0, 20), 0.3), ((1.35, 0.9, -1.05), ori(0, -45, 0), 0.34),
                           ((-1.52, 0.75, 0.3), ori(0, 90, 0), 0.3)):
            sp.extra((sz, sz, 0.1), pos, R @ G.rz(45), glow[2], material="Neon")              # glowing spots

    def mouth(self, sp):
        mouth_smile(sp, width=0.56, cheek_col="6a8cff")

    def crown(self, sp):
        crown(sp, jewel="4ff0ff")


class HydraTuberKind(Kind):
    """Purple and green with three heads on short necks: the big purple one in the middle and two
    little green ones on its shoulders, all looking about."""
    pid, display, rarity, area = "HydraTuber", "Hydra Tuber", "Mythic", "Marsh"
    skin = ("7a4aa8", "5e3888", "9466c4")
    limb = "5e3888"
    shoe = "3e8a3a"
    face = dict(z=-0.98, eye_y=3.55, eye_dx=0.42, mouth_y=2.98, cheek_dx=0.74)
    shoulder = (1.55, 1.7)
    head = (0.0, 4.25, 0.0)
    leg_h = 1.15

    def body(self, sp):
        mid, dark, light = self.skin
        green = ("5aa84a", "468a3a", "74c460")
        octo(sp, 0.35, 2.4, 3.2, 2.8, 2.0, 0.6, (mid, dark, light), core=True)
        sp.extra((1.0, 0.7, 0.9), (0.0, 2.55, 0.0), None, dark)                          # the middle neck
        sp.extra((2.2, 1.65, 1.95), (0.0, 3.42, 0.0), None, mid)                         # the middle head
        for s in (-1, 1):                                                                # the side heads
            Rh = ori(0, s * 18, -s * 16)
            c = np.array((s * 1.5, 2.95, -0.1))
            sp.extra((1.1, 0.95, 1.05), c, Rh, green[0 if s < 0 else 2])
            for k in (-1, 1):
                sp.extra((0.18, 0.26, 0.1), c + Rh @ (k * 0.24, 0.05, -0.53), Rh, INK)

    def mouth(self, sp):
        mouth_smile(sp, width=0.56)


MARSH = [MossyTaterKind(), ToadstoolTotKind(), FroggySpudKind(), SwampThingKind(), GlowshroomKind(), HydraTuberKind()]
