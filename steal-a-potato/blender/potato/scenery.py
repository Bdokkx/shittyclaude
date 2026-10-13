"""Heroes and props in bricks: PotatoKit.Heroes.<AreaId> and PotatoKit.Props.<AreaId>.<Name>.

A hero stands against one wall of the corridor with its front (-Z) to the lane: a footprint at most
46 along X and 30 deep, up to 220 parts, as tall as it likes (the walls are 44). The parts players
stand on are solid (CanCollide and CanQuery on, CanTouch off); everything else is decoration
(anchored, CanCollide / CanTouch / CanQuery off). No shadow from parts under 2.5 studs.

A prop is 10 to 40 parts of decoration. It carries the attributes the scatterer reads: Count,
ScaleMin, ScaleMax, Band ("Edge", "Side" or "Any") and Solid.

Parts that move or glow carry Spin (degrees a second about the part's own Y), Flicker (on Neon) and
NightLamp (lit at night). Every part of a spinning thing is centred on its axle with its own Y along
it, so turning each part about its own Y turns the whole thing.

Every Model's pivot is the middle of its footprint on the ground (Y 0 in the frame it is built in).
"""
import math

import numpy as np

import spsgeo as G
from spsgeo import CF

from . import brickcheck
from .bricks import Bricks, hexc, mix, ori, shade  # noqa: F401  (re-exported for the area modules)

HERO_W, HERO_D, HERO_PARTS = 46.0, 30.0, 220
PROP_MIN, PROP_MAX = 10, 40
BANDS = ("Edge", "Side", "Any")
INK = "1e1a22"
FLAME = ("ff7a1a", "ffb02e", "ffe066")


class Build:
    """One Model under construction, built in its own frame with the ground at Y 0."""

    def __init__(self, sc, parent, name, seed=7):
        self.sc, self.name = sc, name
        self.m = sc.model(parent, name)
        self.deco = Bricks(sc, None, anchored=True, collide=False, touch=False, query=False)
        self.hard = Bricks(sc, None, anchored=True, collide=True, touch=False, query=True)
        self.rng = np.random.default_rng(seed)

    def p(self, name, size, pos, R=None, col="ffffff", material="Plastic", solid=False, spin=None, flicker=None,
          lamp=False, transparency=0.0, shadow=None, shape="Block"):
        b = self.hard if solid else self.deco
        part = b.part(self.m, name, size, np.asarray(pos, float), R, col, material=material,
                      transparency=transparency, shadow=shadow, shape=shape)
        at = part.p["attrs"]
        if spin is not None:
            at["Spin"] = float(spin)
        if flicker is not None:
            at["Flicker"] = float(flicker)
        if lamp:
            at["NightLamp"] = True
        return part

    def plate(self, name, size, pos, R=None, col=INK, **kw):
        """A flat plate that carries a face or a mark: SmoothPlastic, Smooth faces, no shadow."""
        kw.setdefault("shadow", False)
        return self.p(name, size, pos, R, col, material="SmoothPlastic", **kw)

    def parts(self):
        return [n for n in self.m.walk() if n.kind == "Part"]

    def finish(self, attrs=None):
        """PrimaryPart (the biggest part) and a pivot in the middle of the footprint on the ground."""
        parts = self.parts()
        lo, hi = bounds(parts)
        centre = np.array(((lo[0] + hi[0]) / 2, 0.0, (lo[2] + hi[2]) / 2))
        primary = max(parts, key=lambda q: float(np.prod(q.p["size"])))
        self.m.p["primary"] = primary
        primary.p["pivot"] = primary.p["cf"].inv() * CF(centre)
        if attrs:
            self.m.p.setdefault("attrs", {}).update(attrs)
        return self.m


def bounds(parts):
    lo = np.min([q.p["cf"].p - np.abs(q.p["cf"].R) @ (np.array(q.p["size"]) / 2) for q in parts], axis=0)
    hi = np.max([q.p["cf"].p + np.abs(q.p["cf"].R) @ (np.array(q.p["size"]) / 2) for q in parts], axis=0)
    return lo, hi


def pivot_of(m):
    pr = m.p["primary"]
    return pr.p["cf"] * pr.p["pivot"]


