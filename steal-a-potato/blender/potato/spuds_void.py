"""Glitch Void potatoes, worst to best: StaticSpud, ErrorTater, ShadowFry, GlitchSpud, VoidWalker,
KingNull. Same rig, features and rules as the Meadow Patch kinds (spuds.py).

ShadowFry's body is a little see-through (Transparency 0.25)."""
import numpy as np

import spsgeo as G

from .bricks import ori
from .spuds import (INK, Kind, arms, crown, dimples, eyes, legs, mouth_smile, octo, sprout)
from .spuds_cosmic import ring
from .spuds_crystal import jagged_crown
from .spuds_lava import glow_eyes, glow_mouth, stick

VOID = ("b44dff", "6ff3ff", "ff3cc8", "3cff6a")


class StaticSpudKind(Kind):
    """TV static: speckled grey, black and white noise across it and an old set's rabbit-ear aerial
    on its head."""
    pid, display, rarity, area = "StaticSpud", "Static Spud", "Legendary", "Void"
    skin = ("8a8a90", "74747a", "a2a2a8")
    limb = "74747a"
    shoe = "3a3a40"
    face = dict(z=-1.45, eye_y=2.32, eye_dx=0.5, mouth_y=1.55, cheek_dx=0.84)
    shoulder = (1.55, 1.8)
    head = (0.0, 3.62, 0.0)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        W, D = 3.2, 2.9
        octo(sp, 0.35, 2.95, W, D, 2.0, 0.6, (mid, dark, light), core=True)
        sp.extra((2.45, 0.6, 2.2), (0.0, 3.08, 0.05), None, light)
        for pos, col in (((0.82, 2.85, -1.47), "ffffff"), ((-0.86, 2.7, -1.47), "1e1e22"),   # static noise
                         ((0.7, 0.6, -1.47), "1e1e22"), ((-0.62, 0.9, -1.47), "ffffff"),
                         ((-0.2, 0.55, -1.47), "c8c8cc")):
            sp.extra((0.3, 0.3, 0.1), pos, None, col)
        sp.extra((0.5, 0.3, 0.5), (0.0, 3.5, 0.3), None, "3a3a40")                               # a rabbit-ear aerial
        for s in (-1, 1):
            stick(sp, (s * 0.1, 3.55, 0.3), (s * 1.05, 5.05, 0.3), 0.15, "2a2a30", n=(0, 0, 1), t=0.15 + 0.02 * (s > 0),
                  material="Plastic")

    def features(self, sp):
        dimples(sp)
        eyes(sp)
        mouth_smile(sp)
        arms(sp, self.limb)
        legs(sp, self.limb, self.shoe)
        sprout(sp, at=(-0.45, 3.5, -0.2))
        crown(sp, at=(0.0, 3.62, -0.2), jewel="6ff3ff")


class ErrorTaterKind(Kind):
    """An error message: a pale window with a blue title bar on top, a red X to close it and a yellow
    warning sign on its front."""
    pid, display, rarity, area = "ErrorTater", "Error Tater", "Mythic", "Void"
    skin = ("e8eaf0", "d0d4dc", "f4f6fa")
    limb = "a8b0bc"
    shoe = "2f5ec8"
    face = dict(z=-1.45, eye_y=2.1, eye_dx=0.5, mouth_y=1.42, cheek_dx=0.84)
    shoulder = (1.55, 1.75)
    head = (-0.3, 3.65, 0.0)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 2.95, 3.2, 2.9, 2.0, 0.6, (mid, dark, light), core=True)
        sp.extra((3.3, 0.6, 3.0), (0.0, 3.1, 0.0), None, "2f5ec8")                                # a blue title bar
        sp.extra((0.5, 0.42, 0.1), (1.2, 3.12, -1.52), None, "e8302a")                            # a red X
        for a in (45.0, -45.0):
            sp.extra((0.4, 0.07, 0.1 + 0.02 * (a > 0)), (1.2, 3.12, -1.58), G.rz(a), "ffffff")
        for x in (0.6, 0.06):
            sp.extra((0.4, 0.34, 0.1), (x, 3.12, -1.52), None, "8aa8e8")                          # its other buttons
        sp.extra((0.62, 0.62, 0.1), (-0.66, 0.72, -1.47), G.rz(45), "ffd23f")                     # a warning sign
        sp.extra((0.1, 0.3, 0.1), (-0.66, 0.76, -1.52), None, "1e1a22")

    def features(self, sp):
        dimples(sp)
        eyes(sp)
        mouth_smile(sp)
        arms(sp, self.limb)
        legs(sp, self.limb, self.shoe)
        sprout(sp, at=(-0.3, 3.55, 0.0))
        crown(sp, jewel="e8302a")


