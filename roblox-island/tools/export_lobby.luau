--[[ Lobby export: takes the original Lobby model (roblox/LobbyOriginal.rbxm), keeps everything the game
scripts use (Markers/LobbySpawn, SpawnLocation, CoinsBoard, StreakBoard with their attributes and
SurfaceGuis) and replaces the contents of Island and Decor with the rebuild from build/Lobby.json.

    lune run tools/export_lobby.luau roblox/LobbyOriginal.rbxm build/Lobby.json roblox/Lobby.rbxm
]]
local fs = require("@lune/fs")
local roblox = require("@lune/roblox")
local serde = require("@lune/serde")
local process = require("@lune/process")
local Instance, CFrame, Vector3, Color3, Enum = roblox.Instance, roblox.CFrame, roblox.Vector3, roblox.Color3, roblox.Enum

local src, jsonPath, out = process.args[1], process.args[2], process.args[3]
local lobby = roblox.deserializeModel(fs.readFile(src))[1]
assert(lobby.Name == "Lobby", "expected the Lobby folder")
local island = lobby:FindFirstChild("Island")
local decor = lobby:FindFirstChild("Decor")
for _, c in island:GetChildren() do c:Destroy() end
for _, c in decor:GetChildren() do c:Destroy() end

local function hex(h)
	h = h:gsub("#", "")
	return Color3.fromRGB(tonumber(h:sub(1, 2), 16), tonumber(h:sub(3, 4), 16), tonumber(h:sub(5, 6), 16))
end

local data = serde.decode("json", fs.readFile(jsonPath))
local groups, count = {}, 0
for _, d in data.parts do
	if d.stage == "keep" then continue end
	local p = Instance.new("Part")
	local R = d.R
	p.Size = Vector3.new(d.size[1], d.size[2], d.size[3])
	p.CFrame = CFrame.new(d.pos[1], d.pos[2], d.pos[3],
		R[1][1], R[1][2], R[1][3], R[2][1], R[2][2], R[2][3], R[3][1], R[3][2], R[3][3])
	p.Color = hex(d.color)
	p.Material = Enum.Material[d.mat]
	p.Anchored = true
	local decorSmall = (d.stage == "props") and math.max(d.size[1], d.size[2], d.size[3]) < 2
	local collide = d.collide and not decorSmall
	p.CanCollide = collide
	p.CanQuery = collide
	p.CanTouch = false
	p.CastShadow = d.shadow and not decorSmall
	if d.mat == "Plastic" then
		for _, s in { "TopSurface", "BottomSurface", "FrontSurface", "BackSurface", "LeftSurface", "RightSurface" } do
			p[s] = Enum.SurfaceType.Inlet
		end
	end
	if d.light then
		local l = Instance.new(d.light[1])
		l.Brightness = d.light[2]
		l.Range = d.light[3]
		l.Color = hex(d.light[4])
		l.Parent = p
	end
	if d.folder == "Island" then
		p.Name = d.name or (d.stage == "terrain" and "Ground" or "Part")
		p.Parent = island
		if d.name == "Grass" then island.PrimaryPart = p end
	else
		local kind = string.match(d.tag, "^([^:]+)")
		local g = groups[d.tag]
		if not g then
			g = Instance.new("Model")
			g.Name = kind
			g.Parent = decor
			groups[d.tag] = g
		end
		p.Name = d.name or kind
		p.Parent = g
		if not g.PrimaryPart then g.PrimaryPart = p end
	end
	count += 1
end
fs.writeFile(out, roblox.serializeModel({ lobby }))

-- sanity: reload and check the parts scripts depend on
local back = roblox.deserializeModel(fs.readFile(out))[1]
local function need(path)
	local x = back
	for name in string.gmatch(path, "[^/]+") do
		x = x:FindFirstChild(name)
		assert(x, "missing " .. path)
	end
	return x
end
need("Markers/LobbySpawn")
need("SpawnLocation")
assert(need("CoinsBoard/Board"):GetAttribute("Leaderboard") == "Coins")
assert(need("StreakBoard/Board"):GetAttribute("Leaderboard") == "Streak")
assert(need("CoinsBoard/Header/Label/Text").Text == "TOP COINS")
assert(need("StreakBoard/Header/Label/Text").Text == "TOP STREAKS")
assert(need("Island").PrimaryPart and need("Island").PrimaryPart.Name == "Grass")
print(string.format("Lobby.rbxm: %d new parts in Island + %d Decor models; boards, spawn and markers kept", count,
	#back.Decor:GetChildren()))
