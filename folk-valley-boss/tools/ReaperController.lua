--[[
ReaperController: the Grim Reaper boss's brain (a Script inside the GrimReaper model).

It plays the boss's animations and runs a simple fight AI: notice the nearest
player, roar, stalk or chase them, and pick an attack that fits the distance.
Hits land on the animation markers, the same moment the scythe connects:

  Stomp  Impact            shockwave ring round the stomping foot (jump to dodge)
  Swing  Hit               one huge sweep across the front, low (jump to dodge)
  Spin   SpinStart..End    the blade sweeps every side while it whirls
  Throw  Release..Catch    the scythe flies out, loops and comes back (dodge it)
  Roar   Roar              pushes everyone near away, no damage

Settings are attributes on the GrimReaper model:
  AI              chase and attack players on its own (off: it only animates)
  AggroRange      how far away it notices players, in studs
  WalkSpeed       stalking speed (the walk animation is made for about 7)
  ChaseSpeed      running speed (the run animation is made for about 18)
  AttackCooldown  seconds between attacks (shorter once it is enraged)
  MaxHealth       the boss's health
  Damage          health one hit takes from a player (0: knockback only)
  Knockback       how hard a hit throws players
  HealthBar       show the boss bar over its head
  RemoveOnDefeat  fade away and remove itself after the defeat animation
  AnimIdle, AnimWalk, AnimRun, AnimStomp, AnimSwing, AnimSpin, AnimThrow,
  AnimRoar, AnimHurt, AnimDefeat   published animation ids ("rbxassetid://...")

Without the AnimXxx ids it plays the KeyframeSequences in a folder named
GrimReaperAnimations (in ServerStorage, ReplicatedStorage or the model). That
works when you play-test in Studio only: a live game needs published ids.

For other scripts (all inside the model):
  ReaperAttack    BindableEvent: ReaperAttack:Fire("Swing") makes it attack now
  ReaperHit       BindableEvent fired with (player, attackName, damage) per hit
  ReaperDefeated  BindableEvent fired once when its health runs out
Optional sounds: put Sound objects in a folder named Sounds inside the model,
named Footstep, Stomp, Swing, Spin, Throw, Catch, Roar, Hurt or Defeat.
]]

local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local Debris = game:GetService("Debris")
local TweenService = game:GetService("TweenService")
local ServerStorage = game:GetService("ServerStorage")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local model = script.Parent
local humanoid = model:WaitForChild("Humanoid")
local hrp = model:WaitForChild("HumanoidRootPart")
local animator = humanoid:FindFirstChildOfClass("Animator")
if not animator then
	animator = Instance.new("Animator")
	animator.Parent = humanoid
end

local GLOW = Color3.fromRGB(122, 255, 106)
local PURPLE = Color3.fromRGB(150, 70, 230)
local WALK_PACE = 7.1 -- studs per second the walk animation's feet move at (speed 1)
local RUN_PACE = 18 -- the same for the run

-- the throw: where the whirling scythe is after Release (seconds; studs from the root part)
local THROW_PATH = {} -- filled in by gen_boss.py
-- the throw aim: (target distance, degrees to turn left) so the scythe's way out crosses the target
local THROW_AIM = {} -- filled in by gen_boss.py

local CLIPS = {
	Idle = {seq = "ReaperIdle", priority = Enum.AnimationPriority.Idle, looped = true, length = 3.4},
	Walk = {seq = "ReaperWalk", priority = Enum.AnimationPriority.Movement, looped = true, length = 1.5},
	Run = {seq = "ReaperRun", priority = Enum.AnimationPriority.Movement, looped = true, length = 0.9},
	Stomp = {seq = "ReaperStomp", priority = Enum.AnimationPriority.Action, length = 2.0},
	Swing = {seq = "ReaperSwing", priority = Enum.AnimationPriority.Action, length = 1.8},
	Spin = {seq = "ReaperSpin", priority = Enum.AnimationPriority.Action, length = 2.6},
	Throw = {seq = "ReaperThrow", priority = Enum.AnimationPriority.Action, length = 3.0},
	Roar = {seq = "ReaperRoar", priority = Enum.AnimationPriority.Action, length = 2.6},
	Hurt = {seq = "ReaperHurt", priority = Enum.AnimationPriority.Action2, length = 0.8},
	Defeat = {seq = "ReaperDefeat", priority = Enum.AnimationPriority.Action4, length = 3.4},
}
local ORDER = {"Idle", "Walk", "Run", "Stomp", "Swing", "Spin", "Throw", "Roar", "Hurt", "Defeat"}
-- when the scythe trail shows (seconds into the attack)
local TRAIL = {Swing = {0.4, 1.0}, Spin = {0.35, 2.1}, Throw = {0.45, 2.3}}

