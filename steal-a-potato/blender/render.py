"""Preview renders of the potato map (Cycles, a Roblox-like 70 degree camera, blue sky, high sun).

    python blender/render.py <outdir> [views=overview,corridor,area1,...] [w=1280] [samples=24]
                             [areas=1,2] ["cams=name:x,y,z:tx,ty,tz;..."]

Named views: overview (0, 60, 200) -> (0, 0, -100); corridor (0, 7, -40) north up the corridor;
area1..area8 at eye height (5.5) in the middle of each area looking north; gate, yard, plots.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy  # noqa: E402,I001
import numpy as np  # noqa: E402
from mathutils import Vector  # noqa: E402

import spsblend as SB  # noqa: E402
import rbxscene as rs  # noqa: E402
from potato import layout as L  # noqa: E402

FOV = 70.0
SKY = (0.32, 0.62, 1.0)


def views():
    v = {"overview": ((0, 60, 200), (0, 0, -100)), "corridor": ((0, 7, -40), (0, 6, -400)),
         "gate": ((0, 14, 60), (0, 14, -10)), "yard": ((0, 70, 250), (0, 0, 90)),
         "yard_west": ((40, 30, 200), (-70, 0, 120)), "stalls": ((0, 12, 70), (0, 6, 20))}
    for n in range(1, L.N_AREAS + 1):
        zs, zn = L.area_z(n)
        v["area%d" % n] = ((0, 5.5, zs - 30), (0, 5.0, zn))
        v["area%d_back" % n] = ((0, 5.5, zn + 30), (0, 5.0, zs))
    v["kit_seeds"] = ((12, -496.6, -9.5), (12, -499.0, 0))
    v["kit_fences"] = ((12, -478, -14), (12, -496, 28))
    v["kit_misc"] = ((-2, -494, -14), (2, -498.5, 3))
    v["kit_roots"] = ((-14, -494, -12), (-26, -498.5, 0))
    return v


def camera(scene, pos, tgt):
    p, t = SB.rb2bl(np.array(pos, float)), SB.rb2bl(np.array(tgt, float))
    cam = rs.add_camera(scene, tuple(p), tuple(t), lens=30)
    cam.data.sensor_fit = "VERTICAL"
    cam.data.angle = math.radians(FOV)
    cam.data.clip_end = 5000
    return cam


def light(scene):
    rs.setup_world(scene, color=SKY, strength=0.85, key=3.6, key_from=(-0.35, 0.3, 0.88), fill=0.6,
                   fill_from=(0.6, -0.5, 0.4), rim=0.8, rim_from=(0.2, -0.9, 0.4))


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    opts = dict(a.split("=", 1) for a in sys.argv[2:] if "=" in a)
    w = int(opts.get("w", 1280))
    h = w * 9 // 16
    samples = int(opts.get("samples", 24))
    areas = [int(x) for x in opts["areas"].split(",")] if "areas" in opts else None
    from potato import build
    kit_only = opts.get("kit") == "1"
    sc = build.build(areas=areas, kit=kit_only, roots=kit_only and opts.get("roots", "1") == "1",
                     showcase=kit_only)
    vs = views()
    if "cams" in opts:
        for spec in opts["cams"].split(";"):
            nm, a, b = spec.split(":")
            vs[nm] = (tuple(float(x) for x in a.split(",")), tuple(float(x) for x in b.split(",")))
    want = opts["views"].split(",") if "views" in opts else ["overview", "corridor", "area1", "area2"]
    scene = SB.reset()
    coll = bpy.data.collections.new("Map")
    scene.collection.children.link(coll)
    if kit_only:
        SB.realize(sc, coll, filter_fn=lambda n: n.top() == "PotatoKit")
        import spsgeo as G_
        floor = G_.box(400, 1.0, 400, (40, -500.5, 60))
        me = bpy.data.meshes.new("floor")
        me.from_pydata(SB.rb2bl(np.array(floor.v)).tolist(), [], floor.f)
        me.materials.append(SB.material((120, 196, 90), "SmoothPlastic", 0.0))
        coll.objects.link(bpy.data.objects.new("floor", me))
    else:
        SB.realize(sc, coll)
    light(scene)
    rs.setup_render(scene, w, h, samples=samples, bloom=True)
    for name in want:
        pos, tgt = vs[name]
        camera(scene, pos, tgt)
        p = os.path.join(out, "%s.png" % name)
        rs.render(scene, p)
        from PIL import Image
        Image.open(p).convert("RGB").save(p[:-4] + ".jpg", quality=90)
        os.remove(p)
        print("saved", p[:-4] + ".jpg", flush=True)


if __name__ == "__main__":
    main()
