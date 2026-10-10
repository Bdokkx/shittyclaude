"""More Grim Reaper animations for the same rig (model, bone names and rest pose
unchanged, so the boss already in the game plays them as they are).

    python tools/reaper_anims_more.py <rig.json> <out.json>   (rbxtool JSON: a Folder "GrimReaperAnimationsMore")

ReaperFall (loop) and ReaperLand; the jump slam in three parts: ReaperJumpStart,
ReaperJumpAir (loop) and ReaperJumpLand; the two-handed combat-ready hold:
ReaperIdleReady and ReaperWalkReady (loops); two idle fidgets, ReaperIdleLook
and ReaperIdleTap; and a bigger death, ReaperDefeat2. The root never moves in
the falls and jumps: the game moves the model.

Two-handed holds use arm IK: the right fist sits on the scythe's grip and the left
claw on the shaft further along, both re-solved every frame.
"""
import json
import math
import sys

import numpy as np

import banim as B
import reaper_anims as RA
from banim import E, T, inv, rot_x, Clip
from reaper_anims import (smooth, lerp, bump, VCurve, curve1, rot_between, blend_xf, BASE, REST, HOLD_TILT,
                          IDLE, MOVEMENT, ACTION, ACTION4)

A = B.A
TAU = math.tau


def norm(v):
    v = np.asarray(v, dtype=float)
    return v / np.linalg.norm(v)


def orth(v, d):
    """v made perpendicular to the unit vector d, then normalised."""
    v = np.asarray(v, dtype=float)
    d = np.asarray(d, dtype=float)
    v = v - d * v.dot(d)
    return v / np.linalg.norm(v)


def m3(R):
    m = np.eye(4)
    m[:3, :3] = R
    return m


def eased(keys, t):
    """Piecewise smoothstep through (t, value) keys (values are floats)."""
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t <= t1:
            return v0 + (v1 - v0) * smooth((t - t0) / (t1 - t0)) if t1 > t0 else v1
    return keys[-1][1]


# ---------------------------------------------------------------- holds

def axis_angle(m, i):
    """Rotation of a single-axis turn about joint axis i (1 = X, 3 = Z), in (-180, 180]."""
    q = A.mat_to_quat(m[:3, :3])
    if q[0] < 0:
        q = -q
    return math.degrees(2 * math.atan2(q[i], q[0]))


def robe_push(X, hips, extra=None, lim=80.0):
    """banim.robe_from_legs, but each panel's total swing is capped at `lim` degrees, so a
    deep crouch can't swing a panel over the top and round behind the legs."""
    pr, rr = hips.get("Right", (0.0, 0.0))
    pl, rl = hips.get("Left", (0.0, 0.0))
    e = extra or {}
    adds = (("RobeFront", max(pr, pl, 0.0) * 0.78 + e.get("front", 0.0), 1),
            ("RobeBack", min(pr, pl, 0.0) * 0.62 - e.get("back", 0.0), 1),
            ("RobeRight", max(rr, 0.0) * 1.1 + 0.18 * abs(pr) + e.get("right", 0.0), 3),
            ("RobeLeft", min(rl, 0.0) * 1.1 - 0.18 * abs(pl) - e.get("left", 0.0), 3))
    for b, add, i in adds:
        m = X.get(b, np.eye(4))
        tot = max(-lim, min(lim, axis_angle(m, i) + add))
        r = E(tot, 0, 0) if i == 1 else E(0, 0, tot)
        r[:3, 3] = m[:3, 3]
        X[b] = r


class Hold:
    """Where the scythe is: 'upright' in the right fist (the normal one-handed hold),
    'torso' (a model-space pose that moves with the chest) or 'world' (fixed in
    model space, e.g. stuck in the ground), plus where the left claw goes on the
    shaft and which way each elbow points."""

    def __init__(self, kind, S=None, s_left=None, pole_r=(0.8, -0.6, 0.6), pole_l=(-0.8, -0.6, 0.6), tilt=HOLD_TILT):
        self.kind = kind
        self.S = S
        self.s_left = s_left
        self.pole_r = np.array(pole_r, dtype=float)
        self.pole_l = np.array(pole_l, dtype=float)
        self.tilt = tilt


