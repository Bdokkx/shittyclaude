"""Batch 2, section A: the CustomerKit.

Every piece is a Model with an invisible Handle at the centre of the R6 part it sits on
(Head, Torso or Right Arm), so `Handle.CFrame = part.CFrame` plus a WeldConstraint puts it
on. Geometry is modelled in that part's frame: the classic head (SpecialMesh Head x 1.25
on the 2 x 1 x 1 Head) is a rounded cylinder 1.25 across and 1.25 tall; the torso is
2 x 2 x 1; the arm 1 x 2 x 1 with the fist at its bottom (y = -1). Hand things are held in
the fist (on a line front to back at y = -0.82) and point forward, out of the front of the fist.
"""
import math

import numpy as np

import spsgeo as G
from assets_common import P
from spsgeo import CF, T, RX, RY, RZ, S

TAU = math.tau
HR, HH, RC = 0.625, 0.625, 0.25          # classic head: radius, half height, rim rounding
U_TOP = HR - RC                          # arc length (from the top pole) where the flat top ends
U_ARC = U_TOP + math.pi / 2 * RC         # ... and where the straight side starts


# ---------------------------------------------------------------- head-hugging shapes

def _surf(u, th, t):
    """Point t proud of the classic head, at arc length u from the top pole (the side runs on
    straight down past the head), angle th (0 = front, -Z; +90 deg = the right side, +X)."""
    if u <= U_TOP:
        r, y, nr, ny = u, HH, 0.0, 1.0
    elif u <= U_ARC:
        ph = (u - U_TOP) / RC
        r, y = U_TOP + RC * math.sin(ph), HH - RC + RC * math.cos(ph)
        nr, ny = math.sin(ph), math.cos(ph)
    else:
        r, y, nr, ny = HR, HH - RC - (u - U_ARC), 1.0, 0.0
    r, y = r + t * nr, y + t * ny
    return np.array((r * math.sin(th), y, -r * math.cos(th)))


def _u_of(y):
    if y <= HH - RC:
        return U_ARC + (HH - RC - y)
    c = min(1.0, max(-1.0, (y - (HH - RC)) / RC))
    return U_TOP + RC * math.acos(c)


CLEAR = 0.03         # the least a cap's surface may come to the head between its vertices


def _profile(u, t):
    """(r, y) of the point t proud of the head at arc length u, and its outward normal."""
    p = _surf(u, 0.0, t)
    q = _surf(u, 0.0, t + 1.0)
    return np.array((p[2] * -1, p[1])), np.array((-(q[2] - p[2]), q[1] - p[1]))


def _clear_rows(us, ts):
    """Thicken rows so the straight segments between them stay CLEAR outside the rounded rim
    of the head (a row-to-row chord across the rim sags into it)."""
    ts = list(ts)
    for _ in range(4):
        extra = [0.0] * len(us)
        for j in range(len(us) - 1):
            a, na = _profile(us[j], ts[j])
            b, nb = _profile(us[j + 1], ts[j + 1])
            d = b - a
            nrm = np.array((d[1], -d[0])) / (np.linalg.norm(d) + 1e-12)
            if np.dot(nrm, na + nb) < 0:
                nrm = -nrm                       # outward
            worst = 0.0
            for s in np.linspace(0.0, 1.0, 9)[1:-1]:
                h, _ = _profile(us[j] + (us[j + 1] - us[j]) * s, 0.0)
                worst = max(worst, np.dot(h - a, nrm) + CLEAR)
            extra[j] = max(extra[j], worst)
            extra[j + 1] = max(extra[j + 1], worst)
        if max(extra) <= 1e-6:
            break
        ts = [t + e for t, e in zip(ts, extra)]
    return ts


def cap(yb, thick, n=10, rows=4, inner=(0.0, 0.0, 0.0), sx=1.0, sz=1.0, lift=0.0):
    """Hair or a hat crown: from the edge height yb(th) up over the top of the head,
    thick(th, f) proud of it (f = 0 at the edge .. 1 at the top). A closed solid: the
    outer surface, a fan to the top pole and a hidden fan from the edge into the head.
    The rows are thickened where a straight facet would cut into the head's rounded rim,
    and spread out by 1 / cos(180 / n) so the flat sides between columns clear it too."""
    g = G.Geo()
    cols = []
    widen = 1.0 / math.cos(math.pi / n)
    for k in range(n):
        th = TAU * k / n
        ub = _u_of(yb(th))
        us = [ub * (1 - j / rows) for j in range(rows)] + [0.0]
        ts = _clear_rows(us, [thick(th, j / rows) for j in range(rows)] + [thick(th, 1.0)])
        col = []
        for j in range(rows):
            f = j / rows
            p = _surf(us[j], th, ts[j])
            p[1] += lift * f
            col.append(len(g.v))
            g.v.append((p[0] * sx * widen, p[1], p[2] * sz * widen))
        cols.append(col)
    pole = len(g.v)
    g.v.append((0.0, HH + thick(0.0, 1.0) + lift, 0.0))
    ip = len(g.v)
    g.v.append(tuple(inner))
    for k in range(n):
        a, b = cols[k], cols[(k + 1) % n]
        for j in range(rows - 1):
            g.f.extend(_bulge(g.v, a[j], b[j], b[j + 1], a[j + 1]))
        g.f.append((a[-1], b[-1], pole))
        g.f.append((b[0], a[0], ip))
    return G.outward(g)


