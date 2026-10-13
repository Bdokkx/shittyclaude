"""ReplicatedStorage.PotatoKit: Mound, Soil, Seeds (8), Fences (4 tiers of Post, Rail, GateArch)
and UpgradeBoard. Laid out in a row far below the map so they never show by accident (the game
clones them and pivots them where it wants).

White parts are the ones the game tints: every seed's Body. Everything else comes coloured."""
import math

import numpy as np

import spsgeo as G
from spsgeo import CF, T, RX, RY, RZ, S

from . import mound as MD
from . import props as P
from .geo import bevel_box, ccyl, cfrustum, rod
from .kit import darker, facing, lighter

KIT_Y = -500.0
TINT = (236, 236, 232)          # light grey: tinted in game


def slot(i, row=0):
    return CF((i * 14.0, KIT_Y, row * 14.0))


def build(k, kf):
    MD.mound(k, kf, slot(0))
    soil(k, kf, slot(1))
    seeds = k.sc.folder(kf, "Seeds")
    for i, (name, fn) in enumerate(SEEDS):
        seed(k, seeds, name, fn, slot(i, 1))
    fences = k.sc.folder(kf, "Fences")
    for i, (name, style) in enumerate(FENCES):
        fence_tier(k, fences, name, style, i)
    upgrade_board(k, kf, slot(2))


# ---------------------------------------------------------------- Soil

def soil(k, parent, base):
    """A neat square raised bed 5 x 5, 0.8 high, with a wooden border; pivot at the top centre."""
    m = k.sc.model(parent, "Soil")
    dirt = k.mesh(m, "Dirt", "Soil_Dirt", bevel_box(4.2, 0.7, 4.2, 0.12, (0, 0.35, 0)), base, MD.SOIL)
    rows = G.Geo()
    for z in (-1.2, 0.0, 1.2):
        rows.add(bevel_box(3.6, 0.3, 0.6, 0.12, (0, 0.8, z)))
    k.mesh(m, "Rows", "Soil_Rows", rows, base, darker(MD.SOIL, 0.85))
    b = G.Geo()
    for (x, z, sx, sz) in ((0, -2.2, 5.0, 0.6), (0, 2.2, 5.0, 0.6), (-2.2, 0, 0.6, 3.8), (2.2, 0, 0.6, 3.8)):
        b.add(bevel_box(sx, 0.8, sz, 0.12, (x, 0.4, z)))
    for (x, z) in ((-2.2, -2.2), (2.2, -2.2), (-2.2, 2.2), (2.2, 2.2)):
        b.add(bevel_box(0.8, 1.0, 0.8, 0.15, (x, 0.5, z)))
    k.mesh(m, "Border", "Soil_Border", b, base, P.WOOD)
    dirt.p["pivot"] = dirt.p["cf"].inv() * (base * CF((0.0, 0.8, 0.0)))
    m.p["primary"] = dirt
    return m


# ---------------------------------------------------------------- Seeds

def seed_body(h=1.7, w=1.35):
    """An upright seed potato from layered bevelled blocks, its bottom at y = 0."""
    g = G.Geo()
    n = 6
    for kk in range(n):
        a0, a1 = -1 + 2 * kk / n, -1 + 2 * (kk + 1) / n
        am = (a0 + a1) / 2
        f = math.sqrt(max(0.12, 1 - am * am))
        ww = w * (0.55 + 0.45 * f) * (1.0 - 0.06 * am)
        y0, y1 = (a0 + 1) / 2 * h, (a1 + 1) / 2 * h
        g.add(bevel_box(ww, y1 - y0 + 0.02, ww * 0.9, 0.1, (0, (y0 + y1) / 2, 0)))
        g.add(bevel_box(ww * 0.8, (y1 - y0) * 0.8, ww * 1.02, 0.1, (0, (y0 + y1) / 2, 0)))
    return g


def leaf(l=0.7, w=0.45):
    return bevel_box(l, 0.2, w, 0.06, (l / 2, 0, 0))


