"""Batch 2 (V3): PapaStud, the founder and mascot of Papa Stud's Pizza, who lives in the forest.

A full R6 rig at 1.7 x (the Inspector's joints and names; no Humanoid): HumanoidRootPart
anchored, soles 5.1 under its centre, arms 1.25 x long. A tall heavy chef in whites that have
seen years of sauce, always smiling because the smile is a mask: the billboard's pizza slice
(crust on top, point down, round white eyes, small pupils, red cheeks, a wide black grin,
pepperoni) as a thick moulded slab 4.2 wide, strapped on over a plain dark hood, chipped at
its top right corner and cracked through the right cheek. A tall puffed chef's hat, a
double-breasted jacket, a red neckerchief, a long stained apron (sauce and flour), dark
checked trousers, black shoes, white cartoon gloves (three fat fingers and a thumb) and a
wooden pizza peel held upright like a staff in the right hand.

Built facing -Z, feet on the ground at the origin. Every detail is a MeshPart welded to its
body part, massless, not colliding."""
import math

import numpy as np

import assets_r6 as R6
import spsgeo as G
from assets_common import detail, mirror_x, slab
from spsgeo import CF, T, RX, RY, RZ, S

# 1.7 x R6, arms 1.25 x long: HRP centre 5.1 above the soles, hands hang to 1.5
PAPA = R6.Body(torso=(3.4, 3.4, 1.7), arm=(1.7, 4.25, 1.7), leg=(1.7, 3.4, 1.7), head=(3.4, 1.7, 1.7), k=0.85)

PC = {
    "whites": (240, 238, 230), "apron": (220, 212, 192), "sauce": (214, 96, 44), "sauce_old": (204, 140, 92),
    "flour": (250, 249, 244), "hood": (26, 24, 28), "trousers": (44, 44, 52), "check": (86, 86, 96),
    "shoe": (20, 20, 22), "glove": (248, 248, 244), "button": (206, 200, 186), "kerchief": (186, 32, 30),
    "cheese": (246, 196, 72), "crust": (206, 140, 66), "eye": (255, 255, 250), "pupil": (20, 18, 20),
    "cheek": (224, 92, 88), "grin": (22, 18, 18), "pepperoni": (168, 40, 30), "strap": (40, 34, 30),
    "peel": (186, 136, 82), "peel_dark": (132, 90, 52), "hat": (250, 250, 246),
}

# the mask in head space (head centre, front -Z): crust on top, cheese slab, the point down
MASK_TOP, MASK_POINT = 1.0, -2.0           # the cheese's top edge (under the crust) and its point
MASK_Z = (-1.22, -1.58)                    # its back and front faces
CRUST_Y, CRUST_R = 1.2, 0.4


def _mask_half(y):
    """Half width of the cheese at height y (4.0 at the top, 0.35 at the point)."""
    return (0.35 + 3.65 * (y - MASK_POINT) / (MASK_TOP - MASK_POINT)) / 2


def _disc(r, z0, z1, x, y, n=12):
    return G.cyl(r, z1 - z0, n, "z", (x, y, (z0 + z1) / 2))