def _bulge(v, i0, i1, i2, i3):
    """Split the quad i0 i1 i2 i3 along the diagonal that folds outwards (further from the
    head), so neither triangle dips towards the head."""
    p = [np.array(v[i]) for i in (i0, i1, i2, i3)]
    if np.linalg.norm((p[0] + p[2]) / 2) >= np.linalg.norm((p[1] + p[3]) / 2):
        return [(i0, i1, i2), (i0, i2, i3)]
    return [(i0, i1, i3), (i1, i2, i3)]


def band(y0, y1, t0, t1, th0=0.0, th1=TAU, n=12, closed=True):
    """A strip round the side of the head between heights y0(th) and y1(th), from t0 to
    t1 proud of it, for th in [th0, th1]."""
    g = G.Geo()
    secs = []
    m = n if closed else n + 1
    for k in range(m):
        th = th0 + (th1 - th0) * k / n
        d = np.array((math.sin(th), 0.0, -math.cos(th)))
        a, b = y0(th), y1(th)
        r0, r1 = HR + t0(th), HR + t1(th)
        secs.append([d * r0 + (0, a, 0), d * r1 + (0, a, 0), d * r1 + (0, b, 0), d * r0 + (0, b, 0)])
    rings = []
    for s in secs:
        ring = []
        for p in s:
            ring.append(len(g.v))
            g.v.append(tuple(p))
        rings.append(ring)
    pairs = list(zip(rings, rings[1:]))
    if closed:
        pairs.append((rings[-1], rings[0]))
    for a, b in pairs:
        for i in range(4):
            j = (i + 1) % 4
            g.f.append((a[i], b[i], b[j], a[j]))
    if not closed:
        g.f.append(tuple(rings[0]))
        g.f.append(tuple(rings[-1][::-1]))
    return G.outward(g)


def const(v):
    return lambda *a: v


def edge(front, side, back, side_l=None, wave=0.0, waves=0):
    """Edge height round the head: front (th=0), sides (+-90), back (180); smooth between."""
    side_l = side if side_l is None else side_l

    def f(th):
        c = math.cos(th)
        s = math.sin(th)
        sd = side if s >= 0 else side_l
        if c >= 0:
            v = sd + (front - sd) * c ** 1.5
        else:
            v = sd + (back - sd) * (-c) ** 1.2
        return v + wave * math.sin(waves * th)
    return f


def wrap_face(g, z0=-0.02):
    """Bend a flat (x, y) shape modelled at z ~ 0 onto the front of the classic head."""
    out = []
    for x, y, z in g.v:
        zz = -math.sqrt(max(HR * HR - x * x, 0.01)) + z0 + z
        out.append((x, y, zz))
    g.v = out
    return g


def ftube(path, w, h, close_ends=True):
    """Flat strap along a path (rectangular section w across, h thick; up = +Y-ish)."""
    path = [np.asarray(p, float) for p in path]
    secs = []
    for k, p in enumerate(path):
        t = (path[min(k + 1, len(path) - 1)] - path[max(k - 1, 0)])
        t /= np.linalg.norm(t)
        side = np.cross(t, (0.0, 1.0, 0.0))
        if np.linalg.norm(side) < 1e-3:
            side = np.cross(t, (0.0, 0.0, 1.0))
        side /= np.linalg.norm(side)
        up = np.cross(side, t)
        secs.append([p + side * w / 2 + up * h / 2, p - side * w / 2 + up * h / 2, p - side * w / 2 - up * h / 2,
                     p + side * w / 2 - up * h / 2])
    return G.outward(G.loft(secs, close_ends))


def rbox(w, h, d, r=0.12, c=(0, 0, 0), n=1):
    """Box with rounded vertical edges (top view outline), extruded along Y."""
    pts = G.rounded_rect_pts(w, d, r, n)
    return G.extrude(pts, h, "y", c)


# ---------------------------------------------------------------- the pieces
# each returns [(part name, colour, material, transparency, Geo)] in its R6 part's frame

KIT = {}          # name -> (category, body part, builder, notes)


def piece(name, category, body, notes=""):
    def deco(fn):
        KIT[name] = (category, body, fn, notes)
        return fn
    return deco


def hp(parts):
    return [(p[0], p[1], p[2] if len(p) > 2 else "Plastic", p[3] if len(p) > 3 else 0.0, p[-1]) for p in parts]


# -- hair (Head) ---------------------------------------------------------------------------

@piece("Short", "Hair", "Head", "short crop")
def _short():
    g = cap(edge(0.38, 0.06, -0.18), lambda th, f: 0.04 + 0.05 * f, n=10)
    return [("Hair", "kit_hair", "Plastic", 0.0, g)]


@piece("Side", "Hair", "Head", "side parting, the fringe swept over one brow")
def _side():
    yb0 = edge(0.4, -0.1, -0.3, side_l=-0.04)

    def yb(th):
        d = math.atan2(math.sin(th - 0.45), math.cos(th - 0.45))       # 0 at the swoop (right front)
        return yb0(th) - 0.26 * math.exp(-(d / 0.55) ** 2)

    def th_f(th, f):
        d = math.atan2(math.sin(th - 0.45), math.cos(th - 0.45))
        return 0.06 + 0.04 * f + 0.17 * math.exp(-(d / 0.7) ** 2) * math.sin(math.pi * min(1.0, f * 1.3))
    g = cap(yb, th_f, n=10, rows=4)
    return [("Hair", "kit_hair", "Plastic", 0.0, g)]


