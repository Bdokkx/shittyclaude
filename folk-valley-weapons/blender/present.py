"""Presentation renders for review:
  hero/<Id>.png      3/4 view of each weapon
  hand/<Id>.png      held by a blocky R6 avatar (5 studs tall) for scale
  phone_<class>.png  a whole class 60 studs from a Roblox-style camera (70 deg FOV),
                     framed like a phone screen
and composed sheets per class (swords, daggers, hammers) plus one for the Mythics:
  sheet_<group>_hero.png, sheet_<group>_hand.png, sheet_<group>_phone.png

    python blender/present.py <out_dir> [--ids=A,B] [--samples=48] [--only=hero,hand,phone,sheets]
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy  # noqa: E402,I001
import bmesh  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import defs  # noqa: E402
import rbxscene as rs  # noqa: E402
import wlib  # noqa: E402

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
OUT = os.path.abspath(args[0])
OPTS = dict(a[2:].split("=", 1) if "=" in a else (a[2:], "1") for a in args[1:] if a.startswith("--"))
IDS = OPTS["ids"].split(",") if "ids" in OPTS else list(defs.ORDER)
SAMPLES = int(OPTS.get("samples", 48))
ONLY = set(OPTS.get("only", "hero,hand,phone,sheets").split(","))
for d in ("hero", "hand"):
    os.makedirs(os.path.join(OUT, d), exist_ok=True)

RARITY_COLORS = {"Common": (170, 176, 186), "Uncommon": (92, 200, 92), "Rare": (70, 140, 255),
                 "Epic": (178, 92, 255), "Legendary": (255, 176, 40), "Limited": (255, 120, 30),
                 "Mythic": (255, 70, 120)}
GROUPS = [("swords", "Swords", lambda r, k: k == "Sword"), ("daggers", "Daggers", lambda r, k: k == "Dagger"),
          ("hammers", "Hammers", lambda r, k: k == "Hammer"), ("mythics", "Mythics", lambda r, k: r == "Mythic")]


def group_ids(test):
    return [w for w in IDS if test(*defs.WEAPONS[w][:2])]


def rb(x, y, z):
    return rs.RB2BL @ Vector((x, y, z))


# ---------------------------------------------------------------- R6 avatar

def _obj(name, bm, mat, coll, m=Matrix.Identity(4)):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.transform(rs.RB2BL @ m)
    me.shade_smooth()
    me.set_sharp_from_angle(angle=math.radians(35))
    ob = bpy.data.objects.new(name, me)
    me.materials.append(mat)
    coll.objects.link(ob)
    return ob


def r6(coll, at=(0, 0, 0), skin=(245, 205, 48), shirt=(13, 105, 172), pants=(164, 189, 71)):
    """Classic blocky R6 avatar, feet at `at`, facing -Z, right arm raised forward
    in the tool-holding pose. Returns the Roblox-space position of the tool grip."""
    ax, ay, az = at
    sk = rs.roblox_material("SmoothPlastic", skin)
    sh = rs.roblox_material("SmoothPlastic", shirt)
    pa = rs.roblox_material("SmoothPlastic", pants)
    face = rs.roblox_material("SmoothPlastic", (30, 30, 34))
    T = wlib.T
    _obj("Torso", wlib.box(2, 2, 1, 0.05, 2), sh, coll, T(ax, ay + 3, az))
    _obj("LeftArm", wlib.box(1, 2, 1, 0.05, 2), sk, coll, T(ax - 1.5, ay + 3, az))
    _obj("RightArm", wlib.box(1, 1, 2, 0.05, 2), sk, coll, T(ax + 1.5, ay + 3.5, az - 0.5))
    _obj("LeftLeg", wlib.box(1, 2, 1, 0.05, 2), pa, coll, T(ax - 0.5, ay + 1, az))
    _obj("RightLeg", wlib.box(1, 2, 1, 0.05, 2), pa, coll, T(ax + 0.5, ay + 1, az))
    head = wlib.lathe([(0, -0.6), (0.48, -0.6), (0.6, -0.48), (0.62, 0.0), (0.6, 0.48), (0.48, 0.6), (0, 0.6)],
                      segs=24)
    _obj("Head", head, sk, coll, T(ax, ay + 4.62, az))
    for ex in (-0.2, 0.2):
        _obj("Eye", wlib.sphere(0.075, 10, 6, scale=(0.8, 1.3, 0.5)), face, coll, T(ax + ex, ay + 4.74, az - 0.6))
    smile = [Vector((ax + 0.26 * math.cos(math.radians(a)), ay + 4.50 + 0.10 * math.sin(math.radians(a)), az - 0.6))
             for a in range(200, 341, 20)]
    _obj("Smile", wlib.sweep(smile, [0.05] * len(smile), [0.04] * len(smile), sides=6, point_end=False), face, coll)
    return (ax + 1.5, ay + 3.5, az - 1.5)


# ---------------------------------------------------------------- build weapons

scene = rs.reset_scene()
rs.setup_world(scene)
rs.setup_render(scene, 700, 1000, samples=SAMPLES, transparent=True)

built = {}
if ONLY & {"hero", "hand", "phone"}:
    for wid in IDS:
        rarity, kind, fn = defs.WEAPONS[wid]
        w = wlib.Weapon(wid, rarity, kind)
        fn(w)
        coll = bpy.data.collections.new(wid)
        scene.collection.children.link(coll)
        objs, info = w.build(coll)
        built[wid] = (coll, objs, info)


def only(wids):
    for other, (coll, objs, info) in built.items():
        coll.hide_render = other not in wids


def move(wid, pos_rb):
    coll, objs, info = built[wid]
    m = Matrix.Translation(rb(*pos_rb))
    for ob in objs:
        ob.matrix_world = m


cam = rs.add_camera(scene, (0, -30, 0), (0, 0, 0), ortho=8)

# ---------------------------------------------------------------- hero tiles
if "hero" in ONLY:
    yaw, pitch = math.radians(34), math.radians(12)
    for wid in IDS:
        only({wid})
        coll, objs, info = built[wid]
        lo, hi = rs.bounds(objs)
        c = (lo + hi) / 2
        cam.data.type = "ORTHO"
        cam.data.ortho_scale = 8.6
        loc = c + Vector((math.sin(yaw) * math.cos(pitch), -math.cos(yaw) * math.cos(pitch), math.sin(pitch))) * 30
        rs.look_at(cam, loc, c)
        rs.render(scene, os.path.join(OUT, "hero", wid + ".png"))

# ---------------------------------------------------------------- in-hand tiles
if "hand" in ONLY:
    av = bpy.data.collections.new("Avatar")
    scene.collection.children.link(av)
    grip = r6(av)
    scene.render.resolution_x, scene.render.resolution_y = 760, 1000
    cam.data.type = "PERSP"
    cam.data.lens = 50
    for wid in IDS:
        only({wid})
        move(wid, grip)
        rs.look_at(cam, rb(-9.5, 7.0, -17.0), rb(0.7, 4.3, -0.6))
        rs.render(scene, os.path.join(OUT, "hand", wid + ".png"))
        move(wid, (0, 0, 0))
    for ob in list(av.objects):
        bpy.data.objects.remove(ob)
    bpy.data.collections.remove(av)

# ---------------------------------------------------------------- phone distance test, one class at a time
if "phone" in ONLY:
    scene.render.film_transparent = False
    scene.render.resolution_x, scene.render.resolution_y = 2532, 1170
    ground = bpy.data.meshes.new("Ground")
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=5000)
    bm.to_mesh(ground)
    bm.free()
    gob = bpy.data.objects.new("Ground", ground)
    gm = bpy.data.materials.new("Grass")
    gm.use_nodes = True
    gb = gm.node_tree.nodes["Principled BSDF"]
    gb.inputs["Base Color"].default_value = rs.lin((92, 164, 70))
    gb.inputs["Roughness"].default_value = 1.0
    if "Specular IOR Level" in gb.inputs:
        gb.inputs["Specular IOR Level"].default_value = 0.0
    ground.materials.append(gm)
    scene.collection.objects.link(gob)
    bg = scene.world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.42, 0.66, 1.0, 1)
    bg.inputs[1].default_value = 1.0
    cam.data.type = "PERSP"
    cam.data.sensor_fit = "VERTICAL"
    cam.data.angle_y = math.radians(70)
    for key, title, test in GROUPS[:3]:
        wids = group_ids(test)
        if not wids:
            continue
        av = bpy.data.collections.new("Avatars")
        scene.collection.children.link(av)
        n = len(wids)
        spacing = 7.0
        for i, wid in enumerate(wids):
            x = -(i - (n - 1) / 2) * spacing      # +X shows on the left from this camera
            g = r6(av, at=(x, 0, 0))
            move(wid, g)
        only(set(wids))
        rs.look_at(cam, rb(0, 9, -60), rb(0, 3.0, 0))
        rs.render(scene, os.path.join(OUT, "phone_%s.png" % key))
        for wid in wids:
            move(wid, (0, 0, 0))
        for ob in list(av.objects):
            bpy.data.objects.remove(ob)
        bpy.data.collections.remove(av)

# ---------------------------------------------------------------- sheets
if "sheets" in ONLY:
    from PIL import Image, ImageDraw, ImageFont

    FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    FONT2 = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

    def gradient(w, h, top=(118, 146, 190), bottom=(70, 92, 130)):
        col = Image.new("RGB", (1, h))
        px = col.load()
        for y in range(h):
            t = y / max(h - 1, 1)
            px[0, y] = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        return col.resize((w, h))

    def label(draw, x, y, w, name, rarity, size=30):
        f = ImageFont.truetype(FONT, size)
        f2 = ImageFont.truetype(FONT2, int(size * 0.62))
        while draw.textlength(name, font=f) > w - 16 and size > 16:
            size -= 2
            f = ImageFont.truetype(FONT, size)
        tw = draw.textlength(name, font=f)
        draw.text((x + (w - tw) / 2, y), name, font=f, fill=(255, 255, 255))
        rc = RARITY_COLORS.get(rarity, (200, 200, 200))
        rw = draw.textlength(rarity.upper(), font=f2) + 24
        cy = y + 38
        draw.rounded_rectangle((x + (w - rw) / 2, cy, x + (w + rw) / 2, cy + 26), radius=10, fill=rc)
        draw.text((x + (w - rw) / 2 + 12, cy + 2), rarity.upper(), font=f2, fill=(20, 22, 30))

    def sheet(folder, wids, name, title, tile_w, tile_h, cols=6, crop=None, label_h=80):
        rows = (len(wids) + cols - 1) // cols
        head = 80
        W, H = tile_w * cols, head + rows * (tile_h + label_h)
        im = gradient(W, H)
        d = ImageDraw.Draw(im)
        d.text((24, 18), title, font=ImageFont.truetype(FONT, 42), fill=(255, 255, 255))
        for i, wid in enumerate(wids):
            r, c = divmod(i, cols)
            t = Image.open(os.path.join(OUT, folder, wid + ".png")).convert("RGBA")
            if crop:
                t = t.crop(crop)
            t = t.resize((tile_w, int(t.height * tile_w / t.width)))
            x0, y0 = c * tile_w, head + r * (tile_h + label_h)
            im.paste(t, (x0, y0 + (tile_h - t.height) // 2), t)
            label(d, x0, y0 + tile_h + 2, tile_w, defs.NAMES.get(wid, wid), defs.WEAPONS[wid][0])
        im.save(os.path.join(OUT, name))
        print("sheet", name, im.size)

    for key, title, test in GROUPS:
        wids = group_ids(test)
        if not wids:
            continue
        if os.path.exists(os.path.join(OUT, "hero", wids[0] + ".png")):
            sheet("hero", wids, "sheet_%s_hero.png" % key, "%s (%d)" % (title, len(wids)), 300, 430,
                  cols=min(len(wids), 8))
        if os.path.exists(os.path.join(OUT, "hand", wids[0] + ".png")):
            sheet("hand", wids, "sheet_%s_hand.png" % key, "%s in hand" % title, 260, 342,
                  cols=min(len(wids), 8))
        ph = os.path.join(OUT, "phone_%s.png" % key)
        if os.path.exists(ph):
            img = Image.open(ph).convert("RGB")
            W, H = img.size
            cw, ch = int(W * 0.50), int(H * 0.30)
            cx, cy = W // 2, int(H * 0.50)
            crop = img.crop((cx - cw // 2, cy - ch // 2, cx + cw // 2, cy + ch // 2))
            big = crop.resize((crop.width * 3 // 2, crop.height * 3 // 2), Image.NEAREST)
            small = img.resize((big.width, int(H * big.width / W)))
            out = Image.new("RGB", (big.width, small.height + big.height + 70), (24, 26, 34))
            out.paste(small, (0, 0))
            out.paste(big, (0, small.height + 70))
            d = ImageDraw.Draw(out)
            d.text((20, small.height + 18), "%s 60 studs away on a phone (70 deg FOV): full screen above, middle "
                   "enlarged below" % title, font=ImageFont.truetype(FONT, 28), fill=(255, 255, 255))
            out.save(os.path.join(OUT, "sheet_%s_phone.png" % key))
print("done")
