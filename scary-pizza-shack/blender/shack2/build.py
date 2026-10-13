"""Assemble the remade shack map.

    python -m shack2.build <outdir>          (from blender/)

Pass 1 (blockout): new shell, terrain, road, forest and horizon; the stations are batch 1's,
recoloured to a blockout grey (they keep every marker and moving part) until pass 3
rebuilds them one by one."""
import copy
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

import numpy as np  # noqa: E402

import spslib  # noqa: E402
from spsgeo import CF  # noqa: E402

from . import forest, layout as L, props_in, props_insides, props_out, shell, terrain  # noqa: E402,F401
from .kit import Kit  # noqa: E402

BLOCKOUT_GREY = (176, 176, 172)


def _copy_tree(src, dst_parent, dst_sc, src_sc, recolor=None, keep=lambda n: True):
    """Deep-copy a node subtree from another Scene (geometry, welds and joints remapped)."""
    mapping = {}

    def rec(n, parent):
        if not keep(n):
            return
        p = dict(n.p)
        node = spslib.Node(n.kind, n.name, parent, **p)
        mapping[n] = node
        if n.kind == "MeshPart":
            name = p["mesh"]
            if name not in dst_sc.geoms:
                dst_sc.geoms[name] = src_sc.geoms[name]
                dst_sc.geom_info[name] = dict(src_sc.geom_info[name])
        if recolor and n.kind in ("Part", "MeshPart") and n.p.get("material") != "Neon":
            node.p["color"] = recolor
        if n.kind in ("Part", "MeshPart") and node.p.get("material") == "Metal":
            node.p["material"] = "SmoothPlastic"
        for c in n.children:
            rec(c, node)
    rec(src, dst_parent)
    for old, new in mapping.items():
        for key in ("part0", "part1", "primary"):
            if key in new.p and new.p[key] is not None:
                new.p[key] = mapping.get(new.p[key], new.p[key])
    return mapping.get(src)


def old_stations(sc, old, skip=()):
    """Batch 1's stations not rebuilt yet (and the Markers folder) in blockout grey; no Lights."""
    st = sc.folder(sc.root, "Stations")
    shift = {"BusStop": (L.BUS_STOP_X[0] - 37.0, 0.0, 0.0)}
    for m in old.root.get("Stations").children:
        if m.name in skip:
            continue
        new = _copy_tree(m, st, sc, old, recolor=BLOCKOUT_GREY, keep=lambda n: n.kind != "Light")
        if m.name in shift:
            d = np.array(shift[m.name])
            for n in new.walk():
                for key in ("cf",):
                    if key in n.p and n.p[key] is not None:
                        n.p[key] = CF(n.p[key].p + d, n.p[key].R)
                if n.kind == "Motor":
                    n.p["hinge"] = CF(n.p["hinge"].p + d, n.p["hinge"].R)
    mk = sc.folder(sc.root, "Markers")
    for m in old.root.get("Markers").children:
        _copy_tree(m, mk, sc, old)
    return old


def road_markers(sc):
    """Car path along the near (north) lane, driving west, from the east bend's far end to the
    west bend's far end; Car_Start, Car_Stop and Car_End are among them."""
    mk = sc.root.get("Markers")
    for name in ("Car_Start", "Car_Stop", "Car_End"):
        n = mk.find(name)
        if n is not None:
            mk.children.remove(n)
    pts = terrain.centre_line()[::-1]                 # east -> west
    lane = terrain.offset_line(terrain.centre_line(), -5.0)[::-1]
    path = lane[::4]
    names = []
    stop_i = min(range(len(path)), key=lambda i: abs(path[i][0]) + abs(path[i][1] - (L.ROAD_Z - 5)))
    for i, (x, z) in enumerate(path):
        j = min(i + 1, len(path) - 1)
        dx, dz = path[j][0] - x, path[j][1] - z
        if i == len(path) - 1:
            dx, dz = x - path[i - 1][0], z - path[i - 1][1]
        R = spslib.G.facing(np.array((dx, 0.0, dz)) / (math.hypot(dx, dz) or 1))
        nm = "Car_Path%d" % (i + 1)
        sc.marker(mk, nm, CF((x, L.ROAD_TOP, z), R))
        names.append(nm)
        if i == 0:
            sc.marker(mk, "Car_Start", CF((x, L.ROAD_TOP, z), R))
        if i == stop_i:
            sc.marker(mk, "Car_Stop", CF((x, L.ROAD_TOP, z), R))
        if i == len(path) - 1:
            sc.marker(mk, "Car_End", CF((x, L.ROAD_TOP, z), R))
    return names


