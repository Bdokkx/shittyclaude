"""VoxelIsland - compact version (origin 0,0,0).

A small hand-laid island (~190 studs across) built to the style bible:
  beach ring (y=3) -> main lawn (y=12) -> hill (y=24) with the lighthouse.
  Hub on the lawn with three shop stalls around a plain stone floor, a portal ledge (Blender portal
  marker) west of the hub, wooden stairs down to a T-dock over a coral reef, stone stairs up the hill,
  a waterfall from the hill into a pond, tree clumps, beach palms, grass tufts, a small beach camp.
"""
import math
import random

import buildings as Bd
import props as P
from core import Model
from terrain import blob, noise2, path_strip, slab_stack
from core import poly_contains
from terraced import DIRS, ground_and_cliffs, rowboat, stair_rails
from voxel_island import BANDS, C, PRESET, plant_tree, adiff

DECK_Y = 4.5
BEACH, MAIN, HILL = 3.0, 12.0, 24.0


class Grid:
    """Same interface as terraced.Grid, filled from hand-made outlines."""
    S, N = 4, 52

    def __init__(self):
        self.top, self.kind, self.surf, self.path, self.plaza = {}, {}, {}, {}, set()

    def wx(self, i):
        return (i - self.N / 2 + 0.5) * self.S

    def cell_of(self, x, z):
        return (int(math.floor(x / self.S + self.N / 2)), int(math.floor(z / self.S + self.N / 2)))

    def top_at(self, x, z):
        return self.top.get(self.cell_of(x, z))


