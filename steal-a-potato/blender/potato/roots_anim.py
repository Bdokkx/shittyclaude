"""The RootMonster's four animations, baked at 30 fps into KeyframeSequences (rbxtool JSON, the
same writer as the game's other animations: every key Linear, the motion already smooth).

  RootEmerge  1.0 s  from completely under the ground it bursts up and the roots unfurl; marker Out
  RootChase   0.7 s  loop: the roots claw forward one after another, the heap bobs and lunges
  RootGrab    0.6 s  every root whips forward and closes; marker Hit
  RootWither  1.2 s  it loses: shudders, shrivels, sags and sinks; ends completely under the ground

Joint conventions (see roots.py): a root joint's +X turn lifts it, +Y swings it to its left; the
Heap joint is in model axes (front -Z)."""
import copy
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(HERE, "..", "..", "..", "folk-valley-animations", "tools"))
import anim as A  # noqa: E402

from . import roots as R  # noqa: E402

FPS = 30
PRIORITY = {"Idle": 0, "Movement": 1, "Action": 2}


# ---------------------------------------------------------------- maths

def rx(d):
    c, s = math.cos(math.radians(d)), math.sin(math.radians(d))
    m = np.eye(4)
    m[1, 1], m[1, 2], m[2, 1], m[2, 2] = c, -s, s, c
    return m


def ry(d):
    c, s = math.cos(math.radians(d)), math.sin(math.radians(d))
    m = np.eye(4)
    m[0, 0], m[0, 2], m[2, 0], m[2, 2] = c, s, -s, c
    return m


def rz(d):
    c, s = math.cos(math.radians(d)), math.sin(math.radians(d))
    m = np.eye(4)
    m[0, 0], m[0, 1], m[1, 0], m[1, 1] = c, -s, s, c
    return m


def tr(x, y, z):
    m = np.eye(4)
    m[:3, 3] = (x, y, z)
    return m


def m4(cf):
    m = np.eye(4)
    m[:3, :3] = cf.R
    m[:3, 3] = cf.p
    return m


def spline(keys, t, loop=None):
    """Catmull-Rom through (time, value) keys; loop = period (the keys span 0..period)."""
    ts = [k[0] for k in keys]
    vs = [k[1] for k in keys]
    if loop:
        t = t % loop
    if t <= ts[0]:
        return vs[0]
    if t >= ts[-1]:
        return vs[-1]
    i = max(j for j in range(len(ts) - 1) if ts[j] <= t)
    t0, t1 = ts[i], ts[i + 1]
    u = (t - t0) / (t1 - t0)

    def at(j):
        if loop:
            n = len(vs) - 1                       # the last key repeats the first
            return vs[j % n]
        return vs[min(max(j, 0), len(vs) - 1)]
    p0, p1, p2, p3 = at(i - 1), at(i), at(i + 1), at(i + 2)
    return 0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u +
                  (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3)


def ease(a, b, t, t0, t1, kind="inout"):
    if t <= t0:
        return a
    if t >= t1:
        return b
    u = (t - t0) / (t1 - t0)
    if kind == "out":
        u = 1 - (1 - u) ** 3
    elif kind == "in":
        u = u ** 3
    else:
        u = u * u * (3 - 2 * u)
    return a + (b - a) * u


# ---------------------------------------------------------------- posing

SIDE = {t[0]: (1.0 if t[1][0] > 0 else -1.0) for t in R.TENTACLES}
CURL_W = (1.0, 1.15, 1.3, 1.45)


def root_pose(X, tname, lift=0.0, yaw=0.0, curl=0.0, wave=0.0, phase=0.0):
    """Pose one root: seg1 lifts and swings (yaw > 0 = forward / inward, either side), the
    other joints curl (> 0 up, < 0 hooking down) with a travelling wave on top."""
    s = SIDE[tname]
    X["%sSeg1" % tname] = ry(s * yaw) @ rx(lift)
    for i in range(2, R.SEGS + 1):
        w = wave * math.sin(phase - 0.9 * i)
        X["%sSeg%d" % (tname, i)] = rx(curl * CURL_W[i - 2] + w)


