"""The road dressed, and the things far away: reflector posts along both edges, the guard
rail over the ditch, the telegraph poles with their sagging wires (the transformer on the
one that feeds the shack), the speed, deer and PAPA STUD'S signs, two more street lamps,
the double-sided billboard with the mascot (a little too happy) looking back at the shack,
and two lights on the far hills under the moon: a radio mast and a single window."""
import math

import numpy as np

import spsgeo as G
from spsgeo import CF

from . import layout as L, outkit as O, terrain as TR
from .kit import bevel_box, ccyl, cfrustum, chamfer_slab, rod
from .st_common import board


def face_slab(pts, h, b=0.08):
    return chamfer_slab([(x, -y) for (x, y) in pts], h, b).xf(G.M(G.rx(90))).xf(G.T(0, 0, -h / 2))


def facing(dx, dz):
    """Rotation whose Front (-Z) looks along (dx, dz): for Boards and signs."""
    d = np.array((dx, 0.0, dz), float)
    return G.facing(d / np.linalg.norm(d))


def off_road(x, z, dist):
    """(x, z) pushed straight away from the road's centre line to `dist` from it."""
    P = L._road_pts()
    i = int(np.argmin((P[:, 0] - x) ** 2 + (P[:, 1] - z) ** 2))
    c = P[i]
    d = np.array((x - c[0], z - c[1]))
    n = np.linalg.norm(d)
    if n < 1e-6:
        return x, z
    q = c + d / n * dist
    return float(q[0]), float(q[1])


def _arc_points(pts, step):
    """Points every `step` along a polyline, with the unit direction there."""
    P = np.asarray(pts, float)
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
    s = np.concatenate(([0.0], np.cumsum(seg)))
    out = []
    t = step / 2
    while t < s[-1]:
        i = min(np.searchsorted(s, t) - 1, len(seg) - 1)
        i = max(i, 0)
        u = (t - s[i]) / max(seg[i], 1e-9)
        p = P[i] + (P[i + 1] - P[i]) * u
        d = (P[i + 1] - P[i]) / max(seg[i], 1e-9)
        out.append((p, d))
        t += step
    return out


# ---------------------------------------------------------------- along the road

def reflector_posts(k, f, gr):
    """White posts with an orange reflector on each face, every 18 along both edges."""
    m = k.sc.model(f, "ReflectorPosts")
    post = bevel_box(0.4, 3.2, 0.4, 0.06, c=(0, 1.5, 0))
    refl = G.Geo()
    for sd in (-1, 1):
        refl.add(bevel_box(0.3, 0.6, 0.15, 0.03, c=(0, 2.6, sd * 0.24)))
    cl = TR.centre_line()
    n = 0
    for off in (-12.2, 12.2):
        for (p, d) in _arc_points(TR.offset_line(cl, off), 18.0):
            x, z = float(p[0]), float(p[1])
            if off < 0 and L.FORECOURT[0] - 3 < x < L.BUS_STOP_X[1] + 4 and z > 15:
                continue                                   # the forecourt and the lot open onto the road here
            if off > 0 and -56 < x < 62 and z > 40:
                continue                                   # the guard rail carries its own reflectors there
            if math.hypot(x, z) > L.GROUND_R - 6:
                continue
            y = gr.y(x, z)
            yaw = math.degrees(math.atan2(d[0], d[1]))
            cf = CF((x, y, z), G.ry(yaw))
            pm = k.sc.model(m, "ReflectorPost")
            k.mesh(pm, "Post", "Road__ReflectorPost", post, cf, "sign_white", shadow=False)
            k.mesh(pm, "Reflectors", "Road__Reflectors", refl, cf, "reflector", shadow=False)
            n += 1
    k.mark_used("ReflectorPost", "outside")
    return n


