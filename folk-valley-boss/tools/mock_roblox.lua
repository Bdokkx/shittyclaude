-- A small stand-in for the Roblox engine, enough to run the Grim Reaper's build
-- script and its controller outside Studio: Vector3 / CFrame maths, instances
-- with the properties these scripts use (anything else is an error, so typos
-- show up), known enums only, a simulated clock with task.spawn / wait / delay,
-- Heartbeat, BindableEvents, humanoids and animation tracks that fire their
-- markers as simulated time passes.

ERRORS = {}
WARNINGS = {}
function warn(...)
	local t = {...}
	for i = 1, #t do t[i] = tostring(t[i]) end
	table.insert(WARNINGS, table.concat(t, " "))
end

-- ---------------------------------------------------------------- Vector3

V = {}
local function vec(x, y, z) return setmetatable({X = x or 0, Y = y or 0, Z = z or 0}, V) end
V.__index = function(v, k)
	if k == "Magnitude" then return math.sqrt(v.X * v.X + v.Y * v.Y + v.Z * v.Z) end
	if k == "Unit" then
		local m = math.sqrt(v.X * v.X + v.Y * v.Y + v.Z * v.Z)
		if m == 0 then return vec(0 / 0, 0 / 0, 0 / 0) end
		return vec(v.X / m, v.Y / m, v.Z / m)
	end
	if k == "Cross" then return function(a, b) return vec(a.Y * b.Z - a.Z * b.Y, a.Z * b.X - a.X * b.Z, a.X * b.Y - a.Y * b.X) end end
	if k == "Dot" then return function(a, b) return a.X * b.X + a.Y * b.Y + a.Z * b.Z end end
	if k == "Lerp" then return function(a, b, t) return a + (b - a) * t end end
	error("Vector3 has no member " .. tostring(k), 2)
end
V.__add = function(a, b) return vec(a.X + b.X, a.Y + b.Y, a.Z + b.Z) end
V.__sub = function(a, b) return vec(a.X - b.X, a.Y - b.Y, a.Z - b.Z) end
V.__unm = function(a) return vec(-a.X, -a.Y, -a.Z) end
V.__div = function(a, s) return vec(a.X / s, a.Y / s, a.Z / s) end
V.__mul = function(a, s)
	if type(a) == "number" then a, s = s, a end
	if type(s) == "table" then return vec(a.X * s.X, a.Y * s.Y, a.Z * s.Z) end
	return vec(a.X * s, a.Y * s, a.Z * s)
end
V.__eq = function(a, b) return a.X == b.X and a.Y == b.Y and a.Z == b.Z end
V.__tostring = function(v) return string.format("(%.3f, %.3f, %.3f)", v.X, v.Y, v.Z) end
Vector3 = {new = vec, zero = vec(0, 0, 0), one = vec(1, 1, 1), xAxis = vec(1, 0, 0), yAxis = vec(0, 1, 0), zAxis = vec(0, 0, 1)}
Vector2 = {new = function(x, y) return {X = x, Y = y} end}

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
local function toquat(m)
	local tr = m[1][1] + m[2][2] + m[3][3]
	local w, x, y, z
	if tr > 0 then
		local s = math.sqrt(tr + 1) * 2
		w, x, y, z = 0.25 * s, (m[3][2] - m[2][3]) / s, (m[1][3] - m[3][1]) / s, (m[2][1] - m[1][2]) / s
	elseif m[1][1] > m[2][2] and m[1][1] > m[3][3] then
		local s = math.sqrt(1 + m[1][1] - m[2][2] - m[3][3]) * 2
		w, x, y, z = (m[3][2] - m[2][3]) / s, 0.25 * s, (m[1][2] + m[2][1]) / s, (m[1][3] + m[3][1]) / s
	elseif m[2][2] > m[3][3] then
		local s = math.sqrt(1 + m[2][2] - m[1][1] - m[3][3]) * 2
		w, x, y, z = (m[1][3] - m[3][1]) / s, (m[1][2] + m[2][1]) / s, 0.25 * s, (m[2][3] + m[3][2]) / s
	else
		local s = math.sqrt(1 + m[3][3] - m[1][1] - m[2][2]) * 2
		w, x, y, z = (m[2][1] - m[1][2]) / s, (m[1][3] + m[3][1]) / s, (m[2][3] + m[3][2]) / s, 0.25 * s
	end
	return {w, x, y, z}
end
local function frommquat(q)
	local w, x, y, z = q[1], q[2], q[3], q[4]
	local n = math.sqrt(w * w + x * x + y * y + z * z)
	w, x, y, z = w / n, x / n, y / n, z / n
	return {{1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)},
		{2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)},
		{2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)}}
