"""Animation toolkit for the Grim Reaper rig.

A clip is keyed per bone (Euler degrees about the joint's X, Y, Z, plus an
optional offset), sampled on a smooth spline at 30 fps, then a per-frame hook
adds what keys can't do well: leg IK (feet planted or following a path), the
scythe solver (point it somewhere in model space, or fly it along a path), and
cloth (robe panels pushed by the legs, everything cloth lagging a little).
Written out as KeyframeSequences with Linear keys, like the game's other
animations. Joint frames are axis-aligned with the model at rest (model faces
-Z): +X turns a hanging limb forward, +Z turns it toward the model's right (+X),
+Y yaws to the model's left.
"""
import copy
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "folk-valley-animations", "tools"))
import anim as A  # noqa: E402

FPS = 30


def T(x, y=None, z=None):
    if y is None:
        x, y, z = x
    m = np.eye(4)
    m[:3, 3] = (x, y, z)
    return m


def Rq(q):
    m = np.eye(4)
    m[:3, :3] = A.quat_to_mat(q)
    return m


def E(rx=0.0, ry=0.0, rz=0.0):
    """4x4 rotation from Euler degrees (X, then Y, then Z, like CFrame.Angles)."""
    return Rq(A.euler_quat(rx, ry, rz))


def rot_x(d):
    return E(d, 0, 0)


def inv(m):
    return np.linalg.inv(m)


class Rig:
    def __init__(self, path):
        data = json.load(open(path))
        self.rest = {"HumanoidRootPart": T(data["HRP"]["Center"])}
        for p in data["Parts"]:
            if p["Name"] == p["Model"]:
                self.rest[p["Model"]] = T(p["Center"])
        self.joints = [(j["Motor"], j["Part0"], j["Part1"], np.array(j["Pivot"], dtype=float)) for j in data["Rig"]]
        self.parent = {b: a for _, a, b, _ in self.joints}
        self.pivot = {b: c for _, _, b, c in self.joints}
        self.C0 = {b: inv(self.rest[a]) @ T(c) for _, a, b, c in self.joints}
        self.C1 = {b: inv(self.rest[b]) @ T(c) for _, a, b, c in self.joints}
        self.children = {}
        for _, a, b, _ in self.joints:
            self.children.setdefault(a, []).append(b)
        self.bones = [b for _, _, b, _ in self.joints]
        self.parts = data["Parts"]
        self.hip_height = data["HRP"]["Center"][1] - data["HRP"]["Size"][1] / 2

    def fk(self, X):
        """{bone: 4x4 Transform} -> {bone: 4x4 world matrix} (model space, HRP fixed)."""
        W = {"HumanoidRootPart": self.rest["HumanoidRootPart"]}
        for _, a, b, _ in self.joints:
            W[b] = W[a] @ self.C0[b] @ X.get(b, np.eye(4)) @ inv(self.C1[b])
        return W

    def joint_world(self, W, bone):
        """World matrix of a joint's frame (C0 side) for the posed parent."""
        return W[self.parent[bone]] @ self.C0[bone]


# ---------------------------------------------------------------- IK

def leg_ik(rig, X, W, side, target, pitch=0.0):
    """Set hip / knee / ankle so the ankle reaches `target` (model space) and the
    foot sits at `pitch` degrees (toes up +) in the model's frame."""
    hipb, kneeb, footb = side + "UpperLeg", side + "LowerLeg", side + "Foot"
    J = rig.joint_world(W, hipb)                       # hip joint frame (LowerTorso's orientation)
    loc = inv(J) @ np.array([*target, 1.0])
    a = loc[:3]
    k0 = rig.pivot[kneeb] - rig.pivot[hipb]
    a0 = rig.pivot[footb] - rig.pivot[hipb]
    L1 = float(np.linalg.norm(k0))
    L2 = float(np.linalg.norm(a0 - k0))
    roll = math.degrees(math.atan2(a[0] - a0[0], -a[1]))
    d = math.hypot(a[1], a[2])
    d = min(max(d, 1.0), (L1 + L2) * 0.997)
    bend = math.pi - math.acos(max(-1.0, min(1.0, (L1 * L1 + L2 * L2 - d * d) / (2 * L1 * L2))))
    alpha = math.atan2(-a[2], -a[1])
    beta = math.acos(max(-1.0, min(1.0, (L1 * L1 + d * d - L2 * L2) / (2 * L1 * d))))
    hip_p = math.degrees(alpha + beta)
    X[hipb] = E(0, 0, roll) @ rot_x(hip_p)
    X[kneeb] = rot_x(-math.degrees(bend))
    # the foot: undo the leg's pitch, and the body's own pitch, then add the wanted pitch
    W2 = rig.fk(X)
    R = W2[kneeb][:3, :3]
    toes = R @ np.array([0.0, 0.0, -1.0])
    cur = math.degrees(math.atan2(toes[1], -toes[2]))
    X[footb] = rot_x(pitch - cur)
    return hip_p, roll


