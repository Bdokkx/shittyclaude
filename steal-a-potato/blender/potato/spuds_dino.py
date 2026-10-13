"""Dino Valley potatoes, worst to best: FossilFry, DinoEggSpud, RaptorTater, TriceraTot, PteroSpud,
RexOverlord. Same rig, features and rules as the Meadow Patch kinds (spuds.py).

RexOverlord's arms are the same ArmL/ArmR and HandL/HandR, only tiny."""
import numpy as np

import spsgeo as G

from .bricks import ori
from .spuds import (INK, Kind, arms, crown, dimples, eyes, legs, mouth_smile, octo, sprout)
from .spuds_lava import chamfer_normal, crack, stick

BONE = ("f4ecd8", "e6dcc2")


def reptile_eyes(sp, col="ffd23f", w=0.5, hgt=0.56, slit=(0.12, 0.44)):
    """Two yellow reptile eyes, a dark slit for each pupil."""
    f = sp.kind.face
    z, y, dx = f["z"], f["eye_y"], f["eye_dx"]
    h = sp.holder("Eyes", (0.0, y, z))
    for s in (1, -1):
        ex = s * dx
        sp.plate(h, "Eye", (w, hgt, 0.1), (ex, y, z - 0.04), color=col)
        sp.plate(h, "Pupil", (slit[0], slit[1], 0.1), (ex - s * 0.04, y, z - 0.09), color=INK)
    return h


