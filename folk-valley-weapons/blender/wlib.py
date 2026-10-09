"""Weapon modelling toolkit.

Everything here works in ROBLOX space, relative to the Handle:
  +Y = along the weapon (grip at the bottom, tip / head at the top)
  +X = width, the cutting edge or hammer face side
  +Z = the thin side
Geometry is built as bmesh pieces, merged into one mesh per colour ("part"), and
only turned into Blender objects (Z up) at the very end.
"""
import math

import bpy  # noqa: I001  (bpy must load before bmesh / mathutils)
import bmesh
from mathutils import Matrix, Vector

import rbxscene as rs

TAU = math.tau


# ---------------------------------------------------------------- transforms (Roblox space)

def T(x=0.0, y=0.0, z=0.0):
    return Matrix.Translation((x, y, z))


def R(axis, deg):
    return Matrix.Rotation(math.radians(deg), 4, axis)


def S(x, y=None, z=None):
    y = x if y is None else y
    z = x if z is None else z
    return Matrix.Diagonal((x, y, z, 1.0))


def lerp(a, b, t):
    return a + (b - a) * t


def smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


# ---------------------------------------------------------------- bmesh helpers

def _bm_from_mesh(me):
    bm = bmesh.new()
    bm.from_mesh(me)
    bpy.data.meshes.remove(me)
    return bm


def copy_bm(bm):
    me = bpy.data.meshes.new("tmp")
    bm.to_mesh(me)
    return _bm_from_mesh(me)


def xform(bm, m):
    bmesh.ops.transform(bm, matrix=m, verts=bm.verts)
    if m.determinant() < 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    return bm


def merge_into(dst, src, m=None):
    me = bpy.data.meshes.new("tmp")
    src.to_mesh(me)
    if m is not None:
        me.transform(m)
        if m.determinant() < 0:
            me.flip_normals()
    dst.from_mesh(me)
    bpy.data.meshes.remove(me)


def fix_normals(bm):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


# ---------------------------------------------------------------- primitives

def box(sx, sy, sz, bevel=0.0, seg=2):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
    if bevel > 0:
        bmesh.ops.bevel(bm, geom=list(bm.edges) + list(bm.verts), offset=min(bevel, min(sx, sy, sz) / 2 - 1e-4),
                        segments=seg, profile=0.5, affect="EDGES", clamp_overlap=True)
    return bm


