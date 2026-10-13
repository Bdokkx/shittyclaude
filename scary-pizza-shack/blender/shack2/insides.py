"""Filling the cupboards and drawers: what a station keeps behind its doors, set against the
back of each level so the front stays free for a Stash (an item spawn place, opens.py)."""
import zlib

import numpy as np

import spsgeo as G
from spsgeo import CF

from . import counters as C, props_insides  # noqa: F401  (registers the props)
from .kit import PROPS
from .opens import stash
from .st_common import board

# what a station of each kind keeps, per level: (bottom, above the shelf)
CUPBOARD = {
    "kitchen": (["LiddedPot", "FryPans", "SheetTrays", "Tins", "PlateStack"], ["PlateStack", "Tins", "Rags", "SheetTrays"]),
    "cleaning": (["Bucket", "BleachJug", "SprayBottle", "Rags"], ["Rags", "SprayBottle", "Tins"]),
    "front": (["Carton", "Tins", "Rags"], ["Carton", "Rags", "PlateStack"]),
    "office": (["ToolBox", "Carton", "LunchBox"], ["Carton", "Rags"]),
}
DRAWER = {
    "kitchen": ["CutleryTray", "Utensils", "Spatulas"],
    "cleaning": ["Odds", "Pens", "Odds"],
    "front": ["Paperwork", "Odds", "Pens"],
    "office": ["Paperwork", "Pens", "Odds"],
}
STASH_W = 1.0                # the clear space a cupboard Stash wants (width and depth)
GAP = 0.15

_DIMS = {}


def dims(kind):
    """(width, height, depth) of a prop in its own space, and its bbox centre (x, z)."""
    if kind not in _DIMS:
        g = G.Geo()
        for _, _, geo, *rest in PROPS[kind](np.random.default_rng(1)):
            g.add(geo)
        lo, hi = g.bbox()
        _DIMS[kind] = (hi - lo, ((lo[0] + hi[0]) / 2, lo[1], (lo[2] + hi[2]) / 2))
    return _DIMS[kind]


def _rng(*keys):
    return np.random.default_rng(zlib.crc32(repr(keys).encode()))


def default_drawers(stock, n, station):
    pool = DRAWER.get(stock, DRAWER["kitchen"])
    r = _rng(station, stock, n)
    off = int(r.integers(len(pool)))
    return [pool[(off + j) % len(pool)] for j in range(n)]


def _level_items(want, pool, r, width, height, depth):
    """The kinds for one level: what the station asked for, or picks from its pool, that fit."""
    out, used = [], 0.0
    cands = list(want) if want is not None else [pool[i] for i in r.permutation(len(pool))]
    for kind in cands:
        (sx, sy, sz), _ = dims(kind)
        turn = False
        if sz > depth or sy > height:
            if sx <= depth and sz <= width - used and sy <= height:
                turn = True
            else:
                continue
        wd = sz if turn else sx
        if used + wd + (GAP if out else 0.0) > width:
            continue
        out.append((kind, turn))
        used += wd + (GAP if len(out) > 1 else 0.0)
        if want is None and used > width * 0.6:
            break
    return out


