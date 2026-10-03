"""Quality check (every island theme): drop a ray from the base of every island prop onto the deformed terrain
mesh (+ path tiles) and report anything floating over a receded cliff edge.

    blender -b -P tools/qa_island.py -- <repo-root>
"""
import collections
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ROOT = os.path.abspath(argv[0] if argv else ".")
sys.path.insert(0, os.path.join(ROOT, "gen"))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import terrainmesh  # noqa: E402
from island import build_island  # noqa: E402
from themes import ORDER, THEMES  # noqa: E402


def qa(theme):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    coll = bpy.data.collections.new("qa")
    bpy.context.scene.collection.children.link(coll)
    m = build_island(theme)
    objs = terrainmesh.build_island_terrain(m, coll, "/tmp")
    # path tiles + shallows as plain boxes
    import bmesh  # noqa: E402
    bm = bmesh.new()
    for gname, boxes in m["groups"]:
        if gname not in ("Paths", "Shallows"):
            continue
        for (x0, y0, z0, x1, y1, z1, c) in boxes:
            if x1 - x0 > 500:
                continue
            r = bmesh.ops.create_cube(bm, size=1)
            for v in r["verts"]:
                lx, ly, lz = v.co
                v.co = ((x0 + x1) / 2 + lx * (x1 - x0), -((z0 + z1) / 2 - ly * (z1 - z0)), (y0 + y1) / 2 + lz * (y1 - y0))
    me = bpy.data.meshes.new("boxes")
    bm.to_mesh(me)
    coll.objects.link(bpy.data.objects.new("boxes", me))
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    scene = bpy.context.scene

    R = THEMES[theme]["rocks"]
    SKIP = {"Dock", "Rowboat", R["stack"], R["stack_big"], R["stack_small"], "LavaGlow"}
    SUNK = {R["crag"], R["rocks"], R["ledge"], R["arch"]}   # placed partly below ground on purpose
    bad = collections.Counter()
    total = collections.Counter()
    worst = []
    for p in m["props"]:
        name, x, y, z = p[0], p[1], p[2], p[3]
        if name in SKIP or y < 1:
            continue
        total[name] += 1
        lift = 3.0 if name in SUNK else 0.6
        origin = Vector((x, -z, y + lift))
        hit, loc, n, i, ob, mat = scene.ray_cast(dg, origin, Vector((0, 0, -1)), distance=200)
        gap = (y - loc.z) if hit else 99
        # inside a bulging cliff / slightly sunk? then the first surface straight up faces up
        up_hit, up_loc, up_n, *_ = scene.ray_cast(dg, origin, Vector((0, 0, 1)), distance=200)
        if up_hit and up_n.z > 0:
            continue
        if gap > 1.0:
            bad[name] += 1
            worst.append((round(gap, 1), name, x, z))
    print(m["map"], "QA floating props (base > 1 stud above terrain):", sum(bad.values()), "of", sum(total.values()))
    for k, v in bad.most_common():
        print("   %-14s %3d / %d" % (k, v, total[k]))
    print("   worst:", sorted(worst, reverse=True)[:8])
    # how well do the mesh tops match the collision column heights?
    cells = {(i, j): t for i, j, t, k, sf in m["mesh_cells"]}
    errs = []
    for (i, j), t in list(cells.items())[::7]:
        x, z = (i - m["N"] / 2 + 0.5) * m["cell"], (j - m["N"] / 2 + 0.5) * m["cell"]
        hit, loc, *_ = scene.ray_cast(dg, Vector((x, -z, t + 30)), Vector((0, 0, -1)), distance=200)
        if hit and abs(loc.z - t) < 6:
            errs.append(abs(loc.z - t))
    errs.sort()
    print("QA top height vs collision: median %.2f, 95%% %.2f studs (%d samples)" % (
        errs[len(errs) // 2], errs[int(len(errs) * 0.95)], len(errs)))


for theme in ([a for a in argv[1:] if a in THEMES] or ORDER):
    qa(theme)
