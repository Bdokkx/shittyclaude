-- Runs the generated Roblox builder offline (Lune) and saves the results as
-- Roblox model files you can drag into Studio.
local fs = require("@lune/fs")
local luau = require("@lune/luau")
local roblox = require("@lune/roblox")
local process = require("@lune/process")

local root = process.args[1] or "."
local srcPath = root .. "/roblox/VoxelIslandBuilder.server.lua"
local source = fs.readFile(srcPath)

local Instance, CFrame, Vector3, Color3, Enum =
	roblox.Instance, roblox.CFrame, roblox.Vector3, roblox.Color3, roblox.Enum

local exported
local G = { __VOXEL_EXPORT = function(b) exported = b end }
local env = {
	Instance = Instance, CFrame = CFrame, Vector3 = Vector3, Color3 = Color3, Enum = Enum,
	math = math, table = table, string = string, os = os,
	pairs = pairs, ipairs = ipairs, print = print, type = type, typeof = typeof,
	tostring = tostring, tonumber = tonumber, assert = assert, error = error,
	pcall = pcall, select = select, setmetatable = setmetatable, _G = G,
}
local chunk = luau.load(source, { debugName = "VoxelIslandBuilder", environment = env })
chunk()
assert(exported, "builder did not hand over its API")

local B = exported
B.CONFIG.UseTerrainWater = false
B.CONFIG.YieldEvery = 0

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
save(B.buildMap("VoxelIsland", B.MAPS.Island, Vector3.new(0, 0, 0), holder), "VoxelIsland")
save(B.buildMap("CoralReef", B.MAPS.Reef, Vector3.new(0, 0, 700), holder), "CoralReef")
save(B.buildAssetLibrary(holder, Vector3.new(0, 0, -400)), "VoxelAssetLibrary")

-- the builder script itself, as a drag-in Script
local script = Instance.new("Script")
script.Name = "VoxelIslandBuilder"
script.Source = source
fs.writeFile(out .. "/VoxelIslandBuilder.rbxmx", roblox.serializeModel({ script }, true))
print("VoxelIslandBuilder.rbxmx (Script)")
