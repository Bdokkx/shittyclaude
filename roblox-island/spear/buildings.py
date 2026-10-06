"""Buildings and structures to the Building Quality Standard:
primary form (not a box) + secondary detail (plinth, trim, recessed framed windows, roof overhang with
fascia, door frame + step) + tertiary props (entrance cluster, sign, awning, chimney).
Local frame: ground at y=0, FRONT faces -Z."""
import math
import random

import props as P
from props import ACCENTS, METAL, METAL_LT, STONE, STONE_DK, WOOD, WOOD_DK

GLASS_DARK = "#33456B"


# ---------------------------------------------------------------- building blocks

def wall(m, w, h, t, color, openings=(), y0=0.0):
    """Wall from x=-w/2..w/2, y=y0..y0+h; outer face at z=0 (facing -Z), inner at z=t.
    openings: [(cx, oy, ow, oh)] relative to the wall (oy from y0). Splits the wall around them."""
    xs = sorted({-w / 2, w / 2} | {o[0] - o[2] / 2 for o in openings} | {o[0] + o[2] / 2 for o in openings})
    for xa, xb in zip(xs, xs[1:]):
        xm = (xa + xb) / 2
        cut = sorted((o[1], o[1] + o[3]) for o in openings if o[0] - o[2] / 2 <= xm <= o[0] + o[2] / 2)
        y = 0.0
        for ya, yb in cut + [(h, h)]:
            if ya > y + 0.01:
                m.span((xa, y0 + y, 0), (xb, y0 + ya, t), color)
            y = max(y, yb)


def window(m, cx, cy, ow, oh, frame, pane=GLASS_DARK, recess=0.7, shutters=None, glow=False):
    """Framed, recessed window centred at (cx, cy) on a wall whose outer face is z=0."""
    m.span((cx - ow / 2, cy - oh / 2, recess), (cx + ow / 2, cy + oh / 2, recess + 0.25), pane,
           mat="Neon" if glow else "Plastic", collide=False)
    f = 0.45
    m.span((cx - ow / 2 - f, cy + oh / 2, -0.3), (cx + ow / 2 + f, cy + oh / 2 + f, 0.2), frame)       # head
    m.span((cx - ow / 2 - f, cy - oh / 2 - 0.45, -0.7), (cx + ow / 2 + f, cy - oh / 2, 0.2), frame)     # sill
    for s in (-1, 1):
        m.span((cx + s * ow / 2, cy - oh / 2, -0.3), (cx + s * (ow / 2 + f), cy + oh / 2, 0.2), frame)
    m.span((cx - 0.12, cy - oh / 2, recess - 0.15), (cx + 0.12, cy + oh / 2, recess), frame, collide=False)  # mullion
    if shutters:
        for s in (-1, 1):
            m.span((cx + s * (ow / 2 + f), cy - oh / 2, -0.25), (cx + s * (ow / 2 + f + ow * 0.45), cy + oh / 2, 0.0),
                   shutters, collide=False)


def door(m, cx, w, h, frame, planks=(WOOD, WOOD_DK), step=STONE, recess=0.6, y0=0.0):
    for k in range(int(w / 1.0)):
        m.span((cx - w / 2 + k, y0, recess), (cx - w / 2 + k + 1, y0 + h, recess + 0.3), planks[k % 2])
    f = 0.5
    m.span((cx - w / 2 - f, y0 + h, -0.35), (cx + w / 2 + f, y0 + h + f, 0.2), frame)
    for s in (-1, 1):
        m.span((cx + s * w / 2, y0, -0.35), (cx + s * (w / 2 + f), y0 + h, 0.2), frame)
    m.box((cx + w / 2 - 0.9, y0 + h * 0.48, recess - 0.2), (0.4, 0.4, 0.4), "#D9B44A", collide=False)
    if step:
        m.span((cx - w / 2 - 0.8, y0 - 0.3, -1.8), (cx + w / 2 + 0.8, y0 + 0.3, 0.0), step)


def gable_roof(m, w, d, y, pitch, color, trim, overhang=1.5, thick=0.9, ridge=None, gable=None, gable_t=0.8):
    """Gable roof, ridge along X, eaves at height y. gable = wall colour to fill the end triangles."""
    p = math.radians(pitch)
    run = d / 2 + overhang
    rise = (d / 2) * math.tan(p)
    L = run / math.cos(p)
    for s in (-1, 1):
        with m.at((0, y + rise - (run / 2) * math.tan(p) + thick / 2 * math.cos(p), s * run / 2), rx=s * pitch):
            m.box((0, 0, 0), (w + 2 * overhang, thick, L), color)
            m.box((0, -thick / 2 - 0.15, s * (L / 2 - 0.3)), (w + 2 * overhang + 0.2, 0.7, 0.7), trim)   # fascia
        for e in (-1, 1):   # barge boards on the gable ends
            with m.at((e * (w / 2 + overhang + 0.05), y + rise - (run / 2) * math.tan(p) + thick / 2, s * run / 2),
                      rx=s * pitch):
                m.box((0, 0, 0), (0.5, thick + 0.5, L), trim)
    m.box((0, y + rise + thick * 0.9, 0), (w + 2 * overhang + 0.4, 0.8, 1.2), trim)   # ridge cap
    if gable:
        band = 1.2
        k = 0
        yy = y
        while yy < y + rise - 0.3:
            half = (y + rise - yy - band / 2) / math.tan(p)
            for e in (-1, 1):
                m.box((e * (w / 2 - gable_t / 2), yy + band / 2, 0), (gable_t, band, max(0.6, 2 * half)), gable)
            yy += band
            k += 1
    return y + rise


def plank_wall(m, x0, x1, y0, y1, z0, z1, tones=(WOOD, WOOD_DK), board=1.2, vertical=False):
    """Two-tone plank wall filling the given box."""
    if vertical:
        n = max(1, int(round((x1 - x0) / board)))
        for k in range(n):
            m.span((x0 + (x1 - x0) * k / n, y0, z0), (x0 + (x1 - x0) * (k + 1) / n, y1, z1), tones[k % 2])
    else:
        n = max(1, int(round((y1 - y0) / board)))
        for k in range(n):
            m.span((x0, y0 + (y1 - y0) * k / n, z0), (x1, y0 + (y1 - y0) * (k + 1) / n, z1), tones[k % 2])


def fish_icon(m, length, body, fin, eye="#1E2230"):
    """Big flat fish silhouette in the XY plane (for signs). Centre at origin."""
    L = length
    m.box((0, 0, 0), (L * 0.62, L * 0.36, 0.5), body)
    m.box((L * 0.3, 0, 0), (L * 0.2, L * 0.24, 0.5), body)
    m.box((-L * 0.36, 0, 0), (L * 0.14, L * 0.28, 0.5), body)
    for s in (-1, 1):
        m.box((-L * 0.48, s * L * 0.1, 0), (L * 0.2, L * 0.16, 0.5), fin, rz=s * 30)
    m.box((0, L * 0.22, 0), (L * 0.3, L * 0.1, 0.45), fin)
    m.box((L * 0.26, L * 0.05, -0.3), (L * 0.07, L * 0.07, 0.2), eye)
    m.box((L * 0.26, L * 0.05, 0.3), (L * 0.07, L * 0.07, 0.2), eye)


def spear_icon(m, length, shaft="#C8A06A", tip=METAL_LT, rz=35):
    with m.at((0, 0, 0), rz=rz):
        m.box((0, 0, 0), (length, 0.45, 0.4), shaft)
        m.box((length / 2 + 0.6, 0, 0), (1.4, 0.9, 0.45), tip, rz=45)


