"""Look at Folk Valley's props as the owner built them: every part a box, every face Inlet.

    python blender/fv_view.py <folk_valley_props.json> <outdir> [tile=224] [samples=10] [groups=Meadow,Farm]

Writes one contact sheet per group (sheet_<group>_<n>.jpg): each prop seen from the front, its
right, the back, its left (25 degrees up) and from above, with its part count.
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy  # noqa: E402,I001
import numpy as np  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

import spsblend as SB  # noqa: E402
import spslib  # noqa: E402
import rbxscene as rs  # noqa: E402
from spsgeo import CF  # noqa: E402

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
SURF = {"In": "inlet", "St": "studs", "Sm": "smooth", "We": "wedge"}


def orientation(rx, ry, rz):
    """CFrame.fromOrientation(rx, ry, rz): Y, then X, then Z (radians)."""
    cx, sx_ = math.cos(rx), math.sin(rx)
    cy, sy_ = math.cos(ry), math.sin(ry)
    cz, sz_ = math.cos(rz), math.sin(rz)
    Rx = np.array(((1, 0, 0), (0, cx, -sx_), (0, sx_, cx)))
    Ry = np.array(((cy, 0, sy_), (0, 1, 0), (-sy_, 0, cy)))
    Rz = np.array(((cz, -sz_, 0), (sz_, cz, 0), (0, 0, 1)))
    return Ry @ Rx @ Rz


def surfaces(code):
    if code in SURF:
        return SURF[code]
    faces = [code[i:i + 2] for i in range(0, 12, 2)]      # Top, Bottom, Front, Back, Left, Right
    if faces[0] == "St":
        return "studs"
    return "inlet" if "In" in faces else "smooth"


def load(sc, parent, rows):
    for r in rows:
        name, cls, sx, sy, sz, x, y, z, rx, ry, rz, col, mat, surf, shape, tr, cc = r
        color = tuple(int(col[i:i + 2], 16) for i in (0, 2, 4))
        if mat not in spslib.MATERIALS:
            mat = "Plastic"
        sc.part(parent, name, (sx, sy, sz), CF((x, y, z), orientation(rx, ry, rz)), color,
                shape="Wedge" if shape == "Wedge" else "Block", material=mat, transparency=tr, grid=False,
                surfaces=surfaces(surf))


def ground(coll, size, y=0.0, color=(120, 178, 92)):
    import spsgeo as G
    g = G.box(size, 0.2, size, (0, y - 0.1, 0))
    me = bpy.data.meshes.new("ground")
    me.from_pydata(SB.rb2bl(np.array(g.v)).tolist(), [], g.f)
    me.materials.append(SB.material(color, "SmoothPlastic", 0.0))
    coll.objects.link(bpy.data.objects.new("ground", me))


VIEWS = (("front", 0.0, 25.0), ("right", 90.0, 25.0), ("back", 180.0, 25.0), ("left", 270.0, 25.0),
         ("top", 20.0, 72.0))


def render_prop(rows, size, out_png, tile, samples):
    sc = spslib.Scene("FV")
    m = sc.model(sc.root, "Prop")
    load(sc, m, rows)
    scene = SB.reset()
    coll = bpy.data.collections.new("P")
    scene.collection.children.link(coll)
    SB.realize(sc, coll)
    ext = np.array(size, float)
    r = 0.5 * float(np.linalg.norm(ext)) + 0.3
    ground(coll, max(ext[0], ext[2]) * 3 + 20)
    rs.setup_world(scene, strength=0.75, key=3.2)
    rs.setup_render(scene, tile, tile, samples=samples, bloom=True)
    centre = np.array((0.0, ext[1] / 2, 0.0))
    lens = 50.0
    fov = 2 * math.atan(18.0 / lens)
    d = r / math.sin(fov / 2) * 1.02
    files = []
    for name, az, el in VIEWS:
        # the prop's front is -Z: 'front' looks at it from -Z
        a, e = math.radians(az), math.radians(el)
        dirv = np.array((math.sin(a) * math.cos(e), math.sin(e), -math.cos(a) * math.cos(e)))
        pos = centre + dirv * d
        cam = SB.camera(scene, tuple(pos), tuple(centre), lens=lens)
        scene.camera = cam
        p = out_png.replace(".png", "_%s.png" % name)
        rs.render(scene, p)
        files.append(p)
    return files


def main():
    src, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    opts = dict(a.split("=", 1) for a in sys.argv[3:] if "=" in a)
    tile = int(opts.get("tile", 224))
    samples = int(opts.get("samples", 10))
    data = json.load(open(src))["groups"]
    groups = opts.get("groups", ",".join(data)).split(",")
    font = ImageFont.truetype(FONT, 15)
    per_sheet = int(opts.get("per", 8))
    for g in groups:
        items = data[g]
        for s0 in range(0, len(items), per_sheet):
            chunk = items[s0:s0 + per_sheet]
            sheet = Image.new("RGB", (tile * len(VIEWS), tile * len(chunk)), (30, 30, 30))
            for row, it in enumerate(chunk):
                base = os.path.join(out, "_%s_%d.png" % (g, s0 + row))
                files = render_prop(it["parts"], it["size"], base, tile, samples)
                for col, f in enumerate(files):
                    im = Image.open(f).convert("RGB")
                    if col == 0:
                        d = ImageDraw.Draw(im)
                        d.text((6, 4), "%s %d: %s" % (g, s0 + row, it["kind"]), fill=(255, 255, 255), font=font,
                               stroke_width=2, stroke_fill=(0, 0, 0))
                        d.text((6, tile - 22), "%d parts  %.0fx%.0fx%.0f" % ((len(it["parts"]),) + tuple(it["size"])),
                               fill=(255, 255, 255), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
                    sheet.paste(im, (col * tile, row * tile))
                    os.remove(f)
            sp = os.path.join(out, "sheet_%s_%d.jpg" % (g, s0 // per_sheet))
            sheet.save(sp, quality=86)
            print("saved", sp, flush=True)


if __name__ == "__main__":
    main()