def heap_pose(X, y=0.0, z=0.0, pitch=0.0, roll=0.0, yaw=0.0):
    X["Heap"] = tr(0.0, y, z) @ ry(yaw) @ rx(pitch) @ rz(roll)


class Clip:
    def __init__(self, name, length, loop, priority, fn, markers=()):
        self.name, self.length, self.loop, self.priority, self.fn = name, length, loop, priority, fn
        self.markers = list(markers)

    def times(self):
        n = int(round(self.length * FPS))
        return [i / FPS for i in range(n + (0 if self.loop else 1))] + ([self.length] if self.loop else [])

    def bake(self):
        out = []
        for t in self.times():
            X = {}
            self.fn(X, t if not self.loop else t % self.length)
            out.append(X)
        return out


# -- RootChase: the roots claw forward one after another (front pair half a cycle apart)
CH_LEN = 0.7
CH_OFF = {"Tentacle1": 0.0, "Tentacle2": 0.5, "Tentacle3": 0.27, "Tentacle4": 0.77, "Tentacle5": 0.62,
          "Tentacle6": 0.12}
CH_LIFT = [(0.0, 1.0), (0.22, 44.0), (0.42, -3.0), (0.7, 0.0), (1.0, 1.0)]
CH_YAW = [(0.0, -14.0), (0.22, 12.0), (0.42, 22.0), (0.7, -4.0), (1.0, -14.0)]
CH_CURL = [(0.0, 0.0), (0.22, 14.0), (0.42, -4.0), (0.7, -1.0), (1.0, 0.0)]


def chase(X, t):
    u = t / CH_LEN
    for (tname, *_rest) in R.TENTACLES:
        p = (u + CH_OFF[tname]) % 1.0
        amp = 0.65 if tname in ("Tentacle5", "Tentacle6") else 1.0
        root_pose(X, tname, spline(CH_LIFT, p, 1.0) * amp, spline(CH_YAW, p, 1.0) * amp,
                  spline(CH_CURL, p, 1.0) * amp, wave=5.0, phase=math.tau * p)
    w = math.tau * u
    heap_pose(X, y=0.15 + 0.32 * math.sin(2 * w), z=-0.25 * math.sin(2 * w + 0.6), pitch=-5 + 4 * math.sin(2 * w + 1.0),
              roll=4.0 * math.sin(w), yaw=3.0 * math.sin(w + 0.5))


# -- RootEmerge: from under the ground (heap 11 down, roots coiled), burst, unfurl, settle
EM_LEN = 1.0
UNDER = -11.0


def emerge(X, t):
    if t < 0.3:
        y = ease(UNDER, 0.9, t, 0.0, 0.3, "out")
    elif t < 0.46:
        y = ease(0.9, -0.25, t, 0.3, 0.46)
    else:
        y = ease(-0.25, 0.0, t, 0.46, 0.62)
    shake = 2.5 * math.sin(t * 70) * max(0.0, 1 - t / 0.5)
    heap_pose(X, y=y, pitch=ease(10.0, -4.0, t, 0.05, 0.4) + ease(0.0, 4.0, t, 0.4, 0.8), roll=shake)
    for i, (tname, *_rest) in enumerate(R.TENTACLES):
        d = 0.025 * i
        lift = spline([(0.0, 55.0), (0.26 + d, 55.0), (0.42 + d, -4.0), (0.56 + d, 10.0), (0.72 + d, 0.0),
                       (1.0, 0.0)], t)
        curl = spline([(0.0, 52.0), (0.26 + d, 50.0), (0.44 + d, -4.0), (0.6 + d, 7.0), (0.8 + d, 0.0),
                       (1.0, 0.0)], t)
        yaw = spline([(0.0, -20.0), (0.3 + d, -20.0), (0.48 + d, 10.0), (0.7 + d, -3.0), (1.0, 0.0)], t)
        root_pose(X, tname, lift, yaw, curl, wave=8.0 * max(0.0, 1 - t), phase=t * 25)