def fill_cupboard(k, q, doors):
    """Stand the station's things along the back of each level of a cupboard section, and a
    Stash at the front of the bottom level (or beside the things when there is no depth)."""
    w, m = q["w"], q["m"]
    s = C.sgn(w)
    ua, ub = q["ia"], q["ib"]
    d_back, d_front = C.PANEL + 0.05, q["d"] - 0.35
    if q["shelf_y"] is None:
        levels = [(0.6 + C.PANEL, q["y_body"] - C.PANEL - 0.05)]
    else:
        levels = [(0.6 + C.PANEL, q["shelf_y"] - C.PANEL / 2 - 0.05),
                  (q["shelf_y"] + C.PANEL / 2, q["y_body"] - C.PANEL - 0.05)]
    want = q["insides"]
    split = None
    if want is not None:
        want = list(want)
        split = want.index("|") if "|" in want else len(want)
    bottom_pool, top_pool = CUPBOARD.get(q["stock"], CUPBOARD["kitchen"])
    r = _rng(m.name, round(ua, 2), w)
    stash_done = False
    for li, (y0, y1) in enumerate(levels):
        lw = None if want is None else (want[:split] if li == 0 else want[split + 1:])
        pool = bottom_pool if li == 0 else top_pool
        items = _level_items(lw, pool, r, ub - ua - 2 * GAP, y1 - y0, d_front - d_back)
        u = ua + GAP
        deepest = 0.0
        for kind, turn in items:
            (sx, sy, sz), (cx, _, cz) = dims(kind)
            wd, dp = (sz, sx) if turn else (sx, sz)
            uc = u + wd / 2
            dc = d_back + dp / 2
            R = G.ry(90) if turn else np.eye(3)
            jit = G.ry(float(r.uniform(-4, 4)))
            # place so the prop's bbox centre lands on (uc, dc)
            off = (R @ np.array((cx, 0.0, cz)))
            frame = C.wcf(w, uc, y0, dc) * CF(R=jit) * CF(-off, R)
            k.prop(m, kind, frame, name=kind)
            u += wd + GAP
            deepest = max(deepest, dp)
        if li == 0 and not stash_done:
            free_d = d_front - (d_back + deepest)
            if free_d >= STASH_W:
                sw = min(ub - ua - 2 * GAP, 2.0)
                su, sd = (ua + ub) / 2, d_front - free_d / 2
                size = (sw, y1 - y0, free_d)
            elif ub - u - GAP >= STASH_W:
                su, sd = (u + ub) / 2, (d_back + d_front) / 2
                size = (ub - u - GAP, y1 - y0, d_front - d_back)
            else:
                continue
            front_door = min(doors, key=lambda dm: abs(_door_u(dm, w) - su))
            stash(k, m, CF(C.wpt(w, su, y0, sd), G.facing(C.facing_room(w))), size, behind=front_door.name)
            stash_done = True
    if q.get("note"):
        dm = doors[0]
        leaf = dm.get("Leaf")
        lf = leaf.p["cf"]
        board(k, dm, (min(1.2, _leaf_w(dm) - 0.6), 0.7, 0.15), lf * CF((0.0, 0.6, -0.19)), "paper",
              text=q["note"], text_color=(40, 34, 30), name="Note", font="Arcade")


def _door_u(dm, w):
    p = dm.get("Leaf").p["cf"].p
    return p[0] if w in ("N", "S") else p[2]


def _leaf_w(dm):
    return dm.get("Leaf").p["size"][0]


BADGES = ("KEV", "DONNA", "SAM\nTRAINEE", "PAPA")


def fill_drawer(k, op, floor, inside, want, w, stock="office"):
    """Lay the drawer's thing at the back of its box and put a Stash in front of it."""
    iw, ih, idp = inside
    used_d = 0.0
    if want == "Badges":
        cols = max(1, int((iw - 0.1) // 0.75))
        rows = int(np.ceil(len(BADGES) / cols))
        for i, txt in enumerate(BADGES):
            cx = (i % cols - (cols - 1) / 2) * 0.75
            cz = -idp + 0.3 + 0.45 * (i // cols)
            board(k, op, (0.65, 0.35, 0.15), floor * CF((cx, 0.075, cz), G.rx(90)), "white" if i != 3 else "red",
                  text=txt, text_color=(30, 30, 30) if i != 3 else (255, 240, 220), name="Badge", font="Arcade")
        used_d = 0.45 * rows + 0.15
    elif want is not None:
        for kind in [want] + (["Spatulas", "Odds"] if stock == "kitchen" else ["Odds", "Pens"]):
            (sx, sy, sz), (cx, _, cz) = dims(kind)
            if sy > ih:
                continue
            turn = None
            if sx <= iw and sz <= idp - 0.8:
                turn = False
            elif sz <= iw and sx <= idp - 0.8:
                turn = True
            if turn is None:
                continue
            dp = sx if turn else sz
            R = G.ry(90) if turn else np.eye(3)
            off = R @ np.array((cx, 0.0, cz))
            k.prop(op, kind, floor * CF((0.0, 0.0, -idp + dp / 2 + 0.05)) * CF(-off, R), name=kind)
            used_d = dp + 0.1
            break
    free = idp - used_d
    if free >= 0.6:
        stash(k, op, floor * CF((0.0, 0.0, -free / 2), G.facing((0, 0, 1))), (iw, ih, free))
