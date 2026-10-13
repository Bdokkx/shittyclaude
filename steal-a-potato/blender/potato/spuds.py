"""The potatoes: brick characters on one shared rig (PotatoKit.Potatoes.<Id>).

Rig (every potato):
  Root      invisible, anchored, PrimaryPart, its bottom on the ground (pivot = footprint centre)
  Body      the body's core brick, on Motor6D "Body" (Root -> Body, hinge on the ground)
  Extra     every other brick of the body and everything the kind always wears: children of
            Body, welded to it
  features  each on its own Motor6D named like it, shown by level:
              Dimples 1 only | Eyes 2 | Mouth 3 | ArmL ArmR 4 (on Body) | HandL HandR 5 (on the arms)
              LegL LegR 6 (on Root) | FootL FootR 7 (on the legs) | Sprout 8 | Crown 10
            a one-brick feature is that brick; a feature of several bricks is an invisible part
            with the feature's name, its bricks as its children, welded to it
  LegHeight number attribute: how far Body rises when the legs show (the legs are built for the
            raised body; without legs the body sits on the ground)

Joint frames all have model axes (front -Z, +X the potato's right), so one clip fits every kind.
The hips are always at X = +-HIP_X, Z = 0, so a spin about the body's axis carries the legs round.
"""
import math

import numpy as np

import spsgeo as G
from spsgeo import CF

from .bricks import Bricks, hexc, ori, shade

HIP_X = 0.75
FEATURES = ("Dimples", "Eyes", "Mouth", "ArmL", "ArmR", "HandL", "HandR", "LegL", "LegR", "FootL", "FootR",
            "Sprout", "Crown")
SHOWN_FROM = {"Dimples": 1, "Eyes": 2, "Mouth": 3, "ArmL": 4, "ArmR": 4, "HandL": 5, "HandR": 5, "LegL": 6,
              "LegR": 6, "FootL": 7, "FootR": 7, "Sprout": 8, "Crown": 10}
BUDGET = 45

INK = "1e1a22"          # eyes and mouths
GLINT = "ffffff"
CHEEK = "ff8fa3"
TONGUE = "ff6b8a"
GLOVE = "fff7ec"
GOLD = ("ffd447", "e0a800", "ffe58a")
LEAF = ("55b848", "3f9e3c", "7ad155")


def visible(name, level):
    if name == "Dimples":
        return level == 1
    return level >= SHOWN_FROM[name]


class Spud:
    """One potato under construction. Positions are in the potato's own frame: origin the middle of
    its footprint on the ground, front -Z, +X its right."""

    def __init__(self, sc, parent, kind, base=None):
        self.sc = sc
        self.kind = kind
        self.base = base if base is not None else CF()
        self.m = sc.model(parent, kind.pid)
        self.b = Bricks(sc, self.base, anchored=False, massless=True)
        self.root = sc.part(self.m, "Root", (2.0, 0.4, 2.0), self.base * CF((0.0, 0.2, 0.0)), (255, 255, 255),
                            material="SmoothPlastic", transparency=1.0, anchored=True, collide=False, touch=False,
                            query=False, shadow=False, massless=False, grid=False, surfaces="smooth",
                            pivot=CF((0.0, -0.2, 0.0)))
        self.m.p["primary"] = self.root
        self.body = None
        self.feat = {}
        self.motors = []        # (name, part0, part1, hinge (local CF))
        self.welds = []         # (part0, part1)

    # ---------------------------------------------------------------- pieces
    def core(self, size, pos, R=None, color=None):
        self.body = self.b.part(self.m, "Body", size, pos, R, color)
        self.motors.append(("Body", self.root, self.body, CF()))
        return self.body

    def extra(self, size, pos, R=None, color="ffffff", material="Plastic", **kw):
        p = self.b.part(self.body, "Extra", size, pos, R, color, material=material, **kw)
        self.welds.append((self.body, p))
        return p

    def holder(self, name, pos, part0=None):
        """The invisible part a several-brick feature hangs on (its Motor6D hinge is at pos)."""
        h = self.b.part(self.m, name, (0.2, 0.2, 0.2), pos, None, "ffffff", material="SmoothPlastic",
                        transparency=1.0, shadow=False)
        self.feat[name] = h
        self.motors.append((name, part0 or self.body, h, CF(np.asarray(pos, float))))
        return h

    def brick(self, holder, name, size, pos, R=None, color="ffffff", material="Plastic", **kw):
        p = self.b.part(holder, name, size, pos, R, color, material=material, **kw)
        self.welds.append((holder, p))
        return p

    def plate(self, holder, name, size, pos, R=None, color=INK, material="SmoothPlastic"):
        p = self.b.plate(holder, name, size, pos, R, color, material=material)
        self.welds.append((holder, p))
        return p

    def single(self, name, size, pos, R, color, hinge, part0, material="Plastic"):
        """A one-brick feature: the brick itself carries the name and the Motor6D."""
        p = self.b.part(self.m, name, size, pos, R, color, material=material)
        self.feat[name] = p
        self.motors.append((name, part0, p, CF(np.asarray(hinge, float))))
        return p

    # ---------------------------------------------------------------- finish
    def finish(self):
        k = self.kind
        self.sc.attr(self.m, "LegHeight", float(k.leg_h))
        for p0, p1 in self.welds:
            self.sc.weld(p0, p1, name="Weld")
        for name, p0, p1, hinge in self.motors:
            self.sc.motor(p0, p1, name, self.base * hinge, parent=p1)
        self.sc.anim_controller(self.m)
        n = sum(1 for x in self.m.walk() if x.kind == "Part")
        assert n <= BUDGET, "%s: %d parts" % (k.pid, n)
        missing = [f for f in FEATURES if f not in self.feat]
        assert not missing, "%s lacks %s" % (k.pid, missing)
        return self.m


