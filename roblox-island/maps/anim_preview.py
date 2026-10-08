"""Preview of AnimateScenery: applies the same ghost/bat motion (Python port of AnimateScenery.client.lua) to
build/ArenaOctober.json and writes one JSON per frame for tools/render_spear.py.

    python3 maps/anim_preview.py <frames> <fps> [house|cauldron]   -> build/ArenaOctober_f00.json ...
"""
import json
import math
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "spear"))
from core import euler, mmul, mvec  # noqa: E402


def tr(R):
    return tuple(tuple(R[j][i] for j in range(3)) for i in range(3))


class CF:
    def __init__(self, p, R):
        self.p, self.R = tuple(p), tuple(tuple(r) for r in R)

    def __mul__(self, o):
        return CF([self.p[i] + mvec(self.R, o.p)[i] for i in range(3)], mmul(self.R, o.R))

    def inv(self):
        Rt = tr(self.R)
        return CF([-v for v in mvec(Rt, self.p)], Rt)


def T(x=0.0, y=0.0, z=0.0):
    return CF((x, y, z), euler())


def ang(rx=0.0, ry=0.0, rz=0.0):
    """Radians, CFrame.Angles order (R = Rx * Ry * Rz)."""
    from core import _rx, _ry, _rz
    return CF((0, 0, 0), mmul(mmul(_rx(rx), _ry(ry)), _rz(rz)))


def look_at(pos, target):
    f = [target[i] - pos[i] for i in range(3)]
    n = math.sqrt(sum(v * v for v in f))
    f = [v / n for v in f]
    r = [-f[2], 0, f[0]]                       # forward x up
    rn = math.sqrt(sum(v * v for v in r))
    r = [v / rn for v in r]
    u = [r[1] * f[2] - r[2] * f[1], r[2] * f[0] - r[0] * f[2], r[0] * f[1] - r[1] * f[0]]
    back = [-v for v in f]                     # Roblox: LookVector = -Z
    return CF(pos, ((r[0], u[0], back[0]), (r[1], u[1], back[1]), (r[2], u[2], back[2])))


