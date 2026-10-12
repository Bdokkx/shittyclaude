"""Blender side of the map: turn a Scene into meshes (grouped by look), give Plastic
tops a stud bump, add the scene's lights, and render. Roblox (x, y, z) is Blender
(x, -z, y)."""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "folk-valley-weapons", "blender"))

import bpy  # noqa: E402,I001
import numpy as np  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import rbxscene as rs  # noqa: E402
import spsgeo as G  # noqa: E402


def rb2bl(p):
    p = np.asarray(p, float)
    return np.stack((p[..., 0], -p[..., 2], p[..., 1]), -1)


# ---------------------------------------------------------------- primitive geometry (local space)

_PRIM = {}


def _prim(shape, size):
    sx, sy, sz = size
    if shape == "Block":
        g = G.box(sx, sy, sz)
    elif shape == "Wedge":
        g = G.wedge(sx, sy, sz)
    elif shape == "Cylinder":
        g = G.cyl(min(sy, sz) / 2, sx, 24, "x", phase=0.0)
    else:
        g = G.sphere(min(sx, sy, sz) / 2, 20, 12)
    return g


# ---------------------------------------------------------------- materials

_mats = {}


def stud_group():
    if "StudBump" in bpy.data.node_groups:
        return bpy.data.node_groups["StudBump"]
    ng = bpy.data.node_groups.new("StudBump", "ShaderNodeTree")
    ng.interface.new_socket("Normal", in_out="OUTPUT", socket_type="NodeSocketVector")
    ng.interface.new_socket("Shade", in_out="OUTPUT", socket_type="NodeSocketFloat")
    nodes, links = ng.nodes, ng.links
    out = nodes.new("NodeGroupOutput")
    uv = nodes.new("ShaderNodeUVMap")
    uv.uv_map = "studs"
    sep = nodes.new("ShaderNodeSeparateXYZ")
    links.new(uv.outputs["UV"], sep.inputs[0])
    comps = []
    for k in ("X", "Y"):
        fr = nodes.new("ShaderNodeMath")
        fr.operation = "FRACT"
        links.new(sep.outputs[k], fr.inputs[0])
        sub = nodes.new("ShaderNodeMath")
        sub.operation = "SUBTRACT"
        sub.inputs[1].default_value = 0.5
        links.new(fr.outputs[0], sub.inputs[0])
        comps.append(sub)
    comb = nodes.new("ShaderNodeCombineXYZ")
    links.new(comps[0].outputs[0], comb.inputs["X"])
    links.new(comps[1].outputs[0], comb.inputs["Y"])
    ln = nodes.new("ShaderNodeVectorMath")
    ln.operation = "LENGTH"
    links.new(comb.outputs[0], ln.inputs[0])
    ramp = nodes.new("ShaderNodeMapRange")
    ramp.inputs["From Min"].default_value = 0.31
    ramp.inputs["From Max"].default_value = 0.27
    links.new(ln.outputs["Value"], ramp.inputs["Value"])
    attr = nodes.new("ShaderNodeAttribute")
    attr.attribute_name = "stud"
    attr.attribute_type = "GEOMETRY"
    mul = nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    links.new(ramp.outputs["Result"], mul.inputs[0])
    links.new(attr.outputs["Fac"], mul.inputs[1])
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.7
    bump.inputs["Distance"].default_value = 0.08
    links.new(mul.outputs[0], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], out.inputs["Normal"])
    # a faint ring darkening round each stud base
    ring = nodes.new("ShaderNodeMapRange")
    ring.inputs["From Min"].default_value = 0.27
    ring.inputs["From Max"].default_value = 0.33
    links.new(ln.outputs["Value"], ring.inputs["Value"])
    tri = nodes.new("ShaderNodeMath")
    tri.operation = "PINGPONG"
    tri.inputs[1].default_value = 0.5
    links.new(ring.outputs["Result"], tri.inputs[0])
    m2 = nodes.new("ShaderNodeMath")
    m2.operation = "MULTIPLY"
    links.new(tri.outputs[0], m2.inputs[0])
    links.new(attr.outputs["Fac"], m2.inputs[1])
    links.new(m2.outputs[0], out.inputs["Shade"])
    return ng


