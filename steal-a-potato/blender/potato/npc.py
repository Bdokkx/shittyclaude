"""Farmer Spud, the quest NPC (PotatoKit.QuestNpc), and his clips (PotatoKit.QuestNpcAnimations).

About 11.5 studs tall: a big potato head under a straw hat with a red band, bushy white brows and
moustache (a wheat stalk poking out of it), rosy cheeks, a red neckerchief, a cream shirt with
rolled sleeves, blue overalls with gold buttons, a pencil in the bib pocket and a patch on the
knee, brown boots, hands with fingers, a hoe in his left hand.

Rig: every Motor6D drives an invisible holder part at its hinge that carries the joint's own name
(so a Pose, the Motor6D and its Part1 all share one name); the group's bricks are the holder's
children, welded to it.
  Waist      Root -> Waist (torso)       ShoulderL / ShoulderR   Waist -> ShoulderL / ShoulderR (upper arms)
  Neck       Waist -> Neck (head)        ElbowL / ElbowR         ShoulderL -> ElbowL ... (forearm and hand)
  Brow       Neck -> Brow                HipL / HipR             Root -> HipL / HipR (legs and boots)
  Moustache  Neck -> Moustache           Hat                     Neck -> Hat
  Eyes       Neck -> Eyes  (rx 90 folds the eyes into a line: a blink)
The hoe is in ElbowL's group. Joint frames have model axes (front -Z, +X his right).
"""
import math

import numpy as np

import spsgeo as G
from spsgeo import CF

from .bricks import ori, shade
from .rig import Clip, Rig
from .roots_anim import ease, rx, ry, rz, spline, tr

SKIN = ("d39a52", "b97a3c", "e8b670")
STRAW = ("e8c25a", "d9ae45", "f2d27a")
WHITE = ("f4f4f2", "e2e2e0")
DENIM = ("3e5c99", "34508a", "5a7cc0")
SHIRT = ("f0dcb4", "e0c89c")
RED = "c9402a"
SCARF = "d7372c"
GOLD = "ffd447"
BOOT = ("6b4226", "3a2a1e", "7a4e2d")
INK = "1e1a22"