def guard_rail(k, f, gr):
    """A W-beam rail on posts along the south edge over the ditch (a gap for the farm track)."""
    m = k.sc.model(f, "GuardRail")
    z = L.ROAD_Z + 12.6
    prof = [(0.0, -0.45), (0.25, -0.25), (0.05, 0.0), (0.25, 0.25), (0.0, 0.45), (-0.15, 0.45), (-0.15, -0.45)]
    for (x0, x1) in ((-52.0, L.CULVERT_X - 4.0), (L.CULVERT_X + 4.0, 58.0)):
        g = G.Geo()
        ln = x1 - x0
        beam = G.extrude(prof, ln, "z", (0, 0, 0))
        beam = beam.xf(G.M(G.ry(90)))
        y = gr.y((x0 + x1) / 2, z)
        g.add(beam.xf(G.T((x0 + x1) / 2, y + 2.0, z - 0.35)))
        for x in np.arange(x0 + 0.5, x1, 4.0):
            g.add(bevel_box(0.3, 2.4, 0.3, 0.05, c=(x, gr.y(x, z) + 1.0, z)))
            g.add(bevel_box(0.3, 0.5, 0.5, 0.04, c=(x, y + 2.0, z - 0.2)))
        for end in (x0, x1):                                  # turned-down ends
            g.add(bevel_box(1.2, 0.8, 0.3, 0.06, c=(end, y + 1.2, z - 0.3)).xf(G.T(0, 0, 0)))
        k.mesh(m, "Rail", "Road__Rail%d" % int(x0), g, CF(), "rail", shadow=True)
        k.part(m, "Blocker", (int(round(ln)), 2.4, 1), CF(((x0 + x1) / 2, y + 1.2, z)), "rail", transparency=1.0,
               solid=True, grid=False, shadow=False)
    k.mark_used("GuardRail", "outside")


def telegraph(k, f, gr):
    """Creosoted poles along the meadow edge: crossarm, three insulators, the step bolts,
    three wires sagging between them; the transformer can on the pole that feeds the shack."""
    m = k.sc.model(f, "TelegraphPoles")
    xs = tuple(L.POLE_X)
    tops = []
    for i, x in enumerate(xs):
        z = L.POLE_Z
        y0 = gr.y(x, z)
        pm = k.sc.model(m, "Pole%d" % (i + 1))
        k.mesh(pm, "Pole", "Tele__Pole", O.flat_pole(L.POLE_H + 1.0, 0.5, 0.36, 10), CF((x, y0 - 1.0, z)), "pole_wood",
               solid=True)
        arm = G.Geo()
        arm.add(bevel_box(0.4, 0.5, 5.2, 0.06, c=(0, 0, 0)))
        for dz in (-1.9, 1.9):
            arm.add(rod((0, -0.25, dz * 0.3), (0, -1.6, dz * 0.05), 0.08, 4))          # braces
        k.mesh(pm, "CrossArm", "Tele__Arm", arm, CF((x, y0 + L.POLE_H - 1.4, z)), "pole_wood_dark", shadow=False)
        ins = G.Geo()
        for dz in (-2.0, 0.0, 2.0):
            ins.add(_insulator().xf(G.T(0, 0.25, dz)))
        k.mesh(pm, "Insulators", "Tele__Insulators", ins, CF((x, y0 + L.POLE_H - 1.4, z)), "insulator", shadow=False)
        bolts = G.Geo()
        for j in range(8):
            yy = 7.0 + 1.6 * j
            a = 90.0 * (j % 2)
            bolts.add(rod((0, yy, 0), (0, yy, 0.8), 0.08, 4).xf(G.M(G.ry(a))))
        k.mesh(pm, "StepBolts", "Tele__Bolts", bolts, CF((x, y0, z)), "steel_dark", shadow=False)
        if x == L.POLE_X[3]:
            tf = G.Geo()
            tf.add(ccyl(0.9, 2.4, 10, "y", (0, 0, 0), 0.1))
            tf.add(ccyl(1.0, 0.3, 10, "y", (0, 1.3, 0), 0.06))
            tf.add(bevel_box(0.4, 1.6, 0.6, 0.06, c=(0, 0, 1.0)))
            k.mesh(pm, "Transformer", "Tele__Transformer", tf, CF((x, y0 + L.POLE_H - 6.0, z - 1.4)), "grey",
                   shadow=False)
        tops.append(np.array((x, y0 + L.POLE_H - 0.85, z)))
    wires = G.Geo()
    for a, b in zip(tops, tops[1:]):
        for dz in (-2.0, 0.0, 2.0):
            wires.add(O.catenary(a + (0, 0, dz), b + (0, 0, dz), 1.6 + 0.2 * abs(dz), 0.075, 16))
    k.mesh(m, "Wires", "Tele__Wires", wires, CF(), "black", shadow=False)
    k.mark_used("TelegraphPole", "outside")


