"""Grid contact sheet of weapon tiles with name labels.

    python tools/contact_sheet.py <tiles_dir> <out.png> Id Id ... [--cols=6] [--w=300]
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

args = [a for a in sys.argv[1:] if not a.startswith("--")]
opts = dict(a[2:].split("=", 1) for a in sys.argv[1:] if a.startswith("--") and "=" in a)
tiles_dir, out, ids = args[0], args[1], args[2:]
cols = int(opts.get("cols", 6))
tw = int(opts.get("w", 300))
th = int(tw * 1.5)
lh = 44
rows = (len(ids) + cols - 1) // cols
W, H = cols * tw, rows * (th + lh)
im = Image.new("RGB", (W, H))
px = im.load()
for y in range(H):
    t = y / max(H - 1, 1)
    c = tuple(int(a + (b - a) * t) for a, b in zip((118, 146, 190), (70, 92, 130)))
    for x in range(W):
        px[x, y] = c
d = ImageDraw.Draw(im)
f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", max(14, tw // 14))
for i, wid in enumerate(ids):
    r, c = divmod(i, cols)
    x0, y0 = c * tw, r * (th + lh)
    p = os.path.join(tiles_dir, wid + ".png")
    if os.path.exists(p):
        t = Image.open(p).convert("RGBA").resize((tw, th))
        im.paste(t, (x0, y0), t)
    w = d.textlength(wid, font=f)
    d.text((x0 + (tw - w) / 2, y0 + th + 6), wid, font=f, fill=(255, 255, 255))
im.save(out)
print(out, im.size)
