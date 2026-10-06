"""Portal gate modelled in Blender (frame only - no swirl, no effects; the centre is left open for
your own VFX).

    blender -b -P tools/portal_mesh.py -- <repo-root>

Builds a stepped round dais, a ring of 20 bevelled wedge stones (voussoirs) with a big keystone,
an inner trim ring, carved rune diamonds and two buttress feet. Every surface gets the same stud
texture as the map (box-projected UVs, 1 stud per world stud). Writes:

    exports/portal/Portal.fbx  (+ Portal.obj)   import into Studio, then run roblox/PlacePortal.lua
    exports/portal/portal_bounds.json           bounds in Roblox space (ground y=0, front -Z)
    previews/spear/Portal_mesh.png              studio-style preview render

Also importable: `import portal_mesh; portal_mesh.build(collection, tex_dir)` (used by render_spear.py).
"""
import json
import math
import os
import sys

import bmesh
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "gen"))
sys.path.insert(0, HERE)

STONE = "#7C74C4"
STONE_DK = "#5A519E"
STONE_LT = "#A39BE0"
BASE = "#4A4280"
R_IN, R_OUT, DEPTH = 6.6, 9.4, 3.4
BASE_TOP = 2.6
CY = BASE_TOP + R_OUT + 0.05


def rb(x, y, z):            # Roblox (x, y-up, z) -> Blender (x, -z, y)
    return (x, -z, y)


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def stud_mat(hexcol, tex_dir):
    import rockmesh
    from palette import COLORS
    key = "portal_" + hexcol.lstrip("#")
    if key not in COLORS:
        COLORS[key] = hex_rgb(hexcol) + ("Plastic",)
    return rockmesh.stud_material(key, tex_dir)


def wedge(bm, a0, a1, r0, r1, z0, z1, cy):
    """Curved wedge between angles a0..a1 (radians), radii r0..r1, depth z0..z1 (Roblox space)."""
    steps = max(2, int((a1 - a0) / math.radians(6)))
    rings = []
    for i in range(steps + 1):
        a = a0 + (a1 - a0) * i / steps
        ca, sa = math.cos(a), math.sin(a)
        col = []
        for (r, z) in ((r0, z0), (r1, z0), (r1, z1), (r0, z1)):
            col.append(bm.verts.new(rb(ca * r, cy + sa * r, z)))
        rings.append(col)
    for i in range(steps):
        a, b = rings[i], rings[i + 1]
        for k in range(4):
            bm.faces.new((a[k], a[(k + 1) % 4], b[(k + 1) % 4], b[k]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])


