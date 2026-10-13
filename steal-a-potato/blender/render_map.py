"""Preview renders of Workspace.PotatoMap (Cycles, studs and the owner's 4-stud checker drawn).

    python blender/render_map.py <outdir> [views=overview,corridor,yard,gate,aerial,areas] [w=1600]
                                 [samples=24] [areas=1,2,3] [fv=<folk_valley_props.json>]

  overview   from (0, 60, 200) looking at (0, 0, -100), as asked for part 1
  corridor   from (0, 7, -40) looking north up the corridor
  yard       the yard from high over its south wall
  gate       the gate, the stalls and the avenue from the spawn
  aerial     high over the yard looking up the whole corridor
  areas      one per area at eye height, from just inside its south end looking north
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
from spsgeo import CF  # noqa: E402
import rbxscene as rs  # noqa: E402

import render_spuds as RS  # noqa: E402
from potato import scenery, studmap as SM  # noqa: E402
from build_map import FV_DEFAULT  # noqa: E402
from potato.studmap import PEN  # noqa: E402

scenery.load_all()


def setup(mb, w, h, samples, extra=None):
    scene = SB.reset()
    coll = bpy.data.collections.new("S")
    scene.collection.children.link(coll)
    prev = mb.sc.root.find("PreviewOnly")
    pids = {id(n) for n in prev.walk()} if prev else set()
    extra = extra or set()
    SB.realize(mb.sc, coll, filter_fn=lambda n: n.kind == "Part" and n.p["transparency"] < 0.99 and
               (id(n) not in pids or id(n) in extra))
    g = G.box(9000.0, 1.0, 9000.0, (0.0, -3.0, -1800.0))       # the world outside the walls
    me = bpy.data.meshes.new("outside")
    me.from_pydata(SB.rb2bl(np.array(g.v)).tolist(), [], g.f)
    me.materials.append(SB.material((96, 168, 72), "SmoothPlastic", 0.0))
    coll.objects.link(bpy.data.objects.new("outside", me))
    rs.setup_world(scene, color=(0.42, 0.66, 1.0), strength=0.8, key=3.4, key_from=(-0.45, -0.75, 0.75),
                   fill=0.7, fill_from=(0.8, -0.2, 0.3), rim=1.4, rim_from=(0.3, 0.9, 0.5))
    rs.setup_render(scene, w, h, samples=samples, bloom=False)
    try:
        scene.cycles.denoising_prefilter = "NONE"
    except Exception:
        pass
    return scene


def stretch_rail(sc, parent, name, st, cf_, length):
    """The kit's Rail (7 between post centres along its X) stretched to `length` and placed."""
    from potato import plotkit as PK
    m = PK.fence_rail(sc, parent, name, st)
    k = length / PK.SPAN
    for n in m.walk():
        if n.kind != "Part":
            continue
        c = n.p["cf"]
        sz = list(n.p["size"])
        if abs(c.R[0, 0]) > 0.99:
            sz[0] *= k
        n.p["size"] = tuple(sz)
        n.p["cf"] = cf_ * CF((c.p[0] * k, c.p[1], c.p[2]), c.R)
    return m


