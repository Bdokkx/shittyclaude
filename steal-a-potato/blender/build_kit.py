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

import spslib  # noqa: E402

from potato import brickcheck, spud_anim, spuds  # noqa: E402

PIECES = {
    "potatoes_meadow": dict(file="Potatoes_Meadow", title="the Meadow Patch potatoes and their clips"),
}


def potatoes(area):
    sc = spslib.Scene("PotatoKit")
    pot = sc.container(sc.root, "Potatoes")
    models = [k.build(sc, pot) for k in spuds.AREAS[area]]
    anims = sc.container(sc.root, "PotatoAnimations")
    return sc, models, anims


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