def hammer_icon(m, size):
    with m.at((0, 0, 0), rz=-30):
        m.box((0, -size * 0.15, 0), (size * 0.16, size * 0.8, 0.4), WOOD)
        m.box((0, size * 0.3, 0), (size * 0.7, size * 0.26, 0.45), METAL)


def hanging_sign(m, text, w, h, icon=None, board="#F5E6C8", ink="#5A3A22", trim=WOOD_DK):
    """Sign hanging from a bracket; bracket starts at the origin and reaches out along -Z."""
    m.span((-0.25, -0.25, -h * 0.2 - w * 0.0 - 3.2), (0.25, 0.25, 0.0), trim)
    with m.at((0, -0.6, -2.0)):
        m.box((0, -0.5, -0.0), (0.15, 1.0, 0.15), P.ROPE, collide=False)
        with m.at((0, -1.0 - h / 2, 0), ry=90):
            m.box((0, 0, 0), (w + 0.4, h + 0.4, 0.5), trim)
            b = m.box((0, 0, -0.1), (w, h, 0.45), board)
            m.text(b, text, ink, "Front")
            if icon:
                with m.at((0, h / 2 + 1.4, 0)):
                    icon(m)


# ---------------------------------------------------------------- shops

def fish_market(m, tier, C, seed=1):
    """Tier 1: a simple stall. Tier 2: open wooden market hall with striped awning, ice crates,
    hanging fish, scale and a big fish sign."""
    rng = random.Random(seed)
    red, white = ACCENTS["red"], ACCENTS["white"]
    if tier == 1:
        for x in (-4, 4):
            for z in (-2.5, 2.5):
                m.box((x, 4, z), (0.7, 8, 0.7), WOOD_DK)
        plank_wall(m, -4.5, 4.5, 0, 3.5, -3.2, -2.2, vertical=True)
        m.box((0, 3.75, -2.5), (9.6, 0.5, 2.2), WOOD_DK)
        with m.at((0, 8.4, 0), rx=12):
            m.box((0, 0, 0), (10, 0.5, 7), red)
        with m.at((-2, 4.0, -2.5)):
            m.box((0, 0.2, 0), (3, 0.4, 1.6), "#DFF4FF")
            P.fish(m, ACCENTS["sky"], 1.8, pos=(-0.5, 0.65, 0))
            P.fish(m, ACCENTS["orange"], 1.8, ry=180, pos=(0.6, 0.65, 0.2))
        with m.at((0, 0, -5)):
            P.sign_board(m, "FISH", w=5, h=2, height=4.2)
        with m.at((5.6, 0, -1)):
            P.barrel(m)
        return
    # ---- tier 2 market hall: 16 x 10, L-shaped (side wing for the scale + ice room)
    m.span((-8.6, 0, -5.6), (8.6, 0.9, 5.6), STONE_DK)                       # footing
    for k in range(8):                                                          # deck planks
        m.span((-8 + k * 2, 0.9, -5), (-8 + (k + 1) * 2, 1.4, 5), WOOD if k % 2 else WOOD_DK)
    plank_wall(m, -8, 8, 1.4, 9.4, 4.0, 5.0)                                   # back wall
    for s in (-1, 1):                                                           # low side walls
        plank_wall(m, s * 8 - 0.5, s * 8 + 0.5, 1.4, 4.6, -5, 4)
    for x, z in ((-7.6, -4.6), (7.6, -4.6), (-7.6, 4.6), (7.6, 4.6), (-2.8, -4.6), (2.8, -4.6)):
        m.box((x, 5.4, z), (1.0, 8.0, 1.0), WOOD_DK)
    m.span((-8.2, 9.0, -5.1), (8.2, 9.8, -4.1), WOOD_DK)                      # front beam
    m.span((-8.2, 9.4, 4.0), (8.2, 10.2, 5.0), WOOD_DK)
    # counter
    plank_wall(m, -6.5, 6.5, 1.4, 4.9, -3.6, -2.6, vertical=True, board=1.0)
    m.span((-7.0, 4.9, -4.0), (7.0, 5.4, -2.0), WOOD_DK)
    for k, x in enumerate((-4.6, -0.6, 3.4)):
        m.span((x - 1.6, 5.4, -3.7), (x + 1.6, 5.8, -2.3), "#DFF4FF", collide=False)   # ice trays
        for f in range(2):
            P.fish(m, ACCENTS[("sky", "orange", "pink", "yellow")[(k + f) % 4]], 1.7, ry=8 * (f - 0.5) + 180 * f,
                   pos=(x - 0.6 + 1.2 * f, 6.15, -3.0))
    # hanging scale on the counter's right end
    with m.at((6.0, 5.4, -3.0)):
        m.box((0, 2.2, 0), (0.4, 4.4, 0.4), WOOD_DK)
        m.box((-1.2, 4.3, 0), (2.8, 0.4, 0.4), WOOD_DK)
        m.box((-2.4, 3.4, 0), (0.15, 1.6, 0.15), METAL, collide=False)
        m.box((-2.4, 2.5, 0), (1.8, 0.3, 1.8), METAL_LT, collide=False)
        P.fish(m, ACCENTS["yellow"], 1.5, pos=(-2.4, 2.95, 0))
    # striped awning: back top -> front, overhanging 2.2 past the front
    p = math.degrees(math.atan2(10.2 - 8.6, 10.0 + 2.2))
    with m.at((0, (10.2 + 8.6) / 2 + 0.4, -1.1), rx=p):
        for k in range(9):
            x = -9 + k * 2 + 1
            m.box((x, 0, 0), (2.0, 0.5, 12.6), red if k % 2 == 0 else white)
        for k in range(9):   # scalloped valance
            x = -9 + k * 2 + 1
            m.box((x, -0.8, -6.2), (1.9, 1.1, 0.3), white if k % 2 == 0 else red, collide=False)
    # hanging fish under the front beam
    for k, x in enumerate((-6.2, -4.6, 4.6, 6.2)):
        m.box((x, 8.3, -4.6), (0.12, 1.4, 0.12), P.ROPE, collide=False)
        P.fish(m, ACCENTS[("sky", "pink", "orange", "yellow")[k]], 2.0, rz=-80, pos=(x, 6.8, -4.6))
    # big fish sign on the roof line
    with m.at((0, 10.2, 4.5)):
        for x in (-4.0, 4.0):
            m.box((x, 2.2, 0), (0.7, 4.4, 0.7), WOOD_DK)
        m.box((0, 3.2, -0.1), (10.6, 2.8, 0.6), WOOD_DK)
        board = m.box((0, 3.2, -0.45), (10.0, 2.2, 0.4), "#FFF1D6")
        m.text(board, "FISH MARKET", "#2A5DA8", "Front")
        with m.at((0, 6.4, -0.2)):
            fish_icon(m, 8.0, ACCENTS["sky"], ACCENTS["orange"])
    # entrance prop cluster (anchored to the front-left post)
    with m.at((-10.2, 0, -4.2), ry=12):
        P.crate_cluster(m, seed)
    with m.at((9.8, 0, -3.6)):
        P.ice_crate(m)
    with m.at((10.4, 0, 0.2)):
        P.fish_bucket(m)


