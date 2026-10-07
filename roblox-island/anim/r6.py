"""R6 rig maths for KeyframeSequences: CFrames, the standard R6 Motor6D joints, sampling a sequence the way
Roblox does (per pose: previous keyframe's easing, slerped rotation), forward kinematics and conversion
between joint-space Pose CFrames and intuitive character-space rotations.

Character space = the Torso's frame at rest: X right, Y up, -Z forward (Roblox convention).
A limb "rotation" is about its joint pivot, expressed in its parent's frame:
    rot(x=+30) on an arm or leg swings it FORWARD, rot(z=+30) on the right arm lifts it out sideways.
"""
import math

# ---------------------------------------------------------------- CFrame = (pos, 3x3 rows)

IDENT = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))


def mm(a, b):
    return tuple(tuple(sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)) for i in range(3))


def mv(a, v):
    return tuple(sum(a[i][k] * v[k] for k in range(3)) for i in range(3))


def tr(a):
    return tuple(tuple(a[j][i] for j in range(3)) for i in range(3))


class CF:
    __slots__ = ("p", "R")

    def __init__(self, p=(0.0, 0.0, 0.0), R=IDENT):
        self.p, self.R = tuple(p), R

    @staticmethod
    def comps(c):
        """Roblox GetComponents order: x, y, z, R00, R01, R02, R10, R11, R12, R20, R21, R22."""
        return CF(c[0:3], (tuple(c[3:6]), tuple(c[6:9]), tuple(c[9:12])))

    def components(self):
        return [*self.p, *self.R[0], *self.R[1], *self.R[2]]

    def __mul__(self, o):
        return CF(tuple(self.p[i] + mv(self.R, o.p)[i] for i in range(3)), mm(self.R, o.R))

    def inv(self):
        Rt = tr(self.R)
        return CF(tuple(-x for x in mv(Rt, self.p)), Rt)

    def point(self, v):
        return tuple(self.p[i] + mv(self.R, v)[i] for i in range(3))


def rx(a):
    c, s = math.cos(a), math.sin(a)
    return ((1, 0, 0), (0, c, -s), (0, s, c))


def ry(a):
    c, s = math.cos(a), math.sin(a)
    return ((c, 0, s), (0, 1, 0), (-s, 0, c))


def rz(a):
    c, s = math.cos(a), math.sin(a)
    return ((c, -s, 0), (s, c, 0), (0, 0, 1))


def euler(x=0.0, y=0.0, z=0.0):
    """Degrees; same order as CFrame.Angles (R = Rx * Ry * Rz)."""
    return mm(mm(rx(math.radians(x)), ry(math.radians(y))), rz(math.radians(z)))


def to_euler(R):
    """Inverse of euler() -> (x, y, z) degrees."""
    sy = max(-1.0, min(1.0, R[0][2]))
    y = math.asin(sy)
    if abs(sy) < 0.9999:
        x = math.atan2(-R[1][2], R[2][2])
        z = math.atan2(-R[0][1], R[0][0])
    else:
        x, z = math.atan2(R[2][1], R[1][1]), 0.0
    return math.degrees(x), math.degrees(y), math.degrees(z)


# ---------------------------------------------------------------- quaternions (slerp)

def quat(R):
    t = R[0][0] + R[1][1] + R[2][2]
    if t > 0:
        s = math.sqrt(t + 1.0) * 2
        return ((R[2][1] - R[1][2]) / s, (R[0][2] - R[2][0]) / s, (R[1][0] - R[0][1]) / s, 0.25 * s)
    if R[0][0] > R[1][1] and R[0][0] > R[2][2]:
        s = math.sqrt(1.0 + R[0][0] - R[1][1] - R[2][2]) * 2
        return (0.25 * s, (R[0][1] + R[1][0]) / s, (R[0][2] + R[2][0]) / s, (R[2][1] - R[1][2]) / s)
    if R[1][1] > R[2][2]:
        s = math.sqrt(1.0 + R[1][1] - R[0][0] - R[2][2]) * 2
        return ((R[0][1] + R[1][0]) / s, 0.25 * s, (R[1][2] + R[2][1]) / s, (R[0][2] - R[2][0]) / s)
    s = math.sqrt(1.0 + R[2][2] - R[0][0] - R[1][1]) * 2
    return ((R[0][2] + R[2][0]) / s, (R[1][2] + R[2][1]) / s, 0.25 * s, (R[1][0] - R[0][1]) / s)


def qmat(q):
    x, y, z, w = q
    return ((1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)),
            (2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)),
            (2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)))


def slerp(a, b, t):
    qa, qb = quat(a), quat(b)
    d = sum(x * y for x, y in zip(qa, qb))
    if d < 0:
        qb, d = tuple(-x for x in qb), -d
    if d > 0.9995:
        q = tuple(x + (y - x) * t for x, y in zip(qa, qb))
    else:
        th = math.acos(d)
        s = math.sin(th)
        wa, wb = math.sin((1 - t) * th) / s, math.sin(t * th) / s
        q = tuple(wa * x + wb * y for x, y in zip(qa, qb))
    n = math.sqrt(sum(x * x for x in q))
    return qmat(tuple(x / n for x in q))


def lerp_cf(a, b, t):
    return CF(tuple(x + (y - x) * t for x, y in zip(a.p, b.p)), slerp(a.R, b.R, t))


# ---------------------------------------------------------------- easing (Roblox Pose easing styles)

