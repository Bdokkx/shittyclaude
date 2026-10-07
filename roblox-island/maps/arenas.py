"""Rebuilt tag-game arenas for maps.rbxm (Meadow, Farm, Snow, Desert) in the stud style of the spear islands.

What the game scripts use is NOT touched (tools/export_maps.luau carries it over from the uploaded file):
  Maps/<Map> attributes (MapId, DisplayName), Markers (LineA/B, SafeA/B with the SAFE label, CatcherSpawn),
  Barriers (invisible walls + roof) and the 150 x 300 Field of 200 Tiles (only recoloured) + Trim.
Rebuilt here: Underside, Scenery and the look of the Obstacles (same collider part, size and position).

Fixed: on Farm and Desert an obstacle stood in the middle of CatcherSpawn (the catcher spawned inside it);
that one is replaced by a pair at z = +-28 on the centre line.

Local frame = the map's frame: field top at y = 0, field x +-75, z +-150, walls at x +-76 / z +-151.
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "spear"))

import autumn as A                       # noqa: E402
import buildings as Bd                   # noqa: E402
import props as P                        # noqa: E402
from core import Model, poly_contains    # noqa: E402
from terrain import greedy, noise2, slab_stack   # noqa: E402

FX, FZ = 75.0, 150.0         # field half extents
KEEP_X, KEEP_Z = 78.0, 153.0  # field + trim; nothing new may enter this box above the floor
CELL = 4.0
LEVELS = (0.0, 5.0, 10.0, 16.0)
BORDER_TOP = -0.9

THEMES = {
    "Meadow": dict(
        grass=("#6CCB4A", "#5EBE45", "#7AD155"), lip="#4FA83A", dirt=("#B07A4A", "#9A6238"),
        rock=("#B3BCF2", "#8A97E6", "#5E6BC4"), border="#C9AE78", trim="#8A6A3E",
        field=((64, 190, 96), (54, 172, 86)), safe=((98, 212, 128), (86, 200, 116)),
        hang=("#4FA83A", "#3E8F33"), sign=("#FFF6E2", "#2E7D32")),
    "Farm": dict(
        grass=("#8CBF45", "#9DBA44", "#A8C653"), lip="#6E9A35", dirt=("#A7794A", "#8E6236"),
        rock=("#C9B49A", "#A8927A", "#857060"), border="#B98552", trim="#8E5A2B",
        field=((226, 176, 72), (212, 160, 58)), safe=((240, 200, 110), (232, 189, 96)),
        hang=("#6E9A35", "#8E6236"), sign=("#FFF1D6", "#B5452B")),
    "Snow": dict(
        grass=("#F4F8FF", "#E6EEF9", "#FFFFFF"), lip="#D6E4F5", dirt=("#B8C8DE", "#A2B5CE"),
        rock=("#9AA9C4", "#7C8BA8", "#5F6D8A"), border="#C9D8EC", trim="#8EA3C2",
        field=((242, 247, 255), (228, 237, 250)), safe=((205, 228, 255), (190, 218, 250)),
        hang=("#CFEAFF", "#A9D8FF"), sign=("#FFFFFF", "#2F80ED")),
    "Desert": dict(
        grass=("#F0CF8E", "#E7C27E", "#F5D99E"), lip="#D9B06A", dirt=("#D49A5A", "#C2864A"),
        rock=("#E08A50", "#C66A3A", "#A8532E"), border="#C9965A", trim="#9C6A38",
        field=((236, 198, 128), (224, 184, 110)), safe=((246, 220, 166), (238, 208, 150)),
        hang=("#C66A3A", "#A8532E"), sign=("#FFF1D6", "#C2410C")),
}


# ------------------------------------------------------------------ helpers

def outline(hx=132.0, hz=212.0, seed=1, p=3.0, amp=0.035, n=220):
    rng = random.Random(seed)
    waves = [(k, rng.uniform(0, 6.283), amp / (1 + 0.5 * k)) for k in range(3, 9)]
    pts = []
    for i in range(n):
        a = i * 2 * math.pi / n
        c, s = math.cos(a), math.sin(a)
        rr = 1 / (abs(c / hx) ** p + abs(s / hz) ** p) ** (1 / p)
        rr *= 1 + sum(w * math.sin(k * a + ph) for k, ph, w in waves)
        pts.append((c * rr, s * rr))
    return pts


def scale(poly, f, dx=0.0, dz=0.0):
    return [(x * f + dx, z * f + dz) for x, z in poly]


def cells_in(poly, ext=(40, 60)):
    out = set()
    for i in range(-ext[0], ext[0]):
        for j in range(-ext[1], ext[1]):
            if poly_contains(poly, (i + 0.5) * CELL, (j + 0.5) * CELL):
                out.add((i, j))
    return out


def in_keep(x, z, pad=0.0):
    return abs(x) < KEEP_X + pad and abs(z) < KEEP_Z + pad


class Spots:
    def __init__(self, rim):
        self.rim, self.taken, self.rects = rim, [], [(-KEEP_X - 5, -KEEP_Z - 5, KEEP_X + 5, KEEP_Z + 5)]

    def free(self, x, z, r, edge=5.0):
        if not poly_contains(scale(self.rim, 1 - edge / 130.0), x, z):
            return False
        if any(x0 - r < x < x1 + r and z0 - r < z < z1 + r for x0, z0, x1, z1 in self.rects):
            return False
        return all(math.hypot(x - a, z - b) >= r + q for a, b, q in self.taken)

    def take(self, x, z, r, edge=5.0):
        if self.free(x, z, r, edge):
            self.taken.append((x, z, r))
            return True
        return False


# ------------------------------------------------------------------ terrain

class Ground:
    """Stepped bowl around the field: a border band right at the trim, lawn, then terraces rising outwards."""

    def __init__(self, rim, seed, pads=()):
        self.rim, self.seed = rim, seed
        self.top = {}
        for (i, j) in cells_in(rim):
            x, z = (i + 0.5) * CELL, (j + 0.5) * CELL
            if in_keep(x, z):
                continue
            dx, dz = max(0.0, abs(x) - KEEP_X), max(0.0, abs(z) - KEEP_Z)
            d = math.hypot(dx, dz)
            if d < 7:
                self.top[(i, j)] = BORDER_TOP
                continue
            raw = (d - 18) / 17 + (noise2(x, z, seed, 46) - 0.5) * 1.3
            lvl = 0 if raw < 0 else min(3, 1 + int(raw))
            self.top[(i, j)] = LEVELS[lvl]
        for x0, z0, x1, z1, h in pads:
            for c in list(self.top):
                x, z = (c[0] + 0.5) * CELL, (c[1] + 0.5) * CELL
                if x0 <= x <= x1 and z0 <= z <= z1:
                    self.top[c] = h

    def at(self, x, z):
        if in_keep(x, z):
            return 0.0
        return self.top.get((int(math.floor(x / CELL)), int(math.floor(z / CELL))))

    def build(self, m, th):
        with m.ctx(stage="terrain", folder="Underside", collide=False, shadow=True):
            tops = {}
            for c, h in self.top.items():
                if h == BORDER_TOP:
                    tops[c] = (h, th["border"])
                else:
                    n = noise2(c[0] * 4, c[1] * 4, self.seed + 7, 44)            # broad patches merge well
                    tops[c] = (h, th["grass"][1] if n > 0.6 else th["grass"][0])
            for i0, j0, i1, j1, (h, col) in greedy(tops):
                m.span((i0 * CELL, h - 1.2 if h > BORDER_TOP else -1.6, j0 * CELL), ((i1 + 1) * CELL, h, (j1 + 1) * CELL), col)
            lv = {c: h for c, h in self.top.items()}
            for i0, j0, i1, j1, h in greedy(lv):
                x0, z0, x1, z1 = i0 * CELL, j0 * CELL, (i1 + 1) * CELL, (j1 + 1) * CELL
                if h > BORDER_TOP:
                    m.span((x0, h - 3.2, z0), (x1, h - 1.2, z1), th["dirt"][0])
                    if h - 3.2 > -6:
                        m.span((x0, -6, z0), (x1, h - 3.2, z1), th["rock"][0] if h > 6 else th["dirt"][1])
                else:
                    m.span((x0, -6, z0), (x1, -1.6, z1), th["dirt"][1])


def underside(m, th, rim, seed):
    """Tapering voxel rock body under the whole island (replaces the plain Tier slabs)."""
    rock = th["rock"]
    layers = [(-6, -14, 1.0, 0), (-14, -24, 0.9, 0), (-24, -36, 0.76, 1), (-36, -50, 0.6, 1),
              (-50, -66, 0.44, 1), (-66, -82, 0.29, 2), (-82, -98, 0.16, 2)]
    with m.ctx(stage="terrain", folder="Underside", collide=False, shadow=False):
        for k, (y1, y0, f, band) in enumerate(layers):
            poly = scale(rim, f, dx=math.sin(k * 1.3) * 3.0, dz=math.cos(k * 0.9) * 4.0)
            cs = cells_in(poly) or {(0, 0)}
            keyed = {c: rock[band] if k % 2 == 0 else rock[min(2, band + 1)] for c in cs}   # one colour per layer
            for i0, j0, i1, j1, col in greedy(keyed):
                m.span((i0 * CELL, y0, j0 * CELL), ((i1 + 1) * CELL, y1, (j1 + 1) * CELL), col)
        m.span((-4, -112, -6), (4, -98, 6), rock[2])
        # chunky tilted slabs around the cliff so the sides are not just steps
        rng = random.Random(seed + 21)
        n = len(rim)
        for k, (y_mid, f, step) in enumerate(((-9, 1.0, 5), (-22, 0.88, 7), (-40, 0.64, 9), (-62, 0.4, 12))):
            for i in range(0, n, step):
                x, z = rim[(i + k * 2) % n]
                a = math.atan2(z, x)
                rr = math.hypot(x, z) * f
                w = rng.uniform(10, 18) * (1.0 if k < 2 else 0.8)
                with m.at((math.cos(a) * rr, y_mid + rng.uniform(-2, 2), math.sin(a) * rr),
                          ry=-math.degrees(a) + 90 + rng.uniform(-12, 12)):
                    m.box((0, 0, 0), (w, rng.uniform(4.5, 6.0), 5.0), rock[min(2, k // 2 + rng.choice((0, 0, 1)))],
                          rx=rng.uniform(6, 14), rz=rng.uniform(-8, 8))


def hanging(m, th, rim, g, seed, icicles=False):
    rng = random.Random(seed + 33)
    with m.ctx(stage="props", folder="Scenery", tag="Hanging:0", collide=False, shadow=False):
        for i in range(0, len(rim), 3):
            x, z = rim[i]
            a = math.atan2(z, x)
            r = math.hypot(x, z) - 1.0
            px, pz = math.cos(a) * r, math.sin(a) * r
            L = rng.uniform(3, 10) if not icicles else rng.uniform(2, 6)
            col = rng.choice(th["hang"])
            if icicles:
                m.box((px, -6.0 - L / 2, pz), (1.0, L, 1.0), col, mat="Glass", ry=rng.uniform(0, 90), transparency=0.15)
                m.box((px, -6.2 - L, pz), (0.5, 1.0, 0.5), col, mat="Glass", ry=45, transparency=0.15)
            else:
                m.box((px, -6.0 - L / 2, pz), (0.6, L, 0.6), col, ry=-math.degrees(a))
                if rng.random() < 0.4:
                    m.box((px, -6.0 - L, pz), (1.3, 1.1, 1.3), col)


def rock_cluster(m, seed, cols, s=1.0):
    rng = random.Random(seed)
    m.box((0, 1.2 * s, 0), (4.2 * s, 2.6 * s, 3.6 * s), cols[1], ry=rng.uniform(0, 90), rx=rng.uniform(-6, 6))
    m.box((2.2 * s, 0.8 * s, 1.0 * s), (2.4 * s, 1.8 * s, 2.2 * s), cols[0], ry=rng.uniform(0, 90))
    m.box((-1.8 * s, 0.6 * s, -1.4 * s), (1.8 * s, 1.2 * s, 1.6 * s), cols[2], ry=rng.uniform(0, 90))


def area_sign(m, text, th, z, flip, k):
    """Big name sign behind a safe zone, facing the field."""
    with m.ctx(stage="props", folder="Scenery", tag="AreaSign:%d" % next(k), collide=False):
        with m.at((0, 0, z), ry=180 if flip else 0):
            for x in (-14, 14):
                m.box((x, 7, 0.8), (1.6, 14, 1.6), "#6B4226")
                m.box((x, 0.6, 0.8), (2.6, 1.2, 2.6), "#8E89A0")
            m.box((0, 11.5, 0.2), (34, 8.4, 1.0), "#6B4226")
            board = m.box((0, 11.5, -0.4), (32, 6.8, 0.4), th["sign"][0])
            m.text(board, text, th["sign"][1], "Front")


# ------------------------------------------------------------------ field colours

def field_colors(th):
    out = {}
    xs = [-67.5 + 15 * i for i in range(10)]
    zs = [-142.5 + 15 * j for j in range(20)]
    for j, z in enumerate(zs):
        for i, x in enumerate(xs):
            if abs(z) > 125:
                c = th["safe"][(i + j) % 2]                     # safe ends: checker
            else:
                c = th["field"][j % 2]                          # play area: mowed stripes
            out["%.1f,%.1f" % (x, z)] = "#%02X%02X%02X" % c
    return out


# ------------------------------------------------------------------ scatter

def scatter(m, g, sp, k, seed, trees, n_trees, extras):
    """trees: [(fn, weight)]; extras: [(fn(m, seed), radius, count, tag)] placed on free lawn/terraces."""
    rng = random.Random(seed)
    tot = sum(w for _, w in trees)
    placed = 0
    for _ in range(4000):
        if placed >= n_trees:
            break
        x, z = rng.uniform(-135, 135), rng.uniform(-215, 215)
        h = g.at(x, z)
        if h is None or h == BORDER_TOP or not sp.take(x, z, 5.0):
            continue
        r = rng.uniform(0, tot)
        for fn, w in trees:
            r -= w
            if r <= 0:
                break
        with m.ctx(stage="props", folder="Scenery", tag="Tree:%d" % next(k), collide=False):
            with m.at((x, h, z), ry=rng.uniform(0, 360)):
                fn(m, rng.choice((0, 1, 1, 2)), rng.randint(0, 99999))
        placed += 1
    for fn, rad, count, tag in extras:
        done = 0
        for _ in range(count * 40):
            if done >= count:
                break
            x, z = rng.uniform(-135, 135), rng.uniform(-215, 215)
            h = g.at(x, z)
            if h is None or h == BORDER_TOP or not sp.take(x, z, rad, edge=3.0):
                continue
            with m.ctx(stage="props", folder="Scenery", tag="%s:%d" % (tag, next(k)), collide=False):
                with m.at((x, h, z), ry=rng.uniform(0, 360)):
                    fn(m, rng.randint(0, 99999))
            done += 1


# ------------------------------------------------------------------ obstacles (collider part first)

def obstacle(m, name, k, pos, size, color, ry=0.0):
    """Start an obstacle: the collider part (same name/size/position as the original)."""
    tag = "%s:%d" % (name, next(k))
    with m.ctx(stage="obstacle", folder="Obstacles", tag=tag, collide=True, shadow=True):
        p = m.box(pos, size, color, ry=ry, name=name)
    return tag


def hay_obstacles(m, k):
    for x, z, ry in ((-38, -55, 0), (38, -55, 0), (-38, 55, 0), (38, 55, 0), (0, -28, 90), (0, 28, 90)):
        tag = obstacle(m, "HayBale", k, (x, 2.25, z), (7, 4.5, 4.5), "#F2C94C", ry=ry)
        with m.ctx(stage="obstacle", folder="Obstacles", tag=tag, collide=False, shadow=False):
            with m.at((x, 0, z), ry=ry):
                m.box((0, 2.25, 0), (6.4, 4.6, 3.9), "#E3B53E")
                for sx in (-2.0, 2.0):
                    m.box((sx, 2.25, 0), (0.4, 4.7, 4.7), "#8A5A2B", name="Strap")
                rng = random.Random(x * 7 + z)
                for _ in range(5):
                    m.box((rng.uniform(-3, 3), 4.6, rng.uniform(-1.8, 1.8)), (0.15, 0.15, 1.4), "#F7D774",
                          ry=rng.uniform(0, 180))
                if abs(x) > 1:
                    with m.at((rng.uniform(-1.5, 1.5), 4.5, 0)):
                        A.pumpkin(m, 0.7, int(x + z), carved=False, light=False)


def snow_obstacles(m, k):
    for x, z in ((-40, -50), (40, -50), (-40, 50), (40, 50)):
        tag = obstacle(m, "SnowWall", k, (x, 1.6, z), (16, 3.2, 3), "#FFFFFF")
        with m.ctx(stage="obstacle", folder="Obstacles", tag=tag, collide=False, shadow=False):
            with m.at((x, 0, z)):
                for row in range(2):                                # snow bricks
                    off = 0 if row == 0 else 1.6
                    xx = -8 + off
                    while xx < 8 - 0.4:
                        w = min(3.2, 8 - xx)
                        m.box((xx + w / 2, 0.8 + row * 1.6, -1.52), (w - 0.25, 1.35, 0.1), "#EEF4FC")
                        m.box((xx + w / 2, 0.8 + row * 1.6, 1.52), (w - 0.25, 1.35, 0.1), "#EEF4FC")
                        xx += 3.2
                m.box((0, 3.6, 0), (15, 0.8, 2.6), "#E2EBF8", name="Top")
                for sx in (-6.5, -2, 3.5, 6.8):
                    m.box((sx, 4.1, 0), (1.6, 0.6, 1.8), "#FFFFFF", ry=sx * 13)
                m.box((-7.2, 4.0, 0.9), (0.6, 1.4, 0.6), "#A9D8FF", mat="Glass", transparency=0.2)
                for i, (sx, sz) in enumerate(((5, 2.6), (6.4, 2.4), (5.8, 3.4))):   # snowball pile
                    m.box((sx, 0.6 + (0.9 if i == 2 else 0), sz), (1.3, 1.3, 1.3), "#FFFFFF", ry=30 * i)


def desert_obstacles(m, k):
    for x, z in ((-42, -52), (42, 52)):
        tag = obstacle(m, "Cactus", k, (x, 5.2, z), (3.0, 10.4, 3.0), "#3E9B4F", ry=30)
        with m.ctx(stage="obstacle", folder="Obstacles", tag=tag, collide=False, shadow=False):
            with m.at((x, 0, z), ry=30):
                saguaro_detail(m, 10.4)
    for x, z in ((42, -52), (-42, 52), (0, -28), (0, 28)):
        tag = obstacle(m, "Crate", k, (x, 2.5, z), (5, 5, 5), "#B5793F", ry=15)
        with m.ctx(stage="obstacle", folder="Obstacles", tag=tag, collide=False, shadow=False):
            with m.at((x, 0, z), ry=15):
                for y in (0.45, 4.55):
                    m.box((0, y, 0), (5.3, 0.7, 5.3), "#8A5A2B", name="Band")
                for s in (-1, 1):
                    m.box((s * 2.56, 2.5, 0), (0.2, 4.0, 0.7), "#8A5A2B", ry=0, rx=45)
                    m.box((0, 2.5, s * 2.56), (0.7, 4.0, 0.2), "#8A5A2B", rz=45)
                m.box((0, 5.15, 0), (2.4, 0.3, 1.6), "#D9B77E")


def saguaro_detail(m, h):
    """Arms, ribs and a flower on a cactus trunk of height h (trunk itself is the collider)."""
    g, g2 = "#45A857", "#36894A"
    for s, (y, up) in ((1, (0.48, 3.4)), (-1, (0.32, 3.0))):
        m.box((s * 2.4, h * y, 0), (2.4, 1.6, 1.6), g)
        m.box((s * 3.3, h * y + up / 2 + 0.4, 0), (1.6, up + 0.8, 1.6), g)
        m.box((s * 3.3, h * y + up + 0.9, 0), (1.2, 0.4, 1.2), g2)
    for a in (0, 90):
        m.box((0, h / 2, 0), (3.2, h - 0.6, 0.35), g2, ry=a)
    m.box((0, h + 0.25, 0), (1.4, 0.6, 1.4), "#FF8FC7", ry=45)
    m.box((0, h + 0.55, 0), (0.6, 0.3, 0.6), "#FFD447")


# ------------------------------------------------------------------ theme props

def windmill(m):
    m.octagon(4.0, 4.4, 8.0, "#F1E3C2")
    m.octagon(10.5, 3.6, 5.0, "#F1E3C2")
    m.octagon(13.6, 3.9, 1.2, "#B5523B")
    m.octagon(15.0, 2.8, 1.6, "#B5523B")
    m.box((0, 16.6, 0), (1.6, 1.6, 1.6), "#B5523B")
    m.box((0, 2.6, -4.2), (2.4, 5.2, 0.6), "#6B4226")
    with m.at((0, 13.0, -4.6)):
        m.box((0, 0, 0), (1.4, 1.4, 1.4), "#5A5F6E")
        for a in (0, 90, 180, 270):
            with m.at((0, 0, -0.6), rz=a + 20):
                m.box((0, 5.0, 0), (0.6, 9.0, 0.4), "#6B4226")
                m.box((0.9, 6.0, -0.1), (1.6, 6.5, 0.2), "#FFF7EC")


def pond(m, r=10.0):
    m.octagon(0.02, r + 1.4, 0.2, "#B9B4C8")
    m.octagon(0.06, r, 0.2, "#4FC3F7")
    rng = random.Random(int(r * 10))
    for i in range(5):
        a = rng.uniform(0, 6.28)
        rr = rng.uniform(1.5, r - 2)
        m.box((math.cos(a) * rr, 0.2, math.sin(a) * rr), (1.8, 0.1, 1.8), "#4FA83A", ry=rng.uniform(0, 90))
    m.box((r * 0.4, 0.3, 0.2), (0.6, 0.3, 0.6), "#FF8FC7", ry=45)


def barn(m):
    W, D, H = 18.0, 14.0, 9.0
    red, white = "#B5452B", "#FFF7EC"
    m.box((0, 0.4, 0), (W + 1.2, 0.8, D + 1.2), "#8E89A0")
    Bd.plank_wall(m, -W / 2, W / 2, 0.8, H, -D / 2, -D / 2 + 0.6, tones=(red, "#A33D26"), vertical=True)
    Bd.plank_wall(m, -W / 2, W / 2, 0.8, H, D / 2 - 0.6, D / 2, tones=(red, "#A33D26"), vertical=True)
    Bd.plank_wall(m, -W / 2, -W / 2 + 0.6, 0.8, H, -D / 2, D / 2, tones=(red, "#A33D26"), vertical=True)
    Bd.plank_wall(m, W / 2 - 0.6, W / 2, 0.8, H, -D / 2, D / 2, tones=(red, "#A33D26"), vertical=True)
    for x in (-W / 2, W / 2):                                    # white corner trim
        for z in (-D / 2, D / 2):
            m.box((x, H / 2 + 0.4, z), (0.9, H, 0.9), white)
    m.box((0, H + 0.2, -D / 2 - 0.1), (W + 0.6, 0.6, 0.6), white)
    # big doors with the white X
    m.box((0, 3.6, -D / 2 - 0.3), (8.0, 6.4, 0.4), "#8E2E1C")
    for s in (-1, 1):
        m.box((s * 2.0, 3.6, -D / 2 - 0.55), (0.5, 7.2, 0.2), white, rz=s * 50)
    m.box((0, 3.6, -D / 2 - 0.5), (8.4, 0.5, 0.2), white)
    m.box((0, 6.95, -D / 2 - 0.5), (8.6, 0.5, 0.2), white)
    m.box((0, 11.5, -D / 2 - 0.4), (3.0, 2.2, 0.3), "#3A2A1E")                   # hay loft
    m.box((0, 11.5, -D / 2 - 0.5), (3.4, 2.6, 0.1), white)
    with m.at((0, 0, 0), ry=90):
        Bd.gable_roof(m, D, W, H + 0.2, 38, "#5A5F6E", white, overhang=1.2, gable=red)


def silo(m):
    m.octagon(7.0, 3.6, 14.0, "#C9CED8")
    for y in (3, 7, 11):
        m.octagon(y, 3.75, 0.4, "#8C93A6")
    m.octagon(14.6, 3.2, 1.2, "#B5452B")
    m.octagon(15.6, 2.0, 1.0, "#B5452B")
    m.box((0, 16.4, 0), (1.0, 1.0, 1.0), "#B5452B")


def tractor(m):
    m.box((0, 2.2, 0), (3.4, 2.0, 6.0), "#3FA34D")
    m.box((0, 4.2, 1.2), (3.0, 2.6, 2.6), "#3FA34D")
    m.box((0, 4.6, 1.2), (2.6, 1.6, 2.7), "#BDE7FF", mat="Glass", transparency=0.3)
    m.box((0, 5.6, 1.2), (3.4, 0.3, 3.0), "#2E7D3A")
    m.box((0.9, 4.6, -1.8), (0.5, 2.6, 0.5), "#5A5F6E")
    for x in (-2.0, 2.0):
        m.box((x, 2.2, 1.6), (1.2, 4.0, 4.0), "#2A2A2A")
        m.box((x * 1.03, 2.2, 1.6), (0.3, 2.2, 2.2), "#FFD447")
        m.box((x * 0.95, 1.2, -2.0), (1.0, 2.2, 2.2), "#2A2A2A")


def corn_patch(m, seed, w=14, d=10):
    rng = random.Random(seed)
    m.box((0, 0.15, 0), (w, 0.3, d), A.SOIL[0])
    z = -d / 2 + 1.2
    while z < d / 2 - 0.8:
        x = -w / 2 + 1.0
        while x < w / 2 - 0.8:
            with m.at((x + rng.uniform(-0.3, 0.3), 0.3, z)):
                A.corn_stalk(m, rng.randint(0, 9999))
            x += 3.0
        z += 3.2


def pumpkin_patch(m, seed, w=12, d=9):
    rng = random.Random(seed)
    m.box((0, 0.15, 0), (w, 0.3, d), A.SOIL[0])
    for z in (-d / 4, d / 4):
        m.box((0, 0.45, z), (w - 1.5, 0.25, 0.3), A.VINE)
        x = -w / 2 + 1.8
        while x < w / 2 - 1.2:
            with m.at((x, 0.3, z + rng.uniform(-0.5, 0.5)), ry=rng.uniform(0, 360)):
                A.pumpkin(m, rng.uniform(0.6, 1.0), rng.randint(0, 9999), light=False)
            x += rng.uniform(2.6, 3.4)


def fence_square(m, w, d, gate=True):
    pts = [(-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2), (-w / 2, -d / 2)]
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        if gate and i == 0:
            Bd.rail_line(m, a, (-1.6, -d / 2), 0.0)
            Bd.rail_line(m, (1.6, -d / 2), b, 0.0)
        else:
            Bd.rail_line(m, a, b, 0.0)


def cabin(m):
    W, D, H = 14.0, 11.0, 7.0
    logs = ("#8B5A33", "#74492A")
    m.box((0, 0.4, 0), (W + 1, 0.8, D + 1), "#7C8BA8")
    y = 0.8
    i = 0
    while y < H:
        for z in (-D / 2, D / 2):
            m.box((0, y + 0.5, z), (W + 1.2, 1.0, 1.0), logs[i % 2])
        for x in (-W / 2, W / 2):
            m.box((x, y + 0.5, 0), (1.0, 1.0, D + 1.2), logs[(i + 1) % 2])
        y += 1.0
        i += 1
    m.box((0, 2.9, -D / 2 - 0.4), (3.0, 4.2, 0.3), "#5A3A22")
    for x in (-4.0, 4.0):
        m.box((x, 4.0, -D / 2 - 0.45), (2.6, 2.2, 0.2), "#FFE08A", mat="Neon")
        m.box((x, 4.0, -D / 2 - 0.55), (3.0, 0.3, 0.2), "#5A3A22")
    with m.at((0, 0, 0)):
        Bd.gable_roof(m, W, D, H + 0.8, 36, "#5A3A22", "#3A2A1E", overhang=1.2, gable=logs[0])
        top = H + 0.8 + (D / 2) * math.tan(math.radians(36))
        for s in (-1, 1):                                          # snow on both roof slopes
            run = D / 2 + 1.2
            with m.at((0, H + 0.8 + (D / 2) * math.tan(math.radians(36)) - (run / 2) * math.tan(math.radians(36)) + 0.9,
                       s * run / 2), rx=s * 36):
                m.box((0, 0, 0), (W + 2.6, 0.6, run / math.cos(math.radians(36)) - 0.4), "#FFFFFF")
    m.box((W / 2 - 2.5, top + 1.5, 2.0), (2.0, 5.0, 2.0), "#8E89A0")
    m.box((W / 2 - 2.5, top + 4.2, 2.0), (2.4, 0.5, 2.4), "#FFFFFF")


def snowman(m, seed):
    rng = random.Random(seed)
    m.box((0, 1.6, 0), (3.4, 3.2, 3.4), "#FFFFFF", ry=rng.uniform(0, 45))
    m.box((0, 4.2, 0), (2.6, 2.4, 2.6), "#FFFFFF", ry=rng.uniform(0, 45))
    m.box((0, 6.2, 0), (1.9, 1.8, 1.9), "#FFFFFF")
    m.box((0, 6.2, -1.2), (0.35, 0.35, 0.9), "#FF8A3D")
    for x in (-0.45, 0.45):
        m.box((x, 6.6, -0.96), (0.3, 0.3, 0.05), "#1E2230")
    m.box((0, 5.2, 0), (2.8, 0.5, 2.8), "#E8403A")
    m.box((1.1, 4.6, -1.3), (0.6, 1.6, 0.4), "#E8403A")
    m.box((0, 7.25, 0), (2.4, 0.25, 2.4), "#1E2230")
    m.box((0, 8.0, 0), (1.5, 1.4, 1.5), "#1E2230")
    for s in (-1, 1):
        m.beam((s * 1.2, 4.4, 0), (s * 3.2, 5.8, 0), 0.25, "#6B4226")


def ice_crystals(m, seed):
    rng = random.Random(seed)
    for i in range(rng.randint(3, 5)):
        a = rng.uniform(0, 6.28)
        r = rng.uniform(0, 1.6)
        h = rng.uniform(3, 8)
        m.box((math.cos(a) * r, h / 2 - 0.3, math.sin(a) * r), (1.3, h, 1.3), rng.choice(("#A9D8FF", "#CFEAFF", "#7FC4FF")),
              mat="Glass", transparency=0.15, ry=rng.uniform(0, 90), rx=rng.uniform(-14, 14), rz=rng.uniform(-14, 14))


def frozen_pond(m, r=11.0):
    m.octagon(0.02, r + 1.2, 0.2, "#FFFFFF")
    m.octagon(0.06, r, 0.2, "#BFE4FF")
    for i, (x, z, w) in enumerate(((-3, 2, 5), (2, -3, 4), (4, 3, 3))):
        m.box((x, 0.18, z), (w, 0.05, 0.2), "#E8F6FF", ry=40 * i)


def mesa(m, seed, h, w, th):
    slab_stack(m, seed, h, w, (th["rock"][0], th["rock"][1], th["rock"][2]), cap=th["grass"][0], cap_strip=th["lip"],
               taper=0.8, tilt=(2, 6))


def ufo(m):
    """Crashed saucer half buried in a scorched trench, tilted, with a cracked glass dome."""
    m.box((0, 0.05, 6), (8, 0.15, 18), "#8A6A4A")                         # trench
    for i in range(6):
        m.box(((-1) ** i * 4.5, 0.6, 1 + 2.6 * i), (2.4, 1.2, 2.0), "#C2864A", ry=20 * i)
    with m.at((0, 3.0, -2), rx=-16, rz=12):
        m.octagon(0, 9.0, 1.6, "#8C93A6", name="Disc")
        m.octagon(-1.2, 7.0, 1.2, "#5A5F6E")
        m.octagon(1.3, 6.0, 1.2, "#B4BCCB")
        m.octagon(2.8, 3.8, 2.4, "#7FE3FF", mat="Glass", transparency=0.25)
        for a in range(0, 360, 45):
            x, z = math.cos(math.radians(a)) * 8.4, math.sin(math.radians(a)) * 8.4
            m.box((x, 0.2, z), (1.0, 0.7, 1.0), "#9BE34A" if a % 90 else "#FF5A5A", mat="Neon")
    for i, (x, z, s) in enumerate(((10, 4, 1.4), (-9, 8, 1.0), (6, 12, 0.8), (-6, -10, 1.2))):   # debris
        m.box((x, 0.4 * s, z), (2.2 * s, 0.8 * s, 1.4 * s), "#8C93A6", ry=37 * i, rz=12)


def bones(m, seed):
    rng = random.Random(seed)
    m.box((0, 0.6, 0), (1.6, 1.2, 1.8), "#F2EFE6")                        # skull
    for x in (-0.4, 0.4):
        m.box((x, 0.75, -0.91), (0.4, 0.4, 0.05), "#2A1E14")
    for i in range(3):
        m.box((rng.uniform(1.5, 3), 0.2, rng.uniform(-1.5, 1.5)), (2.4, 0.4, 0.4), "#F2EFE6", ry=rng.uniform(0, 180))


def tumbleweed(m, seed):
    rng = random.Random(seed)
    for i in range(4):
        m.box((0, 1.1, 0), (2.0, 2.0, 2.0), rng.choice(("#B8955F", "#A6824E")), rx=rng.uniform(0, 90),
              ry=rng.uniform(0, 90), rz=rng.uniform(0, 90), transparency=0.0)


def desert_plant(m, seed):
    rng = random.Random(seed)
    h = rng.uniform(5, 9)
    m.box((0, h / 2, 0), (2.0, h, 2.0), "#3E9B4F")
    saguaro_detail_small(m, h, rng)


def saguaro_detail_small(m, h, rng):
    for s in (-1, 1):
        if rng.random() < 0.8:
            y = h * rng.uniform(0.35, 0.55)
            up = rng.uniform(1.6, 3.0)
            m.box((s * 1.6, y, 0), (1.4, 1.2, 1.2), "#45A857")
            m.box((s * 2.2, y + up / 2 + 0.3, 0), (1.2, up + 0.6, 1.2), "#45A857")
    if rng.random() < 0.5:
        m.box((0, h + 0.2, 0), (1.0, 0.4, 1.0), "#FF8FC7", ry=45)


def desert_rock(m, seed):
    rock_cluster(m, seed, ("#E08A50", "#C66A3A", "#A8532E"), s=random.Random(seed).uniform(0.8, 1.5))


def picnic(m, seed):
    m.box((0, 2.0, 0), (6.0, 0.4, 3.0), "#9A6238")
    for x in (-2.4, 2.4):
        m.box((x, 1.0, 0), (0.5, 2.0, 2.4), "#6B4226")
    for z in (-2.4, 2.4):
        m.box((0, 1.1, z), (6.0, 0.3, 1.0), "#9A6238")
        m.box((0, 0.5, z), (0.5, 1.0, 0.8), "#6B4226")
    m.box((0, 2.25, 0), (3.0, 0.1, 3.0), "#FF5A5A")
    m.box((1.0, 2.6, 0.4), (1.0, 0.6, 0.8), "#C8A06A")


# ------------------------------------------------------------------ the four maps

def build(name):
    th = THEMES[name]
    seed = {"Meadow": 11, "Farm": 23, "Snow": 37, "Desert": 41}[name]
    m = Model(name)
    k = iter(range(1, 1000000))
    rim = outline(seed=seed)
    pads = {
        "Meadow": [(-120, -80, -100, -52, 10.0), (96, 40, 122, 70, 0.0)],
        "Farm": [(-128, 20, -96, 64, 0.0), (-128, -40, -104, -20, 0.0), (88, -110, 124, -30, 0.0), (90, 40, 122, 80, 0.0)],
        "Snow": [(96, -60, 124, -20, 5.0), (-122, 30, -96, 66, 0.0)],
        "Desert": [(-124, 50, -88, 96, 0.0)],
    }[name]
    g = Ground(rim, seed, pads)
    sp = Spots(rim)
    g.build(m, th)
    underside(m, th, rim, seed)
    hanging(m, th, rim, g, seed, icicles=(name == "Snow"))
    for z, flip in ((182.0, False), (-182.0, True)):
        sp.rects.append((-19, z - 4, 19, z + 4))
        area_sign(m, {"Meadow": "GREEN MEADOW", "Farm": "HARVEST FARM", "Snow": "SNOWY PEAKS",
                      "Desert": "DESERT CRASH"}[name], th, z, flip, k)

    def place(tag, x, z, r, fn, ry=0.0, collide=False):
        h = g.at(x, z)
        sp.taken.append((x, z, r))
        with m.ctx(stage="props", folder="Scenery", tag="%s:%d" % (tag, next(k)), collide=collide):
            with m.at((x, h if h is not None else 0.0, z), ry=ry):
                fn(m)

    if name == "Meadow":
        place("Windmill", -110, -66, 9, windmill, ry=-90)
        place("Pond", 109, 55, 13, lambda m_: pond(m_, 10.0))
        for i, (x, z) in enumerate(((100, -40), (-100, 40), (104, 100))):
            place("Picnic", x, z, 4.5, lambda m_, i=i: picnic(m_, i), ry=90)
        trees = [(P.oak, 4), (P.birch, 2), (P.apple, 2), (P.cherry, 1.5), (P.poplar, 1.5), (P.pine, 1)]
        extras = [(lambda m_, s: P.bush(m_, s), 3.2, 40, "Bush"),
                  (lambda m_, s: P.flowers(m_, s), 2.2, 30, "Flowers"),
                  (lambda m_, s: P.tuft_cluster(m_, s, flower=random.Random(s).choice((None, "#FFD447", "#FF8FC7"))), 1.5, 70, "Grass"),
                  (lambda m_, s: rock_cluster(m_, s, ("#B9B4C8", "#A3ADEB", "#8E89A0")), 3.0, 14, "Rock")]
        scatter(m, g, sp, k, seed, trees, 85, extras)
    elif name == "Farm":
        place("Barn", -112, 42, 14, barn, ry=-90)
        place("Silo", -116, -30, 5, silo)
        place("CornField", 106, -70, 18, lambda m_: corn_patch(m_, 5, 24, 44), ry=0)
        place("PumpkinPatch", 106, 60, 16, lambda m_: (pumpkin_patch(m_, 9, 26, 30), fence_square(m_, 28, 32)), ry=-90)
        place("Tractor", -96, 10, 5, tractor, ry=200)
        place("Scarecrow", 106, 18, 3, lambda m_: A.scarecrow(m_), ry=-90)

        def maple(m_, size, s):
            P.oak(m_, size, s, greens=("#D7372C", "#B82C24"))

        def orange_oak(m_, size, s):
            P.oak(m_, size, s, greens=("#F28C28", "#E2582A"))
        trees = [(orange_oak, 3), (maple, 2), (P.apple, 2), (lambda m_, sz, s: P.birch(m_, sz, s, greens=("#FFC83D", "#F2A922")), 2),
                 (P.poplar, 1)]
        extras = [(lambda m_, s: A.hay_bale(m_, ry=random.Random(s).uniform(0, 90), seed=s,
                                            top=(lambda m2: A.pumpkin(m2, 0.7, s, light=False)) if s % 3 == 0 else None), 3.0, 16, "HayBale"),
                  (lambda m_, s: A.pumpkin_pile(m_, s, n=3, carved_first=False), 3.0, 14, "Pumpkins"),
                  (lambda m_, s: P.bush(m_, s, greens=("#6E9A35", "#8CBF45"), berry=None), 3.2, 24, "Bush"),
                  (lambda m_, s: A.leaf_litter(m_, s), 1.6, 60, "Leaves"),
                  (lambda m_, s: P.tuft_cluster(m_, s, greens=("#8CBF45", "#B5B84A", "#6E9A35")), 1.5, 80, "Grass")]
        scatter(m, g, sp, k, seed, trees, 70, extras)
    elif name == "Snow":
        place("Cabin", 110, -40, 12, cabin, ry=-90)
        place("FrozenPond", -109, 48, 13, lambda m_: frozen_pond(m_, 11.0))
        for i, (x, z) in enumerate(((-96, -30), (96, 30), (-100, 110))):
            place("Snowman", x, z, 3.5, lambda m_, i=i: snowman(m_, i), ry=90 if x < 0 else -90)

        def snowy_pine(m_, size, s):
            P.pine(m_, size, s, greens=("#2F7F4A", "#3A9457"), snow="#FFFFFF")
        trees = [(snowy_pine, 10), (lambda m_, sz, s: P.birch(m_, sz, s, greens=("#E6EEF9", "#CFDDF0")), 1)]
        extras = [(lambda m_, s: ice_crystals(m_, s), 2.6, 26, "Ice"),
                  (lambda m_, s: rock_cluster(m_, s, ("#E6EEF9", "#9AA9C4", "#7C8BA8")), 3.0, 18, "Rock"),
                  (lambda m_, s: m_.box((0, 0.7, 0), (3.4, 1.4, 2.6), "#FFFFFF", ry=s % 90), 2.0, 40, "SnowPile")]
        scatter(m, g, sp, k, seed, trees, 95, extras)
    elif name == "Desert":
        place("CrashedUFO", -106, 72, 16, ufo, ry=-70)
        rng = random.Random(seed)
        for i in range(14):                                    # mesas on the outer ring
            for _ in range(200):
                a = rng.uniform(0, 6.28)
                x, z = math.cos(a) * rng.uniform(100, 125), math.sin(a) * rng.uniform(150, 200)
                if g.at(x, z) is not None and sp.free(x, z, 9):
                    place("Mesa", x, z, 9, lambda m_, i=i: mesa(m_, 300 + i, rng.uniform(14, 30), rng.uniform(12, 18), th))
                    break
        trees = [(lambda m_, sz, s: desert_plant(m_, s), 6),
                 (lambda m_, sz, s: P.palm(m_, sz, s), 1)]
        extras = [(lambda m_, s: desert_rock(m_, s), 3.0, 30, "Rock"),
                  (lambda m_, s: bones(m_, s), 2.5, 10, "Bones"),
                  (lambda m_, s: tumbleweed(m_, s), 2.0, 14, "Tumbleweed"),
                  (lambda m_, s: P.crate_cluster(m_, s), 4.0, 6, "Crates")]
        scatter(m, g, sp, k, seed, trees, 60, extras)

    {"Farm": hay_obstacles, "Snow": snow_obstacles, "Desert": desert_obstacles}.get(name, lambda m_, k_: None)(m, k)

    for p in m.parts:
        p["light"] = None
    return m, field_colors(th), th["trim"]


def check(m):
    """Nothing new may stand in the play volume except the obstacles."""
    bad = []
    for p in m.parts:
        if p["stage"] == "obstacle":
            continue
        x, y, z = p["pos"]
        R, s = p["R"], p["size"]
        hx, hy, hz = (sum(abs(R[i][j]) * s[j] / 2 for j in range(3)) for i in range(3))   # world AABB half extents
        if abs(x) - hx < FX and abs(z) - hz < FZ and y + hy > 0.05:
            bad.append((p.get("name"), p["tag"], p["pos"], p["size"]))
    return bad
