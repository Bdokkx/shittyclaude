--[[ @@MAP@@ builder (spearfishing islands)

HOW TO USE (Roblox Studio, no plugin needed)
  1. Put this Script in ServerScriptService and press Play, OR paste it into the Command Bar.
     It builds Workspace.Islands.@@MAP@@ at the origin below.
  2. Or skip this and Insert From File: roblox/@@MAP@@.rbxm (already built from this script).

Folders: Islands/@@MAP@@/{Terrain, Dock, Reef, Buildings, Props, Lighting, Spawns, Tier1, Tier2, Tier3}
Upgrade tiers: Tier1 = humble version, Tier2 = upgraded (also shown at tier 3), Tier3 = extra tier-3 decor.
  Switch with:  require(workspace.Islands.@@MAP@@.IslandTiers).SetTier(workspace.Islands.@@MAP@@, 2)

STUDS: every part uses the same stud look at the same world scale:
  * StudMode = "Inlet"   : Roblox's built-in inset-square surface on every Plastic face (1 square = 1 stud).
  * StudMode = "Variant" : MaterialService.StudInset MaterialVariant (StudsPerTile = 1). Upload
    exports/studs/StudInset_color.png as a Decal and paste its id into StudColorMap (StudNormalMap is optional).
]]
local CONFIG = {
	Origin = Vector3.new(@@ORIGIN@@),
	StartTier = 3,
	StudMode = "Inlet", -- "Inlet" | "Variant" | "None"
	StudColorMap = "", -- e.g. "rbxassetid://123" (Variant mode)
	StudNormalMap = "",
	ApplyLighting = true,
	UseTerrainWater = true,
	ClearExisting = true,
	YieldEvery = 1500,
}

local COLORS = { @@COLORS@@ }
local MATS = { @@MATS@@ }
local FOLDERS = { @@FOLDERS@@ }
-- {sx,sy,sz, x,y,z, rx,ry,rz (deg), color, mat, folder, flags(1=collide,2=shadow)}
local P = {
@@PARTS@@
}
-- [part] = {kind, brightness, range, color}
local LIGHTS = { @@LIGHTS@@ }
local NAMES = { @@NAMES@@ }
local TRANSP = { @@TRANSP@@ }
-- [part] = "portal" | "fire" | "pad"  (particles / touch zones)
local EFFECTS = { @@EFFECTS@@ }
-- {part, text, color, face}
local TEXTS = { @@TEXTS@@ }
local PRESET = { @@PRESET@@ }
local WATER = { @@WATER@@ }

local function c3(i)
	local c = COLORS[i]
	return Color3.fromRGB(c[1], c[2], c[3])
end

local MaterialService = game:GetService("MaterialService")
if CONFIG.StudMode == "Variant" then
	local mv = MaterialService:FindFirstChild("StudInset") or Instance.new("MaterialVariant")
	mv.Name = "StudInset"
	mv.BaseMaterial = Enum.Material.Plastic
	mv.StudsPerTile = 1
	pcall(function()
		if CONFIG.StudColorMap ~= "" then mv.ColorMap = CONFIG.StudColorMap end
		if CONFIG.StudNormalMap ~= "" then mv.NormalMap = CONFIG.StudNormalMap end
	end)
	mv.Parent = MaterialService
end

local islands = workspace:FindFirstChild("Islands")
if not islands then
	islands = Instance.new("Folder")
	islands.Name = "Islands"
	islands.Parent = workspace
end
if CONFIG.ClearExisting and islands:FindFirstChild("@@MAP@@") then
	islands["@@MAP@@"]:Destroy()
end
local root = Instance.new("Model")
root.Name = "@@MAP@@"
local anchor = Instance.new("Part")
anchor.Name = "IslandAnchor"
anchor.Anchored, anchor.CanCollide, anchor.CanQuery, anchor.CanTouch = true, false, false, false
anchor.Transparency = 1
anchor.Size = Vector3.new(1, 1, 1)
anchor.CFrame = CFrame.new(CONFIG.Origin)
anchor.Parent = root
root.PrimaryPart = anchor

