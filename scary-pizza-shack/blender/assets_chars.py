"""Batch 2, section B: Inspector, Watcher, Passenger, InspectorHole.

Each builder takes the CFrame where the thing stands (feet / origin on the ground,
facing -Z) and returns the Model."""
import math

import numpy as np

import assets_r6 as R6
import spsgeo as G
from assets_common import P, detail, handle, moving, mirror_x, pivot, slab
from spsgeo import CF, T, RX, RY, RZ, S

# ---------------------------------------------------------------- the Inspector

# 1.7 x the R6 height (HumanoidRootPart centre 5.1 above the soles, hat top 9.8), but thin:
# torso and legs only 1.2 x as wide, arms 1.25 x as long and thin. Head = classic head x 1.4.
INSPECTOR = R6.Body(torso=(2.4, 3.4, 1.2), arm=(0.85, 4.25, 1.0), leg=(1.2, 3.4, 1.2), head=(2.8, 1.4, 1.4), k=0.85)
HAT_TOP = 9.8


def _hand(curl_sign):
    """Palm under the arm block and four long fingers (spread front to back), curling
    towards the body (curl_sign = -1: towards -X). Arm-local, the arm bottom at y=0."""
    g = G.Geo()
    g.add(G.box(0.78, 0.46, 0.86, (0, -0.23, 0)))
    for k, z in enumerate((-0.3, -0.1, 0.1, 0.3)):
        L1, L2 = 0.62 - 0.06 * abs(k - 1.5), 0.5 - 0.05 * abs(k - 1.5)
        seg1 = G.box(0.18, L1, 0.15, (0, -L1 / 2, 0))
        seg2 = G.box(0.16, L2, 0.13, (0, -L2 / 2, 0))
        x0 = curl_sign * 0.1
        g.add(seg1, T(x0, -0.42, z) @ RZ(-curl_sign * 6))
        tip = T(x0 + curl_sign * 0.05, -0.42 - L1 + 0.04, z) @ RZ(-curl_sign * 24)
        g.add(seg2, tip)
    thumb = G.box(0.18, 0.5, 0.18, (0, -0.25, 0))
    g.add(thumb, T(curl_sign * 0.18, -0.36, -0.46) @ RX(28) @ RZ(-curl_sign * 18))
    return g


def _shoe():
    side = [(0.62, 0.0), (0.62, 0.5), (-0.36, 0.5), (-0.78, 0.36), (-0.95, 0.18), (-0.95, 0.0)]
    g = G.extrude(side, 1.3, "x")            # outline (z, y) seen from the side
    return g


