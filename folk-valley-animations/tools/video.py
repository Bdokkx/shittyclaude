"""Make a preview video (MP4) of the animations with the software R6 renderer:
a before / after comparison of the everyday ones, the new weapon equips flowing into
their holds, then every animation in grid pages.

    python tools/video.py <original.json> <improved.json> <out.mp4>
"""
import json
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim  # noqa: E402
import render  # noqa: E402

W, H, FPS = 1280, 720, 30
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT2 = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BG_TOP, BG_BOT = (118, 146, 190), (62, 82, 120)


def font(size, bold=True):
    return ImageFont.truetype(FONT if bold else FONT2, size)


def weapon_for(name):
    for key, w in (("Sword", "Sword"), ("Slash", "Sword"), ("Dagger", "Dagger"), ("Stab", "Dagger"),
                   ("Hammer", "Hammer"), ("Smash", "Hammer")):
        if key in name:
            return w
    return None


def pose_at(a, t, constant=False):
    """{joint: 4x4 Transform} at time t, from the keys (stepped when constant, else linear)."""
    if a.loop:
        t = t % a.length if a.length > 0 else 0.0
    else:
        hold = 0.5                                   # one-shots: play, hold the end, start again
        t = t % (a.length + hold)
        t = min(t, a.length)
    out = {}
    for j, tr in a.tracks.items():
        k = int(np.searchsorted(tr.t, t, side="right") - 1)
        k = max(0, min(k, len(tr.t) - 1))
        if constant or k == len(tr.t) - 1:
            p, q = tr.p[k], tr.q[k]
        else:
            h = tr.t[k + 1] - tr.t[k]
            u = 0.0 if h < 1e-6 else (t - tr.t[k]) / h
            p = tr.p[k] + (tr.p[k + 1] - tr.p[k]) * u
            q = anim.slerp(tr.q[k], tr.q[k + 1], u)
        out[j] = render.xf(p, q)
    return out


def chained(equip, hold, t):
    """Equip once, then the hold loop; the whole thing repeats every few seconds."""
    period = equip.length + 2 * hold.length
    t = t % period
    if t < equip.length:
        return pose_at(equip, t)
    return pose_at(hold, (t - equip.length) % hold.length)


def gradient(w, h, top=BG_TOP, bot=BG_BOT):
    col = Image.new("RGB", (1, h))
    px = col.load()
    for y in range(h):
        k = y / max(h - 1, 1)
        px[0, y] = tuple(int(a + (b - a) * k) for a, b in zip(top, bot))
    return col.resize((w, h))


class Video:
    def __init__(self, path):
        self.proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                                      "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-", "-c:v", "libx264",
                                      "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "medium", "-movflags",
                                      "+faststart", path], stdin=subprocess.PIPE)
        self.frames = 0

    def add(self, img):
        self.proc.stdin.write(img.convert("RGB").tobytes())
        self.frames += 1

    def close(self):
        self.proc.stdin.close()
        self.proc.wait()


def cell_image(world, cam, weapon, size, bg):
    img = render.draw(world, cam, weapon, bg=bg)
    return img if img.size == size else img.resize(size)


def label(d, x, y, w, text, size=22, color=(255, 255, 255), chip=None):
    f = font(size)
    tw = d.textlength(text, font=f)
    if chip:
        cw = tw + 22
        d.rounded_rectangle((x + (w - cw) / 2, y - 3, x + (w + cw) / 2, y + size + 7), radius=10, fill=chip)
    d.text((x + (w - tw) / 2, y), text, font=f, fill=color)


