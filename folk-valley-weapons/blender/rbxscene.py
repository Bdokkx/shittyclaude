"""Shared Blender helpers: Roblox <-> Blender axes, Roblox-like preview materials,
render setup with Neon bloom, and a rebuilder for models stored in rbxtool JSON
(Parts, WedgeParts and Unions rebuilt from their ChildData2 source parts).

Roblox space is Y up. Blender space is Z up. A point (x, y, z) in Roblox is
(x, -z, y) in Blender, so a weapon pointing along Roblox +Y points along Blender +Z,
its +X edge stays +X and its thin Roblox Z side is Blender -Y.
"""
import base64
import json
import math
import os
import subprocess
import tempfile

import bpy  # noqa: I001  (bpy must load before bmesh / mathutils)
import bmesh
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RBXTOOL = os.environ.get("RBXTOOL", os.path.join(ROOT, "tools", "rbxtool", "target", "release", "rbxtool"))

# Roblox space -> Blender space
RB2BL = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))


def srgb_to_linear(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def lin(rgb):
    return tuple(srgb_to_linear(v) for v in rgb[:3]) + (1.0,)


# ---------------------------------------------------------------- materials

_mat_cache = {}


def roblox_material(material, rgb, transparency=0.0):
    """A Blender material that looks roughly like the Roblox material + colour."""
    key = (material, tuple(rgb), round(transparency, 3))
    if key in _mat_cache:
        return _mat_cache[key]
    m = bpy.data.materials.new("%s_%02x%02x%02x" % (material, *rgb[:3]))
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    col = lin(rgb)
    bsdf.inputs["Base Color"].default_value = col
    rough, metal, spec = 0.5, 0.0, 0.35
    if material in ("SmoothPlastic", "Plastic"):
        rough, spec = 0.42, 0.4
    elif material == "Metal":
        rough, metal = 0.32, 0.8
    elif material in ("Fabric",):
        rough, spec = 0.95, 0.15
    elif material in ("Wood", "WoodPlanks"):
        rough, spec = 0.75, 0.2
    elif material in ("Slate", "Basalt", "Rock", "Granite"):
        rough, spec = 0.85, 0.2
    elif material == "Ice":
        rough, spec = 0.12, 0.6
    elif material == "Glass":
        rough, spec = 0.05, 0.6
    elif material == "Foil":
        rough, metal = 0.2, 0.9
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = spec
    if material in ("Wood", "WoodPlanks"):
        # faint grain so the preview reads like Roblox Wood
        tex = nt.nodes.new("ShaderNodeTexWave")
        tex.inputs["Scale"].default_value = 2.5
        tex.inputs["Distortion"].default_value = 6.0
        tex.inputs["Detail"].default_value = 3.0
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.inputs["Factor"].default_value = 0.18
        mix.inputs["A"].default_value = col
        mix.inputs["B"].default_value = tuple(v * 0.55 for v in col[:3]) + (1,)
        nt.links.new(tex.outputs["Fac"], mix.inputs["Factor"])
        mult = nt.nodes.new("ShaderNodeMath")
        mult.operation = "MULTIPLY"
        mult.inputs[1].default_value = 0.12
        nt.links.new(tex.outputs["Fac"], mult.inputs[0])
        nt.links.new(mult.outputs[0], mix.inputs["Factor"])
        nt.links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
    if material == "Neon":
        # Roblox Neon is unlit: flat bright colour plus a glow, no shading
        bsdf.inputs["Base Color"].default_value = (0, 0, 0, 1)
        bsdf.inputs["Emission Color"].default_value = col
        bsdf.inputs["Emission Strength"].default_value = 1.35
        bsdf.inputs["Roughness"].default_value = 1.0
        if "Specular IOR Level" in bsdf.inputs:
            bsdf.inputs["Specular IOR Level"].default_value = 0.0
    alpha = 1.0 - transparency
    if material == "Glass":
        alpha = min(alpha, 0.55)
    elif material == "Ice":
        alpha = min(alpha, 0.85)
    if alpha < 0.999:
        bsdf.inputs["Alpha"].default_value = alpha
        try:
            m.surface_render_method = "BLENDED"
        except Exception:
            pass
    _mat_cache[key] = m
    return m


# ---------------------------------------------------------------- primitive geometry (Roblox local space)

def _box(bm, hx, hy, hz):
    vs = [bm.verts.new((x, y, z)) for x in (-hx, hx) for y in (-hy, hy) for z in (-hz, hz)]
    # index = xi*4 + yi*2 + zi
    faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    for f in faces:
        bm.faces.new([vs[i] for i in f])


def _wedge(bm, hx, hy, hz):
    # bottom is full, the tall face is at +Z, the slope faces -Z / up
    a = bm.verts.new((-hx, -hy, -hz)); b = bm.verts.new((hx, -hy, -hz))
    c = bm.verts.new((hx, -hy, hz)); d = bm.verts.new((-hx, -hy, hz))
    e = bm.verts.new((-hx, hy, hz)); f = bm.verts.new((hx, hy, hz))
    for face in ((a, d, c, b), (d, e, f, c), (a, b, f, e), (a, e, d), (b, c, f)):
        bm.faces.new(face)


def _cylinder_x(bm, length, radius, segs=24):
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segs,
                          radius1=radius, radius2=radius, depth=length,
                          matrix=Matrix.Rotation(math.pi / 2, 4, "Y"))