def seed(k, parent, name, fn, base):
    m = k.sc.model(parent, name)
    body = k.mesh(m, "Body", "Seed_Body", seed_body(), base, TINT)
    body.p["pivot"] = body.p["cf"].inv() * base
    m.p["primary"] = body
    for pname, colr, g, *rest in fn():
        mat = rest[0] if rest else "Plastic"
        k.mesh(m, pname, "%s_%s%d" % (name, pname, len(m.children)), g, base, colr, material=mat)
    return m


def _eyes(col=(150, 110, 70)):
    e = G.Geo()
    for (x, y, z) in ((-0.42, 0.9, -0.5), (0.3, 1.25, -0.48), (0.5, 0.55, -0.4), (-0.3, 0.45, 0.55)):
        e.add(bevel_box(0.22, 0.22, 0.2, 0.05, (x, y, z)))
    return e


def s_meadow():
    sp = G.Geo()
    sp.add(bevel_box(0.25, 0.5, 0.25, 0.06, (0, 1.85, 0)))
    sp.add(leaf().xf(T(0.05, 2.05, 0) @ RZ(25)))
    sp.add(leaf().xf(T(-0.05, 2.0, 0) @ RY(180) @ RZ(35)))
    return [("Sprout", (90, 200, 70), sp), ("Detail", (150, 110, 70), _eyes())]


def s_dunes():
    sp = G.Geo()
    sp.add(bevel_box(0.35, 0.55, 0.35, 0.1, (0, 1.9, 0)))
    sp.add(bevel_box(0.4, 0.22, 0.22, 0.06, (0.27, 1.85, 0)))
    sp.add(bevel_box(0.22, 0.3, 0.22, 0.06, (0.4, 2.0, 0)))
    spines = G.Geo()
    for i in range(10):
        a = i * 2.4
        y = 0.35 + (i % 5) * 0.27
        r = 0.66 * math.sqrt(max(0.2, 1 - ((y - 0.85) / 0.95) ** 2))
        spines.add(bevel_box(0.08 + 0.12, 0.2, 0.4, 0.05, (0, 0, 0.2)).xf(T(r * math.cos(a), y, r * math.sin(a)) @
                                                                         RY(-math.degrees(a) - 90)))
    return [("Sprout", (70, 170, 80), sp), ("Detail", (250, 246, 230), spines)]


def s_marsh():
    stem = cfrustum(0.18, 0.14, 0.45, 8, "y", (0, 1.85, 0), 0.04)
    cap = G.Geo()
    cap.add(ccyl(0.48, 0.24, 10, "y", (0, 2.1, 0), 0.08))
    cap.add(ccyl(0.3, 0.16, 10, "y", (0, 2.26, 0), 0.06))
    spots = G.Geo()
    for (x, z) in ((0.25, 0.1), (-0.2, 0.2), (0.0, -0.3)):
        spots.add(bevel_box(0.2, 0.2, 0.2, 0.05, (x, 2.2, z)))
    return [("Sprout", (236, 226, 200), stem), ("Detail", (220, 50, 60), cap), ("Detail", (250, 250, 245), spots)]


def s_frost():
    sp = G.Geo()
    sp.add(bevel_box(0.25, 0.5, 0.25, 0.06, (0, 1.85, 0)))
    sp.add(leaf(0.55, 0.4).xf(T(0.05, 2.0, 0) @ RZ(30)))
    shards = G.Geo()
    for (x, y, z, a, b) in ((0.55, 0.9, -0.2, -30, 10), (-0.5, 1.1, 0.25, 35, -10), (0.15, 1.45, 0.5, 10, 40),
                            (-0.25, 0.6, -0.55, -15, -35)):
        shards.add(cfrustum(0.2, 0.06, 0.6, 4, "y", (0, 0.3, 0), 0.03).xf(T(x, y, z) @ RZ(a) @ RX(b)))
    return [("Sprout", (170, 230, 250), sp), ("Detail", (120, 210, 255), shards, "Glass")]