# ==================================================================== body shapes

def octo(sp, y0, y1, w, d, front, chamfer, cols, x=0.0, z=0.0, R=None, core=False):
    """An octagonal prism from four slabs (Folk Valley's tower trick): a slab long in Z whose
    end is the flat front (width `front`), a slab long in X for the sides, and two slabs along
    the diagonals whose ends are the chamfers (`chamfer` along each axis). cols = (front, sides,
    chamfers). With core=True the front slab is the Body core."""
    R = np.eye(3) if R is None else R
    h = y1 - y0
    c = np.array((x, (y0 + y1) / 2, z))
    side = d - 2 * chamfer                     # depth of the side faces
    out = []
    mk = sp.core if core else sp.extra
    out.append(mk((front, h, d), c, R, cols[0]))
    out.append(sp.extra((w, h * 0.985, side), c, R, cols[1]))
    # chamfer: from the front edge (front/2, d/2) to the side edge (w/2, side/2)
    ax, az = (w - front) / 2, (d - side) / 2
    ln = math.hypot(ax, az)
    ang = math.degrees(math.atan2(az, ax))     # the chamfer face's slope
    # the slab runs perpendicular to the chamfer face; its ends sit on both opposite chamfers
    mx, mz = (front / 2 + w / 2) / 2, (d / 2 + side / 2) / 2
    nrm = np.array((az, ax)) / ln            # outward normal of the chamfer (x, z)
    dist = mx * nrm[0] + mz * nrm[1]
    for s, kh in ((-1, 0.97), (1, 0.955)):
        a = math.degrees(math.atan2(nrm[1], nrm[0]))
        Rs = R @ G.ry(s * a)                   # local X along the normal (mirrored for the other diagonal)
        out.append(sp.extra((2 * dist, h * kh, ln), c, Rs, cols[2]))
    return out


# ==================================================================== shared features

def dimples(sp, col=INK, size=0.3):
    f = sp.kind.face
    z = f["z"]
    h = sp.holder("Dimples", (0.0, f["eye_y"], z))
    dx = f.get("dimple_dx", f["eye_dx"] * 0.85)
    for s in (-1, 1):
        sp.plate(h, "Dimple", (size, size, 0.1), (s * dx, f["eye_y"] - 0.12, z - 0.04), color=col)
    return h


