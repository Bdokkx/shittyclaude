"""Build the remade Scary Pizza Shack map: scene -> checks -> map.json -> FBX.

    python blender/build_remake.py <outdir>

Writes <outdir>/map.json (everything the Studio script rebuilds), <outdir>/stats.json and
<outdir>/ScaryPizzaShack_Remake.fbx (one white mesh per Model__Part, plus the FV_Axis marker
cubes). Refuses to write anything if a check fails.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import spslib  # noqa: E402
from shack2 import build as B, checks as K  # noqa: E402

BUDGET_IN, BUDGET_OUT = 6000, 12000


def _plain(sc):
    """numpy scalars in attributes and flags become plain Python values (for the JSON)."""
    import numpy as np

    def fix(v):
        if isinstance(v, np.generic):
            return v.item()
        if isinstance(v, dict):
            return {k: fix(x) for k, x in v.items()}
        if isinstance(v, (list, tuple)) and not isinstance(v, np.ndarray):
            return type(v)(fix(x) for x in v)
        return v
    for n in sc.root.walk():
        for key, v in list(n.p.items()):
            if key in ("cf", "hinge") or isinstance(v, np.ndarray):
                continue
            n.p[key] = fix(v)


def main(outdir):
    os.makedirs(outdir, exist_ok=True)
    sc = B.build(items=True)
    import scene_build
    old = scene_build.build(items=False)
    rep = K.run(sc, old, quick=False)
    problems = []
    if rep["budget"]["inside"] > BUDGET_IN or rep["budget"]["outside"] > BUDGET_OUT:
        problems.append("budget %s" % rep["budget"])
    for key in ("grid", "floating", "pierce", "clear", "zfight", "lights", "window", "ceiling_open"):
        if rep[key]:
            problems.append("%s: %d" % (key, len(rep[key])))
    if rep["item_markers"][1]:
        problems.append("item markers off their surface: %s" % rep["item_markers"][1])
    miss, kind, _moved, _opened = rep["contract"]
    if miss or kind:
        problems.append("contract: missing %s, kind changed %s" % (miss, kind))
    seen = {}
    for name in sc.geoms:
        k = "".join(ch for ch in name.lower() if ch.isalnum())
        if k in seen:
            problems.append("mesh names %s and %s collide" % (seen[k], name))
        seen[k] = name
    if problems:
        raise SystemExit("CHECKS FAILED: " + "; ".join(problems))
    _plain(sc)
    spslib.to_json(sc, os.path.join(outdir, "map.json"))
    cnt = spslib.part_counts(sc)
    meta = {"parts": dict(cnt), "total": sum(cnt.values()), "budget": rep["budget"], "props": rep["props"],
            "meshes": len(sc.geoms), "mesh_tris": {k: g.tris() for k, g in sc.geoms.items()}}
    json.dump(meta, open(os.path.join(outdir, "stats.json"), "w"), indent=1)
    print("parts:", dict(cnt), "total", meta["total"], "meshes", meta["meshes"], "budget", rep["budget"])
    import spsblend as SB
    SB.reset()
    SB.export_fbx(sc, os.path.join(outdir, "ScaryPizzaShack_Remake.fbx"))
    return sc


if __name__ == "__main__":
    main(sys.argv[1])
