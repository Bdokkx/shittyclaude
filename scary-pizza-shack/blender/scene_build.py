"""Assemble the whole map Scene (no Blender needed) and run the checks.

    python blender/scene_build.py [--json out/map.json]
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import spslib  # noqa: E402
import map_shell  # noqa: E402
import map_stations  # noqa: E402

try:
    import map_outside  # noqa: E402
except ImportError:  # while it is being written
    map_outside = None
import map_items  # noqa: E402


def build(outside=True, items=True):
    sc = spslib.Scene()
    for name in ("Shack", "Outside", "Stations", "Items", "Markers"):
        sc.folder(sc.root, name)
    map_stations.MOVING.clear()
    map_shell.build(sc)
    map_stations.build_inside(sc)
    if outside and map_outside is not None:
        map_outside.build(sc)
    if items:
        build_items(sc)
    return sc


def build_items(sc):
    """Item templates in a tidy grid well below the map (anchored Handle, welded meshes)."""
    folder = sc.root.get("Items")
    x, z, row_d = -60.0, -20.0, 0.0
    for it in map_items.all_items():
        lo, hi = it.bbox()
        w, d = hi[0] - lo[0] + 2.0, hi[2] - lo[2] + 2.0
        if x + w > 60:
            x, z, row_d = -60.0, z + row_d, 0.0
        cf = spslib.CF((x - lo[0], -60.0 - lo[1], z - lo[2]))
        map_items.place(sc, folder, it, cf)
        x += w
        row_d = max(row_d, d)


def report(sc):
    cnt = spslib.part_counts(sc)
    total = sum(cnt.values())
    print("parts by folder:", dict(cnt), "total", total)
    bad = spslib.check_grid(sc)
    print("off-grid parts:", len(bad))
    for b in bad[:30]:
        print("   ", b)
    zf = spslib.zfight(sc)
    print("z-fighting faces:", len(zf))
    for z in zf[:40]:
        print("   ", z)
    over_p, over_i, per_item = spslib.mesh_budget(sc)
    print("meshes:", len(sc.geoms), "over budget props:", over_p, "items:", over_i)
    return cnt, bad, zf


if __name__ == "__main__":
    sc = build()
    report(sc)
    if "--json" in sys.argv:
        path = sys.argv[sys.argv.index("--json") + 1]
        spslib.to_json(sc, path)
        print("wrote", path)
