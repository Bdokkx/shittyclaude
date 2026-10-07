"""Remade R6 animations for the Sequences folder (animations.rbxm).

Same names, lengths, Loop and Priority as the originals so scripts and timings keep working; Slash still only
poses Torso + arms (Action2 overlay that runs on top of movement). What changed:
  - the originals used Constant easing on every limb, so they snapped from key to key -> smooth CubicV2 easing
    (one-shots) and densely baked cycles (loops)
  - locomotion has real mechanics: opposite arm/leg swing with a little lag, body bob that is lowest at contact,
    torso twist + sway over the stance leg, the head stabilised against the body
  - one-shots get anticipation, overshoot and settle; emotes get secondary motion (head, torso, off arm)

Notation, character space (see r6.py): T = Torso, H = Head, RA/LA/RL/LL = arms/legs.
  T rot x<0 leans forward, y>0 turns left, z>0 leans left; T offset y<0 crouches (offsets in studs)
  arms/legs rot x>0 swings forward; RA/RL z>0 and LA/LL z<0 lift out to the side
  H rot x>0 looks up, y>0 looks left, z>0 tilts left
"""
import math

from r6 import CF, to_transform

PARTS = {"T": "Torso", "H": "Head", "RA": "Right Arm", "LA": "Left Arm", "RL": "Right Leg", "LL": "Left Leg"}
REST = {"T": (0, 0, 0), "H": (0, 0, 0), "RA": (0, 0, 3), "LA": (0, 0, -3), "RL": (0, 0, 1), "LL": (0, 0, -1)}
TAU = 2 * math.pi


def S(p, k=1.0, ph=0.0):
    return math.sin(TAU * (k * p + ph))


def C(p, k=1.0, ph=0.0):
    return math.cos(TAU * (k * p + ph))


def norm(v):
    """part value -> (rot, offset)"""
    if len(v) == 2 and isinstance(v[0], (tuple, list)):
        return tuple(v[0]), tuple(v[1])
    return tuple(v), (0.0, 0.0, 0.0)


def planted(pose):
    """Keep the feet under the body when the torso pitches: the root joint is the torso centre, so leaning
    by `a` swings the hips the other way and tilts the legs. Counter-rotate the legs and shift the torso."""
    (tx, ty, tz), (ox, oy, oz) = pose["T"]
    a = math.radians(tx)
    out = dict(pose)
    out["T"] = ((tx, ty, tz), (ox, oy - (1 - math.cos(a)), oz + math.sin(a)))
    for leg in ("RL", "LL"):
        (x, y, z), off = pose[leg]
        out[leg] = ((x - tx, y, z), off)
    return out


