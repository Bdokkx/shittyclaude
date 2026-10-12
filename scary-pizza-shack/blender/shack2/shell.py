"""The shack's shell, inside and out.

Inside, every wall runs in three bands: a dark skirting (0.2 proud), square off-white tiles
to the dado rail (tile panels on a grout backing; some cracked, missing or replaced in a
different white), a mustard dado rail, tired grey-green paint, and a stepped cream cornice
under the ceiling. The ceiling is dark beams wall to wall with panels between them (a few
stained, one sagging). The floor keeps the checker, worn along the paths, with a patch of
newer tiles that do not quite match exactly where the Inspector rises.

Outside: a brick base course (a ledge), cream siding in bands, red corner pilasters, a green
band, the parapet and coping, and the flat studded roof."""
import math

import numpy as np

import mk
import spsgeo as G
from spsgeo import CF, T

from . import interior as IP, layout as L
from .kit import bevel_box, chamfer_slab, col

# inside band heights (Y). Tiles align with the worktop (3.4) so a worktop shows exactly one row
SKIRT = (0.2, 1.0)        # box; 0.6 shows above the floor
TILES = (1.0, 4.2)        # 4 rows of 0.8
DADO = (4.2, 4.6)
PAINT = (4.6, 8.6)
CORN1 = (8.6, 9.0)
CORN2 = (9.0, 9.4)
OUT_OFF = 0.5             # the outer skin's face is this far outside the wall core (37 x 23 outside)


def build(k, root, rng):
    sc = k.sc
    shack = sc.folder(root, "Shack")
    floor(k, sc.folder(shack, "Floor"), rng)
    inside_walls(k, sc.folder(shack, "Walls"), rng)
    ceiling(k, sc.folder(shack, "Ceiling"), rng)
    outside_walls(k, sc.folder(shack, "Exterior"), rng)
    roof(k, sc.folder(shack, "Roof"), rng)
    return shack


# ---------------------------------------------------------------- floor

CRACKED = ((-11, -4), (1, 4), (-15, -8), (7, 0))     # floor cells (x0, z0) with a cracked tile
MISSING = (5, 2)                                     # one tile gone, the screed and its adhesive showing


def _crack_halves(rng, gap=0.09):
    """A 2 x 2 tile split by a zig-zag running west to east: two outlines (top view, centred)."""
    zs = [rng.uniform(-0.5, 0.5)]
    for _ in range(4):
        zs.append(float(np.clip(zs[-1] + rng.uniform(-0.45, 0.45), -0.7, 0.7)))
    xs = np.linspace(-1.0, 1.0, len(zs))
    south = [(-1.0, -1.0), (1.0, -1.0)] + [(x, z - gap) for x, z in zip(xs[::-1], zs[::-1])]
    north = [(-1.0, 1.0)] + [(x, z + gap) for x, z in zip(xs, zs)] + [(1.0, 1.0)]
    north = north[::-1]
    return south, north


def floor(k, f, rng):
    """2 x 2 checker of bevelled tiles in yellowed white and black (smooth: studs are for built
    surfaces outside), worn along the paths, a few cracked, one missing, a drain by the sink,
    and a circle of newer tiles that don't quite match where the Inspector rises."""
    rx, rz = -0.5, 0.5                         # Inspector_Rise
    tile = bevel_box(2.0, 0.4, 2.0, 0.06)
    dx, dz = L.DRAIN
    for i, x in enumerate(range(int(L.IN_X0), int(L.IN_X1), 2)):
        for j, z in enumerate(range(int(L.IN_Z0), int(L.IN_Z1), 2)):
            dark = (i + j) % 2 == 0
            cx, cz = x + 1, z + 1
            # worn along the paths: the aisle in front of the north line, to the window, to the back door
            worn = (-6.5 < cz < -2.5) or (abs(cx) < 3 and cz > 2) or (cx < -10 and -10 < cz < 0)
            new = math.hypot(cx - rx, cz - rz) < L.INSPECT_R + 0.6
            if new:
                c = "floor_b_new" if dark else "floor_w_new"
                y1 = L.FLOOR + 0.02                     # the newer tiles sit a hair proud
            else:
                c = ("floor_b_worn" if dark else "floor_w_worn") if worn and rng.random() < 0.8 else \
                    ("floor_b" if dark else "floor_w")
                y1 = L.FLOOR
            if (x, z) == MISSING:
                _missing_tile(k, f, x, z, rng)
            elif x < dx < x + 2 and z < dz < z + 2:
                _drain_tile(k, f, x, z, c)
            elif (x, z) in CRACKED:
                _cracked_tile(k, f, x, z, c, rng)
            else:
                k.mesh(f, "Tile", "Floor__Tile", tile, CF((cx, y1 - 0.2, cz)), c, solid=True)
    mats(k, f)


