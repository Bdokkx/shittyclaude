"""Every prop's design. Each function gets the Prop to fill and the Original it
replaces (positions of the old parts, in Handle space), and keeps the old part
names for anything the game might look up."""
import math
import random

import bmesh
from plib import (TAU, T, R, S, lerp, smoothstep, merge_into, xform, copy_bm, box, cylinder, sphere, ico, torus,  # noqa: F401
                  lathe, slab, loft, sweep, circle_pts, star_pts, catmull, arc_pts, rock, teardrop, leaf_pts,
                  puff, slab_holes, crescent_pts, bat_wing_pts, pyramid, rounded_rect_pts, ring_slab, capsule,
                  boolean, projected_slab, star3d, drop_facing, aim, densify, lathe_x, lathe_z, shaft, band,
                  pumpkin_profile, pumpkin_body, pumpkin_zsurf, pumpkin_leaf, bmesh_new, blob, union_all, cut,
                  rounded_box, superellipse_pts, wobble_pts, tube, taper_tube, straw_tuft, ellipsoid_shell_z,
                  zigzag_hem, thicken, subdivide_smooth, displace, fix_normals, lathe_loop, lathe_loop_z)
from plib import boolean  # noqa: F811  (self-intersection tolerant)
from mathutils import Matrix, Vector

PROPS = {}
ORDER = []
SOURCE = {}          # prop id -> original model it replaces (when the names differ)
VIEW = {}            # prop id -> (yaw, pitch, zoom) for the preview tile


def prop(pid, kind="Prop", view=None, source=None):
    def deco(fn):
        PROPS[pid] = (fn, kind)
        ORDER.append(pid)
        if view:
            VIEW[pid] = view
        if source:
            SOURCE[pid] = source
        return fn
    return deco


# ---------------------------------------------------------------- small helpers

def fillet_pts(pts, r, n=3):
    """Round every corner of a closed polygon with an arc of radius ~r."""
    out = []
    m = len(pts)
    for i in range(m):
        p0, p1, p2 = Vector(pts[i - 1]), Vector(pts[i]), Vector(pts[(i + 1) % m])
        a, b = (p0 - p1), (p2 - p1)
        la, lb = a.length, b.length
        if la < 1e-6 or lb < 1e-6:
            out.append(tuple(p1))
            continue
        a.normalize()
        b.normalize()
        ang = math.acos(max(-1.0, min(1.0, a.dot(b))))
        if ang < 1e-3 or ang > math.pi - 1e-3:
            out.append(tuple(p1))
            continue
        d = min(r / math.tan(ang / 2), la * 0.45, lb * 0.45)
        s, e = p1 + a * d, p1 + b * d
        for k in range(n + 1):
            t = k / n
            q = (1 - t) ** 2 * s + 2 * (1 - t) * t * p1 + t ** 2 * e      # quadratic bezier through the corner
            out.append((q.x, q.y))
    return out


def offset_poly(pts, d):
    """Grow a closed CCW-or-CW polygon outward by d (miter, clamped)."""
    m = len(pts)
    area = sum(pts[i][0] * pts[(i + 1) % m][1] - pts[(i + 1) % m][0] * pts[i][1] for i in range(m))
    sgn = 1 if area > 0 else -1
    out = []
    for i in range(m):
        p0, p1, p2 = Vector(pts[i - 1]), Vector(pts[i]), Vector(pts[(i + 1) % m])
        e1 = (p1 - p0).normalized()
        e2 = (p2 - p1).normalized()
        n1 = Vector((e1.y, -e1.x)) * sgn
        n2 = Vector((e2.y, -e2.x)) * sgn
        nb = (n1 + n2)
        if nb.length < 1e-6:
            nb = n1
        nb.normalize()
        k = d / max(nb.dot(n1), 0.35)
        q = p1 + nb * k
        out.append((q.x, q.y))
    return out


def sphere_walk(seed, n, step, jag=0.45, start=None, heading=None):
    """Random zigzag path of unit vectors over a sphere."""
    rng = random.Random(seed)
    p = Vector(start).normalized() if start else Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))).normalized()
    h = Vector(heading) if heading else p.orthogonal()
    h = (h - p * h.dot(p)).normalized()
    pts = [p.copy()]
    for i in range(n):
        side = p.cross(h).normalized()
        turn = jag * (1 if i % 2 == 0 else -1) * rng.uniform(0.5, 1.0)
        d = (h * math.cos(turn) + side * math.sin(turn)).normalized()
        p = (p + d * step).normalized()
        h = (d - p * d.dot(p)).normalized()
        pts.append(p.copy())
    return pts


def radial_ribbon(dirs, r_in, r_out, widths):
    """A closed slab following a path of unit directions on a sphere, spanning
    radius r_in..r_out (a crack cutter)."""
    rings = []
    n = len(dirs)
    for i, u in enumerate(dirs):
        t = (dirs[min(i + 1, n - 1)] - dirs[max(i - 1, 0)])
        side = u.cross(t).normalized()
        w = widths[i] / 2
        rings.append([u * r_in - side * w, u * r_out - side * w, u * r_out + side * w, u * r_in + side * w])
    return loft(rings)


def lumpy(bm, r, bumps, seed):
    """Push a sphere-ish mesh into a lumpy rock: radius * (1 + sum of smooth bumps)."""
    rng = random.Random(seed)
    dirs = [(Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))).normalized(),
             rng.uniform(-0.09, 0.12), rng.uniform(2.0, 5.0)) for _ in range(bumps)]
    for v in bm.verts:
        u = v.co.normalized()
        k = 1.0
        for d, a, p in dirs:
            k += a * max(0.0, u.dot(d)) ** p
        v.co = u * r * k
    return bm


# ================================================================= events / weather

@prop("Meteor", view=(28, 14, 1.0))
def meteor(p, o):
    """A chunky charred space rock split by glowing magma cracks, with the hot
    core showing through the cracks and a few deep glowing pits."""
    rock_p = p.part("Rock", (62, 46, 44), "Slate", smooth=24)
    glow = p.part("Glow", (255, 122, 26), "Neon")
    R0 = 2.84
    rng = random.Random(7)
    bumps = [(Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))).normalized(),
              rng.uniform(-0.10, 0.15), rng.uniform(2.0, 6.0)) for _ in range(14)]

    def radius(u):
        k = 1.0 + sum(a * max(0.0, u.dot(d)) ** pw for d, a, pw in bumps)
        return R0 * max(k, 0.95)
    body = ico(1.0, subdiv=2)
    jit = random.Random(11)
    for v in body.verts:
        u = v.co.normalized()
        v.co = u * radius(u) * (1 + jit.uniform(-0.03, 0.03))
    cutters = bmesh_new()
    starts = [((0.6, 0.7, 0.5), (0.3, -0.4, 0.8)), ((-0.7, 0.2, 0.7), (0.5, 0.8, 0.0)),
              ((0.2, -0.6, 0.8), (-0.9, 0.1, 0.2)), ((-0.3, 0.8, -0.5), (0.9, 0.1, 0.4)),
              ((0.8, -0.3, -0.5), (0.0, 0.8, -0.4)), ((-0.6, -0.5, -0.6), (0.6, -0.2, -0.7))]
    for k, (st, h) in enumerate(starts):
        path = sphere_walk(20 + k, 6, 0.24, jag=0.5, start=st, heading=h)
        n = len(path)
        widths = [0.16 + 0.36 * math.sin(math.pi * (i + 0.5) / n) for i in range(n)]
        merge_into(cutters, radial_ribbon(path, 2.40, 3.60, widths))
    for d, r in (((0.15, 0.95, 0.25), 0.46), ((-0.85, -0.35, 0.40), 0.40), ((0.55, -0.20, -0.80), 0.42),
                 ((0.70, 0.10, 0.70), 0.30), ((-0.20, -0.30, 0.93), 0.34)):
        u = Vector(d).normalized()
        merge_into(cutters, sphere(r, 12, 8, scale=(1, 1.6, 1)), T(*(u * (radius(u) + 0.12))) @ aim(u))
    rock_p.add(boolean(body, cutters))
    glow.add(sphere(2.66, 28, 16))


@prop("Coin", view=(24, 8, 1.0))
def coin(p, o):
    """A fat gold coin: a rounded rim, a sunken face and a puffy glowing star on
    both sides."""
    rim = p.part("Rim", (255, 176, 0), "Metal", smooth=30)
    face = p.part("Face", (255, 222, 64), "Metal", smooth=30)
    star = p.part("Star", (255, 240, 138), "Neon")
    rim.add(lathe_loop_z([(0.78, -0.10), (0.80, -0.13), (0.92, -0.155), (0.975, -0.14), (1.0, -0.08), (1.0, 0.08),
                          (0.975, 0.14), (0.92, 0.155), (0.80, 0.13), (0.78, 0.10)], segs=48))
    face.add(lathe_z([(0, -0.10), (0.79, -0.10), (0.79, 0.10), (0, 0.10)], segs=48))
    for m in (T(0, 0.02, 0.085), T(0, 0.02, -0.085) @ R("Y", 180)):
        star.add(star3d(0.50, 0.23, 0.035, 0.10, n=5), m)


@prop("UFO", view=(24, 20, 1.0))
def ufo(p, o):
    """Classic flying saucer: a lens-shaped hull with a trim band, a ring of
    round lights, a glowing beam emitter underneath and a glass dome with a
    little green pilot waving inside."""
    hull = p.part("Hull", (160, 168, 188), "Metal", smooth=30)
    trim = p.part("Trim", (96, 102, 130), "Metal", smooth=30)
    dome = p.part("Dome", (124, 245, 255), "Glass", transparency=0.35, smooth=60)
    lights = p.part("Lights", (255, 226, 46), "Neon")
    emit = p.part("Emitter", (124, 245, 255), "Neon")
    alien = p.part("Alien", (124, 222, 86), "SmoothPlastic", smooth=50)
    eyes = p.part("AlienEyes", (24, 24, 34), "SmoothPlastic", smooth=50)
    hull.add(lathe([(0, -1.86), (1.6, -1.86), (2.3, -1.92), (2.8, -1.92), (4.4, -1.72), (6.6, -1.42), (8.2, -1.12),
                    (8.85, -0.98), (8.85, -0.52), (8.2, -0.36), (6.6, -0.12), (4.6, 0.12), (3.9, 0.20), (0, 0.20)],
                   segs=48))
    trim.add(lathe_loop([(8.70, -1.02), (9.02, -0.96), (9.10, -0.75), (9.02, -0.54), (8.70, -0.48)], segs=48))
    trim.add(lathe_loop([(3.50, 0.12), (3.95, 0.14), (4.05, 0.32), (3.90, 0.46), (3.50, 0.44)], segs=40))
    for i in range(12):
        a = TAU * (i + 0.5) / 12
        u = Vector((math.cos(a), 0, math.sin(a)))
        lights.add(sphere(0.46, 8, 5, scale=(1, 0.75, 1)), T(*(u * 9.06)) @ T(0, -0.75, 0))
    emit.add(lathe([(0, -1.98), (1.4, -1.98), (2.05, -1.94), (2.3, -1.88), (2.3, -1.80), (0, -1.80)], segs=40))
    # glass dome resting on the deck (closed at its base so it sorts cleanly)
    prof = []
    for i in range(13):
        t = math.radians(-17 + 107 * i / 12)
        prof.append((3.6 * math.cos(t), 1.2 + 3.24 * math.sin(t)))
    prof[-1] = (0, 4.44)
    dome.add(lathe([(0, prof[0][1])] + prof, segs=40))
    # the pilot: round body, big head, huge eyes, antennae, one arm up waving
    alien.add(lathe([(0, 0.25), (0.55, 0.30), (0.78, 0.65), (0.70, 1.20), (0.48, 1.55), (0, 1.62)], segs=20))
    alien.add(sphere(0.92, 22, 14, scale=(1.08, 0.92, 1.0)), T(0, 2.30, 0))
    for sx in (-1, 1):
        stalk = [Vector((sx * 0.30, 3.00, 0.0)), Vector((sx * 0.48, 3.40, 0.05)), Vector((sx * 0.62, 3.72, 0.10))]
        alien.add(tube(stalk, 0.055, sides=6))
        alien.add(sphere(0.14, 10, 6), T(sx * 0.64, 3.80, 0.10))
    arm = [Vector((0.62, 1.20, 0.10)), Vector((1.05, 1.55, 0.20)), Vector((1.25, 2.05, 0.28))]
    alien.add(tube(arm, 0.13, sides=8))
    alien.add(sphere(0.20, 10, 6), T(1.28, 2.18, 0.30))
    alien.add(tube([Vector((-0.62, 1.20, 0.10)), Vector((-0.95, 0.95, 0.30)), Vector((-1.05, 0.65, 0.42))], 0.13, sides=8))
    for sx in (-1, 1):
        eyes.add(sphere(0.30, 16, 10, scale=(0.82, 1.15, 0.45)), T(sx * 0.36, 2.36, 0.80) @ R("Z", -sx * 18))
    eyes.add(sphere(0.06, 8, 5, scale=(2.2, 1.0, 1.0)), T(0, 1.86, 0.84))