def pens_preview(mb, rng):
    """For the pictures only (the map leaves the pens bare, the game fences them): the kit's
    fences round every pen, a tier per row of pens, and a few potatoes and seeds in some."""
    from potato import plotkit as PK
    from potato import spuds
    sc = mb.sc
    f = sc.folder(sc.root, "PreviewOnly")
    keep_extra, pot_ids = set(), set()
    tiers = PK.TIER_ORDER
    for i, (name, (ex, ez), (dx, dz), (x0, x1, z0, z1)) in enumerate(SM.plots()):
        tier = tiers[i // 3 % 4] if i < 12 else tiers[0]
        st = PK.TIERS[tier]
        corners = [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]
        for k in range(4):
            (ax, az), (bx, bz) = corners[k], corners[(k + 1) % 4]
            pieces = [((ax, az), (bx, bz))]
            on_side = abs((bx - ax) * (ez - az) - (bz - az) * (ex - ax)) < 1e-6 and \
                min(ax, bx) - 1e-6 <= ex <= max(ax, bx) + 1e-6 and min(az, bz) - 1e-6 <= ez <= max(az, bz) + 1e-6
            if on_side:
                ux, uz = (bx - ax) / PEN, (bz - az) / PEN
                g1 = (ex - ux * 7.8, ez - uz * 7.8)
                g2 = (ex + ux * 7.8, ez + uz * 7.8)
                pieces = [((ax, az), g1), (g2, (bx, bz))]
                PK.gate_arch(sc, f, tier, st, CF((ex, 0.0, ez), SM.facing(-dx, -dz)))
            for (p0, p1) in pieces:
                L = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
                n = max(1, round(L / 7.5))
                R = G.ry(0) if abs(p1[1] - p0[1]) < 1e-6 else G.ry(90)
                for j in range(n):
                    t0, t1 = j / n, (j + 1) / n
                    a_ = (p0[0] + (p1[0] - p0[0]) * t0, p0[1] + (p1[1] - p0[1]) * t0)
                    b_ = (p0[0] + (p1[0] - p0[0]) * t1, p0[1] + (p1[1] - p0[1]) * t1)
                    stretch_rail(sc, f, tier, st, CF(((a_[0] + b_[0]) / 2, 0.0, (a_[1] + b_[1]) / 2), R), L / n)
                    if not (on_side and j == n - 1 and p1 != (bx, bz)) and not (on_side and j == 0 and p0 != (ax, az)):
                        PK.fence_post(sc, f, tier, st, CF((a_[0], 0.0, a_[1])))
        # a few potatoes on their soil patches and seeds on heaps in some pens
        if i % 3 == 0:
            cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
            kinds = spuds.MEADOW
            models = []
            for j in range(3):
                px, pz = cx + (j - 1) * 14.0, cz + (8.0 if dz == 0 else 6.0)
                PK.soil_patch(sc, f, CF((px, 0.0, pz)))
                m = kinds[(i + j) % len(kinds)].build(sc, f, CF((px, 0.22, pz), SM.facing(-dx, -dz)))
                models.append(m)
            for j in range(2):
                px, pz = cx + (j - 0.5) * 16.0, cz - 10.0
                PK.soil_heap(sc, f, CF((px, 0.0, pz)))
                PK.seed(sc, f, "Meadow", CF((px, 1.0, pz)))
            keep, _restore = RS.pose_models(models, 10)
            keep_extra |= keep
            pot_ids |= {id(x) for m in models for x in m.walk()}
    keep_extra |= {id(n) for n in f.walk() if n.kind == "Part" and id(n) not in pot_ids}
    return keep_extra


def shoot(scene, path, pos, tgt, fov, label=None, w=1600):
    c = RS.cam(scene, pos, tgt, fov=fov)
    c.data.clip_end = 9000.0
    rs.render(scene, path)
    return RS.label(path, [((w * 0.5, 34), label)] if label else [], size=w // 46)


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    opts = dict(a.split("=", 1) for a in sys.argv[2:] if "=" in a)
    w = int(opts.get("w", 1600))
    h = int(w * 0.5625)
    samples = int(opts.get("samples", 24))
    views = opts.get("views", "overview,corridor,yard,gate,aerial,areas").split(",")
    mb = SM.MapBuild(opts.get("fv", FV_DEFAULT)).build()
    extra = pens_preview(mb, np.random.default_rng(3)) if "nopens" not in sys.argv else set()
    scene = setup(mb, w, h, samples, extra)
    files = []
    j = lambda name: os.path.join(out, name + ".png")  # noqa: E731
    if "overview" in views:
        files.append(shoot(scene, j("map_overview"), (0.0, 60.0, 200.0), (0.0, 0.0, -100.0), 50.0, w=w))
    if "corridor" in views:
        files.append(shoot(scene, j("map_corridor"), (0.0, 7.0, -40.0), (0.0, 6.0, -400.0), 50.0, w=w))
    if "yard" in views:
        files.append(shoot(scene, j("map_yard"), (0.0, 230.0, 470.0), (0.0, 0.0, 150.0), 50.0, w=w))
    if "gate" in views:
        files.append(shoot(scene, j("map_gate"), (0.0, 9.0, 112.0), (0.0, 16.0, 0.0), 52.0, w=w))
    if "aerial" in views:
        files.append(shoot(scene, j("map_aerial"), (0.0, 320.0, 260.0), (0.0, 0.0, -900.0), 46.0, w=w))
    if "areas" in views:
        which = [int(v) for v in opts["areas"].split(",")] if "areas" in opts else range(1, SM.N_AREAS + 1)
        for n in which:
            zs, zn = SM.area_z(n)
            a = SM.AREAS[n - 1]
            files.append(shoot(scene, j("map_area%02d_%s" % (n, a[0])), (0.0, 9.0, zs - 6.0),
                               (0.0, 5.0, zs - 150.0), 58.0, label="%d  %s" % (n, a[1]), w=w))
    for f in files:
        print("saved", f)


if __name__ == "__main__":
    main()
