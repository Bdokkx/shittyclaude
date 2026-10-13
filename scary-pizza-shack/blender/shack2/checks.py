"""The remake's checks (brief sections 4, 7 and 9), run on a built Scene.

    python -m shack2.checks [quick]          (from blender/; builds the map and prints the report)

  planes      no unbroken single-colour plane larger than 6 x 6 inside or 12 x 12 outside
  floating    every visible part touches something that leads down to the ground
  pierce      nothing passes right through anything (a part crossing another's whole thickness)
  clear       a clear box 3 wide and 3 high in front of every item marker towards its Stand,
              and room to stand at every Stand
  ceiling     rays straight up from all over the room hit the ceiling (closed everywhere)
  window      the PlayerBlock fills the serving window
  horizon     no world edge can be seen: something stands above it in every direction
  contract    every batch-1 station, marker and moving part is still there under its name
  props       80+ different prop models inside, 50+ outside
  lights      no Light objects; every lamp is a Model with a Bulb and Lamp* attributes
  budget      parts inside <= 6000, outside <= 12000
"""
import math
import sys
from collections import defaultdict

import numpy as np

import spslib
from spsgeo import CF  # noqa: F401

from . import layout as L

ROOM = (L.IN_X0, L.IN_X1, 0.4, 9.4, -10.0, 10.0)   # the room's air (X0, X1, Y0, Y1, Z0, Z1)
SHACK = (L.OUT_X0 - 0.6, 18.6, -1.0, 16.0, -11.6, 11.6)   # the building, walls and roof included


def in_room(p, pad=0.0):
    x0, x1, y0, y1, z0, z1 = ROOM
    return x0 - pad <= p[0] <= x1 + pad and y0 - pad <= p[1] <= y1 + pad and z0 - pad <= p[2] <= z1 + pad


def in_shack(p):
    x0, x1, y0, y1, z0, z1 = SHACK
    return x0 <= p[0] <= x1 and y0 <= p[1] <= y1 and z0 <= p[2] <= z1


def where(n):
    """'inside' or 'outside', by where the part's centre is."""
    return "inside" if in_shack(n.p["cf"].p) else "outside"


# ---------------------------------------------------------------- oriented boxes

MAX_PIECES = 48
_PIECES = {}


def _pieces(sc, mesh_name):
    """(centre, half size) in mesh space of each connected piece of a mesh, or None when it
    is one piece or too many to be worth it."""
    if mesh_name in _PIECES:
        return _PIECES[mesh_name]
    g = sc.geoms[mesh_name]
    V = np.asarray(g.v, float)
    parent = np.arange(len(V))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for f in g.f:
        r0 = find(f[0])
        for v in f[1:]:
            r = find(v)
            if r != r0:
                parent[r] = r0
    roots = np.array([find(i) for i in range(len(V))])
    keys = np.unique(roots)
    out = None
    if 1 < len(keys) <= MAX_PIECES:
        out = []
        for key in keys:
            P = V[roots == key]
            lo, hi = P.min(0), P.max(0)
            out.append(((lo + hi) / 2, np.maximum((hi - lo) / 2, 0.01)))
    _PIECES[mesh_name] = out
    return out


class Boxes:
    """Every visible Part / MeshPart as an oriented box (centre, axes as columns, half sizes)."""

    def __init__(self, sc, keep=lambda n: True, max_transp=0.99, split=True):
        """split: a MeshPart made of separate pieces (three downpipes, a row of posts) gives
        one box per piece instead of one box round all of them (up to MAX_PIECES)."""
        nodes, C, R, H = [], [], [], []
        for n in sc.nodes(("Part", "MeshPart")):
            p = n.p
            if p["transparency"] >= max_transp or not keep(n):
                continue
            pieces = _pieces(sc, p["mesh"]) if (split and n.kind == "MeshPart") else None
            if pieces:
                for (c, h) in pieces:
                    nodes.append(n)
                    C.append(p["cf"].p + p["cf"].R @ c)
                    R.append(p["cf"].R)
                    H.append(h)
                continue
            nodes.append(n)
            C.append(p["cf"].p)
            R.append(p["cf"].R)
            H.append(np.asarray(p["size"], float) / 2)
        self.sc = sc
        self.nodes = nodes
        self.index = {n: i for i, n in enumerate(nodes)}
        self.C = np.array(C, float).reshape(-1, 3)
        self.R = np.array(R, float).reshape(-1, 3, 3)
        self.H = np.array(H, float).reshape(-1, 3)
        ext = np.einsum("nij,nj->ni", np.abs(self.R), self.H)
        self.lo, self.hi = self.C - ext, self.C + ext
        self._grid = None

    def grid(self, cell=6.0):
        if self._grid is None:
            g = defaultdict(list)
            a = np.floor(self.lo / cell).astype(int)
            b = np.floor(self.hi / cell).astype(int)
            for i in range(len(self.nodes)):
                for x in range(a[i, 0], b[i, 0] + 1):
                    for y in range(a[i, 1], b[i, 1] + 1):
                        for z in range(a[i, 2], b[i, 2] + 1):
                            g[(x, y, z)].append(i)
            self._grid = (cell, g)
        return self._grid

    def pairs(self, eps=0.06):
        """Index pairs whose world AABBs overlap (grown by eps)."""
        cell, g = self.grid()
        out = set()
        lo, hi = self.lo - eps, self.hi + eps
        for lst in g.values():
            if len(lst) < 2:
                continue
            arr = np.array(lst)
            L0, H0 = lo[arr], hi[arr]
            ov = np.all((L0[:, None, :] <= H0[None, :, :]) & (L0[None, :, :] <= H0[:, None, :]), -1)
            ii, jj = np.nonzero(np.triu(ov, 1))
            for a, b in zip(arr[ii], arr[jj]):
                out.add((a, b) if a < b else (b, a))
        if not out:
            return np.zeros((0, 2), int)
        return np.array(sorted(out))

    def query(self, lo, hi):
        """Indices of boxes whose AABB overlaps the world box lo..hi."""
        cell, g = self.grid()
        a = np.floor(np.asarray(lo) / cell).astype(int)
        b = np.floor(np.asarray(hi) / cell).astype(int)
        cand = set()
        for x in range(a[0], b[0] + 1):
            for y in range(a[1], b[1] + 1):
                for z in range(a[2], b[2] + 1):
                    cand.update(g.get((x, y, z), ()))
        lo, hi = np.asarray(lo), np.asarray(hi)
        return [i for i in cand if np.all(self.lo[i] <= hi) and np.all(lo <= self.hi[i])]

    def overlap(self, I, J, eps=0.0):
        """Separating-axis test for pairs: returns the smallest overlap depth over the 15 axes
        (negative = apart by that much)."""
        Ca, Cb, Ra, Rb, Ha, Hb = self.C[I], self.C[J], self.R[I], self.R[J], self.H[I], self.H[J]
        T = Cb - Ca
        best = np.full(len(I), np.inf)
        axes = [Ra[:, :, k] for k in range(3)] + [Rb[:, :, k] for k in range(3)]
        for i in range(3):
            for j in range(3):
                c = np.cross(Ra[:, :, i], Rb[:, :, j])
                nrm = np.linalg.norm(c, axis=1)
                ok = nrm > 1e-6
                c[ok] /= nrm[ok, None]
                c[~ok] = Ra[~ok, :, i]
                axes.append(c)
        for ax in axes:
            ra = np.einsum("nk,nk->n", np.abs(np.einsum("nij,ni->nj", Ra, ax)), Ha)
            rb = np.einsum("nk,nk->n", np.abs(np.einsum("nij,ni->nj", Rb, ax)), Hb)
            d = np.abs(np.einsum("ni,ni->n", T, ax))
            best = np.minimum(best, ra + rb - d)
        return best + eps

    def corners(self, i):
        s = np.array([[sx, sy, sz] for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)], float)
        return self.C[i] + (s * self.H[i]) @ self.R[i].T