def crater_field(R0, craters):
    """Radius function for a sphere with smooth dished craters and soft raised rims.
    craters = [(direction, rim radius a, depth)]."""
    cs = [(Vector(d).normalized(), a, depth) for d, a, depth in craters]

    def f(u):
        h = 0.0
        for c, a, depth in cs:
            s = R0 * math.acos(max(-1.0, min(1.0, u.dot(c))))
            if s < a:
                h += -depth * (1 - (s / a) ** 2) + depth * 0.22 * (s / a) ** 6
            h += depth * 0.22 * math.exp(-((s - a) / (0.30 * a)) ** 2) if s >= a else 0.0
        return R0 + h
    return f


def sphere_patch(radius_fn, axis, a, lift, rings=4, segs=20):
    """A thin round patch lying on a radius-function surface around `axis` (crater floors)."""
    u = Vector(axis).normalized()
    e1 = u.orthogonal().normalized()
    e2 = u.cross(e1).normalized()
    R0 = radius_fn(u)
    bm = bmesh_new()

    def vert(r, ang):
        d = (u * R0 + (e1 * math.cos(ang) + e2 * math.sin(ang)) * r).normalized()
        return bm.verts.new(d * (radius_fn(d) + lift))
    centre = bm.verts.new(u * (radius_fn(u) + lift))
    prev = None
    for i in range(1, rings + 1):
        r = a * i / rings
        ring = [vert(r, TAU * k / segs) for k in range(segs)]
        if prev is None:
            for k in range(segs):
                bm.faces.new((centre, ring[k], ring[(k + 1) % segs]))
        else:
            for k in range(segs):
                bm.faces.new((prev[k], ring[k], ring[(k + 1) % segs], prev[(k + 1) % segs]))
        prev = ring
    bm.normal_update()
    for f in bm.faces:                       # face outward
        if f.normal.dot(f.calc_center_median()) < 0:
            f.normal_flip()
    return bm


@prop("Moon", view=(18, 8, 1.0))
def moon(p, o):
    """A big pale moon with smooth dished craters (soft raised rims, darker floors)
    and a ring of puffy glowing stars."""
    body = p.part("Moon", (242, 238, 220), "SmoothPlastic", smooth=50)
    crat = p.part("Craters", (196, 190, 164), "SmoothPlastic", smooth=50)
    stars = p.part("Stars", (255, 226, 46), "Neon")
    R0 = 5.0
    craters = [((0.42, 0.52, 0.74), 1.45, 0.30), ((-0.62, -0.12, 0.78), 1.05, 0.24), ((0.18, -0.70, 0.70), 0.82, 0.19),
               ((0.88, -0.22, 0.42), 0.66, 0.15), ((-0.88, 0.40, -0.25), 1.2, 0.26), ((0.30, 0.20, -0.93), 1.3, 0.28),
               ((-0.4, -0.85, -0.3), 0.95, 0.21), ((-0.15, 0.80, 0.35), 0.58, 0.13)]
    rf = crater_field(R0, craters)
    ball = ico(1.0, subdiv=5)
    for v in ball.verts:
        u = v.co.normalized()
        v.co = u * rf(u)
    body.add(ball)
    for d, a, depth in craters:
        crat.add(sphere_patch(rf, d, a * 0.82, 0.02, rings=4, segs=24))
    for ang, rad, ro, tilt in ((96, 8.1, 1.0, 8), (22, 7.4, 0.74, -12), (166, 7.5, 0.82, 14), (250, 7.6, 0.72, -6),
                               (318, 7.3, 0.66, 18)):
        a = math.radians(ang)
        stars.add(star3d(ro, ro * 0.48, 0.07, 0.22), T(rad * math.cos(a), rad * math.sin(a), 0.6) @ R("Z", tilt))


@prop("Bolt", view=(20, 4, 1.0))
def bolt(p, o):
    """A fat cartoon lightning bolt with rounded corners and an orange outline."""
    core = p.part("Bolt", (255, 226, 46), "Neon")
    edge = p.part("Edge", (255, 150, 30), "SmoothPlastic", smooth=40)
    raw = [(-0.18, 0.50), (0.24, 0.50), (0.06, 0.13), (0.28, 0.13), (-0.16, -0.52), (-0.03, -0.05), (-0.28, -0.05)]
    pts = [(x * 10.4, y * 10.4 - 0.48) for x, y in raw]
    pts = [(x * math.cos(math.radians(-8)) - y * math.sin(math.radians(-8)),
            x * math.sin(math.radians(-8)) + y * math.cos(math.radians(-8))) for x, y in pts]
    inner = fillet_pts(pts, 0.28, n=3)
    outer = fillet_pts(offset_poly(pts, 0.38), 0.45, n=3)
    core.add(slab(inner, 1.0, 0.28, seg=2))
    edge.add(slab(outer, 0.62, 0.16, seg=2))


@prop("CandyCorn", view=(26, 10, 1.0))
def candy_corn(p, o):
    """A big glossy candy corn kernel: rounded, a little flat front to back,
    yellow base, orange middle and a white tip."""
    base = p.part("Base", (255, 196, 40), "SmoothPlastic", smooth=50)
    mid = p.part("Mid", (255, 128, 24), "SmoothPlastic", smooth=50)
    tip = p.part("Tip", (255, 248, 234), "SmoothPlastic", smooth=50)
    ctrl = [(0.0, 0.0), (0.62, 0.0), (0.98, 0.07), (1.14, 0.26), (1.16, 0.48), (1.10, 0.74), (0.98, 1.02),
            (0.84, 1.36), (0.70, 1.70), (0.55, 2.04), (0.40, 2.36), (0.25, 2.62), (0.11, 2.81), (0.0, 2.87)]
    sm = [(max(r, 0.0), y) for r, y in catmull(ctrl, samples=2)]
    sm[0] = (0.0, 0.0)
    sm[-1] = (0.0, 2.87)

    def r_at(y):
        for (ra, ya), (rb, yb) in zip(sm, sm[1:]):
            if ya <= y <= yb:
                return lerp(ra, rb, (y - ya) / max(yb - ya, 1e-6))
        return 0.0

    def band_prof(y0, y1):
        lo = [(0.0, 0.0)] if y0 <= 0 else [(0.0, y0), (r_at(y0), y0)]
        hi = [(0.0, 2.87)] if y1 >= 2.87 else [(r_at(y1), y1), (0.0, y1)]
        return lo + [(r, y) for r, y in sm if y0 + 1e-4 < y < y1 - 1e-4] + hi
    for part, y0, y1 in ((base, 0.0, 0.98), (mid, 0.98, 2.03), (tip, 2.03, 2.87)):
        part.add(lathe(band_prof(y0, y1), segs=32, sz=0.74))


@prop("Tornado", view=(24, 10, 1.0))
def tornado(p, o):
    """A twisting cartoon twister: a lobed funnel that corkscrews up and flares
    out at the top, white wind ribbons spiralling round it, and planks and leaves
    caught up in it."""
    funnel = p.part("Funnel", (201, 211, 224), "SmoothPlastic", transparency=0.3, smooth=60)
    bands = p.part("Bands", (255, 255, 255), "SmoothPlastic", smooth=60)
    debris = p.part("Debris", (150, 98, 48), "Wood", smooth=30)
    leaves = p.part("Leaves", (82, 194, 52), "SmoothPlastic", smooth=40)
    H = 24.0

    def rad(y):
        t = y / H
        return 0.9 + 7.4 * t ** 1.7 + 0.35 * math.sin(t * 9.0)

    def bend(y):                                   # the funnel snakes a little
        t = y / H
        return Vector((0.9 * math.sin(t * 3.4) * (1 - t * 0.6), 0, 0.5 * math.sin(t * 2.3 + 1.0)))
    rings = []
    ny, segs = 22, 40
    for j in range(ny + 1):
        y = H * (j / ny) ** 0.9
        rr = rad(y)
        tw = y * 0.32
        ring = []
        for i in range(segs):
            a = TAU * i / segs
            k = 1 + 0.07 * math.cos(5 * (a - tw))
            off = bend(y)
            ring.append(Vector((off.x + rr * k * math.cos(a), y, off.z + rr * k * math.sin(a))))
        rings.append(ring)
    # rounded top: pull the last rings in to a shallow dome
    top = bend(H)
    for j, (dy, f) in enumerate(((0.35, 0.92), (0.65, 0.7), (0.8, 0.35))):
        rings.append([Vector((top.x + (v.x - top.x) * f, H + dy - 0.8, top.z + (v.z - top.z) * f)) for v in rings[ny]])
    rings.append([Vector((top.x, H, top.z))])
    rings[0] = [Vector((v.x, 0.0, v.z)) for v in rings[0]]
    funnel.add(loft(rings, cap_start=True, cap_end=False))
    # wind ribbons
    for k, (y0, y1, turns, ph, w) in enumerate(((2.0, 13.0, 1.6, 0.0, 0.75), (9.0, 21.0, 1.4, 2.4, 0.9),
                                                (15.0, 23.2, 0.9, 4.4, 0.9))):
        path, ws, ts = [], [], []
        n = 46
        for i in range(n + 1):
            t = i / n
            y = lerp(y0, y1, t)
            a = ph + TAU * turns * t + y * 0.32
            rr = rad(y) * 1.07 + 0.35
            off = bend(y)
            path.append(Vector((off.x + rr * math.cos(a), y + 0.25 * math.sin(t * 12), off.z + rr * math.sin(a))))
            taper = math.sin(math.pi * t) ** 0.5
            ws.append(w * (0.25 + 0.75 * taper))
            ts.append(0.16 * (0.4 + 0.6 * taper))
        bands.add(sweep(path, ts, ws, sides=6, point_end=False, up=Vector((0, 1, 0))))
    rng = random.Random(5)
    # planks and a little fence piece
    for i, (y, a, tilt) in enumerate(((5.0, 40, 30), (9.5, 160, -45), (14.0, 280, 60), (18.5, 70, -20),
                                      (21.5, 210, 35), (12.0, 340, 75))):
        rr = rad(y) * 1.12 + 0.9
        aa = math.radians(a)
        pos = bend(y) + Vector((rr * math.cos(aa), y, rr * math.sin(aa)))
        L = rng.uniform(1.6, 2.4)
        debris.add(box(0.55, L, 0.18, bevel=0.05, seg=1),
                   T(*pos) @ R("Y", -a) @ R("Z", tilt) @ R("X", rng.uniform(-30, 30)))
    fence = bmesh_new()
    for x in (-0.55, 0.55):
        merge_into(fence, box(0.22, 1.4, 0.16, bevel=0.04, seg=1), T(x, 0, 0))
    for y in (-0.28, 0.32):
        merge_into(fence, box(1.6, 0.2, 0.12, bevel=0.03, seg=1), T(0, y, 0.12))
    aa = math.radians(115)
    rr = rad(7.0) * 1.12 + 1.0
    debris.add(fence, T(*(bend(7.0) + Vector((rr * math.cos(aa), 7.0, rr * math.sin(aa))))) @ R("Y", -115) @ R("Z", 25))
    for i in range(10):
        y = 3.0 + i * 1.95
        a = rng.uniform(0, 360)
        rr = rad(y) * 1.1 + rng.uniform(0.4, 1.4)
        aa = math.radians(a)
        pos = bend(y) + Vector((rr * math.cos(aa), y, rr * math.sin(aa)))
        leaf = slab(leaf_pts(0.9, 0.55, n=6), 0.06, 0.0)
        leaves.add(leaf, T(*pos) @ R("Y", rng.uniform(0, 360)) @ R("X", rng.uniform(-60, 60)) @ R("Z", rng.uniform(0, 360)))