local folders = {}
local function folder(path)
	if folders[path] then return folders[path] end
	local parent, name = root, path
	local slash = string.find(path, "/[^/]*$")
	if slash then
		parent = folder(string.sub(path, 1, slash - 1))
		name = string.sub(path, slash + 1)
	end
	local f = Instance.new(string.match(name, "^Tier%d$") and "Model" or "Folder")
	f.Name = name
	f.Parent = parent
	folders[path] = f
	return f
end
for _, f in ipairs({ "Terrain", "Dock", "Reef", "Buildings", "Props", "Lighting", "Spawns", "Tier1", "Tier2", "Tier3" }) do
	folder(f)
end

local origin = CFrame.new(CONFIG.Origin)
local made = {}
for i, d in ipairs(P) do
	local p = Instance.new("Part")
	p.Size = Vector3.new(d[1], d[2], d[3])
	p.CFrame = origin * CFrame.new(d[4], d[5], d[6]) * CFrame.fromEulerAnglesYXZ(math.rad(d[7]), math.rad(d[8]), math.rad(d[9]))
	p.Color = c3(d[10])
	local mat = MATS[d[11]]
	p.Material = Enum.Material[mat]
	p.Anchored = true
	local collide = bit32.band(d[13], 1) ~= 0
	p.CanCollide = collide
	p.CanTouch = false
	p.CanQuery = collide
	p.CastShadow = bit32.band(d[13], 2) ~= 0
	if mat == "Glass" then
		p.Transparency = 0.35
	end
	if mat == "Plastic" then
		if CONFIG.StudMode == "Inlet" then
			for _, s in ipairs({ "TopSurface", "BottomSurface", "FrontSurface", "BackSurface", "LeftSurface", "RightSurface" }) do
				p[s] = Enum.SurfaceType.Inlet
			end
		elseif CONFIG.StudMode == "Variant" then
			p.MaterialVariant = "StudInset"
		end
	end
	p.Parent = folder(FOLDERS[d[12]])
	made[i] = p
	if CONFIG.YieldEvery > 0 and i % CONFIG.YieldEvery == 0 and not _G.__SPEAR_EXPORT then
		task.wait()
	end
end
for i, t in pairs(TRANSP) do
	made[i].Transparency = t
end
for i, n in pairs(NAMES) do
	made[i].Name = n
end
local function seq(a, b)
	return NumberSequence.new({ NumberSequenceKeypoint.new(0, a), NumberSequenceKeypoint.new(1, b) })
end
for i, kind in pairs(EFFECTS) do
	local p = made[i]
	if kind == "portal" then
		local sparks = Instance.new("ParticleEmitter")
		sparks.Name = "PortalSparkles"
		sparks.Texture = "rbxasset://textures/particles/sparkles_main.dds"
		sparks.Color = ColorSequence.new(Color3.fromRGB(196, 140, 255), Color3.fromRGB(79, 227, 255))
		sparks.LightEmission = 1
		sparks.Rate = 45
		sparks.Lifetime = NumberRange.new(1, 2)
		sparks.Speed = NumberRange.new(1, 4)
		sparks.SpreadAngle = Vector2.new(180, 180)
		sparks.Size = seq(0.9, 0)
		sparks.Parent = p
		local wisps = Instance.new("ParticleEmitter")
		wisps.Name = "PortalWisps"
		wisps.Texture = "rbxasset://textures/particles/smoke_main.dds"
		wisps.Color = ColorSequence.new(Color3.fromRGB(150, 90, 255), Color3.fromRGB(60, 200, 255))
		wisps.LightEmission = 0.8
		wisps.Rate = 12
		wisps.Lifetime = NumberRange.new(1.5, 2.5)
		wisps.Speed = NumberRange.new(0.5, 1.5)
		wisps.Acceleration = Vector3.new(0, 2.5, 0)
		wisps.RotSpeed = NumberRange.new(-90, 90)
		wisps.Size = seq(2.5, 0.2)
		wisps.Transparency = seq(0.35, 1)
		wisps.Parent = p
	elseif kind == "fire" then
		local fire = Instance.new("Fire")
		fire.Heat, fire.Size = 9, 5
		fire.Color, fire.SecondaryColor = Color3.fromRGB(255, 150, 40), Color3.fromRGB(255, 70, 20)
		fire.Parent = p
		local embers = Instance.new("ParticleEmitter")
		embers.Name = "Embers"
		embers.Texture = "rbxasset://textures/particles/sparkles_main.dds"
		embers.Color = ColorSequence.new(Color3.fromRGB(255, 200, 80), Color3.fromRGB(255, 90, 30))
		embers.LightEmission = 1
		embers.Rate = 10
		embers.Lifetime = NumberRange.new(1, 2)
		embers.Speed = NumberRange.new(3, 6)
		embers.SpreadAngle = Vector2.new(25, 25)
		embers.Size = seq(0.35, 0)
		embers.Parent = p
	elseif kind == "pad" then
		p.CanTouch = true          -- step on the glowing square to open the shop / use the portal
		local glow = Instance.new("ParticleEmitter")
		glow.Name = "PadGlow"
		glow.Texture = "rbxasset://textures/particles/sparkles_main.dds"
		glow.Color = ColorSequence.new(p.Color)
		glow.LightEmission = 1
		glow.Rate = 6
		glow.Lifetime = NumberRange.new(1, 1.6)
		glow.Speed = NumberRange.new(1, 2)
		glow.EmissionDirection = Enum.NormalId.Top
		glow.Size = seq(0.4, 0)
		glow.Parent = p
	end
