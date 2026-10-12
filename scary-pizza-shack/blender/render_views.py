"""Review renders from the code session's camera list (remake brief, section 9).

    python blender/render_views.py <outdir> [map=old|new] [light=neutral,night] [views=V1,V2,...]
                                   [w=1280] [samples=24] [sheet=1]

Every view is 16:9 with a vertical field of view of 78 (as a Roblox camera), rendered once in
a neutral light (soft daylight outside, even fill inside) and once at night (moonlight and
the lamps: Light objects on the old map, Bulb parts with Lamp* attributes on the new one).
map=old renders the batch-1 map (blender/scene_build.py), map=new the remake (blender/shack2).
sheet=1 also writes a labelled contact sheet per light.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy  # noqa: E402,I001
import numpy as np  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

import spsblend as SB  # noqa: E402
import rbxscene as rs  # noqa: E402

FOV = 78.0
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# the brief's own cameras (map coordinates: X east, Z south towards the road, floor at Y 0)
FIXED = {
    "V1": ("spawn", (-9, 4.8, -3), (0, 4.5, 9)),
    "V2": ("prep line", (-9, 5.2, 3.5), (2, 3.6, -8)),
    "V3": ("oven", (4, 5, 2.5), (15, 5.2, -3.5)),
    "V4": ("window from inside", (3, 5.2, -4.5), (1.5, 4.6, 9)),
    "V5": ("west end", (-3, 5.4, 1.5), (-16, 4.4, -1.5)),
    "V6": ("camera desk", (-5, 5, 2), (-10, 4.5, 8.5)),
    "V7": ("cut, box and plushie corner", (8, 5, 1), (14.5, 4, 8)),
    "V8": ("out through the serving window", (0, 5, 6), (0, 4, 45)),
    "V9": ("the front from across the road", (6, 5.5, 52), (0, 9, 8)),
    "V13": ("out of the back door to the generator", (-12, 5.5, -14), (-18, 4, -34)),
}
INSIDE = {"V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8"}


def views_for(sc, which):
    """The brief's fixed cameras plus the ones that depend on where things are on this map."""
    v = dict(FIXED)
    st = {m.name: m for m in sc.root.get("Stations").children}
    mk = {m.name: m for m in sc.root.get("Markers").children}
    if which == "old":
        v["V10"] = ("from the bus stop towards the shack", (38, 5.0, 21.5), (0, 6, 8))
        v["V11"] = ("on the road, looking west", (12, 4.1, 30), (-80, 3.6, 30))
        v["V12"] = ("on the road, looking east", (-12, 4.1, 41), (80, 3.6, 41))
        v["V14"] = ("from the yard gate back at the shack", (10, 5.0, -44.5), (-2, 5.0, -11))
        v["V16"] = ("high overview", (70, 75, 95), (0, 0, -8))
    else:
        import shack2.views as SV
        v.update(SV.views(sc))
    for k, name in enumerate(("Cam_Front", "Cam_Back", "Cam_Yard", "Cam_Road")):
        if name in mk:
            c = mk[name].p["cf"]
            v["V15%s" % "abcd"[k]] = ("camera marker " + name, tuple(c.p), tuple(c.p + c.look * 10.0))
    return v


def build(which):
    if which == "old":
        import scene_build
        return scene_build.build(items=False)
    import shack2.build as B
    return B.build(items=False)


# ---------------------------------------------------------------- lights

MOON = np.array((0.41, 0.24, 0.88))          # from the shack towards the moon (Roblox axes)
MOON /= np.linalg.norm(MOON)
WARM = (255, 196, 132)                       # the game's indoor lamp colour


def _lamp(coll, pos, color, energy, kind="SPOT", angle=110.0, down=(0, -1, 0), shadows=True, name="Lamp"):
    ld = bpy.data.lights.new(name, kind)
    ld.energy = energy
    ld.color = [c / 255 for c in color]
    ld.use_shadow = shadows
    if kind == "SPOT":
        ld.spot_size = math.radians(angle)
        ld.spot_blend = 0.5
        ld.shadow_soft_size = 0.25
    else:
        ld.shadow_soft_size = 0.4
    ob = bpy.data.objects.new(name, ld)
    ob.location = Vector(SB.rb2bl(pos))
    if kind == "SPOT":
        ob.rotation_euler = Vector(SB.rb2bl(np.asarray(down, float))).to_track_quat("-Z", "Y").to_euler()
    coll.objects.link(ob)
    return ob