def build(sc, parent, base=None):
    r = Rig(sc, parent, "QuestNpc", base)

    # -------------------------------------------------------------- legs (on Root)
    for s, side in ((-1, "L"), (1, "R")):
        x = s * 0.78
        leg = r.group("Hip" + side, "Root", (x, 3.5, 0.0), "Hip" + side)
        r.brick(leg, "Trouser", (1.15, 2.6, 1.25), (x, 2.25, 0.0), None, DENIM[0])
        r.brick(leg, "Cuff", (1.3, 0.36, 1.4), (x, 1.1, 0.0), None, DENIM[2])
        r.brick(leg, "Sole", (1.3, 0.3, 1.9), (x + s * 0.03, 0.15, -0.2), None, BOOT[1])
        r.brick(leg, "Boot", (1.16, 0.78, 1.36), (x + s * 0.03, 0.68, 0.0), None, BOOT[0])
        r.brick(leg, "Toe", (1.14, 0.56, 0.62), (x + s * 0.03, 0.5, -0.86), None, BOOT[2])
        if side == "L":                         # a patch on the left knee, cross-stitched
            r.brick(leg, "Patch", (0.66, 0.62, 0.12), (x, 2.15, -0.66), G.rz(6), RED)
            r.plate(leg, "Stitch", (0.62, 0.08, 0.1), (x, 2.15, -0.73), G.rz(51), SHIRT[0])
            r.plate(leg, "Stitch", (0.62, 0.08, 0.1), (x, 2.15, -0.735), G.rz(-39), SHIRT[0])

    # -------------------------------------------------------------- torso
    t = r.group("Waist", "Root", (0.0, 3.6, 0.0), "Waist")
    r.brick(t, "Overalls", (2.9, 0.95, 2.0), (0.0, 3.95, 0.0), None, DENIM[0])
    r.brick(t, "Shirt", (2.7, 2.7, 2.0), (0.0, 5.3, 0.05), None, SHIRT[0])
    r.brick(t, "Bib", (2.3, 2.35, 0.5), (0.0, 5.15, -1.05), None, DENIM[0])
    r.brick(t, "Bib", (1.9, 1.9, 0.3), (0.0, 5.0, -1.34), None, DENIM[0])          # the round of the belly
    r.brick(t, "Bib", (2.95, 1.24, 2.06), (0.0, 4.55, 0.0), None, DENIM[1])         # the waistband
    r.brick(t, "Pocket", (0.82, 0.62, 0.1), (0.0, 5.5, -1.53), None, DENIM[1])
    r.brick(t, "Pencil", (0.13, 0.55, 0.13), (0.22, 5.95, -1.52), G.rz(-8), GOLD)
    r.brick(t, "Pencil", (0.13, 0.14, 0.13), (0.255, 6.27, -1.52), G.rz(-8), "ff9fb0")
    for s in (-1, 1):
        x = s * 0.72
        r.brick(t, "Strap", (0.46, 0.6, 0.26), (x, 6.42, -1.0), None, DENIM[0])
        r.brick(t, "Strap", (0.44, 0.26, 2.12), (x, 6.74, 0.0), None, DENIM[0])
        r.brick(t, "Strap", (0.46, 1.6, 0.26), (x, 5.95, 1.1), G.rz(s * 14), DENIM[0])
        r.brick(t, "Button", (0.34, 0.34, 0.16), (x, 6.25, -1.33), G.rz(45), GOLD)
    r.brick(t, "Collar", (2.0, 0.36, 1.62), (0.0, 6.795, 0.0), None, SHIRT[0])
    for s in (-1, 1):
        r.brick(t, "Collar", (0.6, 0.42, 0.14), (s * 0.48, 6.62, -0.86), G.rz(-s * 30), SHIRT[1])
    r.brick(t, "Neckerchief", (0.62, 0.5, 0.46), (0.0, 6.74, -0.9), G.rz(45), SCARF)
    r.brick(t, "Neckerchief", (1.12, 1.12, 0.2), (0.0, 6.28, -1.42), G.rz(45), SCARF)

    # -------------------------------------------------------------- arms
    for s, side in ((-1, "L"), (1, "R")):
        sh = np.array((s * 1.72, 6.25, 0.0))
        R = G.rz(s * 10.0)
        down = R @ np.array((0.0, -1.0, 0.0))
        arm = r.group("Shoulder" + side, t, tuple(sh), "Shoulder" + side)
        r.brick(arm, "Shoulder", (1.08, 0.62, 1.08), sh + (s * 0.05, 0.05, 0.0), None, SHIRT[0])
        r.brick(arm, "Sleeve", (0.96, 1.7, 0.96), sh + down * 0.8, R, SHIRT[0])
        el = sh + down * 1.62
        fa = r.group("Elbow" + side, arm, tuple(el), "Elbow" + side)
        r.brick(fa, "Cuff", (1.06, 0.42, 1.06), el + down * 0.12, R, SHIRT[1])
        r.brick(fa, "Forearm", (0.76, 1.15, 0.76), el + down * 0.75, R, SKIN[0])
        hc = el + down * 1.52
        r.brick(fa, "Hand", (0.96, 0.78, 0.66), hc, R, SKIN[0])
        for i, fx in enumerate((-0.3, 0.0, 0.3)):                 # three fingers curled to the front
            r.brick(fa, "Finger", (0.26, 0.48, 0.3), hc + R @ (fx, -0.38, -0.2), R @ G.rx(-25), SKIN[2 if i == 1 else 0])
        r.brick(fa, "Thumb", (0.28, 0.5, 0.32), hc + R @ (-s * 0.5, 0.05, -0.18), R @ G.rz(s * 35), SKIN[0])
        if side == "L":                                          # the hoe, held upright, blade up
            hx, hz = hc[0], hc[2] - 0.05
            r.brick(fa, "Hoe", (0.24, 8.6, 0.24), (hx, 4.5, hz), None, "9a6238")
            r.brick(fa, "Hoe", (0.34, 0.5, 0.34), (hx, 8.85, hz), None, BOOT[0])
            r.brick(fa, "Hoe", (0.18, 0.62, 0.18), (hx, 9.2, hz - 0.18), G.rx(-35), "8e89a0")
            r.brick(fa, "Hoe", (0.17, 0.17, 0.62), (hx, 9.42, hz - 0.62), None, "8e89a0")
            r.brick(fa, "Hoe", (1.05, 0.72, 0.12), (hx, 9.05, hz - 0.92), None, "8e89a0")
            r.brick(fa, "Hoe", (1.06, 0.16, 0.14), (hx, 8.66, hz - 0.92), None, "d4d8e2")

    # -------------------------------------------------------------- head
    h = r.group("Neck", t, (0.0, 6.75, 0.0), "Neck")
    mid, dark, light = SKIN
    # an octagonal potato 4 wide and 3.4 deep in the middle, rounding off above and below
    w, d, front, ch = 4.0, 3.4, 2.6, 0.62
    side = d - 2 * ch
    y0, y1 = 7.6, 9.6
    c = np.array((0.0, (y0 + y1) / 2, 0.0))
    hh = y1 - y0
    r.brick(h, "Skin", (front, hh, d), c, None, mid)
    r.brick(h, "Skin", (w, hh * 0.985, side), c, None, dark)
    ax, az = (w - front) / 2, (d - side) / 2
    ln = math.hypot(ax, az)
    nrm = np.array((az, ax)) / ln
    mx, mz = (front / 2 + w / 2) / 2, (d / 2 + side / 2) / 2
    dist = mx * nrm[0] + mz * nrm[1]
    a = math.degrees(math.atan2(nrm[1], nrm[0]))
    for s, kh in ((-1, 0.97), (1, 0.955)):
        r.brick(h, "Skin", (2 * dist, hh * kh, ln), c, G.ry(s * a), light)
    r.brick(h, "Skin", (3.4, 0.72, 2.5), (0.0, 7.32, 0.0), None, dark)                 # jowls
    r.brick(h, "Skin", (2.5, 0.74, 3.2), (0.0, 7.32, 0.0), None, mid)
    r.brick(h, "Skin", (2.5, 0.4, 2.2), (0.0, 6.95, 0.0), ori(0, 10, 0), dark)         # chin
    r.brick(h, "Skin", (3.5, 0.72, 2.7), (0.0, 9.88, 0.0), ori(0, 6, 0), mid)          # crown of the head
    r.brick(h, "Skin", (2.7, 0.74, 3.3), (0.0, 9.88, 0.0), ori(0, 6, 0), light)
    r.brick(h, "Skin", (2.4, 0.3, 2.3), (0.0, 10.28, 0.0), ori(0, 40, 0), mid)
    r.brick(h, "Spot", (0.42, 0.34, 0.1), (-1.33, 9.3, -1.3), ori(0, 45, 12), shade(dark, -0.3))
    r.brick(h, "Spot", (0.34, 0.3, 0.1), (1.55, 7.9, -1.18), ori(0, -45, -6), shade(dark, -0.3))
    fz = -d / 2
    # nose: a round potato nose, rosy at the tip
    r.brick(h, "Nose", (0.96, 0.76, 0.6), (0.0, 8.55, fz - 0.27), None, "c98349")
    r.brick(h, "Nose", (0.82, 0.6, 0.36), (0.0, 8.52, fz - 0.6), None, "d08a52")
    r.brick(h, "Nose", (0.6, 0.82, 0.37), (0.0, 8.53, fz - 0.6), None, "d08a52")
    r.plate(h, "Nose", (0.28, 0.2, 0.1), (0.2, 8.7, fz - 0.8), color="f0b08e")
    for s in (-1, 1):
        r.plate(h, "Cheek", (0.6, 0.4, 0.1), (s * 1.12, 8.38, fz - 0.03), color="ff9aa8")
    r.plate(h, "Mouth", (0.74, 0.18, 0.1), (0.0, 7.5, fz + 0.06), color=INK)
    r.plate(h, "Mouth", (0.3, 0.12, 0.1), (0.0, 7.4, fz + 0.055), color="ff6b8a")
    # eyes (their own joint, so they can blink)
    e = r.group("Eyes", h, (0.0, 9.02, fz), "Eyes")
    for s in (1, -1):
        r.plate(e, "Eye", (0.44, 0.62, 0.1), (s * 0.64, 9.02, fz - 0.04))
        r.plate(e, "Glint", (0.18, 0.18, 0.1), (s * 0.64 + 0.08, 9.2, fz - 0.09), color="ffffff")
    # bushy white brows
    b = r.group("Brow", h, (0.0, 9.62, fz), "Brow")
    for s in (1, -1):
        Rb = G.rz(-s * 10)
        r.brick(b, "Brow", (1.06, 0.38, 0.46), (s * 0.68, 9.64, fz - 0.16), Rb, WHITE[0])
        r.brick(b, "Brow", (0.52, 0.32, 0.4), (s * 1.22, 9.48, fz - 0.14), G.rz(-s * 32), WHITE[1])
    # the moustache, and the wheat stalk he chews
    mo = r.group("Moustache", h, (0.0, 8.05, fz - 0.3), "Moustache")
    r.brick(mo, "Moustache", (1.46, 0.58, 0.62), (0.0, 8.03, fz - 0.4), None, WHITE[0])
    for s in (1, -1):
        r.brick(mo, "Moustache", (1.12, 0.52, 0.56), (s * 0.96, 7.93, fz - 0.33), G.rz(-s * 18), WHITE[1])
        r.brick(mo, "Moustache", (0.64, 0.44, 0.5), (s * 1.6, 7.62, fz - 0.27), G.rz(-s * 42), WHITE[0])
    r.brick(mo, "Wheat", (0.12, 0.12, 1.5), (-0.95, 7.5, fz - 0.75), ori(-12, -32, 0), STRAW[1])
    r.brick(mo, "Wheat", (0.24, 0.24, 0.5), (-1.32, 7.6, fz - 1.33), ori(-12, -32, 0), STRAW[2])

    # -------------------------------------------------------------- the straw hat, worn back and a little aslant
    hat = r.group("Hat", h, (0.0, 10.2, 0.0), "Hat")
    Rh = ori(-6, 0, 5)
    o = np.array((0.0, 10.2, 0.0))

    def hb(name, size, local, col, Rl=None):
        r.brick(hat, name, size, o + Rh @ np.asarray(local, float), Rh @ (np.eye(3) if Rl is None else Rl), col)
    hb("Brim", (5.6, 0.22, 3.8), (0, 0.12, 0), STRAW[0])
    hb("Brim", (3.8, 0.24, 5.6), (0, 0.12, 0), STRAW[0])
    hb("Brim", (4.8, 0.26, 4.8), (0, 0.12, 0), STRAW[1], G.ry(45))
    hb("Crown", (3.0, 1.15, 2.2), (0, 0.8, 0), STRAW[0])
    hb("Crown", (2.2, 1.17, 3.0), (0, 0.8, 0), STRAW[2])
    hb("Crown", (2.6, 1.19, 2.6), (0, 0.8, 0), STRAW[1], G.ry(45))
    hb("Crown", (1.9, 0.18, 1.5), (0, 1.43, 0), STRAW[1])
    hb("Band", (3.06, 0.34, 2.26), (0, 0.45, 0), RED)
    hb("Band", (2.26, 0.36, 3.06), (0, 0.45, 0), RED)
    hb("Band", (2.66, 0.38, 2.66), (0, 0.45, 0), shade(RED, -0.1), G.ry(45))
    for (lx, lz, yaw, col) in ((2.75, -0.6, 20, STRAW[2]), (-2.6, 1.0, -35, STRAW[2]), (0.9, 2.75, 70, STRAW[0])):
        hb("Straw", (0.7, 0.1, 0.18), (lx, 0.1, lz), col, G.ry(yaw) @ G.rz(8))

    # -------------------------------------------------------------- where players talk to him
    r.part("Prompt", (4.0, 4.0, 2.0), (0.0, 6.0, -3.4), None, "ffffff", material="SmoothPlastic",
           transparency=1.0, shadow=False, anchored=True)
    m = r.finish()
    sc.attr(m, "Height", 11.6)
    return m