class Ctx2(RA.Ctx):
    def __init__(self, rig, rig_path):
        super().__init__(rig)
        data = json.load(open(rig_path))
        att = {a["Name"]: np.array(a["Position"], dtype=float) for a in data["Attachments"]}
        self.tip_rest = att["BladeTip"]
        self.base_rest = att["BladeBase"]
        parts = {p["Name"]: p for p in rig.parts}
        sc = parts["Scythe"]
        self.butt_rest = np.array([4.78, sc["Center"][1] - sc["Size"][1] / 2, -0.25])
        self.lgrip_rest = np.array([-4.55, 6.1, -0.45])      # where the left claw closes
        self.stats = {}
        self.current = None

    def plant(self, X, extra=None, targets=None, pitches=None, lim=80.0):
        """Feet planted as in reaper_anims.Ctx.plant, robe pushed with a capped swing."""
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
        robe_push(X, hips, extra, lim)

    # -------- building scythe poses (model space)

    def S_from(self, g, d, b):
        """The scythe with its grip at g, shaft along d, blade pointing along b."""
        y = norm(d)
        z = -orth(b, y)
        x = np.cross(y, z)
        return T(g) @ m3(np.column_stack([x, y, z])) @ T(-self.grip_rest) @ self.scythe_rest

    def S_tip(self, tip, d, b):
        """The scythe with its blade tip at `tip` (shaft along d, blade along b)."""
        S0 = self.S_from(np.zeros(3), d, b)
        t0 = (S0 @ inv(self.scythe_rest) @ np.array([*self.tip_rest, 1.0]))[:3]
        return T(np.asarray(tip) - t0) @ S0

    def on_scythe(self, S, local):
        """A rest-space point of the scythe, carried by the scythe pose S."""
        return (S @ inv(self.scythe_rest) @ np.array([*local, 1.0]))[:3]

    def grip_of(self, S):
        return self.on_scythe(S, self.grip_rest)

    def shaft_point(self, S, s):
        return self.on_scythe(S, self.grip_rest + np.array([0.0, s, 0.0]))

    # -------- arm IK

    def arm_ik(self, X, side, target, pole):
        """Two-bone IK: turn the upper arm and bend the elbow so the hand's grip point
        reaches `target` (model space), the elbow towards `pole`. The hand keeps its pose."""
        rig = self.rig
        up, lo, hd = side + "UpperArm", side + "LowerArm", side + "Hand"
        sp, ep, wp = rig.pivot[up], rig.pivot[lo], rig.pivot[hd]
        gp = self.grip_rest if side == "Right" else self.lgrip_rest
        H = X.get(hd, np.eye(4))
        u0 = ep - sp
        f0 = (wp - ep) + H[:3, :3] @ (gp - wp) + H[:3, 3]
        X[up] = np.eye(4)
        X[lo] = np.eye(4)
        J = rig.joint_world(rig.fk(X), up)
        Ji = inv(J)
        p = (Ji @ np.array([*target, 1.0]))[:3]
        pl = Ji[:3, :3] @ np.asarray(pole, dtype=float)
        L1, L2 = float(np.linalg.norm(u0)), float(np.linalg.norm(f0))
        dist = float(np.linalg.norm(p))
        dirn = p / max(dist, 1e-9)
        d = min(max(dist, abs(L1 - L2) + 1e-3), L1 + L2 - 1e-3)
        a = (L1 * L1 - L2 * L2 + d * d) / (2 * d)
        h = math.sqrt(max(L1 * L1 - a * a, 0.0))
        n = pl - dirn * pl.dot(dirn)
        if np.linalg.norm(n) < 1e-6:
            n = orth((0.0, 0.0, 1.0), dirn)
        n = n / np.linalg.norm(n)
        Ept = dirn * a + n * h
        Ppt = dirn * d
        a1 = norm(Ept)
        a2 = norm(Ppt - Ept)
        y0 = norm(u0)
        x0 = orth((1.0, 0.0, 0.0), y0)
        z0 = np.cross(x0, y0)
        x1 = np.cross(a1, a2)
        if np.linalg.norm(x1) < 1e-5:
            x1 = np.cross(n, dirn)
        x1 = orth(x1, a1)
        z1 = np.cross(x1, a1)
        R1 = np.column_stack([x1, a1, z1]) @ np.column_stack([x0, y0, z0]).T
        X[up] = m3(R1)
        X[lo] = rot_between(f0, R1.T @ a2)

    def hand_point(self, X, side):
        rig = self.rig
        hd = side + "Hand"
        gp = self.grip_rest if side == "Right" else self.lgrip_rest
        W = rig.fk(X)
        return (W[hd] @ inv(rig.rest[hd]) @ np.array([*gp, 1.0]))[:3]

    # -------- placing the scythe

    def upright_S(self, X, tilt=HOLD_TILT):
        W = self.rig.fk(X)
        g = self.grip_point(W)
        return T(g) @ E(*tilt) @ T(-self.grip_rest) @ self.scythe_rest

    def torso_S(self, X, S_rest):
        W = self.rig.fk(X)
        return W["UpperTorso"] @ inv(self.rig.rest["UpperTorso"]) @ S_rest

    def resolve(self, X, hold):
        if hold.kind == "upright":
            return self.upright_S(X, hold.tilt)
        if hold.kind == "torso":
            return self.torso_S(X, hold.S)
        return hold.S

    def place(self, X, holds, t, wr, wl):
        """holds: [(time, Hold)], blended with smoothstep between neighbours; wr / wl: how
        much each arm follows the scythe (0 = its keyed pose, 1 = IK onto the scythe)."""
        i = 0
        while i + 1 < len(holds) and holds[i + 1][0] <= t:
            i += 1
        h0 = holds[i][1]
        if i + 1 < len(holds) and t > holds[i][0]:
            t0, t1 = holds[i][0], holds[i + 1][0]
            k = smooth((t - t0) / (t1 - t0))
            h1 = holds[i + 1][1]
        else:
            k, h1 = 0.0, h0
        S = blend_xf(self.resolve(X, h0), self.resolve(X, h1), k)
        pole_r = lerp(h0.pole_r, h1.pole_r, k)
        pole_l = lerp(h0.pole_l, h1.pole_l, k)
        s0 = h0.s_left if h0.s_left is not None else (h1.s_left or 0.0)
        s1 = h1.s_left if h1.s_left is not None else s0
        s_left = lerp(s0, s1, k)
        if wr > 1e-4:
            Xa = dict(X)
            self.arm_ik(Xa, "Right", self.grip_of(S), pole_r)
            for b in ("RightUpperArm", "RightLowerArm"):
                X[b] = blend_xf(X.get(b, np.eye(4)), Xa[b], wr)
        if wl > 1e-4:
            Xa = dict(X)
            self.arm_ik(Xa, "Left", self.shaft_point(S, s_left), pole_l)
            for b in ("LeftUpperArm", "LeftLowerArm"):
                X[b] = blend_xf(X.get(b, np.eye(4)), Xa[b], wl)
        # the scythe always stays in the right fist
        W = self.rig.fk(X)
        g = self.grip_point(W)
        S = T(g - self.grip_of(S)) @ S
        B.scythe_to(self.rig, X, W, S)
        # how well the claw sits on the shaft (only counts when fully two-handed)
        if wl > 0.999 and self.current:
            q = self.hand_point(X, "Left")
            a = self.grip_of(S)
            dvec = self.shaft_point(S, 1.0) - a
            off = q - a
            miss = float(np.linalg.norm(off - dvec * off.dot(dvec)))
            st = self.stats.setdefault(self.current, {"claw": 0.0})
            st["claw"] = max(st["claw"], miss)
        if wr > 0.999 and self.current:
            miss = float(np.linalg.norm(self.hand_point(X, "Right") - self.grip_of(S)))
            st = self.stats.setdefault(self.current, {"claw": 0.0})
            st["fist"] = max(st.get("fist", 0.0), miss)
        return S


