-- Offline test for roblox/MeshSwap.lua (run with Lune): loads both maps into a fake
-- DataModel, fakes a 3D import whose part names have ".001" suffixes and whose sizes are
-- in different units, runs MeshSwap, and checks every swapped piece lands exactly where
-- the part version was. Then runs it again (idempotent) and with UNDO = true.
local fs = require("@lune/fs")
local luau = require("@lune/luau")
local roblox = require("@lune/roblox")
local Instance, CFrame, Vector3, Color3, Enum = roblox.Instance, roblox.CFrame, roblox.Vector3, roblox.Color3, roblox.Enum

local LYING = require("@lune/process").args[1] == "lying"
print(LYING and "== import laid on its side ==" or "== normal import ==")
local game = Instance.new("DataModel")
local ws = game:GetService("Workspace")
local ss = game:GetService("ServerStorage")
for _, f in { "roblox/VoxelIsland.rbxm", "roblox/CoralReef.rbxm" } do
	for _, inst in roblox.deserializeModel(fs.readFile(f)) do
		inst.Parent = ws
	end
end
local base = Instance.new("Part")
base.Name = "Baseplate"
base.Parent = ws

local src = fs.readFile("roblox/MeshSwap.lua")
local warnings = {}
local function env()
	return {
		game = game, workspace = ws, Instance = Instance, CFrame = CFrame, Vector3 = Vector3, Color3 = Color3,
		Enum = Enum, print = print, warn = function(...) table.insert(warnings, table.concat({ ... }, " ")) end,
		pcall = pcall, ipairs = ipairs, pairs = pairs, next = next, table = table, math = math, string = string,
		tostring = tostring, type = type,
	}
