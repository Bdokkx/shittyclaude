"""Put the Grim Reaper preview video together from the rendered frames
(blender/render_anims.py --frames / --turntable / --hero): a turntable intro,
the boss next to a player, then every animation with its name, what it does,
a timeline with its markers and a pop-up when a hit marker fires, and an
overview to finish.

    python tools/reaper_video.py <render_dir> <anims.json> <out.mp4>
"""
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from check_anims import read_clips  # noqa: E402

W, H, FPS = 1280, 720, 30
VIEW = 720
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT2 = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BG_TOP, BG_BOT = (64, 52, 104), (22, 18, 40)
GREEN = (122, 255, 106)
PURPLE = (176, 120, 255)
TEXT = (232, 226, 248)
DIM = (160, 150, 190)

CLIPS = [
    ("ReaperIdle", "Idle", 1, "Breathes, looks round with a creepy head tilt, beckons with its claw and chuckles."),
    ("ReaperWalk", "Walk", 2, "A slow, heavy stalk. The Footstep markers kick up dust. Made for about 7 studs a second."),
    ("ReaperRun", "Run", 3, "The chase: hunched over, scythe up over its shoulder. Made for about 18 studs a second."),
    ("ReaperStomp", "Stomp", 1, "Knee up high, then a slam. Impact sends a shockwave ring 18 studs round the foot: jump it!"),
    ("ReaperSwing", "Swing", 1, "Winds up, then sweeps the blade across the front at player height, 24 studs out."),
    ("ReaperSpin", "Spin", 1, "Rises off the ground and whirls round twice: the blade sweeps 22 studs on every side."),
    ("ReaperThrow", "Throw", 1, "Hurls the scythe: it whirls out about 31 studs, loops round like a boomerang and flies "
                                "back into its fist."),
    ("ReaperRoar", "Roar", 1, "Rears up and roars, and the wave pushes everyone back. On first sight and when enraged."),
    ("ReaperHurt", "Hurt", 2, "A quick flinch when it takes damage."),
    ("ReaperDefeat", "Defeat", 1, "Staggers, drops to its knees, lets the scythe slip and slumps as its eyes go dark."),
]
PRIORITY = {0: "Idle", 1: "Movement", 2: "Action", 3: "Action2", 4: "Action3", 5: "Action4"}
POP = {"Impact": "IMPACT!", "Hit": "HIT!", "SpinStart": "SPIN!", "SpinEnd": "spin ends", "Release": "THROW!",
       "Catch": "CATCH!", "Roar": "ROAR!", "ScytheDrop": "clang", "Collapsed": "defeated", "Footstep": "step"}
BIG = {"Impact", "Hit", "SpinStart", "Release", "Catch", "Roar"}


def font(size, bold=True):
    return ImageFont.truetype(FONT if bold else FONT2, size)


def backdrop():
    col = Image.new("RGB", (1, H))
    for y in range(H):
        k = y / (H - 1)
        col.putpixel((0, y), tuple(int(a + (b - a) * k) for a, b in zip(BG_TOP, BG_BOT)))
    return col.resize((W, H))


def wrap(draw, text, fnt, width):
    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=fnt) <= width:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


class Frames:
    def __init__(self, root):
        self.root = root
        self.cache = {}

    def get(self, clip, i):
        key = (clip, i)
        if key not in self.cache:
            if len(self.cache) > 400:
                self.cache.clear()
            im = Image.open(os.path.join(self.root, "frames", clip, "%04d.png" % i)).convert("RGBA")
            if im.size != (VIEW, VIEW):
                im = im.resize((VIEW, VIEW), Image.LANCZOS)
            self.cache[key] = im
        return self.cache[key]

    def count(self, clip):
        return len([f for f in os.listdir(os.path.join(self.root, "frames", clip)) if f.endswith(".png")])


def header(d):
    d.text((VIEW + 34, 30), "GRIM REAPER", fill=GREEN, font=font(40))
    d.text((VIEW + 36, 80), "Folk Valley [RUN]: Halloween event boss", fill=DIM, font=font(18, False))


