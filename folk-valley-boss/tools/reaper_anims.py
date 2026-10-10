"""The Grim Reaper's animations.

    python tools/reaper_anims.py <rig.json> <out.json>     (rbxtool JSON: a Folder of KeyframeSequences)

Idle, Walk, Run (loops); Stomp, Swing, Spin, Throw, Roar (attacks / taunt);
Hurt and Defeat. Markers: Footstep (Walk, Run), Impact (Stomp), Hit (Swing),
SpinStart / SpinEnd (Spin), Release / Catch (Throw), Roar, ScytheDrop and
Collapsed (Defeat). Priorities: Idle = Idle, Walk / Run = Movement, attacks =
Action, Hurt = Action2, Defeat = Action4.

The scythe attacks keep the blade at player height (about 3 studs up) where it
counts: the Swing sweeps it round the front, the Spin round every side and the
Throw sends it whirling out and back like a boomerang.
"""
import json
import math
import sys

import numpy as np

import banim as B
from banim import E, T, inv, rot_x, Clip

A = B.A
IDLE, MOVEMENT, ACTION, ACTION2, ACTION4 = 0, 1, 2, 3, 5


def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def smoother(t):
    t = max(0.0, min(1.0, t))
    return t * t * t * (t * (6 * t - 15) + 10)


def lerp(a, b, t):
    return a + (b - a) * t


def bump(t, t0, t1):
    """0 -> 1 -> 0 over [t0, t1]."""
    return math.sin(math.pi * smooth((t - t0) / (t1 - t0))) if t1 > t0 else 0.0


class VCurve:
    """A smooth curve through (t, vector) keys."""

    def __init__(self, keys, loop=False, length=None):
        keys = sorted(keys, key=lambda k: k[0])
        self.track = A.Track([k[0] for k in keys], [list(k[1]) for k in keys], [[1, 0, 0, 0]] * len(keys))
        self.loop = loop
        self.length = length or keys[-1][0]

    def __call__(self, t):
        p, _ = A.sample(self.track, [t], self.loop, self.length)
        return np.array(p[0])


def curve1(keys):
    c = VCurve([(t, (v, 0.0, 0.0)) for t, v in keys])
    return lambda t: float(c(t)[0])


def dir_az(az, el):
    """Model-space direction: azimuth from straight ahead (-Z) round to the reaper's left
    (+90 = left, -90 = right, 180 = behind), elevation up from level."""
    a, e = math.radians(az), math.radians(el)
    return np.array([-math.sin(a) * math.cos(e), math.sin(e), -math.cos(a) * math.cos(e)])


def tangent_az(az):
    """Level direction of travel for increasing azimuth (sweeping right to left)."""
    a = math.radians(az)
    return np.array([-math.cos(a), 0.0, math.sin(a)])


def rot_between(a, b):
    a = a / np.linalg.norm(a)
    b = b / np.linalg.norm(b)
    v = np.cross(a, b)
    c = float(np.dot(a, b))
    m = np.eye(4)
    if c < -0.99999:
        axis = np.cross(a, (1.0, 0, 0))
        if np.linalg.norm(axis) < 1e-6:
            axis = np.cross(a, (0, 1.0, 0))
        axis /= np.linalg.norm(axis)
        m[:3, :3] = 2 * np.outer(axis, axis) - np.eye(3)
        return m
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    m[:3, :3] = np.eye(3) + K + K @ K / (1 + c)
    return m


def rot_axis(axis, deg):
    m = np.eye(4)
    m[:3, :3] = A.quat_to_mat(A.axis_quat(axis, deg))
    return m


def blend_xf(a, b, k):
    """Between two rigid transforms: slerp the turn, lerp the shift."""
    if k <= 0:
        return a.copy()
    if k >= 1:
        return b.copy()
    m = np.eye(4)
    m[:3, :3] = A.quat_to_mat(A.slerp(A.mat_to_quat(a[:3, :3]), A.mat_to_quat(b[:3, :3]), k))
    m[:3, 3] = a[:3, 3] * (1 - k) + b[:3, 3] * k
    return m


# ---------------------------------------------------------------- shared pieces

BASE = {
    "UpperTorso": (-6, 0, 0),
    "Head": (-5, 0, 0),
    "RightUpperArm": (10, 0, 3),
    "RightLowerArm": (16, 0, 0),
    "RightHand": (0, 0, 0),
    "LeftUpperArm": (8, 0, -5),
    "LeftLowerArm": (24, 0, 0),
    "LeftHand": (-6, 0, 0),
    "Cape": (-3, 0, 0),
}
REST = dict(BASE, LowerTorso=(0, 0, 0, 0, 0, 0), Jaw=(0, 0, 0))
HOLD_TILT = (-4, 0, -2)


