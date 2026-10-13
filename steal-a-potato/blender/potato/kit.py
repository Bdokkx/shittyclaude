"""The map's building helpers on top of spslib, with the brief's rules built in:

  * solid():  ground, walls and the few big simple props: CanCollide, CanQuery, CanTouch on.
  * deco():   everything else: CanCollide, CanTouch, CanQuery off; CastShadow off on small things.
  * mesh():   a MeshPart, decoration by default (pass solid=True for a big simple collider).
  * board():  the flat part named Board the game writes on (on its FRONT face, the part's -Z).
  * Checker:  ground and wall parts carry the attribute Checker = 4 (the game draws the checker).

Colours are sRGB tuples; flat, saturated, Plastic unless said."""
import math

import numpy as np

import spsgeo as G
from spsgeo import CF

SMALL = 4.0          # decorations whose biggest side is under this cast no shadow


def rgb(c):
    return tuple(int(v) for v in c)


def darker(c, k=0.8):
    return tuple(int(round(v * k)) for v in c)


def lighter(c, k=0.25):
    return tuple(int(round(v + (255 - v) * k)) for v in c)


class Kit:
    def __init__(self, sc):
        self.sc = sc
        self.mesh_count = {}

    # -- parts
    def solid(self, parent, name, size, cf_, color, shape="Block", material="Plastic", studs=True, checker=False,
              shadow=True, **kw):
        p = self.sc.part(parent, name, size, cf_, rgb(color), shape=shape, material=material, grid=False,
                         surfaces=None if studs and shape == "Block" and material == "Plastic" else "smooth",
                         shadow=shadow, **kw)
        if checker:
            self.sc.attr(p, "Checker", 4)
        return p

    def solid_box(self, parent, name, lo, hi, color, **kw):
        lo, hi = np.asarray(lo, float), np.asarray(hi, float)
        return self.solid(parent, name, hi - lo, CF((lo + hi) / 2), color, **kw)

    def deco(self, parent, name, size, cf_, color, shape="Block", material="Plastic", studs=None, shadow=None,
             transparency=0.0, **kw):
        if shadow is None:
            shadow = bool(max(size) >= SMALL)
        if studs is None:
            studs = shape == "Block" and material == "Plastic" and size[1] <= min(size[0], size[2])
        return self.sc.part(parent, name, size, cf_, rgb(color), shape=shape, material=material, grid=False,
                            collide=False, touch=False, query=False, shadow=shadow, transparency=transparency,
                            surfaces="studs" if studs and shape == "Block" else "smooth", **kw)

    def deco_box(self, parent, name, lo, hi, color, **kw):
        lo, hi = np.asarray(lo, float), np.asarray(hi, float)
        return self.deco(parent, name, tuple(hi - lo), CF((lo + hi) / 2), color, **kw)

    def mesh(self, parent, name, mesh_name, geo, frame, color, material="Plastic", solid=False, shadow=None,
             transparency=0.0, **kw):
        if geo is not None:
            lo, hi = geo.bbox()
            big = max(hi - lo)
        else:
            lo, hi = self.sc.geoms[mesh_name].bbox()
            big = max(hi - lo)
        if shadow is None:
            shadow = bool(solid or big >= SMALL)
        self.mesh_count[mesh_name] = self.mesh_count.get(mesh_name, 0) + 1
        return self.sc.mesh(parent, name, mesh_name, geo, frame, rgb(color), material=material, collide=solid,
                            touch=solid, query=solid, shadow=shadow, transparency=transparency, **kw)

    def marker(self, parent, name, cf_):
        return self.sc.marker(parent, name, cf_)

    def board(self, parent, w, h, cf_, color=(250, 248, 240), name="Board", thick=0.4, material="SmoothPlastic"):
        """Flat Board w x h, its front face (the part's -Z) where the game writes."""
        return self.deco(parent, name, (w, h, thick), cf_, color, material=material, studs=False)

    def prompt(self, parent, cf_, name="Prompt", size=(4.0, 4.0, 2.0)):
        """Invisible part the game hangs a ProximityPrompt on."""
        return self.sc.part(parent, name, size, cf_, (255, 255, 255), material="SmoothPlastic", transparency=1.0,
                            collide=False, touch=False, query=False, shadow=False, grid=False, surfaces="smooth")

    def attr(self, node, key, value):
        self.sc.attr(node, key, value)

    def attach(self, part, name, world_pos):
        return self.sc.attachment(part, name, CF(np.asarray(world_pos, float)))


def facing(dx, dz):
    """Rotation whose LookVector (-Z) points along (dx, 0, dz)."""
    return G.facing(np.array((dx, 0.0, dz)) / math.hypot(dx, dz))


def yaw(deg):
    return G.ry(deg)
