"""Batch-2 preview renders.

    python blender/render_assets.py <outdir> [chars] [kit] [vehicles] [plushies] [uniforms] [samples=24]

R6 dummies (classic proportions, plain colours) are preview-only stand-ins for players
and customers; the head on them is a stand-in for the classic head mesh.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy  # noqa: E402,I001
import numpy as np  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

import assets_chars as AC  # noqa: E402
import assets_kit as AK  # noqa: E402
import assets_r6 as R6  # noqa: E402
import spsblend as SB  # noqa: E402
import spsgeo as G  # noqa: E402
import spslib  # noqa: E402
import rbxscene as rs  # noqa: E402
from spsgeo import CF  # noqa: E402

out = sys.argv[1]
os.makedirs(out, exist_ok=True)
want = [a for a in sys.argv[2:] if "=" not in a] or ["chars", "kit", "vehicles", "plushies", "uniforms"]
opts = dict(a.split("=") for a in sys.argv[2:] if "=" in a)
samples = int(opts.get("samples", 24))
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

NOOB = {"Torso": (13, 105, 172), "Head": (245, 205, 48), "Left Arm": (245, 205, 48), "Right Arm": (245, 205, 48),
        "Left Leg": (40, 127, 71), "Right Leg": (40, 127, 71)}
PLAIN = {"Torso": (150, 150, 156), "Head": (226, 196, 164), "Left Arm": (226, 196, 164),
         "Right Arm": (226, 196, 164), "Left Leg": (90, 92, 104), "Right Leg": (90, 92, 104)}


def font(size, bold=True):
    return ImageFont.truetype(FONT if bold else FONT_R, size)


def sheet(tiles, cols, title, path, tw, th, sub_h=46):
    rows = int(math.ceil(len(tiles) / cols))
    head = 70
    img = Image.new("RGB", (cols * tw, head + rows * th), (24, 26, 30))
    d = ImageDraw.Draw(img)
    d.text((20, 18), title, fill=(240, 228, 196), font=font(30))
    for k, (p, label, sub) in enumerate(tiles):
        x, y = (k % cols) * tw, head + (k // cols) * th
        img.paste(Image.open(p).convert("RGB").resize((tw, th)), (x, y))
        d.rectangle((x, y + th - sub_h, x + tw, y + th), fill=(20, 20, 24))
        d.text((x + 10, y + th - sub_h + 2), label, fill=(255, 255, 255), font=font(20))
        if sub:
            d.text((x + 10, y + th - 20), sub, fill=(190, 190, 180), font=font(14, False))
    img.save(path, quality=92)
    print("sheet", path)


def floor(coll, size=(400, 400), y=0.0, color=(84, 88, 96), c=(0, 0)):
    me = bpy.data.meshes.new("floor")
    g = G.box(size[0], 0.2, size[1], (c[0], y - 0.1, c[1]))
    me.from_pydata(SB.rb2bl(np.array(g.v)).tolist(), [], g.f)
    mat = SB.material(color, "Plastic", 0.0).copy()      # matte, so the sun leaves no glare patch
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.92
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.15
    me.materials.append(mat)
    ob = bpy.data.objects.new("floor", me)
    coll.objects.link(ob)


def new_scene(sc, day=True, strength=0.9):
    scene = SB.reset()
    coll = bpy.data.collections.new("A")
    scene.collection.children.link(coll)
    SB.realize(sc, coll)
    if day:
        SB.day_world(scene, strength=strength)
    return scene, coll


def finish(scene, cam, png, items, bar=92, note=None):
    """Save png as .jpg with a bar underneath naming each model under where it stands.
    items: [(name, sub line, Roblox position of its feet)]."""
    from bpy_extras.object_utils import world_to_camera_view
    from mathutils import Vector
    img = Image.open(png).convert("RGB")
    w, h = img.size
    extra = 34 if note else 0
    out_img = Image.new("RGB", (w, h + bar + extra), (22, 24, 28))
    out_img.paste(img, (0, 0))
    d = ImageDraw.Draw(out_img)
    placed = []
    for name, sub, pos in sorted(items, key=lambda it: world_to_camera_view(
            scene, cam, Vector(SB.rb2bl(np.array(it[2], float))))[0]):
        x = world_to_camera_view(scene, cam, Vector(SB.rb2bl(np.array(pos, float))))[0] * w
        half = max(d.textlength(name, font=font(26)), d.textlength(sub, font=font(18, False))) / 2 + 12
        lo, hi = max(x - half, 8), min(x + half, w - 8)
        if placed and lo < placed[-1]:
            print("WARNING: labels collide near", name)
        placed.append(hi)
        for txt, fnt, y in ((name, font(26), h + 12), (sub, font(18, False), h + 50)):
            tw = d.textlength(txt, font=fnt)
            xx = min(max(x - tw / 2, 8), w - tw - 8)
            d.text((xx, y), txt, fill=(255, 255, 255) if fnt.size == 26 else (196, 196, 186), font=fnt)
    if note:
        d.text((14, h + bar + 4), note, fill=(150, 150, 142), font=font(17, False))
    jpg = png[:-4] + ".jpg"
    out_img.save(jpg, quality=90)
    print("saved", jpg)


def model_size(sc, model, skip=("HumanoidRootPart", "Base", "Zone", "Gate", "Handle")):
    pts = []
    for n in model.walk():
        if n.kind not in ("Part", "MeshPart") or n.name in skip or n.p["transparency"] >= 0.99:
            continue
        if n.kind == "MeshPart":
            V = (n.p["cf"].R @ np.array(sc.geoms[n.p["mesh"]].v).T).T + n.p["cf"].p
        else:
            hh = np.abs(n.p["cf"].R) @ (np.array(n.p["size"]) / 2)
            V = np.array([n.p["cf"].p - hh, n.p["cf"].p + hh])
        pts.append(V)
    V = np.vstack(pts)
    return V.max(0) - V.min(0)


def fmt_size(v):
    return " x ".join(("%.1f" % a).rstrip("0").rstrip(".") for a in v)


# ---------------------------------------------------------------- kit sheet

BACK_VIEW = {"Long", "Bun", "Ponytail", "Backpack", "Hoodie", "BaldRing"}


def render_kit():
    sc = spslib.Scene("Preview")
    f = sc.folder(sc.root, "Kit")
    spots = {}
    for k, name in enumerate(AK.ORDER):
        x, z = (k % 11) * 8.0, (k // 11) * 10.0
        m, parts = R6.build(sc, f, "Dummy%d" % k, R6.Body(), CF((x, 0, z)), PLAIN, humanoid=False, attachments=False)
        cat, body, fn, notes = AK.KIT[name]
        AK.place(sc, f, name, parts[body].p["cf"])
        spots[name] = (x, z, body)
    scene, coll = new_scene(sc)
    floor(coll, (200, 120), 0.0, (84, 88, 96), (40, 10))
    tw, th = 420, 420
    rs.setup_render(scene, tw, th, samples=samples, bloom=False)
    tiles = []
    only = opts.get("only", "").split(",") if opts.get("only") else AK.ORDER
    for name in only:
        x, z, body = spots[name]
        cat = AK.KIT[name][0]
        back = name in BACK_VIEW
        sgn = 1 if back else -1
        if body == "Head":
            tgt, dist, lens = (x, 4.55, z), 3.6, 50
        elif body == "Torso":
            tgt, dist, lens = (x, 3.6, z), 6.0, 50
        else:
            tgt, dist, lens = (x + 1.3, 2.0, z - 0.9), 5.0, 50
        way = (0.5, 0.25, sgn * 1.0) if body != "Right Arm" else (0.85, 0.55, -0.9)
        cam = np.array(tgt) + np.array(way) * dist
        SB.camera(scene, tuple(cam), tgt, lens=lens, name="C_" + name)
        p = os.path.join(out, "kit_%s.png" % name)
        rs.render(scene, p)
        tris = sum(g.tris() for *_, g in AK.KIT[name][2]())
        tiles.append((p, name, "%s on %s, %d tris%s" % (cat, body, tris, " (back)" if back else "")))
    if len(tiles) == len(AK.ORDER):
        sheet(tiles, 6, "Scary Pizza Shack - CustomerKit (each piece on a plain R6 dummy)",
              os.path.join(out, "kit_sheet.jpg"), 360, 360)
    else:
        sheet(tiles, min(len(tiles), 6), "CustomerKit (test)", os.path.join(out, "kit_test.jpg"), 360, 360)


# ---------------------------------------------------------------- characters line-up

def render_chars():
    import assets_papa as PAPA
    sc = spslib.Scene("Preview")
    f = sc.folder(sc.root, "Line")
    xs = {"Dummy": 13.0, "Customer": 6.6, "Watcher": 0.2, "PapaStud": -8.4, "PapaSide": -19.0}
    R6.build(sc, f, "Dummy", R6.Body(), CF((xs["Dummy"], 0, 0)), NOOB, humanoid=False)
    m, parts = R6.build(sc, f, "Customer", R6.Body(), CF((xs["Customer"], 0, 0)), PLAIN, humanoid=False)
    AC.passenger(sc, f, parts["Torso"].p["cf"])
    w = AC.watcher(sc, f, CF((xs["Watcher"], 0, 0)))
    pose(w, "Right Arm", 7)            # arms turned out a little so their length shows
    pose(w, "Left Arm", -7)
    papa = PAPA.papa_stud(sc, f, CF((xs["PapaStud"], 0, 0)))
    PAPA.papa_stud(sc, f, CF((xs["PapaSide"], 0, 0), G.ry(-90)), name="PapaSide")
    top = model_size(sc, papa)[1]
    eye, _ = PAPA.eye_height()
    scene, coll = new_scene(sc, strength=0.85)
    floor(coll, (160, 120), 0.0, (78, 82, 90))
    rs.setup_render(scene, 1920, 900, samples=samples, bloom=True)
    items = [("R6 dummy", "for scale, 5 tall", (xs["Dummy"], 0, 0)),
             ("Passenger", "on a customer's Torso", (xs["Customer"], 0, 0)),
             ("Watcher", "1.18x, arms 1.3x long", (xs["Watcher"], 0, 0)),
             ("PapaStud", "%.1f to the hat top, eyes %.1f over the root" % (top, eye), (xs["PapaStud"], 0, 0)),
             ("PapaStud", "from the side", (xs["PapaSide"], 0, 0))]
    for name, pos, tgt in (("characters_front", (-2.0, 8.5, -36.0), (-4.0, 4.6, 0.0)),
                           ("characters_back", (-8.0, 8.5, 36.0), (-4.0, 4.6, 0.0))):
        cam = SB.camera(scene, pos, tgt, lens=30, name=name)
        p = os.path.join(out, name + ".png")
        rs.render(scene, p)
        its = items if name == "characters_front" else [(a, b, (x, y, z)) for a, b, (x, y, z) in items]
        finish(scene, cam, p, its, note="Watcher's arms turned out 7 degrees for the picture" +
               ("" if name == "characters_front" else "; seen from behind"))
    # close look at the mask and the hands
    cam = SB.camera(scene, (xs["PapaStud"] - 3.0, 8.4, -10.0), (xs["PapaStud"], 6.6, 0.0), lens=40, name="papa_close")
    p = os.path.join(out, "papa_close.png")
    rs.render(scene, p)
    finish(scene, cam, p, [("PapaStud", "Mask, MaskCrust, MaskEyes (Neon), MaskPupils, MaskGrin, MaskCheeks, "
                                        "MaskPepperoni; HatBand, HatPuff; PeelHandle, PeelBlade",
                            (xs["PapaStud"], 0, 0))])
    render_papa_night()


def render_papa_night():
    """Papa Stud 100 studs out at night, seen at a Roblox camera's field of view (78 degrees
    vertical): what a player at the window gets. A 4x crop of the same frame beside it."""
    import assets_papa as PAPA
    sc = spslib.Scene("Night")
    f = sc.folder(sc.root, "N")
    PAPA.papa_stud(sc, f, CF((0.0, 0.0, 0.0), G.ry(180)))
    scene, coll = new_scene(sc, day=False)
    SB.night_world(scene, color=(0.05, 0.07, 0.12), strength=0.6, moon=0.25, moon_from=(0.3, 0.5, 1.0))
    floor(coll, (400, 400), 0.0, (24, 30, 26))
    W, H = 1280, 720
    rs.setup_render(scene, W, H, samples=samples, bloom=True)
    cam = SB.camera(scene, (0.0, 6.0, 100.0), (0.0, 6.5, 0.0), lens=30, name="night")
    cam.data.sensor_fit = "VERTICAL"
    cam.data.angle = math.radians(78.0)
    p = os.path.join(out, "papa_night_100.png")
    rs.render(scene, p)
    img = Image.open(p).convert("RGB")
    cw, ch = 200, 112
    crop = img.crop((W // 2 - cw // 2, H // 2 - ch // 2 - 6, W // 2 + cw // 2, H // 2 + ch // 2 - 6))
    crop = crop.resize((cw * 4, ch * 4), Image.NEAREST)
    outi = Image.new("RGB", (W + cw * 4 + 20, max(H, ch * 4)), (12, 12, 14))
    outi.paste(img, (0, 0))
    outi.paste(crop, (W + 20, (H - ch * 4) // 2))
    d = ImageDraw.Draw(outi)
    d.text((14, H - 40), "100 studs, night, 78 degree camera (left); the middle of the frame, 4x (right)",
           fill=(200, 200, 190), font=font(22, False))
    outi.save(p[:-4] + ".jpg", quality=90)
    os.remove(p)
    print("saved", p[:-4] + ".jpg")


# ---------------------------------------------------------------- helpers for posed previews

def swing(root_node, piece_name, angle_deg, axis="y"):
    """Preview only: turn a moving piece (and the parts welded to it) about its pivot."""
    import assets_vehicles  # noqa: F401
    piece = root_node.find(piece_name)
    pv = piece.p["cf"] * piece.p["pivot"]
    R = {"x": G.rx, "y": G.ry, "z": G.rz}[axis](angle_deg)
    M = pv * CF((0, 0, 0), R) * pv.inv()
    moved = {piece}
    for n in root_node.walk():
        if n.kind == "Weld" and n.p["part0"] is piece:
            moved.add(n.p["part1"])
    for n in moved:
        n.p["cf"] = M * n.p["cf"]


def pose(model, limb_name, angle_deg, axis="z"):
    """Preview only: turn an R6 limb (and the parts welded to it) about its Motor6D hinge,
    about the Torso's own axis (z: out to the side, x: forward/back)."""
    limb = model.find(limb_name)
    j = [n for n in model.walk() if n.kind == "Motor" and n.p["part1"] is limb][0]
    pv = CF(j.p["hinge"].p, j.p["part0"].p["cf"].R)
    M = pv * CF((0, 0, 0), {"x": G.rx, "y": G.ry, "z": G.rz}[axis](angle_deg)) * pv.inv()
    moved = {limb}
    for n in model.walk():
        if n.kind == "Weld" and n.p["part0"] is limb:
            moved.add(n.p["part1"])
    for n in moved:
        n.p["cf"] = M * n.p["cf"]


