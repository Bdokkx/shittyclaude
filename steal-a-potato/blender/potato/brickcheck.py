"""Checks for brick-built pieces.

  zfight(parts)   pairs of faces that lie in the same plane, face the same way and overlap: in
                  Studio those flicker (z-fighting), so every one is reported
  rules(parts)    Plastic parts Inlet all round, Neon / SmoothPlastic Smooth, sizes >= 0.05
"""
import itertools

import numpy as np

FACES = [(0, 1), (0, -1), (1, 1), (1, -1), (2, 1), (2, -1)]


def _faces(p):
    """[(normal, offset, corners (4x3))] of a Block part in world space."""
    cf = p.p["cf"]
    hs = np.array(p.p["size"]) / 2
    out = []
    for ax, sg in FACES:
        n = cf.R[:, ax] * sg
        o = [a for a in range(3) if a != ax]
        cs = []
        for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            v = np.zeros(3)
            v[ax] = sg * hs[ax]
            v[o[0]] = a * hs[o[0]]
            v[o[1]] = b * hs[o[1]]
            cs.append(cf.p + cf.R @ v)
        cs = np.array(cs)
        out.append((n, float(n @ cs[0]), cs))
    return out


def _clip(subject, clipper):
    """Sutherland-Hodgman: convex polygon subject clipped by convex polygon clipper (2D, CCW)."""
    out = list(subject)
    for i in range(len(clipper)):
        a, b = clipper[i], clipper[(i + 1) % len(clipper)]
        inp, out = out, []
        if not inp:
            break

        def inside(p):
            return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]) >= -1e-9

        def cross(p, q):
            d1 = np.array(q) - np.array(p)
            d2 = np.array(b) - np.array(a)
            den = d1[0] * d2[1] - d1[1] * d2[0]
            if abs(den) < 1e-12:
                return p
            t = ((a[0] - p[0]) * d2[1] - (a[1] - p[1]) * d2[0]) / den
            return (p[0] + t * d1[0], p[1] + t * d1[1])
        for j in range(len(inp)):
            p, q = inp[j], inp[(j + 1) % len(inp)]
            if inside(q):
                if not inside(p):
                    out.append(cross(p, q))
                out.append(q)
            elif inside(p):
                out.append(cross(p, q))
    return out


def _area(poly):
    if len(poly) < 3:
        return 0.0
    a = 0.0
    for i in range(len(poly)):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % len(poly)]
        a += x1 * y2 - x2 * y1
    return abs(a) / 2


def _ccw(poly):
    return poly if _signed(poly) > 0 else poly[::-1]


def _signed(poly):
    a = 0.0
    for i in range(len(poly)):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % len(poly)]
        a += x1 * y2 - x2 * y1
    return a / 2


def zfight(parts, tol=0.004, min_area=0.004):
    parts = [p for p in parts if p.p["shape"] == "Block" and p.p["transparency"] < 0.99]
    faces = {id(p): _faces(p) for p in parts}
    cents = {id(p): p.p["cf"].p for p in parts}
    rad = {id(p): float(np.linalg.norm(p.p["size"])) / 2 for p in parts}
    bad = []
    for a, b in itertools.combinations(parts, 2):
        if np.linalg.norm(cents[id(a)] - cents[id(b)]) > rad[id(a)] + rad[id(b)] + 0.01:
            continue
        for na, oa, ca in faces[id(a)]:
            for nb, ob, cb in faces[id(b)]:
                if na @ nb < 0.9999 or abs(oa - ob) > tol:
                    continue
                # project both onto the plane's own axes
                u = ca[1] - ca[0]
                u /= np.linalg.norm(u)
                v = np.cross(na, u)
                pa = _ccw([(float(c @ u), float(c @ v)) for c in ca])
                pb = _ccw([(float(c @ u), float(c @ v)) for c in cb])
                ar = _area(_clip(pa, pb))
                if ar > min_area:
                    bad.append((a, b, round(ar, 3)))
    return bad


def rules(parts):
    bad = []
    for p in parts:
        m, s = p.p["material"], p.p["surfaces"]
        if m == "Plastic" and s != "inlet":
            bad.append("%s: Plastic but %s" % (p.path(), s))
        if m != "Plastic" and s != "smooth":
            bad.append("%s: %s but %s" % (p.path(), m, s))
        if min(p.p["size"]) < 0.05:
            bad.append("%s: size %s" % (p.path(), p.p["size"]))
    return bad
