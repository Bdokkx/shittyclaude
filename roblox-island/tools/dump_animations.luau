-- Dump every KeyframeSequence in a model to JSON (poses as raw CFrame components) for anim/make_previews.py.
--   lune run tools/dump_animations.luau roblox/AnimationsOriginal.rbxm build/animations_original.json
local fs = require("@lune/fs")
local roblox = require("@lune/roblox")
local serde = require("@lune/serde")
local process = require("@lune/process")
local root = roblox.deserializeModel(fs.readFile(process.args[1]))
local function pose(p)
	local c = { p.CFrame:GetComponents() }
	local kids = {}
	for _, k in p:GetChildren() do
		if k:IsA("Pose") then table.insert(kids, pose(k)) end
	end
	return { name = p.Name, cf = c, style = p.EasingStyle.Name, dir = p.EasingDirection.Name, weight = p.Weight, kids = kids }
end
local out = {}
local function walk(inst, path)
	for _, c in inst:GetChildren() do
		if c:IsA("KeyframeSequence") then
			local kfs = {}
			for _, kf in c:GetChildren() do
				if kf:IsA("Keyframe") then
					local poses, markers = {}, {}
					for _, p in kf:GetChildren() do
						if p:IsA("Pose") then table.insert(poses, pose(p))
						else table.insert(markers, { class = p.ClassName, name = p.Name }) end
					end
					table.insert(kfs, { name = kf.Name, time = kf.Time, poses = poses, other = markers })
				else
					table.insert(kfs, { class = kf.ClassName, name = kf.Name })
				end
			end
			table.sort(kfs, function(a, b) return (a.time or 0) < (b.time or 0) end)
			table.insert(out, { path = path .. "/" .. c.Name, name = c.Name, loop = c.Loop, priority = c.Priority.Name,
				hip = c.AuthoredHipHeight, attrs = c:GetAttributes(), keyframes = kfs })
		else
			walk(c, path .. "/" .. c.Name)
		end
	end
end
for _, r in root do
	print("root", r.ClassName, r.Name, #r:GetChildren())
	walk(r, r.Name)
end
fs.writeFile(process.args[2], serde.encode("json", out))