def mask_parts():
    """[(part name, colour, geo)] in head space."""
    zb, zf = MASK_Z
    zc, th = (zb + zf) / 2, zb - zf
    # the cheese, its top right corner chipped off
    hp = _mask_half(MASK_POINT)
    right = [(hp, MASK_POINT + 0.08), (_mask_half(0.5), 0.5), (1.62, 0.66), (1.74, 0.8), (1.5, MASK_TOP)]
    left = [(-_mask_half(MASK_TOP), MASK_TOP), (-hp, MASK_POINT + 0.08)]
    tip = [(0.0, MASK_POINT - 0.06)]
    cheese = slab(tip + right + left, th, c=(0, 0, zc))
    out = [("Mask", "cheese", cheese)]
    # the crust: a fat rounded roll across the top, its right end broken off short
    x0, x1 = -2.1, 1.62
    crust = G.cyl(CRUST_R, x1 - x0, 12, "x", ((x0 + x1) / 2, CRUST_Y, zc - 0.06))
    crust.add(G.sphere(CRUST_R, 10, 5, (1, 1, 1), (x0, CRUST_Y, zc - 0.06)))
    crust.add(G.box(0.3, 0.62, 0.62, (x1 + 0.05, CRUST_Y - 0.02, zc - 0.06)).xf(
        T(x1, CRUST_Y, zc) @ RZ(-14) @ T(-x1, -CRUST_Y, -zc)))
    out.append(("MaskCrust", "crust", crust))
    # eyes, pupils (looking a little down and in), cheeks, the grin, pepperoni
    eyes, pupils = G.Geo(), G.Geo()
    for sx in (-1, 1):
        eyes.add(_disc(0.45, zf - 0.08, zf + 0.02, sx * 0.75, 0.35, 16))
        pupils.add(_disc(0.14, zf - 0.13, zf - 0.06, sx * 0.68, 0.24, 10))
    out.append(("MaskEyes", "eye", eyes))
    out.append(("MaskPupils", "pupil", pupils))
    cheeks = G.Geo()
    for sx in (-1, 1):
        cheeks.add(_disc(0.22, zf - 0.06, zf + 0.02, sx * 0.86, -0.45, 12))
    out.append(("MaskCheeks", "cheek", cheeks))
    up = [(x, -0.5 - 0.42 * (1 - (x / 0.62) ** 2)) for x in np.linspace(-0.62, 0.62, 9)]
    lo = [(x, -0.5 - 0.62 * (1 - (x / 0.62) ** 2) - 0.02) for x in np.linspace(0.56, -0.56, 8)]
    grin = G.extrude(up + lo, 0.08, "z", (0, 0, zf - 0.03))
    # the crack: from the grin's right corner through the right cheek to the edge
    crack = [(0.6, -0.56), (0.74, -0.47), (0.84, -0.54), (0.97, -0.38), (1.06, -0.44), (1.17, -0.3)]
    for (ax, ay), (bx, by) in zip(crack, crack[1:]):
        ln = math.hypot(bx - ax, by - ay)
        a = math.degrees(math.atan2(by - ay, bx - ax))
        grin.add(G.box(ln + 0.04, 0.05, 0.1, (0, 0, 0)).xf(T((ax + bx) / 2, (ay + by) / 2, zf - 0.05) @ RZ(a)))
    out.append(("MaskGrin", "grin", grin))
    pep = G.Geo()
    for (x, y, r) in ((-1.42, 0.72, 0.22), (0.0, -1.42, 0.2), (-0.86, 0.95, 0.12)):
        pep.add(_disc(r, zf - 0.07, zf + 0.02, x, y, 12))
    out.append(("MaskPepperoni", "pepperoni", pep))
    # the strap round the hood (from the mask's edges, just under the eyes' line)
    strap = G.lathe_loop([(1.24, 0.18), (1.31, 0.18), (1.31, 0.48), (1.24, 0.48)], 16)
    out.append(("MaskStrap", "strap", strap))
    return out


def hood_geo():
    """A plain dark hood over the head, falling onto the shoulders (head space)."""
    prof = [(1.62, -1.02), (1.42, -0.86), (1.24, -0.4), (1.2, 0.3), (1.12, 0.8), (0.86, 1.1), (0.4, 1.24),
            (0.0, 1.26)]
    return G.outward(G.lathe(prof, 16, sz=0.95))


def hat_parts(base):
    """HatBand and HatPuff, standing on the hood's crown at height `base` (head space)."""
    band = G.outward(G.lathe([(0.0, base), (1.0, base), (1.05, base + 0.55), (0.0, base + 0.55)], 16))
    puff = G.lathe([(0.0, base + 0.45), (1.0, base + 0.45), (1.22, base + 0.75), (1.4, base + 1.15),
                    (1.36, base + 1.45), (1.15, base + 1.65), (0.65, base + 1.75), (0.0, base + 1.76)], 16,
                   rmod=lambda a: 1.0 + 0.06 * math.sin(7 * a))
    return [("HatBand", "hat", band), ("HatPuff", "hat", G.outward(puff))]


def _splats(rng, n, box, z, size, seed_pts=None):
    """Flat smears inside box (x0, x1, y0, y1) at depth z (a number or z(x, y)), facing -Z: a
    wiped streak of tomato sauce or a dusting of flour (rounded, no drips: it is food)."""
    g = G.Geo()
    pts = seed_pts or [(rng.uniform(box[0], box[1]), rng.uniform(box[2], box[3])) for _ in range(n)]
    for (cx, cy) in pts:
        r = rng.uniform(*size)
        ang = rng.uniform(-25, 25)
        k = 10
        poly = []
        for i in range(k):
            a = math.tau * i / k
            rr = 1.0 + rng.uniform(-0.12, 0.12)
            poly.append((1.6 * r * rr * math.cos(a), 0.55 * r * rr * math.sin(a)))
        zz = z(cx, cy) if callable(z) else z
        g.add(G.extrude(poly, 0.03, "z", (0, 0, 0)).xf(T(cx, cy, zz) @ RZ(ang)))
        if rng.random() < 0.6:                        # a second, shorter wipe beside it
            g.add(G.extrude(poly, 0.03, "z", (0, 0, 0)).xf(T(cx + 0.2 * r, cy - 0.7 * r, zz) @ RZ(ang + 6) @
                                                           S(0.6, 0.7, 1.0)))
    return g