def lamp(coll, pos, rng_, bright, color=WARM, angle=110.0, down=(0, -1, 0), shadows=True):
    """As the game lights a lamp now: a spot pointing down plus a faint fill."""
    _lamp(coll, pos, color, bright * rng_ ** 2 * 2.2, "SPOT", angle, down, shadows)
    _lamp(coll, pos, color, bright * rng_ ** 2 * 0.12, "POINT", shadows=False, name="Fill")


def old_lamps(sc, coll):
    """Batch-1 map: its Light objects, re-lit the way the game lights lamps now."""
    for n in sc.nodes("Light"):
        p = n.p
        if not p["enabled"]:
            continue
        pos = n.parent.p["cf"].p
        name = n.parent.name
        if name == "Glow":                        # oven fire: a warm point inside the deck
            _lamp(coll, pos, (255, 140, 60), p["brightness"] * p["range"] ** 2 * 1.2, "POINT", shadows=False)
        elif p["cls"] == "SurfaceLight":          # fridge / cooler strips: cold, small
            _lamp(coll, pos, p["color"], p["brightness"] * p["range"] ** 2 * 0.8, "POINT", shadows=False)
        else:
            lamp(coll, pos, p["range"], p["brightness"] * 0.8, WARM if n.parent.top() != "Outside" else p["color"])


def lamp_lights(sc, coll):
    """The new map's lamps: every Bulb part whose Model (or itself) carries Lamp* attributes."""
    for n in sc.nodes(("Part", "MeshPart")):
        if n.name != "Bulb":
            continue
        a = dict(n.parent.p.get("attrs") or {})
        a.update(n.p.get("attrs") or {})
        if "LampKind" not in a and "LampRange" not in a:
            continue
        col = tuple(int(c) for c in str(a.get("LampColor", "%d,%d,%d" % WARM)).split(","))
        rng_ = float(a.get("LampRange", 16))
        br = float(a.get("LampBrightness", 1.0))
        kind = a.get("LampKind", "Spot")
        down = -n.p["cf"].R[:, 1]
        if kind == "Point":
            _lamp(coll, n.p["cf"].p, col, br * rng_ ** 2 * 1.4, "POINT", shadows=bool(a.get("LampShadows", True)))
        else:
            lamp(coll, n.p["cf"].p, rng_, br, col, float(a.get("LampAngle", 110)), down,
                 bool(a.get("LampShadows", True)))
    for n in sc.nodes(("Part", "MeshPart")):       # fire in the oven decks
        if n.name.startswith("Glow") and n.p.get("material") == "Neon":
            _lamp(coll, n.p["cf"].p, (255, 140, 60), 260, "POINT", shadows=False, name="Fire")