# ---------------------------------------------------------------- the holds used here

# combat-ready: right fist low in front of the right hip, the shaft rising across the
# body to the left claw in front of the left shoulder, the blade up over that shoulder
READY_G = np.array([2.6, 9.0, -3.4])
READY_D = norm((-5.2, 5.6, 0.4))
READY_B = orth((-0.6, 0.1, 0.8), READY_D)
READY_SL = 7.4
# raised overhead in both hands: the shaft level above the hood, blade standing up at the left end
OVER_G = np.array([1.6, 21.7, -0.5])
OVER_D = norm((-1.0, 0.14, 0.16))
OVER_B = orth((0.0, 1.0, 0.3), OVER_D)
OVER_SL = 3.0


def holds_for(ctx):
    ready = Hold("torso", ctx.S_from(READY_G, READY_D, READY_B), READY_SL,
                 pole_r=(0.7, -0.5, 0.8), pole_l=(-0.6, -1.0, 0.2))
    over = Hold("torso", ctx.S_from(OVER_G, OVER_D, OVER_B), OVER_SL,
                pole_r=(1.0, 0.0, 0.3), pole_l=(-1.0, 0.0, 0.3))
    upright = Hold("upright")
    return ready, over, upright


# ---------------------------------------------------------------- shared poses

def fall_keys(t, L=0.8):
    """Falling feet first: robe and cape streaming up, fluttering in the wind."""
    ph = t / L * TAU

    def f(k, a=0.0):
        return math.sin(k * ph + a)
    return dict(
        LowerTorso=(5 + 2 * f(1), 3 * f(1, 1), 2 * f(1, 2), 0, 0.15 * f(2), 0),
        UpperTorso=(-6 + 2 * f(2), 0, 1.5 * f(1)),
        Head=(-10 + 2 * f(2, 1), 5 * f(1), 0),
        Jaw=(-12 - 5 * f(2, 0.5), 0, 0),
        LeftHand=(-24, 0, 0),
        RightHand=(0, 0, 0),
        RobeFront=(106 + 12 * f(3), 0, 0),
        RobeBack=(-110 - 12 * f(3, 1.3), 0, 0),
        RobeLeft=(0, 0, -104 - 12 * f(3, 2.1)),
        RobeRight=(0, 0, 104 + 12 * f(3, 0.7)),
        Cape=(-150 + 10 * f(3, 0.4), 0, 6 * f(2)))


def air_keys(t, L=0.6):
    """Airborne in the jump: knees up a little, robe and cape lifting and fluttering."""
    ph = t / L * TAU

    def f(k, a=0.0):
        return math.sin(k * ph + a)
    return dict(
        LowerTorso=(-4 + 2 * f(1), 2 * f(1, 1), 0, 0, 0.6 + 0.12 * f(1), 0),
        UpperTorso=(4 + 2 * f(1, 0.5), 0, 1.5 * f(1)),
        Head=(-12 + 2 * f(1, 1), 4 * f(1), 0),
        Jaw=(-14 - 4 * f(2), 0, 0),
        LeftHand=(-24, 0, 0),
        RightHand=(0, 0, 0),
        RobeFront=(46 + 10 * f(2), 0, 0),
        RobeBack=(-58 - 10 * f(2, 1.1), 0, 0),
        RobeLeft=(0, 0, -50 - 10 * f(2, 2.0)),
        RobeRight=(0, 0, 50 + 10 * f(2, 0.6)),
        Cape=(-95 + 10 * f(2, 0.3), 0, 5 * f(1)))


FALL_FEET = {"Right": ((1.25, 3.5, 0.5), -50.0), "Left": ((-1.25, 3.5, 0.5), -50.0)}
AIR_FEET = {"Right": ((1.35, 3.6, -0.7), -32.0), "Left": ((-1.35, 3.3, 0.4), -38.0)}


def legs_fk_ik(ctx, X, feet):
    """Legs off the ground: IK to the given ankle spots and foot pitches, no floor clamp."""
    hips = {}
    for s in ("Right", "Left"):
        pos, pitch = feet[s]
        hips[s] = B.leg_ik(ctx.rig, X, ctx.rig.fk(X), s, np.array(pos, dtype=float), pitch)
    B.robe_from_legs(X, hips, None)


def lerp_feet(a, b, k):
    return {s: (tuple(np.array(a[s][0]) + (np.array(b[s][0]) - np.array(a[s][0])) * k),
                a[s][1] + (b[s][1] - a[s][1]) * k) for s in ("Right", "Left")}


def rest_feet(ctx):
    return {s: (tuple(ctx.ankle_rest[s]), 0.0) for s in ("Right", "Left")}


# ---------------------------------------------------------------- the clips

def fall(ctx):
    L = 0.8
    c = Clip("ReaperFall", L, True, ACTION, BASE)
    for i in range(25):
        t = L * i / 24
        c.key(t, **fall_keys(t, L))
    _, over, _ = holds_for(ctx)

    def frame(t, X, _):
        ph = t / L * TAU
        feet = {s: ((p[0], p[1] + 0.1 * math.sin(ph + (0 if s == "Right" else 2)), p[2]), pitch + 4 * math.sin(2 * ph))
                for s, (p, pitch) in FALL_FEET.items()}
        legs_fk_ik(ctx, X, feet)
        ctx.place(X, [(0.0, over)], t, 1.0, 1.0)
    c.frame = frame
    c.cloth_lag = 0.05
    return c


