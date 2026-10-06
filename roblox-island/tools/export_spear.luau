-- Runs a spearfishing island builder (roblox/builders/<Map>Builder.server.lua) offline in Lune,
-- exactly as Studio would, and saves the result as roblox/<Map>.rbxm (+ the builder as .rbxmx).
--   lune run tools/export_spear.luau <repo-root> VoxelIsland [DesertCoast ...]
local fs = require("@lune/fs")
local luau = require("@lune/luau")
local roblox = require("@lune/roblox")
local process = require("@lune/process")

local root = process.args[1] or "."
local maps = { table.unpack(process.args, 2) }

for _, name in maps do
	local path = root .. "/roblox/builders/" .. name .. "Builder.server.lua"
	local source = fs.readFile(path)
	local game = roblox.Instance.new("DataModel")
	local env = {
		game = game, workspace = game:GetService("Workspace"),
		Instance = roblox.Instance, CFrame = roblox.CFrame, Vector3 = roblox.Vector3, Color3 = roblox.Color3,
		Enum = roblox.Enum, UDim2 = roblox.UDim2,
		math = math, table = table, string = string, bit32 = bit32, os = os,
		pairs = pairs, ipairs = ipairs, print = print, warn = print, type = type, typeof = typeof,
		tostring = tostring, tonumber = tonumber, assert = assert, error = error, pcall = pcall,
		select = select, setmetatable = setmetatable, next = next,
		task = { wait = function() end },
		_G = { __SPEAR_EXPORT = true },
	}
	local island = luau.load(source, { debugName = name, environment = env })()
	assert(island and island:IsA("Model"), "builder did not return the island model")
	local parts, hidden = 0, 0
	for _, d in island:GetDescendants() do
		if d:IsA("BasePart") then
			parts += 1
			if d.Transparency >= 1 then
				hidden += 1
			end
		end
	end
	-- tier toggle test: Tier1 alone at tier 1, Tier2 at tier 2, Tier2 + Tier3 at tier 3
	local tiers = luau.load(island.IslandTiers.Source, { environment = env })()
	local function shown(model)
		local on, total = 0, 0
		for _, d in model:GetDescendants() do
			if d:IsA("BasePart") then
				total += 1
				if d.Transparency < 1 then on += 1 end
			end
		end
		return on, total
	end
	for _, case in { { 1, true, false, false }, { 2, false, true, false }, { 3, false, true, true }, { 3, false, true, true } } do
		tiers.SetTier(island, case[1])
		for k, model in { island.Tier1, island.Tier2, island.Tier3 } do
			local on, total = shown(model)
			assert(total > 0, model.Name .. " is empty")
			assert((on > 0) == case[k + 1], ("tier %d: %s shown=%d/%d"):format(case[1], model.Name, on, total))
			if case[k + 1] then
				local opaque = 0
				for _, d in model:GetDescendants() do
					if d:IsA("BasePart") and d.Transparency == (d:GetAttribute("TierT") or 0) then opaque += 1 end
				end
				assert(opaque == total, model.Name .. " did not restore its own transparency")
			end
		end
	end
	print("    tier toggle OK (1 -> Tier1, 2 -> Tier2, 3 -> Tier2+Tier3, re-toggle restores parts)")
	island.Parent = nil
	fs.writeFile(root .. "/roblox/" .. name .. ".rbxm", roblox.serializeModel({ island }, false))
	local script = roblox.Instance.new("Script")
	script.Name = name .. "Builder"
	script.Source = source
	fs.writeFile(root .. "/roblox/builders/" .. name .. "Builder.rbxmx", roblox.serializeModel({ script }, true))
	print(("%-16s %6d parts (%d hidden by the inactive tier)  -> roblox/%s.rbxm"):format(name, parts, hidden, name))
end
