"""Build the Grim Reaper in Blender: preview renders, rig data for the Roblox build
script and the FBX.

    python blender/build_boss.py <out_dir> [--fbx=out.fbx] [--samples=48] [--size=900] [--no-render]
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import reaper  # noqa: E402,I001
import plib  # noqa: E402
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

rs = plib.rs
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
OUT = os.path.abspath(args[0])
OPTS = dict(a[2:].split("=", 1) if "=" in a else (a[2:], "1") for a in args[1:] if a.startswith("--"))
SAMPLES = int(OPTS.get("samples", 48))
SIZE = int(OPTS.get("size", 900))
os.makedirs(OUT, exist_ok=True)

scene = rs.reset_scene()
rs.setup_world(scene)
rs.setup_render(scene, SIZE, int(SIZE * 1.15), samples=SAMPLES, transparent=True)

p = plib.Prop("Reaper", None, "Boss")
reaper.build(p)
coll = bpy.data.collections.new("Reaper")
scene.collection.children.link(coll)
objs, info = p.build(coll)
bones = {}
for q in info["Parts"]:
    bones.setdefault(q["Model"], []).append(q["Name"])
print("parts %d, triangles %d, top %.2f, bottom %.2f" % (len(info["Parts"]), info["Tris"], info["Top"], info["Bottom"]))
for b, names in bones.items():
    print("  %-14s %s" % (b, ", ".join(names)))
missing = [m[2] for m in reaper.RIG if m[2] not in bones]
if missing:
    raise SystemExit("bones with no parts: %s" % missing)
rig = {"Parts": info["Parts"], "Rig": [{"Motor": m, "Part0": a, "Part1": b, "Pivot": list(c)} for m, a, b, c in reaper.RIG],
       "HRP": {"Center": list(reaper.HRP_CENTER), "Size": list(reaper.HRP_SIZE)},
       "Attachments": [{"Name": n, "Bone": b, "Position": list(pos)} for n, b, pos in reaper.ATTACHMENTS],
       "Tris": info["Tris"], "Top": info["Top"], "Bottom": info["Bottom"]}
with open(os.path.join(OUT, "rig.json"), "w") as f:
    json.dump(rig, f, indent=1)

if "no-render" not in OPTS:
    lo, hi = rs.bounds(objs)
    c = (lo + hi) / 2
    cam = rs.add_camera(scene, (0, -60, 0), c, ortho=(hi.z - lo.z) * 1.12)
    # the reaper faces Roblox -Z, which is Blender +Y
    for tag, yaw, pitch in (("front", 200, 8), ("three_quarter", 225, 12), ("side", 270, 6), ("back", 25, 10)):
        d = Vector((math.sin(math.radians(yaw)) * math.cos(math.radians(pitch)),
                    -math.cos(math.radians(yaw)) * math.cos(math.radians(pitch)), math.sin(math.radians(pitch))))
        rs.look_at(cam, c + d * 80, c)
        rs.render(scene, os.path.join(OUT, "reaper_%s.png" % tag))
    # head close-up
    hc = Vector((0, 0.6, 17.6))
    cam.data.ortho_scale = 7.5
    d = Vector((math.sin(math.radians(205)), -math.cos(math.radians(205)), 0.12)).normalized()
    rs.look_at(cam, hc + d * 60, hc)
    rs.render(scene, os.path.join(OUT, "reaper_head.png"))

if "fbx" in OPTS:
    sys.path.insert(0, reaper.PROPS_BLENDER)
    import export_fbx  # noqa: E402
    export_fbx.export(scene, [(coll, objs, info)], OPTS["fbx"])
