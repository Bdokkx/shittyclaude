"""Neon City potatoes, worst to best: PixelSpud, GlowTater, DJSpud, HoverFry, LaserTuber, CyberOverlord.
Same rig, features and rules as the Meadow Patch kinds (spuds.py).

HoverFry's visor is see-through (Transparency 0.35)."""
import numpy as np

import spsgeo as G

from .bricks import ori
from .spuds import (INK, Kind, arms, crown, dimples, eyes, legs, mouth_smile, octo, sprout)
from .spuds_lava import crack, glow_eyes, glow_mouth, stick

PINK, CYAN, LIME = "ff3cc8", "3ce8ff", "7dff4a"


def cyber_eyes(sp, w=0.5, hgt=0.6, cyber="ff2a3a"):
    """One white eye with a dark pupil and, on the other side, a glowing red cyber eye."""
    f = sp.kind.face
    z, y, dx = f["z"], f["eye_y"], f["eye_dx"]
    h = sp.holder("Eyes", (0.0, y, z))
    sp.plate(h, "Eye", (w, hgt, 0.1), (dx, y, z - 0.04), color="ffffff")
    sp.plate(h, "Pupil", (0.24, 0.3, 0.1), (dx - 0.06, y - 0.05, z - 0.09))
    sp.plate(h, "Eye", (w * 0.86, w * 0.86, 0.1), (-dx, y, z - 0.06), G.rz(45), color=cyber, material="Neon")
    sp.plate(h, "Glint", (0.16, 0.16, 0.1), (-dx, y, z - 0.11), color="ffe0e0", material="Neon")
    return h


class PixelSpudKind(Kind):
    """An 8-bit potato: square-cut magenta like an old game's sprite, highlight pixels in cyan and
    yellow, and loose pixels floating round it."""
    pid, display, rarity, area = "PixelSpud", "Pixel Spud", "Epic", "Neon"
    skin = ("e040d0", "b82cac", "f070e0")
    limb = "b82cac"
    shoe = "3c3cff"
    face = dict(z=-1.3, eye_y=2.05, eye_dx=0.52, mouth_y=1.3, cheek_dx=0.88)
    shoulder = (1.5, 1.65)
    head = (0.0, 3.32, 0.0)
    leg_h = 1.15

    def body(self, sp):
        mid, dark, light = self.skin
        sp.core((3.0, 2.7, 2.6), (0.0, 1.65, 0.0), None, mid)                                    # square-cut
        sp.extra((3.06, 2.5, 2.4), (0.0, 1.6, 0.02), None, dark)
        sp.extra((2.6, 0.32, 2.3), (0.0, 3.1, 0.0), None, light)
        for pos, col in (((0.95, 2.72, -1.32), CYAN), ((-0.95, 0.62, -1.32), "ffe83a"),          # highlight pixels
                         ((1.55, 2.2, -0.4), CYAN), ((-1.55, 1.2, 0.6), "ffe83a")):
            R = None if abs(pos[0]) < 1.5 else G.ry(90)
            sp.extra((0.4, 0.4, 0.1), pos, R, col)
        for pos, col in (((-2.0, 2.9, -0.3), CYAN), ((2.1, 1.0, -0.2), PINK), ((1.4, 3.9, 0.4), LIME)):
            sp.extra((0.36, 0.36, 0.36), pos, None, col, material="Neon")                         # loose pixels

    def features(self, sp):
        dimples(sp)
        eyes(sp, w=0.48, hgt=0.48)
        mouth_smile(sp, width=0.5)
        arms(sp, self.limb)
        legs(sp, self.limb, self.shoe)
        sprout(sp, at=(0.0, 3.25, 0.0))
        crown(sp, jewel=CYAN)