@piece("Bowl", "Hair", "Head", "bowl cut, straight fringe all round")
def _bowl():
    g = cap(edge(0.22, 0.14, 0.06), lambda th, f: 0.17 - 0.09 * f, n=12)
    return [("Hair", "kit_hair", "Plastic", 0.0, g)]


@piece("Long", "Hair", "Head", "long, down the back to the shoulder blades")
def _long():
    g = cap(edge(0.34, -0.32, -0.3), lambda th, f: 0.07 + 0.05 * f, n=8)
    secs = []
    for y, half, zb, zc in ((-0.2, 0.62, 0.42, 0.72), (-0.75, 0.66, 0.55, 0.74), (-1.4, 0.6, 0.56, 0.68)):
        outer, inner = [], []
        for k in range(5):
            x = -half + 2 * half * k / 4
            bulge = 1 - (x / half) ** 2
            outer.append((x, y, zb + (zc - zb) * bulge + 0.1))
            inner.append((x, y, zb + (zc - zb) * bulge - 0.02))
        secs.append(outer + inner[::-1])
    panel = G.outward(G.loft(secs))
    return [("Hair", "kit_hair", "Plastic", 0.0, G.Geo().add([g, panel]))]


@piece("Bun", "Hair", "Head", "pulled back into a bun")
def _bun():
    g = cap(edge(0.36, 0.0, -0.22), lambda th, f: 0.05 + 0.03 * f, n=9)
    g.add(G.sphere(0.27, 7, 4, scale=(1, 0.9, 1), c=(0, 0.5, 0.62)))
    return [("Hair", "kit_hair", "Plastic", 0.0, g)]


@piece("Ponytail", "Hair", "Head", "ponytail with a band")
def _ponytail():
    g = cap(edge(0.36, -0.02, -0.24), lambda th, f: 0.05 + 0.04 * f, n=8)
    tail = G.tube([(0, 0.32, 0.66), (0, 0.18, 0.84), (0, -0.25, 0.88), (0, -0.62, 0.8)], 0.17, 5)
    vs = tail.arr()
    for i, p in enumerate(vs):                      # taper towards the end
        k = (0.32 - p[1]) / 0.95
        c = np.array((0, p[1], 0.8 + 0.06 * (1 - k)))
        tail.v[i] = tuple(c + (p - c) * (1.0 - 0.45 * max(0.0, min(1.0, k))))
    g.add(tail)
    tie = G.box(0.3, 0.12, 0.3, (0, 0.26, 0.76)).xf(T(0, 0.26, 0.76) @ RX(-30) @ T(0, -0.26, -0.76))
    return [("Hair", "kit_hair", "Plastic", 0.0, g), ("Band", "kit_cloth2", "Plastic", 0.0, tie)]


@piece("Curly", "Hair", "Head", "chunky curls")
def _curly():
    th_f = lambda th, f: 0.13 + 0.06 * math.sin(5 * th + 3 * f) * (0.5 + f) + 0.05 * f
    g = cap(edge(0.3, -0.06, -0.3, wave=0.05, waves=7), th_f, n=12, rows=3)
    return [("Hair", "kit_hair2", "Plastic", 0.0, g)]


@piece("Mohawk", "Hair", "Head", "a spiked crest front to back")
def _mohawk():
    # side outline (z, y): base follows the head top, top edge in spikes
    base = []
    for k in range(7):
        a = -1.25 + 2.5 * k / 6                  # angle over the top, front (-) to back (+)
        base.append((0.66 * math.sin(a) * 0.98, 0.66 * math.cos(a) - 0.06))
    top = []
    for k in range(7):
        a = -1.25 + 2.5 * (6 - k) / 6
        h = 0.5 if k % 2 == 0 else 0.26
        rr = 0.66 + h
        top.append((rr * math.sin(a) * 0.98, rr * math.cos(a) - 0.06))
    outline = base + top
    g = G.extrude([(z, y) for z, y in outline], 0.26, "x")
    return [("Hair", "kit_hair2", "Plastic", 0.0, g)]


@piece("BaldRing", "Hair", "Head", "bald on top, a ring of hair round the back and sides")
def _baldring():
    g = band(const(-0.18), lambda th: 0.3 - 0.06 * math.cos(th - math.pi) ** 2 + 0.04 * math.sin(7 * th),
             const(-0.01), lambda th: 0.09 + 0.02 * math.sin(5 * th), th0=math.radians(70), th1=math.radians(290),
             n=10, closed=False)
    return [("Hair", "kit_hair", "Plastic", 0.0, g)]


@piece("Afro", "Hair", "Head", "big round afro")
def _afro():
    th_f = lambda th, f: (0.2 + 0.28 * f + 0.1 * max(0.0, -math.cos(th))) * (1 + 0.08 * math.sin(6 * th + 4 * f))
    g = cap(edge(0.36, -0.1, -0.32), th_f, n=12, rows=4, lift=0.08)
    return [("Hair", "kit_hair2", "Plastic", 0.0, g)]


# -- hats (Head) ---------------------------------------------------------------------------

