"""Write the Roblox Studio Command Bar script that turns the imported FBX meshes
into the game's Props folder and the two restyled NPCs.

    python tools/gen_build.py <orig_props.json> <orig_npc.json> <props.json> <npc_meta.json> <out.lua>

orig_*.json are rbxtool dumps of the files the game uses (props.rbxm, npc.rbxm);
props.json / npc_meta.json come from blender/build.py.
"""
import base64
import json
import sys

PROP_KEYS = ["Shape", "Size", "CFrame", "Color", "Material", "Transparency", "Reflectance", "Anchored", "CanCollide",
             "CanTouch", "CanQuery", "Massless", "CastShadow", "Locked", "TopSurface", "BottomSurface", "FrontSurface",
             "BackSurface", "LeftSurface", "RightSurface"]
CLASS_KEYS = {
    "Part": PROP_KEYS, "WedgePart": [k for k in PROP_KEYS if k != "Shape"],
    "Attachment": ["CFrame"],
    "Motor6D": ["C0", "C1"],
    "Humanoid": ["RigType", "DisplayDistanceType", "HealthDisplayType", "HipHeight", "DisplayName", "NameDisplayDistance",
                 "HealthDisplayDistance", "MaxHealth", "Health", "WalkSpeed", "BreakJointsOnDeath", "RequiresNeck",
                 "AutomaticScalingEnabled", "AutoRotate", "NameOcclusion"],
    "Animator": [],
    "ProximityPrompt": ["ActionText", "ObjectText", "HoldDuration", "MaxActivationDistance", "KeyboardKeyCode",
                        "GamepadKeyCode", "RequiresLineOfSight", "Style", "UIOffset", "Enabled", "ClickablePrompt",
                        "Exclusivity"],
    "SpecialMesh": ["MeshType", "MeshId", "TextureId", "Scale", "Offset", "VertexColor"],
    "Decal": ["Texture", "Face", "Color3", "Transparency", "ZIndex"],
    "Folder": [], "Model": [],
}
ENUMS = {"Shape": "PartType", "Material": "Material", "TopSurface": "SurfaceType", "BottomSurface": "SurfaceType",
         "FrontSurface": "SurfaceType", "BackSurface": "SurfaceType", "LeftSurface": "SurfaceType",
         "RightSurface": "SurfaceType", "MeshType": "MeshType", "Face": "NormalId", "RigType": "HumanoidRigType",
         "DisplayDistanceType": "HumanoidDisplayDistanceType", "HealthDisplayType": "HumanoidHealthDisplayType",
         "NameOcclusion": "NameOcclusion", "KeyboardKeyCode": "KeyCode", "GamepadKeyCode": "KeyCode",
         "Style": "ProximityPromptStyle", "Exclusivity": "ProximityPromptExclusivity"}
ALIASES = {"MeshId": ("MeshContent", "MeshId"), "TextureId": ("TextureContent", "TextureId"),
           "Texture": ("TextureContent", "Texture")}
FLAGS = ["Anchored", "CanCollide", "CanTouch", "CanQuery", "Massless"]