def s_lava():
    sp = G.Geo()
    sp.add(bevel_box(0.25, 0.45, 0.25, 0.06, (0, 1.82, 0)))
    sp.add(cfrustum(0.25, 0.04, 0.5, 5, "y", (0, 2.25, 0), 0.04))
    cracks = G.Geo()
    for (x, y, z, ang, ln) in ((-0.62, 0.8, 0.0, 70, 0.7), (-0.6, 1.2, 0.15, -30, 0.5), (0.1, 0.9, -0.62, 20, 0.8),
                               (0.35, 1.25, -0.52, -50, 0.5), (0.58, 0.6, 0.25, 80, 0.6), (0.0, 0.5, 0.62, 10, 0.7)):
        d = np.array((x, 0.0, z))
        n = d / np.linalg.norm(d)
        yaw = math.degrees(math.atan2(n[0], n[2]))
        cracks.add(bevel_box(0.12 + 0.08, ln, 0.2, 0.05, (0, 0, 0)).xf(T(x, y, z) @ RY(yaw) @ RZ(ang)))
    return [("Sprout", (255, 120, 40), sp, "Neon"), ("Detail", (255, 150, 40), cracks, "Neon")]


def s_crystal():
    gem = G.Geo()
    gem.add(cfrustum(0.25, 0.32, 0.25, 6, "y", (0, 1.8, 0), 0.03))
    gem.add(cfrustum(0.32, 0.0, 0.6, 6, "y", (0, 2.2, 0), 0.03))
    facets = G.Geo()
    for (x, y, z) in ((0.6, 0.8, 0.0), (-0.55, 1.1, 0.2), (0.15, 1.3, -0.55), (-0.2, 0.5, 0.58)):
        d = np.array((x, 0, z))
        yaw = math.degrees(math.atan2(d[0], d[2]))
        facets.add(cfrustum(0.22, 0.0, 0.3, 4, "z", (0, 0, 0.12), 0.02).xf(T(x, y, z) @ RY(yaw)))
    return [("Sprout", (250, 110, 200), gem, "Glass"), ("Detail", (90, 230, 250), facets, "Glass")]


def s_candy():
    sp = G.Geo()
    sp.add(bevel_box(0.25, 0.5, 0.25, 0.06, (0, 1.85, 0)))
    sp.add(ccyl(0.3, 0.2, 10, "z", (0, 2.25, 0), 0.06))
    out = [("Sprout", (250, 120, 180), sp)]
    rng = np.random.default_rng(42)
    for col in ((255, 90, 160), (80, 170, 255), (255, 220, 60)):
        g = G.Geo()
        for i in range(6):
            a = rng.uniform(0, math.tau)
            y = rng.uniform(0.35, 1.5)
            r = 0.68 * math.sqrt(max(0.2, 1 - ((y - 0.85) / 0.95) ** 2))
            g.add(bevel_box(0.36, 0.2, 0.2, 0.05, (0, 0, 0)).xf(T(r * math.cos(a), y, r * math.sin(a)) @
                                                              RY(rng.uniform(0, 180)) @ RZ(rng.uniform(-40, 40))))
        out.append(("Detail", col, g))
    return out


def s_cosmic():
    sp = G.Geo()
    sp.add(bevel_box(0.2, 0.55, 0.2, 0.05, (0, 1.9, 0)))
    star = G.Geo()
    for i in range(5):
        star.add(bevel_box(0.2, 0.42, 0.2, 0.05, (0, 0.21, 0)).xf(T(0, 2.3, 0) @ RZ(i * 72)))
    ring = G.lathe_loop([(0.9, -0.08), (1.25, -0.08), (1.25, 0.12), (0.9, 0.12)], 16).xf(T(0, 0.95, 0) @ RX(18) @
                                                                                       RZ(-12))
    return [("Sprout", (120, 90, 220), sp), ("Detail", (255, 230, 90), star, "Neon"),
            ("Detail", (170, 120, 255), ring, "Neon")]


SEEDS = [("Seed_Meadow", s_meadow), ("Seed_Dunes", s_dunes), ("Seed_Marsh", s_marsh), ("Seed_Frost", s_frost),
         ("Seed_Lava", s_lava), ("Seed_Crystal", s_crystal), ("Seed_Candy", s_candy), ("Seed_Cosmic", s_cosmic)]