# -- RootGrab: wind up wide, whip forward and close (Hit), hold, ease back
GR_LEN = 0.6
GR_HIT = 0.32


def grab(X, t):
    heap_pose(X, y=spline([(0.0, 0.0), (0.18, 0.5), (0.32, 0.2), (0.6, 0.0)], t),
              z=spline([(0.0, 0.0), (0.18, 0.8), (0.32, -2.0), (0.45, -1.6), (0.6, -0.3)], t),
              pitch=spline([(0.0, 0.0), (0.18, 9.0), (0.32, -5.0), (0.45, -4.0), (0.6, -1.0)], t))
    for (tname, *_rest) in R.TENTACLES:
        back = tname in ("Tentacle5", "Tentacle6")
        k = 0.6 if back else 1.0
        lift = spline([(0.0, 0.0), (0.18, 46.0), (0.32, 22.0), (0.45, 20.0), (0.6, 3.0)], t) * k
        yaw = spline([(0.0, 0.0), (0.18, -30.0), (0.32, 46.0), (0.45, 42.0), (0.6, 8.0)], t) * k
        curl = spline([(0.0, 0.0), (0.18, 16.0), (0.32, -9.0), (0.45, -10.0), (0.6, -2.0)], t) * k
        root_pose(X, tname, lift, yaw, curl)


# -- RootWither: shudder, shrivel and sag, then sink completely under the ground
WI_LEN = 1.2


def wither(X, t):
    tremble = 3.0 * math.sin(t * 60) * (1 - t / WI_LEN)
    if t < 0.7:
        y = ease(0.0, -1.6, t, 0.25, 0.7)
    else:
        y = ease(-1.6, UNDER, t, 0.7, 1.2, "in")
    heap_pose(X, y=y, pitch=spline([(0.0, 0.0), (0.15, 8.0), (0.5, -6.0), (0.8, -10.0), (1.2, -10.0)], t),
              roll=tremble + ease(0.0, 6.0, t, 0.3, 0.8))
    for i, (tname, *_rest) in enumerate(R.TENTACLES):
        d = 0.02 * i
        lift = spline([(0.0, 0.0), (0.12 + d, 32.0), (0.3 + d, -2.0), (0.6 + d, -5.0), (0.85, -2.0),
                       (1.2, 60.0)], t)
        curl = spline([(0.0, 0.0), (0.12 + d, 12.0), (0.3 + d, -4.0), (0.6 + d, -8.0), (0.85, 10.0),
                       (1.2, 55.0)], t)
        yaw = spline([(0.0, 0.0), (0.15, -12.0), (0.6, 18.0), (1.2, 25.0)], t)
        root_pose(X, tname, lift, yaw, curl, wave=6.0 * (1 - t / WI_LEN), phase=t * 40)


CLIPS = [Clip("RootEmerge", EM_LEN, False, PRIORITY["Action"], emerge, [(0.3, "Out")]),
         Clip("RootChase", CH_LEN, True, PRIORITY["Movement"], chase),
         Clip("RootGrab", GR_LEN, False, PRIORITY["Action"], grab, [(GR_HIT, "Hit")]),
         Clip("RootWither", WI_LEN, False, PRIORITY["Action"], wither)]


# ---------------------------------------------------------------- forward kinematics (previews, checks)

def fk(rig, X):
    """{joint: Transform} -> {part name: 4x4 model-space delta} (part world = base * delta * rest)."""
    D = {"Root": np.eye(4)}
    for (jname, p0, p1, hinge) in rig["joints"]:
        H = m4(hinge)
        D[p1] = D[p0] @ H @ X.get(jname, np.eye(4)) @ np.linalg.inv(H)
    return D