def night_sky(scene, ambient=0.05, moon_energy=2.0):
    """Black-to-deep-blue sky with haze on the horizon, stars and the low moon to the SSE;
    the sky lights the scene only faintly (little ambient)."""
    world = bpy.data.worlds.new("NightSky")
    scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    nodes, links = nt.nodes, nt.links
    nodes.clear()
    out = nodes.new("ShaderNodeOutputWorld")
    tc = nodes.new("ShaderNodeTexCoord")
    sep = nodes.new("ShaderNodeSeparateXYZ")
    links.new(tc.outputs["Generated"], sep.inputs[0])
    ramp = nodes.new("ShaderNodeValToRGB")
    cr = ramp.color_ramp
    cr.elements[0].position, cr.elements[0].color = 0.0, (0.055, 0.07, 0.11, 1)      # haze at the horizon
    cr.elements[1].position, cr.elements[1].color = 0.35, (0.004, 0.006, 0.016, 1)   # near black up high
    e = cr.elements.new(0.08)
    e.color = (0.016, 0.03, 0.075, 1)                                                 # deep blue
    links.new(sep.outputs["Z"], ramp.inputs["Factor"])
    # stars
    vor = nodes.new("ShaderNodeTexVoronoi")
    vor.inputs["Scale"].default_value = 180.0
    links.new(tc.outputs["Generated"], vor.inputs["Vector"])
    st = nodes.new("ShaderNodeMapRange")
    st.inputs["From Min"].default_value = 0.035
    st.inputs["From Max"].default_value = 0.0
    links.new(vor.outputs["Distance"], st.inputs["Value"])
    pick = nodes.new("ShaderNodeSeparateColor")
    links.new(vor.outputs["Color"], pick.inputs["Color"])
    gate = nodes.new("ShaderNodeMath")
    gate.operation = "GREATER_THAN"
    gate.inputs[1].default_value = 0.8
    links.new(pick.outputs[0], gate.inputs[0])
    up = nodes.new("ShaderNodeMath")
    up.operation = "GREATER_THAN"
    up.inputs[1].default_value = 0.12
    links.new(sep.outputs["Z"], up.inputs[0])
    s1 = nodes.new("ShaderNodeMath")
    s1.operation = "MULTIPLY"
    links.new(st.outputs["Result"], s1.inputs[0])
    links.new(gate.outputs[0], s1.inputs[1])
    s2 = nodes.new("ShaderNodeMath")
    s2.operation = "MULTIPLY"
    links.new(s1.outputs[0], s2.inputs[0])
    links.new(up.outputs[0], s2.inputs[1])
    s3 = nodes.new("ShaderNodeMath")
    s3.operation = "MULTIPLY"
    s3.inputs[1].default_value = 0.9
    links.new(s2.outputs[0], s3.inputs[0])
    # moon disc and a soft halo round it
    md = Vector(SB.rb2bl(MOON))
    dot = nodes.new("ShaderNodeVectorMath")
    dot.operation = "DOT_PRODUCT"
    dot.inputs[1].default_value = md
    links.new(tc.outputs["Generated"], dot.inputs[0])
    disc = nodes.new("ShaderNodeMapRange")
    disc.inputs["From Min"].default_value = math.cos(math.radians(1.6))
    disc.inputs["From Max"].default_value = math.cos(math.radians(1.3))
    disc.inputs["To Max"].default_value = 30.0
    links.new(dot.outputs["Value"], disc.inputs["Value"])
    halo = nodes.new("ShaderNodeMath")
    halo.operation = "POWER"
    halo.inputs[1].default_value = 600.0
    clampd = nodes.new("ShaderNodeMath")
    clampd.operation = "MAXIMUM"
    clampd.inputs[1].default_value = 0.0
    links.new(dot.outputs["Value"], clampd.inputs[0])
    links.new(clampd.outputs[0], halo.inputs[0])
    halo2 = nodes.new("ShaderNodeMath")
    halo2.operation = "MULTIPLY"
    halo2.inputs[1].default_value = 0.35
    links.new(halo.outputs[0], halo2.inputs[0])
    add1 = nodes.new("ShaderNodeMath")
    add1.operation = "ADD"
    links.new(disc.outputs["Result"], add1.inputs[0])
    links.new(halo2.outputs[0], add1.inputs[1])
    add2 = nodes.new("ShaderNodeMath")
    add2.operation = "ADD"
    links.new(add1.outputs[0], add2.inputs[0])
    links.new(s3.outputs[0], add2.inputs[1])
    moonc = nodes.new("ShaderNodeMix")
    moonc.data_type = "RGBA"
    moonc.blend_type = "ADD"
    moonc.inputs["Factor"].default_value = 1.0
    links.new(ramp.outputs["Color"], moonc.inputs["A"])
    tint = nodes.new("ShaderNodeMix")
    tint.data_type = "RGBA"
    tint.blend_type = "MULTIPLY"
    tint.inputs["Factor"].default_value = 1.0
    tint.inputs["B"].default_value = (0.85, 0.9, 1.0, 1)
    links.new(add2.outputs[0], tint.inputs["A"])
    links.new(tint.outputs["Result"], moonc.inputs["B"])
    bg_cam = nodes.new("ShaderNodeBackground")
    bg_cam.inputs["Strength"].default_value = 1.0
    links.new(moonc.outputs["Result"], bg_cam.inputs["Color"])
    bg_amb = nodes.new("ShaderNodeBackground")
    bg_amb.inputs["Color"].default_value = (0.03, 0.045, 0.09, 1)
    bg_amb.inputs["Strength"].default_value = ambient
    lp = nodes.new("ShaderNodeLightPath")
    mix = nodes.new("ShaderNodeMixShader")
    links.new(lp.outputs["Is Camera Ray"], mix.inputs[0])
    links.new(bg_amb.outputs[0], mix.inputs[1])
    links.new(bg_cam.outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], out.inputs["Surface"])
    world.mist_settings.start = 40.0
    world.mist_settings.depth = 260.0
    world.mist_settings.falloff = "QUADRATIC"
    # the moon itself
    d = bpy.data.lights.new("Moon", "SUN")
    d.energy = moon_energy
    d.angle = math.radians(1.0)
    d.color = (0.62, 0.72, 1.0)
    o = bpy.data.objects.new("Moon", d)
    o.rotation_euler = (-md).to_track_quat("-Z", "Y").to_euler()
    scene.collection.objects.link(o)
    return world


