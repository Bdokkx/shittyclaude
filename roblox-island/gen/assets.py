"""Voxel asset definitions — the single source of truth for both the Blender
meshes and the Roblox part-built models.

Units are studs, Y is up, origin is the asset's ground point (bottom centre).
Each asset is a list of axis-aligned boxes (x0, y0, z0, x1, y1, z1, color)
plus optional lights / fires.
"""


def B(cx, y, cz, sx, sy, sz, c):
    """Box centred on (cx, cz) horizontally, sitting on y."""
    return (cx - sx / 2, y, cz - sz / 2, cx + sx / 2, y + sy, cz + sz / 2, c)


EPS = 0.04  # enough separation for Roblox's depth buffer


def _overlap(a0, a1, b0, b1):
    return min(a1, b1) - max(a0, b0) > 1e-6


def dezfight(boxes):
    """Push apart faces of differently-coloured boxes that lie in the same plane,
    face the same way and overlap (they would flicker in Roblox). The later box
    grows outward by EPS on that face. Faces resting on the ground are left alone."""
    bx = [list(b) for b in boxes]
    ground = min(b[1] for b in bx)
    for _ in range(8):
        changed = False
        for i in range(len(bx)):
            for j in range(i + 1, len(bx)):
                p, q = bx[i], bx[j]
                if p[6] == q[6]:
                    continue
                for ax in range(3):
                    if not all(_overlap(p[k], p[k + 3], q[k], q[k + 3]) for k in range(3) if k != ax):
                        continue
                    for side in (0, 3):
                        if abs(p[ax + side] - q[ax + side]) < 1e-6:
                            if ax == 1 and side == 0 and abs(q[1] - ground) < 1e-6:
                                continue
                            q[ax + side] += EPS if side else -EPS
                            changed = True
        if not changed:
            break
    return [tuple(round(v, 3) if isinstance(v, float) else v for v in b) for b in bx]


def asset(boxes, lights=(), fires=(), tintable=False):
    return {"boxes": dezfight(boxes), "lights": list(lights), "fires": list(fires),
            "tintable": tintable}


# ---------------------------------------------------------------- plants

def pine(tiers=6, tip_tiers=3):
    b = [B(0, 0, 0, 2, 4 + tiers, 2, "trunk")]
    size = 2 * tiers
    y = 3
    for i in range(tiers):
        c = "leaf_dark" if i % 2 == 0 else "leaf"
        b.append(B(0, y, 0, size, 3, size, c))
        if i < tip_tiers:
            h = size / 2 + 0.5
            o = 1 if i % 2 else -1
            alt = "leaf" if c == "leaf_dark" else "leaf_dark"
            b += [B(h, y + 0.5, o, 1, 1.5, 2, alt), B(-h, y + 0.5, -o, 1, 1.5, 2, alt),
                  B(-o, y + 0.5, h, 2, 1.5, 1, alt), B(o, y + 0.5, -h, 2, 1.5, 1, alt)]
        size = max(2, size - 2)
        y += 3
    b.append(B(0, y, 0, 1, 1, 1, "leaf"))
    return asset(b)


def bush():
    return asset([B(0, 0, 0, 6, 3, 6, "leaf"), B(1, 2, -1, 4, 2, 4, "leaf_dark"),
                  B(-2, 0, 2, 3, 4, 3, "grass_dark"), B(2.5, 0, 2, 2, 2, 2, "leaf_dark")])


def seaweed():
    b = []
    for sx, sz, h, ph in [(0, 0, 13, 0), (2, 1, 10, 1), (-1.5, 1.5, 8, 0), (0.5, -2, 9, 1)]:
        for k in range(int(h / 2)):
            off = 0.7 if (k + ph) % 2 else -0.7
            b.append(B(sx + off, k * 2, sz, 1, 2.2, 1, "seaweed" if k % 3 else "seaweed_dk"))
    return asset(b)


def coral_root():
    return [B(0, 0, 0, 5, 2, 5, "coral_root"), B(0.5, 1.5, 0, 4, 1, 3.5, "coral_root"),
            B(-1, 0, 1.5, 3, 1.5, 3, "coral_root")]


def tube_coral():
    b = coral_root()
    for x, z, h in [(-1.1, -1, 6), (1.2, 0, 8), (0, 1.3, 5), (-1.3, 1.2, 4), (1.4, -1.6, 3.5)]:
        b.append(B(x, 2, z, 1.6, h, 1.6, "accent"))
        b.append(B(x, 2 + h, z, 1.0, 0.4, 1.0, "accent_dark"))  # hollow-tube rim hint
    return asset(b, tintable=True)