class Ctx:
    def __init__(self, rig):
        self.rig = rig
        self.ankle_rest = {s: rig.pivot[s + "Foot"].copy() for s in ("Right", "Left")}
        self.grip_rest = rig.pivot["Scythe"].copy()
        self.scythe_rest = rig.rest["Scythe"].copy()
        parts = {p["Name"]: p for p in rig.parts}
        # the scythe's balance point (between the shaft's middle and the blade): it whirls round this
        self.scythe_mid = (np.array(parts["Scythe"]["Center"]) * 0.4 + np.array(parts["ScytheBlade"]["Center"]) * 0.6)
        # the corners of each foot (toe and heel, sole and top), rest model space
        self.sole = {}
        for s in ("Right", "Left"):
            f = parts[s + "Foot"]
            c, h = np.array(f["Center"]), np.array(f["Size"]) / 2
            self.sole[s] = [np.array([c[0] + dx * h[0] * 0.8, c[1] + dy * (h[1] - 0.06), c[2] + dz * h[2] * 0.92, 1.0])
                            for dx in (-1, 1) for dy in (-1, 1) for dz in (-1, 1)]

    def grip_point(self, W):
        return (W[self.rig.parent["Scythe"]] @ self.rig.C0["Scythe"])[:3, 3]

    def scythe_world(self, X):
        return self.rig.fk(X)["Scythe"]

    def scythe_upright(self, X, tilt=HOLD_TILT):
        """Keep the scythe standing in the fist, tilted by `tilt` (model-space Euler) about the grip."""
        W = self.rig.fk(X)
        g = self.grip_point(W)
        target = T(g) @ E(*tilt) @ T(-self.grip_rest) @ self.scythe_rest
        B.scythe_to(self.rig, X, W, target)

    def scythe_dir(self, X, shaft, blade, slide=0.0):
        """Scythe in the fist with its shaft pointing along `shaft` and the blade along `blade`."""
        rig = self.rig
        W = rig.fk(X)
        g = self.grip_point(W)
        y = np.asarray(shaft, dtype=float)
        y = y / np.linalg.norm(y)
        b = np.asarray(blade, dtype=float)
        z = -(b - y * b.dot(y))                       # the blade points along the scythe's -Z
        if np.linalg.norm(z) < 1e-6:
            z = np.cross(y, (1.0, 0, 0))
        z /= np.linalg.norm(z)
        x = np.cross(y, z)
        R = np.eye(4)
        R[:3, 0], R[:3, 1], R[:3, 2] = x, y, z
        target = T(g + y * slide) @ R @ T(-self.grip_rest) @ self.scythe_rest
        B.scythe_to(rig, X, W, target)

    def aim_arm(self, X, side, direction, elbow=10.0, twist=0.0):
        """Turn the upper arm so the line shoulder -> grip (wrist for the left) points along
        `direction` (model space), the elbow bent a little."""
        rig = self.rig
        up, lo, hand = side + "UpperArm", side + "LowerArm", side + "Hand"
        X[lo] = rot_x(elbow)
        X2 = dict(X)
        X2[up] = np.eye(4)
        W = rig.fk(X2)
        J = rig.joint_world(W, up)
        tip = self.grip_point(W) if side == "Right" else rig.joint_world(W, hand)[:3, 3]
        Ji = inv(J)
        v0 = (Ji @ np.array([*tip, 1.0]))[:3]
        d = Ji[:3, :3] @ np.asarray(direction, dtype=float)
        X[up] = rot_axis(d / np.linalg.norm(d), twist) @ rot_between(v0, d)

    def plant(self, X, extra=None, targets=None, pitches=None):
        """Leg IK for both feet (rest spots unless given), the ankle raised if a pitched foot
        would dig its toes or heel into the ground, and the robe pushed out of the legs' way."""
        rig = self.rig
        hips = {}
        for s in ("Right", "Left"):
            tgt = np.array(targets[s] if targets and s in targets else self.ankle_rest[s], dtype=float)
            pitch = pitches.get(s, 0.0) if pitches else 0.0
            for _ in range(3):
                hips[s] = B.leg_ik(rig, X, rig.fk(X), s, tgt, pitch)
                Wf = rig.fk(X)[s + "Foot"] @ inv(rig.rest[s + "Foot"])
                low = min((Wf @ p)[1] for p in self.sole[s])
                if low >= -0.02:
                    break
                tgt = tgt + (0.0, 0.02 - low, 0.0)
        B.robe_from_legs(X, hips, extra)

    def swing_pose(self, X, az, el, wrist=15.0, elbow=10.0):
        """Right arm aimed at (az, el), the shaft cocked `wrist` degrees above the arm and the
        blade leading the sweep (pointing towards increasing azimuth)."""
        self.aim_arm(X, "Right", dir_az(az, el), elbow=elbow)
        self.scythe_dir(X, dir_az(az, el + wrist), tangent_az(az))

    def mix_arm(self, X, Xa, k, bones=("RightUpperArm", "RightLowerArm", "RightHand", "Scythe")):
        """Blend the aimed arm and scythe in Xa over the keyed ones in X by k."""
        for b in bones:
            if b in Xa:
                X[b] = blend_xf(X.get(b, np.eye(4)), Xa[b], k)


def yaw_body(X, deg):
    """Turn the whole body (the Root joint) about the vertical."""
    m = X.get("LowerTorso", np.eye(4))
    r = np.eye(4)
    r[:3, :3] = m[:3, :3]
    X["LowerTorso"] = T(m[:3, 3]) @ E(0, deg, 0) @ r


# ---------------------------------------------------------------- loops