def material(color, mat, transparency, emit_scale=1.0):
    key = (tuple(color), mat, round(transparency, 3), emit_scale)
    if key in _mats:
        return _mats[key]
    m = bpy.data.materials.new("%s_%02x%02x%02x" % (mat, *color))
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    col = rs.lin(color)
    rough, metal, spec = 0.55, 0.0, 0.35
    if mat == "SmoothPlastic":
        rough, spec = 0.32, 0.45
    elif mat == "Metal":
        rough, metal = 0.35, 0.75
    elif mat in ("Wood", "WoodPlanks"):
        rough, spec = 0.75, 0.2
    elif mat == "Glass":
        rough, spec = 0.05, 0.6
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = spec
    if mat == "Neon":
        bsdf.inputs["Base Color"].default_value = (0, 0, 0, 1)
        bsdf.inputs["Emission Color"].default_value = col
        bsdf.inputs["Emission Strength"].default_value = 2.2 * emit_scale
        bsdf.inputs["Roughness"].default_value = 1.0
    else:
        # base colour, slightly darkened in the gap round each stud
        sg = nt.nodes.new("ShaderNodeGroup")
        sg.node_tree = stud_group()
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.inputs["A"].default_value = col
        mix.inputs["B"].default_value = tuple(c * 0.72 for c in col[:3]) + (1,)
        nt.links.new(sg.outputs["Shade"], mix.inputs["Factor"])
        nt.links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
        nt.links.new(sg.outputs["Normal"], bsdf.inputs["Normal"])
    alpha = 1.0 - transparency
    if mat == "Glass":
        alpha = min(alpha, 0.5)
    if alpha < 0.999:
        bsdf.inputs["Alpha"].default_value = alpha
        try:
            m.surface_render_method = "BLENDED"
        except Exception:
            pass
    _mats[key] = m
    return m


def reset():
    _mats.clear()
    scene = rs.reset_scene()
    scene.render.use_persistent_data = True
    return scene


# ---------------------------------------------------------------- scene -> Blender

class Builder:
    """Accumulates world-space faces per look, then makes one Blender object per look."""

    def __init__(self):
        self.groups = {}

    def add(self, key, verts_rb, faces, uvs=None, stud=None, smooth=False):
        g = self.groups.setdefault(key, {"v": [], "f": [], "uv": [], "stud": [], "smooth": []})
        base = sum(len(v) for v in g["v"])
        g["v"].append(np.asarray(verts_rb, float))
        for k, f in enumerate(faces):
            g["f"].append(tuple(i + base for i in f))
            g["uv"].append(uvs[k] if uvs is not None else [(0.0, 0.0)] * len(f))
            g["stud"].append(stud[k] if stud is not None else 0.0)
            g["smooth"].append(smooth)

    def build(self, coll, name_prefix="M", emit_scale=1.0, skip_neon_bounce=True):
        objs = []
        for key, g in self.groups.items():
            color, mat, tr = key
            V = rb2bl(np.vstack(g["v"]))
            me = bpy.data.meshes.new("%s_%s" % (name_prefix, mat))
            me.from_pydata(V.tolist(), [], g["f"])
            me.update()
            uvl = me.uv_layers.new(name="studs")
            loops = []
            for uv in g["uv"]:
                loops.extend(uv)
            uvl.data.foreach_set("uv", np.asarray(loops, float).ravel())
            at = me.attributes.new("stud", "FLOAT", "FACE")
            at.data.foreach_set("value", np.asarray(g["stud"], float))
            me.polygons.foreach_set("use_smooth", np.asarray(g["smooth"], bool))
            me.materials.append(material(color, mat, tr, emit_scale))
            ob = bpy.data.objects.new(me.name, me)
            coll.objects.link(ob)
            if mat == "Neon" and skip_neon_bounce:
                rs.neon_no_bounce(ob)
            objs.append(ob)
        return objs


