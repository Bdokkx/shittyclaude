"""Build one piece of the bricks kit: scene -> checks -> JSON -> Studio build script -> mock test.

    python blender/build_kit.py <piece> <outdir>

Pieces:
  potatoes_meadow   PotatoKit.Potatoes.<6 Meadow Patch kinds> + PotatoKit.PotatoAnimations (6 clips)

Writes <outdir>/<Piece>.json (the scene), <outdir>/<Piece>_anims.json (rbxtool JSON of the clips),
<outdir>/Build<Piece>.lua (the unattended build script) and runs tools/mock_kit.py on it.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
TOOLS = os.path.join(os.path.dirname(HERE), "tools")
sys.path.insert(0, TOOLS)

import numpy as np  # noqa: E402
from spsgeo import CF  # noqa: E402
import spslib  # noqa: E402

from potato import brickcheck, fuse, guardian_anim, guardians, npc, plotkit, rig, spud_anim, spuds  # noqa: E402,E501
from potato import roots as ROOTS, roots_anim as RA, rootbricks  # noqa: E402
from potato import scenery, scenery_clock, scenery_dino, scenery_haunt, scenery_jungle, scenery_reef  # noqa: E402,F401,E501
from potato import scenery_cloud, scenery_neon, scenery_olympus, scenery_toy, scenery_void  # noqa: E402,F401,E501

PIECES = {
    "potatoes_meadow": dict(file="Potatoes_Meadow", title="the Meadow Patch potatoes and their clips"),
    "potatoes_dunes": dict(file="Potatoes_Dunes", title="the Sandy Dunes potatoes", area="Dunes"),
    "potatoes_marsh": dict(file="Potatoes_Marsh", title="the Mushroom Marsh potatoes", area="Marsh"),
    "potatoes_frost": dict(file="Potatoes_Frost", title="the Frost Fields potatoes", area="Frost"),
    "potatoes_lava": dict(file="Potatoes_Lava", title="the Lava Furrows potatoes", area="Lava"),
    "potatoes_crystal": dict(file="Potatoes_Crystal", title="the Crystal Caverns potatoes", area="Crystal"),
    "potatoes_candy": dict(file="Potatoes_Candy", title="the Candy Crops potatoes", area="Candy"),
    "potatoes_cosmic": dict(file="Potatoes_Cosmic", title="the Cosmic Garden potatoes", area="Cosmic"),
    "potatoes_jungle": dict(file="Potatoes_Jungle", title="the Jungle Ruins potatoes", area="Jungle"),
    "potatoes_reef": dict(file="Potatoes_Reef", title="the Coral Cove potatoes", area="Reef"),
    "potatoes_haunt": dict(file="Potatoes_Haunt", title="the Haunted Hollow potatoes", area="Haunt"),
    "potatoes_dino": dict(file="Potatoes_Dino", title="the Dino Valley potatoes", area="Dino"),
    "potatoes_toy": dict(file="Potatoes_Toy", title="the Toy Town potatoes", area="Toy"),
    "potatoes_clock": dict(file="Potatoes_Clock", title="the Clockwork Yard potatoes", area="Clock"),
    "potatoes_neon": dict(file="Potatoes_Neon", title="the Neon City potatoes", area="Neon"),
    "potatoes_cloud": dict(file="Potatoes_Cloud", title="the Cloud Kingdom potatoes", area="Cloud"),
    "potatoes_void": dict(file="Potatoes_Void", title="the Glitch Void potatoes", area="Void"),
    "potatoes_olympus": dict(file="Potatoes_Olympus", title="the Spud Olympus potatoes", area="Olympus"),
    "scenery_jungle": dict(file="Scenery_Jungle", title="the Jungle Ruins hero and props", area="Jungle"),
    "scenery_reef": dict(file="Scenery_Reef", title="the Coral Cove hero and props", area="Reef"),
    "scenery_haunt": dict(file="Scenery_Haunt", title="the Haunted Hollow hero and props", area="Haunt"),
    "scenery_dino": dict(file="Scenery_Dino", title="the Dino Valley hero and props", area="Dino"),
    "scenery_toy": dict(file="Scenery_Toy", title="the Toy Town hero and props", area="Toy"),
    "scenery_clock": dict(file="Scenery_Clock", title="the Clockwork Yard hero and props", area="Clock"),
    "scenery_neon": dict(file="Scenery_Neon", title="the Neon City hero and props", area="Neon"),
    "scenery_cloud": dict(file="Scenery_Cloud", title="the Cloud Kingdom hero and props", area="Cloud"),
    "scenery_void": dict(file="Scenery_Void", title="the Glitch Void hero and props", area="Void"),
    "scenery_olympus": dict(file="Scenery_Olympus", title="the Spud Olympus hero and props", area="Olympus"),
    "plot": dict(file="PlotKit", title="the plot kit (fences, soil, board, mound, seeds)"),
    "questnpc": dict(file="QuestNpc", title="Farmer Spud, the quest NPC, and his clips"),
    "fuse": dict(file="FuseMachine", title="the Fuse Machine"),
    "rootmonster": dict(file="RootMonster", title="the RootMonster in bricks and its four clips"),
    "guardians1": dict(file="Guardians1", title="guardians 1-6 (Meadow to Frost) and their clips", span=(0, 6)),
    "guardians2": dict(file="Guardians2", title="guardians 7-12 (Haunt to Candy) and their clips", span=(6, 12)),
    "guardians3": dict(file="Guardians3", title="guardians 13-18 (Clock to Olympus) and their clips", span=(12, 18)),
}
GAITS = ("Stomp", "Scuttle", "Hop", "Float", "Gallop")


def check_rootmonster(sc, m):
    """The same rig as part 1's: joints, their Part0s and frames, attachments, eyes; the clips start
    and end under the ground; no flickering faces."""
    errs = []
    parts = [n for n in m.walk() if n.kind == "Part"]
    root = m.p.get("primary")
    if root is None or root.name != "Root" or not root.p["anchored"] or root.p["transparency"] < 0.99 \
            or not root.p["touch"]:
        errs.append("Root is not the anchored, invisible, touchable PrimaryPart")
    for p in parts:
        if p is root:
            continue
        if p.p["anchored"] or p.p["collide"] or p.p["touch"] or p.p["query"] or not p.p["massless"]:
            errs.append("%s flags" % p.path())
        if p.p["shadow"] and max(p.p["size"]) < 2.5:
            errs.append("small %s casts a shadow" % p.path())
    want = [("Heap", "Root", "Heap", CF())]
    for (tname, bp, d0, length, bend, claw) in ROOTS.TENTACLES:
        frames, seg = ROOTS.tentacle_frames(bp, d0, length, bend)
        prev = "Heap"
        for i, fr in enumerate(frames):
            pname = "%sSeg%d" % (tname, i + 1)
            want.append((pname, prev, pname, fr))
            prev = pname
    motors = {n.name: n for n in m.walk() if n.kind == "Motor"}
    if sorted(motors) != sorted(w[0] for w in want):
        errs.append("joints %s" % sorted(motors))
    for (j, p0, p1, fr) in want:
        n = motors.get(j)
        if n is None:
            continue
        if n.p["part0"].name != p0 or n.p["part1"].name != p1 or n.parent is not n.p["part0"]:
            errs.append("%s joins %s -> %s (in %s)" % (j, n.p["part0"].name, n.p["part1"].name, n.parent.name))
        h = n.p["hinge"]
        if not (np.allclose(h.p, fr.p, atol=1e-6) and np.allclose(h.R, fr.R, atol=1e-6)):
            errs.append("%s: frame moved" % j)
    att = sorted((n.parent.name, n.name) for n in m.walk() if n.kind == "Attachment")
    if att != sorted([("Root", "Fx_Dirt"), ("Heap", "Fx_Eyes"), ("Tentacle1Seg5", "Claw"), ("Tentacle2Seg5", "Claw")]):
        errs.append("attachments %s" % att)
    eyes = [p for p in parts if p.name == "Eye"]
    if len(eyes) != 2 or any(p.p["material"] != "Neon" or p.p.get("attrs", {}).get("Flicker") != 0.1 for p in eyes):
        errs.append("eyes")
    errs += brickcheck.rules(parts)
    for a, b, ar in brickcheck.zfight(parts, ground=0.0):
        errs.append("z-fight %s %s / %s %s (%.3f)" % (a.path().split("/", 2)[-1], [round(v, 2) for v in a.p["size"]],
                                                      b.path().split("/", 2)[-1], [round(v, 2) for v in b.p["size"]], ar))
    P = rig.Pose(m)

    def extent(X):
        lo, hi = 1e9, -1e9
        for part, cf_ in P.world(X).values():
            if part.p["transparency"] >= 0.99:
                continue
            e = np.abs(cf_.R) @ (np.array(part.p["size"]) / 2)
            lo, hi = min(lo, float(cf_.p[1] - e[1])), max(hi, float(cf_.p[1] + e[1]))
        return lo, hi
    for c in RA.CLIPS:
        fr = c.bake()
        if c.name == "RootEmerge":
            top = extent(fr[0])[1]
            print("  RootEmerge starts with its highest brick %.1f under the ground" % -top)
            if top > -1.0:
                errs.append("RootEmerge starts with a brick %.2f above ground" % top)
        if c.name == "RootWither":
            top = extent(fr[-1])[1]
            print("  RootWither ends with its highest brick %.1f under the ground" % -top)
            if top > -1.0:
                errs.append("RootWither ends with a brick %.2f above ground" % top)
        if c.name == "RootChase":
            low = min(extent(X)[0] for X in fr)
            print("  RootChase digs at most %.1f into the soil" % -low)
    return errs


def check_guardian(m, area):
    errs = []
    parts = [n for n in m.walk() if n.kind == "Part"]
    root = m.p.get("primary")
    if root is None or root.name != "Root" or not root.p["anchored"] or root.p["transparency"] < 0.99:
        errs.append("%s: Root is not an anchored invisible PrimaryPart" % area)
    elif abs(float(root.p["cf"].p[1]) - root.p["size"][1] / 2) > 1e-6:
        errs.append("%s: Root is not on the ground" % area)
    if len(parts) > 60:
        errs.append("%s: %d parts" % (area, len(parts)))
    for p in parts:
        if p is root:
            continue
        if p.p["anchored"] or p.p["collide"] or p.p["touch"] or p.p["query"] or not p.p["massless"]:
            errs.append("%s: %s flags" % (area, p.path()))
        if p.p["shadow"] and max(p.p["size"]) < 2.5:
            errs.append("%s: small %s casts a shadow" % (area, p.path()))
    eo = [p for p in parts if p.name == "EyeOpen"]
    es = [p for p in parts if p.name == "EyeShut"]
    if not eo or not es or any(p.p["transparency"] > 0 for p in eo) or any(p.p["transparency"] < 1 for p in es):
        errs.append("%s: eyes (%d open, %d shut)" % (area, len(eo), len(es)))
    at = m.p.get("attrs", {})
    if at.get("Gait") not in GAITS or not 6.0 <= at.get("Height", 0) <= 10.0 or not at.get("RunSpeed"):
        errs.append("%s: attributes %s" % (area, at))
    motors = [n for n in m.walk() if n.kind == "Motor"]
    for n in motors:
        if n.p["part1"].name != n.name:
            errs.append("%s: motor %s drives %s" % (area, n.name, n.p["part1"].name))
    names = {n.name for n in motors}
    for c in guardian_anim.CLIPS[area]:
        frames = c.bake()
        extra = set().union(*[set(X) for X in frames]) - names
        if extra:
            errs.append("%s: %s writes %s" % (area, c.name, sorted(extra)))
    errs += ["%s: %s" % (area, e) for e in brickcheck.rules(parts)]
    for shut in (False, True):                                 # flickering faces, eyes open and eyes shut
        if shut:
            for p in eo:
                p.p["transparency"] = 1.0
            for p in es:
                p.p["transparency"] = 0.0
        for a, b, ar in brickcheck.zfight(parts, ground=0.0):
            errs.append("%s%s: z-fight %s %s / %s %s (%.3f)" % (area, " (shut)" if shut else "", a.path().split("/", 2)[-1],
                        [round(v, 2) for v in a.p["size"]], b.path().split("/", 2)[-1],
                        [round(v, 2) for v in b.p["size"]], ar))
        if shut:
            for p in eo:
                p.p["transparency"] = 0.0
            for p in es:
                p.p["transparency"] = 1.0
    # no clip pushes a part far into the ground
    P = rig.Pose(m)
    for c in guardian_anim.CLIPS[area]:
        frames = c.bake()
        low = 1e9
        for X in frames[::3]:
            for part, cf_ in P.world(X).values():
                if part.p["transparency"] >= 0.99 and part.name != "EyeShut":
                    continue
                low = min(low, float((cf_.p - np.abs(cf_.R) @ (np.array(part.p["size"]) / 2))[1]))
        if low < -0.45:
            errs.append("%s: %s goes %.2f into the ground" % (area, c.name, -low))
    return errs


def check_rig(m, joints, allowed_anchored=("Root", "Prompt")):
    """A brick rig: Root anchored PrimaryPart, every other part unanchored (but the Prompt), the joints
    there, surfaces right, no flickering faces at rest."""
    errs = []
    parts = [n for n in m.walk() if n.kind == "Part"]
    if m.p.get("primary") is None or m.p["primary"].name != "Root":
        errs.append("%s: PrimaryPart is not Root" % m.name)
    for p in parts:
        if p.p["anchored"] and p.name not in allowed_anchored:
            errs.append("%s: %s anchored" % (m.name, p.path()))
        if p.p["collide"] or p.p["touch"]:
            errs.append("%s: %s collides / touches" % (m.name, p.path()))
        if p.p["shadow"] and max(p.p["size"]) < 2.5:
            errs.append("%s: small %s casts a shadow" % (m.name, p.path()))
    names = sorted(n.name for n in m.walk() if n.kind == "Motor")
    for j in joints:
        if j not in names:
            errs.append("%s: no Motor6D %s (has %s)" % (m.name, j, names))
    errs += ["%s: %s" % (m.name, e) for e in brickcheck.rules(parts)]
    for a, b, ar in brickcheck.zfight(parts, ground=0.0):
        errs.append("%s: z-fight %s %s / %s %s (%.3f)" % (m.name, a.path().split("/", 2)[-1],
                    [round(v, 2) for v in a.p["size"]], b.path().split("/", 2)[-1],
                    [round(v, 2) for v in b.p["size"]], ar))
    return errs


def check_deco(sc):
    """Decoration rules for the kit pieces, and flickering faces inside each piece."""
    errs = []
    items = [n for n in sc.root.walk() if n.kind == "Model"]
    for m in items:
        parts = [n for n in m.walk() if n.kind == "Part"]
        if m.p.get("primary") is None:
            errs.append("%s: no PrimaryPart" % m.path())
        for p in parts:
            if not p.p["anchored"] or p.p["collide"] or p.p["touch"] or p.p["query"]:
                errs.append("%s: flags" % p.path())
            if p.p["shadow"] and max(p.p["size"]) < 2.5:
                errs.append("%s: small part casts a shadow" % p.path())
        errs += brickcheck.rules(parts)
        for a, b, ar in brickcheck.zfight(parts, ground=0.0):
            errs.append("%s: z-fight %s %s / %s %s (%.3f)" % (m.path(), a.name, [round(v, 2) for v in a.p["size"]],
                                                               b.name, [round(v, 2) for v in b.p["size"]], ar))
    return errs


def potatoes(area, anims=True):
    sc = spslib.Scene("PotatoKit")
    pot = sc.container(sc.root, "Potatoes")
    models = [k.build(sc, pot) for k in spuds.AREAS[area]]
    folder = sc.container(sc.root, "PotatoAnimations") if anims else None
    return sc, models, folder


def check_potatoes(models):
    errs = []
    for m in models:
        parts = [n for n in m.walk() if n.kind == "Part"]
        if len(parts) > spuds.BUDGET:
            errs.append("%s: %d parts" % (m.name, len(parts)))
        if m.p.get("primary") is None or m.p["primary"].name != "Root" or not m.p["primary"].p["anchored"]:
            errs.append("%s: Root is not an anchored PrimaryPart" % m.name)
        names = {c.name for c in m.children}
        for f in spuds.FEATURES + ("Root", "Body"):
            if f not in names:
                errs.append("%s: no %s" % (m.name, f))
        motors = [n for n in m.walk() if n.kind == "Motor"]
        mnames = sorted(n.name for n in motors)
        if mnames != sorted(spuds.FEATURES + ("Body",)):
            errs.append("%s: motors %s" % (m.name, mnames))
        for n in motors:
            if n.p["part1"].name != n.name:
                errs.append("%s: motor %s drives %s" % (m.name, n.name, n.p["part1"].name))
        for p in parts:
            if p.name == "Root":
                continue
            if p.p["anchored"] or p.p["collide"] or p.p["touch"] or p.p["query"] or not p.p["massless"]:
                errs.append("%s: %s flags" % (m.name, p.path()))
            if p.p["transparency"] >= 0.99 and p.name not in spuds.FEATURES:
                errs.append("%s: invisible %s" % (m.name, p.path()))
        if "LegHeight" not in m.p.get("attrs", {}):
            errs.append("%s: no LegHeight" % m.name)
        errs += ["%s: %s" % (m.name, e) for e in brickcheck.rules(parts)]
        # flickering faces, in the two shapes a potato takes: on the ground without legs (levels
        # 2-5, the most features it shows there) and on its legs with everything (level 10)
        P = spuds.Pose(m)
        for level in (1, 5, 10):
            world = P.world({}, level)
            saved = {}
            for key, (part, cf_) in world.items():
                saved[key] = part.p["cf"]
                part.p["cf"] = cf_
            shown = [p for p in parts if P.shown(p, level)]
            for a, b, ar in brickcheck.zfight(shown):
                errs.append("%s L%d: z-fight %s %s / %s %s (%.3f)" % (m.name, level, a.path().split("/", 3)[-1],
                            [round(v, 2) for v in a.p["size"]], b.path().split("/", 3)[-1],
                            [round(v, 2) for v in b.p["size"]], ar))
            for key, (part, _cf) in world.items():
                part.p["cf"] = saved[key]
    return errs


def main():
    piece, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    cfg = PIECES[piece]
    anim_specs = {}
    if piece == "potatoes_meadow":
        sc, models, _anims = potatoes("Meadow")
        errs = check_potatoes(models)
        baked, folder = spud_anim.bake_all()
        ap = os.path.join(out, cfg["file"] + "_anims.json")
        with open(ap, "w") as f:
            json.dump([folder], f)
        anim_specs["PotatoAnimations"] = ap
        for m in models:
            n = sum(1 for x in m.walk() if x.kind == "Part")
            print("  %-12s %2d parts  LegHeight %.2f" % (m.name, n, m.p["attrs"]["LegHeight"]))
        for c, fr in baked:
            print("  %-14s %.1f s  %d keyframes  joints %s" % (c.name, c.length, len(fr),
                                                              sorted(spud_anim.moving(fr))))
    elif piece.startswith("potatoes_"):
        sc, models, _f = potatoes(cfg["area"], anims=False)
        errs = check_potatoes(models)
        for m in models:
            n = sum(1 for x in m.walk() if x.kind == "Part")
            print("  %-14s %2d parts  LegHeight %.2f" % (m.name, n, m.p["attrs"]["LegHeight"]))
    elif piece == "questnpc":
        sc = spslib.Scene("PotatoKit")
        m = npc.build(sc, sc.root)
        sc.container(sc.root, "QuestNpcAnimations")
        errs = check_rig(m, ("Waist", "Neck", "ShoulderL", "ShoulderR", "Brow", "Moustache"))
        clips = [rig.write_clip(m, c, c.bake()) for c in npc.CLIPS]
        ap = os.path.join(out, cfg["file"] + "_anims.json")
        with open(ap, "w") as f:
            json.dump([rig.folder_json("QuestNpcAnimations", clips)], f)
        anim_specs["QuestNpcAnimations"] = ap
        print("  QuestNpc: %d parts, joints %s" % (sum(1 for x in m.walk() if x.kind == "Part"),
                                                   sorted(n.name for n in m.walk() if n.kind == "Motor")))
        for c in npc.CLIPS:
            print("  %-6s %.1f s loop=%s joints %s" % (c.name, c.length, c.loop, sorted(rig.moving(c.bake()))))
    elif piece == "fuse":
        sc = spslib.Scene("PotatoKit")
        m = fuse.build(sc, sc.root)
        parts = [n for n in m.walk() if n.kind == "Part"]
        errs = []
        for nm in ("Board", "Screen", "Prompt", "Socket1", "Socket2", "Socket3"):
            if not any(p.name == nm for p in parts):
                errs.append("FuseMachine: no %s" % nm)
        for p in parts:
            if not p.p["anchored"] or p.p["touch"]:
                errs.append("FuseMachine: %s flags" % p.name)
            if p.p["shadow"] and max(p.p["size"]) < 2.5:
                errs.append("FuseMachine: small %s casts a shadow" % p.name)
        errs += brickcheck.rules(parts)
        for a, b, ar in brickcheck.zfight(parts, ground=0.0):
            errs.append("FuseMachine: z-fight %s %s / %s %s (%.3f)" % (a.name, [round(v, 2) for v in a.p["size"]],
                        b.name, [round(v, 2) for v in b.p["size"]], ar))
        lo = np.min([p.p["cf"].p - np.abs(p.p["cf"].R) @ (np.array(p.p["size"]) / 2) for p in parts], axis=0)
        hi = np.max([p.p["cf"].p + np.abs(p.p["cf"].R) @ (np.array(p.p["size"]) / 2) for p in parts], axis=0)
        print("  FuseMachine: %d parts (%d solid), size %s" % (len(parts), sum(1 for p in parts if p.p["collide"]),
                                                             np.round(hi - lo, 1)))
    elif piece == "rootmonster":
        sc = spslib.Scene("PotatoKit")
        m = rootbricks.build(sc, sc.root)
        sc.container(sc.root, "RootAnimations")
        errs = check_rootmonster(sc, m)
        clips = [RA.write(sc.root_rig, c, c.bake()) for c in RA.CLIPS]
        ap = os.path.join(out, cfg["file"] + "_anims.json")
        with open(ap, "w") as f:
            json.dump([rig.folder_json("RootAnimations", clips)], f)
        anim_specs["RootAnimations"] = ap
        print("  RootMonster: %d parts, %d joints" % (sum(1 for x in m.walk() if x.kind == "Part"),
                                                     sum(1 for x in m.walk() if x.kind == "Motor")))
    elif piece.startswith("guardians"):
        sc = spslib.Scene("PotatoKit")
        gfold = sc.container(sc.root, "Guardians")
        afold = sc.container(sc.root, "GuardianAnimations")
        errs = []
        i0, i1 = cfg["span"]
        for area, title, fn in guardians.AREAS[i0:i1]:
            m = fn(sc, gfold)
            sc.container(afold, area)
            errs += check_guardian(m, area)
            clips = [rig.write_clip(m, c, c.bake()) for c in guardian_anim.CLIPS[area]]
            ap = os.path.join(out, "%s_%s_anims.json" % (cfg["file"], area))
            with open(ap, "w") as f:
                json.dump([rig.folder_json(area, clips)], f)
            anim_specs[area] = ap
            at = m.p["attrs"]
            print("  %-8s %-16s %2d parts  %-7s Height %.2f  RunSpeed %4.1f  joints %s" % (
                area, title, sum(1 for x in m.walk() if x.kind == "Part"), at["Gait"], at["Height"], at["RunSpeed"],
                sorted(n.name for n in m.walk() if n.kind == "Motor")))
            for c in guardian_anim.CLIPS[area]:
                fr = c.bake()
                print("           %-5s %.2f s %s %3d keys  joints %s" % (c.name, c.length, "loop" if c.loop else "once",
                                                                      len(fr), sorted(rig.moving(fr))))
    elif piece.startswith("scenery_"):
        sc = spslib.Scene("PotatoKit")
        hero, props = scenery.build_area(sc, cfg["area"])
        errs = scenery.check(hero, props)
        for m in [hero] + props:
            print("  " + scenery.summary(m))
    elif piece == "plot":
        sc = spslib.Scene("PotatoKit")
        plotkit.build(sc)
        errs = check_deco(sc)
        for m in [n for n in sc.root.walk() if n.kind == "Model"]:
            print("  %-34s %3d parts" % (m.path(), sum(1 for x in m.walk() if x.kind == "Part")))
    else:
        raise SystemExit("unknown piece " + piece)
    if errs:
        print("CHECKS FAILED:")
        for e in errs:
            print("   ", e)
        sys.exit(1)
    print("checks passed")
    jp = os.path.join(out, cfg["file"] + ".json")
    spslib.to_json(sc, jp)
    lua = os.path.join(out, "Build" + cfg["file"].replace("_", "") + ".lua")
    import gen_kit
    gen_kit.main(jp, lua, cfg["title"], anim_specs)
    py = sys.executable
    r = subprocess.run([py, os.path.join(TOOLS, "mock_kit.py"), jp, lua] +
                       ["%s=%s" % kv for kv in anim_specs.items()])
    sys.exit(r.returncode)


if __name__ == "__main__":
    main()