def inspector(sc, parent, origin=CF(), name="Inspector"):
    B = INSPECTOR
    cols = {"Torso": P["suit"], "Head": P["skin_grey"], "Left Arm": P["suit"], "Right Arm": P["suit"],
            "Left Leg": P["suit"], "Right Leg": P["suit"]}
    m, parts = R6.build(sc, parent, name, B, origin, cols)
    own = "Inspector"
    TW, TH, TD = B.torso
    fz = -TD / 2
    # -- suit front: shirt V, tie, lapels, buttons, pocket square
    tcf = parts["Torso"].p["cf"]
    shirt = slab([(-0.52, TH / 2), (0.52, TH / 2), (0.08, 0.28), (0, 0.18), (-0.08, 0.28)], 0.04, c=(0, 0, fz - 0.02))
    detail(sc, m, parts["Torso"], "Shirt", shirt, tcf, "shirt", own)
    tie = G.Geo().add([slab([(-0.15, 1.64), (0.15, 1.64), (0.11, 1.42), (-0.11, 1.42)], 0.07, c=(0, 0, fz - 0.06)),
                       slab([(-0.1, 1.42), (0.1, 1.42), (0.14, 0.62), (0, 0.44), (-0.14, 0.62)], 0.05,
                            c=(0, 0, fz - 0.06))])
    detail(sc, m, parts["Torso"], "Tie", tie, tcf, "tie_red", own)
    lap = slab([(-0.52, TH / 2), (-0.07, 0.24), (-0.3, 0.24), (-0.6, 0.92), (-0.82, 1.1), (-0.73, 1.28),
                (-0.86, TH / 2)], 0.05, c=(0, 0, fz - 0.03))
    detail(sc, m, parts["Torso"], "Lapels", G.Geo().add([lap, mirror_x(lap)]), tcf, "suit_light", own)
    btn = G.Geo().add([G.cyl(0.085, 0.06, 8, "z", (0, y, fz - 0.03)) for y in (-0.15, -0.75)])
    detail(sc, m, parts["Torso"], "Buttons", btn, tcf, "ink", own)
    sq = slab([(-0.98, 0.9), (-0.62, 0.9), (-0.74, 1.08), (-0.86, 1.03)], 0.04, c=(0, 0, fz - 0.02))
    detail(sc, m, parts["Torso"], "PocketSquare", sq, tcf, "shirt", own)
    # -- cuffs, long-fingered hands
    AW, AL, AD = B.arm
    for side, sgn in (("Left", 1), ("Right", -1)):
        arm = parts[side + " Arm"]
        acf = arm.p["cf"]
        cuff = G.box(AW + 0.08, 0.24, AD + 0.08, (0, -AL / 2 + 0.1, 0))
        detail(sc, m, arm, side + "Cuff", cuff, acf, "shirt", own, mesh_name=own + "__Cuff")
        hand = _hand(sgn).xf(T(0, -AL / 2, 0))
        detail(sc, m, arm, side + "Hand", hand, acf, "skin_grey", own)
    # -- shoes
    LW, LH, LD = B.leg
    for side in ("Left", "Right"):
        leg = parts[side + " Leg"]
        detail(sc, m, leg, side + "Shoe", _shoe().xf(T(0, -LH / 2 - 0.01, 0)), leg.p["cf"], "shoe_black", own,
               mesh_name=own + "__Shoe")
    # -- the hat (wide flat brim, tall crown, dark red band); its top is at 9.8
    hcf = parts["Head"].p["cf"]
    top = HAT_TOP - hcf.p[1] + origin.p[1]
    yb = top - 1.66
    brim = G.lathe_loop([(1.02, yb + 0.04), (2.05, yb - 0.1), (2.05, yb - 0.2), (1.02, yb - 0.05)], 20)
    detail(sc, m, parts["Head"], "HatBrim", brim, hcf, "hat_black", own)
    crown = G.lathe([(0.0, yb - 0.02), (1.1, yb - 0.02), (1.08, top - 0.32), (1.0, top - 0.06), (0.55, top),
                     (0.0, top - 0.1)], 16)
    detail(sc, m, parts["Head"], "HatCrown", G.outward(crown), hcf, "hat_black", own)
    band = G.lathe_loop([(1.095, yb + 0.02), (1.15, yb + 0.02), (1.14, yb + 0.36), (1.09, yb + 0.36)], 16)
    detail(sc, m, parts["Head"], "HatBand", band, hcf, "tie_red", own)
    # -- clipboard + paper in the left hand, pen in the right
    la, ra = parts["Left Arm"], parts["Right Arm"]
    bx, by, bz = -0.12, -AL / 2 - 0.95, -0.42        # board centre, arm-local
    board = G.box(1.2, 1.5, 0.08, (bx, by - 0.5, bz))
    cb = detail(sc, m, la, "Clipboard", board, la.p["cf"], "clip_wood", own, collide=False)
    clip = G.Geo().add([G.box(0.5, 0.18, 0.12, (bx, by + 0.2, bz - 0.06)), G.cyl(0.07, 0.4, 6, "x", (bx, by + 0.3, bz - 0.1))])
    detail(sc, m, la, "Clip", clip, la.p["cf"], "steel", own, material="Metal")
    paper = G.box(1.0, 1.24, 0.02, (bx, by - 0.58, bz - 0.05))
    detail(sc, m, la, "Paper", paper, la.p["cf"], "paper", own)
    d = np.array((0.0, -0.32, -1.0))
    d /= np.linalg.norm(d)
    pen = G.Geo().add([G.cyl(0.065, 0.8, 8, "y", (0, 0.0, 0)), G.frustum(0.065, 0.0, 0.14, 8, "y", (0, -0.47, 0))])
    up = np.array((0.0, 1.0, 0.0))
    Ry = -d
    Rx = np.cross(Ry, (0, 0, 1.0))
    Rx /= np.linalg.norm(Rx)
    Rz = np.cross(Rx, Ry)
    Rpen = np.column_stack((Rx, Ry, Rz))
    pen_c = np.array((0.12, -AL / 2 - 0.85, -0.5))
    detail(sc, m, ra, "Pen", pen, ra.p["cf"] * CF(pen_c, Rpen), "ink", own)
    return m