def branch_coral():
    b = coral_root()
    b.append(B(0, 2, 0, 1.4, 3, 1.4, "accent"))
    for dx, dz, y, h in [(1.6, 0, 4, 4), (-1.6, 0.4, 3.5, 5), (0, 1.6, 4.5, 3.5),
                         (0.2, -1.6, 4, 3)]:
        b.append(B(dx / 2, y, dz / 2, 1.4 + abs(dx), 1, 1.4 + abs(dz), "accent_dark"))
        b.append(B(dx, y, dz, 1.2, h, 1.2, "accent"))
        b.append(B(dx * 1.6, y + h - 1, dz * 1.6, 1.0, 2, 1.0, "accent"))
    return asset(b, tintable=True)


def fan_coral():
    b = coral_root()
    for i in range(5):
        w = 6 - abs(i - 2) * 1.5
        b.append(B(0, 2 + i * 1.4, 0, w, 1.4, 0.8, "accent" if i % 2 else "accent_dark"))
    return asset(b, tintable=True)


# ---------------------------------------------------------------- rocks

def rock():
    return asset([B(0, 0, 0, 6, 3, 5, "rock"), B(0.5, 3, 0, 4, 2, 4, "rock_dark"),
                  B(-2, 0, 1.5, 3, 4, 3, "rock"), B(0, 5, 0.5, 2, 1, 2, "rock")])


def rock_spire():
    b = []
    layers = [(14, 4, 12, 0, 0), (12, 4, 11, 1, -1), (11, 4, 9, -1, 0), (9, 4, 8, 0, 1),
              (7, 3, 6, 1, 0), (4, 3, 4, 0, 0)]
    y = 0
    for i, (sx, h, sz, ox, oz) in enumerate(layers):
        b.append(B(ox, y, oz, sx, h, sz, "rock" if i % 2 == 0 else "rock_dark"))
        y += h
    b += [B(-3, 12, 2, 3, 2, 3, "rock"), B(3, 8, -3, 3, 2, 3, "rock_dark"),
          B(0, y, 0, 3, 1, 3, "grass"), B(-1, y - 2, 2, 2, 1, 2, "grass_dark")]
    return asset(b)


def boulder():
    return asset([B(0, 0, 0, 9, 2, 9, "rock_light"), B(0, 2, 0, 8, 2, 8, "rock_light"),
                  B(0, 4, 0, 6.5, 1.5, 6.5, "rock_light"), B(0, 5.5, 0, 4.5, 1, 4.5, "rock_light"),
                  B(0, 6.5, 0, 2, 0.6, 2, "rock_light")])


def arch():
    b = [B(-9, 0, 0, 7, 14, 8, "rock"), B(9, 0, 0, 7, 14, 8, "rock"),
         B(0, 14, 0, 25, 6, 8, "rock_dark"), B(-6, 12, 0, 3, 2, 7.6, "rock"),
         B(6, 12, 0, 3, 2, 7.6, "rock"), B(-11.3, 4, 1, 3, 6, 9, "rock_dark"),
         B(10, 6, -1, 3, 5, 9, "rock_dark"),
         B(0, 20, 0, 25, 1.5, 8, "sand"), B(0, 21.5, 0, 25, 1.5, 8, "grass"),
         B(-7, 23, 1, 6, 2, 4, "leaf_dark"), B(6, 23, -1, 4, 3, 4, "leaf")]
    return asset(b)


# ---------------------------------------------------------------- reef rock formations

def reef_pinnacle():
    b = []
    y = 0
    for i, (sx, sz, h, ox, oz) in enumerate([(14, 12, 4, 0, 0), (10, 10, 4, 2, -1),
                                              (12, 8, 3, -1, 1), (8, 9, 4, 1, 0),
                                              (10, 7, 3, -2, -1), (6, 6, 4, 0, 1)]):
        b.append(B(ox, y, oz, sx, h, sz, "rock" if i % 2 == 0 else "rock_dark"))
        b.append(B(ox + sx * 0.15, y + h, oz, sx * 0.6, 0.6, sz * 0.6, "reef_sand"))
        y += h
    b.append(B(0, y, 1, 6.4, 0.8, 6.4, "reef_sand"))
    return asset(b)


