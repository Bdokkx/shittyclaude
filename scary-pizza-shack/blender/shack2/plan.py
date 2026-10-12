"""Top-down plans of the remade map, with labels, and the parts still to come drawn dashed.

    python -m shack2.plan <outdir> [inside] [site] [world] [samples=16] [reuse=1]   (from blender/)
"""
import math
import os
import sys

import bpy  # noqa: I001
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import spsblend as SB
import rbxscene as rs

from . import build as B, layout as L, terrain
from . import interior as IP

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
YELLOW = (255, 210, 60, 255)
CYAN = (40, 230, 255, 255)
PLAN = (255, 150, 60, 255)           # dashed: planned, built in a later pass
MOONC = (170, 200, 255, 255)


def font(s, bold=True):
    return ImageFont.truetype(FONT if bold else FONT_R, s)


class View:
    def __init__(self, cx, cz, w_studs, h_studs, k):
        self.cx, self.cz, self.k = cx, cz, k
        self.W, self.H = int(w_studs * k), int(h_studs * k)
        self.S = max(w_studs, h_studs)

    def px(self, x, z):
        return (self.W / 2 + (x - self.cx) * self.k, self.H / 2 + (z - self.cz) * self.k)


def render_top(sc, view, path, filt, samples, reuse=False):
    if reuse and os.path.exists(path):
        return
    scene = SB.reset()
    coll = bpy.data.collections.new("Map")
    scene.collection.children.link(coll)
    SB.realize(sc, coll, filt)
    SB.day_world(scene, strength=1.05)
    rs.setup_render(scene, view.W, view.H, samples=samples, bloom=False)
    # camera a hair south of its target so "up" in the image is north
    SB.camera(scene, (view.cx, 600, view.cz + 1e-3), (view.cx, 0, view.cz), ortho=view.S)
    scene.camera.data.clip_end = 2000
    rs.render(scene, path)


# ---------------------------------------------------------------- drawing

class Labels:
    """Labels that step aside instead of covering each other."""

    def __init__(self, d):
        self.d, self.boxes = d, []

    def put(self, xy, text, f, fill=(255, 255, 255), bg=(16, 16, 20, 205), pad=4, tries=None):
        d = self.d
        for ox, oy in tries or ((0, 0), (0, -26), (0, 26), (0, -52), (0, 52), (-70, 0), (70, 0), (0, -78),
                                (0, 78), (-90, -30), (90, 30), (-90, 30), (90, -30)):
            p = (xy[0] + ox, xy[1] + oy)
            bb = d.textbbox(p, text, font=f, anchor="mm")
            bb = (bb[0] - pad, bb[1] - pad, bb[2] + pad, bb[3] + pad)
            if not any(bb[0] < b[2] and b[0] < bb[2] and bb[1] < b[3] and b[1] < bb[3] for b in self.boxes):
                break
        self.boxes.append(bb)
        d.rectangle(bb, fill=bg)
        d.text(p, text, font=f, fill=fill, anchor="mm")
        return p


def arrow(d, p, look, col, size=14, width=4):
    x, y = p
    lx, lz = look[0], look[-1]
    n = math.hypot(lx, lz) or 1.0
    lx, lz = lx / n, lz / n
    tip = (x + lx * size, y + lz * size)
    tail = (x - lx * size * 0.6, y - lz * size * 0.6)
    d.line((tail, tip), fill=col, width=width)
    left = (tip[0] - lx * size * 0.55 + lz * size * 0.45, tip[1] - lz * size * 0.55 - lx * size * 0.45)
    right = (tip[0] - lx * size * 0.55 - lz * size * 0.45, tip[1] - lz * size * 0.55 + lx * size * 0.45)
    d.polygon((tip, left, right), fill=col)


def dashed(d, pts, col, width=3, on=9, off=7, closed=False):
    pts = list(pts) + ([pts[0]] if closed else [])
    carry = 0.0
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        seg = math.hypot(bx - ax, by - ay)
        t = -carry
        while t < seg:
            t0, t1 = max(t, 0.0), min(t + on, seg)
            if t1 > t0:
                d.line((ax + (bx - ax) * t0 / seg, ay + (by - ay) * t0 / seg,
                        ax + (bx - ax) * t1 / seg, ay + (by - ay) * t1 / seg), fill=col, width=width)
            t += on + off
        carry = (t - seg) if t > seg else 0.0


