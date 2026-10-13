"""Pure numpy geometry in ROBLOX space (Y up, characters face -Z).

CF is a Roblox-style CFrame (position + 3x3 rotation). Geo is a polygon mesh
(vertex list + face index lists) with chunky low-poly primitives: boxes, wedges,
frustums, lathes, spheres, tori and extruded outlines. Nothing here needs Blender,
so the map can be described, checked and written to JSON without it.
"""
import math

import numpy as np

TAU = math.tau


# ---------------------------------------------------------------- rotations / CFrames

def rx(deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return np.array(((1, 0, 0), (0, c, -s), (0, s, c)), float)


def ry(deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return np.array(((c, 0, s), (0, 1, 0), (-s, 0, c)), float)


def rz(deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return np.array(((c, -s, 0), (s, c, 0), (0, 0, 1)), float)


def rot_axis(axis, deg):
    a = np.asarray(axis, float)
    a = a / np.linalg.norm(a)
    t = math.radians(deg)
    K = np.array(((0, -a[2], a[1]), (a[2], 0, -a[0]), (-a[1], a[0], 0)))
    return np.eye(3) + math.sin(t) * K + (1 - math.cos(t)) * K @ K


def clean(R):
    """Snap near-0/±1 entries so axis-aligned turns stay exact."""
    R = np.array(R, float)
    for v in (0.0, 1.0, -1.0):
        R[np.abs(R - v) < 1e-9] = v
    return R


class CF:
    """A CFrame: p is the position, R the rotation (columns = right, up, back)."""
    __slots__ = ("p", "R")

    def __init__(self, p=(0, 0, 0), R=None):
        self.p = np.array(p, float)
        self.R = np.eye(3) if R is None else clean(R)

    def __mul__(self, o):
        if isinstance(o, CF):
            return CF(self.p + self.R @ o.p, self.R @ o.R)
        return self.p + self.R @ np.asarray(o, float)

    def inv(self):
        Rt = self.R.T
        return CF(-Rt @ self.p, Rt)

    @property
    def look(self):
        return -self.R[:, 2]

    def m4(self):
        m = np.eye(4)
        m[:3, :3] = self.R
        m[:3, 3] = self.p
        return m

    def is_axis_aligned(self):
        return bool(np.all(np.isin(np.round(self.R, 9), (-1.0, 0.0, 1.0))))

    def __repr__(self):
        return "CF(%s, %s)" % (np.round(self.p, 3).tolist(), np.round(self.R, 3).tolist())


def cf(x=0.0, y=0.0, z=0.0, R=None):
    return CF((x, y, z), R)


def facing(d):
    """Rotation whose -Z (LookVector) points along the horizontal direction d."""
    d = np.array(d, float)
    d[1] = 0
    d /= np.linalg.norm(d)
    Z = -d
    Y = np.array((0.0, 1.0, 0.0))
    X = np.cross(Y, Z)
    return clean(np.column_stack((X, Y, Z)))


def yaw(deg):
    """Facing by compass yaw: 0 = north (-Z), 90 = east (+X), 180 = south, 270 = west."""
    a = math.radians(deg)
    return facing((math.sin(a), 0.0, -math.cos(a)))


def look_at(pos, target, up=(0, 1, 0)):
    pos, target = np.asarray(pos, float), np.asarray(target, float)
    Z = pos - target
    Z /= np.linalg.norm(Z)
    X = np.cross(np.asarray(up, float), Z)
    if np.linalg.norm(X) < 1e-6:
        X = np.array((1.0, 0, 0))
    X /= np.linalg.norm(X)
    Y = np.cross(Z, X)
    return CF(pos, np.column_stack((X, Y, Z)))


# ---------------------------------------------------------------- 4x4 transforms for geometry

def M(R=None, t=(0, 0, 0), s=None):
    m = np.eye(4)
    if R is not None:
        m[:3, :3] = R
    if s is not None:
        m[:3, :3] = m[:3, :3] @ np.diag(np.broadcast_to(np.asarray(s, float), (3,)))
    m[:3, 3] = t
    return m


def T(x=0.0, y=0.0, z=0.0):
    return M(t=(x, y, z))


def RX(deg):
    return M(rx(deg))


def RY(deg):
    return M(ry(deg))


def RZ(deg):
    return M(rz(deg))


def S(x, y=None, z=None):
    return M(s=(x, x if y is None else y, x if z is None else z))


# ---------------------------------------------------------------- polygon mesh

class Geo:
    def __init__(self, v=None, f=None):
        self.v = [] if v is None else [tuple(map(float, p)) for p in v]
        self.f = [] if f is None else [tuple(x) for x in f]

    def copy(self):
        return Geo(list(self.v), list(self.f))

    def add(self, other, m=None):
        """Append another Geo (optionally transformed by 4x4 m)."""
        if isinstance(other, (list, tuple)):
            for o in other:
                self.add(o, m)
            return self
        base = len(self.v)
        vs = np.array(other.v, float).reshape(-1, 3)
        flip = False
        if m is not None:
            vs = (m[:3, :3] @ vs.T).T + m[:3, 3]
            flip = np.linalg.det(m[:3, :3]) < 0
        self.v += [tuple(p) for p in vs]
        for f in other.f:
            f = tuple(i + base for i in f)
            self.f.append(f[::-1] if flip else f)
        return self

    def xf(self, m):
        return Geo().add(self, m)

    def tris(self):
        return sum(len(f) - 2 for f in self.f)

    def arr(self):
        return np.array(self.v, float).reshape(-1, 3)

    def bbox(self):
        a = self.arr()
        return a.min(0), a.max(0)

    def flip(self):
        self.f = [f[::-1] for f in self.f]
        return self

    def weld(self, eps=1e-5):
        """Merge coincident vertices (keeps faces; drops degenerate ones)."""
        key, remap, nv = {}, [], []
        for p in self.v:
            k = tuple(np.round(np.asarray(p) / eps).astype(np.int64))
            if k not in key:
                key[k] = len(nv)
                nv.append(p)
            remap.append(key[k])
        nf = []
        for f in self.f:
            g = []
            for i in f:
                j = remap[i]
                if not g or g[-1] != j:
                    g.append(j)
            if len(g) > 2 and g[0] == g[-1]:
                g.pop()
            if len(set(g)) >= 3:
                nf.append(tuple(g))
        self.v, self.f = nv, nf
        return self


def merge(*geos):
    g = Geo()
    for x in geos:
        g.add(x)
    return g


# ---------------------------------------------------------------- primitives

def box(sx, sy, sz, c=(0, 0, 0)):
    hx, hy, hz = sx / 2, sy / 2, sz / 2
    cx, cy, cz = c
    v = [(cx + x, cy + y, cz + z) for x in (-hx, hx) for y in (-hy, hy) for z in (-hz, hz)]
    # index = xi*4 + yi*2 + zi ; faces wound counter-clockwise seen from outside
    f = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    return Geo(v, f)


def box_lohi(lo, hi):
    lo, hi = np.asarray(lo, float), np.asarray(hi, float)
    s = hi - lo
    return box(*s, c=(lo + hi) / 2)


def wedge(sx, sy, sz, c=(0, 0, 0)):
    """Roblox WedgePart: full bottom, tall face at +Z, slope down towards -Z."""
    hx, hy, hz = sx / 2, sy / 2, sz / 2
    cx, cy, cz = c
    v = [(-hx, -hy, -hz), (hx, -hy, -hz), (hx, -hy, hz), (-hx, -hy, hz), (-hx, hy, hz), (hx, hy, hz)]
    v = [(cx + a, cy + b, cz + d) for a, b, d in v]
    f = [(0, 1, 2, 3), (3, 2, 5, 4), (0, 4, 5, 1), (0, 3, 4), (1, 5, 2)]
    return Geo(v, f)


def frustum(r0, r1, h, n=8, axis="y", c=(0, 0, 0), cap0=True, cap1=True, phase=None, sx=1.0, sz=1.0):
    """Cylinder / cone frustum along an axis, centred on c. r0 at the - end, r1 at the + end."""
    if phase is None:
        phase = math.pi / n          # a flat side faces +X / +Z (blockier look)
    g = Geo()
    ring0, ring1 = [], []
    for i in range(n):
        a = phase + TAU * i / n
        ca, sa = math.cos(a), math.sin(a)
        ring0.append(len(g.v))
        g.v.append((r0 * ca * sx, -h / 2, r0 * sa * sz))
        ring1.append(len(g.v))
        g.v.append((r1 * ca * sx, h / 2, r1 * sa * sz))
    for i in range(n):
        j = (i + 1) % n
        g.f.append((ring0[i], ring1[i], ring1[j], ring0[j]))
    if cap0 and r0 > 1e-9:
        g.f.append(tuple(ring0))
    if cap1 and r1 > 1e-9:
        g.f.append(tuple(ring1[::-1]))
    g.weld()
    return _orient(g, axis, c)


def cyl(r, h, n=8, axis="y", c=(0, 0, 0), **kw):
    return frustum(r, r, h, n, axis, c, **kw)


def _orient(g, axis, c):
    if axis == "x":
        m = RZ(-90)
    elif axis == "z":
        m = RX(90)
    else:
        m = np.eye(4)
    m = T(*c) @ m
    return g.xf(m)


def lathe(profile, n=8, phase=None, close=True, sx=1.0, sz=1.0, rmod=None):
    """Surface of revolution around +Y. profile = [(r, y), ...] from bottom to top.
    r == 0 at an end makes a pole. Faces point outwards for a bottom-to-top profile."""
    if phase is None:
        phase = math.pi / n
    g = Geo()
    rings = []
    for r, y in profile:
        if r <= 1e-9:
            rings.append([len(g.v)])
            g.v.append((0.0, y, 0.0))
        else:
            ring = []
            for i in range(n):
                a = phase + TAU * i / n
                k = rmod(a) if rmod else 1.0
                ring.append(len(g.v))
                g.v.append((r * k * sx * math.cos(a), y, r * k * sz * math.sin(a)))
            rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        if len(a) == 1 and len(b) == 1:
            continue
        if len(a) == 1:
            for i in range(n):
                g.f.append((a[0], b[i], b[(i + 1) % n]))
        elif len(b) == 1:
            for i in range(n):
                g.f.append((a[i], b[0], a[(i + 1) % n]))
        else:
            for i in range(n):
                j = (i + 1) % n
                g.f.append((a[i], b[i], b[j], a[j]))
    if close:
        if len(rings[0]) > 1:
            g.f.append(tuple(rings[0]))
        if len(rings[-1]) > 1:
            g.f.append(tuple(rings[-1][::-1]))
    return g


def sphere(r, n=8, rings=5, scale=(1, 1, 1), c=(0, 0, 0)):
    prof = [(r * math.sin(math.pi * k / rings), -r * math.cos(math.pi * k / rings)) for k in range(rings + 1)]
    prof[0] = (0.0, -r)
    prof[-1] = (0.0, r)
    g = lathe(prof, n)
    return g.xf(T(*c) @ S(*scale))


def torus(R_, r, n=12, m=6, axis="y", c=(0, 0, 0), phase=None):
    """Ring around the axis (lies in the plane across it)."""
    if phase is None:
        phase = math.pi / n
    g = Geo()
    rings = []
    for i in range(n):
        a = phase + TAU * i / n
        ring = []
        for j in range(m):
            b = TAU * j / m
            rr = R_ + r * math.cos(b)
            ring.append(len(g.v))
            g.v.append((rr * math.cos(a), r * math.sin(b), rr * math.sin(a)))
        rings.append(ring)
    for i in range(n):
        a, b = rings[i], rings[(i + 1) % n]
        for j in range(m):
            k = (j + 1) % m
            g.f.append((a[j], a[k], b[k], b[j]))
    return _orient(g, axis, c)


def ring(r_out, r_in, h, n=12, axis="y", c=(0, 0, 0), phase=None):
    """Flat washer / ring along an axis."""
    if phase is None:
        phase = math.pi / n
    g = Geo()
    o0, o1, i0, i1 = [], [], [], []
    for k in range(n):
        a = phase + TAU * k / n
        ca, sa = math.cos(a), math.sin(a)
        for lst, r, y in ((o0, r_out, -h / 2), (o1, r_out, h / 2), (i0, r_in, -h / 2), (i1, r_in, h / 2)):
            lst.append(len(g.v))
            g.v.append((r * ca, y, r * sa))
    for k in range(n):
        j = (k + 1) % n
        g.f.append((o0[k], o1[k], o1[j], o0[j]))          # outside
        g.f.append((i0[k], i0[j], i1[j], i1[k]))          # inside
        g.f.append((o1[k], i1[k], i1[j], o1[j]))          # top
        g.f.append((o0[k], o0[j], i0[j], i0[k]))          # bottom
    return _orient(g, axis, c)


# ---------------------------------------------------------------- outlines

def poly_area(pts):
    a = 0.0
    for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
        a += x0 * y1 - x1 * y0
    return a / 2


def triangulate(pts):
    """Ear clipping of a simple polygon (list of (x, y)). Returns index triples, CCW."""
    idx = list(range(len(pts)))
    if poly_area(pts) < 0:
        idx.reverse()
    P = [np.array(p, float) for p in pts]

    def inside(p, a, b, c):
        d1 = (p[0] - b[0]) * (a[1] - b[1]) - (a[0] - b[0]) * (p[1] - b[1])
        d2 = (p[0] - c[0]) * (b[1] - c[1]) - (b[0] - c[0]) * (p[1] - c[1])
        d3 = (p[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (p[1] - a[1])
        neg = d1 < -1e-12 or d2 < -1e-12 or d3 < -1e-12
        pos = d1 > 1e-12 or d2 > 1e-12 or d3 > 1e-12
        return not (neg and pos)

    tris = []
    guard = 0
    while len(idx) > 3 and guard < 10000:
        guard += 1
        n = len(idx)
        for k in range(n):
            i0, i1, i2 = idx[(k - 1) % n], idx[k], idx[(k + 1) % n]
            a, b, c = P[i0], P[i1], P[i2]
            cross = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
            if cross <= 1e-12:
                continue
            if any(inside(P[j], a, b, c) for j in idx if j not in (i0, i1, i2)):
                continue
            tris.append((i0, i1, i2))
            idx.pop(k)
            break
        else:
            break
    if len(idx) == 3:
        tris.append(tuple(idx))
    return tris


def is_convex(pts):
    s = 0
    n = len(pts)
    for k in range(n):
        a, b, c = np.array(pts[k - 1]), np.array(pts[k]), np.array(pts[(k + 1) % n])
        cr = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
        if abs(cr) < 1e-12:
            continue
        if s == 0:
            s = 1 if cr > 0 else -1
        elif (cr > 0) != (s > 0):
            return False
    return True


def extrude(pts, depth, axis="z", c=(0, 0, 0)):
    """2D outline (x, y) extruded along +-depth/2. axis='z': outline in XY (front view);
    axis='y': outline in XZ (top view, y of the outline -> Z); axis='x': outline in ZY."""
    pts = [tuple(map(float, p)) for p in pts]
    if poly_area(pts) < 0:
        pts = pts[::-1]
    n = len(pts)
    g = Geo()
    for x, y in pts:
        g.v.append((x, y, -depth / 2))
    for x, y in pts:
        g.v.append((x, y, depth / 2))
    for k in range(n):
        j = (k + 1) % n
        g.f.append((k, j, n + j, n + k))
    if is_convex(pts):
        g.f.append(tuple(range(n))[::-1])            # back (-Z)
        g.f.append(tuple(range(n, 2 * n)))            # front (+Z)
    else:
        for a, b, cc in triangulate(pts):
            g.f.append((a, cc, b))
            g.f.append((n + a, n + b, n + cc))
    if axis == "y":      # top view: outline (x, y) -> world (x, z), extruded along Y
        g = g.xf(M(np.array(((1, 0, 0), (0, 0, 1), (0, 1, 0)), float)))
    elif axis == "x":    # side view: outline (x, y) -> world (z, y), extruded along X
        g = g.xf(M(np.array(((0, 0, 1), (0, 1, 0), (1, 0, 0)), float)))
    return g.xf(T(*c))


def circle_pts(r, n=12, phase=None, cx=0.0, cy=0.0, sx=1.0, sy=1.0):
    if phase is None:
        phase = math.pi / n
    return [(cx + r * sx * math.cos(phase + TAU * k / n), cy + r * sy * math.sin(phase + TAU * k / n)) for k in range(n)]


def rounded_rect_pts(w, h, r, n=2, cx=0.0, cy=0.0):
    pts = []
    for (qx, qy, a0) in ((w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180),
                         (w / 2 - r, -h / 2 + r, 270)):
        for k in range(n + 1):
            a = math.radians(a0 + 90 * k / n)
            pts.append((cx + qx + r * math.cos(a), cy + qy + r * math.sin(a)))
    return pts


def loft(sections, close_ends=True):
    """Connect rings of equal length (each a list of 3D points) into a tube."""
    g = Geo()
    rings = []
    for s in sections:
        ring = []
        for p in s:
            ring.append(len(g.v))
            g.v.append(tuple(p))
        rings.append(ring)
    n = len(rings[0])
    for a, b in zip(rings, rings[1:]):
        for k in range(n):
            j = (k + 1) % n
            g.f.append((a[k], b[k], b[j], a[j]))
    if close_ends:
        g.f.append(tuple(rings[0]))
        g.f.append(tuple(rings[-1][::-1]))
    return g


def tube(path, r, n=6, close_ends=True):
    """A tube of radius r along a 3D polyline (rotation-minimising frames)."""
    path = [np.asarray(p, float) for p in path]
    secs = []
    up = np.array((0.0, 1.0, 0.0))
    for k, p in enumerate(path):
        if k == 0:
            t = path[1] - path[0]
        elif k == len(path) - 1:
            t = path[-1] - path[-2]
        else:
            t = (path[k + 1] - path[k - 1])
        t = t / np.linalg.norm(t)
        if abs(np.dot(up, t)) > 0.95:
            up = np.array((1.0, 0, 0))
        x = np.cross(up, t)
        x /= np.linalg.norm(x)
        y = np.cross(t, x)
        up = y
        secs.append([p + r * (math.cos(TAU * i / n + math.pi / n) * x + math.sin(TAU * i / n + math.pi / n) * y)
                     for i in range(n)])
    g = loft(secs, close_ends)
    # make the faces point outwards
    c = np.mean(np.array(g.v), 0)
    vs = np.array(g.v)
    f0 = g.f[0]
    nrm = np.cross(vs[f0[1]] - vs[f0[0]], vs[f0[2]] - vs[f0[0]])
    mid = vs[list(f0)].mean(0)
    ring_c = np.mean(np.array(secs[0]), 0)
    if np.dot(nrm, mid - ring_c) < 0:
        g.flip()
    return g


def ngon_disc(r, h, n=16, c=(0, 0, 0)):
    return cyl(r, h, n, "y", c)


def signed_volume(g):
    v = g.arr()
    s = 0.0
    for f in g.f:
        for k in range(1, len(f) - 1):
            s += np.dot(v[f[0]], np.cross(v[f[k]], v[f[k + 1]])) / 6
    return s


def outward(g):
    """Flip a closed mesh if its faces point inwards."""
    if signed_volume(g) < 0:
        g.flip()
    return g


def lathe_loop(loop, n=12, phase=None, rmod=None, sx=1.0, sz=1.0):
    """Revolve a closed (r, y) outline around +Y: rings, tori, rims."""
    if phase is None:
        phase = math.pi / n
    g = Geo()
    rings = []
    for r, y in loop:
        ring = []
        for i in range(n):
            a = phase + TAU * i / n
            k = rmod(a) if rmod else 1.0
            ring.append(len(g.v))
            g.v.append((r * k * sx * math.cos(a), y, r * k * sz * math.sin(a)))
        rings.append(ring)
    m = len(rings)
    for j in range(m):
        a, b = rings[j], rings[(j + 1) % m]
        for i in range(n):
            k = (i + 1) % n
            g.f.append((a[i], b[i], b[k], a[k]))
    return outward(g)


def lobed_ring(r_out, r_in, h, n=16, lobes=4, depth=0.12, phase=0.0):
    """Ring whose outline bulges into lobes (bell pepper slices)."""
    rm = lambda a: 1.0 + depth * math.cos(lobes * (a - phase))  # noqa: E731
    return lathe_loop([(r_in, -h / 2), (r_out, -h / 2), (r_out, h / 2), (r_in, h / 2)], n, rmod=rm)


def blob(r, n=10, rings=6, scale=(1, 1, 1), jitter=0.12, seed=1, c=(0, 0, 0), flat_bottom=None):
    """Lumpy low-poly ball (dough, bags, rocks). flat_bottom=y clips the underside flat."""
    rng = np.random.default_rng(seed)
    g = sphere(r, n, rings)
    vs = g.arr()
    out = []
    for p in vs:
        k = 1.0 + jitter * (rng.random() * 2 - 1)
        q = p * k * np.asarray(scale, float)
        if flat_bottom is not None:
            q[1] = max(q[1], flat_bottom)
        out.append(tuple(q))
    g.v = out
    g.weld()
    return outward(g).xf(T(*c))


def leaf_pts(length, width, n=6, tip=1.5):
    """Leaf outline from (0, 0) to (0, length), in the XY plane."""
    left, right = [], []
    for k in range(1, n):
        t = k / n
        w = width / 2 * math.sin(math.pi * t) ** (1.0 / tip) * (1.0 - 0.25 * t)
        right.append((w, length * t))
        left.append((-w, length * t))
    return [(0.0, 0.0)] + right + [(0.0, length)] + left[::-1]


def slab_poly(pts, thick, c=(0, 0, 0)):
    """Flat outline in the XZ plane (top view), thickness along Y, bottom at c[1]."""
    return extrude(pts, thick, "y", (c[0], c[1] + thick / 2, c[2]))