def _insulator():
    return G.outward(G.lathe([(0.0, 0.0), (0.18, 0.0), (0.28, 0.15), (0.2, 0.3), (0.26, 0.45), (0.12, 0.6),
                              (0.0, 0.62)], 8))


def road_signs(k, f, gr):
    m = k.sc.model(f, "RoadSigns")
    rs = {}
    for name, s in L.ROAD_SIGNS.items():                  # just off the shoulder, on the verge
        x, z = off_road(s["x"], s["z"], 15.4 if name != "PapaSign" else 17.9)
        rs[name] = dict(s, x=x, z=z)
    # speed limit
    s = rs["SpeedSign"]
    sm = k.sc.model(m, "SpeedSign")
    y0 = gr.y(s["x"], s["z"])
    R = facing(*s["face"])
    k.mesh(sm, "Post", "Sign__Post", O.flat_pole(7.4, 0.16, 0.14, 8), CF((s["x"], y0 - 0.4, s["z"])), "galv",
           solid=True)
    k.mesh(sm, "Plate", "Sign__SpeedPlate", bevel_box(2.6, 3.2, 0.15, 0.08), CF((s["x"], y0 + 5.4, s["z"]), R) *
           CF((0, 0, -0.25)), "sign_white", shadow=False)
    board(k, sm, (2.2, 2.8, 0.15), CF((s["x"], y0 + 5.4, s["z"]), R) * CF((0, 0, -0.4)), "sign_white",
          text="SPEED\nLIMIT\n45", text_color=(20, 20, 20))
    # deer crossing: a yellow diamond with a deer on it
    s = rs["DeerSign"]
    dm = k.sc.model(m, "DeerSign")
    y0 = gr.y(s["x"], s["z"])
    R = facing(*s["face"])
    k.mesh(dm, "Post", "Sign__Post", O.flat_pole(7.4, 0.16, 0.14, 8), CF((s["x"], y0 - 0.4, s["z"])), "galv",
           solid=True)
    dia = G.Geo()
    dia.add(bevel_box(2.8, 2.8, 0.15, 0.08).xf(G.M(G.rz(45))))
    k.mesh(dm, "Plate", "Sign__Diamond", dia, CF((s["x"], y0 + 5.4, s["z"]), R) * CF((0, 0, -0.25)), "sign_yellow",
           shadow=False)
    k.mesh(dm, "Rim", "Sign__DiamondRim", _diamond_rim(), CF((s["x"], y0 + 5.4, s["z"]), R) * CF((0, 0, -0.35)),
           "black", shadow=False)
    k.mesh(dm, "Deer", "Sign__Deer", _deer(), CF((s["x"], y0 + 5.4, s["z"]), R) * CF((0, -0.2, -0.38), G.ry(180)),
           "black", shadow=False)
    # PAPA STUD'S PIZZA OPEN LATE, with an arrow, on two timber posts
    s = rs["PapaSign"]
    pm = k.sc.model(m, "PapaSign")
    y0 = gr.y(s["x"], s["z"])
    R = facing(*s["face"])
    base = CF((s["x"], y0, s["z"]), R)
    for dx in (-3.6, 3.6):
        k.mesh(pm, "Post", "Sign__PapaPost", bevel_box(0.6, 9.0, 0.6, 0.08), base * CF((dx, 4.1, 0.4)), "pole_wood",
               solid=True)
    k.mesh(pm, "Back", "Sign__PapaBack", bevel_box(9.6, 4.6, 0.4, 0.1), base * CF((0, 6.6, 0.0)), "red", solid=True)
    board(k, pm, (9.0, 2.9, 0.15), base * CF((0, 7.2, -0.28)), "cream", text="PAPA STUD'S PIZZA\nOPEN LATE",
          text_color=(170, 32, 26))
    arrow = face_slab([(-3.4, 0.0), (-2.2, 0.75), (-2.2, 0.35), (3.0, 0.35), (3.0, -0.35), (-2.2, -0.35), (-2.2, -0.75)],
                      0.3, 0.06)
    k.mesh(pm, "Arrow", "Sign__PapaArrow", arrow.xf(G.M(G.ry(180))), base * CF((0.0, 5.05, -0.3)), "mustard",
           shadow=False)
    lm = k.sc.model(pm, "Lamp")
    k.mesh(lm, "ArmPipe", "Sign__PapaLampArm", G.tube([(0, 0, 0), (0, 0.8, -1.2), (0, 0.6, -1.9)], 0.1, 6),
           base * CF((0, 9.0, 0.0)), "charcoal", shadow=False)
    bulb = k.part(lm, "Bulb", (0.5, 0.5, 0.5), base * CF((0, 9.3, -1.95)), (255, 226, 170), material="Neon",
                  shape="Ball", grid=False, shadow=False)
    k.lamp(lm, bulb, "Street", "Spot", 16.0, 1.4, (255, 206, 150), angle=80.0, flicker=0.2)
    k.mark_used("SpeedSign", "outside")
    k.mark_used("DeerSign", "outside")
    k.mark_used("PapaSign", "outside")