# ---------------------------------------------------------------- the Watcher

WATCHER = R6.Body.scaled(1.18, arm_len=1.3)


def watcher(sc, parent, origin=CF(), name="Watcher"):
    B = WATCHER
    cols = {k: P["void"] for k in R6.PARTS}
    m, parts = R6.build(sc, parent, name, B, origin, cols)
    head = parts["Head"]
    w, h, d = B.head_dims()
    for sx in (-1, 1):
        e = sc.part(m, "Eye", (0.2, 0.2, 0.2), head.p["cf"] * CF((sx * 0.25, 0.1, -d / 2 + 0.05)), P["eye_pale"],
                    shape="Ball", material="Neon", anchored=False, collide=False, touch=False, query=False,
                    shadow=False, massless=True, surfaces="smooth", grid=False)
        sc.weld(head, e, "Weld")
    return m


# ---------------------------------------------------------------- the Passenger

def passenger(sc, parent, torso_cf=CF(), name="Passenger"):
    """Clings to a customer's back (Handle = the torso centre of a standard 2x2x1 R6 torso)."""
    m = sc.model(parent, name)
    h = handle(sc, m, torso_cf)
    own = "Passenger"
    body = G.Geo()
    body.add(G.blob(0.5, 8, 5, scale=(0.95, 1.25, 0.62), jitter=0.06, seed=7, c=(0.12, 0.38, 0.86)))
    for sx in (-1, 1):
        body.add(G.tube([(sx * 0.3, -0.06, 0.84), (sx * 0.62, -0.3, 0.78), (sx * 0.86, -0.47, 0.62),
                         (sx * 0.92, -0.54, 0.52)], 0.1, 5))          # legs gripping the waist
    detail(sc, m, h, "Body", body, torso_cf, "shadow", own)
    arms = G.Geo()
    for sx, sh in ((-1, (-0.3, 0.92, 0.66)), (1, (0.48, 0.98, 0.64))):
        path = [sh, (sx * 0.82, 1.1, 0.32), (sx * 0.84, 1.1, -0.12), (sx * 0.8, 0.86, -0.6), (sx * 0.66, 0.38, -0.62)]
        arms.add(G.tube(path, 0.075, 5))
        hx, hy = sx * 0.66, 0.38
        for k, (dx, dy) in enumerate(((-0.06, -0.38), (sx * -0.2, -0.32), (sx * -0.3, -0.18))):
            arms.add(G.tube([(hx, hy, -0.62), (hx + dx * 0.6, hy + dy * 0.6, -0.635), (hx + dx, hy + dy, -0.62)],
                            0.035, 4))
    detail(sc, m, h, "Arms", arms, torso_cf, "shadow", own)
    hc = np.array((0.95, 1.32, 0.16))
    headg = G.blob(0.31, 8, 5, scale=(1.0, 0.95, 1.0), jitter=0.05, seed=3)
    neck = G.tube([(0.4, 0.86, 0.72), (0.66, 1.08, 0.46), (0.86, 1.2, 0.26)], 0.11, 5)
    detail(sc, m, h, "Neck", neck, torso_cf, "shadow", own)
    hd = sc.mesh(m, "Head", own + "__Head", headg, torso_cf * CF(hc), P["shadow"], anchored=False, collide=False,
                 touch=False, query=False, massless=True, owner=own)
    sc.motor(h, hd, "Neck", torso_cf * CF((0.78, 1.12, 0.32)), parent=h)
    pivot(hd, torso_cf * CF((0.78, 1.12, 0.32)))
    for dx in (-0.11, 0.11):
        e = sc.part(m, "Eye", (0.1, 0.1, 0.1), torso_cf * CF(hc + (dx, 0.04, -0.29)), P["eye_pale"], shape="Ball",
                    material="Neon", anchored=False, collide=False, touch=False, query=False, shadow=False,
                    massless=True, surfaces="smooth", grid=False)
        sc.weld(hd, e, "Weld")
    moving(name, "Head", "on the Motor6D Neck (in the Handle; Part1 = Head): turn it with Neck.Transform, e.g. "
                         "CFrame.Angles(0, math.rad(-40), 0) to look round at the camera. The Eyes are welded to it")
    return m


# ---------------------------------------------------------------- the hole