def _peak(r_back=0.6, reach=0.62, y=0.18, droop=8):
    pts = []
    for k in range(9):
        a = math.radians(-75 + 150 * k / 8)
        pts.append((r_back * math.sin(a), -r_back * math.cos(a)))
    for k in range(9):
        a = math.radians(75 - 150 * k / 8)
        pts.append((0.74 * math.sin(a), -(r_back + reach) * math.cos(a) ** 0.8))
    g = G.slab_poly(pts, 0.06, (0, y, 0))
    return g.xf(T(0, y, -0.55) @ RX(droop) @ T(0, -y, 0.55))


@piece("Cap", "Hat", "Head", "baseball cap")
def _cap():
    crown = cap(edge(0.2, 0.12, 0.06), lambda th, f: 0.06 + 0.02 * f, n=12, lift=0.05)
    crown.add(G.cyl(0.07, 0.06, 6, "y", (0, HH + 0.13, 0)))
    return [("Crown", "kit_cloth", "Plastic", 0.0, crown), ("Peak", "kit_cloth", "Plastic", 0.0, _peak())]


@piece("Beanie", "Hat", "Head", "knitted beanie with a turned-up cuff")
def _beanie():
    yb = edge(0.2, 0.0, -0.1)
    knit = cap(yb, lambda th, f: 0.08 + 0.08 * f, n=12, lift=0.12)
    cuff = band(lambda th: yb(th) - 0.02, lambda th: yb(th) + 0.24, const(0.04), const(0.15), n=12)
    return [("Knit", "kit_cloth2", "Plastic", 0.0, knit), ("Cuff", "kit_cloth2", "Plastic", 0.0, cuff)]


def shell(outer_cols, inner_cols, top_out, top_in):
    """Closed shell between two column grids (outer faces out, inner faces in, a rim at the
    open edge). Columns run from the edge (index 0) towards the top pole."""
    g = G.Geo()
    n, rows = len(outer_cols), len(outer_cols[0])
    o = [[g.v.append(tuple(p)) or len(g.v) - 1 for p in col] for col in outer_cols]
    i = [[g.v.append(tuple(p)) or len(g.v) - 1 for p in col] for col in inner_cols]
    po = len(g.v)
    g.v.append(top_out)
    pi_ = len(g.v)
    g.v.append(top_in)
    for k in range(n):
        a, b = o[k], o[(k + 1) % n]
        c, d = i[k], i[(k + 1) % n]
        for j in range(rows - 1):
            g.f.append((a[j], b[j], b[j + 1], a[j + 1]))
            g.f.append((c[j + 1], d[j + 1], d[j], c[j]))
        g.f.append((a[-1], b[-1], po))
        g.f.append((d[-1], c[-1], pi_))
        g.f.append((b[0], a[0], c[0], d[0]))
    return G.outward(g)


@piece("Hood", "Hat", "Head", "hood up (hides the hair: attribute HidesHair)")
def _hood():
    def yb(th):
        c = math.cos(th)
        return -0.95 + 1.38 * max(0.0, c) ** 0.7
    n, rows = 16, 4
    oc, ic, lc, lc2 = [], [], [], []
    for k in range(n):
        th = TAU * k / n
        ub = _u_of(yb(th))
        o_, i_, l_, l2 = [], [], [], []
        for j in range(rows):
            f = j / rows
            u = ub * (1 - f)
            po = _surf(u, th, 0.16 + 0.04 * f)
            po[2] *= 1.06
            po[1] += 0.06 * f
            o_.append(po)
            i_.append(_surf(u, th, 0.07))
            l_.append(_surf(u, th, 0.065))
            l2.append(_surf(u, th, 0.03))
        oc.append(o_)
        ic.append(i_)
        lc.append(l_)
        lc2.append(l2)
    hood = shell(oc, ic, (0.0, HH + 0.26, 0.0), (0.0, HH + 0.07, 0.0))
    lining = shell(lc, lc2, (0.0, HH + 0.065, 0.0), (0.0, HH + 0.03, 0.0))
    return [("Hood", "kit_cloth", "Plastic", 0.0, hood), ("Lining", "kit_dark", "Plastic", 0.0, lining)]


@piece("TruckerCap", "Hat", "Head", "trucker cap: foam front, mesh back")
def _trucker():
    yb = edge(0.22, 0.12, 0.08)
    crown = cap(yb, lambda th, f: 0.06 + 0.02 * f, n=12, lift=0.12)
    crown.add(G.cyl(0.07, 0.06, 6, "y", (0, HH + 0.2, 0)))
    mesh = band(lambda th: yb(th) + 0.04, const(0.52), const(0.075), const(0.1), th0=math.radians(100),
                th1=math.radians(260), n=8, closed=False)
    return [("Front", "kit_light", "Plastic", 0.0, crown), ("Mesh", "kit_cloth", "Plastic", 0.0, mesh),
            ("Peak", "kit_cloth", "Plastic", 0.0, _peak(y=0.2))]


@piece("BucketHat", "Hat", "Head", "bucket hat")
def _bucket():
    crown = G.lathe([(0.0, 0.12), (0.73, 0.12), (0.7, 0.74), (0.6, 0.86), (0.0, 0.88)], 12)
    brim = G.lathe_loop([(0.7, 0.22), (1.06, 0.02), (1.06, -0.04), (0.7, 0.14)], 14)
    return [("Crown", "kit_cloth", "Plastic", 0.0, G.outward(crown)), ("Brim", "kit_cloth", "Plastic", 0.0, brim)]


