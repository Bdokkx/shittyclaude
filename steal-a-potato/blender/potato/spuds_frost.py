"""Frost Fields potatoes, worst to best: SnowballSpud, FrostbiteFry, PenguinPotato, YetiYam,
GlacierSpud, AuroraTuber. Same rig, features and rules as the Meadow Patch kinds (spuds.py)."""
import numpy as np

import spsgeo as G

from .bricks import ori, shade
from .spuds import (CHEEK, GLINT, INK, Kind, arms, crown, dimples, eyes, legs, mouth_smile, octo, sprout,
                    star)

SNOW = ("f2f6fa", "dde6ee", "ffffff")
ICE = ("a8e4ff", "86d0f8", "d4f3ff")


def flippers(sp, col, tip, length=1.5, spread=34.0):
    """Arms like arms() but flat, a penguin's flippers; a small tip for a hand."""
    sx, sy = sp.kind.shoulder
    for s, side in ((-1, "L"), (1, "R")):
        hinge = np.array((s * sx, sy, 0.0))
        R = G.rz(s * spread)
        down = R @ np.array((0.0, -1.0, 0.0))
        c = hinge + down * (length / 2 - 0.15)
        arm = sp.single("Arm" + side, (0.3, length, 0.85), c, R, col, hinge, sp.body)
        wrist = hinge + down * (length - 0.2)
        sp.single("Hand" + side, (0.32, 0.45, 0.7), wrist + down * 0.18, R, tip, wrist, arm)


class SnowballSpudKind(Kind):
    """A round white snowball with a carrot nose and a twig on its head; twig arms, red mittens."""
    pid, display, rarity, area = "SnowballSpud", "Snowball Spud", "Uncommon", "Frost"
    skin = SNOW
    limb = "6b4a2a"
    shoe = "3e6fd6"
    face = dict(z=-1.55, eye_y=2.38, eye_dx=0.5, mouth_y=1.42, cheek_dx=0.68)
    shoulder = (1.55, 1.85)
    head = (0.0, 3.65, 0.0)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 2.95, 3.3, 3.1, 1.8, 0.75, (mid, dark, light), core=True)
        sp.extra((2.4, 0.66, 1.7), (0.0, 3.15, 0.0), None, light)                      # a round top
        sp.extra((1.7, 0.68, 2.4), (0.0, 3.15, 0.0), None, mid)
        sp.extra((2.3, 0.5, 2.2), (0.0, 0.25, 0.0), ori(0, 22, 0), dark)
        sp.extra((0.36, 0.36, 0.5), (0.0, 1.92, -1.75), G.rz(45), "ff8a1f")            # the carrot nose
        sp.extra((0.22, 0.22, 0.42), (0.0, 1.92, -2.18), G.rz(45), "f07412")
        sp.extra((0.15, 0.95, 0.15), (0.75, 3.75, 0.25), G.rz(-22), "6b4a2a")          # the twig on its head
        sp.extra((0.12, 0.45, 0.12), (0.98, 3.98, 0.25), G.rz(-62), "7a5a38")
        for y in (0.9, 0.55):
            sp.extra((0.26, 0.26, 0.1), (0.0, y, -1.58), G.rz(45), "2b2b33")             # coal buttons

    def features(self, sp):
        dimples(sp)
        eyes(sp, hgt=0.66)
        mouth_smile(sp, width=0.56)
        arms(sp, self.limb, thick=0.28, hand="d7372c", hand_size=(0.66, 0.62, 0.62))
        legs(sp, "dde6ee", self.shoe)
        sprout(sp)
        crown(sp)


class FrostbiteFryKind(Kind):
    """A tall icy-blue fry with icicles hanging over its eyes, in a red woolly hat with a pompom."""
    pid, display, rarity, area = "FrostbiteFry", "Frostbite Fry", "Rare", "Frost"
    skin = ICE
    limb = "86d0f8"
    shoe = "d7372c"
    face = dict(z=-1.15, eye_y=2.72, eye_dx=0.44, mouth_y=1.98, cheek_dx=0.74)
    shoulder = (1.35, 2.1)
    head = (-0.3, 4.95, 0.0)
    leg_h = 1.3

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.3, 3.9, 2.6, 2.3, 2.1, 0.25, (mid, dark, light), core=True)
        sp.extra((2.1, 0.3, 1.8), (0.0, 0.15, 0.0), None, dark)
        red, dred = "d7372c", "a82820"
        sp.extra((2.8, 0.55, 2.5), (0.0, 3.92, 0.0), None, dred)                        # the hat's turned-up cuff
        sp.extra((2.3, 0.95, 2.1), (-0.08, 4.62, 0.0), G.rz(6), red)                    # its body
        sp.extra((0.7, 0.7, 0.7), (0.62, 5.0, 0.35), ori(30, 45, 0), "fafafa")          # the pompom
        for x, h in ((-0.75, 0.55), (0.05, 0.42), (0.78, 0.6)):
            sp.extra((0.18, h, 0.18), (x, 3.62 - h / 2, -1.2), G.ry(45), "e8faff")          # icicles
        for pos in ((-0.95, 1.2, -1.17), (0.85, 0.75, -1.17)):
            sp.extra((0.3, 0.3, 0.1), pos, G.rz(45), "ffffff")                              # frost specks

    def features(self, sp):
        dimples(sp)
        eyes(sp, w=0.46, hgt=0.62)
        mouth_smile(sp, width=0.5, cheek_col="ff9fb0")
        arms(sp, self.limb, hand="fafafa")
        legs(sp, self.limb, self.shoe)
        sprout(sp)
        crown(sp)


