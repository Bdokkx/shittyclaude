"""Candy Crops potatoes, worst to best: GumdropSpud, LollipopTater, CottonCandyMash, ChocolateChip,
JawbreakerSpud, SugarKing. Same rig, features and rules as the Meadow Patch kinds (spuds.py).

LollipopTater and SugarKing hold something in their left hand: those bricks are children of HandL,
welded to it, so they come and go with the hand (level 5) and move with it in every clip."""
import numpy as np

import spsgeo as G

from .bricks import ori, shade
from .spuds import (Kind, arms, crown, dimples, eyes, legs, mouth_smile, octo, sprout)
from .spuds_lava import crack


def hand_at(sp, side="L", length=1.45, spread=38.0, hand_size=(0.8, 0.74, 0.74)):
    """Where arms() puts a hand: its middle and turn (in the potato's frame)."""
    s = -1 if side == "L" else 1
    sx, sy = sp.kind.shoulder
    R = G.rz(s * spread)
    down = R @ np.array((0.0, -1.0, 0.0))
    wrist = np.array((s * sx, sy, 0.0)) + down * (length - 0.2)
    return wrist + down * (hand_size[1] / 2 - 0.05), R


def held(sp, name, size, pos, R=None, color="ffffff", side="L", material="Plastic", **kw):
    """A brick held in a hand: a child of the hand, welded to it."""
    hand = sp.feat["Hand" + side]
    p = sp.b.part(hand, name, size, pos, R, color, material=material, **kw)
    sp.welds.append((hand, p))
    return p


def candy_crown(sp, at=None, band=("ff9ac8", "ffffff"), drops=("ff5a8a", "7ad1ff", "ffd23f"), jewel="ff3b5c"):
    """A crown of candy: a pink band with a white rim, three gumdrops for points and a glowing
    peppermint at the front."""
    x, y, z = at or sp.kind.head
    c = np.array((x, y - 0.12, z))
    h = sp.holder("Crown", tuple(c))
    R = G.rz(-9.0) @ G.ry(4.0)
    sp.brick(h, "Band", (1.7, 0.5, 1.5), c + R @ (0, 0.25, 0), R, band[0])
    for (px, pz), col in zip(((-0.6, -0.5), (0.6, -0.5), (0.0, 0.48)), drops):
        sp.brick(h, "Point", (0.52, 0.52, 0.52), c + R @ (px, 0.72, pz), R @ ori(35, 45, 0), col)
    sp.plate(h, "Jewel", (0.4, 0.4, 0.1), c + R @ (0.0, 0.26, -0.79), R @ G.rz(45), color=jewel, material="Neon")
    return h


class GumdropSpudKind(Kind):
    """A green gumdrop: a squat dome, wide at the bottom, coated in sugar."""
    pid, display, rarity, area = "GumdropSpud", "Gumdrop Spud", "Epic", "Candy"
    skin = ("3fcf5a", "2fae48", "6be27f")
    limb = "2fae48"
    shoe = "e8407a"
    face = dict(z=-1.65, eye_y=1.55, eye_dx=0.52, mouth_y=0.85, cheek_dx=0.9)
    shoulder = (1.7, 1.25)
    head = (0.0, 3.04, 0.0)
    leg_h = 1.1

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.25, 1.95, 3.6, 3.3, 2.2, 0.7, (mid, dark, light), core=True)              # wide at the bottom
        sp.extra((2.9, 0.62, 2.7), (0.0, 2.2, 0.0), None, light)                            # then a dome
        sp.extra((2.4, 0.6, 2.4), (0.0, 2.17, 0.0), G.ry(45), mid)
        sp.extra((1.8, 0.45, 1.65), (0.0, 2.7, 0.0), G.ry(20), light)
        for pos, R in (((-1.02, 0.62, -1.67), ori(0, 0, 30)), ((0.98, 1.72, -1.67), ori(0, 0, 45)),   # sugar
                       ((1.82, 0.9, -0.3), ori(0, 0, 20)), ((-1.82, 1.4, 0.4), ori(0, 0, 40)),
                       ((-0.72, 2.3, -1.37), ori(0, 0, 45)), ((0.3, 2.94, -0.3), ori(0, 30, 0))):
            sp.extra((0.2, 0.2, 0.2), pos, R, "ffffff")

    def features(self, sp):
        dimples(sp)
        eyes(sp)
        mouth_smile(sp)
        arms(sp, self.limb)
        legs(sp, self.limb, self.shoe)
        sprout(sp)
        crown(sp, jewel="ff5a8a")


