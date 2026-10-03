--[[
  Voxel Island + Coral Reef builder
  ---------------------------------
  Put this Script in ServerScriptService (or run it from the Command Bar).
  It builds two maps out of anchored, studded Parts:

    Workspace.VoxelIsland  - terraced island, plaza, stairs, dock, boat, pines
    Workspace.CoralReef    - sandy reef, rock shelves, shipwreck, corals

  Asset shapes come from the same data used to make the Blender meshes, so
  if you import the Blender FBX files into ReplicatedStorage.IslandAssets
  (one Model per asset, named like "PineTree"), the builder will clone those
  instead of building the part versions (see CONFIG.UseImportedMeshes).

  Generated file - edit the generator (gen/*.py) rather than the data below.
]]

local CONFIG = {
	BuildIsland = true,
	BuildReef = true,
	IslandOrigin = Vector3.new(0, 0, 0),
	ReefOrigin = Vector3.new(0, 0, 700),

	-- true: fill real Roblox terrain water around the island (recommended)
	-- false: use a translucent "Ocean" part instead
	UseTerrainWater = true,
	SetupLighting = true, -- bright, saturated lighting + clear turquoise water like the reference
	ReefUnderwater = false, -- also flood the reef with terrain water

	Studs = true, -- stud surfaces on every face, like the screenshots
	UseImportedMeshes = true,
	ClearExisting = true, -- delete an old VoxelIsland / CoralReef first
	AddSpawns = true,
	YieldEvery = 600, -- parts built between task.wait() calls (0 = never yield)
}

--@@DATA@@

----------------------------------------------------------------------------
-- builder
----------------------------------------------------------------------------

local Builder = {}

local colorCache = {}
local function color3(index)
	local c = colorCache[index]
	if not c then
		local p = PALETTE[index]
		c = Color3.fromRGB(p[1], p[2], p[3])
		colorCache[index] = c
	end
	return c
end

local ACCENT = PALETTE_INDEX.accent
local ACCENT_DARK = PALETTE_INDEX.accent_dark
local GLASS_ALPHA = 0.35

local built = 0
local function maybeYield()
	built += 1
	if CONFIG.YieldEvery > 0 and built % CONFIG.YieldEvery == 0 and task then
		task.wait()
	end
end

local function applySurfaces(part)
	if CONFIG.Studs then
		part.TopSurface = Enum.SurfaceType.Studs
		part.BottomSurface = Enum.SurfaceType.Inlet
		part.FrontSurface = Enum.SurfaceType.Studs
		part.BackSurface = Enum.SurfaceType.Studs
		part.LeftSurface = Enum.SurfaceType.Studs
		part.RightSurface = Enum.SurfaceType.Studs
	else
		part.TopSurface = Enum.SurfaceType.Smooth
		part.BottomSurface = Enum.SurfaceType.Smooth
	end
end

-- box = {x0, y0, z0, x1, y1, z1, colorIndex}
local function makeBox(parent, box, cf, scale, tint, name)
	local sx = (box[4] - box[1]) * scale
	local sy = (box[5] - box[2]) * scale
	local sz = (box[6] - box[3]) * scale
	local part = Instance.new("Part")
	part.Name = name or "Block"
	part.Anchored = true
	part.Size = Vector3.new(sx, sy, sz)
	local cx = (box[1] + box[4]) * 0.5 * scale
	local cy = (box[2] + box[5]) * 0.5 * scale
	local cz = (box[3] + box[6]) * 0.5 * scale
	part.CFrame = cf * CFrame.new(cx, cy, cz)
	local ci = box[7]
	local pal = PALETTE[ci]
	if tint and ci == ACCENT then
		part.Color = tint[1]
	elseif tint and ci == ACCENT_DARK then
		part.Color = tint[2]
	else
		part.Color = color3(ci)
	end
	part.Material = Enum.Material[pal[4]]
	if pal[4] == "Glass" then
		part.Transparency = GLASS_ALPHA
		part.CanCollide = false
	end
	if pal[4] == "Neon" then
		part.CastShadow = false
	end
	applySurfaces(part)
	part.Parent = parent
	maybeYield()
	return part
end

local function tintColors(tintIndex)
	if not tintIndex or tintIndex == 0 then
		return nil
	end
	local t = TINTS[tintIndex]
	return {
		Color3.fromRGB(t[1], t[2], t[3]),
		Color3.fromRGB(math.floor(t[1] * 0.75), math.floor(t[2] * 0.75), math.floor(t[3] * 0.75)),
	}
end

local function addLights(model, def, cf, scale)
	for _, l in ipairs(def.lights) do
		local holder = Instance.new("Part")
		holder.Name = "LightSource"
		holder.Anchored = true
		holder.CanCollide = false
		holder.CanQuery = false
		holder.CastShadow = false
		holder.Transparency = 1
		holder.Size = Vector3.new(0.2, 0.2, 0.2)
		holder.CFrame = cf * CFrame.new(l[1] * scale, l[2] * scale, l[3] * scale)
		local light = Instance.new("PointLight")
		light.Color = color3(l[4])
		light.Range = l[5] * scale
		light.Brightness = l[6]
		light.Shadows = l[6] >= 2 -- only the big lights cast shadows (cheaper)
		light.Parent = holder
		holder.Parent = model
	end
	for _, f in ipairs(def.fires) do
		local holder = Instance.new("Part")
		holder.Name = "FireSource"
		holder.Anchored = true
		holder.CanCollide = false
		holder.CanQuery = false
		holder.Transparency = 1
		holder.Size = Vector3.new(0.2, 0.2, 0.2)
		holder.CFrame = cf * CFrame.new(f[1] * scale, f[2] * scale, f[3] * scale)
		local fire = Instance.new("Fire")
		fire.Size = f[4] * scale
		fire.Heat = 6
		fire.Parent = holder
		holder.Parent = model
	end
end

local function importedTemplate(name)
	if not CONFIG.UseImportedMeshes or not game then
		return nil
	end
	local ok, rs = pcall(function()
		return game:GetService("ReplicatedStorage")
	end)
	local folder = ok and rs and rs:FindFirstChild("IslandAssets")
	return folder and folder:FindFirstChild(name)
end

-- Build one asset as a Model at CFrame cf. Exposed so you can reuse it:
--   Builder.spawnAsset("PineTree", CFrame.new(0, 10, 0), 1.2, nil, workspace)
function Builder.spawnAsset(name, cf, scale, tintIndex, parent)
	local def = ASSETS[name]
	assert(def, "unknown asset " .. tostring(name))
	scale = scale or 1
	local tmpl = (not tintIndex or tintIndex == 0) and importedTemplate(name)
	local model
	if tmpl then
		-- imported Blender mesh: fit it to the voxel asset's bounding box
		model = tmpl:Clone()
		local _, size = model:GetBoundingBox()
		local want = (def.max[2] - def.min[2]) * scale
		if size.Y > 0 then
			model:ScaleTo(model:GetScale() * want / size.Y)
		end
		local bbCf = model:GetBoundingBox()
		local center = Vector3.new(
			(def.min[1] + def.max[1]) * 0.5 * scale,
			(def.min[2] + def.max[2]) * 0.5 * scale,
			(def.min[3] + def.max[3]) * 0.5 * scale
		)
		local offset = bbCf.Rotation:Inverse() * (model:GetPivot().Position - bbCf.Position)
		model:PivotTo(cf * CFrame.new(center + offset))
		for _, d in ipairs(model:GetDescendants()) do
			if d:IsA("BasePart") then
				d.Anchored = true
			end
		end
		model.Parent = parent
		addLights(model, def, cf, scale)
		return model
	end
	model = Instance.new("Model")
	model.Name = name
	local tint = tintColors(tintIndex)
	for _, box in ipairs(def.boxes) do
		makeBox(model, box, cf, scale, tint)
	end
	addLights(model, def, cf, scale)
	model.WorldPivot = cf
	model.Parent = parent
	return model
end

local function propCFrame(origin, p)
	-- p = {asset, x, y, z, rotY, scale, tint, rotX, rotZ}
	return CFrame.new(origin + Vector3.new(p[2], p[3], p[4]))
		* CFrame.Angles(0, math.rad(p[5]), 0)
		* CFrame.Angles(math.rad(p[8]), 0, math.rad(p[9]))
end

function Builder.buildMap(mapName, data, origin, parent)
	if CONFIG.ClearExisting and parent:FindFirstChild(mapName) then
		parent[mapName]:Destroy()
	end
	local root = Instance.new("Model")
	root.Name = mapName
	root.Parent = parent

	local ground = Instance.new("Model")
	ground.Name = "Ground"
	ground.Parent = root
	local base = CFrame.new(origin)
	for _, box in ipairs(data.terrain) do
		makeBox(ground, box, base, 1, nil, "Ground")
	end

	local propsFolder = Instance.new("Folder")
	propsFolder.Name = "Props"
	propsFolder.Parent = root
	for _, p in ipairs(data.props) do
		Builder.spawnAsset(p[1], propCFrame(origin, p), p[6], p[7], propsFolder)
	end

	if data.water then
		local w = data.water
		local size = Vector3.new(w[4] - w[1], w[5] - w[2], w[6] - w[3])
		local center = origin + Vector3.new((w[1] + w[4]) / 2, (w[2] + w[5]) / 2, (w[3] + w[6]) / 2)
		local terrain = workspace and workspace:FindFirstChildOfClass("Terrain")
		if CONFIG.UseTerrainWater and terrain then
			terrain:FillBlock(CFrame.new(center), size, Enum.Material.Water)
		else
			local ocean = makeBox(root, { w[1], w[2], w[3], w[4], w[5], w[6], PALETTE_INDEX.ocean },
				base, 1, nil, "Ocean")
			ocean.CanQuery = false
			ocean.CastShadow = false
		end
	end

	if CONFIG.AddSpawns and data.spawn then
		local s = Instance.new("SpawnLocation")
		s.Name = mapName .. "Spawn"
		s.Anchored = true
		s.Size = Vector3.new(6, 1, 6)
		s.CFrame = CFrame.new(origin + Vector3.new(data.spawn[1], data.spawn[2] + 0.5, data.spawn[3]))
		s.Color = color3(PALETTE_INDEX.cobble)
		s.Material = Enum.Material.Slate
		s.Parent = root
	end
	root.WorldPivot = CFrame.new(origin)
	return root
end

-- Lighting / water look used for the reference renders. Safe to run more than once.
function Builder.setupLighting()
	local Lighting = game:GetService("Lighting")
	pcall(function()
		Lighting.Technology = Enum.Technology.Future -- only settable from Studio / command bar
	end)
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
	atmo.Density = 0.28
	atmo.Offset = 0.15
	atmo.Haze = 0.6
	atmo.Glare = 0.2
	atmo.Color = Color3.fromRGB(205, 225, 245)
	atmo.Decay = Color3.fromRGB(120, 150, 190)
	local cc = ensure("ColorCorrectionEffect", "VoxelColor")
	cc.Saturation = 0.22
	cc.Contrast = 0.1
	cc.Brightness = 0.02
	cc.TintColor = Color3.fromRGB(255, 251, 245)
	local bloom = ensure("BloomEffect", "VoxelBloom")
	bloom.Intensity = 0.35
	bloom.Size = 22
	bloom.Threshold = 1.6
	local rays = ensure("SunRaysEffect", "VoxelSunRays")
	rays.Intensity = 0.04
	rays.Spread = 0.6
	local terrain = workspace:FindFirstChildOfClass("Terrain")
	if terrain then
		terrain.WaterColor = Color3.fromRGB(24, 118, 168)
		terrain.WaterTransparency = 0.75
		terrain.WaterReflectance = 0.25
		terrain.WaterWaveSize = 0.08
		terrain.WaterWaveSpeed = 6
	end
end

function Builder.buildReefWater(origin)
	local terrain = workspace and workspace:FindFirstChildOfClass("Terrain")
	if terrain then
		terrain:FillBlock(CFrame.new(origin + Vector3.new(0, 30, 0)), Vector3.new(520, 76, 420),
			Enum.Material.Water)
	end
end

-- Folder of every asset laid out in a row (handy for copy/pasting into a scene).
function Builder.buildAssetLibrary(parent, origin)
	local folder = Instance.new("Folder")
	folder.Name = "VoxelAssetLibrary"
	local x = 0
	for _, name in ipairs(ASSET_ORDER) do
		local def = ASSETS[name]
		local w = def.max[1] - def.min[1]
		x += w / 2 + 6
		Builder.spawnAsset(name, CFrame.new(origin + Vector3.new(x, -def.min[2], 0)), 1,
			def.tintable and 1 or 0, folder)
		x += w / 2
	end
	folder.Parent = parent
	return folder
end

Builder.CONFIG = CONFIG
Builder.ASSETS = ASSETS
Builder.MAPS = MAPS

-- Offline export hook (used by the generator to write .rbxmx files).
if _G.__VOXEL_EXPORT then
	_G.__VOXEL_EXPORT(Builder)
	return
end

----------------------------------------------------------------------------
-- main
----------------------------------------------------------------------------
local t0 = os.clock()
if CONFIG.SetupLighting then
	Builder.setupLighting()
end
if CONFIG.BuildIsland then
	Builder.buildMap("VoxelIsland", MAPS.Island, CONFIG.IslandOrigin, workspace)
end
if CONFIG.BuildReef then
	Builder.buildMap("CoralReef", MAPS.Reef, CONFIG.ReefOrigin, workspace)
	if CONFIG.ReefUnderwater then
		Builder.buildReefWater(CONFIG.ReefOrigin)
	end
end
print(("[VoxelIsland] built %d parts in %.1fs"):format(built, os.clock() - t0))