class PenguinPotatoKind(Kind):
    """A black potato with a white front: a penguin, with an orange beak, flippers and a red bow tie."""
    pid, display, rarity, area = "PenguinPotato", "Penguin Potato", "Epic", "Frost"
    skin = ("2b2b33", "1e1e26", "3a3a44")
    limb = "2b2b33"
    shoe = "ff8a1f"
    face = dict(z=-1.55, eye_y=2.35, eye_dx=0.48, mouth_y=1.6)
    shoulder = (1.6, 1.9)
    head = (0.0, 3.55, 0.0)
    leg_h = 1.15

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 2.95, 3.2, 2.9, 2.0, 0.6, (mid, dark, light), core=True)
        sp.extra((2.4, 0.66, 1.66), (0.0, 3.05, 0.0), None, light)
        sp.extra((1.7, 0.68, 2.36), (0.0, 3.05, 0.0), None, mid)
        sp.extra((1.9, 2.3, 0.1), (0.0, 1.62, -1.5), None, "f6f6f6")                     # its white front
        sp.extra((0.26, 0.26, 0.12), (0.0, 0.95, -1.58), G.rz(45), "b02a22")            # a bow tie
        for s in (-1, 1):
            sp.extra((0.42, 0.34, 0.1), (s * 0.28, 0.95, -1.56), G.rz(s * 12), "d7372c")

    def features(self, sp):
        dimples(sp)
        eyes(sp)
        f = self.face
        z, y = f["z"], f["mouth_y"]
        h = sp.holder("Mouth", (0.0, y, z))                                              # the beak
        sp.brick(h, "Beak", (0.62, 0.26, 0.5), (0.0, y + 0.08, z - 0.25), None, "ff8a1f")
        sp.brick(h, "Beak", (0.48, 0.18, 0.4), (0.0, y - 0.12, z - 0.19), None, "f07412")
        for s in (-1, 1):
            sp.plate(h, "Cheek", (0.4, 0.22, 0.1), (s * 0.78, y + 0.3, z - 0.025), color=CHEEK)
        flippers(sp, self.limb, "1e1e26")
        legs(sp, self.limb, self.shoe, shoe_size=(1.1, 0.42, 1.5))
        sprout(sp)
        crown(sp)


class YetiYamKind(Kind):
    """A shaggy white yeti of a yam: tufts of fur all over, a pale blue face and two little blue horns."""
    pid, display, rarity, area = "YetiYam", "Yeti Yam", "Legendary", "Frost"
    skin = ("f4f6f8", "dfe6ec", "ffffff")
    limb = "dfe6ec"
    shoe = "b8c8d8"
    face = dict(z=-1.63, eye_y=2.32, eye_dx=0.5, mouth_y=1.52, cheek_dx=0.78)
    shoulder = (1.65, 1.9)
    head = (0.0, 3.68, 0.05)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 3.0, 3.4, 3.1, 2.0, 0.7, (mid, dark, light), core=True)
        sp.extra((2.6, 0.7, 1.9), (0.0, 3.15, 0.0), ori(0, 0, 3), light)
        sp.extra((1.9, 0.72, 2.6), (0.0, 3.15, 0.0), ori(0, 0, 3), mid)
        sp.extra((1.9, 1.75, 0.1), (0.0, 2.0, -1.58), None, "bfe0ff")                    # its pale blue face
        for pos, R in (((1.72, 2.5, -0.4), ori(0, 20, -35)), ((-1.75, 1.6, 0.2), ori(10, -15, 40)),
                       ((0.9, 3.45, 0.85), ori(25, 30, -20)), ((-1.15, 0.75, -1.12), ori(0, 38, 50))):
            sp.extra((0.7, 0.5, 0.5), pos, R, SNOW[0])                                        # fur tufts
        for s in (-1, 1):
            sp.extra((0.3, 0.62, 0.3), (s * 0.95, 3.6, 0.15), G.rz(-s * 18), "6fb8ff")         # little horns

    def features(self, sp):
        dimples(sp)
        eyes(sp)
        mouth_smile(sp, width=0.62, cheek_col="ff9fb0")
        arms(sp, self.limb, thick=0.62, hand="b8c8d8")
        legs(sp, self.limb, self.shoe, shoe_size=(1.15, 0.55, 1.5))
        sprout(sp)
        crown(sp, jewel="6fb8ff")


