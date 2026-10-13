"""Preview renders of the plot kit (4.2).

    python blender/render_plot.py <outdir> [shots=tiers,tier,misc,mound,seeds] [w=1600] [samples=24]

  tiers   the four fence tiers side by side as you'd see them across the yard
  tier    one picture per tier: a run of posts and rails with its GateArch and a potato for scale
  misc    SoilHeap (with a seed on it), SoilPatch (with a potato on it), Mound (with a seed in its
          hollow), UpgradeBoard
  mound   the Mound close up: with a seed, empty, and tinted for two areas the way the game does it
          (the Soil, Leaf and Flag bricks set to shade(tint, Shade))
  seeds   the eighteen seeds as built (bodies untinted), and the same eighteen tinted
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
        move(g, CF((x0 + (posts - 1) * PK.SPAN + 9.6, 0, z0)))
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


def labels(scene, w, h, pts):
    """Screen positions of world points (Roblox space), for RS.label."""
    import bpy_extras.object_utils as ou
    import mathutils
    out = []
    for pos, name in pts:
        v = ou.world_to_camera_view(scene, scene.camera, mathutils.Vector(SB.rb2bl(pos)))
        out.append(((v.x * w, (1 - v.y) * h), name))
    return out


def tint(model, soil, leaf, flag):
    """What the game does per area: the bricks named Soil, Leaf and Flag take the area's colour,
    each shaded by its own Shade."""
    base = {"Soil": soil, "Leaf": leaf, "Flag": flag}
    for n in model.walk():
        if n.kind == "Part" and n.name in base:
            n.p["color"] = PK.shade(base[n.name], n.p["attrs"].get("Shade", 0.0))


def shot_misc(out, w, samples):
    """plot_misc: the four pieces in use, left to right (+X is on the left from the front);
    plot_soil: SoilHeap and SoilPatch close up, empty and in use."""
    files = []
    sc = spslib.Scene("Kit")
    hp = PK.soil_heap(sc, sc.root)
    move(hp, CF((10.5, 0, 0)))
    sd = PK.seed(sc, sc.root, "Meadow")
    move(sd, CF((10.5, 1.0, 0)))
    pt = PK.soil_patch(sc, sc.root)
    move(pt, CF((3.5, 0, 0)))
    k = spuds.SpudKind()
    m = k.build(sc, sc.root, CF((3.5, 0.22, 0)))
    md = PK.mound(sc, sc.root)
    move(md, CF((-3.5, 0, 0)))
    sd2 = PK.seed(sc, sc.root, "Meadow")
    move(sd2, CF((-3.5, PK.MOUND_FLOOR, 0)))
    ub = PK.upgrade_board(sc, sc.root)
    move(ub, CF((-10.5, 0, 0)))
    keep, restore = RS.pose_models([m], 3)
    mids = {id(x) for x in m.walk()}
    keep |= {id(n) for n in sc.root.walk() if n.kind == "Part" and id(n) not in mids}
    p = os.path.join(out, "plot_misc.png")
    h = int(w * 0.45)
    scene = render(sc, keep, p, w, h, samples, (0.0, 10.5, -22.0), (0.0, 2.2, 0.0), fov=40.0)
    restore()
    texts = labels(scene, w, h, [((10.5, -0.6, -3.4), "SoilHeap"), ((3.5, -0.6, -3.4), "SoilPatch"),
                                 ((-3.5, -0.6, -3.4), "Mound"), ((-10.5, -0.6, -3.4), "UpgradeBoard")])
    files.append(RS.label(p, texts, size=w // 50))

    sc = spslib.Scene("Kit")
    xs = (9.0, 3.0, -3.0, -9.0)
    for x in xs[:2]:
        move(PK.soil_heap(sc, sc.root), CF((x, 0, 0)))
    move(PK.seed(sc, sc.root, "Dunes"), CF((xs[1], 1.0, 0)))
    for x in xs[2:]:
        move(PK.soil_patch(sc, sc.root), CF((x, 0, 0)))
    m = spuds.SpudKind().build(sc, sc.root, CF((xs[3], 0.22, 0)))
    keep, restore = RS.pose_models([m], 1)
    mids = {id(x) for x in m.walk()}
    keep |= {id(n) for n in sc.root.walk() if n.kind == "Part" and id(n) not in mids}
    p = os.path.join(out, "plot_soil.png")
    h = int(w * 0.4)
    scene = render(sc, keep, p, w, h, samples, (0.0, 9.0, -14.5), (0.0, 0.9, 0.5), fov=38.0)
    restore()
    texts = labels(scene, w, h, [((xs[0], -0.6, -3.2), "SoilHeap"), ((xs[1], -0.6, -3.2), "SoilHeap + seed"),
                                 ((xs[2], -0.6, -3.2), "SoilPatch"), ((xs[3], -0.6, -3.2), "SoilPatch + potato")])
    files.append(RS.label(p, texts, size=w // 52))
    return files


AREA_TINTS = (("Sandy Dunes", ("d9a95b", "7f9a3c", "e8403a")), ("Frost Fields", ("e6eef8", "3f9e9a", "4fc3f7")))


def shot_mound(out, w, samples):
    sc = spslib.Scene("Kit")
    xs = (10.5, 3.5, -3.5, -10.5)
    names = ["with a seed", "empty"] + [a + " tint" for a, _ in AREA_TINTS]
    seeds = ("Meadow", None, "Dunes", "Frost")
    for i, x in enumerate(xs):
        md = PK.mound(sc, sc.root)
        if i >= 2:
            tint(md, *AREA_TINTS[i - 2][1])
        move(md, CF((x, 0, 0)))
        if seeds[i]:
            sd = PK.seed(sc, sc.root, seeds[i])
            move(sd, CF((x, PK.MOUND_FLOOR, 0)))
    keep = everything(sc)
    p = os.path.join(out, "plot_mound.png")
    h = int(w * 0.4)
    scene = render(sc, keep, p, w, h, samples, (0.0, 9.5, -16.5), (0.0, 0.9, 0.6), fov=38.0)
    texts = labels(scene, w, h, [((x, -0.8, -3.6), n) for x, n in zip(xs, names)])
    return RS.label(p, texts, size=w // 58)


SEED_TINTS = ("d39a52", "e8c27a", "6aa84f", "4f9a3a", "ff8a5c", "dff1ff", "8a5cc0", "c0392b", "b67cff",
              "9bbf5a", "4da6ff", "ff9cc8", "c9a227", "00e0ff", "f4f8ff", "3d4f9f", "3a3346", "ffd447")


def shot_seeds(out, w, samples):
    files = []
    for tinted in (False, True):
        sc = spslib.Scene("Kit")
        for i, a in enumerate(PK.AREAS):
            row, col = divmod(i, 9)
            sd = PK.seed(sc, sc.root, a)
            move(sd, CF(((4.0 - col) * 2.7, 0, row * 3.4)))
            if tinted:
                for n in sd.walk():
                    if n.kind == "Part" and n.name == "Body":
                        n.p["color"] = PK.hexc(SEED_TINTS[i])
        keep = everything(sc)
        p = os.path.join(out, "plot_seeds_tinted.png" if tinted else "plot_seeds.png")
        h = int(w * 0.45)
        scene = render(sc, keep, p, w, h, samples, (0.0, 8.0, -15.5), (0.0, 1.3, 1.9), fov=40.0)
        texts = labels(scene, w, h, [(((4.0 - i % 9) * 2.7, -0.5, (i // 9) * 3.4 - 1.25), a)
                                     for i, a in enumerate(PK.AREAS) if i < 9])
        texts += labels(scene, w, h, [(((4.0 - i % 9) * 2.7, 3.7, (i // 9) * 3.4), a)
                                      for i, a in enumerate(PK.AREAS) if i >= 9])
        files.append(RS.label(p, texts, size=w // 64))
    return files


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    opts = dict(a.split("=", 1) for a in sys.argv[2:] if "=" in a)
    w = int(opts.get("w", 1600))
    samples = int(opts.get("samples", 24))
    for s in opts.get("shots", "tiers,tier,misc,mound,seeds").split(","):
        {"tiers": shot_tiers, "tier": shot_tier, "misc": shot_misc, "mound": shot_mound,
         "seeds": shot_seeds}[s](out, w, samples)


if __name__ == "__main__":
    main()