def title_card(v, title, sub, seconds=2.2):
    bg = gradient(W, H)
    d = ImageDraw.Draw(bg)
    label(d, 0, H // 2 - 70, W, title, 54)
    label(d, 0, H // 2 + 10, W, sub, 26)
    for _ in range(int(seconds * FPS)):
        v.add(bg)


def page_before_after(v, pairs, seconds, heading):
    cols, rows = 3, 2
    cw, ch = W // cols, (H - 70) // rows
    half = cw // 2
    cam = render.Camera(px=half, height=7.6, center=(0, 3.4, 0))
    base = gradient(W, H)
    d = ImageDraw.Draw(base)
    label(d, 0, 18, W, heading, 30)
    for k in range(int(seconds * FPS)):
        t = k / FPS
        img = base.copy()
        dd = ImageDraw.Draw(img)
        for i, (name, before, after) in enumerate(pairs):
            c, r = i % cols, i // cols
            x0, y0 = c * cw, 70 + r * ch
            wpn = weapon_for(name)
            for side, (a, constant, tint) in enumerate(((before, True, (96, 104, 124)), (after, False, (86, 128, 196)))):
                world = render.pose_world(pose_at(a, t, constant))
                cell = render.draw(world, cam, wpn, bg=tint)
                img.paste(cell, (x0 + side * half, y0 + max(0, (ch - 44 - cell.height) // 2) + 4))
            dd.text((x0 + 10, y0 + 10), "before", font=font(16), fill=(230, 230, 236))
            dd.text((x0 + half + 10, y0 + 10), "after", font=font(16), fill=(255, 230, 120))
            label(dd, x0, y0 + ch - 36, cw, name, 22)
        v.add(img)


def page_chains(v, chains, seconds, heading):
    n = len(chains)
    cw = W // n
    cam = render.Camera(px=min(cw, H - 140), height=8.4, center=(0, 3.6, 0))
    base = gradient(W, H)
    d = ImageDraw.Draw(base)
    label(d, 0, 18, W, heading, 30)
    for k in range(int(seconds * FPS)):
        t = k / FPS
        img = base.copy()
        dd = ImageDraw.Draw(img)
        for i, (title, equip, hold, wpn) in enumerate(chains):
            world = render.pose_world(chained(equip, hold, t))
            cell = render.draw(world, cam, wpn, bg=(86, 128, 196))
            x0 = i * cw + (cw - cell.width) // 2
            img.paste(cell, (x0, 80))
            period = equip.length + 2 * hold.length
            phase = "Equip" if (t % period) < equip.length else "Hold"
            label(dd, i * cw, 90 + cell.height, cw, title, 26)
            label(dd, i * cw, 130 + cell.height, cw, phase, 18, (20, 22, 30), chip=(255, 200, 70))
        v.add(img)


def page_grid(v, items, seconds, heading, cols=4, rows=3):
    cw, ch = W // cols, (H - 64) // rows
    cam = render.Camera(px=ch - 30, height=8.6, center=(0, 3.6, 0))
    base = gradient(W, H)
    d = ImageDraw.Draw(base)
    label(d, 0, 14, W, heading, 28)
    for k in range(int(seconds * FPS)):
        t = k / FPS
        img = base.copy()
        dd = ImageDraw.Draw(img)
        for i, (name, a) in enumerate(items):
            c, r = i % cols, i // cols
            x0, y0 = c * cw, 64 + r * ch
            world = render.pose_world(pose_at(a, t))
            cell = render.draw(world, cam, weapon_for(name), bg=(86, 128, 196))
            img.paste(cell, (x0 + (cw - cell.width) // 2, y0))
            label(dd, x0, y0 + ch - 30, cw, name, 18)
        v.add(img)


def main(orig_path, new_path, out_path):
    orig_folder = json.load(open(orig_path))[0]
    new_folder = json.load(open(new_path))[0]
    orig = {}
    for c in orig_folder["children"]:
        a = anim.read_sequence(c)
        first = c["children"][0]["children"][0]["children"][0]       # first keyframe's Torso pose
        orig[a.name] = (a, first["props"]["EasingStyle"]["Enum"] == 1)
    new = {c["name"]: anim.read_sequence(c) for c in new_folder["children"]}
    v = Video(out_path)
    title_card(v, "FOLK VALLEY [RUN]: animations", "64 smoothed and polished, plus 6 new weapon animations")
    for names in (("Idle", "Walk", "Sprint", "CatcherRun", "CatcherRunSword", "CatcherRunHammer"),
                  ("SwordSwing1", "DaggerSwing1", "HammerSwing1", "Tagged", "Pounce", "Land")):
        pairs = [(n, orig[n][0], new[n]) for n in names]
        page_before_after(v, pairs, 6.0, "Before: joints snap from key to key       After: smooth, with more life")
    title_card(v, "New: weapon hold and equip animations", "equip once, then the hold loops while standing", 1.6)
    chains = [("Sword", new["SwordEquip"], new["SwordHold"], "Sword"),
              ("Dagger", new["DaggerEquip"], new["DaggerHold"], "Dagger"),
              ("Hammer", new["HammerEquip"], new["HammerHold"], "Hammer")]
    page_chains(v, chains, 8.0, "New: <Weapon>Equip, then <Weapon>Hold")
    names = [c["name"] for c in new_folder["children"]]
    pages = [names[i:i + 12] for i in range(0, len(names), 12)]
    title_card(v, "Every animation", "%d in the Sequences folder" % len(names), 1.4)
    for k, page in enumerate(pages):
        page_grid(v, [(n, new[n]) for n in page], 5.0, "All animations (%d / %d)" % (k + 1, len(pages)))
    v.close()
    print("wrote", out_path, "%d frames, %.1f s" % (v.frames, v.frames / FPS))


if __name__ == "__main__":
    main(*sys.argv[1:4])
