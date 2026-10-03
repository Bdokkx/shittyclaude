"""Blender side: builds the voxel assets + both maps as meshes, exports every
asset (FBX / GLB / OBJ with a palette texture), saves .blend files and renders
previews.

    blender -b -P tools/blender_build.py -- <repo-root> [--no-render]
"""
import math
import os
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ROOT = os.path.abspath(argv[0] if argv else ".")
RENDER = "--no-render" not in argv
OPTS = dict(a[2:].split("=", 1) for a in argv if a.startswith("--") and "=" in a)
ONLY = OPTS.get("only")          # assets | island | reef
SAMPLES = int(OPTS["samples"]) if "samples" in OPTS else None
RES = int(OPTS.get("res", 100))
sys.path.insert(0, os.path.join(ROOT, "gen"))

from assets import ASSETS, MESH_SOURCES, bounds  # noqa: E402
sys.path.insert(0, os.path.join(ROOT, "tools"))
import mathutils  # noqa: E402
USE_MESHES = OPTS.get("meshes", "1") != "0"   # show rocks as the Blender meshes (final look)
MESH_LIB = {}
from maps import build_island, build_reef  # noqa: E402
from palette import COLORS, CORAL_TINTS, TINT_NAMES, darker  # noqa: E402

OUT = os.path.join(ROOT, "blender")
EXP = os.path.join(ROOT, "exports")
PREV = os.path.join(ROOT, "previews")
for d in (OUT, EXP, PREV, *(os.path.join(EXP, k) for k in ("fbx", "glb", "obj"))):
    os.makedirs(d, exist_ok=True)

# ---------------------------------------------------------------- palette texture
CELLS = 16          # 16 x 16 colour cells
CELL_PX = 8
SIZE = CELLS * CELL_PX

swatches = {n: (r, g, b) for n, (r, g, b, _) in COLORS.items()}
for t in TINT_NAMES:
    swatches["tint_" + t] = CORAL_TINTS[t]
    swatches["tint_" + t + "_dk"] = darker(CORAL_TINTS[t])
cell_of = {n: k for k, n in enumerate(swatches)}
GLOW = {n for n, c in COLORS.items() if c[3] == "Neon"}


def make_palette_image():
    img = bpy.data.images.new("voxel_palette", SIZE, SIZE, alpha=False)
    px = [0.0] * (SIZE * SIZE * 4)
    for name, k in cell_of.items():
        r, g, b = swatches[name]
        cx, cy = k % CELLS, k // CELLS
        for y in range(cy * CELL_PX, (cy + 1) * CELL_PX):
            for x in range(cx * CELL_PX, (cx + 1) * CELL_PX):
                i = (y * SIZE + x) * 4
                px[i:i + 4] = [r / 255, g / 255, b / 255, 1.0]
    img.pixels = px
    path = os.path.join(EXP, "voxel_palette.png")
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    for sub in ("fbx", "glb", "obj"):
        import shutil
        shutil.copy(path, os.path.join(EXP, sub, "voxel_palette.png"))
    img.filepath = path
    return img


def uv_for(name):
    k = cell_of[name]
    return ((k % CELLS + 0.5) / CELLS, (k // CELLS + 0.5) / CELLS)


# ---------------------------------------------------------------- materials

def palette_material(img, glow=False):
    m = bpy.data.materials.new("VoxelGlow" if glow else "VoxelPalette")
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.interpolation = "Closest"
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.75
    if glow:
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Emission Color"])
        bsdf.inputs["Emission Strength"].default_value = 4.0
    return m


def ocean_material():
    m = bpy.data.materials.new("Ocean")
    m.use_nodes = True
    nt = m.node_tree
    out = nt.nodes["Material Output"]
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.02, 0.18, 0.5, 1)
    bsdf.inputs["Roughness"].default_value = 0.08
    transp = nt.nodes.new("ShaderNodeBsdfTransparent")
    transp.inputs["Color"].default_value = (0.35, 0.75, 0.95, 1)
    mix = nt.nodes.new("ShaderNodeMixShader")
    mix.inputs["Fac"].default_value = 0.35
    nt.links.new(transp.outputs[0], mix.inputs[1])
    nt.links.new(bsdf.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    m.blend_method = "BLEND"
    return m


# ---------------------------------------------------------------- geometry (Roblox space -> Blender)

def rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return ((1, 0, 0), (0, c, -s), (0, s, c))


def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return ((c, 0, s), (0, 1, 0), (-s, 0, c))


def rot_z(a):
    c, s = math.cos(a), math.sin(a)
    return ((c, -s, 0), (s, c, 0), (0, 0, 1))


def mul(a, b):
    return tuple(tuple(sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)) for i in range(3))


IDENT = ((1, 0, 0), (0, 1, 0), (0, 0, 1))


def apply(m, v):
    return tuple(m[i][0] * v[0] + m[i][1] * v[1] + m[i][2] * v[2] for i in range(3))


def to_blender(p):
    x, y, z = p
    return (x, -z, y)


CUBE_FACES = ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3))


