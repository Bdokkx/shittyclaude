--[[ Rebuild the keyframes of every KeyframeSequence in the uploaded animations file from anim/anims.py.

    python3 anim/build_animations.py                       (writes build/animations.json)
    lune run tools/export_animations.luau <original.rbxm (Tags stripped)> build/animations.json roblox/Animations.rbxm

Everything else on each KeyframeSequence (Name, Loop, Priority, AuthoredHipHeight, GUID) is kept as it was, so
the file drops in where the old one was. Pose tree per keyframe: HumanoidRootPart (Weight 0) > Torso > limbs.
]]
local fs = require("@lune/fs")
local roblox = require("@lune/roblox")
local serde = require("@lune/serde")
local process = require("@lune/process")
local Instance, CFrame, Enum = roblox.Instance, roblox.CFrame, roblox.Enum

local src, jsonPath, out = process.args[1], process.args[2], process.args[3]
local root = roblox.deserializeModel(fs.readFile(src))
local seqs = {}
for _, r in root do
	for _, d in r:GetDescendants() do
		if d:IsA("KeyframeSequence") then seqs[d.Name] = d end
	end
end

local function pose(name, p)
	local x = Instance.new("Pose")
	x.Name = name
	x.CFrame = CFrame.new(table.unpack(p.cf))
	x.EasingStyle = Enum.PoseEasingStyle[p.style]
	x.EasingDirection = Enum.PoseEasingDirection[p.dir]
	x.Weight = p.weight
	return x
end

local data = serde.decode("json", fs.readFile(jsonPath))
local done = 0
for _, s in data do
	local ks = assert(seqs[s.name], "no KeyframeSequence named " .. s.name)
	assert(ks.Loop == s.loop and ks.Priority.Name == s.priority, "loop/priority mismatch on " .. s.name)
	for _, c in ks:GetChildren() do c:Destroy() end
	for _, k in s.keyframes do
		local kf = Instance.new("Keyframe")
		kf.Name = "Keyframe"
		kf.Time = k.time
		local hrp = pose("HumanoidRootPart", { cf = { 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1 }, style = "Linear", dir = "In", weight = 0 })
		hrp.Parent = kf
		local torso = k.poses["Torso"] and pose("Torso", k.poses["Torso"])
		if torso then torso.Parent = hrp end
		for name, p in k.poses do
			if name ~= "Torso" then pose(name, p).Parent = torso or hrp end
		end
		kf.Parent = ks
	end
	done += 1
end
fs.writeFile(out, roblox.serializeModel(root))

-- sanity: reload, every sequence present with the expected number of keyframes and the same end time
local back = roblox.deserializeModel(fs.readFile(out))
local found = {}
for _, r in back do
	for _, d in r:GetDescendants() do
		if d:IsA("KeyframeSequence") then found[d.Name] = d end
	end
end
for _, s in data do
	local ks = assert(found[s.name], "missing after reload: " .. s.name)
	local n, last = 0, 0
	for _, kf in ks:GetChildren() do
		n += 1
		last = math.max(last, kf.Time)
		local hrp = kf:FindFirstChild("HumanoidRootPart")
		assert(hrp and hrp:IsA("Pose"), s.name .. ": keyframe without HumanoidRootPart pose")
	end
	assert(n == #s.keyframes and math.abs(last - s.length) < 1e-4, s.name .. ": keyframes did not round-trip")
end
print(string.format("Animations.rbxm: %d sequences rebuilt", done))