def scythe_to(rig, X, W, target):
    """Grip transform that puts the Scythe part's world matrix at `target`."""
    hand = W[rig.parent["Scythe"]]
    X["Scythe"] = inv(rig.C0["Scythe"]) @ inv(hand) @ target @ rig.C1["Scythe"]


def scythe_rest_world(rig):
    return rig.rest["Scythe"]


def about(point, R):
    """A rotation R (4x4) about a model-space point."""
    return T(point) @ R @ T(-np.asarray(point))


# ---------------------------------------------------------------- clips

class Clip:
    def __init__(self, name, length, loop, priority, base=None):
        self.name = name
        self.length = length
        self.loop = loop
        self.priority = priority
        self.keys = {}
        self.markers = []
        self.frame = None                 # per-frame hook(t, X, ctx)
        self.base = base or {}
        self.cloth_lag = 0.10             # seconds
        self.floor_mode = "out"           # how robe_floor clears the ground (see there)

    def key(self, t, **bones):
        for b, v in bones.items():
            v = tuple(v)
            rot = v[:3]
            pos = v[3:6] if len(v) >= 6 else (0.0, 0.0, 0.0)
            self.keys.setdefault(b, []).append((t, rot, pos))
        return self

    def pose(self, t, pose):
        return self.key(t, **pose)

    def marker(self, t, name):
        self.markers.append((t, name))
        return self


CLOTH = ("RobeFront", "RobeBack", "RobeLeft", "RobeRight", "Cape")


def bake(rig, clip):
    n = int(round(clip.length * FPS))
    times = [min(i / FPS, clip.length) for i in range(n + 1)]
    if clip.loop:
        times = times[:-1]
    curves = {}
    for b, ks in clip.keys.items():
        ks = sorted(ks, key=lambda k: k[0])
        track = A.Track([k[0] for k in ks], [k[2] for k in ks], [A.euler_quat(*k[1]) for k in ks])
        curves[b] = A.sample(track, times, clip.loop, clip.length)
    frames = []
    ctx = {}
    for i, t in enumerate(times):
        X = {}
        for b in rig.bones:
            if b in curves:
                p, q = curves[b][0][i], curves[b][1][i]
                X[b] = T(p) @ Rq(q)
            elif b in clip.base:
                v = clip.base[b]
                X[b] = T(v[3:6] if len(v) >= 6 else (0, 0, 0)) @ E(*v[:3])
        if clip.frame:
            clip.frame(t, X, ctx)
        frames.append(X)
    lag_cloth(clip, frames)
    for X in frames:
        robe_floor(rig, X, floor=getattr(clip, "floor_level", 0.12), mode=getattr(clip, "floor_mode", "out"))
    if clip.loop:
        # Roblox loops from the last keyframe straight back to the first: end on a copy of it
        times.append(clip.length)
        frames.append({b: m.copy() for b, m in frames[0].items()})
    return times, frames


def lag_cloth(clip, frames):
    """Cloth trails the motion: a one-pole filter on every cloth bone's rotation
    (run round the loop a few times so looping clips stay seamless)."""
    if clip.cloth_lag <= 0:
        return
    k = 1 - math.exp(-1.0 / (FPS * clip.cloth_lag))
    n = len(frames)
    for b in CLOTH:
        qs = [A.mat_to_quat(f[b][:3, :3]) if b in f else np.array([1.0, 0, 0, 0]) for f in frames]
        state = qs[0].copy()
        passes = 3 if clip.loop else 1
        out = [None] * n
        for _ in range(passes):
            for i in range(n):
                state = A.slerp(state, qs[i], k)
                out[i] = state.copy()
        for i in range(n):
            m = np.eye(4)
            m[:3, :3] = A.quat_to_mat(out[i])
            if b in frames[i]:
                m[:3, 3] = frames[i][b][:3, 3]
            frames[i][b] = m


def robe_from_legs(X, hips, extra=None):
    """Push the robe panels out of the way of the legs: hips = {side: (pitch, roll)}."""
    pr, rr = hips.get("Right", (0.0, 0.0))
    pl, rl = hips.get("Left", (0.0, 0.0))
    front = max(pr, pl, 0.0) * 0.78
    back = min(pr, pl, 0.0) * 0.62
    right = max(rr, 0.0) * 1.1 + 0.18 * abs(pr)
    left = min(rl, 0.0) * 1.1 - 0.18 * abs(pl)
    e = extra or {}
    X["RobeFront"] = E(front + e.get("front", 0.0), 0, 0) @ X.get("RobeFront", np.eye(4))
    X["RobeBack"] = E(back - e.get("back", 0.0), 0, 0) @ X.get("RobeBack", np.eye(4))
    X["RobeRight"] = E(0, 0, right + e.get("right", 0.0)) @ X.get("RobeRight", np.eye(4))
    X["RobeLeft"] = E(0, 0, left - e.get("left", 0.0)) @ X.get("RobeLeft", np.eye(4))


