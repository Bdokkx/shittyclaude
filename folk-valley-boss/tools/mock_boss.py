"""Dry-run the Grim Reaper outside Roblox (tools/mock_roblox.lua stands in for the engine):

1. build: fake an FBX import (optionally scaled / turned by the importer), run
   BuildGrimReaper.lua and check the model: parts, colours, bones, welds,
   Motor6Ds, attachments, effects, attributes, the controller script, where it
   stands;
2. rig: pose the built Motor6Ds with frames of every animation and check every
   bone lands where the animation tools put it (so C0 / C1 match the poses);
3. fight: run the ReaperController in simulated time against a player: it must
   notice them and roar, close in, use each attack, land hits where the player
   stands and miss when the player jumps clear, flinch, enrage at half health
   and play its defeat, then fade away.

    python tools/mock_boss.py <BuildGrimReaper.lua> <rig.json> <anims.json> [--scale=0.01] [--turn]
"""
import json
import math
import os
import sys

import numpy as np
from lupa import LuaRuntime

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import banim as B  # noqa: E402
from check_anims import read_clips  # noqa: E402


class Problems(list):
    def add(self, msg):
        self.append(msg)


def main(build_path, rig_path, anims_path, scale=1.0, turn=False):
    probs = Problems()
    rig = json.load(open(rig_path))
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute(open(os.path.join(HERE, "mock_roblox.lua")).read())
    G = lua.globals()

    # ---------------------------------------------------------------- 1. build
    imp = lua.eval('function() local m = Instance.new("Model"); m.Name = "FolkValley_GrimReaper"; m.Parent = workspace; '
                   'return m end')()
    mk = lua.eval('''function(parent, name, x, y, z, sx, sy, sz, turn)
        local p = Instance.new("MeshPart"); p.Name = name
        local c = CFrame.new(x, y, z)
        if turn then c = c * CFrame.Angles(0, math.rad(90), 0) end
        p.CFrame = c; p.Size = Vector3.new(sx, sy, sz); p.Parent = parent
        local extra = Instance.new("Attachment"); extra.Parent = p
        return p end''')

    def place(x, y, z):
        if turn:
            x, z = z, -x
        return x * scale + 100, y * scale + 5, z * scale - 40

    for p in rig["Parts"]:
        cx, cy, cz = p["Center"]
        sx, sy, sz = p["Size"]          # a turning importer turns each mesh's CFrame; its own size stays
        mk(imp, p["Mesh"], *place(cx, cy, cz), sx * scale, sy * scale, sz * scale, turn)
    for name, (dx, dy, dz) in (("FV_AxisO", (0, 0, 0)), ("FV_AxisX", (4, 0, 0)), ("FV_AxisY", (0, 4, 0)),
                               ("FV_AxisZ", (0, 0, 4))):
        mk(imp, name, *place(-12 + dx, dy, dz), 0.25 * scale, 0.25 * scale, 0.25 * scale, turn)

    try:
        lua.execute(open(build_path).read())
    except Exception as e:  # noqa: BLE001
        print("build script error:", e)
        return 1
    for w in G.WARNINGS.values():
        probs.add("build warning: " + w)
    ws = G.workspace
    model = ws.FindFirstChild(ws, "GrimReaper")
    if model is None:
        print("no GrimReaper in Workspace", list(G.WARNINGS.values()))
        return 1
    kids = lambda x: list(x.GetChildren(x).values())  # noqa: E731
    desc = lambda x: list(x.GetDescendants(x).values())  # noqa: E731
    left = [k.Name for k in kids(ws) if k.Name != "GrimReaper"]
    if left:
        probs.add("left in Workspace after the build: %s" % left)
    by_name = {}
    for d in desc(model):
        by_name.setdefault(d.Name, []).append(d)
    hrp = model.PrimaryPart
    if hrp is None or hrp.Name != "HumanoidRootPart":
        probs.add("PrimaryPart is not the HumanoidRootPart")
    hum = model.FindFirstChild(model, "Humanoid")
    if hum is None or hum.FindFirstChildOfClass(hum, "Animator") is None:
        probs.add("no Humanoid / Animator")
    meshparts = [d for d in desc(model) if d.ClassName == "MeshPart"]
    if len(meshparts) != len(rig["Parts"]):
        probs.add("%d mesh parts, %d expected" % (len(meshparts), len(rig["Parts"])))
    relpos = lua.eval("function(a, b) return (a:Inverse() * b).Position end")
    rows = lua.eval("cframe_rows")
    root_cf = hrp.CFrame
    hrp_rest = np.array(rig["HRP"]["Center"])
    for p in rig["Parts"]:
        part = (by_name.get(p["Name"]) or [None])[0]
        if part is None:
            probs.add("missing part " + p["Name"])
            continue
        r = relpos(root_cf, part.CFrame)
        if math.dist((r.X, r.Y, r.Z), np.array(p["Center"]) - hrp_rest) > 2e-3:
            probs.add("%s is not where the mesh data puts it" % p["Name"])
        rr = np.abs(np.array(rows(part.CFrame)[3:]).reshape(3, 3))
        ext = rr @ np.array([part.Size.X, part.Size.Y, part.Size.Z])
        if math.dist(ext, p["Size"]) > 2e-3:
            probs.add("%s size %s, not %s" % (p["Name"], part.Size, p["Size"]))
        rgb = list(part.Color._rgb.values())
        if [round(v) for v in rgb] != list(p["Color"]):
            probs.add("%s colour %s" % (p["Name"], rgb))
        if part.Material.Name != p["Material"]:
            probs.add("%s material %s" % (p["Name"], part.Material.Name))
        welds = [c for c in kids(part) if c.ClassName == "WeldConstraint"]
        if p["Name"] != p["Model"]:
            if len(welds) != 1 or welds[0].Part0.Name != p["Model"]:
                probs.add(p["Name"] + ": should be welded to " + p["Model"])
        elif welds:
            probs.add(p["Name"] + ": a bone part should not be welded")
        if part.CanCollide or not part.Massless:
            probs.add(p["Name"] + ": should be CanCollide off and Massless")
    motors = [d for d in desc(model) if d.ClassName == "Motor6D"]
    if len(motors) != len(rig["Rig"]):
        probs.add("%d Motor6Ds, %d expected" % (len(motors), len(rig["Rig"])))
    worldpos = lua.eval("function(a, b) return (a * b).Position end")
    for j in rig["Rig"]:
        m = [x for x in motors if x.Name == j["Motor"]]
        if not m:
            probs.add("missing Motor6D " + j["Motor"])
            continue
        m = m[0]
        if m.Part0.Name != j["Part0"] or m.Part1.Name != j["Part1"] or m.Parent.Name != j["Part1"]:
            probs.add(j["Motor"] + ": parts / parent")
        a = worldpos(m.Part0.CFrame, m.C0)
        b = worldpos(m.Part1.CFrame, m.C1)
        want = lua.eval("function(c, v) return c:Inverse() * v end")(root_cf, a)
        if math.dist((a.X, a.Y, a.Z), (b.X, b.Y, b.Z)) > 1e-3 or \
                math.dist((want.X, want.Y, want.Z), np.array(j["Pivot"]) - hrp_rest) > 2e-3:
            probs.add(j["Motor"] + ": C0 / C1 do not meet at the pivot")
    for a in rig["Attachments"]:
        at = [d for d in by_name.get(a["Name"], []) if d.ClassName == "Attachment"]
        if not at:
            probs.add("missing attachment " + a["Name"])
            continue
        r = relpos(root_cf, lua.eval("function(at) return at.WorldCFrame end")(at[0]))
        if math.dist((r.X, r.Y, r.Z), np.array(a["Position"]) - hrp_rest) > 2e-3 or at[0].Parent.Name != a["Bone"]:
            probs.add("attachment %s misplaced" % a["Name"])
    for cls, name in (("PointLight", None), ("ParticleEmitter", "Mist"), ("Trail", "ScytheTrail"), ("Script", "ReaperController")):
        found = [d for d in desc(model) if d.ClassName == cls and (name is None or d.Name == name)]
        if len(found) != 1:
            probs.add("expected one %s %s" % (cls, name or ""))
    script = (by_name.get("ReaperController") or [None])[0]
    if script is not None and ("THROW_PATH = {{" not in (script.Source or "") or "THROW_AIM = {{" not in script.Source):
        probs.add("the controller is missing its throw data")
    attrs = dict(model.GetAttributes(model).items())
    for k in ("AI", "AggroRange", "WalkSpeed", "ChaseSpeed", "AttackCooldown", "MaxHealth", "Damage", "Knockback",
              "HealthBar", "RemoveOnDefeat", "AnimIdle", "AnimDefeat"):
        if k not in attrs:
            probs.add("attribute %s missing" % k)
    # standing on the ground (the mock's floor is y = 0) where the camera looks
    hip = hum.HipHeight
    bottom = hrp.CFrame.Position.Y - hrp.Size.Y / 2
    if abs(bottom - hip) > 1e-3:
        probs.add("the root part should float HipHeight above the ground (bottom %.3f, hip %.3f)" % (bottom, hip))
    feet = min(part.CFrame.Position.Y - part.Size.Y / 2 for part in meshparts if part.Name.endswith("Foot"))
    if abs(feet) > 0.05:
        probs.add("feet are not on the ground (%.3f)" % feet)
    print("build: %d mesh parts, %d motors, %d attachments" % (len(meshparts), len(motors), len(rig["Attachments"])))

    # ---------------------------------------------------------------- 2. rig vs animations
    brig = B.Rig(rig_path)
    clips = read_clips(anims_path)
    motor_by_part1 = {m.Part1.Name: m for m in motors}
    mkcf = lua.eval("function(x, y, z, a, b, c, d, e, f, g, h, i) return CFrame.new(x, y, z, a, b, c, d, e, f, g, h, i) end")
    lua_fk = lua.eval('''function(order, motors, parts, root, poses)
        local W = {HumanoidRootPart = root}
        for _, b in ipairs(order) do
            local m = motors[b]
            W[b] = W[m.Part0.Name] * m.C0 * (poses[b] or CFrame.new()) * m.C1:Inverse()
        end
        return W end''')
    rows = lua.eval("cframe_rows")
    order = [b for _, _, b, _ in brig.joints]
    model_to_world = None
    worst = 0.0
    for name, clip in clips.items():
        for i in np.linspace(0, len(clip["frames"]) - 1, 6).astype(int):
            X = clip["frames"][i]
            poses = lua.table_from({b: mkcf(*m[:3, 3], *m[:3, :3].flatten()) for b, m in X.items()})
            Wl = lua_fk(lua.table_from(order), lua.table_from(motor_by_part1), None, root_cf, poses)
            Wp = brig.fk(X)
            if model_to_world is None:
                r = rows(root_cf)
                hw = np.eye(4)
                hw[:3, 3] = r[:3]
                hw[:3, :3] = np.array(r[3:]).reshape(3, 3)
                model_to_world = hw @ np.linalg.inv(brig.rest["HumanoidRootPart"])
            for b in order:
                r = rows(Wl[b])
                lw = np.eye(4)
                lw[:3, 3] = r[:3]
                lw[:3, :3] = np.array(r[3:]).reshape(3, 3)
                pw = model_to_world @ Wp[b]
                err = float(np.abs(lw - pw).max())
                worst = max(worst, err)
                if err > 2e-3:
                    probs.add("%s frame %d: %s off by %.4f" % (name, i, b, err))
                    break
    print("rig: every bone of 6 frames of each animation matches the animation tools (worst %.1e)" % worst)

    # ---------------------------------------------------------------- 3. the fight
    folder = lua.eval('function() local f = Instance.new("Folder"); f.Name = "GrimReaperAnimations"; '
                      'f.Parent = game:GetService("ServerStorage"); return f end')()
    add_seq = lua.eval('''function(folder, name, length, loop, markers)
        local k = Instance.new("KeyframeSequence"); k.Name = name; k.Parent = folder
        local ms = {}
        for i = 1, #markers do ms[i] = {markers[i][1], markers[i][2]} end
        rawset(k, "_seq", {length = length, loop = loop, markers = ms})
        end''')
    for name, clip in clips.items():
        add_seq(folder, name, float(clip["length"]), bool(clip["loop"]),
                lua.table_from([lua.table_from([float(t), m]) for t, m in clip["markers"]]))
    lua.execute('''
        HITS = {}
        function make_player(name, x, z)
            local char = Instance.new("Model"); char.Name = name
            local hum = Instance.new("Humanoid"); hum.Parent = char
            local root = Instance.new("Part"); root.Name = "HumanoidRootPart"; root.Size = Vector3.new(2, 2, 1)
            root.CFrame = CFrame.new(x, 3, z); root.Parent = char
            local att = Instance.new("Attachment"); att.Name = "RootAttachment"; att.Parent = root
            char.PrimaryPart = root
            char.Parent = workspace
            local player = {Name = name, Character = char}
            table.insert(PLAYERS, player)
            return player, root, hum
        end
        function knocks(root)
            local n = 0
            for _, c in ipairs(root:GetChildren()) do if c.Name == "ReaperKnockback" then n = n + 1 end end
            return n
        end
    ''')
    model.SetAttribute(model, "Damage", 10)
    boss_hum, boss_root = hum, hrp
    G.SIM.humanoids = lua.table_from([boss_hum])
    lua.eval("function(h, r) rawset(h, '_root', r) end")(boss_hum, boss_root)
    # run the controller from its Source, as a Script would
    src = script.Source
    start = lua.eval('''function(script, src)
        local env = setmetatable({script = script}, {__index = _G})
        local fn, err = load(src, "=ReaperController", "t", env)
        if not fn then error(err) end
        local co = coroutine.create(fn)
        SIM.resume(co)
        return co end''')
    player, proot, phum = lua.eval("make_player")("Tester", 0.0, 0.0)
    boss_pos = boss_root.CFrame.Position
    vec = G.Vector3.new
    cfnew = G.CFrame.new

    def put_player(dist, bearing_deg=0.0, up=0.0):
        """Stand the player `dist` studs from the boss, `bearing` degrees right of its facing."""
        c = boss_root.CFrame
        look = c.LookVector
        right = (look.Z * -1, 0, look.X)        # facing (x, z) turned right
        b = math.radians(bearing_deg)
        dx = look.X * math.cos(b) + right[0] * math.sin(b)
        dz = look.Z * math.cos(b) + right[2] * math.sin(b)
        p = c.Position
        floor = p.Y - boss_root.Size.Y / 2 - boss_hum.HipHeight
        proot.CFrame = cfnew(p.X + dx * dist, floor + 3 + up, p.Z + dz * dist)

    events = []
    hit_log = lua.eval("HITS")
    aim_line = next(r for r in src.split("\n") if r.startswith("local THROW_AIM"))
    throw_aim = json.loads(aim_line.split("=", 1)[1].strip().replace("{", "[").replace("}", "]"))
    co = start(script, src)
    if G.ERRORS and len(G.ERRORS) > 0:
        for e in G.ERRORS.values():
            print("controller error:", e)
        return 1
    lua.eval('''function(model)
        model.ReaperHit.Event:Connect(function(player, attack, damage)
            table.insert(HITS, {attack, damage, SIM.t, player.Name})
        end)
        end''')(model)
    step = G.SIM.step
    dt = 1 / 30

    def run(seconds, each=None):
        for _ in range(int(round(seconds / dt))):
            if each:
                each()
            step(dt)

    def hits_since(t0, attack=None):
        out = []
        for h in hit_log.values():
            if h[3] >= t0 - 1e-6 and (attack is None or h[1] == attack):
                out.append(h)
        return out

    def played(name):
        p = G.SIM.played
        return 0 if p is None or p[name] is None else p[name]

    # a) it notices the player 100 studs away and roars, then closes in and attacks
    put_player(100)
    t0 = G.SIM.t
    run(4.0)
    if played("ReaperRoar") < 1:
        probs.add("no roar on first sight of the player")
    d0 = 100
    run(14.0)
    p = boss_root.CFrame.Position
    q = proot.CFrame.Position
    d1 = math.hypot(p.X - q.X, p.Z - q.Z)
    if d1 > 40:
        probs.add("the boss did not close in (still %.1f studs away)" % d1)
    if played("ReaperRun") < 1 or played("ReaperWalk") + played("ReaperRun") < 1:
        probs.add("no walk / run animation while closing in")
    natural = sum(played(n) for n in ("ReaperStomp", "ReaperSwing", "ReaperSpin", "ReaperThrow"))
    if natural < 1:
        probs.add("the AI never attacked in 14 seconds")
    events.append("AI: roared, closed from %d to %.0f studs, %d attacks on its own, %d hits" % (
        d0, d1, natural, len(hits_since(t0))))

    # b) each attack on demand, the player where it should land (or jumping clear)
    model.SetAttribute(model, "AI", False)
    run(4.0)
    attack = lua.eval("function(model, name) model.ReaperAttack:Fire(name) end")
    cases = [("Stomp", 9, 0, 0, True), ("Stomp", 9, 0, 8, False), ("Swing", 16, 10, 0, True), ("Swing", 16, 150, 0, False),
             ("Spin", 14, 180, 0, True), ("Spin", 30, 0, 0, False), ("Throw", 22, 0, 0, True), ("Roar", 20, 40, 0, True)]
    for name, dist, bearing, up, want in cases:
        run(0.6)
        phum.Health = 100
        put_player(dist, bearing, 0)
        t0 = G.SIM.t
        attack(model, name)
        jumping = {"on": up > 0}

        def keep():
            if name != "Throw":
                put_player(dist, bearing, up if jumping["on"] else 0)
        if name == "Throw":
            # it turns so the player sits on the scythe's way out (the aim angle to its right)
            run(0.4)
            bear = float(np.interp(dist, [r[0] for r in throw_aim], [r[1] for r in throw_aim]))
            if bearing == 0:
                put_player(dist, bear, 0)
            run(3.2)
        else:
            run(3.2, keep)
        got = hits_since(t0, name)
        if bool(got) != want:
            probs.add("%s with the player %d studs away at %d degrees%s: %s" % (
                name, dist, bearing, ", jumping" if up else "", "hit" if got else "missed"))
        events.append("%-5s player %2d studs, %3d deg%s -> %s" % (name, dist, bearing, " (jumping)" if up else "",
                                                                 "HIT" if got else "miss"))
    if lua.eval("knocks")(proot) < 1 and not any(h[2] > 0 for h in hit_log.values()):
        probs.add("hits never pushed the player or took damage")
    if not any(h[2] > 0 for h in hit_log.values()):
        probs.add("hits never took damage with Damage = 10")

    # c) hurt, enrage at half health, defeat
    run(2.0)
    hurts = played("ReaperHurt")
    boss_hum.Health = boss_hum.Health - 30
    run(1.0)
    if played("ReaperHurt") <= hurts:
        probs.add("no hurt flinch when damaged")
    roars = played("ReaperRoar")
    boss_hum.Health = boss_hum.MaxHealth * 0.45
    run(3.0)
    if played("ReaperRoar") <= roars:
        probs.add("no enrage roar at half health")
    defeated = lua.eval("{n = 0}")
    lua.eval("function(model, d) model.ReaperDefeated.Event:Connect(function() d.n = d.n + 1 end) end")(model, defeated)
    boss_hum.Health = 0
    run(1.0)
    if defeated.n != 1 or played("ReaperDefeat") != 1:
        probs.add("defeat: event %d, animation %d" % (defeated.n, played("ReaperDefeat")))
    if not boss_root.Anchored:
        probs.add("the root part should be anchored once defeated")
    run(7.0)
    if model.Parent is not None:
        probs.add("the boss was not removed after its defeat")
    events.append("hurt flinch, enrage roar, defeat event + animation, faded and removed")
    for e in G.ERRORS.values():
        probs.add("runtime error: " + e)
    for w in G.WARNINGS.values():
        if "build warning" not in w:
            probs.add("warning: " + w)
    print("fight (%.0f simulated seconds):" % G.SIM.t)
    for e in events:
        print("  ", e)
    seen = sorted({h[1] for h in hit_log.values()})
    print("   hits by attack: %s" % ", ".join("%s %d" % (a, sum(1 for h in hit_log.values() if h[1] == a)) for a in seen))
    print("%d problems" % len(probs))
    for p in probs[:40]:
        print("  ", p)
    return 1 if probs else 0


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    o = dict(x[2:].split("=", 1) if "=" in x else (x[2:], "1") for x in sys.argv[1:] if x.startswith("--"))
    sys.exit(main(a[0], a[1], a[2], float(o.get("scale", 1.0)), "turn" in o))