def spear_shop(m, tier, C, seed=2):
    """Tier 1: canvas stall with a spear rack. Tier 2: timber-frame cottage, blue gable roof, chimney,
    recessed windows, spear rack and target board on the walls, hanging sign."""
    if tier == 1:
        for x in (-4, 4):
            for z in (-2.5, 2.5):
                m.box((x, 4, z), (0.7, 8, 0.7), WOOD_DK)
        plank_wall(m, -4.5, 4.5, 0, 3.5, -3.2, -2.2, vertical=True)
        m.box((0, 3.75, -2.5), (9.6, 0.5, 2.2), WOOD_DK)
        with m.at((0, 8.4, 0), rx=12):
            m.box((0, 0, 0), (10, 0.5, 7), C["roof"])
        with m.at((0, 0, 2.6)):
            P.spear_rack(m)
        with m.at((0, 0, -5)):
            P.sign_board(m, "SPEARS", w=5.5, h=2, height=4.2)
        return
    W, D, H, PL = 14.0, 11.0, 8.6, 1.2
    cream, timber = C["wall"], WOOD_DK
    m.span((-W / 2 - 0.6, 0, -D / 2 - 0.6), (W / 2 + 0.6, PL, D / 2 + 0.6), STONE_DK)          # plinth
    m.span((-W / 2 - 0.9, PL - 0.3, -D / 2 - 0.9), (W / 2 + 0.9, PL, D / 2 + 0.9), STONE)
    with m.at((0, 0, -D / 2)):                                                                    # front
        wall(m, W, H, 0.8, cream, [(-3.2, 0.0, 4.0, 7.6), (3.4, 3.2, 3.2, 3.0)], y0=PL)
        door(m, -3.2, 4.0, 7.6, timber, y0=PL)
        window(m, 3.4, PL + 4.7, 3.2, 3.0, timber, shutters=C["roof"])
    with m.at((0, 0, D / 2), ry=180):                                                             # back
        wall(m, W, H, 0.8, cream, [(-3.4, 3.2, 3.0, 3.0), (3.4, 3.2, 3.0, 3.0)], y0=PL)
        window(m, -3.4, PL + 4.7, 3.0, 3.0, timber)
        window(m, 3.4, PL + 4.7, 3.0, 3.0, timber)
    for s in (-1, 1):                                                                             # sides
        with m.at((s * W / 2, 0, 0), ry=-90 * s):
            wall(m, D - 1.6, H, 0.8, cream, [(0.0, 3.2, 3.0, 3.0)], y0=PL)
            window(m, 0.0, PL + 4.7, 3.0, 3.0, timber, shutters=C["roof"])
    # timber frame: corner posts, mid posts, sill/mid/top beams (protrude 0.3)
    for sx in (-1, 1):
        for sz in (-1, 1):
            m.box((sx * W / 2, PL + H / 2, sz * D / 2), (1.1, H, 1.1), timber)
    for z in (-D / 2 - 0.15, D / 2 + 0.15):
        for x in (-0.6,):
            m.box((x, PL + H / 2, z), (0.7, H, 0.5), timber)
        for y in (PL + 0.3, PL + H - 0.3):
            m.box((0, y, z), (W + 0.6, 0.6, 0.5), timber)
    for x in (-W / 2 - 0.15, W / 2 + 0.15):
        for y in (PL + 0.3, PL + H - 0.3):
            m.box((x, y, 0), (0.5, 0.6, D + 0.6), timber)
        m.box((x, PL + 2.4, -2.6), (0.45, 3.4, 0.45), timber, rx=40)    # side braces
        m.box((x, PL + 2.4, 2.6), (0.45, 3.4, 0.45), timber, rx=-40)
    top = gable_roof(m, W + 0.2, D + 0.2, PL + H, 32, C["roof"], C["roof_trim"], overhang=1.6, gable=cream)
    # chimney
    m.span((3.2, PL + H - 1, 1.2), (5.4, top + 2.6, 3.4), STONE)
    m.span((2.9, top + 2.6, 0.9), (5.7, top + 3.3, 3.7), STONE_DK)
    # spear rack on the right wall, target board on the left wall
    with m.at((W / 2 + 0.9, 0, 0), ry=-90):
        with m.at((0, PL, 0)):
            P.spear_rack(m, n=5)
    with m.at((-W / 2 - 0.5, PL + 2.0, 0), ry=90):
        m.box((0, 2.6, 0), (5.2, 5.2, 0.5), WOOD_DK)
        for k, (s, col) in enumerate(((4.6, ACCENTS["white"]), (3.6, ACCENTS["red"]), (2.6, ACCENTS["white"]),
                                      (1.6, ACCENTS["red"]), (0.7, ACCENTS["yellow"]))):
            m.box((0, 2.6, -0.3 - 0.06 * k), (s, s, 0.2), col, collide=False)
        m.box((0.6, 3.0, -0.9), (0.2, 0.2, 1.6), "#C8A06A", collide=False)   # spear stuck in the target
    # hanging sign at the front-right corner, entrance cluster at the door
    with m.at((W / 2 + 0.6, PL + H - 0.6, -D / 2 - 0.2)):
        with m.at((0, 0, 0), ry=0):
            hanging_sign(m, "SPEAR SHOP", 6.0, 2.0, icon=lambda mm: spear_icon(mm, 5.0))
    with m.at((-6.4, PL, -D / 2 - 2.2)):
        P.barrel(m)
    with m.at((-0.4, PL, -D / 2 - 2.4)):
        P.crate(m, 2.0)
    with m.at((0.8, PL, -D / 2 - 1.6)):
        m.box((0, 0.8, 0), (1.6, 1.6, 1.6), "#B5653A")                       # potted plant
        m.box((0, 2.2, 0), (2.0, 1.8, 2.0), "#4FA83A", ry=20)
        m.box((0, 3.0, 0), (1.2, 1.0, 1.2), "#63BF4C", ry=50)