def _cracked_tile(k, f, x, z, c, rng):
    south, north = _crack_halves(rng)
    k.mesh(f, "Bed", "Floor__Bed", bevel_box(2.0, 0.1, 2.0, 0.02), CF((x + 1, 0.05, z + 1)), "adhesive", solid=True)
    k.mesh(f, "Tile", "Floor__CrackS%d_%d" % (x, z), chamfer_slab(south, 0.3, 0.05), CF((x + 1, 0.1, z + 1)), c,
           solid=True)
    k.mesh(f, "Tile", "Floor__CrackN%d_%d" % (x, z), chamfer_slab(north, 0.26, 0.05), CF((x + 1, 0.1, z + 1)), c,
           solid=True)                                 # the loose half has sunk a little


def _missing_tile(k, f, x, z, rng):
    """The tile is gone: grey screed with combed lines of old black adhesive, a corner of the
    broken tile still stuck down."""
    k.mesh(f, "Screed", "Floor__Screed", bevel_box(2.0, 0.2, 2.0, 0.03), CF((x + 1, 0.1, z + 1)), "screed",
           solid=True)
    comb = G.Geo()
    for t in np.arange(-0.7, 0.75, 0.35):
        comb.add(bevel_box(1.5, 0.05, 0.15, 0.015, c=(0.0, 0.025, t)))
    k.mesh(f, "Adhesive", "Floor__Adhesive", comb.xf(G.M(G.ry(30))), CF((x + 1, 0.2, z + 1)), "adhesive",
           shadow=False)
    corner = [(-1.0, -1.0), (-0.1, -1.0), (-0.35, -0.55), (-0.7, -0.4), (-1.0, -0.15)]
    k.mesh(f, "Shard", "Floor__Shard", chamfer_slab(corner, 0.2, 0.04), CF((x + 1, 0.2, z + 1)), "floor_w",
           solid=True)


def _drain_tile(k, f, x, z, c):
    """A tile with a square steel drain let into it: frame, grate and the dark sump under it."""
    ring = G.Geo()
    for (sx, sz, ox, oz) in ((2.0, 0.4, 0.0, -0.8), (2.0, 0.4, 0.0, 0.8), (0.4, 1.2, -0.8, 0.0), (0.4, 1.2, 0.8, 0.0)):
        ring.add(bevel_box(sx, 0.4, sz, 0.06, c=(ox, 0.0, oz)))
    k.mesh(f, "Tile", "Floor__DrainTile", ring, CF((x + 1, L.FLOOR - 0.2, z + 1)), c, solid=True)
    k.box(f, "Sump", (x + 0.6, -0.8, z + 0.6), (x + 1.4, 0.0, z + 1.4), "charcoal", solid=True, grid=False)
    gr = G.Geo()
    for t in (-0.45, -0.15, 0.15, 0.45):
        gr.add(bevel_box(1.2, 0.15, 0.15, 0.03, c=(0.0, -0.075, t)))
    gr.add(bevel_box(0.15, 0.15, 1.2, 0.03, c=(0.0, -0.225, 0.0)))
    k.mesh(f, "Grate", "Floor__Grate", gr, CF((x + 1, L.FLOOR - 0.02, z + 1)), "steel_dark", solid=True)
    k.mark_used("FloorDrain")


def _mat_geo(w, d):
    g = G.Geo()
    g.add(bevel_box(w, 0.1, d, 0.04, c=(0.0, 0.05, 0.0)))
    n = int((d - 0.3) / 0.45)
    for t in np.linspace(-(d - 0.5) / 2, (d - 0.5) / 2, n):
        g.add(bevel_box(w - 0.3, 0.06, 0.2, 0.02, c=(0.0, 0.13, t)))
    return g