class GlacierSpudKind(Kind):
    """A light blue ice crystal of a potato: sharp facets, crystal shards on top, glints of light."""
    pid, display, rarity, area = "GlacierSpud", "Glacier Spud", "Mythic", "Frost"
    skin = ICE
    limb = "86d0f8"
    shoe = "d4f3ff"
    face = dict(z=-1.45, eye_y=2.3, eye_dx=0.46, mouth_y=1.5, cheek_dx=0.7)
    shoulder = (1.55, 1.8)
    head = (0.0, 3.62, 0.0)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 2.9, 3.2, 2.9, 1.8, 0.75, (mid, dark, light), core=True)
        sp.extra((1.7, 1.7, 1.7), (0.0, 2.85, 0.15), ori(35, 45, 0), light)                  # its faceted crown
        for pos, R, sz in (((1.05, 3.05, 0.5), ori(10, 30, -32), (0.62, 1.5, 0.62)),          # crystal shards
                           ((-1.1, 2.95, 0.3), ori(-8, -20, 30), (0.56, 1.3, 0.56)),
                           ((0.15, 3.0, 1.15), ori(30, 45, 6), (0.5, 1.2, 0.5))):
            sp.extra(sz, pos, R @ G.ry(45), mid)
        for s in (-1, 1):                                                                # light along its facets
            sp.extra((0.1, 1.7, 0.1), (s * 1.27, 1.65, -1.16), G.ry(s * 45), "ecfbff", material="Neon")
        star(sp, sp.extra, (1.75, 2.9, -0.65), 0.7, "f2fdff", ori(0, -30, 45))

    def features(self, sp):
        dimples(sp)
        eyes(sp, w=0.48, hgt=0.7)
        mouth_smile(sp, width=0.54, cheek_col="9fdcff")
        arms(sp, self.limb, hand="d4f3ff")
        legs(sp, self.limb, self.shoe)
        sprout(sp)
        crown(sp, cols=("d4f3ff", "ffffff", "a8e4ff"), jewel="6ff3ff")


class AuroraTuberKind(Kind):
    """Dark teal like the polar night, glowing green and purple aurora ribbons swirling round it."""
    pid, display, rarity, area = "AuroraTuber", "Aurora Tuber", "Secret", "Frost"
    skin = ("1e4a50", "143a40", "2a5e66")
    limb = "143a40"
    shoe = "0e2a30"
    face = dict(z=-1.45, eye_y=2.32, eye_dx=0.5, mouth_y=1.55, cheek_dx=0.82)
    shoulder = (1.55, 1.8)
    head = (0.0, 3.62, 0.0)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 2.95, 3.2, 2.9, 2.0, 0.6, (mid, dark, light), core=True)
        sp.extra((2.45, 0.7, 2.2), (0.0, 3.1, 0.0), ori(0, -8, 3), light)
        green, purple = "5fff9a", "c06aff"
        for pos, R, ln, col in (((-1.36, 1.55, -1.12), ori(0, 45, 32), 2.3, green),           # the ribbons
                                ((1.36, 2.15, -1.12), ori(0, -45, -28), 2.1, purple),
                                ((1.66, 1.0, 0.3), ori(0, 90, 40), 1.9, green),
                                ((-1.66, 2.4, 0.4), ori(0, -90, -35), 1.8, purple),
                                ((0.3, 3.45, 0.2), ori(80, 30, 0), 2.0, green),
                                ((0.0, 1.85, 1.47), ori(0, 180, 30), 2.4, purple)):
            sp.extra((0.22, ln, 0.12), pos, R, col, material="Neon")
        star(sp, sp.extra, (-1.65, 3.4, -0.6), 0.5, "ffffff", ori(0, 30, 45))

    def crown(self, sp):
        crown(sp, jewel="c06aff")


FROST = [SnowballSpudKind(), FrostbiteFryKind(), PenguinPotatoKind(), YetiYamKind(), GlacierSpudKind(),
         AuroraTuberKind()]