@prop("IcePatch", view=(28, 34, 1.0))
def ice_patch(p, o):
    """A slippery puddle of ice: a rounded wobbly sheet with a soft edge, white
    glints, and clusters of ice crystals poking up round the rim."""
    ice = p.part("Ice", (191, 239, 255), "Ice", transparency=0.15, smooth=50)
    shine = p.part("Shine", (255, 255, 255), "Neon")
    crys = p.part("Crystals", (124, 245, 255), "Glass", transparency=0.25, smooth=20)
    outline = wobble_pts(superellipse_pts(6.4, 6.3, p=2.3, n=72), 0.06, freq=5, seed=0.7)
    sheet = slab(outline, 0.36, 0.12, seg=2)
    ice.add(sheet, T(0, 0.16, 0) @ R("X", -90))
    for (x, z, L, ang) in ((-2.2, -1.0, 2.6, 35), (-1.2, 0.6, 1.4, 35), (1.6, 1.8, 2.0, 35), (2.6, -2.2, 1.2, 35),
                           (0.4, -3.0, 1.6, 35)):
        st = slab(rounded_rect_pts(L, 0.16, 0.08, n=2), 0.05, 0.0)
        shine.add(st, T(x, 0.335, z) @ R("Y", ang) @ R("X", -90))
    def crystal(h, r):
        return lathe([(0, 0), (r, 0.0), (r * 1.05, h * 0.72), (0, h)], segs=6)
    clusters = [((-4.6, -3.4), [(2.6, 0.42, 0, 0), (1.7, 0.30, 30, 1), (1.3, 0.26, -35, 2), (0.9, 0.2, 60, 3)]),
                ((4.9, 2.6), [(2.2, 0.38, 0, 0), (1.5, 0.28, -28, 1), (1.1, 0.22, 40, 2)]),
                ((-3.4, 4.4), [(1.6, 0.30, 0, 0), (1.1, 0.24, 35, 1), (0.8, 0.18, -40, 2)]),
                ((3.8, -4.3), [(1.2, 0.24, 0, 0), (0.85, 0.18, 30, 1)])]
    for (cx, cz), parts in clusters:
        for h, r, tilt, k in parts:
            ang = k * 97.0
            dx, dz = 0.35 * k * math.cos(math.radians(ang)), 0.35 * k * math.sin(math.radians(ang))
            crys.add(crystal(h, r), T(cx + dx, 0.1, cz + dz) @ R("Y", ang) @ R("Z", tilt))


@prop("SnowCloud", view=(22, 6, 1.0))
def snow_cloud(p, o):
    """A fat cartoon snow cloud: big round puffs on top, a darker heavy belly and
    a row of icicles hanging underneath."""
    cloud = p.part("Cloud", (232, 238, 248), "SmoothPlastic", smooth=60)
    belly = p.part("Belly", (176, 188, 210), "SmoothPlastic", smooth=60)
    ice = p.part("Icicles", (191, 239, 255), "Ice", transparency=0.1, smooth=30)
    puffs = [(-6.6, -0.4, 0.4, 2.9), (-3.6, 1.2, 0.0, 3.6), (0.2, 1.5, -0.4, 3.9), (3.9, 0.9, 0.3, 3.4),
             (6.8, -0.3, -0.2, 2.8), (-1.6, 0.6, 2.4, 2.6), (2.4, 0.4, 2.2, 2.5), (-1.0, 0.8, -2.6, 2.6),
             (3.0, 0.2, -2.3, 2.4), (8.3, -1.2, 0.6, 1.7), (-8.2, -1.3, -0.3, 1.7)]
    shell = blob([(x, y, z, r, 1.0, 0.92, 1.0) for x, y, z, r in puffs], segs=20, rings=12)
    cutter = box(30, 10, 30)
    xform(cutter, T(0, -6.0 - 2.2, 0))
    cloud.add(boolean(shell, cutter))
    bl = blob([(-5.0, -2.0, 0.0, 2.6, 1.3, 0.62, 1.1), (-1.0, -2.3, 0.2, 3.0, 1.35, 0.6, 1.15),
               (3.2, -2.1, -0.1, 2.7, 1.3, 0.6, 1.1)], segs=20, rings=12)
    belly.add(bl)
    rng = random.Random(3)
    for i, x in enumerate((-7.0, -5.4, -3.7, -2.0, -0.3, 1.4, 3.1, 4.8, 6.4)):
        z = rng.uniform(-1.4, 1.4)
        top = -3.0 if abs(x) < 5.5 else -2.2
        L = rng.uniform(2.0, 3.6) if abs(x) < 5.5 else rng.uniform(1.2, 2.0)
        r = rng.uniform(0.28, 0.42)
        prof = [(0, top - L), (r * 0.35, top - L * 0.8), (r * 0.7, top - L * 0.45), (r, top - 0.05), (r * 0.9, top + 0.6), (0, top + 0.7)]
        ice.add(lathe(prof, segs=7, rmod=lambda a: 1 + 0.12 * math.cos(3 * a)), T(x, 0, z))


@prop("FogCloud", view=(20, 14, 1.0))
def fog_cloud(p, o):
    """A low rolling bank of fog: a few big soft puffs, flat underneath,
    see-through."""
    puffs = p.part("Puffs", (230, 234, 240), "SmoothPlastic", transparency=0.5, smooth=70)
    cs = [(-6.6, 2.2, 0.4, 3.0), (-2.6, 3.0, -0.8, 3.9), (1.8, 3.1, 0.7, 4.1), (6.2, 2.3, -0.4, 3.1),
          (-0.6, 1.8, 3.0, 2.6), (2.0, 1.6, -3.1, 2.5)]
    shell = blob([(x, y, z, r, 1.25, 0.95, 1.05) for x, y, z, r in cs], segs=20, rings=12)
    cutter = box(40, 10, 40)
    xform(cutter, T(0, -0.6 - 5.0, 0))
    puffs.add(boolean(shell, cutter))


@prop("BananaPeel", view=(30, 30, 1.0))
def banana_peel(p, o):
    """A cartoon banana peel flopped on the ground: four floppy strips with curled
    tips, creamy insides, a little hump in the middle and the stem on top."""
    peel = p.part("Peel", (255, 222, 52), "SmoothPlastic", smooth=45)
    inside = p.part("Inside", (255, 246, 196), "SmoothPlastic", smooth=45)
    stem = p.part("Stem", (107, 74, 30), "SmoothPlastic", smooth=45)
    for k, (ang, L) in enumerate(((20, 2.6), (110, 2.3), (200, 2.7), (290, 2.4))):
        a = math.radians(ang)
        d = Vector((math.cos(a), 0, math.sin(a)))
        n = 10
        path, ws, ts = [], [], []
        for i in range(n + 1):
            t = i / n
            r = 0.25 + L * t
            y = 0.95 * (1 - t) ** 2.2 + 0.03 + (0.35 * smoothstep((t - 0.75) / 0.25))
            side = Vector((-d.z, 0, d.x)) * 0.25 * math.sin(t * 2.5 + k)
            path.append(d * r + Vector((0, y, 0)) + side)
            w = 0.95 * math.sin(math.pi * min(1.0, 0.18 + t * 0.92)) ** 0.6 + 0.12
            ws.append(w)
            ts.append(0.16)
        peel.add(sweep(path, ws, ts, sides=8, point_end=False, up=Vector((0, 1, 0))))
        # the creamy inside: a thinner strip lying on top of each one
        ip = [q + Vector((0, 0.07, 0)) for q in path[1:-2]]
        inside.add(sweep(ip, [w * 0.72 for w in ws[1:-2]], [0.07] * (len(ip)), sides=8, point_end=False,
                         up=Vector((0, 1, 0))))
        tipdir = (path[-1] - path[-2]).normalized()
        stem.add(sphere(0.13, 8, 5, scale=(1.3, 0.8, 1.3)), T(*(path[-1] + tipdir * 0.05)))
    peel.add(sphere(0.62, 16, 10, scale=(1.0, 1.05, 1.0)), T(0, 0.62, 0))
    st = [Vector((0, 1.05, 0)), Vector((0.05, 1.25, 0.02)), Vector((0.14, 1.40, 0.04))]
    stem.add(taper_tube(st, 0.16, 0.12, sides=7))
    stem.add(sphere(0.14, 8, 5, scale=(1, 0.6, 1)), T(0.15, 1.42, 0.04))


@prop("UFOBeam", view=(24, 10, 1.0))
def ufo_beam(p, o):
    """The tractor beam: a smooth see-through cone of light with soft rings
    rippling down it."""
    beam = p.part("Beam", (124, 245, 255), "Neon", transparency=0.7)
    prof = [(0, 0.0)]
    n = 30
    for i in range(n + 1):
        y = 34.0 * i / n
        t = y / 34.0
        r = lerp(12.8, 2.2, t)
        ripple = 0.05 * max(0.0, math.cos(TAU * y / 3.4)) ** 6
        prof.append((r * (1 + ripple), y))
    prof.append((0, 34.0))
    beam.add(lathe(prof, segs=36))
    for y in (3.0, 9.0, 15.0, 21.0, 27.0):
        r = lerp(12.8, 2.2, y / 34.0)
        beam.add(torus(r * 1.03, 0.10 + 0.012 * r, segs=36, rsegs=4), T(0, y, 0))


# ================================================================= effects (the game tints / fades these)

@prop("FxRing", view=(20, 40, 1.0))
def fx_ring(p, o):
    """Shockwave ring: a flat, smooth rounded band."""
    ring = p.part("Ring", (255, 255, 255), "Neon")
    ring.add(lathe_loop([(0.84, -0.03), (0.95, -0.06), (1.05, -0.04), (1.07, 0.0), (1.05, 0.04), (0.95, 0.06),
                         (0.84, 0.03), (0.82, 0.0)], segs=48))


@prop("FxSpikes", view=(26, 14, 1.0))
def fx_spikes(p, o):
    """A burst of chunky rock spikes punching out of a little pile of rubble."""
    sp = p.part("Spikes", (154, 160, 180), "Slate", smooth=20)
    rng = random.Random(4)
    base = rock(0.55, seed=2, jitter=0.14, subdiv=2, scale=(1.5, 0.35, 1.05))
    sp.add(base, T(0.05, 0.0, 0.0))
    for h, r, x, z, tilt, ang in ((0.95, 0.24, 0.0, 0.0, 0, 0), (0.70, 0.19, 0.45, 0.18, 22, 30),
                                  (0.62, 0.18, -0.48, 0.10, -24, 200), (0.52, 0.16, 0.20, -0.36, 26, 110),
                                  (0.46, 0.15, -0.22, 0.38, -20, 300), (0.40, 0.13, 0.72, -0.20, 34, 60),
                                  (0.36, 0.12, -0.74, -0.24, -34, 160)):
        cone = lathe([(0, 0.0), (r, 0.0), (r * 0.55, h * 0.55), (0, h)], segs=5, rmod=lambda a: 1 + 0.1 * math.cos(2 * a))
        sp.add(cone, T(x, -0.05, z) @ R("Y", ang) @ R("Z", tilt))


