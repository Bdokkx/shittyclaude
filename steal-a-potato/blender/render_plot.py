"""Preview renders of the plot kit (4.2).

    python blender/render_plot.py <outdir> [shots=tiers,tier,misc,seeds] [w=1600] [samples=24]

  tiers   the four fence tiers side by side as you'd see them across the yard
  tier    one picture per tier: a run of posts and rails with its GateArch and a potato for scale
  misc    Soil (with a potato on it), Mound, UpgradeBoard
  seeds   the eight seeds (bodies untinted, as built) and the same eight tinted
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy  # noqa: E402,I001
import numpy as np  # noqa: E402

import spsblend as SB  # noqa: E402
import spsgeo as G  # noqa: E402
import spslib  # noqa: E402
import rbxscene as rs  # noqa: E402
from spsgeo import CF  # noqa: E402

import render_spuds as RS  # noqa: E402
from potato import plotkit as PK  # noqa: E402
from potato import spuds  # noqa: E402


def move(model, cf_):
    """Place a built Model (made at the origin) at cf_."""
    for n in model.walk():
        if n.kind == "Part":
            n.p["cf"] = cf_ * n.p["cf"]


def fence_run(sc, parent, name, x0, z0, posts=4, gate=True):
    st = PK.TIERS[name]
    f = sc.folder(parent, name)
    for i in range(posts):
        p = PK.fence_post(sc, f, name, st)
        move(p, CF((x0 + i * PK.SPAN, 0, z0)))
    for i in range(posts - 1):
        r = PK.fence_rail(sc, f, name, st)
        move(r, CF((x0 + (i + 0.5) * PK.SPAN, 0, z0)))
    if gate:
        g = PK.gate_arch(sc, f, name, st)
        move(g, CF((x0 + (posts - 1) * PK.SPAN + 6.25, 0, z0)))
    return f


def render(sc, keep, path, w, h, samples, pos, tgt, fov=34.0, ground=(0.0, 0.0)):
    scene = RS.scene_for(sc, keep, w, h, samples, ground_at=ground)
    RS.cam(scene, pos, tgt, fov=fov)
    rs.render(scene, path)
    return scene


def everything(sc):
    return {id(n) for n in sc.root.walk() if n.kind == "Part"}


def shot_tiers(out, w, samples):
    sc = spslib.Scene("Kit")
    for i, name in enumerate(PK.TIER_ORDER):
        fence_run(sc, sc.root, name, -12.0, i * 12.0, posts=3)
    keep = everything(sc)
    p = os.path.join(out, "plot_tiers.png")
    render(sc, keep, p, w, int(w * 0.6), samples, (-34.0, 17.0, -24.0), (2.0, 3.0, 17.0), fov=40.0,
           ground=(0.0, 18.0))
    return RS.label(p, [])


def shot_tier(out, w, samples):
    files = []
    for name in PK.TIER_ORDER:
        sc = spslib.Scene("Kit")
        fence_run(sc, sc.root, name, -12.0, 0.0, posts=3)
        k = spuds.SpudKind()
        m = k.build(sc, sc.root, CF((-5.0, 0, -3.0)))
        keep, restore = RS.pose_models([m], 10)
        mids = {id(x) for x in m.walk()}
        keep |= {id(n) for n in sc.root.walk() if n.kind == "Part" and id(n) not in mids}
        p = os.path.join(out, "plot_%s.png" % name)
        render(sc, keep, p, w, int(w * 0.5), samples, (-2.0, 10.0, -31.0), (0.5, 4.6, 0.0), fov=38.0)
        restore()
        files.append(RS.label(p, [((w * 0.5, 30), name)]))
    return files


def shot_misc(out, w, samples):
    sc = spslib.Scene("Kit")
    s = PK.soil(sc, sc.root)
    move(s, CF((-7.0, 0, 0)))
    k = spuds.SpudKind()
    m = k.build(sc, sc.root, CF((-7.0, 0.62, 0)))
    md = PK.mound(sc, sc.root)
    move(md, CF((0.0, 0, 0)))
    sd = PK.seed(sc, sc.root, "Meadow")
    move(sd, CF((0.0, 0.74, 0)))
    ub = PK.upgrade_board(sc, sc.root)
    move(ub, CF((7.5, 0, 0)))
    keep, restore = RS.pose_models([m], 3)
    mids = {id(x) for x in m.walk()}
    keep |= {id(n) for n in sc.root.walk() if n.kind == "Part" and id(n) not in mids}
    p = os.path.join(out, "plot_misc.png")
    render(sc, keep, p, w, int(w * 0.5), samples, (2.0, 9.0, -17.0), (0.5, 2.6, 0.0), fov=40.0)
    restore()
    return RS.label(p, [])


def shot_seeds(out, w, samples):
    sc = spslib.Scene("Kit")
    tints = ["d39a52", "e8c27a", "6aa84f", "dff1ff", "c0392b", "b67cff", "ff9cc8", "3d4f9f"]
    for row in range(2):
        for i, a in enumerate(PK.AREAS):
            sd = PK.seed(sc, sc.root, a)
            move(sd, CF(((3.5 - i) * 2.6, 0, row * 3.2)))
            if row == 1:
                for n in sd.walk():
                    if n.kind == "Part" and n.name == "Body":
                        n.p["color"] = tuple(int(tints[i][j:j + 2], 16) for j in (0, 2, 4))
    keep = everything(sc)
    p = os.path.join(out, "plot_seeds.png")
    render(sc, keep, p, w, int(w * 0.45), samples, (0.0, 7.0, -14.0), (0.0, 1.4, 1.6), fov=40.0)
    return RS.label(p, [])


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    opts = dict(a.split("=", 1) for a in sys.argv[2:] if "=" in a)
    w = int(opts.get("w", 1600))
    samples = int(opts.get("samples", 24))
    for s in opts.get("shots", "tiers,tier,misc,seeds").split(","):
        {"tiers": shot_tiers, "tier": shot_tier, "misc": shot_misc, "seeds": shot_seeds}[s](out, w, samples)


if __name__ == "__main__":
    main()