def land(ctx):
    """From the fall: a slam into a deep crouch with the blade driven into the ground at
    the right front (Impact), a menacing look up, then up to the idle pose."""
    L = 1.6
    TI = 5 / 30
    c = Clip("ReaperLand", L, False, ACTION, BASE)
    c.pose(0.0, fall_keys(0.0))
    c.pose(TI, {"LowerTorso": (-3, -14, 0, 0.3, -3.2, -0.3), "UpperTorso": (-9, -8, 3), "Head": (4, 10, 0),
                "Jaw": (-26, 0, 0), "LeftHand": (-24, 0, 0), "RightHand": (0, 0, 0),
                "RobeFront": (10, 0, 0), "RobeBack": (-10, 0, 0), "RobeLeft": (0, 0, -12), "RobeRight": (0, 0, 12),
                "Cape": (-40, 0, 0)})
    c.pose(0.32, {"LowerTorso": (-4, -14, 0, 0.3, -3.4, -0.35), "UpperTorso": (-11, -8, 3), "Head": (0, 10, 0),
                  "Jaw": (-8, 0, 0), "Cape": (-8, 0, 0)})
    c.pose(0.55, {"LowerTorso": (-4, -14, 0, 0.3, -3.3, -0.3), "UpperTorso": (-10, -8, 3), "Head": (20, 6, 0),
                  "Jaw": (-34, 0, 0), "Cape": (-6, 0, 0)})
    c.pose(0.8, {"LowerTorso": (-5, -10, 0, 0.2, -2.6, -0.35), "UpperTorso": (-12, -6, 2), "Head": (12, 4, 0),
                 "Jaw": (-10, 0, 0), "Cape": (-6, 0, 0)})
    c.pose(1.15, {"LowerTorso": (-2, -3, 0, 0, -0.7, 0), "UpperTorso": (-9, -2, 0), "Head": (-2, 0, 0),
                  "Jaw": (0, 0, 0), "LeftHand": (-10, 0, 0), "Cape": (-4, 0, 0)})
    c.pose(L, REST)
    c.marker(TI, "Impact")
    ready, over, upright = holds_for(ctx)
    stuck = Hold("world", ctx.S_from((3.0, 9.7, -8.9), (0.1, -0.15, -0.98), (0.0, -1.0, 0.3)), -4.4,
                 pole_r=(1.0, -0.6, 0.3), pole_l=(-1.0, -0.6, 0.3))
    chop = Hold("world", ctx.S_from((1.5, 15.5, -7.5), (0.12, 0.85, -0.5), (0.0, -0.5, -0.85)), -3.0,
                pole_r=(1.0, -0.3, 0.4), pole_l=(-1.0, -0.3, 0.4))
    pull = Hold("world", ctx.S_from((5.0, 9.6, -5.0), (0.3, 0.55, -0.78), (0.0, -0.4, -0.9)), -4.0,
                pole_r=(1.0, -0.4, 0.5), pole_l=(-1.0, -0.4, 0.4))
    holds = [(0.0, over), (TI * 0.5, chop), (TI, stuck), (0.82, stuck), (0.98, pull), (1.18, upright)]
    fall_feet = FALL_FEET
    wide = {"Right": ((1.95, 1.15, -0.9), 0.0), "Left": ((-1.85, 1.15, 0.9), 0.0)}

    def frame(t, X, _):
        if t < TI:
            feet = lerp_feet(fall_feet, wide, smooth(t / TI))
            targets = {s: np.array(feet[s][0]) for s in feet}
            pitches = {s: feet[s][1] for s in feet}
        else:
            targets, pitches = {}, {}
            for s, t0, t1 in (("Right", 0.95, 1.2), ("Left", 1.15, 1.4)):
                k = smooth((t - t0) / (t1 - t0))
                p = np.array(wide[s][0]) + (ctx.ankle_rest[s] - np.array(wide[s][0])) * k
                p[1] += 0.6 * bump(t, t0, t1)
                targets[s], pitches[s] = p, 0.0
        flare = 18 * math.exp(-max(0.0, t - TI) / 0.25) if t >= TI - 0.04 else 0.0
        ctx.plant(X, {"front": flare, "back": flare * 0.5, "left": flare * 0.4, "right": flare * 0.4}, targets,
                  pitches, lim=180.0 if t < TI else 80.0)
        wr = 1.0 - smooth((t - 0.98) / 0.26)
        wl = 1.0 - smooth((t - 0.86) / 0.2)
        ctx.place(X, holds, t, wr, wl)
    c.frame = frame
    c.cloth_lag = 0.09
    return c