# ---------------------------------------------------------------- Fences

FENCES = [
    ("Fence_Wood", dict(post=(160, 100, 56), rail=(186, 122, 70), brace=(150, 92, 52), pw=0.8, rw=0.5, cap=None)),
    ("Fence_Gold", dict(post=(250, 180, 40), rail=(250, 140, 40), brace=(255, 210, 70), pw=1.1, rw=0.7,
                        cap="ball", cap_col=(255, 224, 90))),
    ("Fence_Neon", dict(post=(40, 110, 230), rail=(40, 200, 240), brace=(30, 150, 230), pw=1.0, rw=0.6,
                        cap="crystal", cap_col=(120, 240, 255), strip=(90, 255, 255))),
    ("Fence_Cosmic", dict(post=(46, 26, 70), rail=(60, 34, 92), brace=(70, 40, 110), pw=1.1, rw=0.65, cap="star",
                          cap_col=(255, 230, 90), strip="rainbow")),
]
POST_H = 4.5
SPAN = 7.0
RAINBOW = ((255, 70, 70), (255, 170, 40), (255, 240, 60), (70, 230, 100), (60, 170, 255), (180, 90, 255))


def fence_tier(k, parent, name, st, row):
    f = k.sc.folder(parent, name)
    base = CF((0.0, KIT_Y, 40.0 + row * 14.0))
    fence_post(k, f, st, base)
    fence_rail(k, f, st, base * CF((10.0, 0, 0)))
    gate_arch(k, f, st, base * CF((26.0, 0, 0)))


def _post_geo(st, h=POST_H):
    pw = st["pw"]
    g = G.Geo()
    g.add(bevel_box(pw, h, pw, 0.15, (0, h / 2, 0)))
    g.add(bevel_box(pw + 0.3, 0.4, pw + 0.3, 0.1, (0, 0.2, 0)))
    return g


def _cap(k, m, st, base, h=POST_H, nm="Cap", tag="Cap"):
    kind = st.get("cap")
    pw = st["pw"]
    if kind is None:
        g = bevel_box(pw + 0.2, 0.3, pw + 0.2, 0.08, (0, h + 0.1, 0))
        return k.mesh(m, nm, "%s_%s" % (st["name"], tag), g, base, darker(st["post"], 0.85))
    if kind == "ball":
        g = ccyl(pw * 0.6, 0.5, 10, "y", (0, h + 0.2, 0), 0.1)
        g.add(G.sphere(pw * 0.55, 10, 6, (1, 1, 1), (0, h + 0.8, 0)))
        return k.mesh(m, nm, "%s_%s" % (st["name"], tag), g, base, st["cap_col"])
    if kind == "crystal":
        g = cfrustum(pw * 0.45, pw * 0.5, 0.4, 6, "y", (0, h + 0.2, 0), 0.05)
        g.add(cfrustum(pw * 0.5, 0.0, 1.2, 6, "y", (0, h + 1.0, 0), 0.05))
        return k.mesh(m, nm, "%s_%s" % (st["name"], tag), g, base, st["cap_col"], material="Glass")
    g = G.Geo()                                              # a five-point star
    for i in range(5):
        g.add(bevel_box(0.36, 0.7, 0.3, 0.08, (0, 0.35, 0)).xf(T(0, h + 1.0, 0) @ RZ(i * 72)))
    g.add(ccyl(0.35, 0.3, 8, "z", (0, h + 1.0, 0), 0.06))
    g.add(bevel_box(0.3, 0.5, 0.3, 0.06, (0, h + 0.25, 0)))
    return k.mesh(m, nm, "%s_%s" % (st["name"], tag), g, base, st["cap_col"], material="Neon")


