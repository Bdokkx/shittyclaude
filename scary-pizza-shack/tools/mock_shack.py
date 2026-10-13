"""Dry-run a generated build script outside Roblox and check what it builds.

    python tools/mock_shack.py out/map.json out/BuildPizzaShack.lua                  # batch 1
    python tools/mock_shack.py out/assets.json out/BuildPizzaShackAssets.lua assets  # batch 2

A strict Studio mock (tools/mock_studio.lua) stands in for the engine. Each case
puts a LoadAsset-like container of MeshParts under Workspace (optionally scaled,
and turned either on the CFrames or baked into the meshes), runs the script, and
compares Workspace.PizzaShack with map.json node by node: classes, names, sizes,
CFrames, colours, materials, flags, surfaces, pivots, welds, joints, attachments,
lights, attributes, primary parts. Then it runs the script again without an
import (it must reuse ServerStorage.PizzaShackMeshes) and once more with a fresh,
differently turned import, and checks nothing is left over.
"""
import json
import math
import os
import sys

import numpy as np
from lupa import LuaRuntime

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from gen_build import CONFIGS  # noqa: E402

CFG = CONFIGS["map"]
FLAG_KEYS = ("anchored", "collide", "touch", "query", "shadow", "massless")
LUA_FLAG = {"anchored": "Anchored", "collide": "CanCollide", "touch": "CanTouch", "query": "CanQuery",
            "shadow": "CastShadow", "massless": "Massless"}



def attr_eq(got, val):
    """An attribute read back from the mock against map.json (Vector3s arrive as [x, y, z])."""
    if isinstance(val, (list, tuple)):
        try:
            return all(abs(float(a) - float(b)) < 1e-3 for a, b in zip((got.X, got.Y, got.Z), val))
        except Exception:
            return False
    return got == val