def _chunk(pts_xz, thick, lift_inner, inner_dir, rng):
    """Irregular tile chunk (outline in XZ), tilted so its inner edge is lifted."""
    pts = [(p[0], p[1]) for p in pts_xz]
    c = np.mean(np.array(pts), 0)
    pts = [tuple(c + (np.array(p) - c) * 0.93) for p in pts]        # cracks between chunks
    g = G.slab_poly(pts, thick, (0, 0, 0))
    # tilt about the axis through the chunk's outer edge (tangential)
    ang = math.degrees(math.atan2(lift_inner, 0.9)) * (0.7 + 0.6 * rng.random())
    t = np.array((-inner_dir[1], 0.0, inner_dir[0]))           # tangent (axis)
    outer = np.array((c[0], 0.0, c[1])) - 0.45 * np.array((inner_dir[0], 0.0, inner_dir[1]))
    R = G.rot_axis(t, -ang)
    m4 = G.M(R)
    g = g.xf(T(*outer) @ m4 @ T(*(-outer)))
    return g


def _checker(x, z):
    return (math.floor(x / 2.0) + math.floor(z / 2.0)) % 2 == 0


def inspector_hole(sc, parent, origin=CF(), name="InspectorHole"):
    """8 across at scale 1: Model:ScaleTo(width / 8) for anything from 3 to 8 studs."""
    rng = np.random.default_rng(11)
    m = sc.model(parent, name)
    own = "InspectorHole"
    r_in, r_out = 2.7, 4.0
    dark = sc.cylinder(m, "Dark", 0.1, 2 * r_in + 0.5, origin * np.array((0, 0.05, 0)), origin.R @ (0, 1, 0),
                       (0, 0, 0), material="Neon", anchored=True, collide=False, touch=False, query=False,
                       shadow=False, grid=False)
    pivot(dark, origin)
    m.p["primary"] = dark
    white, black = G.Geo(), G.Geo()
    n = 18
    for i in range(n):
        a0 = math.tau * (i + 0.15 * (rng.random() - 0.5)) / n
        a1 = math.tau * (i + 1 + 0.15 * (rng.random() - 0.5)) / n
        for j in range(2):
            if j == 1 and rng.random() < 0.2:
                continue                                  # ragged outer edge
            ra = r_in - 0.15 + (r_out - r_in) * j / 2 + 0.1 * rng.random()
            rb = r_in + (r_out - r_in) * (j + 1) / 2 + (0.35 * rng.random() if j else 0.1 * rng.random())
            pts = [(ra * math.cos(a0), ra * math.sin(a0)), (rb * math.cos(a0 + 0.02), rb * math.sin(a0 + 0.02)),
                   (rb * math.cos(a1 - 0.02), rb * math.sin(a1 - 0.02)), (ra * math.cos(a1), ra * math.sin(a1))]
            am = (a0 + a1) / 2
            inner_dir = (-math.cos(am), -math.sin(am))
            lift = (0.55 if j == 0 else 0.18) * (0.6 + 0.8 * rng.random())
            g = _chunk(pts, 0.2, lift, inner_dir, rng)
            cx, cz = np.mean(np.array(pts), 0)
            (white if _checker(cx, cz) else black).add(g)
    for pname, g, colr in (("TilesLight", white, P["tile_light"]), ("TilesDark", black, P["tile_dark"])):
        sc.mesh(m, pname, own + "__" + pname, g, origin, colr, anchored=True, collide=False, touch=False,
                query=False, owner=own)
    for k in range(8):
        a = math.tau * (k + 0.4 * rng.random()) / 8
        rr = 3.0 + 0.8 * rng.random()
        sz = 0.45 + 0.3 * rng.random()
        pts = [(sz * math.cos(t) * (0.8 + 0.4 * rng.random()), sz * math.sin(t) * (0.8 + 0.4 * rng.random()))
               for t in np.linspace(0, math.tau, 5, endpoint=False) + rng.random()]
        g = G.slab_poly(pts, 0.18, (0, -0.09, 0))
        R = G.rot_axis((rng.random() - 0.5, 0.0, rng.random() - 0.5), 25 + 30 * rng.random())
        cf_ = origin * CF((rr * math.cos(a), 0.42 + 0.1 * rng.random(), rr * math.sin(a)), R)
        sc.mesh(m, "Shard%d" % (k + 1), own + "__Shard%d" % (k + 1), g, cf_,
                P["tile_light"] if k % 2 == 0 else P["tile_dark"], anchored=True, collide=False, touch=False,
                query=False, owner=own)
    return m
