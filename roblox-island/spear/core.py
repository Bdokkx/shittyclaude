"""Geometry core for the spearfishing islands.

Everything is a list of Roblox parts (blocks) with a full rotation, built in nested local frames:

    m = Model()
    with m.at((10, 0, 5), ry=30):          # move + rotate a local frame
        m.box((0, 2, 0), (4, 4, 4), "rock")  # centre + size in that frame

Rotations use Roblox's CFrame.fromEulerAnglesYXZ convention (R = Ry * Rx * Rz, degrees here),
so the Luau builder can rebuild each part exactly. Studs, Y up, water surface at y = 0.
"""
import contextlib
import math

# ---------------------------------------------------------------- 3x3 matrices


def _rx(a):
    c, s = math.cos(a), math.sin(a)
    return ((1, 0, 0), (0, c, -s), (0, s, c))


def _ry(a):
    c, s = math.cos(a), math.sin(a)
    return ((c, 0, s), (0, 1, 0), (-s, 0, c))


def _rz(a):
    c, s = math.cos(a), math.sin(a)
    return ((c, -s, 0), (s, c, 0), (0, 0, 1))


def mmul(a, b):
    return tuple(tuple(sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)) for i in range(3))


def mvec(a, v):
    return tuple(sum(a[i][k] * v[k] for k in range(3)) for i in range(3))


IDENT = ((1, 0, 0), (0, 1, 0), (0, 0, 1))


def euler(rx=0.0, ry=0.0, rz=0.0):
    """Degrees, Roblox fromEulerAnglesYXZ order."""
    return mmul(mmul(_ry(math.radians(ry)), _rx(math.radians(rx))), _rz(math.radians(rz)))


def to_euler(R):
    """Inverse of euler(): returns (rx, ry, rz) in degrees."""
    sx = max(-1.0, min(1.0, -R[1][2]))
    rx = math.asin(sx)
    if abs(sx) < 0.99999:
        ry = math.atan2(R[0][2], R[2][2])
        rz = math.atan2(R[1][0], R[1][1])
    else:  # gimbal lock: fold everything into ry
        ry = math.atan2(-R[2][0], R[0][0])
        rz = 0.0
    return math.degrees(rx), math.degrees(ry), math.degrees(rz)


# ---------------------------------------------------------------- model