def box(bm, x0, y0, z0, x1, y1, z1):
    vs = [bm.verts.new(rb(x, y, z)) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
    idx = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    for f in idx:
        bm.faces.new([vs[i] for i in f])


def cylinder(bm, r, y0, y1, n=24):
    bot = [bm.verts.new(rb(math.cos(2 * math.pi * k / n) * r, y0, math.sin(2 * math.pi * k / n) * r)) for k in range(n)]
    top = [bm.verts.new(rb(math.cos(2 * math.pi * k / n) * r, y1, math.sin(2 * math.pi * k / n) * r)) for k in range(n)]
    for k in range(n):
        bm.faces.new((bot[k], bot[(k + 1) % n], top[(k + 1) % n], top[k]))
    bm.faces.new(list(reversed(bot)))
    bm.faces.new(top)


def finish(name, bm, color, coll, tex_dir, bevel=0.22):
    import rockmesh
    me = bpy.data.meshes.new(name)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    mod = ob.modifiers.new("bevel", "BEVEL")
    mod.width = bevel
    mod.segments = 2
    mod.limit_method = "ANGLE"
    dg = bpy.context.evaluated_depsgraph_get()
    new = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    ob.modifiers.clear()
    ob.data = new
    for p in ob.data.polygons:
        p.use_smooth = False
    rockmesh.box_uv(ob.data)
    ob.data.materials.append(stud_mat(color, tex_dir))
    ob.data.name = name
    return ob


def build(coll, tex_dir):
    objs = []
    # dais: three stepped round tiers
    bm = bmesh.new()
    cylinder(bm, 8.6, 0.0, 1.2)
    objs.append(finish("Portal_Base", bm, BASE, coll, tex_dir, 0.25))
    bm = bmesh.new()
    cylinder(bm, 7.5, 1.2, 2.0)
    objs.append(finish("Portal_Step", bm, STONE, coll, tex_dir, 0.2))
    bm = bmesh.new()
    cylinder(bm, 6.4, 2.0, BASE_TOP)
    objs.append(finish("Portal_Top", bm, STONE_LT, coll, tex_dir, 0.15))
    # voussoirs: 20 wedge stones in two tones, a big keystone on top
    n, gap = 20, math.radians(1.1)
    for tone, color in ((0, STONE), (1, STONE_DK)):
        bm = bmesh.new()
        for k in range(n):
            if k % 2 != tone:
                continue
            a0 = 2 * math.pi * k / n - math.pi / 2 + gap / 2
            a1 = 2 * math.pi * (k + 1) / n - math.pi / 2 - gap / 2
            mid = (a0 + a1) / 2
            if abs(math.sin(mid) - 1) < 0.02:
                continue                                  # keystone slot (top)
            r1 = R_OUT + (0.35 if k % 4 == 0 else 0.0)
            wedge(bm, a0, a1, R_IN, r1, -DEPTH / 2, DEPTH / 2, CY)
        objs.append(finish("Portal_Ring%d" % tone, bm, color, coll, tex_dir))
    bm = bmesh.new()                                      # keystone: bigger and deeper
    k_top = [k for k in range(n) if abs(math.sin(2 * math.pi * (k + 0.5) / n - math.pi / 2) - 1) < 0.02]
    a0 = 2 * math.pi * min(k_top) / n - math.pi / 2 + gap / 2          # one solid keystone over the slot
    a1 = 2 * math.pi * (max(k_top) + 1) / n - math.pi / 2 - gap / 2
    wedge(bm, a0 + math.radians(2), a1 - math.radians(2), R_IN - 0.3, R_OUT + 1.6, -DEPTH / 2 - 0.5,
          DEPTH / 2 + 0.5, CY)
    objs.append(finish("Portal_Keystone", bm, STONE_LT, coll, tex_dir))
    # inner trim ring (a smooth band just inside the stones)
    bm = bmesh.new()
    wedge(bm, 0, 2 * math.pi, R_IN - 0.55, R_IN + 0.05, -DEPTH / 2 - 0.2, DEPTH / 2 + 0.2, CY)
    objs.append(finish("Portal_Trim", bm, STONE_LT, coll, tex_dir, 0.12))
    # carved runes: diamonds set into the front face of every other stone
    bm = bmesh.new()
    for k in range(n):
        if k % 2:
            continue
        a = 2 * math.pi * (k + 0.5) / n - math.pi / 2
        if abs(math.sin(a) - 1) < 0.02:
            continue
        r = (R_IN + R_OUT) / 2
        cx, cy_ = math.cos(a) * r, CY + math.sin(a) * r
        s = 0.55
        pts = [(cx, cy_ + s), (cx + s, cy_), (cx, cy_ - s), (cx - s, cy_)]
        front = [bm.verts.new(rb(x, y, -DEPTH / 2 - 0.12)) for x, y in pts]
        back = [bm.verts.new(rb(x, y, -DEPTH / 2 + 0.05)) for x, y in pts]
        for i in range(4):
            bm.faces.new((front[i], front[(i + 1) % 4], back[(i + 1) % 4], back[i]))
        bm.faces.new(front)
        bm.faces.new(list(reversed(back)))
    objs.append(finish("Portal_Runes", bm, STONE_LT, coll, tex_dir, 0.05))
    # buttress feet either side of the ring base
    bm = bmesh.new()
    for s_ in (-1, 1):
        box(bm, s_ * 7.4 - 1.6, BASE_TOP - 0.4, -2.3, s_ * 7.4 + 1.6, BASE_TOP + 3.4, 2.3)
        box(bm, s_ * 8.6 - 1.0, BASE_TOP + 3.0, -1.8, s_ * 8.6 + 1.0, BASE_TOP + 5.0, 1.8)
    objs.append(finish("Portal_Feet", bm, STONE_DK, coll, tex_dir, 0.25))
    return objs


def bounds(objs):
    xs, ys, zs = [], [], []
    for ob in objs:
        for v in ob.data.vertices:
            x, by, bz = v.co
            xs.append(x)
            ys.append(bz)
            zs.append(-by)
    return [round(min(xs), 3), round(min(ys), 3), round(min(zs), 3)], [round(max(xs), 3), round(max(ys), 3),
                                                                       round(max(zs), 3)]


if __name__ == "__main__":
    bpy.ops.wm.read_factory_settings(use_empty=True)
    out = os.path.join(ROOT, "exports", "portal")
    os.makedirs(out, exist_ok=True)
    coll = bpy.context.scene.collection
    objs = build(coll, out)
    root = bpy.data.objects.new("Portal", None)
    coll.objects.link(root)
    for ob in objs:
        ob.parent = root
    mn, mx = bounds(objs)
    json.dump({"min": mn, "max": mx}, open(os.path.join(out, "portal_bounds.json"), "w"))
    print("portal bounds", mn, mx)
    bpy.ops.object.select_all(action="DESELECT")
    root.select_set(True)
    for ob in objs:
        ob.select_set(True)
    bpy.ops.export_scene.fbx(filepath=os.path.join(out, "Portal.fbx"), use_selection=True, path_mode="COPY",
                             embed_textures=True, axis_forward="-Z", axis_up="Y",
                             apply_scale_options="FBX_SCALE_ALL", mesh_smooth_type="FACE",
                             object_types={"EMPTY", "MESH"})
    bpy.ops.wm.obj_export(filepath=os.path.join(out, "Portal.obj"), export_selected_objects=True,
                          path_mode="COPY", forward_axis="NEGATIVE_Z", up_axis="Y")
    # preview render
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 48
    scene.cycles.use_denoising = False
    scene.render.resolution_x, scene.render.resolution_y = 1000, 1000
    scene.view_settings.view_transform = "Standard"
    world = bpy.data.worlds.new("w")
    scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.72, 0.95, 1)
    sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
    sun.data.energy = 3.5
    sun.rotation_euler = (math.radians(50), 0, math.radians(30))
    coll.objects.link(sun)
    gnd = bpy.data.meshes.new("g")
    gnd.from_pydata([(-40, -40, 0), (40, -40, 0), (40, 40, 0), (-40, 40, 0)], [], [(0, 1, 2, 3)])
    gm = bpy.data.materials.new("gm")
    gm.use_nodes = True
    gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.2, 0.55, 0.12, 1)
    gnd.materials.append(gm)
    coll.objects.link(bpy.data.objects.new("ground", gnd))
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    cam.data.lens = 35
    cam.location = (14, -30, 14)
    d = (0 - 14, 0 + 30, 11 - 14)
    cam.rotation_euler = (math.atan2(math.hypot(d[0], d[1]), -d[2]), 0, math.atan2(d[1], d[0]) - math.pi / 2)
    coll.objects.link(cam)
    scene.camera = cam
    scene.render.filepath = os.path.join(ROOT, "previews", "spear", "Portal_mesh.png")
    bpy.ops.render.render(write_still=True)
    print("done")
