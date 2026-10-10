"""Rebuild the original props (from rbxtool JSON) in Blender: like the weapons'
rbxscene.build_model, plus nested Models (Trapdoor flaps), SpecialMesh spheres
and MeshParts (drawn as a stand-in, since their meshes live on Roblox)."""
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


def handle_origin(model):
    h = next((c for c in model["children"] if c["name"] == "Handle"), None)
    return Vector(h["props"]["CFrame"]["CFrame"]["position"]) if h else Vector((0, 0, 0))


def _sphere_mesh(name, size):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=18, radius=0.5)
    bm.verts.ensure_lookup_table()
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return me


def _frustum_mesh(name, size):
    """Stand-in for an unknown MeshPart: a tapered octagonal block filling its size."""
    bm = bmesh.new()
    sx, sy, sz = size
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=24, radius1=0.5, radius2=0.36,
                          depth=1.0, matrix=Matrix.Rotation(-math.pi / 2, 4, "X"))
    for v in bm.verts:
        v.co = Vector((v.co.x * sx, v.co.y * sy, v.co.z * sz))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return me


def build_part(part, coll, name):
    p = part["props"]
    special = next((c for c in part.get("children", []) if c["class"] == "SpecialMesh"), None)
    size = p["Size"]["Vector3"]
    if special and special["props"].get("MeshType", {}).get("Enum") == 3:
        sc = special["props"].get("Scale", {}).get("Vector3", [1, 1, 1])
        o = bpy.data.objects.new(name, _sphere_mesh(name, [size[i] * sc[i] for i in range(3)]))
        coll.objects.link(o)
        return o
    if part["class"] == "MeshPart":
        o = bpy.data.objects.new(name, _frustum_mesh(name, size))
        coll.objects.link(o)
        return o
    return rs.build_geometry(part, coll, name)


def build_model(model, coll, origin=None, prefix=None, out=None):
    """Every visible part of the model (recursing into child Models), placed relative to
    `origin` (the Handle), as (object, part node) pairs."""
    out = [] if out is None else out
    origin = handle_origin(model) if origin is None else origin
    prefix = prefix or model["name"]
    for i, part in enumerate(model["children"]):
        if part["class"] == "Model":
            build_model(part, coll, origin, "%s_%s%d" % (prefix, part["name"], i), out)
            continue
        if "Size" not in part["props"]:
            continue
        p = part["props"]
        if p.get("Transparency", {}).get("Float32", 0) >= 0.99:
            continue
        o = build_part(part, coll, "%s_%s" % (prefix, part["name"]))
        m = Matrix.Translation(-origin) @ rs.cframe_matrix(p["CFrame"])
        o.matrix_world = rs.RB2BL @ m
        rs._bake(o)
        mat_name = rs.MATERIAL_NAMES.get(p.get("Material", {}).get("Enum"), "SmoothPlastic")
        rgb = p.get("Color", {}).get("Color3uint8", [200, 200, 200])
        o.data.materials.clear()
        o.data.materials.append(rs.roblox_material(mat_name, rgb, p.get("Transparency", {}).get("Float32", 0.0)))
        if mat_name == "Neon":
            rs.neon_no_bounce(o)
        for poly in o.data.polygons:
            poly.use_smooth = False
        out.append((o, part))
    return out


# ---------------------------------------------------------------- NPCs (R6 characters)

def _classic_head_mesh(name):
    """The classic R6 head: a rounded cylinder about 1.2 studs across."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=32, radius1=0.6, radius2=0.6, depth=1.2,
                          matrix=Matrix.Rotation(-math.pi / 2, 4, "X"))
    bmesh.ops.bevel(bm, geom=[e for e in bm.edges if abs(e.verts[0].co.y - e.verts[1].co.y) < 1e-6
                              and abs(abs(e.verts[0].co.y) - 0.6) < 1e-6],
                    offset=0.22, segments=4, affect="EDGES", profile=0.5)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return me


def build_npc(npc, coll):
    """Body parts + every outfit model of an NPC, relative to its HumanoidRootPart.
    Returns (object, node) pairs; the head's face decal is drawn as two eyes and a smile."""
    hrp = next(c for c in npc["children"] if c["name"] == "HumanoidRootPart")
    origin = Vector(hrp["props"]["CFrame"]["CFrame"]["position"])
    out = []
    for part in npc["children"]:
        if part["class"] != "Part" or part["props"].get("Transparency", {}).get("Float32", 0) >= 0.99:
            continue
        p = part["props"]
        name = "%s_%s" % (npc["name"], part["name"].replace(" ", ""))
        if part["name"] == "Head":
            o = bpy.data.objects.new(name, _classic_head_mesh(name))
            coll.objects.link(o)
        else:
            o = rs.build_geometry(part, coll, name)
        o.matrix_world = rs.RB2BL @ Matrix.Translation(-origin) @ rs.cframe_matrix(p["CFrame"])
        rs._bake(o)
        mat_name = rs.MATERIAL_NAMES.get(p.get("Material", {}).get("Enum"), "SmoothPlastic")
        o.data.materials.append(rs.roblox_material(mat_name, p["Color"]["Color3uint8"]))
        out.append((o, part))
        if part["name"] == "Head" and any(c["class"] == "Decal" for c in part.get("children", [])):
            # classic smile: eyes + mouth on the head's front (-Z in Roblox)
            bm = bmesh.new()
            for ex in (-0.2, 0.2):
                bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=0.07,
                                          matrix=Matrix.Translation((ex, 0.12, -0.58)) @ Matrix.Diagonal((0.8, 1.5, 0.4, 1)))
            for i in range(9):
                a = math.radians(200 + i * 17.5)
                bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=6, radius=0.035,
                                          matrix=Matrix.Translation((0.3 * math.cos(a), 0.02 + 0.3 * math.sin(a) + 0.1, -0.585)))
            me = bpy.data.meshes.new(name + "_face")
            bm.to_mesh(me)
            bm.free()
            f = bpy.data.objects.new(name + "_face", me)
            coll.objects.link(f)
            f.matrix_world = rs.RB2BL @ Matrix.Translation(-origin) @ rs.cframe_matrix(p["CFrame"])
            rs._bake(f)
            f.data.materials.append(rs.roblox_material("SmoothPlastic", (25, 25, 30)))
            out.append((f, part))
    outfit = next((c for c in npc["children"] if c["name"] == "Outfit"), None)
    for m in (outfit or {}).get("children", []):
        out += build_model(m, coll, origin, "%s_%s" % (npc["name"], m["name"]))
    return out
