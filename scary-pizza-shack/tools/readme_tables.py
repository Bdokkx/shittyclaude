"""Markdown tables for the README, straight from the scene.

    python tools/readme_tables.py > out/tables.md
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "blender"))

import numpy as np  # noqa: E402

import map_items as I  # noqa: E402
import map_stations as MS  # noqa: E402
import scene_build  # noqa: E402
import spslib  # noqa: E402


def bbox(node, sc):
    pts = []
    for c in node.walk():
        if c.kind == "Part" and c.p["transparency"] < 0.99:
            half = np.abs(c.p["cf"].R) @ (np.array(c.p["size"]) / 2)
            pts += [c.p["cf"].p - half, c.p["cf"].p + half]
        elif c.kind == "MeshPart" and c.p["transparency"] < 0.99:
            g = sc.geoms[c.p["mesh"]]
            V = (c.p["cf"].R @ np.array(g.v).T).T + c.p["cf"].p
            pts += [V.min(0), V.max(0)]
    a = np.array(pts)
    return a.min(0), a.max(0)


def f(v, nd=1):
    s = ("%." + str(nd) + "f") % v
    s = s.rstrip("0").rstrip(".") if "." in s else s
    return "0" if s in ("-0", "") else s


def vec(v, nd=1):
    return "(%s)" % ", ".join(f(x, nd) for x in v)


def compass(look):
    a = math.degrees(math.atan2(look[0], -look[2])) % 360
    names = ["north", "north-east", "east", "south-east", "south", "south-west", "west", "north-west"]
    k = int((a + 22.5) // 45) % 8
    if abs(look[1]) > 0.35:
        return "%s, %s %d deg" % (names[k], "down" if look[1] < 0 else "up", round(abs(math.degrees(math.asin(look[1])))))
    return names[k]


def main():
    sc = scene_build.build()
    moving = {}
    for m, part, how in MS.MOVING:
        moving.setdefault(m, []).append((part, how))
    print("### Stations\n")
    print("| Model | where (centre X, Y, Z) | size (X x Y x Z) | markers | moving parts |")
    print("|---|---|---|---|---|")
    for m in sc.root.get("Stations").children:
        lo, hi = bbox(m, sc)
        c = (lo + hi) / 2
        marks = [n.name for n in m.walk() if n.kind == "Marker"]
        mv = moving.get(m.name, [])
        for sub in m.walk():
            if sub is not m and sub.kind == "Model" and sub.name in moving:
                mv += [("%s.%s" % (sub.name, p), h) for p, h in moving[sub.name]]
        mvs = "; ".join("**%s**: %s" % (p, h) for p, h in mv) or "-"
        print("| %s | %s | %s x %s x %s | %s | %s |" % (m.name, vec(c), f(hi[0] - lo[0]), f(hi[1] - lo[1]),
                                                         f(hi[2] - lo[2]), ", ".join(marks), mvs))
    print("\n### Markers folder\n")
    print("| Marker | position (X, Y, Z) | faces (-Z) |")
    print("|---|---|---|")
    for n in sc.root.get("Markers").children:
        print("| %s | %s | %s |" % (n.name, vec(n.p["cf"].p, 2), compass(n.p["cf"].look)))
    print("\n### Items\n")
    print("| Item | size (X x Y x Z) | tris | parts (mesh names) | notes |")
    print("|---|---|---|---|---|")
    for it in I.all_items():
        s = it.size()
        parts = ", ".join("%s__%s" % (it.prefix, p[0]) for p in it.parts)
        notes = it.desc
        # name markers and joints the description does not already mention
        marks = [m[0] for m in it.markers if m[0] not in it.desc]
        joints = [m[1] for m in it.motors if m[1] not in it.desc]
        if marks:
            notes += "; marker " + ", ".join(marks)
        if joints:
            notes += "; Motor6D " + ", ".join(joints)
        print("| %s | %s x %s x %s | %d | %s | %s |" % (it.name, f(s[0]), f(s[1]), f(s[2]), it.tris(), parts, notes))
    cnt = spslib.part_counts(sc)
    print("\n### Part counts\n")
    print("| folder | parts (Parts + MeshParts + markers) |")
    print("|---|---|")
    for k in ("Shack", "Stations", "Outside", "Items", "Markers"):
        print("| %s | %d |" % (k, cnt[k]))
    print("| **total** | **%d** |" % sum(cnt.values()))


if __name__ == "__main__":
    main()
