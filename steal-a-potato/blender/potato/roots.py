"""The RootMonster: a churned heap of dirt about 9 wide and 3 high with six fat knobbly potato
roots coming out of it, brown with paler tips and a few root hairs; the two front roots end in
claw-like forks. Two small glowing yellow eyes deep in the heap (scary-funny, not horror).

Rig (front -Z, pivot on the ground in the middle):
  Root (PrimaryPart, anchored, invisible, pivot on the ground)
   -> Heap (Motor6D "Heap")
       -> Tentacle1Seg1 -> Tentacle1Seg2 -> ... -> Tentacle1Seg5     (Motor6Ds named like Part1)
       ... Tentacle6
Each Motor6D's C0/C1 sit on the joint: its -Z runs along the root segment, its X across, so a
positive turn about X lifts the root, about Y swings it to its left."""
import math

import numpy as np

import spsgeo as G
from spsgeo import CF, T, RX, RY, RZ, S

from .geo import bevel_box, ccyl, cfrustum

SOIL = (112, 72, 44)
SOIL_DARK = (84, 54, 34)
ROOT = (156, 102, 60)
ROOT_MID = (186, 136, 88)
ROOT_TIP = (228, 200, 152)
EYE = (255, 222, 60)
SEGS = 5

# (name, base on the heap, direction out, length, bend per joint (deg, + lifts), claw)
TENTACLES = [
    ("Tentacle1", (-1.5, 1.9, -2.7), (-0.22, 0.42, -0.88), 9.0, -9.0, True),
    ("Tentacle2", (1.5, 1.9, -2.7), (0.22, 0.42, -0.88), 9.0, -9.0, True),
    ("Tentacle3", (-3.4, 1.4, -0.7), (-0.88, 0.38, -0.28), 7.5, -10.0, False),
    ("Tentacle4", (3.4, 1.4, -0.7), (0.88, 0.38, -0.28), 7.5, -10.0, False),
    ("Tentacle5", (-2.4, 1.7, 2.3), (-0.6, 0.55, 0.58), 6.5, -12.0, False),
    ("Tentacle6", (2.4, 1.7, 2.3), (0.6, 0.55, 0.58), 6.5, -12.0, False),
]


def heap_geo(rng):
    """Churned dirt: a layered lumpy heap and a ring of clods."""
    g = G.Geo()
    rmod = lambda a: 1.0 + 0.08 * math.sin(4 * a + 0.5) + 0.05 * math.sin(9 * a)
    prof = [(0.0, 0.0), (4.5, 0.0), (4.4, 0.5), (3.9, 1.3), (3.0, 2.2), (1.8, 2.8), (0.6, 3.05), (0.0, 3.1)]
    g.add(G.outward(G.lathe(prof, 14, rmod=rmod)))
    for i in range(12):
        a = i * math.tau / 12 + rng.uniform(-0.2, 0.2)
        r = rng.uniform(2.6, 4.2)
        y = 2.9 * (1 - (r / 4.6) ** 2) + 0.1
        s = rng.uniform(0.7, 1.3)
        g.add(bevel_box(s, s * 0.7, s * 0.9, 0.2, (r * math.cos(a), y, r * math.sin(a))).xf(
            G.M(G.ry(rng.uniform(0, 90)))))
    return g


def clods_geo(rng):
    """Darker clods thrown up round the heap's foot."""
    g = G.Geo()
    for i in range(9):
        a = i * math.tau / 9 + rng.uniform(-0.3, 0.3)
        r = rng.uniform(4.3, 5.0)
        s = rng.uniform(0.5, 0.9)
        g.add(bevel_box(s, s * 0.6, s, 0.15, (r * math.cos(a), s * 0.3, r * math.sin(a))).xf(
            G.M(G.ry(rng.uniform(0, 90)))))
    return g


def eye_hole_geo():
    """A dark hollow in the heap's front where the eyes sit."""
    g = G.Geo()
    g.add(bevel_box(2.6, 1.2, 0.8, 0.3, (0, 1.75, -2.75)))
    return g


def frame_along(p, d):
    """CF at p whose -Z runs along d and X lies level (d is not vertical here)."""
    d = np.asarray(d, float) / np.linalg.norm(d)
    Z = -d
    X = np.cross((0.0, 1.0, 0.0), Z)
    X /= np.linalg.norm(X)
    Y = np.cross(Z, X)
    return CF(np.asarray(p, float), np.column_stack((X, Y, Z)))


def tentacle_frames(base, d0, length, bend):
    """Rest-pose joint frames along a root: it leaves the heap along d0 and bends `bend`
    degrees at each joint (about the joint's own X)."""
    seg = length / SEGS
    frames = []
    cf_ = frame_along(base, d0)
    for i in range(SEGS):
        frames.append(cf_)
        cf_ = cf_ * CF((0.0, 0.0, -seg)) * CF((0, 0, 0), G.rx(bend))
    return frames, seg