def _diamond_rim():
    g = G.Geo()
    for a in range(4):
        g.add(bevel_box(2.9, 0.2, 0.15, 0.04, c=(0, 1.45, 0)).xf(G.M(G.rz(45 + 90 * a))))
    return g


def _deer():
    """A leaping deer, in blocks: body, neck, head, four legs, antlers."""
    g = G.Geo()
    g.add(bevel_box(1.1, 0.42, 0.15, 0.06, c=(0, 0, 0)).xf(G.M(G.rz(12))))
    g.add(bevel_box(0.25, 0.6, 0.15, 0.05, c=(0.55, 0.38, 0)).xf(G.M(G.rz(-25))))
    g.add(bevel_box(0.4, 0.22, 0.15, 0.05, c=(0.72, 0.68, 0)))
    for (x0, y0, x1, y1) in ((0.35, -0.15, 0.75, -0.6), (0.25, -0.15, 0.45, -0.65), (-0.35, -0.2, -0.75, -0.6),
                             (-0.45, -0.2, -0.95, -0.4)):
        g.add(G.tube([(x0, y0, 0), (x1, y1, 0)], 0.08, 4))
    for (x1, y1) in ((0.55, 1.05), (0.85, 1.05)):
        g.add(G.tube([(0.7, 0.75, 0), (x1, y1, 0)], 0.075, 4))
    return g


def road_lamps(k, f, gr):
    """Two more street lamps on the north verge: pools of light with dark between them."""
    m = k.sc.model(f, "RoadLamps")
    for i, (x, z) in enumerate((off_road(-46.0, 21.6, 13.6), off_road(68.0, 18.4, 13.6))):
        lm = k.sc.model(m, "RoadLamp%d" % (i + 1))
        y0 = gr.y(x, z)
        k.mesh(lm, "Base", "RoadLamp__Base", ccyl(0.7, 0.8, 10, "y", (0, 0.2, 0), 0.08), CF((x, y0, z)), "concrete",
               solid=True)
        k.mesh(lm, "Pole", "RoadLamp__Pole", O.flat_pole(11.0, 0.3, 0.2, 10), CF((x, y0 + 0.6, z)), "galv", solid=True)
        arm = G.tube([(0, 11.2, 0), (0, 12.0, 0.6), (0, 12.2, 1.6), (0, 12.05, 2.6), (0, 11.9, 3.0)], 0.15, 8)
        k.mesh(lm, "ArmPipe", "RoadLamp__Arm", arm, CF((x, y0, z)), "galv", shadow=False)
        hd = G.outward(G.lathe([(0.0, -0.35), (0.55, -0.3), (0.7, 0.0), (0.5, 0.3), (0.0, 0.35)], 10, sz=1.6))
        k.mesh(lm, "Head", "RoadLamp__Head", hd, CF((x, y0 + 11.75, z + 3.6)), "galv_dark")
        bulb = k.part(lm, "Bulb", (1.0, 0.4, 1.6), CF((x, y0 + 11.35, z + 3.6)), "sodium", material="Neon",
                      grid=False, shadow=False)
        k.lamp(lm, bulb, "Street", "Spot", 44.0, 2.2, (255, 184, 110), angle=125.0, flicker=0.12 if i else 0.0)
        k.sc.attachment(bulb, "Fx_Moths", CF((x, y0 + 10.8, z + 3.6)))
    k.prop(m, "MileMarker", CF((-70.0, gr.y(-70.0, 47.0), 47.0), G.ry(180)), where="outside", name="MileMarker")
    k.prop(m, "Mailbox", CF((L.CULVERT_X + 4.2, gr.y(L.CULVERT_X + 4.2, 58.5), 58.5), G.ry(180)), where="outside",
           name="Mailbox")
    for (x, z, s) in ((18.0, 26.4, 1), (19.6, 26.9, 2)):
        cf = CF((x, L.ROAD_TOP + 0.5, z), G.rz(85)) if s == 2 else CF((x, L.ROAD_TOP, z))
        k.prop(m, "Cone", cf, where="outside", name="Cone", seed=s)