def cylinder(r, h, segs=24, bevel=0.0, bseg=2, r_top=None):
    """Cylinder along Y centred on the origin; r_top makes it a cone frustum."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segs,
                          radius1=r, radius2=r if r_top is None else r_top, depth=h,
                          matrix=Matrix.Rotation(-math.pi / 2, 4, "X"))
    if bevel > 0:
        cap_edges = [e for e in bm.edges if all(abs(abs(v.co.y) - h / 2) < 1e-5 for v in e.verts)]
        bmesh.ops.bevel(bm, geom=cap_edges, offset=bevel, segments=bseg, profile=0.5,
                        affect="EDGES", clamp_overlap=True)
    return bm


def sphere(r, segs=16, rings=10, scale=(1, 1, 1)):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=rings, radius=r)
    # make the poles point along Y
    bmesh.ops.rotate(bm, matrix=Matrix.Rotation(-math.pi / 2, 3, "X"), verts=bm.verts)
    bmesh.ops.scale(bm, vec=scale, verts=bm.verts)
    return bm


def ico(r, subdiv=1, scale=(1, 1, 1)):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=r)
    bmesh.ops.scale(bm, vec=scale, verts=bm.verts)
    return bm


def torus(R_, r, segs=24, rsegs=8, axis="Y"):
    """Ring around the Y axis (lies in the XZ plane)."""
    bm = bmesh.new()
    rings = []
    for i in range(segs):
        a = TAU * i / segs
        ring = []
        for j in range(rsegs):
            b = TAU * j / rsegs
            rr = R_ + r * math.cos(b)
            ring.append(bm.verts.new((rr * math.cos(a), r * math.sin(b), rr * math.sin(a))))
        rings.append(ring)
    for i in range(segs):
        a, b_ = rings[i], rings[(i + 1) % segs]
        for j in range(rsegs):
            bm.faces.new((a[j], a[(j + 1) % rsegs], b_[(j + 1) % rsegs], b_[j]))
    fix_normals(bm)
    if axis == "Z":
        xform(bm, R("X", 90))
    elif axis == "X":
        xform(bm, R("Z", 90))
    return bm


def lathe(profile, segs=24, sx=1.0, sz=1.0, phase=0.0, close=True, rmod=None):
    """Surface of revolution around Y. profile = [(r, y), ...] bottom to top.
    An r of 0 at either end closes it with a pole. rmod(angle) scales the radius
    around the axis (lobes, petals)."""
    bm = bmesh.new()
    rings = []
    for r, y in profile:
        if r <= 1e-6:
            rings.append([bm.verts.new((0, y, 0))])
        else:
            ring = []
            for i in range(segs):
                a = phase + TAU * i / segs
                k = rmod(a) if rmod else 1.0
                ring.append(bm.verts.new((r * k * sx * math.cos(a), y, r * k * sz * math.sin(a))))
            rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        if len(a) == 1 and len(b) == 1:
            continue
        if len(a) == 1:
            for i in range(segs):
                bm.faces.new((a[0], b[(i + 1) % segs], b[i]))
        elif len(b) == 1:
            for i in range(segs):
                bm.faces.new((a[i], a[(i + 1) % segs], b[0]))
        else:
            for i in range(segs):
                bm.faces.new((a[i], a[(i + 1) % segs], b[(i + 1) % segs], b[i]))
    if close:
        if len(rings[0]) > 1:
            bm.faces.new(list(reversed(rings[0])))
        if len(rings[-1]) > 1:
            bm.faces.new(rings[-1])
    fix_normals(bm)
    return bm


def slab(points, thickness, bevel=0.0, seg=2):
    """A 2D outline (x, y) in the Roblox XY plane, extruded along Z (thickness)
    with rounded bevelled edges. The silhouette matches the outline exactly."""
    cu = bpy.data.curves.new("slab", "CURVE")
    cu.dimensions = "2D"
    cu.fill_mode = "BOTH"
    sp = cu.splines.new("POLY")
    sp.points.add(len(points) - 1)
    for p, (x, y) in zip(sp.points, points):
        p.co = (x, y, 0, 1)
    sp.use_cyclic_u = True
    bevel = min(bevel, thickness / 2 - 1e-4) if bevel > 0 else 0.0
    cu.extrude = max(thickness / 2 - bevel, 1e-4)
    cu.bevel_depth = bevel
    cu.bevel_resolution = seg if bevel > 0 else 0
    cu.offset = -bevel
    ob = bpy.data.objects.new("slab_tmp", cu)
    bpy.context.scene.collection.objects.link(ob)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    bpy.data.objects.remove(ob)
    bpy.data.curves.remove(cu)
    bm = _bm_from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    fix_normals(bm)
    return bm


def loft(rings, tags=None, cap_start=True, cap_end=True, closed=True, gap_tags=None):
    """Join cross-section rings (lists of Vector, same count; or a single point
    for a pointed end). tags[k] labels the faces between ring point k and k+1 (an
    int stored on each face so the mesh can later be split into colours)."""
    bm = bmesh.new()
    tag_layer = bm.faces.layers.int.new("tag")
    vrings = [[bm.verts.new(p) for p in ring] for ring in rings]
    n = max(len(r) for r in rings)
    for gi, (a, b) in enumerate(zip(vrings, vrings[1:])):
        for k in range(n if closed else n - 1):
            t = gap_tags[gi] if gap_tags else (tags[k] if tags else 0)
            if len(a) == 1 and len(b) == 1:
                continue
            if len(b) == 1:
                f = bm.faces.new((a[k], a[(k + 1) % n], b[0]))
            elif len(a) == 1:
                f = bm.faces.new((a[0], b[(k + 1) % n], b[k]))
            else:
                f = bm.faces.new((a[k], a[(k + 1) % n], b[(k + 1) % n], b[k]))
            f[tag_layer] = t
    if closed and cap_start and len(vrings[0]) > 2:
        f = bm.faces.new(list(reversed(vrings[0])))
        f[tag_layer] = gap_tags[0] if gap_tags else -1
    if closed and cap_end and len(vrings[-1]) > 2:
        f = bm.faces.new(vrings[-1])
        f[tag_layer] = -1
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    if closed:
        fix_normals(bm)
    return bm


def split_by_tag(bm, mapping):
    """mapping: {tag: name}. Returns {name: bmesh} (tags not listed go to mapping[None])."""
    layer = bm.faces.layers.int.get("tag")
    out = {}
    for name in set(mapping.values()):
        keep = {t for t, n in mapping.items() if n == name}
        c = copy_bm(bm)
        lay = c.faces.layers.int.get("tag")
        drop = [f for f in c.faces if (f[lay] if f[lay] in mapping else None) not in keep]
        bmesh.ops.delete(c, geom=drop, context="FACES")
        out[name] = c
    return out


def sweep(path, widths, thicks=None, sides=10, cap_start=True, point_end=True, up=Vector((0, 0, 1))):
    """Tube along a path (list of Vector). Cross-sections are ellipses: `widths`
    across the path in the path's plane, `thicks` along `up` (Roblox Z by default).
    A width of 0 at the end makes a point."""
    thicks = thicks or widths
    rings = []
    n = len(path)
    for i, p in enumerate(path):
        t = (path[min(i + 1, n - 1)] - path[max(i - 1, 0)]).normalized()
        side = t.cross(up)
        if side.length < 1e-6:
            side = t.orthogonal()
        side.normalize()
        u = side.cross(t).normalized()
        w, th = widths[i], thicks[i]
        if w <= 1e-6 and th <= 1e-6:
            rings.append([p.copy()])
            continue
        rings.append([p + side * (w / 2) * math.cos(TAU * k / sides) + u * (th / 2) * math.sin(TAU * k / sides)
                      for k in range(sides)])
    return loft(rings, cap_start=cap_start, cap_end=not point_end)


# ---------------------------------------------------------------- 2D outlines

def circle_pts(r, n=24, cx=0.0, cy=0.0, a0=0.0, sx=1.0):
    return [(cx + r * sx * math.cos(a0 + TAU * i / n), cy + r * math.sin(a0 + TAU * i / n)) for i in range(n)]


def star_pts(n, ro, ri, rot=90.0, round_tips=0):
    pts = []
    for i in range(2 * n):
        r = ro if i % 2 == 0 else ri
        a = math.radians(rot) + math.pi * i / n
        pts.append((r * math.cos(a), r * math.sin(a)))
    return pts


def catmull(points, samples=6, closed=False):
    """Smooth a polyline through `points` with a Catmull-Rom spline."""
    pts = [Vector(p) if not isinstance(p, Vector) else p for p in points]
    out = []
    n = len(pts)
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        p0 = pts[(i - 1) % n] if closed else pts[max(i - 1, 0)]
        p1 = pts[i]
        p2 = pts[(i + 1) % n]
        p3 = pts[(i + 2) % n] if closed else pts[min(i + 2, n - 1)]
        for s in range(samples):
            t = s / samples
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    if not closed:
        out.append(pts[-1])
    return [tuple(v) for v in out]


def arc_pts(cx, cy, r, a0, a1, n):
    return [(cx + r * math.cos(math.radians(lerp(a0, a1, i / n))), cy + r * math.sin(math.radians(lerp(a0, a1, i / n))))
            for i in range(n + 1)]


# ---------------------------------------------------------------- blades

def blade_section(xl, xr, t, el, er, z0=0.0, spine=None):
    """Hexagonal blade cross-section in the XZ plane (as (x, z) pairs, CCW from +Y).
    xl/xr = left / right edge x, t = thickness at the flats, el/er = width of the
    bevelled edge bands. spine = thickness of a flat back on the left (single edge)."""
    h = t / 2
    if spine is None:
        return [(xr, z0), (xr - er, z0 + h), (xl + el, z0 + h), (xl, z0), (xl + el, z0 - h), (xr - er, z0 - h)]
    s = spine / 2
    return [(xr, z0), (xr - er, z0 + h), (xl + el, z0 + h), (xl, z0 + s), (xl, z0 - s), (xl + el, z0 - h),
            (xr - er, z0 - h)]


def blade(stations, single_edge=False, edge_tag=1, tip=True):
    """Loft a blade through stations: dicts with y, xl, xr, t, el, er (+ spine for
    single-edged, optional x shift and z0). Faces on the bevelled edge bands get
    edge_tag, the flats get 0, the spine 2. Returns a tagged bmesh."""
    rings = []
    for s in stations:
        sec = blade_section(s["xl"], s["xr"], s["t"], s["el"], s["er"], s.get("z0", 0.0),
                            s.get("spine") if single_edge else None)
        rings.append([Vector((x, s["y"], z)) for x, z in sec])
    if tip:
        last = stations[-1]
        tip_pt = Vector((last.get("tipx", (last["xl"] + last["xr"]) / 2), last.get("tipy", last["y"] + 0.3), 0))
        rings.append([tip_pt])
    if single_edge:
        # faces: 0 edge(+z) 1 flat(+z) 2 back bevel(+z) 3 spine 4 back bevel(-z) 5 flat(-z) 6 edge(-z)
        tags = [edge_tag, 0, 0, 2, 0, 0, edge_tag]
    else:
        tags = [edge_tag, 0, edge_tag, edge_tag, 0, edge_tag]
    return loft(rings, tags=tags, cap_start=True, cap_end=not tip)


# ---------------------------------------------------------------- weapon assembly

class Part:
    def __init__(self, name, color, material="SmoothPlastic", transparency=0.0, smooth=None):
        self.name = name
        self.color = tuple(color)
        self.material = material
        self.transparency = transparency
        self.smooth = smooth      # sharp-edge angle in degrees (None = weapon default)
        self.bm = bmesh.new()

    def add(self, bm, m=None):
        merge_into(self.bm, bm, m)
        return self


class Weapon:
    def __init__(self, wid, rarity, kind):
        self.id = wid
        self.rarity = rarity
        self.kind = kind          # Sword | Dagger | Hammer
        self.parts = {}
        self.order = []
        self.fx = None            # Roblox-space position of the Fx attachment
        self.smooth_angle = 28.0

    def part(self, name, color, material="SmoothPlastic", transparency=0.0, smooth=None):
        p = Part(name, color, material, transparency, smooth)
        self.parts[name] = p
        self.order.append(name)
        return p

    # -------------------------------------------------------------- finish
    def build(self, collection, smooth_angle=None):
        """Create one Blender object per part (Blender space), with Roblox-like
        preview materials, clean normals and UVs. Returns metadata for the rig."""
        info = {"Id": self.id, "Rarity": self.rarity, "Kind": self.kind, "Parts": []}
        lo = Vector((1e9, 1e9, 1e9))
        hi = Vector((-1e9, -1e9, -1e9))
        objs = []
        tris = 0
        for name in self.order:
            p = self.parts[name]
            if not p.bm.verts:
                continue
            bm = p.bm
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
            bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-6)
            me = bpy.data.meshes.new("%s__%s" % (self.id, name))
            bm.to_mesh(me)
            # bounds in Roblox space
            vs = [v.co for v in me.vertices]
            plo = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
            phi = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
            lo = Vector(map(min, lo, plo))
            hi = Vector(map(max, hi, phi))
            box_uvs(me)
            me.transform(rs.RB2BL)
            me.shade_smooth()
            me.set_sharp_from_angle(angle=math.radians(p.smooth or smooth_angle or self.smooth_angle))
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
                "Name": name, "Mesh": me.name, "Color": list(p.color), "Material": p.material,
                "Transparency": p.transparency,
                "Size": [round(v, 4) for v in (phi - plo)], "Center": [round(v, 4) for v in c],
                "Tris": nt,
            })
        info["Top"] = round(hi.y, 3)
        info["Bottom"] = round(lo.y, 3)
        info["Tris"] = tris
        info["Fx"] = [round(v, 3) for v in self.fx] if self.fx else None
        info["Extents"] = {"lo": [round(v, 3) for v in lo], "hi": [round(v, 3) for v in hi]}
        return objs, info


def box_uvs(me, scale=0.25):
    """Box-projected UVs (1 UV unit = 4 studs) so Roblox material textures tile sanely."""
    uvl = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        n = poly.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            if ax == 0:
                uv = (co.z, co.y)
            elif ax == 1:
                uv = (co.x, co.z)
            else:
                uv = (co.x, co.y)
            uvl.data[li].uv = (uv[0] * scale, uv[1] * scale)


# ---------------------------------------------------------------- crafted pieces (sword anatomy)

def oct_section(w, h, c):
    """Chamfered rectangle (octagon) w x h with corner chamfer c, as (u, v) pairs."""
    w2, h2 = w / 2, h / 2
    c = min(c, w2 * 0.95, h2 * 0.95)
    return [(w2, h2 - c), (w2 - c, h2), (-w2 + c, h2), (-w2, h2 - c),
            (-w2, -h2 + c), (-w2 + c, -h2), (w2 - c, -h2), (w2, -h2 + c)]


def bar_x(stations, chamfer=0.04, y=0.0, z=0.0):
    """Loft along X through stations (x, height_y, depth_z[, chamfer]) with
    chamfered-rectangle sections. Good for crossguards."""
    rings = []
    for st in stations:
        x, sy, sz = st[:3]
        c = st[3] if len(st) > 3 else chamfer
        rings.append([Vector((x, y + v, z + u)) for u, v in oct_section(sz, sy, c)])
    return loft(rings)


def blade_ring(y, w, h, ef=0.02, eb=0.0, hb=None, ridge_x=0.0, x0=0.0, z0=0.0):
    """One double-edged blade cross-section at height y: half-width w, half
    thickness h at the ridge, small edge flats (half-height ef), optional bevel band
    eb wide (half thickness hb at its inner side). Returns (points, tags)."""
    hb = h * 0.55 if hb is None else hb
    pts, tags = [], []

    def add(x, z, tag):
        pts.append(Vector((x0 + x, y, z0 + z)))
        tags.append(tag)
    add(w, -ef, 1)            # right edge flat (to next point)
    add(w, ef, 1 if eb else 0)
    if eb:
        add(w - eb, hb, 0)
    add(ridge_x, h, 0)
    if eb:
        add(-w + eb, hb, 1)
    add(-w, ef, 1)            # left edge flat
    add(-w, -ef, 1 if eb else 0)
    if eb:
        add(-w + eb, -hb, 0)
    add(ridge_x, -h, 0)
    if eb:
        add(w - eb, -hb, 1)
    return pts, tags


def sword_blade(y0, y_shoulder, y_tip, w0, w1, h0, h1, ef=0.02, eb=0.0, point_curve=0.35,
                n_point=6, x_fn=None, tip_x=0.0):
    """Straight double-edged blade: linear taper from y0 (half-width w0, half-thick h0)
    to the shoulder of the point (w1, h1), then an ogive point to y_tip.
    x_fn(y) can bend the blade sideways. Returns a tagged bmesh (0 faces, 1 edges)."""
    stations = [(y0, w0, h0), ((y0 + y_shoulder) / 2, (w0 + w1) / 2, (h0 + h1) / 2), (y_shoulder, w1, h1)]
    for i in range(1, n_point):
        t = i / n_point
        # convex point: width falls off slowly then quickly
        k = 1 - t ** (1 + point_curve * 2) if point_curve > 0 else 1 - t
        k = max(k, 0.0)
        stations.append((lerp(y_shoulder, y_tip, t), w1 * k, max(h1 * (1 - t * 0.75), 0.012)))
    rings = []
    tags = None
    for y, w, h in stations:
        x0 = x_fn(y) if x_fn else 0.0
        pts, tg = blade_ring(y, w, h, ef=min(ef, h * 0.6), eb=eb * (w / w1 if w1 else 1), ridge_x=0.0, x0=x0)
        rings.append(pts)
        tags = tg
    rings.append([Vector(((x_fn(y_tip) if x_fn else 0.0) + tip_x, y_tip, 0.0))])
    return loft(rings, tags=tags, cap_start=True, cap_end=False)


def wrapped_grip(y0, y1, r0, r_mid=None, pitch=0.22, amp=0.022, around=12, sx=1.0, sz=1.0,
                 profile=(0.15, 1.0, 0.62, 0.30)):
    """Leather strap spiral-wrapped around a barrel-shaped grip core along Y.

    The mesh grid itself follows the helix, so each strap edge is a crisp step:
    rows within one turn use `profile` (radius bump at phases 0, .04, .35, .65, .95
    of the strap: low at the hidden edge, high where it overlaps the next turn)."""
    r_mid = r0 if r_mid is None else r_mid
    phases = (0.0, 0.05, 0.50, 0.93)
    k = len(phases)
    turns = int(math.ceil((y1 - y0) / pitch)) + 1
    bm = bmesh.new()
    rows = []
    for n in range(turns * k + 1):
        q, m = divmod(n, k)
        yb = y0 + (q - 1 + phases[m]) * pitch
        row = []
        for j in range(around):
            th = TAU * j / around
            y = yb + (th / TAU) * pitch
            yc = min(max(y, y0), y1)
            t = (yc - y0) / (y1 - y0)
            base = lerp(r0, r_mid, math.sin(math.pi * t))
            inside = y0 + 0.004 < y < y1 - 0.004
            r = base + (amp * profile[m] if inside else 0.0)
            row.append(bm.verts.new((r * sx * math.cos(th), yc, r * sz * math.sin(th))))
        rows.append(row)
    N = len(rows)
    for n in range(N - 1):
        for j in range(around):
            a, b = rows[n][j], rows[n + 1][j]
            if j + 1 < around:
                c, d = rows[n + 1][j + 1], rows[n][j + 1]
            else:
                if n + 1 + k >= N:
                    continue
                c, d = rows[n + 1 + k][0], rows[n + k][0]
            try:
                bm.faces.new((a, d, c, b))
            except ValueError:
                pass
    # drop the slivers that were clamped flat onto the end planes
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-5)
    flat = [f for f in bm.faces if all(abs(v.co.y - y0) < 1e-5 for v in f.verts)
            or all(abs(v.co.y - y1) < 1e-5 for v in f.verts)]
    bmesh.ops.delete(bm, geom=flat, context="FACES")
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context="VERTS")
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    # make sure the normals point outward (open tube: check one face)
    f = max(bm.faces, key=lambda f: f.calc_area())
    c = f.calc_center_median()
    if f.normal.dot(Vector((c.x, 0, c.z))) < 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    return bm


def wheel_pommel(cy, rd, half_t, rb, hb, c=0.03, segs=28, cx=0.0):
    """Disc ('wheel') pommel facing +/-Z with a raised round boss on both faces."""
    cb = min(0.025, hb * 0.6)
    prof = [(0, -half_t - hb), (rb - cb, -half_t - hb), (rb, -half_t - hb + cb), (rb, -half_t),
            (rd - c, -half_t), (rd, -half_t + c), (rd, half_t - c), (rd - c, half_t), (rb, half_t),
            (rb, half_t + hb - cb), (rb - cb, half_t + hb), (0, half_t + hb)]
    bm = lathe(prof, segs=segs)
    xform(bm, R("X", 90))
    xform(bm, T(cx, cy, 0))
    return bm


def helix_ribbon(y0, y1, rx, rz, turns, width, height, phase=0.0, hand=1, samples_per_turn=16, lift=0.0,
                 dwell=0.0, face=math.pi / 2):
    """A flat cord wound helically around an oval core (radii rx, rz) along Y.
    Two of these with opposite `hand` make the diamond lattice of a katana grip.
    dwell (0..0.9) makes the cord cross the faces at `face` / face+pi steeply and
    fold quickly around the sides, like real tsuka-ito."""
    n = max(int(turns * samples_per_turn), 4)
    # time spent per unit angle ~ 1 / (1 + dwell * cos(2 (theta - face)))
    steps = 4000
    total_angle = TAU * turns
    cum = [0.0]
    for k in range(steps):
        a = (k + 0.5) / steps * total_angle
        th_abs = phase + hand * a
        cum.append(cum[-1] + 1.0 / (1.0 + dwell * math.cos(2 * (th_abs - face))))
    path, normals = [], []
    j = 0
    for i in range(n + 1):
        t = i / n
        target = t * cum[-1]
        while j < steps and cum[j + 1] < target:
            j += 1
        seg = cum[j + 1] - cum[j]
        f = (target - cum[j]) / seg if seg > 0 else 0.0
        a = (j + f) / steps * total_angle
        th = phase + hand * a
        y = lerp(y0, y1, t)
        p = Vector((rx * math.cos(th), y, rz * math.sin(th)))
        nrm = Vector((math.cos(th) / rx, 0, math.sin(th) / rz)).normalized()
        path.append(p + nrm * lift)
        normals.append(nrm)
    rings = []
    for i, p in enumerate(path):
        tan = (path[min(i + 1, n)] - path[max(i - 1, 0)]).normalized()
        nrm = normals[i]
        side = nrm.cross(tan).normalized()
        w = width / 2
        rings.append([p + side * w - nrm * 0.004, p + side * (w * 0.7) + nrm * height,
                      p - side * (w * 0.7) + nrm * height, p - side * w - nrm * 0.004])
    return loft(rings)


def katana_blade(y0, y_tip, w0, w1, h0, h1, sori=0.32, kissaki=0.55, hamon=0.45, hamon_amp=0.07,
                 hamon_freq=6.5, n=28, x0=-0.17):
    """Curved single-edged blade (edge toward +X, curving back toward -X).
    Cross-section: edge, hamon line, shinogi ridge, mune. Faces between the edge
    and the wavy hamon line get tag 1 (lighter steel), the rest tag 0."""
    L = y_tip - y0
    tk = 1 - kissaki / L
    rings = []
    for i in range(n + 1):
        t = i / n
        y = y0 + L * t
        xb = x0 - sori * t ** 2
        if t <= tk:
            W = lerp(w0, w1, t / tk)
            hs = lerp(h0, h1, t / tk)
        else:
            u = (t - tk) / (1 - tk)
            W = w1 * math.sqrt(max(1 - u ** 2.2, 0.0))
            hs = max(h1 * (1 - u) ** 0.8, 0.012)
        if t >= 1:
            rings.append([Vector((xb, y, 0))])
            break
        xe = xb + W
        xs = xb + 0.33 * W
        hm = hs * 0.72
        m = 0.05 * W
        frac = hamon + hamon_amp * math.sin(hamon_freq * y + 0.6) + 0.03 * math.sin(hamon_freq * 2.3 * y)
        frac = max(0.18, min(0.8, frac))
        xh = xe - frac * (xe - xs)
        zh = hs * (xe - xh) / max(xe - xs, 1e-6)
        sec = [(xe, 0), (xh, zh), (xs, hs), (xb + m, hm), (xb, 0), (xb + m, -hm), (xs, -hs), (xh, -zh)]
        rings.append([Vector((x, y, z)) for x, z in sec])
    tags = [1, 0, 0, 0, 0, 0, 0, 1]
    return loft(rings, tags=tags, cap_start=True, cap_end=False)


def bar_y(stations, chamfer=0.03, x=0.0, z=0.0):
    """Loft along Y through stations (y, width_x, depth_z[, chamfer]) with chamfered
    rectangle sections (collars, habaki, hammer heads seen end-on)."""
    rings = []
    for st in stations:
        y, sx, sz = st[:3]
        c = st[3] if len(st) > 3 else chamfer
        rings.append([Vector((x + u, y, z + v)) for u, v in oct_section(sx, sz, c)])
    return loft(rings)


def oval_surface(x, rx, rz):
    """Height of an oval grip's front surface (+Z) above its axis at offset x."""
    return rz * math.sqrt(max(0.0, 1.0 - (x / rx) ** 2))


