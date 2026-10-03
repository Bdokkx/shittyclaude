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
GLASS = {n for n, c in COLORS.items() if c[3] == "Glass" and n != "ocean"}


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


def glass_material(img):
    m = palette_material(img)
    m.name = "VoxelGlass"
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.05
    bsdf.inputs["Alpha"].default_value = 0.6
    m.blend_method = "BLEND"
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
        glow = 1 if c in GLOW else (2 if c in GLASS else 0)
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
            if gname in ("Shallows", "Paths", "Accents"):
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

# ================================================================= 2. islands + reef
from island import build_island as build_themed  # noqa: E402
from themes import ORDER, THEMES  # noqa: E402

ISLAND_ASSETS = {
    "voxel": ["PineTree", "PineTreeTall", "Bush", "GrassTuft", "Flowers", "Fern", "Mushrooms", "SmallRock",
              "CliffCrag", "CliffRocks", "LedgeRock", "RockOutcrop", "RockOutcropBig", "Arch", "Dock", "Rowboat",
              "MarketStall", "Campfire", "LampPost", "Torch", "WoodFrame", "Statue", "Signpost", "Well",
              "FlagFrame", "CaveEntrance", "Fence", "CrateStack", "Barrels", "LogPile"],
    "desert": ["PalmTree", "PalmTreeTall", "PalmTreeSmall", "Cactus", "DryBush", "DesertTuft", "DesertRock", "Pots",
               "AdobeHouse", "AdobeHouseBig", "DesertStall", "DesertWell", "Obelisk", "SandstonePillar", "Brazier",
               "Ziggurat", "DesertCrag", "DesertRocks", "DesertLedge", "DesertStack", "DesertStackBig", "DesertArch"],
    "frost": ["SnowPine", "SnowPineTall", "SnowPineSmall", "FrostBush", "SnowPile", "IceCrystal", "FrostRock",
              "Snowman", "LogCabin", "IceCrag", "IceRocks", "IceLedge", "Iceberg", "IcebergBig", "IceArch"],
    "volcanic": ["CharredPine", "CharredPineSmall", "DeadTree", "AshTuft", "LavaRock", "ObsidianShards",
                 "BasaltColumns", "VolcanicBrazier", "StiltHut", "BasaltCrag", "BasaltRocks", "BasaltLedge",
                 "ObsidianStack", "ObsidianStackBig", "BasaltArch"],
}


def fresh_scene(w=1700, h=960, samples=48):
    reset()
    scene = bpy.context.scene
    img = make_palette_image()
    mats = [palette_material(img), palette_material(img, glow=True), glass_material(img)]
    MESH_LIB.clear()
    setup_world(scene)
    setup_render(scene, w, h, samples)
    return scene, mats


def ortho_top(scene, size, name):
    cam_data = bpy.data.cameras.new("Top")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = size
    cam_data.clip_end = 5000
    cam = bpy.data.objects.new("Top", cam_data)
    scene.collection.objects.link(cam)
    cam.location = (0, 0, 900)
    scene.camera = cam
    w, h = scene.render.resolution_x, scene.render.resolution_y
    scene.render.resolution_x = scene.render.resolution_y = 1000
    render(scene, os.path.join(PREV, name))
    scene.render.resolution_x, scene.render.resolution_y = w, h


def look(scene, target, offset, lens=30, lift=8):
    tx, ty, tz = target
    add_camera(scene, to_blender((tx + offset[0], ty + offset[1], tz + offset[2])),
               to_blender((tx, ty + lift, tz)), lens=lens)


def first(m, name):
    return next((p for p in m["props"] if p[0] == name), None)


