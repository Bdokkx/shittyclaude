"""Write a self-contained Studio build script for the Scary Pizza Shack.

    python tools/gen_build.py out/map.json out/BuildPizzaShack.lua                 # batch 1: the map
    python tools/gen_build.py out/assets.json out/BuildPizzaShackAssets.lua assets # batch 2: assets

The JSON comes from blender/build_map.py or blender/build_assets.py. The script runs
unattended (loadstring from the command-bar context) after the batch's FBX has been
uploaded and loaded with InsertService:LoadAsset somewhere under Workspace.
"""
import json
import sys

CONFIGS = {
    "map": dict(root="PizzaShack", cache="PizzaShackMeshes", axis="FV_Axis", fbx="ScaryPizzaShack_Batch1.fbx",
                batch=1, title="batch 1 map builder", what="the Pizza Shack",
                folders="Shack, Outside, Stations, Items, Markers"),
    "remake": dict(root="PizzaShack", cache="PizzaShackMeshes", axis="FV_Axis", fbx="ScaryPizzaShack_Remake.fbx",
                   batch=1, title="remade map builder", what="the remade Pizza Shack",
                   folders="Shack, Outside, Stations, Items, Markers"),
    "assets": dict(root="PizzaShackAssets", cache="PizzaShackAssetMeshes", axis="PSA_Axis",
                   fbx="ScaryPizzaShack_Batch2.fbx", batch=2, title="batch 2 assets builder",
                   what="the Pizza Shack assets",
                   folders="one Model per asset: CustomerKit, Passenger, Watcher, Inspector, InspectorHole, "
                           "InspectorCar, DeliveryTruck, Van, Plushies, Uniforms"),
}

FLAG_BITS = (("anchored", 1), ("collide", 2), ("touch", 4), ("query", 8), ("shadow", 16), ("massless", 32))
SHAPE = {"Block": "B", "Wedge": "W", "Cylinder": "C", "Ball": "S"}
SURF = {"smooth": 0, "studs": 1, "wedge": 2}


def num(v, nd=3):
    s = ("%." + str(nd) + "f") % v
    s = s.rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def flags(d, defaults):
    f = 0
    for k, bit in FLAG_BITS:
        if d.get(k, defaults.get(k, False)):
            f |= bit
    return f


class Tables:
    def __init__(self):
        self.colors, self.mats, self.rots, self.meshes = {}, {}, {}, {}
        self.rot(((1, 0, 0), (0, 1, 0), (0, 0, 1)))

    def color(self, c):
        return self.colors.setdefault(tuple(c), len(self.colors) + 1)

    def mat(self, m):
        return self.mats.setdefault(m, len(self.mats) + 1)

    def rot(self, R):
        key = tuple(round(float(v), 5) + 0.0 for row in R for v in row)
        return self.rots.setdefault(key, len(self.rots) + 1)

    def mesh(self, name):
        return self.meshes.setdefault(name, len(self.meshes) + 1)


def pos(cf):
    return " ".join(num(v) for v in cf[0])


def lua_name(name):
    """Names and string attributes go into a whitespace-separated record: spaces travel as
    '~', line breaks (a board's text on several lines) as '^'."""
    assert "~" not in name and "^" not in name, name
    return name.replace(" ", "~").replace("\n", "^")


