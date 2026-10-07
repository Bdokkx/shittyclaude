"""Build the four arenas: build/maps_export.json (for tools/export_maps.luau) and build/Arena<Map>.json
(lifted copies for tools/render_spear.py previews).

    python3 maps/build_maps.py [Meadow Farm Snow Desert]
"""
import json
import os
import sys
import time

from arenas import build, check
from to_preview import LIFT, cams

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "spear"))
from core import IDENT  # noqa: E402

LINE = {"Snow": "#2F80ED"}


def field_preview(name, colors, trim):
    """The kept field (tiles recoloured, trim, lines) so the previews show the whole map."""
    out = [dict(size=[156, 2, 306], pos=[0, -2.2 + LIFT, 0], R=IDENT, color=trim, mat="Plastic", stage="terrain")]
    for key, col in colors.items():
        x, z = (float(v) for v in key.split(","))
        out.append(dict(size=[15, 3, 15], pos=[x, -1.5 + LIFT, z], R=IDENT, color=col, mat="Plastic", stage="terrain"))
    for z in (-125, 125):
        out.append(dict(size=[150, 0.3, 1.6], pos=[0, 0.1 + LIFT, z], R=IDENT, color=LINE.get(name, "#FFFFFF"),
                        mat="Plastic", stage="terrain"))
    for p in out:
        p.update(light=None, folder="Field", tier=0, tag=None, collide=True, shadow=True, name=None, transparency=0.0,
                 effect=None)
    return out

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def part_json(p, lift=0.0):
    return dict(size=p["size"], pos=[p["pos"][0], p["pos"][1] + lift, p["pos"][2]], R=p["R"], color=p["color"],
                mat=p["mat"], light=None, stage=p["stage"], folder=p["folder"], tier=0, tag=p["tag"],
                collide=p["collide"], shadow=p["shadow"], name=p.get("name"), transparency=p.get("transparency", 0.0),
                effect=None)


if __name__ == "__main__":
    names = sys.argv[1:] or ["Meadow", "Farm", "Snow", "Desert"]
    out = {}
    for n in names:
        t = time.time()
        m, colors, trim = build(n)
        bad = check(m)
        assert not bad, (n, bad[:5])
        out[n] = dict(parts=[part_json(p) for p in m.parts], texts=m.texts, field=colors, trim=trim)
        prev = dict(name="Arena" + n, origin=[0, LIFT, 0], water=[-600, 0, -600, 600, 0, 600],
                    preset=dict(ClockTime=14, WaterColor="#2E9BE6", AtmosphereColor="#C7DFFF"), cameras=cams(LIFT),
                    parts=[part_json(p, LIFT) for p in m.parts] + field_preview(n, colors, trim), texts=m.texts)
        json.dump(prev, open(os.path.join(ROOT, "build", "Arena%s.json" % n), "w"))
        print("%-7s %5d parts  (%.1fs)" % (n, len(m.parts), time.time() - t))
    path = os.path.join(ROOT, "build", "maps_export.json")
    old = json.load(open(path)) if os.path.exists(path) and len(names) < 4 else {}
    old.update(out)
    json.dump(old, open(path, "w"))
