"""The guardians' clips: PotatoKit.GuardianAnimations.<AreaId>.Sleep / Wake / Run.

  Sleep  3.0 s, loops, 10 keys a second. The sleeping pose, breathing. Show EyeShut.
  Wake   1.5 s, once. Starts in the Sleep pose, lifts its head (open the eyes at EYES_OPEN_AT,
         marker "EyesOpen"), gets up, roars or threatens (marker "Roar") and ends in its rest pose
         (the pose it is built in), so Run or a held rest pose follows cleanly.
  Run    loops, 30 keys a second. Its gait, in place: move the model along the ground at about
         RUN_SPEED[area] studs a second, or scale the clip's speed by (your speed / RUN_SPEED).
         Markers "Step" on footfalls, "Land" on landings.
Joint transforms are in model axes at each hinge (front -Z, +X the guardian's right):
rx(+a) swings a hanging limb forward and tips a forward-pointing part up; ry(+a) turns it to its
left; rz(+a) lifts its right (+X) side.
"""
import math

import numpy as np

from .rig import Clip
from .roots_anim import ease, rx, ry, rz, tr

TAU = math.tau
SLEEP_LEN, SLEEP_FPS = 3.0, 10
WAKE_LEN = 1.5
EYES_OPEN_AT = 0.25
ROAR_AT = 1.0
SIDES = (("L", -1.0), ("R", 1.0))


def breath(t):
    return 0.5 - 0.5 * math.cos(TAU * t / SLEEP_LEN)


def wake_curves(t):
    """head: the head's share of the sleep pose (it lifts first); s: the body's share; r: the roar."""
    head = 1.0 - ease(0.0, 1.0, t, 0.0, 0.3, "out")
    s = 1.0 - ease(0.0, 1.0, t, 0.25, 0.8)
    r = ease(0.0, 1.0, t, 0.8, 1.0, "out") * (1.0 - ease(0.0, 1.0, t, 1.15, 1.5))
    return head, s, r


def shake(t, amp, f=11.0):
    return amp * math.sin(TAU * f * t)


def arc(u, a, b):
    """0 outside [a, b]; a parabola 0 -> 1 -> 0 inside."""
    if u <= a or u >= b:
        return 0.0
    v = (u - a) / (b - a)
    return 4.0 * v * (1.0 - v)


def frac(x):
    return x - math.floor(x)


def fold_angle(L, b, h):
    """Degrees to swing a leg forward about its hip so that its lowest corner (L below the hip and b
    behind it at rest) ends h below the hip."""
    if h >= L:
        return 0.0
    lo, hi = 0.0, 89.0
    for _ in range(40):
        mid = (lo + hi) / 2
        y = L * math.cos(math.radians(mid)) + b * math.sin(math.radians(mid))
        if y > h:
            lo = mid
        else:
            hi = mid
    return lo


def foot_comp(a, L, z_toe, z_heel):
    """How far to raise a rigid leg (hip L above the sole; sole from z_toe to z_heel) swung a degrees
    about its hip so its sole does not dig in."""
    ra = math.radians(a)
    low = min(-L * math.cos(ra) - z * math.sin(ra) for z in (z_toe, z_heel))
    return max(0.0, -L - low)


def leg_lift_angle(hip_y, drop, reach, foot_dy):
    """Degrees to raise a leg about its hip so its foot stays on the ground when the hip drops."""
    R = math.hypot(reach, foot_dy)
    phi = math.atan2(foot_dy, reach)
    return math.degrees(math.asin(max(-1.0, min(1.0, -(hip_y - drop) / R))) - phi)


# ==================================================================== two legs, stomping (golems, robot)

def biped_sleep(X, P, s, head, br):
    """Dormant on its feet: sagging, bent forward, arms dangling, head bowed."""
    for side, sg in SIDES:
        X["Leg" + side] = rz(sg * 3 * s)
        X["Arm" + side] = rx(26 * s + 2 * br * s) @ rz(-sg * 7 * s)
    X["Body"] = tr(0, -0.22 * s + 0.05 * br * s, 0) @ rx(-14 * s - 2.0 * br * s) @ rz(3 * s)
    X["Head"] = rx(-30 * head - 2.0 * br * head) @ rz(8 * head)


