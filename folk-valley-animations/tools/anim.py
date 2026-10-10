"""R6 KeyframeSequence toolkit: read the poses out of an rbxtool JSON dump, turn them
into smooth per-joint curves, and write dense, smooth KeyframeSequences back.

A Pose's CFrame is the Motor6D.Transform of its joint (local to the joint frame).
Joints: Torso (RootJoint), Head (Neck), Right Arm / Left Arm (shoulders),
Right Leg / Left Leg (hips).
"""
import copy
import math
import secrets

import numpy as np

JOINTS = ["Torso", "Head", "Right Arm", "Left Arm", "Right Leg", "Left Leg"]
LIMBS = JOINTS[1:]

# ---------------------------------------------------------------- rotation helpers

def mat_to_quat(m):
    m = np.asarray(m, dtype=float)
    t = m[0, 0] + m[1, 1] + m[2, 2]
    if t > 0:
        s = math.sqrt(t + 1.0) * 2
        q = [0.25 * s, (m[2, 1] - m[1, 2]) / s, (m[0, 2] - m[2, 0]) / s, (m[1, 0] - m[0, 1]) / s]
    elif m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
        s = math.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2]) * 2
        q = [(m[2, 1] - m[1, 2]) / s, 0.25 * s, (m[0, 1] + m[1, 0]) / s, (m[0, 2] + m[2, 0]) / s]
    elif m[1, 1] > m[2, 2]:
        s = math.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2]) * 2
        q = [(m[0, 2] - m[2, 0]) / s, (m[0, 1] + m[1, 0]) / s, 0.25 * s, (m[1, 2] + m[2, 1]) / s]
    else:
        s = math.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2
        q = [(m[1, 0] - m[0, 1]) / s, (m[0, 2] + m[2, 0]) / s, (m[1, 2] + m[2, 1]) / s, 0.25 * s]
    q = np.array(q)
    return q / np.linalg.norm(q)


def quat_to_mat(q):
    w, x, y, z = q / np.linalg.norm(q)
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def quat_mul(a, b):
    w1, x1, y1, z1 = a
    w2, x2, y2, z2 = b
    return np.array([w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2, w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
                     w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2, w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2])


def axis_quat(axis, deg):
    a = math.radians(deg) / 2
    v = np.asarray(axis, dtype=float)
    v = v / np.linalg.norm(v)
    return np.array([math.cos(a), *(v * math.sin(a))])


def euler_quat(rx=0.0, ry=0.0, rz=0.0):
    """Rotation in degrees about the joint's X, then Y, then Z (CFrame.Angles order)."""
    return quat_mul(quat_mul(axis_quat((1, 0, 0), rx), axis_quat((0, 1, 0), ry)), axis_quat((0, 0, 1), rz))


def slerp(a, b, t):
    d = float(np.dot(a, b))
    if d < 0:
        b, d = -b, -d
    if d > 0.9995:
        q = a + (b - a) * t
        return q / np.linalg.norm(q)
    th = math.acos(min(d, 1.0))
    return (math.sin((1 - t) * th) * a + math.sin(t * th) * b) / math.sin(th)


# ---------------------------------------------------------------- tracks

class Track:
    """One joint's keys: times, positions (n, 3) and quaternions (n, 4)."""

    def __init__(self, times, pos, quat):
        self.t = np.asarray(times, dtype=float)
        self.p = np.asarray(pos, dtype=float)
        self.q = np.asarray(quat, dtype=float)
        for i in range(1, len(self.q)):         # keep neighbours in the same hemisphere
            if np.dot(self.q[i], self.q[i - 1]) < 0:
                self.q[i] = -self.q[i]


class Anim:
    """A whole KeyframeSequence as joint tracks plus its settings."""

    def __init__(self, name, length, loop, priority, tracks, props=None):
        self.name = name
        self.length = length
        self.loop = loop
        self.priority = priority
        self.tracks = tracks            # {joint: Track}
        self.props = props              # original KeyframeSequence props (kept on write)

    def copy(self):
        return copy.deepcopy(self)


