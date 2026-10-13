"""Spud Olympus potatoes, worst to best: MarbleSpud, LaurelTater, HeroFry, PegasusSpud, PoseidonTuber,
ZeusSpud. Same rig, features and rules as the Meadow Patch kinds (spuds.py).

HeroFry's shield, PoseidonTuber's trident and ZeusSpud's thunderbolt are held in the left hand:
children of HandL, welded to it, like the Candy Crops' lollipop."""
import math

import numpy as np

import spsgeo as G

from .bricks import ori
from .spuds import (Kind, arms, crown, dimples, eyes, legs, mouth_smile, octo, sprout)
from .spuds_candy import hand_at, held
from .spuds_lava import crack, stick

GOLD = ("f5c518", "d9a20c", "ffe066")
LEAF = ("5a9a3a", "6cb04a")


def held_stick(sp, name, a, b, w, col, n=(0.0, 0.0, 1.0), t=None, side="L", material="Plastic"):
    """stick(), held in a hand: a bar from a to b, a child of the hand and welded to it."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = b - a
    L = float(np.linalg.norm(d))
    y = d / L
    z = np.asarray(n, float)
    z = z - y * (z @ y)
    z /= np.linalg.norm(z)
    x = np.cross(y, z)
    return held(sp, name, (w, L, t if t is not None else w), (a + b) / 2, np.column_stack((x, y, z)), col,
                side=side, material=material)


class MarbleSpudKind(Kind):
    """A statue in white marble: grey veins running through the stone and a gold band with a Greek key
    round its head."""
    pid, display, rarity, area = "MarbleSpud", "Marble Spud", "Legendary", "Olympus"
    skin = ("f0eee8", "dcd8d0", "faf8f4")
    limb = "dcd8d0"
    shoe = "b8b2a8"
    face = dict(z=-1.45, eye_y=2.22, eye_dx=0.5, mouth_y=1.48, cheek_dx=0.84)
    shoulder = (1.55, 1.8)
    head = (0.0, 3.07, 0.0)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        W, D = 3.2, 2.9
        octo(sp, 0.35, 2.95, W, D, 2.0, 0.6, (mid, dark, light), core=True)
        vein = "8a867e"                                                                       # grey veins
        z = -D / 2
        crack(sp, [(0.98, 1.12, z), (0.3, 0.42, z)], (0, 0, -1), w=0.1, col=vein, material="Plastic")
        crack(sp, [(-0.98, 1.25, z), (-0.62, 0.95, z), (-0.74, 0.5, z)], (0, 0, -1), w=0.1, col=vein, material="Plastic")
        crack(sp, [(W / 2, 2.4, 0.7), (W / 2, 1.2, 0.15)], (1, 0, 0), w=0.1, col=vein, material="Plastic")
        sp.extra((3.3, 0.22, 3.0), (0.0, 2.76, 0.0), None, GOLD[0])                              # a gold circlet
        for k, x in enumerate((-0.75, -0.25, 0.25, 0.75)):
            sp.extra((0.26, 0.12, 0.1), (x, 2.73 + 0.06 * (k % 2), -1.54), None, "b8860b")       # its Greek key

    def features(self, sp):
        dimples(sp)
        eyes(sp)
        mouth_smile(sp)
        arms(sp, self.limb, hand="faf8f4")
        legs(sp, self.limb, self.shoe)
        sprout(sp)
        crown(sp, jewel="3b8bff")


class LaurelTaterKind(Kind):
    """A Greek champion: a wreath of laurel leaves round its head and the torch held high in its left
    hand."""
    pid, display, rarity, area = "LaurelTater", "Laurel Tater", "Mythic", "Olympus"
    skin = ("d8b47a", "c09a5c", "e6c890")
    limb = "c09a5c"
    shoe = "8a5a2a"
    face = dict(z=-1.45, eye_y=2.22, eye_dx=0.5, mouth_y=1.48, cheek_dx=0.84)
    shoulder = (1.55, 1.8)
    head = (0.0, 3.07, 0.0)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 2.95, 3.2, 2.9, 2.0, 0.6, (mid, dark, light), core=True)
        sp.extra((3.28, 0.2, 2.98), (0.0, 2.74, 0.0), None, "3e7a2a")                           # a laurel wreath
        for k in range(6):
            a = math.radians(-90.0 + 60.0 * k + 30.0)
            pos = np.array((1.72 * math.cos(a), 2.8, 1.6 * math.sin(a)))
            R = G.ry(-math.degrees(a)) @ G.rz(32)
            sp.extra((0.8, 0.12 + 0.01 * (k % 2), 0.4), pos, R, LEAF[k % 2])

    def features(self, sp):
        dimples(sp)
        eyes(sp)
        mouth_smile(sp)
        arms(sp, self.limb)
        legs(sp, self.limb, self.shoe)
        sprout(sp)
        crown(sp, jewel="3bd96b")
        hc, _R = hand_at(sp, "L")                                                             # the torch
        held_stick(sp, "Torch", hc - (0.0, 0.5, 0.0), hc + (0.0, 1.15, 0.0), 0.24, GOLD[1])
        held(sp, "Torch", (0.5, 0.5, 0.5), hc + (0.0, 1.5, 0.0), G.rz(45) @ G.rx(12), "ff8a1a", material="Neon")


class HeroFryKind(Kind):
    """A hero of old: tall and bronzed, a bronze helmet with cheek guards and a red horsehair crest,
    a red cape and a round bronze shield on its left arm."""
    pid, display, rarity, area = "HeroFry", "Hero Fry", "Secret", "Olympus"
    skin = ("ecc488", "d4a86c", "f6d6a0")
    limb = "d4a86c"
    shoe = "8a5a2a"
    face = dict(z=-1.3, eye_y=2.45, eye_dx=0.45, mouth_y=1.7, cheek_dx=0.8)
    shoulder = (1.45, 2.0)
    head = (0.0, 4.0, -0.55)
    leg_h = 1.3

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 3.3, 2.9, 2.6, 1.9, 0.5, (mid, dark, light), core=True)
        bronze, red = "c8842a", "c8202a"
        sp.extra((3.1, 0.95, 2.8), (0.0, 3.42, 0.0), None, bronze)                              # a bronze helmet
        for s in (-1, 1):
            sp.extra((0.36, 0.9, 0.3), (s * 0.9, 2.82, -1.36), None, "a8661c")                   # cheek guards
        sp.extra((0.42, 1.45, 1.7), (0.0, 4.55, 0.75), None, red)                               # a horsehair crest
        sp.extra((0.38, 1.1, 0.8), (0.0, 4.25, 1.75), G.rx(18), "a81a22")
        sp.extra((3.4, 2.9, 0.16), (0.0, 1.85, 1.42), None, red)                                # a red cape

    def features(self, sp):
        dimples(sp)
        eyes(sp, w=0.44, hgt=0.56)
        mouth_smile(sp, width=0.5)
        arms(sp, self.limb)
        legs(sp, self.limb, self.shoe)
        sprout(sp, at=(0.55, 3.85, 0.4))
        crown(sp, jewel="c8202a")
        hc, R = hand_at(sp, "L")                                                              # a round shield
        out = np.array((-1.0, 0.0, 0.0))
        c = hc + out * 0.25 + (0.0, 0.25, 0.0)
        Rs = G.ry(-18)
        held(sp, "Shield", (1.7, 1.7, 0.16), c, Rs, "b07a3a")
        held(sp, "Shield", (1.6, 1.6, 0.2), c, Rs @ G.rz(45), "c88a44")
        held(sp, "Shield", (0.6, 0.6, 0.26), c + out * 0.03, Rs @ G.rz(22.5), GOLD[0])


class PegasusSpudKind(Kind):
    """Pegasus: white, great feathered wings tipped gold and a pale blue mane flowing down the back of
    its head."""
    pid, display, rarity, area = "PegasusSpud", "Pegasus Spud", "Divine", "Olympus"
    skin = ("f8f6ff", "e6e4f2", "ffffff")
    limb = "e6e4f2"
    shoe = GOLD[0]
    face = dict(z=-1.45, eye_y=2.32, eye_dx=0.52, mouth_y=1.55, cheek_dx=0.86)
    shoulder = (1.55, 1.8)
    head = (0.0, 3.07, -0.1)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 2.95, 3.2, 2.9, 2.0, 0.6, (mid, dark, light), core=True)
        for s in (-1, 1):                                                                    # great wings
            root = np.array((s * 0.85, 2.45, 1.2))
            for k, (a, L, w, col) in enumerate(((60.0, 2.7, 0.72, "ffffff"), (33.0, 2.5, 0.72, "eef0ff"),
                                                (6.0, 2.1, 0.68, GOLD[2]))):
                d = np.array((s * math.cos(math.radians(a)), math.sin(math.radians(a)), 0.35))
                stick(sp, root, root + d * L, w, col, n=(0, 0, 1), t=0.16 + 0.02 * k, material="Plastic")
        mane = ("9fd0ff", "b8a8ff", "8fbaf0")
        for k, (y, z) in enumerate(((3.1, 0.3), (2.6, 1.0), (1.9, 1.45))):                    # a flowing mane
            sp.extra((0.6 + (0.06, 0.0, -0.05)[k], 0.9, 0.7), (0.0, y, z), G.rx(-25 - 15 * k), mane[k])

    def features(self, sp):
        dimples(sp)
        eyes(sp, w=0.5, hgt=0.7)
        mouth_smile(sp)
        arms(sp, self.limb, hand="ffffff")
        legs(sp, self.limb, self.shoe)
        sprout(sp, at=(0.0, 2.95, -0.1))
        crown(sp, jewel="9fd0ff")


class PoseidonTuberKind(Kind):
    """The god of the sea: sea green, dark teal hair, a great beard of white surf and a golden trident
    in its left hand."""
    pid, display, rarity, area = "PoseidonTuber", "Poseidon Tuber", "Divine", "Olympus"
    skin = ("2fa8a0", "238a84", "48c0b8")
    limb = "238a84"
    shoe = GOLD[1]
    face = dict(z=-1.45, eye_y=2.38, eye_dx=0.5, mouth_y=1.62)
    shoulder = (1.55, 1.85)
    head = (0.0, 3.5, 0.0)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 2.95, 3.2, 2.9, 2.0, 0.6, (mid, dark, light), core=True)
        sp.extra((2.45, 0.6, 2.5), (0.0, 3.08, 0.3), ori(0, -6, 0), "15607a")                    # dark teal hair
        sp.extra((1.7, 1.15, 0.1), (0.0, 1.32, -1.47), None, "d8f4f8")                           # a beard of surf
        sp.extra((1.2, 0.6, 0.12), (0.0, 0.45, -1.47), None, "b8e8f0")
        sp.extra((1.2, 0.2, 0.18), (0.0, 1.89, -1.5), None, "ffffff")                            # a moustache

    def features(self, sp):
        dimples(sp)
        eyes(sp, brows=(4.0, -4.0), brow_col="f0fbff")
        mouth_smile(sp, width=0.5, cheeks=False)
        arms(sp, self.limb)
        legs(sp, self.limb, self.shoe)
        sprout(sp)
        crown(sp, jewel="3bd9c8")
        hc, _R = hand_at(sp, "L")                                                             # a golden trident
        held_stick(sp, "Trident", hc - (0.0, 0.9, 0.0), hc + (0.0, 3.3, 0.0), 0.16, GOLD[1])
        top = hc + (0.0, 3.3, 0.0)
        held_stick(sp, "Trident", top + (-0.5, 0.0, 0.0), top + (0.5, 0.0, 0.0), 0.16, GOLD[0], t=0.18)
        for k, x in enumerate((-0.45, 0.0, 0.45)):
            held_stick(sp, "Trident", top + (x, -0.05, 0.0), top + (x, 0.8 if x == 0.0 else 0.62, 0.0), 0.14, GOLD[0],
                       t=0.2 + 0.02 * k)


class ZeusSpudKind(Kind):
    """The king of the gods: a great white beard and moustache, bushy white brows and hair, gold sandals
    and a glowing thunderbolt raised in its left hand."""
    pid, display, rarity, area = "ZeusSpud", "Zeus Spud", "Divine", "Olympus"
    skin = ("f0d8b8", "dcc09a", "f8e6cc")
    limb = "f4f4fa"
    shoe = GOLD[1]
    face = dict(z=-1.45, eye_y=2.42, eye_dx=0.5, mouth_y=1.62)
    shoulder = (1.55, 1.85)
    head = (0.0, 3.57, 0.0)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 2.95, 3.2, 2.9, 2.0, 0.6, (mid, dark, light), core=True)
        sp.extra((2.45, 0.7, 2.2), (0.0, 3.1, 0.05), ori(0, -8, 3), "ffffff")                    # white hair
        sp.extra((1.9, 1.3, 0.1), (0.0, 1.22, -1.47), None, "e6eaf2")                            # a great beard
        sp.extra((1.3, 0.55, 0.12), (0.0, 0.42, -1.47), None, "d8dde8")
        sp.extra((1.4, 0.2, 0.18), (0.0, 1.92, -1.5), None, "ffffff")                            # a moustache
        for s in (-1, 1):
            sp.extra((0.5, 1.1, 1.4), (s * 1.5, 2.6, 0.2), None, "ffffff")                        # and at its sides

    def features(self, sp):
        dimples(sp)
        eyes(sp, brows=(-6.0, 6.0), brow_col="ffffff", brow_dy=(0.02, 0.02))
        mouth_smile(sp, width=0.5, cheeks=False)
        arms(sp, "f4f4fa", hand="f0d8b8")
        legs(sp, "f4f4fa", self.shoe)
        sprout(sp)
        crown(sp, jewel="ffe83a", size=1.2)
        hc, _R = hand_at(sp, "L")                                                             # a thunderbolt raised
        pts = [hc + (0.1, 0.2, 0.0), hc + (-0.35, 1.3, 0.0), hc + (0.3, 1.45, 0.0), hc + (-0.2, 2.7, 0.0)]
        for k in range(3):
            a, b = pts[k], pts[k + 1]
            e = (b - a) / np.linalg.norm(b - a) * 0.12
            held_stick(sp, "Thunderbolt", a - e, b + e, 0.26 - 0.04 * k, "ffe83a", t=0.22 + 0.03 * k, material="Neon")


OLYMPUS = [MarbleSpudKind(), LaurelTaterKind(), HeroFryKind(), PegasusSpudKind(), PoseidonTuberKind(),
           ZeusSpudKind()]
