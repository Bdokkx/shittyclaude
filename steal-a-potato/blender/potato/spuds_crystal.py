"""Crystal Caverns potatoes, worst to best: GeodeSpud, AmethystTater, EmeraldFry, DiamondSpud,
PrismPotato, ObsidianOverlord. Same rig, features and rules as the Meadow Patch kinds (spuds.py).

PrismPotato's body is the kit's one see-through piece: clear glass (Transparency 0.4) with the light
inside it showing through."""
import numpy as np

import spsgeo as G

from .bricks import ori
from .spuds import (INK, Kind, arms, crown, dimples, eyes, legs, mouth_smile, octo, sprout, star)
from .spuds_lava import chamfer_normal, crack, glow_mouth, stick

AMETHYST = ("8e3fe8", "b57bff", "a35cff", "7a2ee0", "c99bff")
RAINBOW = ("ff3b3b", "ff9a1f", "ffe83a", "3bd96b", "3b8bff", "9b4dff")
GLASS = 0.4


def slant_eyes(sp, col, w=0.6, hgt=0.38, tilt=14.0, pupil=0.17, pupil_col=INK):
    """Two narrow glowing eyes slanting down to the middle, a dark pupil in each: a glare."""
    f = sp.kind.face
    z, y, dx = f["z"], f["eye_y"], f["eye_dx"]
    h = sp.holder("Eyes", (0.0, y, z))
    for s in (1, -1):
        ex = s * dx
        R = G.rz(s * tilt)
        sp.plate(h, "Eye", (w, hgt, 0.1), (ex, y, z - 0.04), R, color=col, material="Neon")
        sp.plate(h, "Pupil", (pupil, pupil, 0.1), (ex - s * 0.07, y - 0.02, z - 0.09), R, color=pupil_col)
    return h


def jagged_crown(sp, at=None, cols=("120c18", "2c2238"), jewel="c86bff"):
    """A crown of jagged black glass: a band, four spikes of different heights leaning their own
    ways (three at the front, one behind) and a glowing jewel."""
    x, y, z = at or sp.kind.head
    c = np.array((x, y - 0.12, z))
    h = sp.holder("Crown", tuple(c))
    R = G.rz(-5.0)
    sp.brick(h, "Band", (1.8, 0.45, 1.6), c + R @ (0, 0.22, 0), R, cols[1])
    for px, pz, ht, lean in ((-0.6, -0.5, 0.95, 12.0), (0.02, -0.56, 1.3, -4.0), (0.6, -0.46, 0.8, -15.0),
                             (0.12, 0.52, 1.05, 6.0)):
        Rp = R @ G.rz(lean)
        sp.brick(h, "Point", (0.36, ht, 0.36), c + R @ (px, 0.38, pz) + Rp @ (0, ht / 2, 0), Rp @ G.ry(45), cols[0])
    sp.plate(h, "Jewel", (0.34, 0.34, 0.1), c + R @ (0.0, 0.22, -0.82), R @ G.rz(45), color=jewel, material="Neon")
    return h