def idle(ctx):
    """Two slow breaths, a look round with a creepy head tilt, a beckoning claw and a
    dry chuckle."""
    L = 3.4
    c = Clip("ReaperIdle", L, True, IDLE, BASE)
    n = 34
    for i in range(n + 1):
        t = L * i / n
        ph = t / L * math.tau
        br = 0.5 - 0.5 * math.cos(2 * ph)                         # two breaths
        look = 20 * math.sin(ph)
        tilt = 9 * math.sin(ph - 0.9)
        beck = bump(t, 1.85, 2.95)
        curl = math.sin(math.pi * smooth((t - 1.95) / 0.42)) + math.sin(math.pi * smooth((t - 2.37) / 0.42))
        c.key(t, LowerTorso=(0, 3 * math.sin(ph), 0, 0, -0.06 + 0.12 * br, 0),
              UpperTorso=(-7 + 3 * br, -0.35 * look, 1.5 * math.sin(ph)),
              Head=(-5 + 2 * br - 2 * beck, look, tilt),
              RightUpperArm=(10 + 2 * br, 0, 3 + 2 * br), RightLowerArm=(16 - 2 * br, 0, 0),
              LeftUpperArm=(8 + 3 * br + 26 * beck, 0, -5 - 2 * br - 6 * beck),
              LeftLowerArm=(24 + 2 * br + 34 * beck, 0, 0),
              LeftHand=(-6 - 34 * curl * beck, 0, 0),
              Cape=(-3 - 2 * br + 2 * math.sin(ph), 0, 1.5 * math.cos(ph)))
    for t, j in ((0.0, 0), (2.4, 0), (2.55, -10), (2.68, -2), (2.81, -10), (2.94, -2), (3.1, 0), (3.4, 0)):
        c.key(t, Jaw=(j, 0, 0))

    def frame(t, X, _):
        s = math.sin(t / L * math.tau)
        ctx.plant(X, {"front": 1.5 * s, "back": -1.5 * s, "right": 1.2 * math.cos(t / L * math.tau), "left": 1.2 * s})
        ctx.scythe_upright(X, (-4 + 2 * math.sin(2 * t / L * math.tau), 0, -2))
    c.frame = frame
    return c


def locomotion(ctx, name, length, stance, stride, lift, bob, lean, scythe_tilt, arm, cape, pitch_swing,
               marker_times, priority=MOVEMENT):
    c = Clip(name, length, True, priority, BASE)

    def foot(u):
        """Ankle offset (z, y, pitch) at phase u (0 = heel strike, foot forward)."""
        if u < stance:
            s = u / stance
            return lerp(-stride, stride, s), 0.0, 0.0
        s = (u - stance) / (1 - stance)
        z = lerp(stride, -stride, smooth(s))
        y = lift * math.sin(math.pi * s) ** 0.8
        p = lerp(-pitch_swing, pitch_swing * 0.6, s)
        return z, y, p
    for k in range(9):
        t = length * k / 8
        ph = t / length * math.tau
        c.key(t, LowerTorso=(lean[0] * 0.3, 5 * math.cos(ph), 0, 0, -bob[0] + bob[1] * (0.5 - 0.5 * math.cos(2 * ph)), 0),
              UpperTorso=(lean[0], -7 * math.cos(ph), 3 * math.sin(ph)),
              Head=(lean[1], 5 * math.cos(ph), -1.5 * math.sin(ph)),
              RightUpperArm=(arm[0] - arm[1] * math.cos(ph), 0, arm[2]),
              RightLowerArm=(arm[3], 0, 0),
              LeftUpperArm=(arm[4] + arm[5] * math.cos(ph), 0, -arm[6]),
              LeftLowerArm=(arm[7] + 6 * math.cos(ph), 0, 0),
              Cape=(cape[0] + cape[1] * math.sin(2 * ph), 0, 2 * math.sin(ph)))
    for t in marker_times:
        c.marker(t, "Footstep")

    def frame(t, X, _):
        u = (t / length) % 1.0
        targets, pitches = {}, {}
        for s, off in (("Right", 0.0), ("Left", 0.5)):
            z, y, p = foot((u + off) % 1.0)
            r = ctx.ankle_rest[s]
            targets[s] = np.array([r[0], r[1] + y, r[2] + z])
            pitches[s] = p
        ctx.plant(X, None, targets, pitches)
        ph = t / length * math.tau
        ctx.scythe_upright(X, (scythe_tilt[0] + 3 * math.cos(ph), scythe_tilt[1], scythe_tilt[2]))
    c.frame = frame
    return c


def walk(ctx):
    # about 7 studs a second at speed 1
    return locomotion(ctx, "ReaperWalk", 1.5, 0.56, 3.0, 1.7, (0.25, 0.42), (-12, 6), (14, 0, -6),
                      (4, 9, 4, 22, 6, 16, 6, 26), (-8, 4), 18, (0.0, 0.75))


def run(ctx):
    # about 18 studs a second at speed 1; the scythe held up and out so its blade shows over the shoulder
    return locomotion(ctx, "ReaperRun", 0.9, 0.42, 3.4, 2.7, (0.45, 0.9), (-22, 14), (20, 0, -24),
                      (-10, 12, 16, 30, 42, 24, 8, 34), (-26, 9), 32, (0.0, 0.45))


# ---------------------------------------------------------------- attacks

