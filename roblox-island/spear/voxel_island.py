"""VoxelIsland (grass, starter island, origin 0,0,0) - maps/01_VoxelIsland_GRASS.md.

Keeps the original island's shape (terraces, mesas, spiral stair path to the summit, stone arch
top-left, dock bottom-left) and rebuilds it to the style bible.

Hub: the old sunken plaza bowl is flattened into an open plateau with a plain stone floor (no
centerpiece). Three simple shop stalls (Fish Market, Spear Shop, Upgrades) stand around its edge
where no path comes in, each with a glowing pad. Next to the hub a rock cliff with wide stairs holds
the portal (stone ring, glowing rim, spinning swirl, particles). Places to go: the hub, the portal
cliff, the big T-dock over the reef, the beach camp, the fishing jetty, the waterfall pond, the
lighthouse, the cave, the arch + travel boat.
"""
import math
import random

import buildings as Bd
import props as P
from core import Model
from terrain import path_strip, slab_stack, stairs
from terraced import DIRS, Grid, fence, ground_and_cliffs, rowboat, stair_rails

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
HUB_R = 66.0          # flattened plateau radius
FLOOR_R = 16.0        # stone floor radius


def plant_tree(m, rnd, near_hub, size=None, seed=0):
    """Pick a tree type by zone: fruit / blossom / oak / birch near the village, pines, birches and poplars
    further out."""
    size = rnd.choice((0, 1, 1, 2)) if size is None else size
    pick = rnd.random()
    if near_hub:
        fn = P.oak if pick < 0.34 else P.apple if pick < 0.52 else P.cherry if pick < 0.7 else P.birch if pick < 0.86 else P.poplar
    else:
        fn = P.pine if pick < 0.5 else P.birch if pick < 0.68 else P.poplar if pick < 0.82 else P.oak if pick < 0.94 else P.cherry
    fn(m, size, seed)


def adiff(a, b):
    return abs((a - b + 180) % 360 - 180)