def upgrade_station(m, tier, C, seed=3):
    """Carpenter's yard: lean-to shed, workbench, stacked logs, sawhorse, blueprint easel,
    scaffolding and a hammer sign. Tier 1 is just the bench, logs and easel."""
    def logs(n_base, length=8.0):
        k = 0
        for row in range(n_base):
            for i in range(n_base - row):
                x = (i - (n_base - row - 1) / 2) * 1.9
                with m.at((x, 0.95 + row * 1.6, 0)):
                    m.box((0, 0, 0), (1.8, 1.8, length), WOOD if k % 2 else "#86542F", rz=45 / 2 * (k % 2))
                    for e in (-1, 1):
                        m.box((0, 0, e * length / 2), (1.3, 1.3, 0.15), "#D9B07A", rz=45 / 2 * (k % 2), collide=False)
                k += 1

    def bench(x, z):
        with m.at((x, 0, z)):
            for sx in (-2.6, 2.6):
                for sz in (-1, 1):
                    m.box((sx, 1.7, sz), (0.6, 3.4, 0.6), WOOD_DK)
            m.box((0, 3.6, 0), (6.4, 0.5, 2.8), WOOD)
            m.box((-1.5, 4.1, 0), (2.4, 0.5, 0.4), WOOD_DK, collide=False)
            with m.at((1.6, 4.2, 0)):
                hammer_icon(m, 2.2)

    def easel(x, z, ry=0):
        with m.at((x, 0, z), ry=ry):
            for s in (-1, 1):
                m.box((s * 1.6, 3.2, 0.3), (0.45, 6.6, 0.45), WOOD_DK, rz=s * 8)
            m.box((0, 2.4, 1.6), (0.45, 5.0, 0.45), WOOD_DK, rx=-20)
            m.box((0, 2.8, -0.2), (4.6, 0.4, 0.8), WOOD_DK)
            b = m.box((0, 4.6, -0.2), (4.4, 3.4, 0.25), "#3B6FD6")
            for y, w_ in ((5.6, 3.2), (4.7, 2.2), (3.8, 2.8)):
                m.box((0 - (3.2 - w_) / 2, y, -0.36), (w_, 0.2, 0.05), "#EAF2FF", collide=False)
            m.box((1.2, 4.4, -0.36), (0.2, 1.8, 0.05), "#EAF2FF", collide=False)
            return b

    if tier == 1:
        bench(0, 0)
        with m.at((-6.5, 0, 1.0)):
            logs(2, 6.0)
        easel(5.6, -0.6, ry=-15)
        return
    # tier 2: lean-to shed 13 x 8, open at the front, red roof
    W, D = 13.0, 8.0
    m.span((-W / 2 - 0.5, 0, -D / 2 - 0.5), (W / 2 + 0.5, 0.8, D / 2 + 0.5), STONE_DK)
    plank_wall(m, -W / 2, W / 2, 0.8, 10.0, D / 2 - 1.0, D / 2)
    for s in (-1, 1):
        plank_wall(m, s * W / 2 - 0.5 * s - 0.5, s * W / 2 - 0.5 * s + 0.5, 0.8, 8.4, -D / 2 + 1, D / 2 - 1,
                   board=1.4)
    for x in (-W / 2, 0, W / 2):
        m.box((x, 4.6, -D / 2), (1.0, 7.6, 1.0), WOOD_DK)
    m.span((-W / 2 - 0.5, 8.2, -D / 2 - 0.5), (W / 2 + 0.5, 9.0, -D / 2 + 0.5), WOOD_DK)
    p = math.degrees(math.atan2(10.6 - 8.8, D + 2.4))
    with m.at((0, 9.9, 0), rx=p):
        m.box((0, 0, 0), (W + 3.0, 0.8, D + 3.4), C["roof2"])
        m.box((0, -0.3, -(D + 3.4) / 2 + 0.3), (W + 3.2, 0.9, 0.6), WOOD_DK)
    bench(0, 0.6)
    with m.at((0, 0.8, D / 2 - 1.6)):
        for k, x in enumerate((-4.5, -3.3, 3.4, 4.6)):       # tools on the back wall
            m.box((x, 5.2, 0.4), (0.3, 3.0, 0.3), WOOD_DK, collide=False)
            m.box((x, 6.6, 0.3), (0.9, 0.7, 0.3), METAL, collide=False)
    # yard: log pile, sawhorse, blueprint easel, scaffolding
    with m.at((-W / 2 - 6.0, 0, 1.5)):
        logs(3)
    with m.at((W / 2 + 4.5, 0, -2.5), ry=20):
        for s in (-1, 1):
            m.box((s * 2.0, 1.4, 0), (0.5, 3.2, 2.2), WOOD_DK, rx=0)
        m.box((0, 3.0, 0), (5.6, 0.5, 0.9), WOOD)
        m.box((0.4, 3.4, 0), (7.0, 0.4, 1.6), "#C68A52")
    easel(-3.6, -D / 2 - 3.2, ry=10)
    with m.at((W / 2 + 4.0, 0, 4.0)):     # scaffolding beside the shed
        for x in (-2.4, 2.4):
            for z in (-1.6, 1.6):
                m.box((x, 6, z), (0.5, 12, 0.5), "#C68A52")
        for y in (4.5, 9.0):
            plank_wall(m, -2.8, 2.8, y, y + 0.5, -2.0, 2.0, vertical=True, board=1.0)
        for k in range(6):
            m.box((-2.9, 1 + k * 1.5, 0), (0.3, 0.3, 2.4), WOOD_DK)
    with m.at((-W / 2 + 0.5, 0, -D / 2 - 2.0)):
        P.sign_board(m, "UPGRADES", w=6.5, h=2.2, height=5.0)
        with m.at((0, 7.6, -0.3)):
            hammer_icon(m, 3.2)


# ---------------------------------------------------------------- landmark, plaza, gate, boats

def lighthouse(m, C, beam_tier=3):
    """Lighthouse landmark (door faces -Z):
    two-tier stone foundation with steps, keeper's cottage attached at the back, tapering octagonal
    tower in red/white bands with trim rings, framed windows, arched door with a little roof,
    corbelled gallery with railing, glass lamp room with mullions and a glowing lamp, stepped red
    dome with a ball finial and a weather vane."""
    red, white = C["lh_red"], C["lh_white"]
    stone, stone_dk = P.STONE, P.STONE_DK
    m.octagon(1.0, 9.0, 2.0, stone_dk)                                  # foundation
    m.octagon(2.2, 8.2, 0.4, stone)
    m.octagon(3.0, 7.6, 1.2, stone_dk)
    m.octagon(3.75, 7.9, 0.3, stone)
    for k in range(3):                                                    # steps up to the door
        m.span((-3.0, 0, -9.0 - (2 - k) * 1.3), (3.0, 1.3 * (k + 1), -7.7 - (2 - k) * 1.3 + 0.01), stone)
    with m.at((0, 0, 8.0)):                                               # keeper's cottage at the back
        m.span((-6.5, 0, 0), (6.5, 1.2, 9.5), stone_dk)
        with m.at((0, 1.2, 9.0), ry=180):
            wall(m, 12, 7.0, 0.7, "#F1E3C2", [(0, 0, 3.6, 6.0)])
            door(m, 0, 3.6, 6.0, C["wood_dark"], y0=0.0, step=None)
        for s_ in (-1, 1):
            with m.at((s_ * 6.0, 1.2, 4.5), ry=-90 * s_):
                wall(m, 8.4, 7.0, 0.7, "#F1E3C2", [(0, 2.6, 2.6, 2.6)])
                window(m, 0, 3.9, 2.6, 2.6, C["wood_dark"], shutters=C["roof"])
        for x in (-6.2, 6.2):
            m.box((x, 4.7, 9.0), (1.0, 7.0, 1.0), C["wood_dark"])
        with m.at((0, 0, 4.6)):
            top = gable_roof(m, 12.6, 9.6, 8.2, 30, red, "#B23B3B", overhang=1.2, gable="#F1E3C2", gable_t=0.7)
        m.span((3.0, 7.0, 6.0), (5.0, top + 2.2, 8.0), stone)
        m.span((2.7, top + 2.2, 5.7), (5.3, top + 2.8, 8.3), stone_dk)
    with m.at((0, 4.0, 0), rx=1.5, rz=-1.0):
        y, r = 0.0, 5.6
        for k in range(7):
            h = 4.2
            m.octagon(y + h / 2, r, h, white if k % 2 == 0 else red)
            m.octagon(y + h - 0.15, r + 0.25, 0.3, P.STONE_DK if k % 2 == 0 else white)
            y += h
            r -= 0.3
        with m.at((0, 0, -5.6)):                                        # arched door + little roof
            door(m, 0, 3.6, 6.2, stone_dk, planks=(WOOD, WOOD_DK), step=None, recess=-0.3, y0=0.0)
            m.span((-2.4, 6.6, -1.8), (2.4, 7.1, 0.1), red)
            m.span((-2.7, 7.1, -2.0), (2.7, 7.5, 0.1), "#B23B3B")
        for k, yy in enumerate((11.0, 19.5, 26.5)):
            for side in (-1, 1) if k == 1 else (-1,):
                ry_ = 0 if side == -1 else 180
                rr = 5.6 - 0.3 * (yy / 4.2)
                with m.at((0, 0, 0), ry=ry_ + (90 if k == 2 else 0)):
                    with m.at((0, 0, -rr)):
                        window(m, 0, yy, 1.8, 2.6, P.STONE_DK, recess=-0.15)
        # corbels + gallery deck + railing
        for k in range(8):
            a = k * math.pi / 4 + math.pi / 8
            m.box((math.cos(a) * 3.9, y - 0.6, math.sin(a) * 3.9), (1.0, 1.2, 1.0), stone_dk)
        m.octagon(y + 0.5, 6.6, 1.0, stone_dk)
        m.octagon(y + 1.05, 6.3, 0.15, stone)
        for k in range(16):
            a = k * math.pi / 8
            m.box((math.cos(a) * 6.0, y + 2.0, math.sin(a) * 6.0), (0.35, 2.0, 0.35), P.METAL)
        with m.ctx(collide=False):
            m.octagon(y + 3.0, 6.2, 0.3, P.METAL)
        # glass lamp room
        with m.ctx(collide=False):
            m.octagon(y + 4.0, 3.4, 5.0, "#CFEFFF", mat="Glass")
        for k in range(8):
            a = k * math.pi / 4 + math.pi / 8
            m.box((math.cos(a) * 3.55, y + 4.0, math.sin(a) * 3.55), (0.45, 5.2, 0.45), P.METAL)
        m.octagon(y + 1.7, 3.8, 0.8, P.METAL)
        m.box((0, y + 4.0, 0), (2.4, 3.0, 2.4), C["lamp"], mat="Neon", ry=45,
              light=("PointLight", 3, 40, C["lamp"]), shadow=False)
        m.octagon(y + 6.9, 4.4, 0.8, red)                               # stepped dome
        m.octagon(y + 7.8, 3.6, 1.0, red)
        m.octagon(y + 8.8, 2.6, 1.0, red)
        m.octagon(y + 9.7, 1.5, 0.8, "#B23B3B")
        m.box((0, y + 10.9, 0), (0.5, 1.6, 0.5), P.METAL)
        m.box((0, y + 12.0, 0), (1.1, 1.1, 1.1), "#FFD447", ry=45, rx=35)
        with m.at((0, y + 13.2, 0)):                                    # weather vane
            m.box((0, 0, 0), (0.25, 1.6, 0.25), P.METAL)
            m.box((0.9, 0.5, 0), (2.2, 0.25, 0.15), P.METAL)
            m.box((1.9, 0.5, 0), (0.6, 0.6, 0.12), P.METAL, rz=45)
        with m.ctx(tier=beam_tier, collide=False, shadow=False):   # rotating beam (spun by the Spinner script)
            m.box((0, y + 4.0, 0), (1.4, 1.4, 44), "#FFF3B0", mat="Neon", name="LighthouseBeam", transparency=0.7,
                  light=("SpotLight", 4, 60, "#FFF3B0"))
        return y + 12


