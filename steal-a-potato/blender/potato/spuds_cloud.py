"""Cloud Kingdom potatoes, worst to best: CloudPuff, RainySpud, SunnyTater, RainbowFry, ThunderTuber,
SeraphSpud. Same rig, features and rules as the Meadow Patch kinds (spuds.py).

RainySpud's umbrella is held in its left hand: children of HandL, welded to it, like the Candy
Crops' lollipop."""
import math

import numpy as np

import spsgeo as G

from .bricks import ori
from .spuds import (INK, Kind, arms, crown, dimples, eyes, legs, mouth_smile, octo, sprout)
from .spuds_candy import hand_at, held
from .spuds_cosmic import ring
from .spuds_lava import crack, glow_eyes, stick

RAINBOW = ("ff3b3b", "ff9a1f", "ffe83a", "3bd96b", "3b8bff", "6a4cff", "b44dff")


def puffs(sp, spec):
    """Rounded puffs of cloud: cubes turned every which way, (size, position, (rx, ry, rz), colour)."""
    for k, pos, r, col in spec:
        sp.extra((k, k, k), pos, ori(*r), col)


class CloudPuffKind(Kind):
    """A little white cloud: puff upon soft puff, a face peeping out of the middle."""
    pid, display, rarity, area = "CloudPuff", "Cloud Puff", "Epic", "Cloud"
    skin = ("fbfcff", "e8eef8", "ffffff")
    limb = "e0e8f4"
    shoe = "a8c8f0"
    face = dict(z=-1.25, eye_y=2.1, eye_dx=0.48, mouth_y=1.38, cheek_dx=0.82)
    shoulder = (1.4, 1.75)
    head = (0.05, 3.95, 0.1)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        sp.core((2.8, 2.6, 2.5), (0.0, 1.65, 0.0), None, mid)
        pale = "dfe8f6"
        puffs(sp, ((1.6, (-0.5, 3.0, 0.25), (20, 30, 15), light), (1.5, (0.65, 3.05, 0.05), (-15, 50, -10), mid),
                   (1.25, (0.05, 3.5, 0.5), (30, 15, 25), light), (1.35, (-1.45, 2.25, 0.2), (10, 40, 30), pale),
                   (1.25, (1.45, 2.15, 0.3), (-20, 20, -25), light), (1.15, (-1.4, 1.0, 0.1), (25, 10, 10), mid),
                   (1.15, (1.42, 1.05, -0.1), (-10, 35, 20), pale), (1.3, (0.0, 0.5, 0.3), (15, 45, 0), light),
                   (0.9, (-1.08, 2.85, -0.85), (20, 30, 40), mid)))

    def features(self, sp):
        dimples(sp)
        eyes(sp)
        mouth_smile(sp)
        arms(sp, self.limb, hand="ffffff")
        legs(sp, self.limb, self.shoe)
        sprout(sp)
        crown(sp, jewel="7ad1ff")


class RainySpudKind(Kind):
    """Dressed for the rain: a yellow raincoat with its hood up, blue wellies, a red umbrella held
    up in its left hand and raindrops falling."""
    pid, display, rarity, area = "RainySpud", "Rainy Spud", "Legendary", "Cloud"
    skin = ("ffd23f", "f0bc20", "ffe27a")
    limb = "f0bc20"
    shoe = "2f6fd8"
    face = dict(z=-1.45, eye_y=2.2, eye_dx=0.5, mouth_y=1.45, cheek_dx=0.84)
    shoulder = (1.55, 1.8)
    head = (0.25, 3.72, 0.0)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 2.95, 3.2, 2.9, 2.0, 0.6, (mid, dark, light), core=True)
        sp.extra((2.9, 0.75, 2.6), (0.0, 3.15, 0.1), None, light)                               # its hood up
        sp.extra((2.2, 0.16, 0.1), (0.0, 2.84, -1.47), None, dark)                              # the hood's edge
        for pos in ((-2.9, 2.2, -0.4), (-1.75, 1.7, -0.6), (-3.3, 1.1, -0.2)):
            sp.extra((0.22, 0.22, 0.22), pos, ori(35, 45, 0), "7ad1ff")                          # raindrops

    def features(self, sp):
        dimples(sp)
        eyes(sp)
        mouth_smile(sp)
        arms(sp, self.limb, hand="ffd23f")
        legs(sp, "2f6fd8", self.shoe)
        sprout(sp, at=(0.25, 3.6, 0.0))
        crown(sp, jewel="2f6fd8")
        hc, _R = hand_at(sp, "L")                                                             # a red umbrella
        held(sp, "Umbrella", (0.12, 3.6, 0.12), hc + (0.0, 1.55, 0.0), None, "4a3a2a")
        top = hc + (0.0, 3.4, 0.0)
        held(sp, "Umbrella", (2.7, 0.3, 2.7), top, G.ry(22.5), "e8302a")                        # a domed canopy
        held(sp, "Umbrella", (1.75, 0.4, 1.75), top + (0.0, 0.3, 0.0), G.ry(67.5), "c8221e")
        held(sp, "Umbrella", (0.2, 0.36, 0.2), top + (0.0, 0.62, 0.0), None, "4a3a2a")


