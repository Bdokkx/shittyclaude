"""Build weapons in Blender: preview tiles, metadata for the Roblox rig, FBX.

    python blender/build.py <out_dir> [--ids=Wooden,Katana] [--fbx=out.fbx] [--samples=64] [--no-render]
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy  # noqa: E402,I001
from mathutils import Vector  # noqa: E402

import rbxscene as rs  # noqa: E402
import wlib  # noqa: E402
import defs  # noqa: E402

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
OUT = os.path.abspath(args[0])
OPTS = dict(a[2:].split("=", 1) if "=" in a else (a[2:], "1") for a in args[1:] if a.startswith("--"))
IDS = OPTS["ids"].split(",") if "ids" in OPTS else list(defs.ORDER)
SAMPLES = int(OPTS.get("samples", 64))
RENDER = "no-render" not in OPTS
os.makedirs(OUT, exist_ok=True)
os.makedirs(os.path.join(OUT, "tiles"), exist_ok=True)

scene = rs.reset_scene()
rs.setup_world(scene)
rs.setup_render(scene, 600, 900, samples=SAMPLES, transparent=True)

built = {}
for wid in IDS:
    rarity, kind, fn = defs.WEAPONS[wid]
    w = wlib.Weapon(wid, rarity, kind)
    fn(w)
    coll = bpy.data.collections.new(wid)
    scene.collection.children.link(coll)
    objs, info = w.build(coll)
    built[wid] = (coll, objs, info)
    print("%-16s %-10s top=%5.2f bottom=%5.2f len=%4.2f parts=%d tris=%d" % (
        wid, rarity, info["Top"], info["Bottom"], info["Top"] - info["Bottom"], len(info["Parts"]), info["Tris"]))

with open(os.path.join(OUT, "weapons.json"), "w") as f:
    json.dump([built[w][2] for w in IDS], f, indent=1)

if RENDER:
    yaw, pitch = math.radians(28), math.radians(8)
    cam = rs.add_camera(scene, (0, -30, 0), (0, 0, 0), ortho=8.5)
    for wid in IDS:
        for other, (coll, objs, info) in built.items():
            coll.hide_render = other != wid
        coll, objs, info = built[wid]
        lo, hi = rs.bounds(objs)
        c = (lo + hi) / 2
        loc = c + Vector((math.sin(yaw) * math.cos(pitch), -math.cos(yaw) * math.cos(pitch), math.sin(pitch))) * 30
        rs.look_at(cam, loc, c)
        rs.render(scene, os.path.join(OUT, "tiles", wid + ".png"))
    if "hero" in OPTS:
        # bigger 3/4 view + a hilt close-up for checking details
        os.makedirs(os.path.join(OUT, "hero"), exist_ok=True)
        scene.render.resolution_x, scene.render.resolution_y = 1000, 1400
        for wid in IDS:
            for other, (coll, objs, info) in built.items():
                coll.hide_render = other != wid
            coll, objs, info = built[wid]
            lo, hi = rs.bounds(objs)
            c = (lo + hi) / 2
            span = max(hi.z - lo.z, (hi.x - lo.x) * 1.4)
            cam.data.ortho_scale = span * 1.08
            yaw2, pitch2 = math.radians(38), math.radians(14)
            loc = c + Vector((math.sin(yaw2) * math.cos(pitch2), -math.cos(yaw2) * math.cos(pitch2), math.sin(pitch2))) * 30
            rs.look_at(cam, loc, c)
            rs.render(scene, os.path.join(OUT, "hero", wid + ".png"))
            # hilt close-up around the grip (origin)
            hc = Vector((0, 0, min(0.3, hi.z)))
            cam.data.ortho_scale = 2.6
            loc = hc + Vector((math.sin(yaw2) * math.cos(pitch2), -math.cos(yaw2) * math.cos(pitch2), math.sin(pitch2))) * 30
            rs.look_at(cam, loc, hc)
            rs.render(scene, os.path.join(OUT, "hero", wid + "_hilt.png"))
        scene.render.resolution_x, scene.render.resolution_y = 600, 900
        cam.data.ortho_scale = 8.5
    for coll, objs, info in built.values():
        coll.hide_render = False

if "fbx" in OPTS:
    import export_fbx  # noqa: E402
    export_fbx.export(scene, [built[w] for w in IDS], OPTS["fbx"])
