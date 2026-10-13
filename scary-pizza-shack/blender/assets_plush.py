"""Batch 2, section D: seven plushies, about 1.3 tall, sitting, facing -Z.

Each is a Model whose PrimaryPart `Body` is anchored with its pivot on the underside
(so `plush:PivotTo(slot.CFrame)` sits it on a shelf slot); every other part is welded to
it. The Watchdog's and NightOwl's Head hangs on a Motor6D `Neck` (pivot at the neck), with
the eyes, ears and nose welded to the Head."""
import math

import numpy as np

import spsgeo as G
from assets_common import moving, pivot
from spsgeo import CF, T, RX, RY, RZ, S

PC = {
    "dog": (150, 100, 62), "dog_dark": (98, 64, 40), "dog_light": (226, 196, 156), "black": (24, 22, 24),
    "red": (196, 40, 32), "gold": (232, 184, 60), "cream": (242, 232, 210), "pink": (236, 150, 160),
    "suit": (50, 52, 58), "skin_grey": (198, 200, 194), "owl": (128, 112, 150), "owl_light": (190, 176, 206),
    "owl_eye": (246, 226, 140), "orange": (228, 140, 50), "bear": (190, 44, 40), "bear_light": (232, 170, 150),
    "white": (244, 244, 238), "sloth": (180, 150, 112), "sloth_light": (226, 206, 170), "sloth_dark": (92, 70, 52),
    "pig": (240, 160, 172), "pig_light": (250, 196, 204), "thread": (60, 50, 50),
    # Little Papa (the shack kit's names)
    "cheese": (246, 196, 72), "crust": (206, 140, 66), "pepperoni": (168, 40, 30), "red_light": (224, 92, 88),
    "grey_dark": (60, 60, 66),
}


def soft_box(w, h, d, r, c=(0, 0, 0)):
    """Box with every edge chamfered by r: the pillowy toy look, 44 triangles."""
    hw, hh, hd = w / 2, h / 2, d / 2
    idx = {}
    g = G.Geo()
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (-1, 1):
                for ax in range(3):
                    p = [sx * (hw - r), sy * (hh - r), sz * (hd - r)]
                    p[ax] = (sx, sy, sz)[ax] * (hw, hh, hd)[ax]
                    idx[(sx, sy, sz, ax)] = len(g.v)
                    g.v.append(tuple(p))
    faces = []
    for ax in range(3):
        u, v_ = [a for a in range(3) if a != ax]
        for s in (-1, 1):
            quad = []
            for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                key = [0, 0, 0]
                key[ax], key[u], key[v_] = s, a, b
                quad.append(idx[(key[0], key[1], key[2], ax)])
            faces.append(quad)
    for ax in range(3):                         # edges along axis `ax`
        u, v_ = [a for a in range(3) if a != ax]
        for su in (-1, 1):
            for sv in (-1, 1):
                quad = []
                for s, which in ((-1, u), (-1, v_), (1, v_), (1, u)):
                    key = [0, 0, 0]
                    key[ax], key[u], key[v_] = s, su, sv
                    quad.append(idx[(key[0], key[1], key[2], which)])
                faces.append(quad)
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (-1, 1):
                faces.append([idx[(sx, sy, sz, a)] for a in range(3)])
    vs = np.array(g.v)
    for f in faces:
        a, b, c_ = vs[f[0]], vs[f[1]], vs[f[2]]
        n = np.cross(b - a, c_ - a)
        if np.dot(n, vs[f].mean(0)) < 0:
            f = f[::-1]
        g.f.append(tuple(f))
    return g.xf(T(*c))


def button(r=0.09, c=(0, 0, 0)):
    """A button eye facing -Z."""
    return G.Geo().add([G.cyl(r, 0.05, 8, "z", c), G.cyl(r * 0.55, 0.03, 6, "z", (c[0], c[1], c[2] - 0.03))])


def stitches(path, step=0.09, size=0.035):
    """Short thread dashes along a polyline, standing slightly proud of a surface."""
    g = G.Geo()
    pts = [np.asarray(p, float) for p in path]
    for a, b in zip(pts, pts[1:]):
        L = np.linalg.norm(b - a)
        n = max(1, int(L / step))
        for k in range(n):
            if k % 2:
                continue
            p = a + (b - a) * (k + 0.5) / n
            g.add(G.box(size, size, size, p))
    return g


