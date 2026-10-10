"""Prop modelling toolkit: the weapons' geometry helpers (wlib) plus a Prop
assembler that knows about the original prop it replaces.

Everything is modelled in the prop's HANDLE space (Roblox axes: +Y up, +Z the
front for the NPC outfit pieces, which are welded on turned 180 degrees). A
prop is a list of parts; each part is one colour / material and becomes one
MeshPart. Several parts may share a name (four Crown jewels), and parts can
belong to a sub-model (the Trapdoor's flaps).
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WEAPONS_BLENDER = os.path.join(os.path.dirname(os.path.dirname(HERE)), "folk-valley-weapons", "blender")
sys.path.insert(0, WEAPONS_BLENDER)

import bpy  # noqa: E402,I001
import bmesh  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import rbxscene as rs  # noqa: E402
import wlib  # noqa: E402
from wlib import (T, R, S, lerp, smoothstep, merge_into, xform, copy_bm, fix_normals, box, cylinder,  # noqa: E402,F401
                  sphere, ico, torus, lathe, slab, loft, sweep, circle_pts, star_pts, catmull, arc_pts, rock,
                  teardrop, leaf_pts, bolt_pts, puff, slab_holes, text_slab, crescent_pts, bat_wing_pts, pyramid,
                  rounded_rect_pts, ring_slab, capsule, boolean, projected_slab, star3d, drop_facing, box_uvs,
                  snowflake, helix_ribbon)
import defs as wdefs  # noqa: E402  (pumpkin helpers, aim, densify, lathe_x / lathe_z)
from defs import (aim, densify, lathe_x, lathe_z, shaft, band, pumpkin_profile, pumpkin_body,  # noqa: E402,F401
                  pumpkin_zsurf, pumpkin_leaf, bmesh_new)

TAU = math.tau

MATERIALS = {"SmoothPlastic", "Plastic", "Neon", "Metal", "Glass", "Wood", "Fabric", "Ice", "Slate", "Foil"}


# ---------------------------------------------------------------- the original props (rbxtool JSON)

def _m4(cf):
    c = cf["CFrame"] if "CFrame" in cf else cf
    r, p = c["orientation"], c["position"]
    return Matrix(((r[0][0], r[0][1], r[0][2], p[0]), (r[1][0], r[1][1], r[1][2], p[1]),
                   (r[2][0], r[2][1], r[2][2], p[2]), (0, 0, 0, 1)))


class Original:
    """Lookups into the original prop: where each named part sits in Handle space."""

    def __init__(self, node):
        self.node = node
        h = next((c for c in node["children"] if c["name"] == "Handle"), None)
        self.handle = _m4(h["props"]["CFrame"]) if h else Matrix.Identity(4)
        self.inv = self.handle.inverted()
        attrs = node["props"].get("Attributes", {}).get("Attributes", {})
        self.attrs = {k: list(v.values())[0] for k, v in attrs.items()}

    def parts(self, name, node=None):
        """[(size Vector, Handle-space 4x4 matrix)] of every part called `name` (recursing into sub-models)."""
        out = []
        for c in (node or self.node)["children"]:
            if c["class"] == "Model":
                out += self.parts(name, c)
            elif c["name"] == name and "Size" in c["props"]:
                out.append((Vector(c["props"]["Size"]["Vector3"]), self.inv @ _m4(c["props"]["CFrame"])))
        return out

    def part(self, name):
        return self.parts(name)[0]

    def center(self, name):
        return self.part(name)[1].translation

    def size(self, name):
        return self.part(name)[0]


# ---------------------------------------------------------------- assembly

class PPart:
    def __init__(self, name, color, material, transparency, smooth, model, cast_shadow):
        assert material in MATERIALS, material
        self.name = name
        self.color = tuple(int(c) for c in color)
        self.material = material
        self.transparency = transparency
        self.smooth = smooth
        self.model = model            # index of the sub-model it belongs to (None = the prop itself)
        self.cast_shadow = cast_shadow
        self.bm = bmesh.new()

    def add(self, bm, m=None):
        merge_into(self.bm, bm, m)
        return self


class Prop:
    def __init__(self, pid, original=None, kind="Prop"):
        self.id = pid
        self.orig = original
        self.kind = kind
        self.parts = []
        self.smooth_angle = 32.0
        self.notes = ""

    def part(self, name, color, material="SmoothPlastic", transparency=0.0, smooth=None, model=None,
             cast_shadow=None):
        p = PPart(name, color, material, transparency, smooth, model, cast_shadow)
        self.parts.append(p)
        return p

    def build(self, collection):
        """One Blender object per part (Blender space) with preview materials; returns
        (objects, metadata for the Roblox build script)."""
        info = {"Id": self.id, "Kind": self.kind, "Parts": []}
        lo = Vector((1e9, 1e9, 1e9))
        hi = Vector((-1e9, -1e9, -1e9))
        objs, tris, used = [], 0, {}
        for p in self.parts:
            if not p.bm.verts:
                continue
            bm = p.bm
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
            bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-6)
            used[p.name] = used.get(p.name, 0) + 1
            mesh_name = "%s__%s" % (self.id, p.name) + ("" if used[p.name] == 1 else str(used[p.name]))
            me = bpy.data.meshes.new(mesh_name)
            bm.to_mesh(me)
            vs = [v.co for v in me.vertices]
            plo = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
            phi = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
            lo = Vector(map(min, lo, plo))
            hi = Vector(map(max, hi, phi))
            box_uvs(me)
            me.transform(rs.RB2BL)
            me.shade_smooth()
            me.set_sharp_from_angle(angle=math.radians(p.smooth or self.smooth_angle))
            ob = bpy.data.objects.new(me.name, me)
            collection.objects.link(ob)
            wn = ob.modifiers.new("wn", "WEIGHTED_NORMAL")
            wn.keep_sharp = True
            wn.weight = 50
            with bpy.context.temp_override(object=ob, active_object=ob, selected_objects=[ob]):
                bpy.ops.object.modifier_apply(modifier=wn.name)
            me.calc_loop_triangles()
            nt = len(me.loop_triangles)
            tris += nt
            me.materials.append(rs.roblox_material(p.material, p.color, p.transparency))
            if p.material == "Neon":
                rs.neon_no_bounce(ob)
            objs.append(ob)
            c = (plo + phi) / 2
            info["Parts"].append({
                "Name": p.name, "Mesh": me.name, "Color": list(p.color), "Material": p.material,
                "Transparency": p.transparency, "Model": p.model, "CastShadow": p.cast_shadow,
                "Size": [round(v, 4) for v in (phi - plo)], "Center": [round(v, 4) for v in c], "Tris": nt,
            })
        info["Top"] = round(hi.y, 4)
        info["Bottom"] = round(lo.y, 4)
        info["Tris"] = tris
        info["Extents"] = {"lo": [round(v, 3) for v in lo], "hi": [round(v, 3) for v in hi]}
        return objs, info


# ---------------------------------------------------------------- extra shapes for props

def blob(centers, segs=20, rings=12):
    """Cartoon cloud / puff cluster: spheres (x, y, z, r[, sx, sy, sz]) unioned
    into one watertight shell (exact boolean union, so no hidden inner faces)."""
    out = None
    for c in centers:
        x, y, z, r = c[:4]
        sc = c[4:7] if len(c) >= 7 else (1, 1, 1)
        s = sphere(r, segs, rings, scale=sc)
        xform(s, T(x, y, z))
        out = s if out is None else boolean(out, s, "UNION")
    return out


def union_all(pieces):
    out = None
    for p in pieces:
        out = p if out is None else boolean(out, p, "UNION")
    return out


def cut(a, *cutters):
    for c in cutters:
        a = boolean(a, c, "DIFFERENCE")
    return a


def rounded_box(sx, sy, sz, r, seg=3):
    return box(sx, sy, sz, bevel=r, seg=seg)


def superellipse_pts(rx, ry, p=2.6, n=40, cx=0.0, cy=0.0, a0=0.0):
    """Rounded-square-ish outline (|x/rx|^p + |y/ry|^p = 1)."""
    pts = []
    for i in range(n):
        a = a0 + TAU * i / n
        c, s = math.cos(a), math.sin(a)
        x = rx * math.copysign(abs(c) ** (2 / p), c)
        y = ry * math.copysign(abs(s) ** (2 / p), s)
        pts.append((cx + x, cy + y))
    return pts


def wobble_pts(pts, amp, freq=5, seed=0.0):
    """Push an outline in and out a little (hand-cut look)."""
    n = len(pts)
    cx = sum(p[0] for p in pts) / n
    cy = sum(p[1] for p in pts) / n
    out = []
    for i, (x, y) in enumerate(pts):
        a = math.atan2(y - cy, x - cx)
        k = 1 + amp * math.sin(freq * a + seed) + amp * 0.5 * math.sin(2.3 * freq * a + seed * 1.7)
        out.append((cx + (x - cx) * k, cy + (y - cy) * k))
    return out


def tube(points, r, sides=10, cap=True):
    """Constant-radius tube along a polyline (list of Vector)."""
    points = [Vector(q) for q in points]
    return sweep(points, [2 * r] * len(points), [2 * r] * len(points), sides=sides, cap_start=cap, point_end=False)


def taper_tube(points, r0, r1, sides=8, point=False):
    points = [Vector(q) for q in points]
    n = len(points)
    ws = [2 * lerp(r0, r1, i / max(n - 1, 1)) for i in range(n)]
    if point:
        ws[-1] = 0.0
    return sweep(points, ws, ws, sides=sides, cap_start=True, point_end=point)


def straw_tuft(base, direction, length, n=7, spread=22.0, width=0.07, seed=1, droop=0.15):
    """A bundle of tapered straw strands fanning out from `base` along `direction`."""
    import random
    rng = random.Random(seed)
    d = Vector(direction).normalized()
    side = d.orthogonal().normalized()
    up2 = d.cross(side).normalized()
    out = bmesh.new()
    for i in range(n):
        a = TAU * i / n + rng.uniform(-0.3, 0.3)
        tilt = math.radians(spread * rng.uniform(0.4, 1.0))
        dd = (d * math.cos(tilt) + (side * math.cos(a) + up2 * math.sin(a)) * math.sin(tilt)).normalized()
        L = length * rng.uniform(0.75, 1.1)
        p0 = Vector(base) + (side * math.cos(a) + up2 * math.sin(a)) * width * 0.8
        p1 = p0 + dd * L * 0.5
        p2 = p0 + dd * L + Vector((0, -droop * L * rng.uniform(0.2, 1.0), 0))
        w = width * rng.uniform(0.8, 1.2)
        strand = sweep([p0, p1, p2], [w, w * 0.8, 0.0], [w * 0.55, w * 0.45, 0.0], sides=4, point_end=True)
        merge_into(out, strand)
    return out


def ellipsoid_shell_z(rx, ry, rz):
    """z(x, y) on the front (+Z) of an ellipsoid centred at the origin (for projected_slab)."""
    def zs(x, y):
        k = 1 - (x / rx) ** 2 - (y / ry) ** 2
        return rz * math.sqrt(max(k, 1e-6))
    return zs


def zigzag_hem(r_top, r_bot, y_top, y_bot, teeth=10, depth=0.25, segs_per=4, sx=1.0, sz=1.0, flare=None):
    """A flared skirt / cone whose bottom edge is cut into zigzag points.
    Returns an open-bottom shell (outer surface only, double-sided by thickness)."""
    n = teeth * segs_per
    rings = []
    rows = 6
    for j in range(rows + 1):
        t = j / rows
        ring = []
        for i in range(n):
            a = TAU * i / n
            ph = (i % segs_per) / segs_per
            tooth = abs(ph - 0.5) * 2               # 1 at a notch, 0 at a point
            yb = y_bot + depth * tooth
            y = lerp(y_top, yb, t)
            r = lerp(r_top, r_bot, t if flare is None else flare(t))
            ring.append(Vector((r * sx * math.cos(a), y, r * sz * math.sin(a))))
        rings.append(ring)
    return loft(rings, cap_start=False, cap_end=False)


def thicken(bm, t):
    """Give an open shell some thickness (solidify, keeps it watertight)."""
    me = bpy.data.meshes.new("thick")
    bm.to_mesh(me)
    ob = bpy.data.objects.new("thick", me)
    bpy.context.scene.collection.objects.link(ob)
    mod = ob.modifiers.new("sol", "SOLIDIFY")
    mod.thickness = t
    mod.offset = -1
    mod.use_even_offset = True
    mod.use_rim = True
    dg = bpy.context.evaluated_depsgraph_get()
    me2 = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    bpy.data.objects.remove(ob)
    bpy.data.meshes.remove(me)
    out = bmesh.new()
    out.from_mesh(me2)
    bpy.data.meshes.remove(me2)
    fix_normals(out)
    return out


def subdivide_smooth(bm, levels=1):
    """Catmull-Clark subdivision (keeps the outline, rounds everything)."""
    me = bpy.data.meshes.new("subd")
    bm.to_mesh(me)
    ob = bpy.data.objects.new("subd", me)
    bpy.context.scene.collection.objects.link(ob)
    mod = ob.modifiers.new("sub", "SUBSURF")
    mod.levels = levels
    mod.render_levels = levels
    dg = bpy.context.evaluated_depsgraph_get()
    me2 = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    bpy.data.objects.remove(ob)
    bpy.data.meshes.remove(me)
    out = bmesh.new()
    out.from_mesh(me2)
    bpy.data.meshes.remove(me2)
    return out


def displace(bm, fn):
    """Move every vertex by fn(co) -> Vector offset."""
    for v in bm.verts:
        v.co = v.co + fn(v.co.copy())
    return bm


def load_original(path):
    with open(path) as f:
        data = json.load(f)
    return {m["name"]: m for m in data[0]["children"] if m["class"] == "Model"}


def lathe_loop(loop, segs=24, rmod=None, phase=0.0, sx=1.0, sz=1.0):
    """Surface of revolution around Y of a CLOSED cross-section loop [(r, y), ...]
    (rings, rims, tyres): watertight with no end caps."""
    bm = bmesh.new()
    rings = []
    for r, y in loop:
        ring = []
        for i in range(segs):
            a = phase + TAU * i / segs
            k = rmod(a) if rmod else 1.0
            ring.append(bm.verts.new((r * k * sx * math.cos(a), y, r * k * sz * math.sin(a))))
        rings.append(ring)
    n = len(rings)
    for j in range(n):
        a, b = rings[j], rings[(j + 1) % n]
        for i in range(segs):
            bm.faces.new((a[i], a[(i + 1) % segs], b[(i + 1) % segs], b[i]))
    fix_normals(bm)
    return bm


def lathe_loop_z(loop, segs=24, rmod=None):
    """lathe_loop around the Z axis (faces the viewer): loop = [(r, z), ...]."""
    return xform(lathe_loop(loop, segs=segs, rmod=rmod), R("X", 90))


def boolean(a, b, op="DIFFERENCE", self_check=True):
    """a minus (or union / intersect) b, both closed bmeshes; returns a new bmesh.
    Unlike wlib.boolean this tolerates b being several overlapping pieces."""
    sc = bpy.context.scene.collection
    objs = []
    for name, bm in (("bool_a", a), ("bool_b", b)):
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        ob = bpy.data.objects.new(name, me)
        sc.objects.link(ob)
        objs.append(ob)
    mod = objs[0].modifiers.new("bool", "BOOLEAN")
    mod.operation = op
    mod.solver = "EXACT"
    mod.object = objs[1]
    mod.use_self = self_check
    mod.use_hole_tolerant = True
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(objs[0].evaluated_get(dg))
    for ob in objs:
        m = ob.data
        bpy.data.objects.remove(ob)
        bpy.data.meshes.remove(m)
    out = bmesh.new()
    out.from_mesh(me)
    bpy.data.meshes.remove(me)
    bmesh.ops.remove_doubles(out, verts=out.verts, dist=1e-6)
    return out
