--[[ Export a standalone model (e.g. the Monster Mouth event piece) from build/<Name>_export.json.

    lune run tools/export_model.luau build/MonsterMouth_export.json roblox/MonsterMouth.rbxm

Root Model <name> (attributes from "attrs") > one Folder per part folder > one Model per tag; parts with an
empty folder sit directly under the root. Plastic gets the Inlet stud surface; collision follows "collide";
a part named MouthTrigger becomes an invisible CanTouch trigger. "scripts" become client Scripts.
]]
local fs = require("@lune/fs")
local roblox = require("@lune/roblox")
local serde = require("@lune/serde")
local process = require("@lune/process")
local Instance, CFrame, Vector3, Color3, Enum = roblox.Instance, roblox.CFrame, roblox.Vector3, roblox.Color3, roblox.Enum

local d = serde.decode("json", fs.readFile(process.args[1]))
local out = process.args[2]

local function hex(h)
	h = h:gsub("#", "")
	return Color3.fromRGB(tonumber(h:sub(1, 2), 16), tonumber(h:sub(3, 4), 16), tonumber(h:sub(5, 6), 16))
end

local root = Instance.new("Model")
root.Name = d.name
for k, v in d.attrs or {} do root:SetAttribute(k, v) end

local folders, groups = {}, {}
local function folderOf(name)
	if name == "" then return root end
	if not folders[name] then
		local f = Instance.new("Folder")
		f.Name = name
		f.Parent = root
		folders[name] = f
	end
	return folders[name]
end

local count = 0
for _, p in d.parts do
	if p.stage == "preview" then continue end
	local part = Instance.new("Part")
	local R = p.R
	part.Size = Vector3.new(p.size[1], p.size[2], p.size[3])
	part.CFrame = CFrame.new(p.pos[1], p.pos[2], p.pos[3],
		R[1][1], R[1][2], R[1][3], R[2][1], R[2][2], R[2][3], R[3][1], R[3][2], R[3][3])
	part.Color = hex(p.color)
	part.Material = Enum.Material[p.mat]
	part.Anchored = true
	part.Transparency = p.transparency or 0
	if p.mat == "Plastic" then
		for _, s in { "TopSurface", "BottomSurface", "FrontSurface", "BackSurface", "LeftSurface", "RightSurface" } do
			part[s] = Enum.SurfaceType.Inlet
		end
	end
	local trigger = p.name == "MouthTrigger"
	part.CanCollide = p.collide and not trigger
	part.CanQuery = p.collide or trigger
	part.CanTouch = trigger
	part.CastShadow = p.shadow and math.max(p.size[1], p.size[2], p.size[3]) >= 2
	local parent = folderOf(p.folder)
	local kind = p.tag and string.match(p.tag, "^([^:]+)")
	if kind then
		local key = p.folder .. "/" .. p.tag
		local g = groups[key]
		if not g then
			g = Instance.new("Model")
			g.Name = kind
			g.Parent = parent
			groups[key] = g
		end
		parent = g
		if not g.PrimaryPart then g.PrimaryPart = part end
	end
	part.Name = p.name or kind or p.folder
	part.Parent = parent
	count += 1
end

for sname, path in d.scripts or {} do
	local sc = Instance.new("Script")
	sc.Name = sname
	sc.RunContext = Enum.RunContext.Client
	sc.Source = fs.readFile(path)
	sc.Parent = root
end
fs.writeFile(out, roblox.serializeModel({ root }))
print(string.format("%s.rbxm: %d parts", d.name, count))