def footer(d, text="R15 Humanoid + Motor6Ds, KeyframeSequences with hit markers"):
    d.text((VIEW + 36, H - 36), text, fill=DIM, font=font(15, False))


def compose_clip(bg, view, idx, label, desc, info, t, length, markers, pops):
    im = bg.copy().convert("RGBA")
    im.alpha_composite(view, (0, 0))
    d = ImageDraw.Draw(im)
    header(d)
    x0 = VIEW + 36
    d.text((x0, 140), "%d / %d" % (idx, len(CLIPS)), fill=DIM, font=font(20, False))
    d.text((x0, 168), label, fill=TEXT, font=font(58))
    y = 250
    for line in wrap(d, desc, font(22, False), W - x0 - 30):
        d.text((x0, y), line, fill=TEXT, font=font(22, False))
        y += 31
    d.text((x0, y + 10), info, fill=DIM, font=font(18, False))
    # timeline with the markers
    bx, by, bw = x0, 560, W - x0 - 40
    d.rounded_rectangle((bx, by, bx + bw, by + 12), radius=6, fill=(40, 30, 64))
    k = min(max(t / length, 0.0), 1.0)
    d.rounded_rectangle((bx, by, bx + max(12, int(bw * k)), by + 12), radius=6, fill=GREEN)
    placed = []
    for mt, name in markers:
        mx = bx + int(bw * mt / length)
        d.line((mx, by - 8, mx, by + 20), fill=PURPLE, width=3)
        if name != "Footstep":
            lx = mx - 4
            row = sum(1 for p in placed if abs(p - lx) < 110)
            d.text((lx, by + 26 + 22 * row), name, fill=PURPLE, font=font(16, False))
            placed.append(lx)
    d.text((bx, by - 34), "%.2fs" % min(t, length), fill=DIM, font=font(16, False))
    # marker pop-ups over the view
    for age, name in pops:
        a = max(0.0, 1.0 - age / 0.55)
        if a <= 0:
            continue
        txt = POP.get(name, name)
        size = 64 if name in BIG else 28
        f = font(size)
        tw = d.textlength(txt, font=f)
        layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        px, py = VIEW - tw - 30, 26 - int(14 * (1 - a)) + (0 if name in BIG else 40)
        col = GREEN if name in BIG else TEXT
        ld.text((px + 3, py + 3), txt, fill=(10, 6, 18, int(200 * a)), font=f)
        ld.text((px, py), txt, fill=(*col, int(255 * a)), font=f)
        im.alpha_composite(layer)
    footer(d)
    return im.convert("RGB")