def neutral(scene, coll, inside):
    SB.day_world(scene, strength=1.0)
    if inside:
        # even fill under the ceiling, like Roblox's ambient light reaching everywhere
        for x in (-12, -4, 4, 12):
            for z in (-5, 4):
                ld = bpy.data.lights.new("Fill", "AREA")
                ld.energy = 900
                ld.size = 7.0
                ld.color = (1.0, 0.97, 0.92)
                ob = bpy.data.objects.new("Fill", ld)
                ob.location = Vector(SB.rb2bl((x, 8.6, z)))
                coll.objects.link(ob)


def night(scene, coll, sc, which, inside):
    night_sky(scene, ambient=0.04 if inside else 0.06)
    if which == "old":
        old_lamps(sc, coll)
    else:
        lamp_lights(sc, coll)


def compositor(scene, fog):
    """Bloom on the lamps and, outside at night, a blue-grey haze that thickens with distance."""
    scene.render.compositor_device = "CPU"
    tree = bpy.data.node_groups.new("Comp", "CompositorNodeTree")
    scene.compositing_node_group = tree
    rl = tree.nodes.new("CompositorNodeRLayers")
    out = tree.nodes.new("NodeGroupOutput")
    tree.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    img = rl.outputs["Image"]
    if fog:
        bpy.context.view_layer.use_pass_mist = True
        k = tree.nodes.new("ShaderNodeMath")
        k.operation = "MULTIPLY"
        k.inputs[1].default_value = 0.85
        tree.links.new(rl.outputs["Mist"], k.inputs[0])
        mix = tree.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.inputs["B"].default_value = (0.03, 0.045, 0.08, 1)
        tree.links.new(k.outputs[0], mix.inputs["Factor"])
        tree.links.new(img, mix.inputs["A"])
        img = mix.outputs["Result"]
    glare = tree.nodes.new("CompositorNodeGlare")
    try:
        glare.inputs["Type"].default_value = "Bloom"
    except Exception:
        pass
    for nm, v in (("Threshold", 0.9), ("Strength", 0.6), ("Size", 0.6)):
        if nm in glare.inputs:
            try:
                glare.inputs[nm].default_value = v
            except Exception:
                pass
    tree.links.new(img, glare.inputs["Image"])
    tree.links.new(glare.outputs["Image"], out.inputs[0])


# ---------------------------------------------------------------- camera / sheet

SIGN_FONT = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
RB2BL = np.array(((1.0, 0.0, 0.0), (0.0, 0.0, -1.0), (0.0, 1.0, 0.0)))
# what the game writes on the rules board (its own SurfaceGui), shown here as chalk lines
PREVIEW_TEXT = {("RulesBoard", "Face"): ("STAFF RULES\n1. ______________\n2. ______________\n3. ______________\n"
                                         "4. ______________", "235,235,225")}


def board_texts(sc, coll):
    """Preview only: each Board's BoardText laid on its Front face (-Z), centred, fitted to
    the face with a margin, in BoardTextColor (the game does this with a SurfaceGui)."""
    font = bpy.data.fonts.load(SIGN_FONT) if os.path.exists(SIGN_FONT) else None
    n_txt = 0
    for n in sc.nodes(("Part", "MeshPart")):
        a = n.p.get("attrs") or {}
        txt, tcol = a.get("BoardText"), a.get("BoardTextColor", "30,30,30")
        par = n.parent.name if getattr(n, "parent", None) is not None else ""
        if not txt and (par, n.name) in PREVIEW_TEXT:
            txt, tcol = PREVIEW_TEXT[(par, n.name)]
        if not txt:
            continue
        sx, sy, sz = n.p["size"]
        cu = bpy.data.curves.new("BoardText", "FONT")
        cu.body = txt
        if font is not None:
            cu.font = font
        cu.align_x, cu.align_y = "CENTER", "CENTER"
        cu.size = 1.0
        ob = bpy.data.objects.new("BoardText", cu)
        coll.objects.link(ob)
        bpy.context.view_layer.update()
        w, h = max(ob.dimensions.x, 1e-3), max(ob.dimensions.y, 1e-3)
        cu.size = min(0.84 * sx / w, 0.66 * sy / h)
        R = n.p["cf"].R @ np.diag((-1.0, 1.0, -1.0))         # reads along -X, faces -Z
        pos = n.p["cf"].p + n.p["cf"].R @ np.array((0.0, 0.0, -sz / 2 - 0.012))
        M = np.eye(4)
        M[:3, :3] = RB2BL @ R
        M[:3, 3] = RB2BL @ pos
        ob.matrix_world = Matrix(M.tolist())
        col = tuple(int(v) for v in str(tcol).split(","))
        cu.materials.append(SB.material(col, "SmoothPlastic", 0.0))
        n_txt += 1
    return n_txt