def ease(style, direction, t):
    if style == "Constant":
        return 0.0
    if style == "Linear":
        return t

    def base(u):           # "In" curve
        if style in ("Cubic", "CubicV2"):
            return u ** 3
        if style == "Elastic":
            if u in (0, 1):
                return u
            return -(2 ** (10 * (u - 1))) * math.sin((u - 1.075) * 2 * math.pi / 0.3)
        if style == "Bounce":
            return 1 - bounce_out(1 - u)
        return u

    if direction == "In":
        return base(t)
    if direction == "Out":
        return 1 - base(1 - t)
    return base(2 * t) / 2 if t < 0.5 else 1 - base(2 - 2 * t) / 2


def bounce_out(u):
    if u < 1 / 2.75:
        return 7.5625 * u * u
    if u < 2 / 2.75:
        u -= 1.5 / 2.75
        return 7.5625 * u * u + 0.75
    if u < 2.5 / 2.75:
        u -= 2.25 / 2.75
        return 7.5625 * u * u + 0.9375
    u -= 2.625 / 2.75
    return 7.5625 * u * u + 0.984375


# ---------------------------------------------------------------- the R6 rig

def _cf(x, y, z, *r):
    return CF((x, y, z), (r[0:3], r[3:6], r[6:9]))


JOINTS = {  # part1: (part0, C0, C1) - Roblox's default R6 Motor6Ds
    "Torso": ("HumanoidRootPart", _cf(0, 0, 0, -1, 0, 0, 0, 0, 1, 0, 1, 0), _cf(0, 0, 0, -1, 0, 0, 0, 0, 1, 0, 1, 0)),
    "Head": ("Torso", _cf(0, 1, 0, -1, 0, 0, 0, 0, 1, 0, 1, 0), _cf(0, -0.5, 0, -1, 0, 0, 0, 0, 1, 0, 1, 0)),
    "Right Arm": ("Torso", _cf(1, 0.5, 0, 0, 0, 1, 0, 1, 0, -1, 0, 0), _cf(-0.5, 0.5, 0, 0, 0, 1, 0, 1, 0, -1, 0, 0)),
    "Left Arm": ("Torso", _cf(-1, 0.5, 0, 0, 0, -1, 0, 1, 0, 1, 0, 0), _cf(0.5, 0.5, 0, 0, 0, -1, 0, 1, 0, 1, 0, 0)),
    "Right Leg": ("Torso", _cf(1, -1, 0, 0, 0, 1, 0, 1, 0, -1, 0, 0), _cf(0.5, 1, 0, 0, 0, 1, 0, 1, 0, -1, 0, 0)),
    "Left Leg": ("Torso", _cf(-1, -1, 0, 0, 0, -1, 0, 1, 0, 1, 0, 0), _cf(-0.5, 1, 0, 0, 0, -1, 0, 1, 0, 1, 0, 0)),
}
ORDER = ("Torso", "Head", "Right Arm", "Left Arm", "Right Leg", "Left Leg")
SIZES = {"HumanoidRootPart": (2, 2, 1), "Torso": (2, 2, 1), "Head": (1.2, 1.2, 1.2),
         "Right Arm": (1, 2, 1), "Left Arm": (1, 2, 1), "Right Leg": (1, 2, 1), "Left Leg": (1, 2, 1)}


def to_transform(part, rot=(0, 0, 0), offset=(0, 0, 0)):
    """Character-space rotation (degrees, about the joint pivot, parent frame) + offset (studs, parent frame)
    -> the Pose CFrame (Motor6D.Transform) Roblox stores.  T = Rc0^-1 * R * Rc0."""
    Rc0 = JOINTS[part][1].R
    R = euler(*rot)
    T = mm(mm(tr(Rc0), R), Rc0)
    return CF(mv(tr(Rc0), offset), T)


def from_transform(part, T):
    """Pose CFrame -> (rot degrees, offset) in character space (inverse of to_transform)."""
    Rc0 = JOINTS[part][1].R
    R = mm(mm(Rc0, T.R), tr(Rc0))
    return to_euler(R), mv(Rc0, T.p)


def fk(transforms, root=CF()):
    """transforms: part -> Pose CFrame. Returns world CFrames of every part (root = HumanoidRootPart)."""
    world = {"HumanoidRootPart": root}
    for part in ORDER:
        p0, C0, C1 = JOINTS[part]
        T = transforms.get(part, CF())
        world[part] = world[p0] * C0 * T * C1.inv()
    return world


# ---------------------------------------------------------------- sampling a sequence

def flatten(poses, out=None):
    out = {} if out is None else out
    for p in poses:
        out[p["name"]] = p
        flatten(p.get("kids", []), out)
    return out


def sample(seq, t):
    """seq: dict from the dump (keyframes with time + nested poses). Returns part -> Pose CFrame at time t."""
    kfs = [k for k in seq["keyframes"] if "time" in k]
    tracks = {}
    for k in kfs:
        for name, p in flatten(k["poses"]).items():
            tracks.setdefault(name, []).append((k["time"], p))
    res = {}
    for name, tr_ in tracks.items():
        tr_.sort(key=lambda x: x[0])
        prev = tr_[0]
        nxt = None
        for item in tr_:
            if item[0] <= t:
                prev = item
            else:
                nxt = item
                break
        a = CF.comps(prev[1]["cf"])
        if nxt is None or t <= prev[0]:
            res[name] = a
            continue
        u = (t - prev[0]) / (nxt[0] - prev[0])
        e = ease(prev[1]["style"], prev[1]["dir"], u)
        res[name] = lerp_cf(a, CF.comps(nxt[1]["cf"]), e)
    return res


def length(seq):
    return max(k["time"] for k in seq["keyframes"] if "time" in k)
