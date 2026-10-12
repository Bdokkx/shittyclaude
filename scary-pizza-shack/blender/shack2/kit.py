"""The building vocabulary of the remake: palette, parts with the right defaults, the one
mesh language (chunky, bevelled, 6..12 sided, nothing thinner than 0.15), lamps as Models
with a Bulb and Lamp* attributes (no Light objects), and a registry of prop models so the
build can count them (the brief asks for 80+ different ones inside and 50+ outside).

Defaults follow the brief's style rules:
  * Parts are Plastic with SMOOTH surfaces; studs only where asked for (ground, roofs, brick
    tops, foliage, crates).
  * Decoration (the default) has CanCollide / CanTouch / CanQuery off, and CastShadow off
    when it is small; structure (solid=True) collides and can be queried.
"""
import math

import numpy as np

import spsgeo as G
from spsgeo import CF, T, RX, RY, RZ, S  # noqa: F401

# ---------------------------------------------------------------- palette (sRGB, true daylight colours)

PAL = {
    # inside: quiet base
    "tile": (226, 222, 206), "tile_old": (214, 206, 184), "tile_new": (242, 241, 234), "grout": (150, 146, 134),
    "skirt": (58, 50, 46), "dado": (196, 146, 44), "paint": (128, 142, 116), "paint_dark": (110, 124, 100),
    "cornice": (212, 200, 168), "ceil": (212, 206, 186), "ceil_stain": (190, 172, 130), "ceil_stain2": (198, 186, 150),
    "tbar": (176, 170, 154),
    "beam": (98, 66, 44), "beam_dark": (78, 52, 36),
    "floor_w": (222, 214, 192), "floor_b": (46, 44, 46), "floor_w_worn": (200, 190, 164),
    "floor_b_worn": (72, 66, 60), "floor_w_new": (244, 244, 238), "floor_b_new": (24, 24, 28),
    "fridge_body": (66, 70, 76), "liner": (214, 224, 228), "puddle": (120, 132, 140), "crate_blue": (52, 92, 160),
    "tub_lid_red": (196, 52, 40), "tub_lid_green": (70, 140, 70), "tub_white": (236, 234, 226),
    "screed": (78, 70, 60), "adhesive": (58, 52, 44), "rubber_worn": (58, 56, 54),
    "steel": (172, 176, 180), "steel_dark": (126, 130, 136), "steel_light": (200, 204, 206),
    "charcoal": (52, 52, 56), "rubber": (36, 36, 38), "black": (28, 28, 30), "cab_inside": (38, 28, 26),
    "wood": (150, 102, 64), "wood_dark": (96, 64, 42), "wood_light": (196, 156, 108), "wood_pale": (214, 184, 140),
    # brand
    "red": (178, 38, 32), "red_dark": (140, 28, 24), "red_light": (204, 64, 52),
    "cream": (236, 222, 184), "cream_dark": (212, 196, 154), "mustard": (214, 160, 44), "mustard_dark": (180, 128, 30),
    # oven
    "brick1": (156, 62, 46), "brick2": (142, 54, 42), "brick3": (168, 72, 52), "mortar": (72, 62, 58),
    "soot": (44, 38, 36), "ash": (120, 116, 112), "fire": (255, 132, 40), "hearth": (112, 58, 42),
    "brick_sooty": (92, 48, 40), "ember": (255, 96, 30), "iron": (46, 46, 50), "glass_hot": (255, 150, 70),
    # accents
    "shade_green": (40, 108, 70), "door_green": (52, 92, 70), "chalkboard": (34, 58, 44),
    "till_cream": (214, 202, 176), "crt_cream": (206, 196, 172), "grey_dark": (70, 72, 76), "grey": (130, 132, 134),
    "grey_light": (186, 188, 186), "locker_grey": (96, 108, 112), "locker_door": (118, 132, 136),
    "blind": (222, 214, 190), "neon_red": (255, 60, 50), "neon_warm": (255, 196, 132), "screen": (30, 46, 40),
    "glass": (190, 214, 222), "paper": (240, 236, 222), "paper_old": (222, 206, 160), "cork": (172, 128, 84),
    "label_blue": (54, 92, 150), "label_green": (64, 128, 72), "label_yellow": (230, 196, 70),
    "label_white": (238, 236, 228), "cardboard": (196, 160, 112), "cardboard_dark": (164, 128, 86),
    "flour": (248, 246, 238), "dough": (236, 204, 150), "sauce": (184, 36, 26), "cheese": (250, 206, 92),
    "tomato": (196, 46, 34), "basil": (60, 140, 64), "onion": (224, 206, 220), "pepper": (64, 150, 54),
    # outside: an overcast afternoon
    "grass": (78, 124, 74), "grass2": (70, 114, 68), "grass3": (88, 132, 80), "grass_dry": (128, 132, 84),
    "moss": (64, 96, 60), "litter": (116, 96, 66), "dirt": (128, 104, 78), "mud": (98, 82, 64),
    "pine": (54, 98, 72), "pine2": (48, 88, 66), "pine3": (62, 108, 78), "pine_dark": (42, 76, 58),
    "leaf": (84, 120, 62), "leaf2": (100, 128, 66), "trunk": (112, 80, 56), "trunk2": (96, 68, 48),
    "bark_grey": (128, 116, 102), "deadwood": (138, 124, 106),
    "asphalt": (92, 94, 100), "asphalt_patch": (80, 82, 88), "asphalt_new": (64, 66, 72), "tar": (54, 56, 60),
    "line_white": (232, 230, 220), "line_yellow": (220, 176, 58),
    "gravel": (150, 148, 140), "gravel2": (138, 136, 128), "concrete": (176, 174, 166),
    "concrete2": (164, 162, 154), "concrete_dark": (146, 144, 138), "kerb": (186, 184, 178),
    "rock": (132, 132, 126), "rock_dark": (108, 110, 106), "water": (60, 74, 80),
    "siding": (234, 220, 182), "siding2": (222, 206, 166), "trim_green": (40, 96, 64), "rust": (150, 84, 54),
    "hill": (52, 84, 62), "hill2": (46, 76, 58), "hill3": (60, 92, 66), "far_trees": (44, 74, 56),
}

