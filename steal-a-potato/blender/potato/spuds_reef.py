"""Coral Cove potatoes, worst to best: SandySpud, BubbleTater, ClamChip, PufferPotato, CaptainSpud,
KrakenTuber. Same rig, features and rules as the Meadow Patch kinds (spuds.py).

BubbleTater's bubbles are see-through (Transparency 0.45), like PrismPotato's glass. CaptainSpud's
hook is held in his left hand like the Candy Crops' lollipop: a child of HandL, welded to it."""
import numpy as np

import spsgeo as G

from .bricks import ori
from .spuds import (Kind, arms, crown, dimples, eyes, legs, mouth_smile, octo, sprout)
from .spuds_candy import hand_at, held
from .spuds_lava import stick

BUBBLE = 0.45


class SandySpudKind(Kind):
    """A sandy beach of a potato: speckled with sand, a pink starfish stuck on it, a little spiral
    shell on its head."""
    pid, display, rarity, area = "SandySpud", "Sandy Spud", "Uncommon", "Reef"
    skin = ("e8d4a0", "d4bc84", "f2e2b8")
    limb = "d4bc84"
    shoe = "3fa8d8"
    face = dict(z=-1.45, eye_y=2.32, eye_dx=0.5, mouth_y=1.55, cheek_dx=0.84)
    shoulder = (1.55, 1.8)
    head = (-0.15, 3.65, -0.05)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 2.95, 3.2, 2.9, 2.0, 0.6, (mid, dark, light), core=True)
        sp.extra((2.45, 0.7, 2.2), (0.0, 3.1, 0.05), ori(0, -8, 3), light)
        for pos, R in (((0.7, 0.62, -1.47), G.rz(20)), ((0.15, 0.9, -1.47), G.rz(-30)),
                       ((-1.62, 2.3, 0.4), G.ry(-90) @ G.rz(15))):
            sp.extra((0.2, 0.2, 0.1), pos, R, "b89a5c")                                         # sand
        for k, a in enumerate((0.0, 60.0, 120.0)):                                            # a starfish
            sp.extra((0.16, 0.7, 0.1 + 0.015 * k), (-0.66, 0.8, -1.47), G.rz(a + 8), "ff8a6a")
        sp.extra((0.62, 0.5, 0.62), (0.72, 3.5, 0.35), ori(0, 30, -12), "fff0e8")              # a spiral shell
        sp.extra((0.36, 0.44, 0.36), (0.8, 3.86, 0.38), ori(20, 60, -18), "ffc8b8")

    def features(self, sp):
        dimples(sp)
        eyes(sp)
        mouth_smile(sp)
        arms(sp, self.limb)
        legs(sp, self.limb, self.shoe)
        sprout(sp, at=(-0.15, 3.55, -0.05))
        crown(sp, jewel="ff8a6a")


class BubbleTaterKind(Kind):
    """An aqua potato blowing bubbles: see-through bubbles float round it, one just leaving its
    pursed mouth."""
    pid, display, rarity, area = "BubbleTater", "Bubble Tater", "Rare", "Reef"
    skin = ("5fd0e0", "45b8cc", "86e0ec")
    limb = "45b8cc"
    shoe = "2f7fc8"
    face = dict(z=-1.45, eye_y=2.32, eye_dx=0.5, mouth_y=1.5, cheek_dx=0.84)
    shoulder = (1.55, 1.8)
    head = (0.0, 3.7, 0.0)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 2.95, 3.2, 2.9, 2.0, 0.6, (mid, dark, light), core=True)
        sp.extra((2.45, 0.7, 2.2), (0.0, 3.1, 0.05), ori(0, -8, 3), light)
        for pos, k in (((0.0, 1.32, -1.95), 0.42), ((-1.15, 2.2, -1.55), 0.62), ((1.85, 3.2, -0.6), 0.8),
                       ((-1.6, 3.85, 0.1), 0.56), ((0.9, 4.55, 0.4), 0.44)):                    # bubbles
            sp.extra((k, k, k), pos, ori(35, 45, 0), "e2f8ff", transparency=BUBBLE)
        for pos in ((1.72, 3.38, -0.98), (-1.28, 2.38, -1.88)):
            sp.extra((0.14, 0.14, 0.1), pos, None, "ffffff")                                     # their glints

    def features(self, sp):
        dimples(sp)
        eyes(sp)
        mouth_smile(sp, width=0.34, tongue=False)
        arms(sp, self.limb)
        legs(sp, self.limb, self.shoe)
        sprout(sp)
        crown(sp, jewel="2f7fc8")