def build():
    m = Model("VoxelIsland")
    g = Grid("voxel")
    rng = random.Random(5)
    old = g.props
    px, _, pz = g.landmarks["plaza"]
    peak = g.landmarks["peak"]
    HY = g.top[g.cell_of(px, pz)]

    def first(name):
        return next((p for p in old if p[0] == name), None)

    # ------------------------------------------------------------ open the hub: flatten the bowl
    rising = {c for c in g.top if g.kind[c] == "path" and g.top[c] > HY + 1.5}

    def near_rising(c, r):
        return any((c[0] + a, c[1] + b) in rising for a in range(-r, r + 1) for b in range(-r, r + 1))

    changed = set()
    for c, t in list(g.top.items()):
        d = math.hypot(g.wx(c[0]) - px, g.wx(c[1]) - pz)
        if d > HUB_R or g.kind[c] == "beach" or c in rising or near_rising(c, 2):
            continue
        if HY - 1.6 < t <= 36 and abs(t - HY) > 1e-6 or (g.kind[c] == "path" and abs(t - HY) < 1e-6):
            g.top[c] = HY
            changed.add(c)
            if g.kind[c] == "path" and not (c in g.path and g.path[c][1] == "wood"):
                g.kind[c], g.surf[c] = "land", "grass"          # the old grey bowl becomes lawn
    for c in changed:
        if g.kind[c] == "path":
            g.kind[c], g.surf[c] = "land", "grass"
    # exits: groups of path cells touching the flattened area -> one stone path from the floor edge to each
    border = {c for c in g.top if c not in changed and g.kind[c] == "path"
              and any((c[0] + d[0], c[1] + d[1]) in changed for d in DIRS)}
    exits, seen = [], set()
    for c in sorted(border):
        if c in seen:
            continue
        group, todo = [], [c]
        seen.add(c)
        while todo:
            q = todo.pop()
            group.append(q)
            for a in (-1, 0, 1):
                for b in (-1, 0, 1):
                    n = (q[0] + a, q[1] + b)
                    if n in border and n not in seen:
                        seen.add(n)
                        todo.append(n)
        near = min(group, key=lambda q: math.hypot(g.wx(q[0]) - px, g.wx(q[1]) - pz))
        f = next((near[0] + d[0], near[1] + d[1]) for d in DIRS if (near[0] + d[0], near[1] + d[1]) in changed)
        a = math.degrees(math.atan2(g.wx(f[1]) - pz, g.wx(f[0]) - px))
        if all(adiff(a, e[0]) > 30 for e in exits):
            exits.append((a, f))
    print("    hub exits at", sorted(round(a) for a, _ in exits))

    dock = first("Dock")
    dock_x, dock_z = dock[1], dock[3]
    arch = first("Arch")

    def face(pos, target):
        return math.degrees(math.atan2(-(target[0] - pos[0]), -(target[1] - pos[1])))

    def flat_footprint(x, z, ry, w, d, level=HY):
        a = math.radians(ry)
        rx_, rz_ = math.cos(a), -math.sin(a)
        fx, fz = math.sin(a), math.cos(a)
        for u in range(-int(w / 2), int(w / 2) + 1, 2):
            for v in range(-int(d / 2), int(d / 2) + 1, 2):
                c = g.cell_of(x + rx_ * u + fx * v, z + rz_ * u + fz * v)
                if c not in g.top or abs(g.top[c] - level) > 0.3 or g.kind[c] != "land":
                    return False
        return True

    # ------------------------------------------------------------ hub layout: 3 stalls around the floor
    exit_angles = [a for a, _ in exits]
    stalls, taken = [], []
    placed_xy = []
    for ex_clear, sep in ((22, 0), (18, 0), (14, 0)):
        for name in ("market", "shop", "upgrade"):
            if any(s_[0] == name for s_ in stalls):
                continue
            best = None
            for a in range(0, 360, 5):
                if any(adiff(a, t) < ex_clear for t in exit_angles):
                    continue
                for r in (28, 31, 34, 38, 42):
                    x, z = px + math.cos(math.radians(a)) * r, pz + math.sin(math.radians(a)) * r
                    if any(math.hypot(x - qx, z - qz) < 24 for qx, qz in placed_xy):
                        continue
                    ry = face((x, z), (px, pz))
                    ra = math.radians(ry)
                    if flat_footprint(x, z, ry, 16, 11) and \
                            flat_footprint(x - math.sin(ra) * 9, z - math.cos(ra) * 9, ry, 9, 6):
                        score = adiff(a, 90)          # prefer the dock side so the shops are seen from the pier
                        if best is None or score < best[0]:
                            best = (score, a, (x, z), ry)
                        break
            if best:
                stalls.append((name, best[2], best[3]))
                taken.append(best[1])
                placed_xy.append(best[2])
                print("   ", name, "stall at", [round(v) for v in best[2]], "angle", best[1])

    # ------------------------------------------------------------ portal cliff: a 7x7-cell plateau raised
    # into the terrain grid (so its walls are normal banded slab cliffs) with stone steps down to the hub
    CH = 9.0
    portal_at, best = None, None
    for cc, t in g.top.items():
        x, z = g.wx(cc[0]), g.wx(cc[1])
        dd = math.hypot(x - px, z - pz)
        if not 42 <= dd <= 84:
            continue
        a = math.degrees(math.atan2(z - pz, x - px))
        if any(adiff(a, e) < 26 for e in exit_angles) or any(adiff(a, t2) < 34 for t2 in taken):
            continue
        d = max(DIRS, key=lambda d: d[0] * (px - x) + d[1] * (pz - z))      # face the hub
        plat = [(cc[0] + i, cc[1] + j) for i in range(-3, 4) for j in range(-3, 4)]
        if not all(q in g.top and g.kind[q] not in ("path", "beach") and HY - 0.3 <= g.top[q] <= HY + CH + 12
                   for q in plat):
            continue
        u = (abs(d[1]), abs(d[0]))
        steps = [(cc[0] + d[0] * (4 + k) + u[0] * w, cc[1] + d[1] * (4 + k) + u[1] * w)
                 for k in range(5) for w in (-1, 0, 1)]
        if not all(q in g.top and abs(g.top[q] - HY) < 0.3 and g.kind[q] == "land" for q in steps):
            continue
        land_in_front = [(cc[0] + d[0] * (9 + k) + u[0] * w, cc[1] + d[1] * (9 + k) + u[1] * w) for k in range(2)
                         for w in (-1, 0, 1)]
        if not all(q in g.top and abs(g.top[q] - HY) < 0.3 for q in land_in_front):
            continue
        score = abs(dd - 56) + adiff(a, -60) * 0.2
        if best is None or score < best[0]:
            best = (score, cc, d, plat, steps, a)
    if best:
        _, cc, d, plat, steps, a = best
        for q in plat:
            g.top[q] = HY + CH
            g.kind[q], g.surf[q] = "land", "grass"
            changed.discard(q)
        for q in steps:
            k = (q[0] - cc[0]) * d[0] + (q[1] - cc[1]) * d[1] - 4      # 0 at the platform, 4 at the hub
            g.top[q] = HY + CH * (5 - k) / 6.0
            g.kind[q], g.surf[q] = "path", ""
            g.path[q] = (g.top[q], "cobble", (float(d[0]), float(d[1])), 0.0)
        x, z = g.wx(cc[0]), g.wx(cc[1])
        portal_at = ((x, z), math.degrees(math.atan2(-d[0], -d[1])), a, d)
        taken.append(a)
    print("    portal cliff at", portal_at and [round(v) for v in portal_at[0]])

    levels, height = ground_and_cliffs(m, g, C, seed=21, water_levels=(-1.5, -5.0, -12.0))

    stall_y = {name: HY for name, _, _ in stalls}
    if "upgrade" not in stall_y:      # on a terrace toward the lighthouse (spec: between the shops and the landmark)
        best_u = None
        for c, t in g.top.items():
            if g.kind[c] != "land" or c in changed or not HY - 12 <= t <= HY + 30 or abs(t - HY) < 0.5:
                continue
            x, z = g.wx(c[0]), g.wx(c[1])
            dd = math.hypot(x - px, z - pz)
            if not 40 < dd < 170:
                continue
            ry = face((x, z), (px, pz))
            if not flat_footprint(x, z, ry, 17, 10, level=t):
                continue
            a = math.radians(ry)            # the pad in front must be on the same level too
            if not flat_footprint(x - math.sin(a) * 9, z - math.cos(a) * 9, ry, 9, 6, level=t):
                continue
            near_path = any(g.kind.get((c[0] + i, c[1] + j)) == "path" for i in range(-4, 5) for j in range(-4, 5))
            score = dd + (0 if near_path else 40) + abs(math.atan2(z - pz, x - px) + math.pi / 2) * 30
            if best_u is None or score < best_u[0]:
                best_u = (score, (x, z), ry, t)
        if best_u:
            stalls.append(("upgrade", best_u[1], best_u[2]))
            stall_y["upgrade"] = best_u[3]
            print("    upgrade stall (terrace) at", [round(v) for v in best_u[1]], "y", best_u[3])

    keep = [((px, pz), FLOOR_R + 14), ((peak[0], peak[2]), 12), ((arch[1], arch[3]), 18), ((dock_x, dock_z), 10)]
    keep += [(pos, 15) for _, pos, _ in stalls]
    if portal_at:
        keep.append((portal_at[0], 22))

    # ------------------------------------------------------------ hero sea stacks
    with m.ctx(stage="terrain", folder="Terrain"):
        stacks = sorted((p for p in old if p[0] in ("RockOutcropBig", "RockOutcrop")),
                        key=lambda p: (p[0] != "RockOutcropBig", p[1]))[:3]
        for k, p in enumerate(stacks):
            base = height(g.cell_of(p[1], p[3])) - 0.5
            with m.at((p[1], base, p[3]), ry=p[4]):
                top = slab_stack(m, 40 + k, (31, 26, 28)[k], 14, BANDS, cap=C["grass"], cap_strip=C["sand"])
                with m.ctx(stage="props", folder="Props"):
                    with m.at((1.5, top + 1.0, 0)):
                        P.bush(m, 50 + k)
                    with m.at((-2.5, top + 1.0, 2.0)):
                        P.flowers(m, 60 + k, ("pink", "yellow"))

    # ------------------------------------------------------------ reef ring + dock reef
    with m.ctx(stage="reef", folder="Reef"):
        colors = ["pink", "orange", "yellow", "sky", "lime", "purple"]
        edge_cells = [c for c, lv in levels.items() if lv == -12.0 and any(levels.get((c[0] + a, c[1] + b)) == -5.0
                                                                           for a, b in DIRS)]
        edge_cells.sort(key=lambda c: math.atan2(g.wx(c[1]), g.wx(c[0])))
        spots_reef = [(dock_x - 22, dock_z + 74, 5.5), (dock_x + 30, dock_z + 80, 5.0), (dock_x + 4, dock_z + 92, 4.5),
                      (dock_x + 46, dock_z + 54, 4.0), (dock_x - 44, dock_z + 50, 4.0)]
        step = max(1, len(edge_cells) // 9)
        for c in edge_cells[::step]:
            x, z = g.wx(c[0]), g.wx(c[1])
            if math.hypot(x - dock_x, z - dock_z - 50) > 60:
                spots_reef.append((x, z, rng.choice((3.5, 4.5, 5.5))))
        ci = 0
        for k, (x, z, h) in enumerate(spots_reef):
            with m.at((x, -12, z), ry=rng.uniform(0, 90)):
                top = slab_stack(m, 100 + k, h, rng.uniform(10, 15), BANDS, cap=C["sea_sand"], taper=0.8,
                                 depth=rng.uniform(8, 12))
                with m.at((rng.uniform(-2, 2), top + 0.6, rng.uniform(-2, 2))):
                    P.coral_tubes(m, 200 + k, P.ACCENTS[colors[ci % 6]],
                                  tall=max(0.4, min(1.0, (-2.5 - (top - 11.4)) / 9.5)))
                ci += 1
                for j in range(2 if k < 5 else 1):
                    a = rng.uniform(0, 6.28)
                    with m.at((math.cos(a) * 8.5, 0, math.sin(a) * 8.5)):
                        (P.coral_tubes, P.coral_fan, P.coral_branch)[(k + j) % 3](m, 300 + k * 3 + j,
                                                                                  P.ACCENTS[colors[ci % 6]])
                    ci += 1
                if k % 3 == 0:
                    with m.at((-7, 0, 5)):
                        P.kelp(m, 400 + k, height=rng.uniform(7, 8.5))

    # ------------------------------------------------------------ big T-dock (tiers)
    z0 = dock_z
    with m.ctx(stage="dock", folder="Dock"):
        with m.at((dock_x, 0, 0)):
            for k in range(2):        # wide steps from the sand up to the deck
                m.span((-5.5, 2.0, z0 - 3.4 + k * 1.7), (5.5, 3.0 + 0.75 * (k + 1), z0 - 1.7 + k * 1.7),
                       C["wood_dark"] if k % 2 else C["wood"])
            with m.ctx(tier=1):
                Bd.dock_deck(m, -4, z0, 4, z0 + 26, DECK_Y, rails=("x0", "x1"))
                Bd.dock_deck(m, -10, z0 + 26, 10, z0 + 38, DECK_Y, along="x",
                             rails=("z1", "x0", "x1", ("z0", (-4.6, 4.6))))
                with m.at((7.5, DECK_Y, z0 + 35)):
                    P.lantern_post(m)
                with m.at((-6.5, DECK_Y, z0 + 34), ry=90):
                    P.fish_bucket(m)
            W0, T0, T1, TX = z0, z0 + 40, z0 + 66, 32.0
            with m.ctx(tier=2):
                Bd.dock_deck(m, -5, W0, 5, T0, DECK_Y, rails=("x0", "x1"))
                Bd.dock_deck(m, -TX, T0, TX, T1, DECK_Y, along="x",
                             rails=("z1", ("x0", (T0 + 8, T0 + 16)), ("x1", (T0 + 8, T0 + 16)), ("z0", (-5.6, 5.6))))
                for x in (-TX + 2.2, TX - 2.2):
                    for z in (T0 + 2.2, T1 - 2.2):
                        with m.at((x, DECK_Y, z), ry=180 if x < 0 else 0):
                            P.lantern_post(m)
                for k, x in enumerate((-22, -10, 10, 22)):          # spear racks along the far rail
                    if k % 2 == 0:
                        with m.at((x, DECK_Y, T1 - 2.4)):
                            P.spear_rack(m, n=5)
                    else:
                        with m.at((x, DECK_Y, T1 - 2.6)):
                            P.fish_bucket(m)
                with m.at((-16, DECK_Y, T0 + 3.5)):
                    P.ice_crate(m)
                with m.at((17, DECK_Y, T0 + 3.2)):
                    P.crate_cluster(m, 7)
                with m.at((-6.5, DECK_Y, T1 - 6.0)):
                    P.rope_coil(m)
                # entrance arch with the SPEARFISHING sign over the walkway
                with m.at((0, DECK_Y, T0 - 0.8)):
                    for s_ in (-1, 1):
                        m.box((s_ * 5.4, 4.2, 0), (0.9, 8.4, 0.9), C["wood_dark"])
                    m.box((0, 8.6, 0), (12.4, 0.8, 1.0), C["wood_dark"])
                    board = m.box((0, 10.0, -0.1), (11.0, 2.2, 0.5), "#FFF1D6")
                    m.text(board, "SPEARFISHING", "#2A5DA8", "Front")
                    m.text(board, "SPEARFISHING", "#2A5DA8", "Back")
                for side in (-1, 1):                            # boats tied at the rail openings
                    with m.at((side * (TX + 4.5), 0.2, T0 + 12), ry=0):
                        rowboat(m, C["wood"], C["wood_dark"], P.ACCENTS["white"])
            with m.ctx(tier=3):          # fishing wings off both sides + a shade canopy
                for side in (-1, 1):
                    xa, xb = (TX, TX + 18) if side > 0 else (-TX - 18, -TX)
                    Bd.dock_deck(m, xa, T0 + 6, xb, T0 + 18, DECK_Y, along="x",
                                 rails=("z0", "z1", "x1" if side > 0 else "x0"))
                    with m.at(((xa + xb) / 2, DECK_Y, T0 + 7.6)):
                        P.lantern_post(m)
                    with m.at(((xa + xb) / 2 + 4 * side, DECK_Y, T0 + 16)):
                        P.spear_rack(m, n=4)
                with m.at((-18, DECK_Y, (T0 + T1) / 2 + 2)):
                    for x in (-6, 6):
                        for z in (-4, 4):
                            m.box((x, 4.5, z), (0.8, 9, 0.8), C["wood_dark"])
                    for k in range(7):
                        m.box((-6 + k * 2, 9.2, 0), (2.0, 0.5, 10.4), P.ACCENTS["sky"] if k % 2 else "#FFFFFF")
        for p in old:
            if p[0] == "Rowboat" and p[3] < z0:
                with m.at((p[1], 0.2, p[3]), ry=p[4]):
                    rowboat(m, C["wood"], C["wood_dark"], P.ACCENTS["white"])
        # travel pier past the arch, with the green-sailed boat
        ax, az = arch[1], arch[3]
        L = math.hypot(ax, az)
        ux, uz = ax / L, az / L
        t = 0.0
        while g.top_at(ax + ux * t, az + uz * t) is not None and t < 200:
            t += 2
        sx, sz = ax + ux * (t - 4), az + uz * (t - 4)
        with m.at((sx, 0, sz), ry=math.degrees(math.atan2(ux, uz))):
            Bd.dock_deck(m, -3.5, 0, 3.5, 26, DECK_Y, rails=("x0",))
            with m.at((9.5, 0, 16), ry=180):
                Bd.sailboat(m, C["sail"])
            with m.at((-2.0, DECK_Y, 3.0), ry=180):
                P.sign_board(m, "TRAVEL", w=6, h=2, color="#FFF1D6", text_color="#2E8B57", height=5.0)
            with m.at((-2.6, DECK_Y, 23)):
                P.lantern_post(m)

    # ------------------------------------------------------------ hub, stalls, portal, landmarks
    with m.ctx(stage="buildings", folder="Buildings"):
        with m.at((px, HY, pz)):
            with m.ctx(tier=1):
                m.octagon(0.25, FLOOR_R - 2, 0.6, C["dirt"])
            with m.ctx(tier=2):
                m.octagon(0.2, FLOOR_R, 0.6, C["path_border"])
                m.octagon(0.3, FLOOR_R - 1.5, 0.6, C["path"])
        with m.ctx(stage="buildings", folder="Buildings"):
            for a, f in exits:           # stone paths from the floor edge to every way out of the hub
                ex, ez = g.wx(f[0]), g.wx(f[1])
                d = math.hypot(ex - px, ez - pz)
                if d > FLOOR_R + 1:
                    sx_, sz_ = px + (ex - px) / d * (FLOOR_R - 1), pz + (ez - pz) / d * (FLOOR_R - 1)
                    path_strip(m, [(sx_, sz_), (ex, ez)], 9, C["path"], C["path_border"], lambda x, z: HY)
        kinds = {"market": ("FISH MARKET", P.ACCENTS["sky"], "#4FC3F7", "ShopPad_FishMarket", Bd.goods_fish, Bd.icon_fish),
                 "shop": ("SPEAR SHOP", P.ACCENTS["red"], "#FF5A5A", "ShopPad_SpearShop", Bd.goods_spears, Bd.icon_spear),
                 "upgrade": ("UPGRADES", "#FFC93C", "#FFB020", "ShopPad_Upgrades", Bd.goods_upgrades, Bd.icon_hammer)}
        for name, (x, z), ry in stalls:
            title, stripe, cloth, pad, goods, icon = kinds[name]
            with m.at((x, stall_y[name], z), ry=ry):
                Bd.simple_stall(m, title, stripe, cloth, pad, goods, icon=icon)
                with m.ctx(tier=3):      # tier 3: pennants on the stall roofs
                    for s_ in (-1, 1):
                        m.box((s_ * 6.5, 13.0, 4.6), (0.3, 3.4, 0.3), C["wood_dark"])
                        m.box((s_ * 6.5 + 0.9 * s_, 14.2, 4.6), (1.6, 1.0, 0.15), stripe, collide=False)
        if portal_at:
            (x, z), ry, _, _ = portal_at
            pb = Bd.portal_bounds()
            with m.at((x, HY + CH, z), ry=ry):
                # invisible marker the Blender portal snaps to (roblox/PlacePortal.lua)
                spot = m.box(((pb[0][0] + pb[1][0]) / 2, (pb[0][1] + pb[1][1]) / 2, (pb[0][2] + pb[1][2]) / 2),
                             (pb[1][0] - pb[0][0], pb[1][1] - pb[0][1], pb[1][2] - pb[0][2]), "#B67CFF",
                             name="PortalSpot", transparency=1.0, collide=False, shadow=False)
                with m.ctx(stage="props", folder="Props"):
                    for s_ in (-1, 1):
                        with m.at((s_ * 10.5, 0, 10.5)):
                            P.bush(m, 70 + s_)
                        with m.at((s_ * 10.5, 0, -10.0)):
                            P.flowers(m, 75 + s_, ("pink", "sky") if s_ > 0 else ("yellow", "pink"))
                        with m.at((s_ * 8.0, -CH, -35.0)):
                            P.lantern_post(m)
        ly = g.top_at(peak[0], peak[2]) or peak[1]
        with m.at((peak[0], ly, peak[2]), ry=face((peak[0], peak[2]), (dock_x, dock_z))):
            Bd.lighthouse(m, C, beam_tier=3)
        with m.at((arch[1], arch[2] - 0.5, arch[3]), ry=arch[4]):
            Bd.stone_arch(m, BANDS, C["grass"], half=13.0)
        cave = first("CaveEntrance")
        if cave:
            with m.at((cave[1], cave[2], cave[3]), ry=cave[4] + 180):
                m.span((-5, 0, -1.0), (5, 9, 0.6), "#2A2E45")
                for s_ in (-1, 1):
                    m.span((s_ * 5 - 0.7, 0, -1.6), (s_ * 5 + 0.7, 10, 0.2), C["wood_dark"])
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

    blocked = keep + [((dock_x, dock_z + 30), 40)]

    def clear(x, z, r=0):
        return all(math.hypot(x - a, z - b) > rr + r for (a, b), rr in blocked)

    # ------------------------------------------------------------ waterfall from a terrace into a pond
    best = None
    for c, t in g.top.items():
        if g.kind[c] != "land" or c in changed:
            continue
        x, z = g.wx(c[0]), g.wx(c[1])
        dd = math.hypot(x - px, z - pz)
        if not HUB_R - 8 < dd < 110 or not clear(x, z, 9):
            continue
        for d in DIRS:
            up = (c[0] + d[0], c[1] + d[1])
            up2 = (c[0] + 2 * d[0], c[1] + 2 * d[1])
            if g.kind.get(up) != "land" or g.top.get(up, 0) < t + 9 or g.top.get(up2, 0) < t + 9:
                continue
            pc = (c[0] - 2 * d[0], c[1] - 2 * d[1])
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
                for k in range(3):
                    m.box((2.5 - k * 2.6, 1.0, (-1) ** k * 2.0), (1.6, 0.2, 1.6), "#4FA83A", ry=k * 25, collide=False)
            ex, ez = g.wx(c[0]) + d[0] * 2.1, g.wx(c[1]) + d[1] * 2.1
            with m.at((ex, 0, ez), ry=math.degrees(math.atan2(-d[0], -d[1]))), m.ctx(collide=False, shadow=False):
                n = 4
                for k in range(n):
                    y0, y1 = upper - (upper - fy) * k / n, upper - (upper - fy) * (k + 1) / n
                    m.span((-3.2, y1 - 0.2, 1.6 + k * 0.45), (3.2, y0 + 0.4, 2.6 + k * 0.45),
                           "#6FD3FA" if k % 2 else "#4FC3F7", mat="Glass")
                    for xs in (-1.6, 1.2):
                        m.span((xs - 0.25, y1, 2.62 + k * 0.45), (xs + 0.25, y0, 2.8 + k * 0.45), "#FFFFFF")
                m.span((-3.5, upper - 0.4, -6.0), (3.5, upper + 0.35, 2.6), "#4FC3F7", mat="Glass")
                for k in range(3):
                    m.box((-2 + k * 2, fy + 0.9, 4.2 + k * 0.4), (1.8, 0.8, 1.8), "#FFFFFF", ry=k * 20)
        blocked.append(((g.wx(pc[0]), g.wx(pc[1])), 10))
        print("    waterfall at", (g.wx(c[0]), fy, g.wx(c[1])), "drop", upper - fy)

    # ------------------------------------------------------------ props
    def water_near(c, r):
        return any((c[0] + a, c[1] + b) not in g.top for a in range(-r, r + 1) for b in range(-r, r + 1))

    def cliff_near(c, r):
        return any(g.top.get((c[0] + a, c[1] + b), 0) > g.top[c] + 2 for a in range(-r, r + 1) for b in range(-r, r + 1))

    beach_cells = [c for c in g.top if g.kind[c] == "beach" and water_near(c, 3) and not water_near(c, 1)
                   and not cliff_near(c, 3)]
    beach_cells.sort(key=lambda c: math.atan2(g.wx(c[1]), g.wx(c[0])))

    def beach_open(c):
        return all(g.kind.get((c[0] + a, c[1] + b)) == "beach" for a in range(-2, 3) for b in range(-2, 3)) and \
            not any(g.kind.get((c[0] + a, c[1] + b)) == "path" for a in range(-4, 5) for b in range(-4, 5))

    with m.ctx(stage="props", folder="Props"):
        # beach camp: campfire, log seats, tent, 2 palms - on the most open beach far from the dock
        camp = None
        for c in sorted(beach_cells, key=lambda c: -math.hypot(g.wx(c[0]) - dock_x, g.wx(c[1]) - dock_z)):
            x, z = g.wx(c[0]), g.wx(c[1])
            if beach_open(c) and clear(x, z, 14):
                camp = (x, g.top[c], z)
                break
        if camp:
            x, y, z = camp
            out = math.degrees(math.atan2(x, z))       # tent faces the sea
            with m.at((x, y, z), ry=out):
                Bd.campfire(m)
                for k, a in enumerate((0, 120, 240)):
                    r = math.radians(a)
                    with m.at((math.cos(r) * 5.2, 0, math.sin(r) * 5.2), ry=-a + 90):
                        Bd.log_seat(m)
                with m.at((-2, 0, -11), ry=180):
                    Bd.tent(m)
                for k, (dx, dz) in enumerate(((8, -9), (-10, 6))):
                    with m.at((dx, 0, dz), ry=-math.degrees(math.atan2(dz, dx))):
                        P.palm(m, (2, 1)[k], 1700 + k)
                with m.at((10, 0, 4)):
                    P.flowers(m, 1710, ("red", "yellow"))
            blocked.append(((x, z), 16))
            print("    beach camp at", (round(x), round(z)))
        # fishing jetty on the beach opposite the dock
        jetty = None
        for c in sorted(beach_cells, key=lambda c: math.hypot(g.wx(c[0]) + dock_x, g.wx(c[1]) + dock_z)):
            x, z = g.wx(c[0]), g.wx(c[1])
            if clear(x, z, 12) and not any(g.kind.get((c[0] + a, c[1] + b)) == "path" for a in range(-3, 4) for b in range(-3, 4)):
                jetty = (x, g.top[c], z)
                break
        if jetty:
            x, y, z = jetty
            ry = math.degrees(math.atan2(x, z))           # out to sea
            with m.at((x, 0, z), ry=ry), m.ctx(stage="dock", folder="Dock"):
                Bd.dock_deck(m, -3.5, 0, 3.5, 22, DECK_Y, rails=("x0", "x1"))
                Bd.dock_deck(m, -7, 22, 7, 30, DECK_Y, along="x", rails=("z1", ("z0", (-4, 4))))
                with m.at((0, DECK_Y, 27.5), ry=180):
                    P.bench(m)
                with m.at((5, DECK_Y, 24)):
                    P.fish_bucket(m)
                with m.at((-5.2, DECK_Y, 28)):
                    P.lantern_post(m)
                with m.at((10, 0.2, 18), ry=10):
                    rowboat(m, C["wood"], C["wood_dark"], P.ACCENTS["white"])
            blocked.append(((x, z), 14))
            print("    fishing jetty at", (round(x), round(z)))
        # trees: original spots outside the hub; oaks near the hub, pines further out
        kept = []
        for p in sorted((p for p in old if p[0] in TREES and clear(p[1], p[3], 4)
                         and g.cell_of(p[1], p[3]) not in changed), key=lambda p: (p[1], p[3])):
            if all(math.hypot(p[1] - q[1], p[3] - q[3]) > 6.5 for q in kept):
                kept.append(p)
        trng = random.Random(31)
        for k, p in enumerate(kept):
            with m.at((p[1], p[2], p[3]), ry=p[4]):
                plant_tree(m, trng, math.hypot(p[1] - px, p[3] - pz) < 100, TREES[p[0]], 1000 + k)
        # oak clumps around the open hub lawn (frame it without blocking it)
        for k, a in enumerate(range(0, 360, 40)):
            if any(adiff(a, t) < 28 for t in taken) or (portal_at and adiff(a, portal_at[2]) < 30):
                continue
            r = HUB_R - 10
            x, z = px + math.cos(math.radians(a)) * r, pz + math.sin(math.radians(a)) * r
            c = g.cell_of(x, z)
            if c in g.top and abs(g.top[c] - HY) < 0.3 and g.kind[c] == "land" and clear(x, z, 4) and \
                    all(abs(g.top.get((c[0] + i, c[1] + j), -9) - HY) < 0.3 for i in (-1, 0, 1) for j in (-1, 0, 1)):
                with m.at((x, HY, z), ry=a * 7):
                    plant_tree(m, random.Random(k), True, k % 3, 1800 + k)
                with m.at((x + 4, HY, z + 3)):
                    P.flowers(m, 1850 + k, ("red", "yellow") if k % 2 else ("pink", "sky"))
        # fill pass: clumps of trees on every open grass terrace so no area is left bare
        from terrain import noise2
        trees_at = [(p[1], p[3]) for p in kept]
        cand = []
        for c, t in g.top.items():
            if g.kind[c] != "land" or c in changed or g.surf.get(c) not in ("grass", "rocktop"):
                continue
            if any(g.kind.get((c[0] + a, c[1] + b)) == "path" for a in range(-1, 2) for b in range(-1, 2)):
                continue
            if not all(abs(g.top.get((c[0] + a, c[1] + b), -99) - t) < 0.3 for a in (-1, 0, 1) for b in (-1, 0, 1)):
                continue
            x, z = g.wx(c[0]), g.wx(c[1])
            if noise2(x, z, 77, 46) < 0.3 or not clear(x, z, 5):
                continue
            cand.append((c, x, z, t))
        rng2 = random.Random(9)
        rng2.shuffle(cand)
        n_fill = 0
        for c, x, z, t in cand:
            jx, jz = rng2.uniform(-1.2, 1.2), rng2.uniform(-1.2, 1.2)
            if any(math.hypot(x + jx - a, z + jz - b) < 6.8 for a, b in trees_at):
                continue
            trees_at.append((x + jx, z + jz))
            n_fill += 1
            with m.at((x + jx, t, z + jz), ry=rng2.uniform(0, 360)):
                plant_tree(m, rng2, math.hypot(x - px, z - pz) < 105, None, 2000 + n_fill)
            if n_fill % 4 == 0:
                with m.at((x + jx + 3.2, t, z + jz + 1.5)):
                    (P.bush if n_fill % 8 else P.flowers)(m, 2500 + n_fill)
        print("    fill trees", n_fill, "total trees", len(trees_at))
        # grass tufts: clusters of 3-4 tufts all over the lawns (not on paths, cliff edges or the hub floor)
        trng2 = random.Random(57)
        tuft_at = []
        for c, t in sorted(g.top.items()):
            if g.kind[c] != "land" or g.surf.get(c) not in ("grass", "rocktop"):
                continue
            x, z = g.wx(c[0]) + trng2.uniform(-1.5, 1.5), g.wx(c[1]) + trng2.uniform(-1.5, 1.5)
            if trng2.random() > 0.3 + 0.25 * noise2(x, z, 91, 30):
                continue
            if any(g.kind.get((c[0] + a, c[1] + b)) == "path" for a in (-1, 0, 1) for b in (-1, 0, 1)):
                continue
            if not all(abs(g.top.get((c[0] + a, c[1] + b), -99) - t) < 0.3 for a in (-1, 0, 1) for b in (-1, 0, 1)):
                continue
            if math.hypot(x - px, z - pz) < FLOOR_R + 3 or not clear(x, z, 1) or \
                    any(math.hypot(x - a, z - b) < 2.6 for a, b in trees_at):
                continue
            tuft_at.append((x, z))
            fl = (P.ACCENTS["yellow"], P.ACCENTS["white"], P.ACCENTS["pink"], None, None, None)[len(tuft_at) % 6]
            with m.at((x, t, z), ry=trng2.uniform(0, 360)):
                P.tuft_cluster(m, 3000 + len(tuft_at), flower=fl)
        for c in beach_cells[::3]:            # dune grass on the beaches
            x, z = g.wx(c[0]), g.wx(c[1])
            if clear(x, z, 2) and trng2.random() < 0.5:
                with m.at((x + trng2.uniform(-1, 1), g.top[c], z + trng2.uniform(-1, 1)), ry=trng2.uniform(0, 360)):
                    P.tuft_cluster(m, 4000 + len(tuft_at), greens=("#9CCB5A", "#B8D86A", "#7FB34A"))
                tuft_at.append((x, z))
        print("    grass tuft clusters", len(tuft_at))
        # beach palm clumps: 2 palms leaning out + bush + flowers
        palms_at = []
        for c in beach_cells[::7]:
            x, z = g.wx(c[0]), g.wx(c[1])
            near_path = any(g.kind.get((c[0] + a, c[1] + b)) == "path" for a in range(-3, 4) for b in range(-3, 4))
            if near_path or not clear(x, z, 8) or len(palms_at) >= 6:
                continue
            if all(math.hypot(x - a, z - b) > 45 for a, b in palms_at):
                palms_at.append((x, z))
                for j, off in enumerate((-1, 1)):
                    a_ = math.atan2(z, x) + off * 0.9
                    with m.at((x + math.cos(a_) * 3.6, g.top[c], z + math.sin(a_) * 3.6), ry=-math.degrees(a_)):
                        P.palm(m, (2, 0)[j], 1500 + len(palms_at) * 5 + j)
                with m.at((x - math.cos(math.atan2(z, x)) * 3.5, g.top[c], z - math.sin(math.atan2(z, x)) * 3.5)):
                    P.bush(m, 1550 + len(palms_at))
                with m.at((x + 2.5, g.top[c], z + 3.0)):
                    P.flowers(m, 1560 + len(palms_at), ("pink", "yellow"))
        bushes, flowers = [], []
        for p in old:
            if g.cell_of(p[1], p[3]) in changed:
                continue
            if p[0] == "Bush" and len(bushes) < 10 and clear(p[1], p[3], 2) and \
                    any(math.hypot(p[1] - q[1], p[3] - q[3]) < 14 for q in kept) and \
                    all(math.hypot(p[1] - a, p[3] - b) > 20 for a, b in bushes):
                bushes.append((p[1], p[3]))
                with m.at((p[1], p[2], p[3])):
                    P.bush(m, 1100 + len(bushes))
            if p[0] == "Flowers" and len(flowers) < 12 and clear(p[1], p[3], 2):
                c = g.cell_of(p[1], p[3])
                near_path = any(g.kind.get((c[0] + a, c[1] + b)) == "path" for a in (-1, 0, 1) for b in (-1, 0, 1))
                if near_path and all(math.hypot(p[1] - a, p[3] - b) > 22 for a, b in flowers):
                    flowers.append((p[1], p[3]))
                    with m.at((p[1], p[2], p[3])):
                        P.flowers(m, 1200 + len(flowers), (("red", "yellow"), ("pink", "yellow"), ("red", "pink"))[len(flowers) % 3])
        stair_rails(m, g, C)
        with m.ctx(tier=2):
            for p in old:
                if p[0] in ("Torch", "LampPost") and g.cell_of(p[1], p[3]) not in changed and clear(p[1], p[3], 1) \
                        and p[2] > 3.5:
                    with m.at((p[1], p[2], p[3]), ry=p[4]):
                        P.lantern_post(m)
            for a, f in exits:            # lanterns where each path leaves the hub floor
                r = math.radians(a)
                for s_ in (-1, 1):
                    x = px + math.cos(r) * (FLOOR_R + 2) - math.sin(r) * 5.2 * s_
                    z = pz + math.sin(r) * (FLOOR_R + 2) + math.cos(r) * 5.2 * s_
                    if g.top_at(x, z) == HY:
                        with m.at((x, HY, z), ry=-a):
                            P.lantern_post(m)

    ly = g.top_at(peak[0], peak[2]) or peak[1]
    cams = {
        "overhead": ((235, 165, 335), (0, 22, 0), 30),
        "dock": ((dock_x, DECK_Y + 5.5, z0 + 64), (6, 45, 0), 24),
        "plaza": ((px - 6, HY + 6, pz - 14), (px + 4, HY + 6, pz + 30), 26),
        "village": ((px + 80, HY + 70, pz + 90), (px, HY, pz - 8), 28),
        "lighthouse": ((peak[0] + 45, ly + 25, peak[2] + 45), (peak[0], ly + 18, peak[2]), 28),
        "reef": ((dock_x + 20, DECK_Y + 3, z0 + 78), (dock_x, -10, z0 + 60), 26),
        "dockdeck": ((dock_x + 46, DECK_Y + 22, z0 + 92), (dock_x, DECK_Y, z0 + 44), 28),
    }
    for name, (x, z), ry in stalls:
        a = math.radians(ry)
        fx, fz = -math.sin(a), -math.cos(a)
        y_ = {n: v for n, v in stall_y.items()}[name]
        cams[name] = ((x + fx * 30 - fz * 10, y_ + 12, z + fz * 30 + fx * 10), (x, y_ + 7, z), 32)
    if portal_at:
        (x, z), ry, _, _ = portal_at
        a = math.radians(ry)
        fx, fz = -math.sin(a), -math.cos(a)
        cams["portal"] = ((x + fx * 40 + fz * 16, HY + CH + 9, z + fz * 40 - fx * 16), (x, HY + CH + 9, z), 30)
    if camp:
        x, y, z = camp
        L = math.hypot(x, z) or 1
        cams["camp"] = ((x + x / L * 30 + z / L * 10, y + 9, z + z / L * 30 - x / L * 10), (x, y + 3, z), 30)
    if palms_at:
        bx, bz = palms_at[0]
        L = math.hypot(bx, bz) or 1
        cams["beach"] = ((bx + bx / L * 40 + bz / L * 12, 9, bz + bz / L * 40 - bx / L * 12), (bx, 9, bz), 30)
    cams["stairs"] = ((dock_x + 10, 14, dock_z + 16), (dock_x, 20, dock_z - 40), 28)
    if best:
        wx_, wz_ = g.wx(best[1][0]), g.wx(best[1][1])
        cams["waterfall"] = ((wx_ - best[2][0] * 36 + 12, best[0] * 0 + 36, wz_ - best[2][1] * 36 + 12),
                             (wx_, 28, wz_), 30)
    spawn = (px, HY + 1.5, pz)
    water = (-300, -14, -300, 300, 0, 300)
    return m, PRESET, water, spawn, cams