# cloth bone, the joint axis that swings it outward (+1 / -1 about X or Z)
FLARE = (("RobeFront", (1, 0, 0)), ("RobeBack", (-1, 0, 0)), ("RobeRight", (0, 0, 1)), ("RobeLeft", (0, 0, -1)),
         ("Cape", (-1, 0, 0)))


def _hem(rig, bone):
    """The bottom corners and middle of a cloth part (rest model space)."""
    p = next(q for q in rig.parts if q["Name"] == bone)
    c, s = np.array(p["Center"]), np.array(p["Size"]) / 2
    y = c[1] - s[1] + 0.05
    pts = [(c[0] + dx * s[0], y, c[2] + dz * s[2]) for dx in (-1, 1) for dz in (-1, 1)] + [(c[0], y, c[2])]
    return [np.array([*q, 1.0]) for q in pts]


def robe_floor(rig, X, floor=0.12, mode="out"):
    """Swing any cloth panel whose hem would dip under the ground out just far enough
    to rest on it (kneeling, crouching, big hip swings). mode "out" only swings outward
    (as the first ten animations were made); "both" looks for the smallest swing either
    way and leaves a panel alone if nothing within 85 degrees clears the ground."""
    if not hasattr(rig, "_hems"):
        rig._hems = {b: _hem(rig, b) for b, _ in FLARE}
    W = rig.fk(X)
    for b, ax in FLARE:
        par = W[rig.parent[b]] @ rig.C0[b]
        back = inv(rig.C1[b]) @ inv(rig.rest[b])
        base = X.get(b, np.eye(4))

        def low(extra):
            m = par @ E(*(np.array(ax) * extra)) @ base @ back
            return min((m @ p)[1] for p in rig._hems[b])
        if low(0.0) >= floor:
            continue
        if mode == "out":
            lo, hi = 0.0, 85.0
            if low(hi) < floor:
                lo = hi
            else:
                for _ in range(14):
                    mid = (lo + hi) / 2
                    if low(mid) >= floor:
                        hi = mid
                    else:
                        lo = mid
                lo = hi
            X[b] = E(*(np.array(ax) * lo)) @ base
            continue
        # the smallest swing that clears the ground: outward first, then inward; a panel
        # that can't be cleared within 85 degrees either way is left as it is
        best = None
        for sign in (1.0, -1.0):
            prev = 0.0
            for step in range(5, 86, 5):
                if low(sign * step) >= floor:
                    lo, hi = prev, float(step)
                    for _ in range(14):
                        mid = (lo + hi) / 2
                        if low(sign * mid) >= floor:
                            hi = mid
                        else:
                            lo = mid
                    best = sign * hi
                    break
                prev = float(step)
            if best is not None:
                break
        if best is not None:
            X[b] = E(*(np.array(ax) * best)) @ base


# ---------------------------------------------------------------- writing

MARKER_PROPS = {"Attributes": {"Attributes": {}}, "Capabilities": {"SecurityCapabilities": 0},
                "Sandboxed": {"Bool": False}, "SerializedOverrides": {"BinaryString": ""},
                "SourceAssetId": {"Int64": -1}, "Tags": {"Tags": []}, "Value": {"String": ""}}


def _xf_to_pose(m):
    return m[:3, 3], A.mat_to_quat(m[:3, :3])


def write(rig, clip, times, frames):
    props = copy.deepcopy(A.KS_PROPS)
    props["Loop"] = {"Bool": bool(clip.loop)}
    props["Priority"] = {"Enum": int(clip.priority)}
    props["AuthoredHipHeight"] = {"Float32": round(float(rig.hip_height), 3)}
    marks = {}
    for t, name in clip.markers:
        i = int(np.argmin([abs(t - x) for x in times]))
        marks.setdefault(i, []).append(name)
    kfs = []
    for i, X in enumerate(frames):
        def pose(b):
            kids = [pose(c) for c in rig.children.get(b, [])]
            if b == "HumanoidRootPart":
                return A._pose(b, (0, 0, 0), np.array([1.0, 0, 0, 0]), kids, weight=0.0)
            p, q = _xf_to_pose(X.get(b, np.eye(4)))
            return A._pose(b, p, q, kids)
        kp = copy.deepcopy(A.KF_PROPS)
        kp["Time"] = {"Float32": round(float(times[i]), 5)}
        kids = [pose("HumanoidRootPart")]
        for name in marks.get(i, []):
            mp = copy.deepcopy(MARKER_PROPS)
            kids.append({"class": "KeyframeMarker", "name": name, "ref": A._ref(), "props": mp, "children": []})
        kfs.append({"class": "Keyframe", "name": "Keyframe", "ref": A._ref(), "props": kp, "children": kids})
    return {"class": "KeyframeSequence", "name": clip.name, "ref": A._ref(), "props": props, "children": kfs}