def face_inlay(points, cy, rx, rz, t=0.03, side=1, bevel=0.008, sink=0.006):
    """A small bevelled slab (outline in x / y around 0) laid onto the front (+Z,
    side=1) or back (side=-1) of an oval grip centred at height cy, following its curve."""
    bm = slab(points, t, bevel, seg=1)
    # poke the flat caps so they can follow the grip's curve without dipping into it
    caps = [f for f in bm.faces if abs(f.normal.z) > 0.9]
    bmesh.ops.poke(bm, faces=caps)
    for v in bm.verts:
        x, y, z = v.co
        zz = oval_surface(x, rx, rz) - sink + (z + t / 2)
        v.co = Vector((x, y + cy, side * zz))
    if side < 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    fix_normals(bm)
    return bm


def profile_blade(stations, y_tip, n_point=6, point_curve=0.3, ef=0.02, tip_x=0.0, x_fn=None):
    """Double-edged ridged blade through explicit stations (y, half_width, half_thick,
    bevel_band) followed by an ogive point to y_tip. Faces of the edge flats and
    bevel bands get tag 1 (so they can be a separate colour), the rest tag 0."""
    sts = list(stations)
    y1, w1, h1, e1 = sts[-1]
    for i in range(1, n_point):
        t = i / n_point
        k = max(1 - t ** (1 + point_curve * 2), 0.0)
        sts.append((lerp(y1, y_tip, t), w1 * k, max(h1 * (1 - t * 0.75), 0.012), e1 * max(k, 0.25)))
    rings, tags = [], None
    for y, w, h, e in sts:
        x0 = x_fn(y) if x_fn else 0.0
        pts, tg = blade_ring(y, w, h, ef=min(ef, h * 0.6), eb=min(e, w * 0.45), x0=x0)
        rings.append(pts)
        tags = tg
    rings.append([Vector(((x_fn(y_tip) if x_fn else 0.0) + tip_x, y_tip, 0.0))])
    return loft(rings, tags=tags, cap_start=True, cap_end=False)