# ==================================================================== the clips

JOINTS = ("Waist", "Neck", "ShoulderL", "ShoulderR", "ElbowL", "ElbowR", "HipL", "HipR", "Hat", "Brow",
          "Moustache", "Eyes")


def blink(t, at, frames=2, fps=30):
    f, f0 = t * fps, at * fps
    if f0 - 1 <= f <= f0 + frames:
        if f < f0:
            return 90.0 * (f - (f0 - 1))
        if f <= f0 + frames - 1:
            return 90.0
        return 90.0 * (f0 + frames - f)
    return 0.0


def arms(X, raise_r=0.0, raise_l=0.0, fwd_r=0.0, fwd_l=0.0, el_r=0.0, el_l=0.0, el_rz_r=0.0, el_rz_l=0.0):
    """raise > 0 lifts the arm out to its side; fwd > 0 swings it forward; el > 0 bends the elbow
    forward; el_rz > 0 folds the forearm in towards the head when the arm is up."""
    X["ShoulderR"] = rz(raise_r) @ rx(fwd_r)
    X["ShoulderL"] = rz(-raise_l) @ rx(fwd_l)
    X["ElbowR"] = rz(el_rz_r) @ rx(el_r)
    X["ElbowL"] = rz(-el_rz_l) @ rx(el_l)


