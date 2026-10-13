"""Batch 2, section E: uniforms, as real Roblox Accessories for R6 avatars.

Each Accessory has an invisible Handle at the centre of the R6 part it is worn on and,
inside the Handle, the attachment of that part with the same local CFrame as on an R6
body (HatAttachment (0, 0.6, 0) on the Head, BodyFrontAttachment (0, 0, -0.5) on the
Torso, ...). Humanoid:AddAccessory therefore puts the Handle exactly on the part. The
colour parts are welded to the Handle (massless, no collisions)."""
import math

import numpy as np

import assets_kit as K
import assets_r6 as R6
import spsgeo as G
from assets_common import col, handle
from spsgeo import CF, T, RX, RY, RZ, S

UC = {"uni_red": (196, 40, 32), "uni_white": (244, 242, 236), "uni_cream": (240, 228, 196),
      "uni_black": (30, 30, 34), "uni_yellow": (232, 214, 40), "uni_silver": (196, 200, 204),
      "uni_cheese": (250, 206, 92), "uni_crust": (214, 158, 84), "uni_flour": (250, 248, 240),
      "uni_sauce": (170, 30, 24), "uni_grey": (110, 112, 120), "uni_glass": (170, 210, 230),
      "uni_navy": (40, 52, 90)}

ATT = {  # attachment name -> (R6 part, local CFrame on that part)
    "HatAttachment": ("Head", CF((0, 0.6, 0))),
    "HairAttachment": ("Head", CF((0, 0.6, 0))),
    "BodyFrontAttachment": ("Torso", CF((0, 0, -0.5))),
    "LeftGripAttachment": ("Left Arm", CF((0, -1, 0), R6.R_GRIP)),
    "RightGripAttachment": ("Right Arm", CF((0, -1, 0), R6.R_GRIP)),
}

UNIFORMS = {}       # name -> (attachment, builder, notes)


def uniform(name, att, notes=""):
    def deco(fn):
        UNIFORMS[name] = (att, fn, notes)
        return fn
    return deco


def c(k):
    return UC.get(k, k) if isinstance(k, str) else k


# -- hats -----------------------------------------------------------------------------------

@uniform("PizzaCap", "HatAttachment", "peaked cap with a pizza slice on the front")
def _pizza_cap():
    crown = K.cap(K.edge(0.2, 0.12, 0.06), lambda th, f: 0.06 + 0.02 * f, n=12, lift=0.06)
    crown.add(G.cyl(0.07, 0.06, 6, "y", (0, K.HH + 0.14, 0)))
    tri = [(-0.17, 0.48), (0.17, 0.48), (0.0, 0.16)]
    slice_ = K.wrap_face(G.extrude(tri, 0.04, "z", (0, 0, 0)), -0.095)
    crust = K.wrap_face(G.extrude([(-0.19, 0.5), (0.19, 0.5), (0.17, 0.44), (-0.17, 0.44)], 0.06, "z", (0, 0, 0)),
                        -0.1)
    pep = G.Geo()
    for x, y in ((-0.05, 0.38), (0.06, 0.33), (0.0, 0.25)):
        pep.add(G.cyl(0.035, 0.03, 6, "z", (x, y, 0.0)))
    pep = K.wrap_face(pep, -0.12)
    return [("Crown", "uni_red", crown), ("Peak", "uni_red", K._peak()), ("Slice", "uni_cheese", slice_),
            ("Crust", "uni_crust", crust), ("Pepperoni", "uni_red", pep)]


@uniform("ChefHat", "HatAttachment", "tall white chef's hat")
def _chef_hat():
    band = G.lathe_loop([(0.66, 0.2), (0.72, 0.2), (0.72, 0.62), (0.66, 0.62)], 14)
    puff = G.lathe([(0.0, 0.6), (0.7, 0.6), (0.78, 0.9), (0.86, 1.3), (0.8, 1.6), (0.55, 1.78), (0.0, 1.82)], 14,
                   rmod=lambda a: 1.0 + 0.05 * math.sin(6 * a))
    return [("Band", "uni_white", band), ("Puff", "uni_white", G.outward(puff))]


