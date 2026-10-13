"""Haunted Hollow potatoes, worst to best: PumpkinSpud, GhostTater, BatSpud, WitchFry, FrankenSpud,
ReaperTuber. Same rig, features and rules as the Meadow Patch kinds (spuds.py).

GhostTater's sheet is a little see-through (Transparency 0.2). ReaperTuber's scythe is held in its
left hand: children of HandL, welded to it, like the Candy Crops' lollipop."""
import numpy as np

import spsgeo as G

from .bricks import ori
from .spuds import (INK, Kind, arms, crown, dimples, eyes, legs, mouth_smile, octo, sprout)
from .spuds_candy import hand_at, held
from .spuds_lava import crack, glow_eyes, glow_mouth, stick

GLOW = ("ffd23f", "ff9a1f")


def lantern_eyes(sp, col=GLOW[0], k=0.56):
    """Two carved triangle eyes glowing from inside (a diamond with its lower half in shadow)."""
    f = sp.kind.face
    z, y, dx = f["z"], f["eye_y"], f["eye_dx"]
    h = sp.holder("Eyes", (0.0, y, z))
    for s in (1, -1):
        ex = s * dx
        sp.plate(h, "Eye", (k, k, 0.1), (ex, y + 0.12, z - 0.04), G.rz(45), color=col, material="Neon")
        sp.plate(h, "Glint", (k * 1.5, k * 0.72, 0.1), (ex, y - 0.14, z - 0.06), None, color="c86a10")
    return h


class PumpkinSpudKind(Kind):
    """A jack-o'-lantern: ribbed orange, a curly green stem and a leaf on top, carved eyes and a
    jagged grin glowing from inside."""
    pid, display, rarity, area = "PumpkinSpud", "Pumpkin Spud", "Rare", "Haunt"
    skin = ("ff8a1f", "e0701a", "ffa23f")
    limb = "3f7a2a"
    shoe = "2a4a1a"
    face = dict(z=-1.6, eye_y=2.1, eye_dx=0.55, mouth_y=1.2)
    shoulder = (1.75, 1.75)
    head = (0.0, 3.2, 0.0)
    leg_h = 1.15

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.3, 2.85, 3.5, 3.2, 1.9, 0.75, (mid, dark, dark), core=True)                  # ribbed
        sp.extra((2.6, 0.45, 2.4), (0.0, 2.95, 0.0), G.ry(45), light)
        sp.extra((0.4, 0.75, 0.4), (0.1, 3.4, 0.0), G.rz(-14), "5a7a2a")                        # a curly stem
        sp.extra((0.32, 0.5, 0.32), (0.32, 3.8, 0.0), G.rz(-62), "4a6a22")
        sp.extra((0.9, 0.08, 0.55), (-0.5, 3.2, 0.3), ori(0, 30, 14), "4caf50")                 # a leaf

    def features(self, sp):
        dimples(sp, col="c86a10")
        lantern_eyes(sp)
        f = self.face
        z, y = f["z"], f["mouth_y"]
        h = sp.holder("Mouth", (0.0, y, z))                                                  # a jagged grin
        sp.plate(h, "Mouth", (1.3, 0.42, 0.1), (0.0, y, z - 0.04), color=GLOW[1], material="Neon")
        for x in (-0.3, 0.3):
            sp.plate(h, "Tooth", (0.26, 0.24, 0.1), (x, y + 0.1, z - 0.09), G.rz(45), color="e0701a")
        arms(sp, self.limb)
        legs(sp, self.limb, self.shoe)
        sprout(sp, at=(-0.35, 3.1, -0.2))
        crown(sp, jewel=GLOW[1])


class GhostTaterKind(Kind):
    """A sheet ghost: white and a little see-through, a wavy hem, big dark eyes and an 'oo' mouth,
    a wisp trailing behind."""
    pid, display, rarity, area = "GhostTater", "Ghost Tater", "Rare", "Haunt"
    skin = ("f4f4ff", "e2e2f2", "ffffff")
    limb = "e8e8f6"
    shoe = "c8c8dc"
    face = dict(z=-1.45, eye_y=2.32, eye_dx=0.5, mouth_y=1.45)
    shoulder = (1.55, 1.8)
    head = (0.0, 3.7, 0.0)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        parts = octo(sp, 0.35, 2.95, 3.2, 2.9, 2.0, 0.6, (mid, dark, light), core=True)
        for p in parts:
            p.p["transparency"] = 0.2
        sp.extra((2.45, 0.7, 2.2), (0.0, 3.1, 0.05), ori(0, -8, 3), light, transparency=0.2)
        for x, z in ((-1.05, -1.32), (0.0, -1.42), (1.05, -1.32), (1.55, 0.1)):                 # a wavy hem
            sp.extra((0.72, 0.72, 0.3), (x, 0.32, z), G.rz(45), mid, transparency=0.2)
        stick(sp, (0.2, 1.6, 1.3), (0.9, 2.2, 2.5), 0.6, light, n=(0, 1, 0), t=0.3, material="Plastic")   # a wisp
        stick(sp, (0.85, 2.15, 2.4), (1.5, 2.9, 3.0), 0.36, light, n=(0, 1, 0), t=0.2, material="Plastic")

    def features(self, sp):
        dimples(sp, col="c8c8dc")
        eyes(sp, w=0.56, hgt=0.86)
        mouth_smile(sp, width=0.36, tongue=False, cheeks=False)
        arms(sp, self.limb, hand="ffffff")
        legs(sp, self.limb, self.shoe)
        sprout(sp)
        crown(sp, jewel="9fd0ff")