FLAG_DECO = dict(collide=False, touch=False, query=False)


def col(c):
    return PAL[c] if isinstance(c, str) else tuple(int(v) for v in c)


# ---------------------------------------------------------------- the mesh language

def _orient_convex(V, faces):
    """Wind every face of a convex solid so its normal points away from the centre."""
    V = np.asarray(V, float)
    c = V.mean(0)
    out = []
    for f in faces:
        P = V[list(f)]
        n = np.zeros(3)
        for i in range(len(P)):
            a, b = P[i], P[(i + 1) % len(P)]
            n += np.array(((a[1] - b[1]) * (a[2] + b[2]), (a[2] - b[2]) * (a[0] + b[0]), (a[0] - b[0]) * (a[1] + b[1])))
        out.append(tuple(f) if np.dot(n, P.mean(0) - c) >= 0 else tuple(f[::-1]))
    return out


def bevel_box(sx, sy, sz, b=0.08, c=(0, 0, 0)):
    """Box with every edge chamfered by b: the basic 'chunky bevelled' block."""
    hx, hy, hz = sx / 2, sy / 2, sz / 2
    b = min(b, hx * 0.45, hy * 0.45, hz * 0.45)
    V, idx = [], {}

    def v(key, p):
        idx[key] = len(V)
        V.append(p)
    for sxg in (-1, 1):
        for syg in (-1, 1):
            for szg in (-1, 1):
                v((sxg, syg, szg, 0), (sxg * hx, syg * (hy - b), szg * (hz - b)))
                v((sxg, syg, szg, 1), (sxg * (hx - b), syg * hy, szg * (hz - b)))
                v((sxg, syg, szg, 2), (sxg * (hx - b), syg * (hy - b), szg * hz))
    F = []
    # main faces
    for ax in range(3):
        for sg in (-1, 1):
            quad = []
            for a in (-1, 1):
                for bb in ((-1, 1) if a == -1 else (1, -1)):
                    s = [0, 0, 0]
                    s[ax] = sg
                    o = [k for k in range(3) if k != ax]
                    s[o[0]], s[o[1]] = a, bb
                    quad.append(idx[(s[0], s[1], s[2], ax)])
            F.append(quad)
    # edge chamfers (between faces ax1 and ax2, running along the third axis)
    for ax1, ax2 in ((0, 1), (0, 2), (1, 2)):
        ax3 = 3 - ax1 - ax2
        for s1 in (-1, 1):
            for s2 in (-1, 1):
                q = []
                for s3, which in ((-1, ax1), (1, ax1), (1, ax2), (-1, ax2)):
                    s = [0, 0, 0]
                    s[ax1], s[ax2], s[ax3] = s1, s2, s3
                    q.append(idx[(s[0], s[1], s[2], which)])
                F.append(q)
    # corner triangles
    for sxg in (-1, 1):
        for syg in (-1, 1):
            for szg in (-1, 1):
                F.append([idx[(sxg, syg, szg, k)] for k in range(3)])
    V = [(p[0] + c[0], p[1] + c[1], p[2] + c[2]) for p in V]
    return G.Geo(V, _orient_convex(V, F))


