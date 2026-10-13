"""4.3: the RootMonster in bricks (PotatoKit.RootMonster, PotatoKit.RootAnimations).

The same rig as part 1's RootMonster, joint for joint, so its four KeyframeSequences
(RootEmerge, RootChase, RootGrab, RootWither) are baked by the same functions (roots_anim) and play
the same:
  Root (PrimaryPart: anchored, invisible, 4 x 0.4 x 4, CanTouch on, pivot on the ground)
   -> Motor6D "Heap" (Root -> Heap), in model axes at the pivot
       -> Motor6D "Tentacle1Seg1" (Heap -> Tentacle1Seg1) -> ... -> "Tentacle1Seg5", and Tentacle2-6
          (each joint's -Z runs along its segment, X level: +X turns lift a root, +Y swing it left)
Motor6Ds live in their Part0, as before. Attachments: Fx_Dirt (Root), Fx_Eyes (Heap), Claw (the
front roots' tips). The two Eye parts are Neon with the attribute Flicker = 0.1.

Now every part is a Roblox Part in the Folk Valley idiom: the heap is three stacked rounds of dug
soil with clods and pebbles round its foot and a dark hollow for the eyes; each root segment is a tapering
eight-sided brick (a block and the same block turned 45 degrees about the root), with a knob, root
hairs from the third segment on, a two-pronged fork on the front roots and a point on the others.
"""
import math

import numpy as np

import spsgeo as G
from spsgeo import CF

from . import roots as R
from .bricks import Bricks, hexc, ori, shade

SOIL = ("70482c", "5c3a24", "84583a")
DARK = ("543622", "46301e")
BARK = ("9c663c", "8a5832", "ae7446")
MID = ("ba8858", "a87848")
TIP = ("e4c898", "d4b480")
HOLE = "221610"
PEBBLE = ("9a948a", "7e786e")
EYE = "ffde3c"


def seg_cols(i):
    return BARK if i < 3 else (MID if i == 3 else TIP)