def fence_post(k, parent, st, base):
    st = dict(st, name=parent.name)
    m = k.sc.model(parent, "Post")
    post = k.mesh(m, "Post", "%s_Post" % parent.name, _post_geo(st), base, st["post"])
    _cap(k, m, st, base)
    if st.get("strip"):
        _strips(k, m, st, base, [(0, 0.6, -st["pw"] / 2 - 0.08, 0.25, POST_H - 1.2, 0.2)], "PostStrip")
    post.p["pivot"] = post.p["cf"].inv() * base
    m.p["primary"] = post
    return m


def _strips(k, m, st, base, boxes, nm):
    """Neon strips: one colour (Neon tier) or a rainbow run (Cosmic tier); boxes (x, y0, z, w, h, d)."""
    if st["strip"] == "rainbow":
        for ci, col in enumerate(RAINBOW):
            g = G.Geo()
            for (x, y0, z, w, h, d) in boxes:
                seg = h / len(RAINBOW) if h > w else None
                if seg:
                    g.add(bevel_box(w, seg, d, 0.04, (x, y0 + seg * (ci + 0.5), z)))
                else:
                    sw = w / len(RAINBOW)
                    g.add(bevel_box(sw, h, d, 0.04, (x - w / 2 + sw * (ci + 0.5), y0 + h / 2, z)))
            k.mesh(m, nm, "%s_%s%d" % (m.parent.name, nm, ci + 1), g, base, col, material="Neon")
    else:
        g = G.Geo()
        for (x, y0, z, w, h, d) in boxes:
            g.add(bevel_box(w, h, d, 0.04, (x, y0 + h / 2, z)))
        k.mesh(m, nm, "%s_%s" % (m.parent.name, nm), g, base, st["strip"], material="Neon")


def fence_rail(k, parent, st, base):
    """7 long between post centres (local X from -3.5 to 3.5): two rails and an X brace.
    Pivot on the ground halfway between the posts."""
    m = k.sc.model(parent, "Rail")
    rw = st["rw"]
    L_ = SPAN
    rails = G.Geo()
    for y in (POST_H * 0.82, POST_H * 0.3):
        rails.add(bevel_box(L_, rw, rw * 0.7, 0.1, (0, y, 0)))
    r = k.mesh(m, "Rails", "%s_Rails" % parent.name, rails, base, st["rail"])
    br = G.Geo()
    y0, y1 = POST_H * 0.3, POST_H * 0.82
    ln = math.hypot(L_ - st["pw"], y1 - y0)
    ang = math.degrees(math.atan2(y1 - y0, L_ - st["pw"]))
    for sg in (-1, 1):
        br.add(bevel_box(ln, rw * 0.8, rw * 0.5, 0.08, (0, 0, 0)).xf(T(0, (y0 + y1) / 2, 0) @ RZ(sg * ang)))
    k.mesh(m, "Brace", "%s_Brace" % parent.name, br, base, st["brace"])
    if st.get("strip"):
        _strips(k, m, st, base, [(0, POST_H * 0.82 + rw / 2, 0, L_ - st["pw"], 0.2, rw * 0.5)], "RailStrip")
    r.p["pivot"] = r.p["cf"].inv() * base
    m.p["primary"] = r
    return m


