"""Build props in Blender: preview tiles, metadata for the Roblox build script, FBX.

    python blender/build.py <out_dir> --orig=<props.json> [--ids=Meteor,Coin] [--fbx=out.fbx]
                            [--samples=48] [--no-render] [--size=600]
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plib  # noqa: E402,I001
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import pdefs  # noqa: E402

rs = plib.rs
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
OUT = os.path.abspath(args[0])
OPTS = dict(a[2:].split("=", 1) if "=" in a else (a[2:], "1") for a in args[1:] if a.startswith("--"))
IDS = OPTS["ids"].split(",") if "ids" in OPTS else list(pdefs.ORDER)
SAMPLES = int(OPTS.get("samples", 48))
SIZE = int(OPTS.get("size", 600))
RENDER = "no-render" not in OPTS
os.makedirs(os.path.join(OUT, "tiles"), exist_ok=True)

orig = {}
for path in OPTS.get("orig", "").split(","):
    if path:
        orig.update(plib.load_original(path))

scene = rs.reset_scene()
rs.setup_world(scene)
rs.setup_render(scene, SIZE, SIZE, samples=SAMPLES, transparent=True)

built = {}
for pid in IDS:
    fn, kind = pdefs.PROPS[pid]
    o = plib.Original(orig[pdefs.SOURCE.get(pid, pid)]) if pdefs.SOURCE.get(pid, pid) in orig else None
    p = plib.Prop(pid, o, kind)
    fn(p, o)
    coll = bpy.data.collections.new(pid)
    scene.collection.children.link(coll)
    objs, info = p.build(coll)
    built[pid] = (coll, objs, info)
    ot = "" if not o or "Top" not in o.attrs else " (was %.2f / %.2f)" % (o.attrs["Top"], o.attrs["Bottom"])
    print("%-16s top=%6.2f bottom=%6.2f%s parts=%d tris=%d" % (pid, info["Top"], info["Bottom"], ot,
                                                            len(info["Parts"]), info["Tris"]))

with open(os.path.join(OUT, "props.json"), "w") as f:
    json.dump([built[i][2] for i in IDS], f, indent=1)
with open(os.path.join(OUT, "npc_meta.json"), "w") as f:
    json.dump({"BODY": pdefs.BODY, "HIDE": pdefs.HIDE}, f, indent=1)

if RENDER:
    cam = rs.add_camera(scene, (0, -30, 0), (0, 0, 0), ortho=8.0)
    for pid in IDS:
        for other, (coll, objs, info) in built.items():
            coll.hide_render = other != pid
        coll, objs, info = built[pid]
        yaw, pitch, zoom = pdefs.VIEW.get(pid, (30, 16, 1.0))
        lo, hi = rs.bounds(objs)
        c = (lo + hi) / 2
        span = max((hi - lo).length * 0.80, 0.4) / zoom
        cam.data.ortho_scale = span * 1.06
        d = Vector((math.sin(math.radians(yaw)) * math.cos(math.radians(pitch)),
                    -math.cos(math.radians(yaw)) * math.cos(math.radians(pitch)), math.sin(math.radians(pitch))))
        rs.look_at(cam, c + d * (span * 4 + 30), c)
        rs.render(scene, os.path.join(OUT, "tiles", pid + ".png"))
        if "back" in OPTS:
            d2 = Vector((-d.x, -d.y, d.z))
            rs.look_at(cam, c + d2 * (span * 4 + 30), c)
            rs.render(scene, os.path.join(OUT, "tiles", pid + "_back.png"))
    for coll, objs, info in built.values():
        coll.hide_render = False

if "fbx" in OPTS:
    import export_fbx  # noqa: E402
    export_fbx.export(scene, [built[i] for i in IDS], OPTS["fbx"])