def build(sc, parent, base=None):
    base = base or CF()
    m = sc.model(parent, "RootMonster")
    b = Bricks(sc, base, anchored=False, collide=False, touch=False, query=False, massless=True)
    root = sc.part(m, "Root", (4.0, 0.4, 4.0), base * CF((0.0, 0.2, 0.0)), (255, 255, 255), material="SmoothPlastic",
                   transparency=1.0, anchored=True, collide=False, touch=True, query=False, shadow=False, grid=False,
                   surfaces="smooth", pivot=CF((0.0, -0.2, 0.0)))
    m.p["primary"] = root
    joints = []                                                      # (joint, part0 name, part1 name, frame)

    def weld_to(owner, p):
        sc.weld(owner, p)
        return p

    # -------------------------------------------------------------- the heap: three rounds of dug soil
    heap = b.part(m, "Heap", (7.0, 1.4, 6.6), (0.0, 0.7, 0.0), None, SOIL[0])
    sc.motor(root, heap, "Heap", base, parent=root)
    joints.append(("Heap", "Root", "Heap", CF()))

    def h(name, size, pos, R_=None, col=SOIL[0], **kw):
        return weld_to(heap, b.part(m, name, size, pos, R_, col, **kw))
    rng = np.random.default_rng(5)
    for (w, hh, d, y, cols, turn) in ((9.0, 1.2, 5.0, 0.6, (SOIL[1], SOIL[1], SOIL[2]), 8),
                                     (7.0, 1.14, 6.6, 1.7, (SOIL[0], SOIL[2], SOIL[1]), -14),
                                     (4.6, 0.96, 4.4, 2.6, (SOIL[2], SOIL[0], SOIL[1]), 22)):
        Rr = G.ry(turn)
        h("Heap", (w, hh, d * 0.6), (0.0, y, 0.0), Rr, cols[0])
        h("Heap", (w * 0.6, hh - 0.03, d), (0.0, y, 0.0), Rr, cols[1])
        s = math.sqrt(w * d) * 0.82
        h("Heap", (s, hh - 0.06, s), (0.0, y, 0.0), Rr @ G.ry(45), cols[2])
    h("Heap", (1.6, 0.45, 1.4), (0.3, 3.25, 0.5), ori(4, 30, -5), SOIL[2])
    h("Heap", (1.0, 0.4, 0.9), (-0.7, 3.2, -0.4), ori(-6, 60, 4), SOIL[0])
    for i in range(6):                                              # lumps on its flanks
        a = math.radians(30 + 60 * i + rng.uniform(-12, 12))
        r = 3.0 + rng.uniform(-0.2, 0.3)
        s = rng.uniform(0.9, 1.3)
        h("Heap", (s, s * 0.7, s * 0.9), (r * math.sin(a), 1.75 + rng.uniform(-0.2, 0.25), -r * math.cos(a) + 0.3),
          ori(rng.uniform(-8, 8), rng.uniform(0, 90), rng.uniform(-8, 8)), SOIL[2] if i % 2 else SOIL[1])
    for i in range(9):                                              # clods thrown up round its foot
        a = i * math.tau / 9 + rng.uniform(-0.3, 0.3)
        r = rng.uniform(4.4, 5.0)
        s = rng.uniform(0.55, 0.95)
        h("Clods", (s, s * 0.6, s), (r * math.cos(a), s * 0.3, r * math.sin(a)), G.ry(rng.uniform(0, 90)),
          DARK[i % 2])
    for i in range(7):                                              # and pebbles among them
        a = i * math.tau / 7 + 0.4 + rng.uniform(-0.25, 0.25)
        r = rng.uniform(3.9, 5.3)
        s = rng.uniform(0.3, 0.5)
        h("Pebbles", (s, s * 0.7, s * 0.9), (r * math.cos(a), s * 0.35, r * math.sin(a)),
          ori(rng.uniform(-10, 10), rng.uniform(0, 90), rng.uniform(-10, 10)), PEBBLE[i % 2])
    # the dark hollow with the two glowing eyes
    h("EyeHole", (3.0, 1.5, 0.4), (0.0, 1.8, -3.2), None, HOLE, material="SmoothPlastic", shadow=False)
    h("EyeHole", (3.4, 0.35, 0.6), (0.0, 2.68, -3.2), None, SOIL[2])                  # a brow of soil over it
    for sx in (-1, 1):
        e = h("Eye", (0.66, 0.66, 0.2), (sx * 0.74, 1.84, -3.52), G.rz(45), EYE, material="Neon", shadow=False)
        sc.attr(e, "Flicker", 0.1)
    sc.attachment(root, "Fx_Dirt", base * CF((0.0, 0.5, 0.0)))
    sc.attachment(heap, "Fx_Eyes", base * CF((0.0, 1.8, -3.2)))

    # -------------------------------------------------------------- the six roots, five segments each
    for (tname, bp, d0, length, bend, claw) in R.TENTACLES:
        frames, seg = R.tentacle_frames(bp, d0, length, bend)
        prev, prev_name = heap, "Heap"
        for i, fr in enumerate(frames):
            pname = "%sSeg%d" % (tname, i + 1)
            wf = base * fr
            r0 = 0.95 - 0.13 * i
            r1 = 0.95 - 0.13 * (i + 1)
            cols = seg_cols(i)
            sb = Bricks(sc, wf, anchored=False, collide=False, touch=False, query=False, massless=True)
            L = seg + 0.4
            w = r0 + r1                                              # its mean diameter
            p = sb.part(m, pname, (w, w, L), (0.0, 0.0, -seg / 2 + 0.05), None, cols[0])
            sc.motor(prev, p, pname, wf, parent=prev)
            joints.append((pname, prev_name, pname, fr))

            def s_(name, size, pos, R_=None, col=cols[0], **kw):
                return weld_to(p, sb.part(m, name, size, pos, R_, col, **kw))
            s_("Bark", (w * 0.86, w * 0.86, L - 0.12), (0.0, 0.0, -seg / 2 + 0.05), G.rz(45), cols[1])
            a = rng.uniform(0, math.tau)                             # a knob
            kz = -rng.uniform(0.3, 0.7) * seg
            kr = w / 2
            s_("Knob", (kr * 0.9, kr * 0.9, kr), (kr * 0.75 * math.cos(a), kr * 0.75 * math.sin(a), kz),
               ori(rng.uniform(0, 40), rng.uniform(0, 40), 0), cols[1 if i % 2 else 0])
            if i >= 2:                                               # root hairs
                for k in range(2 if i < 4 else 1):
                    a = rng.uniform(0, math.tau)
                    hz = -rng.uniform(0.25, 0.75) * seg
                    Rh = G.rz(math.degrees(a) - 90) @ G.rx(-35)
                    pos = np.array((kr * 0.85 * math.cos(a), kr * 0.85 * math.sin(a), hz)) + Rh @ (0, 0.45, 0)
                    s_("Hairs", (0.18, 0.9, 0.18), pos, Rh, TIP[0])
            if i == R.SEGS - 1:
                if claw:                                             # a two-pronged fork reaching forward and down
                    for sx in (-1, 1):
                        Rf = G.ry(-sx * 18) @ G.rx(-14)
                        s_("Fork", (0.36, 0.36, 1.9), np.array((sx * 0.3, 0.0, -seg + 0.1)) + Rf @ (0, 0, -0.85),
                           Rf, TIP[1])
                    sc.attachment(p, "Claw", wf * CF((0.0, 0.0, -seg - 1.6)))
                else:
                    s_("Tip", (w * 0.55, w * 0.55, 1.0), (0.0, 0.0, -seg - 0.3), G.rz(45), TIP[1])
            prev, prev_name = p, pname
    sc.anim_controller(m)
    sc.root_rig = dict(base=base, joints=joints, model=m)
    return m
