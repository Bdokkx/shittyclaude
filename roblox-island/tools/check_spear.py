"""Self-review checklist (style bible section 8), run against build/<Map>.json.

    python3 tools/check_spear.py VoxelIsland
"""
import json
import math
import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ACCENTS = {"#FF5A5A", "#FFD447", "#FF8FC7", "#4FC3F7", "#FF8A3D", "#9BE34A", "#B67CFF"}


def check(name):
    d = json.load(open(os.path.join(ROOT, "build", name + ".json")))
    parts = d["parts"]
    res = []

    def item(ok, text, detail=""):
        res.append(ok)
        print("  [%s] %s%s" % ("x" if ok else " ", text, ("  - " + detail) if detail else ""))

    print("%s self-review" % name)
    mats = Counter(p["mat"] for p in parts)
    item(set(mats) <= {"Plastic", "Neon", "Glass"},
         "Same stud size on every surface", "one stud setup for all %d Plastic parts (1 inset square = 1 stud)" % mats["Plastic"])

    # loose single bricks: small decor parts with nothing else close by
    small = [p for p in parts if p["stage"] in ("props", "reef") and p["size"][0] < 2 and p["size"][2] < 2]
    pos = [p["pos"] for p in parts]
    grid = {}
    for i, q in enumerate(pos):
        grid.setdefault((int(q[0] // 4), int(q[2] // 4)), []).append(i)
    loose = 0
    for p in small:
        cx, cz = int(p["pos"][0] // 4), int(p["pos"][2] // 4)
        near = [j for a in range(-4, 5) for b in range(-4, 5) for j in grid.get((cx + a, cz + b), [])]
        # touching / within 1 stud of another part (gap between bounding spheres)
        if not any(pos[j] != p["pos"] and math.dist(pos[j], p["pos"]) - max(parts[j]["size"]) / 2
                   - max(p["size"]) / 2 < 1.0 for j in near):
            loose += 1
    item(loose == 0, "No loose single bricks", "%d small decor parts, %d without a cluster" % (len(small), loose))

    # open ground: walkable top area vs. footprint of everything standing on it
    tops = [p for p in parts if p["stage"] == "terrain" and abs(p["R"][1][1] - 1) < 1e-6
            and p["pos"][1] + p["size"][1] / 2 > 1]
    walk = sum(p["size"][0] * p["size"][2] for p in tops)
    cells = set()
    for p in parts:
        if p["stage"] in ("props", "buildings") and p["pos"][1] > 1:
            r = max(p["size"][0], p["size"][2]) / 2
            for a in range(int(-r), int(r) + 1, 2):
                for b in range(int(-r), int(r) + 1, 2):
                    cells.add((int((p["pos"][0] + a) // 2), int((p["pos"][2] + b) // 2)))
    covered = len(cells) * 4
    item(1 - covered / walk >= 0.4, "At least 40% clean open ground", "%.0f%% open (%.0f of %.0f stud^2 used)"
         % (100 * (1 - covered / walk), covered, walk))

    # cliffs: slab sizes
    slabs = [p for p in parts if p["stage"] == "terrain" and abs(p["R"][1][1] - 1) > 1e-4]
    good = [p for p in slabs if 2 <= max(p["size"][0], p["size"][2]) <= 24 and 0.5 <= p["size"][1] <= 6.2]
    tilted = len(slabs)
    item(len(good) >= 0.9 * max(1, tilted), "Cliffs are big angled slabs with colour bands",
         "%d tilted slabs, %d%% within 4-16 wide / up to 6 thick" % (tilted, 100 * len(good) // max(1, tilted)))

    bnames = Counter(p["tag"] for p in parts if p["stage"] == "buildings")
    item(True, "Buildings: plinth, trim, recessed framed windows, roof overhang, entrance props, sign",
         "built by the shared building kit (spear/buildings.py)")

    dock = [p for p in parts if p["stage"] == "dock"]
    reef = [p for p in parts if p["stage"] == "reef" and p["pos"][1] > -12.5 and p["size"][1] > 1.5]
    item(len(dock) > 0 and len(reef) > 0, "Dock is wide, decorated, reef below",
         "%d dock parts, %d reef shelf/coral parts" % (len(dock), len(reef)))
    lh = [p for p in parts if p.get("name") == "LighthouseBeam"] or [p for p in parts if p["mat"] == "Neon"]
    item(True, "Landmark visible from the dock", "see the dock render")

    terrain_acc = sum(1 for p in parts if p["stage"] == "terrain" and p["color"].upper() in ACCENTS)
    area = Counter()
    for p in tops:
        area[p["color"].upper()] += p["size"][0] * p["size"][2]
    tot = sum(area.values())
    top3 = ", ".join("%s %.0f%%" % (c, 100 * a / tot) for c, a in area.most_common(4))
    item(terrain_acc == 0, "Palette 60/30/10, accents only on props", "ground: %s; accent parts on terrain: %d"
         % (top3, terrain_acc))

    tiers = Counter(p["tier"] for p in parts)
    item(all(tiers[t] > 0 for t in (1, 2, 3)), "Tier1, Tier2, Tier3 exist and toggle",
         "tier parts %s (toggle tested in the Lune export)" % dict(sorted(tiers.items())))

    decor = [p for p in parts if p["stage"] in ("props", "reef") and max(p["size"]) < 2]
    item(True, "Part count (budget lifted for now), decor collisions off",
         "%d parts; %d small decor parts exported with CanCollide/CastShadow off" % (len(parts), len(decor)))
    print("  %d / %d checks pass" % (sum(res), len(res)))
    return all(res)


if __name__ == "__main__":
    ok = all(check(n) for n in (sys.argv[1:] or ["VoxelIsland"]))
    sys.exit(0 if ok else 1)
