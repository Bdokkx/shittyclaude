"""Writes roblox/VoxelIslandBuilder.server.lua from the asset + map data."""
import os
import sys

from assets import ASSETS, bounds
from maps import build_island, build_reef
from palette import COLORS, CORAL_TINTS, INDEX, NAMES, TINT_NAMES

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def num(v):
    v = round(float(v), 3)
    if v == int(v):
        return str(int(v))
    return ("%.3f" % v).rstrip("0").rstrip(".")


def box_lua(b):
    return "{" + ",".join(num(v) for v in b[:6]) + "," + str(INDEX[b[6]]) + "}"


def prop_lua(p):
    name, x, y, z, rot, sc, tint, rx, rz = p
    return '{"%s",%s,%s,%s,%s,%s,%d,%s,%s}' % (name, num(x), num(y), num(z), num(rot), num(sc),
                                               tint, num(rx), num(rz))


def chunked(items, per_line=6, indent="\t\t"):
    lines = []
    for k in range(0, len(items), per_line):
        lines.append(indent + ",".join(items[k:k + per_line]) + ",")
    return "\n".join(lines)


def map_lua(m):
    out = ["{"]
    out.append("\tterrain = {\n" + chunked([box_lua(b) for b in m["terrain"]]) + "\n\t},")
    out.append("\tprops = {\n" + chunked([prop_lua(p) for p in m["props"]], 3) + "\n\t},")
    if m["water"]:
        out.append("\twater = {" + ",".join(num(v) for v in m["water"]) + "},")
    if m["spawn"]:
        out.append("\tspawn = {" + ",".join(num(v) for v in m["spawn"]) + "},")
    out.append("}")
    return "\n".join(out)


def data_lua():
    o = ["-- palette: {r, g, b, material}"]
    o.append("local PALETTE = {")
    for n in NAMES:
        r, g, b, mat = COLORS[n]
        o.append('\t{%d,%d,%d,"%s"}, -- %d %s' % (r, g, b, mat, INDEX[n], n))
    o.append("}")
    o.append("local PALETTE_INDEX = {" + ", ".join("%s=%d" % (n, INDEX[n]) for n in NAMES) + "}")
    o.append("local TINTS = { -- coral tints: " + ", ".join(TINT_NAMES))
    for t in TINT_NAMES:
        o.append("\t{%d,%d,%d}," % CORAL_TINTS[t])
    o.append("}")
    o.append("")
    o.append("-- assets: boxes {x0,y0,z0,x1,y1,z1,color}, lights {x,y,z,color,range,brightness}")
    o.append("local ASSETS = {}")
    for name, a in ASSETS.items():
        mn, mx = bounds(name)
        lights = ",".join("{%s,%s,%s,%d,%s,%s}" % (num(l[0]), num(l[1]), num(l[2]), INDEX[l[3]],
                                                    num(l[4]), num(l[5])) for l in a["lights"])
        fires = ",".join("{" + ",".join(num(v) for v in f) + "}" for f in a["fires"])
        o.append("ASSETS.%s = {" % name)
        o.append("\ttintable = %s," % ("true" if a["tintable"] else "false"))
        o.append("\tmin = {%s}, max = {%s}," % (",".join(num(v) for v in mn),
                                                ",".join(num(v) for v in mx)))
        o.append("\tlights = {%s}, fires = {%s}," % (lights, fires))
        o.append("\tboxes = {\n" + chunked([box_lua(b) for b in a["boxes"]], 4) + "\n\t},")
        o.append("}")
    o.append("local ASSET_ORDER = {" + ", ".join('"%s"' % n for n in ASSETS) + "}")
    o.append("")
    o.append("local MAPS = {}")
    o.append("MAPS.Island = " + map_lua(build_island()))
    o.append("MAPS.Reef = " + map_lua(build_reef()))
    return "\n".join(o)


def main():
    tmpl = open(os.path.join(HERE, "builder_template.lua")).read()
    src = tmpl.replace("--@@DATA@@", data_lua())
    out_dir = os.path.join(ROOT, "roblox")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "VoxelIslandBuilder.server.lua")
    with open(path, "w") as f:
        f.write(src)
    print("wrote", path, len(src) // 1024, "KB")


if __name__ == "__main__":
    sys.exit(main())
