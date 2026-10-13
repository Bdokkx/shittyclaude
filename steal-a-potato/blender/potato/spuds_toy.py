"""Toy Town potatoes, worst to best: BlockSpud, TeddyTater, DuckySpud, RoboSpud, JackSpud, GeneralTater.
Same rig, features and rules as the Meadow Patch kinds (spuds.py)."""
import numpy as np

import spsgeo as G

from .bricks import ori, shade
from .spuds import (Kind, arms, crown, dimples, eyes, legs, mouth_smile, octo, sprout)
from .spuds_lava import glow_eyes, stick

BUBBLE = 0.45


class BlockSpudKind(Kind):
    """A toy building brick: square and bright red, four big studs on top."""
    pid, display, rarity, area = "BlockSpud", "Block Spud", "Epic", "Toy"
    skin = ("e3342f", "c22824", "f05a50")
    limb = "c22824"
    shoe = "2f6fd8"
    face = dict(z=-1.3, eye_y=2.0, eye_dx=0.52, mouth_y=1.25, cheek_dx=0.88)
    shoulder = (1.45, 1.6)
    head = (0.0, 3.32, 0.0)
    leg_h = 1.15

    def body(self, sp):
        mid, dark, light = self.skin
        sp.core((2.9, 2.6, 2.6), (0.0, 1.6, 0.0), None, mid)                                    # square
        sp.extra((2.96, 2.4, 2.4), (0.0, 1.55, 0.02), None, dark)
        for x in (-0.68, 0.68):                                                              # four big studs
            for z in (-0.62, 0.62):
                k = 1.0 + 0.03 * (x > 0) + 0.015 * (z > 0)
                sp.extra((0.86 * k, 0.42, 0.86 * k), (x, 3.08, z), None, light)
                sp.extra((0.7 * k, 0.4, 0.7 * k), (x, 3.08, z), G.ry(45), mid)

    def features(self, sp):
        dimples(sp)
        eyes(sp)
        mouth_smile(sp)
        arms(sp, self.limb)
        legs(sp, self.limb, self.shoe)
        sprout(sp, at=(0.0, 3.2, 0.0))
        crown(sp, jewel="2f6fd8")


class TeddyTaterKind(Kind):
    """A teddy bear: soft brown, round ears with tan middles, a tan muzzle with a black nose and a red
    bow tie."""
    pid, display, rarity, area = "TeddyTater", "Teddy Tater", "Legendary", "Toy"
    skin = ("a8743a", "8e5e2a", "bc884c")
    limb = "8e5e2a"
    shoe = "6a4420"
    face = dict(z=-1.45, eye_y=2.38, eye_dx=0.52, mouth_y=1.48, cheek_dx=0.92)
    shoulder = (1.55, 1.8)
    head = (0.0, 3.7, 0.0)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        tan = "e8c896"
        octo(sp, 0.35, 2.95, 3.2, 2.9, 2.0, 0.6, (mid, dark, light), core=True)
        sp.extra((2.45, 0.7, 2.2), (0.0, 3.1, 0.05), ori(0, -8, 3), light)
        for s in (-1, 1):                                                                    # round ears
            sp.extra((0.95, 0.95, 0.4), (s * 1.12, 3.3, 0.2), G.rz(45 * 0.5), mid)
            sp.extra((0.58, 0.58, 0.42), (s * 1.12, 3.3, 0.18), G.rz(22.5 * 0.5), tan)
        sp.extra((1.1, 0.78, 0.08), (0.0, 1.7, -1.47), None, tan)                                # a muzzle
        sp.extra((0.36, 0.24, 0.12), (0.0, 1.92, -1.53), None, "1e1a22")                          # a black nose
        for s in (-1, 1):                                                                    # a red bow tie
            sp.extra((0.5, 0.42, 0.14 + 0.02 * (s > 0)), (s * 0.26, 0.82, -1.5), G.rz(s * 20), "d7372c")

    def features(self, sp):
        dimples(sp)
        eyes(sp, w=0.44, hgt=0.56)
        mouth_smile(sp, width=0.44, tongue=False, cheek_col="e88a8a")
        arms(sp, self.limb, hand="e8c896")
        legs(sp, self.limb, self.shoe)
        sprout(sp)
        crown(sp, jewel="d7372c")