def main(src, dst, config="map"):
    cfg = CONFIGS[config]
    data = json.load(open(src))
    nodes = data["nodes"]
    tb = Tables()
    idx = {}            # json index -> Lua instance number (root = 0)
    lines = []
    joints = []         # welds and motors, written once every part exists
    post = []           # records that refer to instances made later (primary parts)
    count = 0
    stats = {"Part": 0, "MeshPart": 0, "Marker": 0}

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
        if k in ("Folder", "Model", "Accessory"):
            me = new(n)
            lines.append("%s %d %s" % ({"Folder": "F", "Model": "M", "Accessory": "Y"}[k], par, name))
            if n.get("primary") is not None:
                post.append(("R", me, n["primary"]))
            for ak, av in (n.get("attrs") or {}).items():
                post.append(("T", me, ak, av))
        elif k == "Part":
            me = new(n)
            stats["Part"] += 1
            sx, sy, sz = n["size"]
            lines.append("P %d %s %s %s %s %s %s %d %d %d %s %d %d" % (
                par, name, SHAPE[n["shape"]], num(sx), num(sy), num(sz), pos(n["cf"]), tb.rot(n["cf"][1]),
                tb.color(n["color"]), tb.mat(n["material"]), num(n["transparency"]),
                flags(n, {}), SURF[n["surfaces"]]))
        elif k == "Marker":
            me = new(n)
            stats["Marker"] += 1
            f = flags({"anchored": n.get("anchored", True), "massless": n.get("massless", False)}, {})
            lines.append("K %d %s %s %d %d" % (par, name, pos(n["cf"]), tb.rot(n["cf"][1]), f))
            for ak, av in (n.get("attrs") or {}).items():
                post.append(("T", me, ak, av))
        elif k == "MeshPart":
            me = new(n)
            stats["MeshPart"] += 1
            lines.append("X %d %s %d %s %d %d %d %s %d" % (
                par, name, tb.mesh(n["mesh"]), pos(n["cf"]), tb.rot(n["cf"][1]), tb.color(n["color"]),
                tb.mat(n["material"]), num(n["transparency"]), flags(n, {})))
        elif k == "Attachment":
            me = new(n)
            lines.append("A %d %s %s %d" % (par, name, pos(n["cf"]), tb.rot(n["cf"][1])))
            for ak, av in (n.get("attrs") or {}).items():
                post.append(("T", me, ak, av))
        elif k == "Light":
            new(n)
            lines.append("L %d %s %s %d %s %s %d %s %s %d" % (
                par, n["cls"], name, tb.color(n["color"]), num(n["brightness"]), num(n["range"]),
                1 if n["shadows"] else 0, num(n["angle"]) if n.get("angle") is not None else "-",
                n.get("face") or "-", 1 if n.get("enabled", True) else 0))
        elif k == "Humanoid":
            new(n)
            lines.append("H %d %s %s" % (par, name, n["rig"]))
        elif k == "Animator":
            new(n)
            lines.append("N %d %s" % (par, name))
        elif k == "SpecialMesh":
            new(n)
            lines.append("Q %d %s %s %s" % (par, name, n["mesh_type"], " ".join(num(v, 4) for v in n["scale"])))
        elif k == "Weld":
            joints.append(("W", n, par, name))      # numbered after every other instance
        elif k == "Motor":
            joints.append(("J", n, par, name))
        else:
            raise SystemExit("unknown kind " + k)
        if k in ("Part", "MeshPart") and n.get("pivot") is not None:
            pv = n["pivot"]
            post.append(("V", idx[n["i"]], pos(pv), tb.rot(pv[1])))
        if k in ("Part", "MeshPart"):
            for ak, av in (n.get("attrs") or {}).items():
                post.append(("T", idx[n["i"]], ak, av))
    for kind, n, par, name in joints:
        new(n)
        if kind == "W":
            lines.append("W %d %d %s %d" % (idx[n["part0"]], idx[n["part1"]], name, par))
        else:
            lines.append("J %d %d %s %s %d %d" % (idx[n["part0"]], idx[n["part1"]], name, pos(n["hinge"]),
                                                  tb.rot(n["hinge"][1]), par))
    for rec in post:
        if rec[0] == "R":
            lines.append("R %d %d" % (rec[1], idx[rec[2]]))
        elif rec[0] == "V":
            lines.append("V %d %s %d" % rec[1:])
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

    colors = ", ".join("{%d, %d, %d}" % c for c in tb.colors)
    mats = ", ".join('"%s"' % m for m in tb.mats)
    rots = ",\n\t".join("{%s}" % ", ".join(num(v, 5) for v in r) for r in tb.rots)
    meshes = ",\n\t".join('"%s"' % m for m in tb.meshes)
    body = TEMPLATE
    for key, val in (("@@TITLE@@", cfg["title"]), ("@@FBX@@", cfg["fbx"]), ("@@ROOT@@", cfg["root"]),
                     ("@@CACHE@@", cfg["cache"]), ("@@AXIS@@", cfg["axis"]), ("@@WHAT@@", cfg["what"]),
                     ("@@FOLDERS@@", cfg["folders"]), ("@@BATCH@@", str(cfg["batch"]))):
        body = body.replace(key, val)
    body = body.replace("@@COLORS@@", colors).replace("@@MATS@@", mats).replace("@@ROTS@@", rots)
    body = body.replace("@@MESHES@@", meshes).replace("@@DATA@@", "\n".join(lines))
    body = body.replace("@@NPARTS@@", str(stats["Part"])).replace("@@NMESH@@", str(stats["MeshPart"]))
    marks = (", %d markers" % stats["Marker"]) if stats["Marker"] else ""
    body = body.replace("@@MARKS@@", marks).replace("@@NUNIQUE@@", str(len(tb.meshes)))
    assert "]]" not in "\n".join(lines)
    assert "@@" not in body
    with open(dst, "w") as f:
        f.write(body)
    print("wrote %s: %d records, %d parts, %d mesh parts (%d meshes), %d markers, %d rotations, %d colours, "
          "%.0f KB" % (dst, len(lines), stats["Part"], stats["MeshPart"], len(tb.meshes), stats["Marker"],
                       len(tb.rots), len(tb.colors), len(body) / 1024))


