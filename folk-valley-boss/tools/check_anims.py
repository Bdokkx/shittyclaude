"""Numbers behind the Reaper's animations, read back from the written KeyframeSequences:
where the blade is at each marker and through each attack window, what dips under
the ground, and how close the scythe's shaft and blade come to the body.

    python tools/check_anims.py <rig.json> <anims.json>
"""
import json
import sys

import numpy as np

import banim as B

A = B.A


def read_clips(path):
    folder = json.load(open(path))[0]
    out = {}
    for ks in folder["children"]:
        kfs = sorted((k for k in ks["children"] if k["class"] == "Keyframe"), key=lambda k: k["props"]["Time"]["Float32"])
        times, frames, markers = [], [], []
        for kf in kfs:
            t = kf["props"]["Time"]["Float32"]
            X = {}
            stack = [c for c in kf["children"] if c["class"] == "Pose"]
            while stack:
                p = stack.pop()
                if p["props"]["Weight"]["Float32"] > 0:
                    cf = p["props"]["CFrame"]["CFrame"]
                    m = np.eye(4)
                    m[:3, :3] = np.array(cf["orientation"], dtype=float)
                    m[:3, 3] = cf["position"]
                    X[p["name"]] = m
                stack.extend(c for c in p["children"] if c["class"] == "Pose")
            markers += [(t, c["name"]) for c in kf["children"] if c["class"] == "KeyframeMarker"]
            times.append(t)
            frames.append(X)
        out[ks["name"]] = {"times": np.array(times), "frames": frames, "markers": markers,
                           "loop": ks["props"]["Loop"]["Bool"], "length": times[-1],
                           "priority": ks["props"]["Priority"]["Enum"]}
    return out


def seg_dist(p, a, b):
    ab = b - a
    t = np.clip(np.dot(p - a, ab) / np.dot(ab, ab), 0, 1)
    return np.linalg.norm(p - (a + ab * t))


def main(rig_path, anims_path):
    rig = B.Rig(rig_path)
    data = json.load(open(rig_path))
    att = {a["Name"]: a for a in data["Attachments"]}
    rest = rig.fk({})
    clips = read_clips(anims_path)
    parts = rig.parts
    shaft = [np.array([4.78, y, -0.25, 1.0]) for y in np.linspace(0.6, 20.8, 22)]
    blade = [np.array([*att["BladeBase"]["Position"], 1.0]), np.array([*att["BladeTip"]["Position"], 1.0]),
             np.array([4.78, 17.6, -5.0, 1.0])]
    problems = 0
    for name, clip in clips.items():
        ys_low = []
        worst = (1e9, None)
        blade_y = []
        for t, X in zip(clip["times"], clip["frames"]):
            W = rig.fk(X)
            D = {b: W[b] @ np.linalg.inv(rest[b]) for b in W}
            # lowest corner of every part except the scythe (it may lie on the floor)
            for p in parts:
                if p["Model"] == "Scythe":
                    continue
                c, s = np.array(p["Center"]), np.array(p["Size"]) / 2
                lo = min((D[p["Model"]] @ np.array([*(c + s * (dx, dy, dz)), 1.0]))[1]
                         for dx in (-1, 1) for dy in (-1, 1) for dz in (-1, 1))
                if lo < -0.35:
                    ys_low.append((round(float(t), 2), p["Name"], round(float(lo), 2)))
            # the shaft and blade against the body (a capsule round the spine) and the head
            spine_a = (D["LowerTorso"] @ np.array([0, 7.5, 0, 1.0]))[:3]
            spine_b = (D["UpperTorso"] @ np.array([0, 14.5, 0, 1.0]))[:3]
            head = (D["Head"] @ np.array([0, 17.4, -0.1, 1.0]))[:3]
            for q in shaft + blade:
                w = (D["Scythe"] @ q)[:3]
                d = min(seg_dist(w, spine_a, spine_b) - 2.3, np.linalg.norm(w - head) - 2.4)
                if d < worst[0]:
                    worst = (d, round(float(t), 2))
            blade_y.append((float(t), min((D["Scythe"] @ q)[1] for q in blade), max((D["Scythe"] @ q)[1] for q in blade)))
        print("%-13s %5.2fs prio %d %s" % (name, clip["length"], clip["priority"], "loop" if clip["loop"] else ""))
        for t, m in clip["markers"]:
            i = int(np.argmin([abs(t - b[0]) for b in blade_y]))
            print("   marker %-10s t=%.2f  blade y %.1f .. %.1f" % (m, t, blade_y[i][1], blade_y[i][2]))
        names = [m for _, m in clip["markers"]]
        for a, b in (("SpinStart", "SpinEnd"), ("Release", "Catch")):
            if a in names and b in names:
                ta, tb = dict((m, t) for t, m in clip["markers"])[a], dict((m, t) for t, m in clip["markers"])[b]
                win = [v for v in blade_y if ta <= v[0] <= tb]
                print("   %s..%s blade y %.1f .. %.1f" % (a, b, min(v[1] for v in win), max(v[2] for v in win)))
        print("   scythe closest to body: %.2f studs at %ss" % worst)
        if ys_low:
            problems += 1
            by_part = {}
            for t, n, y in ys_low:
                by_part.setdefault(n, []).append((t, y))
            for n, v in by_part.items():
                print("   BELOW GROUND %-12s %d frames, lowest %.2f at %.2fs" % (n, len(v), min(y for _, y in v),
                                                                              min(v, key=lambda a: a[1])[0]))
        if worst[0] < -0.3:
            problems += 1
            print("   SCYTHE INSIDE BODY")
    print("problems:", problems)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