class Plush:
    def __init__(self, sc, parent, name, origin):
        self.sc, self.name, self.o = sc, name, origin
        self.m = sc.model(parent, name)
        self.body = None
        self.head = None

    def add(self, pname, geo, colr, to="body", material="Fabric", mesh_name=None, root=False):
        anchored = root
        mp = self.sc.mesh(self.m, pname, mesh_name or self.name + "__" + pname, geo, self.o, PC[colr],
                          material=material, anchored=anchored, collide=root, touch=root, query=root,
                          massless=not root, owner=self.name)
        if root:
            self.body = mp
            pivot(mp, self.o)
            self.m.p["primary"] = mp
        elif to == "head":
            self.sc.weld(self.head, mp, "Weld")
        else:
            self.sc.weld(self.body, mp, "Weld")
        return mp

    def head_part(self, geo, colr, neck):
        hd = self.sc.mesh(self.m, "Head", self.name + "__Head", geo, self.o, PC[colr], material="Fabric",
                          anchored=False, collide=False, touch=False, query=False, massless=True, owner=self.name)
        self.head = hd
        self.sc.motor(self.body, hd, "Neck", self.o * CF(neck), parent=self.body)
        pivot(hd, self.o * CF(neck))
        return hd


def watchdog(sc, parent, origin=CF()):
    p = Plush(sc, parent, "Watchdog", origin)
    body = soft_box(0.8, 0.72, 0.62, 0.16, (0, 0.36, 0.05))
    for sx in (-1, 1):
        body.add(soft_box(0.26, 0.24, 0.42, 0.08, (sx * 0.22, 0.12, -0.36)))      # paws forward
        body.add(soft_box(0.22, 0.42, 0.22, 0.07, (sx * 0.36, 0.42, -0.18)))      # front legs
    p.add("Body", body, "dog", root=True)
    p.add("Belly", soft_box(0.46, 0.4, 0.06, 0.03, (0, 0.38, -0.27)), "dog_light")
    p.add("Tail", G.tube([(0, 0.2, 0.34), (0.02, 0.3, 0.5), (0.0, 0.45, 0.58)], 0.06, 5), "dog_dark")
    p.add("Collar", G.Geo().add([soft_box(0.66, 0.1, 0.56, 0.04, (0, 0.73, -0.02))]), "red")
    p.add("Tag", G.cyl(0.06, 0.03, 8, "z", (0, 0.64, -0.32)), "gold", material="Metal")
    head = soft_box(0.66, 0.56, 0.58, 0.15, (0, 1.02, -0.04))
    p.head_part(head, "dog", (0, 0.76, 0.0))
    p.add("Muzzle", soft_box(0.36, 0.24, 0.24, 0.07, (0, 0.92, -0.38)), "dog_light", to="head")
    p.add("Nose", soft_box(0.14, 0.1, 0.08, 0.03, (0, 0.99, -0.5)), "black", to="head")
    eyes = G.Geo().add([button(0.07, (sx * 0.15, 1.1, -0.34)) for sx in (-1, 1)])
    p.add("Eyes", eyes, "black", to="head", material="SmoothPlastic")
    ears = G.Geo()
    for sx in (-1, 1):
        ears.add(soft_box(0.1, 0.52, 0.3, 0.04, (0, 0, 0)).xf(T(sx * 0.37, 1.02, -0.02) @ RZ(sx * 12)))
    p.add("Ears", ears, "dog_dark", to="head")
    p.add("Stitches", stitches([(0, 1.3, -0.3), (0, 1.3, 0.25)], 0.08), "thread", to="head")
    moving("Plushies.Watchdog", "Head", "on the Motor6D Neck (in the Body): shake it with Neck.Transform, e.g. "
                                        "CFrame.Angles(0, 0, math.rad(15)) back and forth; ears, eyes, muzzle "
                                        "and nose are welded to the Head")
    return p.m


