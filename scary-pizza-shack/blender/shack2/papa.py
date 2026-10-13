"""Where Papa Stud stands outside: the Papa_ markers, each found by searching its area for a
spot where a 9-stud figure fits (between the trunks, clear of everything built) and from
whose head height (8 up) there is a clear line to at least one of the places a player
looks out from: the serving window, the side window, the back door, the yard, the cameras.

Also the walk round the shack (Papa_Walk1..N) and the truck's lane (Truck_Path1..N)."""
import math

import numpy as np

import spsgeo as G
from spsgeo import CF

from . import layout as L

BODY = np.array((2.5, 4.6, 1.5))          # half extents of a 9-stud figure, arms in
HEAD = 8.0
SEE_THROUGH = ("Glass", "Window", "Fence", "Mesh", "Gate", "Wire", "Blocker", "PlayerBlock", "Chain", "Cable",
               "Tuft", "Fern", "Leaf", "Litter", "Puddle", "Rut", "Stain", "Cracks", "Weeds", "Moth", "Glow",
               "Bulb", "Board", "Tape", "BayLines", "EdgeLine", "CentreLine")
GROUNDY = ("Ground", "Path", "Meadow", "Bank", "FarBank", "Verge", "Ruts", "Slab", "LotAsphalt", "YardGround",
           "Shoulder", "Asphalt", "Apron", "Pad", "Paver", "Walk", "Gravel", "Kerb", "Patch", "DitchBed")


def viewpoints(sc):
    """The places a player looks out from: name -> eye position."""
    vp = {"ServingWindow": np.array((0.0, 6.0, 9.4)), "ServingWindowL": np.array((-3.5, 6.0, 9.4)),
          "ServingWindowR": np.array((3.5, 6.0, 9.4)),
          "SideWindow": np.array((L.IN_X0 + 0.6, 5.8, (L.SIDE_Z0 + L.SIDE_Z1) / 2)),
          "BackDoor": np.array(((L.DOOR_X0 + L.DOOR_X1) / 2, 5.0, L.OUT_Z0 - 2.0)),
          "Yard": np.array((0.0, 5.0, -30.0))}
    mk = sc.root.get("Markers")
    for n in mk.children:
        if n.name.startswith("Cam_"):
            vp[n.name] = np.asarray(n.p["cf"].p, float)
    return vp


class Space:
    """The built scene as boxes, for fitting a body and testing lines of sight."""

    def __init__(self, sc):
        from . import checks as K
        self.K = K
        self.b = K.Boxes(sc, keep=lambda n: n.p["transparency"] < 0.3)
        self.solid_sight = np.array([not any(s in n.name or s in (n.parent.name if n.parent else "")
                                             for s in SEE_THROUGH) for n in self.b.nodes])
        self.groundy = np.array([n.name in GROUNDY for n in self.b.nodes])
        low = ("Weeds", "Tuft", "Fern", "Litter", "Puddle", "Stones", "Rut", "Stain", "Cracks")
        self.under = np.array(["/Undergrowth/" in n.path() or any(s in n.path() for s in low) for n in self.b.nodes])

    def fits(self, p, R, half=BODY, lift=0.4):
        """A body standing at p (looking along R's -Z) touches nothing but ground and low plants."""
        C = p + R @ np.array((0.0, half[1] + lift, 0.0))
        ext = np.abs(R) @ half
        for i in self.b.query(C - ext, C + ext):
            if self.groundy[i] or self.under[i]:
                continue
            if self.K.sat_depth(self.b.C[i], self.b.R[i], self.b.H[i], C, R, half) > 0.05:
                return False
        return True

    def blocked(self, p0, p1, skip_end=1.5):
        """The first solid box the segment p0 -> p1 passes through (None: a clear line)."""
        d = p1 - p0
        ln = float(np.linalg.norm(d))
        if ln < 1e-6:
            return None
        steps = max(1, int(ln / 6.0) + 1)
        seen = set()
        for s in range(steps):
            a = p0 + d * (s / steps)
            c = p0 + d * ((s + 1) / steps)
            lo, hi = np.minimum(a, c) - 0.1, np.maximum(a, c) + 0.1
            for i in self.b.query(lo, hi):
                if i in seen or not self.solid_sight[i]:
                    continue
                seen.add(i)
                if self._hits(i, p0, d, ln, skip_end):
                    return self.b.nodes[i]
        return None

    def _hits(self, i, p0, d, ln, skip_end):
        R, C, H = self.b.R[i], self.b.C[i], self.b.H[i] - 0.05
        if np.any(H <= 0):
            return False
        o = R.T @ (p0 - C)
        v = R.T @ d
        t0, t1 = 0.0, 1.0
        for k in range(3):
            if abs(v[k]) < 1e-9:
                if abs(o[k]) > H[k]:
                    return False
                continue
            a, b = (-H[k] - o[k]) / v[k], (H[k] - o[k]) / v[k]
            if a > b:
                a, b = b, a
            t0, t1 = max(t0, a), min(t1, b)
            if t0 > t1:
                return False
        # ignore what the line only touches right at its ends (the window's own frame, the feet)
        e = skip_end / ln
        return t1 > e and t0 < 1.0 - e

    def sees(self, p, vps):
        """The viewpoints with a clear line to the head over p."""
        head = p + np.array((0.0, HEAD, 0.0))
        return [name for name, v in vps.items() if self.blocked(head, v) is None]


