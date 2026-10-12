"""Quick check renders while modelling.

    python blender/render_check.py <outdir> [plan] [inside] [front] [samples=32]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy  # noqa: E402,I001
import numpy as np  # noqa: E402

import scene_build  # noqa: E402
import spsblend as SB  # noqa: E402
import rbxscene as rs  # noqa: E402

out = sys.argv[1]
os.makedirs(out, exist_ok=True)
want = set(a for a in sys.argv[2:] if "=" not in a) or {"plan", "inside", "front", "site"}
opts = dict(a.split("=") for a in sys.argv[2:] if "=" in a)
samples = int(opts.get("samples", 32))

sc = scene_build.build(outside="outside" in opts or True, items=False)


def roofless(n):
    path = n.path()
    if "/Roof/" in path or "/PizzaSign/" in path:
        return False
    if n.p["cf"].p[1] > 9.25 and "/Stations/" in path:
        return False
    return True


def fresh():
    scene = SB.reset()
    coll = bpy.data.collections.new("Map")
    scene.collection.children.link(coll)
    return scene, coll


if "plan" in want:
    scene, coll = fresh()
    SB.realize(sc, coll, roofless)
    SB.day_world(scene, strength=1.1)
    rs.setup_render(scene, 1700, 1050, samples=samples, bloom=False)
    SB.camera(scene, (0, 60, 0.001), (0, 0, 0), ortho=38)
    rs.render(scene, os.path.join(out, "plan.png"))

if "inside" in want:
    scene, coll = fresh()
    SB.realize(sc, coll)
    SB.night_world(scene, strength=0.25, moon=0.2)
    SB.add_lights(sc, coll)
    SB.point_light(coll, (0, 8.6, 0), 900, (1, 0.9, 0.75), name="Fill")
    rs.setup_render(scene, 1600, 900, samples=samples)
    SB.camera(scene, (-14.5, 5.6, 7.5), (6, 3.2, -4), lens=16)
    rs.render(scene, os.path.join(out, "inside_a.png"))
    SB.camera(scene, (12, 5.6, -3.5), (-4, 3.6, 7), lens=16, name="Cam2")
    rs.render(scene, os.path.join(out, "inside_b.png"))

if "front" in want:
    scene, coll = fresh()
    SB.realize(sc, coll)
    SB.night_world(scene, strength=0.5, moon=0.6)
    SB.add_lights(sc, coll)
    rs.setup_render(scene, 1600, 900, samples=samples)
    SB.camera(scene, (16, 7, 42), (0, 7, 5), lens=24)
    rs.render(scene, os.path.join(out, "front.png"))

if "site" in want:
    scene, coll = fresh()
    SB.realize(sc, coll, lambda n: n.top() != "Items")
    SB.day_world(scene, strength=1.0)
    rs.setup_render(scene, 1400, 1600, samples=samples, bloom=False)
    SB.camera(scene, (0, 200, -5.999), (0, 0, -6), ortho=150)
    rs.render(scene, os.path.join(out, "site.png"))
    SB.camera(scene, (0, 400, 0.001), (0, 0, 0), ortho=340, name="Map")
    scene.render.resolution_x, scene.render.resolution_y = 1700, 1150
    rs.render(scene, os.path.join(out, "map.png"))

if "aerial" in want:
    scene, coll = fresh()
    SB.realize(sc, coll, lambda n: n.top() != "Items")
    SB.day_world(scene, strength=1.0)
    rs.setup_render(scene, 1600, 900, samples=samples, bloom=False)
    SB.camera(scene, (55, 50, 70), (0, 0, 0), lens=30)
    rs.render(scene, os.path.join(out, "aerial.png"))