def lucky_cat(sc, parent, origin=CF()):
    p = Plush(sc, parent, "LuckyCat", origin)
    body = soft_box(0.78, 0.7, 0.6, 0.16, (0, 0.35, 0.02))
    body.add(soft_box(0.66, 0.6, 0.56, 0.15, (0, 0.98, -0.02)))                   # head
    body.add(soft_box(0.24, 0.2, 0.36, 0.07, (-0.2, 0.1, -0.32)))
    body.add(soft_box(0.24, 0.2, 0.36, 0.07, (0.2, 0.1, -0.32)))
    body.add(soft_box(0.2, 0.36, 0.2, 0.07, (-0.36, 0.42, -0.14)))                # paw down
    body.add(soft_box(0.2, 0.46, 0.2, 0.07, (0, 0, 0)).xf(T(0.36, 0.86, -0.12) @ RZ(-12)))   # waving paw up
    for sx in (-1, 1):
        ear = G.Geo()
        ear.v = [(-0.13, 0, -0.07), (0.13, 0, -0.07), (0.13, 0, 0.07), (-0.13, 0, 0.07), (0.0, 0.22, 0.0)]
        ear.f = [(0, 1, 2, 3), (0, 4, 1), (1, 4, 2), (2, 4, 3), (3, 4, 0)]
        body.add(G.outward(ear).xf(T(sx * 0.2, 1.26, -0.02) @ RZ(-sx * 14)))
    p.add("Body", body, "cream", root=True)
    p.add("Collar", soft_box(0.62, 0.08, 0.5, 0.03, (0, 0.7, -0.02)), "red")
    p.add("Bell", G.sphere(0.07, 8, 4, c=(0, 0.62, -0.28)), "gold", material="Metal")
    inner = G.Geo()
    for sx in (-1, 1):
        inner.add(G.box(0.12, 0.12, 0.04, (sx * 0.2, 1.32, -0.08)).xf(T(sx * 0.2, 1.32, -0.08) @ RZ(-sx * 14) @ T(-sx * 0.2, -1.32, 0.08)))
    p.add("EarsInner", inner, "pink")
    p.add("Eyes", G.Geo().add([button(0.065, (sx * 0.15, 1.04, -0.31)) for sx in (-1, 1)]), "black",
          material="SmoothPlastic")
    p.add("Nose", soft_box(0.1, 0.07, 0.05, 0.02, (0, 0.92, -0.31)), "pink")
    wh = G.Geo()
    for sx in (-1, 1):
        for dy in (-0.03, 0.03):
            wh.add(G.box(0.24, 0.015, 0.015, (sx * 0.24, 0.9 + dy, -0.32)).xf(
                T(sx * 0.24, 0.9 + dy, -0.32) @ RZ(sx * dy * 120) @ T(-sx * 0.24, -0.9 - dy, 0.32)))
    p.add("Whiskers", wh, "thread")
    p.add("Stitches", stitches([(0, 0.62, -0.29), (0, 0.12, -0.29)], 0.08), "thread")
    return p.m


def little_inspector(sc, parent, origin=CF()):
    """Little Papa (the Model keeps the name LittleInspector): a stuffed toy of Papa Stud's mask,
    1.3 tall, sitting; the same toy as the one hidden in the shack (shack2.props_insides),
    turned to face -Z, with stitches round its slice of a face."""
    from shack2.props_insides import little_papa_geo
    p = Plush(sc, parent, "LittleInspector", origin)
    k = 1.3 / 1.7
    turn = S(k) @ RY(180)
    for pname, colr, g in little_papa_geo():
        p.add(pname, g.xf(turn), colr, root=pname == "Body",
              material="SmoothPlastic" if pname in ("Eyes", "Pupils") else "Fabric")
    z = 0.12 + 0.11 + 0.012
    edge = [(-0.4, 0.42), (-0.06, -0.3), (0.06, -0.3), (0.4, 0.42)]
    p.add("Stitches", stitches([(x, y + 0.86, z) for x, y in edge], 0.07, 0.03).xf(turn), "thread")
    return p.m