local function attr(name, default)
	local v = model:GetAttribute(name)
	if v == nil then
		return default
	end
	return v
end

local function clamp(x, lo, hi)
	if x < lo then
		return lo
	elseif x > hi then
		return hi
	end
	return x
end

local function flat(v)
	return Vector3.new(v.X, 0, v.Z)
end

local function event(name)
	local e = model:FindFirstChild(name)
	if not (e and e:IsA("BindableEvent")) then
		e = Instance.new("BindableEvent")
		e.Name = name
		e.Parent = model
	end
	return e
end
local attackEvent = event("ReaperAttack")
local hitEvent = event("ReaperHit")
local defeatedEvent = event("ReaperDefeated")

-- ---------------------------------------------------------------- state

local tracks = {}
local attacking = nil -- name of the attack playing
local defeated = false
local enraged = false
local spinning = false
local throwing = false
local lastAttack = -100
local lastAttackName = nil
local lastRoar = -100
local lastHurt = -100
local currentTarget = nil
local lastHit = {}

local function now()
	return os.clock()
end

local function find(name, class)
	local d = model:FindFirstChild(name, true)
	if d and (class == nil or d:IsA(class)) then
		return d
	end
	return nil
end

local scythe = model:FindFirstChild("Scythe")
local trail = find("ScytheTrail", "Trail")
local eyeLight = nil
local eyeAttach = find("EyeGlow", "Attachment")
if eyeAttach then
	eyeLight = eyeAttach:FindFirstChildOfClass("PointLight")
end
local mist = find("Mist", "ParticleEmitter")
local feet = {find("LeftStomp", "Attachment"), find("RightStomp", "Attachment")}

local function groundY()
	return hrp.Position.Y - hrp.Size.Y / 2 - humanoid.HipHeight
end

local function playSound(name)
	local folder = model:FindFirstChild("Sounds")
	local s = folder and folder:FindFirstChild(name)
	if s and s:IsA("Sound") then
		local c = s:Clone()
		c.Parent = hrp
		c:Play()
		Debris:AddItem(c, 8)
	end
end

-- ---------------------------------------------------------------- effects (all built-in)

local dustAttach = Instance.new("Attachment")
dustAttach.Name = "ReaperDust"
dustAttach.Parent = hrp
local dust = Instance.new("ParticleEmitter")
dust.Name = "Dust"
dust.Texture = "rbxasset://textures/particles/smoke_main.dds"
dust.Color = ColorSequence.new(Color3.fromRGB(120, 108, 140), Color3.fromRGB(60, 52, 76))
dust.Size = NumberSequence.new({NumberSequenceKeypoint.new(0, 1.5), NumberSequenceKeypoint.new(1, 5)})
dust.Transparency = NumberSequence.new({NumberSequenceKeypoint.new(0, 0.35), NumberSequenceKeypoint.new(1, 1)})
dust.Lifetime = NumberRange.new(0.6, 1.2)
dust.Speed = NumberRange.new(6, 16)
dust.SpreadAngle = Vector2.new(70, 70)
dust.Acceleration = Vector3.new(0, -4, 0)
dust.Drag = 3
dust.Rate = 0
dust.EmissionDirection = Enum.NormalId.Top
dust.Parent = dustAttach

local function puff(pos, count)
	dustAttach.WorldPosition = pos
	dust:Emit(count)
end