# ==================================================================== shapes in Folk Valley's idiom

def frame(d, n=None):
    """A turn whose own Y runs along d, its own Z as close to n as it can be."""
    y = np.asarray(d, float)
    y = y / np.linalg.norm(y)
    if n is None:
        n = (0.0, 0.0, -1.0) if abs(y[1]) > 0.9 else (0.0, 1.0, 0.0)
    z = np.asarray(n, float)
    z = z - y * (z @ y)
    if np.linalg.norm(z) < 1e-6:
        z = np.array((1.0, 0.0, 0.0)) - y * y[0]
    z /= np.linalg.norm(z)
    x = np.cross(y, z)
    return np.column_stack((x, y, z))


def bar(B, name, a, b, w, col, t=None, n=None, over=0.0, **kw):
    """A bar from a to b (stretched `over` past each end), w wide and t thick, its t side facing n."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = b - a
    L = float(np.linalg.norm(d))
    R = frame(d, n)
    return B.p(name, (w, L + 2 * over, t if t is not None else w), (a + b) / 2, R, col, **kw)


def turn(rng, tilt=(4.0, 12.0), heading=None):
    """A Folk Valley turn: any heading, tilted and rolled a few degrees each way."""
    h = float(rng.uniform(0, 360)) if heading is None else heading
    s = rng.choice((-1.0, 1.0), 2)
    return ori(float(s[0] * rng.uniform(*tilt)), h, float(s[1] * rng.uniform(*tilt)))


def round3(B, name, c, w, h, d, cols, R=None, lid=None, solid=False, **kw):
    """Folk Valley's round: a core, two crossing slabs (one long in X, one long in Z, a hair apart in
    height) and a block turned 45 degrees about Y; a lid (w, h, d) on top if asked."""
    R = np.eye(3) if R is None else R
    c = np.asarray(c, float)
    cols = tuple(cols) + (cols[-1],) * (4 - len(cols))
    out = [B.p(name, (w * 0.82, h, d * 0.82), c, R, cols[0], solid=solid, **kw),
           B.p(name, (w, h * 0.8, d * 0.68), c + R @ (0, -h * 0.04, 0), R, cols[1], solid=solid, **kw),
           B.p(name, (w * 0.68, h * 0.76, d), c + R @ (0, -h * 0.05, 0), R, cols[1], solid=solid, **kw),
           B.p(name, (w * 0.66, h * 0.7, d * 0.66), c + R @ (0, h * 0.02, 0), R @ G.ry(45), cols[2], solid=solid,
               **kw)]
    if lid:
        lw, lh, ld = lid
        out.append(B.p(name, (lw, lh, ld), c + R @ (0, h / 2 + lh / 2 - 0.02, 0), R, cols[3], solid=solid, **kw))
    return out


def octagon(B, name, c, w, h, cols, R=None, solid=False, **kw):
    """A low octagonal drum in three blocks: a square, the same square turned 45 degrees, both a hair
    apart in height, and a narrower cross-block between them to round the corners off."""
    R = np.eye(3) if R is None else R
    c = np.asarray(c, float)
    cols = tuple(cols) + (cols[-1],) * (3 - len(cols))
    k = w * 0.83
    return [B.p(name, (k, h, k), c, R, cols[0], solid=solid, **kw),
            B.p(name, (k, h * 0.97, k), c, R @ G.ry(45), cols[1], solid=solid, **kw),
            B.p(name, (w, h * 0.94, w * 0.42), c, R @ G.ry(22.5), cols[2], solid=solid, **kw)]


def rock(B, c, s, cols, name="Rock", solid=False, flat=0.72, heading=None):
    """Folk Valley's rock: three blocks, turned and tilted, the biggest the darkest."""
    rng = B.rng
    c = np.asarray(c, float)
    h0 = float(rng.uniform(0, 90)) if heading is None else heading
    out = [B.p(name, (s, s * flat, s * 0.86), c + (0, s * flat * 0.42, 0), turn(rng, (3, 9), h0), cols[0],
               solid=solid)]
    for k, (f, dx, dz) in enumerate(((0.68, 0.42, -0.3), (0.46, -0.48, -0.22))):
        q = s * f
        off = np.array((dx * s, q * flat * 0.4, dz * s))
        out.append(B.p(name, (q, q * flat * (1.05 + 0.08 * k), q * 0.9), c + G.ry(h0) @ off,
                       turn(rng, (4, 12), h0 + 25 * (k + 1)), cols[1 + k % (len(cols) - 1)], solid=solid))
    return out


