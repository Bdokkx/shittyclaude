-- Paste this whole thing into Studio's Command Bar (View > Command Bar) after inserting island .rbxm files.
-- It:
--   1. moves the default Baseplate out of the way (its top sits at water level and flickers)
--   2. puts every inserted island into Workspace.Islands (the folder layout from the style bible)
--   3. fills real terrain water around each island (clear water so the reef shows from the dock)
--   4. applies the lighting preset of the island named in SHOW (each island carries its own preset;
--      call require(island.IslandLighting).Apply(island) when a player teleports there)
local SHOW = "VoxelIsland"

local ServerStorage = game:GetService("ServerStorage")
local bp = workspace:FindFirstChild("Baseplate")
if bp and bp:IsA("BasePart") then
	bp.Parent = ServerStorage
	print("[Islands] moved the default Baseplate to ServerStorage")
end

local islands = workspace:FindFirstChild("Islands") or Instance.new("Folder")
islands.Name = "Islands"
islands.Parent = workspace
for _, m in ipairs(workspace:GetChildren()) do
	if m:IsA("Model") and (m:FindFirstChild("IslandAnchor") or m:FindFirstChild("VoxelAnchor")) then
		m.Parent = islands
	end
end

for _, map in ipairs(islands:GetChildren()) do
	local anchor = map:FindFirstChild("IslandAnchor") or map:FindFirstChild("VoxelAnchor")
	local wmin, wmax = map:GetAttribute("WaterMin"), map:GetAttribute("WaterMax")
	if anchor and wmin and wmax then
		if map:FindFirstChild("Ocean") then
			map.Ocean:Destroy()
		end
		local size = wmax - wmin
		local tiles = math.ceil(math.max(size.X, size.Z) / 512)
		local tx, tz = size.X / tiles, size.Z / tiles
		for a = 0, tiles - 1 do
			for b = 0, tiles - 1 do
				local c = Vector3.new(wmin.X + (a + 0.5) * tx, (wmin.Y + wmax.Y) / 2, wmin.Z + (b + 0.5) * tz)
				workspace.Terrain:FillBlock(anchor.CFrame * CFrame.new(c), Vector3.new(tx, size.Y, tz), Enum.Material.Water)
			end
		end
		print("[Islands] water filled around " .. map.Name)
	end
end

local show = islands:FindFirstChild(SHOW)
local lighting = show and show:FindFirstChild("IslandLighting")
if lighting then
	require(lighting).Apply(show)
	print("[Islands] lighting preset of " .. SHOW .. " applied")
else
	warn("[Islands] " .. SHOW .. " not found - insert roblox/" .. SHOW .. ".rbxm first")
end
pcall(function()
	workspace.StreamingEnabled = true
end)