def eyes(sp, w=0.5, hgt=0.74, glint=0.22, brows=None, brow_col=INK, brow_dy=(0.0, 0.0)):
    """Two tall dark eyes, each with a white glint high on the same side (one light, from the
    potato's right). brows = (tilt over its right eye, tilt over its left eye) in degrees adds a
    dark brow over each."""
    f = sp.kind.face
    z, y, dx = f["z"], f["eye_y"], f["eye_dx"]
    h = sp.holder("Eyes", (0.0, y, z))
    for s in (1, -1):
        ex = s * dx
        sp.plate(h, "Eye", (w, hgt, 0.1), (ex, y, z - 0.04))
        sp.plate(h, "Glint", (glint, glint, 0.1), (ex + w / 2 - glint / 2 - 0.05, y + hgt / 2 - glint / 2 - 0.06,
                                                   z - 0.09), color=GLINT)
        if brows:
            i = 0 if s > 0 else 1
            sp.plate(h, "Brow", (w + 0.18, 0.15, 0.1), (ex, y + hgt / 2 + 0.24 + brow_dy[i], z - 0.025),
                     G.rz(brows[i]), color=brow_col)
    return h


def mouth_smile(sp, width=0.66, tongue=True, cheeks=True, cheek_col=CHEEK):
    """An open smile with a pink tongue, and a pink cheek either side."""
    f = sp.kind.face
    z, y = f["z"], f["mouth_y"]
    h = sp.holder("Mouth", (0.0, y, z))
    sp.plate(h, "Mouth", (width, 0.3, 0.1), (0.0, y, z - 0.04))
    if tongue:
        sp.plate(h, "Tongue", (width * 0.52, 0.13, 0.1), (0.0, y - 0.07, z - 0.09), color=TONGUE)
    if cheeks:
        cx = f.get("cheek_dx", f["eye_dx"] + 0.36)
        cy = f.get("cheek_y", y + 0.36)
        for s in (-1, 1):
            sp.plate(h, "Cheek", (0.42, 0.24, 0.1), (s * cx, cy, z - 0.025), color=cheek_col)
    return h


def arms(sp, col, length=1.45, thick=0.52, spread=38.0, hand=GLOVE, hand_size=(0.8, 0.74, 0.74)):
    """Stubby arms hanging down and out from the shoulders; a glove on each."""
    sx, sy = sp.kind.shoulder
    for s, side in ((-1, "L"), (1, "R")):
        hinge = np.array((s * sx, sy, 0.0))
        R = G.rz(s * spread)                       # tip swung outwards
        down = R @ np.array((0.0, -1.0, 0.0))
        c = hinge + down * (length / 2 - 0.15)
        arm = sp.single("Arm" + side, (thick, length, thick), c, R, col, hinge, sp.body)
        wrist = hinge + down * (length - 0.2)
        hc = wrist + down * (hand_size[1] / 2 - 0.05)
        sp.single("Hand" + side, hand_size, hc, R, hand, wrist, arm)


def legs(sp, col, shoe, thick=0.62, shoe_size=(0.92, 0.56, 1.3)):
    """Legs from the ground up into the raised body; a shoe on each, toes forward."""
    lh = sp.kind.leg_h
    top = lh + 0.56                                 # well up inside the raised body
    for s, side in ((-1, "L"), (1, "R")):
        x = s * HIP_X
        hip = (x, lh + 0.1, 0.0)
        leg = sp.single("Leg" + side, (thick, top - 0.2, thick), (x, 0.2 + (top - 0.2) / 2, 0.0), None, col, hip,
                        sp.root)
        ankle = (x, 0.3, 0.0)
        sw, shh, sd = shoe_size
        sp.single("Foot" + side, shoe_size, (x + s * 0.04, shh / 2, -sd / 2 + 0.38), G.ry(-s * 6), shoe, ankle, leg)


def sprout(sp, lean=8.0, at=None):
    """A green shoot with two leaves on top of the head."""
    x, y, z = at or sp.kind.head
    h = sp.holder("Sprout", (x, y, z))
    R = G.rz(-lean)
    base = np.array((x, y, z))
    sp.brick(h, "Stem", (0.3, 1.15, 0.3), base + R @ (0, 0.45, 0), R, LEAF[1])
    tip = base + R @ (0, 0.92, 0)
    for s in (-1, 1):
        Rl = R @ G.ry(s * 12) @ G.rz(s * 28)
        sp.brick(h, "Leaf", (0.95, 0.16, 0.55), tip + Rl @ (s * 0.48, 0.0, 0.0), Rl, LEAF[0] if s < 0 else LEAF[2])
    return h


