"""VoxelIsland (grass, starter island, origin 0,0,0) - maps/01_VoxelIsland_GRASS.md.

Keeps the original island's shape (terraces, mesas, spiral stair path to the summit, stone arch
top-left, dock bottom-left, plaza in the middle) and rebuilds it to the style bible:
calm 2-tone ground, banded slab cliffs, no clutter, clumped trees, lighthouse landmark on the
summit, Fish Market / Spear Shop / Upgrade Station facing the plaza, T-dock over a coral reef,
travel boat pier past the arch, Tier1/2/3.
"""
import math
import random

import buildings as Bd
import props as P
from core import Model
from terrain import slab_stack
from terraced import Grid, fence, find_spot, ground_and_cliffs, rowboat, stair_rails

C = dict(
    grass="#6CCB4A", grass2="#4FA83A", rock="#8A97E6", rock_dark="#5E6BC4", rock_light="#B3BCF2",
    rocktop="#A3ADEB", sand="#F3DC9A", sand2="#E8CC84", path="#A8A3B8", path_border="#8E89A0",
    wood="#9A6238", wood_dark="#6B4226", wall="#F1E3C2", roof="#4F7FD9", roof_trim="#3A5DA8",
    roof2="#B5523B", lh_red="#FF5A5A", lh_white="#F7F4EE", lamp="#FFE08A", dirt="#C9A27A",
    sail="#3FB75A", body="#5E6BC4", sea_sand="#EAD48E", sea_sand2="#DDC47C",
)
BANDS = (C["rock_light"], C["rock"], C["rock_dark"])
PRESET = dict(ClockTime=14, Brightness=2.5, Ambient="#7A86A8", OutdoorAmbient="#9AA6C8",
              EnvironmentDiffuseScale=0.5, EnvironmentSpecularScale=0.3,
              AtmosphereColor="#C7DFFF", AtmosphereDecay="#9FC4FF", AtmosphereDensity=0.25, AtmosphereHaze=1,
              CCTint="#FFFFFF", CCSaturation=0.15, CCContrast=0.05, BloomIntensity=0.4, WaterColor="#2E9BE6")
DECK_Y = 4.5
TREES = {"PineTreeSmall": 0, "PineTree": 1, "PineTreeTall": 2}