def blade_face_z(x, y, stations):
    """Surface height of a profile_blade's flat faces at (x, y) (interpolated)."""
    if y <= stations[0][0]:
        st = stations[0]
    elif y >= stations[-1][0]:
        st = stations[-1]
    else:
        for a, b in zip(stations, stations[1:]):
            if a[0] <= y <= b[0]:
                t = (y - a[0]) / (b[0] - a[0])
                st = tuple(lerp(a[i], b[i], t) for i in range(4))
                break
    _, w, h, e = st
    hb = h * 0.55
    inner = max(w - e, 1e-4)
    ax = min(abs(x), inner)
    return h - (h - hb) * ax / inner


def surface_vein(points, width, stations, side=1, lift=0.006, thick=0.012, taper=True, sub=2):
    """A thin raised strip drawn on a profile_blade face along `points` [(x, y)],
    following the faces (and over the ridge). width can taper to the end."""
    pts = []
    for (xa, ya), (xb, yb) in zip(points, points[1:]):
        for k in range(sub):
            t = k / sub
            pts.append((lerp(xa, xb, t), lerp(ya, yb, t)))
    pts.append(points[-1])
    n = len(pts)
    rings = []
    for i, (x, y) in enumerate(pts):
        xa, ya = pts[max(i - 1, 0)]
        xb, yb = pts[min(i + 1, n - 1)]
        tx, ty = xb - xa, yb - ya
        L = math.hypot(tx, ty) or 1.0
        nx, ny = -ty / L, tx / L
        wd = width * ((1 - 0.85 * i / (n - 1)) if taper else 1.0) / 2
        ring = []
        for sx, up in ((-1, 0.0), (0.0, 1.0), (1, 0.0)):
            px, py = x + nx * wd * sx, y + ny * wd * sx
            z = blade_face_z(px, py, stations) + lift - 0.004 + up * thick
            ring.append(Vector((px, py, side * z)))
        rings.append(ring if side > 0 else list(reversed(ring)))
    return loft(rings, closed=False)