def crown(sp, tilt=-9.0, cols=("f5b700", "ffd447", "e0a800"), jewel="ff3b5c", at=None, size=1.0):
    """A gold crown worn at a jaunty angle: a band, three points (two at the front, one behind) and
    a Neon jewel at the front."""
    x, y, z = at or sp.kind.head
    c = np.array((x, y - 0.12, z))
    h = sp.holder("Crown", tuple(c))
    R = G.rz(tilt) @ G.ry(4)
    k = size
    sp.brick(h, "Band", (1.7 * k, 0.5 * k, 1.5 * k), c + R @ (0, 0.25 * k, 0), R, cols[0])
    for px, pz, col in ((-0.6, -0.5, cols[1]), (0.6, -0.5, cols[1]), (0.0, 0.48, cols[2])):
        sp.brick(h, "Point", (0.44 * k, 0.66 * k, 0.44 * k), c + R @ (px * k, 0.78 * k, pz * k), R @ G.ry(45), col)
    sp.plate(h, "Jewel", (0.38 * k, 0.3 * k, 0.1), c + R @ (0.0, 0.26 * k, -0.79 * k), R, color=jewel, material="Neon")
    return h


def star(sp, parent_fn, centre, size, col, R=None, material="Neon"):
    """A four-point star glint: two thin crossing bars."""
    R = np.eye(3) if R is None else R
    c = np.asarray(centre, float)
    out = []
    for k, rz in enumerate((0.0, 90.0)):
        out.append(parent_fn((size, size * 0.24, 0.12), c + R @ (0.0, 0.0, 0.015 * k), R @ G.rz(rz), col,
                             material=material))
    return out


# ==================================================================== the kinds

class Kind:
    area = "Meadow"
    leg_h = 1.2
    face = {}
    shoulder = (1.55, 1.8)
    head = (0.0, 3.7, 0.0)
    brows = None
    brow_dy = (0.0, 0.0)

    def build(self, sc, parent, base=None):
        sp = Spud(sc, parent, self, base)
        self.body(sp)
        self.features(sp)
        return sp.finish()

    def features(self, sp):
        dimples(sp)
        eyes(sp, brows=self.brows, brow_dy=self.brow_dy)
        self.mouth(sp)
        arms(sp, self.limb)
        legs(sp, self.limb, self.shoe)
        sprout(sp)
        self.crown(sp)

    def mouth(self, sp):
        mouth_smile(sp)

    def crown(self, sp):
        crown(sp)

    def spots(self, sp, spots, col):
        for pos, R, sz in spots:
            sp.extra(sz, pos, R, col)


class SpudKind(Kind):
    pid, display, rarity = "Spud", "Spud", "Common"
    skin = ("d39a52", "b97a3c", "e8b670")
    limb = "b97a3c"
    shoe = "e8403a"
    face = dict(z=-1.45, eye_y=2.32, eye_dx=0.5, mouth_y=1.55, cheek_dx=0.82)
    shoulder = (1.55, 1.8)
    head = (0.0, 3.7, 0.0)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 2.95, 3.2, 2.9, 2.0, 0.6, (mid, dark, light), core=True)
        sp.extra((2.3, 0.6, 2.1), (0.0, 0.3, 0.0), ori(0, 9, 0), dark)               # narrower bottom
        sp.extra((2.45, 0.8, 2.25), (0.0, 3.2, 0.05), ori(0, -8, 3), light)          # top
        sp.extra((1.45, 0.32, 1.35), (0.06, 3.62, 0.05), ori(0, 14, 3), mid)         # lid
        sp.extra((0.9, 1.0, 1.2), (-1.5, 2.35, 0.55), ori(10, 25, 14), light)        # a knobbly lump
        self.spots(sp, (((0.62, 0.95, -1.47), ori(0, 0, 12), (0.42, 0.34, 0.1)),
                        ((-1.3, 2.75, -0.95), ori(0, 45, -8), (0.36, 0.3, 0.1)),
                        ((1.62, 1.2, 0.2), ori(0, 90, 20), (0.4, 0.32, 0.1))), shade(dark, -0.3))