def jump_start(ctx):
    """Crouch, swing the scythe up into both hands, leap (Jump: the feet leave the ground)."""
    L = 0.5
    TJ = 12 / 30
    c = Clip("ReaperJumpStart", L, False, ACTION, BASE)
    c.pose(0.0, REST)
    c.pose(0.24, {"LowerTorso": (12, 0, 0, 0, -2.3, -0.5), "UpperTorso": (-26, 0, 0), "Head": (20, 0, 0),
                  "Jaw": (-8, 0, 0), "LeftHand": (-20, 0, 0), "Cape": (-8, 0, 0)})
    c.pose(0.36, {"LowerTorso": (-6, 0, 0, 0, 0.9, 0.3), "UpperTorso": (10, 0, 0), "Head": (-6, 0, 0),
                  "Jaw": (-22, 0, 0), "LeftHand": (-24, 0, 0), "Cape": (-34, 0, 0)})
    c.pose(L, air_keys(0.0))
    c.marker(TJ, "Jump")
    ready, over, upright = holds_for(ctx)
    lift = Hold("torso", ctx.S_from((2.0, 17.0, -5.0), (-0.9, 0.35, 0.25), (0.0, 1.0, 0.3)), 3.0,
                pole_r=(1.0, -0.4, 0.4), pole_l=(-1.0, -0.4, 0.4))
    holds = [(0.0, upright), (0.22, ready), (0.33, lift), (0.45, over)]

    def frame(t, X, _):
        if t <= TJ:
            pitch = -46 * smooth((t - 0.3) / (TJ - 0.3))
            ctx.plant(X, {"front": 6 * bump(t, 0.1, 0.4), "back": 0, "left": 4 * bump(t, 0.1, 0.4),
                          "right": 4 * bump(t, 0.1, 0.4)}, None, {"Right": pitch, "Left": pitch})
        else:
            k = smooth((t - TJ) / (L - TJ))
            start = {s: (tuple(ctx.ankle_rest[s] + (0, 0.9, 0.3)), -46.0) for s in ("Right", "Left")}
            legs_fk_ik(ctx, X, lerp_feet(start, AIR_FEET, k))
        wr = smooth((t - 0.04) / 0.18)
        wl = smooth((t - 0.08) / 0.18)
        ctx.place(X, holds, t, wr, wl)
    c.frame = frame
    c.cloth_lag = 0.07
    return c


def jump_air(ctx):
    L = 0.6
    c = Clip("ReaperJumpAir", L, True, ACTION, BASE)
    for i in range(19):
        t = L * i / 18
        c.key(t, **air_keys(t, L))
    _, over, _ = holds_for(ctx)

    def frame(t, X, _):
        ph = t / L * TAU
        feet = {s: ((p[0], p[1] + 0.12 * math.sin(ph + (0 if s == "Right" else 1.5)), p[2]), pitch)
                for s, (p, pitch) in AIR_FEET.items()}
        legs_fk_ik(ctx, X, feet)
        ctx.place(X, [(0.0, over)], t, 1.0, 1.0)
    c.frame = frame
    c.cloth_lag = 0.06
    return c


def jump_land(ctx):
    """Feet and scythe smash down in front together (Impact), hold, then back to idle."""
    L = 1.4
    TI = 5 / 30
    c = Clip("ReaperJumpLand", L, False, ACTION, BASE)
    c.pose(0.0, air_keys(0.0))
    c.pose(TI, {"LowerTorso": (-4, 0, 0, 0, -2.9, -0.4), "UpperTorso": (-10, 0, 0), "Head": (10, 0, 0),
                "Jaw": (-30, 0, 0), "LeftHand": (-24, 0, 0), "RightHand": (0, 0, 0),
                "RobeFront": (8, 0, 0), "RobeBack": (-8, 0, 0), "RobeLeft": (0, 0, -10), "RobeRight": (0, 0, 10),
                "Cape": (-30, 0, 0)})
    c.pose(0.32, {"LowerTorso": (-5, 0, 0, 0, -3.1, -0.45), "UpperTorso": (-12, 0, 0), "Head": (8, 0, 0),
                  "Jaw": (-12, 0, 0), "Cape": (-8, 0, 0)})
    c.pose(0.6, {"LowerTorso": (-4, 0, 0, 0, -2.6, -0.4), "UpperTorso": (-10, 0, 0), "Head": (6, 0, 0),
                 "Jaw": (-6, 0, 0)})
    c.pose(0.95, {"LowerTorso": (-4, 0, 0, 0, -0.9, -0.1), "UpperTorso": (-10, 0, 0), "Head": (0, 0, 0),
                  "Jaw": (0, 0, 0), "LeftHand": (-10, 0, 0), "Cape": (-4, 0, 0)})
    c.pose(L, REST)
    c.marker(TI, "Impact")
    ready, over, upright = holds_for(ctx)
    smash = Hold("world", ctx.S_from((2.2, 9.4, -9.2), (-0.05, -0.15, -0.99), (0.0, -1.0, 0.3)), -4.4,
                 pole_r=(1.0, -0.6, 0.3), pole_l=(-1.0, -0.6, 0.3))
    chop = Hold("world", ctx.S_from((2.4, 15.5, -7.5), (0.0, 0.85, -0.52), (0.0, -0.5, -0.85)), -3.0,
                pole_r=(1.0, -0.3, 0.4), pole_l=(-1.0, -0.3, 0.4))
    swing = Hold("world", ctx.S_from((2.5, 12.6, -9.0), (-0.03, 0.3, -0.95), (0.0, -0.95, -0.3)), -3.8,
                 pole_r=(1.0, -0.4, 0.4), pole_l=(-1.0, -0.4, 0.4))
    holds = [(0.0, over), (TI * 0.45, chop), (TI * 0.75, swing), (TI, smash), (0.62, smash), (0.96, upright)]
    wide = {"Right": ((1.9, 1.15, -0.45), 0.0), "Left": ((-1.9, 1.15, 0.45), 0.0)}

    def frame(t, X, _):
        if t < TI:
            feet = lerp_feet(AIR_FEET, wide, smooth(t / TI))
            targets = {s: np.array(feet[s][0]) for s in feet}
            pitches = {s: feet[s][1] for s in feet}
        else:
            targets, pitches = {}, {}
            for s, t0, t1 in (("Right", 0.75, 1.0), ("Left", 0.92, 1.17)):
                k = smooth((t - t0) / (t1 - t0))
                p = np.array(wide[s][0]) + (ctx.ankle_rest[s] - np.array(wide[s][0])) * k
                p[1] += 0.5 * bump(t, t0, t1)
                targets[s], pitches[s] = p, 0.0
        flare = 16 * math.exp(-max(0.0, t - TI) / 0.25) if t >= TI - 0.04 else 0.0
        ctx.plant(X, {"front": flare, "back": flare * 0.5, "left": flare * 0.4, "right": flare * 0.4}, targets,
                  pitches, lim=180.0 if t < TI else 80.0)
        wr = 1.0 - smooth((t - 0.76) / 0.24)
        wl = 1.0 - smooth((t - 0.66) / 0.2)
        ctx.place(X, holds, t, wr, wl)
    c.frame = frame
    c.cloth_lag = 0.08
    return c