def reef_shelf():
    return asset([B(-7, 0, 0, 7, 8, 7, "rock"), B(8, 0, 1, 6, 8, 6, "rock_dark"),
                  B(0, 8, 0, 28, 3, 16, "rock"), B(2, 6, 0, 22, 2, 12, "rock_dark"),
                  B(0, 11, 0, 27, 0.8, 15, "reef_sand"),
                  B(-4, 11.8, 2, 10, 2, 8, "rock"), B(-4, 13.8, 2, 9, 0.6, 7, "reef_sand")])


def reef_arch():
    return asset([B(-8, 0, 0, 6, 10, 7, "rock"), B(8, 0, 0, 6, 10, 7, "rock_dark"),
                  B(0, 10, 0, 22, 4, 8, "rock"), B(0, 14, 0, 21, 0.7, 7, "reef_sand"),
                  B(-5, 8, 0, 3, 2, 7, "rock_dark"), B(5, 8, 0, 3, 2, 7, "rock")])


def ruin_pillar():
    return asset([B(0, 0, 0, 5, 1.5, 5, "stone_dark"), B(0, 1.5, 0, 3.5, 9, 3.5, "stone"),
                  B(0.5, 10.5, 0, 4.5, 1.5, 4.5, "stone_dark"), B(-0.5, 12, 0.5, 2.5, 1, 2.5, "stone"),
                  B(2.5, 0, 2, 2, 1.5, 2, "stone")])


# ---------------------------------------------------------------- built props

def dock():
    """Origin = land end of the deck; deck top at y=0, extends toward +Z."""
    b = []
    L, W = 36, 10
    for k in range(int(L / 2)):  # planks across, alternating tone
        b.append(B(0, -1, k * 2 + 1, W, 1, 1.9, "plank" if k % 2 else "wood"))
    for z in range(0, L + 1, 9):
        for x in (-W / 2 + 0.5, W / 2 - 0.5):
            b.append(B(x, -12, min(z, L - 0.5), 1.2, 13.5, 1.2, "wood_dark"))
    for x in (-W / 2 + 0.3, W / 2 - 0.3):
        b.append(B(x, -1.6, L / 2, 0.6, 0.6, L, "wood_dark"))  # stringers
    # mooring posts + rope rail at the end
    for x in (-W / 2 + 0.5, W / 2 - 0.5):
        b.append(B(x, 0, L - 0.5, 1.4, 4, 1.4, "wood_dark"))
    b.append(B(0, 2.5, L - 0.5, W, 0.5, 0.5, "wood"))
    # lantern post
    b += [B(W / 2 - 0.5, 0, 2, 1, 9, 1, "wood_dark"), B(W / 2 - 1.5, 8, 2, 2.5, 0.6, 0.6, "wood_dark"),
          B(W / 2 - 2.6, 6.4, 2, 1.2, 1.6, 1.2, "glow"), B(W / 2 - 2.6, 8, 2, 1.4, 0.3, 1.4, "metal")]
    return asset(b, lights=[(W / 2 - 2.6, 7.2, 2, "glow", 18, 1.5)])


def rowboat():
    """Origin = waterline. Long axis Z."""
    return asset([B(0, -1, 0, 3, 1, 9, "wood_dark"),
                  B(-2, -0.6, 0, 1, 2.2, 10, "wood"), B(2, -0.6, 0, 1, 2.2, 10, "wood"),
                  B(0, -0.6, 5.2, 3, 2.2, 1, "wood"), B(0, -0.6, -5.2, 3, 2.2, 1, "wood"),
                  B(0, 0, 6.1, 1.6, 1.6, 1, "wood_dark"), B(0, 0.4, 0, 3, 0.4, 1.4, "plank"),
                  B(0, 0.4, -3, 3, 0.4, 1.4, "plank"), B(-1, 0.8, 2, 0.4, 0.4, 6, "wood_dark")])