def glove(right):
    """A white cartoon glove under the arm (arm space, the arm's bottom at y -AL/2): a rolled
    cuff, a puffy palm, three fat fingers and a thumb. The right one is a fist round the peel."""
    AW, AL, AD = PAPA.arm
    yb = -AL / 2
    g = G.Geo()
    g.add(G.lathe_loop([(0.9, yb + 0.25), (1.06, yb + 0.25), (1.08, yb - 0.1), (0.92, yb - 0.1)], 14))
    g.add(G.box(1.62, 0.9, 1.62, (0, yb - 0.52, 0)))
    if not right:
        for i, z in enumerate((-0.52, 0.0, 0.52)):
            L1 = 0.9 - 0.08 * abs(i - 1)
            fing = G.frustum(0.27, 0.25, L1, 8, "y", (0, -L1 / 2, 0))
            fing.add(G.sphere(0.25, 8, 4, (1, 1, 1), (0, -L1, 0)))
            g.add(fing.xf(T(-0.18, yb - 0.92, z) @ RZ(-12)))
        th = G.frustum(0.24, 0.22, 0.7, 8, "y", (0, -0.35, 0))
        th.add(G.sphere(0.22, 8, 4, (1, 1, 1), (0, -0.7, 0)))
        g.add(th.xf(T(0.0, yb - 0.5, -0.82) @ RX(55)))
    else:
        # a fist round the upright handle (which passes through at z -1.05): the fingers wrap
        # its front, the thumb lies over them
        for i in range(3):
            y = yb - 0.32 - 0.36 * i
            g.add(G.cyl(0.24, 1.3, 10, "x", (0.05, y, -1.25)))
            g.add(G.sphere(0.26, 8, 4, (1, 1, 1), (-0.62, y, -1.2)))
        g.add(G.box(1.3, 1.0, 0.7, (0.05, yb - 0.66, -0.75)))
        th = G.frustum(0.24, 0.22, 0.8, 8, "x", (0.0, 0, 0))
        g.add(th.xf(T(0.05, yb - 0.2, -1.32) @ RZ(-8)))
    return g


def peel_parts(handle_x, handle_z, y0, y_neck, y_top):
    """The pizza peel upright in arm space: a round handle and a wide flat blade on top."""
    h = G.cyl(0.19, y_neck - y0 + 0.2, 10, "y", (handle_x, (y0 + y_neck + 0.2) / 2, handle_z))
    h.add(G.cyl(0.24, 0.2, 10, "y", (handle_x, y0 + 0.1, handle_z)))        # a cap on its foot
    w = 1.8
    blade = [(-0.22, y_neck - 0.05), (0.22, y_neck - 0.05), (0.5, y_neck + 0.3), (w / 2, y_neck + 0.75)]
    for k in range(7):                                                      # the rounded top
        a = math.radians(k * 180 / 6)
        blade.append((w / 2 * math.cos(a), y_top - 0.5 + 0.5 * math.sin(a) * 1.0))
    blade += [(-w / 2, y_neck + 0.75), (-0.5, y_neck + 0.3)]
    b = G.extrude(blade, 0.14, "z", (0, 0, handle_z)).xf(T(handle_x, 0, 0))
    burn = G.Geo()
    for (dx, dy, r) in ((-0.3, 0.9, 0.22), (0.25, 1.5, 0.16), (0.05, 2.0, 0.26)):
        burn.add(G.cyl(r, 0.16, 10, "z", (handle_x + dx, y_neck + dy, handle_z)))
    return [("PeelHandle", "peel", h), ("PeelBlade", "peel", b), ("PeelScorch", "peel_dark", burn)]