class MeshBuilder:
    def __init__(self):
        self.verts, self.faces, self.uvs, self.mats = [], [], [], []

    def box(self, b, rot=IDENT, pos=(0, 0, 0), scale=1.0, color=None):
        x0, y0, z0, x1, y1, z1, c = b
        c = color or c
        base = len(self.verts)
        for k in range(8):
            lp = (x1 if k & 1 else x0, y1 if k & 2 else y0, z1 if k & 4 else z0)
            wp = apply(rot, (lp[0] * scale, lp[1] * scale, lp[2] * scale))
            self.verts.append(to_blender((wp[0] + pos[0], wp[1] + pos[1], wp[2] + pos[2])))
        uv = uv_for(c)
        glow = 1 if c in GLOW else 0
        for f in CUBE_FACES:
            # CUBE_FACES wind inward; reverse for outward normals
            self.faces.append(tuple(base + i for i in reversed(f)))
            self.uvs.append(uv)
            self.mats.append(glow)

    def asset(self, name, pos=(0, 0, 0), roty=0, scale=1, tint=0, rx=0, rz=0):
        rot = mul(rot_y(math.radians(roty)), mul(rot_x(math.radians(rx)), rot_z(math.radians(rz))))
        tname = TINT_NAMES[tint - 1] if tint else None
        for b in ASSETS[name]["boxes"]:
            col = None
            if tname and b[6] == "accent":
                col = "tint_" + tname
            elif tname and b[6] == "accent_dark":
                col = "tint_" + tname + "_dk"
            self.box(b, rot, pos, scale, col)

    def to_object(self, name, mats, collection):
        me = bpy.data.meshes.new(name)
        me.from_pydata(self.verts, [], self.faces)
        uvl = me.uv_layers.new(name="UVMap")
        for poly in me.polygons:
            uv = self.uvs[poly.index]
            poly.material_index = self.mats[poly.index]
            for li in poly.loop_indices:
                uvl.data[li].uv = uv
        me.update()
        for m in mats:
            me.materials.append(m)
        ob = bpy.data.objects.new(name, me)
        collection.objects.link(ob)
        return ob


# ---------------------------------------------------------------- scene helpers

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def setup_world(scene, strength=1.0):
    world = bpy.data.worlds.new("Sky")
    scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    bg = nt.nodes["Background"]
    bg.inputs[0].default_value = (0.55, 0.75, 1.0, 1)
    bg.inputs[1].default_value = 0.9 * strength
    sun_data = bpy.data.lights.new("Sun", "SUN")
    sun_data.energy = 3.2
    sun_data.angle = math.radians(4)
    sun_data.color = (1.0, 0.96, 0.9)
    sun = bpy.data.objects.new("Sun", sun_data)
    sun.rotation_euler = (math.radians(40), math.radians(-15), math.radians(30))
    scene.collection.objects.link(sun)


def setup_render(scene, w, h, samples=48):
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = SAMPLES or samples
    scene.cycles.max_bounces = 4
    scene.cycles.use_denoising = False  # distro Blender builds often lack OIDN
    scene.cycles.filter_width = 1.2
    scene.render.resolution_x = w
    scene.render.resolution_y = h
    scene.render.resolution_percentage = RES
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.exposure = -0.35
    scene.render.threads_mode = "AUTO"


def add_camera(scene, loc, target, lens=35, ortho=None):
    cam_data = bpy.data.cameras.new("Camera")
    cam_data.lens = lens
    cam_data.clip_end = 5000
    if ortho:
        cam_data.type = "ORTHO"
        cam_data.ortho_scale = ortho
    cam = bpy.data.objects.new("Camera", cam_data)
    scene.collection.objects.link(cam)
    cam.location = loc
    d = [target[i] - loc[i] for i in range(3)]
    yaw = math.atan2(d[1], d[0]) - math.pi / 2
    pitch = math.atan2(math.hypot(d[0], d[1]), -d[2])
    cam.rotation_euler = (pitch, 0, yaw)
    scene.camera = cam
    return cam


