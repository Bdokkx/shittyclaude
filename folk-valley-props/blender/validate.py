"""Check every prop before export:

  * every visible part of the old prop still has a part with its name (the game
    may look parts up by name), materials from the allowed list
  * triangle count (warns above 5,000)
  * Top / Bottom compared with the old attributes
  * no z-fighting: overlapping triangles of different parts lying in the same
    plane and facing the same way (Roblox flickers between them)

    python blender/validate.py --orig=<props.json> [--ids=A,B]
"""
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plib  # noqa: E402,I001
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import pdefs  # noqa: E402

rs = plib.rs
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
OPTS = dict(a[2:].split("=", 1) if "=" in a else (a[2:], "1") for a in args if a.startswith("--"))
IDS = OPTS["ids"].split(",") if "ids" in OPTS else list(pdefs.ORDER)
KEEP_VISIBLE = {"Trapdoor": {"Void"}}


def tri_area2(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1])


def clip(poly, a, b):
    out = []
    n = len(poly)
    for i in range(n):
        p, q = poly[i], poly[(i + 1) % n]
        fp, fq = tri_area2(a, b, p), tri_area2(a, b, q)
        if fp >= 0:
            out.append(p)
        if (fp >= 0) != (fq >= 0):
            t = fp / (fp - fq)
            out.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
    return out


def overlap_area(t1, t2):
    poly = list(t1)
    for i in range(3):
        poly = clip(poly, t2[i], t2[(i + 1) % 3])
        if len(poly) < 3:
            return 0.0
    return abs(sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1]
                   for i in range(len(poly)))) / 2


def zfight(objs, min_area=4e-4):
    tris = []
    for ob in objs:
        me = ob.data
        me.calc_loop_triangles()
        for lt in me.loop_triangles:
            vs = [me.vertices[i].co.copy() for i in lt.vertices]
            n = (vs[1] - vs[0]).cross(vs[2] - vs[0])
            if n.length < 1e-9:
                continue
            n.normalize()
            tris.append((ob.name, n, vs))
    planes = defaultdict(list)
    for k, (name, n, vs) in enumerate(tris):
        planes[(round(n.x, 2), round(n.y, 2), round(n.z, 2), round(n.dot(vs[0]), 3))].append(k)
    hits = []
    for key, idx in planes.items():
        if len(idx) < 2 or len({tris[k][0] for k in idx}) < 2:
            continue
        n = tris[idx[0]][1]
        u = n.orthogonal().normalized()
        v = n.cross(u)
        flat = []
        for k in idx:
            pts = [(p.dot(u), p.dot(v)) for p in tris[k][2]]
            if tri_area2(*pts) < 0:
                pts = [pts[0], pts[2], pts[1]]
            flat.append((k, pts))
        for i in range(len(flat)):
            for j in range(i + 1, len(flat)):
                if tris[flat[i][0]][0] == tris[flat[j][0]][0]:
                    continue
                a = overlap_area(flat[i][1], flat[j][1])
                if a > min_area:
                    c = sum(tris[flat[i][0]][2], Vector()) / 3
                    hits.append((tris[flat[i][0]][0], tris[flat[j][0]][0], a, (c.x, c.z, -c.y)))
    return hits


orig = plib.load_original(OPTS["orig"])
scene = rs.reset_scene()
fails, warns = 0, 0
for pid in IDS:
    fn, kind = pdefs.PROPS[pid]
    o = plib.Original(orig[pid]) if pid in orig else None
    p = plib.Prop(pid, o, kind)
    fn(p, o)
    coll = bpy.data.collections.new(pid)
    scene.collection.children.link(coll)
    objs, info = p.build(coll)
    msgs = []
    names = {q["Name"] for q in info["Parts"]}
    if o is not None:
        for c in o.node["children"]:
            sub = [c] if c["class"] != "Model" else c["children"]
            for d in sub:
                vis = d.get("props", {}).get("Transparency", {}).get("Float32", 0) < 0.99
                if vis and "Size" in d["props"] and d["name"] not in names and d["name"] not in KEEP_VISIBLE.get(pid, ()):
                    msgs.append("FAIL old part %r has no new part with its name" % d["name"])
        if "Top" in o.attrs:
            sc = o.node["props"].get("Scale", {}).get("Float32", 1.0)
            t, b = info["Top"] / sc, info["Bottom"] / sc
            span_old = o.attrs["Top"] - o.attrs["Bottom"]
            if abs((t - b) - span_old) > 0.2 * max(span_old, 0.5):
                msgs.append("WARN height %.2f vs old %.2f" % (t - b, span_old))
    for q in info["Parts"]:
        if q["Material"] not in plib.MATERIALS:
            msgs.append("FAIL material %s on %s" % (q["Material"], q["Name"]))
    if info["Tris"] > 5000:
        msgs.append("WARN %d triangles" % info["Tris"])
    for a, b, area, c in zfight(objs)[:4]:
        msgs.append("FAIL z-fighting %s / %s (%.4f sq studs) near (%.2f, %.2f, %.2f)" % (a, b, area, *c))
    fails += sum(1 for m in msgs if m.startswith("FAIL"))
    warns += sum(1 for m in msgs if m.startswith("WARN"))
    print("%-16s %5d tris %s" % (pid, info["Tris"], "ok" if not msgs else ""))
    for m in msgs:
        print("    " + m)
    for ob in objs:
        me = ob.data
        bpy.data.objects.remove(ob)
        bpy.data.meshes.remove(me)
print("%d props: %d failing checks, %d warnings" % (len(IDS), fails, warns))
