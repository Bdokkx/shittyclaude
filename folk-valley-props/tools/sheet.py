"""Grid contact sheet of square prop tiles with name labels.

    python tools/sheet.py <tiles_dir> <out.png|jpg> Name Name ... [--cols=6] [--w=300] [--title=...]
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
args = [a for a in sys.argv[1:] if not a.startswith("--")]
opts = dict(a[2:].split("=", 1) for a in sys.argv[1:] if a.startswith("--") and "=" in a)
tiles_dir, out, names = args[0], args[1], args[2:]
cols = min(int(opts.get("cols", 6)), len(names))
tw = int(opts.get("w", 300))
title = opts.get("title")
lh = max(30, tw // 9)
top = 56 if title else 0
rows = (len(names) + cols - 1) // cols
W, H = cols * tw, top + rows * (tw + lh)
col = Image.new("RGB", (1, H))
for y in range(H):
    t = y / max(H - 1, 1)
    col.putpixel((0, y), tuple(int(a + (b - a) * t) for a, b in zip((118, 146, 190), (70, 92, 130))))
im = col.resize((W, H))
d = ImageDraw.Draw(im)
f = ImageFont.truetype(FONT, max(13, tw // 15))
if title:
    ft = ImageFont.truetype(FONT, 30)
    d.text(((W - d.textlength(title, font=ft)) / 2, 12), title, font=ft, fill=(255, 255, 255))
for i, name in enumerate(names):
    r, c = divmod(i, cols)
    x0, y0 = c * tw, top + r * (tw + lh)
    p = os.path.join(tiles_dir, name + ".png")
    if os.path.exists(p):
        t = Image.open(p).convert("RGBA").resize((tw, tw), Image.LANCZOS)
        im.paste(t, (x0, y0), t)
    w = d.textlength(name, font=f)
    d.text((x0 + (tw - w) / 2, y0 + tw + 4), name, font=f, fill=(255, 255, 255))
im.convert("RGB").save(out, quality=90)
print(out, im.size)
