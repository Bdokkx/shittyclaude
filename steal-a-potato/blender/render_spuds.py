"""Preview renders of the potatoes (Cycles, studs drawn on every Plastic face).

    python blender/render_spuds.py <outdir> [shots=lineup,levels,turn] [area=Meadow] [w=1600] [samples=24]
                                   [ids=Spud,TaterTot] [level=10]

  lineup   every potato of the area side by side at one level (default 10)
  levels   one potato (ids, default the area's first) at levels 1, 2, 4, 6, 8 and 10
  turn     each potato from the front, its right, the back and its left (level 10)
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
import spslib  # noqa: E402
import rbxscene as rs  # noqa: E402
from spsgeo import CF  # noqa: E402

from potato import spuds  # noqa: E402

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
GRASS = (93, 187, 70)
BLOOM = False


def ground(coll, cx=0.0, cz=0.0, size=120.0, color=GRASS):
    g = G.box(size, 1.0, size, (cx, -0.5, cz))
    me = bpy.data.meshes.new("ground")
    me.from_pydata(SB.rb2bl(np.array(g.v)).tolist(), [], g.f)
    me.materials.append(SB.material(color, "SmoothPlastic", 0.0))
    coll.objects.link(bpy.data.objects.new("ground", me))


def pose_models(models, level, X=None):
    """Move every part to where the level and the joint transforms put it; returns the set of
    parts to draw and a function that puts them back."""
    saved, keep = {}, set()
    for m in models:
        P = spuds.Pose(m)
        Xm = X.get(m.name, {}) if isinstance(X, dict) and X and isinstance(next(iter(X.values())), dict) else (X or {})
        for key, (part, cf_) in P.world(Xm, level).items():
            saved[key] = (part, part.p["cf"])
            part.p["cf"] = cf_
            if P.shown(part, level):
                keep.add(key)

    def restore():
        for part, cf_ in saved.values():
            part.p["cf"] = cf_
    return keep, restore


def scene_for(sc, keep, w, h, samples, ground_at=(0.0, 0.0)):
    scene = SB.reset()
    coll = bpy.data.collections.new("S")
    scene.collection.children.link(coll)
    SB.realize(sc, coll, filter_fn=lambda n: id(n) in keep)
    ground(coll, *ground_at)
    rs.setup_world(scene, color=(0.42, 0.66, 1.0), strength=0.8, key=3.4, key_from=(-0.45, -0.75, 0.75),
                   fill=0.7, fill_from=(0.8, -0.2, 0.3), rim=1.4, rim_from=(0.3, 0.9, 0.5))
    rs.setup_render(scene, w, h, samples=samples, bloom=BLOOM)
    try:
        scene.cycles.denoising_prefilter = "NONE"     # the accurate prefilter blacks out small white parts
    except Exception:
        pass
    return scene


def cam(scene, pos, tgt, fov=34.0):
    c = SB.camera(scene, pos, tgt, lens=50)
    c.data.sensor_fit = "VERTICAL"
    c.data.angle = math.radians(fov)
    scene.camera = c
    return c


def label(path, texts, size=26):
    im = Image.open(path).convert("RGB")
    d = ImageDraw.Draw(im)
    font = ImageFont.truetype(FONT, size)
    for (x, y), t in texts:
        d.text((x, y), t, fill=(255, 255, 255), font=font, stroke_width=3, stroke_fill=(20, 20, 30), anchor="mm")
    out = path[:-4] + ".jpg"
    im.save(out, quality=90)
    os.remove(path)
    print("saved", out, flush=True)
    return out


def kinds_for(area, ids=None):
    ks = spuds.AREAS[area]
    if ids:
        ks = [k for k in ks if k.pid in ids]
    return ks


def shot_lineup(out, area, w, samples, level=10, ids=None):
    ks = kinds_for(area, ids)
    sc = spslib.Scene("Kit")
    sp = 6.5
    models = spuds.build_area(sc, sc.root, ks, spacing=-sp)      # first kind on the left of the picture
    keep, restore = pose_models(models, level)
    n = len(models)
    h = int(w * 0.42)
    scene = scene_for(sc, keep, w, h, samples)
    span = (n - 1) * sp
    cam(scene, (0.0, 6.2, -(span * 0.67 + 9.5)), (0.0, 2.4, 0.0), fov=30.0)
    p = os.path.join(out, "lineup_%s_L%d.png" % (area, level))
    rs.render(scene, p)
    restore()
    # names under each potato: project the feet onto the image
    texts = []
    import bpy_extras.object_utils as ou
    for i, k in enumerate(ks):
        x = -(i - (n - 1) / 2) * sp
        v = ou.world_to_camera_view(scene, scene.camera, __import__("mathutils").Vector(SB.rb2bl((x, -0.9, 0.0))))
        texts.append(((v.x * w, (1 - v.y) * h), k.display))
    longest = max(len(k.display) for k in ks)                      # long names shrink so they never touch
    return label(p, texts, size=max(16, min(w // 60, int(w / n / (longest * 0.68)))))


def shot_levels(out, area, w, samples, pid=None):
    ks = kinds_for(area, [pid] if pid else None)[:1]
    k = ks[0]
    sc = spslib.Scene("Kit")
    levels = (1, 2, 4, 6, 8, 10)
    sp = 6.0
    models = []
    for i, lv in enumerate(levels):
        b = CF(((2.5 - i) * sp, 0.0, 0.0))
        m = k.build(sc, sc.root, b)
        m.name = "%s_L%d" % (k.pid, lv)
        models.append((m, lv))
    keep, saved = set(), []
    for m, lv in models:
        kp, rest = pose_models([m], lv)
        keep |= kp
        saved.append(rest)
    h = int(w * 0.42)
    scene = scene_for(sc, keep, w, h, samples)
    cam(scene, (0.0, 6.2, -(2.5 * sp * 0.62 * 2 + 9.5)), (0.0, 2.6, 0.0), fov=30.0)
    p = os.path.join(out, "levels_%s.png" % k.pid)
    rs.render(scene, p)
    for r in saved:
        r()
    import bpy_extras.object_utils as ou
    from mathutils import Vector
    texts = []
    for i, lv in enumerate(levels):
        v = ou.world_to_camera_view(scene, scene.camera, Vector(SB.rb2bl(((2.5 - i) * sp, -0.9, 0.0))))
        texts.append(((v.x * w, (1 - v.y) * h), "level %d" % lv))
    return label(p, texts, size=max(18, w // 60))


def shot_turn(out, area, w, samples, ids=None, level=10):
    ks = kinds_for(area, ids)
    files = []
    tile = w // 4
    for k in ks:
        sc = spslib.Scene("Kit")
        m = k.build(sc, sc.root)
        keep, restore = pose_models([m], level)
        scene = scene_for(sc, keep, tile, tile, samples)
        ims = []
        for j, az in enumerate((0, 90, 180, 270)):
            a = math.radians(az)
            d = 14.0
            pos = (math.sin(a) * d, 5.6, -math.cos(a) * d)
            cam(scene, pos, (0.0, 3.0, 0.0), fov=30.0)
            p = os.path.join(out, "_turn_%d.png" % j)
            rs.render(scene, p)
            ims.append(Image.open(p).convert("RGB"))
            os.remove(p)
        restore()
        sheet = Image.new("RGB", (tile * 4, tile))
        for j, im in enumerate(ims):
            sheet.paste(im, (j * tile, 0))
        d = ImageDraw.Draw(sheet)
        font = ImageFont.truetype(FONT, max(16, tile // 14))
        n = sum(1 for x in m.walk() if x.kind == "Part")
        d.text((10, 8), "%s  (%s, %d parts)" % (k.display, k.rarity, n), fill=(255, 255, 255), font=font,
               stroke_width=3, stroke_fill=(20, 20, 30))
        fp = os.path.join(out, "turn_%s.jpg" % k.pid)
        sheet.save(fp, quality=90)
        print("saved", fp, flush=True)
        files.append(fp)
    return files


def shot_clips(out, area, w, samples, ids=None, level=10, clips=None, video=False):
    """Each clip on one potato: a strip of six frames (or, with video=1, every frame into an mp4)."""
    from potato import spud_anim as SA
    k = kinds_for(area, ids)[0]
    tile = w // 3
    font = ImageFont.truetype(FONT, max(16, tile // 16))
    files = []
    for clip in SA.CLIPS:
        if clips and clip.name not in clips:
            continue
        frames = clip.bake()
        times = clip.times()
        idx = list(range(len(frames))) if video else \
            [int(round(i * (len(frames) - 1) / 5)) for i in range(6)]
        tiles = []
        for i in idx:
            sc = spslib.Scene("Kit")
            m = k.build(sc, sc.root)
            keep, restore = pose_models([m], level, frames[i])
            scene = scene_for(sc, keep, tile, tile, samples)
            cam(scene, (7.5, 6.5, -12.5), (0.0, 3.2, 0.0), fov=34.0)
            p = os.path.join(out, "_clip_%03d.png" % i)
            rs.render(scene, p)
            im = Image.open(p).convert("RGB")
            d = ImageDraw.Draw(im)
            d.text((8, 6), "%s  %.2f s" % (clip.name, times[i]), fill=(255, 255, 255), font=font, stroke_width=3,
                   stroke_fill=(20, 20, 30))
            if video:
                im.save(os.path.join(out, "_v_%s_%03d.png" % (clip.name, i)))
            else:
                tiles.append(im)
            os.remove(p)
        if not video:
            sheet = Image.new("RGB", (tile * 3, tile * 2))
            for j, im in enumerate(tiles):
                sheet.paste(im, ((j % 3) * tile, (j // 3) * tile))
            fp = os.path.join(out, "clip_%s.jpg" % clip.name)
            sheet.save(fp, quality=88)
            print("saved", fp, flush=True)
            files.append(fp)
    if video:
        import glob
        import subprocess
        lst = os.path.join(out, "_frames.txt")
        names = []
        for clip in SA.CLIPS:
            if clips and clip.name not in clips:
                continue
            fs = sorted(glob.glob(os.path.join(out, "_v_%s_*.png" % clip.name)))
            reps = 2 if clip.loop else 1
            for _ in range(reps):
                names += fs
            names += [fs[-1]] * 8                     # a short hold between clips
        with open(lst, "w") as f:
            for n in names:
                f.write("file '%s'\nduration %f\n" % (n, 1.0 / 30))
        mp4 = os.path.join(out, "potato_clips_%s.mp4" % k.pid)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-vf",
                        "fps=30,format=yuv420p", "-c:v", "libx264", "-crf", "20", mp4], check=True)
        for n in set(names):
            os.remove(n)
        os.remove(lst)
        print("saved", mp4, flush=True)
        files.append(mp4)
    return files


def shot_lineup_video(out, area, w, samples, level=10, clips=None):
    """All of an area's potatoes playing each clip together (mp4, 30 fps)."""
    import glob
    import subprocess
    from potato import spud_anim as SA
    ks = kinds_for(area)
    sp = 6.5
    h = int(w * 0.5)
    n = len(ks)
    span = (n - 1) * sp
    font = ImageFont.truetype(FONT, max(16, w // 48))
    names = []
    for clip in SA.CLIPS:
        if clips and clip.name not in clips:
            continue
        frames = clip.bake()
        for i, X in enumerate(frames):
            sc = spslib.Scene("Kit")
            models = spuds.build_area(sc, sc.root, ks, spacing=-sp)
            keep, restore = pose_models(models, level, X)
            scene = scene_for(sc, keep, w, h, samples)
            cam(scene, (0.0, 7.0, -(span * 0.62 + 11.0)), (0.0, 3.0, 0.0), fov=32.0)
            p = os.path.join(out, "_lv_%s_%03d.png" % (clip.name, i))
            rs.render(scene, p)
            im = Image.open(p).convert("RGB")
            d = ImageDraw.Draw(im)
            d.text((12, 8), clip.name, fill=(255, 255, 255), font=font, stroke_width=3, stroke_fill=(20, 20, 30))
            im.save(p)
        fs = sorted(glob.glob(os.path.join(out, "_lv_%s_*.png" % clip.name)))
        for _ in range(2 if clip.loop else 1):
            names += fs
        names += [fs[-1]] * 10
        print("rendered", clip.name, flush=True)
    lst = os.path.join(out, "_frames.txt")
    with open(lst, "w") as f:
        for nme in names:
            f.write("file '%s'\nduration %f\n" % (nme, 1.0 / 30))
    mp4 = os.path.join(out, "potato_clips_%s.mp4" % area)
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
    area = opts.get("area", "Meadow")
    ids = opts["ids"].split(",") if "ids" in opts else None
    for s in opts.get("shots", "lineup,levels,turn").split(","):
        if s == "lineup":
            shot_lineup(out, area, w, samples, int(opts.get("level", 10)), ids)
        elif s == "levels":
            shot_levels(out, area, w, samples, ids[0] if ids else None)
        elif s == "turn":
            shot_turn(out, area, w, samples, ids)
        elif s == "video":
            shot_lineup_video(out, area, w, samples, int(opts.get("level", 10)),
                              opts["clips"].split(",") if "clips" in opts else None)
        elif s == "clips":
            shot_clips(out, area, w, samples, ids, int(opts.get("level", 10)),
                       opts["clips"].split(",") if "clips" in opts else None, opts.get("video") == "1")


if __name__ == "__main__":
    main()