class DuckySpudKind(Kind):
    """A rubber duck: bright yellow, a flat orange beak, a curl of a tuft on its head, a little
    tail cocked up behind and bath bubbles round it."""
    pid, display, rarity, area = "DuckySpud", "Ducky Spud", "Legendary", "Toy"
    skin = ("ffd83a", "f0c020", "ffe46a")
    limb = "f0c020"
    shoe = "ff8a1f"
    face = dict(z=-1.45, eye_y=2.45, eye_dx=0.55, mouth_y=1.7)
    shoulder = (1.55, 1.8)
    head = (-0.15, 3.68, 0.0)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 2.95, 3.2, 2.9, 2.0, 0.6, (mid, dark, light), core=True)
        sp.extra((2.45, 0.7, 2.2), (0.0, 3.1, 0.05), ori(0, -8, 3), light)
        sp.extra((0.3, 0.7, 0.3), (0.62, 3.6, 0.1), G.rz(-20), mid)                             # a curl of a tuft
        sp.extra((0.26, 0.5, 0.26), (0.85, 3.98, 0.1), G.rz(-70), mid)
        sp.extra((1.2, 0.8, 0.9), (0.0, 1.6, 1.62), G.rx(-35), mid)                             # a little tail
        for pos, k in (((-2.05, 0.9, -0.6), 0.6), ((1.95, 3.4, 0.2), 0.45)):                     # bath bubbles
            sp.extra((k, k, k), pos, ori(35, 45, 0), "e2f8ff", transparency=BUBBLE)

    def features(self, sp):
        dimples(sp)
        eyes(sp, w=0.44, hgt=0.6)
        f = self.face
        z, y = f["z"], f["mouth_y"]
        h = sp.holder("Mouth", (0.0, y, z))                                                  # a flat orange beak
        sp.brick(h, "Beak", (1.1, 0.3, 0.7), (0.0, y + 0.06, z - 0.3), G.rx(-6), "ff8a1f")
        sp.brick(h, "Beak", (0.95, 0.2, 0.55), (0.0, y - 0.18, z - 0.24), G.rx(8), "e8701a")
        arms(sp, self.limb, hand="ffe46a")
        legs(sp, self.limb, self.shoe)
        sprout(sp, at=(-0.15, 3.56, 0.0))
        crown(sp, jewel="ff8a1f")


class RoboSpudKind(Kind):
    """A tin toy robot: riveted silver, glowing square eyes, a grille for a mouth, a screen on its
    chest with a glowing heartbeat, bolts at its sides and an antenna with a red light."""
    pid, display, rarity, area = "RoboSpud", "Robo Spud", "Mythic", "Toy"
    skin = ("b8c0c8", "9aa4ae", "d0d6dc")
    limb = "8a949e"
    shoe = "4a525a"
    face = dict(z=-1.45, eye_y=2.42, eye_dx=0.52, mouth_y=1.78)
    shoulder = (1.55, 1.85)
    head = (0.0, 3.62, 0.0)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 2.95, 3.2, 2.9, 2.0, 0.65, (mid, dark, light), core=True)
        sp.extra((2.45, 0.6, 2.2), (0.0, 3.08, 0.0), None, light)
        sp.extra((1.2, 0.62, 0.1), (0.0, 0.9, -1.47), None, "1e2a2e")                           # a screen on its chest
        sp.extra((0.86, 0.12, 0.12), (0.0, 0.9, -1.5), G.rz(18), "3bff8a", material="Neon")     # with a heartbeat
        for x, y in ((-0.85, 2.85), (0.85, 2.85)):
            sp.extra((0.16, 0.16, 0.1), (x, y, -1.47), None, "e8ecf0")                           # rivets
        stick(sp, (0.0, 3.3, 0.0), (0.0, 4.55, 0.0), 0.12, "6a747e", n=(0, 0, 1), t=0.12, material="Plastic")
        sp.extra((0.34, 0.34, 0.34), (0.0, 4.65, 0.0), ori(35, 45, 0), "ff3b3b", material="Neon")  # a red light
        for s in (-1, 1):
            sp.extra((0.28, 0.5, 0.5), (s * 1.66, 2.4, 0.0), None, "6a747e")                     # bolts at its sides

    def features(self, sp):
        dimples(sp, col="6a747e")
        glow_eyes(sp, "6ff3ff", glint_col="1e2a2e", w=0.5, hgt=0.44)
        f = self.face
        z, y = f["z"], f["mouth_y"]
        h = sp.holder("Mouth", (0.0, y, z))                                                  # a grille
        sp.plate(h, "Mouth", (0.8, 0.34, 0.1), (0.0, y, z - 0.04), color="1e2a2e")
        for x in (-0.2, 0.0, 0.2):
            sp.plate(h, "Grille", (0.06, 0.3, 0.1), (x, y, z - 0.09), color="c8d0d8")
        arms(sp, self.limb, hand="6a747e")
        legs(sp, self.limb, self.shoe)
        sprout(sp, at=(-0.45, 3.35, 0.2))
        crown(sp, jewel="ff3b3b")