def stomp(ctx):
    """Knee high, a lean back, then the foot slams down (Impact): a shockwave ring in game."""
    c = Clip("ReaperStomp", 2.0, False, ACTION, BASE)
    c.pose(0.0, REST)
    c.pose(0.55, {"LowerTorso": (8, 4, 7, -0.55, 0.45, 0.1), "UpperTorso": (12, 6, -4), "Head": (-2, -4, 0),
                  "RightUpperArm": (42, 0, 26), "RightLowerArm": (46, 0, 0),
                  "LeftUpperArm": (20, 0, -60), "LeftLowerArm": (32, 0, 0), "LeftHand": (-22, 0, 0),
                  "Cape": (-10, 0, 0), "Jaw": (-8, 0, 0)})
    c.pose(0.76, {"LowerTorso": (10, 4, 8, -0.6, 0.6, 0.15), "UpperTorso": (16, 6, -4), "Head": (-4, -4, 0),
                  "RightUpperArm": (48, 0, 30), "RightLowerArm": (50, 0, 0),
                  "LeftUpperArm": (24, 0, -66), "LeftLowerArm": (36, 0, 0), "LeftHand": (-26, 0, 0),
                  "Cape": (-14, 0, 0), "Jaw": (-12, 0, 0)})
    c.pose(0.9, {"LowerTorso": (-6, 0, 0, -0.1, -1.1, -0.1), "UpperTorso": (-18, 0, 0), "Head": (12, 0, 0),
                 "RightUpperArm": (6, 0, 40), "RightLowerArm": (20, 0, 0),
                 "LeftUpperArm": (4, 0, -50), "LeftLowerArm": (20, 0, 0), "LeftHand": (10, 0, 0),
                 "Cape": (-38, 0, 0), "Jaw": (-34, 0, 0)})
    c.pose(1.15, {"LowerTorso": (-3, 0, 0, 0, -0.75, 0), "UpperTorso": (-14, 0, 0), "Head": (8, 0, 0),
                  "RightUpperArm": (8, 0, 30), "RightLowerArm": (22, 0, 0),
                  "LeftUpperArm": (6, 0, -36), "LeftLowerArm": (22, 0, 0), "LeftHand": (4, 0, 0),
                  "Cape": (-18, 0, 0), "Jaw": (-20, 0, 0)})
    c.pose(1.5, {"LowerTorso": (0, 0, 0, 0, -0.2, 0), "UpperTorso": (-8, 0, 0), "Head": (-4, 0, 0),
                 "RightUpperArm": BASE["RightUpperArm"], "RightLowerArm": BASE["RightLowerArm"],
                 "LeftUpperArm": BASE["LeftUpperArm"], "LeftLowerArm": BASE["LeftLowerArm"], "LeftHand": BASE["LeftHand"],
                 "Cape": (-6, 0, 0), "Jaw": (-4, 0, 0)})
    c.pose(2.0, REST)
    c.marker(0.9, "Impact")
    r = ctx.ankle_rest["Right"]
    foot = VCurve([(0.0, r), (0.3, r + (0.1, 2.2, -1.0)), (0.55, r + (0.2, 5.4, -2.6)), (0.76, r + (0.2, 5.9, -2.8)),
                   (0.84, r + (0.15, 2.6, -2.4)), (0.9, r + (0.1, 0.0, -2.1)), (1.5, r + (0.1, 0.0, -2.1)),
                   (1.72, r + (0.05, 1.1, -1.0)), (2.0, r)])
    pitch = curve1([(0.0, 0.0), (0.5, 26.0), (0.76, 30.0), (0.88, 6.0), (0.9, 0.0), (1.5, 0.0), (1.72, 12.0), (2.0, 0.0)])

    def frame(t, X, _):
        flare = 26 * math.exp(-max(0.0, t - 0.9) / 0.18) if t >= 0.88 else 0.0
        ctx.plant(X, {"front": flare, "back": flare, "left": flare, "right": flare},
                  {"Right": foot(t)}, {"Right": pitch(t)})
        up = smooth((t - 0.2) / 0.5) * (1 - smooth((t - 1.2) / 0.7))
        ctx.scythe_upright(X, (lerp(-4, 18, up), 0, -2 - 22 * smooth((t - 0.8) / 0.12) * (1 - smooth((t - 1.2) / 0.7))))
    c.frame = frame
    return c