def gate_arch(k, parent, st, base):
    """An open doorway 8 wide (clear between the posts, local X) the player runs through along Z,
    9 high, with a Board on top for the owner's name sign. Pivot on the ground at its centre."""
    m = k.sc.model(parent, "GateArch")
    pw = st["pw"] * 1.4
    W, H = 8.0, 9.0
    posts = G.Geo()
    for sx in (-1, 1):
        posts.add(bevel_box(pw, H, pw, 0.2, (sx * (W / 2 + pw / 2), H / 2, 0)))
        posts.add(bevel_box(pw + 0.4, 0.5, pw + 0.4, 0.12, (sx * (W / 2 + pw / 2), 0.25, 0)))
    p = k.mesh(m, "Posts", "%s_ArchPosts" % parent.name, posts, base, st["post"])
    beam = G.Geo()
    beam.add(bevel_box(W + 2 * pw + 1.0, 1.0, pw + 0.2, 0.15, (0, H + 0.5, 0)))
    beam.add(bevel_box(W + 2 * pw - 0.4, 0.6, pw * 0.7, 0.12, (0, H - 0.6, 0)))
    k.mesh(m, "Beam", "%s_ArchBeam" % parent.name, beam, base, st["rail"])
    sign = G.Geo()
    sign.add(bevel_box(9.0, 3.2, 0.6, 0.15, (0, H + 2.6, 0)))
    k.mesh(m, "SignFrame", "%s_ArchSign" % parent.name, sign, base, st["brace"])
    for sx in (-1, 1):
        _cap(k, m, dict(st, name=parent.name, pw=pw), base * CF((sx * (W / 2 + pw / 2), 0, 0)), h=H + 1.0,
             nm="Cap", tag="ArchCap")
    k.board(m, 8.2, 2.4, base * CF((0.0, H + 2.6, -0.35)), name="Board")
    k.board(m, 8.2, 2.4, base * CF((0.0, H + 2.6, 0.35), G.ry(180)), name="BoardBack")
    if st.get("strip"):
        _strips(k, m, st, base, [(0, H + 1.05, -pw / 2 - 0.12, W + 2 * pw, 0.25, 0.2)], "ArchStrip")
    p.p["pivot"] = p.p["cf"].inv() * base
    m.p["primary"] = p
    k.attr(m, "OpeningWidth", W)
    return m


# ---------------------------------------------------------------- UpgradeBoard

def upgrade_board(k, parent, base):
    """A small signboard on a post: a flat Board (front face -Z) and an invisible Prompt in front.
    Pivot on the ground under the post."""
    m = k.sc.model(parent, "UpgradeBoard")
    post = G.Geo()
    post.add(bevel_box(0.8, 6.0, 0.8, 0.15, (0, 3.0, 0.4)))
    post.add(bevel_box(1.4, 0.4, 1.4, 0.1, (0, 0.2, 0.4)))
    pp = k.mesh(m, "Post", "UpgradeBoard_Post", post, base, P.WOOD)
    fr = G.Geo()
    fr.add(bevel_box(6.0, 4.0, 0.5, 0.15, (0, 5.0, 0)))
    k.mesh(m, "Frame", "UpgradeBoard_Frame", fr, base, (250, 180, 40))
    roof = G.Geo()
    for sg in (-1, 1):
        roof.add(bevel_box(7.0, 0.4, 1.6, 0.1, (0, 0, 0)).xf(T(0, 7.3, sg * 0.55) @ RX(sg * 25)))
    k.mesh(m, "Roof", "UpgradeBoard_Roof", roof, base, (220, 70, 60))
    k.board(m, 5.2, 3.2, base * CF((0.0, 5.0, -0.35)))
    k.prompt(m, base * CF((0.0, 3.0, -2.5)))
    pp.p["pivot"] = pp.p["cf"].inv() * base
    m.p["primary"] = pp
    return m


def showcase(k, parent):
    """Preview only (never exported): the kit laid out to be looked at. Each fence tier as a
    short run (three posts, two rails) with its GateArch; the seeds in a row; Mound, Soil and
    UpgradeBoard together."""
    for i, (name, fn) in enumerate(SEEDS):
        seed(k, k.sc.folder(parent, "Seeds"), name, fn, CF((i * 3.4, KIT_Y, 0.0)))
    MD.mound(k, parent, CF((-8.0, KIT_Y, 2.0)))
    soil(k, parent, CF((-15.0, KIT_Y, 2.0)))
    upgrade_board(k, parent, CF((32.0, KIT_Y, 4.0), G.ry(-20)))
    for row, (name, st) in enumerate(FENCES):
        f = k.sc.folder(parent, name)
        z = 16.0 + row * 9.0
        for j in range(3):
            fence_post(k, f, st, CF((j * SPAN - 2.0, KIT_Y, z)))
        for j in range(2):
            fence_rail(k, f, st, CF(((j + 0.5) * SPAN - 2.0, KIT_Y, z)))
        gate_arch(k, f, st, CF((24.0, KIT_Y, z)))