# ---------------------------------------------------------------- floating

GROUNDED = ("/Outside/Ground/", "/Outside/Road/", "/Outside/RoadSide/", "/Outside/Forecourt/", "/Outside/Lot/",
            "/Outside/YardGround/", "/Shack/Floor/", "/Shack/Walls/", "/Shack/Exterior/", "/Outside/Forest/Hills/",
            "/Outside/Forest/FarGround/")


def floating(sc, boxes=None, eps=0.06):
    """Parts (grouped by Model) with no chain of contacts down to the ground or the building."""
    b = boxes or Boxes(sc)
    P = b.pairs(eps)
    adj = defaultdict(list)
    if len(P):
        d = b.overlap(P[:, 0], P[:, 1], eps)
        for (i, j), dd in zip(P, d):
            if dd >= 0:
                adj[i].append(j)
                adj[j].append(i)
    sibs = defaultdict(list)
    for i, n in enumerate(b.nodes):
        sibs[id(n)].append(i)
    for lst in sibs.values():                      # the pieces of one part hold together
        for i in lst[1:]:
            adj[lst[0]].append(i)
            adj[i].append(lst[0])
    seen = set()
    stack = [i for i, n in enumerate(b.nodes) if any(g in n.path() for g in GROUNDED) or b.lo[i, 1] < -0.3]
    seen.update(stack)
    while stack:
        i = stack.pop()
        for j in adj[i]:
            if j not in seen:
                seen.add(j)
                stack.append(j)
    loose = defaultdict(list)
    done = set()
    for i, n in enumerate(b.nodes):
        if i not in seen and id(n) not in done:
            done.add(id(n))
            m = n.parent if n.parent.kind == "Model" else n
            loose[m.path()].append(n.name)
    return dict(loose)


# ---------------------------------------------------------------- pierce

PIERCE_OK = ("Flue", "Duct", "Conduit", "Cable", "Wire", "Pipe", "Cord", "Root", "Trunk", "Rope", "Gas", "Stems")
# ground a post, a pole or a footing is set into
GROUNDLIKE = ("Path", "Ground", "Slab", "LotAsphalt", "YardGround", "Pad", "Asphalt", "Shoulder", "Verge", "Meadow",
              "Bank", "FarGround", "Hill", "Ridge", "DitchBed", "FarBank", "Apron", "Track")
# structure that other things are set into: it never counts as passing through them
STRUCT = ("TileBacking", "Paint", "AtticWall", "Siding", "BaseCourse", "Core", "Breast", "Ground", "Pilaster",
          "Tiles", "TileHole", "Cornice",
          "Parapet", "Roof", "Asphalt", "Shoulder", "Bank", "Verge", "Meadow", "DitchBed", "FarBank", "Slab",
          "LotAsphalt", "YardGround", "FarGround", "Hill", "Tile", "Panel", "AtticLining", "AtticJoist", "Stain",
          "Ridge", "Footing", "Path")


def pierce(sc, boxes=None, margin=0.1, ok=PIERCE_OK):
    """Pairs where one part crosses the other's whole thickness and comes out on both sides,
    inside the other's face (a blade through a block, a slab through a ceiling). Thin
    things that are meant to go through (flue, conduit, cables, roots) are allowed by name."""
    b = boxes or Boxes(sc)
    P = b.pairs(0.0)
    if not len(P):
        return []
    d = b.overlap(P[:, 0], P[:, 1])
    P = P[d > 0.02]
    out = []
    for i, j in P:
        if b.nodes[i] is b.nodes[j]:
            continue
        if "/Outside/Forest/" in b.nodes[i].path() and "/Outside/Forest/" in b.nodes[j].path():
            continue                              # crowns of a forest wall grow into each other
        for a, c in ((i, j), (j, i)):            # does a pass through c?
            na, nc = b.nodes[a], b.nodes[c]
            if any(w in na.name for w in ok) or any(w in nc.name for w in ok):
                continue
            if na.name in STRUCT or nc.name in ("Tiles", "TileHole") or nc.name in GROUNDLIKE:
                continue
            if na.parent is nc.parent and na.parent.kind == "Model" and na.kind == "MeshPart":
                continue                          # pieces of one mesh prop
            k = int(np.argmin(b.H[c]))
            if b.H[c][k] * 2 > 3.0:               # only thin things can be pierced
                continue
            q = (b.corners(a) - b.C[c]) @ b.R[c]   # a's corners in c's frame
            hk = b.H[c][k]
            if not (q[:, k].min() < -hk - margin and q[:, k].max() > hk + margin):
                continue
            inside = True
            for u in range(3):
                if u == k:
                    continue
                if q[:, u].max() < -b.H[c][u] + margin or q[:, u].min() > b.H[c][u] - margin:
                    inside = False
            # a's cross-section must not cover all of c's face (then c is just sunk into a)
            covers = all(q[:, u].min() <= -b.H[c][u] and q[:, u].max() >= b.H[c][u] for u in range(3) if u != k)
            if inside and not covers:
                out.append((na.path(), nc.path()))
    return out