def render(scene, path):
    if not RENDER:
        return
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("rendered", path)


def mesh_library():
    """Build the deformed rock meshes once (hidden) so map renders can instance them."""
    if MESH_LIB or not USE_MESHES:
        return MESH_LIB
    import rockmesh
    lib = bpy.data.collections.new("RockMeshLibrary")
    bpy.context.scene.collection.children.link(lib)
    tex_dir = os.path.join(EXP, "meshes")
    os.makedirs(tex_dir, exist_ok=True)
    for name, src in MESH_SOURCES.items():
        root, objs = rockmesh.build_rock(name, src, lib, tex_dir)
        MESH_LIB[name] = objs
    lib.hide_render = True
    return MESH_LIB


A = mathutils.Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))  # Roblox -> Blender axes


def prop_matrix(x, y, z, rot, sc, rx, rz):
    r = mul(rot_y(math.radians(rot)), mul(rot_x(math.radians(rx)), rot_z(math.radians(rz))))
    rb = A @ mathutils.Matrix(r) @ A.transposed()
    m = rb.to_4x4() @ mathutils.Matrix.Scale(sc, 4)
    m.translation = to_blender((x, y, z))
    return m


def map_objects(m, coll, mats, ocean_mat, prefix, offset=(0, 0, 0)):
    lib = mesh_library()
    ground = MeshBuilder()
    extra = []
    if USE_MESHES and "groups" in m:
        # final look: deformed terrain mesh instead of the Ground columns + Cliffs facades
        import terrainmesh
        for gname, boxes in m["groups"]:
            if gname in ("Shallows", "Paths"):
                for b in boxes:
                    ground.box(b)
        extra = terrainmesh.build_island_terrain(m, coll, os.path.join(EXP, "meshes"))
    else:
        for b in m["terrain"]:
            ground.box(b)
    props = MeshBuilder()
    for (name, x, y, z, rot, sc, tint, rx, rz) in m["props"]:
        if name in lib:
            mat = prop_matrix(x, y, z, rot, sc, rx, rz)
            for src in lib[name]:
                ob = bpy.data.objects.new(prefix + "_" + src.name, src.data)
                ob.matrix_world = mat
                ob.matrix_world.translation += mathutils.Vector(offset)
                coll.objects.link(ob)
        else:
            props.asset(name, (x, y, z), rot, sc, tint, rx, rz)
    objs = [ground.to_object(prefix + "_Ground", mats, coll), props.to_object(prefix + "_Props", mats, coll)]
    if m["water"]:
        x0, y0, z0, x1, y1, z1 = m["water"]
        wb = MeshBuilder()
        wb.box((x0, y1 - 0.01, z0, x1, y1, z1, "ocean"))
        ob = wb.to_object(prefix + "_Ocean", [ocean_mat], coll)
        objs.append(ob)
    for ob in objs + extra:
        ob.location = offset
    return objs + extra