class Seq:
    def __init__(self, name, length, loop, priority, parts=tuple(PARTS), plant=False, containers=()):
        self.name, self.length, self.loop, self.priority, self.parts = name, length, loop, priority, parts
        self.plant = plant
        self.containers = containers    # parts exported as unkeyed (identity, Weight 0) parents
        self.keys = []          # (time, {part: (rot, off)} as authored, style, direction, plant)

    def key(self, t, style="CubicV2", direction="InOut", rest=False, plant=None, **parts):
        """Pose at time t; parts not given carry over from the previous key (or rest).
        plant: keep feet under the body (defaults to the sequence setting)."""
        prev = {k: norm(v) for k, v in REST.items()} if (rest or not self.keys) else dict(self.keys[-1][1])
        for k, v in parts.items():
            prev[k] = norm(v)
        self.keys.append((round(t, 4), prev, style, direction, self.plant if plant is None else plant))
        return self

    def resolved(self, i):
        t, pose, style, d, plant = self.keys[i]
        return planted(pose) if plant else pose

    def cycle(self, fn, samples):
        """Loop baked from a function of phase 0..1 -> {part: value}; last key == first key."""
        for i in range(samples + 1):
            p = (i % samples) / samples
            self.key(i * self.length / samples, "Linear", "InOut", rest=True, **fn(p))
        return self

    def spin(self, t0, t1, a0, a1, pose_fn, steps=10):
        """Eased turn of the torso from yaw a0 to a1 (any number of turns), keyed every <=110 degrees."""
        for i in range(1, steps + 1):
            u = i / steps
            e = 4 * u ** 3 if u < 0.5 else 1 - (-2 * u + 2) ** 3 / 2
            yaw = a0 + (a1 - a0) * e
            self.key(t0 + (t1 - t0) * u, "Linear", "InOut", **pose_fn(u, yaw))
        return self

    # -------------------------------------------------------------- output
    def to_json(self):
        assert abs(self.keys[-1][0] - self.length) < 1e-6, (self.name, self.keys[-1][0], self.length)
        kfs = []
        for i, (t, _, style, d, _) in enumerate(self.keys):
            pose = self.resolved(i)
            poses = {}
            for k in self.parts:
                if k in self.containers:
                    poses[PARTS[k]] = dict(cf=CF().components(), style="Linear", dir="In", weight=0)
                    continue
                T = to_transform(PARTS[k], *pose[k])
                poses[PARTS[k]] = dict(cf=[round(c, 6) for c in T.components()], style=style, dir=d, weight=1)
            kfs.append(dict(time=t, poses=poses))
        return dict(name=self.name, loop=self.loop, priority=self.priority, length=self.length, keyframes=kfs)

    def as_dump(self):
        """Same shape as the dump of the original file, for r6.sample()."""
        kfs = []
        for k in self.to_json()["keyframes"]:
            torso = None
            kids = []
            for name, p in k["poses"].items():
                node = dict(name=name, cf=p["cf"], style=p["style"], dir=p["dir"], kids=[])
                if name == "Torso":
                    torso = node
                else:
                    kids.append(node)
            if torso:
                torso["kids"] = kids
                top = [torso]
            else:
                top = kids
            kfs.append(dict(time=k["time"], poses=[dict(name="HumanoidRootPart", cf=CF().components(),
                                                        style="Linear", dir="In", kids=top)]))
        return dict(name=self.name, keyframes=kfs)


# ================================================================== locomotion (loops)

def walk():
    def f(p):
        s, lag = S(p), S(p, ph=-0.04)
        spread = (1 - C(p, 2)) / 2                        # 0 when legs pass, 1 at contact
        return dict(
            T=((-4 - 1.5 * spread, -5 * lag, 2.0 * C(p)), (-0.07 * C(p), -0.13 * spread, 0)),
            H=(3 + 1.5 * spread, 4 * lag, -1.5 * C(p)),
            RA=(-24 * lag + 2, 0, 6 - 2 * min(0, lag)), LA=(24 * lag + 2, 0, -6 + 2 * max(0, lag)),
            RL=(30 * s, 0, 1.5 - 2 * C(p)), LL=(-30 * s, 0, -1.5 - 2 * C(p)))
    return Seq("Walk", 0.86, True, "Movement", plant=True).cycle(f, 16)


def sprint():
    def f(p):
        s, lag = S(p), S(p, ph=-0.035)
        spread = (1 - C(p, 2)) / 2
        return dict(
            T=((-16 - 4 * spread, -11 * lag, 3 * C(p)), (-0.06 * C(p), -0.2 * spread + 0.06, 0)),
            H=(14 + 3 * spread, 9 * lag, -2 * C(p)),
            RA=(-58 * lag + 14, 0, 9), LA=(58 * lag + 14, 0, -9),
            RL=(50 * s + 6, 0, 2 - 3 * C(p)), LL=(-50 * s + 6, 0, -2 - 3 * C(p)))
    return Seq("Sprint", 0.56, True, "Movement", plant=True).cycle(f, 16)


def catcher_run():
    """Chaser run: hunched, head up on the target, arms reaching forward in turns like grabbing."""
    def f(p):
        s, lag = S(p), S(p, ph=-0.05)
        spread = (1 - C(p, 2)) / 2
        return dict(
            T=((-24 - 4 * spread, -13 * lag, 3 * C(p)), (-0.06 * C(p), -0.22 * spread + 0.04, 0)),
            H=(24 + 4 * spread, 11 * lag, -2 * C(p)),
            RA=(78 - 32 * lag, 0, 16 + 6 * lag), LA=(78 + 32 * lag, 0, -16 + 6 * lag),
            RL=(46 * s + 5, 0, 2 - 3 * C(p)), LL=(-46 * s + 5, 0, -2 - 3 * C(p)))
    return Seq("CatcherRun", 0.60, True, "Movement", plant=True).cycle(f, 16)


