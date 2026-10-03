"""Blender helpers that turn the blocky base shapes from gen/assets.py into the
deformed, faceted, stud-textured rock meshes seen in the reference shots:

    boxes -> voxel remesh (fuse) -> noise displacement (deform) -> decimate (facets)
          -> up-facing faces split off as the sand/grass "Top" mesh
          -> box-projected UVs (1 UV unit = 4 studs) on a tiling stud texture

Import inside Blender only.
"""
import math
import os
import random

import bmesh
import bpy
import numpy as np

from palette import COLORS

STUDS_PER_TILE = 4
TILE_PX = 256


# ------------------------------------------------------------------ stud textures

def stud_texture(name, rgb, out_dir):
    """Tileable texture with 4x4 square studs (bevelled like Roblox's stud look)."""
    path = os.path.join(out_dir, "studs_%s.png" % name)
    img = bpy.data.images.get("studs_" + name)
    if img:
        return img
    n = TILE_PX
    cell = n // STUDS_PER_TILE
    base = np.array(rgb, dtype=np.float32) / 255.0
    px = np.empty((n, n, 3), dtype=np.float32)
    px[:] = base
    yy, xx = np.mgrid[0:n, 0:n]
    cx, cy = xx % cell, yy % cell          # position inside a stud cell (y up in Blender images)
    inset, edge = cell * 0.22, cell * 0.07
    inside = (cx >= inset) & (cx < cell - inset) & (cy >= inset) & (cy < cell - inset)
    top = inside & (cy >= cell - inset - edge)
    left = inside & (cx < inset + edge)
    bottom = inside & (cy < inset + edge)
    right = inside & (cx >= cell - inset - edge)
    face = inside & ~(top | left | bottom | right)
    px[face] = np.clip(base * 1.04, 0, 1)
    px[top | left] = np.clip(base * 1.22 + 0.03, 0, 1)
    px[bottom | right] = np.clip(base * 0.74, 0, 1)
    # faint grain so big faces don't look flat
    rng = np.random.default_rng(abs(hash(name)) % 2 ** 32)
    px *= (1 + (rng.random((n, n, 1), dtype=np.float32) - 0.5) * 0.04)
    rgba = np.concatenate([np.clip(px, 0, 1), np.ones((n, n, 1), np.float32)], axis=2)
    img = bpy.data.images.new("studs_" + name, n, n, alpha=False)
    img.pixels.foreach_set(rgba.ravel())
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    img.filepath = path
    return img


