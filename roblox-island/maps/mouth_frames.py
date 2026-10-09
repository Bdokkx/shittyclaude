"""Preview frames of AnimateMouth (same motion as maps/AnimateMouth.client.lua): build/MonsterMouth_fNN.json."""
import json
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "spear"))
from core import euler, mmul  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def rot_y(p, a, cy):
    """Rotate a part about the vertical axis through the mouth centre (Roblox CFrame.Angles(0, a, 0))."""
    Ry = euler(0, math.degrees(a), 0)
    x, z = p["pos"][0], p["pos"][2]
    c, s = math.cos(a), math.sin(a)
    p["pos"] = [x * c + z * s, p["pos"][1], -x * s + z * c]
    p["R"] = [list(r) for r in mmul(Ry, p["R"])]


if __name__ == "__main__":
    frames, fps = int(sys.argv[1]), float(sys.argv[2])
    base = json.load(open(os.path.join(ROOT, "build", "MonsterMouth.json")))
    rng = random.Random(3)
    mist_ph = {i: (rng.random() * 10, 0.08 + rng.random() * 0.1) for i, p in enumerate(base["parts"]) if p.get("name") == "Mist"}
    blinks = {}
    for f in range(frames):
        t = f / fps
        d = json.loads(json.dumps(base))
        for i, p in enumerate(d["parts"]):
            if p.get("name") == "Swirl":
                rot_y(p, -t * 0.7, 0)
            elif p.get("name") == "Mist":
                ph, sp = mist_ph[i]
                s = t * sp + ph
                rot_y(p, s - ph, 0)
                p["transparency"] = min(0.95, max(0.0, p["transparency"] + math.sin(s * 9) * 0.12))
            elif p.get("name") == "Eye":
                tag = p["tag"]
                if tag not in blinks:
                    blinks[tag] = rng.uniform(0.3, 2.0)
                if 0 <= t - blinks[tag] < 0.15:
                    p["transparency"] = 1.0
        d["name"] = "MonsterMouth_f%02d" % f
        d["cameras"] = {"top": d["cameras"]["top"]}
        json.dump(d, open(os.path.join(ROOT, "build", d["name"] + ".json"), "w"))
