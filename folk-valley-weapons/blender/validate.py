"""Check every weapon against the build contract before export:

  * length (Top - Bottom) inside its class range, Top > 0 > Bottom
  * at most 7 visible parts (8 with the Handle), unique part names, allowed materials
  * triangle count (warns above 3,000, fails above 6,000)
  * an Fx attachment on Epic, Legendary, Limited and Mythic weapons (and only there)
  * no z-fighting: overlapping triangles that lie in the same plane, within a part or
    between parts (Roblox flickers between them)

    python blender/validate.py [--ids=A,B]
"""
import math
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy  # noqa: E402,I001
from mathutils import Vector  # noqa: E402

import defs  # noqa: E402
import rbxscene as rs  # noqa: E402
import wlib  # noqa: E402

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
OPTS = dict(a[2:].split("=", 1) if "=" in a else (a[2:], "1") for a in args if a.startswith("--"))
IDS = OPTS["ids"].split(",") if "ids" in OPTS else list(defs.ORDER)

RANGES = {"Sword": (4.7, 6.4), "Dagger": (3.7, 4.9), "Hammer": (3.6, 7.8)}
MATERIALS = {"SmoothPlastic", "Metal", "Neon", "Glass", "Wood", "Fabric"}
FX_RARITIES = {"Epic", "Legendary", "Limited", "Mythic"}


def tri_area2(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1])


def clip(poly, a, b):
    """Clip a convex polygon by the half-plane left of the directed edge a -> b."""
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
    """Area shared by two 2D triangles (counter-clockwise)."""
    poly = list(t1)
    for i in range(3):
        poly = clip(poly, t2[i], t2[(i + 1) % 3])
        if len(poly) < 3:
            return 0.0
    return abs(sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1]
                   for i in range(len(poly)))) / 2


def zfight(objs, min_area=4e-4):
    """Pairs of overlapping coplanar triangles facing the same way (visible flicker)."""
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
        d = n.dot(vs[0])
        key = (round(n.x, 2), round(n.y, 2), round(n.z, 2), round(d, 3))
        planes[key].append(k)
    hits = []
    for key, idx in planes.items():
        if len(idx) < 2:
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
                    continue      # same part: same colour and material, so nothing flickers
                a = overlap_area(flat[i][1], flat[j][1])
                if a > min_area:
                    c = sum(tris[flat[i][0]][2], Vector()) / 3
                    hits.append((tris[flat[i][0]][0], tris[flat[j][0]][0], a, (c.x, c.z, -c.y)))
    return hits


scene = rs.reset_scene()
failures, warnings = 0, 0
for wid in IDS:
    rarity, kind, fn = defs.WEAPONS[wid]
    w = wlib.Weapon(wid, rarity, kind)
    fn(w)
    coll = bpy.data.collections.new(wid)
    scene.collection.children.link(coll)
    objs, info = w.build(coll)
    problems, notes = [], []
    length = info["Top"] - info["Bottom"]
    lo, hi = RANGES[kind]
    if not lo <= length <= hi:
        problems.append("length %.2f outside %s range %.1f-%.1f" % (length, kind, lo, hi))
    if not info["Top"] > 0 > info["Bottom"]:
        problems.append("Top/Bottom %.2f/%.2f do not straddle the Handle" % (info["Top"], info["Bottom"]))
    names = [p["Name"] for p in info["Parts"]]
    if len(names) > 7:
        problems.append("%d visible parts (max 7 + Handle)" % len(names))
    if len(set(names)) != len(names) or "Handle" in names:
        problems.append("part names not unique / clash with Handle: %s" % names)
    bad = {p["Material"] for p in info["Parts"]} - MATERIALS
    if bad:
        problems.append("materials not allowed: %s" % bad)
    if info["Tris"] > 6000:
        problems.append("%d triangles" % info["Tris"])
    elif info["Tris"] > 3000:
        notes.append("%d triangles" % info["Tris"])
    if (rarity in FX_RARITIES) != bool(info["Fx"]):
        problems.append("Fx attachment %s for %s" % ("missing" if rarity in FX_RARITIES else "unexpected", rarity))
    if wid not in defs.NAMES:
        problems.append("no display name")
    zf = zfight(objs)
    if zf:
        worst = sorted(zf, key=lambda h: -h[2])[:3]
        problems.append("%d coplanar overlaps between parts (z-fighting), e.g. %s" % (
            len(zf), ", ".join("%s/%s %.4f at (%.2f, %.2f, %.2f)" % ((a.split("__")[1], b.split("__")[1], ar) + c)
                               for a, b, ar, c in worst)))
    status = "FAIL" if problems else ("warn" if notes else "ok")
    failures += bool(problems)
    warnings += bool(notes) and not problems
    print("%-4s %-16s %-9s %-6s len=%.2f parts=%d tris=%d %s" % (
        status, wid, rarity, kind, length, len(names), info["Tris"], "; ".join(problems + notes)))
    for ob in objs:
        me = ob.data
        bpy.data.objects.remove(ob)
        bpy.data.meshes.remove(me)
    bpy.data.collections.remove(coll)
print("\n%d weapons, %d failing, %d with warnings" % (len(IDS), failures, warnings))
sys.exit(1 if failures else 0)
