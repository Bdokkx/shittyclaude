"""Custom voxel assets for the Desert Coast, Frost Coast and Volcanic Island, plus
re-coloured theme versions of the shared rocks/plants. Registered into assets.ASSETS.
Same conventions as assets.py (studs, Y up, origin at the ground point)."""
import math
import random

from assets import (ARCH_BASE, B, CLIFF_CRAG, CLIFF_ROCKS, LEDGE_ROCK, asset, blob_rock, pine_boxes,
                    roughen, shifted)

# ------------------------------------------------------------------ re-colouring

DESERT = {"rock": "red_rock", "rock_dark": "red_rock_dark", "rock_light": "red_rock_light",
          "rock_gray": "terracotta", "rock_deep": "red_rock_dark", "stone_dark": "terracotta",
          "stone": "sandstone", "moss": "dry_grass", "moss_dark": "sandstone_dark", "grass": "desert_sand",
          "grass_dark": "sandstone", "grass_light": "dry_grass", "sand": "sandstone",
          "leaf": "palm_leaf", "leaf_dark": "palm_leaf_dk", "leaf_light": "dry_grass", "trunk": "palm_trunk"}
FROST = {"rock": "frost_rock", "rock_dark": "frost_rock_dk", "rock_light": "frost_rock_lt",
         "rock_gray": "ice_dark", "rock_deep": "frost_rock_dk", "stone_dark": "frost_rock_dk",
         "stone": "frost_rock_lt", "moss": "snow", "moss_dark": "snow_shadow", "grass": "snow",
         "grass_dark": "snow_shadow", "grass_light": "snow", "sand": "ice_light",
         "leaf": "snow_leaf", "leaf_dark": "snow_leaf_dk", "leaf_light": "snow"}
ICEBERG = {"rock": "ice_light", "rock_dark": "ice", "rock_light": "snow", "rock_gray": "ice_dark",
           "rock_deep": "ice", "stone_dark": "ice_dark", "moss": "snow", "moss_dark": "snow_shadow",
           "grass": "snow", "grass_dark": "snow_shadow"}
VOLCANIC = {"rock": "basalt", "rock_dark": "basalt_dark", "rock_light": "basalt_light",
            "rock_gray": "ash_dark", "rock_deep": "obsidian", "stone_dark": "basalt_dark",
            "stone": "basalt_light", "moss": "scorched", "moss_dark": "scorched_dk", "grass": "scorched",
            "grass_dark": "scorched_dk", "grass_light": "ash", "sand": "magma_crust",
            "leaf": "ember_leaf", "leaf_dark": "ember_leaf_dk", "leaf_light": "ash", "trunk": "charred"}
OBSIDIAN = dict(VOLCANIC, rock="obsidian", rock_dark="basalt_dark", rock_light="basalt",
                rock_gray="obsidian", moss="ash", moss_dark="ash_dark", grass="ash")


def recolor(boxes, mapping):
    return [b[:6] + (mapping.get(b[6], b[6]),) for b in boxes]


def recolored(name_boxes, mapping):
    return asset(recolor(name_boxes, mapping))


# ------------------------------------------------------------------ desert