def idle():
    def f(p):
        br, br_lag = S(p, 2), S(p, 2, -0.06)               # two breaths per loop, arms follow late
        sway, look = S(p, 1, 0.25), S(p, 1, -0.1)
        return dict(
            T=((-1 + 1.2 * br, 3 * S(p), 1.2 * sway), (0.03 * sway, 0.035 * br, 0)),
            H=(1 - 1.6 * br + 2 * S(p, 1, 0.4), 11 * look, 2 * S(p, 1, 0.1)),
            RA=(2 + 2.5 * S(p, 1, -0.05), 0, 6 + 1.8 * br_lag), LA=(2 - 2.5 * S(p, 1, -0.05), 0, -6 - 1.8 * br_lag),
            RL=(1, 0, 2 - 1.2 * sway), LL=(1, 0, -2 - 1.2 * sway))
    return Seq("Idle", 3.2, True, "Idle", plant=True).cycle(f, 24)


def jump():
    def f(p):
        return dict(
            T=((-5 + 2 * S(p), 0, 0), (0, 0.12, 0)),
            H=(12 + 2 * S(p, 1, -0.1), 0, 0),
            RA=(18 + 4 * S(p, 1, -0.1), 0, 138 + 7 * S(p)), LA=(18 + 4 * S(p, 1, 0.4), 0, -134 - 7 * S(p, 1, 0.5)),
            RL=(56 + 4 * S(p), 0, 4), LL=(-16 - 3 * S(p, 1, 0.3), 0, -5))
    return Seq("Jump", 0.28, True, "Movement").cycle(f, 8)


def fall():
    def f(p):
        return dict(
            T=((6 + 2 * S(p, 2), 0, 3 * S(p)), (0, 0, 0)),
            H=(-14 + 3 * S(p, 2, 0.2), 0, -3 * S(p)),
            RA=(10 + 10 * C(p), 0, 112 + 14 * S(p)), LA=(10 - 10 * C(p), 0, -112 + 14 * S(p)),
            RL=(8 + 22 * S(p, 1, 0.1), 0, 6), LL=(8 - 22 * S(p, 1, 0.1), 0, -6))
    return Seq("Fall", 0.26, True, "Movement").cycle(f, 8)


def slide():
    """Feet-first slide: leaning back on the left hand, right arm up for balance, eyes forward."""
    def f(p):
        j = S(p, 2)
        return dict(
            T=((50 + 1.5 * j, 10, 10), (0.1, -1.65 + 0.04 * j, 0.2)),
            H=(-40 - 1.5 * j, -8, -6),
            RA=(70 + 5 * S(p, 1, 0.2), 0, 38 + 4 * S(p, 2, 0.1)), LA=(-55, 0, -38),
            RL=(30 + 2 * j, 0, 6), LL=(24 - 2 * j, 0, -12))
    return Seq("Slide", 0.28, True, "Action").cycle(f, 8)


def land():
    q = Seq("Land", 0.26, False, "Action")
    q.key(0.00, "CubicV2", "Out", T=((-14, 0, 0), (0, -0.45, 0)), H=(6, 0, 0), RA=(24, 0, 44), LA=(24, 0, -44),
          RL=(28, 0, 16), LL=(28, 0, -16))
    q.key(0.06, T=((-18, 0, 0), (0, -0.55, 0)), H=(10, 0, 0), RA=(18, 0, 52), LA=(18, 0, -52),
          RL=(32, 0, 18), LL=(32, 0, -18))
    q.key(0.18, T=((2, 0, 0), (0, 0.04, 0)), H=(-2, 0, 0), RA=(-4, 0, 9), LA=(-4, 0, -9), RL=(0, 0, 2), LL=(0, 0, -2))
    q.key(0.26, rest=True)
    return q


# ================================================================== tag game actions

