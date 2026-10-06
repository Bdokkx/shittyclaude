"""Props in the chunky toy style of the coral-reef target. Each function builds in the model's current
local frame (origin on the ground, front = -Z, matching Roblox). Scale: player is ~5 studs tall."""
import math
import random

ACCENTS = {"red": "#FF5A5A", "yellow": "#FFD447", "pink": "#FF8FC7", "sky": "#4FC3F7",
           "orange": "#FF8A3D", "lime": "#9BE34A", "purple": "#B67CFF", "white": "#FFF7EC"}
METAL = "#5A5F6E"
METAL_LT = "#8C93A6"
GLOW = "#FFD98A"
ROPE = "#D9B77E"
STONE = "#B9B4C8"
STONE_DK = "#8E89A0"
WOOD = "#9A6238"
WOOD_DK = "#6B4226"
CORAL_BASE = ("#8B5A44", "#A9725A")


# ---------------------------------------------------------------- plants

def pine(m, size, seed, greens=("#2F8F4A", "#3FA85A"), trunk=WOOD_DK, snow=None):
    """size 0/1/2 -> ~14 / 19 / 25 studs. Trunk of 2-3 angled segments, 4-5 big tier slabs."""
    rng = random.Random(seed)
    h = (14, 19, 25)[size]
    tiers = (4, 4, 5)[size]
    with m.ctx(collide=True):
        x, y = 0.0, 0.0
        segs = (2, 3, 3)[size]
        seg_h = h * 0.32 / segs
        for k in range(segs):
            nx = x + rng.uniform(-0.35, 0.35)
            m.beam((x, y, 0), (nx, y + seg_h + 0.6, 0), 2.0 - 0.25 * k, trunk)
            x, y = nx, y + seg_h
        base_w = h * 0.62
        y = h * 0.22
        span = h - y
        for t in range(tiers):
            f = t / tiers
            w = base_w * (1 - 0.72 * f)
            th = span / tiers * 1.15
            rot = 45 * (t % 2) + rng.uniform(-8, 8)
            col = greens[t % 2]
            m.box((x, y + th / 2, 0), (w, th, w), col, ry=rot, rx=rng.uniform(-3, 3), rz=rng.uniform(-3, 3))
            if t < 2:          # cross-block on the lower, wider tiers only
                m.box((x, y + th * 0.55, 0), (w * 0.72, th * 1.1, w * 0.72), col, ry=rot + 45)
            if snow:
                m.box((x, y + th + 0.25, 0), (w * 0.82, 0.5, w * 0.82), snow, ry=rot, collide=False)
            y += th * 0.82
        m.box((x, y + 1.2, 0), (1.6, 2.4, 1.6), greens[tiers % 2], ry=rng.uniform(0, 90))


def oak(m, size, seed, greens=("#5DBB46", "#47A23A"), trunk=WOOD_DK):
    """Round tree: angled trunk segments, two branches, 4-5 big leaf blocks. ~14 / 17 / 21 studs."""
    rng = random.Random(seed)
    h = (14, 17, 21)[size]
    with m.ctx():
        x, y = 0.0, 0.0
        for k in range(3):
            nx = x + rng.uniform(-0.6, 0.6)
            m.beam((x, y, 0), (nx, y + h * 0.17 + 0.6, 0), 2.4 - 0.3 * k, trunk)
            x, y = nx, y + h * 0.17
        for s in (-1, 1):
            m.beam((x, y - 1.5, 0), (x + s * 3.2, y + 1.6, rng.uniform(-1.5, 1.5)), 1.1, trunk)
        cy = y + h * 0.16
        r = h * 0.26
        blobs = [(0, r * 0.35, 0, 1.0)] + [(math.cos(a) * r * 0.75, rng.uniform(-0.6, 0.3) * r, math.sin(a) * r * 0.75, 0.75)
                                           for a in [rng.uniform(0, 6.28) + k * 2.1 for k in range(3)]]
        if size == 2:
            blobs.append((0, r * 1.0, 0, 0.6))
        for k, (bx, by, bz, f) in enumerate(blobs):
            s = r * 1.5 * f
            m.box((x + bx, cy + by, bz), (s, s * 0.85, s), greens[k % 2],
                  ry=rng.uniform(0, 90), rx=rng.uniform(-10, 10), rz=rng.uniform(-10, 10))


