"""Voxel asset definitions: the single source of truth for both the Blender
meshes and the Roblox part-built models.

Units are studs, Y is up, origin is the asset's ground point (bottom centre).
Each asset is a list of axis-aligned boxes (x0, y0, z0, x1, y1, z1, color)
plus optional lights / fires.
"""
import math
import random

from noise import vnoise, weighted

ROCK_SHADES = [("rock", 3), ("rock_dark", 2), ("rock_light", 1.4), ("rock_gray", 1.2),
               ("rock_deep", 1), ("moss", 0.25), ("moss_dark", 0.15)]
GRAY_ROCK_SHADES = [("rock_gray", 3), ("rock", 2), ("rock_dark", 1.5), ("rock_light", 1),
                    ("stone_dark", 1), ("rock_deep", 0.8)]


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
    # round first: comparing unrounded values and rounding afterwards can create new coincidences
    bx = [[round(v, 3) if isinstance(v, float) else v for v in b] for b in boxes]
    ground = min(b[1] for b in bx)
    for _ in range(80):
        changed = False
        for i in range(len(bx)):
            p = bx[i]
            for j in range(i + 1, len(bx)):
                q = bx[j]
                if p[6] == q[6]:
                    continue
                if not (p[0] < q[3] + 1e-6 and q[0] < p[3] + 1e-6 and p[1] < q[4] + 1e-6
                        and q[1] < p[4] + 1e-6 and p[2] < q[5] + 1e-6 and q[2] < p[5] + 1e-6):
                    continue
                for ax in range(3):
                    if not all(_overlap(p[k], p[k + 3], q[k], q[k + 3]) for k in range(3) if k != ax):
                        continue
                    for side in (0, 3):
                        if abs(p[ax + side] - q[ax + side]) < 1e-6:
                            if ax == 1 and side == 0 and abs(q[1] - ground) < 1e-6:
                                continue
                            e = EPS + (j % 5) * 0.013  # per-box step so nudges don't line up again
                            q[ax + side] += e if side else -e
                            changed = True
        if not changed:
            break
    return [tuple(round(v, 3) if isinstance(v, float) else v for v in b) for b in bx]


def asset(boxes, lights=(), fires=(), tintable=False):
    for b in boxes:
        assert min(b[3] - b[0], b[4] - b[1], b[5] - b[2]) > 0.01, "zero-size box %r" % (b,)
    return {"boxes": dezfight(boxes), "lights": list(lights), "fires": list(fires),
            "tintable": tintable}


# ---------------------------------------------------------------- detail helpers

def roughen(boxes, seed, targets=("rock", "rock_dark"), tile=3.0, prot=(0.25, 0.9),
            shades=ROCK_SHADES):
    """Cover the exposed side faces of big rock boxes with small protruding blocks
    in mixed shades, giving the chunky 'stacked cubes' cliff look."""
    rng = random.Random(seed)
    base = list(boxes)
    out = list(boxes)

    def covered(p, me):
        for b in base:
            if b is me:
                continue
            if b[0] < p[0] < b[3] and b[1] < p[1] < b[4] and b[2] < p[2] < b[5]:
                return True
        return False

    for b in base:
        if b[6] not in targets:
            continue
        x0, y0, z0, x1, y1, z1, _ = b
        for axis, side in ((0, 0), (0, 1), (2, 0), (2, 1)):
            u = 2 if axis == 0 else 0
            u0, u1 = (z0, z1) if axis == 0 else (x0, x1)
            plane = (x0, x1)[side] if axis == 0 else (z0, z1)[side]
            sgn = 1 if side else -1
            nu = max(1, round((u1 - u0) / tile))
            du = (u1 - u0) / nu
            for a in range(nu):
                ua, ub = u0 + a * du, u0 + (a + 1) * du
                v = y0
                while v < y1 - 1e-6:
                    h = rng.choice((tile * 0.67, tile, tile * 1.33))
                    vb = y1 if y1 - (v + h) < 1.0 else v + h
                    probe = [0, 0, 0]
                    probe[axis] = plane + sgn * 0.05
                    probe[u] = (ua + ub) / 2
                    probe[1] = (v + vb) / 2
                    if not covered(probe, b):
                        p = rng.uniform(*prot)
                        lo, hi = (plane, plane + p) if side else (plane - p, plane)
                        c = weighted(rng, shades)
                        if axis == 0:
                            out.append((lo, v, ua, hi, vb, ub, c))
                        else:
                            out.append((ua, v, lo, ub, vb, hi, c))
                    v = vb
    return out


