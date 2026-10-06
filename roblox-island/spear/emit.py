"""Write an island Model out as a standalone Luau builder (roblox/builders/<Map>Builder.server.lua)
and as JSON for the Blender renders / checks (build/<Map>.json)."""
import json
import os

from core import to_euler

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def part_folder(p):
    return p["folder"] if not p["tier"] else "Tier%d/%s" % (p["tier"], p["folder"])


def _num(v):
    s = ("%.3f" % v).rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def emit(m, origin, preset, water, spawn, cameras=None):
    colors, cidx = [], {}
    mats, midx = [], {}
    folders, fidx = [], {}

    def idx(table, index, key):
        if key not in index:
            index[key] = len(table) + 1
            table.append(key)
        return index[key]

    rows, lights, names, transp = [], [], [], []
    for i, p in enumerate(m.parts, 1):
        rx, ry, rz = to_euler(p["R"])
        decor = p["stage"] in ("props", "reef") and max(p["size"]) < 2   # small decor: no collision, no shadow
        flags = (1 if p["collide"] and not decor else 0) | (2 if p["shadow"] and not decor else 0)
        rows.append("{%s}" % ",".join([*map(_num, p["size"]), *map(_num, p["pos"]), _num(rx), _num(ry), _num(rz),
                                        str(idx(colors, cidx, p["color"].upper())), str(idx(mats, midx, p["mat"])),
                                        str(idx(folders, fidx, part_folder(p))), str(flags)]))
        if p.get("transparency"):
            transp.append("[%d]=%s" % (i, _num(p["transparency"])))
        if p.get("name"):
            names.append('[%d]="%s"' % (i, p["name"]))
        if p["light"]:
            kind, bright, rng, col = p["light"]
            lights.append('[%d]={"%s",%s,%s,%d}' % (i, kind, _num(bright), _num(rng), idx(colors, cidx, col.upper())))
    texts = ['{%d,%s,%d,"%s"}' % (t["part"] + 1, json.dumps(t["text"]), idx(colors, cidx, t["color"].upper()), t["face"])
             for t in m.texts]
    preset_lua = ",".join("%s=%s" % (k, ("{%d,%d,%d}" % hex_rgb(v)) if isinstance(v, str) else _num(v))
                          for k, v in preset.items())
    src = open(os.path.join(HERE, "builder_template.lua")).read()
    rep = {
        "@@MAP@@": m.name,
        "@@ORIGIN@@": ", ".join(map(_num, origin)),
        "@@COLORS@@": ",".join("{%d,%d,%d}" % hex_rgb(c) for c in colors),
        "@@MATS@@": ",".join('"%s"' % x for x in mats),
        "@@FOLDERS@@": ",".join('"%s"' % x for x in folders),
        "@@PARTS@@": ",\n".join(rows),
        "@@LIGHTS@@": ",".join(lights),
        "@@NAMES@@": ",".join(names),
        "@@TRANSP@@": ",".join(transp),
        "@@TEXTS@@": ",".join(texts),
        "@@PRESET@@": preset_lua,
        "@@WATER@@": ",".join(map(_num, water)),
        "@@SPAWN@@": ", ".join(map(_num, spawn)),
    }
    for k, v in rep.items():
        src = src.replace(k, v)
    out_dir = os.path.join(ROOT, "roblox", "builders")
    os.makedirs(out_dir, exist_ok=True)
    lua_path = os.path.join(out_dir, m.name + "Builder.server.lua")
    open(lua_path, "w").write(src)

    jdir = os.path.join(ROOT, "build")
    os.makedirs(jdir, exist_ok=True)
    data = dict(name=m.name, origin=origin, water=water, preset=preset, cameras=cameras or {},
                parts=[dict(size=p["size"], pos=p["pos"], R=p["R"], color=p["color"], mat=p["mat"],
                            light=p["light"], stage=p["stage"], folder=p["folder"], tier=p["tier"],
                            tag=p["tag"], collide=p["collide"], shadow=p["shadow"], name=p.get("name"),
                            transparency=p.get("transparency", 0.0)) for p in m.parts],
                texts=m.texts)
    json_path = os.path.join(jdir, m.name + ".json")
    json.dump(data, open(json_path, "w"))
    return lua_path, json_path, len(m.parts)