def fountain(m, C):
    """Octagonal basin, glass water, pedestal and a leaping orange fish spouting water."""
    stone, dark, water = STONE, STONE_DK, "#4FC3F7"
    m.octagon(0.9, 5.6, 1.8, dark)
    m.octagon(1.95, 5.8, 0.3, stone)
    with m.ctx(collide=False):
        m.octagon(1.75, 4.8, 0.3, water, mat="Glass")
    m.octagon(2.6, 1.6, 3.2, dark)
    m.octagon(4.3, 1.9, 0.4, stone)
    with m.at((0, 7.2, 0), rz=38, ry=30):
        fish_icon(m, 6.0, ACCENTS["orange"], ACCENTS["yellow"])
    with m.ctx(collide=False, shadow=False):
        for k, (dx, dy, a) in enumerate(((2.8, 9.6, -20), (4.2, 9.0, -55), (5.0, 7.2, -80), (5.2, 5.2, -90),
                                         (5.1, 3.4, -95))):
            with m.at((0, 0, 0), ry=30):
                m.box((dx, dy, 0), (0.9, 1.9, 0.9), water, rz=a, mat="Glass")


def well(m):
    m.octagon(1.1, 2.6, 2.2, STONE)
    with m.ctx(collide=False):
        m.octagon(2.05, 2.0, 0.4, "#2E5D8A")
    for s in (-1, 1):
        m.box((s * 2.6, 3.6, 0), (0.6, 7.2, 0.6), WOOD_DK)
    m.box((0, 6.0, 0), (5.8, 0.5, 0.5), WOOD_DK)
    with m.at((0, 7.6, 0)):
        for s in (-1, 1):
            m.box((0, 0, s * 1.4), (6.6, 0.5, 3.4), "#B5523B", rx=s * 30)
    m.box((0, 4.6, 0), (0.12, 2.6, 0.12), P.ROPE, collide=False)
    m.box((0, 3.2, 0), (1.2, 1.2, 1.2), WOOD, collide=False)


def stone_arch(m, bands, moss, seed=7, half=7.8):
    """Gate of big angled slabs: two legs at x = +-half + lintel slabs, moss cap. Walk-through along Z."""
    rng = random.Random(seed)
    for s in (-1, 1):
        y = 0.0
        k = 0
        while y < 14:
            th = rng.uniform(2.6, 4.0)
            f = y / 18
            col = bands[2] if f < 0.3 else bands[1] if f < 0.62 else bands[0]
            with m.at((s * (half + rng.uniform(-0.4, 0.4)), y + th / 2, rng.uniform(-0.5, 0.5)),
                      ry=rng.uniform(-10, 10), rx=rng.uniform(-6, 6), rz=s * rng.uniform(2, 8)):
                m.box((0, 0, 0), (5.6 - 0.12 * k, th, 7.0 - 0.1 * k), col)
            y += th * 0.9
            k += 1
    with m.at((0, 15.2, 0), rz=rng.uniform(-3, 3)):
        m.box((0, 0, 0), (2 * half + 7.4, 3.2, 7.4), bands[1], ry=rng.uniform(-3, 3))
    with m.at((0.8, 17.6, 0.3), rz=rng.uniform(-4, 4)):
        m.box((0, 0, 0), (2 * half + 3.4, 2.6, 6.6), bands[0], ry=rng.uniform(-6, 6))
    m.box((0.6, 19.3, 0.3), (2 * half + 2.0, 1.0, 6.4), moss)
    with m.at((-4, 19.8, 0.5)):
        P.flowers(m, seed, ("pink", "yellow"))
    with m.at((5, 19.8, -0.6)):
        P.bush(m, seed)


def sailboat(m, sail, hull=(WOOD, "#FFF7EC"), length=16):
    """Small sailboat, bow toward -Z; origin at the waterline."""
    L = length
    m.box((0, -0.8, 0), (2.4, 1.6, L * 0.8), WOOD_DK)
    for k, (w, y, l) in enumerate(((4.4, 0.0, L * 0.86), (5.6, 1.0, L * 0.94), (6.2, 2.0, L))):
        col = hull[1] if k == 1 else hull[0]
        m.box((0, y, 0.4), (w, 1.0, l * 0.8), col)
        for s in (-1, 1):     # tapered bow
            m.box((s * w * 0.18, y, -l * 0.45), (w * 0.55, 1.0, l * 0.22), col, ry=s * 28)
    m.box((0, 2.6, 0.6), (5.4, 0.3, L * 0.72), "#C68A52")
    m.box((0, 9.5, -1.0), (0.7, 14, 0.7), WOOD_DK)
    m.box((0, 4.2, 2.6), (0.5, 0.5, 7.0), WOOD_DK)
    with m.ctx(collide=False):
        for k, (w, y) in enumerate(((6.4, 6.6), (5.0, 10.2), (3.2, 13.6))):
            m.box((0.3, y, 1.6 - k * 0.2), (0.3, 3.6, w), sail)
        m.box((0, 16.8, -1.6), (0.2, 1.2, 2.2), ACCENTS["red"])


