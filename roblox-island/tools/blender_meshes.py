"""Builds the deformed, stud-textured rock meshes and exports them for Roblox.

    blender -b -P tools/blender_meshes.py -- <repo-root> [--no-render]

Outputs
  exports/meshes/VoxelRockMeshes.fbx   every rock in one file (import this one into Studio)
  exports/meshes/<Name>.fbx / .glb     one file per rock
  exports/meshes/studs_*.png           the stud textures (embedded in the FBX too)
  blender/voxel_rock_meshes.blend
  previews/rock_meshes.png
"""
import math
import os
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ROOT = os.path.abspath(argv[0] if argv else ".")
RENDER = "--no-render" not in argv
sys.path.insert(0, os.path.join(ROOT, "gen"))
sys.path.insert(0, os.path.join(ROOT, "tools"))

from assets import MESH_SOURCES  # noqa: E402
import rockmesh  # noqa: E402

OUT = os.path.join(ROOT, "exports", "meshes")
os.makedirs(OUT, exist_ok=True)
os.makedirs(os.path.join(ROOT, "previews"), exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
coll = bpy.data.collections.new("RockMeshes")
scene.collection.children.link(coll)

roots = {}
for name, src in MESH_SOURCES.items():
    root, objs = rockmesh.build_rock(name, src, coll, OUT)
    roots[name] = (root, objs)
    for o in objs:
        assert o.name.startswith(name + "_") and "." not in o.name, o.name
    tris = sum(len(o.data.polygons) for o in objs)
    print("built %-18s %5d faces in %d mesh(es)" % (name, tris, len(objs)))


def select_tree(root):
    bpy.ops.object.select_all(action="DESELECT")
    root.select_set(True)
    for c in root.children:
        c.select_set(True)
    bpy.context.view_layer.objects.active = root


def export_fbx(path):
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, path_mode="COPY", embed_textures=True,
                             axis_forward="-Z", axis_up="Y", apply_scale_options="FBX_SCALE_ALL",
                             mesh_smooth_type="FACE", object_types={"EMPTY", "MESH"})


for name, (root, objs) in roots.items():
    select_tree(root)
    export_fbx(os.path.join(OUT, name + ".fbx"))
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, name + ".glb"), use_selection=True,
                              export_format="GLB")

# everything in one file, laid out in a row (positions don't matter: MeshSwap fits by bounds)
x = 0
for name, (root, objs) in roots.items():
    root.location = (x, 0, 0)
    x += 50
bpy.ops.object.select_all(action="DESELECT")
for root, objs in roots.values():
    root.select_set(True)
    for o in objs:
        o.select_set(True)
export_fbx(os.path.join(OUT, "VoxelRockMeshes.fbx"))
print("exported", len(roots), "rock meshes")

# MeshSwap.lua gets the exact size/centre of every mesh piece, so Roblox can place each
# MeshPart directly instead of guessing from bounding boxes.
from palette import COLORS  # noqa: E402
rows = []
for name, (root, objs) in roots.items():
    pieces = []
    for o in objs:
        mn, mx = rockmesh.roblox_bounds(o)
        r, g, b, _ = COLORS[o["voxel_color"]]
        suffix = o.name[len(name):]
        pieces.append('{ suffix = "%s", min = Vector3.new(%s, %s, %s), max = Vector3.new(%s, %s, %s), '
                      'color = Color3.fromRGB(%d, %d, %d) }' % (suffix, *mn, *mx, r, g, b))
    rows.append('\t%s = {\n\t\t%s,\n\t},' % (name, ",\n\t\t".join(pieces)))
# the island terrain itself as deformed, chunked meshes
import terrainmesh  # noqa: E402
from island import build_island  # noqa: E402
tcoll = bpy.data.collections.new("IslandTerrain")
scene.collection.children.link(tcoll)
terrain_objs = terrainmesh.build_island_terrain(build_island(), tcoll, OUT)
bpy.ops.object.select_all(action="DESELECT")
for o in terrain_objs:
    o.data.name = o.name
    o.select_set(True)