def palm(m, size, seed, greens=("#3FAE4A", "#2E8F3C"), trunk=("#B98552", "#9A6A3E")):
    """Curved trunk of 4 tilted segments + 6 big clean fronds. ~14 / 18 / 23 studs."""
    rng = random.Random(seed)
    h = (14, 18, 23)[size]
    lean = rng.uniform(10, 18)
    with m.ctx():
        x = y = 0.0
        for k in range(4):
            ang = math.radians(lean * (k + 1) / 4)
            seg = h * 0.8 / 4
            nx, ny = x + math.sin(ang) * seg, y + math.cos(ang) * seg
            m.beam((x, y, 0), (nx, ny + 0.4, 0), 1.9 - 0.18 * k, trunk[k % 2])
            x, y = nx, ny
        m.box((x, y + 0.6, 0), (2.4, 1.6, 2.4), greens[1])
        for k in range(6):
            a = k * 60 + rng.uniform(-10, 10)
            with m.at((x, y + 1.1, 0), ry=a):
                # each frond: a long flat leaf rising then two drooping pieces
                m.box((0, 0.6, -2.6), (2.4, 0.5, 5.4), greens[k % 2], rx=-12)
                m.box((0, -0.4, -6.6), (2.0, 0.5, 3.6), greens[(k + 1) % 2], rx=22)
                m.box((0, -1.8, -8.6), (1.4, 0.5, 2.0), greens[k % 2], rx=48)
        for s in (-1, 1):
            m.box((x + s * 0.9, y - 0.4, 0.8), (1.1, 1.1, 1.1), "#7A4E2D")


def bush(m, seed, greens=("#4FA83A", "#63BF4C"), berry=ACCENTS["red"]):
    rng = random.Random(seed)
    with m.ctx(collide=False):
        for k, (dx, dz, s) in enumerate(((0, 0, 3.8), (2.4, 0.8, 3.0), (-1.8, 1.2, 2.6))):
            m.box((dx, s * 0.42, dz), (s, s * 0.85, s), greens[k % 2], ry=rng.uniform(0, 90))
        if berry:
            for k in range(4):
                a = rng.uniform(0, 6.28)
                m.box((math.cos(a) * 1.9, rng.uniform(1.6, 3.0), math.sin(a) * 1.9), (0.7, 0.7, 0.7), berry, shadow=False)


def flowers(m, seed, colors=("red", "yellow", "pink"), n=None, leaf="#4FA83A"):
    """Cluster of 3-5 flowers on a shared leafy base."""
    rng = random.Random(seed)
    n = n or rng.randint(3, 5)
    with m.ctx(collide=False, shadow=False):
        m.box((0, 0.3, 0), (3.6, 0.6, 3.0), leaf, ry=rng.uniform(0, 90))
        for k in range(n):
            a = k * 6.28 / n + rng.uniform(-0.3, 0.3)
            r = rng.uniform(0.6, 1.5)
            fx, fz = math.cos(a) * r, math.sin(a) * r
            sh = rng.uniform(1.4, 2.4)
            col = ACCENTS[colors[k % len(colors)]]
            m.box((fx, 0.5 + sh / 2, fz), (0.35, sh, 0.35), leaf)
            m.box((fx, 0.6 + sh, fz), (1.3, 0.45, 1.3), col, ry=45)
            m.box((fx, 0.62 + sh, fz), (1.3, 0.4, 1.3), col)
            m.box((fx, 0.9 + sh, fz), (0.5, 0.3, 0.5), ACCENTS["yellow"] if col != ACCENTS["yellow"] else ACCENTS["white"])


# ---------------------------------------------------------------- reef

def coral_tubes(m, seed, color, n=None, tall=1.0):
    """2-4 chunky square tubes on a brown mound, like the target."""
    rng = random.Random(seed)
    n = n or rng.randint(2, 4)
    with m.ctx(stage="reef", folder="Reef", collide=False):
        m.box((0, 0.8, 0), (4.4, 1.6, 4.0), CORAL_BASE[0], ry=rng.uniform(0, 90))
        m.box((0, 1.9, 0), (3.2, 1.2, 3.0), CORAL_BASE[1], ry=rng.uniform(0, 90))
        for k in range(n):
            a = k * 6.28 / n + rng.uniform(-0.4, 0.4)
            r = 0.9 if n > 1 else 0
            h = rng.uniform(3.5, 6.5) * (1.0 if k else 1.2) * tall
            w = rng.uniform(1.5, 2.1)
            with m.at((math.cos(a) * r, 2.2, math.sin(a) * r), rx=rng.uniform(-10, 10), rz=rng.uniform(-10, 10),
                      ry=rng.uniform(0, 90)):
                m.box((0, h / 2, 0), (w, h, w), color)
                m.box((0, h - 0.2, 0), (w + 0.5, 0.7, w + 0.5), color)


