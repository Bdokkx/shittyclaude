"""Build the Scary Pizza Shack batch-1 map: scene -> checks -> map.json -> FBX.

    python blender/build_map.py <outdir>

Writes <outdir>/map.json (everything the Studio script rebuilds) and
<outdir>/ScaryPizzaShack_Batch1.fbx (one white mesh per Model__Part, plus the
FV_Axis marker cubes). Fails loudly if a check does not pass.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import scene_build  # noqa: E402
import spslib  # noqa: E402

BUDGET_SHELL, BUDGET_MAP = 900, 7000


def main(outdir):
    os.makedirs(outdir, exist_ok=True)
    sc = scene_build.build()
    cnt, bad, zf = scene_build.report(sc)
    over_p, over_i, per_item = spslib.mesh_budget(sc)
    total = sum(cnt.values())
    problems = []
    if cnt["Shack"] > BUDGET_SHELL:
        problems.append("shack shell has %d parts (> %d)" % (cnt["Shack"], BUDGET_SHELL))
    if total > BUDGET_MAP:
        problems.append("map has %d parts (> %d)" % (total, BUDGET_MAP))
    if bad:
        problems.append("%d parts off the brick grid" % len(bad))
    if zf:
        problems.append("%d z-fighting faces" % len(zf))
    if over_p or over_i:
        problems.append("mesh budget: %s %s" % (over_p, over_i))
    # every mesh name must be unique even after the build script's loose matching
    seen = {}
    for name in sc.geoms:
        k = "".join(ch for ch in name.lower() if ch.isalnum())
        if k in seen:
            problems.append("mesh names %s and %s collide" % (seen[k], name))
        seen[k] = name
    ok, badm = spslib.check_item_markers(sc)
    print("item markers exactly on their surface:", ok)
    if badm:
        problems.append("item markers off their surface: %s" % badm)
    required = ["Queue1", "Queue2", "Queue3", "Spawn_RoadWest", "Spawn_RoadEast", "Spawn_BusStop",
                "Spawn_ForestSouth", "Spawn_ForestNorth", "Cam_Front", "Cam_Back", "Cam_Yard", "Cam_Road",
                "Car_Start", "Car_Stop", "Car_End", "Truck_Stop", "Delivery_Drop", "Inspector_Rise"] + \
               ["Inspection_Stand%d" % k for k in range(1, 5)] + ["PlayerSpawn%d" % k for k in range(1, 5)] + \
               ["Watcher_Window"] + ["TreeLine%d" % k for k in range(1, 7)]
    have = [n.name for n in sc.root.get("Markers").children]
    for r in required:
        if have.count(r) != 1:
            problems.append("marker %s x%d" % (r, have.count(r)))
    for n in sc.nodes("Marker"):
        if tuple(n.p["size"]) != (1.0, 1.0, 1.0):
            problems.append("marker %s size" % n.path())
    stations = {m.name: m for m in sc.root.get("Stations").children}
    need = {"BackDoor": ["Stand"], "Fridge": ["Stand"] + ["Slot%d" % k for k in range(1, 9)],
            "DoughStation": ["Stand", "Work"], "SauceStation": ["Stand", "WorkSauce", "WorkCheese"],
            "ChopStation": ["Stand", "Work"], "ToppingRail": ["Stand", "Work"] + ["Tub%d" % k for k in range(1, 7)],
            "Sink": ["Stand"], "Oven": ["Stand", "Slot1", "Slot2"], "PeelRack": ["Stand"], "CutTable": ["Stand", "Work"],
            "BoxStation": ["Stand", "Work"], "Register": ["Stand"], "RulesBoard": ["Stand"],
            "PlushieShelf": ["Stand"] + ["Slot%d" % k for k in range(1, 5)],
            "ServingWindow": ["Stand", "Handover", "Customer"], "ShutterButton": ["Stand"], "CCTVDesk": ["Stand"],
            "StorageShelf": ["Stand"] + ["Slot%d" % k for k in range(1, 7)],
            "DrinksCooler": ["Stand"] + ["Slot%d" % k for k in range(1, 13)], "FuseBox": ["Stand"],
            "CeilingLamp1": ["Stand"], "CeilingLamp2": ["Stand"], "Hatch": ["Stand"], "Generator": ["Stand"],
            "Dumpster": ["Stand"], "YardGate": ["Stand"], "StreetLamp": ["Stand"], "YardLamp": ["Stand"],
            "BusStop": ["Stand"], "RoadSign": ["Stand"], "Bin": ["Stand"]}
    for st, marks in need.items():
        if st not in stations:
            problems.append("station %s missing" % st)
            continue
        names = [c.name for c in stations[st].children if c.kind == "Marker"]
        for mk_ in marks:
            if names.count(mk_) != 1:
                problems.append("%s.%s x%d" % (st, mk_, names.count(mk_)))
    tr = stations["ServingWindow"].find("TicketRail")
    if tr is None or sorted(c.name for c in tr.children if c.kind == "Marker") != ["Ticket%d" % k for k in range(1, 6)]:
        problems.append("TicketRail markers")
    if problems:
        raise SystemExit("CHECKS FAILED: " + "; ".join(problems))
    spslib.to_json(sc, os.path.join(outdir, "map.json"))
    meta = {"parts": dict(cnt), "total": total, "meshes": len(sc.geoms),
            "mesh_tris": {k: g.tris() for k, g in sc.geoms.items()}, "item_tris": per_item}
    json.dump(meta, open(os.path.join(outdir, "stats.json"), "w"), indent=1)
    try:
        import spsblend as SB
    except ImportError:
        print("no Blender here: skipped the FBX")
        return sc
    SB.reset()
    SB.export_fbx(sc, os.path.join(outdir, "ScaryPizzaShack_Batch1.fbx"))
    return sc


if __name__ == "__main__":
    main(sys.argv[1])