def read_sequence(ks):
    """KeyframeSequence JSON node -> Anim (the original keys, as authored)."""
    kfs = sorted((k for k in ks["children"] if k["class"] == "Keyframe"), key=lambda k: k["props"]["Time"]["Float32"])
    keys = {j: ([], [], []) for j in JOINTS}

    def walk(p, t):
        if p["class"] != "Pose":
            return
        if p["name"] in keys and p["props"].get("Weight", {}).get("Float32", 1.0) > 0:   # Weight 0 = not animated
            cf = p["props"]["CFrame"]["CFrame"]
            keys[p["name"]][0].append(t)
            keys[p["name"]][1].append(cf["position"])
            keys[p["name"]][2].append(mat_to_quat(cf["orientation"]))
        for c in p.get("children", []):
            walk(c, t)
    for k in kfs:
        t = k["props"]["Time"]["Float32"]
        for c in k.get("children", []):
            walk(c, t)
    length = kfs[-1]["props"]["Time"]["Float32"] if kfs else 0.0
    tracks = {j: Track(*v) for j, v in keys.items() if v[0]}
    return Anim(ks["name"], length, ks["props"]["Loop"]["Bool"], ks["props"]["Priority"]["Enum"], tracks,
                copy.deepcopy(ks["props"]))


# ---------------------------------------------------------------- smooth sampling

def _tangents(t, v, loop, length):
    """Monotone-friendly Catmull-Rom tangents (per component) for keys v at times t."""
    n = len(t)
    m = np.zeros_like(v)
    for i in range(n):
        if loop and n > 2:
            ip = i - 1 if i > 0 else n - 2          # the last key duplicates the first in a loop
            inx = i + 1 if i < n - 1 else 1
            tp = t[ip] - (length if i == 0 else 0.0)
            tn = t[inx] + (length if i == n - 1 else 0.0)
        else:
            ip, inx = max(i - 1, 0), min(i + 1, n - 1)
            tp, tn = t[ip], t[inx]
            if i in (0, n - 1):
                continue                             # one-shots ease in and out at the ends
        if tn - tp < 1e-6:
            continue
        m[i] = (v[inx] - v[ip]) / (tn - tp)
        # no overshoot: a component that does not change on one side, or turns around, keeps flat
        d0 = (v[i] - v[ip]) / max(t[i] - tp, 1e-6)
        d1 = (v[inx] - v[i]) / max(tn - t[i], 1e-6)
        flat = (d0 * d1) <= 0
        m[i][flat] = 0.0
        lim = 3.0 * np.minimum(np.abs(d0), np.abs(d1))
        m[i] = np.clip(m[i], -lim, lim)
    return m


def _hermite(t, v, m, x):
    i = int(np.searchsorted(t, x, side="right") - 1)
    i = max(0, min(i, len(t) - 2))
    h = t[i + 1] - t[i]
    if h < 1e-6:
        return v[i + 1].copy()
    s = (x - t[i]) / h
    s2, s3 = s * s, s * s * s
    return ((2 * s3 - 3 * s2 + 1) * v[i] + (s3 - 2 * s2 + s) * h * m[i] + (-2 * s3 + 3 * s2) * v[i + 1]
            + (s3 - s2) * h * m[i + 1])


def sample(track, times, loop, length):
    """Positions and quaternions of a track at the given times, on a smooth curve
    through every key (closing the loop when the animation loops)."""
    t, p, q = track.t, track.p, track.q
    if len(t) == 1:
        return np.repeat(p, len(times), 0), np.repeat(q, len(times), 0)
    if loop:
        # make sure the curve is closed: a copy of the first key at t = length
        if abs(t[-1] - length) > 1e-4 or np.linalg.norm(p[-1] - p[0]) > 1e-4 or abs(abs(np.dot(q[-1], q[0])) - 1) > 1e-6:
            t = np.append(t, length) if t[-1] < length - 1e-4 else t.copy()
            if len(t) > len(p):
                p = np.vstack([p, p[:1]])
                q0 = q[0] if np.dot(q[0], q[-1]) >= 0 else -q[0]
                q = np.vstack([q, q0])
            else:
                p = p.copy()
                q = q.copy()
                p[-1] = p[0]
                q[-1] = q[0] if np.dot(q[0], q[-2]) >= 0 else -q[0]
    mp = _tangents(t, p, loop, length)
    mq = _tangents(t, q, loop, length)
    ps = np.array([_hermite(t, p, mp, x) for x in times])
    qs = np.array([_hermite(t, q, mq, x) for x in times])
    qs /= np.linalg.norm(qs, axis=1)[:, None]
    return ps, qs