def add_part(b, n, show_hidden=False):
    p = n.p
    if p["transparency"] >= 0.99 and not show_hidden:
        return
    g = _prim(p["shape"], p["size"])
    V = np.array(g.v)
    W = (p["cf"].R @ V.T).T + p["cf"].p
    sx, sy, sz = p["size"]
    uvs, stud = [], []
    for f in g.f:
        if p["shape"] == "Block":
            uvs.append([(V[i][0] + sx / 2, V[i][2] + sz / 2) for i in f])
            fv = V[list(f)]
            top = np.all(np.abs(fv[:, 1] - sy / 2) < 1e-6)
            stud.append(1.0 if (top and p["surfaces"] == "studs") else 0.0)
        else:
            uvs.append([(0.0, 0.0)] * len(f))
            stud.append(0.0)
    smooth = p["shape"] in ("Cylinder", "Ball")
    if smooth and p["shape"] == "Cylinder":
        # caps flat, sides smooth: split into two adds
        side = [k for k, f in enumerate(g.f) if len(f) == 4]
        caps = [k for k, f in enumerate(g.f) if len(f) != 4]
        key = (p["color"], p["material"], p["transparency"])
        b.add(key, W, [g.f[k] for k in side], [uvs[k] for k in side], [0.0] * len(side), smooth=True)
        b.add(key, W, [g.f[k] for k in caps], [uvs[k] for k in caps], [0.0] * len(caps), smooth=False)
        return
    b.add((p["color"], p["material"], p["transparency"]), W, g.f, uvs, stud, smooth=smooth)


def add_mesh(b, sc, n):
    p = n.p
    if p["transparency"] >= 0.99:
        return
    g = sc.geoms[p["mesh"]]
    V = np.array(g.v)
    W = (p["cf"].R @ V.T).T + p["cf"].p
    b.add((p["color"], p["material"], p["transparency"]), W, g.f)


def realize(sc, coll, filter_fn=None, emit_scale=1.0):
    b = Builder()
    for n in sc.nodes(("Part", "MeshPart")):
        if filter_fn and not filter_fn(n):
            continue
        if n.kind == "Part":
            add_part(b, n)
        else:
            add_mesh(b, sc, n)
    return b.build(coll, emit_scale=emit_scale)


def add_lights(sc, coll, scale=1.0, filter_fn=None, shadows=True):
    out = []
    for n in sc.nodes("Light"):
        part = n.parent
        if filter_fn and not filter_fn(part):
            continue
        p = n.p
        if not p["enabled"]:
            continue
        pos = rb2bl(part.p["cf"].p)
        col = [c / 255 for c in p["color"]]
        if p["cls"] == "PointLight":
            ld = bpy.data.lights.new(n.name, "POINT")
            ld.energy = p["brightness"] * p["range"] ** 2 * 1.6 * scale
            ld.shadow_soft_size = 0.4
        elif p["cls"] == "SpotLight":
            ld = bpy.data.lights.new(n.name, "SPOT")
            ld.energy = p["brightness"] * p["range"] ** 2 * 2.5 * scale
            ld.spot_size = math.radians(p["angle"] or 90)
        else:
            ld = bpy.data.lights.new(n.name, "AREA")
            ld.energy = p["brightness"] * p["range"] ** 2 * 0.8 * scale
            ld.size = 2.0
        ld.color = col
        ld.use_shadow = shadows and bool(p["shadows"])
        ob = bpy.data.objects.new(n.name, ld)
        ob.location = Vector(pos)
        if p["cls"] != "PointLight":
            face = p["face"] or "Bottom"
            d = {"Bottom": (0, 0, -1), "Top": (0, 0, 1), "Front": (0, 1, 0), "Back": (0, -1, 0),
                 "Left": (-1, 0, 0), "Right": (1, 0, 0)}[face]
            ob.rotation_euler = Vector(d).to_track_quat("-Z", "Y").to_euler()
        coll.objects.link(ob)
        out.append(ob)
    return out