def rock(r, seed=1, jitter=0.18, subdiv=1, scale=(1, 1, 1)):
    """Low-poly faceted rock: an icosphere with its vertices pushed around."""
    import random
    rng = random.Random(seed)
    bm = ico(r, subdiv=subdiv)
    for v in bm.verts:
        v.co *= 1 + rng.uniform(-jitter, jitter)
    bmesh.ops.scale(bm, vec=scale, verts=bm.verts)
    return bm


def teardrop(r, length, segs=10):
    """Drip shape hanging down from y=0 (bulb at the bottom)."""
    prof = [(0, -length)]
    for i in range(1, 7):
        a = -90 + 180 * i / 7
        prof.append((r * math.cos(math.radians(a)), -length + r + r * math.sin(math.radians(a))))
    prof += [(r * 0.45, -length * 0.35), (r * 0.2, 0.0), (0, 0.02)]
    return lathe(prof, segs=segs)


def banded_blade(y0, y_tip, wfun, hfun, bounds, slope=0.45, groove=0.035, inset=0.86, n_point=7,
                 y_shoulder=None, edge_band=0.0, edge_tag=100):
    """Double-edged blade split into chevron bands (^ shaped boundaries) with a
    small notch at each boundary. Faces get the band index as their tag; with
    edge_band > 0 the bevelled cutting edges get edge_tag instead.
    wfun / hfun give half-width / half-thickness at a height y."""
    ys = [y0]
    for b in bounds:
        ys += [b - groove, b, b + groove]
    ysh = y_shoulder if y_shoulder is not None else (bounds[-1] + y0) / 2
    pts = sorted(set([round(v, 5) for v in ys + [ysh]]))
    # point: finer stations above the shoulder
    for i in range(1, n_point):
        pts.append(lerp(ysh, y_tip, i / n_point))
    pts = sorted(set(round(v, 5) for v in pts))
    rings, gaps = [], []
    seg_tags = None
    for y in pts:
        w, h = wfun(y), hfun(y)
        k = inset if any(abs(y - b) < 1e-6 for b in bounds) else 1.0
        eb = min(edge_band, w * 0.4) if edge_band else 0.0
        sec, seg_tags = blade_ring(0.0, w * k, h * k, ef=min(0.02, h * 0.5), eb=eb * k)
        rings.append([Vector((v.x, y - slope * abs(v.x), v.z)) for v in sec])
    rings.append([Vector((0, y_tip, 0))])
    for a, b in zip(pts, pts[1:] + [y_tip]):
        mid = (a + b) / 2
        gaps.append(sum(1 for bb in bounds if bb <= mid))
    bm = loft(rings, gap_tags=gaps, cap_start=True, cap_end=False)
    if edge_band:
        # re-tag the bevelled edge faces: they are the faces whose ring segment had tag 1
        lay = bm.faces.layers.int.get("tag")
        for f in bm.faces:
            c = f.calc_center_median()
            y = c.y + slope * abs(c.x)
            w = wfun(min(max(y, y0), y_tip))
            if abs(c.x) > w - min(edge_band, w * 0.4) * 1.05 - 1e-4 and len(f.verts) >= 3:
                f[lay] = edge_tag
    return bm