def mats(k, f):
    """Ribbed rubber mats where people stand all night: the prep line, the oven front."""
    for i, (x0, x1, z0, z1) in enumerate(L.MATS):
        w, d = x1 - x0, z1 - z0
        k.mesh(f, "Mat", "Floor__Mat%dx%d" % (round(w * 10), round(d * 10)), _mat_geo(w, d),
               CF(((x0 + x1) / 2, L.FLOOR, (z0 + z1) / 2), G.ry(0.5 if i % 2 else -0.4)), "rubber" if i else "rubber_worn",
               solid=True)
    k.mark_used("RubberMat")


# ---------------------------------------------------------------- inside walls

def _wall_lohi(wall, ua, ub, ya, yb, proud, thick=1.0):
    """World box of a band piece on a wall, `proud` into the room, `thick` deep."""
    if wall == "N":
        return (ua, ya, L.IN_Z0 - thick + proud), (ub, yb, L.IN_Z0 + proud)
    if wall == "S":
        return (ua, ya, L.IN_Z1 - proud), (ub, yb, L.IN_Z1 + thick - proud)
    if wall == "W":
        return (L.IN_X0 - thick + proud, ya, ua), (L.IN_X0 + proud, yb, ub)
    return (L.IN_X1 - proud, ya, ua), (L.IN_X1 + thick - proud, yb, ub)


def _band(k, f, name, wall, y0, y1, color, proud=0.0, cut=(), **kw):
    """One band along a wall, cut round openings and furniture. Flush bands are the wall's
    core (1-thick blocks); proud bands (skirting, dado rail, cornice) are bevelled mouldings
    that stand `proud` into the room and reach only 0.1 into the wall."""
    u0, u1 = IP.wall_rect(wall)
    out = []
    for ua, ub, ya, yb, c in mk.wall_pieces(u0, u1, [(y0, y1, color)], list(cut)):
        if ub - ua < 0.01 or yb - ya < 0.01:
            continue
        if proud == 0.0:
            lo, hi = _wall_lohi(wall, ua, ub, ya, yb, 0.0)
            out.append(k.box(f, name, lo, hi, c, **kw))
            continue
        ln, h, d = ub - ua, yb - ya, proud + 0.1
        bev = min(0.08, h * 0.25, d * 0.3)
        geo = bevel_box(ln, h, d, bev)
        mesh_name = "Wall__%s%dx%dx%d" % (name, int(round(ln * 10)), int(round(h * 10)), int(round(d * 100)))
        from .counters import wcf
        frame = wcf(wall, (ua + ub) / 2, (ya + yb) / 2, proud / 2 - 0.05)
        out.append(k.mesh(f, name, mesh_name, geo, frame, c, solid=True, shadow=h >= 0.5))
    return out


WALLS = {
    "N": [(L.DOOR_X0, L.DOOR_X1, L.DOOR_Y0, L.DOOR_Y1)],
    "S": [(L.WIN_X0, L.WIN_X1, L.WIN_Y0, L.WIN_Y1)],
    "W": [(L.SIDE_Z0, L.SIDE_Z1, L.SIDE_Y0, L.SIDE_Y1)],
    "E": [],
}


def _beam_cuts(wall):
    if wall not in ("N", "S"):
        return []
    return [(b - 0.5, b + 0.5, IP.BEAM_Y[0], IP.BEAM_Y[1]) for b in IP.BEAMS]


def pilaster_spots(wall):
    """Beam ends on the N wall where nothing tall stands: a timber post carries the beam.
    (Off for now: the wall shelves and racks of the prep line want those spots.)"""
    if wall != "N" or True:
        return []
    out = []
    for b in IP.BEAMS:
        a0, a1 = b - 0.5, b + 0.5
        if any(u0 < a1 and u1 > a0 and top > DADO[1] for (u0, u1, top) in IP.occupied(wall)):
            continue
        out.append(b)
    return out