def idle_ready(ctx):
    """Combat-ready: a wide stance, the scythe in both hands across the body, a slow sway,
    the head tracking from side to side."""
    L = 3.0
    c = Clip("ReaperIdleReady", L, True, IDLE, BASE)
    for i in range(31):
        t = L * i / 30
        ph = t / L * TAU
        br = 0.5 - 0.5 * math.cos(2 * ph)
        c.key(t, LowerTorso=(3 + 1.5 * math.sin(ph), -12 + 3.5 * math.sin(ph), 1.5 * math.sin(ph + 1), 0,
                             -0.6 + 0.1 * br, 0),
              UpperTorso=(-10 + 2.5 * br, 6 - 2 * math.sin(ph), 1.2 * math.sin(ph + 0.5)),
              Head=(-7 + 1.5 * br, 30 * math.sin(ph - 0.6), 6 * math.sin(ph - 1.6)),
              Jaw=(-3 * br, 0, 0), LeftHand=(-24, 0, 0), RightHand=(0, 0, 0),
              Cape=(-4 - 2 * br + 2 * math.sin(ph), 0, 1.5 * math.cos(ph)))
    ready, _, _ = holds_for(ctx)
    stance = {"Right": (1.95, 1.15, 0.8), "Left": (-1.75, 1.15, -1.0)}

    def frame(t, X, _):
        s = math.sin(t / L * TAU)
        ctx.plant(X, {"front": 2 + 1.5 * s, "back": -1.5 * s, "right": 1.2, "left": 1.2},
                  {k: np.array(v) for k, v in stance.items()}, None)
        ctx.place(X, [(0.0, ready)], t, 1.0, 1.0)
    c.frame = frame
    return c


def walk_ready(ctx):
    """The walk with the two-handed combat-ready hold."""
    c = RA.locomotion(ctx, "ReaperWalkReady", 1.5, 0.56, 3.0, 1.7, (0.35, 0.42), (-14, 6), (14, 0, -6),
                      (4, 9, 4, 22, 6, 16, 6, 26), (-8, 4), 18, (0.0, 0.75))
    for i in range(9):
        t = 1.5 * i / 8
        ph = t / 1.5 * TAU
        c.key(t, UpperTorso=(-14, 4 - 4 * math.cos(ph), 2 * math.sin(ph)), Head=(-6, -4 + 4 * math.cos(ph), 0),
              LeftHand=(-24, 0, 0), RightHand=(0, 0, 0))
    base = c.frame
    ready, _, _ = holds_for(ctx)

    def frame(t, X, k):
        base(t, X, k)
        ctx.place(X, [(0.0, ready)], t, 1.0, 1.0)
    c.frame = frame
    return c


def idle_look(ctx):
    """A slow look round, left then right, with a couple of jaw clacks (Clack)."""
    L = 2.8
    c = Clip("ReaperIdleLook", L, False, MOVEMENT, BASE)
    c.pose(0.0, REST)
    c.pose(0.65, {"LowerTorso": (0, 4, 0, 0, 0, 0), "UpperTorso": (-6, 12, 1), "Head": (-4, 34, 7)})
    c.pose(1.05, {"LowerTorso": (0, 4, 0, 0, 0, 0), "UpperTorso": (-6, 12, 1), "Head": (-6, 38, 9)})
    c.pose(1.6, {"LowerTorso": (0, -4, 0, 0, 0, 0), "UpperTorso": (-6, -12, -1), "Head": (-4, -34, -7)})
    c.pose(2.0, {"LowerTorso": (0, -4, 0, 0, 0, 0), "UpperTorso": (-6, -12, -1), "Head": (-6, -38, -9)})
    c.pose(L, REST)
    for t, j in ((0.0, 0), (1.12, 0), (1.18, -16), (1.26, -1), (1.32, -16), (1.4, -1), (1.48, 0), (2.05, 0),
                 (2.12, -14), (2.2, -1), (2.3, 0), (L, 0)):
        c.key(t, Jaw=(j, 0, 0))
    for t in (1.267, 1.4, 2.2):
        c.marker(t, "Clack")
    for t, lh, la in ((0.0, -6, 24), (0.7, -14, 30), (1.6, 0, 22), (2.1, -10, 28), (L, -6, 24)):
        c.key(t, LeftHand=(lh, 0, 0), LeftLowerArm=(la, 0, 0))

    def frame(t, X, _):
        ctx.plant(X)
        ctx.scythe_upright(X)
    c.frame = frame
    return c