def chamfer_slab(pts, h, b=0.05, c=(0, 0, 0)):
    """A top-view outline (x, z) raised to height h with its top edge chamfered by b (the
    bevelled look for odd shapes: broken tiles, plates). Bottom at c[1]."""
    P = [np.array(p, float) for p in pts]
    if G.poly_area([tuple(p) for p in P]) < 0:
        P = P[::-1]
    n = len(P)
    inset = []
    for k in range(n):
        a, p_, q = P[k - 1], P[k], P[(k + 1) % n]
        e1, e2 = p_ - a, q - p_
        n1 = np.array((-e1[1], e1[0])) / np.linalg.norm(e1)
        n2 = np.array((-e2[1], e2[0])) / np.linalg.norm(e2)
        m = n1 + n2
        d = 1.0 + float(n1 @ n2)
        inset.append(p_ + m * b / max(d, 0.35))
    V = []
    for p_ in P:
        V.append((p_[0], 0.0, p_[1]))
    for p_ in P:
        V.append((p_[0], h - b, p_[1]))
    for p_ in inset:
        V.append((p_[0], h, p_[1]))
    F = []
    for k in range(n):
        j = (k + 1) % n
        F.append((k, j, n + j, n + k))
        F.append((n + k, n + j, 2 * n + j, 2 * n + k))
    if G.is_convex([tuple(p) for p in P]):
        F.append(tuple(range(2 * n, 3 * n)))
        F.append(tuple(range(n))[::-1])
    else:
        for a, bb, cc in G.triangulate([tuple(p) for p in P]):
            F.append((2 * n + a, 2 * n + bb, 2 * n + cc))
            F.append((a, cc, bb))
    g = G.outward(G.Geo(V, F))
    return g.xf(G.T(c[0], c[1], c[2]))


def ccyl(r, h, n=8, axis="y", c=(0, 0, 0), b=0.06):
    """Cylinder with chamfered caps (n sides, a flat side facing +X / +Z)."""
    b = min(b, r * 0.4, h * 0.3)
    prof = [(0.0, -h / 2), (r - b, -h / 2), (r, -h / 2 + b), (r, h / 2 - b), (r - b, h / 2), (0.0, h / 2)]
    g = G.outward(G.lathe(prof, n, phase=math.pi / n))
    return G._orient(g, axis, c)


def cfrustum(r0, r1, h, n=8, axis="y", c=(0, 0, 0), b=0.05):
    b = min(b, min(r0, r1) * 0.4 if min(r0, r1) > 0 else b, h * 0.3)
    prof = [(0.0, -h / 2), (max(r0 - b, 0.0), -h / 2), (r0, -h / 2 + b), (r1, h / 2 - b), (max(r1 - b, 0.0), h / 2),
            (0.0, h / 2)]
    g = G.outward(G.lathe(prof, n, phase=math.pi / n))
    return G._orient(g, axis, c)


