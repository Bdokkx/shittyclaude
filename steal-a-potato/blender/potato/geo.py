"""Chunky geometry helpers for the potato map's meshes (Roblox space: Y up, -Z forward).
Everything stays at least 0.2 thick; rods have r >= 0.1."""
import math

import numpy as np

import spsgeo as G
from spsgeo import CF, T, RX, RY, RZ, S  # noqa: F401


def _orient_convex(V, faces):
    """Wind every face of a convex solid so its normal points away from the centre."""
    V = np.asarray(V, float)
    c = V.mean(0)
    out = []
    for f in faces:
        P = V[list(f)]
        n = np.zeros(3)
        for i in range(len(P)):
            a, b = P[i], P[(i + 1) % len(P)]
            n += np.array(((a[1] - b[1]) * (a[2] + b[2]), (a[2] - b[2]) * (a[0] + b[0]), (a[0] - b[0]) * (a[1] + b[1])))
        out.append(tuple(f) if np.dot(n, P.mean(0) - c) >= 0 else tuple(f[::-1]))
    return out


def bevel_box(sx, sy, sz, b=0.08, c=(0, 0, 0)):
    """Box with every edge chamfered by b: the basic 'chunky bevelled' block."""
    hx, hy, hz = sx / 2, sy / 2, sz / 2
    b = min(b, hx * 0.45, hy * 0.45, hz * 0.45)
    V, idx = [], {}

    def v(key, p):
        idx[key] = len(V)
        V.append(p)
    for sxg in (-1, 1):
        for syg in (-1, 1):
            for szg in (-1, 1):
                v((sxg, syg, szg, 0), (sxg * hx, syg * (hy - b), szg * (hz - b)))
                v((sxg, syg, szg, 1), (sxg * (hx - b), syg * hy, szg * (hz - b)))
                v((sxg, syg, szg, 2), (sxg * (hx - b), syg * (hy - b), szg * hz))
    F = []
    # main faces
    for ax in range(3):
        for sg in (-1, 1):
            quad = []
            for a in (-1, 1):
                for bb in ((-1, 1) if a == -1 else (1, -1)):
                    s = [0, 0, 0]
                    s[ax] = sg
                    o = [k for k in range(3) if k != ax]
                    s[o[0]], s[o[1]] = a, bb
                    quad.append(idx[(s[0], s[1], s[2], ax)])
            F.append(quad)
    # edge chamfers (between faces ax1 and ax2, running along the third axis)
    for ax1, ax2 in ((0, 1), (0, 2), (1, 2)):
        ax3 = 3 - ax1 - ax2
        for s1 in (-1, 1):
            for s2 in (-1, 1):
                q = []
                for s3, which in ((-1, ax1), (1, ax1), (1, ax2), (-1, ax2)):
                    s = [0, 0, 0]
                    s[ax1], s[ax2], s[ax3] = s1, s2, s3
                    q.append(idx[(s[0], s[1], s[2], which)])
                F.append(q)
    # corner triangles
    for sxg in (-1, 1):
        for syg in (-1, 1):
            for szg in (-1, 1):
                F.append([idx[(sxg, syg, szg, k)] for k in range(3)])
    V = [(p[0] + c[0], p[1] + c[1], p[2] + c[2]) for p in V]
    return G.Geo(V, _orient_convex(V, F))


def chamfer_slab(pts, h, b=0.05, c=(0, 0, 0)):
    """A top-view outline (x, z) raised to height h with its top edge chamfered by b (the
    bevelled look for odd shapes: broken tiles, plates). Bottom at c[1]."""
    P = [np.array(p, float) for p in pts]
    if G.poly_area([tuple(p) for p in P]) < 0:
        P = P[::-1]
    n = len(P)
    inset = []
    for k in range(n):
        a, p_, q = P[k - 1], P[k], P[(k + 1) % n]
        e1, e2 = p_ - a, q - p_
        n1 = np.array((-e1[1], e1[0])) / np.linalg.norm(e1)
        n2 = np.array((-e2[1], e2[0])) / np.linalg.norm(e2)
        m = n1 + n2
        d = 1.0 + float(n1 @ n2)
        inset.append(p_ + m * b / max(d, 0.35))
    V = []
    for p_ in P:
        V.append((p_[0], 0.0, p_[1]))
    for p_ in P:
        V.append((p_[0], h - b, p_[1]))
    for p_ in inset:
        V.append((p_[0], h, p_[1]))
    F = []
    for k in range(n):
        j = (k + 1) % n
        F.append((k, j, n + j, n + k))
        F.append((n + k, n + j, 2 * n + j, 2 * n + k))
    if G.is_convex([tuple(p) for p in P]):
        F.append(tuple(range(2 * n, 3 * n)))
        F.append(tuple(range(n))[::-1])
    else:
        for a, bb, cc in G.triangulate([tuple(p) for p in P]):
            F.append((2 * n + a, 2 * n + bb, 2 * n + cc))
            F.append((a, cc, bb))
    g = G.outward(G.Geo(V, F))
    return g.xf(G.T(c[0], c[1], c[2]))


def ccyl(r, h, n=8, axis="y", c=(0, 0, 0), b=0.06):
    """Cylinder with chamfered caps (n sides, a flat side facing +X / +Z)."""
    b = min(b, r * 0.4, h * 0.3)
    prof = [(0.0, -h / 2), (r - b, -h / 2), (r, -h / 2 + b), (r, h / 2 - b), (r - b, h / 2), (0.0, h / 2)]
    g = G.outward(G.lathe(prof, n, phase=math.pi / n))
    return G._orient(g, axis, c)


def cfrustum(r0, r1, h, n=8, axis="y", c=(0, 0, 0), b=0.05):
    b = min(b, min(r0, r1) * 0.4 if min(r0, r1) > 0 else b, h * 0.3)
    prof = [(0.0, -h / 2), (max(r0 - b, 0.0), -h / 2), (r0, -h / 2 + b), (r1, h / 2 - b), (max(r1 - b, 0.0), h / 2),
            (0.0, h / 2)]
    g = G.outward(G.lathe(prof, n, phase=math.pi / n))
    return G._orient(g, axis, c)


def lathe(profile, n=10):
    return G.outward(G.lathe(profile, n, phase=math.pi / n))


def rod(a, b, r=0.09, n=6):
    """A straight chunky rod between two points (r >= 0.075 keeps it 0.15 thick)."""
    return G.tube([tuple(a), tuple(b)], max(r, 0.1), n)


def bent(path, r=0.09, n=6):
    return G.tube([tuple(p) for p in path], max(r, 0.1), n)


def slab(pts_xz, thick, y=0.0):
    """Flat slab from an XZ outline (convex or not), thick upwards from y."""
    return G.slab_poly(pts_xz, thick, (0, y, 0))


def irregular(rng, r, n=7, wob=0.25):
    pts = []
    for k in range(n):
        a = math.tau * k / n + rng.uniform(-0.2, 0.2)
        rr = r * (1 + rng.uniform(-wob, wob))
        pts.append((rr * math.cos(a), rr * math.sin(a)))
    return pts


# ---------------------------------------------------------------- the kit

PROPS = {}          # kind -> (builder, where-hint)

