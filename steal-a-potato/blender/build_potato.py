"""Build STEAL A POTATO: scene -> checks -> potato.json + RootAnimations (JSON and .rbxm) -> FBX.

    python blender/build_potato.py <outdir> [--no-fbx] [--areas=1,2]

Writes <outdir>/potato.json (what BuildStealAPotato.lua rebuilds), RootAnimations.json /
RootAnimations.rbxm (the RootMonster's KeyframeSequences), stats.json and StealAPotato.fbx (one
white mesh per unique mesh name plus the SAP_Axis marker cubes). Fails loudly if a check fails.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from potato import build, checks, roots_anim as RA  # noqa: E402
import spslib  # noqa: E402

RBXTOOL = os.environ.get("RBXTOOL", "/tmp/claude-0/-home-user-shittyclaude/de3978ba-38c5-504e-80ab-5b405ce568f9/"
                                    "scratchpad/rbxtool/target/release/rbxtool")


def main(out, fbx=True, areas=None):
    os.makedirs(out, exist_ok=True)
    sc = build.build(areas=areas)
    rep = checks.run(sc)
    checks.show(rep)
    if rep["problems"]:
        raise SystemExit("CHECKS FAILED:\n  " + "\n  ".join(rep["problems"][:40]))
    spslib.to_json(sc, os.path.join(out, "potato.json"))
    clips, folder = RA.bake_all(sc)
    ap = os.path.join(out, "RootAnimations.json")
    with open(ap, "w") as f:
        json.dump([folder], f)
    if os.path.exists(RBXTOOL):
        subprocess.run([RBXTOOL, "build", ap, os.path.join(out, "RootAnimations.rbxm")], check=True)
    json.dump({"counts": rep["counts"], "meshes": len(sc.geoms),
               "mesh_tris": {k: g.tris() for k, g in sc.geoms.items()}}, open(os.path.join(out, "stats.json"), "w"),
              indent=1)
    if fbx:
        try:
            import spsblend as SB
        except ImportError:
            print("no Blender here: skipped the FBX")
            return sc
        SB.reset()
        SB.export_fbx(sc, os.path.join(out, "StealAPotato.fbx"), axis="SAP_Axis")
    return sc


if __name__ == "__main__":
    args = sys.argv[1:]
    areas = None
    for a in args:
        if a.startswith("--areas="):
            areas = [int(x) for x in a[8:].split(",")]
    main(args[0], fbx="--no-fbx" not in args, areas=areas)
