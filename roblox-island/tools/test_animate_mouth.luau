-- lune run tools/test_animate_mouth.luau roblox/MonsterMouth.rbxm
-- Run AnimateMouth against the exported MonsterMouth with a fake RunService: the spiral turns, eyes blink, mist moves.
local fs = require("@lune/fs")
local luau = require("@lune/luau")
local roblox = require("@lune/roblox")
local process = require("@lune/process")
local CFrame, Vector3 = roblox.CFrame, roblox.Vector3
local map = roblox.deserializeModel(fs.readFile(process.args[1]))[1]
local holder = roblox.Instance.new("Folder") -- stands in for Workspace (the script idles when unparented)
map.Parent = holder
local sc = map:FindFirstChild("AnimateMouth")
assert(sc and sc.RunContext.Name == "Client", "script missing / wrong RunContext")

-- Lune instances have no GetPivot/WaitForChild: add small shims through a proxy environment
local function pivotOf(inst)
	if inst:IsA("Model") then
		if inst.PrimaryPart then return inst.PrimaryPart.CFrame end
		local ok, v = pcall(function() return inst.WorldPivot end)
		return ok and v or CFrame.new()
	end
	return inst.CFrame
end
local wrap
local function method(inst, name)
	if name == "GetPivot" then return function() return pivotOf(inst) end end
	if name == "WaitForChild" then return function(_, n) return wrap(inst:FindFirstChild(n)) end end
	if name == "GetChildren" or name == "GetDescendants" then
		return function()
			local out = {}
			for _, c in inst[name](inst) do table.insert(out, wrap(c)) end
			return out
		end
	end
	if name == "IsA" then return function(_, c) return inst:IsA(c) end end
	return nil
end
local cache = {}
function wrap(inst)
	if inst == nil then return nil end
	if cache[inst] then return cache[inst] end
	local p = setmetatable({}, {
		__index = function(_, k)
			local m = method(inst, k)
			if m then return m end
			local v = inst[k]
			if typeof(v) == "Instance" then return wrap(v) end
			return v
		end,
		__newindex = function(_, k, v) inst[k] = v end,
	})
	cache[inst] = p
	return p
end

local beat
local env = {
	game = { GetService = function(_, n) return { Heartbeat = { Connect = function(_, f) beat = f end } } end },
	workspace = { CurrentCamera = nil },
	script = { Parent = wrap(map) },
	CFrame = CFrame, Vector3 = Vector3, math = math, table = table, typeof = typeof, print = print, pairs = pairs,
}
local fn = luau.load(sc.Source, { debugName = "AnimateMouth", environment = env })
fn()
assert(beat, "no Heartbeat connection")

local function collect(name)
	local out = {}
	for _, p in map:GetDescendants() do
		if p:IsA("BasePart") and p.Name == name then table.insert(out, p) end
	end
	return out
end
local swirl, eyes, mist = collect("Swirl"), collect("Eye"), collect("Mist")
local s0, m0 = {}, {}
for i, p in swirl do s0[i] = p.CFrame.Position end
for i, p in mist do m0[i] = p.CFrame.Position end
local blinked = false
for i = 1, 300 do -- 10 s
	beat(1 / 30)
	for _, e in eyes do if e.Transparency >= 1 then blinked = true end end
end
local moved, mmoved, keepR = 0, 0, true
for i, p in swirl do
	local a, b = s0[i], p.CFrame.Position
	if (b - a).Magnitude > 0.05 then moved += 1 end
	local ra, rb = Vector3.new(a.X, 0, a.Z).Magnitude, Vector3.new(b.X, 0, b.Z).Magnitude
	if math.abs(ra - rb) > 0.05 or math.abs(a.Y - b.Y) > 0.01 then keepR = false end
end
for i, p in mist do if (p.CFrame.Position - m0[i]).Magnitude > 0.05 then mmoved += 1 end end
print(string.format("swirl: %d/%d parts turned (radius kept: %s), eyes blinked: %s, mist: %d/%d moved",
	moved, #swirl, tostring(keepR), tostring(blinked), mmoved, #mist))
assert(moved > #swirl * 0.9 and keepR and blinked and mmoved == #mist, "animation check failed")