class LollipopTaterKind(Kind):
    """A pink and white swirl of a potato, a swirl of candy on its head, holding up a big pinwheel
    lollipop."""
    pid, display, rarity, area = "LollipopTater", "Lollipop Tater", "Legendary", "Candy"
    skin = ("ff8cc6", "f06aae", "ffffff")
    limb = "f06aae"
    shoe = "ffffff"
    face = dict(z=-1.45, eye_y=2.3, eye_dx=0.5, mouth_y=1.55, cheek_dx=0.84)
    shoulder = (1.55, 1.8)
    head = (0.0, 4.12, 0.0)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 2.95, 3.2, 2.9, 2.0, 0.6, (mid, dark, light), core=True)               # white facets
        for (w, d, y, turn, col) in ((2.6, 2.4, 3.15, 15, "ffffff"), (2.0, 1.85, 3.55, 40, mid),
                                     (1.3, 1.2, 3.9, 65, "ffffff")):                            # a swirl on top
            sp.extra((w, 0.42, d), (0.0, y, 0.0), G.ry(turn), col)

    def features(self, sp):
        dimples(sp)
        eyes(sp)
        mouth_smile(sp, cheek_col="ff5aa5")
        arms(sp, self.limb)
        legs(sp, self.limb, self.shoe)
        sprout(sp)
        crown(sp, jewel="ff5aa5")
        hc, _R = hand_at(sp, "L")                                                              # its lollipop
        held(sp, "Stick", (0.18, 2.6, 0.18), hc + (0.0, 1.1, 0.0), None, "ffffff")
        c = hc + (0.0, 3.15, -0.05)
        held(sp, "Candy", (1.5, 1.04, 0.28), c, None, "ff4f9e")
        held(sp, "Candy", (1.04, 1.5, 0.3), c, None, "ff5aa5")
        held(sp, "Candy", (1.24, 1.24, 0.26), c, G.rz(45), "ff6fb0")
        held(sp, "Candy", (0.84, 0.84, 0.34), c, G.rz(22), "ffffff")
        held(sp, "Candy", (0.42, 0.42, 0.38), c, G.rz(-12), "ff4f9e")


class CottonCandyMashKind(Kind):
    """A puff of cotton candy: fluffy pink and blue all over, a face peeping out of the fluff."""
    pid, display, rarity, area = "CottonCandyMash", "Cotton Candy Mash", "Legendary", "Candy"
    skin = ("ffb6d9", "ff9ccc", "ffd1e8")
    limb = "ff9ccc"
    shoe = "8cc8ff"
    face = dict(z=-1.25, eye_y=2.12, eye_dx=0.48, mouth_y=1.38, cheek_dx=0.82)
    shoulder = (1.4, 1.8)
    head = (0.05, 3.95, 0.15)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        blue, lblue = "a9d6ff", "8cc8ff"
        sp.core((2.8, 2.6, 2.5), (0.0, 1.65, 0.0), None, mid)
        for k, pos, R, col in ((1.6, (-0.5, 3.0, 0.25), ori(20, 30, 15), blue),               # fluff
                               (1.45, (0.62, 3.1, 0.05), ori(-15, 50, -10), mid),
                               (1.2, (0.0, 3.5, 0.55), ori(30, 15, 25), light),
                               (1.3, (-1.45, 2.3, 0.2), ori(10, 40, 30), dark),
                               (1.2, (1.45, 2.2, 0.3), ori(-20, 20, -25), blue),
                               (1.1, (-1.38, 1.0, 0.1), ori(25, 10, 10), lblue),
                               (1.1, (1.4, 1.1, -0.1), ori(-10, 35, 20), light),
                               (1.3, (0.0, 0.5, 0.3), ori(15, 45, 0), blue),
                               (0.9, (-1.08, 2.85, -0.88), ori(20, 30, 40), lblue),
                               (0.85, (1.02, 2.9, -0.84), ori(-20, 60, 10), mid)):
            sp.extra((k, k, k), pos, R, col)

    def features(self, sp):
        dimples(sp)
        eyes(sp)
        mouth_smile(sp, cheek_col="ff7fb6")
        arms(sp, self.limb, hand="ffffff")
        legs(sp, self.limb, self.shoe)
        sprout(sp)
        crown(sp, jewel="8cc8ff")


class ChocolateChipKind(Kind):
    """A potato dipped all over in milk chocolate: white chocolate drizzled across its top, dark
    chocolate chips stuck all over it and a wafer stick poking out of its head."""
    pid, display, rarity, area = "ChocolateChip", "Chocolate Chip", "Mythic", "Candy"
    skin = ("8b5a3c", "74482c", "9c6a48")
    limb = "74482c"
    shoe = "e8b86a"
    face = dict(z=-1.45, eye_y=2.2, eye_dx=0.5, mouth_y=1.45, cheek_dx=0.84)
    shoulder = (1.55, 1.8)
    head = (-0.2, 3.57, -0.1)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 2.95, 3.2, 2.9, 2.0, 0.6, (mid, dark, light), core=True)                # dipped all over
        sp.extra((2.45, 0.7, 2.2), (0.0, 3.1, 0.0), None, light)
        z = -1.1                                                                              # white chocolate drizzle
        crack(sp, [(-1.12, 2.92, z), (-0.6, 3.36, z), (-0.05, 2.9, z), (0.5, 3.36, z), (1.05, 2.92, z)], (0, 0, -1),
              w=0.14, col="fff4e6", out=0.02, material="Plastic")
        for pos, R in (((0.72, 0.62, -1.47), G.rz(20)), ((-0.85, 0.82, -1.47), G.rz(-30)),
                       ((1.62, 1.6, 0.3), G.ry(90) @ G.rz(35))):
            sp.extra((0.3, 0.3, 0.1), pos, R, "3a1c10")                                       # chocolate chips
        sp.extra((0.42, 2.3, 0.42), (0.75, 3.95, 0.4), G.rz(-20) @ G.ry(45), "e8b86a")        # a wafer stick

    def features(self, sp):
        dimples(sp, col="4a2a18")
        eyes(sp)
        mouth_smile(sp, cheek_col="d97a8a")
        arms(sp, self.limb, hand="fff4e6")
        legs(sp, self.limb, self.shoe)
        sprout(sp, at=(-0.2, 3.45, -0.1))
        crown(sp, jewel="ff3b5c")