def night_owl(sc, parent, origin=CF()):
    p = Plush(sc, parent, "NightOwl", origin)
    body = G.lathe([(0.0, 0.0), (0.32, 0.02), (0.4, 0.22), (0.38, 0.52), (0.3, 0.7), (0.0, 0.74)], 10)
    body = G.outward(body).xf(S(1.0, 1.0, 0.85))
    p.add("Body", body, "owl", root=True)
    p.add("Belly", G.outward(G.lathe([(0.0, 0.08), (0.24, 0.12), (0.26, 0.4), (0.16, 0.6), (0.0, 0.62)], 8)).xf(
        T(0, 0.0, -0.18) @ S(1.0, 1.0, 0.4)), "owl_light")
    wings = G.Geo()
    for sx in (-1, 1):
        wings.add(soft_box(0.1, 0.48, 0.42, 0.05, (0, 0, 0)).xf(T(sx * 0.4, 0.38, 0.04) @ RZ(sx * 10)))
    p.add("Wings", wings, "owl")
    p.add("Feet", G.Geo().add([soft_box(0.16, 0.06, 0.16, 0.02, (sx * 0.14, 0.03, -0.24)) for sx in (-1, 1)]),
          "orange")
    head = soft_box(0.66, 0.5, 0.56, 0.16, (0, 0.98, 0.0))
    for sx in (-1, 1):
        tuft = G.Geo()
        tuft.v = [(-0.08, 0, -0.06), (0.08, 0, -0.06), (0.08, 0, 0.06), (-0.08, 0, 0.06), (sx * 0.06, 0.2, 0.0)]
        tuft.f = [(0, 1, 2, 3), (0, 4, 1), (1, 4, 2), (2, 4, 3), (3, 4, 0)]
        head.add(G.outward(tuft).xf(T(sx * 0.24, 1.2, 0.0)))
    p.head_part(head, "owl", (0, 0.72, 0.0))
    discs = G.Geo().add([G.cyl(0.15, 0.04, 12, "z", (sx * 0.15, 1.0, -0.29)) for sx in (-1, 1)])
    p.add("EyeDiscs", discs, "owl_eye", to="head")
    p.add("Eyes", G.Geo().add([button(0.075, (sx * 0.15, 1.0, -0.32)) for sx in (-1, 1)]), "black", to="head",
          material="SmoothPlastic")
    beak = G.Geo()
    beak.v = [(-0.06, 0.94, -0.28), (0.06, 0.94, -0.28), (0.0, 0.86, -0.28), (0.0, 0.9, -0.38)]
    beak.f = [(0, 1, 2), (0, 3, 1), (1, 3, 2), (2, 3, 0)]
    p.add("Beak", G.outward(beak), "orange", to="head")
    p.add("Stitches", stitches([(-0.3, 0.75, -0.24), (0.3, 0.75, -0.24)], 0.07), "thread", to="head")
    moving("Plushies.NightOwl", "Head", "on the Motor6D Neck (in the Body): turn it about Y with Neck.Transform "
                                       "(an owl can go well past 90 deg); eyes, beak and tufts turn with it")
    return p.m


def medic_bear(sc, parent, origin=CF()):
    p = Plush(sc, parent, "MedicBear", origin)
    body = soft_box(0.76, 0.7, 0.6, 0.17, (0, 0.35, 0.03))
    body.add(soft_box(0.62, 0.56, 0.54, 0.16, (0, 0.98, 0.0)))
    for sx in (-1, 1):
        body.add(soft_box(0.26, 0.22, 0.4, 0.08, (sx * 0.2, 0.11, -0.34)))
        body.add(soft_box(0.2, 0.4, 0.2, 0.07, (0, 0, 0)).xf(T(sx * 0.42, 0.42, -0.12) @ RZ(sx * 18)))
        body.add(G.cyl(0.12, 0.08, 10, "z", (sx * 0.24, 1.28, 0.0)))
    p.add("Body", body, "bear", root=True)
    p.add("Muzzle", soft_box(0.26, 0.18, 0.12, 0.05, (0, 0.9, -0.3)), "bear_light")
    p.add("Nose", soft_box(0.1, 0.07, 0.05, 0.02, (0, 0.95, -0.37)), "black")
    p.add("Eyes", G.Geo().add([button(0.06, (sx * 0.14, 1.06, -0.28)) for sx in (-1, 1)]), "black",
          material="SmoothPlastic")
    p.add("EarsInner", G.Geo().add([G.cyl(0.07, 0.04, 8, "z", (sx * 0.24, 1.28, -0.05)) for sx in (-1, 1)]),
          "bear_light")
    a, b = 0.06, 0.17
    cross = G.extrude([(-a, b), (a, b), (a, a), (b, a), (b, -a), (a, -a), (a, -b), (-a, -b), (-a, -a), (-b, -a),
                       (-b, a), (-a, a)], 0.04, "z", (0, 0.38, -0.27))
    p.add("Cross", cross, "white")
    p.add("Stitches", stitches([(-0.2, 0.18, -0.27), (-0.2, 0.58, -0.27), (0.2, 0.58, -0.27), (0.2, 0.18, -0.27),
                                (-0.2, 0.18, -0.27)], 0.06, 0.03), "thread")
    return p.m


