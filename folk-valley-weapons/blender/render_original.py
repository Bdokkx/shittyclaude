"""Render the weapons from an existing .rbxm (the "before" reference).

    python blender/render_original.py <weapons.rbxm> <out_dir> [Id Id ...]
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import rbxscene as rs  # noqa: E402

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
src, out_dir = args[0], args[1]
only = set(args[2:])
os.makedirs(out_dir, exist_ok=True)

data = rs.dump_rbxm(src)
folder = data[0]
models = [m for m in folder["children"] if m["class"] == "Model" and (not only or m["name"] in only)]

for model in models:
    scene = rs.reset_scene()
    rs.setup_world(scene)
    rs.setup_render(scene, 600, 900, samples=48, transparent=True)
    objs = rs.build_model(model, scene.collection)
    lo, hi = rs.bounds(objs)
    c = (lo + hi) / 2
    yaw, pitch, dist = math.radians(28), math.radians(8), 30
    cam_loc = c + Vector((math.sin(yaw) * math.cos(pitch), -math.cos(yaw) * math.cos(pitch), math.sin(pitch))) * dist
    rs.add_camera(scene, cam_loc, c, ortho=8.5)
    path = os.path.join(out_dir, model["name"] + ".png")
    rs.render(scene, path)
    print("rendered", path)
