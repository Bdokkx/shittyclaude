-- Paste this whole thing into Studio's Command Bar (View > Command Bar) after
-- inserting VoxelIsland.rbxm / CoralReef.rbxm. It:
--   1. removes the placeholder Ocean part and fills real terrain water around the island
--   2. sets up bright, saturated lighting + clear turquoise water like the reference
local island = workspace:FindFirstChild("VoxelIsland")
if island and island:FindFirstChild("Ocean") then island.Ocean:Destroy() end
local origin = island and island:GetPivot().Position or Vector3.zero
workspace.Terrain:FillBlock(CFrame.new(origin + Vector3.new(0, -6, 0)), Vector3.new(520, 12, 520), Enum.Material.Water)

local Lighting = game:GetService("Lighting")
Lighting.Technology = Enum.Technology.Future
Lighting.ClockTime = 14.2
Lighting.GeographicLatitude = 30
Lighting.Brightness = 3.2
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
cc.Saturation, cc.Contrast, cc.Brightness = 0.22, 0.1, 0.02
cc.TintColor = Color3.fromRGB(255, 251, 245)
local bloom = ensure("BloomEffect", "VoxelBloom")
bloom.Intensity, bloom.Size, bloom.Threshold = 0.35, 22, 1.6
local rays = ensure("SunRaysEffect", "VoxelSunRays")
rays.Intensity, rays.Spread = 0.04, 0.6
local t = workspace.Terrain
t.WaterColor = Color3.fromRGB(24, 118, 168)
t.WaterTransparency, t.WaterReflectance, t.WaterWaveSize, t.WaterWaveSpeed = 0.75, 0.25, 0.08, 6
print("[VoxelIsland] water + lighting ready")
