"""Scary Pizza Shack: the map as data, in ROBLOX space (studs, Y up, -Z = facing).

A Scene is a tree of Folders, Models, Parts, MeshParts, Markers, Attachments,
lights and joints. It knows nothing about Blender: build_map.py fills it, checks
it (brick grid, budgets, names, z-fighting), writes it to JSON for the Studio
build script, and hands it to spsblend.py for the previews and the FBX.

Conventions the build script relies on:
  * Part.cf is the part's CFrame (centre + rotation), size its Size.
  * MeshPart.cf is the CFrame of the mesh's bounding-box centre; the geometry
    stored under its mesh name is centred on that point, in the part's frame.
  * pivot is the PivotOffset (relative to the part), used for every hinge/slide.
  * Markers are 1x1x1 invisible anchored Parts whose -Z is the facing direction.
"""
import json
import math
from collections import Counter, OrderedDict, defaultdict

import numpy as np

import spsgeo as G
from spsgeo import CF, cf

# ---------------------------------------------------------------- palette (sRGB 0-255)

C = {
    # inside
    "cream": (240, 228, 196), "cream_dark": (214, 196, 156), "red": (196, 40, 32), "red_dark": (150, 30, 28),
    "mustard": (226, 170, 40), "mustard_dark": (186, 132, 30), "green": (38, 76, 52), "green_dark": (26, 54, 38),
    "wood": (160, 104, 62), "wood_dark": (112, 70, 42), "wood_light": (196, 150, 100), "black": (30, 30, 32),
    "white": (240, 240, 236), "steel": (150, 156, 162), "steel_dark": (90, 94, 100), "brick": (150, 70, 52),
    "brick_dark": (110, 52, 40), "soot": (40, 34, 32), "cardboard": (196, 160, 112), "cardboard_dark": (164, 128, 86),
    "glass": (186, 214, 224), "screen": (24, 40, 34), "tile_dark": (36, 36, 40), "tile_light": (232, 230, 222),
    "grey": (128, 128, 124), "grey_dark": (72, 72, 74), "fire": (255, 132, 40), "bulb": (255, 214, 140),
    "bulb_cool": (210, 230, 255), "paper": (246, 244, 234), "flour": (248, 246, 238),
    # food
    "dough": (236, 204, 150), "crust": (214, 158, 84), "sauce": (184, 36, 26), "cheese": (250, 206, 92),
    "cheese_melt": (252, 186, 64), "burnt": (46, 32, 24), "pepperoni": (178, 44, 36), "mushroom": (196, 176, 150),
    "mushroom_cap": (150, 112, 82), "pepper": (64, 150, 54), "olive": (40, 36, 40), "onion": (224, 206, 220),
    "onion_skin": (150, 92, 120), "pineapple": (250, 210, 70), "pineapple_skin": (170, 122, 50),
    "leaf": (52, 128, 60), "sausage": (130, 76, 52), "basil": (46, 140, 58), "terracotta": (190, 100, 64),
    "soil": (70, 50, 36),
    # outside, night: desaturated blue-greens
    "grass": (68, 90, 80), "grass_dark": (56, 76, 68), "pine": (42, 70, 64), "pine2": (50, 82, 74),
    "pine3": (34, 58, 54), "trunk": (84, 68, 58), "trunk_dark": (62, 52, 46), "asphalt": (58, 62, 68),
    "road_line": (196, 192, 166), "kerb": (140, 144, 144), "pave": (112, 118, 120), "pave_dark": (96, 102, 106),
    "dirt": (96, 84, 70), "gravel": (104, 108, 106), "fence": (112, 96, 78), "fence2": (90, 78, 66),
    "fence_dark": (70, 62, 54), "concrete": (150, 152, 150), "rust": (130, 70, 46), "bin_green": (52, 84, 66),
    "billboard": (204, 196, 170), "sign_blue": (54, 84, 120),
}

MATERIALS = {"Plastic", "SmoothPlastic", "Neon", "Glass", "Metal", "Wood", "WoodPlanks", "Fabric", "Concrete",
             "Slate", "Brick", "Cobblestone", "Foil", "DiamondPlate", "CorrodedMetal", "Marble", "Granite", "Ice",
             "Pebble", "Sand", "Grass", "Ground"}
