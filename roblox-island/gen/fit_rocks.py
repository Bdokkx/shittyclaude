"""Rock meshes made for one kind of spot on the island, so every level gets the rock that fits it
instead of the same lumpy hill everywhere:

    CliffWall     wide rock face that covers a straight run of cliff (flat back, set into the cliff)
    Buttress      tall tapering rock column against a narrow / tall cliff face
    CornerRock    L-shaped rock that wraps an outside corner of a terrace
    Overhang      lip of rock hanging over the top edge of a tall cliff
    BeachBoulders cluster of smooth round boulders for the beach / waterline
    FlatStones    low flat stepping stones for terrace tops
    RoundBoulder  single rounded boulder for terrace tops

All shapes: studs, Y up, front = +Z, back (where they meet the cliff) at z < 0.
The island placer (gen/island.py) picks the type from the spot and scales it to the cliff height.
"""
import random

from noise import vnoise, weighted

ROCK = [("rock", 3), ("rock_dark", 2), ("rock_light", 1.4), ("rock_gray", 1.2), ("rock_deep", 0.8)]
TOPS = [("grass", 3), ("grass_dark", 2), ("moss", 1.5)]
BACK = -1.5   # how far the rock is set into the cliff

WALL_H, BUTTRESS_H, CORNER_H, OVERHANG_T = 12.0, 15.0, 11.0, 3.5


def cliff_wall(seed, w=20.0, h=WALL_H, depth=4.5):
    rng = random.Random(seed)
    b = []
    cols = int(w / 2)
    for i in range(cols):
        x0 = -w / 2 + i * 2
        edge = min(i, cols - 1 - i)
        ch = h * min(1.0, 0.6 + 0.16 * edge) * (0.92 + 0.08 * vnoise(i * 0.7, 0.3, seed))
        y, dep = 0.0, depth
        while y < ch - 0.3:
            lh = min(rng.choice((1.5, 2.0, 2.5)), ch - y)
            dep = depth * (0.45 + 0.55 * vnoise(i * 0.55, y * 0.35, seed + 3)) * (1 - 0.35 * y / ch)
            b.append((x0, y, BACK, x0 + 2, y + lh, max(0.8, dep), weighted(rng, ROCK)))
            y += lh
        b.append((x0, ch, BACK, x0 + 2, ch + 0.6, max(0.6, dep * 0.8), weighted(rng, TOPS)))
    return b


def buttress(seed, w=7.0, h=BUTTRESS_H, depth=5.0):
    rng = random.Random(seed)
    b = []
    y = 0.0
    while y < h - 0.3:
        t = y / h
        lh = min(rng.choice((1.5, 2.0, 2.5)), h - y)
        ww = w * (1 - 0.45 * t) * rng.uniform(0.9, 1.05)
        dd = depth * (1 - 0.5 * t) * rng.uniform(0.85, 1.05)
        ox = rng.uniform(-0.6, 0.6)
        b.append((ox - ww / 2, y, BACK, ox + ww / 2, y + lh, dd, weighted(rng, ROCK)))
        y += lh
    b.append((-w * 0.28, h, BACK, w * 0.28, h + 0.6, depth * 0.45, weighted(rng, TOPS)))
    return b


def corner_rock(seed, arm=9.0, h=CORNER_H, th=3.5):
    """Corner point at the origin; the terrace is the x<0, z<0 quarter, the arms hug its two
    outside faces (one along x at z>0, one along z at x>0) and meet in a tall rounded corner."""
    rng = random.Random(seed)
    b = []

    def column(x0, z0, x1, z1, ch):
        y = 0.0
        while y < ch - 0.3:
            lh = min(rng.choice((1.5, 2.0, 2.5)), ch - y)
            shrink = 0.3 * y / ch
            b.append((x0, y, z0, x1 - (x1 - x0) * shrink * (x1 > 0), y + lh, z1 - (z1 - z0) * shrink * (z1 > 0),
                      weighted(rng, ROCK)))
            y += lh
        b.append((x0, ch, z0, x1, ch + 0.6, z1, weighted(rng, TOPS)))

    column(BACK, BACK, th + 0.5, th + 0.5, h)              # the corner itself
    k = 0
    for s in range(int(arm / 2)):
        a0 = -(s + 1) * 2
        ch = h * (0.85 - 0.06 * s) * (0.9 + 0.2 * vnoise(s * 0.8, 1.7, seed))
        d1 = th * (0.6 + 0.5 * vnoise(s * 0.6, 2.9, seed + k))
        column(a0, BACK, a0 + 2, d1, ch)                   # arm along x, out toward +z
        d2 = th * (0.6 + 0.5 * vnoise(s * 0.6, 5.3, seed + k + 1))
        column(BACK, a0, d2, a0 + 2, ch)                   # arm along z, out toward +x
        k += 2
    return b


