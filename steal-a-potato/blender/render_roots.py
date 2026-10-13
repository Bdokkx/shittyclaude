"""Posed stills of the RootMonster's animations (Cycles).

    python blender/render_roots.py <outdir> [w=640] [samples=16] [hero=1]

Writes roots_<clip>.jpg (a strip of frames per clip) and, with hero=1, roots_chase_hero.jpg (the
monster mid-chase on Meadow grass, chasing a 5-stud R6 figure).
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy  # noqa: E402,I001
import numpy as np  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

import spsblend as SB  # noqa: E402
import spsgeo as G  # noqa: E402
import rbxscene as rs  # noqa: E402
from spsgeo import CF  # noqa: E402

from potato import build, roots_anim as RA  # noqa: E402
from render import camera, light  # noqa: E402

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def ground(coll, base, color=(104, 208, 62), size=80):
    g = G.box(size, 1.0, size, (base.p[0], base.p[1] - 0.5, base.p[2] - 10))
    me = bpy.data.meshes.new("ground")
    me.from_pydata(SB.rb2bl(np.array(g.v)).tolist(), [], g.f)
    me.materials.append(SB.material(color, "Plastic", 0.0))
    coll.objects.link(bpy.data.objects.new("ground", me))


def shot(sc, X, path, cam_off, tgt_off, w, h, samples, extra=None, ground_col=(104, 208, 62)):
    rig = sc.root_rig
    base = rig["base"]
    posed = RA.posed_parts(sc, X)
    saved = {n: n.p["cf"] for n in posed}
    for n, cf_ in posed.items():
        n.p["cf"] = cf_
    scene = SB.reset()
    coll = bpy.data.collections.new("R")
    scene.collection.children.link(coll)
    m = rig["model"]
    keep = set(id(n) for n in m.walk())
    if extra is not None:
        keep |= set(id(n) for n in extra.walk())
    SB.realize(sc, coll, filter_fn=lambda n: id(n) in keep)
    ground(coll, base, ground_col)
    light(scene)
    rs.setup_render(scene, w, h, samples=samples, bloom=True)
    camera(scene, tuple(np.array(base.p) + cam_off), tuple(np.array(base.p) + tgt_off))
    rs.render(scene, path)
    for n, cf_ in saved.items():
        n.p["cf"] = cf_


def runner(sc, cf_):
    """A plain 5-stud R6 figure mid-stride (preview only), facing -Z of cf_."""
    m = sc.model(sc.root, "Runner")
    cols = {"Head": (245, 205, 60), "Torso": (40, 110, 210), "Arm": (245, 205, 60), "Leg": (60, 160, 70)}

    def p(name, size, local, col, rot=None):
        sc.part(m, name, size, cf_ * CF(local, rot), col, grid=False, surfaces="smooth")
    p("Torso", (2, 2, 1), (0, 3.1, 0), cols["Torso"], G.rx(-12))
    p("Head", (1.2, 1.2, 1.2), (0, 4.75, -0.35), cols["Head"])
    p("Left Arm", (1, 2, 1), (-1.5, 3.1, 0.5), cols["Arm"], G.rx(40))
    p("Right Arm", (1, 2, 1), (1.5, 3.1, -0.6), cols["Arm"], G.rx(-45))
    p("Left Leg", (1, 2, 1), (-0.5, 1.1, -0.6), cols["Leg"], G.rx(-35))
    p("Right Leg", (1, 2, 1), (0.5, 1.1, 0.6), cols["Leg"], G.rx(35))
    return m


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    opts = dict(a.split("=", 1) for a in sys.argv[2:] if "=" in a)
    w = int(opts.get("w", 640))
    h = w * 3 // 4
    samples = int(opts.get("samples", 16))
    sc = build.build(areas=[], kit=False, roots=True)
    clips = dict((c.name, (c, fr)) for c, fr in [(c, c.bake()) for c in RA.CLIPS])
    cam_off, tgt_off = np.array((13.0, 9.0, -17.0)), np.array((0.0, 2.5, -2.5))
    font = ImageFont.truetype(FONT, 22)
    if opts.get("hero") == "1":
        import spslib
        c, fr = clips["RootChase"]
        # a 5-stud R6 figure running away in front of it, for scale
        dummy = runner(sc, CF(sc.root_rig["base"].p + np.array((-5.5, 0.0, -12.0)), G.ry(-25)))
        p = os.path.join(out, "roots_chase_hero.png")
        shot(sc, fr[6], p, np.array((7.0, 3.6, -21.0)), np.array((-1.5, 3.0, -5.0)), 1280, 720, samples * 2,
             extra=dummy)
        Image.open(p).convert("RGB").save(p[:-4] + ".jpg", quality=90)
        os.remove(p)
        print("saved", p[:-4] + ".jpg")
    for name in [c for c in opts.get("clips", "RootEmerge,RootChase,RootGrab,RootWither").split(",") if c]:
        c, fr = clips[name]
        n = 6
        idx = [int(round(i * (len(fr) - 1) / (n - 1))) for i in range(n)]
        tiles = []
        for i in idx:
            p = os.path.join(out, "_f%02d.png" % i)
            shot(sc, fr[i], p, cam_off, tgt_off, w, h, samples)
            im = Image.open(p).convert("RGB")
            d = ImageDraw.Draw(im)
            d.text((10, 8), "%s  %.2f s" % (name, c.times()[i]), fill=(255, 255, 255), font=font)
            tiles.append(im)
            os.remove(p)
        sheet = Image.new("RGB", (w * 3, h * 2))
        for k, im in enumerate(tiles):
            sheet.paste(im, ((k % 3) * w, (k // 3) * h))
        sp = os.path.join(out, "roots_%s.jpg" % name)
        sheet.save(sp, quality=88)
        print("saved", sp, flush=True)


if __name__ == "__main__":
    main()