@prop("FxCrescent", view=(10, 70, 1.0))
def fx_crescent(p, o):
    """A slash swoosh: a smooth crescent that's thick in the middle and tapers to
    needle points, lying flat."""
    arc = p.part("Arc", (255, 255, 255), "Neon")
    pts = []
    n = 28
    outer, inner = [], []
    for i in range(n + 1):
        t = i / n
        a = math.radians(lerp(-62, 62, t))
        w = 0.34 * math.sin(math.pi * t) ** 0.8
        outer.append((1.0 * math.cos(a), 1.0 * math.sin(a)))
        inner.append(((1.0 - w) * math.cos(a), (1.0 - w) * math.sin(a)))
    pts = outer + list(reversed(inner[1:-1]))
    cres = slab(pts, 0.06, 0.0)
    # lie flat, bulge toward the front (+Z), like the old one
    arc.add(cres, T(-0.14, 0, 0.98 - 0.08) @ R("Y", -90) @ R("X", -90))


@prop("FxShard", view=(26, 12, 1.0))
def fx_shard(p, o):
    """An ice shard: a long faceted crystal, pointed at both ends."""
    sh = p.part("Shard", (191, 239, 255), "Glass", transparency=0.1, smooth=15)
    prof = [(0, -0.30), (0.17, -0.12), (0.21, 0.30), (0.15, 0.48), (0, 0.70)]
    shard = lathe(prof, segs=6, rmod=lambda a: 1 + 0.12 * math.cos(2 * a + 0.4))
    sh.add(shard, R("Y", 12) @ R("Z", 6))


@prop("FxStar", view=(16, 6, 1.0))
def fx_star(p, o):
    """A puffy little cartoon star."""
    st = p.part("Star", (255, 226, 46), "Neon")
    st.add(star3d(0.50, 0.24, 0.035, 0.07, n=5), T(0, 0.05, 0))


# ================================================================= Halloween items

def carve_face_shapes(kind="grin"):
    """Jack-o'-lantern face outlines in a unit-ish box (x, y), centred on 0."""
    eyes = [[(-0.42, 0.10), (-0.10, 0.06), (-0.25, 0.36)], [(0.42, 0.10), (0.25, 0.36), (0.10, 0.06)]]
    nose = [(-0.07, -0.06), (0.07, -0.06), (0.0, 0.06)]

    def ytop(x):
        return -0.12 - 0.10 * (1 - (x / 0.50) ** 2)
    grin = [(-0.50, -0.12), (-0.42, -0.27), (-0.30, -0.37), (-0.14, -0.42), (-0.06, -0.43), (-0.06, -0.32),
            (0.06, -0.32), (0.06, -0.43), (0.14, -0.42), (0.30, -0.37), (0.42, -0.27), (0.50, -0.12),
            (0.38, ytop(0.38)), (0.24, ytop(0.24)), (0.24, -0.31), (0.12, -0.31), (0.12, ytop(0.12)),
            (0.0, ytop(0.0)), (-0.12, ytop(-0.12)), (-0.12, -0.31), (-0.24, -0.31), (-0.24, ytop(-0.24)),
            (-0.38, ytop(-0.38))]
    return eyes + [nose, grin]


@prop("SpookyCase", view=(28, 18, 1.0))
def spooky_case(p, o):
    """A Halloween treasure chest: purple with a round lid, orange iron bands and
    corner caps, a glowing jack-o'-lantern face and a big padlock."""
    boxp = p.part("Box", (112, 46, 200), "SmoothPlastic", smooth=35)
    bands = p.part("Bands", (255, 138, 31), "Metal", smooth=35)
    face = p.part("Face", (255, 226, 46), "Neon")
    lock = p.part("Lock", (40, 40, 50), "Metal", smooth=35)
    W, D, Hb = 2.12, 1.32, 1.08
    body = box(W, Hb, D, bevel=0.07, seg=2)
    boxp.add(body, T(0, Hb / 2, 0))
    lid_r = D / 2
    lid = lathe_x([(0, -W / 2 + 0.01), (lid_r - 0.06, -W / 2 + 0.01), (lid_r, -W / 2 + 0.06), (lid_r, W / 2 - 0.06),
                   (lid_r - 0.06, W / 2 - 0.01), (0, W / 2 - 0.01)], segs=28, sy=0.95)
    cutter = box(W + 1, 2.0, 3.0)
    xform(cutter, T(0, -1.0, 0))
    lid = boolean(lid, cutter)
    boxp.add(lid, T(0, Hb + 0.02, 0))
    # iron bands: two straps over body and lid, a rim at the lid seam, corner caps
    for x in (-0.66, 0.66):
        strap_body = box(0.20, Hb + 0.02, D + 0.06, bevel=0.03, seg=1)
        bands.add(strap_body, T(x, Hb / 2, 0))
        strap_lid = lathe_x([(0, -0.10), (lid_r + 0.035, -0.10), (lid_r + 0.035, 0.10), (0, 0.10)], segs=28, sy=0.95)
        c2 = box(1, 2.0, 3.0)
        xform(c2, T(0, -1.0 - 0.012, 0))
        bands.add(boolean(strap_lid, c2), T(x, Hb + 0.02, 0))
    bands.add(box(W + 0.06, 0.12, D + 0.06, bevel=0.03, seg=1), T(0, Hb - 0.02, 0))
    for sx in (-1, 1):
        for sz in (-1, 1):
            bands.add(box(0.22, 0.22, 0.22, bevel=0.04, seg=1), T(sx * (W / 2 - 0.08), 0.10, sz * (D / 2 - 0.08)))
    # glowing jack-o'-lantern face on the front of the box
    for pts in carve_face_shapes():
        pts = [(x * 0.62, y * 0.62 + 0.50) for x, y in pts]
        face.add(slab(pts, 0.06, 0.0), T(0, 0, D / 2 + 0.005))
    # padlock hanging from the lid seam
    lock.add(box(0.36, 0.34, 0.14, bevel=0.05, seg=2), T(0, Hb - 0.16, D / 2 + 0.08))
    shackle = [Vector((-0.11, Hb, D / 2 + 0.08)), Vector((-0.11, Hb + 0.12, D / 2 + 0.08)), Vector((0, Hb + 0.18, D / 2 + 0.08)),
               Vector((0.11, Hb + 0.12, D / 2 + 0.08)), Vector((0.11, Hb, D / 2 + 0.08))]
    lock.add(tube(catmull(shackle, samples=3), 0.035, sides=6))
    face.add(slab([(-0.04, -0.06), (0.04, -0.06), (0.025, 0.02), (0.05, 0.05), (0.0, 0.09), (-0.05, 0.05), (-0.025, 0.02)],
                  0.03, 0.0), T(0, Hb - 0.18, D / 2 + 0.155))


@prop("QuestMarker", view=(20, 10, 1.0))
def quest_marker(p, o):
    """A glowing pumpkin to float over a quest giver: deep ribs so it reads even
    when it glows, a dark carved face, and a curly stem with a leaf."""
    pk = p.part("Pumpkin", (255, 138, 31), "Neon")
    stem = p.part("Stem", (82, 194, 52), "SmoothPlastic", smooth=45)
    face = p.part("Face", (90, 40, 12), "SmoothPlastic", smooth=45)
    R0, H0 = 0.66, 0.96
    pk.add(pumpkin_body(R0, H0, lobes=6, depth=0.16, segs=36), T(0, -0.02, 0))
    zs = pumpkin_zsurf(R0, H0, 6, 0.16)
    for pts in carve_face_shapes():
        pts = densify([(x * 0.62, y * 0.62 + 0.0) for x, y in pts], 0.05)
        face.add(projected_slab(pts, lambda x, y: zs(x, y + 0.02) + 0.012, lambda x, y: zs(x, y + 0.02) - 0.06,
                                spacing=0.06), T(0, -0.02, 0))
    sp = [Vector((0, 0.30, 0)), Vector((0.02, 0.48, 0)), Vector((0.08, 0.62, 0.02)), Vector((0.16, 0.70, 0.03))]
    stem.add(taper_tube(sp, 0.09, 0.06, sides=6))
    stem.add(slab(pumpkin_leaf(0.22), 0.04, 0.012, seg=1), T(-0.06, 0.40, 0.06) @ aim((-0.6, 0.35, 0.7)))


@prop("Cauldron", view=(26, 22, 1.0))
def cauldron(p, o):
    """A witch's cauldron: a round iron pot with a thick lip, ring handles and
    stubby feet, bubbling green brew, and a crackling fire on a little log pile
    underneath."""
    pot = p.part("Pot", (38, 38, 48), "Metal", smooth=35)
    brew = p.part("Brew", (108, 255, 58), "Neon")
    fire = p.part("Fire", (255, 138, 31), "Neon")
    logs = p.part("Logs", (110, 70, 36), "Wood", smooth=30)
    by = 0.36
    pot.add(lathe([(0, by), (0.55, by), (0.95, by + 0.12), (1.30, by + 0.42), (1.52, by + 0.90), (1.55, by + 1.30),
                   (1.46, by + 1.66), (1.30, by + 1.90), (1.22, by + 2.00), (1.20, by + 2.04), (1.08, by + 2.04),
                   (1.06, by + 1.92), (0, by + 1.92)], segs=36))
    pot.add(torus(1.21, 0.11, segs=36, rsegs=8), T(0, by + 2.06, 0))
    for sx in (-1, 1):
        ring = torus(0.24, 0.05, segs=16, rsegs=6, axis="X")
        pot.add(ring, T(sx * 1.52, by + 1.55, 0) @ R("Z", 0))
        pot.add(sphere(0.10, 8, 6), T(sx * 1.50, by + 1.78, 0))
    for k in range(3):
        a = math.radians(90 + 120 * k)
        x, z = 0.95 * math.cos(a), 0.95 * math.sin(a)
        pot.add(lathe([(0, -0.08), (0.20, -0.08), (0.24, 0.05), (0.17, by + 0.25), (0, by + 0.30)], segs=10), T(x, 0, z))
    # brew surface and bubbles
    brew.add(lathe([(0, by + 1.92), (1.07, by + 1.92), (1.07, by + 1.97), (0.7, by + 2.0), (0, by + 2.02)], segs=36))
    for x, y, z, r in ((0.40, 2.04, 0.20, 0.22), (-0.35, 2.03, -0.15, 0.18), (0.05, 2.05, -0.52, 0.15),
                       (-0.25, 2.04, 0.50, 0.14), (0.62, 2.03, -0.40, 0.12), (0.18, 2.45, 0.12, 0.12),
                       (-0.12, 2.62, -0.08, 0.08)):
        brew.add(sphere(r, 10, 6), T(x, by + y - 2.0 + 1.92 + 0.08 if y < 2.1 else by + y, z))
    # fire: a ring of flame tongues between the feet, licking up the sides
    rng = random.Random(9)
    for k in range(7):
        a = math.radians(k * 360 / 7 + 15)
        r = 0.55 + 0.25 * (k % 2)
        h = rng.uniform(0.55, 0.85)
        fl = lathe([(0, 0.0), (0.20, 0.05), (0.22, h * 0.35), (0.12, h * 0.7), (0, h)], segs=7)
        fire.add(fl, T(r * math.cos(a), 0.0, r * math.sin(a)) @ R("Z", 18 * math.cos(a)) @ R("X", -18 * math.sin(a)))
    fire.add(lathe([(0, 0.0), (0.42, 0.04), (0.40, 0.30), (0.20, 0.55), (0, 0.62)], segs=10))
    for k in range(4):
        a = math.radians(45 + 90 * k)
        lg = cylinder(0.11, 1.5, segs=8)
        logs.add(lg, T(0.25 * math.cos(a), 0.06, 0.25 * math.sin(a)) @ R("Y", -math.degrees(a)) @ R("Z", 90) @ R("X", 8))