def biped(P):
    def sleep(X, t):
        biped_sleep(X, P, 1.0, 1.0, breath(t))
        if P.get("key"):
            X["Key"] = np.eye(4)

    def wake(X, t):
        head, s, r = wake_curves(t)
        biped_sleep(X, P, s, head, 0.0)
        for side, sg in SIDES:
            X["Arm" + side] = X["Arm" + side] @ rz(sg * 72 * r) @ rx(22 * r)
        X["Body"] = X["Body"] @ rx(8 * r) @ rz(shake(t, 1.6) * r)
        X["Head"] = X["Head"] @ rx(16 * r) @ ry(shake(t, 3.0, 7.0) * r)
        if P.get("key"):                                   # the wind-up key spins up
            X["Key"] = rz(-360.0 * 4 * (t / WAKE_LEN) ** 2)

    def run(X, t):
        T, A = P["T"], P["A"]
        ph = TAU * t / T
        for (side, sg), o in zip(SIDES, (0.0, math.pi)):
            a = A * math.sin(ph + o)
            up = 0.32 * max(0.0, math.cos(ph + o)) + foot_comp(a, *P["foot"])
            X["Leg" + side] = tr(0, up, 0) @ rx(a)
            X["Arm" + side] = rx(-P["arm"] * math.sin(ph + o)) @ rz(sg * 6)
        bob = -P["bob"] * (0.5 + 0.5 * math.cos(2 * (ph - math.pi / 2 - 0.3)))
        X["Body"] = tr(0, bob, 0) @ rx(-6) @ ry(5 * math.sin(ph)) @ rz(-3 * math.cos(ph))
        X["Head"] = rx(4 + 2 * math.cos(2 * ph)) @ ry(-3 * math.sin(ph))
        if P.get("key"):
            X["Key"] = rz(-360.0 * t / T)
    T = P["T"]
    return [Clip("Sleep", SLEEP_LEN, True, 1, sleep, [(1.5, "Snore")], fps=SLEEP_FPS),
            Clip("Wake", WAKE_LEN, False, 2, wake, [(EYES_OPEN_AT, "EyesOpen"), (ROAR_AT, "Roar")]),
            Clip("Run", T, True, 1, run, [(T / 4, "Step"), (3 * T / 4, "Step")])]


# ==================================================================== four legs, galloping

def quad_sleep(X, P, s, head, br):
    d = P["drop"] * s
    k = fold_angle(P["hip"], P["heel"], P["hip"] - d)
    X["Body"] = tr(0, -d + 0.05 * br * s, 0) @ rx(1.5 * br * s)
    for side, sg in SIDES:
        X["LegF" + side] = rx(k) @ rz(sg * 4 * s)
        X["LegB" + side] = rx(k) @ rz(sg * 14 * s)
    X["Head"] = rx(-16 * head - 1.5 * br * head) @ ry(12 * head) @ rz(-6 * head)
    X["Jaw"] = rx(-2.0 * br * head)
    X["Tail"] = rx(50 * s) @ ry(-45 * s)


def quad(P):
    def sleep(X, t):
        quad_sleep(X, P, 1.0, 1.0, breath(t))

    def wake(X, t):
        head, s, r = wake_curves(t)
        quad_sleep(X, P, s, head, 0.0)
        X["Body"] = X["Body"] @ rx(5 * r)
        X["Head"] = X["Head"] @ rx(20 * r) @ rz(shake(t, 2.0) * r)
        X["Jaw"] = X["Jaw"] @ rx(-30 * r)
        X["Tail"] = X["Tail"] @ rx(-40 * r) @ ry(15 * math.sin(TAU * 3 * t) * r)
        for side, sg in SIDES:
            X["LegF" + side] = X["LegF" + side] @ rx(8 * r)

    def run(X, t):
        T, A = P["T"], P["A"]
        u = t / T
        for leg, p0 in (("LegFL", 0.0), ("LegFR", 0.08), ("LegBL", 0.5), ("LegBR", 0.58)):
            ph = TAU * (u - p0)
            X[leg] = tr(0, 0.25 * max(0.0, math.cos(ph)), 0) @ rx(A * math.sin(ph))
        X["Body"] = tr(0, 0.18 + 0.16 * math.sin(TAU * u + 0.6), 0) @ rx(4 * math.cos(TAU * u))
        X["Head"] = rx(-5 * math.cos(TAU * u)) @ ry(2 * math.sin(TAU * u))
        X["Jaw"] = rx(-10 - 4 * math.sin(2 * TAU * u))
        X["Tail"] = rx(-25 + 6 * math.sin(2 * TAU * u)) @ ry(8 * math.sin(TAU * u))
    T = P["T"]
    return [Clip("Sleep", SLEEP_LEN, True, 1, sleep, [(1.5, "Snore")], fps=SLEEP_FPS),
            Clip("Wake", WAKE_LEN, False, 2, wake, [(EYES_OPEN_AT, "EyesOpen"), (ROAR_AT, "Roar")]),
            Clip("Run", T, True, 1, run, [(T / 4, "Step"), (3 * T / 4, "Step")])]


# ==================================================================== many legs, scuttling