def grass(B, c, n, cols, h=(1.2, 2.0), r=0.55, name="Grass", w=0.35):
    """Blades 0.35 square, leaning up to 15 degrees, their tops a little apart."""
    rng = B.rng
    c = np.asarray(c, float)
    out = []
    for k in range(n):
        a = 2 * math.pi * k / n + float(rng.uniform(-0.4, 0.4))
        hh = float(rng.uniform(*h))
        pos = c + (r * math.cos(a) * 0.6, hh / 2 - 0.05, r * math.sin(a) * 0.6)
        R = G.ry(float(rng.uniform(0, 90))) @ G.rx(float(rng.uniform(-15, 15))) @ G.rz(float(rng.uniform(-15, 15)))
        out.append(B.p(name, (w, hh, w * (1.0 + 0.04 * k)), pos, R, cols[k % len(cols)]))
    return out


def flame(B, c, s, name="Flame", cols=FLAME, flicker=0.2, lamp=True):
    """A Neon flame: an orange block turned and tipped, a yellow one inside it and higher."""
    c = np.asarray(c, float)
    return [B.p(name, (s, s * 1.3, s), c, ori(12, 45, 8), cols[0], material="Neon", flicker=flicker, lamp=lamp),
            B.p(name, (s * 0.58, s * 1.1, s * 0.58), c + (0, s * 0.42, 0), ori(-8, 20, -6), cols[2], material="Neon",
                flicker=flicker, lamp=lamp)]


def palm(B, base, h, lean, trunk_cols, leaf_cols, fronds=7, frond_len=6.5, coconuts=3, segs=6, w0=1.5, w1=0.95,
         heading=0.0, name="Palm", nut_col="7a4a26", droop=28.0):
    """A palm: a segmented trunk bending over (lean = how far its top moves along `heading`), each
    segment turned 45 degrees from the last; long drooping fronds round the top and a few coconuts."""
    rng = B.rng
    base = np.asarray(base, float)
    hd = np.array((math.sin(math.radians(heading)), 0.0, -math.cos(math.radians(heading))))
    pts = [base + (0, h * i / segs, 0) + hd * lean * (i / segs) ** 2 for i in range(segs + 1)]
    out = []
    for i in range(segs):
        a, b = pts[i], pts[i + 1]
        w = w0 + (w1 - w0) * i / (segs - 1)
        d = b - a
        R = frame(d, None) @ G.ry(45.0 * (i % 2) + 8 * i)
        out.append(B.p(name, (w, float(np.linalg.norm(d)) + 0.35, w), (a + b) / 2, R, trunk_cols[i % len(trunk_cols)]))
    top = pts[-1] + (0, 0.2, 0)
    for k in range(fronds):
        a = heading + 360.0 * k / fronds + float(rng.uniform(-12, 12))
        dr = np.array((math.sin(math.radians(a)), 0.0, -math.cos(math.radians(a))))
        dip = math.radians(droop + float(rng.uniform(-8, 10)))
        tip = top + dr * frond_len * math.cos(dip) + (0, -frond_len * math.sin(dip), 0)
        out.append(bar(B, name, top + dr * 0.3, tip, 1.25 + 0.04 * (k % 3), leaf_cols[k % len(leaf_cols)],
                       t=0.22 + 0.02 * (k % 2), n=(0, 1, 0)))
    for k in range(coconuts):
        a = math.radians(heading + 120 * k + 30)
        out.append(B.p(name, (0.75, 0.75, 0.75), top + (0.55 * math.sin(a), -0.75, -0.55 * math.cos(a)),
                       ori(10, 30 * k, 12), nut_col))
    return out


