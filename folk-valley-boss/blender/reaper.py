"""The Grim Reaper boss: a big cartoon reaper (about 21 studs to the hood tip,
24 with the scythe raised) built from rigid pieces for a Motor6D rig.

Roblox space, model facing -Z (the way Roblox characters face), feet on y = 0.
Every part belongs to a bone (the Part1 of a Motor6D, R15 names where there is
one); the part named after its bone is the one the joint drives and the other
parts of that bone are welded to it.
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROPS_BLENDER = os.path.join(os.path.dirname(os.path.dirname(HERE)), "folk-valley-props", "blender")
sys.path.insert(0, PROPS_BLENDER)

import plib  # noqa: E402,I001
import bmesh  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402
from plib import (TAU, T, R, S, lerp, smoothstep, merge_into, xform, box, cylinder, sphere, torus, lathe,  # noqa: E402,F401
                  slab, loft, sweep, catmull, capsule, boolean, projected_slab, star3d, superellipse_pts, thicken,
                  tube, taper_tube, fix_normals, lathe_loop, aim, densify, bmesh_new)
from pdefs import fillet_pts, offset_poly  # noqa: E402

# ---------------------------------------------------------------- palette

ROBE = (54, 36, 80)
MANTLE = (82, 54, 120)
HOOD = (64, 42, 96)
SHADOW = (14, 10, 22)
BONE = (238, 232, 212)
GLOW = (122, 255, 106)
ROPE = (176, 132, 82)
GOLD = (232, 184, 66)
SAND = (255, 196, 82)
WOOD = (70, 48, 36)
STEEL = (60, 64, 82)
SILVER = (176, 182, 202)
WRAP = (112, 62, 176)

# ---------------------------------------------------------------- rig: (motor, part0, part1, pivot)

HRP_CENTER = (0.0, 8.6, 0.0)
HRP_SIZE = (5.0, 5.0, 3.0)
RIG = [
    ("Root", "HumanoidRootPart", "LowerTorso", (0.0, 8.6, 0.0)),
    ("Waist", "LowerTorso", "UpperTorso", (0.0, 9.5, 0.0)),
    ("Neck", "UpperTorso", "Head", (0.0, 15.3, -0.1)),
    ("Jaw", "Head", "Jaw", (0.0, 16.3, -0.05)),
    ("RightShoulder", "UpperTorso", "RightUpperArm", (3.0, 14.3, 0.0)),
    ("RightElbow", "RightUpperArm", "RightLowerArm", (3.85, 10.65, 0.0)),
    ("RightWrist", "RightLowerArm", "RightHand", (4.6, 7.25, 0.0)),
    ("ScytheGrip", "RightHand", "Scythe", (4.78, 6.1, -0.25)),
    ("LeftShoulder", "UpperTorso", "LeftUpperArm", (-3.0, 14.3, 0.0)),
    ("LeftElbow", "LeftUpperArm", "LeftLowerArm", (-3.85, 10.65, 0.0)),
    ("LeftWrist", "LeftLowerArm", "LeftHand", (-4.6, 7.25, 0.0)),
    ("RightHip", "LowerTorso", "RightUpperLeg", (1.3, 7.6, 0.0)),
    ("RightKnee", "RightUpperLeg", "RightLowerLeg", (1.35, 4.25, 0.0)),
    ("RightAnkle", "RightLowerLeg", "RightFoot", (1.4, 1.15, 0.0)),
    ("LeftHip", "LowerTorso", "LeftUpperLeg", (-1.3, 7.6, 0.0)),
    ("LeftKnee", "LeftUpperLeg", "LeftLowerLeg", (-1.35, 4.25, 0.0)),
    ("LeftAnkle", "LeftLowerLeg", "LeftFoot", (-1.4, 1.15, 0.0)),
    ("RobeFront", "LowerTorso", "RobeFront", (0.0, 8.9, -1.66)),
    ("RobeBack", "LowerTorso", "RobeBack", (0.0, 8.9, 1.66)),
    ("RobeLeft", "LowerTorso", "RobeLeft", (-2.36, 8.9, 0.0)),
    ("RobeRight", "LowerTorso", "RobeRight", (2.36, 8.9, 0.0)),
    ("Cape", "UpperTorso", "Cape", (0.0, 13.7, 1.75)),
]

# attachments the game / controller script uses: (name, bone, position in model space)
ATTACHMENTS = [
    ("Overhead", "HumanoidRootPart", (0.0, 23.5, 0.0)),
    ("EyeGlow", "Head", (0.0, 17.28, -1.6)),
    ("Mouth", "Jaw", (0.0, 15.7, -1.3)),
    ("Mist", "LowerTorso", (0.0, 7.0, 0.0)),
    ("LeftStomp", "LeftFoot", (-1.4, 0.0, -1.0)),
    ("RightStomp", "RightFoot", (1.4, 0.0, -1.0)),
    ("BladeBase", "Scythe", (4.78, 19.9, -0.7)),
    ("BladeTip", "Scythe", (4.78, 16.4, -9.45)),
]


# ---------------------------------------------------------------- helpers

def shell(stations, n=32, p=2.4, cap_start=True, cap_end=True):
    """Loft of rounded sections [(y, rx, rz[, dx, dz])] bottom to top."""
    rings = []
    for st in stations:
        y, rx, rz = st[:3]
        dx = st[3] if len(st) > 3 else 0.0
        dz = st[4] if len(st) > 4 else 0.0
        rings.append([Vector((x, y, z)) for x, z in superellipse_pts(rx, rz, p=p, n=n, cx=dx, cy=dz)])
    return loft(rings, cap_start=cap_start, cap_end=cap_end)


def section_r(stations, y):
    for a, b in zip(stations, stations[1:]):
        if a[0] <= y <= b[0]:
            t = (y - a[0]) / (b[0] - a[0])
            return [lerp(a[i], b[i], t) for i in range(1, len(a))]
    return list(stations[-1][1:] if y > stations[-1][0] else stations[0][1:])


def front_z(stations, p):
    """z(x, y) of the FRONT (-Z) surface of a shell(), as a positive depth."""
    def z(x, y):
        rx, rz = section_r(stations, y)[:2]
        k = max(1e-4, 1 - abs(x / rx) ** p)
        return rz * k ** (1 / p)
    return z


def on_front(stations, p, pts, lift, depth=0.06, spacing=0.12):
    """A slab over an outline (x, y) lying on the front (-Z) of a shell()."""
    zf = front_z(stations, p)
    bm = projected_slab(densify(pts, spacing), lambda x, y: zf(x, y) + lift, lambda x, y: zf(x, y) - depth,
                        spacing=spacing)
    return xform(bm, S(1, 1, -1))


def bone_rod(p0, p1, r, knob0=None, knob1=None, segs=10):
    """A bone: a rod between two points with rounded knobs at the ends."""
    bm = bmesh_new()
    merge_into(bm, tube([Vector(p0), Vector(p1)], r, sides=segs))
    for p, k in ((p0, knob0), (p1, knob1)):
        if k:
            merge_into(bm, sphere(k, segs, max(6, segs // 2 + 1)), T(*p))
    return bm


def tattered_shell(a0, a1, y_top, y_bot, rt, rb, sx, sz, teeth, depth, n_per=4, rows=6, folds=0.03, thick=0.16,
                   wave_seed=0.0):
    """An open curved sheet on an elliptical cone (angles a0..a1, measured from +X toward
    +Z), tattered into points along the bottom. Thickened to a closed solid."""
    n = teeth * n_per
    rings = []
    for j in range(rows + 1):
        t = j / rows
        ring = []
        for i in range(n + 1):
            u = i / n
            a = lerp(a0, a1, u)
            r = lerp(rt, rb, t ** 0.9) * (1 + folds * math.sin(6 * a + wave_seed) * t)
            y = lerp(y_top, y_bot, t)
            if j == rows:
                ph = (i % n_per) / n_per
                y = y_bot - depth * (1 - abs(ph - 0.5) * 2) * (0.7 + 0.3 * math.sin(i * 1.7 + wave_seed))
            ring.append(Vector((r * sx * math.cos(a), y, r * sz * math.sin(a))))
        rings.append(ring)
    return thicken(loft(rings, cap_start=False, cap_end=False, closed=False), thick)


def mirror_x(bm):
    return xform(bm, S(-1, 1, 1))


# ---------------------------------------------------------------- body

def torso(p):
    ut = p.part("UpperTorso", ROBE, "Fabric", smooth=50, model="UpperTorso")
    mantle = p.part("Mantle", MANTLE, "Fabric", smooth=45, model="UpperTorso")
    inset = p.part("Chest", SHADOW, "SmoothPlastic", smooth=50, model="UpperTorso")
    ribs = p.part("Ribs", BONE, "SmoothPlastic", smooth=45, model="UpperTorso")
    st = [(9.2, 2.25, 1.55), (10.5, 2.45, 1.65), (12.0, 2.75, 1.80), (13.4, 3.05, 1.85), (14.2, 3.12, 1.80),
          (14.8, 2.85, 1.60), (15.2, 2.0, 1.25), (15.45, 1.15, 0.85)]
    ut.add(shell(st, n=40, p=2.4))
    # tattered mantle over the shoulders, open at the front over the ribcage
    n = 36
    a0, a1 = math.radians(270 + 34), math.radians(270 - 34 + 360)
    rings = []
    for j in range(7):
        t = j / 6
        ring = []
        for i in range(n + 1):
            a = lerp(a0, a1, i / n)
            side = abs(math.cos(a)) ** 2
            y_bot = 12.4 + 0.95 * side
            y = lerp(15.4, y_bot, t)
            if j == 6:
                ph = (i % 4) / 4
                y -= 0.55 * (1 - abs(ph - 0.5) * 2) * (0.6 + 0.4 * math.sin(i * 2.3))
            rx = lerp(1.55, 3.75, t ** 0.75)
            rz = lerp(1.25, 2.45, t ** 0.75)
            ring.append(Vector((rx * math.cos(a), y, rz * math.sin(a))))
        rings.append(ring)
    mantle.add(thicken(loft(rings, cap_start=False, cap_end=False, closed=False), 0.2))
    # dark V-neck opening with the ribcage showing
    vee = [(-0.95, 15.05), (0.0, 12.15), (0.95, 15.05)]
    inset.add(on_front(st, 2.4, fillet_pts(vee, 0.15, n=2), 0.03, depth=0.08))
    ribs.add(on_front(st, 2.4, [(-0.07, 14.55), (0.07, 14.55), (0.06, 12.75), (-0.06, 12.75)], 0.09, depth=0.03))
    zf = front_z(st, 2.4)
    for k, y in enumerate((14.35, 13.75, 13.2, 12.7)):
        w = 0.72 - 0.15 * k
        for sx in (-1, 1):
            pts = []
            for i in range(7):
                u = i / 6
                x = sx * (0.06 + w * u)
                yy = y - 0.28 * u * u
                pts.append(Vector((x, yy, -(zf(x, yy) + 0.08))))
            ribs.add(taper_tube(pts, 0.095, 0.06, sides=6))


def waist(p):
    lt = p.part("LowerTorso", ROBE, "Fabric", smooth=50, model="LowerTorso")
    rope = p.part("Belt", ROPE, "Fabric", smooth=50, model="LowerTorso")
    gold = p.part("Hourglass", GOLD, "Metal", smooth=35, model="LowerTorso")
    sand = p.part("Sand", SAND, "Neon", model="LowerTorso")
    glass = p.part("Glass", (210, 236, 255), "Glass", transparency=0.45, smooth=40, model="LowerTorso")
    lt.add(shell([(6.9, 2.15, 1.5), (7.8, 2.3, 1.6), (8.9, 2.32, 1.62), (9.75, 2.25, 1.55)], n=36, p=2.4))
    ring = [Vector((x, 9.05, z)) for x, z in superellipse_pts(2.42, 1.70, p=2.4, n=48)]
    ring.append(ring[0].copy())
    rope.add(tube(ring, 0.17, sides=8))
    knot = Vector((-0.95, 9.0, -1.86))
    rope.add(sphere(0.3, 10, 7), T(*knot))
    for dx, L in ((-0.12, 1.6), (0.18, 1.25)):
        end = [knot + Vector((dx * 0.3, -0.1, -0.08)), knot + Vector((dx, -L * 0.55, -0.24)), knot + Vector((dx * 1.5, -L, -0.3))]
        rope.add(tube(catmull(end, samples=3), 0.13, sides=6))
        rope.add(sphere(0.17, 8, 5, scale=(1, 1.5, 1)), T(*end[-1]) @ T(0, -0.12, 0))
    # an hourglass hanging off the right hip, its sand glowing
    hc = Vector((2.3, 7.55, -1.85))
    cord = [Vector((1.75, 9.0, -1.55)), Vector((2.1, 8.6, -1.78)), hc + Vector((0, 0.72, 0))]
    rope.add(tube(catmull(cord, samples=3), 0.07, sides=5))
    for y in (0.6, -0.6):
        gold.add(cylinder(0.46, 0.12, segs=16, bevel=0.03), T(*(hc + Vector((0, y, 0)))))
    for k in range(3):
        a = TAU * k / 3 + 0.4
        gold.add(cylinder(0.05, 1.2, segs=6), T(*(hc + Vector((0.40 * math.cos(a), 0, 0.40 * math.sin(a))))))
    gold.add(torus(0.12, 0.03, segs=10, rsegs=4, axis="Z"), T(*(hc + Vector((0, 0.72, 0)))))
    glass.add(lathe([(0, -0.54), (0.34, -0.52), (0.36, -0.30), (0.12, -0.04), (0.06, 0.0), (0.12, 0.04), (0.36, 0.30),
                     (0.34, 0.52), (0, 0.54)], segs=16), T(*hc))
    sand.add(lathe([(0, -0.50), (0.31, -0.48), (0.30, -0.33), (0.18, -0.20), (0, -0.16)], segs=14), T(*hc))
    sand.add(lathe([(0, 0.06), (0.16, 0.14), (0.24, 0.24), (0, 0.24)], segs=12), T(*hc))
    sand.add(cylinder(0.025, 0.36, segs=5), T(*(hc + Vector((0, -0.12, 0)))))


def robe_panels(p):
    spans = {"RobeRight": (0.0, 1.035), "RobeBack": (90.0, 1.0), "RobeLeft": (180.0, 1.035), "RobeFront": (270.0, 1.0)}
    for k, (name, (mid, scale)) in enumerate(spans.items()):
        part = p.part(name, ROBE, "Fabric", smooth=50, model=name)
        a0, a1 = math.radians(mid - 52), math.radians(mid + 52)
        part.add(tattered_shell(a0, a1, 8.95, 1.05, 2.36 * scale, 4.15 * scale, 1.0, 0.76, teeth=4, depth=0.6,
                                folds=0.035, thick=0.16, wave_seed=k * 1.3))


def leg(p, side):
    sx = 1 if side == "Right" else -1
    up = p.part(side + "UpperLeg", BONE, "SmoothPlastic", smooth=45, model=side + "UpperLeg")
    lo = p.part(side + "LowerLeg", BONE, "SmoothPlastic", smooth=45, model=side + "LowerLeg")
    ft = p.part(side + "Foot", BONE, "SmoothPlastic", smooth=45, model=side + "Foot")
    up.add(bone_rod((sx * 1.3, 7.45, 0), (sx * 1.35, 4.6, 0), 0.36, knob0=0.5))
    for dz in (-0.18, 0.18):
        up.add(sphere(0.38, 10, 7), T(sx * 1.35, 4.5, dz))
    lo.add(bone_rod((sx * 1.35, 4.15, 0.05), (sx * 1.4, 1.45, 0.0), 0.3, knob1=0.36))
    lo.add(sphere(0.36, 10, 7, scale=(1.0, 1.1, 0.8)), T(sx * 1.35, 4.2, -0.36))
    ft.add(box(1.5, 0.72, 2.3, bevel=0.3, seg=3), T(sx * 1.4, 0.38, -0.75))
    ft.add(sphere(0.46, 12, 8), T(sx * 1.4, 0.44, 0.45))
    for k, dx in enumerate((-0.48, 0.0, 0.48)):
        z0, z1 = -1.75, -3.2 - 0.15 * (k == 1)
        x = sx * 1.4 + dx
        ft.add(capsule(0.2, 0.0, z0 - z1, segs=8, rings=2), T(x, 0.24, z0) @ R("X", -90))
        ft.add(sphere(0.25, 8, 6), T(x, 0.27, z0))
        ft.add(sphere(0.22, 8, 6), T(x, 0.22, (z0 + z1) / 2))
        ft.add(sphere(0.21, 8, 6), T(x, 0.21, z1))


def arm(p, side):
    sx = 1 if side == "Right" else -1
    up = p.part(side + "UpperArm", ROBE, "Fabric", smooth=50, model=side + "UpperArm")
    lo = p.part(side + "LowerArm", ROBE, "Fabric", smooth=50, model=side + "LowerArm")
    fb = p.part(side + "Forearm", BONE, "SmoothPlastic", smooth=45, model=side + "LowerArm")
    sh, el, wr = Vector((3.0, 14.3, 0)), Vector((3.85, 10.65, 0)), Vector((4.6, 7.25, 0))

    def along(a, b, t):
        return a.lerp(b, t)
    up.add(shell([(el.y - 0.3, 0.94, 0.94, sx * along(sh, el, 1.08).x), (12.0, 1.0, 1.0, sx * 3.54),
                  (13.6, 1.02, 1.02, sx * 3.16), (14.5, 0.92, 0.92, sx * 2.96), (14.95, 0.55, 0.55, sx * 2.86)],
                 n=24, p=2.2))
    lo.add(shell([(10.05, 0.96, 0.96, sx * 3.98), (10.95, 0.94, 0.94, sx * 3.78)], n=24, p=2.2))
    n, rows = 28, 5
    rings = []
    for j in range(rows + 1):
        t = j / rows
        ring = []
        c = along(Vector((3.92, 10.25, 0)), Vector((4.66, 6.95, 0)), t)
        for i in range(n):
            a = TAU * i / n
            r = lerp(0.96, 1.62, t ** 1.4)
            y = c.y
            if j == rows:
                ph = (i % 4) / 4
                y -= 0.5 * (1 - abs(ph - 0.5) * 2) * (0.6 + 0.4 * math.sin(i * 1.9))
            ring.append(Vector((sx * c.x + r * math.cos(a), y, r * 0.92 * math.sin(a))))
        rings.append(ring)
    lo.add(thicken(loft(rings, cap_start=False, cap_end=False), 0.14))
    for dz in (-0.17, 0.17):
        a = along(el, wr, 0.1)
        fb.add(bone_rod((sx * a.x, a.y, dz), (sx * (wr.x - 0.04), wr.y + 0.2, dz * 0.8), 0.15, knob1=0.2, segs=8))


def hands(p):
    rh = p.part("RightHand", BONE, "SmoothPlastic", smooth=45, model="RightHand")
    lh = p.part("LeftHand", BONE, "SmoothPlastic", smooth=45, model="LeftHand")
    # right: a fist round the scythe shaft (shaft axis vertical through (4.78, y, -0.25))
    cx, cz = 4.78, -0.25
    rh.add(sphere(0.34, 10, 7), T(4.6, 7.12, 0.0))
    rh.add(box(0.5, 1.45, 1.05, bevel=0.2, seg=2), T(5.18, 6.15, -0.18))
    for k, y in enumerate((6.67, 6.32, 5.97, 5.63)):
        rf = 0.49
        pts = []
        for i in range(8):
            th = math.radians(lerp(12, -205 + 10 * k, i / 7))
            pts.append(Vector((cx + rf * math.cos(th), y - 0.03 * i, cz + rf * math.sin(th))))
        rh.add(taper_tube(pts, 0.17, 0.13, sides=7))
        rh.add(sphere(0.2, 8, 6), T(*pts[0]))
        rh.add(sphere(0.15, 8, 6), T(*pts[3]))
        rh.add(sphere(0.14, 8, 5), T(*pts[-1]))
    thumb = [Vector((cx + 0.46 * math.cos(math.radians(a)), 6.93 - 0.06 * i, cz + 0.46 * math.sin(math.radians(a))))
             for i, a in enumerate((40, 70, 100, 128, 150))]
    rh.add(taper_tube(thumb, 0.18, 0.14, sides=7))
    rh.add(sphere(0.15, 8, 5), T(*thumb[-1]))
    # left: an open bony claw, palm toward the body
    lh.add(sphere(0.34, 10, 7), T(-4.6, 7.12, 0.0))
    lh.add(box(0.45, 1.25, 1.1, bevel=0.2, seg=2), T(-4.66, 6.32, -0.05))
    for k, dz in enumerate((-0.42, -0.14, 0.14, 0.42)):
        L = 1.35 - 0.12 * abs(k - 1.5)
        base = Vector((-4.68, 5.69, dz))
        pts = [base, base + Vector((0.08, -L * 0.45, -0.04)), base + Vector((0.24, -L * 0.85, -0.08)),
               base + Vector((0.42, -L, -0.06))]
        lh.add(taper_tube(catmull(pts, samples=2), 0.15, 0.09, sides=6, point=False))
        lh.add(sphere(0.18, 8, 6), T(*base))
        lh.add(sphere(0.14, 8, 5), T(*pts[1]))
        lh.add(lathe([(0, 0), (0.1, 0.0), (0, 0.32)], segs=5), T(*pts[3]) @ aim((0.5, -0.8, -0.1)))
    th = [Vector((-4.6, 6.27, -0.62)), Vector((-4.45, 5.82, -0.95)), Vector((-4.3, 5.37, -1.1))]
    lh.add(taper_tube(th, 0.17, 0.12, sides=6))
    lh.add(lathe([(0, 0), (0.11, 0.0), (0, 0.3)], segs=5), T(*th[-1]) @ aim((0.2, -0.7, -0.4)))


# ---------------------------------------------------------------- head

def skull(p):
    head = p.part("Head", BONE, "SmoothPlastic", smooth=40, model="Head")
    eyes = p.part("Eyes", GLOW, "Neon", model="Head")
    jaw = p.part("Jaw", BONE, "SmoothPlastic", smooth=40, model="Jaw")
    hood = p.part("Hood", HOOD, "Fabric", smooth=45, model="Head")
    dark = p.part("HoodShadow", SHADOW, "SmoothPlastic", smooth=50, model="Head")
    cran = sphere(1.55, 28, 18, scale=(1.0, 0.95, 1.0))
    xform(cran, T(0, 17.6, -0.12))
    face = sphere(1.0, 24, 14, scale=(1.18, 0.82, 1.0))
    xform(face, T(0, 16.55, -0.6))
    sk = boolean(cran, face, "UNION")
    cut = bmesh_new()
    for sxx in (-1, 1):
        merge_into(cut, sphere(0.56, 16, 10, scale=(1.0, 1.08, 1.0)), T(sxx * 0.6, 17.3, -1.5))
    nose = projected_slab(densify(fillet_pts([(-0.22, 0.0), (0.22, 0.0), (0.0, 0.36)], 0.05, n=2), 0.05),
                          lambda x, y: 0.6, lambda x, y: -0.6, spacing=0.06)
    merge_into(cut, nose, T(0, 16.45, -1.5))
    sk = boolean(sk, cut)
    head.add(sk)
    for i, x in enumerate((-0.62, -0.37, -0.12, 0.12, 0.37, 0.62)):
        head.add(box(0.22, 0.34, 0.22, bevel=0.07, seg=2), T(x, 15.98, -1.45 + 0.1 * abs(x)))
    for sxx in (-1, 1):
        eyes.add(sphere(0.42, 14, 9), T(sxx * 0.6, 17.28, -1.2))
    # lower jaw: a U-shaped bone hinged at the sides, with a row of teeth
    u = []
    for i in range(13):
        a = math.radians(lerp(-170, -10, i / 12))
        u.append(Vector((1.0 * math.cos(a), 15.55 + 0.45 * abs(math.cos(a)) ** 2.2, -0.35 + 1.0 * math.sin(a))))
    jaw.add(sweep(u, [0.32] * 13, [0.42] * 13, sides=8, point_end=False, up=Vector((0, 1, 0))))
    for sxx in (-1, 1):
        jaw.add(sphere(0.24, 10, 7), T(sxx * 1.0, 16.12, -0.4))
    for i, x in enumerate((-0.5, -0.25, 0.0, 0.25, 0.5)):
        jaw.add(box(0.2, 0.3, 0.2, bevel=0.06, seg=2), T(x, 15.78, -1.33 + 0.12 * abs(x)))
    # hood: a big pointed cowl, its face opening dark inside
    outer = sphere(1.0, 32, 20)
    inner = sphere(1.0, 28, 18)

    def hoodify(bm, rx, ry, rz, cy, cz):
        for v in bm.verts:
            x, y, z = v.co
            yy, zz = y, z
            if y > 0:                                    # pull the top up and back into a drooping point
                k = y ** 3
                yy = y + 0.38 * k - 0.25 * max(0.0, z) ** 2 * k
                zz = z + 0.95 * k
            if z < 0 and y > 0.2:                        # a brim that overhangs the face a little
                zz -= 0.12 * (y - 0.2)
            v.co = Vector((x * rx, cy + yy * ry, cz + zz * rz))
    hoodify(outer, 2.62, 2.7, 2.62, 17.65, 0.2)
    hoodify(inner, 2.34, 2.42, 2.34, 17.65, 0.2)
    hd = boolean(outer, inner)
    opening = cylinder(1.0, 6.0, segs=32)
    xform(opening, T(0, 17.0, -3.4) @ S(1.66, 1.92, 1.0) @ R("X", 90))
    floor = box(8, 4, 8)
    xform(floor, T(0, 15.05 - 2.0, 0))
    hood.add(boolean(boolean(hd, opening), floor))
    bd = sphere(1.0, 24, 16, scale=(2.1, 2.3, 1.8))
    xform(bd, T(0, 17.7, 0.55))
    clip = box(6, 8, 6)
    xform(clip, T(0, 17.7, -0.5 - 3.0))
    dark.add(boolean(bd, clip))


# ---------------------------------------------------------------- scythe

def scythe(p):
    shaft = p.part("Scythe", WOOD, "Wood", smooth=40, model="Scythe")
    bands = p.part("ScytheBands", SILVER, "Metal", smooth=35, model="Scythe")
    wrap = p.part("ScytheWrap", WRAP, "Fabric", smooth=45, model="Scythe")
    blade = p.part("ScytheBlade", STEEL, "Metal", smooth=30, model="Scythe")
    edge = p.part("ScytheEdge", GLOW, "Neon", model="Scythe")
    deco = p.part("ScytheSkull", BONE, "SmoothPlastic", smooth=40, model="Scythe")
    x0, z0 = 4.78, -0.25
    rng = random.Random(4)
    pts = []
    for i in range(15):
        y = lerp(0.55, 21.0, i / 14)
        pts.append(Vector((x0 + 0.08 * math.sin(i * 1.3), y, z0 + 0.07 * math.cos(i * 0.9))))
    shaft.add(taper_tube(catmull(pts, samples=2), 0.29, 0.25, sides=10))
    for i in (3, 7, 10):
        c = pts[i]
        shaft.add(sphere(0.33, 8, 6, scale=(1, 0.7, 1)), T(c.x + 0.05, c.y, c.z) @ R("Y", rng.uniform(0, 360)))
    for y in (1.0, 9.6, 15.9, 20.25):
        bands.add(lathe_loop([(0.27, -0.16), (0.36, -0.12), (0.36, 0.12), (0.27, 0.16)], segs=14), T(x0, y, z0))
    bands.add(lathe([(0, 0.05), (0.2, 0.12), (0.34, 0.4), (0.3, 0.62), (0, 0.7)], segs=12), T(x0, 0.0, z0))
    for k in range(5):
        y = 4.6 + k * 0.62
        wrap.add(lathe_loop([(0.27, -0.22), (0.34, -0.16), (0.34, 0.16), (0.27, 0.22)], segs=12),
                 T(x0, y, z0) @ R("Z", 8 * (1 if k % 2 else -1)))
    # collar where the blade joins
    bands.add(lathe([(0.0, 20.5), (0.42, 20.55), (0.46, 21.05), (0.4, 21.35), (0, 21.4)], segs=14), T(x0, 0, z0))
    # crescent blade sweeping forward and down; the glowing edge runs along its inside curve
    spine = [(0.15, 21.3), (-1.6, 22.05), (-3.7, 22.15), (-5.8, 21.45), (-7.5, 20.1), (-8.8, 18.3), (-9.6, 16.2)]
    edge_c = [(-9.6, 16.2), (-8.35, 17.35), (-6.7, 18.25), (-4.7, 18.75), (-2.7, 18.95), (-1.0, 19.1), (0.15, 19.45)]
    sp = catmull(spine, samples=3)
    ec = catmull(edge_c, samples=3)
    outline = [(z, y) for z, y in sp] + [(z, y) for z, y in ec[1:-1]]
    bl = slab(outline, 0.26, 0.09, seg=2)            # in local XY = (z, y); turn so it lies in the YZ plane
    blade.add(bl, T(x0, 0, z0) @ R("Y", 90) @ S(-1, 1, 1))
    band_out = [(z, y) for z, y in ec]
    band_in = []
    for i, (z, y) in enumerate(ec):
        j = min(max(i, 1), len(ec) - 2)
        dz, dy = ec[j + 1][0] - ec[j - 1][0], ec[j + 1][1] - ec[j - 1][1]
        L = math.hypot(dz, dy) or 1.0
        w = 0.42 * math.sin(math.pi * min(1.0, i / (len(ec) - 1) * 1.05)) ** 0.6 + 0.02
        band_in.append((z - dy / L * w, y + dz / L * w))
    eo = band_out + list(reversed(band_in))
    edge.add(slab(eo, 0.32, 0.06, seg=1), T(x0, 0, z0) @ R("Y", 90) @ S(-1, 1, 1))
    blade.add(lathe([(0, 0), (0.28, 0.0), (0, 1.6)], segs=6), T(x0, 21.1, z0 + 0.3) @ aim((0, 0.45, 1.0)))
    # little skull ornament at the top, eyes glowing
    deco.add(sphere(0.5, 14, 9, scale=(1.0, 0.95, 1.0)), T(x0, 21.75, z0 - 0.15))
    deco.add(box(0.5, 0.3, 0.45, bevel=0.1, seg=2), T(x0, 21.38, z0 - 0.42))
    for sxx in (-1, 1):
        edge.add(sphere(0.12, 8, 5), T(x0 + sxx * 0.19, 21.78, z0 - 0.6))


def cape(p):
    """A long tattered cape hanging from under the mantle down the back."""
    cp = p.part("Cape", ROBE, "Fabric", smooth=50, model="Cape")
    a0, a1 = math.radians(18), math.radians(162)
    n, rows = 32, 8
    rings = []
    for j in range(rows + 1):
        t = j / rows
        ring = []
        for i in range(n + 1):
            u = i / n
            a = lerp(a0, a1, u)
            y = lerp(13.6, 1.5, t)
            if j == rows:
                ph = (i % 4) / 4
                y -= 0.75 * (1 - abs(ph - 0.5) * 2) * (0.55 + 0.45 * math.sin(i * 1.7))
            rx = lerp(3.0, 4.75, t ** 0.85)
            rz = lerp(1.95, 3.95, t ** 0.85) * (1 + 0.05 * math.sin(7 * a) * t)
            ring.append(Vector((rx * math.cos(a), y, rz * math.sin(a))))
        rings.append(ring)
    cp.add(thicken(loft(rings, cap_start=False, cap_end=False, closed=False), 0.15))


def build(p):
    cape(p)
    torso(p)
    waist(p)
    robe_panels(p)
    for side in ("Right", "Left"):
        leg(p, side)
        arm(p, side)
    hands(p)
    skull(p)
    scythe(p)