def crawl_sleep(X, P, s, head, br):
    d = P["drop"] * s
    X["Body"] = tr(0, -d + 0.04 * br * s, 0)
    lift = P["lift_sleep"] * s
    n = P["pairs"]
    for side, sg in SIDES:
        for i in range(1, n + 1):
            spread = (i - (n + 1) / 2.0) * 6.0                  # front legs reach forward, back ones back
            X["Leg%s%d" % (side, i)] = rz(sg * lift) @ ry(-sg * spread * s)
        if P.get("claws"):
            X["Claw" + side] = ry(sg * 22 * s) @ rx(-8 * s)
    kind = P["kind"]
    if kind == "scorpion":
        X["Tail"] = rx(38 * s)
        X["Sting"] = rx(16 * s + 3 * br * s)
        X["Head"] = rx(-8 * head)
    elif kind == "crab":
        X["Head"] = rx(-45 * head)
    elif kind == "spider":
        X["Head"] = rx(4 * head)
    else:
        X["Head"] = rx(-12 * head)
    if kind == "beetle":
        X["Gear"] = np.eye(4)


def crawler(P):
    def sleep(X, t):
        crawl_sleep(X, P, 1.0, 1.0, breath(t))

    def wake(X, t):
        head, s, r = wake_curves(t)
        crawl_sleep(X, P, s, head, 0.0)
        snap = math.sin(TAU * 6 * t)
        X["Body"] = X["Body"] @ tr(0, 0.25 * r, 0) @ rx(7 * r)
        if P.get("claws"):
            for side, sg in SIDES:
                X["Claw" + side] = X["Claw" + side] @ rx(30 * r) @ ry(-sg * (18 + 8 * snap) * r)
        kind = P["kind"]
        if kind == "scorpion":
            X["Head"] = X["Head"] @ rx(6 * r)
            X["Tail"] = X["Tail"] @ rx(-18 * r)
            X["Sting"] = X["Sting"] @ rx((-30 + 15 * snap) * r)
        elif kind == "crab":
            X["Head"] = X["Head"] @ tr(0, 0.35 * r, 0) @ ry(8 * math.sin(TAU * 3 * t) * r)
        elif kind == "spider":
            for side, sg in SIDES:
                X["Leg%s1" % side] = X["Leg%s1" % side] @ rz(sg * 42 * r)
                X["Leg%s2" % side] = X["Leg%s2" % side] @ rz(sg * 24 * r)
            X["Head"] = X["Head"] @ rx(10 * r)
        elif kind == "beetle":
            X["Head"] = X["Head"] @ rx(18 * r)
            X["Gear"] = rx(-360.0 * 3 * (t / WAKE_LEN) ** 2)

    def run(X, t):
        T, A, Lf, n = P["T"], P["A"], P["lift"], P["pairs"]
        ph = TAU * t / T
        for side, sg in SIDES:
            for i in range(1, n + 1):
                grp = (i + (0 if side == "L" else 1)) % 2
                q = ph - math.pi * grp
                X["Leg%s%d" % (side, i)] = rz(sg * Lf * max(0.0, math.cos(q))) @ ry(sg * A * math.sin(q))
            if P.get("claws"):
                X["Claw" + side] = rx(8 + 4 * math.sin(2 * ph)) @ ry(sg * 6 * math.sin(2 * ph + sg))
        X["Body"] = tr(0, 0.07 * math.cos(2 * ph), 0) @ ry(2.5 * math.sin(ph))
        kind = P["kind"]
        if kind == "scorpion":
            X["Tail"] = rx(4 * math.sin(ph)) @ ry(6 * math.sin(ph))
            X["Sting"] = rx(8 * math.sin(ph + 1.2))
            X["Head"] = rx(2 * math.sin(2 * ph))
        elif kind == "crab":
            X["Head"] = tr(0, 0.06 * math.sin(2 * ph), 0) @ ry(6 * math.sin(ph))
        elif kind == "beetle":
            X["Gear"] = rx(-360.0 * t / T)
            X["Head"] = rx(2 * math.sin(2 * ph))
        else:
            X["Head"] = rx(3 * math.sin(2 * ph))
    T = P["T"]
    return [Clip("Sleep", SLEEP_LEN, True, 1, sleep, [(1.5, "Snore")], fps=SLEEP_FPS),
            Clip("Wake", WAKE_LEN, False, 2, wake, [(EYES_OPEN_AT, "EyesOpen"), (ROAR_AT, "Roar")]),
            Clip("Run", T, True, 1, run, [(T / 4, "Step"), (3 * T / 4, "Step")])]


# ==================================================================== Meadow: the scarecrow hops on its pole