ID_LEN = 4.0


def idle(X, t):
    br = 0.5 - 0.5 * math.cos(math.tau * t / 2.0)                       # two breaths a loop
    look = spline([(0.0, 0.0), (0.6, 0.0), (1.3, 22.0), (2.1, 22.0), (2.7, -16.0), (3.4, -16.0), (4.0, 0.0)],
                  t, ID_LEN)
    X["Waist"] = tr(0, 0.05 * br, 0) @ ry(look * 0.15) @ rx(-1.2 * br) @ rz(1.2 * math.sin(math.tau * t / ID_LEN))
    X["Neck"] = ry(look) @ rx(-2.0 + 2.5 * math.sin(math.tau * t / ID_LEN + 1.0)) @ rz(-look * 0.12)
    arms(X, raise_r=2.5 * br, raise_l=2.5 * br, fwd_r=2 * math.sin(math.tau * t / ID_LEN),
         fwd_l=-2 * math.sin(math.tau * t / ID_LEN), el_r=6 + 3 * br, el_l=5 + 2 * br)
    X["Brow"] = tr(0, 0.07 * abs(look) / 22.0, 0)
    X["Eyes"] = rx(blink(t, 0.9) + blink(t, 3.1))
    tw = math.exp(-((t - 2.4) / 0.12) ** 2)                              # one twitch of the moustache
    X["Moustache"] = tr(0, 0.04 * tw, 0) @ rz(6.0 * tw * math.sin(t * 60))
    X["Hat"] = rz(0.8 * math.sin(math.tau * t / ID_LEN + 0.4))


