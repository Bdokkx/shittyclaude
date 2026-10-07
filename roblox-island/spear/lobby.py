"""Lobby island - a rebuild of the uploaded Lobby model (please_make_better.rbxm) in the spear style.

Everything the game scripts can see stays exactly where it was: the Lobby folder, Markers/LobbySpawn,
the SpawnLocation, CoinsBoard / StreakBoard (Board parts with the Leaderboard attribute, Header with the
SurfaceGui text). Those are kept from the original file by tools/export_lobby.luau; this file only builds
the new Island terrain and the Decor folder around them.

Local frame: origin = centre of the plaza on the grass top (world 0, 60, -340); +Z = towards the walk.

Fixed from the original:
  - rails hung past the island edge at both ends -> the fence now follows the rim
  - a flower stood inside a StreakBoard post, a bush inside a tree trunk, bushes overlapping each other
  - lone 1x1 flower bricks -> proper flower clusters on a leafy base
  - Walk and Plaza overlapped with coplanar tops (flicker) -> the walk starts at the plaza trim
  - the rock body had CanCollide off, so players fell into the cliffs -> cliffs collide

October theme: autumn grass and trees, fallen leaves, hay bales, jack-o'-lanterns, a pumpkin inlay on the
plaza, and a Pumpkin Patch quest area on the west side: an open NPC spot (Markers/NPCSpot) with scenery
around it, between two fenced
fields whose pumpkins are separate models in Lobby/PumpkinPatch (QuestPumpkin, PrimaryPart = the core).
"""
import math
import random

import autumn as A
import props as P
from core import Model, poly_contains
from terrain import greedy, noise2
from voxel_island import C, PRESET

ORIGIN = (0.0, 60.0, -340.0)
CELL = 4.0
GRASS = ("#8CBF45", "#9DBA44")       # late-season grass
LIP = "#6E9A35"
DIRT = ("#B07A4A", "#9A6238")
BANDS = (C["rock_light"], C["rock"], C["rock_dark"])
SAND = ("#F3E2B6", "#E9D29C")        # plaza tiles
TRIM = "#C9AE78"
STONE = "#B9B4C8"
STONE_DK = "#8E89A0"
ACC_PURPLE = "#B67CFF"


def outline(r=49.0, seed=5, amp=0.035, p=3.2, n=160):
    """Rounded-square island rim with a little wobble (the walk side stays straight enough for the fence)."""
    rng = random.Random(seed)
    waves = [(k, rng.uniform(0, 6.283), amp / (1 + 0.5 * k)) for k in range(3, 8)]
    pts = []
    for i in range(n):
        a = i * 2 * math.pi / n
        c, s = math.cos(a), math.sin(a)
        rr = r / (abs(c) ** p + abs(s) ** p) ** (1 / p)
        rr *= 1 + sum(w * math.sin(k * a + ph) for k, ph, w in waves)
        pts.append((c * rr, s * rr))
    return pts


def scale(poly, f, dx=0.0, dz=0.0):
    return [(x * f + dx, z * f + dz) for x, z in poly]


def cells_in(poly):
    out = set()
    for i in range(-16, 16):
        for j in range(-16, 16):
            if poly_contains(poly, (i + 0.5) * CELL, (j + 0.5) * CELL):
                out.add((i, j))
    return out


def fill(m, cells, y0, y1, color_fn, name=None):
    keyed = {c: color_fn(c) for c in cells}
    first = None
    for i0, j0, i1, j1, col in greedy(keyed):
        p = m.span((i0 * CELL, y0, j0 * CELL), ((i1 + 1) * CELL, y1, (j1 + 1) * CELL), col)
        first = first or p
    return first


class Spots:
    """Simple footprint bookkeeping so decor never clips into boards, paths or each other."""

    def __init__(self, rim):
        self.rim = rim
        self.taken = []          # (x, z, r)

    def block(self, x, z, r):
        self.taken.append((x, z, r))

    def block_rect(self, x0, z0, x1, z1):
        step = 2.0
        x = x0
        while x <= x1:
            z = z0
            while z <= z1:
                self.taken.append((x, z, 1.2))
                z += step
            x += step

    def free(self, x, z, r, edge=3.0):
        if not poly_contains(scale(self.rim, 1 - edge / 49.0), x, z):
            return False
        return all(math.hypot(x - a, z - b) >= r + q for a, b, q in self.taken)

    def take(self, x, z, r, edge=3.0):
        if self.free(x, z, r, edge):
            self.block(x, z, r)
            return True
        return False