SHAPES = {"Block", "Wedge", "Cylinder", "Ball"}

PLATE = 0.4


def on_grid_xz(v):
    return abs(v - round(v)) < 1e-6 and round(v) >= 1


def on_grid_y(v):
    k = v / PLATE
    return abs(k - round(k)) < 1e-6 and round(k) >= 1


# ---------------------------------------------------------------- nodes

class Node:
    __slots__ = ("kind", "name", "parent", "children", "p", "idx")

    def __init__(self, kind, name, parent=None, **p):
        self.kind = kind
        self.name = name
        self.parent = parent
        self.children = []
        self.p = p
        self.idx = None
        if parent is not None:
            parent.children.append(self)

    # -- tree helpers
    def path(self):
        n, out = self, []
        while n is not None:
            out.append(n.name)
            n = n.parent
        return "/".join(reversed(out))

    def walk(self):
        yield self
        for c in self.children:
            yield from c.walk()

    def find(self, name):
        for c in self.children:
            if c.name == name:
                return c
        return None

    def get(self, path):
        n = self
        for k in path.split("/"):
            n = n.find(k)
            if n is None:
                raise KeyError(path)
        return n

    def top(self):
        """The first-level folder this node lives in (Shack, Outside, Stations, Items, Markers)."""
        n = self
        while n.parent is not None and n.parent.parent is not None:
            n = n.parent
        return n.name

    def is_part(self):
        return self.kind in ("Part", "MeshPart", "Marker")

    def __repr__(self):
        return "<%s %s>" % (self.kind, self.path())


# ---------------------------------------------------------------- scene