def overhang(seed, w=14.0, t=OVERHANG_T, out=5.0):
    """Origin at the cliff top edge: hangs below y=0 and out to +z; grassy lip on top."""
    rng = random.Random(seed)
    b = []
    for i in range(int(w / 2)):
        x0 = -w / 2 + i * 2
        edge = min(i, int(w / 2) - 1 - i)
        o = out * min(1.0, 0.55 + 0.2 * edge) * rng.uniform(0.8, 1.0)
        drip = t * rng.uniform(0.6, 1.0) * min(1.0, 0.6 + 0.2 * edge)
        b.append((x0, -drip, -2.5, x0 + 2, -0.6, o, weighted(rng, ROCK)))
        b.append((x0, -0.6, -2.5, x0 + 2, 0.4, o - 0.5, weighted(rng, TOPS)))
    return b


def _round(rng, cx, cz, r, h, shades):
    """Rounded boulder from 1-stud columns shaped like a squashed half-ellipsoid."""
    b = []
    n = int(r) + 1
    for i in range(-n, n):
        for k in range(-n, n):
            x, z = i + 0.5, k + 0.5
            d = (x / r) ** 2 + (z / (r * 0.85)) ** 2
            if d > 1:
                continue
            ch = h * (1 - d) ** 0.55
            if ch < 0.4:
                continue
            b.append((cx + x - 0.5, 0, cz + z - 0.5, cx + x + 0.5, round(ch, 2), cz + z + 0.5, weighted(rng, shades)))
    return b


def beach_boulders(seed):
    rng = random.Random(seed)
    shades = [("rock_light", 3), ("rock_gray", 2), ("rock", 1)]
    b = _round(rng, 0, 0, 3.6, 4.8, shades)
    b += _round(rng, 5.4, 1.6, 2.4, 3.0, shades)
    b += _round(rng, -4.2, 2.6, 1.8, 2.2, shades)
    b += _round(rng, 1.6, -4.4, 1.6, 1.8, shades)
    return b


def flat_stones(seed):
    rng = random.Random(seed)
    b = []
    for (cx, cz, w, d, h) in ((0, 0, 6, 5, 1.4), (7, 3, 4, 3.5, 1.0), (-6, 3.8, 3.5, 3, 0.9),
                              (2.5, -6.5, 4.5, 3, 1.1), (-5, -5, 2.5, 2.5, 0.7)):   # gaps so they stay separate
        cx, cz = cx + rng.uniform(-0.5, 0.5), cz + rng.uniform(-0.5, 0.5)
        b.append((cx - w / 2, 0, cz - d / 2, cx + w / 2, h, cz + d / 2, weighted(rng, [("rock_gray", 2), ("rock_light", 2)])))
        b.append((cx - w / 2 + 0.6, h, cz - d / 2 + 0.6, cx + w / 2 - 0.6, h + 0.3, cz + d / 2 - 0.6,
                  weighted(rng, [("rock_light", 2), ("moss", 1)])))
    return b


def round_boulder(seed):
    rng = random.Random(seed)
    b = _round(rng, 0, 0, 4.2, 6.5, [("rock_light", 2), ("rock_gray", 2), ("rock", 1)])
    b.append((-1.5, 6.5, -1.2, 1.5, 7.0, 1.2, weighted(rng, TOPS)))
    return b


SHAPES = {   # name -> (builder, seed, mesh params)
    "CliffWall": (cliff_wall, 61, dict(disp=1.5, noise=5, faces=460)),
    "Buttress": (buttress, 62, dict(disp=1.3, noise=4.5, faces=320)),
    "CornerRock": (corner_rock, 63, dict(disp=1.4, noise=4.5, faces=420)),
    "Overhang": (overhang, 64, dict(disp=1.0, noise=4, faces=260, voxel=0.6)),
    "BeachBoulders": (beach_boulders, 65, dict(disp=0.9, noise=3.5, faces=260, voxel=0.6)),
    "FlatStones": (flat_stones, 66, dict(disp=0.45, noise=3, faces=200, voxel=0.45, plain=True)),
    "RoundBoulder": (round_boulder, 67, dict(disp=1.2, noise=4, faces=180, voxel=0.7)),
}
# theme prefix, rock / top mesh colours, beach top colour
THEME_ROCKS = {
    "voxel": ("", "rock", "grass", "sand"),
    "desert": ("Desert", "red_rock", "desert_sand", "desert_sand_lt"),
    "frost": ("Ice", "frost_rock", "snow", "snow"),
    "volcanic": ("Basalt", "basalt", "scorched", "ash"),
}


def fit_rock_assets(asset, recolor, maps):
    """maps: theme -> recolour mapping (None for voxel). Returns {name: asset}."""
    out = {}
    for theme, (prefix, _r, _t, _b) in THEME_ROCKS.items():
        for name, (fn, seed, _m) in SHAPES.items():
            boxes = fn(seed)
            out[prefix + name] = asset(recolor(boxes, maps[theme]) if maps[theme] else boxes)
    return out


def fit_rock_mesh_sources(A):
    src = {}
    for theme, (prefix, rock, top, beach) in THEME_ROCKS.items():
        for name, (_fn, seed, params) in SHAPES.items():
            params = dict(params)
            plain = params.pop("plain", False)   # bare stone, no grass / sand top
            src[prefix + name] = dict(boxes=A[prefix + name]["boxes"], rock=rock,
                                      top=rock if plain else beach if name == "BeachBoulders" else top,
                                      seed=seed, **params)
    return src