def pounce():
    q = Seq("Pounce", 0.46, False, "Action")
    q.key(0.00, "CubicV2", "Out", rest=True)
    q.key(0.07, "CubicV2", "In", T=((-20, 0, 0), (0, -0.45, 0)), H=(16, 0, 0), RA=(-55, 0, 20), LA=(-55, 0, -20),
          RL=(30, 0, 10), LL=(24, 0, -10))
    q.key(0.15, T=((-60, 0, 0), (0, 0.5, 0)), H=(42, 0, 0), RA=(165, 0, 12), LA=(158, 0, -12),
          RL=(-45, 0, 3), LL=(-28, 0, -5))
    q.key(0.30, T=((-24, 0, 0), (0, -0.35, 0)), H=(18, 0, 0), RA=(70, 0, 18), LA=(62, 0, -18),
          RL=(26, 0, 14), LL=(20, 0, -14))
    q.key(0.40, "CubicV2", "Out", T=((-3, 0, 0), (0, 0.02, 0)), H=(2, 0, 0), RA=(8, 0, 8), LA=(8, 0, -8),
          RL=(2, 0, 2), LL=(2, 0, -2))
    q.key(0.46, rest=True)
    return q


def slash():
    """Upper-body overlay (Action2): wind-up, fast diagonal strike, follow-through, recover. Arms only - the Torso
    stays an unkeyed container (Weight 0) like the original, so running/leaning underneath keeps playing."""
    q = Seq("Slash", 0.34, False, "Action2", parts=("T", "RA", "LA"), containers=("T",))
    q.key(0.00, "CubicV2", "In", RA=(158, 0, 30), LA=(-18, 0, -22))
    q.key(0.05, "CubicV2", "In", RA=(176, 0, 42), LA=(-26, 0, -28))
    q.key(0.12, "Linear", "InOut", RA=(92, 0, -10), LA=(-40, 0, -24))
    q.key(0.17, "CubicV2", "Out", RA=(24, 0, -44), LA=(-44, 0, -20))
    q.key(0.24, RA=(14, 0, -50), LA=(-36, 0, -16))
    q.key(0.34, RA=(24, 0, 4), LA=(-8, 0, -8))
    return q


def downed():
    """Lying face down, alternately reaching ahead and dragging (crawl), head up, weak leg kicks, breathing."""
    def f(p):
        return dict(
            T=((-90, 4 * C(p), 0), (0, -2.5 + 0.03 * S(p, 2), 0)),
            H=(32 + 5 * S(p, 1, 0.1), 14 * C(p), 4 * C(p)),
            RA=(8 * S(p), 0, 125 + 35 * C(p)), LA=(8 * S(p, 1, 0.5), 0, -125 - 35 * C(p, 1, 0.5)),
            RL=(-6 - 8 * (1 + S(p)) / 2, 0, 7), LL=(-6 - 8 * (1 + S(p, 1, 0.5)) / 2, 0, -8))
    return Seq("Downed", 1.6, True, "Action").cycle(f, 16)


def tagged():
    q = Seq("Tagged", 1.5, False, "Action")
    down = ((-90, 0, 0), (0, -2.5, 0))
    q.key(0.00, "CubicV2", "Out", rest=True)
    q.key(0.07, "CubicV2", "In", T=((22, 0, 0), (0, 0.25, 0)), H=(25, 0, 0), RA=(-10, 0, 110), LA=(-10, 0, -115),
          RL=(15, 0, 4), LL=(-10, 0, -4))
    q.key(0.24, "CubicV2", "Out", T=down, H=(15, 0, 0), RA=(0, 0, 95), LA=(0, 0, -90), RL=(0, 0, 8), LL=(0, 0, -8))
    q.key(0.30, T=((-84, 0, 0), (0, -2.3, 0)), H=(28, 0, 0), RA=(-15, 0, 85), LA=(-15, 0, -82),
          RL=(-12, 0, 8), LL=(-12, 0, -8))
    q.key(0.38, T=down, H=(22, 20, 0), RA=(0, 0, 90), LA=(0, 0, -88), RL=(-3, 0, 8), LL=(-3, 0, -8))
    q.key(0.55, H=(26, -10, -4))
    q.key(0.62, LL=(-45, 0, -6))
    q.key(0.70, H=(24, 25, 5), LL=(-5, 0, -8))
    q.key(0.80, RL=(-40, 0, 6))
    q.key(0.90, H=(22, 5, 0), RL=(-6, 0, 8))
    q.key(1.02, "CubicV2", "In", T=((-86, 0, 0), (0, -2.4, 0)), H=(20, 0, 0), RA=(25, 0, 62), LA=(25, 0, -62))
    q.key(1.12, T=((-55, 0, 0), (0, -1.7, 0)), H=(18, 0, 0), RA=(48, 0, 30), LA=(48, 0, -30),
          RL=(-25, 0, 6), LL=(-20, 0, -6))
    q.key(1.24, T=((-25, 0, 0), (0, -1.0, 0)), H=(10, 0, 0), RA=(30, 0, 25), LA=(40, 0, -20),
          RL=(-80, 0, 5), LL=(50, 0, -5))
    q.key(1.36, "CubicV2", "Out", T=((4, 0, 0), (0, 0.05, 0)), H=(-2, 0, 0), RA=(-4, 0, 8), LA=(-4, 0, -8),
          RL=(8, 0, 2), LL=(-4, 0, -2))
    q.key(1.50, rest=True)
    return q


