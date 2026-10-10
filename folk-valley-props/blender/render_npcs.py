"""Render the NPCs dressed in the NEW props and body pieces, posed like the
original file (the outfit pieces at their old handles, the body pieces welded
to their limbs, the hidden limbs left out). --old renders the original NPCs
the same way, for a before / after.

    python blender/render_npcs.py <npc.json> <props.json> <out_dir> [--samples=48] [--size=900] [--old]
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plib  # noqa: E402,I001
import propscene as ps  # noqa: E402
import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import pdefs  # noqa: E402

rs = plib.rs
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
NPC_JSON, PROPS_JSON, OUT = args[0], args[1], args[2]
OPTS = dict(a[2:].split("=", 1) if "=" in a else (a[2:], "1") for a in args[3:] if a.startswith("--"))
OLD = "old" in OPTS
SAMPLES = int(OPTS.get("samples", 48))
SIZE = int(OPTS.get("size", 900))
os.makedirs(OUT, exist_ok=True)

COLOR_OVERRIDES = {("Wanda", "NpcScarf", "Scarf"): (82, 194, 52)}
ROT180 = Matrix.Rotation(math.pi, 4, "Y")

npcs = plib.load_original(NPC_JSON)
orig_props = plib.load_original(PROPS_JSON)

scene = rs.reset_scene()
rs.setup_world(scene)
rs.setup_render(scene, SIZE, int(SIZE * 1.25), samples=SAMPLES, transparent=True)
library = bpy.data.collections.new("library")
scene.collection.children.link(library)
library.hide_render = True
built = {}


def get(pid):
    if pid not in built:
        fn, kind = pdefs.PROPS[pid]
        src = pdefs.SOURCE.get(pid, pid)
        o = plib.Original(orig_props[src]) if src in orig_props else None
        p = plib.Prop(pid, o, kind)
        fn(p, o)
        objs, info = p.build(library)
        built[pid] = (objs, info)
    return built[pid]


def place(pid, handle_world_rb, coll, origin, npc_name):
    """Copies of a prop's objects with its Handle at handle_world_rb (Roblox 4x4)."""
    objs, info = get(pid)
    m = rs.RB2BL @ Matrix.Translation(-origin) @ handle_world_rb @ rs.RB2BL.inverted()
    out = []
    for ob, part in zip(objs, info["Parts"]):
        c = ob.copy()
        c.matrix_world = m
        key = (npc_name, pid, part["Name"])
        if key in COLOR_OVERRIDES:
            c.data = ob.data.copy()
            c.data.materials.clear()
            c.data.materials.append(rs.roblox_material(part["Material"], COLOR_OVERRIDES[key], part["Transparency"]))
        coll.objects.link(c)
        out.append(c)
    return out


for name, npc in npcs.items():
    coll = bpy.data.collections.new(name)
    scene.collection.children.link(coll)
    hrp = next(c for c in npc["children"] if c["name"] == "HumanoidRootPart")
    origin = Vector(hrp["props"]["CFrame"]["CFrame"]["position"])
    limbs = {c["name"]: plib._m4(c["props"]["CFrame"]) for c in npc["children"] if c["class"] == "Part"}
    objs = []
    hidden = set(pdefs.HIDE.get(name, []))
    for o, node in ps.build_npc(npc, coll):
        # build_npc draws the old body and outfit; for the new look keep only the visible head (+ face)
        keep = OLD or (node["class"] == "Part" and node["name"] == "Head" and node["name"] not in hidden)
        if keep:
            objs.append(o)
        else:
            bpy.data.objects.remove(o)
    if not OLD:
        outfit = next(c for c in npc["children"] if c["name"] == "Outfit")
        for m in outfit["children"]:
            h = next(c for c in m["children"] if c["name"] == "Handle")
            objs += place(m["name"], plib._m4(h["props"]["CFrame"]), coll, origin, name)
        for pid, limb in pdefs.BODY.get(name, []):
            objs += place(pid, limbs[limb] @ ROT180, coll, origin, name)
    # camera: three-quarter front and back, framing the character (not the cauldron)
    body_objs = [o for o in objs if "Cauldron" not in o.name]
    lo, hi = rs.bounds(body_objs)
    c = (lo + hi) / 2
    r = hrp["props"]["CFrame"]["CFrame"]["orientation"]
    front = Vector((-r[0][2], r[2][2], -r[1][2]))            # Roblox -Z column -> Blender
    front = Vector((front.x, front.y, 0)).normalized()
    for other in bpy.data.collections:
        if other.name in npcs:
            other.hide_render = other.name != name
    span = max(hi.z - lo.z, (hi.x - lo.x), (hi.y - lo.y)) * 1.15
    cam = scene.camera or rs.add_camera(scene, (0, -30, 0), c, ortho=span)
    cam.data.ortho_scale = span
    for tag, yaw in (("front", 30), ("back", 210)):
        d = front.copy()
        d.rotate(Matrix.Rotation(math.radians(yaw), 3, "Z"))
        loc = c + d * 40 * math.cos(math.radians(10)) + Vector((0, 0, 40 * math.sin(math.radians(10))))
        rs.look_at(cam, loc, c)
        rs.render(scene, os.path.join(OUT, "%s_%s.png" % (name, tag)))
    # wide shot with the cauldron for Wanda
    if any("Cauldron" in o.name for o in objs):
        lo2, hi2 = rs.bounds(objs)
        c2 = (lo2 + hi2) / 2
        cam.data.ortho_scale = max(hi2.z - lo2.z, (hi2.xy - lo2.xy).length) * 1.1
        d = front.copy()
        d.rotate(Matrix.Rotation(math.radians(20), 3, "Z"))
        rs.look_at(cam, c2 + d * 40 * math.cos(math.radians(12)) + Vector((0, 0, 40 * math.sin(math.radians(12)))), c2)
        rs.render(scene, os.path.join(OUT, "%s_scene.png" % name))
    print("rendered", name)