@uniform("PaperHat", "HatAttachment", "folded paper diner hat, worn front to back like a garrison cap")
def _paper_hat():
    # sections front to back: a tent whose bottom edges sink into the head's rim, the fold along the top
    def tent(z, top, half, lo=0.44):
        return [(-half, lo, z), (half, lo, z), (0.06, top, z), (-0.06, top, z)]
    secs = [(-0.76, 0.84, 0.46), (-0.62, 1.0, 0.6), (0.0, 0.93, 0.6), (0.62, 1.0, 0.6), (0.76, 0.84, 0.46)]
    hat = G.outward(G.loft([tent(*sc_) for sc_ in secs]))
    stripe = G.Geo()
    for sx in (-1, 1):                          # a red band along each side, just above the head
        rows = []
        for z, top, half in secs[1:-1]:
            a, b = np.array((sx * half, 0.44)), np.array((sx * 0.06, top))
            d = (b - a) / np.linalg.norm(b - a)
            nrm = np.array((sx * d[1], -sx * d[0])) * sx * sx
            if np.dot(nrm, (sx, 0)) < 0:
                nrm = -nrm
            pts = []
            for y, off in ((0.64, 0.004), (0.73, 0.004), (0.73, 0.02), (0.64, 0.02)):
                t = (y - 0.44) / (top - 0.44)
                q = a + (b - a) * t + nrm * off
                pts.append((q[0], q[1], z))
            rows.append(pts)
        stripe.add(G.outward(G.loft(rows)))
    return [("Hat", "uni_white", hat), ("Stripe", "uni_red", stripe)]


@uniform("Visor", "HatAttachment", "sun visor (band and peak, open top)")
def _visor():
    band = K.band(K.const(0.16), K.const(0.4), K.const(0.0), K.const(0.07), n=14)
    return [("Band", "uni_red", band), ("Peak", "uni_red", K._peak(y=0.18, reach=0.66))]


@uniform("Bandana", "HatAttachment", "bandana tied on the head, knot at the back")
def _bandana():
    cloth = K.cap(K.edge(0.32, 0.08, -0.12), lambda th, f: 0.04 + 0.02 * f, n=12)
    knot = G.Geo().add([G.sphere(0.11, 6, 4, c=(0, 0.02, 0.7)),
                        K.ftube([(0.03, 0.0, 0.72), (0.12, -0.25, 0.8), (0.16, -0.5, 0.82)], 0.14, 0.03),
                        K.ftube([(-0.03, 0.0, 0.72), (-0.1, -0.22, 0.82), (-0.08, -0.42, 0.86)], 0.14, 0.03)])
    dots = G.Geo()
    for k in range(10):
        th = math.tau * k / 10 + 0.3
        for f in (0.35, 0.75):
            u = K._u_of(0.1) * (1 - f)
            p = K._surf(u, th, 0.065)
            dots.add(G.box(0.07, 0.07, 0.07, p))
    return [("Cloth", "uni_red", cloth), ("Knot", "uni_red", knot), ("Dots", "uni_white", dots)]


@uniform("DeliveryHelmet", "HatAttachment", "open-face scooter helmet with a centre stripe")
def _helmet():
    shell = K.cap(K.edge(0.36, -0.36, -0.42), lambda th, f: 0.16 + 0.06 * f, n=14, rows=4)
    path = []
    for th, ub, rng_ in ((0.0, K._u_of(0.36), np.linspace(1.0, 0.0, 6)), (math.pi, K._u_of(-0.42), np.linspace(0.0, 1.0, 6))):
        for f in rng_:
            if th > 0 and f == 0.0:
                continue
            u = ub * f
            path.append(K._surf(max(u, 0.02), th, 0.16 + 0.06 * (1 - f) + 0.02))
    stripe = K.ftube(path, 0.24, 0.03)
    vis = K.band(K.const(0.2), K.const(0.5), K.const(0.25), K.const(0.29), th0=math.radians(-62), th1=math.radians(62),
                 n=8, closed=False)
    strap = G.Geo()
    for sx in (-1, 1):
        strap.add(K.ftube([(sx * 0.72, -0.25, 0.0), (sx * 0.6, -0.62, -0.1), (sx * 0.3, -0.74, -0.32),
                           (0.0, -0.76, -0.4)], 0.08, 0.03))
    return [("Shell", "uni_red", shell), ("Stripe", "uni_white", stripe),
            ("Visor", "uni_glass", vis), ("Strap", "uni_black", strap)]


# -- aprons (Torso, BodyFrontAttachment) --------------------------------------------------------