def palm(seed, height=16, lean=4):
    """Leaning ringed trunk with a full crown of continuous fronds that rise, then arch over and droop."""
    rng = random.Random(seed)
    b = []
    segs = int(height / 2)
    x = 0
    for k in range(segs):
        t = k / segs
        nx = lean * t * t
        w = 1.8 - 0.5 * t
        b.append(B(nx, k * 2, 0, w, 2.05, w, "palm_trunk" if k % 2 else "trunk"))
        if k % 2 == 0:
            b.append(B(nx, k * 2 + 1.6, 0, w + 0.3, 0.4, w + 0.3, "trunk"))  # trunk rings
        x = nx
    top = segs * 2
    b.append(B(x, top - 0.4, 0, 2.4, 1.8, 2.4, "palm_leaf_dk"))           # crown
    b.append(B(x, top + 1.4, 0, 1.4, 1.0, 1.4, "palm_leaf"))
    b += [B(x + 1.1, top - 1.0, 0.7, 0.9, 0.9, 0.9, "palm_trunk"),        # coconuts
          B(x - 0.9, top - 1.1, -0.8, 0.9, 0.9, 0.9, "palm_trunk"),
          B(x + 0.2, top - 1.2, -1.1, 0.8, 0.8, 0.8, "trunk")]
    reach = height / 16
    for a in range(8):
        ang = a * math.pi / 4 + rng.uniform(-0.08, 0.08)
        dx, dz = math.cos(ang), math.sin(ang)
        cardinal = a % 2 == 0
        n = 7 if cardinal else 6
        lift = rng.uniform(0.5, 0.75)
        for st in range(n):
            r = (1.2 + st * 1.25) * reach
            y = top + 1.0 + lift * st - 0.3 * st * st                          # rises, then arches down
            w = max(0.7, 1.7 - 0.15 * st)
            col = "palm_leaf" if (st // 2 + a) % 2 else "palm_leaf_dk"
            cx, cz = x + dx * r, dz * r
            if cardinal:   # long strip segments that overlap, so the frond is one continuous leaf
                lx, lz = (1.7, w) if abs(dx) > 0.5 else (w, 1.7)
                b.append(B(cx, y, cz, lx, 0.5, lz, col))
                if 1 <= st <= n - 2:   # leaflets hanging off both sides
                    px, pz = (0.6, w + 1.6) if abs(dx) > 0.5 else (w + 1.6, 0.6)
                    b.append(B(cx, y - 0.45, cz, px, 0.4, pz, "palm_leaf_dk" if col == "palm_leaf" else "palm_leaf"))
            else:          # diagonal fronds: overlapping squares make a continuous staircase leaf
                b.append(B(cx, y, cz, w + 0.4, 0.5, w + 0.4, col))
    return asset(b)


def cactus():
    return asset([B(0, 0, 0, 1.6, 7, 1.6, "cactus"), B(0, 7, 0, 1.2, 0.6, 1.2, "cactus_dk"),
                  B(1.4, 2.5, 0, 1.4, 1, 1, "cactus_dk"), B(1.9, 3.5, 0, 1, 3, 1, "cactus"),
                  B(-1.3, 3.6, 0, 1.2, 1, 1, "cactus_dk"), B(-1.8, 4.6, 0, 1, 2.2, 1, "cactus"),
                  B(0, 7.6, 0, 0.6, 0.4, 0.6, "cloth_red")])


def dry_bush():
    return asset([B(0, 0, 0, 3, 1.6, 3, "dry_grass"), B(0.4, 1.4, -0.3, 2, 1, 2, "sandstone_dark"),
                  B(-1, 0, 1, 1.4, 1.2, 1.4, "palm_trunk"), B(1.2, 0.6, 1.1, 0.6, 1.4, 0.6, "dry_grass")])


def adobe_house(big=False):
    w, d, h = (14, 11, 9) if big else (11, 9, 7)
    b = [B(0, 0, 0, w, h, d, "adobe"), B(0, h, 0, w + 0.6, 0.8, d + 0.6, "adobe_dark"),
         B(0, h - 0.6, 0, w - 1.6, 0.6, d - 1.6, "adobe")]
    b += [B(0, 0, d / 2 + 0.1, 2.6, 4.2, 0.3, "palm_trunk"), B(0, 4.2, d / 2 + 0.15, 3.2, 0.5, 0.4, "adobe_dark")]
    for x in (-w / 2 + 2.2, w / 2 - 2.2):
        b.append(B(x, h / 2, d / 2 + 0.1, 1.6, 1.8, 0.3, "basalt_dark"))  # windows
        b.append(B(x, h / 2 - 0.4, d / 2 + 0.25, 2.2, 0.35, 0.5, "adobe_dark"))
    for k in range(4):  # roof beams poking out
        b.append(B(-w / 2 + 1.5 + k * (w - 3) / 3, h - 1.6, d / 2 + 0.6, 0.6, 0.6, 1.4, "palm_trunk"))
    b += [B(-w / 2 + 2, h + 0.8, -d / 2 + 2, 1.6, 1.6, 1.6, "terracotta"),
          B(w / 2 - 2.4, h + 0.8, -d / 2 + 2.2, 2.4, 1.6, 2.4, "wood")]
    b += [B(w / 2 - 3, 4.2, d / 2 + 1.4, 4, 0.3, 2.6, "cloth_teal"),
          B(w / 2 - 4.8, 0, d / 2 + 2.6, 0.4, 4.2, 0.4, "palm_trunk"),
          B(w / 2 - 1.2, 0, d / 2 + 2.6, 0.4, 4.2, 0.4, "palm_trunk")]
    if big:  # second storey + outside stairs
        b += [B(-2, h + 0.8, 0, w * 0.55, 6, d * 0.7, "adobe"), B(-2, h + 6.8, 0, w * 0.55 + 0.6, 0.7, d * 0.7 + 0.6, "adobe_dark"),
              B(-2, h + 3, d * 0.35 + 0.1, 1.4, 1.6, 0.3, "basalt_dark")]
        for k in range(5):
            b.append(B(w / 2 + 1, k * h / 5, -d / 2 + 2 + k * 1.4, 2.2, h / 5, 1.4, "adobe_dark"))
    return asset(b)


def desert_stall():
    b = []
    for x in (-5, 5):
        for z in (-3, 3):
            b.append(B(x, 0, z, 0.8, 7.5, 0.8, "palm_trunk"))
    b += [B(0, 0, 2.8, 10, 3, 1.6, "adobe_dark"), B(0, 3, 2.8, 10.6, 0.4, 2, "plank")]
    cols = ["cloth_red", "cloth_yellow", "cloth_teal"]
    for s in range(6):
        b.append(B(-5 + s * 2, 7.5, 0, 2, 0.4, 8, cols[s % 3]))
        b.append(B(-5 + s * 2, 6.6, 4.2, 2, 1, 0.3, cols[s % 3]))
    for x, c in [(-3.5, "gold"), (-1.6, "terracotta"), (0.4, "cactus"), (2.4, "cloth_red"), (4, "gold")]:
        b.append(B(x, 3.4, 2.8, 1.2, 0.9, 1.2, c))
    b += [B(-7, 0, 1.5, 1.8, 2.4, 1.8, "terracotta"), B(-7, 2.4, 1.5, 1.2, 0.6, 1.2, "terracotta"),
          B(7, 0, 1, 2.6, 2.6, 2.6, "wood")]
    return asset(b)


def pots():
    b = []
    for x, z, h in ((0, 0, 2.6), (1.9, 0.6, 2), (0.6, 1.9, 1.6)):
        b += [B(x, 0, z, 1.6, h, 1.6, "terracotta"), B(x, h * 0.4, z, 1.9, h * 0.35, 1.9, "terracotta"),
              B(x, h, z, 1.1, 0.4, 1.1, "red_rock_dark")]
    return asset(b)


def obelisk():
    return asset([B(0, 0, 0, 5, 1.2, 5, "sandstone_dark"), B(0, 1.2, 0, 3, 12, 3, "sandstone"),
                  B(0, 13.2, 0, 2.2, 2, 2.2, "sandstone"), B(0, 15.2, 0, 1.2, 1.4, 1.2, "gold"),
                  B(0, 6, 1.55, 1.6, 4, 0.2, "gold")])


def ziggurat():
    b = []
    y = 0
    for k, (w, h) in enumerate([(30, 4), (24, 4), (18, 4), (12, 4)]):
        b.append(B(0, y, 0, w, h, w, "sandstone" if k % 2 == 0 else "sandstone_dark"))
        b.append(B(0, y + h - 0.6, 0, w + 0.6, 0.6, w + 0.6, "adobe_dark"))
        y += h
    for k in range(8):  # front stairs
        b.append(B(0, k * 2, 15 - k * 1.5, 6, 2, 1.5, "adobe" if k % 2 else "adobe_dark"))
    for x in (-4, 4):
        for z in (-4, 4):
            b.append(B(x, y, z, 1.4, 6, 1.4, "sandstone"))
    b += [B(0, y + 6, 0, 10.6, 1.2, 10.6, "sandstone_dark"), B(0, y + 7.2, 0, 7, 1.2, 7, "gold"),
          B(0, y, 0, 3, 3, 3, "lava_core")]
    return asset(roughen(b, 51, targets=("sandstone",), tile=3, prot=(0.1, 0.35),
                         shades=[("sandstone", 3), ("sandstone_dark", 1), ("adobe", 1)]),
                 lights=[(0, y + 2, 0, "glow", 22, 1.2)])


def brazier():
    return asset([B(0, 0, 0, 1.2, 4, 1.2, "stone_dark"), B(0, 4, 0, 2.6, 1, 2.6, "metal"),
                  B(0, 5, 0, 1.8, 1.4, 1.8, "fire"), B(0.2, 5.6, 0.1, 0.9, 1.4, 0.9, "fire_core")],
                 lights=[(0, 6, 0, "fire", 18, 1.4)], fires=[(0, 5.4, 0, 2)])


# ------------------------------------------------------------------ frost

def log_cabin():
    w, d, h = 14, 10, 7
    b = [B(0, 0, 0, w, h, d, "wood"), B(0, -0.4, 0, w + 1, 0.8, d + 1, "stone_dark")]
    for k in range(1, 7):  # log lines
        b.append(B(0, k - 0.1, d / 2 + 0.05, w, 0.25, 0.2, "wood_dark"))
        b.append(B(0, k - 0.1, -d / 2 - 0.05, w, 0.25, 0.2, "wood_dark"))
    for x in (-w / 2, w / 2):  # corner posts
        for z in (-d / 2, d / 2):
            b.append(B(x, 0, z, 1, h + 0.4, 1, "wood_dark"))
    for k in range(6):  # stepped roof, snow on every step
        ww = d + 2 - k * 1.9
        b.append(B(0, h + k * 1.1, 0, w + 2, 1.1, ww, "cloth_brown" if k % 2 else "wood_dark"))
        b.append(B(0, h + k * 1.1 + 1.1, ww / 2 - 0.5, w + 2, 0.4, 1, "snow"))
        b.append(B(0, h + k * 1.1 + 1.1, -(ww / 2 - 0.5), w + 2, 0.4, 1, "snow"))
    b += [B(4, h + 3, -2, 2, 6, 2, "stone"), B(4, h + 9, -2, 2.4, 0.5, 2.4, "snow")]  # chimney
    b += [B(0, 0, d / 2 + 0.1, 2.4, 4.4, 0.3, "wood_dark"),
          B(-4, 3, d / 2 + 0.1, 2.2, 2, 0.3, "window_glow"), B(4, 3, d / 2 + 0.1, 2.2, 2, 0.3, "window_glow"),
          B(-w / 2 - 0.05, 3, 0, 0.3, 2, 2.2, "window_glow"),
          B(0, 0, d / 2 + 1.8, w - 2, 0.6, 3, "plank"), B(-w / 2 + 1.5, 0.6, d / 2 + 3, 0.6, 3, 0.6, "wood_dark"),
          B(w / 2 - 1.5, 0.6, d / 2 + 3, 0.6, 3, 0.6, "wood_dark"),
          B(-3, 3.4, d / 2 + 1, 1, 1.4, 1, "glow"), B(-w / 2 - 2, 0, 2, 3, 1.4, 4, "snow_shadow")]
    return asset(b, lights=[(-3, 4, d / 2 + 1.6, "glow", 18, 1.3)])


def snowman():
    return asset([B(0, 0, 0, 4, 3.4, 4, "snow"), B(0, 3.4, 0, 3, 2.6, 3, "snow"), B(0, 6, 0, 2.2, 2.2, 2.2, "snow"),
                  B(-0.5, 7, 1.15, 0.4, 0.4, 0.2, "metal"), B(0.5, 7, 1.15, 0.4, 0.4, 0.2, "metal"),
                  B(0, 6.6, 1.5, 0.4, 0.4, 1, "fire"), B(0, 8.2, 0, 2, 0.4, 2, "metal"),
                  B(0, 8.6, 0, 1.4, 1.4, 1.4, "metal"), B(0, 5.6, 0, 3.2, 0.5, 3.2, "cloth_red"),
                  B(2.2, 4.4, 0, 2, 0.3, 0.3, "wood_dark"), B(-2.2, 4.6, 0, 2, 0.3, 0.3, "wood_dark")])


def ice_crystal():
    b = []
    for x, z, h, w in ((0, 0, 9, 1.8), (1.6, 0.8, 6, 1.3), (-1.4, 0.6, 5, 1.2), (0.4, -1.5, 4, 1.1), (-0.8, -1, 7, 1)):
        b.append(B(x, 0, z, w, h, w, "ice" if h > 5 else "ice_light"))
        b.append(B(x, h, z, w * 0.5, 1, w * 0.5, "ice_light"))
    b.append(B(0, 0, 0, 5, 0.8, 4.4, "snow"))
    return asset(b)


def snow_pile():
    return asset([B(0, 0, 0, 5, 1.4, 4, "snow"), B(0.4, 1.4, 0.2, 3, 1, 2.6, "snow"),
                  B(-1.4, 0, 1.4, 2.4, 0.9, 2.2, "snow_shadow")])


# ------------------------------------------------------------------ volcanic

def stilt_hut():
    b = []
    for x in (-5, 5):
        for z in (-4, 4):
            b.append(B(x, 0, z, 1, 6.5, 1, "charred"))
    b += [B(0, 6, 0, 12, 0.8, 10, "plank"), B(0, 6.8, 0, 9, 6, 7, "wood_dark"),
          B(0, 6.8, 3.6, 2.2, 4, 0.3, "charred"), B(-3, 9, 3.6, 1.6, 1.6, 0.3, "window_glow"),
          B(3, 9, 3.6, 1.6, 1.6, 0.3, "window_glow")]
    for k in range(4):  # stepped roof
        b.append(B(0, 12.8 + k * 1.1, 0, 11 - k * 2.4, 1.1, 9 - k * 2, "magma_crust" if k % 2 else "charred"))
    b += [B(0, 17.2, 0, 1, 1.6, 1, "charred")]
    for k in range(4):  # ladder
        b.append(B(0, k * 1.5, 5.6, 2.2, 0.3, 0.3, "wood"))
    b += [B(-1.2, 0, 5.6, 0.3, 6.5, 0.3, "wood"), B(1.2, 0, 5.6, 0.3, 6.5, 0.3, "wood"),
          B(5.6, 6.8, 4.6, 0.3, 3, 0.3, "metal"), B(5.6, 8.8, 4.6, 1, 1.3, 1, "glow")]
    for x in (-6, 6):  # railing
        b.append(B(x, 6.8, 0, 0.3, 1.8, 10, "wood"))
    return asset(b, lights=[(5.6, 9.4, 4.6, "glow", 18, 1.3)])


def dead_tree():
    """Gnarled burnt tree: a tapering trunk that leans as it climbs, forked bare branches."""
    b = [B(0, 0, 0, 3.2, 0.7, 3.2, "ash_dark"), B(0.6, 0, -0.5, 1.2, 1.2, 1.0, "charred"),  # roots
         B(-0.7, 0, 0.6, 1.0, 1.0, 1.2, "charred")]
    x = 0.0
    for k, (w, h) in enumerate(((2.0, 3.0), (1.7, 2.6), (1.4, 2.4), (1.1, 2.2), (0.8, 2.0))):
        y = sum(hh for _, hh in ((2.0, 3.0), (1.7, 2.6), (1.4, 2.4), (1.1, 2.2), (0.8, 2.0))[:k])
        b.append(B(x, y, 0, w, h, w, "charred" if k % 2 == 0 else "basalt_dark"))
        x += 0.35
    for (y, dx, dz, ln) in ((4.6, 1, 0, 3.2), (6.8, -1, 0.3, 2.8), (8.4, 0.2, 1, 2.4), (5.6, 0, -1, 2.0)):
        bx, bz = x * 0.6 + dx * ln / 2, dz * ln / 2
        b.append(B(bx, y, bz, abs(dx) * ln + 0.6, 0.6, abs(dz) * ln + 0.6, "charred"))
        tx, tz = x * 0.6 + dx * ln, dz * ln
        b.append(B(tx, y, tz, 0.6, 1.8, 0.6, "charred"))          # branch tips turn upward
        b.append(B(tx + dx * 0.6, y + 1.8, tz + dz * 0.6, 0.5, 1.0, 0.5, "basalt_dark"))
    b.append(B(x, 12.2, 0, 0.6, 1.2, 0.6, "ash"))                   # snapped top
    return asset(b)


def lava_rock():
    """Lumpy basalt boulder with glowing magma seams on top."""
    return asset(blob_rock(77, 3.4, 3.0, 7.0, vox=1.4, vh=1.1, moss=0.35, peak=1.3,
                           shades=[("basalt", 3), ("basalt_dark", 2), ("basalt_light", 1), ("obsidian", 0.8)],
                           tops=(("magma_crust", 2), ("lava", 1.5), ("lava_core", 0.5))))


def obsidian_shards():
    b = []
    for x, z, h in ((0, 0, 8), (1.5, 1, 5), (-1.4, 0.4, 6), (0.3, -1.6, 4)):
        b.append(B(x, 0, z, 1.2, h, 1.2, "obsidian"))
        b.append(B(x, h, z, 0.6, 1, 0.6, "basalt_light"))
    return asset(b)


def basalt_columns(seed=61):
    """Cluster of hexagon-ish basalt columns of different heights (parts, no deformation)."""
    rng = random.Random(seed)
    b = []
    for gx in range(-2, 3):
        for gz in range(-2, 3):
            if abs(gx) + abs(gz) > 3:
                continue
            h = 4 + (3 - abs(gx) - abs(gz)) * 3.5 + rng.uniform(-1.5, 2)
            x, z = gx * 2.6 + (gz % 2) * 1.3, gz * 2.3
            b.append(B(x, 0, z, 2.4, h, 2.4, rng.choice(("basalt", "basalt_dark", "basalt_light"))))
            b.append(B(x, h, z, 2.0, 0.3, 2.0, "scorched" if rng.random() < 0.4 else "basalt_light"))
    return asset(b)


# ------------------------------------------------------------------ registration

def theme_assets():
    from assets import ASSETS as A  # the shared ones (already built)
    out = {
        # desert
        "PalmTree": palm(71, 16, 4), "PalmTreeTall": palm(72, 22, 6), "PalmTreeSmall": palm(73, 11, 2.5),
        "Cactus": cactus(), "DryBush": dry_bush(), "AdobeHouse": adobe_house(), "AdobeHouseBig": adobe_house(True),
        "DesertStall": desert_stall(), "Pots": pots(), "Obelisk": obelisk(), "Ziggurat": ziggurat(),
        "Brazier": brazier(),
        "DesertTuft": recolored(A["GrassTuft"]["boxes"], DESERT),
        "DesertRock": recolored(A["SmallRock"]["boxes"], DESERT),
        "SandstonePillar": recolored(A["RuinPillar"]["boxes"],
                                     {"stone": "sandstone", "stone_dark": "sandstone_dark", "moss": "dry_grass"}),
        "DesertWell": recolored(A["Well"]["boxes"], {"stone": "sandstone", "stone_dark": "sandstone_dark",
                                                     "cloth_brown": "cloth_red", "wood_dark": "palm_trunk",
                                                     "flag_blue": "oasis_water"}),
        # frost
        "SnowPine": asset(pine_boxes(6, 12, 81, snow=True)), "SnowPineTall": asset(pine_boxes(7, 14, 82, snow=True)),
        "SnowPineSmall": asset(pine_boxes(4, 8, 83, trunk=3, snow=True)),
        "LogCabin": log_cabin(), "Snowman": snowman(), "IceCrystal": ice_crystal(), "SnowPile": snow_pile(),
        "FrostBush": recolored(A["Bush"]["boxes"] + [B(0.8, 3.9, -0.4, 3, 0.4, 2.6, "snow"),
                                                    B(-1.9, 2, 1.4, 2.6, 0.4, 2.6, "snow")],
                               {"leaf": "snow_leaf", "leaf_dark": "snow_leaf_dk", "leaf_light": "snow",
                                "grass_dark": "snow_leaf_dk", "mushroom_red": "cloth_red"}),
        "FrostRock": recolored(A["SmallRock"]["boxes"], FROST),
        # volcanic
        "CharredPine": recolored(pine_boxes(6, 12, 91), VOLCANIC),
        "CharredPineSmall": recolored(pine_boxes(4, 8, 93, trunk=3), VOLCANIC),
        "DeadTree": dead_tree(), "StiltHut": stilt_hut(), "LavaRock": lava_rock(),
        "ObsidianShards": obsidian_shards(), "BasaltColumns": basalt_columns(),
        "AshTuft": recolored(A["GrassTuft"]["boxes"], {"grass": "ash", "grass_light": "ash", "grass_dark": "scorched"}),
        "VolcanicBrazier": brazier(),
        "LavaGlow": asset([B(0, 0, 0, 0.8, 0.3, 0.8, "lava_core")], lights=[(0, 3, 0, "lava", 24, 1.6)]),
    }
    # theme rock sets (same base shapes as the island rocks, re-coloured)
    for prefix, mapping, stack_map in (("Desert", DESERT, DESERT), ("Ice", FROST, ICEBERG),
                                        ("Basalt", VOLCANIC, OBSIDIAN)):
        stack = {"Desert": "DesertStack", "Ice": "Iceberg", "Basalt": "ObsidianStack"}[prefix]
        out[prefix + "Crag"] = asset(recolor(CLIFF_CRAG, mapping))
        out[prefix + "Rocks"] = asset(recolor(CLIFF_ROCKS, mapping))
        out[prefix + "Ledge"] = asset(recolor(LEDGE_ROCK, mapping))
        out[stack] = asset(recolor(A["RockOutcrop"]["boxes"], stack_map))
        out[stack + "Big"] = asset(recolor(A["RockOutcropBig"]["boxes"], stack_map))
        out[stack + "Small"] = asset(recolor(A["RockOutcropSmall"]["boxes"], stack_map))
        arch = recolor(ARCH_BASE, mapping)
        out[prefix + "Arch"] = asset(roughen(arch, 11, targets=(mapping["rock"], mapping["rock_dark"]),
                                             shades=[(mapping["rock"], 3), (mapping["rock_dark"], 2),
                                                     (mapping["rock_light"], 1.4)]))
    return out


# mesh versions of the theme rocks (deformed in Blender, same as the island rocks)
def theme_mesh_sources(A):
    src = {}
    for prefix, rock, top, stack, srock, stop in (("Desert", "red_rock", "desert_sand", "DesertStack", "red_rock", "sandstone"),
                                                   ("Ice", "frost_rock", "snow", "Iceberg", "ice_light", "snow"),
                                                   ("Basalt", "basalt", "scorched", "ObsidianStack", "obsidian", "ash")):
        src[prefix + "Crag"] = dict(boxes=A[prefix + "Crag"]["boxes"], rock=rock, top=top, seed=11, disp=2.2, noise=6, faces=480)
        src[prefix + "Rocks"] = dict(boxes=A[prefix + "Rocks"]["boxes"], rock=rock, top=top, seed=12, disp=2.0, noise=6, faces=480)
        src[prefix + "Ledge"] = dict(boxes=A[prefix + "Ledge"]["boxes"], rock=rock, top=top, seed=13, disp=1.7, noise=5, faces=300)
        src[stack] = dict(boxes=A[stack]["boxes"], rock=srock, top=stop, seed=6, disp=2.2, noise=6, faces=420)
        src[stack + "Big"] = dict(boxes=A[stack + "Big"]["boxes"], rock=srock, top=stop, seed=7, disp=2.6, noise=7, faces=620)
        src[stack + "Small"] = dict(boxes=A[stack + "Small"]["boxes"], rock=srock, top=stop, seed=8, disp=1.4, noise=4, faces=160)
        src[prefix + "Arch"] = dict(boxes=ARCH_BASE, rock=rock, top=top, seed=9, disp=2.4, noise=7, faces=700)
    return src
