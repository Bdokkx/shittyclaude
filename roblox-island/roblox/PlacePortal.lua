-- Puts the Blender portal on its cliff.
-- 1. File > Import 3D > exports/portal/Portal.fbx   (lands in Workspace as a model called "Portal")
-- 2. Paste this into the Command Bar and press Enter.
-- It scales the imported model to the exact size of the invisible PortalSpot marker on the portal
-- cliff and snaps it into place (standing it up if the importer laid it on its side).
-- The middle of the ring is left open for your own effects.
local spot
for _, d in ipairs(workspace:GetDescendants()) do
	if d.Name == "PortalSpot" and d:IsA("BasePart") then
		spot = d
		break
	end
end
assert(spot, "PortalSpot not found - insert roblox/VoxelIsland.rbxm first")
local portal
for _, d in ipairs(workspace:GetChildren()) do
	if d:IsA("Model") and d.Name:match("^Portal") then
		portal = d
	end
end
assert(portal, "Import exports/portal/Portal.fbx first (File > Import 3D)")

local function bbox()
	local cf, size = portal:GetBoundingBox()
	return cf, size
end
local _, size = bbox()
if size.Y < size.Z * 0.9 then -- imported lying on its back: stand it up
	portal:PivotTo(portal:GetPivot() * CFrame.Angles(math.rad(-90), 0, 0))
	_, size = bbox()
end
pcall(function()
	portal:ScaleTo(portal:GetScale() * (spot.Size.Y / size.Y))
end)
local cf = bbox()
local offset = cf:ToObjectSpace(portal:GetPivot())
portal:PivotTo(spot.CFrame * offset)
for _, d in ipairs(portal:GetDescendants()) do
	if d:IsA("BasePart") then
		d.Anchored = true
	end
end
portal.Parent = spot.Parent
print("[Portal] placed on the portal cliff")