def lathe(profile, n=10):
    return G.outward(G.lathe(profile, n, phase=math.pi / n))


def rod(a, b, r=0.09, n=6):
    """A straight chunky rod between two points (r >= 0.075 keeps it 0.15 thick)."""
    return G.tube([tuple(a), tuple(b)], max(r, 0.075), n)


def bent(path, r=0.09, n=6):
    return G.tube([tuple(p) for p in path], max(r, 0.075), n)


def slab(pts_xz, thick, y=0.0):
    """Flat slab from an XZ outline (convex or not), thick upwards from y."""
    return G.slab_poly(pts_xz, thick, (0, y, 0))


def irregular(rng, r, n=7, wob=0.25):
    pts = []
    for k in range(n):
        a = math.tau * k / n + rng.uniform(-0.2, 0.2)
        rr = r * (1 + rng.uniform(-wob, wob))
        pts.append((rr * math.cos(a), rr * math.sin(a)))
    return pts


# ---------------------------------------------------------------- the kit

PROPS = {}          # kind -> (builder, where-hint)


def prop(kind):
    """Register a mesh prop: fn(rng) -> [(part name, colour, Geo)] in the prop's own space
    (origin on the floor / surface it stands on, -Z = its front)."""
    def deco(fn):
        PROPS[kind] = fn
        return fn
    return deco