# ================================================================= crown, ladle

@prop("Crown", view=(26, 24, 1.0))
def crown(p, o):
    """A chunky gold crown: a flared band with eight points, alternately tall and
    short, a pearl on every tip, a darker gold rim and four glowing jewels."""
    band = p.part("Band", (255, 196, 38), "Metal", smooth=35)
    rim = p.part("Rim", (214, 148, 20), "Metal", smooth=35)
    pearl = p.part("Pearl", (255, 240, 170), "SmoothPlastic", smooth=50)
    jewels = [p.part("Jewel", c, "Neon") for c in ((235, 60, 70), (70, 150, 255), (80, 220, 120), (190, 90, 255))]
    point = p.part("Point", (255, 196, 38), "Metal", smooth=35)
    n = 8
    segs = 64

    def top(a):
        k = (a / TAU * n) % 1.0
        tall = int(a / TAU * n) % 2 == 0
        hpt = 0.62 if tall else 0.36
        return 0.42 + hpt * max(0.0, 1 - abs(k - 0.5) * 2) ** 1.25

    def wall(y_lo, y_hi, r_lo, r_hi, rows):
        """Ring wall (0.08 thick) from y_lo(a) to y_hi(a); radii flare with height."""
        bm = bmesh_new()
        vo, vi = [], []
        for j in range(rows + 1):
            t = j / rows
            ro, ri = [], []
            for i in range(segs):
                a = TAU * (i + 0.5) / segs
                y = lerp(y_lo(a), y_hi(a), t)
                r = lerp(r_lo, r_hi, (y - 0.06) / 1.04)
                ro.append(bm.verts.new(((r + 0.04) * math.cos(a), y, (r + 0.04) * math.sin(a))))
                ri.append(bm.verts.new(((r - 0.04) * math.cos(a), y, (r - 0.04) * math.sin(a))))
            vo.append(ro)
            vi.append(ri)
        for j in range(rows):
            for i in range(segs):
                i2 = (i + 1) % segs
                bm.faces.new((vo[j][i], vo[j][i2], vo[j + 1][i2], vo[j + 1][i]))
                bm.faces.new((vi[j][i2], vi[j][i], vi[j + 1][i], vi[j + 1][i2]))
        for i in range(segs):
            i2 = (i + 1) % segs
            bm.faces.new((vi[rows][i], vo[rows][i], vo[rows][i2], vi[rows][i2]))
            bm.faces.new((vo[0][i], vi[0][i], vi[0][i2], vo[0][i2]))
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
        bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-5)
        fix_normals(bm)
        return bm
    band.add(wall(lambda a: 0.06, lambda a: 0.42, 0.74, 0.81, 2))
    point.add(wall(lambda a: 0.42, top, 0.74, 0.81, 3))
    rim.add(lathe_loop([(0.68, 0.0), (0.86, 0.0), (0.90, 0.06), (0.88, 0.14), (0.70, 0.14)], segs=48))
    rim.add(torus(0.80, 0.025, segs=48, rsegs=5), T(0, 0.40, 0))
    for k in range(n):
        a = TAU * (k + 0.5) / n
        tall = k % 2 == 0
        h = 0.42 + (0.62 if tall else 0.36)
        r = 0.81
        pearl.add(sphere(0.10 if tall else 0.07, 10, 6), T(r * math.cos(a), h + (0.07 if tall else 0.05), r * math.sin(a)))
    for k, j in enumerate(jewels):
        a = TAU * k / 4
        r = 0.83
        gem = lathe([(0, -0.03), (0.10, 0.0), (0.08, 0.05), (0, 0.06)], segs=8)
        j.add(gem, T(r * math.cos(a), 0.27, r * math.sin(a)) @ aim((math.cos(a), 0, math.sin(a))))


@prop("Ladle", view=(24, 16, 1.0))
def ladle(p, o):
    """A witch's wooden ladle: a turned handle with a hanging loop, an iron bowl
    full of glowing brew, and a drip."""
    shaft_p = p.part("Shaft", (124, 82, 46), "Wood", smooth=35)
    cup = p.part("Cup", (58, 60, 72), "Metal", smooth=35)
    brew = p.part("Brew", (120, 235, 80), "Neon")
    path = [Vector((0, 0.22, 0)), Vector((0, -0.4, 0.02)), Vector((0.02, -1.1, 0.06)), Vector((0.0, -1.55, 0.0))]
    sm = [Vector(v) for v in catmull(path, samples=4)]
    shaft_p.add(taper_tube(sm, 0.075, 0.06, sides=8))
    shaft_p.add(torus(0.09, 0.03, segs=12, rsegs=5, axis="Z"), T(0, 0.33, 0))
    shaft_p.add(sphere(0.09, 10, 6), T(0, 0.22, 0))
    bowl = lathe([(0, -2.10), (0.16, -2.09), (0.26, -2.02), (0.31, -1.90), (0.31, -1.80), (0.28, -1.80),
                  (0.28, -1.88), (0.24, -1.98), (0.14, -2.04), (0, -2.05)], segs=24, close=False)
    cup.add(bowl)
    cup.add(torus(0.295, 0.025, segs=24, rsegs=5), T(0, -1.80, 0))
    brew.add(lathe([(0, -1.86), (0.28, -1.86), (0.28, -1.83), (0, -1.82)], segs=24))
    brew.add(teardrop(0.035, 0.16, segs=6), T(0.30, -1.92, 0.0))


# ================================================================= NPC outfit pieces
# Handle space for these = the body part turned 180 degrees: +Z is the NPC's
# front, +X its left. Pete wears a coat and Wanda a dress over the body
# (see the Body pieces), so things that sit on the torso sit ~0.06 proud.

def carve_pumpkin(R0, H0, lobes, ldepth, segs, shapes, scale, cy, depth=0.10, face_y=0.0, back=None):
    """A lobed pumpkin with shapes (x, y outlines) carved into its +Z side; returns
    (carved body, glowing fills sitting at the bottom of each cut)."""
    zs = pumpkin_zsurf(R0, H0, lobes, ldepth)
    cutters, fills = bmesh_new(), bmesh_new()
    for pts in shapes:
        pts = densify([(x * scale, y * scale + face_y) for x, y in pts], 0.08)
        merge_into(cutters, projected_slab(pts, lambda x, y: R0 * 2, lambda x, y: zs(x, y) - depth, spacing=0.09))
        merge_into(fills, projected_slab(pts, lambda x, y: zs(x, y) - depth + 0.012,
                                         lambda x, y: zs(x, y) - depth - 0.08, spacing=0.09))
    body = boolean(pumpkin_body(R0, H0, lobes=lobes, depth=ldepth, segs=segs), cutters)
    xform(body, T(0, cy, 0))
    xform(fills, T(0, cy, 0))
    return body, fills


@prop("NpcPumpkinHead", view=(24, 8, 1.0))
def npc_pumpkin_head(p, o):
    """Pete's head: a big ribbed jack-o'-lantern with a friendly carved grin
    glowing from inside."""
    pk = p.part("Pumpkin", (255, 138, 31), "SmoothPlastic", smooth=40)
    face = p.part("Face", (255, 226, 46), "Neon")
    body, fills = carve_pumpkin(1.71, 2.79, 10, 0.10, 60, carve_face_shapes(), 1.45, 0.70, depth=0.12, face_y=0.12)
    pk.add(body)
    face.add(fills)


@prop("NpcCrookedHat", view=(24, 10, 1.0))
def npc_crooked_hat(p, o):
    """Pete's crooked old hat, sized for his pumpkin head: a floppy wavy brim, a
    tall cone that buckles and flops over, a purple patch and an orange band."""
    hat = p.part("Hat", (34, 32, 42), "Fabric", smooth=40)
    bandp = p.part("Band", (224, 106, 16), "Fabric", smooth=40)
    patch = p.part("Patch", (124, 52, 190), "Fabric", smooth=40)
    tilt = T(0.06, 1.97, 0.0) @ R("Z", 10)
    brim_wave = lambda a: 1 + 0.05 * math.cos(3 * a + 0.6)
    brim = lathe([(0.0, 0.03), (0.95, 0.03), (1.25, 0.0), (1.52, -0.08), (1.57, -0.12), (1.49, -0.13), (1.22, -0.08),
                  (0.95, -0.05), (0.0, -0.05)], segs=44, rmod=brim_wave)
    hat.add(brim, tilt)
    rings = []
    n = 12
    for j in range(n + 1):
        t = j / n
        r = lerp(0.96, 0.17, t ** 0.9)
        y = 1.62 * t
        bend = smoothstep((t - 0.5) / 0.5)
        cx = -0.08 * t + bend * 0.62
        cy = y - bend * 0.36
        ring = []
        for i in range(16):
            a = TAU * i / 16
            dent = 1 - 0.07 * math.sin(3 * a + t * 4)
            ring.append(Vector((cx + r * dent * math.cos(a), cy, r * dent * math.sin(a))))
        rings.append(ring)
    rings.append([Vector((rings[-1][0].x - 0.13, rings[-1][0].y - 0.04, 0.0))])
    hat.add(loft(rings, cap_start=True, cap_end=False), tilt @ T(0, 0.02, 0))
    bandp.add(lathe_loop([(0.93, 0.04), (1.01, 0.06), (1.00, 0.30), (0.91, 0.32)], segs=32), tilt)
    pa = slab(fillet_pts([(-0.20, -0.17), (0.21, -0.15), (0.19, 0.19), (-0.18, 0.17)], 0.03), 0.04, 0.0)
    patch.add(pa, tilt @ T(-0.42, 0.66, 0.58) @ R("Y", -30) @ R("X", -14))


def scarf_pieces(neck_y=1.0, r=0.62, tube_r=0.17):
    wrap, stripes = bmesh_new(), bmesh_new()
    ring = []
    for i in range(41):
        a = TAU * i / 40
        rr = r * (1 + 0.04 * math.sin(5 * a))
        ring.append(Vector((rr * 1.14 * math.cos(a), neck_y + 0.05 * math.sin(a + 0.8), rr * 0.96 * math.sin(a))))
    merge_into(wrap, sweep(ring, [tube_r * 2.2] * 41, [tube_r * 1.6] * 41, sides=10, point_end=False,
                           up=Vector((0, 1, 0))))
    # knot at the front left and two tails down the front
    merge_into(wrap, sphere(0.21, 12, 8, scale=(1.1, 1.0, 0.8)), T(0.30, neck_y - 0.06, 0.60))
    for k, (x0, L, sw) in enumerate(((0.28, 1.30, 0.06), (0.46, 1.00, -0.05))):
        path = [Vector((x0, neck_y - 0.14, 0.62)), Vector((x0 + sw, neck_y - 0.14 - L * 0.5, 0.645)),
                Vector((x0 + sw * 2, neck_y - 0.14 - L, 0.63))]
        path = [Vector(v) for v in catmull(path, samples=4)]
        merge_into(wrap, sweep(path, [0.34] * len(path), [0.08] * len(path), sides=6, point_end=False,
                               up=Vector((0, 0, 1))))
        for j in range(2):
            t = 0.45 + 0.25 * j
            c = path[int(t * (len(path) - 1))]
            merge_into(stripes, box(0.345, 0.08, 0.095, bevel=0.025, seg=1), T(c.x, c.y, c.z + 0.005))
        for f in range(4):                   # fringe
            fx = x0 + sw * 2 - 0.12 + f * 0.08
            merge_into(wrap, box(0.04, 0.16, 0.05), T(fx, neck_y - 0.14 - L - 0.07, 0.63))
    for a0 in (0.0, 1.6, 3.2, 4.8):          # stripes on the wrap
        ang = a0 + 0.4
        tng = Vector((-r * 1.14 * math.sin(ang), 0, r * 0.96 * math.cos(ang)))
        rg = sweep([Vector((0, -0.07, 0)), Vector((0, 0.07, 0))], [tube_r * 2.32] * 2, [tube_r * 1.72] * 2, sides=10,
                   point_end=False)
        merge_into(stripes, rg, T(r * 1.14 * math.cos(ang), neck_y + 0.05 * math.sin(ang + 0.8), r * 0.96 * math.sin(ang))
                   @ aim(tng, up=(0, 1, 0)))
    return wrap, stripes