class Model:
    """A flat list of parts plus a frame stack and context (stage, folder, tier, cluster tag)."""

    def __init__(self, name):
        self.name = name
        self.parts = []
        self.texts = []
        self._frames = [((0.0, 0.0, 0.0), IDENT)]
        self._ctx = [dict(stage="terrain", folder="Terrain", tier=0, tag=None, collide=True, shadow=True)]

    # frames -------------------------------------------------------------
    @contextlib.contextmanager
    def at(self, pos=(0, 0, 0), rx=0.0, ry=0.0, rz=0.0):
        p0, r0 = self._frames[-1]
        wp = tuple(p0[i] + mvec(r0, pos)[i] for i in range(3))
        self._frames.append((wp, mmul(r0, euler(rx, ry, rz))))
        try:
            yield
        finally:
            self._frames.pop()

    @contextlib.contextmanager
    def ctx(self, **kw):
        c = dict(self._ctx[-1])
        c.update(kw)
        self._ctx.append(c)
        try:
            yield
        finally:
            self._ctx.pop()

    def world(self, p):
        p0, r0 = self._frames[-1]
        return tuple(p0[i] + mvec(r0, p)[i] for i in range(3))

    # parts --------------------------------------------------------------
    def box(self, center, size, color, rx=0.0, ry=0.0, rz=0.0, mat="Plastic", light=None, **kw):
        """Block centred at `center` (local frame), rotated by (rx, ry, rz) about its own centre."""
        sx, sy, sz = size
        if min(sx, sy, sz) <= 0.04:
            return None
        p0, r0 = self._frames[-1]
        c = self._ctx[-1]
        part = dict(
            size=(round(sx, 3), round(sy, 3), round(sz, 3)),
            pos=tuple(round(p0[i] + mvec(r0, center)[i], 3) for i in range(3)),
            R=mmul(r0, euler(rx, ry, rz)),
            color=color, mat=mat, light=light,
            stage=c["stage"], folder=c["folder"], tier=c["tier"], tag=c["tag"],
            collide=kw.get("collide", c["collide"]), shadow=kw.get("shadow", c["shadow"]),
            name=kw.get("name"), transparency=kw.get("transparency", 0.0), effect=kw.get("effect"),
        )
        part["id"] = len(self.parts)
        self.parts.append(part)
        return part

    def octagon(self, y, r, h, color, **kw):
        """Regular octagon with apothem r (centre at local x=z=0, mid-height y) built from 6 parts:
        two crossing bars + four 45-degree strips that fill the corners exactly (no 8-point star)."""
        q = r * (math.sqrt(2) - 1)               # half a side
        self.box((0, y, 0), (2 * r, h, 2 * q), color, **kw)
        self.box((0, y, 0), (2 * q, h, 2 * r), color, **kw)
        c = (r + q) / 2 - q / (2 * math.sqrt(2))   # corner strip centre (each axis)
        for a, b in ((1, 1), (-1, -1), (1, -1), (-1, 1)):
            self.box((a * c, y, b * c), (2 * q, h, q), color, ry=45 if a == b else -45, **kw)

    def span(self, a, b, color, **kw):
        """Box from corner a to corner b (local frame, axis aligned in that frame)."""
        center = tuple((a[i] + b[i]) / 2 for i in range(3))
        size = tuple(abs(b[i] - a[i]) for i in range(3))
        return self.box(center, size, color, **kw)

    def beam(self, a, b, thick, color, roll=0.0, **kw):
        """Square beam from point a to point b (local frame), for posts, branches, ropes."""
        d = [b[i] - a[i] for i in range(3)]
        length = math.sqrt(sum(x * x for x in d))
        if length < 1e-6:
            return None
        center = tuple((a[i] + b[i]) / 2 for i in range(3))
        ry = math.degrees(math.atan2(d[0], d[2]))               # turn toward the target...
        rx = math.degrees(math.atan2(math.hypot(d[0], d[2]), d[1]))  # ...then tip +Y over onto it
        t = thick if isinstance(thick, (tuple, list)) else (thick, thick)
        with self.at(center, ry=ry):
            with self.at((0, 0, 0), rx=rx):
                return self.box((0, 0, 0), (t[0], length, t[1]), color, ry=roll, **kw)

    def text(self, part, string, color="#FFFFFF", face="Front", font_size=None):
        """Readable sign text on a face of `part` (SurfaceGui in Roblox, text object in renders)."""
        c = self._ctx[-1]
        self.texts.append(dict(part=part["id"],
                               text=string, color=color, face=face, tier=c["tier"], stage=c["stage"]))


def poly_contains(poly, x, z):
    inside = False
    n = len(poly)
    for i in range(n):
        x1, z1 = poly[i]
        x2, z2 = poly[(i + 1) % n]
        if (z1 > z) != (z2 > z) and x < (x2 - x1) * (z - z1) / (z2 - z1) + x1:
            inside = not inside
    return inside


def resample(poly, step):
    """Points every ~`step` studs along a closed polyline, with tangent directions."""
    out = []
    n = len(poly)
    carry = 0.0
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        seg = math.hypot(b[0] - a[0], b[1] - a[1])
        if seg < 1e-9:
            continue
        tx, tz = (b[0] - a[0]) / seg, (b[1] - a[1]) / seg
        t = carry
        while t < seg:
            out.append((a[0] + tx * t, a[1] + tz * t, tx, tz))
            t += step
        carry = t - seg
    return out