end
local function rx(a) local c, s = math.cos(a), math.sin(a) return {{1, 0, 0}, {0, c, -s}, {0, s, c}} end
local function ry(a) local c, s = math.cos(a), math.sin(a) return {{c, 0, s}, {0, 1, 0}, {-s, 0, c}} end
local function rz(a) local c, s = math.cos(a), math.sin(a) return {{c, -s, 0}, {s, c, 0}, {0, 0, 1}} end
C.__index = function(c, k)
	if k == "Position" then return c.p end
	if k == "X" then return c.p.X end
	if k == "Y" then return c.p.Y end
	if k == "Z" then return c.p.Z end
	if k == "LookVector" then return vec(-c.r[1][3], -c.r[2][3], -c.r[3][3]) end
	if k == "RightVector" then return vec(c.r[1][1], c.r[2][1], c.r[3][1]) end
	if k == "UpVector" then return vec(c.r[1][2], c.r[2][2], c.r[3][2]) end
	if k == "Inverse" then return inverse end
	if k == "ToObjectSpace" then return function(s, o) return inverse(s) * o end end
	if k == "PointToWorldSpace" then return function(s, v) return s * v end end
	if k == "VectorToWorldSpace" then return function(s, v) return rotv(s.r, v) end end
	if k == "Lerp" then
		return function(a, b, t)
			local qa, qb = toquat(a.r), toquat(b.r)
			local d = qa[1] * qb[1] + qa[2] * qb[2] + qa[3] * qb[3] + qa[4] * qb[4]
			if d < 0 then qb = {-qb[1], -qb[2], -qb[3], -qb[4]}; d = -d end
			local q
			if d > 0.9995 then
				q = {qa[1] + (qb[1] - qa[1]) * t, qa[2] + (qb[2] - qa[2]) * t, qa[3] + (qb[3] - qa[3]) * t, qa[4] + (qb[4] - qa[4]) * t}
			else
				local th = math.acos(d)
				local sa, sb = math.sin((1 - t) * th) / math.sin(th), math.sin(t * th) / math.sin(th)
				q = {qa[1] * sa + qb[1] * sb, qa[2] * sa + qb[2] * sb, qa[3] * sa + qb[3] * sb, qa[4] * sa + qb[4] * sb}
			end
			return cf(a.p + (b.p - a.p) * t, frommquat(q))
		end
	end
	error("CFrame has no member " .. tostring(k), 2)
end
C.__mul = function(a, b)
	if getmetatable(b) == V then return rotv(a.r, b) + a.p end
	return cf(rotv(a.r, b.p) + a.p, matmul(a.r, b.r))
end
C.__sub = function(a, v) return cf(a.p - v, a.r) end
C.__add = function(a, v) return cf(a.p + v, a.r) end
CFrame = {
	new = function(x, y, z, ...)
		if type(x) == "table" then return cf(x, I3) end
		local r = {...}
		if #r == 9 then return cf(vec(x, y, z), {{r[1], r[2], r[3]}, {r[4], r[5], r[6]}, {r[7], r[8], r[9]}}) end
		return cf(vec(x or 0, y or 0, z or 0), I3)
	end,
	fromMatrix = function(p, x, y, z)
		if z == nil then z = x:Cross(y) end
		return cf(p, {{x.X, y.X, z.X}, {x.Y, y.Y, z.Y}, {x.Z, y.Z, z.Z}})
	end,
	Angles = function(a, b, c) return cf(vec(0, 0, 0), matmul(matmul(rx(a), ry(b)), rz(c))) end,
	lookAt = function(at, target, up)
		up = up or vec(0, 1, 0)
		local look = (target - at).Unit
		local right = look:Cross(up).Unit
		local u = right:Cross(look)
		return cf(at, {{right.X, u.X, -look.X}, {right.Y, u.Y, -look.Y}, {right.Z, u.Z, -look.Z}})
	end,
	identity = cf(vec(0, 0, 0), I3),
}
function cframe_rows(c) return c.p.X, c.p.Y, c.p.Z, c.r[1][1], c.r[1][2], c.r[1][3], c.r[2][1], c.r[2][2], c.r[2][3], c.r[3][1], c.r[3][2], c.r[3][3] end

-- ---------------------------------------------------------------- small value types

