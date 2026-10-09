"""Cube Monster: a blocky, square-headed monster built from boxes, in the same
style as the island assets.

Writes to monster/:
  CubeMonster.lua           Roblox Command Bar script that builds it from Parts
  CubeMonster.blend/.fbx/.glb + CubeMonster_palette.png
  CubeMonster_preview.png   front and three-quarter renders

    blender -b -P tools/cube_monster.py -- <repo-root>
    python  tools/cube_monster.py <repo-root>      (with the bpy module installed)
"""
import math
import os
import sys

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
ROOT = os.path.abspath(argv[0] if argv else ".")
sys.path.insert(0, os.path.join(ROOT, "gen"))
from assets import B, dezfight  # noqa: E402

OUT = os.path.join(ROOT, "monster")
os.makedirs(OUT, exist_ok=True)

# name: (r, g, b, roblox material)
COLORS = {
    "skin":      (118, 200, 68, "SmoothPlastic"),
    "skin_dark": (80, 150, 46, "SmoothPlastic"),
    "spot":      (96, 172, 54, "SmoothPlastic"),
    "belly":     (196, 232, 132, "SmoothPlastic"),
    "brow":      (48, 96, 32, "SmoothPlastic"),
    "horn":      (242, 230, 198, "SmoothPlastic"),
    "horn_tip":  (198, 182, 146, "SmoothPlastic"),
    "eye":       (255, 212, 36, "SmoothPlastic"),
    "pupil":     (22, 20, 26, "SmoothPlastic"),
    "shine":     (255, 255, 255, "SmoothPlastic"),
    "mouth":     (56, 14, 28, "SmoothPlastic"),
    "tongue":    (228, 72, 98, "SmoothPlastic"),
    "tooth":     (252, 250, 242, "SmoothPlastic"),
}


# ---------------------------------------------------------------- the monster
# Studs, Y up, origin at the ground under the middle, facing -Z (Roblox front).
# The face is the -Z side of the head, at z = -4.5.

def mirrored(cx, *rest):
    return [B(cx, *rest), B(-cx, *rest)]


def monster_boxes():
    b = []
    # legs, feet and toe claws
    b += mirrored(2.0, 0.9, 0.0, 2.6, 2.4, 2.6, "skin")
    b += mirrored(2.0, 0.0, -0.5, 3.2, 1.0, 3.6, "skin_dark")
    for side in (1, -1):
        for dx in (-0.9, 0.0, 0.9):
            b.append(B(side * 2.0 + dx, 0.0, -2.5, 0.6, 0.6, 0.6, "horn"))
    # body, belly patch and stubby tail
    b.append(B(0, 2.8, 0, 7.0, 5.6, 5.0, "skin"))
    b.append(B(0, 3.4, -2.5, 4.4, 3.8, 0.3, "belly"))
    b.append(B(0, 3.4, 3.4, 2.4, 1.8, 2.4, "skin"))
    b.append(B(0, 4.0, 5.2, 1.6, 1.2, 1.6, "skin_dark"))
    b.append(B(0, 5.2, 5.4, 0.8, 0.8, 0.8, "horn"))
    # arms, hands and claws hanging at the sides
    b += mirrored(4.4, 3.2, -0.3, 2.0, 5.0, 2.2, "skin")
    b += mirrored(4.5, 2.0, -0.4, 2.4, 1.4, 2.6, "skin_dark")
    for side in (1, -1):
        for dz in (-1.2, -0.4, 0.4):
            b.append(B(side * 4.5, 1.2, dz - 0.4, 0.5, 0.9, 0.5, "horn"))
    # the big square head
    b.append(B(0, 8.0, 0, 10.0, 9.0, 9.0, "skin"))
    # spots on the sides and top
    for side in (1, -1):
        b.append(B(side * 5.05, 13.0, 1.5, 0.2, 2.0, 2.4, "spot"))
        b.append(B(side * 5.05, 10.0, -1.0, 0.2, 1.4, 1.4, "spot"))
        b.append(B(side * 5.05, 14.6, -2.2, 0.2, 1.0, 1.0, "spot"))
    b.append(B(-2.6, 17.0, 2.4, 2.2, 0.15, 1.8, "spot"))
    b.append(B(2.8, 17.0, 0.4, 1.4, 0.15, 1.4, "spot"))
    # horns: three stepped blocks curling outward and up
    for side in (1, -1):
        b.append(B(side * 3.4, 17.0, 0.5, 1.8, 1.5, 1.8, "horn"))
        b.append(B(side * 3.9, 18.5, 0.5, 1.4, 1.3, 1.4, "horn"))
        b.append(B(side * 4.5, 19.8, 0.5, 1.0, 1.0, 1.0, "horn"))
        b.append(B(side * 4.9, 20.8, 0.5, 0.6, 0.7, 0.6, "horn_tip"))
    # back spikes
    for z in (2.0, 3.6):
        b.append(B(0, 17.0, z, 1.0, 1.1, 1.0, "skin_dark"))
    b.append(B(0, 18.1, 2.0, 0.5, 0.5, 0.5, "skin_dark"))
    # eyes: yellow squares with square pupils and a shine
    for side in (1, -1):
        b.append(B(side * 2.3, 12.8, -4.6, 2.6, 2.6, 0.3, "eye"))
        b.append(B(side * 2.1, 13.3, -4.8, 1.2, 1.4, 0.3, "pupil"))
        b.append(B(side * 2.1 + 0.3, 14.1, -5.0, 0.45, 0.45, 0.2, "shine"))
        # angry stepped brows, low on the inside
        b.append(B(side * 3.1, 16.1, -4.7, 1.8, 0.7, 0.6, "brow"))
        b.append(B(side * 1.4, 15.3, -4.7, 1.8, 0.7, 0.6, "brow"))
    # mouth, tongue and teeth
    b.append(B(0, 8.9, -4.6, 7.6, 3.2, 0.3, "mouth"))
    b.append(B(0.8, 8.94, -4.75, 2.6, 1.0, 0.3, "tongue"))
    for side in (1, -1):
        b.append(B(side * 2.6, 10.5, -4.75, 1.0, 1.58, 0.4, "tooth"))    # fangs
        b.append(B(side * 2.6, 10.0, -4.75, 0.5, 0.52, 0.4, "tooth"))
        b.append(B(side * 3.25, 8.92, -4.75, 0.9, 1.5, 0.4, "tooth"))    # tusks
    for cx in (-1.3, 0.0, 1.3):
        b.append(B(cx, 11.2, -4.75, 0.8, 0.88, 0.4, "tooth"))
    b.append(B(-1.8, 8.92, -4.75, 0.8, 0.8, 0.4, "tooth"))
    for bx in b:
        assert min(bx[3] - bx[0], bx[4] - bx[1], bx[5] - bx[2]) > 0.01, bx
    return dezfight(b)