@prop("NpcScarf", view=(16, 8, 1.0))
def npc_scarf(p, o):
    """A chunky knitted scarf wrapped round the neck, knotted at the front with
    two striped tails ending in a fringe."""
    sc = p.part("Scarf", (138, 52, 218), "Fabric", smooth=55)
    st = p.part("Stripes", (255, 200, 60), "Fabric", smooth=55)
    wrap, stripes = scarf_pieces()
    sc.add(wrap)
    st.add(stripes)


@prop("NpcCoatPatches", view=(18, 6, 1.0))
def npc_coat_patches(p, o):
    """Pete's coat details: two stitched-on patches, three big buttons and the
    ragged coat tails hanging below the waist."""
    red = p.part("PatchRed", (192, 85, 43), "Fabric", smooth=40)
    blue = p.part("PatchBlue", (63, 127, 191), "Fabric", smooth=40)
    buttons = p.part("Buttons", (255, 226, 46), "SmoothPlastic", smooth=40)
    tails = p.part("Tails", (128, 82, 38), "Fabric", smooth=40)
    stitch = p.part("Stitches", (60, 40, 22), "Fabric", smooth=40)
    zf = 0.565

    def patch(part, cx, cy, w, h, rot):
        pts = wobble_pts(fillet_pts([(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)], 0.04), 0.03, 3, cx)
        m = T(cx, cy, zf + 0.015) @ R("Z", rot)
        part.add(slab(pts, 0.04, 0.012, seg=1), m)
        for k in range(4):                   # cross stitches along each side
            for j in range(3):
                t = (j + 0.5) / 3
                if k == 0:
                    x, y, a = lerp(-w / 2, w / 2, t), h / 2, 0
                elif k == 1:
                    x, y, a = lerp(-w / 2, w / 2, t), -h / 2, 0
                elif k == 2:
                    x, y, a = w / 2, lerp(-h / 2, h / 2, t), 90
                else:
                    x, y, a = -w / 2, lerp(-h / 2, h / 2, t), 90
                for sgn in (1, -1):
                    stitch.add(box(0.11, 0.022, 0.02), m @ T(x, y, 0.025) @ R("Z", a + sgn * 40))
    patch(red, -0.50, 0.40, 0.58, 0.52, -12)
    patch(blue, 0.50, -0.50, 0.48, 0.44, 9)
    for y in (0.95, 0.55, 0.15):
        b = lathe_z([(0, 0.0), (0.10, 0.0), (0.115, 0.025), (0.10, 0.05), (0.07, 0.045), (0, 0.035)], segs=14)
        buttons.add(b, T(0, y, zf))
    for sx in (-1, 1):
        pts = [(0.0, 0.0), (0.92, 0.0), (0.95, -0.55), (0.80, -0.68), (0.66, -0.58), (0.50, -0.72), (0.34, -0.60),
               (0.16, -0.74), (0.02, -0.62)]
        pts = [(sx * x + (0.02 if sx > 0 else -0.02), y) for x, y in pts]
        if sx < 0:
            pts = list(reversed(pts))
        tl = slab(pts, 0.10, 0.03, seg=1)
        tails.add(tl, T(0, -0.92, 0.52) @ R("X", 6))


@prop("NpcStrawCollar", view=(20, 16, 1.0))
def npc_straw_collar(p, o):
    """Tufts of straw poking out all round the collar."""
    straw = p.part("Straw", (255, 217, 102), "Fabric", smooth=30)
    for k in range(11):
        a = TAU * k / 11 + 0.2
        d = Vector((math.cos(a), 0.55, math.sin(a) * 0.9))
        base = Vector((0.62 * math.cos(a), 1.06, 0.48 * math.sin(a)))
        straw.add(straw_tuft(base, d, 0.42, n=4, spread=26, width=0.07, seed=k, droop=0.08))


@prop("NpcStrawCuff", view=(20, 4, 1.0))
def npc_straw_cuff(p, o):
    """Straw sticking out of a sleeve or trouser leg."""
    straw = p.part("Straw", (255, 217, 102), "Fabric", smooth=30)
    for k in range(9):
        a = TAU * k / 9 + 0.3
        d = Vector((0.45 * math.cos(a), -1.0, 0.45 * math.sin(a)))
        base = Vector((0.40 * math.cos(a), -0.90, 0.40 * math.sin(a)))
        straw.add(straw_tuft(base, d, 0.50, n=3, spread=20, width=0.075, seed=10 + k, droop=0.0))


@prop("NpcLantern", view=(22, 10, 1.0))
def npc_lantern(p, o):
    """An old iron lantern swinging from Pete's hand: a carry loop, a peaked cap,
    four corner posts round warm glass and a flickering flame."""
    frame = p.part("Frame", (43, 43, 51), "Metal", smooth=30)
    flame = p.part("Flame", (255, 176, 32), "Neon")
    glass = p.part("Glass", (255, 214, 140), "Glass", transparency=0.55, smooth=30)
    frame.add(torus(0.17, 0.035, segs=16, rsegs=5, axis="Z"), T(0, -1.06, 0))
    frame.add(lathe([(0, -1.18), (0.07, -1.18), (0.30, -1.36), (0.36, -1.42), (0.36, -1.46), (0, -1.46)], segs=4,
                    phase=math.pi / 4))
    frame.add(lathe([(0, -2.18), (0.36, -2.18), (0.36, -2.10), (0.31, -2.06), (0, -2.06)], segs=4, phase=math.pi / 4))
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        frame.add(cylinder(0.035, 0.66, segs=6), T(0.33 * math.cos(a), -1.76, 0.33 * math.sin(a)))
    glass.add(box(0.44, 0.60, 0.44), T(0, -1.76, 0))
    flame.add(teardrop(0.09, 0.32, segs=8), T(0, -1.68, 0) @ R("X", 180))
    flame.add(sphere(0.05, 8, 5), T(0, -1.98, 0))


@prop("NpcBat", view=(16, 10, 1.0))
def npc_bat(p, o):
    """Pete's pet bat: a round fuzzy body, big pointy ears, scalloped wings, glowing
    eyes and two tiny fangs."""
    bat = p.part("Bat", (62, 44, 88), "SmoothPlastic", smooth=40)
    eyes = p.part("Eyes", (255, 226, 46), "Neon")
    fangs = p.part("Fangs", (250, 248, 240), "SmoothPlastic", smooth=40)
    bat.add(sphere(0.30, 16, 10, scale=(1.0, 1.05, 0.95)))
    for sx in (-1, 1):
        ear = lathe([(0, 0), (0.09, 0.0), (0.0, 0.26)], segs=6)
        bat.add(ear, T(sx * 0.14, 0.22, 0.0) @ R("Z", -sx * 18))
        wing = slab([(x, y) for x, y in bat_wing_pts(0.95, 0.62, scallops=3)], 0.05, 0.015, seg=1)
        m = T(sx * 0.22, 0.05, -0.04) @ (S(-1, 1, 1) if sx < 0 else S(1)) @ R("Y", -14) @ R("Z", 8)
        bat.add(wing, m)
        bat.add(sphere(0.05, 6, 4, scale=(1, 1.4, 1)), T(sx * 0.10, -0.31, 0.02))
        eyes.add(sphere(0.065, 10, 6, scale=(1.0, 1.25, 0.6)), T(sx * 0.11, 0.06, 0.265))
        fangs.add(lathe([(0, 0), (0.025, 0.0), (0, -0.06)], segs=5), T(sx * 0.045, -0.07, 0.27))


@prop("NpcWitchHat", view=(22, 12, 1.0))
def npc_witch_hat(p, o):
    """Wanda's witch hat: a wide wavy brim, a tall cone with a bent tip, a black
    band with a gold buckle and a little glowing star."""
    hat = p.part("Hat", (106, 43, 194), "Fabric", smooth=40)
    bandp = p.part("Band", (30, 28, 38), "Fabric", smooth=40)
    buckle = p.part("Buckle", (255, 210, 58), "Metal", smooth=30)
    star = p.part("Star", (255, 226, 46), "Neon")
    wave = lambda a: 1 + 0.045 * math.cos(4 * a + 0.3)
    hat.add(lathe([(0.0, 0.50), (0.84, 0.50), (1.16, 0.47), (1.42, 0.41), (1.46, 0.37), (1.38, 0.36), (1.12, 0.41),
                   (0.84, 0.44), (0.0, 0.44)], segs=44, rmod=wave))
    rings = []
    n = 14
    for j in range(n + 1):
        t = j / n
        r = lerp(0.80, 0.07, t ** 0.85)
        bend = 0.62 * smoothstep((t - 0.62) / 0.38)
        cz = -bend * 0.85
        cy = 0.48 + 2.72 * t - bend * 0.38
        ring = [Vector((r * math.cos(TAU * i / 18), cy, cz + r * math.sin(TAU * i / 18))) for i in range(18)]
        rings.append(ring)
    rings.append([Vector((0, rings[-1][0].y - 0.06, rings[-1][0].z - 0.12 - 0.07))])
    hat.add(loft(rings, cap_start=True, cap_end=False))
    bandp.add(lathe_loop([(0.79, 0.50), (0.83, 0.52), (0.80, 0.84), (0.74, 0.86)], segs=32))
    bk = slab_holes(fillet_pts([(-0.2, -0.17), (0.2, -0.17), (0.2, 0.17), (-0.2, 0.17)], 0.04),
                    [fillet_pts([(-0.1, -0.08), (0.1, -0.08), (0.1, 0.08), (-0.1, 0.08)], 0.02)], 0.06)
    buckle.add(bk, T(0, 0.68, 0.82) @ R("X", -8))
    star.add(star3d(0.20, 0.09, 0.03, 0.05), T(0.10, 1.62, 0.53) @ R("X", -17) @ R("Z", 10))


@prop("NpcWitchHair", view=(200, 10, 1.0))
def npc_witch_hair(p, o):
    """Wanda's bright orange hair: a thick wavy curtain round the back and sides
    of her head (open at the face), and two braids over her shoulders tied off
    with green ribbons."""
    hair = p.part("Hair", (232, 97, 42), "Fabric", smooth=50)
    ties = p.part("Ties", (82, 194, 52), "Fabric", smooth=45)
    a0, a1 = math.radians(132), math.radians(408)            # open between 48 and 132 degrees (the face)
    n = 34
    rings = []
    for j, (y, r) in enumerate(((0.62, 0.50), (0.48, 0.66), (0.20, 0.70), (-0.15, 0.71), (-0.45, 0.73), (-0.62, 0.76))):
        ring = []
        for i in range(n + 1):
            a = lerp(a0, a1, i / n)
            yy = y
            if j == 5:
                yy = y - 0.10 * (0.5 + 0.5 * math.cos(9 * (a - a0)))   # wavy bottom edge
            ring.append(Vector((r * math.cos(a), yy, r * 0.98 * math.sin(a) - 0.04)))
        rings.append(ring)
    hair.add(thicken(loft(rings, cap_start=False, cap_end=False, closed=False), 0.16))
    for sx in (-1, 1):                       # locks framing the face
        lock = [Vector((sx * 0.62, 0.40, 0.16)), Vector((sx * 0.66, 0.0, 0.24)), Vector((sx * 0.62, -0.40, 0.22)),
                Vector((sx * 0.56, -0.62, 0.16))]
        hair.add(sweep([Vector(v) for v in catmull(lock, samples=3)], [0.22, 0.22, 0.24, 0.24, 0.22, 0.20, 0.16, 0.12, 0.10, 0.0],
                       [0.16, 0.16, 0.17, 0.17, 0.16, 0.15, 0.12, 0.10, 0.08, 0.0], sides=8, point_end=True))
    for sx in (-1, 1):                       # braids
        pts = [Vector((sx * 0.62, -0.30, -0.20)), Vector((sx * 0.72, -0.70, -0.10)), Vector((sx * 0.74, -1.10, 0.02)),
               Vector((sx * 0.70, -1.36, 0.08))]
        sm = [Vector(v) for v in catmull(pts, samples=3)]
        for i, c in enumerate(sm[:-1]):
            hair.add(sphere(0.15 - 0.004 * i, 8, 5, scale=(1.0, 0.85, 1.0)), T(*c) @ R("Z", 25 * sx * (1 if i % 2 else -1)))
        end = sm[-1]
        ties.add(torus(0.11, 0.045, segs=12, rsegs=5), T(*end) @ T(0, 0.02, 0))
        for side in (1, -1):
            ties.add(sphere(0.09, 8, 5, scale=(1.4, 0.7, 0.6)), T(*end) @ T(side * 0.12, 0.05, 0.06) @ R("Z", side * 30))
        hair.add(lathe([(0, -0.28), (0.09, -0.22), (0.14, -0.08), (0.11, 0.0), (0, 0.02)], segs=8), T(*end) @ T(0, -0.05, 0))