@piece("WoolHat", "Hat", "Head", "tall wool hat with a bobble")
def _woolhat():
    yb = edge(0.22, 0.02, -0.08)
    knit = cap(yb, lambda th, f: 0.07 + 0.1 * f, n=12, lift=0.3)
    cuff = band(lambda th: yb(th) - 0.02, lambda th: yb(th) + 0.22, const(0.04), const(0.14), n=12)
    bob = G.sphere(0.21, 7, 4, c=(0, HH + 0.52, 0))
    return [("Knit", "kit_cloth2", "Plastic", 0.0, knit), ("Cuff", "kit_light", "Plastic", 0.0, cuff),
            ("Bobble", "kit_light", "Plastic", 0.0, bob)]


@piece("Headphones", "Hat", "Head", "over-ear headphones")
def _headphones():
    path = []
    for k in range(11):
        a = math.pi * k / 10
        path.append((-0.72 * math.cos(a), 0.12 + 0.62 * math.sin(a) + 0.06 * math.sin(a) ** 4, 0.0))
    bandg = ftube(path, 0.14, 0.07)
    cups = G.Geo()
    for sx in (-1, 1):
        cups.add(G.cyl(0.26, 0.2, 10, "x", (sx * 0.76, 0.0, 0.0)))
        cups.add(G.cyl(0.06, 0.34, 6, "y", (sx * 0.76, 0.2, 0.0)))
    return [("Band", "kit_dark", "Plastic", 0.0, bandg), ("Cups", "kit_cloth2", "Plastic", 0.0, cups)]


# -- face things (Head; the Scarf sits on the Torso) -------------------------------------------

def _rims(w, h, bar, y=0.1, sep=0.25):
    fr, ln = G.Geo(), G.Geo()
    for sx in (-1, 1):
        c = (sx * sep, y, 0.0)
        o = G.rounded_rect_pts(w, h, 0.06, 1, c[0], c[1])
        i = G.rounded_rect_pts(w - 2 * bar, h - 2 * bar, 0.04, 1, c[0], c[1])
        n = len(o)
        g = G.Geo()
        for x, yy in o:
            g.v.append((x, yy, -0.02))
        for x, yy in o:
            g.v.append((x, yy, 0.02))
        for x, yy in i:
            g.v.append((x, yy, -0.02))
        for x, yy in i:
            g.v.append((x, yy, 0.02))
        for k in range(n):
            j = (k + 1) % n
            g.f += [(k, j, n + j, n + k), (2 * n + j, 2 * n + k, 3 * n + k, 3 * n + j),
                    (k, 2 * n + k, 2 * n + j, j), (n + k, n + j, 3 * n + j, 3 * n + k)]
        fr.add(G.outward(g))
        ln.add(G.slab_poly([(x, -yy) for x, yy in i], 0.01, (0, 0, 0)).xf(RX(90)).xf(T(0, 0, 0)))
    return fr, ln


def _glasses(w, h, bar, dark):
    fr, ln = _rims(w, h, bar)
    fr.add(G.box(0.12, 0.04, 0.04, (0, 0.14, 0.0)))
    fr = wrap_face(fr, -0.035)
    ln = wrap_face(ln, -0.035)
    for sx in (-1, 1):
        x0 = sx * (0.25 + w / 2 - 0.02)
        z0 = -math.sqrt(max(HR * HR - x0 * x0, 0.01)) - 0.04
        fr.add(ftube([(x0, 0.12, z0), (sx * 0.66, 0.12, -0.3), (sx * 0.665, 0.1, 0.12)], 0.04, 0.05))
    return [("Frame", "kit_dark", "Plastic", 0.0, fr),
            ("Lenses", "kit_dark" if dark else "kit_lens", "SmoothPlastic" if dark else "Glass", 0.0 if dark else 0.5, ln)]


@piece("Glasses", "Face", "Head", "glasses (clear lenses, Transparency 0.5)")
def _glasses_plain():
    return _glasses(0.36, 0.26, 0.045, False)


@piece("Sunglasses", "Face", "Head", "dark sunglasses")
def _sunglasses():
    return _glasses(0.42, 0.28, 0.05, True)


@piece("Moustache", "Face", "Head", "moustache")
def _moustache():
    pts = [(0.0, 0.0), (0.14, 0.01), (0.27, -0.05), (0.36, -0.17), (0.35, -0.3), (0.26, -0.26), (0.16, -0.2),
           (0.05, -0.19), (0.0, -0.17), (-0.05, -0.19), (-0.16, -0.2), (-0.26, -0.26), (-0.35, -0.3), (-0.36, -0.17),
           (-0.27, -0.05), (-0.14, 0.01)]
    g = G.extrude(pts, 0.14, "z", (0, -0.03, 0))
    return [("Moustache", "kit_hair", "Plastic", 0.0, wrap_face(g, -0.04))]


@piece("Beard", "Face", "Head", "full beard round the jaw")
def _beard():
    def top(th):
        c = abs(math.cos(th))
        return -0.27 + 0.4 * (1 - c) ** 1.2
    g = band(lambda th: -0.98 + 0.45 * (1 - max(0.0, math.cos(th))) ** 0.8, top, const(-0.02),
             lambda th: 0.07 + 0.2 * max(0.0, math.cos(th)) ** 3, th0=math.radians(-100), th1=math.radians(100),
             n=12, closed=False)
    return [("Beard", "kit_hair", "Plastic", 0.0, g)]


