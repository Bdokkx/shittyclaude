"""Dry-run out/BuildPropsAndNPCs.lua outside Roblox: a small mock of the Studio
API stands in for an imported FBX, runs the script, then checks the Props folder
and the NPCs against the original files and the new meshes.

    python tools/mock_studio.py out/BuildPropsAndNPCs.lua <props.json> <orig_props.json> <orig_npc.json>
                                [--scale=0.01] [--turn]

--scale fakes an importer that scales the file and --turn one that turns it 90
degrees, to check that the marker cubes undo both.
"""
import json
import math
import sys

from lupa import LuaRuntime

MOCK = r'''
local function vec(x, y, z) return setmetatable({X = x, Y = y, Z = z}, V) end
V = {}
V.__index = function(v, k)
    if k == "Magnitude" then return math.sqrt(v.X * v.X + v.Y * v.Y + v.Z * v.Z) end
    if k == "Unit" then local m = math.sqrt(v.X * v.X + v.Y * v.Y + v.Z * v.Z); return vec(v.X / m, v.Y / m, v.Z / m) end
    if k == "Cross" then return function(a, b) return vec(a.Y * b.Z - a.Z * b.Y, a.Z * b.X - a.X * b.Z, a.X * b.Y - a.Y * b.X) end end
    if k == "Dot" then return function(a, b) return a.X * b.X + a.Y * b.Y + a.Z * b.Z end end
end
V.__add = function(a, b) return vec(a.X + b.X, a.Y + b.Y, a.Z + b.Z) end
V.__sub = function(a, b) return vec(a.X - b.X, a.Y - b.Y, a.Z - b.Z) end
V.__div = function(a, s) return vec(a.X / s, a.Y / s, a.Z / s) end
V.__mul = function(a, s) if type(a) == "number" then a, s = s, a end return vec(a.X * s, a.Y * s, a.Z * s) end
V.__tostring = function(v) return string.format("(%.3f, %.3f, %.3f)", v.X, v.Y, v.Z) end
Vector3 = {new = vec, zero = vec(0, 0, 0)}
Vector2 = {new = function(x, y) return {X = x, Y = y} end}

C = {}
local function cf(p, r) return setmetatable({p = p, r = r}, C) end
local I3 = {{1, 0, 0}, {0, 1, 0}, {0, 0, 1}}
local function rotv(r, v) return vec(r[1][1] * v.X + r[1][2] * v.Y + r[1][3] * v.Z,
                                     r[2][1] * v.X + r[2][2] * v.Y + r[2][3] * v.Z,
                                     r[3][1] * v.X + r[3][2] * v.Y + r[3][3] * v.Z) end
local function matmul(a, b)
    local m = {{0, 0, 0}, {0, 0, 0}, {0, 0, 0}}
    for i = 1, 3 do for j = 1, 3 do for k = 1, 3 do m[i][j] = m[i][j] + a[i][k] * b[k][j] end end end
    return m
end
local function transpose(a) return {{a[1][1], a[2][1], a[3][1]}, {a[1][2], a[2][2], a[3][2]}, {a[1][3], a[2][3], a[3][3]}} end
local function inverse(s) local t = transpose(s.r); local q = rotv(t, s.p); return cf(vec(-q.X, -q.Y, -q.Z), t) end
C.__index = function(c, k)
    if k == "Position" then return c.p end
    if k == "LookVector" then return vec(-c.r[1][3], -c.r[2][3], -c.r[3][3]) end
    if k == "Inverse" then return inverse end
    if k == "ToObjectSpace" then return function(s, o) return inverse(s) * o end end
end
C.__mul = function(a, b)
    if getmetatable(b) == V then return rotv(a.r, b) + a.p end
    return cf(rotv(a.r, b.p) + a.p, matmul(a.r, b.r))
end
C.__sub = function(a, v) return cf(a.p - v, a.r) end
C.__add = function(a, v) return cf(a.p + v, a.r) end
CFrame = {
    new = function(x, y, z, ...)
        if type(x) == "table" then return cf(x, I3) end
        local r = {...}
        if #r == 9 then return cf(vec(x, y, z), {{r[1], r[2], r[3]}, {r[4], r[5], r[6]}, {r[7], r[8], r[9]}}) end
        return cf(vec(x or 0, y or 0, z or 0), I3)
    end,
    fromMatrix = function(p, x, y, z) return cf(p, {{x.X, y.X, z.X}, {x.Y, y.Y, z.Y}, {x.Z, y.Z, z.Z}}) end,
    Angles = function(rx, ry, rz)
        assert(rx == 0 and rz == 0)
        local c, s = math.cos(ry), math.sin(ry)
        return cf(vec(0, 0, 0), {{c, 0, s}, {0, 1, 0}, {-s, 0, c}})
    end,
}

Color3 = {fromRGB = function(r, g, b) return {r, g, b} end, new = function(r, g, b) return {r * 255, g * 255, b * 255} end}

-- enums: any member asked for by name or found by value
local function enumType(name)
    local t = {_name = name, _items = {}}
    for v = 0, 2000 do t._items[#t._items + 1] = {Name = name .. "#" .. v, Value = v, EnumType = name} end
    function t.GetEnumItems(self) return self._items end
    return setmetatable(t, {__index = function(self, k)
        if k == "GetEnumItems" then return t.GetEnumItems end
        return {Name = k, EnumType = name} end, __tostring = function() return "Enum." .. name end})
end
Enum = setmetatable({}, {__index = function(self, k) local e = enumType(k); rawset(self, k, e); return e end})

-- Instances
local Inst = {}
local allowed = {Model = true, Part = true, WedgePart = true, MeshPart = true, Folder = true, WeldConstraint = true,
                 Attachment = true, Humanoid = true, Animator = true, Motor6D = true, ProximityPrompt = true,
                 SpecialMesh = true, Decal = true}
local function new(class, props)
    if not allowed[class] then error("Instance.new: unexpected class " .. class) end
    local o = {ClassName = class, _children = {}, _attrs = {}, Name = class}
    if class == "Part" or class == "MeshPart" or class == "WedgePart" then
        o.Anchored = false; o.CanCollide = true; o.CanTouch = true; o.CanQuery = true; o.Massless = false
        o.Transparency = 0; o.CastShadow = true; o.Size = vec(4, 1, 2); o.CFrame = cf(vec(0, 0, 0), I3)
    end
    if class == "Model" then o.Scale = 1 end
    for k, v in pairs(props or {}) do o[k] = v end
    return setmetatable(o, Inst)
end
Inst.__index = function(o, k)
    local m = rawget(Inst, k)
    if m then return m end
    if k == "Parent" then return rawget(o, "_parent") end
    if k == "Position" then return rawget(o, "CFrame").p end
    return nil
end
Inst.__newindex = function(o, k, v)
    if k == "Parent" then
        if rawget(o, "_destroyed") then error("set Parent of a destroyed " .. o.Name) end
        local old = rawget(o, "_parent")
        if old then for i, c in ipairs(old._children) do if c == o then table.remove(old._children, i) break end end end
        rawset(o, "_parent", v)
        if v then table.insert(v._children, o) end
        return
    end
    rawset(o, k, v)
end
local function isPart(o) return o.ClassName == "Part" or o.ClassName == "MeshPart" or o.ClassName == "WedgePart" end
function Inst.IsA(o, c)
    if c == "BasePart" then return isPart(o) end
    return o.ClassName == c
end
function Inst.GetChildren(o) local t = {} for i, c in ipairs(o._children) do t[i] = c end return t end
function Inst.GetDescendants(o)
    local t = {}
    local function walk(x) for _, c in ipairs(x._children) do table.insert(t, c) walk(c) end end
    walk(o)
    return t
end
function Inst.FindFirstChild(o, n) for _, c in ipairs(o._children) do if c.Name == n then return c end end end
function Inst.Destroy(o) o.Parent = nil; rawset(o, "_destroyed", true); for _, c in ipairs(Inst.GetChildren(o)) do Inst.Destroy(c) end end
function Inst.SetAttribute(o, k, v) o._attrs[k] = v end
function Inst.GetAttribute(o, k) return o._attrs[k] end
function Inst.GetPivot(o)
    if o.PrimaryPart then return o.PrimaryPart.CFrame end
    if o.WorldPivot then return o.WorldPivot end
    error("GetPivot: no PrimaryPart / WorldPivot on " .. o.Name)
end
function Inst.PivotTo(o, target)
    local delta = target * inverse(Inst.GetPivot(o))
    for _, d in ipairs(Inst.GetDescendants(o)) do if isPart(d) then d.CFrame = delta * d.CFrame end end
end
function Inst.ScaleTo(o, s)
    local pivot = Inst.GetPivot(o)
    local k = s / o.Scale
    for _, d in ipairs(Inst.GetDescendants(o)) do
        if isPart(d) then
            local rel = inverse(pivot) * d.CFrame
            d.Size = d.Size * k
            d.CFrame = pivot * cf(rel.p * k, rel.r)
        end
    end
    o.Scale = s
end
local REFKEYS = {Part0 = true, Part1 = true, PrimaryPart = true}
function Inst.Clone(o)
    local map = {}
    local function copy(x)
        local c = setmetatable({_children = {}, _attrs = {}}, Inst)
        for k, v in pairs(x) do
            if k ~= "_children" and k ~= "_attrs" and k ~= "_parent" then rawset(c, k, v) end
        end
        for k, v in pairs(x._attrs) do c._attrs[k] = v end
        map[x] = c
        for _, ch in ipairs(x._children) do local cc = copy(ch); rawset(cc, "_parent", c); table.insert(c._children, cc) end
        return c
    end
    local root = copy(o)
    for orig, c in pairs(map) do
        for k in pairs(REFKEYS) do
            local v = rawget(orig, k)
            if v ~= nil then
                if map[v] then rawset(c, k, map[v]) elseif o:IsAncestorOf(v) then error("clone ref") else rawset(c, k, v) end
            end
        end
    end
    return root
end
function Inst.IsAncestorOf(o, x)
    local p = x and rawget(x, "_parent")
    while p do if p == o then return true end p = rawget(p, "_parent") end
    return false
end
Instance = {new = new}

game = new("Folder", {Name = "game"})
workspace = new("Folder", {Name = "Workspace"})
local services = {ServerStorage = new("Folder", {Name = "ServerStorage"}),
                  ReplicatedStorage = new("Folder", {Name = "ReplicatedStorage"}),
                  ChangeHistoryService = {SetWaypoint = function() end},
                  Selection = {Set = function() end}}
function game.GetService(_, n) return services[n] end
WARNINGS = {}
function warn(...) local t = {...} table.insert(WARNINGS, table.concat(t, " ")) end
'''