def camera(scene, pos, tgt, name):
    cam = SB.camera(scene, pos, tgt, lens=30, name=name)
    cam.data.sensor_fit = "VERTICAL"
    cam.data.sensor_height = 24.0
    cam.data.lens = 12.0 / math.tan(math.radians(FOV / 2))
    cam.data.clip_start = 0.1
    cam.data.clip_end = 3000
    scene.camera = cam
    return cam


def sheet(paths, labels, out, title, cols=4, tw=480):
    th = tw * 9 // 16
    rows = (len(paths) + cols - 1) // cols
    img = Image.new("RGB", (cols * tw, 56 + rows * (th + 26)), (22, 24, 28))
    d = ImageDraw.Draw(img)
    f1, f2 = ImageFont.truetype(FONT, 24), ImageFont.truetype(FONT, 15)
    d.text((14, 14), title, fill=(240, 228, 196), font=f1)
    for k, (p, lab) in enumerate(zip(paths, labels)):
        x, y = (k % cols) * tw, 56 + (k // cols) * (th + 26)
        img.paste(Image.open(p).convert("RGB").resize((tw, th)), (x, y))
        d.text((x + 6, y + th + 4), lab, fill=(220, 220, 210), font=f2)
    img.save(out, quality=88)
    print("sheet", out)


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    opts = dict(a.split("=", 1) for a in sys.argv[2:] if "=" in a)
    which = opts.get("map", "new")
    lights = opts.get("light", "neutral,night").split(",")
    w = int(opts.get("w", 1280))
    h = w * 9 // 16
    samples = int(opts.get("samples", 24))
    sc = build(which)
    views = views_for(sc, which)
    # extra cameras for close looks: cams=name:x,y,z:tx,ty,tz;... (inside=1 lights them as inside)
    if "cams" in opts:
        for spec in opts["cams"].split(";"):
            nm, a, b = spec.split(":")
            views[nm] = ("close look " + nm, tuple(float(v) for v in a.split(",")),
                         tuple(float(v) for v in b.split(",")))
            if opts.get("inside", "1") == "1":
                INSIDE.add(nm)
    want = opts["views"].split(",") if "views" in opts else list(views)
    order = sorted(want, key=lambda k: (int("".join(ch for ch in k[1:] if ch.isdigit()) or 0), k))
    for light in lights:
        done, labels = [], []
        for inside in (True, False):
            todo = [k for k in order if (k in INSIDE) == inside and k in views]
            if not todo:
                continue
            scene = SB.reset()
            coll = bpy.data.collections.new("Map")
            scene.collection.children.link(coll)
            SB.realize(sc, coll)
            if which == "new":
                board_texts(sc, coll)
            if light == "neutral":
                neutral(scene, coll, inside)
            else:
                night(scene, coll, sc, which, inside)
            rs.setup_render(scene, w, h, samples=samples, bloom=False,
                            exposure=0.0 if light == "neutral" else (0.3 if inside else 0.9))
            if light == "night":
                compositor(scene, fog=not inside)
            for k in todo:
                name, pos, tgt = views[k]
                camera(scene, pos, tgt, k)
                p = os.path.join(out, "%s_%s_%s.png" % (which, k, light))
                rs.render(scene, p)
                jpg = p[:-4] + ".jpg"
                Image.open(p).convert("RGB").save(jpg, quality=90)
                os.remove(p)
                done.append(jpg)
                labels.append("%s %s" % (k, name))
                print("saved", jpg, flush=True)
        if opts.get("sheet") and done:
            sheet(done, labels, os.path.join(out, "%s_sheet_%s.jpg" % (which, light)),
                  "%s map, %s light" % ("batch-1" if which == "old" else "remake", light))


if __name__ == "__main__":
    main()