@piece("Scarf", "Face", "Torso", "scarf round the neck (sits on the Torso)")
def _scarf():
    loop = []
    for k in range(12):
        a = TAU * k / 12
        loop.append((0.66 * math.sin(a), 1.12 - 0.04 * math.cos(a), -0.52 * math.cos(a)))
    secs = []
    for k, p in enumerate(loop):
        a = TAU * k / 12
        d = np.array((math.sin(a), 0, -math.cos(a)))
        p = np.array(p)
        secs.append([p - d * 0.05 + (0, 0.15, 0), p + d * 0.14 + (0, 0.15, 0), p + d * 0.14 - (0, 0.15, 0),
                     p - d * 0.05 - (0, 0.15, 0)])
    ring = G.Geo()
    rings = []
    for s in secs:
        r = []
        for q in s:
            r.append(len(ring.v))
            ring.v.append(tuple(q))
        rings.append(r)
    for i in range(12):
        a, b = rings[i], rings[(i + 1) % 12]
        for q in range(4):
            j = (q + 1) % 4
            ring.f.append((a[q], b[q], b[j], a[j]))
    ring = G.outward(ring)
    tail1 = G.box(0.36, 0.95, 0.08, (-0.28, 0.48, -0.62)).xf(T(-0.28, 1.0, -0.6) @ RZ(-6) @ RX(-4) @ T(0.28, -1.0, 0.6))
    tail2 = G.box(0.34, 0.7, 0.08, (-0.02, 0.6, -0.66)).xf(T(0, 1.0, -0.64) @ RZ(8) @ T(0, -1.0, 0.64))
    stripes = G.Geo()
    for y in (0.22, 0.42):
        stripes.add(G.box(0.38, 0.08, 0.1, (-0.28, y, -0.62)).xf(T(-0.28, 1.0, -0.6) @ RZ(-6) @ RX(-4) @ T(0.28, -1.0, 0.6)))
    return [("Scarf", "kit_cloth2", "Plastic", 0.0, G.Geo().add([ring, tail1, tail2])),
            ("Stripes", "kit_light", "Plastic", 0.0, stripes)]


# -- torso things -----------------------------------------------------------------------------

@piece("Backpack", "Torso", "Torso", "backpack with shoulder straps")
def _backpack():
    bag = rbox(1.4, 1.5, 0.6, 0.18, (0, 0.05, 0.82), n=2)
    top = G.lathe([(0.0, 0.0), (0.7, 0.0), (0.6, 0.12), (0.0, 0.16)], 8, sz=0.3 / 0.7).xf(T(0, 0.8, 0.82))
    pocket = rbox(0.9, 0.55, 0.22, 0.08, (0, -0.28, 1.2))
    straps = G.Geo()
    for sx in (-1, 1):
        straps.add(ftube([(sx * 0.62, 0.62, 0.55), (sx * 0.7, 1.06, 0.22), (sx * 0.7, 1.07, -0.25),
                          (sx * 0.68, 0.6, -0.56), (sx * 0.66, -0.25, -0.56)], 0.2, 0.06))
    return [("Bag", "kit_cloth", "Plastic", 0.0, G.Geo().add([bag, G.outward(top)])),
            ("Pocket", "kit_cloth2", "Plastic", 0.0, pocket), ("Straps", "kit_dark", "Plastic", 0.0, straps)]


@piece("Satchel", "Torso", "Torso", "satchel on a strap across the chest")
def _satchel():
    strap = ftube([(0.62, 1.06, 0.3), (0.68, 1.07, -0.1), (0.6, 0.85, -0.56), (-0.45, -0.45, -0.57),
                   (-0.56, -0.62, -0.57)], 0.16, 0.05)
    strap.add(ftube([(0.62, 1.06, 0.3), (0.55, 0.8, 0.56), (-0.6, -0.55, 0.57), (-1.0, -0.62, 0.4),
                     (-1.02, -0.62, -0.3)], 0.16, 0.05))
    bag = rbox(0.9, 0.72, 0.3, 0.08, (-0.5, -0.82, -0.72))
    flap = G.box(0.92, 0.36, 0.06, (-0.5, -0.66, -0.9))
    flap.add(G.box(0.14, 0.12, 0.05, (-0.5, -0.86, -0.94)))
    return [("Bag", "kit_leather", "Plastic", 0.0, bag), ("Flap", "kit_leather", "Plastic", 0.0, flap),
            ("Strap", "kit_dark", "Plastic", 0.0, strap)]


@piece("Hoodie", "Torso", "Torso", "hoodie: kangaroo pocket, drawstrings, hood down on the back")
def _hoodie():
    pocket = G.extrude([(-0.66, -0.96), (0.66, -0.96), (0.52, -0.34), (-0.52, -0.34)], 0.07, "z", (0, 0, -0.535))
    hood = G.blob(0.55, 8, 5, scale=(1.15, 0.6, 0.62), jitter=0.04, seed=5, c=(0, 0.86, 0.62))
    collar = G.torus(0.62, 0.09, 12, 4, "y", (0, 1.04, 0)).xf(S(1.0, 1.0, 0.85))
    strings = G.Geo()
    for sx in (-1, 1):
        strings.add(G.box(0.05, 0.62, 0.05, (sx * 0.17, 0.66, -0.54)))
        strings.add(G.box(0.08, 0.1, 0.08, (sx * 0.17, 0.32, -0.54)))
    return [("Hood", "kit_cloth", "Plastic", 0.0, G.Geo().add([hood, collar])),
            ("Pocket", "kit_cloth", "Plastic", 0.0, pocket), ("Strings", "kit_light", "Plastic", 0.0, strings)]


