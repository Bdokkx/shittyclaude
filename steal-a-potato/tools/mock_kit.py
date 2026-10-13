"""Dry-run a generated kit-piece build script outside Roblox and check what it builds.

    python tools/mock_kit.py out/<piece>.json out/Build<Piece>.lua [Folder=anims.json ...]

Runs the script in the strict Studio mock (tools/mock_studio.lua) three ways: into an empty
place; into a place whose PotatoKit already holds somebody else's things plus a stale copy of
every item this script makes (it must replace those and leave the rest); and a second time on
top of itself. After each run it compares ReplicatedStorage.PotatoKit with the piece's JSON node
by node: classes, names, sizes, CFrames, colours, materials, surfaces (Inlet on all six faces for
Plastic, Smooth otherwise), flags, pivots, welds, Motor6D C0/C1, attributes, primary parts and
every keyframe and pose of the clips.
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from mock_potato import LUA_FLAG, FLAG_KEYS, Mock, attr_eq, children  # noqa: E402

SIDES = ("TopSurface", "BottomSurface", "FrontSurface", "BackSurface", "LeftSurface", "RightSurface")


def close(a, b, tol=2e-3):
    return np.allclose(np.asarray(a, float), np.asarray(b, float), atol=tol)


def check(m, data, anims):
    g = m.g
    rsto = g.game.GetService(g.game, "ReplicatedStorage")
    kits = [c for c in children(rsto) if c.Name == "PotatoKit"]
    if len(kits) != 1 or kits[0].ClassName != "Folder":
        return ["%d PotatoKit folders" % len(kits)]
    kit = kits[0]
    errs = []
    if kit.GetAttribute(kit, "Studs") is not True:
        errs.append("PotatoKit has no Studs = true")
    nodes = data["nodes"]
    kids = {}
    for n in nodes:
        kids.setdefault(n["parent"], []).append(n)
    root = nodes[0]
    lua_of = {root["i"]: kit}

    def named(lo, name):
        return [c for c in children(lo) if c.Name == name]

    def merge(jn, lo):
        """jn is a container: find each of its children by name."""
        for a in kids.get(jn["i"], []):
            got = named(lo, a["name"])
            if len(got) != 1:
                errs.append("%s.%s: %d found" % (lo.Name, a["name"], len(got)))
                continue
            b = got[0]
            lua_of[a["i"]] = b
            if a.get("container"):
                if b.ClassName != "Folder":
                    errs.append("%s is a %s" % (a["name"], b.ClassName))
                    continue
                if a["name"] in anims:
                    check_anims(b, anims[a["name"]])
                    continue
                merge(a, b)
            else:
                check_node(a, b)
                walk(a, b)

    def walk(jn, lo):
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
            walk(a, b)

    def check_node(a, b):
        k = a["kind"]
        want = {"Folder": "Folder", "Model": "Model", "Attachment": "Attachment", "Weld": "WeldConstraint",
                "Motor": "Motor6D", "Animator": "Animator", "AnimationController": "AnimationController"}.get(k)
        if k == "Part":
            want = "WedgePart" if a["shape"] == "Wedge" else "Part"
        if k == "Light":
            want = a["cls"]
        if b.ClassName != want:
            errs.append("%s: class %s, wanted %s" % (a["name"], b.ClassName, want))
            return
        if k == "Part":
            p, R = m.rows(b.CFrame)
            if not close(p, a["cf"][0]) or not close(R, a["cf"][1]):
                errs.append("part %s: CFrame off (%s vs %s)" % (a["name"], p.round(3), np.round(a["cf"][0], 3)))
            if not close(m.vec(b.Size), a["size"]):
                errs.append("part %s: size" % a["name"])
            for key in FLAG_KEYS:
                if bool(b[LUA_FLAG[key]]) != bool(a[key]):
                    errs.append("part %s: %s is %s" % (a["name"], LUA_FLAG[key], b[LUA_FLAG[key]]))
            col = [int(round(v)) for v in b.Color.rgb.values()]
            if col != list(a["color"]):
                errs.append("part %s colour %s vs %s" % (a["name"], col, a["color"]))
            if b.Material.Name != a["material"]:
                errs.append("part %s material %s" % (a["name"], b.Material.Name))
            if abs(b.Transparency - a["transparency"]) > 1e-6:
                errs.append("part %s transparency" % a["name"])
            if a["shape"] != "Wedge" and b.Shape.Name != a["shape"]:
                errs.append("part %s shape %s" % (a["name"], b.Shape.Name))
            faces = {b[s].Name for s in SIDES}
            want_f = {"Inlet"} if a["material"] == "Plastic" else {"Smooth"}
            if faces != want_f:
                errs.append("part %s (%s) surfaces %s" % (a["name"], a["material"], faces))
            if a.get("pivot") is not None:
                wp, wR = m.rows(m.g.cf_mul(b.CFrame, b.PivotOffset))
                d = a["cf"]
                tp = np.array(d[1]) @ np.array(a["pivot"][0]) + np.array(d[0])
                tR = np.array(d[1]) @ np.array(a["pivot"][1])
                if not close(wp, tp) or not close(wR, tR):
                    errs.append("part %s pivot" % a["name"])
        elif k == "Attachment":
            wp, wR = m.rows(m.g.cf_mul(b.Parent.CFrame, b.CFrame))
            if not close(wp, a["cf"][0]) or not close(wR, a["cf"][1]):
                errs.append("attachment %s off" % a["name"])
        elif k == "Model" and a.get("wpivot") is not None:
            wp, wR = m.rows(b.WorldPivot)
            if not close(wp, a["wpivot"][0]) or not close(wR, a["wpivot"][1]):
                errs.append("model %s WorldPivot" % a["name"])
        for key, val in (a.get("attrs") or {}).items():
            if not attr_eq(b.GetAttribute(b, key), val):
                errs.append("%s attribute %s" % (a["name"], key))

    def check_anims(folder, ks_list):
        got = {c.Name: c for c in children(folder)}
        for ks in ks_list:
            name = ks["name"]
            if name not in got:
                errs.append("clip %s missing" % name)
                continue
            if len([c for c in children(folder) if c.Name == name]) != 1:
                errs.append("clip %s twice" % name)
            b = got[name]
            if b.ClassName != "KeyframeSequence" or bool(b.Loop) != ks["props"]["Loop"]["Bool"] or \
                    b.Priority.Value != ks["props"]["Priority"]["Enum"]:
                errs.append("%s: class / Loop / Priority" % name)
            kfs = children(b)
            if len(kfs) != len(ks["children"]):
                errs.append("%s: %d keyframes, wanted %d" % (name, len(kfs), len(ks["children"])))
                continue
            for jkf, lkf in zip(ks["children"], kfs):
                if abs(lkf.Time - jkf["props"]["Time"]["Float32"]) > 1e-4:
                    errs.append("%s: keyframe time" % name)
                    break

                def cmp(jp, lp):
                    if jp["class"] != lp.ClassName or jp["name"] != lp.Name:
                        errs.append("%s: %s %s vs %s %s" % (name, jp["class"], jp["name"], lp.ClassName, lp.Name))
                        return
                    if jp["class"] == "Pose":
                        c = jp["props"]["CFrame"]["CFrame"]
                        p_, R_ = m.rows(lp.CFrame)
                        if not close(p_, c["position"], 2e-3) or not close(R_, c["orientation"], 2e-3):
                            errs.append("%s: pose %s CFrame" % (name, jp["name"]))
                        if abs(lp.Weight - jp["props"]["Weight"]["Float32"]) > 1e-3 or lp.EasingStyle.Name != "Linear":
                            errs.append("%s: pose %s weight / easing" % (name, jp["name"]))
                    lch = children(lp)
                    if len(lch) != len(jp["children"]):
                        errs.append("%s: %s children" % (name, jp["name"]))
                        return
                    for a_, b_ in zip(jp["children"], lch):
                        cmp(a_, b_)
                if len(children(lkf)) != len(jkf["children"]):
                    errs.append("%s: keyframe children" % name)
                for a_, b_ in zip(jkf["children"], children(lkf)):
                    cmp(a_, b_)

    merge(root, kit)
    for n in nodes:
        b = lua_of.get(n["i"])
        if b is None:
            continue
        same = m.g.same
        if n["kind"] in ("Weld", "Motor"):
            if not (same(b.Part0, lua_of.get(n["part0"])) and same(b.Part1, lua_of.get(n["part1"])) and
                    same(b.Parent, lua_of.get(n["parent"]))):
                errs.append("%s %s wired wrong" % (n["kind"], n["name"]))
            if n["kind"] == "Motor":
                hp, hR = np.array(n["hinge"][0]), np.array(n["hinge"][1])
                for part, c in ((b.Part0, b.C0), (b.Part1, b.C1)):
                    wp, wR = m.rows(m.g.cf_mul(part.CFrame, c))
                    if not close(wp, hp) or not close(wR, hR):
                        errs.append("motor %s: C0/C1 not on the hinge" % n["name"])
        elif n["kind"] == "Model" and n.get("primary") is not None:
            if not same(b.PrimaryPart, lua_of.get(n["primary"])):
                errs.append("model %s PrimaryPart" % n["name"])
    return errs


def seed_place(m, data):
    """A PotatoKit that already holds somebody else's things and a stale copy of every item."""
    new = m.g.mock_new
    tbl = m.lua.table_from
    rsto = m.g.game.GetService(m.g.game, "ReplicatedStorage")
    kit = new("Folder", tbl({"Name": "PotatoKit"}))
    kit.Parent = rsto
    theirs = new("Folder", tbl({"Name": "TheirStuff"}))
    theirs.Parent = kit
    nodes = data["nodes"]
    by = {n["i"]: n for n in nodes}
    live = {nodes[0]["i"]: kit}
    for n in nodes[1:]:
        par = live.get(n["parent"])
        if par is None or not (by[n["parent"]]["parent"] is None or by[n["parent"]].get("container")):
            continue
        if n.get("container"):
            f = new("Folder", tbl({"Name": n["name"]}))
            f.Parent = par
            live[n["i"]] = f
            other = new("Model", tbl({"Name": "NotOurs_" + n["name"]}))
            other.Parent = f
        else:
            stale = new("Model", tbl({"Name": n["name"]}))
            stale.Parent = par
    return kit