class TaterTotKind(Kind):
    """Short, wide and crispy: a golden cylinder standing on end."""
    pid, display, rarity = "TaterTot", "Tater Tot", "Common"
    skin = ("eeb23a", "d4922a", "f7cd5c")
    limb = "d4922a"
    shoe = "6b4226"
    face = dict(z=-1.6, eye_y=1.78, eye_dx=0.46, mouth_y=1.08)
    shoulder = (1.55, 1.3)
    head = (0.0, 2.75, 0.0)
    leg_h = 1.0

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.12, 2.62, 3.3, 3.2, 1.9, 0.72, (mid, dark, light), core=True)
        sp.extra((2.4, 0.3, 2.3), (0.0, 0.14, 0.0), ori(0, 22, 0), dark)               # base
        sp.extra((2.5, 0.22, 2.4), (0.0, 2.66, 0.0), ori(0, 22, 0), light)             # flat top
        crisp = shade(dark, -0.12)
        for pos, R, sz, col in (((0.7, 2.82, 0.4), ori(8, 30, 6), (0.55, 0.32, 0.5), crisp),
                                ((-0.55, 2.8, -0.35), ori(-6, 60, -9), (0.5, 0.3, 0.45), "ffd86b"),
                                ((-0.2, 2.78, 0.75), ori(5, 15, 4), (0.45, 0.28, 0.4), crisp),
                                ((1.63, 1.95, -0.3), ori(0, 0, 0), (0.12, 0.4, 0.45), crisp),
                                ((-1.63, 0.75, 0.25), ori(0, 0, 0), (0.12, 0.45, 0.5), crisp),
                                ((0.6, 0.5, -1.62), ori(0, 0, 0), (0.42, 0.34, 0.12), crisp)):
            sp.extra(sz, pos, R, col)                                                 # crispy bits

    def mouth(self, sp):
        h = mouth_smile(sp, width=0.56, cheeks=False)
        # its cheeks sit on the front chamfers, either side of the face
        w, d, front, ch = 3.3, 3.2, 1.9, 0.72
        side = d - 2 * ch
        ax, az = (w - front) / 2, (d - side) / 2
        ln = math.hypot(ax, az)
        n = np.array((az, 0.0, -ax)) / ln                                   # front-right chamfer normal
        mid = np.array(((front / 2 + w / 2) / 2, 1.36, -(d / 2 + side / 2) / 2))
        turn = math.degrees(math.atan2(-n[0], -n[2]))
        for s in (-1, 1):
            c = mid + n * 0.065
            c = np.array((s * c[0], c[1], c[2]))
            sp.plate(h, "Cheek", (0.42, 0.24, 0.1), c, G.ry(s * turn), color=CHEEK)


class YukonGoldKind(Kind):
    """Smooth, shiny, pale gold and egg-shaped, with a little leaf sprouting from its head."""
    pid, display, rarity = "YukonGold", "Yukon Gold", "Uncommon"
    skin = ("f3d77e", "dfbd5c", "fbe9ad")
    limb = "dfbd5c"
    shoe = "3e7bd6"
    face = dict(z=-1.5, eye_y=2.35, eye_dx=0.5, mouth_y=1.58, cheek_dx=0.84)
    shoulder = (1.55, 1.75)
    head = (0.12, 3.88, 0.0)
    leg_h = 1.2

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.3, 2.9, 3.2, 3.0, 2.0, 0.62, (mid, dark, light), core=True)
        sp.extra((2.5, 0.7, 1.6), (0.0, 3.2, 0.0), None, mid)                          # rounded top:
        sp.extra((1.6, 0.72, 2.4), (0.0, 3.2, 0.0), None, light)                       # two crossing slabs
        sp.extra((1.4, 0.3, 1.3), (0.0, 3.68, 0.0), ori(0, 45, 0), light)              # crown of the egg
        sp.extra((2.3, 0.4, 2.1), (0.0, 0.2, 0.0), ori(0, 45, 0), dark)                # bottom
        sp.extra((0.24, 0.5, 0.1), (0.8, 2.6, -1.55), None, "fffaea")                  # shine
        # the leaf it was born with, on the left of its head
        sp.extra((0.24, 0.6, 0.24), (-0.5, 3.95, 0.1), ori(0, 0, 18), LEAF[1])
        sp.extra((0.7, 0.14, 0.45), (-0.85, 4.25, 0.1), ori(0, -15, 32), LEAF[2])


