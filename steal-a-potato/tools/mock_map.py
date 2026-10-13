"""Dry-run the generated map build script outside Roblox and check what it builds.

    python tools/mock_map.py <map.json> <BuildPotatoMap.lua>

Runs the script in the strict Studio mock (tools/mock_studio.lua):
  1. into an empty place, then again on top of itself (it must replace its own map);
  2. into a place that holds somebody else's things and the part 1 map (attribute Batch): the old
     map goes, the rest stays;
  3. into a place whose Workspace.PotatoMap was made by something else: it must change nothing
     and warn once.
After each build it compares Workspace.PotatoMap with map.json node by node: classes, names,
sizes, CFrames, colours, materials, surfaces (Inlet on all six faces for Plastic, Smooth
otherwise), flags, pivots, attributes and primary parts.
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from mock_potato import LUA_FLAG, FLAG_KEYS, Mock, children  # noqa: E402

SIDES = ("TopSurface", "BottomSurface", "FrontSurface", "BackSurface", "LeftSurface", "RightSurface")


def close(a, b, tol=3e-3):
    return np.allclose(np.asarray(a, float), np.asarray(b, float), atol=tol)


def attr_same(got, val):
    if isinstance(val, bool) or isinstance(got, bool):
        return got is val or got == val
    if isinstance(val, (int, float)):
        try:
            return abs(float(got) - float(val)) < 1e-3
        except Exception:
            return False
    return got == val


def check(m, data):
    ws = m.g.workspace
    maps = [c for c in children(ws) if c.Name == "PotatoMap"]
    if len(maps) != 1 or maps[0].ClassName != "Model":
        return ["%d PotatoMap models" % len(maps)]
    pm = maps[0]
    errs = []
    if pm.GetAttribute(pm, "Studs") is not True:
        errs.append("PotatoMap has no Studs = true")
    nodes = data["nodes"]
    kids = {}
    for n in nodes:
        kids.setdefault(n["parent"], []).append(n)
    lua_of = {nodes[0]["i"]: pm}
    stack = [(nodes[0], pm)]
    nparts = 0
    while stack:
        jn, lo = stack.pop()
        jk = kids.get(jn["i"], [])
        lk = children(lo)
        if len(jk) != len(lk):
            errs.append("%s: %d children expected, %d built" % (lo.Name, len(jk), len(lk)))
            continue
        for a, b in zip(jk, lk):
            lua_of[a["i"]] = b
            if a["name"] != b.Name:
                errs.append("name %s != %s (under %s)" % (a["name"], b.Name, lo.Name))
                continue
            nparts += a["kind"] in ("Part", "Marker")
            check_node(m, a, b, errs)
            stack.append((a, b))
        if len(errs) > 40:
            break
    for n in nodes:
        if n["kind"] == "Model" and n.get("primary") is not None and n["i"] in lua_of:
            b = lua_of[n["i"]]
            if not m.g.same(b.PrimaryPart, lua_of.get(n["primary"])):
                errs.append("model %s PrimaryPart" % n["name"])
    return errs, nparts


def check_node(m, a, b, errs):
    k = a["kind"]
    want = {"Folder": "Folder", "Model": "Model", "Marker": "Part", "Attachment": "Attachment"}.get(k)
    if k == "Part":
        want = "WedgePart" if a["shape"] == "Wedge" else "Part"
    if b.ClassName != want:
        errs.append("%s: class %s, wanted %s" % (a["name"], b.ClassName, want))
        return
    if k in ("Part", "Marker"):
        p, R = m.rows(b.CFrame)
        if not close(p, a["cf"][0]) or not close(R, a["cf"][1]):
            errs.append("part %s: CFrame off (%s vs %s)" % (a["name"], p.round(3), np.round(a["cf"][0], 3)))
        if not close(m.vec(b.Size), a["size"]):
            errs.append("part %s: size %s vs %s" % (a["name"], m.vec(b.Size).round(3), a["size"]))
    if k == "Attachment":
        wp, wR = m.rows(m.g.cf_mul(b.Parent.CFrame, b.CFrame))
        if not close(wp, a["cf"][0]) or not close(wR, a["cf"][1]):
            errs.append("attachment %s off" % a["name"])
    if k == "Marker":
        if not (b.Anchored and not b.CanCollide and not b.CanTouch and not b.CanQuery and b.Transparency == 1):
            errs.append("marker %s: not an invisible anchored part" % a["name"])
    if k == "Part":
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
    for key, val in (a.get("attrs") or {}).items():
        if not attr_same(b.GetAttribute(b, key), val):
            errs.append("%s attribute %s: %s vs %s" % (a["name"], key, b.GetAttribute(b, key), val))


def others(m):
    out = []
    for d in m.g.workspace.GetDescendants(m.g.workspace).values():
        if d.Name.startswith("NotOurs"):
            out.append(d.Name)
    return sorted(out)


def plant(m, name, cls, attrs=None, parent=None):
    o = m.g.mock_new(cls, m.lua.table_from({"Name": name}))
    o.Parent = parent if parent is not None else m.g.workspace
    for k, v in (attrs or {}).items():
        o.SetAttribute(o, k, v)
    return o


def run(m, script, data, label, expect_refusal=False):
    before = others(m)
    nwarn0 = len(list(m.g.WARNINGS.values()))
    m.run(script)
    warns = list(m.g.WARNINGS.values())[nwarn0:]
    errs = []
    if expect_refusal:
        maps = [c for c in children(m.g.workspace) if c.Name == "PotatoMap"]
        if len(maps) != 1 or maps[0].GetAttribute(maps[0], "Studs") is not None:
            errs.append("a foreign PotatoMap was touched")
        if len(warns) != 1:
            errs.append("expected one warning, got %d" % len(warns))
        warns = []
        n = 0
    else:
        errs, n = check(m, data)
    if others(m) != before:
        errs.append("somebody else's things changed: %s -> %s" % (before, others(m)))
    print("%-40s errors %d  warnings %d  parts %d  %s" % (label, len(errs), len(warns), n,
                                                           list(m.g.PRINTS.values())[-1:]))
    for e in errs[:15]:
        print("    ", e)
    for w in warns:
        print("     warn:", w)
    return len(errs) + len(warns)


def main(path, script_path):
    data = json.load(open(path))
    script = open(script_path).read()
    total = 0
    m = Mock()
    total += run(m, script, data, "empty place")
    total += run(m, script, data, "empty place (again)")
    m = Mock()
    plant(m, "NotOursModel", "Model")
    plant(m, "PotatoMap", "Model", {"Batch": 1})
    total += run(m, script, data, "part 1 map and somebody else's things")
    m = Mock()
    theirs = plant(m, "PotatoMap", "Model")
    plant(m, "NotOursTheirMapPart", "Folder", parent=theirs)
    total += run(m, script, data, "a PotatoMap made by something else", expect_refusal=True)
    print("PROBLEMS:", total)
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