def count_names(m):
    rsto = m.g.game.GetService(m.g.game, "ReplicatedStorage")
    out = []
    for d in rsto.GetDescendants(rsto).values():
        if d.Name.startswith("NotOurs_") or d.Name == "TheirStuff":
            out.append(d.Name)
    return sorted(out)


def run_case(data, script, anims, label, seeded):
    m = Mock()
    expected_theirs = []
    if seeded:
        seed_place(m, data)
        expected_theirs = count_names(m)
    total = 0
    for k in range(2):
        m.run(script)
        errs = check(m, data, anims)
        theirs = count_names(m)
        if theirs != expected_theirs:
            errs.append("somebody else's things changed: %s -> %s" % (expected_theirs, theirs))
        warns = list(m.g.WARNINGS.values())
        print("%-34s errors %d  warnings %d  %s" % (label + (" (again)" if k else ""), len(errs), len(warns),
                                                     list(m.g.PRINTS.values())[-1:]))
        for e in errs[:12]:
            print("    ", e)
        for w in warns:
            print("     warn:", w)
        total += len(errs) + len(warns)
    return total


def main(piece, script_path, anim_specs):
    data = json.load(open(piece))
    script = open(script_path).read()
    anims = {k: json.load(open(v))[0]["children"] for k, v in anim_specs.items()}
    total = run_case(data, script, anims, "empty place", False)
    total += run_case(data, script, anims, "PotatoKit already in use", True)
    print("PROBLEMS:", total)
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], dict(a.split("=", 1) for a in sys.argv[3:] if "=" in a))