class Scene:
    def __init__(self, root_name="PizzaShack"):
        self.root = Node("Folder", root_name)
        self.geoms = OrderedDict()        # mesh name -> centred Geo
        self.geom_info = {}               # mesh name -> dict(kind='prop'|'item', owner)
        self.notes = []                   # preview-only lights etc.
        self.preview_lights = []

    # -- containers
    def folder(self, parent, name):
        parent = self._node(parent)
        return parent.find(name) or Node("Folder", name, parent)

    def model(self, parent, name, **p):
        parent = self._node(parent)
        return Node("Model", name, parent, **p)

    def accessory(self, parent, name):
        """A real Roblox Accessory (Humanoid:AddAccessory): give it a part named Handle."""
        parent = self._node(parent)
        return Node("Accessory", name, parent)

    def humanoid(self, model, name="Humanoid", rig="R6"):
        """Humanoid (no name/health display) with an Animator inside."""
        h = Node("Humanoid", name, model, rig=rig)
        Node("Animator", "Animator", h)
        return h

    def special_mesh(self, part, mesh_type="Head", scale=(1.25, 1.25, 1.25), name="Mesh"):
        assert part.kind == "Part"
        return Node("SpecialMesh", name, part, mesh_type=mesh_type, scale=tuple(float(v) for v in scale))

    def _node(self, x):
        if isinstance(x, Node):
            return x
        return self.root.get(x)

    # -- parts
    def part(self, parent, name, size, cf_, color, shape="Block", material="Plastic", transparency=0.0,
             anchored=True, collide=True, touch=True, query=True, shadow=True, massless=False, surfaces=None,
             pivot=None, attrs=None, grid=True, tag=None, reflectance=0.0):
        parent = self._node(parent)
        assert shape in SHAPES, shape
        assert material in MATERIALS, material
        color = C[color] if isinstance(color, str) else tuple(int(v) for v in color)
        size = tuple(float(v) for v in size)
        if surfaces is None:
            if shape == "Block" and material == "Plastic":
                surfaces = "studs"
            elif shape == "Wedge" and material == "Plastic":
                surfaces = "wedge"
            else:
                surfaces = "smooth"
        return Node("Part", name, parent, size=size, cf=cf_, color=color, shape=shape, material=material,
                    transparency=float(transparency), anchored=anchored, collide=collide, touch=touch, query=query,
                    shadow=shadow, massless=massless, surfaces=surfaces, pivot=pivot, attrs=attrs or {},
                    grid=grid and shape in ("Block", "Wedge"), tag=tag, reflectance=reflectance)

    def box(self, parent, name, lo, hi, color, **kw):
        """Axis-aligned Block from its min / max corners (Roblox world)."""
        lo, hi = np.asarray(lo, float), np.asarray(hi, float)
        size = hi - lo
        assert np.all(size > 0), (name, lo, hi)
        return self.part(parent, name, size, CF((lo + hi) / 2), color, **kw)

    def boxr(self, parent, name, size, center, R, color, **kw):
        return self.part(parent, name, size, CF(center, R), color, **kw)

    def wedge(self, parent, name, size, center, R, color, **kw):
        return self.part(parent, name, size, CF(center, R), color, shape="Wedge", **kw)

    def cylinder(self, parent, name, length, diameter, center, axis_dir, color, **kw):
        """Cylinder part (Roblox cylinders run along local X)."""
        R = _axis_to_x(axis_dir)
        kw.setdefault("material", "Plastic")
        return self.part(parent, name, (length, diameter, diameter), CF(center, R), color, shape="Cylinder", **kw)

    def ball(self, parent, name, diameter, center, color, **kw):
        return self.part(parent, name, (diameter, diameter, diameter), CF(center), color, shape="Ball", **kw)

    # -- meshes
    def geom(self, name, geo, kind="prop", owner=None):
        """Register a geometry (any frame). Returns (centre, centred Geo). Same name twice must be identical."""
        lo, hi = geo.bbox()
        c = (lo + hi) / 2
        g = geo.xf(G.T(*(-c)))
        if name in self.geoms:
            old = self.geoms[name]
            if len(old.v) != len(g.v) or not np.allclose(old.arr(), g.arr(), atol=1e-6):
                raise ValueError("geometry %s registered twice with different shapes" % name)
        else:
            self.geoms[name] = g
            self.geom_info[name] = {"kind": kind, "owner": owner}
        return c, self.geoms[name]

    def mesh(self, parent, name, mesh_name, geo_or_none, frame, color, material="Plastic", transparency=0.0,
             anchored=True, collide=False, touch=True, query=True, shadow=True, massless=False, pivot=None,
             attrs=None, kind="prop", owner=None, tag=None):
        """MeshPart. `frame` is the CFrame of the space the geometry was modelled in; the
        part itself sits at frame * (bbox centre)."""
        parent = self._node(parent)
        if geo_or_none is None:
            g = self.geoms[mesh_name]
            c = np.zeros(3)
        else:
            c, g = self.geom(mesh_name, geo_or_none, kind, owner)
        color = C[color] if isinstance(color, str) else tuple(int(v) for v in color)
        lo, hi = g.bbox()
        return Node("MeshPart", name, parent, mesh=mesh_name, cf=frame * CF(c), size=tuple(hi - lo), color=color,
                    material=material, transparency=float(transparency), anchored=anchored, collide=collide,
                    touch=touch, query=query, shadow=shadow, massless=massless, pivot=pivot, attrs=attrs or {},
                    tag=tag)

    # -- markers / attachments / lights / joints
    def marker(self, parent, name, cf_):
        parent = self._node(parent)
        return Node("Marker", name, parent, cf=cf_, size=(1.0, 1.0, 1.0))

    def attachment(self, part, name, world_cf):
        assert part.is_part()
        return Node("Attachment", name, part, cf=world_cf)

    def light(self, part, kind="PointLight", name="Light", color=(255, 214, 160), brightness=1.0, range_=12.0,
              shadows=True, angle=None, face=None, enabled=True):
        assert kind in ("PointLight", "SpotLight", "SurfaceLight")
        color = C[color] if isinstance(color, str) else tuple(int(v) for v in color)
        return Node("Light", name, part, cls=kind, color=color, brightness=brightness, range=range_,
                    shadows=shadows, angle=angle, face=face, enabled=enabled)

    def weld(self, part0, part1, name="Weld"):
        return Node("Weld", name, part1, part0=part0, part1=part1)

    def motor(self, part0, part1, name, hinge_world_cf, parent=None):
        """Motor6D whose C0/C1 both land on hinge_world_cf. Parented to part1 unless told
        otherwise (R6 joints live in Part0: HumanoidRootPart.RootJoint, Torso.Neck, ...)."""
        return Node("Motor", name, parent or part1, part0=part0, part1=part1, hinge=hinge_world_cf)

    def attr(self, node, key, value):
        node.p.setdefault("attrs", {})[key] = value

    # -- queries
    def nodes(self, kind=None):
        for n in self.root.walk():
            if kind is None or n.kind == kind or (isinstance(kind, tuple) and n.kind in kind):
                yield n

    def number(self):
        for i, n in enumerate(self.root.walk()):
            n.idx = i