def _ball(bm, radius):
    bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=14, radius=radius)


def primitive_mesh(node, name):
    p = node["props"]
    sx, sy, sz = p["Size"]["Vector3"]
    bm = bmesh.new()
    cls = node["class"]
    shape = p.get("Shape", {}).get("Enum", 1)
    if cls == "WedgePart" or (cls == "Part" and shape == 3):
        _wedge(bm, sx / 2, sy / 2, sz / 2)
    elif cls == "Part" and shape == 2:
        _cylinder_x(bm, sx, min(sy, sz) / 2)
    elif cls == "Part" and shape == 0:
        _ball(bm, min(sx, sy, sz) / 2)
    else:
        _box(bm, sx / 2, sy / 2, sz / 2)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return me


def cframe_matrix(cf):
    c = cf["CFrame"] if "CFrame" in cf else cf
    r = c["orientation"]
    p = c["position"]
    return Matrix(((r[0][0], r[0][1], r[0][2], p[0]),
                   (r[1][0], r[1][1], r[1][2], p[1]),
                   (r[2][0], r[2][1], r[2][2], p[2]),
                   (0, 0, 0, 1)))


# ---------------------------------------------------------------- rbxm JSON

def dump_rbxm(path):
    out = tempfile.mktemp(suffix=".json")
    subprocess.run([RBXTOOL, "dump", path, out], check=True)
    with open(out) as f:
        data = json.load(f)
    os.remove(out)
    return data


def _child_data(node):
    blob = node["props"].get("ChildData2", {}).get("SharedString")
    if not blob:
        return []
    raw = base64.b64decode(blob)
    tmp = tempfile.mktemp(suffix=".rbxm")
    with open(tmp, "wb") as f:
        f.write(raw)
    try:
        return dump_rbxm(tmp)
    finally:
        os.remove(tmp)


def _link(obj, coll):
    coll.objects.link(obj)
    return obj


def _boolean(target, other, op):
    mod = target.modifiers.new("bool", "BOOLEAN")
    mod.operation = op
    mod.solver = "EXACT"
    mod.object = other
    try:
        mod.use_self = True
    except Exception:
        pass
    with bpy.context.temp_override(object=target, active_object=target, selected_objects=[target]):
        bpy.ops.object.modifier_apply(modifier=mod.name)


def _join(objs, name):
    if len(objs) == 1:
        objs[0].name = name
        return objs[0]
    with bpy.context.temp_override(active_object=objs[0], object=objs[0], selected_objects=objs,
                                   selected_editable_objects=objs):
        bpy.ops.object.join()
    objs[0].name = name
    return objs[0]


def _bake(obj):
    obj.data.transform(obj.matrix_world)
    obj.matrix_world = Matrix.Identity(4)