# ---------------------------------------------------------------- vehicles

def render_vehicles():
    import assets_vehicles as AV
    sc = spslib.Scene("Preview")
    f = sc.folder(sc.root, "V")
    car = AV.inspector_car(sc, f, CF((-16, 0, 0)))
    truck = AV.delivery_truck(sc, f, CF((0, 0, 0)))
    v = AV.van(sc, f, CF((16, 0, 0)))
    body = ("HumanoidRootPart", "Base", "Zone", "Gate", "Handle", "Mirrors", "Ramp")
    sizes = {m.name: fmt_size(model_size(sc, m, body)) for m in (car, truck, v)}
    sizes["Van"] += " + Ramp"
    for nm in ("DoorL", "DoorR"):
        d = v.find(nm)
        swing(v, nm, d.p["attrs"]["OpenAngle"])
    dd = car.find("DriverDoor")                       # an openable Model: turn all of it about its pivot
    pv = dd.p["primary"].p["cf"] * dd.p["primary"].p["pivot"]
    M_ = pv * CF((0, 0, 0), G.ry(dd.p["attrs"]["OpenAngle"])) * pv.inv()
    for n in dd.walk():
        if n.kind in ("Part", "MeshPart"):
            n.p["cf"] = M_ * n.p["cf"]
    crew = [((14.4, 1.6, 0.6), NOOB), ((17.6, 1.6, 2.2), PLAIN), ((14.8, 1.6, 4.6), PLAIN), ((17.3, 1.6, 6.4), NOOB)]
    for k, (pos, cols) in enumerate(crew):
        R6.build(sc, f, "Crew%d" % k, R6.Body(), CF(pos, G.ry(180)), cols, humanoid=False, attachments=False)
    R6.build(sc, f, "Scale", R6.Body(), CF((-8.0, 0, -13.0)), NOOB, humanoid=False, attachments=False)
    scene, coll = new_scene(sc, strength=0.85)
    floor(coll, (200, 160), 0.0, (74, 78, 86))
    rs.setup_render(scene, 1920, 960, samples=samples, bloom=False)
    items = [("InspectorCar", sizes["InspectorCar"] + " (W x H x L), DriverDoor open", (-16, 0, -9.5)),
             ("DeliveryTruck", sizes["DeliveryTruck"], (0, 0, -12)),
             ("Van", sizes["Van"], (16, 0, -9.5))]
    back = [(a, b, (p[0], 0, -p[2])) for a, b, p in items]
    for name, pos, tgt, lens, its, note in (
            ("vehicles_front", (-30.0, 19.0, -46.0), (1.0, 3.0, 0.0), 30, items,
             "R6 dummy for scale; sizes without the mirrors"),
            ("vehicles_back", (-26.0, 16.0, 50.0), (2.0, 3.5, 2.0), 30, back,
             "Van doors swung to their OpenAngle, four R6 inside")):
        cam = SB.camera(scene, pos, tgt, lens=lens, name=name)
        p = os.path.join(out, name + ".png")
        rs.render(scene, p)
        finish(scene, cam, p, its, note=note)
    cam = SB.camera(scene, (22.0, 9.5, 27.0), (16.0, 4.6, 6.0), lens=32, name="van_back")
    p = os.path.join(out, "van_back.png")
    rs.render(scene, p)
    finish(scene, cam, p, [("Van from the back", "DoorL -135, DoorR 135 (OpenAngle), Ramp, Sign above the opening",
                            (16.0, 0, 9.5))], bar=92)