def shipwreck():
    """Long axis Z, bow toward +Z. Broken in the middle."""
    b = []
    hull = [(4, 2, 44, "ship_dark"), (10, 3, 50, "ship"), (14, 3, 56, "ship_dark"), (16, 3, 58, "ship")]
    y = 0
    for w, h, length, c in hull:
        for seg_z, seg_l in ((-length / 4 - 2, length / 2 - 4), (length / 4 + 1, length / 2 - 2)):
            b.append(B(0, y, seg_z, w, h, seg_l, c))
        y += h
    # walls above deck line + raised stern
    b += [B(-7.5, y, -14, 1, 3, 24, "ship_dark"), B(7.5, y, -14, 1, 3, 24, "ship_dark"),
          B(-7.5, y, 16, 1, 2, 22, "ship_dark"), B(7.5, y, 17, 1, 3, 20, "ship_dark"),
          B(0, y, -24, 14, 6, 8, "ship"), B(0, y + 6, -24, 15, 1, 9, "ship_dark"),
          B(0, y, -14, 14, 0.4, 24, "plank"), B(0, y, 16, 14, 0.4, 22, "plank")]
    # bow + bowsprit
    b += [B(0, 3, 30.5, 8, 6, 3, "ship"), B(0, 6, 33, 4, 4, 3, "ship_dark"),
          B(0, 9, 38, 1.2, 1.2, 12, "wood_dark")]
    # masts (one standing, one snapped & lying on deck)
    b += [B(0, y - 1, 6, 2, 26, 2, "wood_dark"), B(0, y + 17, 6, 16, 1, 1, "wood_dark"),
          B(0, y - 1, -10, 2, 8, 2, "wood_dark"), B(3, y + 1, -18, 1.6, 1.6, 18, "wood_dark")]
    # ribs exposed at the break
    for z in (-3, 1):
        b.append(B(-6.5, 3, z, 1, 9, 1, "ship_dark"))
        b.append(B(6.5, 3, z, 1, 9, 1, "ship_dark"))
    return asset(b)


def market_stall():
    b = []
    for x in (-5, 5):
        for z in (-3, 3):
            b.append(B(x, 0, z, 1, 9 if z < 0 else 7.5, 1, "wood_dark"))
    b += [B(0, 0, 3, 10, 3.5, 2, "wood"), B(0, 3.5, 3, 11, 0.5, 2.6, "plank"),
          B(-2, 4, 3, 2, 1, 1.5, "fire"), B(1.5, 4, 3, 1.5, 1.5, 1.5, "grass"),
          B(3.5, 4, 3.2, 1.2, 0.8, 1.2, "flag_blue")]
    # striped awning, stepping down toward the front (+Z)
    for row in range(5):
        yy = 9 - row * 0.4
        zz = -3.5 + row * 1.8
        for s in range(6):
            c = "cloth" if s % 2 == 0 else "cloth_brown"
            b.append(B(-5 + s * 2 + 0, yy, zz, 2, 0.5, 1.9, c))
    for s in range(6):  # scalloped front edge
        c = "cloth" if s % 2 == 0 else "cloth_brown"
        b.append(B(-5 + s * 2, 6.8, 5.5, 2, 1.2, 0.3, c))
    # crates & barrel beside
    b += [B(7.5, 0, 1, 3, 3, 3, "wood"), B(7.5, 3, 1.4, 2.4, 2.4, 2.4, "plank"),
          B(-7.5, 0, 2, 2.6, 3.6, 2.6, "wood_dark"), B(-7.5, 3.6, 2, 2.2, 0.4, 2.2, "metal")]
    return asset(b)


def campfire():
    b = []
    for (x, z) in [(2.5, 0), (-2.5, 0), (0, 2.5), (0, -2.5), (1.8, 1.8), (-1.8, 1.8),
                   (1.8, -1.8), (-1.8, -1.8)]:
        b.append(B(x, 0, z, 1.4, 1, 1.4, "stone" if (x + z) % 2 else "stone_dark"))
    b += [B(0, 0.2, 0, 4, 0.8, 0.8, "trunk"), B(0, 0.6, 0, 0.8, 0.8, 4, "wood_dark"),
          B(0, 1, 0, 2, 2, 2, "fire"), B(0.3, 1.5, -0.2, 1, 2.5, 1, "fire_core"),
          B(-0.6, 1.4, 0.5, 0.7, 1.4, 0.7, "fire")]
    # log benches
    b += [B(0, 0, 6, 6, 1.4, 1.4, "trunk"), B(-6, 0, 0, 1.4, 1.4, 6, "trunk")]
    return asset(b, lights=[(0, 3, 0, "fire", 26, 2)], fires=[(0, 1.5, 0, 3)])


