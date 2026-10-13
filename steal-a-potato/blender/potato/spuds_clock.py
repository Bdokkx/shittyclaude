"""Clockwork Yard potatoes, worst to best: RustyBolt, GearTater, SteamFry, TickTockSpud, TeslaTuber,
ChronoKing. Same rig, features and rules as the Meadow Patch kinds (spuds.py).

ChronoKing's hourglass is held in its left hand: children of HandL, welded to it, like the Candy
Crops' lollipop; its glass is see-through (Transparency 0.4)."""
import numpy as np

import spsgeo as G

from .bricks import ori
from .spuds import (Kind, arms, crown, dimples, eyes, legs, mouth_smile, octo, sprout)
from .spuds_candy import hand_at, held
from .spuds_lava import crack, glow_eyes

BRASS = ("c8a040", "a8842c", "dcb85c")


def gear(sp, centre, R, radius, t, cols, hub=None):
    """A cog: two squares turned 45 degrees to each other make its eight teeth, a hub in the middle.
    R turns it (its axle along R's local Z)."""
    c = np.asarray(centre, float)
    k = radius * 1.41
    sp.extra((k, k, t), c, R, cols[0])
    sp.extra((k * 0.98, k * 0.98, t * 1.12), c, R @ G.rz(45), cols[1])
    if hub:
        sp.extra((radius * 0.5, radius * 0.5, t * 1.3), c, R @ G.rz(22.5), hub)


class RustyBoltKind(Kind):
    """A rusty old bolt of a potato: a grey hex head on top, the thread's ridges round it and
    patches of orange rust."""
    pid, display, rarity, area = "RustyBolt", "Rusty Bolt", "Epic", "Clock"
    skin = ("8a6a5a", "745648", "a08070")
    limb = "745648"
    shoe = "4a3a32"
    face = dict(z=-1.45, eye_y=2.3, eye_dx=0.5, mouth_y=1.55, cheek_dx=0.84)
    shoulder = (1.55, 1.8)
    head = (0.0, 3.62, 0.0)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        W, D = 3.2, 2.9
        octo(sp, 0.35, 2.95, W, D, 2.0, 0.6, (mid, dark, light), core=True)
        sp.extra((2.6, 0.62, 2.25), (0.0, 3.2, 0.0), None, "8a929a")                           # a hex head
        sp.extra((2.5, 0.6, 2.2), (0.0, 3.17, 0.0), G.ry(60), "a2aab2")
        for y in (0.95, 0.62):                                                               # the thread's ridges
            crack(sp, [(-1.0, y + 0.1, -D / 2), (1.0, y - 0.1, -D / 2)], (0, 0, -1), w=0.12, col="5a4438",
                  material="Plastic")
        for pos, R, k in (((0.82, 2.85, -1.47), G.rz(20), 0.4), ((-1.62, 1.3, 0.3), G.ry(-90) @ G.rz(-30), 0.55)):
            sp.extra((k, k * 0.7, 0.1), pos, R, "d0702a")                                        # rust

    def features(self, sp):
        dimples(sp)
        eyes(sp)
        mouth_smile(sp)
        arms(sp, self.limb)
        legs(sp, self.limb, self.shoe)
        sprout(sp)
        crown(sp, jewel="d0702a")


class GearTaterKind(Kind):
    """A brass potato made of clockwork: a big cog set in its front, another turning behind its head."""
    pid, display, rarity, area = "GearTater", "Gear Tater", "Legendary", "Clock"
    skin = BRASS
    limb = "a8842c"
    shoe = "6a5020"
    face = dict(z=-1.45, eye_y=2.38, eye_dx=0.5, mouth_y=1.68, cheek_dx=0.84)
    shoulder = (1.55, 1.85)
    head = (0.0, 3.7, 0.0)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 2.95, 3.2, 2.9, 2.0, 0.6, (mid, dark, light), core=True)
        sp.extra((2.45, 0.7, 2.2), (0.0, 3.1, 0.05), ori(0, -8, 3), light)
        gear(sp, (-0.72, 0.82, -1.5), np.eye(3), 0.62, 0.12, ("8a6a2a", "b08a3a"), hub="5a4420")     # a cog in its front
        gear(sp, (0.0, 3.85, 1.0), G.rx(10), 1.5, 0.2, ("a8842c", "c8a040"), hub="6a5020")          # one behind its head

    def features(self, sp):
        dimples(sp, col="6a5020")
        eyes(sp)
        mouth_smile(sp)
        arms(sp, self.limb)
        legs(sp, self.limb, self.shoe)
        sprout(sp)
        crown(sp, jewel="3b8bff")