class BatSpudKind(Kind):
    """A bat: dusky purple, big scalloped wings spread behind it, pointed ears, glowing yellow eyes
    and two little fangs."""
    pid, display, rarity, area = "BatSpud", "Bat Spud", "Epic", "Haunt"
    skin = ("3a2a4a", "2a1e38", "4a3a5e")
    limb = "2a1e38"
    shoe = "1e1428"
    face = dict(z=-1.45, eye_y=2.32, eye_dx=0.5, mouth_y=1.5)
    shoulder = (1.55, 1.8)
    head = (0.0, 3.7, 0.0)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 2.95, 3.2, 2.9, 2.0, 0.6, (mid, dark, light), core=True)
        sp.extra((2.45, 0.7, 2.2), (0.0, 3.1, 0.05), ori(0, -8, 3), light)
        wing = "5a4870"
        for s in (-1, 1):                                                                    # wings spread behind
            root = np.array((s * 0.8, 2.3, 1.15))
            for k, (a, L) in enumerate(((24.0, 2.3), (2.0, 2.5), (-20.0, 2.1))):
                d = np.array((s * np.cos(np.radians(a)), np.sin(np.radians(a)), 0.22))
                stick(sp, root, root + d * L, 0.95, wing if k != 1 else dark, n=(0, 0, 1), t=0.12 + 0.015 * k,
                      material="Plastic")
            Re = G.rz(-s * 18)
            sp.extra((0.5, 0.85, 0.3), (s * 0.95, 3.55, -0.25), Re @ G.ry(45), dark)              # pointed ears

    def features(self, sp):
        dimples(sp, col="1e1428")
        glow_eyes(sp, GLOW[0], glint_col=INK)
        f = self.face
        z, y = f["z"], f["mouth_y"]
        h = sp.holder("Mouth", (0.0, y, z))                                                  # a smile and fangs
        sp.plate(h, "Mouth", (0.62, 0.22, 0.1), (0.0, y, z - 0.04), color="1e1428")
        for x in (-0.17, 0.17):
            sp.plate(h, "Fang", (0.16, 0.16, 0.1), (x, y - 0.12, z - 0.09), G.rz(45), color="ffffff")
        arms(sp, self.limb, hand="5a4870")
        legs(sp, self.limb, self.shoe)
        sprout(sp)
        crown(sp, jewel="ff3b5c")


class WitchFryKind(Kind):
    """A tall green witch: a black pointed hat with a crooked tip and a purple band, straggly purple
    hair, a long nose with a wart."""
    pid, display, rarity, area = "WitchFry", "Witch Fry", "Legendary", "Haunt"
    skin = ("8cc85a", "74ae46", "a4d872")
    limb = "4a2a6a"
    shoe = "1e1a22"
    face = dict(z=-1.3, eye_y=2.6, eye_dx=0.46, mouth_y=1.62, cheek_dx=0.8)
    shoulder = (1.45, 2.05)
    head = (0.0, 3.56, 0.0)
    leg_h = 1.3

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 3.3, 2.9, 2.6, 1.9, 0.5, (mid, dark, light), core=True)
        black, band = "1e1a22", "6a2fb0"
        sp.extra((3.4, 0.16, 3.1), (0.0, 3.38, 0.0), None, black)                              # a pointed hat
        sp.extra((1.45, 1.0, 1.35), (0.0, 3.95, 0.1), None, black)
        sp.extra((1.0, 1.05, 0.95), (0.08, 4.9, 0.12), G.rz(-6), "2a2430")
        sp.extra((0.55, 1.0, 0.5), (0.42, 5.72, 0.15), G.rz(-32), black)                       # crooked at the tip
        sp.extra((1.5, 0.22, 1.4), (0.0, 3.6, 0.1), None, band)
        for s in (-1, 1):
            sp.extra((0.3, 1.0, 1.6), (s * 1.42, 2.8, 0.2), G.rz(s * 6), "6a2fb0")             # straggly hair
        sp.extra((0.36, 0.36, 0.5), (0.0, 2.12, -1.48), G.rx(-8), dark)                        # a long nose
        sp.extra((0.13, 0.13, 0.13), (0.12, 2.18, -1.74), None, "5a8a3a")

    def features(self, sp):
        dimples(sp)
        eyes(sp, w=0.44, hgt=0.6)
        mouth_smile(sp, width=0.5, cheek_col="d97a8a")
        arms(sp, self.limb)
        legs(sp, self.limb, self.shoe)
        sprout(sp, at=(0.55, 3.5, 0.4))
        crown(sp, jewel="6a2fb0")


