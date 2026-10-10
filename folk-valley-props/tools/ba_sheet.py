"""Before / after sheet: the old and new render of each prop side by side.

    python tools/ba_sheet.py <before_dir> <after_dir> <out.jpg> Name Name ... [--cols=3] [--w=260] [--title=...]
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
args = [a for a in sys.argv[1:] if not a.startswith("--")]
opts = dict(a[2:].split("=", 1) for a in sys.argv[1:] if a.startswith("--") and "=" in a)
before, after, out, names = args[0], args[1], args[2], args[3:]
cols = min(int(opts.get("cols", 3)), len(names))
tw = int(opts.get("w", 260))
title = opts.get("title")
lh = 40
top = 56 if title else 0
gap = 24
pair_w = tw * 2 + gap
rows = (len(names) + cols - 1) // cols
W, H = pair_w * cols, top + rows * (tw + lh)
col = Image.new("RGB", (1, H))
for y in range(H):
    t = y / max(H - 1, 1)
    col.putpixel((0, y), tuple(int(a + (b - a) * t) for a, b in zip((118, 146, 190), (70, 92, 130))))
im = col.resize((W, H))
d = ImageDraw.Draw(im)
f = ImageFont.truetype(FONT, max(14, tw // 13))
fs = ImageFont.truetype(FONT, max(11, tw // 20))
if title:
    ft = ImageFont.truetype(FONT, 30)
    d.text(((W - d.textlength(title, font=ft)) / 2, 12), title, font=ft, fill=(255, 255, 255))
for i, name in enumerate(names):
    r, c = divmod(i, cols)
    x0, y0 = c * pair_w, top + r * (tw + lh)
    d.rounded_rectangle((x0 + 6, y0 + 4, x0 + tw - 6, y0 + tw - 4), radius=12, fill=(84, 100, 128))
    for k, src in enumerate((before, after)):
        p = os.path.join(src, name + ".png")
        if os.path.exists(p):
            t = Image.open(p).convert("RGBA").resize((tw, tw), Image.LANCZOS)
            im.paste(t, (x0 + k * (tw + gap), y0), t)
    d.text((x0 + 12, y0 + 8), "before", font=fs, fill=(225, 230, 240))
    d.text((x0 + tw + gap + 8, y0 + 8), "after", font=fs, fill=(255, 226, 120))
    d.text((x0 + tw + gap // 2 - 8, y0 + tw / 2 - 12), "→", font=f, fill=(255, 255, 255))
    w = d.textlength(name, font=f)
    d.text((x0 + (pair_w - gap - w) / 2, y0 + tw + 6), name, font=f, fill=(255, 255, 255))
im.convert("RGB").save(out, quality=88)
print(out, im.size)