# ================================================================== emotes

def wave():
    q = Seq("Wave", 1.75, False, "Action", plant=True)
    q.key(0.00, "CubicV2", "Out", rest=True)
    q.key(0.18, T=(0, -4, -4), H=(2, -10, -6), RA=(10, 0, 172), LA=(0, 0, -10))
    q.key(0.28, RA=(15, 0, 150))
    for i, t in enumerate((0.48, 0.68, 0.88, 1.08, 1.28)):
        a = i % 2 == 0
        q.key(t, T=(0, -4, -3 if a else -5), H=(2, -10, -4 if a else -8),
              RA=(14, -18 if a else 14, 128 if a else 162))
    q.key(1.36, RA=(15, 0, 150))
    q.key(1.52, "CubicV2", "In", T=(0, 0, 0), H=(0, 0, 0), RA=(-8, 0, -2), LA=(0, 0, -4))
    q.key(1.64, RA=(4, 0, 5))
    q.key(1.75, rest=True)
    return q


def spin_emote():
    q = Seq("Spin", 1.2, False, "Action", plant=True)
    q.key(0.00, "CubicV2", "Out", rest=True)
    q.key(0.12, "Linear", "InOut", T=((-6, -30, 0), (0, -0.3, 0)), RA=(30, 0, -10), LA=(30, 0, 10),
          RL=(12, 0, 8), LL=(12, 0, -8))

    def mid(u, yaw):
        arms = min(1.0, u / 0.15) * (1 - max(0.0, (u - 0.85) / 0.15) * 0.5)
        return dict(T=((0, yaw, 0), (0, -0.3 + 1.0 * math.sin(math.pi * u), 0)), H=(4 * math.sin(math.pi * u), 0, 0),
                    RA=(30 * (1 - arms), 0, -10 + 98 * arms), LA=(30 * (1 - arms), 0, 10 - 98 * arms),
                    RL=(4, 0, 4 + 20 * math.sin(math.pi * u)), LL=(4, 0, -4))
    q.spin(0.12, 0.82, -30, 720, mid, steps=10)
    q.key(0.92, T=((-8, 720, 0), (0, -0.35, 0)), H=(4, 0, 0), RA=(10, 0, 40), LA=(10, 0, -40),
          RL=(18, 0, 12), LL=(18, 0, -12))
    q.key(1.05, T=((2, 720, 0), (0, 0.05, 0)), H=(-2, 0, 0), RA=(-4, 0, 8), LA=(-4, 0, -8), RL=(0, 0, 2), LL=(0, 0, -2))
    q.key(1.20, rest=True)
    return q


def shuffle():
    def f(p):
        side = S(p)                                   # +1 = shifted right
        hit = (1 + C(p, 2)) / 2                       # 1 on the beats (p = 0, 0.5)
        return dict(
            T=((-3 - 3 * hit, -10 * side, -6 * side), (0.45 * side, -0.18 * hit, 0)),
            H=(4 * C(p, 2, -0.06), 9 * side, 5 * side),
            RA=(15 + 12 * side, 0, 58 + 42 * side - 10 * hit), LA=(15 - 12 * side, 0, -58 + 42 * side + 10 * hit),
            RL=(4 * side, 0, 8 + 12 * side), LL=(-4 * side, 0, -8 + 12 * side))
    return Seq("Shuffle", 0.8, True, "Action", plant=True).cycle(f, 16)