def _axis_to_x(d):
    """Rotation taking local +X to direction d (for cylinders)."""
    d = np.asarray(d, float)
    d = d / np.linalg.norm(d)
    x = np.array((1.0, 0, 0))
    if np.allclose(d, x):
        return np.eye(3)
    if np.allclose(d, -x):
        return G.ry(180)
    if abs(d[1]) > 0.999:
        return G.rz(90 if d[1] > 0 else -90)
    if abs(d[2]) > 0.999:
        return G.ry(-90 if d[2] > 0 else 90)
    axis = np.cross(x, d)
    ang = math.degrees(math.acos(np.clip(np.dot(x, d), -1, 1)))
    return G.rot_axis(axis, ang)


# ---------------------------------------------------------------- checks

def check_grid(scene):
    bad = []
    for n in scene.nodes("Part"):
        if not n.p["grid"]:
            continue
        sx, sy, sz = n.p["size"]
        if not (on_grid_xz(sx) and on_grid_xz(sz) and on_grid_y(sy)):
            bad.append((n.path(), n.p["size"]))
    for n in scene.nodes("Part"):
        if n.p["shape"] == "Cylinder":
            L, d1, d2 = n.p["size"]
            if abs(d1 - d2) > 1e-6:
                bad.append((n.path() + " (cylinder not round)", n.p["size"]))
    return bad


def part_counts(scene):
    cnt = Counter()
    for n in scene.nodes(("Part", "MeshPart", "Marker")):
        cnt[n.top()] += 1
    return cnt


def mesh_budget(scene):
    """(prop meshes over 1500 tris, items over 600 tris in total)."""
    over_prop = [(k, g.tris()) for k, g in scene.geoms.items()
                 if scene.geom_info[k]["kind"] == "prop" and g.tris() >= 1500]
    per_item = defaultdict(int)
    items = scene.root.find("Items")
    if items:
        for m in items.children:
            for n in m.walk():
                if n.kind == "MeshPart":
                    per_item[m.name] += scene.geoms[n.p["mesh"]].tris()
    over_item = [(k, v) for k, v in per_item.items() if v >= 600]
    return over_prop, over_item, dict(per_item)


def _faces_aa(n):
    """Axis-aligned faces of a Block part: [(axis, sign, coord, (u0, u1, v0, v1))]."""
    R = n.p["cf"].R
    half = np.abs(R) @ (np.array(n.p["size"]) / 2)
    c = n.p["cf"].p
    lo, hi = c - half, c + half
    out = []
    for ax in range(3):
        u, v = [a for a in range(3) if a != ax]
        rect = (lo[u], hi[u], lo[v], hi[v])
        out.append((ax, -1, round(lo[ax], 4), rect))
        out.append((ax, 1, round(hi[ax], 4), rect))
    return out