class SteamFryKind(Kind):
    """A tall copper steam engine: brass goggles pushed up on its forehead, a smokestack on its
    head puffing steam and a pipe along its side."""
    pid, display, rarity, area = "SteamFry", "Steam Fry", "Mythic", "Clock"
    skin = ("c87a4a", "a8603a", "dc945e")
    limb = "a8603a"
    shoe = "4a3020"
    face = dict(z=-1.3, eye_y=2.3, eye_dx=0.45, mouth_y=1.6, cheek_dx=0.8)
    shoulder = (1.45, 1.95)
    head = (-0.25, 3.72, 0.0)
    leg_h = 1.3

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 3.3, 2.9, 2.6, 1.9, 0.5, (mid, dark, light), core=True)
        brass = BRASS[0]
        for s in (-1, 1):                                                                    # brass goggles
            sp.extra((0.66, 0.66, 0.16), (s * 0.45, 3.0, -1.35), G.rz(45), brass)
            sp.extra((0.44, 0.44, 0.18), (s * 0.45, 3.0, -1.38), G.rz(45), "bfeaff", material="SmoothPlastic")
        sp.extra((2.95, 0.16, 0.1), (0.0, 3.0, -1.3), None, "4a3020")                           # their strap
        sp.extra((0.55, 1.2, 0.55), (0.75, 3.85, 0.35), None, "4a4a52")                         # a smokestack
        sp.extra((0.62, 0.62, 0.62), (0.95, 4.75, 0.45), ori(35, 45, 0), "f4f4f8")               # puffing steam
        sp.extra((0.46, 0.46, 0.46), (1.3, 5.35, 0.55), ori(20, 30, 10), "ffffff")
        sp.extra((0.32, 2.4, 0.32), (1.48, 1.7, 0.35), None, brass)                             # a pipe

    def features(self, sp):
        dimples(sp)
        eyes(sp, w=0.44, hgt=0.6)
        mouth_smile(sp, width=0.52)
        arms(sp, self.limb, hand="4a3020")
        legs(sp, self.limb, self.shoe)
        sprout(sp, at=(-0.25, 3.6, 0.0))
        crown(sp, jewel="ff8a1f")


class TickTockSpudKind(Kind):
    """An alarm clock: bright red, its face is the white clock dial with ticks at twelve and six, two
    gold bells on top and the hammer between them."""
    pid, display, rarity, area = "TickTockSpud", "Tick Tock Spud", "Mythic", "Clock"
    skin = ("d7372c", "b02a22", "f05a48")
    limb = "b02a22"
    shoe = "1e1a22"
    face = dict(z=-1.5, eye_y=2.12, eye_dx=0.46, mouth_y=1.45, cheek_dx=0.78)
    shoulder = (1.55, 1.75)
    head = (0.0, 3.4, 0.25)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 2.95, 3.2, 2.9, 2.0, 0.6, (mid, dark, light), core=True)
        sp.extra((2.3, 2.3, 0.05), (0.0, 1.72, -1.48), None, "fffaf0")                           # the clock dial
        sp.extra((2.25, 2.25, 0.07), (0.0, 1.72, -1.475), G.rz(45), "f4eee0")
        for y in (2.68, 0.76):
            sp.extra((0.1, 0.26, 0.1), (0.0, y, -1.53), None, "1e1a22")                          # ticks
        for s in (-1, 1):                                                                    # two gold bells
            sp.extra((1.0, 0.62, 1.0), (s * 1.2, 3.35, 0.0), G.rz(-s * 26), BRASS[0])
            sp.extra((0.8, 0.6, 0.8), (s * 1.17, 3.43, 0.0), G.rz(-s * 26) @ G.ry(45), BRASS[2])
        sp.extra((0.16, 1.1, 0.16), (0.0, 3.5, 0.55), None, "4a4a52")                            # the hammer

    def features(self, sp):
        dimples(sp)
        eyes(sp, w=0.44, hgt=0.6)
        mouth_smile(sp, width=0.5)
        arms(sp, self.limb)
        legs(sp, self.limb, self.shoe)
        sprout(sp, at=(0.0, 3.3, 0.35))
        crown(sp, jewel="ffd23f")


