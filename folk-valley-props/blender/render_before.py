"""Render the props in an existing .rbxm (the "before" reference), one PNG each.

    python blender/render_before.py <props.rbxm> <out_dir> [Name Name ...]
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import propscene as ps  # noqa: E402
import bpy  # noqa: E402,F401
from mathutils import Vector  # noqa: E402

try:                                        # same views as the new renders, for before / after sheets
    import pdefs  # noqa: E402
    VIEW = pdefs.VIEW
except Exception:
    VIEW = {}

rs = ps.rs
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
src, out_dir = args[0], args[1]
only = set(args[2:])
os.makedirs(out_dir, exist_ok=True)
folder = rs.dump_rbxm(src)[0]
for model in folder["children"]:
    if model["class"] != "Model" or (only and model["name"] not in only):
        continue
    scene = rs.reset_scene()
    rs.setup_world(scene)
    rs.setup_render(scene, 640, 640, samples=32, transparent=True)
    objs = [o for o, _ in ps.build_model(model, scene.collection)]
    lo, hi = rs.bounds(objs)
    c = (lo + hi) / 2
    yaw, pitch, zoom = VIEW.get(model["name"], (30, 16, 1.0))
    span = max((hi - lo).length * 0.80, 0.4) / zoom
    yaw, pitch = math.radians(yaw), math.radians(pitch)
    loc = c + Vector((math.sin(yaw) * math.cos(pitch), -math.cos(yaw) * math.cos(pitch), math.sin(pitch))) * (span * 4 + 30)
    rs.add_camera(scene, loc, c, ortho=span * 1.06)
    rs.render(scene, os.path.join(out_dir, model["name"] + ".png"))
    print("rendered", model["name"], "span %.2f" % span)