def sleepy_sloth(sc, parent, origin=CF()):
    p = Plush(sc, parent, "SleepySloth", origin)
    body = soft_box(0.74, 0.66, 0.56, 0.17, (0, 0.33, 0.04))
    body.add(soft_box(0.58, 0.5, 0.5, 0.17, (0, 0.92, 0.0)))
    for sx in (-1, 1):
        body.add(soft_box(0.24, 0.2, 0.42, 0.08, (sx * 0.2, 0.1, -0.32)))
        arm = soft_box(0.16, 0.62, 0.18, 0.06, (0, -0.31, 0))
        body.add(arm.xf(T(sx * 0.4, 0.66, -0.1) @ RZ(-sx * 38) @ RX(30)))      # arms hugging the tummy
    p.add("Body", body, "sloth", root=True)
    p.add("Face", soft_box(0.42, 0.3, 0.06, 0.03, (0, 0.92, -0.25)), "sloth_light")
    stripes = G.Geo()
    for sx in (-1, 1):
        stripes.add(G.box(0.16, 0.07, 0.03, (0, 0, 0)).xf(T(sx * 0.12, 0.95, -0.285) @ RZ(sx * 18)))
    p.add("EyeStripes", stripes, "sloth_dark")
    shut = G.Geo()
    for sx in (-1, 1):
        shut.add(G.tube([(sx * 0.17, 0.97, -0.295), (sx * 0.12, 0.945, -0.3), (sx * 0.07, 0.97, -0.295)], 0.012, 4))
    p.add("Eyes", shut, "black")
    p.add("Nose", soft_box(0.08, 0.06, 0.04, 0.02, (0, 0.88, -0.29)), "sloth_dark")
    claws = G.Geo()
    for sx in (-1, 1):
        for k in range(3):
            claws.add(G.box(0.03, 0.03, 0.1, (sx * (0.06 + 0.04 * k), 0.36 - 0.02 * k, -0.36)))
    p.add("Claws", claws, "sloth_dark")
    p.add("Stitches", stitches([(0, 0.62, -0.25), (0, 0.15, -0.25)], 0.07), "thread")
    return p.m


def piggy_bank(sc, parent, origin=CF()):
    p = Plush(sc, parent, "PiggyBank", origin)
    body = soft_box(0.86, 0.84, 1.0, 0.24, (0, 0.66, 0.04))
    for sx in (-1, 1):
        for sz in (-1, 1):
            body.add(soft_box(0.22, 0.3, 0.22, 0.07, (sx * 0.24, 0.15, 0.04 + sz * 0.3)))
        ear = G.Geo()
        ear.v = [(-0.12, 0, -0.05), (0.12, 0, -0.05), (0.12, 0, 0.05), (-0.12, 0, 0.05), (sx * 0.05, 0.22, -0.05)]
        ear.f = [(0, 1, 2, 3), (0, 4, 1), (1, 4, 2), (2, 4, 3), (3, 4, 0)]
        body.add(G.outward(ear).xf(T(sx * 0.24, 1.07, -0.3)))
    p.add("Body", body, "pig", root=True)
    p.add("Snout", G.cyl(0.15, 0.14, 10, "z", (0, 0.64, -0.5)), "pig_light")
    p.add("Nostrils", G.Geo().add([G.cyl(0.035, 0.03, 6, "z", (sx * 0.06, 0.64, -0.575)) for sx in (-1, 1)]),
          "thread")
    p.add("Eyes", G.Geo().add([button(0.065, (sx * 0.19, 0.82, -0.46)) for sx in (-1, 1)]), "black",
          material="SmoothPlastic")
    p.add("Slot", G.box(0.07, 0.05, 0.36, (0, 1.08, 0.08)), "black")
    p.add("Tail", G.tube([(0, 0.66, 0.54), (0.07, 0.73, 0.6), (0.0, 0.8, 0.63), (-0.06, 0.73, 0.64)], 0.035, 5),
          "pig_light")
    p.add("Stitches", stitches([(0, 1.08, -0.36), (0, 1.08, -0.1)], 0.06), "thread")
    return p.m


PLUSHIES = [watchdog, lucky_cat, little_inspector, night_owl, medic_bear, sleepy_sloth, piggy_bank]


def plushies(sc, parent, origin=CF(), spacing=2.0):
    m = sc.model(parent, "Plushies")
    for k, fn in enumerate(PLUSHIES):
        fn(sc, m, origin * CF((k * spacing, 0, 0)))
    return m