def m4(cf):
    c = cf["CFrame"] if "CFrame" in cf else cf
    return c["position"], c["orientation"]


def main(lua_path, props_path, orig_props_path, orig_npc_path, scale=1.0, turn=False):
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute(MOCK)
    new = json.load(open(props_path))
    orig = {m["name"]: m for m in json.load(open(orig_props_path))[0]["children"]}
    npcs = {m["name"]: m for m in json.load(open(orig_npc_path))[0]["children"]}
    imp = lua.eval('function() local m = Instance.new("Model"); m.Name = "FolkValley_Props"; m.Parent = workspace; return m end')()
    mk = lua.eval('''function(parent, name, x, y, z, sx, sy, sz, turn)
        local p = Instance.new("MeshPart"); p.Name = name
        local r = turn and {{0, 0, 1}, {0, 1, 0}, {-1, 0, 0}} or {{1, 0, 0}, {0, 1, 0}, {0, 0, 1}}
        local c = CFrame.new(x, y, z); c = setmetatable({p = c.p, r = r}, getmetatable(c))
        p.CFrame = c; p.Size = Vector3.new(sx, sy, sz); p.Parent = parent
        local child = Instance.new("Attachment"); child.Parent = p
        return p end''')

    def place(x, y, z):
        if turn:
            x, z = z, -x
        return x * scale + 100, y * scale + 5, z * scale - 40

    for i, w in enumerate(new):
        for p in w["Parts"]:
            cx, cy, cz = p["Center"]
            sx, sy, sz = p["Size"]
            x, y, z = place(cx + 30 * i, cy, cz)
            mk(imp, p["Mesh"], x, y, z, sx * scale, sy * scale, sz * scale, turn)
    for name, (dx, dy, dz) in (("FV_AxisO", (0, 0, 0)), ("FV_AxisX", (4, 0, 0)), ("FV_AxisY", (0, 4, 0)),
                               ("FV_AxisZ", (0, 0, 4))):
        x, y, z = place(-12 + dx, dy, dz)
        mk(imp, name, x, y, z, 0.25 * scale, 0.25 * scale, 0.25 * scale, turn)

    lua.execute(open(lua_path).read())
    problems = list(lua.eval("WARNINGS").values())
    ss = lua.eval('game:GetService("ServerStorage")')
    ws = lua.eval("workspace")
    same = lua.eval("function(a, b) return rawequal(a, b) end")
    relcf = lua.eval("function(a, b) return a:Inverse() * b end")
    kids = lambda x: list(x.GetChildren(x).values())
    desc = lambda x: list(x.GetDescendants(x).values())
    folder = ss.FindFirstChild(ss, "Props")
    if folder is None:
        print("no Props folder;", problems)
        return 1
    by_id = {w["Id"]: w for w in new}
    models = {m.Name: m for m in kids(folder)}
    lib_ids = [n for n in orig]
    if sorted(models) != sorted(lib_ids):
        problems.append("Props folder: %s" % sorted(set(models) ^ set(lib_ids)))
    nparts = 0
    for name, m in models.items():
        o, w = orig[name], by_id[name]
        handle = m.PrimaryPart
        oh = next(c for c in o["children"] if c["name"] == "Handle")
        if handle is None or handle.Name != "Handle":
            problems.append(name + ": PrimaryPart")
            continue
        (hp, hr) = m4(oh["props"]["CFrame"])
        if math.dist((handle.CFrame.p.X, handle.CFrame.p.Y, handle.CFrame.p.Z), hp) > 1e-4:
            problems.append(name + ": Handle moved")
        hs = oh["props"]["Size"]["Vector3"]
        if math.dist((handle.Size.X, handle.Size.Y, handle.Size.Z), hs) > 1e-4:
            problems.append(name + ": Handle size %s" % handle.Size)
        a = o["props"].get("Attributes", {}).get("Attributes", {})
        for k in a:
            if m.GetAttribute(m, k) is None:
                problems.append(name + ": attribute " + k)
        sc = o["props"].get("Scale", {}).get("Float32", 1.0)
        if abs((m.Scale or 1) - sc) > 1e-4:
            problems.append(name + ": Scale %s, was %s" % (m.Scale, sc))
        # every invisible original part is still there, at the same spot
        for c in o["children"] + [g for k in o["children"] if k["class"] == "Model" for g in k["children"]]:
            if c.get("props", {}).get("Transparency", {}).get("Float32", 0) >= 0.99 or c["name"] == "Void":
                found = [d for d in desc(m) if d.Name == c["name"] and
                         math.dist((d.CFrame.p.X, d.CFrame.p.Y, d.CFrame.p.Z), m4(c["props"]["CFrame"])[0]) < 1e-3]
                if not found:
                    problems.append("%s: lost %s" % (name, c["name"]))
        subs = [k for k in kids(m) if k.ClassName == "Model"]
        osubs = [k for k in o["children"] if k["class"] == "Model"]
        if len(subs) != len(osubs):
            problems.append(name + ": %d sub-models" % len(subs))
        for s in subs:
            if s.PrimaryPart is None:
                problems.append(name + ": sub-model without PrimaryPart")
        meshparts = [d for d in desc(m) if d.ClassName == "MeshPart"]
        if len(meshparts) != len(w["Parts"]):
            problems.append(name + ": %d mesh parts, %d expected" % (len(meshparts), len(w["Parts"])))
        welded = any(k["class"] == "WeldConstraint" for c in o["children"] if c["name"] != "Handle"
                     for k in c.get("children", []))
        for k, p in zip(sorted(meshparts, key=lambda x: x.Name), sorted(w["Parts"], key=lambda q: q["Name"])):
            nparts += 1
            welds = [c for c in kids(k) if c.ClassName == "WeldConstraint"]
            if welded and (len(welds) != 1 or not same(welds[0].Part0, handle) or not same(welds[0].Part1, k)):
                problems.append(name + "." + k.Name + ": weld")
            if not welded and welds:
                problems.append(name + "." + k.Name + ": unexpected weld")
        for p in w["Parts"]:
            cands = [k for k in meshparts if k.Name == p["Name"]]
            ok = False
            for k in cands:
                r = relcf(handle.CFrame, k.CFrame)
                if math.dist((r.p.X, r.p.Y, r.p.Z), p["Center"]) < 1e-3 and \
                        math.dist((k.Size.X, k.Size.Y, k.Size.Z), p["Size"]) < 1e-3:
                    ok = True
            if not ok:
                problems.append("%s.%s: not where the mesh data puts it" % (name, p["Name"]))
    # NPCs
    nf = ws.FindFirstChild(ws, "NPCs")
    if nf is None:
        problems.append("no NPCs folder in Workspace")
    else:
        for npc in kids(nf):
            o = npcs[npc.Name]
            hum = npc.FindFirstChild(npc, "Humanoid")
            if hum is None or hum.FindFirstChild(hum, "Animator") is None:
                problems.append(npc.Name + ": Humanoid / Animator")
            pp = o["props"].get("PrimaryPart", {}).get("Ref")
            want = next((c["name"] for c in o["children"] if c.get("ref") == pp), None)
            if want and (npc.PrimaryPart is None or npc.PrimaryPart.Name != want):
                problems.append(npc.Name + ": PrimaryPart should be " + want)
            if npc.GetAttribute(npc, "Npc") != npc.Name:
                problems.append(npc.Name + ": Npc attribute %r" % npc.GetAttribute(npc, "Npc"))
            motors = [d for d in desc(npc) if d.ClassName == "Motor6D"]
            if len(motors) != 6 or any(mm.Part0 is None or mm.Part1 is None for mm in motors):
                problems.append(npc.Name + ": motors")
            prompt = [d for d in desc(npc) if d.ClassName == "ProximityPrompt"]
            if len(prompt) != 1 or prompt[0].ActionText != "Talk":
                problems.append(npc.Name + ": Talk prompt")
            limbs = {c["name"]: c for c in o["children"] if c["class"] == "Part"}
            for lname, c in limbs.items():
                part = npc.FindFirstChild(npc, lname)
                if part is None or math.dist((part.CFrame.p.X, part.CFrame.p.Y, part.CFrame.p.Z),
                                             m4(c["props"]["CFrame"])[0]) > 1e-4:
                    problems.append(npc.Name + ": limb " + lname)
            outfit = npc.FindFirstChild(npc, "Outfit")
            ooutfit = next(c for c in o["children"] if c["name"] == "Outfit")
            if outfit is None or len(kids(outfit)) != len(ooutfit["children"]):
                problems.append(npc.Name + ": outfit count")
            else:
                for item, oi in zip(kids(outfit), ooutfit["children"]):
                    h = item.PrimaryPart
                    oh = next(c for c in oi["children"] if c["name"] == "Handle")
                    if item.Name != oi["name"] or math.dist((h.CFrame.p.X, h.CFrame.p.Y, h.CFrame.p.Z),
                                                            m4(oh["props"]["CFrame"])[0]) > 1e-4:
                        problems.append("%s: outfit %s misplaced" % (npc.Name, item.Name))
                    ow = [k for k in oh.get("children", []) if k["class"] == "WeldConstraint"]
                    hw = [k for k in kids(h) if k.ClassName == "WeldConstraint"]
                    if len(ow) != len(hw):
                        problems.append("%s: outfit %s welds" % (npc.Name, item.Name))
            body = npc.FindFirstChild(npc, "Body")
            if body is None or not kids(body):
                problems.append(npc.Name + ": no Body")
            else:
                for piece in kids(body):
                    h = piece.PrimaryPart
                    w = [k for k in kids(h) if k.ClassName == "WeldConstraint"]
                    if len(w) != 1 or w[0].Part0 is None or not same(w[0].Part0.Parent, npc):
                        problems.append("%s: body %s not welded to a limb" % (npc.Name, piece.Name))
    stray = [d for d in kids(ws) if d.Name != "NPCs"]
    if stray:
        problems.append("left in Workspace: %s" % [d.Name for d in stray][:5])
    print("%d props (%d mesh parts) and %d NPCs checked; %d problems" % (
        len(models), nparts, len(kids(nf)) if nf else 0, len(problems)))
    for p in problems[:30]:
        print("  ", p)
    return 1 if problems else 0


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    o = dict(x[2:].split("=", 1) if "=" in x else (x[2:], "1") for x in sys.argv[1:] if x.startswith("--"))
    sys.exit(main(a[0], a[1], a[2], a[3], float(o.get("scale", 1.0)), "turn" in o))