# ---------------------------------------------------------------- planes

def _faces(n):
    """Flat faces of a Block: (axis, sign, coord, 2-D corner polygon in the other two axes)."""
    R, c = n.p["cf"].R, n.p["cf"].p
    h = np.asarray(n.p["size"], float) / 2
    out = []
    for k in range(3):
        for s in (-1, 1):
            nrm = R[:, k] * s
            ax = int(np.argmax(np.abs(nrm)))
            if abs(nrm[ax]) < 0.999:
                continue
            sg = 1 if nrm[ax] > 0 else -1
            u, v = [a for a in range(3) if a != k]
            fc = c + nrm * h[k]
            pts = []
            for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                p = fc + R[:, u] * h[u] * su + R[:, v] * h[v] * sv
                pts.append(p)
            pts = np.array(pts)
            uu, vv = [a for a in range(3) if a != ax]
            out.append((ax, sg, round(float(fc[ax]), 2), pts[:, [uu, vv]]))
    return out


def _poly_mask(mask, poly, ox, oy, res):
    from PIL import Image, ImageDraw
    img = Image.fromarray(mask.astype(np.uint8) * 255)
    d = ImageDraw.Draw(img)
    pts = [((p[0] - ox) / res, (p[1] - oy) / res) for p in poly]
    d.polygon(pts, fill=255)
    return np.array(img) > 0


def _largest_square(mask):
    """Side (in cells) of the largest all-True square in mask (integral image + bisection)."""
    if not mask.any():
        return 0
    S = np.zeros((mask.shape[0] + 1, mask.shape[1] + 1), np.int64)
    S[1:, 1:] = mask.astype(np.int64).cumsum(0).cumsum(1)

    def fits(s):
        if s > min(mask.shape):
            return False
        w = S[s:, s:] - S[:-s, s:] - S[s:, :-s] + S[:-s, :-s]
        return bool((w == s * s).any())
    lo, hi = 1, min(mask.shape)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if fits(mid):
            lo = mid
        else:
            hi = mid - 1
    return lo


def planes(sc, boxes=None, res=0.2, limit_in=6.0, limit_out=12.0, radius=110.0):
    """Unbroken single-colour planes over the limit. A plane is the union of coplanar,
    same-facing faces of one colour and material; anything else lying on it or within 0.4 in
    front of it breaks it. Faces nobody sees (undersides near the ground, beyond `radius`)
    are skipped."""
    b = boxes or Boxes(sc)
    groups = defaultdict(list)
    for n in sc.nodes("Part"):
        p = n.p
        if p["shape"] != "Block" or p["transparency"] >= 0.5:
            continue
        c = p["cf"].p
        if math.hypot(c[0], c[2]) > radius:
            continue
        for ax, sg, co, poly in _faces(n):
            if ax == 1 and sg < 0 and co < 2.0:
                continue
            # the room decides the limit: a point just in front of the face
            mid = np.zeros(3)
            mid[ax] = co + sg * 0.3
            uu, vv = [a for a in range(3) if a != ax]
            mid[uu], mid[vv] = poly.mean(0)
            groups[(ax, sg, co, p["color"], p["material"], in_room(mid, 0.2))].append((poly, n))
    bad = []
    for (ax, sg, co, color, mat, inside), lst in groups.items():
        allp = np.concatenate([q for q, _ in lst])
        u0, v0 = allp.min(0)
        u1, v1 = allp.max(0)
        uu, vv = [a for a in range(3) if a != ax]
        limit = limit_in if inside else limit_out
        if (u1 - u0) <= limit or (v1 - v0) <= limit:
            continue
        area = sum(abs(0.5 * np.sum(q[:, 0] * np.roll(q[:, 1], -1) - np.roll(q[:, 0], -1) * q[:, 1])) for q, _ in lst)
        if area <= limit * limit:
            continue
        W, H = int(math.ceil((u1 - u0) / res)) + 1, int(math.ceil((v1 - v0) / res)) + 1
        mask = np.zeros((H, W), bool)
        for q, _ in lst:
            mask |= _poly_mask(np.zeros((H, W), bool), q, u0, v0, res)
        # breakers: other parts touching or just in front of the plane
        lo = np.zeros(3)
        hi = np.zeros(3)
        lo[uu], hi[uu], lo[vv], hi[vv] = u0, u1, v0, v1
        lo[ax], hi[ax] = (co - 0.01, co + 0.4) if sg > 0 else (co - 0.4, co + 0.01)
        own = {id(n) for _, n in lst}
        for i in b.query(lo, hi):
            n = b.nodes[i]
            if id(n) in own:
                continue
            if n.kind == "Part" and n.p["color"] == color and n.p["material"] == mat:
                continue
            a0, a1 = b.lo[i][uu], b.hi[i][uu]
            c0, c1 = b.lo[i][vv], b.hi[i][vv]
            # only things that reach the plane's front (not buried behind it)
            front = b.hi[i][ax] > co + 0.01 if sg > 0 else b.lo[i][ax] < co - 0.01
            if not front:
                continue
            x0, x1 = int(max(0, (a0 - u0) / res)), int(min(W, math.ceil((a1 - u0) / res)))
            y0, y1 = int(max(0, (c0 - v0) / res)), int(min(H, math.ceil((c1 - v0) / res)))
            if x1 > x0 and y1 > y0:
                mask[y0:y1, x0:x1] = False
        side = _largest_square(mask) * res
        if side > limit + 1e-6:
            ys, xs = np.nonzero(mask)
            centre = np.zeros(3)
            centre[ax] = co
            centre[uu], centre[vv] = u0 + xs.mean() * res, v0 + ys.mean() * res
            bad.append(dict(axis="XYZ"[ax], sign=sg, coord=co, color=color, material=mat, side=round(side, 1),
                            limit=limit, centre=tuple(np.round(centre, 1)), parts=len(lst),
                            example=lst[0][1].path()))
    bad.sort(key=lambda r: -r["side"] / r["limit"])
    return bad


