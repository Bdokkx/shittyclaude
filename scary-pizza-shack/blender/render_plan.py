"""Top-down plans with labels: the inside of the shack and the whole site.

    python blender/render_plan.py <outdir> [samples=24]
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy  # noqa: E402,I001
import numpy as np  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

import scene_build  # noqa: E402
import spsblend as SB  # noqa: E402
import rbxscene as rs  # noqa: E402
import spslib  # noqa: E402

out = sys.argv[1]
os.makedirs(out, exist_ok=True)
opts = dict(a.split("=") for a in sys.argv[2:] if "=" in a)
samples = int(opts.get("samples", 24))
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def font(s, bold=True):
    return ImageFont.truetype(FONT if bold else FONT_R, s)


sc = scene_build.build(items=False)


class View:
    def __init__(self, cx, cz, w_studs, h_studs, k):
        self.cx, self.cz, self.k = cx, cz, k
        self.W, self.H = int(w_studs * k), int(h_studs * k)
        self.S = max(w_studs, h_studs)

    def px(self, x, z):
        return (self.W / 2 + (x - self.cx) * self.k, self.H / 2 + (z - self.cz) * self.k)


def render_top(view, path, filt, night=False):
    if opts.get("reuse") and os.path.exists(path):
        return
    scene = SB.reset()
    coll = bpy.data.collections.new("Map")
    scene.collection.children.link(coll)
    SB.realize(sc, coll, filt)
    SB.day_world(scene, strength=1.05)
    rs.setup_render(scene, view.W, view.H, samples=samples, bloom=False)
    # camera a hair south of its target so "up" in the image is north
    SB.camera(scene, (view.cx, 400, view.cz + 1e-3), (view.cx, 0, view.cz), ortho=view.S)
    scene.camera.data.clip_end = 1000
    rs.render(scene, path)


def arrow(d, p, look, col, size=14, width=4):
    x, y = p
    lx, lz = look[0], look[2]
    n = math.hypot(lx, lz) or 1.0
    lx, lz = lx / n, lz / n
    tip = (x + lx * size, y + lz * size)
    tail = (x - lx * size * 0.6, y - lz * size * 0.6)
    d.line((tail, tip), fill=col, width=width)
    left = (tip[0] - lx * size * 0.55 + lz * size * 0.45, tip[1] - lz * size * 0.55 - lx * size * 0.45)
    right = (tip[0] - lx * size * 0.55 - lz * size * 0.45, tip[1] - lz * size * 0.55 + lx * size * 0.45)
    d.polygon((tip, left, right), fill=col)


def label(d, xy, text, f, fill=(255, 255, 255), bg=(16, 16, 20, 205), anchor="mm", pad=4):
    bb = d.textbbox(xy, text, font=f, anchor=anchor)
    d.rectangle((bb[0] - pad, bb[1] - pad, bb[2] + pad, bb[3] + pad), fill=bg)
    d.text(xy, text, font=f, fill=fill, anchor=anchor)


def footprint(m):
    pts = [c.p["cf"].p for c in m.walk() if c.kind in ("Part", "MeshPart") and c.p["transparency"] < 0.99]
    if not pts:
        pts = [c.p["cf"].p for c in m.walk() if c.kind == "Marker"]
    return np.mean(np.array(pts), 0)


# ---------------------------------------------------------------- inside

def inside():
    v = View(0.0, 0.0, 40.0, 25.0, 55.0)
    raw = os.path.join(out, "plan_inside_raw.png")

    def filt(n):
        path = n.path()
        if "/Roof/" in path or "/PizzaSign/" in path or "/Awning/" in path:
            return False
        if n.p["cf"].p[1] > 8.6 and ("/Stations/" in path):
            return False
        return n.top() in ("Shack", "Stations")
    render_top(v, raw, filt)
    img = Image.open(raw).convert("RGBA")
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    st = sc.root.get("Stations")
    names = {"CeilingLamp1": "CeilingLamp1 (ceiling)", "CeilingLamp2": "CeilingLamp2 (ceiling)",
             "Hatch": "Hatch (ceiling)"}
    offsets = {"RulesBoard": (0, -26), "PlushieShelf": (0, 26), "Register": (0, 24), "Bin": (-30, 0),
               "PeelRack": (-8, 0), "FuseBox": (6, -26), "ShutterButton": (0, -22), "Sink": (0, 20),
               "BackDoor": (0, 24), "Hatch": (0, 0), "CeilingLamp1": (0, -24), "CeilingLamp2": (0, -24),
               "ServingWindow": (0, 44)}
    from map_shell import HATCH
    hx0, hx1, hz0, hz1 = HATCH
    (ax, ay), (bx, by) = v.px(hx0, hz0), v.px(hx1, hz1)
    for k in range(0, int(bx - ax), 16):
        d.line((ax + k, ay, min(ax + k + 9, bx), ay), fill=(255, 255, 255, 230), width=3)
        d.line((ax + k, by, min(ax + k + 9, bx), by), fill=(255, 255, 255, 230), width=3)
    for k in range(0, int(by - ay), 16):
        d.line((ax, ay + k, ax, min(ay + k + 9, by)), fill=(255, 255, 255, 230), width=3)
        d.line((bx, ay + k, bx, min(ay + k + 9, by)), fill=(255, 255, 255, 230), width=3)
    for m in st.children:
        stand = m.find("Stand")
        if stand is None:
            continue
        sp = stand.p["cf"]
        if abs(sp.p[0]) > 18.5 or abs(sp.p[2]) > 11.5:
            continue
        # item markers: dots; stand: cyan arrow
        for c in m.walk():
            if c.kind == "Marker" and c is not stand and not c.name.startswith("Stand"):
                x, y = v.px(c.p["cf"].p[0], c.p["cf"].p[2])
                d.ellipse((x - 6, y - 6, x + 6, y + 6), fill=(255, 60, 200, 255), outline=(0, 0, 0, 255))
        for c in m.children:
            if c.kind == "Marker" and c.name.startswith("Stand"):
                arrow(d, v.px(c.p["cf"].p[0], c.p["cf"].p[2]), c.p["cf"].look, (40, 230, 255, 255), 16, 5)
        c = footprint(m)
        x, y = v.px(c[0], c[2])
        ox, oy = offsets.get(m.name, (0, 0))
        label(d, (x + ox, y + oy), names.get(m.name, m.name), font(19))
    # section C markers that are inside (the four player spawns get one label)
    spawns = []
    for n in sc.root.get("Markers").children:
        p = n.p["cf"].p
        if abs(p[0]) < 18 and abs(p[2]) < 11:
            x, y = v.px(p[0], p[2])
            arrow(d, (x, y), n.p["cf"].look, (255, 210, 60, 255), 13, 4)
            if n.name.startswith("PlayerSpawn"):
                spawns.append((x, y))
                label(d, (x + 12, y - 4), n.name[-1], font(13), fill=(255, 220, 120), bg=(16, 16, 20, 170), pad=2)
                continue
            label(d, (x, y + 22), n.name, font(14, False), fill=(255, 220, 120), bg=(16, 16, 20, 170))
    if spawns:
        sx = sum(p[0] for p in spawns) / len(spawns)
        sy = max(p[1] for p in spawns)
        label(d, (sx, sy + 26), "PlayerSpawn1-4", font(14, False), fill=(255, 220, 120), bg=(16, 16, 20, 170))
    # compass + legend
    d.rectangle((0, 0, v.W, 46), fill=(16, 16, 20, 230))
    d.text((16, 10), "PizzaShack - inside (roof off). North up, +X east, +Z south (road). Room X -17..17, Z -10..10, "
           "floor top Y 0.4, ceiling Y 9.4.", font=font(19), fill=(240, 228, 196))
    lx = v.W - 640
    d.rectangle((lx, v.H - 44, v.W, v.H), fill=(16, 16, 20, 220))
    arrow(d, (lx + 24, v.H - 22), (1, 0, 0), (40, 230, 255, 255), 12, 4)
    d.text((lx + 44, v.H - 34), "Stand (facing)", font=font(17, False), fill=(255, 255, 255))
    d.ellipse((lx + 200, v.H - 28, lx + 212, v.H - 16), fill=(255, 60, 200, 255))
    d.text((lx + 220, v.H - 34), "item marker", font=font(17, False), fill=(255, 255, 255))
    arrow(d, (lx + 360, v.H - 22), (1, 0, 0), (255, 210, 60, 255), 12, 4)
    d.text((lx + 380, v.H - 34), "Markers folder", font=font(17, False), fill=(255, 255, 255))
    img = Image.alpha_composite(img, ov).convert("RGB")
    img.save(os.path.join(out, "plan_inside.jpg"), quality=92)
    print("saved plan_inside.jpg")


# ---------------------------------------------------------------- site

def site():
    v = View(2.0, -4.0, 136.0, 146.0, 13.0)
    raw = os.path.join(out, "plan_site_raw.png")
    render_top(v, raw, lambda n: n.top() != "Items")
    img = Image.open(raw).convert("RGBA")
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    st = sc.root.get("Stations")
    outside = ["Generator", "Dumpster", "YardGate", "StreetLamp", "YardLamp", "BusStop", "RoadSign"]
    offs = {"StreetLamp": (-100, 0), "RoadSign": (0, -40), "BusStop": (0, -46), "YardGate": (0, -36),
            "YardLamp": (34, -22), "Generator": (0, -48), "Dumpster": (0, 40)}
    for name in outside:
        m = st.find(name)
        c = footprint(m)
        x, y = v.px(c[0], c[2])
        ox, oy = offs.get(name, (0, 0))
        label(d, (x + ox, y + oy), name, font(17), fill=(120, 255, 255))
    for name, pos in (("Shack (see inside plan)", (0, 0)), ("Yard (gravel)", (-12, -26)),
                      ("Road (asphalt Y -0.4)", (-36, 35.5)), ("Ditch", (-36, 52)), ("Billboard", (-31, 66)),
                      ("Dirt path", (14, -64)), ("Pavement", (-18, 16)), ("Delivery pad", (10, -36.5))):
        x, y = v.px(*pos)
        label(d, (x, y), name, font(16, False), fill=(255, 255, 255))
    stands = []
    for n in sc.root.get("Markers").children:
        p = n.p["cf"].p
        if abs(p[0] - v.cx) > 66 or abs(p[2] - v.cz) > 72:
            continue
        if abs(p[0]) < 18 and abs(p[2]) < 11:
            continue
        x, y = v.px(p[0], p[2])
        arrow(d, (x, y), n.p["cf"].look, (255, 210, 60, 255), 12, 4)
        if n.name.startswith("Inspection_Stand"):
            stands.append((x, y))
            label(d, (x, y + 16), n.name[-1], font(12), fill=(255, 220, 120), bg=(16, 16, 20, 160), pad=2)
            continue
        label(d, (x, y + 18), n.name, font(12, False), fill=(255, 220, 120), bg=(16, 16, 20, 160))
    if stands:
        sx = sum(p[0] for p in stands) / len(stands)
        label(d, (sx, stands[0][1] + 38), "Inspection_Stand1-4", font(12, False), fill=(255, 220, 120),
              bg=(16, 16, 20, 160))
    d.rectangle((0, 0, v.W, 40), fill=(16, 16, 20, 230))
    d.text((14, 9), "PizzaShack - site plan. North up. Yellow arrows = Markers folder (facing); cyan = outside stations.",
           font=font(17), fill=(240, 228, 196))
    img = Image.alpha_composite(img, ov).convert("RGB")
    img.save(os.path.join(out, "plan_site.jpg"), quality=90)
    print("saved plan_site.jpg")


def world():
    v = View(0.0, 0.0, 340.0, 240.0, 5.0)
    raw = os.path.join(out, "plan_world_raw.png")
    render_top(v, raw, lambda n: n.top() != "Items")
    img = Image.open(raw).convert("RGBA")
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for n in sc.root.get("Markers").children:
        if not (n.name.startswith("Spawn") or n.name.startswith("TreeLine") or n.name.startswith("Car_") or
                n.name == "Truck_Stop"):
            continue
        p = n.p["cf"].p
        x, y = v.px(p[0], p[2])
        arrow(d, (x, y), n.p["cf"].look, (255, 210, 60, 255), 12, 4)
        label(d, (x, y + 18), n.name, font(12, False), fill=(255, 220, 120), bg=(16, 16, 20, 160))
    d.rectangle((0, 0, v.W, 34), fill=(16, 16, 20, 230))
    d.text((12, 7), "Whole map (X -165..165, Z -115..115): spawns, tree-line and vehicle markers", font=font(16),
           fill=(240, 228, 196))
    img = Image.alpha_composite(img, ov).convert("RGB")
    img.save(os.path.join(out, "plan_world.jpg"), quality=90)
    print("saved plan_world.jpg")


inside()
site()
world()
