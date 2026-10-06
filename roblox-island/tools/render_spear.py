"""Render a spearfishing island (build/<Map>.json, written by spear/build.py) in Blender.

    blender -b -P tools/render_spear.py -- <repo-root> <Map> [--tier=3] [--stages=terrain,dock,...]
          [--views=dock,overhead,plaza] [--res=100] [--samples=48] [--suffix=]

Every Plastic face gets the same inset-stud texture at 1 square per stud (per-face UVs in stud units,
so tilted slabs keep the same stud size). Neon glows, Glass is clear tinted water/ice.
"""
import json
import math
import os
import sys

import bpy
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1:]
ROOT, MAP = os.path.abspath(argv[0]), argv[1]
OPTS = dict(a[2:].split("=", 1) for a in argv[2:] if a.startswith("--") and "=" in a)
TIER = int(OPTS.get("tier", 3))
STAGES = set(OPTS["stages"].split(",")) if "stages" in OPTS else None
VIEWS = OPTS["views"].split(",") if "views" in OPTS else None
RES = int(OPTS.get("res", 100))
SAMPLES = int(OPTS.get("samples", 48))
SUFFIX = OPTS.get("suffix", "")
OUT = os.path.join(ROOT, "previews", "spear")
os.makedirs(OUT, exist_ok=True)

data = json.load(open(os.path.join(ROOT, "build", MAP + ".json")))


BEAM = OPTS.get("beam", "0") == "1"


def visible(p):
    if p.get("name") == "LighthouseBeam" and not BEAM:
        return False          # the beam spins in game; in a still it reads as a stick
    if STAGES is not None and p["stage"] not in STAGES:
        return False
    t = p["tier"]
    return t == 0 or (t == 1 and TIER == 1) or (t == 2 and TIER >= 2) or (t == 3 and TIER >= 3)


def srgb_to_lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_lin(h):
    h = h.lstrip("#")
    return tuple(srgb_to_lin(int(h[i:i + 2], 16)) for i in (0, 2, 4))


def rb(v):  # Roblox (x, y-up, z) -> Blender (x, -z, y)
    return (v[0], -v[2], v[1])


# ---------------------------------------------------------------- scene
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = SAMPLES
scene.cycles.use_denoising = False
scene.cycles.max_bounces = 4
scene.cycles.transparent_max_bounces = 8
scene.render.resolution_x, scene.render.resolution_y = 1600, 900
scene.render.resolution_percentage = RES
scene.view_settings.view_transform = "Standard"
scene.view_settings.exposure = -0.2
scene.render.film_transparent = False


def stud_image():
    """One stud: flat face with an inset square (dark top-left inner walls, light bottom-right)."""
    n = 64
    a = np.full((n, n), 0.93, np.float32)
    lo, hi, w = int(n * 0.27), int(n * 0.73), max(2, int(n * 0.07))
    yy, xx = np.mgrid[0:n, 0:n]
    inside = (xx >= lo) & (xx < hi) & (yy >= lo) & (yy < hi)
    a[inside] = 0.80
    a[inside & (xx < lo + w)] = 0.62           # left inner wall in shadow
    a[inside & (yy >= hi - w)] = 0.66          # top inner wall (image y is up)
    a[inside & (xx >= hi - w)] = 0.97          # lit walls
    a[inside & (yy < lo + w)] = 0.99
    a[(xx == 0) | (yy == 0)] *= 0.97           # faint seam between studs
    img = bpy.data.images.new("Stud", n, n, alpha=False)
    rgba = np.stack([a, a, a, np.ones_like(a)], axis=-1)
    img.pixels.foreach_set(rgba.ravel())
    img.pack()
    return img


STUD = stud_image()


