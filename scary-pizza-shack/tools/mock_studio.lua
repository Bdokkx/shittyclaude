-- A strict stand-in for the bits of Roblox Studio the Pizza Shack build script uses.
-- Unknown classes, properties or enum members raise errors, so typos show up.

WARNINGS, PRINTS = {}, {}
function warn(...)
	local t = {...}
	for i = 1, #t do t[i] = tostring(t[i]) end
	table.insert(WARNINGS, table.concat(t, " "))
end
function print(...)
	local t = {...}
	for i = 1, #t do t[i] = tostring(t[i]) end
	table.insert(PRINTS, table.concat(t, " "))
end

-- ---------------------------------------------------------------- Vector3
V = {}
local function vec(x, y, z) return setmetatable({X = x or 0, Y = y or 0, Z = z or 0}, V) end
V.__index = function(v, k)
	if k == "Magnitude" then return math.sqrt(v.X * v.X + v.Y * v.Y + v.Z * v.Z) end
	if k == "Unit" then local m = math.sqrt(v.X * v.X + v.Y * v.Y + v.Z * v.Z) return vec(v.X / m, v.Y / m, v.Z / m) end
	if k == "Cross" then return function(a, b) return vec(a.Y * b.Z - a.Z * b.Y, a.Z * b.X - a.X * b.Z, a.X * b.Y - a.Y * b.X) end end
	if k == "Dot" then return function(a, b) return a.X * b.X + a.Y * b.Y + a.Z * b.Z end end
	error("Vector3 has no member " .. tostring(k), 2)
end
V.__add = function(a, b) return vec(a.X + b.X, a.Y + b.Y, a.Z + b.Z) end
V.__sub = function(a, b) return vec(a.X - b.X, a.Y - b.Y, a.Z - b.Z) end
V.__unm = function(a) return vec(-a.X, -a.Y, -a.Z) end
V.__div = function(a, s) assert(type(s) == "number", "Vector3 / non-number") return vec(a.X / s, a.Y / s, a.Z / s) end
V.__mul = function(a, s)
	if type(a) == "number" then a, s = s, a end
	if type(s) == "table" then return vec(a.X * s.X, a.Y * s.Y, a.Z * s.Z) end
	return vec(a.X * s, a.Y * s, a.Z * s)
end
V.__tostring = function(v) return string.format("(%.3f, %.3f, %.3f)", v.X, v.Y, v.Z) end
Vector3 = {new = vec, zero = vec(0, 0, 0)}

-- ---------------------------------------------------------------- CFrame
C = {}
local I3 = {{1, 0, 0}, {0, 1, 0}, {0, 0, 1}}
local function cf(p, r) return setmetatable({p = p, r = r}, C) end
local function rotv(r, v)
	return vec(r[1][1] * v.X + r[1][2] * v.Y + r[1][3] * v.Z, r[2][1] * v.X + r[2][2] * v.Y + r[2][3] * v.Z,
		r[3][1] * v.X + r[3][2] * v.Y + r[3][3] * v.Z)
end
local function matmul(a, b)
	local m = {{0, 0, 0}, {0, 0, 0}, {0, 0, 0}}
	for i = 1, 3 do for j = 1, 3 do for k = 1, 3 do m[i][j] = m[i][j] + a[i][k] * b[k][j] end end end
	return m
end
local function transpose(a) return {{a[1][1], a[2][1], a[3][1]}, {a[1][2], a[2][2], a[3][2]}, {a[1][3], a[2][3], a[3][3]}} end
local function inverse(s) local t = transpose(s.r); local q = rotv(t, s.p); return cf(vec(-q.X, -q.Y, -q.Z), t) end
C.__index = function(c, k)
	if k == "Position" then return c.p end
	if k == "LookVector" then return vec(-c.r[1][3], -c.r[2][3], -c.r[3][3]) end
	if k == "Inverse" then return inverse end
	if k == "Rotation" then return cf(vec(0, 0, 0), c.r) end
	error("CFrame has no member " .. tostring(k), 2)
end
C.__mul = function(a, b)
	if getmetatable(b) == V then return rotv(a.r, b) + a.p end
	assert(getmetatable(b) == C, "CFrame * something odd")
	return cf(rotv(a.r, b.p) + a.p, matmul(a.r, b.r))