def dock_deck(m, x0, z0, x1, z1, y, planks=(WOOD, WOOD_DK), along="z", post=WOOD_DK, post_every=6.0,
              rails=(), rope=True, seabed=-10.0):
    """Plank deck from (x0,z0) to (x1,z1) with its top at y; posts down to the seabed.
    rails: sides to rail ('x0','x1','z0','z1'), with gaps every other bay so players can shoot through."""
    if along == "z":
        n = max(1, int(round(abs(z1 - z0) / 2)))
        for k in range(n):
            za, zb = z0 + (z1 - z0) * k / n, z0 + (z1 - z0) * (k + 1) / n
            m.span((x0, y - 0.8, za), (x1, y, zb), planks[k % 2])
    else:
        n = max(1, int(round(abs(x1 - x0) / 2)))
        for k in range(n):
            xa, xb = x0 + (x1 - x0) * k / n, x0 + (x1 - x0) * (k + 1) / n
            m.span((xa, y - 0.8, z0), (xb, y, z1), planks[k % 2])
    m.span((x0 + 0.4, y - 1.6, z0), (x0 + 1.0, y - 0.8, z1), post)        # stringers
    m.span((x1 - 1.0, y - 1.6, z0), (x1 - 0.4, y - 0.8, z1), post)
    xs = [x0, x1]
    zs = [z0 + (z1 - z0) * k / max(1, round(abs(z1 - z0) / post_every)) for k in range(int(round(abs(z1 - z0) / post_every)) + 1)]
    xs_line = [x0 + (x1 - x0) * k / max(1, round(abs(x1 - x0) / post_every)) for k in range(int(round(abs(x1 - x0) / post_every)) + 1)]
    posts = set()
    for z in zs:
        for x in xs:
            posts.add((round(x, 2), round(z, 2)))
    for x in xs_line:
        for z in (z0, z1):
            posts.add((round(x, 2), round(z, 2)))
    for (x, z) in posts:          # pilings stop under the deck; the railing does the job above it
        m.span((x - 0.6, seabed, z - 0.6), (x + 0.6, y - 0.8, z + 0.6), post)
    for side in rails:            # continuous railings; ("z0", (xa, xb)) leaves a gap where a walkway joins
        gap = None
        if isinstance(side, tuple):
            side, gap = side
        if side in ("x0", "x1"):
            x = (x0 + 0.35) if side == "x0" else (x1 - 0.35)
            segs = [(z0, z1)] if not gap else [(z0, gap[0]), (gap[1], z1)]
            for za, zb in segs:
                rail_line(m, (x, za + 0.35), (x, zb - 0.35), y, planks)
        else:
            z = (z0 + 0.35) if side == "z0" else (z1 - 0.35)
            segs = [(x0, x1)] if not gap else [(x0, gap[0]), (gap[1], x1)]
            for xa, xb in segs:
                rail_line(m, (xa + 0.35, z), (xb - 0.35, z), y, planks)


# ---------------------------------------------------------------- simple shop stall (all three shops)

STALL_WOOD = ("#C97A3A", "#A35F2A")


def dashed_square(m, w, d, color, name, dash=1.2, gap=0.8):
    """Glowing dashed outline on the ground (the 'step here' zone) + a faint glowing fill that is the
    touch part for scripts (named `name`)."""
    with m.ctx(collide=False, shadow=False):
        m.box((0, 0.08, 0), (w, 0.12, d), color, mat="Neon", transparency=0.82, name=name, effect="pad")
        for (length, other, horiz) in ((w, d, True), (d, w, False)):
            n = int(length / (dash + gap))
            start = -(n * (dash + gap) - gap) / 2
            for k in range(n):
                c = start + k * (dash + gap) + dash / 2
                for s in (-1, 1):
                    if horiz:
                        m.box((c, 0.12, s * other / 2), (dash, 0.2, 0.4), color, mat="Neon")
                    else:
                        m.box((s * other / 2, 0.12, c), (0.4, 0.2, dash), color, mat="Neon")


def simple_stall(m, title, stripe, cloth, pad_name, goods=None, ink="#2A3A5C", icon=None):
    """Market stall, front faces -Z, ~14 wide x 9 deep:
    stone footing, plank floor, thick corner posts with capitals, framed counter with a draped cloth,
    plank back wall with two shelves, low side walls, sloped striped awning with a scalloped valance,
    big framed sign with a 3D icon, hanging lantern, a crate/barrel cluster and a glowing pad in front."""
    lw, dw = STALL_WOOD
    trim = "#7A4423"
    W, D = 13.0, 8.0
    # footing + floor
    m.box((0, 0.4, 0.3), (W + 1.4, 0.8, D + 1.4), P.STONE_DK)
    m.box((0, 0.85, 0.3), (W + 0.8, 0.3, D + 0.8), P.STONE)
    for k in range(7):
        x = -W / 2 + (k + 0.5) * W / 7
        m.box((x, 1.15, 0.3), (W / 7 - 0.05, 0.3, D), lw if k % 2 else "#B66D33")
    # corner posts with stone feet + capitals
    for x in (-W / 2, W / 2):
        for z in (-D / 2, D / 2 + 0.6):
            m.box((x, 1.6, z), (1.8, 0.9, 1.8), P.STONE_DK)
            m.box((x, 5.6, z), (1.3, 8.0, 1.3), dw)
            m.box((x, 9.8, z), (1.7, 0.6, 1.7), trim)
    m.box((0, 9.6, -D / 2), (W + 1.2, 0.9, 1.0), trim)                 # front beam
    m.box((0, 11.2, D / 2 + 0.6), (W + 1.2, 0.9, 1.0), trim)           # back beam (higher)
    # back wall: vertical boards + two shelves
    for k in range(9):
        x = -W / 2 + 0.7 + k * (W - 1.4) / 9 + (W - 1.4) / 18
        m.box((x, 6.1, D / 2 + 0.6), ((W - 1.4) / 9 - 0.04, 9.6, 0.6), lw if k % 2 else "#B66D33")
    for y in (5.0, 7.6):
        m.box((0, y, D / 2 - 0.2), (W - 1.6, 0.35, 1.4), trim)
        for s_ in (-1, 1):
            m.box((s_ * 4.5, y - 0.6, D / 2 - 0.2), (0.3, 0.9, 1.2), trim, rx=0)
    # low side walls
    for s_ in (-1, 1):
        for k in range(3):
            m.box((s_ * W / 2, 1.9 + k * 0.95, 0.3), (0.5, 0.9, D - 1.2), lw if k % 2 else "#B66D33")
        m.box((s_ * W / 2, 4.85, 0.3), (0.8, 0.35, D - 0.8), trim)
    # counter: framed panels + top + cloth
    m.box((0, 2.6, -D / 2 + 0.6), (W - 1.4, 3.0, 1.2), "#B66D33")
    for k in range(4):
        x = -W / 2 + 0.7 + (k + 0.5) * (W - 1.4) / 4
        m.box((x, 2.6, -D / 2 - 0.05), ((W - 1.4) / 4 - 0.9, 2.0, 0.2), lw)
    for x in [-W / 2 + 0.7 + k * (W - 1.4) / 4 for k in range(5)]:
        m.box((x, 2.6, -D / 2 - 0.1), (0.45, 3.0, 0.3), trim)
    m.box((0, 4.35, -D / 2 + 0.6), (W - 0.6, 0.5, 2.2), trim)
    m.box((0, 4.65, -D / 2 + 0.6), (W - 2.6, 0.15, 2.0), cloth)
    with m.at((0, 3.9, -D / 2 - 0.45)):
        m.box((0, 0, 0), (W - 2.6, 1.2, 0.15), cloth)
        for k in range(5):
            m.box((-(W - 2.6) / 2 + (k + 0.5) * (W - 2.6) / 5, -0.9, 0), (1.1, 1.1, 0.15), cloth, rz=45)
    # awning: sloped striped roof with scalloped valance
    slope = math.degrees(math.atan2(11.6 - 10.0, D + 2.6))
    with m.at((0, 10.9, 0.2), rx=-slope):
        n = 7
        for k in range(n):
            x = -W / 2 - 0.9 + (k + 0.5) * (W + 1.8) / n
            m.box((x, 0, 0), ((W + 1.8) / n + 0.02, 0.6, D + 3.2), stripe if k % 2 == 0 else "#FFFFFF")
        m.box((0, 0.45, D / 2 + 1.3), (W + 2.0, 0.4, 0.8), trim)
        for k in range(n):
            x = -W / 2 - 0.9 + (k + 0.5) * (W + 1.8) / n
            col = "#FFFFFF" if k % 2 == 0 else stripe
            m.box((x, -0.8, -(D + 3.2) / 2 + 0.15), ((W + 1.8) / n - 0.3, 1.0, 0.3), col)
            m.box((x, -1.35, -(D + 3.2) / 2 + 0.15), (0.9, 0.9, 0.3), col, rz=45)
    # sign: framed board on two short posts above the awning, with a 3D icon
    for s_ in (-1, 1):
        m.box((s_ * 3.6, 12.6, -1.0), (0.6, 2.6, 0.6), trim)
    m.box((0, 14.2, -1.0), (10.4, 2.8, 0.6), trim)
    board = m.box((0, 14.2, -1.35), (9.6, 2.1, 0.3), "#FFF6E2")
    m.text(board, title, ink, "Front")
    if icon:
        with m.at((0, 17.0, -1.0)):
            icon(m)
    # hanging lantern on the front-left post
    with m.at((-W / 2 - 0.2, 8.4, -D / 2 - 1.0)):
        m.box((0, 0.9, 0.5), (0.3, 0.3, 1.6), P.METAL)
        m.box((0, 0.3, 0), (0.15, 0.9, 0.15), P.METAL, collide=False)
        m.box((0, -0.5, 0), (1.3, 0.3, 1.3), P.METAL, collide=False)
        m.box((0, -1.2, 0), (0.9, 1.1, 0.9), P.GLOW, mat="Neon", collide=False,
              light=("PointLight", 1.2, 16, P.GLOW))
        m.box((0, -1.9, 0), (1.3, 0.3, 1.3), P.METAL, collide=False)
    if goods:
        goods(m)
    with m.at((W / 2 + 2.2, 0, 1.5)):                          # side cluster against the wall
        P.barrel(m)
    with m.at((W / 2 + 2.0, 0, 4.4)):
        P.crate(m, 2.6)
    with m.at((W / 2 + 2.1, 2.6, 4.3)):
        P.crate(m, 1.6)
    with m.at((0, 0, -9.0)):
        dashed_square(m, 8.0, 5.0, cloth, pad_name)