def chicken():
    def f(p):
        w = (1 - C(p, 2)) / 2                          # wings: 0 down at the beats, 1 up between
        peck = ((1 + C(p, 2, -0.03)) / 2) ** 3
        return dict(
            T=((-18 + 3 * w, 0, 3 * S(p)), (0, -0.12 + 0.12 * w, 0)),
            H=((-15 * peck + 10 * (1 - peck), 0, -3 * S(p)), (0, 0, -0.28 * peck)),
            RA=(-20, 0, 38 + 46 * w), LA=(-20, 0, -38 - 46 * w),
            RL=(15 - 15 * C(p), 0, 6), LL=(15 + 15 * C(p), 0, -6))
    return Seq("Chicken", 0.48, True, "Action", plant=True).cycle(f, 16)


def flex():
    q = Seq("Flex", 1.8, False, "Action", plant=True)
    q.key(0.00, "CubicV2", "Out", rest=True)
    q.key(0.14, "CubicV2", "In", T=((-10, 0, 0), (0, -0.15, 0)), H=(-10, 0, 0), RA=(25, 0, -15), LA=(25, 0, 15))
    q.key(0.30, "CubicV2", "Out", T=((8, 0, 0), (0, 0.1, 0)), H=(10, 0, 0), RA=(-10, 0, 106), LA=(-10, 0, -106),
          RL=(0, 0, 12), LL=(0, 0, -12))
    q.key(0.40, T=((6, 0, 0), (0, 0.05, 0)), RA=(-10, 0, 98), LA=(-10, 0, -98))
    q.key(0.62, T=((6, -18, -3), (0, 0.05, 0)), H=(4, -22, 0), RA=(-18, 0, 118), LA=(-10, 0, -88))
    q.key(0.70, RA=(-20, 0, 124))
    q.key(0.94, T=((6, 18, 3), (0, 0.05, 0)), H=(4, 22, 0), RA=(-10, 0, 88), LA=(-18, 0, -118))
    q.key(1.02, LA=(-20, 0, -124))
    q.key(1.22, "CubicV2", "Out", T=((10, 0, 0), (0, 0.12, 0)), H=(12, 0, 0), RA=(-14, 0, 108), LA=(-14, 0, -108),
          RL=(0, 0, 14), LL=(0, 0, -14))
    q.key(1.30, T=((12, 0, 0), (0, 0.12, 0)), RA=(-16, 0, 112), LA=(-16, 0, -112))
    q.key(1.50, T=((11, 0, 0), (0, 0.1, 0)), RA=(-15, 0, 110), LA=(-15, 0, -110))
    q.key(1.68, T=((-2, 0, 0), (0, 0, 0)), H=(0, 0, 0), RA=(4, 0, 10), LA=(4, 0, -10), RL=(0, 0, 2), LL=(0, 0, -2))
    q.key(1.80, rest=True)
    return q


def laugh():
    q = Seq("Laugh", 1.95, False, "Action", plant=True)
    q.key(0.00, "CubicV2", "Out", rest=True)
    q.key(0.12, T=((-6, 0, 0), (0, -0.05, 0)), H=(-8, 0, 0), RA=(20, 0, -8), LA=(20, 0, 8))
    q.key(0.26, "CubicV2", "Out", T=((16, 0, 0), (0, 0.06, 0)), H=(26, 0, 0), RA=(45, 0, -12), LA=(45, 0, 12))
    t, i = 0.26, 0
    while t < 1.06:                                    # chuckles, slowly calming down
        t += 0.07
        i += 1
        amp = 1 - 0.4 * (t - 0.26) / 0.8
        up = i % 2 == 1
        q.key(t, T=((12 + (6 if up else 0) * amp, 2 * (1 if up else -1), 0), (0, (0.07 if up else 0.0) * amp, 0)),
              H=(20 + (8 if up else 0) * amp, 0, 3 if up else -3), RA=(45, 0, -12 + (3 if up else 0)),
              LA=(45, 0, 12 - (3 if up else 0)))
    q.key(1.20, T=((-26, 0, 0), (0, 0.0, 0)), H=(-20, -5, 0), RA=(20, 0, 12), LA=(50, 0, 20))
    t, i = 1.20, 0
    while t < 1.55:
        t += 0.08
        i += 1
        q.key(t, T=((-30 if i % 2 else -24, 0, 0), (0, -0.03 if i % 2 else 0.0, 0)), H=(-22 if i % 2 else -17, -5, 0))
    q.key(1.72, T=((4, 0, 0), (0, 0.02, 0)), H=(6, 0, 0), RA=(2, 0, 8), LA=(2, 0, -8))
    q.key(1.95, rest=True)
    return q