class ShadowFryKind(Kind):
    """A shadow standing up on its own: tall, dark and a little see-through, wisps of shadow curling
    off it, nothing showing but its glowing white eyes and mouth."""
    pid, display, rarity, area = "ShadowFry", "Shadow Fry", "Secret", "Void"
    skin = ("1a1424", "120e1a", "241c30")
    limb = "120e1a"
    shoe = "0a080e"
    face = dict(z=-1.3, eye_y=2.55, eye_dx=0.45, mouth_y=1.8)
    shoulder = (1.45, 2.0)
    head = (0.0, 3.42, 0.0)
    leg_h = 1.3

    def body(self, sp):
        mid, dark, light = self.skin
        parts = octo(sp, 0.35, 3.3, 2.9, 2.6, 1.9, 0.5, (mid, dark, light), core=True)
        for p in parts:
            p.p["transparency"] = 0.25
        for a, b, k in (((0.6, 3.1, 0.3), (1.3, 4.3, 0.6), 0.44), ((-0.7, 3.0, 0.2), (-1.5, 4.0, 0.7), 0.36),
                        ((1.3, 1.0, 0.6), (2.2, 1.6, 1.2), 0.32), ((-1.3, 0.8, 0.5), (-2.1, 1.2, 1.1), 0.3),
                        ((0.0, 2.0, 1.2), (0.3, 2.8, 2.3), 0.4)):                              # wisps of shadow
            stick(sp, a, b, k, light, n=(0, 0, 1), t=k * 0.7, material="Plastic")

    def features(self, sp):
        dimples(sp, col="3a3048")
        glow_eyes(sp, "ffffff", glint_col="241c30", w=0.46, hgt=0.5)
        glow_mouth(sp, "ffffff", width=0.42, hgt=0.12)
        arms(sp, self.limb, hand="241c30")
        legs(sp, self.limb, self.shoe)
        sprout(sp)
        crown(sp, jewel="ffffff")


class GlitchSpudKind(Kind):
    """A glitch: slices of it slipped sideways, red and cyan fringes down its edges like a bad
    signal and stray pixels floating off it."""
    pid, display, rarity, area = "GlitchSpud", "Glitch Spud", "Secret", "Void"
    skin = ("7a5ae0", "6046c0", "9474f0")
    limb = "6046c0"
    shoe = "2a1e5a"
    face = dict(z=-1.45, eye_y=2.1, eye_dx=0.5, mouth_y=1.45, cheek_dx=0.84)
    shoulder = (1.55, 1.8)
    head = (0.0, 3.07, 0.0)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        W, D = 3.2, 2.9
        octo(sp, 0.35, 2.95, W, D, 2.0, 0.6, (mid, dark, light), core=True)
        sp.extra((2.2, 0.36, 2.94), (0.42, 2.78, 0.0), None, light)                               # slices slipped
        sp.extra((2.3, 0.3, 2.96), (-0.38, 0.72, 0.0), None, dark)
        for x, col in ((-1.08, VOID[1]), (1.08, "ff2a3a")):                                       # red and cyan fringes
            sp.extra((0.14, 1.4, 0.1), (x, 1.75, -1.47), None, col, material="Neon")
        for x, col in ((-1.62, VOID[1]), (1.62, "ff2a3a")):
            sp.extra((0.1, 1.0, 0.14), (x, 2.3, -0.6), None, col, material="Neon")
        for pos, col in (((-2.0, 3.0, -0.2), VOID[3]), ((2.05, 1.2, 0.0), VOID[2]), ((1.3, 3.95, 0.4), VOID[1])):
            sp.extra((0.32, 0.32, 0.32), pos, None, col, material="Neon")                         # stray pixels

    def features(self, sp):
        dimples(sp)
        eyes(sp)
        mouth_smile(sp)
        arms(sp, self.limb)
        legs(sp, self.limb, self.shoe)
        sprout(sp)
        crown(sp, jewel=VOID[3])