def coral_fan(m, seed, color):
    rng = random.Random(seed)
    with m.ctx(stage="reef", folder="Reef", collide=False):
        m.box((0, 0.7, 0), (3.4, 1.4, 3.0), CORAL_BASE[0], ry=rng.uniform(0, 90))
        for k in range(5):
            a = -50 + k * 25 + rng.uniform(-6, 6)
            with m.at((0, 1.2, 0), rz=a):
                m.box((0, 2.6, 0), (2.2, 5.2, 0.5), color)
                m.box((0, 5.2, 0), (2.8, 1.4, 0.6), color)


def coral_branch(m, seed, color):
    rng = random.Random(seed)
    with m.ctx(stage="reef", folder="Reef", collide=False):
        m.box((0, 0.7, 0), (3.2, 1.4, 3.2), CORAL_BASE[1], ry=rng.uniform(0, 90))
        m.box((0, 3.0, 0), (1.6, 4.2, 1.6), color, rz=rng.uniform(-6, 6))
        for k in range(3):
            a = rng.uniform(0, 360)
            with m.at((0, 2.4 + k * 1.2, 0), ry=a):
                m.box((1.4, 0.8, 0), (2.4, 1.2, 1.2), color, rz=35)
                m.box((2.3, 2.0, 0), (1.3, 2.4, 1.3), color)


def kelp(m, seed, height=16, greens=("#3DBE4A", "#2E9E3E")):
    """3-4 tall wavy ribbons in one clump."""
    rng = random.Random(seed)
    with m.ctx(stage="reef", folder="Reef", collide=False, shadow=False):
        for s in range(rng.randint(3, 4)):
            bx, bz = rng.uniform(-1.6, 1.6), rng.uniform(-1.6, 1.6)
            h = height * rng.uniform(0.7, 1.15)
            ry = rng.uniform(0, 180)
            y, k = 0.0, 0
            while y < h:
                seg = 2.4
                tilt = 18 if k % 2 else -18
                with m.at((bx + (0.5 if k % 2 else -0.5), y + seg / 2, bz), ry=ry):
                    m.box((0, 0, 0), (1.5, seg + 0.5, 0.35), greens[k % 2], rz=tilt)
                y += seg
                k += 1


# ---------------------------------------------------------------- props

def lantern_post(m, h=9, glow=GLOW, wood=WOOD_DK, tier_light=True):
    with m.ctx():
        m.box((0, 0.5, 0), (1.8, 1.0, 1.8), STONE_DK)
        m.box((0, h / 2, 0), (0.8, h, 0.8), wood)
        m.box((0.9, h - 0.4, 0), (2.4, 0.6, 0.6), wood)
        with m.ctx(collide=False):
            m.box((1.8, h - 1.2, 0), (0.25, 1.0, 0.25), METAL)
            m.box((1.8, h - 2.0, 0), (1.5, 0.3, 1.5), METAL)
            m.box((1.8, h - 3.1, 0), (1.5, 0.3, 1.5), METAL)
            m.box((1.8, h - 2.55, 0), (1.1, 0.9, 1.1), glow, mat="Neon",
                  light=("PointLight", 1.6, 18, glow) if tier_light else None, shadow=False)


def crate(m, s=2.8, wood=WOOD, dark=WOOD_DK, ry=0):
    with m.ctx():
        m.box((0, s / 2, 0), (s, s, s), wood, ry=ry)
        m.box((0, s / 2, 0), (s + 0.2, 0.5, s + 0.2), dark, ry=ry)
        m.box((0, s - 0.2, 0), (s + 0.2, 0.4, s + 0.2), dark, ry=ry)


def barrel(m, h=3.2, wood=WOOD, band=METAL):
    with m.ctx():
        m.octagon(h / 2, 1.2, h, wood)
        for y in (0.7, h - 0.7):
            m.octagon(y, 1.3, 0.35, band)


def fish(m, color, length=2.6, ry=0, rx=0, rz=0, pos=(0, 0, 0)):
    """Chunky fish: body, tail, fin, eye. Body along +X."""
    with m.ctx(collide=False, shadow=False):
        with m.at(pos, rx=rx, ry=ry, rz=rz):
            m.box((0, 0, 0), (length, length * 0.42, length * 0.3), color)
            m.box((-length * 0.6, 0, 0), (length * 0.3, length * 0.45, length * 0.12), color, rz=0)
            m.box((0.1, length * 0.26, 0), (length * 0.4, length * 0.14, length * 0.1), color)
            m.box((length * 0.32, length * 0.06, length * 0.16), (0.25, 0.25, 0.05), "#1E2230")


