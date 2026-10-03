"""Lay the Blender renders out into labelled images (needs Pillow):

    python3 tools/compose_previews.py

  previews/<Map>_assets.png   every custom asset of that island on its own tile, with names
  previews/<Map>_poster.png   overview + top view + detail insets, like the reference sheet
  previews/AllIslands.png     the four islands side by side
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "gen"))
from themes import ORDER, THEMES  # noqa: E402

PREV = os.path.join(ROOT, "previews")
TITLES = {"voxel": "Voxel Island", "desert": "Desert Coast", "frost": "Frost Coast", "volcanic": "Volcanic Island"}
ACCENT = {"voxel": (92, 168, 70), "desert": (214, 150, 74), "frost": (150, 200, 235), "volcanic": (238, 104, 40)}
BG = (24, 27, 34)


def font(size, bold=True):
    for f in ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",):
        for d in ("/usr/share/fonts/truetype/dejavu", "/usr/share/fonts/TTF"):
            p = os.path.join(d, f)
            if os.path.exists(p):
                return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def nice(name):
    out = ""
    for k, ch in enumerate(name):
        if ch.isupper() and k and not name[k - 1].isupper():
            out += " "
        out += ch
    return out


def fit(img, w, h):
    """Cover-crop img into w x h."""
    s = max(w / img.width, h / img.height)
    img = img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS)
    x, y = (img.width - w) // 2, (img.height - h) // 2
    return img.crop((x, y, x + w, y + h))


def framed(canvas, img, box, color, label=None):
    x0, y0, x1, y1 = box
    canvas.paste(fit(img, x1 - x0, y1 - y0), (x0, y0))
    d = ImageDraw.Draw(canvas)
    d.rectangle(box, outline=color, width=4)
    if label:
        f = font(22)
        tw = d.textlength(label, font=f)
        d.rectangle((x0 + 4, y1 - 38, x0 + 20 + tw, y1 - 4), fill=(0, 0, 0))
        d.text((x0 + 12, y1 - 35), label, font=f, fill=(255, 255, 255))


def load(name):
    p = os.path.join(PREV, name)
    return Image.open(p).convert("RGB") if os.path.exists(p) else None


def asset_sheet(theme, names):
    tdir = os.path.join(PREV, "tiles", theme)
    names = [n for n in names if os.path.exists(os.path.join(tdir, n + ".png"))]
    if not names:
        return None
    cols, t, pad, head = 6, 250, 12, 86
    rows = -(-len(names) // cols)
    W = cols * (t + pad) + pad
    H = head + rows * (t + 36 + pad) + pad
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.text((pad + 4, 18), TITLES[theme] + " - custom assets", font=font(40), fill=ACCENT[theme])
    f = font(19, bold=False)
    for k, n in enumerate(names):
        r, c = divmod(k, cols)
        x, y = pad + c * (t + pad), head + r * (t + 36 + pad)
        img.paste(fit(Image.open(os.path.join(tdir, n + ".png")).convert("RGB"), t, t), (x, y))
        d.rectangle((x, y, x + t, y + t), outline=(60, 66, 80), width=2)
        tw = d.textlength(nice(n), font=f)
        d.text((x + (t - tw) / 2, y + t + 7), nice(n), font=f, fill=(225, 228, 235))
    out = os.path.join(PREV, THEMES[theme]["map"] + "_assets.png")
    img.save(out, optimize=True)
    return out


def poster(theme):
    m = THEMES[theme]["map"]
    over, top = load(m + ".png"), load(m + "_top.png")
    if over is None:
        return None
    insets = [(load(m + s), lab) for s, lab in (("_village.png", "village"), ("_detail.png", "detail"),
                                                 ("_falls.png", {"desert": "oasis falls", "frost": "frozen falls",
                                                                 "volcanic": "lava falls"}.get(theme, "waterfall")))]
    insets = [(i, lab) for i, lab in insets if i is not None]
    W, H = 2400, 1500
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    col = ACCENT[theme]
    d.text((40, 26), TITLES[theme].upper(), font=font(64), fill=col)
    framed(img, over, (40, 120, 1560, 975), col, "overview")
    if top:
        framed(img, top, (1600, 120, 2360, 880), col, "top view")
    iw = (W - 80 - 40 * (len(insets) - 1)) // max(1, len(insets))
    for k, (im, lab) in enumerate(insets):
        x = 40 + k * (iw + 40)
        framed(img, im, (x, 1015, x + iw, 1460), col, lab)
    out = os.path.join(PREV, m + "_poster.png")
    img.save(out, optimize=True)
    return out, over, top


def main():
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    lists = {}
    src = open(os.path.join(ROOT, "tools", "blender_build.py")).read()
    block = src[src.index("ISLAND_ASSETS = {"):]
    block = block[:block.index("\n}\n") + 3]
    exec(block, {}, lists)
    overs = []
    for theme in ORDER:
        s = asset_sheet(theme, lists["ISLAND_ASSETS"][theme])
        p = poster(theme)
        print(theme, s, p and p[0])
        if p:
            overs.append((theme, p[1]))
    if overs:
        w, h = 1200, 700
        img = Image.new("RGB", (2 * w + 120, 2 * h + 220), BG)
        d = ImageDraw.Draw(img)
        for k, (theme, im) in enumerate(overs):
            r, c = divmod(k, 2)
            x, y = 40 + c * (w + 40), 40 + r * (h + 90)
            d.text((x, y), TITLES[theme], font=font(44), fill=ACCENT[theme])
            framed(img, im, (x, y + 60, x + w, y + 60 + h), ACCENT[theme])
        img.save(os.path.join(PREV, "AllIslands.png"), optimize=True)
        print("AllIslands.png")


if __name__ == "__main__":
    main()