# ---------------------------------------------------------------- billboard

def billboard(k, f, gr):
    """The double-sided billboard at the west end of the straight: steel legs, a catwalk,
    two lamps. The face towards the shack: the mascot, grinning a little too wide, and the
    shack's name; the other face: a faded motel advert for the cars coming round the bend."""
    b = L.BILLBOARD
    m = k.sc.model(f, "Billboard")
    y0 = gr.y(b["x"], b["z"])
    R = facing(*b["face"])                               # its Front looks at the shack
    base = CF((b["x"], y0, b["z"]), R)
    w, h, yb = 16.0, 7.0, 10.0
    for dx in (-(w / 2 + 0.75), w / 2 + 0.75):               # the legs run up the frame's two ends
        leg = G.Geo()
        leg.add(bevel_box(0.8, yb + h, 0.2, 0.04, c=(0, (yb + h) / 2, -0.35)))
        leg.add(bevel_box(0.8, yb + h, 0.2, 0.04, c=(0, (yb + h) / 2, 0.35)))
        leg.add(bevel_box(0.2, yb + h, 0.6, 0.04, c=(0, (yb + h) / 2, 0)))
        k.mesh(m, "Leg", "Billboard__Leg", leg, base * CF((dx, -0.5, 0.5)), "galv_dark", solid=True)
        k.mesh(m, "Strut", "Billboard__Strut", rod((0, 0, 4.2), (0, yb - 1.0, 0.85), 0.18, 6), base * CF((dx, 0, 0)),
               "galv_dark", shadow=False)
    k.mesh(m, "Frame", "Billboard__Frame", bevel_box(w + 0.6, h + 0.6, 1.0, 0.12), base * CF((0, yb + h / 2, 0.5)),
           "charcoal", solid=True)
    # the face towards the shack: red and cream, the mascot on the left, the name on the right
    k.mesh(m, "AdBack", "Billboard__AdBack", bevel_box(w, h, 0.15, 0.04), base * CF((0, yb + h / 2, -0.05)), "cream",
           shadow=False)
    k.mesh(m, "AdStripe", "Billboard__Stripe", bevel_box(w, 1.2, 0.2, 0.04), base * CF((0, yb + 0.8, -0.12)), "red",
           shadow=False)
    board(k, m, (9.0, 3.6, 0.15), base * CF((3.0, yb + 4.2, -0.2)), "cream",
          text="PAPA STUD'S\nPIZZA\nHOT! OPEN LATE!", text_color=(170, 32, 26), name="Board")
    board(k, m, (8.0, 0.9, 0.15), base * CF((3.0, yb + 0.8, -0.27)), "red", text="1/2 MILE AHEAD",
          text_color=(250, 236, 200), name="Distance")
    mascot = k.sc.model(m, "Mascot")
    mb = base * CF((-4.4, yb + 0.6, -0.35))
    k.mesh(mascot, "Slice", "Billboard__Slice", face_slab([(0.0, 0.0), (2.9, 6.0), (-2.9, 6.0)], 0.4, 0.1)
           .xf(G.M(G.ry(180))), mb, "cheese", shadow=False)
    k.mesh(mascot, "Crust", "Billboard__Crust", bevel_box(6.4, 1.0, 0.6, 0.25), mb * CF((0, 6.2, 0.1)), "dough",
           shadow=False)
    face = G.Geo()
    for dx in (-0.9, 0.9):
        face.add(ccyl(0.62, 0.15, 12, "z", (dx, 4.3, 0), 0.05))
    k.mesh(mascot, "Eyes", "Billboard__Eyes", face, mb * CF((0, 0, -0.3)), "paper", shadow=False)
    pupils = G.Geo()
    for dx in (-0.85, 0.95):
        pupils.add(ccyl(0.16, 0.15, 8, "z", (dx, 4.2, 0), 0.03))
    k.mesh(mascot, "Pupils", "Billboard__Pupils", pupils, mb * CF((0, 0, -0.42)), "black", shadow=False)
    grin = G.Geo()
    pts = []
    for i in range(13):
        a = math.radians(200 + 140 * i / 12)
        pts.append((1.9 * math.cos(a), 3.05 + 1.3 * math.sin(a) * 0.55))
    for i in range(12, -1, -1):
        a = math.radians(200 + 140 * i / 12)
        pts.append((1.6 * math.cos(a), 3.05 + 1.3 * math.sin(a) * 0.3))
    grin.add(face_slab(pts, 0.15, 0.03))
    k.mesh(mascot, "Grin", "Billboard__Grin", grin.xf(G.M(G.ry(180))), mb * CF((0, 0, -0.32)), "black", shadow=False)
    cheeks = G.Geo()
    for dx in (-1.7, 1.7):
        cheeks.add(ccyl(0.4, 0.15, 10, "z", (dx, 3.4, 0), 0.04))
    k.mesh(mascot, "Cheeks", "Billboard__Cheeks", cheeks, mb * CF((0, 0, -0.3)), "red_light", shadow=False)
    pep = G.Geo()
    for (px, py) in ((-1.4, 5.4), (1.5, 5.3), (0.0, 1.6)):
        pep.add(ccyl(0.45, 0.15, 10, "z", (px, py, 0), 0.04))
    k.mesh(mascot, "Pepperoni", "Billboard__Pepperoni", pep, mb * CF((0, 0, -0.3)), "sauce", shadow=False)
    # the other face: a faded motel advert
    k.mesh(m, "BackFace", "Billboard__BackFace", bevel_box(w, h, 0.15, 0.04), base * CF((0, yb + h / 2, 1.05)),
           "label_blue", shadow=False)
    board(k, m, (14.0, 5.6, 0.15), base * CF((0, yb + h / 2, 1.2), G.ry(180)), "label_blue",
          text="SLEEPY PINES MOTEL\nVACANCY\n3 MILES", text_color=(236, 226, 200), name="BackBoard")
    # catwalk and two lamps lighting the shack face
    cw = G.Geo()
    cw.add(bevel_box(w, 0.2, 1.6, 0.04, c=(0, 0, -0.8)))
    for dx in np.arange(-w / 2 + 0.2, w / 2, 2.0):
        cw.add(rod((dx, 0, -1.55), (dx, 1.6, -1.55), 0.075, 4))
    cw.add(rod((-w / 2 + 0.2, 1.6, -1.55), (w / 2 - 0.2, 1.6, -1.55), 0.08, 4))
    k.mesh(m, "Catwalk", "Billboard__Catwalk", cw, base * CF((0, yb - 0.4, 0)), "galv_dark", shadow=False)
    for i, dx in enumerate((-4.0, 4.0)):
        lm = k.sc.model(m, "Spot%d" % (i + 1))
        k.mesh(lm, "ArmPipe", "Billboard__LampArm", G.tube([(0, 0, -1.4), (0, 0.6, -2.6), (0, 0.5, -3.3)], 0.12, 6),
               base * CF((dx, yb - 0.3, 0)), "galv_dark", shadow=False)
        hood = G.outward(G.lathe([(0.0, -0.3), (0.5, -0.25), (0.6, 0.25), (0.0, 0.3)], 8))
        k.mesh(lm, "Hood", "Billboard__LampHood", hood.xf(G.M(G.rx(55))), base * CF((dx, yb + 0.5, -3.4)), "charcoal",
               shadow=False)
        bulb = k.part(lm, "Bulb", (0.5, 0.5, 0.5), base * CF((dx, yb + 0.6, -3.2)), (255, 232, 190), material="Neon",
                      shape="Ball", grid=False, shadow=False)
        k.lamp(lm, bulb, "Street", "Spot", 20.0, 1.8, (255, 214, 160), angle=80.0, face="Top", shadows=False,
               flicker=0.3 if i else 0.0)
    k.mark_used("Billboard", "outside")