class SunnyTaterKind(Kind):
    """A little sun: warm yellow, glowing rays fanned round its head and shoulders."""
    pid, display, rarity, area = "SunnyTater", "Sunny Tater", "Mythic", "Cloud"
    skin = ("ffcf3a", "f0b020", "ffe070")
    limb = "f0b020"
    shoe = "ff8a1f"
    face = dict(z=-1.45, eye_y=2.32, eye_dx=0.5, mouth_y=1.55, cheek_dx=0.84)
    shoulder = (1.55, 1.8)
    head = (0.0, 3.7, 0.0)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 2.95, 3.2, 2.9, 2.0, 0.6, (mid, dark, light), core=True)
        sp.extra((2.45, 0.7, 2.2), (0.0, 3.1, 0.05), ori(0, -8, 3), light)
        c = np.array((0.0, 2.4, 0.9))                                                         # rays round its top
        for k in range(6):
            a = math.radians(-10.0 + 40.0 * k)
            d = np.array((math.cos(a), math.sin(a), 0.0))
            R = G.rz(math.degrees(a) - 90.0)
            sp.extra((0.62, 1.1, 0.14 + 0.02 * (k % 2)), c + d * 2.3, R, "ffb02a" if k % 2 else "ffe83a",
                     material="Neon")

    def features(self, sp):
        dimples(sp)
        eyes(sp)
        mouth_smile(sp, cheek_col="ff8a6a")
        arms(sp, self.limb)
        legs(sp, self.limb, self.shoe)
        sprout(sp)
        crown(sp, jewel="ff8a1f")


class RainbowFryKind(Kind):
    """A tall fry under its own rainbow: a glowing arc of seven colours over its head, a little cloud
    at each end."""
    pid, display, rarity, area = "RainbowFry", "Rainbow Fry", "Secret", "Cloud"
    skin = ("f4f0ff", "e0dcf4", "ffffff")
    limb = "c8c0ec"
    shoe = "b44dff"
    face = dict(z=-1.3, eye_y=2.55, eye_dx=0.45, mouth_y=1.78, cheek_dx=0.8)
    shoulder = (1.45, 2.0)
    head = (0.0, 3.72, 0.0)
    leg_h = 1.3

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 3.3, 2.9, 2.6, 1.9, 0.5, (mid, dark, light), core=True)
        c = np.array((0.0, 3.2, 0.75))                                                        # an arc of seven colours
        r = 2.45
        for k, col in enumerate(RAINBOW):
            a0, a1 = math.radians(180.0 * k / 7), math.radians(180.0 * (k + 1) / 7)
            p0 = c + r * np.array((math.cos(a0), math.sin(a0), 0.0))
            p1 = c + r * np.array((math.cos(a1), math.sin(a1), 0.0))
            e = (p1 - p0) * 0.06
            stick(sp, p0 - e, p1 + e, 0.5, col, n=(0, 0, 1), t=0.2 + 0.02 * (k % 2))
        for x in (-r, r):                                                                    # a cloud at each end
            sp.extra((0.95, 0.95, 0.95), c + (x, -0.15, 0.0), ori(25, 40, 15), "ffffff")

    def features(self, sp):
        dimples(sp)
        eyes(sp, w=0.44, hgt=0.6)
        mouth_smile(sp, width=0.5)
        arms(sp, self.limb, hand="ffffff")
        legs(sp, self.limb, self.shoe)
        sprout(sp)
        crown(sp, jewel="ff3b3b")