def papa_stud(sc, parent, origin=CF(), name="PapaStud"):
    B = PAPA
    own = "PapaStud"
    cols = {"Torso": PC["whites"], "Head": PC["hood"], "Left Arm": PC["whites"], "Right Arm": PC["whites"],
            "Left Leg": PC["trousers"], "Right Leg": PC["trousers"]}
    m, parts = R6.build(sc, parent, name, B, origin, cols, humanoid=False)
    rng = np.random.default_rng(1962)
    TW, TH, TD = B.torso
    AW, AL, AD = B.arm
    LW, LH, LD = B.leg
    fz = -TD / 2
    torso, head = parts["Torso"], parts["Head"]
    tcf, hcf = torso.p["cf"], head.p["cf"]

    def add(part, pname, geo, color, **kw):
        return detail(sc, m, part, pname, geo, part.p["cf"], PC.get(color, color), own, **kw)

    # -- the jacket: a heavy front, two rows of buttons on it, the double-breasted seam, the collar
    BR, BY, BZ = 1.6, 0.1, 0.25                             # the belly: a flattened ball on the front

    def front(x, y):                                        # the jacket's surface (torso space z)
        q = 1 - (x / BR) ** 2 - ((y - BY) / (0.85 * BR)) ** 2
        return fz - BZ * BR * math.sqrt(q) if q > 0 else fz
    add(torso, "Belly", G.sphere(BR, 14, 7, (1.0, 0.85, BZ), (0, BY, fz)), "whites")
    btn = G.Geo()
    for x in (-0.6, 0.6):
        for y in (1.05, 0.45):
            btn.add(G.sphere(0.13, 8, 4, (1, 1, 0.6), (x, y, front(x, y) - 0.03)))
    add(torso, "Buttons", btn, "button")
    seam = G.Geo()
    ys = np.linspace(TH / 2 - 0.1, -0.35, 9)
    for ya, yb in zip(ys, ys[1:]):
        za, zb = front(0.98, ya) - 0.02, front(0.98, yb) - 0.02
        ln = math.hypot(yb - ya, zb - za)
        a = math.degrees(math.atan2(zb - za, yb - ya))
        seam.add(G.box(0.07, ln + 0.02, 0.05, (0, 0, 0)).xf(T(0.98, (ya + yb) / 2, (za + zb) / 2) @ RX(a)))
    add(torso, "JacketSeam", seam, "button")
    collar = G.lathe_loop([(0.9, TH / 2 - 0.05), (1.02, TH / 2 - 0.05), (1.0, TH / 2 + 0.32), (0.9, TH / 2 + 0.32)],
                          16, sz=0.7)
    add(torso, "Collar", collar, "whites")
    # the red neckerchief: a band round the collar, a knot and a point over the belly's top
    nk = G.Geo()
    # tied at the side, so the knot and its two ends show beside the mask's point
    nk.add(G.sphere(0.3, 8, 4, (1.1, 0.9, 0.9), (1.05, TH / 2 - 0.02, -1.0)))
    for dx, a in ((-0.12, 8), (0.18, -14)):
        nk.add(slab([(-0.16, 0.0), (0.16, 0.0), (0.2, -0.75), (0.0, -0.9), (-0.2, -0.75)], 0.07, c=(0, 0, 0)).xf(
            T(1.05 + dx, TH / 2 - 0.15, front(1.05 + dx, TH / 2 - 0.6) - 0.06) @ RZ(a)))
    nk.add(G.lathe_loop([(0.98, TH / 2 + 0.02), (1.08, TH / 2 + 0.02), (1.08, TH / 2 + 0.24), (0.98, TH / 2 + 0.24)],
                        16, sz=0.72))
    add(torso, "Neckerchief", nk, "kerchief")
    # old sauce on the jacket front
    js = _splats(rng, 0, None, lambda x, y: front(x, y) - 0.03, (0.1, 0.18), [(1.15, 0.5), (-0.4, 1.3), (0.9, -0.2)])
    add(torso, "JacketStains", js, "sauce_old")
    # -- the long apron: a waist piece on the torso, a panel on each leg (they part as he walks)
    az = fz - 0.51                                          # in front of the belly
    ap = slab([(-1.78, -0.42), (1.78, -0.42), (1.8, -TH / 2), (-1.8, -TH / 2)], 0.08, c=(0, 0, az))
    ap.add(G.lathe_loop([(1.0, -0.5), (1.08, -0.5), (1.08, -0.3), (1.0, -0.3)], 16, sx=1.74, sz=0.9))
    for sx in (-1, 1):                                      # the ties hanging at the back
        ap.add(G.box(0.18, 0.8, 0.06, (sx * 0.3, -0.85, TD / 2 + 0.05)).xf(
            T(sx * 0.3, -0.45, TD / 2) @ RZ(sx * 12) @ T(-sx * 0.3, 0.45, -TD / 2)))
    add(torso, "Apron", ap, "apron")
    sauce = _splats(rng, 0, None, az - 0.055, (0.16, 0.3), [(-0.9, -0.95), (0.7, -1.3)])
    flour = _splats(rng, 0, None, az - 0.055, (0.22, 0.34), [(0.3, -0.75), (-1.35, -1.4)])
    for side, sx in (("Left", -1), ("Right", 1)):
        leg = parts[side + " Leg"]
        x_in, x_out = -sx * LW / 2, sx * (LW / 2 + 0.1)                   # leg space: inner edge, outer edge
        lo, hi = sorted((x_in, x_out))
        lz = az                                                             # same plane as the waist piece
        pnl = slab([(lo, LH / 2), (hi, LH / 2), (hi + 0.06 * (sx > 0), -0.95), (lo - 0.06 * (sx < 0), -0.95)], 0.08,
                   c=(0, 0, lz))
        add(leg, side + "Apron", pnl, "apron")
        pts_s = [((lo + hi) / 2 + 0.2 * sx, 0.6 - 0.9 * (sx > 0)), ((lo + hi) / 2 - 0.25 * sx, -0.35)]
        pts_f = [((lo + hi) / 2 - 0.1, 0.1 + 0.8 * (sx < 0))]
        sauce_l = _splats(rng, 0, None, lz - 0.055, (0.14, 0.26), pts_s)
        flour_l = _splats(rng, 0, None, lz - 0.055, (0.2, 0.32), pts_f)
        add(leg, side + "ApronSauce", sauce_l, "sauce")
        add(leg, side + "ApronFlour", flour_l, "flour")
        # dark checked trousers: lighter lines on the four faces below the apron's hem
        chk = G.Geo()
        for y in np.arange(-LH / 2 + 0.45, LH / 2 - 0.1, 0.55):
            chk.add(G.box(LW + 0.04, 0.07, LD + 0.04, (0, y, 0)))
        for x in (-0.42, 0.0, 0.42):
            chk.add(G.box(0.07, LH - 0.4, LD + 0.1, (x, 0.1, 0)))
        for z in (-0.42, 0.0, 0.42):
            chk.add(G.box(LW + 0.1, LH - 0.4, 0.07, (0, 0.1, z)))
        add(leg, side + "Checks", chk, "check", mesh_name=own + "__Checks")
        # black shoes, big and round-toed
        side_o = [(0.95, 0.0), (0.95, 0.62), (-0.5, 0.62), (-1.05, 0.48), (-1.32, 0.25), (-1.32, 0.0)]
        shoe = G.extrude(side_o, LW + 0.14, "x").xf(T(0, -LH / 2 - 0.01, 0))
        add(leg, side + "Shoe", shoe, "shoe", mesh_name=own + "__Shoe")
    add(torso, "ApronSauce", sauce, "sauce")
    add(torso, "ApronFlour", flour, "flour")
    # -- sleeves: a turned-back cuff, a stain; white cartoon gloves
    for side, right in (("Left", False), ("Right", True)):
        arm = parts[side + " Arm"]
        cuff = G.box(AW + 0.14, 0.5, AD + 0.14, (0, -AL / 2 + 0.55, 0))
        add(arm, side + "Cuff", cuff, "whites", mesh_name=own + "__Cuff")
        add(arm, side + "Glove", glove(right), "glove")
    st = _splats(rng, 0, None, -AD / 2 - 0.03, (0.12, 0.2), [(0.2, -0.9)])
    add(parts["Right Arm"], "SleeveStain", st, "sauce_old")
    # -- the peel in the right fist, upright like a staff, its blade over his shoulder
    ra = parts["Right Arm"]
    ay = ra.p["cf"].p[1] - origin.p[1]                   # the arm's centre above the soles
    for pname, colr, g in peel_parts(0.05, -1.05, 0.15 - ay, 7.9 - ay, 10.35 - ay):
        add(ra, pname, g, colr)
    # -- the head: a dark hood, the mask strapped on, the hat on top
    add(head, "Hood", hood_geo(), "hood")
    for pname, colr, g in mask_parts():
        kw = {"material": "Neon"} if pname == "MaskEyes" else {}
        add(head, pname, g, colr, **kw)
    for pname, colr, g in hat_parts(1.08):
        add(head, pname, g, colr)
    return m


def eye_height():
    """Height of the mask's eyes above the HumanoidRootPart's centre (and above the soles)."""
    HW, HH, HD = PAPA.head
    LW, LH, LD = PAPA.leg
    TW, TH, TD = PAPA.torso
    head_y = LH + TH + HH / 2
    return head_y + 0.35 - (LH + TH / 2), head_y + 0.35