class GeodeSpudKind(Kind):
    """A grey rock of a potato, cracked open across the top: a white lining and purple crystals
    bursting out of the crack, one of them glowing."""
    pid, display, rarity, area = "GeodeSpud", "Geode Spud", "Rare", "Crystal"
    skin = ("8e8c94", "76747c", "a4a2aa")
    limb = "76747c"
    shoe = "4a4850"
    face = dict(z=-1.45, eye_y=2.1, eye_dx=0.5, mouth_y=1.36, cheek_dx=0.84)
    shoulder = (1.6, 1.7)
    head = (0.62, 2.98, 0.45)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 2.7, 3.2, 2.9, 2.0, 0.6, (mid, dark, light), core=True)
        sp.extra((2.6, 0.14, 2.4), (0.0, 2.74, 0.0), None, "efe8f8")                        # its crystal lining
        for x, k, col in ((-0.78, 0.62, light), (0.06, 0.5, mid), (0.84, 0.66, light)):     # the broken edge
            sp.extra((k, k, 0.5), (x, 2.72, -1.18), G.rz(45), col)
        for pos, lean, size, col in (((-0.3, 3.2, -0.42), (-14, 8), (0.6, 1.6), AMETHYST[0]),    # crystals
                                     ((0.36, 3.05, -0.62), (-18, -22), (0.5, 1.3), AMETHYST[1]),
                                     ((-0.88, 2.98, -0.48), (-14, 28), (0.46, 1.15), AMETHYST[2]),
                                     ((-0.55, 3.0, 0.2), (12, 14), (0.46, 1.2), AMETHYST[3])):
            sp.extra((size[0], size[1], size[0]), pos, G.rz(lean[1]) @ G.rx(lean[0]) @ G.ry(45), col)
        sp.extra((0.36, 0.95, 0.36), (0.02, 3.0, -0.86), G.rz(-4) @ G.rx(-26) @ G.ry(45), "e2c6ff",
                 material="Neon")                                                            # a glowing one

    def features(self, sp):
        dimples(sp)
        eyes(sp)
        mouth_smile(sp)
        arms(sp, self.limb)
        legs(sp, self.limb, self.shoe)
        sprout(sp, at=(0.62, 2.86, 0.5), lean=-6)
        crown(sp, tilt=-14.0)


class AmethystTaterKind(Kind):
    """A purple potato with a ridge of amethyst crystal spikes growing out of its back, the two
    tallest tipped with light."""
    pid, display, rarity, area = "AmethystTater", "Amethyst Tater", "Epic", "Crystal"
    skin = ("9b59d0", "7d3fb3", "b07ae0")
    limb = "7d3fb3"
    shoe = "4a2470"
    face = dict(z=-1.45, eye_y=2.32, eye_dx=0.5, mouth_y=1.55, cheek_dx=0.84)
    shoulder = (1.55, 1.8)
    head = (0.0, 3.7, 0.0)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 2.95, 3.2, 2.9, 2.0, 0.6, (mid, dark, light), core=True)
        sp.extra((2.45, 0.7, 2.2), (0.0, 3.1, 0.05), ori(0, -8, 3), light)
        tips = []
        for base, lz, lx, (w, L), col in (((0.0, 3.0, 0.85), 0, 32, (0.62, 1.75), "c9a0ff"),     # crystal spikes
                                          ((-1.0, 2.65, 0.75), 34, 22, (0.6, 1.85), "a66cff"),
                                          ((1.0, 2.7, 0.8), -32, 24, (0.6, 1.9), "b88aff"),
                                          ((-0.9, 1.55, 1.15), 42, 48, (0.42, 1.1), "8a4be0"),
                                          ((0.88, 1.4, 1.2), -40, 52, (0.4, 1.0), "a66cff"),
                                          ((0.05, 2.0, 1.35), 4, 64, (0.46, 1.25), "8a4be0")):
            R = G.rz(lz) @ G.rx(lx)
            sp.extra((w, L, w), np.array(base) + R @ (0, L / 2, 0), R @ G.ry(45), col)
            tips.append((np.array(base) + R @ (0, L + 0.02, 0), R))
        for i in (0, 2):
            p, R = tips[i]
            sp.extra((0.26, 0.42, 0.26), p, R @ G.ry(45), "f0e0ff", material="Neon")          # tipped with light

    def features(self, sp):
        dimples(sp)
        eyes(sp)
        mouth_smile(sp)
        arms(sp, self.limb)
        legs(sp, self.limb, self.shoe)
        sprout(sp)
        crown(sp, jewel="c99bff")


