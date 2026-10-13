"""Write one unattended Studio build script for one piece of the Steal a Potato kit (bricks only).

    python tools/gen_kit.py <piece.json> <Build<Piece>.lua> "<title>" [Folder=anims.json ...]

piece.json comes from blender/build_kit.py (spslib.to_json of a Scene whose root stands for
ReplicatedStorage.PotatoKit). Folders marked as containers (PotatoKit itself, Potatoes,
PotatoAnimations, Fences, Props, ...) are merged into the live ones: each item in them (a potato,
a clip, a fence tier) replaces whatever has that name there, and nothing else is touched.
`Folder=anims.json` puts the KeyframeSequences of anims.json (rbxtool JSON) into that folder.

Every Plastic part gets Inlet on all six faces; Neon and SmoothPlastic parts are Smooth all round.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from gen_build import FLAG_BITS, SHAPE, Tables, _mat_quat, flags, lua_name, num, pos  # noqa: E402,F401

SURF = {"smooth": 0, "studs": 1, "wedge": 2, "inlet": 3}


def items_of(nodes):
    """Dotted paths of everything the script places (the non-container children of containers)."""
    by = {n["i"]: n for n in nodes}
    out = []
    for n in nodes:
        if n["parent"] is None:
            continue
        par = by[n["parent"]]
        if (par["parent"] is None or par.get("container")) and not n.get("container"):
            path, q = [n["name"]], par
            while q is not None:
                path.append(q["name"])
                q = by.get(q["parent"]) if q["parent"] is not None else None
            out.append(".".join(reversed(path)))
    return out


def anim_records(ks_list, fpar, count, lines):
    nkey = 0
    for ks in ks_list:
        count += 1
        me = count
        pr = ks["props"]
        lines.append("S %d %s %d %d" % (fpar, lua_name(ks["name"]), 1 if pr["Loop"]["Bool"] else 0,
                                         pr["Priority"]["Enum"]))
        for kf in ks["children"]:
            count += 1
            kme = count
            nkey += 1
            lines.append("E %d %s" % (me, num(kf["props"]["Time"]["Float32"], 5)))

            def pose(node, parent):
                nonlocal count
                count += 1
                if node["class"] == "KeyframeMarker":
                    lines.append("Z %d %s" % (parent, lua_name(node["name"])))
                    return
                pme = count
                c = node["props"]["CFrame"]["CFrame"]
                q = _mat_quat(c["orientation"])
                lines.append("O %d %s %s %s %s" % (parent, lua_name(node["name"]),
                                                    " ".join(num(v, 4) for v in c["position"]),
                                                    " ".join(num(v, 5) for v in q),
                                                    num(node["props"]["Weight"]["Float32"], 3)))
                for ch in node["children"]:
                    pose(ch, pme)
            for ch in kf["children"]:
                pose(ch, kme)
    return count, nkey


def main(src, dst, title, anims=None):
    data = json.load(open(src))
    nodes = data["nodes"]
    assert not data.get("meshes"), "bricks only: this piece has meshes"
    tb = Tables()
    idx = {}
    lines, joints, post = [], [], []
    count = 0
    stats = {"Part": 0, "Neon": 0, "Inlet": 0}

    def new(n):
        nonlocal count
        count += 1
        idx[n["i"]] = count
        return count

    for n in nodes:
        k = n["kind"]
        if n["parent"] is None:
            idx[n["i"]] = 0
            continue
        par = idx[n["parent"]]
        name = lua_name(n["name"])
        if k == "Folder" and n.get("container"):
            me = new(n)
            lines.append("C %d %s" % (par, name))
        elif k in ("Folder", "Model"):
            me = new(n)
            lines.append("%s %d %s" % ("F" if k == "Folder" else "M", par, name))
            if n.get("primary") is not None:
                post.append(("R", me, n["primary"]))
            if n.get("wpivot") is not None:
                post.append(("U", me, pos(n["wpivot"]), tb.rot(n["wpivot"][1])))
        elif k == "Part":
            me = new(n)
            stats["Part"] += 1
            mat = n["material"]
            surf = n["surfaces"]
            if mat == "Plastic":
                assert surf == "inlet", "%s: Plastic parts are Inlet all round" % n["name"]
                stats["Inlet"] += 1
            else:
                assert surf == "smooth", "%s: %s parts are Smooth all round" % (n["name"], mat)
            stats["Neon"] += mat == "Neon"
            sx, sy, sz = n["size"]
            lines.append("P %d %s %s %s %s %s %s %d %d %d %s %d %d" % (
                par, name, SHAPE[n["shape"]], num(sx), num(sy), num(sz), pos(n["cf"]), tb.rot(n["cf"][1]),
                tb.color(n["color"]), tb.mat(mat), num(n["transparency"]), flags(n, {}), SURF[surf]))
        elif k == "Attachment":
            me = new(n)
            lines.append("A %d %s %s %d" % (par, name, pos(n["cf"]), tb.rot(n["cf"][1])))
        elif k == "Light":
            new(n)
            lines.append("L %d %s %s %d %s %s %d %s %s %d" % (
                par, n["cls"], name, tb.color(n["color"]), num(n["brightness"]), num(n["range"]),
                1 if n["shadows"] else 0, num(n["angle"]) if n.get("angle") is not None else "-",
                n.get("face") or "-", 1 if n.get("enabled", True) else 0))
        elif k == "AnimationController":
            new(n)
            lines.append("G %d %s" % (par, name))
        elif k == "Animator":
            new(n)
            lines.append("N %d %s" % (par, name))
        elif k == "Weld":
            joints.append(("W", n, par, name))
        elif k == "Motor":
            joints.append(("J", n, par, name))
        else:
            raise SystemExit("gen_kit: unexpected %s %s" % (k, n["name"]))
        if k == "Part" and n.get("pivot") is not None:
            post.append(("V", idx[n["i"]], pos(n["pivot"]), tb.rot(n["pivot"][1])))
        for ak, av in (n.get("attrs") or {}).items():
            post.append(("T", idx[n["i"]], ak, av))
    for kind, n, par, name in joints:
        new(n)
        if kind == "W":
            lines.append("W %d %d %s %d" % (idx[n["part0"]], idx[n["part1"]], name, par))
        else:
            lines.append("J %d %d %s %s %d %d" % (idx[n["part0"]], idx[n["part1"]], name, pos(n["hinge"]),
                                                  tb.rot(n["hinge"][1]), par))
    nkey = 0
    for folder_name, path in (anims or {}).items():
        f = [n for n in nodes if n["kind"] == "Folder" and n["name"] == folder_name]
        assert len(f) == 1, "no folder %s for %s" % (folder_name, path)
        count, nk = anim_records(json.load(open(path))[0]["children"], idx[f[0]["i"]], count, lines)
        nkey += nk
    for rec in post:
        if rec[0] == "R":
            lines.append("R %d %d" % (rec[1], idx[rec[2]]))
        elif rec[0] in ("V", "U"):
            lines.append("%s %d %s %d" % rec)
        elif rec[0] == "T":
            _, me, key, val = rec
            if isinstance(val, bool):
                lines.append("T %d %s b %s" % (me, key, "1" if val else "0"))
            elif isinstance(val, (int, float)):
                lines.append("T %d %s n %s" % (me, key, num(val, 4)))
            elif isinstance(val, (list, tuple)) and len(val) == 3:
                lines.append("T %d %s v %s %s %s" % (me, key, num(val[0], 4), num(val[1], 4), num(val[2], 4)))
            else:
                lines.append("T %d %s s %s" % (me, key, lua_name(str(val))))

    items = items_of(nodes)
    colors = ", ".join("{%d, %d, %d}" % c for c in tb.colors)
    mats = ", ".join('"%s"' % m for m in tb.mats)
    rots = ",\n\t".join("{%s}" % ", ".join(num(v, 5) for v in r) for r in tb.rots)
    body = TEMPLATE
    listing = "\n".join("    " + it for it in items)
    for key, val in (("@@TITLE@@", title), ("@@ITEMS@@", listing), ("@@NPARTS@@", str(stats["Part"])),
                     ("@@NKEY@@", str(nkey)), ("@@COLORS@@", colors), ("@@MATS@@", mats), ("@@ROTS@@", rots),
                     ("@@FILE@@", os.path.basename(dst))):
        body = body.replace(key, val)
    body = body.replace("@@DATA@@", "\n".join(lines))
    assert "]]" not in "\n".join(lines)
    assert "@@" not in body
    with open(dst, "w") as f:
        f.write(body)
    print("wrote %s: %d records, %d parts (%d Inlet Plastic, %d Neon), %d keyframes, %d rotations, %d colours, "
          "%.0f KB" % (dst, len(lines), stats["Part"], stats["Inlet"], stats["Neon"], nkey, len(tb.rots),
                       len(tb.colors), len(body) / 1024))
    return items


TEMPLATE = r'''--[[
STEAL A POTATO - @@TITLE@@
(@@FILE@@, generated by tools/gen_kit.py)

Runs unattended: paste it into the command bar, or loadstring it. It builds, inside
ReplicatedStorage.PotatoKit (made if missing; attribute Studs = true):

@@ITEMS@@

@@NPARTS@@ Parts, every one a plain Roblox Part (Plastic with Inlet on all six faces; Neon and
SmoothPlastic ones Smooth), plus @@NKEY@@ keyframes. Each item above replaces anything with the
same name in the same folder (what an earlier run built); nothing else is touched.
Safe to run twice.
]]

local TAG = "Steal a Potato: "
local KIT_NAME = "PotatoKit"

local COLORS = {@@COLORS@@}
local MATERIALS = {@@MATS@@}
local ROTS = {
	@@ROTS@@
}
local DATA = [[
@@DATA@@
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ChangeHistoryService = game:GetService("ChangeHistoryService")

local live = ReplicatedStorage:FindFirstChild(KIT_NAME)
if live and not live:IsA("Folder") then
	warn(TAG .. "ReplicatedStorage." .. KIT_NAME .. " is a " .. live.ClassName .. ", not a Folder. Nothing was changed.")
	return
end
pcall(function() ChangeHistoryService:SetWaypoint("Before building @@TITLE@@") end)

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
local PRIORITY = {[0] = Enum.AnimationPriority.Idle, [1] = Enum.AnimationPriority.Movement,
	[2] = Enum.AnimationPriority.Action}
local MAT = {}
for i, m in ipairs(MATERIALS) do MAT[i] = Enum.Material[m] end

-- 1. build everything in a loose folder ------------------------------------------------------
local root = Instance.new("Folder")
root.Name = KIT_NAME
local inst = {[0] = root}
local container = {[root] = true}
local n = 0
local parts = 0

local function nm(s)
	return (string.gsub(string.gsub(s, "~", " "), "%^", "\n"))
end
local function fields(line)
	local f = {}
	for w in string.gmatch(line, "%S+") do f[#f + 1] = w end
	return f
end
local function cfAt(f, i)
	return CFrame.new(tonumber(f[i]), tonumber(f[i + 1]), tonumber(f[i + 2])) * rotation(tonumber(f[i + 3]))
end
local function add(o, f)
	o.Parent = inst[tonumber(f[2])]
	n = n + 1
	inst[n] = o
	return o
end

for line in string.gmatch(DATA, "[^\n]+") do
	local f = fields(line)
	local k = f[1]
	if k == "C" or k == "F" or k == "M" then
		local o = Instance.new(k == "M" and "Model" or "Folder")
		o.Name = nm(f[3])
		add(o, f)
		if k == "C" then container[o] = true end
	elseif k == "P" then
		local shape = f[4]
		local p
		if shape == "W" then
			p = Instance.new("WedgePart")
		else
			p = Instance.new("Part")
			p.Shape = (shape == "C" and Enum.PartType.Cylinder) or (shape == "S" and Enum.PartType.Ball)
				or Enum.PartType.Block
		end
		p.Name = nm(f[3])
		p.Size = Vector3.new(tonumber(f[5]), tonumber(f[6]), tonumber(f[7]))
		p.CFrame = cfAt(f, 8)
		p.Color = color(tonumber(f[12]))
		p.Material = MAT[tonumber(f[13])]
		p.Transparency = tonumber(f[14])
		p.Reflectance = 0
		setFlags(p, tonumber(f[15]))
		setSurfaces(p, tonumber(f[16]))
		add(p, f)
		parts = parts + 1
	elseif k == "A" then
		local par = inst[tonumber(f[2])]
		local a = Instance.new("Attachment")
		a.Name = nm(f[3])
		a.CFrame = par.CFrame:Inverse() * cfAt(f, 4)
		add(a, f)
	elseif k == "L" then
		local l = Instance.new(f[3])
		l.Name = nm(f[4])
		l.Color = color(tonumber(f[5]))
		l.Brightness = tonumber(f[6])
		l.Range = tonumber(f[7])
		l.Shadows = f[8] == "1"
		if f[9] ~= "-" then l.Angle = tonumber(f[9]) end
		if f[10] ~= "-" then l.Face = Enum.NormalId[f[10]] end
		l.Enabled = f[11] ~= "0"
		add(l, f)
	elseif k == "G" or k == "N" then
		local a = Instance.new(k == "G" and "AnimationController" or "Animator")
		a.Name = nm(f[3])
		add(a, f)
	elseif k == "S" then
		local ks = Instance.new("KeyframeSequence")
		ks.Name = nm(f[3])
		ks.Loop = f[4] == "1"
		ks.Priority = PRIORITY[tonumber(f[5])] or Enum.AnimationPriority.Action
		add(ks, f)
	elseif k == "E" then
		local kf = Instance.new("Keyframe")
		kf.Time = tonumber(f[3])
		add(kf, f)
	elseif k == "O" then
		local p = Instance.new("Pose")
		p.Name = nm(f[3])
		p.CFrame = CFrame.new(tonumber(f[4]), tonumber(f[5]), tonumber(f[6]), tonumber(f[7]), tonumber(f[8]),
			tonumber(f[9]), tonumber(f[10]))
		p.Weight = tonumber(f[11])
		p.EasingStyle = Enum.PoseEasingStyle.Linear
		p.EasingDirection = Enum.PoseEasingDirection.In
		add(p, f)
	elseif k == "Z" then
		local mk = Instance.new("KeyframeMarker")
		mk.Name = nm(f[3])
		mk.Value = ""
		add(mk, f)
	elseif k == "W" then
		-- joints come after every part: W part0 part1 name parent
		local w = Instance.new("WeldConstraint")
		w.Name = nm(f[4])
		w.Part0 = inst[tonumber(f[2])]
		w.Part1 = inst[tonumber(f[3])]
		w.Parent = inst[tonumber(f[5])]
		n = n + 1
		inst[n] = w
	elseif k == "J" then
		local p0, p1 = inst[tonumber(f[2])], inst[tonumber(f[3])]
		local hinge = cfAt(f, 5)
		local j = Instance.new("Motor6D")
		j.Name = nm(f[4])
		j.Part0 = p0
		j.Part1 = p1
		j.C0 = p0.CFrame:Inverse() * hinge
		j.C1 = p1.CFrame:Inverse() * hinge
		j.Parent = inst[tonumber(f[9])]
		n = n + 1
		inst[n] = j
	elseif k == "V" then
		inst[tonumber(f[2])].PivotOffset = cfAt(f, 3)
	elseif k == "U" then
		inst[tonumber(f[2])].WorldPivot = cfAt(f, 3)
	elseif k == "T" then
		local o = inst[tonumber(f[2])]
		local t, v = f[4], f[5]
		if t == "n" then
			o:SetAttribute(f[3], tonumber(v))
		elseif t == "b" then
			o:SetAttribute(f[3], v == "1")
		elseif t == "v" then
			o:SetAttribute(f[3], Vector3.new(tonumber(f[5]), tonumber(f[6]), tonumber(f[7])))
		else
			o:SetAttribute(f[3], nm(v))
		end
	elseif k == "R" then
		inst[tonumber(f[2])].PrimaryPart = inst[tonumber(f[3])]
	end
end

-- 2. put each item in its place, replacing the one an earlier run made -----------------------
if not live then
	live = Instance.new("Folder")
	live.Name = KIT_NAME
	live.Parent = ReplicatedStorage
end
live:SetAttribute("Studs", true)
local placed, replaced, skipped = 0, 0, {}
local function place(src, dst)
	for _, c in ipairs(src:GetChildren()) do
		if container[c] then
			local d = dst:FindFirstChild(c.Name)
			if d and not d:IsA("Folder") then
				table.insert(skipped, d:GetFullName())
			else
				if not d then
					d = Instance.new("Folder")
					d.Name = c.Name
					d.Parent = dst
				end
				place(c, d)
			end
		else
			for _, old in ipairs(dst:GetChildren()) do
				if old.Name == c.Name then
					old:Destroy()
					replaced = replaced + 1
				end
			end
			c.Parent = dst
			placed = placed + 1
		end
	end
end
place(root, live)
root:Destroy()
for _, s in ipairs(skipped) do
	warn(TAG .. s .. " is not a Folder, so nothing was put in it.")
end

pcall(function() ChangeHistoryService:SetWaypoint("Built @@TITLE@@") end)
print(TAG .. string.format("built @@TITLE@@ in ReplicatedStorage.%s: %d items (%d replaced), %d parts", KIT_NAME,
	placed, replaced, parts))
'''

if __name__ == "__main__":
    extra = dict(a.split("=", 1) for a in sys.argv[4:] if "=" in a)
    main(sys.argv[1], sys.argv[2], sys.argv[3], extra)
