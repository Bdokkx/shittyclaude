"""Before / after sheet: pairs of tiles per weapon with display names.

    python tools/ba_sheet.py <before_dir> <after_dir> <out.png> Id Id ... [--cols=3] [--w=300]
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "blender"))
args = [a for a in sys.argv[1:] if not a.startswith("--")]
opts = dict(a[2:].split("=", 1) for a in sys.argv[1:] if a.startswith("--") and "=" in a)
before, after, out, ids = args[0], args[1], args[2], args[3:]
try:
    import ast
    src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "blender", "defs.py")).read()
    start = src.index("NAMES = {")
    end = src.index("}\n", start) + 1
    NAMES = ast.literal_eval(src[start + len("NAMES = "):end])
except Exception:
    NAMES = {}
cols = int(opts.get("cols", 3))
tw = int(opts.get("w", 300))
th = int(tw * 1.5)
pair_w = tw * 2
rows = (len(ids) + cols - 1) // cols
W, H = pair_w * cols, rows * (th + 80)
im = Image.new("RGB", (W, H))
px = im.load()
for y in range(H):
    t = y / max(H - 1, 1)
    c = tuple(int(a + (b - a) * t) for a, b in zip((118, 146, 190), (70, 92, 130)))
    for x in range(W):
        px[x, y] = c
d = ImageDraw.Draw(im)
F = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", max(16, tw // 10))
F2 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", max(12, tw // 14))
for i, wid in enumerate(ids):
    col, row = i % cols, i // cols
    x0, y0 = col * pair_w, row * (th + 80)
    for j, folder in enumerate((before, after)):
        p = os.path.join(folder, wid + ".png")
        if os.path.exists(p):
            t = Image.open(p).convert("RGBA").resize((tw, th))
            im.paste(t, (x0 + j * tw, y0 + 40), t)
        lab = ("before", "after")[j]
        lw = d.textlength(lab, font=F2)
        d.text((x0 + j * tw + (tw - lw) / 2, y0 + 40 + th - 6), lab, font=F2,
               fill=(220, 228, 240) if j == 0 else (255, 214, 90))
    name = NAMES.get(wid, wid)
    nw = d.textlength(name, font=F)
    d.text((x0 + (pair_w - nw) / 2, y0 + 6), name, font=F, fill=(255, 255, 255))
    if col:
        d.line((x0, y0 + 10, x0, y0 + th + 60), fill=(150, 170, 205), width=2)
im.save(out)
print(out, im.size)