class ThunderTuberKind(Kind):
    """A thundercloud: dark storm grey, its top piled with dark cloud, glowing yellow eyes and bolts of
    lightning striking down from it."""
    pid, display, rarity, area = "ThunderTuber", "Thunder Tuber", "Secret", "Cloud"
    skin = ("5a6070", "4a505e", "6e7484")
    limb = "4a505e"
    shoe = "2a2e38"
    face = dict(z=-1.45, eye_y=2.28, eye_dx=0.5, mouth_y=1.5)
    shoulder = (1.55, 1.8)
    head = (0.0, 3.95, 0.1)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 2.95, 3.2, 2.9, 2.0, 0.6, (mid, dark, light), core=True)
        puffs(sp, ((1.5, (-0.6, 3.05, 0.25), (20, 30, 15), dark), (1.4, (0.7, 3.1, 0.05), (-15, 50, -10), mid),
                   (1.2, (0.0, 3.5, 0.5), (30, 15, 25), dark), (1.1, (-1.55, 2.6, 0.3), (10, 40, 30), mid)))
        bolt = "ffe83a"                                                                       # lightning striking
        crack(sp, [(1.75, 1.9, 0.7), (2.15, 1.25, 0.7), (1.85, 1.05, 0.7), (2.3, 0.2, 0.7)], (0, 0, -1),
              w=0.2, col=bolt)
        crack(sp, [(-1.75, 1.5, 0.6), (-2.1, 0.95, 0.6), (-1.85, 0.8, 0.6), (-2.2, 0.2, 0.6)], (0, 0, -1),
              w=0.18, col=bolt)

    def features(self, sp):
        dimples(sp, col="2a2e38")
        glow_eyes(sp, "ffe83a", glint_col=INK, w=0.5, hgt=0.44)
        mouth_smile(sp, width=0.5, cheeks=False)
        arms(sp, self.limb, hand="8a90a0")
        legs(sp, self.limb, self.shoe)
        sprout(sp, at=(0.0, 3.85, 0.1))
        crown(sp, jewel="ffe83a")


class SeraphSpudKind(Kind):
    """An angel: soft white, a glowing gold halo over its head and white feathered wings."""
    pid, display, rarity, area = "SeraphSpud", "Seraph Spud", "Divine", "Cloud"
    skin = ("fbf8f0", "ece6d8", "ffffff")
    limb = "ece6d8"
    shoe = "f5c518"
    face = dict(z=-1.45, eye_y=2.32, eye_dx=0.5, mouth_y=1.55)
    shoulder = (1.55, 1.8)
    head = (0.0, 3.07, 0.0)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 2.95, 3.2, 2.9, 2.0, 0.6, (mid, dark, light), core=True)
        ring(sp, (0.0, 4.5, 0.0), 0.95, 6, 0.24, 0.16, G.rx(-12), ("ffd447", "ffe58a"), material="Neon")   # a halo
        for s in (-1, 1):                                                                    # feathered wings
            root = np.array((s * 0.8, 2.3, 1.2))
            for k, (a, L, w) in enumerate(((40.0, 2.4, 0.9), (8.0, 2.0, 0.8))):
                d = np.array((s * math.cos(math.radians(a)), math.sin(math.radians(a)), 0.35))
                stick(sp, root, root + d * L, w, "ffffff" if k == 0 else "f0ece4", n=(0, 0, 1),
                      t=0.16 + 0.02 * k, material="Plastic")

    def features(self, sp):
        dimples(sp, col="e0d4b8")
        eyes(sp)
        mouth_smile(sp, cheeks=False)
        arms(sp, self.limb, hand="ffffff")
        legs(sp, self.limb, self.shoe)
        sprout(sp)
        crown(sp, jewel="7ad1ff")


CLOUD = [CloudPuffKind(), RainySpudKind(), SunnyTaterKind(), RainbowFryKind(), ThunderTuberKind(), SeraphSpudKind()]