def drect(d, v, x0, x1, z0, z1, col=PLAN, width=3):
    a, b = v.px(x0, z0), v.px(x1, z1)
    dashed(d, (a, (b[0], a[1]), b, (a[0], b[1])), col, width, closed=True)


def dcircle(d, v, x, z, r, col=PLAN, width=3, n=48):
    pts = [v.px(x + r * math.cos(2 * math.pi * k / n), z + r * math.sin(2 * math.pi * k / n)) for k in range(n)]
    dashed(d, pts, col, width, closed=True)


def dot(d, p, r, col, outline=(0, 0, 0, 255)):
    d.ellipse((p[0] - r, p[1] - r, p[0] + r, p[1] + r), fill=col, outline=outline)


def footprint(m):
    pts = [c.p["cf"].p for c in m.walk() if c.kind in ("Part", "MeshPart") and c.p["transparency"] < 0.99]
    if not pts:
        pts = [c.p["cf"].p for c in m.walk() if c.kind == "Marker"]
    return np.mean(np.array(pts), 0)


def header(d, v, text, h=46, size=19):
    d.rectangle((0, 0, v.W, h), fill=(16, 16, 20, 232))
    d.text((16, (h - size) // 2 - 1), text, font=font(size), fill=(240, 228, 196))


def legend(d, v, items, size=17):
    w = 26 + sum(40 + d.textlength(t, font=font(size, False)) + 28 for t, _ in items)
    x = v.W - w
    d.rectangle((x, v.H - 44, v.W, v.H), fill=(16, 16, 20, 225))
    x += 16
    for text, draw in items:
        draw(d, (x + 14, v.H - 22))
        d.text((x + 38, v.H - 33), text, font=font(size, False), fill=(255, 255, 255))
        x += 40 + d.textlength(text, font=font(size, False)) + 28


def _leg_stand(d, p):
    arrow(d, p, (1, 0), CYAN, 12, 4)


def _leg_item(d, p):
    dot(d, p, 6, (255, 60, 200, 255))


def _leg_marker(d, p):
    arrow(d, p, (1, 0), YELLOW, 12, 4)


def _leg_plan(d, p):
    dashed(d, ((p[0] - 14, p[1] - 9), (p[0] + 14, p[1] - 9), (p[0] + 14, p[1] + 9), (p[0] - 14, p[1] + 9)),
           PLAN, 3, 6, 4, closed=True)


def _leg_lamp(d, p):
    dot(d, p, 7, (255, 196, 132, 255))


# ---------------------------------------------------------------- inside

def inside(sc, out, samples, reuse):
    v = View(-2.0, 0.0, 44.0, 27.5, 55.0)
    raw = os.path.join(out, "plan_inside_raw.png")

    def filt(n):
        path = n.path()
        if "/Roof/" in path or "/Ceiling/" in path or "/Exterior/" in path:
            return False
        if n.top() == "Stations" and n.p["cf"].p[1] > 8.6:
            return False
        return n.top() in ("Shack", "Stations")
    render_top(sc, v, raw, filt, samples, reuse)
    img = Image.open(raw).convert("RGBA")
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    lab = Labels(d)
    # what later passes add, dashed
    drect(d, v, *L.HOOD)
    dcircle(d, v, IP.FAN[0], IP.FAN[1], IP.FAN_R)
    for m in L.MATS:
        drect(d, v, *m, width=2)
    dot(d, v.px(*L.DRAIN), 6, PLAN)
    for name, (x, z, _) in IP.WORK_LAMPS.items():
        dot(d, v.px(x, z), 8, (255, 196, 132, 255))
    hx0, hx1, hz0, hz1 = IP.HATCH
    drect(d, v, hx0, hx1, hz0, hz1, col=(255, 255, 255, 230))
    # stations, stands and item markers
    st = sc.root.get("Stations")
    names = {"CeilingLamp1": "CeilingLamp1 (ceiling)", "CeilingLamp2": "CeilingLamp2 (ceiling)",
             "Hatch": "Hatch (ceiling)"}
    for m in st.children:
        stand = m.find("Stand")
        if stand is None:
            continue
        sp = stand.p["cf"]
        if abs(sp.p[0]) > 18.5 or abs(sp.p[2]) > 11.5:
            continue
        for c in m.walk():
            if c.kind == "Marker" and c is not stand and not c.name.startswith("Stand"):
                dot(d, v.px(c.p["cf"].p[0], c.p["cf"].p[2]), 6, (255, 60, 200, 255))
        for c in m.children:
            if c.kind == "Marker" and c.name.startswith("Stand"):
                arrow(d, v.px(c.p["cf"].p[0], c.p["cf"].p[2]), c.p["cf"].look, CYAN, 16, 5)
    for m in st.children:
        stand = m.find("Stand")
        if stand is None or abs(stand.p["cf"].p[0]) > 18.5 or abs(stand.p["cf"].p[2]) > 11.5:
            continue
        c = footprint(m)
        lab.put(v.px(c[0], c[2]), names.get(m.name, m.name), font(18))
    spawns = []
    for n in sc.root.get("Markers").children:
        p = n.p["cf"].p
        if abs(p[0]) < 18 and abs(p[2]) < 11:
            x, y = v.px(p[0], p[2])
            arrow(d, (x, y), n.p["cf"].look, YELLOW, 13, 4)
            if n.name.startswith("PlayerSpawn"):
                spawns.append((x, y))
                continue
            lab.put((x, y + 22), n.name, font(14, False), fill=(255, 220, 120), bg=(16, 16, 20, 170))
    if spawns:
        sx = sum(p[0] for p in spawns) / len(spawns)
        sy = max(p[1] for p in spawns)
        lab.put((sx, sy + 24), "PlayerSpawn1-4", font(14, False), fill=(255, 220, 120), bg=(16, 16, 20, 170))
    small = font(14, False)
    for text, (x, z) in (("vent hood + duct", (15.0, -6.9)),
                         ("ceiling fan (Spin)", (IP.FAN[0], IP.FAN[1] + 3.0)), ("drain", (L.DRAIN[0] + 1.6, L.DRAIN[1])),
                         ("mats", (-6.0, -2.2)), ("Radio shelf", (L.RADIO[0], L.RADIO[1] - 1.0))):
        lab.put(v.px(x, z), text, small, fill=(255, 190, 120), bg=(16, 16, 20, 170))
    header(d, v, "Remake, pass 1 (blockout): inside, roof and ceiling off. North up, +X east, +Z south (road). "
           "Room X %d..%d, Z -10..10." % (L.IN_X0, L.IN_X1), size=18)
    legend(d, v, (("Stand", _leg_stand), ("item marker", _leg_item), ("Markers", _leg_marker),
                  ("work lamp (warm spot)", _leg_lamp), ("later pass", _leg_plan)), size=16)
    img = Image.alpha_composite(img, ov).convert("RGB")
    img.save(os.path.join(out, "plan_inside.jpg"), quality=92)
    print("saved plan_inside.jpg", flush=True)


# ---------------------------------------------------------------- site

def site(sc, out, samples, reuse):
    v = View(4.0, 6.0, 200.0, 150.0, 8.0)
    raw = os.path.join(out, "plan_site_raw.png")

    def filt(n):
        return n.top() != "Items" and "/FarTrees/" not in n.path() and "/Hills/" not in n.path()
    render_top(sc, v, raw, filt, samples, reuse)
    img = Image.open(raw).convert("RGBA")
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    lab = Labels(d)
    small, mid = font(13, False), font(15)
    # planned dressing
    for x in L.POLE_X:
        dot(d, v.px(x, L.POLE_Z), 5, PLAN)
    dashed(d, [v.px(x, L.POLE_Z) for x in L.POLE_X], PLAN, 2, 5, 5)
    b = L.BILLBOARD
    fx, fz = b["face"]
    tx, tz = -fz, fx
    pts = [v.px(b["x"] + tx * s * 7.0, b["z"] + tz * s * 7.0) for s in (-1, 1)]
    dashed(d, pts, PLAN, 5, 6, 4)
    arrow(d, v.px(b["x"] + fx * 2, b["z"] + fz * 2), (fx, fz), PLAN, 10, 3)
    for name, s in L.ROAD_SIGNS.items():
        p = v.px(s["x"], s["z"])
        dot(d, p, 5, PLAN)
        arrow(d, p, s["face"], PLAN, 10, 3)
    for name, (x, z) in L.FORECOURT_PROPS.items():
        dot(d, v.px(x, z), 4, PLAN)
    sx0, sx1, sz0, sz1 = L.SHED
    drect(d, v, sx0, sx1, sz0, sz1)
    p = L.PICKUP
    drect(d, v, p["x"] - 4.0, p["x"] + 4.0, p["z"] - 9.0, p["z"] + 9.0)
    for (x, z) in L.YARD_PROPS.values():
        dot(d, v.px(x, z), 4, PLAN)
    for (x, z) in L.PUDDLES:
        dcircle(d, v, x, z, 1.6, width=2, n=16)
    # the moon's direction from the serving window, and the sight line through it
    w = v.px(0.0, 11.0)
    az = math.atan2(L.MOON[0], L.MOON[2])
    far = v.px(math.sin(az) * 120, 11.0 + math.cos(az) * 120)
    dashed(d, (w, far), MOONC, 3, 12, 6)
    lab.put(v.px(math.sin(az) * 70 + 9, 11 + math.cos(az) * 70), "to the moon (low, SSE)", small, fill=(200, 220, 255))
    # stations outside
    st = sc.root.get("Stations")
    for name in ("Generator", "Dumpster", "YardGate", "StreetLamp", "YardLamp", "BusStop", "RoadSign"):
        m = st.find(name)
        c = footprint(m)
        lab.put(v.px(c[0], c[2]), name, mid, fill=(120, 255, 255))
    # markers (not inside, not the car path)
    for n in sc.root.get("Markers").children:
        p = n.p["cf"].p
        if abs(p[0] - v.cx) > 98 or abs(p[2] - v.cz) > 73:
            continue
        if abs(p[0]) < 18 and abs(p[2]) < 11:
            continue
        x, y = v.px(p[0], p[2])
        if n.name.startswith("Car_Path"):
            dot(d, (x, y), 3, YELLOW, None)
            continue
        arrow(d, (x, y), n.p["cf"].look, YELLOW, 11, 3)
        if n.name.startswith("Inspection_Stand") and n.name[-1] != "1":
            continue
        text = "Inspection_Stand1-4" if n.name.startswith("Inspection_Stand") else n.name
        lab.put((x, y + 16), text, small, fill=(255, 220, 120), bg=(16, 16, 20, 170))
    for text, (x, z) in (("Shack", (0, 0)), ("Yard", (-8, -30)), ("Forecourt (cracked concrete)", (-10, 18.5)),
                         ("Lot: bay A (oil stains)", (29, -7)), ("bay B: old pickup", (39, 15)),
                         ("Road (2 lanes, gravel shoulders)", (-30, 34)), ("Ditch", (-30, 52.5)),
                         ("Culvert + farm track", (30, 60)), ("Meadow (low cover under the moon)", (34, 75)),
                         ("Telegraph poles + wires", (-20, 61)), ("Billboard (both faces)", (-60, 69)),
                         ("Generator lean-to", (-20, -42.5)), ("Delivery track", (10, -64)),
                         ("Forest wall, 3 rows", (-75, -40)), ("string lights", (-24, 21.5)),
                         ("Speed sign", (62, 18)), ("PAPA STUD'S OPEN LATE", (81, 13)), ("Deer sign", (-84, 57))):
        lab.put(v.px(x, z), text, small)
    header(d, v, "Remake, pass 1: site. North up. Yellow = Markers (dots = Car_Path1..N, driving west on the north "
           "lane); cyan = outside stations; orange dashed = built in later passes.", h=36, size=15)
    img = Image.alpha_composite(img, ov).convert("RGB")
    img.save(os.path.join(out, "plan_site.jpg"), quality=90)
    print("saved plan_site.jpg", flush=True)


# ---------------------------------------------------------------- world

def world(sc, out, samples, reuse):
    v = View(0.0, 0.0, 700.0, 700.0, 2.0)
    raw = os.path.join(out, "plan_world_raw.png")
    render_top(sc, v, raw, lambda n: n.top() != "Items", samples, reuse)
    img = Image.open(raw).convert("RGBA")
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    lab = Labels(d)
    small = font(13, False)
    for r, text in ((L.FOREST_R[0], None), (L.FOREST_R[1], "forest wall 52..92"), (L.FAR_R[1], "far tree masses"),
                    (L.HILLS_R[1], "ring of dark hills")):
        dcircle(d, v, 0, 0, r, col=(255, 255, 255, 140), width=2, n=120)
        if text:
            lab.put(v.px(-r * 0.71, -r * 0.71), text, small)
    m = L.MEADOW
    for a in (m["az0"], m["az1"]):
        t = math.radians(a)
        dashed(d, (v.px(math.sin(t) * m["r0"], math.cos(t) * m["r0"]),
                   v.px(math.sin(t) * (m["r1"] + 140), math.cos(t) * (m["r1"] + 140))), MOONC, 2)
    az = math.atan2(L.MOON[0], L.MOON[2])
    arrow(d, v.px(math.sin(az) * 300, math.cos(az) * 300), (math.sin(az), math.cos(az)), MOONC, 22, 5)
    dashed(d, (v.px(0, 0), v.px(math.sin(az) * 300, math.cos(az) * 300)), MOONC, 3, 12, 6)
    lab.put(v.px(math.sin(az) * 250 + 36, math.cos(az) * 250), "moon: 25 deg east of south, 14 deg up", font(14),
            fill=(200, 220, 255))
    lab.put(v.px(30, 175), "low run of trees under the moon", small, fill=(200, 220, 255))
    dot(d, v.px(*L.MAST), 7, (255, 60, 50, 255))
    lab.put(v.px(L.MAST[0] + 50, L.MAST[1]), "radio mast, red light", small, fill=(255, 150, 140))
    dot(d, v.px(*L.HILL_WINDOW), 7, (255, 210, 120, 255))
    lab.put(v.px(L.HILL_WINDOW[0] - 60, L.HILL_WINDOW[1]), "one lit window", small, fill=(255, 220, 160))
    pts = terrain.centre_line()
    dashed(d, [v.px(x, z) for x, z in pts], (255, 255, 255, 200), 2, 4, 4)
    (we, wd, wl), (ee, ed, el) = L.road_ends()
    for (p, dd, ln), text in (((we, wd, wl), "road bends away SW into the trees"),
                              ((ee, ed, el), "road bends away NE into the trees")):
        q = (p[0] + dd[0] * ln, p[1] + dd[1] * ln)
        lab.put(v.px(q[0] + dd[0] * 30, q[1] + dd[1] * 30), text, small)
    for n in sc.root.get("Markers").children:
        p = n.p["cf"].p
        if n.name.startswith("Car_Path"):
            dot(d, v.px(p[0], p[2]), 2, YELLOW, None)
            continue
        if not (n.name.startswith("Spawn") or n.name.startswith("TreeLine") or n.name in ("Car_Start", "Car_End")):
            continue
        x, y = v.px(p[0], p[2])
        arrow(d, (x, y), n.p["cf"].look, YELLOW, 10, 3)
        lab.put((x, y + 14), n.name, font(11, False), fill=(255, 220, 120), bg=(16, 16, 20, 160))
    header(d, v, "Remake, pass 1: the whole world (X, Z -350..350). Spawn_RoadWest/East and the TreeLine markers move "
           "to the new road ends and forest edge in pass 5.", h=32, size=14)
    img = Image.alpha_composite(img, ov).convert("RGB")
    img.save(os.path.join(out, "plan_world.jpg"), quality=90)
    print("saved plan_world.jpg", flush=True)


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    opts = dict(a.split("=") for a in sys.argv[2:] if "=" in a)
    samples = int(opts.get("samples", 16))
    reuse = bool(opts.get("reuse"))
    sc = B.build(items=False)
    for which in [a for a in sys.argv[2:] if "=" not in a] or ["inside", "site", "world"]:
        {"inside": inside, "site": site, "world": world}[which](sc, out, samples, reuse)


if __name__ == "__main__":
    main()