def sweep_band(path, widths, thicks, phi0, phi1, lift=0.006, rise=0.01, up=Vector((0, 0, 1)), n_across=3):
    """A strip lying on the surface of an elliptical sweep (same path / sizes as
    sweep()) between section angles phi0..phi1 (degrees, 0 = +side, 90 = +up)."""
    rings = []
    n = len(path)
    for i, p in enumerate(path):
        t = (path[min(i + 1, n - 1)] - path[max(i - 1, 0)]).normalized()
        side = t.cross(up)
        if side.length < 1e-6:
            side = t.orthogonal()
        side.normalize()
        u = side.cross(t).normalized()
        w, th = widths[i] / 2, thicks[i] / 2
        ring = []
        for j in range(n_across):
            f = j / (n_across - 1)
            ph = math.radians(lerp(phi0, phi1, f))
            nrm = (side * math.cos(ph) / max(w, 1e-4) + u * math.sin(ph) / max(th, 1e-4)).normalized()
            bump = rise * math.sin(math.pi * f)
            ring.append(p + side * w * math.cos(ph) + u * th * math.sin(ph) + nrm * (lift + bump))
        rings.append(ring)
    return loft(rings, closed=False)


def leaf_pts(length, width, n=10, tip_sharp=1.6, base_round=0.8):
    """Pointed oval (feather / leaf) outline from (0, 0) to (0, length)."""
    right = []
    for i in range(1, n):
        t = i / n
        x = width / 2 * (math.sin(math.pi * t) ** base_round) * (1 - t) ** (tip_sharp - 1) * 1.4
        right.append((min(x, width / 2), length * t))
    return [(0, 0)] + right + [(0, length)] + [(-x, y) for x, y in reversed(right)]


def bolt_pts(s=1.0):
    """Chunky lightning bolt outline, about 0.5 x 1.0 at s=1, centred on the origin."""
    pts = [(-0.05, 0.50), (0.24, 0.50), (0.07, 0.12), (0.25, 0.12), (-0.17, -0.52), (-0.02, -0.05),
           (-0.21, -0.05)]
    return [(x * s, y * s) for x, y in pts]


def puff(r, scale=(1, 1, 1), segs=12, rings=8):
    return sphere(r, segs=segs, rings=rings, scale=scale)