def goods_fish(m):
    for k, x in enumerate((-3.6, 0, 3.6)):                       # low ice trays with small fish on the counter
        m.box((x, 4.85, -3.4), (3.0, 0.3, 1.8), "#DFF4FF", collide=False)
        P.fish(m, P.ACCENTS[("sky", "orange", "pink")[k]], 1.3, ry=90, rz=90, pos=(x, 5.15, -3.4))
    for k, x in enumerate((-4, -1.3, 1.3, 4)):                   # jars + baskets on the shelves
        m.box((x, 5.75, 3.6), (1.4, 1.2, 1.2), ("#5BB6E3", "#C8A06A", "#5BB6E3", "#C8A06A")[k])
        m.box((x, 8.35, 3.6), (1.6, 1.2, 1.2), ("#C8A06A", "#FF8A3D", "#C8A06A", "#FF8A3D")[k])


def goods_spears(m):
    with m.ctx(collide=False):
        for k in range(7):                                       # spearguns on the back wall
            x = -4.5 + k * 1.5
            m.box((x, 6.6, 4.1), (0.3, 6.6, 0.3), "#C8A06A")
            m.box((x, 10.1, 4.0), (0.6, 1.0, 0.25), P.METAL_LT, rz=45)
            m.box((x, 4.6, 4.0), (0.7, 0.9, 0.5), "#3A3F4E")
        for k in range(2):                                       # two on the counter
            with m.at((-2.5 + k * 5, 5.0, -3.4), ry=12 - 24 * k):
                m.box((0, 0, 0), (5.0, 0.35, 0.35), "#C8A06A")
                m.box((2.8, 0, 0), (1.0, 0.6, 0.3), P.METAL_LT, rz=45)
                m.box((-1.2, -0.4, 0), (0.6, 0.8, 0.4), "#3A3F4E")


def goods_upgrades(m):
    with m.ctx(collide=False):
        m.box((-2.6, 4.9, -3.4), (3.4, 0.3, 2.0), "#3B6FD6")              # blueprint on the counter
        for k in range(3):
            m.box((-2.9 + 0.3 * k, 5.07, -3.6 + 0.5 * k), (2.2 - 0.4 * k, 0.05, 0.12), "#EAF2FF")
        with m.at((2.6, 5.2, -3.4)):
            hammer_icon(m, 2.2)
        for k in range(4):                                       # planks + tools on the shelves
            m.box((-2.0, 5.5 + 0.4 * k, 3.6), (6.0, 0.35, 0.9), "#C68A52" if k % 2 else "#A8703F")
        for k, x in enumerate((2.6, 4.2)):
            m.box((x, 8.6, 4.0), (0.3, 2.8, 0.3), P.WOOD_DK)
            m.box((x, 9.8, 3.9), (1.0, 0.6, 0.3), P.METAL)
        m.box((-3.5, 8.4, 3.6), (2.4, 1.2, 1.2), "#B5523B")


def icon_fish(m):
    fish_icon(m, 5.0, P.ACCENTS["sky"], P.ACCENTS["orange"])


def icon_spear(m):
    spear_icon(m, 5.5)


def icon_hammer(m):
    hammer_icon(m, 3.6)


# ---------------------------------------------------------------- portal

def ring(m, R, n, w, depth, colors, z=0.0, mat="Plastic", phase=0.5, **kw):
    """Ring of n blocks of radius R in the local XY plane (normal +Z)."""
    seg = 2 * math.pi * R / n + 0.3
    for k in range(n):
        a = 2 * math.pi * (k + phase) / n
        with m.at((math.cos(a) * R, math.sin(a) * R, z), rz=math.degrees(a) + 90):
            m.box((0, 0, 0), (seg, w, depth), colors[k % len(colors)], mat=mat, **kw)


