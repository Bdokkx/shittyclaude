"""Final preview renders for the README.

    python blender/render_final.py <outdir> [shot ...] [samples=48] [test=1]

Shots: interior, interior_2, front, aerial, yard. Without test=1 each shot renders its
first camera at 1920 x 1080; test=1 renders every candidate camera small and fast
(<shot>_<k>.jpg) for choosing between them.

R6-sized dummies (5 studs tall, preview only, not part of the map) stand at a few
stations and in the queue for scale: staff in the classic yellow / blue / green, the
customers in dull colours.
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
opts = dict(a.split("=") for a in sys.argv[2:] if "=" in a)
samples = int(opts.get("samples", 48))
test = bool(opts.get("test"))

sc = scene_build.build(items=False)
markers = {n.name: n for n in sc.root.get("Markers").children}
stations = {m.name: m for m in sc.root.get("Stations").children}

STAFF = {"shirt": (13, 105, 172), "arms": (245, 205, 48), "skin": (245, 205, 48), "pants": (40, 127, 71)}


def stand(station, name="Stand"):
    return stations[station].find(name).p["cf"]


def queue(n=3):
    shirts = ((120, 126, 150), (150, 110, 95), (95, 115, 95))
    return [(markers["Queue%d" % (k + 1)].p["cf"], {"shirt": shirts[k]}) for k in range(n)]


def dummy(b, cf, shirt=(70, 70, 76), skin=(200, 190, 170), pants=(40, 40, 46), arms=None):
    """Classic R6 block figure, feet at cf."""
    arms = arms or shirt
    parts = [((2, 2, 1), (0, 3, 0), shirt), ((1, 2, 1), (-1.5, 3, 0), arms), ((1, 2, 1), (1.5, 3, 0), arms),
             ((1, 2, 1), (-0.5, 1, 0), pants), ((1, 2, 1), (0.5, 1, 0), pants), ((1.2, 1, 1.2), (0, 4.5, 0), skin)]
    for size, c, col in parts:
        g = G.box(*size, c=c)
        V = (cf.R @ np.array(g.v).T).T + cf.p
        b.add((col, "SmoothPlastic", 0.0), V, g.f)


def inside_light(scene, coll):
    SB.night_world(scene, strength=0.15, moon=0.15)
    SB.point_light(coll, (0, 8.8, 0.5), 450, (1, 0.88, 0.7), name="Fill")


# shot: night or day, who stands where, the world, exposure, candidate cameras
# (position, look-at, lens), the first one is the final
SHOTS = {
    "interior": dict(
        people=lambda: [(stand("SauceStation", "StandSauce"), STAFF), (stand("Oven"), STAFF)],
        world=inside_light,
        cams=[((-11.5, 7.0, 4.5), (8.0, 3.0, -5.0), 15),
              ((-11.8, 6.6, 5.0), (8.0, 3.2, -4.0), 15)]),
    "interior_2": dict(
        people=lambda: [(stand("ServingWindow"), STAFF), (stand("CCTVDesk"), STAFF)] + queue(),
        world=inside_light,
        cams=[((11.0, 6.0, -2.0), (-2.0, 4.2, 9.0), 16),
              ((4.5, 6.0, -1.5), (-2.0, 4.6, 13.0), 16)]),
    "front": dict(
        people=queue,
        world=lambda scene, coll: SB.night_world(scene, strength=0.22, moon=0.35, moon_from=(-0.4, 0.8, 0.5)),
        exposure=0.3,
        cams=[((8.0, 5.0, 45.0), (0.0, 10.5, 8.0), 22),
              ((12.0, 5.5, 46.0), (-1.0, 10.5, 8.0), 22)]),
    "aerial": dict(
        night=False,
        world=lambda scene, coll: SB.day_world(scene, strength=0.95),
        bloom=False,
        cams=[((62.0, 54.0, 78.0), (0.0, 0.0, -4.0), 28),
              ((-60.0, 58.0, 80.0), (0.0, 0.0, -6.0), 28)]),
    "yard": dict(
        people=lambda: [(markers["Inspection_Stand%d" % k].p["cf"], {"shirt": (120, 120, 132)}) for k in range(1, 5)],
        world=lambda scene, coll: SB.night_world(scene, strength=0.3, moon=0.7, moon_from=(0.5, 0.7, 0.4)),
        exposure=1.0,
        cams=[((24.0, 10.0, -14.0), (-8.0, 1.5, -40.0), 20),
              ((22.0, 12.0, -13.0), (-6.0, 1.0, -38.0), 18)]),
}
FILES = {"interior": "interior", "interior_2": "interior_2", "front": "front_night", "aerial": "aerial",
         "yard": "yard_night"}


def save(path_png, path_jpg):
    Image.open(path_png).convert("RGB").save(path_jpg, quality=90)
    os.remove(path_png)
    print("saved", path_jpg)


def render_shot(name, shot):
    scene = SB.reset()
    coll = bpy.data.collections.new("Map")
    scene.collection.children.link(coll)
    SB.realize(sc, coll)
    b = SB.Builder()
    for cf, kw in shot.get("people", list)():
        dummy(b, cf, **kw)
    b.build(coll)
    night = shot.get("night", True)
    if night:
        SB.add_lights(sc, coll)
    shot["world"](scene, coll)
    w, h = (640, 360) if test else (1920, 1080)
    n = 8 if test else (samples if night else max(32, samples // 2))
    rs.setup_render(scene, w, h, samples=n, bloom=shot.get("bloom", True), exposure=shot.get("exposure", 0.0))
    cams = shot["cams"] if test else shot["cams"][:1]
    for k, (pos, tgt, lens) in enumerate(cams):
        SB.camera(scene, pos, tgt, lens=lens, name="Cam%d" % k)
        stem = "%s_%d" % (FILES[name], k) if test else FILES[name]
        p = os.path.join(out, stem + ".png")
        rs.render(scene, p)
        save(p, os.path.join(out, stem + ".jpg"))


for name in [a for a in sys.argv[2:] if "=" not in a] or list(SHOTS):
    render_shot(name, SHOTS[name])