def swing(ctx):
    """A wind-up to the right, then one huge sweep across the front at knee-to-chest height
    of a player (Hit when the blade passes straight ahead), follow-through, recover."""
    c = Clip("ReaperSwing", 1.8, False, ACTION, BASE)
    c.pose(0.0, REST)
    c.pose(0.45, {"LowerTorso": (2, -18, 0, 0, -0.45, 0.35), "UpperTorso": (0, -36, 3), "Head": (-8, 28, 0),
                  "LeftUpperArm": (56, 0, -10), "LeftLowerArm": (30, 0, 0), "LeftHand": (-24, 0, 0),
                  "Jaw": (-8, 0, 0), "Cape": (-6, 0, -8)})
    c.pose(0.6, {"LowerTorso": (6, 8, 0, 0, -0.85, -0.15), "UpperTorso": (-12, 14, -2), "Head": (-2, -8, 0),
                 "LeftUpperArm": (10, 0, -40), "LeftLowerArm": (20, 0, 0), "LeftHand": (0, 0, 0),
                 "Jaw": (-30, 0, 0), "Cape": (-18, 0, 10)})
    c.pose(0.8, {"LowerTorso": (4, 22, 0, 0, -0.75, -0.35), "UpperTorso": (-10, 46, -4), "Head": (-4, -30, 0),
                 "LeftUpperArm": (-14, 0, -42), "LeftLowerArm": (24, 0, 0), "LeftHand": (6, 0, 0),
                 "Jaw": (-18, 0, 0), "Cape": (-14, 0, 14)})
    c.pose(1.15, {"LowerTorso": (2, 12, 0, 0, -0.35, -0.15), "UpperTorso": (-8, 24, -2), "Head": (-6, -14, 0),
                  "LeftUpperArm": (2, 0, -16), "LeftLowerArm": (24, 0, 0), "LeftHand": (-4, 0, 0),
                  "Jaw": (-6, 0, 0), "Cape": (-6, 0, 6)})
    c.pose(1.8, REST)
    c.marker(0.6, "Hit")
    az = curve1([(0.1, -82.0), (0.45, -142.0), (0.53, -100.0), (0.6, 0.0), (0.68, 62.0), (0.82, 96.0),
                 (1.05, 72.0), (1.32, -40.0), (1.6, -80.0)])
    el = curve1([(0.1, -76.0), (0.45, -4.0), (0.53, -20.0), (0.6, -38.0), (0.68, -34.0), (0.82, -14.0),
                 (1.05, 2.0), (1.32, 16.0), (1.6, 0.0)])

    def frame(t, X, _):
        flare = 16 * bump(t, 0.45, 1.1)
        ctx.plant(X, {"front": flare * 0.6, "back": flare * 0.6, "left": flare, "right": flare})
        k = smooth((t - 0.08) / 0.27) * (1 - smooth((t - 1.2) / 0.5))
        ctx.scythe_upright(X)
        if k > 1e-3:
            Xa = dict(X)
            ctx.swing_pose(Xa, az(t), el(t))
            ctx.mix_arm(X, Xa, k)
    c.frame = frame
    return c


def spin(ctx):
    """Rises a little off the ground, scythe out low, and whirls round twice: the blade
    sweeps every side (SpinStart to SpinEnd)."""
    L = 2.6
    c = Clip("ReaperSpin", L, False, ACTION, BASE)
    arms_out = {"LeftUpperArm": (6, 0, -76), "LeftLowerArm": (12, 0, 0), "LeftHand": (0, 0, -16)}
    c.pose(0.0, REST)
    c.pose(0.4, dict(arms_out, LowerTorso=(6, 0, 0, 0, -0.8, 0), UpperTorso=(-14, -24, 0), Head=(-6, 18, 0),
                     Cape=(-12, 0, 0), Jaw=(-8, 0, 0)))
    c.pose(0.62, dict(arms_out, LowerTorso=(0, 0, 0, 0, 0.6, 0), UpperTorso=(-6, 0, 0), Head=(-2, 0, 0),
                      Cape=(-50, 0, 0), Jaw=(-26, 0, 0)))
    c.pose(1.8, dict(arms_out, LowerTorso=(0, 0, 0, 0, 0.8, 0), UpperTorso=(-6, 0, 0), Head=(-2, 0, 0),
                     Cape=(-56, 0, 0), Jaw=(-22, 0, 0)))
    c.pose(2.08, dict(arms_out, LowerTorso=(4, 0, 0, 0, -0.55, 0), UpperTorso=(-14, 8, 0), Head=(-10, -6, 0),
                      Cape=(-20, 0, 0), Jaw=(-8, 0, 0)))
    c.pose(L, REST)
    c.marker(0.45, "SpinStart")
    c.marker(2.0, "SpinEnd")

    def yaw(t):
        if t < 0.4:
            return -35 * smooth(t / 0.4)
        if t < 2.0:
            return -35 + 755 * smoother((t - 0.4) / 1.6)
        return 720.0

    float_up = curve1([(0.0, 0.0), (0.42, 0.0), (0.62, 1.1), (1.8, 1.2), (2.02, 0.0), (L, 0.0)])

    def frame(t, X, _):
        w = yaw(t)
        yaw_body(X, w)
        up = float_up(t)
        R = E(0, w, 0)
        targets, pitches = {}, {}
        for s in ("Right", "Left"):
            p = (R @ np.array([*ctx.ankle_rest[s], 1.0]))[:3]
            targets[s] = p + (0, up * 0.9, 0)
            pitches[s] = -24 * up
        on = smooth((t - 0.4) / 0.25) * (1 - smooth((t - 1.85) / 0.35))
        ctx.plant(X, {"front": 30 * on, "back": 30 * on, "left": 34 * on, "right": 34 * on}, targets, pitches)
        k = smooth((t - 0.15) / 0.3) * (1 - smooth((t - 2.0) / 0.45))
        ctx.scythe_upright(X)
        if k > 1e-3:
            Xa = dict(X)
            ctx.swing_pose(Xa, w - 92, -42 + 8 * (1 - on), wrist=14)
            ctx.mix_arm(X, Xa, k)
    c.frame = frame
    c.cloth_lag = 0.06
    return c


