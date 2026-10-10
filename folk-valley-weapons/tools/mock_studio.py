"""Dry-run out/BuildWeapons.lua outside Roblox: a small mock of the Studio API
(Instances, Vector3, CFrame, services) stands in for an imported FBX, then the
resulting Weapons folder is checked against the build contract.

    python tools/mock_studio.py out/BuildWeapons.lua out/weapons.json [--scale=0.01] [--turn]

--scale fakes an importer that scales the file (FBX cm -> studs, say) and --turn one
that turns it, to check that the marker cubes undo both.
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
V.__mul = function(a, s) return vec(a.X * s, a.Y * s, a.Z * s) end
V.__tostring = function(v) return string.format("(%.3f, %.3f, %.3f)", v.X, v.Y, v.Z) end
Vector3 = {new = vec, zero = vec(0, 0, 0)}

-- CFrame: rotation columns r (3x3, r[i][j] = row i col j) and position p
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
C.__index = function(c, k)
    if k == "Position" then return c.p end
    if k == "LookVector" then return vec(-c.r[1][3], -c.r[2][3], -c.r[3][3]) end
    if k == "Inverse" then return function(s) local t = transpose(s.r); local q = rotv(t, s.p); return cf(vec(-q.X, -q.Y, -q.Z), t) end end
end
C.__mul = function(a, b)
    if getmetatable(b) == V then return rotv(a.r, b) + a.p end
    return cf(rotv(a.r, b.p) + a.p, matmul(a.r, b.r))
end
C.__sub = function(a, v) return cf(a.p - v, a.r) end
CFrame = {
    new = function(x, y, z) return cf(vec(x or 0, y or 0, z or 0), I3) end,
    fromMatrix = function(p, x, y, z) return cf(p, {{x.X, y.X, z.X}, {x.Y, y.Y, z.Y}, {x.Z, y.Z, z.Z}}) end,
}

Color3 = {fromRGB = function(r, g, b) return {r, g, b} end}
local materials = {}
for _, n in ipairs({"SmoothPlastic", "Metal", "Neon", "Glass", "Wood", "Fabric", "Plastic"}) do materials[n] = "Enum.Material." .. n end
Enum = {Material = setmetatable({}, {__index = function(_, k)
            if materials[k] == nil then error("Enum.Material has no member " .. tostring(k)) end
            return materials[k] end}),
        SurfaceType = {Smooth = "Smooth"}, CollisionFidelity = {Box = "Box"}}

-- Instances
local Inst = {}
local allowed = {Model = true, Part = true, MeshPart = true, Folder = true, WeldConstraint = true, Attachment = true}
local function new(class, props)
    if not allowed[class] then error("Instance.new: unexpected class " .. class) end
    local o = {ClassName = class, _children = {}, _attrs = {}, Name = class}
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
        local old = rawget(o, "_parent")
        if old then for i, c in ipairs(old._children) do if c == o then table.remove(old._children, i) break end end end
        rawset(o, "_parent", v)
        if v then table.insert(v._children, o) end
        return
    end
    if k == "PrimaryPart" or k == "WorldPivot" then rawset(o, k, v) return end
    rawset(o, k, v)
end
function Inst.IsA(o, c)
    if c == "BasePart" then return o.ClassName == "Part" or o.ClassName == "MeshPart" end
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
function Inst.Destroy(o) o.Parent = nil; rawset(o, "_destroyed", true) end
function Inst.SetAttribute(o, k, v) o._attrs[k] = v end
function Inst.GetAttribute(o, k) return o._attrs[k] end
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


def main(lua_path, json_path, scale=1.0, turn=False):
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute(MOCK)
    weapons = json.load(open(json_path))
    # the "imported model": every mesh where the FBX put it (weapon i at X = 3i, markers from X = -6),
    # optionally scaled and turned 90 degrees about Y like an importer might
    imp = lua.eval('function() local m = Instance.new("Model"); m.Name = "FolkValley_Weapons"; m.Parent = workspace; return m end')()
    mk = lua.eval('''function(parent, name, x, y, z, sx, sy, sz, turn)
        local p = Instance.new("MeshPart"); p.Name = name
        local r = turn and {{0, 0, 1}, {0, 1, 0}, {-1, 0, 0}} or {{1, 0, 0}, {0, 1, 0}, {0, 0, 1}}
        local c = CFrame.new(x, y, z); c = setmetatable({p = c.p, r = r}, getmetatable(c))
        p.CFrame = c; p.Size = Vector3.new(sx, sy, sz); p.Parent = parent
        local child = Instance.new("Attachment"); child.Parent = p
        return p end''')

    def place(x, y, z):
        if turn:              # rotate the whole file 90 degrees about Y: (x, z) -> (z, -x)
            x, z = z, -x
        return x * scale + 100, y * scale + 5, z * scale - 40

    for i, w in enumerate(weapons):
        for p in w["Parts"]:
            cx, cy, cz = p["Center"]
            sx, sy, sz = p["Size"]
            x, y, z = place(cx + 3 * i, cy, cz)
            mk(imp, p["Mesh"], x, y, z, sx * scale, sy * scale, sz * scale, turn)
    for name, (dx, dy, dz) in (("FV_AxisO", (0, 0, 0)), ("FV_AxisX", (4, 0, 0)), ("FV_AxisY", (0, 4, 0)),
                               ("FV_AxisZ", (0, 0, 4))):
        x, y, z = place(-6 + dx, dy, dz)
        mk(imp, name, x, y, z, 0.25 * scale, 0.25 * scale, 0.25 * scale, turn)

    lua.execute(open(lua_path).read())
    warns = list(lua.eval("WARNINGS").values())
    ss = lua.eval('game:GetService("ServerStorage")')
    folder = ss.FindFirstChild(ss, "Weapons")
    problems = list(warns)
    if folder is None:
        print("no Weapons folder built;", warns)
        return 1
    models = list(folder.GetChildren(folder).values())
    if len(models) != len(weapons):
        problems.append("%d models built, %d expected" % (len(models), len(weapons)))
    by_id = {w["Id"]: w for w in weapons}
    same = lua.eval("function(a, b) return rawequal(a, b) end")
    for m in models:
        w = by_id[m.Name]
        kids = list(m.GetChildren(m).values())
        handle = m.PrimaryPart
        if handle is None or handle.Name != "Handle" or handle.ClassName != "Part":
            problems.append(m.Name + ": PrimaryPart is not the Handle Part")
            continue
        hs = handle.Size
        if (hs.X, hs.Y, hs.Z) != (0.4, 0.4, 0.4) or handle.Transparency != 1:
            problems.append(m.Name + ": Handle size / transparency")
        if abs(m.GetAttribute(m, "Top") - round(w["Top"], 2)) > 1e-6 or abs(m.GetAttribute(m, "Bottom") - round(w["Bottom"], 2)) > 1e-6:
            problems.append(m.Name + ": Top/Bottom attributes")
        fx = [c for c in handle.GetChildren(handle).values() if c.Name == "Fx"]
        if bool(fx) != bool(w["Fx"]):
            problems.append(m.Name + ": Fx attachment")
        meshparts = [k for k in kids if k.ClassName == "MeshPart"]
        if len(meshparts) != len(w["Parts"]) or len(kids) != len(w["Parts"]) + 1:
            problems.append(m.Name + ": %d children" % len(kids))
        for k in meshparts:
            p = next(q for q in w["Parts"] if q["Name"] == k.Name)
            welds = [c for c in k.GetChildren(k).values() if c.ClassName == "WeldConstraint"]
            if len(welds) != 1 or not same(welds[0].Part0, handle) or not same(welds[0].Part1, k):
                problems.append(m.Name + "." + k.Name + ": weld")
            for flag, want in (("Anchored", False), ("CanCollide", False), ("CanTouch", False), ("CanQuery", False),
                               ("Massless", True)):
                if getattr(k, flag) is not want:
                    problems.append(m.Name + "." + k.Name + ": " + flag)
            # position relative to the handle and size, back in studs
            rel = (k.CFrame.p.X - handle.CFrame.p.X, k.CFrame.p.Y - handle.CFrame.p.Y, k.CFrame.p.Z - handle.CFrame.p.Z)
            err_c = math.dist(rel, p["Center"])
            sz = k.Size
            err_s = math.dist((sz.X, sz.Y, sz.Z), p["Size"])
            r = k.CFrame.r
            if any(abs(r[i][j] - (1 if i == j else 0)) > 1e-6 for i in range(1, 4) for j in range(1, 4)):
                problems.append("%s.%s: still turned" % (m.Name, k.Name))
            if err_c > 1e-3 or err_s > 1e-3:
                problems.append("%s.%s: off by %.4f / size %.4f" % (m.Name, k.Name, err_c, err_s))
    left = [d.Name for d in lua.eval("workspace").GetDescendants(lua.eval("workspace")).values()]
    if left:
        problems.append("left in Workspace: %s" % left[:5])
    print("%d models, %d meshparts checked; %d problems" % (len(models), sum(len(w["Parts"]) for w in weapons),
                                                          len(problems)))
    for p in problems[:20]:
        print("  ", p)
    return 1 if problems else 0


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    o = dict(x[2:].split("=", 1) if "=" in x else (x[2:], "1") for x in sys.argv[1:] if x.startswith("--"))
    sys.exit(main(a[0], a[1], float(o.get("scale", 1.0)), "turn" in o))