class ClamChipKind(Kind):
    """A pink potato with a big scallop shell standing up behind its head like a crest: a scalloped
    pink edge and white ridges running out from it. At level 10 its crown's jewel is a pearl."""
    pid, display, rarity, area = "ClamChip", "Clam Chip", "Epic", "Reef"
    skin = ("f2c6b6", "dfae9e", "fad8ca")
    limb = "dfae9e"
    shoe = "ff8aa0"
    face = dict(z=-1.45, eye_y=2.32, eye_dx=0.5, mouth_y=1.55, cheek_dx=0.84)
    shoulder = (1.55, 1.8)
    head = (0.0, 3.7, -0.15)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 2.95, 3.2, 2.9, 2.0, 0.6, (mid, dark, light), core=True)
        sp.extra((2.45, 0.7, 2.2), (0.0, 3.1, 0.05), ori(0, -8, 3), light)
        c = np.array((0.0, 3.85, 1.2))                                                        # a scallop shell crest
        Rt = G.rx(14)
        nrm = Rt @ np.array((0.0, 0.0, -1.0))
        sp.extra((3.5, 3.5, 0.2), c, Rt @ G.rz(45), "ffb6c1")
        sp.extra((3.3, 3.3, 0.24), c + Rt @ (0.0, -0.05, 0.0), Rt @ G.rz(22.5), "ffd2da")
        for k, a in enumerate((-54.0, -18.0, 18.0, 54.0)):                                    # its ridges
            R = Rt @ G.rz(a)
            sp.extra((0.18, 1.5, 0.1 + 0.01 * (k % 2)), c + R @ (0.0, 1.35, 0.0) + nrm * 0.16, R, "fff4f6")

    def features(self, sp):
        dimples(sp)
        eyes(sp)
        mouth_smile(sp)
        arms(sp, self.limb)
        legs(sp, self.limb, self.shoe)
        sprout(sp, at=(0.0, 3.6, -0.15))
        crown(sp, jewel="fff6fa")


class PufferPotatoKind(Kind):
    """A pufferfish puffed up round: yellow with spines sticking out all over it and a little pout."""
    pid, display, rarity, area = "PufferPotato", "Puffer Potato", "Epic", "Reef"
    skin = ("f2d06a", "dcb84c", "f8e090")
    limb = "dcb84c"
    shoe = "8a6a2a"
    face = dict(z=-1.6, eye_y=2.25, eye_dx=0.55, mouth_y=1.4, cheek_dx=0.92)
    shoulder = (1.7, 1.75)
    head = (0.0, 3.62, 0.0)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.3, 3.0, 3.5, 3.2, 2.2, 0.7, (mid, dark, light), core=True)
        sp.extra((2.6, 0.62, 2.4), (0.0, 3.1, 0.0), G.ry(45 / 2), light)
        spine = "c89a3a"
        for pos, d in (((1.75, 2.5, -0.3), (1, 0.35, -0.3)), ((-1.75, 2.4, 0.2), (-1, 0.3, 0.2)),   # spines
                       ((1.75, 0.9, 0.3), (1, -0.25, 0.2)), ((-1.75, 1.0, -0.4), (-1, -0.2, -0.3)),
                       ((0.9, 3.25, -0.6), (0.5, 1, -0.4)), ((-0.85, 3.25, 0.7), (-0.5, 1, 0.5)),
                       ((0.0, 2.2, 1.6), (0, 0.2, 1)), ((1.2, 1.5, -1.3), (0.6, 0.0, -0.8))):
            d = np.array(d, float)
            d /= np.linalg.norm(d)
            stick(sp, np.array(pos) - d * 0.1, np.array(pos) + d * 0.85, 0.3, spine, n=np.cross(d, (0.3, 0.9, 0.2)),
                  t=0.3, material="Plastic")

    def features(self, sp):
        dimples(sp)
        eyes(sp, w=0.52, hgt=0.7)
        mouth_smile(sp, width=0.3, tongue=False, cheek_col="ff9a6a")
        arms(sp, self.limb)
        legs(sp, self.limb, self.shoe)
        sprout(sp)
        crown(sp, jewel="ff8a6a")