def throw(ctx):
    """Winds up and hurls the scythe: it whirls flat out in front at player height, loops
    round like a boomerang and flies back into the fist (Release, Catch)."""
    L = 3.0
    c = Clip("ReaperThrow", L, False, ACTION, BASE)
    c.pose(0.0, REST)
    c.pose(0.45, {"LowerTorso": (0, -20, 0, 0, -0.5, 0.35), "UpperTorso": (2, -48, 4), "Head": (-6, 36, 0),
                  "LeftUpperArm": (70, 10, -8), "LeftLowerArm": (10, 0, 0), "LeftHand": (-28, 0, 0),
                  "Cape": (-6, 0, -8), "Jaw": (-4, 0, 0)})
    c.pose(0.62, {"LowerTorso": (4, 10, 0, 0, -0.75, -0.3), "UpperTorso": (-14, 26, -2), "Head": (-4, -14, 0),
                  "LeftUpperArm": (26, 0, -34), "LeftLowerArm": (20, 0, 0), "LeftHand": (0, 0, 0),
                  "Cape": (-20, 0, 8), "Jaw": (-28, 0, 0)})
    c.pose(0.9, {"LowerTorso": (2, 10, 0, 0, -0.45, -0.2), "UpperTorso": (-10, 22, -2), "Head": (-2, -12, 0),
                 "LeftUpperArm": (40, 0, -10), "LeftLowerArm": (16, 0, 0), "LeftHand": (-16, 0, 0),
                 "Cape": (-10, 0, 4), "Jaw": (-16, 0, 0)})
    for t, j in ((1.1, -6), (1.25, -22), (1.38, -6), (1.52, -22), (1.66, -6)):
        c.key(t, Jaw=(j, 0, 0))
    c.pose(1.75, {"LowerTorso": (0, 0, 0, 0, -0.25, 0), "UpperTorso": (-8, 0, 0), "Head": (-4, 4, 0),
                  "LeftUpperArm": (20, 0, -10), "LeftLowerArm": (30, 0, 0), "LeftHand": (0, 0, 0), "Cape": (-6, 0, 0)})
    c.pose(2.2, {"LowerTorso": (-4, -6, 0, 0, -0.55, 0.35), "UpperTorso": (6, -10, 0), "Head": (-8, 6, 0),
                 "LeftUpperArm": BASE["LeftUpperArm"], "LeftLowerArm": BASE["LeftLowerArm"], "LeftHand": BASE["LeftHand"],
                 "Cape": (-16, 0, 0), "Jaw": (-14, 0, 0)})
    c.pose(2.45, {"LowerTorso": (0, -4, 0, 0, -0.3, 0.1), "UpperTorso": (-8, -6, 0), "Head": (-4, 4, 0), "Jaw": (-4, 0, 0),
                  "Cape": (-8, 0, 0)})
    c.pose(L, REST)
    c.marker(0.62, "Release")
    c.marker(2.2, "Catch")
    az = curve1([(0.1, -82.0), (0.45, -150.0), (0.55, -100.0), (0.62, -8.0), (0.78, 30.0), (1.0, 4.0), (1.5, -18.0),
                 (2.1, -24.0), (2.24, -40.0), (2.5, -62.0), (2.8, -80.0)])
    el = curve1([(0.1, -76.0), (0.45, -6.0), (0.55, -12.0), (0.62, -22.0), (0.78, -36.0), (1.0, -26.0), (1.5, -18.0),
                 (2.1, -16.0), (2.24, -22.0), (2.5, 8.0), (2.8, -6.0)])
    T0, T1 = 0.62, 2.2
    path_keys = [(0.84, (8.0, 3.6, -14.0)), (1.08, (6.0, 3.4, -26.0)), (1.34, (-3.0, 3.4, -31.0)),
                 (1.6, (-10.0, 3.5, -23.0)), (1.86, (-7.0, 4.2, -14.0))]
    st = {}

    def held(X, t):
        """X with the arm aimed for moment t and the scythe in the fist."""
        Xa = dict(X)
        ctx.swing_pose(Xa, az(t), el(t), wrist=10)
        return Xa

    def mid_of(world):
        return (world @ inv(ctx.scythe_rest) @ np.array([*ctx.scythe_mid, 1.0]))[:3]

    def frame(t, X, _):
        ctx.plant(X, {"front": 8 * bump(t, 0.4, 1.0), "back": 4 * bump(t, 2.1, 2.6), "left": 0, "right": 0})
        k = smooth((t - 0.08) / 0.25) * (1 - smooth((t - 2.42) / 0.5))
        ctx.scythe_upright(X)
        if k <= 1e-3:
            return
        ctx.mix_arm(X, held(X, t), k)
        if t <= T0 or t > T1:
            if t <= T0:
                st["release"] = ctx.scythe_world(X)
            return
        # in flight: whirling flat round its balance point along the boomerang path, from
        # where it left the hand to where the hand will be at the catch
        catch = ctx.scythe_world(held(X, T1))
        path = VCurve([(T0, mid_of(st["release"]))] + path_keys + [(T1, mid_of(catch))])
        spin_deg = 900.0 * (t - T0)
        flight = T(path(t)) @ E(0, spin_deg, 0) @ E(0, 0, -90) @ T(-ctx.scythe_mid) @ ctx.scythe_rest
        world = blend_xf(st["release"], flight, smooth((t - T0) / 0.12))
        kout = smooth((t - (T1 - 0.16)) / 0.16)
        if kout > 0:
            world = blend_xf(world, ctx.scythe_world(X), kout)
        B.scythe_to(ctx.rig, X, ctx.rig.fk(X), world)
    c.frame = frame
    return c