class Kit:
    def __init__(self, sc, seed=7):
        self.sc = sc
        self.rng = np.random.default_rng(seed)
        self.used = {"inside": set(), "outside": set()}

    # -- parts ---------------------------------------------------------------
    def part(self, parent, name, size, cf_, color, solid=False, studs=False, shadow=None, material="Plastic",
             shape="Block", transparency=0.0, grid=True, **kw):
        flags = {} if solid else dict(FLAG_DECO)
        flags.update({k: kw.pop(k) for k in ("collide", "touch", "query") if k in kw})
        if shadow is None:
            shadow = max(size) >= 1.0 or solid
        surfaces = kw.pop("surfaces", None)
        if surfaces is None:
            if shape == "Block":
                surfaces = "studs" if studs else "smooth"
            elif shape == "Wedge":
                surfaces = "wedge" if studs else "smooth"
            else:
                surfaces = "smooth"
        return self.sc.part(parent, name, size, cf_, col(color), shape=shape, material=material,
                            transparency=transparency, shadow=shadow, surfaces=surfaces, grid=grid, **flags, **kw)

    def box(self, parent, name, lo, hi, color, **kw):
        lo, hi = np.asarray(lo, float), np.asarray(hi, float)
        size = hi - lo
        assert np.all(size > 0), (name, lo, hi)
        return self.part(parent, name, size, CF((lo + hi) / 2), color, **kw)

    def boxr(self, parent, name, size, center, R, color, **kw):
        return self.part(parent, name, size, CF(center, R), color, **kw)

    def wedge(self, parent, name, size, center, R, color, **kw):
        return self.part(parent, name, size, CF(center, R), color, shape="Wedge", **kw)

    def cyl(self, parent, name, length, diameter, center, axis_dir, color, **kw):
        import spslib
        R = spslib._axis_to_x(axis_dir)
        return self.part(parent, name, (length, diameter, diameter), CF(center, R), color, shape="Cylinder", **kw)

    def ball(self, parent, name, diameter, center, color, **kw):
        return self.part(parent, name, (diameter,) * 3, CF(center), color, shape="Ball", **kw)

    def pz(self, parent, name, z_mid, x0, x1, y0, y1, color, **kw):
        """Upright 0.4 plate facing +-Z (width x0..x1 and height y0..y1 in whole studs)."""
        return self.part(parent, name, (x1 - x0, 0.4, y1 - y0), CF(((x0 + x1) / 2, (y0 + y1) / 2, z_mid), G.rx(90)),
                         color, **kw)

    def px(self, parent, name, x_mid, z0, z1, y0, y1, color, **kw):
        """Upright 0.4 plate facing +-X (width z0..z1 and height y0..y1 in whole studs)."""
        return self.part(parent, name, (y1 - y0, 0.4, z1 - z0), CF((x_mid, (y0 + y1) / 2, (z0 + z1) / 2), G.rz(90)),
                         color, **kw)

    # -- meshes ---------------------------------------------------------------
    def mesh(self, parent, name, mesh_name, geo, frame, color, solid=False, shadow=None, material="SmoothPlastic",
             transparency=0.0, **kw):
        flags = {} if solid else dict(FLAG_DECO)
        flags.update({k: kw.pop(k) for k in ("collide", "touch", "query") if k in kw})
        if not solid:
            flags.setdefault("collide", False)
        else:
            flags.setdefault("collide", True)
        if shadow is None and geo is not None:
            lo, hi = geo.bbox()
            shadow = float(np.max(hi - lo)) >= 1.0 or solid
        elif shadow is None:
            shadow = True
        return self.sc.mesh(parent, name, mesh_name, geo, frame, col(color), material=material,
                            transparency=transparency, shadow=shadow, **flags, **kw)

    # -- props ------------------------------------------------------------------
    def prop(self, parent, kind, cf_, where="inside", name=None, colors=None, solid=False, seed=None, **kw):
        """Instantiate registered prop `kind` as a Model at cf_ (its origin on the surface)."""
        fn = PROPS[kind]
        rng = np.random.default_rng(seed if seed is not None else 1)
        parts = fn(rng)
        m = self.sc.model(parent, name or kind)
        first = None
        # one mesh per prop part; a prop whose shape depends on its seed gets one per seed
        tag = "" if seed is None else "_%d" % seed
        for pname, c, geo, *rest in parts:
            opts = rest[0] if rest else {}
            c = (colors or {}).get(pname, c)
            mesh_name = "P%s__%s" % (kind, pname)
            if mesh_name in self.sc.geoms and tag:
                lo, hi = geo.bbox()
                old = self.sc.geoms[mesh_name]
                cent = geo.xf(G.T(*(-(lo + hi) / 2)))
                if len(old.v) != len(cent.v) or not np.allclose(old.arr(), cent.arr(), atol=1e-6):
                    mesh_name = "P%s%s__%s" % (kind, tag, pname)
            mp = self.mesh(m, pname, mesh_name, geo, cf_, c, solid=solid and first is None, **opts, **kw)
            if first is None:
                first = mp
        if first is not None:
            m.p["primary"] = first
        self.used[where].add(kind)
        return m

    def mark_used(self, kind, where="inside"):
        self.used[where].add(kind)

    # -- markers, attributes ------------------------------------------------------
    def marker(self, parent, name, cf_):
        return self.sc.marker(parent, name, cf_)

    def attr(self, node, key, value):
        self.sc.attr(node, key, value)

    # -- lamps ----------------------------------------------------------------------
    def lamp(self, model, bulb, group="Shack", kind="Spot", rng=16.0, bright=1.0, color=(255, 196, 132),
             angle=110.0, shadows=True, flicker=0.0, face="Bottom", on_model=True):
        """Give `model` (holding the part `bulb`, named Bulb) the lamp attributes the game reads."""
        assert bulb.name == "Bulb", bulb
        a = {}
        a["LampGroup"] = group
        a["LampKind"] = kind
        a["LampRange"] = float(rng)
        a["LampBrightness"] = float(bright)
        a["LampColor"] = "%d,%d,%d" % tuple(col(color))
        if kind == "Spot":
            a["LampAngle"] = float(angle)
            a["LampFace"] = face           # the Bulb's face the spot shines from (its -Y: Bottom)
        a["LampShadows"] = bool(shadows)
        if flicker:
            a["LampFlicker"] = float(flicker)
        # on the Bulb always; on the Model too when the Model is the lamp itself
        bulb.p.setdefault("attrs", {}).update(a)
        if on_model:
            model.p.setdefault("attrs", {}).update(a)
        return model


def weld_to(sc, root, parts):
    for p in parts:
        p.p["anchored"] = False
        p.p["massless"] = True
        sc.weld(root, p, "Weld")


def pivot(node, world_cf):
    node.p["pivot"] = node.p["cf"].inv() * world_cf