def plastic_mat():
    m = bpy.data.materials.new("StudPlastic")
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = STUD
    tex.interpolation = "Linear"
    attr = nt.nodes.new("ShaderNodeVertexColor")
    attr.layer_name = "Col"
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 1.0
    nt.links.new(attr.outputs["Color"], mix.inputs[6])
    nt.links.new(tex.outputs["Color"], mix.inputs[7])
    nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.35
    nt.links.new(tex.outputs["Color"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Roughness"].default_value = 0.62
    bsdf.inputs["Specular IOR Level"].default_value = 0.35
    return m


def neon_mat():
    m = bpy.data.materials.new("Neon")
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    attr = nt.nodes.new("ShaderNodeVertexColor")
    attr.layer_name = "Col"
    nt.links.new(attr.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(attr.outputs["Color"], bsdf.inputs["Emission Color"])
    bsdf.inputs["Emission Strength"].default_value = 4.0
    return m


def beam_mat():
    m = bpy.data.materials.new("Beam")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    vc = nt.nodes.new("ShaderNodeVertexColor")
    vc.layer_name = "Col"
    nt.links.new(vc.outputs["Color"], em.inputs["Color"])
    em.inputs["Strength"].default_value = 2.5
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    mix.inputs["Fac"].default_value = 0.55
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    m.blend_method = "BLEND"
    return m


def glass_mat():
    m = bpy.data.materials.new("Glass")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    attr = nt.nodes.new("ShaderNodeVertexColor")
    attr.layer_name = "Col"
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    gl = nt.nodes.new("ShaderNodeBsdfPrincipled")
    gl.inputs["Roughness"].default_value = 0.1
    nt.links.new(attr.outputs["Color"], tr.inputs["Color"])
    nt.links.new(attr.outputs["Color"], gl.inputs["Base Color"])
    mix = nt.nodes.new("ShaderNodeMixShader")
    mix.inputs["Fac"].default_value = 0.55
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(gl.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    m.blend_method = "BLEND"
    return m


MATS = {"Plastic": plastic_mat(), "Neon": neon_mat(), "Glass": glass_mat(), "Beam": beam_mat()}

# box faces: (corner indices, u axis, v axis) in part-local corner space
CORNERS = [(-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1), (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)]
FACES = [((4, 5, 6, 7), 0, 1), ((1, 0, 3, 2), 0, 1), ((0, 4, 7, 3), 2, 1), ((5, 1, 2, 6), 2, 1),
         ((3, 7, 6, 2), 0, 2), ((0, 1, 5, 4), 0, 2)]


def build_meshes(parts):
    groups = {}
    for p in parts:
        key = "Beam" if p.get("transparency", 0) > 0.3 and p["mat"] == "Neon" else p["mat"]
        groups.setdefault(key if key in MATS else "Plastic", []).append(p)
    objs = []
    for matname, plist in groups.items():
        verts, faces, uvs, cols = [], [], [], []
        for pi, p in enumerate(plist):
            sx, sy, sz = p["size"]
            R = p["R"]
            jit = ((pi * 7919) % 13) * 0.0016          # separates coplanar faces (Cycles renders those black)
            sx, sy, sz = sx + jit, sy + jit, sz + jit
            base = len(verts)
            for c in CORNERS:
                lp = (c[0] * sx / 2, c[1] * sy / 2, c[2] * sz / 2)
                wp = [p["pos"][i] + sum(R[i][k] * lp[k] for k in range(3)) for i in range(3)]
                verts.append(rb(wp))
            col = hex_lin(p["color"]) + (1.0,)
            for idx, ua, va in FACES:
                faces.append(tuple(base + j for j in idx))
                for j in idx:
                    c = CORNERS[j]
                    half = (sx / 2, sy / 2, sz / 2)
                    uvs.append(((c[ua] + 1) * half[ua], (c[va] + 1) * half[va]))   # stud units, from the face corner
                    cols.append(col)
        me = bpy.data.meshes.new(MAP + "_" + matname)
        me.from_pydata(verts, [], faces)
        uv = me.uv_layers.new(name="UVMap")
        uv.data.foreach_set("uv", [x for t in uvs for x in t])
        ca = me.color_attributes.new("Col", "FLOAT_COLOR", "CORNER")
        ca.data.foreach_set("color", [x for t in cols for x in t])
        me.materials.append(MATS[matname])
        ob = bpy.data.objects.new(me.name, me)
        scene.collection.objects.link(ob)
        objs.append(ob)
    return objs


parts = [p for p in data["parts"] if visible(p)]
build_meshes(parts)

# signs
FACE_N = {"Front": (0, 0, -1), "Back": (0, 0, 1), "Left": (-1, 0, 0), "Right": (1, 0, 0), "Top": (0, 1, 0)}
for t in data["texts"]:
    p = data["parts"][t["part"]]
    if not visible(p):
        continue
    R, size = p["R"], p["size"]
    nl = FACE_N[t["face"]]
    ul = (0, 0, -1) if t["face"] == "Top" else (0, 1, 0)
    n = [sum(R[i][k] * nl[k] for k in range(3)) for i in range(3)]
    u = [sum(R[i][k] * ul[k] for k in range(3)) for i in range(3)]
    r = [u[1] * n[2] - u[2] * n[1], u[2] * n[0] - u[0] * n[2], u[0] * n[1] - u[1] * n[0]]
    depth = abs(sum(abs(nl[k]) * size[k] for k in range(3))) / 2 + 0.03
    center = [p["pos"][i] + n[i] * depth for i in range(3)]
    width = sum(abs((1 if t["face"] in ("Front", "Back", "Top") else 0) * (k == 0) + (t["face"] in ("Left", "Right")) * (k == 2)) * size[k] for k in range(3))
    height = size[2] if t["face"] == "Top" else size[1]
    cu = bpy.data.curves.new("txt", "FONT")
    cu.body = t["text"]
    cu.align_x, cu.align_y = "CENTER", "CENTER"
    cu.extrude = 0.02
    ob = bpy.data.objects.new("txt", cu)
    scene.collection.objects.link(ob)
    import mathutils
    M = mathutils.Matrix((rb(r), rb(u), rb(n))).transposed()
    ob.matrix_world = M.to_4x4()
    ob.location = rb(center)
    bpy.context.view_layer.update()
    dims = ob.dimensions
    s = min(width * 0.86 / max(dims.x, 1e-3), height * 0.7 / max(dims.y, 1e-3))
    ob.scale = (s, s, s)
    tm = bpy.data.materials.new("txt")
    tm.use_nodes = True
    tm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = hex_lin(t["color"]) + (1,)
    tm.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = hex_lin(t["color"]) + (1,)
    tm.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 0.4
    cu.materials.append(tm)

# lights
for p in parts:
    if p["light"]:
        kind, bright, rng, col = p["light"]
        ld = bpy.data.lights.new("L", "POINT")
        ld.energy = bright * rng * 14
        ld.color = hex_lin(col)
        ld.shadow_soft_size = 0.8
        lo = bpy.data.objects.new("L", ld)
        lo.location = rb(p["pos"])
        scene.collection.objects.link(lo)

# water: same ocean look as the original island renders (saturated blue, partly see-through)
x0, y0, z0, x1, y1, z1 = data["water"]
x0, z0, x1, z1 = x0 - 300, z0 - 300, x1 + 300, z1 + 300
water_col = hex_lin(data["preset"].get("WaterColor", "#2E9BE6"))
wme = bpy.data.meshes.new("Water")
wme.from_pydata([rb((x0, -0.05, z0)), rb((x1, -0.05, z0)), rb((x1, -0.05, z1)), rb((x0, -0.05, z1))], [],
                [(0, 1, 2, 3)])
wm = bpy.data.materials.new("Ocean")
wm.use_nodes = True
nt = wm.node_tree
bsdf = nt.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = tuple(c * 0.55 for c in water_col) + (1,)
bsdf.inputs["Roughness"].default_value = 0.08
transp = nt.nodes.new("ShaderNodeBsdfTransparent")
transp.inputs["Color"].default_value = tuple(min(1, 0.3 + c) for c in water_col) + (1,)
mix = nt.nodes.new("ShaderNodeMixShader")
mix.inputs["Fac"].default_value = 0.42
nt.links.new(transp.outputs[0], mix.inputs[1])
nt.links.new(bsdf.outputs[0], mix.inputs[2])
nt.links.new(mix.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
wm.blend_method = "BLEND"
wme.materials.append(wm)
scene.collection.objects.link(bpy.data.objects.new("Water", wme))
fme = bpy.data.meshes.new("Deep")
fme.from_pydata([rb((x0, -16, z0)), rb((x1, -16, z0)), rb((x1, -16, z1)), rb((x0, -16, z1))], [], [(0, 1, 2, 3)])
fm = bpy.data.materials.new("Deep")
fm.use_nodes = True
fm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = tuple(c * 0.5 for c in water_col) + (1,)
fme.materials.append(fm)
scene.collection.objects.link(bpy.data.objects.new("Deep", fme))

# sky + sun from the preset
pre = data["preset"]
world = bpy.data.worlds.new("Sky")
scene.world = world
world.use_nodes = True
wn = world.node_tree
bg = wn.nodes["Background"]
sky = hex_lin(pre.get("AtmosphereColor", "#C7DFFF"))
bg.inputs["Color"].default_value = tuple(0.5 * c + 0.5 * d for c, d in zip(sky, (0.55, 0.75, 1.0))) + (1,)
bg.inputs["Strength"].default_value = 0.85
sun_d = bpy.data.lights.new("Sun", "SUN")
sun_d.energy = 3.6
sun_d.angle = math.radians(3)
clock = pre.get("ClockTime", 14)
elev = max(12.0, 72 - abs(clock - 12.5) * 11)
sun_d.color = (1.0, 0.97, 0.92) if clock < 16 else (1.0, 0.82, 0.62)
sun = bpy.data.objects.new("Sun", sun_d)
sun.rotation_euler = (math.radians(90 - elev), 0, math.radians(35))
scene.collection.objects.link(sun)


def camera(loc, target, lens):
    cd = bpy.data.cameras.new("Cam")
    cd.lens = lens
    cd.clip_end = 6000
    cam = bpy.data.objects.new("Cam", cd)
    scene.collection.objects.link(cam)
    L, T = rb(loc), rb(target)
    d = [T[i] - L[i] for i in range(3)]
    cam.location = L
    cam.rotation_euler = (math.atan2(math.hypot(d[0], d[1]), -d[2]), 0, math.atan2(d[1], d[0]) - math.pi / 2)
    scene.camera = cam


for name, (loc, target, lens) in data["cameras"].items():
    if VIEWS and name not in VIEWS:
        continue
    camera(loc, target, lens)
    scene.render.filepath = os.path.join(OUT, "%s_%s%s.png" % (MAP, name, SUFFIX))
    bpy.ops.render.render(write_still=True)
    print("rendered", scene.render.filepath)