class GlowTaterKind(Kind):
    """A glow stick: tall and glowing lime green all over, a dark cap on top with a loop to hang it by
    and sparks of light round it."""
    pid, display, rarity, area = "GlowTater", "Glow Tater", "Legendary", "Neon"
    skin = (LIME, "5ee02a", "a4ff7a")
    limb = "2a8a2a"
    shoe = "1e3a1e"
    face = dict(z=-1.3, eye_y=2.5, eye_dx=0.46, mouth_y=1.72, cheek_dx=0.8)
    shoulder = (1.45, 2.0)
    head = (0.0, 4.12, 0.0)
    leg_h = 1.3

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 3.3, 2.9, 2.6, 1.9, 0.5, (mid, dark, light), core=True, material="Neon")    # glowing
        sp.extra((2.3, 0.5, 2.1), (0.0, 3.5, 0.0), None, "3a3a46")                               # a dark cap
        sp.extra((1.7, 0.4, 1.55), (0.0, 3.85, 0.0), G.ry(45), "2a2a34")
        for k, x in enumerate((-0.28, 0.28)):                                                 # a loop
            sp.extra((0.14, 0.7, 0.14 + 0.02 * k), (x, 4.2, 0.35), G.rz(-x * 40), "4a4a56")
        for pos in ((-1.85, 3.2, -0.5), (1.9, 1.2, 0.2)):
            sp.extra((0.22, 0.22, 0.22), pos, ori(35, 45, 0), "ffffff", material="Neon")       # sparks of light

    def features(self, sp):
        dimples(sp, col="2a8a2a")
        eyes(sp, w=0.44, hgt=0.6)
        mouth_smile(sp, width=0.5, cheek_col="ff6aa8")
        arms(sp, self.limb, hand=LIME)
        legs(sp, self.limb, self.shoe)
        sprout(sp, at=(0.0, 4.0, -0.3))
        crown(sp, at=(0.0, 4.12, -0.3), jewel=PINK)


class DJSpudKind(Kind):
    """A DJ: purple, big headphones over its head, dark shades with a pink shine and a glowing
    music note in the air."""
    pid, display, rarity, area = "DJSpud", "DJ Spud", "Mythic", "Neon"
    skin = ("6a3fd0", "5430b0", "8458e8")
    limb = "5430b0"
    shoe = "1e1a2a"
    face = dict(z=-1.45, eye_y=2.32, eye_dx=0.5, mouth_y=1.5, cheek_dx=0.84)
    shoulder = (1.55, 1.8)
    head = (0.0, 3.62, 0.0)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 2.95, 3.2, 2.9, 2.0, 0.6, (mid, dark, light), core=True)
        sp.extra((2.45, 0.7, 2.2), (0.0, 3.1, 0.05), ori(0, -8, 3), light)
        black = "1e1a2a"
        sp.extra((3.5, 0.26, 0.56), (0.0, 3.5, 0.1), None, black)                                # big headphones
        for s in (-1, 1):
            sp.extra((0.6, 1.0, 1.0), (s * 1.78, 2.86, 0.1), None, black)
        for s in (-1, 1):                                                                    # dark shades
            sp.extra((0.66, 0.5, 0.1), (s * 0.5, 2.36, -1.58), None, "141220")
        sp.extra((0.5, 0.08, 0.1), (0.52, 2.5, -1.64), G.rz(20), PINK, material="Neon")          # a pink shine
        sp.extra((0.4, 0.32, 0.3), (-1.95, 3.9, -0.3), G.rz(20), CYAN, material="Neon")         # a music note
        sp.extra((0.1, 0.9, 0.1), (-1.79, 4.3, -0.3), None, CYAN, material="Neon")

    def features(self, sp):
        dimples(sp)
        eyes(sp)
        mouth_smile(sp, width=0.6)
        arms(sp, self.limb, hand=PINK)
        legs(sp, self.limb, self.shoe)
        sprout(sp)
        crown(sp, jewel=PINK)


class HoverFryKind(Kind):
    """A tall chrome potato of the future: glowing cyan stripes, a see-through visor over its eyes and
    a jetpack on its back with glowing jets."""
    pid, display, rarity, area = "HoverFry", "Hover Fry", "Secret", "Neon"
    skin = ("c8d0dc", "a8b2c0", "e0e6ee")
    limb = "8a94a4"
    shoe = "3a404c"
    face = dict(z=-1.3, eye_y=2.55, eye_dx=0.45, mouth_y=1.75, cheek_dx=0.8)
    shoulder = (1.45, 2.0)
    head = (0.0, 3.72, 0.0)
    leg_h = 1.3

    def body(self, sp):
        mid, dark, light = self.skin
        D = 2.6
        octo(sp, 0.35, 3.3, 2.9, D, 1.9, 0.5, (mid, dark, light), core=True)
        for y in (3.1, 0.7):
            sp.extra((1.96, 0.12, 0.1), (0.0, y, -D / 2 - 0.01), None, CYAN, material="Neon")        # glowing stripes
        sp.extra((2.0, 0.62, 0.12), (0.0, 2.55, -1.42), None, "6ff3ff", transparency=0.35)          # a visor
        for s in (-1, 1):                                                                    # a jetpack
            sp.extra((0.72, 1.7, 0.72), (s * 0.55, 2.0, 1.62), G.ry(45), "8a94a4")
            sp.extra((0.4, 0.62, 0.4), (s * 0.55, 0.92, 1.62), G.ry(45), "ff9a1f", material="Neon")

    def features(self, sp):
        dimples(sp, col="6a7484")
        eyes(sp, w=0.44, hgt=0.5)
        mouth_smile(sp, width=0.5)
        arms(sp, self.limb, hand="e0e6ee")
        legs(sp, self.limb, self.shoe)
        sprout(sp)
        crown(sp, jewel=CYAN)


