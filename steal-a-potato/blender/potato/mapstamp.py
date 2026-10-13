"""Stamps: a piece built once (a template) and placed many times (instances) in the map.

The map's scene holds every placed part, so the checks and the renders see the real thing. The
build script writes each template once and makes its copies in Studio: a copy is the template turned
and moved to the instance's pivot, scaled about that pivot, with some colours swapped (an area's
tint) and, for a solid prop, its big parts made solid.

A template's parts are kept relative to its pivot (for a prop the middle of its footprint on the
ground, for the Mound the top of its hollow), so an instance is placed by where its pivot goes.
"""
import json

import numpy as np

import spslib
from spsgeo import CF

from .bricks import hexc

BIG = 2.0           # a solid prop's parts this big or bigger collide
MIN_SIDE = 0.05     # no side under this, however small a copy is scaled
SMALL = 2.5         # parts smaller than this cast no shadow


class Template:
    def __init__(self, key, parts, primary, attrs=None, name=None):
        self.key = key
        self.name = name or key
        self.parts = parts          # [dict(name, size, rel (CF), color, shape, material, transparency, flags, surfaces, attrs)]
        self.primary = primary      # index of the PrimaryPart
        self.attrs = attrs or {}

    def bounds(self, scale=1.0):
        """(lo, hi) of the template's parts about its pivot, as built (scale applies)."""
        lo, hi = np.full(3, 1e9), np.full(3, -1e9)
        for p in self.parts:
            h = np.abs(p["rel"].R) @ (np.asarray(p["size"]) / 2)
            lo = np.minimum(lo, p["rel"].p - h)
            hi = np.maximum(hi, p["rel"].p + h)
        return lo * scale, hi * scale

    def radius(self, scale=1.0):
        lo, hi = self.bounds(scale)
        return float(max(abs(lo[0]), abs(hi[0]), abs(lo[2]), abs(hi[2])))

    def count(self):
        return len(self.parts)


def capture(model, key):
    """A Template from a Model built (anywhere) in some scene: its parts relative to its pivot."""
    prim = model.p.get("primary")
    assert prim is not None, "%s has no PrimaryPart" % model.name
    piv = prim.p["cf"] * (prim.p.get("pivot") or CF())
    inv = piv.inv()
    parts, primary = [], None
    for n in model.walk():
        if n.kind != "Part":
            continue
        assert n.kind == "Part", n
        if n is prim:
            primary = len(parts)
        parts.append(dict(name=n.name, size=tuple(n.p["size"]), rel=inv * n.p["cf"], color=tuple(n.p["color"]),
                          shape=n.p["shape"], material=n.p["material"], transparency=n.p["transparency"],
                          flags=dict(anchored=n.p["anchored"], collide=n.p["collide"], touch=n.p["touch"],
                                     query=n.p["query"], shadow=n.p["shadow"], massless=n.p["massless"]),
                          surfaces=n.p["surfaces"], attrs=dict(n.p.get("attrs") or {})))
    return Template(key, parts, primary, dict(model.p.get("attrs") or {}), name=model.name)


def build_template(key, builder):
    """Run builder(sc, parent) -> Model in a scratch scene and capture it."""
    sc = spslib.Scene("T")
    m = builder(sc, sc.root)
    return capture(m, key)


# ---------------------------------------------------------------- Folk Valley's own props

SURF = {"In": "inlet", "St": "inlet", "Sm": "smooth"}


def fv_orientation(rx, ry, rz):
    """CFrame.fromOrientation(rx, ry, rz) (radians): Y, then X, then Z."""
    cx, sx_ = np.cos(rx), np.sin(rx)
    cy, sy_ = np.cos(ry), np.sin(ry)
    cz, sz_ = np.cos(rz), np.sin(rz)
    Rx = np.array(((1, 0, 0), (0, cx, -sx_), (0, sx_, cx)))
    Ry = np.array(((cy, 0, sy_), (0, 1, 0), (-sy_, 0, cy)))
    Rz = np.array(((cz, -sz_, 0), (sz_, cz, 0), (0, 0, 1)))
    return Ry @ Rx @ Rz