class EmeraldFryKind(Kind):
    """A tall emerald stood on end: emerald-cut, its corners cut off, its facets in three greens
    round a raised table where its face is, star glints flashing off it."""
    pid, display, rarity, area = "EmeraldFry", "Emerald Fry", "Legendary", "Crystal"
    skin = ("17a35a", "12864a", "26c06f")
    limb = "12864a"
    shoe = "0d5c33"
    face = dict(z=-1.2, eye_y=2.6, eye_dx=0.38, mouth_y=1.82, cheek_dx=0.52, cheek_y=2.12)
    shoulder = (1.4, 2.45)
    head = (0.0, 3.97, 0.0)
    leg_h = 1.3

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.95, 3.15, 2.8, 3.6, 1.8, 0.55, (mid, dark, light), R=G.rx(90), core=True)   # stood on end
        sp.extra((1.5, 3.0, 0.12), (0.0, 2.05, -1.14), None, "45d68f")                      # its table
        star(sp, sp.extra, (1.55, 3.62, -0.62), 0.7, "f2fff6", ori(0, -30, 45))
        star(sp, sp.extra, (-1.35, 0.95, -0.9), 0.5, "f2fff6")

    def features(self, sp):
        dimples(sp)
        eyes(sp, w=0.42, hgt=0.6)
        mouth_smile(sp, width=0.5)
        arms(sp, self.limb, hand="d9ffe9")
        legs(sp, self.limb, self.shoe)
        sprout(sp)
        crown(sp, jewel="2bbf74")


class DiamondSpudKind(Kind):
    """A sparkling diamond, cut like one: a narrow flat table on top, widest at its girdle, then
    tapering away underneath; white and cyan facets, star glints flashing off it."""
    pid, display, rarity, area = "DiamondSpud", "Diamond Spud", "Mythic", "Crystal"
    skin = ("f4fbff", "aeeaf8", "d2f5fd")
    limb = "bfeefb"
    shoe = "5fc8e8"
    face = dict(z=-1.3, eye_y=2.02, eye_dx=0.42, mouth_y=1.28, cheek_dx=0.6)
    shoulder = (1.42, 1.9)
    head = (0.0, 3.47, 0.0)
    leg_h = 1.25

    def body(self, sp):
        mid, dark, light = self.skin
        sp.core((1.6, 2.0, 2.6), (0.0, 1.6, 0.0), None, mid)                                  # the front facet
        for s in (-1, 1):                                                                    # tapering away below
            top, bot = np.array((s * 1.8, 2.6)), np.array((s * 0.7, 0.3))
            u = (top - bot) / np.linalg.norm(top - bot)
            n = np.array((u[1], -u[0])) * s
            c = (top + bot) / 2 - n * 0.5
            sp.extra((1.0, float(np.linalg.norm(top - bot)), 2.4 - 0.03 * (s < 0)), (c[0], c[1], 0.0),
                     G.rz(np.degrees(np.arctan2(-u[0], u[1]))), dark)
        sp.extra((3.4, 0.5, 2.5), (0.0, 2.85, 0.0), None, light)                              # its girdle
        sp.extra((1.7, 0.36, 1.6), (0.0, 3.27, 0.0), None, "ffffff")                          # its table
        star(sp, sp.extra, (2.0, 3.25, -0.55), 0.85, "ffffff", ori(0, -30, 45))               # sparkles
        star(sp, sp.extra, (-1.7, 0.95, -0.75), 0.6, "bff6ff")
        for pos in ((-1.45, 2.85, -1.23), (1.0, 2.85, -1.23)):
            sp.extra((0.24, 0.24, 0.1), pos, G.rz(45), "ffffff", material="Neon")             # glints on its girdle

    def features(self, sp):
        dimples(sp)
        eyes(sp, w=0.44, hgt=0.62)
        mouth_smile(sp, width=0.5)
        arms(sp, self.limb, hand="ffffff")
        legs(sp, self.limb, self.shoe)
        sprout(sp)
        crown(sp, jewel="6ff3ff")


