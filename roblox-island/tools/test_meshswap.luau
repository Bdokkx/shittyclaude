-- Offline test for roblox/MeshSwap.lua (run with Lune):
--   lune run tools/test_meshswap.luau [lying] [terrain]
-- Loads every map (.rbxm) into a fake DataModel, fakes the 3D imports (rock meshes + every
-- island's terrain) with ".001" name suffixes and wrong units (optionally laid on their side),
-- runs MeshSwap and checks every piece lands exactly where it should, the blocky ground turns
-- into invisible collision, cliffs are parked, accents stay; then re-runs and undoes.
local fs = require("@lune/fs")
local luau = require("@lune/luau")
local roblox = require("@lune/roblox")
local process = require("@lune/process")
local Instance, CFrame, Vector3, Color3, Enum = roblox.Instance, roblox.CFrame, roblox.Vector3, roblox.Color3, roblox.Enum

local LYING = table.find(process.args, "lying") ~= nil
local TERRAIN_MODE = table.find(process.args, "terrain") ~= nil   -- optional whole-island terrain mesh mode
print((LYING and "== import laid on its side ==" or "== normal import ==") .. (TERRAIN_MODE and " + terrain mesh" or ""))
local ISLANDS = { "VoxelIsland", "DesertCoast", "FrostCoast", "VolcanicIsland" }

local game = Instance.new("DataModel")
local ws = game:GetService("Workspace")
local ss = game:GetService("ServerStorage")
for _, name in { "VoxelIsland", "CoralReef", "DesertCoast", "FrostCoast", "VolcanicIsland" } do
	for _, inst in roblox.deserializeModel(fs.readFile("roblox/" .. name .. ".rbxm")) do
		inst.Parent = ws
	end
end

local src = fs.readFile("roblox/MeshSwap.lua")
if TERRAIN_MODE then
	src = src:gsub("local TERRAIN_MESH = false", "local TERRAIN_MESH = true")
end
local warnings = {}
local function env()
	return {
		game = game, workspace = ws, Instance = Instance, CFrame = CFrame, Vector3 = Vector3, Color3 = Color3,
		Enum = Enum, print = print, warn = function(...) table.insert(warnings, table.concat({ ... }, " ")) end,
		pcall = pcall, ipairs = ipairs, pairs = pairs, next = next, table = table, math = math, string = string,
		tostring = tostring, type = type,
	}
end
local PIECES = luau.load(src:match("(local PIECES = %b{})") .. "\nreturn PIECES", { environment = env() })()
local TERRAIN = luau.load(src:match("(local TERRAIN = %b{})") .. "\nreturn TERRAIN", { environment = env() })()
print("rock assets:", (function() local n = 0 for _ in PIECES do n += 1 end return n end)(), "terrain pieces:", #TERRAIN)

local function fakeSize(want)
	local sz = want * 3.57
	return LYING and Vector3.new(sz.X, sz.Z, sz.Y) or sz
end
local imported = Instance.new("Model")
imported.Name = "VoxelRockMeshes"
for name, pieces in PIECES do
	for _, piece in pieces do
		local mp = Instance.new("MeshPart")
		mp.Name = name .. piece.suffix .. (piece.suffix == "_Rock" and ".001" or "")
		mp.Size = fakeSize(piece.max - piece.min)
		mp.Parent = imported
	end
end
imported.Parent = ws
for _, island in ISLANDS do
	local m = Instance.new("Model")
	m.Name = island .. "_Terrain"
	for _, t in TERRAIN do
		if t.map == island then
			local mp = Instance.new("MeshPart")
			mp.Name = t.name
			mp.Size = fakeSize(t.max - t.min)
			mp.Parent = m
		end
	end
	m.Parent = ws
end

local function rocks(meshOnly)
	local n = 0
	for _, map in ws:GetChildren() do
		if map:FindFirstChild("VoxelAnchor") or map.Name == "CoralReef" then
			for _, d in map:GetDescendants() do
				if d:IsA("Model") and d:GetAttribute("VoxelAsset") and PIECES[d:GetAttribute("VoxelAsset")]
					and (d:GetAttribute("VoxelMesh") == true) == meshOnly then
					n += 1
				end
			end
		end
	end
	return n
end
local nAccents = {}
for _, island in ISLANDS do
	nAccents[island] = #ws[island].Accents:GetChildren()
end
local nRocks = rocks(false)
print("part rocks to swap:", nRocks)

luau.load(src, { environment = env() })()
assert(rocks(true) == nRocks and rocks(false) == 0, ("swapped %d of %d rocks"):format(rocks(true), nRocks))

local maxErr = 0
for _, island in ISLANDS do
	local map = ws[island]
	local tm = map:FindFirstChild("TerrainMesh")
	if not TERRAIN_MODE then
		-- default: parts terrain stays exactly as built, only the rocks became meshes
		assert(tm == nil, island .. ": terrain mesh placed although TERRAIN_MESH = false")
		assert(map:FindFirstChild("Cliffs"), island .. ": part cliffs must stay")
		for _, g in map.Ground:GetChildren() do
			assert(g.Transparency == 0, island .. ": ground must stay visible")
		end
		assert(#map.Accents:GetChildren() == nAccents[island], island .. ": accents must stay")
		print(("  %-15s part terrain kept (%d cliff parts)"):format(island, #map.Cliffs:GetDescendants()))
		continue
	end
	local base = map.VoxelAnchor.CFrame
	local n = 0
	for _, t in TERRAIN do
		if t.map == island then
			n += 1
			local p = tm:FindFirstChild(t.name)
			assert(p, "missing terrain piece " .. t.name)
			local want = t.max - t.min
			if LYING then
				want = Vector3.new(want.X, want.Z, want.Y)
			end
			maxErr = math.max(maxErr, (p.Size - want).Magnitude,
				(p.CFrame.Position - (base * CFrame.new((t.min + t.max) * 0.5)).Position).Magnitude)
			assert(not p.CanCollide)
			if t.material == "Neon" then
				assert(p.Material == Enum.Material.Neon, "lava terrain should glow")
			end
		end
	end
	assert(#tm:GetChildren() == n, island .. ": wrong terrain piece count")
	for _, g in map.Ground:GetChildren() do
		assert(g.Transparency == 1 and g.CanCollide, island .. ": ground should be invisible but solid")
	end
	assert(map:FindFirstChild("Cliffs") == nil, island .. ": cliffs not parked")
	assert(#map.Accents:GetChildren() == nAccents[island], island .. ": accents must stay")
	assert(map:FindFirstChild("Paths") and map:FindFirstChild("Shallows"), island .. ": paths/shallows must stay")
	print(("  %-15s %3d terrain meshes, %4d accent parts kept"):format(island, n, nAccents[island]))
end
-- rock pieces: every mesh rock sits where its part version was
for _, map in ws:GetChildren() do
	for _, d in map:GetDescendants() do
		if d:IsA("Model") and d:GetAttribute("VoxelMesh") and d:GetAttribute("VoxelAsset") then
			local pieces = PIECES[d:GetAttribute("VoxelAsset")]
			local cf, sc = d:GetAttribute("VoxelPivot"), d:GetAttribute("VoxelScale")
			for _, piece in pieces do
				local p = d:FindFirstChild(d:GetAttribute("VoxelAsset") .. piece.suffix)
				assert(p, "missing rock piece")
				maxErr = math.max(maxErr, (p.CFrame.Position - (cf * CFrame.new((piece.min + piece.max) * 0.5 * sc)).Position).Magnitude)
			end
		end
	end
end
print(("max placement error %.5f studs"):format(maxErr))
assert(maxErr < 1e-3)

luau.load(src, { environment = env() })()
assert(rocks(true) == nRocks and rocks(false) == 0, "second run changed the count")
print("re-run OK")

luau.load((src:gsub("local UNDO = false", "local UNDO = true")), { environment = env() })()
assert(rocks(true) == 0 and rocks(false) == nRocks, "undo failed")
for _, island in ISLANDS do
	local map = ws[island]
	assert(map:FindFirstChild("TerrainMesh") == nil and map:FindFirstChild("Cliffs"), island .. ": terrain undo failed")
	for _, g in map.Ground:GetChildren() do
		assert(g.Transparency == 0, island .. ": ground not visible after undo")
	end
end
print("undo OK; warnings:", #warnings)
for _, w in warnings do
	print("  warn:", w)
end