def tree(B, base, cols_trunk, cols_leaf, h=10.5, canopy=(6.4, 5.0, 5.0, 4.6), w=(2.4, 2.1, 1.8), branches=2,
         name="Tree", fruit=None, fruit_col="e8403a", solid_trunk=False):
    """Folk Valley's tree: a trunk of three blocks turning a little each, two branch sticks leaning out
    40-55 degrees, a canopy of big tilted blocks (and fruit if asked)."""
    rng = B.rng
    base = np.asarray(base, float)
    seg = h / 3
    out = []
    for i, ww in enumerate(w):
        out.append(B.p(name, (ww, seg + 0.05, ww), base + (0.0, seg * (i + 0.5), 0.0),
                       ori(float(rng.uniform(4, 8)) * (-1) ** i, 121 - 180 * (i % 2) + float(rng.uniform(-6, 6)), 0),
                       cols_trunk[i % len(cols_trunk)], solid=solid_trunk))
    top = base + (0, h, 0)
    for k in range(branches):
        a = math.radians(40 + 180 * k + float(rng.uniform(-20, 20)))
        lean = math.radians(float(rng.uniform(40, 55)))
        d = np.array((math.cos(a) * math.sin(lean), math.cos(lean), math.sin(a) * math.sin(lean)))
        s = top - (0, seg * 0.6, 0)
        out.append(bar(B, name, s, s + d * 4.2, 1.1, cols_trunk[0]))
    for k, s in enumerate(canopy):
        if k == 0:
            c = top + (0, s * 0.42, 0)
        else:
            a = math.radians(360 * (k - 1) / (len(canopy) - 1) + float(rng.uniform(-20, 20)))
            c = top + (math.cos(a) * s * 0.52, float(rng.uniform(-0.4, 0.9)), math.sin(a) * s * 0.52)
        out.append(B.p(name, (s, s * 0.85, s), c, turn(rng, (3, 8)), cols_leaf[k % len(cols_leaf)]))
        if fruit and k > 0:
            for j in range(fruit):
                fa = float(rng.uniform(0, 2 * math.pi))
                out.append(B.p(name, (0.9, 0.9, 0.9), c + (math.cos(fa) * s * 0.5, -s * 0.2, math.sin(fa) * s * 0.5),
                               ori(0, float(rng.uniform(0, 90)), 0), fruit_col))
    return out


def bush(B, c, s, cols, name="Bush", heading=None):
    """Folk Valley's bush: two crossing blocks and a turned one on top, a little tilted."""
    rng = B.rng
    c = np.asarray(c, float)
    h = float(rng.uniform(0, 90)) if heading is None else heading
    return [B.p(name, (s, s * 0.72, s * 0.74), c + (0, s * 0.34, 0), ori(3, h, -4), cols[0]),
            B.p(name, (s * 0.76, s * 0.7, s * 1.02), c + (0, s * 0.33, 0), ori(-4, h + 8, 3), cols[1 % len(cols)]),
            B.p(name, (s * 0.66, s * 0.56, s * 0.66), c + (0, s * 0.7, 0), ori(6, h + 45, 5), cols[2 % len(cols)])]


def vine(B, top, length, cols, n=(0.0, 0.0, -1.0), w=0.35, sway=6.0, leaves=1, name="Vine", leaf_cols=None):
    """A vine hanging from top: a thin bar falling `length`, swinging a few degrees, and a leaf or
    two on it."""
    rng = B.rng
    top = np.asarray(top, float)
    a = math.radians(float(rng.uniform(-sway, sway)))
    n = np.asarray(n, float)
    side = np.cross((0, 1, 0), n)
    bot = top + (0, -length, 0) + side * math.sin(a) * length * 0.5
    out = [bar(B, name, top, bot, w, cols[0], t=w * 0.6, n=n)]
    lc = leaf_cols or cols
    for k in range(leaves):
        t = 0.45 + 0.4 * k / max(1, leaves)
        p = top + (bot - top) * t + n * 0.12
        out.append(B.p(name, (0.75, 0.42, 0.12), p, frame((0, 1, 0), n) @ G.rz(35 * (-1) ** k), lc[(k + 1) % len(lc)]))
    return out