@prop("NpcBelt", view=(18, 10, 1.0))
def npc_belt(p, o):
    """Wanda's belt: a black band round her dress, a big square gold buckle and
    a little green pouch with a button flap."""
    belt = p.part("Belt", (30, 28, 38), "Fabric", smooth=40)
    buckle = p.part("Buckle", (255, 210, 58), "Metal", smooth=30)
    pouch = p.part("Pouch", (82, 194, 52), "Fabric", smooth=40)
    loop = superellipse_pts(1.12, 0.62, p=3.2, n=48)
    ring = slab_holes(loop, [superellipse_pts(1.04, 0.54, p=3.2, n=48)], 0.30, 0.0)
    belt.add(ring, T(0, -0.60, 0) @ R("X", -90))
    bk = slab_holes(fillet_pts([(-0.27, -0.22), (0.27, -0.22), (0.27, 0.22), (-0.27, 0.22)], 0.05),
                    [fillet_pts([(-0.14, -0.10), (0.14, -0.10), (0.14, 0.10), (-0.14, 0.10)], 0.03)], 0.08, 0.02, seg=1)
    buckle.add(bk, T(0, -0.60, 0.66))
    pouch.add(box(0.40, 0.42, 0.24, bevel=0.08, seg=2), T(0.72, -0.86, 0.62))
    pouch.add(box(0.42, 0.18, 0.26, bevel=0.06, seg=2), T(0.72, -0.68, 0.63))
    buckle.add(sphere(0.045, 8, 5), T(0.72, -0.72, 0.765))


@prop("NpcBroom", view=(20, 8, 1.0))
def npc_broom(p, o):
    """Wanda's broom: a knobbly crooked stick held at her side, a fat flared
    bundle of bristles and a red binding."""
    stick = p.part("Stick", (138, 90, 43), "Wood", smooth=35)
    bris = p.part("Bristles", (232, 193, 90), "Fabric", smooth=30)
    bind = p.part("Binding", (224, 20, 28), "Fabric", smooth=40)
    x0 = 0.66
    path = [Vector((x0 + 0.02, -2.25, 0.0)), Vector((x0, -1.0, 0.02)), Vector((x0 - 0.04, 0.3, -0.03)),
            Vector((x0 + 0.03, 1.4, 0.02)), Vector((x0 - 0.06, 1.95, 0.05))]
    sm = [Vector(v) for v in catmull(path, samples=4)]
    stick.add(taper_tube(sm, 0.11, 0.085, sides=8))
    stick.add(sphere(0.13, 10, 6), T(*sm[-1]))
    for y in (-0.2, 0.9):
        stick.add(sphere(0.13, 8, 5, scale=(1.0, 0.6, 1.0)), T(x0 - 0.02, y, 0.0))
    # bristles: a flared bundle of tapered tufts
    for k in range(16):
        a = TAU * k / 16
        r0 = 0.16
        top = Vector((x0 + r0 * math.cos(a), -2.10, r0 * math.sin(a)))
        bot = Vector((x0 + 0.52 * math.cos(a + 0.12), -3.0, 0.52 * math.sin(a + 0.12)))
        mid = top.lerp(bot, 0.5) + Vector((0.10 * math.cos(a), 0, 0.10 * math.sin(a)))
        bris.add(sweep([top, mid, bot], [0.26, 0.30, 0.16], [0.26, 0.30, 0.16], sides=6, point_end=False))
    bris.add(lathe([(0, -2.95), (0.40, -2.95), (0.30, -2.40), (0.17, -2.05), (0, -2.0)], segs=16), T(x0, 0, 0))
    bind.add(lathe_loop([(0.17, -2.22), (0.21, -2.20), (0.21, -2.04), (0.17, -2.02)], segs=16), T(x0, 0, 0))
    bind.add(torus(0.20, 0.03, segs=16, rsegs=4), T(x0, -2.12, 0))


@prop("BroomPumpkin", view=(200, 12, 1.0))
def broom_pumpkin(p, o):
    """A jack-o'-lantern: round ribbed pumpkin, a glowing grin, a curly stem and
    a leaf (replaces the old block-built one, same size and spot)."""
    pk = p.part("Pumpkin", (240, 116, 18), "SmoothPlastic", smooth=40)
    glow = p.part("Glow", (255, 201, 60), "Neon")
    stem = p.part("Stem", (91, 122, 46), "SmoothPlastic", smooth=45)
    c = o.center("Glow") * 0 if o else Vector((0, 0, 0))
    # old body centre (Handle space) and the side its face was on (-Z)
    body, fills = carve_pumpkin(1.42, 1.95, 10, 0.10, 56, carve_face_shapes(), 1.15, 0.0, depth=0.11, face_y=-0.05)
    turn = R("Y", 180)
    cy = 0.02
    pk.add(body, T(0, cy, 0) @ turn)
    glow.add(fills, T(0, cy, 0) @ turn)
    sp = [Vector((0, 0.80, 0)), Vector((0.02, 1.10, 0.0)), Vector((0.10, 1.32, -0.02)), Vector((0.24, 1.42, -0.04))]
    stem.add(taper_tube([Vector(v) for v in catmull(sp, samples=3)], 0.17, 0.12, sides=7), T(0, cy, 0))
    stem.add(slab(pumpkin_leaf(0.42), 0.05, 0.015, seg=1), T(-0.15, cy + 0.88, -0.05) @ aim((-0.6, 0.25, 0.75)))


# ================================================================= the trapdoor

@prop("Trapdoor", view=(26, 38, 1.0))
def trapdoor(p, o):
    """A hidden trapdoor: twelve wedge flaps of turf that drop open round the
    rim. Grassy tops with a few tufts, soil underneath (seen when it opens).
    The flaps, hinges and the black void keep their old positions."""
    flaps = o.parts("Hinge")
    rng = random.Random(8)
    for k, (hsize, hm) in enumerate(flaps):
        hinge_pos = hm.translation
        ang = math.atan2(hinge_pos.z, hinge_pos.x)
        rot = Matrix.Rotation(-ang, 4, "Y")               # local +X = out along this flap
        R0 = 4.5
        half = math.tan(math.radians(15)) * R0 - 0.015
        tri = [(0.06, 0.0), (R0 - 0.01, -half), (R0 - 0.01, half)]
        turf = p.part("Turf", (96, 170, 70), "SmoothPlastic", smooth=40, model=k, cast_shadow=True)
        soil = p.part("Soil", (112, 76, 44), "SmoothPlastic", smooth=40, model=k, cast_shadow=True)
        tufts = p.part("Grass", (78, 150, 56), "SmoothPlastic", smooth=40, model=k, cast_shadow=True)
        top = slab(tri, 0.14, 0.03, seg=1)                    # in local XY: x out, y across
        turf.add(top, T(0, 0.13, 0) @ rot @ R("X", 90))
        bot = slab(tri, 0.18, 0.0)
        soil.add(bot, T(0, -0.03, 0) @ rot @ R("X", 90))
        for j in range(2):
            rr = rng.uniform(1.6, 4.0)
            off = rng.uniform(-0.5, 0.5) * rr / R0
            pos = rot @ Vector((rr, 0.2, off))
            for b in range(3):
                blade = lathe([(0, 0), (0.035, 0.0), (0, 0.22 + 0.06 * b)], segs=4)
                tufts.add(blade, T(*pos) @ R("Y", b * 120 + j * 40) @ R("Z", 20 if b else 0))


# ================================================================= NPC bodies
# Clothes welded over each R6 limb (the limbs themselves are hidden), in the
# same Handle space as the outfit pieces: +Z front, +X the NPC's left.

BODY = {
    "Pete": [("PeteCoat", "Torso"), ("PeteSleeve", "Right Arm"), ("PeteSleeve", "Left Arm"),
             ("PeteTrousers", "Right Leg"), ("PeteTrousers", "Left Leg")],
    "Wanda": [("WandaDress", "Torso"), ("WandaSleeveR", "Right Arm"), ("WandaSleeveL", "Left Arm"),
              ("WandaLeg", "Right Leg"), ("WandaLeg", "Left Leg"), ("WandaNose", "Head")],
}
HIDE = {"Pete": ["Torso", "Left Arm", "Right Arm", "Left Leg", "Right Leg"],
        "Wanda": ["Torso", "Left Arm", "Right Arm", "Left Leg", "Right Leg"]}


def shell(stations, n=32, p=3.0, cap_start=True, cap_end=True):
    """Loft of rounded-rectangle sections [(y, rx, rz[, dx, dz])] bottom to top."""
    rings = []
    for st in stations:
        y, rx, rz = st[:3]
        dx = st[3] if len(st) > 3 else 0.0
        dz = st[4] if len(st) > 4 else 0.0
        rings.append([Vector((x, y, z)) for x, z in superellipse_pts(rx, rz, p=p, n=n, cx=dx, cy=dz)])
    return loft(rings, cap_start=cap_start, cap_end=cap_end)


def station_rz(stations, y):
    for a, b in zip(stations, stations[1:]):
        if a[0] <= y <= b[0]:
            t = (y - a[0]) / (b[0] - a[0])
            return lerp(a[1], b[1], t), lerp(a[2], b[2], t)
    return stations[-1][1], stations[-1][2]


def on_front(stations, p, pts, lift, depth=0.05, spacing=0.06):
    """A slab over an outline (x, y) lying on the front (+Z) of a shell()."""
    def zf(x, y):
        rx, rz = station_rz(stations, y)
        k = max(1e-4, 1 - abs(x / rx) ** p)
        return rz * k ** (1 / p)
    return projected_slab(densify(pts, spacing), lambda x, y: zf(x, y) + lift, lambda x, y: zf(x, y) - depth,
                          spacing=spacing)


def hem_skirt(stations, teeth, depth, n_per=4, p=3.0, thick=0.05):
    """Open flared skirt: rounded sections, the last ring cut into zigzag points."""
    n = teeth * n_per
    rings = []
    for j, (y, rx, rz) in enumerate(stations):
        ring = []
        for i, (x, z) in enumerate(superellipse_pts(rx, rz, p=p, n=n, a0=math.pi / 2)):
            yy = y
            if j == len(stations) - 1:
                ph = (i % n_per) / n_per
                yy = y + depth * abs(ph - 0.5) * 2
            ring.append(Vector((x, yy, z)))
        rings.append(ring)
    return thicken(loft(rings, cap_start=False, cap_end=False), thick), rings[-1]


PETE_COAT = [(-1.10, 1.10, 0.60), (-0.86, 1.06, 0.585), (-0.30, 1.03, 0.565), (0.45, 1.03, 0.56), (0.92, 1.00, 0.555),
             (0.99, 0.93, 0.53), (1.05, 0.72, 0.45), (1.09, 0.42, 0.32)]