def facing(p, target):
    d = np.array((target[0] - p[0], 0.0, target[2] - p[2]))
    n = np.linalg.norm(d)
    return G.facing(d / n if n > 1e-6 else np.array((0.0, 0.0, 1.0)))


def ring(r0, r1, az0, az1, n_r=5, n_az=24):
    """Candidate (x, z) points on a ring segment (azimuth from +Z towards +X, degrees)."""
    out = []
    for r in np.linspace(r0, r1, n_r):
        for az in np.linspace(az0, az1, n_az):
            a = math.radians(az)
            out.append((r * math.sin(a), r * math.cos(a)))
    return out


def place(sc, gr, space, vps, name, cands, want, target=(0.0, 0.0, 0.0), half=BODY, y=None, need_fit=True):
    """The first candidate where the body fits and one of `want` (viewpoint names) sees it."""
    best = None
    for (x, z) in cands:
        yy = gr.y(x, z) if y is None else y
        p = np.array((x, yy, z))
        R = facing(p, target)
        if need_fit and not space.fits(p, R, half):
            continue
        seen = space.sees(p, {k: vps[k] for k in want if k in vps})
        if seen:
            return p, R, seen
        if best is None:
            best = (p, R, [])
    return best if best is not None else (None, None, [])


def build(k, sc):
    """Place every Papa_ marker, the walk and the truck's path (in Markers)."""
    gr = sc.kit_ground
    mk = sc.root.get("Markers")
    space = Space(sc)
    vps = viewpoints(sc)
    report = {}

    def put(name, p, R, seen, attrs=None):
        if p is None:
            report[name] = (None, "no spot where the body fits")
            return
        old = mk.find(name)
        if old is not None:
            mk.children.remove(old)
        m = sc.marker(mk, name, CF(p, R))
        k.attr(m, "SeenFrom", ",".join(seen) if seen else "")
        for a, v in (attrs or {}).items():
            k.attr(m, a, v)
        report[name] = (np.round(p, 1).tolist(), seen)

    win = ["ServingWindow", "ServingWindowL", "ServingWindowR"]
    cams = [n for n in vps if n.startswith("Cam_")]
    # far out: the silhouettes (the meadow across the road, up the truck's lane, the west)
    deep = [("Papa_Deep1", ring(90, 130, 4, 20), win + ["Cam_Back"]),
            ("Papa_Deep2", ring(90, 130, 24, 50), win + ["Cam_Back", "Cam_Road"]),
            ("Papa_Deep3", [(10.0 + dx, z) for z in np.arange(-100.0, -131.0, -5.0) for dx in (0.0, -3.0, 3.0)],
             ["Yard", "BackDoor", "Cam_Yard"]),
            ("Papa_Deep4", ring(90, 130, -110, -60), ["SideWindow", "BackDoor", "Yard"] + cams)]
    for name, cands, want in deep:
        p, R, seen = place(sc, gr, space, vps, name, cands, want)
        put(name, p, R, seen)
    # in the trees, 45..70 out
    trees = [("Papa_Trees1", ring(45, 70, -100, -75), ["SideWindow"] + cams),
             ("Papa_Trees2", ring(45, 70, -175, -110, 6, 60), ["BackDoor", "Yard", "Cam_Yard"]),
             ("Papa_Trees3", ring(45, 70, -30, -5), win + ["Cam_Back"]),
             ("Papa_Trees4", ring(45, 70, 60, 100), win + cams)]
    def in_woods(c):                                # outside the yard's fence and off the lane
        x, z = c
        yard = L.YARD_X[0] - 3.0 < x < L.YARD_X[1] + 3.0 and L.YARD_Z[0] - 3.0 < z < L.YARD_Z[1] + 3.0
        lane = L.TRUCK_LANE[0] - 1.0 < x < L.TRUCK_LANE[1] + 1.0 and z < L.TRUCK_LANE[3] + 2.0
        return not yard and not lane
    for name, cands, want in trees:
        p, R, seen = place(sc, gr, space, vps, name, [c for c in cands if in_woods(c)], want)
        put(name, p, R, seen)
    # across the road: one at the verge, one under the far street lamp
    road_z = L.ROAD_Z + 13.0
    p, R, seen = place(sc, gr, space, vps, "Papa_Road1",
                       [(x, road_z + dz) for x in (14.0, 10.0, 18.0, 6.0, 22.0) for dz in (0.0, 1.5, -1.0)], win + cams)
    put("Papa_Road1", p, R, seen)
    p, R, seen = place(sc, gr, space, vps, "Papa_Road2",
                       [(-14.0 + dx, 43.0 + dz) for dz in (0.0, -0.5, 0.5, -1.0) for dx in (0.0, -1.0, 1.0, -2.0, 2.0)],
                       win + cams)
    put("Papa_Road2", p, R, seen, {"Light": "RoadLamp3"})
    # the bus stop: standing at the shelter's end, and sitting on its seat
    from .st_out2 import BX0, BX1, BZ0
    p, R, seen = place(sc, gr, space, vps, "Papa_BusStop",
                       [(BX0 - 4.5 - dx, 21.6 + dz) for dx in (0.0, 0.5, 1.0) for dz in (0.0, 1.0, -0.6)] +
                       [(BX1 + 4.3 + dx, 21.6 + dz) for dx in (0.0, 0.5) for dz in (0.0, 1.0)], win + cams)
    put("Papa_BusStop", p, R, seen)
    seat_y = gr.y((BX0 + BX1) / 2, 23.2) + 1.6 + 0.1
    ps = np.array(((BX0 + BX1) / 2, seat_y, BZ0 + 0.9))
    put("Papa_BusStopSit", ps, G.facing((0.0, 0.0, 1.0)), space.sees(ps, vps), {"Pose": "Sit"})
    # the forecourt, 15 from the window, staring in
    wt = (0.0, 5.5, L.OUT_Z1)
    for name, cands in (("Papa_Forecourt1", [(-12.5 - d, 20.5) for d in (0.0, 0.5, 1.0)] +
                         [(-4.5 - d, 24.0) for d in (0.0, 0.5)]),
                        ("Papa_Forecourt2", [(8.0 + d, 22.6) for d in (0.0, 0.5, 1.0, 1.5)])):
        p, R, seen = place(sc, gr, space, vps, name, cands, win, target=wt)
        put(name, p, R, seen)
    # at the side window, at the back door, in the yard (half behind the dumpster's far end
    # between it and the fence, and at the gate)
    sw = (L.OUT_X0, 5.5, (L.SIDE_Z0 + L.SIDE_Z1) / 2)
    p, R, seen = place(sc, gr, space, vps, "Papa_SideWindow",
                       [(L.OUT_X0 - 4.0 - d, (L.SIDE_Z0 + L.SIDE_Z1) / 2) for d in (0.0, 0.5, 1.0)], ["SideWindow"],
                       target=sw)
    put("Papa_SideWindow", p, R, seen)
    bd = ((L.DOOR_X0 + L.DOOR_X1) / 2, 4.0, L.OUT_Z0)
    p, R, seen = place(sc, gr, space, vps, "Papa_BackDoor",
                       [(bd[0], L.OUT_Z0 - 5.0 - d) for d in (0.0, 0.5, 1.0, 1.5)], ["BackDoor", "Cam_Yard", "Yard"],
                       target=bd)
    put("Papa_BackDoor", p, R, seen)
    p, R, seen = place(sc, gr, space, vps, "Papa_Yard1",
                       [(24.0 + dx, -26.5 + dz) for dz in (0.0, 0.5, -0.3, 1.0) for dx in (0.0, -0.2)],
                       ["Yard", "Cam_Yard", "BackDoor"])
    put("Papa_Yard1", p, R, seen)
    gx = (L.GATE_X[0] + L.GATE_X[1]) / 2
    p, R, seen = place(sc, gr, space, vps, "Papa_Yard2", [(gx, L.YARD_Z[0] + 3.5 + d) for d in (0.0, 0.5, 1.0)],
                       ["Yard", "Cam_Yard", "BackDoor"])
    put("Papa_Yard2", p, R, seen)
    # on the roof, crouched beside the sign's east end, looking down at the forecourt
    crouch = np.array((2.5, 3.1, 1.6))
    p, R, seen = place(sc, gr, space, vps, "Papa_Roof",
                       [(13.6 + dx, L.OUT_Z1 - 3.5 + dz) for dx in (0.0, 0.5, -0.5) for dz in (0.0, -1.0, 1.0)],
                       win + cams + ["Yard"], target=(0.0, 0.0, 40.0), half=crouch, y=L.ROOF_TOP)
    put("Papa_Roof", p, R, seen, {"Pose": "Crouch"})
    # the walk round the shack (a loop: along the front, down the west side past the side
    # window, through the yard past the back door and the gate, out by the east side), found on
    # a grid of the spots his body fits and straightened into legs that are clear all the way
    walk = walk_points(space, gr)
    for i, (x, z) in enumerate(walk):
        nx, nz = walk[(i + 1) % len(walk)]
        p = np.array((x, gr.y(x, z), z))
        put("Papa_Walk%d" % (i + 1), p, facing(p, (nx, 0.0, nz)), [])
    # the truck's path up the lane; the last place is where it stops (Truck_Stop): nose 3 short of the gate
    stop_z = L.YARD_Z[0] + 0.4 - 3.0 - L.TRUCK_NOSE
    zs = list(np.arange(L.TRUCK_LANE[2] + 2.0, stop_z, 12.0)) + [stop_z]
    tx = (L.TRUCK_LANE[0] + L.TRUCK_LANE[1]) / 2
    for i, z in enumerate(zs):
        p = np.array((tx, gr.y(tx, z), z))
        put("Truck_Path%d" % (i + 1), p, G.facing((0.0, 0.0, 1.0)), [])
    put("Truck_Stop", np.array((tx, gr.y(tx, stop_z), stop_z)), G.facing((0.0, 0.0, 1.0)), [])
    old = mk.find("Inspector_Rise")                 # retired with the InspectorHole
    if old is not None:
        mk.children.remove(old)
    sc.papa_report = report
    return report


