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
    if "groups" in m:
        out.append("\tgroups = {")
        for gname, boxes in m["groups"]:
            out.append('\t\t{ name = "%s", boxes = {\n%s\n\t\t} },' % (gname, chunked([box_lua(b) for b in boxes], 6, "\t\t\t")))
        out.append("\t},")
    else:
        out.append("\tterrain = {\n" + chunked([box_lua(b) for b in m["terrain"]]) + "\n\t},")
    out.append("\tprops = {\n" + chunked([prop_lua(p) for p in m["props"]], 3) + "\n\t},")
    if m["water"]:
        out.append("\twater = {" + ",".join(num(v) for v in m["water"]) + "},")
    if m["spawn"]:
        out.append("\tspawn = {" + ",".join(num(v) for v in m["spawn"]) + "},")
    out.append("}")
    return "\n".join(out)


def data_lua(maps, asset_names=None):
    """maps: list of (name, origin, map dict). asset_names: assets to include (default: those used)."""
    if asset_names is None:
        asset_names = sorted({p[0] for _, _, m in maps for p in m["props"]})
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
    for name in asset_names:
        a = ASSETS[name]
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
    o.append("local ASSET_ORDER = {" + ", ".join('"%s"' % n for n in asset_names) + "}")
    o.append("")
    o.append("local MAPS = {}")
    for name, origin, m in maps:
        o.append("table.insert(MAPS, { name = \"%s\", origin = Vector3.new(%s, %s, %s), data = %s })"
                 % (name, num(origin[0]), num(origin[1]), num(origin[2]), map_lua(m)))
    return "\n".join(o)


def all_maps():
    from themes import ORDER, ORIGINS, THEMES
    out = []
    for theme in ORDER:
        m = build_island(theme)
        out.append((THEMES[theme]["map"], ORIGINS[THEMES[theme]["map"]], m))
    out.insert(1, ("CoralReef", ORIGINS["CoralReef"], build_reef()))
    return out


def main():
    tmpl = open(os.path.join(HERE, "builder_template.lua")).read()
    out_dir = os.path.join(ROOT, "roblox", "builders")
    os.makedirs(out_dir, exist_ok=True)
    for name, origin, m in all_maps():
        src = tmpl.replace("--@@DATA@@", data_lua([(name, origin, m)]))
        path = os.path.join(out_dir, name + "Builder.server.lua")
        with open(path, "w") as f:
            f.write(src)
        print("wrote", os.path.relpath(path, ROOT), len(src) // 1024, "KB")
    # every asset, no maps: used to export the asset library model
    src = tmpl.replace("--@@DATA@@", data_lua([], list(ASSETS)))
    with open(os.path.join(out_dir, "AssetLibrary.lua"), "w") as f:
        f.write(src)


if __name__ == "__main__":
    sys.exit(main())