class JackSpudKind(Kind):
    """A jack-in-the-box's jester: purple and yellow, a three-pointed jester's hat with gold bells, a
    red clown's nose and harlequin diamonds."""
    pid, display, rarity, area = "JackSpud", "Jack Spud", "Secret", "Toy"
    skin = ("8a3fd0", "7030b4", "a05ae0")
    limb = "ffd23f"
    shoe = "8a3fd0"
    face = dict(z=-1.45, eye_y=2.3, eye_dx=0.5, mouth_y=1.5, cheek_dx=0.84)
    shoulder = (1.55, 1.8)
    head = (0.0, 3.45, 0.0)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        yellow = "ffd23f"
        octo(sp, 0.35, 2.95, 3.2, 2.9, 2.0, 0.6, (mid, dark, yellow), core=True)
        sp.extra((2.9, 0.42, 2.6), (0.0, 3.1, 0.0), None, "ffffff")                             # a jester's hat: band
        for k, (lean, col) in enumerate(((44.0, mid), (0.0, yellow), (-44.0, mid))):          # three points
            R = G.rz(lean) @ G.rx(12 if k == 1 else 0)
            base = np.array((-np.sin(np.radians(lean)) * 0.7, 3.25, 0.25 if k == 1 else 0.0))
            sp.extra((0.5, 1.5, 0.5 + 0.02 * k), base + R @ (0, 0.72, 0), R @ G.ry(45), col)
            if k != 1:
                sp.extra((0.32, 0.32, 0.32), base + R @ (0, 1.5, 0), ori(35, 45, 0), "ffd23f", material="Neon")
        sp.extra((0.34, 0.34, 0.3), (0.0, 1.92, -1.58), ori(0, 0, 45), "e8302a")                 # a red nose
        for x, col in ((-0.62, yellow), (0.62, yellow)):
            sp.extra((0.5, 0.5, 0.1), (x, 0.75, -1.47), G.rz(45), col)                           # harlequin diamonds

    def features(self, sp):
        dimples(sp)
        eyes(sp)
        mouth_smile(sp, width=0.72, cheek_col="ff6a8a")
        arms(sp, self.limb, hand="ffffff")
        legs(sp, self.limb, self.shoe)
        sprout(sp, at=(0.0, 3.35, -0.2))
        crown(sp, at=(0.0, 3.45, -0.25), jewel="ffd23f")


class GeneralTaterKind(Kind):
    """A toy soldier general: a red coat with a white cross-belt, gold buttons, gold epaulettes and a
    medal, a tall black busby with a gold badge and a red plume, and a black moustache."""
    pid, display, rarity, area = "GeneralTater", "General Tater", "Secret", "Toy"
    skin = ("c8202a", "a81a22", "dc3a40")
    limb = "1e2a6a"
    shoe = "1e1a22"
    face = dict(z=-1.45, eye_y=2.38, eye_dx=0.5, mouth_y=1.62)
    shoulder = (1.55, 1.85)
    head = (0.0, 4.6, 0.1)
    leg_h = 1.25

    def body(self, sp):
        mid, dark, light = self.skin
        gold = "f5c518"
        octo(sp, 0.35, 2.95, 3.2, 2.9, 2.0, 0.6, (mid, dark, light), core=True)
        stick(sp, (-0.95, 1.45, -1.5), (0.95, 0.35, -1.5), 0.3, "ffffff", n=(0, 0, -1), t=0.1,
              material="Plastic")                                                             # a cross-belt
        for y in (0.95, 0.5):
            sp.extra((0.18, 0.18, 0.1), (-0.62, y, -1.53), G.rz(45), gold)                       # gold buttons
        for s in (-1, 1):
            sp.extra((0.9, 0.26, 1.2), (s * 1.3, 2.98, 0.0), G.rz(-s * 8), gold)                 # epaulettes
        sp.extra((0.26, 0.26, 0.1), (0.68, 1.15, -1.5), G.rz(45), "3b8bff")                       # a medal
        sp.extra((2.1, 1.6, 1.9), (0.0, 3.75, 0.05), None, "1e1a22")                             # a tall busby
        sp.extra((0.42, 0.42, 0.1), (0.0, 3.55, -1.03), G.rz(45), gold)
        sp.extra((0.26, 0.9, 0.26), (0.85, 4.35, -0.3), G.rz(-12), "e8302a")                     # a red plume

    def features(self, sp):
        dimples(sp)
        eyes(sp)
        f = self.face
        mouth_smile(sp, width=0.5, cheeks=False)
        z, y = f["z"], f["mouth_y"]
        for s in (-1, 1):                                                                    # a black moustache
            sp.extra((0.62, 0.22, 0.12), (s * 0.33, y + 0.3, z - 0.07), G.rz(s * 14), "1e1a22")
        arms(sp, self.limb, hand="ffffff")
        legs(sp, self.limb, self.shoe)
        sprout(sp, at=(-0.4, 4.5, 0.2))
        crown(sp, jewel="3b8bff")


TOY = [BlockSpudKind(), TeddyTaterKind(), DuckySpudKind(), RoboSpudKind(), JackSpudKind(), GeneralTaterKind()]