end
C.__sub = function(a, v) assert(getmetatable(v) == V, "CFrame - non-Vector3") return cf(a.p - v, a.r) end
C.__add = function(a, v) return cf(a.p + v, a.r) end
CFrame = {
	new = function(x, y, z, ...)
		if type(x) == "table" then return cf(x, I3) end
		local r = {...}
		if #r == 9 then return cf(vec(x, y, z), {{r[1], r[2], r[3]}, {r[4], r[5], r[6]}, {r[7], r[8], r[9]}}) end
		assert(#r == 0, "CFrame.new with " .. (#r + 3) .. " numbers")
		return cf(vec(x or 0, y or 0, z or 0), I3)
	end,
	fromMatrix = function(p, x, y, z)
		if z == nil then z = x:Cross(y) end
		return cf(p, {{x.X, y.X, z.X}, {x.Y, y.Y, z.Y}, {x.Z, y.Z, z.Z}})
	end,
}
function cframe_rows(c) return c.p.X, c.p.Y, c.p.Z, c.r[1][1], c.r[1][2], c.r[1][3], c.r[2][1], c.r[2][2], c.r[2][3], c.r[3][1], c.r[3][2], c.r[3][3] end
function make_cframe(x, y, z, a, b, c, d, e, f, g, h, i) return cf(vec(x, y, z), {{a, b, c}, {d, e, f}, {g, h, i}}) end

Color3 = {fromRGB = function(r, g, b)
	assert(r >= 0 and r <= 255 and g >= 0 and g <= 255 and b >= 0 and b <= 255, "Color3.fromRGB out of range")
	return {R = r / 255, G = g / 255, B = b / 255, rgb = {r, g, b}}
end}

-- ---------------------------------------------------------------- enums
local ENUMS = {
	PartType = {"Ball", "Block", "Cylinder", "Wedge", "CornerWedge"},
	Material = {"Plastic", "SmoothPlastic", "Neon", "Wood", "WoodPlanks", "Marble", "Slate", "Concrete", "Granite",
		"Brick", "Pebble", "Cobblestone", "CorrodedMetal", "DiamondPlate", "Foil", "Metal", "Grass", "Sand", "Fabric",
		"Ice", "Glass", "ForceField", "Ground"},
	SurfaceType = {"Smooth", "Glue", "Weld", "Studs", "Inlet", "Universal", "Hinge", "Motor", "SteppingMotor", "SmoothNoOutlines"},
	NormalId = {"Right", "Top", "Back", "Left", "Bottom", "Front"},
	CollisionFidelity = {"Default", "Hull", "Box", "PreciseConvexDecomposition"},
	HumanoidRigType = {"R6", "R15"},
	HumanoidDisplayDistanceType = {"Viewer", "Subject", "None"},
	HumanoidHealthDisplayType = {"DisplayWhenDamaged", "AlwaysOn", "AlwaysOff"},
	MeshType = {"Head", "Torso", "Wedge", "Prism", "Pyramid", "ParallelRamp", "RightAngleRamp", "CornerWedge",
		"Brick", "Sphere", "Cylinder", "FileMesh"},
}
Enum = {}
for ename, members in pairs(ENUMS) do
	local e = {}
	for i, m in ipairs(members) do e[m] = {Name = m, Value = i - 1, EnumType = ename} end
	Enum[ename] = setmetatable(e, {__index = function(_, k) error("Enum." .. ename .. " has no member " .. tostring(k), 2) end})
end
setmetatable(Enum, {__index = function(_, k) error("unknown enum Enum." .. tostring(k), 2) end})

-- ---------------------------------------------------------------- instances
local P = {}
local function props(class, list, base)
	local t = {}
	if base then for k in pairs(P[base]) do t[k] = true end end
	for _, k in ipairs(list) do t[k] = true end
	P[class] = t
end
props("Instance", {"Name", "Parent"})
props("BasePart", {"Anchored", "CanCollide", "CanTouch", "CanQuery", "Massless", "Transparency", "CastShadow",
	"Size", "CFrame", "Color", "Material", "Reflectance", "TopSurface", "BottomSurface", "FrontSurface",
	"BackSurface", "LeftSurface", "RightSurface", "PivotOffset"}, "Instance")
props("Part", {"Shape"}, "BasePart")
props("WedgePart", {}, "BasePart")
props("MeshPart", {"TextureID", "CollisionFidelity", "MeshId"}, "BasePart")
props("Model", {"PrimaryPart", "WorldPivot"}, "Instance")
props("Folder", {}, "Instance")
props("Attachment", {"CFrame"}, "Instance")
props("WeldConstraint", {"Part0", "Part1", "Enabled"}, "Instance")
props("Motor6D", {"Part0", "Part1", "C0", "C1"}, "Instance")
props("PointLight", {"Color", "Brightness", "Range", "Shadows", "Enabled"}, "Instance")
props("SpotLight", {"Color", "Brightness", "Range", "Shadows", "Enabled", "Angle", "Face"}, "Instance")
props("SurfaceLight", {"Color", "Brightness", "Range", "Shadows", "Enabled", "Angle", "Face"}, "Instance")
props("SurfaceAppearance", {}, "Instance")
props("Accessory", {}, "Instance")
props("Humanoid", {"RigType", "DisplayDistanceType", "HealthDisplayType"}, "Instance")
props("Animator", {}, "Instance")
props("SpecialMesh", {"MeshType", "Scale"}, "Instance")
local PARTS = {Part = true, MeshPart = true, WedgePart = true}
local CREATABLE = {Folder = true, Model = true, Part = true, WedgePart = true, Attachment = true,
	WeldConstraint = true, Motor6D = true, PointLight = true, SpotLight = true, SurfaceLight = true,
	Accessory = true, Humanoid = true, Animator = true, SpecialMesh = true}

Inst = {}
CREATED = 0
local function newInst(class, fields)
	local o = {ClassName = class, _children = {}, _attrs = {}, _p = {Name = class}}
	setmetatable(o, Inst)
	local p = o._p
	if PARTS[class] then
		p.Anchored = false; p.CanCollide = true; p.CanTouch = true; p.CanQuery = true; p.Massless = false
		p.Transparency = 0; p.CastShadow = true; p.Size = vec(4, 1, 2); p.CFrame = CFrame.new()
		p.PivotOffset = CFrame.new(); p.Reflectance = 0
		p.TopSurface = Enum.SurfaceType.Smooth; p.BottomSurface = Enum.SurfaceType.Smooth
		p.Material = Enum.Material.Plastic; p.Color = Color3.fromRGB(163, 162, 165)
		if class == "Part" then p.Shape = Enum.PartType.Block end
	elseif class == "Attachment" then
		p.CFrame = CFrame.new()
	elseif class == "Motor6D" then
		p.C0 = CFrame.new(); p.C1 = CFrame.new()
	elseif class == "SpecialMesh" then
		p.MeshType = Enum.MeshType.Head; p.Scale = vec(1, 1, 1)
	elseif class == "Humanoid" then
		p.RigType = Enum.HumanoidRigType.R15
		p.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.Viewer
		p.HealthDisplayType = Enum.HumanoidHealthDisplayType.DisplayWhenDamaged
	end
	for k, v in pairs(fields or {}) do p[k] = v end
	CREATED = CREATED + 1
	return o
end
Instance = {new = function(class, parent)
	if not CREATABLE[class] then error("Instance.new: class " .. tostring(class) .. " not expected here", 2) end
	assert(parent == nil, "use .Parent instead of the 2nd argument")
	return newInst(class)
end}
function mock_new(class, fields) return newInst(class, fields) end

Inst.__index = function(o, k)
	local m = rawget(Inst, k)
	if m then return m end
	if type(k) == "string" and k:sub(1, 1) == "_" then return nil end
	local cls = rawget(o, "ClassName")
	if k == "Parent" then return rawget(o, "_parent") end
	if k == "ClassName" then return cls end
	if k == "Position" and PARTS[cls] then return o._p.CFrame.p end
	local v = o._p[k]
	if v ~= nil then return v end
	if P[cls] and P[cls][k] then return nil end
	local child = Inst.FindFirstChild(o, k)
	if child then return child end
	error(cls .. "." .. tostring(k) .. " is not a valid member", 2)
end
Inst.__newindex = function(o, k, v)
	local cls = rawget(o, "ClassName")
	if not (P[cls] and P[cls][k]) then error("cannot set " .. cls .. "." .. tostring(k), 2) end
	if k == "Parent" then
		if rawget(o, "_destroyed") then error("cannot parent a destroyed " .. o._p.Name, 2) end
		local old = rawget(o, "_parent")
		if old then for i, c in ipairs(old._children) do if c == o then table.remove(old._children, i) break end end end
		rawset(o, "_parent", v)
		if v then table.insert(v._children, o) end
		return
	end
	if k == "Size" then assert(getmetatable(v) == V and v.X > 0 and v.Y > 0 and v.Z > 0, "bad Size") end
	if k == "CFrame" or k == "PivotOffset" or k == "C0" or k == "C1" then assert(getmetatable(v) == C, "bad " .. k) end
	if k == "Scale" then assert(getmetatable(v) == V, "bad Scale") end
	if (k == "Material" or k == "Shape" or k:find("Surface") or k == "Face" or k == "CollisionFidelity" or
		k == "RigType" or k == "DisplayDistanceType" or k == "HealthDisplayType" or k == "MeshType") then
		assert(type(v) == "table" and v.EnumType, "bad enum for " .. k)
	end
	if k == "PrimaryPart" and v ~= nil then assert(v:IsDescendantOf(o), "PrimaryPart must be inside the model") end
	o._p[k] = v
end
Inst.__tostring = function(o) return o._p.Name end

function Inst.IsA(o, c)
	local k = rawget(o, "ClassName")
	if c == k or c == "Instance" then return true end
	if c == "BasePart" then return PARTS[k] == true end
	return false
end
function Inst.GetChildren(o) local t = {} for i, c in ipairs(o._children) do t[i] = c end return t end
function Inst.GetDescendants(o)
	local t = {}
	local function walk(x) for _, c in ipairs(x._children) do table.insert(t, c) walk(c) end end
	walk(o)
	return t
end
function Inst.FindFirstChild(o, n)
	for _, c in ipairs(o._children) do if c._p.Name == n then return c end end
	return nil
end
function Inst.IsDescendantOf(o, a)
	local p = rawget(o, "_parent")
	while p do if p == a then return true end p = rawget(p, "_parent") end
	return false
end
function Inst.Destroy(o)
	for _, c in ipairs(Inst.GetChildren(o)) do Inst.Destroy(c) end
	if rawget(o, "_parent") then o.Parent = nil end
	rawset(o, "_destroyed", true)
end
function Inst.SetAttribute(o, k, v)
	assert(type(k) == "string" and k:match("^[%w_]+$"), "bad attribute name " .. tostring(k))
	local t = type(v)
	assert(t == "number" or t == "string" or t == "boolean", "bad attribute value for " .. k)
	o._attrs[k] = v
end
function Inst.GetAttribute(o, k) return o._attrs[k] end
local REFKEYS = {Part0 = true, Part1 = true, PrimaryPart = true}
function Inst.Clone(o)
	local map = {}
	local function copy(x)
		local c = setmetatable({ClassName = x.ClassName, _children = {}, _attrs = {}, _p = {}}, Inst)
		for k, v in pairs(x._p) do c._p[k] = v end
		for k, v in pairs(x._attrs) do c._attrs[k] = v end
		map[x] = c
		for _, ch in ipairs(x._children) do
			local cc = copy(ch)
			rawset(cc, "_parent", c)
			table.insert(c._children, cc)
		end
		CREATED = CREATED + 1
		return c
	end
	local root = copy(o)
	for orig, c in pairs(map) do
		for k in pairs(REFKEYS) do
			local v = orig._p[k]
			if v ~= nil and map[v] then c._p[k] = map[v] end
		end
	end
	return root
end

-- ---------------------------------------------------------------- services
game = newInst("Folder", {Name = "game"})
workspace = newInst("Folder", {Name = "Workspace"})
workspace.Parent = game
local services = {
	Workspace = workspace,
	ServerStorage = newInst("Folder", {Name = "ServerStorage"}),
	ReplicatedStorage = newInst("Folder", {Name = "ReplicatedStorage"}),
	ChangeHistoryService = {SetWaypoint = function(self, name) assert(type(name) == "string") end},
}
services.ServerStorage.Parent = game
services.ReplicatedStorage.Parent = game
function Inst.GetService(o, n)
	local s = services[n]
	if not s then error("GetService: unexpected service " .. tostring(n), 2) end
	return s
end
rawset(Inst, "GetService", Inst.GetService)
function cf_mul(a, b) return a * b end
function same(a, b) return rawequal(a, b) end
