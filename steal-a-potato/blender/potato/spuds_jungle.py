"""Jungle Ruins potatoes, worst to best: VineSpud, BananaTater, ParrotPotato, MonkeyMash, TikiTuber,
GoldenIdol. Same rig, features and rules as the Meadow Patch kinds (spuds.py)."""
import numpy as np

import spsgeo as G

from .bricks import ori
from .spuds import (INK, Kind, arms, crown, dimples, eyes, legs, mouth_smile, octo, sprout, star)
from .spuds_lava import chamfer_normal, crack, glow_eyes, soot_eyes, stick

LEAF = ("4caf50", "6cc24a", "2f7a32")


class VineSpudKind(Kind):
    """A brown potato wrapped in jungle vines, leaves sprouting from them."""
    pid, display, rarity, area = "VineSpud", "Vine Spud", "Uncommon", "Jungle"
    skin = ("a87a4a", "8c6238", "c09060")
    limb = "8c6238"
    shoe = "2f7a32"
    face = dict(z=-1.45, eye_y=2.32, eye_dx=0.5, mouth_y=1.55, cheek_dx=0.84)
    shoulder = (1.55, 1.8)
    head = (0.0, 3.7, 0.0)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        W, D, F, C = 3.2, 2.9, 2.0, 0.6
        octo(sp, 0.35, 2.95, W, D, F, C, (mid, dark, light), core=True)
        sp.extra((2.45, 0.7, 2.2), (0.0, 3.1, 0.05), ori(0, -8, 3), light)
        vine = LEAF[2]                                                                        # vines
        z = -D / 2
        crack(sp, [(1.02, 0.98, z), (-0.2, 0.62, z), (-1.02, 0.88, z)], (0, 0, -1), w=0.2, col=vine, material="Plastic")
        n, mid_ = chamfer_normal(W, D, F, C, 1)
        u = np.array((-n[2], 0.0, n[0]))
        crack(sp, [mid_ - u * 0.36 + (0, 0.95, 0), mid_ + u * 0.3 + (0, 2.7, 0)], n, w=0.2, col=vine, material="Plastic")
        crack(sp, [(-W / 2, 0.9, -0.7), (-W / 2, 2.75, 0.5)], (-1, 0, 0), w=0.2, col=vine, material="Plastic")
        for pos, R, col in (((1.5, 2.62, -0.95), ori(0, -45, 30), LEAF[0]),                     # leaves
                            ((-0.25, 0.6, -1.62), ori(-30, 0, 20), LEAF[1]),
                            ((-1.75, 2.2, 0.2), ori(0, 90, -25), LEAF[0]),
                            ((0.62, 3.5, -0.45), ori(10, 30, 0), LEAF[1])):
            sp.extra((0.66, 0.08, 0.36), pos, R, col)

    def features(self, sp):
        dimples(sp)
        eyes(sp)
        mouth_smile(sp)
        arms(sp, self.limb)
        legs(sp, self.limb, self.shoe)
        sprout(sp)
        crown(sp, jewel="3bd96b")


class BananaTaterKind(Kind):
    """A yellow banana of a potato, peeled at the top: the cream fruit showing, three strips of peel
    flopping open round it, a few brown spots."""
    pid, display, rarity, area = "BananaTater", "Banana Tater", "Rare", "Jungle"
    skin = ("ffd54a", "f0c030", "ffe27a")
    limb = "f0c030"
    shoe = "8a5a2a"
    face = dict(z=-1.35, eye_y=2.45, eye_dx=0.48, mouth_y=1.7, cheek_dx=0.82)
    shoulder = (1.5, 1.95)
    head = (0.0, 4.02, 0.0)
    leg_h = 1.25

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 3.1, 3.0, 2.7, 1.9, 0.55, (mid, dark, light), core=True)
        sp.extra((1.7, 0.9, 1.5), (0.0, 3.45, 0.0), G.ry(10), "fff3c4")                       # the fruit
        for k, ang in enumerate((60.0, 180.0, 300.0)):                                       # peel flopping open
            Ry = G.ry(ang)
            R = Ry @ G.rx(-40)
            hinge = Ry @ np.array((0.0, 3.05, -0.85))
            sp.extra((0.95, 1.3, 0.16 + 0.02 * k), hinge + R @ (0, 0.6, 0), R, mid if k != 1 else dark)
        for pos, R in (((0.78, 0.7, -1.37), G.rz(20)), ((-1.52, 1.4, 0.2), G.ry(-90) @ G.rz(-30))):
            sp.extra((0.26, 0.2, 0.1), pos, R, "8a5a2a")                                       # brown spots

    def features(self, sp):
        dimples(sp)
        eyes(sp, w=0.46, hgt=0.66)
        mouth_smile(sp, width=0.56)
        arms(sp, self.limb)
        legs(sp, self.limb, self.shoe)
        sprout(sp, at=(0.0, 3.9, 0.0))
        crown(sp, jewel="ff3b5c")


