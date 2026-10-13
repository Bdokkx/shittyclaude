"""The potatoes' six clips, baked at 30 fps on the shared joint names (one set for all 48 kinds).

  PotatoIdle     2.0 s loop    breathing, a sway, one blink (the Eyes fold flat for two frames)
  PotatoHop      0.8 s loop    a happy hop: squash, spring, arms up, land, squash (from level 6)
  PotatoWave     1.2 s         raises its right arm and waves three times
  PotatoDance    2.4 s loop    four-beat bounce, sway and twist, arms pumping in turn, feet stepping
  PotatoHatch    0.8 s         pops up out of the ground with a twist, overshoots, settles; marker Out
  PotatoLevelUp  0.7 s         crouches, jumps, spins once, lands; marker Top at the peak

Joint frames have model axes (front -Z, +X the potato's right). Conventions used below:
  Body    hinge on the ground under the body: rz(+) leans to its left, rx(-) leans forward
  ArmR    rz(+) raises it out to the side (ArmL mirrored: rz(-)); rx(+) swings it forward
  LegL/R  hinge at the hip: rx(+) swings the leg forward; rz(+-) splays it out
  FootL/R hinge at the ankle: rx(-) points the toes down
  Eyes    rx(90) folds the eye plates flat into a line: a blink
Body, legs and feet all carry the same vertical lift so the whole potato leaves the ground; when
it spins, the legs (on Root) orbit with the body (the hips are always at X = +-HIP_X).
"""
import copy
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(HERE, "..", "..", "..", "folk-valley-animations", "tools"))
import anim as A  # noqa: E402

from . import spuds as S  # noqa: E402
from .roots_anim import MARKER_PROPS, ease, rx, ry, rz, spline, tr  # noqa: E402

FPS = 30
PRIORITY = {"Idle": 0, "Movement": 1, "Action": 2}
TREE = {"Root": ["Body", "LegL", "LegR"],
        "Body": ["Dimples", "Eyes", "Mouth", "ArmL", "ArmR", "Sprout", "Crown"],
        "ArmL": ["HandL"], "ArmR": ["HandR"], "LegL": ["FootL"], "LegR": ["FootR"]}
PARENT = {c: p for p, cs in TREE.items() for c in cs}
JOINTS = list(PARENT)


class Clip:
    def __init__(self, name, length, loop, priority, fn, markers=()):
        self.name, self.length, self.loop, self.priority, self.fn = name, length, loop, priority, fn
        self.markers = list(markers)

    def times(self):
        n = int(round(self.length * FPS))
        return [i / FPS for i in range(n + 1)]

    def bake(self):
        out = []
        for t in self.times():
            X = {}
            self.fn(X, (t % self.length) if (self.loop and t < self.length - 1e-9) else
                    (0.0 if self.loop else t))
            out.append(X)
        return out


# ---------------------------------------------------------------- helpers

def body(X, y=0.0, x=0.0, z=0.0, pitch=0.0, roll=0.0, yaw=0.0):
    X["Body"] = tr(x, y, z) @ ry(yaw) @ rx(pitch) @ rz(roll)


def arm(X, side, raise_=0.0, fwd=0.0, twist=0.0):
    """raise_ > 0 lifts the arm out and up on either side."""
    s = 1.0 if side == "R" else -1.0
    X["Arm" + side] = rz(s * raise_) @ rx(fwd) @ ry(s * twist)


def hand(X, side, flick=0.0, curl=0.0):
    s = 1.0 if side == "R" else -1.0
    X["Hand" + side] = rz(s * flick) @ rx(curl)


def leg(X, side, lift=0.0, swing=0.0, splay=0.0, spin=0.0, step=0.0):
    """lift: the whole potato's vertical lift; spin: the body's turn (the leg orbits with it);
    step: this leg's own lift off the ground."""
    s = 1.0 if side == "R" else -1.0
    hx = s * S.HIP_X
    a = math.radians(spin)
    dx, dz = hx * (math.cos(a) - 1.0), -hx * math.sin(a)
    X["Leg" + side] = tr(dx, lift + step, dz) @ ry(spin) @ rx(swing) @ rz(s * splay)