def scarecrow_clips():
    T, LAND = 0.7, 0.85

    def pose(X, s, head, br, t):
        X["Body"] = rz(3 * s) @ rx(-3 * s)
        X["Head"] = rx(-24 * head - 2 * br * head) @ rz(12 * head)
        for side, sg in SIDES:
            X["Arm" + side] = rz(-sg * 28 * s)
            X["Leg" + side] = np.eye(4)
        X["Hat"] = rz(-6 * s)
        X["Crow"] = np.eye(4)

    def sleep(X, t):
        pose(X, 1.0, 1.0, breath(t), t)
        peck = max(math.exp(-((t - 0.8) / 0.07) ** 2), math.exp(-((t - 1.05) / 0.07) ** 2),
                   math.exp(-((t - 2.2) / 0.07) ** 2))              # the crow keeps watch, pecking
        X["Crow"] = rx(-35 * peck) @ ry(25 * math.sin(TAU * t / SLEEP_LEN))

    def wake(X, t):
        head, s, r = wake_curves(t)
        pose(X, s, head, 0.0, t)
        hop = 0.9 * arc(t, 0.3, 0.7)
        X["Body"] = tr(0, hop, 0) @ X["Body"]
        for side, sg in SIDES:
            X["Arm" + side] = X["Arm" + side] @ rz(sg * (35 * arc(t, 0.25, 0.75) + (25 + 12 * math.sin(TAU * 4 * t)) * r))
            X["Leg" + side] = rx(-sg * 18 * arc(t, 0.3, 0.7))
        fly = arc(t, 0.15, 0.95)                                    # the crow flies up off the hat and lands
        X["Crow"] = tr(0.3 * fly, 1.6 * fly, 0) @ rz(-15 * fly) @ rx(10 * math.sin(TAU * 6 * t) * fly)
        X["Head"] = X["Head"] @ rx(10 * r) @ rz(shake(t, 4.0) * r)

    def run(X, t):
        u = t / T
        v = min(1.0, max(0.0, (u - 0.15) / (LAND - 0.15)))
        env = math.sin(math.pi * v)
        h = 1.6 * arc(u, 0.15, LAND)
        squash = 0.12 * (arc(u, LAND, 1.0) + arc(u, 0.0, 0.15))
        X["Body"] = tr(0, h - squash, 0) @ rx(-6 * env - 8 * squash / 0.12)
        for side, sg in SIDES:
            X["Leg" + side] = rx(-22 * math.cos(math.pi * v) * env)
            X["Arm" + side] = rz(sg * (18 * env + 5 * math.sin(TAU * 3 * u) * env))
        X["Head"] = rx(6 * env - 6 * squash / 0.12)
        X["Hat"] = tr(0, 0.15 * max(0.0, v - 0.5) * 2 * env, 0)
        X["Crow"] = rx(-10 * env)
    return [Clip("Sleep", SLEEP_LEN, True, 1, sleep, [(1.5, "Snore")], fps=SLEEP_FPS),
            Clip("Wake", WAKE_LEN, False, 2, wake, [(EYES_OPEN_AT, "EyesOpen"), (ROAR_AT, "Roar")]),
            Clip("Run", T, True, 1, run, [(LAND * T, "Land")])]


# ==================================================================== Marsh: the bog frog

def frog_clips():
    T, LAND = 0.65, 0.8

    def pose(X, s, head, br):
        X["Body"] = tr(0, -0.12 * s + 0.05 * br * s, 0) @ rx(4 * s)
        X["Head"] = rx(-10 * head)
        X["Jaw"] = rx(-2.5 * br * s)
        for side, sg in SIDES:
            X["Arm" + side] = rx(10 * s)
            X["Leg" + side] = np.eye(4)

    def sleep(X, t):
        pose(X, 1.0, 1.0, breath(t))

    def wake(X, t):
        head, s, r = wake_curves(t)
        pose(X, s, head, 0.0)
        croak = r * (0.75 + 0.25 * math.sin(TAU * 5 * t))
        X["Jaw"] = X["Jaw"] @ rx(-35 * croak)
        X["Body"] = X["Body"] @ tr(0, 0.2 * r, 0) @ rx(8 * r)
        X["Head"] = X["Head"] @ rx(10 * r)

    def run(X, t):
        u = t / T
        v = min(1.0, max(0.0, (u - 0.12) / (LAND - 0.12)))
        h = 2.0 * arc(u, 0.12, LAND)
        crouch = 0.2 * arc(u, 0.0, 0.12) + 0.15 * arc(u, LAND, 1.0)
        pitch = 0.0
        if 0.12 < u < LAND:
            pitch = 16 * math.sin(TAU * v) if v < 0.5 else 8 * math.sin(TAU * v)
        X["Body"] = tr(0, h - crouch, 0) @ rx(pitch)
        ext = min(ease(0.0, 1.0, v, 0.0, 0.25, "out"), max(0.0, h - 0.2) / 2.4) * (1.0 - ease(0.0, 1.0, v, 0.5, 0.9))
        for side, sg in SIDES:
            X["Leg" + side] = rx(-45 * ext)
            reach = ease(0.0, 1.0, v, 0.5, 0.9) if u < LAND else 1.0 - ease(0.0, 1.0, u, LAND, 1.0)
            X["Arm" + side] = rx(35 * reach)
        X["Head"] = rx(-4 * math.sin(TAU * v))
        X["Jaw"] = np.eye(4)
    return [Clip("Sleep", SLEEP_LEN, True, 1, sleep, [(1.5, "Snore")], fps=SLEEP_FPS),
            Clip("Wake", WAKE_LEN, False, 2, wake, [(EYES_OPEN_AT, "EyesOpen"), (ROAR_AT, "Roar")]),
            Clip("Run", T, True, 1, run, [(LAND * T, "Land")])]