class RedRascalKind(Kind):
    """Round, red and up to something: one brow up and a lopsided grin."""
    pid, display, rarity = "RedRascal", "Red Rascal", "Rare"
    skin = ("d2412f", "b02f22", "e9604c")
    limb = "b02f22"
    shoe = "ffd447"
    face = dict(z=-1.55, eye_y=2.28, eye_dx=0.5, mouth_y=1.45, cheek_dx=0.86)
    shoulder = (1.6, 1.75)
    head = (0.0, 3.5, 0.0)
    leg_h = 1.15
    brows = (-14.0, -10.0)
    brow_dy = (0.16, -0.04)

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.4, 2.8, 3.4, 3.1, 2.1, 0.68, (mid, dark, light), core=True)
        sp.extra((2.6, 0.65, 1.7), (0.0, 3.0, 0.0), ori(0, 0, -3), light)               # round top:
        sp.extra((1.7, 0.67, 2.4), (0.0, 3.0, 0.0), ori(0, 0, -3), mid)                # two crossing slabs
        sp.extra((2.5, 0.5, 2.3), (0.0, 0.27, 0.0), ori(0, 30, 0), dark)
        speck = "f2836c"
        self.spots(sp, (((-0.62, 0.95, -1.57), ori(0, 0, 10), (0.3, 0.26, 0.1)),
                        ((1.0, 2.95, -0.98), ori(0, -45, 0), (0.28, 0.24, 0.1)),
                        ((-1.72, 1.6, 0.17), ori(0, 90, 0), (0.32, 0.28, 0.1))), speck)

    def mouth(self, sp):
        """A wide grin pulled up on one side, one tooth showing."""
        f = self.face
        z, y = f["z"], f["mouth_y"]
        h = sp.holder("Mouth", (0.0, y, z))
        sp.plate(h, "Mouth", (0.86, 0.26, 0.1), (0.04, y, z - 0.04), G.rz(7))
        sp.plate(h, "Mouth", (0.24, 0.2, 0.1), (0.46, y + 0.12, z - 0.028), G.rz(30))
        sp.plate(h, "Tooth", (0.2, 0.13, 0.1), (-0.12, y + 0.05, z - 0.09), G.rz(7), color="ffffff")
        for s in (-1, 1):
            sp.plate(h, "Cheek", (0.42, 0.24, 0.1), (s * f["cheek_dx"], y + 0.4, z - 0.025), color="ffa0a0")


class SweetPotatoKind(Kind):
    """Long and orange with pointed ends, a pink bow on top."""
    pid, display, rarity = "SweetPotato", "Sweet Potato", "Epic"
    skin = ("ec7438", "cf5a28", "f8955a")
    limb = "cf5a28"
    shoe = "ff7eb6"
    face = dict(z=-1.35, eye_y=2.62, eye_dx=0.48, mouth_y=1.86, cheek_dx=0.8)
    shoulder = (1.45, 2.05)
    head = (0.12, 4.05, 0.0)
    leg_h = 1.3

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.85, 3.45, 2.9, 2.7, 1.9, 0.55, (mid, dark, light), core=True)
        sp.extra((2.1, 0.62, 1.4), (0.0, 0.62, 0.0), None, dark)                       # lower taper
        sp.extra((1.4, 0.64, 1.9), (0.0, 0.62, 0.0), None, mid)
        sp.extra((0.9, 0.5, 0.9), (0.0, 0.25, 0.0), ori(0, 45, 0), dark)               # bottom point
        sp.extra((2.15, 0.62, 1.45), (0.04, 3.68, 0.0), ori(0, 0, -5), mid)            # upper taper
        sp.extra((1.45, 0.64, 1.95), (0.04, 3.68, 0.0), ori(0, 0, -5), light)
        sp.extra((0.85, 0.6, 0.85), (0.14, 4.2, 0.0), ori(0, 45, -10), light)          # top point
        # the bow: a knot and two loops, on the left of its head, turned to the front
        bow = ("ff7eb6", "e8559a")
        c = np.array((-1.0, 3.72, -0.55))
        Rb = ori(0, 35, 22)
        sp.extra((0.4, 0.4, 0.34), c, Rb, bow[1])
        for s in (-1, 1):
            Rl = Rb @ G.rz(s * 20)
            sp.extra((0.78, 0.62, 0.28), c + Rb @ (s * 0.5, 0.0, 0.0), Rl, bow[0])

    def mouth(self, sp):
        mouth_smile(sp, width=0.6)