local function ring(center, size, color, time)
	local p = Instance.new("Part")
	p.Name = "ReaperShockwave"
	p.Shape = Enum.PartType.Cylinder
	p.Anchored = true
	p.CanCollide = false
	p.CanQuery = false
	p.CanTouch = false
	p.CastShadow = false
	p.Material = Enum.Material.Neon
	p.Color = color
	p.Transparency = 0.2
	p.Size = Vector3.new(0.35, 2, 2)
	p.CFrame = CFrame.new(center + Vector3.new(0, 0.25, 0)) * CFrame.Angles(0, 0, math.rad(90))
	p.Parent = workspace
	local info = TweenInfo.new(time, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
	TweenService:Create(p, info, {Size = Vector3.new(0.35, size, size), Transparency = 1}):Play()
	Debris:AddItem(p, time + 0.1)
end

local function burst(center, size, color, time)
	local p = Instance.new("Part")
	p.Name = "ReaperRoarWave"
	p.Shape = Enum.PartType.Ball
	p.Anchored = true
	p.CanCollide = false
	p.CanQuery = false
	p.CanTouch = false
	p.CastShadow = false
	p.Material = Enum.Material.ForceField
	p.Color = color
	p.Transparency = 0.1
	p.Size = Vector3.new(4, 4, 4)
	p.CFrame = CFrame.new(center)
	p.Parent = workspace
	local info = TweenInfo.new(time, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
	TweenService:Create(p, info, {Size = Vector3.new(size, size, size), Transparency = 1}):Play()
	Debris:AddItem(p, time + 0.1)
end

local function eyes(brightness, time)
	if eyeLight then
		TweenService:Create(eyeLight, TweenInfo.new(time), {Brightness = brightness}):Play()
	end
end

local function setTrail(on)
	if trail then
		trail.Enabled = on
	end
end

-- ---------------------------------------------------------------- boss bar

local bar = nil
local function makeBar()
	if not attr("HealthBar", true) then
		return
	end
	local gui = Instance.new("BillboardGui")
	gui.Name = "BossBar"
	gui.Size = UDim2.new(16, 0, 2.6, 0)
	gui.StudsOffset = Vector3.new(0, 1.5, 0)
	gui.MaxDistance = 300
	gui.LightInfluence = 0
	gui.ResetOnSpawn = false
	gui.Adornee = find("Overhead", "Attachment") or hrp
	local title = Instance.new("TextLabel")
	title.Name = "Title"
	title.BackgroundTransparency = 1
	title.Size = UDim2.new(1, 0, 0.5, 0)
	title.Font = Enum.Font.FredokaOne
	title.Text = "GRIM REAPER"
	title.TextScaled = true
	title.TextColor3 = GLOW
	title.TextStrokeTransparency = 0
	title.TextStrokeColor3 = Color3.fromRGB(20, 10, 30)
	title.Parent = gui
	local back = Instance.new("Frame")
	back.Name = "Back"
	back.Position = UDim2.new(0, 0, 0.56, 0)
	back.Size = UDim2.new(1, 0, 0.36, 0)
	back.BackgroundColor3 = Color3.fromRGB(24, 14, 36)
	back.BorderSizePixel = 0
	back.Parent = gui
	local corner = Instance.new("UICorner")
	corner.CornerRadius = UDim.new(0.5, 0)
	corner.Parent = back
	local fill = Instance.new("Frame")
	fill.Name = "Fill"
	fill.Size = UDim2.new(1, 0, 1, 0)
	fill.BackgroundColor3 = Color3.fromRGB(255, 255, 255)
	fill.BorderSizePixel = 0
	fill.Parent = back
	local c2 = Instance.new("UICorner")
	c2.CornerRadius = UDim.new(0.5, 0)
	c2.Parent = fill
	local grad = Instance.new("UIGradient")
	grad.Color = ColorSequence.new(PURPLE, GLOW)
	grad.Parent = fill
	gui.Parent = hrp
	bar = fill
end

local function updateBar()
	if bar then
		local k = 0
		if humanoid.MaxHealth > 0 then
			k = clamp(humanoid.Health / humanoid.MaxHealth, 0, 1)
		end
		bar.Size = UDim2.new(k, 0, 1, 0)
	end
end

-- ---------------------------------------------------------------- animations

local function findSequences()
	for _, place in ipairs({model, ServerStorage, ReplicatedStorage, workspace}) do
		local f = place:FindFirstChild("GrimReaperAnimations")
		if f then
			return f
		end
	end
	return nil
end

local function loadAnimations()
	local folder = findSequences()
	local missing = {}
	for _, name in ipairs(ORDER) do
		local info = CLIPS[name]
		local id = model:GetAttribute("Anim" .. name)
		if type(id) == "number" then
			id = "rbxassetid://" .. string.format("%.0f", id)
		end
		if (id == nil or id == "") and folder then
			local seq = folder:FindFirstChild(info.seq)
			if seq then
				local ok, res = pcall(function()
					return game:GetService("KeyframeSequenceProvider"):RegisterKeyframeSequence(seq)
				end)
				if ok then
					id = res
				end
			end
		end
		local track = nil
		if id ~= nil and id ~= "" then
			local anim = Instance.new("Animation")
			anim.Name = info.seq
			anim.AnimationId = id
			local ok, res = pcall(function()
				return animator:LoadAnimation(anim)
			end)
			if ok then
				track = res
			end
		end
		if track then
			track.Priority = info.priority
			track.Looped = info.looped == true
			tracks[name] = track
		else
			table.insert(missing, name)
		end
	end
	if #missing > 0 then
		warn("GrimReaper: no animation for " .. table.concat(missing, ", ")
			.. ". Put GrimReaperAnimations in ServerStorage (Studio tests) or set the AnimXxx attributes to published ids.")
	end
end

local moveState = nil
local function setMove(state)
	if state == moveState then
		return
	end
	moveState = state
	for _, n in ipairs({"Idle", "Walk", "Run"}) do
		local tr = tracks[n]
		if tr then
			if n == state then
				tr:Play(0.3)
			elseif tr.IsPlaying then
				tr:Stop(0.3)
			end
		end
	end
end

local function updateMove()
	if defeated then
		return
	end
	local v = hrp.AssemblyLinearVelocity
	local speed = flat(v).Magnitude
	if attacking or speed < 0.75 then
		setMove("Idle")
	elseif speed < 11 then
		setMove("Walk")
		if tracks.Walk then
			tracks.Walk:AdjustSpeed(clamp(speed / WALK_PACE, 0.6, 1.6))
		end
	else
		setMove("Run")
		if tracks.Run then
			tracks.Run:AdjustSpeed(clamp(speed / RUN_PACE, 0.7, 1.5))
		end
	end
end

-- ---------------------------------------------------------------- hitting players

local function characterOf(player)
	local char = player.Character
	if not char then
		return nil
	end
	local hum = char:FindFirstChildOfClass("Humanoid")
	local root = char:FindFirstChild("HumanoidRootPart")
	if hum and root and hum.Health > 0 then
		return char, hum, root
	end
	return nil
end

local function hitPlayer(player, attackName, from, power, damageScale)
	local char, hum, root = characterOf(player)
	if not char then
		return
	end
	local t = now()
	if lastHit[player] and t - lastHit[player] < 0.6 then
		return
	end
	lastHit[player] = t
	local dir = flat(root.Position - from)
	if dir.Magnitude < 0.1 then
		dir = flat(hrp.CFrame.LookVector)
	end
	dir = dir.Unit
	local kb = attr("Knockback", 70) * power
	if kb > 0 then
		local att = root:FindFirstChild("RootAttachment")
		if not (att and att:IsA("Attachment")) then
			att = Instance.new("Attachment")
			att.Name = "RootAttachment"
			att.Parent = root
		end
		local push = Instance.new("LinearVelocity")
		push.Name = "ReaperKnockback"
		push.Attachment0 = att
		push.RelativeTo = Enum.ActuatorRelativeTo.World
		push.VelocityConstraintMode = Enum.VelocityConstraintMode.Vector
		push.MaxForce = 1e6
		push.VectorVelocity = dir * kb + Vector3.new(0, kb * 0.55, 0)
		push.Parent = root
		Debris:AddItem(push, 0.18)
	end
	local damage = attr("Damage", 0) * damageScale
	if damage > 0 then
		hum:TakeDamage(damage)
	end
	hitEvent:Fire(player, attackName, damage)
end

-- every player standing (not jumping clear) within `radius` of `center`, optionally inside a cone
local function playersNear(center, radius, maxHeight, look, halfAngle)
	local out = {}
	for _, player in ipairs(Players:GetPlayers()) do
		local char, _, root = characterOf(player)
		if char then
			local off = flat(root.Position - center)
			local d = off.Magnitude
			local up = root.Position.Y - center.Y
			if d <= radius and up < maxHeight and up > -6 then
				local inCone = true
				if look and d > 4 then
					inCone = look:Dot(off.Unit) >= math.cos(math.rad(halfAngle))
				end
				if inCone then
					table.insert(out, player)
				end
			end
		end
	end
	return out
end

local function floorPoint(offset)
	return (hrp.CFrame * CFrame.new(offset.X, -(hrp.Size.Y / 2 + humanoid.HipHeight), offset.Z)).Position
end

local function pathAt(t)
	local n = #THROW_PATH
	if n == 0 or t > THROW_PATH[n][1] then
		return nil
	end
	for i = 2, n do
		local a, b = THROW_PATH[i - 1], THROW_PATH[i]
		if t <= b[1] then
			local k = 0
			if b[1] > a[1] then
				k = (t - a[1]) / (b[1] - a[1])
			end
			return Vector3.new(a[2] + (b[2] - a[2]) * k, a[3] + (b[3] - a[3]) * k, a[4] + (b[4] - a[4]) * k)
		end
	end
	return Vector3.new(THROW_PATH[1][2], THROW_PATH[1][3], THROW_PATH[1][4])
end

local MARKERS = {
	Stomp = {
		Impact = function()
			local center = floorPoint(Vector3.new(1.5, 0, -3.2))
			ring(center, 38, GLOW, 0.5)
			puff(center, 40)
			playSound("Stomp")
			for _, player in ipairs(playersNear(center, 18, 7)) do
				hitPlayer(player, "Stomp", center, 1.0, 1.0)
			end
		end,
	},
	Swing = {
		Hit = function()
			local center = floorPoint(Vector3.new(0, 0, 0))
			for _, player in ipairs(playersNear(center, 24, 7.5, flat(hrp.CFrame.LookVector).Unit, 80)) do
				hitPlayer(player, "Swing", center, 1.0, 1.2)
			end
		end,
	},
	Spin = {
		SpinStart = function()
			spinning = true
			playSound("Spin")
			task.spawn(function()
				while spinning and not defeated do
					local center = floorPoint(Vector3.new(0, 0, 0))
					for _, player in ipairs(playersNear(center, 22, 7.5)) do
						hitPlayer(player, "Spin", center, 0.8, 0.6)
					end
					task.wait(0.1)
				end
			end)
		end,
		SpinEnd = function()
			spinning = false
		end,
	},
	Throw = {
		Release = function()
			throwing = true
			playSound("Throw")
			local start = now()
			local base = hrp.CFrame
			local struck = {}
			task.spawn(function()
				while throwing and not defeated do
					local p = pathAt(now() - start)
					if not p then
						break
					end
					local pos = (base * CFrame.new(p)).Position
					for _, player in ipairs(Players:GetPlayers()) do
						local char, _, root = characterOf(player)
						if char and not struck[player] then
							local d = flat(root.Position - pos).Magnitude
							if d <= 8 and math.abs(root.Position.Y - pos.Y) < 5 then
								struck[player] = true
								hitPlayer(player, "Throw", pos, 1.0, 1.0)
							end
						end
					end
					RunService.Heartbeat:Wait()
				end
			end)
		end,
		Catch = function()
			throwing = false
			playSound("Catch")
		end,
	},
	Roar = {
		Roar = function()
			local head = find("Mouth", "Attachment")
			local center = head and head.WorldPosition or hrp.Position
			burst(center, 60, PURPLE, 0.7)
			eyes(12, 0.15)
			task.delay(0.9, function()
				if not defeated then
					eyes(3, 0.6)
				end
			end)
			playSound("Roar")
			local floor = floorPoint(Vector3.new(0, 0, 0))
			for _, player in ipairs(playersNear(floor, 40, 30)) do
				hitPlayer(player, "Roar", floor, 0.6, 0)
			end
		end,
	},
	Walk = {
		Footstep = function()
			local f = feet[1]
			if feet[2] and (f == nil or feet[2].WorldPosition.Y < f.WorldPosition.Y) then
				f = feet[2]
			end
			if f then
				puff(f.WorldPosition, 5)
			end
			playSound("Footstep")
		end,
	},
}
MARKERS.Run = MARKERS.Walk

local function hookMarkers()
	for name, marks in pairs(MARKERS) do
		local tr = tracks[name]
		if tr then
			for marker, fn in pairs(marks) do
				tr:GetMarkerReachedSignal(marker):Connect(function()
					if not defeated then
						fn()
					end
				end)
			end
		end
	end
end

-- ---------------------------------------------------------------- attacks

local function face(point, time)
	local pos = hrp.Position
	local target = Vector3.new(point.X, pos.Y, point.Z)
	if (target - pos).Magnitude < 0.5 then
		return
	end
	local from = hrp.CFrame - pos
	local goal = CFrame.lookAt(pos, target) - pos
	local t0 = now()
	while true do
		local k = clamp((now() - t0) / time, 0, 1)
		hrp.CFrame = CFrame.new(hrp.Position) * from:Lerp(goal, k)
		if k >= 1 then
			break
		end
		RunService.Heartbeat:Wait()
	end
end

local function interp(tbl, x)
	local n = #tbl
	if n == 0 then
		return 0
	end
	if x <= tbl[1][1] then
		return tbl[1][2]
	end
	for i = 2, n do
		if x <= tbl[i][1] then
			local a, b = tbl[i - 1], tbl[i]
			return a[2] + (b[2] - a[2]) * (x - a[1]) / (b[1] - a[1])
		end
	end
	return tbl[n][2]
end

-- face so that the target sits where the scythe's way out passes
local function throwAim(targetPos)
	local off = flat(targetPos - hrp.Position)
	if off.Magnitude < 1 then
		return targetPos
	end
	local turn = math.rad(interp(THROW_AIM, off.Magnitude))
	return hrp.Position + (CFrame.Angles(0, turn, 0) * off.Unit) * 10
end

local function doAttack(name, targetPos)
	local tr = tracks[name]
	if not tr or defeated then
		if attacking == name then
			attacking = nil
		end
		return
	end
	attacking = name
	humanoid.WalkSpeed = 0
	humanoid:Move(Vector3.new(0, 0, 0))
	humanoid:MoveTo(hrp.Position)
	humanoid.AutoRotate = false
	if targetPos then
		if name == "Throw" then
			face(throwAim(targetPos), 0.3)
		else
			face(targetPos, 0.25)
		end
	end
	if defeated then
		return
	end
	if name ~= "Spin" and name ~= "Throw" and name ~= "Roar" then
		playSound(name)
	end
	tr:Play(0.12, 1, 1)
	local window = TRAIL[name]
	if window then
		task.delay(window[1], function()
			if attacking == name and not defeated then
				setTrail(true)
			end
		end)
		task.delay(window[2], function()
			setTrail(false)
		end)
	end
	local started = now()
	local length = CLIPS[name].length
	while not defeated and now() - started < length + 0.5 do
		if not tr.IsPlaying and now() - started > 0.3 then
			break
		end
		task.wait(0.05)
	end
	spinning = false
	throwing = false
	setTrail(false)
	humanoid.AutoRotate = true
	if not defeated then
		attacking = nil
	end
	lastAttack = now()
	lastAttackName = name
end

local function pick(options)
	local total = 0
	for _, o in ipairs(options) do
		if tracks[o[1]] then
			local w = o[2]
			if o[1] == lastAttackName then
				w = w * 0.35
			end
			total = total + w
		end
	end
	if total <= 0 then
		return nil
	end
	local r = math.random() * total
	for _, o in ipairs(options) do
		if tracks[o[1]] then
			local w = o[2]
			if o[1] == lastAttackName then
				w = w * 0.35
			end
			r = r - w
			if r <= 0 then
				return o[1]
			end
		end
	end
	return options[#options][1]
end

local function chooseAttack(dist)
	if dist <= 15 then
		return pick({{"Stomp", 4}, {"Spin", 3}, {"Swing", 3}})
	elseif dist <= 23 then
		return pick({{"Swing", 6}, {"Spin", 4}})
	elseif dist <= 33 then
		return pick({{"Throw", 1}})
	end
	return nil
end

local function startAttack(name, targetPos)
	if attacking or defeated or not tracks[name] then
		return false
	end
	attacking = name
	task.spawn(doAttack, name, targetPos)
	return true
end

-- ---------------------------------------------------------------- the AI

local function nearestPlayer(range)
	local best, bestDist = nil, range
	for _, player in ipairs(Players:GetPlayers()) do
		local char, _, root = characterOf(player)
		if char then
			local d = flat(root.Position - hrp.Position).Magnitude
			if d < bestDist then
				best, bestDist = player, d
			end
		end
	end
	return best, bestDist
end

local function aiStep()
	if defeated or attacking or not attr("AI", true) then
		return
	end
	local target, dist = nearestPlayer(attr("AggroRange", 140))
	if not target then
		if currentTarget then
			humanoid:MoveTo(hrp.Position)
		end
		currentTarget = nil
		return
	end
	local _, _, root = characterOf(target)
	if target ~= currentTarget then
		currentTarget = target
		if now() - lastRoar > 25 and startAttack("Roar", root.Position) then
			lastRoar = now()
			return
		end
	end
	local cooldown = attr("AttackCooldown", 2.5)
	if enraged then
		cooldown = cooldown * 0.65
	end
	if now() - lastAttack >= cooldown then
		local choice = chooseAttack(dist)
		if choice and startAttack(choice, root.Position) then
			return
		end
	end
	local speed = attr("WalkSpeed", 8)
	if dist > 30 then
		speed = attr("ChaseSpeed", 20)
	end
	if enraged then
		speed = speed * 1.15
	end
	humanoid.WalkSpeed = speed
	if dist > 10 then
		humanoid:MoveTo(root.Position)
	else
		humanoid:MoveTo(hrp.Position)
	end
end

-- ---------------------------------------------------------------- hurt and defeat

local function defeat()
	if defeated then
		return
	end
	defeated = true
	attacking = "Defeat"
	spinning = false
	throwing = false
	setTrail(false)
	humanoid.WalkSpeed = 0
	humanoid:Move(Vector3.new(0, 0, 0))
	humanoid.AutoRotate = false
	hrp.Anchored = true
	for name, tr in pairs(tracks) do
		if name ~= "Defeat" and tr.IsPlaying then
			tr:Stop(0.25)
		end
	end
	playSound("Defeat")
	local tr = tracks.Defeat
	if tr then
		tr:GetMarkerReachedSignal("Collapsed"):Connect(function()
			eyes(0, 1.2)
			if mist then
				mist.Enabled = false
			end
			puff(floorPoint(Vector3.new(0, 0, -1)), 30)
		end)
		tr:GetMarkerReachedSignal("ScytheDrop"):Connect(function()
			if scythe then
				puff(scythe.Position, 12)
			end
		end)
		tr:Play(0.2)
	else
		eyes(0, 1.2)
	end
	defeatedEvent:Fire()
	task.delay(CLIPS.Defeat.length + 1.5, function()
		if not attr("RemoveOnDefeat", true) then
			return
		end
		local info = TweenInfo.new(1.5)
		for _, d in ipairs(model:GetDescendants()) do
			if d:IsA("BasePart") and d.Transparency < 1 then
				TweenService:Create(d, info, {Transparency = 1}):Play()
			elseif d:IsA("BillboardGui") then
				d.Enabled = false
			end
		end
		task.wait(1.6)
		model:Destroy()
	end)
end

local lastHealth = humanoid.Health
local function onHealth(health)
	updateBar()
	if defeated then
		return
	end
	if health <= 0 then
		defeat()
		return
	end
	if health < lastHealth then
		if not enraged and health <= humanoid.MaxHealth * 0.5 then
			enraged = true
			if mist then
				mist.Rate = mist.Rate * 2
			end
			if not attacking then
				startAttack("Roar", currentTarget and currentTarget.Character and currentTarget.Character:GetPivot().Position)
			end
		elseif not attacking and now() - lastHurt > 1.0 and tracks.Hurt then
			lastHurt = now()
			tracks.Hurt:Play(0.05)
			eyes(10, 0.05)
			task.delay(0.25, function()
				if not defeated then
					eyes(3, 0.3)
				end
			end)
			playSound("Hurt")
		end
	end
	lastHealth = health
end

-- ---------------------------------------------------------------- start

humanoid.MaxHealth = attr("MaxHealth", 1000)
humanoid.Health = humanoid.MaxHealth
lastHealth = humanoid.Health
humanoid.BreakJointsOnDeath = false
humanoid.RequiresNeck = false
-- it never "dies" like a player: the defeat is its own animation
humanoid:SetStateEnabled(Enum.HumanoidStateType.Dead, false)
humanoid:SetStateEnabled(Enum.HumanoidStateType.FallingDown, false)
humanoid:SetStateEnabled(Enum.HumanoidStateType.Ragdoll, false)
humanoid:SetStateEnabled(Enum.HumanoidStateType.Climbing, false)
humanoid:SetStateEnabled(Enum.HumanoidStateType.Jumping, false)
pcall(function()
	hrp:SetNetworkOwner(nil)
end)
setTrail(false)
makeBar()
updateBar()
loadAnimations()
hookMarkers()
setMove("Idle")

humanoid.HealthChanged:Connect(onHealth)
attackEvent.Event:Connect(function(name)
	local pos = nil
	if currentTarget and currentTarget.Character then
		pos = currentTarget.Character:GetPivot().Position
	end
	startAttack(name, pos)
end)
RunService.Heartbeat:Connect(updateMove)

while model.Parent and not defeated do
	aiStep()
	task.wait(0.15)
end