# ---------------------------------------------------------------- plushies

def render_plushies():
    import assets_plush as AP
    sc = spslib.Scene("Preview")
    f = sc.folder(sc.root, "P")
    pl = AP.plushies(sc, f, CF((5.4, 0, 0)), spacing=-1.8)
    scene, coll = new_scene(sc, strength=0.9)
    floor(coll, (60, 40), 0.0, (120, 96, 72))
    rs.setup_render(scene, 1920, 760, samples=samples, bloom=False)
    cam = SB.camera(scene, (0.0, 4.2, -13.4), (0.0, 0.6, 0.0), lens=36, name="plush")
    p = os.path.join(out, "plushies.png")
    rs.render(scene, p)
    items = [(m.name, "%.2f tall" % model_size(sc, m)[1], (5.4 - 1.8 * k, 0, 0)) for k, m in enumerate(pl.children)]
    finish(scene, cam, p, items)


# ---------------------------------------------------------------- uniforms on dummies

OUTFITS = [("PizzaCap", "Apron", "NameTag"), ("ChefHat", "ApronStriped", "OvenMittL", "OvenMittR"),
           ("PaperHat", "ApronStained", "NameTag"), ("Visor", "HiVisVest", "Headset"),
           ("Bandana", "Apron"), ("DeliveryHelmet", "HiVisVest")]
