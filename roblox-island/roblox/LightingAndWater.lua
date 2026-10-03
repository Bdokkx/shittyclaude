-- Paste this whole thing into Studio's Command Bar (View > Command Bar) after inserting
-- any of the island .rbxm files (VoxelIsland, DesertCoast, FrostCoast, VolcanicIsland, CoralReef).
-- It:
--   1. moves the default Baseplate out of the way (its top sits at water level and flickers)
--   2. for every inserted island: removes its placeholder Ocean part and fills real terrain water
--   3. sets up bright lighting + clear turquoise water like the reference
local ServerStorage = game:GetService("ServerStorage")
local bp = workspace:FindFirstChild("Baseplate")
if bp and bp:IsA("BasePart") then
	bp.Parent = ServerStorage
	print("[VoxelIsland] moved the default Baseplate to ServerStorage")
end

for _, map in ipairs(workspace:GetChildren()) do
	local anchor = map:IsA("Model") and map:FindFirstChild("VoxelAnchor")
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
				local local_ = Vector3.new(wmin.X + (a + 0.5) * tx, (wmin.Y + wmax.Y) / 2, wmin.Z + (b + 0.5) * tz)
				workspace.Terrain:FillBlock(anchor.CFrame * CFrame.new(local_), Vector3.new(tx, size.Y, tz),
					Enum.Material.Water)
			end
		end
		print("[VoxelIsland] water filled around " .. map.Name)
	end
end

local Lighting = game:GetService("Lighting")
Lighting.Technology = Enum.Technology.Future
Lighting.ClockTime = 14.2
Lighting.GeographicLatitude = 30
Lighting.Brightness = 2.6
Lighting.Ambient = Color3.fromRGB(96, 104, 128)
Lighting.OutdoorAmbient = Color3.fromRGB(150, 158, 182)
Lighting.EnvironmentDiffuseScale = 0.6
Lighting.EnvironmentSpecularScale = 0.3
Lighting.GlobalShadows = true
Lighting.ShadowSoftness = 0.25
local function ensure(class, name)
	local o = Lighting:FindFirstChild(name) or Instance.new(class)
	o.Name = name
	o.Parent = Lighting
	return o
end
local atmo = ensure("Atmosphere", "VoxelAtmosphere")
atmo.Density, atmo.Offset, atmo.Haze, atmo.Glare = 0.28, 0.15, 0.6, 0.2
atmo.Color, atmo.Decay = Color3.fromRGB(205, 225, 245), Color3.fromRGB(120, 150, 190)
local cc = ensure("ColorCorrectionEffect", "VoxelColor")
cc.Saturation, cc.Contrast, cc.Brightness = 0.08, 0.08, 0
cc.TintColor = Color3.fromRGB(255, 255, 255)
local bloom = ensure("BloomEffect", "VoxelBloom")
bloom.Intensity, bloom.Size, bloom.Threshold = 0.15, 22, 2
local rays = ensure("SunRaysEffect", "VoxelSunRays")
rays.Intensity, rays.Spread = 0.02, 0.6
local t = workspace.Terrain
t.WaterColor = Color3.fromRGB(24, 118, 168)
t.WaterTransparency, t.WaterReflectance, t.WaterWaveSize, t.WaterWaveSpeed = 0.75, 0.25, 0.08, 6
print("[VoxelIsland] water + lighting ready")
