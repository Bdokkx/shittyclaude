--[[ AnimateScenery (Pumpkin Hollow / October map)

Exported as a Script with RunContext = Client inside the map Model, so it runs on every player's machine
wherever the map is parented in Workspace (the server never runs it and nothing is replicated).

  Ghosts  float up and down, sway, slowly turn and drift in small circles; their arms wave.
  Bats    circle the haunted house's tower at different speeds and heights, flapping their wings.
  Cauldron  green bubbles rise out of the brew, swell, pop and come back somewhere else; the brew churns.

Everything is measured relative to the map's pivot, so the map can be moved/pivoted by the game
before or after it is parented. Animation pauses when the map is far from the camera.
]]
local RunService = game:GetService("RunService")

local map = script.Parent
local scenery = map:WaitForChild("Scenery")
local MAX_DISTANCE = 600 -- studs from the camera before animation pauses

local function partsOf(model, pivot)
	local list = {}
	for _, p in model:GetDescendants() do
		if p:IsA("BasePart") then
			table.insert(list, { part = p, rel = pivot:ToObjectSpace(p.CFrame), name = p.Name })
		end
	end
	return list
end

local mapPivot0 = map:GetPivot()
local ghosts, bats = {}, {}
local batCentre, nBats = Vector3.zero, 0

for _, m in scenery:GetChildren() do
	if m:IsA("Model") and (m.Name == "Ghost" or m.Name == "Bat") then
		local pivot = m:GetPivot()
		local item = {
			model = m,
			base = mapPivot0:ToObjectSpace(pivot), -- pose relative to the map
			parts = partsOf(m, pivot),
			phase = math.random() * 10,
			speed = 0.8 + math.random() * 0.5,
		}
		if m.Name == "Ghost" then
			table.insert(ghosts, item)
		else
			table.insert(bats, item)
			batCentre += item.base.Position
			nBats += 1
		end
	end