SPAWNS = ((-10.6, 0.6), (-9.0, 1.9), (-7.4, 0.6), (-5.8, 1.9))     # the middle aisle, west of the inspector's circle


def inside_markers(sc):
    """PlayerSpawn1..4 on the open floor between the north and south stands, each looking at
    the serving window (as batch 1)."""
    mk = sc.root.get("Markers")
    for i, (x, z) in enumerate(SPAWNS):
        nm = "PlayerSpawn%d" % (i + 1)
        n = mk.find(nm)
        if n is not None:
            mk.children.remove(n)
        d = np.array((0.0 - x, 0.0, L.IN_Z1 - z))
        sc.marker(mk, nm, CF((x, L.FLOOR, z), spslib.G.facing(d / np.linalg.norm(d))))


def outside_markers(sc):
    """Markers that moved with the remade outside: the bus stop's spawn (the shelter moved
    east past the lot) and the road ends (the road now bends away into the trees)."""
    mk = sc.root.get("Markers")

    def put(name, pos, look):
        n = mk.find(name)
        if n is not None:
            mk.children.remove(n)
        d = np.array((look[0], 0.0, look[1]), float)
        sc.marker(mk, name, CF(pos, spslib.G.facing(d / np.linalg.norm(d))))
    put("Spawn_BusStop", (53.0, sc.kit_ground.y(53.0, 22.4), 22.4), (-1.0, 0.0))

    # (the Cam_ markers are set with their cameras: st_out2.cameras)
    # walkers come along the north verge from where the road leaves the trees at both ends
    put("Spawn_RoadWest", (-92.0, sc.kit_ground.y(-92.0, 22.0), 22.0), (1.0, 0.0))
    put("Spawn_RoadEast", (92.0, sc.kit_ground.y(92.0, 14.0), 14.0), (-1.0, 0.1))
    # batch-1 markers that stand on the ground keep their X and Z and step onto the new ground
    # (the land north of the yard and in the forest rises a plate or two)
    gr = sc.kit_ground
    for name in ("Truck_Stop", "Spawn_ForestSouth", "Spawn_ForestNorth") + tuple("TreeLine%d" % i for i in range(1, 7)):
        n = mk.find(name)
        if n is not None:
            q = n.p["cf"].p
            n.p["cf"] = CF((q[0], gr.y(q[0], q[2]), q[2]), n.p["cf"].R)
    # Queue3 stays 4 behind Queue2, up on the road's gravel shoulder; the forest spawn south of
    # the road moves 2 east, off a step in the ground
    n = mk.find("Queue3")
    if n is not None:
        n.p["cf"] = CF((0.0, gr.y(0.0, 21.5), 21.5), n.p["cf"].R)
    n = mk.find("Spawn_ForestSouth")
    if n is not None:
        n.p["cf"] = CF((-6.0, gr.y(-6.0, 69.0), 69.0), n.p["cf"].R)
    # Queue1 stands where ServingWindow.Customer does: a whole body clear of the ledge
    n = mk.find("Queue1")
    if n is not None:
        q = n.p["cf"].p
        n.p["cf"] = CF((q[0], q[1], L.QUEUE_Z + 0.85), n.p["cf"].R)
    # the Watcher's spot outside the side window moves out with the widened west wall
    n = mk.find("Watcher_Window")
    if n is not None:
        q = n.p["cf"].p
        x = q[0] - L.WIDEN
        n.p["cf"] = CF((x, gr.y(x, q[2]), q[2]), n.p["cf"].R)
    # the yard's drop spot stays where it was, down on the new yard ground
    n = mk.find("Delivery_Drop")
    if n is not None:
        q = n.p["cf"].p
        y = spslib.surface_under(sc, (q[0], q[1] + 0.3, q[2]), depth=1.0)
        if y is not None:
            n.p["cf"] = CF((q[0], y, q[2]), n.p["cf"].R)


