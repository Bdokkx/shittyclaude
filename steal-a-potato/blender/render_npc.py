"""Preview renders of a brick rig (Farmer Spud, the fuse machine, the guardians...).

    python blender/render_npc.py <outdir> [what=npc] [shots=turn,face,clips] [w=1600] [samples=24]
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
import spslib  # noqa: E402
import rbxscene as rs  # noqa: E402
from spsgeo import CF  # noqa: E402

import render_spuds as RS  # noqa: E402
from potato import npc, rig  # noqa: E402

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def posed(model, X):
    P = rig.Pose(model)
    saved, keep = {}, set()
    for key, (part, cf_) in P.world(X).items():
        saved[key] = (part, part.p["cf"])
        part.p["cf"] = cf_
        if part.p["transparency"] < 0.99:
            keep.add(key)

    def restore():
        for part, cf_ in saved.values():
            part.p["cf"] = cf_
    return keep, restore


def frame(sc, keep, w, h, samples, pos, tgt, fov, path, extra=None):
    scene = RS.scene_for(sc, keep, w, h, samples)
    if extra:
        extra(scene)
    RS.cam(scene, pos, tgt, fov=fov)
    rs.render(scene, path)
    return scene


def shot_turn(out, build, name, w, samples, tgt_y, dist, height):
    tile = w // 4
    sc = spslib.Scene("Kit")
    m = build(sc, sc.root)
    keep, restore = posed(m, {})
    ims = []
    for j, az in enumerate((0, 90, 180, 270)):
        a = math.radians(az)
        pos = (math.sin(a) * dist, height, -math.cos(a) * dist)
        p = os.path.join(out, "_t%d.png" % j)
        frame(sc, keep, tile, int(tile * 1.4), samples, pos, (0.0, tgt_y, 0.0), 34.0, p)
        ims.append(Image.open(p).convert("RGB"))
        os.remove(p)
    restore()
    sheet = Image.new("RGB", (tile * 4, int(tile * 1.4)))
    for j, im in enumerate(ims):
        sheet.paste(im, (j * tile, 0))
    n = sum(1 for x in m.walk() if x.kind == "Part")
    d = ImageDraw.Draw(sheet)
    d.text((10, 8), "%s  (%d parts)" % (name, n), fill=(255, 255, 255), font=ImageFont.truetype(FONT, tile // 14),
           stroke_width=3, stroke_fill=(20, 20, 30))
    fp = os.path.join(out, "turn_%s.jpg" % name)
    sheet.save(fp, quality=90)
    print("saved", fp, flush=True)
    return fp


def shot_face(out, build, name, w, samples, pos, tgt, fov=30.0):
    sc = spslib.Scene("Kit")
    m = build(sc, sc.root)
    keep, restore = posed(m, {})
    p = os.path.join(out, "face_%s.png" % name)
    frame(sc, keep, w, int(w * 0.75), samples, pos, tgt, fov, p)
    restore()
    return RS.label(p, [])


def shot_clips(out, build, clips, name, w, samples, pos, tgt, fov=36.0, n=6):
    tile = w // 3
    font = ImageFont.truetype(FONT, max(16, tile // 16))
    files = []
    for clip in clips:
        frames = clip.bake()
        times = clip.times()
        idx = [int(round(i * (len(frames) - 1) / (n - 1))) for i in range(n)]
        tiles = []
        for i in idx:
            sc = spslib.Scene("Kit")
            m = build(sc, sc.root)
            keep, restore = posed(m, frames[i])
            p = os.path.join(out, "_c%03d.png" % i)
            frame(sc, keep, tile, tile, samples, pos, tgt, fov, p)
            im = Image.open(p).convert("RGB")
            d = ImageDraw.Draw(im)
            d.text((8, 6), "%s  %.2f s" % (clip.name, times[i]), fill=(255, 255, 255), font=font, stroke_width=3,
                   stroke_fill=(20, 20, 30))
            tiles.append(im)
            os.remove(p)
            restore()
        sheet = Image.new("RGB", (tile * 3, tile * ((n + 2) // 3)))
        for j, im in enumerate(tiles):
            sheet.paste(im, ((j % 3) * tile, (j // 3) * tile))
        fp = os.path.join(out, "clip_%s_%s.jpg" % (name, clip.name))
        sheet.save(fp, quality=88)
        print("saved", fp, flush=True)
        files.append(fp)
    return files


def video(out, build, clips, name, w, samples, pos, tgt, fov=36.0, reps=None):
    import glob
    import subprocess
    h = int(w * 0.75)
    font = ImageFont.truetype(FONT, max(16, w // 40))
    names = []
    for clip in clips:
        frames = clip.bake()
        for i, X in enumerate(frames):
            sc = spslib.Scene("Kit")
            m = build(sc, sc.root)
            keep, restore = posed(m, X)
            p = os.path.join(out, "_v_%s_%03d.png" % (clip.name, i))
            frame(sc, keep, w, h, samples, pos, tgt, fov, p)
            im = Image.open(p).convert("RGB")
            ImageDraw.Draw(im).text((12, 8), clip.name, fill=(255, 255, 255), font=font, stroke_width=3,
                                    stroke_fill=(20, 20, 30))
            im.save(p)
        fs = sorted(glob.glob(os.path.join(out, "_v_%s_*.png" % clip.name)))
        for _ in range((reps or {}).get(clip.name, 2 if clip.loop else 1)):
            names += fs
        names += [fs[-1]] * 10
        print("rendered", clip.name, flush=True)
    lst = os.path.join(out, "_frames.txt")
    with open(lst, "w") as f:
        for nme in names:
            f.write("file '%s'\nduration %f\n" % (nme, 1.0 / 30))
    mp4 = os.path.join(out, "%s_clips.mp4" % name)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-vf",
                    "fps=30,format=yuv420p", "-c:v", "libx264", "-crf", "20", mp4], check=True)
    for nme in set(names):
        os.remove(nme)
    os.remove(lst)
    print("saved", mp4, flush=True)
    return mp4


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    opts = dict(a.split("=", 1) for a in sys.argv[2:] if "=" in a)
    w = int(opts.get("w", 1600))
    samples = int(opts.get("samples", 24))
    what = opts.get("what", "npc")
    if what == "npc":
        b = npc.build
        for s in opts.get("shots", "turn,face,clips").split(","):
            if s == "turn":
                shot_turn(out, b, "FarmerSpud", w, samples, 6.0, 27.0, 8.0)
            elif s == "face":
                shot_face(out, b, "FarmerSpud", w, samples, (3.5, 10.5, -9.0), (0.0, 8.6, 0.0), fov=34.0)
            elif s == "clips":
                shot_clips(out, b, npc.CLIPS, "FarmerSpud", w, samples, (9.0, 9.5, -19.0), (0.0, 6.4, 0.0), fov=40.0)
            elif s == "video":
                video(out, b, npc.CLIPS, "FarmerSpud", w, samples, (9.0, 9.5, -19.0), (0.0, 6.4, 0.0), fov=40.0)


if __name__ == "__main__":
    main()