end
-- cauldrons: bubbles + brew surface, all relative to the cauldron's pivot
local cauldrons = {}
for _, m in scenery:GetChildren() do
	if m:IsA("Model") and m.Name == "Cauldron" then
		local pivot = m:GetPivot()
		local c = { base = mapPivot0:ToObjectSpace(pivot), bubbles = {}, brew = {} }
		local sum, n, top = Vector3.zero, 0, -math.huge
		for _, p in m:GetDescendants() do
			if p:IsA("BasePart") and p.Name == "Brew" then
				local rel = pivot:ToObjectSpace(p.CFrame)
				table.insert(c.brew, { part = p, rel = rel })
				sum += rel.Position
				n += 1
				top = math.max(top, rel.Position.Y + p.Size.Y / 2)
			end
		end
		for _, p in m:GetDescendants() do
			if p:IsA("BasePart") and p.Name == "Bubble" then
				table.insert(c.bubbles, { part = p, period = 1.1 + (#c.bubbles % 4) * 0.23, phase = #c.bubbles * 0.37 })
			end
		end
		if n > 0 then
			c.centre = Vector3.new(sum.X / n, top, sum.Z / n)
			table.insert(cauldrons, c)
		end
	end
end
local function hash(x) -- 0..1, deterministic
	local v = math.sin(x * 12.9898) * 43758.5453
	return v - math.floor(v)
end

if nBats > 0 then
	batCentre /= nBats
end
for _, b in bats do -- each bat orbits the flock centre at its own radius / height / direction
	local off = b.base.Position - batCentre
	b.radius = math.max(6, Vector3.new(off.X, 0, off.Z).Magnitude)
	b.angle0 = math.atan2(off.Z, off.X)
	b.height = off.Y
	b.dir = (math.random() < 0.75) and 1 or -1
	b.angular = (0.5 + math.random() * 0.5) * b.dir
end

local function apply(item, pivot, extra)
	for _, e in item.parts do
		local cf = pivot * e.rel
		if extra then
			cf = extra(e, pivot) or cf
		end
		e.part.CFrame = cf
	end
end

-- wing flap: rotate each wing about its hinge on the body (x = +-0.35, y = 0.15 in bat space)
local HINGE_L, HINGE_R = CFrame.new(-0.35, 0.15, 0), CFrame.new(0.35, 0.15, 0)
local function flapped(rel, hinge, angle)
	return hinge * CFrame.Angles(0, 0, angle) * hinge:Inverse() * rel
end

local t = 0
RunService.Heartbeat:Connect(function(dt)
	if not map.Parent then return end
	local camera = workspace.CurrentCamera
	local mapPivot = map:GetPivot()
	if camera and (camera.CFrame.Position - mapPivot.Position).Magnitude > MAX_DISTANCE then return end
	t += dt

	for _, g in ghosts do
		local s = t * g.speed + g.phase
		local drift = Vector3.new(math.cos(s * 0.35) * 2.5, math.sin(s * 1.6) * 1.2, math.sin(s * 0.35) * 2.5)
		local pose = mapPivot * g.base
			* CFrame.new(drift)
			* CFrame.Angles(math.sin(s * 1.1) * 0.06, math.sin(s * 0.4) * 0.7, math.sin(s * 1.3) * 0.1)
		local wave = math.sin(s * 3) * 0.35
		apply(g, pose, function(e, pivot)
			if e.name == "ArmL" or e.name == "ArmR" then
				local side = e.name == "ArmL" and -1 or 1
				local shoulder = CFrame.new(side * 1.2, e.rel.Position.Y + 0.6, 0)
				return pivot * (shoulder * CFrame.Angles(0, 0, side * wave) * shoulder:Inverse() * e.rel)
			end
		end)
	end

	for _, c in cauldrons do
		local pivot = mapPivot * c.base
		local churn = math.sin(t * 3.1) * 0.05
		for i, e in c.brew do
			e.part.CFrame = pivot * CFrame.new(0, churn, 0) * e.rel * CFrame.Angles(0, math.sin(t * 0.8 + i) * 0.04, 0)
		end
		for i, b in c.bubbles do
			local x = (t + b.phase) / b.period
			local cycle = math.floor(x)
			local u = x - cycle -- 0 = just appeared at the surface, 1 = gone
			local a = hash(cycle * 7.13 + i) * math.pi * 2
			local r = math.sqrt(hash(cycle * 3.71 + i * 1.3)) * 1.6
			local size, transparency
			if u < 0.75 then
				size = 0.2 + 0.55 * (u / 0.75)
				transparency = 0
			else -- pop: swell quickly, then vanish
				local k = (u - 0.75) / 0.25
				size = 0.75 + 0.45 * k
				transparency = math.min(1, k * 1.6)
			end
			local wobble = math.sin(t * 9 + i) * 0.08
			b.part.Size = Vector3.new(size, size, size)
			b.part.Transparency = transparency
			b.part.CFrame = pivot * CFrame.new(c.centre.X + math.cos(a) * r + wobble, c.centre.Y + 0.1 + u * 1.6,
				c.centre.Z + math.sin(a) * r) * CFrame.Angles(0, u * 2 + i, 0)
		end
	end

	local centre = mapPivot * batCentre
	for _, b in bats do
		local a = b.angle0 + t * b.angular
		local pos = centre + Vector3.new(math.cos(a) * b.radius, b.height + math.sin(t * 2 + b.phase) * 1.5,
			math.sin(a) * b.radius)
		local tangent = Vector3.new(-math.sin(a), 0, math.cos(a)) * b.dir
		local bank = CFrame.Angles(0, 0, -0.35 * b.dir)
		local pose = CFrame.lookAt(pos, pos + tangent) * bank
		local flap = math.sin(t * 14 * b.speed + b.phase) * 0.7
		apply(b, pose, function(e, pivot)
			if e.name == "WingL" then
				return pivot * flapped(e.rel, HINGE_L, -flap)
			elseif e.name == "WingR" then
				return pivot * flapped(e.rel, HINGE_R, flap)
			end
		end)
	end
end)