def portal(m, R=7.5):
    """Round portal gate facing -Z on a stepped round dais: chunky two-tone stone ring with an inner
    trim ring, keystone with a gem, side horns, a vortex of glowing rings that spin around the core
    (PortalSwirl / PortalSwirl2, spun by the Spinner script), a bright core (PortalCore: light +
    particles), runes, three floating crystals (PortalOrbit) and a glowing dashed pad (PortalPad)."""
    stone, stone_dk, stone_lt = "#7C74C4", "#5A519E", "#A39BE0"
    # stepped dais
    m.octagon(0.5, 8.2, 1.0, stone_dk)
    m.octagon(1.25, 7.2, 0.5, stone)
    m.octagon(1.75, 6.0, 0.5, stone_lt)
    with m.ctx(collide=False):
        m.octagon(1.52, 7.25, 0.08, "#B67CFF", mat="Neon")            # glowing inlay line
    cy = 2.0 + R + 1.0
    with m.at((0, cy, 0)):
        ring(m, R, 28, 2.4, 3.2, (stone, stone_dk))                  # outer ring
        ring(m, R - 1.5, 24, 0.8, 3.6, (stone_lt,), phase=0)          # inner trim, slightly deeper
        ring(m, R + 1.3, 28, 0.5, 2.0, (stone_dk,), z=0.2)            # back flange
        with m.ctx(collide=False):
            ring(m, R - 2.05, 24, 0.35, 0.6, ("#E2C4FF",), z=-1.5, mat="Neon")   # glowing rim
        # keystone + gem, side horns, feet
        m.box((0, R + 0.4, 0), (3.0, 3.4, 4.0), stone_dk)
        m.box((0, R + 0.4, -2.05), (1.4, 1.4, 0.3), "#4FE3FF", mat="Neon", rz=45)
        for s_ in (-1, 1):
            with m.at((s_ * (R + 0.6), 0, 0)):
                m.box((0, 0, 0), (2.2, 3.0, 3.8), stone_dk)
                m.box((s_ * 1.0, 1.2, 0), (1.2, 1.6, 2.6), stone, rz=-s_ * 30)
            with m.at((s_ * (R * 0.62), -R * 0.82, 0), rz=s_ * 35):
                m.box((0, 0, 0), (2.6, 3.0, 3.8), stone_dk)
        for k in range(8):                                          # runes on the front of the ring
            a = math.radians(22.5 + 45 * k)
            if abs(math.cos(a)) > 0.95:
                continue
            with m.at((math.cos(a) * R, math.sin(a) * R, -1.65), rz=math.degrees(a)):
                m.box((0, 0, 0), (0.8, 0.8, 0.12), "#4FE3FF", mat="Neon", rz=45, collide=False)
        # vortex: rings fading from deep purple at the rim to white at the core, each further back
        with m.ctx(collide=False, shadow=False):
            vort = [(R - 2.6, 1.1, "#5B2FD1", "PortalSwirl", -0.2), (R - 3.5, 1.0, "#8A4DFF", "PortalSwirl2", 0.0),
                    (R - 4.4, 0.95, "#B07CFF", "PortalSwirl", 0.2), (R - 5.2, 0.9, "#62D8FF", "PortalSwirl2", 0.4),
                    (R - 5.9, 0.8, "#A9F1FF", "PortalSwirl", 0.6)]
            for k, (r, w, col, nm, z) in enumerate(vort):
                n = max(8, int(2 * math.pi * r / 1.4))
                for j in range(n):
                    a = 2 * math.pi * j / n
                    if j % 3 == 2:
                        continue                                    # gaps make the spin visible
                    with m.at((math.cos(a) * r, math.sin(a) * r, z), rz=math.degrees(a) + 90 + 18):
                        m.box((0, 0, 0), (2 * math.pi * r / n * 1.05, w, 0.3), col, mat="Neon", name=nm)
            m.box((0, 0, 0.9), (2 * (R - 2.3), 2 * (R - 2.3), 0.2), "#3A1C8C", mat="Neon", transparency=0.15)
            m.box((0, 0, 0.8), (2.0, 2.0, 0.4), "#FFFFFF", mat="Neon", name="PortalCore", rz=45,
                  light=("PointLight", 3.5, 36, "#A57BFF"), effect="portal")
    # floating crystals orbiting the ring
    with m.ctx(collide=False):
        for k, (a, h) in enumerate(((150, 1.0), (30, 0.6), (270, 0.0))):
            r = math.radians(a)
            with m.at((math.cos(r) * (R + 4.2), cy + math.sin(r) * (R + 2.5) + h, -1.0), rz=20 * k):
                m.box((0, 0, 0), (1.0, 2.2, 1.0), "#4FE3FF", mat="Neon", ry=45, name="PortalOrbit")
                m.box((0, 1.5, 0), (0.6, 0.9, 0.6), "#E2C4FF", mat="Neon", ry=45, name="PortalOrbit")
    # stone lantern pillars either side of the dais
    for s_ in (-1, 1):
        with m.at((s_ * (R + 4.5), 0, -3.0)):
            m.box((0, 0.6, 0), (2.4, 1.2, 2.4), stone_dk)
            m.box((0, 2.8, 0), (1.5, 3.4, 1.5), stone)
            m.box((0, 4.7, 0), (2.2, 0.5, 2.2), stone_dk)
            m.box((0, 5.6, 0), (1.2, 1.3, 1.2), "#4FE3FF", mat="Neon", ry=45,
                  light=("PointLight", 1.2, 14, "#4FE3FF"))
            m.box((0, 6.5, 0), (2.0, 0.5, 2.0), stone_dk)
    with m.at((0, 0.0, -10.5)):
        dashed_square(m, 8.0, 5.0, "#B67CFF", "PortalPad")


# ---------------------------------------------------------------- camp

def campfire(m):
    m.octagon(0.4, 2.4, 0.8, "#8E89A0")
    m.octagon(0.5, 1.7, 0.8, "#4A3A30")
    for k in range(4):
        m.box((0, 1.0, 0), (3.2, 0.7, 0.7), "#6B4226", ry=k * 45 + 10, rz=8)
    m.box((0, 1.9, 0), (1.4, 1.6, 1.4), "#FF8A3D", mat="Neon", ry=45, effect="fire",
          light=("PointLight", 2, 22, "#FFA552"), collide=False)
    m.box((0, 2.9, 0), (0.8, 1.0, 0.8), "#FFD447", mat="Neon", ry=20, collide=False)


def log_seat(m, length=6):
    m.box((0, 0.9, 0), (length, 1.6, 1.6), "#86542F", rx=0)
    for e in (-1, 1):
        m.box((e * length / 2, 0.9, 0), (0.2, 1.2, 1.2), "#D9B07A", collide=False)


def tent(m, cloth=("#FF5A5A", "#FFF7EC")):
    """A-frame tent, opening toward -Z."""
    for s in (-1, 1):
        with m.at((s * 1.9, 2.0, 0), rz=s * 42):
            for k in range(3):
                m.box((0, 0, -3 + k * 2 + 1), (0.4, 5.6, 2.0), cloth[k % 2])
    m.box((0, 4.1, 0), (0.6, 0.6, 6.6), "#6B4226")
    for z in (-3.2, 3.2):
        m.box((0, 2.0, z), (0.5, 4.2, 0.5), "#6B4226")
    m.box((0, 0.15, 0), (6.4, 0.3, 6.2), "#C9A27A")


# ---------------------------------------------------------------- rails

def rail_line(m, a, b, y, color=(WOOD, WOOD_DK), every=4.0, h=3.0):
    """Continuous railing from a to b (x, z) at deck height y: posts every ~4 studs, top + mid rail."""
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    if L < 0.5:
        return
    n = max(1, int(round(L / every)))
    for k in range(n + 1):
        t = k / n
        x, z = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
        m.box((x, y + h / 2, z), (0.7, h, 0.7), color[1])
    ry = math.degrees(math.atan2(b[0] - a[0], b[1] - a[1]))
    with m.at(((a[0] + b[0]) / 2, y, (a[1] + b[1]) / 2), ry=ry):
        m.box((0, h - 0.25, 0), (0.45, 0.45, L + 0.4), color[0])
        m.box((0, h * 0.5, 0), (0.35, 0.35, L), color[0])


def portal_bounds():
    """Bounds of the Blender portal (exports/portal/portal_bounds.json, written by tools/portal_mesh.py)
    in its own space: ground at y=0, front facing -Z."""
    import json
    import os
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "exports", "portal",
                        "portal_bounds.json")
    if os.path.exists(path):
        b = json.load(open(path))
        return b["min"], b["max"]
    return [-12.0, 0.0, -8.0], [12.0, 24.0, 8.0]