def idle_tap(ctx):
    """Lifts the scythe and taps its butt on the ground twice (Tap)."""
    L = 2.6
    taps = (27 / 30, 45 / 30)
    c = Clip("ReaperIdleTap", L, False, MOVEMENT, BASE)
    c.pose(0.0, REST)
    for t, ua, la, head, ut in ((0.55, 30, 54, (-10, -12, 0), (-8, -4, 0)), (taps[0], 6, 16, (2, -8, 0), (-6, -3, 0)),
                                (1.18, 26, 46, (-9, -10, 0), (-8, -4, 0)), (taps[1], 6, 16, (3, -8, 0), (-6, -3, 0)),
                                (1.95, 12, 20, (-5, -4, 0), (-6, -1, 0))):
        c.key(t, RightUpperArm=(ua, 0, 3), RightLowerArm=(la, 0, 0), Head=head, UpperTorso=ut)
    c.key(L, RightUpperArm=BASE["RightUpperArm"], RightLowerArm=BASE["RightLowerArm"], Head=BASE["Head"],
          UpperTorso=BASE["UpperTorso"])
    for t, j in ((0.0, 0), (taps[0] - 0.03, 0), (taps[0] + 0.05, -10), (taps[0] + 0.15, 0), (taps[1] - 0.03, 0),
                 (taps[1] + 0.05, -10), (taps[1] + 0.15, 0), (L, 0)):
        c.key(t, Jaw=(j, 0, 0))
    for t in taps:
        c.marker(t, "Tap")
    butt = [(0.0, None), (0.5, 3.2), (taps[0] - 0.12, 2.0), (taps[0], 0.0), (taps[0] + 0.07, 0.3), (1.18, 2.8),
            (taps[1] - 0.12, 1.8), (taps[1], 0.0), (taps[1] + 0.07, 0.3), (2.0, None), (L, None)]

    def frame(t, X, _):
        ctx.plant(X)
        S = ctx.upright_S(X)
        y_now = ctx.on_scythe(S, ctx.butt_rest)[1]
        # where the butt should be: its own height while just held, a set height round the taps
        keys = [(tk, y_now if v is None else v) for tk, v in butt]
        want = eased(keys, t)
        slide = max(-1.2, min(1.2, want - y_now))
        S = T((0.0, slide, 0.0)) @ S
        B.scythe_to(ctx.rig, X, ctx.rig.fk(X), S)
    c.frame = frame
    return c


def defeat2(ctx):
    """A bigger death: staggers back, stumbles forward, drops to its knees, the scythe falls
    (ScytheDrop), then it keels over face down (Collapsed)."""
    L = 4.6
    c = Clip("ReaperDefeat2", L, False, ACTION4, BASE)
    c.pose(0.0, REST)
    c.pose(0.25, {"LowerTorso": (-8, 0, 4, 0, -0.3, 0.6), "UpperTorso": (24, 6, 6), "Head": (28, -10, 8),
                  "RightUpperArm": (-8, 0, 32), "RightLowerArm": (10, 0, 0), "LeftUpperArm": (-14, 0, -42),
                  "LeftLowerArm": (12, 0, 0), "LeftHand": (-30, 0, 0), "Cape": (-12, 0, 0), "Jaw": (-34, 0, 0)})
    c.pose(0.62, {"LowerTorso": (10, 8, -4, 0, -0.9, -0.6), "UpperTorso": (-24, 6, -6), "Head": (-12, 10, -4),
                  "RightUpperArm": (22, 0, 20), "RightLowerArm": (30, 0, 0), "LeftUpperArm": (34, 0, -18),
                  "LeftLowerArm": (36, 0, 0), "LeftHand": (-10, 0, 0), "Cape": (-6, 0, 0), "Jaw": (-16, 0, 0)})
    c.pose(1.0, {"LowerTorso": (12, 4, 0, 0, -2.4, -0.1), "UpperTorso": (-22, 2, -2), "Head": (-14, 4, 0),
                 "RightUpperArm": (14, 0, 18), "RightLowerArm": (24, 0, 0), "LeftUpperArm": (18, 0, -18),
                 "LeftLowerArm": (26, 0, 0), "LeftHand": (-6, 0, 0), "Cape": (-10, 0, 0), "Jaw": (-24, 0, 0)})
    c.pose(1.4, {"LowerTorso": (10, 0, 0, 0, -3.6, 0.6), "UpperTorso": (-26, 0, 0), "Head": (-16, 0, 0),
                 "RightUpperArm": (16, 0, 14), "RightLowerArm": (26, 0, 0), "LeftUpperArm": (18, 0, -14),
                 "LeftLowerArm": (26, 0, 0), "LeftHand": (0, 0, 0), "Cape": (-16, 0, 0), "Jaw": (-20, 0, 0)})
    c.pose(2.3, {"LowerTorso": (14, 0, 0, 0, -3.7, 0.7), "UpperTorso": (-36, 0, 3), "Head": (-30, 0, 8),
                 "RightUpperArm": (10, 0, 10), "RightLowerArm": (20, 0, 0), "LeftUpperArm": (12, 0, -10),
                 "LeftLowerArm": (20, 0, 0), "LeftHand": (8, 0, 0), "Cape": (-4, 0, 0), "Jaw": (-22, 0, 0)})
    c.pose(2.6, {"LowerTorso": (8, 0, 0, 0, -3.6, 0.5), "UpperTorso": (-30, 0, 2), "Head": (-24, 0, 6),
                 "RightUpperArm": (30, 0, 14), "RightLowerArm": (24, 0, 0), "LeftUpperArm": (34, 0, -14),
                 "LeftLowerArm": (24, 0, 0), "Jaw": (-30, 0, 0)})
    c.pose(3.2, {"LowerTorso": (-80, 0, 4, 0, -6.15, -1.6), "UpperTorso": (-6, 0, 0), "Head": (14, 62, 8),
                 "RightUpperArm": (176, 0, 34), "RightLowerArm": (16, 0, 0), "LeftUpperArm": (168, 0, -46),
                 "LeftLowerArm": (22, 0, 0), "LeftHand": (20, 0, 0), "Cape": (-10, 0, 0), "Jaw": (-26, 0, 0)})
    c.pose(3.38, {"LowerTorso": (-77, 0, 4, 0, -5.85, -1.6), "UpperTorso": (-8, 0, 0), "Head": (12, 64, 8)})
    c.pose(3.6, {"LowerTorso": (-80, 0, 4, 0, -6.15, -1.6), "UpperTorso": (-6, 0, 0), "Head": (14, 62, 8),
                 "Cape": (-2, 0, 0)})
    c.pose(L, {"LowerTorso": (-80, 0, 4, 0, -6.17, -1.6), "UpperTorso": (-6, 0, 0), "Head": (15, 64, 8),
               "RightUpperArm": (178, 0, 36), "RightLowerArm": (12, 0, 0), "LeftUpperArm": (170, 0, -48),
               "LeftLowerArm": (18, 0, 0), "LeftHand": (24, 0, 0), "Cape": (0, 0, 0), "Jaw": (-28, 0, 0)})
    c.marker(1.7, "ScytheDrop")
    c.marker(3.2, "Collapsed")
    sgn = {"Right": 1, "Left": -1}
    knee = {s: VCurve([(0.0, ctx.ankle_rest[s]), (0.45, ctx.ankle_rest[s] + (0, 0, 0.0)),
                       (0.62, ctx.ankle_rest[s] + (0, 0.5 if s == "Left" else 0.0, -1.2 if s == "Left" else 0.0)),
                       (0.8, ctx.ankle_rest[s] + (0, 0, -1.6 if s == "Left" else 0.0)),
                       (1.0, ctx.ankle_rest[s] + (0.05 * sgn[s], 0.0, 0.6)),
                       (1.4, ctx.ankle_rest[s] + (0.1 * sgn[s], -0.55, 3.4)),
                       (2.6, ctx.ankle_rest[s] + (0.1 * sgn[s], -0.6, 3.5)),
                       (3.2, ctx.ankle_rest[s] + (0.3 * sgn[s], -0.5, 5.6)),
                       (L, ctx.ankle_rest[s] + (0.3 * sgn[s], -0.5, 5.65))]) for s in ("Right", "Left")}
    pitch = curve1([(0.0, 0.0), (0.9, -10.0), (1.4, -160.0), (2.6, -165.0), (3.2, -172.0), (L, -172.0)])
    rest_mid = np.array([4.78, 11.0, -2.0])
    drop = VCurve([(1.42, (6.0, 8.8, -1.8)), (1.58, (7.4, 3.8, -2.6)), (1.7, (7.9, 0.35, -3.0)),
                   (1.82, (8.0, 0.8, -3.1)), (1.95, (8.1, 0.35, -3.2)), (L, (8.1, 0.35, -3.2))])
    held = {}

    def frame(t, X, _):
        flare = 10 * smooth((t - 1.0) / 0.5) * (1 - smooth((t - 2.6) / 0.6))
        lift = 2.6 * bump(t, 2.55, 3.25)
        ctx.plant(X, {"front": flare, "back": -4 * (1 - smooth((t - 2.6) / 0.6)), "left": flare, "right": flare},
                  {s: knee[s](t) + (0, lift, 0) for s in ("Right", "Left")}, {"Right": pitch(t), "Left": pitch(t)})
        if t < 1.42:
            ctx.scythe_upright(X, (-4 - 10 * smooth(t / 1.3), 0, -2 - 16 * smooth(t / 1.3)))
            held["m"] = ctx.scythe_world(X)
            return
        u = smooth((t - 1.42) / 0.3)
        fall_r = E(0, 30, 0) @ E(0, 0, -88 * u) @ E(-10 * u, 0, 0)
        target = T(drop(t)) @ fall_r @ T(-rest_mid) @ ctx.scythe_rest
        world = blend_xf(held.get("m", target), target, smooth((t - 1.42) / 0.08))
        B.scythe_to(ctx.rig, X, ctx.rig.fk(X), world)
    c.frame = frame
    return c