end
for i, l in pairs(LIGHTS) do
	local light = Instance.new(l[1])
	light.Brightness = l[2]
	light.Range = l[3]
	light.Color = c3(l[4])
	light.Shadows = false
	if l[1] == "SpotLight" then
		light.Angle = 40
		light.Face = Enum.NormalId.Front
	end
	light.Parent = made[i]
end
for _, t in ipairs(TEXTS) do
	local gui = Instance.new("SurfaceGui")
	gui.Face = Enum.NormalId[t[4]]
	gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
	gui.PixelsPerStud = 40
	gui.LightInfluence = 0.6
	local label = Instance.new("TextLabel")
	label.BackgroundTransparency = 1
	label.Size = UDim2.fromScale(1, 1)
	label.Text = t[2]
	label.TextScaled = true
	label.Font = Enum.Font.FredokaOne
	label.TextColor3 = c3(t[3])
	label.TextStrokeTransparency = 0.6
	label.Parent = gui
	gui.Parent = made[t[1]]
end

-- spawn in the plaza
local spawn = Instance.new("SpawnLocation")
spawn.Name = "PlazaSpawn"
spawn.Anchored = true
spawn.Transparency = 1
spawn.CanCollide = false
spawn.Size = Vector3.new(6, 1, 6)
spawn.CFrame = origin * CFrame.new(@@SPAWN@@)
spawn.Neutral = true
spawn.Parent = folder("Spawns")

-- lighting preset (applied on teleport by IslandLighting, or right now by this builder)
local preset = Instance.new("Configuration")
preset.Name = "LightingPreset"
for k, v in pairs(PRESET) do
	if type(v) == "table" then
		preset:SetAttribute(k, Color3.fromRGB(v[1], v[2], v[3]))
	else
		preset:SetAttribute(k, v)
	end
end
preset.Parent = folder("Lighting")
root:SetAttribute("WaterMin", Vector3.new(WATER[1], WATER[2], WATER[3]))
root:SetAttribute("WaterMax", Vector3.new(WATER[4], WATER[5], WATER[6]))

