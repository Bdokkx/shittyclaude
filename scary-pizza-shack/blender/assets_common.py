"""Shared bits for the batch-2 assets: colours, welded detail meshes, moving-part notes."""
import numpy as np

import spsgeo as G
from spsgeo import CF

# sRGB 0-255; the build script colours every white mesh with these
P = {
    # Inspector
    "skin_grey": (198, 200, 194), "suit": (50, 52, 58), "suit_light": (70, 72, 80), "shirt": (236, 236, 230),
    "tie_red": (118, 22, 26), "hat_black": (22, 22, 24), "shoe_black": (18, 18, 20), "clip_wood": (156, 108, 64),
    "steel": (176, 180, 186), "paper": (244, 242, 232), "ink": (30, 30, 34),
    # Watcher / Passenger
    "void": (14, 14, 16), "eye_pale": (255, 248, 226), "shadow": (24, 24, 28),
    # neutral kit colours (the game recolours them)
    "kit_hair": (92, 62, 40), "kit_hair2": (60, 42, 30), "kit_cloth": (70, 96, 140), "kit_cloth2": (170, 60, 50),
    "kit_dark": (40, 40, 44), "kit_light": (220, 216, 204), "kit_metal": (170, 174, 180), "kit_lens": (150, 200, 220),
    "kit_yellow": (232, 214, 40), "kit_silver": (196, 200, 204), "kit_leather": (120, 74, 44),
    # floor tiles (batch 1)
    "tile_dark": (36, 36, 40), "tile_light": (232, 230, 222),
}

MOVING = []        # (model path, part, how) for the README


def col(c):
    return P[c] if isinstance(c, str) and c in P else c


def detail(sc, model, body_part, pname, geo, frame, color, owner, material="Plastic", transparency=0.0,
           mesh_name=None, collide=False, shadow=True):
    """A MeshPart modelled in `frame` space, welded (unanchored, massless) to body_part."""
    mp = sc.mesh(model, pname, mesh_name or owner + "__" + pname, geo, frame, col(color), material=material,
                 transparency=transparency, anchored=False, collide=collide, touch=False, query=False,
                 shadow=shadow, massless=True, owner=owner)
    sc.weld(body_part, mp, "Weld")
    return mp


def handle(sc, model, cf_, size=(0.4, 0.4, 0.4)):
    """Invisible anchored Handle (the template's root; set Anchored = false when you weld it on)."""
    h = sc.part(model, "Handle", size, cf_, (255, 255, 255), material="SmoothPlastic", transparency=1.0,
                anchored=True, collide=False, touch=False, query=False, shadow=False, massless=True,
                surfaces="smooth", grid=False)
    model.p["primary"] = h
    return h


def pivot(node, world_cf):
    node.p["pivot"] = node.p["cf"].inv() * world_cf


def moving(path, part, how):
    MOVING.append((path, part, how))


def slab(pts, thick, axis="z", c=(0, 0, 0)):
    """Outline extruded `thick` (axis 'z': outline in XY seen from the front)."""
    return G.extrude(pts, thick, axis, c)


def mirror_x(g):
    return g.xf(np.diag([-1.0, 1.0, 1.0, 1.0]))