end
-- grab the PIECES table by running the generated header only
local header = src:match("(local PIECES = %b{})")
local PIECES = luau.load(header .. "\nreturn PIECES", { environment = env() })()
local theader = src:match("(local TERRAIN = %b{})")
local TERRAIN = luau.load(theader .. "\nreturn TERRAIN", { environment = env() })()
print("terrain pieces:", #TERRAIN)

-- fake import: one MeshPart per piece, wrong units (x3.57), odd names, random placement
local imported = Instance.new("Model")
imported.Name = "VoxelRockMeshes"
local k = 0
for name, pieces in PIECES do
	local group = Instance.new("Model")
	group.Name = name
	group.Parent = imported
	for _, piece in pieces do
		k += 1
		local mp = Instance.new("MeshPart")
		mp.Name = name .. piece.suffix .. (piece.suffix == "_Rock" and ".001" or "")
		local sz = (piece.max - piece.min) * 3.57
		if LYING then -- pretend the importer laid every mesh on its side
			sz = Vector3.new(sz.X, sz.Z, sz.Y)
		end
		mp.Size = sz
		mp.CFrame = CFrame.new(k * 100, 50, 0)
		mp.Parent = group
	end
end
imported.Parent = ws
local timport = Instance.new("Model")
timport.Name = "IslandTerrain"
for _, t in TERRAIN do
	local mp = Instance.new("MeshPart")
	mp.Name = t.name
	local sz = (t.max - t.min) * 3.57
	if LYING then
		sz = Vector3.new(sz.X, sz.Z, sz.Y)
	end
	mp.Size = sz
	mp.Parent = timport
end
timport.Parent = ws
local island = ws.VoxelIsland
local nGround = #island.Ground:GetChildren()

local function tagged(meshOnly)
	local n = 0
	for _, mapName in { "VoxelIsland", "CoralReef" } do
		for _, d in ws[mapName]:GetDescendants() do
			if d:IsA("Model") and d:GetAttribute("VoxelAsset") and PIECES[d:GetAttribute("VoxelAsset")] then
				if (d:GetAttribute("VoxelMesh") == true) == meshOnly then
					n += 1
				end
			end
		end
	end
	return n
end

-- remember where every part rock was
local expected = {}
for _, mapName in { "VoxelIsland", "CoralReef" } do
	for _, d in ws[mapName]:GetDescendants() do
		local name = d:IsA("Model") and d:GetAttribute("VoxelAsset")
		if name and PIECES[name] then
			local cf = d:FindFirstChild("VoxelRef").CFrame * d:GetAttribute("VoxelRefOffset")
			table.insert(expected, { name = name, cf = cf, s = d:GetAttribute("VoxelScale") })
		end
	end
end
print("part rocks to swap:", #expected)

luau.load(src, { environment = env() })()
assert(tagged(true) == #expected, ("swapped %d of %d"):format(tagged(true), #expected))
assert(tagged(false) == 0, "part rocks left in the maps")

-- every mesh piece must sit exactly on its expected box
local maxErr = 0
for _, mapName in { "VoxelIsland", "CoralReef" } do
	for _, d in ws[mapName]:GetDescendants() do
		if d:IsA("Model") and d:GetAttribute("VoxelMesh") and d:GetAttribute("VoxelAsset") then
			local name = d:GetAttribute("VoxelAsset")
			local cf = d:GetAttribute("VoxelPivot")
			local match
			for _, e in expected do
				if e.name == name and (e.cf.Position - cf.Position).Magnitude < 1e-3 then
					match = e
				end
			end
			assert(match, "no source rock for a mesh " .. name)
			for _, piece in PIECES[name] do
				local p = d:FindFirstChild(name .. piece.suffix)
				assert(p and p:IsA("MeshPart"), "missing piece " .. name .. piece.suffix)
				local wantSize = (piece.max - piece.min) * match.s
				if LYING then
					wantSize = Vector3.new(wantSize.X, wantSize.Z, wantSize.Y)
					-- the part's local +Z (the mesh's up) must point along the rock's up axis
					local up = (match.cf.Rotation * Vector3.new(0, 1, 0))
					assert((p.CFrame.Rotation * Vector3.new(0, 0, 1) - up).Magnitude < 1e-3, name .. " not stood up")
				end
				local wantPos = (match.cf * CFrame.new((piece.min + piece.max) * 0.5 * match.s)).Position
				maxErr = math.max(maxErr, (p.Size - wantSize).Magnitude, (p.CFrame.Position - wantPos).Magnitude)
				assert(p.Anchored, "not anchored")
			end
		end
	end
end
-- terrain: every piece placed relative to the anchor, ground hidden (but still solid), cliffs parked
local tm = island:FindFirstChild("TerrainMesh")
assert(tm and #tm:GetChildren() == #TERRAIN, "terrain mesh not placed")
local base = island.VoxelAnchor.CFrame
for _, t in TERRAIN do
	local p = tm:FindFirstChild(t.name)
	local want = (t.max - t.min)
	if LYING then
		want = Vector3.new(want.X, want.Z, want.Y)
	end
	maxErr = math.max(maxErr, (p.Size - want).Magnitude,
		(p.CFrame.Position - (base * CFrame.new((t.min + t.max) * 0.5)).Position).Magnitude)
	assert(not p.CanCollide, "terrain mesh should not collide")
end
for _, g in island.Ground:GetChildren() do
	assert(g.Transparency == 1 and g.CanCollide, "ground should be invisible but solid")
end
assert(island:FindFirstChild("Cliffs") == nil and ss.VoxelPartRocks:FindFirstChild("Cliffs"), "cliffs not parked")
assert(island:FindFirstChild("Paths") and island:FindFirstChild("Shallows"), "paths/shallows must stay")
print(("swapped %d rocks + %d terrain pieces, max placement error %.5f studs"):format(tagged(true), #TERRAIN, maxErr))
assert(maxErr < 1e-3)
assert(#ss.VoxelPartRocks:GetChildren() == #expected + 1)

-- second run must not double up
luau.load(src, { environment = env() })()
assert(tagged(true) == #expected and tagged(false) == 0, "second run changed the count")
print("re-run OK")

-- undo puts the part rocks back
luau.load((src:gsub("local UNDO = false", "local UNDO = true")), { environment = env() })()
assert(tagged(true) == 0 and tagged(false) == #expected, "undo failed")
assert(island:FindFirstChild("TerrainMesh") == nil and island:FindFirstChild("Cliffs"), "terrain undo failed")
for _, g in island.Ground:GetChildren() do
	assert(g.Transparency == 0, "ground not visible again after undo")
end
assert(#island.Ground:GetChildren() == nGround)
print("undo OK; warnings:", #warnings)
for _, w in warnings do print("  warn:", w) end