@prop("PeteCoat", kind="NpcBody", view=(24, 8, 1.0))
def pete_coat(p, o):
    """Pete's old farm coat: a roomy patched coat flaring a little at the hem,
    dark lapels, a centre seam and a rope belt knotted at the front."""
    coat = p.part("Coat", (138, 90, 43), "Fabric", smooth=45, cast_shadow=True)
    dark = p.part("Lapels", (100, 64, 30), "Fabric", smooth=45, cast_shadow=True)
    rope = p.part("Rope", (204, 168, 98), "Fabric", smooth=50, cast_shadow=True)
    coat.add(shell(PETE_COAT, n=40, p=3.2))
    dark.add(on_front(PETE_COAT, 3.2, [(-0.03, -1.07), (0.03, -1.07), (0.03, 0.05), (-0.03, 0.05)], 0.012))
    for sx in (-1, 1):
        lap = [(sx * 0.07, 0.60), (sx * 0.46, 0.98), (sx * 0.20, 1.06), (sx * 0.06, 0.92)]
        if sx < 0:
            lap = list(reversed(lap))
        dark.add(on_front(PETE_COAT, 3.2, lap, 0.03))
    ring = []
    for x, z in superellipse_pts(1.085, 0.605, p=3.2, n=48):
        ring.append(Vector((x, -0.84, z)))
    ring.append(ring[0].copy())
    rope.add(tube(ring, 0.055, sides=7))
    rope.add(sphere(0.11, 10, 6), T(-0.34, -0.84, 0.64))
    for k, (dx, L) in enumerate(((-0.08, 0.40), (0.07, 0.30))):
        end = [Vector((-0.34 + dx * 0.3, -0.86, 0.66)), Vector((-0.34 + dx, -0.86 - L * 0.6, 0.68)),
               Vector((-0.34 + dx * 1.4, -0.86 - L, 0.66))]
        rope.add(tube(end, 0.045, sides=6))
        rope.add(sphere(0.06, 6, 4, scale=(1, 1.4, 1)), T(*end[-1]) @ T(0, -0.03, 0))


@prop("PeteSleeve", kind="NpcBody", view=(30, 8, 1.0))
def pete_sleeve(p, o):
    """A baggy coat sleeve with a dark turned-back cuff; straw pokes out of it."""
    sl = p.part("Sleeve", (138, 90, 43), "Fabric", smooth=45, cast_shadow=True)
    cuff = p.part("Cuff", (100, 64, 30), "Fabric", smooth=45, cast_shadow=True)
    sl.add(shell([(-0.86, 0.47, 0.47), (-0.30, 0.45, 0.45), (0.50, 0.46, 0.46), (0.92, 0.46, 0.46),
                  (1.02, 0.40, 0.40), (1.08, 0.26, 0.26)], n=28, p=2.4))
    cuff.add(lathe_loop([(0.40, -1.0), (0.53, -1.0), (0.55, -0.84), (0.47, -0.78), (0.40, -0.80)], segs=28))


@prop("PeteTrousers", kind="NpcBody", view=(30, 8, 1.0))
def pete_trousers(p, o):
    """A baggy patched trouser leg with a rolled cuff."""
    tr = p.part("Trousers", (74, 53, 36), "Fabric", smooth=45, cast_shadow=True)
    patch = p.part("Patch", (196, 150, 60), "Fabric", smooth=45, cast_shadow=True)
    st = [(-0.80, 0.48, 0.48), (-0.50, 0.46, 0.46), (0.30, 0.46, 0.46), (0.90, 0.48, 0.48), (1.02, 0.46, 0.46),
          (1.08, 0.30, 0.30)]
    tr.add(shell(st, n=28, p=2.6))
    tr.add(lathe_loop([(0.40, -0.98), (0.52, -0.98), (0.54, -0.78), (0.46, -0.74), (0.40, -0.76)], segs=28))
    pts = wobble_pts(fillet_pts([(-0.19, -0.17), (0.19, -0.16), (0.18, 0.17), (-0.18, 0.16)], 0.04), 0.04, 3, 1.3)
    pts = [(x * math.cos(0.15) - y * math.sin(0.15), y * math.cos(0.15) + x * math.sin(0.15) + 0.02) for x, y in pts]
    patch.add(on_front(st, 2.6, pts, 0.025))


WANDA_BODICE = [(-0.78, 1.00, 0.52), (-0.60, 1.02, 0.53), (-0.30, 0.98, 0.52), (0.30, 1.00, 0.53), (0.65, 1.00, 0.54),
                (0.90, 0.97, 0.52), (0.99, 0.86, 0.47), (1.05, 0.62, 0.38), (1.08, 0.36, 0.28)]


@prop("WandaDress", kind="NpcBody", view=(24, 8, 1.0))
def wanda_dress(p, o):
    """Wanda's witch dress: a fitted purple bodice and a wide flared skirt with a
    zigzag hem trimmed in orange."""
    dress = p.part("Dress", (106, 43, 194), "Fabric", smooth=45, cast_shadow=True)
    trim = p.part("Trim", (255, 138, 31), "Fabric", smooth=45, cast_shadow=True)
    dress.add(shell(WANDA_BODICE, n=40, p=3.0))
    skirt_st = [(-0.66, 1.02, 0.54), (-0.90, 1.12, 0.62), (-1.30, 1.27, 0.74), (-1.80, 1.40, 0.85), (-2.22, 1.48, 0.92)]
    skirt, hem = hem_skirt(skirt_st, teeth=9, depth=-0.22, n_per=4, p=3.0, thick=0.05)
    dress.add(skirt)
    a = [Vector((v.x * 1.018, v.y + 0.05, v.z * 1.018)) for v in hem]
    b = [Vector((v.x * 1.012, v.y + 0.17, v.z * 1.012)) for v in hem]
    band = loft([a, b], cap_start=False, cap_end=False)
    trim.add(thicken(band, 0.03))


def bell_cuff(r0, r1, y0, y1, teeth=7, depth=0.15, thick=0.04):
    n = teeth * 4
    rings = []
    for j in range(4):
        t = j / 3
        y = lerp(y0, y1, t)
        r = lerp(r0, r1, t ** 1.6)
        ring = []
        for i in range(n):
            a = TAU * i / n
            yy = y
            if j == 3:
                ph = (i % 4) / 4
                yy = y1 - depth * abs(ph - 0.5) * 2
            ring.append(Vector((r * math.cos(a), yy, r * math.sin(a))))
        rings.append(ring)
    return thicken(loft(rings, cap_start=False, cap_end=False), thick)


def wanda_sleeve(p, fist):
    sl = p.part("Sleeve", (106, 43, 194), "Fabric", smooth=45, cast_shadow=True)
    hand = p.part("Hand", (143, 212, 106), "SmoothPlastic", smooth=50, cast_shadow=True)
    sl.add(shell([(-0.60, 0.40, 0.40), (0.30, 0.44, 0.44), (0.88, 0.46, 0.46), (1.0, 0.40, 0.40), (1.07, 0.26, 0.26)],
                 n=28, p=2.4))
    sl.add(bell_cuff(0.40, 0.66, -0.42, -1.02, teeth=7, depth=0.16))
    hand.add(cylinder(0.17, 0.4, segs=12), T(0, -0.86, 0))
    if fist:
        hand.add(box(0.40, 0.40, 0.42, bevel=0.14, seg=3), T(0.46, -1.16, 0.0))
        hand.add(capsule(0.08, -0.12, 0.12, segs=8, rings=2), T(0.46, -1.06, 0.22) @ R("Z", 90))
    else:
        hand.add(box(0.20, 0.44, 0.36, bevel=0.09, seg=3), T(0, -1.22, 0.02))
        hand.add(capsule(0.075, 0.0, 0.26, segs=8, rings=2), T(0.02, -1.10, 0.14) @ R("X", 62))


@prop("WandaSleeveR", kind="NpcBody", view=(30, 8, 1.0))
def wanda_sleeve_r(p, o):
    """Wanda's right sleeve: a fitted purple sleeve ending in a flared zigzag
    bell cuff, and her green hand."""
    wanda_sleeve(p, fist=False)


@prop("WandaSleeveL", kind="NpcBody", view=(30, 8, 1.0))
def wanda_sleeve_l(p, o):
    """Wanda's left sleeve, her hand closed round the broom handle."""
    wanda_sleeve(p, fist=True)


@prop("WandaLeg", kind="NpcBody", view=(40, 8, 1.0))
def wanda_leg(p, o):
    """A stripy stocking (black with orange bands) and a pointy witch shoe with a
    curled toe and a gold buckle."""
    sock = p.part("Stocking", (34, 30, 44), "Fabric", smooth=45, cast_shadow=True)
    stripes = p.part("Stripes", (255, 138, 31), "Fabric", smooth=45, cast_shadow=True)
    shoe = p.part("Shoe", (52, 34, 70), "SmoothPlastic", smooth=40, cast_shadow=True)
    buckle = p.part("Buckle", (255, 210, 58), "Metal", smooth=30, cast_shadow=True)
    st = [(-0.80, 0.30, 0.30), (-0.60, 0.30, 0.30), (-0.20, 0.33, 0.33), (0.40, 0.37, 0.37), (1.0, 0.40, 0.40),
          (1.06, 0.30, 0.30)]
    sock.add(shell(st, n=24, p=2.2))
    for y in (-0.62, -0.38, -0.14, 0.10, 0.34, 0.58):
        r = station_rz(st, y)[0] + 0.012
        stripes.add(lathe_loop([(r - 0.02, y - 0.06), (r, y - 0.06), (r, y + 0.06), (r - 0.02, y + 0.06)], segs=24))
    path = [Vector((0, -0.80, -0.20)), Vector((0, -0.81, 0.12)), Vector((0, -0.84, 0.42)), Vector((0, -0.83, 0.68)),
            Vector((0, -0.74, 0.86)), Vector((0, -0.60, 0.90)), Vector((0, -0.52, 0.84))]
    shoe.add(sweep(path, [0.62, 0.62, 0.50, 0.30, 0.17, 0.10, 0.0], [0.40, 0.38, 0.28, 0.17, 0.11, 0.07, 0.0],
                   sides=12, point_end=True, up=Vector((0, 1, 0))))
    shoe.add(cylinder(0.33, 0.34, segs=16, bevel=0.04), T(0, -0.80, 0.0))
    shoe.add(box(0.56, 0.08, 0.5, bevel=0.03, seg=1), T(0, -0.97, -0.05))
    bk = slab_holes(fillet_pts([(-0.12, -0.09), (0.12, -0.09), (0.12, 0.09), (-0.12, 0.09)], 0.02),
                    [fillet_pts([(-0.06, -0.04), (0.06, -0.04), (0.06, 0.04), (-0.06, 0.04)], 0.01)], 0.04)
    buckle.add(bk, T(0, -0.64, 0.30) @ R("X", -62))


@prop("WandaNose", kind="NpcBody", view=(60, 6, 1.0))
def wanda_nose(p, o):
    """A long pointy witch nose (with a wart) for Wanda's face."""
    nose = p.part("Nose", (143, 212, 106), "SmoothPlastic", smooth=50, cast_shadow=True)
    wart = p.part("Wart", (96, 168, 70), "SmoothPlastic", smooth=50, cast_shadow=True)
    path = [Vector((0, 0.05, 0.46)), Vector((0, 0.01, 0.70)), Vector((0, -0.06, 0.92)), Vector((0, -0.07, 1.06)),
            Vector((0, -0.03, 1.14))]
    nose.add(sweep(path, [0.30, 0.22, 0.14, 0.08, 0.0], [0.28, 0.20, 0.13, 0.07, 0.0], sides=12, point_end=True,
                   up=Vector((0, 1, 0))))
    wart.add(sphere(0.05, 8, 6), T(0.07, -0.02, 0.84))
