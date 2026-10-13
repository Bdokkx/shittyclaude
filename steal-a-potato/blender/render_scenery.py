"""Preview renders of an area's hero and props (Cycles, studs drawn on every Plastic face).

    python blender/render_scenery.py <outdir> area=Jungle [shots=hero,props] [w=1600] [samples=24]

  hero    hero_<Area>.jpg: the hero from the lane, as a player walking past sees it, and
          hero_<Area>_corner.jpg from up on the far corner; a 5-stud player and a potato for scale
  props   props_<Area>.jpg: the props in a row from the front, named, and props_<Area>_top.jpg from
          above the front corner
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
from render_roots import runner  # noqa: E402
from potato import scenery, spuds  # noqa: E402
from potato import scenery_clock, scenery_dino, scenery_haunt, scenery_jungle, scenery_reef  # noqa: E402,F401
from potato import scenery_cloud, scenery_neon, scenery_toy  # noqa: E402,F401


def hexrgb(c):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def move(model, cf_):
    for n in model.walk():
        if n.kind == "Part":
            n.p["cf"] = cf_ * n.p["cf"]


def scene_for(sc, keep, w, h, samples, ground_col, size=400.0, cx=0.0, cz=0.0):
    scene = SB.reset()
    coll = bpy.data.collections.new("S")
    scene.collection.children.link(coll)
    SB.realize(sc, coll, filter_fn=lambda n: id(n) in keep)
    RS.ground(coll, cx, cz, size, ground_col)
    rs.setup_world(scene, color=(0.42, 0.66, 1.0), strength=0.8, key=3.4, key_from=(-0.45, -0.75, 0.75),
                   fill=0.7, fill_from=(0.8, -0.2, 0.3), rim=1.4, rim_from=(0.3, 0.9, 0.5))
    rs.setup_render(scene, w, h, samples=samples, bloom=False)
    try:
        scene.cycles.denoising_prefilter = "NONE"
    except Exception:
        pass
    return scene


def everything(sc):
    return {id(n) for n in sc.root.walk() if n.kind == "Part"}


def footprint(m):
    lo, hi = scenery.bounds([n for n in m.walk() if n.kind == "Part"])
    return lo, hi


def scale_refs(sc, at_runner, at_spud):
    """A 5-stud player and a level-10 potato; returns the ids of their parts to draw."""
    r = runner(sc, CF(np.asarray(at_runner, float), G.ry(-20)))
    m = spuds.SpudKind().build(sc, sc.root)
    keep, _restore = RS.pose_models([m], 10)
    move(m, CF(np.asarray(at_spud, float), G.ry(15)))
    return keep | {id(n) for n in r.walk() if n.kind == "Part"}


def shot_hero(out, area, w, samples):
    A = scenery.AREAS[area]
    files = []
    for view in ("front", "corner"):
        sc = spslib.Scene("Kit")
        hero, _props = scenery.build_area(sc, area)
        keep = {id(n) for n in hero.walk() if n.kind == "Part"}
        lo, hi = footprint(hero)
        keep |= scale_refs(sc, (-7.0, 0.0, lo[2] - 6.0), (6.5, 0.0, lo[2] - 5.0))
        hgt = hi[1]
        h = int(w * 0.5625)
        scene = scene_for(sc, keep, w, h, samples, hexrgb(A.ground))
        if view == "front":
            fov = 34.0
            dist = max(hgt * 0.62 / math.tan(math.radians(fov / 2)), 64.0)
            RS.cam(scene, (0.0, 7.5, lo[2] - dist), (0.0, hgt * 0.42, 0.0), fov=fov)
            p = os.path.join(out, "hero_%s.png" % area)
        else:
            RS.cam(scene, (-58.0, hgt * 0.75 + 14.0, lo[2] - 52.0), (0.0, hgt * 0.32, 1.0), fov=36.0)
            p = os.path.join(out, "hero_%s_corner.png" % area)
        rs.render(scene, p)
        files.append(RS.label(p, []))
    return files


def shot_props(out, area, w, samples):
    A = scenery.AREAS[area]
    sc = spslib.Scene("Kit")
    hero, props = scenery.build_area(sc, area)
    widths = []
    for m in props:
        lo, hi = footprint(m)
        widths.append((lo, hi))
    gap = 2.5
    slots = [max(hi[0] - lo[0] + gap, 0.62 * len(m.name)) for m, (lo, hi) in zip(props, widths)]
    total = sum(slots) - gap
    x = total / 2                                       # first prop on the left of the picture (+X)
    places = []
    for m, (lo, hi), slot in zip(props, widths, slots):
        cx = x - (slot - gap) / 2
        mid = scenery.pivot_of(m).p
        move(m, CF((cx - mid[0], 0.0, -mid[2])))
        places.append((cx, m.name, hi[1] - lo[1]))
        x -= slot
    keep = {id(n) for m in props for n in m.walk() if n.kind == "Part"}
    tall = max(p[2] for p in places)
    files = []
    for view in ("front", "top"):
        h = int(w * 0.42) if view == "front" else int(w * 0.5)
        scene = scene_for(sc, keep, w, h, samples, hexrgb(A.ground))
        if view == "front":
            fov = 26.0
            dist = max(total * 0.5 / (math.tan(math.radians(fov / 2)) * w / h) + 6.0, tall * 1.6)
            RS.cam(scene, (0.0, tall * 0.42, -dist), (0.0, tall * 0.38, 0.0), fov=fov)
            p = os.path.join(out, "props_%s.png" % area)
        else:
            RS.cam(scene, (-total * 0.32, total * 0.5, -total * 0.62), (0.0, 1.0, 0.0), fov=40.0)
            p = os.path.join(out, "props_%s_top.png" % area)
        rs.render(scene, p)
        texts = []
        if view == "front":
            import bpy_extras.object_utils as ou
            import mathutils
            for cx, name, _t in places:
                v = ou.world_to_camera_view(scene, scene.camera, mathutils.Vector(SB.rb2bl((cx, -1.2, -3.0))))
                texts.append(((v.x * w, (1 - v.y) * h), name))
        size = w // 64
        xs = [t[0][0] for t in texts]
        for i, ((x, _y), name) in enumerate(texts):
            room = min([abs(x - xs[j]) for j in (i - 1, i + 1) if 0 <= j < len(xs)] or [w])
            size = min(size, int(room / (len(name) * 0.64)))
        files.append(RS.label(p, texts, size=max(12, size)))
    return files


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    opts = dict(a.split("=", 1) for a in sys.argv[2:] if "=" in a)
    area = opts.get("area", "Jungle")
    w = int(opts.get("w", 1600))
    samples = int(opts.get("samples", 24))
    shots = opts.get("shots", "hero,props").split(",")
    if "hero" in shots:
        shot_hero(out, area, w, samples)
    if "props" in shots:
        shot_props(out, area, w, samples)


if __name__ == "__main__":
    main()