WV_LEN = 1.6


def wave(X, t):
    up = ease(0.0, 1.0, t, 0.0, 0.3, "out") * (1.0 - ease(0.0, 1.0, t, 1.3, 1.6))
    w = math.sin(math.tau * 3 * (t - 0.3) / 1.0) if 0.3 <= t <= 1.3 else 0.0
    X["Waist"] = rz(4.0 * up) @ ry(-6.0 * up) @ tr(0, 0.04 * up, 0)
    X["Neck"] = rz(-6.0 * up) @ rx(3.0 * up) @ ry(-4.0 * up)
    arms(X, raise_r=128.0 * up, fwd_r=18.0 * up, el_rz_r=(48.0 + 26.0 * w) * up, raise_l=5.0 * up, el_l=6.0 * up)
    X["Brow"] = tr(0, 0.1 * up, 0)
    X["Moustache"] = tr(0, 0.05 * up, 0) @ rz(3.0 * w * up)
    X["Eyes"] = rx(blink(t, 0.85))
    X["Hat"] = rz(-2.0 * w * up)


TK_LEN = 2.0


def talk(X, t):
    p = math.tau * t
    X["Neck"] = rx(-3.0 + 5.0 * math.sin(p / 1.0 * 2)) @ ry(7.0 * math.sin(p / 2.0)) @ rz(2.0 * math.sin(p / 1.0))
    X["Waist"] = rz(1.5 * math.sin(p / 2.0)) @ rx(-1.0)
    arms(X, raise_r=14.0 + 6.0 * math.sin(p + 1.0), fwd_r=26.0 + 16.0 * math.sin(p * 2 / 2.0 + 0.5),
         el_r=48.0 + 24.0 * math.sin(p * 2 / 2.0), raise_l=7.0 + 2.0 * math.sin(p + 2.5),
         fwd_l=5.0 + 4.0 * math.sin(p + 2.0), el_l=12.0 + 6.0 * math.sin(p + 1.6))
    X["Moustache"] = tr(0, 0.045 * abs(math.sin(p / 0.5)), 0) @ rz(3.0 * math.sin(p / 0.5 + 0.7))
    X["Brow"] = tr(0, 0.05 * math.sin(p + 1.0), 0)
    X["Eyes"] = rx(blink(t, 1.3))