class FrankenSpudKind(Kind):
    """Frankenstein's monster: grey-green, a flat top of black hair with a ragged fringe for a heavy
    brow, bolts in its neck and a stitched scar down one cheek."""
    pid, display, rarity, area = "FrankenSpud", "Franken Spud", "Mythic", "Haunt"
    skin = ("8fbf7a", "76a862", "a4d090")
    limb = "3a3a4a"
    shoe = "1e1a22"
    face = dict(z=-1.45, eye_y=2.18, eye_dx=0.5, mouth_y=1.4)
    shoulder = (1.55, 1.75)
    head = (0.0, 3.6, 0.0)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 2.95, 3.2, 2.9, 2.0, 0.6, (mid, dark, light), core=True)
        hair, stitch = "1e1a22", "2a2a3a"
        sp.extra((3.0, 0.62, 2.7), (0.0, 3.2, 0.05), None, hair)                               # a flat top
        for x in (-0.6, 0.05, 0.7):
            sp.extra((0.44, 0.44, 0.3), (x, 2.88, -1.32), G.rz(45), hair)                       # a ragged fringe
        for s in (-1, 1):
            sp.extra((0.5, 0.26, 0.26), (s * 1.78, 1.0, 0.0), None, "a8acb4")                   # bolts
        sp.extra((0.08, 0.9, 0.1), (-0.85, 1.55, -1.48), G.rz(-14), stitch)                     # a stitched scar
        for y in (1.35, 1.75):
            sp.extra((0.3, 0.07, 0.1), (-0.85 + (y - 1.55) * 0.25, y, -1.5), G.rz(-14), stitch)

    def features(self, sp):
        dimples(sp)
        eyes(sp, w=0.5, hgt=0.58)
        mouth_smile(sp, width=0.66, tongue=False, cheeks=False)
        arms(sp, self.limb, hand="8fbf7a")
        legs(sp, self.limb, self.shoe)
        sprout(sp)
        crown(sp, jewel="6ff36a")


class ReaperTuberKind(Kind):
    """A grim reaper: a black hooded cloak, eyes glowing out of the shadow of its hood, a ghostly
    glow about it and a scythe in its left hand."""
    pid, display, rarity, area = "ReaperTuber", "Reaper Tuber", "Secret", "Haunt"
    skin = ("2a2830", "1e1c24", "38343f")
    limb = "1e1c24"
    shoe = "141218"
    face = dict(z=-1.45, eye_y=2.25, eye_dx=0.48, mouth_y=1.55)
    shoulder = (1.55, 1.8)
    head = (0.0, 3.92, 0.1)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 2.95, 3.2, 2.9, 2.0, 0.6, (mid, dark, light), core=True)
        hood = "16141a"
        sp.extra((3.4, 1.0, 3.1), (0.0, 3.25, 0.05), None, hood)                               # a hood
        sp.extra((1.6, 0.9, 1.6), (0.0, 3.85, 0.4), ori(-10, 45, 0), dark)
        for s in (-1, 1):
            sp.extra((0.4, 1.5, 0.3), (s * 1.08, 2.45, -1.5), None, hood)                       # framing its face
        for pos, k in (((1.85, 2.9, -0.5), 0.3), ((-1.95, 1.4, 0.2), 0.24)):
            sp.extra((k, k, k), pos, ori(35, 45, 0), "6ff3ff", material="Neon")                 # a ghostly glow

    def features(self, sp):
        dimples(sp, col="38343f")
        glow_eyes(sp, "6ff3ff", glint_col="16141a", w=0.46, hgt=0.4)
        glow_mouth(sp, "6ff3ff", width=0.4, hgt=0.12)
        arms(sp, self.limb, hand="d8d8e0")
        legs(sp, self.limb, self.shoe)
        sprout(sp, at=(0.0, 3.8, 0.1))
        crown(sp, jewel="6ff3ff")
        hc, _R = hand_at(sp, "L")                                                             # a scythe
        held(sp, "Scythe", (0.24, 4.3, 0.24), hc + (0.0, 1.45, 0.0), None, "8a6a4a")
        top = hc + (0.0, 3.5, 0.0)
        for k, (dx, dy, a, L, col) in enumerate(((-0.62, 0.1, 8.0, 1.3, "d8dce4"), (-1.62, -0.12, 30.0, 1.0, "e8ecf2"),
                                                  (-2.2, -0.62, 62.0, 0.75, "f4f6fa"))):
            held(sp, "Scythe", (L, 0.4 - 0.08 * k, 0.12 + 0.02 * k), top + (dx, dy, 0.0), G.rz(a), col)


HAUNT = [PumpkinSpudKind(), GhostTaterKind(), BatSpudKind(), WitchFryKind(), FrankenSpudKind(), ReaperTuberKind()]