# ==================================================================== Candy: the jelly slime

def slime_clips():
    T, UP, LAND = 0.6, 0.15, 0.75

    def sleep(X, t):
        br = breath(t)
        X["Body"] = np.eye(4)
        X["Top"] = tr(0, -0.35 + 0.12 * br, 0) @ rz(2 * math.sin(TAU * t / SLEEP_LEN))
        X["Head"] = rx(-6)

    def wake(X, t):
        head, s, r = wake_curves(t)
        wob = math.exp(-2.5 * max(0.0, t - 0.3)) * math.sin(TAU * 3 * t) if t > 0.3 else 0.0
        X["Top"] = tr(0, -0.35 * s + 0.7 * r, 0) @ rz(10 * wob)
        X["Body"] = tr(0, 0.9 * arc(t, 0.85, 1.2), 0)
        X["Head"] = rx(-6 * head + 6 * r)

    def run(X, t):
        u = t / T
        v = min(1.0, max(0.0, (u - UP) / (LAND - UP)))
        squash = arc(u, 0.0, UP) + arc(u, LAND, 1.0)
        stretch = arc(u, UP, UP + 0.3)
        X["Body"] = tr(0, 1.6 * arc(u, UP, LAND), 0)
        X["Top"] = tr(0, -0.5 * squash + 0.35 * stretch, 0) @ rx(-6 * math.sin(math.pi * v))
        X["Head"] = rx(4 * math.sin(math.pi * v))
    return [Clip("Sleep", SLEEP_LEN, True, 1, sleep, [(1.5, "Snore")], fps=SLEEP_FPS),
            Clip("Wake", WAKE_LEN, False, 2, wake, [(EYES_OPEN_AT, "EyesOpen"), (ROAR_AT, "Roar")]),
            Clip("Run", T, True, 1, run, [(LAND * T, "Land")])]


# ==================================================================== Void: the glitch cube

def glitch(k, salt):
    """A jumpy value in -1..1 that changes every other key."""
    k = k // 2
    return ((k * 7919 + salt * 104729) % 13 - 6) / 6.0


def cube_clips():
    T, UP, LAND = 0.6, 0.1, 0.8

    def sleep(X, t):
        br = breath(t)
        X["Body"] = tr(0, 0.03 * br, 0)
        X["SliceMid"] = ry(4)
        X["SliceTop"] = ry(-3)
        X["Head"] = np.eye(4)
        X["Bits"] = tr(0, -1.2 + 0.15 * br, 0) @ ry(360.0 * t / SLEEP_LEN)

    def wake(X, t):
        head, s, r = wake_curves(t)
        k = int(round(t * 30))
        g = 1.0 if 0.3 <= t <= 1.0 else 0.0
        X["Body"] = tr(0, 1.1 * arc(t, 1.0, 1.35), 0)
        X["SliceMid"] = tr(0.5 * glitch(k, 1) * g, 0, 0) @ ry(4 * s)
        X["SliceTop"] = tr(0.6 * glitch(k, 2) * g, 0, 0.3 * glitch(k, 3) * g) @ ry(-3 * s)
        X["Head"] = tr(0.15 * glitch(k, 4) * g, 0, 0)
        X["Bits"] = tr(0.4 * glitch(k, 5) * g, -1.2 * s + 0.3 * glitch(k, 6) * g, 0) @ ry(-360.0 * (1 - s))

    def run(X, t):
        u = t / T
        k = int(round(t * 30))
        snap = 1.0 if 0.45 <= u <= 0.55 else 0.0
        X["Body"] = tr(0, 1.4 * arc(u, UP, LAND), 0)
        X["SliceMid"] = ry(15 * math.sin(TAU * u))
        X["SliceTop"] = tr(0.5 * snap, 0, 0) @ ry(-15 * math.sin(TAU * u))
        X["Head"] = tr(0.12 * glitch(k, 7) * snap, 0, 0)
        X["Bits"] = tr(0, 0.25 * math.sin(TAU * u), 0) @ ry(-360.0 * u)
    return [Clip("Sleep", SLEEP_LEN, True, 1, sleep, [(1.5, "Snore")], fps=SLEEP_FPS),
            Clip("Wake", WAKE_LEN, False, 2, wake, [(EYES_OPEN_AT, "EyesOpen"), (ROAR_AT, "Roar")]),
            Clip("Run", T, True, 1, run, [(LAND * T, "Land")])]