local LIGHTING_SRC = [==[-- require(island.IslandLighting).Apply(island)  -- call on teleport
local M = {}
function M.Apply(island)
	local preset = island:FindFirstChild("Lighting") and island.Lighting:FindFirstChild("LightingPreset")
	if not preset then return end
	local a = preset:GetAttributes()
	local Lighting = game:GetService("Lighting")
	pcall(function() Lighting.Technology = Enum.Technology.Future end)
	Lighting.ClockTime = a.ClockTime
	Lighting.Brightness = a.Brightness
	Lighting.Ambient = a.Ambient
	Lighting.OutdoorAmbient = a.OutdoorAmbient
	Lighting.EnvironmentDiffuseScale = a.EnvironmentDiffuseScale
	Lighting.EnvironmentSpecularScale = a.EnvironmentSpecularScale
	Lighting.GlobalShadows = true
	local function get(class, name)
		local o = Lighting:FindFirstChild(name) or Instance.new(class)
		o.Name = name
		o.Parent = Lighting
		return o
	end
	local atmo = get("Atmosphere", "IslandAtmosphere")
	atmo.Color, atmo.Decay = a.AtmosphereColor, a.AtmosphereDecay
	atmo.Density, atmo.Haze, atmo.Glare, atmo.Offset = a.AtmosphereDensity, a.AtmosphereHaze, 0, 0.1
	local cc = get("ColorCorrectionEffect", "IslandColor")
	cc.TintColor, cc.Saturation, cc.Contrast, cc.Brightness = a.CCTint, a.CCSaturation, a.CCContrast, 0
	local bloom = get("BloomEffect", "IslandBloom")
	bloom.Intensity, bloom.Size, bloom.Threshold = a.BloomIntensity, 24, 1.5
	local t = workspace.Terrain
	t.WaterColor = a.WaterColor
	t.WaterTransparency, t.WaterReflectance, t.WaterWaveSize, t.WaterWaveSpeed = 0.75, 0.1, 0.1, 6
end
return M]==]
local TIERS_SRC = [==[-- require(island.IslandTiers).SetTier(island, 1 | 2 | 3)
-- Tier1 shows at tier 1 only; Tier2 shows at tiers 2 and 3; Tier3 adds the tier-3 extras.
local M = {}
local function show(model, on)
	for _, d in ipairs(model:GetDescendants()) do
		if d:IsA("BasePart") then
			if d:GetAttribute("TierT") == nil then
				d:SetAttribute("TierT", d.Transparency)
				d:SetAttribute("TierC", d.CanCollide)
				d:SetAttribute("TierS", d.CastShadow)
			end
			d.Transparency = on and d:GetAttribute("TierT") or 1
			d.CanCollide = on and d:GetAttribute("TierC") or false
			d.CanQuery = on and d:GetAttribute("TierC") or false
			d.CastShadow = on and d:GetAttribute("TierS") or false
		elseif d:IsA("Light") or d:IsA("SurfaceGui") or d:IsA("ParticleEmitter") then
			d.Enabled = on
		end
	end
end
function M.SetTier(island, n)
	show(island.Tier1, n == 1)
	show(island.Tier2, n >= 2)
	show(island.Tier3, n >= 3)
	island:SetAttribute("Tier", n)
end
return M]==]
-- the same code, usable right now (a Script cannot require a module whose Source it just set)
local IslandLighting = (function()
-- require(island.IslandLighting).Apply(island)  -- call on teleport
local M = {}
function M.Apply(island)
	local preset = island:FindFirstChild("Lighting") and island.Lighting:FindFirstChild("LightingPreset")
	if not preset then return end
	local a = preset:GetAttributes()
	local Lighting = game:GetService("Lighting")
	pcall(function() Lighting.Technology = Enum.Technology.Future end)
	Lighting.ClockTime = a.ClockTime
	Lighting.Brightness = a.Brightness
	Lighting.Ambient = a.Ambient
	Lighting.OutdoorAmbient = a.OutdoorAmbient
	Lighting.EnvironmentDiffuseScale = a.EnvironmentDiffuseScale
	Lighting.EnvironmentSpecularScale = a.EnvironmentSpecularScale
	Lighting.GlobalShadows = true
	local function get(class, name)
		local o = Lighting:FindFirstChild(name) or Instance.new(class)
		o.Name = name
		o.Parent = Lighting
		return o
	end
	local atmo = get("Atmosphere", "IslandAtmosphere")
	atmo.Color, atmo.Decay = a.AtmosphereColor, a.AtmosphereDecay
	atmo.Density, atmo.Haze, atmo.Glare, atmo.Offset = a.AtmosphereDensity, a.AtmosphereHaze, 0, 0.1
	local cc = get("ColorCorrectionEffect", "IslandColor")
	cc.TintColor, cc.Saturation, cc.Contrast, cc.Brightness = a.CCTint, a.CCSaturation, a.CCContrast, 0
	local bloom = get("BloomEffect", "IslandBloom")
	bloom.Intensity, bloom.Size, bloom.Threshold = a.BloomIntensity, 24, 1.5
	local t = workspace.Terrain
	t.WaterColor = a.WaterColor
	t.WaterTransparency, t.WaterReflectance, t.WaterWaveSize, t.WaterWaveSpeed = 0.75, 0.1, 0.1, 6
end
return M
end)()
local IslandTiers = (function()
-- require(island.IslandTiers).SetTier(island, 1 | 2 | 3)
-- Tier1 shows at tier 1 only; Tier2 shows at tiers 2 and 3; Tier3 adds the tier-3 extras.
local M = {}
local function show(model, on)
	for _, d in ipairs(model:GetDescendants()) do
		if d:IsA("BasePart") then
			if d:GetAttribute("TierT") == nil then
				d:SetAttribute("TierT", d.Transparency)
				d:SetAttribute("TierC", d.CanCollide)
				d:SetAttribute("TierS", d.CastShadow)
			end
			d.Transparency = on and d:GetAttribute("TierT") or 1
			d.CanCollide = on and d:GetAttribute("TierC") or false
			d.CanQuery = on and d:GetAttribute("TierC") or false
			d.CastShadow = on and d:GetAttribute("TierS") or false
		elseif d:IsA("Light") or d:IsA("SurfaceGui") or d:IsA("ParticleEmitter") then
			d.Enabled = on
		end
	end
end
function M.SetTier(island, n)
	show(island.Tier1, n == 1)
	show(island.Tier2, n >= 2)
	show(island.Tier3, n >= 3)
	island:SetAttribute("Tier", n)
end
return M
end)()
for name, src in pairs({ IslandLighting = LIGHTING_SRC, IslandTiers = TIERS_SRC }) do
	local m = Instance.new("ModuleScript")
	m.Name = name
	pcall(function() m.Source = src end) -- works from the Command Bar / export; harmless otherwise
	m.Parent = root