def num(v, nd=5):
    s = ("%." + str(nd) + "f") % v
    s = s.rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def lstr(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def cframe(c, scale=1.0, origin=None):
    c = c["CFrame"] if "CFrame" in c else c
    p = list(c["position"])
    if origin is not None:
        p = [origin[i] + (p[i] - origin[i]) * scale for i in range(3)]
    r = c["orientation"]
    return "CFrame.new(%s)" % ", ".join(num(x) for x in p + [r[i][j] for i in range(3) for j in range(3)])


def content(v):
    c = v.get("Content", v)
    if isinstance(c, dict):
        c = c.get("Uri", "")
    if c in (None, "None"):
        c = ""
    c = str(c)
    if "assetdelivery.roblox.com" in c and "id=" in c:
        c = "rbxassetid://" + c.split("id=")[1].split("&")[0]
    return lstr(c)


def value(key, v, scale=1.0, origin=None):
    """rbxtool JSON property -> Lua expression (None to skip)."""
    t, x = next(iter(v.items()))
    if key in ENUMS and t == "Enum":
        return "E(Enum.%s, %d)" % (ENUMS[key], x)
    if t == "Vector3":
        return "Vector3.new(%s)" % ", ".join(num(a * (scale if key == "Size" else 1.0)) for a in x)
    if t == "Vector2":
        return "Vector2.new(%s)" % ", ".join(num(a) for a in x)
    if t == "CFrame":
        return cframe(x, scale if key == "CFrame" else 1.0, origin if key == "CFrame" else None)
    if t == "Color3uint8":
        return "Color3.fromRGB(%d, %d, %d)" % tuple(x)
    if t == "Color3":
        return "Color3.new(%s)" % ", ".join(num(a) for a in x)
    if t == "Bool":
        return "true" if x else "false"
    if t in ("Float32", "Float64", "Int32", "Int64"):
        return num(x)
    if t == "String":
        return lstr(x)
    if t in ("Content", "ContentId"):
        return content(v)
    return None


def props_list(node, scale=1.0, origin=None):
    out = []
    p = node["props"]
    for key in CLASS_KEYS.get(node["class"], []):
        src = None
        for alias in ALIASES.get(key, (key,)):
            if alias in p:
                src = p[alias]
                break
        if src is None:
            continue
        val = value(key, src, scale, origin)
        if val is not None:
            out.append("{%s, %s}" % (lstr(key), val))
    return "{" + ", ".join(out) + "}"


def attributes(node):
    attrs = node["props"].get("Attributes", {}).get("Attributes", {})
    out = []
    for k, v in attrs.items():
        t, x = next(iter(v.items()))
        if t == "BinaryString":
            out.append("[%s] = %s" % (lstr(k), lstr(base64.b64decode(x).decode("utf-8", "replace"))))
        elif t in ("Float64", "Float32", "Int32"):
            out.append("[%s] = %s" % (lstr(k), num(x)))
        elif t == "Bool":
            out.append("[%s] = %s" % (lstr(k), "true" if x else "false"))
        elif t == "String":
            out.append("[%s] = %s" % (lstr(k), lstr(x)))
    return "{" + ", ".join(out) + "}"


def visible(n):
    return n["class"] in ("Part", "WedgePart", "UnionOperation", "MeshPart", "CornerWedgePart") and \
        n["props"].get("Transparency", {}).get("Float32", 0) < 0.99


def flags_of(n):
    return {f: n["props"][f]["Bool"] for f in FLAGS + ["CastShadow"] if f in n["props"]}


def common(dicts):
    out = {}
    for k in dicts[0] if dicts else []:
        vals = [d.get(k) for d in dicts]
        if all(v == vals[0] for v in vals):
            out[k] = vals[0]
    return out


# ---------------------------------------------------------------- props

KEEP_VISIBLE = {"Trapdoor": {"Void"}}     # visible originals that stay as they are


def prop_entry(orig, new, library=True):
    """Lua table for one prop: kept original instances + the new mesh parts."""
    pid = new["Id"]
    scale = 1.0
    if orig is not None:
        sc = orig["props"].get("Scale", {}).get("Float32", 1.0)
        scale = sc if abs(sc - 1.0) > 1e-4 else 1.0
    lines = []
    keep, models = [], []
    vis_flags, by_name = [], {}
    welded = False
    origin = None
    if orig is not None:
        h = next(c for c in orig["children"] if c["name"] == "Handle")
        origin = h["props"]["CFrame"]["CFrame"]["position"]
        inv = 1.0 / scale

        def walk(node, model_idx):
            nonlocal welded
            for c in node["children"]:
                if c["class"] == "Model":
                    models.append(c)
                    walk(c, len(models))
                    continue
                if c["class"] not in ("Part", "WedgePart", "UnionOperation", "MeshPart"):
                    continue
                if any(k["class"] == "WeldConstraint" for k in c.get("children", [])):
                    if c["name"] != "Handle":
                        welded = True
                if visible(c) and c["name"] not in KEEP_VISIBLE.get(pid, ()):
                    vis_flags.append(flags_of(c))
                    by_name.setdefault(c["name"], flags_of(c))
                    continue
                if c["class"] not in ("Part", "WedgePart"):
                    raise SystemExit("%s: can't keep a %s (%s)" % (pid, c["class"], c["name"]))
                primary = node["class"] == "Model" and node["props"].get("PrimaryPart", {}).get("Ref") == c["ref"]
                keep.append("{Class = %s, Name = %s, Model = %s, Primary = %s, Props = %s}" % (
                    lstr(c["class"]), lstr(c["name"]), model_idx or "nil", "true" if primary else "false",
                    props_list(c, inv, origin)))
        walk(orig, None)
    else:
        keep.append('{Class = "Part", Name = "Handle", Model = nil, Primary = true, Props = {'
                    '{"Size", Vector3.new(0.4, 0.4, 0.4)}, {"CFrame", CFrame.new(0, 3000, 0)}, {"Transparency", 1}, '
                    '{"Anchored", false}, {"CanCollide", false}, {"CanTouch", false}, {"CanQuery", false}, '
                    '{"Massless", true}, {"TopSurface", E(Enum.SurfaceType, 0)}, {"BottomSurface", E(Enum.SurfaceType, 0)}}}')
        welded = True
    base = common(vis_flags) if vis_flags else {"Anchored": False, "CanCollide": False, "CanTouch": False,
                                                 "CanQuery": False, "Massless": True, "CastShadow": True}
    attrs = attributes(orig) if orig is not None else "{}"
    if orig is not None:
        a = orig["props"].get("Attributes", {}).get("Attributes", {})
        if "Top" in a or "Bottom" in a:
            attrs = "{Top = %s, Bottom = %s}" % (num(new["Top"] / scale, 3), num(new["Bottom"] / scale, 3))
    lines.append("\t{Id = %s, Library = %s, Scale = %s, Weld = %s, Attributes = %s," % (
        lstr(pid), "true" if library else "false", num(scale) if scale != 1.0 else "nil", "true" if welded else "false",
        attrs))
    lines.append("\t\tModels = {%s}," % ", ".join(
        "{Name = %s}" % lstr(m["name"]) for m in models))
    lines.append("\t\tKeep = {")
    for k in keep:
        lines.append("\t\t\t" + k + ",")
    lines.append("\t\t},")
    lines.append("\t\tParts = {")
    for p in new["Parts"]:
        f = dict(base)
        f.update(by_name.get(p["Name"], {}))
        if p.get("CastShadow") is not None:
            f["CastShadow"] = p["CastShadow"]
        f.setdefault("CastShadow", True)
        lines.append("\t\t\t{Name = %s, Mesh = %s, Model = %s, Color = Color3.fromRGB(%d, %d, %d), "
                     "Material = Enum.Material.%s, Transparency = %s, Center = Vector3.new(%s), Size = Vector3.new(%s), "
                     "Flags = {%s}}," % (
                         lstr(p["Name"]), lstr(p["Mesh"]), (p["Model"] + 1) if p.get("Model") is not None else "nil",
                         *p["Color"], p["Material"], num(p["Transparency"]),
                         ", ".join(num(v / scale) for v in p["Center"]), ", ".join(num(v / scale) for v in p["Size"]),
                         ", ".join("%s = %s" % (k, "true" if v else "false") for k, v in sorted(f.items()))))
    lines.append("\t\t},")
    lines.append("\t},")
    return lines


# ---------------------------------------------------------------- NPCs

def tree(node, skip=("Outfit",)):
    """Lua table rebuilding an instance and its children (refs by part name)."""
    kids = [tree(c) for c in node.get("children", []) if c["name"] not in skip and c["class"] in CLASS_KEYS]
    refs = []
    p = node["props"]
    for key in ("Part0", "Part1", "PrimaryPart"):
        r = p.get(key, {}).get("Ref")
        if r and r in REFS:
            refs.append("{%s, %s}" % (lstr(key), lstr(REFS[r]["name"])))
    extra = ""
    if node["class"] == "Model":
        wp = p.get("WorldPivotData", {}).get("OptionalCFrame")
        if wp:
            extra = ', Pivot = ' + cframe(wp)
    return "{Class = %s, Name = %s, Props = %s, Attributes = %s, Refs = {%s}%s, Children = {%s}}" % (
        lstr(node["class"]), lstr(node["name"]), props_list(node), attributes(node), ", ".join(refs), extra,
        ", ".join(kids))


REFS = {}


def index(n):
    REFS[n.get("ref")] = n
    for c in n.get("children", []):
        index(c)


def npc_entry(npc, orig_props, meta):
    name = npc["name"]
    outfit = next((c for c in npc["children"] if c["name"] == "Outfit"), None)
    parts = {c["name"] for c in npc["children"] if c["class"] == "Part"}
    lines = ["\t{Name = %s, Hide = {%s}," % (lstr(name), ", ".join(lstr(h) for h in meta["HIDE"].get(name, [])))]
    lines.append("\t\tTree = " + tree(npc) + ",")
    lines.append("\t\tOutfit = {")
    for m in (outfit or {}).get("children", []):
        h = next(c for c in m["children"] if c["name"] == "Handle")
        weld_to = None
        for k in h.get("children", []):
            if k["class"] == "WeldConstraint":
                for key in ("Part0", "Part1"):
                    r = k["props"][key].get("Ref")
                    if r in REFS and REFS[r]["name"] in parts:
                        weld_to = REFS[r]["name"]
        # what this copy changes compared with the library prop
        lib = orig_props.get(m["name"])
        hprops = {f: h["props"][f]["Bool"] for f in FLAGS if f in h["props"]}
        lib_h = next(c for c in lib["children"] if c["name"] == "Handle") if lib else None
        handle_over = {k: v for k, v in hprops.items() if lib_h is None or lib_h["props"][k]["Bool"] != v}
        mine = [c for c in m["children"] if visible(c)]
        theirs = [c for c in (lib or {}).get("children", []) if visible(c)]
        model_over = {}
        cm, ct = common([flags_of(c) for c in mine]), common([flags_of(c) for c in theirs])
        for k, v in cm.items():
            if ct.get(k) != v:
                model_over[k] = v
        colors = {}
        for c in mine:
            t = next((x for x in theirs if x["name"] == c["name"]), None)
            if t and t["props"]["Color"]["Color3uint8"] != c["props"]["Color"]["Color3uint8"]:
                colors[c["name"]] = c["props"]["Color"]["Color3uint8"]
        lines.append("\t\t\t{Prop = %s, Handle = %s, WeldTo = %s, HandleFlags = {%s}, Flags = {%s}, Colors = {%s}}," % (
            lstr(m["name"]), cframe(h["props"]["CFrame"]), lstr(weld_to) if weld_to else "nil",
            ", ".join("%s = %s" % (k, "true" if v else "false") for k, v in sorted(handle_over.items())),
            ", ".join("%s = %s" % (k, "true" if v else "false") for k, v in sorted(model_over.items())),
            ", ".join("[%s] = Color3.fromRGB(%d, %d, %d)" % (lstr(k), *v) for k, v in colors.items())))
    lines.append("\t\t},")
    lines.append("\t\tBody = {%s}," % ", ".join(
        "{Prop = %s, Limb = %s}" % (lstr(pid), lstr(limb)) for pid, limb in meta["BODY"].get(name, [])))
    lines.append("\t},")
    return lines


HEADER = '''--[[
FOLK VALLEY [RUN] - props and NPCs builder (generated by tools/gen_build.py)

1. In Studio: File > Import 3D > choose FolkValley_Props.fbx > Import.
   Default import settings are fine ("Merge Meshes" must stay off).
   The meshes come in plain grey: that's normal, step 2 colours them.
2. View > Command Bar: paste ALL of this file and press Enter.

It builds:
  * ServerStorage.Props (or "Props (new)" if there already is one): the %d props,
    every Model with the same name, Handle, attributes, hinges and helper parts as
    before, with the new MeshParts in place of the old parts (same part names)
  * Workspace.NPCs (or "NPCs (new)"): Pete and Wanda, standing where they stood,
    with the same rig, Humanoid, Talk prompts and attributes, wearing the new
    props and new clothes (a "Body" folder welded over their limbs)
The imported model is cleaned up afterwards. Ctrl+Z undoes the whole thing.
3. Move the new folders to wherever the old ones were, then delete the old ones.
]]

local MARKER_STEP = 4
local function E(enumType, value)
	for _, item in ipairs(enumType:GetEnumItems()) do
		if item.Value == value then
			return item
		end
	end
	error("no " .. tostring(enumType) .. " with value " .. tostring(value))
end
'''

BODY = r'''
local ChangeHistoryService = game:GetService("ChangeHistoryService")
local ServerStorage = game:GetService("ServerStorage")
local TAG = "FolkValley props: "

-- 1. find the imported meshes (the importer puts them in Workspace)
local meshes, loose = {}, {}
local function norm(s)
	return (string.lower(s):gsub("[^%w]", ""))
end
for _, root in ipairs({workspace, ServerStorage, game:GetService("ReplicatedStorage")}) do
	for _, d in ipairs(root:GetDescendants()) do
		if d:IsA("MeshPart") then
			if meshes[d.Name] == nil then
				meshes[d.Name] = d
			end
			if loose[norm(d.Name)] == nil then
				loose[norm(d.Name)] = d
			end
		end
	end
end
local function mesh(name)
	return meshes[name] or loose[norm(name)]
end

local wanted = {"FV_AxisO", "FV_AxisX", "FV_AxisY", "FV_AxisZ"}
for _, spec in ipairs(PROPS) do
	for _, p in ipairs(spec.Parts) do
		table.insert(wanted, p.Mesh)
	end
end
local missing = {}
for _, name in ipairs(wanted) do
	if mesh(name) == nil then
		table.insert(missing, name)
	end
end
if #missing > 0 then
	warn(TAG .. #missing .. " imported meshes not found (first: " .. missing[1]
		.. "). Import FolkValley_Props.fbx with File > Import 3D first, with Merge Meshes off.")
	return
end

-- 2. work out how the importer scaled / turned the file from the marker cubes
local o = mesh("FV_AxisO").Position
local ex = mesh("FV_AxisX").Position - o
local ey = mesh("FV_AxisY").Position - o
local ez = mesh("FV_AxisZ").Position - o
local scale = (ex.Magnitude + ey.Magnitude + ez.Magnitude) / (3 * MARKER_STEP)
if ex.Unit:Cross(ey.Unit):Dot(ez.Unit) < 0.9 then
	warn(TAG .. "the import looks mirrored. Re-import with the default axis settings.")
	return
end
local fromFile = CFrame.fromMatrix(Vector3.zero, ex.Unit, ey.Unit, ez.Unit):Inverse()

ChangeHistoryService:SetWaypoint("Before building FolkValley props")

local function make(spec)
	local inst = Instance.new(spec.Class)
	for _, kv in ipairs(spec.Props) do
		inst[kv[1]] = kv[2]
	end
	inst.Name = spec.Name
	return inst
end

local containers = {}
local function buildProp(spec)
	local model = Instance.new("Model")
	model.Name = spec.Id
	local subs = {}
	for k, m in ipairs(spec.Models) do
		local sm = Instance.new("Model")
		sm.Name = m.Name
		sm.Parent = model
		subs[k] = sm
	end
	local handle
	for _, ks in ipairs(spec.Keep) do
		local inst = make(ks)
		local parent = ks.Model and subs[ks.Model] or model
		inst.Parent = parent
		if ks.Primary then
			parent.PrimaryPart = inst
		end
		if ks.Name == "Handle" and not ks.Model then
			handle = inst
		end
	end
	for _, p in ipairs(spec.Parts) do
		local part = mesh(p.Mesh)
		containers[part.Parent] = true
		local turn = fromFile * (part.CFrame - part.CFrame.Position)
		for _, child in ipairs(part:GetChildren()) do
			child:Destroy() -- importer extras (SurfaceAppearance, attachments)
		end
		part.Name = p.Name
		part.Size = part.Size / scale / (spec.Scale or 1)
		part.CFrame = handle.CFrame * CFrame.new(p.Center) * turn
		part.Color = p.Color
		part.Material = p.Material
		part.Transparency = p.Transparency
		part.Reflectance = 0
		pcall(function() part.TextureID = "" end)
		pcall(function() part.CollisionFidelity = Enum.CollisionFidelity.Box end)
		for flag, v in pairs(p.Flags) do
			part[flag] = v
		end
		part.Parent = p.Model and subs[p.Model] or model
		if spec.Weld then
			local weld = Instance.new("WeldConstraint")
			weld.Part0 = handle
			weld.Part1 = part
			weld.Parent = part
		end
	end
	model.PrimaryPart = handle
	for k, v in pairs(spec.Attributes) do
		model:SetAttribute(k, v)
	end
	if spec.Scale then
		local ok = pcall(function() model:ScaleTo(spec.Scale) end)
		if not ok then -- older Studio: scale the parts about the Handle by hand
			local pivot = handle.CFrame
			for _, d in ipairs(model:GetDescendants()) do
				if d:IsA("BasePart") then
					local rel = pivot:ToObjectSpace(d.CFrame)
					d.Size = d.Size * spec.Scale
					d.CFrame = pivot * (rel - rel.Position + rel.Position * spec.Scale)
				end
			end
		end
	end
	return model
end

-- 3. the props (and the NPC clothes, which aren't props)
local folder = Instance.new("Folder")
folder.Name = ServerStorage:FindFirstChild("Props") and "Props (new)" or "Props"
local library = {}
for _, spec in ipairs(PROPS) do
	local model = buildProp(spec)
	library[spec.Id] = model
	if spec.Library then
		model.Parent = folder
	end
end
folder.Parent = ServerStorage

-- 4. the NPCs
local npcFolder = Instance.new("Folder")
npcFolder.Name = workspace:FindFirstChild("NPCs") and "NPCs (new)" or "NPCs"
local turnAround = CFrame.Angles(0, math.pi, 0)
for _, npc in ipairs(NPCS) do
	local made, names = {}, {}
	local function build(spec, parent)
		local inst = make(spec)
		for k, v in pairs(spec.Attributes) do
			inst:SetAttribute(k, v)
		end
		if inst:IsA("BasePart") then
			names[spec.Name] = inst
		end
		table.insert(made, {inst, spec})
		for _, c in ipairs(spec.Children) do
			build(c, inst)
		end
		inst.Parent = parent
		return inst
	end
	local model = build(npc.Tree, nil)
	for _, pair in ipairs(made) do
		for _, ref in ipairs(pair[2].Refs) do
			pair[1][ref[1]] = names[ref[2]]
		end
	end
	if npc.Tree.Pivot then
		model.WorldPivot = npc.Tree.Pivot
	end
	for _, limb in ipairs(npc.Hide) do
		names[limb].Transparency = 1
	end
	local body = Instance.new("Folder")
	body.Name = "Body"
	body.Parent = model
	for _, b in ipairs(npc.Body) do
		local m = library[b.Prop]:Clone()
		m:PivotTo(names[b.Limb].CFrame * turnAround)
		local weld = Instance.new("WeldConstraint")
		weld.Part0 = names[b.Limb]
		weld.Part1 = m.PrimaryPart
		weld.Parent = m.PrimaryPart
		m.Parent = body
	end
	local outfit = Instance.new("Folder")
	outfit.Name = "Outfit"
	outfit.Parent = model
	for _, item in ipairs(npc.Outfit) do
		local m = library[item.Prop]:Clone()
		m:PivotTo(item.Handle)
		for flag, v in pairs(item.HandleFlags) do
			m.PrimaryPart[flag] = v
		end
		for _, d in ipairs(m:GetDescendants()) do
			if d:IsA("BasePart") and d ~= m.PrimaryPart then
				for flag, v in pairs(item.Flags) do
					d[flag] = v
				end
				if item.Colors[d.Name] then
					d.Color = item.Colors[d.Name]
				end
			end
		end
		if item.WeldTo then
			local weld = Instance.new("WeldConstraint")
			weld.Part0 = names[item.WeldTo]
			weld.Part1 = m.PrimaryPart
			weld.Parent = m.PrimaryPart
		end
		m.Parent = outfit
	end
	model.Parent = npcFolder
end
npcFolder.Parent = workspace
for id, model in pairs(library) do
	if model.Parent == nil then
		model:Destroy()
	end
end

-- 5. tidy up: every marker cube (from every import of the file) and the now-empty imported model
for _, root in ipairs({workspace, ServerStorage, game:GetService("ReplicatedStorage")}) do
	for _, d in ipairs(root:GetDescendants()) do
		if d:IsA("BasePart") and d.Name:match("^FV_Axis[OXYZ]$") then
			containers[d.Parent] = true
			d:Destroy()
		end
	end
end
for container in pairs(containers) do
	local c = container
	while c and c ~= game and c ~= workspace and c.Parent and not c:IsA("Folder") do
		local hasParts = false
		for _, d in ipairs(c:GetDescendants()) do
			if d:IsA("BasePart") then
				hasParts = true
				break
			end
		end
		if hasParts then
			break
		end
		local parent = c.Parent
		c:Destroy()
		c = parent
	end
end

ChangeHistoryService:SetWaypoint("Built FolkValley props and NPCs")
game:GetService("Selection"):Set({folder, npcFolder})
print(("%sbuilt %d props in ServerStorage.%s and %d NPCs in Workspace.%s"):format(
	TAG, #folder:GetChildren(), folder.Name, #NPCS, npcFolder.Name))
'''


def main(orig_props_path, orig_npc_path, props_path, meta_path, out):
    orig_props = {m["name"]: m for m in json.load(open(orig_props_path))[0]["children"] if m["class"] == "Model"}
    npc_root = json.load(open(orig_npc_path))[0]
    index(npc_root)
    new = json.load(open(props_path))
    meta = json.load(open(meta_path))
    body_ids = {pid for lst in meta["BODY"].values() for pid, _ in lst}
    lines = [HEADER % sum(1 for p in new if p["Id"] not in body_ids), "local PROPS = {"]
    for p in new:
        lines += prop_entry(orig_props.get(p["Id"]), p, library=p["Id"] not in body_ids)
    lines.append("}")
    lines.append("local NPCS = {")
    for npc in npc_root["children"]:
        if npc["class"] == "Model":
            lines += npc_entry(npc, orig_props, meta)
    lines.append("}")
    with open(out, "w") as f:
        f.write("\n".join(lines) + "\n" + BODY)
    print("wrote", out, len(new), "models")


if __name__ == "__main__":
    main(*sys.argv[1:6])