def build():
    m = Model("VoxelIsland")
    g = Grid()
    beach = blob(0, 4, 74, seed=11, amp=0.08)
    main = blob(-2, -4, 50, seed=12, amp=0.09)
    hx, hz = 22.0, -30.0
    hill = blob(hx, hz, 21, seed=13, amp=0.07)
    for i in range(g.N):
        for j in range(g.N):
            x, z = g.wx(i), g.wx(j)
            if poly_contains(hill, x, z):
                t, k = HILL, "land"
            elif poly_contains(main, x, z):
                t, k = MAIN, "land"
            elif poly_contains(beach, x, z):
                t, k = BEACH, "beach"
            else:
                continue
            g.top[(i, j)], g.kind[(i, j)], g.surf[(i, j)] = t, k, "grass" if k == "land" else "sand"

    hub = (-4.0, 10.0)
    FLOOR_R = 12.0

    # ---- wooden stairs: hub -> south down to the beach (3 cells wide)
    ci, cj = g.cell_of(hub[0], hub[1])
    j = cj
    while g.top.get((ci, j + 1), 0) == MAIN:
        j += 1
    dock_stair = []
    for k in range(6):                     # 6 steps of 1.5 carved into the lawn edge
        jj = j - 5 + k
        for di in (-1, 0, 1):
            c = (ci + di, jj)
            g.top[c] = MAIN - 1.5 * (k + 1)
            g.kind[c], g.surf[c] = "path", ""
            g.path[c] = (g.top[c], "wood", (0.0, 1.0), 0.0)
            dock_stair.append(c)
    stair_foot_z = g.wx(j) + 2
    # ---- stone stairs up the hill's south face
    hi, hj = g.cell_of(hx, hz)
    j2 = hj
    while g.top.get((hi, j2 + 1), 0) == HILL:
        j2 += 1
    for k in range(8):                     # from the lawn (12) up to the hill (24), carved into the hill
        jj = j2 - k
        for di in (-1, 0, 1):
            c = (hi + di, jj)
            g.top[c] = MAIN + 1.5 * (k + 1)
            g.kind[c], g.surf[c] = "path", ""
            g.path[c] = (g.top[c], "cobble", (0.0, -1.0), 0.0)
    hill_stair_foot = (g.wx(hi), g.wx(j2) + 4)
    # ---- portal ledge: 6x6 cells raised west of the hub, stone steps facing the hub (east)
    pc = g.cell_of(hub[0] - 34, hub[1] - 2)
    PL = MAIN + 7.5
    ledge = [(pc[0] + a, pc[1] + b) for a in range(-3, 3) for b in range(-3, 3)]
    for c in ledge:
        if c in g.top:
            g.top[c], g.kind[c], g.surf[c] = PL, "land", "grass"
    for k in range(5):
        for dj in (-1, 0):
            c = (pc[0] + 3 + k, pc[1] + dj)
            if c in g.top:
                g.top[c] = PL - 1.5 * (k + 1)
                g.kind[c], g.surf[c] = "path", ""
                g.path[c] = (g.top[c], "cobble", (1.0, 0.0), 0.0)
    portal_pos = (g.wx(pc[0]) - 2, g.wx(pc[1]) - 2)

    levels, height = ground_and_cliffs(m, g, C, seed=21, water_levels=(-1.5, -5.0, -12.0))

    def ground(x, z):
        return g.top_at(x, z)

    keep = [(hub, FLOOR_R + 2), (portal_pos, 15), ((hx, hz), 11)]

    def clear(x, z, r=0):
        return all(math.hypot(x - a, z - b) > rr + r for (a, b), rr in keep)

    def flat(x, z, w, d, ry, level):
        a = math.radians(ry)
        rx_, rz_ = math.cos(a), -math.sin(a)
        fx, fz = math.sin(a), math.cos(a)
        for u in range(-int(w / 2), int(w / 2) + 1, 2):
            for v in range(-int(d / 2), int(d / 2) + 1, 2):
                c = g.cell_of(x + rx_ * u + fx * v, z + rz_ * u + fz * v)
                if g.top.get(c) != level or g.kind.get(c) != "land":
                    return False
        return True

    def face(pos, target):
        return math.degrees(math.atan2(-(target[0] - pos[0]), -(target[1] - pos[1])))

    # ------------------------------------------------------------ hub: floor, paths, stalls
    with m.ctx(stage="buildings", folder="Buildings"):
        with m.at((hub[0], MAIN, hub[1])):
            with m.ctx(tier=1):
                m.octagon(0.25, FLOOR_R - 1.5, 0.6, C["dirt"])
            with m.ctx(tier=2):
                m.octagon(0.2, FLOOR_R, 0.6, C["path_border"])
                m.octagon(0.3, FLOOR_R - 1.4, 0.6, C["path"])
        fy = lambda x, z: MAIN
        path_strip(m, [(hub[0], hub[1] + FLOOR_R - 1), (g.wx(ci), g.wx(j - 5) - 1)], 10, C["path"], C["path_border"], fy)
        path_strip(m, [(hub[0] + FLOOR_R * 0.6, hub[1] - FLOOR_R * 0.7), (hill_stair_foot[0], hill_stair_foot[1] + 1)],
                   9, C["path"], C["path_border"], fy)
        path_strip(m, [(hub[0] - FLOOR_R + 1, hub[1] - 1), (g.wx(pc[0] + 8), g.wx(pc[1]) - 2)], 9, C["path"],
                   C["path_border"], fy)
    segs = [((hub[0], hub[1]), (g.wx(ci), g.wx(j - 5))), ((hub[0], hub[1]), hill_stair_foot),
            ((hub[0], hub[1]), (g.wx(pc[0] + 8), g.wx(pc[1]) - 2))]

    def near_path(x, z, r):
        for (ax, az), (bx, bz) in segs:
            dx_, dz_ = bx - ax, bz - az
            L2 = dx_ * dx_ + dz_ * dz_ or 1
            tt = max(0, min(1, ((x - ax) * dx_ + (z - az) * dz_) / L2))
            if math.hypot(x - ax - dx_ * tt, z - az - dz_ * tt) < r:
                return True
        return False

    exits = [90, math.degrees(math.atan2(hill_stair_foot[1] - hub[1], hill_stair_foot[0] - hub[0])), 180]
    kinds = {"market": ("FISH MARKET", P.ACCENTS["sky"], "#4FC3F7", "ShopPad_FishMarket", Bd.goods_fish, Bd.icon_fish),
             "shop": ("SPEAR SHOP", P.ACCENTS["red"], "#FF5A5A", "ShopPad_SpearShop", Bd.goods_spears, Bd.icon_spear),
             "upgrade": ("UPGRADES", "#FFC93C", "#FFB020", "ShopPad_Upgrades", Bd.goods_upgrades, Bd.icon_hammer)}
    stalls = []
    for name, want in (("market", 40), ("shop", 140), ("upgrade", -110)):
        best = None
        for da in range(-40, 41, 5):
            a = want + da
            if any(adiff(a, e) < 26 for e in exits):
                continue
            for r in (24, 27, 30):
                x, z = hub[0] + math.cos(math.radians(a)) * r, hub[1] + math.sin(math.radians(a)) * r
                ry = face((x, z), hub)
                ra = math.radians(ry)
                if flat(x, z, 16, 11, ry, MAIN) and flat(x - math.sin(ra) * 9, z - math.cos(ra) * 9, 9, 6, ry, MAIN) \
                        and all(math.hypot(x - q[1][0], z - q[1][1]) > 22 for q in stalls):
                    if best is None or abs(da) < best[0]:
                        best = (abs(da), (x, z), ry)
                    break
        if best:
            stalls.append((name, best[1], best[2]))
            keep.append((best[1], 13))
            print("   ", name, "stall at", [round(v) for v in best[1]])
    with m.ctx(stage="buildings", folder="Buildings"):
        for name, (x, z), ry in stalls:
            title, stripe, cloth, pad, goods, icon = kinds[name]
            with m.at((x, MAIN, z), ry=ry):
                Bd.simple_stall(m, title, stripe, cloth, pad, goods, icon=icon)
                with m.ctx(tier=3):
                    for s_ in (-1, 1):
                        m.box((s_ * 6.5, 13.0, 4.6), (0.3, 3.4, 0.3), C["wood_dark"])
                        m.box((s_ * 6.5 + 0.9 * s_, 14.2, 4.6), (1.6, 1.0, 0.15), stripe, collide=False)
        # portal marker on the ledge, facing the hub
        pb = Bd.portal_bounds()
        with m.at((portal_pos[0], PL, portal_pos[1]), ry=-90):
            m.box(((pb[0][0] + pb[1][0]) / 2, (pb[0][1] + pb[1][1]) / 2, (pb[0][2] + pb[1][2]) / 2),
                  (pb[1][0] - pb[0][0], pb[1][1] - pb[0][1], pb[1][2] - pb[0][2]), "#B67CFF",
                  name="PortalSpot", transparency=1.0, collide=False, shadow=False)
            with m.ctx(stage="props", folder="Props"):
                for s_ in (-1, 1):
                    with m.at((s_ * 9.5, 0, 8.0)):
                        P.bush(m, 70 + s_)
                    with m.at((s_ * 9.5, 0, -7.5)):
                        P.flowers(m, 75 + s_, ("pink", "sky") if s_ > 0 else ("yellow", "pink"))
        # lighthouse on the hill, door toward the stairs
        with m.at((hx, HILL, hz - 2)):
            Bd.lighthouse(m, C, beam_tier=3)

    # ------------------------------------------------------------ waterfall: hill west face -> pond on the lawn
    with m.ctx(stage="buildings", folder="Props"):
        wc = None
        for i in range(hi - 8, hi):
            c = (i, hj)
            if g.top.get(c) == HILL and g.top.get((i - 1, hj)) == MAIN:
                wc = c
                break
        if wc:
            ex = g.wx(wc[0]) - 2.1
            ez = g.wx(wc[1])
            pond = (ex - 12, ez + 2)
            with m.at((pond[0], MAIN, pond[1])):
                m.octagon(0.3, 7.2, 1.0, "#B9B4C8")
                with m.ctx(collide=False):
                    m.octagon(0.45, 6.2, 1.0, "#4FC3F7", mat="Glass")
                for k in range(3):
                    m.box((2.5 - k * 2.6, 1.0, (-1) ** k * 2.0), (1.6, 0.2, 1.6), "#4FA83A", ry=k * 25, collide=False)
            with m.at((ex, 0, ez), ry=90), m.ctx(collide=False, shadow=False):
                n = 4
                for k in range(n):
                    y0, y1 = HILL - (HILL - MAIN) * k / n, HILL - (HILL - MAIN) * (k + 1) / n
                    m.span((-3.2, y1 - 0.2, 1.6 + k * 0.45), (3.2, y0 + 0.4, 2.6 + k * 0.45),
                           "#6FD3FA" if k % 2 else "#4FC3F7", mat="Glass")
                    for xs in (-1.6, 1.2):
                        m.span((xs - 0.25, y1, 2.62 + k * 0.45), (xs + 0.25, y0, 2.8 + k * 0.45), "#FFFFFF")
                m.span((-3.5, HILL - 0.4, -6.0), (3.5, HILL + 0.35, 2.6), "#4FC3F7", mat="Glass")
                for k in range(3):
                    m.box((-2 + k * 2, MAIN + 0.9, 4.2 + k * 0.4), (1.8, 0.8, 1.8), "#FFFFFF", ry=k * 20)
            keep.append((pond, 10))

    # ------------------------------------------------------------ dock (tiers) over the reef
    dx, z0 = g.wx(ci), stair_foot_z
    while g.top_at(dx, z0 + 4) is not None:
        z0 += 4
    z0 += 1
    with m.ctx(stage="dock", folder="Dock"):
        with m.at((dx, 0, 0)):
            m.span((-6, 0, stair_foot_z), (6, BEACH + 0.3, z0), C["sand2"])          # sand ramp to the pier
            for k in range(2):
                m.span((-5.5, 2.0, z0 - 3.4 + k * 1.7), (5.5, 3.0 + 0.75 * (k + 1), z0 - 1.7 + k * 1.7),
                       C["wood_dark"] if k % 2 else C["wood"])
            with m.ctx(tier=1):
                Bd.dock_deck(m, -4, z0, 4, z0 + 22, DECK_Y, rails=("x0", "x1"))
                Bd.dock_deck(m, -10, z0 + 22, 10, z0 + 34, DECK_Y, along="x",
                             rails=("z1", "x0", "x1", ("z0", (-4.6, 4.6))))
                with m.at((7.5, DECK_Y, z0 + 31)):
                    P.lantern_post(m)
            T0, T1, TX = z0 + 30, z0 + 54, 28.0
            with m.ctx(tier=2):
                Bd.dock_deck(m, -5, z0, 5, T0, DECK_Y, rails=("x0", "x1"))
                Bd.dock_deck(m, -TX, T0, TX, T1, DECK_Y, along="x",
                             rails=("z1", ("x0", (T0 + 8, T0 + 16)), ("x1", (T0 + 8, T0 + 16)), ("z0", (-5.6, 5.6))))
                for x in (-TX + 2.2, TX - 2.2):
                    for z in (T0 + 2.2, T1 - 2.2):
                        with m.at((x, DECK_Y, z), ry=180 if x < 0 else 0):
                            P.lantern_post(m)
                for k, x in enumerate((-18, -6, 6, 18)):
                    with m.at((x, DECK_Y, T1 - 2.5)):
                        (P.spear_rack if k % 2 == 0 else P.fish_bucket)(m)
                with m.at((-14, DECK_Y, T0 + 3.5)):
                    P.ice_crate(m)
                with m.at((15, DECK_Y, T0 + 3.2)):
                    P.crate_cluster(m, 7)
                with m.at((0, DECK_Y, T0 - 0.8)):
                    for s_ in (-1, 1):
                        m.box((s_ * 5.4, 4.2, 0), (0.9, 8.4, 0.9), C["wood_dark"])
                    m.box((0, 8.6, 0), (12.4, 0.8, 1.0), C["wood_dark"])
                    board = m.box((0, 10.0, -0.1), (11.0, 2.2, 0.5), "#FFF1D6")
                    m.text(board, "SPEARFISHING", "#2A5DA8", "Front")
                    m.text(board, "SPEARFISHING", "#2A5DA8", "Back")
                for side in (-1, 1):
                    with m.at((side * (TX + 4.5), 0.2, T0 + 12)):
                        rowboat(m, C["wood"], C["wood_dark"], P.ACCENTS["white"])
            with m.ctx(tier=3):
                for side in (-1, 1):
                    xa, xb = (TX, TX + 16) if side > 0 else (-TX - 16, -TX)
                    Bd.dock_deck(m, xa, T0 + 6, xb, T0 + 18, DECK_Y, along="x",
                                 rails=("z0", "z1", "x1" if side > 0 else "x0"))
                    with m.at(((xa + xb) / 2, DECK_Y, T0 + 7.6)):
                        P.lantern_post(m)
                with m.at((-14, DECK_Y, (T0 + T1) / 2 + 2)):
                    for x in (-5, 5):
                        for z in (-4, 4):
                            m.box((x, 4.5, z), (0.8, 9, 0.8), C["wood_dark"])
                    for k in range(6):
                        m.box((-5 + k * 2, 9.2, 0), (2.0, 0.5, 10.4), P.ACCENTS["sky"] if k % 2 else "#FFFFFF")
    keep.append(((dx, z0 + 20), 30))

    # ------------------------------------------------------------ reef ring
    rng = random.Random(5)
    with m.ctx(stage="reef", folder="Reef"):
        colors = ["pink", "orange", "yellow", "sky", "lime", "purple"]
        spots = [(dx - 22, z0 + 66, 5.5), (dx + 26, z0 + 72, 5.0), (dx + 2, z0 + 84, 4.5),
                 (dx + 44, z0 + 46, 4.0), (dx - 44, z0 + 42, 4.0)]
        for k in range(10):
            a = math.radians(-90 + k * 32)
            r = 112
            x, z = math.cos(a) * r, math.sin(a) * r + 4
            if math.hypot(x - dx, z - z0 - 40) > 55:
                spots.append((x, z, rng.choice((3.5, 4.5, 5.5))))
        ci_ = 0
        for k, (x, z, h) in enumerate(spots):
            with m.at((x, -12, z), ry=rng.uniform(0, 90)):
                top = slab_stack(m, 100 + k, h, rng.uniform(10, 15), BANDS, cap=C["sea_sand"], taper=0.8,
                                 depth=rng.uniform(8, 12))
                with m.at((rng.uniform(-2, 2), top + 0.6, rng.uniform(-2, 2))):
                    P.coral_tubes(m, 200 + k, P.ACCENTS[colors[ci_ % 6]],
                                  tall=max(0.4, min(1.0, (-2.5 - (top - 11.4)) / 9.5)))
                ci_ += 1
                for jx in range(2):
                    a = rng.uniform(0, 6.28)
                    with m.at((math.cos(a) * 8.5, 0, math.sin(a) * 8.5)):
                        (P.coral_tubes, P.coral_fan, P.coral_branch)[(k + jx) % 3](m, 300 + k * 3 + jx,
                                                                                   P.ACCENTS[colors[ci_ % 6]])
                    ci_ += 1
                if k % 3 == 0:
                    with m.at((-7, 0, 5)):
                        P.kelp(m, 400 + k, height=rng.uniform(7, 8.5))

    # ------------------------------------------------------------ props
    with m.ctx(stage="props", folder="Props"):
        stair_rails(m, g, C)
        # lanterns: along the dock stairs, at the hub exits and the hill stairs
        with m.ctx(tier=2):
            for x, z in ((g.wx(ci) - 7.5, g.wx(j - 6)), (g.wx(ci) + 7.5, g.wx(j - 6)),
                         (hill_stair_foot[0] - 7.5, hill_stair_foot[1] + 2), (hill_stair_foot[0] + 7.5, hill_stair_foot[1] + 2),
                         (g.wx(pc[0] + 9), g.wx(pc[1]) + 4), (g.wx(pc[0] + 9), g.wx(pc[1]) - 8)):
                if g.top_at(x, z) == MAIN:
                    with m.at((x, MAIN, z)):
                        P.lantern_post(m)
        # beach: palm pairs, a camp, dune grass
        def water_near(c, r):
            return any((c[0] + a, c[1] + b) not in g.top for a in range(-r, r + 1) for b in range(-r, r + 1))
        beach_cells = sorted((c for c in g.top if g.kind[c] == "beach" and water_near(c, 3) and not water_near(c, 1)),
                             key=lambda c: math.atan2(g.wx(c[1]), g.wx(c[0])))
        palms_at = []
        camp = None
        for c in beach_cells[::4]:
            x, z = g.wx(c[0]), g.wx(c[1])
            if not clear(x, z, 8) or abs(x - dx) < 18 and z > 20:
                continue
            if camp is None and x > 30 and z > 0:
                camp = (x, z)
                with m.at((x, BEACH, z), ry=math.degrees(math.atan2(x, z))):
                    Bd.campfire(m)
                    for k, a in enumerate((0, 120, 240)):
                        r_ = math.radians(a)
                        with m.at((math.cos(r_) * 5.2, 0, math.sin(r_) * 5.2), ry=-a + 90):
                            Bd.log_seat(m)
                    with m.at((-2, 0, -10.5), ry=180):
                        Bd.tent(m)
                keep.append((camp, 14))
                continue
            if all(math.hypot(x - a, z - b) > 34 for a, b in palms_at + ([camp] if camp else [])):
                palms_at.append((x, z))
                for jj, off in enumerate((-1, 1)):
                    a_ = math.atan2(z, x) + off * 0.9
                    with m.at((x + math.cos(a_) * 3.6, BEACH, z + math.sin(a_) * 3.6), ry=-math.degrees(a_)):
                        P.palm(m, (2, 0)[jj], 1500 + len(palms_at) * 5 + jj)
                with m.at((x - math.cos(math.atan2(z, x)) * 3.5, BEACH, z - math.sin(math.atan2(z, x)) * 3.5)):
                    P.bush(m, 1550 + len(palms_at))
                with m.at((x + 2.5, BEACH, z + 3.0)):
                    P.flowers(m, 1560 + len(palms_at), ("pink", "yellow"))
                keep.append(((x, z), 6))
        # trees: clumps on the lawn and hill, open around the hub / paths
        trng = random.Random(31)
        trees_at = []
        cells = sorted(c for c in g.top if g.kind[c] == "land")
        trng.shuffle(cells)
        for c in cells:
            t = g.top[c]
            if not all(g.top.get((c[0] + a, c[1] + b)) == t for a in (-1, 0, 1) for b in (-1, 0, 1)):
                continue
            if any(g.kind.get((c[0] + a, c[1] + b)) == "path" for a in range(-2, 3) for b in range(-2, 3)):
                continue
            x, z = g.wx(c[0]) + trng.uniform(-1.2, 1.2), g.wx(c[1]) + trng.uniform(-1.2, 1.2)
            if math.hypot(x - hub[0], z - hub[1]) < 22 or not clear(x, z, 4) or near_path(x, z, 9):
                continue
            if noise2(x, z, 77, 30) < 0.22 or any(math.hypot(x - a, z - b) < 6.4 for a, b in trees_at):
                continue
            trees_at.append((x, z))
            with m.at((x, t, z), ry=trng.uniform(0, 360)):
                plant_tree(m, trng, t == MAIN, None, 1000 + len(trees_at))
            if len(trees_at) % 3 == 0:
                with m.at((x + 3.2, t, z + 1.6)):
                    (P.bush if len(trees_at) % 2 else P.flowers)(m, 1100 + len(trees_at))
        print("    trees", len(trees_at), "palm pairs", len(palms_at))
        # grass tufts on the lawns, dune grass on the beach
        tuft_at = []
        for c in sorted(g.top):
            t = g.top[c]
            if g.kind[c] == "path" or not all(g.top.get((c[0] + a, c[1] + b)) == t for a in (-1, 0, 1) for b in (-1, 0, 1)):
                continue
            if any(g.kind.get((c[0] + a, c[1] + b)) == "path" for a in (-1, 0, 1) for b in (-1, 0, 1)):
                continue
            x, z = g.wx(c[0]) + trng.uniform(-1.5, 1.5), g.wx(c[1]) + trng.uniform(-1.5, 1.5)
            if trng.random() > (0.55 if g.kind[c] == "land" else 0.18) or not clear(x, z, 1) or near_path(x, z, 6) or \
                    any(math.hypot(x - a, z - b) < 2.6 for a, b in trees_at) or \
                    (t == MAIN and math.hypot(x - hub[0], z - hub[1]) < FLOOR_R + 2):
                continue
            tuft_at.append((x, z))
            with m.at((x, t, z), ry=trng.uniform(0, 360)):
                if g.kind[c] == "land":
                    fl = (P.ACCENTS["yellow"], P.ACCENTS["white"], P.ACCENTS["pink"], None, None, None)[len(tuft_at) % 6]
                    P.tuft_cluster(m, 3000 + len(tuft_at), flower=fl)
                else:
                    P.tuft_cluster(m, 3000 + len(tuft_at), greens=("#9CCB5A", "#B8D86A", "#7FB34A"))
        print("    grass tuft clusters", len(tuft_at))
        # a flower cluster at each side of every stall and on both sides of each path mouth
        for k, (name, (x, z), ry) in enumerate(stalls):
            a = math.radians(ry)
            for s_ in (-1, 1):
                fx_, fz_ = x + math.cos(a) * 10 * s_ - math.sin(a) * -4, z - math.sin(a) * 10 * s_ - math.cos(a) * -4
                if g.top_at(fx_, fz_) == MAIN:
                    with m.at((fx_, MAIN, fz_)):
                        P.flowers(m, 1600 + k * 2 + (s_ > 0), ("red", "yellow") if s_ > 0 else ("pink", "sky"))
    # hero sea stacks
    with m.ctx(stage="terrain", folder="Terrain"):
        for k, ang in enumerate((205, 335)):
            a = math.radians(ang)
            x, z = math.cos(a) * 96, math.sin(a) * 96 + 4
            with m.at((x, -6, z), ry=ang):
                top = slab_stack(m, 40 + k, (24, 20)[k], 12, BANDS, cap=C["grass"], cap_strip=C["sand"])
                with m.ctx(stage="props", folder="Props"):
                    with m.at((1.5, top + 1.0, 0)):
                        P.bush(m, 50 + k)
                    with m.at((-2.5, top + 1.0, 2.0)):
                        P.flowers(m, 60 + k, ("pink", "yellow"))

    cams = {
        "overhead": ((150, 120, 210), (0, 8, 0), 32),
        "dock": ((dx, DECK_Y + 5.5, z0 + 52), (0, 18, -10), 26),
        "plaza": ((hub[0] - 2, MAIN + 6, hub[1] - 12), (hub[0] + 2, MAIN + 6, hub[1] + 30), 26),
        "village": ((hub[0] + 52, MAIN + 46, hub[1] + 62), (hub[0], MAIN, hub[1] - 4), 28),
        "lighthouse": ((hx + 30, HILL + 16, hz + 36), (hx, HILL + 16, hz), 28),
        "portal": ((portal_pos[0] + 34, PL + 9, portal_pos[1] + 14), (portal_pos[0], PL + 9, portal_pos[1]), 30),
        "dockdeck": ((dx + 46, DECK_Y + 22, z0 + 80), (dx, DECK_Y, z0 + 34), 28),
        "reef": ((dx + 20, DECK_Y + 3, z0 + 70), (dx, -10, z0 + 52), 26),
        "west": ((-150, 70, 60), (-10, 10, 0), 30),
    }
    for name, (x, z), ry in stalls:
        a = math.radians(ry)
        fx, fz = -math.sin(a), -math.cos(a)
        cams[name] = ((x + fx * 30 - fz * 10, MAIN + 12, z + fz * 30 + fx * 10), (x, MAIN + 7, z), 32)
    if camp:
        x, z = camp
        L = math.hypot(x, z) or 1
        cams["camp"] = ((x + x / L * 30 + z / L * 10, BEACH + 9, z + z / L * 30 - x / L * 10), (x, BEACH + 3, z), 30)
    if palms_at:
        bx, bz = palms_at[len(palms_at) // 2]
        L = math.hypot(bx, bz) or 1
        cams["beach"] = ((bx + bx / L * 34 + bz / L * 10, 9, bz + bz / L * 34 - bx / L * 10), (bx, 9, bz), 30)
    cams["stairs"] = ((dx + 10, 10, z0 + 14), (dx, 14, hub[1] - 10), 28)
    spawn = (hub[0], MAIN + 1.5, hub[1])
    water = (-260, -14, -260, 260, 0, 260)
    return m, PRESET, water, spawn, cams
