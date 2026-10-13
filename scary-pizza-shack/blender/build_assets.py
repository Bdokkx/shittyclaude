"""Build Scary Pizza Shack batch 2 (characters, vehicles, plushies, uniforms):
scene -> checks -> assets.json -> FBX.

    python blender/build_assets.py <outdir>

Writes <outdir>/assets.json (what BuildPizzaShackAssets.lua rebuilds) and
<outdir>/ScaryPizzaShack_Batch2.fbx (one white mesh per Model__Part plus the PSA_Axis
marker cubes). Fails loudly if a check does not pass.

Everything goes into one folder, Workspace.PizzaShackAssets, laid out in a row 120 studs
under the map (out of the way until you move it to ReplicatedStorage.Assets).
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import numpy as np  # noqa: E402

import assets_chars as AC  # noqa: E402
import assets_common  # noqa: E402
import assets_kit as AK  # noqa: E402
import assets_papa as PAPA  # noqa: E402
import assets_plush as AP  # noqa: E402
import assets_r6 as R6  # noqa: E402
import assets_uniforms as AU  # noqa: E402
import assets_vehicles as AV  # noqa: E402
import spslib  # noqa: E402
from spsgeo import CF  # noqa: E402

Y0 = -120.0
MODELS = ["CustomerKit", "Passenger", "Watcher", "PapaStud", "InspectorCar", "DeliveryTruck", "Van", "Plushies",
          "Uniforms"]              # V3: PapaStud replaces the Inspector; the InspectorHole is retired
AXIS = "PSA_Axis"


def build():
    assets_common.MOVING.clear()
    sc = spslib.Scene("PizzaShackAssets")
    root = sc.root
    kit = sc.model(root, "CustomerKit")
    for k, name in enumerate(AK.ORDER):
        x, z = -110.0 + (k % 11) * 4.0, -8.0 + (k // 11) * 6.0
        AK.place(sc, kit, name, CF((x, Y0 + 4.0, z)))
    AC.passenger(sc, root, CF((-60.0, Y0 + 3.0, 0.0)))
    AC.watcher(sc, root, CF((-50.0, Y0, 0.0)))
    PAPA.papa_stud(sc, root, CF((-34.0, Y0, 0.0)))
    AV.inspector_car(sc, root, CF((0.0, Y0, 0.0)))
    AV.delivery_truck(sc, root, CF((20.0, Y0, 0.0)))
    AV.van(sc, root, CF((40.0, Y0, 0.0)))
    AP.plushies(sc, root, CF((56.0, Y0, 0.0)), spacing=2.5)
    AU.uniforms(sc, root, CF((78.0, Y0 + 3.0, 0.0)), spacing=4.0)
    return sc


def check(sc, batch1_json=None):
    problems = []
    root = sc.root
    names = [c.name for c in root.children]
    if names != MODELS:
        problems.append("top level is %s" % names)
    M = {c.name: c for c in root.children}

    def need(model, path, kind=None, count=1):
        hits = [n for n in model.walk() if n.name == path and (kind is None or n.kind == kind)]
        if len(hits) != count:
            problems.append("%s: %s x%d (want %d)" % (model.name, path, len(hits), count))
        return hits

    # -- R6 rigs: names, joints in Part0, standard joint frames
    for rig in ("Watcher", "PapaStud"):
        m = M[rig]
        for pn in R6.PARTS:
            need(m, pn, "Part")
        for jn, p0, p1, _ in R6.Body().joints():
            hits = need(m, jn, "Motor")
            if hits and (hits[0].parent.name != p0 or hits[0].p["part1"].name != p1):
                problems.append("%s.%s wired wrong" % (rig, jn))
        if m.p.get("primary") is None or m.p["primary"].name != "HumanoidRootPart":
            problems.append("%s PrimaryPart" % rig)
        need(m, "Humanoid", "Humanoid", 1 if rig == "Watcher" else 0)
        for n in m.walk():
            if n.kind in ("Part", "MeshPart") and n.p["anchored"] != (n.name == "HumanoidRootPart"):
                problems.append("%s.%s anchored=%s" % (rig, n.name, n.p["anchored"]))
    need(M["Watcher"], "Eye", "Part", 2)
    papa = M["PapaStud"]
    for pn in ("Mask", "MaskCrust", "MaskEyes", "MaskPupils", "MaskGrin", "MaskCheeks", "MaskPepperoni", "Hood",
               "HatBand", "HatPuff", "Neckerchief", "Apron", "LeftGlove", "RightGlove", "PeelHandle", "PeelBlade"):
        need(papa, pn)
    soles = min(n.p["cf"].p[1] for n in papa.walk() if n.name in ("Left Leg", "Right Leg")) - 1.7
    hrp = papa.find("HumanoidRootPart").p["cf"].p[1]
    arm = papa.find("Right Arm").p["size"]
    if abs(hrp - soles - 5.1) > 1e-6 or abs(arm[1] - 4.25) > 1e-6:
        problems.append("PapaStud: HRP %.3f above the soles, arm %.2f long" % (hrp - soles, arm[1]))
    for n in papa.walk():
        if n.name in ("PeelHandle", "PeelBlade"):
            if not any(c.kind == "Weld" and c.p["part0"].name == "Right Arm" for c in n.children):
                problems.append("PapaStud.%s not welded to the right arm" % n.name)
    # -- Passenger, hole
    need(M["Passenger"], "Eye", "Part", 2)
    need(M["Passenger"], "Handle", "Part")
    # -- vehicles
    for vn, wheels in (("InspectorCar", 4), ("DeliveryTruck", 6), ("Van", 4)):
        m = M[vn]
        if m.p.get("primary") is None or m.p["primary"].name != "Base":
            problems.append("%s PrimaryPart" % vn)
        need(m, "Wheel", "Part", wheels)
        need(m, "Headlight", "Part", 2)
        need(m, "TailLight", "Part", 2)
        for n in m.walk():
            if n.name == "Wheel" and (n.p["shape"] != "Cylinder" or n.p.get("pivot") is not None):
                problems.append("%s Wheel not a plain cylinder on its axle" % vn)
    need(M["InspectorCar"], "Beacon", "Part")
    for pn in ("SideL", "SideR"):
        need(M["DeliveryTruck"], pn, "Part")
        need(M["Van"], pn, "Part")
    need(M["DeliveryTruck"], "RearDoor")
    van = M["Van"]
    for pn in ("DoorL", "DoorR", "Zone", "Gate", "Sign"):
        need(van, pn, "Part")
    for pn, ang in (("DoorL", -135), ("DoorR", 135)):
        d = van.find(pn)
        if d is None or d.p["attrs"].get("OpenAngle") != ang or d.p.get("pivot") is None:
            problems.append("Van.%s OpenAngle/pivot" % pn)
    lamp = van.find("VanLamp")
    if lamp is None or lamp.kind != "Model" or lamp.find("Bulb") is None:
        problems.append("Van.VanLamp.Bulb")
    vo = np.array((40.0, Y0, 0.0))
    zone = van.find("Zone")
    zs, zc = np.array(zone.p["size"]), zone.p["cf"].p - vo
    floor_top = zc[1] - zs[1] / 2
    if zs[0] < 7.6 - 1e-6 or zs[1] < 8.2 - 1e-6 or zs[2] < 11 - 1e-6 or abs(floor_top - 1.6) > 1e-6:
        problems.append("Van inside %s, floor %.2f" % (zs, floor_top))
    # -- plushies, uniforms
    pl = M["Plushies"]
    if [c.name for c in pl.children] != ["Watchdog", "LuckyCat", "LittleInspector", "NightOwl", "MedicBear",
                                        "SleepySloth", "PiggyBank"]:
        problems.append("Plushies children")
    for c in pl.children:
        lo = min(n.p["cf"].p[1] - n.p["size"][1] / 2 for n in c.walk() if n.kind == "MeshPart")
        hi = max(n.p["cf"].p[1] + n.p["size"][1] / 2 for n in c.walk() if n.kind == "MeshPart")
        if not 1.1 <= hi - lo <= 1.5:
            problems.append("%s is %.2f tall" % (c.name, hi - lo))
        if c.p.get("primary") is None or c.p["primary"].name != "Body":
            problems.append("%s PrimaryPart" % c.name)
    for pn in ("Watchdog", "NightOwl"):
        need(pl.find(pn), "Neck", "Motor")
        need(pl.find(pn), "Head", "MeshPart")
    un = M["Uniforms"]
    for name in AU.ORDER:
        acc = [n for n in un.walk() if n.name == name and n.kind == "Accessory"]
        if len(acc) != 1 or acc[0].kind != "Accessory":
            problems.append("Uniforms.%s" % name)
            continue
        h = acc[0].find("Handle")
        att = AU.UNIFORMS[name][0]
        if h is None or h.find(att) is None:
            problems.append("Uniforms.%s Handle/%s" % (name, att))
    # -- kit
    for name in AK.ORDER:
        m = kit_m = M["CustomerKit"].find(name)
        if m is None or m.p.get("primary") is None or m.p["primary"].name != "Handle":
            problems.append("CustomerKit.%s" % name)
            continue
        if AK.KIT[name][0] == "Hair":
            tris = sum(sc.geoms[n.p["mesh"]].tris() for n in kit_m.walk() if n.kind == "MeshPart")
            if not 30 <= tris <= 120:
                problems.append("hair %s has %d triangles" % (name, tris))
    # -- exactly one part named Handle in every kit piece, accessory and the Passenger
    holders = [M["Passenger"]] + list(M["CustomerKit"].children) + \
        [n for n in M["Uniforms"].walk() if n.kind == "Accessory"]
    for m in holders:
        hs = [n for n in m.walk() if n.name == "Handle"]
        if len(hs) != 1:
            problems.append("%s has %d parts named Handle" % (m.path(), len(hs)))
    # -- grid, z-fighting, budgets, names
    bad = spslib.check_grid(sc)
    if bad:
        problems.append("%d parts off the brick grid: %s" % (len(bad), bad[:5]))
    zf = spslib.zfight(sc)
    if zf:
        problems.append("%d z-fighting faces: %s" % (len(zf), zf[:5]))
    over = [(k, g.tris()) for k, g in sc.geoms.items() if g.tris() >= 1500]
    if over:
        problems.append("meshes over 1500 triangles: %s" % over)
    seen = {}
    if batch1_json and os.path.exists(batch1_json):
        for k in json.load(open(batch1_json))["meshes"]:
            seen["".join(ch for ch in k.lower() if ch.isalnum())] = "batch 1 " + k
    for k in sc.geoms:
        key = "".join(ch for ch in k.lower() if ch.isalnum())
        if key in seen:
            problems.append("mesh names %s and %s collide" % (seen[key], k))
        seen[key] = k
        if key.startswith(AXIS.lower().replace("_", "")):
            problems.append("mesh %s looks like an axis cube" % k)
    for n in sc.nodes():
        if "~" in n.name:
            problems.append("name with ~: %s" % n.path())
    return problems


def main(outdir):
    os.makedirs(outdir, exist_ok=True)
    sc = build()
    cnt = spslib.part_counts(sc)
    total = sum(cnt.values())
    print("parts by model:", dict(cnt), "total", total)
    print("meshes:", len(sc.geoms), "largest:", max((g.tris(), k) for k, g in sc.geoms.items()))
    problems = check(sc, os.path.join(outdir, "map.json"))
    if problems:
        raise SystemExit("CHECKS FAILED:\n  " + "\n  ".join(problems))
    print("checks: all passed (names, rigs, heights, vehicles, van contract, plushies, accessories, grid, "
          "z-fighting, budgets, mesh names)")
    spslib.to_json(sc, os.path.join(outdir, "assets.json"))
    meta = {"parts": dict(cnt), "total": total, "meshes": len(sc.geoms),
            "mesh_tris": {k: g.tris() for k, g in sc.geoms.items()},
            "moving": [list(x) for x in assets_common.MOVING]}
    json.dump(meta, open(os.path.join(outdir, "assets_stats.json"), "w"), indent=1)
    try:
        import spsblend as SB
    except ImportError:
        print("no Blender here: skipped the FBX")
        return sc
    SB.reset()
    SB.export_fbx(sc, os.path.join(outdir, "ScaryPizzaShack_Batch2.fbx"), axis=AXIS)
    return sc


if __name__ == "__main__":
    main(sys.argv[1])