WALK_VIA = [(0.0, 23.5), (-26.0, 20.0), (-26.5, -4.0), (-25.0, -24.0), (-5.0, -38.0), (10.0, -42.0),
            (22.5, -22.0), (22.5, 0.0), (16.0, 22.5)]      # clockwise from the forecourt's middle
WALK_BOX = (-36.0, 36.0, -50.0, 30.0)
WALK_CELL = 0.5


def _walk_free(space, gr):
    """Grid of cells (x, z) where the body fits facing along X and along Z."""
    x0, x1, z0, z1 = WALK_BOX
    xs = np.arange(x0, x1 + 1e-6, WALK_CELL)
    zs = np.arange(z0, z1 + 1e-6, WALK_CELL)
    free = np.zeros((len(xs), len(zs)), bool)
    Rz, Rx = G.facing((0.0, 0.0, 1.0)), G.facing((1.0, 0.0, 0.0))
    for i, x in enumerate(xs):
        for j, z in enumerate(zs):
            p = np.array((x, gr.y(x, z), z))
            free[i, j] = space.fits(p, Rz) and space.fits(p, Rx)
    return xs, zs, free


def _astar(free, a, b):
    import heapq
    nx, nz = free.shape
    steps = [(1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0),
             (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (-1, -1, 1.414)]
    h = lambda c: math.hypot(c[0] - b[0], c[1] - b[1])
    best = {a: 0.0}
    came = {}
    q = [(h(a), 0.0, a)]
    while q:
        _, g, c = heapq.heappop(q)
        if c == b:
            out = [c]
            while c in came:
                c = came[c]
                out.append(c)
            return out[::-1]
        if g > best.get(c, 1e18):
            continue
        for (di, dj, w) in steps:
            n = (c[0] + di, c[1] + dj)
            if not (0 <= n[0] < nx and 0 <= n[1] < nz) or not free[n]:
                continue
            if di and dj and not (free[c[0] + di, c[1]] and free[c[0], c[1] + dj]):
                continue
            g2 = g + w
            if g2 < best.get(n, 1e18):
                best[n] = g2
                came[n] = c
                heapq.heappush(q, (g2 + h(n), g2, n))
    return None


def leg_clear(space, gr, a, b, step=0.5):
    """His body clear all along the straight leg a -> b ((x, z) points), facing along it."""
    a, b = np.array((a[0], 0.0, a[1])), np.array((b[0], 0.0, b[1]))
    n = max(1, int(np.linalg.norm(b - a) / step))
    R = facing(a, b)
    for s in range(n + 1):
        q = a + (b - a) * (s / n)
        q[1] = gr.y(q[0], q[2])
        if not space.fits(q, R):
            return False
    return True


def walk_points(space, gr):
    """The loop round the shack through WALK_VIA, as few straight legs as stay clear."""
    xs, zs, free = _walk_free(space, gr)
    fi, fj = np.nonzero(free)

    def cell(p):                                    # the nearest free cell to a via point
        d = (xs[fi] - p[0]) ** 2 + (zs[fj] - p[1]) ** 2
        m = int(np.argmin(d))
        assert d[m] < 36.0, ("walk via point blocked", p)
        return int(fi[m]), int(fj[m])
    vias = [cell(p) for p in WALK_VIA]
    path = []
    for i, ca in enumerate(vias):
        cb = vias[(i + 1) % len(vias)]
        a, b = WALK_VIA[i], WALK_VIA[(i + 1) % len(vias)]
        seg = _astar(free, ca, cb)
        assert seg is not None, ("no way round", a, b)
        path += [(float(xs[c[0]]), float(zs[c[1]])) for c in seg[:-1]]
    # straighten: from each kept point, the farthest point along the path reachable in a clear line
    out = [path[0]]
    i = 0
    n = len(path)
    while i < n:
        j = min(i + 1, n)
        for k_ in range(min(n, i + 120), i + 1, -1):
            if leg_clear(space, gr, path[i], path[k_ % n]):
                j = k_
                break
        if j >= n:
            break
        out.append(path[j])
        i = j
    return [(round(x, 1), round(z, 1)) for (x, z) in out]


CROUCH = np.array((2.5, 3.1, 1.6))


def check(sc):
    """Problems with Papa's places, his walk and the truck's lane (empty: all good)."""
    out = []
    mk = sc.root.get("Markers")
    space = Space(sc)
    gr = sc.kit_ground
    need = (["Papa_Deep%d" % i for i in range(1, 5)] + ["Papa_Trees%d" % i for i in range(1, 5)] +
            ["Papa_Road1", "Papa_Road2", "Papa_BusStop", "Papa_BusStopSit", "Papa_Forecourt1", "Papa_Forecourt2",
             "Papa_SideWindow", "Papa_BackDoor", "Papa_Yard1", "Papa_Yard2", "Papa_Roof", "Papa_Camp",
             "Truck_Stop"])
    for name in need:
        if mk.find(name) is None:
            out.append(("missing", name))
    for m in mk.children:
        n = m.name
        if not n.startswith("Papa_") or n.startswith("Papa_Walk") or n in ("Papa_Camp", "Papa_CarDoor"):
            continue
        a = m.p.get("attrs") or {}
        cf_ = m.p["cf"]
        p, R = np.asarray(cf_.p, float), np.asarray(cf_.R, float)
        if a.get("Pose") != "Sit":
            if not space.fits(p, R, CROUCH if a.get("Pose") == "Crouch" else BODY):
                out.append(("body does not fit", n))
        if not a.get("SeenFrom"):
            out.append(("seen from nowhere", n))
    # the walk: his body clear all the way round
    walk = sorted([m for m in mk.children if m.name.startswith("Papa_Walk")], key=lambda m: int(m.name[9:]))
    if len(walk) < 3:
        out.append(("walk", "fewer than 3 points"))
    for i, m in enumerate(walk):
        a = np.asarray(m.p["cf"].p, float)
        b = np.asarray(walk[(i + 1) % len(walk)].p["cf"].p, float)
        if not leg_clear(space, gr, (a[0], a[2]), (b[0], b[2])):
            out.append(("walk blocked", m.name))
    # the truck's lane: 14 wide, 13 of headroom, from its far end to the gate
    x0, x1, z0, z1 = L.TRUCK_LANE
    for z in np.arange(z0, z1 - 0.6, 4.0):
        za, zb = z, min(z + 4.0, z1 - 0.6)
        y = max(gr.y(x, zz) for x in (x0, (x0 + x1) / 2, x1) for zz in (za, zb))
        lo, hi = np.array((x0, y + 0.5, za)), np.array((x1, y + L.TRUCK_HEAD, zb))
        C, H = (lo + hi) / 2, (hi - lo) / 2
        for i in space.b.query(lo, hi):
            if space.groundy[i] or space.under[i]:
                continue
            if space.K.sat_depth(space.b.C[i], space.b.R[i], space.b.H[i], C, np.eye(3), H) > 0.05:
                out.append(("in the truck's lane", space.b.nodes[i].path().replace("PizzaShack/", ""), round(za)))
    return out


def standins(sc):
    """Review renders only: a block figure at every Papa_ place (chef's whites, dark legs, the
    pale mask, the tall hat), so the renders show where he stands and how much of him shows."""
    k = sc.kit
    f = sc.folder(sc.root, "PapaStandIns")
    for m in sc.root.get("Markers").children:
        n = m.name
        if not n.startswith("Papa_") or n in ("Papa_Camp", "Papa_CarDoor"):
            continue
        pose = (m.p.get("attrs") or {}).get("Pose")
        cf_ = m.p["cf"]
        if n.startswith("Papa_Walk"):
            k.part(f, "WalkPost", (0.6, 2.0, 0.6), cf_ * CF((0.0, 1.0, 0.0)), "pepperoni")
            continue
        legs = 1.2 if pose in ("Sit", "Crouch") else 3.4
        y = 0.0
        if pose != "Sit":
            k.part(f, "Legs", (3.0, legs, 1.6), cf_ * CF((0.0, legs / 2, 0.0)), "charcoal")
            y = legs
        else:
            k.part(f, "Legs", (3.0, 1.0, 3.0), cf_ * CF((0.0, 0.5, -1.0)), "charcoal")
        k.part(f, "Torso", (3.4, 3.4, 1.7), cf_ * CF((0.0, y + 1.7, 0.0)), "white")
        k.part(f, "Arms", (6.4, 3.0, 1.4), cf_ * CF((0.0, y + 1.9, 0.0)), "white")
        k.part(f, "Mask", (4.2, 3.0, 0.4), cf_ * CF((0.0, y + 4.9, -0.9)), "crust")
        k.part(f, "Eyes", (2.6, 0.6, 0.2), cf_ * CF((0.0, y + 5.4, -1.15)), "white", material="Neon")
        k.part(f, "Hat", (2.4, 2.2, 2.0), cf_ * CF((0.0, y + 7.4, 0.0)), "white")
