"""Contact sheets: every item (labelled tiles) and every station seen from its Stand
(with the markers shown as small arrows), for checking and for the README.

    python blender/render_sheets.py <outdir> [items] [stations] [samples=16] [only=A,B] [reuse=1]
"""
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy  # noqa: E402,I001
import numpy as np  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

import map_items as I  # noqa: E402
import scene_build  # noqa: E402
import spsblend as SB  # noqa: E402
import spsgeo as G  # noqa: E402
import spslib  # noqa: E402
import rbxscene as rs  # noqa: E402

out = sys.argv[1]
os.makedirs(out, exist_ok=True)
want = set(a for a in sys.argv[2:] if "=" not in a) or {"items", "stations"}
opts = dict(a.split("=") for a in sys.argv[2:] if "=" in a)
samples = int(opts.get("samples", 16))
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def font(size, bold=True):
    return ImageFont.truetype(FONT if bold else FONT_R, size)


def sheet(tiles, cols, title, path, tw, th):
    rows = int(math.ceil(len(tiles) / cols))
    head = 70
    img = Image.new("RGB", (cols * tw, head + rows * th), (24, 26, 30))
    d = ImageDraw.Draw(img)
    d.text((20, 18), title, fill=(240, 228, 196), font=font(30))
    for k, (p, label, sub) in enumerate(tiles):
        x, y = (k % cols) * tw, head + (k // cols) * th
        img.paste(Image.open(p).convert("RGB").resize((tw, th)), (x, y))
        d.rectangle((x, y + th - 46, x + tw, y + th), fill=(20, 20, 24))
        d.text((x + 10, y + th - 44), label, fill=(255, 255, 255), font=font(20))
        if sub:
            d.text((x + 10, y + th - 20), sub, fill=(190, 190, 180), font=font(14, False))
    img.save(path, quality=92)
    print("sheet", path)


# ---------------------------------------------------------------- items

def render_items():
    tiles = []
    tw, th = 420, 340
    for it in I.all_items():
        sc = spslib.Scene()
        sc.folder(sc.root, "Items")
        I.place(sc, sc.root.get("Items"), it, spslib.CF())
        scene = SB.reset()
        coll = bpy.data.collections.new("Item")
        scene.collection.children.link(coll)
        SB.realize(sc, coll)
        SB.day_world(scene, strength=0.9)
        rs.setup_render(scene, tw * 2, th * 2, samples=samples, bloom=False)
        lo, hi = it.bbox()
        c = (lo + hi) / 2
        r = max(np.linalg.norm(hi - lo) / 2, 0.3)
        d = np.array((1.0, 0.75, 1.3))
        d /= np.linalg.norm(d)
        cam = SB.camera(scene, c + d * r * 3.2, c, lens=50)
        # ground disc under the item
        me = bpy.data.meshes.new("floor")
        g = G.cyl(r * 3, 0.02, 32, "y", (c[0], lo[1] - 0.011, c[2]))
        me.from_pydata(SB.rb2bl(np.array(g.v)).tolist(), [], g.f)
        me.materials.append(SB.material((70, 74, 80), "SmoothPlastic", 0.0))
        ob = bpy.data.objects.new("floor", me)
        coll.objects.link(ob)
        p = os.path.join(out, "item_%s.png" % it.name)
        rs.render(scene, p)
        s = it.size()
        tiles.append((p, it.name, "%.1f x %.1f x %.1f, %d tris" % (s[0], s[1], s[2], it.tris())))
    sheet(tiles, 6, "Scary Pizza Shack - hand-held items (Workspace.PizzaShack.Items)", os.path.join(out, "items_sheet.jpg"),
          tw, th)


# ---------------------------------------------------------------- stations

# station: (camera position, look-at), Roblox space
VIEWS = {
    "BackDoor": ((-11.5, 6.2, -3.0), (-15.5, 3.6, -10.0)),
    "Fridge": ((-8.2, 6.0, -1.4), (-11.0, 4.2, -8.0)),
    "DoughStation": ((-7.0, 6.8, -2.0), (-7.0, 3.9, -8.4)),
    "SauceStation": ((-1.0, 7.2, -1.2), (-1.0, 4.2, -8.6)),
    "ChopStation": ((5.0, 6.8, -2.0), (5.0, 3.9, -8.6)),
    "ToppingRail": ((10.0, 6.8, -2.0), (10.0, 3.8, -8.6)),
    "Oven": ((7.0, 6.0, -0.6), (15.0, 4.4, -2.6)),
    "PeelRack": ((8.4, 5.8, 4.6), (15.0, 4.6, 1.4)),
    "CutTable": ((9.0, 6.6, 2.4), (15.0, 3.6, 4.0)),
    "Bin": ((8.6, 5.2, 4.2), (12.3, 1.4, 6.0)),
    "BoxStation": ((9.0, 6.6, 6.0), (15.0, 2.6, 8.0)),
    "Register": ((7.5, 6.8, 1.8), (7.5, 4.0, 8.6)),
    "RulesBoard": ((8.5, 6.4, 0.6), (8.5, 6.6, 10.0)),
    "PlushieShelf": ((11.5, 6.2, 2.2), (14.5, 6.4, 9.6)),
    "ServingWindow": ((0.0, 6.8, 1.4), (0.0, 4.4, 10.0)),
    "ShutterButton": ((-3.8, 6.2, 3.8), (-6.0, 5.2, 9.6)),
    "CCTVDesk": ((-10.0, 6.8, 1.8), (-10.0, 4.6, 9.0)),
    "Sink": ((-12.0, 6.6, 2.4), (-15.2, 3.6, 8.6)),
    "StorageShelf": ((-10.2, 6.0, 4.0), (-16.0, 4.6, 4.0)),
    "DrinksCooler": ((-9.8, 6.0, 0.0), (-16.0, 4.4, 0.0)),
    "FuseBox": ((-13.6, 6.2, -4.2), (-16.6, 5.6, -8.4)),
    "Hatch": ((4.5, 4.6, 4.6), (4.5, 9.4, -1.5)),
    "CeilingLamp1": ((-6.0, 4.6, 6.0), (-6.0, 7.6, 0.5)),
    "CeilingLamp2": ((6.5, 4.9, 5.2), (6.5, 7.8, 2.5)),
    "Generator": ((-11.5, 7.0, -26.5), (-20.0, 2.0, -34.0)),
    "Dumpster": ((11.5, 7.0, -23.5), (19.0, 2.0, -30.0)),
    "YardGate": ((10.0, 6.0, -37.0), (10.0, 3.4, -47.0)),
    "StreetLamp": ((-1.0, 6.0, 31.0), (-9.0, 6.0, 21.0)),
    "YardLamp": ((9.0, 6.0, -15.0), (3.0, 6.0, -27.0)),
    "BusStop": ((40.0, 5.0, 33.0), (40.0, 3.6, 20.5)),
    "RoadSign": ((31.0, 8.0, 37.0), (26.0, 13.0, 21.0)),
}
OUTSIDE = {"Generator", "Dumpster", "YardGate", "StreetLamp", "YardLamp", "BusStop", "RoadSign"}


def marker_geo(sc):
    """Small arrows for every marker (preview only)."""
    arrow = G.Geo().add([G.box(0.5, 0.12, 0.5), G.frustum(0.0, 0.18, 0.5, 4, "z", (0, 0, -0.45))])
    b = SB.Builder()
    for n in sc.nodes("Marker"):
        V = np.array(arrow.v)
        W = (n.p["cf"].R @ V.T).T + n.p["cf"].p + (0, 0.07, 0)
        col = (40, 220, 255) if n.name == "Stand" else (255, 60, 200)
        b.add((col, "Neon", 0.0), W, arrow.f)
    return b


def marker_label(m):
    """Marker names of a station, numbered runs grouped: 'Slot1-12, Stand'."""
    groups = {}
    for c in m.children:
        if c.kind != "Marker":
            continue
        mm = re.match(r"^(.*?)(\d+)$", c.name)
        key, num = (mm.group(1), int(mm.group(2))) if mm else (c.name, None)
        groups.setdefault(key, []).append(num)
    parts = []
    for key in sorted(groups):
        nums = sorted(x for x in groups[key] if x is not None)
        if None in groups[key]:
            parts.append(key)
        if len(nums) > 2 and nums == list(range(nums[0], nums[-1] + 1)):
            parts.append("%s%d-%d" % (key, nums[0], nums[-1]))
        else:
            parts.extend("%s%d" % (key, x) for x in nums)
    return ", ".join(parts)


def render_stations():
    """only=A,B renders just those tiles; reuse=1 keeps tiles that already exist.
    The sheet is always recomposed from every tile."""
    sc = scene_build.build(items=False)
    tw, th = 640, 400
    stations = sc.root.get("Stations")
    only = set(opts["only"].split(",")) if "only" in opts else None
    reuse = bool(opts.get("reuse"))

    def tile_path(m):
        return os.path.join(out, "station_%s.png" % m.name)

    shown = [m for m in stations.children if m.name in VIEWS]
    for outside in (False, True):
        todo = [m for m in shown if (m.name in OUTSIDE) == outside
                and (only is None or m.name in only)
                and not (reuse and os.path.exists(tile_path(m)))]
        if not todo:
            continue
        scene = SB.reset()
        coll = bpy.data.collections.new("Map")
        scene.collection.children.link(coll)
        SB.realize(sc, coll)
        marker_geo(sc).build(coll, emit_scale=0.6)
        if outside:
            SB.day_world(scene, strength=0.8)
        else:
            SB.night_world(scene, strength=0.3, moon=0.3)
            SB.add_lights(sc, coll)
            SB.point_light(coll, (0, 8.6, 0), 700, (1, 0.9, 0.75), name="Fill")
        rs.setup_render(scene, int(tw * 1.5), int(th * 1.5), samples=samples, bloom=not outside)
        for m in todo:
            pos, tgt = VIEWS[m.name]
            SB.camera(scene, pos, tgt, lens=18 if not outside else 24, name="Cam_" + m.name)
            rs.render(scene, tile_path(m))
    sheet([(tile_path(m), m.name, marker_label(m)) for m in shown], 4,
          "Scary Pizza Shack - every station (cyan arrow = Stand, pink = its other markers)",
          os.path.join(out, "stations_sheet.jpg"), tw, th)


if "items" in want:
    render_items()
if "stations" in want:
    render_stations()