def foot(X, side, point=0.0, roll=0.0):
    s = 1.0 if side == "R" else -1.0
    X["Foot" + side] = rx(-point) @ rz(s * roll)


def blink(t, at, frames=2):
    """Eyes fold flat for `frames` frames starting at `at` (one frame in, one frame out)."""
    f = t * FPS
    f0 = at * FPS
    if f0 - 1 <= f <= f0 + frames:
        if f < f0:
            return 90.0 * (f - (f0 - 1))
        if f <= f0 + frames - 1:
            return 90.0
        return 90.0 * (f0 + frames - f)
    return 0.0


def wave(t, period, amp, phase=0.0):
    return amp * math.sin(math.tau * t / period + phase)


# ---------------------------------------------------------------- PotatoIdle 2.0 s loop

ID_LEN = 2.0


def idle(X, t):
    br = 0.5 - 0.5 * math.cos(math.tau * t / ID_LEN)          # 0 -> 1 -> 0 once a loop (one breath)
    body(X, y=0.07 * br, roll=wave(t, ID_LEN, 3.0), yaw=wave(t, ID_LEN, 4.0, 1.2), pitch=-1.5 * br)
    for sd in ("L", "R"):
        k = 1.0 if sd == "R" else -1.0
        arm(X, sd, raise_=4.0 * br + wave(t, ID_LEN, 1.5, 0.5 * k), fwd=wave(t, ID_LEN, 4.0, 1.0 + k))
        hand(X, sd, flick=wave(t, ID_LEN / 2, 4.0, k))
    X["Eyes"] = rx(blink(t, 1.4))
    X["Sprout"] = rz(wave(t, ID_LEN / 2, 5.0, 0.6)) @ rx(wave(t, ID_LEN, 3.0))
    X["Crown"] = rz(wave(t, ID_LEN, 1.5, 2.0))


# ---------------------------------------------------------------- PotatoHop 0.8 s loop

HOP_LEN = 0.8
HOP_UP, HOP_DOWN, HOP_H, SQUASH = 0.1, 0.62, 1.5, 0.22


def hop_lift(t):
    if HOP_UP <= t <= HOP_DOWN:
        u = (t - HOP_UP) / (HOP_DOWN - HOP_UP)
        return 4 * HOP_H * u * (1 - u)
    if t < HOP_UP:                                   # rising out of the squash
        return -SQUASH * (1 - ease(0.0, 1.0, t, 0.0, HOP_UP, "out"))
    return -SQUASH * ease(0.0, 1.0, t, HOP_DOWN, HOP_LEN, "out")


def hop(X, t):
    y = hop_lift(t)
    air = max(0.0, y) / HOP_H                        # 0 on the ground, 1 at the top
    sq = max(0.0, -y) / SQUASH                       # 1 at the deepest squash
    body(X, y=y, pitch=-6.0 * sq + 4.0 * air, roll=wave(t, HOP_LEN, 3.0))
    for sd in ("L", "R"):
        arm(X, sd, raise_=-8.0 * sq + 70.0 * air, fwd=-14.0 * sq + 10.0 * air)
        hand(X, sd, flick=20.0 * air)
        leg(X, sd, lift=max(0.0, y), swing=12.0 * air, splay=9.0 * sq)
        foot(X, sd, point=35.0 * air)
    X["Sprout"] = rx(-18.0 * air + 14.0 * sq) @ rz(wave(t, HOP_LEN, 6.0))
    X["Crown"] = tr(0.0, 0.12 * sq - 0.06 * air, 0.0) @ rz(wave(t, HOP_LEN, 3.0, 1.0))


# ---------------------------------------------------------------- PotatoWave 1.2 s

WV_LEN = 1.2


def wave_clip(X, t):
    up = ease(0.0, 1.0, t, 0.0, 0.22, "out") * (1.0 - ease(0.0, 1.0, t, 0.98, 1.2))
    w = math.sin(math.tau * 3 * (t - 0.22) / 0.76) if 0.22 <= t <= 0.98 else 0.0
    body(X, roll=5.0 * up, yaw=-8.0 * up, y=0.06 * up + 0.04 * abs(w) * up)
    arm(X, "R", raise_=112.0 * up + 22.0 * w * up, fwd=24.0 * up)
    hand(X, "R", flick=26.0 * w * up)
    arm(X, "L", raise_=6.0 * up)
    X["Eyes"] = rx(blink(t, 0.3))
    X["Sprout"] = rz(-4.0 * up + 4.0 * w * up)


