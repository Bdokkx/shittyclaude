-- MeshSwap: replaces the part-built rocks in VoxelIsland / CoralReef with the
-- deformed, stud-textured Blender meshes.
--
-- 1. File > Import 3D > exports/meshes/VoxelRockMeshes.fbx  (import it anywhere in Workspace)
-- 2. Paste this whole file into the Command Bar (View > Command Bar) and press Enter.
--
-- It finds the imported meshes by name (ReefPinnacle_Rock, ReefPinnacle_Top, ...),
-- scales/places a copy over every matching rock, and moves the old part version to
-- ServerStorage.VoxelPartRocks (so you can put it back). Ctrl+Z undoes the whole swap.

local ChangeHistoryService = game:GetService("ChangeHistoryService")
local ServerStorage = game:GetService("ServerStorage")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local MESH_ASSETS = {
	"ReefPinnacle", "ReefPinnacleTall", "ReefShelf", "ReefArch", "Boulder",
	"RockOutcrop", "RockOutcropBig", "RockOutcropSmall", "Arch", "Seaweed",
}
-- big shapes people walk through/under get exact collisions
local PRECISE = { ReefShelf = true, ReefArch = true, Arch = true, ReefPinnacle = true, ReefPinnacleTall = true }

-- 1. collect the imported mesh parts for every asset --------------------------------
local roots = { workspace, ReplicatedStorage, ServerStorage }
local templates = {}
for _, name in ipairs(MESH_ASSETS) do
	local found = {}
	for _, root in ipairs(roots) do
		for _, d in ipairs(root:GetDescendants()) do
			if d:IsA("MeshPart") and (d.Name == name or d.Name:sub(1, #name + 1) == name .. "_")
				and not d:FindFirstAncestor("VoxelIsland") and not d:FindFirstAncestor("CoralReef") then
				local suffix = d.Name:sub(#name + 1)
				if suffix == "" or suffix == "_Rock" or suffix == "_Top" then
					table.insert(found, d)
				end
			end
		end
		if #found > 0 then
			break
		end
	end
	if #found > 0 then
		local model = Instance.new("Model")
		model.Name = name
		for _, p in ipairs(found) do
			p:Clone().Parent = model
		end
		local cf = model:GetBoundingBox()
		model.WorldPivot = CFrame.new(cf.Position)
		templates[name] = model
	end
end

local missing = {}
for _, name in ipairs(MESH_ASSETS) do
	if not templates[name] then
		table.insert(missing, name)
	end
end
if next(templates) == nil then
	warn("[MeshSwap] No imported meshes found. Import exports/meshes/VoxelRockMeshes.fbx first.")
	return
end
if #missing > 0 then
	warn("[MeshSwap] Not imported (left as parts): " .. table.concat(missing, ", "))
end

-- 2. swap every tagged rock -----------------------------------------------------------
ChangeHistoryService:SetWaypoint("Before MeshSwap")
local backup = ServerStorage:FindFirstChild("VoxelPartRocks") or Instance.new("Folder")
backup.Name = "VoxelPartRocks"
backup.Parent = ServerStorage

local swapped = 0
for _, mapName in ipairs({ "VoxelIsland", "CoralReef" }) do
	local map = workspace:FindFirstChild(mapName)
	if map then
		for _, m in ipairs(map:GetDescendants()) do
			local name = m:IsA("Model") and m:GetAttribute("VoxelAsset")
			local tmpl = name and templates[name]
			if tmpl then
				local scale = m:GetAttribute("VoxelScale") or 1
				local mn, mx = m:GetAttribute("AssetMin"), m:GetAttribute("AssetMax")
				local cf = m.WorldPivot
				local copy = tmpl:Clone()
				local _, size = copy:GetBoundingBox()
				local want = (mx.Y - mn.Y) * scale
				if size.Y > 0 then
					copy:ScaleTo(copy:GetScale() * want / size.Y)
				end
				local bb = copy:GetBoundingBox()
				local offset = bb:ToObjectSpace(copy:GetPivot())
				copy:PivotTo(cf * CFrame.new((mn + mx) * 0.5 * scale) * offset)
				for _, p in ipairs(copy:GetDescendants()) do
					if p:IsA("BasePart") then
						p.Anchored = true
						p.CanCollide = name ~= "Seaweed"
						p.CastShadow = true
						if PRECISE[name] then
							pcall(function()
								p.CollisionFidelity = Enum.CollisionFidelity.PreciseConvexDecomposition
							end)
						end
					end
				end
				copy:SetAttribute("VoxelAsset", name)
				copy:SetAttribute("VoxelMesh", true)
				copy.Parent = m.Parent
				-- keep any lights/fires that were inside the part version
				for _, d in ipairs(m:GetChildren()) do
					if d.Name == "LightSource" or d.Name == "FireSource" then
						d.Parent = copy
					end
				end
				m.Parent = backup
				swapped += 1
			end
		end
	end
end
for _, t in pairs(templates) do
	t:Destroy()
end
ChangeHistoryService:SetWaypoint("MeshSwap")
print(("[MeshSwap] swapped %d rocks for meshes. Old part rocks are in ServerStorage.VoxelPartRocks."):format(swapped))
print("[MeshSwap] You can delete the imported VoxelRockMeshes model from Workspace now.")