export_fbx(os.path.join(OUT, "IslandTerrain.fbx"))
tris = sum(len(o.data.polygons) for o in terrain_objs)
print("exported island terrain: %d meshes, %d triangles (max %d per mesh)" % (
    len(terrain_objs), tris, max(len(o.data.polygons) for o in terrain_objs)))
trows = []
for o in terrain_objs:
    mn, mx = rockmesh.roblox_bounds(o)
    r, g, b, _ = COLORS[o["voxel_color"]]
    trows.append('\t{ name = "%s", min = Vector3.new(%s, %s, %s), max = Vector3.new(%s, %s, %s), '
                 'color = Color3.fromRGB(%d, %d, %d) },' % (o.name, *mn, *mx, r, g, b))
for o in terrain_objs:
    o.hide_render = True

tmpl = open(os.path.join(ROOT, "tools", "meshswap_template.lua")).read()
with open(os.path.join(ROOT, "roblox", "MeshSwap.lua"), "w") as f:
    f.write(tmpl.replace("--@@PIECES@@", "\n".join(rows)).replace("--@@TERRAIN@@", "\n".join(trows)))
print("wrote roblox/MeshSwap.lua")

# contact sheet
cols = 5
for k, (name, (root, objs)) in enumerate(roots.items()):
    r, c = divmod(k, cols)
    root.location = ((c - (cols - 1) / 2) * 42, -r * 46, 0)
floor_me = bpy.data.meshes.new("floor")
floor_me.from_pydata([(-130, -120, 0), (130, -120, 0), (130, 50, 0), (-130, 50, 0)], [], [(0, 1, 2, 3)])
floor = bpy.data.objects.new("floor", floor_me)
scene.collection.objects.link(floor)
fm = bpy.data.materials.new("floor")
fm.use_nodes = True
fm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.78, 0.74, 0.52, 1)
floor_me.materials.append(fm)

world = bpy.data.worlds.new("Sky")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.75, 1.0, 1)
world.node_tree.nodes["Background"].inputs[1].default_value = 0.9
sun_data = bpy.data.lights.new("Sun", "SUN")
sun_data.energy = 3.2
sun = bpy.data.objects.new("Sun", sun_data)
sun.rotation_euler = (math.radians(40), math.radians(-15), math.radians(30))
scene.collection.objects.link(sun)
cam_data = bpy.data.cameras.new("Cam")
cam_data.lens = 34
cam = bpy.data.objects.new("Cam", cam_data)
scene.collection.objects.link(cam)
cam.location = (0, -200, 120)
cam.rotation_euler = (math.radians(62), 0, 0)
scene.camera = cam
scene.render.engine = "CYCLES"
scene.cycles.samples = 48
scene.cycles.use_denoising = False
scene.render.resolution_x, scene.render.resolution_y = 1600, 1000
scene.view_settings.view_transform = "Standard"
scene.view_settings.exposure = -0.35
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "blender", "voxel_rock_meshes.blend"))
if RENDER:
    scene.render.filepath = os.path.join(ROOT, "previews", "rock_meshes.png")
    bpy.ops.render.render(write_still=True)
    print("rendered", scene.render.filepath)

# close-up of a reef pinnacle + shelf to check the deformation and studs
if RENDER:
    for k, (name, (root, objs)) in enumerate(roots.items()):
        root.hide_render = name not in ("ReefPinnacleTall", "ReefShelf", "Seaweed")
    roots["ReefPinnacleTall"][0].location = (-14, 0, 0)
    roots["ReefShelf"][0].location = (16, 6, 0)
    roots["Seaweed"][0].location = (-2, -12, 0)
    cam.location = (0, -62, 22)
    cam.rotation_euler = (math.radians(80), 0, 0)
    scene.render.resolution_x, scene.render.resolution_y = 1400, 900
    scene.render.filepath = os.path.join(ROOT, "previews", "rock_meshes_closeup.png")
    bpy.ops.render.render(write_still=True)
    print("rendered", scene.render.filepath)