# ==================================================================== Haunt: the ghost

def ghost_clips():
    T = 1.0

    def pose(X, s, head, br, t):
        X["Body"] = tr(0, -0.9 * s + 0.12 * br * s, 0) @ rx(-6 * s)
        X["Head"] = rx(-14 * head) @ rz(8 * head)
        for side, sg in SIDES:
            X["Arm" + side] = rz(-sg * 25 * s)
        X["Tail"] = ry(10 * math.sin(TAU * t / SLEEP_LEN) * s)

    def sleep(X, t):
        pose(X, 1.0, 1.0, breath(t), t)

    def wake(X, t):
        head, s, r = wake_curves(t)
        pose(X, s, head, 0.0, 0.0)
        X["Body"] = X["Body"] @ tr(0, 0.4 * r, 0) @ rx(-8 * r)
        X["Head"] = X["Head"] @ rx(8 * r) @ rz(shake(t, 3.0) * r)
        for side, sg in SIDES:
            X["Arm" + side] = X["Arm" + side] @ rz(sg * 70 * r) @ rx(20 * r)
        X["Tail"] = X["Tail"] @ ry(20 * math.sin(TAU * 3 * t) * r)

    def run(X, t):
        u = t / T
        X["Body"] = tr(0, 0.25 * math.sin(TAU * u), 0) @ rx(-14 + 2 * math.sin(TAU * u)) @ rz(3 * math.sin(TAU * u))
        X["Head"] = rx(10) @ ry(4 * math.sin(TAU * u))
        for side, sg in SIDES:
            X["Arm" + side] = rx(-35 + 10 * math.sin(TAU * u + sg)) @ rz(-sg * 10)
        X["Tail"] = rx(-25 + 10 * math.sin(2 * TAU * u)) @ ry(12 * math.sin(TAU * u))
    return [Clip("Sleep", SLEEP_LEN, True, 1, sleep, [(1.5, "Snore")], fps=SLEEP_FPS),
            Clip("Wake", WAKE_LEN, False, 2, wake, [(EYES_OPEN_AT, "EyesOpen"), (ROAR_AT, "Roar")]),
            Clip("Run", T, True, 1, run)]


# ==================================================================== Neon: the patrol drone

ROTORS = (("RotorFL", 1.0), ("RotorFR", -1.0), ("RotorBL", -1.0), ("RotorBR", 1.0))


def drone_clips():
    T, SPIN = 0.6, 5.0                                           # rotor turns a second when flying

    def pose(X, s, head, br):
        X["Body"] = tr(0, -3.0 * s + 0.02 * br * s, 0) @ rx(4 * s) @ rz(-3 * s)
        X["Head"] = rx(-20 * head)

    def sleep(X, t):
        pose(X, 1.0, 1.0, breath(t))
        for nm, d in ROTORS:
            X[nm] = np.eye(4)

    def wake(X, t):
        head, s0, r = wake_curves(t)
        s = 1.0 - ease(0.0, 1.0, t, 0.4, 1.0)                      # lifts off once its rotors are going
        pose(X, s, head, 0.0)
        turns = 4.0 * (t / WAKE_LEN) ** 2                          # spins up to 4 whole turns, ending square
        for nm, d in ROTORS:
            X[nm] = ry(d * 360.0 * turns)
        scan = 30 * math.sin(TAU * t / 0.7) * ease(0.0, 1.0, t, 0.6, 0.9) * (1 - ease(0.0, 1.0, t, 1.2, 1.5))
        X["Head"] = X["Head"] @ ry(scan)
        X["Body"] = X["Body"] @ tr(0, 0.3 * r, 0)

    def run(X, t):
        u = t / T
        X["Body"] = tr(0, 0.18 * math.sin(TAU * u), 0) @ rx(-14) @ rz(4 * math.sin(TAU * u))
        X["Head"] = rx(8) @ ry(22 * math.sin(TAU * u))
        for nm, d in ROTORS:
            X[nm] = ry(d * 360.0 * SPIN * t)
    return [Clip("Sleep", SLEEP_LEN, True, 1, sleep, fps=SLEEP_FPS),
            Clip("Wake", WAKE_LEN, False, 2, wake, [(EYES_OPEN_AT, "EyesOpen"), (ROAR_AT, "Roar")]),
            Clip("Run", T, True, 1, run)]