def fern(B, c, n, cols, length=2.6, rise=38.0, w=0.62, name="Fern", heading=0.0):
    """Fronds radiating from a point, rising `rise` degrees: a fern, a bush of leaves."""
    rng = B.rng
    c = np.asarray(c, float)
    out = []
    for k in range(n):
        a = math.radians(heading + 360.0 * k / n + float(rng.uniform(-10, 10)))
        r = math.radians(rise + float(rng.uniform(-10, 10)))
        d = np.array((math.sin(a) * math.cos(r), math.sin(r), -math.cos(a) * math.cos(r)))
        L = length * float(rng.uniform(0.85, 1.1))
        out.append(bar(B, name, c + d * 0.1, c + d * L, w, cols[k % len(cols)], t=0.16 + 0.01 * (k % 3), n=(0, 1, 0)))
    return out


def potato(B, c, s, cols, R=None, name="Potato", eyes="1e1a22", eye_mat="SmoothPlastic", mouth=True, solid=False,
           glow=None, cheeks=None, glints=False):
    """A potato in bricks, s tall: a round body (core, two crossing slabs, a turned block) with a face
    on its front (-Z of R): two tall eyes, a smile."""
    R = np.eye(3) if R is None else R
    c = np.asarray(c, float)
    w, h, d = s * 0.86, s, s * 0.78
    out = round3(B, name, c, w, h, d, cols, R=R, solid=solid)
    zf = -d / 2 - 0.02
    ew, eh = s * 0.14, s * 0.22
    for sx in (-1, 1):
        out.append(B.p(name, (ew, eh, 0.12), c + R @ (sx * s * 0.17, s * 0.12, zf), R, eyes, material=eye_mat,
                       shadow=False, flicker=glow, lamp=glow is not None))
        if glints:
            g = ew * 0.42
            out.append(B.p(name, (g, g, 0.1), c + R @ (sx * s * 0.17 + ew / 2 - g / 2 - ew * 0.12,
                                                       s * 0.12 + eh / 2 - g / 2 - eh * 0.08, zf - 0.04), R, "ffffff",
                           material="SmoothPlastic", shadow=False))
    if mouth:
        out.append(B.p(name, (s * 0.26, s * 0.08, 0.12), c + R @ (0, -s * 0.14, zf - 0.005), R, INK,
                       material="SmoothPlastic", shadow=False))
    if cheeks:
        for sx in (-1, 1):
            out.append(B.p(name, (s * 0.13, s * 0.07, 0.1), c + R @ (sx * s * 0.3, -s * 0.06, zf + 0.012), R, cheeks,
                           material="SmoothPlastic", shadow=False))
    return out


def stairs(B, x0, x1, z_front, z_back, y0, y1, n, cols, name="Step", solid=True):
    """A flight of n steps from (y0, z_front) up to (y1, z_back), x0..x1 wide: each step a slab one
    rise high reaching back to z_back, so the flight is solid; two shades by turns."""
    rise = (y1 - y0) / n
    run = (z_back - z_front) / n
    out = []
    for k in range(n):
        zf = z_front + run * k
        out.append(B.p(name, (x1 - x0 - 0.02 * (k % 2), rise, z_back - zf), ((x0 + x1) / 2, y0 + rise * (k + 0.5),
                       (zf + z_back) / 2), None, cols[k % len(cols)], solid=solid))
    return out


# ==================================================================== a whole area

class Area:
    """An area's scenery: hero(sc, parent) builds Heroes.<Id>; props is a list of (fn, attrs) where
    fn(sc, parent) builds one prop and attrs are its scatter attributes."""

    def __init__(self, aid, title, hero, props, ground="5dbb46"):
        self.aid, self.title, self.hero, self.props, self.ground = aid, title, hero, props, ground


AREAS = {}


def register(area):
    AREAS[area.aid] = area
    return area


def prop_attrs(count=6, smin=0.9, smax=1.3, band="Side", solid=False):
    return dict(Count=int(count), ScaleMin=float(smin), ScaleMax=float(smax), Band=band, Solid=bool(solid))


