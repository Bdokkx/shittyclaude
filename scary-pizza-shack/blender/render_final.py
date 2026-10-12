"""Final preview renders for the README.

    python blender/render_final.py <outdir> [interior] [front] [aerial] [yard] [samples=96]

R6-sized dummies (5 studs tall, preview only, not part of the map) stand in the queue
and at a couple of stations for scale.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy  # noqa: E402,I001
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

import scene_build  # noqa: E402
import spsblend as SB  # noqa: E402
import spsgeo as G  # noqa: E402
import rbxscene as rs  # noqa: E402

out = sys.argv[1]
os.makedirs(out, exist_ok=True)
want = set(a for a in sys.argv[2:] if "=" not in a) or {"interior", "front", "aerial", "yard"}
opts = dict(a.split("=") for a in sys.argv[2:] if "=" in a)
samples = int(opts.get("samples", 96))

sc = scene_build.build(items=False)
markers = {n.name: n for n in sc.root.get("Markers").children}
stations = {m.name: m for m in sc.root.get("Stations").children}


def dummy(b, cf, shirt=(70, 70, 76), skin=(200, 190, 170), pants=(40, 40, 46)):
    """Classic R6 block figure, feet at cf."""
    parts = [((2, 2, 1), (0, 3, 0), shirt), ((1, 2, 1), (-1.5, 3, 0), shirt), ((1, 2, 1), (1.5, 3, 0), shirt),
             ((1, 2, 1), (-0.5, 1, 0), pants), ((1, 2, 1), (0.5, 1, 0), pants), ((1.2, 1, 1.2), (0, 4.5, 0), skin)]
    for size, c, col in parts:
        g = G.box(*size, c=c)
        V = (cf.R @ np.array(g.v).T).T + cf.p
        b.add((col, "SmoothPlastic", 0.0), V, g.f)


def base_scene(night=True, people=()):
    scene = SB.reset()
    coll = bpy.data.collections.new("Map")
    scene.collection.children.link(coll)
    SB.realize(sc, coll)
    b = SB.Builder()
    for cf, kw in people:
        dummy(b, cf, **kw)
    b.build(coll)
    if night:
        SB.add_lights(sc, coll)
    return scene, coll


def save(path_png, path_jpg):
    Image.open(path_png).convert("RGB").save(path_jpg, quality=90)
    os.remove(path_png)
    print("saved", path_jpg)


if "interior" in want:
    st = stations
    people = [(st["DoughStation"].find("Stand").p["cf"], {}),
              (st["ServingWindow"].find("Stand").p["cf"], {"shirt": (150, 40, 40)})]
    scene, coll = base_scene(people=people)
    SB.night_world(scene, strength=0.15, moon=0.15)
    SB.point_light(coll, (0, 8.8, 0.5), 450, (1, 0.88, 0.7), name="Fill")
    rs.setup_render(scene, 1920, 1080, samples=samples)
    SB.camera(scene, (-14.2, 6.4, 8.6), (5.5, 3.3, -4.5), lens=15)
    p = os.path.join(out, "interior.png")
    rs.render(scene, p)
    save(p, os.path.join(out, "interior.jpg"))
    SB.camera(scene, (13.6, 6.6, -3.2), (-5.0, 3.6, 7.5), lens=15, name="Cam2")
    p = os.path.join(out, "interior_2.png")
    rs.render(scene, p)
    save(p, os.path.join(out, "interior_2.jpg"))

if "front" in want:
    q = [(markers["Queue%d" % k].p["cf"], {"shirt": col}) for k, col in
         ((1, (90, 96, 120)), (2, (110, 80, 70)), (3, (60, 70, 60)))]
    scene, coll = base_scene(people=q)
    SB.night_world(scene, strength=0.22, moon=0.35, moon_from=(-0.4, 0.8, 0.5))
    rs.setup_render(scene, 1920, 1080, samples=samples, exposure=0.3)
    SB.camera(scene, (14.0, 6.0, 44.0), (-1.0, 8.0, 8.0), lens=22)
    p = os.path.join(out, "front_night.png")
    rs.render(scene, p)
    save(p, os.path.join(out, "front_night.jpg"))

if "aerial" in want:
    scene, coll = base_scene(night=False)
    SB.day_world(scene, strength=0.95)
    rs.setup_render(scene, 1920, 1080, samples=max(32, samples // 2), bloom=False)
    SB.camera(scene, (62.0, 54.0, 78.0), (0.0, 0.0, -4.0), lens=28)
    p = os.path.join(out, "aerial.png")
    rs.render(scene, p)
    save(p, os.path.join(out, "aerial.jpg"))

if "yard" in want:
    people = [(markers["Inspection_Stand%d" % k].p["cf"], {"shirt": (80, 80, 90)}) for k in range(1, 5)]
    scene, coll = base_scene(people=people)
    SB.night_world(scene, strength=0.25, moon=0.45, moon_from=(0.5, 0.7, 0.4))
    rs.setup_render(scene, 1920, 1080, samples=samples, exposure=0.4)
    SB.camera(scene, (-6.0, 11.0, -12.5), (6.0, 1.5, -40.0), lens=20)
    p = os.path.join(out, "yard_night.png")
    rs.render(scene, p)
    save(p, os.path.join(out, "yard_night.jpg"))