# ---------------------------------------------------------------- writing

def _ref():
    return secrets.token_hex(16).upper()


POSE_PROPS = {"Attributes": {"Attributes": {}}, "Capabilities": {"SecurityCapabilities": 0},
              "EasingDirection": {"Enum": 0}, "EasingStyle": {"Enum": 0}, "Sandboxed": {"Bool": False},
              "SerializedOverrides": {"BinaryString": ""}, "SourceAssetId": {"Int64": -1}, "Tags": {"Tags": []},
              "Weight": {"Float32": 1.0}}
KF_PROPS = {"Attributes": {"Attributes": {}}, "Capabilities": {"SecurityCapabilities": 0}, "Sandboxed": {"Bool": False},
            "SerializedOverrides": {"BinaryString": ""}, "SourceAssetId": {"Int64": -1}, "Tags": {"Tags": []}}
KS_PROPS = {"Attributes": {"Attributes": {}}, "AuthoredHipHeight": {"Float32": 2.0},
            "Capabilities": {"SecurityCapabilities": 0}, "GuidBinaryString": {"BinaryString": "AAAAAAAAAAAAAAAAAAAAAA=="},
            "Sandboxed": {"Bool": False}, "SerializedOverrides": {"BinaryString": ""}, "SourceAssetId": {"Int64": -1},
            "Tags": {"Tags": []}}


def _pose(name, pos, quat, children=(), style=0, weight=1.0):
    props = copy.deepcopy(POSE_PROPS)
    props["EasingStyle"] = {"Enum": style}
    props["Weight"] = {"Float32": float(weight)}
    m = quat_to_mat(quat)
    props["CFrame"] = {"CFrame": {"position": [round(float(v), 5) for v in pos],
                                  "orientation": [[round(float(v), 6) for v in row] for row in m]}}
    return {"class": "Pose", "name": name, "ref": _ref(), "props": props, "children": list(children)}


def write_sequence(anim, samples, fps, times=None):
    """Anim + sampled joints {joint: (positions, quats)} at `fps` -> KeyframeSequence JSON node.
    Every key is Linear: the motion is already smooth in the samples."""
    props = copy.deepcopy(anim.props) if anim.props else copy.deepcopy(KS_PROPS)
    props["Loop"] = {"Bool": bool(anim.loop)}
    props["Priority"] = {"Enum": int(anim.priority)}
    n = len(next(iter(samples.values()))[0])
    kfs = []
    for i in range(n):
        limbs = [_pose(j, samples[j][0][i], samples[j][1][i]) for j in LIMBS if j in samples]
        if "Torso" in samples:
            torso = _pose("Torso", samples["Torso"][0][i], samples["Torso"][1][i], limbs)
        else:                            # structural only: holds the limbs, does not drive the torso
            torso = _pose("Torso", (0, 0, 0), np.array([1.0, 0, 0, 0]), limbs, weight=0.0)
        root = _pose("HumanoidRootPart", (0, 0, 0), np.array([1.0, 0, 0, 0]), [torso], weight=0.0)
        kp = copy.deepcopy(KF_PROPS)
        kp["Time"] = {"Float32": round(float(times[i]) if times is not None else min(i / fps, anim.length), 5)}
        kfs.append({"class": "Keyframe", "name": "Keyframe", "ref": _ref(), "props": kp, "children": [root]})
    return {"class": "KeyframeSequence", "name": anim.name, "ref": _ref(), "props": props, "children": kfs}


def frame_times(length, fps):
    n = max(2, int(round(length * fps)) + 1)
    return np.linspace(0.0, length, n)