# ---------------------------------------------------------------- far away, under the moon

def _mound(rng, r, h, steps=4):
    from .forest import hill_geo
    return hill_geo(rng, r, h, steps)


def far_lights(k, f, gr):
    """A radio mast with its red light on a ridge, and a single lit window in a house on a
    hill, both inside the moon's wedge so the serving window sees them."""
    rng = np.random.default_rng(88)
    m = k.sc.model(f, "FarLights")
    mx, mz = L.MAST
    hh = 34.0
    k.mesh(m, "Ridge", "Far__MastRidge", _mound(rng, 46.0, hh, 4), CF((mx, 0.0, mz)), "hill2", shadow=False)
    mast = G.Geo()
    H = L.MAST_H
    legs = [(math.cos(a), math.sin(a)) for a in (0.0, 2.094, 4.189)]
    for i in range(3):
        a0, a1 = legs[i], legs[(i + 1) % 3]
        mast.add(rod((2.0 * a0[0], 0, 2.0 * a0[1]), (0.6 * a0[0], H, 0.6 * a0[1]), 0.3, 4))
        for j in range(12):
            t0, t1 = j / 12, (j + 1) / 12
            r0, r1 = 2.0 - 1.4 * t0, 2.0 - 1.4 * t1
            mast.add(rod((r0 * a0[0], H * t0, r0 * a0[1]), (r1 * a1[0], H * t1, r1 * a1[1]), 0.2, 4))
    k.mesh(m, "Mast", "Far__Mast", mast, CF((mx, hh - 0.5, mz)), "grey_dark", shadow=False)
    for i, yy in enumerate((H + 0.3,)):
        lm = k.sc.model(m, "MastLight%d" % (i + 1))
        off = 0.0
        b = k.part(lm, "Bulb", (1.6, 1.6, 1.6), CF((mx + off, hh + yy, mz)), (255, 40, 30), material="Neon", shape="Ball",
                   grid=False, shadow=False)
        k.lamp(lm, b, "Always", "Point", 24.0, 2.0, (255, 50, 40), shadows=False, flicker=0.0)
        k.attr(b, "Flicker", 0.5)
    # the house on the hill with one lit window
    hx, hz = L.HILL_WINDOW
    hy = 26.0
    k.mesh(m, "Hill", "Far__HouseHill", _mound(rng, 40.0, hy, 4), CF((hx, 0.0, hz)), "hill", shadow=False)
    hm = k.sc.model(m, "HillHouse")
    house = G.Geo()
    house.add(bevel_box(9.0, 6.0, 7.0, 0.2, c=(0, 3.0, 0)))
    house.add(G.extrude([(-5.0, 0.0), (5.0, 0.0), (0.0, 3.4)], 7.6, "z", (0, 6.0, 0)))
    house.add(bevel_box(1.2, 3.0, 1.2, 0.1, c=(2.6, 8.5, 1.0)))
    k.mesh(hm, "House", "Far__House", house, CF((hx, hy - 0.2, hz), G.ry(15)), "far_trees", shadow=False)
    win = k.part(hm, "Bulb", (1.6, 1.4, 0.4), CF((hx, hy + 3.4, hz), G.ry(15)) * CF((-1.8, 0, -3.55)),
                 (255, 200, 120), material="Neon", grid=False, shadow=False)
    k.lamp(hm, win, "Always", "Point", 10.0, 0.8, (255, 196, 132), shadows=False)
    k.mark_used("RadioMast", "outside")
    k.mark_used("HillHouse", "outside")


def build(k, sc):
    gr = sc.kit_ground
    f = sc.folder(sc.root.get("Outside"), "RoadDressing")
    reflector_posts(k, f, gr)
    guard_rail(k, f, gr)
    telegraph(k, f, gr)
    road_signs(k, f, gr)
    road_lamps(k, f, gr)
    billboard(k, f, gr)
    far_lights(k, f, gr)
    return f
