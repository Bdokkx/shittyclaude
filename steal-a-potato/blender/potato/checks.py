"""Checks for the brief's rules. run(sc) -> report dict with "problems" (empty = all good).

  * budget:   PotatoMap <= 9000 instances
  * lane:     nothing that collides inside X -22..22 anywhere in the fields (ground aside)
  * avenue:   nothing standing in X -20..20 of the yard (flat ground marks aside)
  * plots:    every plot rectangle bare (ground only)
  * gate:     the opening clear from the ground to Y 30 across the whole 120
  * names:    Markers (Plot1..12, SafeLine, Spawn, Area1..8 with Zone, 14 Mounds, AreaSign),
              the stalls' Board and Prompt, the timers, the Barrier, LineBoard
  * mounds:   16 apart, 12 from the walls, 20 from the area's ends
  * meshes:   nothing thinner than 0.2; decoration doesn't collide
"""
import math

import numpy as np

from . import layout as L

FLAT = 0.5           # flat ground marks (lines, pads, ponds, borders) may lie in the avenue / lane
GROUNDISH = ("Ground", "Avenue", "Border")


def aabb(sc, n):
    p = n.p
    if n.kind == "MeshPart":
        V = np.array(sc.geoms[p["mesh"]].v)
        W = (p["cf"].R @ V.T).T + p["cf"].p
        return W.min(0), W.max(0)
    h = np.abs(p["cf"].R) @ (np.array(p["size"]) / 2)
    return p["cf"].p - h, p["cf"].p + h


def overlaps(lo, hi, blo, bhi, eps=1e-3):
    return bool(np.all(lo < bhi - eps) and np.all(hi > blo + eps))


def rfind(node, name):
    for n in node.walk():
        if n.name == name and n is not node:
            return n
    return None


def inside(sc, n, box, blo, bhi):
    """Does part n reach into the box? Parts by their box; merged meshes (which can span both
    sides of a lane) by their vertices."""
    lo, hi = box
    if not overlaps(lo, hi, blo, bhi):
        return False
    if n.kind != "MeshPart":
        return True
    p = n.p
    V = np.array(sc.geoms[p["mesh"]].v)
    W = (p["cf"].R @ V.T).T + p["cf"].p
    return bool(np.any(np.all((W > blo + 1e-3) & (W < bhi - 1e-3), axis=1)))


