"""Before/after previews of the animations.

    python3 make_previews.py <original_dump.json> <out_dir> [Name ...]

Writes <Name>.gif (old | new side by side, looping) and <Name>_strip.png (8 frames over time: old/new from the
front-3/4, then old/new from the side) for every animation, plus all_new.png (one strip per animation) and
all_before_after.mp4 (every GIF back to back)."""
import json
import math
import os
import subprocess
import sys

from PIL import Image, ImageDraw

import preview as PV
from anims import build_all
from r6 import length, sample


def main():
    dump = {a["name"]: a for a in json.load(open(sys.argv[1]))}
    out = sys.argv[2]
    only = set(sys.argv[3:])
    os.makedirs(out, exist_ok=True)
    fnt, small = PV.font(15), PV.font(11)
    rows, video = [], []
    for seq in build_all():
        if only and seq.name not in only:
            continue
        old, new = dump[seq.name], seq.as_dump()
        L = seq.length
        loops = max(1, math.ceil(1.2 / L)) if seq.loop else 1
        cam = PV.default_cam((300, 300))
        fo = PV.frames(lambda t: sample(old, t), length(old), loops=loops, cam=cam, label=seq.name + "  (old)", font=fnt)
        fn = PV.frames(lambda t: sample(new, t), L, loops=loops, cam=cam, label=seq.name + "  (new)", font=fnt)
        if not seq.loop:                                     # hold the last frame a moment
            fo += [fo[-1]] * 12
            fn += [fn[-1]] * 12
        both = PV.side_by_side(fo, fn)
        PV.save_gif(os.path.join(out, seq.name + ".gif"), both)
        video.extend(both * (2 if len(both) < 45 else 1))
        # strips for checking poses by eye
        sc = PV.default_cam((150, 150))
        side = PV.Camera((12.5, 3.0, -1.0), (0, 2.2, 0), (150, 150))       # from the character's right
        n = 8
        ts = [L * i / (n - 1) if not seq.loop else L * i / n for i in range(n)]
        strip = Image.new("RGB", (150 * n, 600 + 18), "white")
        for i, t in enumerate(ts):
            so, sn = sample(old, min(t, length(old))), sample(new, t)
            strip.paste(PV.draw_frame(so, sc), (150 * i, 18))
            strip.paste(PV.draw_frame(sn, sc), (150 * i, 168))
            strip.paste(PV.draw_frame(so, side), (150 * i, 318))
            strip.paste(PV.draw_frame(sn, side), (150 * i, 468))
            ImageDraw.Draw(strip).text((150 * i + 4, 2), "%.2fs" % t, fill=(0, 0, 0), font=small)
        strip.save(os.path.join(out, seq.name + "_strip.png"))
        rows.append((seq.name, [PV.draw_frame(sample(new, t), sc) for t in ts]))
        print("preview", seq.name)
    if video and not only:
        tmp = os.path.join(out, "_frames")
        os.makedirs(tmp, exist_ok=True)
        for i, im in enumerate(video):
            im.save(os.path.join(tmp, "%05d.png" % i))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "30", "-i", os.path.join(tmp, "%05d.png"),
                        "-pix_fmt", "yuv420p", "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2", os.path.join(out, "all_before_after.mp4")],
                       check=True)
        for f in os.listdir(tmp):
            os.remove(os.path.join(tmp, f))
        os.rmdir(tmp)
    if rows and not only:
        sheet = Image.new("RGB", (120 + 150 * 8, 150 * len(rows)), "white")
        d = ImageDraw.Draw(sheet)
        for r, (name, fr) in enumerate(rows):
            d.text((6, 150 * r + 66), name, fill=(0, 0, 0), font=fnt)
            for i, im in enumerate(fr):
                sheet.paste(im, (120 + 150 * i, 150 * r))
        sheet.save(os.path.join(out, "all_new.png"))


if __name__ == "__main__":
    main()
