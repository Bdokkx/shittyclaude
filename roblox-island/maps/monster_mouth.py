"""Event piece "Monster Mouth" (flat): a small torn hole lying on top of any lawn, about 18 studs across and
under 1 stud tall, made to read from above. A black disc with a glowing purple spiral that fades from bright at
the rim to dark at the centre (so it looks deep), faint glowing eyes near the middle, jagged turf teeth lying
around the rim, purple mist wisps, cracks and dirt clods.

Local frame: ground (the lawn it sits on) at y = 0, mouth centred on the origin.
In the exported model everything is decoration (no collision) except nothing - players walk over it. Hooks:
  MouthTrigger  invisible, CanTouch, covers the hole (for "stepped into the mouth" scripts)
  AnimateMouth  client Script: the spiral turns, mist drifts, eyes blink
The lawn under it in the previews is preview-only and not exported.
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "spear"))

from core import Model                # noqa: E402

R = 4.5               # radius of the black hole
GRASS = ("#6CCB4A", "#5EBE45", "#56B040", "#7AD155")
DIRT = ("#6E4A2C", "#5A3A22", "#4A3326")
SWIRL = ("#A24DF2", "#8E34E6", "#7A22CC", "#6418B0", "#4E1290", "#360B68", "#22063F")
EYE = ("#D8F25A", "#FF5A5A", "#E9D8FF")


def lerp_col(cols, u):
    u = max(0.0, min(1.0, u)) * (len(cols) - 1)
    i = min(int(u), len(cols) - 2)
    return cols[i] if u - i < 0.5 else cols[i + 1]


def ring(m, r, y, h, col, n=28, width=1.0, **kw):
    for k in range(n):
        a = (k + 0.5) * 2 * math.pi / n
        with m.at((math.cos(a) * r, y, math.sin(a) * r), ry=90 - math.degrees(a)):
            m.box((0, 0, 0), (2 * math.pi * r / n * 1.12, h, width), col, **kw)


def hole(m):
    with m.ctx(stage="props", folder="Hole", tag="Hole:0", collide=False, shadow=False):
        m.octagon(0.06, R + 0.6, 0.12, DIRT[2])                        # torn soil edge
        ring(m, R + 0.35, 0.16, 0.12, DIRT[0], width=0.8)
        m.octagon(0.14, R, 0.12, "#07050A", name="Void")             # the black hole itself
        ring(m, R - 0.25, 0.2, 0.08, "#1A0F24", width=0.6)           # dark inner wall band


def swirl(m):
    """Three flat spiral arms on the void: wide and bright at the rim, thin and dark at the centre."""
    arms, steps = 3, 36
    with m.ctx(stage="props", folder="Swirl", tag="Swirl:0", collide=False, shadow=False):
        for arm in range(arms):
            prev = None
            for i in range(steps + 1):
                u = i / steps
                r = (R - 0.9) * (1 - u) ** 1.25 + 0.15     # pulls inward straight away: no ring at the rim
                a = arm * 2 * math.pi / arms + u * 2.2 * math.pi
                p = (math.cos(a) * r, 0.24 + 0.02 * (1 - u), math.sin(a) * r)
                if prev:
                    seg = math.dist(prev, p)
                    mid = ((prev[0] + p[0]) / 2, p[1], (prev[2] + p[2]) / 2)
                    ry = math.degrees(math.atan2(p[0] - prev[0], p[2] - prev[2]))
                    m.box(mid, (0.7 - 0.55 * u, 0.06, seg + 0.12), lerp_col(SWIRL, u), mat="Neon", ry=ry,
                          name="Swirl")
                prev = p
        m.octagon(0.22, 0.7, 0.08, "#1E063C", mat="Neon", name="Swirl")   # faint glow far down the middle


def eyes(m, rng):
    with m.ctx(stage="props", folder="Eyes", collide=False, shadow=False):
        for i in range(3):
            a = i * 2.1 + rng.uniform(-0.3, 0.3)
            r = rng.uniform(1.1, 2.0)
            with m.ctx(tag="Eyes:%d" % i):
                with m.at((math.cos(a) * r, 0.31, math.sin(a) * r), ry=rng.uniform(0, 180)):
                    for s in (-1, 1):
                        m.box((s * 0.34, 0, 0), (0.46, 0.08, 0.22), EYE[i], mat="Neon", name="Eye", ry=s * 12)


def teeth(m, rng):
    """Jagged turf flaps lying almost flat around the rim, pointing into the hole like teeth."""
    n = 13
    with m.ctx(stage="props", folder="Rim", collide=False):
        for k in range(n):
            a = k * 2 * math.pi / n + rng.uniform(-0.05, 0.05)
            L = rng.uniform(2.2, 3.0)                                  # tooth length
            w = 2 * math.pi * (R + 2.2) / n * rng.uniform(1.05, 1.3)
            hinge = R + L - 0.6                                         # tip reaches just over the black edge
            with m.ctx(tag="Tooth:%d" % k):
                with m.at((math.cos(a) * hinge, 0.12, math.sin(a) * hinge), ry=90 - math.degrees(a)):
                    with m.at((0, 0, 0), rx=rng.uniform(4, 9), rz=rng.uniform(-3, 3)):
                        segs = 4
                        for s in range(segs):
                            f0 = s / segs
                            ww = w * (1 - f0) ** 1.2 + 0.18
                            ln = L / segs + 0.08
                            z0 = -L * f0
                            m.box((0, 0.17, z0 - ln / 2), (ww, 0.22, ln), GRASS[(k + s) % 3])   # grass on top
                            m.box((0, 0.0, z0 - ln / 2), (ww * 0.97, 0.16, ln), DIRT[s % 2])    # soil edge
                        m.box((0, 0.06, -L - 0.12), (0.22, 0.2, 0.3), DIRT[1])
                        for t in range(2):                                                  # grass blades
                            m.box((rng.uniform(-w * 0.3, w * 0.3), 0.38, -rng.uniform(0.1, L * 0.4)),
                                  (0.14, rng.uniform(0.25, 0.5), 0.14), GRASS[3], rx=rng.uniform(-25, 25))
            if rng.random() < 0.6:                                      # small sliver between two teeth
                b = a + math.pi / n
                with m.ctx(tag="Tooth:%ds" % k):
                    with m.at((math.cos(b) * (R + 1.4), 0.1, math.sin(b) * (R + 1.4)), ry=90 - math.degrees(b)):
                        m.box((0, 0.14, -0.7), (0.6, 0.18, 1.4), GRASS[2])
                        m.box((0, 0.0, -0.7), (0.55, 0.12, 1.4), DIRT[1])


def mist(m, rng):
    with m.ctx(stage="props", folder="Mist", tag="Mist:0", collide=False, shadow=False):
        for i in range(12):
            a = rng.uniform(0, 2 * math.pi)
            r = rng.uniform(R - 2.0, R + 2.5)
            m.box((math.cos(a) * r, rng.uniform(0.45, 0.8), math.sin(a) * r),
                  (rng.uniform(1.6, 3.0), 0.12, rng.uniform(0.6, 1.2)), rng.choice(("#B48CFF", "#C9A6FF", "#9C6BFF")),
                  ry=math.degrees(-a) + rng.uniform(-20, 20), transparency=rng.uniform(0.55, 0.72), name="Mist")


def surroundings(m, rng):
    with m.ctx(stage="props", folder="Decor", tag="Cracks:0", collide=False, shadow=False):
        for k in range(9):
            a = k * 2 * math.pi / 9 + rng.uniform(-0.2, 0.2)
            r0 = R + 3.0
            for s in range(rng.randint(1, 3)):
                L = rng.uniform(1.0, 2.0)
                a2 = a + rng.uniform(-0.3, 0.3)
                x0, z0 = math.cos(a) * r0, math.sin(a) * r0
                x1, z1 = x0 + math.cos(a2) * L, z0 + math.sin(a2) * L
                mid = ((x0 + x1) / 2, 0.03, (z0 + z1) / 2)
                m.box(mid, (0.2 - 0.04 * s, 0.05, L + 0.1), "#2E2418", ry=math.degrees(math.atan2(x1 - x0, z1 - z0)))
                r0 = math.hypot(x1, z1)
                a = math.atan2(z1, x1)
    with m.ctx(stage="props", folder="Decor", tag="Clods:0", collide=False, shadow=False):
        for i in range(12):
            a = rng.uniform(0, 2 * math.pi)
            r = R + rng.uniform(3.0, 6.5)
            s = rng.uniform(0.3, 0.6)
            m.box((math.cos(a) * r, s * 0.3, math.sin(a) * r), (s, s * 0.6, s * 0.8), rng.choice(DIRT),
                  ry=rng.uniform(0, 90))


def preview_lawn(m):
    with m.ctx(stage="preview", folder="Preview", tag=None, collide=True):
        for i in range(-6, 6):
            for j in range(-4, 4):
                m.box((i * 4 + 2, -0.6, j * 4 + 2), (4, 1.2, 4), GRASS[(i + j) % 2 if (i * j) % 3 else 2])


def build(with_preview_lawn=False):
    rng = random.Random(13)
    m = Model("MonsterMouth")
    if with_preview_lawn:
        preview_lawn(m)
    hole(m)
    swirl(m)
    eyes(m, rng)
    teeth(m, rng)
    mist(m, rng)
    surroundings(m, rng)
    with m.ctx(stage="marker", folder="", tag=None, collide=False, shadow=False):
        m.box((0, 0.6, 0), (2 * R, 1.2, 2 * R), "#FFFFFF", name="MouthTrigger", transparency=1.0)
    for p in m.parts:
        p["light"] = None
    return m


if __name__ == "__main__":
    import json
    root = os.path.dirname(HERE)

    def pj(p, dy=0.0):
        return dict(size=p["size"], pos=[p["pos"][0], p["pos"][1] + dy, p["pos"][2]], R=p["R"], color=p["color"],
                    mat=p["mat"], light=None, stage=p["stage"], folder=p["folder"], tier=0, tag=p["tag"],
                    collide=p["collide"], shadow=p["shadow"], name=p.get("name"),
                    transparency=p.get("transparency", 0.0), effect=None)
    m = build()
    os.makedirs(os.path.join(root, "build"), exist_ok=True)
    json.dump(dict(name="MonsterMouth", attrs=dict(EventId="MonsterMouth"), parts=[pj(p) for p in m.parts],
                   scripts={"AnimateMouth": "maps/AnimateMouth.client.lua"}),
              open(os.path.join(root, "build", "MonsterMouth_export.json"), "w"))
    L = 120.0
    mp = build(with_preview_lawn=True)
    cams = {"top": ((0.01, L + 26, 0.0), (0, L, 0), 30),
            "angle": ((13, L + 11, 15), (0, L, 0), 30)}
    json.dump(dict(name="MonsterMouth", origin=[0, L, 0], water=[-600, 0, -600, 600, 0, 600],
                   preset=dict(ClockTime=14, WaterColor="#2E9BE6", AtmosphereColor="#C7DFFF"), cameras=cams,
                   parts=[pj(p, L) for p in mp.parts], texts=[]),
              open(os.path.join(root, "build", "MonsterMouth.json"), "w"))
    print("MonsterMouth: %d parts, %.1f studs across, %.2f studs tall" % (
        len(m.parts), 2 * max(math.hypot(p["pos"][0], p["pos"][2]) for p in m.parts),
        max(p["pos"][1] + p["size"][1] / 2 for p in m.parts if p.get("name") != "MouthTrigger")))
