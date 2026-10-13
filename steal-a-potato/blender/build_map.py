"""Build Workspace.PotatoMap in bricks: scene -> checks -> JSON -> Studio build script -> mock test.

    python blender/build_map.py <outdir> [fv=<folk_valley_props.json>] [nomock]

Writes <outdir>/PotatoMap.json (every placed part), <outdir>/PotatoMap_stamps.json (the pieces
written once and their copies), <outdir>/BuildPotatoMap.lua and runs tools/mock_map.py on it.
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

from potato import scenery, studmap as SM  # noqa: E402

FV_DEFAULT = "/tmp/claude-0/-home-user-shittyclaude/de3978ba-38c5-504e-80ab-5b405ce568f9/scratchpad/fvdata/fv.json"


def _cf(c):
    return [[round(float(v), 5) for v in c.p], [[round(float(v), 6) for v in row] for row in c.R]]


def write_stamps(mb, path):
    T = {}
    for key, t in mb.st.templates.items():
        T[key] = {"parts": [dict(name=p["name"], size=[round(float(v), 5) for v in p["size"]], rel=_cf(p["rel"]),
                                 color=list(p["color"]), shape=p["shape"], material=p["material"],
                                 transparency=p["transparency"], flags=p["flags"], surfaces=p["surfaces"],
                                 attrs=p["attrs"]) for p in t.parts],
                  "primary": t.primary}
    inst = []
    for i in mb.st.instances:
        inst.append(dict(node=i["model"].idx, key=i["key"], cf=_cf(i["cf"]), scale=i["scale"],
                         recolour=[[list(a), list(b)] for a, b in i["recolour"].items()], solid=i["solid"]))
    with open(path, "w") as f:
        json.dump({"templates": T, "instances": inst}, f, separators=(",", ":"))


def main():
    out = sys.argv[1]
    opts = dict(a.split("=", 1) for a in sys.argv[2:] if "=" in a)
    os.makedirs(out, exist_ok=True)
    scenery.load_all()
    mb = SM.MapBuild(opts.get("fv", FV_DEFAULT)).build()
    tops, per_area = SM.stats(mb)
    print("parts:", sum(tops.values()), tops)
    for n, c in per_area.items():
        a = SM.AREAS[n - 1]
        hero = "hero" if mb.info[n]["hero"] else "NO HERO"
        print("  Area%-2d %-16s %5d parts  %-7s props %3d" % (n, a[1], c, hero, len(mb.info[n]["props"])))
    print("templates %d (%d parts), copies %d" % (len(mb.st.templates), mb.st.parts(), len(mb.st.instances)))
    errs = SM.check(mb)
    if errs:
        print("CHECKS FAILED:")
        for e in errs[:80]:
            print("   ", e)
        print("   (%d in all)" % len(errs))
        if "force" not in sys.argv:
            sys.exit(1)
    else:
        print("checks passed")
    info = {"total": sum(tops.values()), "tops": tops, "templates": len(mb.st.templates),
            "template_parts": mb.st.parts(), "copies": len(mb.st.instances), "areas": []}
    for n, c in per_area.items():
        a = SM.AREAS[n - 1]
        kinds = {}
        for m in mb.fields.find("Area%d" % n).find("Scenery").children:
            kinds[m.name] = kinds.get(m.name, 0) + 1
        extras = [m.name for m in mb.fields.find("Area%d" % n).children if m.kind == "Model" and m.name != "Hero"]
        info["areas"].append(dict(n=n, id=a[0], name=a[1], ground=a[2], wall=a[3], side=a[8], parts=c,
                                  hero=bool(mb.info[n]["hero"]), props=kinds, extras=extras,
                                  mounds=[[round(x, 1), round(z, 1)] for x, z in mb.info[n]["mounds"]]))
    with open(os.path.join(out, "map_stats.json"), "w") as f:
        json.dump(info, f, indent=1)
    jp = os.path.join(out, "PotatoMap.json")
    spslib.to_json(mb.sc, jp)
    sp = os.path.join(out, "PotatoMap_stamps.json")
    write_stamps(mb, sp)
    lua = os.path.join(out, "BuildPotatoMap.lua")
    import gen_map
    gen_map.main(jp, sp, lua, "the map (Workspace.PotatoMap)")
    if "nomock" in sys.argv:
        return
    r = subprocess.run([sys.executable, os.path.join(TOOLS, "mock_map.py"), jp, lua])
    sys.exit(r.returncode)


if __name__ == "__main__":
    main()