# ---------------------------------------------------------------- PotatoDance 2.4 s loop

DN_LEN = 2.4
BEAT = DN_LEN / 4


def dance(X, t):
    b = (t % BEAT) / BEAT                               # 0..1 within the beat
    bounce = math.sin(math.pi * b) ** 2                 # up between beats, down on them
    side = math.sin(math.tau * t / (2 * BEAT))          # one sway left-right every two beats
    body(X, y=0.22 * bounce, x=0.18 * side, roll=-7.0 * side, yaw=16.0 * math.sin(math.tau * t / DN_LEN),
         pitch=-3.0 * bounce)
    pump = math.sin(math.tau * t / (2 * BEAT))
    arm(X, "R", raise_=75.0 + 55.0 * pump, fwd=10.0)
    arm(X, "L", raise_=75.0 - 55.0 * pump, fwd=10.0)
    hand(X, "R", flick=-20.0 * pump)
    hand(X, "L", flick=20.0 * pump)
    beat_no = int(t // BEAT) % 4
    for sd, on in (("L", (0, 2)), ("R", (1, 3))):
        stepping = beat_no in on
        st = math.sin(math.pi * b) if stepping else 0.0
        leg(X, sd, lift=0.0, step=0.35 * st, swing=18.0 * st, splay=4.0)
        foot(X, sd, point=20.0 * st)
    X["Eyes"] = rx(blink(t, 1.55))
    X["Sprout"] = rz(14.0 * math.sin(math.tau * t / BEAT + 0.7))
    X["Crown"] = tr(0.0, 0.08 * math.sin(math.tau * t / BEAT + 0.9), 0.0) @ rz(4.0 * side)


# ---------------------------------------------------------------- PotatoHatch 0.8 s (marker Out)

HT_LEN = 0.8
HT_OUT = 0.2
UNDER = -7.0                 # deep enough to hide the tallest potato, legs and crown and all


def hatch(X, t):
    if t < HT_OUT:
        y = ease(UNDER, 0.0, t, 0.0, HT_OUT, "out")
    elif t < 0.34:
        y = ease(0.0, 0.7, t, HT_OUT, 0.34, "out")
    elif t < 0.5:
        y = ease(0.7, -0.18, t, 0.34, 0.5, "in")
    else:
        y = ease(-0.18, 0.0, t, 0.5, 0.66)
    spin = ease(-40.0, 0.0, t, 0.0, 0.42, "out")
    tuck = 1.0 - ease(0.0, 1.0, t, 0.16, 0.34, "out")
    pop = math.sin(math.pi * min(1.0, max(0.0, (t - 0.28) / 0.32)))
    body(X, y=y, yaw=spin, roll=wave(t, 0.4, 4.0) * (1 - t / HT_LEN))
    for sd in ("L", "R"):
        arm(X, sd, raise_=-34.0 * tuck + 26.0 * pop, fwd=-10.0 * tuck)
        hand(X, sd, flick=18.0 * pop)
        leg(X, sd, lift=y if y > 0 else y, spin=spin, splay=6.0 * max(0.0, -y) / 0.18 if y < 0 else 0.0)
        foot(X, sd, point=30.0 * max(0.0, y) / 0.7)
    X["Sprout"] = rx(-25.0 * tuck + 16.0 * pop) @ rz(10.0 * pop)
    X["Eyes"] = rx(90.0 * tuck if t < 0.34 else blink(t, 0.58))
    X["Crown"] = tr(0.0, -0.1 * pop, 0.0)


# ---------------------------------------------------------------- PotatoLevelUp 0.7 s (marker Top)

LU_LEN = 0.7
LU_TOP = 0.34
LU_H = 2.2


def levelup(X, t):
    if t < 0.08:
        y = -0.25 * ease(0.0, 1.0, t, 0.0, 0.08)
    elif t < LU_TOP:
        y = ease(-0.25, LU_H, t, 0.08, LU_TOP, "out")
    elif t < 0.56:
        y = ease(LU_H, 0.0, t, LU_TOP, 0.56, "in")
    else:
        y = -0.2 * math.sin(math.pi * (t - 0.56) / (LU_LEN - 0.56))
    spin = ease(0.0, 360.0, t, 0.1, 0.52)
    air = max(0.0, y) / LU_H
    sq = max(0.0, -y) / 0.25
    body(X, y=y, yaw=spin, pitch=-5.0 * sq)
    for sd in ("L", "R"):
        arm(X, sd, raise_=-10.0 * sq + 95.0 * air, fwd=8.0 * air)
        hand(X, sd, flick=25.0 * air)
        leg(X, sd, lift=max(0.0, y), spin=spin, swing=10.0 * air, splay=8.0 * sq)
        foot(X, sd, point=40.0 * air)
    X["Sprout"] = rx(-20.0 * air + 12.0 * sq) @ rz(8.0 * math.sin(t * 30))
    X["Crown"] = tr(0.0, -0.08 * air + 0.1 * sq, 0.0)
    X["Eyes"] = rx(blink(t, 0.6))


CLIPS = [Clip("PotatoIdle", ID_LEN, True, PRIORITY["Idle"], idle),
         Clip("PotatoHop", HOP_LEN, True, PRIORITY["Movement"], hop),
         Clip("PotatoWave", WV_LEN, False, PRIORITY["Action"], wave_clip),
         Clip("PotatoDance", DN_LEN, True, PRIORITY["Movement"], dance),
         Clip("PotatoHatch", HT_LEN, False, PRIORITY["Action"], hatch, [(HT_OUT, "Out")]),
         Clip("PotatoLevelUp", LU_LEN, False, PRIORITY["Action"], levelup, [(LU_TOP, "Top")])]


# ---------------------------------------------------------------- KeyframeSequences (rbxtool JSON)

def moving(frames):
    """Joints that ever leave their rest pose in these frames."""
    out = set()
    for X in frames:
        for j, m in X.items():
            if not np.allclose(m, np.eye(4), atol=1e-6):
                out.add(j)
    return out


def write(clip, frames):
    props = copy.deepcopy(A.KS_PROPS)
    props["Loop"] = {"Bool": bool(clip.loop)}
    props["Priority"] = {"Enum": int(clip.priority)}
    props["AuthoredHipHeight"] = {"Float32": 0.0}
    times = clip.times()
    used = moving(frames)
    # a joint that moves needs its parents in the pose tree too
    need = set(used)
    for j in list(used):
        p = PARENT.get(j)
        while p and p != "Root":
            need.add(p)
            p = PARENT.get(p)
    marks = {}
    for t, name in clip.markers:
        i = int(np.argmin([abs(t - x) for x in times]))
        marks.setdefault(i, []).append(name)
    kfs = []
    for i, X in enumerate(frames):
        def pose(b):
            kids = [pose(c) for c in TREE.get(b, []) if c in need]
            if b == "Root":
                return A._pose(b, (0, 0, 0), np.array([1.0, 0, 0, 0]), kids, weight=0.0)
            m = X.get(b, np.eye(4))
            return A._pose(b, m[:3, 3], A.mat_to_quat(m[:3, :3]), kids)
        kp = copy.deepcopy(A.KF_PROPS)
        kp["Time"] = {"Float32": round(float(times[i]), 5)}
        kids = [pose("Root")]
        for name in marks.get(i, []):
            kids.append({"class": "KeyframeMarker", "name": name, "ref": A._ref(), "props": copy.deepcopy(MARKER_PROPS),
                         "children": []})
        kfs.append({"class": "Keyframe", "name": "Keyframe", "ref": A._ref(), "props": kp, "children": kids})
    return {"class": "KeyframeSequence", "name": clip.name, "ref": A._ref(), "props": props, "children": kfs}


def bake_all():
    out = [(c, c.bake()) for c in CLIPS]
    folder = {"class": "Folder", "name": "PotatoAnimations", "ref": A._ref(),
              "props": {"Attributes": {"Attributes": {}}, "Tags": {"Tags": []}},
              "children": [write(c, fr) for c, fr in out]}
    return out, folder