# ==================================================================== Cloud: the storm cloud

def cloud_clips():
    T = 0.8

    def pose(X, s, head, br, t):
        X["Body"] = tr(0, -0.5 * s + 0.1 * br * s, 0)
        for side, sg in SIDES:
            X["Puff" + side] = tr(sg * 0.12 * br * s, 0, 0)
        X["Head"] = rx(-6 * head)
        X["Bolt"] = tr(0, 2.6 * s, 0)                              # tucked up inside the cloud
        X["Rain"] = tr(0, -0.8 * frac(t / 1.5) * s, 0)             # a drizzle

    def sleep(X, t):
        pose(X, 1.0, 1.0, breath(t), t)

    def wake(X, t):
        head, s, r = wake_curves(t)
        pose(X, s, head, 0.0, 0.0)
        rumble = ease(0.0, 1.0, t, 0.2, 0.5) * (1 - ease(0.0, 1.0, t, 1.2, 1.5))
        X["Body"] = X["Body"] @ tr(shake(t, 0.08, 9.0) * rumble, 0, 0)
        for side, sg in SIDES:
            X["Puff" + side] = X["Puff" + side] @ tr(sg * 0.6 * r, 0.2 * r, 0)
        sb = 1.0 - ease(0.0, 1.0, t, 0.55, 0.8)
        X["Bolt"] = tr(0, 2.6 * sb, 0) @ rz(10 * math.sin(TAU * 8 * t) * r)
        X["Rain"] = tr(0, -2.0 * frac(t / 0.5) * rumble, 0)

    def run(X, t):
        u = t / T
        X["Body"] = tr(0, 0.2 * math.sin(TAU * u), 0) @ rx(-10) @ rz(3 * math.sin(TAU * u))
        for side, sg in SIDES:
            X["Puff" + side] = tr(sg * 0.25 * math.sin(2 * TAU * u), 0, 0)
        X["Head"] = np.eye(4)
        X["Rain"] = tr(0, -2.0 * frac(2 * u), 0)
        X["Bolt"] = rz(8 * math.sin(4 * TAU * u)) @ tr(0.15 * math.sin(4 * TAU * u + 1), 0, 0)
    return [Clip("Sleep", SLEEP_LEN, True, 1, sleep, [(1.5, "Snore")], fps=SLEEP_FPS),
            Clip("Wake", WAKE_LEN, False, 2, wake, [(EYES_OPEN_AT, "EyesOpen"), (ROAR_AT, "Roar")]),
            Clip("Run", T, True, 1, run)]


# ==================================================================== Dino: the raptor

def raptor_clips():
    T, A = 0.5, 28.0

    def pose(X, s, head, br):
        X["Body"] = tr(0, -3.1 * s + 0.06 * br * s, 0) @ rx(4 * s)
        k = fold_angle(4.3, 0.0, 4.3 - 3.1 * s)
        for side, sg in SIDES:
            X["Leg" + side] = rx(k) @ rz(sg * 10 * s)
            X["Arm" + side] = rx(-20 * s)
        X["Head"] = rx(-30 * head - 1.5 * br * head) @ ry(15 * head)
        X["Jaw"] = np.eye(4)
        X["Tail"] = rx(12 * s) @ ry(-30 * s)
        X["TailTip"] = ry(-40 * s)

    def sleep(X, t):
        pose(X, 1.0, 1.0, breath(t))

    def wake(X, t):
        head, s, r = wake_curves(t)
        pose(X, s, head, 0.0)
        X["Body"] = X["Body"] @ rx(6 * r)
        X["Head"] = X["Head"] @ rx(25 * r) @ rz(shake(t, 2.5) * r)
        X["Jaw"] = rx(-35 * r)
        for side, sg in SIDES:
            X["Arm" + side] = X["Arm" + side] @ rz(sg * 20 * r)
        X["Tail"] = X["Tail"] @ rx(-15 * r)
        X["TailTip"] = X["TailTip"] @ ry(25 * math.sin(TAU * 3 * t) * r)

    def run(X, t):
        ph = TAU * t / T
        for (side, sg), o in zip(SIDES, (0.0, math.pi)):
            a = A * math.sin(ph + o)
            up = 0.35 * max(0.0, math.cos(ph + o)) + foot_comp(a, 4.3, -1.7, 0.0)
            X["Leg" + side] = tr(0, up, 0) @ rx(a)
            X["Arm" + side] = rx(6 * math.sin(ph + o + math.pi / 2))
        bob = 0.12 - 0.2 * (0.5 + 0.5 * math.cos(2 * (ph - math.pi / 2 - 0.3)))
        X["Body"] = tr(0, bob, 0) @ rx(-4 + 2 * math.cos(2 * ph)) @ rz(2 * math.sin(ph))
        X["Head"] = rx(3 - 2 * math.cos(2 * ph)) @ ry(-2 * math.sin(ph))
        X["Jaw"] = rx(-8 - 4 * math.sin(2 * ph))
        X["Tail"] = ry(8 * math.sin(ph)) @ rx(-4 * math.cos(2 * ph))
        X["TailTip"] = ry(14 * math.sin(ph - 0.8))
    return [Clip("Sleep", SLEEP_LEN, True, 1, sleep, [(1.5, "Snore")], fps=SLEEP_FPS),
            Clip("Wake", WAKE_LEN, False, 2, wake, [(EYES_OPEN_AT, "EyesOpen"), (ROAR_AT, "Roar")]),
            Clip("Run", T, True, 1, run, [(T / 4, "Step"), (3 * T / 4, "Step")])]