def roar(ctx):
    c = Clip("ReaperRoar", 2.6, False, ACTION, BASE)
    c.pose(0.0, REST)
    c.pose(0.45, {"LowerTorso": (8, 0, 0, 0, -0.8, 0), "UpperTorso": (-24, 0, 0), "Head": (-12, 0, 0),
                  "RightUpperArm": (30, 0, -6), "RightLowerArm": (60, 0, 0), "LeftUpperArm": (30, 0, 6),
                  "LeftLowerArm": (64, 0, 0), "LeftHand": (-20, 0, 0), "Cape": (-6, 0, 0), "Jaw": (-4, 0, 0)})
    c.pose(0.8, {"LowerTorso": (-4, 0, 0, 0, 0.8, 0), "UpperTorso": (16, 0, 0), "Head": (22, 0, 0),
                 "RightUpperArm": (14, 0, 128), "RightLowerArm": (16, 0, 0), "LeftUpperArm": (22, 0, -88),
                 "LeftLowerArm": (12, 0, 0), "LeftHand": (-30, 0, 0), "Cape": (-44, 0, 0), "Jaw": (-40, 0, 0)})
    c.pose(1.75, {"LowerTorso": (-4, 0, 0, 0, 0.9, 0), "UpperTorso": (18, 0, 0), "Head": (24, 0, 0),
                  "RightUpperArm": (16, 0, 132), "RightLowerArm": (14, 0, 0), "LeftUpperArm": (24, 0, -92),
                  "LeftLowerArm": (12, 0, 0), "LeftHand": (-34, 0, 0), "Cape": (-50, 0, 0)})
    for t, j in ((0.95, -22), (1.08, -40), (1.21, -20), (1.34, -40), (1.47, -20), (1.6, -40), (1.75, -30)):
        c.key(t, Jaw=(j, 0, 0))
    c.pose(2.6, REST)
    c.marker(0.8, "Roar")

    def frame(t, X, _):
        f = 22 * bump(t, 0.6, 2.2)
        shake = 2.5 * math.sin(t * 55) * bump(t, 0.8, 1.8)
        X["UpperTorso"] = X["UpperTorso"] @ E(0, shake, shake * 0.5)
        ctx.plant(X, {"front": f, "back": f * 0.8, "left": f, "right": f})
        ctx.scythe_upright(X)
    c.frame = frame
    return c


def hurt(ctx):
    c = Clip("ReaperHurt", 0.8, False, ACTION2, BASE)
    c.pose(0.0, REST)
    c.pose(0.12, {"LowerTorso": (-6, 0, 3, 0, -0.35, 0.45), "UpperTorso": (22, 6, 4), "Head": (26, -8, 8),
                  "RightUpperArm": (-4, 0, 26), "RightLowerArm": (8, 0, 0), "LeftUpperArm": (-6, 0, -32),
                  "LeftLowerArm": (10, 0, 0), "LeftHand": (-30, 0, 0), "Cape": (-10, 0, 0), "Jaw": (-26, 0, 0)})
    c.pose(0.35, {"LowerTorso": (-2, 0, 1, 0, -0.2, 0.2), "UpperTorso": (4, 2, 1), "Head": (4, -2, 2),
                  "RightUpperArm": (6, 0, 10), "RightLowerArm": (14, 0, 0), "LeftUpperArm": (4, 0, -14),
                  "LeftLowerArm": (20, 0, 0), "LeftHand": (-10, 0, 0), "Cape": (-6, 0, 0), "Jaw": (-10, 0, 0)})
    c.pose(0.8, REST)

    def frame(t, X, _):
        ctx.plant(X)
        ctx.scythe_upright(X, (-4 - 10 * bump(t, 0.0, 0.5), 0, -2))
    c.frame = frame
    return c