def point_light(coll, pos_rb, energy, color=(1, 0.85, 0.65), size=0.5, name="Lamp"):
    ld = bpy.data.lights.new(name, "POINT")
    ld.energy = energy
    ld.color = color
    ld.shadow_soft_size = size
    ob = bpy.data.objects.new(name, ld)
    ob.location = Vector(rb2bl(pos_rb))
    coll.objects.link(ob)
    return ob


def camera(scene, pos_rb, target_rb, lens=30, ortho=None, name="Camera"):
    return rs.add_camera(scene, tuple(rb2bl(pos_rb)), tuple(rb2bl(target_rb)), lens=lens, ortho=ortho, name=name)


def night_world(scene, color=(0.06, 0.08, 0.12), strength=0.35, moon=0.35, moon_from=(-0.5, 0.7, 0.6)):
    world = bpy.data.worlds.new("Night")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (*color, 1)
    bg.inputs[1].default_value = strength
    d = bpy.data.lights.new("Moon", "SUN")
    d.energy = moon
    d.angle = math.radians(2)
    d.color = (0.62, 0.72, 1.0)
    o = bpy.data.objects.new("Moon", d)
    o.rotation_euler = (-Vector(rb2bl(moon_from))).to_track_quat("-Z", "Y").to_euler()
    scene.collection.objects.link(o)
    return world


def day_world(scene, strength=0.9):
    rs.setup_world(scene, strength=strength, key=3.0)


# ---------------------------------------------------------------- FBX for Studio

MARK_O = np.array((-12.0, 0.0, 0.0))     # Roblox space
MARK_STEP = 4.0


def _white():
    m = bpy.data.materials.get("White") or bpy.data.materials.new("White")
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (1, 1, 1, 1)
    bsdf.inputs["Roughness"].default_value = 0.5
    return m


def export_fbx(sc, path, axis="FV_Axis"):
    """One object per unique mesh (named exactly like the mesh, white material), laid out on
    a grid so the raw import is readable, plus the four <axis>O/X/Y/Z marker cubes."""
    white = _white()
    coll = bpy.data.collections.new("FBXExport")
    bpy.context.scene.collection.children.link(coll)
    names = list(sc.geoms)
    cols = int(math.ceil(math.sqrt(len(names))))
    objs = []
    x = z = row_d = 0.0
    for i, name in enumerate(names):
        g = sc.geoms[name]
        lo, hi = g.bbox()
        if i and i % cols == 0:
            x, z, row_d = 0.0, z + row_d, 0.0
        off = np.array((x - lo[0], -lo[1], z - lo[2]))
        V = rb2bl(np.array(g.v) + off)
        me = bpy.data.meshes.new(name)
        me.from_pydata(V.tolist(), [], [tuple(f) for f in g.f])
        me.update()
        me.materials.append(white)
        ob = bpy.data.objects.new(name, me)
        assert ob.name == name, (ob.name, name)
        coll.objects.link(ob)
        objs.append(ob)
        x += hi[0] - lo[0] + 3.0
        row_d = max(row_d, hi[2] - lo[2] + 3.0)
    for nm, d in ((axis + "O", (0, 0, 0)), (axis + "X", (MARK_STEP, 0, 0)), (axis + "Y", (0, MARK_STEP, 0)),
                  (axis + "Z", (0, 0, MARK_STEP))):
        g = G.box(0.25, 0.25, 0.25, MARK_O + np.array(d))
        me = bpy.data.meshes.new(nm)
        me.from_pydata(rb2bl(np.array(g.v)).tolist(), [], g.f)
        me.update()
        me.materials.append(white)
        ob = bpy.data.objects.new(nm, me)
        coll.objects.link(ob)
        objs.append(ob)
    bpy.ops.object.select_all(action="DESELECT")
    for ob in objs:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={"MESH"},
                             axis_forward="-Z", axis_up="Y", apply_unit_scale=True,
                             bake_space_transform=True, mesh_smooth_type="OFF",
                             use_mesh_modifiers=True, add_leaf_bones=False, path_mode="STRIP",
                             use_custom_props=False)
    print("exported", path, len(objs), "objects")
    return [o.name for o in objs]
