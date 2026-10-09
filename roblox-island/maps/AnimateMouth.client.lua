--[[ AnimateMouth (Monster Mouth event piece)

Exported as a Script with RunContext = Client inside the MonsterMouth model: runs on every player's machine
wherever the model sits in Workspace; nothing is replicated.

  Swirl  the purple spiral slowly turns, like it is sucking things down
  Eyes   each pair blinks now and then, at its own random times
  Mist   wisps drift round the rim and fade in and out

Everything is measured from the MouthTrigger part, so the model can be moved or rotated by the game.
]]
local RunService = game:GetService("RunService")

local mouth = script.Parent
local void = mouth:WaitForChild("MouthTrigger") -- unique, centred on the hole, never moved by this script
local MAX_DISTANCE = 400

local centre0 = void.CFrame
local swirl, eyes, mist = {}, {}, {}
for _, p in mouth:GetDescendants() do
	if p:IsA("BasePart") then
		local entry = { part = p, rel = centre0:ToObjectSpace(p.CFrame), tr = p.Transparency }
		if p.Name == "Swirl" then
			table.insert(swirl, entry)
		elseif p.Name == "Eye" then
			table.insert(eyes, entry)
		elseif p.Name == "Mist" then
			entry.phase = math.random() * 10
			entry.speed = 0.08 + math.random() * 0.1
			table.insert(mist, entry)
		end
	end
end
-- eyes blink in pairs: group by parent model
local pairsByModel = {}
for _, e in eyes do
	local key = e.part.Parent
	pairsByModel[key] = pairsByModel[key] or { parts = {}, nextBlink = 1 + math.random() * 4, closedUntil = 0 }
	table.insert(pairsByModel[key].parts, e.part)
end

local t = 0
RunService.Heartbeat:Connect(function(dt)
	if not mouth.Parent then return end
	local camera = workspace.CurrentCamera
	local centre = void.CFrame
	if camera and (camera.CFrame.Position - centre.Position).Magnitude > MAX_DISTANCE then return end
	t += dt

	local spin = CFrame.Angles(0, -t * 0.7, 0)
	for _, e in swirl do
		e.part.CFrame = centre * spin * e.rel
	end

	for _, pair in pairsByModel do
		if t >= pair.nextBlink then
			pair.closedUntil = t + 0.14
			pair.nextBlink = t + 2 + math.random() * 5
		end
		local closed = t < pair.closedUntil
		for _, p in pair.parts do
			p.Transparency = closed and 1 or 0
		end
	end

	for _, e in mist do
		local s = t * e.speed + e.phase
		e.part.CFrame = centre * CFrame.Angles(0, s, 0) * e.rel * CFrame.new(0, math.sin(s * 6) * 0.15, 0)
		e.part.Transparency = math.clamp(e.tr + math.sin(s * 9) * 0.12, 0, 0.95)
	end
end)
