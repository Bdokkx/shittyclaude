"""One review sheet per island from the spear renders (needs Pillow):

    python3 tools/compose_spear.py VoxelIsland   ->  previews/spear/<Map>_review.png
"""
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREV = os.path.join(ROOT, "previews", "spear")
BG, INK, ACC = (22, 25, 33), (232, 235, 242), (108, 203, 74)


def font(size, bold=True):
    p = "/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf" % ("-Bold" if bold else "")
    return ImageFont.truetype(p, size) if os.path.exists(p) else ImageFont.load_default()


def fit(img, w, h):
    s = max(w / img.width, h / img.height)
    img = img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS)
    x, y = (img.width - w) // 2, (img.height - h) // 2
    return img.crop((x, y, x + w, y + h))


def panel(canvas, name, box, label):
    p = os.path.join(PREV, name + ".png")
    if not os.path.exists(p):
        return
    x0, y0, x1, y1 = box
    canvas.paste(fit(Image.open(p).convert("RGB"), x1 - x0, y1 - y0), (x0, y0))
    d = ImageDraw.Draw(canvas)
    d.rectangle(box, outline=ACC, width=3)
    f = font(22)
    tw = d.textlength(label, font=f)
    d.rectangle((x0 + 4, y1 - 36, x0 + 20 + tw, y1 - 4), fill=(0, 0, 0))
    d.text((x0 + 12, y1 - 33), label, font=f, fill=(255, 255, 255))


def main(m):
    W = 2400
    img = Image.new("RGB", (W, 3800), BG)
    d = ImageDraw.Draw(img)
    d.text((40, 24), m.upper() + "  -  rebuild for review", font=font(56), fill=ACC)
    d.text((40, 96), "open hub with 3 shop stalls + glowing pads, Blender portal on a cliff by the hub, 230+ trees "
                     "(6 kinds), grass tufts, big railed T-dock, beach camp, jetty, waterfall, new lighthouse",
           font=font(24, False), fill=INK)
    panel(img, m + "_overhead", (40, 150, 1560, 1005), "overhead 45 deg (checklist b)")
    panel(img, m + "_dock", (1600, 150, 2360, 575), "end of the dock (checklist a)")
    panel(img, m + "_plaza", (1600, 580, 2360, 1005), "plaza at player height (checklist c)")
    row = [(m + "_portal", "Portal cliff"), (m + "_market", "Fish Market stall"), (m + "_shop", "Spear Shop stall"),
           (m + "_upgrade", "Upgrades stall")]
    w = (W - 80 - 3 * 30) // 4
    for k, (n, lab) in enumerate(row):
        x = 40 + k * (w + 30)
        panel(img, n, (x, 1040, x + w, 1460), lab)
    row = [(m + "_village", "hub from above"), (m + "_dockdeck", "big T-dock"), (m + "_lighthouse", "lighthouse")]
    w = (W - 80 - 2 * 30) // 3
    for k, (n, lab) in enumerate(row):
        x = 40 + k * (w + 30)
        panel(img, n, (x, 1495, x + w, 1955), lab)
    row = [(m + "_camp", "beach camp"), (m + "_stairs", "railed stairs from the dock"), (m + "_beach", "beach palms")]
    for k, (n, lab) in enumerate(row):
        x = 40 + k * (w + 30)
        panel(img, n, (x, 1985, x + w, 2445), lab)
    oy = 490
    d.text((40, 1985 + oy), "BUILD STAGES", font=font(34), fill=ACC)
    row = [(m + "_overhead_stage1_terrain", "1 terrain"), (m + "_overhead_stage2_dock_reef", "2 + dock & reef"),
           (m + "_overhead_stage3_buildings", "3 + buildings"), (m + "_overhead", "4 + props & lighting")]
    w = (W - 80 - 3 * 30) // 4
    for k, (n, lab) in enumerate(row):
        x = 40 + k * (w + 30)
        panel(img, n, (x, 2035 + oy, x + w, 2365 + oy), lab)
    d.text((40, 2395 + oy), "UPGRADE TIERS", font=font(34), fill=ACC)
    row = [(m + "_overhead_tier1", "Tier 1: short pier, dirt hub floor"),
           (m + "_overhead_tier2", "Tier 2: big T-dock, stone hub floor, lanterns"),
           (m + "_overhead_tier3", "Tier 3: fishing wings, canopy, pennants, beam")]
    w = (W - 80 - 2 * 30) // 3
    for k, (n, lab) in enumerate(row):
        x = 40 + k * (w + 30)
        panel(img, n, (x, 2445 + oy, x + w, 2845 + oy), lab)
    out = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "check_spear.py"), m], capture_output=True,
                         text=True).stdout.splitlines()
    d.text((40, 2880 + oy), "SELF-REVIEW CHECKLIST (style bible section 8)", font=font(30), fill=ACC)
    f = font(20, False)
    for k, line in enumerate(out[1:]):
        d.text((40 + (k // 6) * 1180, 2925 + oy + (k % 6) * 30), line.strip()[:110], font=f, fill=INK)
    path = os.path.join(PREV, m + "_review.png")
    img.save(path, optimize=True)
    print(path)


if __name__ == "__main__":
    for name in sys.argv[1:] or ["VoxelIsland"]:
        main(name)