BOXES = monster_boxes()


# ---------------------------------------------------------------- Roblox script

def write_lua(path):
    rows = []
    for x0, y0, z0, x1, y1, z1, c in BOXES:
        rows.append('\t{%.3f, %.3f, %.3f, %.3f, %.3f, %.3f, "%s"},' % (x0, y0, z0, x1, y1, z1, c))
    colors = []
    for n, (r, g, bl, mat) in COLORS.items():
        colors.append('\t%s = {Color3.fromRGB(%d, %d, %d), Enum.Material.%s},' % (n, r, g, bl, mat))
    lua = """-- Cube Monster: paste all of this into View -> Command Bar and press Enter.
-- Builds a blocky square-headed monster from anchored Parts in front of the camera.
-- Generated by tools/cube_monster.py.

local SCALE = 1          -- 1 = about 21 studs tall. 0.4 is player-sized.
local PARENT = workspace

local COLORS = {
%s
}

-- {x0, y0, z0, x1, y1, z1, color} in studs, origin at the feet, facing -Z
local BOXES = {
%s
}

local cam = workspace.CurrentCamera
local look = cam.CFrame.LookVector
local flat = Vector3.new(look.X, 0, look.Z)
if flat.Magnitude < 0.01 then flat = Vector3.new(0, 0, -1) end
flat = flat.Unit
local spot = cam.CFrame.Position + flat * 40 * math.max(SCALE, 0.5)
local hit = workspace:Raycast(spot + Vector3.new(0, 200, 0), Vector3.new(0, -1000, 0))
local ground = hit and hit.Position or Vector3.new(spot.X, 0, spot.Z)
-- origin's -Z (LookVector) points back at the camera, so the monster's -Z face looks at you
local origin = CFrame.lookAt(ground, ground - flat)

local model = Instance.new("Model")
model.Name = "CubeMonster"
for i, b in ipairs(BOXES) do
	local p = Instance.new("Part")
	p.Name = b[7]
	p.Anchored = true
	p.TopSurface = Enum.SurfaceType.Smooth
	p.BottomSurface = Enum.SurfaceType.Smooth
	p.Size = Vector3.new(b[4] - b[1], b[5] - b[2], b[6] - b[3]) * SCALE
	local c = Vector3.new(b[1] + b[4], b[2] + b[5], b[3] + b[6]) / 2 * SCALE
	p.CFrame = origin * CFrame.new(c)
	p.Color = COLORS[b[7]][1]
	p.Material = COLORS[b[7]][2]
	p.Parent = model
end
model.WorldPivot = origin
model.Parent = PARENT
game:GetService("Selection"):Set({model})
print("CubeMonster built with " .. #BOXES .. " parts")
""" % ("\n".join(colors), "\n".join(rows))
    with open(path, "w") as f:
        f.write(lua)


write_lua(os.path.join(OUT, "CubeMonster.lua"))
print("wrote CubeMonster.lua,", len(BOXES), "boxes")

# ---------------------------------------------------------------- Blender

import bpy  # noqa: E402

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

NAMES = list(COLORS)
CELL_PX = 8
SIZE = 4 * CELL_PX   # 4 x 4 colour cells