end

local spinner = Instance.new("Script")
spinner.Name = "Spinner"
pcall(function()
	spinner.Source = [==[
-- spins the lighthouse beam and the portal swirl while the game runs
local RunService = game:GetService("RunService")
local island = script.Parent
local beams, swirl, orbit, core = {}, {}, {}, nil
for _, p in ipairs(island:GetDescendants()) do
	if p:IsA("BasePart") then
		if p.Name == "LighthouseBeam" then table.insert(beams, p)
		elseif p.Name == "PortalSwirl" then table.insert(swirl, { p, 1.4 })
		elseif p.Name == "PortalSwirl2" then table.insert(swirl, { p, -0.9 })
		elseif p.Name == "PortalOrbit" then table.insert(orbit, p)
		elseif p.Name == "PortalCore" then core = p end
	end
end
local t = 0
RunService.Heartbeat:Connect(function(dt)
	t += dt
	for _, p in ipairs(beams) do
		if p.Transparency < 1 then
			p.CFrame = p.CFrame * CFrame.Angles(0, dt * 0.9, 0)
		end
	end
	if core then
		local c = core.CFrame
		for _, s in ipairs(swirl) do      -- vortex rings turn around the portal axis
			s[1].CFrame = c * CFrame.Angles(0, 0, dt * s[2]) * c:Inverse() * s[1].CFrame
		end
		for _, p in ipairs(orbit) do      -- crystals bob gently
			p.CFrame = p.CFrame + Vector3.new(0, math.sin(t * 1.5 + p.Position.X) * dt * 0.6, 0)
		end
	end
end)
]==]
end)
spinner.Parent = root

root.Parent = islands
IslandTiers.SetTier(root, CONFIG.StartTier)

if not _G.__SPEAR_EXPORT then
	if CONFIG.ApplyLighting then
		IslandLighting.Apply(root)
	end
	if CONFIG.UseTerrainWater then
		local wmin, wmax = root:GetAttribute("WaterMin"), root:GetAttribute("WaterMax")
		local size = wmax - wmin
		local tiles = math.ceil(math.max(size.X, size.Z) / 512)
		local tx, tz = size.X / tiles, size.Z / tiles
		for a = 0, tiles - 1 do
			for b = 0, tiles - 1 do
				local c = Vector3.new(wmin.X + (a + 0.5) * tx, (wmin.Y + wmax.Y) / 2, wmin.Z + (b + 0.5) * tz)
				workspace.Terrain:FillBlock(origin * CFrame.new(c), Vector3.new(tx, size.Y, tz), Enum.Material.Water)
			end
		end
	end
	local bp = workspace:FindFirstChild("Baseplate")
	if bp then
		bp.Parent = game:GetService("ServerStorage")
	end
	pcall(function() workspace.StreamingEnabled = true end)
	print(("[@@MAP@@] built %d parts"):format(#P))
end
return root