class ParrotPotatoKind(Kind):
    """A bright red parrot of a potato: white patches round its eyes, a hooked beak, a crest of red,
    yellow and blue feathers, blue wings tipped yellow and a long tail."""
    pid, display, rarity, area = "ParrotPotato", "Parrot Potato", "Rare", "Jungle"
    skin = ("e8302a", "c0221e", "ff5a48")
    limb = "2f6fd8"
    shoe = "6a6a72"
    face = dict(z=-1.45, eye_y=2.38, eye_dx=0.52, mouth_y=1.7)
    shoulder = (1.55, 1.8)
    head = (0.0, 3.7, 0.0)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 2.95, 3.2, 2.9, 2.0, 0.6, (mid, dark, light), core=True)
        sp.extra((2.45, 0.7, 2.2), (0.0, 3.1, 0.05), ori(0, -8, 3), light)
        for s in (-1, 1):
            sp.extra((0.8, 0.92, 0.1), (s * 0.52, 2.38, -1.47), None, "ffffff")                # white round its eyes
        for col, lean in (("e8302a", 26.0), ("ffd54a", 0.0), ("2f6fd8", -26.0)):              # its crest
            R = G.rz(lean) @ G.rx(14)
            sp.extra((0.32, 1.9, 0.14 + 0.01 * (lean > 0)), np.array((0.0, 3.25, 0.78)) + R @ (0, 0.9, 0), R, col)
        stick(sp, (0.2, 0.95, 1.3), (0.38, 0.45, 2.75), 0.36, "2f6fd8", n=(0, 1, 0), t=0.14,
              material="Plastic")                                                             # its tail
        stick(sp, (-0.12, 1.0, 1.3), (-0.2, 0.6, 2.5), 0.3, "ffd54a", n=(0, 1, 0), t=0.16, material="Plastic")

    def features(self, sp):
        dimples(sp)
        eyes(sp, w=0.42, hgt=0.6)
        f = self.face
        z, y = f["z"], f["mouth_y"]
        h = sp.holder("Mouth", (0.0, y, z))                                                  # a hooked beak
        sp.brick(h, "Beak", (0.62, 0.46, 0.56), (0.0, y + 0.1, z - 0.2), G.rx(-12), "f0e6c8")
        sp.brick(h, "Beak", (0.34, 0.4, 0.3), (0.0, y - 0.14, z - 0.42), G.rx(40), "e6d8b0")
        sp.brick(h, "Beak", (0.5, 0.2, 0.36), (0.0, y - 0.2, z - 0.16), None, "4a4a52")
        arms(sp, self.limb, hand="ffd54a")
        legs(sp, "6a6a72", "4a4a52")
        sprout(sp, at=(0.0, 3.55, -0.2))
        crown(sp, at=(0.0, 3.62, -0.15), jewel="2f6fd8")


class MonkeyMashKind(Kind):
    """A brown monkey of a potato: a tan face, big round ears with tan middles and a curly tail."""
    pid, display, rarity, area = "MonkeyMash", "Monkey Mash", "Epic", "Jungle"
    skin = ("8b5a2b", "74481f", "a06a38")
    limb = "74481f"
    shoe = "4a2e14"
    face = dict(z=-1.45, eye_y=2.32, eye_dx=0.5, mouth_y=1.55, cheek_dx=0.8)
    shoulder = (1.55, 1.8)
    head = (0.0, 3.7, 0.0)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        tan = "e8c08a"
        octo(sp, 0.35, 2.95, 3.2, 2.9, 2.0, 0.6, (mid, dark, light), core=True)
        sp.extra((2.45, 0.7, 2.2), (0.0, 3.1, 0.05), ori(0, -8, 3), light)
        sp.extra((1.92, 0.88, 0.06), (0.0, 2.34, -1.46), None, tan)                            # its face
        sp.extra((1.26, 0.8, 0.06), (0.0, 1.6, -1.479), None, tan)
        for s in (-1, 1):                                                                    # big round ears
            sp.extra((0.95, 0.95, 0.24), (s * 1.86, 2.45, 0.1), None, mid)
            sp.extra((0.6, 0.6, 0.26), (s * 1.86, 2.45, 0.08), None, tan)
        stick(sp, (0.3, 0.8, 1.35), (0.95, 0.6, 2.15), 0.26, dark, n=(0, 1, 0), t=0.26, material="Plastic")  # a tail
        stick(sp, (0.88, 0.5, 2.15), (1.25, 1.55, 2.25), 0.26, dark, n=(0, 0, 1), t=0.26, material="Plastic")

    def features(self, sp):
        dimples(sp)
        eyes(sp)
        mouth_smile(sp, cheek_col="e88a8a")
        arms(sp, self.limb, hand="e8c08a")
        legs(sp, self.limb, self.shoe)
        sprout(sp)
        crown(sp, jewel="3bd96b")