CLIPS = [fall, land, jump_start, jump_air, jump_land, idle_ready, walk_ready, idle_look, idle_tap, defeat2]
# deep crouches and lying down: the robe may settle this far into the floor (it reads as cloth
# pooling on the ground) instead of being swung up into stiff wings to clear it
CLOTH_FLOOR = {"ReaperLand": -0.9, "ReaperJumpLand": -0.9, "ReaperDefeat2": -1.8}
AIRBORNE = {"ReaperFall": (0.0, 99.0), "ReaperJumpAir": (0.0, 99.0), "ReaperJumpStart": (12 / 30 + 1e-3, 99.0),
            "ReaperLand": (0.0, 4.5 / 30), "ReaperJumpLand": (0.0, 4.5 / 30)}


def build_all(rig_path):
    rig = B.Rig(rig_path)
    ctx = Ctx2(rig, rig_path)
    out = []
    for fn in CLIPS:
        clip = fn(ctx)
        clip.floor_mode = "both"
        clip.floor_level = CLOTH_FLOOR.get(clip.name, 0.12)
        ctx.current = clip.name
        times, frames = B.bake(rig, clip)
        out.append((clip, times, frames))
    return rig, ctx, out


def main(rig_path, out_path):
    rig, ctx, clips = build_all(rig_path)
    seqs = [B.write(rig, clip, times, frames) for clip, times, frames in clips]
    folder = {"class": "Folder", "name": "GrimReaperAnimationsMore", "ref": A._ref(),
              "props": {"Attributes": {"Attributes": {}}, "Tags": {"Tags": []}}, "children": seqs}
    with open(out_path, "w") as f:
        json.dump([folder], f)
    for clip, times, frames in clips:
        st = ctx.stats.get(clip.name, {})
        grip = ""
        if st:
            grip = "  fist off grip %.2f, claw off shaft %.2f" % (st.get("fist", 0.0), st.get("claw", 0.0))
        print("%-16s %5.2fs %s %3d keys, markers %s%s" % (clip.name, clip.length, "loop" if clip.loop else "    ",
                                                           len(times), [(m[1], round(m[0], 3)) for m in clip.markers],
                                                           grip))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