def posed_parts(sc, X):
    """{part node: new world CF} for the RootMonster posed by X (welded parts follow)."""
    from spsgeo import CF
    rig = sc.root_rig
    base = m4(rig["base"])
    D = fk(rig, X)
    m = rig["model"]
    welds = {}
    for n in m.walk():
        if n.kind == "Weld":
            welds[n.p["part1"]] = n.p["part0"]
    out = {}
    binv = np.linalg.inv(base)
    for n in m.walk():
        if n.kind not in ("Part", "MeshPart"):
            continue
        owner = welds.get(n, n)
        d = D.get(owner.name, np.eye(4))
        w = base @ d @ binv @ m4(n.p["cf"])
        out[n] = CF(w[:3, 3], w[:3, :3])
    return out


def extent(sc, X):
    """(lowest, highest) vertex of the posed monster relative to its own ground."""
    rig = sc.root_rig
    posed = posed_parts(sc, X)
    lo, hi = 1e9, -1e9
    for n, cf_ in posed.items():
        if n.p.get("transparency", 0) >= 0.99 or n.name in ("Clods",):
            continue
        if n.kind == "MeshPart":
            V = np.array(sc.geoms[n.p["mesh"]].v)
        else:
            V = np.array([[sx * n.p["size"][0] / 2, sy * n.p["size"][1] / 2, 0.0] for sx in (-1, 1) for sy in (-1, 1)])
        W = (cf_.R @ V.T).T + cf_.p
        lo, hi = min(lo, float(W[:, 1].min())), max(hi, float(W[:, 1].max()))
    return lo - rig["base"].p[1], hi - rig["base"].p[1]


def highest_point(sc, X):
    """The highest vertex of the posed monster above its own ground (for the under-ground check)."""
    rig = sc.root_rig
    posed = posed_parts(sc, X)
    top = -1e9
    for n, cf_ in posed.items():
        if n.p.get("transparency", 0) >= 0.99:
            continue
        if n.kind == "MeshPart":
            V = np.array(sc.geoms[n.p["mesh"]].v)
        else:
            V = np.array([[sx * n.p["size"][0] / 2, sy * n.p["size"][1] / 2, 0.0] for sx in (-1, 1) for sy in (-1, 1)])
        W = (cf_.R @ V.T).T + cf_.p
        top = max(top, float(W[:, 1].max()))
    return top - rig["base"].p[1]


# ---------------------------------------------------------------- writing

MARKER_PROPS = {"Attributes": {"Attributes": {}}, "Capabilities": {"SecurityCapabilities": 0},
                "Sandboxed": {"Bool": False}, "SerializedOverrides": {"BinaryString": ""},
                "SourceAssetId": {"Int64": -1}, "Tags": {"Tags": []}, "Value": {"String": ""}}


def children(rig):
    ch = {}
    for (jname, p0, p1, _h) in rig["joints"]:
        ch.setdefault(p0, []).append(p1)
    return ch


def write(rig, clip, frames):
    props = copy.deepcopy(A.KS_PROPS)
    props["Loop"] = {"Bool": bool(clip.loop)}
    props["Priority"] = {"Enum": int(clip.priority)}
    props["AuthoredHipHeight"] = {"Float32": 0.0}
    ch = children(rig)
    times = clip.times()
    marks = {}
    for t, name in clip.markers:
        i = int(np.argmin([abs(t - x) for x in times]))
        marks.setdefault(i, []).append(name)
    kfs = []
    for i, X in enumerate(frames):
        def pose(b):
            kids = [pose(c) for c in ch.get(b, [])]
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


def bake_all(sc):
    """[(clip, frames)] and the rbxtool JSON folder RootAnimations."""
    rig = sc.root_rig
    out = [(c, c.bake()) for c in CLIPS]
    folder = {"class": "Folder", "name": "RootAnimations", "ref": A._ref(),
              "props": {"Attributes": {"Attributes": {}}, "Tags": {"Tags": []}},
              "children": [write(rig, c, fr) for c, fr in out]}
    return out, folder