def segment_geo(i, seg, rng, claw):
    """One root segment in its joint frame (from the joint along -Z): an eight-sided tapered
    body with knobs; the last ones get root hairs; a claw fork on the front roots' tips."""
    r0 = 0.95 - 0.13 * i
    r1 = 0.95 - 0.13 * (i + 1)
    g = cfrustum(r0, r1, seg + 0.5, 8, "z", (0, 0, -seg / 2 + 0.1), 0.12)
    for k in range(2):
        a = rng.uniform(0, math.tau)
        z = -rng.uniform(0.25, 0.75) * seg
        r = r0 + (r1 - r0) * (-z / seg)
        g.add(bevel_box(r * 0.8, r * 0.8, r * 0.9, 0.12, (r * 0.7 * math.cos(a), r * 0.7 * math.sin(a), z)))
    hairs = G.Geo()
    if i >= 2:
        for k in range(2):
            a = rng.uniform(0, math.tau)
            z = -rng.uniform(0.2, 0.8) * seg
            r = r0 + (r1 - r0) * (-z / seg)
            h = bevel_box(0.2, 0.9, 0.2, 0.05, (0, 0.45, 0))
            hairs.add(h.xf(T(r * 0.9 * math.cos(a), r * 0.9 * math.sin(a), z) @ RZ(math.degrees(a) - 90) @ RX(-35)))
    if i == SEGS - 1:
        if claw:
            for sx in (-1, 1):                 # a two-prong fork reaching forward and down
                pr = cfrustum(0.32, 0.08, 1.8, 6, "z", (0, 0, -0.9), 0.05)
                g.add(pr.xf(T(sx * 0.32, 0, -seg + 0.1) @ RY(-sx * 18) @ RX(-14)))
        else:
            g.add(cfrustum(r1, 0.08, 1.0, 8, "z", (0, 0, -seg - 0.35), 0.05))
    return g, hairs


def build(k, kf, base=CF((-26.0, -500.0, 0.0))):
    """Model RootMonster at `base` (its pivot); returns it. Also stores the rig (joint list with
    rest frames in model space) on the scene for the animation baker."""
    sc = k.sc
    rng = np.random.default_rng(5)
    m = sc.model(kf, "RootMonster")
    root = sc.part(m, "Root", (4.0, 0.4, 4.0), base * CF((0.0, 0.2, 0.0)), (255, 255, 255), material="SmoothPlastic",
                   transparency=1.0, anchored=True, collide=False, touch=True, query=False, shadow=False, grid=False,
                   surfaces="smooth")
    root.p["pivot"] = CF((0.0, -0.2, 0.0))
    m.p["primary"] = root

    def part_mesh(name, mesh, geo, frame, color, material="Plastic"):
        return sc.mesh(m, name, mesh, geo, frame, color, material=material, anchored=False, collide=False,
                       touch=False, query=False, massless=True, shadow=True, owner="RootMonster")

    heap = part_mesh("Heap", "Root_Heap", heap_geo(rng), base, SOIL)
    rig = [("Heap", "Root", "Heap", CF((0.0, 0.0, 0.0)))]
    sc.motor(root, heap, "Heap", base, parent=root)
    clods = part_mesh("Clods", "Root_Clods", clods_geo(rng), base, SOIL_DARK)
    sc.weld(heap, clods)
    hole = part_mesh("EyeHole", "Root_EyeHole", eye_hole_geo(), base, (34, 22, 16))
    sc.weld(heap, hole)
    for sx in (-1, 1):
        e = sc.part(m, "Eye", (0.8, 0.8, 0.8), base * CF((sx * 0.62, 1.82, -3.05)), EYE, shape="Ball",
                    material="Neon", anchored=False, collide=False, touch=False, query=False, shadow=False,
                    massless=True, grid=False, surfaces="smooth")
        sc.weld(heap, e)
        sc.attr(e, "Flicker", 0.1)
    sc.attachment(root, "Fx_Dirt", base * CF((0.0, 0.5, 0.0)))
    sc.attachment(heap, "Fx_Eyes", base * CF((0.0, 1.8, -3.2)))
    for (tname, bp, d0, length, bend, claw) in TENTACLES:
        frames, seg = tentacle_frames(bp, d0, length, bend)
        prev, prev_name = heap, "Heap"
        for i, fr in enumerate(frames):
            pname = "%sSeg%d" % (tname, i + 1)
            col = ROOT if i < 3 else (ROOT_MID if i == 3 else ROOT_TIP)
            g, hairs = segment_geo(i, seg, rng, claw)
            wf = base * fr
            p = part_mesh(pname, "Root_%s" % pname, g, wf, col)
            if hairs.f:
                h = part_mesh("Hairs", "Root_%sHairs" % pname, hairs, wf, ROOT_TIP)
                sc.weld(p, h)
            sc.motor(prev, p, pname, wf, parent=prev)
            rig.append((pname, prev_name, pname, fr))
            prev, prev_name = p, pname
            if i == SEGS - 1 and claw:
                sc.attachment(p, "Claw", wf * CF((0.0, 0.0, -seg - 1.6)))
    sc.anim_controller(m)
    sc.folder(kf, "RootAnimations")            # the build script fills it with the KeyframeSequences
    sc.root_rig = dict(base=base, joints=rig, model=m)
    return m


def chains():
    """[[joint names of one root, base first], ...]"""
    return [["%sSeg%d" % (t[0], i + 1) for i in range(SEGS)] for t in TENTACLES]