# ---------------------------------------------------------------- clear boxes at markers

def clear(sc, boxes=None, width=3.0, height=3.0, lift=0.3, depth=0.3, reach_top=8.0):
    """For every item marker: the box from the marker to its station's Stand, `width` wide,
    from `lift` to `height` above the marker's surface, must hold nothing but the marker's
    own station (its shelves, tub walls, the slot's enclosure). For every Stand: a 1.6-wide
    column 5 high above the floor (things lower than 0.3 -- mats -- don't count). An
    overlap counts when it goes deeper than `depth` in every direction."""
    b = boxes or Boxes(sc, keep=lambda n: n.p.get("collide") or n.p["transparency"] < 0.99)
    out = []
    st = sc.root.get("Stations")
    for m in st.children:
        stands = {c.name: c for c in m.children if c.kind == "Marker" and c.name.startswith("Stand")}
        if not stands:
            continue
        own = {id(n) for n in m.walk()}
        for c in m.walk():
            if c.kind != "Marker" or c.name.startswith("Stand") or not spslib.is_item_marker(c.name):
                continue
            stand = stands.get("Stand" + c.name[4:]) if c.name.startswith("Work") and len(c.name) > 4 else None
            stand = stand or stands.get("Stand")
            p0 = c.p["cf"].p
            p1 = stand.p["cf"].p
            hit = _box_hits(b, p0, p1, width, p0[1] + lift, min(p0[1] + height, max(reach_top, p0[1] + 1.2)),
                            skip=own, depth=depth)
            if hit:
                out.append((m.name + "." + c.name, hit[:4]))
        for s_ in stands.values():
            p = s_.p["cf"].p
            hit = _box_hits(b, p, p + s_.p["cf"].look * 0.01, 1.6, p[1] + 0.3, p[1] + 5.0, length_pad=0.8, depth=depth)
            if hit:
                out.append((m.name + "." + s_.name, hit[:4]))
    return out


def _box_hits(b, p0, p1, width, y0, y1, skip=(), length_pad=0.0, depth=0.15):
    d = np.array((p1[0] - p0[0], p1[2] - p0[2]))
    ln = float(np.linalg.norm(d))
    d = d / ln if ln > 1e-6 else np.array((0.0, 1.0))
    nrm = np.array((-d[1], d[0]))
    mid = np.array(((p0[0] + p1[0]) / 2, (p0[2] + p1[2]) / 2))
    half = np.array((ln / 2 + length_pad, width / 2))
    cs = np.array([mid + d * half[0] * a + nrm * half[1] * c for a in (-1, 1) for c in (-1, 1)])
    lo = (cs[:, 0].min(), y0, cs[:, 1].min())
    hi = (cs[:, 0].max(), y1, cs[:, 1].max())
    hits = []
    for i in b.query(lo, hi):
        n = b.nodes[i]
        if n.kind == "Marker" or id(n) in skip or n.top() == "Items" or n.name in STRUCT:
            continue
        Cb = np.array((mid[0], (y0 + y1) / 2, mid[1]))
        Rb = np.column_stack(((d[0], 0.0, d[1]), (0.0, 1.0, 0.0), (nrm[0], 0.0, nrm[1])))
        Hb = np.array((half[0], (y1 - y0) / 2, half[1]))
        if sat_depth(b.C[i], b.R[i], b.H[i], Cb, Rb, Hb) > depth:
            hits.append(n.path())
    return hits


def sat_depth(Ca, Ra, Ha, Cb, Rb, Hb):
    """Smallest overlap of two oriented boxes over the 15 separating axes (< 0: apart)."""
    axes = [Ra[:, k] for k in range(3)] + [Rb[:, k] for k in range(3)]
    for i in range(3):
        for j in range(3):
            c = np.cross(Ra[:, i], Rb[:, j])
            nn = np.linalg.norm(c)
            if nn > 1e-6:
                axes.append(c / nn)
    T = Cb - Ca
    best = np.inf
    for ax in axes:
        ra = np.sum(np.abs(Ra.T @ ax) * Ha)
        rb = np.sum(np.abs(Rb.T @ ax) * Hb)
        best = min(best, ra + rb - abs(T @ ax))
    return best


# ---------------------------------------------------------------- ceiling, window, horizon

def ceiling(sc, boxes=None, step=0.5):
    """Rays straight up from Y 5 all over the room: each must hit an opaque part below Y 10
    (the ceiling) unless it is under the hatch, where it must hit the attic or the roof."""
    from .interior import HATCH
    b = boxes or Boxes(sc, max_transp=0.2)
    x0, x1, _, _, z0, z1 = ROOM
    open_ = []
    xs = np.arange(x0 + step / 2, x1, step)
    zs = np.arange(z0 + step / 2, z1, step)
    up = [i for i in range(len(b.nodes)) if b.hi[i, 1] > 5.0 and b.lo[i, 1] < 16.0 and
          b.lo[i, 0] < x1 and b.hi[i, 0] > x0 and b.lo[i, 2] < z1 and b.hi[i, 2] > z0]
    hx0, hx1, hz0, hz1 = HATCH
    for x in xs:
        for z in zs:
            top = 16.0 if (hx0 <= x <= hx1 and hz0 <= z <= hz1) else 10.0
            hit = False
            for i in up:
                if not (b.lo[i, 0] <= x <= b.hi[i, 0] and b.lo[i, 2] <= z <= b.hi[i, 2]):
                    continue
                q = (np.array((x, 7.0, z)) - b.C[i]) @ b.R[i]
                hx, _, hz = b.H[i]
                R = b.R[i]
                if abs(R[1, 1]) > 0.999:          # upright box: exact XZ footprint test
                    if abs(q[0]) > hx or abs(q[2]) > hz:
                        continue
                if b.lo[i, 1] >= 5.0 and b.lo[i, 1] <= top:
                    hit = True
                    break
            if not hit:
                open_.append((round(float(x), 2), round(float(z), 2)))
    return open_