def _apron_shape():
    bib = [(-0.5, 0.75), (0.5, 0.75), (0.55, 0.0), (0.92, -0.25), (0.88, -1.0), (-0.88, -1.0), (-0.92, -0.25),
           (-0.55, 0.0)]
    body = G.extrude(bib, 0.05, "z", (0, 0, -0.53))
    skirt = G.extrude([(-0.88, -1.0), (0.88, -1.0), (0.92, -2.3), (-0.92, -2.3)], 0.05, "z", (0, 0, -0.6))
    skirt = skirt.xf(T(0, -1.0, -0.53) @ RX(3) @ T(0, 1.0, 0.53))
    straps = G.Geo()
    for sx in (-1, 1):
        straps.add(K.ftube([(sx * 0.42, 0.75, -0.53), (sx * 0.45, 1.04, -0.3), (sx * 0.45, 1.04, 0.3),
                            (sx * 0.4, 0.8, 0.53)], 0.1, 0.03))
        straps.add(K.ftube([(sx * 0.92, -0.3, -0.53), (sx * 1.03, -0.3, 0.0), (sx * 0.8, -0.3, 0.53),
                            (sx * 0.2, -0.3, 0.55)], 0.1, 0.03))
    return G.Geo().add([body, skirt]), straps


@uniform("Apron", "BodyFrontAttachment", "plain bib apron with a front pocket")
def _apron():
    a, s = _apron_shape()
    pocket = G.extrude([(-0.4, -0.5), (0.4, -0.5), (0.4, -0.95), (-0.4, -0.95)], 0.04, "z", (0, 0, -0.575))
    return [("Apron", "uni_white", a), ("Pocket", "uni_white", pocket), ("Straps", "uni_white", s)]


@uniform("ApronStriped", "BodyFrontAttachment", "striped bib apron")
def _apron_striped():
    a, s = _apron_shape()
    st = G.Geo()
    for k in range(5):
        x = -0.6 + 0.3 * k
        top = 0.7 if abs(x) < 0.5 else -0.1
        st.add(G.box(0.1, top + 1.0, 0.03, (x, (top - 1.0) / 2, -0.565)))
        st.add(G.box(0.1, 1.28, 0.03, (x, -1.66, -0.62)).xf(T(0, -1.0, -0.53) @ RX(3) @ T(0, 1.0, 0.53)))
    return [("Apron", "uni_white", a), ("Stripes", "uni_red", st), ("Straps", "uni_white", s)]


@uniform("ApronStained", "BodyFrontAttachment", "bib apron with flour and sauce marks")
def _apron_stained():
    a, s = _apron_shape()
    rng = np.random.default_rng(23)
    flour, sauce = G.Geo(), G.Geo()
    for k in range(9):
        x, y = rng.uniform(-0.7, 0.7), rng.uniform(-1.9, 0.4)
        r = rng.uniform(0.08, 0.2)
        pts = [(x + r * math.cos(t) * (0.8 + 0.4 * rng.random()), y + r * math.sin(t) * (0.8 + 0.4 * rng.random()))
               for t in np.linspace(0, math.tau, 7, endpoint=False)]
        z = (-0.565 if y > -1.0 else -0.62 - 0.05 * (-1.0 - y) / 1.3) - 0.004 * k
        blot = G.extrude(pts, 0.03, "z", (0, 0, z))
        (flour if k % 3 else sauce).add(blot)
    return [("Apron", "uni_cream", a), ("Flour", "uni_flour", flour), ("Sauce", "uni_sauce", sauce),
            ("Straps", "uni_cream", s)]


@uniform("HiVisVest", "BodyFrontAttachment", "hi-vis vest (same shape as the customer one)")
def _hivis():
    return [(n, colr, g) for n, colr, mat, tr, g in K.KIT["HiVisVest"][2]()]


# -- small things -----------------------------------------------------------------------------

@uniform("NameTag", "BodyFrontAttachment", "name tag on the chest; Tag's Front face is flat for a SurfaceGui")
def _name_tag():
    tag = G.box(0.62, 0.3, 0.03, (-0.5, 0.5, -0.535))
    border = G.box(0.68, 0.36, 0.02, (-0.5, 0.5, -0.515))
    border.add(G.box(0.1, 0.04, 0.03, (-0.5, 0.67, -0.53)))
    return [("Tag", "uni_white", tag), ("Border", "uni_red", border)]


