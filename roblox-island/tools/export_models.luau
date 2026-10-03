-- Runs the generated Roblox builder offline (Lune) and saves the results as
-- Roblox model files you can drag into Studio.
local fs = require("@lune/fs")
local luau = require("@lune/luau")
local roblox = require("@lune/roblox")
local process = require("@lune/process")

local root = process.args[1] or "."
local Instance, CFrame, Vector3, Color3, Enum =
	roblox.Instance, roblox.CFrame, roblox.Vector3, roblox.Color3, roblox.Enum

local function loadBuilder(path)
	local source = fs.readFile(path)
	local exported
	local G = { __VOXEL_EXPORT = function(b) exported = b end }
	local env = {
		Instance = Instance, CFrame = CFrame, Vector3 = Vector3, Color3 = Color3, Enum = Enum,
		math = math, table = table, string = string, os = os,
		pairs = pairs, ipairs = ipairs, print = print, type = type, typeof = typeof,
		tostring = tostring, tonumber = tonumber, assert = assert, error = error,
		pcall = pcall, select = select, setmetatable = setmetatable, _G = G,
	}
	luau.load(source, { debugName = path, environment = env })()
	assert(exported, "builder did not hand over its API: " .. path)
	exported.CONFIG.UseTerrainWater = false
	exported.CONFIG.YieldEvery = 0
	return exported, source
end

local out = root .. "/roblox"
local function count(inst)
	local n = 0
	for _, d in inst:GetDescendants() do
		if d:IsA("BasePart") then n += 1 end
	end
	return n
end
local function save(inst, name)
	fs.writeFile(out .. "/" .. name .. ".rbxm", roblox.serializeModel({ inst }, false))
	print(("%-20s %6d parts"):format(name, count(inst)))
end

local holder = Instance.new("Folder")
for _, file in fs.readDir(out .. "/builders") do
	local name = file:match("^(.-)Builder%.server%.lua$")
	if name then
		local B, source = loadBuilder(out .. "/builders/" .. file)
		local entry = B.MAPS[1]
		save(B.buildMap(entry.name, entry.data, entry.origin, holder), entry.name)
		local script = Instance.new("Script")
		script.Name = name .. "Builder"
		script.Source = source
		fs.writeFile(out .. "/builders/" .. name .. "Builder.rbxmx", roblox.serializeModel({ script }, true))
	end
end
local L = loadBuilder(out .. "/builders/AssetLibrary.lua")
save(L.buildAssetLibrary(holder, Vector3.new(0, 0, -400)), "VoxelAssetLibrary")