def lamp_post():
    return asset([B(0, 0, 0, 1.6, 1, 1.6, "stone_dark"), B(0, 1, 0, 1, 10, 1, "wood_dark"),
                  B(0.9, 10, 0, 2.8, 0.6, 0.6, "wood_dark"), B(1.8, 8.2, 0, 1.2, 1.6, 1.2, "glow"),
                  B(1.8, 9.8, 0, 1.6, 0.4, 1.6, "metal")],
                 lights=[(1.8, 9, 0, "glow", 20, 1.4)])


def flag_frame():
    b = [B(0, 0, 0, 12, 1, 5, "stone_dark"),
         B(-5, 1, 0, 1.4, 16, 1.4, "wood_dark"), B(5, 1, 0, 1.4, 16, 1.4, "wood_dark"),
         B(0, 15, 0, 13, 1.4, 1.4, "wood"), B(0, 12, 0, 12, 0.8, 0.8, "wood_dark"),
         B(-4, 6, 1, 1, 1, 1, "wood_dark"), B(4, 6, 1, 1, 1, 1, "wood_dark"),
         B(6.6, 15.2, 0, 1, 1, 1, "wood_dark")]
    # blue banner hanging from the crossbeam
    b += [B(0, 7, 0, 7, 8, 0.4, "flag_blue"), B(-2.5, 6, 0, 2, 1, 0.4, "flag_blue"),
          B(2.5, 6, 0, 2, 1, 0.4, "flag_blue"),
          B(0, 10, 0, 3, 3, 0.6, "cloth"), B(0, 10.75, 0, 1.4, 1.5, 0.8, "flag_blue")]
    # lantern hanging
    b += [B(-3.5, 12.6, 0.6, 0.3, 2, 0.3, "metal"), B(-3.5, 11, 0.6, 1, 1.4, 1, "glow")]
    return asset(b, lights=[(-3.5, 11.7, 0.6, "glow", 16, 1)])


def fence(length=8):
    b = []
    for x in (-length / 2, 0, length / 2):
        b.append(B(x, 0, 0, 0.8, 4, 0.8, "wood_dark"))
    b += [B(0, 1.4, 0, length, 0.5, 0.4, "wood"), B(0, 3, 0, length, 0.5, 0.4, "wood")]
    return asset(b)


def crate_stack():
    return asset([B(0, 0, 0, 3, 3, 3, "wood"), B(3.2, 0, 0.3, 3, 3, 3, "plank"),
                  B(1.5, 3, 0.2, 3, 3, 3, "wood"), B(-2.6, 0, 2, 2.4, 3.4, 2.4, "wood_dark"),
                  B(-2.6, 3.4, 2, 2, 0.3, 2, "metal")])


def stairs(width=6, steps=6, rise=1.5, run=2):
    """Wooden stairs climbing toward +Z, origin at the bottom front."""
    b = []
    for k in range(steps):
        b.append(B(0, 0, k * run + run / 2, width, (k + 1) * rise, run, "plank" if k % 2 else "wood"))
    for x in (-width / 2 - 0.3, width / 2 + 0.3):
        for k in range(0, steps + 1, 3):
            b.append(B(x, k * rise, k * run, 0.6, 4, 0.6, "wood_dark"))
    return asset(b)


ASSETS = {
    "PineTree": pine(6, 3),
    "PineTreeTall": pine(8, 4),
    "Bush": bush(),
    "Rock": rock(),
    "RockSpire": rock_spire(),
    "Boulder": boulder(),
    "Arch": arch(),
    "Seaweed": seaweed(),
    "TubeCoral": tube_coral(),
    "BranchCoral": branch_coral(),
    "FanCoral": fan_coral(),
    "ReefPinnacle": reef_pinnacle(),
    "ReefShelf": reef_shelf(),
    "ReefArch": reef_arch(),
    "RuinPillar": ruin_pillar(),
    "Dock": dock(),
    "Rowboat": rowboat(),
    "Shipwreck": shipwreck(),
    "MarketStall": market_stall(),
    "Campfire": campfire(),
    "LampPost": lamp_post(),
    "FlagFrame": flag_frame(),
    "Fence": fence(),
    "CrateStack": crate_stack(),
    "WoodenStairs": stairs(),
}


def bounds(name):
    bx = ASSETS[name]["boxes"]
    mn = [min(b[i] for b in bx) for i in range(3)]
    mx = [max(b[i + 3] for b in bx) for i in range(3)]
    return mn, mx
