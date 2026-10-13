"""Fill out/map/README.md's numbers and tables from the build's map_stats.json.

    python tools/map_readme.py <map_stats.json> <BuildPotatoMap.lua> <README template> <README out>
"""
import json
import os
import sys

HERO = {
    "Meadow": "the red-and-white windmill with turning sails and a potato scarecrow",
    "Dunes": "the stepped pyramid with a potato pharaoh",
    "Marsh": "the giant toadstool house",
    "Jungle": "the stepped temple with the golden idol",
    "Reef": "the shipwreck with the pirate potato",
    "Frost": "the ice castle gate",
    "Haunt": "the haunted manor and the giant jack-o'-lantern",
    "Lava": "the volcano with lava running down it",
    "Crystal": "the giant crystal cluster bursting out of a mine mouth",
    "Dino": "the huge dinosaur skeleton",
    "Toy": "the castle of building blocks and the toy train",
    "Candy": "the three-tier cake",
    "Clock": "the clock tower with its turning gears",
    "Neon": "the stage with speakers and beams of light on a floor grid",
    "Cloud": "the rainbow over the palace of cloud",
    "Cosmic": "the crashed rocket",
    "Void": "the huge black cube with lit edges",
    "Olympus": "the temple with the potato Zeus",
}
TOUCH = {
    "Frost": "icicles under both caps",
    "Lava": "glowing lava channels along both walls behind low rock kerbs (not walkable)",
    "Candy": "white icing drips under both caps and a red-and-white stripe band on top",
    "Cosmic": "Neon star specks on both walls, glowing star tiles on the ground",
    "Neon": "Neon strips along both walls and Neon lines at the lane's edges",
    "Marsh": "four patches of murky water, flush with the ground and walk-through",
    "Olympus": "white columns with gold capitals along both walls",
    "Toy": "toy-block bands in four colours along the foot of both walls",
    "Void": "glitch squares flickering on both walls",
}
SIDE = {"E": "east", "W": "west"}


def main(stats_path, lua_path, src, dst):
    st = json.load(open(stats_path))
    kb = os.path.getsize(lua_path) / 1024
    size = ("**%s parts**, %d of them written once as templates and copied %d times, so the script is %.0f KB."
            % (format(st["total"], ","), st["templates"], st["copies"], kb))
    rows = ["| # | Area | Ground / walls | Hero (wall) | Its own touch | Parts |", "|---|---|---|---|---|---|"]
    for a in st["areas"]:
        rows.append("| %d | %s (`%s`) | `%s` / `%s` | %s (%s) | %s | %s |" % (
            a["n"], a["name"], a["id"], a["ground"].upper(), a["wall"].upper(),
            HERO[a["id"]] if a["hero"] else "none yet", SIDE[a["side"]], TOUCH.get(a["id"], "none"),
            format(a["parts"], ",")))
    rows.append("")
    rows.append("Each row's parts count everything in `Fields/AreaN` and `Markers/AreaN`: the hero, the props, the "
                "Mounds, the sign and the shell. The yard has %s parts and the gate %s."
                % (format(st["tops"]["Yard"], ","), format(st["tops"]["Gate"], ",")))
    prev = "\n".join([
        "- `map_overview.jpg`: from (0, 60, 200) looking at (0, 0, −100), the view asked for in part 1.",
        "- `map_corridor.jpg`: from (0, 7, −40) looking north up the corridor.",
        "- `map_yard.jpg`: the yard from high over its south wall.",
        "- `map_gate.jpg`: the gate, the stalls and the avenue from the spawn.",
        "- `map_aerial.jpg`: high over the yard, looking up the whole corridor.",
        "- `map_area01_Meadow.jpg` … `map_area18_Olympus.jpg`: each area at eye height, from just inside its south "
        "end looking north."])
    s = open(src).read()
    s = s.replace("@@SIZE@@", size).replace("@@TOTAL@@", format(st["total"], ","))
    s = s.replace("@@AREAS@@", "\n".join(rows)).replace("@@PREVIEWS@@", prev)
    assert "@@" not in s
    open(dst, "w").write(s)
    print("wrote", dst)


if __name__ == "__main__":
    main(*sys.argv[1:5])
