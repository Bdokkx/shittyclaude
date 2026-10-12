"""Write README_Batch2.md: docs/b2_head.md + generated tables + docs/b2_changes.md + docs/b2_foot.md.

    python tools/make_readme_b2.py
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "blender"))

import numpy as np  # noqa: E402

import assets_common  # noqa: E402
import assets_kit as AK  # noqa: E402
import assets_uniforms as AU  # noqa: E402
import build_assets  # noqa: E402


def f(v):
    s = "%.2f" % v
    return s.rstrip("0").rstrip(".")


def bbox(model, sc, skip=("HumanoidRootPart", "Base", "Zone", "Gate", "Handle")):
    pts = []
    for n in model.walk():
        if n.kind not in ("Part", "MeshPart") or n.name in skip or n.p["transparency"] >= 0.99:
            continue
        if n.kind == "MeshPart":
            g = sc.geoms[n.p["mesh"]]
            V = (n.p["cf"].R @ np.array(g.v).T).T + n.p["cf"].p
        else:
            R = n.p["cf"].R
            h = np.abs(R) @ (np.array(n.p["size"]) / 2)
            V = np.array([n.p["cf"].p - h, n.p["cf"].p + h])
        pts.append(V)
    V = np.vstack(pts)
    return V.min(0), V.max(0)


def size_str(lo, hi):
    s = hi - lo
    return "%s x %s x %s" % (f(s[0]), f(s[1]), f(s[2]))


def tris_of(model, sc):
    return sum(sc.geoms[n.p["mesh"]].tris() for n in model.walk() if n.kind == "MeshPart")


def parts_of(model, kinds=("Part", "MeshPart"), skip=()):
    seen = []
    for n in model.walk():
        if n.kind in kinds and n.name not in skip and n.name not in seen:
            seen.append(n.name)
    return seen


def tables(sc):
    out = []
    M = {c.name: c for c in sc.root.children}
    moving = {}
    for path, part, how in assets_common.MOVING:
        moving.setdefault(path.split(".")[-1], []).append((part, how))
    # -- kit
    out.append("### A. CustomerKit (Model, 33 pieces)\n")
    out.append("Every piece: a Model, PrimaryPart `Handle` (invisible 0.4 cube, anchored in the template) at the "
               "centre of the R6 part named in *sits on*; its parts are welded to the Handle. Attributes: "
               "`Category`, `BodyPart`, and `HidesHair` on the Hood.\n")
    out.append("| Piece | category | sits on | size (X x Y x Z) | tris | parts (mesh names) | notes |")
    out.append("|---|---|---|---|---|---|---|")
    for name in AK.ORDER:
        m = M["CustomerKit"].find(name)
        cat, body, fn, notes = AK.KIT[name]
        lo, hi = bbox(m, sc)
        parts = ", ".join("%s (`%s`)" % (n.name, n.p["mesh"]) for n in m.children if n.kind == "MeshPart")
        out.append("| %s | %s | %s | %s | %d | %s | %s |" % (name, cat, body, size_str(lo, hi), tris_of(m, sc),
                                                           parts, notes))
    # -- characters
    out.append("\n### B. Passenger, Watcher, Inspector, InspectorHole\n")
    out.append("| Model | PrimaryPart | size (X x Y x Z) | tris | parts | moving parts |")
    out.append("|---|---|---|---|---|---|")
    for name in ("Passenger", "Watcher", "Inspector", "InspectorHole"):
        m = M[name]
        lo, hi = bbox(m, sc)
        mv = "; ".join("**%s**: %s" % (p, h) for p, h in moving.get(name, [])) or \
             ("R6 joints (RootJoint, Neck, Left/Right Shoulder, Left/Right Hip)" if name in ("Watcher", "Inspector")
              else "-")
        if name == "InspectorHole":
            mv = "the whole Model scales (Model:ScaleTo(width / 8)); Shard1..8 are loose pieces to throw about"
        out.append("| %s | %s | %s | %d | %s | %s |" % (name, m.p["primary"].name, size_str(lo, hi), tris_of(m, sc),
                                                       ", ".join(parts_of(m)), mv))
    # -- vehicles
    out.append("\n### C. Vehicles\n")
    out.append("Sizes are X (width) x Y (height) x Z (length). *body* leaves out the mirrors and the Van's ramp; "
               "*overall* is everything.\n")
    out.append("| Model | body | overall | parts | lights | moving parts |")
    out.append("|---|---|---|---|---|---|")
    for name in ("InspectorCar", "DeliveryTruck", "Van"):
        m = M[name]
        lo, hi = bbox(m, sc)
        blo, bhi = bbox(m, sc, skip=("Base", "Zone", "Gate", "Mirrors", "Ramp"))
        lights = sorted({n.name for n in m.walk() if n.name in ("Headlight", "TailLight", "Beacon", "Bulb")})
        mv = "; ".join("**%s**: %s" % (p, h) for p, h in moving.get(name, []))
        out.append("| %s | %s | %s | %s | %s | %s |" % (name, size_str(blo, bhi), size_str(lo, hi),
                                                       ", ".join(parts_of(m)), ", ".join(lights), mv))
    # -- plushies
    out.append("\n### D. Plushies (Model holding seven Models)\n")
    out.append("| Plush | size (X x Y x Z) | tris | parts (mesh names) | moving parts |")
    out.append("|---|---|---|---|---|")
    for m in M["Plushies"].children:
        lo, hi = bbox(m, sc)
        parts = ", ".join("%s (`%s`)" % (n.name, n.p["mesh"]) for n in m.children if n.kind == "MeshPart")
        mv = "; ".join("**%s**: %s" % (p, h) for p, h in moving.get(m.name, [])) or "-"
        out.append("| %s | %s | %d | %s | %s |" % (m.name, size_str(lo, hi), tris_of(m, sc), parts, mv))
    # -- uniforms
    out.append("\n### E. Uniforms (Model of Accessories)\n")
    out.append("| Accessory | attachment (in Handle) | worn on | size (X x Y x Z) | tris | parts (mesh names) | notes |")
    out.append("|---|---|---|---|---|---|---|")
    accs = [n for n in M["Uniforms"].walk() if n.kind == "Accessory"]
    for a in accs:
        att, fn, notes = AU.UNIFORMS[a.name]
        lo, hi = bbox(a, sc)
        parts = ", ".join("%s (`%s`)" % (n.name, n.p["mesh"]) for n in a.children if n.kind == "MeshPart")
        where = a.name if a.parent.name == "Uniforms" else "%s.%s" % (a.parent.name, a.name)
        out.append("| %s | `%s` | %s | %s | %d | %s | %s |" % (where, att, AU.ATT[att][0], size_str(lo, hi),
                                                             tris_of(a, sc), parts, notes))
    return "\n".join(out) + "\n"


def joint_table():
    import assets_chars as AC
    import assets_r6 as R6
    bodies = (("standard R6", R6.Body()), ("Watcher", AC.WATCHER), ("Inspector", AC.INSPECTOR))
    out = ["| joint (in Part0) | " + " | ".join("%s C0 / C1 position" % n for n, _ in bodies) + " |",
           "|---|" + "---|" * len(bodies)]
    for k, (jn, p0, p1, _) in enumerate(R6.Body().joints()):
        row = []
        for _, b in bodies:
            j = b.joints()[k]
            cfs = b.cfs()
            c0 = j[3]
            c1 = cfs[j[2]].inv() * cfs[j[1]] * c0
            fmt = lambda v: "(%s)" % ", ".join(f(x) for x in v)  # noqa: E731
            row.append("%s / %s" % (fmt(c0.p), fmt(c1.p)))
        out.append("| %s.%s -> %s | %s |" % (p0, jn, p1, " | ".join(row)))
    sizes = ["| part | " + " | ".join(n for n, _ in bodies) + " |", "|---|" + "---|" * len(bodies)]
    for pn in ("Torso", "Head", "Right Arm", "Right Leg"):
        sizes.append("| %s | %s |" % (pn, " | ".join("%s x %s x %s" % tuple(f(v) for v in b.size(pn)) for _, b in bodies)))
    return "\n".join(out) + "\n\nRotations are the standard R6 ones (RootJoint and Neck `CFrame.Angles(-90, 0, 180)` " \
        "in degrees, the right side `0,0,1 / 0,1,0 / -1,0,0`, the left side mirrored).\n\n" + "\n".join(sizes) + "\n"


def main():
    sc = build_assets.build()
    stats = json.load(open(os.path.join(ROOT, "out", "assets_stats.json")))
    head = open(os.path.join(ROOT, "docs", "b2_head.md")).read()
    changes = open(os.path.join(ROOT, "docs", "b2_changes.md")).read()
    foot = open(os.path.join(ROOT, "docs", "b2_foot.md")).read()
    counts = "\n### Part counts\n\n| Model | parts + mesh parts |\n|---|---|\n" + "\n".join(
        "| %s | %d |" % (k, v) for k, v in stats["parts"].items()) + "\n| **total** | **%d** |\n" % stats["total"]
    largest = max(stats["mesh_tris"].items(), key=lambda kv: kv[1])
    text = head + "\n## The models\n\n" + tables(sc) + counts + "\n" + changes + "\n" + foot
    text = text.replace("@@JOINTS@@", joint_table())
    text = text.replace("@@NMESH@@", str(stats["meshes"])).replace("@@TOTAL@@", str(stats["total"]))
    text = text.replace("@@NPARTS@@", str(sum(1 for n in sc.root.walk() if n.kind == "Part")))
    text = text.replace("@@NMESHPARTS@@", str(sum(1 for n in sc.root.walk() if n.kind == "MeshPart")))
    text = text.replace("@@LARGEST@@", "%d triangles (`%s`)" % (largest[1], largest[0]))
    left = sorted(set(re.findall(r"@@[A-Z]+@@", text)))
    if left:
        raise SystemExit("placeholders left: %s" % left)
    open(os.path.join(ROOT, "README_Batch2.md"), "w").write(text)
    print("README_Batch2.md", text.count("\n"), "lines")


if __name__ == "__main__":
    main()