class PrismPotatoKind(Kind):
    """A potato of clear glass, a prism: a beam of white light shines in at one side and fans out
    of the other as a rainbow, and through the glass you can see it split."""
    pid, display, rarity, area = "PrismPotato", "Prism Potato", "Secret", "Crystal"
    skin = ("e6f6ff", "d4eefc", "f2fbff")
    limb = "cdeefc"
    shoe = "9fd8f0"
    face = dict(z=-1.3, eye_y=2.22, eye_dx=0.5, mouth_y=1.48, cheek_dx=0.84)
    shoulder = (1.4, 1.75)
    head = (0.0, 3.6, 0.0)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        sp.core((2.8, 2.6, 2.6), (0.0, 1.65, 0.0), None, mid, transparency=GLASS)              # clear glass
        sp.extra((2.3, 0.6, 2.3), (0.0, 3.2, 0.0), G.ry(45), light, transparency=GLASS)
        S = np.array((0.15, 2.95, 0.35))                                                      # where it splits
        stick(sp, (2.75, 3.65, 0.33), S, 0.26, "ffffff")                                     # white light in
        for i, col in enumerate(RAINBOW):                                                     # a rainbow out
            stick(sp, S + (0.0, -0.03 * i, 0.02 + 0.012 * i), (-2.75, 3.3 - 0.27 * i, 0.37 + 0.012 * i), 0.22, col)
        star(sp, sp.extra, (1.62, 3.3, -0.95), 0.6, "ffffff")

    def features(self, sp):
        dimples(sp)
        eyes(sp)
        mouth_smile(sp)
        arms(sp, self.limb, hand="ffffff")
        legs(sp, self.limb, self.shoe)
        sprout(sp)
        crown(sp, jewel="ff3b5c")


class ObsidianOverlordKind(Kind):
    """Black volcanic glass with glowing purple cracks running through it, shards of glass jutting
    from its shoulders and back, a purple glare and, at the top level, a jagged crown of obsidian."""
    pid, display, rarity, area = "ObsidianOverlord", "Obsidian Overlord", "Secret", "Crystal"
    skin = ("231a2c", "17111e", "352a44")
    limb = "17111e"
    shoe = "2c2238"
    face = dict(z=-1.5, eye_y=2.32, eye_dx=0.52, mouth_y=1.5)
    shoulder = (1.65, 1.85)
    head = (0.0, 3.12, 0.0)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        W, D, F, C = 3.3, 3.0, 2.0, 0.65
        octo(sp, 0.35, 3.0, W, D, F, C, (mid, dark, light), core=True)
        for size, pos, R, col in (((0.45, 1.3, 0.3), (1.45, 3.0, 0.3), ori(10, 20, -28), "3a2e4a"),   # shards
                                  ((0.4, 1.1, 0.28), (-1.5, 2.85, 0.4), ori(-8, -15, 32), "2c2238"),
                                  ((0.5, 1.5, 0.32), (0.2, 2.6, 1.55), ori(35, 10, -6), light)):
            sp.extra(size, pos, R, col)
        n, mid_ = chamfer_normal(W, D, F, C, -1)
        sp.extra((0.14, 0.86, 0.1), mid_ + (0, 2.48, 0) + n * 0.03, G.ry(45), "7a6a94",
                 material="SmoothPlastic")                                                    # a glassy shine
        z = -D / 2
        purple, lilac = "b44dff", "d98bff"
        crack(sp, [(0.95, 0.45, z), (0.7, 0.86, z), (0.86, 1.22, z)], (0, 0, -1), col=purple)   # glowing cracks
        crack(sp, [(-0.36, 0.4, z), (-0.72, 0.66, z)], (0, 0, -1), col=lilac)
        for s, (t0, t1, y0, y1), col in ((1, (-0.4, 0.2, 1.22, 2.3), purple), (-1, (-0.4, 0.15, 0.66, 1.9), lilac)):
            n, mid_ = chamfer_normal(W, D, F, C, s)
            u = np.array((-n[2], 0.0, n[0])) * s
            crack(sp, [mid_ + u * t0 + (0, y0, 0), mid_ + u * t1 + (0, y1, 0)], n, col=col)
        crack(sp, [(W / 2, 2.7, 0.6), (W / 2, 1.3, 0.2)], (1, 0, 0), col=lilac)
        crack(sp, [(-W / 2, 2.5, -0.4), (-W / 2, 1.2, 0.3)], (-1, 0, 0), col=purple)

    def features(self, sp):
        dimples(sp, col="4a3c5c")
        slant_eyes(sp, "d98bff")
        glow_mouth(sp, "b44dff", width=0.62, hgt=0.16)
        arms(sp, self.limb, hand="2c2238")
        legs(sp, self.limb, self.shoe)
        sprout(sp)
        jagged_crown(sp)


CRYSTAL = [GeodeSpudKind(), AmethystTaterKind(), EmeraldFryKind(), DiamondSpudKind(), PrismPotatoKind(),
           ObsidianOverlordKind()]