def window(sc):
    """The PlayerBlock: invisible, collides, fills the serving window opening."""
    n = next((x for x in sc.root.walk() if x.name == "PlayerBlock"), None)
    if n is None:
        return ["no PlayerBlock"]
    p = n.p
    probs = []
    half = np.abs(p["cf"].R) @ (np.array(p["size"]) / 2)
    lo, hi = p["cf"].p - half, p["cf"].p + half
    want_lo = (L.WIN_X0, L.WIN_Y0, L.IN_Z1)
    want_hi = (L.WIN_X1, L.WIN_Y1, L.OUT_Z1)
    if not (np.all(lo <= np.array(want_lo) + 1e-3) and np.all(hi >= np.array(want_hi) - 1e-3)):
        probs.append("PlayerBlock %s..%s does not cover %s..%s" % (tuple(lo), tuple(hi), want_lo, want_hi))
    if p["transparency"] < 1.0 or not p["collide"]:
        probs.append("PlayerBlock must be invisible and collide")
    return probs


def horizon(sc, boxes=None, eye=(0.0, 5.0, 20.0), r_min=40.0, bins=360):
    """In every direction from the forecourt, something must stand higher (in angle) than
    the ground's far edge."""
    b = boxes or Boxes(sc)
    x0, x1, z0, z1 = L.WORLD
    best = np.full(bins, -90.0)
    e = np.asarray(eye)
    for i in range(len(b.nodes)):
        c = b.C[i]
        dx, dz = c[0] - e[0], c[2] - e[2]
        r = math.hypot(dx, dz)
        if r < r_min:
            continue
        top = b.hi[i, 1]
        ang = math.degrees(math.atan2(top - e[1], r))
        half = math.degrees(math.atan2(max(b.H[i][0], b.H[i][2]) * 1.0, r))
        az = math.degrees(math.atan2(dx, dz))
        for k in range(int((az - half) // (360 / bins)), int((az + half) // (360 / bins)) + 1):
            best[k % bins] = max(best[k % bins], ang)
    edge = math.degrees(math.atan2(-2.8 - e[1], min(x1 - abs(e[0]), z1 - abs(e[2]))))
    gaps = [k * 360 / bins for k in range(bins) if best[k] <= edge + 0.5]
    return gaps, float(best.min()), edge


# ---------------------------------------------------------------- contract, lights, props, budget

CONTRACT_NAMES = ("Door", "Door1", "Door2", "DoorHandle", "Lid", "Drawer", "TipJar", "Face", "Shutter",
                  "TicketPrinter", "TicketRail", "Button", "Screen", "Monitor1", "Monitor2", "Phone", "Handset", "Dial",
                  "SwitchBox", "Cradle", "Lever", "Cord", "FuelCap", "Handle", "Exhaust", "Gate", "Head",
                  "Bulb", "WheelieBin1", "WheelieBin2", "Shade")


def contract(sc, old):
    """Paths (relative to Stations / Markers) of batch 1's markers, attachments, moving and
    named parts that the remake must still have."""
    def names(scene):
        out = {}
        st = scene.root.get("Stations")
        for m in st.children:
            out["Stations/" + m.name] = "Model"
            for n in m.walk():
                if n is m:
                    continue
                rel = n.path().split("/Stations/" + m.name + "/", 1)[-1]
                if n.kind in ("Marker", "Attachment") or (n.kind in ("Part", "MeshPart") and (
                        n.p.get("pivot") is not None or n.name in CONTRACT_NAMES or n.name.startswith("Glow")
                        or n.name.startswith("Ticket"))):
                    out["Stations/%s/%s" % (m.name, rel)] = n.kind
                if n.kind == "Model" and n.name in CONTRACT_NAMES:
                    out["Stations/%s/%s" % (m.name, rel)] = n.kind
            for k, v in (m.p.get("attrs") or {}).items():
                if k != "Lamp" and not k.startswith("Lamp"):
                    out["Stations/%s@%s" % (m.name, k)] = "attr"
        for n in scene.root.get("Markers").children:
            out["Markers/" + n.name] = n.kind
        return out
    want = names(old)
    have = names(sc)
    # V3: a moving part became an openable Model of the same name, or rides inside one
    from . import opens as O
    opened = {n.path().split("/Stations/", 1)[-1] for n in sc.nodes("Model") if O.is_openable(n)}
    opened = {"Stations/" + p for p in opened}
    missing, moved = [], []
    for k in sorted(want):
        if k in have or k.startswith("Markers/Car_Path"):
            continue
        head_, _, leaf = k.rpartition("/")
        alt = [o + "/" + leaf for o in opened if o.rpartition("/")[0] == head_ and (o + "/" + leaf) in have]
        (moved if alt else missing).append(k if not alt else "%s -> %s" % (k, alt[0]))
    kind = sorted(k for k in want if k in have and have[k] != want[k] and
                  {have[k], want[k]} != {"Part", "MeshPart"} and k not in opened)
    now_open = sorted(k for k in want if k in opened)
    return missing, kind, moved, now_open


def lights(sc):
    probs = []
    for n in sc.nodes("Light"):
        probs.append("Light object: " + n.path())
    for n in sc.nodes(("Part", "MeshPart")):
        a = dict(n.parent.p.get("attrs") or {})
        a.update(n.p.get("attrs") or {})
        if any(k.startswith("Lamp") for k in a) and n.name == "Bulb":
            for k in ("LampGroup", "LampKind", "LampRange", "LampBrightness", "LampColor"):
                if k not in a:
                    probs.append("%s: no %s" % (n.path(), k))
            if a.get("LampGroup") not in ("Shack", "Street", "Always"):
                probs.append("%s: LampGroup %r" % (n.path(), a.get("LampGroup")))
    return probs


def budget(sc):
    cnt = {"inside": 0, "outside": 0}
    for n in sc.nodes(("Part", "MeshPart")):
        if n.top() in ("Items",):
            continue
        cnt[where(n)] += 1
    return cnt


# ---------------------------------------------------------------- bodies, items and swings

BODY = (2.0, 5.0, 1.0)             # an R6 player: 2 wide, 5 tall, 1 deep
PIZZA_STATIONS = {"DoughStation": ["Work"], "SauceStation": ["WorkSauce", "WorkCheese"], "ChopStation": ["Work"],
                  "ToppingRail": ["Work"], "CutTable": ["Work"], "BoxStation": ["Work"]}
BOX_WORK = {"BoxStation": ["Work"]}
SIDE = 4.0                         # clear floor a Stand needs on at least two sides


FLOORISH = ("Mat", "Tile", "Floor", "Puddle", "Drain", "Threshold", "Skirting")
CONTAINERS = ("Tub", "DeckLining", "Hearth", "StoreFloor", "Liner", "Back", "Leaf", "Grip")   # (a shut lid over a Tub)


def _not_floor(n):
    return not any(f in n.name for f in FLOORISH)


def _hits_obb(b, C, R, H, skip=(), depth=0.05, keep=None, min_top=None):
    """Paths of the boxes in b that overlap the oriented box (C, R, H) deeper than `depth`;
    min_top: ignore what does not reach above that height (a dusting of flour under a pizza)."""
    ext = np.abs(R) @ H
    out = []
    for i in b.query(C - ext, C + ext):
        n = b.nodes[i]
        if n.kind == "Marker" or n.top() == "Items" or id(n) in skip:
            continue
        if min_top is not None and b.hi[i][1] <= min_top:
            continue
        if keep is not None and not keep(n):
            continue
        if sat_depth(b.C[i], b.R[i], b.H[i], C, R, H) > depth:
            out.append(n.path().replace("PizzaShack/", ""))
    return out


def _flat(R):
    """The marker's frame turned upright: its look kept level."""
    look = -R[:, 2]
    f = np.array((look[0], 0.0, look[2]))
    f = f / (np.linalg.norm(f) or 1.0)
    z = -f
    x = np.cross((0.0, 1.0, 0.0), z)
    return np.column_stack((x, (0.0, 1.0, 0.0), z))


def bodies(sc):
    """Real bodies and items instead of points.
    * a 2 x 5 x 1 body at every Stand, Queue, Customer and PlayerSpawn hits nothing that collides;
    * every Stand has 4 studs of clear floor (nothing that collides, 0.5 .. 5 up) on two of its sides;
    * a pizza (3.4 x 0.4 x 3.4) at every pizza Work, an open box's lid zone at the box station's
      Work (3.6 wide, 3.2 behind the marker, 3.5 up), a 0.8 cube at every Slot and Tub, hit
      nothing visible but what they sit on;
    * the oven: 6 studs of clear floor in front of its mouths, nothing in the doors' swing plus
      the peel (2 studs)."""
    out = []
    bc = Boxes(sc, keep=lambda n: bool(n.p.get("collide")) and n.p["transparency"] < 0.99)
    bv = Boxes(sc, keep=lambda n: n.p["transparency"] < 0.99)
    mk = sc.root.get("Markers")
    people = [(c.name, c) for c in mk.children if c.name.startswith(("Queue", "PlayerSpawn"))]
    st = sc.root.get("Stations")
    for m in st.children:
        for c in m.walk():
            if c.kind == "Marker" and (c.name.startswith("Stand") or c.name == "Customer"):
                people.append((m.name + "." + c.name, c))
    for name, c in people:
        R = _flat(c.p["cf"].R)
        p = c.p["cf"].p
        C = p + np.array((0.0, BODY[1] / 2 + 0.3, 0.0))              # feet clear of mats and sills
        hit = _hits_obb(bc, C, R, np.array(BODY) / 2, keep=_not_floor)
        if hit:
            out.append(("body", name, hit[:4]))
        if ".Stand" in name:
            clear_sides = 0
            for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                d = R @ np.array((dx, 0.0, dz))
                along = SIDE / 2 + (BODY[0] / 2 if dx else BODY[2] / 2)
                Cs = p + d * along + np.array((0.0, 1.75, 0.0))          # the floor up to the hips
                Hs = np.array((BODY[0] / 2 if dz else SIDE / 2, 1.25, SIDE / 2 if dz else BODY[2] / 2 + 0.5))
                if not _hits_obb(bc, Cs, R, Hs, keep=_not_floor):
                    clear_sides += 1
            if clear_sides < 2:
                out.append(("sides", name, clear_sides))
    for m in st.children:
        own_surface = {id(n) for n in m.walk() if n.name in ("Top", "Board", "Shelf", "Deck", "Hearth", "Rail")}
        for c in m.walk():
            if c.kind != "Marker":
                continue
            p, R = c.p["cf"].p, _flat(c.p["cf"].R)
            if c.name in PIZZA_STATIONS.get(m.name, ()):
                hit = _hits_obb(bv, p + np.array((0.0, 0.22, 0.0)), R, np.array((1.7, 0.2, 1.7)), skip=own_surface,
                                min_top=p[1] + 0.25)
                if hit:
                    out.append(("pizza", m.name + "." + c.name, hit[:4]))
            if c.name in BOX_WORK.get(m.name, ()):
                Cb = p + R @ np.array((0.0, 1.9, -1.6))           # behind = along the marker's look (-Z), from
                hit = _hits_obb(bv, Cb, R, np.array((1.8, 1.6, 1.6)), skip=own_surface)     # the box's rim up
                if hit:
                    out.append(("lid", m.name + "." + c.name, hit[:4]))
            if c.name.startswith(("Slot", "Tub")):
                hold = own_surface | {id(n) for n in m.walk() if n.name in CONTAINERS}
                hit = _hits_obb(bv, p + np.array((0.0, 0.45, 0.0)), R, np.array((0.4, 0.4, 0.4)), skip=hold,
                                depth=0.08)
                if hit:
                    out.append(("item", m.name + "." + c.name, hit[:4]))
    oven = st.get("Oven")
    if oven is not None:
        from . import st_east as OE
        own = {id(n) for n in oven.walk()}
        zc = (OE.MZ[0] + OE.MZ[1]) / 2
        zh = (OE.MZ[1] - OE.MZ[0]) / 2 + 0.3
        C = np.array((OE.X0 - OE.APRON / 2, 3.0, zc))
        hit = _hits_obb(bc, C, np.eye(3), np.array((OE.APRON / 2, 2.5, zh)), keep=_not_floor, skip=own)
        if hit:
            out.append(("apron", "Oven", hit[:4]))
        for (yf, ys, yc) in OE.DECKS:
            C = np.array((OE.X0 - 1.6, yf + 0.75, zc))
            hit = _hits_obb(bv, C, np.eye(3), np.array((1.6, 0.75, zh)), skip=own)
            if hit:
                out.append(("swing", "Oven", hit[:4]))
    return out


# ---------------------------------------------------------------- z-fighting

def zfight(sc, boxes=None):
    """spslib's coplanar-face test, then each hit re-sampled against the mesh pieces too (a
    sill lining or a trim mesh lying on the shared plane hides it): only the ones still seen."""
    b = boxes or Boxes(sc)
    hits = spslib.zfight(sc)
    if not hits:
        return hits
    by_path = defaultdict(list)
    for n in sc.nodes("Part"):
        by_path[n.path()].append(n)
    meshes = np.array([n.kind == "MeshPart" for n in b.nodes])
    idx = spslib.BoxIndex(sc)

    def covered(pt):
        for i in b.query(pt - 1e-3, pt + 1e-3):
            if not meshes[i]:
                continue
            loc = b.R[i].T @ (pt - b.C[i])
            if np.all(np.abs(loc) < b.H[i] - 1e-4):
                return True
        return False

    out = []
    for pa, pb, (ax, sg, co), area in hits:
        seen = False
        for na in by_path[pa]:
            for nb in by_path[pb]:
                ra = [r for (a_, s_, c_, r) in spslib._faces_aa(na) if a_ == ax and s_ == sg and abs(c_ - co) < 1e-3]
                rb = [r for (a_, s_, c_, r) in spslib._faces_aa(nb) if a_ == ax and s_ == sg and abs(c_ - co) < 1e-3]
                if not ra or not rb:
                    continue
                (a0, a1, b0, b1), (c0, c1, d0, d1) = ra[0], rb[0]
                u0, u1, v0, v1 = max(a0, c0), min(a1, c1), max(b0, d0), min(b1, d1)
                if u1 - u0 <= 1e-6 or v1 - v0 <= 1e-6:
                    continue
                u, v = [k for k in range(3) if k != ax]
                for fu in (0.137, 0.512, 0.883):
                    for fv in (0.141, 0.527, 0.871):
                        pt = np.zeros(3)
                        pt[ax] = co + sg * 0.02
                        pt[u] = u0 + (u1 - u0) * fu
                        pt[v] = v0 + (v1 - v0) * fv
                        if not idx.inside(pt, exclude=(na, nb)) and not covered(pt):
                            seen = True
        if seen:
            out.append((pa, pb, (ax, sg, co), area))
    return out


# ---------------------------------------------------------------- openables

KEEP_CLEAR = {}         # name -> (lo, hi) world boxes no open door may stand in (filled in openings())
# sweep hits that are box artefacts, checked by hand. The oven doors' plates are arched and the
# surround's band is an arc: their boxes overlap round the arch while the shapes do not (a
# 0.35 plate dropping open about its front bottom edge rises at most 0.054 at its crown, and
# it is inset 0.06 from the mouth all round).
SWEEP_OK = {("Oven/Door", "Oven/Surround"), ("Oven/Door", "Oven/Rivets")}


def openings(sc):
    """Everything that opens, swept from shut to open (a quarter at a time) through what is
    around it, then left open: it may not stand in another open door, a Stand's body, the way
    out of the back door or the floor in front of the oven. Also: a Model that says it opens
    must have a PrimaryPart with a pivot, and only parts that move."""
    from . import opens as O, st_east as OE
    out = []
    bv = Boxes(sc, keep=lambda n: n.p["transparency"] < 0.99)
    ops = [m for m in sc.nodes("Model") if O.is_openable(m)]
    clear_zones = {
        "BackDoorWay": (np.array((L.DOOR_X0, 0.6, L.IN_Z0)), np.array((L.DOOR_X1, 7.0, L.IN_Z0 + 3.0))),
        "OvenApron": (np.array((OE.X0 - OE.APRON, 0.6, OE.MZ[0] - 0.3)), np.array((OE.X0 - 0.4, 6.0, OE.MZ[1] + 0.3))),
    }
    KEEP_CLEAR.update(clear_zones)
    bodies_ = []
    for st in sc.root.get("Stations").children:
        for n in st.walk():
            if n.kind == "Marker" and n.name.startswith("Stand"):
                R = _flat(n.p["cf"].R)
                bodies_.append((st.name, n.p["cf"].p + np.array((0.0, BODY[1] / 2 + 0.3, 0.0)), R,
                                np.array(BODY) / 2))
    opened = []
    for m in ops:
        a = m.p["attrs"]
        name = m.path().replace("PizzaShack/", "")
        if m.p.get("primary") is None or m.p["primary"].p.get("pivot") is None:
            out.append(("no pivot", name, []))
            continue
        own = {id(n) for n in m.walk()}
        idx = [i for i, n in enumerate(bv.nodes) if id(n) in own]
        hits = set()
        # what a piece already touches shut (a frame it sits in; boxes round curved pieces) is
        # the pierce check's business: only what the moving piece runs into on the way counts
        rest = {i: set(_hits_obb(bv, bv.C[i], bv.R[i], bv.H[i], skip=own, depth=0.06)) for i in idx}
        for f in (0.25, 0.5, 0.75, 1.0):
            T_ = O.open_tf(m, f)
            for i in idx:
                C_ = T_.R @ bv.C[i] + T_.p
                R_ = T_.R @ bv.R[i]
                for h in _hits_obb(bv, C_, R_, bv.H[i], skip=own, depth=0.06):
                    if h not in rest[i] and not any(a_ in name and b_ in h for a_, b_ in SWEEP_OK):
                        hits.add(h)
                if f == 1.0:
                    opened.append((m, name, C_, R_, bv.H[i]))
        if hits:
            out.append(("sweep", name, sorted(hits)[:4]))
    # a swing door's hinge is its edge away from its station's nearest Stand
    for m in ops:
        a = m.p["attrs"]
        if a["Opens"] != "Swing" or a.get("OpenAxis") == "X" or m.parent.kind != "Model":
            continue
        st_ = m.parent
        sts = [n.p["cf"].p for n in st_.walk() if n.kind == "Marker" and n.name.startswith("Stand")]
        leaf = m.p["primary"]
        if not sts or leaf.name != "Leaf":
            continue
        P = O.world_pivot(m).p
        c = leaf.p["cf"].p
        sp = min(sts, key=lambda p: np.hypot(*(p - c)[[0, 2]]))
        ax = leaf.p["cf"].R[:, 0]                       # along the leaf's width
        free = 2 * c - P
        if abs(np.dot(sp - P, ax)) + 0.05 < abs(np.dot(sp - free, ax)):
            out.append(("hinge toward its Stand", m.path().replace("PizzaShack/", ""), []))
    # left open: other open doors, bodies at Stands, the keep-clear floor
    seen = set()
    for j, (m, name, C_, R_, H_) in enumerate(opened):
        for (m2, name2, C2, R2, H2) in opened[j + 1:]:
            if m2 is m or (name, name2) in seen:
                continue
            if np.any(np.abs(C_ - C2) > (np.abs(R_) @ H_ + np.abs(R2) @ H2)):
                continue
            if sat_depth(C_, R_, H_, C2, R2, H2) > 0.06:
                seen.add((name, name2))
                out.append(("open vs open", name, [name2]))
        for (stn, Cb, Rb, Hb) in bodies_:
            if (name, stn) in seen or m.parent.name == stn or m.parent.parent.name == stn:
                continue                     # its own Stand: the hinge rule (away from it) is checked below
            if sat_depth(C_, R_, H_, Cb, Rb, Hb) > 0.06:
                seen.add((name, stn))
                out.append(("in a Stand", name, [stn]))
        for zn, (lo, hi) in clear_zones.items():
            if (name, zn) in seen or (zn == "OvenApron" and "/Oven/" in name):
                continue                     # the oven's own doors drop open into its apron, as they should
            if sat_depth(C_, R_, H_, (lo + hi) / 2, np.eye(3), (hi - lo) / 2) > 0.06:
                seen.add((name, zn))
                out.append(("in the way", name, [zn]))
    return out


# ---------------------------------------------------------------- report

def run(sc, old=None, quick=False):
    rep = {}
    b = Boxes(sc)
    rep["budget"] = budget(sc)
    rep["props"] = {k: len(v) for k, v in sc.kit.used.items()} if hasattr(sc, "kit") else {}
    rep["lights"] = lights(sc)
    rep["grid"] = spslib.check_grid(sc)
    rep["window"] = window(sc)
    rep["ceiling_open"] = ceiling(sc)
    rep["floating"] = floating(sc, b)
    rep["pierce"] = pierce(sc, b)
    rep["clear"] = clear(sc)
    rep["bodies"] = bodies(sc)
    rep["openings"] = openings(sc)
    if not quick:
        rep["planes"] = planes(sc, b)
        rep["horizon"] = horizon(sc, b)
        rep["zfight"] = zfight(sc, b)
        ok, badm = spslib.check_item_markers(sc)
        rep["item_markers"] = (ok, badm)
    if old is not None:
        rep["contract"] = contract(sc, old)
    return rep


def show(rep, limit=25):
    def head(t):
        print("\n== " + t)
    head("budget (<= 6000 inside, <= 12000 outside)")
    print(rep["budget"])
    head("prop models (80 inside, 50 outside)")
    print(rep["props"])
    head("lights")
    print(len(rep["lights"]), rep["lights"][:limit])
    head("grid")
    print(len(rep["grid"]), rep["grid"][:limit])
    head("PlayerBlock")
    print(rep["window"])
    head("ceiling: open spots")
    print(len(rep["ceiling_open"]), rep["ceiling_open"][:limit])
    head("floating (model: parts)")
    fl = rep["floating"]
    print(len(fl))
    for k, v in list(fl.items())[:limit]:
        print("  ", k, v[:6])
    head("pierce (a passes through b)")
    print(len(rep["pierce"]))
    for a, c in rep["pierce"][:limit]:
        print("  ", a, " -> ", c)
    head("bodies, items and swings")
    print(len(rep["bodies"]))
    for r in rep["bodies"][:limit * 2]:
        print("  ", r)
    head("openables: swept, left open")
    print(len(rep["openings"]))
    for r in rep["openings"][:limit * 3]:
        print("  ", r)
    head("clear boxes at markers")
    print(len(rep["clear"]))
    for k, v in rep["clear"][:limit]:
        print("  ", k, v)
    if "planes" in rep:
        head("planes over the limit")
        print(len(rep["planes"]))
        for r in rep["planes"][:limit]:
            print("   %s%s %.2f %s %s side %.1f > %g at %s (%d parts, e.g. %s)" % (
                "+" if r["sign"] > 0 else "-", r["axis"], r["coord"], r["color"], r["material"], r["side"],
                r["limit"], r["centre"], r["parts"], r["example"]))
        head("horizon (gaps in degrees, lowest angle, edge angle)")
        g, lo, edge = rep["horizon"]
        print(len(g), g[:20], round(lo, 2), round(edge, 2))
        head("z-fighting")
        print(len(rep["zfight"]), rep["zfight"][:limit])
        head("item markers on their surfaces")
        ok, bad = rep["item_markers"]
        print(ok, "ok;", len(bad), "bad", bad[:limit])
    if "contract" in rep:
        head("contract: missing / kind changed")
        miss, kind, moved, now_open = rep["contract"]
        print(len(miss), miss[:60])
        print(len(kind), kind[:limit])
        head("contract: V3 changes (a moving part is now an openable Model, its parts inside it)")
        print(len(now_open), now_open)
        print(len(moved), moved)


if __name__ == "__main__":
    import time
    t = time.time()
    from . import build as B
    sc = B.build()
    import scene_build
    old = scene_build.build(items=False)
    print("built in %.1fs" % (time.time() - t))
    rep = run(sc, old, quick="quick" in sys.argv)
    show(rep)
    print("\nchecks in %.1fs" % (time.time() - t))