# things within reach that are not floor, wall, a counter's body or a blocker: no collision
# (fittings, things on counters, inside cabinets, on the walls); everything else that
# collides is a body you walk round
NO_COLLIDE = ("CCTVDesk/Phone/", "CCTVDesk/Radio/", "CCTVDesk/Monitor", "CCTVDesk/SwitchBox/", "DoughStation/Board",
              "DrinksCooler/Shelf", "Extinguisher/Cradle", "Fridge/Shelf", "Fridge/Deck", "FuseBox/Lever", "FuseBox/Box",
              "Hatch/Door/", "PeelRack/Arm", "PeelRack/Backboard", "PeelRack/FloorRail", "PlushieShelf/",
              "Register/DisplayCase", "Register/TillBase", "Register/TillTop", "Register/Drawer/",
              "RulesBoard/Cleat", "RulesBoard/Frame", "ServingWindow/TicketPrinter/", "ServingWindow/TicketRail/",
              "ServingWindow/LedgeBracket", "ShutterButton/", "BoxStation/StickerShelf", "Stations/Bin/",
              "Dressing/SideWindow/Sill", "Oven/Door1/", "Oven/Door2/")


def clear_undergrowth(sc):
    """The undergrowth is scattered before the site is built: drop any piece that ends up in
    something built (a lamp's base, a culvert's wall) rather than nudging the scatter."""
    from . import checks as K
    und = sc.root.get("Outside").get("Forest").get("Undergrowth")
    if und is None:
        return 0
    b = K.Boxes(sc)
    own = {}
    for m in und.children:
        for n in m.walk():
            own[id(n)] = m
    drop = set()
    for i, n in enumerate(b.nodes):
        m = own.get(id(n))
        if m is None or m in drop:
            continue
        for j in b.query(b.lo[i], b.hi[i]):
            o = b.nodes[j]
            if id(o) in own or "/Forest/" in o.path() or o.name in ("Ground", "Path", "Meadow", "Bank", "FarBank",
                                                                      "Verge", "Ruts"):
                continue
            if K.sat_depth(b.C[i], b.R[i], b.H[i], b.C[j], b.R[j], b.H[j]) > 0.02:
                drop.add(m)
                break
    for m in drop:
        und.children.remove(m)
    return len(drop)


def no_collide(sc):
    n_off = 0
    for n in sc.nodes(("Part", "MeshPart")):
        if n.p.get("collide") and any(s in n.path() for s in NO_COLLIDE):
            n.p["collide"] = False
            n_off += 1
    return n_off


def build(items=False, seed=2026):
    import scene_build
    sc = spslib.Scene()
    for name in ("Shack", "Outside", "Stations", "Items", "Markers"):
        sc.folder(sc.root, name)
    k = Kit(sc)
    rng = np.random.default_rng(seed)
    old = scene_build.build(items=False)
    shell.build(k, sc.root, rng)
    out = sc.root.get("Outside")
    terrain.build(k, out, rng)
    # the forest draws from its own stream, so changes inside the shack never move a tree
    forest.build(k, out, np.random.default_rng(seed + 101))
    from . import outkit
    gr = outkit.Ground(sc)
    sc.kit_ground = gr
    from . import st_ceiling, st_east, st_north, st_out, st_out2, st_south, st_west
    built = {m.name for mod in (st_north, st_east, st_south, st_west, st_ceiling) for m in mod.build(k)}
    built |= {m.name for m in st_out.build(k, old, gr)}
    built |= {m.name for m in st_out2.build(k, gr)}
    from . import dressing
    dressing.build(k)
    from . import counters
    counters.finish(k)              # the cupboard doors and drawers, hinged away from the Stands, and filled
    from . import ext_shack, road_dress, site
    ext_shack.build(k, sc)
    site.build(k, sc)
    road_dress.build(k, sc)
    old_stations(sc, old, skip=built)
    road_markers(sc)
    inside_markers(sc)
    outside_markers(sc)
    st_out2.cameras(k, sc)
    no_collide(sc)
    clear_undergrowth(sc)
    from . import papa
    papa.build(k, sc)               # Papa Stud's places outside, his walk, the truck's path
    if items:
        from . import items2
        items2.build_items(k)
    sc.kit = k
    return sc


def report(sc):
    cnt = spslib.part_counts(sc)
    print("parts by folder:", dict(cnt), "total", sum(cnt.values()))
    print("meshes:", len(sc.geoms))
    lights = sum(1 for _ in sc.nodes("Light"))
    print("Light objects:", lights)
    print("prop models used: inside %d, outside %d" % (len(sc.kit.used["inside"]), len(sc.kit.used["outside"])))


if __name__ == "__main__":
    s = build()
    report(s)
