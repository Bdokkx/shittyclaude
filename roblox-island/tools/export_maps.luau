--[[ Arena export: takes the uploaded Maps file (Tags stripped) and the rebuild from maps/build_maps.py.

    lune run tools/export_maps.luau roblox/MapsOriginal.rbxm build/maps_export.json roblox/Maps.rbxm

Kept exactly as uploaded: each map Model and its attributes, Markers (lines, safe zones + SAFE labels, catcher
spawn), Barriers, and the Field tiles/trim (only their colour changes).
A map missing from the upload (the October event map) is first cloned from its template map.
Replaced: Underside, Scenery, and Obstacles (each obstacle is still one collider Part with the same name, with its
detail parts parented under it). The Desert UFO's ParticleEmitter is moved onto the new saucer.
]]
local fs = require("@lune/fs")
local roblox = require("@lune/roblox")
local serde = require("@lune/serde")
local process = require("@lune/process")
local Instance, CFrame, Vector3, Color3, Enum, UDim2 = roblox.Instance, roblox.CFrame, roblox.Vector3, roblox.Color3,
	roblox.Enum, roblox.UDim2

local src, jsonPath, out = process.args[1], process.args[2], process.args[3]
local root = roblox.deserializeModel(fs.readFile(src))
local maps = root[1]
assert(maps.Name == "Maps", "expected the Maps folder")

local function hex(h)
	h = h:gsub("#", "")
	return Color3.fromRGB(tonumber(h:sub(1, 2), 16), tonumber(h:sub(3, 4), 16), tonumber(h:sub(5, 6), 16))
end

local function count(inst)
	return #inst:GetDescendants()
end

local data = serde.decode("json", fs.readFile(jsonPath))
-- event maps that are not in the uploaded file: copy a template map (markers, barriers, field), then rebuild it
for name, d in data do
	if not maps:FindFirstChild(name) and d.template then
		local m = assert(maps:FindFirstChild(d.template), "no template map " .. d.template):Clone()
		m.Name = name
		for k, v in d.attrs do m:SetAttribute(k, v) end
		m.Parent = maps
	end
end
local before = {}
for name, _ in data do
	local m = assert(maps:FindFirstChild(name), "no map " .. name)
	before[name] = { markers = count(m.Markers), barriers = count(m.Barriers) }
end

for name, d in data do
	local m = maps:FindFirstChild(name)
	-- field: recolour only
	local recoloured = 0
	for _, t in m.Field:GetChildren() do
		if t.Name == "Tile" then
			local p = t.CFrame.Position
			local col = d.field[string.format("%.1f,%.1f", p.X, p.Z)]
			assert(col, name .. ": no colour for tile at " .. tostring(p))
			t.Color = hex(col)
			recoloured += 1
		elseif t.Name == "Trim" then
			t.Color = hex(d.trim)
		end
	end
	assert(recoloured == 200, name .. ": expected 200 tiles, got " .. recoloured)

	local emitter
	for _, x in m.Scenery:GetDescendants() do
		if x:IsA("ParticleEmitter") then emitter = x:Clone() end
	end
	for _, f in { m.Underside, m.Scenery, m.Obstacles } do
		for _, c in f:GetChildren() do c:Destroy() end
	end

	local groups, made, disc = {}, {}, nil
	for i, p in d.parts do
		local part = Instance.new("Part")
		local R = p.R
		part.Size = Vector3.new(p.size[1], p.size[2], p.size[3])
		part.CFrame = CFrame.new(p.pos[1], p.pos[2], p.pos[3],
			R[1][1], R[1][2], R[1][3], R[2][1], R[2][2], R[2][3], R[3][1], R[3][2], R[3][3])
		part.Color = hex(p.color)
		part.Material = Enum.Material[p.mat]
		part.Anchored = true
		if p.transparency and p.transparency > 0 then part.Transparency = p.transparency end
		if p.mat == "Plastic" then
			for _, s in { "TopSurface", "BottomSurface", "FrontSurface", "BackSurface", "LeftSurface", "RightSurface" } do
				part[s] = Enum.SurfaceType.Inlet
			end
		end
		local isCollider = p.stage == "obstacle" and p.collide
		part.CanCollide = isCollider
		part.CanTouch = isCollider
		part.CanQuery = isCollider
		part.CastShadow = p.shadow and math.max(p.size[1], p.size[2], p.size[3]) >= 2
		if p.folder == "Underside" then
			part.Name = p.name or "Rock"
			part.Parent = m.Underside
		else
			local kind = string.match(p.tag, "^([^:]+)")
			part.Name = p.name or kind
			local g = groups[p.tag]
			if p.folder == "Obstacles" then
				if not g then
					assert(isCollider, name .. ": obstacle " .. p.tag .. " must start with its collider")
					part.Parent = m.Obstacles
					groups[p.tag] = part
				else
					part.Parent = g
				end
			else
				if not g then
					g = Instance.new("Model")
					g.Name = kind
					g.Parent = m.Scenery
					groups[p.tag] = g
				end
				part.Parent = g
				if not g.PrimaryPart then g.PrimaryPart = part end
			end
		end
		if p.name == "Disc" and not disc then disc = part end
		made[i] = part
	end
	if emitter and disc then emitter.Parent = disc end

	for _, t in d.texts do
		local part = made[t.part + 1]
		local gui = Instance.new("SurfaceGui")
		gui.Name = "Label"
		gui.Face = Enum.NormalId[t.face]
		gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
		gui.PixelsPerStud = 30
		local label = Instance.new("TextLabel")
		label.Name = "Text"
		label.Size = UDim2.fromScale(1, 1)
		label.BackgroundTransparency = 1
		label.Text = t.text
		label.TextScaled = true
		label.FontFace = roblox.Font.fromEnum(Enum.Font.FredokaOne)
		label.TextColor3 = hex(t.color)
		label.Parent = gui
		gui.Parent = part
	end
end
-- client-side animation scripts (RunContext = Client, so they run wherever the map sits in Workspace)
for name, d in data do
	if d.scripts then
		local m = maps:FindFirstChild(name)
		for sname, path in d.scripts do
			local old = m:FindFirstChild(sname)
			if old then old:Destroy() end
			local sc = Instance.new("Script")
			sc.Name = sname
			sc.RunContext = Enum.RunContext.Client
			sc.Source = fs.readFile(path)
			sc.Parent = m
		end
	end
end
fs.writeFile(out, roblox.serializeModel(root))

-- sanity: reload; markers/barriers untouched, every map has its field, obstacles are colliders
local back = roblox.deserializeModel(fs.readFile(out))[1]
for name, d in data do
	local m = back:FindFirstChild(name)
	assert(m:GetAttribute("MapId") == name, name .. ": MapId attribute lost")
	assert(count(m.Markers) == before[name].markers and count(m.Barriers) == before[name].barriers,
		name .. ": markers/barriers changed")
	for _, o in m.Obstacles:GetChildren() do
		assert(o:IsA("BasePart") and o.CanCollide, name .. ": obstacle " .. o.Name .. " is not a collider part")
	end
	print(string.format("%-7s %5d scenery parts, %4d underside parts, %d obstacles", name,
		count(m.Scenery), #m.Underside:GetChildren(), #m.Obstacles:GetChildren()))
end