@piece("Tie", "Torso", "Torso", "shirt collar and tie")
def _tie():
    tie = G.Geo().add([G.extrude([(-0.13, 0.96), (0.13, 0.96), (0.1, 0.76), (-0.1, 0.76)], 0.08, "z", (0, 0, -0.55)),
                       G.extrude([(-0.09, 0.76), (0.09, 0.76), (0.16, -0.3), (0, -0.48), (-0.16, -0.3)], 0.05, "z",
                                 (0, 0, -0.54))])
    collar = G.Geo()
    for sx in (-1, 1):
        collar.add(G.extrude([(sx * 0.04, 1.0), (sx * 0.4, 1.0), (sx * 0.24, 0.74)], 0.05, "z", (0, 0, -0.53)))
    return [("Tie", "kit_cloth2", "Plastic", 0.0, tie), ("Collar", "kit_light", "Plastic", 0.0, collar)]


@piece("HiVisVest", "Torso", "Torso", "hi-vis vest with reflective stripes")
def _hivis():
    front = G.extrude([(-1.04, -0.96), (1.04, -0.96), (1.04, 0.86), (0.6, 0.86), (0.08, 0.2), (-0.08, 0.2),
                       (-0.6, 0.86), (-1.04, 0.86)], 0.06, "z", (0, 0, -0.53))
    back = G.box(2.08, 1.82, 0.06, (0, -0.05, 0.53))
    sides = G.Geo().add([G.box(0.06, 1.82, 1.12, (sx * 1.03, -0.05, 0)) for sx in (-1, 1)])
    straps = G.Geo().add([G.box(0.34, 0.08, 1.12, (sx * 0.82, 0.9, 0)) for sx in (-1, 1)])
    vest = G.Geo().add([front, back, sides, straps])
    st = G.Geo()
    for y in (-0.62, -0.22):
        st.add(G.box(2.12, 0.14, 0.04, (0, y, -0.57)))
        st.add(G.box(2.12, 0.14, 0.04, (0, y, 0.57)))
    for sx in (-1, 1):
        st.add(G.box(0.14, 0.75, 0.04, (sx * 0.76, 0.47, -0.57)))
        st.add(G.box(0.14, 1.0, 0.04, (sx * 0.76, 0.36, 0.57)))
    return [("Vest", "kit_yellow", "Plastic", 0.0, vest), ("Stripes", "kit_silver", "SmoothPlastic", 0.0, st)]


@piece("RaincoatCollar", "Torso", "Torso", "turned-up raincoat collar with toggles")
def _raincoat():
    col = band(const(-0.62), lambda th: -0.12 + 0.06 * abs(math.sin(th)), const(0.0), const(0.1),
               th0=math.radians(28), th1=math.radians(332), n=12, closed=False)
    col = col.xf(T(0, 1.5, 0) @ S(1.14, 1.0, 1.0))
    lap = G.Geo()
    for sx in (-1, 1):
        lap.add(G.extrude([(sx * 0.22, 1.02), (sx * 0.62, 1.02), (sx * 0.3, 0.3), (sx * 0.06, 0.3)], 0.06, "z",
                          (0, 0, -0.53)))
    btn = G.Geo()
    for y in (0.05, -0.45):
        btn.add(G.box(0.36, 0.1, 0.08, (0, y, -0.55)))
    return [("Collar", "kit_yellow", "Plastic", 0.0, G.Geo().add([col, lap])),
            ("Buttons", "kit_dark", "Plastic", 0.0, btn)]


# -- in the right hand (Right Arm; fist at y = -1) ----------------------------------------------
# Held in the fist on the grip line (x 0, y -0.82, running front to back) and pointing forward
# (-Z) out of the front of the fist, so the item shows from the front with the arm at rest.

GRIP_Y = -0.82


def held(g, tilt):
    """Tip a hand item `tilt` degrees nose-down about the grip line."""
    return g.xf(T(0, GRIP_Y, 0) @ RX(-tilt) @ T(0, -GRIP_Y, 0))


@piece("Umbrella", "Hand", "Right Arm", "closed umbrella carried like a walking stick: crook behind the fist, "
                                        "tip forward and 30 degrees down")
def _umbrella():
    y = GRIP_Y
    crook = G.tube([(0, y, -0.55), (0, y, 0.55), (0, y - 0.1, 0.74), (0, y - 0.3, 0.8), (0, y - 0.48, 0.7),
                     (0, y - 0.54, 0.54)], 0.08, 6)
    canopy = G.Geo()
    canopy.add(G.frustum(0.3, 0.24, 0.2, 8, "z", (0, y, -0.8), cap0=False))     # the gathered rib ends
    canopy.add(G.frustum(0.07, 0.3, 1.55, 8, "z", (0, y, -1.675), cap1=False))  # tapering to the tip
    canopy.add(G.ring(0.26, 0.14, 0.09, 8, "z", (0, y, -1.3)))           # the strap
    tip = G.Geo().add([G.cyl(0.04, 0.32, 6, "z", (0, y, -2.6)), G.cyl(0.035, 0.2, 6, "z", (0, y, -0.6))])
    return [("Canopy", "kit_cloth2", "Plastic", 0.0, held(canopy, 30)),
            ("Crook", "kit_leather", "Plastic", 0.0, held(crook, 30)),
            ("Tip", "kit_metal", "Metal", 0.0, held(tip, 30))]