def stud_material(color_name, out_dir):
    mat = bpy.data.materials.get("Studs_" + color_name)
    if mat:
        return mat
    r, g, b, _ = COLORS[color_name]
    img = stud_texture(color_name, (r, g, b), out_dir)
    mat = bpy.data.materials.new("Studs_" + color_name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.interpolation = "Linear"
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.7
    return mat


# ------------------------------------------------------------------ geometry

def _to_blender(x, y, z):
    return (x, -z, y)


def boxes_object(name, boxes, coll):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    for (x0, y0, z0, x1, y1, z1, _c) in boxes:
        res = bmesh.ops.create_cube(bm, size=1.0)
        for v in res["verts"]:
            lx, ly, lz = v.co  # -0.5..0.5 in Blender space (x, y=depth, z=up)
            rx = (x0 + x1) / 2 + lx * (x1 - x0)
            ry = (y0 + y1) / 2 + lz * (y1 - y0)
            rz = (z0 + z1) / 2 - ly * (z1 - z0)
            v.co = _to_blender(rx, ry, rz)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


def _apply_all(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = bpy.data.meshes.new_from_object(ev)
    old = ob.data
    ob.modifiers.clear()
    ob.data = me
    bpy.data.meshes.remove(old)


def deform(ob, seed, disp=1.3, voxel=0.7, faces=900, noise=4.0):
    """Fuse, deform and facet the blocky shape."""
    m = ob.modifiers.new("fuse", "REMESH")
    m.mode = "VOXEL"
    m.voxel_size = voxel
    _apply_all(ob)
    # offset the noise per asset so every rock deforms differently
    rnd = random.Random(seed)
    off = (rnd.uniform(-500, 500), rnd.uniform(-500, 500), rnd.uniform(-500, 500))
    ob.location = off
    for strength, size, kind in ((disp, noise, "CLOUDS"), (disp * 0.35, noise * 0.35, "CLOUDS")):
        tex = bpy.data.textures.new("n%d_%s" % (seed, size), kind)
        tex.noise_scale = size
        tex.noise_depth = 1
        d = ob.modifiers.new("deform", "DISPLACE")
        d.texture = tex
        d.texture_coords = "GLOBAL"
        d.strength = strength
        d.mid_level = 0.5
        _apply_all(ob)
    ob.location = (0, 0, 0)
    n = len(ob.data.polygons)
    dec = ob.modifiers.new("facets", "DECIMATE")
    dec.decimate_type = "COLLAPSE"
    dec.ratio = min(1.0, faces / max(1, n))
    dec.use_collapse_triangulate = True
    _apply_all(ob)
    for p in ob.data.polygons:
        p.use_smooth = False


def box_uv(me):
    """Box-projected UVs at a fixed world scale so studs line up across faces."""
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    uv = me.uv_layers.active.data
    s = 1.0 / STUDS_PER_TILE
    for p in me.polygons:
        nx, ny, nz = (abs(c) for c in p.normal)
        for li in p.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            if nz >= nx and nz >= ny:
                uv[li].uv = (co.x * s, co.y * s)
            elif nx >= ny:
                uv[li].uv = (co.y * s, co.z * s)
            else:
                uv[li].uv = (co.x * s, co.z * s)


def split_top(ob, top_dot=0.55):
    """Split faces that point up into their own object (sand / grass / moss tops)."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.normal_update()
    up = [f for f in bm.faces if f.normal.z > top_dot]
    if not up or len(up) == len(bm.faces):
        bm.free()
        return None
    top_bm = bmesh.new()
    vmap = {}
    for f in up:
        vs = []
        for v in f.verts:
            if v.index not in vmap:
                vmap[v.index] = top_bm.verts.new(v.co)
            vs.append(vmap[v.index])
        top_bm.faces.new(vs)
    bmesh.ops.delete(bm, geom=up, context="FACES_ONLY")
    bmesh.ops.delete(bm, geom=[e for e in bm.edges if not e.link_faces], context="EDGES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    bm.to_mesh(ob.data)
    bm.free()
    me = bpy.data.meshes.new(ob.name.replace("_Rock", "_Top"))
    top_bm.to_mesh(me)
    top_bm.free()
    top = bpy.data.objects.new(me.name, me)
    for c in ob.users_collection:
        c.objects.link(top)
    for p in me.polygons:
        p.use_smooth = False
    return top


def seaweed_object(name, seed, coll):
    """Wavy lobed ribbons, like the kelp in the reference."""
    rng = random.Random(seed)
    bm = bmesh.new()
    strands = [(0, 0, 13, 0), (2.4, 1.0, 10, 1.3), (-2.0, 1.4, 8.5, 2.1), (0.6, -2.2, 11, 0.7),
               (-1.0, -1.2, 7, 2.8)]
    for sx, sz, h, ph in strands:
        yaw = rng.uniform(0, math.pi)
        steps = int(h / 0.7)
        prev = None
        for k in range(steps + 1):
            t = k / steps
            y = t * h
            sway = math.sin(y * 0.5 + ph) * 1.4 * (0.3 + t)
            lobe = 0.55 + 0.45 * abs(math.sin(y * 1.6 + ph))
            w = (2.4 - 1.6 * t) * lobe
            cx = sx + sway * math.cos(yaw)
            cz = sz + sway * math.sin(yaw)
            dx, dz = math.cos(yaw + math.pi / 2) * w / 2, math.sin(yaw + math.pi / 2) * w / 2
            a = bm.verts.new(_to_blender(cx - dx, y, cz - dz))
            b = bm.verts.new(_to_blender(cx + dx, y, cz + dz))
            if prev:
                bm.faces.new((prev[0], prev[1], b, a))
            prev = (a, b)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    sol = ob.modifiers.new("thick", "SOLIDIFY")
    sol.thickness = 0.35
    sol.offset = 0
    _apply_all(ob)
    for p in ob.data.polygons:
        p.use_smooth = False
    return ob


def build_rock(name, src, coll, tex_dir):
    """Returns (root_empty, [mesh objects]) for one MESH_SOURCES entry."""
    root = bpy.data.objects.new(name, None)
    coll.objects.link(root)
    parts = []
    if src.get("kind") == "seaweed":
        ob = seaweed_object(name + "_Rock", src["seed"], coll)
        parts.append((ob, src["rock"]))
    else:
        ob = boxes_object(name + "_Rock", src["boxes"], coll)
        deform(ob, src["seed"], disp=src.get("disp", 1.3), voxel=src.get("voxel", 0.7),
               faces=src.get("faces", 900), noise=src.get("noise", 4.0))
        top = split_top(ob) if src["top"] != src["rock"] else None
        parts.append((ob, src["rock"]))
        if top:
            parts.append((top, src["top"]))
    objs = []
    for ob, color in parts:
        box_uv(ob.data)
        ob.data.materials.clear()
        ob.data.materials.append(stud_material(color, tex_dir))
        ob.parent = root
        objs.append(ob)
    return root, objs