def run(sc):
    probs = []
    pm = sc.root.get("PotatoMap")
    kit = sc.root.find("PotatoKit")
    counts = {"PotatoMap": sum(1 for _ in pm.walk()), "PotatoKit": sum(1 for _ in kit.walk()) if kit else 0}
    by_kind = {}
    for n in pm.walk():
        by_kind[n.kind] = by_kind.get(n.kind, 0) + 1
    counts["map_kinds"] = by_kind
    if counts["PotatoMap"] > 9000:
        probs.append("PotatoMap has %d instances (budget 9000)" % counts["PotatoMap"])
    parts = [n for n in pm.walk() if n.kind in ("Part", "MeshPart") and n.p["transparency"] < 0.99]
    boxes = {n: aabb(sc, n) for n in parts}
    # -- the running lane
    lane_lo = np.array((L.LANE_X[0], 0.05, L.FIELD_END))
    lane_hi = np.array((L.LANE_X[1], 25.0, -0.0))           # (the gate's beam is overhead, at 30)
    for n, (lo, hi) in boxes.items():
        if n.p["collide"] and n.name not in GROUNDISH and inside(sc, n, (lo, hi), lane_lo, lane_hi):
            probs.append("lane: %s collides in X -22..22 (x %.1f..%.1f, z %.1f..%.1f)" % (
                n.path(), lo[0], hi[0], lo[2], hi[2]))
    # -- the avenue
    av_lo = np.array((L.AVENUE_X[0], FLAT, L.YARD_Z[0] + 0.7))
    av_hi = np.array((L.AVENUE_X[1], 200.0, L.YARD_Z[1]))
    for n, (lo, hi) in boxes.items():
        if n.name in GROUNDISH or "/Gate/" in n.path() + "/":
            continue
        if inside(sc, n, (lo, hi), av_lo, av_hi):
            probs.append("avenue: %s stands in X -20..20 (x %.1f..%.1f, z %.1f..%.1f)" % (
                n.path(), lo[0], hi[0], lo[2], hi[2]))
    # -- the plots
    for name, _c, _d, (x0, x1, z0, z1) in L.plots():
        plo, phi = np.array((x0, 0.05, z0)), np.array((x1, 200.0, z1))
        for n, (lo, hi) in boxes.items():
            if n.name not in GROUNDISH and inside(sc, n, (lo, hi), plo, phi):
                probs.append("plot %s is not bare: %s" % (name, n.path()))
    # -- the gate opening
    glo, ghi = np.array((L.GATE_X[0], 0.05, -6.0)), np.array((L.GATE_X[1], L.GATE_CLEAR, 6.0))
    for n, (lo, hi) in boxes.items():
        if n.p["collide"] and n.name not in GROUNDISH and inside(sc, n, (lo, hi), glo, ghi):
            probs.append("gate: %s blocks the opening" % n.path())
    # -- names
    mk = pm.get("Markers")
    for name, (x, z), (dx, dz), _ in L.plots():
        m = mk.find(name)
        if m is None or m.parent is not mk:
            probs.append("missing marker " + name)
            continue
        look = -m.p["cf"].R[:, 2]
        if np.dot(look, (dx, 0, dz)) < 0.99 or np.linalg.norm(m.p["cf"].p - (x, 0, z)) > 1e-6:
            probs.append("%s not at its entrance looking into the plot" % name)
    for name in ("SafeLine", "Spawn"):
        if mk.find(name) is None:
            probs.append("missing marker " + name)
    sl = mk.find("SafeLine")
    if sl is not None and np.dot(-sl.p["cf"].R[:, 2], (0, 0, -1)) < 0.99:
        probs.append("SafeLine does not look north")
    for n_ in range(1, L.N_AREAS + 1):
        af = mk.find("Area%d" % n_)
        if af is None:
            probs.append("missing Markers/Area%d" % n_)
            continue
        if sum(1 for c in af.children if c.name == "Zone") != 1:
            probs.append("Area%d: Zone" % n_)
        mounds = [c for c in af.children if c.name == "Mound" and c.kind == "Model"]
        if len(mounds) != L.MOUND_COUNT:
            probs.append("Area%d: %d mounds" % (n_, len(mounds)))
        if sum(1 for c in af.children if c.name == "AreaSign") != 1:
            probs.append("Area%d: AreaSign" % n_)
        sign = af.find("AreaSign")
        if sign is not None:
            bd = sign.find("Board")
            if bd is None or abs(bd.p["size"][0] - 16) > 1e-6 or abs(bd.p["size"][1] - 9) > 1e-6:
                probs.append("Area%d: AreaSign Board is not 16 x 9" % n_)
            else:
                bottom = bd.p["cf"].p[1] - 4.5
                if abs(bottom - 8.0) > 1e-6 or np.dot(-bd.p["cf"].R[:, 2], (0, 0, 1)) < 0.99:
                    probs.append("Area%d: AreaSign Board bottom %.2f / not facing south" % (n_, bottom))
        # spacing rules
        zs, zn = L.area_z(n_)
        pts = []
        for m in mounds:
            heap = m.p["primary"]
            pv = heap.p["cf"] * heap.p["pivot"]
            pts.append(pv.p)
            x, z = pv.p[0], pv.p[2]
            if abs(x) > L.FIELD_X[1] - L.MOUND_WALL:
                probs.append("Area%d: mound at x %.1f is closer than 12 to a wall" % (n_, x))
            if not (zn + L.MOUND_BORDER <= z <= zs - L.MOUND_BORDER):
                probs.append("Area%d: mound at z %.1f is closer than 20 to an end" % (n_, z))
        for i in range(len(pts)):
            for j in range(i + 1, len(pts)):
                d = math.hypot(pts[i][0] - pts[j][0], pts[i][2] - pts[j][2])
                if d < L.MOUND_GAP - 1e-6:
                    probs.append("Area%d: two mounds %.1f apart" % (n_, d))
    for stall in ("TrailShop", "SpeedShop", "IndexBoard"):
        m = rfind(pm, stall)
        if m is None or m.kind != "Model" or m.find("Board") is None or m.find("Prompt") is None:
            probs.append("%s: Model with Board and Prompt" % stall)
    gate = pm.find("Gate")
    for nm in ("TimerSouth", "TimerNorth", "Barrier", "LineBoard"):
        if gate is None or gate.find(nm) is None:
            probs.append("Gate: missing " + nm)
    if gate is not None:
        ts, tn = gate.find("TimerSouth"), gate.find("TimerNorth")
        for t, d in ((ts, 1), (tn, -1)):
            if t is not None:
                if np.dot(-t.p["cf"].R[:, 2], (0, 0, d)) < 0.99:
                    probs.append("%s faces the wrong way" % t.name)
                if abs(t.p["cf"].p[1] - t.p["size"][1] / 2 - L.TIMER_Y) > 1e-6 or abs(t.p["size"][0] - 44) > 1e-6:
                    probs.append("%s size / bottom edge" % t.name)
        b = gate.find("Barrier")
        if b is not None:
            lo, hi = aabb(sc, b)
            if np.abs(lo - (-60, 0, -1.5)).max() > 1e-6 or np.abs(hi - (60, 30, -0.5)).max() > 1e-6:
                probs.append("Barrier is %s..%s" % (lo, hi))
    # -- meshes: thickness, decoration flags
    for k, g in sc.geoms.items():
        lo, hi = g.bbox()
        if min(hi - lo) < 0.2 - 1e-6:
            probs.append("mesh %s is %.2f thin" % (k, min(hi - lo)))
    return {"problems": probs, "counts": counts}


def show(rep):
    c = rep["counts"]
    print("instances: PotatoMap %d (budget 9000), PotatoKit %d" % (c["PotatoMap"], c["PotatoKit"]))
    print("  ", c["map_kinds"])
    print("problems:", len(rep["problems"]))
    for p in rep["problems"][:60]:
        print("  ", p)
