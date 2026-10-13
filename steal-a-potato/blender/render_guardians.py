"""Preview renders of the guardians.

    python blender/render_guardians.py <outdir> [areas=Meadow,Dunes,...] [shots=grid,sleep,turn,clips,video]
                                       [w=1800] [samples=20]
"""
import glob
import math
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy  # noqa: E402,F401,I001
import numpy as np  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

import spsblend  # noqa: E402,F401
import spslib  # noqa: E402
import rbxscene as rs  # noqa: E402

import render_spuds as RS  # noqa: E402
from potato import guardian_anim, guardians, rig  # noqa: E402

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
BUILDERS = {a: (title, fn) for a, title, fn in guardians.AREAS}


def posed(model, X, sleep=False):
    """Pose the model (X = joint transforms); sleep shows EyeShut instead of EyeOpen."""
    P = rig.Pose(model)
    saved, keep, pts = {}, set(), []
    for key, (part, cf_) in P.world(X).items():
        saved[key] = (part, part.p["cf"])
        part.p["cf"] = cf_
        vis = part.p["transparency"] < 0.99
        if part.name == "EyeShut":
            vis = sleep
        elif part.name == "EyeOpen":
            vis = not sleep
        if vis:
            keep.add(key)
            half = np.array(part.p["size"]) / 2
            for c in np.array(np.meshgrid([-1, 1], [-1, 1], [-1, 1])).T.reshape(-1, 3):
                pts.append(cf_.p + cf_.R @ (c * half))

    def restore():
        for part, cf_ in saved.values():
            part.p["cf"] = cf_
    pts = np.array(pts)
    return keep, restore, pts.min(axis=0), pts.max(axis=0)


def framed(lo, hi, az, el, fov, aspect=1.0, margin=1.12):
    c = (lo + hi) / 2
    rad = np.linalg.norm(hi - lo) / 2
    d = rad / math.tan(math.radians(fov) / 2) * margin / min(1.0, aspect)
    a, e = math.radians(az), math.radians(el)
    pos = c + d * np.array((math.sin(a) * math.cos(e), math.sin(e), -math.cos(a) * math.cos(e)))
    return tuple(pos), tuple(c)


def render_one(area, X, path, w, h, samples, az=32.0, el=14.0, fov=30.0, sleep=False, fix=None):
    sc = spslib.Scene("Kit")
    m = BUILDERS[area][1](sc, sc.root)
    keep, restore, lo, hi = posed(m, X, sleep)
    if fix:                                   # one framing for a whole clip
        lo, hi = fix
    pos, tgt = framed(lo, hi, az, el, fov, w / h)
    scene = RS.scene_for(sc, keep, w, h, samples)
    RS.cam(scene, pos, tgt, fov=fov)
    rs.render(scene, path)
    restore()
    n = sum(1 for x in m.walk() if x.kind == "Part")
    return n, (lo, hi)


def text(im, s, size, xy=(10, 8)):
    d = ImageDraw.Draw(im)
    d.text(xy, s, fill=(255, 255, 255), font=ImageFont.truetype(FONT, size), stroke_width=3, stroke_fill=(20, 20, 30))