class JawbreakerSpudKind(Kind):
    """A round jawbreaker: rainbow layers of candy one on another, a shine on top."""
    pid, display, rarity, area = "JawbreakerSpud", "Jawbreaker Spud", "Secret", "Candy"
    skin = ("ffd23f", "ff8c42", "ffffff")
    limb = "ff8c42"
    shoe = "9b5de5"
    face = dict(z=-1.8, eye_y=1.95, eye_dx=0.52, mouth_y=1.27, cheek_dx=0.92, cheek_y=1.62)
    shoulder = (1.75, 1.65)
    head = (0.0, 3.9, 0.0)
    leg_h = 1.2

    def body(self, sp):
        layers = ((0.3, 0.95, 2.9, "ff4d6d"), (0.95, 1.6, 3.6, "ff8c42"), (1.6, 2.25, 3.6, "ffd23f"),
                  (2.25, 2.9, 3.3, "3ec46d"), (2.9, 3.55, 2.7, "4d96ff"))
        for i in (2, 0, 1, 3, 4):                                                             # rainbow layers
            y0, y1, w, col = layers[i]
            h, y = y1 - y0, (y0 + y1) / 2
            ka = 0.97 if i % 2 == 0 else 1.03                                                 # so no faces meet flush
            (sp.core if i == 2 else sp.extra)((w * 0.62, h, w), (0.0, y, 0.0), None, col)
            sp.extra((w, h * ka, w * 0.62), (0.0, y, 0.0), None, shade(col, 0.18))
        sp.extra((1.9, 0.36, 1.9), (0.0, 3.72, 0.0), G.ry(45), "9b5de5")
        sp.extra((0.55, 0.18, 0.1), (0.62, 2.65, -1.64), G.rz(20), "ffffff", material="SmoothPlastic")  # a shine

    def features(self, sp):
        dimples(sp)
        eyes(sp)
        mouth_smile(sp)
        arms(sp, self.limb)
        legs(sp, self.limb, self.shoe)
        sprout(sp)
        crown(sp, jewel="ff4d6d")


class SugarKingKind(Kind):
    """The king of the candy: pastel pink, a peppermint cape striped red and white with a fluffy
    collar, a candy cane for a sceptre in his left hand and, at the top level, a crown of candy."""
    pid, display, rarity, area = "SugarKing", "Sugar King", "Divine", "Candy"
    skin = ("ffc2dc", "f7a8c9", "ffd6e7")
    limb = "f7a8c9"
    shoe = "e23a4e"
    face = dict(z=-1.45, eye_y=2.32, eye_dx=0.5, mouth_y=1.55, cheek_dx=0.84)
    shoulder = (1.55, 1.8)
    head = (0.0, 3.1, 0.0)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 2.95, 3.2, 2.9, 2.0, 0.6, (mid, dark, light), core=True)
        sp.extra((4.3, 2.7, 0.16), (0.0, 1.75, 1.6), None, "ffffff")                         # a peppermint cape
        for x in (-1.72, 1.72):
            sp.extra((0.6, 2.72, 0.22), (x, 1.75, 1.6), None, "e23a4e")
        sp.extra((3.5, 0.45, 0.6), (0.0, 3.05, 1.25), None, "fff5f8")                        # its fluffy collar

    def features(self, sp):
        dimples(sp)
        eyes(sp)
        mouth_smile(sp, cheek_col="ff8fb1")
        arms(sp, self.limb, hand="ffffff")
        legs(sp, self.limb, self.shoe)
        sprout(sp)
        candy_crown(sp)
        hc, _R = hand_at(sp, "L")                                                             # a candy cane sceptre
        held(sp, "Cane", (0.26, 3.1, 0.26), hc + (0.0, 1.25, 0.0), None, "ffffff")
        for dy in (0.75, 1.75):
            held(sp, "Cane", (0.32, 0.24, 0.32), hc + (0.0, dy, 0.0), G.rz(25), "e23a4e")
        top = hc + (0.0, 2.8, 0.0)
        held(sp, "Cane", (0.26, 0.7, 0.23), top + (0.2, 0.2, 0.0), G.rz(-55), "e23a4e")
        held(sp, "Cane", (0.26, 0.5, 0.29), top + (0.55, 0.08, 0.0), None, "ffffff")


CANDY = [GumdropSpudKind(), LollipopTaterKind(), CottonCandyMashKind(), ChocolateChipKind(), JawbreakerSpudKind(),
         SugarKingKind()]