def inside_walls(k, f, rng):
    for w, op in WALLS.items():
        occ = IP.occupied(w)
        items = IP.wall_items(w)
        low = [(u0, u1, -1.0, top) for (u0, u1, top) in occ] + items          # counters + tall things
        tall = [(u0, u1, -1.0, top) for (u0, u1, top) in occ if top > DADO[0]] + items
        posts = [(b - 0.5, b + 0.5, DADO[1], IP.BEAM_Y[0]) for b in pilaster_spots(w)]
        # the core carries the grout (tile band) and the paint; the rest stand proud
        _band(k, f, "Skirting", w, *SKIRT, "skirt", proud=0.2, cut=op + low, solid=True)
        _band(k, f, "TileBacking", w, *TILES, "grout", cut=op, solid=True)
        _band(k, f, "DadoRail", w, *DADO, "dado", proud=0.2, cut=op + tall, solid=True)
        _band(k, f, "Paint", w, *PAINT, "paint", cut=op, solid=True)
        _band(k, f, "Cornice", w, *CORN1, "cornice", proud=0.2, cut=op + tall + _beam_cuts(w) + posts, solid=True)
        _band(k, f, "Cornice", w, *CORN2, "cornice", proud=0.4, cut=op + tall + _beam_cuts(w), solid=True)
        tiles(k, f, w, op + items, occ, rng)
        # the core above the ceiling (attic)
        _band(k, f, "AtticWall", w, L.CEIL, L.WALL_TOP, "beam_dark", cut=op, solid=True)
        # timber posts under the beam ends, from the dado rail up to the beam
        for b in pilaster_spots(w):
            lo, hi = _wall_lohi(w, b - 0.5, b + 0.5, DADO[1], IP.BEAM_Y[0], 0.4)
            k.box(f, "Post", lo, hi, "beam", solid=True)
            lo, hi = _wall_lohi(w, b - 0.7, b + 0.7, IP.BEAM_Y[0] - 0.4, IP.BEAM_Y[0], 0.6, thick=1.0)
            k.mesh(f, "PostCap", "Wall__PostCap", bevel_box(1.4, 0.4, 0.6, 0.06),
                   CF(((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, (lo[2] + hi[2]) / 2)) *
                   CF(R=np.eye(3) if w in ("N", "S") else G.ry(90)) * CF((0, 0, 0.2 if w == "N" else -0.2)),
                   "beam_dark", shadow=False)


TILE = 0.7          # tile face, 0.1 grout
TILE_T = 0.15       # tiles stand 0.15 proud of the grout
PITCH = 0.8


def _wall_cf(w, u, y):
    """Frame on a wall's inside face at (u, y): local +Z points into the room, +X along u."""
    if w == "N":
        return CF((u, y, L.IN_Z0), np.eye(3))
    if w == "S":
        return CF((u, y, L.IN_Z1), G.ry(180))
    if w == "W":
        return CF((L.IN_X0, y, u), G.ry(90))
    return CF((L.IN_X1, y, u), G.ry(-90))


def _u_dir(w):
    """Which way a wall frame's local +X runs along u: with it on N and E, against it on S and W."""
    return 1.0 if w in ("N", "E") else -1.0


_PANELS = {}


def _panel_geo(mask):
    """The tiles of one 5 x 4 panel; mask[c][r] in the panel's own column order."""
    key = "".join("1" if mask[c][r] else "0" for c in range(5) for r in range(4))
    if key not in _PANELS:
        g = G.Geo()
        for c in range(5):
            for r in range(4):
                if mask[c][r]:
                    g.add(bevel_box(TILE, TILE, TILE_T, 0.05, c=(-2.0 + 0.4 + PITCH * c, 0.4 + PITCH * r, TILE_T / 2)))
        _PANELS[key] = g
    return key, _PANELS[key]


def tiles(k, f, w, openings, occ, rng):
    """Square tiles on the tile band in panels of 5 x 4: only the tiles that can be seen (above
    the counters exactly the one row at 3.4..4.2), a few missing (the dark gap shows), a few
    replaced in a whiter white."""
    y0 = TILES[0]
    u0, u1 = IP.wall_rect(w)
    sd = _u_dir(w)
    u = u0
    while u + 4 <= u1 + 1e-6:
        seen = {}
        for c in range(5):                         # c counts along u
            ta, tb = u + 0.05 + PITCH * c, u + 0.75 + PITCH * c
            for r in range(4):
                ya, yb = y0 + 0.05 + PITCH * r, y0 + 0.75 + PITCH * r
                hid = any(oa < tb and ob > ta and oy0 < yb and oy1 > ya for (oa, ob, oy0, oy1) in openings)
                hid = hid or any(a < tb and b > ta and ya < top for (a, b, top) in occ)
                seen[(c, r)] = not hid
        present = [cr for cr, v in seen.items() if v]
        if present:
            v = rng.random()
            miss = odd = None
            if v < 0.14 and len(present) > 4:
                miss = present[int(rng.integers(0, len(present)))]
            elif v < 0.34:
                odd = present[int(rng.integers(0, len(present)))]

            def local(c):                          # u-order column -> the panel's own column
                return c if sd > 0 else 4 - c
            mask = [[False] * 4 for _ in range(5)]
            for (c, r), vis in seen.items():
                mask[local(c)][r] = vis and (c, r) != miss and (c, r) != odd
            key, g = _panel_geo(mask)
            cf = _wall_cf(w, u + 2.0, y0)
            if any(any(col) for col in mask):
                k.mesh(f, "Tiles", "WallTiles__" + key, g, cf, "tile", shadow=False)

            def at(c, r, dz):
                return cf * CF((-2.0 + 0.4 + PITCH * local(c), 0.4 + PITCH * r, dz))
            if miss:
                k.mesh(f, "TileHole", "WallTiles__Hole", bevel_box(0.7, 0.7, 0.1, 0.03), at(*miss, 0.05), "skirt",
                       shadow=False)
            if odd:
                k.mesh(f, "Tile", "WallTiles__Odd", bevel_box(TILE, TILE, TILE_T + 0.02, 0.05),
                       at(*odd, TILE_T / 2 + 0.01), "tile_new", shadow=False)
        u += 4


# ---------------------------------------------------------------- ceiling

def ceiling(k, f, rng):
    """Dark beams wall to wall (on timber posts on the north wall), panels between them in a
    T-bar grid -- a few stained, one sagging out of its grid -- the hatch hole, and the attic
    above (joists and a dark lining) seen through it."""
    from .terrain import subtract
    y0, y1 = L.CEIL, L.CEIL_TOP
    hole = IP.HATCH
    stained = {(1, 1): "ceil_stain", (3, 3): "ceil_stain", (4, 0): "ceil_stain2", (0, 2): "ceil_stain2"}
    sag = (2, 3)
    zs = [L.IN_Z0, -5.0, 0.0, 5.0, L.IN_Z1]
    for bi, (x0, x1) in enumerate(IP.bays()):
        for pj, (z0, z1) in enumerate(zip(zs, zs[1:])):
            c = stained.get((bi, pj), "ceil")
            pieces = subtract((x0, x1, z0, z1), [hole])
            for (a, b, cz0, cz1) in pieces:
                if (bi, pj) == sag and len(pieces) == 1:
                    # a sagging panel: dropped out of its grid at one end
                    k.boxr(f, "Panel", (b - a, 0.4, cz1 - cz0), ((a + b) / 2, y0 + 0.2 - 0.13, (cz0 + cz1) / 2),
                           G.rx(-3.0), c, solid=True)
                else:
                    k.box(f, "Panel", (a, y0, cz0), (b, y1, cz1), c, solid=True)
            hx0_, hx1_, hz0_, hz1_ = hole
            under_hatch = x0 <= hx0_ and x1 >= hx1_ and hz0_ - 0.6 <= z0 <= hz1_ + 0.6
            if pj > 0 and not under_hatch:
                # T-bar under the joint between this panel and the one north of it
                k.mesh(f, "TBar", "Ceiling__TBar%d" % int(x1 - x0), bevel_box(x1 - x0, 0.15, 0.3, 0.04),
                       CF(((x0 + x1) / 2, y0 - 0.075, z0)), "tbar", shadow=False)
    # beams wall to wall
    for x in IP.BEAMS:
        k.box(f, "Beam", (x - 0.5, IP.BEAM_Y[0], L.IN_Z0), (x + 0.5, IP.BEAM_Y[1], L.IN_Z1), "beam", solid=True)
    # attic over the ceiling: joists and a dark lining (seen through the hatch)
    for x in IP.BEAMS:
        k.box(f, "AtticJoist", (x - 0.5, y1, L.IN_Z0), (x + 0.5, y1 + 1.2, L.IN_Z1), "beam_dark")
    k.box(f, "AtticLining", (L.IN_X0, L.WALL_TOP - 0.4, L.IN_Z0), (L.IN_X1, L.WALL_TOP, L.IN_Z1), "beam_dark",
          solid=True)


# ---------------------------------------------------------------- outside walls

OUT_BANDS = [(-0.6, 1.8, "brick1"), (1.8, 3.0, "siding"), (3.0, 4.2, "siding2"), (4.2, 5.4, "siding"),
             (5.4, 6.6, "siding2"), (6.6, 7.0, "red"), (7.0, 8.2, "siding"), (8.2, 9.4, "siding2"),
             (9.4, 10.6, "siding"), (10.6, 11.0, "siding2"), (11.0, 11.8, "trim_green"), (11.8, 14.6, "siding")]


def outside_walls(k, f, rng):
    """The outer skin, 0.5 outside the wall core; openings 0.5 wider (0.4 taller) so no
    reveal faces meet and every piece stays on the brick grid."""
    o = OUT_OFF
    win = (L.WIN_X0 - o, L.WIN_X1 + o, L.WIN_Y0 - 0.0, L.WIN_Y1 + 0.4)
    door = (L.DOOR_X0 - o, L.DOOR_X1 + o, -0.6, L.DOOR_Y1 + 0.4)
    side = (L.SIDE_Z0 - o, L.SIDE_Z1 + o, L.SIDE_Y0 - 0.4, L.SIDE_Y1 + 0.4)
    walls = (("S", L.OUT_X0, L.OUT_X1, [win]), ("N", L.OUT_X0, L.OUT_X1, [door]),
             ("W", L.OUT_Z0, L.OUT_Z1, [side]), ("E", L.OUT_Z0, L.OUT_Z1, []))
    for w, u0, u1, op in walls:
        for (y0, y1, c) in OUT_BANDS:
            base = c == "brick1"
            proud = 0.6 if base else 0.0
            t = 2.0 if base else 1.0                  # the base course reaches back into the core
            for ua, ub, ya, yb, cc in mk.wall_pieces(u0 - o, u1 + o, [(y0, y1, c)], op):
                if w == "S":
                    lo, hi = (ua, ya, L.OUT_Z1 + o - t + proud), (ub, yb, L.OUT_Z1 + o + proud)
                elif w == "N":
                    lo, hi = (ua, ya, L.OUT_Z0 - o - proud), (ub, yb, L.OUT_Z0 - o + t - proud)
                elif w == "W":
                    lo, hi = (L.OUT_X0 - o - proud, ya, ua), (L.OUT_X0 - o + t - proud, yb, ub)
                else:
                    lo, hi = (L.OUT_X1 + o - t + proud, ya, ua), (L.OUT_X1 + o + proud, yb, ub)
                k.box(f, "BaseCourse" if base else "Siding", lo, hi, cc, studs=base, solid=True)
    # corner pilasters
    for x in (L.OUT_X0 - o, L.OUT_X1 + o):
        for z in (L.OUT_Z0 - o, L.OUT_Z1 + o):
            k.box(f, "Pilaster", (x - 1, -0.6, z - 1), (x + 1, 15.4, z + 1), "red", solid=True)


# ---------------------------------------------------------------- roof

def roof(k, f, rng):
    o = OUT_OFF
    k.box(f, "Roof", (L.OUT_X0 - o, L.WALL_TOP, L.OUT_Z0 - o), (L.OUT_X1 + o, L.ROOF_TOP, L.OUT_Z1 + o), "charcoal",
          studs=True, solid=True)
    p0, p1 = L.ROOF_TOP, L.PARAPET_TOP
    c0, c1 = L.PARAPET_TOP, L.COPING_TOP
    X0, X1, Z0, Z1 = L.OUT_X0 - o, L.OUT_X1 + o, L.OUT_Z0 - o, L.OUT_Z1 + o
    for (a, b, c, d) in ((X0, X1, Z1 - 1, Z1), (X0, X1, Z0, Z0 + 1), (X0, X0 + 1, Z0 + 1, Z1 - 1),
                         (X1 - 1, X1, Z0 + 1, Z1 - 1)):
        k.box(f, "Parapet", (a, p0, c), (b, p1, d), "siding", solid=True)
    for (a, b, c, d) in ((X0 - 0.5, X1 + 0.5, Z1 - 1.5, Z1 + 0.5), (X0 - 0.5, X1 + 0.5, Z0 - 0.5, Z0 + 1.5),
                         (X0 - 0.5, X0 + 1.5, Z0 + 1.5, Z1 - 1.5), (X1 - 1.5, X1 + 0.5, Z0 + 1.5, Z1 - 1.5)):
        k.box(f, "Coping", (a, c0, c), (b, c1, d), "trim_green", studs=True, solid=True)