Color3 = {
	fromRGB = function(r, g, b) return {R = r / 255, G = g / 255, B = b / 255, _rgb = {r, g, b}} end,
	new = function(r, g, b) return {R = r, G = g, B = b, _rgb = {r * 255, g * 255, b * 255}} end,
}
ColorSequence = {new = function(a, b) assert(a and a.R, "ColorSequence.new: colour expected") return {a, b or a} end}
NumberSequenceKeypoint = {new = function(t, v) assert(type(t) == "number" and type(v) == "number") return {Time = t, Value = v} end}
NumberSequence = {new = function(x)
	if type(x) == "table" then
		assert(#x >= 2 and x[1].Time == 0 and x[#x].Time == 1, "NumberSequence: keypoints must start at 0 and end at 1")
	end
	return {x}
end}
NumberRange = {new = function(a, b) assert(type(a) == "number") return {Min = a, Max = b or a} end}
UDim = {new = function(s, o) return {Scale = s, Offset = o} end}
UDim2 = {new = function(a, b, c, d) return {X = {Scale = a, Offset = b}, Y = {Scale = c, Offset = d}} end}
TweenInfo = {new = function(t, style, dir) assert(type(t) == "number") return {Time = t, EasingStyle = style, EasingDirection = dir} end}
RaycastParams = {new = function() return {FilterDescendantsInstances = {}, FilterType = nil} end}

-- ---------------------------------------------------------------- enums (only the members that exist)

local ENUMS = {
	AnimationPriority = {"Idle", "Movement", "Action", "Action2", "Action3", "Action4", "Core"},
	PartType = {"Ball", "Block", "Cylinder", "Wedge", "CornerWedge"},
	Material = {"Plastic", "SmoothPlastic", "Neon", "Wood", "WoodPlanks", "Marble", "Slate", "Concrete", "Granite",
		"Brick", "Pebble", "Cobblestone", "CorrodedMetal", "DiamondPlate", "Foil", "Metal", "Grass", "Sand", "Fabric",
		"Ice", "Glass", "ForceField", "Rock", "Glacier", "Snow", "Sandstone", "Mud", "Basalt", "Ground", "CrackedLava",
		"Asphalt", "LeafyGrass", "Salt", "Limestone", "Pavement", "Cardboard", "Carpet", "CeramicTiles",
		"ClayRoofTiles", "RoofShingles", "Leather", "Plaster", "Rubber"},
	EasingStyle = {"Linear", "Sine", "Back", "Quad", "Quart", "Quint", "Bounce", "Elastic", "Exponential", "Circular", "Cubic"},
	EasingDirection = {"In", "Out", "InOut"},
	ActuatorRelativeTo = {"Attachment0", "Attachment1", "World"},
	VelocityConstraintMode = {"Line", "Plane", "Vector"},
	HumanoidStateType = {"FallingDown", "Running", "RunningNoPhysics", "Climbing", "StrafingNoPhysics", "Ragdoll",
		"GettingUp", "Jumping", "Landed", "Flying", "Freefall", "Seated", "PlatformStanding", "Dead", "Swimming",
		"Physics", "None"},
	NormalId = {"Right", "Top", "Back", "Left", "Bottom", "Front"},
	Font = {"Legacy", "Arial", "ArialBold", "SourceSans", "SourceSansBold", "Gotham", "GothamBold", "GothamBlack",
		"FredokaOne", "Bangers", "Creepster", "Cartoon", "LuckiestGuy"},
	HumanoidRigType = {"R6", "R15"},
	HumanoidDisplayDistanceType = {"Viewer", "Subject", "None"},
	HumanoidHealthDisplayType = {"DisplayWhenDamaged", "AlwaysOn", "AlwaysOff"},
	ParticleEmitterShape = {"Box", "Sphere", "Cylinder", "Disc"},
	ParticleEmitterShapeStyle = {"Volume", "Surface"},
	CollisionFidelity = {"Default", "Hull", "Box", "PreciseConvexDecomposition"},
	SurfaceType = {"Smooth", "Glue", "Weld", "Studs", "Inlet", "Universal", "Hinge", "Motor", "SteppingMotor", "SmoothNoOutlines"},
}
Enum = {}
for ename, members in pairs(ENUMS) do
	local e = {}
	for i, m in ipairs(members) do e[m] = {Name = m, Value = i - 1, EnumType = ename} end
	Enum[ename] = setmetatable(e, {__index = function(_, k) error("Enum." .. ename .. " has no member " .. tostring(k), 2) end})
end
setmetatable(Enum, {__index = function(_, k) error("unknown enum Enum." .. tostring(k), 2) end})

-- ---------------------------------------------------------------- the clock, tasks and signals

SIM = {t = 0, frame = 0, threads = {}, heartbeat = {}, hbwait = {}}
os.clock = function() return SIM.t end
function tick() return SIM.t end
function time() return SIM.t end

local function resume(co, ...)
	local ok, err = coroutine.resume(co, ...)
	if not ok then table.insert(ERRORS, debug.traceback(co, tostring(err))) end
	return ok
end
SIM.resume = resume

local function schedule(co, at, args) table.insert(SIM.threads, {co = co, at = at, args = args}) end

task = {}
function task.spawn(fn, ...)
	local co = type(fn) == "thread" and fn or coroutine.create(fn)
	resume(co, ...)
	return co
end
function task.defer(fn, ...)
	local co = coroutine.create(fn)
	schedule(co, SIM.t, {...})
	return co
end
function task.delay(dt, fn, ...)
	local co = coroutine.create(fn)
	schedule(co, SIM.t + (dt or 0), {...})
	return co
end
function task.wait(dt)
	local co, main = coroutine.running()
	if main then error("task.wait outside a coroutine in the mock") end
	local t0 = SIM.t
	schedule(co, SIM.t + (dt or 0), nil)
	coroutine.yield()
	return SIM.t - t0
end
wait = task.wait
spawn = task.spawn
delay = task.delay

local Signal = {}
Signal.__index = Signal
function Signal.new() return setmetatable({fns = {}, waiting = {}}, Signal) end
function Signal:Connect(fn)
	local entry = {fn = fn, connected = true}
	table.insert(self.fns, entry)
	return {Connected = true, Disconnect = function(c) entry.connected = false; c.Connected = false end}
end
function Signal:Once(fn)
	local c
	c = self:Connect(function(...) c:Disconnect() fn(...) end)
	return c
end
function Signal:Fire(...)
	local fns = {}
	for _, e in ipairs(self.fns) do if e.connected then table.insert(fns, e.fn) end end
	for _, fn in ipairs(fns) do task.spawn(fn, ...) end
	local w = self.waiting
	self.waiting = {}
	for _, co in ipairs(w) do resume(co, ...) end
end
function Signal:Wait()
	local co, main = coroutine.running()
	if main then error("Signal:Wait outside a coroutine in the mock") end
	table.insert(self.waiting, co)
	return coroutine.yield()
end

-- ---------------------------------------------------------------- instances

local P = {} -- per class: allowed properties (beyond Name, Parent)
local function props(class, list, base)
	local t = {}
	if base then for k in pairs(P[base]) do t[k] = true end end
	for _, k in ipairs(list) do t[k] = true end
	P[class] = t
end
props("Instance", {"Name", "Parent", "Archivable"})
props("BasePart", {"Anchored", "CanCollide", "CanTouch", "CanQuery", "Massless", "Transparency", "CastShadow",
	"Size", "CFrame", "Color", "Material", "Reflectance", "TopSurface", "BottomSurface", "AssemblyLinearVelocity",
	"AssemblyAngularVelocity", "Position", "Orientation", "Locked"}, "Instance")
props("Part", {"Shape"}, "BasePart")
props("MeshPart", {"TextureID", "CollisionFidelity", "MeshId"}, "BasePart")
props("Model", {"PrimaryPart", "WorldPivot"}, "Instance")
props("Folder", {}, "Instance")
props("Attachment", {"CFrame", "WorldPosition", "Position", "Visible"}, "Instance")
props("WeldConstraint", {"Part0", "Part1", "Enabled"}, "Instance")
props("Motor6D", {"Part0", "Part1", "C0", "C1", "Transform", "MaxVelocity"}, "Instance")
props("Humanoid", {"RigType", "AutomaticScalingEnabled", "HipHeight", "BreakJointsOnDeath", "RequiresNeck",
	"MaxHealth", "Health", "WalkSpeed", "UseJumpPower", "JumpPower", "DisplayDistanceType", "HealthDisplayType",
	"AutoRotate", "PlatformStand", "Sit", "WalkToPoint"}, "Instance")
props("Animator", {}, "Instance")
props("Script", {"Source", "Disabled", "Enabled"}, "Instance")
props("PointLight", {"Color", "Brightness", "Range", "Shadows", "Enabled"}, "Instance")
props("ParticleEmitter", {"Texture", "Color", "Size", "Transparency", "Lifetime", "Speed", "SpreadAngle",
	"Acceleration", "Drag", "Rate", "EmissionDirection", "RotSpeed", "Rotation", "LightEmission", "LightInfluence",
	"Shape", "ShapeStyle", "Enabled", "ZOffset", "LockedToPart"}, "Instance")
props("Trail", {"Attachment0", "Attachment1", "Color", "Transparency", "Lifetime", "LightEmission", "FaceCamera",
	"Enabled", "WidthScale", "MinLength"}, "Instance")
props("BindableEvent", {}, "Instance")
props("Animation", {"AnimationId"}, "Instance")
props("Sound", {"SoundId", "Volume", "PlaybackSpeed", "TimeLength", "Playing", "Looped"}, "Instance")
props("KeyframeSequence", {"Loop", "Priority"}, "Instance")
props("LinearVelocity", {"Attachment0", "Attachment1", "RelativeTo", "VelocityConstraintMode", "MaxForce",
	"VectorVelocity", "Enabled", "ForceLimitsEnabled"}, "Instance")
props("GuiObject", {"Size", "Position", "AnchorPoint", "BackgroundColor3", "BackgroundTransparency", "BorderSizePixel",
	"Visible", "ZIndex"}, "Instance")
props("Frame", {}, "GuiObject")
props("TextLabel", {"Text", "Font", "TextScaled", "TextColor3", "TextStrokeTransparency", "TextStrokeColor3",
	"TextSize", "TextTransparency"}, "GuiObject")
props("BillboardGui", {"Size", "StudsOffset", "MaxDistance", "LightInfluence", "ResetOnSpawn", "Adornee",
	"AlwaysOnTop", "Enabled", "StudsOffsetWorldSpace"}, "Instance")
props("UICorner", {"CornerRadius"}, "Instance")
props("UIGradient", {"Color", "Rotation", "Transparency"}, "Instance")
props("UIStroke", {"Color", "Thickness", "Transparency"}, "Instance")
local PARTS = {Part = true, MeshPart = true}
local GUI = {Frame = true, TextLabel = true}
local CREATABLE = {}
for k in pairs(P) do CREATABLE[k] = true end
CREATABLE.Instance, CREATABLE.BasePart, CREATABLE.GuiObject = nil, nil, nil

Inst = {}
local function isA(o, c)
	local k = rawget(o, "ClassName")
	if c == k or c == "Instance" then return true end
	if c == "BasePart" then return PARTS[k] == true end
	if c == "GuiObject" or c == "GuiBase2d" then return GUI[k] == true end
	if c == "LayerCollector" then return k == "BillboardGui" end
	if c == "Constraint" then return k == "LinearVelocity" end
	if c == "JointInstance" then return k == "Motor6D" end
	if c == "LuaSourceContainer" or c == "BaseScript" then return k == "Script" end
	return false
end

local function newInst(class, fields)
	local o = {ClassName = class, _children = {}, _attrs = {}, _p = {Name = class}, _signals = {}}
	setmetatable(o, Inst)
	local p = o._p
	if PARTS[class] then
		p.Anchored = false; p.CanCollide = true; p.CanTouch = true; p.CanQuery = true; p.Massless = false
		p.Transparency = 0; p.CastShadow = true; p.Size = vec(4, 1, 2); p.CFrame = CFrame.new()
		p.AssemblyLinearVelocity = vec(0, 0, 0)
	elseif class == "Attachment" then
		p.CFrame = CFrame.new()
	elseif class == "Humanoid" then
		p.MaxHealth = 100; p.Health = 100; p.WalkSpeed = 16; p.HipHeight = 2; p.AutoRotate = true
		rawset(o, "_states", {})
	elseif class == "ParticleEmitter" then
		p.Rate = 20; p.Enabled = true
	elseif class == "Trail" or class == "BillboardGui" or class == "PointLight" then
		p.Enabled = true
		if class == "PointLight" then p.Brightness = 1 end
	end
	for k, v in pairs(fields or {}) do p[k] = v end
	return o
end

local function signal(o, name)
	local s = o._signals[name]
	if not s then s = Signal.new(); o._signals[name] = s end
	return s
end

Inst.__index = function(o, k)
	local m = rawget(Inst, k)
	if m then return m end
	if type(k) == "string" and k:sub(1, 1) == "_" then return nil end
	local cls = rawget(o, "ClassName")
	if k == "Parent" then return rawget(o, "_parent") end
	if k == "ClassName" then return cls end
	if k == "Position" and PARTS[cls] then return o._p.CFrame.p end
	if k == "WorldPosition" and cls == "Attachment" then
		local par = rawget(o, "_parent")
		if par and PARTS[par.ClassName] then return (par._p.CFrame * o._p.CFrame).p end
		return o._p.CFrame.p
	end
	if k == "WorldCFrame" and cls == "Attachment" then
		local par = rawget(o, "_parent")
		return par._p.CFrame * o._p.CFrame
	end
	if k == "HealthChanged" and cls == "Humanoid" then return signal(o, "HealthChanged") end
	if k == "Died" and cls == "Humanoid" then return signal(o, "Died") end
	if k == "Event" and cls == "BindableEvent" then return signal(o, "Event") end
	if k == "AncestryChanged" then return signal(o, "AncestryChanged") end
	if k == "Changed" then return signal(o, "Changed") end
	local v = o._p[k]
	if v ~= nil then return v end
	if P[cls] and P[cls][k] then return nil end
	local child = Inst.FindFirstChild(o, k)
	if child then return child end
	error(cls .. "." .. tostring(k) .. " is not a valid member", 2)
end
Inst.__newindex = function(o, k, v)
	local cls = rawget(o, "ClassName")
	if rawget(o, "_destroyed") and k == "Parent" and v ~= nil then error("cannot parent a destroyed " .. o._p.Name, 2) end
	if not (P[cls] and P[cls][k]) then error("cannot set " .. cls .. "." .. tostring(k), 2) end
	if k == "Parent" then
		if rawget(o, "_parent_locked") then error("Parent of " .. o._p.Name .. " is locked", 2) end
		local old = rawget(o, "_parent")
		if old then for i, c in ipairs(old._children) do if c == o then table.remove(old._children, i) break end end end
		rawset(o, "_parent", v)
		if v then table.insert(v._children, o) end
		return
	end
	if k == "Position" and PARTS[cls] then
		o._p.CFrame = cf(v, o._p.CFrame.r)
		return
	end
	if k == "WorldPosition" and cls == "Attachment" then
		local par = rawget(o, "_parent")
		local rel = par and inverse(par._p.CFrame) * v or v
		o._p.CFrame = cf(rel, o._p.CFrame.r)
		return
	end
	if cls == "Humanoid" and k == "Health" then
		local old = o._p.Health
		v = math.max(0, math.min(v, o._p.MaxHealth or 100))
		o._p.Health = v
		if v ~= old then signal(o, "HealthChanged"):Fire(v) end
		return
	end
	if cls == "Humanoid" and k == "MaxHealth" then
		o._p.MaxHealth = v
		if (o._p.Health or 0) > v then o._p.Health = v end
		return
	end
	o._p[k] = v
end
Inst.__tostring = function(o) return o._p.Name end

function Inst.IsA(o, c) return isA(o, c) end
function Inst.GetChildren(o) local t = {} for i, c in ipairs(o._children) do t[i] = c end return t end
function Inst.GetDescendants(o)
	local t = {}
	local function walk(x) for _, c in ipairs(x._children) do table.insert(t, c) walk(c) end end
	walk(o)
	return t
end
function Inst.FindFirstChild(o, n, recursive)
	for _, c in ipairs(o._children) do if c._p.Name == n then return c end end
	if recursive then
		for _, c in ipairs(o._children) do local f = Inst.FindFirstChild(c, n, true) if f then return f end end
	end
	return nil
end
function Inst.FindFirstChildOfClass(o, cls) for _, c in ipairs(o._children) do if c.ClassName == cls then return c end end end
function Inst.FindFirstChildWhichIsA(o, cls) for _, c in ipairs(o._children) do if isA(c, cls) then return c end end end
function Inst.WaitForChild(o, n)
	local c = Inst.FindFirstChild(o, n)
	if not c then error("WaitForChild would wait forever for " .. n .. " in " .. o._p.Name, 2) end
	return c
end
function Inst.IsDescendantOf(o, a)
	local p = rawget(o, "_parent")
	while p do if p == a then return true end p = rawget(p, "_parent") end
	return false
end
function Inst.IsAncestorOf(o, x) return Inst.IsDescendantOf(x, o) end
function Inst.Destroy(o)
	if rawget(o, "_destroyed") then return end
	for _, c in ipairs(Inst.GetChildren(o)) do Inst.Destroy(c) end
	local old = rawget(o, "_parent")
	if old then for i, c in ipairs(old._children) do if c == o then table.remove(old._children, i) break end end end
	rawset(o, "_parent", nil)
	rawset(o, "_destroyed", true)
end
function Inst.ClearAllChildren(o) for _, c in ipairs(Inst.GetChildren(o)) do Inst.Destroy(c) end end
function Inst.SetAttribute(o, k, v)
	assert(type(k) == "string" and k:match("^[%w_]+$"), "bad attribute name " .. tostring(k))
	local t = type(v)
	assert(v == nil or t == "string" or t == "number" or t == "boolean" or (t == "table" and (getmetatable(v) == V or v.R)),
		"attribute " .. k .. " has a type attributes can't hold")
	o._attrs[k] = v
end
function Inst.GetAttribute(o, k) return o._attrs[k] end
function Inst.GetAttributes(o) local t = {} for k, v in pairs(o._attrs) do t[k] = v end return t end
function Inst.GetPivot(o)
	if PARTS[o.ClassName] then return o._p.CFrame end
	if o._p.PrimaryPart then return o._p.PrimaryPart._p.CFrame end
	if o._p.WorldPivot then return o._p.WorldPivot end
	error("GetPivot: no PrimaryPart on " .. o._p.Name)
end
function Inst.PivotTo(o, target)
	local delta = target * inverse(Inst.GetPivot(o))
	for _, d in ipairs(Inst.GetDescendants(o)) do if PARTS[d.ClassName] then d._p.CFrame = delta * d._p.CFrame end end
end
function Inst.Clone(o)
	local c = newInst(o.ClassName)
	for k, v in pairs(o._p) do c._p[k] = v end
	for k, v in pairs(o._attrs) do c._attrs[k] = v end
	for _, ch in ipairs(o._children) do local cc = Inst.Clone(ch); cc.Parent = c end
	return c
end
-- parts
function Inst.SetNetworkOwner(o, who)
	if o._p.Anchored then error("SetNetworkOwner on an anchored part") end
	if not Inst.IsDescendantOf(o, workspace) then error("SetNetworkOwner: not in Workspace") end
end
-- humanoids
function Inst.MoveTo(h, pos, part) rawset(h, "_move", {to = pos}) end
function Inst.Move(h, dir) rawset(h, "_move", (dir.Magnitude > 0) and {dir = dir} or nil) end
function Inst.TakeDamage(h, n) h.Health = h._p.Health - n end
function Inst.SetStateEnabled(h, state, on) assert(state.EnumType == "HumanoidStateType") h._states[state.Name] = on end
function Inst.ChangeState(h, state) assert(state.EnumType == "HumanoidStateType") end
function Inst.GetState(h) return Enum.HumanoidStateType.Running end
-- bindables
function Inst.Fire(e, ...) signal(e, "Event"):Fire(...) end
-- sounds
function Inst.Play(s) SIM.sounds = (SIM.sounds or 0) + 1 end
function Inst.Emit(e, n) assert(type(n) == "number") SIM.emits = (SIM.emits or 0) + n end

-- animation tracks: time advances with SIM.step, markers fire as they are passed
SEQUENCES = {} -- content id -> {length, loop, markers = {{t, name}}}
local Track = {}
Track.__index = function(t, k)
	local m = rawget(Track, k)
	if m then return m end
	if k == "Stopped" or k == "Ended" or k == "DidLoop" or k == "KeyframeReached" then
		local s = t._signals[k]
		if not s then s = Signal.new(); t._signals[k] = s end
		return s
	end
	if k == "Length" then return t._seq.length end
	if k == "TimePosition" then return t._time end
	if k == "Speed" then return t._speed end
	if k == "WeightCurrent" then return t._playing and 1 or 0 end
	error("AnimationTrack." .. tostring(k) .. " is not a valid member", 2)
end
Track.__newindex = function(t, k, v)
	if k == "Priority" then assert(v.EnumType == "AnimationPriority") rawset(t, "_priority", v) return end
	if k == "Looped" then rawset(t, "_looped", v) return end
	if k == "TimePosition" then rawset(t, "_time", v) return end
	error("cannot set AnimationTrack." .. tostring(k), 2)
end
TRACKS = {}
function Track:Play(fade, weight, speed)
	self._playing = true
	self._time = 0
	if speed then self._speed = speed end
	self._plays = self._plays + 1
	SIM.played = SIM.played or {}
	SIM.played[self._name] = (SIM.played[self._name] or 0) + 1
end
function Track:Stop(fade)
	if self._playing then
		self._playing = false
		self.Stopped:Fire()
	end
end
function Track:AdjustSpeed(s) assert(type(s) == "number" and s == s) self._speed = s end
function Track:AdjustWeight(w) assert(type(w) == "number") end
function Track:GetMarkerReachedSignal(name)
	local found = false
	for _, m in ipairs(self._seq.markers) do if m[2] == name then found = true end end
	if not found then error("the animation " .. self._name .. " has no marker " .. name, 2) end
	local s = self._markers[name]
	if not s then s = Signal.new(); self._markers[name] = s end
	return s
end
function Track:_step(dt)
	if not self._playing then return end
	local t0, t1 = self._time, self._time + dt * self._speed
	local len = self._seq.length
	for _, m in ipairs(self._seq.markers) do
		if m[1] > t0 and m[1] <= t1 or (t0 == 0 and m[1] == 0) then
			local s = self._markers[m[2]]
			if s then s:Fire(m[2]) end
		end
	end
	if t1 >= len then
		if self._looped then
			t1 = t1 - len
			for _, m in ipairs(self._seq.markers) do
				if m[1] <= t1 then local s = self._markers[m[2]] if s then s:Fire(m[2]) end end
			end
		else
			self._time = len
			self._playing = false
			self.Stopped:Fire()
			return
		end
	end
	self._time = t1
end
Track.__index = (function(old) return function(t, k)
	if k == "IsPlaying" then return t._playing end
	if k == "Priority" then return t._priority end
	if k == "Looped" then return t._looped end
	return old(t, k)
end end)(Track.__index)

function Inst.LoadAnimation(animator, anim)
	assert(animator.ClassName == "Animator" or animator.ClassName == "Humanoid")
	local id = anim._p.AnimationId
	local seq = SEQUENCES[id]
	if not seq then error("LoadAnimation: unknown animation id " .. tostring(id)) end
	local t = setmetatable({_seq = seq, _name = anim._p.Name, _time = 0, _speed = 1, _playing = false, _looped = seq.loop,
		_markers = {}, _signals = {}, _plays = 0}, Track)
	table.insert(TRACKS, t)
	return t
end

Instance = {new = function(class, parent)
	if not CREATABLE[class] then error("Instance.new: class " .. tostring(class) .. " is not in the mock (a typo?)", 2) end
	local o = newInst(class)
	if parent then o.Parent = parent end
	return o
end}

-- ---------------------------------------------------------------- the data model

game = newInst("Folder", {Name = "game"})
workspace = newInst("Folder", {Name = "Workspace"})
Workspace = workspace
rawset(workspace, "_parent", game)
table.insert(game._children, workspace)
local camera = {Focus = CFrame.new(10, 0, 20), CFrame = CFrame.new(10, 12, 60)}
local wsExtra = {
	CurrentCamera = camera,
	Raycast = function(_, origin, dir, params)
		-- flat ground at y = 0
		if dir.Y < 0 and origin.Y > 0 then
			local k = -origin.Y / dir.Y
			if k <= 1 then return {Position = origin + dir * k, Normal = vec(0, 1, 0), Instance = workspace} end
		end
		return nil
	end,
}
local wsMeta = getmetatable(workspace)
setmetatable(workspace, {__index = function(o, k) if wsExtra[k] then return wsExtra[k] end return wsMeta.__index(o, k) end,
	__newindex = wsMeta.__newindex, __tostring = wsMeta.__tostring})

PLAYERS = {}
local Heartbeat = Signal.new()
local services = {
	ServerStorage = newInst("Folder", {Name = "ServerStorage"}),
	ReplicatedStorage = newInst("Folder", {Name = "ReplicatedStorage"}),
	ChangeHistoryService = {SetWaypoint = function() end},
	Selection = {Set = function() end},
	Players = {GetPlayers = function() local t = {} for i, p in ipairs(PLAYERS) do t[i] = p end return t end},
	RunService = {Heartbeat = Heartbeat, Stepped = Signal.new(), IsStudio = function() return true end,
		IsServer = function() return true end},
	Debris = {AddItem = function(_, item, t) task.delay(t or 10, function() item:Destroy() end) end},
	TweenService = {Create = function(_, inst, info, goal)
		assert(info and info.Time, "TweenService:Create needs a TweenInfo")
		for k in pairs(goal) do assert(P[inst.ClassName][k], "tween of a property " .. inst.ClassName .. " lacks: " .. k) end
		return {Play = function() task.delay(info.Time, function() for k, v in pairs(goal) do inst[k] = v end end) end,
			Cancel = function() end, Completed = Signal.new()}
	end},
	KeyframeSequenceProvider = {RegisterKeyframeSequence = function(_, seq)
		assert(seq.ClassName == "KeyframeSequence")
		local id = "active://" .. seq._p.Name
		SEQUENCES[id] = seq._seq
		return id
	end},
}
for _, n in ipairs({"ServerStorage", "ReplicatedStorage"}) do
	rawset(services[n], "_parent", game)
	table.insert(game._children, services[n])
end
rawset(game, "GetService", function(_, n)
	local s = services[n]
	if not s then error("game:GetService: " .. tostring(n) .. " is not in the mock", 2) end
	return s
end)

-- ---------------------------------------------------------------- running time

-- one simulated frame: due threads, Heartbeat, animation tracks, simple movement
function SIM.step(dt)
	SIM.t = SIM.t + dt
	SIM.frame = SIM.frame + 1
	for _, t in ipairs(TRACKS) do t:_step(dt) end
	-- humanoids walk towards their MoveTo point
	for _, h in ipairs(SIM.humanoids or {}) do
		local root = h._root
		if root and not root._p.Anchored and not rawget(root, "_destroyed") then
			local v = vec(0, 0, 0)
			if h._move and h._move.to then
				local d = h._move.to - root._p.CFrame.p
				d = vec(d.X, 0, d.Z)
				if d.Magnitude > 0.5 then v = d.Unit * h._p.WalkSpeed end
			elseif h._move and h._move.dir then
				v = h._move.dir.Unit * h._p.WalkSpeed
			end
			root._p.AssemblyLinearVelocity = v
			if v.Magnitude > 0 then
				local p = root._p.CFrame.p + v * dt
				if h._p.AutoRotate then
					root._p.CFrame = CFrame.lookAt(p, p + v)
				else
					root._p.CFrame = cf(p, root._p.CFrame.r)
				end
				-- carry the rest of the model along
				local model = rawget(h, "_parent")
				for _, d in ipairs(model:GetDescendants()) do
					if PARTS[d.ClassName] and d ~= root then d._p.CFrame = cf(d._p.CFrame.p + v * dt, d._p.CFrame.r) end
				end
			end
		end
	end
	Heartbeat:Fire(dt)
	local due = {}
	local keep = {}
	for _, th in ipairs(SIM.threads) do
		if th.at <= SIM.t + 1e-9 then table.insert(due, th) else table.insert(keep, th) end
	end
	SIM.threads = keep
	table.sort(due, function(a, b) return a.at < b.at end)
	for _, th in ipairs(due) do
		if coroutine.status(th.co) == "suspended" then
			if th.args then resume(th.co, table.unpack(th.args)) else resume(th.co) end
		end
	end
end