TEMPLATE = r'''--[[
SCARY PIZZA SHACK - @@TITLE@@ (generated by tools/gen_build.py)

Runs unattended. Upload @@FBX@@ with Open Cloud, load it with
InsertService:LoadAsset and parent the result anywhere under Workspace, then run
this file with loadstring from the command-bar context. It:

  1. finds the imported MeshParts by name anywhere under Workspace (and in
     ServerStorage / ReplicatedStorage), and undoes any scale or turn the
     importer applied, using the four @@AXIS@@ marker cubes in the file;
  2. keeps a clean copy of every mesh in ServerStorage.@@CACHE@@, so the
     script can be run again later even without a fresh import;
  3. builds Workspace.@@ROOT@@ (@@FOLDERS@@):
     @@NPARTS@@ Parts, @@NMESH@@ MeshParts (@@NUNIQUE@@ different meshes)@@MARKS@@;
  4. replaces the @@ROOT@@ an earlier run built, and deletes the import
     container and the marker cubes.

Safe to run twice. If the meshes can't be found it changes nothing and warns.
]]

local TAG = "@@ROOT@@: "
local MARKER_STEP = 4
local ROOT_NAME = "@@ROOT@@"
local CACHE_NAME = "@@CACHE@@"
local AXIS = "@@AXIS@@"

local COLORS = {@@COLORS@@}
local MATERIALS = {@@MATS@@}
local ROTS = {
	@@ROTS@@
}
local MESHES = {
	@@MESHES@@
}
local DATA = [[
@@DATA@@
]]

local ServerStorage = game:GetService("ServerStorage")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ChangeHistoryService = game:GetService("ChangeHistoryService")

local function norm(s)
	return (string.lower(s):gsub("[^%w]", ""))
end

local function rotation(i)
	local r = ROTS[i]
	return CFrame.new(0, 0, 0, r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9])
end

-- 1. find the imported meshes ----------------------------------------------------------
local oldRoot = workspace:FindFirstChild(ROOT_NAME)
local cache = ServerStorage:FindFirstChild(CACHE_NAME)
local wanted, wantedNorm = {}, {}
for i, name in ipairs(MESHES) do
	wanted[name] = i
	wantedNorm[norm(name)] = i
end
for _, name in ipairs({AXIS .. "O", AXIS .. "X", AXIS .. "Y", AXIS .. "Z"}) do
	wanted[name] = 0
	wantedNorm[norm(name)] = 0
end

local found, foundNorm = {}, {}
local function inOurs(d)
	return (oldRoot and d:IsDescendantOf(oldRoot)) or (cache and d:IsDescendantOf(cache))
end
-- the import is the container holding the axis cubes: look for the meshes in there first, so a
-- part elsewhere in the game that happens to share a mesh's name is never taken for it
local searchRoots = {workspace, ServerStorage, ReplicatedStorage}
for _, root in ipairs({workspace, ServerStorage, ReplicatedStorage}) do
	for _, d in ipairs(root:GetDescendants()) do
		if d:IsA("MeshPart") and not inOurs(d) and norm(d.Name) == norm(AXIS .. "O") then
			local top = d
			while top.Parent and top.Parent ~= workspace and top.Parent ~= ServerStorage
				and top.Parent ~= ReplicatedStorage and top.Parent ~= game do
				top = top.Parent
			end
			searchRoots = {top}
			break
		end
	end
	if #searchRoots == 1 then break end
end
for _, root in ipairs(searchRoots) do
	for _, d in ipairs(root:GetDescendants()) do
		if d:IsA("MeshPart") and not inOurs(d) then
			if wanted[d.Name] ~= nil and found[d.Name] == nil then
				found[d.Name] = d
			elseif wantedNorm[norm(d.Name)] ~= nil and foundNorm[norm(d.Name)] == nil then
				foundNorm[norm(d.Name)] = d
			end
		end
	end
end
local function imported(name)
	return found[name] or foundNorm[norm(name)]
end

local fresh = imported(AXIS .. "O") ~= nil
local missing = {}
if fresh then
	for _, name in ipairs({AXIS .. "X", AXIS .. "Y", AXIS .. "Z"}) do
		if not imported(name) then table.insert(missing, name) end
	end
	for _, name in ipairs(MESHES) do
		if not imported(name) then table.insert(missing, name) end
	end
	if #missing > 0 then
		warn(TAG .. #missing .. " imported meshes are missing (first: " .. missing[1] .. "). Nothing was changed.")
		return
	end
else
	if not cache then
		warn(TAG .. "no imported meshes found under Workspace and no ServerStorage." .. CACHE_NAME
			.. " from an earlier run. Load @@FBX@@ first. Nothing was changed.")
		return
	end
	for _, name in ipairs(MESHES) do
		if not cache:FindFirstChild(name) then table.insert(missing, name) end
	end
	if #missing > 0 then
		warn(TAG .. "ServerStorage." .. CACHE_NAME .. " is incomplete (first missing: " .. missing[1]
			.. "). Load the FBX again. Nothing was changed.")
		return
	end
end

pcall(function() ChangeHistoryService:SetWaypoint("Before building @@WHAT@@") end)

-- 2. the clean mesh cache -------------------------------------------------------------------
local containers = {}
if fresh then
	local o = imported(AXIS .. "O").Position
	local ex = imported(AXIS .. "X").Position - o
	local ey = imported(AXIS .. "Y").Position - o
	local ez = imported(AXIS .. "Z").Position - o
	local scale = (ex.Magnitude + ey.Magnitude + ez.Magnitude) / (3 * MARKER_STEP)
	if ex.Unit:Cross(ey.Unit):Dot(ez.Unit) < 0.9 or scale <= 0 then
		warn(TAG .. "the import looks mirrored or collapsed; re-upload the FBX with default settings. Nothing was changed.")
		return
	end
	local fromFile = CFrame.fromMatrix(Vector3.zero, ex.Unit, ey.Unit, ez.Unit):Inverse()
	local newCache = Instance.new("Folder")
	newCache.Name = CACHE_NAME
	for i, name in ipairs(MESHES) do
		local src = imported(name)
		local turn = fromFile * (src.CFrame - src.CFrame.Position)
		local m = src:Clone()
		for _, child in ipairs(m:GetChildren()) do
			child:Destroy() -- importer extras (SurfaceAppearance, attachments, welds)
		end
		m.Name = name
		m.Size = src.Size / scale
		m.CFrame = CFrame.new(0, -10000, 0) * turn
		m.PivotOffset = CFrame.new() -- the importer leaves pivots far away; the real hinges come later
		m.Anchored = true
		m.CanCollide = false
		m.CanTouch = false
		m.CanQuery = false
		m.Parent = newCache
	end
	-- remember the import this run used (only those instances: other parts that happen to share
	-- a mesh's name elsewhere in the game are left alone), so it can be removed afterwards
	for _, name in ipairs(MESHES) do
		containers[imported(name)] = true
	end
	for _, name in ipairs({AXIS .. "O", AXIS .. "X", AXIS .. "Y", AXIS .. "Z"}) do
		containers[imported(name)] = true
	end
	if cache then cache:Destroy() end
	cache = newCache
	cache.Parent = ServerStorage
end

local SOURCES, TURNS = {}, {}
for i, name in ipairs(MESHES) do
	local m = cache:FindFirstChild(name)
	SOURCES[i] = m
	TURNS[i] = m.CFrame - m.CFrame.Position
end

-- 3. build -------------------------------------------------------------------------------------
local SURFACES = {Enum.SurfaceType.Smooth, Enum.SurfaceType.Studs, Enum.SurfaceType.Inlet}
local function setSurfaces(p, kind)
	local s = Enum.SurfaceType.Smooth
	p.TopSurface, p.BottomSurface = s, s
	p.FrontSurface, p.BackSurface, p.LeftSurface, p.RightSurface = s, s, s, s
	if kind == 1 then
		p.TopSurface = Enum.SurfaceType.Studs
		p.BottomSurface = Enum.SurfaceType.Inlet
	elseif kind == 2 then
		p.BottomSurface = Enum.SurfaceType.Inlet
	end
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

local root = Instance.new("Folder")
root.Name = ROOT_NAME
local inst = {[0] = root}
local meshOf = {}           -- instance -> mesh index (for pivot offsets)
local n = 0
local counts = {parts = 0, meshes = 0, markers = 0}

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

for line in string.gmatch(DATA, "[^\n]+") do
	local f = fields(line)
	local k = f[1]
	if k == "F" or k == "M" or k == "Y" then
		local o = Instance.new((k == "F" and "Folder") or (k == "M" and "Model") or "Accessory")
		o.Name = nm(f[3])
		o.Parent = inst[tonumber(f[2])]
		n = n + 1
		inst[n] = o
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
		p.Parent = inst[tonumber(f[2])]
		n = n + 1
		inst[n] = p
		counts.parts = counts.parts + 1
	elseif k == "K" then
		local p = Instance.new("Part")
		p.Name = nm(f[3])
		p.Size = Vector3.new(1, 1, 1)
		p.CFrame = cfAt(f, 4)
		p.Transparency = 1
		setFlags(p, tonumber(f[8]))
		p.CanCollide, p.CanQuery, p.CanTouch, p.CastShadow = false, false, false, false
		setSurfaces(p, 0)
		p.Parent = inst[tonumber(f[2])]
		n = n + 1
		inst[n] = p
		counts.markers = counts.markers + 1
	elseif k == "X" then
		local mi = tonumber(f[4])
		local p = SOURCES[mi]:Clone()
		p.PivotOffset = CFrame.new() -- an imported mesh's pivot can sit thousands of studs away
		p.Name = nm(f[3])
		p.CFrame = cfAt(f, 5) * TURNS[mi]
		p.Color = color(tonumber(f[9]))
		p.Material = MAT[tonumber(f[10])]
		p.Transparency = tonumber(f[11])
		p.Reflectance = 0
		setFlags(p, tonumber(f[12]))
		pcall(function() p.TextureID = "" end)
		pcall(function() p.CollisionFidelity = Enum.CollisionFidelity.Box end)
		p.Parent = inst[tonumber(f[2])]
		n = n + 1
		inst[n] = p
		meshOf[p] = mi
		counts.meshes = counts.meshes + 1
	elseif k == "A" then
		local par = inst[tonumber(f[2])]
		local a = Instance.new("Attachment")
		a.Name = nm(f[3])
		a.CFrame = par.CFrame:Inverse() * cfAt(f, 4)
		a.Parent = par
		n = n + 1
		inst[n] = a
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
		l.Parent = inst[tonumber(f[2])]
		n = n + 1
		inst[n] = l
	elseif k == "H" then
		local h = Instance.new("Humanoid")
		h.Name = nm(f[3])
		h.RigType = Enum.HumanoidRigType[f[4]]
		h.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
		h.HealthDisplayType = Enum.HumanoidHealthDisplayType.AlwaysOff
		h.Parent = inst[tonumber(f[2])]
		n = n + 1
		inst[n] = h
	elseif k == "N" then
		local a = Instance.new("Animator")
		a.Name = nm(f[3])
		a.Parent = inst[tonumber(f[2])]
		n = n + 1
		inst[n] = a
	elseif k == "Q" then
		local sm = Instance.new("SpecialMesh")
		sm.Name = nm(f[3])
		sm.MeshType = Enum.MeshType[f[4]]
		sm.Scale = Vector3.new(tonumber(f[5]), tonumber(f[6]), tonumber(f[7]))
		sm.Parent = inst[tonumber(f[2])]
		n = n + 1
		inst[n] = sm
	elseif k == "W" then
		-- joints come last (every part exists by then): W part0 part1 name parent
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
		local p = inst[tonumber(f[2])]
		local off = cfAt(f, 3)
		local mi = meshOf[p]
		if mi then
			off = TURNS[mi]:Inverse() * off -- mesh parts carry the import turn in their CFrame
		end
		p.PivotOffset = off
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
root:SetAttribute("Batch", @@BATCH@@)
pcall(function() root:SetAttribute("Built", DateTime.now():ToIsoDate()) end)

-- 4. swap in the new map, remove the old one and the import ----------------------------------
if oldRoot then
	oldRoot:Destroy()
end
root.Parent = workspace

local removed = 0
local seen = {}
for part in pairs(containers) do
	-- climb to the outermost ancestor that holds nothing but imported pieces
	local top = part
	local p = part.Parent
	while p and p ~= workspace and p ~= ServerStorage and p ~= ReplicatedStorage and p ~= game do
		local clean = true
		for _, d in ipairs(p:GetDescendants()) do
			if d:IsA("BasePart") and not containers[d] then -- anything this run did not bring in: keep it
				clean = false
				break
			end
		end
		if not clean then break end
		top = p
		p = p.Parent
	end
	if not seen[top] and top.Parent then
		seen[top] = true
		top:Destroy()
		removed = removed + 1
	end
end

pcall(function() ChangeHistoryService:SetWaypoint("Built @@WHAT@@") end)
print(TAG .. string.format("built Workspace.%s: %d parts, %d mesh parts%s%s", ROOT_NAME, counts.parts,
	counts.meshes, counts.markers > 0 and (", " .. counts.markers .. " markers") or "",
	fresh and (", removed " .. removed .. " import container(s)") or
	" (meshes from ServerStorage." .. CACHE_NAME .. ")"))
'''

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], *(sys.argv[3:4] or ["map"]))