class BoxIndex:
    """Point-in-solid queries against axis-aligned opaque Blocks (spatial hash)."""

    def __init__(self, scene, cell=8.0):
        self.cell = cell
        self.grid = defaultdict(list)
        for n in scene.nodes("Part"):
            p = n.p
            if p["shape"] != "Block" or p["transparency"] > 0.2 or not p["cf"].is_axis_aligned():
                continue
            half = np.abs(p["cf"].R) @ (np.array(p["size"]) / 2)
            lo, hi = p["cf"].p - half, p["cf"].p + half
            for i in range(int(lo[0] // cell), int(hi[0] // cell) + 1):
                for j in range(int(lo[1] // cell), int(hi[1] // cell) + 1):
                    for k in range(int(lo[2] // cell), int(hi[2] // cell) + 1):
                        self.grid[(i, j, k)].append((lo, hi, n))

    def inside(self, pt, exclude=()):
        key = tuple(int(v // self.cell) for v in pt)
        for lo, hi, n in self.grid.get(key, ()):
            if n in exclude:
                continue
            if np.all(pt > lo + 1e-4) and np.all(pt < hi - 1e-4):
                return True
        return False


def zfight(scene, min_area=0.02, ignore=lambda n: False):
    """Coplanar, same-facing, overlapping faces of axis-aligned opaque Blocks that can be
    seen (the overlap is not buried inside or against another solid part)."""
    buckets = defaultdict(list)
    for n in scene.nodes("Part"):
        if n.p["shape"] != "Block" or n.p["transparency"] >= 0.99 or not n.p["cf"].is_axis_aligned() or ignore(n):
            continue
        for ax, sg, co, rect in _faces_aa(n):
            buckets[(ax, sg, co)].append((rect, n))
    idx = BoxIndex(scene)
    hits = []
    for key, lst in buckets.items():
        if len(lst) < 2:
            continue
        ax, sg, co = key
        u, v = [a for a in range(3) if a != ax]
        lst.sort(key=lambda t: t[0][0])
        for i in range(len(lst)):
            (a0, a1, b0, b1), na = lst[i]
            for j in range(i + 1, len(lst)):
                (c0, c1, d0, d1), nb = lst[j]
                if c0 >= a1 - 1e-6:
                    break
                u0, u1 = max(a0, c0), min(a1, c1)
                v0, v1 = max(b0, d0), min(b1, d1)
                if u1 - u0 <= 1e-6 or v1 - v0 <= 1e-6 or (u1 - u0) * (v1 - v0) < min_area:
                    continue
                if na.p["color"] == nb.p["color"] and na.p["material"] == nb.p["material"]:
                    continue    # same look: harmless
                # sample the overlap just outside the faces: visible if any sample is in open air
                seen = False
                for fu in (0.137, 0.512, 0.883):
                    for fv in (0.141, 0.527, 0.871):
                        pt = np.zeros(3)
                        pt[ax] = co + sg * 0.02
                        pt[u] = u0 + (u1 - u0) * fu
                        pt[v] = v0 + (v1 - v0) * fv
                        if not idx.inside(pt, exclude=(na, nb)):
                            seen = True
                            break
                    if seen:
                        break
                if seen:
                    hits.append((na.path(), nb.path(), (ax, sg, float(co)), round((u1 - u0) * (v1 - v0), 3)))
    return hits


# ---------------------------------------------------------------- JSON

def _cf_json(c):
    return [[round(float(v), 5) for v in c.p], [[round(float(v), 6) for v in row] for row in c.R]]


def to_json(scene, path):
    scene.number()
    out = []
    for n in scene.root.walk():
        d = {"i": n.idx, "kind": n.kind, "name": n.name, "parent": n.parent.idx if n.parent else None}
        p = n.p
        if n.kind in ("Part", "MeshPart", "Marker"):
            d["cf"] = _cf_json(p["cf"])
            d["size"] = [round(v, 5) for v in p["size"]]
        if n.kind == "Marker":
            d["anchored"] = p.get("anchored", True)
            d["massless"] = p.get("massless", not p.get("anchored", True))
            if p.get("attrs"):
                d["attrs"] = p["attrs"]
        if n.kind == "Part":
            for k in ("color", "shape", "material", "transparency", "anchored", "collide", "touch", "query",
                      "shadow", "massless", "surfaces", "reflectance"):
                d[k] = p[k]
        if n.kind == "MeshPart":
            for k in ("mesh", "color", "material", "transparency", "anchored", "collide", "touch", "query",
                      "shadow", "massless"):
                d[k] = p[k]
        if n.kind in ("Part", "MeshPart"):
            if p.get("pivot") is not None:
                d["pivot"] = _cf_json(p["pivot"])
            if p.get("attrs"):
                d["attrs"] = p["attrs"]
        if n.kind in ("Model", "Accessory"):
            if p.get("primary") is not None:
                d["primary"] = p["primary"].idx
            if p.get("attrs"):
                d["attrs"] = p["attrs"]
        if n.kind == "Humanoid":
            d["rig"] = p["rig"]
        if n.kind == "SpecialMesh":
            d["mesh_type"] = p["mesh_type"]
            d["scale"] = list(p["scale"])
        if n.kind == "Attachment":
            d["cf"] = _cf_json(p["cf"])
        if n.kind == "Light":
            for k in ("cls", "color", "brightness", "range", "shadows", "angle", "face", "enabled"):
                d[k] = p[k]
        if n.kind == "Attachment" and p.get("attrs"):
            d["attrs"] = p["attrs"]
        if n.kind in ("Weld", "Motor"):
            d["part0"] = p["part0"].idx
            d["part1"] = p["part1"].idx
            if n.kind == "Motor":
                d["hinge"] = _cf_json(p["hinge"])
        out.append(d)
    geoms = {k: {"tris": g.tris(), "size": [round(float(v), 5) for v in (g.bbox()[1] - g.bbox()[0])],
                 "kind": scene.geom_info[k]["kind"]} for k, g in scene.geoms.items()}
    with open(path, "w") as f:
        json.dump({"nodes": out, "meshes": geoms}, f, separators=(",", ":"))
    return out


ITEM_MARKERS = ("Work", "WorkSauce", "WorkCheese", "Handover", "Delivery_Drop")


def is_item_marker(name):
    return name in ITEM_MARKERS or name.startswith("Slot") or name.startswith("Tub")


def surface_under(scene, pt, geoms=True, depth=0.6):
    """Height of the highest solid top face directly under pt (within `depth`), from Parts
    (blocks, any rotation via their AABB when axis-aligned) and MeshParts (vertex tops)."""
    best = None
    x, y, z = pt
    for n in scene.nodes(("Part", "MeshPart")):
        p = n.p
        if p["transparency"] >= 0.99:
            continue
        if n.kind == "Part":
            if p["shape"] != "Block" or not p["cf"].is_axis_aligned():
                continue
            half = np.abs(p["cf"].R) @ (np.array(p["size"]) / 2)
            lo, hi = p["cf"].p - half, p["cf"].p + half
            if lo[0] - 1e-6 <= x <= hi[0] + 1e-6 and lo[2] - 1e-6 <= z <= hi[2] + 1e-6 and y - depth <= hi[1] <= y + 1e-3:
                best = hi[1] if best is None else max(best, hi[1])
        elif geoms:
            g = scene.geoms[p["mesh"]]
            V = (p["cf"].R @ np.array(g.v).T).T + p["cf"].p
            if not (V[:, 0].min() - 0.6 <= x <= V[:, 0].max() + 0.6 and V[:, 2].min() - 0.6 <= z <= V[:, 2].max() + 0.6):
                continue
            top = _ray_down(V, g.f, x, z, y + 1e-3, y - depth)
            if top is None:
                near = V[(np.abs(V[:, 0] - x) < 0.6) & (np.abs(V[:, 2] - z) < 0.6) & (V[:, 1] <= y + 1e-3) &
                         (V[:, 1] >= y - depth)]
                top = near[:, 1].max() if len(near) else None
            if top is not None:
                best = top if best is None else max(best, top)
    return best


def _ray_down(V, faces, x, z, y_hi, y_lo):
    """Highest point of the mesh's faces straight under (x, z) between y_lo and y_hi."""
    best = None
    for f in faces:
        a = V[f[0]]
        for k in range(1, len(f) - 1):
            b, c = V[f[k]], V[f[k + 1]]
            d = (b[2] - c[2]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[2] - c[2])
            if abs(d) < 1e-12:
                continue
            l1 = ((b[2] - c[2]) * (x - c[0]) + (c[0] - b[0]) * (z - c[2])) / d
            l2 = ((c[2] - a[2]) * (x - c[0]) + (a[0] - c[0]) * (z - c[2])) / d
            l3 = 1.0 - l1 - l2
            if min(l1, l2, l3) < -1e-9:
                continue
            yy = l1 * a[1] + l2 * b[1] + l3 * c[1]
            if y_lo <= yy <= y_hi and (best is None or yy > best):
                best = yy
    return best


def check_item_markers(scene):
    """Every item marker must sit exactly on the surface under it."""
    bad, ok = [], 0
    for n in scene.nodes("Marker"):
        if not is_item_marker(n.name) or n.top() == "Items":
            continue
        pt = n.p["cf"].p
        s = surface_under(scene, pt)
        if s is None or abs(s - pt[1]) > 1e-4:
            bad.append((n.path(), round(float(pt[1]), 3), None if s is None else round(float(s), 3)))
        else:
            ok += 1
    return ok, bad