class TeslaTuberKind(Kind):
    """A Tesla coil: copper wound with darker coils, a silver sphere on its head and lightning
    crackling from it, its eyes glowing electric blue."""
    pid, display, rarity, area = "TeslaTuber", "Tesla Tuber", "Secret", "Clock"
    skin = ("c87a4a", "a8603a", "dc945e")
    limb = "6a747e"
    shoe = "3a4048"
    face = dict(z=-1.45, eye_y=2.32, eye_dx=0.5, mouth_y=1.55)
    shoulder = (1.55, 1.8)
    head = (0.0, 4.02, 0.0)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        D = 2.9
        octo(sp, 0.35, 2.95, 3.2, D, 2.0, 0.6, (mid, dark, light), core=True)
        for y in (2.85, 0.95, 0.6):                                                           # wound coils
            sp.extra((2.06, 0.14, 0.1), (0.0, y, -D / 2 - 0.02), None, "7a4024")
        sp.extra((2.0, 1.0, 2.0), (0.0, 3.45, 0.0), None, "c8d0d8")                              # a silver sphere
        sp.extra((1.7, 0.96, 1.7), (0.0, 3.46, 0.0), G.ry(45), "e0e6ec")
        for s in (-1, 1):                                                                    # lightning crackling
            crack(sp, [(s * 0.9, 3.6, 0.0), (s * 1.55, 4.1, -0.1), (s * 1.35, 4.5, -0.1), (s * 2.0, 5.0, -0.1)],
                  (0, 0, -1), w=0.16, col="8ff6ff")

    def features(self, sp):
        dimples(sp, col="7a4024")
        glow_eyes(sp, "8ff6ff", glint_col="1e2a3a")
        mouth_smile(sp, width=0.5, cheeks=False)
        arms(sp, self.limb, hand="c8d0d8")
        legs(sp, self.limb, self.shoe)
        sprout(sp, at=(0.0, 3.9, 0.0))
        crown(sp, jewel="8ff6ff")


class ChronoKingKind(Kind):
    """The king of time: gold, a royal purple cape, a cog turning beside its head and an hourglass
    of running sand in its left hand."""
    pid, display, rarity, area = "ChronoKing", "Chrono King", "Divine", "Clock"
    skin = ("f5c518", "d9a20c", "ffe066")
    limb = "d9a20c"
    shoe = "6a2fb0"
    face = dict(z=-1.45, eye_y=2.32, eye_dx=0.5, mouth_y=1.55, cheek_dx=0.84)
    shoulder = (1.55, 1.8)
    head = (0.0, 3.7, 0.0)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 2.95, 3.2, 2.9, 2.0, 0.6, (mid, dark, light), core=True)
        sp.extra((2.45, 0.7, 2.2), (0.0, 3.1, 0.05), ori(0, -8, 3), light)
        sp.extra((4.1, 2.7, 0.16), (0.0, 1.75, 1.62), None, "6a2fb0")                           # a royal cape
        sp.extra((3.5, 0.45, 0.6), (0.0, 3.05, 1.25), None, "fff5f8")                           # its ermine collar
        gear(sp, (1.95, 3.9, 0.3), G.ry(-20), 0.75, 0.16, ("c8a040", "ffe066"))                  # a cog turning

    def features(self, sp):
        dimples(sp, col="a87a0c")
        eyes(sp)
        mouth_smile(sp)
        arms(sp, self.limb, hand="ffffff")
        legs(sp, self.limb, self.shoe)
        sprout(sp)
        crown(sp, jewel="6a2fb0", size=1.2)
        hc, _R = hand_at(sp, "L")                                                             # an hourglass
        c = hc + (0.0, 1.0, -0.1)
        held(sp, "Hourglass", (0.9, 0.16, 0.9), c + (0.0, 0.95, 0.0), None, "d9a20c")
        held(sp, "Hourglass", (0.92, 0.18, 0.92), c + (0.0, -0.95, 0.0), None, "d9a20c")
        held(sp, "Hourglass", (0.66, 0.85, 0.66), c + (0.0, 0.45, 0.0), G.ry(45), "e8f6ff", transparency=0.4)
        held(sp, "Hourglass", (0.62, 0.8, 0.62), c + (0.0, -0.46, 0.0), G.ry(45), "f0d090")


CLOCK = [RustyBoltKind(), GearTaterKind(), SteamFryKind(), TickTockSpudKind(), TeslaTuberKind(), ChronoKingKind()]