def shot_grid(out, areas, w, samples, sleep=False, cols=3, tag="grid"):
    tile = w // cols
    rows = (len(areas) + cols - 1) // cols
    sheet = Image.new("RGB", (tile * cols, tile * rows))
    for i, a in enumerate(areas):
        p = os.path.join(out, "_g_%s.png" % a)
        n, _ = render_one(a, {}, p, tile, tile, samples, sleep=sleep)
        im = Image.open(p).convert("RGB")
        text(im, "%s: %s  (%d parts)" % (a, BUILDERS[a][0], n), max(14, tile // 22))
        sheet.paste(im, ((i % cols) * tile, (i // cols) * tile))
        os.remove(p)
    fp = os.path.join(out, "guardians_%s_%s.jpg" % (tag, "_".join(areas) if len(areas) < 4 else
                                                     "%s-%s" % (areas[0], areas[-1])))
    sheet.save(fp, quality=88)
    print("saved", fp, flush=True)
    return fp


def shot_turn(out, area, w, samples):
    tile = w // 4
    ims = []
    lo_hi = None
    for j, az in enumerate((0, 90, 180, 270)):
        p = os.path.join(out, "_t%d.png" % j)
        n, lo_hi = render_one(area, {}, p, tile, int(tile * 1.2), samples, az=az, el=10, fix=lo_hi)
        ims.append(Image.open(p).convert("RGB"))
        os.remove(p)
    sheet = Image.new("RGB", (tile * 4, int(tile * 1.2)))
    for j, im in enumerate(ims):
        sheet.paste(im, (j * tile, 0))
    text(sheet, "%s  (%d parts)" % (area, n), tile // 14)
    fp = os.path.join(out, "turn_%s.jpg" % area)
    sheet.save(fp, quality=90)
    print("saved", fp, flush=True)
    return fp


def clip_frames(area):
    return {c.name: (c, c.bake()) for c in guardian_anim.CLIPS[area]}


def rest_box(area):
    """One framing for every clip: the rest pose's box, with room to hop and rear up."""
    sc = spslib.Scene("Kit")
    m = BUILDERS[area][1](sc, sc.root)
    keep, restore, lo, hi = posed(m, {})
    restore()
    return lo - np.array((0.8, 0.3, 0.8)), hi + np.array((0.8, 1.6, 0.8))


def shot_clips(out, area, w, samples, n=6):
    tile = w // n
    rows = []
    fix = rest_box(area)
    for name, (clip, frames) in clip_frames(area).items():
        times = clip.times()
        idx = [int(round(i * (len(frames) - 1) / (n - 1))) for i in range(n)] if clip.loop else \
            [int(round(i * (len(frames) - 1) / (n - 1))) for i in range(n)]
        row = Image.new("RGB", (tile * n, tile))
        for j, i in enumerate(idx):
            p = os.path.join(out, "_c%03d.png" % i)
            sleep = name == "Sleep" or (name == "Wake" and times[i] < guardian_anim.EYES_OPEN_AT)
            render_one(area, frames[i], p, tile, tile, samples, sleep=sleep, fix=fix)
            im = Image.open(p).convert("RGB")
            text(im, "%s %.2fs" % (name, times[i]), max(14, tile // 12))
            row.paste(im, (j * tile, 0))
            os.remove(p)
        rows.append(row)
    sheet = Image.new("RGB", (tile * n, tile * len(rows)))
    for k, row in enumerate(rows):
        sheet.paste(row, (0, k * tile))
    fp = os.path.join(out, "clips_%s.jpg" % area)
    sheet.save(fp, quality=88)
    print("saved", fp, flush=True)
    return fp


def video(out, area, w, samples):
    h = int(w * 0.75)
    names = []
    fix = rest_box(area)
    for name, (clip, frames) in clip_frames(area).items():
        times = clip.times()
        for i, X in enumerate(frames):
            p = os.path.join(out, "_v_%s_%s_%03d.png" % (area, name, i))
            sleep = name == "Sleep" or (name == "Wake" and times[i] < guardian_anim.EYES_OPEN_AT)
            render_one(area, X, p, w, h, samples, sleep=sleep, fix=fix)
            im = Image.open(p).convert("RGB")
            text(im, "%s  %s" % (area, name), max(16, w // 40))
            im.save(p)
        fs = sorted(glob.glob(os.path.join(out, "_v_%s_%s_*.png" % (area, name))))
        reps = {"Sleep": 1, "Wake": 1, "Run": 4}.get(name, 1)
        for _ in range(reps):
            names += fs[:-1] if clip.loop else fs
        names += [fs[-1]] * 6
    lst = os.path.join(out, "_frames_%s.txt" % area)
    with open(lst, "w") as f:
        for nme in names:
            f.write("file '%s'\nduration %f\n" % (os.path.abspath(nme), 1.0 / 30))
    mp4 = os.path.join(out, "%s_clips.mp4" % area)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-vf",
                    "fps=30,format=yuv420p", "-c:v", "libx264", "-crf", "21", mp4], check=True)
    for nme in set(names):
        os.remove(nme)
    os.remove(lst)
    print("saved", mp4, flush=True)
    return mp4


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    opts = dict(a.split("=", 1) for a in sys.argv[2:] if "=" in a)
    w = int(opts.get("w", 1800))
    samples = int(opts.get("samples", 20))
    areas = opts.get("areas", ",".join(BUILDERS)).split(",")
    for s in opts.get("shots", "grid").split(","):
        if s == "grid":
            shot_grid(out, areas, w, samples)
        elif s == "sleep":
            shot_grid(out, areas, w, samples, sleep=True, tag="sleep")
        elif s == "turn":
            for a in areas:
                shot_turn(out, a, w, samples)
        elif s == "clips":
            for a in areas:
                shot_clips(out, a, w, samples)
        elif s == "video":
            for a in areas:
                video(out, a, w, samples)


if __name__ == "__main__":
    main()