def blob_rock(seed, rx, rz, height, vox=2.0, vh=2.5, moss=0.18, shades=GRAY_ROCK_SHADES, peak=1.5,
              tops=(("moss", 3), ("moss_dark", 2), ("grass", 1))):
    """Lumpy voxel rock built from 2-stud columns with per-voxel shading and mossy tops."""
    rng = random.Random(seed)
    ni, nk = int(round(2 * rx / vox)), int(round(2 * rz / vox))
    cols = {}
    for i in range(ni):
        for k in range(nk):
            x = (i + 0.5) * vox - rx
            z = (k + 0.5) * vox - rz
            d = math.hypot(x / rx, z / rz)
            if d > 1:
                continue
            hh = height * (1 - d ** peak) * (0.6 + 0.7 * vnoise(i * 0.55, k * 0.55, seed))
            cols[(i, k)] = max(1, int(round(hh / vh)))
    boxes = []
    for (i, k), L in cols.items():
        x0, z0 = i * vox - rx, k * vox - rz
        x1, z1 = x0 + vox, z0 + vox
        lowest = min(cols.get((i + a, k + b), 0) for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        colors = [weighted(rng, shades) for _ in range(L)]
        if rng.random() < moss:
            colors[-1] = weighted(rng, list(tops))
        start = min(lowest, L - 1)
        if start > 0:  # hidden core of the column
            boxes.append((x0, 0, z0, x1, start * vh, z1, colors[0]))
        l = start
        while l < L:
            m = l
            while m + 1 < L and colors[m + 1] == colors[l]:
                m += 1
            boxes.append((x0, l * vh, z0, x1, (m + 1) * vh, z1, colors[l]))
            l = m + 1
    return boxes


# ---------------------------------------------------------------- plants

def pine(tiers, base, seed, trunk=4):
    return asset(pine_boxes(tiers, base, seed, trunk))


def pine_boxes(tiers, base, seed, trunk=4, snow=False):
    """Voxel pine. snow=True adds snow along every tier's rim and on the crown."""
    rng = random.Random(seed)
    b = [B(0, 0, 0, 2, trunk + tiers * 3 - 1, 2, "trunk"),
         B(1.25, 0, 0.2, 0.5, 1, 1, "trunk"), B(-0.2, 0, -1.25, 1, 0.8, 0.5, "trunk")]
    s, y = base, trunk
    for i in range(tiers):
        b.append(B(0, y, 0, s, 1.5, s, "leaf_dark"))
        if s <= 2:  # top tier: just the skirt, the crown sits right on it
            y += 1.5
            break
        b.append(B(0, y + 1.5, 0, s - 2, 1.5, s - 2, "leaf"))
        w = 2 if s >= 6 else 1
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if rng.random() < 0.7:
                off = rng.choice((-1, 0, 1)) * (s / 4 if s >= 8 else 0)
                if dx:
                    b.append(B(dx * (s / 2 + 0.5), y - 0.75, off, 1, 1.5, w, "leaf_dark"))
                else:
                    b.append(B(off, y - 0.75, dz * (s / 2 + 0.5), w, 1.5, 1, "leaf_dark"))
        if s >= 6:  # sunlit rim on the skirt
            side = rng.choice((-1, 1)) * (s / 2 - 0.5)
            along = rng.uniform(-(s / 2 - 2), s / 2 - 2)
            if rng.random() < 0.5:
                b.append(B(side, y + 1.5, along, 1, 0.4, 2, "leaf_light"))
            else:
                b.append(B(along, y + 1.5, side, 2, 0.4, 1, "leaf_light"))
        y += 3
        s -= 2
        if s < 2:
            break
    b.append(B(0, y, 0, 2, 2, 2, "leaf"))
    b.append(B(0, y + 2, 0, 1, 1.2, 1, "leaf_light"))
    if snow:
        b.append(B(0, y + 2, 0, 1.2, 0.5, 1.2, "snow"))
        s, yy = base, trunk
        for i in range(tiers):
            if s <= 2:
                break
            b += [B(0, yy + 1.5, s / 2 - 0.5, s, 0.45, 1, "snow"), B(0, yy + 1.5, -(s / 2 - 0.5), s, 0.45, 1, "snow"),
                  B(s / 2 - 0.5, yy + 1.5, 0, 1, 0.45, s - 2, "snow"), B(-(s / 2 - 0.5), yy + 1.5, 0, 1, 0.45, s - 2, "snow")]
            s -= 2
            yy += 3
    return b


def bush():
    return asset([B(0, 0, 0, 5, 2.5, 4, "leaf"), B(0.8, 2.5, -0.4, 3, 1.4, 2.6, "leaf_light"),
                  B(-1.9, 0, 1.4, 2.6, 2, 2.6, "leaf_dark"), B(2.3, 0, 1.5, 2, 1.6, 2, "leaf_dark"),
                  B(-1, 2.5, 0.8, 1.6, 0.8, 1.6, "leaf"), B(1.6, 1.2, -2.2, 0.6, 0.6, 0.6, "mushroom_red")])


def grass_tuft():
    return asset([B(0, 0, 0, 0.4, 1.6, 0.4, "grass"), B(0.55, 0, 0.3, 0.4, 1.1, 0.4, "grass_light"),
                  B(-0.45, 0, 0.45, 0.4, 1.3, 0.4, "grass_dark"), B(0.1, 0, -0.55, 0.4, 0.9, 0.4, "grass_light")])


def flowers():
    b = []
    for x, z, h in ((0, 0, 1.4), (0.9, 0.5, 1.0), (-0.7, 0.7, 1.2)):
        b.append(B(x, 0, z, 0.25, h, 0.25, "grass_dark"))
        b.append(B(x, h, z, 0.7, 0.5, 0.7, "accent"))
    b.append(B(0.2, 0, 0.3, 1.8, 0.35, 1.4, "grass"))
    return asset(b, tintable=True)


def fern():
    return asset([B(0, 0, 0, 0.6, 1.2, 0.6, "leaf"), B(0.9, 0.6, 0, 1.4, 0.3, 0.6, "leaf"),
                  B(-0.9, 0.8, 0.1, 1.4, 0.3, 0.6, "leaf_light"), B(0, 0.7, 0.9, 0.6, 0.3, 1.4, "leaf"),
                  B(0.1, 0.9, -0.9, 0.6, 0.3, 1.4, "leaf_light"), B(1.7, 0.3, 0, 0.4, 0.3, 0.6, "leaf")])


def mushrooms():
    return asset([B(0, 0, 0, 0.6, 1, 0.6, "flower_white"), B(0, 1, 0, 1.6, 0.6, 1.6, "mushroom_red"),
                  B(0.35, 1.6, 0.2, 0.4, 0.15, 0.4, "flower_white"),
                  B(0.9, 0, 0.7, 0.4, 0.6, 0.4, "flower_white"), B(0.9, 0.6, 0.7, 1, 0.4, 1, "mushroom_red")])


def small_rock():
    return asset([B(0, 0, 0, 2, 1.1, 1.6, "rock_gray"), B(0.5, 0, 0.8, 1.1, 0.7, 1, "cobble"),
                  B(-0.3, 1.1, -0.1, 1.1, 0.5, 0.9, "rock_gray"), B(-0.9, 0, -0.6, 0.6, 0.4, 0.6, "moss")])


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
        b.append(B(x, 2 + h, z, 1.0, 0.4, 1.0, "accent_dark"))
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
#
# Rocks exist twice: as part-built models (roughened boxes, work everywhere) and
# as deformed, stud-textured meshes made in Blender from the *same base shapes*
# (see MESH_SOURCES + tools/blender_meshes.py). The MeshSwap command swaps the
# part versions in a placed map for the meshes once they're imported.

def boulder_base():
    return [B(0, 0, 0, 9, 2, 9, "rock_light"), B(0, 2, 0, 8, 2, 8, "rock_light"),
            B(0, 4, 0, 6.5, 1.5, 6.5, "rock_light"), B(0, 5.5, 0, 4.5, 1, 4.5, "rock_light"),
            B(0, 6.5, 0, 2, 0.6, 2, "rock_light"), B(3, 0, 3.5, 3, 1.5, 3, "rock_gray")]


def arch_base():
    """Natural rock arch, 32 wide x 24 tall x 9 deep, 20-stud opening (fits a path)."""
    return [B(-13, 0, 0, 6, 16, 9, "rock"), B(13, 0, 0, 6, 16, 9, "rock"),
            B(0, 16, 0, 32, 5, 9, "rock_dark"), B(-8.5, 14, 0, 3, 2, 8, "rock"), B(8.5, 14, 0, 3, 2, 8, "rock"),
            B(0, 21, 0, 32, 1.5, 9, "sand"), B(0, 22.5, 0, 32, 1.5, 9, "grass")]


ARCH_BASE = arch_base()


def arch():
    b = roughen(arch_base(), 11)
    b += [B(-8, 24, 1, 5, 2, 4, "leaf_dark"), B(7, 24, -2, 4, 2.5, 4, "leaf"),
          B(16.6, 18, 0, 1.4, 5, 3, "moss"), B(-16.8, 17, 2, 1.2, 6, 2, "moss_dark")]
    return asset(b)


def stacked_slabs(layers, cap=True):
    """Offset stacked slabs with small sand caps (reef pinnacles)."""
    b = []
    y = 0
    for i, (sx, sz, h, ox, oz) in enumerate(layers):
        b.append(B(ox, y, oz, sx, h, sz, "rock" if i % 2 == 0 else "rock_dark"))
        b.append(B(ox + sx * 0.15, y + h, oz, sx * 0.6, 0.6, sz * 0.6, "reef_sand"))
        y += h
    if cap:
        b.append(B(layers[-1][3], y, layers[-1][4], 6.4, 0.8, 6.4, "reef_sand"))
    return b


PINNACLE_A = [(14, 12, 4, 0, 0), (10, 10, 4, 2, -1), (12, 8, 3, -1, 1), (8, 9, 4, 1, 0),
              (10, 7, 3, -2, -1), (6, 6, 4, 0, 1)]
PINNACLE_B = [(18, 14, 3, 0, 0), (12, 11, 5, -2, 1), (16, 10, 3, 2, -1), (9, 9, 5, -1, 0),
              (13, 9, 3, 1, 2), (8, 7, 4, -2, 0), (11, 6, 2.5, 0, -1)]


def reef_shelf_base():
    return [B(-7, 0, 0, 7, 8, 7, "rock"), B(8, 0, 1, 6, 8, 6, "rock_dark"),
            B(0, 8, 0, 28, 3, 16, "rock"), B(2, 6, 0, 22, 2, 12, "rock_dark"),
            B(0, 11, 0, 27, 0.8, 15, "reef_sand"),
            B(-4, 11.8, 2, 10, 2, 8, "rock"), B(-4, 13.8, 2, 9, 0.6, 7, "reef_sand")]


def reef_arch_base():
    return [B(-8, 0, 0, 6, 10, 7, "rock"), B(8, 0, 0, 6, 10, 7, "rock_dark"),
            B(0, 10, 0, 22, 4, 8, "rock"), B(0, 14, 0, 21, 0.7, 7, "reef_sand"),
            B(-5, 8, 0, 3, 2, 7, "rock_dark"), B(5, 8, 0, 3, 2, 7, "rock")]


def rough(base, seed):
    return asset(roughen(base, seed, tile=2.5, prot=(0.2, 0.7)))


def ruin_pillar():
    return asset([B(0, 0, 0, 5, 1.5, 5, "stone_dark"), B(0, 1.5, 0, 3.5, 9, 3.5, "stone"),
                  B(0.5, 10.5, 0, 4.5, 1.5, 4.5, "stone_dark"), B(-0.5, 12, 0.5, 2.5, 1, 2.5, "stone"),
                  B(2.5, 0, 2, 2, 1.5, 2, "stone"), B(-1.9, 3, 0.5, 0.3, 3, 1.5, "moss")])


# ---------------------------------------------------------------- built props

def dock():
    """T-shaped pier. Origin = land end of the deck; deck top at y=0. The walkway runs 48 studs out
    toward +Z, then a 46-wide crossbar (the top of the T) sits across its end."""
    rng = random.Random(5)
    b = []
    L, W = 48, 10            # walkway
    TW, TD = 46, 10          # crossbar of the T
    for k in range(int(L / 2)):  # walkway planks across, slightly uneven
        j = rng.choice((0, 0.08, 0.15))
        b.append(B(0, -1 + j, k * 2 + 1, W, 1, 1.85, "plank" if k % 2 else "wood"))
    for k in range(int(TW / 2)):  # crossbar planks run the other way
        j = rng.choice((0, 0.08, 0.15))
        b.append(B(-TW / 2 + k * 2 + 1, -1 + j, L + TD / 2, 1.85, 1, TD, "plank" if k % 2 else "wood"))

    def post(x, z, tall=False):
        b.append(B(x, -12, z, 1.4, 13.5 if tall else 11.4, 1.4, "wood_dark"))

    for z in range(0, L, 10):
        zz = max(z, 0.7)
        for x in (-W / 2 - 0.2, W / 2 + 0.2):
            post(x, zz, z == 20)
        b.append(B(0, -2.6, zz, W, 0.8, 0.8, "wood_dark"))           # cross beam
        b.append(B(0, -7, zz, W - 1, 0.6, 0.6, "wood_dark"))           # lower brace
    for x in (-W / 2 + 0.3, W / 2 - 0.3):
        b.append(B(x, -1.8, L / 2, 0.6, 0.8, L, "wood_dark"))           # stringers
    for x in range(int(-TW / 2), int(TW / 2) + 1, 9):                    # crossbar posts + beams
        xx = max(min(x, TW / 2 - 0.7), -TW / 2 + 0.7)
        for z in (L + 0.2, L + TD - 0.2):
            post(xx, z, abs(x) > TW / 2 - 5)
        b.append(B(xx, -2.6, L + TD / 2, 0.8, 0.8, TD, "wood_dark"))
    for z in (L + 0.8, L + TD - 0.8):
        b.append(B(0, -1.8, z, TW, 0.8, 0.6, "wood_dark"))
    # rope rails around the outer edge of the T
    for x0, x1 in ((-TW / 2, -W / 2 - 0.5), (W / 2 + 0.5, TW / 2)):
        b.append(B((x0 + x1) / 2, 1.1, L + 0.2, x1 - x0, 0.3, 0.3, "rope"))
    b.append(B(0, 1.1, L + TD - 0.2, TW, 0.3, 0.3, "rope"))
    for x in (-TW / 2 - 0.2, TW / 2 + 0.2):
        b.append(B(x, 1.1, L + TD / 2, 0.3, 0.3, TD, "rope"))
    # crane / lantern gallows at the land end (like the reference)
    b += [B(-W / 2 + 0.8, 0, 3, 1.4, 14, 1.4, "wood_dark"), B(-W / 2 + 3.2, 12.6, 3, 6, 1.2, 1.2, "wood"),
          B(-W / 2 + 2, 10.4, 3, 1, 2.2, 1, "wood_dark"),
          B(-W / 2 + 5.4, 9.2, 3, 0.25, 3.4, 0.25, "rope"),
          B(-W / 2 + 5.4, 7.6, 3, 1.3, 1.6, 1.3, "glow"), B(-W / 2 + 5.4, 9.2, 3, 1.6, 0.35, 1.6, "metal"),
          B(-W / 2 + 5.4, 7.3, 3, 1.6, 0.3, 1.6, "metal")]
    lights = [(-W / 2 + 5.4, 8.4, 3, "glow", 22, 1.6)]
    for x in (-TW / 2 + 1.2, TW / 2 - 1.2):                               # lantern posts at both ends of the T
        z = L + TD - 1.2
        b += [B(x, 0, z, 0.9, 7, 0.9, "wood_dark"), B(x, 7, z, 1.6, 0.3, 1.6, "metal"),
              B(x, 5.4, z, 1.2, 1.6, 1.2, "glow"), B(x, 5.1, z, 1.6, 0.3, 1.6, "metal")]
        lights.append((x, 6.2, z, "glow", 20, 1.4))
    # cargo on the T
    b += [B(-14, 0.15, L + 4, 2.6, 2.6, 2.6, "wood"), B(-13.6, 2.75, L + 4.2, 2, 2, 2, "plank"),
          B(-10, 0.15, L + 3.5, 2, 2.6, 2, "barrel"), B(-10, 0.75, L + 3.5, 2.1, 0.25, 2.1, "metal"),
          B(-10, 2.0, L + 3.5, 2.1, 0.25, 2.1, "metal"), B(15, 0.15, L + 6, 1.6, 0.8, 1.6, "rope"),
          B(12, 0.15, L + 3, 2.6, 2.6, 2.6, "wood")]
    # ladders down both sides of the T
    for x in (-TW / 2 + 8, TW / 2 - 8):
        for k in range(5):
            b.append(B(x, -1.6 - k * 1.6, L + TD + 0.5, 3, 0.4, 0.4, "wood_dark"))
        b += [B(x - 1.5, -8.5, L + TD + 0.5, 0.4, 8, 0.4, "wood_dark"),
              B(x + 1.5, -8.5, L + TD + 0.5, 0.4, 8, 0.4, "wood_dark")]
    return asset(b, lights=lights)


def rowboat():
    """Origin = waterline. Long axis Z."""
    return asset([B(0, -1.2, 0, 3.2, 1, 9, "wood_dark"),
                  B(-2, -0.8, 0, 1, 2.2, 8, "wood"), B(2, -0.8, 0, 1, 2.2, 8, "wood"),
                  B(-1.4, -0.8, 4.6, 1, 2.2, 1.6, "wood"), B(1.4, -0.8, 4.6, 1, 2.2, 1.6, "wood"),
                  B(0, -0.8, 5.6, 2, 2.4, 1, "wood_dark"),
                  B(-1.4, -0.8, -4.6, 1, 2.2, 1.6, "wood"), B(1.4, -0.8, -4.6, 1, 2.2, 1.6, "wood"),
                  B(0, -0.8, -5.2, 2.6, 2.2, 0.8, "wood_dark"),
                  B(-2, 1.4, 0, 1.2, 0.3, 8.2, "wood_dark"), B(2, 1.4, 0, 1.2, 0.3, 8.2, "wood_dark"),
                  B(0, 0.4, 1.5, 3, 0.4, 1.4, "plank"), B(0, 0.4, -2.5, 3, 0.4, 1.4, "plank"),
                  B(-3.2, 1, 0.5, 2.6, 0.3, 0.3, "wood"), B(-5, 0.6, 0.5, 1.2, 0.2, 1, "wood"),
                  B(3.2, 1, -0.5, 2.6, 0.3, 0.3, "wood"), B(5, 0.6, -0.5, 1.2, 0.2, 1, "wood"),
                  B(0, -0.3, -3.6, 1.4, 1, 1.4, "rope")])


def shipwreck():
    """Long axis Z, bow toward +Z. Broken in the middle."""
    b = []
    hull = [(4, 2, 44, "ship_dark"), (10, 3, 50, "ship"), (14, 3, 56, "ship_dark"), (16, 3, 58, "ship")]
    y = 0
    for w, h, length, c in hull:
        for seg_z, seg_l in ((-length / 4 - 2, length / 2 - 4), (length / 4 + 1, length / 2 - 2)):
            b.append(B(0, y, seg_z, w, h, seg_l, c))
        y += h
    b += [B(-7.5, y, -14, 1, 3, 24, "ship_dark"), B(7.5, y, -14, 1, 3, 24, "ship_dark"),
          B(-7.5, y, 16, 1, 2, 22, "ship_dark"), B(7.5, y, 17, 1, 3, 20, "ship_dark"),
          B(0, y, -24, 14, 6, 8, "ship"), B(0, y + 6, -24, 15, 1, 9, "ship_dark"),
          B(0, y, -14, 14, 0.4, 24, "plank"), B(0, y, 16, 14, 0.4, 22, "plank")]
    b += [B(0, 3, 30.5, 8, 6, 3, "ship"), B(0, 6, 33, 4, 4, 3, "ship_dark"),
          B(0, 9, 38, 1.2, 1.2, 12, "wood_dark")]
    b += [B(0, y - 1, 6, 2, 26, 2, "wood_dark"), B(0, y + 17, 6, 16, 1, 1, "wood_dark"),
          B(0, y - 1, -10, 2, 8, 2, "wood_dark"), B(3, y + 1, -18, 1.6, 1.6, 18, "wood_dark")]
    for z in (-3, 1):
        b.append(B(-6.5, 3, z, 1, 9, 1, "ship_dark"))
        b.append(B(6.5, 3, z, 1, 9, 1, "ship_dark"))
    for x, yy, z in ((-8.2, 7, 10), (8.2, 5, -18), (-7.2, 4, -20), (8.2, 8, 20)):  # weed on hull
        b.append(B(x, yy, z, 0.5, 1.5, 3, "seaweed_dk"))
    return asset(b)


def market_stall():
    b = []
    for x in (-5, 5):
        for z in (-3, 3):
            b.append(B(x, 0, z, 1, 9 if z < 0 else 7.5, 1, "wood_dark"))
    b += [B(0, 0, 3, 10, 3.5, 2, "wood"), B(0, 3.5, 3, 11, 0.5, 2.6, "plank")]
    for k in range(5):  # front boards
        b.append(B(-4 + k * 2, 0.4, 4.1, 1.8, 2.7, 0.2, "plank" if k % 2 else "wood_dark"))
    for x, c in [(-3.6, "mushroom_red"), (-2.2, "fire_core"), (-0.8, "grass_light"),
                 (0.6, "mushroom_red"), (2, "fire"), (3.6, "flag_blue")]:  # goods
        b.append(B(x, 4, 3, 1, 0.8, 1.2, c))
    for row in range(5):  # striped awning stepping down to the front
        yy = 9 - row * 0.4
        zz = -3.5 + row * 1.8
        for s in range(6):
            b.append(B(-5 + s * 2, yy, zz, 2, 0.5, 1.9, "cloth" if s % 2 == 0 else "cloth_brown"))
    for s in range(6):
        b.append(B(-5 + s * 2, 6.8, 5.5, 2, 1.2, 0.3, "cloth" if s % 2 == 0 else "cloth_brown"))
    b += [B(0, 9.6, -3.4, 6, 1.8, 0.4, "plank"), B(0, 10, -3.65, 4, 1, 0.3, "fire")]  # sign board
    b += [B(7.5, 0, 1, 3, 3, 3, "wood"), B(7.5, 3, 1.4, 2.4, 2.4, 2.4, "plank"),
          B(-7.5, 0, 2, 2.6, 3.6, 2.6, "barrel"), B(-7.5, 3.6, 2, 2.2, 0.4, 2.2, "metal"),
          B(-7.5, 1, 2, 2.7, 0.3, 2.7, "metal")]
    return asset(b)


def campfire():
    b = []
    for k in range(8):
        a = k * math.pi / 4
        b.append(B(2.6 * math.cos(a), 0, 2.6 * math.sin(a), 1.4, 1, 1.4,
                   "stone" if k % 2 else "stone_dark"))
    b += [B(0, 0.1, 0, 4, 0.8, 0.8, "trunk"), B(0, 0.5, 0, 0.8, 0.8, 4, "wood_dark"),
          B(0, 0.9, 0, 2, 2, 2, "fire"), B(0.3, 1.4, -0.2, 1, 2.6, 1, "fire_core"),
          B(-0.6, 1.3, 0.5, 0.7, 1.5, 0.7, "fire"), B(0.7, 1.1, 0.6, 0.6, 1.2, 0.6, "fire")]
    b += [B(-3.4, 0, 0, 0.5, 4, 0.5, "wood_dark"), B(3.4, 0, 0, 0.5, 4, 0.5, "wood_dark"),
          B(0, 3.6, 0, 7.4, 0.35, 0.35, "metal"), B(0, 2.8, 0, 1.2, 0.8, 0.8, "cloth_brown")]
    b += [B(0, 0, 6.5, 6, 1.4, 1.4, "trunk"), B(-6.5, 0, 0, 1.4, 1.4, 6, "trunk"),
          B(6.5, 0, -1, 1.4, 1.4, 5, "trunk")]
    return asset(b, lights=[(0, 3.5, 0, "fire", 28, 2.2)], fires=[(0, 1.5, 0, 3)])


def lamp_post():
    return asset([B(0, 0, 0, 1.6, 1, 1.6, "stone_dark"), B(0, 1, 0, 1, 10, 1, "wood_dark"),
                  B(0.9, 10, 0, 2.8, 0.6, 0.6, "wood_dark"), B(1.8, 8.2, 0, 1.2, 1.6, 1.2, "glow"),
                  B(1.8, 9.8, 0, 1.6, 0.4, 1.6, "metal"), B(1.8, 7.9, 0, 1.6, 0.3, 1.6, "metal")],
                 lights=[(1.8, 9, 0, "glow", 20, 1.4)])


def torch():
    return asset([B(0, 0, 0, 0.7, 4.5, 0.7, "wood_dark"), B(0, 4.5, 0, 1, 0.5, 1, "metal"),
                  B(0, 5, 0, 0.8, 1.2, 0.8, "fire"), B(0, 5.4, 0, 0.45, 1.1, 0.45, "fire_core")],
                 lights=[(0, 5.6, 0, "fire", 14, 1)])


def wood_frame():
    """Wooden frame with two hanging lanterns (plaza decoration from the reference)."""
    b = [B(-5, 0, 0, 1.2, 11, 1.2, "wood_dark"), B(5, 0, 0, 1.2, 11, 1.2, "wood_dark"),
         B(0, 11, 0, 13, 1.2, 1.4, "wood"), B(-3.9, 9.8, 0, 1, 1.2, 1, "wood_dark"),
         B(3.9, 9.8, 0, 1, 1.2, 1, "wood_dark"), B(-5, 0, 0, 2, 0.8, 2, "stone_dark"),
         B(5, 0, 0, 2, 0.8, 2, "stone_dark")]
    for x in (-2, 2):
        b += [B(x, 8.6, 0, 0.25, 2.4, 0.25, "rope"), B(x, 7.2, 0, 1.2, 1.4, 1.2, "glow"),
              B(x, 8.6, 0, 1.5, 0.3, 1.5, "metal"), B(x, 6.9, 0, 1.5, 0.3, 1.5, "metal")]
    return asset(b, lights=[(-2, 7.9, 0, "glow", 16, 1.1), (2, 7.9, 0, "glow", 16, 1.1)])


def statue():
    return asset([B(0, 0, 0, 5, 1.5, 5, "stone_dark"), B(0, 1.5, 0, 4, 2, 4, "stone"),
                  B(-0.7, 3.5, 0, 1.2, 3.5, 1.4, "stone"), B(0.7, 3.5, 0, 1.2, 3.5, 1.4, "stone"),
                  B(0, 7, 0, 3.2, 3.8, 1.8, "stone"), B(0, 10.8, 0, 1.8, 1.8, 1.8, "stone"),
                  B(0, 12.6, 0, 1.2, 0.6, 1.2, "stone_dark"),
                  B(-2.1, 7.6, 0, 1, 3, 1, "stone"), B(2.1, 7.6, 0.3, 1, 3, 1, "stone"),
                  B(2.1, 5, 1.1, 0.5, 7.5, 0.5, "stone_dark"), B(2.1, 9.6, 1.1, 1.8, 0.4, 0.5, "stone_dark"),
                  B(-2.8, 6.8, 0.8, 0.5, 3.2, 2.6, "stone_dark"), B(-1.2, 1.5, 2.1, 1.6, 1, 0.3, "moss")])


def signpost():
    return asset([B(0, 0, 0, 0.8, 7, 0.8, "wood_dark"), B(1.6, 5.2, 0, 3.6, 1.1, 0.3, "plank"),
                  B(3.6, 5.35, 0, 0.6, 0.8, 0.3, "plank"), B(-1.4, 3.8, 0.1, 3, 1, 0.3, "wood"),
                  B(-3.1, 3.95, 0.1, 0.5, 0.7, 0.3, "wood"), B(0, 7, 0, 1.1, 0.4, 1.1, "wood")])


def bench():
    return asset([B(0, 1.4, 0, 5, 0.5, 1.6, "plank"), B(-2, 0, 0, 0.6, 1.4, 1.4, "wood_dark"),
                  B(2, 0, 0, 0.6, 1.4, 1.4, "wood_dark"), B(0, 1.9, -0.65, 5, 1.6, 0.3, "wood")])


def well():
    b = [B(0, 0, -2.4, 6, 3, 1.2, "stone"), B(0, 0, 2.4, 6, 3, 1.2, "stone"),
         B(-2.4, 0, 0, 1.2, 3, 3.6, "stone_dark"), B(2.4, 0, 0, 1.2, 3, 3.6, "stone_dark"),
         B(0, 0, 0, 3.6, 2.2, 3.6, "flag_blue"),
         B(-2.6, 3, 0, 0.8, 5, 0.8, "wood_dark"), B(2.6, 3, 0, 0.8, 5, 0.8, "wood_dark"),
         B(0, 6.6, 0, 6, 0.5, 0.5, "wood"), B(0, 5, 0, 0.2, 1.6, 0.2, "rope"),
         B(0, 4.2, 0, 1, 0.9, 1, "barrel")]
    for k in range(3):
        b.append(B(0, 8 + k * 0.6, 0, 8 - k * 2.4, 0.6, 4, "cloth_brown" if k % 2 else "wood_dark"))
    return asset(b)


def flag_frame():
    b = [B(0, 0, 0, 13, 1, 6, "stone_dark"), B(0, 1, 0, 11, 0.4, 4.4, "plank"),
         B(-5, 1, 0, 1.4, 17, 1.4, "wood_dark"), B(5, 1, 0, 1.4, 17, 1.4, "wood_dark"),
         B(0, 16, 0, 14, 1.4, 1.4, "wood"), B(0, 12.6, 0, 9, 0.8, 0.8, "wood_dark"),
         B(-3.9, 14.8, 0, 1, 1.2, 1, "wood_dark"), B(3.9, 14.8, 0, 1, 1.2, 1, "wood_dark"),
         B(7.2, 16.2, 0, 1, 1, 1, "wood_dark"), B(-7.2, 16.2, 0, 1, 1, 1, "wood_dark")]
    b += [B(0.5, 7, 0, 6, 8.6, 0.4, "flag_blue"), B(-1.5, 6, 0, 2, 1, 0.4, "flag_blue"),
          B(2.5, 6, 0, 2, 1, 0.4, "flag_blue"),
          B(0.5, 10, 0, 3, 3, 0.6, "cloth"), B(0.5, 10.75, 0, 1.4, 1.5, 0.8, "flag_blue"),
          B(0.5, 15.6, 0, 6.4, 0.4, 0.5, "rope")]
    b += [B(-3.6, 13.4, 0.7, 0.3, 2.4, 0.3, "metal"), B(-3.6, 11.8, 0.7, 1.1, 1.5, 1.1, "glow"),
          B(-3.6, 13.2, 0.7, 1.4, 0.3, 1.4, "metal")]
    return asset(b, lights=[(-3.6, 12.5, 0.7, "glow", 18, 1.2)])


def fence():
    """4-stud fence segment along X (fits one map cell)."""
    return asset([B(-2, 0, 0, 0.7, 3.6, 0.7, "wood_dark"), B(2, 0, 0, 0.7, 3.6, 0.7, "wood_dark"),
                  B(0, 1.3, 0, 4, 0.5, 0.4, "wood"), B(0, 2.7, 0, 4, 0.5, 0.4, "wood")])


def crate_stack():
    return asset([B(0, 0, 0, 3, 3, 3, "wood"), B(3.2, 0, 0.3, 3, 3, 3, "plank"),
                  B(1.5, 3, 0.2, 3, 3, 3, "wood"), B(-2.6, 0, 2, 2.4, 3.4, 2.4, "barrel"),
                  B(-2.6, 3.4, 2, 2, 0.3, 2, "metal"), B(-2.6, 1, 2, 2.5, 0.25, 2.5, "metal"),
                  B(0, 0.2, 0, 3.1, 0.4, 3.1, "wood_dark")])


def barrels():
    b = []
    for x, z in ((0, 0), (2.3, 0.6), (1, 2.2)):
        b += [B(x, 0, z, 2, 2.6, 2, "barrel"), B(x, 0.5, z, 2.1, 0.25, 2.1, "metal"),
              B(x, 1.9, z, 2.1, 0.25, 2.1, "metal"), B(x, 2.6, z, 1.6, 0.15, 1.6, "wood_dark")]
    return asset(b)


def log_pile():
    return asset([B(0, 0, -0.8, 6, 1.5, 1.5, "trunk"), B(0.3, 0, 0.8, 6, 1.5, 1.5, "trunk"),
                  B(0.1, 1.5, 0, 6, 1.5, 1.5, "wood_dark"), B(-3.1, 0, -0.8, 0.2, 1.5, 1.5, "plank"),
                  B(-2.8, 0, 0.8, 0.2, 1.5, 1.5, "plank")])


def cave_entrance():
    """Mine/cave mouth set against a cliff face. Origin = ground at the face; +Z = out of the cliff."""
    return asset([B(0, 0, 0.1, 6, 8, 0.2, "cave_dark"),
                  B(-3.6, 0, 0.6, 1.2, 9, 1.2, "wood_dark"), B(3.6, 0, 0.6, 1.2, 9, 1.2, "wood_dark"),
                  B(0, 9, 0.6, 9, 1.4, 1.4, "wood"), B(0, 0, 0.6, 6, 0.3, 1.2, "plank"),
                  B(4.9, 4, 1.4, 0.3, 4, 0.3, "metal"), B(4.9, 6.6, 1.4, 1.1, 1.5, 1.1, "glow"),
                  B(4.9, 8.1, 1.4, 1.4, 0.3, 1.4, "metal"),
                  B(-5.5, 0, 2, 2.2, 1.6, 2, "rock_gray"), B(-2, 0, 3, 1.6, 1.4, 1.2, "barrel"),
                  B(2, 0, 3.4, 2.2, 0.5, 1.2, "plank")],
                 lights=[(4.9, 7.3, 1.4, "glow", 18, 1.3)])


def stairs(width=6, steps=6, rise=1.5, run=2):
    b = []
    for k in range(steps):
        b.append(B(0, 0, k * run + run / 2, width, (k + 1) * rise, run, "plank" if k % 2 else "wood"))
    for x in (-width / 2 - 0.3, width / 2 + 0.3):
        for k in range(0, steps + 1, 3):
            b.append(B(x, k * rise, k * run, 0.6, 4, 0.6, "wood_dark"))
    return asset(b)


ASSETS_PLACEHOLDER = object()


def shifted(boxes, dx, dz):
    return [(b[0] + dx, b[1], b[2] + dz, b[3] + dx, b[4], b[5] + dz, b[6]) for b in boxes]


GRASSY = (("grass", 3), ("grass_dark", 2), ("moss", 2))
CLIFF_CRAG = blob_rock(41, 6.5, 5.5, 32, shades=ROCK_SHADES, peak=0.75, moss=0.35, tops=GRASSY)
CLIFF_ROCKS = (blob_rock(42, 6.5, 6, 13, shades=ROCK_SHADES, moss=0.5, tops=GRASSY)
               + shifted(blob_rock(43, 5, 4.5, 9, shades=ROCK_SHADES, moss=0.5, tops=GRASSY), 9, 3)
               + shifted(blob_rock(44, 4, 4, 6, shades=ROCK_SHADES, moss=0.5, tops=GRASSY), -8, -4))
LEDGE_ROCK = blob_rock(45, 8, 6, 9, shades=ROCK_SHADES, peak=2.5, moss=0.6, tops=GRASSY)

ASSETS = {
    "PineTree": pine(6, 12, 1),
    "PineTreeTall": pine(7, 14, 2),
    "PineTreeSmall": pine(4, 8, 3, trunk=3),
    "Bush": bush(),
    "GrassTuft": grass_tuft(),
    "Flowers": flowers(),
    "Fern": fern(),
    "Mushrooms": mushrooms(),
    "SmallRock": small_rock(),
    "RockOutcrop": asset(blob_rock(31, 8, 7, 18)),
    "RockOutcropBig": asset(blob_rock(32, 11, 9, 26, shades=GRAY_ROCK_SHADES)),
    "RockOutcropSmall": asset(blob_rock(33, 4.5, 4, 8)),
    # rocks that sit *in* the island: cliff colours, grassy tops
    "CliffCrag": asset(CLIFF_CRAG),
    "CliffRocks": asset(CLIFF_ROCKS),
    "LedgeRock": asset(LEDGE_ROCK),
    "Boulder": asset(boulder_base()),
    "Arch": arch(),
    "Seaweed": seaweed(),
    "TubeCoral": tube_coral(),
    "BranchCoral": branch_coral(),
    "FanCoral": fan_coral(),
    "ReefPinnacle": rough(stacked_slabs(PINNACLE_A), 21),
    "ReefPinnacleTall": rough(stacked_slabs(PINNACLE_B), 24),
    "ReefShelf": rough(reef_shelf_base(), 22),
    "ReefArch": rough(reef_arch_base(), 23),
    "RuinPillar": ruin_pillar(),
    "Dock": dock(),
    "Rowboat": rowboat(),
    "Shipwreck": shipwreck(),
    "MarketStall": market_stall(),
    "Campfire": campfire(),
    "LampPost": lamp_post(),
    "Torch": torch(),
    "WoodFrame": wood_frame(),
    "Statue": statue(),
    "Signpost": signpost(),
    "Bench": bench(),
    "Well": well(),
    "FlagFrame": flag_frame(),
    "Fence": fence(),
    "CrateStack": crate_stack(),
    "Barrels": barrels(),
    "LogPile": log_pile(),
    "CaveEntrance": cave_entrance(),
    "WoodenStairs": stairs(),
}


# Mesh versions (built by tools/blender_meshes.py). boxes = the un-roughened base
# shape; faces pointing up get the `top` colour, the rest `rock`.
REEF_ROCK = (118, 136, 226)
ISLE_ROCK = (122, 132, 196)
MESH_SOURCES = {
    "ReefPinnacle": dict(boxes=stacked_slabs(PINNACLE_A, cap=False), rock="mesh_rock", top="mesh_sand",
                         seed=1, disp=2.3, noise=6, faces=520),
    "ReefPinnacleTall": dict(boxes=stacked_slabs(PINNACLE_B, cap=False), rock="mesh_rock", top="mesh_sand",
                             seed=2, disp=2.4, noise=6, faces=600),
    "ReefShelf": dict(boxes=reef_shelf_base(), rock="mesh_rock", top="mesh_sand", seed=3, disp=2.2,
                      noise=6.5, faces=560),
    "ReefArch": dict(boxes=reef_arch_base(), rock="mesh_rock", top="mesh_sand", seed=4, disp=2.0, noise=6,
                     faces=480),
    "Boulder": dict(boxes=boulder_base(), rock="rock_light", top="rock_light", seed=5, disp=1.6, noise=5,
                    faces=110, voxel=0.9),
    "Seaweed": dict(kind="seaweed", rock="seaweed", top="seaweed", seed=10),
    # island rocks: same deformation + same rock/grass textures as the island terrain mesh
    "Arch": dict(boxes=arch_base(), rock="rock", top="grass", seed=9, disp=2.4, noise=7, faces=700),
    "CliffCrag": dict(boxes=ASSETS_PLACEHOLDER, rock="rock", top="grass", seed=11, disp=2.2, noise=6, faces=480),
    "CliffRocks": dict(boxes=ASSETS_PLACEHOLDER, rock="rock", top="grass", seed=12, disp=2.0, noise=6, faces=480),
    "LedgeRock": dict(boxes=ASSETS_PLACEHOLDER, rock="rock", top="grass", seed=13, disp=1.7, noise=5, faces=300),
    "RockOutcrop": dict(boxes=ASSETS_PLACEHOLDER, rock="rock", top="moss", seed=6, disp=2.2, noise=6, faces=420),
    "RockOutcropBig": dict(boxes=ASSETS_PLACEHOLDER, rock="rock", top="moss", seed=7, disp=2.6, noise=7,
                           faces=620),
    "RockOutcropSmall": dict(boxes=ASSETS_PLACEHOLDER, rock="rock", top="moss", seed=8, disp=1.4, noise=4,
                             faces=160),
}
for _n, _src in MESH_SOURCES.items():
    if _src.get("boxes") is ASSETS_PLACEHOLDER:
        _src["boxes"] = ASSETS[_n]["boxes"]

# Desert / Frost / Volcanic assets and their rock meshes
from theme_assets import theme_assets, theme_mesh_sources  # noqa: E402

ASSETS.update(theme_assets())
MESH_SOURCES.update(theme_mesh_sources(ASSETS))

# rocks made for one kind of spot (cliff wall, buttress, corner, overhang, beach, terrace) per theme
from fit_rocks import fit_rock_assets, fit_rock_mesh_sources  # noqa: E402
from theme_assets import DESERT, FROST, VOLCANIC, recolor  # noqa: E402

ASSETS.update(fit_rock_assets(asset, recolor, {"voxel": None, "desert": DESERT, "frost": FROST,
                                               "volcanic": VOLCANIC}))
MESH_SOURCES.update(fit_rock_mesh_sources(ASSETS))


def bounds(name):
    bx = ASSETS[name]["boxes"]
    mn = [min(b[i] for b in bx) for i in range(3)]
    mx = [max(b[i + 3] for b in bx) for i in range(3)]
    return mn, mx


# (run `python3 -c "import assets"` - this module can't be run directly: theme_assets imports it)