def make_palette():
    img = bpy.data.images.new("CubeMonster_palette", SIZE, SIZE, alpha=False)
    px = [0.0] * (SIZE * SIZE * 4)
    for k, n in enumerate(NAMES):
        r, g, bl = COLORS[n][:3]
        cx, cy = k % 4, k // 4
        for y in range(cy * CELL_PX, (cy + 1) * CELL_PX):
            for x in range(cx * CELL_PX, (cx + 1) * CELL_PX):
                i = (y * SIZE + x) * 4
                px[i:i + 4] = [r / 255, g / 255, bl / 255, 1.0]
    img.pixels = px
    path = os.path.join(OUT, "CubeMonster_palette.png")
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    img.filepath = path
    return img


def uv_for(name):
    k = NAMES.index(name)
    return ((k % 4 + 0.5) / 4, (k // 4 + 0.5) / 4)


def to_blender(p):
    x, y, z = p
    return (x, -z, y)


CUBE_FACES = ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3))

img = make_palette()
mat = bpy.data.materials.new("CubeMonster")
mat.use_nodes = True
nt = mat.node_tree
bsdf = nt.nodes["Principled BSDF"]
tex = nt.nodes.new("ShaderNodeTexImage")
tex.image = img
tex.interpolation = "Closest"
nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
bsdf.inputs["Roughness"].default_value = 0.6

verts, faces, uvs = [], [], []
for x0, y0, z0, x1, y1, z1, c in BOXES:
    base = len(verts)
    for k in range(8):
        verts.append(to_blender((x1 if k & 1 else x0, y1 if k & 2 else y0, z1 if k & 4 else z0)))
    for f in CUBE_FACES:
        faces.append(tuple(base + i for i in reversed(f)))   # outward normals
        uvs.append(uv_for(c))

me = bpy.data.meshes.new("CubeMonster")
me.from_pydata(verts, [], faces)
uvl = me.uv_layers.new(name="UVMap")
for poly in me.polygons:
    for li in poly.loop_indices:
        uvl.data[li].uv = uvs[poly.index]
me.update()
me.materials.append(mat)
monster = bpy.data.objects.new("CubeMonster", me)
scene.collection.objects.link(monster)

# exports (mesh only, before the preview scene is added)
bpy.ops.object.select_all(action="DESELECT")
monster.select_set(True)
bpy.context.view_layer.objects.active = monster
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, "CubeMonster.glb"), export_format="GLB",
                          use_selection=True)
bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, "CubeMonster.fbx"), use_selection=True,
                         path_mode="COPY", embed_textures=True)

# preview scene
world = bpy.data.worlds.new("Sky")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs[0].default_value = (0.62, 0.78, 1.0, 1)
bg.inputs[1].default_value = 0.8
sun_data = bpy.data.lights.new("Sun", "SUN")
sun_data.energy = 3.4
sun_data.angle = math.radians(6)
sun = bpy.data.objects.new("Sun", sun_data)
sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(200))
scene.collection.objects.link(sun)

floor_me = bpy.data.meshes.new("Floor")
floor_me.from_pydata([(-2000, -2000, 0), (2000, -2000, 0), (2000, 2000, 0), (-2000, 2000, 0)], [], [(0, 1, 2, 3)])
floor_mat = bpy.data.materials.new("Floor")
floor_mat.use_nodes = True
floor_mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.42, 0.36, 0.5, 1)
floor_me.materials.append(floor_mat)
floor = bpy.data.objects.new("Floor", floor_me)
scene.collection.objects.link(floor)

scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 96
scene.cycles.max_bounces = 4
scene.cycles.use_denoising = False
scene.render.resolution_x = 900
scene.render.resolution_y = 1000
scene.view_settings.view_transform = "Standard"
scene.view_settings.exposure = -0.3

cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam


def aim(loc, target):
    cam.location = loc
    d = [target[i] - loc[i] for i in range(3)]
    yaw = math.atan2(d[1], d[0]) - math.pi / 2
    pitch = math.atan2(math.hypot(d[0], d[1]), -d[2])
    cam.rotation_euler = (pitch, 0, yaw)


shots = []
for name, loc in (("front", (0, 52, 13)), ("three_quarter", (-34, 40, 17))):
    aim(loc, (0, 0, 10.5))
    path = os.path.join(OUT, "_shot_%s.png" % name)
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    shots.append(path)

monster.select_set(False)
floor.hide_render = True
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "CubeMonster.blend"))

try:
    from PIL import Image
    ims = [Image.open(p) for p in shots]
    sheet = Image.new("RGB", (sum(i.width for i in ims), max(i.height for i in ims)))
    x = 0
    for im in ims:
        sheet.paste(im, (x, 0))
        x += im.width
    sheet.save(os.path.join(OUT, "CubeMonster_preview.png"))
    for p in shots:
        os.remove(p)
except ImportError:
    print("Pillow not installed: left the single shots in monster/")
print("done")