# ==================================================================== who does what

def _quad(hip_y, heel, belly, T, A):
    return dict(hip=hip_y, heel=heel, drop=belly - 0.05, T=T, A=A)


def _crawl(kind, pairs, hip_y, reach, belly, T, A, lift, claws=False):
    drop = belly - 0.05
    return dict(kind=kind, pairs=pairs, drop=drop, T=T, A=A, lift=lift, claws=claws,
                lift_sleep=leg_lift_angle(hip_y, drop, reach, 0.05 - hip_y), reach=reach)


QUADS = {"Jungle": _quad(3.2, 0.55, 1.85, 0.5, 36.0), "Cosmic": _quad(3.1, 0.5, 1.85, 0.5, 36.0),
         "Olympus": _quad(3.3, 0.58, 2.0, 0.55, 34.0)}
CRAWLS = {"Dunes": _crawl("scorpion", 3, 1.45, 2.0, 1.1, 0.4, 25.0, 18.0, claws=True),
          "Reef": _crawl("crab", 3, 2.1, 2.3, 1.32, 0.45, 22.0, 18.0, claws=True),
          "Crystal": _crawl("spider", 4, 2.5, 3.5, 1.35, 0.45, 22.0, 20.0),
          "Clock": _crawl("beetle", 3, 2.0, 2.0, 1.4, 0.4, 25.0, 18.0)}
BIPEDS = {"Frost": dict(T=0.8, A=30.0, arm=24.0, bob=0.22, foot=(2.6, -1.4, 1.0)),
          "Lava": dict(T=0.8, A=30.0, arm=24.0, bob=0.24, foot=(2.7, -1.5, 1.1)),
          "Toy": dict(T=0.6, A=32.0, arm=30.0, bob=0.16, key=True, foot=(2.7, -1.4, 0.9))}


def run_speed():
    """Studs a second each Run is made for (where its feet would not slide)."""
    out = {}
    for a, P in BIPEDS.items():
        hip = {"Frost": 2.6, "Lava": 2.7, "Toy": 2.7}[a]
        out[a] = 4 * hip * math.sin(math.radians(P["A"])) / P["T"]
    for a, P in QUADS.items():
        hip = {"Jungle": 3.2, "Cosmic": 3.1, "Olympus": 3.3}[a]
        out[a] = 2 * hip * math.sin(math.radians(P["A"])) / (0.5 * P["T"])
    for a, P in CRAWLS.items():
        out[a] = 2 * P["reach"] * math.sin(math.radians(P["A"])) / (0.5 * P["T"])
    out["Dino"] = 4 * 4.3 * math.sin(math.radians(28.0)) / 0.5
    out.update({"Meadow": 7.0, "Marsh": 8.0, "Candy": 6.0, "Void": 6.0, "Haunt": 8.0, "Neon": 12.0, "Cloud": 7.0})
    return {a: round(v, 1) for a, v in out.items()}


RUN_SPEED = run_speed()

CLIPS = {"Meadow": scarecrow_clips(), "Dunes": crawler(CRAWLS["Dunes"]), "Marsh": frog_clips(),
         "Jungle": quad(QUADS["Jungle"]), "Reef": crawler(CRAWLS["Reef"]), "Frost": biped(BIPEDS["Frost"]),
         "Haunt": ghost_clips(), "Lava": biped(BIPEDS["Lava"]), "Crystal": crawler(CRAWLS["Crystal"]),
         "Dino": raptor_clips(), "Toy": biped(BIPEDS["Toy"]), "Candy": slime_clips(),
         "Clock": crawler(CRAWLS["Clock"]), "Neon": drone_clips(), "Cloud": cloud_clips(),
         "Cosmic": quad(QUADS["Cosmic"]), "Void": cube_clips(), "Olympus": quad(QUADS["Olympus"])}