# ================================================================= 1. assets
if ONLY in (None, "assets"):
    reset()
    scene = bpy.context.scene
    img = make_palette_image()
    mat, glow = palette_material(img), palette_material(img, glow=True)
    coll = bpy.data.collections.new("VoxelAssets")
    scene.collection.children.link(coll)

    variants = []
    for name, a in ASSETS.items():
        if a["tintable"]:
            variants += [(name + "_" + t, name, k + 1) for k, t in enumerate(TINT_NAMES)]
        else:
            variants.append((name, name, 0))

    objects = {}
    for vname, name, tint in variants:
        mb = MeshBuilder()
        mb.asset(name, tint=tint)
        objects[vname] = mb.to_object(vname, [mat, glow], coll)


    def export_one(ob, vname):
        bpy.ops.object.select_all(action="DESELECT")
        ob.select_set(True)
        bpy.context.view_layer.objects.active = ob
        bpy.ops.export_scene.fbx(filepath=os.path.join(EXP, "fbx", vname + ".fbx"), use_selection=True,
                                 path_mode="COPY", embed_textures=True, axis_forward="-Z", axis_up="Y",
                                 apply_scale_options="FBX_SCALE_ALL", mesh_smooth_type="FACE")
        bpy.ops.export_scene.gltf(filepath=os.path.join(EXP, "glb", vname + ".glb"), use_selection=True,
                                  export_format="GLB")
        bpy.ops.wm.obj_export(filepath=os.path.join(EXP, "obj", vname + ".obj"),
                              export_selected_objects=True, path_mode="RELATIVE",
                              forward_axis="NEGATIVE_Z", up_axis="Y")


    for vname, ob in objects.items():
        export_one(ob, vname)
    print("exported", len(objects), "asset variants")

    # lay the base (untinted / pink) variants out on a grid for the contact sheet
    shown = [v for v in variants if v[2] in (0, 1) and v[0] != "Shipwreck"]
    cols = 6
    cell = 44
    for k, (vname, name, tint) in enumerate(shown):
        ob = objects[vname]
        r, c = divmod(k, cols)
        ob.location = ((c - (cols - 1) / 2) * cell, -r * cell, -bounds(name)[0][1])
        if name in ("Dock", "WoodenStairs"):
            ob.rotation_euler = (0, 0, math.radians(90))
    rows = math.ceil(len(shown) / cols) + 1
    ship = objects["Shipwreck"]
    ship.location = (0, -(rows - 1) * cell - 4, 0)
    ship.rotation_euler = (0, 0, math.radians(90))
    shown.append(("Shipwreck", "Shipwreck", 0))
    for vname, ob in objects.items():
        if vname not in [v[0] for v in shown]:
            ob.hide_render = True
            ob.location = (0, 0, -500)
    ground = MeshBuilder()
    ground.box((-170, -2, -60, 170, 0, rows * cell + 40, "reef_sand"))
    ground.to_object("Floor", [mat, glow], scene.collection)
    setup_world(scene)
    setup_render(scene, 1600, 1100, 64)
    add_camera(scene, (0, -rows * cell * 0.5 - 250, 250), (0, -rows * cell * 0.5 + 4, 0), lens=33)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "voxel_assets.blend"))
    render(scene, os.path.join(PREV, "assets_contact_sheet.png"))

# ================================================================= 2. maps
reset()
scene = bpy.context.scene
img = make_palette_image()
mat, glow = palette_material(img), palette_material(img, glow=True)
ocean = ocean_material()
setup_world(scene)
setup_render(scene, 1700, 960, 64)

isl_coll = bpy.data.collections.new("VoxelIsland")
scene.collection.children.link(isl_coll)
reef_coll = bpy.data.collections.new("CoralReef")
scene.collection.children.link(reef_coll)
if ONLY in (None, "island"):
    map_objects(build_island(), isl_coll, [mat, glow], ocean, "Island")
if ONLY in (None, "reef"):
    # Roblox (0,0,700) -> Blender (0,-700,0)
    map_objects(build_reef(), reef_coll, [mat, glow], ocean, "Reef", offset=(0, -700, 0))

if ONLY is None:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "voxel_maps.blend"))

if ONLY in (None, "island"):
    reef_coll.hide_render = True
    isl_coll.hide_render = False
    # overview from the south-east, like the reference shot
    add_camera(scene, (235, -335, 165), (-5, 5, 22), lens=30)
    render(scene, os.path.join(PREV, "island.png"))
    # close-up of the village and the stairs
    add_camera(scene, (50, -205, 95), (2, -52, 20), lens=30)
    render(scene, os.path.join(PREV, "island_village.png"))
    # the mountain with its crags and the stair path
    add_camera(scene, (150, -70, 150), (0, 50, 62), lens=30)
    render(scene, os.path.join(PREV, "island_mountain.png"))
    # walking up the west path towards the arch gateway
    arch = next((p for p in build_island()["props"] if p[0] == "Arch"), None)
    if arch:
        ax, ay, az, rot = arch[1], arch[2], arch[3], math.radians(arch[4])
        dx, dz = math.sin(rot), math.cos(rot)
        add_camera(scene, to_blender((ax - dx * 70, ay + 22, az - dz * 70)), to_blender((ax, ay + 14, az)), lens=28)
        render(scene, os.path.join(PREV, "island_arch.png"))
    # low along the shore, sea stacks and cliff-foot rocks
    add_camera(scene, (-250, -250, 32), (-120, -70, 16), lens=30)
    render(scene, os.path.join(PREV, "island_shore.png"))

if ONLY in (None, "reef"):
    reef_coll.hide_render = False
    isl_coll.hide_render = True
    add_camera(scene, (-120, -700 - 250, 70), (20, -700 + 20, 6), lens=28)
    render(scene, os.path.join(PREV, "reef.png"))
print("done")