class TikiTuberKind(Kind):
    """A tiki carved from wood: a heavy brow over wide white eyes, a broad nose, a big toothy grin,
    painted bands and palm fronds springing from its head."""
    pid, display, rarity, area = "TikiTuber", "Tiki Tuber", "Legendary", "Jungle"
    skin = ("9a6a3a", "7e5428", "b07c48")
    limb = "7e5428"
    shoe = "4a2e14"
    face = dict(z=-1.4, eye_y=2.55, eye_dx=0.52, mouth_y=1.4)
    shoulder = (1.5, 2.0)
    head = (0.0, 3.42, 0.0)
    leg_h = 1.25

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 3.3, 3.0, 2.8, 2.0, 0.55, (mid, dark, light), core=True)
        sp.extra((2.08, 0.3, 0.32), (0.0, 3.0, -1.42), None, "5c3a1c")                         # a heavy brow
        sp.extra((0.5, 0.42, 0.3), (0.0, 2.02, -1.48), None, dark)                             # a broad nose
        for y, col in ((0.92, "1fa0a0"), (0.66, "d7372c")):                                   # painted bands
            sp.extra((1.7, 0.16, 0.1), (0.0, y, -1.42), None, col)
        for k, (ang, lean) in enumerate(((62.0, -52.0), (-62.0, -52.0), (150.0, -44.0), (-150.0, -44.0))):   # fronds
            Ry = G.ry(ang)
            R = Ry @ G.rx(lean)
            base = Ry @ np.array((0.0, 3.2, -0.62))
            sp.extra((0.46, 1.9, 0.1 + 0.01 * k), base + R @ (0, 0.9, 0), R, LEAF[k % 2])

    def features(self, sp):
        dimples(sp)
        soot_eyes(sp, w=0.62, hgt=0.52, pupil=(0.3, 0.3))
        f = self.face
        z, y = f["z"], f["mouth_y"]
        h = sp.holder("Mouth", (0.0, y, z))                                                  # a toothy grin
        sp.plate(h, "Mouth", (1.2, 0.44, 0.1), (0.0, y, z - 0.04))
        sp.plate(h, "Teeth", (1.0, 0.14, 0.1), (0.0, y + 0.09, z - 0.09), color="fff4e0")
        arms(sp, self.limb)
        legs(sp, self.limb, self.shoe)
        sprout(sp)
        crown(sp, jewel="1fa0a0")


class GoldenIdolKind(Kind):
    """A golden idol: solid gold, a carved headband set with a red gem, gold discs in its ears,
    green gem eyes glowing, glints flashing off it."""
    pid, display, rarity, area = "GoldenIdol", "Golden Idol", "Mythic", "Jungle"
    skin = ("f5c518", "d9a20c", "ffe066")
    limb = "d9a20c"
    shoe = "a87a0c"
    face = dict(z=-1.45, eye_y=2.25, eye_dx=0.5, mouth_y=1.5)
    shoulder = (1.55, 1.8)
    head = (0.0, 3.62, 0.0)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 2.95, 3.2, 2.9, 2.0, 0.6, (mid, dark, light), core=True)
        sp.extra((2.45, 0.7, 2.2), (0.0, 3.1, 0.05), ori(0, -8, 3), light)
        sp.extra((3.3, 0.42, 3.0), (0.0, 3.0, 0.0), None, "c88a0c")                            # a carved headband
        sp.extra((0.44, 0.44, 0.1), (0.0, 3.0, -1.56), G.rz(45), "ff2a3a", material="Neon")    # set with a gem
        for s in (-1, 1):
            sp.extra((0.72, 0.72, 0.2), (s * 1.78, 2.15, 0.0), None, light)                    # ear discs
        star(sp, sp.extra, (1.95, 3.35, -0.55), 0.8, "fffbe6", ori(0, -30, 45))                # glints
        star(sp, sp.extra, (-1.0, 0.85, -1.53), 0.55, "fffbe6")

    def features(self, sp):
        dimples(sp, col="a87a0c")
        glow_eyes(sp, "3bd96b", glint_col=INK, w=0.5, hgt=0.52)
        mouth_smile(sp, width=0.62, tongue=False, cheeks=False)
        arms(sp, self.limb)
        legs(sp, self.limb, self.shoe)
        sprout(sp)
        crown(sp, cols=("e0a800", "fff1a8", "ffe58a"), jewel="3bd96b")


JUNGLE = [VineSpudKind(), BananaTaterKind(), ParrotPotatoKind(), MonkeyMashKind(), TikiTuberKind(), GoldenIdolKind()]