class GoldenSpudKind(SpudKind):
    """Spud cast in solid gold, star glints flashing round it."""
    pid, display, rarity = "GoldenSpud", "Golden Spud", "Legendary"
    skin = ("f5c518", "d9a20c", "ffe066")
    limb = "d9a20c"
    shoe = "ffffff"

    def body(self, sp):
        mid, dark, light = self.skin
        octo(sp, 0.35, 2.95, 3.2, 2.9, 2.0, 0.6, (mid, dark, light), core=True)
        sp.extra((2.3, 0.6, 2.1), (0.0, 0.3, 0.0), ori(0, 9, 0), dark)
        sp.extra((2.45, 0.8, 2.25), (0.0, 3.2, 0.05), ori(0, -8, 3), light)
        sp.extra((1.45, 0.32, 1.35), (0.06, 3.62, 0.05), ori(0, 14, 3), mid)
        sp.extra((0.9, 1.0, 1.2), (-1.5, 2.35, 0.55), ori(10, 25, 14), light)
        sp.extra((0.18, 0.44, 0.1), (0.78, 2.7, -1.5), None, "fff6c9")                 # shine
        # star glints flashing near it
        star(sp, sp.extra, (1.8, 3.4, -0.55), 0.8, "fffbe6", ori(0, -30, 45))
        star(sp, sp.extra, (-1.0, 0.85, -1.52), 0.55, "fffbe6")

    def crown(self, sp):
        crown(sp, cols=("e0a800", "fff1a8", "ffe58a"), jewel="6ff3ff")


MEADOW = [SpudKind(), TaterTotKind(), YukonGoldKind(), RedRascalKind(), SweetPotatoKind(), GoldenSpudKind()]


def build_area(sc, parent, kinds=MEADOW, spacing=6.0, base=None):
    out = []
    for i, k in enumerate(kinds):
        b = (base or CF()) * CF(((i - (len(kinds) - 1) / 2) * spacing, 0.0, 0.0))
        out.append(k.build(sc, parent, b))
    return out


# ==================================================================== posing (previews and clips)

class Pose:
    """World CFrames of every part of one built potato for a level and a set of joint transforms
    (4x4 matrices in each joint's frame)."""

    def __init__(self, model):
        self.model = model
        self.motors = {}
        self.welded = {}
        for n in model.walk():
            for c in n.children:
                if c.kind == "Motor":
                    p = c.p
                    self.motors[id(p["part1"])] = (c.name, p["part0"], p["part1"], p["hinge"])
                elif c.kind == "Weld":
                    self.welded[id(c.p["part1"])] = c.p["part0"]
        self.root = model.p["primary"]
        self.leg_h = model.p["attrs"]["LegHeight"]

    def world(self, X=None, level=10):
        X = X or {}
        out = {id(self.root): (self.root, self.root.p["cf"])}

        def solve(part):
            key = id(part)
            if key in out:
                return out[key][1]
            if key in self.motors:
                name, p0, p1, hinge = self.motors[key]
                w0 = solve(p0)
                C0 = p0.p["cf"].inv() * hinge
                if name == "Body" and level >= 6:
                    C0 = C0 * CF((0.0, self.leg_h, 0.0))
                C1 = p1.p["cf"].inv() * hinge
                T = X.get(name)
                Tcf = CF() if T is None else CF(T[:3, 3], T[:3, :3])
                w = w0 * C0 * Tcf * C1.inv()
            elif key in self.welded:
                p0 = self.welded[key]
                w = solve(p0) * (p0.p["cf"].inv() * part.p["cf"])
            else:
                raise KeyError(part.name)
            out[key] = (part, w)
            return w
        for n in self.model.walk():
            if n.kind == "Part":
                solve(n)
        return out

    def shown(self, part, level):
        """Is this part visible at this level (its feature shown, itself not invisible)?"""
        if part.p["transparency"] >= 0.99:
            return False
        n = part
        while n is not None and n is not self.model:
            if n.name in SHOWN_FROM and n.parent is self.model:
                return visible(n.name, level)
            n = n.parent
        return True


AREAS = {"Meadow": MEADOW}