SHIRTS = [(70, 90, 140), (60, 120, 80), (150, 60, 60), (90, 90, 96), (120, 80, 140), (60, 60, 66)]


def render_uniforms():
    import assets_uniforms as AU
    sc = spslib.Scene("Preview")
    f = sc.folder(sc.root, "U")
    xs = []
    for k, outfit in enumerate(OUTFITS):
        cols = dict(PLAIN)
        cols["Torso"] = SHIRTS[k]
        x = 12.5 - k * 5.0
        xs.append(x)
        m, parts = R6.build(sc, f, "Dummy%d" % k, R6.Body(), CF((x, 0, 0)), cols, humanoid=False, attachments=False)
        for name in outfit:
            att = AU.UNIFORMS[name][0]
            AU.place(sc, f, name, parts[AU.ATT[att][0]].p["cf"])
    scene, coll = new_scene(sc, strength=0.9)
    floor(coll, (80, 40), 0.0, (84, 88, 96))
    rs.setup_render(scene, 1920, 860, samples=samples, bloom=False)
    for name, pos, tgt in (("uniforms_front", (2.0, 6.5, -29.0), (0.0, 3.0, 0.0)),
                           ("uniforms_back", (-2.0, 6.5, 29.0), (0.0, 3.0, 0.0))):
        cam = SB.camera(scene, pos, tgt, lens=34, name=name)
        p = os.path.join(out, name + ".png")
        rs.render(scene, p)
        items = [(o[0], ", ".join(n for n in o[1:] if n != "OvenMittR").replace("OvenMittL", "OvenMitts"), (x, 0, 0))
                 for o, x in zip(OUTFITS, xs)]
        finish(scene, cam, p, items, note=None if name == "uniforms_front" else "seen from behind")


if "kit" in want:
    render_kit()
if "chars" in want:
    render_chars()
if "vehicles" in want:
    render_vehicles()
if "plushies" in want:
    render_plushies()
if "uniforms" in want:
    render_uniforms()