def build_area(sc, aid):
    area = AREAS[aid]
    heroes = sc.container(sc.root, "Heroes")
    props = sc.container(sc.container(sc.root, "Props"), aid)
    hero = area.hero(sc, heroes)
    ps = []
    for fn, attrs in area.props:
        m = fn(sc, props)
        m.p.setdefault("attrs", {}).update(attrs)
        ps.append(m)
    return hero, ps


# ==================================================================== checks

def _flags(m, p, errs, allow_solid):
    solid = p.p["collide"]
    if not p.p["anchored"] or p.p["touch"]:
        errs.append("%s: %s not anchored / touches" % (m.name, p.name))
    if solid and not allow_solid:
        errs.append("%s: %s collides" % (m.name, p.name))
    if solid and not p.p["query"]:
        errs.append("%s: solid %s not queryable" % (m.name, p.name))
    if not solid and p.p["query"]:
        errs.append("%s: decoration %s queryable" % (m.name, p.name))
    if p.p["shadow"] and max(p.p["size"]) < 2.5:
        errs.append("%s: small %s casts a shadow" % (m.name, p.name))
    at = p.p.get("attrs", {})
    if "Flicker" in at and p.p["material"] != "Neon":
        errs.append("%s: %s flickers but is %s" % (m.name, p.name, p.p["material"]))
    if "NightLamp" in at and p.p["material"] != "Neon":
        errs.append("%s: %s is a night lamp but %s" % (m.name, p.name, p.p["material"]))


def check_model(m, hero):
    errs = []
    parts = [n for n in m.walk() if n.kind == "Part"]
    if hero and len(parts) > HERO_PARTS:
        errs.append("%s: %d parts" % (m.name, len(parts)))
    if not hero and not PROP_MIN <= len(parts) <= PROP_MAX:
        errs.append("%s: %d parts" % (m.name, len(parts)))
    if m.p.get("primary") is None:
        errs.append("%s: no PrimaryPart" % m.name)
    lo, hi = bounds(parts)
    pv = pivot_of(m).p
    mid = (lo + hi) / 2
    if abs(pv[1]) > 1e-6 or abs(pv[0] - mid[0]) > 1e-3 or abs(pv[2] - mid[2]) > 1e-3:
        errs.append("%s: pivot %s is not the middle of its footprint" % (m.name, np.round(pv, 2)))
    if lo[1] < -1.5:
        errs.append("%s: %.2f below the ground" % (m.name, -lo[1]))
    if hero and (hi[0] - lo[0] > HERO_W + 1e-6 or hi[2] - lo[2] > HERO_D + 1e-6):
        errs.append("%s: footprint %.1f x %.1f" % (m.name, hi[0] - lo[0], hi[2] - lo[2]))
    for p in parts:
        _flags(m, p, errs, allow_solid=hero)
    if not hero:
        at = m.p.get("attrs", {})
        if at.get("Band") not in BANDS or not at.get("Count") or not at.get("ScaleMin") or "Solid" not in at:
            errs.append("%s: attributes %s" % (m.name, at))
    errs += ["%s: %s" % (m.name, e) for e in brickcheck.rules(parts)]
    for a, b, ar in brickcheck.zfight(parts, ground=0.0):
        errs.append("%s: z-fight %s %s %s / %s %s %s (%.3f)" % (
            m.name, a.name, [round(v, 2) for v in a.p["size"]], np.round(a.p["cf"].p, 2), b.name,
            [round(v, 2) for v in b.p["size"]], np.round(b.p["cf"].p, 2), ar))
    return errs


def check(hero, props):
    errs = check_model(hero, True)
    for m in props:
        errs += check_model(m, False)
    return errs


def summary(m):
    parts = [n for n in m.walk() if n.kind == "Part"]
    lo, hi = bounds(parts)
    sz = hi - lo
    solid = sum(1 for p in parts if p.p["collide"])
    neon = sum(1 for p in parts if p.p["material"] == "Neon")
    at = m.p.get("attrs", {})
    return "%-16s %3d parts  %5.1f x %5.1f x %5.1f  solid %3d  neon %2d  %s" % (
        m.name, len(parts), sz[0], sz[1], sz[2], solid, neon, " ".join("%s=%s" % kv for kv in sorted(at.items())))
