"""Write the unattended Studio build script for Workspace.PotatoMap (bricks only).

    python tools/gen_map.py <map.json> <stamps.json> <BuildPotatoMap.lua> "<title>"

map.json is the whole map as a spslib scene (every part placed, for the checks); stamps.json lists
the templates (pieces placed many times: mounds, props, heroes) and every copy of them. The script
writes each template once and makes the copies in Studio: turned, moved, scaled about its pivot,
recoloured and (for a solid prop) with its big parts made solid, exactly as the scene has them.

Every Plastic part gets Inlet on all six faces; Neon and SmoothPlastic parts are Smooth all round.
Markers are invisible anchored parts with CanCollide, CanTouch and CanQuery off.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from gen_build import SHAPE, Tables, flags, lua_name, num  # noqa: E402

SURF = {"smooth": 0, "inlet": 3}
BIG = 2.0


def attr_rec(tag, me, key, val):
    if isinstance(val, bool):
        return "%s %s %s b %s" % (tag, me, key, "1" if val else "0")
    if isinstance(val, (int, float)):
        return "%s %s %s n %s" % (tag, me, key, num(val, 4))
    return "%s %s %s s %s" % (tag, me, key, lua_name(str(val)))


def main(src, stamps_path, dst, title):
    data = json.load(open(src))
    nodes = data["nodes"]
    assert not data.get("meshes"), "bricks only"
    st = json.load(open(stamps_path))
    tb = Tables()
    lines = []
    stats = {"Part": 0, "Neon": 0, "Inlet": 0, "templates": 0, "copies": 0, "template_parts": 0}

    # 1. the templates
    tkey = {}
    for key, t in st["templates"].items():
        tkey[key] = len(tkey) + 1
        lines.append("B %d %s" % (tkey[key], lua_name(key)))
        stats["templates"] += 1
        for q in t["parts"]:
            mat, surf = q["material"], q["surfaces"]
            if mat == "Plastic":
                assert surf == "inlet", "%s/%s: Plastic parts are Inlet all round" % (key, q["name"])
            else:
                assert surf == "smooth", "%s/%s: %s parts are Smooth all round" % (key, q["name"], mat)
            sx, sy, sz = q["size"]
            big = 1 if max(q["size"]) >= BIG and q["transparency"] < 1.0 else 0
            lines.append("Q %s %s %s %s %s %s %d %d %d %s %d %d %d" % (
                lua_name(q["name"]), SHAPE[q["shape"]], num(sx), num(sy), num(sz),
                " ".join(num(v) for v in q["rel"][0]), tb.rot(q["rel"][1]), tb.color(q["color"]), tb.mat(mat),
                num(q["transparency"]), flags(q["flags"], {}), SURF[surf], big))
            stats["template_parts"] += 1
            for ak, av in (q.get("attrs") or {}).items():
                lines.append(attr_rec("QA", "-", ak, av))
        lines.append("QP %d" % (t["primary"] + 1))

    # 2. the recolour maps
    kid = {}
    for inst in st["instances"]:
        pairs = tuple(sorted((tb.color(a), tb.color(b)) for a, b in inst["recolour"]))
        if pairs and pairs not in kid:
            kid[pairs] = len(kid) + 1
            lines.append("K %d %s" % (kid[pairs], " ".join("%d %d" % ab for ab in pairs)))
    inst_of = {}
    for inst in st["instances"]:
        inst_of[inst["node"]] = inst

    # 3. the tree: folders, models, parts, markers, copies
    idx = {}
    count = 0
    post = []
    skip = set()
    by_parent = {}
    for n in nodes:
        by_parent.setdefault(n["parent"], []).append(n)
    by_i = {n["i"]: n for n in nodes}

    def new(n):
        nonlocal count
        count += 1
        idx[n["i"]] = count
        return count

    for n in nodes:
        k = n["kind"]
        if n["parent"] is None:
            idx[n["i"]] = 0
            if n.get("primary") is not None:
                post.append(("R 0 %d", n["primary"]))
            continue
        if n["parent"] in skip:
            skip.add(n["i"])
            continue
        par = idx[n["parent"]]
        name = lua_name(n["name"])
        if n["i"] in inst_of:
            inst = inst_of[n["i"]]
            me = new(n)
            pairs = tuple(sorted((tb.color(a), tb.color(b)) for a, b in inst["recolour"]))
            lines.append("I %d %s %d %s %d %s %d %d" % (
                par, name, tkey[inst["key"]], " ".join(num(v) for v in inst["cf"][0]), tb.rot(inst["cf"][1]),
                num(inst["scale"], 4), kid.get(pairs, 0), 1 if inst["solid"] else 0))
            stats["copies"] += 1
            stats["Part"] += len(st["templates"][inst["key"]]["parts"])
            skip.add(n["i"])
            for ak, av in (n.get("attrs") or {}).items():
                post.append(attr_rec("T", me, ak, av))
            continue
        if k in ("Folder", "Model"):
            me = new(n)
            lines.append("%s %d %s" % ("F" if k == "Folder" else "M", par, name))
            if n.get("primary") is not None:
                post.append(("R %d %%d" % me, n["primary"]))
        elif k == "Part":
            me = new(n)
            stats["Part"] += 1
            mat, surf = n["material"], n["surfaces"]
            if mat == "Plastic":
                assert surf == "inlet", "%s: Plastic parts are Inlet all round" % n["name"]
                stats["Inlet"] += 1
            else:
                assert surf == "smooth", "%s: %s parts are Smooth all round" % (n["name"], mat)
            stats["Neon"] += mat == "Neon"
            sx, sy, sz = n["size"]
            lines.append("P %d %s %s %s %s %s %s %d %d %d %s %d %d" % (
                par, name, SHAPE[n["shape"]], num(sx), num(sy), num(sz), " ".join(num(v) for v in n["cf"][0]),
                tb.rot(n["cf"][1]), tb.color(n["color"]), tb.mat(mat), num(n["transparency"]), flags(n, {}),
                SURF[surf]))
            if n.get("pivot") is not None:
                post.append("V %d %s %d" % (me, " ".join(num(v) for v in n["pivot"][0]), tb.rot(n["pivot"][1])))
        elif k == "Attachment":
            me = new(n)
            pn = by_i[n["parent"]]
            import numpy as np
            Rp, pp = np.array(pn["cf"][1]), np.array(pn["cf"][0])
            rel_p = Rp.T @ (np.array(n["cf"][0]) - pp)
            rel_R = Rp.T @ np.array(n["cf"][1])
            lines.append("A %d %s %s %d" % (par, name, " ".join(num(v) for v in rel_p), tb.rot(rel_R.tolist())))
        elif k == "Marker":
            me = new(n)
            sx, sy, sz = n["size"]
            lines.append("X %d %s %s %s %s %s %d" % (par, name, num(sx), num(sy), num(sz),
                                                   " ".join(num(v) for v in n["cf"][0]), tb.rot(n["cf"][1])))
        else:
            raise SystemExit("gen_map: unexpected %s %s" % (k, n["name"]))
        for ak, av in (n.get("attrs") or {}).items():
            post.append(attr_rec("T", me, ak, av))
    for rec in post:
        if isinstance(rec, tuple):
            fmt, prim = rec
            lines.append(fmt % idx[prim])
        else:
            lines.append(rec)

    colors = ", ".join("{%d, %d, %d}" % c for c in tb.colors)
    mats = ", ".join('"%s"' % m for m in tb.mats)
    rots = ",\n\t".join("{%s}" % ", ".join(num(v, 5) for v in r) for r in tb.rots)
    body = TEMPLATE
    for key, val in (("@@TITLE@@", title), ("@@NPARTS@@", str(stats["Part"])), ("@@COLORS@@", colors),
                     ("@@MATS@@", mats), ("@@ROTS@@", rots), ("@@FILE@@", os.path.basename(dst)),
                     ("@@NTEMPL@@", str(stats["templates"])), ("@@NCOPIES@@", str(stats["copies"]))):
        body = body.replace(key, val)
    blob = "\n".join(lines)
    assert "]]" not in blob
    body = body.replace("@@DATA@@", blob)
    assert "@@" not in body
    with open(dst, "w") as f:
        f.write(body)
    print("wrote %s: %d records, %d parts (%d templates of %d parts, %d copies), %d rotations, %d colours, %.0f KB"
          % (dst, len(lines), stats["Part"], stats["templates"], stats["template_parts"], stats["copies"],
             len(tb.rots), len(tb.colors), len(body) / 1024))
    return stats


TEMPLATE = r'''--[[
STEAL A POTATO - @@TITLE@@
(@@FILE@@, generated by tools/gen_map.py)

Runs unattended: paste it into the command bar, or loadstring it. It builds Workspace.PotatoMap
(a Model; attribute Studs = true): the walled yard with its twelve bare 60 x 60 pens, the gate,
and the corridor of eighteen areas with their heroes, props, mounds, signs and zones.

@@NPARTS@@ Parts, every one a plain Roblox Part (Plastic with Inlet on all six faces; Neon and
SmoothPlastic ones Smooth). @@NTEMPL@@ pieces are written once and copied (@@NCOPIES@@ copies).

It replaces Workspace.PotatoMap only if one of my build scripts made it (attribute Studs, or
the part 1 map's Batch). If a PotatoMap made by anything else is there, it changes nothing and
says so: rename that one and run this again. Nothing else in the place is touched.
Safe to run twice.
]]

local TAG = "Steal a Potato: "
local MAP_NAME = "PotatoMap"

local COLORS = {@@COLORS@@}
local MATERIALS = {@@MATS@@}
local ROTS = {
	@@ROTS@@
}
local DATA = [[
@@DATA@@
]]

local ChangeHistoryService = game:GetService("ChangeHistoryService")

local old = workspace:FindFirstChild(MAP_NAME)
if old and old:GetAttribute("Studs") == nil and old:GetAttribute("Batch") == nil then
	warn(TAG .. "Workspace." .. MAP_NAME .. " is there and was not made by my build scripts. Nothing was changed: rename it and run this again.")
	return
end
pcall(function() ChangeHistoryService:SetWaypoint("Before building the Steal a Potato map") end)

local function rotation(i)
	local r = ROTS[i]
	return CFrame.new(0, 0, 0, r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9])
end
local function setSurfaces(p, kind)
	local s = kind == 3 and Enum.SurfaceType.Inlet or Enum.SurfaceType.Smooth
	p.TopSurface, p.BottomSurface = s, s
	p.FrontSurface, p.BackSurface, p.LeftSurface, p.RightSurface = s, s, s, s
end
local function setFlags(p, f)
	p.Anchored = f % 2 == 1
	p.CanCollide = math.floor(f / 2) % 2 == 1
	p.CanTouch = math.floor(f / 4) % 2 == 1
	p.CanQuery = math.floor(f / 8) % 2 == 1
	p.CastShadow = math.floor(f / 16) % 2 == 1
	p.Massless = math.floor(f / 32) % 2 == 1
end
local function color(i)
	local c = COLORS[i]
	return Color3.fromRGB(c[1], c[2], c[3])
end
local MAT = {}
for i, m in ipairs(MATERIALS) do MAT[i] = Enum.Material[m] end
local SHAPES = {B = Enum.PartType.Block, W = Enum.PartType.Wedge, C = Enum.PartType.Cylinder, S = Enum.PartType.Ball}

local function nm(s)
	return (string.gsub(string.gsub(s, "~", " "), "%^", "\n"))
end
local function fields(line)
	local f = {}
	for w in string.gmatch(line, "%S+") do f[#f + 1] = w end
	return f
end
local function attrValue(t, v, f)
	if t == "n" then return tonumber(v) end
	if t == "b" then return v == "1" end
	return nm(v)
end

local function makePart(parent, name, shape, size, cf, col, mat, tr, fl, surf)
	local p
	if shape == "W" then
		p = Instance.new("WedgePart")
	else
		p = Instance.new("Part")
		if shape ~= "B" then p.Shape = SHAPES[shape] end
	end
	p.Name = nm(name)
	p.Size = size
	p.CFrame = cf
	p.Color = color(col)
	p.Material = MAT[mat]
	p.Transparency = tr
	setFlags(p, fl)
	setSurfaces(p, surf)
	p.Parent = parent
	return p
end

-- 1. build everything in a loose model --------------------------------------------------------
local root = Instance.new("Model")
root.Name = MAP_NAME
local inst = {[0] = root}
local n = 0
local parts = 0
local templates, recolours = {}, {}
local cur, lastQ

for line in string.gmatch(DATA, "[^\n]+") do
	local f = fields(line)
	local k = f[1]
	if k == "B" then
		cur = {parts = {}, primary = 1}
		templates[tonumber(f[2])] = cur
	elseif k == "Q" then
		lastQ = {name = f[2], shape = f[3], sx = tonumber(f[4]), sy = tonumber(f[5]), sz = tonumber(f[6]),
			x = tonumber(f[7]), y = tonumber(f[8]), z = tonumber(f[9]), rot = tonumber(f[10]), col = tonumber(f[11]),
			mat = tonumber(f[12]), tr = tonumber(f[13]), fl = tonumber(f[14]), surf = tonumber(f[15]),
			big = f[16] == "1", attrs = {}}
		table.insert(cur.parts, lastQ)
	elseif k == "QA" then
		table.insert(lastQ.attrs, {f[3], attrValue(f[4], f[5], f)})
	elseif k == "QP" then
		cur.primary = tonumber(f[2])
	elseif k == "K" then
		local map = {}
		for i = 3, #f, 2 do map[tonumber(f[i])] = tonumber(f[i + 1]) end
		recolours[tonumber(f[2])] = map
	elseif k == "F" or k == "M" then
		local o = Instance.new(k == "M" and "Model" or "Folder")
		o.Name = nm(f[3])
		o.Parent = inst[tonumber(f[2])]
		n = n + 1
		inst[n] = o
	elseif k == "P" then
		local o = makePart(inst[tonumber(f[2])], f[3], f[4], Vector3.new(tonumber(f[5]), tonumber(f[6]), tonumber(f[7])),
			CFrame.new(tonumber(f[8]), tonumber(f[9]), tonumber(f[10])) * rotation(tonumber(f[11])),
			tonumber(f[12]), tonumber(f[13]), tonumber(f[14]), tonumber(f[15]), tonumber(f[16]))
		n = n + 1
		inst[n] = o
		parts = parts + 1
	elseif k == "X" then
		local o = Instance.new("Part")
		o.Name = nm(f[3])
		o.Size = Vector3.new(tonumber(f[4]), tonumber(f[5]), tonumber(f[6]))
		o.CFrame = CFrame.new(tonumber(f[7]), tonumber(f[8]), tonumber(f[9])) * rotation(tonumber(f[10]))
		o.Anchored, o.CanCollide, o.CanTouch, o.CanQuery, o.CastShadow = true, false, false, false, false
		o.Transparency = 1
		setSurfaces(o, 0)
		o.Parent = inst[tonumber(f[2])]
		n = n + 1
		inst[n] = o
	elseif k == "I" then
		local t = templates[tonumber(f[4])]
		local base = CFrame.new(tonumber(f[5]), tonumber(f[6]), tonumber(f[7])) * rotation(tonumber(f[8]))
		local s = tonumber(f[9])
		local map = recolours[tonumber(f[10])]
		local solid = f[11] == "1"
		local m = Instance.new("Model")
		m.Name = nm(f[3])
		local made = {}
		for i, q in ipairs(t.parts) do
			local fl = q.fl
			if solid and q.big then
				if math.floor(fl / 2) % 2 == 0 then fl = fl + 2 end
				if math.floor(fl / 8) % 2 == 0 then fl = fl + 8 end
			end
			local size = Vector3.new(math.max(q.sx * s, 0.05), math.max(q.sy * s, 0.05), math.max(q.sz * s, 0.05))
			if math.floor(fl / 16) % 2 == 1 and math.max(size.X, size.Y, size.Z) < 2.5 then fl = fl - 16 end
			local col = (map and map[q.col]) or q.col
			local p = makePart(m, q.name, q.shape, size, base * CFrame.new(q.x * s, q.y * s, q.z * s) * rotation(q.rot),
				col, q.mat, q.tr, fl, q.surf)
			for _, a in ipairs(q.attrs) do p:SetAttribute(a[1], a[2]) end
			made[i] = p
			parts = parts + 1
		end
		local prim = made[t.primary]
		m.PrimaryPart = prim
		prim.PivotOffset = prim.CFrame:Inverse() * base
		m.Parent = inst[tonumber(f[2])]
		n = n + 1
		inst[n] = m
	elseif k == "A" then
		local o = Instance.new("Attachment")
		o.Name = nm(f[3])
		o.CFrame = CFrame.new(tonumber(f[4]), tonumber(f[5]), tonumber(f[6])) * rotation(tonumber(f[7]))
		o.Parent = inst[tonumber(f[2])]
		n = n + 1
		inst[n] = o
	elseif k == "R" then
		inst[tonumber(f[2])].PrimaryPart = inst[tonumber(f[3])]
	elseif k == "V" then
		inst[tonumber(f[2])].PivotOffset = CFrame.new(tonumber(f[3]), tonumber(f[4]), tonumber(f[5])) * rotation(tonumber(f[6]))
	elseif k == "T" then
		inst[tonumber(f[2])]:SetAttribute(f[3], attrValue(f[4], f[5], f))
	end
end

-- 2. swap it in ---------------------------------------------------------------------------------
root:SetAttribute("Studs", true)
local replaced = 0
for _, o in ipairs(workspace:GetChildren()) do
	if o.Name == MAP_NAME and (o:GetAttribute("Studs") ~= nil or o:GetAttribute("Batch") ~= nil) then
		o:Destroy()
		replaced = replaced + 1
	end
end
root.Parent = workspace

pcall(function() ChangeHistoryService:SetWaypoint("Built the Steal a Potato map") end)
print(TAG .. string.format("built Workspace.%s: %d parts%s", MAP_NAME, parts,
	replaced > 0 and " (replaced the one an earlier run made)" or ""))
'''

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