def kept_parts(m):
    """The original boards (exported as-is from the uploaded file; here only so the renders show them)."""
    with m.ctx(stage="keep", folder="Keep", collide=True):
        for side, head, label in ((-1, "#F5B700", "TOP COINS"), (1, "#F0352B", "TOP STREAKS")):
            cx = 13.0 * side
            for px in (cx - 8.4, cx + 8.4):
                m.box((px, 10.0, -34.0), (1.8, 20.0, 1.8), "#C8743A")
                m.box((px, 1.1, -34.0), (3.0, 2.2, 3.0), "#A0572B")
            m.box((cx, 10.4, -34.0), (15.0, 15.0, 0.8), "#22232B")
            h = m.box((cx, 19.8, -34.0), (18.6, 3.4, 1.8), head)
            m.text(h, label, "#FFFFFF", "Back")


def terrain(m, rim):
    top = cells_in(rim)
    with m.ctx(stage="terrain", folder="Island", tag=None, collide=True):
        # grass top in two tones, a darker lip one cell wider at the rim, then dirt
        def grass(c):
            return GRASS[1] if noise2(c[0] * 4, c[1] * 4, 3, 22) > 0.62 else GRASS[0]
        core = {c for c in top if abs(c[0] + 0.5) < 6 and abs(c[1] + 0.5) < 6}
        g = fill(m, core, -1.2, 0.0, lambda c: GRASS[0])
        g["name"] = "Grass"
        fill(m, top - core, -1.2, 0.0, grass)
        fill(m, top, -2.4, -1.2, lambda c: LIP)
        fill(m, top, -5.0, -2.4, lambda c: DIRT[0] if (c[0] + c[1]) % 3 else DIRT[1])

        # stepped rock body tapering to a point (voxel layers + colour bands)
        layers = [(-5, -10, 0.96, 0), (-10, -16, 0.86, 0), (-16, -23, 0.74, 1), (-23, -31, 0.6, 1),
                  (-31, -40, 0.46, 1), (-40, -50, 0.33, 2), (-50, -61, 0.22, 2), (-61, -74, 0.12, 2)]
        for k, (y1, y0, f, band) in enumerate(layers):
            poly = scale(rim, f, dx=math.sin(k * 1.3) * 2.0, dz=math.cos(k * 0.9) * 2.0)
            cs = cells_in(poly) or {(-1, -1), (0, -1), (-1, 0), (0, 0)}
            fill(m, cs, y0, y1, lambda c, b=band: BANDS[b] if (c[0] * 7 + c[1] * 3) % 5 else BANDS[min(2, b + 1)])
        m.span((-2, -82, -2), (2, -74, 2), BANDS[2])

        # chunky tilted slabs around the cliff so the sides are not plain steps
        rng = random.Random(21)
        n = len(rim)
        for k, (y_mid, f, th) in enumerate(((-7.5, 0.97, 5.0), (-19, 0.79, 5.5), (-34, 0.55, 6.0), (-52, 0.3, 5.0))):
            step = (7, 9, 12, 18)[k]
            for i in range(0, n, step):
                x, z = rim[(i + k * 3) % n]
                a = math.atan2(z, x)
                rr = math.hypot(x, z) * f
                w = rng.uniform(8, 14) * (1.0 if k < 2 else 0.8)
                col = BANDS[min(2, k // 2 + rng.choice((0, 0, 1)))]
                with m.at((math.cos(a) * rr, y_mid + rng.uniform(-1.5, 1.5), math.sin(a) * rr),
                          ry=-math.degrees(a) + 90 + rng.uniform(-12, 12)):
                    m.box((0, 0, 0), (w, th, 4.0), col, rx=rng.uniform(6, 14), rz=rng.uniform(-8, 8))


def plaza(m, sp):
    with m.ctx(stage="terrain", folder="Island", collide=True):
        m.box((0, 0.175, 0), (48, 0.35, 48), TRIM)["name"] = "PlazaTrim"
        m.box((0, 0.3, 0), (44, 0.6, 44), SAND[0])["name"] = "Plaza"
        # walk from the trim edge to the rim (no overlap with the plaza any more)
        m.box((0, 0.3, 35.0), (16, 0.6, 22.0), SAND[0])["name"] = "Walk"
    with m.ctx(stage="props", folder="Decor", tag="PlazaInlay:0", collide=False, shadow=False):
        # checker tiles around the edge of the plaza, a ring + compass in the middle (flat, nothing to trip on)
        for i in range(-5, 6):
            for j in range(-5, 6):
                if max(abs(i), abs(j)) >= 4 and (i + j) % 2 == 0:
                    m.box((i * 4, 0.65, j * 4), (3.6, 0.1, 3.6), SAND[1])
        m.octagon(0.66, 13.0, 0.12, TRIM)
        m.octagon(0.70, 11.6, 0.12, SAND[0])
        # pumpkin inlay: body, darker ribs, stem + leaf, and a purple ring
        m.octagon(0.73, 9.2, 0.1, A.PURPLE)
        m.octagon(0.75, 8.2, 0.1, SAND[0])
        m.box((0, 0.78, 0.6), (11.0, 0.1, 8.4), A.ORANGE[0])
        m.box((0, 0.78, 0.6), (8.4, 0.1, 10.0), A.ORANGE[0])
        for x in (-2.6, 2.6):
            m.box((x, 0.8, 0.6), (0.6, 0.1, 9.0), A.ORANGE[1])
        m.box((0, 0.8, 0.6), (0.6, 0.1, 9.6), A.ORANGE[1])
        m.box((0, 0.8, -5.2), (1.4, 0.1, 2.6), A.STEM)
        m.box((1.8, 0.8, -5.0), (2.4, 0.1, 1.2), A.LEAF, ry=-25)
        # walk: darker edges + stepping tiles
        for x in (-7.5, 7.5):
            m.box((x, 0.65, 35.0), (1.0, 0.1, 22.0), TRIM)
        for z in range(26, 46, 4):
            m.box((0, 0.65, z), (5.0, 0.1, 2.6), SAND[1])
    sp.block_rect(-26, -26, 26, 26)           # plaza + trim
    sp.block_rect(-10, 22, 10, 50)            # walk


def boards_decor(m, sp, k):
    """Lanterns and a trophy around the leaderboards (the boards themselves are untouched; nothing tall
    stands in front of them so the bottom rows stay readable)."""
    sp.block_rect(-24, -37, 24, -31)
    with m.ctx(stage="props", folder="Decor", tag="BoardTrophy:0"):
        with m.at((0, 0, -34)):
            m.box((0, 0.8, 0), (4.4, 1.6, 4.4), STONE_DK)
            m.box((0, 1.8, 0), (3.6, 0.4, 3.6), STONE)
            m.box((0, 2.6, 0), (1.0, 1.2, 1.0), "#E0A800")
            m.box((0, 4.0, 0), (2.6, 2.0, 2.0), "#FFD447")
            for s in (-1, 1):
                m.box((s * 1.6, 4.3, 0), (0.5, 1.2, 0.5), "#FFD447")
            m.box((0, 5.1, 0), (2.9, 0.3, 2.3), "#FFE58A", collide=False)
            m.box((0, 2.1, 0), (2.0, 0.4, 1.6), "#E0A800")
    for s in (-1, 1):
        with m.ctx(stage="props", folder="Decor", tag="Lantern:%d" % next(k)):
            with m.at((s * 25.0, 0, -32.5), ry=90 if s < 0 else -90):
                P.lantern_post(m, h=9)
        with m.ctx(stage="props", folder="Decor", tag="JackOLantern:%d" % next(k)):
            with m.at((s * 25.0, 0, -29.0), ry=180 + s * 20):
                A.pumpkin_pile(m, 50 + s)
        sp.block(s * 25.0, -32.5, 2.5)
        sp.block(s * 25.0, -29.0, 3.0)


def plaza_ring(m, sp, k):
    # lanterns on the plaza corners (outside the 30x30 spawn zone)
    for x in (-21, 21):
        for z in (-21, 21):
            with m.ctx(stage="props", folder="Decor", tag="Lantern:%d" % next(k)):
                with m.at((x, 0.6, z), ry=math.degrees(math.atan2(-x, -z)) + 90):
                    P.lantern_post(m, h=8)
    # benches facing the plaza from the east (the west side holds the NPC spot), hay bales on the east
    for s in (-1, 1):
        for z in ((-6, 6) if s > 0 else ()):
            with m.ctx(stage="props", folder="Decor", tag="Bench:%d" % next(k)):
                with m.at((s * 28.5, 0, z), ry=90 * s):
                    P.bench(m)
            sp.block(s * 28.5, z, 3.6)
        for z in ((-15, 15) if s > 0 else ()):
            with m.ctx(stage="props", folder="Decor", tag="HayBale:%d" % next(k)):
                with m.at((28.5, 0, z)):
                    A.hay_bale(m, ry=90, seed=z, top=lambda m_, z=z: A.pumpkin(m_, 0.8, 70 + z, carved=z > 0))
            sp.block(28.5, z, 3.2)
    # jack-o'-lanterns on the plaza corners, next to the lanterns (on the trim, outside the spawn zone)
    for x in (-1, 1):
        for z in (-1, 1):
            with m.ctx(stage="props", folder="Decor", tag="JackOLantern:%d" % next(k)):
                with m.at((x * 23.0, 0.35, z * 23.0), ry=math.degrees(math.atan2(x, z)) + 180):
                    A.pumpkin(m, 0.9, 80 + x * 3 + z, carved=True)
    # lanterns along the walk and a pair of stone pillars at the walk end
    for z in (30, 40):
        for s in (-1, 1):
            with m.ctx(stage="props", folder="Decor", tag="Lantern:%d" % next(k)):
                with m.at((s * 10.0, 0, z), ry=180 if s < 0 else 0):
                    P.lantern_post(m, h=8)
            with m.ctx(stage="props", folder="Decor", tag="JackOLantern:%d" % next(k)):
                with m.at((s * 10.2, 0, z + 2.6), ry=-90 * s):
                    A.pumpkin(m, 0.6, 90 + z + s, carved=z == 30, light=False)
            sp.block(s * 10.0, z, 2.0)
            sp.block(s * 10.2, z + 2.6, 1.2)


def npc_spot(m, sp, k, pos=(-31.0, 0.0, 0.0)):
    """A spot for an NPC on the west side of the plaza - no building, just a trodden dirt clearing with autumn
    scenery around the back and sides (hay bales, pumpkins, corn, a maple) and the open side facing the plaza.
    Markers/NPCSpot (invisible) is where the NPC stands; its front (LookVector) faces the plaza, so a script can
    do  npc:PivotTo(Lobby.Markers.NPCSpot.CFrame * CFrame.new(0, 3, 0)).
    Local frame: front = -Z (towards the plaza)."""
    sp.block(pos[0], pos[2], 7.0)
    sp.block(pos[0] - 10.5, pos[2], 4.5)                                 # the maple behind it
    rng = random.Random(77)
    with m.at(pos, ry=-90):
        with m.ctx(stage="props", folder="Decor", tag="NPCClearing:%d" % next(k), collide=True):
            # flat, walkable ground: dirt clearing with a lighter centre and stepping stones from the plaza
            m.octagon(0.1, 5.2, 0.2, "#A7794A")
            m.octagon(0.22, 3.4, 0.08, "#C9A27A")
            for z, x in ((-6.2, -0.4), (-7.6, 0.5)):
                m.box((x, 0.08, z), (2.0, 0.16, 1.2), STONE, ry=rng.uniform(-15, 15))
        with m.ctx(stage="props", folder="Decor", tag="NPCScenery:%d" % next(k), collide=True):
            # back: two hay bales with a third on top, pumpkins on and in front of them
            for x in (-2.3, 2.3):
                with m.at((x, 0, 6.2)):
                    A.hay_bale(m, w=4.2, seed=int(x * 3))
            with m.at((0.3, 2.2, 6.2), ry=6):
                A.hay_bale(m, w=3.8, seed=9, top=lambda m_: A.pumpkin(m_, 0.9, 31, carved=True))
            with m.at((-3.4, 2.2, 6.0), ry=20):
                A.pumpkin(m, 0.6, 32)
            with m.at((3.2, 0, 4.0), ry=-25):
                A.pumpkin(m, 0.8, 33, carved=True)
            # sides: pumpkin piles and a crate of pumpkins, corn stalks at the back corners
            with m.at((-5.4, 0, 1.0), ry=60):
                A.pumpkin_pile(m, 34, n=3, carved_first=False)
            with m.at((5.6, 0, 0.6), ry=-40):
                A.pumpkin_pile(m, 35, n=2, carved_first=True)
            with m.at((-5.2, 0, 4.6), ry=12):
                P.crate(m, 2.6)
                with m.at((0, 2.6, 0)):
                    A.pumpkin(m, 0.55, 36)
            for x, z in ((-6.4, 6.4), (-5.4, 7.6), (6.0, 6.8), (6.8, 5.4), (5.0, 7.9)):
                with m.at((x, 0, z)):
                    A.corn_stalk(m, int(x * 7 + z))
            for x, z in ((-1.6, -5.6), (1.8, -5.0), (5.2, -3.2)):          # leaves in front
                with m.at((x, 0, z)):
                    A.leaf_litter(m, int(x * 11 + z))
        with m.ctx(stage="props", folder="Decor", tag="Tree:%d" % next(k)):
            with m.at((0, 0, 10.5), ry=35):
                P.oak(m, 1, 140, greens=("#D7372C", "#B82C24"))
        with m.ctx(stage="marker", folder="Markers", tag="Marker", collide=False, shadow=False):
            m.box((0, 0.76, 0), (3.0, 1.0, 3.0), "#FFFFFF", name="NPCSpot", transparency=1.0)


FIELDS = ((-44.0, -25.0, -27.0, -8.0), (-44.0, 8.0, -27.0, 25.0))     # x0, z0, x1, z1 (local)


def pumpkin_patch(m, sp, k):
    """Two fenced pumpkin fields north and south of the NPC spot, gates facing the plaza. Soil rows with
    vines; 5 big QuestPumpkin models per field (Lobby/PumpkinPatch) plus small decorative ones, a scarecrow
    in the north field and a corn row in the south one."""
    rng = random.Random(44)
    q = 0
    for f, (x0, z0, x1, z1) in enumerate(FIELDS):
        sp.block_rect(x0 - 1, z0 - 1, x1 + 1, z1 + 1)
        zm = (z0 + z1) / 2
        with m.ctx(stage="props", folder="Decor", tag="PatchFence:%d" % next(k)):
            for a, b in (((x0, z0), (x1, z0)), ((x0, z1), (x1, z1)), ((x0, z0), (x0, z1)),
                         ((x1, z0), (x1, zm - 2.2)), ((x1, zm + 2.2), (x1, z1))):
                P_rail(m, a, b, h=2.4)
            for z in (zm - 2.2, zm + 2.2):                              # gate posts with a pumpkin on top
                m.box((x1, 1.6, z), (1.2, 3.2, 1.2), C["wood_dark"])
                with m.at((x1, 3.2, z), ry=-90):
                    A.pumpkin(m, 0.55, int(z), carved=True, light=False)
        rows = (z0 + 4.0, zm, z1 - 4.0)
        rx0, rx1 = x0 + 3.2, x1 - 2.2
        with m.ctx(stage="props", folder="Decor", tag="SoilRows:%d" % next(k)):
            for i, z in enumerate(rows):
                with m.at(((rx0 + rx1) / 2, 0, z)):
                    A.soil_row(m, rx1 - rx0, 60 + f * 3 + i)
        for i, z in enumerate(rows):
            xs = [rx0 + 2.2 + j * 4.2 for j in range(3)]
            if i == 1:
                xs = [x + 2.1 for x in xs[:2]]
            with m.ctx(stage="props", folder="Decor", tag="Vines:%d" % next(k), collide=False, shadow=False):
                m.box(((rx0 + rx1) / 2, 0.5, z + 0.5), (rx1 - rx0 - 1.0, 0.25, 0.25), A.VINE)
                for x in [rx0 + 1.2 + 1.6 * j for j in range(int((rx1 - rx0 - 2) / 1.6))]:
                    m.box((x, 0.55, z + rng.choice((-0.7, 0.8))), (0.9, 0.15, 0.8), A.LEAF, ry=rng.uniform(0, 90))
            for j, x in enumerate(xs):
                big = (i + j) % 2 == 0 or i == 1
                if big:
                    q += 1
                    with m.ctx(stage="props", folder="PumpkinPatch", tag="QuestPumpkin:%d" % q):
                        with m.at((x, 0.4, z), ry=rng.uniform(0, 360)):
                            A.pumpkin(m, 1.0, 200 + q)
                else:
                    with m.ctx(stage="props", folder="Decor", tag="Pumpkin:%d" % next(k)):
                        with m.at((x, 0.4, z), ry=rng.uniform(0, 360)):
                            A.pumpkin(m, 0.6, 300 + q + j)
        if f == 0:
            with m.ctx(stage="props", folder="Decor", tag="Scarecrow:%d" % next(k)):
                with m.at((x0 + 1.6, 0, zm), ry=-90):
                    A.scarecrow(m)
        else:
            with m.ctx(stage="props", folder="Decor", tag="CornRow:%d" % next(k)):
                z = z0 + 1.6
                while z < z1 - 1.0:
                    with m.at((x0 + 1.4, 0, z)):
                        A.corn_stalk(m, int(z * 10))
                    z += 1.9
    return q


def fence(m, rim, sp, k):
    """Fence along the south rim (the old rails stuck out past the island at both ends), gap at the walk."""
    inset = scale(rim, 1 - 2.2 / 49.0)
    south = [(x, z) for x, z in inset if z > 26]
    south.sort(key=lambda p: p[0])
    for side in (-1, 1):
        pts = [p for p in south if p[0] * side > 9.5]
        pts.sort(key=lambda p: abs(p[0]))
        pts = pts[::3] + ([pts[-1]] if (len(pts) - 1) % 3 else [])
        with m.ctx(stage="props", folder="Decor", tag="Fence:%d" % next(k)):
            for a, b in zip(pts, pts[1:]):
                P_rail(m, a, b)
        for x, z in pts:
            sp.block(x, z, 1.5)
    # gate posts at the walk opening
    for s in (-1, 1):
        x, z = s * 9.6, south and max(z for x2, z in south if abs(x2) < 12) or 46
        with m.ctx(stage="props", folder="Decor", tag="GatePost:%d" % next(k)):
            m.box((x, 1.6, z), (2.0, 3.2, 2.0), STONE)
            m.box((x, 3.4, z), (2.4, 0.4, 2.4), STONE_DK)
            with m.at((x, 3.6, z)):
                A.pumpkin(m, 0.8, 120 + s, carved=True)


def P_rail(m, a, b, h=3.0):
    from buildings import rail_line
    rail_line(m, a, b, 0.0, color=(C["wood"], C["wood_dark"]), every=4.5, h=h)


def plants(m, rim, sp, k):
    rng = random.Random(9)
    def maple(m_, size, seed):
        P.oak(m_, size, seed, greens=("#D7372C", "#B82C24"))

    def orange_oak(m_, size, seed):
        P.oak(m_, size, seed, greens=("#F28C28", "#E2582A"))

    def gold_birch(m_, size, seed):
        P.birch(m_, size, seed, greens=("#FFC83D", "#F2A922"))

    def amber_poplar(m_, size, seed):
        P.poplar(m_, size, seed, greens=("#F2A22A", "#D9822B"))

    trees = [  # hand placed: framing the boards, the plaza sides and the walk (the west side is the patch)
        (maple, 1, -38, -31), (orange_oak, 2, 37, -31), (P.pine, 1, 42, -14),
        (maple, 1, 39, 10), (amber_poplar, 1, -18, 40), (amber_poplar, 1, 18, 40),
        (P.pine, 0, -30, -42), (gold_birch, 0, 30, -42), (orange_oak, 0, 36, 30), (gold_birch, 0, -36, 31),
        (gold_birch, 1, 44, -4),
    ]
    for i, (fn, size, x, z) in enumerate(trees):
        if not sp.take(x, z, 4.0, edge=4.0):
            continue
        with m.ctx(stage="props", folder="Decor", tag="Tree:%d" % next(k)):
            with m.at((x, 0, z), ry=rng.uniform(0, 360)):
                fn(m, size, 100 + i)
    # bushes, flower clusters and grass tufts on the free lawn
    cand = [(rng.uniform(-46, 46), rng.uniform(-46, 46)) for _ in range(900)]
    # small pumpkin piles out on the lawn
    npile = 0
    for x, z in cand[:300]:
        if npile < 5 and sp.take(x, z, 3.2, edge=4.0):
            with m.ctx(stage="props", folder="Decor", tag="PumpkinPile:%d" % next(k)):
                with m.at((x, 0, z), ry=rng.uniform(0, 360)):
                    A.pumpkin_pile(m, 600 + npile, n=rng.choice((2, 3)), carved_first=False)
            npile += 1
    nb = nf = nt = 0
    for x, z in cand:
        if nb < 14 and sp.take(x, z, 3.2, edge=4.0):
            with m.ctx(stage="props", folder="Decor", tag="Bush:%d" % next(k)):
                with m.at((x, 0, z)):
                    P.bush(m, 300 + nb, greens=rng.choice((("#6E9A35", "#8CBF45"), ("#C8502A", "#E07B2C"),
                                                           ("#B5452B", "#D9822B"))), berry=None)
            nb += 1
        elif nf < 18 and sp.take(x, z, 2.2, edge=3.0):
            with m.ctx(stage="props", folder="Decor", tag="Flowers:%d" % next(k)):
                with m.at((x, 0, z)):
                    P.flowers(m, 400 + nf, rng.choice((("orange", "yellow"), ("purple", "yellow"),
                                                      ("orange", "red"))), leaf=LIP)
            nf += 1
        elif nt < 40 and sp.take(x, z, 1.6, edge=2.5):
            with m.ctx(stage="props", folder="Decor", tag="Grass:%d" % next(k)):
                with m.at((x, 0, z)):
                    P.tuft_cluster(m, 500 + nt, greens=("#8CBF45", "#B5B84A", "#6E9A35"),
                                   flower=rng.choice((None, None, P.ACCENTS["orange"])))
            nt += 1
    # fallen leaves everywhere, including the plaza edge (flat, no collision)
    for i, (x, z) in enumerate(cand[300:]):
        if i > 260:
            break
        if poly_contains(scale(rim, 0.94), x, z) and not (abs(x) < 15 and abs(z) < 15) and \
                all(math.hypot(x - a, z - b) >= q + 0.6 for a, b, q in sp.taken if q > 1.3):
            with m.ctx(stage="props", folder="Decor", tag="Leaves:%d" % next(k)):
                on_plaza = (abs(x) < 22 and abs(z) < 22) or (abs(x) < 8 and z > 0)
                on_trim = not on_plaza and abs(x) < 24 and abs(z) < 24
                with m.at((x, 0.6 if on_plaza else 0.35 if on_trim else 0, z)):
                    A.leaf_litter(m, 800 + i)


def hanging(m, rim, k):
    """Vines and roots hanging from the grass lip, and floating islets below the lobby."""
    rng = random.Random(33)
    with m.ctx(stage="props", folder="Decor", tag="Vines:%d" % next(k), collide=False, shadow=False):
        for i in range(0, len(rim), 5):
            x, z = rim[i]
            a = math.atan2(z, x)
            r = math.hypot(x, z) - 0.6
            L = rng.uniform(3, 9)
            col = rng.choice((LIP, "#3E8F33", "#5EBE45"))
            m.box((math.cos(a) * r, -2.0 - L / 2, math.sin(a) * r), (0.6, L, 0.6), col, ry=-math.degrees(a))
            if rng.random() < 0.4:
                m.box((math.cos(a) * r, -2.0 - L, math.sin(a) * r), (1.2, 1.0, 1.2), col)
    for i, (x, y, z, s) in enumerate(((-62, -30, 24, 1.0), (58, -38, -30, 0.8), (-34, -52, -64, 0.6),
                                      (40, -22, 58, 0.55))):
        with m.ctx(stage="props", folder="Decor", tag="FloatingRock:%d" % next(k), collide=False):
            with m.at((x, y, z), ry=rng.uniform(0, 90)):
                w = 14 * s
                m.box((0, -0.6, 0), (w, 1.2, w * 0.9), GRASS[0])
                m.box((0, -1.6, 0), (w + 0.4, 0.8, w * 0.9 + 0.4), LIP)
                m.box((0, -4.0, 0), (w * 0.9, 4.0, w * 0.8), DIRT[0])
                m.box((0.5, -8.5, 0.3), (w * 0.62, 5.0, w * 0.56), BANDS[1], rx=4)
                m.box((-0.3, -12.5, 0), (w * 0.34, 3.6, w * 0.3), BANDS[2], rz=6)
                if s >= 0.8:
                    with m.at((w * 0.15, 0, 0)):
                        P.pine(m, 0, 700 + i)
                else:
                    with m.at((0, 0, 0), ry=30):
                        A.pumpkin(m, 0.9, 720 + i)


def build():
    m = Model("Lobby")
    rim = outline()
    sp = Spots(rim)
    counter = iter(range(1, 100000))
    with m.at(ORIGIN):
        kept_parts(m)
        terrain(m, rim)
        plaza(m, sp)
        boards_decor(m, sp, counter)
        npc_spot(m, sp, counter)
        pumpkin_patch(m, sp, counter)
        plaza_ring(m, sp, counter)
        fence(m, rim, sp, counter)
        plants(m, rim, sp, counter)
        hanging(m, rim, counter)
    for p in m.parts:          # no PointLights anywhere (lanterns and jack-o'-lanterns glow with Neon only)
        p["light"] = None
    ox, oy, oz = ORIGIN
    cams = {
        "overview": ((ox + 95, oy + 55, oz + 120), (ox, oy - 10, oz), 32),
        "plaza": ((ox + 0, oy + 14, oz + 62), (ox, oy + 6, oz - 30), 24),
        "boards": ((ox - 26, oy + 8, oz + 8), (ox + 4, oy + 9, oz - 34), 24),
        "npc": ((ox - 6, oy + 12, oz + 22), (ox - 33, oy + 3, oz), 22),
        "patch": ((ox + 2, oy + 30, oz + 30), (ox - 34, oy, oz - 4), 24),
        "under": ((ox - 120, oy - 40, oz + 90), (ox, oy - 25, oz), 32),
    }
    return m, cams


if __name__ == "__main__":
    import json
    import os
    m, cams = build()
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data = dict(name="Lobby", origin=ORIGIN, water=(-400, 0, -800, 400, 0, 100), preset=PRESET, cameras=cams,
                parts=[dict(size=p["size"], pos=p["pos"], R=p["R"], color=p["color"], mat=p["mat"],
                            light=p["light"], stage=p["stage"], folder=p["folder"], tier=p["tier"],
                            tag=p["tag"], collide=p["collide"], shadow=p["shadow"], name=p.get("name"),
                            transparency=p.get("transparency", 0.0), effect=p.get("effect")) for p in m.parts],
                texts=m.texts)
    os.makedirs(os.path.join(root, "build"), exist_ok=True)
    json.dump(data, open(os.path.join(root, "build", "Lobby.json"), "w"))
    print("Lobby: %d parts (%d new)" % (len(m.parts), sum(p["stage"] != "keep" for p in m.parts)))