class VoidWalkerKind(Kind):
    """A walker between worlds: void black with stars inside it, glowing purple edges, a portal ring
    glowing behind it and glowing eyes."""
    pid, display, rarity, area = "VoidWalker", "Void Walker", "Divine", "Void"
    skin = ("0e0a16", "08060e", "16101e")
    limb = "08060e"
    shoe = "16101e"
    face = dict(z=-1.45, eye_y=2.32, eye_dx=0.5, mouth_y=1.55)
    shoulder = (1.55, 1.8)
    head = (0.0, 3.07, 0.0)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        D = 2.9
        octo(sp, 0.35, 2.95, 3.2, D, 2.0, 0.6, (mid, dark, light), core=True)
        for pos, k in (((0.82, 2.85, -1.47), 0.14), ((-0.75, 0.62, -1.47), 0.12), ((0.55, 0.9, -1.47), 0.1),
                       ((-0.88, 2.0, -1.47), 0.1)):
            sp.extra((k, k, 0.1), pos, G.rz(45), "ffffff", material="Neon")                       # stars inside
        for s in (-1, 1):
            sp.extra((0.12, 2.5, 0.1), (s * 1.06, 1.65, -D / 2 - 0.01), None, VOID[0], material="Neon")   # edges
        ring(sp, (0.0, 2.4, 1.0), 2.2, 6, 0.34, 0.24, G.rx(90), (VOID[0], "d27bff"), material="Neon")    # a portal

    def features(self, sp):
        dimples(sp, col="3a2a4a")
        glow_eyes(sp, "d27bff", glint_col=INK)
        glow_mouth(sp, "d27bff", width=0.5, hgt=0.14)
        arms(sp, self.limb, hand="2a1e3a")
        legs(sp, self.limb, self.shoe)
        sprout(sp)
        crown(sp, jewel=VOID[0])


class KingNullKind(Kind):
    """The king of nothing: void black, a glowing white zero on its chest, a cape lined with glowing
    purple, black cubes orbiting it, glowing white eyes and, at the top level, a jagged black crown."""
    pid, display, rarity, area = "KingNull", "King Null", "Divine", "Void"
    skin = ("16121e", "0e0a14", "221c2c")
    limb = "0e0a14"
    shoe = "221c2c"
    face = dict(z=-1.45, eye_y=2.4, eye_dx=0.5, mouth_y=1.82)
    shoulder = (1.55, 1.85)
    head = (0.0, 3.07, 0.0)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 2.95, 3.2, 2.9, 2.0, 0.6, (mid, dark, light), core=True)
        z = -1.47                                                                             # a glowing zero
        for (x, y, w, h) in ((0.0, 1.22, 0.62, 0.12), (0.0, 0.52, 0.62, 0.12), (-0.31, 0.87, 0.12, 0.86),
                             (0.31, 0.87, 0.12, 0.86)):
            sp.extra((w, h, 0.1 + 0.01 * (w < 0.2)), (x, y, z), None, "ffffff", material="Neon")
        sp.extra((4.0, 2.6, 0.1), (0.0, 1.78, 1.53), None, VOID[0], material="Neon")               # a cape, its lining
        sp.extra((4.2, 2.7, 0.16), (0.0, 1.75, 1.64), None, "0e0a14")                              # glowing
        for pos in ((2.1, 3.2, -0.3), (-2.2, 2.4, 0.4), (1.6, 0.9, 1.0)):
            sp.extra((0.42, 0.42, 0.42), pos, ori(35, 45, 0), "0e0a14")                             # black cubes

    def features(self, sp):
        dimples(sp, col="3a3048")
        glow_eyes(sp, "ffffff", glint_col=INK, w=0.46, hgt=0.5)
        glow_mouth(sp, "ffffff", width=0.46, hgt=0.12)
        arms(sp, self.limb, hand="221c2c")
        legs(sp, self.limb, self.shoe)
        sprout(sp)
        jagged_crown(sp, cols=("0e0a14", "221c2c"), jewel="ffffff")


VOID_KINDS = [StaticSpudKind(), ErrorTaterKind(), ShadowFryKind(), GlitchSpudKind(), VoidWalkerKind(), KingNullKind()]