def bone(sp, a, b, w, col=BONE[0], knob=None):
    """A cartoon bone from a to b: a shaft with a knob at the far end."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    stick(sp, a, b, w, col, n=(0, 0, 1), t=w, material="Plastic")
    k = knob or w * 1.9
    sp.extra((k, k * 0.62, k * 0.7), b, ori(0, 0, float(np.degrees(np.arctan2(b[1] - a[1], b[0] - a[0])))) @ G.rz(90),
             BONE[1])


class FossilFryKind(Kind):
    """A tall lump of fossil stone: a dinosaur bone stuck in its head, an ammonite's coil set in its
    side and a little bone in its front."""
    pid, display, rarity, area = "FossilFry", "Fossil Fry", "Epic", "Dino"
    skin = ("cdbf9e", "b4a684", "ddd1b4")
    limb = "b4a684"
    shoe = "7a6a4a"
    face = dict(z=-1.3, eye_y=2.6, eye_dx=0.46, mouth_y=1.85, cheek_dx=0.8)
    shoulder = (1.45, 2.1)
    head = (-0.2, 3.85, 0.0)
    leg_h = 1.3

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 3.3, 2.9, 2.6, 1.9, 0.5, (mid, dark, light), core=True)
        sp.extra((2.3, 0.6, 2.1), (0.0, 3.45, 0.0), ori(0, 12, -3), light)
        a, b = np.array((0.95, 3.25, 0.35)), np.array((1.95, 4.75, 0.35))                      # a bone stuck in its head
        stick(sp, a, b, 0.34, BONE[0], n=(0, 0, 1), t=0.34, material="Plastic")
        d = (b - a) / np.linalg.norm(b - a)
        across = np.array((-d[1], d[0], 0.0))
        for side in (-1, 1):                                                                 # its knobbly end
            sp.extra((0.36, 0.36, 0.4 + 0.02 * (side > 0)), b + across * side * 0.2, G.rz(45), BONE[1])
        sp.extra((0.78, 0.78, 0.1), (0.6, 0.9, -1.33), G.rz(15), "8a6a42")                      # an ammonite's coil
        sp.extra((0.52, 0.52, 0.12), (0.64, 0.93, -1.35), G.rz(40), "c8a878")
        sp.extra((0.26, 0.26, 0.14), (0.68, 0.96, -1.37), G.rz(5), "8a6a42")
        bone(sp, (-0.95, 0.7, -1.33), (-0.4, 0.88, -1.33), 0.16)                              # a little bone

    def features(self, sp):
        dimples(sp)
        eyes(sp, w=0.44, hgt=0.6)
        mouth_smile(sp, width=0.52)
        arms(sp, self.limb)
        legs(sp, self.limb, self.shoe)
        sprout(sp, at=(-0.2, 3.72, 0.0))
        crown(sp, jewel="ff8a1f")


class DinoEggSpudKind(Kind):
    """A speckled dinosaur egg, tall and round-topped, cracked across the top with a piece of shell
    perched on it like a cap."""
    pid, display, rarity, area = "DinoEggSpud", "Dino Egg Spud", "Epic", "Dino"
    skin = ("eef0d8", "d8dcc0", "f8faea")
    limb = "c8d0a8"
    shoe = "6a9a4a"
    face = dict(z=-1.4, eye_y=2.2, eye_dx=0.5, mouth_y=1.45, cheek_dx=0.84)
    shoulder = (1.5, 1.8)
    head = (0.1, 3.92, 0.0)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 2.9, 3.0, 2.8, 1.9, 0.6, (mid, dark, light), core=True)
        sp.extra((2.5, 0.55, 2.3), (0.0, 3.1, 0.0), G.ry(20), light)                           # round-topped
        sp.extra((1.7, 0.45, 1.6), (0.0, 3.5, 0.0), G.ry(55), mid)
        for pos, R, k in (((0.8, 0.78, -1.42), G.rz(20), 0.34), ((-0.75, 2.85, -1.2), G.rz(-10), 0.28),
                          ((1.52, 2.2, 0.2), G.ry(90) @ G.rz(30), 0.4)):
            sp.extra((k, k * 0.8, 0.1), pos, R, "6a9a4a")                                         # speckles
        n, mid_ = chamfer_normal(3.0, 2.8, 1.9, 0.6, 1)                                         # cracked down one side
        u = np.array((-n[2], 0.0, n[0]))
        crack(sp, [mid_ + u * 0.1 + (0, 2.88, 0), mid_ - u * 0.2 + (0, 2.4, 0), mid_ + u * 0.15 + (0, 1.95, 0),
                   mid_ - u * 0.1 + (0, 1.55, 0)], n, w=0.12, col="7a7a5a", material="Plastic")
        sp.extra((1.4, 0.36, 1.25), (0.1, 3.82, 0.0), ori(0, 30, -12), light)                    # a piece of shell

    def features(self, sp):
        dimples(sp)
        eyes(sp)
        mouth_smile(sp)
        arms(sp, self.limb)
        legs(sp, self.limb, self.shoe)
        sprout(sp, at=(0.1, 3.85, 0.0))
        crown(sp, jewel="6a9a4a")


class RaptorTaterKind(Kind):
    """A velociraptor: green with dark stripes down its back, yellow slit eyes, a toothy grin, a
    crest of red quills and a long stiff tail."""
    pid, display, rarity, area = "RaptorTater", "Raptor Tater", "Legendary", "Dino"
    skin = ("6a9a4a", "568038", "80b05e")
    limb = "568038"
    shoe = "3a5a2a"
    face = dict(z=-1.45, eye_y=2.32, eye_dx=0.52, mouth_y=1.5)
    shoulder = (1.55, 1.8)
    head = (0.0, 3.7, 0.0)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 2.95, 3.2, 2.9, 2.0, 0.6, (mid, dark, light), core=True)
        sp.extra((2.45, 0.7, 2.2), (0.0, 3.1, 0.05), ori(0, -8, 3), light)
        stripe = "3e5a28"
        for y in (2.5, 1.85, 1.2):                                                            # stripes down its back
            sp.extra((2.1, 0.26, 0.1), (0.0, y, 1.47), G.rz(10), stripe)
        for k, (x, lean) in enumerate(((-0.35, 18.0), (0.05, 2.0), (0.42, -16.0))):           # red quills
            R = G.rz(lean) @ G.rx(28)
            sp.extra((0.22, 1.2, 0.1 + 0.01 * k), np.array((x, 3.25, 0.6)) + R @ (0, 0.55, 0), R, "d7372c")
        stick(sp, (0.0, 1.3, 1.2), (0.25, 1.0, 2.6), 0.62, mid, n=(0, 1, 0), t=0.62, material="Plastic")   # a tail
        stick(sp, (0.22, 1.02, 2.5), (0.5, 0.95, 3.6), 0.38, dark, n=(0, 1, 0), t=0.38, material="Plastic")

    def features(self, sp):
        dimples(sp)
        reptile_eyes(sp)
        f = self.face
        z, y = f["z"], f["mouth_y"]
        h = sp.holder("Mouth", (0.0, y, z))                                                  # a toothy grin
        sp.plate(h, "Mouth", (0.86, 0.3, 0.1), (0.0, y, z - 0.04))
        for x in (-0.22, 0.22):
            sp.plate(h, "Tooth", (0.17, 0.17, 0.1), (x, y + 0.1, z - 0.09), G.rz(45), color="ffffff")
        arms(sp, self.limb, hand="80b05e")
        legs(sp, self.limb, self.shoe)
        sprout(sp)
        crown(sp, jewel="d7372c")


class TriceraTotKind(Kind):
    """A triceratops: teal, a great orange frill fanned up behind its head with knobs round its
    edge, two long horns over its eyes and a little one on its nose."""
    pid, display, rarity, area = "TriceraTot", "Tricera Tot", "Mythic", "Dino"
    skin = ("4aa898", "38907e", "62bcac")
    limb = "38907e"
    shoe = "24685a"
    face = dict(z=-1.45, eye_y=2.22, eye_dx=0.5, mouth_y=1.4, cheek_dx=0.84)
    shoulder = (1.55, 1.75)
    head = (0.0, 3.62, 0.0)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 2.95, 3.2, 2.9, 2.0, 0.6, (mid, dark, light), core=True)
        sp.extra((2.45, 0.7, 2.2), (0.0, 3.1, 0.05), ori(0, -8, 3), light)
        Rf = G.rx(-18)                                                                        # a great frill
        c = np.array((0.0, 3.3, 0.9))
        sp.extra((3.9, 2.4, 0.24), c, Rf, "e8a050")
        for x, y in ((-1.7, 0.95), (0.0, 1.32), (1.7, 0.95)):
            sp.extra((0.5, 0.5, 0.3), c + Rf @ (x, y, 0.0), Rf @ G.rz(45), "c8803a")             # knobs round its edge
        horn = BONE[0]
        for s in (-1, 1):                                                                    # long horns
            stick(sp, (s * 0.5, 2.85, -1.2), (s * 0.82, 4.0, -1.95), 0.26, horn, n=(1, 0, 0), t=0.26,
                  material="Plastic")
        stick(sp, (0.0, 1.85, -1.42), (0.0, 2.05, -1.88), 0.2, horn, n=(1, 0, 0), t=0.2, material="Plastic")

    def features(self, sp):
        dimples(sp)
        eyes(sp)
        mouth_smile(sp)
        arms(sp, self.limb)
        legs(sp, self.limb, self.shoe)
        sprout(sp)
        crown(sp, jewel="e8a050")


class PteroSpudKind(Kind):
    """A pterodactyl: rusty orange, great pointed wings spread behind it, a long crest sweeping back
    from its head and a long pointed beak."""
    pid, display, rarity, area = "PteroSpud", "Ptero Spud", "Secret", "Dino"
    skin = ("d0783a", "b4602a", "e4904e")
    limb = "b4602a"
    shoe = "6a3a1a"
    face = dict(z=-1.45, eye_y=2.38, eye_dx=0.52, mouth_y=1.62)
    shoulder = (1.55, 1.8)
    head = (0.0, 3.62, -0.1)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 2.95, 3.2, 2.9, 2.0, 0.6, (mid, dark, light), core=True)
        sp.extra((2.45, 0.7, 2.2), (0.0, 3.1, 0.05), ori(0, -8, 3), light)
        wing = "a85a2a"
        for s in (-1, 1):                                                                    # great pointed wings
            root = np.array((s * 0.7, 2.6, 1.1))
            for k, (a, L, w) in enumerate(((30.0, 3.4, 0.7), (6.0, 3.0, 0.95), (-22.0, 2.0, 0.85))):
                d = np.array((s * np.cos(np.radians(a)), np.sin(np.radians(a)), 0.3))
                stick(sp, root, root + d * L, w, wing if k != 1 else "c06a32", n=(0, 0, 1), t=0.12 + 0.015 * k,
                      material="Plastic")
        stick(sp, (0.0, 3.2, 0.2), (0.0, 4.0, 2.4), 0.36, dark, n=(1, 0, 0), t=0.2, material="Plastic")   # a crest

    def features(self, sp):
        dimples(sp)
        eyes(sp, w=0.44, hgt=0.6)
        f = self.face
        z, y = f["z"], f["mouth_y"]
        h = sp.holder("Mouth", (0.0, y, z))                                                  # a long pointed beak
        sp.brick(h, "Beak", (0.56, 0.36, 0.9), (0.0, y, z - 0.42), G.rx(-6), "f0c870")
        sp.brick(h, "Beak", (0.32, 0.24, 0.7), (0.0, y - 0.04, z - 1.1), G.rx(-6), "e0b050")
        arms(sp, self.limb)
        legs(sp, self.limb, self.shoe)
        sprout(sp, at=(0.0, 3.5, -0.1))
        crown(sp, jewel="ffd23f")


class RexOverlordKind(Kind):
    """Tyrannosaurus rex and overlord: big and dark green, a great jaw full of teeth, tiny arms,
    spikes down its back, a heavy tail and, at the top level, a big gold crown."""
    pid, display, rarity, area = "RexOverlord", "Rex Overlord", "Secret", "Dino"
    skin = ("3e7a3a", "2e6030", "4e9048")
    limb = "2e6030"
    shoe = "1e3a1e"
    face = dict(z=-1.6, eye_y=2.5, eye_dx=0.58, mouth_y=1.45)
    shoulder = (1.72, 1.95)
    head = (0.0, 3.62, 0.0)
    leg_h = 1.25

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.3, 3.0, 3.5, 3.2, 2.3, 0.6, (mid, dark, light), core=True)
        sp.extra((2.7, 0.6, 2.4), (0.0, 3.12, 0.05), ori(0, -6, 2), light)
        for k, (y, z) in enumerate(((3.25, 0.7), (2.95, 1.35), (2.3, 1.62), (1.5, 1.66))):     # spikes down its back
            sp.extra((0.5, 0.5, 0.12 + 0.02 * k), (0.0, y, z), G.rx(-30 * k) @ G.rz(45), "1e4a20")
        stick(sp, (0.0, 1.2, 1.3), (0.35, 0.7, 3.0), 0.9, mid, n=(0, 1, 0), t=0.8, material="Plastic")   # a heavy tail
        stick(sp, (0.3, 0.75, 2.85), (0.6, 0.55, 4.1), 0.55, dark, n=(0, 1, 0), t=0.5, material="Plastic")

    def features(self, sp):
        dimples(sp)
        reptile_eyes(sp, col="ffb02a", w=0.52, hgt=0.46)
        f = self.face
        z, y = f["z"], f["mouth_y"]
        h = sp.holder("Mouth", (0.0, y, z))                                                  # a great jaw of teeth
        sp.plate(h, "Mouth", (1.5, 0.5, 0.1), (0.0, y, z - 0.04))
        for x in (-0.46, 0.0, 0.46):
            sp.plate(h, "Tooth", (0.2, 0.2, 0.1), (x, y + 0.2, z - 0.09), G.rz(45), color="ffffff")
        for x in (-0.33, 0.33):
            sp.plate(h, "Tooth", (0.18, 0.18, 0.1), (x, y - 0.2, z - 0.09), G.rz(45), color="ffffff")
        arms(sp, self.limb, length=0.85, thick=0.38, spread=20.0, hand="4e9048", hand_size=(0.46, 0.4, 0.4))
        legs(sp, self.limb, self.shoe, thick=0.72, shoe_size=(1.05, 0.56, 1.45))
        sprout(sp)
        crown(sp, jewel="ff3b5c", size=1.2)


DINO = [FossilFryKind(), DinoEggSpudKind(), RaptorTaterKind(), TriceraTotKind(), PteroSpudKind(), RexOverlordKind()]