def build_geometry(node, coll, name):
    """Return one Blender object holding this node's geometry, in the node's own
    local space (centred like Roblox: at the part's CFrame)."""
    cls = node["class"]
    if cls in ("Part", "WedgePart", "TrussPart", "CornerWedgePart"):
        me = primitive_mesh(node, name)
        return _link(bpy.data.objects.new(name, me), coll)
    # CSG: rebuild from the source parts in the union's construction frame
    kids = _child_data(node)
    pos, neg = [], []
    for i, k in enumerate(kids):
        if k["class"] not in ("Part", "WedgePart", "UnionOperation", "IntersectOperation", "NegateOperation",
                              "CornerWedgePart", "TrussPart"):
            continue
        o = build_geometry(k, coll, "%s_%d" % (name, i))
        o.matrix_world = cframe_matrix(k["props"]["CFrame"]) @ o.matrix_world
        _bake(o)
        (neg if k["class"] == "NegateOperation" else pos).append(o)
    if not pos:
        return _link(bpy.data.objects.new(name, bpy.data.meshes.new(name)), coll)
    if cls == "IntersectOperation":
        res = pos[0]
        for o in pos[1:]:
            _boolean(res, o, "INTERSECT")
            bpy.data.objects.remove(o)
    else:
        res = _join(pos, name)
    for o in neg:
        _boolean(res, o, "DIFFERENCE")
        bpy.data.objects.remove(o)
    # Union children are stored relative to the union's own CFrame (no recentring).
    # A resized union scales about that origin by Size / InitialSize.
    size = node["props"].get("Size", {}).get("Vector3")
    init = node["props"].get("InitialSize", {}).get("Vector3")
    if size and init:
        sc = [size[i] / init[i] if init[i] > 1e-6 else 1.0 for i in range(3)]
        if any(abs(v - 1) > 1e-4 for v in sc):
            res.data.transform(Matrix.Diagonal((*sc, 1)))
    res.name = name
    return res


def build_model(model, coll, origin=None, skip=("Handle",)):
    """Build every visible part of a Roblox Model into Blender, placed relative to
    `origin` (Roblox world position that should land on Blender's origin)."""
    objs = []
    handle = next((c for c in model["children"] if c["name"] == "Handle"), None)
    if origin is None and handle:
        origin = Vector(handle["props"]["CFrame"]["CFrame"]["position"])
    origin = origin or Vector((0, 0, 0))
    for part in model["children"]:
        if part["name"] in skip or "Size" not in part["props"]:
            continue
        p = part["props"]
        if p.get("Transparency", {}).get("Float32", 0) >= 0.99:
            continue
        o = build_geometry(part, coll, model["name"] + "_" + part["name"])
        m = cframe_matrix(p["CFrame"])
        m = Matrix.Translation(-origin) @ m
        o.matrix_world = RB2BL @ m
        _bake(o)
        mat_name = MATERIAL_NAMES.get(p.get("Material", {}).get("Enum"), "SmoothPlastic")
        rgb = p.get("Color", {}).get("Color3uint8", [200, 200, 200])
        o.data.materials.clear()
        o.data.materials.append(roblox_material(mat_name, rgb, p.get("Transparency", {}).get("Float32", 0.0)))
        if mat_name == "Neon":
            neon_no_bounce(o)
        for poly in o.data.polygons:
            poly.use_smooth = False
        objs.append(o)
    return objs


MATERIAL_NAMES = {256: "Plastic", 272: "SmoothPlastic", 288: "Neon", 512: "Wood", 528: "WoodPlanks",
                  784: "Marble", 788: "Basalt", 800: "Slate", 816: "Concrete", 832: "Granite",
                  848: "Brick", 864: "Pebble", 880: "Cobblestone", 896: "Rock", 1040: "CorrodedMetal",
                  1056: "DiamondPlate", 1072: "Foil", 1088: "Metal", 1312: "Fabric", 1536: "Ice",
                  1552: "Glacier", 1568: "Glass", 1584: "ForceField"}


# ---------------------------------------------------------------- scene / render

def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _mat_cache.clear()
    return bpy.context.scene