def ice_crate(m, fish_colors=("sky", "orange", "pink")):
    with m.ctx():
        m.box((0, 0.9, 0), (4.0, 1.8, 2.8), WOOD)
        m.box((0, 1.6, 0), (4.2, 0.4, 3.0), WOOD_DK)
        m.box((0, 1.9, 0), (3.4, 0.4, 2.2), "#DFF4FF", collide=False)
        for k, c in enumerate(fish_colors):
            fish(m, ACCENTS[c], 2.0, ry=10 * (k - 1), pos=(-0.9 + k * 0.9, 2.35, -0.5 + 0.5 * k))


def fish_bucket(m):
    with m.ctx():
        m.box((0, 0.9, 0), (2.0, 1.8, 2.0), METAL_LT)
        m.box((0, 1.75, 0), (2.2, 0.3, 2.2), METAL)
        fish(m, ACCENTS["orange"], 1.6, rz=70, pos=(0.2, 2.3, 0))
        fish(m, ACCENTS["sky"], 1.5, rz=60, ry=40, pos=(-0.3, 2.2, 0.3))


def rope_coil(m):
    with m.ctx(collide=False):
        for k, s in enumerate((2.4, 1.9)):
            m.octagon(0.25 + k * 0.45, s / 2, 0.45, ROPE)
        m.box((0, 0.7, 0), (1.1, 0.5, 1.1), "#B8955F")


def spear_rack(m, n=4, wood=WOOD_DK):
    with m.ctx():
        m.box((-2.6, 2.4, 0), (0.6, 4.8, 0.6), wood)
        m.box((2.6, 2.4, 0), (0.6, 4.8, 0.6), wood)
        m.box((0, 4.2, 0), (6.0, 0.5, 0.7), wood)
        m.box((0, 1.4, 0), (6.0, 0.5, 0.7), wood)
        with m.ctx(collide=False):
            for k in range(n):
                x = -1.8 + k * 3.6 / max(1, n - 1)
                m.box((x, 3.0, -0.5), (0.25, 5.6, 0.25), "#C8A06A", rx=-6)
                m.box((x, 6.1, -0.83), (0.5, 0.9, 0.2), METAL_LT, rx=-6)


def bench(m, wood=WOOD, dark=WOOD_DK):
    with m.ctx():
        for x in (-2.2, 2.2):
            m.box((x, 0.9, 0), (0.6, 1.8, 2.0), dark)
        m.box((0, 1.9, 0.1), (6.0, 0.4, 2.2), wood)
        m.box((0, 3.1, 1.0), (6.0, 1.2, 0.4), wood, rx=-8)


def planter(m, seed, wood=WOOD_DK, colors=("red", "yellow", "pink")):
    with m.ctx():
        m.box((0, 0.9, 0), (5.0, 1.8, 2.6), wood)
        m.box((0, 1.85, 0), (5.3, 0.3, 2.9), "#4A2E1A")
        m.box((0, 1.8, 0), (4.4, 0.2, 2.0), "#5B3B22")
        with m.at((-1.2, 1.6, 0)):
            flowers(m, seed, colors, n=3)
        with m.at((1.3, 1.6, 0)):
            flowers(m, seed + 1, colors[::-1], n=3)


def sign_board(m, text, w=8, h=3, color="#F5E6C8", text_color="#5A3A22", post=WOOD_DK, height=5.5, posts=True):
    """Sign on two posts; returns the board part."""
    with m.ctx():
        if posts:
            for x in (-w / 2 + 0.6, w / 2 - 0.6):
                m.box((x, height / 2, 0.3), (0.7, height, 0.7), post)
        m.box((0, height - h / 2 + 0.6, 0), (w + 0.6, h + 0.6, 0.6), post)
        board = m.box((0, height - h / 2 + 0.6, -0.15), (w, h, 0.5), color)
        m.text(board, text, text_color, "Front")
        return board


def crate_cluster(m, seed, wood=WOOD, dark=WOOD_DK):
    """1 large, 2 medium, 1 small - anchored to a wall or post by the caller."""
    rng = random.Random(seed)
    crate(m, 3.0, wood, dark, ry=rng.uniform(-8, 8))
    with m.at((3.1, 0, 0.4)):
        barrel(m)
    with m.at((0.2, 3.0, 0.1)):
        crate(m, 2.0, wood, dark, ry=rng.uniform(10, 30))
    with m.at((-2.4, 0, -1.3)):
        crate(m, 1.6, wood, dark, ry=rng.uniform(20, 40))