@piece("Phone", "Hand", "Right Arm", "phone lying in the fist, pointing forward, screen up")
def _phone():
    body = rbox(0.42, 0.08, 0.8, 0.07, (0, GRIP_Y - 0.04, -0.62))
    screen = G.box(0.34, 0.02, 0.64, (0, GRIP_Y + 0.01, -0.65))
    return [("Body", "kit_dark", "Plastic", 0.0, body), ("Screen", (90, 140, 190), "SmoothPlastic", 0.0, screen)]


@piece("CarKeys", "Hand", "Right Arm", "key fob in the fist with the key pointing forward, a second key "
                                       "hanging from the ring")
def _keys():
    y = GRIP_Y
    fob = rbox(0.12, 0.26, 0.42, 0.04, (0, y - 0.13, -0.56))
    keys = G.Geo()
    keys.add(G.box(0.03, 0.08, 0.36, (0, y + 0.01, -0.95)))                  # the blade
    for t in range(3):
        keys.add(G.box(0.03, 0.05, 0.05, (0, y - 0.05, -0.86 - 0.09 * t)))      # its teeth
    keys.add(G.torus(0.12, 0.025, 10, 4, "x", (0, y - 0.38, -0.7)))         # the ring under the fob
    keys.add(G.box(0.04, 0.12, 0.16, (0, y - 0.55, -0.7)))                   # a second key hanging from it
    keys.add(G.box(0.03, 0.3, 0.07, (0, y - 0.76, -0.7)))
    for t in range(2):
        keys.add(G.box(0.03, 0.05, 0.05, (0, y - 0.7 - 0.1 * t, -0.65)))
    return [("Keys", "kit_metal", "Metal", 0.0, keys), ("Fob", "kit_dark", "Plastic", 0.0, fob)]


LEAD_END = (0.0, GRIP_Y - 0.76, -1.5)


@piece("DogLead", "Hand", "Right Arm", "dog lead: the hand loop round the fist and the first bit of lead, "
                                       "forward and down (Attachment LeadEnd on the Handle for a Beam/Rope to the dog)")
def _doglead():
    y = GRIP_Y + 0.1
    s2 = math.sqrt(2.0)
    loop = G.ring(0.57 * s2, 0.52 * s2, 0.14, 4, "y", (0, y, 0), phase=math.pi / 4)   # square, clear of the arm
    lead = ftube([(0, y - 0.02, -0.58), (0, y - 0.12, -0.84), (0, y - 0.42, -1.16), LEAD_END], 0.12, 0.05)
    ring = G.torus(0.1, 0.025, 8, 4, "z", (0, y - 0.02, -0.62))
    return [("Lead", "kit_cloth2", "Plastic", 0.0, G.Geo().add([loop, lead])),
            ("Ring", "kit_metal", "Metal", 0.0, ring)]


@piece("Newspaper", "Hand", "Right Arm", "rolled-up newspaper gripped in the middle, pointing forward")
def _newspaper():
    y = GRIP_Y
    paper = G.Geo().add([G.cyl(0.17, 1.9, 8, "z", (0, y, -0.2)),
                         G.box(0.02, 0.1, 1.9, (0.167, y + 0.04, -0.2))])         # the outer sheet's edge
    top = y + 0.167                                                            # the roll's flat top
    pr = G.Geo()
    for k in range(4):
        pr.add(G.box(0.022, 0.02, 0.36, (-0.045 + 0.03 * k, top, -0.8)))        # columns of print
    pr.add(G.box(0.12, 0.02, 0.1, (0, top, -1.06)))                          # headline
    pr.add(G.box(0.12, 0.02, 0.12, (0, top, 0.58)))
    return [("Paper", "kit_light", "Plastic", 0.0, paper), ("Print", "kit_dark", "Plastic", 0.0, pr)]


ORDER = ["Short", "Side", "Bowl", "Long", "Bun", "Ponytail", "Curly", "Mohawk", "BaldRing", "Afro",
         "Cap", "Beanie", "Hood", "TruckerCap", "BucketHat", "WoolHat", "Headphones",
         "Glasses", "Sunglasses", "Moustache", "Beard", "Scarf",
         "Backpack", "Satchel", "Hoodie", "Tie", "HiVisVest", "RaincoatCollar",
         "Umbrella", "Phone", "CarKeys", "DogLead", "Newspaper"]
assert sorted(ORDER) == sorted(KIT), set(ORDER) ^ set(KIT)


def place(sc, parent, name, part_cf):
    """Build kit piece `name` as a Model whose Handle sits at part_cf (the R6 part's CFrame)."""
    from assets_common import col, handle
    category, body, fn, notes = KIT[name]
    m = sc.model(parent, name)
    h = handle(sc, m, part_cf)
    for pname, colr, mat, tr, geo in fn():
        mp = sc.mesh(m, pname, "Kit%s__%s" % (name, pname), geo, part_cf, col(colr), material=mat, transparency=tr,
                     anchored=False, collide=False, touch=False, query=False, massless=True, owner="Kit" + name)
        sc.weld(h, mp, "Weld")
    if name == "DogLead":
        sc.attachment(h, "LeadEnd", part_cf * CF(LEAD_END))
    sc.attr(m, "Category", category)
    sc.attr(m, "BodyPart", body)
    if name == "Hood":
        sc.attr(m, "HidesHair", True)
    return m