class CaptainSpudKind(Kind):
    """A pirate captain: a black tricorn with a white skull on it, a patch over one eye, a bushy
    ginger beard round its mouth and a silver hook for a left hand."""
    pid, display, rarity, area = "CaptainSpud", "Captain Spud", "Legendary", "Reef"
    skin = ("d39a52", "b97a3c", "e8b670")
    limb = "8a1e24"
    shoe = "2a1e18"
    face = dict(z=-1.45, eye_y=2.3, eye_dx=0.5, mouth_y=1.55, cheek_dx=0.84)
    shoulder = (1.55, 1.8)
    head = (0.0, 4.02, 0.1)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 2.95, 3.2, 2.9, 2.0, 0.6, (mid, dark, light), core=True)
        black = "1e1a22"
        sp.extra((3.0, 0.2, 2.6), (0.0, 3.05, 0.05), None, black)                              # a tricorn
        sp.extra((2.0, 0.75, 1.6), (0.0, 3.5, 0.1), None, "2a2430")
        Rf = G.rx(16)                                                                         # its brim turned up
        flap = np.array((0.0, 3.4, -1.12))
        sp.extra((2.9, 0.66, 0.18), flap, Rf, black)
        sp.extra((0.46, 0.4, 0.1), flap + Rf @ (0.0, 0.04, -0.12), Rf, "ffffff")                # a skull on it
        sp.extra((0.66, 0.84, 0.1), (-0.5, 2.3, -1.56), None, black)                            # an eye patch
        sp.extra((1.3, 0.12, 0.1), (0.42, 2.84, -1.52), G.rz(12), black)
        sp.extra((1.6, 1.05, 0.1), (0.0, 1.3, -1.47), None, "a8481e")                           # a bushy ginger beard
        sp.extra((1.1, 0.4, 0.12), (0.0, 0.66, -1.47), None, "8e3a16")

    def features(self, sp):
        dimples(sp)
        eyes(sp)
        mouth_smile(sp, cheeks=False)
        arms(sp, self.limb, hand="ffffff")
        legs(sp, "2a2430", self.shoe)
        sprout(sp, at=(0.0, 3.92, 0.1))
        crown(sp, jewel="ff3b5c")
        hc, R = hand_at(sp, "L")                                                              # a hook for a hand
        down = R @ np.array((0.0, -1.0, 0.0))
        held(sp, "Hook", (0.16, 0.7, 0.16), hc + down * 0.55, R, "c8ccd4")
        tip = hc + down * 0.9
        held(sp, "Hook", (0.16, 0.5, 0.2), tip + np.array((0.18, 0.12, 0.0)), G.rz(-60) @ R, "c8ccd4")


class KrakenTuberKind(Kind):
    """A kraken: deep red-purple, great tentacles curling out from under it, paler at their tips,
    big eyes."""
    pid, display, rarity, area = "KrakenTuber", "Kraken Tuber", "Mythic", "Reef"
    skin = ("8a2a5a", "6e1e48", "a8386e")
    limb = "6e1e48"
    shoe = "4a1232"
    face = dict(z=-1.45, eye_y=2.36, eye_dx=0.52, mouth_y=1.6, cheek_dx=0.86)
    shoulder = (1.55, 1.85)
    head = (0.0, 3.07, 0.0)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 2.95, 3.2, 2.9, 2.0, 0.6, (mid, dark, light), core=True)
        for side in (-1, 1):                                                                 # great tentacles
            for (a, b, c), k in ((((1.35, 0.7, -0.7), (2.35, 0.35, -1.2), (2.85, 1.35, -1.5)), 0.5),
                                 (((1.0, 0.6, 1.0), (1.85, 0.35, 2.0), (2.15, 1.3, 2.55)), 0.44)):
                a, b, c = (np.array((side * p[0], p[1], p[2])) for p in (a, b, c))
                stick(sp, a, b + (b - a) * 0.08, k, mid, n=(0, 1, 0), t=k, material="Plastic")
                stick(sp, b - (c - b) * 0.08, c, k * 0.72, light, n=(0, 0, 1), t=k * 0.72, material="Plastic")

    def features(self, sp):
        dimples(sp)
        eyes(sp, w=0.56, hgt=0.76)
        mouth_smile(sp, cheek_col="ff7aa8")
        arms(sp, self.limb)
        legs(sp, self.limb, self.shoe)
        sprout(sp)
        crown(sp, jewel="3bd9c8")


REEF = [SandySpudKind(), BubbleTaterKind(), ClamChipKind(), PufferPotatoKind(), CaptainSpudKind(), KrakenTuberKind()]