class LaserTuberKind(Kind):
    """A laser show: dark with glowing pink edges, red glowing eyes and a laser on its head throwing
    beams of red, green, cyan and pink into the sky."""
    pid, display, rarity, area = "LaserTuber", "Laser Tuber", "Secret", "Neon"
    skin = ("1e1e2a", "16161f", "2a2a3a")
    limb = "16161f"
    shoe = "2a2a3a"
    face = dict(z=-1.45, eye_y=2.32, eye_dx=0.5, mouth_y=1.55)
    shoulder = (1.55, 1.8)
    head = (0.0, 3.6, -0.3)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        W, D = 3.2, 2.9
        octo(sp, 0.35, 2.95, W, D, 2.0, 0.6, (mid, dark, light), core=True)
        for s in (-1, 1):
            sp.extra((0.12, 2.5, 0.1), (s * 1.06, 1.65, -D / 2 - 0.01), None, PINK, material="Neon")   # glowing edges
        sp.extra((0.7, 0.5, 0.7), (0.0, 3.2, 0.5), None, "8a94a4")                                # a laser
        c = np.array((0.0, 3.4, 0.5))
        for k, (a, col) in enumerate(((-38.0, "ff2a3a"), (-12.0, "3cff6a"), (12.0, CYAN), (38.0, PINK))):
            d = np.array((-np.sin(np.radians(a)), np.cos(np.radians(a)), 0.15 + 0.03 * k))
            stick(sp, c, c + d * 3.6, 0.1, col, n=(0, 0, 1), t=0.1 + 0.01 * k)                     # its beams

    def features(self, sp):
        dimples(sp, col="3a3a4a")
        glow_eyes(sp, "ff2a3a", glint_col=INK, w=0.5, hgt=0.42)
        mouth_smile(sp, width=0.5, cheeks=False)
        arms(sp, self.limb, hand=PINK)
        legs(sp, self.limb, self.shoe)
        sprout(sp, at=(0.0, 3.5, -0.3))
        crown(sp, jewel=PINK)


class CyberOverlordKind(Kind):
    """Part potato, part machine and lord of the city: dark chrome with glowing circuit traces, a
    steel plate over one side of its face with a red cyber eye, chrome shoulder pads and a big crown."""
    pid, display, rarity, area = "CyberOverlord", "Cyber Overlord", "Divine", "Neon"
    skin = ("2a2a36", "1e1e28", "3a3a4a")
    limb = "1e1e28"
    shoe = "3a3a4a"
    face = dict(z=-1.45, eye_y=2.32, eye_dx=0.5, mouth_y=1.5)
    shoulder = (1.55, 1.8)
    head = (0.0, 3.62, 0.0)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        W, D = 3.2, 2.9
        octo(sp, 0.35, 2.95, W, D, 2.0, 0.6, (mid, dark, light), core=True)
        sp.extra((2.45, 0.7, 2.2), (0.0, 3.1, 0.05), ori(0, -8, 3), light)
        sp.extra((1.0, 1.26, 0.08), (-0.52, 2.3, -1.47), None, "a8b2c0")                         # a steel plate
        z = -D / 2                                                                            # circuit traces
        crack(sp, [(0.95, 0.5, z), (0.62, 0.5, z), (0.62, 1.05, z)], (0, 0, -1), w=0.1, col=CYAN)
        crack(sp, [(-0.95, 0.95, z), (-0.45, 0.95, z), (-0.45, 0.45, z)], (0, 0, -1), w=0.1, col=CYAN)
        crack(sp, [(W / 2, 2.6, 0.5), (W / 2, 1.5, 0.5)], (1, 0, 0), w=0.1, col=CYAN)
        for s in (-1, 1):
            sp.extra((1.0, 0.36, 1.3), (s * 1.42, 2.98, 0.0), G.rz(-s * 14), "c8d0dc")             # shoulder pads

    def features(self, sp):
        dimples(sp, col="4a4a5a")
        cyber_eyes(sp)
        glow_mouth(sp, CYAN, width=0.56, hgt=0.14)
        arms(sp, self.limb, hand="c8d0dc")
        legs(sp, self.limb, self.shoe)
        sprout(sp)
        crown(sp, jewel="ff2a3a", size=1.2)


NEON = [PixelSpudKind(), GlowTaterKind(), DJSpudKind(), HoverFryKind(), LaserTuberKind(), CyberOverlordKind()]