def main():
    frames, fps = int(sys.argv[1]), float(sys.argv[2])
    view = sys.argv[3] if len(sys.argv) > 3 else "house"
    data = json.load(open(os.path.join(ROOT, "build", "ArenaOctober.json")))
    groups = {}
    for i, p in enumerate(data["parts"]):
        tag = p.get("tag") or ""
        if tag.startswith(("Ghost:", "Bat:", "Cauldron:")):
            groups.setdefault(tag, []).append(i)
    rng = random.Random(4)
    ghosts, bats, cauldrons = [], [], []
    for tag, idx in groups.items():
        body = data["parts"][idx[0]]
        pivot = CF(body["pos"], body["R"])
        item = dict(base=pivot, parts=[(i, pivot.inv() * CF(data["parts"][i]["pos"], data["parts"][i]["R"]),
                                        data["parts"][i].get("name")) for i in idx],
                    phase=rng.random() * 10, speed=0.8 + rng.random() * 0.5)
        if tag.startswith("Cauldron"):
            cauldrons.append(item)
        else:
            (ghosts if tag.startswith("Ghost") else bats).append(item)
    centre = [sum(b["base"].p[i] for b in bats) / len(bats) for i in range(3)]
    for b in bats:
        off = [b["base"].p[i] - centre[i] for i in range(3)]
        b["radius"] = max(6.0, math.hypot(off[0], off[2]))
        b["angle0"] = math.atan2(off[2], off[0])
        b["height"] = off[1]
        b["dir"] = 1 if rng.random() < 0.75 else -1
        b["angular"] = (0.5 + rng.random() * 0.5) * b["dir"]
    for c in cauldrons:
        brew = [(i, rel) for i, rel, name in c["parts"] if name == "Brew"]
        c["brew"] = brew
        c["bubbles"] = [i for i, rel, name in c["parts"] if name == "Bubble"]
        top = max(rel.p[1] + data["parts"][i]["size"][1] / 2 for i, rel in brew)
        c["centre"] = (sum(rel.p[0] for _, rel in brew) / len(brew), top, sum(rel.p[2] for _, rel in brew) / len(brew))

    def h(x):
        v = math.sin(x * 12.9898) * 43758.5453
        return v - math.floor(v)
    hl, hr = T(-0.35, 0.15, 0), T(0.35, 0.15, 0)
    for f in range(frames):
        t = f / fps
        out = json.loads(json.dumps(data))
        for g in ghosts:
            s = t * g["speed"] + g["phase"]
            pose = g["base"] * T(math.cos(s * 0.35) * 2.5, math.sin(s * 1.6) * 1.2, math.sin(s * 0.35) * 2.5) * \
                ang(math.sin(s * 1.1) * 0.06, math.sin(s * 0.4) * 0.7, math.sin(s * 1.3) * 0.1)
            wave = math.sin(s * 3) * 0.35
            for i, rel, name in g["parts"]:
                if name in ("ArmL", "ArmR"):
                    side = -1 if name == "ArmL" else 1
                    sh = T(side * 1.2, rel.p[1] + 0.6, 0)
                    cf = pose * (sh * ang(0, 0, side * wave) * sh.inv() * rel)
                else:
                    cf = pose * rel
                out["parts"][i]["pos"], out["parts"][i]["R"] = list(cf.p), [list(r) for r in cf.R]
        for b in bats:
            a = b["angle0"] + t * b["angular"]
            pos = [centre[0] + math.cos(a) * b["radius"], centre[1] + b["height"] + math.sin(t * 2 + b["phase"]) * 1.5,
                   centre[2] + math.sin(a) * b["radius"]]
            tan = [-math.sin(a) * b["dir"], 0, math.cos(a) * b["dir"]]
            pose = look_at(pos, [pos[i] + tan[i] for i in range(3)]) * ang(0, 0, -0.35 * b["dir"])
            flap = math.sin(t * 14 * b["speed"] + b["phase"]) * 0.7
            for i, rel, name in b["parts"]:
                if name == "WingL":
                    cf = pose * (hl * ang(0, 0, -flap) * hl.inv() * rel)
                elif name == "WingR":
                    cf = pose * (hr * ang(0, 0, flap) * hr.inv() * rel)
                else:
                    cf = pose * rel
                out["parts"][i]["pos"], out["parts"][i]["R"] = list(cf.p), [list(r) for r in cf.R]
        for c in cauldrons:
            piv = c["base"]
            churn = math.sin(t * 3.1) * 0.05
            for j, (i, rel) in enumerate(c["brew"]):
                cf = piv * T(0, churn, 0) * rel * ang(0, math.sin(t * 0.8 + j + 1) * 0.04, 0)
                out["parts"][i]["pos"], out["parts"][i]["R"] = list(cf.p), [list(r) for r in cf.R]
            for j, i in enumerate(c["bubbles"], 1):
                period, phase = 1.1 + ((j - 1) % 4) * 0.23, (j - 1) * 0.37
                x = (t + phase) / period
                cyc = math.floor(x)
                u = x - cyc
                a = h(cyc * 7.13 + j) * math.pi * 2
                r = math.sqrt(h(cyc * 3.71 + j * 1.3)) * 1.6
                if u < 0.75:
                    size, tr_ = 0.2 + 0.55 * (u / 0.75), 0.0
                else:
                    k_ = (u - 0.75) / 0.25
                    size, tr_ = 0.75 + 0.45 * k_, min(1.0, k_ * 1.6)
                cx, cy, cz = c["centre"]
                cf = piv * T(cx + math.cos(a) * r + math.sin(t * 9 + j) * 0.08, cy + 0.1 + u * 1.6, cz + math.sin(a) * r) \
                    * ang(0, u * 2 + j, 0)
                out["parts"][i].update(pos=list(cf.p), R=[list(rr) for rr in cf.R], size=[size] * 3, transparency=tr_)
        out["name"] = "ArenaOctober_f%02d" % f
        L = data["origin"][1]
        if view == "cauldron":
            c = cauldrons[0]["base"].p
            out["cameras"] = {"anim": ((c[0] + 12, c[1] + 6.0, c[2] + 7), (c[0], c[1] + 3.0, c[2]), 32)}
        else:
            out["cameras"] = {"anim": ((-48, L + 30, 14), (-108, L + 30, 74), 30)}
        json.dump(out, open(os.path.join(ROOT, "build", out["name"] + ".json"), "w"))
    print("frames", frames, "ghosts", len(ghosts), "bats", len(bats))


if __name__ == "__main__":
    main()