def _mitt():
    mitt = K.rbox(1.2, 0.9, 1.2, 0.2, (0, -0.56, 0), n=2)
    mitt.add(K.rbox(1.24, 0.12, 1.24, 0.22, (0, -1.04, 0), n=2))
    thumb = K.rbox(0.3, 0.5, 0.36, 0.1, (0, 0, 0)).xf(T(0, -0.62, -0.68) @ RX(-20))
    mitt.add(thumb)
    cuff = K.rbox(1.26, 0.22, 1.26, 0.22, (0, -0.06, 0), n=2)
    return mitt, cuff


@uniform("OvenMittL", "LeftGripAttachment", "left oven mitt (the pair lives in the Model OvenMitts)")
def _mitt_l():
    m, cuff = _mitt()
    return [("Mitt", "uni_red", m), ("Cuff", "uni_white", cuff)]


@uniform("OvenMittR", "RightGripAttachment", "right oven mitt")
def _mitt_r():
    m, cuff = _mitt()
    return [("Mitt", "uni_red", m), ("Cuff", "uni_white", cuff)]


@uniform("Headset", "HairAttachment", "headset: band, one ear cup and a mic boom")
def _headset():
    path = []
    for k in range(11):
        a = math.pi * k / 10
        path.append((-0.7 * math.cos(a), 0.1 + 0.62 * math.sin(a) + 0.05 * math.sin(a) ** 4, 0.0))
    band = K.ftube(path, 0.1, 0.06)
    ear = G.Geo().add([G.cyl(0.22, 0.16, 10, "x", (0.74, 0.0, 0.0)), G.cyl(0.12, 0.1, 8, "x", (-0.71, 0.1, 0.0))])
    mic = K.ftube([(0.8, -0.05, -0.12), (0.76, -0.28, -0.42), (0.5, -0.34, -0.66), (0.2, -0.3, -0.7)], 0.05, 0.05)
    mic.add(G.sphere(0.06, 6, 4, c=(0.18, -0.3, -0.7)))
    return [("Band", "uni_black", band), ("Earpiece", "uni_black", ear), ("Mic", "uni_grey", mic)]


ORDER = ["PizzaCap", "ChefHat", "PaperHat", "Visor", "Bandana", "DeliveryHelmet", "Apron", "ApronStriped",
         "ApronStained", "HiVisVest", "NameTag", "OvenMittL", "OvenMittR", "Headset"]

SHARED = {"HiVisVest": "KitHiVisVest"}     # accessory -> mesh prefix it shares


def place(sc, parent, name, part_cf):
    """Accessory `name` with its Handle at part_cf (the CFrame of the R6 part it is worn on)."""
    att, fn, notes = UNIFORMS[name]
    acc = sc.accessory(parent, name)
    h = handle(sc, acc, part_cf)
    acc.p.pop("primary", None)
    part, lcf = ATT[att]
    sc.attachment(h, att, part_cf * lcf)
    prefix = SHARED.get(name) or ("UniOvenMitt" if name.startswith("OvenMitt") else "Uni" + name)
    for pname, colr, geo in fn():
        if att == "HatAttachment":
            geo = geo.xf(G.S(K.HAT_OVER_HAIR))          # 15% bigger than the head it was fitted to: over hair
        mp = sc.mesh(acc, pname, "%s__%s" % (prefix, pname), geo, part_cf, col(c(colr)),
                     material="Glass" if colr == "uni_glass" else "Plastic",
                     transparency=0.4 if colr == "uni_glass" else 0.0, anchored=False, collide=False, touch=False,
                     query=False, massless=True, owner=prefix)
        sc.weld(h, mp, "Weld")
    return acc


def uniforms(sc, parent, origin=CF(), spacing=4.0):
    """Model Uniforms: every accessory laid out in a row; the two oven mitts in a Model OvenMitts."""
    m = sc.model(parent, "Uniforms")
    k = 0
    mitts = None
    for name in ORDER:
        att = UNIFORMS[name][0]
        part = ATT[att][0]
        cf_ = origin * CF((k * spacing, 0, 0))
        if name.startswith("OvenMitt"):
            if mitts is None:
                mitts = sc.model(m, "OvenMitts")
            place(sc, mitts, name, cf_)
        else:
            place(sc, m, name, cf_)
        k += 1
    return m