def defeat(ctx):
    """Staggers, drops to its knees, lets the scythe slip and slumps (ScytheDrop, Collapsed)."""
    L = 3.4
    c = Clip("ReaperDefeat", L, False, ACTION4, BASE)
    c.pose(0.0, REST)
    c.pose(0.3, {"LowerTorso": (-6, 0, 0, 0, -0.3, 0.5), "UpperTorso": (22, 0, 4), "Head": (26, 0, 6),
                 "RightUpperArm": (-6, 0, 30), "RightLowerArm": (10, 0, 0), "LeftUpperArm": (-8, 0, -34),
                 "LeftLowerArm": (10, 0, 0), "LeftHand": (-30, 0, 0), "Cape": (-10, 0, 0), "Jaw": (-30, 0, 0)})
    c.pose(0.9, {"LowerTorso": (8, 6, -4, 0.2, -1.6, -0.2), "UpperTorso": (-26, 4, -6), "Head": (-14, 8, -4),
                 "RightUpperArm": (20, 0, 18), "RightLowerArm": (30, 0, 0), "LeftUpperArm": (30, 0, -10),
                 "LeftLowerArm": (40, 0, 0), "LeftHand": (-10, 0, 0), "Cape": (-6, 0, 0), "Jaw": (-14, 0, 0)})
    c.pose(1.45, {"LowerTorso": (10, 0, 0, 0, -3.5, 0.6), "UpperTorso": (-28, 0, 0), "Head": (-14, 0, 0),
                  "RightUpperArm": (16, 0, 14), "RightLowerArm": (26, 0, 0), "LeftUpperArm": (18, 0, -14),
                  "LeftLowerArm": (26, 0, 0), "LeftHand": (0, 0, 0), "Cape": (-16, 0, 0), "Jaw": (-20, 0, 0)})
    c.pose(2.3, {"LowerTorso": (14, 0, 0, 0, -3.7, 0.7), "UpperTorso": (-42, 0, 4), "Head": (-28, 0, 10),
                 "RightUpperArm": (22, 0, 10), "RightLowerArm": (30, 0, 0), "LeftUpperArm": (24, 0, -10),
                 "LeftLowerArm": (30, 0, 0), "LeftHand": (10, 0, 0), "Cape": (-4, 0, 0), "Jaw": (-22, 0, 0)})
    c.pose(L, {"LowerTorso": (16, 0, 0, 0, -3.8, 0.7), "UpperTorso": (-46, 0, 4), "Head": (-32, 0, 12),
               "RightUpperArm": (24, 0, 8), "RightLowerArm": (32, 0, 0), "LeftUpperArm": (26, 0, -8),
               "LeftLowerArm": (32, 0, 0), "LeftHand": (12, 0, 0), "Cape": (-2, 0, 0), "Jaw": (-24, 0, 0)})
    c.marker(1.6, "ScytheDrop")
    c.marker(2.4, "Collapsed")
    knee_targets = {s: VCurve([(0.0, ctx.ankle_rest[s]), (0.9, ctx.ankle_rest[s] + (0, 0, 0.5)),
                               (1.45, ctx.ankle_rest[s] + (0.1 * (1 if s == "Right" else -1), -0.55, 3.4)),
                               (L, ctx.ankle_rest[s] + (0.1 * (1 if s == "Right" else -1), -0.6, 3.5))])
                    for s in ("Right", "Left")}
    pitch = curve1([(0.0, 0.0), (0.9, -10.0), (1.45, -160.0), (L, -165.0)])
    rest_mid = np.array([4.78, 11.0, -2.0])
    drop_path = VCurve([(0.95, (6.4, 10.0, -1.0)), (1.3, (7.4, 5.0, -2.2)), (1.6, (7.8, 0.35, -3.0)),
                        (1.75, (7.9, 0.75, -3.1)), (1.9, (8.0, 0.35, -3.2)), (L, (8.0, 0.35, -3.2))])
    held = {}

    def frame(t, X, _):
        ctx.plant(X, {"front": 8 * smooth((t - 1.0) / 0.5), "back": -4, "left": 10 * smooth((t - 1.0) / 0.5),
                      "right": 10 * smooth((t - 1.0) / 0.5)},
                  {s: knee_targets[s](t) for s in ("Right", "Left")},
                  {"Right": pitch(t), "Left": pitch(t)})
        if t < 0.95:
            ctx.scythe_upright(X, (-4 - 8 * smooth(t / 0.9), 0, -2 - 14 * smooth(t / 0.9)))
            held["m"] = ctx.scythe_world(X)
            return
        # it slips out of the bony fingers, topples and bounces flat on the ground
        u = smooth((t - 0.95) / 0.65)
        fall = E(0, 25, 0) @ E(0, 0, -88 * u) @ E(-10 * u, 0, 0)
        target = T(drop_path(t)) @ fall @ T(-rest_mid) @ ctx.scythe_rest
        world = blend_xf(held.get("m", target), target, smooth((t - 0.95) / 0.1))
        B.scythe_to(ctx.rig, X, ctx.rig.fk(X), world)
    c.frame = frame
    return c


CLIPS = [idle, walk, run, stomp, swing, spin, throw, roar, hurt, defeat]


def build_all(rig_path):
    rig = B.Rig(rig_path)
    ctx = Ctx(rig)
    out = []
    for fn in CLIPS:
        clip = fn(ctx)
        times, frames = B.bake(rig, clip)
        out.append((clip, times, frames))
    return rig, ctx, out


def main(rig_path, out_path):
    rig, ctx, clips = build_all(rig_path)
    seqs = [B.write(rig, clip, times, frames) for clip, times, frames in clips]
    folder = {"class": "Folder", "name": "GrimReaperAnimations", "ref": A._ref(),
              "props": {"Attributes": {"Attributes": {}}, "Tags": {"Tags": []}}, "children": seqs}
    with open(out_path, "w") as f:
        json.dump([folder], f)
    for clip, times, frames in clips:
        print("%-14s %5.2fs %s %3d keys, markers %s" % (clip.name, clip.length, "loop" if clip.loop else "    ",
                                                        len(times), [m[1] for m in clip.markers]))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