CH_LEN = 1.6
HOPS = ((0.25, 0.65), (0.85, 1.25))


def cheer_lift(t):
    for a, b in HOPS:
        if a <= t <= b:
            u = (t - a) / (b - a)
            return 0.9 * 4 * u * (1 - u)
        if a - 0.15 <= t < a:                      # crouch before each hop
            return -0.18 * math.sin(math.pi * (t - (a - 0.15)) / 0.15) if t > a - 0.15 else 0.0
    if 1.25 < t <= 1.45:                           # land and settle
        return -0.15 * math.sin(math.pi * (t - 1.25) / 0.2)
    return 0.0


def cheer(X, t):
    up = ease(0.0, 1.0, t, 0.0, 0.25, "out") * (1.0 - ease(0.0, 1.0, t, 1.3, 1.6))
    y = cheer_lift(t)
    air = max(0.0, y) / 0.9
    pump = math.sin(math.tau * t / 0.6)
    X["Waist"] = tr(0, y, 0) @ rx(3.0 * air)
    for side, s in (("L", -1), ("R", 1)):
        X["Hip" + side] = tr(0, max(0.0, y), 0) @ rx(s * 8.0 * air)
    arms(X, raise_r=(150.0 + 10.0 * pump) * up, raise_l=(150.0 - 10.0 * pump) * up, el_rz_r=14.0 * up,
         el_rz_l=14.0 * up, fwd_r=6.0 * up, fwd_l=6.0 * up)
    X["Neck"] = rx(10.0 * up) @ rz(4.0 * math.sin(math.tau * t / 0.8))
    X["Hat"] = tr(0, 0.28 * air, 0) @ rx(-6.0 * air)
    X["Brow"] = tr(0, 0.12 * up, 0)
    X["Moustache"] = tr(0, 0.06 * up, 0) @ rz(6.0 * math.sin(math.tau * t / 0.4) * up)
    X["Eyes"] = rx(90.0 if 0.35 <= t <= 0.55 or 0.95 <= t <= 1.15 else 0.0)


CLIPS = [Clip("Idle", ID_LEN, True, 0, idle),
         Clip("Wave", WV_LEN, False, 2, wave),
         Clip("Talk", TK_LEN, True, 1, talk),
         Clip("Cheer", CH_LEN, False, 2, cheer)]