def main(root, anims_path, out_path):
    clips = read_clips(anims_path)
    fr = Frames(root)
    bg = backdrop()
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s",
                           "%dx%d" % (W, H), "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow",
                           "-crf", "19", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out_path],
                          stdin=subprocess.PIPE)
    n_out = 0

    def emit(im):
        nonlocal n_out
        ff.stdin.write(np.asarray(im, dtype=np.uint8).tobytes())
        n_out += 1

    # 1. the turntable
    n = fr.count("Turntable")
    names = ", ".join(c[1] for c in CLIPS)
    for i in range(n):
        im = bg.copy().convert("RGBA")
        im.alpha_composite(fr.get("Turntable", i), (0, 0))
        d = ImageDraw.Draw(im)
        header(d)
        x0 = VIEW + 36
        y = 160
        for line in ("A big cartoon Grim Reaper with a", "glowing scythe, built in Blender", "and rigged for Roblox."):
            d.text((x0, y), line, fill=TEXT, font=font(24, False))
            y += 34
        y += 20
        for k, v in (("Height", "21.4 studs to the hood tip"), ("Parts", "39 meshes on 22 Motor6D joints"),
                     ("Animations", "10")):
            d.text((x0, y), k, fill=DIM, font=font(18, False))
            d.text((x0 + 130, y), v, fill=TEXT, font=font(18))
            y += 30
        y += 14
        for line in wrap(d, names, font(18, False), W - x0 - 40):
            d.text((x0, y), line, fill=PURPLE, font=font(18, False))
            y += 26
        footer(d)
        emit(im.convert("RGB"))
    # 2. next to a player
    hero = Image.open(os.path.join(root, "hero.png")).convert("RGBA").resize((VIEW, VIEW), Image.LANCZOS)
    for _ in range(int(2.6 * FPS)):
        im = bg.copy().convert("RGBA")
        im.alpha_composite(hero, (0, 0))
        d = ImageDraw.Draw(im)
        header(d)
        d.text((VIEW + 36, 170), "Next to a", fill=TEXT, font=font(30, False))
        d.text((VIEW + 36, 210), "5-stud player", fill=GREEN, font=font(44))
        d.text((VIEW + 36, 280), "About 4 times as tall. Its scythe", fill=TEXT, font=font(22, False))
        d.text((VIEW + 36, 311), "reaches about 22 studs.", fill=TEXT, font=font(22, False))
        footer(d)
        emit(im.convert("RGB"))
    # 3. every animation
    for idx, (name, label, reps, desc) in enumerate(CLIPS, 1):
        c = clips[name]
        L = float(c["length"])
        loop = bool(c["loop"])
        n = fr.count(name)
        info = "%.2fs, %s, %s priority" % (L, "loops" if loop else "plays once", PRIORITY[c["priority"]])
        total = reps * L + (0.0 if loop else 0.7)
        steps = int(round(total * FPS))
        fired = []
        for s in range(steps):
            t_all = s / FPS
            rep = int(t_all // L) if loop else min(int(t_all // (L + 0.35)), reps - 1)
            if loop:
                t = t_all - rep * L
                i = int(round(t * FPS)) % n
            else:
                t = t_all - rep * (L + 0.35) if reps > 1 else t_all
                t = min(t, L)
                i = min(int(round(t * FPS)), n - 1)
            for mt, mname in c["markers"]:
                if abs(t - mt) < 0.5 / FPS and not any(f[0] == (rep, mt, mname) for f in fired):
                    fired.append(((rep, mt, mname), t_all))
            pops = [(t_all - ft, key[2]) for key, ft in fired if 0 <= t_all - ft < 0.55]
            emit(compose_clip(bg, fr.get(name, i), idx, label, desc, info, t, L, c["markers"], pops))
    # 4. all ten at a glance
    picks = {"ReaperIdle": 25, "ReaperWalk": 11, "ReaperRun": 7, "ReaperStomp": 27, "ReaperSwing": 18,
             "ReaperSpin": 30, "ReaperThrow": 33, "ReaperRoar": 30, "ReaperHurt": 4, "ReaperDefeat": 80}
    sheet = bg.copy().convert("RGBA")
    d = ImageDraw.Draw(sheet)
    tile = 236
    gx = (W - 5 * tile) // 2
    for k, (name, label, _, _) in enumerate(CLIPS):
        cx, cy = gx + (k % 5) * tile, 80 + (k // 5) * (tile + 40)
        im = fr.get(name, min(picks[name], fr.count(name) - 1)).resize((tile, tile), Image.LANCZOS)
        sheet.alpha_composite(im, (cx, cy))
        tw = d.textlength(label, font=font(22))
        d.text((cx + (tile - tw) / 2, cy + tile + 4), label, fill=TEXT, font=font(22))
    d.text((gx, 26), "GRIM REAPER", fill=GREEN, font=font(34))
    d.text((gx + 270, 38), "10 animations, ready for Roblox", fill=DIM, font=font(20, False))
    final = sheet.convert("RGB")
    for _ in range(int(3.5 * FPS)):
        emit(final)
    ff.stdin.close()
    ff.wait()
    final.save(os.path.join(os.path.dirname(out_path), "reaper_animations.jpg"), quality=90)
    print("wrote %s: %d frames, %.1fs" % (out_path, n_out, n_out / FPS))


if __name__ == "__main__":
    main(*sys.argv[1:4])