for theme in ORDER:
    if ONLY not in (None, "islands", theme):
        continue
    scene, mats = fresh_scene()
    m = build_themed(theme)
    name = m["map"]
    coll = bpy.data.collections.new(name)
    scene.collection.children.link(coll)
    map_objects(m, coll, mats, ocean_material(), name)
    L = m["landmarks"]
    look(scene, (0, 0, 0), (235, 165, 335), lift=22)                      # overview from the south-east
    render(scene, os.path.join(PREV, name + ".png"))
    ortho_top(scene, 540, name + "_top.png")
    px, py, pz = L["plaza"]                                               # the village
    look(scene, (px, py, pz), (48, 75, 140), lens=30, lift=4)
    render(scene, os.path.join(PREV, name + "_village.png"))
    if theme == "desert":                                                 # signature close-ups
        z = first(m, "Ziggurat")
        look(scene, (z[1], z[2], z[3]), (55, 40, 70), lift=10)
        render(scene, os.path.join(PREV, name + "_detail.png"))
    elif theme == "volcanic" and L["crater"]:
        cx, cy, cz = L["crater"]
        look(scene, (cx, cy, cz), (80, 55, 120), lift=0)
        render(scene, os.path.join(PREV, name + "_detail.png"))
    elif theme == "voxel":
        arch = first(m, "Arch")
        ax, ay, az, rot = arch[1], arch[2], arch[3], math.radians(arch[4])
        look(scene, (ax, ay, az), (-math.sin(rot) * 70, 22, -math.cos(rot) * 70), lens=28, lift=14)
        render(scene, os.path.join(PREV, name + "_detail.png"))
    else:
        look(scene, L["peak"], (90, 10, 120), lift=-20)
        render(scene, os.path.join(PREV, name + "_detail.png"))
    if L["falls"]:                                                        # waterfall / frozen fall / lava fall
        fx, fy, fz, d = L["falls"][len(L["falls"]) // 2]
        look(scene, (fx, fy * 0.6, fz), (d[0] * 115 + d[1] * 45, 34, d[1] * 115 + d[0] * 45), lens=30, lift=0)
        render(scene, os.path.join(PREV, name + "_falls.png"))
    if theme == "voxel":
        look(scene, (-120, 16, 70), (-130, 16, 180), lift=0)                # shoreline
        render(scene, os.path.join(PREV, name + "_shore.png"))

if ONLY in (None, "reef"):
    scene, mats = fresh_scene()
    coll = bpy.data.collections.new("CoralReef")
    scene.collection.children.link(coll)
    map_objects(build_reef(), coll, mats, ocean_material(), "Reef")
    add_camera(scene, (-120, -250, 70), (20, 20, 6), lens=28)
    render(scene, os.path.join(PREV, "CoralReef.png"))

# ================================================================= 3. per-theme asset tiles
# Every custom asset of every island is rendered on its own framed tile (previews/tiles/<theme>/);
# tools/compose_previews.py lays them out into labelled sheets + posters.
for theme in ORDER:
    if ONLY not in (None, "sheets", theme):
        continue
    scene, mats = fresh_scene(420, 420, 32)
    scene.render.film_transparent = False
    lib = mesh_library()
    coll = bpy.data.collections.new("Tile")
    scene.collection.children.link(coll)
    floor = THEMES[theme]["sand_top"][0][0]
    fb = MeshBuilder()
    fb.box((-400, -2, -400, 400, 0, 400, floor))
    fb.to_object("Floor", mats, coll)
    tdir = os.path.join(PREV, "tiles", theme)
    os.makedirs(tdir, exist_ok=True)
    for n in ISLAND_ASSETS[theme]:
        made = []
        if n in lib:
            m_ = prop_matrix(0, 0, 0, 30, 1, 0, 0)
            for src in lib[n]:
                ob = bpy.data.objects.new("T_" + src.name, src.data)
                ob.matrix_world = m_
                coll.objects.link(ob)
                made.append(ob)
        else:
            mb = MeshBuilder()
            mb.asset(n, (0, 0, 0), 30, 1, 1 if ASSETS[n]["tintable"] else 0)
            made.append(mb.to_object("T_" + n, mats, coll))
        mn, mx = bounds(n)
        h = mx[1] - mn[1]
        r = max(math.hypot(mx[0] - mn[0], mx[2] - mn[2]) / 2, h * 0.62, 3)
        for ob in made:   # sit the asset on the floor
            ob.location.z -= mn[1]
        cam = add_camera(scene, to_blender((r * 1.25, h * 0.5 + r * 1.05, r * 2.1)),
                         to_blender((0, h * 0.42, 0)), lens=42)
        render(scene, os.path.join(tdir, n + ".png"))
        for ob in made:
            bpy.data.objects.remove(ob)
        bpy.data.objects.remove(cam)
print("done")