class FV:
    """Folk Valley's props (the owner's data file): FV(path).template(group, index)."""

    def __init__(self, path):
        self.data = json.load(open(path))["groups"]
        self.cache = {}

    def kind(self, group, i):
        return self.data[group][i]["kind"]

    def template(self, group, i):
        key = "FV_%s_%d" % (group, i)
        if key in self.cache:
            return self.cache[key]
        rows = self.data[group][i]["parts"]
        parts = []
        for r in rows:
            name, cls, sx, sy, sz, x, y, z, rx, ry, rz, col, mat, surf, shape, tr, cc = r
            if tr >= 0.99:                      # hit boxes
                continue
            if mat not in ("Plastic", "SmoothPlastic", "Neon"):
                mat = "Plastic"
            size = (max(sx, 0.05), max(sy, 0.05), max(sz, 0.05))
            parts.append(dict(name=name, size=size, rel=CF((x, y, z), fv_orientation(rx, ry, rz)),
                              color=hexc(col), shape="Wedge" if shape == "Wedge" else "Block", material=mat,
                              transparency=float(tr),
                              flags=dict(anchored=True, collide=False, touch=False, query=False,
                                         shadow=max(size) >= SMALL, massless=False),
                              surfaces="inlet" if mat == "Plastic" else "smooth", attrs={}))
        # the PrimaryPart: the biggest part
        primary = int(np.argmax([np.prod(p["size"]) for p in parts]))
        t = Template(key, parts, primary, name=self.data[group][i]["kind"])
        self.cache[key] = t
        return t


# ---------------------------------------------------------------- recolouring

def hsv(c):
    r, g, b = [v / 255.0 for v in c]
    mx, mn = max(r, g, b), min(r, g, b)
    d = mx - mn
    if d == 0:
        h = 0.0
    elif mx == r:
        h = ((g - b) / d) % 6
    elif mx == g:
        h = (b - r) / d + 2
    else:
        h = (r - g) / d + 4
    return h * 60.0, (0.0 if mx == 0 else d / mx), mx


def role(c):
    """What a colour is in a Folk Valley prop: leaf (greens), wood (browns), stone (greys) or other."""
    h, s, v = hsv(c)
    if s < 0.16:
        return "stone"
    if 65 <= h <= 170 and s >= 0.25:
        return "leaf"
    if 10 <= h <= 45 and v < 0.62 and s >= 0.3:
        return "wood"
    return "other"


def lum(c):
    r, g, b = c
    return 0.299 * r + 0.587 * g + 0.114 * b


def recolour_map(template, scheme):
    """{old colour: new colour} for a template: scheme maps a role to a list of 1-3 colours (dark to
    light); each old colour of that role takes the new one nearest in lightness rank."""
    by_role = {}
    for p in template.parts:
        c = tuple(p["color"])
        by_role.setdefault(role(c), set()).add(c)
    out = {}
    for rl, cols in by_role.items():
        new = scheme.get(rl)
        if not new:
            continue
        new = [hexc(x) for x in new]
        cols = sorted(cols, key=lum)
        for i, c in enumerate(cols):
            j = 0 if len(cols) == 1 else round(i * (len(new) - 1) / (len(cols) - 1))
            out[c] = tuple(new[j])
    return out


# ---------------------------------------------------------------- instances

class Stamps:
    """The map's templates and where each copy goes."""

    def __init__(self, sc):
        self.sc = sc
        self.templates = {}
        self.instances = []         # dict(model, key, cf, scale, recolour, solid)

    def add_template(self, t):
        self.templates.setdefault(t.key, t)
        return self.templates[t.key]

    def place(self, parent, name, t, cf_, scale=1.0, recolour=None, solid=False):
        """A copy of template t with its pivot at cf_ (a CF), scaled about it."""
        t = self.add_template(t)
        sc = self.sc
        m = sc.model(parent, name)
        recolour = recolour or {}
        made = []
        for p in t.parts:
            rel = p["rel"]
            size = tuple(max(float(v) * scale, MIN_SIDE) for v in p["size"])
            fl = dict(p["flags"])
            if solid and max(p["size"]) >= BIG and p["transparency"] < 1.0:
                fl.update(collide=True, query=True)
            if fl["shadow"] and max(size) < SMALL:
                fl["shadow"] = False
            col = recolour.get(tuple(p["color"]), tuple(p["color"]))
            n = sc.part(m, p["name"], size, cf_ * CF(rel.p * scale, rel.R), col, shape=p["shape"],
                        material=p["material"], transparency=p["transparency"], surfaces=p["surfaces"], grid=False,
                        attrs=dict(p["attrs"]), **fl)
            made.append(n)
        prim = made[t.primary]
        m.p["primary"] = prim
        prim.p["pivot"] = prim.p["cf"].inv() * cf_
        self.instances.append(dict(model=m, key=t.key, cf=cf_, scale=float(scale), recolour=dict(recolour),
                                   solid=bool(solid)))
        return m

    def parts(self):
        return sum(t.count() for t in self.templates.values())