def _sun(scene, name, energy, from_dir, angle=6.0, color=(1.0, 0.97, 0.92)):
    d = bpy.data.lights.new(name, "SUN")
    d.energy = energy
    d.angle = math.radians(angle)
    d.color = color
    o = bpy.data.objects.new(name, d)
    # a sun shines along its local -Z: point that away from `from_dir`
    o.rotation_euler = (-Vector(from_dir)).to_track_quat("-Z", "Y").to_euler()
    scene.collection.objects.link(o)
    return o


def setup_world(scene, color=(0.80, 0.87, 1.0), strength=0.55, key=4.0, key_from=(-0.75, -0.55, 0.55),
                fill=0.9, fill_from=(0.8, -0.3, 0.2), rim=2.4, rim_from=(0.35, 0.9, 0.5)):
    """Sky ambient + a key light from the upper left (shows blade ridges), a cool
    fill from the right and a rim light from behind that picks out edges."""
    world = bpy.data.worlds.new("Sky")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (*color, 1)
    bg.inputs[1].default_value = strength
    _sun(scene, "Key", key, key_from)
    _sun(scene, "Fill", fill, fill_from, angle=30, color=(0.85, 0.9, 1.0))
    _sun(scene, "Rim", rim, rim_from, angle=5)


def setup_render(scene, w, h, samples=64, bloom=True, transparent=False, exposure=0.0):
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.cycles.max_bounces = 6
    scene.cycles.transparent_max_bounces = 12
    scene.cycles.use_denoising = True
    try:
        scene.cycles.denoiser = "OPENIMAGEDENOISE"
    except Exception:
        pass
    scene.render.resolution_x = w
    scene.render.resolution_y = h
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = transparent
    # Khronos PBR Neutral keeps base colours true while rolling off highlights,
    # so pale wood and Neon don't clip to flat white.
    scene.view_settings.view_transform = "Khronos PBR Neutral"
    scene.view_settings.look = "None"
    scene.view_settings.exposure = exposure
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA" if transparent else "RGB"
    if bloom:
        add_bloom(scene)


def add_bloom(scene, threshold=0.85, size=7, mix=0.0, strength=0.75):
    scene.render.compositor_device = "CPU"   # no GPU / EGL in headless runs
    tree = bpy.data.node_groups.new("Bloom", "CompositorNodeTree")
    scene.compositing_node_group = tree
    rl = tree.nodes.new("CompositorNodeRLayers")
    glare = tree.nodes.new("CompositorNodeGlare")
    out = tree.nodes.new("NodeGroupOutput")
    tree.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    # Blender 5.x exposes the glare settings as inputs
    def setin(name, value):
        if name in glare.inputs:
            try:
                glare.inputs[name].default_value = value
            except Exception:
                pass
    try:
        glare.inputs["Type"].default_value = "Bloom"
    except Exception:
        try:
            glare.glare_type = "BLOOM"
        except Exception:
            pass
    setin("Threshold", threshold)
    setin("Strength", strength)
    setin("Size", 0.6)
    tree.links.new(rl.outputs["Image"], glare.inputs["Image"])
    tree.links.new(glare.outputs["Image"], out.inputs[0])


def add_camera(scene, loc, target, lens=50, ortho=None, name="Camera"):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.clip_start = 0.05
    cd.clip_end = 2000
    if ortho:
        cd.type = "ORTHO"
        cd.ortho_scale = ortho
    cam = bpy.data.objects.new(name, cd)
    scene.collection.objects.link(cam)
    look_at(cam, loc, target)
    scene.camera = cam
    return cam


def look_at(cam, loc, target):
    cam.location = Vector(loc)
    d = Vector(target) - Vector(loc)
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def render(scene, path):
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return path


def bounds(objs):
    vs = []
    for o in objs:
        for v in o.data.vertices:
            vs.append(o.matrix_world @ v.co)
    lo = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
    hi = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
    return lo, hi


def neon_no_bounce(obj):
    """Neon in Roblox doesn't light or reflect in other surfaces."""
    for attr in ("visible_diffuse", "visible_glossy", "visible_transmission", "visible_shadow"):
        if hasattr(obj, attr):
            setattr(obj, attr, False)