def hero():
    q = Seq("Hero", 2.6, False, "Action")
    q.key(0.00, "CubicV2", "Out", rest=True)
    q.key(0.12, "CubicV2", "In", T=((-14, 0, 0), (0, -0.45, 0)), H=(6, 0, 0), RA=(-30, 0, 25), LA=(-30, 0, -25),
          RL=(26, 0, 16), LL=(26, 0, -16))
    q.key(0.30, "CubicV2", "In", T=((6, 0, 0), (0, 1.0, 0)), H=(18, 0, 0), RA=(15, 0, 150), LA=(15, 0, -150),
          RL=(40, 0, 8), LL=(-20, 0, -8))
    q.key(0.46, "CubicV2", "Out", T=((-10, 0, 0), (0, -0.35, 0)), H=(4, 0, 0), RA=(10, 0, 110), LA=(10, 0, -110),
          RL=(26, 0, 16), LL=(26, 0, -16))
    q.key(0.60, "CubicV2", "Out", T=((2, 15, 0), (0, 0.05, 0)), H=(12, 0, 0), RA=(20, 0, 165), LA=(35, 0, -20),
          RL=(0, 0, 12), LL=(0, 0, -12))
    q.key(0.76, "CubicV2", "Out", T=((2, -15, 0), (0, 0.05, 0)), LA=(20, 0, -165), RA=(35, 0, 20))
    q.key(0.92, "Linear", "InOut", T=((-4, -30, 0), (0, -0.25, 0)), H=(0, 0, 0), RA=(30, 0, -10), LA=(30, 0, 10),
          RL=(10, 0, 6), LL=(10, 0, -6))

    def mid(u, yaw):
        arms = min(1.0, u / 0.2)
        return dict(T=((0, yaw, 0), (0, -0.25 + 0.85 * math.sin(math.pi * u), 0)),
                    RA=(30 * (1 - arms), 0, -10 + 95 * arms), LA=(30 * (1 - arms), 0, 10 - 95 * arms),
                    RL=(6, 0, 6 + 14 * math.sin(math.pi * u)), LL=(6, 0, -6))
    q.spin(0.92, 1.40, -30, 360, mid, steps=6)
    q.key(1.48, "CubicV2", "Out", T=((-10, 360, 0), (0, -0.4, 0)), RA=(10, 0, 50), LA=(10, 0, -50),
          RL=(24, 0, 15), LL=(24, 0, -15))
    q.key(1.66, "CubicV2", "Out", T=((6, -10, 0), (0, 0.05, 0)), H=(14, -8, 0), RA=(15, 0, 172), LA=(-25, 0, -35),
          RL=(0, 0, 14), LL=(0, 0, -14))
    q.key(1.78, RA=(15, 0, 158))
    q.key(2.02, T=((7, -10, 0), (0, 0.08, 0)), RA=(15, 0, 161))
    q.key(2.25, T=((6, -10, 0), (0, 0.04, 0)), RA=(15, 0, 157))
    q.key(2.45, T=((0, 0, 0), (0, 0, 0)), H=(0, 0, 0), RA=(4, 0, 10), LA=(2, 0, -10), RL=(0, 0, 3), LL=(0, 0, -3))
    q.key(2.60, rest=True)
    return q


ORDER = ["Sprint", "Spin", "Shuffle", "Slide", "Land", "Fall", "Chicken", "Idle", "Jump", "Pounce", "CatcherRun",
         "Downed", "Wave", "Slash", "Flex", "Tagged", "Laugh", "Hero", "Walk"]
BUILDERS = {"Sprint": sprint, "Spin": spin_emote, "Shuffle": shuffle, "Slide": slide, "Land": land, "Fall": fall,
            "Chicken": chicken, "Idle": idle, "Jump": jump, "Pounce": pounce, "CatcherRun": catcher_run,
            "Downed": downed, "Wave": wave, "Slash": slash, "Flex": flex, "Tagged": tagged, "Laugh": laugh,
            "Hero": hero, "Walk": walk}


def build_all():
    return [BUILDERS[n]() for n in ORDER]