def build():
    m = Model("VoxelIsland")
    g = Grid("voxel")
    rng = random.Random(5)
    levels, height = ground_and_cliffs(m, g, C, seed=21, water_levels=(-1.5, -5.0, -12.0))

    px, PY, pz = g.landmarks["plaza"]
    peak = g.landmarks["peak"]
    old = g.props

    def first(name):
        return next((p for p in old if p[0] == name), None)

    PY = g.top[g.cell_of(px, pz)]                # the plaza floor (a round sunken bowl ~64 studs wide)
    PR = 15.0                                   # 30-stud centre floor + fountain; shops stand around it
    dock = first("Dock")
    dock_x, dock_z = dock[1], dock[3]
    arch = first("Arch")
    keep = [((px, pz), PR + 2), ((peak[0], peak[2]), 12), ((arch[1], arch[3]), 18), ((dock_x, dock_z), 10)]

    def ok_cell(c, level):
        return (c in g.top and abs(g.top[c] - level) < 0.6 and
                (g.kind[c] == "land" or c in g.plaza) and not (c in g.path and g.path[c][1] == "wood"))

    def ring_spot(angle, size, taken, level=PY, spread=60):
        """Spot around the plaza, facing its centre, whose whole (w x d) footprint is plaza-level ground."""
        w, d = size
        for da in sorted(range(-spread, spread + 1, 5), key=abs):
            for dist in [PR + d / 2 + k for k in (2, 4, 6, 9, 13)]:
                a_ = math.radians(angle + da)
                x, z = px + math.cos(a_) * dist, pz + math.sin(a_) * dist
                if any(math.hypot(x - tx, z - tz) < (w + tw) / 2 + 1 for (tx, tz), tw in taken):
                    continue
                fx, fz = -math.cos(a_), -math.sin(a_)           # front direction (toward the plaza)
                rx, rz = -fz, fx
                ok = True
                for u in range(-int(w / 2), int(w / 2) + 1, 2):
                    for v in range(-int(d / 2), int(d / 2) + 1, 2):
                        if not ok_cell(g.cell_of(x + rx * u + fx * v, z + rz * u + fz * v), level):
                            ok = False
                            break
                    if not ok:
                        break
                if ok:
                    return (x, z)
        return None

    spots, taken = {}, []
    for name, angle, size in (("market", 180, (22, 12)), ("shop", 0, (19, 15)), ("upgrade", -90, (30, 14))):
        r = max(size) / 2
        spot = ring_spot(angle, size, taken)
        if spot is None and name == "upgrade":       # the terrace toward the lighthouse, or beside the plaza
            for lvl in (34, 24, 44):
                spot = find_spot(g, (px, pz), 9.5, lvl, keep, lambda x, z: max(0, z - pz) * 4, rmin=30, rmax=90)
                if spot:
                    break
        else:
            lvl = PY
        if spot:
            spots[name] = (spot[0], lvl, spot[1])
            taken.append((spot, size[0]))
            keep.append((spot, r + 3))
            print("   ", name, "at", spots[name])

    def face(pos, target):
        return math.degrees(math.atan2(-(target[0] - pos[0]), -(target[1] - pos[1])))

    # ------------------------------------------------------------ hero rocks + sea stacks
    with m.ctx(stage="terrain", folder="Terrain"):
        stacks = sorted((p for p in old if p[0] in ("RockOutcropBig", "RockOutcrop")),
                        key=lambda p: (p[0] != "RockOutcropBig", p[1]))[:3]
        for k, p in enumerate(stacks):
            base = height(g.cell_of(p[1], p[3])) - 0.5
            with m.at((p[1], base, p[3]), ry=p[4]):
                top = slab_stack(m, 40 + k, (31, 26, 28)[k] - base * 0.0, 14, BANDS, cap=C["grass"],
                                 cap_strip=C["sand"])
                with m.ctx(stage="props", folder="Props"):
                    with m.at((1.5, top + 1.0, 0)):
                        P.bush(m, 50 + k)
                    with m.at((-2.5, top + 1.0, 2.0)):
                        P.flowers(m, 60 + k, ("pink", "yellow"))

    # ------------------------------------------------------------ reef ring (target style) + dock reef
    with m.ctx(stage="reef", folder="Reef"):
        colors = ["pink", "orange", "yellow", "sky", "lime", "purple"]
        edge_cells = [c for c, lv in levels.items() if lv == -12.0 and any(levels.get((c[0] + a, c[1] + b)) == -5.0
                                                                           for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
        edge_cells.sort(key=lambda c: math.atan2(g.wx(c[1]), g.wx(c[0])))
        spots_reef = [(dock_x - 16, dock_z + 58, 5.5), (dock_x + 26, dock_z + 64, 5.0), (dock_x + 4, dock_z + 76, 4.5),
                      (dock_x + 30, dock_z + 40, 4.0), (dock_x - 28, dock_z + 36, 4.0)]
        step = max(1, len(edge_cells) // 9)
        for c in edge_cells[::step]:
            x, z = g.wx(c[0]), g.wx(c[1])
            if math.hypot(x - dock_x, z - dock_z - 40) > 50:
                spots_reef.append((x, z, rng.choice((3.5, 4.5, 5.5))))
        ci = 0
        for k, (x, z, h) in enumerate(spots_reef):
            with m.at((x, -12, z), ry=rng.uniform(0, 90)):
                top = slab_stack(m, 100 + k, h, rng.uniform(10, 15), BANDS, cap=C["sea_sand"], taper=0.8,
                                 depth=rng.uniform(8, 12))
                with m.at((rng.uniform(-2, 2), top + 0.6, rng.uniform(-2, 2))):   # stays under the surface
                    P.coral_tubes(m, 200 + k, P.ACCENTS[colors[ci % 6]], tall=max(0.4, min(1.0, (-2.5 - (top - 11.4)) / 9.5)))
                ci += 1
                for j in range(2 if k < 5 else 1):     # the dock reef gets the most coral
                    a = rng.uniform(0, 6.28)
                    with m.at((math.cos(a) * 8.5, 0, math.sin(a) * 8.5)):
                        (P.coral_tubes, P.coral_fan, P.coral_branch)[(k + j) % 3](m, 300 + k * 3 + j,
                                                                                  P.ACCENTS[colors[ci % 6]])
                    ci += 1
                if k % 3 == 0:
                    with m.at((-7, 0, 5)):
                        P.kelp(m, 400 + k, height=rng.uniform(7, 8.5))

    # ------------------------------------------------------------ dock (tiers) + travel boat
    z0 = dock_z
    with m.ctx(stage="dock", folder="Dock"):
        with m.at((dock_x, 0, 0)):
            for k in range(2):
                m.span((-4.5, 2.0, z0 - 3 + k * 1.6), (4.5, 3.0 + 0.75 * (k + 1), z0 - 1.4 + k * 1.6),
                       C["wood_dark"] if k % 2 else C["wood"])
            with m.ctx(tier=1):
                Bd.dock_deck(m, -4, z0, 4, z0 + 24, DECK_Y, rails=("x0", "x1"))
                Bd.dock_deck(m, -7, z0 + 24, 7, z0 + 34, DECK_Y, along="x", rails=("z1",))
                with m.at((5.5, DECK_Y, z0 + 31)):
                    P.lantern_post(m)
                with m.at((-4.5, DECK_Y, z0 + 31), ry=90):
                    P.fish_bucket(m)
            T0, T1 = z0 + 36, z0 + 54
            with m.ctx(tier=2):
                Bd.dock_deck(m, -4, z0, 4, T0, DECK_Y, rails=("x0", "x1"))
                Bd.dock_deck(m, -17, T0, 17, T1, DECK_Y, along="x", rails=("z1", "x0", "x1"))
                for x in (-15.5, 15.5):
                    for z in (T0 + 1.5, T1 - 1.5):
                        with m.at((x, DECK_Y, z), ry=180 if x < 0 else 0):
                            P.lantern_post(m)
                with m.at((10.5, DECK_Y, T1 - 2.0)):
                    P.spear_rack(m, n=5)
                with m.at((10, DECK_Y, T0 + 1.8)):
                    P.ice_crate(m)
                with m.at((6.5, DECK_Y, T0 + 2.2)):
                    P.fish_bucket(m)
                with m.at((-6.0, DECK_Y, T1 - 2.2)):
                    P.rope_coil(m)
                with m.at((13.0, DECK_Y, T1 - 5.0)):
                    P.fish_bucket(m)
                with m.at((-13.5, DECK_Y, T1 - 3.0)):
                    P.crate(m, 2.4)
                with m.at((-10.5, DECK_Y, T0 + 1.2), ry=180):
                    P.sign_board(m, "SPEARFISHING", w=10, h=2.4, color="#FFF1D6", text_color="#2A5DA8", height=7.0)
            with m.ctx(tier=3):
                Bd.dock_deck(m, 17, T0 + 5, 34, T0 + 11, DECK_Y, along="x", rails=("z0", "z1"))
                Bd.dock_deck(m, 34, T0 - 3, 54, T0 + 13, DECK_Y, along="x", rails=("x1", "z0", "z1"))
                for x, z in ((36, T0 - 1.5), (52, T0 - 1.5), (52, T0 + 11.5)):
                    with m.at((x, DECK_Y, z)):
                        P.lantern_post(m)
                with m.at((44, DECK_Y, T0 + 11.0)):
                    P.spear_rack(m)
                with m.at((40, DECK_Y, T0 + 0.5)):
                    P.fish_bucket(m)
        for p in old:
            if p[0] == "Rowboat":
                with m.at((p[1], 0.2, p[3]), ry=p[4]):
                    rowboat(m, C["wood"], C["wood_dark"], P.ACCENTS["white"])
        # travel pier: from the arch, out to the nearest water, with the green-sailed boat
        ax, az = arch[1], arch[3]
        L = math.hypot(ax, az)
        ux, uz = ax / L, az / L
        t = 0.0
        while g.top_at(ax + ux * t, az + uz * t) is not None and t < 200:
            t += 2
        sx, sz = ax + ux * (t - 4), az + uz * (t - 4)
        ry = math.degrees(math.atan2(ux, uz))
        with m.at((sx, 0, sz), ry=ry):            # local +Z = out to sea
            Bd.dock_deck(m, -3.5, 0, 3.5, 26, DECK_Y, rails=("x0",))
            with m.at((9.5, 0, 16), ry=180):
                Bd.sailboat(m, C["sail"])
            with m.at((-2.0, DECK_Y, 3.0), ry=180):
                P.sign_board(m, "TRAVEL", w=6, h=2, color="#FFF1D6", text_color="#2E8B57", height=5.0)
            with m.at((-2.6, DECK_Y, 23)):
                P.lantern_post(m)

    # ------------------------------------------------------------ buildings
    with m.ctx(stage="buildings", folder="Buildings"):
        with m.at((px, PY, pz)):
            with m.ctx(tier=1):
                m.octagon(0.2, PR - 2, 0.6, C["dirt"])
                Bd.well(m)
            with m.ctx(tier=2):
                m.octagon(0.2, PR, 0.6, C["path_border"])
                m.octagon(0.3, PR - 1.5, 0.6, C["path"])
                m.octagon(0.36, 9.0, 0.6, "#B9B4C8")
                m.octagon(0.42, 7.6, 0.6, C["path"])
                Bd.fountain(m, C)
        for name, fn, seed in (("market", Bd.fish_market, 1), ("shop", Bd.spear_shop, 2)):
            if name not in spots:
                continue
            x, y, z = spots[name]
            with m.at((x, y, z), ry=face((x, z), (px, pz))):
                with m.ctx(tier=1):
                    fn(m, 1, C, seed)
                with m.ctx(tier=2):
                    fn(m, 2, C, seed)
        if "upgrade" in spots:
            x, y, z = spots["upgrade"]
            with m.at((x, y, z), ry=face((x, z), (px, pz))):
                with m.ctx(tier=1):
                    Bd.upgrade_station(m, 1, C)
                with m.ctx(tier=2):
                    Bd.upgrade_station(m, 2, C)
        ly = g.top_at(peak[0], peak[2]) or peak[1]
        with m.at((peak[0], ly, peak[2]), ry=face((peak[0], peak[2]), (dock_x, dock_z))):
            Bd.lighthouse(m, C, beam_tier=3)
        with m.at((arch[1], arch[2] - 0.5, arch[3]), ry=arch[4]):
            Bd.stone_arch(m, BANDS, C["grass"], half=13.0)
        cave = first("CaveEntrance")
        if cave:
            with m.at((cave[1], cave[2], cave[3]), ry=cave[4] + 180):
                m.span((-5, 0, -1.0), (5, 9, 0.6), "#2A2E45")
                for s in (-1, 1):
                    m.span((s * 5 - 0.7, 0, -1.6), (s * 5 + 0.7, 10, 0.2), C["wood_dark"])
                m.span((-6, 9, -1.6), (6, 10.4, 0.2), C["wood_dark"])
                with m.at((6.5, 0, -2.5)):
                    P.lantern_post(m, h=8)
        flag = first("FlagFrame")
        if flag:
            with m.at((flag[1], flag[2], flag[3]), ry=flag[4]):
                m.box((0, 0.5, 0), (2.4, 1.0, 2.4), P.STONE_DK)
                m.box((0, 8, 0), (0.7, 16, 0.7), C["wood_dark"])
                with m.ctx(collide=False):
                    m.box((0, 13.6, -3.2), (0.3, 4.2, 6.2), P.ACCENTS["sky"])
                    with m.at((0, 13.6, -3.4), ry=90):
                        Bd.fish_icon(m, 3.6, P.ACCENTS["white"], P.ACCENTS["orange"])

    # ------------------------------------------------------------ props: trees, beach palms, rails,
    # lanterns, flower / bush clusters (no scattered clutter)
    blocked = keep + [((dock_x, dock_z + 20), 26)]

    def clear(x, z, r=0):
        return all(math.hypot(x - a, z - b) > rr + r for (a, b), rr in blocked)

    # ------------------------------------------------------------ waterfall from a terrace into a pond
    best = None
    for c, t in g.top.items():
        if g.kind[c] != "land" or abs(t - 24) > 0.6:
            continue
        x, z = g.wx(c[0]), g.wx(c[1])
        dd = math.hypot(x - px, z - pz)
        if not 40 < dd < 95 or not clear(x, z, 9):
            continue
        for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            up = (c[0] + d[0], c[1] + d[1])
            up2 = (c[0] + 2 * d[0], c[1] + 2 * d[1])
            if g.kind.get(up) != "land" or g.top.get(up, 0) < t + 9 or g.top.get(up2, 0) < t + 9:
                continue
            pc = (c[0] - 2 * d[0], c[1] - 2 * d[1])           # pond centre, two cells out from the cliff
            if all(g.kind.get((pc[0] + a, pc[1] + b)) == "land" and abs(g.top.get((pc[0] + a, pc[1] + b), 0) - t) < 0.6
                   for a in range(-2, 3) for b in range(-2, 3)):
                if best is None or dd < best[0]:
                    best = (dd, c, d, pc, g.top[up])
    if best:
        _, c, d, pc, upper = best
        fy = g.top[c]
        with m.ctx(stage="buildings", folder="Props"):
            with m.at((g.wx(pc[0]), fy, g.wx(pc[1]))):
                m.octagon(0.3, 7.2, 1.0, "#B9B4C8")
                with m.ctx(collide=False):
                    m.octagon(0.45, 6.2, 1.0, "#4FC3F7", mat="Glass")
                for k in range(3):        # lily pads
                    m.box((2.5 - k * 2.6, 1.0, (-1) ** k * 2.0), (1.6, 0.2, 1.6), "#4FA83A", ry=k * 25, collide=False)
            ex, ez = g.wx(c[0]) + d[0] * 2.1, g.wx(c[1]) + d[1] * 2.1     # the cliff face
            # local +Z points away from the cliff (toward the pond); the fall hangs in front of the slabs
            with m.at((ex, 0, ez), ry=math.degrees(math.atan2(-d[0], -d[1]))), m.ctx(collide=False, shadow=False):
                n = 4
                for k in range(n):
                    y0, y1 = upper - (upper - fy) * k / n, upper - (upper - fy) * (k + 1) / n
                    m.span((-3.2, y1 - 0.2, 1.6 + k * 0.45), (3.2, y0 + 0.4, 2.6 + k * 0.45),
                           "#6FD3FA" if k % 2 else "#4FC3F7", mat="Glass")
                    for xs in (-1.6, 1.2):          # white streaks on every step of the fall
                        m.span((xs - 0.25, y1, 2.62 + k * 0.45), (xs + 0.25, y0, 2.8 + k * 0.45), "#FFFFFF")
                m.span((-3.5, upper - 0.4, -6.0), (3.5, upper + 0.35, 2.6), "#4FC3F7", mat="Glass")   # channel on top
                for k in range(3):        # foam where it lands
                    m.box((-2 + k * 2, fy + 0.9, 4.2 + k * 0.4), (1.8, 0.8, 1.8), "#FFFFFF", ry=k * 20)
        blocked.append(((g.wx(pc[0]), g.wx(pc[1])), 10))
        print("    waterfall at", (g.wx(c[0]), fy, g.wx(c[1])), "drop", upper - fy)

    with m.ctx(stage="props", folder="Props"):
        # trees: every original tree spot that is clear of the buildings; oaks around the village
        kept = []
        for p in sorted((p for p in old if p[0] in TREES and clear(p[1], p[3], 4)), key=lambda p: (p[1], p[3])):
            if len(kept) < 78 and all(math.hypot(p[1] - q[1], p[3] - q[3]) > 6.5 for q in kept):
                kept.append(p)
        for k, p in enumerate(kept):
            with m.at((p[1], p[2], p[3]), ry=p[4]):
                if math.hypot(p[1] - px, p[3] - pz) < 80 and k % 3 != 0:
                    P.oak(m, (0, 1, 2)[k % 3], 1000 + k)
                else:
                    P.pine(m, TREES[p[0]], 1000 + k)
        # beach: palm clumps (2-3 palms + bush + flowers at the base) and hero rocks
        def water_near(c, r):
            return any((c[0] + a, c[1] + b) not in g.top for a in range(-r, r + 1) for b in range(-r, r + 1))

        def cliff_near(c, r):
            return any(g.top.get((c[0] + a, c[1] + b), 0) > g.top[c] + 2 for a in range(-r, r + 1) for b in range(-r, r + 1))

        # open beach near the waterline (not right at the edge, not under a cliff)
        beach_cells = [c for c in g.top if g.kind[c] == "beach" and water_near(c, 3) and not water_near(c, 1)
                       and not cliff_near(c, 3)]
        beach_cells.sort(key=lambda c: math.atan2(g.wx(c[1]), g.wx(c[0])))
        palms_at, rocks_at = [], []
        for c in beach_cells[::7]:
            x, z = g.wx(c[0]), g.wx(c[1])
            near_path = any(g.kind.get((c[0] + a, c[1] + b)) == "path" for a in range(-3, 4) for b in range(-3, 4))
            if near_path or not clear(x, z, 8):
                continue
            if len(rocks_at) < 3 and all(math.hypot(x - a, z - b) > 90 for a, b in rocks_at + palms_at) \
                    and len(palms_at) >= len(rocks_at) * 2:
                rocks_at.append((x, z))
                with m.ctx(stage="terrain", folder="Terrain"), m.at((x, g.top[c] - 1, z), ry=(c[0] * 37) % 360):
                    slab_stack(m, 70 + len(rocks_at), 9, 10, BANDS, cap=C["grass"], cap_strip=C["sand"], taper=0.7)
                with m.at((x + 6.5, g.top[c], z + 1.5)):
                    P.flowers(m, 80 + len(rocks_at), ("red", "yellow", "pink"))
                with m.at((x - 5.0, g.top[c], z - 4.0)):
                    P.bush(m, 85 + len(rocks_at))
            elif len(palms_at) < 7 and all(math.hypot(x - a, z - b) > 45 for a, b in palms_at + rocks_at):
                palms_at.append((x, z))
                n = 3 if len(palms_at) % 2 else 2
                for j in range(n):
                    a_ = j * 2.4 + c[0]
                    with m.at((x + math.cos(a_) * 4.5, g.top[c], z + math.sin(a_) * 4.5), ry=(j * 140 + c[1] * 13) % 360):
                        P.palm(m, (2, 1, 0)[j], 1500 + len(palms_at) * 5 + j)
                with m.at((x + 1.0, g.top[c], z - 1.5)):
                    P.bush(m, 1550 + len(palms_at))
                with m.at((x - 2.5, g.top[c], z + 3.0)):
                    P.flowers(m, 1560 + len(palms_at), ("pink", "yellow"))
        bushes, flowers = [], []
        for p in old:
            if p[0] == "Bush" and len(bushes) < 10 and clear(p[1], p[3], 2) and \
                    any(math.hypot(p[1] - q[1], p[3] - q[3]) < 14 for q in kept) and \
                    all(math.hypot(p[1] - a, p[3] - b) > 20 for a, b in bushes):
                bushes.append((p[1], p[3]))
                with m.at((p[1], p[2], p[3])):
                    P.bush(m, 1100 + len(bushes))
            if p[0] == "Flowers" and len(flowers) < 14 and clear(p[1], p[3], 2):
                c = g.cell_of(p[1], p[3])
                near_path = any(g.kind.get((c[0] + a, c[1] + b)) == "path" for a in (-1, 0, 1) for b in (-1, 0, 1))
                if near_path and all(math.hypot(p[1] - a, p[3] - b) > 22 for a, b in flowers):
                    flowers.append((p[1], p[3]))
                    with m.at((p[1], p[2], p[3])):
                        P.flowers(m, 1200 + len(flowers), (("red", "yellow"), ("pink", "yellow"), ("red", "pink"))[len(flowers) % 3])
        # railings: proper stair rails on the wooden stairs, fences only along the stone paths
        stair_rails(m, g, C)
        wood = {c for c, v in g.path.items() if v[1] == "wood"}
        for p in old:
            c = g.cell_of(p[1], p[3])
            if p[0] == "Fence" and clear(p[1], p[3], 1) and not any((c[0] + a, c[1] + b) in wood
                                                                    for a in (-1, 0, 1) for b in (-1, 0, 1)):
                fence(m, p[1], p[2], p[3], p[4], C["wood"], C["wood_dark"])
        with m.ctx(tier=2):
            for p in old:
                if p[0] in ("Torch", "LampPost") and clear(p[1], p[3], 1) and p[2] > 3.5:
                    with m.at((p[1], p[2], p[3]), ry=p[4]):
                        P.lantern_post(m)
            for k, a in enumerate((45, 135, 225, 315)):
                r = math.radians(a)
                with m.at((px + math.cos(r) * (PR * 0.66), PY + 0.4, pz + math.sin(r) * (PR * 0.66)),
                          ry=math.degrees(math.atan2(math.cos(r), math.sin(r)))):
                    for s_ in (-1, 1):
                        with m.at((s_ * 3.6, 0, 0)):
                            P.bench(m)
        with m.ctx(tier=3):    # bunting across the plaza + flower boxes by the shops
            poles = [(px + math.cos(math.radians(a)) * (PR - 1), pz + math.sin(math.radians(a)) * (PR - 1))
                     for a in (25, 155, 205, 335)]
            for (x, z) in poles:
                m.box((x, PY + 6, z), (0.7, 12, 0.7), C["wood_dark"])
            flags = ["red", "yellow", "sky", "pink", "lime"]
            for (ax_, az_), (bx, bz) in ((poles[0], poles[2]), (poles[1], poles[3])):
                L = math.hypot(bx - ax_, bz - az_)
                n = int(L / 2.2)
                with m.ctx(collide=False, shadow=False):
                    m.beam((ax_, PY + 11.4, az_), (bx, PY + 11.4, bz), 0.15, P.ROPE)
                    for k in range(1, n):
                        t = k / n
                        sag = 1.6 * math.sin(math.pi * t)
                        x, z = ax_ + (bx - ax_) * t, az_ + (bz - az_) * t
                        with m.at((x, PY + 10.8 - sag, z), ry=math.degrees(math.atan2(bx - ax_, bz - az_)) + 90):
                            m.box((0, 0, 0), (1.2, 1.2, 0.15), P.ACCENTS[flags[k % 5]], rz=45)
            for k, name in enumerate(("market", "shop")):
                if name in spots:
                    x, y, z = spots[name]
                    ang = math.radians(face((x, z), (px, pz)))
                    fx, fz = -math.sin(ang), -math.cos(ang)
                    with m.at((x + fx * 9 + fz * 8, y, z + fz * 9 - fx * 8), ry=face((x, z), (px, pz))):
                        P.planter(m, 1400 + k)

    cams = {
        "overhead": ((235, 165, 335), (0, 22, 0), 30),
        "dock": ((dock_x, DECK_Y + 5.5, z0 + 52), (6, 45, 0), 24),
        "plaza": ((px + 3, PY + 5.5, pz + PR + 12), (px - 2, PY + 7, pz - 30), 20),
        "village": ((px + 75, PY + 60, pz + 75), (px, PY, pz - 8), 28),
        "lighthouse": ((peak[0] + 45, ly + 25, peak[2] + 45), (peak[0], ly + 18, peak[2]), 28),
        "reef": ((dock_x + 20, DECK_Y + 3, z0 + 62), (dock_x, -10, z0 + 46), 26),
        "cliffs": ((120, 40, 150), (70, 22, 80), 30),
    }
    for name, (x, y, z) in spots.items():     # close-ups in front of each building
        ang = math.radians(face((x, z), (px, pz)))
        fx, fz = -math.sin(ang), -math.cos(ang)
        cams[name] = ((x + fx * 34 - fz * 12, y + 20, z + fz * 34 + fx * 12), (x, y + 5, z), 32)
    if palms_at:
        bx, bz = palms_at[0]
        L = math.hypot(bx, bz) or 1
        cams["beach"] = ((bx + bx / L * 46 + bz / L * 14, 9, bz + bz / L * 46 - bx / L * 14), (bx, 9, bz), 30)
        print("    palm clumps", [(round(a), round(b)) for a, b in palms_at])
    cams["stairs"] = ((dock_x + 10, 14, dock_z + 16), (dock_x, 20, dock_z - 40), 28)
    if best:
        wx_, wz_ = g.wx(best[1][0]), g.wx(best[1][1])
        cams["waterfall"] = ((wx_ - best[2][0] * 36 + 12, 36, wz_ - best[2][1] * 36 + 12), (wx_, 28, wz_), 30)
    spawn = (px + 4, PY + 1.5, pz + PR * 0.5)
    water = (-300, -14, -300, 300, 0, 300)
    return m, PRESET, water, spawn, cams
