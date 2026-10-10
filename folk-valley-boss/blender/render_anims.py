"""Pose the Reaper with its animations and render them in Cycles. The poses are read
back from the written KeyframeSequences, so this shows exactly what Roblox plays.

    python blender/render_anims.py <rig.json> <anims.json> <out_dir> [options]

    --stills             a few moments of every clip, as one contact sheet per clip
    --times=Clip:0.5,0.9;Clip2:1.2    these moments instead of the defaults
    --frames             every frame (30 fps) of the clips, for the preview video
    --clips=A,B          only these clips
    --size=WxH  --samples=N
    --dummy[=x,z,yaw]    a 5-stud player beside the boss, for scale
    --turntable=N        N frames of the camera circling the idle pose (out_dir/frames/Turntable)
    --hero               one still of the idle pose with a 5-stud player beside it (out_dir/hero.png)
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "tools"))
import reaper  # noqa: E402,I001
import plib  # noqa: E402
import banim as B  # noqa: E402
import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

rs = plib.rs
A = B.A
RB = np.array([list(r) for r in rs.RB2BL])
RBi = np.linalg.inv(RB)
FPS = 30
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
BG_TOP, BG_BOT = (64, 52, 104), (22, 18, 40)

# per clip camera: (yaw, pitch) in degrees, yaw 180 = straight in front, 270 = the reaper's left
VIEWS = {"ReaperThrow": (232, 9), "ReaperSpin": (205, 11), "ReaperDefeat": (215, 10)}
DEFAULT_VIEW = (208, 8)


# ---------------------------------------------------------------- reading the sequences

def read_clips(path):
    folder = json.load(open(path))[0]
    out = {}
    for ks in folder["children"]:
        kfs = sorted((k for k in ks["children"] if k["class"] == "Keyframe"), key=lambda k: k["props"]["Time"]["Float32"])
        times, frames, markers = [], [], []
        for kf in kfs:
            t = kf["props"]["Time"]["Float32"]
            X = {}
            stack = [c for c in kf["children"] if c["class"] == "Pose"]
            while stack:
                p = stack.pop()
                if p["props"]["Weight"]["Float32"] > 0:
                    cf = p["props"]["CFrame"]["CFrame"]
                    m = np.eye(4)
                    m[:3, :3] = np.array(cf["orientation"], dtype=float)
                    m[:3, 3] = cf["position"]
                    X[p["name"]] = m
                stack.extend(c for c in p["children"] if c["class"] == "Pose")
            markers += [(t, c["name"]) for c in kf["children"] if c["class"] == "KeyframeMarker"]
            times.append(t)
            frames.append(X)
        out[ks["name"]] = {"name": ks["name"], "times": np.array(times), "frames": frames, "markers": markers,
                           "loop": ks["props"]["Loop"]["Bool"], "length": times[-1]}
    return out


def pose_at(clip, t):
    """Linear keys, like Roblox plays them."""
    ts = clip["times"]
    t = min(max(t, 0.0), clip["length"])
    k = max(0, min(int(np.searchsorted(ts, t, side="right") - 1), len(ts) - 2))
    h = ts[k + 1] - ts[k]
    u = 0.0 if h < 1e-9 else min(max((t - ts[k]) / h, 0.0), 1.0)
    a, b = clip["frames"][k], clip["frames"][k + 1]
    X = {}
    for name in set(a) | set(b):
        ma, mb = a.get(name, np.eye(4)), b.get(name, np.eye(4))
        m = np.eye(4)
        m[:3, :3] = A.quat_to_mat(A.slerp(A.mat_to_quat(ma[:3, :3]), A.mat_to_quat(mb[:3, :3]), u))
        m[:3, 3] = ma[:3, 3] * (1 - u) + mb[:3, 3] * u
        X[name] = m
    return X


# ---------------------------------------------------------------- the posed model

class Poser:
    def __init__(self, rig, objs, parts):
        self.rig = rig
        self.rest = rig.fk({})
        self.items = [(o, p["Model"]) for o, p in zip(objs, parts)]
        self.parts = parts

    def deltas(self, X):
        W = self.rig.fk(X)
        return {b: W[b] @ np.linalg.inv(self.rest[b]) for b in W}

    def apply(self, X):
        D = self.deltas(X)
        for o, b in self.items:
            o.matrix_world = Matrix((RB @ D[b] @ RBi).tolist())
        return D

    def corners(self, D):
        pts = []
        for p in self.parts:
            c, s = np.array(p["Center"]), np.array(p["Size"]) / 2
            for sx in (-1, 1):
                for sy in (-1, 1):
                    for sz in (-1, 1):
                        pts.append((D[p["Model"]] @ np.array([*(c + s * (sx, sy, sz)), 1.0]))[:3])
        return np.array(pts)


# ---------------------------------------------------------------- scene

def ground(scene, radius=70.0, fade=(26.0, 44.0)):
    bm = bmesh.new()
    bmesh.ops.create_circle(bm, cap_ends=True, radius=radius, segments=96)
    me = bpy.data.meshes.new("Ground")
    bm.to_mesh(me)
    ob = bpy.data.objects.new("Ground", me)
    scene.collection.objects.link(ob)
    mat = bpy.data.materials.new("GroundMat")
    mat.use_nodes = True
    nt = mat.node_tree
    nodes, links = nt.nodes, nt.links
    bsdf = nodes["Principled BSDF"]
    out = nodes["Material Output"]
    tc = nodes.new("ShaderNodeTexCoord")
    chk = nodes.new("ShaderNodeTexChecker")
    chk.inputs["Scale"].default_value = 0.25                      # 4-stud squares
    chk.inputs["Color1"].default_value = rs.lin((58, 66, 52))
    chk.inputs["Color2"].default_value = rs.lin((48, 56, 44))
    links.new(tc.outputs["Object"], chk.inputs["Vector"])
    links.new(chk.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.95
    # fade the disc out towards its edge so it sits on the backdrop like a stage
    sep = nodes.new("ShaderNodeVectorMath")
    sep.operation = "LENGTH"
    links.new(tc.outputs["Object"], sep.inputs[0])
    mr = nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = fade[0]
    mr.inputs["From Max"].default_value = fade[1]
    mr.inputs["To Min"].default_value = 1.0
    mr.inputs["To Max"].default_value = 0.0
    links.new(sep.outputs["Value"], mr.inputs["Value"])
    tr = nodes.new("ShaderNodeBsdfTransparent")
    mix = nodes.new("ShaderNodeMixShader")
    links.new(mr.outputs["Result"], mix.inputs["Fac"])
    links.new(tr.outputs[0], mix.inputs[1])
    links.new(bsdf.outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], out.inputs["Surface"])
    me.materials.append(mat)
    return ob


def dummy(scene, x, z, yaw=0.0):
    """A plain 5-stud blocky player (R15 proportions) for scale, facing `yaw`."""
    coll = bpy.data.collections.new("Dummy")
    scene.collection.children.link(coll)
    skin = rs.roblox_material("SmoothPlastic", (234, 184, 146))
    shirt = rs.roblox_material("SmoothPlastic", (52, 142, 64))
    pants = rs.roblox_material("SmoothPlastic", (40, 72, 160))
    boxes = [((0, 4.45, 0), (1.2, 1.2, 1.2), skin), ((0, 3.0, 0), (2, 1.75, 1), shirt), ((0, 2.1, 0), (2, 0.4, 1), pants),
             ((1.5, 2.95, 0), (1, 1.9, 1), skin), ((-1.5, 2.95, 0), (1, 1.9, 1), skin),
             ((0.5, 0.95, 0), (1, 1.9, 1), pants), ((-0.5, 0.95, 0), (1, 1.9, 1), pants)]
    rot = Matrix.Rotation(math.radians(yaw), 4, "Y")
    for i, (c, s, mat) in enumerate(boxes):
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=0.08, segments=2, affect="EDGES")
        bmesh.ops.scale(bm, vec=Vector(s), verts=bm.verts)
        me = bpy.data.meshes.new("Dummy%d" % i)
        bm.to_mesh(me)
        me.transform(rs.RB2BL @ Matrix.Translation(Vector((x, 0, z))) @ rot @ Matrix.Translation(Vector(c)))
        me.shade_smooth()
        me.materials.append(mat)
        ob = bpy.data.objects.new(me.name, me)
        coll.objects.link(ob)
    # a little face so it reads as a player
    face = rs.roblox_material("SmoothPlastic", (30, 24, 20))
    for ex in (-0.22, 0.22):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=0.09)
        me = bpy.data.meshes.new("DummyEye")
        bm.to_mesh(me)
        me.transform(rs.RB2BL @ Matrix.Translation(Vector((x, 0, z))) @ rot @ Matrix.Translation(Vector((ex, 4.55, -0.6))))
        me.materials.append(face)
        coll.objects.link(bpy.data.objects.new("DummyEye", me))


def fit_camera(cam, pts_rb, yaw, pitch, aspect, margin=1.1):
    """Perspective camera from (yaw, pitch) that just fits the points (Roblox space)."""
    P = (RB[:3, :3] @ np.asarray(pts_rb).T).T
    d = np.array([math.sin(math.radians(yaw)) * math.cos(math.radians(pitch)),
                  -math.cos(math.radians(yaw)) * math.cos(math.radians(pitch)), math.sin(math.radians(pitch))])
    fwd = -d
    right = np.cross(fwd, (0, 0, 1.0))
    right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    th = 18.0 / cam.data.lens / margin
    tv = th / aspect
    c = (P.min(0) + P.max(0)) / 2
    for _ in range(4):
        rel = P - c
        x, y, z0 = rel @ right, rel @ up, rel @ fwd
        D = float(np.max(np.maximum(np.abs(x) / th, np.abs(y) / tv) - z0))
        z = z0 + D
        # recentre on what the camera actually sees
        sx, sy = x / z, y / z
        c = c + right * (sx.max() + sx.min()) / 2 * D + up * (sy.max() + sy.min()) / 2 * D
    cam.data.sensor_fit = "HORIZONTAL"
    rs.look_at(cam, Vector((c + d * D).tolist()), Vector(c.tolist()))
    return D


def backdrop(w, h):
    col = Image.new("RGB", (1, h))
    px = col.load()
    for y in range(h):
        k = y / max(h - 1, 1)
        px[0, y] = tuple(int(a + (b - a) * k) for a, b in zip(BG_TOP, BG_BOT))
    return col.resize((w, h))


def composite(png, out=None):
    im = Image.open(png).convert("RGBA")
    bg = backdrop(*im.size).convert("RGBA")
    bg.alpha_composite(im)
    bg = bg.convert("RGB")
    bg.save(out or png)
    return bg


# ---------------------------------------------------------------- main

def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    rig_path, anims_path, out_dir = args[:3]
    opts = dict(a[2:].split("=", 1) if "=" in a else (a[2:], "1") for a in args[3:] if a.startswith("--"))
    w, h = (int(v) for v in opts.get("size", "560x620").split("x"))
    samples = int(opts.get("samples", 12))
    os.makedirs(out_dir, exist_ok=True)

    rig = B.Rig(rig_path)
    clips = read_clips(anims_path)
    names = opts["clips"].split(",") if "clips" in opts else list(clips)

    scene = rs.reset_scene()
    rs.setup_world(scene)
    rs.setup_render(scene, w, h, samples=samples, transparent=True)
    scene.render.use_persistent_data = True
    p = plib.Prop("Reaper", None, "Boss")
    reaper.build(p)
    coll = bpy.data.collections.new("Reaper")
    scene.collection.children.link(coll)
    objs, info = p.build(coll)
    poser = Poser(rig, objs, info["Parts"])
    ground(scene)
    dummy_at = None
    if "dummy" in opts:
        v = opts["dummy"].split(",") if opts["dummy"] != "1" else ["-7.5", "-1", "34"]
        dummy_at = [float(x) for x in v]
        dummy(scene, dummy_at[0], dummy_at[1], yaw=dummy_at[2])
    cam = rs.add_camera(scene, (0, -60, 10), (0, 0, 10), lens=45)

    if "turntable" in opts or "hero" in opts:
        clip = clips["ReaperIdle"]
        X = pose_at(clip, 0.0)
        D = poser.apply(X)
        pts = poser.corners(D)
        if "hero" in opts:
            # the boss and the player both in frame
            if dummy_at:
                x, z = dummy_at[:2]
                pts = np.vstack([pts, [[x - 1.6, 0, z - 1], [x + 1.6, 5.2, z + 1]]])
            fit_camera(cam, pts, 214, 7, w / h, margin=1.08)
            rs.render(scene, os.path.join(out_dir, "hero.png"))
            print("hero", flush=True)
        if "turntable" in opts:
            n = int(opts["turntable"])
            d = os.path.join(out_dir, "frames", "Turntable")
            os.makedirs(d, exist_ok=True)
            for i in range(n):
                path = os.path.join(d, "%04d.png" % i)
                if os.path.exists(path):
                    continue
                yaw = 180 + 360.0 * i / n
                fit_camera(cam, poser.corners(D), yaw, 7, w / h, margin=1.12)
                rs.render(scene, path)
            print("turntable", n, flush=True)
        return

    times_opt = {}
    if "times" in opts:
        for part in opts["times"].split(";"):
            n, ts = part.split(":")
            times_opt[n] = [float(v) for v in ts.split(",")]

    for name in names:
        clip = clips[name]
        L = clip["length"]
        # frame the whole clip once, so the camera holds still
        pts = []
        for t in np.linspace(0, L, max(2, int(L * 10))):
            pts.append(poser.corners(poser.deltas(pose_at(clip, t))))
        pts = np.vstack(pts + [poser.corners(poser.deltas({}))])
        yaw, pitch = VIEWS.get(name, DEFAULT_VIEW)
        if "view" in opts:
            yaw, pitch = (float(v) for v in opts["view"].split(","))
        fit_camera(cam, pts, yaw, pitch, w / h, margin=1.14)

        if "frames" in opts:
            d = os.path.join(out_dir, "frames", name)
            os.makedirs(d, exist_ok=True)
            n = int(round(L * FPS)) + (0 if clip["loop"] else 1)
            for i in range(n):
                path = os.path.join(d, "%04d.png" % i)
                if os.path.exists(path):
                    continue
                poser.apply(pose_at(clip, i / FPS))
                rs.render(scene, path)
            print("frames", name, n, flush=True)
        else:
            ts = times_opt.get(name)
            if ts is None:
                ts = sorted(set([round(v, 2) for v in np.linspace(0, L, 7)[:-1 if clip["loop"] else None]] +
                                [round(t, 2) for t, _ in clip["markers"]]))
            tiles = []
            for t in ts:
                poser.apply(pose_at(clip, t))
                path = os.path.join(out_dir, "%s_%05.2f.png" % (name, t))
                rs.render(scene, path)
                tiles.append((t, composite(path)))
            cols = min(len(tiles), 4)
            rows = (len(tiles) + cols - 1) // cols
            sheet = Image.new("RGB", (cols * w, rows * h + 44), (16, 12, 28))
            dr = ImageDraw.Draw(sheet)
            f = ImageFont.truetype(FONT, 26)
            f2 = ImageFont.truetype(FONT, 20)
            marks = {round(t, 2): m for t, m in clip["markers"]}
            dr.text((12, 8), "%s  (%.2fs%s)" % (name, L, ", loop" if clip["loop"] else ""), fill=(240, 236, 255), font=f)
            for i, (t, im) in enumerate(tiles):
                x, y = (i % cols) * w, 44 + (i // cols) * h
                sheet.paste(im, (x, y))
                label = "%.2fs" % t + ("  " + marks[round(t, 2)] if round(t, 2) in marks else "")
                dr.text((x + 10, y + 8), label, fill=(255, 240, 160), font=f2)
            sheet.save(os.path.join(out_dir, "sheet_%s.jpg" % name), quality=88)
            print("sheet", name, flush=True)


if __name__ == "__main__":
    main()