def rot_y(deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return np.array(((c, 0, s), (0, 1, 0), (-s, 0, c)))


def rot_x(deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return np.array(((1, 0, 0), (0, c, -s), (0, s, c)))


class Mock:
    def __init__(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute(open(os.path.join(HERE, "mock_studio.lua")).read())
        self.g = self.lua.globals()

    def cf(self, p, R):
        R = np.asarray(R, float)
        return self.g.make_cframe(*[float(v) for v in p], *[float(v) for v in R.ravel()])

    def rows(self, c):
        v = list(self.g.cframe_rows(c))
        return np.array(v[:3]), np.array(v[3:]).reshape(3, 3)

    def vec(self, v):
        return np.array((v.X, v.Y, v.Z))

    def import_container(self, meshes, scale=1.0, R_imp=np.eye(3), mode="cframe", offset=(37.0, 5.0, -80.0)):
        """A LoadAsset-like Model with a nested model of MeshParts named like the FBX meshes."""
        new = self.g.mock_new
        stem = CFG["fbx"].rsplit(".", 1)[0]
        outer = new("Model", self.lua.table_from({"Name": stem}))
        inner = new("Model", self.lua.table_from({"Name": stem}))
        inner.Parent = outer
        k = 0
        off = np.array(offset)
        for name, info in meshes.items():
            size = np.array(info["size"]) * scale
            local = np.array((k % 13 * 9.0, 0.0, k // 13 * 9.0)) * scale
            k += 1
            pos = off + R_imp @ local
            if mode == "cframe":
                R, sz = R_imp, size
            else:                                    # turn baked into the vertices: size permuted
                R, sz = np.eye(3), np.abs(R_imp) @ size
            mp = new("MeshPart", self.lua.table_from({"Name": name}))
            mp.Size = self.g.Vector3.new(*[float(v) for v in sz])
            mp.CFrame = self.cf(pos, R)
            extra = new("SurfaceAppearance", None)
            extra.Parent = mp
            mp.Parent = inner
        ax = CFG["axis"]
        for name, d in ((ax + "O", (0, 0, 0)), (ax + "X", (4, 0, 0)), (ax + "Y", (0, 4, 0)), (ax + "Z", (0, 0, 4))):
            mp = new("MeshPart", self.lua.table_from({"Name": name}))
            mp.Size = self.g.Vector3.new(0.25 * scale, 0.25 * scale, 0.25 * scale)
            mp.CFrame = self.cf(off + R_imp @ ((np.array((-30.0, 0, 0)) + np.array(d)) * scale),
                                R_imp if mode == "cframe" else np.eye(3))
            mp.Parent = inner
        outer.Parent = self.g.workspace
        return outer

    def run(self, script):
        fn = self.lua.eval("function(src) local f, err = load(src, 'BuildScript') "
                           "if not f then error(err) end return f() end")
        fn(script)


def children(o):
    return list(o.GetChildren(o).values())


def check(m, data, R_geom=np.eye(3), size_map=None, tag=""):
    """Compare Workspace.PizzaShack with map.json. R_geom: how the mesh geometry is turned
    inside the MeshPart's own frame (baked import turn)."""
    g = m.g
    ws = g.workspace
    roots = [c for c in children(ws) if c.Name == CFG["root"]]
    errs = []
    if len(roots) != 1:
        return ["%d %s roots in Workspace" % (len(roots), CFG["root"])]
    root = roots[0]
    nodes = data["nodes"]
    kids = {}
    for n in nodes:
        kids.setdefault(n["parent"], []).append(n)
    lua_of = {nodes[0]["i"]: root}

    def close(a, b, tol=2e-3):
        return np.allclose(np.asarray(a, float), np.asarray(b, float), atol=tol)

    def walk(jn, lo):
        # the script makes every instance in data order, except welds and motors, which come
        # last (once every part exists): so a parent's children are its other children in
        # order, then its joints in order
        jk = kids.get(jn["i"], [])
        jk = [c for c in jk if c["kind"] not in ("Weld", "Motor")] + [c for c in jk if c["kind"] in ("Weld", "Motor")]
        lk = children(lo)
        if len(jk) != len(lk):
            errs.append("%s: %d children expected, %d built" % (lo.Name, len(jk), len(lk)))
            return
        for a, b in zip(jk, lk):
            lua_of[a["i"]] = b
            if a["name"] != b.Name:
                errs.append("name %s != %s (under %s)" % (a["name"], b.Name, lo.Name))
                continue
            check_node(a, b)
            if a["kind"] in ("Folder", "Model", "Accessory", "Part", "MeshPart", "Marker", "Humanoid"):
                walk(a, b)

    def check_node(a, b):
        k = a["kind"]
        cls = b.ClassName
        want = {"Folder": "Folder", "Model": "Model", "MeshPart": "MeshPart", "Marker": "Part", "Attachment": "Attachment",
                "Weld": "WeldConstraint", "Motor": "Motor6D", "Accessory": "Accessory", "Humanoid": "Humanoid",
                "Animator": "Animator", "SpecialMesh": "SpecialMesh"}.get(k)
        if k == "Part":
            want = "WedgePart" if a["shape"] == "Wedge" else "Part"
        if k == "Light":
            want = a["cls"]
        if cls != want:
            errs.append("%s: class %s, wanted %s" % (a["name"], cls, want))
            return
        if k in ("Part", "Marker", "MeshPart"):
            p, R = m.rows(b.CFrame)
            tp, tR = np.array(a["cf"][0]), np.array(a["cf"][1])
            if k == "MeshPart":
                R = R @ R_geom
            if not close(p, tp) or not close(R, tR):
                errs.append("%s %s: CFrame off (%s vs %s)" % (k, a["name"], p.round(3), tp.round(3)))
            size = m.vec(b.Size)
            wsize = np.array(a["size"])
            if k == "MeshPart":
                wsize = np.abs(R_geom) @ wsize
            if not close(size, wsize):
                errs.append("%s %s: size %s vs %s" % (k, a["name"], size.round(3), wsize.round(3)))
            for key in FLAG_KEYS:
                if k == "Marker":
                    exp = {"anchored": a.get("anchored", True), "collide": False, "touch": False, "query": False,
                           "shadow": False, "massless": a.get("massless", False)}[key]
                else:
                    exp = a[key]
                if bool(b[LUA_FLAG[key]]) != bool(exp):
                    errs.append("%s %s: %s is %s" % (k, a["name"], LUA_FLAG[key], b[LUA_FLAG[key]]))
            if k == "Marker":
                if b.Transparency != 1:
                    errs.append("marker %s visible" % a["name"])
            else:
                col = list(b.Color.rgb.values())
                if [int(round(v)) for v in col] != list(a["color"]):
                    errs.append("%s colour %s vs %s" % (a["name"], col, a["color"]))
                if b.Material.Name != a["material"]:
                    errs.append("%s material %s vs %s" % (a["name"], b.Material.Name, a["material"]))
                if abs(b.Transparency - a["transparency"]) > 1e-6:
                    errs.append("%s transparency" % a["name"])
            if k == "Part":
                if a["shape"] != "Wedge" and b.Shape.Name != a["shape"]:
                    errs.append("%s shape %s" % (a["name"], b.Shape.Name))
                top, bot = b.TopSurface.Name, b.BottomSurface.Name
                sides = {b[s].Name for s in ("FrontSurface", "BackSurface", "LeftSurface", "RightSurface")}
                exp = {"studs": ("Studs", "Inlet"), "wedge": ("Smooth", "Inlet"), "smooth": ("Smooth", "Smooth")}
                if (top, bot) != exp[a["surfaces"]] or sides != {"Smooth"}:
                    errs.append("%s surfaces %s/%s/%s" % (a["name"], top, bot, sides))
            if a.get("pivot") is not None:
                wp, wR = m.rows(m.g.cf_mul(b.CFrame, b.PivotOffset))
                d = a["cf"]
                tcf = (np.array(d[1]) @ np.array(a["pivot"][0]) + np.array(d[0]),
                       np.array(d[1]) @ np.array(a["pivot"][1]))
                if not close(wp, tcf[0]) or not close(wR, tcf[1]):
                    errs.append("%s pivot off: %s vs %s" % (a["name"], wp.round(3), tcf[0].round(3)))
            for key, val in (a.get("attrs") or {}).items():
                if not attr_eq(b.GetAttribute(b, key), val):
                    errs.append("%s attribute %s" % (a["name"], key))
        elif k == "Attachment":
            par = b.Parent
            wp, wR = m.rows(m.g.cf_mul(par.CFrame, b.CFrame))
            if not close(wp, a["cf"][0]) or not close(wR, a["cf"][1]):
                errs.append("attachment %s off" % a["name"])
            for key, val in (a.get("attrs") or {}).items():
                if not attr_eq(b.GetAttribute(b, key), val):
                    errs.append("attachment %s attribute %s" % (a["name"], key))
        elif k == "Humanoid":
            if b.RigType.Name != a["rig"] or b.DisplayDistanceType.Name != "None":
                errs.append("humanoid %s settings" % a["name"])
        elif k == "SpecialMesh":
            if b.MeshType.Name != a["mesh_type"] or not close(m.vec(b.Scale), a["scale"], 1e-4):
                errs.append("special mesh %s" % a["name"])
        elif k == "Light":
            if abs(b.Brightness - a["brightness"]) > 1e-6 or abs(b.Range - a["range"]) > 1e-6:
                errs.append("light %s values" % a["name"])
            if bool(b.Enabled) != bool(a.get("enabled", True)):
                errs.append("light %s enabled" % a["name"])
        elif k in ("Model", "Accessory"):
            for key, val in (a.get("attrs") or {}).items():
                if not attr_eq(b.GetAttribute(b, key), val):
                    errs.append("model %s attribute %s" % (a["name"], key))

    walk(nodes[0], root)
    # references: welds, motors, primary parts
    for n in nodes:
        b = lua_of.get(n["i"])
        if b is None:
            continue
        if n["kind"] == "Weld":
            same = m.g.same
            if not (same(b.Part0, lua_of[n["part0"]]) and same(b.Part1, lua_of[n["part1"]]) and
                    same(b.Parent, lua_of[n["parent"]])):
                errs.append("weld %s wired wrong" % n["name"])
        elif n["kind"] == "Motor":
            same = m.g.same
            if not (same(b.Part0, lua_of[n["part0"]]) and same(b.Part1, lua_of[n["part1"]]) and
                    same(b.Parent, lua_of[n["parent"]])):
                errs.append("motor %s wired wrong" % n["name"])
            hp, hR = np.array(n["hinge"][0]), np.array(n["hinge"][1])
            for part, c in ((b.Part0, b.C0), (b.Part1, b.C1)):
                wp, wR = m.rows(m.g.cf_mul(part.CFrame, c))
                if not close(wp, hp) or not close(wR, hR):
                    errs.append("motor %s: C0/C1 not on the hinge" % n["name"])
        elif n["kind"] == "Model" and n.get("primary") is not None:
            if not m.g.same(b.PrimaryPart, lua_of[n["primary"]]):
                errs.append("model %s PrimaryPart" % n["name"])
    return errs


def leftovers(m):
    bad = []
    for d in m.g.workspace.GetDescendants(m.g.workspace).values():
        if d.ClassName == "MeshPart" and (d.Name.startswith(CFG["axis"]) or "__" in d.Name):
            bad.append(d.Name)
    names = [c.Name for c in children(m.g.workspace)]
    return bad, names


def case(data, script, scale, R_imp, mode, label):
    m = Mock()
    meshes = data["meshes"]
    cont = m.import_container(meshes, scale, R_imp, mode)
    created0 = m.g.CREATED
    m.run(script)
    R_geom = R_imp if mode == "baked" else np.eye(3)
    errs = check(m, data, R_geom=R_geom)
    bad, names = leftovers(m)
    warns = list(m.g.WARNINGS.values())
    cache = m.g.game.GetService(m.g.game, "ServerStorage").FindFirstChild(
        m.g.game.GetService(m.g.game, "ServerStorage"), CFG["cache"])
    ncache = len(children(cache)) if cache else 0
    print("%-34s errors %d  leftovers %d  workspace %s  cache %d  warnings %d  %s" % (
        label, len(errs), len(bad), names, ncache, len(warns), list(m.g.PRINTS.values())[-1:]))
    for e in errs[:12]:
        print("    ", e)
    for w in warns:
        print("     warn:", w)
    # second run, no import: uses the cache, replaces the map
    m.run(script)
    errs2 = check(m, data, R_geom=R_geom)
    bad2, names2 = leftovers(m)
    print("%-34s errors %d  leftovers %d  workspace %s  %s" % (
        "   again, no import", len(errs2), len(bad2), names2, list(m.g.PRINTS.values())[-1:]))
    for e in errs2[:6]:
        print("    ", e)
    # third run: a fresh import turned differently
    R2 = rot_y(90)
    m.import_container(meshes, 0.5, R2, "baked", offset=(-200.0, 3.0, 40.0))
    m.run(script)
    errs3 = check(m, data, R_geom=R2)
    bad3, names3 = leftovers(m)
    print("%-34s errors %d  leftovers %d  workspace %s  %s" % (
        "   again, new turned import", len(errs3), len(bad3), names3, list(m.g.PRINTS.values())[-1:]))
    for e in errs3[:6]:
        print("    ", e)
    return len(errs) + len(errs2) + len(errs3) + len(bad) + len(bad2) + len(bad3) + len(warns)


def no_import_case(script):
    m = Mock()
    m.run(script)
    warns = list(m.g.WARNINGS.values())
    names = [c.Name for c in children(m.g.workspace)]
    print("%-34s warnings %s  workspace %s" % ("no import, no cache", warns, names))
    return 0 if warns and not names else 1


def main(map_path, script_path, config="map"):
    global CFG
    CFG = CONFIGS[config]
    data = json.load(open(map_path))
    script = open(script_path).read()
    total = 0
    total += case(data, script, 1.0, np.eye(3), "cframe", "plain import")
    total += case(data, script, 0.01, np.eye(3), "cframe", "scaled 0.01")
    total += case(data, script, 1.0, rot_y(90) @ rot_x(90), "cframe", "turned (CFrames)")
    total += case(data, script, 2.0, rot_y(-90), "baked", "turned (baked into meshes) x2")
    total += no_import_case(script)
    print("PROBLEMS:", total)
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], *(sys.argv[3:4] or ["map"]))
