-- lune run tools/test_animate_scenery.luau roblox/Maps.rbxm
-- Run AnimateScenery against the exported October map with a fake RunService, and check that ghosts/bats move.
local fs = require("@lune/fs")
local luau = require("@lune/luau")
local roblox = require("@lune/roblox")
local process = require("@lune/process")
local CFrame, Vector3 = roblox.CFrame, roblox.Vector3
local maps = roblox.deserializeModel(fs.readFile(process.args[1]))[1]
local map = maps:FindFirstChild("October")
local sc = map:FindFirstChild("AnimateScenery")
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
	CFrame = CFrame, Vector3 = Vector3, math = math, table = table, typeof = typeof, print = print,
}
local fn = luau.load(sc.Source, { debugName = "AnimateScenery", environment = env })
fn()
assert(beat, "no Heartbeat connection")

local function snapshot()
	local s = {}
	for _, m in map.Scenery:GetChildren() do
		if m.Name == "Ghost" or m.Name == "Bat" then
			for _, p in m:GetDescendants() do table.insert(s, p.CFrame.Position) end
		end
	end
	return s
end
local a = snapshot()
for i = 1, 90 do beat(1 / 30) end
local b = snapshot()
local moved, n, maxd = 0, 0, 0
for i, pos in a do
	n += 1
	local d = (b[i] - pos).Magnitude
	if d > 0.05 then moved += 1 end
	maxd = math.max(maxd, d)
end
-- a static part elsewhere must not move
print(string.format("%d / %d ghost+bat parts moved after 3 s (max %.1f studs)", moved, n, maxd))
assert(moved > n * 0.9, "animation did not move the parts")
assert(maxd < 80, "something flew off")
