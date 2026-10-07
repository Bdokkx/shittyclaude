"""Turn a parts dump (tools/dump_parts.luau JSON) of the Maps file into build/<Name>.json for tools/render_spear.py.
Everything is lifted by LIFT studs because the renderer's sea sits at y=0 and the arenas' floor is at y=0."""
import json
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "spear"))
from core import euler  # noqa: E402

LIFT = 120.0
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def cams(cy):
    return {
        "overview": ((150, cy + 150, 260), (0, cy - 15, 0), 30),
        "field": ((0, cy + 7, 146), (0, cy + 3, 20), 30),
        "side": ((-190, cy + 40, -60), (0, cy, 0), 30),
    }


def convert(dump, name, out_name, lift=LIFT):
    parts = []
    for e in dump:
        if not e["path"].startswith("Maps/%s/" % name) or "pos" not in e or e["tr"] >= 0.99:
            continue
        rx, ry, rz = e["rot"]
        mat = e["mat"] if e["mat"] in ("Neon", "Glass") else "Plastic"
        parts.append(dict(size=e["size"], pos=[e["pos"][0], e["pos"][1] + lift, e["pos"][2]], R=euler(rx, ry, rz),
                          color="#%02X%02X%02X" % tuple(e["color"]), mat=mat, light=None, stage="terrain",
                          folder="x", tier=0, tag=None, collide=True, shadow=True, name=e["name"],
                          transparency=e["tr"], effect=None))
    data = dict(name=out_name, origin=[0, lift, 0], water=[-600, 0, -600, 600, 0, 600],
                preset=dict(ClockTime=14, WaterColor="#2E9BE6", AtmosphereColor="#C7DFFF"),
                cameras=cams(lift), parts=parts, texts=[])
    os.makedirs(os.path.join(ROOT, "build"), exist_ok=True)
    json.dump(data, open(os.path.join(ROOT, "build", out_name + ".json"), "w"))
    return len(parts)


if __name__ == "__main__":
    dump = json.load(open(sys.argv[1]))
    for n in sys.argv[2:]:
        print(n, convert(dump, n, "Orig" + n))
